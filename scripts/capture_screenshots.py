"""
capture_screenshots.py - Rob's pre-review screenshot grab.

Walks a customer's app at desktop + mobile viewports, screenshots a handful of
canonical pages, and produces a single-page HTML index so Rob can scroll
through every shot during his review session.

Usage:
    python scripts/capture_screenshots.py --customer-id <notion-page-id>
    python scripts/capture_screenshots.py --url https://example.com   # smoke test

Output:
    output/customers/<slug>/screenshots/<viewport>/<path-slug>.png
    output/customers/<slug>/index.html
    output/customers/<slug>/capture-meta.json

Designed to be safe to re-run: each run overwrites the previous PNGs and the
index.html file. The meta.json file tracks status codes per (viewport, path).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from lib.customer_loader import Customer, load_customer, slugify  # noqa: E402

VIEWPORTS = {
    "desktop": (1440, 900),
    "mobile": (390, 844),
}

DEFAULT_PATHS = [
    "/",
    "/privacy",
    "/terms",
    "/auth",
    "/login",
    "/sign-in",
    "/sign-up",
    "/__nonexistent_test__",
]

PAGE_TIMEOUT_MS = 15_000

COOKIE_BANNER_TEXTS = ["Accept", "Accept all", "Got it", "OK", "I agree", "Allow all"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def path_slug(path: str) -> str:
    if path == "/" or not path:
        return "home"
    return slugify(path.strip("/").replace("/", "-")) or "home"


def join_url(base: str, path: str) -> str:
    if not base.endswith("/"):
        base = base + "/"
    return urljoin(base, path.lstrip("/"))


def dismiss_cookie_banner(page) -> None:
    """Best-effort: click anything that looks like a cookie consent button."""
    for label in COOKIE_BANNER_TEXTS:
        try:
            button = page.get_by_role("button", name=label, exact=False)
            if button.count() > 0:
                button.first.click(timeout=1500)
                page.wait_for_timeout(300)
                return
        except Exception:
            continue


# ---------------------------------------------------------------------------
# Capture loop
# ---------------------------------------------------------------------------


def capture(customer: Customer, paths: list[str]) -> dict[str, Any]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "ERROR: Playwright not installed. "
            "Run: pip install -r requirements-automation.txt && playwright install chromium"
        )

    out_dir = customer.output_dir
    screenshots_root = out_dir / "screenshots"
    screenshots_root.mkdir(parents=True, exist_ok=True)

    meta: dict[str, Any] = {
        "customer": customer.slug,
        "app_url": customer.app_url,
        "captured_at": datetime.now(UTC).isoformat(),
        "viewports": {},
    }

    base_url = customer.app_url
    print(f"[capture] customer={customer.slug} base={base_url}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            for viewport_name, (width, height) in VIEWPORTS.items():
                vp_dir = screenshots_root / viewport_name
                vp_dir.mkdir(parents=True, exist_ok=True)
                viewport_meta: list[dict[str, Any]] = []
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    ignore_https_errors=True,
                    user_agent=(
                        "Mozilla/5.0 (LaunchLook Review Bot; +https://launchlook.app)"
                    ),
                )
                for path in paths:
                    url = join_url(base_url, path)
                    out_path = vp_dir / f"{path_slug(path)}.png"
                    entry: dict[str, Any] = {
                        "path": path,
                        "url": url,
                        "file": str(out_path.relative_to(out_dir)),
                    }
                    page = context.new_page()
                    try:
                        response = page.goto(
                            url, timeout=PAGE_TIMEOUT_MS, wait_until="networkidle"
                        )
                        status = response.status if response else None
                        entry["status"] = status
                        dismiss_cookie_banner(page)
                        page.wait_for_timeout(500)
                        page.screenshot(path=str(out_path), full_page=True)
                        print(f"  [{viewport_name}] {status} {path} -> {out_path.name}")
                    except PlaywrightError as exc:
                        msg = str(exc)
                        if "ERR_INVALID_AUTH_CREDENTIALS" in msg or "401" in msg:
                            entry["status"] = "auth_required"
                            print(
                                f"  [{viewport_name}] AUTH required at {path} - skipped"
                            )
                        elif "timeout" in msg.lower():
                            entry["status"] = "timeout"
                            print(f"  [{viewport_name}] TIMEOUT at {path}")
                        else:
                            entry["status"] = "error"
                            entry["error"] = msg[:200]
                            print(f"  [{viewport_name}] ERROR at {path}: {msg[:120]}")
                    except Exception as exc:  # noqa: BLE001
                        entry["status"] = "error"
                        entry["error"] = str(exc)[:200]
                        print(f"  [{viewport_name}] ERROR at {path}: {exc}")
                    finally:
                        page.close()
                    viewport_meta.append(entry)
                context.close()
                meta["viewports"][viewport_name] = viewport_meta
        finally:
            browser.close()

    meta_path = out_dir / "capture-meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[capture] meta -> {meta_path}")
    return meta


# ---------------------------------------------------------------------------
# HTML index
# ---------------------------------------------------------------------------


def render_index(customer: Customer, meta: dict[str, Any]) -> Path:
    out_dir = customer.output_dir
    captured_at = meta.get("captured_at", "")

    def shots_for(viewport: str) -> str:
        items = meta["viewports"].get(viewport, [])
        if not items:
            return '<p class="muted">No screenshots captured.</p>'
        cards: list[str] = []
        for entry in items:
            status = entry.get("status")
            badge_cls = "badge"
            if isinstance(status, int):
                if 200 <= status < 300:
                    badge_cls = "badge ok"
                elif status == 404:
                    badge_cls = "badge notfound"
                else:
                    badge_cls = "badge warn"
            else:
                badge_cls = "badge warn"
            file_rel = entry.get("file")
            url = entry.get("url", "")
            img = (
                f'<img loading="lazy" src="{file_rel}" alt="{entry["path"]}">'
                if file_rel and (out_dir / file_rel).exists()
                else '<div class="missing">No screenshot (status: ' f"{status})</div>"
            )
            cards.append(
                f"""<div class="card">
  <div class="card-head">
    <code class="path">{entry["path"]}</code>
    <span class="{badge_cls}">{status}</span>
  </div>
  <div class="card-url"><a href="{url}" target="_blank" rel="noopener">{url}</a></div>
  {img}
