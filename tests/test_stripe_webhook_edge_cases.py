"""Tests for edge cases in api/stripe-webhook.py.

Covers:
  - process_event ignores unknown event types (no-op)
  - Duplicate checkout.session.completed delivery: the second call should
    *update* the existing row, NOT create a second Notion row (idempotency).
    This verifies the upsert_customer behaviour under Stripe's at-least-once
    delivery guarantee.
  - Unknown tier amount: tier is None, Notion row still created, notes hint
    includes the amount so Rob can identify it.
  - Session with no email returns an error dict, not a 500 exception.
  - Confidence-check session (metadata.product=confidence_check) is NOT routed
    to the standard audit flow.
  - Handoff-report session (metadata.product=handoff_report) is NOT routed to
    the standard audit flow.
  - cents_to_tier mapping covers all documented SKUs.

Runs two ways:
  * pytest tests/test_stripe_webhook_edge_cases.py
  * python tests/test_stripe_webhook_edge_cases.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_CUSTOMERS_DB_ID", "test-customers-db-id")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_placeholder")

_STRIPE_WEBHOOK_PATH = REPO_ROOT / "api" / "stripe-webhook.py"
_spec = importlib.util.spec_from_file_location("stripe_webhook_api", _STRIPE_WEBHOOK_PATH)
stripe_webhook = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(stripe_webhook)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session(
    *,
    email: str = "customer@example.com",
    name: str = "Test Customer",
    amount_cents: int = 1900,
    session_id: str = "cs_test_123",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": session_id,
        "object": "checkout.session",
        "customer_details": {"email": email, "name": name},
        "amount_total": amount_cents,
        "currency": "usd",
        "metadata": metadata or {},
    }


def _make_event(session: dict[str, Any], event_type: str = "checkout.session.completed") -> dict[str, Any]:
    return {
        "type": event_type,
        "data": {"object": session},
    }


def _noop_upsert(
    client: Any, ds_id: str, fields: dict[str, Any], email_for_match: str
) -> tuple[str, str]:
    """Stub that always creates (returns 'created')."""
    return ("page-id-1", "created")


# ---------------------------------------------------------------------------
# cents_to_tier mapping
# ---------------------------------------------------------------------------


class CentsToTierCase(unittest.TestCase):
    def test_starter_1900(self) -> None:
        self.assertEqual(stripe_webhook.cents_to_tier(1900), "Starter Package")

    def test_scale_up_4900(self) -> None:
        self.assertEqual(stripe_webhook.cents_to_tier(4900), "Scale Up Package")

    def test_pro_9900(self) -> None:
        self.assertEqual(stripe_webhook.cents_to_tier(9900), "Pro Package")

    def test_legacy_starter_900(self) -> None:
        self.assertEqual(stripe_webhook.cents_to_tier(900), "Starter Package")

    def test_legacy_scale_up_2900(self) -> None:
        self.assertEqual(stripe_webhook.cents_to_tier(2900), "Scale Up Package")

    def test_unknown_amount_returns_none(self) -> None:
        self.assertIsNone(stripe_webhook.cents_to_tier(9999))

    def test_none_amount_returns_none(self) -> None:
        self.assertIsNone(stripe_webhook.cents_to_tier(None))


# ---------------------------------------------------------------------------
# process_event routing
# ---------------------------------------------------------------------------


class ProcessEventRoutingCase(unittest.TestCase):
    def test_non_checkout_event_ignored(self) -> None:
        event = {"type": "customer.subscription.created", "data": {}}
        result = stripe_webhook.process_event(event)
        self.assertEqual(result["status"], "ignored")
        self.assertEqual(result["event_type"], "customer.subscription.created")

    def test_unknown_event_type_ignored(self) -> None:
        result = stripe_webhook.process_event({"type": "totally.unknown", "data": {}})
        self.assertEqual(result["status"], "ignored")

    def test_empty_event_dict_ignored(self) -> None:
        result = stripe_webhook.process_event({})
        self.assertEqual(result["status"], "ignored")

    def test_confidence_check_metadata_routes_to_confidence_check(self) -> None:
        session = _make_session(
            amount_cents=1900,
            metadata={"product": "confidence_check"},
        )
        event = _make_event(session)
        # find_customer_by_email is a local import inside process_checkout_session;
        # patch it on the _lib.notion_helpers module rather than the top-level module.
        import _lib.notion_helpers as _nh
        with patch.object(stripe_webhook, "get_client", return_value=MagicMock()), \
             patch.object(stripe_webhook, "get_customers_ds_id", return_value="ds-id"), \
             patch.object(_nh, "find_customer_by_email", return_value=None), \
             patch.object(stripe_webhook, "upsert_customer", side_effect=_noop_upsert):
            result = stripe_webhook.process_event(event)
        # Should be handled as confidence_check, not as a regular audit
        self.assertEqual(result.get("product"), "confidence_check")
        self.assertNotIn("tier", result)

    def test_handoff_report_metadata_routes_to_handoff_report(self) -> None:
        session = _make_session(
            amount_cents=4900,
            metadata={"product": "handoff_report"},
        )
        event = _make_event(session)
        import _lib.notion_helpers as _nh
        with patch.object(stripe_webhook, "get_client", return_value=MagicMock()), \
             patch.object(stripe_webhook, "get_customers_ds_id", return_value="ds-id"), \
             patch.object(_nh, "find_customer_by_email", return_value=None), \
             patch.object(stripe_webhook, "upsert_customer", side_effect=_noop_upsert):
            result = stripe_webhook.process_event(event)
        self.assertEqual(result.get("product"), "handoff_report")
        self.assertNotIn("tier", result)


# ---------------------------------------------------------------------------
# Idempotency: duplicate checkout.session.completed
# ---------------------------------------------------------------------------


class DuplicateWebhookCase(unittest.TestCase):
    """Stripe guarantees at-least-once delivery. A duplicate event for the same
    session_id should call upsert_customer twice for the same email, which
    must result in an UPDATE (not a second CREATE) on the second call.

    This test verifies that upsert_customer is called with the same email both
    times, so the caller's database layer can do the email-based match. It does
    NOT test the Notion implementation itself (that lives in notion_helpers),
    but it confirms the webhook passes the correct email_for_match so dedup
    is possible.
    """

    def test_duplicate_event_calls_upsert_with_same_email_both_times(self) -> None:
        session = _make_session(amount_cents=9900, session_id="cs_duplicate_999")
        event = _make_event(session)

        emails_seen: list[str] = []

        def _capturing_upsert(
            client: Any,
            ds_id: str,
            fields: dict[str, Any],
            email_for_match: str,
        ) -> tuple[str, str]:
            emails_seen.append(email_for_match)
            action = "created" if len(emails_seen) == 1 else "updated"
            return ("page-id-1", action)

        import _lib.notion_helpers as _nh
        for _ in range(2):
            with patch.object(stripe_webhook, "get_client", return_value=MagicMock()), \
                 patch.object(stripe_webhook, "get_customers_ds_id", return_value="ds-id"), \
                 patch.object(_nh, "find_customer_by_email", return_value=None), \
                 patch.object(stripe_webhook, "upsert_customer", side_effect=_capturing_upsert):
                stripe_webhook.process_event(event)

        self.assertEqual(len(emails_seen), 2, "upsert should be called once per delivery")
        self.assertEqual(
            emails_seen[0],
            emails_seen[1],
            "both calls must use the same email so the DB layer can deduplicate",
        )


# ---------------------------------------------------------------------------
# Session with no email
# ---------------------------------------------------------------------------


class SessionNoEmailCase(unittest.TestCase):
    def test_session_with_no_email_returns_error_dict_not_exception(self) -> None:
        """A checkout session with no email (malformed Stripe payload) should
        return an error-shaped dict rather than raising an exception."""
        session = {
            "id": "cs_no_email",
            "customer_details": {},
            "amount_total": 1900,
            "metadata": {},
        }
        event = _make_event(session)
        with patch.object(stripe_webhook, "get_client", return_value=MagicMock()), \
             patch.object(stripe_webhook, "get_customers_ds_id", return_value="ds-id"):
            result = stripe_webhook.process_event(event)
        self.assertEqual(result.get("status"), "error")
        self.assertIn("email", str(result.get("reason", "")).lower())


# ---------------------------------------------------------------------------
# Unknown tier amount
# ---------------------------------------------------------------------------


class UnknownTierAmountCase(unittest.TestCase):
    def test_unknown_amount_still_creates_notion_row(self) -> None:
        """A checkout for an unrecognised amount (e.g. gift/promo amount)
        should still create a Notion row; the Notes field should contain
        a hint about the unknown amount so Rob can investigate."""
        session = _make_session(amount_cents=7777)
        event = _make_event(session)

        captured_fields: list[dict[str, Any]] = []

        def _capturing_upsert(
            client: Any, ds_id: str, fields: dict[str, Any], email_for_match: str
        ) -> tuple[str, str]:
            captured_fields.append(fields)
            return ("page-x", "created")

        import _lib.notion_helpers as _nh
        with patch.object(stripe_webhook, "get_client", return_value=MagicMock()), \
             patch.object(stripe_webhook, "get_customers_ds_id", return_value="ds-id"), \
             patch.object(_nh, "find_customer_by_email", return_value=None), \
             patch.object(stripe_webhook, "upsert_customer", side_effect=_capturing_upsert):
            stripe_webhook.process_event(event)

        self.assertEqual(len(captured_fields), 1, "should still write one Notion row")
        notes = captured_fields[0].get("notes") or ""
        self.assertIn("7777", notes, msg=f"notes should mention the amount; got: {notes!r}")
        # Tier should be absent from fields or None when unrecognised.
        self.assertIsNone(captured_fields[0].get("tier"))


# ---------------------------------------------------------------------------
# Stdlib-only runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
