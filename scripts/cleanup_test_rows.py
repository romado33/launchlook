#!/usr/bin/env python3
"""Archive stale test rows from LaunchLook Notion operational databases.

Targets:
  - Customers (NOTION_CUSTOMERS_DB_ID)
  - Free Audit Requests (NOTION_FREE_AUDIT_DB_ID)
  - Confidence Checks (NOTION_CONFIDENCE_CHECK_DB_ID)

Does NOT touch Findings (product library) or Outreach.

Usage:
    python scripts/cleanup_test_rows.py              # list + confirm
    python scripts/cleanup_test_rows.py --dry-run    # list only
    python scripts/cleanup_test_rows.py --yes        # archive without prompt
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from api._lib.notion_helpers import get_client, get_customers_ds_id  # noqa: E402

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError
except ImportError:
    sys.exit("ERROR: pip install notion-client>=2.2 (see requirements-automation.txt)")


# ---------------------------------------------------------------------------
# Test emails and their deletion rules (Customers DB only)
# ---------------------------------------------------------------------------
# Each entry: (email, allow_all_statuses)
# allow_all_statuses=False → skip rows with status "Delivered"

TEST_EMAIL_RULES: list[tuple[str, bool]] = [
    ("romado33@gmail.com", False),
    ("tally-test@example.com", True),
    ("stripe-test@example.com", True),
    ("smoke-test@launchlook.app", True),
    ("stranger+launchlook-smoke-test@launchlook.app", True),
]

SKIP_STATUSES = {"Delivered"}

# Free Audit + Confidence Check: archive all rows for these emails.
TEST_EMAILS_ALL_STATUSES = {email for email, _ in TEST_EMAIL_RULES}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ds_id_from_db(client: Client, db_id: str, label: str) -> str | None:
    try:
        db = client.databases.retrieve(database_id=db_id)
    except APIResponseError as exc:
        if exc.code in ("object_not_found", "validation_error"):
            print(f"  [skip] {label} — not found or not shared with integration ({db_id[:8]}...)")
            return None
        raise
    sources = db.get("data_sources") or []
    if not sources:
        print(f"  [skip] {label} — no data_sources ({db_id[:8]}...)")
        return None
    return sources[0]["id"]


def _prop_text(props: dict, name: str) -> str:
    p = props.get(name) or {}
    for key in ("title", "rich_text"):
        items = p.get(key) or []
        if items:
            return items[0].get("plain_text", "")
    v = p.get("email") or p.get("url") or ""
    return str(v) if v else ""


def _prop_select(props: dict, name: str) -> str:
    sel = (props.get(name) or {}).get("select") or {}
    return sel.get("name", "")


def _prop_email(props: dict, name: str) -> str:
    return str((props.get(name) or {}).get("email") or "")


def _created_date(page: dict) -> str:
    ct = page.get("created_time", "")
    return ct[:10] if ct else "unknown"


def _query_by_email(client: Client, ds_id: str, email_prop: str, email: str) -> list[dict]:
    """Return all non-archived rows matching email (case-insensitive)."""
    rows: list[dict] = []
    cursor = None
    while True:
        kwargs: dict = {
            "data_source_id": ds_id,
            "filter": {
                "property": email_prop,
                "email": {"equals": email.strip().lower()},
            },
            "page_size": 100,
            "sorts": [{"timestamp": "created_time", "direction": "descending"}],
        }
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = client.data_sources.query(**kwargs)
        for r in resp.get("results", []):
            if not (r.get("archived") or r.get("in_trash")):
                rows.append(r)
        if resp.get("has_more") and resp.get("next_cursor"):
            cursor = resp["next_cursor"]
        else:
            break
    return rows


def _query_smoke_title_rows(client: Client, ds_id: str) -> list[dict]:
    """Customers rows whose Name/title starts with SMOKE TEST."""
    rows: list[dict] = []
    cursor = None
    while True:
        kwargs: dict = {
            "data_source_id": ds_id,
            "filter": {
                "property": "Name",
                "title": {"starts_with": "SMOKE TEST"},
            },
            "page_size": 100,
        }
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = client.data_sources.query(**kwargs)
        for r in resp.get("results", []):
            if not (r.get("archived") or r.get("in_trash")):
                rows.append(r)
        if resp.get("has_more") and resp.get("next_cursor"):
            cursor = resp["next_cursor"]
        else:
            break
    return rows


def _archive_rows(client: Client, rows: list[dict]) -> int:
    archived = 0
    for row in rows:
        try:
            client.pages.update(page_id=row["id"], archived=True)
            archived += 1
        except APIResponseError as exc:
            print(f"  [error] failed to archive {row['id'][:8]}...: {exc}")
    return archived


def _row_label(row: dict, *, email_prop: str = "Email", status_prop: str = "Status") -> str:
    props = row["properties"]
    email_val = _prop_email(props, email_prop) or _prop_text(props, email_prop)
    if not email_val:
        email_val = _prop_text(props, "Name") or _prop_text(props, "Request") or "(no email)"
    status = _prop_select(props, status_prop) or "(no status)"
    return f"{email_val:<45}  {status:<18}  {_created_date(row)}"


# ---------------------------------------------------------------------------
# Per-database collectors
# ---------------------------------------------------------------------------


def collect_customers(client: Client) -> list[dict]:
    ds_id = get_customers_ds_id(client)
    seen: set[str] = set()
    candidates: list[dict] = []

    for email, allow_all in TEST_EMAIL_RULES:
        for row in _query_by_email(client, ds_id, "Email", email):
            if row["id"] in seen:
                continue
            status = _prop_select(row["properties"], "Status")
            if not allow_all and status in SKIP_STATUSES:
                print(f"  [skip] Customers  {_row_label(row)}  (Delivered — keeping)")
                continue
            seen.add(row["id"])
            candidates.append(row)

    for row in _query_smoke_title_rows(client, ds_id):
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        candidates.append(row)

    return candidates


def collect_free_audit(client: Client) -> list[dict]:
    db_id = os.getenv("NOTION_FREE_AUDIT_DB_ID", "").strip()
    if not db_id:
        print("  [skip] Free Audit DB — NOTION_FREE_AUDIT_DB_ID not set")
        return []
    ds_id = _ds_id_from_db(client, db_id, "Free Audit DB")
    if not ds_id:
        return []
    seen: set[str] = set()
    candidates: list[dict] = []
    for email in sorted(TEST_EMAILS_ALL_STATUSES):
        for row in _query_by_email(client, ds_id, "Email", email):
            if row["id"] not in seen:
                seen.add(row["id"])
                candidates.append(row)
    return candidates


def collect_confidence_checks(client: Client) -> list[dict]:
    db_id = os.getenv("NOTION_CONFIDENCE_CHECK_DB_ID", "").strip()
    if not db_id:
        print("  [skip] Confidence Check DB — NOTION_CONFIDENCE_CHECK_DB_ID not set")
        return []
    ds_id = _ds_id_from_db(client, db_id, "Confidence Check DB")
    if not ds_id:
        return []
    seen: set[str] = set()
    candidates: list[dict] = []
    for email in sorted(TEST_EMAILS_ALL_STATUSES):
        for row in _query_by_email(client, ds_id, "customer_email", email):
            if row["id"] not in seen:
                seen.add(row["id"])
                candidates.append(row)
    return candidates


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Archive test rows from Notion operational DBs.")
    parser.add_argument("--dry-run", action="store_true", help="List candidates only.")
    parser.add_argument("--yes", action="store_true", help="Archive without confirmation.")
    args = parser.parse_args()

    client = get_client()

    sections: list[tuple[str, list[dict]]] = [
        ("Customers", collect_customers(client)),
        ("Free Audit Requests", collect_free_audit(client)),
        ("Confidence Checks", collect_confidence_checks(client)),
    ]

    total = sum(len(rows) for _, rows in sections)
    if total == 0:
        print("No test rows found.")
        return

    print(f"\nFound {total} test row(s) to archive:\n")
    for label, rows in sections:
        if not rows:
            continue
        print(f"  [{label}] ({len(rows)})")
        for row in rows:
            email_prop = "customer_email" if label == "Confidence Checks" else "Email"
            print(f"    - {_row_label(row, email_prop=email_prop)}")
        print()

    if args.dry_run:
        print("Dry run — no rows archived.")
        return

    if not args.yes:
        answer = input("Archive these rows? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted — no rows archived.")
            return

    archived_total = 0
    for label, rows in sections:
        if not rows:
            continue
        n = _archive_rows(client, rows)
        archived_total += n
        print(f"  [{label}] archived {n} row(s)")

    print(f"\nDone — archived {archived_total} row(s).")


if __name__ == "__main__":
    main()
