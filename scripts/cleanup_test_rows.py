#!/usr/bin/env python3
"""Delete stale test rows from the Notion Customers DB.

Searches for known test-only emails and archives matching rows after
interactive confirmation.  Does NOT touch rows with status "Delivered".

Usage:
    python scripts/cleanup_test_rows.py
"""

from __future__ import annotations

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

# ---------------------------------------------------------------------------
# Test emails and their deletion rules
# ---------------------------------------------------------------------------
# Each entry: (email, allow_all_statuses)
# allow_all_statuses=False → skip rows with status "Delivered"
# allow_all_statuses=True  → include every status

TEST_EMAIL_RULES: list[tuple[str, bool]] = [
    ("romado33@gmail.com", False),       # only In Progress / Paid, skip Delivered
    ("tally-test@example.com", True),    # all statuses
    ("stripe-test@example.com", True),   # all statuses
]

SKIP_STATUSES = {"Delivered"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _created_date(page: dict) -> str:
    ct = page.get("created_time", "")
    return ct[:10] if ct else "unknown"


def _get_all_rows_for_email(client, ds_id: str, email: str) -> list[dict]:
    """Return all non-archived rows matching email (case-insensitive)."""
    rows: list[dict] = []
    cursor = None
    while True:
        kwargs: dict = {
            "data_source_id": ds_id,
            "filter": {
                "property": "Email",
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    client = get_client()
    ds_id = get_customers_ds_id(client)

    candidates: list[dict] = []

    for email, allow_all in TEST_EMAIL_RULES:
        rows = _get_all_rows_for_email(client, ds_id, email)
        for row in rows:
            status = _prop_select(row["properties"], "Status")
            if not allow_all and status in SKIP_STATUSES:
                print(f"  [skip] {email}  {status}  {_created_date(row)}  (Delivered — keeping)")
                continue
            candidates.append(row)

    if not candidates:
        print("No test rows found.")
        return

    print(f"\nFound {len(candidates)} test row(s) to delete:")
    for row in candidates:
        props = row["properties"]
        email_val = _prop_text(props, "Email") or _prop_select(props, "Email")
        if not email_val:
            email_val = (props.get("Email") or {}).get("email") or "(no email)"
        status = _prop_select(props, "Status") or "(no status)"
        created = _created_date(row)
        print(f"  - {email_val:<35}  {status:<20}  {created}")

    print()
    answer = input("Delete these? [y/N]: ").strip().lower()
    if answer != "y":
        print("Aborted — no rows deleted.")
        return

    deleted = 0
    for row in candidates:
        page_id = row["id"]
        client.pages.update(page_id=page_id, archived=True)
        deleted += 1

    print(f"Deleted {deleted} row(s).")


if __name__ == "__main__":
    main()
