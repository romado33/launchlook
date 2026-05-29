"""
deliver_report.py: render Main Report + Quick Start Guide + Pre-Launch
Checklist PDFs and email them.

Reads a customer YAML file (verdict, findings, QSG sections) and renders three
A4 PDFs with Playwright + Jinja2:

    output/reports/{slug}/main-report.pdf
    output/reports/{slug}/quick-start-guide.pdf
    output/reports/{slug}/pre-launch-checklist.pdf

The Pre-Launch Checklist is a generic deliverable bundled with every paid
tier (Starter / Scale Up / Pro). It replaces the deleted
landing/checklist.html surface.

Workflow:

    # Default: render PDFs and open them in the system viewer for review.
    python scripts/deliver_report.py --customer customers/jane-sparkle.yaml

    # Same, but also send to the customer via Resend (with confirmation).
    python scripts/deliver_report.py --customer customers/jane-sparkle.yaml --send

The send path requires RESEND_API_KEY in .env (https://resend.com/api-keys).
The dry-run path needs nothing beyond Playwright + chromium.

Setup once:
    pip install -r requirements.txt
    playwright install chromium
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.fix_pack import (  # noqa: E402
    enrich_findings_for_templates,
    render_builder_memory,
    render_fix_pack_markdown,
)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# Windows consoles default to cp1252; force UTF-8 so unicode is safe to print.
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = REPO_ROOT / "templates"
REPORT_TEMPLATE_DIR = TEMPLATE_ROOT / "report"
QSG_TEMPLATE_DIR = TEMPLATE_ROOT / "qsg"
USER_GUIDE_TEMPLATE_DIR = TEMPLATE_ROOT / "user_guide"
EMAIL_TEMPLATE_DIR = TEMPLATE_ROOT / "email"
CONFIDENCE_CHECK_TEMPLATE_DIR = TEMPLATE_ROOT / "confidence_check"
HANDOFF_TEMPLATE_DIR = TEMPLATE_ROOT / "handoff"
SHAREABLE_TEMPLATE_DIR = TEMPLATE_ROOT / "r"
CONFIDENCE_CHECKS_DATA_DIR = REPO_ROOT / "data" / "confidence_checks"
OUTPUT_ROOT = REPO_ROOT / "output" / "reports"
CONFIDENCE_CHECK_OUTPUT_ROOT = REPO_ROOT / "output" / "confidence_checks"

# q22: shareable hosted report pages. JSON data goes here, per-customer
# HTML pages go to landing/r/{slug}.html. See docs/SHAREABLE-REPORT-WORKFLOW.md.
SHAREABLE_REPORTS_DATA_DIR = REPO_ROOT / "landing" / "data" / "reports"
SHAREABLE_PAGES_DIR = REPO_ROOT / "landing" / "r"

# Handoff Report (q18). Pro Package gets it bundled; Starter / Scale Up
# can buy it as a $49 add-on, which is signalled by --tier-override
# Starter+Handoff / "Full+Handoff". See docs/HANDOFF-REPORT-WORKFLOW.md.
HANDOFF_OVERRIDE_SEPARATOR = "+"
HANDOFF_OVERRIDE_SUFFIX = "Handoff"
TIER_ALIAS_TO_CANONICAL = {
    "starter": "Starter Package",
    "starter package": "Starter Package",
    # Back-compat: "Full Package" was the pre-rename name for the middle
    # tier. Old customer YAMLs and Stripe events written before the rename
    # still pass these strings, so we normalise them to the canonical
    # "Scale Up Package" rather than treating them as a distinct tier.
    "full": "Scale Up Package",
    "full package": "Scale Up Package",
    "scaleup": "Scale Up Package",
    "scale up": "Scale Up Package",
    "scale up package": "Scale Up Package",
    "pro": "Pro Package",
    "pro package": "Pro Package",
}

VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_TIERS = {"Starter Package", "Scale Up Package", "Pro Package"}

# P1 #16: Maximum total attachment size (base64-encoded) before we strip
# attachments and tell the customer to ask for a transfer link instead.
ATTACHMENT_SIZE_WARN_MB = 9


# ---------------------------------------------------------------------------
# YAML loading + validation
# ---------------------------------------------------------------------------


def load_customer_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        sys.exit("ERROR: pyyaml not installed. Run: pip install -r requirements.txt")

    if not path.exists():
        sys.exit(f"ERROR: customer file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        sys.exit(f"ERROR: {path} did not parse as a YAML mapping")

    return data


def validate(data: dict[str, Any]) -> None:
    customer = data.get("customer", {})
    for key in ("first_name", "email", "app_name", "tier", "builder"):
        if not customer.get(key):
            sys.exit(f"ERROR: customer.{key} is required in the YAML")

    tier = customer["tier"]
    if tier not in VALID_TIERS:
        sys.exit(f"ERROR: customer.tier must be one of {sorted(VALID_TIERS)}, got: {tier!r}")

    findings = data.get("findings") or []
    if not isinstance(findings, list) or not findings:
        sys.exit("ERROR: at least one finding is required")

    for i, f in enumerate(findings, start=1):
        if not isinstance(f, dict):
            sys.exit(f"ERROR: findings[{i}] is not a mapping")
        if f.get("severity") not in VALID_SEVERITIES:
            sys.exit(
                f"ERROR: findings[{i}].severity must be one of {sorted(VALID_SEVERITIES)}, "
                f"got: {f.get('severity')!r}"
            )
        if not f.get("title"):
            sys.exit(f"ERROR: findings[{i}].title is required")

    cap = {"Starter Package": 10, "Scale Up Package": 30, "Pro Package": 40}.get(tier, 30)
    if len(findings) > cap:
        print(
            f"WARN: {tier} caps at {cap} findings, this YAML has {len(findings)}.",
            file=sys.stderr,
        )

    verdict = data.get("verdict", {})
    if not verdict.get("summary"):
        sys.exit("ERROR: verdict.summary is required")


# ---------------------------------------------------------------------------
# Slug + URL helpers
# ---------------------------------------------------------------------------


def slugify(*parts: str) -> str:
    text = "-".join(p for p in parts if p)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "customer"


def display_url(app_url: str, redacted: bool) -> str:
    if not app_url:
        return ""
    if redacted:
        return "URL redacted"
    cleaned = re.sub(r"^https?://", "", app_url).rstrip("/")
    return cleaned


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def build_jinja_env():
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        sys.exit("ERROR: jinja2 not installed. Run: pip install -r requirements.txt")

    return Environment(
        loader=FileSystemLoader(
            [
                str(REPORT_TEMPLATE_DIR),
                str(QSG_TEMPLATE_DIR),
                str(USER_GUIDE_TEMPLATE_DIR),
                str(EMAIL_TEMPLATE_DIR),
                str(CONFIDENCE_CHECK_TEMPLATE_DIR),
                str(HANDOFF_TEMPLATE_DIR),
                str(SHAREABLE_TEMPLATE_DIR),
                str(TEMPLATE_ROOT),
            ]
        ),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )


# ---------------------------------------------------------------------------
# Handoff Report helpers (q18)
# ---------------------------------------------------------------------------


def parse_tier_override(raw: str | None) -> tuple[str | None, bool]:
    """Resolve a ``--tier-override`` argument.

    Accepts values like ``"Starter"``, ``"Starter Package"``,
    ``"Starter+Handoff"``, ``"Pro Package"``. Returns
    ``(canonical_tier, has_handoff_addon)``. ``canonical_tier`` is
    ``None`` when the caller didn't pass an override (use the YAML).

    The ``+Handoff`` suffix is a signal that this customer paid the
    $49 add-on. It's used so the Handoff Report still renders for
    Starter / Scale Up buyers without flipping their canonical tier
    (which would change finding caps + dedup rules upstream).
    """
    if not raw:
        return None, False
    parts = [p.strip() for p in raw.split(HANDOFF_OVERRIDE_SEPARATOR)]
    base_alias = parts[0].lower()
    has_addon = any(p.lower() == HANDOFF_OVERRIDE_SUFFIX.lower() for p in parts[1:])
    canonical = TIER_ALIAS_TO_CANONICAL.get(base_alias)
    if not canonical:
        sys.exit(
            f"ERROR: --tier-override {raw!r} is not recognised. "
            f"Use one of: Starter, Full, Pro, Starter+Handoff, Full+Handoff, Pro+Handoff."
        )
    return canonical, has_addon


def severity_buckets_for_handoff(
    findings: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group findings into the 3 Handoff Report sections."""
    high: list[dict[str, Any]] = []
    medium: list[dict[str, Any]] = []
    low: list[dict[str, Any]] = []
    for f in findings or []:
        sev = (f.get("severity") or "").strip().lower()
        if sev in ("critical", "high"):
            high.append(f)
        elif sev == "medium":
            medium.append(f)
        elif sev == "low":
            low.append(f)
    return {
        "findings_high": high,
        "findings_medium": medium,
        "findings_low": low,
    }


