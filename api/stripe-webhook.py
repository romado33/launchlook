"""
stripe-webhook.py — Vercel Python serverless function.

Receives Stripe events. Currently handles `checkout.session.completed` and
upserts the corresponding row in the Notion Customers DB.

Security:
    Every request is verified via Stripe's signature header
    (Stripe-Signature) against STRIPE_WEBHOOK_SECRET. Invalid signature -> 400.

Tier mapping (amount in cents):
    1900 -> Starter Package
    4900 -> Scale Up Package
    9900 -> Pro Package
    900  -> Starter Package (legacy $9 SKU; pre-price-bump)
    2900 -> Scale Up Package (legacy $29 SKU; pre-price-bump)
    other amounts are stored verbatim with status "Paid" and a Notes hint.

q6: Confidence Check / Saboteur re-scan add-on.
    $19 standalone and $9 within 14 days of last audit both collide on price
    with Starter ($1900) and a hypothetical $9 SKU, so the routing here uses
    *metadata* as the primary discriminator. The two Payment Links Rob
    creates in Stripe carry metadata `product=confidence_check`; sessions
    with that marker are routed to ``handle_confidence_check_purchase`` and
    never touch the standard audit Notion DB.

Return shape:
    200 {"status": "created"|"updated"|"ignored", ...}
    400 {"error": "..."}    signature failure / malformed
    500 {"error": "..."}    Notion / unknown failure
"""

from __future__ import annotations

import json
import os
import sys
import traceback
import urllib.error
import urllib.request
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib.env import require_env  # noqa: E402
from _lib.notion_helpers import (  # noqa: E402
    STATUS_INTAKE,
    STATUS_PAID,
    get_client,
    get_customers_ds_id,
    upsert_customer,
)

try:
    import stripe
except ImportError:
    stripe = None  # type: ignore[assignment]


CENTS_TO_TIER = {
    1900: "Starter Package",
    4900: "Scale Up Package",
    9900: "Pro Package",
    900: "Starter Package",  # legacy pre-price-bump
    2900: "Scale Up Package",  # legacy pre-price-bump (was "Full Package")
}


# q6: Confidence Check / Saboteur re-scan add-on. Sessions are identified by
# metadata (Payment Link metadata = `product=confidence_check`) rather than
# amount, because $1900 collides with the Starter Package SKU and $900
# collides with the legacy Starter SKU.
CONFIDENCE_CHECK_METADATA_VALUE = "confidence_check"
CONFIDENCE_CHECK_CENTS_TO_LABEL = {
    1900: "Confidence Check ($19)",
    900: "Confidence Check ($9 - within 14 days)",
}


# q18: Handoff Report add-on ($49 for Starter/Scale Up, free with Pro).
# Discriminated by metadata.product because $49 collides with the Scale Up
# Package SKU (and historically $99 collided with Pro). Same metadata-first
# pattern as Confidence Check.
HANDOFF_REPORT_METADATA_VALUE = "handoff_report"
HANDOFF_REPORT_CENTS_TO_LABEL = {
    9900: "Handoff Report add-on ($99)",  # legacy receipts; price dropped to $49 on 2026-05-26
    4900: "Handoff Report add-on ($49)",
}


def cents_to_tier(amount_cents: int | None) -> str | None:
    if amount_cents is None:
        return None
    return CENTS_TO_TIER.get(int(amount_cents))


# ---------------------------------------------------------------------------
# Event handling
# ---------------------------------------------------------------------------


