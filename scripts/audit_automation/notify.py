"""Founder notification emails after automation draft (never customer delivery)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from scripts.audit_automation.jobs import AuditJob
from scripts.launchlook_constants import FREE_AUDIT_DELIVER_COUNT

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_findings(yaml_rel: str) -> list[dict[str, Any]]:
    """Read findings from the written YAML. Returns [] on any error."""
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return []
    try:
        path = REPO_ROOT / yaml_rel
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return list(data.get("findings") or [])
    except Exception:  # noqa: BLE001
        return []


def _format_findings_text(findings: list[dict[str, Any]]) -> str:
    """Render findings as plain text for inline email display."""
    if not findings:
        return ""
    lines: list[str] = []
    for i, f in enumerate(findings, 1):
        sev = (f.get("severity") or "").upper()
        title = f.get("title") or ""
        saw = (f.get("what_we_saw") or "").strip()
        matters = (f.get("why_it_matters") or "").strip()
        fix = (f.get("fix_prompt") or "").strip()
        lines.append(
            f"\n── FINDING {i}/{len(findings)} ─ {sev} "
            + "─" * max(0, 52 - len(sev) - len(str(i)) - len(str(len(findings))))
        )
        lines.append(title)
        if saw:
            lines.append(f"WHAT WE SAW: {saw}")
        if matters:
            lines.append(f"WHY IT MATTERS: {matters}")
        if fix:
            lines.append(f"FIX PROMPT: {fix}")
    return "\n".join(lines)


def _build_mailto(
    job: AuditJob,
    findings: list[dict[str, Any]],
    deliver_count: int,
) -> str:
    """Build a mailto: link that opens a pre-composed delivery draft in Gmail.

    For free audits the body includes only the top ``deliver_count`` findings.
    For paid audits all findings are included (founder trims before sending).
    """
    import urllib.parse

    top = findings[:deliver_count] if job.kind.value == "free" else findings
    app_name = job.app_name or job.url

    subject = f"Your LaunchLook findings for {app_name}"

    lines = [
        "Hi there,",
        "",
        f"I reviewed {job.url} and here are your findings:",
        "",
    ]
    for i, f in enumerate(top, 1):
        sev = (f.get("severity") or "").capitalize()
        title = f.get("title") or ""
        saw = (f.get("what_we_saw") or "").strip()
        fix = (f.get("fix_prompt") or "").strip()
        lines.append(f"── {i}. [{sev}] {title}")
        if saw:
            lines.append(f"   {saw}")
        if fix:
            lines.append(f"   Fix: {fix}")
        lines.append("")

    lines += [
        "Let me know if you have any questions.",
        "",
        "Rob",
        "LaunchLook",
    ]

    body = "\n".join(lines)
    params = urllib.parse.urlencode(
        {"subject": subject, "body": body}, quote_via=urllib.parse.quote
    )
    return f"mailto:{job.email}?{params}"


def _post_resend(payload: dict[str, Any], context: str) -> bool:
    api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    if not api_key:
        print(f"[automation] WARN: RESEND_API_KEY missing; skip {context}", flush=True)
        return False
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Cloudflare in front of Resend's API blocks the default
            # "Python-urllib/X.Y" UA with HTTP 403 + Cloudflare error 1010.
            # Identify ourselves explicitly so the WAF lets us through.
            "User-Agent": "LaunchLook-Automation/1.0 (+https://launchlook.app)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:  # noqa: S310
            resp.read()
        return True
    except urllib.error.HTTPError as exc:
        print(
            f"[automation] WARN: Resend HTTP {exc.code} on {context}: {exc.read()[:200]!r}",
            flush=True,
        )
    except urllib.error.URLError as exc:
        print(f"[automation] WARN: Resend error on {context}: {exc}", flush=True)
    return False


def send_draft_ready_email(
    job: AuditJob,
    *,
    findings_count: int,
    yaml_rel: str,
    form_smoke_ran: bool,
    form_smoke_failed: list[str],
    email_roundtrip_ran: bool,
    error: str | None = None,
) -> None:
    admin = (os.getenv("ADMIN_EMAIL") or "").strip()
    if not admin:
        print("[automation] WARN: ADMIN_EMAIL missing; skip draft-ready email", flush=True)
        return

    from_email = (os.getenv("FROM_EMAIL") or "hello@launchlook.app").strip()
    kind_label = "Free audit" if job.kind.value == "free" else f"Paid ({job.tier})"

    notion_url = (
        "https://notion.so/" + job.notion_page_id.replace("-", "")
        if job.notion_page_id and not job.notion_page_id.startswith("(")
        else None
    )

    if error:
        subject = f"[LaunchLook] Automation failed: {job.slug}"
        body = (
            f"{kind_label} automation failed.\n\n"
            f"URL: {job.url}\n"
            f"Email: {job.email}\n"
            f"Slug: {job.slug}\n"
            f"Notion page: {notion_url or job.notion_page_id}\n\n"
            f"Error:\n{error}\n\n"
            "Fix and re-run:\n"
            f"  python scripts/process_audit_queue.py --slug {job.slug}\n"
        )
    else:
        subject = f"[LaunchLook] Draft ready for review: {job.slug}"
        deliver_note = (
            f"Pick top {FREE_AUDIT_DELIVER_COUNT} by severity, then deliver free email."
            if job.kind.value == "free"
            else "Review findings, QSG if Scale Up/Pro, then deliver PDFs when ready."
        )
        findings = _load_findings(yaml_rel)
        body = (
            f"{kind_label} — AI draft is ready. Customer has NOT been emailed.\n\n"
            f"URL: {job.url}\n"
            f"Email: {job.email}\n"
            f"Tier: {job.tier}\n"
            f"Slug: {job.slug}\n"
            f"Findings in draft: {findings_count}\n"
        )
        body += f"\nForm smoke: {'ran' if form_smoke_ran else 'skipped/failed'}\n"
        if form_smoke_failed:
            body += f"Form smoke issues: {', '.join(form_smoke_failed[:5])}\n"
        if email_roundtrip_ran:
            body += "Email round-trip: attempted (check your inbox for smoke-test mail).\n"
        findings_text = _format_findings_text(findings)
        if findings_text:
            body += f"\n{'═' * 60}{findings_text}\n{'═' * 60}\n"

        mailto = _build_mailto(job, findings, FREE_AUDIT_DELIVER_COUNT)

        # Start the review server once; all links below then work.
        start_cmd = "python scripts/audit_ui.py"
        review_url = f"http://localhost:8000/review/{job.slug}"
        preview_url = f"http://localhost:8000/preview/{job.slug}"

        body += (
            "\n--- Your checklist ---\n"
            f"1. Start the review server (if not already running):\n"
            f"   {start_cmd}\n\n"
            f"2. Refine findings (opens the editor):\n"
            f"   {review_url}\n\n"
            f"3. Preview the report as it will look in the PDF:\n"
            f"   {preview_url}\n\n"
            f"4. Happy with it? Click to open a delivery draft email to the customer:\n"
            f"   {mailto}\n\n"
            f"5. {deliver_note}\n"
            "6. Mark Notion row delivered when done.\n"
        )
        if notion_url:
            body += f"\nNotion row: {notion_url}\n"

    payload: dict[str, Any] = {
        "from": f"LaunchLook Automation <{from_email}>",
        "to": [admin],
        "subject": subject,
        "text": body,
        "reply_to": job.email,
    }
    _post_resend(payload, "draft-ready")
