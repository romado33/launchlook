"""Core Web Vitals fetcher + plain-English translator (q14).

Pulls Google PageSpeed Insights v5 for the customer's homepage and
translates the three Core Web Vitals (LCP / INP / CLS) into plain
English findings the buyer can act on.

Buyer-facing display name for the whole category is
"performance & speed". The internal acronyms (LCP / INP / CLS) and the
phrase "Core Web Vitals" NEVER appear on a customer surface, per
``docs/SIMPLICITY-GUARDRAILS.md`` section 6.

Caching
-------
PSI responses are cached per (url, strategy) in
``data/psi_cache/<sha1>.json`` for 24h (override with
``PSI_CACHE_TTL_SECONDS``). Re-runs of the same customer never burn
the 25K/day quota. The cache dir is gitignored.

API key
-------
Set ``PSI_API_KEY`` (or the legacy alias ``PAGESPEED_API_KEY``) in
``.env`` for the 25K/day per-project budget. Without a key the
runner falls back to anonymous calls with retry-on-429 backoff.

Tier-cap
--------
* Starter Package -- 1 finding (worst-rated metric only).
* Scale Up Package -- up to 3 (one per metric that isn't GOOD).
* Pro Package -- full breakdown plus all three metrics.

Builder-specific fix prompts (Lovable / Bolt / v0 / Cursor / Webflow
/ generic) are pre-generated from a deterministic library; we never
ask the LLM to draft them.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CATEGORY_ID = "performance_speed"

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

_DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60
_CACHE_DIR = Path("data/psi_cache")


# Each metric maps to a buyer-facing dimension we can talk about
# without ever uttering the acronym.
_METRIC_LABEL = {
    "lcp": "how fast the main image or headline shows up",
    "inp": "how fast the page reacts to a tap or click",
    "cls": "how much things jump around as the page loads",
}

_SEVERITY_BY_RATING = {
    "GOOD": "low",
    "NEEDS_IMPROVEMENT": "medium",
    "POOR": "high",
    "UNKNOWN": "low",
}

_RATING_RANK = {"POOR": 3, "NEEDS_IMPROVEMENT": 2, "GOOD": 1, "UNKNOWN": 0}

# Threshold table (per Google CrUX). Values in ms for LCP/INP,
# unitless for CLS.
_THRESHOLDS = {
    "lcp": (2500, 4000),
    "inp": (200, 500),
    "cls": (0.10, 0.25),
}


def _rating_for(metric: str, value: float | None) -> str:
    if value is None:
        return "UNKNOWN"
    good_cap, ni_cap = _THRESHOLDS[metric]
    if value <= good_cap:
        return "GOOD"
    if value <= ni_cap:
        return "NEEDS_IMPROVEMENT"
    return "POOR"


# Fix prompt library: pre-generated, builder-specific, plain English.
# Keyed by (metric, platform). Platforms beyond "generic" fall through
# to the generic prompt when missing.
_FIX_PROMPT_LIBRARY: dict[tuple[str, str], str] = {
    ("lcp", "lovable"): (
        "Open your homepage in Lovable. Find the largest image at the top of the page. "
        'Ask Lovable: "Make the hero image lazy-load only after the page is interactive, '
        'and add a low-resolution placeholder so visitors see something immediately."'
    ),
    ("lcp", "bolt"): (
        "Open your project in Bolt. Find the top-of-page image or headline. Ask Bolt: "
        '"Preload the hero image and serve a smaller WebP variant. Add width and height '
        'so the browser reserves space while it loads."'
    ),
    ("lcp", "v0"): (
        'Open your homepage component in v0. Ask v0: "Wrap the hero image in Next.js Image '
        'with priority=true and provide explicit width and height. Preload the chosen variant."'
    ),
    ("lcp", "cursor"): (
        "In Cursor, open the homepage component. Identify the hero image or headline element. "
        'Add <link rel="preload" as="image" href="..."> to the document head and set '
        "explicit width and height on the element so it doesn't reflow."
    ),
    ("lcp", "webflow"): (
        "Open Webflow Designer. Click the hero image, open the Settings panel, and switch "
        "Loading to Eager. Then in Image Settings set explicit width and height so the "
        "browser reserves the space while the file downloads."
    ),
    ("lcp", "generic"): (
        "Find the largest image or headline at the top of the page. Add explicit width and "
        "height, serve a smaller compressed variant, and preload it so it appears as soon as "
        "the page starts rendering."
    ),
    ("inp", "lovable"): (
        'Open your homepage in Lovable. Ask Lovable: "Find every button or input handler on '
        "the homepage that does heavy work synchronously. Defer the heavy parts with "
        'requestIdleCallback so the page reacts to taps right away."'
    ),
    ("inp", "bolt"): (
        'Open your project in Bolt. Ask Bolt: "Profile homepage onClick handlers. Move any '
        'blocking work off the main thread; debounce input handlers; preload heavy modules."'
    ),
    ("inp", "v0"): (
        'Open the homepage in v0. Ask v0: "Audit React event handlers for blocking work. '
        'Wrap heavy logic in startTransition or move it to a server action."'
    ),
    ("inp", "cursor"): (
        "In Cursor, open the homepage React component. Find handlers attached to onClick or "
        "onInput. Move heavy computation off the main thread using requestIdleCallback or "
        "setTimeout(fn, 0), and debounce input handlers."
    ),
    ("inp", "webflow"): (
        "Open Webflow Designer and identify any custom code embeds attached to clickable "
        "elements. Move heavy logic into a worker or defer it using setTimeout so taps "
        "respond instantly."
    ),
    ("inp", "generic"): (
        "Find buttons and inputs on the homepage that take more than a quarter-second to react. "
        "Move any heavy work off the main thread (workers, idle callbacks) so the page feels "
        "instantly responsive."
    ),
    ("cls", "lovable"): (
        'Open your homepage in Lovable. Ask Lovable: "Find every image and embedded video on '
        "the homepage and add explicit width and height so the browser reserves the right amount "
        'of space while loading."'
    ),
    ("cls", "bolt"): (
        'Open your project in Bolt. Ask Bolt: "Add explicit width and height to every image, '
        "iframe, and ad slot on the homepage. Reserve space for above-the-fold fonts with "
        'size-adjust."'
    ),
    ("cls", "v0"): (
        'Open the homepage in v0. Ask v0: "Use the Next.js Image component with width and '
        'height set on every image. Add font-display: optional or size-adjust to webfonts."'
    ),
    ("cls", "cursor"): (
        "In Cursor, find every <img>, <iframe>, and ad container on the homepage. Add explicit "
        "width and height attributes. For webfonts, add size-adjust or font-display: optional "
        "so text doesn't reflow once the font loads."
    ),
    ("cls", "webflow"): (
        "Open Webflow Designer. For every element with position: absolute near the top of the "
        "homepage, add explicit width and height in pixels. Reserve space for images and "
        "embeds via the Settings panel."
    ),
    ("cls", "generic"): (
        "Find images, embeds, and ads near the top of the page. Add explicit width and height "
        "so the browser reserves the right space; lock font sizing so text doesn't reflow."
    ),
}


def _fix_prompt_for(metric: str, platform: str) -> str:
    key = (metric, (platform or "generic").lower())
    if key in _FIX_PROMPT_LIBRARY:
        return _FIX_PROMPT_LIBRARY[key]
    return _FIX_PROMPT_LIBRARY[(metric, "generic")]


# ---------------------------------------------------------------------------
# Caching helpers
# ---------------------------------------------------------------------------


def _cache_key(url: str, strategy: str) -> str:
    h = hashlib.sha1(f"{url}|{strategy}".encode()).hexdigest()
    return h


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"{key}.json"


def _cache_ttl_seconds() -> int:
    raw = os.environ.get("PSI_CACHE_TTL_SECONDS")
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
# PSI fetch
# ---------------------------------------------------------------------------


def fetch_psi(
    url: str,
    *,
    strategy: str = "mobile",
    api_key: str | None = None,
    use_cache: bool = True,
    max_retries: int = 3,
) -> dict[str, Any] | None:
    """Call the PSI v5 API. Returns parsed JSON, or None on failure."""
    key = (
        api_key or os.environ.get("PSI_API_KEY") or os.environ.get("PAGESPEED_API_KEY")
    )
    cache_key = _cache_key(url, strategy)
    if use_cache:
        cached = _read_cache(cache_key)
        if cached is not None:
            return cached

    params = {"url": url, "strategy": strategy, "category": "performance"}
    if key:
        params["key"] = key
    qs = urllib.parse.urlencode(params)
    full_url = f"{PSI_ENDPOINT}?{qs}"

    backoff = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "LaunchLook/1.0 (performance_speed)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if use_cache:
                _write_cache(cache_key, data)
            return data
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            return None
    return None


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


def extract_metrics(psi_data: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Extract LCP / INP / CLS values + Google ratings from a PSI payload.

    Returns a dict like::

        {"lcp": {"value_ms": 3200, "rating": "NEEDS_IMPROVEMENT", "pct_poor": 18}, ...}

    Missing metrics are returned with ``rating == "UNKNOWN"``.
    """
    out: dict[str, dict[str, Any]] = {}
    if not psi_data:
        for m in ("lcp", "inp", "cls"):
            out[m] = {"value": None, "rating": "UNKNOWN", "pct_poor": None}
        return out

    crux = (psi_data.get("loadingExperience") or {}).get("metrics") or {}
    mapping = {
        "lcp": "LARGEST_CONTENTFUL_PAINT_MS",
        "inp": "INTERACTION_TO_NEXT_PAINT",
        "cls": "CUMULATIVE_LAYOUT_SHIFT_SCORE",
    }

    for key, crux_key in mapping.items():
        block = crux.get(crux_key) or {}
        percentile = block.get("percentile")
        # CLS comes back x100 (per PSI convention). Normalize to float.
        value: float | None
        if percentile is None:
            value = None
        elif key == "cls":
            value = percentile / 100.0
        else:
            value = float(percentile)
        rating = block.get("category") or _rating_for(key, value)
        # Estimate % of users in POOR bucket from distributions array.
        pct_poor: float | None = None
        dists = block.get("distributions") or []
        if dists:
            try:
                pct_poor = round((dists[-1].get("proportion", 0) or 0) * 100)
            except (TypeError, ValueError):
                pct_poor = None
        out[key] = {"value": value, "rating": rating, "pct_poor": pct_poor}

    return out


