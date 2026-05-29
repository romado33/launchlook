"""Fix Pack Markdown + paste-first wrappers for delivery surfaces.

Generates ``fix-pack.md`` from customer audit YAML (findings + verdict).
Used by ``deliver_report.py`` for email attachments and inline context.
"""

from __future__ import annotations

from typing import Any

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_LABELS = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}


def _builder_key(customer: dict[str, Any]) -> str:
    platform = (customer.get("platform") or "").strip().lower()
    builder = (customer.get("builder") or "").strip().lower()
    if platform == "webflow" or builder == "webflow":
        return "webflow"
    if builder in ("cursor",):
        return "cursor"
    if builder in ("v0",):
        return "v0"
    if builder in ("replit",):
        return "replit"
    return "default"


def paste_first_line(customer: dict[str, Any]) -> str:
    """One-line instruction shown above every fix block in PDF/email."""
    builder = customer.get("builder") or "your builder"
    key = _builder_key(customer)
    if key == "webflow":
        return (
            "Paste this first: follow each step in Webflow Designer, click Publish, "
            "then verify on your live URL before moving to the next finding."
        )
    if key == "cursor":
        return (
            "Paste this first: send the block below to Cursor Agent as one task. "
            "Apply the change, then verify on your live URL before the next finding."
        )
    if key == "v0":
        return (
            "Paste this first: send the block below to v0 or your editor chat as one task. "
            "Verify on your live URL before the next finding."
        )
    if key == "replit":
        return (
            "Paste this first: send the block below to Replit Agent as one message. "
            "Verify on your live URL before the next finding."
        )
    return (
        f"Paste this first: send the block below to {builder} as one message. "
        "Wait for it to apply, publish if needed, then verify on your live URL "
        "before the next finding."
    )


def wrap_fix_prompt(customer: dict[str, Any], fix_prompt: str) -> str:
    """Paste-first wrapper + fix body (for PDF blocks and Fix Pack sections)."""
    body = (fix_prompt or "").strip()
    if not body:
        return ""
    return f"{paste_first_line(customer)}\n\n{body}"


def render_builder_memory(
    customer: dict[str, Any],
    *,
    explicit: str | None = None,
) -> str | None:
    """Pro-tier 'builder memory' blurb for delivery email / Handoff.

    Rob can set ``builder_memory: |`` in customer YAML. When absent on Pro,
    we emit a short templated paragraph from intake fields.
    """
    if explicit and str(explicit).strip():
        return str(explicit).strip()

    tier = customer.get("tier") or ""
    if tier != "Pro Package":
        return None

    app = customer.get("app_name") or "this app"
    builder = customer.get("builder") or "their AI builder"
    url = ""
    if customer.get("app_url") and not customer.get("url_redacted"):
        url = customer["app_url"].strip()

    lines = [
        f"This is {app}, built with {builder}.",
        "LaunchLook ran a pre-launch checkup on the live URL (not the repo).",
    ]
    if url:
        lines.append(f"Live URL at audit time: {url}")
    if customer.get("primary_user_description"):
        lines.append(f"Primary users: {customer['primary_user_description'].strip()}")
    if customer.get("brand_tone"):
        lines.append(f"Tone to preserve: {customer['brand_tone'].strip()}")
    lines.append(
        "Fix the findings in the attached Fix Pack from the top down. "
        "Do not refactor unrelated code."
    )
    return " ".join(lines)


def _sorted_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [f for f in findings if isinstance(f, dict)],
        key=lambda f: (
            SEVERITY_ORDER.get((f.get("severity") or "low").lower(), 99),
            (f.get("title") or "").lower(),
        ),
    )


def render_fix_pack_markdown(data: dict[str, Any], delivered_at: str) -> str:
    """Full Fix Pack Markdown for attachment / paste into Cursor or Lovable."""
    customer = data.get("customer") or {}
    verdict = data.get("verdict") or {}
    findings = _sorted_findings(data.get("findings") or [])
    builder = customer.get("builder") or "your builder"
    app_name = customer.get("app_name") or "Your app"
    first = customer.get("first_name") or "there"

    lines: list[str] = [
        f"# Fix Pack — {app_name}",
        "",
        f"_Prepared {delivered_at} · LaunchLook pre-launch checkup for {first}_",
        "",
        f"Copy this file into {builder} (or Cursor) and work top to bottom. "
        "Each section is one finding with paste-ready fix text.",
        "",
    ]

    if verdict.get("summary"):
        lines.extend([f"**Verdict:** {verdict['summary']}", ""])

    memory = render_builder_memory(
        customer, explicit=data.get("builder_memory") or customer.get("builder_memory")
    )
    if memory:
        lines.extend(["## Builder memory (read this first)", "", memory, ""])

    lines.extend(["## Paste this first (every finding)", "", paste_first_line(customer), "", "---", ""])

    if not findings:
        lines.append("_No findings in this audit._")
        return "\n".join(lines)

    for i, f in enumerate(findings, start=1):
        sev = (f.get("severity") or "medium").lower()
        sev_label = SEVERITY_LABELS.get(sev, sev.title())
        title = f.get("title") or f"Finding {i}"
        lines.append(f"## {i}. {title}")
        lines.append("")
        lines.append(f"**Severity:** {sev_label}")
        lines.append("")
        if f.get("what_we_saw"):
            lines.append("**What we saw**")
            lines.append("")
            lines.append(f.get("what_we_saw").strip())
            lines.append("")
        if f.get("why_it_matters"):
            lines.append("**Why it matters**")
            lines.append("")
            lines.append(f.get("why_it_matters").strip())
            lines.append("")
        prompt = f.get("fix_prompt") or ""
        if prompt.strip():
            lines.append(f"**Paste into {builder}**")
            lines.append("")
            lines.append("```")
            lines.append(wrap_fix_prompt(customer, prompt))
            lines.append("```")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend(
        [
            "",
            "_Questions or want a Fix Check after you ship fixes? Reply to your LaunchLook delivery email._",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def enrich_findings_for_templates(
    findings: list[dict[str, Any]], customer: dict[str, Any]
) -> list[dict[str, Any]]:
    """Add ``fix_prompt_display`` for Jinja templates (PDF, Handoff)."""
    out: list[dict[str, Any]] = []
    for f in findings or []:
        if not isinstance(f, dict):
            continue
        row = dict(f)
        raw = row.get("fix_prompt") or ""
        if raw.strip():
            row["fix_prompt_display"] = wrap_fix_prompt(customer, raw)
        out.append(row)
    return out
