"""Tests for ``scripts/ai_audit/unsubscribe_check.py``.

Covers:
1. extract_unsubscribe_links — anchor text, href keywords, plain-text
   proximity, List-Unsubscribe header, and de-duplication.
2. check_unsubscribe_url — 200 working, 404 not working, network error.
3. run_unsubscribe_check — found+working, found+broken, not found.
4. Integration path through to_findings in form_smoke_test.py:
   - email arrived + no unsubscribe link → medium finding
   - email arrived + broken unsubscribe link → high finding
   - email arrived + working unsubscribe link → passed check
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts.ai_audit.unsubscribe_check import (  # noqa: E402
    check_unsubscribe_url,
    extract_unsubscribe_links,
    run_unsubscribe_check,
)

# ---------------------------------------------------------------------------
# 1. extract_unsubscribe_links
# ---------------------------------------------------------------------------


class TestExtractUnsubscribeLinks(unittest.TestCase):
    def test_anchor_text_match(self):
        html = '<a href="https://example.com/unsub?tok=abc">Unsubscribe</a>'
        links = extract_unsubscribe_links(html)
        assert "https://example.com/unsub?tok=abc" in links

    def test_anchor_text_case_insensitive(self):
        html = '<a href="https://example.com/remove">UNSUBSCRIBE HERE</a>'
        links = extract_unsubscribe_links(html)
        assert "https://example.com/remove" in links

    def test_anchor_href_keyword(self):
        html = '<a href="https://example.com/optout?id=1">Click here</a>'
        links = extract_unsubscribe_links(html)
        assert "https://example.com/optout?id=1" in links

    def test_opt_out_href(self):
        html = '<a href="https://example.com/opt-out">manage preferences</a>'
        links = extract_unsubscribe_links(html)
        assert "https://example.com/opt-out" in links

    def test_plain_text_near_unsubscribe(self):
        text = "To stop receiving these emails, visit https://example.com/unsub?t=xyz to unsubscribe."
        links = extract_unsubscribe_links("", text)
        assert "https://example.com/unsub?t=xyz" in links

    def test_plain_text_url_too_far_not_matched(self):
        # URL is more than 120 chars away from "unsubscribe"
        far_text = "https://example.com/random " + " " * 200 + " unsubscribe at some point"
        links = extract_unsubscribe_links("", far_text)
        # Should not pick up the URL that's 200 chars from "unsubscribe"
        assert "https://example.com/random" not in links

    def test_list_unsubscribe_header(self):
        header = "<https://example.com/unsub>, <mailto:unsub@example.com>"
        links = extract_unsubscribe_links("", "", header)
        assert "https://example.com/unsub" in links

    def test_deduplication(self):
        url = "https://example.com/unsubscribe"
        html = f'<a href="{url}">Unsubscribe</a> <a href="{url}">opt out</a>'
        links = extract_unsubscribe_links(html)
        assert links.count(url) == 1

    def test_no_links_in_empty_email(self):
        assert extract_unsubscribe_links("", "", "") == []

    def test_irrelevant_links_ignored(self):
        html = '<a href="https://example.com/blog">Read the blog</a>'
        assert extract_unsubscribe_links(html) == []

    def test_trailing_punctuation_stripped(self):
        text = "unsubscribe here: https://example.com/unsub."
        links = extract_unsubscribe_links("", text)
        assert "https://example.com/unsub" in links
        assert "https://example.com/unsub." not in links


# ---------------------------------------------------------------------------
# 2. check_unsubscribe_url
# ---------------------------------------------------------------------------


class TestCheckUnsubscribeUrl(unittest.TestCase):
    def test_200_returns_200(self):
        with patch("scripts.ai_audit.unsubscribe_check.urllib.request.urlopen") as m:
            m.return_value.__enter__.return_value.status = 200
            assert check_unsubscribe_url("https://example.com/unsub") == 200

    def test_404_returns_404(self):
        import urllib.error

        exc = urllib.error.HTTPError(
            "https://example.com/unsub", 404, "Not Found", {}, None
        )
        with patch("scripts.ai_audit.unsubscribe_check.urllib.request.urlopen", side_effect=exc):
            assert check_unsubscribe_url("https://example.com/unsub") == 404

    def test_network_error_returns_none(self):
        import urllib.error

        with patch(
            "scripts.ai_audit.unsubscribe_check.urllib.request.urlopen",
            side_effect=urllib.error.URLError("timeout"),
        ):
            assert check_unsubscribe_url("https://example.com/unsub") is None


# ---------------------------------------------------------------------------
# 3. run_unsubscribe_check
# ---------------------------------------------------------------------------


class TestRunUnsubscribeCheck(unittest.TestCase):
    def test_found_and_working(self):
        html = '<a href="https://example.com/unsub">Unsubscribe</a>'
        with patch(
            "scripts.ai_audit.unsubscribe_check.check_unsubscribe_url", return_value=200
        ):
            result = run_unsubscribe_check(html)
        assert result["found"] is True
        assert result["working"] is True
        assert result["url"] == "https://example.com/unsub"
        assert result["status"] == 200

    def test_found_but_broken(self):
        html = '<a href="https://example.com/unsub">Unsubscribe</a>'
        with patch(
            "scripts.ai_audit.unsubscribe_check.check_unsubscribe_url", return_value=404
        ):
            result = run_unsubscribe_check(html)
        assert result["found"] is True
        assert result["working"] is False
        assert result["status"] == 404

    def test_not_found(self):
        result = run_unsubscribe_check("<p>Thanks for signing up!</p>")
        assert result["found"] is False
        assert result["working"] is None
        assert result["url"] is None

    def test_network_error_is_not_working(self):
        html = '<a href="https://example.com/unsub">Unsubscribe</a>'
        with patch(
            "scripts.ai_audit.unsubscribe_check.check_unsubscribe_url", return_value=None
        ):
            result = run_unsubscribe_check(html)
        assert result["found"] is True
        assert result["working"] is False

    def test_3xx_redirect_counts_as_working(self):
        html = '<a href="https://example.com/unsub">Unsubscribe</a>'
        with patch(
            "scripts.ai_audit.unsubscribe_check.check_unsubscribe_url", return_value=302
        ):
            result = run_unsubscribe_check(html)
        assert result["working"] is True

    def test_all_urls_returned(self):
        html = (
            '<a href="https://example.com/unsub1">Unsubscribe</a>'
            '<a href="https://example.com/unsub2">opt out</a>'
        )
        with patch(
            "scripts.ai_audit.unsubscribe_check.check_unsubscribe_url", return_value=200
        ):
            result = run_unsubscribe_check(html)
        assert len(result["all_urls"]) == 2


# ---------------------------------------------------------------------------
# 4. Integration with to_findings (email_roundtrip path)
# ---------------------------------------------------------------------------


class TestToFindingsUnsubscribeIntegration(unittest.TestCase):
    def _call_to_findings(self, email_roundtrip: list) -> dict:
        from scripts.ai_audit.form_smoke_test import to_findings

        return to_findings(
            [],
            tier="Pro Package",
            platform="generic",
            email_roundtrip=email_roundtrip,
        )

    def _entry(self, arrived: bool, email_html: str = "") -> dict:
        return {
            "arrived": arrived,
            "email_html": email_html,
            "email_text": "",
            "list_unsubscribe_header": "",
            "form": {"id": "newsletter", "submit_label": "Subscribe"},
        }

    def test_no_unsubscribe_link_produces_medium_finding(self):
        entry = self._entry(arrived=True, email_html="<p>Thanks!</p>")
        result = self._call_to_findings([entry])
        ids = [f["id"] for f in result["findings"]]
        assert any("no_unsubscribe_link" in fid for fid in ids)
        unsub_findings = [f for f in result["findings"] if "no_unsubscribe" in f["id"]]
        assert unsub_findings[0]["severity"] == "medium"

    def test_broken_unsubscribe_produces_high_finding(self):
        html = '<a href="https://example.com/unsub">Unsubscribe</a>'
        entry = self._entry(arrived=True, email_html=html)
        with patch(
            "scripts.ai_audit.unsubscribe_check.check_unsubscribe_url", return_value=404
        ):
            result = self._call_to_findings([entry])
        broken = [f for f in result["findings"] if "broken_unsubscribe" in f["id"]]
        assert broken, "expected broken_unsubscribe_link finding"
        assert broken[0]["severity"] == "high"

    def test_working_unsubscribe_passes(self):
        html = '<a href="https://example.com/unsub">Unsubscribe</a>'
        entry = self._entry(arrived=True, email_html=html)
        with patch(
            "scripts.ai_audit.unsubscribe_check.check_unsubscribe_url", return_value=200
        ):
            result = self._call_to_findings([entry])
        assert any("unsubscribe_link_works" in pid for pid in result["passed_check_ids"])
        assert not any("unsubscribe" in f["id"] for f in result["findings"])

    def test_email_not_arrived_no_unsubscribe_check(self):
        entry = self._entry(arrived=False)
        with patch(
            "scripts.ai_audit.unsubscribe_check.check_unsubscribe_url"
        ) as mock_check:
            self._call_to_findings([entry])
        mock_check.assert_not_called()


if __name__ == "__main__":
    unittest.main()
