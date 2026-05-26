"""LaunchLook internal consistency audit.

Scans all customer-facing surfaces (landing/, customers/, templates/email/,
templates/report/, templates/qsg/, templates/handoff/, templates/confidence_check/,
templates/r/) for stale names, forbidden vocab, em-dashes, and persona / category
name mismatches against the canonical truth in:

  - docs/SIMPLICITY-GUARDRAILS.md (forbidden vocab, em-dash rule)
  - docs/PRODUCT-DECISIONS.md (tier ladder, pricing, finding caps)
  - docs/TESTERS-CAST.md (canonical 7-persona spelling)
  - scripts/ai_audit/finding_categories.yaml (buyer-facing finding names)
  - api/stripe-webhook.py (Stripe cents-to-tier mapping)

The script also sanity-checks the Stripe cents-to-tier routing in api/ + scripts/.

Usage:
  python scripts/consistency_check.py [--auto-fix-safe] [--report-only] [--report PATH]

Default mode is ``--report-only`` (no writes). ``--auto-fix-safe`` applies only the
zero-risk string-replace fixes (e.g. ``Full Package`` -> ``Scale Up Package``); every
other delta is written to docs/CONSISTENCY-AUDIT-REPORT.md for human review.

Exit code is 0 if no ``critical`` issues remain after auto-fix, 1 otherwise, so the
script can later be wired in as a pre-commit hook.
"""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Scope definitions
# ---------------------------------------------------------------------------

# Files where stale tier names, persona names, category names, and forbidden
# vocab must be absent. customers/*.yaml is in scope because the example YAMLs
# are referenced by operators day-to-day; their comments must stay accurate.
STALE_NAME_GLOBS: tuple[str, ...] = (
    "landing/*.html",
    "landing/*.js",
    "landing/assets/*.js",
    "customers/*.yaml",
    "templates/email/*.j2",
    "templates/report/*.j2",
    "templates/qsg/*.j2",
    "templates/handoff/*.j2",
    "templates/handoff/*.md.j2",
    "templates/confidence_check/*.j2",
    "templates/r/*.j2",
)

# Em-dashes are dangerous only on rendered customer surfaces. Internal dev docs
# and markdown notes are allowed em-dashes per SIMPLICITY-GUARDRAILS section 6.
EM_DASH_GLOBS: tuple[str, ...] = (
    "landing/*.html",
    "landing/*.js",
    "landing/assets/*.js",
    "templates/email/*.j2",
    "templates/report/*.j2",
    "templates/qsg/*.j2",
    "templates/handoff/*.j2",
    "templates/handoff/*.md.j2",
    "templates/confidence_check/*.j2",
    "templates/r/*.j2",
)

# Stripe pricing checks are code-only.
STRIPE_CODE_GLOBS: tuple[str, ...] = (
    "api/*.py",
    "scripts/*.py",
)


# ---------------------------------------------------------------------------
# Canonical truth (locked to docs/PRODUCT-DECISIONS.md section 1)
# ---------------------------------------------------------------------------

TIER_LADDER = {
    "Starter Package": {"price": 19, "cents": 1900, "cap": 10, "validity_days": 30},
    "Scale Up Package": {"price": 49, "cents": 4900, "cap": 30, "validity_days": 90},
    "Pro Package": {"price": 99, "cents": 9900, "cap": 40, "validity_days": 180},
}

CANONICAL_PERSONAS = (
    "The Skeptic",
    "The Klutz",
    "The Snoop",
    "The Tourist",
    "The Phone-First Friend",
    "The Saboteur",
    "The Stranger Who Tried to Sign Up",
)

CANONICAL_FINDING_CATEGORIES = (
    "trust signals & legal pages",
    "broken buttons & dead links",
    "mobile layout issues",
    "confusing or placeholder text",
    "obvious visible risks",
    "user data isolation",
    "copy that sounds AI-written",
    "growth-readiness checks",
    "common legal must-haves",
    "performance & speed",
    "accessibility checks",
    "form & signup flows",
    "dev tools and test data on the live site",
)


# ---------------------------------------------------------------------------
# Issue model
# ---------------------------------------------------------------------------

KIND_STALE_TIER = "stale_tier_name"
KIND_FORBIDDEN_VOCAB = "forbidden_vocab"
KIND_EM_DASH = "em_dash_customer_facing"
KIND_PERSONA_TYPO = "persona_typo"
KIND_CATEGORY_TYPO = "category_typo"
KIND_STALE_PRICE = "stale_price"
KIND_STRIPE_ROUTING = "stripe_routing_inconsistency"

SEV_AUTO = "auto_safe"
SEV_HUMAN = "human_review"
SEV_CRITICAL = "critical"


@dataclass
class Issue:
    file: str
    line: int
    snippet: str
    kind: str
    severity: str
    suggested_fix: str
    auto_fixable: bool
    # Optional: a literal (old, new) string-replace pair the auto-fixer can apply
    # to the matched line.
    fix_replace_pair: tuple[str, str] | None = None


# ---------------------------------------------------------------------------
# Stale tier name fixers (auto-safe)
# ---------------------------------------------------------------------------

