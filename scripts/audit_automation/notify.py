"""Founder notification emails after automation draft (never customer delivery).

Emails are sent as multipart (HTML + plain text). The HTML version keeps the
long ``mailto:`` delivery-draft URL behind a clean anchor tag so Gmail does
not autolink half of it and spill the query string into the visible body.
The plain text version uses a compact ``mailto:`` (subject only, no body) as
a fallback for clients that don't render HTML.
"""

from __future__ import annotations

import datetime
import html
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from scripts.audit_automation.jobs import AuditJob
from scripts.launchlook_constants import FREE_AUDIT_DELIVER_COUNT

REPO_ROOT = Path(__file__).resolve().parents[2]
_LOG_PATH = REPO_ROOT / "logs" / "email_sends.jsonl"


def _append_send_log(
    *,
    slug: str,
    tier: str,
    email: str,
    findings_count: int,
    status: str,
    status_code: int | None = None,
    context: str = "draft-ready",
) -> None:
    """Append one JSON line to logs/email_sends.jsonl. Never raises."""
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "context": context,
            "slug": slug,
            "tier": tier,
            "email": email,
            "findings_count": findings_count,
            "status": status,
            "status_code": status_code,
        }
        with _LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:  # noqa: BLE001
        pass  # log failure must never crash the caller


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


def _build_delivery_subject(job: AuditJob) -> str:
    app_name = job.app_name or job.url
    return f"Your LaunchLook findings for {app_name}"


def _build_delivery_body(
    job: AuditJob,
    findings: list[dict[str, Any]],
    deliver_count: int,
) -> str:
    """Build the plain-text body that goes inside the delivery-draft mailto."""
    top = findings[:deliver_count] if job.kind.value == "free" else findings
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
        lines.append(f"-- {i}. [{sev}] {title}")
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
    return "\n".join(lines)


def _build_mailto(
    job: AuditJob,
    findings: list[dict[str, Any]],
    deliver_count: int,
) -> str:
    """Full mailto: link with pre-composed subject AND body. Used in HTML email."""
    subject = _build_delivery_subject(job)
    body = _build_delivery_body(job, findings, deliver_count)
    params = urllib.parse.urlencode({"subject": subject, "body": body}, quote_via=urllib.parse.quote)
    return f"mailto:{job.email}?{params}"


def _build_mailto_compact(job: AuditJob) -> str:
    """Compact mailto: subject only, no body. Safe for plain-text fallback."""
    subject = _build_delivery_subject(job)
    params = urllib.parse.urlencode({"subject": subject}, quote_via=urllib.parse.quote)
    return f"mailto:{job.email}?{params}"


