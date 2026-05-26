"""End-to-end AI audit pipeline.

Public entry points:

* ``run(...)``                — orchestrates the full pipeline (capture →
                                 prescreen → HTML extract → LLM → YAML).
* ``regenerate_finding(...)`` — refresh a single finding, used by the
                                 audit UI's per-finding 🔄 button.
* ``load_tier_caps()``        — read the tier-cap values out of
                                 ``scripts/deliver_report.py`` so the
                                 default cap auto-tracks future changes.

The pipeline never modifies an existing YAML in place: ``run`` writes
``customers/{slug}.yaml`` (overwriting if present), and the regenerate
helper returns a single dict that the caller patches into its own state.
"""

from __future__ import annotations

import csv
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.audit_ui import yaml_writer  # noqa: E402

from . import cost_tracker  # noqa: E402
from . import feedback as feedback_log  # noqa: E402
from . import html_extract, llm_client  # noqa: E402
from . import security_lite  # noqa: E402
from . import performance_speed  # noqa: E402  -- pre-generated Core Web Vitals translator
from . import accessibility_axe  # noqa: E402  -- pre-generated axe-core findings
from . import dedup as dedup_module  # noqa: E402  -- free->Starter dedup helpers
from . import free_audit_lookup  # noqa: E402  -- Notion lookup for prior free-audit fingerprints


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
CATEGORIES_YAML = Path(__file__).resolve().parent / "finding_categories.yaml"

DEFAULT_TIER_CAPS = {"Starter Package": 10, "Scale Up Package": 30, "Pro Package": 40}

# Mapping from internal verdict labels to the emoji we render. The four
# labels are constrained by scripts/ai_audit/prompts/verdict_generation.txt
# and visible to the customer in templates/report/report.html.j2.
VERDICT_LABEL_EMOJI = {
    "Ready to share": "🟢",
    "Safe for friends/family testing": "🟡",
    "Needs fixes before launch": "🔴",
    "Do not invite real users yet": "🔴",
}
VERDICT_LABELS = tuple(VERDICT_LABEL_EMOJI.keys())

# ---------------------------------------------------------------------------
# Platform registry
# ---------------------------------------------------------------------------
#
# A "platform" selects which fix-prompt appendix is layered onto the base
# system prompt. The default ("vibe-coder") keeps the original behavior
# (Lovable / Bolt / v0 / Cursor / Replit / Base44). Adding a new platform
# is intentionally additive: register a slug here, point it at a prompt
# file under ``prompts/``, and the pipeline will start using it. The base
# system.txt is *never* rewritten -- it explicitly delegates platform-
# specific language to whichever appendix the pipeline appends at runtime.

VALID_PLATFORMS = ("vibe-coder", "webflow")
DEFAULT_PLATFORM = "vibe-coder"

PLATFORM_PROMPT_FILES: dict[str, str | None] = {
    "vibe-coder": None,  # base system.txt already speaks vibe-coder
    "webflow": "fix_prompt_webflow.txt",
}


def normalize_platform(value: str | None) -> str:
    """Normalize a free-form platform string to a known slug.

    Falls back to ``DEFAULT_PLATFORM`` when the input is empty or unknown,
    so the pipeline keeps working for unspecified / legacy inputs.
    """
    if not value:
        return DEFAULT_PLATFORM
    cleaned = value.strip().lower().replace("_", "-").replace(" ", "-")
    if cleaned in VALID_PLATFORMS:
        return cleaned
    return DEFAULT_PLATFORM

DELIVER_REPORT = REPO_ROOT / "scripts" / "deliver_report.py"
FINDINGS_CSV = REPO_ROOT / "findings_library" / "findings.csv"
SCREENSHOTS_OUT_ROOT = REPO_ROOT / "output" / "customers"   # capture_screenshots.py landing zone
SCREENSHOTS_MIRROR = REPO_ROOT / "screenshots"               # legacy + audit-UI lookup path


# ---------------------------------------------------------------------------
# Config / context dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CustomerContext:
    slug: str
    url: str
    tier: str
    builder: str
    first_name: str
    last_name: str = ""
    email: str = ""
    app_name: str = ""
    intake_notes: str = ""
    platform: str = DEFAULT_PLATFORM


@dataclass
class PipelineResult:
    slug: str
    yaml_path: Path | None
    yaml_text: str
    payload: dict[str, Any]
    provider: str
    model: str
    findings_count: int
    capture_meta: dict[str, Any] = field(default_factory=dict)
    prescreener_hits: list[dict[str, Any]] = field(default_factory=list)
    pages: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tier caps — discovered from deliver_report.py (same regex audit_ui uses)
# ---------------------------------------------------------------------------


# Match the dict-lookup cap form used by deliver_report.py:
#   cap = {"Starter Package": 10, "Scale Up Package": 30, "Pro Package": 40}.get(tier, 30)
# Captures every "Tier Name": <int> pair so the pipeline auto-tracks future
# tier additions without a code edit here.
_TIER_CAP_DICT_PATTERN = re.compile(
    r'cap\s*=\s*\{(?P<body>[^}]*)\}\s*\.get\(\s*tier'
)
_TIER_CAP_ENTRY_PATTERN = re.compile(
    r'["\'](?P<tier>[^"\']+)["\']\s*:\s*(?P<cap>\d+)'
)


def load_tier_caps() -> dict[str, int]:
    """Read tier caps from ``deliver_report.py``. Falls back to defaults."""
    try:
        text = DELIVER_REPORT.read_text(encoding="utf-8")
    except OSError:
        return dict(DEFAULT_TIER_CAPS)
    dict_match = _TIER_CAP_DICT_PATTERN.search(text)
    if not dict_match:
        return dict(DEFAULT_TIER_CAPS)
    parsed: dict[str, int] = {}
    for entry in _TIER_CAP_ENTRY_PATTERN.finditer(dict_match.group("body")):
        parsed[entry.group("tier")] = int(entry.group("cap"))
    return parsed or dict(DEFAULT_TIER_CAPS)


