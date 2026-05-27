"""sanitize_for_public.py: strip customer PII before publishing a report JSON.

Used by ``scripts/deliver_report.py::_generate_shareable_page`` and by
``scripts/share_report.py``. The public ``landing/data/reports/{slug}.json``
file should never contain anything a stranger embedding the badge could turn
into a privacy leak.

What gets stripped (per docs/SIMPLICITY-GUARDRAILS.md sections 1, 3, 5):

* ``customer.email`` -- the audit buyer's address
* ``customer.notion_row_id`` -- internal CRM key
* ``customer.url_redacted`` -- internal-only flag
* ``customer.app_url`` -- the live URL (only kept when ``is_public`` is
  true AND the customer explicitly opted in; the default is to strip)
* Anything under ``customer.*`` not on the public allow-list
* Any ``screenshot_*`` field on a finding -- screenshots may contain real
  data, real names, dev tooling, etc.
* The customer's domain anywhere in finding text -- replaced with
  generic copy ("your homepage", "your checkout") so a public report
  never leaks the customer's staging URL by accident.

What is kept on the public surface:

* ``customer.first_name`` (optional; can be stripped if customer asks)
* ``customer.app_name`` -- already in the verdict / share metadata
* ``customer.builder`` -- helpful context for visitors
* ``customer.platform`` -- needed for Webflow vs vibe-coder styling
* ``customer.tier`` -- needed for the validity banner
* ``verdict.*`` -- the headline and narrative
* ``passed_checks`` -- what worked
* ``findings`` -- with URLs / emails / screenshots scrubbed
* ``share_metadata`` -- title / description / og_image for OG scrapers

This module is import-safe (no I/O, no network) so it can be unit-tested
without setting up a customer YAML.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Public allow-lists
# ---------------------------------------------------------------------------

# Keys under ``customer`` that may appear on the public page.
# Anything not on this list is dropped during sanitization, on purpose.
PUBLIC_CUSTOMER_KEYS: frozenset[str] = frozenset(
    {
        "first_name",
        "app_name",
        "tier",
        "builder",
        "platform",
    }
)

# Keys on a finding that may appear on the public page.
PUBLIC_FINDING_KEYS: frozenset[str] = frozenset(
    {
        "title",
        "severity",
        "category",
        "tag",
        "what_we_saw",
        "why_it_matters",
        "fix_prompt",
    }
)

# Generic replacements for customer-URL leakage. The map keys are the
# heuristic substrings we look for in finding text; values are the
# replacement words a stranger reading the public page should see.
GENERIC_PATH_REPLACEMENTS: dict[str, str] = {
    "/auth": "the sign-in page",
    "/login": "the sign-in page",
    "/signin": "the sign-in page",
    "/sign-in": "the sign-in page",
    "/admin": "the admin route",
    "/checkout": "the checkout flow",
    "/pricing": "the pricing page",
    "/privacy": "the privacy page",
    "/terms": "the terms page",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _host_from_url(url: str) -> str:
    """Return the bare host (no scheme, no trailing slash, no path) for a URL.

    Empty strings and obviously malformed inputs return ``""`` so the
    caller can skip URL stripping when there is nothing to strip.
    """
    if not url:
        return ""
    cleaned = url.strip()
    if not cleaned:
        return ""
    if "://" not in cleaned:
        cleaned = "http://" + cleaned
    try:
        parsed = urlparse(cleaned)
    except (ValueError, TypeError):
        return ""
    host = (parsed.netloc or "").lower()
    return host


def _email_pattern() -> re.Pattern[str]:
    # Local-part + @ + domain. Conservative; we only strip obvious emails.
    return re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _scrub_text(text: str, customer_host: str) -> str:
    """Strip customer host + raw email addresses from a string.

    The substitution is deliberately blunt:
      * ``https://customer-host`` / ``http://customer-host`` -> "your site"
      * Bare ``customer-host`` -> "your site"
      * Any email address -> "[email redacted]"

    The point is to make sure no customer-specific URL or address ends
    up on the public report. False positives here are acceptable; false
    negatives (a leaked URL) are not.
    """
    if not text:
        return text

    out = text

    if customer_host:
        host = re.escape(customer_host)
        # https://host or http://host (with optional path)
        out = re.sub(rf"https?://{host}(/[^\s)\"']*)?", "your site", out, flags=re.IGNORECASE)
        # Bare host appearance (word boundary on left)
        out = re.sub(rf"(?<![A-Za-z0-9.-]){host}\b", "your site", out, flags=re.IGNORECASE)

    out = _email_pattern().sub("[email redacted]", out)
    return out


def _strip_obvious_paths(text: str) -> str:
    """Replace specific URL paths (``/auth``, ``/admin``, ...) with generic phrases.

    Findings often say "On /auth, the dev bypass button..." which is
    fine on the private surface but reveals the customer's site
    structure to strangers. We translate the most common paths into
    plain-English phrasing.

    Only applied when the path appears wrapped in whitespace or
    punctuation so we don't munge legitimate prose that contains the
    same letters.
    """
    if not text:
        return text
    out = text
    for path, phrase in GENERIC_PATH_REPLACEMENTS.items():
        out = re.sub(rf"(?<![A-Za-z0-9]){re.escape(path)}\b", phrase, out)
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sanitize_finding(finding: dict[str, Any], customer_url: str) -> dict[str, Any]:
    """Return a sanitized copy of a finding.

    * Drops any key not in ``PUBLIC_FINDING_KEYS`` (so internal fields
      such as ``screenshot_path``, ``screenshot_caption``, ``notes``,
      ``fingerprint``, ``internal_notes`` never reach the public file).
    * Scrubs the customer's URL out of every kept text field.
    * Replaces common path names (``/admin`` etc.) with generic phrases.
    """
    if not isinstance(finding, dict):
        return {}

    host = _host_from_url(customer_url)
    clean: dict[str, Any] = {}
    for key in PUBLIC_FINDING_KEYS:
        if key not in finding:
            continue
        value = finding[key]
        if isinstance(value, str):
            value = _scrub_text(value, host)
            value = _strip_obvious_paths(value)
        clean[key] = value
    return clean


def sanitize_customer(customer: dict[str, Any]) -> dict[str, Any]:
    """Return a sanitized copy of the customer block.

    Only fields in ``PUBLIC_CUSTOMER_KEYS`` are kept. Everything else
    (email, notion_row_id, app_url, internal_notes, ...) is dropped.
    """
    if not isinstance(customer, dict):
        return {}
    return {key: customer[key] for key in PUBLIC_CUSTOMER_KEYS if key in customer}


def sanitize_verdict(verdict: dict[str, Any], customer_url: str) -> dict[str, Any]:
    if not isinstance(verdict, dict):
        return {}
    host = _host_from_url(customer_url)
    out: dict[str, Any] = {}
    for key in ("label", "summary", "narrative", "emoji"):
        if key not in verdict:
            continue
        value = verdict[key]
        if isinstance(value, str):
            value = _scrub_text(value, host)
            value = _strip_obvious_paths(value)
        out[key] = value
    return out


def sanitize_report_json(report: dict[str, Any], customer: dict[str, Any]) -> dict[str, Any]:
    """Top-level sanitizer. Returns the public-safe report dict.

    The input ``report`` is the full delivery-time dict (verdict +
    findings + share_metadata etc.) and ``customer`` is the raw
    customer block from the YAML (with email, app_url, and so on).

    Output is suitable to JSON-dump straight into
    ``landing/data/reports/{slug}.json``.
    """
    if not isinstance(report, dict):
        return {}
    customer = customer or {}
    customer_url = customer.get("app_url") or report.get("customer_url") or ""

    findings_in = report.get("findings") or []
    findings_out = [sanitize_finding(f, customer_url) for f in findings_in if isinstance(f, dict)]

    out: dict[str, Any] = {
        "customer_slug": report.get("customer_slug", ""),
        "is_public": bool(report.get("is_public", False)),
        "tier": report.get("tier", customer.get("tier", "")),
        "audit_date": report.get("audit_date", ""),
        "app_name": report.get("app_name", customer.get("app_name", "")),
        "customer": sanitize_customer(customer),
        "verdict": sanitize_verdict(report.get("verdict") or {}, customer_url),
        "passed_checks": list(report.get("passed_checks") or []),
        "findings": findings_out,
        "share_metadata": dict(report.get("share_metadata") or {}),
        "handoff_report": {
            "available": bool((report.get("handoff_report") or {}).get("available", False)),
            "shared": bool((report.get("handoff_report") or {}).get("shared", False)),
        },
    }
    return out