def _render_html_email(
    *,
    job: AuditJob,
    kind_label: str,
    findings_count: int,
    findings: list[dict[str, Any]],
    form_smoke_ran: bool,
    form_smoke_failed: list[str],
    email_roundtrip_ran: bool,
    review_url: str,
    preview_url: str,
    start_cmd: str,
    mailto_full: str,
    deliver_note: str,
    notion_url: str | None,
) -> str:
    """Render the founder notification as inline-styled HTML.

    Inline styles only (no <style> block) so Gmail and Outlook render it
    consistently without stripping anything.
    """
    e = html.escape

    sev_color = {
        "critical": "#b00020",
        "high": "#d97706",
        "medium": "#0369a1",
        "low": "#475569",
    }

    findings_html_parts: list[str] = []
    for i, f in enumerate(findings, 1):
        sev = (f.get("severity") or "").lower()
        color = sev_color.get(sev, "#475569")
        title = e(f.get("title") or "")
        saw = e((f.get("what_we_saw") or "").strip())
        matters = e((f.get("why_it_matters") or "").strip())
        fix = e((f.get("fix_prompt") or "").strip())
        findings_html_parts.append(
            f"""
<div style="border-left:3px solid {color};padding:8px 12px;margin:12px 0;background:#fafafa;">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:{color};font-weight:600;">
    Finding {i}/{findings_count} &middot; {e(sev.upper())}
  </div>
  <div style="font-weight:600;color:#111;margin-top:2px;">{title}</div>
  {f'<div style="margin-top:6px;color:#333;font-size:13px;"><b>What we saw:</b> {saw}</div>' if saw else ''}
  {f'<div style="margin-top:4px;color:#333;font-size:13px;"><b>Why it matters:</b> {matters}</div>' if matters else ''}
  {f'<div style="margin-top:4px;color:#333;font-size:13px;"><b>Paste into builder:</b> {fix}</div>' if fix else ''}
</div>"""
        )
    findings_html = "".join(findings_html_parts) or "<p><em>No findings in YAML.</em></p>"

    smoke_line = (
        f"<li><b>Form smoke:</b> {'ran &#10003;' if form_smoke_ran else 'not run (Playwright unavailable or no forms detected)'}"
        + (f" &mdash; issues flagged: {e(', '.join(form_smoke_failed[:5]))}" if form_smoke_failed else "")
        + "</li>"
    )
    roundtrip_line = (
        "<li><b>Email round-trip:</b> attempted (check your inbox for smoke-test mail).</li>"
        if email_roundtrip_ran
        else ""
    )
    notion_line = (
        f'<p style="font-size:13px;color:#555;">Notion row: <a href="{e(notion_url)}">{e(notion_url)}</a></p>'
        if notion_url
        else ""
    )

    return f"""<!doctype html>
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#111;max-width:680px;margin:0 auto;padding:16px;">
  <h2 style="margin:0 0 4px 0;font-weight:600;">{e(kind_label)} &mdash; AI draft is ready</h2>
  <p style="margin:0 0 16px 0;color:#666;font-size:13px;">Customer has NOT been emailed. Review, then deliver manually.</p>

  <table style="font-size:14px;border-collapse:collapse;margin-bottom:8px;">
    <tr><td style="padding:2px 12px 2px 0;color:#666;">URL</td><td><a href="{e(job.url)}">{e(job.url)}</a></td></tr>
    <tr><td style="padding:2px 12px 2px 0;color:#666;">Customer email</td><td>{e(job.email)}</td></tr>
    <tr><td style="padding:2px 12px 2px 0;color:#666;">Tier</td><td>{e(job.tier)}</td></tr>
    <tr><td style="padding:2px 12px 2px 0;color:#666;">Slug</td><td><code>{e(job.slug)}</code></td></tr>
    <tr><td style="padding:2px 12px 2px 0;color:#666;">Findings</td><td>{findings_count}</td></tr>
  </table>
  <ul style="font-size:13px;color:#555;margin:0 0 16px 0;padding-left:20px;">
    {smoke_line}
    {roundtrip_line}
  </ul>

  <h3 style="margin:24px 0 8px 0;border-bottom:1px solid #eee;padding-bottom:6px;">Your checklist</h3>
  <ol style="font-size:14px;line-height:1.6;padding-left:22px;">
    <li>Start the review server (if not already running):<br>
      <code style="background:#f4f4f5;padding:2px 6px;border-radius:3px;">{e(start_cmd)}</code>
    </li>
    <li><a href="{e(review_url)}" style="display:inline-block;background:#111;color:#fff;text-decoration:none;padding:8px 14px;border-radius:6px;margin:6px 0;">Refine findings &rarr;</a></li>
    <li><a href="{e(preview_url)}" style="display:inline-block;background:#fff;color:#111;text-decoration:none;padding:8px 14px;border-radius:6px;border:1px solid #ddd;margin:6px 0;">Preview report PDF &rarr;</a></li>
    <li>Happy with it?
      <a href="{mailto_full}" style="display:inline-block;background:#0369a1;color:#fff;text-decoration:none;padding:8px 14px;border-radius:6px;margin:6px 0;">Open delivery draft email &rarr;</a>
    </li>
    <li>{e(deliver_note)}</li>
    <li>Mark Notion row delivered when done.</li>
  </ol>

  {notion_line}

  <h3 style="margin:24px 0 8px 0;border-bottom:1px solid #eee;padding-bottom:6px;">Findings preview</h3>
  {findings_html}
</body></html>"""


