"""Unsubscribe-link checker for the form-smoke email round-trip.

After the disposable mailbox receives a confirmation email (Pro tier,
form_smoke_test.py), this module:

1. Extracts candidate unsubscribe URLs from the email HTML and plain-text
   body.  Covers the four common patterns:
     a. Anchor text contains "unsubscribe" or "opt out".
     b. href contains "unsubscribe", "optout", or "opt-out".
     c. Bare URL in plain text within 120 chars of "unsubscribe"/"opt out".
     d. RFC 2369 List-Unsubscribe header URL (if passed in ``headers``).

2. GETs each candidate URL and records the HTTP status code.

3. Returns a result dict that form_smoke_test.py translates into a finding:
     - No unsubscribe link found in the email   → medium finding
     - Unsubscribe link found but returns 4xx/5xx → high finding
     - Unsubscribe link found and returns 2xx/3xx → passed check

Per SIMPLICITY-GUARDRAILS §6 none of the internal terms ("List-Unsubscribe",
"round-trip", "RFC 2369") appear on customer surfaces.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from typing import Any

_USER_AGENT = "Mozilla/5.0 (LaunchLook AI Audit; +https://launchlook.app)"
_GET_TIMEOUT_SEC = 10

# ---------------------------------------------------------------------------
# Link extraction
# ---------------------------------------------------------------------------

# Matches <a href="..."> tags; captures href and inner text separately.
_ANCHOR_RE = re.compile(
    r'<a\s[^>]*href=["\']([^"\'>\s]+)["\'][^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)

# Tokens in anchor text or href that signal an unsubscribe link.
_UNSUB_TEXT_TOKENS = ("unsubscribe", "opt out", "opt-out", "remove me")
_UNSUB_HREF_TOKENS = ("unsubscribe", "optout", "opt-out", "opt_out", "remove")

# Bare URL pattern for plain-text bodies.
_URL_RE = re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE)


def extract_unsubscribe_links(
    html: str,
    text: str = "",
    list_unsubscribe_header: str = "",
) -> list[str]:
    """Return a de-duplicated list of candidate unsubscribe URLs.

    Searches ``html`` first (anchor text + href), then ``text`` (bare URLs
    near the word "unsubscribe"), then ``list_unsubscribe_header`` (RFC 2369).
    """
    seen: set[str] = set()
    results: list[str] = []

    def _add(url: str) -> None:
        url = url.strip().rstrip(".,;)")
        if url and url not in seen:
            seen.add(url)
            results.append(url)

    # --- HTML anchors ---
    for href, inner in _ANCHOR_RE.findall(html or ""):
        inner_lower = re.sub(r"<[^>]+>", "", inner).lower().strip()
        href_lower = href.lower()
        if any(t in inner_lower for t in _UNSUB_TEXT_TOKENS) or any(
            t in href_lower for t in _UNSUB_HREF_TOKENS
        ):
            _add(href)

    # --- Plain-text bare URLs near "unsubscribe" / "opt out" ---
    plain = text or ""
    for m in _URL_RE.finditer(plain):
        url = m.group(0)
        start = max(0, m.start() - 120)
        end = min(len(plain), m.end() + 120)
        context = plain[start:end].lower()
        if any(t in context for t in _UNSUB_TEXT_TOKENS):
            _add(url)

    # --- RFC 2369 List-Unsubscribe header ---
    # Format: <https://example.com/unsubscribe>, <mailto:...>
    for m in re.finditer(r"<(https?://[^>]+)>", list_unsubscribe_header or ""):
        _add(m.group(1))

    return results


# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------


def check_unsubscribe_url(url: str, *, timeout: int = _GET_TIMEOUT_SEC) -> int | None:
    """GET ``url`` and return the HTTP status code, or None on network error."""
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": _USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_unsubscribe_check(
    html: str,
    text: str = "",
    list_unsubscribe_header: str = "",
) -> dict[str, Any]:
    """Check whether the email contains a working unsubscribe link.

    Returns::

        {
          "found": bool,          # at least one candidate URL extracted
          "working": bool | None, # True = 2xx/3xx, False = 4xx/5xx, None = not found
          "url": str | None,      # first candidate checked
          "status": int | None,   # HTTP status of first candidate
          "all_urls": list[str],  # all candidates found
        }
    """
    candidates = extract_unsubscribe_links(html, text, list_unsubscribe_header)

    if not candidates:
        return {
            "found": False,
            "working": None,
            "url": None,
            "status": None,
            "all_urls": [],
        }

    # Check the first candidate; that's what a real user would click.
    first = candidates[0]
    status = check_unsubscribe_url(first)
    working = (status is not None) and (status < 400)

    return {
        "found": True,
        "working": working,
        "url": first,
        "status": status,
        "all_urls": candidates,
    }


__all__ = [
    "extract_unsubscribe_links",
    "check_unsubscribe_url",
    "run_unsubscribe_check",
]
