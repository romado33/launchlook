"""Tests for URL-only lite checks (console, broken links, trust SEO, SSL)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts.ai_audit.broken_links_lite import (  # noqa: E402
    _build_finding,
    _collect_candidates,
    run_broken_links_lite,
)
from scripts.ai_audit.console_errors_lite import (  # noqa: E402
    _build_finding as console_build,
    _humanize_error_line,
    _is_noise,
)
from scripts.ai_audit.security_lite import (  # noqa: E402
    _check_referrer_policy,
    _check_ssl_expiry,
)
from scripts.ai_audit.trust_seo_lite import (  # noqa: E402
    _check_meta_description,
    _check_viewport,
    run_trust_seo_lite,
)


class TestConsoleHelpers(unittest.TestCase):
    def test_noise_filters_favicon(self):
        self.assertTrue(_is_noise("Failed to load favicon.ico"))

    def test_humanize_strips_error_prefix(self):
        self.assertIn("cannot read", _humanize_error_line("TypeError: cannot read property 'x'"))

    def test_build_finding_plain_english(self):
        hits = [{"path": "/", "url": "https://app.test/", "errors": ["TypeError: broken thing"]}]
        f = console_build(hits)
        self.assertIsNotNone(f)
        assert f is not None
        self.assertIn("Background errors", f["title"])
        self.assertNotIn("FL-015", f["title"])


class TestBrokenLinks(unittest.TestCase):
    def test_collect_internal_only(self):
        pages = [
            {
                "path": "/",
                "status": 200,
                "links": [
                    {"text": "Pricing", "href": "/pricing"},
                    {"text": "External", "href": "https://other.com/x"},
                ],
            }
        ]
        cands = _collect_candidates(pages, "https://app.test")
        self.assertEqual(len(cands), 1)
        self.assertEqual(cands[0]["href"], "/pricing")

    def test_build_finding_lists_dead_links(self):
        broken = [{"text": "Pricing", "href": "/pricing", "url": "https://app.test/pricing", "status": 404}]
        f = _build_finding(broken)
        self.assertIsNotNone(f)
        assert f is not None
        self.assertIn("missing page", f["title"].lower())


class TestTrustSeo(unittest.TestCase):
    def test_viewport_missing(self):
        home = {"path": "/", "status": 200, "meta": {}}
        f = _check_viewport(home)
        self.assertIsNotNone(f)
        assert f is not None
        self.assertIn("phone", f["title"].lower())

    def test_description_short(self):
        home = {"path": "/", "status": 200, "meta": {"description": "Hi"}}
        f = _check_meta_description(home)
        self.assertIsNotNone(f)

    def test_run_caps_at_two(self):
        pages = [{"path": "/", "status": 200, "meta": {}}]
        out = run_trust_seo_lite(base_url="https://app.test", pages=pages)
        self.assertLessEqual(len(out["findings"]), 2)


class TestSecurityExtras(unittest.TestCase):
    def test_referrer_missing(self):
        f = _check_referrer_policy({})
        self.assertIsNotNone(f)
        self.assertEqual(f["severity"], "low")

    def test_referrer_present_passes(self):
        self.assertIsNone(_check_referrer_policy({"referrer-policy": "strict-origin"}))

    def test_ssl_expiry_more_than_30_days_passes(self):
        """Sites with valid distant expiry should not generate a finding."""
        # example.com typically has a valid cert; if unreachable test still passes
        f = _check_ssl_expiry("https://example.com")
        # None = pass (either healthy cert or check skipped on network error)
        self.assertIsNone(f)


class TestBrokenLinksRunner(unittest.TestCase):
    @patch("scripts.ai_audit.broken_links_lite._probe_url", return_value=404)
    def test_runner_finds_404(self, _mock_probe):
        pages = [
            {
                "path": "/",
                "status": 200,
                "links": [{"text": "Pricing", "href": "/pricing"}],
            }
        ]
        out = run_broken_links_lite(base_url="https://app.test", pages=pages)
        self.assertEqual(len(out["findings"]), 1)


if __name__ == "__main__":
    unittest.main()