def _post_resend(payload: dict[str, Any], context: str) -> tuple[bool, int | None]:
    """POST to Resend API. Returns (ok, http_status_code)."""
    api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    if not api_key:
        print(f"[automation] WARN: RESEND_API_KEY missing; skip {context}", flush=True)
        return False, None
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
        return True, 200
    except urllib.error.HTTPError as exc:
        print(
            f"[automation] WARN: Resend HTTP {exc.code} on {context}: {exc.read()[:200]!r}",
            flush=True,
        )
        return False, exc.code
    except urllib.error.URLError as exc:
        print(f"[automation] WARN: Resend error on {context}: {exc}", flush=True)
    return False, None


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
        payload: dict[str, Any] = {
            "from": f"LaunchLook Automation <{from_email}>",
            "to": [admin],
            "subject": subject,
            "text": body,
            "reply_to": job.email,
        }
        ok, code = _post_resend(payload, "draft-ready")
        _append_send_log(
            slug=job.slug,
            tier=job.tier,
            email=job.email,
            findings_count=findings_count,
            status="ok" if ok else "failed",
            status_code=code,
        )
        return

    subject = f"[LaunchLook] Draft ready for review: {job.slug}"
    deliver_note = (
        f"Pick top {FREE_AUDIT_DELIVER_COUNT} by severity, then deliver free email."
        if job.kind.value == "free"
        else "Review findings, QSG if Scale Up/Pro, then deliver PDFs when ready."
    )
    findings = _load_findings(yaml_rel)
    mailto_full = _build_mailto(job, findings, FREE_AUDIT_DELIVER_COUNT)
    mailto_compact = _build_mailto_compact(job)
    start_cmd = "python scripts/audit_ui.py"
    review_url = f"http://localhost:8000/review/{job.slug}"
    preview_url = f"http://localhost:8000/preview/{job.slug}"

    # ---- Plain-text fallback (no monster mailto URL) ----
    text_body = (
        f"{kind_label} — AI draft is ready. Customer has NOT been emailed.\n\n"
        f"URL: {job.url}\n"
        f"Email: {job.email}\n"
        f"Tier: {job.tier}\n"
        f"Slug: {job.slug}\n"
        f"Findings in draft: {findings_count}\n"
    )
    text_body += f"\nForm smoke: {'ran' if form_smoke_ran else 'not run (Playwright unavailable or no forms detected)'}\n"
    if form_smoke_failed:
        text_body += f"Form smoke issues: {', '.join(form_smoke_failed[:5])}\n"
    if email_roundtrip_ran:
        text_body += "Email round-trip: attempted (check your inbox for smoke-test mail).\n"
    findings_text = _format_findings_text(findings)
    if findings_text:
        text_body += f"\n{'=' * 60}{findings_text}\n{'=' * 60}\n"

    text_body += (
        "\n--- Your checklist ---\n"
        f"1. Start the review server (if not already running):\n"
        f"   {start_cmd}\n\n"
        f"2. Refine findings (opens the editor):\n"
        f"   {review_url}\n\n"
        f"3. Preview the report as it will look in the PDF:\n"
        f"   {preview_url}\n\n"
        f"4. Happy with it? Open a delivery draft (subject only, paste findings yourself):\n"
        f"   {mailto_compact}\n"
        f"   (HTML view of this email has a one-click button with findings pre-filled.)\n\n"
        f"5. {deliver_note}\n"
        "6. Mark Notion row delivered when done.\n"
    )
    if notion_url:
        text_body += f"\nNotion row: {notion_url}\n"

    # ---- HTML body (proper anchors so long mailto stays out of the visible body) ----
    html_body = _render_html_email(
        job=job,
        kind_label=kind_label,
        findings_count=findings_count,
        findings=findings,
        form_smoke_ran=form_smoke_ran,
        form_smoke_failed=form_smoke_failed,
        email_roundtrip_ran=email_roundtrip_ran,
        review_url=review_url,
        preview_url=preview_url,
        start_cmd=start_cmd,
        mailto_full=mailto_full,
        deliver_note=deliver_note,
        notion_url=notion_url,
    )

    payload: dict[str, Any] = {
        "from": f"LaunchLook Automation <{from_email}>",
        "to": [admin],
        "subject": subject,
        "text": text_body,
        "html": html_body,
        "reply_to": job.email,
    }
    ok, code = _post_resend(payload, "draft-ready")
    _append_send_log(
        slug=job.slug,
        tier=job.tier,
        email=job.email,
        findings_count=findings_count,
        status="ok" if ok else "failed",
        status_code=code,
    )


def send_plain_admin_email(
    subject: str,
    html_body: str,
    text_body: str,
    *,
    context: str = "admin",
) -> bool:
    """Send an arbitrary HTML+text email to ADMIN_EMAIL. Returns True on success.

    Used by maintenance scripts (heartbeat, stale-queue, digest) that don't
    operate on a specific AuditJob. Never raises; logs on failure.
    """
    admin = (os.getenv("ADMIN_EMAIL") or "").strip()
    from_email = (os.getenv("FROM_EMAIL") or "hello@launchlook.app").strip()
    if not admin:
        print(f"[automation] WARN: ADMIN_EMAIL missing; skip {context}", flush=True)
        return False
    payload: dict[str, Any] = {
        "from": f"LaunchLook Automation <{from_email}>",
        "to": [admin],
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }
    ok, _ = _post_resend(payload, context)
    return ok
