"""Tests for scripts/github_integration.py.

Covers the behaviour the q19 task spec calls out:

* `parse_repo_url` accepts valid HTTPS GitHub URLs and rejects SSH,
  GitLab, Gitea, and malformed paths.
* `issue_title_from_finding` includes the persona tag in the title.
* `issue_body_from_finding` includes every required section (severity
  badge, what we saw, why it matters, fix prompt, audit footer).
* `create_issue` mocks the GitHub API and asserts the request shape.
* `create_all_issues` (live mode) sleeps between POSTs to respect the
  rate-limit floor.
* DO NOT make real GitHub API calls. Every test that touches the
  network does so through `unittest.mock.patch` on `requests.Session`.

Runnable two ways:
    * `pytest tests/test_github_integration.py` (preferred).
    * `python tests/test_github_integration.py` for a stdlib-only run.
"""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import github_integration as gh  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _finding(
    title: str = "Your /pricing page takes 4+ seconds to show its main image.",
    severity: str = "high",
    tester: str | None = "The Phone-First Friend",
) -> dict:
    f = {
        "severity": severity,
        "title": title,
        "what_we_saw": "We loaded /pricing on a cold cache and waited.",
        "why_it_matters": "First-time visitors usually leave before that finishes.",
        "fix_prompt": "Lazy-load the hero image and serve a 100 KB poster instead.",
    }
    if tester is not None:
        f["tester"] = tester
    return f


def _audit_metadata() -> dict:
    return {
        "audit_id": "jane-sparkle-2026-05-26",
        "audit_timestamp": "2026-05-26",
        "commit_sha": "abc123def",
        "pr_number": 42,
    }