def render_handoff_markdown(
    env, data: dict[str, Any], narrative: dict[str, Any], audit_date: str
) -> str:
    """Render templates/handoff/handoff.md.j2 with audit + narrative data."""
    customer = dict(data["customer"])
    buckets = severity_buckets_for_handoff(data.get("findings") or [])
    template = env.get_template("handoff.md.j2")
    return template.render(
        customer=customer,
        verdict=data.get("verdict") or {},
        audit_date=audit_date,
        passed_checks=data.get("passed_checks") or [],
        context_paragraph=narrative.get("context_paragraph", "").strip(),
        recommended_order=narrative.get("recommended_order", "").strip(),
        code_review_notes=(narrative.get("code_review_notes") or "").strip() or None,
        builder_memory=(narrative.get("builder_memory") or "").strip() or None,
        tier=narrative.get("effective_tier") or customer.get("tier"),
        **buckets,
    )


def render_handoff_html(
    env, data: dict[str, Any], narrative: dict[str, Any], audit_date: str
) -> str:
    """Render templates/handoff/handoff.html.j2 for PDF generation."""
    customer = dict(data["customer"])
    buckets = severity_buckets_for_handoff(data.get("findings") or [])
    template = env.get_template("handoff.html.j2")
    return template.render(
        customer=customer,
        verdict=data.get("verdict") or {},
        audit_date=audit_date,
        passed_checks=data.get("passed_checks") or [],
        context_paragraph=narrative.get("context_paragraph", "").strip(),
        recommended_order=narrative.get("recommended_order", "").strip(),
        code_review_notes=(narrative.get("code_review_notes") or "").strip() or None,
        builder_memory=(narrative.get("builder_memory") or "").strip() or None,
        tier=narrative.get("effective_tier") or customer.get("tier"),
        groups=buckets,
    )


