"""Tests for q17 LaunchLook Verified badge infrastructure.

Covers the verification steps in the task spec:

* Badge image generation produces SVG with the customer slug + verified
  date stamp + tier display name.
* ``verify.json`` checksum is deterministic given the same inputs (two
  runs with the same slug / tier / date produce the same hash).
* ``/api/verify`` behaviour:
    - Valid badge -> 200 + ``valid: true``
    - Expired badge -> 200 + ``valid: false`` + ``expired_on``
    - Unknown slug -> 404
    - Rate limit -> 429 after 10 requests in the rolling 60s window
* Re-verification flow: ``--re-verify`` against an existing
  verify.json refreshes ``verified_at`` and bumps ``expires_at``;
  ``--re-verify`` against a missing record exits non-zero so the
  ``$9`` SKU cannot mint a badge for a customer who never had one.

Plus a guardrail case: ``landing/verify-scope.html`` must not contain
over-promising language (the ``rg`` step from the task spec).

Runs two ways (mirrors tests/test_form_smoke_test.py):

* ``pytest tests/test_verified_badge.py``
* ``python tests/test_verified_badge.py`` (stdlib-only)
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import time
import unittest
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import the badge generator + verify API as plain modules so the tests
# do not need an HTTP layer or Vercel runtime.
from scripts import generate_verified_badge as badge_gen  # noqa: E402

# `api/verify.py` is not a regular package (the directory has no
# __init__.py). Load it via importlib so the tests stay drop-in.
import importlib.util  # noqa: E402

_VERIFY_PATH = REPO_ROOT / "api" / "verify.py"
_spec = importlib.util.spec_from_file_location("verify_api", _VERIFY_PATH)
verify_api = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(verify_api)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _example_yaml() -> dict:
    return {
        "customer": {
            "first_name": "Jane",
            "app_name": "Sparkle",
            "tier": "Scale Up Package",
            "email": "jane@example.com",
            "app_url": "https://sparkle.example.com",
            "builder": "Webflow",
        },
    }


def _make_ctx(
    verified_at: date | None = None,
    tier: str = "Scale Up Package",
) -> badge_gen.BadgeContext:
    data = _example_yaml()
    data["customer"]["tier"] = tier
    verified = verified_at or date(2026, 5, 26)
    return badge_gen.build_context_from_yaml(
        data, verified_at=verified, domain="launchlook.app"
    )


# ---------------------------------------------------------------------------
# Badge generation
# ---------------------------------------------------------------------------


class TestBadgeGeneration(unittest.TestCase):
    def test_svg_contains_slug_and_verified_date(self) -> None:
        ctx = _make_ctx()
        svg = badge_gen.render_svg(ctx, "light")
        self.assertIn("LaunchLook Verified", svg)
        self.assertIn("Scale Up Package", svg)
        # "May 2026" is what _make_ctx produces; mirrors what the badge
        # surfaces to readers.
        self.assertIn("May 2026", svg)
        # SVG aria label references the slug so screen readers + the
        # verify page can both find it.
        self.assertIn("jane-sparkle", svg)

    def test_dark_variant_uses_dark_palette(self) -> None:
        ctx = _make_ctx()
        light = badge_gen.render_svg(ctx, "light")
        dark = badge_gen.render_svg(ctx, "dark")
        self.assertNotEqual(light, dark)
        # The light card uses ink #1F1B16 on cream #FAF7F2; the dark
        # card flips both. Spot-check the swatches are present.
        self.assertIn("#FAF7F2", light)
        self.assertIn("#1F1B16", light)
        self.assertIn("#1F1B16", dark)
        self.assertIn("#FAF7F2", dark)

    def test_tier_validity_windows(self) -> None:
        cases = [
            ("Starter Package", 30),
            ("Scale Up Package", 90),
            ("Full Package", 90),  # legacy alias resolves to Scale Up
            ("Pro Package", 180),
        ]
        verified = date(2026, 5, 26)
        for tier, days in cases:
            with self.subTest(tier=tier):
                ctx = _make_ctx(verified_at=verified, tier=tier)
                self.assertEqual(
                    (ctx.expires_at - ctx.verified_at).days, days,
                    f"{tier} should expire {days} days from {verified}",
                )

    def test_unknown_tier_exits(self) -> None:
        with self.assertRaises(SystemExit):
            badge_gen.normalize_tier("Enterprise Premium")


# ---------------------------------------------------------------------------
# verify.json checksum determinism
# ---------------------------------------------------------------------------


class TestVerifyJsonChecksum(unittest.TestCase):
    def test_checksum_is_deterministic_for_same_inputs(self) -> None:
        ctx_a = _make_ctx()
        ctx_b = _make_ctx()
        record_a = badge_gen.build_verify_record(ctx_a)
        record_b = badge_gen.build_verify_record(ctx_b)
        self.assertEqual(record_a["checksum"], record_b["checksum"])
        self.assertTrue(record_a["checksum"].startswith("sha256:"))

    def test_checksum_changes_when_verified_at_changes(self) -> None:
        ctx_today = _make_ctx(verified_at=date(2026, 5, 26))
        ctx_tomorrow = _make_ctx(verified_at=date(2026, 5, 27))
        sum_today = badge_gen.build_verify_record(ctx_today)["checksum"]
        sum_tomorrow = badge_gen.build_verify_record(ctx_tomorrow)["checksum"]
        self.assertNotEqual(sum_today, sum_tomorrow)

    def test_previous_verified_at_does_not_affect_checksum(self) -> None:
        # Re-verify records carry previous_verified_at for transparency
        # but the checksum stays anchored to the audit content + dates.
        ctx = _make_ctx()
        fresh = badge_gen.build_verify_record(ctx)
        reverified = badge_gen.build_verify_record(
            ctx, previous_verified_at="2026-02-26"
        )
        self.assertEqual(fresh["checksum"], reverified["checksum"])
        self.assertEqual(reverified["previous_verified_at"], "2026-02-26")


# ---------------------------------------------------------------------------
# /api/verify behaviour
# ---------------------------------------------------------------------------


class TestVerifyApi(unittest.TestCase):
    def setUp(self) -> None:
        # Each test gets a fresh tmp verify_root so writes don't bleed
        # into the real repo.
        self._tmpdir = tempfile.TemporaryDirectory()
        self.verify_root = Path(self._tmpdir.name)
        verify_api._reset_rate_state_for_tests()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        verify_api._reset_rate_state_for_tests()

    def _seed(self, slug: str, *, verified_at: date, expires_at: date,
              tier: str = "Scale Up Package") -> None:
        record = {
            "customer_slug": slug,
            "verified_at": verified_at.isoformat(),
            "tier": tier,
            "expires_at": expires_at.isoformat(),
            "issued_by": "LaunchLook",
            "customer_url": f"https://{slug}.example.com",
            "checksum": "sha256:test",
        }
        path = self.verify_root / f"{slug}.json"
        path.write_text(json.dumps(record), encoding="utf-8")

    def test_valid_badge_returns_200_and_valid_true(self) -> None:
        self._seed("jane-sparkle",
                   verified_at=date(2026, 5, 26),
                   expires_at=date(2026, 8, 24))
        status, body = verify_api.handle_verify(
            "jane-sparkle", ip="1.1.1.1",
            verify_root=self.verify_root,
            today=date(2026, 6, 15),
            enforce_rate_limit=False,
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["valid"])
        self.assertEqual(body["customer_slug"], "jane-sparkle")
        self.assertEqual(body["tier"], "Scale Up Package")
        self.assertEqual(body["expires_at"], "2026-08-24")
        self.assertEqual(body["customer_url"], "https://jane-sparkle.example.com")

    def test_expired_badge_returns_200_and_valid_false(self) -> None:
        self._seed("expired-co",
                   verified_at=date(2026, 1, 1),
                   expires_at=date(2026, 4, 1))
        status, body = verify_api.handle_verify(
            "expired-co", ip="1.1.1.1",
            verify_root=self.verify_root,
            today=date(2026, 5, 1),
            enforce_rate_limit=False,
        )
        self.assertEqual(status, 200)
        self.assertFalse(body["valid"])
        self.assertEqual(body["reason"], "expired")
        self.assertEqual(body["expired_on"], "2026-04-01")
        self.assertIn("re-verification", body.get("reverify_cta", "").lower())

    def test_unknown_slug_returns_404(self) -> None:
        status, body = verify_api.handle_verify(
            "never-existed", ip="1.1.1.1",
            verify_root=self.verify_root,
            enforce_rate_limit=False,
        )
        self.assertEqual(status, 404)
        self.assertFalse(body["valid"])
        self.assertEqual(body["reason"], "unknown_slug")
        self.assertEqual(body["customer_slug"], "never-existed")
        self.assertIn("hello@launchlook.app", body.get("hint", ""))

    def test_missing_slug_returns_400(self) -> None:
        status, body = verify_api.handle_verify(
            "", ip="1.1.1.1", verify_root=self.verify_root,
            enforce_rate_limit=False,
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "missing_slug")

    def test_invalid_slug_format_returns_400(self) -> None:
        status, body = verify_api.handle_verify(
            "../etc/passwd", ip="1.1.1.1",
            verify_root=self.verify_root,
            enforce_rate_limit=False,
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "missing_slug")

    def test_rate_limit_after_10_requests_per_minute(self) -> None:
        self._seed("rl-target",
                   verified_at=date(2026, 5, 26),
                   expires_at=date(2026, 8, 24))
        ip = "9.9.9.9"
        for _ in range(verify_api.RATE_LIMIT_PER_MINUTE):
            status, _ = verify_api.handle_verify(
                "rl-target", ip=ip,
                verify_root=self.verify_root,
                today=date(2026, 6, 1),
            )
            self.assertEqual(status, 200)

        status, body = verify_api.handle_verify(
            "rl-target", ip=ip,
            verify_root=self.verify_root,
            today=date(2026, 6, 1),
        )
        self.assertEqual(status, 429)
        self.assertEqual(body["error"], "rate_limited")
        self.assertGreater(body["retry_after_seconds"], 0)

    def test_rate_limit_window_slides(self) -> None:
        # Fake a fresh bucket then prove a request 61s later is allowed.
        ip = "5.5.5.5"
        start = time.monotonic()
        for _ in range(verify_api.RATE_LIMIT_PER_MINUTE):
            verify_api.is_rate_limited(ip, now=start)
        limited, _ = verify_api.is_rate_limited(ip, now=start)
        self.assertTrue(limited)
        limited_later, _ = verify_api.is_rate_limited(ip, now=start + 61)
        self.assertFalse(limited_later)


# ---------------------------------------------------------------------------
# Re-verification flow
# ---------------------------------------------------------------------------


class TestReVerification(unittest.TestCase):
    def test_fresh_run_writes_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_root = Path(tmp) / "badges"
            verify_root = Path(tmp) / "verified"
            ctx = _make_ctx(verified_at=date(2026, 5, 26))
            written = badge_gen.write_badge_assets(
                ctx,
                out_root=out_root,
                verify_root=verify_root,
                skip_png=True,
            )
            self.assertIn("light_svg", written)
            self.assertIn("dark_svg", written)
            self.assertIn("verify_json", written)
            self.assertTrue(written["verify_json"].exists())
            record = json.loads(written["verify_json"].read_text())
            self.assertEqual(record["customer_slug"], "jane-sparkle")
            self.assertEqual(record["tier"], "Scale Up Package")
            self.assertEqual(record["verified_at"], "2026-05-26")
            self.assertEqual(record["expires_at"], "2026-08-24")

    def test_reverify_refreshes_dates_and_carries_previous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_root = Path(tmp) / "badges"
            verify_root = Path(tmp) / "verified"

            # 1) Original badge stamped February 2026.
            ctx_orig = _make_ctx(verified_at=date(2026, 2, 26))
            badge_gen.write_badge_assets(
                ctx_orig,
                out_root=out_root,
                verify_root=verify_root,
                skip_png=True,
            )

            # 2) Re-verify in May 2026; expect a new expires_at.
            ctx_new = _make_ctx(verified_at=date(2026, 5, 26))
            written = badge_gen.write_badge_assets(
                ctx_new,
                out_root=out_root,
                verify_root=verify_root,
                previous_verified_at="2026-02-26",
                skip_png=True,
            )
            record = json.loads(written["verify_json"].read_text())
            self.assertEqual(record["verified_at"], "2026-05-26")
            self.assertEqual(record["expires_at"], "2026-08-24")
            self.assertEqual(record["previous_verified_at"], "2026-02-26")

    def test_reverify_main_fails_without_prior(self) -> None:
        # Drive the CLI entrypoint with --re-verify and assert it
        # SystemExits because no prior verify.json exists in the tmp
        # verify_root.
        with tempfile.TemporaryDirectory() as tmp:
            verify_root = Path(tmp) / "verified"
            badge_root = Path(tmp) / "badges"
            verify_root.mkdir(parents=True, exist_ok=True)

            # Build a YAML on disk so the CLI can load it.
            import yaml

            yaml_path = Path(tmp) / "customer.yaml"
            yaml_path.write_text(yaml.safe_dump(_example_yaml()), encoding="utf-8")

            # Monkey-patch the output roots so we don't pollute the
            # real landing/ directory if the CLI ever gets past the
            # guard (it should not, but defence in depth).
            original_badge = badge_gen.BADGE_OUTPUT_ROOT
            original_verify = badge_gen.VERIFY_DATA_ROOT
            badge_gen.BADGE_OUTPUT_ROOT = badge_root
            badge_gen.VERIFY_DATA_ROOT = verify_root
            try:
                with self.assertRaises(SystemExit) as cm:
                    badge_gen.main([
                        "--customer", str(yaml_path),
                        "--re-verify",
                        "--skip-png",
                    ])
                self.assertIn("re-verify", str(cm.exception))
            finally:
                badge_gen.BADGE_OUTPUT_ROOT = original_badge
                badge_gen.VERIFY_DATA_ROOT = original_verify


# ---------------------------------------------------------------------------
# Honest scope language guardrail
# ---------------------------------------------------------------------------


class TestScopePageLanguage(unittest.TestCase):
    """Mirrors the spec's grep step:

        rg "certified|certification|guarantee|guaranteed" landing/verify-scope.html

    should return zero matches.
    """

    def test_no_over_promising_words(self) -> None:
        path = REPO_ROOT / "landing" / "verify-scope.html"
        text = path.read_text(encoding="utf-8")
        forbidden = re.compile(
            r"\b(certified|certification|guarantee|guaranteed)\b",
            re.IGNORECASE,
        )
        matches = forbidden.findall(text)
        self.assertEqual(
            matches, [],
            f"verify-scope.html still references {matches!r}; "
            "per SIMPLICITY-GUARDRAILS section 3 the scope page must not "
            "over-promise.",
        )


if __name__ == "__main__":
    unittest.main()
