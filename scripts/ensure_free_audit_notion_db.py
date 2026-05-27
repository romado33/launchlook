#!/usr/bin/env python3
"""Verify or create the Notion Free Audit Requests database.

Usage:
    python scripts/ensure_free_audit_notion_db.py
    python scripts/ensure_free_audit_notion_db.py --create-if-missing

Exits 0 when NOTION_FREE_AUDIT_DB_ID is set and the integration can read it.
Exits 1 with actionable errors otherwise.

After --create-if-missing, paste the printed ID into:
  - local .env  NOTION_FREE_AUDIT_DB_ID
  - Vercel      Project Settings -> Environment Variables (Production)
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

STATUS_OPTIONS = [
    "queued",
    "processing",
    "draft_ready",
    "failed",
    "delivered",
    "skipped",
    "abuse",
    # legacy alias — treat same as draft_ready in ops
    "processed",
]
SOURCE_OPTIONS = ["index", "webflow", "api"]
PLATFORM_OPTIONS = ["vibe-coder", "webflow"]


def _select_options(names: list[str]) -> dict:
    return {"select": {"options": [{"name": n} for n in names]}}


def _schema() -> dict:
    return {
        "Request": {"title": {}},
        "Email": {"email": {}},
        "URL": {"url": {}},
        "IP": {"rich_text": {}},
        "Status": _select_options(STATUS_OPTIONS),
        "Source": _select_options(SOURCE_OPTIONS),
        "Platform": _select_options(PLATFORM_OPTIONS),
        "Finding Fingerprints": {"rich_text": {}},
        "Finding Summaries": {"rich_text": {}},
    }


def _verify(client, db_id: str) -> tuple[bool, str]:
    try:
        db = client.databases.retrieve(database_id=db_id)
    except Exception as exc:  # noqa: BLE001
        return False, f"retrieve failed: {exc}"

    title = ""
    if db.get("title"):
        title = db["title"][0].get("plain_text", "")
    sources = db.get("data_sources") or []
    if not sources:
        return False, "database has no data_sources (re-share with LaunchLook Ops integration)"
    return True, f'"{title}" OK (data_source {sources[0]["id"][:8]}...)'


def _pick_parent_page_id(client) -> str:
    for key in ("NOTION_FREE_AUDIT_PARENT_PAGE_ID", "NOTION_CRAWLER_WISHLIST_PAGE_ID"):
        page_id = (os.getenv(key) or "").strip()
        if not page_id:
            continue
        try:
            client.pages.retrieve(page_id=page_id)
            return page_id
        except Exception:
            continue
    raise RuntimeError(
        "No parent page reachable. Set NOTION_CRAWLER_WISHLIST_PAGE_ID or "
        "NOTION_FREE_AUDIT_PARENT_PAGE_ID to a page shared with the integration."
    )


def _create_db(client) -> str:
    parent_id = _pick_parent_page_id(client)
    # Notion API 2025-09-03+: schema belongs under initial_data_source, not top-level.
    created = client.databases.create(
        parent={"type": "page_id", "page_id": parent_id},
        title=[{"type": "text", "text": {"content": "Free Audit Requests"}}],
        initial_data_source={"properties": _schema()},
    )
    db_id = created["id"]
    ok, detail = _verify(client, db_id)
    if not ok:
        raise RuntimeError(f"created database but verify failed: {detail}")
    return db_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create-if-missing",
        action="store_true",
        help="Create the database when the configured ID is missing or invalid.",
    )
    args = parser.parse_args()

    token = os.getenv("NOTION_TOKEN")
    if not token:
        print("ERROR: NOTION_TOKEN not set", file=sys.stderr)
        return 1

    try:
        from notion_client import Client
    except ImportError:
        print("ERROR: pip install notion-client", file=sys.stderr)
        return 1

    client = Client(auth=token)
    db_id = (os.getenv("NOTION_FREE_AUDIT_DB_ID") or "").strip()

    if db_id:
        ok, detail = _verify(client, db_id)
        if ok:
            print(f"OK  NOTION_FREE_AUDIT_DB_ID={db_id}  ({detail})")
            return 0
        print(f"WARN  configured ID invalid: {detail}", file=sys.stderr)
        if not args.create_if_missing:
            print(
                "Run with --create-if-missing to create a replacement database.",
                file=sys.stderr,
            )
            return 1
    elif not args.create_if_missing:
        print("ERROR: NOTION_FREE_AUDIT_DB_ID not set", file=sys.stderr)
        return 1

    print("Creating Free Audit Requests database...")
    try:
        new_id = _create_db(client)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: create failed: {exc}", file=sys.stderr)
        return 1

    print(f"CREATED  NOTION_FREE_AUDIT_DB_ID={new_id}")
    print(f"Notion URL: https://www.notion.so/{new_id.replace('-', '')}")
    print("Add that ID to .env and Vercel, then redeploy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
