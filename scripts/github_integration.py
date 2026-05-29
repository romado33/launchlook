"""GitHub issue creation from LaunchLook audit findings.

Pro tier feature. Customer provides a GitHub repo URL (and optionally a
commit SHA + PR number) via the intake form / customer YAML. This module
creates one GitHub issue per audit finding with the full context the
buyer already paid for, tagged with the persona that caught it.

Design discipline
-----------------
* Library-style: importable from ``scripts/github_push.py`` (the thin
  CLI) and from automated tests. No ``argparse`` here.
* Never auto-runs from the delivery pipeline. ``scripts/deliver_report.py``
  only logs a reminder; Rob runs the CLI manually after the customer
  signs off (see ``docs/GITHUB-INTEGRATION.md``).
* PAT is read from an environment variable named in the customer YAML
  (``github.token_env``). The PAT itself never appears in the YAML,
  never crosses into customer-facing surfaces, and is never printed to
  stdout or log files. Validated via ``_redact_token_in_text``.
* Only ``https://github.com/owner/repo`` URLs are accepted. SSH /
  GitLab / Gitea / self-hosted GitHub Enterprise can be added later.
* Polite rate limiting: 1-second sleep between issue POSTs. For a
  40-finding Pro audit that's a 40-second floor — comfortably inside
  GitHub's 5000 req/hour authenticated quota.

Module-level constants
----------------------
``GITHUB_API``
    GitHub REST v3 base URL.
``ISSUE_CREATE_DELAY_SECONDS``
    Floor between consecutive issue POSTs.
``USER_AGENT``
    Sent on every request so GitHub can identify the script if anything
    misbehaves at their end.
"""

from __future__ import annotations

import os
import re
import sys
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

GITHUB_API = "https://api.github.com"
USER_AGENT = "launchlook-github-integration/1.0 (+https://launchlook.app)"
ISSUE_CREATE_DELAY_SECONDS = 1.0

REPO_ROOT = Path(__file__).resolve().parent.parent

SEVERITY_BADGES = {
    "critical": "🔴 Critical",
    "high": "🟠 High",
    "medium": "🟡 Medium",
    "low": "🔵 Low",
}

# Fallback persona for findings whose YAML row predates the persona-tag
# enrichment (q5+q13). The Tourist is the documented default for happy-
# path findings with no narrower owner — see ``docs/TESTERS-CAST.md`` §3.3.
DEFAULT_TESTER = "The Tourist"


# ---------------------------------------------------------------------------
# Repo URL parsing + validation
# ---------------------------------------------------------------------------


_GITHUB_OWNER_REPO_RE = re.compile(r"^/([^/]+)/([^/]+?)(?:\.git)?/?$")


def parse_repo_url(url: str) -> tuple[str, str]:
    """Parse ``https://github.com/owner/repo`` into ``(owner, repo)``.

    Only the canonical HTTPS scheme on ``github.com`` is accepted.
    SSH (``git@github.com:...``), GitLab, Gitea, and self-hosted GitHub
    Enterprise are intentionally rejected — they can be added later if
    a customer asks. A trailing ``.git`` suffix is tolerated since
    that's how GitHub renders clone URLs.

    Raises ``ValueError`` (not a system exit) so the caller can decide
    how loudly to fail. The CLI translates it into a one-line error;
    tests assert on the ValueError directly.
    """
    if not url or not isinstance(url, str):
        raise ValueError("github.repo is required and must be a string")

    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        raise ValueError(
            f"github.repo must be an https:// URL (got {parsed.scheme or 'no'} scheme); "
            "SSH and other schemes are not supported"
        )
    if parsed.netloc.lower() != "github.com":
        raise ValueError(
            f"github.repo host must be github.com (got {parsed.netloc!r}); "
            "GitLab / Gitea / self-hosted GitHub Enterprise are not supported"
        )

    match = _GITHUB_OWNER_REPO_RE.match(parsed.path)
    if not match:
        raise ValueError(f"github.repo path must look like /owner/repo (got {parsed.path!r})")

    owner, repo = match.group(1), match.group(2)
    if not owner or not repo:
        raise ValueError(f"github.repo missing owner or repo segment: {url!r}")
    return owner, repo


# ---------------------------------------------------------------------------
# Authenticated session
# ---------------------------------------------------------------------------


