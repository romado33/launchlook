"""
notion_helpers.py — thin wrapper around notion_client for the Customers DB.

Both webhooks (Tally + Stripe) reuse these. The Customers DB schema is defined
in templates/notion/customers-db.csv; the property names hard-coded here match
that schema. If a property is missing from the live DB, build_properties()
silently drops it so the create/update call still succeeds.

Public surface:
    get_client()                       -> notion_client.Client bound to NOTION_TOKEN
    get_customers_ds_id(client)        -> data source id for the Customers DB
    find_customer_by_email(client, ds, email, since=None) -> dict | None
    upsert_customer(client, ds, fields, email_for_match) -> (page_id, "created" | "updated")
    update_customer_fields(client, page_id, fields)      -> None
    build_properties(fields)           -> dict ready for the Notion API

`fields` is a plain dict using friendly keys (see FIELD_TO_NOTION). Unknown keys
are ignored; None / empty values are skipped so we never blank out a column.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from typing import Any

from .env import require_env

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError
except ImportError:
    sys.exit("ERROR: pip install notion-client>=2.2 (see requirements-automation.txt)")


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------
# Friendly key -> (Notion property name, Notion property type).
# Friendly keys are what callers pass in. The property type tells
# build_properties how to wrap the value. Order does not matter.

FIELD_TO_NOTION: dict[str, tuple[str, str]] = {
    "name": ("Name", "title"),
    "email": ("Email", "email"),
    "app_url": ("App URL", "url"),
    "app_name": ("App Name", "rich_text"),
    "platform": ("Platform", "select"),
    "tier": ("Tier", "select"),
    "status": ("Status", "select"),
    "payment_date": ("Payment Date", "date"),
    "intake_received": ("Intake Received", "checkbox"),
    "intake_received_at": ("Intake Received At", "date"),
    "stripe_payment_id": ("Stripe Payment ID", "rich_text"),
    "delivered_at": ("Delivered At", "date"),
    "followup_sent_at": ("Follow-up Sent At", "date"),
    "notes": ("Notes", "rich_text"),
}


# Status values used in the Customers DB Status select column.
# Keep in sync with scripts/dashboard.py.
STATUS_PAID = "Paid"
STATUS_INTAKE = "Intake Received"
STATUS_IN_PROGRESS = "In Progress"
STATUS_DELIVERED = "Delivered"
STATUS_REFUNDED = "Refunded"


# ---------------------------------------------------------------------------
# Client + data source helpers
# ---------------------------------------------------------------------------


def get_client() -> Client:
    return Client(auth=require_env("NOTION_TOKEN"))


def get_customers_ds_id(client: Client) -> str:
    """Return the data source id for the Customers DB.

    Notion's 2025 API requires queries against a data source, not the DB id.
    The DB envelope lists its data sources; the first one is the canonical one.
    """
    db_id = require_env("NOTION_CUSTOMERS_DB_ID")
    db = client.databases.retrieve(database_id=db_id)
    sources = db.get("data_sources") or []
    if not sources:
        raise RuntimeError(
            f"Customers DB {db_id[:8]}... has no data_sources. "
            "Re-share the database with the integration in Notion."
        )
    return sources[0]["id"]


# ---------------------------------------------------------------------------
# Property building
# ---------------------------------------------------------------------------


def build_properties(fields: dict[str, Any]) -> dict[str, Any]:
    """Convert friendly field dict to Notion properties payload.

    Skips keys we don't know about and skips None / empty-string / empty-list
    values so we never overwrite a column with a blank.
    """
    props: dict[str, Any] = {}
    for key, value in fields.items():
        spec = FIELD_TO_NOTION.get(key)
        if not spec:
            continue
        if value is None or value == "" or value == []:
            continue
        prop_name, prop_type = spec
        if prop_type == "title":
            props[prop_name] = {"title": [{"text": {"content": str(value)[:2000]}}]}
        elif prop_type == "rich_text":
            props[prop_name] = {"rich_text": [{"text": {"content": str(value)[:2000]}}]}
        elif prop_type == "email":
            props[prop_name] = {"email": str(value)}
        elif prop_type == "url":
            props[prop_name] = {"url": str(value)}
        elif prop_type == "select":
            props[prop_name] = {"select": {"name": str(value)}}
        elif prop_type == "checkbox":
            props[prop_name] = {"checkbox": bool(value)}
        elif prop_type == "date":
            iso = value if isinstance(value, str) else _to_iso(value)
            props[prop_name] = {"date": {"start": iso}}
        elif prop_type == "number":
            props[prop_name] = {"number": float(value)}
    return props


def _to_iso(dt: Any) -> str:
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return str(dt)


# ---------------------------------------------------------------------------
# Lookup + upsert
# ---------------------------------------------------------------------------


def find_customer_by_email(
    client: Client,
    ds_id: str,
    email: str,
    since: datetime | None = None,
) -> dict | None:
    """Return the most recent matching row, or None.

    If `since` is given, also require the row was created at/after that time
    (used to scope "is this a recent paying customer?" lookups).
    """
    if not email:
        return None
    filter_clause: dict[str, Any] = {
        "property": "Email",
        "email": {"equals": email.strip().lower()},
    }
    if since is not None:
        filter_clause = {
            "and": [
                filter_clause,
                {
                    "timestamp": "created_time",
                    "created_time": {"on_or_after": since.astimezone(timezone.utc).isoformat()},
                },
            ]
        }
    try:
        resp = client.data_sources.query(
            data_source_id=ds_id,
            filter=filter_clause,
            page_size=5,
            sorts=[{"timestamp": "created_time", "direction": "descending"}],
        )
    except APIResponseError as exc:
        raise RuntimeError(f"Notion query failed: {exc}") from exc
    rows = [r for r in resp.get("results", []) if not (r.get("archived") or r.get("in_trash"))]
    return rows[0] if rows else None


def upsert_customer(
    client: Client,
    ds_id: str,
    fields: dict[str, Any],
    email_for_match: str,
    match_window: timedelta | None = timedelta(hours=48),
) -> tuple[str, str]:
    """Create or update a Customer row, keyed on email.

    Returns (page_id, "created" | "updated").

    If match_window is provided, only rows created within that window are
    treated as "the same customer". This stops us from clobbering an older
    completed customer record when the same email re-purchases.
    """
    since = datetime.now(timezone.utc) - match_window if match_window else None
    existing = find_customer_by_email(client, ds_id, email_for_match, since=since)
    props = build_properties(fields)
    if existing:
        page_id = existing["id"]
        if props:
            try:
                client.pages.update(page_id=page_id, properties=props)
            except APIResponseError as exc:
                raise RuntimeError(f"Notion update failed: {exc}") from exc
        return page_id, "updated"
    try:
        created = client.pages.create(
            parent={"data_source_id": ds_id},
            properties=props,
        )
    except APIResponseError as exc:
        raise RuntimeError(f"Notion create failed: {exc}") from exc
    return created["id"], "created"


def update_customer_fields(
    client: Client,
    page_id: str,
    fields: dict[str, Any],
) -> None:
    props = build_properties(fields)
    if not props:
        return
    try:
        client.pages.update(page_id=page_id, properties=props)
    except APIResponseError as exc:
        raise RuntimeError(f"Notion update failed: {exc}") from exc
