"""Trust and sharing checks from rendered page meta (non-technical wording)."""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urljoin, urlparse

CATEGORY_ID = "trust_gaps"
PERSONA = "The Skeptic"
PERSONA_TAG = "Caught by The Skeptic"

USER_AGENT = "Mozilla/5.0 (LaunchLook AI Audit; +https://launchlook.app)"
_OG_IMAGE_TIMEOUT = 8


def _homepage(pages: list[dict[str, Any]]) -> dict[str, Any] | None:
    for p in pages or []:
        if (p.get("path") or "/") == "/" and isinstance(p.get("status"), int):
            if 200 <= p["status"] < 400:
                return p
    for p in pages or []:
        if isinstance(p.get("status"), int) and 200 <= p["status"] < 400:
            return p
    return None


def _check_viewport(home: dict[str, Any]) -> dict[str, Any] | None:
    meta = home.get("meta") or {}
    viewport = meta.get("viewport") or ""
    if viewport.strip():
        return None
    return {
        "severity": "high",
        "title": "Your site may not fit phone screens correctly",
        "what_we_saw": (
            "The homepage is missing the standard mobile viewport setting. On many "
            "phones the page will zoom out and look tiny instead of filling the screen."
        ),
        "why_it_matters": (
            "Most vibe-coded traffic is on phones. If the layout looks like a "
            "shrunken desktop site, people bounce before they tap Sign up."
        ),
        "fix_prompt": (
            "Add a mobile viewport tag on your main layout (in Lovable: Project Settings "
            "or the main page head; in Bolt/Webflow: site or page settings). Typical value: "
            "width=device-width, initial-scale=1. Republish after saving."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": PERSONA,
        "tag": PERSONA_TAG,
        "check_id": "missing_viewport",
    }


def _check_meta_description(home: dict[str, Any]) -> dict[str, Any] | None:
    meta = home.get("meta") or {}
    desc = (meta.get("description") or "").strip()
    if len(desc) >= 40:
        return None
    return {
        "severity": "medium",
        "title": "Google and social previews may look empty or generic",
        "what_we_saw": (
            "The homepage meta description is missing or very short "
            f"({len(desc)} characters). When someone shares your link in Slack, "
            "iMessage, or Google, they may see blank or boilerplate text."
        ),
        "why_it_matters": (
            "Before launch, shared links are how you get beta users and Product Hunt "
            "traffic. A blank preview looks like an unfinished side project."
        ),
        "fix_prompt": (
            "Write a plain 1–2 sentence description of what your app does and add it "
            "as the page meta description (SEO settings in Lovable, Bolt, or Webflow). "
            "Aim for roughly 120–160 characters."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": PERSONA,
        "tag": PERSONA_TAG,
        "check_id": "thin_meta_description",
    }


def _og_image_url(meta: dict[str, str], base_url: str) -> str | None:
    for key in ("og:image", "og:image:url", "twitter:image"):
        raw = (meta.get(key) or "").strip()
        if raw:
            return urljoin(base_url, raw)
    return None


def _probe_image(url: str) -> bool:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_OG_IMAGE_TIMEOUT) as resp:
            return 200 <= resp.status < 400
    except urllib.error.HTTPError as exc:
        return 200 <= exc.code < 400
    except Exception:  # noqa: BLE001
        return False


def _check_og_image(home: dict[str, Any], base_url: str) -> dict[str, Any] | None:
    meta = home.get("meta") or {}
    img_url = _og_image_url(meta, base_url)
    if not img_url:
        return {
            "severity": "medium",
            "title": "Link previews may show no image when you share the app",
            "what_we_saw": (
                "The homepage does not declare a share image (Open Graph image). "
                "When you paste your URL in Slack, Discord, or Twitter, the preview "
                "card may show no picture."
            ),
            "why_it_matters": (
                "A real screenshot or logo in the preview makes the app look "
                "trustworthy. Missing images hurt clicks from friends and launch posts."
            ),
            "fix_prompt": (
                "Add a share image in your site SEO/social settings (often called "
                "Open Graph image or social preview). Use a 1200×630 PNG or JPG of "
                "your product. Republish, then re-paste the link in Slack to verify."
            ),
            "category": CATEGORY_ID,
            "tagged_by_persona": PERSONA,
            "tag": PERSONA_TAG,
            "check_id": "missing_og_image",
        }
    if _probe_image(img_url):
        return None
    return {
        "severity": "medium",
        "title": "Your share preview image link is broken",
        "what_we_saw": (
            f"The site points to a preview image at {img_url}, but that image "
            "did not load when we checked (missing file or wrong URL)."
        ),
        "why_it_matters": (
            "Shared links will look broken or generic exactly when you're trying "
            "to impress beta users or launch day traffic."
        ),
        "fix_prompt": (
            "Upload the image to your host or CDN, update the Open Graph image URL "
            "in SEO settings to the working link, and republish."
        ),
        "category": CATEGORY_ID,
        "tagged_by_persona": PERSONA,
        "tag": PERSONA_TAG,
        "check_id": "broken_og_image",
    }


def run_trust_seo_lite(
    *,
    base_url: str,
    pages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run trust/sharing meta checks. Never raises."""
    findings: list[dict[str, Any]] = []
    failed: list[str] = []
    passed: list[str] = []

    home = _homepage(pages or [])

    checks = [
        ("missing_viewport", lambda: _check_viewport(home) if home else None),
        ("thin_meta_description", lambda: _check_meta_description(home) if home else None),
        ("og_image", lambda: _check_og_image(home, base_url) if home else None),
    ]

    try:
        for check_id, fn in checks:
            finding = fn()
            if finding is None:
                passed.append(check_id)
            else:
                cid = finding.get("check_id") or check_id
                failed.append(cid)
                findings.append(finding)
    except Exception as exc:  # noqa: BLE001
        print(f"[trust-seo] WARN: {exc}", file=sys.stderr)

    # Avoid crowding the report — keep the most important trust/sharing items.
    _rank = {"high": 3, "medium": 2, "low": 1}
    findings.sort(key=lambda f: _rank.get((f.get("severity") or "").lower(), 0), reverse=True)
    findings = findings[:2]

    return {
        "findings": findings,
        "passed_check_ids": passed,
        "failed_check_ids": failed,
    }


__all__ = ["CATEGORY_ID", "run_trust_seo_lite"]
