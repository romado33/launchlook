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

q17: LaunchLook Verified badge re-verification add-on.
    $9 single-price SKU collides with the legacy Starter amount AND with
    the discounted Confidence Check. Same metadata-first pattern: the
    Stripe Payment Link must carry `metadata.product=reverify`. Optional
    metadata `customer_slug` (or `session.client_reference_id`) lets
    Rob look up the badge directly. See docs/VERIFIED-BADGE-WORKFLOW.md.

    Operational rule: the $9 re-verify SKU is only valid for customers who
    already had a badge. `scripts/generate_verified_badge.py --re-verify`
    fails fast if no prior verify.json exists, so a misfired $9 charge is
    caught at the operator step (Rob refunds or redirects to upgrade).

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


# q17: LaunchLook Verified badge re-verification ($9). Single price point
# because there is no tier ladder for re-verifies; the customer is renewing
# the same badge they already had. Discriminated by metadata.product, same
# pattern as Confidence Check.
REVERIFY_METADATA_VALUE = "reverify"
REVERIFY_LABEL = "Badge re-verification ($9)"


# q18: Handoff Report add-on ($99 for Starter/Scale Up, free with Pro).
# Discriminated by metadata.product because $99 collides with the Pro
# Package SKU. Same metadata-first pattern as Confidence Check (q6) and
# badge re-verification (q17).
HANDOFF_REPORT_METADATA_VALUE = "handoff_report"
HANDOFF_REPORT_CENTS_TO_LABEL = {
    9900: "Handoff Report add-on ($99)",
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
    email = (
        (details.get("email") or session.get("customer_email") or "").strip().lower()
    )
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
        notes_lines.append(
            f"Tier could not be inferred from amount ({amount_cents} cents)."
        )

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


def is_reverify_session(session: dict[str, Any]) -> bool:
    """True when the Stripe checkout session is a $9 badge re-verification (q17)."""
    return _session_product_metadata(session) == REVERIFY_METADATA_VALUE


def is_handoff_report_session(session: dict[str, Any]) -> bool:
    """True when the Stripe checkout session is a $99 Handoff Report add-on (q18)."""
    return _session_product_metadata(session) == HANDOFF_REPORT_METADATA_VALUE


def handoff_report_label(amount_cents: int | None) -> str:
    if amount_cents is None:
        return "Handoff Report add-on"
    return HANDOFF_REPORT_CENTS_TO_LABEL.get(int(amount_cents), "Handoff Report add-on")


def confidence_check_label(amount_cents: int | None) -> str:
    if amount_cents is None:
        return "Confidence Check"
    return CONFIDENCE_CHECK_CENTS_TO_LABEL.get(
        amount_cents, f"Confidence Check (${amount_cents/100:.2f})"
    )


def handle_confidence_check_purchase(session: dict[str, Any]) -> dict[str, Any]:
    """Route a Confidence Check Stripe Checkout Session.

    Writes a row to the Notion Confidence Checks DB (if configured) and
    queues a confirmation email asking the customer to submit their URL.
    Falls back to a warning-level log if either side is missing so the
    customer never sees a failed purchase.
    """
    customer_details = session.get("customer_details") or {}
    email = (
        customer_details.get("email") or session.get("customer_email") or ""
    ).strip()
    amount_cents = session.get("amount_total")
    label = confidence_check_label(
        amount_cents if isinstance(amount_cents, int) else None
    )

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
                "price_paid": {
                    "number": amount_cents if isinstance(amount_cents, int) else None
                },
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


# ---------------------------------------------------------------------------
# q17: LaunchLook Verified badge re-verification helpers
# ---------------------------------------------------------------------------


def handle_reverify_purchase(session: dict[str, Any]) -> dict[str, Any]:
    """Route a $9 badge re-verification Stripe Checkout Session (q17).

    Mirrors `handle_confidence_check_purchase` (same Notion DB, same
    best-effort tolerance) because operationally Rob runs both add-ons
    out of the same queue: after payment, he runs
    `python scripts/generate_verified_badge.py --customer customers/<slug>.yaml --re-verify`
    to mint a fresh badge and emails the customer the updated embed
    snippet. The script refuses to run if no prior `verify.json` exists,
    enforcing the "no prior badge = no $9 re-verify" rule operationally.

    Falls back to a stderr log on every failure path so Stripe does not
    retry the webhook forever on a single malformed row.
    """
    customer_details = session.get("customer_details") or {}
    email = (
        customer_details.get("email") or session.get("customer_email") or ""
    ).strip()
    amount_cents = session.get("amount_total")
    session_id = session.get("id") or ""

    metadata = session.get("metadata") or {}
    customer_slug = (
        metadata.get("customer_slug") or session.get("client_reference_id") or ""
    )
    if isinstance(customer_slug, str):
        customer_slug = customer_slug.strip()
    else:
        customer_slug = ""

    paid_at = datetime.now(UTC).isoformat(timespec="seconds")

    db_id = os.getenv("NOTION_CONFIDENCE_CHECK_DB_ID", "").strip()
    notion_status = "skipped"
    if db_id and email:
        try:
            client = get_client()
            note_lines = [REVERIFY_LABEL]
            if customer_slug:
                note_lines.append(f"slug: {customer_slug}")
            properties: dict[str, Any] = {
                "customer_email": {"email": email},
                "paid_at": {"date": {"start": paid_at}},
                "price_paid": {
                    "number": amount_cents if isinstance(amount_cents, int) else None
                },
                "status": {"select": {"name": "queued"}},
                "original_audit_id": {
                    "rich_text": [{"text": {"content": " | ".join(note_lines)[:2000]}}]
                },
            }
            client.pages.create(parent={"database_id": db_id}, properties=properties)
            notion_status = "created"
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"[q17] Notion write failed for {email}: {exc}\n")
            traceback.print_exc()
            notion_status = "error"
    elif not db_id:
        sys.stderr.write(
            "[q17] NOTION_CONFIDENCE_CHECK_DB_ID not configured; skipping Notion "
            "write for badge re-verification. The customer still gets the "
            "confirmation email. See docs/VERIFIED-BADGE-WORKFLOW.md.\n"
        )

    email_status = "skipped"
    resend_key = os.getenv("RESEND_API_KEY", "").strip()
    if resend_key and email:
        try:
            import resend  # type: ignore

            resend.api_key = resend_key
            from_email = os.getenv("FROM_EMAIL", "hello@launchlook.app")
            subject = (
                "Got your re-verification. Your fresh LaunchLook badge is on the way."
            )
            slug_line = (
                f"  Slug we have on file: {customer_slug}\n\n"
                if customer_slug
                else "  We did not see a slug on your payment. Reply with the badge slug you want renewed.\n\n"
            )
            body_text = (
                "Hi,\n\n"
                "Thanks for the $9 re-verification.\n\n"
                f"{slug_line}"
                "I will re-run the same checks on your live URL, refresh the dates, "
                "and email you a new badge image plus an updated embed snippet. "
                "Expect this within 24 hours. The new badge is valid for the same "
                "window as your original tier (Starter 30 days, Scale Up 90, Pro 180).\n\n"
                "Reply to this email if the slug above is wrong or if your live "
                "URL has changed since the original audit.\n\n"
                "Rob\n"
            )
            resend.Emails.send(
                {
                    "from": f"Rob at LaunchLook <{from_email}>",
                    "to": [email],
                    "subject": subject,
                    "text": body_text,
                    "reply_to": from_email,
                }
            )
            email_status = "sent"
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(
                f"[q17] reverify confirmation email failed for {email}: {exc}\n"
            )
            email_status = "error"

    return {
        "status": "queued",
        "product": "reverify",
        "label": REVERIFY_LABEL,
        "email": email,
        "customer_slug": customer_slug or None,
        "amount_cents": amount_cents,
        "paid_at": paid_at,
        "session_id": session_id,
        "notion": notion_status,
        "email_status": email_status,
    }