def authenticated_session(token: str) -> requests.Session:
    """Return a ``requests.Session`` pre-configured with a GitHub PAT.

    Uses the GitHub-recommended ``Bearer`` scheme + the
    ``application/vnd.github+json`` Accept header so we get the
    contemporary response shape. Pins ``X-GitHub-Api-Version`` to
    ``2022-11-28`` (current stable) so the integration doesn't break
    silently when GitHub ships a new default.
    """
    if not token or not isinstance(token, str):
        raise ValueError("github PAT is empty — set the env var named in github.token_env")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        }
    )
    return session


# ---------------------------------------------------------------------------
# Issue title + body formatting
# ---------------------------------------------------------------------------


def _tester_label(finding: dict[str, Any]) -> str:
    """Resolve the persona tag for a finding, falling back to The Tourist.

    Once q5+q13 lands, findings will carry an explicit ``tester`` key.
    Until then we default to the documented fallback persona so the
    integration ships without waiting on that work.
    """
    raw = finding.get("tester") or finding.get("caught_by") or DEFAULT_TESTER
    return str(raw).strip() or DEFAULT_TESTER


def issue_title_from_finding(finding: dict[str, Any]) -> str:
    """Format ``[LaunchLook] {title} — Caught by {tester}``.

    The em-dash here is intentional (it's an issue title, not customer
    copy that lands in the PDF / email / landing page surfaces covered
    by ``SIMPLICITY-GUARDRAILS.md`` §6). It keeps the GitHub timeline
    readable and matches the in-PDF persona tag exactly.
    """
    title = (finding.get("title") or "").strip() or "(untitled finding)"
    tester = _tester_label(finding)
    return f"[LaunchLook] {title} — Caught by {tester}"


def _format_section(label: str, body: str) -> str:
    """Render a single markdown section, skipping empty bodies cleanly."""
    body = (body or "").strip()
    if not body:
        return ""
    return f"### {label}\n\n{body}\n"


def issue_body_from_finding(
    finding: dict[str, Any],
    audit_metadata: dict[str, Any],
) -> str:
    """Build the markdown body for one GitHub issue.

    Sections (in order):
        * Severity badge (one line at the top so it's visible from the
          issue list as well as the issue page)
        * What we saw       (``finding.what_we_saw``)
        * Why it matters    (``finding.why_it_matters``)
        * Recommended fix   (``finding.fix_prompt`` wrapped in a fenced
          block so it copy-pastes cleanly into an AI builder)
        * Footer            (audit id + timestamp + Saboteur re-scan
          link — see ``TESTERS-CAST.md`` §6 for The Saboteur's role)
    """
    severity = (finding.get("severity") or "").lower().strip()
    badge = SEVERITY_BADGES.get(severity, f"⚪ {severity or 'unscored'}")
    tester = _tester_label(finding)

    parts: list[str] = [f"**Severity:** {badge}  ", f"**Caught by:** {tester}", ""]

    parts.append(_format_section("What we saw", finding.get("what_we_saw", "")))
    parts.append(_format_section("Why it matters", finding.get("why_it_matters", "")))

    fix_prompt = (finding.get("fix_prompt") or "").strip()
    if fix_prompt:
        parts.append("### Paste into builder\n")
        parts.append("```text\n" + fix_prompt + "\n```\n")

    audit_id = audit_metadata.get("audit_id") or "(no audit id)"
    audit_timestamp = audit_metadata.get("audit_timestamp") or "(no timestamp)"
    commit_sha = audit_metadata.get("commit_sha")
    pr_number = audit_metadata.get("pr_number")

    footer_lines = [
        "---",
        f"From LaunchLook audit `{audit_id}` — {audit_timestamp}. "
        "Re-scan with The Saboteur at https://launchlook.app",
    ]
    if commit_sha:
        footer_lines.append(f"Tied to commit `{commit_sha}`.")
    if pr_number:
        footer_lines.append(f"Audit was triggered against PR #{pr_number}.")
    parts.append("\n".join(footer_lines))

    return "\n".join(p for p in parts if p).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Issue + PR comment creation
# ---------------------------------------------------------------------------


def _redact_token_in_text(text: str, token: str) -> str:
    """Defense-in-depth: scrub a token if it ever ended up in a string.

    GitHub error bodies very occasionally echo the auth header. We do
    not want to surface that on stdout / cost logs / Slack pastes.
    """
    if not token:
        return text
    return text.replace(token, "***REDACTED-PAT***")


