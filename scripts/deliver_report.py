"""
deliver_report.py: render Main Report + Quick Start Guide PDFs and email them.

Reads a customer YAML file (verdict, findings, QSG sections) and renders two
A4 PDFs with Playwright + Jinja2:

    output/reports/{slug}/main-report.pdf
    output/reports/{slug}/quick-start-guide.pdf

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
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

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
EMAIL_TEMPLATE_DIR = TEMPLATE_ROOT / "email"
# q6: Confidence Check / Saboteur re-scan add-on.
CONFIDENCE_CHECK_TEMPLATE_DIR = TEMPLATE_ROOT / "confidence_check"
HANDOFF_TEMPLATE_DIR = TEMPLATE_ROOT / "handoff"  # q18: Handoff Report
CONFIDENCE_CHECKS_DATA_DIR = REPO_ROOT / "data" / "confidence_checks"
OUTPUT_ROOT = REPO_ROOT / "output" / "reports"
CONFIDENCE_CHECK_OUTPUT_ROOT = REPO_ROOT / "output" / "confidence_checks"

VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_TIERS = {"Starter Package", "Scale Up Package", "Pro Package"}
VALID_PLATFORMS = {"vibe-coder", "webflow"}
DEFAULT_PLATFORM = "vibe-coder"


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

    # ``platform`` is optional. Legacy YAMLs without it default to vibe-coder
    # so existing customers keep rendering identically.
    platform = (customer.get("platform") or DEFAULT_PLATFORM).strip().lower()
    if platform not in VALID_PLATFORMS:
        sys.exit(
            f"ERROR: customer.platform must be one of {sorted(VALID_PLATFORMS)}, got: {platform!r}"
        )
    customer["platform"] = platform

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
        loader=FileSystemLoader([
            str(REPORT_TEMPLATE_DIR),
            str(QSG_TEMPLATE_DIR),
            str(EMAIL_TEMPLATE_DIR),
            str(CONFIDENCE_CHECK_TEMPLATE_DIR),
            str(HANDOFF_TEMPLATE_DIR),
        ]),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )


# ---------------------------------------------------------------------------
# Verified badge context (q17)
# ---------------------------------------------------------------------------

# Validity windows mirrored from scripts/generate_verified_badge.py so that
# the embed snippet in delivered emails / report PDFs surfaces the same
# expiry the badge JSON does. Keep these two maps in sync.
VERIFIED_BADGE_TIER_DAYS = {
    "Starter Package": 30,
    "Full Package": 90,
    "Scale Up Package": 90,
    "Pro Package": 180,
}
VERIFIED_BADGE_DOMAIN = "launchlook.app"


def _verified_badge_context(customer: dict[str, Any]) -> dict[str, Any] | None:
    """Build the `verified_badge` context dict for delivery templates.

    Mirrors the slug + validity window logic in
    `scripts/generate_verified_badge.py` so that the embed snippet baked
    into the delivery email / report PDF references the same URLs the
    actual badge generator will write under `landing/images/badges/{slug}/`.
    Returns `None` for tiers without a badge (defensive; we currently
    issue one for every paid tier).
    """
    tier = (customer.get("tier") or "").strip()
    validity_days = VERIFIED_BADGE_TIER_DAYS.get(tier)
    if not validity_days:
        return None

    raw_slug = customer.get("slug") or customer.get("customer_slug") or ""
    if not raw_slug:
        raw_slug = slugify(customer.get("first_name", ""), customer.get("app_name", ""))
    slug = slugify(raw_slug)

    builder = (customer.get("builder") or "").strip().lower()
    is_webflow = builder.startswith("webflow")

    base = f"https://{VERIFIED_BADGE_DOMAIN}"
    return {
        "customer_slug": slug,
        "tier": tier,
        "validity_days": validity_days,
        "verify_url": f"{base}/verify?slug={slug}",
        "badge_url_light": f"{base}/images/badges/{slug}/light.svg",
        "badge_url_dark": f"{base}/images/badges/{slug}/dark.svg",
        "is_webflow": is_webflow,
    }


def render_main_report_html(env, data: dict[str, Any], delivered_at: str, qsg_link: str | None) -> str:
    customer = dict(data["customer"])
    customer["url_redacted_or_shown"] = display_url(
        customer.get("app_url", ""), bool(customer.get("url_redacted")),
    )

    template = env.get_template("report.html.j2")
    return template.render(
        customer=customer,
        verdict=data["verdict"],
        findings=data["findings"],
        passed_checks=data.get("passed_checks", []) or [],
        delivered_at=delivered_at,
        qsg_link=qsg_link,
        verified_badge=_verified_badge_context(customer),
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
        'padding:0 20mm; font-family:-apple-system,sans-serif; '
        'display:flex; justify-content:space-between;">'
        f'<span>LaunchLook · launchlook.app · prepared {date.today().isoformat()}</span>'
        f'<span>Confidential, for {customer_name} only · '
        '<span class="pageNumber"></span> / <span class="totalPages"></span></span>'
        '</div>'
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
                header_template='<span></span>',
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

    html_tpl = env.get_template("delivery_pdf.html.j2")
    text_tpl = env.get_template("delivery_pdf.txt.j2")

    ctx = {
        "customer": customer,
        "n_findings": n_findings,
        "delivered_at": delivered_at,
        "verified_badge": _verified_badge_context(customer),
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

    encoded_attachments = []
    for path in attachments:
        encoded_attachments.append({
            "filename": path.name,
            "content": base64.b64encode(path.read_bytes()).decode("ascii"),
            "content_type": "application/pdf",
        })

    payload: dict[str, Any] = {
        "from": f"Rob at LaunchLook <{from_email}>",
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




# ---------------------------------------------------------------------------
# q6: Confidence Check / Saboteur re-scan delivery
# ---------------------------------------------------------------------------


def latest_confidence_check_for(customer_id: str) -> Path:
    """Return the most recent ``data/confidence_checks/<customer_id>-*.yaml``.

    ``customer_id`` can also be a full path to a YAML file (for callers that
    want to pin a specific re-scan).
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
            f"ERROR: no confidence_checks YAML found for customer {customer_id!r}. "
            "Run scripts/confidence_check.py first."
        )
    return matches[-1].resolve()