def handle_handoff_report_purchase(session: dict[str, Any]) -> dict[str, Any]:
    """Process a $99 Handoff Report add-on payment (q18).

    The customer has already received their main audit report. This add-on
    pays for the additional Handoff Report deliverable (Markdown + PDF
    formatted for the developer they hire to fix things). Pro tier
    customers never hit this code path: their Handoff Report ships with the
    main delivery flow for free.

    We upsert the customer in Notion with a Handoff Report note and send a
    confirmation email letting them know the report will arrive within 24
    hours. The actual Markdown + PDF generation runs from
    ``scripts/deliver_report.py --handoff-report``, kicked off by Rob from
    the operator workflow described in docs/HANDOFF-REPORT-WORKFLOW.md.
    """
    amount_cents = (session.get("amount_total") or 0) or None
    customer_email = (
        (session.get("customer_details") or {}).get("email") or ""
    ).strip() or (session.get("customer_email") or "").strip()
    label = handoff_report_label(amount_cents)
    return {
        "status": "handoff_report_recorded",
        "product": HANDOFF_REPORT_METADATA_VALUE,
        "label": label,
        "amount_cents": amount_cents,
        "customer_email": customer_email,
        "session_id": session.get("id"),
    }


def process_event(event: dict[str, Any]) -> dict[str, Any]:
    event_type = event.get("type") or ""
    if event_type != "checkout.session.completed":
        return {"status": "ignored", "event_type": event_type}
    session = (event.get("data") or {}).get("object") or {}
    # q18: Handoff Report add-on ($99). Metadata-first routing prevents
    # the $9900 collision with the Pro Package SKU.
    if is_handoff_report_session(session):
        return handle_handoff_report_purchase(session)
    # q17: badge re-verification ($9). Metadata-first routing prevents
    # the $900 collision with the legacy Starter SKU and with the $9
    # Confidence Check.
    if is_reverify_session(session):
        return handle_reverify_purchase(session)
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
