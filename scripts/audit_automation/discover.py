"""Discover pending audit jobs from Notion (queue lives in Notion, not on Vercel disk)."""

from __future__ import annotations

import datetime
from typing import Any
from urllib.parse import urlparse

from scripts.audit_automation.jobs import AuditJob, JobKind
from scripts.audit_automation.slug import slug_from_email_url as make_slug
from scripts.launchlook_constants import FREE_AUDIT_PIPELINE_TIER

# How long before a stale [automation:processing] lock is reclaimed (P0 #6).
_PROCESSING_LOCK_RECLAIM_HOURS = 2

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from notion_client import Client  # noqa: E402

from api._lib.env import require_env  # noqa: E402
from api._lib.notion_helpers import (  # noqa: E402
    STATUS_INTAKE,
    get_client,
    get_customers_ds_id,
)


def _get_free_audit_ds_id(client: Client) -> str:
    db_id = require_env("NOTION_FREE_AUDIT_DB_ID")
    db = client.databases.retrieve(database_id=db_id)
    sources = db.get("data_sources") or []
    if not sources:
        raise RuntimeError("Free Audit DB has no data_sources")
    return sources[0]["id"]


def _prop_text(props: dict[str, Any], name: str) -> str:
    p = props.get(name) or {}
    if "title" in p:
        parts = p["title"] or []
        return "".join(x.get("plain_text", "") for x in parts).strip()
    if "rich_text" in p:
        parts = p["rich_text"] or []
        return "".join(x.get("plain_text", "") for x in parts).strip()
    if "email" in p:
        return (p.get("email") or "").strip()
    if "url" in p:
        return (p.get("url") or "").strip()
    if "select" in p and p["select"]:
        return (p["select"].get("name") or "").strip()
    return ""


def _platform_from_select(raw: str) -> tuple[str, str]:
    low = (raw or "").strip().lower()
    if low == "webflow":
        return "webflow", "Webflow"
    return "vibe-coder", raw.title() if raw else "Lovable"


def _is_stale_processing(row: dict[str, Any]) -> bool:
    """True if a row's last_edited_time is older than the reclaim threshold."""
    raw = row.get("last_edited_time") or row.get("created_time") or ""
    if not raw:
        return True  # unknown age → treat as stale so we don't block forever
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        edited_at = datetime.datetime.fromisoformat(raw)
        if edited_at.tzinfo is None:
            edited_at = edited_at.replace(tzinfo=datetime.UTC)
    except ValueError:
        return True
    age = datetime.datetime.now(datetime.UTC) - edited_at
    return age > datetime.timedelta(hours=_PROCESSING_LOCK_RECLAIM_HOURS)


def discover_free_jobs(client: Client | None = None) -> list[AuditJob]:
    client = client or get_client()
    ds_id = _get_free_audit_ds_id(client)
    # Query both queued and processing rows; stale processing rows are
    # reclaimed after _PROCESSING_LOCK_RECLAIM_HOURS (P0 #6).
    resp = client.data_sources.query(
        data_source_id=ds_id,
        filter={
            "or": [
                {"property": "Status", "select": {"equals": "queued"}},
                {"property": "Status", "select": {"equals": "processing"}},
            ]
        },
        sorts=[{"timestamp": "created_time", "direction": "ascending"}],
        page_size=20,
    )
    jobs: list[AuditJob] = []
    for row in resp.get("results") or []:
        if row.get("archived") or row.get("in_trash"):
            continue
        props = row.get("properties") or {}
        status = _prop_text(props, "Status")
        # Skip processing rows that were modified recently (another run is
        # still working). Only reclaim if older than the lock threshold.
        if status.lower() == "processing" and not _is_stale_processing(row):
            continue
        email = _prop_text(props, "Email").lower()
        url = _prop_text(props, "URL")
        if not email or not url:
            continue
        plat_raw = _prop_text(props, "Platform") or "vibe-coder"
        platform, builder = _platform_from_select(plat_raw)
        host = urlparse(url).hostname or "app"
        jobs.append(
            AuditJob(
                kind=JobKind.FREE,
                slug=make_slug(email, url),
                url=url,
                email=email,
                tier=FREE_AUDIT_PIPELINE_TIER,
                builder=builder,
                platform=platform,
                app_name=host,
                name="",
                intake_notes="",
                notion_page_id=row["id"],
                notion_db="free_audit",
            )
        )
    return jobs


TIER_NORMALIZE = {
    "starter package": "Starter Package",
    "starter package ($19)": "Starter Package",
    "starter package ($9)": "Starter Package",  # legacy
    "starter": "Starter Package",
    "scale up package": "Scale Up Package",
    "scale up package ($49)": "Scale Up Package",
    "scale up": "Scale Up Package",
    "pro package": "Pro Package",
    "pro package ($99)": "Pro Package",
    "pro": "Pro Package",
    "full package": "Scale Up Package",
    "full package ($49)": "Scale Up Package",
    "full package ($29)": "Scale Up Package",
}


def discover_paid_jobs(client: Client | None = None) -> list[AuditJob]:
    """Customers with intake received who are not delivered yet."""
    client = client or get_client()
    ds_id = get_customers_ds_id(client)
    resp = client.data_sources.query(
        data_source_id=ds_id,
        filter={
            "and": [
                {"property": "Status", "select": {"equals": STATUS_INTAKE}},
                {"property": "Intake Received", "checkbox": {"equals": True}},
            ]
        },
        sorts=[{"timestamp": "created_time", "direction": "ascending"}],
        page_size=20,
    )
    jobs: list[AuditJob] = []
    for row in resp.get("results") or []:
        if row.get("archived") or row.get("in_trash"):
            continue
        props = row.get("properties") or {}
        email = _prop_text(props, "Email").lower()
        url = _prop_text(props, "App URL")
        if not email or not url:
            continue
        tier_raw = _prop_text(props, "Tier").lower()
        tier = TIER_NORMALIZE.get(tier_raw, _prop_text(props, "Tier") or "Starter Package")
        plat = _prop_text(props, "Platform") or "Lovable"
        platform, builder = _platform_from_select(plat)
        name = _prop_text(props, "Name")
        app_name = _prop_text(props, "App Name") or urlparse(url).hostname or "App"
        notes = _prop_text(props, "Notes")
        notes_lower = notes.lower()
        # Skip if the pipeline already finished this job.
        if "[automation:draft_ready]" in notes_lower:
            continue
        # Skip if another run is currently processing this job (P0 #6).
        # Only reclaim the lock once it is older than the stale threshold,
        # which catches crashed pipeline runs without blocking live ones.
        if "[automation:processing]" in notes_lower and not _is_stale_processing(row):
            continue
        jobs.append(
            AuditJob(
                kind=JobKind.PAID,
                slug=make_slug(email, url),
                url=url,
                email=email,
                tier=tier,
                builder=builder if builder != "Vibe-Coder" else plat or "Lovable",
                platform=platform,
                app_name=app_name,
                name=name,
                intake_notes=notes,
                notion_page_id=row["id"],
                notion_db="customers",
            )
        )
    return jobs


def discover_all() -> list[AuditJob]:
    client = get_client()
    return discover_free_jobs(client) + discover_paid_jobs(client)
