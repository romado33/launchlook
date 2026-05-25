"""
prescreen_findings.py - pattern-based finding hits to prep Rob's review.

Crawls a customer's app (post-JS HTML, same domain only, capped at 10 pages),
then runs every regex pattern from findings_library/findings.csv against the
collected HTML. Outputs a Markdown report listing potential hits so Rob can
confirm or dismiss each before any finding lands in the delivered YAML.

This is a PREP tool, not a scanner. Pattern hits != confirmed findings.

Usage:
    python scripts/prescreen_findings.py --customer-id <notion-page-id>
    python scripts/prescreen_findings.py --url https://example.com

Output:
    output/customers/<slug>/prescreen-findings.md
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from lib.customer_loader import Customer, load_customer  # noqa: E402


FINDINGS_CSV = REPO_ROOT / "findings_library" / "findings.csv"

MAX_PAGES = 10
PAGE_TIMEOUT_MS = 15_000
SEED_PATHS = ["/", "/privacy", "/terms", "/about", "/contact"]


# ---------------------------------------------------------------------------
# Findings library
# ---------------------------------------------------------------------------


# Detection field formats observed in findings.csv:
#   regex: /pattern/flags
#   regex: pattern              (no slashes, no flags)
#   manual: ...                 (skip - human-only)
#   http: ...                   (skip for now - handled by capture_screenshots.py status codes)
DETECTION_RE = re.compile(r"^\s*regex:\s*(.*?)\s*$", re.IGNORECASE)


def parse_regex(detection: str) -> re.Pattern[str] | None:
    """Parse a `regex: /.../flags` line into a compiled pattern.

    Returns None if the detection isn't a regex (manual/http rules)."""
    match = DETECTION_RE.match(detection or "")
    if not match:
        return None
    body = match.group(1).strip()
    if not body:
        return None
    # Format: /pattern/flags
    slash_re = re.match(r"^/(.*)/([a-zA-Z]*)$", body)
    if slash_re:
        pattern_src, flag_str = slash_re.group(1), slash_re.group(2)
    else:
        pattern_src, flag_str = body, ""

    flags = 0
    for ch in flag_str.lower():
        if ch == "i":
            flags |= re.IGNORECASE
        elif ch == "m":
            flags |= re.MULTILINE
        elif ch == "s":
            flags |= re.DOTALL
    try:
        return re.compile(pattern_src, flags)
    except re.error as exc:
        print(f"  WARN: skipping unparseable regex {pattern_src!r}: {exc}")
        return None


def load_findings() -> list[dict[str, Any]]:
    """Read findings.csv and return only the rows with a usable regex."""
    if not FINDINGS_CSV.exists():
        sys.exit(f"ERROR: {FINDINGS_CSV} not found")
    findings: list[dict[str, Any]] = []
    with FINDINGS_CSV.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            pattern = parse_regex(row.get("Detection", ""))
            if pattern is None:
                continue
            findings.append(
                {
                    "id": row.get("ID", "").strip(),
                    "name": row.get("Finding Name", "").strip(),
                    "category": row.get("Category", "").strip(),
                    "severity": row.get("Severity", "").strip(),
                    "detection": row.get("Detection", "").strip(),
                    "explanation": row.get("Customer Explanation", "").strip(),
                    "pattern": pattern,
                }
            )
    return findings


# ---------------------------------------------------------------------------
# Crawler
# ---------------------------------------------------------------------------


def same_domain(base: str, candidate: str) -> bool:
    return urlparse(base).hostname == urlparse(candidate).hostname


def normalize_url(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/")


def crawl(base_url: str, max_pages: int = MAX_PAGES) -> list[dict[str, Any]]:
    """Fetch rendered HTML for up to max_pages pages on the same domain.

    Seeds with SEED_PATHS, then follows hrefs found on each page until we
    hit max_pages or run out of new urls. Returns dicts with url + html.
    """
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "ERROR: Playwright not installed. "
            "Run: pip install -r requirements-automation.txt && playwright install chromium"
        )

    visited: set[str] = set()
    queue: list[str] = []
    for path in SEED_PATHS:
        seed = normalize_url(urljoin(base_url + "/", path.lstrip("/")))
        if seed not in visited:
            queue.append(seed)
            visited.add(seed)

    pages: list[dict[str, Any]] = []
    print(f"[crawl] base={base_url} seeds={len(queue)}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (LaunchLook Review Bot; +https://launchlook.app)",
        )
        try:
            while queue and len(pages) < max_pages:
                url = queue.pop(0)
                page = context.new_page()
                try:
                    response = page.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="networkidle")
                    status = response.status if response else None
                    html = page.content() if status and 200 <= status < 400 else ""
                    print(f"  [crawl] {status} {url} ({len(html)} chars)")
                    pages.append({"url": url, "status": status, "html": html})

                    # Discover same-domain links.
                    if html and len(pages) + len(queue) < max_pages * 3:
                        try:
                            hrefs = page.eval_on_selector_all(
                                "a[href]",
                                "els => els.map(e => e.href)",
                            )
                        except Exception:
                            hrefs = []
                        for href in hrefs:
                            if not href:
                                continue
                            norm = normalize_url(href)
                            if not norm.startswith("http"):
                                continue
                            if not same_domain(base_url, norm):
                                continue
                            if norm in visited:
                                continue
                            visited.add(norm)
                            queue.append(norm)
                except PlaywrightError as exc:
                    print(f"  [crawl] ERROR {url}: {str(exc)[:120]}")
                    pages.append({"url": url, "status": "error", "html": ""})
                except Exception as exc:  # noqa: BLE001
                    print(f"  [crawl] ERROR {url}: {exc}")
                    pages.append({"url": url, "status": "error", "html": ""})
                finally:
                    page.close()
        finally:
            context.close()
            browser.close()
    return pages


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------


