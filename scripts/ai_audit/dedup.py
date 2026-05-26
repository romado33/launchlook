"""Finding fingerprints + collision detection for Free -> Starter dedup.

Why this exists
---------------
Per ``docs/PRODUCT-DECISIONS.md`` section 2 the Free -> Starter conversion
is the most fragile moment in the funnel. A buyer who paid $19 cannot
re-read the 3 findings we already gave them for free; that would burn the
relationship the dedup rule exists to protect.

What this module does
---------------------
* ``fingerprint(finding)`` collapses a finding dict to a stable hash so
  the same issue surfaced twice (in the free audit and again by the paid
  Starter pipeline) compares equal even if the LLM phrased it slightly
  differently the second time.
* ``fingerprints(findings)`` is the vectorized version.
* ``collisions(new_findings, excluded_fingerprints)`` returns the subset
  of new findings whose fingerprint matches the excluded set.
* ``filter_out_collisions(new_findings, excluded_fingerprints)`` returns
  the kept subset (inverse of ``collisions``).
* ``render_exclude_block(excluded_fingerprints, prior_summaries=None)``
  renders the ``EXCLUDE_FINGERPRINTS`` block the pipeline pastes into
  the system prompt so the LLM knows what it MUST NOT re-surface.

Customer-visible boundary
-------------------------
None of these helpers ever cross the customer boundary. Per
``docs/SIMPLICITY-GUARDRAILS.md`` section 6 the dedup mechanism is not
mentioned in any report, email, or landing page; if a customer asks we
just say "your Starter findings build on your free preview."

Fingerprint shape
-----------------
Hash of (category_id + URL_path + a short normalized description). The
category id is the rule-pack id (e.g. ``trust_gaps`` from
``scripts/ai_audit/finding_categories.yaml``); the path keeps two
different mobile-layout findings on ``/`` vs ``/pricing`` distinct; and
the normalized description (lower-case, alpha-num only, first 120 chars)
catches the same issue described in slightly different words.

We intentionally use a short hex digest (16 hex chars / 64 bits) -- long
enough to make accidental collisions implausible (~1 in 1.8e19) but
short enough to keep the Notion rich-text payload readable when Rob
peeks at the row in the Notion UI.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable
from urllib.parse import urlparse

__all__ = [
    "fingerprint",
    "fingerprints",
    "collisions",
    "filter_out_collisions",
    "render_exclude_block",
    "normalize_description",
    "extract_path",
]

# Length of the hex digest stored per finding. 16 chars = 64 bits.
_DIGEST_LEN = 16

# Strip everything that isn't a word char or whitespace, then collapse
# runs of whitespace to single spaces. Done in lower case so casing
# variations don't create false-negatives.
_NON_WORD = re.compile(r"[^\w\s]+", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")

# A finding's "description" surface for normalization. We prefer the
# longer "what we saw" body (more discriminating than the title alone)
# but fall back to title if that's all we have.
_DESCRIPTION_KEYS = ("what_we_saw", "description", "body", "title")

# How many normalized chars from the description we feed into the hash.
# Short enough that a few wording tweaks don't change the hash; long
# enough that two genuinely different findings in the same category
# don't collapse together.
_DESC_HASH_LEN = 120


def normalize_description(value: str) -> str:
    """Lower-case, strip punctuation, collapse whitespace, truncate.

    Designed so two LLM passes describing the same issue produce the
    same normalized string even with minor wording drift. NOT designed
    as a security primitive: an adversary who controls the LLM output
    can avoid collisions trivially, but the dedup rule is a UX promise,
    not a defense.
    """
    if not value:
        return ""
    text = value.strip().lower()
    text = _NON_WORD.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text[:_DESC_HASH_LEN]


def extract_path(finding: dict[str, Any], *, base_url: str | None = None) -> str:
    """Derive a stable "this is the page" path for a finding.

    Falls back through several common keys we use across the pipeline:
    explicit ``path``, ``url_path``, ``page``, or a full ``url`` we parse
    down to just the path. Returns "/" when nothing usable is present
    so a homepage finding without an explicit path still hashes stably.
    """
    for key in ("path", "url_path"):
        value = finding.get(key)
        if isinstance(value, str) and value.strip():
            return _canonical_path(value)
    page = finding.get("page")
    if isinstance(page, dict):
        for key in ("path", "url_path", "url"):
            value = page.get(key)
            if isinstance(value, str) and value.strip():
                return _canonical_path(_parse_path(value))
    url_value = finding.get("url")
    if isinstance(url_value, str) and url_value.strip():
        return _canonical_path(_parse_path(url_value))
    # Last resort: try the customer's base URL so two findings against
    # the same site without explicit paths still collide.
    if base_url:
        return _canonical_path(_parse_path(base_url))
    return "/"


def _parse_path(value: str) -> str:
    """Return path from a full URL or pass through a bare path."""
    if not value:
        return "/"
    if "://" in value:
        parsed = urlparse(value)
        return parsed.path or "/"
    return value


def _canonical_path(path: str) -> str:
    """Drop trailing slashes (except root) and lower-case the path."""
    path = (path or "/").strip().lower()
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path or "/"


def _category_id(finding: dict[str, Any]) -> str:
    """Return a stable category id for the finding.

    Prefers the explicit ``category_id`` field that the pipeline writes
    when it has one; falls back to ``category`` (which may be a slug or
    a display name) so legacy findings still hash. Empty becomes
    ``"uncategorized"`` so two unlabeled findings with the same path +
    description still collide.
    """
    for key in ("category_id", "category", "rule_id"):
        value = finding.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return "uncategorized"


def fingerprint(finding: dict[str, Any], *, base_url: str | None = None) -> str:
    """Stable hex digest for one finding. Length: ``_DIGEST_LEN`` (16)."""
    category = _category_id(finding)
    path = extract_path(finding, base_url=base_url)
    desc_source = ""
    for key in _DESCRIPTION_KEYS:
        value = finding.get(key)
        if isinstance(value, str) and value.strip():
            desc_source = value
            break
    desc = normalize_description(desc_source)
    blob = f"{category}\x1f{path}\x1f{desc}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:_DIGEST_LEN]


def fingerprints(findings: Iterable[dict[str, Any]], *, base_url: str | None = None) -> list[str]:
    """Fingerprint each finding, preserving input order. Skips non-dicts."""
    out: list[str] = []
    for f in findings or []:
        if isinstance(f, dict):
            out.append(fingerprint(f, base_url=base_url))
    return out


def collisions(
    new_findings: Iterable[dict[str, Any]],
    excluded_fingerprints: Iterable[str],
    *,
    base_url: str | None = None,
) -> list[dict[str, Any]]:
    """Return the subset of ``new_findings`` that collide with the exclude set."""
    excluded = {fp.strip() for fp in (excluded_fingerprints or []) if fp}
    if not excluded:
        return []
    out: list[dict[str, Any]] = []
    for f in new_findings or []:
        if not isinstance(f, dict):
            continue
        if fingerprint(f, base_url=base_url) in excluded:
            out.append(f)
    return out


def filter_out_collisions(
    new_findings: Iterable[dict[str, Any]],
    excluded_fingerprints: Iterable[str],
    *,
    base_url: str | None = None,
) -> list[dict[str, Any]]:
    """Return ``new_findings`` minus anything colliding with the exclude set."""
    excluded = {fp.strip() for fp in (excluded_fingerprints or []) if fp}
    if not excluded:
        return [f for f in (new_findings or []) if isinstance(f, dict)]
    out: list[dict[str, Any]] = []
    for f in new_findings or []:
        if not isinstance(f, dict):
            continue
        if fingerprint(f, base_url=base_url) not in excluded:
            out.append(f)
    return out


def render_exclude_block(
    excluded_fingerprints: Iterable[str],
    prior_summaries: Iterable[str] | None = None,
) -> str:
    """Render the ``EXCLUDE_FINGERPRINTS`` block for the LLM prompt.

    The prompt template references this via a single placeholder in
    ``scripts/ai_audit/prompts/finding_generation.txt``; if the
    placeholder is missing the pipeline appends the block to the bottom
    of the user prompt so existing prompt files keep working.

    ``prior_summaries`` is optional: if Rob's free-audit row has
    short human-readable summaries of the 3 prior findings we render
    them as a bulleted list under the hashes so the LLM has plain-
    English context (not just opaque hashes) for what NOT to surface.
    """
    fps = [fp.strip() for fp in (excluded_fingerprints or []) if fp and fp.strip()]
    if not fps:
        return ""

    lines = [
        "",
        "### EXCLUDE_FINGERPRINTS",
        "",
        (
            "These findings were already delivered to this customer in their "
            "free audit. Do NOT surface them again. Generate NEW findings "
            "focused on different categories or different specific instances."
        ),
        "",
        "Excluded fingerprints (do not repeat the underlying issues):",
    ]
    for fp in fps:
        lines.append(f"  - {fp}")

    summaries = [s.strip() for s in (prior_summaries or []) if s and s.strip()]
    if summaries:
        lines.append("")
        lines.append("Plain-English summary of the prior free findings:")
        for summary in summaries:
            lines.append(f"  - {summary}")

    lines.append("")
    lines.append(
        "If your draft includes a finding equivalent to any of the above, "
        "replace it with a genuinely different issue grounded in the "
        "screenshots and HTML extracts."
    )
    return "\n".join(lines)