# Order matters: longer / more specific patterns first so they win over the
# more general ones below.
STALE_TIER_AUTO_FIXES: tuple[tuple[str, str, str], ...] = (
    # (old_literal, new_literal, plain-English explanation)
    ("Get Full Package ($49)", "Get Scale Up Package ($49)", "Renamed Full Package to Scale Up Package per PRODUCT-DECISIONS section 1."),
    ("Get Full Package", "Get Scale Up Package", "Renamed Full Package to Scale Up Package per PRODUCT-DECISIONS section 1."),
    ("Full Package ($49)", "Scale Up Package ($49)", "Renamed Full Package to Scale Up Package per PRODUCT-DECISIONS section 1."),
    ("Full Package", "Scale Up Package", "Renamed Full Package to Scale Up Package per PRODUCT-DECISIONS section 1."),
    ("Full ($49)", "Scale Up ($49)", "Renamed Full to Scale Up per PRODUCT-DECISIONS section 1."),
    ("Full $49", "Scale Up $49", "Renamed Full to Scale Up per PRODUCT-DECISIONS section 1."),
    ("Everything in Full,", "Everything in Scale Up,", "Renamed Full to Scale Up per PRODUCT-DECISIONS section 1."),
    ("Everything in Full ", "Everything in Scale Up ", "Renamed Full to Scale Up per PRODUCT-DECISIONS section 1."),
    ("everything in Full plus", "everything in Scale Up plus", "Renamed Full to Scale Up per PRODUCT-DECISIONS section 1."),
    ("Starter, Full, and Pro", "Starter, Scale Up, and Pro", "Renamed Full to Scale Up per PRODUCT-DECISIONS section 1."),
    ("Full (cap 25)", "Scale Up Package (cap 30)", "Renamed Full to Scale Up and updated cap to 30 per PRODUCT-DECISIONS section 1."),
)


# Stale tier mentions that require human judgement (no clean string-replace).
STALE_TIER_FLAGS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"\bShip Package\b"), "Deprecated tier (no longer in the ladder). Verify whether this should be Starter / Scale Up / Pro per PRODUCT-DECISIONS section 1.", SEV_HUMAN),
    (re.compile(r"\bFounder Roast\b"), "Cancelled tier per PRODUCT-DECISIONS section 3. Remove the reference or replace with Pro Package.", SEV_HUMAN),
    (re.compile(r"\bpriority triage\b"), "Replaced in q3 with plain-English Starter framing per PRODUCT-DECISIONS section 7. Replace with 'top issues' or 'the most important findings'.", SEV_HUMAN),
    (re.compile(r"\bPriority triage\b"), "Replaced in q3 with plain-English Starter framing per PRODUCT-DECISIONS section 7. Replace with 'Top issues' or similar.", SEV_HUMAN),
)


# Stale price patterns. The fixes here are HUMAN review only because changing
# a price string is a semantic change, not a name change.
STALE_PRICE_FLAGS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"Full \(\$29\)"), "Stale Full $29 price (bumped to $49). Replace with 'Scale Up ($49)' per PRODUCT-DECISIONS section 7."),
    (re.compile(r"Starter \(\$9\)"), "Stale Starter $9 price (bumped to $19). Replace with 'Starter ($19)' per PRODUCT-DECISIONS section 7."),
    (re.compile(r"Starter Package \(\$9\)"), "Stale Starter Package $9 price (bumped to $19). Replace with 'Starter Package ($19)' per PRODUCT-DECISIONS section 7."),
)


# Stale finding caps (now wrong vs PRODUCT-DECISIONS section 1).
STALE_CAP_FLAGS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bStarter caps at 7\b"), "Starter cap was bumped to 10. Update to 'Starter caps at 10' per PRODUCT-DECISIONS section 1."),
    (re.compile(r"\bcap 7\b"), "Starter cap was bumped to 10. Update reference to 'cap 10' per PRODUCT-DECISIONS section 1."),
    (re.compile(r"\bcap 25\b"), "Scale Up cap was bumped to 30 (was 25). Update reference to 'cap 30' per PRODUCT-DECISIONS section 1."),
    (re.compile(r"\btop 7 things\b"), "Starter cap was bumped to 10 (was 7). Verify whether '7' is still the right number to mention here."),
    (re.compile(r"\bthe 7 most important\b"), "Starter cap was bumped to 10 (was 7). Verify whether '7 most important' should be '10 most important'."),
    (re.compile(r"\b7 most important findings\b"), "Starter cap was bumped to 10 (was 7). Verify whether '7 most important' should be '10 most important'."),
    (re.compile(r"\bUp to 25\b"), "Scale Up cap was bumped to 30 (was 25). Verify whether 'Up to 25' should be 'Up to 30'."),
    (re.compile(r"\bup to 25 findings\b"), "Scale Up cap was bumped to 30 (was 25). Verify whether '25 findings' should be '30 findings'."),
)


# ---------------------------------------------------------------------------
# Forbidden vocabulary (SIMPLICITY-GUARDRAILS section 6)
# ---------------------------------------------------------------------------

