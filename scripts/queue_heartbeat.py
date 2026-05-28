#!/usr/bin/env python3
"""Emit a queue-state email to the founder (run weekly, or on demand).

Queries Notion for:
  - Free audit rows in queued / processing / draft_ready status
  - Paid customer rows that are not yet Delivered
  - Jobs delivered this week

Sends a plain summary to ADMIN_EMAIL. Also serves as a scheduler
liveness check: if this email stops arriving on Sunday mornings,
the scheduled task is dead.

Usage:
    python scripts/queue_heartbeat.py           # send the email
    python scripts/queue_heartbeat.py --dry-run # print to console, no email
"""

from __future__ import annotations

import argparse
import datetime
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
    STATUS_IN_PROGRESS,
    STATUS_INTAKE,
    STATUS_PAID,
    get_client,
    get_customers_ds_id,
)
from scripts.audit_automation.notify import send_plain_admin_email  # noqa: E402


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


def _get_free_audit_ds_id(client) -> str | None:
    import os
    db_id = os.getenv("NOTION_FREE_AUDIT_DB_ID", "").strip()
    if not db_id:
        return None
    db = client.databases.retrieve(database_id=db_id)
    sources = db.get("data_sources") or []
    return sources[0]["id"] if sources else None


def build_report() -> tuple[str, str]:
    """Return (html_body, text_body) for the heartbeat email."""
    client = get_client()
    now = datetime.datetime.now(datetime.UTC)
    week_start = (now - datetime.timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # ---- Free audit queue ----
    free_rows: list[dict] = []
    free_ds = _get_free_audit_ds_id(client)
    if free_ds:
        resp = client.data_sources.query(
            data_source_id=free_ds,
            filter={
                "or": [
                    {"property": "Status", "select": {"equals": "queued"}},
                    {"property": "Status", "select": {"equals": "processing"}},
                    {"property": "Status", "select": {"equals": "draft_ready"}},
                ]
            },
            sorts=[{"timestamp": "created_time", "direction": "ascending"}],
            page_size=50,
        )
        free_rows = [r for r in resp.get("results", []) if not (r.get("archived") or r.get("in_trash"))]

    # ---- Paid queue (not yet delivered) ----
    cust_ds = get_customers_ds_id(client)
    resp = client.data_sources.query(
        data_source_id=cust_ds,
        filter={
            "or": [
                {"property": "Status", "select": {"equals": STATUS_PAID}},
                {"property": "Status", "select": {"equals": STATUS_INTAKE}},
                {"property": "Status", "select": {"equals": STATUS_IN_PROGRESS}},
            ]
        },
        sorts=[{"timestamp": "created_time", "direction": "ascending"}],
        page_size=50,
    )
    paid_rows = [r for r in resp.get("results", []) if not (r.get("archived") or r.get("in_trash"))]

    # ---- Delivered this week ----
    resp = client.data_sources.query(
        data_source_id=cust_ds,
        filter={
            "and": [
                {"property": "Status", "select": {"equals": STATUS_DELIVERED}},
                {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {"on_or_after": week_start.isoformat()},
                },
            ]
        },
        page_size=50,
    )
    delivered_rows = [r for r in resp.get("results", []) if not (r.get("archived") or r.get("in_trash"))]

    # ---- Build report ----
    lines_text: list[str] = [
        f"Queue heartbeat — {now.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"FREE AUDIT QUEUE ({len(free_rows)} pending)",
    ]
    for row in free_rows:
        props = row.get("properties") or {}
        email = _prop_text(props, "Email")
        status = _prop_text(props, "Status")
        created = (row.get("created_time") or "")[:10]
        lines_text.append(f"  {status:12} {email:35} (created {created})")

    lines_text += [
        "",
        f"PAID QUEUE ({len(paid_rows)} pending)",
    ]
    for row in paid_rows:
        props = row.get("properties") or {}
        email = _prop_text(props, "Email")
        tier = _prop_text(props, "Tier")
        status = _prop_text(props, "Status")
        created = (row.get("created_time") or "")[:10]
        lines_text.append(f"  {status:20} {tier:20} {email:35} (since {created})")

    lines_text += [
        "",
        f"DELIVERED THIS WEEK ({len(delivered_rows)})",
    ]
    for row in delivered_rows:
        props = row.get("properties") or {}
        email = _prop_text(props, "Email")
        tier = _prop_text(props, "Tier")
        lines_text.append(f"  {tier:20} {email}")

    lines_text += ["", "-- LaunchLook Automation"]
    text_body = "\n".join(lines_text)

    # ---- HTML version ----
    def _rows_html(rows: list[dict], cols: list[tuple[str, str]]) -> str:
        if not rows:
            return "<p style='color:#888;font-size:13px;'>None.</p>"
        html = "<table style='font-size:13px;border-collapse:collapse;width:100%;'>"
        html += "<tr>" + "".join(
            f"<th style='text-align:left;padding:4px 12px 4px 0;color:#666;border-bottom:1px solid #eee;'>{h}</th>"
            for h, _ in cols
        ) + "</tr>"
        for row in rows:
            props = row.get("properties") or {}
            html += "<tr>" + "".join(
                f"<td style='padding:4px 12px 4px 0;'>{_prop_text(props, k) or row.get('created_time', '')[:10]}</td>"
                for _, k in cols
            ) + "</tr>"
        html += "</table>"
        return html

    free_html = _rows_html(
        free_rows,
        [("Status", "Status"), ("Email", "Email"), ("Created", "__created")],
    )
    paid_html = _rows_html(
        paid_rows,
        [("Status", "Status"), ("Tier", "Tier"), ("Email", "Email")],
    )
    delivered_html = _rows_html(
        delivered_rows,
        [("Tier", "Tier"), ("Email", "Email")],
    )

    html_body = f"""<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#111;max-width:700px;margin:0 auto;padding:16px;">
  <h2 style="margin:0 0 4px;">Queue heartbeat</h2>
  <p style="color:#666;font-size:13px;margin:0 0 20px;">{now.strftime('%A %d %B %Y, %H:%M UTC')}</p>

  <h3 style="margin:0 0 8px;border-bottom:1px solid #eee;padding-bottom:4px;">
    Free audit queue &mdash; {len(free_rows)} pending
  </h3>
  {free_html}

  <h3 style="margin:20px 0 8px;border-bottom:1px solid #eee;padding-bottom:4px;">
    Paid queue &mdash; {len(paid_rows)} pending
  </h3>
  {paid_html}

  <h3 style="margin:20px 0 8px;border-bottom:1px solid #eee;padding-bottom:4px;">
    Delivered this week &mdash; {len(delivered_rows)}
  </h3>
  {delivered_html}
</body></html>"""

    return html_body, text_body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Email a queue-state heartbeat to the founder")
    parser.add_argument("--dry-run", action="store_true", help="Print report to console, no email")
    args = parser.parse_args(argv)

    html_body, text_body = build_report()

    if args.dry_run:
        print(text_body)
        return 0

    now = datetime.datetime.now(datetime.UTC)
    subject = f"[LaunchLook] Queue heartbeat — {now.strftime('%Y-%m-%d')}"
    ok = send_plain_admin_email(subject, html_body, text_body, context="heartbeat")
    if ok:
        print(f"[heartbeat] Email sent: {subject}")
    else:
        print("[heartbeat] Email failed — check RESEND_API_KEY and ADMIN_EMAIL", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
