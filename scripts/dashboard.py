"""
dashboard.py — generate a single-file HTML dashboard from the Customers DB.

Pulls every customer row from Notion, computes summary metrics, and writes
output/dashboard.html. Auto-refreshes itself every 90 seconds when open in
a browser, so leaving the tab open gives you live status.

What you see:
  * Headline metrics: revenue total, revenue this week, customer count,
    deliverables in flight.
  * Action queue: customers who paid but the report isn't out yet,
    sorted by delivery deadline (most overdue first).
  * Pipeline funnel: Paid -> Intake received -> In progress -> Delivered.
  * Recent customers table.
  * Setup gap warnings (e.g., Stripe ID missing) so you can spot data drift.

Pricing constants live at the top of this file. Adjust if you change tiers.

Usage:
    python scripts/dashboard.py
    python scripts/dashboard.py --open      # also open in your default browser
    python scripts/dashboard.py --watch 60  # regenerate every N seconds

Required env (load from .env):
    NOTION_TOKEN
    NOTION_CUSTOMERS_DB_ID
"""

from __future__ import annotations

import argparse
import html
import os
import sys
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "output" / "dashboard.html"

TIER_PRICE = {
    "Starter Package": 19,
    "Scale Up Package": 49,
    "Pro Package": 99,
    # Retain legacy keys so a stale Notion record (pre-q3 rename) still
    # contributes to dashboard totals at its original price point.
    "Full Package": 29,
}

# Status values used in the Customers DB Status column
STATUS_PAID = "Paid"
STATUS_INTAKE = "Intake received"
STATUS_IN_PROGRESS = "In progress"
STATUS_DELIVERED = "Delivered"
STATUS_REFUNDED = "Refunded"

PIPELINE_STAGES = [STATUS_PAID, STATUS_INTAKE, STATUS_IN_PROGRESS, STATUS_DELIVERED]


# ---------------------------------------------------------------------------
# Notion fetch
# ---------------------------------------------------------------------------


def fetch_all_customers(notion, ds_id: str) -> list[dict]:
    """Page through the Customers data source and return non-archived rows."""
    rows: list[dict] = []
    cursor = None
    while True:
        resp = notion.data_sources.query(
            data_source_id=ds_id,
            page_size=100,
            start_cursor=cursor,
        )
        rows.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return [r for r in rows if not (r.get("archived") or r.get("in_trash"))]


def get_text(prop: dict | None) -> str:
    if not prop:
        return ""
    if "title" in prop and prop["title"]:
        return prop["title"][0].get("plain_text", "")
    if "rich_text" in prop and prop["rich_text"]:
        return prop["rich_text"][0].get("plain_text", "")
    return ""


def get_select(prop: dict | None) -> str | None:
    if not prop or not prop.get("select"):
        return None
    return prop["select"].get("name")


def get_email(prop: dict | None) -> str:
    if not prop:
        return ""
    return prop.get("email") or ""


def get_url(prop: dict | None) -> str:
    if not prop:
        return ""
    return prop.get("url") or ""


def get_date(prop: dict | None) -> datetime | None:
    if not prop or not prop.get("date"):
        return None
    raw = prop["date"].get("start")
    if not raw:
        return None
    try:
        if "T" in raw:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return datetime.fromisoformat(raw + "T00:00:00+00:00")
    except ValueError:
        return None


def get_checkbox(prop: dict | None) -> bool:
    if not prop:
        return False
    return bool(prop.get("checkbox"))


def normalize_row(row: dict) -> dict[str, Any]:
    p = row.get("properties", {})
    return {
        "name": get_text(p.get("Name")) or "(untitled)",
        "email": get_email(p.get("Email")),
        "app_url": get_url(p.get("App URL")),
        "app_name": get_text(p.get("App Name")),
        "platform": get_select(p.get("Platform")),
        "tier": get_select(p.get("Tier")),
        "status": get_select(p.get("Status")),
        "payment_date": get_date(p.get("Payment Date")),
        "intake_received": get_checkbox(p.get("Intake Received")),
        "delivery_due": get_date(p.get("Delivery Due")),
        "delivered_at": get_date(p.get("Delivered At")),
        "report_url": get_url(p.get("Notion Report URL")),
        "stripe_id": get_text(p.get("Stripe Payment ID")),
        "followup_d3_sent": get_checkbox(p.get("Follow-up D3 Sent")),
        "followup_d7_sent": get_checkbox(p.get("Follow-up D7 Sent")),
        "useful_rating": get_select(p.get("Useful Rating")),
        "page_id": row.get("id"),
    }


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def revenue_for_tier(tier: str | None) -> int:
    if not tier:
        return 0
    return TIER_PRICE.get(tier, 0)