# Each entry: (regex, suggested-replacement description, severity, optional auto-fix pair).
FORBIDDEN_VOCAB: tuple[tuple[re.Pattern[str], str, str, tuple[str, str] | None], ...] = (
    (re.compile(r"\bCore Web Vitals\b"), "Use 'performance & speed' per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bLCP\b"), "Internal CWV jargon. Use 'performance & speed' per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bINP\b"), "Internal CWV jargon. Use 'performance & speed' per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bCLS\b"), "Internal CWV jargon. Use 'performance & speed' per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\baxe-core\b"), "Use 'accessibility checks' per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bWCAG\b"), "Use 'accessibility checks' per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bScale-Ready\b"), "Use 'growth-readiness checks' (buyer-facing name from finding_categories.yaml).", SEV_HUMAN, None),
    (re.compile(r"\bCompliance-Lite\b"), "Use 'common legal must-haves' (buyer-facing name from finding_categories.yaml).", SEV_HUMAN, None),
    (re.compile(r"\bai_sounding\b"), "Internal taxonomy. Use 'copy that sounds AI-written'.", SEV_HUMAN, None),
    (re.compile(r"\bform-submit smoke test\b"), "Use 'form & signup flows' per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bsynthetic values\b"), "Internal jargon. Use plain-English 'safe test data' or similar.", SEV_HUMAN, None),
    (re.compile(r"\bround-trip\b"), "Internal jargon. Use plain-English 'whether the form actually delivers' or similar.", SEV_HUMAN, None),
    (re.compile(r"\bregression test\b"), "Use The Saboteur language: 'did anything break after AI changes' or similar.", SEV_HUMAN, None),
    (re.compile(r"\bunit test\b"), "Engineering jargon. Use plain English.", SEV_HUMAN, None),
    (re.compile(r"\bchaos monkey\b"), "Engineering jargon. Use The Saboteur language.", SEV_HUMAN, None),
    (re.compile(r"\bpentest\b"), "Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('this is not a pentest' style scope-statements are OK; flag exists so human can verify framing.)", SEV_HUMAN, None),
    (re.compile(r"\bsecurity audit\b"), "Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6. ('not a security audit' style scope-statement is OK.)", SEV_HUMAN, None),
    (re.compile(r"\bvulnerability scan\b"), "Security jargon. Reframe per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bpassionate\b"), "Corporate vocabulary per SIMPLICITY-GUARDRAILS section 6. Cut the sentence.", SEV_HUMAN, None),
    (re.compile(r"\bobsessed\b"), "Corporate vocabulary per SIMPLICITY-GUARDRAILS section 6. Cut the sentence.", SEV_HUMAN, None),
    (re.compile(r"\bfounder-led\b"), "Corporate vocabulary per SIMPLICITY-GUARDRAILS section 6. Cut the sentence.", SEV_HUMAN, None),
    (re.compile(r"\bstakeholder summary\b"), "Corporate vocabulary per SIMPLICITY-GUARDRAILS section 6. Cut the phrase.", SEV_HUMAN, None),
    (re.compile(r"\bexecutive overview\b"), "Corporate vocabulary per SIMPLICITY-GUARDRAILS section 6. Use 'verdict' instead.", SEV_HUMAN, None),
    (re.compile(r"\bcomprehensive deliverable\b"), "Corporate vocabulary per SIMPLICITY-GUARDRAILS section 6. Cut the phrase.", SEV_HUMAN, None),
    (re.compile(r"\bleverage\b"), "Vocabulary list per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\butilize\b"), "Vocabulary list per SIMPLICITY-GUARDRAILS section 6. Use 'use'.", SEV_HUMAN, None),
    (re.compile(r"\brobust\b"), "Vocabulary list per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bseamless\b"), "Vocabulary list per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bintuitive\b"), "Vocabulary list per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\belevate\b"), "Vocabulary list per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bempower\b"), "Vocabulary list per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    (re.compile(r"\bunlock\b"), "Vocabulary list per SIMPLICITY-GUARDRAILS section 6.", SEV_HUMAN, None),
    # 'comprehensive' is allowed only inside 'comprehensive checklist' (the literal
    # product name from PRODUCT-DECISIONS section 8). Anywhere else, flag it.
    (re.compile(r"\bcomprehensive (?!checklist)\w+", re.IGNORECASE), "Vocabulary list per SIMPLICITY-GUARDRAILS section 6. Only 'comprehensive checklist' is allowed (PRODUCT-DECISIONS section 8). Reword.", SEV_HUMAN, None),
    # 'AI scanner' is only allowed when explicitly framed as a competitor /
    # anti-pattern. We catch the standalone usage; reviewers eyeball the
    # framing.
    (re.compile(r"\bAI scanner\b"), "Per q3 settle, 'AI-powered audit + founder review' is the canonical positioning. Verify this usage is anti-pattern framing (talking about competitor tools), not self-description.", SEV_HUMAN, None),
)

