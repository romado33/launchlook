"""Thin Notion lookup for prior free-audit rows used by the dedup flow.

Why a separate module
---------------------
``scripts/ai_audit/pipeline.py`` already pulls in capture, prescreen,
HTML extract, LLM, and security-lite. Adding direct Notion lookups
there would make it harder to test and harder for future workers to
swap out the storage backend. This module owns:

* ``load_excluded_fingerprints(...)`` -- looks up the most recent
  free-audit row for ``(email, url, window_days)``, parses the stored
  ``Finding Fingerprints`` rich-text field, and returns
  ``(fingerprints, prior_summaries, row_id)``. Empty when no row is
  found.
* ``persist_free_audit_fingerprints(...)`` -- after the offline free-
  audit pipeline produces the 3 findings, this writes their fingerprints
  back to the same Notion row so the next paid Starter audit can dedup.

Per ``docs/SIMPLICITY-GUARDRAILS.md`` section 6 the dedup mechanism is
never customer-visible; this module only logs and writes hashes that
stay inside the Notion DB Rob sees.

Failure mode
------------
Everything here degrades to "no-op" when env vars are missing, when
``notion_client`` isn't installed (CI / minimal local runs), or when the
DB query fails. The dedup is a soft constraint per the task spec; the
pipeline must not refuse to run because Notion is unavailable.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

# Mirrors the schema in api/free-audit.py / docs/FREE-AUDIT-WORKFLOW.md.
PROP_EMAIL = "Email"
PROP_URL = "URL"
PROP_FINGERPRINTS = "Finding Fingerprints"
PROP_SUMMARIES = "Finding Summaries"  # optional rich_text; used only if present
PROP_STATUS = "Status"

DEFAULT_WINDOW_DAYS = 90
FINGERPRINT_SEPARATOR = ";"


def _get_client():
    """Return a notion_client.Client or None when unavailable."""
    token = os.getenv("NOTION_TOKEN")
    if not token:
        return None
    try:
        from notion_client import Client  # noqa: WPS433 -- optional dep
    except ImportError:
        print(
            "[dedup] WARN: notion-client not installed; skipping prior-audit lookup",
            file=sys.stderr,
        )
        return None
    return Client(auth=token)


def _get_ds_id(client) -> str | None:
    db_id = os.getenv("NOTION_FREE_AUDIT_DB_ID")
    if not db_id:
        return None
    try:
        db = client.databases.retrieve(database_id=db_id)
    except Exception as exc:  # noqa: BLE001
        print(f"[dedup] WARN: NOTION_FREE_AUDIT_DB_ID retrieve failed: {exc}", file=sys.stderr)
        return None
    sources = db.get("data_sources") or []
    if not sources:
        print(
            "[dedup] WARN: free-audit DB has no data sources; re-share with the integration.",
            file=sys.stderr,
        )
        return None
    return sources[0]["id"]


def _rich_text_value(prop: dict[str, Any] | None) -> str:
    """Pull plain text out of a Notion rich_text property."""
    if not prop:
        return ""
    parts = prop.get("rich_text") or []
    return "".join(p.get("plain_text") or "" for p in parts)


def load_excluded_fingerprints(
    *,
    email: str,
    url: str,
    window_days: int = DEFAULT_WINDOW_DAYS,
    now: datetime | None = None,
) -> tuple[list[str], list[str], str | None]:
    """Return (fingerprints, prior_summaries, row_id) for a recent free audit.

    * Same email and same URL host within the lookback window -> hit.
    * No hit -> empty tuples and None.
    * Notion misconfigured or query failed -> empty tuples and None
      (logs a warning; dedup is a soft constraint).
    """
    if not email or not url:
        return [], [], None
    email_norm = email.strip().lower()
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return [], [], None

    client = _get_client()
    if client is None:
        return [], [], None
    ds_id = _get_ds_id(client)
    if not ds_id:
        return [], [], None

    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=window_days)
    try:
        resp = client.data_sources.query(
            data_source_id=ds_id,
            filter={
                "and": [
                    {"property": PROP_EMAIL, "email": {"equals": email_norm}},
                    {"timestamp": "created_time", "created_time": {"on_or_after": cutoff.isoformat()}},
                ]
            },
            sorts=[{"timestamp": "created_time", "direction": "descending"}],
            page_size=10,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[dedup] WARN: free-audit lookup failed: {exc}", file=sys.stderr)
        return [], [], None

    for row in resp.get("results", []):
        if row.get("archived") or row.get("in_trash"):
            continue
        props = row.get("properties", {})
        existing_url = (props.get(PROP_URL) or {}).get("url") or ""
        if not existing_url:
            continue
        existing_host = (urlparse(existing_url).hostname or "").lower()
        if existing_host != host:
            continue
        raw_fp = _rich_text_value(props.get(PROP_FINGERPRINTS))
        fingerprints = [fp.strip() for fp in raw_fp.split(FINGERPRINT_SEPARATOR) if fp.strip()]
        raw_summaries = _rich_text_value(props.get(PROP_SUMMARIES))
        # Summaries are optional and stored on a separate rich-text line
        # per finding; split on newline so blank rows degrade to empty.
        summaries = [s.strip() for s in raw_summaries.split("\n") if s.strip()]
        return fingerprints, summaries, row.get("id")
    return [], [], None


def persist_free_audit_fingerprints(
    *,
    row_id: str,
    fingerprints: list[str],
    summaries: list[str] | None = None,
) -> bool:
    """Write the 3 free-audit fingerprints (and optional summaries) back.

    Called by the offline free-audit run after Rob approves the 3
    findings in the audit UI. Returns True on success, False on any
    failure (logged; soft constraint).
    """
    if not row_id or not fingerprints:
        return False
    client = _get_client()
    if client is None:
        return False
    payload: dict[str, Any] = {
        PROP_FINGERPRINTS: {
            "rich_text": [
                {"text": {"content": FINGERPRINT_SEPARATOR.join(fingerprints)[:2000]}}
            ]
        },
    }
    if summaries:
        payload[PROP_SUMMARIES] = {
            "rich_text": [{"text": {"content": "\n".join(summaries)[:2000]}}]
        }
    try:
        client.pages.update(page_id=row_id, properties=payload)
    except Exception as exc:  # noqa: BLE001
        print(f"[dedup] WARN: free-audit fingerprint persist failed: {exc}", file=sys.stderr)
        return False
    return True
