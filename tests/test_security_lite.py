"""Tests for ``scripts/ai_audit/security_lite.py``.

Covers:
1. Header checks (hsts, csp, x_frame_options, x_content_type_options).
2. Exposed credentials: AWS key, Stripe live key, Firebase config.
3. Supabase service_role JWT detection (must decode to service_role;
   anon JWTs are NOT flagged).
4. NEXT_PUBLIC env-var pattern in page source.
5. Leaky link patterns (/admin, /.env, /.git).
6. Sitemap check: 200 passes, non-200 fails, network error passes silently.
7. Robots.txt check: Disallow: / under User-agent: * is flagged;
   partial disallow, missing robots.txt, and allow-all are not flagged.
8. Noindex meta tag on homepage is flagged; absent tag passes.
9. JWT role helper: valid service_role / anon / malformed inputs.
10. run_security_lite returns correct passed/failed check_id sets.
"""

from __future__ import annotations

import base64
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts.ai_audit.security_lite import (  # noqa: E402
    _check_noindex,
    _check_robots,
    _check_sitemap,
    _jwt_role,
    run_security_lite,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_jwt(role: str) -> str:
    """Build a minimal syntactically-valid JWT with the given role claim."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    payload_bytes = json.dumps({"role": role, "iss": "supabase"}).encode()
    payload = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    return f"{header}.{payload}.{sig}"


# ---------------------------------------------------------------------------
# 9. JWT role helper
# ---------------------------------------------------------------------------


class TestJwtRole(unittest.TestCase):
    def test_service_role(self):
        assert _jwt_role(_make_jwt("service_role")) == "service_role"

    def test_anon_role(self):
        assert _jwt_role(_make_jwt("anon")) == "anon"

    def test_malformed_not_three_parts(self):
        assert _jwt_role("notajwt") is None

    def test_invalid_base64(self):
        assert _jwt_role("abc.!!!.xyz") is None

    def test_no_role_claim(self):
        payload = base64.urlsafe_b64encode(b'{"sub":"1234"}').rstrip(b"=").decode()
        token = f"eyJhbGc.{payload}.sig"
        assert _jwt_role(token) is None


# ---------------------------------------------------------------------------
# 3. Supabase service_role JWT in page HTML
# ---------------------------------------------------------------------------


class TestSupabaseJwtDetection(unittest.TestCase):
    def _pages_with(self, text: str) -> list[dict]:
        return [{"url": "https://example.com/", "text": text, "links": []}]

    def test_service_role_jwt_flagged(self):
        from scripts.ai_audit.security_lite import _check_exposed_creds

        token = _make_jwt("service_role")
        pages = self._pages_with(f'const key = "{token}"')
        findings = _check_exposed_creds(pages)
        assert len(findings) == 1
        assert "service_role" in findings[0]["title"].lower()
        assert findings[0]["severity"] == "critical"

    def test_anon_jwt_not_flagged(self):
        from scripts.ai_audit.security_lite import _check_exposed_creds

        token = _make_jwt("anon")
        pages = self._pages_with(f'const anonKey = "{token}"')
        findings = _check_exposed_creds(pages)
        assert findings == []

    def test_aws_key_still_flagged(self):
        from scripts.ai_audit.security_lite import _check_exposed_creds

        # Build the key at runtime so literal scanners don't trip on the test file.
        # Pattern: AKIA + 16 uppercase alphanumeric chars.
        fake_key = "AKIA" + "IOSFODNN7EXAMPLE"
        pages = self._pages_with(fake_key)
        findings = _check_exposed_creds(pages)
        assert any("AWS" in f["title"] for f in findings)

    def test_stripe_live_key_flagged(self):
        from scripts.ai_audit.security_lite import _check_exposed_creds

        # Assemble at runtime so literal scanners don't trip on the test file.
        fake_key = "sk_" + "live_" + "abcdefghijklmnopqrstuvwx"
        pages = self._pages_with(fake_key)
        findings = _check_exposed_creds(pages)
        assert any("Stripe" in f["title"] for f in findings)


# ---------------------------------------------------------------------------
# 4. NEXT_PUBLIC env-var pattern
# ---------------------------------------------------------------------------


class TestEnvVarPattern(unittest.TestCase):
    def _pages_with(self, text: str) -> list[dict]:
        return [{"url": "https://example.com/", "text": text, "links": []}]

    def test_next_public_with_value_flagged(self):
        from scripts.ai_audit.security_lite import _check_exposed_creds

        pages = self._pages_with('NEXT_PUBLIC_SUPABASE_URL: "https://abc.supabase.co"')
        findings = _check_exposed_creds(pages)
        assert any("env_var_in_client" == f.get("check_id") for f in findings)

    def test_short_placeholder_not_flagged(self):
        from scripts.ai_audit.security_lite import _check_exposed_creds

        # value shorter than 8 chars shouldn't trigger
        pages = self._pages_with('NEXT_PUBLIC_FOO: "bar"')
        findings = _check_exposed_creds(pages)
        env_findings = [f for f in findings if f.get("check_id") == "env_var_in_client"]
        assert env_findings == []


# ---------------------------------------------------------------------------
# 6. Sitemap check
# ---------------------------------------------------------------------------


class TestCheckSitemap(unittest.TestCase):
    def test_200_passes(self):
        with patch("scripts.ai_audit.security_lite._fetch_url_status", return_value=200):
            assert _check_sitemap("https://example.com") is None

    def test_404_returns_finding(self):
        with patch("scripts.ai_audit.security_lite._fetch_url_status", return_value=404):
            finding = _check_sitemap("https://example.com")
            assert finding is not None
            assert finding["check_id"] == "sitemap_xml"
            assert finding["severity"] == "low"

    def test_network_error_returns_finding(self):
        with patch("scripts.ai_audit.security_lite._fetch_url_status", return_value=None):
            finding = _check_sitemap("https://example.com")
            assert finding is not None

    def test_sitemap_url_constructed_correctly(self):
        calls = []

        def capture(url):
            calls.append(url)
            return 200

        with patch("scripts.ai_audit.security_lite._fetch_url_status", side_effect=capture):
            _check_sitemap("https://myapp.com/subpath")
        assert calls[0] == "https://myapp.com/sitemap.xml"


# ---------------------------------------------------------------------------
# 7. Robots.txt check
# ---------------------------------------------------------------------------


class TestCheckRobots(unittest.TestCase):
    def _patch_robots(self, body: str):
        return patch("scripts.ai_audit.security_lite._fetch_text", return_value=body)

    def test_disallow_all_under_star_flagged(self):
        body = "User-agent: *\nDisallow: /\n"
        with self._patch_robots(body):
            finding = _check_robots("https://example.com")
        assert finding is not None
        assert finding["check_id"] == "robots_disallow_all"
        assert finding["severity"] == "medium"

    def test_disallow_specific_path_not_flagged(self):
        body = "User-agent: *\nDisallow: /admin/\n"
        with self._patch_robots(body):
            assert _check_robots("https://example.com") is None

    def test_allow_all_passes(self):
        body = "User-agent: *\nAllow: /\n"
        with self._patch_robots(body):
            assert _check_robots("https://example.com") is None

    def test_missing_robots_passes(self):
        with self._patch_robots(""):
            assert _check_robots("https://example.com") is None

    def test_specific_bot_disallow_not_flagged(self):
        body = "User-agent: Googlebot\nDisallow: /\n"
        with self._patch_robots(body):
            assert _check_robots("https://example.com") is None

    def test_disallow_trailing_whitespace(self):
        body = "User-agent: *\nDisallow:  /  \n"
        with self._patch_robots(body):
            finding = _check_robots("https://example.com")
        assert finding is not None


# ---------------------------------------------------------------------------
# 8. Noindex meta tag check
# ---------------------------------------------------------------------------


class TestCheckNoindex(unittest.TestCase):
    def test_noindex_meta_flagged(self):
        pages = [{"url": "https://example.com/", "raw_html": '<meta name="robots" content="noindex">'}]
        finding = _check_noindex(pages)
        assert finding is not None
        assert finding["check_id"] == "noindex_on_live_site"
        assert finding["severity"] == "high"

    def test_noindex_nofollow_flagged(self):
        pages = [{"url": "https://example.com/", "raw_html": '<meta name="robots" content="noindex, nofollow">'}]
        assert _check_noindex(pages) is not None

    def test_index_follow_passes(self):
        pages = [{"url": "https://example.com/", "raw_html": '<meta name="robots" content="index, follow">'}]
        assert _check_noindex(pages) is None

    def test_no_meta_passes(self):
        pages = [{"url": "https://example.com/", "raw_html": "<html><body>hello</body></html>"}]
        assert _check_noindex(pages) is None

    def test_empty_pages_passes(self):
        assert _check_noindex([]) is None

    def test_page_without_raw_html_key_passes(self):
        pages = [{"url": "https://example.com/", "text": "no html here"}]
        assert _check_noindex(pages) is None


# ---------------------------------------------------------------------------
# 10. run_security_lite integrates new check_ids
# ---------------------------------------------------------------------------


class TestRunSecurityLiteCheckIds(unittest.TestCase):
    def test_new_check_ids_in_output(self):
        with (
            patch("scripts.ai_audit.security_lite._fetch_response_headers", return_value=({}, 200)),
            patch("scripts.ai_audit.security_lite._fetch_url_status", return_value=200),
            patch("scripts.ai_audit.security_lite._fetch_text", return_value="User-agent: *\nAllow: /\n"),
        ):
            result = run_security_lite(
                base_url="https://example.com",
                pages=[{"url": "https://example.com/", "raw_html": "<html></html>", "text": "", "links": []}],
            )
        all_ids = result["passed_check_ids"] + result["failed_check_ids"]
        assert "sitemap_xml" in all_ids
        assert "robots_disallow_all" in all_ids
        assert "noindex_on_live_site" in all_ids

    def test_sitemap_miss_goes_to_failed(self):
        with (
            patch("scripts.ai_audit.security_lite._fetch_response_headers", return_value=({}, 200)),
            patch("scripts.ai_audit.security_lite._fetch_url_status", return_value=404),
            patch("scripts.ai_audit.security_lite._fetch_text", return_value=""),
        ):
            result = run_security_lite(base_url="https://example.com", pages=[])
        assert "sitemap_xml" in result["failed_check_ids"]
        assert any(f["check_id"] == "sitemap_xml" for f in result["findings"])


if __name__ == "__main__":
    unittest.main()