# Persona typo patterns (case-sensitive + structure-sensitive).
PERSONA_TYPO_FLAGS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"\bPhone First Friend\b"), "Missing hyphen. Use 'The Phone-First Friend' (TESTERS-CAST.md).", "The Phone-First Friend"),
    (re.compile(r"\bphone first friend\b"), "Missing hyphen + lowercase. Use 'The Phone-First Friend' (TESTERS-CAST.md).", "The Phone-First Friend"),
    (re.compile(r"\bPhonefirst Friend\b"), "Spacing typo. Use 'The Phone-First Friend' (TESTERS-CAST.md).", "The Phone-First Friend"),
    (re.compile(r"\bStranger who Tried\b"), "Casing typo. Use 'The Stranger Who Tried to Sign Up' (TESTERS-CAST.md).", "The Stranger Who Tried to Sign Up"),
    (re.compile(r"\bThe stranger who tried\b"), "Casing typo. Use 'The Stranger Who Tried to Sign Up' (TESTERS-CAST.md).", "The Stranger Who Tried to Sign Up"),
)


# Stale internal category names that should never leak to customer surfaces.
STALE_CATEGORY_FLAGS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bTrust gaps\b"), "Internal taxonomy. Use buyer-facing 'trust signals & legal pages'."),
    (re.compile(r"\bBroken CTAs\b"), "Internal taxonomy. Use buyer-facing 'broken buttons & dead links'."),
    (re.compile(r"\bSecurity-lite\b"), "Internal taxonomy. Use buyer-facing 'obvious visible risks'."),
    (re.compile(r"\bMobile audit\b"), "Internal taxonomy. Use buyer-facing 'mobile layout issues'."),
    (re.compile(r"\bCopy & clarity\b"), "Internal taxonomy. Use buyer-facing 'confusing or placeholder text'."),
    (re.compile(r"\bCross-user data check\b"), "Internal taxonomy. Use buyer-facing 'user data isolation'."),
    (re.compile(r"\bAI-sounding copy detection\b"), "Internal taxonomy. Use buyer-facing 'copy that sounds AI-written'."),
)


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def discover_files(globs: Iterable[str]) -> list[Path]:
    seen: list[Path] = []
    for pattern in globs:
        for p in sorted(ROOT.glob(pattern)):
            if p.is_file() and p not in seen:
                seen.append(p)
    return seen


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def trim_snippet(line: str, span: tuple[int, int] | None = None, max_len: int = 160) -> str:
    snippet = line.rstrip("\n").strip()
    if len(snippet) <= max_len:
        return snippet
    if span is None:
        return snippet[:max_len] + "..."
    start = max(0, span[0] - 30)
    end = min(len(snippet), span[1] + 60)
    return ("..." if start > 0 else "") + snippet[start:end] + ("..." if end < len(snippet) else "")


# ---------------------------------------------------------------------------
# Customer-facing em-dash detection
# ---------------------------------------------------------------------------

# Em-dashes that are OK to keep even on customer surfaces:
#   * Inside HTML / Jinja comments (never rendered to a customer eye).
#   * Inside the "-- Rob" signature line (SIMPLICITY-GUARDRAILS section 5.2 exception).
#   * Inside JS-only comments (never rendered).
#   * Inside table empty-cell placeholders (the dash itself IS the visible
#     "no value here" UI token; replacing breaks the table layout). The audit
#     still surfaces these as informational entries.
EM_DASH_LINE_COMMENT_OPEN = ("//",)


def _is_signature_em_dash(line: str) -> bool:
    # Per SIMPLICITY-GUARDRAILS section 5.2, '-- Rob' (em-dash + Rob) at the
    # end of an email is the only exception.
    return bool(re.match(r"^\s*\u2014\s*Rob\b", line))


def _is_placeholder_em_dash(line: str) -> bool:
    """Detect '-- alone in a table cell or as a JS-filled placeholder."""
    stripped = line.strip()
    # Bare em-dash as the only visible content in a tag.
    if re.fullmatch(r".*>\s*\u2014\s*<.*", stripped):
        return True
    # Inline 'X: --' style cell content (mobile pricing table).
    if re.fullmatch(r".*:\s*\u2014\s*<.*", stripped):
        return True
    return False


def _classify_lines(text: str, suffix: str) -> list[bool]:
    """Return a parallel list[bool] flagging each line as 'inside a comment'.

    Handles block comments for the three relevant template families:
      * Jinja: {# ... #}
      * HTML:  <!-- ... -->
      * JS / CSS: /* ... */

    A line is flagged as inside-comment when ALL non-whitespace content on
    that line falls inside a block comment, OR the line is itself a
    self-contained line comment (//... at the start of a JS line).
    """
    is_comment: list[bool] = []
    in_jinja = False
    in_html = False
    in_js_block = False
    for raw_line in text.splitlines():
        line = raw_line
        line_has_real_content = False
        scan = line
        # Walk through the line, tracking transitions in / out of each
        # block-comment style. If any non-comment, non-whitespace character
        # appears, mark the line as carrying real content.
        i = 0
        while i < len(scan):
            ch = scan[i]
            if in_jinja:
                close = scan.find("#}", i)
                if close == -1:
                    i = len(scan)
                else:
                    in_jinja = False
                    i = close + 2
                continue
            if in_html:
                close = scan.find("-->", i)
                if close == -1:
                    i = len(scan)
                else:
                    in_html = False
                    i = close + 3
                continue
            if in_js_block:
                close = scan.find("*/", i)
                if close == -1:
                    i = len(scan)
                else:
                    in_js_block = False
                    i = close + 2
                continue
            # Not currently inside any block comment.
            if scan.startswith("{#", i):
                in_jinja = True
                i += 2
                continue
            if scan.startswith("<!--", i):
                in_html = True
                i += 4
                continue
            if scan.startswith("/*", i):
                in_js_block = True
                i += 2
                continue
            # Line comments (//) consume the rest of the line.
            if scan.startswith("//", i):
                # Anything on this line BEFORE i counted as content; from i
                # onward is comment.
                break
            if not ch.isspace():
                line_has_real_content = True
            i += 1
        # If the whole line ended up inside a block comment OR was empty
        # apart from whitespace and line-comments, treat as comment-only.
        is_comment.append(not line_has_real_content)
    return is_comment