def _fake_response(status: int = 201, body: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.ok = 200 <= status < 300
    resp.text = "" if body is None else str(body)
    resp.json.return_value = body or {
        "html_url": "https://github.com/owner/repo/issues/1",
        "number": 1,
    }
    return resp


# ---------------------------------------------------------------------------
# parse_repo_url
# ---------------------------------------------------------------------------


class ParseRepoUrlTests(unittest.TestCase):
    def test_canonical_https_url(self):
        self.assertEqual(
            gh.parse_repo_url("https://github.com/jane-sparkle/main-site"),
            ("jane-sparkle", "main-site"),
        )

    def test_trailing_slash_tolerated(self):
        self.assertEqual(
            gh.parse_repo_url("https://github.com/jane-sparkle/main-site/"),
            ("jane-sparkle", "main-site"),
        )

    def test_dot_git_suffix_tolerated(self):
        self.assertEqual(
            gh.parse_repo_url("https://github.com/jane-sparkle/main-site.git"),
            ("jane-sparkle", "main-site"),
        )

    def test_ssh_rejected(self):
        with self.assertRaises(ValueError):
            gh.parse_repo_url("git@github.com:jane-sparkle/main-site.git")

    def test_http_rejected(self):
        with self.assertRaises(ValueError):
            gh.parse_repo_url("http://github.com/jane-sparkle/main-site")

    def test_gitlab_rejected(self):
        with self.assertRaises(ValueError):
            gh.parse_repo_url("https://gitlab.com/jane-sparkle/main-site")

    def test_gitea_rejected(self):
        with self.assertRaises(ValueError):
            gh.parse_repo_url("https://gitea.example.com/jane/main")

    def test_missing_repo_segment_rejected(self):
        with self.assertRaises(ValueError):
            gh.parse_repo_url("https://github.com/jane-sparkle")

    def test_extra_segments_rejected(self):
        with self.assertRaises(ValueError):
            gh.parse_repo_url("https://github.com/jane-sparkle/main-site/tree/main")

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            gh.parse_repo_url("")


# ---------------------------------------------------------------------------
# issue_title_from_finding
# ---------------------------------------------------------------------------


class IssueTitleTests(unittest.TestCase):
    def test_format_includes_persona_tag(self):
        title = gh.issue_title_from_finding(_finding(tester="The Phone-First Friend"))
        self.assertIn("[LaunchLook]", title)
        self.assertIn("Caught by The Phone-First Friend", title)
        self.assertIn(
            "Your /pricing page takes 4+ seconds to show its main image.",
            title,
        )

    def test_falls_back_to_tourist_when_tester_missing(self):
        title = gh.issue_title_from_finding(_finding(tester=None))
        self.assertIn("Caught by The Tourist", title)

    def test_untitled_finding_does_not_crash(self):
        title = gh.issue_title_from_finding({"severity": "low"})
        self.assertIn("(untitled finding)", title)
        self.assertIn("Caught by The Tourist", title)


# ---------------------------------------------------------------------------
# issue_body_from_finding
# ---------------------------------------------------------------------------


class IssueBodyTests(unittest.TestCase):
    def test_includes_all_required_sections(self):
        body = gh.issue_body_from_finding(_finding(severity="high"), _audit_metadata())
        # Severity badge
        self.assertIn("**Severity:**", body)
        self.assertIn("🟠 High", body)
        # Persona
        self.assertIn("**Caught by:** The Phone-First Friend", body)
        # What we saw / why it matters
        self.assertIn("### What we saw", body)
        self.assertIn("We loaded /pricing on a cold cache and waited.", body)
        self.assertIn("### Why it matters", body)
        self.assertIn("First-time visitors usually leave before that finishes.", body)
        # Fix prompt
        self.assertIn("### Recommended fix prompt", body)
        self.assertIn("Lazy-load the hero image", body)
        # Audit footer
        self.assertIn("From LaunchLook audit `jane-sparkle-2026-05-26`", body)
        self.assertIn("2026-05-26", body)
        self.assertIn("Re-scan with The Saboteur at https://launchlook.app", body)

    def test_unknown_severity_renders_safely(self):
        body = gh.issue_body_from_finding(
            _finding(severity="weird"), _audit_metadata(),
        )
        self.assertIn("weird", body)
        self.assertIn("**Severity:**", body)

    def test_commit_sha_and_pr_in_footer_when_present(self):
        body = gh.issue_body_from_finding(_finding(), _audit_metadata())
        self.assertIn("Tied to commit `abc123def`.", body)
        self.assertIn("Audit was triggered against PR #42.", body)

    def test_commit_sha_omitted_when_absent(self):
        meta = _audit_metadata()
        meta["commit_sha"] = None
        meta["pr_number"] = None
        body = gh.issue_body_from_finding(_finding(), meta)
        self.assertNotIn("Tied to commit", body)
        self.assertNotIn("Audit was triggered against PR", body)


# ---------------------------------------------------------------------------
# create_issue (mocked)
# ---------------------------------------------------------------------------


class CreateIssueTests(unittest.TestCase):
    def test_posts_correct_payload(self):
        session = gh.authenticated_session("dummy-token")
        session.post = MagicMock(return_value=_fake_response(201))

        result = gh.create_issue(
            session,
            owner="jane-sparkle",
            repo="main-site",
            finding=_finding(),
            audit_metadata=_audit_metadata(),
            labels=["launchlook", "audit-finding"],
        )

        # Verify the URL we POSTed to
        self.assertEqual(session.post.call_count, 1)
        args, kwargs = session.post.call_args
        self.assertEqual(args[0], "https://api.github.com/repos/jane-sparkle/main-site/issues")

        # Verify payload shape
        payload = kwargs["json"]
        self.assertIn("[LaunchLook]", payload["title"])
        self.assertIn("Caught by The Phone-First Friend", payload["title"])
        self.assertIn("**Severity:**", payload["body"])
        self.assertEqual(payload["labels"], ["launchlook", "audit-finding"])

        # Verify we returned the parsed response body
        self.assertEqual(result["number"], 1)

    def test_403_raises_helpful_error(self):
        session = gh.authenticated_session("dummy-token")
        session.post = MagicMock(return_value=_fake_response(403, {"message": "forbidden"}))
        with self.assertRaises(RuntimeError) as ctx:
            gh.create_issue(
                session,
                owner="jane",
                repo="main-site",
                finding=_finding(),
                audit_metadata=_audit_metadata(),
            )
        self.assertIn("403", str(ctx.exception))
        self.assertIn("Issues:write", str(ctx.exception))

    def test_404_raises_helpful_error(self):
        session = gh.authenticated_session("dummy-token")
        session.post = MagicMock(return_value=_fake_response(404, {"message": "not found"}))
        with self.assertRaises(RuntimeError) as ctx:
            gh.create_issue(
                session,
                owner="jane",
                repo="main-site",
                finding=_finding(),
                audit_metadata=_audit_metadata(),
            )
        self.assertIn("404", str(ctx.exception))

    def test_pat_never_in_error_message(self):
        # Defense-in-depth: if GitHub echoes our token back in a body,
        # we redact it before raising.
        session = gh.authenticated_session("super-secret-token-xyz")
        echo_body = {"message": "Bad credentials: super-secret-token-xyz"}
        # Need the response.text to actually contain the token (it doesn't
        # by default from MagicMock — supply it explicitly).
        resp = _fake_response(401, echo_body)
        resp.text = "super-secret-token-xyz lives here"
        session.post = MagicMock(return_value=resp)
        with self.assertRaises(RuntimeError) as ctx:
            gh.create_issue(
                session,
                owner="jane",
                repo="main-site",
                finding=_finding(),
                audit_metadata=_audit_metadata(),
            )
        msg = str(ctx.exception)
        self.assertNotIn("super-secret-token-xyz", msg)
        self.assertIn("REDACTED-PAT", msg)


# ---------------------------------------------------------------------------
# Rate limiting / backoff
# ---------------------------------------------------------------------------


class RateLimitTests(unittest.TestCase):
    def test_create_all_issues_sleeps_between_posts(self):
        # Build a 3-finding YAML in memory and patch the loader to return it.
        data = {
            "customer": {"first_name": "Mira", "app_name": "Tessera"},
            "findings": [_finding(title=f"Finding {i}") for i in range(3)],
            "github": {"repo": "https://github.com/owner/repo"},
        }
        sleep_calls: list[float] = []

        with patch.object(gh, "_load_yaml", return_value=data), \
             patch.object(gh, "requests") as mock_requests:
            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=_fake_response(201))
            mock_session.headers = {"Authorization": "Bearer dummy"}
            mock_requests.Session = MagicMock(return_value=mock_session)

            results = gh.create_all_issues(
                repo_url="https://github.com/owner/repo",
                token="dummy",
                audit_yaml_path="/fake/path.yaml",
                dry_run=False,
                sleep_fn=sleep_calls.append,
                out=io.StringIO(),
            )

        # Between 3 POSTs we expect 2 sleeps (none before the first one).
        self.assertEqual(len(sleep_calls), 2)
        # Each sleep should be the rate-limit floor.
        for delay in sleep_calls:
            self.assertGreaterEqual(delay, gh.ISSUE_CREATE_DELAY_SECONDS)
        # We still returned 3 results.
        self.assertEqual(len(results), 3)


