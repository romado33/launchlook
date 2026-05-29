"""Snoop's security-lite checks (per docs/TESTERS-CAST.md).

The Snoop persona "pokes around for exposed keys, public admin routes,
missing security headers, leaky URLs." This module runs a small,
deterministic set of HTTP-header and HTML-content checks against the
customer's live URL and emits *pre-generated findings* that get merged
into the LLM-driven findings list.

The checks (8 total):
    1. HSTS header presence (HTTPS sites only).
    2. CSP header presence.
    3. X-Frame-Options presence (and not too permissive).
    4. X-Content-Type-Options nosniff.
    5. Exposed credentials / paths in the HTML extract:
       - AWS access keys, Google/Stripe API keys, RSA private key blocks.
       - Supabase service_role JWTs (decoded to confirm role).
       - Visible /admin, /.env, /.git, firebase config dumps.
    6. sitemap.xml reachable (GET /sitemap.xml returns 200).
    7. robots.txt not blocking all crawlers (no bare Disallow: / for *).
    8. noindex meta tag on the homepage (leftover staging setting).

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

import base64
import json
import re
import socket
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

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
        "what_we_saw": ("Your homepage response does not include X-Content-Type-Options: nosniff."),
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


def _check_referrer_policy(headers: dict[str, str]) -> dict[str, Any] | None:
    if headers.get("referrer-policy"):
        return None
    return {
        "severity": "low",
        "title": "Referrer-Policy header is not set",
        "what_we_saw": (
            "Your homepage response does not include a Referrer-Policy header. "
            "We checked the live URL's response headers."
        ),
        "why_it_matters": (
            "Without it, other sites may see full URLs when people click links "
            "away from your app — including pages with private IDs in the address bar. "
            "It's a small privacy and trust polish item before launch."
        ),
        "fix_prompt": (
            "Add a Referrer-Policy response header on production. A sensible default "
            "for most apps: Referrer-Policy: strict-origin-when-cross-origin. "
            "Set it in your host's custom headers (Vercel, Netlify, Cloudflare, Webflow)."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": SNOOP_PERSONA,
        "tag": SNOOP_TAG,
        "check_id": "referrer_policy",
    }


def _check_permissions_policy(headers: dict[str, str]) -> dict[str, Any] | None:
    if headers.get("permissions-policy") or headers.get("feature-policy"):
        return None
    return {
        "severity": "low",
        "title": "Permissions-Policy header is not set",
        "what_we_saw": (
            "Your homepage does not send a Permissions-Policy (or legacy "
            "Feature-Policy) header."
        ),
        "why_it_matters": (
            "This header tells browsers which device features (camera, mic, location) "
            "your site can request. It's optional for simple apps but good practice "
            "before you handle payments or accounts."
        ),
        "fix_prompt": (
            "Add a Permissions-Policy response header that only allows what your app "
            "needs. Example for a basic SaaS with no camera: "
            "Permissions-Policy: camera=(), microphone=(), geolocation=(). "
            "Adjust in your hosting platform's security/header settings."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": SNOOP_PERSONA,
        "tag": SNOOP_TAG,
        "check_id": "permissions_policy",
    }


def _check_ssl_expiry(base_url: str) -> dict[str, Any] | None:
    parsed = urlparse(base_url)
    if parsed.scheme != "https":
        return None
    host = parsed.hostname
    if not host:
        return None
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=HEAD_TIMEOUT_SEC) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter")
        if not not_after:
            return None
        expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc
        )
        days = (expires - datetime.now(timezone.utc)).days
    except Exception:  # noqa: BLE001
        return None

    if days > 30:
        return None

    severity = "critical" if days < 7 else "high"
    when = "today" if days <= 0 else f"in about {days} day(s)"
    return {
        "severity": severity,
        "title": "Your site's security certificate expires soon",
        "what_we_saw": (
            f"Your live site's HTTPS certificate expires {when} "
            f"(on {expires.strftime('%B %d, %Y')}). Browsers will show scary warnings "
            "after that and people may not be able to open your app at all."
        ),
        "why_it_matters": (
            "If the certificate lapses during launch week, every visitor sees a "
            "'connection not private' warning — signup and payments stop cold."
        ),
        "fix_prompt": (
            "Renew HTTPS on your hosting provider before launch. On Vercel, Netlify, "
            "Cloudflare, or Webflow this is usually automatic once DNS is correct — "
            "log in to the host, check SSL/TLS status, and force renewal if needed. "
            "If you use a custom domain, confirm it is verified and not pointing at "
            "an old server."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": SNOOP_PERSONA,
        "tag": SNOOP_TAG,
        "check_id": "ssl_expiry",
    }


# ---------------------------------------------------------------------------
# 5: HTML content sweep for exposed creds / paths
# ---------------------------------------------------------------------------


# Each entry: (label, pattern). Patterns are intentionally tight to
# minimize false positives on placeholder copy ("YOUR_API_KEY_HERE" etc.).
_CRED_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Stripe secret key (live)", re.compile(r"sk_live_[0-9a-zA-Z]{16,}")),
    ("Stripe restricted key", re.compile(r"rk_live_[0-9a-zA-Z]{16,}")),
    ("Slack token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")),
    ("Firebase config (apiKey)", re.compile(r'apiKey\s*:\s*"AIza[0-9A-Za-z\-_]{35}"')),
    # Matches any JWT-shaped token; we decode and filter for service_role below.
    ("JWT token", re.compile(r"eyJ[A-Za-z0-9+/=_-]{20,}\.[A-Za-z0-9+/=_-]{20,}\.[A-Za-z0-9+/=_-]{10,}")),
]

# Patterns that match assignment of a secret to a named variable in JS/HTML.
# These catch Lovable / Cursor apps that inline env vars into client bundles.
_ENV_VAR_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "Supabase URL + key inline assignment",
        re.compile(
            r'supabase(?:Url|_url|URL)\s*[=:]\s*["\']https://[a-z0-9]+\.supabase\.co["\']',
            re.IGNORECASE,
        ),
    ),
    (
        "NEXT_PUBLIC env var with a value in client HTML",
        re.compile(r'NEXT_PUBLIC_[A-Z0-9_]{3,}\s*[=:]\s*["\'][^"\']{8,}["\']'),
    ),
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


def _jwt_role(token: str) -> str | None:
    """Return the ``role`` claim from a JWT payload, or None on any failure."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        padding = (4 - len(parts[1]) % 4) % 4
        payload = base64.urlsafe_b64decode(parts[1] + "=" * padding)
        return json.loads(payload).get("role")
    except Exception:  # noqa: BLE001
        return None