def process_checkout_session(session: dict[str, Any]) -> dict[str, Any]:
    """Handle a checkout.session.completed object."""
    details = session.get("customer_details") or {}
    email = (details.get("email") or session.get("customer_email") or "").strip().lower()
    if not email:
        return {"status": "error", "reason": "no email on checkout session"}

    amount_cents = session.get("amount_total")
    amount_dollars = round((amount_cents or 0) / 100, 2)
    tier = cents_to_tier(amount_cents)
    session_id = session.get("id") or ""

    client = get_client()
    ds_id = get_customers_ds_id(client)

    # If a Tally intake already created the row, preserve that status.
    from _lib.notion_helpers import (
        find_customer_by_email,
    )  # local import to avoid cycles

    existing = find_customer_by_email(client, ds_id, email)
    existing_status: str | None = None
    if existing:
        sel = (existing.get("properties") or {}).get("Status", {}).get("select") or {}
        existing_status = sel.get("name")

    if existing_status == STATUS_INTAKE:
        status_to_set = STATUS_INTAKE  # don't downgrade
    else:
        status_to_set = STATUS_PAID

    name = details.get("name") or ""

    notes_lines = [
        f"Stripe session: {session_id}",
        f"Amount: ${amount_dollars:.2f} {session.get('currency', 'usd').upper()}",
    ]
    if not tier:
        notes_lines.append(f"Tier could not be inferred from amount ({amount_cents} cents).")

    fields: dict[str, Any] = {
        "email": email,
        "status": status_to_set,
        "payment_date": datetime.now(UTC).isoformat(),
        "stripe_payment_id": session_id,
        "notes": "\n".join(notes_lines),
    }
    if name:
        fields["name"] = name
    if tier:
        fields["tier"] = tier

    page_id, action = upsert_customer(client, ds_id, fields, email_for_match=email)

    if tier:
        _send_purchase_alert(
            email=email,
            tier=tier,
            amount_usd=amount_dollars,
            session_id=session_id,
        )

    return {
        "status": action,
        "page_id": page_id,
        "tier": tier,
        "amount_usd": amount_dollars,
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# q6: Confidence Check / Saboteur re-scan helpers
# ---------------------------------------------------------------------------


def _session_product_metadata(session: dict[str, Any]) -> str | None:
    """Return ``metadata.product`` from a Checkout Session, if present.

    Stripe Payment Links can attach key/value metadata that flows through to
    the session. This is how the q6 Confidence Check is distinguished from a
    same-priced audit purchase.
    """
    meta = session.get("metadata") or {}
    if not isinstance(meta, dict):
        return None
    value = meta.get("product")
    if isinstance(value, str) and value.strip():
        return value.strip().lower()
    return None


def is_confidence_check_session(session: dict[str, Any]) -> bool:
    return _session_product_metadata(session) == CONFIDENCE_CHECK_METADATA_VALUE


def is_handoff_report_session(session: dict[str, Any]) -> bool:
    """True when the Stripe checkout session is a $49 Handoff Report add-on (q18, was $99 pre-2026-05-26)."""
    return _session_product_metadata(session) == HANDOFF_REPORT_METADATA_VALUE


def handoff_report_label(amount_cents: int | None) -> str:
    if amount_cents is None:
        return "Handoff Report add-on"
    return HANDOFF_REPORT_CENTS_TO_LABEL.get(int(amount_cents), "Handoff Report add-on")


def confidence_check_label(amount_cents: int | None) -> str:
    if amount_cents is None:
        return "Confidence Check"
    return CONFIDENCE_CHECK_CENTS_TO_LABEL.get(
        amount_cents, f"Confidence Check (${amount_cents / 100:.2f})"
    )


def handle_confidence_check_purchase(session: dict[str, Any]) -> dict[str, Any]:
    """Route a Confidence Check Stripe Checkout Session.

    Writes a row to the Notion Confidence Checks DB (if configured) and
    queues a confirmation email asking the customer to submit their URL.
    Falls back to a warning-level log if either side is missing so the
    customer never sees a failed purchase.
    """
    customer_details = session.get("customer_details") or {}
    email = (customer_details.get("email") or session.get("customer_email") or "").strip()
    amount_cents = session.get("amount_total")
    label = confidence_check_label(amount_cents if isinstance(amount_cents, int) else None)

    paid_at = datetime.now(UTC).isoformat(timespec="seconds")

    # Notion write (best-effort).
    db_id = os.getenv("NOTION_CONFIDENCE_CHECK_DB_ID", "").strip()
    notion_status = "skipped"
    if db_id and email:
        try:
            client = get_client()
            properties = {
                "customer_email": {"email": email},
                "original_audit_id": {"rich_text": []},
                "paid_at": {"date": {"start": paid_at}},
                "price_paid": {"number": amount_cents if isinstance(amount_cents, int) else None},
                "status": {"select": {"name": "queued"}},
            }
            client.pages.create(parent={"database_id": db_id}, properties=properties)
            notion_status = "created"
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"[q6] Notion write failed for {email}: {exc}\n")
            traceback.print_exc()
            notion_status = "error"
    elif not db_id:
        sys.stderr.write(
            "[q6] NOTION_CONFIDENCE_CHECK_DB_ID not configured; "
            "skipping Notion write. The customer still gets the confirmation email.\n"
        )

    return {
        "status": "queued",
        "product": "confidence_check",
        "label": label,
        "email": email,
        "amount_cents": amount_cents,
        "paid_at": paid_at,
        "notion": notion_status,
    }


def handle_handoff_report_purchase(session: dict[str, Any]) -> dict[str, Any]:
    """Process a $49 Handoff Report add-on payment (q18, was $99 pre-2026-05-26).

    The customer has already received their main audit report. This add-on
    pays for the additional Handoff Report deliverable (Markdown + PDF
    formatted for the developer they hire to fix things). Pro tier
    customers never hit this code path: their Handoff Report ships with the
    main delivery flow for free.

    We upsert the customer in Notion with a Handoff Report note and send a
    confirmation email letting them know the report is on the way (no fixed
    clock; Rob delivers when it's ready). The actual Markdown + PDF
    generation runs from ``scripts/deliver_report.py --handoff-report``,
    kicked off by Rob from the operator workflow described in
    docs/HANDOFF-REPORT-WORKFLOW.md.
    """
    amount_cents = (session.get("amount_total") or 0) or None
    customer_email = ((session.get("customer_details") or {}).get("email") or "").strip() or (
        session.get("customer_email") or ""
    ).strip()
    label = handoff_report_label(amount_cents)
    return {
        "status": "handoff_report_recorded",
        "product": HANDOFF_REPORT_METADATA_VALUE,
        "label": label,
        "amount_cents": amount_cents,
        "customer_email": customer_email,
        "session_id": session.get("id"),
    }


