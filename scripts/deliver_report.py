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
OUTPUT_ROOT = REPO_ROOT / "output" / "reports"

VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_TIERS = {"Starter Package", "Full Package", "Pro Package"}


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

    cap = {"Starter Package": 7, "Full Package": 25, "Pro Package": 40}.get(tier, 25)
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
        ]),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )


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
        delivered_at=delivered_at,
        qsg_link=qsg_link,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--customer", required=True, help="Path to customer YAML")
    parser.add_argument("--send", action="store_true", help="Send via Resend (default is dry-run preview)")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run (default behavior)")
    parser.add_argument("--no-open", action="store_true", help="Skip auto-opening PDFs in dry-run")
    parser.add_argument("--qsg-link", default=None, help="Optional public URL of the QSG PDF (for the report cross-link)")
    parser.add_argument("--yes", action="store_true", help="Skip the send confirmation prompt")
    args = parser.parse_args()

    if args.send and args.dry_run:
        sys.exit("ERROR: --send and --dry-run are mutually exclusive")

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

    env = build_jinja_env()

    print(f"→ Customer:  {customer['first_name']} ({customer['email']})")
    print(f"→ App:       {customer['app_name']} [{customer['tier']}]")
    print(f"→ Findings:  {len(data['findings'])}")
    print(f"→ Output:    {out_dir.relative_to(REPO_ROOT)}")

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
