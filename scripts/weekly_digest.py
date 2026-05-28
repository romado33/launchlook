#!/usr/bin/env python3
"""Send a weekly business digest to the founder every Sunday morning.

Covers the previous Mon-Sun week. Pulls from:
  - Notion Customers DB: delivered count, pending count, new paid count
  - Notion Free Audit DB: new free signups, conversion to paid
  - data/ai_costs/*.jsonl: total LLM spend for the week

Schedule via Task Scheduler to run Sunday at 08:00.

Usage:
    python scripts/weekly_digest.py            # send this week's digest
    python scripts/weekly_digest.py --dry-run  # print to console, no email
    python scripts/weekly_digest.py --weeks 2  # go back 2 weeks instead of 1
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any

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
    STATUS_DELIVERED,
    STATUS_IN_PROGRESS,
    STATUS_INTAKE,
    STATUS_PAID,
    get_client,
    get_customers_ds_id,
)
from scripts.audit_automation.notify import send_plain_admin_email  # noqa: E402

TIER_REVENUE: dict[str, float] = {
    "Starter Package": 19.0,
    "Scale Up Package": 49.0,
    "Pro Package": 99.0,
}


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


def _prop_date(props: dict, name: str) -> datetime.datetime | None:
    p = props.get(name) or {}
    date_obj = p.get("date") or {}
    start = date_obj.get("start")
    if not start:
        return None
    try:
        return datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
    except ValueError:
        return None


def _week_bounds(weeks_back: int = 1) -> tuple[datetime.datetime, datetime.datetime]:
    """Return (start, end) for the target week (Mon 00:00 UTC → Sun 23:59 UTC)."""
    now = datetime.datetime.now(datetime.UTC)
    # Most recent Monday
    this_monday = (now - datetime.timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = this_monday - datetime.timedelta(seconds=1)  # previous Sunday 23:59:59
    start = this_monday - datetime.timedelta(weeks=weeks_back)
    return start, end


def _load_ai_costs(week_start: datetime.datetime, week_end: datetime.datetime) -> dict[str, Any]:
    """Sum LLM costs from data/ai_costs/*.jsonl for the target week."""
    costs_dir = REPO_ROOT / "data" / "ai_costs"
    total_usd = 0.0
    total_calls = 0
    by_model: dict[str, float] = {}

    for path in sorted(costs_dir.glob("*.jsonl")):
        try:
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    ts_str = rec.get("timestamp") or ""
                    if not ts_str:
                        continue
                    try:
                        ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if not (week_start <= ts <= week_end):
                        continue
                    cost = float(rec.get("cost_usd") or 0)
                    model = rec.get("model") or "unknown"
                    total_usd += cost
                    total_calls += 1
                    by_model[model] = by_model.get(model, 0) + cost
        except Exception:  # noqa: BLE001
            continue

    return {"total_usd": total_usd, "total_calls": total_calls, "by_model": by_model}


def _get_free_audit_ds_id(client) -> str | None:
    db_id = os.getenv("NOTION_FREE_AUDIT_DB_ID", "").strip()
    if not db_id:
        return None
    db = client.databases.retrieve(database_id=db_id)
    sources = db.get("data_sources") or []
    return sources[0]["id"] if sources else None


def collect_stats(week_start: datetime.datetime, week_end: datetime.datetime) -> dict[str, Any]:
    client = get_client()
    cust_ds = get_customers_ds_id(client)
    start_iso = week_start.isoformat()
    end_iso = week_end.isoformat()

    # New paid customers this week (created in window)
    resp = client.data_sources.query(
        data_source_id=cust_ds,
        filter={
            "and": [
                {"timestamp": "created_time", "created_time": {"on_or_after": start_iso}},
                {"timestamp": "created_time", "created_time": {"before": end_iso}},
            ]
        },
        page_size=100,
    )
    new_paid_rows = [r for r in resp.get("results", []) if not (r.get("archived") or r.get("in_trash"))]

    # Delivered this week
    resp = client.data_sources.query(
        data_source_id=cust_ds,
        filter={
            "and": [
                {"property": "Status", "select": {"equals": STATUS_DELIVERED}},
                {"timestamp": "last_edited_time", "last_edited_time": {"on_or_after": start_iso}},
                {"timestamp": "last_edited_time", "last_edited_time": {"before": end_iso}},
            ]
        },
        page_size=100,
    )
    delivered_rows = [r for r in resp.get("results", []) if not (r.get("archived") or r.get("in_trash"))]

    # Still pending (total backlog, not just this week)
    resp = client.data_sources.query(
        data_source_id=cust_ds,
        filter={
            "or": [
                {"property": "Status", "select": {"equals": STATUS_PAID}},
                {"property": "Status", "select": {"equals": STATUS_INTAKE}},
                {"property": "Status", "select": {"equals": STATUS_IN_PROGRESS}},
            ]
        },
        page_size=100,
    )
    pending_rows = [r for r in resp.get("results", []) if not (r.get("archived") or r.get("in_trash"))]

    # Tier breakdown for delivered
    tier_counts: dict[str, int] = {}
    for row in delivered_rows:
        props = row.get("properties") or {}
        tier = _prop_text(props, "Tier") or "Unknown"
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    # Revenue estimate (delivered this week only)
    revenue = sum(
        TIER_REVENUE.get(t, 0) * count for t, count in tier_counts.items()
    )

    # Free audit signups this week
    free_signups = 0
    free_ds = _get_free_audit_ds_id(client)
    if free_ds:
        resp = client.data_sources.query(
            data_source_id=free_ds,
            filter={
                "and": [
                    {"timestamp": "created_time", "created_time": {"on_or_after": start_iso}},
                    {"timestamp": "created_time", "created_time": {"before": end_iso}},
                ]
            },
            page_size=100,
        )
        free_signups = len([
            r for r in resp.get("results", [])
            if not (r.get("archived") or r.get("in_trash"))
        ])

    # Conversion rate: new paid / (new paid + free signups) for the week
    total_top_of_funnel = new_paid_rows.__len__() + free_signups
    conversion_rate = (
        f"{100 * len(new_paid_rows) / total_top_of_funnel:.0f}%"
        if total_top_of_funnel > 0 else "n/a"
    )

    ai_costs = _load_ai_costs(week_start, week_end)

    return {
        "week_start": week_start,
        "week_end": week_end,
        "new_paid": len(new_paid_rows),
        "delivered": len(delivered_rows),
        "pending": len(pending_rows),
        "free_signups": free_signups,
        "conversion_rate": conversion_rate,
        "tier_counts": tier_counts,
        "revenue_est": revenue,
        "ai_costs": ai_costs,
    }


def build_digest(stats: dict[str, Any]) -> tuple[str, str]:
    ws = stats["week_start"].strftime("%d %b")
    we = stats["week_end"].strftime("%d %b %Y")
    period = f"{ws} – {we}"

    tier_lines = "\n".join(
        f"    {tier}: {count}" for tier, count in sorted(stats["tier_counts"].items())
    ) or "    (none)"

    cost = stats["ai_costs"]
    cost_str = f"${cost['total_usd']:.4f} across {cost['total_calls']} LLM calls"

    text_body = f"""Weekly digest — {period}

New paid orders:    {stats['new_paid']}
Delivered:          {stats['delivered']}
  {tier_lines}
Revenue est:        ${stats['revenue_est']:.2f}
Pending backlog:    {stats['pending']}

Free signups:       {stats['free_signups']}
Free → paid rate:   {stats['conversion_rate']}

LLM cost:           {cost_str}
"""
    if cost["by_model"]:
        text_body += "\nBy model:\n"
        for model, usd in sorted(cost["by_model"].items(), key=lambda x: -x[1]):
            text_body += f"  {model}: ${usd:.4f}\n"

    text_body += "\n-- LaunchLook Automation"

    tier_rows_html = "".join(
        f"<tr><td style='padding:2px 10px 2px 0;color:#666;'>{t}</td>"
        f"<td style='padding:2px 0;'>{c}</td></tr>"
        for t, c in sorted(stats["tier_counts"].items())
    ) or "<tr><td colspan='2' style='color:#888;'>(none)</td></tr>"

    model_rows_html = ""
    if cost["by_model"]:
        model_rows_html = "<tr><td colspan='2' style='padding-top:8px;color:#666;font-size:12px;'>By model:</td></tr>"
        for model, usd in sorted(cost["by_model"].items(), key=lambda x: -x[1]):
            model_rows_html += (
                f"<tr><td style='padding:2px 10px 2px 16px;color:#888;font-size:12px;'>{model}</td>"
                f"<td style='padding:2px 0;font-size:12px;'>${usd:.4f}</td></tr>"
            )

    html_body = f"""<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#111;max-width:600px;margin:0 auto;padding:16px;">
  <h2 style="margin:0 0 4px;">Weekly digest</h2>
  <p style="color:#666;font-size:13px;margin:0 0 20px;">{period}</p>

  <table style="font-size:15px;border-collapse:collapse;width:100%;">
    <tr>
      <td style="padding:6px 16px 6px 0;color:#666;border-bottom:1px solid #f0f0f0;">New paid orders</td>
      <td style="padding:6px 0;font-weight:600;border-bottom:1px solid #f0f0f0;">{stats['new_paid']}</td>
    </tr>
    <tr>
      <td style="padding:6px 16px 6px 0;color:#666;border-bottom:1px solid #f0f0f0;">Delivered</td>
      <td style="padding:6px 0;font-weight:600;border-bottom:1px solid #f0f0f0;">{stats['delivered']}</td>
    </tr>
    <tr>
      <td style="padding:6px 16px 6px 0;color:#666;border-bottom:1px solid #f0f0f0;" colspan="2">
        <table style="width:100%;font-size:13px;">{tier_rows_html}</table>
      </td>
    </tr>
    <tr>
      <td style="padding:6px 16px 6px 0;color:#666;border-bottom:1px solid #f0f0f0;">Revenue est.</td>
      <td style="padding:6px 0;font-weight:600;border-bottom:1px solid #f0f0f0;">${stats['revenue_est']:.2f}</td>
    </tr>
    <tr>
      <td style="padding:6px 16px 6px 0;color:#666;border-bottom:1px solid #f0f0f0;">Pending backlog</td>
      <td style="padding:6px 0;border-bottom:1px solid #f0f0f0;">{stats['pending']}</td>
    </tr>
  </table>

  <table style="font-size:15px;border-collapse:collapse;width:100%;margin-top:16px;">
    <tr>
      <td style="padding:6px 16px 6px 0;color:#666;border-bottom:1px solid #f0f0f0;">Free signups</td>
      <td style="padding:6px 0;border-bottom:1px solid #f0f0f0;">{stats['free_signups']}</td>
    </tr>
    <tr>
      <td style="padding:6px 16px 6px 0;color:#666;border-bottom:1px solid #f0f0f0;">Free → paid rate</td>
      <td style="padding:6px 0;font-weight:600;border-bottom:1px solid #f0f0f0;">{stats['conversion_rate']}</td>
    </tr>
  </table>

  <table style="font-size:14px;border-collapse:collapse;width:100%;margin-top:16px;">
    <tr>
      <td style="padding:6px 16px 6px 0;color:#666;border-bottom:1px solid #f0f0f0;">LLM cost</td>
      <td style="padding:6px 0;border-bottom:1px solid #f0f0f0;">{cost_str}</td>
    </tr>
    {model_rows_html}
  </table>
</body></html>"""

    return html_body, text_body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Send the weekly LaunchLook digest")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print digest to console, no email")
    parser.add_argument("--weeks", type=int, default=1,
                        help="How many weeks back to report (default 1 = last complete week)")
    args = parser.parse_args(argv)

    week_start, week_end = _week_bounds(args.weeks)
    stats = collect_stats(week_start, week_end)
    html_body, text_body = build_digest(stats)

    if args.dry_run:
        print(text_body)
        return 0

    ws_str = stats["week_start"].strftime("%d %b")
    we_str = stats["week_end"].strftime("%d %b")
    subject = f"[LaunchLook] Weekly digest — {ws_str}–{we_str}"
    ok = send_plain_admin_email(subject, html_body, text_body, context="weekly-digest")
    if ok:
        print(f"[digest] Sent: {subject}")
    else:
        print("[digest] Email failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
