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

from . import feedback as feedback_log  # noqa: E402
from . import html_extract, llm_client  # noqa: E402


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

DEFAULT_TIER_CAPS = {"Starter Package": 7, "Full Package": 25, "Pro Package": 40}

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


# Matches the dict-lookup form in deliver_report.validate(), e.g.
#   cap = {"Starter Package": 7, "Full Package": 25, "Pro Package": 40}.get(tier, 25)
_TIER_CAP_PATTERN = re.compile(
    r"cap\s*=\s*\{(?P<body>[^}]*)\}\s*\.get\s*\(\s*tier\s*,",
)
_TIER_CAP_ENTRY = re.compile(
    r"['\"](?P<name>[^'\"]+)['\"]\s*:\s*(?P<cap>\d+)"
)


def load_tier_caps() -> dict[str, int]:
    """Read tier caps from ``deliver_report.py``. Falls back to defaults."""
    try:
        text = DELIVER_REPORT.read_text(encoding="utf-8")
    except OSError:
        return dict(DEFAULT_TIER_CAPS)
    match = _TIER_CAP_PATTERN.search(text)
    if not match:
        return dict(DEFAULT_TIER_CAPS)
    caps: dict[str, int] = {}
    for entry in _TIER_CAP_ENTRY.finditer(match.group("body")):
        caps[entry.group("name")] = int(entry.group("cap"))
    return caps or dict(DEFAULT_TIER_CAPS)


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


def _read_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")


def _tier_guidance(tier: str, cap: int) -> str:
    if tier == "Starter Package":
        return (
            f"Starter Package is priority triage. Return at most {cap} findings, "
            "the most important things a first-time visitor would notice. Skew "
            "toward criticals and highs. If the app is clean, return fewer."
        )
    if tier == "Pro Package":
        return (
            f"Pro Package is the deepest pass we offer. Return up to {cap} findings "
            "spanning trust, polish, mobile, broken functionality, AND a dedicated "
            "review of the customer's operational integrations (Stripe / auth / "
            "email / analytics setup) — flag misconfiguration, missing webhooks, "
            "leaked test keys on the public surface, redirect URLs that point at "
            "localhost, broken from-addresses, double-counted analytics events, "
            "etc. Include lower-severity polish items the customer paid extra "
            "for. Still drop any finding you cannot ground in real evidence."
        )
    return (
        f"Full Package is the deeper pass. Return up to {cap} findings spanning "
        "trust, polish, mobile, and broken functionality. Include the lower-"
        "severity polish items the customer paid extra for. Still drop any "
        "finding you cannot ground in real evidence."
    )


def build_finding_user_prompt(
    customer_ctx: CustomerContext,
    *,
    cap: int,
    n_screenshots: int,
    prescreener_hits: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    library: list[dict[str, Any]],
) -> str:
    template = _read_prompt("finding_generation.txt")
    return template.format(
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
    has_critical = any((f.get("severity") or "").lower() == "critical" for f in findings)
    has_high = any((f.get("severity") or "").lower() == "high" for f in findings)
    emoji = "🔴" if has_critical else ("🟡" if has_high else "🟢")
    if has_critical:
        summary = "Two or more critical issues to clear before sharing publicly."
    elif has_high:
        summary = "Needs a few fixes before sharing publicly."
    else:
        summary = "Ready to share, just a couple of polish items."
    return {
        "emoji": emoji,
        "summary": summary,
        "narrative": (
            f"{app_name} is in reasonable shape. The findings below are sorted "
            f"by severity. Fix anything marked critical before sharing the URL "
            f"more widely, then work down the list as time allows."
        ),
    }


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
    cap = max_findings or tier_caps.get(customer_ctx.tier, 25)
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
    system_prompt = _read_prompt("system.txt")

    finding_prompt = build_finding_user_prompt(
        customer_ctx,
        cap=cap,
        n_screenshots=len(screenshots),
        prescreener_hits=prescreener_hits,
        pages=pages,
        library=library,
    )

    findings = client.generate_findings(
        system_prompt=system_prompt,
        user_prompt=finding_prompt,
        screenshots=screenshots,
        max_findings=cap,
    )

    findings = yaml_writer.sort_findings(findings)[:cap]
    print(f"[llm] generated {len(findings)} finding(s)")

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

    # ---- 7. QSG (Full Package + Pro Package) ----
    qsg = None
    if customer_ctx.tier in ("Full Package", "Pro Package"):
        qsg_prompt = build_qsg_user_prompt(customer_ctx, pages=pages)
        try:
            qsg = client.generate_qsg(
                system_prompt=system_prompt,
                user_prompt=qsg_prompt,
                screenshots=screenshots[:4],   # fewer images for the QSG call
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[qsg] WARN: QSG generation failed ({exc}); leaving QSG empty", file=sys.stderr)

    # ---- 8. Payload + YAML ----
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
        },
        "verdict": verdict,
        "findings": findings,
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

    system_prompt = _read_prompt("system.txt")
    base = build_finding_user_prompt(
        customer_ctx,
        cap=1,
        n_screenshots=len(screenshots),
        prescreener_hits=[],
        pages=pages,
        library=library,
    )
    regen_hint = (
        "\n\n### Regeneration request\n\n"
        "Produce exactly ONE replacement finding. The previous draft was:\n"
        f"  severity: {existing_finding.get('severity') if existing_finding else '?'}\n"
        f"  title:    {existing_finding.get('title') if existing_finding else '?'}\n"
        "Pick a DIFFERENT, well-grounded issue if possible. If the prior "
        "finding was actually correct but the wording was off, return the "
        "same issue with sharper wording. Apply the same voice rules."
    )

    finding = client.regenerate_finding(
        system_prompt=system_prompt,
        user_prompt=base + regen_hint,
        screenshots=screenshots,
    )
    return finding


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
    if tier not in {"Starter Package", "Full Package", "Pro Package"}:
        sys.exit("ERROR: --tier must be 'Starter Package', 'Full Package', or 'Pro Package'")

    builder = (kwargs.get("builder") or "").strip() or "Lovable"

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
    )