def find_em_dashes(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)
    comment_mask = _classify_lines(text, path.suffix)
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "\u2014" not in line:
            continue
        if comment_mask[lineno - 1]:
            continue
        if _is_signature_em_dash(line):
            continue
        severity = SEV_HUMAN
        suggested = (
            "Customer-facing em-dash. Replace with a parenthetical, period, comma, "
            "or colon. Preserve voice and meaning. See SIMPLICITY-GUARDRAILS section 6."
        )
        if _is_placeholder_em_dash(line):
            severity = SEV_HUMAN
            suggested = (
                "Em-dash as a table / placeholder cell. Visible but structural. "
                "Consider replacing with '-' (hyphen) or 'none' if context allows. "
                "Lower priority than em-dashes inside prose."
            )
        issues.append(
            Issue(
                file=relative(path),
                line=lineno,
                snippet=trim_snippet(line),
                kind=KIND_EM_DASH,
                severity=severity,
                suggested_fix=suggested,
                auto_fixable=False,
            )
        )
    return issues


# ---------------------------------------------------------------------------
# Pattern-driven checks
# ---------------------------------------------------------------------------

def scan_with_patterns(
    path: Path,
    patterns: Iterable[tuple[re.Pattern[str], str, str]],
    kind: str,
) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)
    for lineno, line in enumerate(text.splitlines(), start=1):
        for entry in patterns:
            pattern, suggested, sev = entry
            match = pattern.search(line)
            if not match:
                continue
            issues.append(
                Issue(
                    file=relative(path),
                    line=lineno,
                    snippet=trim_snippet(line, match.span()),
                    kind=kind,
                    severity=sev,
                    suggested_fix=suggested,
                    auto_fixable=False,
                )
            )
    return issues


