#!/usr/bin/env python3
"""Send a post-delivery follow-up to customers delivered 3-5 days ago.

Finds Customers DB rows where:
  - Status = Delivered
  - Delivered At date is 3-5 days ago
  - Follow-up Sent At is empty (not already sent)

Sends a short, friendly email asking if the fixes landed and offering
the next tier. Marks Follow-up Sent At in Notion after sending.

This is the upsell window: the customer just fixed the issues from their
audit and is in a "that was useful" moment. One casual email here converts
better than any cold outreach.

Usage:
    python scripts/followup_email.py            # send to eligible customers
    python scripts/followup_email.py --dry-run  # show who would get it, no send
    python scripts/followup_email.py --limit 3  # cap at 3 emails per run
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
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

# Days-after-delivery window to send the follow-up
FOLLOWUP_MIN_DAYS = 3
FOLLOWUP_MAX_DAYS = 5

TIER_UPSELL: dict[str, str] = {
    "Free": "Starter Package",
    "Starter Package": "Scale Up Package",
    "Scale Up Package": "Pro Package",
    "Pro Package": "",  # already at top; skip upsell
}

TIER_PRICE: dict[str, str] = {
    "Starter Package": "$19",
    "Scale Up Package": "$49",
    "Pro Package": "$99",
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
        # Notion date format: "2026-05-28T10:00:00.000+00:00" or "2026-05-28"
        return datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
    except ValueError:
        return None


def find_eligible_customers() -> list[dict]:
    """Return rows eligible for a follow-up email."""
    client = get_client()
    ds_id = get_customers_ds_id(client)
    now = datetime.datetime.now(datetime.UTC)
    window_end = now - datetime.timedelta(days=FOLLOWUP_MIN_DAYS)
    window_start = now - datetime.timedelta(days=FOLLOWUP_MAX_DAYS)

    resp = client.data_sources.query(
        data_source_id=ds_id,
        filter={"property": "Status", "select": {"equals": STATUS_DELIVERED}},
        sorts=[{"timestamp": "last_edited_time", "direction": "descending"}],
        page_size=100,
    )

    eligible: list[dict] = []
    for row in resp.get("results", []):
        if row.get("archived") or row.get("in_trash"):
            continue
        props = row.get("properties") or {}

        # Must have a Delivered At date in the window
        delivered_at = _prop_date(props, "Delivered At")
        if not delivered_at:
            continue
        if not (window_start <= delivered_at <= window_end):
            continue

        # Must not have already sent a follow-up
        followup_sent = _prop_date(props, "Follow-up Sent At")
        if followup_sent:
            continue

        email = _prop_text(props, "Email")
        tier = _prop_text(props, "Tier")
        name = _prop_text(props, "Name")
        app_url = _prop_text(props, "App URL")
        if not email:
            continue

        eligible.append({
            "page_id": row["id"],
            "email": email,
            "name": name,
            "tier": tier,
            "app_url": app_url,
            "delivered_at": delivered_at,
        })

    return eligible


def _first_name(name: str) -> str:
    return (name or "").strip().split()[0] if name.strip() else "there"


def _build_followup_email(customer: dict) -> tuple[str, str, str]:
    """Return (subject, html_body, text_body)."""
    first = _first_name(customer["name"])
    tier = customer["tier"]
    next_tier = TIER_UPSELL.get(tier, "")
    next_price = TIER_PRICE.get(next_tier, "")
    app_url = customer["app_url"] or "your app"

    subject = f"Did the fixes land okay? ({app_url})"

    upsell_text = ""
    upsell_html = ""
    if next_tier and next_price:
        upsell_text = (
            f"\n\nIf you want to go deeper, the {next_tier} ({next_price}) covers "
            f"{'8 more findings' if next_tier == 'Starter Package' else 'more findings, a Quick Start Guide, and a full Handoff Report'}. "
            f"Same process: https://launchlook.app/#pricing"
        )
        upsell_html = (
            f"<p style='margin-top:16px;'>If you want to go deeper, the <b>{next_tier}</b> "
            f"({next_price}) covers "
            f"{'8 more findings' if next_tier == 'Starter Package' else 'more findings, a Quick Start Guide, and a Handoff Report'}. "
            f"<a href='https://launchlook.app/#pricing'>Same process &rarr;</a></p>"
        )

    text_body = (
        f"Hi {first},\n\n"
        f"Just checking in — did the fixes from your LaunchLook audit land okay?\n\n"
        f"If anything was unclear or you hit a snag, reply here and I'll help you through it."
        f"{upsell_text}\n\n"
        f"Rob\n"
        f"LaunchLook\n"
        f"https://launchlook.app"
    )

    html_body = f"""<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#111;max-width:580px;margin:0 auto;padding:16px;font-size:15px;line-height:1.6;">
  <p>Hi {first},</p>
  <p>Just checking in &mdash; did the fixes from your LaunchLook audit land okay?</p>
  <p>If anything was unclear or you hit a snag, reply here and I'll help you through it.</p>
  {upsell_html}
  <p style="margin-top:24px;">Rob<br>
  <a href="https://launchlook.app" style="color:#111;">LaunchLook</a></p>
</body></html>"""

    return subject, html_body, text_body


def _send_customer_email(*, to: str, subject: str, html_body: str, text_body: str) -> bool:
    api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    from_email = (os.getenv("FROM_EMAIL") or "hello@launchlook.app").strip()
    if not api_key:
        print("[followup] WARN: RESEND_API_KEY missing", file=sys.stderr)
        return False
    payload = {
        "from": f"Rob at LaunchLook <{from_email}>",
        "to": [to],
        "subject": subject,
        "text": text_body,
        "html": html_body,
        "reply_to": from_email,
    }
    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "LaunchLook-Automation/1.0 (+https://launchlook.app)",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            resp.read()
        return True
    except urllib.error.HTTPError as exc:
        print(f"[followup] Resend HTTP {exc.code}: {exc.read()[:200]!r}", file=sys.stderr)
    except urllib.error.URLError as exc:
        print(f"[followup] Resend error: {exc}", file=sys.stderr)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Send post-delivery follow-up emails")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show eligible customers, no email sent")
    parser.add_argument("--limit", type=int, default=10,
                        help="Max emails to send per run (default 10)")
    args = parser.parse_args(argv)

    eligible = find_eligible_customers()[: args.limit]

    if not eligible:
        print(f"[followup] No customers in the {FOLLOWUP_MIN_DAYS}-{FOLLOWUP_MAX_DAYS} day follow-up window.")
        return 0

    print(f"[followup] {len(eligible)} customer(s) eligible for follow-up:")
    for c in eligible:
        print(f"  {c['email']:40} tier={c['tier']:20} delivered={c['delivered_at'].date()}")

    if args.dry_run:
        print("[followup] Dry run — no emails sent.")
        return 0

    client = get_client()
    sent = 0
    for customer in eligible:
        subject, html_body, text_body = _build_followup_email(customer)
        ok = _send_customer_email(
            to=customer["email"],
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        if ok:
            now_iso = datetime.datetime.now(datetime.UTC).isoformat()
            update_customer_fields(client, customer["page_id"], {"followup_sent_at": now_iso})
            print(f"[followup] Sent to {customer['email']}")
            sent += 1
        else:
            print(f"[followup] Failed to send to {customer['email']}", file=sys.stderr)

    print(f"[followup] Done: {sent}/{len(eligible)} sent.")
    return 0 if sent == len(eligible) else 1


if __name__ == "__main__":
    sys.exit(main())
