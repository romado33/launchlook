"""Form data → customer YAML serialization.

The audit UI posts JSON describing a customer review. This module turns that
payload into a YAML file that round-trips cleanly through
``scripts/deliver_report.py``: the same multi-line block style as the
hand-written examples (``customers/example-jane-sparkle.yaml``,
``customers/lilo-test.yaml``), severities sorted critical → low, and only
the keys ``deliver_report.py`` reads.

The serializer is intentionally hand-rolled rather than using ``yaml.dump``
so we can guarantee:

* multi-line strings are emitted as ``|`` literal blocks (not folded, not
  quoted), preserving newlines exactly as Rob types them
* single-line strings are emitted bare, except where escaping forces quoting
* the ``verdict.emoji`` value stays double-quoted for visual parity with the
  existing examples
* keys land in a stable, human-friendly order regardless of how the form
  serialized them

The output is then re-parsed with ``yaml.safe_load`` to confirm it is valid
YAML before we hand it back to the caller.
"""

from __future__ import annotations

import re
from typing import Any

import yaml


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
VALID_SEVERITIES = ("critical", "high", "medium", "low")
VALID_TIERS = ("Starter Package", "Full Package")
VALID_BUILDERS = ("Lovable", "Bolt", "v0", "Base44", "Replit", "Cursor", "Other")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort findings by severity (critical → low). Stable within a severity."""
    return sorted(
        findings,
        key=lambda f: SEVERITY_ORDER.get(_normalize_severity(f.get("severity")), 99),
    )


def form_to_yaml(payload: dict[str, Any]) -> str:
    """Serialize a form payload (dict) to a customer YAML string.

    The payload is expected to look like::

        {
          "customer": { ... },
          "verdict": { ... },
          "findings": [ ... ],
          "quick_start_guide": { ... }   # optional
        }

    Severities are sorted, empty optional fields are dropped, and strings
    are formatted as either bare scalars or ``|`` literal blocks depending
    on whether they contain newlines.
    """
    customer = _clean_customer(payload.get("customer", {}))
    verdict = _clean_verdict(payload.get("verdict", {}))
    findings = sort_findings(_clean_findings(payload.get("findings", [])))

    lines: list[str] = []

    lines.append("customer:")
    lines.extend(_indent(_emit_mapping(customer, _CUSTOMER_KEYS), 1))
    lines.append("")

    lines.append("verdict:")
    lines.extend(_indent(_emit_mapping(verdict, _VERDICT_KEYS), 1))
    lines.append("")

    lines.append("findings:")
    if not findings:
        lines.append("  []")
    else:
        for i, finding in enumerate(findings):
            block = _emit_mapping(finding, _FINDING_KEYS)
            if not block:
                continue
            block[0] = "- " + block[0]
            block[1:] = ["  " + ln if ln else ln for ln in block[1:]]
            lines.extend(_indent(block, 1))
            if i != len(findings) - 1:
                lines.append("")

    if customer.get("tier") == "Full Package":
        qsg = _clean_qsg(payload.get("quick_start_guide", {}))
        if qsg:
            lines.append("")
            lines.append("quick_start_guide:")
            lines.extend(_indent(_emit_qsg(qsg), 1))

    text = "\n".join(lines).rstrip() + "\n"

    parsed = yaml.safe_load(text)
    if not isinstance(parsed, dict):
        raise ValueError("Internal error: serialized YAML did not round-trip as a mapping")

    return text


# ---------------------------------------------------------------------------
# Cleaning helpers — strip empty optional fields and normalize values.
# ---------------------------------------------------------------------------


_CUSTOMER_KEYS = (
    "first_name",
    "last_name",
    "email",
    "app_name",
    "app_url",
    "url_redacted",
    "tier",
    "builder",
)

_VERDICT_KEYS = ("emoji", "summary", "narrative")

_FINDING_KEYS = (
    "severity",
    "title",
    "what_we_saw",
    "why_it_matters",
    "screenshot_path",
    "screenshot_caption",
    "fix_prompt",
)

_QSG_KEYS = ("title", "intro", "steps", "footer_note")


def _clean_customer(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in _CUSTOMER_KEYS:
        val = raw.get(key)
        if key == "url_redacted":
            out[key] = bool(val)
            continue
        if isinstance(val, str):
            val = val.strip()
        if val:
            out[key] = val
    return out


def _clean_verdict(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in _VERDICT_KEYS:
        val = raw.get(key)
        if isinstance(val, str):
            val = val.strip("\n")
            if key != "narrative":
                val = val.strip()
        if val:
            out[key] = val
    return out


def _clean_findings(raw: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for entry in raw or []:
        if not isinstance(entry, dict):
            continue
        cleaned: dict[str, Any] = {}
        for key in _FINDING_KEYS:
            val = entry.get(key)
            if isinstance(val, str):
                val = val.strip("\n") if key in ("what_we_saw", "why_it_matters", "fix_prompt") else val.strip()
            if key == "severity":
                val = _normalize_severity(val)
            if val:
                cleaned[key] = val
        if cleaned.get("severity") and cleaned.get("title"):
            out.append(cleaned)
    return out


def _clean_qsg(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, Any] = {}
    title = (raw.get("title") or "").strip()
    intro = (raw.get("intro") or "").strip("\n").strip()
    footer = (raw.get("footer_note") or "").strip("\n").strip()
    steps_in = raw.get("steps") or []
    steps_out: list[dict[str, str]] = []
    for step in steps_in:
        if not isinstance(step, dict):
            continue
        stitle = (step.get("title") or "").strip()
        sbody = (step.get("body") or "").strip("\n").strip()
        if stitle or sbody:
            entry: dict[str, str] = {}
            if stitle:
                entry["title"] = stitle
            if sbody:
                entry["body"] = sbody
            steps_out.append(entry)
    if title:
        out["title"] = title
    if intro:
        out["intro"] = intro
    if steps_out:
        out["steps"] = steps_out
    if footer:
        out["footer_note"] = footer
    return out


def _normalize_severity(val: Any) -> str:
    if not isinstance(val, str):
        return ""
    val = val.strip().lower()
    return val if val in VALID_SEVERITIES else ""


# ---------------------------------------------------------------------------
# Emission helpers — turn a cleaned dict into a list of YAML lines.
# ---------------------------------------------------------------------------


def _emit_mapping(data: dict[str, Any], key_order: tuple[str, ...]) -> list[str]:
    lines: list[str] = []
    for key in key_order:
        if key not in data:
            continue
        val = data[key]
        lines.extend(_emit_kv(key, val))
    return lines


def _emit_kv(key: str, val: Any) -> list[str]:
    if isinstance(val, bool):
        return [f"{key}: {'true' if val else 'false'}"]
    if isinstance(val, (int, float)):
        return [f"{key}: {val}"]
    if not isinstance(val, str):
        return [f"{key}: {yaml.safe_dump(val).strip()}"]

    if key == "emoji":
        return [f'{key}: "{val}"']

    if "\n" in val:
        block = ["|"]
        for line in val.splitlines():
            block.append("  " + line if line else "")
        block[0] = f"{key}: |"
        return block

    return [f"{key}: {_format_scalar(val)}"]


def _format_scalar(s: str) -> str:
    """Format a single-line string. Quote only when YAML would mis-parse it."""
    if s == "":
        return '""'
    if _needs_quoting(s):
        return _double_quote(s)
    return s


_QUOTE_TRIGGERS = re.compile(
    r"""
    ^[\s\-?:,\[\]\{\}\#\&\*\!\|\>\'\"\%\@\`]    # leading specials
    | :\s | \s\#                                # mid-string sequences
    | ^(true|false|null|yes|no|on|off|~)$       # YAML reserved scalars
    | ^[0-9]                                     # numeric-looking
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _needs_quoting(s: str) -> bool:
    if s != s.strip():
        return True
    if _QUOTE_TRIGGERS.search(s):
        return True
    if s.lower() in {"true", "false", "null", "yes", "no", "on", "off", "~"}:
        return True
    try:
        parsed = yaml.safe_load(s)
    except yaml.YAMLError:
        return True
    if not isinstance(parsed, str) or parsed != s:
        return True
    return False


def _double_quote(s: str) -> str:
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _indent(lines: list[str], levels: int) -> list[str]:
    pad = "  " * levels
    return [pad + ln if ln else ln for ln in lines]


def _emit_qsg(qsg: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if "title" in qsg:
        lines.extend(_emit_kv("title", qsg["title"]))
    if "intro" in qsg:
        lines.extend(_emit_kv("intro", qsg["intro"]))
    steps = qsg.get("steps") or []
    if steps:
        lines.append("steps:")
        for step in steps:
            block: list[str] = []
            if "title" in step:
                block.extend(_emit_kv("title", step["title"]))
            if "body" in step:
                block.extend(_emit_kv("body", step["body"]))
            if not block:
                continue
            block[0] = "- " + block[0]
            block[1:] = ["  " + ln if ln else ln for ln in block[1:]]
            lines.extend(_indent(block, 1))
    if "footer_note" in qsg:
        lines.extend(_emit_kv("footer_note", qsg["footer_note"]))
    return lines


# ---------------------------------------------------------------------------
# Reverse: load an existing customer YAML back into a form payload.
# ---------------------------------------------------------------------------


def yaml_to_form(text: str) -> dict[str, Any]:
    """Parse a customer YAML file into the form payload shape."""
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError("YAML must be a mapping at the top level")

    customer = data.get("customer") or {}
    verdict = data.get("verdict") or {}
    findings = data.get("findings") or []
    qsg = data.get("quick_start_guide") or {}

    payload = {
        "customer": {
            "first_name": customer.get("first_name", "") or "",
            "last_name": customer.get("last_name", "") or "",
            "email": customer.get("email", "") or "",
            "app_name": customer.get("app_name", "") or "",
            "app_url": customer.get("app_url", "") or "",
            "url_redacted": bool(customer.get("url_redacted", False)),
            "tier": customer.get("tier", "") or "",
            "builder": customer.get("builder", "") or "",
        },
        "verdict": {
            "emoji": verdict.get("emoji", "") or "",
            "summary": verdict.get("summary", "") or "",
            "narrative": verdict.get("narrative", "") or "",
        },
        "findings": [
            {
                "severity": f.get("severity", "") or "",
                "title": f.get("title", "") or "",
                "what_we_saw": f.get("what_we_saw", "") or "",
                "why_it_matters": f.get("why_it_matters", "") or "",
                "screenshot_path": f.get("screenshot_path", "") or "",
                "screenshot_caption": f.get("screenshot_caption", "") or "",
                "fix_prompt": f.get("fix_prompt", "") or "",
            }
            for f in findings
            if isinstance(f, dict)
        ],
        "quick_start_guide": {
            "title": qsg.get("title", "") or "",
            "intro": qsg.get("intro", "") or "",
            "steps": [
                {
                    "title": s.get("title", "") or "",
                    "body": s.get("body", "") or "",
                }
                for s in (qsg.get("steps") or [])
                if isinstance(s, dict)
            ],
            "footer_note": qsg.get("footer_note", "") or "",
        },
    }
    return payload