def scan_persona_typos(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern, message, canonical in PERSONA_TYPO_FLAGS:
            match = pattern.search(line)
            if not match:
                continue
            issues.append(
                Issue(
                    file=relative(path),
                    line=lineno,
                    snippet=trim_snippet(line, match.span()),
                    kind=KIND_PERSONA_TYPO,
                    severity=SEV_HUMAN,
                    suggested_fix=f"{message} (Canonical: '{canonical}'.)",
                    auto_fixable=False,
                )
            )
    return issues


def scan_stale_category_names(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)
    # Skip YAML keys: 'category: scale_ready_audit' style lines are internal
    # taxonomy IDs that the renderer maps to buyer-facing names. Only flag
    # internal names appearing in customer-facing prose.
    is_yaml = path.suffix in {".yaml", ".yml"}
    for lineno, line in enumerate(text.splitlines(), start=1):
        if is_yaml and re.match(r"\s*(category|display_name_internal|id|tester|source|tier_min)\s*:", line):
            continue
        for pattern, message in STALE_CATEGORY_FLAGS:
            match = pattern.search(line)
            if not match:
                continue
            issues.append(
                Issue(
                    file=relative(path),
                    line=lineno,
                    snippet=trim_snippet(line, match.span()),
                    kind=KIND_CATEGORY_TYPO,
                    severity=SEV_HUMAN,
                    suggested_fix=message,
                    auto_fixable=False,
                )
            )
    return issues


def scan_stale_prices(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern, message in STALE_PRICE_FLAGS:
            match = pattern.search(line)
            if not match:
                continue
            issues.append(
                Issue(
                    file=relative(path),
                    line=lineno,
                    snippet=trim_snippet(line, match.span()),
                    kind=KIND_STALE_PRICE,
                    severity=SEV_CRITICAL,
                    suggested_fix=message,
                    auto_fixable=False,
                )
            )
    return issues


def scan_stale_caps(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern, message in STALE_CAP_FLAGS:
            match = pattern.search(line)
            if not match:
                continue
            issues.append(
                Issue(
                    file=relative(path),
                    line=lineno,
                    snippet=trim_snippet(line, match.span()),
                    kind=KIND_STALE_TIER,
                    severity=SEV_HUMAN,
                    suggested_fix=message,
                    auto_fixable=False,
                )
            )
    return issues


# Auto-fixable stale tier names: detect-then-fix.
def scan_and_collect_auto_stale_tiers(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        for old, new, message in STALE_TIER_AUTO_FIXES:
            if old in line:
                issues.append(
                    Issue(
                        file=relative(path),
                        line=lineno,
                        snippet=trim_snippet(line),
                        kind=KIND_STALE_TIER,
                        severity=SEV_AUTO,
                        suggested_fix=f"{message} Replace '{old}' with '{new}'.",
                        auto_fixable=True,
                        fix_replace_pair=(old, new),
                    )
                )
    # Human-review stale tier flags (Ship Package, Founder Roast, etc.).
    issues.extend(scan_with_patterns(path, STALE_TIER_FLAGS, KIND_STALE_TIER))
    return issues


def scan_forbidden_vocab(path: Path) -> list[Issue]:
    """Forbidden vocab scoped to customer-facing surfaces.

    Skips:
      - YAML category/id/tier keys (internal taxonomy is fine in YAML data).
      - HTML / Jinja / JS block-comment lines (never rendered to a customer).
    """
    issues: list[Issue] = []
    text = read_text(path)
    is_yaml = path.suffix in {".yaml", ".yml"}
    comment_mask = _classify_lines(text, path.suffix)
    for lineno, line in enumerate(text.splitlines(), start=1):
        if is_yaml and re.match(r"\s*(category|display_name_internal|id|tester|source|tier_min)\s*:", line):
            continue
        if comment_mask[lineno - 1]:
            continue
        for pattern, message, sev, _fix in FORBIDDEN_VOCAB:
            match = pattern.search(line)
            if not match:
                continue
            issues.append(
                Issue(
                    file=relative(path),
                    line=lineno,
                    snippet=trim_snippet(line, match.span()),
                    kind=KIND_FORBIDDEN_VOCAB,
                    severity=sev,
                    suggested_fix=message,
                    auto_fixable=False,
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Stripe pricing routing check (api/, scripts/)
# ---------------------------------------------------------------------------

def scan_stripe_pricing() -> list[Issue]:
    """Verify cents-to-tier mapping in api/stripe-webhook.py aligns with canonical.

    Specifically checks that the live CENTS_TO_TIER dictionary maps:
      1900 -> Starter Package
      4900 -> Scale Up Package
      9900 -> Pro Package

    Also verifies metadata-discriminated routing exists for the q6 Confidence
    Check ($19 + product=confidence_check, $9 + product=confidence_check), the
    q17 badge re-verification ($9 + product=reverify), and the q18 Handoff
    Report add-on ($99 + product=handoff_report).
    """
    issues: list[Issue] = []
    webhook = ROOT / "api" / "stripe-webhook.py"
    if not webhook.exists():
        return [
            Issue(
                file="api/stripe-webhook.py",
                line=0,
                snippet="(file missing)",
                kind=KIND_STRIPE_ROUTING,
                severity=SEV_CRITICAL,
                suggested_fix="Stripe webhook file not present. Tier mapping cannot be audited.",
                auto_fixable=False,
            )
        ]
    text = read_text(webhook)
    expected_pairs = [
        ("1900: \"Starter Package\"", "Starter $19 maps to Starter Package."),
        ("4900: \"Scale Up Package\"", "Scale Up $49 maps to Scale Up Package."),
        ("9900: \"Pro Package\"", "Pro $99 maps to Pro Package."),
        ("CONFIDENCE_CHECK_METADATA_VALUE = \"confidence_check\"", "q6 Confidence Check metadata routing present."),
        ("REVERIFY_METADATA_VALUE = \"reverify\"", "q17 badge re-verification metadata routing present."),
        ("HANDOFF_REPORT_METADATA_VALUE = \"handoff_report\"", "q18 Handoff Report metadata routing present."),
    ]
    for needle, _explanation in expected_pairs:
        if needle not in text:
            issues.append(
                Issue(
                    file="api/stripe-webhook.py",
                    line=0,
                    snippet=needle,
                    kind=KIND_STRIPE_ROUTING,
                    severity=SEV_CRITICAL,
                    suggested_fix=(
                        f"Expected Stripe routing constant or mapping not found: '{needle}'. "
                        f"Verify api/stripe-webhook.py against PRODUCT-DECISIONS section 1."
                    ),
                    auto_fixable=False,
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Auto-fix application
# ---------------------------------------------------------------------------

def apply_auto_fixes(issues: list[Issue]) -> tuple[int, dict[str, int]]:
    """Apply every Issue whose auto_fixable=True. Returns (count, by_file_count)."""
    by_file: dict[str, list[Issue]] = {}
    for issue in issues:
        if issue.auto_fixable and issue.fix_replace_pair:
            by_file.setdefault(issue.file, []).append(issue)
    applied = 0
    file_count: dict[str, int] = {}
    for rel, file_issues in by_file.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = read_text(path)
        original = text
        # Deduplicate replacement pairs so we don't double-apply.
        pairs: list[tuple[str, str]] = []
        seen_pairs: set[tuple[str, str]] = set()
        for issue in file_issues:
            assert issue.fix_replace_pair is not None
            if issue.fix_replace_pair in seen_pairs:
                continue
            pairs.append(issue.fix_replace_pair)
            seen_pairs.add(issue.fix_replace_pair)
        # Apply longest-key-first to avoid partial overlap (we already ordered
        # STALE_TIER_AUTO_FIXES that way, but be defensive).
        pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
        for old, new in pairs:
            if old in text:
                replacements = text.count(old)
                text = text.replace(old, new)
                applied += replacements
                file_count[rel] = file_count.get(rel, 0) + replacements
        if text != original:
            path.write_text(text, encoding="utf-8", newline="\n")
    return applied, file_count


# ---------------------------------------------------------------------------
# Audit driver
# ---------------------------------------------------------------------------

def run_audit() -> list[Issue]:
    issues: list[Issue] = []

    # Stale names + caps + prices + categories: same scope.
    for path in discover_files(STALE_NAME_GLOBS):
        issues.extend(scan_and_collect_auto_stale_tiers(path))
        issues.extend(scan_stale_prices(path))
        issues.extend(scan_stale_caps(path))
        issues.extend(scan_stale_category_names(path))
        issues.extend(scan_persona_typos(path))
        issues.extend(scan_forbidden_vocab(path))

    # Em-dashes: customer-facing render scope only.
    for path in discover_files(EM_DASH_GLOBS):
        issues.extend(find_em_dashes(path))

    # Stripe routing.
    issues.extend(scan_stripe_pricing())

    return issues


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_report(
    *,
    issues_before: list[Issue],
    issues_after: list[Issue],
    auto_fixed_count: int,
    auto_fixed_by_file: dict[str, int],
    auto_fix_ran: bool,
    generated_iso: str,
) -> str:
    """Build the docs/CONSISTENCY-AUDIT-REPORT.md markdown body."""

    # Tally totals from the BEFORE-fix run (what existed when we started).
    by_kind_total: dict[str, int] = {}
    for issue in issues_before:
        by_kind_total[issue.kind] = by_kind_total.get(issue.kind, 0) + 1

    auto_fix_per_kind: dict[str, int] = {}
    for issue in issues_before:
        if issue.auto_fixable and issue.fix_replace_pair:
            auto_fix_per_kind[issue.kind] = auto_fix_per_kind.get(issue.kind, 0) + 1

    if auto_fix_ran:
        # Re-tally remaining issues against the AFTER list.
        remaining_per_kind: dict[str, int] = {}
        for issue in issues_after:
            remaining_per_kind[issue.kind] = remaining_per_kind.get(issue.kind, 0) + 1
    else:
        remaining_per_kind = {k: by_kind_total[k] for k in by_kind_total}

    summary_rows = []
    kind_labels = [
        (KIND_STALE_TIER, "Stale tier names + finding caps"),
        (KIND_STALE_PRICE, "Stale prices"),
        (KIND_FORBIDDEN_VOCAB, "Forbidden vocabulary"),
        (KIND_EM_DASH, "Customer-facing em-dashes"),
        (KIND_PERSONA_TYPO, "Persona typos"),
        (KIND_CATEGORY_TYPO, "Stale internal category names"),
        (KIND_STRIPE_ROUTING, "Stripe routing"),
    ]
    for kind, label in kind_labels:
        total = by_kind_total.get(kind, 0)
        autofixed = auto_fix_per_kind.get(kind, 0) if auto_fix_ran else 0
        remaining = remaining_per_kind.get(kind, 0)
        summary_rows.append(f"| {label} | {total} | {autofixed} | {remaining} |")

    needs_review_lines = []
    review_groupings: dict[str, list[Issue]] = {}
    for issue in issues_after:
        if issue.severity in (SEV_HUMAN, SEV_CRITICAL):
            review_groupings.setdefault(issue.kind, []).append(issue)

    def _render_group(kind: str, heading: str, suggested_action_col: str = "Suggested replacement") -> str:
        items = review_groupings.get(kind, [])
        if not items:
            return f"### {heading}\n\nNone remaining.\n"
        rows = []
        for issue in items:
            file_link = issue.file
            line = issue.line if issue.line else "-"
            snippet = issue.snippet.replace("|", "\\|")
            fix = issue.suggested_fix.replace("|", "\\|")
            rows.append(f"| `{file_link}` | {line} | {snippet} | {fix} |")
        body = (
            f"### {heading} ({len(items)} instance{'s' if len(items) != 1 else ''})\n\n"
            f"| File | Line | Context | {suggested_action_col} |\n"
            f"|---|---|---|---|\n"
            + "\n".join(rows)
            + "\n"
        )
        return body

    critical_issues = [i for i in issues_after if i.severity == SEV_CRITICAL]

    # Auto-fixed log: re-derive from BEFORE list (so the audit trail records
    # what got fixed even though those issues are now gone from AFTER).
    auto_fixed_log_rows: list[str] = []
    if auto_fix_ran:
        for issue in issues_before:
            if issue.auto_fixable and issue.fix_replace_pair:
                old, new = issue.fix_replace_pair
                auto_fixed_log_rows.append(
                    f"| `{issue.file}` | {issue.line} | `{old}` -> `{new}` | {issue.kind} |"
                )
    if not auto_fixed_log_rows:
        auto_fixed_log_body = "_No auto-safe fixes were applied (none qualified, or run was --report-only)._\n"
    else:
        auto_fixed_log_body = (
            "| File | Line | Fix | Kind |\n"
            "|---|---|---|---|\n"
            + "\n".join(auto_fixed_log_rows)
            + "\n"
        )

    files_modified_count = len(auto_fixed_by_file) if auto_fix_ran else 0

    parts: list[str] = []
    parts.append("# LaunchLook Internal Consistency Audit\n")
    parts.append(f"Generated: {generated_iso} by `scripts/consistency_check.py` (q-final-audit worker)\n")
    parts.append("")
    parts.append("Canonical truth sources audited against:")
    parts.append("- `docs/SIMPLICITY-GUARDRAILS.md` section 6 (forbidden vocab, em-dash rule)")
    parts.append("- `docs/PRODUCT-DECISIONS.md` section 1 (tier ladder, finding caps), section 7 (pricing)")
    parts.append("- `docs/TESTERS-CAST.md` (canonical 7-persona spelling)")
    parts.append("- `scripts/ai_audit/finding_categories.yaml` (buyer-facing finding category names)")
    parts.append("- `api/stripe-webhook.py` (Stripe cents-to-tier mapping)")
    parts.append("")
    parts.append("## Summary")
    parts.append("")
    parts.append("| Check | Total found | Auto-fixed | Needs review |")
    parts.append("|---|---|---|---|")
    parts.extend(summary_rows)
    parts.append("")
    parts.append(
        f"Auto-fix mode: {'**applied** in this run' if auto_fix_ran else '**not applied** (use `--auto-fix-safe` to write changes)'}. "
        f"Files modified by auto-fix: **{files_modified_count}**."
    )
    parts.append("")
    parts.append("## Auto-fixed (already applied)")
    parts.append("")
    parts.append(auto_fixed_log_body)
    parts.append("## Needs human review")
    parts.append("")
    parts.append(_render_group(KIND_STALE_TIER, "Stale tier names + finding caps"))
    parts.append(_render_group(KIND_STALE_PRICE, "Stale prices"))
    parts.append(_render_group(KIND_FORBIDDEN_VOCAB, "Forbidden vocab still on customer surfaces"))
    parts.append(_render_group(KIND_EM_DASH, "Em-dashes on customer-facing surfaces"))
    parts.append(_render_group(KIND_PERSONA_TYPO, "Persona typos"))
    parts.append(_render_group(KIND_CATEGORY_TYPO, "Stale internal category names"))
    parts.append(_render_group(KIND_STRIPE_ROUTING, "Stripe routing"))
    parts.append("## Critical issues (block ship -- must fix)")
    parts.append("")
    if not critical_issues:
        parts.append("None.")
    else:
        parts.append("| File | Line | Context | Suggested action |")
        parts.append("|---|---|---|---|")
        for issue in critical_issues:
            snippet = issue.snippet.replace("|", "\\|")
            fix = issue.suggested_fix.replace("|", "\\|")
            parts.append(f"| `{issue.file}` | {issue.line if issue.line else '-'} | {snippet} | {fix} |")
    parts.append("")
    parts.append("## Notes for q-final-lint")
    parts.append("")
    parts.append("- After this audit, run linters as planned.")
    parts.append("- Em-dash replacements are stylistic: review the surrounding sentence and pick parenthetical / period / comma / colon. Do not bulk-replace globally; meaning gets lost.")
    parts.append("- Stale finding caps (Starter cap=10, Scale Up cap=30) and Starter framing copy are surfaced for human review; pricing-page numbers that conflict with PRODUCT-DECISIONS section 1 need a copywriting pass, not a string-replace.")
    parts.append(f"- Re-run this audit at any time with `python scripts/consistency_check.py --report-only` to verify a fix.")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--auto-fix-safe",
        action="store_true",
        help="Apply safe auto-fix string replacements (Full Package -> Scale Up Package, etc.).",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Default: scan + write report, do not modify any source files.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "CONSISTENCY-AUDIT-REPORT.md",
        help="Where to write the audit markdown report. Default: docs/CONSISTENCY-AUDIT-REPORT.md.",
    )
    args = parser.parse_args(argv)

    if args.auto_fix_safe and args.report_only:
        parser.error("--auto-fix-safe and --report-only are mutually exclusive.")

    issues_before = run_audit()
    auto_fix_ran = args.auto_fix_safe
    auto_fixed_count = 0
    auto_fixed_by_file: dict[str, int] = {}
    if auto_fix_ran:
        auto_fixed_count, auto_fixed_by_file = apply_auto_fixes(issues_before)
        issues_after = run_audit()
    else:
        issues_after = list(issues_before)

    generated_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = render_report(
        issues_before=issues_before,
        issues_after=issues_after,
        auto_fixed_count=auto_fixed_count,
        auto_fixed_by_file=auto_fixed_by_file,
        auto_fix_ran=auto_fix_ran,
        generated_iso=generated_iso,
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8", newline="\n")

    critical = sum(1 for i in issues_after if i.severity == SEV_CRITICAL)
    human = sum(1 for i in issues_after if i.severity == SEV_HUMAN)

    print(f"[consistency_check] Issues before fix: {len(issues_before)}")
    if auto_fix_ran:
        print(f"[consistency_check] Auto-safe fixes applied: {auto_fixed_count} replacement(s) across {len(auto_fixed_by_file)} file(s)")
        print(f"[consistency_check] Issues after fix:  {len(issues_after)}")
    print(f"[consistency_check] Needs human review:  {human}")
    print(f"[consistency_check] Critical (block ship): {critical}")
    print(f"[consistency_check] Report: {relative(args.report)}")

    return 0 if critical == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
