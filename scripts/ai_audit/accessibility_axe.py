"""axe-core accessibility runner + plain-English translator (q16).

Loads axe-core (pinned at ``4.10.0`` via the unpkg CDN) into a headless
Playwright tab pointed at the customer's homepage, runs the WCAG 2.1
AA rule subset, and rolls the violations into five buyer-facing
buckets:

* ``image_alt`` -- images missing alt text.
* ``color_contrast`` -- text-on-background contrast too low.
* ``form_label`` -- inputs missing labels.
* ``button_name`` -- buttons / links with no readable text.
* ``keyboard`` -- elements unreachable with the Tab key.

Buyer-facing display name for the whole category is
"accessibility checks". The strings ``axe-core``, ``WCAG``,
``aria-label``, and ``a11y`` NEVER appear on a customer surface, per
``docs/SIMPLICITY-GUARDRAILS.md`` section 6.

Caching
-------
Axe-core results are cached per URL in ``data/axe_cache/<sha1>.json``
for 24h (override with ``AXE_CACHE_TTL_SECONDS``). Re-runs skip
Chromium entirely. The cache dir is gitignored.

Tier-cap
--------
* Starter Package -- 1 finding (worst bucket).
* Scale Up Package -- up to 3.
* Pro Package -- all five buckets.

Builder-specific fix prompts (Lovable / Bolt / v0 / Cursor / Webflow
/ generic) are pre-generated. We never ask the LLM to draft them.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

CATEGORY_ID = "accessibility_checks"

AXE_SCRIPT_URL = "https://unpkg.com/axe-core@4.10.0/axe.min.js"

_DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60
_CACHE_DIR = Path("data/axe_cache")

# Mapping from axe rule id -> internal bucket id.
_RULE_TO_BUCKET = {
    "image-alt": "image_alt",
    "input-image-alt": "image_alt",
    "color-contrast": "color_contrast",
    "label": "form_label",
    "label-title-only": "form_label",
    "button-name": "button_name",
    "link-name": "button_name",
    "input-button-name": "button_name",
    "keyboard": "keyboard",
    "tabindex": "keyboard",
    "focus-order-semantics": "keyboard",
}

_SEVERITY_BY_BUCKET = {
    "image_alt": "medium",
    "color_contrast": "medium",
    "form_label": "high",
    "button_name": "medium",
    "keyboard": "high",
}

_BUCKET_TITLES = {
    "image_alt": "Some images have no description for screen readers",
    "color_contrast": "Some text is hard to read against its background",
    "form_label": "Some form fields don't tell screen readers what to type",
    "button_name": "Some buttons or links have no readable text",
    "keyboard": "Some interactive elements can't be reached with the Tab key",
}

_BUCKET_WHAT_WE_SAW = {
    "image_alt": (
        "We found {n} image(s) on your homepage with no description. Screen readers skip "
        "them silently, so visitors with low vision don't get the context they convey."
    ),
    "color_contrast": (
        "We found {n} block(s) of text where the contrast against the background is too low. "
        "Visitors with weaker eyesight (and anyone outside in sunlight) struggle to read it."
    ),
    "form_label": (
        "We found {n} form field(s) with no visible or programmatic label. Voice-input and "
        "screen-reader users can't tell what to type, so they bounce instead of converting."
    ),
    "button_name": (
        "We found {n} button(s) or link(s) with no readable text. People using a hidden "
        "description for assistive tools don't know what they do, so they avoid clicking."
    ),
    "keyboard": (
        "We found {n} interactive element(s) that can't be reached with the Tab key. Visitors "
        "who don't use a mouse will get stuck and abandon the flow."
    ),
}

_WHY_IT_MATTERS = (
    "Accessibility gaps directly hurt conversion. A buyer who can't read the headline, fill "
    "the form, or tab through to the CTA simply leaves -- and the bounce never shows up in "
    "your analytics as 'accessibility'."
)


# Fix prompts: keyed by (bucket, platform).
_FIX_PROMPT_LIBRARY: dict[tuple[str, str], str] = {
    ("image_alt", "lovable"): (
        "Open Lovable and ask it: \"Find every <img> tag on the homepage with no alt attribute "
        "or an empty one. For decorative images keep alt=\\\"\\\", for content images write what "
        "the image shows in 5-10 plain words.\""
    ),
    ("image_alt", "bolt"): (
        "Open your project in Bolt. Ask Bolt: \"List every <img> on the homepage. Add an alt "
        "attribute to each one describing the content of the image, or alt=\\\"\\\" if it's purely "
        "decorative.\""
    ),
    ("image_alt", "v0"): (
        "Open the homepage in v0. Ask v0: \"Audit every Image component on the page. Pass a "
        "descriptive alt prop on each one; pass alt=\\\"\\\" only for purely decorative images.\""
    ),
    ("image_alt", "cursor"): (
        "In Cursor, search the homepage for <img tags. Add an alt attribute to every match -- "
        "5-10 words describing what the image shows for content images, alt=\"\" for purely "
        "decorative ones."
    ),
    ("image_alt", "webflow"): (
        "Open Webflow Designer. Click each image on the homepage, open the Image Settings "
        "panel, and fill in the Alt Text field with a 5-10 word description (or check 'Decorative'."
    ),
    ("image_alt", "generic"): (
        "On every image on the homepage, add a short description of what the image shows. For "
        "purely decorative images, mark them as decorative so screen readers skip them."
    ),
    ("color_contrast", "lovable"): (
        "Open Lovable and ask it: \"Find every text block on the homepage where the foreground "
        "color doesn't meet a 4.5:1 contrast ratio against the background. Suggest darker text "
        "or a lighter background that passes.\""
    ),
    ("color_contrast", "bolt"): (
        "Open your project in Bolt. Ask Bolt: \"Audit the homepage CSS for any text-on-background "
        "color pair below 4.5:1 contrast. Adjust the colors so every paragraph and CTA passes.\""
    ),
    ("color_contrast", "v0"): (
        "Open the homepage in v0. Ask v0: \"Increase the contrast of any low-contrast text by "
        "darkening the foreground or lightening the background, targeting at least 4.5:1.\""
    ),
    ("color_contrast", "cursor"): (
        "In Cursor, run a quick contrast audit on the homepage. For each failing pair, edit the "
        "stylesheet so the ratio is at least 4.5:1 -- darken foreground or lighten background."
    ),
    ("color_contrast", "webflow"): (
        "Open Webflow Designer Style Manager. Use a contrast checker (e.g. webaim.org) on each "
        "text color against its background. Adjust to a darker text or lighter background so "
        "every pair hits at least 4.5:1."
    ),
    ("color_contrast", "generic"): (
        "Increase the contrast of any text that fails 4.5:1 against its background. Tools like "
        "webaim.org show you the exact ratio; pick a darker text color or lighter background."
    ),
    ("form_label", "lovable"): (
        "Open Lovable and ask it: \"Find every form field on the homepage with no visible label "
        "or no associated <label for>. Add a clear visible label tied to each input.\""
    ),
    ("form_label", "bolt"): (
        "Open your project in Bolt. Ask Bolt: \"Audit homepage form fields. Wrap each input in a "
        "<label> tag, or use a <label for> with a matching id. Visible labels beat placeholders.\""
    ),
    ("form_label", "v0"): (
        "Open the homepage form in v0. Ask v0: \"Add a visible <Label> component to every "
        "<Input> so screen readers and voice-input users know what to type.\""
    ),
    ("form_label", "cursor"): (
        "In Cursor, open the form component on the homepage. For every <input> add a paired "
        "<label for=\"...\"> with text describing what to type. Don't rely on placeholders alone."
    ),
    ("form_label", "webflow"): (
        "Open Webflow Designer. Select each form input, open the Settings panel, and add a "
        "label element above it. Connect the label's For attribute to the input's Name."
    ),
    ("form_label", "generic"): (
        "Every form field needs a visible text label above or beside it. Placeholders alone "
        "aren't enough -- they disappear once the visitor starts typing."
    ),
    ("button_name", "lovable"): (
        "Open Lovable and ask it: \"Find every <button> or <a> on the homepage with no visible "
        "text (icon-only buttons especially). Add a short text label or a hidden description "
        "for assistive tools.\""
    ),
    ("button_name", "bolt"): (
        "Open your project in Bolt. Ask Bolt: \"Audit icon-only buttons and links on the "
        "homepage. Add either visible text or a hidden description for assistive tools "
        "describing the action.\""
    ),
    ("button_name", "v0"): (
        "Open the homepage in v0. Ask v0: \"Add a hidden description for assistive tools to "
        "every icon-only Button component so screen readers announce its purpose.\""
    ),
    ("button_name", "cursor"): (
        "In Cursor, search the homepage for icon-only buttons or links. For each one, add a "
        "short visible label, or attach a hidden description for assistive tools describing "
        "what tapping it does."
    ),
    ("button_name", "webflow"): (
        "Open Webflow Designer. For each icon-only button or link on the homepage, open the "
        "Settings panel and add a short Accessibility Label describing what it does."
    ),
    ("button_name", "generic"): (
        "Every button or link needs readable text describing what it does. If you want a "
        "visual icon only, add a hidden description for assistive tools so the action stays "
        "discoverable."
    ),
    ("keyboard", "lovable"): (
        "Open Lovable and ask it: \"Find every interactive element on the homepage that's "
        "skipped by Tab navigation. Add tabindex=\\\"0\\\" or convert it to a real <button>.\""
    ),
    ("keyboard", "bolt"): (
        "Open your project in Bolt. Ask Bolt: \"Audit homepage interactives. Any clickable <div> "
        "or <span> should become a <button> or get tabindex=\\\"0\\\" plus an Enter handler.\""
    ),
    ("keyboard", "v0"): (
        "Open the homepage in v0. Ask v0: \"Replace clickable <div> elements with proper "
        "<Button> components, or add keyboard handlers (Enter, Space) and tabindex=\\\"0\\\".\""
    ),
    ("keyboard", "cursor"): (
        "In Cursor, find clickable <div> or <span> elements on the homepage. Convert them to "
        "<button>, or add role=\"button\" plus tabindex=\"0\" plus key handlers for Enter and "
        "Space."
    ),
    ("keyboard", "webflow"): (
        "Open Webflow Designer. For each interactive element that's not a native button or "
        "link, swap it for the Button or Link element so it shows up in keyboard tab order."
    ),
    ("keyboard", "generic"): (
        "Every interactive element needs to be reachable with the Tab key. Use real <button> "
        "and <a> tags wherever possible; if you must use a generic element, add tabindex and "
        "keyboard handlers."
    ),
}


def _fix_prompt_for(bucket: str, platform: str) -> str:
    key = (bucket, (platform or "generic").lower())
    if key in _FIX_PROMPT_LIBRARY:
        return _FIX_PROMPT_LIBRARY[key]
    return _FIX_PROMPT_LIBRARY[(bucket, "generic")]


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _cache_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"{key}.json"


def _cache_ttl_seconds() -> int:
    raw = os.environ.get("AXE_CACHE_TTL_SECONDS")
    if not raw:
        return _DEFAULT_CACHE_TTL_SECONDS
    try:
        return max(0, int(raw))
    except ValueError:
        return _DEFAULT_CACHE_TTL_SECONDS


def _read_cache(key: str) -> dict[str, Any] | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > _cache_ttl_seconds():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(key: str, payload: dict[str, Any]) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(key).write_text(json.dumps(payload), encoding="utf-8")


# ---------------------------------------------------------------------------
# Playwright runner
# ---------------------------------------------------------------------------


async def _run_axe_async(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright  # local import: optional dep

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=45_000)
            await page.add_script_tag(url=AXE_SCRIPT_URL)
            results = await page.evaluate(
                """async () => {
                    const r = await window.axe.run(document, {
                        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
                        resultTypes: ['violations']
                    });
                    return r;
                }"""
            )
        finally:
            await browser.close()
    return results or {}


def run_axe_raw(url: str, *, use_cache: bool = True) -> dict[str, Any] | None:
    """Run axe-core against ``url`` and return the raw JSON result.

    Returns None when Playwright isn't installed or the page can't
    load. Result is cached for 24h per URL.
    """
    key = _cache_key(url)
    if use_cache:
        cached = _read_cache(key)
        if cached is not None:
            return cached
    try:
        result = asyncio.run(_run_axe_async(url))
    except Exception:  # noqa: BLE001
        return None
    if use_cache and result:
        _write_cache(key, result)
    return result


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


def _bucket_violations(axe_results: dict[str, Any] | None) -> dict[str, int]:
    """Roll axe violations into the five buyer-facing buckets."""
    buckets: dict[str, int] = {}
    if not axe_results:
        return buckets
    for violation in axe_results.get("violations") or []:
        rule_id = violation.get("id")
        bucket = _RULE_TO_BUCKET.get(rule_id)
        if not bucket:
            continue
        count = len(violation.get("nodes") or [])
        buckets[bucket] = buckets.get(bucket, 0) + (count or 1)
    return buckets


_BUCKET_RANK = {
    "form_label": 5,
    "keyboard": 4,
    "color_contrast": 3,
    "image_alt": 2,
    "button_name": 1,
}


def _check_id(bucket: str) -> str:
    return f"accessibility_checks.{bucket}"


def _tier_cap(tier: str) -> int:
    t = (tier or "").strip().lower()
    if t in {"pro", "pro package"}:
        return 99
    if t in {"scale up", "scale up package", "scaleup", "scale-up"}:
        return 3
    return 1


def to_findings(
    bucketed: dict[str, int],
    *,
    tier: str,
    platform: str,
) -> dict[str, Any]:
    """Apply tier cap + builder fix prompt to the bucketed violations."""

    cap = _tier_cap(tier)
    actionable = [(bucket, count) for bucket, count in bucketed.items() if count > 0]
    actionable.sort(
        key=lambda pair: (-_BUCKET_RANK.get(pair[0], 0), -pair[1])
    )

    findings: list[dict[str, Any]] = []
    failed_ids: list[str] = []
    for bucket, count in actionable[:cap]:
        findings.append(
            {
                "id": _check_id(bucket),
                "category": CATEGORY_ID,
                "title": _BUCKET_TITLES[bucket],
                "severity": _SEVERITY_BY_BUCKET[bucket],
                "what_we_saw": _BUCKET_WHAT_WE_SAW[bucket].format(n=count),
                "why_it_matters": _WHY_IT_MATTERS,
                "fix_prompt": _fix_prompt_for(bucket, platform),
                "tester": "The Phone-First Friend",
                "source": "external",
                "external_origin": "axe",
            }
        )
        failed_ids.append(_check_id(bucket))

    passed_ids = [
        _check_id(b)
        for b in _BUCKET_TITLES
        if b not in bucketed
    ]

    return {
        "findings": findings,
        "passed_check_ids": passed_ids,
        "failed_check_ids": failed_ids,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_accessibility_axe(
    *,
    base_url: str,
    tier: str,
    platform: str = "generic",
    use_cache: bool = True,
) -> dict[str, Any]:
    """Run axe-core against ``base_url`` and translate the result.

    Returns a dict with keys::

        {
          "findings": list[dict],
          "passed_check_ids": list[str],
          "failed_check_ids": list[str],
          "ran": bool,
        }

    When Playwright is missing or the headless run fails, ``ran``
    is False, findings is empty, and passed_check_ids is empty -- we
    don't get to claim accessibility passes if we never ran the check.
    """
    raw = run_axe_raw(base_url, use_cache=use_cache)
    ran = raw is not None
    if not ran:
        return {
            "findings": [],
            "passed_check_ids": [],
            "failed_check_ids": [],
            "ran": False,
        }
    bucketed = _bucket_violations(raw)
    translated = to_findings(bucketed, tier=tier, platform=platform)
    translated["ran"] = True
    return translated
