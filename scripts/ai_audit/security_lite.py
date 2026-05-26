"""Snoop's security-lite checks (per docs/TESTERS-CAST.md).

The Snoop persona "pokes around for exposed keys, public admin routes,
missing security headers, leaky URLs." This module runs a small,
deterministic set of HTTP-header and HTML-content checks against the
customer's live URL and emits *pre-generated findings* that get merged
into the LLM-driven findings list.

The checks (5 total, per docs/PRODUCT-DECISIONS.md and the q3 brief):
    1. HSTS header presence (HTTPS sites only).
    2. CSP header presence.
    3. X-Frame-Options presence (and not too permissive).
    4. X-Content-Type-Options nosniff.
    5. Exposed credentials / paths in the HTML extract:
       - AWS access keys, Google/Stripe API keys, RSA private key blocks.
       - Visible /admin, /.env, /.git, firebase config dumps.

Each check returns a dict in the same shape as an LLM-generated finding
(severity, title, what_we_saw, why_it_matters, fix_prompt) plus the
internal-only fields ``category`` and ``tagged_by_persona`` ("Snoop").
The pipeline merges these into the final findings list before the YAML
write, and tags the customer-visible "What's working" / "Passed checks"
section with whichever Snoop categories returned no finding.

Per SIMPLICITY-GUARDRAILS §6 (no internal jargon on customer surfaces),
the customer-facing fields use plain English. The category id and the
"Caught by The Snoop" persona tag stay in YAML / report meta only.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse


SNOOP_PERSONA = "The Snoop"
SNOOP_TAG = "Caught by The Snoop"
CATEGORY_ID = "security_lite"

HEAD_TIMEOUT_SEC = 10
USER_AGENT = "Mozilla/5.0 (LaunchLook AI Audit; +https://launchlook.app)"


# ---------------------------------------------------------------------------
# 1-4: header checks
# ---------------------------------------------------------------------------


def _fetch_response_headers(url: str) -> tuple[dict[str, str], int | None]:
    """Return ``(headers, status)`` for ``url``. Empty dict on any error."""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=HEAD_TIMEOUT_SEC) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return headers, resp.status
    except urllib.error.HTTPError as exc:
        try:
            return {k.lower(): v for k, v in exc.headers.items()}, exc.code
        except Exception:  # noqa: BLE001
            return {}, exc.code
    except Exception:  # noqa: BLE001
        return {}, None


def _check_hsts(url: str, headers: dict[str, str]) -> dict[str, Any] | None:
    is_https = urlparse(url).scheme == "https"
    if not is_https:
        return None
    if "strict-transport-security" in headers:
        return None
    return {
        "severity": "high",
        "title": "Site is missing HTTPS-only protection (HSTS)",
        "what_we_saw": (
            "Your live site loads over HTTPS, but the server does not send a "
            "Strict-Transport-Security response header. We checked the homepage "
            "response and the header is absent."
        ),
        "why_it_matters": (
            "Without HSTS, a visitor's first request can still land on the "
            "insecure HTTP version of your site before redirecting. On a "
            "hostile network that gap is enough to leak login cookies or "
            "swap in modified content."
        ),
        "fix_prompt": (
            "Configure the production server / hosting platform to send a "
            "Strict-Transport-Security response header on every page. "
            "Recommended starter value: "
            "Strict-Transport-Security: max-age=31536000; includeSubDomains. "
            "Most builders (Vercel, Netlify, Cloudflare, Webflow) expose this "
            "in the platform's SSL or HTTPS settings."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": SNOOP_PERSONA,
        "tag": SNOOP_TAG,
        "check_id": "hsts",
    }


def _check_csp(headers: dict[str, str]) -> dict[str, Any] | None:
    if "content-security-policy" in headers:
        return None
    return {
        "severity": "medium",
        "title": "No Content-Security-Policy header",
        "what_we_saw": (
            "Your homepage response does not include a Content-Security-Policy "
            "header. We checked the live URL's response headers and the "
            "policy is absent."
        ),
        "why_it_matters": (
            "A Content-Security-Policy is the modern browser-level defense "
            "against accidentally injected scripts (from a third-party widget, "
            "a vibe-coded copy-paste, or an attacker-controlled CDN). Without "
            "one, anything that lands in your HTML can run."
        ),
        "fix_prompt": (
            "Add a Content-Security-Policy response header on the production "
            "domain. Start with a permissive baseline that allows your "
            "current scripts and tighten later: "
            "Content-Security-Policy: default-src 'self' https: data: 'unsafe-inline'. "
            "Most hosting platforms (Vercel, Netlify, Cloudflare, Webflow) "
            "let you set custom response headers in the project settings."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": SNOOP_PERSONA,
        "tag": SNOOP_TAG,
        "check_id": "csp",
    }


def _check_xfo(headers: dict[str, str]) -> dict[str, Any] | None:
    raw = headers.get("x-frame-options")
    if raw and raw.strip().upper() in {"DENY", "SAMEORIGIN"}:
        return None
    if raw:
        return {
            "severity": "medium",
            "title": "X-Frame-Options is set, but not strictly enough",
            "what_we_saw": (
                "Your homepage sends an X-Frame-Options response header, but "
                f"the value ({raw!r}) does not match DENY or SAMEORIGIN."
            ),
            "why_it_matters": (
                "A loose X-Frame-Options value means a hostile site could "
                "embed your live URL in an invisible iframe and trick users "
                "into clicking buttons they think they aren't (clickjacking)."
            ),
            "fix_prompt": (
                "Update the production X-Frame-Options response header to "
                "either DENY (your site never appears in any iframe) or "
                "SAMEORIGIN (your site only appears in iframes on your own "
                "domain). Most hosting platforms expose this in custom "
                "response-header settings."
            ),
            "category": CATEGORY_ID,
            "tagged_by_persona": SNOOP_PERSONA,
            "tag": SNOOP_TAG,
            "check_id": "x_frame_options",
        }
    return {
        "severity": "medium",
        "title": "No X-Frame-Options header (clickjacking protection)",
        "what_we_saw": (
            "Your homepage response does not include an X-Frame-Options "
            "header, and we did not find a frame-ancestors directive in any "
            "Content-Security-Policy header."
        ),
        "why_it_matters": (
            "Without this header, a hostile site can embed your live URL in "
            "an invisible iframe and trick users into clicking buttons they "
            "did not mean to (clickjacking). It's a one-line fix."
        ),
        "fix_prompt": (
            "Add X-Frame-Options: SAMEORIGIN as a custom response header on "
            "the production domain. If you control the CSP header, you can "
            "also use frame-ancestors 'self' which is the modern equivalent. "
            "Most hosting platforms (Vercel, Netlify, Cloudflare, Webflow) "
            "expose response-header settings in the project dashboard."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": SNOOP_PERSONA,
        "tag": SNOOP_TAG,
        "check_id": "x_frame_options",
    }


def _check_xcto(headers: dict[str, str]) -> dict[str, Any] | None:
    raw = headers.get("x-content-type-options", "").strip().lower()
    if raw == "nosniff":
        return None
    return {
        "severity": "low",
        "title": "Missing X-Content-Type-Options: nosniff",
        "what_we_saw": (
            "Your homepage response does not include "
            "X-Content-Type-Options: nosniff."
        ),
        "why_it_matters": (
            "Without nosniff, the browser is allowed to guess the type of a "
            "response (e.g. treat a text file as JavaScript). It's a small, "
            "preventable risk on a customer-facing site."
        ),
        "fix_prompt": (
            "Add X-Content-Type-Options: nosniff as a custom response header "
            "on the production domain. Most hosting platforms expose this "
            "alongside other response-header settings."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": SNOOP_PERSONA,
        "tag": SNOOP_TAG,
        "check_id": "x_content_type_options",
    }


# ---------------------------------------------------------------------------
# 5: HTML content sweep for exposed creds / paths
# ---------------------------------------------------------------------------


# Each entry: (label, pattern, redact). Patterns are intentionally tight to
# minimize false positives on placeholder copy ("YOUR_API_KEY_HERE" etc.).
_CRED_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Stripe secret key (live)", re.compile(r"sk_live_[0-9a-zA-Z]{16,}")),
    ("Stripe restricted key", re.compile(r"rk_live_[0-9a-zA-Z]{16,}")),
    ("Slack token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")),
    ("Firebase config (apiKey)", re.compile(r'apiKey\s*:\s*"AIza[0-9A-Za-z\-_]{35}"')),
]


# Visible link hrefs that suggest a public surface that probably should not
# be on a published consumer site. We match on links rather than free text
# to avoid false positives from copy that happens to mention "/admin".
_LEAKY_LINK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("public /admin route", re.compile(r"^/admin(/|$)", re.IGNORECASE)),
    ("public /.env file", re.compile(r"\.env(\?|$)", re.IGNORECASE)),
    ("public /.git directory", re.compile(r"\.git(/|$)", re.IGNORECASE)),
    ("public /debug route", re.compile(r"^/debug(/|$)", re.IGNORECASE)),
    ("public /dev-tools route", re.compile(r"^/dev-tools(/|$)", re.IGNORECASE)),
]


def _redact_match(match: str) -> str:
    if len(match) <= 8:
        return "*" * len(match)
    return match[:4] + "…" + match[-4:]


def _check_exposed_creds(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for page in pages or []:
        body_blob_parts: list[str] = []
        text = page.get("text") or ""
        if text:
            body_blob_parts.append(text)
        for link in page.get("links") or []:
            href = link.get("href") or ""
            label = link.get("text") or ""
            if href:
                body_blob_parts.append(f"{label} -> {href}")
        body_blob = " ".join(body_blob_parts)
        path = page.get("path") or page.get("url") or "(unknown page)"
        for label, pattern in _CRED_PATTERNS:
            for hit in pattern.finditer(body_blob):
                value = hit.group(0)
                key = (label, value)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                findings.append(
                    {
                        "severity": "critical",
                        "title": f"{label} appears to be exposed in your live HTML",
                        "what_we_saw": (
                            f"While reading the rendered HTML for {path} we "
                            f"matched the pattern of a {label}. Sample "
                            f"(redacted): {_redact_match(value)}."
                        ),
                        "why_it_matters": (
                            "A real key in the public HTML can be copied by "
                            "anyone who views the page. If this matches a "
                            "real production key, rotate it immediately and "
                            "audit the affected service for unexpected use."
                        ),
                        "fix_prompt": (
                            f"Search the project for the exposed {label} "
                            "value and remove it from any client-side code, "
                            "HTML, or config that ships to the browser. Move "
                            "it to a server-side environment variable. After "
                            "removing, rotate the key in the issuing service "
                            "(AWS / Google / Stripe / etc.) so the leaked "
                            "value is no longer valid. Then redeploy and "
                            "verify the live URL no longer contains the "
                            "value."
                        ),
                        "category": CATEGORY_ID,
                        "tagged_by_persona": SNOOP_PERSONA,
                        "tag": SNOOP_TAG,
                        "check_id": "exposed_credentials",
                        "evidence_path": path,
                    }
                )
        for label, pattern in _LEAKY_LINK_PATTERNS:
            for link in page.get("links") or []:
                href = (link.get("href") or "").strip()
                if href and pattern.search(href):
                    key = (label, href)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    findings.append(
                        {
                            "severity": "high",
                            "title": (
                                "Public link to "
                                f"{label} visible on your site"
                            ),
                            "what_we_saw": (
                                f"On {path}, the rendered HTML contains a "
                                f"link with href {href!r} which matches a "
                                f"{label} pattern."
                            ),
                            "why_it_matters": (
                                "Anyone with your URL can follow the link. "
                                "If it lands on a live admin panel, debug "
                                "page, or a leaked .env / .git directory, "
                                "the next step for a curious visitor is to "
                                "see what's there."
                            ),
                            "fix_prompt": (
                                f"Remove the public link to {href!r} from "
                                "the live site. If the underlying route is a "
                                "real admin / debug / dev surface, gate it "
                                "behind authentication or an environment "
                                "guard so it does not respond on the "
                                "production URL. If the route is a stale "
                                "deployment artifact (.env, .git), delete "
                                "the file from the deploy and confirm the "
                                "URL returns 404 in production."
                            ),
                            "category": CATEGORY_ID,
                            "tagged_by_persona": SNOOP_PERSONA,
                            "tag": SNOOP_TAG,
                            "check_id": "exposed_paths",
                            "evidence_path": path,
                        }
                    )
    return findings


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_security_lite(
    *,
    base_url: str,
    pages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run all five Snoop checks. Always returns a dict; never raises.

    Returns::

        {
          "findings": [<finding>, ...],   # may be empty
          "passed_check_ids": [<str>, ...],   # checks that found nothing
          "failed_check_ids": [<str>, ...],
        }

    Callers should merge ``findings`` into the LLM findings list and use
    ``passed_check_ids`` to decide whether the report's "What's working"
    section can mention the security-lite category as passing.
    """
    headers, _status = _fetch_response_headers(base_url)

    header_checks = [
        ("hsts", _check_hsts(base_url, headers)),
        ("csp", _check_csp(headers)),
        ("x_frame_options", _check_xfo(headers)),
        ("x_content_type_options", _check_xcto(headers)),
    ]

    findings: list[dict[str, Any]] = []
    failed_ids: list[str] = []
    passed_ids: list[str] = []
    for check_id, finding in header_checks:
        if finding is None:
            passed_ids.append(check_id)
        else:
            failed_ids.append(check_id)
            findings.append(finding)

    cred_findings = _check_exposed_creds(pages or [])
    if cred_findings:
        failed_ids.append("exposed_credentials_or_paths")
        findings.extend(cred_findings)
    else:
        passed_ids.append("exposed_credentials_or_paths")

    return {
        "findings": findings,
        "passed_check_ids": passed_ids,
        "failed_check_ids": failed_ids,
    }


__all__ = [
    "CATEGORY_ID",
    "SNOOP_PERSONA",
    "SNOOP_TAG",
    "run_security_lite",
]