def _raise_for_github_error(response: requests.Response, token: str, context: str) -> None:
    """Convert GitHub error responses into helpful, PAT-safe exceptions."""
    if response.ok:
        return

    status = response.status_code
    body_excerpt = _redact_token_in_text(response.text[:400], token)

    if status == 401:
        raise RuntimeError(
            f"{context}: 401 Unauthorized. The PAT is missing, expired, or revoked. "
            f"Generate a fresh fine-grained PAT with Issues: read+write on this repo.\n"
            f"GitHub said: {body_excerpt}"
        )
    if status == 403:
        raise RuntimeError(
            f"{context}: 403 Forbidden. The PAT exists but lacks repository or "
            "Issues:write scope (or you hit a secondary rate limit). Re-issue a "
            "fine-grained PAT scoped to this single repo with Issues: read+write.\n"
            f"GitHub said: {body_excerpt}"
        )
    if status == 404:
        raise RuntimeError(
            f"{context}: 404 Not Found. Either the repo URL is wrong, the repo is "
            "private and the PAT cannot see it, or the PAT belongs to a user who "
            "is not a collaborator.\n"
            f"GitHub said: {body_excerpt}"
        )
    raise RuntimeError(f"{context}: GitHub returned HTTP {status}. Body: {body_excerpt}")