def render_confidence_check_html(env, data: dict[str, Any], delivered_at: str) -> str:
    template = env.get_template("confidence_check_report.html.j2")
    cc = data.get("confidence_check") or {}
    customer = {
        "first_name": cc.get("customer_first_name", "there"),
        "email": cc.get("customer_email", ""),
        "app_name": cc.get("app_name", ""),
        "app_url": cc.get("url", ""),
        "tier": cc.get("tier", ""),
        "builder": cc.get("builder", ""),
    }
    return template.render(
        confidence_check=cc,
        customer=customer,
        verdict=data.get("verdict", {}) or {},
        fixed=data.get("fixed", []) or [],
        still_present=data.get("still_present", []) or [],
        new=data.get("new", []) or [],
        footer_note=data.get("footer_note", ""),
        delivered_at=delivered_at,
        original_audit_id=cc.get("original_audit_id"),
    )


def render_confidence_check_email(env, data: dict[str, Any], delivered_at: str) -> tuple[str, str, str]:
    """Return ``(subject, text_body, html_body)`` for the Confidence Check email."""
    cc = data.get("confidence_check") or {}
    first_name = cc.get("customer_first_name", "there")
    customer = {
        "first_name": first_name,
        "email": cc.get("customer_email", ""),
        "app_name": cc.get("app_name", ""),
        "app_url": cc.get("url", ""),
    }
    subject = f"Your Confidence Check is in - {first_name}, here's what The Saboteur found"
    ctx = {
        "customer": customer,
        "confidence_check": cc,
        "first_name": first_name,
        "app_name": customer.get("app_name") or "your app",
        "verdict": data.get("verdict", {}) or {},
        "fixed_count": len(data.get("fixed", []) or []),
        "still_count": len(data.get("still_present", []) or []),
        "still_present_count": len(data.get("still_present", []) or []),
        "new_count": len(data.get("new", []) or []),
        "delivered_at": delivered_at,
    }
    text_body = env.get_template("confidence_check_email.txt.j2").render(**ctx)
    html_body = env.get_template("confidence_check_email.html.j2").render(**ctx)
    return subject, text_body, html_body