def context_snippet(text: str, match: re.Match[str], before: int = 5, after: int = 50) -> str:
    start = max(0, match.start() - before)
    end = min(len(text), match.end() + after)
    snippet = text[start:end].replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", snippet).strip()


def scan(pages: list[dict[str, Any]], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one record per (finding, page) where the regex matches."""
    hits: list[dict[str, Any]] = []
    for finding in findings:
        pattern: re.Pattern[str] = finding["pattern"]
        for page in pages:
            html = page.get("html") or ""
            if not html:
                continue
            page_matches: list[dict[str, Any]] = []
            for match in pattern.finditer(html):
                page_matches.append(
                    {"text": match.group(0), "snippet": context_snippet(html, match)}
                )
                if len(page_matches) >= 3:
                    break  # cap per page so the report stays readable
            if page_matches:
                hits.append({"finding": finding, "page": page, "matches": page_matches})
    return hits


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def render_markdown(customer: Customer, pages: list[dict[str, Any]], hits: list[dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc).isoformat()
    page_count = len([p for p in pages if p.get("html")])
    lines: list[str] = []
    lines.append(f"# Prescreen findings - {customer.name}")
    lines.append("")
    lines.append(f"_Generated {now}_")
    lines.append("")
    lines.append("> **These are PATTERN HITS, not confirmed findings.** Rob confirms each one (or dismisses it) before it goes into the YAML for the delivered report. False positives are expected - that is what the human review is for.")
    lines.append("")
    lines.append("## Run summary")
    lines.append("")
    lines.append(f"- Base URL: {customer.app_url}")
    lines.append(f"- Pages crawled with HTML: {page_count}")
    lines.append(f"- Pattern hits to review: {len(hits)}")
    lines.append("")

    lines.append("## Pages visited")
    lines.append("")
    for page in pages:
        status = page.get("status")
        lines.append(f"- `{status}` {page['url']}")
    lines.append("")

    if not hits:
        lines.append("## No pattern hits")
        lines.append("")
        lines.append("Nothing in `findings_library/findings.csv` matched the rendered HTML on any crawled page. Either the site is clean of these specific patterns, or the patterns need broadening.")
        return "\n".join(lines)

    # Group hits by finding id for a cleaner review flow.
    by_finding: dict[str, list[dict[str, Any]]] = {}
    for hit in hits:
        by_finding.setdefault(hit["finding"]["id"], []).append(hit)

    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    sorted_finding_ids = sorted(
        by_finding.keys(),
        key=lambda fid: (
            severity_order.get(by_finding[fid][0]["finding"]["severity"], 99),
            fid,
        ),
    )

    lines.append("## Pattern hits to review")
    lines.append("")
    for fid in sorted_finding_ids:
        hit_group = by_finding[fid]
        finding = hit_group[0]["finding"]
        lines.append(f"### {fid} - {finding['name']}")
        lines.append("")
        lines.append(f"- Category: {finding['category']}")
        lines.append(f"- Severity: {finding['severity']}")
        lines.append(f"- Detection: `{finding['detection']}`")
        if finding.get("explanation"):
            lines.append(f"- Customer explanation (preview): {finding['explanation']}")
        lines.append("- [ ] Confirm or dismiss")
        lines.append("")
        for hit in hit_group:
            page = hit["page"]
            lines.append(f"**On `{page['url']}`** (status {page.get('status')}):")
            for m in hit["matches"]:
                snippet = m["snippet"].replace("`", "'")
                lines.append(f"  - match: `{m['text'][:60]}` ... `{snippet[:140]}`")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--customer-id", help="Notion Customers DB page id (or unique prefix)")
    parser.add_argument("--url", help="Override URL - smoke test without Notion")
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES, help="Cap on pages crawled")
    args = parser.parse_args()

    max_pages = max(1, args.max_pages)
    customer = load_customer(args.customer_id, args.url)
    findings = load_findings()
    print(f"[prescreen] loaded {len(findings)} regex finding(s)")

    pages = crawl(customer.app_url, max_pages)
    hits = scan(pages, findings)
    print(f"[prescreen] {len(hits)} pattern hit(s) across {len(pages)} page(s)")

    out_dir = customer.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    md = render_markdown(customer, pages, hits)
    out_path = out_dir / "prescreen-findings.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"[prescreen] report -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