def _check_id(metric: str) -> str:
    return f"performance_speed.{metric}"


def _finding_title(metric: str, rating: str) -> str:
    label = _METRIC_LABEL[metric]
    if rating == "POOR":
        return f"{label.capitalize()} is slow"
    if rating == "NEEDS_IMPROVEMENT":
        return f"{label.capitalize()} is slower than most sites"
    return label.capitalize()


def _finding_description(metric: str, rating: str, pct_poor: float | None) -> str:
    label = _METRIC_LABEL[metric]
    if rating == "POOR":
        if pct_poor and pct_poor >= 10:
            return (
                f"On {label}, about {int(pct_poor)}% of real visitors on mobile see a slow "
                "experience. Slow pages bounce; the first impression dies before it lands."
            )
        return (
            f"On {label}, most visitors see a slow experience. Slow pages bounce; the first "
            "impression dies before it lands."
        )
    if rating == "NEEDS_IMPROVEMENT":
        return (
            f"On {label}, your site is slower than most sites visitors compare you to. Not "
            "broken, but you're paying a tax in bounces and form abandonment."
        )
    return (
        f"On {label}, your site is in good shape for most mobile visitors. Keep an eye on "
        "this if you add new images or third-party scripts."
    )


def _tier_cap(tier: str) -> int:
    t = (tier or "").strip().lower()
    if t in {"pro", "pro package"}:
        return 99
    if t in {"scale up", "scale up package", "scaleup", "scale-up"}:
        return 3
    return 1  # Starter, Launch, free, anything else


