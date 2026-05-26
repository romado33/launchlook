"""Tests for ``scripts/ai_audit/form_smoke_test.py`` (q15).

Covers the four cases the task spec calls out:

1. SYNTHETIC_VALUES dispatch (email field -> email value, phone field
   -> phone value, name field -> name value, password field ->
   password value, fallback to default_text).
2. Tier-cap in ``to_findings`` (Starter = 1 actionable, Scale Up = 3,
   Pro = all).
3. Checkout / payment / destructive forms get SKIPPED (no submit, but
   a low-severity "we saw it" finding is surfaced).
4. The disposable-mailbox round-trip is only invoked for the Pro tier
   (and only for forms that capture an email).

Plus a stability case: the persona tag on every finding stays the
canonical "Caught by The Stranger Who Tried to Sign Up" string so
the report's persona-pill CSS picks it up.

Runnable two ways (mirrors ``tests/test_dedup.py``):

* ``pytest tests/test_form_smoke_test.py`` if pytest is installed.
* ``python tests/test_form_smoke_test.py`` for a stdlib-only run.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ai_audit import form_smoke_test as fst  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _newsletter_form() -> dict:
    """A clean newsletter signup form (1 email field, Subscribe button)."""
    return {
        "index": 0,
        "selector": "#newsletter",
        "id": "newsletter",
        "name": "Newsletter signup",
        "action": "/api/subscribe",
        "method": "post",
        "submit_label": "Subscribe",
        "field_count": 1,
        "fields": [
            {
                "tag": "input",
                "type": "email",
                "name": "email",
                "id": "email",
                "placeholder": "you@example.com",
                "autocomplete": "email",
                "required": True,
                "label": "Email address",
            },
        ],
        "parent_haystack": "footer site-footer",
    }


def _contact_form() -> dict:
    """A multi-field contact form (name + email + message)."""
    return {
        "index": 1,
        "selector": "#contact",
        "id": "contact",
        "name": "Contact us",
        "action": "/api/contact",
        "method": "post",
        "submit_label": "Send message",
        "field_count": 3,
        "fields": [
            {
                "tag": "input",
                "type": "text",
                "name": "full_name",
                "id": "name",
                "placeholder": "Your name",
                "autocomplete": "name",
                "required": True,
                "label": "Name",
            },
            {
                "tag": "input",
                "type": "email",
                "name": "email",
                "id": "email-contact",
                "placeholder": "you@example.com",
                "autocomplete": "email",
                "required": True,
                "label": "Email",
            },
            {
                "tag": "textarea",
                "type": "textarea",
                "name": "message",
                "id": "msg",
                "placeholder": "How can we help?",
                "autocomplete": "",
                "required": False,
                "label": "Message",
            },
        ],
        "parent_haystack": "section contact-section",
    }


def _checkout_form() -> dict:
    """A checkout / payment form -- must be SKIPPED."""
    return {
        "index": 2,
        "selector": "#prod-checkout",
        "id": "prod-checkout",
        "name": "Complete your order",
        "action": "/api/checkout",
        "method": "post",
        "submit_label": "Pay $19",
        "field_count": 3,
        "fields": [
            {
                "tag": "input",
                "type": "text",
                "name": "card_number",
                "id": "cc-number",
                "placeholder": "Card number",
                "autocomplete": "cc-number",
                "required": True,
                "label": "Card number",
            },
            {
                "tag": "input",
                "type": "text",
                "name": "cvv",
                "id": "cc-cvv",
                "placeholder": "CVV",
                "autocomplete": "cc-csc",
                "required": True,
                "label": "CVV",
            },
        ],
        "parent_haystack": "section checkout billing",
    }


def _delete_account_form() -> dict:
    """A destructive 'Delete my account' form -- must be SKIPPED."""
    return {
        "index": 3,
        "selector": "#delete-account",
        "id": "delete-account",
        "name": "Delete account",
        "action": "/api/account",
        "method": "post",
        "submit_label": "Delete my account",
        "field_count": 1,
        "fields": [
            {
                "tag": "input",
                "type": "text",
                "name": "confirm",
                "id": "confirm",
                "placeholder": "Type DELETE",
                "autocomplete": "",
                "required": True,
                "label": "Confirm",
            },
        ],
        "parent_haystack": "settings danger-zone",
    }


def _phone_form() -> dict:
    """A form whose visible field is a phone input (no email field)."""
    return {
        "index": 4,
        "selector": "#callback",
        "id": "callback",
        "name": "Request callback",
        "action": "/api/callback",
        "method": "post",
        "submit_label": "Call me",
        "field_count": 1,
        "fields": [
            {
                "tag": "input",
                "type": "tel",
                "name": "phone",
                "id": "phone",
                "placeholder": "+1 555 ...",
                "autocomplete": "tel",
                "required": True,
                "label": "Phone",
            },
        ],
        "parent_haystack": "section callback",
    }


# ---------------------------------------------------------------------------
# Case 1: SYNTHETIC_VALUES dispatch on field type / name keywords
# ---------------------------------------------------------------------------


class SyntheticValueDispatchCase(unittest.TestCase):
    def test_email_input_type_picks_email_value(self) -> None:
        value, key = fst._synthetic_value_for({"type": "email", "name": "anything"})
        self.assertEqual(key, "email")
        self.assertEqual(value, fst.SYNTHETIC_VALUES["email"])

    def test_phone_input_type_picks_phone_value(self) -> None:
        value, key = fst._synthetic_value_for({"type": "tel", "name": "callme"})
        self.assertEqual(key, "phone")
        self.assertEqual(value, fst.SYNTHETIC_VALUES["phone"])

    def test_password_input_type_picks_password_value(self) -> None:
        value, key = fst._synthetic_value_for({"type": "password", "name": "pwd"})
        self.assertEqual(key, "password")
        self.assertEqual(value, fst.SYNTHETIC_VALUES["password"])

    def test_first_name_keyword_picks_first_name(self) -> None:
        value, key = fst._synthetic_value_for({"type": "text", "name": "first_name"})
        self.assertEqual(key, "first_name")
        self.assertEqual(value, fst.SYNTHETIC_VALUES["first_name"])

    def test_full_name_keyword_picks_name(self) -> None:
        # "full_name" should fall through to the generic ``name`` family
        # (the hint list explicitly maps full_name -> name before the
        # shorter ``name`` substring catches everything).
        value, key = fst._synthetic_value_for({"type": "text", "name": "full_name"})
        self.assertEqual(key, "name")
        self.assertEqual(value, fst.SYNTHETIC_VALUES["name"])

    def test_message_keyword_picks_message_value(self) -> None:
        value, key = fst._synthetic_value_for({"type": "textarea", "name": "message"})
        self.assertEqual(key, "message")
        self.assertEqual(value, fst.SYNTHETIC_VALUES["message"])

    def test_unknown_field_falls_back_to_default_text(self) -> None:
        value, key = fst._synthetic_value_for(
            {"type": "text", "name": "x", "placeholder": "??"}
        )
        self.assertEqual(key, "default_text")
        self.assertEqual(value, fst.SYNTHETIC_VALUES["default_text"])

    def test_synthetic_values_label_themselves_as_launchlook_smoke_test(self) -> None:
        # Per the task spec: every text value must identify itself so the
        # customer can grep their inbox / database for our rows.
        labelled = (
            "email",
            "name",
            "first_name",
            "company",
            "message",
            "comment",
            "default_text",
        )
        for key in labelled:
            with self.subTest(key=key):
                self.assertIn(
                    "launchlook",
                    fst.SYNTHETIC_VALUES[key].lower(),
                    msg=f"SYNTHETIC_VALUES[{key!r}] should label itself",
                )


# ---------------------------------------------------------------------------
# Case 2: Tier cap inside ``to_findings``
# ---------------------------------------------------------------------------


def _three_failed_results() -> list[dict]:
    """Three forms all returning ``no_response`` (high severity)."""
    return [
        {"form": _newsletter_form(), "outcome": "no_response", "filled": {}},
        {"form": _contact_form(), "outcome": "no_response", "filled": {}},
        {"form": _phone_form(), "outcome": "no_response", "filled": {}},
    ]


class TierCapCase(unittest.TestCase):
    def test_starter_caps_at_one_actionable_finding(self) -> None:
        out = fst.to_findings(_three_failed_results(), tier="Starter Package", platform="lovable")
        actionable = [f for f in out["findings"] if not f.get("skipped")]
        self.assertEqual(len(actionable), 1)

    def test_scale_up_caps_at_three_actionable_findings(self) -> None:
        out = fst.to_findings(_three_failed_results(), tier="Scale Up Package", platform="lovable")
        actionable = [f for f in out["findings"] if not f.get("skipped")]
        self.assertEqual(len(actionable), 3)

    def test_pro_surfaces_all_actionable_findings(self) -> None:
        # Add a fourth so we can prove Pro doesn't get capped at 3.
        raw = _three_failed_results()
        raw.append({
            "form": {
                "id": "support",
                "name": "Get support",
                "selector": "#support",
                "fields": [{"type": "email", "name": "email", "id": "se"}],
            },
            "outcome": "no_response",
            "filled": {},
        })
        out = fst.to_findings(raw, tier="Pro Package", platform="lovable")
        actionable = [f for f in out["findings"] if not f.get("skipped")]
        self.assertEqual(len(actionable), 4)

    def test_passed_findings_increment_passed_check_ids(self) -> None:
        raw = [
            {"form": _newsletter_form(), "outcome": "ok", "filled": {}},
            {"form": _contact_form(), "outcome": "no_response", "filled": {}},
        ]
        out = fst.to_findings(raw, tier="Pro Package", platform="lovable")
        self.assertEqual(len(out["passed_check_ids"]), 1)
        self.assertTrue(out["passed_check_ids"][0].startswith("form_submit_smoke."))


# ---------------------------------------------------------------------------
# Case 3: Checkout / payment / destructive forms are SKIPPED
# ---------------------------------------------------------------------------


class SafetyGuardrailsCase(unittest.TestCase):
    def test_checkout_form_detected_as_skip(self) -> None:
        self.assertEqual(fst._skip_reason(_checkout_form()), "checkout_skipped")

    def test_destructive_form_detected_as_skip(self) -> None:
        self.assertEqual(fst._skip_reason(_delete_account_form()), "destructive_skipped")

    def test_clean_form_not_skipped(self) -> None:
        self.assertIsNone(fst._skip_reason(_newsletter_form()))

    def test_checkout_skip_surfaces_low_severity_finding(self) -> None:
        # Even at Starter (cap 1), the skip finding must surface so the
        # customer knows we saw the checkout form on purpose.
        raw = [
            {
                "form": _checkout_form(),
                "outcome": "checkout_skipped",
                "label": "Pay $19",
            },
        ]
        out = fst.to_findings(raw, tier="Starter Package", platform="lovable")
        skipped = [f for f in out["findings"] if f.get("skipped")]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["severity"], "low")
        self.assertEqual(
            skipped[0]["tag"], "Caught by The Stranger Who Tried to Sign Up"
        )
        self.assertIn("didn't submit", skipped[0]["what_we_saw"].lower())

    def test_destructive_skip_surfaces_low_severity_finding(self) -> None:
        raw = [
            {
                "form": _delete_account_form(),
                "outcome": "destructive_skipped",
                "label": "Delete my account",
            },
        ]
        out = fst.to_findings(raw, tier="Starter Package", platform="lovable")
        skipped = [f for f in out["findings"] if f.get("skipped")]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["severity"], "low")

    def test_skipped_findings_survive_tier_cap_even_with_competing_actionable(self) -> None:
        # Starter cap is 1 actionable. Add a no_response and a checkout
        # skip; both should land in the output (skipped findings never
        # get capped).
        raw = [
            {"form": _newsletter_form(), "outcome": "no_response", "filled": {}},
            {
                "form": _checkout_form(),
                "outcome": "checkout_skipped",
                "label": "Pay $19",
            },
        ]
        out = fst.to_findings(raw, tier="Starter Package", platform="lovable")
        self.assertEqual(len(out["findings"]), 2)
        skipped = [f for f in out["findings"] if f.get("skipped")]
        actionable = [f for f in out["findings"] if not f.get("skipped")]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(len(actionable), 1)

    def test_max_forms_per_audit_is_three(self) -> None:
        # This is a hard cap inside the async runner. The constant lives
        # at module scope so it can be asserted without firing Playwright.
        self.assertEqual(fst._MAX_FORMS_PER_AUDIT, 3)

    def test_blocked_selector_match_is_substring(self) -> None:
        # The customer-YAML opt-out should accept a selector substring.
        self.assertTrue(fst._is_blocked_selector("#prod-checkout", ["#prod-checkout"]))
        self.assertTrue(fst._is_blocked_selector("form#prod-checkout", ["#prod-checkout"]))
        self.assertFalse(fst._is_blocked_selector("#newsletter", ["#prod-checkout"]))
        self.assertFalse(fst._is_blocked_selector("#x", []))


# ---------------------------------------------------------------------------
# Case 4: disposable-mailbox round-trip only fires for Pro tier
# ---------------------------------------------------------------------------


class EmailRoundTripCase(unittest.TestCase):
    def setUp(self) -> None:
        self.calls: list[dict] = []

        def fake_roundtrip(*, raw_results, customer_email=None):
            self.calls.append(
                {"raw_results": raw_results, "customer_email": customer_email}
            )
            # Pretend nothing arrived so we surface a finding.
            return [{"form": _newsletter_form(), "arrived": False}]

        self.fake_roundtrip = fake_roundtrip

    def _stub_runner(self, *_args, **_kwargs):
        return [
            {"form": _newsletter_form(), "outcome": "ok", "filled": {}},
        ]

    def test_round_trip_is_skipped_for_starter_tier(self) -> None:
        orig = fst.run_form_smoke_test_raw
        fst.run_form_smoke_test_raw = self._stub_runner
        try:
            out = fst.run_form_smoke_test(
                base_url="https://example.test",
                tier="Starter Package",
                platform="lovable",
                email_roundtrip=self.fake_roundtrip,
            )
        finally:
            fst.run_form_smoke_test_raw = orig
        self.assertEqual(self.calls, [])
        self.assertTrue(out["ran"])

    def test_round_trip_is_skipped_for_scale_up_tier(self) -> None:
        orig = fst.run_form_smoke_test_raw
        fst.run_form_smoke_test_raw = self._stub_runner
        try:
            fst.run_form_smoke_test(
                base_url="https://example.test",
                tier="Scale Up Package",
                platform="lovable",
                email_roundtrip=self.fake_roundtrip,
            )
        finally:
            fst.run_form_smoke_test_raw = orig
        self.assertEqual(self.calls, [])

    def test_round_trip_fires_for_pro_tier(self) -> None:
        orig = fst.run_form_smoke_test_raw
        fst.run_form_smoke_test_raw = self._stub_runner
        try:
            out = fst.run_form_smoke_test(
                base_url="https://example.test",
                tier="Pro Package",
                platform="lovable",
                email_roundtrip=self.fake_roundtrip,
            )
        finally:
            fst.run_form_smoke_test_raw = orig
        self.assertEqual(len(self.calls), 1)
        # The Pro round-trip returning arrived=False must surface a
        # "no_confirmation_email" finding.
        titles = [f["title"] for f in out["findings"]]
        self.assertTrue(any("confirmation email" in t.lower() for t in titles))

    def test_opt_out_short_circuits_the_runner(self) -> None:
        out = fst.run_form_smoke_test(
            base_url="https://example.test",
            tier="Pro Package",
            platform="lovable",
            email_roundtrip=self.fake_roundtrip,
            enabled=False,
        )
        self.assertFalse(out["ran"])
        self.assertEqual(out["findings"], [])
        self.assertEqual(self.calls, [])
        self.assertEqual(out.get("skipped_reason"), "opt_out")

    def test_runner_falls_back_when_playwright_unavailable(self) -> None:
        orig = fst.run_form_smoke_test_raw
        fst.run_form_smoke_test_raw = lambda *a, **kw: None
        try:
            out = fst.run_form_smoke_test(
                base_url="https://example.test",
                tier="Pro Package",
                platform="lovable",
                email_roundtrip=self.fake_roundtrip,
            )
        finally:
            fst.run_form_smoke_test_raw = orig
        self.assertFalse(out["ran"])
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["passed_check_ids"], [])

    def test_email_capture_detection(self) -> None:
        self.assertTrue(fst._captures_email(_newsletter_form()))
        self.assertTrue(fst._captures_email(_contact_form()))
        self.assertFalse(fst._captures_email(_phone_form()))


# ---------------------------------------------------------------------------
# Stability case: persona tag stays canonical so the report can theme it
# ---------------------------------------------------------------------------


class PersonaTagCase(unittest.TestCase):
    def test_every_finding_carries_canonical_persona_tag(self) -> None:
        raw = [
            {"form": _newsletter_form(), "outcome": "no_response", "filled": {}},
            {"form": _checkout_form(), "outcome": "checkout_skipped", "label": "Pay"},
            {
                "form": _delete_account_form(),
                "outcome": "destructive_skipped",
                "label": "Delete",
            },
        ]
        out = fst.to_findings(raw, tier="Pro Package", platform="lovable")
        for f in out["findings"]:
            with self.subTest(title=f["title"]):
                self.assertEqual(
                    f["tag"], "Caught by The Stranger Who Tried to Sign Up"
                )
                self.assertEqual(f["category"], "form_submit_smoke")
                self.assertEqual(f["source"], "external")

    def test_category_id_constant_matches_yaml(self) -> None:
        # If a future worker renames CATEGORY_ID, the YAML must move too.
        self.assertEqual(fst.CATEGORY_ID, "form_submit_smoke")


# ---------------------------------------------------------------------------
# Fix-prompt library: prompts include the form name and stay buyer-friendly
# ---------------------------------------------------------------------------


class FixPromptCase(unittest.TestCase):
    def test_form_name_substituted_into_fix_prompt(self) -> None:
        prompt = fst._fix_prompt_for(
            "no_response",
            "lovable",
            form_name="newsletter signup form",
        )
        self.assertIn("newsletter signup form", prompt)

    def test_fix_prompt_falls_back_to_generic_when_platform_missing(self) -> None:
        # 'xyz' is not a known platform; we still get a non-empty prompt.
        prompt = fst._fix_prompt_for(
            "no_response", "xyz", form_name="newsletter signup form"
        )
        self.assertTrue(prompt)
        self.assertIn("newsletter signup form", prompt)


# ---------------------------------------------------------------------------
# Stdlib-only runner
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main(verbosity=2)
