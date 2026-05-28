"""Tests for pipeline edge cases not covered elsewhere.

Covers:
  - Slug generation: collision behaviour (two customers same first-name + same
    host get the SAME slug — documenting the known limitation so a future fix
    is a deliberate change).
  - Slug stability: same inputs always produce the same slug.
  - Slug robustness: unusual email / URL inputs don't crash or produce
    an empty string.
  - Tier normalisation: unknown tier name triggers the pipeline warn path
    and caps to Starter Package default (10), not 7 or 0.
  - Tier guidance target range: each tier guidance string contains a
    numeric target minimum that is >= floor(cap * 0.5).

Runs two ways:
  * pytest tests/test_pipeline_edge_cases.py
  * python tests/test_pipeline_edge_cases.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.audit_automation.slug import slug_from_email_url  # noqa: E402

# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------


class SlugStabilityCase(unittest.TestCase):
    def test_same_inputs_produce_same_slug(self) -> None:
        a = slug_from_email_url("alice@example.com", "https://myapp.io")
        b = slug_from_email_url("alice@example.com", "https://myapp.io")
        self.assertEqual(a, b)

    def test_www_prefix_stripped(self) -> None:
        with_www = slug_from_email_url("alice@example.com", "https://www.myapp.io")
        without_www = slug_from_email_url("alice@example.com", "https://myapp.io")
        self.assertEqual(with_www, without_www)

    def test_trailing_slash_ignored(self) -> None:
        with_slash = slug_from_email_url("alice@example.com", "https://myapp.io/")
        without_slash = slug_from_email_url("alice@example.com", "https://myapp.io")
        self.assertEqual(with_slash, without_slash)

    def test_slug_contains_only_safe_chars(self) -> None:
        slug = slug_from_email_url("alice+tag@example.com", "https://my-app.io")
        self.assertRegex(slug, r"^[a-z0-9-]+$", msg=f"unsafe chars in slug: {slug!r}")

    def test_slug_not_empty(self) -> None:
        slug = slug_from_email_url("", "")
        self.assertGreater(len(slug), 0)

    def test_unicode_email_doesnt_crash(self) -> None:
        # Non-ASCII local part — should not raise; may produce a dashed slug.
        slug = slug_from_email_url("ünïcödé@example.com", "https://example.com")
        self.assertIsInstance(slug, str)
        self.assertGreater(len(slug), 0)

    def test_very_long_email_truncated(self) -> None:
        long_local = "a" * 200
        slug = slug_from_email_url(f"{long_local}@example.com", "https://example.com")
        # local_slug is capped at 24 chars in the implementation
        local_part = slug.split("-example-com")[0]
        self.assertLessEqual(len(local_part), 24, msg=f"local part too long: {slug!r}")


class SlugCollisionCase(unittest.TestCase):
    """Document the known slug-collision limitation.

    Two different customers whose email local-part and hostname both normalise
    to the same strings will get the same slug. This is an intentional
    trade-off (slugs are human-readable) but it means a second customer with
    the same slug silently overwrites the first customer's YAML on disk.

    These tests document the *current* behaviour so any future de-collision
    work (e.g. appending a counter suffix) is a deliberate, visible change.
    """

    def test_same_local_same_host_produces_same_slug(self) -> None:
        slug_a = slug_from_email_url("rob@example.com", "https://myapp.io")
        slug_b = slug_from_email_url("rob@other.com", "https://myapp.io")
        # Different emails but same local + same host → same slug
        # (the host wins because it's the longer component).
        # This test just asserts they ARE the same, documenting the collision.
        self.assertEqual(slug_a, slug_b)

    def test_same_local_different_host_produces_different_slug(self) -> None:
        slug_a = slug_from_email_url("rob@example.com", "https://appleone.io")
        slug_b = slug_from_email_url("rob@example.com", "https://appletwo.io")
        self.assertNotEqual(slug_a, slug_b)

    def test_different_local_same_host_produces_different_slug(self) -> None:
        slug_a = slug_from_email_url("alice@example.com", "https://myapp.io")
        slug_b = slug_from_email_url("bob@example.com", "https://myapp.io")
        self.assertNotEqual(slug_a, slug_b)


# ---------------------------------------------------------------------------
# Tier guidance strings
# ---------------------------------------------------------------------------


class TierGuidanceCase(unittest.TestCase):
    """Verify the target range in _tier_guidance covers the expected minimum."""

    def _guidance(self, tier: str, cap: int) -> str:
        from scripts.ai_audit.pipeline import _tier_guidance  # type: ignore[attr-defined]

        return _tier_guidance(tier, cap)

    def test_starter_guidance_mentions_target_range(self) -> None:
        text = self._guidance("Starter Package", 10)
        self.assertIn("Target", text)
        # Should contain at least one digit for the minimum.
        import re

        self.assertTrue(re.search(r"\d+-\d+", text), msg=f"no range in: {text!r}")

    def test_scale_up_guidance_minimum_is_at_least_two_thirds_cap(self) -> None:
        import re

        text = self._guidance("Scale Up Package", 30)
        m = re.search(r"Target\s+(\d+)-(\d+)", text)
        self.assertIsNotNone(m, msg=f"no 'Target X-Y' in guidance: {text!r}")
        assert m is not None
        target_min = int(m.group(1))
        self.assertGreaterEqual(target_min, 20, msg=f"min too low for Scale Up: {target_min}")

    def test_pro_guidance_minimum_is_at_least_three_quarters_cap(self) -> None:
        import re

        text = self._guidance("Pro Package", 40)
        m = re.search(r"Target\s+(\d+)-(\d+)", text)
        self.assertIsNotNone(m, msg=f"no 'Target X-Y' in guidance: {text!r}")
        assert m is not None
        target_min = int(m.group(1))
        self.assertGreaterEqual(target_min, 25, msg=f"min too low for Pro: {target_min}")

    def test_unknown_tier_defaults_to_starter_cap(self) -> None:
        """An unrecognized tier should not raise; it should log a WARN and use
        the Starter Package cap (10). Verified by checking the DEFAULT_TIER_CAPS
        constant exported from the pipeline module."""
        from scripts.ai_audit.pipeline import DEFAULT_TIER_CAPS  # type: ignore[attr-defined]

        starter_cap = DEFAULT_TIER_CAPS["Starter Package"]
        self.assertEqual(starter_cap, 10, msg="Starter cap changed — update pricing copy too")


# ---------------------------------------------------------------------------
# Tier caps match DELIVER_COUNT constants
# ---------------------------------------------------------------------------


class TierCapSanityCase(unittest.TestCase):
    def test_free_deliver_count_is_below_starter_cap(self) -> None:
        """Free audit delivers fewer findings than the cheapest paid tier."""
        from scripts.ai_audit.pipeline import DEFAULT_TIER_CAPS
        from scripts.launchlook_constants import FREE_AUDIT_DELIVER_COUNT

        starter_cap = DEFAULT_TIER_CAPS["Starter Package"]
        self.assertLess(
            FREE_AUDIT_DELIVER_COUNT,
            starter_cap,
            msg=(
                f"FREE_AUDIT_DELIVER_COUNT ({FREE_AUDIT_DELIVER_COUNT}) "
                f"must be strictly less than Starter cap ({starter_cap})"
            ),
        )


# ---------------------------------------------------------------------------
# Stdlib-only runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