def load_finding_categories() -> list[dict[str, Any]]:
    """Read scripts/ai_audit/finding_categories.yaml. Falls back to []."""
    if not CATEGORIES_YAML.exists():
        return []
    try:
        import yaml  # noqa: WPS433  -- already a project dep
    except ImportError:
        print(
            "[categories] WARN: PyYAML missing, prompt will skip category list",
            file=sys.stderr,
        )
        return []
    try:
        data = yaml.safe_load(CATEGORIES_YAML.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        print(
            f"[categories] WARN: failed to parse finding_categories.yaml: {exc}",
            file=sys.stderr,
        )
        return []
    cats = data.get("categories") or []
    return [dict(c) for c in cats if isinstance(c, dict) and c.get("id")]


def render_categories_for_prompt(
    categories: list[dict[str, Any]],
    *,
    tier: str,
) -> str:
    """Format finding categories for ``{categories_list}`` in system.txt.

    Filters out tier-restricted categories the customer's tier doesn't
    reach (e.g. cross-user data check on Starter Package).
    """
    if not categories:
        return "(no categories registered; refer to severity rules below)"
    tier_rank = {"Starter Package": 1, "Scale Up Package": 2, "Pro Package": 3}
    customer_rank = tier_rank.get(tier, 1)
    blocks: list[str] = []
    for cat in categories:
        min_tier = cat.get("tier_min")
        if min_tier and customer_rank < tier_rank.get(min_tier, 0):
            continue
        cid = cat.get("id", "?")
        display = cat.get("display_name_buyer") or cat.get("display_name_internal") or cid
        sev = cat.get("severity_default", "medium")
        desc = (cat.get("description_for_llm") or "").strip()
        source = cat.get("source", "llm")
        tester = cat.get("tester", "")
        marker = " [external; merge, do not regenerate]" if source == "external" else ""
        header = f"- **{display}** (id: {cid}, severity_default: {sev}, tester: {tester}){marker}"
        body_lines = [header]
        if desc:
            for line in desc.split("\n"):
                line = line.rstrip()
                if line:
                    body_lines.append(f"    {line}")
        blocks.append("\n".join(body_lines))
    return "\n".join(blocks)


def load_findings_library() -> list[dict[str, Any]]:
    """Read findings.csv into a compact list for the prompt."""
    if not FINDINGS_CSV.exists():
        return []
    out: list[dict[str, Any]] = []
    with FINDINGS_CSV.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            out.append(
                {
                    "id": row.get("ID", "").strip(),
                    "name": row.get("Finding Name", "").strip(),
                    "category": row.get("Category", "").strip(),
                    "severity": row.get("Severity", "").strip(),
                    "explanation": (row.get("Customer Explanation") or "").strip(),
                }
            )
    return out


def _format_findings_library(library: list[dict[str, Any]]) -> str:
    if not library:
        return "(findings.csv unavailable)"
    lines = []
    for f in library:
        lines.append(
            f"  - [{f['severity']:<8}] {f['id']}  {f['name']}  ({f['category']})"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Stage 1: capture screenshots (delegates to existing module)
# ---------------------------------------------------------------------------


def stage_capture(customer_ctx: CustomerContext) -> dict[str, Any]:
    """Run capture_screenshots.py in-process and return the capture-meta dict."""
    from lib.customer_loader import Customer  # noqa: WPS433
    from scripts import capture_screenshots  # noqa: WPS433

    customer = Customer(
        page_id=None,
        slug=customer_ctx.slug,
        name=f"{customer_ctx.first_name} {customer_ctx.last_name}".strip() or customer_ctx.slug,
        email=customer_ctx.email,
        app_url=customer_ctx.url,
    )

    meta = capture_screenshots.capture(customer, list(capture_screenshots.DEFAULT_PATHS))
    try:
        capture_screenshots.render_index(customer, meta)
    except Exception as exc:  # noqa: BLE001
        print(f"[capture] WARN: index.html render failed: {exc}", file=sys.stderr)

    # Mirror the canonical screenshots dir to ``screenshots/{slug}`` for
    # the audit UI's screenshot lookup and the spec's documented path.
    _mirror_screenshots(customer)
    return meta


def _mirror_screenshots(customer) -> None:
    """Mirror ``output/customers/<slug>/screenshots`` → ``screenshots/<slug>``.

    The audit UI looks for ``screenshots/<slug>/<file>`` when rendering
    finding-card previews. We avoid moving the originals (other scripts
    expect them under ``output/customers/``) by copying.
    """
    import shutil

    src = customer.output_dir / "screenshots"
    if not src.exists():
        return
    dst = SCREENSHOTS_MIRROR / customer.slug
    dst.mkdir(parents=True, exist_ok=True)
    for shot in src.rglob("*.png"):
        rel = shot.relative_to(src)
        out_path = dst / rel.as_posix().replace("/", "_")
        try:
            shutil.copyfile(shot, out_path)
        except Exception as exc:  # noqa: BLE001
            print(f"  [capture] WARN: mirror copy failed for {shot}: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Stage 2: prescreener (delegates to existing module)
# ---------------------------------------------------------------------------


def stage_prescreen(customer_ctx: CustomerContext) -> list[dict[str, Any]]:
    """Run the regex prescreener and return its hits list.

    Returns ``[]`` on any error so the pipeline keeps going. The LLM still
    has screenshots + HTML; the prescreener is a hint, not a requirement.
    """
    try:
        from scripts import prescreen_findings  # noqa: WPS433
    except Exception as exc:  # noqa: BLE001
        print(f"[prescreen] skipped, import failed: {exc}", file=sys.stderr)
        return []

    try:
        findings = prescreen_findings.load_findings()
        pages = prescreen_findings.crawl(customer_ctx.url)
        hits = prescreen_findings.scan(pages, findings)
        print(f"[prescreen] {len(hits)} pattern hit(s)")
        return hits
    except SystemExit:
        return []
    except Exception as exc:  # noqa: BLE001
        print(f"[prescreen] WARN: skipped due to error: {exc}", file=sys.stderr)
        return []


def _format_prescreener_hits(hits: list[dict[str, Any]]) -> str:
    if not hits:
        return "(no regex pattern hits)"
    lines: list[str] = []
    for hit in hits[:40]:
        finding = hit.get("finding", {})
        page = hit.get("page", {})
        matches = hit.get("matches") or []
        sample = matches[0].get("text", "")[:60] if matches else ""
        lines.append(
            f"  - {finding.get('id','?')} [{finding.get('severity','?')}] "
            f"{finding.get('name','?')}  on {page.get('url','?')}  sample='{sample}'"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Stage 3: HTML extraction
# ---------------------------------------------------------------------------


def stage_html(customer_ctx: CustomerContext, paths: list[str] | None = None) -> list[dict[str, Any]]:
    return html_extract.extract_pages(customer_ctx.url, paths=paths)


# ---------------------------------------------------------------------------
# Stage 4: screenshot collection (for vision input)
# ---------------------------------------------------------------------------


# A handful of representative shots: home (both viewports), auth + privacy
# if they exist, plus 404 to show the model "what missing pages look like".
SCREENSHOT_PRIORITY = [
    ("desktop", "home"),
    ("mobile", "home"),
    ("desktop", "auth"),
    ("mobile", "auth"),
    ("desktop", "login"),
    ("desktop", "sign-in"),
    ("desktop", "sign-up"),
    ("desktop", "privacy"),
    ("desktop", "terms"),
    ("desktop", "nonexistent-test"),
]


def collect_screenshots(slug: str, *, max_shots: int = 8) -> list[tuple[str, Path]]:
    """Find the best PNGs for vision input.

    Looks under ``output/customers/<slug>/screenshots/<viewport>/<path>.png``
    first (what ``capture_screenshots.py`` writes), and falls back to the
    mirror at ``screenshots/<slug>/`` so the audit UI's existing convention
    keeps working.
    """
    src = SCREENSHOTS_OUT_ROOT / slug / "screenshots"
    found: list[tuple[str, Path]] = []
    seen: set[Path] = set()

    if src.exists():
        for viewport, name in SCREENSHOT_PRIORITY:
            candidate = src / viewport / f"{name}.png"
            if candidate.exists() and candidate not in seen:
                seen.add(candidate)
                found.append((f"{viewport} /{('' if name=='home' else name)}", candidate))
            if len(found) >= max_shots:
                break

    if not found:
        mirror = SCREENSHOTS_MIRROR / slug
        if mirror.exists():
            for png in sorted(mirror.glob("*.png")):
                if png not in seen:
                    seen.add(png)
                    found.append((png.stem, png))
                    if len(found) >= max_shots:
                        break

    return found


# ---------------------------------------------------------------------------
# Stage 5: LLM generation
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Persona tagging (q5/q13 - extend Snoop's pattern to all 7 personas)
# ---------------------------------------------------------------------------
#
# The 7 canonical personas live in docs/TESTERS-CAST.md. Each finding
# category in finding_categories.yaml declares which tester ("The Skeptic",
# "The Klutz", ...) owns it. The LLM is asked to emit a ``tag`` of the form
# "Caught by The {Persona}" on every finding (see prompts/system.txt). This
# helper validates / repairs the field so a missing or stale tag never leaks
# into the report PDF, per SIMPLICITY-GUARDRAILS section 3.4.

PERSONA_TAG_PREFIX = "Caught by "
FALLBACK_PERSONA = "The Skeptic"
FALLBACK_TAG = f"{PERSONA_TAG_PREFIX}{FALLBACK_PERSONA}"


def _build_category_tester_map(categories: list[dict[str, Any]]) -> dict[str, str]:
    """Return ``{category_id: 'The Persona'}`` from the loaded categories."""
    out: dict[str, str] = {}
    for cat in categories or []:
        cid = (cat.get("id") or "").strip()
        tester = (cat.get("tester") or "").strip()
        if cid and tester:
            out[cid] = tester
    return out


def apply_persona_tags(
    findings: list[dict[str, Any]],
    categories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ensure every finding carries a ``tag: 'Caught by The {Persona}'``.

    Pure helper: returns a new list of finding dicts; never mutates the
    inputs. Falls back to ``FALLBACK_TAG`` (and prints a stderr warning)
    when a finding has no recognisable category and no LLM-supplied tag.
    Snoop's externally-generated findings (security_lite.py) already carry
    a correct tag; this helper is a no-op for them.
    """
    cat_map = _build_category_tester_map(categories)
    out: list[dict[str, Any]] = []
    for finding in findings or []:
        if not isinstance(finding, dict):
            out.append(finding)
            continue
        f = dict(finding)
        cid = (f.get("category") or "").strip()
        existing_tag = (f.get("tag") or "").strip()

        canonical_tag = ""
        if cid:
            tester = cat_map.get(cid)
            if tester:
                canonical_tag = f"{PERSONA_TAG_PREFIX}{tester}"
            else:
                print(
                    f"[personas] WARN: category {cid!r} has no tester; "
                    f"falling back to {FALLBACK_TAG!r} for finding "
                    f"{f.get('title','?')!r}",
                    file=sys.stderr,
                )

        if canonical_tag:
            if existing_tag and existing_tag != canonical_tag:
                print(
                    f"[personas] WARN: LLM tag {existing_tag!r} did not "
                    f"match category {cid!r} expected {canonical_tag!r}; "
                    f"overriding for finding {f.get('title','?')!r}",
                    file=sys.stderr,
                )
            f["tag"] = canonical_tag
        elif existing_tag.startswith(PERSONA_TAG_PREFIX):
            f["tag"] = existing_tag
        else:
            print(
                f"[personas] WARN: finding {f.get('title','?')!r} has no "
                f"category and no usable tag; defaulting to {FALLBACK_TAG!r}",
                file=sys.stderr,
            )
            f["tag"] = FALLBACK_TAG
        out.append(f)
    return out


def _read_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")


def build_system_prompt(
    platform: str = DEFAULT_PLATFORM,
    *,
    tier: str = "Starter Package",
) -> str:
    """Return the system prompt layered with any platform-specific appendix.

    The base ``system.txt`` is always loaded and templated with the
    active finding categories (loaded from
    ``scripts/ai_audit/finding_categories.yaml``). If the platform has a
    registered appendix (see ``PLATFORM_PROMPT_FILES``), its contents
    are appended below a clear divider. The two layers compose
    additively:

    * **Categories** are data-driven; future workers add a category by
      editing the YAML, not by rewriting the prompt.
    * **Platform appendices** layer on top to swap fix-prompt voice
      (Lovable, Bolt, v0, Cursor, Replit, Webflow Designer).
    """
    base = _read_prompt("system.txt")

    categories = load_finding_categories()
    categories_block = render_categories_for_prompt(categories, tier=tier)
    base = base.replace("{{ categories_list }}", categories_block)

    platform = normalize_platform(platform)
    appendix_file = PLATFORM_PROMPT_FILES.get(platform)
    if not appendix_file:
        return base
    appendix_path = PROMPTS_DIR / appendix_file
    if not appendix_path.exists():
        return base
    appendix = appendix_path.read_text(encoding="utf-8")
    return (
        f"{base}\n\n"
        f"==========================================================================\n"
        f"PLATFORM APPENDIX — {platform.upper()}\n"
        f"==========================================================================\n"
        f"\n"
        f"The customer's platform is **{platform}**. Apply the rules below in\n"
        f"addition to (not in replacement of) the base system prompt. When the\n"
        f"base prompt and this appendix conflict, the appendix wins for any\n"
        f"language pointed at the customer's editing environment (fix_prompt\n"
        f"voice, platform-specific finding categories). Severity definitions,\n"
        f"grounding rules, and voice rules from the base prompt always apply.\n"
        f"\n"
        f"{appendix}\n"
    )


# Webflow-specific finding-category guidance appended to the user prompt
# (not the system prompt) so it sits next to the per-customer evidence and
# can be tuned per audit without rewriting the platform appendix.
_WEBFLOW_FINDING_CHECKS = """
### Webflow-specific check list (apply when platform=webflow)

Beyond the standard pre-launch checks, look hard for these Webflow-only
failure modes. Each one is high-value because Webflow's own Designer does
not warn the customer when it happens:

1. **Silent form submission failure (post-Nov 2024)**. For every <form> on
   the site, check whether the form has a Webflow Form Notification email
   configured. If the form action points at Webflow's standard handler but
   no notification recipient is set, submissions disappear silently after
   showing a success message. Flag any form whose evidence suggests this
   pattern (e.g., missing form name attribute, default success/error blocks
   still present, no JSON-LD organization contact pointing to a real
   inbox). Severity: critical when contact / lead form, high otherwise.

2. **Accidental noindex / robots block on a production page**. Inspect the
   <head> for `<meta name="robots" content="noindex">` on pages that
   appear to be production (homepage, about, contact, pricing, services,
   collection landing pages). Also check the robots.txt body if visible
   in the page-status summary for a wildcard `Disallow: /` on the live
   host. Severity: critical when on the homepage, high otherwise.

3. **Missing or malformed JSON-LD schema**. Check whether the page exposes
   a `<script type="application/ld+json">` block. For business / agency /
   product pages, the absence of Organization, LocalBusiness, Product, or
   Article schema (whichever fits) is a finding. Severity: medium unless
   the customer's intake notes mention SEO as a goal, then high.

4. **Designer-to-live mismatch indicators**. Flag any of: visible "Lorem
   ipsum" placeholder text, default Webflow component placeholders like
   "Heading goes here" or "Button text," literal "Your text goes here" in
   CMS-bound elements, broken Symbol instances (empty interior), elements
   marked hidden in Designer that render visible on the live URL.

5. **Mobile breakpoint breakage at Webflow's three native breakpoints**:
   991px (Tablet), 767px (Mobile landscape), 478px (Mobile portrait). If
   the mobile screenshot at 390px width shows overflow, broken nav, text
   overlap, or hidden CTAs, flag the most likely breakpoint origin in the
   fix_prompt so the customer knows which breakpoint to switch to in the
   Designer.

These are *categories*, not personas. Other workers may layer persona
tagging on top of findings later; do not assign persona names in the
finding payload.
"""


def _maybe_append_webflow_checks(prompt: str, platform: str) -> str:
    if normalize_platform(platform) != "webflow":
        return prompt
    return f"{prompt}\n{_WEBFLOW_FINDING_CHECKS}"


def _tier_guidance(tier: str, cap: int) -> str:
    if tier == "Starter Package":
        return (
            f"Starter Package surfaces the most impactful pre-launch issues. "
            f"Return at most {cap} findings: the things a first-time visitor "
            "would notice within the first minute. Skew toward criticals and "
            "highs. If the app is clean, return fewer."
        )
    if tier == "Scale Up Package":
        return (
            f"Scale Up Package is the deeper pass. Return up to {cap} findings "
            "spanning trust, polish, mobile, security-lite, and broken "
            "functionality. Includes the cross-user data isolation check. "
            "Include lower-severity polish items the customer paid extra for. "
            "Still drop any finding you cannot ground in real evidence."
        )
    return (
        f"Pro Package is the deepest pass. Return up to {cap} findings across "
        "every category, plus an integrations review (auth, payments, email, "
        "analytics) for misconfiguration. Drop any finding you cannot ground "
        "in real evidence."
    )


def build_finding_user_prompt(
    customer_ctx: CustomerContext,
    *,
    cap: int,
    n_screenshots: int,
    prescreener_hits: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    library: list[dict[str, Any]],
    exclude_block: str = "",
) -> str:
    template = _read_prompt("finding_generation.txt")
    body = template.format(
        max_findings=cap,
        tier=customer_ctx.tier,
        customer_name=f"{customer_ctx.first_name} {customer_ctx.last_name}".strip(),
        app_name=customer_ctx.app_name,
        app_url=customer_ctx.url,
        builder=customer_ctx.builder,
        intake_notes=customer_ctx.intake_notes or "(none provided)",
        tier_guidance=_tier_guidance(customer_ctx.tier, cap),
        n_screenshots=n_screenshots,
        findings_library=_format_findings_library(library),
        prescreener_hits=_format_prescreener_hits(prescreener_hits),
        html_extracts=html_extract.render_pages_for_prompt(pages),
        page_status_summary=html_extract.render_status_summary(pages),
    )
    if exclude_block:
        # Appended below the rendered template so prompt files keep
        # working without a placeholder edit. See
        # docs/AI-AUDIT-PIPELINE.md (Free -> Starter dedup) for the
        # full contract.
        body = body.rstrip() + "\n\n" + exclude_block.strip() + "\n"
    return body


def build_verdict_user_prompt(
    customer_ctx: CustomerContext,
    *,
    findings: list[dict[str, Any]],
) -> str:
    template = _read_prompt("verdict_generation.txt")
    summary_lines = []
    for f in findings:
        summary_lines.append(
            f"  - [{f.get('severity','?'):<8}] {f.get('title','?')}"
        )
    return template.format(
        app_name=customer_ctx.app_name,
        findings_summary="\n".join(summary_lines) if summary_lines else "  (no findings)",
    )


def build_qsg_user_prompt(
    customer_ctx: CustomerContext,
    *,
    pages: list[dict[str, Any]],
) -> str:
    template = _read_prompt("qsg_generation.txt")
    return template.format(
        app_name=customer_ctx.app_name,
        app_url=customer_ctx.url,
        builder=customer_ctx.builder,
    )


def _default_verdict(findings: list[dict[str, Any]], app_name: str) -> dict[str, Any]:
    """Heuristic fallback when the LLM verdict call fails.

    Picks one of the four canonical labels in
    ``scripts/ai_audit/prompts/verdict_generation.txt`` based on the
    finding mix. The label is the customer-facing hero phrase; the
    emoji is a small accent.
    """
    has_critical = any((f.get("severity") or "").lower() == "critical" for f in findings)
    high_count = sum(1 for f in findings if (f.get("severity") or "").lower() == "high")
    has_security = any(
        (f.get("category") or "") == security_lite.CATEGORY_ID
        and (f.get("severity") or "").lower() in {"critical", "high"}
        for f in findings
    )

    if has_security or has_critical and high_count >= 1:
        label = "Do not invite real users yet"
        summary = "Critical safety or auth issues to clear before any real users."
    elif has_critical:
        label = "Needs fixes before launch"
        summary = "One critical blocker to fix before sharing the URL more widely."
    elif high_count >= 2:
        label = "Needs fixes before launch"
        summary = "Multiple high-impact issues to clear before going public."
    elif high_count == 1:
        label = "Safe for friends/family testing"
        summary = "Looks workable; clean up the high-impact item before going wider."
    else:
        label = "Ready to share"
        summary = "No blockers; a couple of polish items to round it out."

    return {
        "emoji": VERDICT_LABEL_EMOJI[label],
        "label": label,
        "summary": summary,
        "narrative": (
            f"{app_name} is in reasonable shape. The findings below are "
            "sorted by severity. Fix anything marked critical before sharing "
            "the URL more widely, then work down the list as time allows."
        ),
    }


def _normalize_verdict(verdict: dict[str, Any]) -> dict[str, Any]:
    """Coerce an LLM verdict dict to the canonical 4-label vocabulary.

    The schema constrains ``label`` to one of the four allowed values,
    but we still defend against drift (missing label, wrong casing, an
    extra trailing period) so the report template can render
    deterministically.
    """
    out = dict(verdict or {})
    raw_label = (out.get("label") or "").strip()
    canonical = ""
    for option in VERDICT_LABELS:
        if raw_label.lower().rstrip(".") == option.lower():
            canonical = option
            break
    if not canonical:
        # Fall back to the closest match by emoji if the label is missing.
        emoji = (out.get("emoji") or "").strip()
        if emoji == "🟢":
            canonical = "Ready to share"
        elif emoji == "🟡":
            canonical = "Safe for friends/family testing"
        elif emoji == "🔴":
            canonical = "Needs fixes before launch"
        else:
            canonical = "Safe for friends/family testing"
    out["label"] = canonical
    out["emoji"] = VERDICT_LABEL_EMOJI[canonical]
    return out


def compute_passed_checks(
    *,
    findings: list[dict[str, Any]],
    snoop_passed_ids: list[str],
    categories: list[dict[str, Any]],
    tier: str,
    external_passed_ids: dict[str, list[str]] | None = None,
) -> list[str]:
    """Build the customer-facing "What's working" list.

    A category passes when it has no Critical/High finding in the final
    list (Snoop's externally-passed checks short-circuit the security-lite
    category to "passing" when none of its findings landed). We emit the
    plain-English buyer name for each passing category, capped at 8 lines
    so the report stays scannable per SIMPLICITY-GUARDRAILS §3.7.
    """
    if not categories:
        return []

    tier_rank = {"Starter Package": 1, "Scale Up Package": 2, "Pro Package": 3}
    customer_rank = tier_rank.get(tier, 1)

    blocking = {"critical", "high", "medium"}

    by_category: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        cid = (f.get("category") or "").strip()
        if cid:
            by_category.setdefault(cid, []).append(f)

    passed: list[str] = []
    for cat in categories:
        cid = cat.get("id")
        min_tier = cat.get("tier_min")
        if min_tier and customer_rank < tier_rank.get(min_tier, 0):
            continue
        cat_findings = by_category.get(cid, [])
        has_blocker = any(
            (f.get("severity") or "").lower() in blocking for f in cat_findings
        )
        if has_blocker:
            continue
        # External-source categories must have actually run cleanly (not
        # just be absent from findings because the LLM didn't tag anything
        # with this category). The security_lite gate is kept for back-compat;
        # q14 + q16 categories are gated via external_passed_ids.
        if cid == security_lite.CATEGORY_ID:
            if not snoop_passed_ids:
                continue
        elif (cat.get("source") == "external") and external_passed_ids is not None:
            if not external_passed_ids.get(cid):
                continue
        display = cat.get("display_name_buyer") or cat.get("display_name_internal") or cid
        passed.append(display.strip().rstrip("."))
    return passed[:8]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run(
    customer_ctx: CustomerContext,
    *,
    provider: str = "auto",
    skip_capture: bool = False,
    skip_prescreen: bool = False,
    dry_run: bool = False,
    max_findings: int | None = None,
) -> PipelineResult:
    """Run the full pipeline. Returns the result (YAML text + payload)."""
    tier_caps = load_tier_caps()
    cap = max_findings or tier_caps.get(customer_ctx.tier, 7)
    print(f"[pipeline] tier={customer_ctx.tier!r} cap={cap} provider={provider!r}")

    # ---- 1. Capture ----
    capture_meta: dict[str, Any] = {}
    if not skip_capture:
        try:
            capture_meta = stage_capture(customer_ctx)
        except SystemExit as exc:
            print(f"[capture] aborted: {exc}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"[capture] WARN: failed: {exc}", file=sys.stderr)
    else:
        print("[capture] skipped (--skip-capture)")

    # ---- 2. Prescreen ----
    if not skip_prescreen:
        prescreener_hits = stage_prescreen(customer_ctx)
    else:
        print("[prescreen] skipped (--skip-prescreen)")
        prescreener_hits = []

    # ---- 3. HTML extract ----
    try:
        pages = stage_html(customer_ctx)
    except Exception as exc:  # noqa: BLE001
        print(f"[html] WARN: extraction failed: {exc}", file=sys.stderr)
        pages = []

    # ---- 3b. Snoop's security-lite checks (per docs/TESTERS-CAST.md) ----
    # Runs after the HTML extract (so cred-leak checks can scan the
    # rendered HTML) and before the LLM call. Any findings here are
    # merged into the LLM output below. Failures of individual checks
    # are non-fatal: pipeline still produces a YAML.
    try:
        snoop = security_lite.run_security_lite(
            base_url=customer_ctx.url,
            pages=pages,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[security-lite] WARN: skipped: {exc}", file=sys.stderr)
        snoop = {"findings": [], "passed_check_ids": [], "failed_check_ids": []}
    print(
        f"[security-lite] {len(snoop['findings'])} finding(s); "
        f"passed: {snoop['passed_check_ids']}; failed: {snoop['failed_check_ids']}"
    )

    # ---- 3c. Performance & speed (Core Web Vitals translator, q14) ----
    # Pre-generated by performance_speed.py from the PageSpeed Insights
    # API (24h cached so re-runs do not burn the 25K daily quota).
    # Buyer-facing name is "performance & speed"; internal acronyms
    # never cross the customer surface per SIMPLICITY-GUARDRAILS section 6.
    try:
        perf = performance_speed.run_performance_speed(
            base_url=customer_ctx.url,
            tier=customer_ctx.tier,
            platform=(customer_ctx.builder or customer_ctx.platform or "generic"),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[performance] WARN: skipped: {exc}", file=sys.stderr)
        perf = {"findings": [], "passed_check_ids": [], "failed_check_ids": [], "fetched": False}
    print(
        f"[performance] fetched={perf.get('fetched')} "
        f"{len(perf['findings'])} finding(s); "
        f"passed: {perf['passed_check_ids']}; failed: {perf['failed_check_ids']}"
    )

    # ---- 3d. Accessibility checks (axe-core, q16) ----
    # Pre-generated by accessibility_axe.py loading axe-core into a
    # headless Playwright tab. Buyer-facing name is "accessibility
    # checks"; "axe-core" and "WCAG" never appear on customer surfaces
    # per SIMPLICITY-GUARDRAILS section 6.
    try:
        a11y = accessibility_axe.run_accessibility_axe(
            base_url=customer_ctx.url,
            tier=customer_ctx.tier,
            platform=(customer_ctx.builder or customer_ctx.platform or "generic"),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[a11y] WARN: skipped: {exc}", file=sys.stderr)
        a11y = {"findings": [], "passed_check_ids": [], "failed_check_ids": [], "ran": False}
    print(
        f"[a11y] ran={a11y.get('ran')} "
        f"{len(a11y['findings'])} finding(s); "
        f"passed: {a11y['passed_check_ids']}; failed: {a11y['failed_check_ids']}"
    )

    # ---- 4. Screenshots for vision ----
    screenshots = collect_screenshots(customer_ctx.slug)
    print(f"[vision] {len(screenshots)} screenshot(s) ready for LLM")

    # ---- 5. LLM ----
    stub_context = {
        "prescreener_hits": prescreener_hits,
        "builder": customer_ctx.builder,
        "app_name": customer_ctx.app_name,
    }
    client = llm_client.build_client(provider=provider, stub_context=stub_context)
    print(f"[llm] provider={client.name} model={client.model}")

    library = load_findings_library()
    system_prompt = build_system_prompt(customer_ctx.platform, tier=customer_ctx.tier)

    # ---- 4b. Free -> Starter dedup lookup (PRODUCT-DECISIONS.md section 2) ----
    # Same email + same URL host within 90 days -> exclude the prior 3
    # free-audit fingerprints so the LLM is forced to surface NEW issues.
    excluded_fps, prior_summaries, _free_row_id = free_audit_lookup.load_excluded_fingerprints(
        email=customer_ctx.email,
        url=customer_ctx.url,
    )
    if excluded_fps:
        print(f"[dedup] {len(excluded_fps)} prior free-audit fingerprint(s) to exclude")
    exclude_block = dedup_module.render_exclude_block(excluded_fps, prior_summaries)

    finding_prompt = build_finding_user_prompt(
        customer_ctx,
        cap=cap,
        n_screenshots=len(screenshots),
        prescreener_hits=prescreener_hits,
        pages=pages,
        library=library,
        exclude_block=exclude_block,
    )
    finding_prompt = _maybe_append_webflow_checks(finding_prompt, customer_ctx.platform)

    with cost_tracker.customer_context(customer_ctx.slug, customer_ctx.tier):
        findings = client.generate_findings(
            system_prompt=system_prompt,
            user_prompt=finding_prompt,
            screenshots=screenshots,
            max_findings=cap,
        )

        # Merge Snoop's pre-generated security-lite findings before the cap
        # is applied so a critical exposed credential isn't dropped because
        # the LLM filled the cap with lower-severity items. The performance
        # & accessibility runners (q14 + q16) follow the same pattern: their
        # findings are already tier-capped internally, so we prepend them
        # here and let the global cap run after the merge.
        snoop_findings = list(snoop.get("findings") or [])
        perf_findings = list(perf.get("findings") or [])
        a11y_findings = list(a11y.get("findings") or [])
        external_findings = snoop_findings + perf_findings + a11y_findings
        if external_findings:
            findings = external_findings + list(findings or [])
            print(
                f"[merge] +{len(snoop_findings)} Snoop / "
                f"+{len(perf_findings)} performance / "
                f"+{len(a11y_findings)} accessibility finding(s) merged"
            )

        findings = yaml_writer.sort_findings(findings)[:cap]
        print(f"[llm] {len(findings)} finding(s) after merge + cap")

        # ---- 5b. Dedup pass against the prior free-audit fingerprints ----
        if excluded_fps:
            clashes = dedup_module.collisions(findings, excluded_fps, base_url=customer_ctx.url)
            if clashes:
                clash_titles = [c.get("title", "?") for c in clashes]
                print(f"[dedup] {len(clashes)} finding(s) collide with prior free audit; re-prompting once")
                kept = dedup_module.filter_out_collisions(findings, excluded_fps, base_url=customer_ctx.url)
                needed = cap - len(kept)
                if needed > 0:
                    retry_block = exclude_block + (
                        "\n\n### COLLISION_RETRY\n\n"
                        f"The following {len(clashes)} candidate finding(s) overlap with the "
                        "prior free-audit findings above. REPLACE them with genuinely different "
                        "issues (different category or different specific instance). Do not "
                        "return any of these titles again:\n"
                        + "\n".join(f"  - {t}" for t in clash_titles)
                        + "\n"
                    )
                    retry_prompt = build_finding_user_prompt(
                        customer_ctx,
                        cap=needed,
                        n_screenshots=len(screenshots),
                        prescreener_hits=prescreener_hits,
                        pages=pages,
                        library=library,
                        exclude_block=retry_block,
                    )
                    retry_prompt = _maybe_append_webflow_checks(retry_prompt, customer_ctx.platform)
                    try:
                        replacements = client.generate_findings(
                            system_prompt=system_prompt,
                            user_prompt=retry_prompt,
                            screenshots=screenshots,
                            max_findings=needed,
                        )
                    except Exception as exc:  # noqa: BLE001
                        print(f"[dedup] WARN: re-prompt failed ({exc}); shipping with collisions filtered out", file=sys.stderr)
                        replacements = []
                    # Drop any re-prompt response that ALSO collides; soft
                    # constraint per task spec, ship even if imperfect.
                    fresh = dedup_module.filter_out_collisions(replacements or [], excluded_fps, base_url=customer_ctx.url)
                    findings = yaml_writer.sort_findings(kept + fresh)[:cap]
                    remaining_clash = dedup_module.collisions(findings, excluded_fps, base_url=customer_ctx.url)
                    if remaining_clash:
                        print(f"[dedup] WARN: {len(remaining_clash)} collision(s) still present after re-prompt; shipping anyway (soft constraint)", file=sys.stderr)
                    print(f"[dedup] post-retry: {len(findings)} finding(s) total")
                else:
                    findings = yaml_writer.sort_findings(kept)
                    print(f"[dedup] removed {len(clashes)} colliding finding(s); cap already met")

        # ---- 5c. Persona tags (q5/q13) ----
        # Validates / repairs the per-finding ``tag`` field so every
        # finding ships with one of the 7 Testers personas. Cites
        # docs/SIMPLICITY-GUARDRAILS.md section 3.4.
        findings = apply_persona_tags(findings, load_finding_categories())

        # ---- 6. Verdict ----
        verdict_prompt = build_verdict_user_prompt(customer_ctx, findings=findings)
        try:
            verdict = client.generate_verdict(
                system_prompt=system_prompt,
                user_prompt=verdict_prompt,
            )
            if not verdict.get("summary") or not verdict.get("narrative"):
                raise RuntimeError("verdict missing summary or narrative")
        except Exception as exc:  # noqa: BLE001
            print(f"[verdict] WARN: LLM verdict failed ({exc}); using heuristic default", file=sys.stderr)
            verdict = _default_verdict(findings, customer_ctx.app_name)

        # Constrain to the four canonical labels regardless of LLM drift.
        verdict = _normalize_verdict(verdict)

    # ---- 7. QSG (every paid tier per PRODUCT-DECISIONS.md §8) ----
    qsg = None
    if customer_ctx.tier in ("Starter Package", "Scale Up Package", "Pro Package"):
        qsg_prompt = build_qsg_user_prompt(customer_ctx, pages=pages)
        try:
            with cost_tracker.customer_context(customer_ctx.slug, customer_ctx.tier):
                qsg = client.generate_qsg(
                    system_prompt=system_prompt,
                    user_prompt=qsg_prompt,
                    screenshots=screenshots[:4],   # fewer images for the QSG call
                )
        except Exception as exc:  # noqa: BLE001
            print(f"[qsg] WARN: QSG generation failed ({exc}); leaving QSG empty", file=sys.stderr)

    # ---- 8. Payload + YAML ----
    categories = load_finding_categories()
    passed_checks = compute_passed_checks(
        findings=findings,
        snoop_passed_ids=list(snoop.get("passed_check_ids") or []),
        categories=categories,
        tier=customer_ctx.tier,
        external_passed_ids={
            performance_speed.CATEGORY_ID: list(perf.get("passed_check_ids") or []),
            accessibility_axe.CATEGORY_ID: list(a11y.get("passed_check_ids") or []),
        },
    )

    payload: dict[str, Any] = {
        "customer": {
            "first_name": customer_ctx.first_name,
            "last_name": customer_ctx.last_name,
            "email": customer_ctx.email,
            "app_name": customer_ctx.app_name,
            "app_url": customer_ctx.url,
            "url_redacted": False,
            "tier": customer_ctx.tier,
            "builder": customer_ctx.builder,
            "platform": customer_ctx.platform,
        },
        "verdict": verdict,
        "findings": findings,
        "passed_checks": passed_checks,
    }
    if qsg and qsg.get("steps"):
        payload["quick_start_guide"] = qsg

    if not findings:
        # form_to_yaml requires at least one finding to round-trip; emit a
        # placeholder so the YAML stays valid and Rob can fill it in.
        payload["findings"] = [
            {
                "severity": "low",
                "title": "(Empty draft) AI returned no findings",
                "what_we_saw": (
                    "The AI pipeline ran but produced zero grounded findings. "
                    "Review the screenshots and HTML extracts manually."
                ),
                "why_it_matters": (
                    "Either the app is clean, or the LLM lacked enough evidence."
                ),
                "fix_prompt": (
                    "Review the prescreener output and screenshots. "
                    "Add findings manually or rerun with --provider gpt."
                ),
            }
        ]

    yaml_text = yaml_writer.form_to_yaml(payload)

    yaml_path: Path | None = None
    if not dry_run:
        customers_dir = REPO_ROOT / "customers"
        customers_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = customers_dir / f"{customer_ctx.slug}.yaml"
        yaml_path.write_text(yaml_text, encoding="utf-8")
        print(f"[yaml] wrote {yaml_path.relative_to(REPO_ROOT)}")

        feedback_log.initialize(
            REPO_ROOT,
            customer_ctx.slug,
            findings=payload["findings"],
            provider=client.name,
            model=client.model,
            tier=customer_ctx.tier,
        )

    return PipelineResult(
        slug=customer_ctx.slug,
        yaml_path=yaml_path,
        yaml_text=yaml_text,
        payload=payload,
        provider=client.name,
        model=client.model,
        findings_count=len(payload["findings"]),
        capture_meta=capture_meta,
        prescreener_hits=prescreener_hits,
        pages=pages,
    )


# ---------------------------------------------------------------------------
# Regenerate a single finding (called from the audit UI's 🔄 button)
# ---------------------------------------------------------------------------


def regenerate_finding(
    customer_ctx: CustomerContext,
    *,
    existing_finding: dict[str, Any] | None = None,
    provider: str = "auto",
) -> dict[str, Any]:
    """Generate one replacement finding for the same customer.

    Uses cached screenshots and re-runs the HTML extract (cheap). The LLM
    is told what we already have and to produce ONE distinct finding it
    can ground in the evidence.
    """
    library = load_findings_library()
    pages = stage_html(customer_ctx)
    screenshots = collect_screenshots(customer_ctx.slug, max_shots=6)
    print(f"[regen] {len(screenshots)} screenshots, {len(pages)} pages")

    stub_context = {
        "prescreener_hits": [],
        "builder": customer_ctx.builder,
        "app_name": customer_ctx.app_name,
    }
    client = llm_client.build_client(provider=provider, stub_context=stub_context)

    system_prompt = build_system_prompt(customer_ctx.platform, tier=customer_ctx.tier)
    base = build_finding_user_prompt(
        customer_ctx,
        cap=1,
        n_screenshots=len(screenshots),
        prescreener_hits=[],
        pages=pages,
        library=library,
    )
    base = _maybe_append_webflow_checks(base, customer_ctx.platform)
    regen_hint = (
        "\n\n### Regeneration request\n\n"
        "Produce exactly ONE replacement finding. The previous draft was:\n"
        f"  severity: {existing_finding.get('severity') if existing_finding else '?'}\n"
        f"  title:    {existing_finding.get('title') if existing_finding else '?'}\n"
        "Pick a DIFFERENT, well-grounded issue if possible. If the prior "
        "finding was actually correct but the wording was off, return the "
        "same issue with sharper wording. Apply the same voice rules."
    )

    with cost_tracker.customer_context(customer_ctx.slug, customer_ctx.tier):
        finding = client.regenerate_finding(
            system_prompt=system_prompt,
            user_prompt=base + regen_hint,
            screenshots=screenshots,
        )
    # Apply the same persona-tag fallback so a regenerated finding ships
    # with a valid Tester tag even if the LLM forgets the field.
    repaired = apply_persona_tags([finding], load_finding_categories())
    return repaired[0] if repaired else finding


# ---------------------------------------------------------------------------
# Customer-context builder (CLI side)
# ---------------------------------------------------------------------------


def context_from_kwargs(**kwargs: Any) -> CustomerContext:
    first = (kwargs.get("first_name") or "").strip()
    last = (kwargs.get("last_name") or "").strip()
    full = (kwargs.get("name") or "").strip()
    if full and not (first or last):
        parts = full.split(None, 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ""

    slug = (kwargs.get("slug") or "").strip()
    if not slug:
        sys.exit("ERROR: --slug is required")

    url = (kwargs.get("url") or "").strip()
    if not url:
        sys.exit("ERROR: --url is required")
    if not url.startswith(("http://", "https://")):
        sys.exit("ERROR: --url must start with http:// or https://")

    tier = (kwargs.get("tier") or "").strip()
    if tier not in {"Starter Package", "Scale Up Package", "Pro Package"}:
        sys.exit(
            "ERROR: --tier must be 'Starter Package', 'Scale Up Package', or 'Pro Package'"
        )

    builder = (kwargs.get("builder") or "").strip() or "Lovable"
    platform = normalize_platform(kwargs.get("platform"))

    # If the caller passed builder=Webflow but forgot to set platform, infer
    # webflow so the right fix-prompt voice kicks in automatically. The
    # reverse (platform=webflow but builder=Lovable) trusts the explicit
    # caller intent and does not override builder.
    if platform == DEFAULT_PLATFORM and builder.strip().lower() == "webflow":
        platform = "webflow"

    return CustomerContext(
        slug=slug,
        url=url,
        tier=tier,
        builder=builder,
        first_name=first or kwargs.get("first_name") or "",
        last_name=last,
        email=(kwargs.get("email") or "").strip(),
        app_name=(kwargs.get("app_name") or "").strip() or kwargs.get("app_name", ""),
        intake_notes=(kwargs.get("intake_notes") or "").strip(),
        platform=platform,
    )
