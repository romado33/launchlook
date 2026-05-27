"""ai_costs_report.py - daily / per-customer / summary / alert reporting.

Reads ``data/ai_costs/<YYYY-MM-DD>.jsonl`` written by
``scripts/ai_audit/cost_tracker.py`` and prints structured stdout that
Rob can later pipe into Slack / email / a Notion sync.

Modes:

    # Daily totals for one specific UTC date.
    python scripts/ai_costs_report.py --date 2026-05-26

    # Per-customer breakdown across all logs.
    python scripts/ai_costs_report.py --customer jane-sparkle

    # Last 30 days with margin analysis (uses data/customers.json for
    # revenue when available; otherwise estimates from tiers in the
    # cost log themselves).
    python scripts/ai_costs_report.py --summary --days 30

    # Print alerts if any thresholds are tripped over the last N days.
    python scripts/ai_costs_report.py --alert --days 7

Internal-only tooling per docs/SIMPLICITY-GUARDRAILS.md §6 (no customer
surface ever sees these numbers).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Force UTF-8 console output on Windows so the table headers / emoji
# print safely if Rob pipes the output to a file.
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

from scripts.ai_audit import cost_tracker  # noqa: E402

CUSTOMERS_JSON = REPO_ROOT / "data" / "customers.json"

# Local-tracker tier slugs (from scripts/customers_track.py) -> internal
# pipeline tier name, plus the per-audit revenue from PRODUCT-DECISIONS.md
# §1 (Starter $19, Scale Up $49, Pro $99).
LOCAL_TIER_TO_PIPELINE_TIER = {
    "starter": "Starter Package",
    "full": "Full Package",  # internal name for Scale Up
    "pro": "Pro Package",
}
TIER_PRICE_USD = cost_tracker.TIER_PRICE_USD


# ---------------------------------------------------------------------------
# Pretty-printing helpers
# ---------------------------------------------------------------------------


def _fmt_usd(amount: float) -> str:
    return f"${amount:,.4f}" if amount < 1 else f"${amount:,.2f}"


def _fmt_ratio(ratio: float) -> str:
    return f"{ratio * 100:.1f}%"


def _hr(char: str = "-", width: int = 64) -> str:
    return char * width


# ---------------------------------------------------------------------------
# Revenue lookup
# ---------------------------------------------------------------------------


def load_local_customers() -> list[dict[str, Any]]:
    """Return rows from ``data/customers.json`` if present, else []."""
    if not CUSTOMERS_JSON.exists():
        return []
    try:
        data = json.loads(CUSTOMERS_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = data.get("customers") if isinstance(data, dict) else None
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def revenue_from_cost_rows(rows: list[dict[str, Any]]) -> tuple[float, dict[str, int]]:
    """Estimate revenue by counting unique customers per tier.

    Each unique ``customer_id`` in the cost log counts as ONE completed
    audit. We multiply by the tier price. This is a best-effort estimate
    when ``data/customers.json`` is missing / out of date; the canonical
    source of truth for paid customers is the local tracker (or Notion
    Customers DB if/when wired up).
    """
    seen_per_tier: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        cid = row.get("customer_id", "unknown")
        tier = row.get("tier", "unknown")
        if cid == "unknown":
            continue
        seen_per_tier[tier].add(cid)
    counts = {tier: len(ids) for tier, ids in seen_per_tier.items()}
    revenue = sum(TIER_PRICE_USD.get(tier, 0.0) * len(ids) for tier, ids in seen_per_tier.items())
    return revenue, counts


def revenue_from_local_tracker(
    since_date: str | None = None,
) -> tuple[float, dict[str, int]]:
    """Sum delivered-audit revenue from ``data/customers.json``.

    ``since_date`` filters by ``delivered_at`` >= YYYY-MM-DD. Returns
    ``(0.0, {})`` when the tracker file is missing or empty.
    """
    customers = load_local_customers()
    if not customers:
        return 0.0, {}
    counts: dict[str, int] = defaultdict(int)
    revenue = 0.0
    for row in customers:
        if row.get("status") != "delivered":
            continue
        delivered = row.get("delivered_at") or ""
        if since_date and (delivered[:10] < since_date):
            continue
        local_tier = (row.get("tier") or "").strip().lower()
        pipeline_tier = LOCAL_TIER_TO_PIPELINE_TIER.get(local_tier, "Starter Package")
        counts[pipeline_tier] += 1
        revenue += TIER_PRICE_USD.get(pipeline_tier, 0.0)
    return revenue, dict(counts)


# ---------------------------------------------------------------------------
# Per-customer rollup (re-uses cost_tracker.aggregate_customer)
# ---------------------------------------------------------------------------


def group_rows_by_customer(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row.get("customer_id", "unknown")].append(row)
    return groups


def summarize_customer(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    total_cost = sum(float(r.get("cost_usd", 0.0)) for r in rows)
    in_tok = sum(int(r.get("input_tokens", 0)) for r in rows)
    out_tok = sum(int(r.get("output_tokens", 0)) for r in rows)
    tier = next((r.get("tier") for r in rows if r.get("tier")), "unknown")
    call_types: dict[str, int] = defaultdict(int)
    for r in rows:
        call_types[r.get("call_type", "other")] += 1
    return {
        "call_count": len(rows),
        "tier": tier,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": round(total_cost, 6),
        "call_types": dict(call_types),
    }


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def mode_daily(date: str) -> int:
    summary = cost_tracker.daily_summary(date)
    print()
    print(f"LaunchLook AI cost report - daily totals for {summary['date']} (UTC)")
    print(_hr("="))
    if summary["call_count"] == 0:
        print(f"  (no cost log rows recorded on {summary['date']})")
        return 0
    print(f"  Total cost:        {_fmt_usd(summary['total_cost_usd'])}")
    print(f"  LLM calls:         {summary['call_count']}")
    print(f"  Unique customers:  {summary['customer_count']}")
    print(f"  Input tokens:      {summary['input_tokens']:,}")
    print(f"  Output tokens:     {summary['output_tokens']:,}")
    print(f"  Latency p50/p95:   {summary['p50_latency_ms']} ms / {summary['p95_latency_ms']} ms")
    print()
    print("  Calls by model:")
    for model, count in sorted(summary["models"].items(), key=lambda x: -x[1]):
        print(f"    {count:>4}  {model}")
    print()
    print("  Calls by type:")
    for ct, count in sorted(summary["call_types"].items(), key=lambda x: -x[1]):
        print(f"    {count:>4}  {ct}")
    return 0


def mode_customer(customer_id: str) -> int:
    agg = cost_tracker.aggregate_customer(customer_id)
    print()
    print(f"LaunchLook AI cost report - customer '{customer_id}'")
    print(_hr("="))
    if agg["call_count"] == 0:
        print(f"  (no cost log rows recorded for customer_id={customer_id!r})")
        return 0
    tier = agg["tier"]
    tier_price = TIER_PRICE_USD.get(tier, 0.0)
    ratio = (agg["cost_usd"] / tier_price) if tier_price else 0.0
    print(f"  Tier:              {tier}  (price ${tier_price:.2f})")
    print(f"  Total cost:        {_fmt_usd(agg['cost_usd'])}")
    if tier_price:
        print(f"  Cost / tier price: {_fmt_ratio(ratio)}")
    print(f"  LLM calls:         {agg['call_count']}")
    print(f"  Input tokens:      {agg['input_tokens']:,}")
    print(f"  Output tokens:     {agg['output_tokens']:,}")
    print(f"  First seen (UTC):  {agg.get('first_seen') or '-'}")
    print(f"  Last seen (UTC):   {agg.get('last_seen') or '-'}")
    print()
    print("  Calls by type:")
    for ct, count in sorted(agg["call_type_counts"].items(), key=lambda x: -x[1]):
        print(f"    {count:>4}  {ct}")
    return 0


def mode_summary(days: int) -> int:
    rows = list(cost_tracker.iter_rows_since(days))
    print()
    print(f"LaunchLook AI cost report - last {days} days summary")
    print(_hr("="))
    if not rows:
        print(f"  (no cost log rows recorded in the last {days} days)")
        return 0

    total_cost = sum(float(r.get("cost_usd", 0.0)) for r in rows)

    # Revenue: prefer local tracker (truth), fall back to estimate from
    # the cost log itself (one row per unique customer_id).
    since_date = _days_ago(days)
    tracker_revenue, tracker_counts = revenue_from_local_tracker(since_date)
    if tracker_revenue > 0:
        revenue = tracker_revenue
        counts = tracker_counts
        revenue_source = f"data/customers.json (delivered since {since_date})"
    else:
        revenue, counts = revenue_from_cost_rows(rows)
        revenue_source = "estimated from cost log (one audit per unique customer_id)"

    margin_ratio = ((revenue - total_cost) / revenue) if revenue > 0 else 0.0

    print(f"  Period:            last {days} days (since {since_date} UTC)")
    print(f"  Total AI cost:     {_fmt_usd(total_cost)}")
    print(f"  Total revenue:     {_fmt_usd(revenue)}   [{revenue_source}]")
    if revenue > 0:
        margin_emoji = "OK " if margin_ratio >= 0.70 else "!! "
        print(
            f"  Margin:            {margin_emoji}{_fmt_ratio(margin_ratio)}   "
            f"(target >=70%; gap5 spec)"
        )
    else:
        print("  Margin:            n/a (no completed audits in window)")

    print()
    print("  Audits counted by tier:")
    for tier in ("Starter Package", "Full Package", "Pro Package"):
        n = counts.get(tier, 0)
        print(f"    {n:>3}  {tier:<18}  @ ${TIER_PRICE_USD.get(tier, 0):.2f}")

    print()
    print("  Average AI cost per audit by tier:")
    grouped = group_rows_by_customer(rows)
    per_tier_costs: dict[str, list[float]] = defaultdict(list)
    for cid, rows_for_cust in grouped.items():
        if cid == "unknown":
            continue
        c = summarize_customer(rows_for_cust)
        per_tier_costs[c["tier"]].append(c["cost_usd"])
    for tier in ("Starter Package", "Full Package", "Pro Package"):
        costs = per_tier_costs.get(tier, [])
        if not costs:
            print(f"    {tier:<18}  (no audits)")
            continue
        avg = sum(costs) / len(costs)
        avg_ratio = avg / TIER_PRICE_USD.get(tier, 1.0)
        print(
            f"    {tier:<18}  avg {_fmt_usd(avg)}  "
            f"({_fmt_ratio(avg_ratio)} of tier price; n={len(costs)})"
        )

    outliers: list[tuple[str, dict[str, Any], float]] = []
    for cid, rows_for_cust in grouped.items():
        if cid == "unknown":
            continue
        c = summarize_customer(rows_for_cust)
        price = TIER_PRICE_USD.get(c["tier"], 0)
        if price <= 0:
            continue
        ratio = c["cost_usd"] / price
        if ratio > cost_tracker.PER_CUSTOMER_HIGH_COST_RATIO:
            outliers.append((cid, c, ratio))
    if outliers:
        print()
        print(
            f"  High-cost outliers (>{int(cost_tracker.PER_CUSTOMER_HIGH_COST_RATIO * 100)}% "
            "of tier price):"
        )
        for cid, c, ratio in sorted(outliers, key=lambda x: -x[2]):
            print(
                f"    {cid:<24}  {c['tier']:<18}  "
                f"{_fmt_usd(c['cost_usd'])} ({_fmt_ratio(ratio)})  "
                f"calls={c['call_count']}"
            )
    return 0


def mode_alert(days: int) -> int:
    rows = list(cost_tracker.iter_rows_since(days))
    alerts: list[str] = []

    # 1. Per-customer cost > 20% of tier price
    grouped = group_rows_by_customer(rows)
    for cid, rows_for_cust in grouped.items():
        if cid == "unknown":
            continue
        c = summarize_customer(rows_for_cust)
        price = TIER_PRICE_USD.get(c["tier"], 0)
        if price <= 0:
            continue
        ratio = c["cost_usd"] / price
        if ratio > cost_tracker.PER_CUSTOMER_COST_ALERT_RATIO:
            alerts.append(
                f"[high-cost-customer] {cid} ({c['tier']}): "
                f"{_fmt_usd(c['cost_usd'])} = {_fmt_ratio(ratio)} of tier price "
                f"(threshold {int(cost_tracker.PER_CUSTOMER_COST_ALERT_RATIO * 100)}%)"
            )

    # 2. Daily total cost > $50
    by_day: dict[str, float] = defaultdict(float)
    for r in rows:
        day = (r.get("timestamp") or "")[:10]
        by_day[day] += float(r.get("cost_usd", 0.0))
    for day, total in sorted(by_day.items()):
        if total > cost_tracker.DAILY_COST_ALERT_USD:
            alerts.append(
                f"[daily-spend] {day}: {_fmt_usd(total)} > "
                f"{_fmt_usd(cost_tracker.DAILY_COST_ALERT_USD)} sanity-check threshold"
            )

    # 3. Per-customer call count > 15 (suggests loop / retry storm)
    for cid, rows_for_cust in grouped.items():
        if cid == "unknown":
            continue
        n = len(rows_for_cust)
        if n > cost_tracker.PER_CUSTOMER_CALL_COUNT_ALERT:
            alerts.append(
                f"[runaway-calls] {cid}: {n} calls > "
                f"{cost_tracker.PER_CUSTOMER_CALL_COUNT_ALERT} (probable prompt loop / retry storm)"
            )

    print()
    print(f"LaunchLook AI cost report - alerts over last {days} days")
    print(_hr("="))
    if not alerts:
        print("  No alerts. Margin and per-call cost are within thresholds.")
        return 0
    for line in alerts:
        print(f"  {line}")
    return 0


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------


def _days_ago(days: int) -> str:
    from datetime import timedelta

    cutoff = datetime.now(UTC) - timedelta(days=max(0, days - 1))
    return cutoff.strftime("%Y-%m-%d")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report on LaunchLook AI cost log (internal-only tool).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--date", help="YYYY-MM-DD (UTC). Daily totals + per-model breakdown.")
    parser.add_argument("--customer", help="Aggregate cost for one customer slug.")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Period summary with margin analysis. Use with --days.",
    )
    parser.add_argument(
        "--alert",
        action="store_true",
        help="Print threshold-trip alerts only. Use with --days.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Window for --summary / --alert (default: 7).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    modes = [bool(args.date), bool(args.customer), args.summary, args.alert]
    if sum(1 for m in modes if m) != 1:
        print(
            "ERROR: pick exactly one mode: --date YYYY-MM-DD, --customer SLUG, "
            "--summary, or --alert.",
            file=sys.stderr,
        )
        return 2

    if args.date:
        return mode_daily(args.date)
    if args.customer:
        return mode_customer(args.customer)
    if args.summary:
        return mode_summary(max(1, args.days))
    if args.alert:
        return mode_alert(max(1, args.days))
    return 2  # unreachable


if __name__ == "__main__":
    sys.exit(main())
