"""Capture browser console errors on key pages (plain-English findings).

Uses Playwright on the customer's homepage (and a few common paths if
they load). Surfaces up to one rolled-up finding so founders see
"background errors" without DevTools jargon.
"""

from __future__ import annotations

import re
import sys
from typing import Any
from urllib.parse import urljoin

from .html_extract import DEFAULT_PATHS, join_url

CATEGORY_ID = "broken_ctas_links"
PERSONA = "The Klutz"
PERSONA_TAG = "Caught by The Klutz"

# Paths worth probing beyond home (cap total page visits).
_EXTRA_PATHS = ("/login", "/sign-in", "/sign-up", "/auth")

_MAX_PAGES = 3
_MAX_ERRORS_PER_PAGE = 5
_MAX_MESSAGE_LEN = 160

# Benign noise common on vibe-coded hosts — skip for the report.
_NOISE_RE = re.compile(
    r"(?i)(favicon|chrome-extension|moz-extension|"
    r"ResizeObserver loop|Third-party cookie|"
    r"Failed to load resource.*favicon|"
    r"analytics\.|googletagmanager|facebook\.net|"
    r"sentry\.io|hotjar|clarity\.ms)"
)


def _normalize_message(msg: str) -> str:
    text = re.sub(r"\s+", " ", (msg or "").strip())
    if len(text) > _MAX_MESSAGE_LEN:
        text = text[: _MAX_MESSAGE_LEN - 1] + "…"
    return text


def _is_noise(message: str) -> bool:
    if not message:
        return True
    if _NOISE_RE.search(message):
        return True
    # Very short generic lines
    if len(message) < 12:
        return True
    return False


def _humanize_error_line(message: str) -> str:
    """Strip stack-file paths but keep the readable bit."""
    line = _normalize_message(message)
    # Drop "at https://..." tail if present
    line = re.sub(r"\s+at\s+https?://\S+", "", line).strip()
    # Avoid leading "Error:" duplication in lists
    line = re.sub(r"^(Error|TypeError|ReferenceError):\s*", "", line, flags=re.I)
    return line or _normalize_message(message)


def _paths_to_visit(base_url: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for p in ["/", *_EXTRA_PATHS, *DEFAULT_PATHS[1:4]]:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
        if len(ordered) >= _MAX_PAGES:
            break
    return ordered


def _collect_console_errors(base_url: str) -> list[dict[str, Any]]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    hits: list[dict[str, Any]] = []
    paths = _paths_to_visit(base_url)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (LaunchLook AI Audit; +https://launchlook.app)",
            )
            for path in paths:
                url = join_url(base_url, path)
                page = context.new_page()
                page_errors: list[str] = []

                def _on_console(msg) -> None:  # noqa: ANN001
                    if msg.type != "error":
                        return
                    text = msg.text or ""
                    if _is_noise(text):
                        return
                    page_errors.append(text)
                    if len(page_errors) >= _MAX_ERRORS_PER_PAGE:
                        return

                page.on("console", _on_console)
                try:
                    response = page.goto(url, timeout=15_000, wait_until="domcontentloaded")
                    status = response.status if response else None
                    # Brief settle for late console errors
                    page.wait_for_timeout(1500)
                    if page_errors and status and 200 <= status < 400:
                        hits.append({"path": path, "url": url, "errors": page_errors})
                        print(
                            f"  [console] {path}: {len(page_errors)} error(s)"
                        )
                except PlaywrightError:
                    pass
                except Exception:  # noqa: BLE001
                    pass
                finally:
                    page.close()
            context.close()
        finally:
            browser.close()

    return hits


def _build_finding(hits: list[dict[str, Any]], *, platform: str = "generic") -> dict[str, Any] | None:
    if not hits:
        return None

    lines: list[str] = []
    for hit in hits:
        path = hit.get("path") or "/"
        label = "homepage" if path == "/" else path
        for err in hit.get("errors") or []:
            human = _humanize_error_line(err)
            if human:
                lines.append(f"On {label}: {human}")

    # De-dupe while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    unique = unique[:3]
    if not unique:
        return None

    bullet_block = "\n".join(f"- {u}" for u in unique)
    pages_note = "homepage" if len(hits) == 1 else f"{len(hits)} pages we opened"

    platform_hint = {
        "lovable": "In Lovable, open the browser console while previewing the live URL, fix each error, then republish.",
        "bolt": "In Bolt, check the preview console for the same errors and fix them before redeploying.",
        "webflow": "In Webflow, publish again after fixing the underlying script or embed causing the error.",
    }.get((platform or "generic").lower(), (
        "Open your live site, reproduce the issue in the browser developer console "
        "(usually F12 → Console), and fix the underlying cause — don't hide errors."
    ))

    severity = "high" if any(
        kw in bullet_block.lower()
        for kw in ("typeerror", "referenceerror", "cannot read", "undefined", "failed to fetch")
    ) else "medium"

    return {
        "severity": severity,
        "title": "Background errors when people open your site",
        "what_we_saw": (
            f"When we loaded your live site ({pages_note}), the browser logged errors "
            f"that often mean buttons, forms, or checkout can fail even when the page "
            f"looks fine:\n{bullet_block}"
        ),
        "why_it_matters": (
            "Visitors don't see these errors, but they can stop signup, payments, or "
            "navigation from working. They're common on AI-built apps when a script "
            "or API hook is half-wired."
        ),
        "fix_prompt": platform_hint,
        "category": CATEGORY_ID,
        "tagged_by_persona": PERSONA,
        "tag": PERSONA_TAG,
        "check_id": "console_errors",
    }


def run_console_errors_lite(
    *,
    base_url: str,
    platform: str = "generic",
) -> dict[str, Any]:
    """Return findings dict; never raises."""
    try:
        hits = _collect_console_errors(base_url)
        finding = _build_finding(hits, platform=platform)
    except Exception as exc:  # noqa: BLE001
        print(f"[console-errors] WARN: {exc}", file=sys.stderr)
        finding = None

    findings = [finding] if finding else []
    failed = ["console_errors"] if finding else []
    passed = [] if finding else ["console_errors"]
    return {
        "findings": findings,
        "passed_check_ids": passed,
        "failed_check_ids": failed,
    }


__all__ = ["CATEGORY_ID", "run_console_errors_lite"]