def deliver_handoff_report(
    data: dict[str, Any],
    *,
    out_dir: Path,
    delivered_at: str,
    effective_tier: str,
    has_handoff_addon: bool,
    provider: str = "auto",
    no_open: bool = False,
) -> tuple[Path | None, Path | None]:
    """Render the Handoff Report (Markdown + PDF) for this customer.

    Returns ``(md_path, pdf_path)``. Either may be ``None`` if rendering
    fails or is skipped.

    Eligibility:
      - Customer is Pro Package (bundled), OR
      - Customer is Starter / Scale Up + ``has_handoff_addon=True``
        (the $49 add-on has been paid).
    """
    customer_tier = (data.get("customer", {}) or {}).get("tier", "")
    canonical_tier = effective_tier or customer_tier
    is_pro = canonical_tier == "Pro Package"
    eligible = is_pro or has_handoff_addon
    if not eligible:
        print(
            "  ! Handoff Report not generated: customer is not Pro Package and the "
            "$49 add-on was not signalled (use --tier-override Starter+Handoff).",
            file=sys.stderr,
        )
        return None, None

    # Delayed import so the pipeline / ai_audit deps are only loaded when
    # the Handoff Report is actually requested.
    from scripts.ai_audit import pipeline as ai_pipeline  # noqa: PLC0415

    narrative = ai_pipeline.run_handoff_report(
        audit_payload=data,
        effective_tier=canonical_tier,
        audit_date=delivered_at,
        provider=provider,
    )

    customer = dict(data.get("customer") or {})
    handoff_data = dict(data)
    handoff_data["findings"] = enrich_findings_for_templates(data.get("findings") or [], customer)
    memory = render_builder_memory(
        customer,
        explicit=data.get("builder_memory") or customer.get("builder_memory"),
    )
    if memory:
        narrative = dict(narrative)
        narrative["builder_memory"] = memory

    env = build_jinja_env()

    md_text = render_handoff_markdown(env, handoff_data, narrative, delivered_at)
    md_path = out_dir / "handoff-report.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"  âœ“ wrote {md_path.name} ({md_path.stat().st_size / 1024:.1f} KB)")

    html = render_handoff_html(env, handoff_data, narrative, delivered_at)
    pdf_path = out_dir / "handoff-report.pdf"
    try:
        html_to_pdf(html, pdf_path, data.get("customer", {}).get("first_name", "customer"))
        print(f"  âœ“ wrote {pdf_path.name} ({pdf_path.stat().st_size / 1024:.1f} KB)")
    except SystemExit as exc:
        print(f"  ! Handoff PDF skipped: {exc}", file=sys.stderr)
        pdf_path = None

    if not no_open and pdf_path and pdf_path.exists():
        open_in_viewer(pdf_path)

    return md_path, pdf_path


def render_main_report_html(
    env, data: dict[str, Any], delivered_at: str, qsg_link: str | None
) -> str:
    customer = dict(data["customer"])
    customer["url_redacted_or_shown"] = display_url(
        customer.get("app_url", ""),
        bool(customer.get("url_redacted")),
    )

    findings = enrich_findings_for_templates(data.get("findings") or [], customer)

    template = env.get_template("report.html.j2")
    return template.render(
        customer=customer,
        verdict=data["verdict"],
        findings=findings,
        delivered_at=delivered_at,
        qsg_link=qsg_link,
        readiness_score=data.get("readiness_score"),
    )


def render_qsg_html(env, data: dict[str, Any], delivered_at: str) -> str | None:
    qsg = data.get("quick_start_guide")
    if not qsg or not qsg.get("title"):
        return None

    template = env.get_template("qsg.html.j2")
    return template.render(
        customer=data["customer"],
        qsg=qsg,
        delivered_at=delivered_at,
    )


def render_user_guide_html(env, data: dict[str, Any], delivered_at: str) -> str | None:
    """Render the 2-3 page User Guide PDF (Scale Up and Pro only)."""
    user_guide = data.get("user_guide")
    if not user_guide or not user_guide.get("sections"):
        return None

    tier = (data.get("customer") or {}).get("tier", "")
    if tier not in ("Scale Up Package", "Pro Package"):
        return None

    template = env.get_template("user_guide.html.j2")
    return template.render(
        customer=data["customer"],
        user_guide=user_guide,
        delivered_at=delivered_at,
    )


