"""Check internal links from crawled pages for obvious 404s."""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urljoin, urlparse

CATEGORY_ID = "broken_ctas_links"
PERSONA = "The Klutz"
PERSONA_TAG = "Caught by The Klutz"

USER_AGENT = "Mozilla/5.0 (LaunchLook AI Audit; +https://launchlook.app)"
_MAX_LINKS_TO_PROBE = 24
_TIMEOUT_SEC = 8

# Link text hints we care about (nav, footer, primary CTAs)
_IMPORTANT_TEXT_RE = (
    "home",
    "pricing",
    "price",
    "about",
    "contact",
    "login",
    "log in",
    "sign",
    "start",
    "demo",
    "faq",
    "help",
    "privacy",
    "terms",
    "blog",
    "features",
    "get",
    "try",
    "book",
)


def _same_site(base: str, href: str) -> bool:
    base_p = urlparse(base)
    joined = urljoin(base, href)
    target = urlparse(joined)
    if not target.scheme.startswith("http"):
        return False
    if target.netloc and target.netloc != base_p.netloc:
        return False
    return True


def _probe_url(url: str) -> int | None:
    """Return HTTP status or None on network failure."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:  # noqa: BLE001
        # Some hosts block HEAD — try GET with range
        try:
            req_get = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"},
            )
            with urllib.request.urlopen(req_get, timeout=_TIMEOUT_SEC) as resp:
                return resp.status
        except urllib.error.HTTPError as exc:
            return exc.code
        except Exception:  # noqa: BLE001
            return None


def _collect_candidates(pages: list[dict[str, Any]], base_url: str) -> list[dict[str, str]]:
    """Gather unique internal links, homepage first."""
    ordered_pages = sorted(
        pages,
        key=lambda p: (0 if (p.get("path") or "/") == "/" else 1),
    )
    seen_href: set[str] = set()
    out: list[dict[str, str]] = []

    for page in ordered_pages:
        if not isinstance(page.get("status"), int) or not (200 <= page["status"] < 400):
            continue
        for link in page.get("links") or []:
            href = (link.get("href") or "").strip()
            text = (link.get("text") or "").strip()
            if not href or not _same_site(base_url, href):
                continue
            full = urljoin(base_url, href)
            if full in seen_href:
                continue
            seen_href.add(full)
            out.append({"text": text or "(link)", "href": href, "url": full})
            if len(out) >= _MAX_LINKS_TO_PROBE:
                return out
    return out


def _prioritize_broken(
    broken: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def score(item: dict[str, Any]) -> int:
        text = (item.get("text") or "").lower()
        if any(k in text for k in _IMPORTANT_TEXT_RE):
            return 0
        return 1

    return sorted(broken, key=score)[:5]


def _build_finding(
    broken: list[dict[str, Any]], *, platform: str = "generic"
) -> dict[str, Any] | None:
    if not broken:
        return None
    shown = _prioritize_broken(broken)
    lines = [
        f'"{b["text"]}" points to {b["href"]} (page not found — error {b["status"]})' for b in shown
    ]
    extra = len(broken) - len(shown)
    if extra > 0:
        lines.append(f"…and {extra} more dead link(s) on the site.")

    platform_hint = {
        "lovable": (
            "In Lovable, find each broken path in Pages or routing settings and "
            "either create the missing page or update the link to the correct URL. "
            "Republish when done."
        ),
        "bolt": ("In Bolt, fix each href so it matches a real route or page, then redeploy."),
        "webflow": (
            "In Webflow Designer, select each nav/footer link and point it to an "
            "existing page or a valid external URL, then publish."
        ),
    }.get(
        (platform or "generic").lower(),
        (
            "Update each menu, footer, or button link so it goes to a page that actually "
            "exists on your live site. Test by clicking every item in the main navigation."
        ),
    )

    count = len(broken)
    title = (
        f"{count} links on your site go to missing pages"
        if count > 1
        else "A link on your site goes to a missing page"
    )

    return {
        "severity": "high" if count >= 2 else "medium",
        "title": title,
        "what_we_saw": (
            "We followed links on your live site and these led to a 'page not found' "
            "error:\n" + "\n".join(f"- {line}" for line in lines)
        ),
        "why_it_matters": (
            "People who click Pricing, Sign up, or footer links and hit a dead end "
            "usually leave. It also looks unfinished to investors or Product Hunt visitors."
        ),
        "fix_prompt": platform_hint,
        "category": CATEGORY_ID,
        "tagged_by_persona": PERSONA,
        "tag": PERSONA_TAG,
        "check_id": "broken_internal_links",
    }


def run_broken_links_lite(
    *,
    base_url: str,
    pages: list[dict[str, Any]] | None = None,
    platform: str = "generic",
) -> dict[str, Any]:
    """Probe internal links from HTML extract output. Never raises."""
    findings: list[dict[str, Any]] = []
    failed: list[str] = []
    passed: list[str] = []

    try:
        candidates = _collect_candidates(pages or [], base_url)
        broken: list[dict[str, Any]] = []
        for cand in candidates:
            status = _probe_url(cand["url"])
            if status == 404:
                broken.append({**cand, "status": status})
            elif status is not None:
                print(f"  [links] OK {cand['href']} -> {status}")
            if status == 404:
                print(f"  [links] 404 {cand['text']} -> {cand['href']}")

        finding = _build_finding(broken, platform=platform)
        if finding:
            findings.append(finding)
            failed.append("broken_internal_links")
        else:
            passed.append("broken_internal_links")
    except Exception as exc:  # noqa: BLE001
        print(f"[broken-links] WARN: {exc}", file=sys.stderr)
        passed.append("broken_internal_links")

    return {
        "findings": findings,
        "passed_check_ids": passed,
        "failed_check_ids": failed,
    }


__all__ = ["CATEGORY_ID", "run_broken_links_lite"]
