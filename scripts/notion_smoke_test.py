"""
notion_smoke_test.py — end-to-end integration check (Tier 1 reads + Tier 2 writes).

Runs through:
  1. Auth + integration identity
  2. Each connected DB / page is retrievable
  3. Findings DB row count check
  4. Read a known finding (FL-001) by filter
  5. List children of Report Templates parent
  6. WRITE: create a temporary Customer row exercising every property type
  7. READ-BACK: retrieve the row and verify properties land correctly
  8. UPDATE: change Tier from Starter to Full
  9. ARCHIVE: delete the test row so the DB stays clean

Required env (load from .env):
    NOTION_TOKEN
    NOTION_CUSTOMERS_DB_ID
    NOTION_FINDINGS_DB_ID
    NOTION_OUTREACH_DB_ID         (optional; tested if set)
    NOTION_REPORTS_PARENT_PAGE_ID (optional; tested if set)

Exit code 0 = all checks passed. Non-zero = at least one failed.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Pretty output helpers
# ---------------------------------------------------------------------------

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
INFO = "[INFO]"


def out(prefix: str, msg: str) -> None:
    print(f"  {prefix} {msg}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def main() -> int:
    try:
        from notion_client import Client
        from notion_client.errors import APIResponseError
    except ImportError:
        sys.exit("ERROR: pip install notion-client>=2.7")

    token = os.getenv("NOTION_TOKEN")
    if not token:
        sys.exit("ERROR: NOTION_TOKEN not set in .env")

    notion = Client(auth=token)
    fails: list[str] = []

    # -----------------------------------------------------------------------
    print("\n=== Tier 1: reads ===\n")

    # 1. Auth
    print("1. Auth + identity")
    try:
        me = notion.users.me()
        name = me.get("name") or me.get("bot", {}).get("owner", {}).get("user", {}).get("name", me.get("id"))
        out(PASS, f"connected as: {name}")
    except APIResponseError as e:
        out(FAIL, f"auth failed: {e}")
        return 1

    # 2. Each connected DB / page is retrievable
    print("\n2. Connected DBs / pages retrievable")
    db_targets = [
        ("Customers DB", "NOTION_CUSTOMERS_DB_ID", "database"),
        ("Findings DB", "NOTION_FINDINGS_DB_ID", "database"),
        ("Outreach DB", "NOTION_OUTREACH_DB_ID", "database"),
        ("Reports parent page", "NOTION_REPORTS_PARENT_PAGE_ID", "page"),
        ("Crawler Wishlist page", "NOTION_CRAWLER_WISHLIST_PAGE_ID", "page"),
    ]
    retrieved: dict[str, dict[str, Any]] = {}
    for label, env_key, kind in db_targets:
        target_id = os.getenv(env_key)
        if not target_id:
            out(SKIP, f"{label} ({env_key} not set)")
            continue
        try:
            if kind == "database":
                obj = notion.databases.retrieve(database_id=target_id)
            else:
                obj = notion.pages.retrieve(page_id=target_id)
            retrieved[label] = obj
            out(PASS, f"{label} ({target_id[:8]}...)")
        except APIResponseError as e:
            out(FAIL, f"{label}: {e.code} — {e}")
            fails.append(f"retrieve {label}")

    # 3. Findings DB row count
    print("\n3. Findings DB row count >= 30")
    findings_db = retrieved.get("Findings DB")
    if not findings_db:
        out(SKIP, "Findings DB not retrieved earlier")
    else:
        try:
            ds_id = findings_db["data_sources"][0]["id"]
            results: list[dict] = []
            cursor = None
            while True:
                resp = notion.data_sources.query(
                    data_source_id=ds_id,
                    page_size=100,
                    start_cursor=cursor,
                )
                results.extend(resp.get("results", []))
                if not resp.get("has_more"):
                    break
                cursor = resp.get("next_cursor")
            count = len(results)
            if count >= 30:
                out(PASS, f"Findings DB has {count} rows")
            else:
                out(FAIL, f"Findings DB has only {count} rows (expected >= 30)")
                fails.append("findings row count")
        except (APIResponseError, KeyError, IndexError) as e:
            out(FAIL, f"query failed: {e}")
            fails.append("findings query")

    # 4. Filter for FL-001 and verify properties
    print("\n4. Read FL-001 by filter, verify shape")
    if findings_db:
        try:
            ds_id = findings_db["data_sources"][0]["id"]
            resp = notion.data_sources.query(
                data_source_id=ds_id,
                filter={"property": "Name", "title": {"equals": "FL-001"}},
                page_size=1,
            )
            rows = resp.get("results", [])
            if not rows:
                out(FAIL, "no row matched Name='FL-001' (try checking the title column name)")
                fails.append("fl-001 lookup")
            else:
                props = rows[0].get("properties", {})
                expected = ["Name", "Finding Name", "Category", "Severity"]
                missing = [p for p in expected if p not in props]
                if missing:
                    out(FAIL, f"missing properties on FL-001: {missing}")
                    fails.append("fl-001 properties")
                else:
                    out(PASS, "FL-001 found with all expected properties")
        except APIResponseError as e:
            out(FAIL, f"filter query failed: {e}")
            fails.append("fl-001 query")

    # 5. List children of Reports parent page
    print("\n5. Reports parent page children")
    reports_page = retrieved.get("Reports parent page")
    if not reports_page:
        out(SKIP, "NOTION_REPORTS_PARENT_PAGE_ID not set or page unreachable")
    else:
        try:
            children = notion.blocks.children.list(block_id=reports_page["id"]).get("results", [])
            out(PASS, f"{len(children)} child block(s) under Reports parent")
            for child in children[:5]:
                ctype = child.get("type", "?")
                title = ""
                if ctype == "child_page":
                    title = child.get("child_page", {}).get("title", "")
                elif ctype == "child_database":
                    title = child.get("child_database", {}).get("title", "")
                if title:
                    out(INFO, f"  - {ctype}: {title}")
        except APIResponseError as e:
            out(FAIL, f"children list failed: {e}")
            fails.append("reports children")

    # -----------------------------------------------------------------------
    print("\n=== Tier 2: write / read-back / update / archive ===\n")

    customers_db = retrieved.get("Customers DB")
    if not customers_db:
        out(SKIP, "Customers DB not retrieved — skipping write tests")
        return summary(fails)

    customers_ds_id = customers_db["data_sources"][0]["id"]

    test_marker = f"SMOKE TEST {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"

    # 6. Create
    print("6. Create temporary Customer row (write permission)")
    try:
        new_props = {
            "Name": {"title": [{"text": {"content": test_marker}}]},
            "Email": {"email": "smoke-test@launchlook.app"},
            "App URL": {"url": "https://example.com/smoke"},
            "App Name": {"rich_text": [{"text": {"content": "Smoke App"}}]},
            "Platform": {"select": {"name": "Lovable"}},
            "Tier": {"select": {"name": "Starter Package"}},
            "Status": {"select": {"name": "Paid"}},
            "Payment Date": {"date": {"start": datetime.now(timezone.utc).date().isoformat()}},
            "Intake Received": {"checkbox": False},
            "Notes": {"rich_text": [{"text": {"content": "Auto-deleted by smoke test."}}]},
        }
        created = notion.pages.create(
            parent={"data_source_id": customers_ds_id},
            properties=new_props,
        )
        page_id = created["id"]
        out(PASS, f"created page {page_id[:8]}...")
    except APIResponseError as e:
        out(FAIL, f"create failed: {e.code} — {e}")
        fails.append("create row")
        return summary(fails)

    # 7. Read back
    print("\n7. Retrieve and verify properties")
    try:
        # Small delay so eventual consistency is on our side
        time.sleep(0.5)
        page = notion.pages.retrieve(page_id=page_id)
        props = page["properties"]

        title_text = props["Name"]["title"][0]["plain_text"] if props["Name"]["title"] else ""
        email = props["Email"]["email"]
        tier = props["Tier"]["select"]["name"] if props["Tier"]["select"] else None
        date_val = props["Payment Date"]["date"]["start"] if props["Payment Date"]["date"] else None

        ok = title_text == test_marker and email == "smoke-test@launchlook.app" and tier == "Starter Package" and date_val
        if ok:
            out(PASS, f"all properties round-tripped: title, email, tier={tier}, date={date_val}")
        else:
            out(FAIL, f"property mismatch: title={title_text!r}, email={email!r}, tier={tier!r}, date={date_val!r}")
            fails.append("read-back")
    except (APIResponseError, KeyError, IndexError) as e:
        out(FAIL, f"read-back failed: {e}")
        fails.append("read-back")

    # 8. Update
    print("\n8. Update Tier: Starter Package -> Full Package")
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "Tier": {"select": {"name": "Full Package"}},
                "Status": {"select": {"name": "In progress"}},
            },
        )
        page = notion.pages.retrieve(page_id=page_id)
        new_tier = page["properties"]["Tier"]["select"]["name"]
        if new_tier == "Full Package":
            out(PASS, f"updated Tier -> {new_tier}")
        else:
            out(FAIL, f"update did not stick: Tier={new_tier}")
            fails.append("update")
    except APIResponseError as e:
        out(FAIL, f"update failed: {e}")
        fails.append("update")

    # 9. Archive
    print("\n9. Archive (soft delete)")
    try:
        notion.pages.update(page_id=page_id, archived=True)
        page = notion.pages.retrieve(page_id=page_id)
        # In_trash is the new field name in 2025+ API; archived is the legacy one
        is_gone = page.get("in_trash") is True or page.get("archived") is True
        if is_gone:
            out(PASS, "row archived — DB stays clean")
        else:
            out(FAIL, "archive did not register")
            fails.append("archive")
    except APIResponseError as e:
        out(FAIL, f"archive failed: {e}")
        fails.append("archive")

    return summary(fails)


def summary(fails: list[str]) -> int:
    print()
    print("=" * 60)
    if not fails:
        print("ALL CHECKS PASSED. Tally -> Notion automation is unblocked.")
        return 0
    print(f"FAILURES ({len(fails)}):")
    for f in fails:
        print(f"  - {f}")
    print("=" * 60)
    return 1


if __name__ == "__main__":
    sys.exit(main())