def deliver_confidence_check(args) -> int:
    """Render + (optionally) send the short-form Confidence Check report.

    Skips Quick Start Guide generation per q6 spec - Confidence Check ships
    only the short report.
    """
    try:
        import yaml
    except ImportError:
        sys.exit("ERROR: pyyaml not installed. Run: pip install -r requirements.txt")

    yaml_path = latest_confidence_check_for(args.customer)
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        sys.exit(f"ERROR: {yaml_path} did not parse as a YAML mapping")

    cc = data.get("confidence_check") or {}
    customer = {
        "first_name": cc.get("customer_first_name", "customer"),
        "email": cc.get("customer_email", ""),
        "app_name": cc.get("app_name", ""),
    }
    slug = slugify(customer.get("first_name", "customer"), customer.get("app_name", ""))
    delivered_at = date.today().isoformat()

    env = build_jinja_env()
    html = render_confidence_check_html(env, data, delivered_at)

    out_dir = CONFIDENCE_CHECK_OUTPUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "confidence-check.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"OK: HTML written to {html_path.relative_to(REPO_ROOT)}")

    pdf_path = out_dir / "confidence-check.pdf"
    try:
        html_to_pdf(html, pdf_path, customer.get("first_name", "customer"))
        print(f"OK: PDF written to {pdf_path.relative_to(REPO_ROOT)}")
    except SystemExit as exc:
        print(f"WARN: PDF skipped ({exc}). HTML preview at {html_path}.", file=sys.stderr)
        pdf_path = None

    subject, text_body, html_body = render_confidence_check_email(env, data, delivered_at)
    text_out = out_dir / "email.txt"
    html_out = out_dir / "email.html"
    text_out.write_text(text_body, encoding="utf-8")
    html_out.write_text(html_body, encoding="utf-8")
    print(f"OK: Email preview at {text_out.relative_to(REPO_ROOT)} / {html_out.relative_to(REPO_ROOT)}")
    print(f"   Subject: {subject}")

    if args.send:
        if not pdf_path or not pdf_path.exists():
            sys.exit("ERROR: cannot --send without a rendered PDF.")
        send_via_resend(
            to_email=customer.get("email", ""),
            subject=subject,
            text=text_body,
            html=html_body,
            attachments=[pdf_path],
            confirm=not args.yes,
        )
    elif not args.no_open and pdf_path and pdf_path.exists():
        open_in_viewer(pdf_path)

    return 0


# ---------------------------------------------------------------------------
# Handoff Report (q18)
# ---------------------------------------------------------------------------


# Tier aliases the CLI accepts on --tier-override. We canonicalize before
# routing through the Handoff Report code so that the template only ever
# sees "Starter Package" / "Scale Up Package" / "Pro Package".
TIER_ALIAS_TO_CANONICAL = {
    "starter": "Starter Package",
    "starter package": "Starter Package",
    "scale up": "Scale Up Package",
    "scaleup": "Scale Up Package",
    "scale up package": "Scale Up Package",
    "full": "Scale Up Package",  # legacy alias before q3 rename
    "full package": "Scale Up Package",
    "pro": "Pro Package",
    "pro package": "Pro Package",
}

HANDOFF_OVERRIDE_SEPARATOR = "+"
HANDOFF_OVERRIDE_SUFFIX = "handoff"


def parse_tier_override(raw: str | None) -> tuple[str | None, bool]:
    """Parse ``--tier-override`` into ``(canonical_tier, handoff_addon)``.

    Accepted shapes:
      ``"Pro"``               -> ("Pro Package", False)
      ``"Starter+Handoff"``   -> ("Starter Package", True)
      ``"Scale Up + Handoff"``-> ("Scale Up Package", True)
      ``None`` / ``""``       -> (None, False)
    """
    if not raw:
        return None, False
    parts = [p.strip().lower() for p in raw.split(HANDOFF_OVERRIDE_SEPARATOR) if p.strip()]
    if not parts:
        return None, False
    tier_alias = parts[0]
    tier = TIER_ALIAS_TO_CANONICAL.get(tier_alias)
    if tier is None:
        sys.exit(
            f"ERROR: --tier-override {raw!r} did not match a known tier. "
            f"Try: Starter, Scale Up, Pro, or any of these with +Handoff."
        )
    handoff_addon = any(p == HANDOFF_OVERRIDE_SUFFIX for p in parts[1:])
    return tier, handoff_addon


