"""
stripe-webhook.py - Vercel Python serverless function.

Receives Stripe events. Currently handles `checkout.session.completed` and
upserts the corresponding row in the Notion Customers DB.

Security:
    Every request is verified via Stripe's signature header
    (Stripe-Signature) against STRIPE_WEBHOOK_SECRET. Invalid signature -> 400.

Tier mapping (amount in cents):
    1900 -> Starter Package
    4900 -> Full Package
    9900 -> Pro Package
    Legacy fallback (in-flight test transactions): 900 -> Starter, 2900 -> Full
    other amounts are stored verbatim with status "Paid" and a Notes hint.

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
from datetime import datetime, timezone
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
    4900: "Full Package",
    9900: "Pro Package",
}

# Legacy amounts kept for backward compatibility with any in-flight test
# transactions that were created before the May 2026 price bump. We log
# a warning when one of these matches so we know to chase the receipt.
LEGACY_CENTS_TO_TIER = {
    900: "Starter Package",
    2900: "Full Package",
}


def cents_to_tier(amount_cents: int | None) -> tuple[str | None, bool]:
    """Resolve an amount in cents to a tier name.

    Returns ``(tier, is_legacy)`` so the caller can log a warning when an
    old (pre-price-bump) amount is observed.
    """
    if amount_cents is None:
        return None, False
    cents = int(amount_cents)
    tier = CENTS_TO_TIER.get(cents)
    if tier:
        return tier, False
    legacy = LEGACY_CENTS_TO_TIER.get(cents)
    if legacy:
        return legacy, True
    return None, False


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
    tier, is_legacy_amount = cents_to_tier(amount_cents)
    if is_legacy_amount:
        print(
            f"[stripe-webhook] WARN: legacy amount {amount_cents} cents detected "
            f"for session {session.get('id')!r}; mapped to {tier!r} via fallback. "
            "Update Stripe products to the new price tiers (1900/4900/9900) "
            "ASAP — this fallback is for in-flight test transactions only.",
            file=sys.stderr,
        )
    session_id = session.get("id") or ""

    client = get_client()
    ds_id = get_customers_ds_id(client)

    # If a Tally intake already created the row, preserve that status.
    from _lib.notion_helpers import find_customer_by_email  # local import to avoid cycles

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
    elif is_legacy_amount:
        notes_lines.append(
            f"Legacy amount ({amount_cents} cents) — mapped to {tier} via fallback. "
            "Verify the Stripe price was updated."
        )

    fields: dict[str, Any] = {
        "email": email,
        "status": status_to_set,
        "payment_date": datetime.now(timezone.utc).isoformat(),
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


def process_event(event: dict[str, Any]) -> dict[str, Any]:
    event_type = event.get("type") or ""
    if event_type != "checkout.session.completed":
        return {"status": "ignored", "event_type": event_type}
    session = (event.get("data") or {}).get("object") or {}
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
            print(f"[stripe-webhook] ERROR: {exc}\n{traceback.format_exc()}", file=sys.stderr)
            self._respond(500, {"error": str(exc)})

    def do_GET(self) -> None:  # noqa: N802
        self._respond(
            200,
            {"status": "ok", "hint": "POST a Stripe event with Stripe-Signature header."},
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