def render_pre_launch_checklist_html(env, data: dict[str, Any], delivered_at: str) -> str:
    """Render the bundled Pre-Launch Checklist PDF.

    The content is generic (same for every paid customer); we only
    personalise the eyebrow line via customer.app_name + customer.tier so
    it does not feel like an unrelated leaflet. Replaces the deleted
    landing/checklist.html surface; bundled with every paid tier per
    docs/PRODUCT-DECISIONS.md changelog (May 2026 simplification).
    """
    template = env.get_template("pre_launch_checklist.html.j2")
    return template.render(
        customer=data["customer"],
        delivered_at=delivered_at,
    )


def html_to_pdf(html: str, out_path: Path, customer_name: str) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "ERROR: playwright not installed.\n"
            "Run: pip install -r requirements.txt && playwright install chromium"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    footer_html = (
        '<div style="font-size:8pt; color:#6B6359; width:100%; '
        "padding:0 20mm; font-family:-apple-system,sans-serif; "
        'display:flex; justify-content:space-between;">'
        f"<span>LaunchLook Â· launchlook.app Â· prepared {date.today().isoformat()}</span>"
        f"<span>Confidential, for {customer_name} only Â· "
        '<span class="pageNumber"></span> / <span class="totalPages"></span></span>'
        "</div>"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context()
            page = context.new_page()
            page.set_content(html, wait_until="networkidle")
            page.pdf(
                path=str(out_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "25mm",
                    "right": "20mm",
                    "bottom": "22mm",
                    "left": "20mm",
                },
                display_header_footer=True,
                header_template="<span></span>",
                footer_template=footer_html,
            )
        finally:
            browser.close()


# ---------------------------------------------------------------------------
# Email send (Resend)
# ---------------------------------------------------------------------------


def render_email_bodies(env, data: dict[str, Any], delivered_at: str) -> tuple[str, str, str]:
    customer = data["customer"]
    n_findings = len(data["findings"])
    subject = f"Your LaunchLook report is ready, {customer['first_name']}"

    builder_memory = render_builder_memory(
        customer,
        explicit=data.get("builder_memory") or customer.get("builder_memory"),
    )

    html_tpl = env.get_template("delivery_pdf.html.j2")
    text_tpl = env.get_template("delivery_pdf.txt.j2")

    ctx = {
        "customer": customer,
        "n_findings": n_findings,
        "delivered_at": delivered_at,
        "builder_memory": builder_memory,
        "is_pro": customer.get("tier") == "Pro Package",
    }
    return subject, html_tpl.render(**ctx), text_tpl.render(**ctx)


def send_via_resend(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str,
    attachments: list[Path],
) -> dict[str, Any]:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        sys.exit(
            "ERROR: RESEND_API_KEY is missing.\n"
            "Add it to .env (see .env.example, line `RESEND_API_KEY=`).\n"
            "Get a key at https://resend.com/api-keys."
        )

    try:
        import resend
    except ImportError:
        sys.exit("ERROR: resend not installed. Run: pip install -r requirements.txt")

    resend.api_key = api_key

    from_email = os.getenv("FROM_EMAIL", "hello@launchlook.app")
    admin_email = os.getenv("ADMIN_EMAIL")

    # P1 #16: Guard total attachment size. Base64 inflates by ~33%, so we
    # check the encoded size directly. If it exceeds ATTACHMENT_SIZE_WARN_MB
    # we strip the attachments and note that in the email body so the
    # customer knows to ask for a transfer link rather than receiving nothing.
    encoded_attachments = []
    total_b64_bytes = 0
    for path in attachments:
        raw = path.read_bytes()
        encoded = base64.b64encode(raw).decode("ascii")
        total_b64_bytes += len(encoded)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            content_type = "application/pdf"
        elif suffix in (".md", ".markdown"):
            content_type = "text/markdown"
        elif suffix == ".txt":
            content_type = "text/plain"
        else:
            content_type = "application/octet-stream"
        encoded_attachments.append(
            {
                "filename": path.name,
                "content": encoded,
                "content_type": content_type,
            }
        )

    size_limit_bytes = ATTACHMENT_SIZE_WARN_MB * 1024 * 1024
    if total_b64_bytes > size_limit_bytes:
        total_mb = total_b64_bytes / (1024 * 1024)
        print(
            f"WARN: total attachment size {total_mb:.1f} MB exceeds "
            f"{ATTACHMENT_SIZE_WARN_MB} MB limit — sending without attachments.",
            file=sys.stderr,
        )
        size_note = (
            "\n\nNote: The PDFs were too large to attach directly to this email. "
            "Reply to this email and I'll send them via a file transfer link."
        )
        html_body = html_body + size_note.replace("\n", "<br>")
        text_body = text_body + size_note
        encoded_attachments = []

    payload: dict[str, Any] = {
        "from": f"LaunchLook <{from_email}>",
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "text": text_body,
        "reply_to": from_email,
        "attachments": encoded_attachments,
    }
    if admin_email and admin_email != to_email:
        payload["bcc"] = [admin_email]

    return resend.Emails.send(payload)


# ---------------------------------------------------------------------------
# Open in default viewer (cross-platform best effort)
# ---------------------------------------------------------------------------


def open_in_viewer(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}" >/dev/null 2>&1 &')
    except Exception as exc:
        print(f"WARN: could not open {path} automatically: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def latest_confidence_check_for(customer_id: str) -> Path:
    """Return the most recent ``data/confidence_checks/<customer_id>-*.yaml``.

    Customer ID may be a slug (e.g. ``jane-sparkle``) or a full file path.
    """
    candidate = Path(customer_id)
    if candidate.suffix == ".yaml" and candidate.exists():
        return candidate.resolve()
    if not CONFIDENCE_CHECKS_DATA_DIR.exists():
        sys.exit(
            f"ERROR: {CONFIDENCE_CHECKS_DATA_DIR.relative_to(REPO_ROOT)} does not exist. "
            "Run scripts/confidence_check.py first."
        )
    matches = sorted(CONFIDENCE_CHECKS_DATA_DIR.glob(f"{customer_id}-*.yaml"))
    if not matches:
        sys.exit(
            f"ERROR: no Confidence Check YAML found for customer {customer_id!r} in "
            f"{CONFIDENCE_CHECKS_DATA_DIR.relative_to(REPO_ROOT)}.\n"
            f"Run: python scripts/confidence_check.py --customer {customer_id} "
            f"--original <original_audit_id>"
        )
    return matches[-1]


def render_confidence_check_html(env, data: dict[str, Any], delivered_at: str) -> str:
    template = env.get_template("confidence_check_report.html.j2")
    return template.render(
        confidence_check=data["confidence_check"],
        verdict=data["verdict"],
        fixed=data.get("fixed") or [],
        still_present=data.get("still_present") or [],
        new=data.get("new") or [],
        footer_note=data.get("footer_note", ""),
        delivered_at=delivered_at,
    )


def render_confidence_check_email(
    env, data: dict[str, Any], delivered_at: str
) -> tuple[str, str, str]:
    cc = data["confidence_check"]
    first_name = cc.get("customer_first_name") or "there"
    subject = f"Your Fix Check is ready, {first_name}"

    fixed = data.get("fixed") or []
    still_present = data.get("still_present") or []
    new = data.get("new") or []

    ctx = {
        "first_name": first_name,
        "app_name": cc.get("app_name", ""),
        "verdict": data["verdict"],
        "fixed_count": len(fixed),
        "still_count": len(still_present),
        "new_count": len(new),
        "fixed": fixed,
        "still_present": still_present,
        "new": new,
        "delivered_at": delivered_at,
    }

    html_tpl = env.get_template("confidence_check_email.html.j2")
    text_tpl = env.get_template("confidence_check_email.txt.j2")
    return subject, html_tpl.render(**ctx), text_tpl.render(**ctx)


def deliver_confidence_check(args) -> int:
    """Render + (optionally) send the Confidence Check short-form report."""
    yaml_path = latest_confidence_check_for(args.customer)
    print(f"â†’ Confidence Check YAML: {yaml_path.relative_to(REPO_ROOT)}")

    try:
        import yaml as _yaml
    except ImportError:
        sys.exit("ERROR: pyyaml not installed.")
    with yaml_path.open("r", encoding="utf-8") as f:
        data = _yaml.safe_load(f) or {}

    cc = data.get("confidence_check") or {}
    if not cc:
        sys.exit(
            f"ERROR: {yaml_path} is missing the top-level 'confidence_check' block. "
            "Re-run scripts/confidence_check.py to regenerate it."
        )

    customer_id = cc.get("customer_id") or args.customer
    delivered_at = date.today().isoformat()

    out_dir = CONFIDENCE_CHECK_OUTPUT_ROOT / customer_id
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "confidence-check.pdf"

    env = build_jinja_env()

    print(
        f"â†’ Customer:   {cc.get('customer_first_name', customer_id)} ({cc.get('customer_email', '?')})"
    )
    print(f"â†’ App:        {cc.get('app_name', '?')}")
    print(f"â†’ Original:   {cc.get('original_audit_id', '?')}")
    print(
        f"â†’ Buckets:    âœ“ {len(data.get('fixed') or [])}"
        f" / âœ— {len(data.get('still_present') or [])}"
        f" / âš  {len(data.get('new') or [])}"
    )
    print(f"â†’ Output:     {out_dir.relative_to(REPO_ROOT)}")

    html = render_confidence_check_html(env, data, delivered_at)
    html_to_pdf(html, pdf_path, cc.get("customer_first_name") or customer_id)
    print(f"  âœ“ wrote {pdf_path.name} ({pdf_path.stat().st_size / 1024:.1f} KB)")

    # Confidence Check intentionally has NO QSG (per the spec â€” it's a
    # short focused report, not a full audit).

    if not args.send:
        if not args.no_open:
            open_in_viewer(pdf_path)
        subject, html_body, text_body = render_confidence_check_email(env, data, delivered_at)
        preview_path = out_dir / "email-preview.txt"
        preview_path.write_text(
            f"Subject: {subject}\n\n--- TEXT ---\n{text_body}\n\n--- HTML ---\n{html_body}\n",
            encoding="utf-8",
        )
        print(f"  âœ“ wrote {preview_path.name} (email preview)")
        print(
            "\nDry-run complete. Review the PDF + email preview, then re-run with "
            "--send to email it.\n"
            f"  python scripts/deliver_report.py --confidence-check "
            f"--customer {customer_id} --send"
        )
        return 0

    subject, html_body, text_body = render_confidence_check_email(env, data, delivered_at)

    to_email = cc.get("customer_email", "")
    if not to_email:
        sys.exit(
            "ERROR: confidence_check.customer_email is empty in the YAML. "
            "Fill it in manually before --send."
        )

    print("\n--- Send preview ---")
    print(f"  To:       {to_email}")
    print(f"  Subject:  {subject}")
    print(f"  Files:    {pdf_path.name}")
    if not args.yes:
        confirm = input("\nSend now? Type 'send' to confirm: ").strip().lower()
        if confirm != "send":
            print("Aborted. No email was sent.")
            return 1

    result = send_via_resend(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        attachments=[pdf_path],
    )
    msg_id = result.get("id") if isinstance(result, dict) else None
    print(f"\nâœ“ Sent. Resend message id: {msg_id or '(none returned)'}")
    return 0


# ---------------------------------------------------------------------------
# Shareable hosted report page (q22)
# ---------------------------------------------------------------------------


def _format_audit_date_human(iso: str) -> str:
    try:
        parts = iso.split("-")
        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        return f"{months[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]}"
    except (ValueError, IndexError):
        return iso


def _build_share_metadata(
    customer: dict[str, Any],
    verdict: dict[str, Any],
    n_findings: int,
    audit_date: str,
) -> dict[str, str]:
    """Build the OG / Twitter Card meta-tag values for the shareable page.

    Phrasing rules (per docs/SIMPLICITY-GUARDRAILS.md sections 3 + 6):
      * No "comprehensive", "AI-powered", or other corporate vocabulary.
      * Plain English. Verdict label up front so a Reddit / Twitter scroller
        can decide whether to click.
    """
    app_name = customer.get("app_name", "this app")
    label = (verdict.get("label") or "Pre-launch audit").strip()
    description = (
        f"Pre-launch audit. Verdict: {label}. "
        f"{n_findings} finding{'s' if n_findings != 1 else ''} "
        f"across trust, broken CTAs, mobile layout, and more."
    )
    return {
        "title": f"LaunchLook audit for {app_name}",
        "description": description,
        "og_image": "https://launchlook.app/images/og.png",
    }


def _build_public_report_dict(
    data: dict[str, Any],
    *,
    slug: str,
    delivered_at: str,
    is_pro_handoff: bool,
) -> dict[str, Any]:
    """Assemble the public-safe report dict before sanitization.

    The output of this function is the *unsanitized* shape -- with raw
    customer URL etc. still attached -- because ``sanitize_report_json``
    expects to do the stripping itself given the customer block. Always
    pipe this through ``sanitize_report_json`` before writing JSON.
    """
    customer = data["customer"]
    verdict = data.get("verdict") or {}
    findings = data.get("findings") or []

    share_metadata = _build_share_metadata(customer, verdict, len(findings), delivered_at)

    return {
        "customer_slug": slug,
        "is_public": False,
        "tier": customer.get("tier", ""),
        "audit_date": delivered_at,
        "app_name": customer.get("app_name", ""),
        "customer_url": customer.get("app_url", ""),
        "verdict": dict(verdict),
        "readiness_score": data.get("readiness_score"),
        "passed_checks": list(data.get("passed_checks") or []),
        "findings": [dict(f) for f in findings if isinstance(f, dict)],
        "share_metadata": share_metadata,
        "handoff_report": {
            "available": bool(is_pro_handoff),
            "shared": False,
        },
    }


def _generate_shareable_page(
    data: dict[str, Any],
    *,
    slug: str,
    delivered_at: str,
    has_handoff: bool,
) -> tuple[Path, Path]:
    """Generate the shareable hosted report page assets for this customer.

    Writes two files:

    * ``landing/data/reports/{slug}.json`` -- sanitized data, default
      ``is_public: false``. The customer flips this with
      ``scripts/share_report.py --slug ... --public``.
    * ``landing/r/{slug}.html`` -- a per-customer HTML page with the
      OG / Twitter meta tags baked in (so Reddit / Twitter / LinkedIn
      preview correctly) and a ``<body data-slug="...">`` that the
      client-side ``r.js`` reads to fetch the JSON above.

    Per docs/SIMPLICITY-GUARDRAILS.md sections 3 and 5: default private,
    never publish without an explicit Rob-typed CLI flip, and never
    customize the page for the customer (it's the LaunchLook marketing
    surface, not a customer-owned site).
    """
    from scripts.sanitize_for_public import sanitize_report_json  # noqa: PLC0415

    raw_report = _build_public_report_dict(
        data,
        slug=slug,
        delivered_at=delivered_at,
        is_pro_handoff=has_handoff,
    )

    # Preserve existing public/shared state if a JSON already exists, so
    # re-running deliver_report.py doesn't quietly flip a live audit back
    # to private. The audit content itself is re-sanitized either way.
    json_path = SHAREABLE_REPORTS_DATA_DIR / f"{slug}.json"
    if json_path.exists():
        try:
            existing = json.loads(json_path.read_text(encoding="utf-8"))
            raw_report["is_public"] = bool(existing.get("is_public", False))
            prior_handoff = existing.get("handoff_report") or {}
            raw_report["handoff_report"]["shared"] = bool(
                raw_report["handoff_report"]["available"] and prior_handoff.get("shared", False)
            )
            if existing.get("share_history"):
                raw_report["share_history"] = existing["share_history"]
        except (ValueError, OSError):
            pass

    public_data = sanitize_report_json(raw_report, data["customer"])
    if raw_report.get("share_history"):
        public_data["share_history"] = raw_report["share_history"]

    SHAREABLE_REPORTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(public_data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    env = build_jinja_env()
    template = env.get_template("shareable.html.j2")
    html = template.render(
        customer_slug=slug,
        app_name=public_data.get("app_name", ""),
        audit_date_human=_format_audit_date_human(delivered_at),
        share_metadata=public_data.get("share_metadata", {}),
    )

    SHAREABLE_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    html_path = SHAREABLE_PAGES_DIR / f"{slug}.html"
    html_path.write_text(html, encoding="utf-8")

    return json_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--customer",
        required=True,
        help=(
            "Path to customer YAML for the regular delivery, OR the customer "
            "slug for --confidence-check (matched against "
            "data/confidence_checks/<slug>-*.yaml)."
        ),
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send via Resend (default is dry-run preview)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run (default behavior)")
    parser.add_argument("--no-open", action="store_true", help="Skip auto-opening PDFs in dry-run")
    parser.add_argument(
        "--qsg-link",
        default=None,
        help="Optional public URL of the QSG PDF (for the report cross-link)",
    )
    parser.add_argument("--yes", action="store_true", help="Skip the send confirmation prompt")
    parser.add_argument(
        "--confidence-check",
        action="store_true",
        help=(
            "Render the Confidence Check / Saboteur re-scan short-form report "
            "instead of the full audit (skips QSG; loads from "
            "data/confidence_checks/<customer>-*.yaml)."
        ),
    )
    parser.add_argument(
        "--handoff-report",
        action="store_true",
        help=(
            "Also render the Handoff Report (Markdown + PDF) for this customer. "
            "Pro Package customers get it bundled; Starter / Scale Up customers "
            "need --tier-override Starter+Handoff or Full+Handoff to signal that "
            "the $49 add-on has been paid. See docs/HANDOFF-REPORT-WORKFLOW.md."
        ),
    )
    parser.add_argument(
        "--tier-override",
        default=None,
        help=(
            "Override the YAML's customer.tier for delivery-side decisions "
            "(e.g. Handoff Report gating). Accepts: Starter, Full, Pro, "
            "Starter+Handoff, Full+Handoff, Pro+Handoff. The +Handoff suffix "
            "signals that the customer paid the $49 Handoff Report add-on."
        ),
    )
    parser.add_argument(
        "--provider",
        default="auto",
        help=(
            "LLM provider for the Handoff Report narrative pieces. One of "
            "auto, claude, gpt, stub. Defaults to auto (Claude > GPT > stub)."
        ),
    )
    args = parser.parse_args()

    if args.send and args.dry_run:
        sys.exit("ERROR: --send and --dry-run are mutually exclusive")

    if args.confidence_check:
        return deliver_confidence_check(args)

    customer_path = Path(args.customer).resolve()
    data = load_customer_yaml(customer_path)
    validate(data)

    customer = data["customer"]
    slug = slugify(customer.get("first_name", ""), customer.get("app_name", ""))
    delivered_at = date.today().isoformat()

    out_dir = OUTPUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    main_pdf = out_dir / "main-report.pdf"
    qsg_pdf = out_dir / "quick-start-guide.pdf"
    user_guide_pdf = out_dir / "user-guide.pdf"

    env = build_jinja_env()

    print(f"â†’ Customer:  {customer['first_name']} ({customer['email']})")
    print(f"â†’ App:       {customer['app_name']} [{customer['tier']}]")
    print(f"â†’ Findings:  {len(data['findings'])}")
    print(f"â†’ Output:    {out_dir.relative_to(REPO_ROOT)}")

    # Pro tier GitHub integration reminder. Never auto-runs: Rob has to
    # invoke scripts/github_push.py manually after reviewing the YAML.
    # See docs/GITHUB-INTEGRATION.md.
    if (
        customer["tier"] == "Pro Package"
        and isinstance(data.get("github"), dict)
        and data["github"].get("repo")
    ):
        print(
            "â†’ GitHub integration available for this customer. "
            f"Run: `python scripts/github_push.py --customer {args.customer}` "
            "after manual review."
        )

    main_html = render_main_report_html(env, data, delivered_at, args.qsg_link)
    html_to_pdf(main_html, main_pdf, customer["first_name"])
    print(f"  âœ“ wrote {main_pdf.name} ({main_pdf.stat().st_size / 1024:.1f} KB)")

    qsg_html = render_qsg_html(env, data, delivered_at)
    if qsg_html:
        html_to_pdf(qsg_html, qsg_pdf, customer["first_name"])
        print(f"  âœ“ wrote {qsg_pdf.name} ({qsg_pdf.stat().st_size / 1024:.1f} KB)")
    else:
        print("  ! no quick_start_guide section in YAML, skipping QSG PDF")

    ug_html = render_user_guide_html(env, data, delivered_at)
    if ug_html:
        html_to_pdf(ug_html, user_guide_pdf, customer["first_name"])
        print(f"  wrote {user_guide_pdf.name} ({user_guide_pdf.stat().st_size / 1024:.1f} KB)")
    elif customer.get("tier") in ("Scale Up Package", "Pro Package"):
        print("  ! no user_guide section in YAML (Scale Up/Pro), skipping User Guide PDF")

    attachments = [main_pdf]
    if qsg_html:
        attachments.append(qsg_pdf)
    if ug_html:
        attachments.append(user_guide_pdf)

    # Pre-Launch Checklist is bundled with every paid tier; this script is
    # only ever invoked for paid deliveries (free 3-finding audits go through
    # api/free-audit.py and do NOT include the checklist).
    checklist_pdf = out_dir / "pre-launch-checklist.pdf"
    checklist_html = render_pre_launch_checklist_html(env, data, delivered_at)
    html_to_pdf(checklist_html, checklist_pdf, customer["first_name"])
    print(f"  - wrote {checklist_pdf.name} ({checklist_pdf.stat().st_size / 1024:.1f} KB)")
    attachments.append(checklist_pdf)

    fix_pack_md = render_fix_pack_markdown(data, delivered_at)
    fix_pack_path = out_dir / "fix-pack.md"
    fix_pack_path.write_text(fix_pack_md, encoding="utf-8")
    print(f"  - wrote {fix_pack_path.name} ({fix_pack_path.stat().st_size / 1024:.1f} KB)")
    attachments.append(fix_pack_path)

    # q22: shareable hosted report page. Default is private (no
    # surprises). Customer opts in by replying 'share' to the delivery
    # email; Rob then runs scripts/share_report.py to flip.
    is_pro_for_handoff = customer["tier"] == "Pro Package"
    if args.tier_override:
        override_tier, has_addon = parse_tier_override(args.tier_override)
        if (override_tier and override_tier == "Pro Package") or has_addon:
            is_pro_for_handoff = True
    shareable_json, shareable_html = _generate_shareable_page(
        data,
        slug=slug,
        delivered_at=delivered_at,
        has_handoff=is_pro_for_handoff,
    )
    print(
        f"  âœ“ wrote {shareable_json.relative_to(REPO_ROOT)}"
        f" + {shareable_html.relative_to(REPO_ROOT)}"
        " (private by default)"
    )

    # Handoff Report (q18). Bundled for Pro Package; opt-in $49 add-on
    # for Starter / Scale Up signalled via --tier-override <Tier>+Handoff.
    handoff_md_path: Path | None = None
    handoff_pdf_path: Path | None = None
    if args.handoff_report:
        override_tier, has_handoff_addon = parse_tier_override(args.tier_override)
        effective_tier = override_tier or customer["tier"]
        is_pro = effective_tier == "Pro Package"
        if is_pro or has_handoff_addon:
            print(
                f"â†’ Handoff Report:  generating (tier={effective_tier!r}, "
                f"addon={has_handoff_addon})"
            )
            handoff_md_path, handoff_pdf_path = deliver_handoff_report(
                data,
                out_dir=out_dir,
                delivered_at=delivered_at,
                effective_tier=effective_tier,
                has_handoff_addon=has_handoff_addon,
                provider=args.provider,
                no_open=args.no_open or args.send,
            )
            if handoff_pdf_path:
                attachments.append(handoff_pdf_path)
        else:
            print(
                "â†’ Handoff Report:  SKIPPED â€” customer is not Pro Package and "
                "no --tier-override <Tier>+Handoff was passed."
            )

    if not args.send:
        if not args.no_open:
            open_in_viewer(main_pdf)
            if qsg_html:
                open_in_viewer(qsg_pdf)
            open_in_viewer(checklist_pdf)
        print(
            "\nDry-run complete. Review the PDFs, then re-run with --send to email them.\n"
            f"  python scripts/deliver_report.py --customer {args.customer} --send"
        )
        return 0

    subject, html_body, text_body = render_email_bodies(env, data, delivered_at)

    print("\n--- Send preview ---")
    print(f"  To:       {customer['email']}")
    print(f"  Subject:  {subject}")
    print(f"  Files:    {', '.join(p.name for p in attachments)}")
    if not args.yes:
        confirm = input("\nSend now? Type 'send' to confirm: ").strip().lower()
        if confirm != "send":
            print("Aborted. No email was sent.")
            return 1

    result = send_via_resend(
        to_email=customer["email"],
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        attachments=attachments,
    )
    msg_id = result.get("id") if isinstance(result, dict) else None
    print(f"\nâœ“ Sent. Resend message id: {msg_id or '(none returned)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