def compute_metrics(customers: list[dict]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    real = [c for c in customers if not c["name"].startswith("EXAMPLE")]

    total_revenue = sum(revenue_for_tier(c["tier"]) for c in real if c["status"] != STATUS_REFUNDED)
    week_revenue = sum(
        revenue_for_tier(c["tier"])
        for c in real
        if c["payment_date"] and c["payment_date"] >= week_ago and c["status"] != STATUS_REFUNDED
    )

    delivered_count = sum(1 for c in real if c["status"] == STATUS_DELIVERED)
    in_flight_count = sum(1 for c in real if c["status"] in (STATUS_PAID, STATUS_INTAKE, STATUS_IN_PROGRESS))

    by_status: dict[str, int] = {s: 0 for s in PIPELINE_STAGES + [STATUS_REFUNDED]}
    by_tier: dict[str, int] = {t: 0 for t in TIER_PRICE}
    by_platform: dict[str, int] = {}
    for c in real:
        if c["status"]:
            by_status[c["status"]] = by_status.get(c["status"], 0) + 1
        if c["tier"]:
            by_tier[c["tier"]] = by_tier.get(c["tier"], 0) + 1
        if c["platform"]:
            by_platform[c["platform"]] = by_platform.get(c["platform"], 0) + 1

    # Action queue: paid but not delivered, sort by delivery_due ascending (overdue first)
    action_queue = [
        c for c in real
        if c["status"] in (STATUS_PAID, STATUS_INTAKE, STATUS_IN_PROGRESS)
    ]
    action_queue.sort(
        key=lambda c: c["delivery_due"] or datetime.max.replace(tzinfo=timezone.utc)
    )

    # Recent customers (last 10 by payment_date)
    recent = sorted(
        [c for c in real if c["payment_date"]],
        key=lambda c: c["payment_date"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )[:10]

    return {
        "total_revenue": total_revenue,
        "week_revenue": week_revenue,
        "total_customers": len(real),
        "delivered_count": delivered_count,
        "in_flight_count": in_flight_count,
        "by_status": by_status,
        "by_tier": by_tier,
        "by_platform": by_platform,
        "action_queue": action_queue,
        "recent": recent,
        "now": now,
        "raw_count": len(customers),
        "example_count": len(customers) - len(real),
    }


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------


def render_html(m: dict[str, Any], notion_db_id: str) -> str:
    now_str = m["now"].astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

    # Action queue rows
    if m["action_queue"]:
        queue_rows = "\n".join(action_row_html(c, m["now"]) for c in m["action_queue"])
        queue_table = f"""
        <table>
          <thead>
            <tr>
              <th>Customer</th>
              <th>Tier</th>
              <th>Status</th>
              <th>Due</th>
              <th>Intake?</th>
              <th>App</th>
            </tr>
          </thead>
          <tbody>{queue_rows}</tbody>
        </table>"""
    else:
        queue_table = '<p class="muted">No customers waiting on a report. Inbox zero.</p>'

    # Recent customers
    if m["recent"]:
        recent_rows = "\n".join(recent_row_html(c) for c in m["recent"])
        recent_table = f"""
        <table>
          <thead>
            <tr>
              <th>Customer</th>
              <th>Tier</th>
              <th>Paid</th>
              <th>Status</th>
              <th>Platform</th>
            </tr>
          </thead>
          <tbody>{recent_rows}</tbody>
        </table>"""
    else:
        recent_table = '<p class="muted">No customers yet.</p>'

    # Pipeline funnel bars
    funnel = pipeline_html(m["by_status"])

    # Tier + platform breakdowns
    tier_summary = breakdown_html("By tier", m["by_tier"], total=m["total_customers"])
    platform_summary = breakdown_html("By platform", m["by_platform"], total=m["total_customers"])

    example_warning = ""
    if m["example_count"]:
        example_warning = f'<div class="warn">⚠ {m["example_count"]} EXAMPLE row(s) still in DB — delete them in Notion.</div>'

    notion_link = f"https://www.notion.so/{notion_db_id.replace('-', '')}"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="90">
  <title>LaunchLook — Ops Dashboard</title>
  <style>
    :root {{
      --bg: #0b0d12;
      --panel: #151821;
      --panel-2: #1c2030;
      --text: #e6e8ef;
      --muted: #8a92a6;
      --accent: #7c5cff;
      --green: #22c55e;
      --yellow: #eab308;
      --red: #ef4444;
      --border: #262a3a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px 64px; }}
    h1 {{ font-size: 28px; margin: 0 0 4px; }}
    h2 {{ font-size: 16px; margin: 32px 0 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }}
    .top {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 12px; }}
    .top .meta {{ color: var(--muted); font-size: 13px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 24px 0; }}
    .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; }}
    .card .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .card .value {{ font-size: 30px; font-weight: 600; margin-top: 6px; }}
    .card .sub {{ color: var(--muted); font-size: 13px; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); border-radius: 10px; overflow: hidden; }}
    th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid var(--border); font-size: 14px; }}
    th {{ color: var(--muted); font-weight: 500; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; background: var(--panel-2); }}
    tr:last-child td {{ border-bottom: none; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .pill {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
    .pill-paid {{ background: rgba(124, 92, 255, 0.18); color: #a991ff; }}
    .pill-intake {{ background: rgba(234, 179, 8, 0.18); color: #fcd34d; }}
    .pill-progress {{ background: rgba(59, 130, 246, 0.18); color: #93c5fd; }}
    .pill-delivered {{ background: rgba(34, 197, 94, 0.18); color: #86efac; }}
    .pill-refunded {{ background: rgba(239, 68, 68, 0.18); color: #fca5a5; }}
    .due-overdue {{ color: var(--red); font-weight: 600; }}
    .due-today {{ color: var(--yellow); font-weight: 600; }}
    .due-future {{ color: var(--muted); }}
    .funnel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; }}
    .funnel-row {{ display: flex; align-items: center; gap: 12px; margin: 8px 0; font-size: 14px; }}
    .funnel-row .stage {{ width: 140px; color: var(--muted); }}
    .funnel-row .bar-bg {{ flex: 1; background: var(--panel-2); height: 18px; border-radius: 4px; overflow: hidden; }}
    .funnel-row .bar {{ height: 100%; background: linear-gradient(90deg, #7c5cff 0%, #5b9eff 100%); }}
    .funnel-row .count {{ width: 40px; text-align: right; font-weight: 600; }}
    .breakdown {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .breakdown ul {{ list-style: none; margin: 0; padding: 0; }}
    .breakdown li {{ display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid var(--border); font-size: 14px; }}
    .breakdown li:last-child {{ border-bottom: none; }}
    .breakdown .label {{ color: var(--muted); }}
    .muted {{ color: var(--muted); }}
    .warn {{ background: rgba(234, 179, 8, 0.12); border: 1px solid rgba(234, 179, 8, 0.4); padding: 10px 14px; border-radius: 8px; color: #fcd34d; font-size: 14px; margin-top: 12px; }}
    @media (max-width: 720px) {{
      .breakdown {{ grid-template-columns: 1fr; }}
      table {{ font-size: 13px; }}
      th, td {{ padding: 10px 8px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="top">
      <div>
        <h1>LaunchLook — Ops</h1>
        <div class="meta">
          Last refreshed {now_str} · auto-refresh every 90s ·
          <a href="{notion_link}" target="_blank">Open Customers in Notion</a>
        </div>
      </div>
    </div>

    {example_warning}

    <div class="metrics">
      <div class="card">
        <div class="label">Total revenue</div>
        <div class="value">${m["total_revenue"]:,}</div>
        <div class="sub">all-time, paid customers</div>
      </div>
      <div class="card">
        <div class="label">Last 7 days</div>
        <div class="value">${m["week_revenue"]:,}</div>
        <div class="sub">paid in last week</div>
      </div>
      <div class="card">
        <div class="label">Customers</div>
        <div class="value">{m["total_customers"]}</div>
        <div class="sub">{m["delivered_count"]} delivered · {m["in_flight_count"]} in flight</div>
      </div>
      <div class="card">
        <div class="label">Action queue</div>
        <div class="value">{len(m["action_queue"])}</div>
        <div class="sub">paid, awaiting report</div>
      </div>
    </div>

    <h2>Action queue — needs your attention</h2>
    {queue_table}

    <h2>Pipeline</h2>
    <div class="funnel">{funnel}</div>

    <h2>Breakdown</h2>
    <div class="breakdown">
      <div class="card">{tier_summary}</div>
      <div class="card">{platform_summary}</div>
    </div>

    <h2>Recent customers</h2>
    {recent_table}

  </div>
</body>
</html>"""


def status_pill(status: str | None) -> str:
    if not status:
        return ""
    cls_map = {
        STATUS_PAID: "pill-paid",
        STATUS_INTAKE: "pill-intake",
        STATUS_IN_PROGRESS: "pill-progress",
        STATUS_DELIVERED: "pill-delivered",
        STATUS_REFUNDED: "pill-refunded",
    }
    cls = cls_map.get(status, "pill-paid")
    return f'<span class="pill {cls}">{html.escape(status)}</span>'


def due_label(due: datetime | None, now: datetime) -> str:
    if not due:
        return '<span class="due-future">—</span>'
    delta = (due - now).total_seconds() / 3600  # hours
    if delta < 0:
        hrs = abs(delta)
        if hrs < 24:
            txt = f"{hrs:.0f}h overdue"
        else:
            txt = f"{hrs/24:.0f}d overdue"
        return f'<span class="due-overdue">{txt}</span>'
    if delta < 12:
        return f'<span class="due-today">in {delta:.0f}h</span>'
    if delta < 24:
        return f'<span class="due-today">in {delta:.0f}h</span>'
    days = delta / 24
    return f'<span class="due-future">in {days:.0f}d</span>'


def action_row_html(c: dict, now: datetime) -> str:
    name = html.escape(c["name"])
    tier = html.escape(c["tier"] or "—")
    intake = "✓" if c["intake_received"] else "—"
    app = (
        f'<a href="{html.escape(c["app_url"])}" target="_blank">{html.escape(c["app_name"] or c["app_url"])}</a>'
        if c["app_url"]
        else "—"
    )
    return f"""
        <tr>
          <td>{name}</td>
          <td>{tier}</td>
          <td>{status_pill(c["status"])}</td>
          <td>{due_label(c["delivery_due"], now)}</td>
          <td>{intake}</td>
          <td>{app}</td>
        </tr>"""


def recent_row_html(c: dict) -> str:
    name = html.escape(c["name"])
    paid = c["payment_date"].astimezone().strftime("%Y-%m-%d") if c["payment_date"] else "—"
    return f"""
        <tr>
          <td>{name}</td>
          <td>{html.escape(c["tier"] or "—")}</td>
          <td class="muted">{paid}</td>
          <td>{status_pill(c["status"])}</td>
          <td>{html.escape(c["platform"] or "—")}</td>
        </tr>"""


def pipeline_html(by_status: dict[str, int]) -> str:
    counts = [by_status.get(s, 0) for s in PIPELINE_STAGES]
    max_count = max(counts) if counts and max(counts) > 0 else 1
    rows = []
    for stage, count in zip(PIPELINE_STAGES, counts):
        pct = int((count / max_count) * 100)
        rows.append(
            f'<div class="funnel-row">'
            f'<div class="stage">{html.escape(stage)}</div>'
            f'<div class="bar-bg"><div class="bar" style="width:{pct}%"></div></div>'
            f'<div class="count">{count}</div>'
            f"</div>"
        )
    return "\n".join(rows)


def breakdown_html(label: str, items: dict[str, int], total: int) -> str:
    if not any(items.values()):
        return f'<h3 style="margin:0 0 8px; font-size:14px; color: var(--muted)">{label}</h3><p class="muted" style="margin:0">No data yet.</p>'
    parts = [f'<h3 style="margin:0 0 8px; font-size:14px; color: var(--muted); text-transform: uppercase; letter-spacing:0.05em;">{label}</h3>', "<ul>"]
    sorted_items = sorted(items.items(), key=lambda kv: kv[1], reverse=True)
    for k, v in sorted_items:
        if v == 0:
            continue
        pct = (v / total * 100) if total else 0
        parts.append(f'<li><span class="label">{html.escape(k)}</span><span><strong>{v}</strong> <span class="muted">({pct:.0f}%)</span></span></li>')
    parts.append("</ul>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def generate_once() -> Path:
    try:
        from notion_client import Client
    except ImportError:
        sys.exit("ERROR: pip install notion-client")

    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_CUSTOMERS_DB_ID")
    if not token:
        sys.exit("ERROR: NOTION_TOKEN not set")
    if not db_id:
        sys.exit("ERROR: NOTION_CUSTOMERS_DB_ID not set")

    notion = Client(auth=token)
    db = notion.databases.retrieve(database_id=db_id)
    ds_id = db["data_sources"][0]["id"]

    rows = fetch_all_customers(notion, ds_id)
    customers = [normalize_row(r) for r in rows]
    metrics = compute_metrics(customers)
    html_out = render_html(metrics, db_id)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html_out, encoding="utf-8")
    return OUTPUT_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open", action="store_true", help="Open the HTML in your default browser after generating.")
    parser.add_argument("--watch", type=int, metavar="SECONDS", help="Regenerate every N seconds. Ctrl+C to stop.")
    args = parser.parse_args()

    if args.watch:
        path = generate_once()
        print(f"Wrote {path}")
        if args.open:
            webbrowser.open(path.as_uri())
        try:
            while True:
                time.sleep(args.watch)
                generate_once()
                print(f"Refreshed at {datetime.now().strftime('%H:%M:%S')}")
        except KeyboardInterrupt:
            print("\nStopped.")
        return 0

    path = generate_once()
    print(f"Wrote {path}")
    if args.open:
        webbrowser.open(path.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
