"""Tests for ``scripts/sanitize_for_public.py``.

Covers the four privacy guarantees the q22 spec carries:

1. Customer URL never appears on the public surface.
2. Customer email never appears on the public surface.
3. Screenshot paths and captions never appear on the public surface.
4. Internal CRM keys (notion_row_id, internal_notes, fingerprint) never
   appear on the public surface.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.sanitize_for_public import (  # noqa: E402
    PUBLIC_CUSTOMER_KEYS,
    PUBLIC_FINDING_KEYS,
    sanitize_customer,
    sanitize_finding,
    sanitize_report_json,
    sanitize_verdict,
)

# ---------------------------------------------------------------------------
# sanitize_finding
# ---------------------------------------------------------------------------


def test_sanitize_finding_strips_customer_url() -> None:
    finding = {
        "title": "Dev Bypass button signs visitors in",
        "severity": "critical",
        "what_we_saw": (
            "On https://sparkle.lovable.app/auth, the Dev Bypass button is " "visible."
        ),
        "why_it_matters": (
            "Anyone with the URL sparkle.lovable.app can skip authentication."
        ),
        "fix_prompt": "Remove the button from /auth on sparkle.lovable.app.",
    }
    clean = sanitize_finding(finding, "https://sparkle.lovable.app")

    blob = " ".join(str(v) for v in clean.values())
    assert "sparkle.lovable.app" not in blob
    assert "lovable.app" not in blob
    assert "/auth" not in blob
    # URL-with-path collapses to "your site"; a free-standing /auth on its own
    # gets translated to a plain-English phrase.
    assert "your site" in clean["what_we_saw"]
    assert "the sign-in page" in clean["fix_prompt"]


def test_sanitize_finding_strips_screenshot_fields() -> None:
    finding = {
        "title": "Missing privacy page",
        "severity": "high",
        "screenshot_path": "screenshots/jane-sparkle-marketplace/footer.png",
        "screenshot_caption": "Footer with broken Privacy and Terms links.",
        "what_we_saw": "/privacy returns a 404.",
    }
    clean = sanitize_finding(finding, "https://sparkle.lovable.app")

    assert "screenshot_path" not in clean
    assert "screenshot_caption" not in clean
    assert "the privacy page" in clean["what_we_saw"]


def test_sanitize_finding_strips_internal_keys() -> None:
    finding = {
        "title": "Quick Book modal dead-ends",
        "severity": "high",
        "fingerprint": "abc123",
        "notion_row_id": "row-9",
        "internal_notes": "we should follow up on this in 2 weeks",
        "what_we_saw": "The Quick Book CTA opens a modal with no slots.",
    }
    clean = sanitize_finding(finding, "https://sparkle.lovable.app")
    for forbidden in ("fingerprint", "notion_row_id", "internal_notes"):
        assert forbidden not in clean


def test_sanitize_finding_strips_emails() -> None:
    finding = {
        "title": "Contact email leak",
        "severity": "low",
        "what_we_saw": "Contact email jane-sparkle@email.com appears on the page.",
    }
    clean = sanitize_finding(finding, "https://sparkle.lovable.app")
    assert "jane-sparkle@email.com" not in clean["what_we_saw"]
    assert "[email redacted]" in clean["what_we_saw"]


def test_sanitize_finding_handles_missing_customer_url() -> None:
    finding = {
        "title": "Trust gap",
        "severity": "medium",
        "what_we_saw": "Footer link is broken.",
    }
    clean = sanitize_finding(finding, "")
    assert clean["what_we_saw"] == "Footer link is broken."


def test_sanitize_finding_returns_empty_dict_for_non_dict() -> None:
    assert sanitize_finding("not a dict", "https://example.com") == {}  # type: ignore[arg-type]
    assert sanitize_finding(None, "https://example.com") == {}  # type: ignore[arg-type]


def test_sanitize_finding_keeps_only_public_keys() -> None:
    finding = {key: "value" for key in PUBLIC_FINDING_KEYS}
    finding["secret"] = "leak me"
    finding["category"] = "broken_ctas"
    clean = sanitize_finding(finding, "")
    assert set(clean.keys()) <= PUBLIC_FINDING_KEYS
    assert "secret" not in clean


# ---------------------------------------------------------------------------
# sanitize_customer
# ---------------------------------------------------------------------------


def test_sanitize_customer_strips_email_url_notion() -> None:
    customer = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane-sparkle@email.com",
        "notion_row_id": "row-42",
        "app_name": "Sparkle Marketplace",
        "app_url": "https://sparkle.lovable.app",
        "url_redacted": False,
        "tier": "Starter Package",
        "builder": "Lovable",
        "internal_notes": "follow up Friday",
    }
    clean = sanitize_customer(customer)
    assert clean == {
        "first_name": "Jane",
        "app_name": "Sparkle Marketplace",
        "tier": "Starter Package",
        "builder": "Lovable",
    }
    blob = " ".join(str(v) for v in clean.values())
    assert "jane-sparkle@email.com" not in blob
    assert "sparkle.lovable.app" not in blob
    assert "row-42" not in blob


def test_sanitize_customer_allowlist_is_exhaustive() -> None:
    assert PUBLIC_CUSTOMER_KEYS == {
        "first_name",
        "app_name",
        "tier",
        "builder",
        "platform",
    }


# ---------------------------------------------------------------------------
# sanitize_verdict
# ---------------------------------------------------------------------------


def test_sanitize_verdict_keeps_label_and_summary() -> None:
    verdict = {
        "label": "Needs fixes before launch",
        "emoji": "🟡",
        "summary": "Two blockers on sparkle.lovable.app.",
        "narrative": "We saw the dev bypass at /auth.",
        "internal_notes": "manual override applied",
    }
    clean = sanitize_verdict(verdict, "https://sparkle.lovable.app")
    assert clean["label"] == "Needs fixes before launch"
    assert "sparkle.lovable.app" not in clean["summary"]
    assert "/auth" not in clean["narrative"]
    assert "internal_notes" not in clean


# ---------------------------------------------------------------------------
# sanitize_report_json
# ---------------------------------------------------------------------------


def _example_report() -> dict:
    return {
        "customer_slug": "jane-sparkle-marketplace",
        "is_public": False,
        "tier": "Starter Package",
        "audit_date": "2026-05-26",
        "app_name": "Sparkle Marketplace",
        "customer_url": "https://sparkle.lovable.app",
        "verdict": {
            "label": "Needs fixes before launch",
            "summary": "Two dev-only blockers on sparkle.lovable.app.",
        },
        "passed_checks": ["mobile layout issues", "obvious visible risks"],
        "findings": [
            {
                "title": "Dev Bypass button signs visitors in",
                "severity": "critical",
                "category": "broken_ctas",
                "tag": "Caught by The Klutz",
                "what_we_saw": "On https://sparkle.lovable.app/auth the button is visible.",
                "why_it_matters": "Anyone with the URL skips authentication.",
                "fix_prompt": "Remove the button from /auth on sparkle.lovable.app.",
                "screenshot_path": "screenshots/jane-sparkle/auth.png",
                "fingerprint": "abc123",
            }
        ],
        "share_metadata": {
            "title": "LaunchLook audit for Sparkle Marketplace",
            "description": "Pre-launch audit. Verdict: Needs fixes before launch.",
            "og_image": "https://launchlook.app/images/og.png",
        },
    }


def _example_customer() -> dict:
    return {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane-sparkle@email.com",
        "notion_row_id": "row-42",
        "app_name": "Sparkle Marketplace",
        "app_url": "https://sparkle.lovable.app",
        "url_redacted": False,
        "tier": "Starter Package",
        "builder": "Lovable",
    }


def test_sanitize_report_json_default_is_private_safe() -> None:
    out = sanitize_report_json(_example_report(), _example_customer())

    blob = repr(out)
    # No customer URL, email, or screenshot path anywhere
    assert "sparkle.lovable.app" not in blob
    assert "jane-sparkle@email.com" not in blob
    assert "screenshot" not in blob
    assert "notion_row_id" not in blob
    assert "fingerprint" not in blob


def test_sanitize_report_json_keeps_public_safe_metadata() -> None:
    out = sanitize_report_json(_example_report(), _example_customer())
    assert out["customer_slug"] == "jane-sparkle-marketplace"
    assert out["is_public"] is False
    assert out["tier"] == "Starter Package"
    assert out["app_name"] == "Sparkle Marketplace"
    assert out["customer"]["first_name"] == "Jane"
    assert "email" not in out["customer"]
    assert "app_url" not in out["customer"]
    assert out["share_metadata"]["title"] == "LaunchLook audit for Sparkle Marketplace"


def test_sanitize_report_json_findings_are_scrubbed() -> None:
    out = sanitize_report_json(_example_report(), _example_customer())
    assert len(out["findings"]) == 1
    f = out["findings"][0]
    assert f["title"] == "Dev Bypass button signs visitors in"
    assert f["severity"] == "critical"
    assert f["tag"] == "Caught by The Klutz"
    assert "sparkle.lovable.app" not in f["what_we_saw"]
    assert "sparkle.lovable.app" not in f["fix_prompt"]
    assert "/auth" not in f["what_we_saw"]
    assert "the sign-in page" in f["fix_prompt"]
    assert "screenshot_path" not in f
    assert "fingerprint" not in f


def test_sanitize_report_json_is_idempotent() -> None:
    out_a = sanitize_report_json(_example_report(), _example_customer())
    # Pretend we then re-published the same sanitized JSON with no customer.
    out_b = sanitize_report_json(out_a, out_a.get("customer", {}))
    assert out_a["findings"] == out_b["findings"]
    assert out_a["customer"] == out_b["customer"]


def test_sanitize_report_json_handles_missing_findings() -> None:
    out = sanitize_report_json(
        {
            "customer_slug": "foo",
            "is_public": True,
            "verdict": {"summary": "All clear"},
        },
        {"first_name": "Foo", "app_name": "Bar"},
    )
    assert out["findings"] == []
    assert out["passed_checks"] == []
    assert out["is_public"] is True


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://sparkle.lovable.app/auth", "your site"),
        ("http://sparkle.lovable.app", "your site"),
        ("sparkle.lovable.app", "your site"),
    ],
)
def test_url_variations_all_get_stripped(raw: str, expected: str) -> None:
    finding = {
        "title": "Test",
        "severity": "low",
        "what_we_saw": f"Visit {raw} to see it.",
    }
    clean = sanitize_finding(finding, "https://sparkle.lovable.app")
    assert "sparkle.lovable.app" not in clean["what_we_saw"]
    assert expected in clean["what_we_saw"]
