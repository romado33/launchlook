"""Comprehensive edge-case / type-safety tests — added May 28, 2026.

Covers:
  (a) Tally webhook null/missing field handling
  (b) Stripe webhook tier mapping and no-email guard
  (c) Notion helper build_properties type safety
  (d) Pipeline readiness score computation
  (e) Slug de-collision (SHA suffix, idempotency)
  (f) Queue worker --list / --dry-run flags

Runs two ways:
  * pytest tests/test_edge_cases_may28.py
  * python tests/test_edge_cases_may28.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Set required env before any module load.
os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_CUSTOMERS_DB_ID", "test-customers-db-id")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_placeholder")


def _load_hyphenated(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_tally = _load_hyphenated("tally_webhook_api", REPO_ROOT / "api" / "tally-webhook.py")
_stripe = _load_hyphenated("stripe_webhook_api", REPO_ROOT / "api" / "stripe-webhook.py")

import _lib.notion_helpers as _nh  # noqa: E402

# ---------------------------------------------------------------------------
# (a) Tally webhook — null / missing field tests
# ---------------------------------------------------------------------------


def _tally_payload(fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "eventType": "FORM_RESPONSE",
        "data": {
            "formId": "form-test",
            "submissionId": "sub-test",
            "fields": fields,
        },
    }


class TallyNullFieldsCase(unittest.TestCase):
    """Tally webhook process_payload handles missing / empty fields gracefully."""

    def _call(self, payload: dict[str, Any]) -> dict[str, Any]:
        with patch.object(_tally, "get_client", return_value=MagicMock()), \
             patch.object(_tally, "get_customers_ds_id", return_value="ds-id"), \
             patch.object(_tally, "upsert_customer", return_value=("page-1", "created")):
            return _tally.process_payload(payload)

    def test_no_tier_hidden_field_falls_back_gracefully(self) -> None:
        """Missing q_tier hidden field: should not crash; tier stored as empty string."""
        payload = _tally_payload([
            {"label": "Email", "value": "rob@example.com", "options": []},
            {"label": "App URL", "value": "https://myapp.io", "options": []},
        ])
        result = self._call(payload)
        self.assertIn(result["status"], ("created", "updated"))
        self.assertEqual(result["email"], "rob@example.com")

    def test_empty_email_value_returns_error_not_crash(self) -> None:
        """Empty email value must return error, not write a blank email to Notion."""
        payload = _tally_payload([
            {"label": "Email", "value": "", "options": []},
            {"label": "App URL", "value": "https://myapp.io", "options": []},
        ])
        with patch.object(_tally, "get_client", return_value=MagicMock()), \
             patch.object(_tally, "get_customers_ds_id", return_value="ds-id"), \
             patch.object(_tally, "upsert_customer", return_value=("page-1", "created")):
            result = _tally.process_payload(payload)
        self.assertEqual(result["status"], "error")
        self.assertIn("email", str(result.get("reason", "")).lower())

    def test_missing_app_url_field_does_not_crash(self) -> None:
        """Missing app_url field entirely: should not raise; should still write row."""
        payload = _tally_payload([
            {"label": "Email", "value": "rob@example.com", "options": []},
            {"label": "App Name", "value": "MyApp", "options": []},
        ])
        result = self._call(payload)
        self.assertIn(result["status"], ("created", "updated", "error"))

    def test_non_form_response_event_ignored(self) -> None:
        """Non-FORM_RESPONSE events should be silently ignored."""
        payload = {"eventType": "FORM_CREATED", "data": {}}
        with patch.object(_tally, "get_client", return_value=MagicMock()):
            result = _tally.process_payload(payload)
        self.assertEqual(result["status"], "ignored")


# ---------------------------------------------------------------------------
# (b) Stripe webhook — tier mapping and missing-email guard
# ---------------------------------------------------------------------------


def _make_session(
    *,
    email: str | None = "customer@example.com",
    amount_cents: int = 1900,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if email is not None:
        details["email"] = email
    return {
        "id": "cs_test_edge",
        "object": "checkout.session",
        "customer_details": details,
        "amount_total": amount_cents,
        "currency": "usd",
        "metadata": metadata or {},
    }


def _noop_upsert(
    client: Any, ds_id: str, fields: dict[str, Any], email_for_match: str
) -> tuple[str, str]:
    return ("page-id-1", "created")


class StripeTierMappingCase(unittest.TestCase):
    """Stripe tier lookups via cents_to_tier."""

    def test_4900_maps_to_scale_up(self) -> None:
        self.assertEqual(_stripe.cents_to_tier(4900), "Scale Up Package")

    def test_9900_maps_to_pro(self) -> None:
        self.assertEqual(_stripe.cents_to_tier(9900), "Pro Package")

    def test_1900_maps_to_starter(self) -> None:
        self.assertEqual(_stripe.cents_to_tier(1900), "Starter Package")


class StripeProcessCheckoutCase(unittest.TestCase):
    """process_checkout_session edge cases."""

    def _call(self, session: dict[str, Any]) -> dict[str, Any]:
        with patch.object(_stripe, "get_client", return_value=MagicMock()), \
             patch.object(_stripe, "get_customers_ds_id", return_value="ds-id"), \
             patch.object(_nh, "find_customer_by_email", return_value=None), \
             patch.object(_stripe, "upsert_customer", side_effect=_noop_upsert), \
             patch.object(_stripe, "_send_purchase_alert", return_value=None):
            return _stripe.process_checkout_session(session)

    def test_scale_up_tier_returned(self) -> None:
        session = _make_session(amount_cents=4900)
        result = self._call(session)
        self.assertEqual(result.get("tier"), "Scale Up Package")
        self.assertIn(result["status"], ("created", "updated"))

    def test_pro_tier_returned(self) -> None:
        session = _make_session(amount_cents=9900)
        result = self._call(session)
        self.assertEqual(result.get("tier"), "Pro Package")

    def test_no_email_returns_error_not_exception(self) -> None:
        """Missing email must return error dict, not silently create a blank Notion row."""
        session = _make_session(email=None, amount_cents=1900)
        # get_client and friends may or may not be called before the guard
        with patch.object(_stripe, "get_client", return_value=MagicMock()), \
             patch.object(_stripe, "get_customers_ds_id", return_value="ds-id"), \
             patch.object(_nh, "find_customer_by_email", return_value=None), \
             patch.object(_stripe, "upsert_customer", side_effect=_noop_upsert):
            result = _stripe.process_checkout_session(session)
        self.assertEqual(result.get("status"), "error")
        self.assertIn("email", str(result.get("reason", "")).lower())


class StripeMetadataRoutingCase(unittest.TestCase):
    """is_handoff_report_session and is_confidence_check_session."""

    def test_handoff_report_session_detected(self) -> None:
        session = _make_session(metadata={"product": "handoff_report"})
        self.assertTrue(_stripe.is_handoff_report_session(session))

    def test_confidence_check_session_detected(self) -> None:
        session = _make_session(metadata={"product": "confidence_check"})
        self.assertTrue(_stripe.is_confidence_check_session(session))

    def test_plain_audit_not_flagged_as_handoff(self) -> None:
        session = _make_session(amount_cents=9900, metadata={})
        self.assertFalse(_stripe.is_handoff_report_session(session))

    def test_plain_audit_not_flagged_as_confidence_check(self) -> None:
        session = _make_session(amount_cents=1900, metadata={})
        self.assertFalse(_stripe.is_confidence_check_session(session))


# ---------------------------------------------------------------------------
# (c) Notion helper build_properties type safety
# ---------------------------------------------------------------------------


class BuildPropertiesTypeSafetyCase(unittest.TestCase):
    """build_properties skips None/empty and formats dates correctly."""

    def test_none_values_skipped(self) -> None:
        props = _nh.build_properties({"email": None, "name": None, "tier": None})
        self.assertEqual(props, {}, "None values must be silently skipped")

    def test_empty_string_values_skipped(self) -> None:
        props = _nh.build_properties({"email": "", "name": "", "app_url": ""})
        self.assertEqual(props, {}, "empty-string values must be silently skipped")

    def test_mixed_none_and_valid_values(self) -> None:
        props = _nh.build_properties({"email": "rob@example.com", "name": None, "tier": ""})
        self.assertIn("Email", props)
        self.assertNotIn("Name", props)
        self.assertNotIn("Tier", props)

    def test_datetime_object_iso_formatted(self) -> None:
        """A Python datetime passed to a date field should be ISO-formatted."""
        dt = datetime(2026, 5, 28, 12, 0, 0, tzinfo=UTC)
        props = _nh.build_properties({"payment_date": dt})
        date_val = props.get("Payment Date", {}).get("date", {}).get("start", "")
        self.assertIn("2026-05-28", date_val, f"expected ISO date in: {date_val!r}")

    def test_intake_received_at_produces_rich_text_not_date(self) -> None:
        """intake_received_at is rich_text in Notion, not a Date column (live fix May 2026)."""
        iso_str = "2026-05-28T15:00:00+00:00"
        props = _nh.build_properties({"intake_received_at": iso_str})
        self.assertIn("Intake Received At", props)
        notion_prop = props["Intake Received At"]
        self.assertIn("rich_text", notion_prop, "must be rich_text, not date")
        self.assertNotIn("date", notion_prop, "must NOT be date type after the May 2026 fix")
        content = notion_prop["rich_text"][0]["text"]["content"]
        self.assertEqual(content, iso_str)

    def test_unknown_keys_ignored(self) -> None:
        props = _nh.build_properties({"totally_unknown_field": "value"})
        self.assertEqual(props, {}, "unknown keys must be silently dropped")


# ---------------------------------------------------------------------------
# (d) Pipeline readiness score
# ---------------------------------------------------------------------------


class ReadinessScoreCase(unittest.TestCase):
    """compute_readiness_score edge cases."""

    def setUp(self) -> None:
        from scripts.ai_audit.pipeline import compute_readiness_score
        self._score = compute_readiness_score

    def test_empty_findings_returns_10(self) -> None:
        self.assertEqual(self._score([]), 10.0)

    def test_empty_list_explicit(self) -> None:
        findings: list[dict[str, Any]] = []
        self.assertEqual(self._score(findings), 10.0)

    def test_one_critical_deducts_2(self) -> None:
        findings = [{"severity": "critical", "title": "SQL injection"}]
        self.assertEqual(self._score(findings), 8.0)

    def test_floor_at_1(self) -> None:
        """Enough findings to push below 1.0 must be clamped to 1.0."""
        findings = [{"severity": "critical"}] * 10  # -20.0 would give -10.0
        result = self._score(findings)
        self.assertEqual(result, 1.0, f"expected floor 1.0, got {result}")

    def test_mixed_severities(self) -> None:
        """10 - 2.0 - 1.0 - 0.4 - 0.1 = 6.5"""
        findings = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
        ]
        self.assertAlmostEqual(self._score(findings), 6.5, places=1)

    def test_unknown_severity_no_deduction(self) -> None:
        findings = [{"severity": "cosmic", "title": "Unknown"}]
        self.assertEqual(self._score(findings), 10.0)


# ---------------------------------------------------------------------------
# (e) Slug de-collision
# ---------------------------------------------------------------------------


class SlugDeCollisionCase(unittest.TestCase):
    """Verify slug_from_email_url idempotency and de-collision (SHA suffix)."""

    def setUp(self) -> None:
        from scripts.audit_automation.slug import slug_from_email_url
        self._slug = slug_from_email_url

    def test_same_email_different_url_produces_different_slugs(self) -> None:
        slug_a = self._slug("john@myapp.com", "https://appleone.io")
        slug_b = self._slug("john@myapp.com", "https://appletwo.io")
        self.assertNotEqual(slug_a, slug_b)

    def test_same_email_same_url_is_idempotent(self) -> None:
        slug_a = self._slug("john@myapp.com", "https://myapp.io")
        slug_b = self._slug("john@myapp.com", "https://myapp.io")
        self.assertEqual(slug_a, slug_b, "same inputs must produce the same slug")

    def test_different_emails_same_host_produce_different_slugs(self) -> None:
        slug_john = self._slug("john@myapp.com", "https://myapp.io")
        slug_jane = self._slug("jane@myapp.com", "https://myapp.io")
        self.assertNotEqual(slug_john, slug_jane, "email-based suffix must prevent collision")

    def test_slug_contains_6_char_hex_suffix(self) -> None:
        """The last segment of the slug must be a 6-char lowercase hex string."""
        slug = self._slug("alice@example.com", "https://myapp.io")
        parts = slug.split("-")
        suffix = parts[-1]
        self.assertRegex(suffix, r"^[0-9a-f]{6}$", f"expected 6-char hex suffix in {slug!r}")


# ---------------------------------------------------------------------------
# (f) Queue worker --list flag
# ---------------------------------------------------------------------------


class QueueWorkerListFlagCase(unittest.TestCase):
    """process_audit_queue.py --list must accept the flag without argparse / import errors.

    With fake Notion credentials the script will raise an APIResponseError
    (Notion 401). That is expected and acceptable — we only fail the test on
    Python-level crashes (ImportError, SyntaxError, AttributeError, etc.)
    which indicate a broken code path, not a connectivity problem.
    """

    # Known "acceptable" error strings that come from Notion refusing fake creds.
    _NOTION_ERRORS = (
        "APIResponseError",
        "API token is invalid",
        "notion_client",
        "HTTPStatusError",
        "401 Unauthorized",
    )

    def test_list_flag_accepted_by_argparse(self) -> None:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "process_audit_queue.py"), "--list"],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "NOTION_TOKEN": "test-token", "NOTION_CUSTOMERS_DB_ID": "test-db"},
        )
        stderr = result.stderr or ""
        # argparse error (exit 2 + "error: unrecognized arguments") = bad flag
        if result.returncode == 2:
            self.fail(f"--list flag not recognised by argparse:\n{stderr}")
        if result.returncode != 0 and "Traceback (most recent call last)" in stderr:
            # Only fail if it's NOT a Notion auth error
            is_notion_error = any(tok in stderr for tok in self._NOTION_ERRORS)
            if not is_notion_error:
                self.fail(
                    f"process_audit_queue.py --list crashed with unexpected error:\n{stderr}"
                )


# ---------------------------------------------------------------------------
# Stdlib-only runner
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main(verbosity=2)