def create_issue(
    session: requests.Session,
    owner: str,
    repo: str,
    finding: dict[str, Any],
    audit_metadata: dict[str, Any],
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """POST one issue to ``/repos/{owner}/{repo}/issues``.

    Returns the parsed JSON body GitHub responds with (which includes
    ``html_url``, ``number``, ``id``). The token is pulled out of the
    session purely so error formatters can redact it from any echoed
    body — it is never logged otherwise.
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    payload: dict[str, Any] = {
        "title": issue_title_from_finding(finding),
        "body": issue_body_from_finding(finding, audit_metadata),
    }
    if labels:
        payload["labels"] = list(labels)

    response = session.post(url, json=payload, timeout=30)
    token = session.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    _raise_for_github_error(response, token, f"create_issue({owner}/{repo})")
    return response.json()


def _format_finding_preview(finding: dict[str, Any], audit_metadata: dict[str, Any]) -> str:
    """Single-block dry-run preview: title + first lines of the body."""
    title = issue_title_from_finding(finding)
    body = issue_body_from_finding(finding, audit_metadata)
    body_preview = "\n".join(body.splitlines()[:12])
    return f"=== {title} ===\n{body_preview}\n...\n"


# ---------------------------------------------------------------------------
# YAML loading helpers (mirrors deliver_report.load_customer_yaml shape)
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency missing
        raise RuntimeError("pyyaml not installed. Run: pip install -r requirements.txt") from exc

    if not path.exists():
        raise FileNotFoundError(f"customer YAML not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as a YAML mapping")
    return data


def _audit_metadata_from_yaml(yaml_path: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Build the audit_metadata dict that the issue body footer consumes."""
    from datetime import date

    customer = data.get("customer") or {}
    github_block = data.get("github") or {}

    # Stable audit_id: derive from YAML stem so re-runs from the same
    # file produce the same audit_id (even though they DO produce
    # duplicate issues — see docs/GITHUB-INTEGRATION.md "Re-running").
    audit_id = github_block.get("audit_id") or yaml_path.stem

    return {
        "audit_id": audit_id,
        "audit_timestamp": github_block.get("audit_timestamp") or date.today().isoformat(),
        "customer_name": customer.get("first_name", ""),
        "app_name": customer.get("app_name", ""),
        "commit_sha": github_block.get("commit_sha"),
        "pr_number": github_block.get("pr_number"),
    }


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def create_all_issues(
    repo_url: str,
    token: str,
    audit_yaml_path: str | Path,
    dry_run: bool = False,
    labels: list[str] | None = None,
    sleep_seconds: float = ISSUE_CREATE_DELAY_SECONDS,
    sleep_fn=time.sleep,
    out=sys.stdout,
) -> list[dict[str, Any]]:
    """Main entry point. Create (or preview) one issue per finding.

    ``dry_run=True`` prints a preview of every issue without making any
    network calls — used by the ``--dry-run`` CLI flag and exercised in
    tests so a misconfigured environment can't accidentally hit GitHub.

    Returns a list of dicts: in live mode each carries the GitHub
    response (``html_url``, ``number``); in dry-run mode each carries
    ``{"title": ..., "preview": ...}`` so the caller can render a table.

    ``sleep_fn`` is parameterized so tests can pass a no-op and assert
    on the call count instead of waiting real seconds.
    """
    owner, repo = parse_repo_url(repo_url)
    yaml_path = Path(audit_yaml_path).resolve()
    data = _load_yaml(yaml_path)
    findings = data.get("findings") or []
    if not isinstance(findings, list) or not findings:
        raise ValueError(f"{yaml_path} has no findings to push")

    audit_metadata = _audit_metadata_from_yaml(yaml_path, data)
    results: list[dict[str, Any]] = []

    if dry_run:
        print(
            f"[dry-run] Would create {len(findings)} issue(s) on {owner}/{repo}.\n",
            file=out,
        )
        for finding in findings:
            preview = _format_finding_preview(finding, audit_metadata)
            print(preview, file=out)
            results.append(
                {
                    "title": issue_title_from_finding(finding),
                    "preview": preview,
                    "dry_run": True,
                }
            )
        return results

    session = authenticated_session(token)
    for i, finding in enumerate(findings, start=1):
        if i > 1:
            # Polite delay between POSTs. See module docstring for the math.
            sleep_fn(sleep_seconds)
        response = create_issue(session, owner, repo, finding, audit_metadata, labels=labels)
        results.append(
            {
                "title": issue_title_from_finding(finding),
                "issue_url": response.get("html_url"),
                "issue_number": response.get("number"),
            }
        )
        print(
            f"  ✓ [{i}/{len(findings)}] #{response.get('number')} {response.get('html_url')}",
            file=out,
        )
    return results


def add_pr_comment(
    repo_url: str,
    pr_number: int,
    token: str,
    audit_yaml_path: str | Path,
    issue_urls: Iterable[str] | None = None,
    out=sys.stdout,
) -> dict[str, Any]:
    """Post a single summary comment on a PR with a checklist of findings.

    ``issue_urls`` (when supplied by the CLI after a live push) links
    each finding line to the issue we just created. When omitted, the
    comment falls back to a plain bulleted summary.
    """
    owner, repo = parse_repo_url(repo_url)
    yaml_path = Path(audit_yaml_path).resolve()
    data = _load_yaml(yaml_path)
    findings = data.get("findings") or []
    if not isinstance(findings, list) or not findings:
        raise ValueError(f"{yaml_path} has no findings to comment")

    issue_urls = list(issue_urls or [])

    lines: list[str] = [
        f"## LaunchLook audit — {len(findings)} findings",
        "",
        "Auto-posted by the LaunchLook Pro tier GitHub integration. "
        "Severity icons match the PDF report.",
        "",
    ]
    for i, finding in enumerate(findings):
        severity = (finding.get("severity") or "").lower()
        badge = SEVERITY_BADGES.get(severity, "⚪")
        title = (finding.get("title") or "(untitled finding)").strip()
        url = issue_urls[i] if i < len(issue_urls) else None
        if url:
            lines.append(f"- [ ] {badge.split()[0]} [{title}]({url})")
        else:
            lines.append(f"- [ ] {badge.split()[0]} {title}")

    body = "\n".join(lines) + "\n"

    session = authenticated_session(token)
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{int(pr_number)}/comments"
    response = session.post(url, json={"body": body}, timeout=30)
    token_for_redaction = session.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    _raise_for_github_error(
        response, token_for_redaction, f"add_pr_comment({owner}/{repo}#{pr_number})"
    )
    payload = response.json()
    print(f"  ✓ Posted PR comment: {payload.get('html_url')}", file=out)
    return payload


# ---------------------------------------------------------------------------
# Helpers exposed for the CLI + tests
# ---------------------------------------------------------------------------


def resolve_token_from_yaml(data: dict[str, Any]) -> tuple[str, str]:
    """Return ``(token, env_var_name)`` from the ``github.token_env`` field.

    Raises ``RuntimeError`` if either the YAML is missing the field or
    the env var is unset. The env var name is returned alongside the
    token so error messages can tell Rob *which* env var to export
    without having to re-open the YAML.
    """
    github_block = data.get("github") or {}
    env_var = github_block.get("token_env")
    if not env_var:
        raise RuntimeError(
            "github.token_env is required in the customer YAML "
            "(name of env var holding the customer's fine-grained PAT)"
        )
    token = os.environ.get(env_var)
    if not token:
        raise RuntimeError(
            f"env var {env_var!r} is unset. Export the customer's fine-grained "
            f"PAT before running the CLI: $env:{env_var}=<pat> (PowerShell) or "
            f"export {env_var}=<pat> (bash)."
        )
    return token, env_var


def load_customer_yaml(path: str | Path) -> dict[str, Any]:
    """Public wrapper around the private YAML loader (for the CLI + tests)."""
    return _load_yaml(Path(path).resolve())
