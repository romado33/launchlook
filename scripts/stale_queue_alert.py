#!/usr/bin/env python3
"""Alert the founder when an audit job has been stuck in queue for > THRESHOLD hours.

Checks both the Free Audit DB (status = queued or processing) and the
Customers DB (status = Paid or Intake Received) for rows older than the
threshold. Sends one email if any stale rows are found; does nothing if
everything is fresh.

Designed to run every 6 hours via Task Scheduler. Only sends when there
is actually something to flag, so it stays low-noise.

Usage:
    python scripts/stale_queue_alert.py                # 48h threshold (default)
    python scripts/stale_queue_alert.py --hours 24     # custom threshold
    python scripts/stale_queue_alert.py --dry-run      # print to console, no email
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

import os  # noqa: E402

from api._lib.notion_helpers import (  # noqa: E402
    STATUS_INTAKE,
    STATUS_PAID,
    get_client,
    get_customers_ds_id,
)
from scripts.audit_automation.notify import send_plain_admin_email  # noqa: E402

DEFAULT_THRESHOLD_HOURS = 48


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
    db_id = os.getenv("NOTION_FREE_AUDIT_DB_ID", "").strip()
    if not db_id:
        return None
    db = client.databases.retrieve(database_id=db_id)
    sources = db.get("data_sources") or []
    return sources[0]["id"] if sources else None


def find_stale_rows(threshold_hours: int) -> list[dict]:
    """Return rows that have been in a pending status past the threshold."""
    client = get_client()
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=threshold_hours)
    cutoff_iso = cutoff.isoformat()
    stale: list[dict] = []

    # Free audit DB
    free_ds = _get_free_audit_ds_id(client)
    if free_ds:
        resp = client.data_sources.query(
            data_source_id=free_ds,
            filter={
                "and": [
                    {
                        "or": [
                            {"property": "Status", "select": {"equals": "queued"}},
                            {"property": "Status", "select": {"equals": "processing"}},
                        ]
                    },
                    {
                        "timestamp": "created_time",
                        "created_time": {"before": cutoff_iso},
                    },
                ]
            },
            page_size=50,
        )
        for row in resp.get("results", []):
            if row.get("archived") or row.get("in_trash"):
                continue
            props = row.get("properties") or {}
            stale.append({
                "db": "free_audit",
                "email": _prop_text(props, "Email"),
                "status": _prop_text(props, "Status"),
                "tier": "Free",
                "created": (row.get("created_time") or "")[:19],
                "page_id": row["id"],
            })

    # Customers DB
    cust_ds = get_customers_ds_id(client)
    resp = client.data_sources.query(
        data_source_id=cust_ds,
        filter={
            "and": [
                {
                    "or": [
                        {"property": "Status", "select": {"equals": STATUS_PAID}},
                        {"property": "Status", "select": {"equals": STATUS_INTAKE}},
                    ]
                },
                {
                    "timestamp": "created_time",
                    "created_time": {"before": cutoff_iso},
                },
            ]
        },
        page_size=50,
    )
    for row in resp.get("results", []):
        if row.get("archived") or row.get("in_trash"):
            continue
        props = row.get("properties") or {}
        stale.append({
            "db": "customers",
            "email": _prop_text(props, "Email"),
            "status": _prop_text(props, "Status"),
            "tier": _prop_text(props, "Tier"),
            "created": (row.get("created_time") or "")[:19],
            "page_id": row["id"],
        })

    return stale


def build_alert(stale: list[dict], threshold_hours: int) -> tuple[str, str]:
    now_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
    count = len(stale)

    lines = [
        f"Stale-queue alert — {count} row(s) stuck > {threshold_hours}h",
        f"Checked at {now_str}",
        "",
    ]
    for row in stale:
        age_desc = f"created {row['created']}"
        lines.append(
            f"  [{row['db']:12}] {row['status']:20} {row['tier']:20} {row['email']}  ({age_desc})"
        )
    lines += [
        "",
        "Actions:",
        "  Free audits: python scripts/process_audit_queue.py --slug <slug>",
        "  Paid audits: check Notion row for missing URL / intake form",
        "  --list:      python scripts/process_audit_queue.py --list",
    ]
    text_body = "\n".join(lines)

    rows_html = "".join(
        f"<tr>"
        f"<td style='padding:4px 10px 4px 0;color:#666;font-size:12px;'>{r['db']}</td>"
        f"<td style='padding:4px 10px 4px 0;'>{r['status']}</td>"
        f"<td style='padding:4px 10px 4px 0;'>{r['tier']}</td>"
        f"<td style='padding:4px 10px 4px 0;'>{r['email']}</td>"
        f"<td style='padding:4px 0;color:#888;font-size:12px;'>since {r['created'][:10]}</td>"
        f"</tr>"
        for r in stale
    )
    html_body = f"""<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#111;max-width:700px;margin:0 auto;padding:16px;">
  <h2 style="margin:0 0 4px;color:#b91c1c;">Stale-queue alert</h2>
  <p style="color:#666;font-size:13px;margin:0 0 16px;">
    {count} row(s) stuck longer than {threshold_hours} hours. Checked at {now_str}.
  </p>
  <table style="font-size:14px;border-collapse:collapse;width:100%;">
    <tr>
      <th style="text-align:left;padding:4px 10px 4px 0;color:#666;border-bottom:1px solid #eee;">DB</th>
      <th style="text-align:left;padding:4px 10px 4px 0;color:#666;border-bottom:1px solid #eee;">Status</th>
      <th style="text-align:left;padding:4px 10px 4px 0;color:#666;border-bottom:1px solid #eee;">Tier</th>
      <th style="text-align:left;padding:4px 10px 4px 0;color:#666;border-bottom:1px solid #eee;">Email</th>
      <th style="text-align:left;padding:4px 0;color:#666;border-bottom:1px solid #eee;">Created</th>
    </tr>
    {rows_html}
  </table>
  <p style="margin-top:20px;font-size:13px;color:#555;">
    <b>Free audits:</b>
    <code style="background:#f4f4f5;padding:2px 6px;border-radius:3px;">
      python scripts/process_audit_queue.py --slug &lt;slug&gt;
    </code><br>
    <b>Paid audits:</b> check the Notion row for missing URL or intake form submission.
  </p>
</body></html>"""

    return html_body, text_body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Alert on stale audit queue rows")
    parser.add_argument("--hours", type=int, default=DEFAULT_THRESHOLD_HOURS,
                        help=f"Threshold in hours (default {DEFAULT_THRESHOLD_HOURS})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print to console, no email")
    args = parser.parse_args(argv)

    stale = find_stale_rows(args.hours)

    if not stale:
        print(f"[stale_alert] No rows stuck > {args.hours}h. All clear.")
        return 0

    html_body, text_body = build_alert(stale, args.hours)

    if args.dry_run:
        print(text_body)
        return 0

    subject = f"[LaunchLook] Stale queue: {len(stale)} row(s) stuck > {args.hours}h"
    ok = send_plain_admin_email(subject, html_body, text_body, context="stale-alert")
    if ok:
        print(f"[stale_alert] Alert sent: {len(stale)} stale rows")
    else:
        print("[stale_alert] Email failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
