"""Fetch + clean HTML from a customer URL for LLM context.

The vision call also sees screenshots, but a cleaned HTML extract lets the
model ground findings in actual text and attributes (button labels, link
hrefs, meta tags, page titles) without paying vision tokens for every page.

Output shape for ``extract_pages``::

    [
      {
        "path": "/",
        "url": "https://example.com/",
        "status": 200,
        "title": "Home",
        "meta": {"description": "...", "og:title": "..."},
        "text": "Visible text body, whitespace-collapsed (capped to ~6000 chars)",
        "buttons": ["Sign up", "Log in", ...],
        "links": [{"text": "Privacy", "href": "/privacy"}, ...],
      },
      ...
    ]

Scripts, styles, SVG bodies, comments, and noscript blocks are stripped.
Inline data: URIs are not preserved (would blow the context budget).
"""

from __future__ import annotations

import re
import sys
from typing import Any
from urllib.parse import urljoin, urlparse

DEFAULT_PATHS = [
    "/",
    "/privacy",
    "/terms",
    "/auth",
    "/login",
    "/sign-in",
    "/sign-up",
]


PAGE_TIMEOUT_MS = 15_000
TEXT_CAP = 6000  # chars of visible text per page
LINK_CAP = 60  # links per page
BUTTON_CAP = 40  # buttons / role=button per page


def join_url(base: str, path: str) -> str:
    if not base.endswith("/"):
        base = base + "/"
    return urljoin(base, path.lstrip("/"))


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _clean_html_to_extract(html: str, url: str) -> dict[str, Any]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        sys.exit(
            "ERROR: beautifulsoup4 not installed.\n"
            "Run: pip install -r requirements-ai.txt"
        )

    soup = BeautifulSoup(html or "", "html.parser")

    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = _collapse_ws(soup.title.string)

    meta: dict[str, str] = {}
    for m in soup.find_all("meta"):
        # BeautifulSoup attr access can return AttributeValueList for multi-valued
        # attrs; coerce to str before the str-only ops we need below.
        name = str(m.get("name") or m.get("property") or "")
        content = str(m.get("content") or "")
        if name and content:
            meta[name.strip().lower()] = _collapse_ws(content)[:300]

    body = soup.body or soup
    text = _collapse_ws(body.get_text(separator=" ", strip=True))
    if len(text) > TEXT_CAP:
        text = text[:TEXT_CAP] + " …[truncated]"

    buttons: list[str] = []
    seen_buttons: set[str] = set()
    for el in soup.select(
        "button, [role='button'], input[type='submit'], input[type='button']"
    ):
        # See comment above re: BeautifulSoup AttributeValueList; coerce to str.
        label = _collapse_ws(
            str(
                el.get_text(" ", strip=True)
                or el.get("value", "")
                or el.get("aria-label", "")
            )
        )
        if label and label not in seen_buttons:
            seen_buttons.add(label)
            buttons.append(label)
            if len(buttons) >= BUTTON_CAP:
                break

    links: list[dict[str, str]] = []
    seen_links: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        label = _collapse_ws(a.get_text(" ", strip=True))
        key = f"{label}|{href}"
        if key in seen_links:
            continue
        seen_links.add(key)
        links.append({"text": label or "(no text)", "href": href[:200]})
        if len(links) >= LINK_CAP:
            break

    return {
        "url": url,
        "title": title,
        "meta": meta,
        "text": text,
        "buttons": buttons,
        "links": links,
    }


def extract_pages(
    base_url: str,
    paths: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Fetch and clean each path. Skips paths whose host can't be reached.

    Uses Playwright + Chromium (already required by the rest of the
    pipeline). Networkidle wait, 15s timeout per page, single browser
    context shared across pages.
    """
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "ERROR: Playwright not installed.\n"
            "Run: pip install -r requirements-ai.txt && playwright install chromium"
        )

    paths = paths or list(DEFAULT_PATHS)
    pages: list[dict[str, Any]] = []
    base_host = urlparse(base_url).hostname or ""

    print(f"[html] base={base_url} host={base_host} paths={len(paths)}")

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
                entry: dict[str, Any] = {"path": path, "url": url}
                try:
                    response = page.goto(
                        url, timeout=PAGE_TIMEOUT_MS, wait_until="networkidle"
                    )
                    status = response.status if response else None
                    entry["status"] = status
                    if status and 200 <= status < 400:
                        html = page.content()
                        cleaned = _clean_html_to_extract(html, url)
                        entry.update(cleaned)
                        print(
                            f"  [html] {status} {path} ({len(cleaned['text'])} chars)"
                        )
                    else:
                        entry["title"] = ""
                        entry["meta"] = {}
                        entry["text"] = ""
                        entry["buttons"] = []
                        entry["links"] = []
                        print(f"  [html] {status} {path} (no content)")
                except PlaywrightError as exc:
                    entry["status"] = "error"
                    entry["error"] = str(exc)[:200]
                    print(f"  [html] ERROR {path}: {str(exc)[:120]}")
                except Exception as exc:  # noqa: BLE001
                    entry["status"] = "error"
                    entry["error"] = str(exc)[:200]
                    print(f"  [html] ERROR {path}: {exc}")
                finally:
                    page.close()
                pages.append(entry)
            context.close()
        finally:
            browser.close()

    return pages


# ---------------------------------------------------------------------------
# Rendering for the prompt context
# ---------------------------------------------------------------------------


def render_pages_for_prompt(pages: list[dict[str, Any]]) -> str:
    """Format the page extracts as the ``{html_extracts}`` block in the prompt.

    Each page becomes a fenced section so the LLM can scan them quickly.
    Pages that errored / 404'd are still listed (their absence matters as
    much as their presence for the audit).
    """
    if not pages:
        return "(no HTML extracted)"
    blocks: list[str] = []
    for p in pages:
        status = p.get("status")
        header = f"### {p['path']}  (status {status})  {p['url']}"
        if not isinstance(status, int) or not (200 <= status < 400):
            blocks.append(header + "\n  (no usable HTML)")
            continue
        lines = [header]
        if p.get("title"):
            lines.append(f"  title: {p['title']}")
        meta = p.get("meta") or {}
        for k in (
            "description",
            "og:title",
            "og:description",
            "og:image",
            "twitter:card",
        ):
            v = meta.get(k)
            if v:
                lines.append(f"  meta[{k}]: {v}")
        buttons = p.get("buttons") or []
        if buttons:
            lines.append("  buttons: " + " | ".join(buttons[:20]))
        links = p.get("links") or []
        if links:
            link_lines = ", ".join(
                f"{link['text']}->{link['href']}" for link in links[:15]
            )
            lines.append("  links: " + link_lines)
        text = p.get("text") or ""
        if text:
            lines.append("  visible_text: " + text[:1500])
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_status_summary(pages: list[dict[str, Any]]) -> str:
    """One-line-per-path status summary for the prompt."""
    if not pages:
        return "(no pages probed)"
    return "\n".join(f"  {p.get('status')!s:>6}  {p['path']}" for p in pages)