</div>"""
            )
        return "\n".join(cards)

    desktop_html = shots_for("desktop")
    mobile_html = shots_for("mobile")

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>LaunchLook screenshots - {customer.slug}</title>
  <style>
    body {{ margin:0; font-family: ui-sans-serif, -apple-system, Segoe UI, Roboto, sans-serif; background:#0b0d12; color:#e6e8ef; }}
    .container {{ max-width: 1500px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin:0 0 4px; font-size: 24px; }}
    .meta {{ color:#8a92a6; font-size: 13px; margin-bottom: 24px; }}
    h2 {{ margin: 32px 0 12px; font-size: 14px; color:#8a92a6; text-transform: uppercase; letter-spacing:.06em; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; }}
    .card {{ background:#151821; border:1px solid #262a3a; border-radius: 10px; overflow:hidden; }}
    .card-head {{ display:flex; justify-content:space-between; align-items:center; padding: 10px 14px; background:#1c2030; border-bottom:1px solid #262a3a; }}
    .card-head code {{ font-size: 13px; color:#cdd3e1; }}
    .card-url {{ padding: 6px 14px; font-size: 11px; color:#8a92a6; word-break: break-all; }}
    .card-url a {{ color:#a991ff; text-decoration: none; }}
    img {{ display:block; max-width: 100%; height: auto; background:#000; }}
    .missing {{ padding: 32px; text-align:center; color:#8a92a6; }}
    .badge {{ font-size: 11px; padding: 2px 8px; border-radius: 4px; background:#374151; color:#e5e7eb; }}
    .badge.ok {{ background: rgba(34,197,94,.18); color:#86efac; }}
    .badge.notfound {{ background: rgba(234,179,8,.18); color:#fcd34d; }}
    .badge.warn {{ background: rgba(239,68,68,.18); color:#fca5a5; }}
    .muted {{ color:#8a92a6; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{customer.name}</h1>
    <div class="meta">
      Base URL: <a href="{customer.app_url}" target="_blank">{customer.app_url}</a><br>
      Captured: {captured_at}
    </div>

    <h2>Desktop (1440 x 900)</h2>
    <div class="grid">{desktop_html}</div>

    <h2>Mobile (390 x 844)</h2>
    <div class="grid">{mobile_html}</div>
  </div>
</body>
</html>
"""
    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--customer-id", help="Notion Customers DB page id (or unique prefix)"
    )
    parser.add_argument(
        "--url", help="Override URL - useful for smoke tests without Notion"
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        help="Override list of paths to visit. Defaults to a sensible set.",
    )
    args = parser.parse_args()

    customer = load_customer(args.customer_id, args.url)
    paths = args.paths or list(DEFAULT_PATHS)

    meta = capture(customer, paths)
    index_path = render_index(customer, meta)
    print(f"[capture] index -> {index_path}")
    print(f"[capture] open: {index_path.resolve().as_uri()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
