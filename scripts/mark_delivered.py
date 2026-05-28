#!/usr/bin/env python3
"""Mark a LaunchLook audit as Delivered in Notion and log the event.

Updates the Customers DB row (paid audits) or the Free Audit DB row to
Status=Delivered and writes the current timestamp to the Delivered At
date column. Also appends a line to logs/email_sends.jsonl so the
delivery is traceable without opening Notion.

Usage:
    python scripts/mark_delivered.py --slug acme-example-com
    python scripts/mark_delivered.py --email customer@example.com
    python scripts/mark_delivered.py --list-delivered   # show last 20 delivered rows
"""

from __future__ import annotations

import argparse
import datetime
import json
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

from api._lib.notion_helpers import (  # noqa: E402
    STATUS_DELIVERED,
    get_client,
    get_customers_ds_id,
    update_customer_fields,
)

_LOG_PATH = REPO_ROOT / "logs" / "email_sends.jsonl"


def _append_delivery_log(*, slug: str, email: str, tier: str) -> None:
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.datetime.now(datetime.UTC).isoformat(),
            "context": "delivered",
            "slug": slug,
            "tier": tier,
            "email": email,
            "findings_count": None,
            "status": "ok",
            "status_code": None,
        }
        with _LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _prop_text(props: dict, name: str) -> str:
    p = props.get(name) or {}
    for key in ("title", "rich_text"):
        if key in p:
            return "".join(x.get("plain_text", "") for x in (p[key] or [])).strip()
    if "email" in p:
        return (p.get("email") or "").strip()
    if "select" in p and p["select"]:
        return (p["select"].get("name") or "").strip()
    return ""


def mark_delivered_by_page_id(page_id: str, *, slug: str = "", email: str = "", tier: str = "") -> None:
    client = get_client()
    now_iso = datetime.datetime.now(datetime.UTC).isoformat()
    update_customer_fields(
        client,
        page_id,
        {
            "status": STATUS_DELIVERED,
            "delivered_at": now_iso,
        },
    )
    print(f"[mark_delivered] Marked {page_id[:8]}... as Delivered at {now_iso}")
    _append_delivery_log(slug=slug, email=email, tier=tier)


def find_by_slug_or_email(
    slug: str | None,
    email: str | None,
) -> tuple[str, str, str, str] | None:
    """Return (page_id, slug, email, tier) or None."""
    client = get_client()
    ds_id = get_customers_ds_id(client)
    if email:
        resp = client.data_sources.query(
            data_source_id=ds_id,
            filter={"property": "Email", "email": {"equals": email.strip().lower()}},
            sorts=[{"timestamp": "created_time", "direction": "descending"}],
            page_size=5,
        )
    else:
        # No direct slug column — fetch recent rows and match by slug-like title
        resp = client.data_sources.query(
            data_source_id=ds_id,
            page_size=50,
            sorts=[{"timestamp": "created_time", "direction": "descending"}],
        )
    rows = [r for r in resp.get("results", []) if not (r.get("archived") or r.get("in_trash"))]
    for row in rows:
        props = row.get("properties") or {}
        row_email = _prop_text(props, "Email")
        row_tier = _prop_text(props, "Tier")
        if email and row_email.lower() == email.strip().lower():
            return row["id"], slug or row_email.split("@")[0], row_email, row_tier
        if slug:
            # Derive a slug-like string from email+url and compare
            row_url = _prop_text(props, "App URL")
            from scripts.audit_automation.slug import slug_from_email_url  # noqa: PLC0415
            derived = slug_from_email_url(row_email, row_url)
            if derived == slug:
                return row["id"], slug, row_email, row_tier
    return None


def list_delivered(limit: int = 20) -> None:
    client = get_client()
    ds_id = get_customers_ds_id(client)
    resp = client.data_sources.query(
        data_source_id=ds_id,
        filter={"property": "Status", "select": {"equals": STATUS_DELIVERED}},
        sorts=[{"timestamp": "last_edited_time", "direction": "descending"}],
        page_size=limit,
    )
    rows = [r for r in resp.get("results", []) if not (r.get("archived") or r.get("in_trash"))]
    if not rows:
        print("No delivered audits found.")
        return
    print(f"{'Email':35} {'Tier':20} {'Delivered At':26}")
    print("-" * 85)
    for row in rows:
        props = row.get("properties") or {}
        email = _prop_text(props, "Email")
        tier = _prop_text(props, "Tier")
        delivered = (props.get("Delivered At") or {}).get("date") or {}
        delivered_str = (delivered.get("start") or "")[:19]
        print(f"{email:35} {tier:20} {delivered_str:26}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mark a LaunchLook audit as Delivered in Notion")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--slug", help="Customer slug (e.g. acme-example-com)")
    group.add_argument("--email", help="Customer email address")
    group.add_argument("--list-delivered", action="store_true", help="Show recently delivered audits")
    args = parser.parse_args(argv)

    if args.list_delivered:
        list_delivered()
        return 0

    if not args.slug and not args.email:
        parser.print_help()
        return 1

    result = find_by_slug_or_email(args.slug, args.email)
    if not result:
        print(f"[mark_delivered] No matching customer row found for slug={args.slug!r} email={args.email!r}")
        return 1

    page_id, slug, email, tier = result
    mark_delivered_by_page_id(page_id, slug=slug, email=email, tier=tier)
    return 0


if __name__ == "__main__":
    sys.exit(main())