def translate_to_findings(
    metrics: dict[str, dict[str, Any]],
    *,
    tier: str,
    platform: str,
) -> dict[str, Any]:
    """Apply the tier-cap and produce finding dicts + passed-check ids."""

    cap = _tier_cap(tier)

    actionable: list[tuple[str, dict[str, Any]]] = []
    passed_ids: list[str] = []

    for metric in ("lcp", "inp", "cls"):
        info = metrics.get(metric) or {}
        rating = info.get("rating", "UNKNOWN")
        if rating == "GOOD":
            passed_ids.append(_check_id(metric))
            continue
        if rating == "UNKNOWN":
            continue
        actionable.append((metric, info))

    # Sort worst-first (POOR before NEEDS_IMPROVEMENT, biggest pct_poor first).
    actionable.sort(
        key=lambda pair: (
            -_RATING_RANK.get(pair[1].get("rating", "UNKNOWN"), 0),
            -(pair[1].get("pct_poor") or 0),
        )
    )

    findings: list[dict[str, Any]] = []
    for metric, info in actionable[:cap]:
        rating = info.get("rating", "UNKNOWN")
        finding = {
            "id": _check_id(metric),
            "category": CATEGORY_ID,
            "title": _finding_title(metric, rating),
            "severity": _SEVERITY_BY_RATING.get(rating, "medium"),
            "what_we_saw": _finding_description(metric, rating, info.get("pct_poor")),
            "why_it_matters": (
                "Mobile visitors notice this in the first three seconds. Even small slowdowns "
                "cost completed signups."
            ),
            "fix_prompt": _fix_prompt_for(metric, platform),
            "tester": "The Phone-First Friend",
            "source": "external",
            "external_origin": "psi",
        }
        findings.append(finding)

    return {
        "findings": findings,
        "passed_check_ids": passed_ids,
        "failed_check_ids": [_check_id(m) for m, _ in actionable],
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_performance_speed(
    *,
    base_url: str,
    tier: str,
    platform: str = "generic",
    use_cache: bool = True,
) -> dict[str, Any]:
    """Fetch PSI for ``base_url`` and translate the result.

    Returns a dict with keys::

        {
          "findings": list[dict],
          "passed_check_ids": list[str],
          "failed_check_ids": list[str],
          "fetched": bool,
        }

    On any network / parse failure ``fetched`` is False and findings
    is empty -- the pipeline still produces a YAML.
    """
    psi = fetch_psi(base_url, use_cache=use_cache)
    fetched = psi is not None
    metrics = extract_metrics(psi)
    translated = translate_to_findings(metrics, tier=tier, platform=platform)
    translated["fetched"] = fetched
    return translated
