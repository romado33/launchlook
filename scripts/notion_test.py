"""
notion_test.py — BL-04 smoke test

Verifies Notion API credentials and database access before wiring automation.

Usage:
    python scripts/notion_test.py
    python scripts/notion_test.py --list-customers

Requires in .env:
    NOTION_TOKEN
    NOTION_CUSTOMERS_DB_ID
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


def require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        sys.exit(
            f"ERROR: {key} not set. Copy .env.example to .env and fill in Notion values."
        )
    return val


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list-customers", action="store_true", help="Query first 5 Customers rows"
    )
    args = parser.parse_args()

    try:
        from notion_client import Client
    except ImportError:
        sys.exit("ERROR: pip install -e .")

    notion = Client(auth=require_env("NOTION_TOKEN"))

    # Verify token works
    me = notion.users.me()
    print(f"OK — connected as integration: {me.get('name', me.get('id'))}")

    db_id = os.getenv("NOTION_CUSTOMERS_DB_ID")
    if not db_id:
        print(
            "WARN: NOTION_CUSTOMERS_DB_ID not set — skipping database query.",
            file=sys.stderr,
        )
        print(
            "Create Customers DB in Notion, import templates/notion/customers-db.csv, share with integration.",
            file=sys.stderr,
        )
        return 0

    db = notion.databases.retrieve(database_id=db_id)
    title = ""
    if db.get("title"):
        title = db["title"][0].get("plain_text", db_id)
    print(f"OK — database: {title} ({db_id[:8]}...)")

    if args.list_customers:
        data_sources = db.get("data_sources", [])
        if not data_sources:
            print(
                "ERROR: database has no data_sources (newer Notion API). Re-share the DB with the integration.",
                file=sys.stderr,
            )
            return 1
        ds_id = data_sources[0]["id"]
        results = notion.data_sources.query(data_source_id=ds_id, page_size=5)
        rows = results.get("results", [])
        print(f"Rows returned: {len(rows)}")
        for row in rows:
            props = row.get("properties", {})
            name_prop = props.get("Name", {}).get("title", [])
            name = name_prop[0]["plain_text"] if name_prop else "(no name)"
            print(f"  - {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