def severity_buckets_for_handoff(
    findings: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group findings into the three buckets the handoff template renders.

    ``critical`` rolls up into ``high`` because the handoff report uses
    three buckets (must / should / polish) per the q18 spec.
    """
    buckets: dict[str, list[dict[str, Any]]] = {"high": [], "medium": [], "low": []}
    for f in findings or []:
        sev = (f.get("severity") or "").strip().lower()
        if sev in {"critical", "high"}:
            buckets["high"].append(f)
        elif sev == "medium":
            buckets["medium"].append(f)
        else:
            buckets["low"].append(f)
    return buckets


def render_handoff_markdown(
    env,
    *,
    customer: dict[str, Any],
    verdict: dict[str, Any],
    passed_checks: list[dict[str, Any]],
    groups: dict[str, list[dict[str, Any]]],
    context_paragraph: str,
    recommended_order: str,
    code_review_notes: str,
    effective_tier: str,
    audit_date: str,
) -> str:
    tmpl = env.get_template("handoff.md.j2")
    return tmpl.render(
        customer=customer,
        verdict=verdict,
        passed_checks=passed_checks,
        findings_high=groups["high"],
        findings_medium=groups["medium"],
        findings_low=groups["low"],
        context_paragraph=context_paragraph,
        recommended_order=recommended_order,
        code_review_notes=code_review_notes,
        tier=effective_tier,
        audit_date=audit_date,
    )


def render_handoff_html(
    env,
    *,
    customer: dict[str, Any],
    verdict: dict[str, Any],
    passed_checks: list[dict[str, Any]],
    groups: dict[str, list[dict[str, Any]]],
    context_paragraph: str,
    recommended_order: str,
    code_review_notes: str,
    effective_tier: str,
    audit_date: str,
) -> str:
    tmpl = env.get_template("handoff.html.j2")
    return tmpl.render(
        customer=customer,
        verdict=verdict,
        passed_checks=passed_checks,
        groups=groups,
        context_paragraph=context_paragraph,
        recommended_order=recommended_order,
        code_review_notes=code_review_notes,
        tier=effective_tier,
        audit_date=audit_date,
    )


def deliver_handoff_report(
    env,
    *,
    data: dict[str, Any],
    paid_tier: str,
    handoff_addon: bool,
    delivered_at: str,
    out_dir: Path,
    customer_name: str,
    provider: str = "auto",
) -> tuple[Path, Path] | None:
    """Generate the Markdown + PDF Handoff Report when the customer is eligible.

    Eligibility per PRODUCT-DECISIONS.md section 8:
      * Pro Package -> Handoff Report is included for free.
      * Starter / Scale Up -> Handoff Report only ships when the customer
        bought the $99 add-on (``handoff_addon=True``).

    Returns ``(md_path, pdf_path)`` when files are written, or ``None`` when
    the customer is ineligible (caller can log and skip).
    """
    pro = paid_tier == "Pro Package"
    eligible = pro or handoff_addon
    if not eligible:
        return None

    # Lazy import to keep CLI startup snappy. deliver_report.py runs as
    # a script so the repo root is not yet on sys.path; add it before
    # importing the ai_audit package.
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from scripts.ai_audit import pipeline as ai_pipeline

    narrative = ai_pipeline.run_handoff_report(
        audit_payload=data,
        effective_tier=paid_tier,
        audit_date=delivered_at,
        provider=provider,
    )

    customer = (data or {}).get("customer") or {}
    verdict = (data or {}).get("verdict") or {}
    findings = (data or {}).get("findings") or []
    passed_checks = (data or {}).get("passed_checks") or []

    groups = severity_buckets_for_handoff(findings)

    md_text = render_handoff_markdown(
        env,
        customer=customer,
        verdict=verdict,
        passed_checks=passed_checks,
        groups=groups,
        context_paragraph=narrative["context_paragraph"],
        recommended_order=narrative["recommended_order"],
        code_review_notes=narrative["code_review_notes"],
        effective_tier=paid_tier,
        audit_date=delivered_at,
    )

    html_text = render_handoff_html(
        env,
        customer=customer,
        verdict=verdict,
        passed_checks=passed_checks,
        groups=groups,
        context_paragraph=narrative["context_paragraph"],
        recommended_order=narrative["recommended_order"],
        code_review_notes=narrative["code_review_notes"],
        effective_tier=paid_tier,
        audit_date=delivered_at,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "handoff_report.md"
    pdf_path = out_dir / "handoff_report.pdf"
    md_path.write_text(md_text, encoding="utf-8")
    html_to_pdf(html_text, pdf_path, customer_name)
    return md_path, pdf_path



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--customer", required=True, help="Path to customer YAML (or, with --confidence-check, customer slug)")
    parser.add_argument(
        "--confidence-check",
        action="store_true",
        help="q6: render the short-form Confidence Check report (skips QSG).",
    )
    parser.add_argument("--send", action="store_true", help="Send via Resend (default is dry-run preview)")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run (default behavior)")
    parser.add_argument("--no-open", action="store_true", help="Skip auto-opening PDFs in dry-run")
    parser.add_argument("--qsg-link", default=None, help="Optional public URL of the QSG PDF (for the report cross-link)")
    parser.add_argument("--yes", action="store_true", help="Skip the send confirmation prompt")
    parser.add_argument(
        "--handoff-report",
        action="store_true",
        help="Also generate the Handoff Report (Markdown + PDF) for this customer.",
    )
    parser.add_argument(
        "--tier-override",
        default=None,
        help=(
            "Override the tier declared in the customer YAML. Useful for the "
            "Starter+Handoff add-on flow. Accepts e.g. \"Starter+Handoff\", "
            "\"Scale Up+Handoff\", or just \"Pro\"."
        ),
    )
    parser.add_argument(
        "--provider",
        default="auto",
        choices=["auto", "claude", "gpt", "stub"],
        help="LLM provider for Handoff Report narrative pieces. Default: auto.",
    )
    args = parser.parse_args()

    if args.confidence_check:
        return deliver_confidence_check(args)


    if args.send and args.dry_run:
        sys.exit("ERROR: --send and --dry-run are mutually exclusive")

    customer_path = Path(args.customer).resolve()
    data = load_customer_yaml(customer_path)
    validate(data)

    # q18: Handoff Report (separate Markdown + PDF deliverable).
    if getattr(args, "handoff_report", False):
        tier_override, handoff_addon = parse_tier_override(
            getattr(args, "tier_override", None)
        )
        effective_tier = tier_override or (data.get("customer") or {}).get("tier") or ""
        if not handoff_addon and effective_tier != "Pro Package":
            # CLI requested --handoff-report explicitly so treat it as the
            # add-on being applied. Webhook callers set --tier-override
            # Starter+Handoff or pass --handoff-report for Pro.
            handoff_addon = effective_tier != "Pro Package"
        env = build_jinja_env()
        out_dir = REPO_ROOT / "out" / (
            slugify((data.get("customer") or {}).get("slug") or "handoff")
        )
        delivered_at = (
            (data.get("customer") or {}).get("audit_date")
            or date.today().isoformat()
        )
        customer_name = (
            (data.get("customer") or {}).get("first_name", "")
            + " "
            + (data.get("customer") or {}).get("last_name", "")
        ).strip() or "customer"
        result = deliver_handoff_report(
            env,
            data=data,
            paid_tier=effective_tier,
            handoff_addon=handoff_addon,
            delivered_at=delivered_at,
            out_dir=out_dir,
            customer_name=customer_name,
            provider=getattr(args, "provider", "auto"),
        )
        if result is None:
            print(
                "[handoff] customer not eligible for Handoff Report (free Pro "
                "or paid Starter/Scale Up add-on). Skipping."
            )
        else:
            md_path, pdf_path = result
            print(f"[handoff] wrote {md_path}")
            print(f"[handoff] wrote {pdf_path}")

    customer = data["customer"]
    slug = slugify(customer.get("first_name", ""), customer.get("app_name", ""))
    delivered_at = date.today().isoformat()

    out_dir = OUTPUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    main_pdf = out_dir / "main-report.pdf"
    qsg_pdf = out_dir / "quick-start-guide.pdf"

    env = build_jinja_env()

    print(f"→ Customer:  {customer['first_name']} ({customer['email']})")
    print(f"→ App:       {customer['app_name']} [{customer['tier']}]")
    print(f"→ Findings:  {len(data['findings'])}")
    print(f"→ Output:    {out_dir.relative_to(REPO_ROOT)}")

    # Pro tier GitHub integration reminder. Never auto-runs: Rob has to
    # invoke scripts/github_push.py manually after reviewing the YAML.
    # See docs/GITHUB-INTEGRATION.md.
    if customer["tier"] == "Pro Package" and isinstance(data.get("github"), dict) and data["github"].get("repo"):
        print(
            "→ GitHub integration available for this customer. "
            f"Run: `python scripts/github_push.py --customer {args.customer}` "
            "after manual review."
        )

    main_html = render_main_report_html(env, data, delivered_at, args.qsg_link)
    html_to_pdf(main_html, main_pdf, customer["first_name"])
    print(f"  ✓ wrote {main_pdf.name} ({main_pdf.stat().st_size / 1024:.1f} KB)")

    qsg_html = render_qsg_html(env, data, delivered_at)
    if qsg_html:
        html_to_pdf(qsg_html, qsg_pdf, customer["first_name"])
        print(f"  ✓ wrote {qsg_pdf.name} ({qsg_pdf.stat().st_size / 1024:.1f} KB)")
    else:
        print("  ! no quick_start_guide section in YAML, skipping QSG PDF")

    attachments = [main_pdf]
    if qsg_html:
        attachments.append(qsg_pdf)

    if not args.send:
        if not args.no_open:
            open_in_viewer(main_pdf)
            if qsg_html:
                open_in_viewer(qsg_pdf)
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
    print(f"\n✓ Sent. Resend message id: {msg_id or '(none returned)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