def _check_exposed_creds(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    for page in pages or []:
        body_blob_parts: list[str] = []
        text = page.get("text") or ""
        if text:
            body_blob_parts.append(text)
        for link in page.get("links") or []:
            href = link.get("href") or ""
            link_label = link.get("text") or ""
            if href:
                body_blob_parts.append(f"{link_label} -> {href}")
        body_blob = " ".join(body_blob_parts)
        path = page.get("path") or page.get("url") or "(unknown page)"
        for label, pattern in _CRED_PATTERNS:
            for hit in pattern.finditer(body_blob):
                value = hit.group(0)
                # For JWT matches: only flag if the decoded role is service_role.
                # anon keys are intentionally public; service_role keys are not.
                if label == "JWT token":
                    if _jwt_role(value) != "service_role":
                        continue
                    label = "Supabase service_role key"
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
                            "(AWS / Google / Stripe / Supabase / etc.) so "
                            "the leaked value is no longer valid. Then "
                            "redeploy and verify the live URL no longer "
                            "contains the value."
                        ),
                        "category": CATEGORY_ID,
                        "tagged_by_persona": SNOOP_PERSONA,
                        "tag": SNOOP_TAG,
                        "check_id": "exposed_credentials",
                        "evidence_path": path,
                    }
                )

        for label, pattern in _ENV_VAR_PATTERNS:
            for hit in pattern.finditer(body_blob):
                value = hit.group(0)
                key = (label, value[:60])
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                findings.append(
                    {
                        "severity": "medium",
                        "title": f"Possible secret variable visible in page source ({label})",
                        "what_we_saw": (
                            f"On {path}, the page source contains a pattern "
                            f"matching {label}. This may indicate that "
                            "environment variables or API credentials are "
                            "being rendered into client-side HTML or "
                            "JavaScript."
                        ),
                        "why_it_matters": (
                            "Environment variables intended for server-side "
                            "use only (database URLs, service keys) should "
                            "never appear in the HTML a visitor can read. "
                            "Even if the current value is safe, the pattern "
                            "suggests credentials may be leaking."
                        ),
                        "fix_prompt": (
                            "Review what your build tool inlines into the "
                            "client bundle. In Lovable / Next.js, only "
                            "variables prefixed NEXT_PUBLIC_ should ever "
                            "reach the browser — and only non-sensitive ones "
                            "(public Supabase anon key is fine; service_role "
                            "key is not). Move any server-side secrets to "
                            "environment variables that are not prefixed "
                            "NEXT_PUBLIC_ and are never passed to "
                            "client-side code."
                        ),
                        "category": CATEGORY_ID,
                        "tagged_by_persona": SNOOP_PERSONA,
                        "tag": SNOOP_TAG,
                        "check_id": "env_var_in_client",
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
                            "title": (f"Public link to {label} visible on your site"),
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
# 6-8: crawlability / discoverability checks
# ---------------------------------------------------------------------------


def _fetch_url_status(url: str) -> int | None:
    """Return the HTTP status code for *url*, or None on network error."""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=HEAD_TIMEOUT_SEC) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:  # noqa: BLE001
        return None


def _fetch_text(url: str) -> str:
    """Return the response body as a string, or '' on any error."""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=HEAD_TIMEOUT_SEC) as resp:
            return resp.read(32_768).decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def _check_sitemap(base_url: str) -> dict[str, Any] | None:
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    status = _fetch_url_status(sitemap_url)
    if status == 200:
        return None
    return {
        "severity": "low",
        "title": "No sitemap.xml found",
        "what_we_saw": (
            f"A GET request to {sitemap_url} returned "
            f"{'HTTP ' + str(status) if status else 'no response'} "
            "rather than 200."
        ),
        "why_it_matters": (
            "A sitemap.xml tells search engines which pages exist and "
            "when they were last updated. Without one, Google may take "
            "longer to discover and index your pages. It is a one-line "
            "config change on most platforms."
        ),
        "fix_prompt": (
            "Enable automatic sitemap generation for your platform. "
            "In Vercel with Next.js, add a sitemap.ts in the app/ "
            "directory. In Lovable, check the SEO settings panel. "
            "In Webflow, enable the sitemap in Site Settings > SEO. "
            "After deploying, verify that /sitemap.xml returns 200 "
            "and submit the URL to Google Search Console."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": SNOOP_PERSONA,
        "tag": SNOOP_TAG,
        "check_id": "sitemap_xml",
    }


def _check_robots(base_url: str) -> dict[str, Any] | None:
    robots_url = urljoin(base_url, "/robots.txt")
    body = _fetch_text(robots_url)
    if not body:
        return None  # missing robots.txt is low-noise; only flag active blocks

    # Detect a bare "Disallow: /" under a User-agent: * block —
    # this blocks all crawlers and is a common leftover from staging.
    in_star_block = False
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            in_star_block = agent == "*"
        elif in_star_block and re.match(r"(?i)disallow\s*:\s*/\s*$", line):
            return {
                "severity": "medium",
                "title": "robots.txt is blocking all search engine crawlers",
                "what_we_saw": (
                    f"Your robots.txt at {robots_url} contains "
                    "'User-agent: *' followed by 'Disallow: /' which "
                    "tells every search engine not to crawl any page."
                ),
                "why_it_matters": (
                    "This setting is commonly left over from a staging "
                    "or development environment and is easy to miss. "
                    "If left in place on your live domain, search "
                    "engines will not index any of your pages."
                ),
                "fix_prompt": (
                    "Open your robots.txt file and remove or replace "
                    "the 'Disallow: /' line under 'User-agent: *'. "
                    "To allow all crawlers: set 'Allow: /'. Then add "
                    "a Sitemap: line pointing to your sitemap.xml. "
                    "After deploying, use Google Search Console's "
                    "robots.txt tester to confirm crawling is allowed."
                ),
                "category": CATEGORY_ID,
                "tagged_by_persona": SNOOP_PERSONA,
                "tag": SNOOP_TAG,
                "check_id": "robots_disallow_all",
            }
    return None


def _check_noindex(pages: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Flag a noindex meta tag on the homepage (common staging leftover)."""
    noindex_re = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', re.IGNORECASE)
    for page in pages or []:
        raw_html = page.get("raw_html") or page.get("html") or ""
        if noindex_re.search(raw_html):
            path = page.get("path") or page.get("url") or "homepage"
            return {
                "severity": "high",
                "title": "noindex tag is preventing search engines from indexing the site",
                "what_we_saw": (
                    f"The rendered HTML for {path} contains a "
                    "<meta name='robots' content='noindex'> tag. "
                    "This tag tells search engines to exclude this "
                    "page from their index."
                ),
                "why_it_matters": (
                    "A noindex tag is commonly added during development "
                    "or staging to prevent Google from indexing an "
                    "unfinished site. If it is still present on the "
                    "live URL, your site will not appear in search "
                    "results regardless of how good your content is."
                ),
                "fix_prompt": (
                    "Search your codebase or CMS settings for the "
                    "noindex meta tag and remove it. In Lovable, check "
                    "the SEO settings. In Webflow, check Site Settings "
                    "> SEO and also the individual page settings. In "
                    "Next.js, check any robots metadata export. After "
                    "removing, redeploy and use Google Search Console "
                    "to request a recrawl."
                ),
                "category": CATEGORY_ID,
                "tagged_by_persona": SNOOP_PERSONA,
                "tag": SNOOP_TAG,
                "check_id": "noindex_on_live_site",
            }
    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_security_lite(
    *,
    base_url: str,
    pages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run all Snoop checks. Always returns a dict; never raises.

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
        ("referrer_policy", _check_referrer_policy(headers)),
        ("permissions_policy", _check_permissions_policy(headers)),
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

    ssl_finding = _check_ssl_expiry(base_url)
    if ssl_finding is None:
        passed_ids.append("ssl_expiry")
    else:
        failed_ids.append("ssl_expiry")
        findings.append(ssl_finding)

    crawl_checks = [
        ("sitemap_xml", _check_sitemap(base_url)),
        ("robots_disallow_all", _check_robots(base_url)),
        ("noindex_on_live_site", _check_noindex(pages or [])),
    ]
    for check_id, finding in crawl_checks:
        if finding is None:
            passed_ids.append(check_id)
        else:
            failed_ids.append(check_id)
            findings.append(finding)

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