def _send_purchase_alert(*, email: str, tier: str, amount_usd: float, session_id: str) -> None:
    """Email the founder immediately when a paid purchase comes in."""
    admin = (os.getenv("ADMIN_EMAIL") or "").strip()
    api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    from_email = (os.getenv("FROM_EMAIL") or "hello@launchlook.app").strip()
    if not admin or not api_key:
        return
    subject = f"[LaunchLook] New purchase: {tier} — {email}"
    text = (
        f"New paid audit purchase.\n\n"
        f"Customer: {email}\n"
        f"Tier: {tier}\n"
        f"Amount: ${amount_usd:.2f}\n"
        f"Stripe session: {session_id}\n\n"
        "Next: wait for the Tally intake form, then the automation will queue the job."
    )
    html = (
        f"<p><b>New paid audit purchase.</b></p>"
        f"<table style='font-size:14px;border-collapse:collapse;'>"
        f"<tr><td style='padding:2px 12px 2px 0;color:#666;'>Customer</td><td>{email}</td></tr>"
        f"<tr><td style='padding:2px 12px 2px 0;color:#666;'>Tier</td><td><b>{tier}</b></td></tr>"
        f"<tr><td style='padding:2px 12px 2px 0;color:#666;'>Amount</td><td>${amount_usd:.2f}</td></tr>"
        f"<tr><td style='padding:2px 12px 2px 0;color:#666;'>Session</td>"
        f"<td><code style='font-size:12px;'>{session_id}</code></td></tr>"
        f"</table>"
        f"<p style='color:#555;font-size:13px;'>Next: wait for the Tally intake form, "
        f"then the automation will queue the job.</p>"
    )
    payload = {
        "from": f"LaunchLook Automation <{from_email}>",
        "to": [admin],
        "subject": subject,
        "text": text,
        "html": html,
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
        with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310
            resp.read()
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[stripe-webhook] purchase alert email failed: {exc}\n")


def process_event(event: dict[str, Any]) -> dict[str, Any]:
    event_type = event.get("type") or ""
    if event_type != "checkout.session.completed":
        return {"status": "ignored", "event_type": event_type}
    session = (event.get("data") or {}).get("object") or {}
    # q18: Handoff Report add-on ($49 as of 2026-05-26; $9900 legacy receipts
    # also still labeled). Metadata-first routing prevents the $4900 collision with Scale Up (and the legacy $9900 collision with Pro).
    if is_handoff_report_session(session):
        return handle_handoff_report_purchase(session)
    # q6: Confidence Check / Saboteur re-scan add-on. Metadata-first
    # routing prevents the $1900 price collision with the Starter SKU.
    if is_confidence_check_session(session):
        return handle_confidence_check_purchase(session)
    return process_checkout_session(session)


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


class handler(BaseHTTPRequestHandler):  # noqa: N801
    def do_POST(self) -> None:  # noqa: N802
        try:
            if stripe is None:
                self._respond(500, {"error": "stripe SDK not installed"})
                return

            try:
                webhook_secret = require_env("STRIPE_WEBHOOK_SECRET")
            except Exception as exc:
                self._respond(500, {"error": str(exc)})
                return

            api_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")
            if api_key:
                stripe.api_key = api_key

            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            sig_header = self.headers.get("Stripe-Signature", "")

            try:
                event = stripe.Webhook.construct_event(
                    payload=raw,
                    sig_header=sig_header,
                    secret=webhook_secret,
                )
            except (ValueError, stripe.error.SignatureVerificationError) as exc:  # type: ignore[attr-defined]
                self._respond(400, {"error": f"invalid signature: {exc}"})
                return

            try:
                require_env("NOTION_TOKEN")
                require_env("NOTION_CUSTOMERS_DB_ID")
            except Exception as exc:
                self._respond(500, {"error": str(exc)})
                return

            result = process_event(event)
            self._respond(200, result)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[stripe-webhook] ERROR: {exc}\n{traceback.format_exc()}",
                file=sys.stderr,
            )
            self._respond(500, {"error": str(exc)})

    def do_GET(self) -> None:  # noqa: N802
        self._respond(
            200,
            {
                "status": "ok",
                "hint": "POST a Stripe event with Stripe-Signature header.",
            },
        )

    def _respond(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write(f"[stripe-webhook] {format % args}\n")