# ---------------------------------------------------------------------------
# Dry-run
# ---------------------------------------------------------------------------


class DryRunTests(unittest.TestCase):
    def test_dry_run_makes_no_network_calls(self):
        data = {
            "customer": {"first_name": "Mira", "app_name": "Tessera"},
            "findings": [_finding(title=f"Finding {i}") for i in range(2)],
            "github": {"repo": "https://github.com/owner/repo"},
        }
        with patch.object(gh, "_load_yaml", return_value=data), \
             patch.object(gh, "requests") as mock_requests:
            buf = io.StringIO()
            results = gh.create_all_issues(
                repo_url="https://github.com/owner/repo",
                token="",
                audit_yaml_path="/fake/path.yaml",
                dry_run=True,
                out=buf,
            )
            # No requests.Session() instantiation in dry-run.
            mock_requests.Session.assert_not_called()
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertTrue(r["dry_run"])
        output = buf.getvalue()
        self.assertIn("[dry-run]", output)
        self.assertIn("[LaunchLook]", output)


# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------


class TokenResolutionTests(unittest.TestCase):
    def test_missing_token_env_raises(self):
        with self.assertRaises(RuntimeError):
            gh.resolve_token_from_yaml({"github": {}})

    def test_unset_env_var_raises_with_var_name(self):
        with patch.dict("os.environ", {}, clear=False):
            try:
                # Ensure the var isn't set
                import os
                os.environ.pop("Q19_TEST_PAT_DOES_NOT_EXIST", None)
                with self.assertRaises(RuntimeError) as ctx:
                    gh.resolve_token_from_yaml(
                        {"github": {"token_env": "Q19_TEST_PAT_DOES_NOT_EXIST"}}
                    )
                self.assertIn("Q19_TEST_PAT_DOES_NOT_EXIST", str(ctx.exception))
            finally:
                pass

    def test_token_resolved_from_env(self):
        with patch.dict("os.environ", {"Q19_TEST_PAT": "ghp_test"}, clear=False):
            token, env_var = gh.resolve_token_from_yaml(
                {"github": {"token_env": "Q19_TEST_PAT"}}
            )
            self.assertEqual(token, "ghp_test")
            self.assertEqual(env_var, "Q19_TEST_PAT")


if __name__ == "__main__":
    unittest.main()
