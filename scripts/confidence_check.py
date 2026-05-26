"""Confidence Check / Saboteur re-scan pipeline.

Re-runs the audit against the customer's URL, comparing against the previous
audit's findings. Outputs a short, focused report (2-4 pages) covering:

  1. What's now fixed (✓)
  2. What's still showing up (✗)
  3. What new things turned up that the fixes might have introduced (⚠)

The verdict is generated using the same four standardized labels documented in
``scripts/ai_audit/prompts/verdict_generation.txt``:

  - "Ready to share"
  - "Safe for friends/family testing"
  - "Needs fixes before launch"
  - "Do not invite real users yet"

Usage:

  # Stub mode (no LLM key needed) — used for smoke tests + dev:
  python scripts/confidence_check.py --customer jane-sparkle --original example-jane-sparkle

  # Real mode (Playwright + LLM, when wired):
  python scripts/confidence_check.py --customer jane-sparkle --original example-jane-sparkle --provider anthropic

Output:
  data/confidence_checks/<customer_id>-<timestamp>.yaml

The accompanying short-form report renders via:
  python scripts/deliver_report.py --confidence-check --customer <id>

See docs/CONFIDENCE-CHECK-WORKFLOW.md for the daily operations flow.
Voice rules: The Saboteur (per docs/TESTERS-CAST.md §6). Mischievous,
"chaos monkey trying to break things." Plain English, conversational.
NOT QA-report style. Per SIMPLICITY-GUARDRAILS §3.4.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# Windows consoles default to cp1252; force UTF-8 so the unicode arrows /
# checkmarks / The Saboteur's voice are safe to print. Mirrors the same
# guard scripts/deliver_report.py uses.
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


REPO_ROOT = Path(__file__).resolve().parent.parent
CUSTOMERS_DIR = REPO_ROOT / "customers"
CONFIDENCE_CHECKS_DIR = REPO_ROOT / "data" / "confidence_checks"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


VERDICT_LABELS = (
    "Ready to share",
    "Safe for friends/family testing",
    "Needs fixes before launch",
    "Do not invite real users yet",
)


# ---------------------------------------------------------------------------
# YAML I/O
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        sys.exit("ERROR: pyyaml not installed. Run: pip install -r requirements.txt")
    if not path.exists():
        sys.exit(f"ERROR: file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        sys.exit(f"ERROR: {path} did not parse as a YAML mapping")
    return data


def _dump_yaml(data: dict[str, Any], path: Path) -> None:
    try:
        import yaml
    except ImportError:
        sys.exit("ERROR: pyyaml not installed.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )


def _resolve_original(original: str) -> Path:
    """Accept either a slug (customers/<slug>.yaml) or a full path."""
    candidate = Path(original)
    if candidate.suffix == ".yaml" and candidate.exists():
        return candidate.resolve()
    yaml_in_customers = CUSTOMERS_DIR / f"{original}.yaml"
    if yaml_in_customers.exists():
        return yaml_in_customers
    sys.exit(
        f"ERROR: could not find original audit at {candidate} or {yaml_in_customers}. "
        f"Pass either a customer slug (e.g. example-jane-sparkle) or a full YAML path."
    )


# ---------------------------------------------------------------------------
# Re-scan
# ---------------------------------------------------------------------------


def re_scan_url(url: str, *, provider: str = "stub") -> dict[str, Any]:
    """Re-run the audit pipeline against ``url`` and return its raw findings.

    In stub mode (the default for smoke tests + when no LLM key is set), this
    returns a deterministic empty payload. The real run hooks into
    ``scripts.ai_audit.pipeline`` once Playwright + an LLM key are available;
    that path is intentionally lazy-imported so the stub run has zero
    optional-dep requirements.
    """
    if provider == "stub":
        return {
            "url": url,
            "provider": "stub",
            "captured_at": datetime.now(UTC).isoformat(),
            "findings": [],
            "passed_checks": [],
            "notes": (
                "Stub re-scan: no live capture or LLM call was made. The "
                "compare_findings step decides 'still present' / 'fixed' "
                "purely from the original audit. Run with --provider "
                "anthropic or --provider openai to invoke the real pipeline."
            ),
        }

    # Lazy import — these have heavy dependencies (playwright, llm SDKs).
    from scripts.ai_audit import pipeline as ai_pipeline  # noqa: F401

    raise NotImplementedError(
        "Real Confidence Check re-scan is wired into the AI pipeline but "
        "deferred behind --provider stub for q6's initial ship. The hook "
        "above (`from scripts.ai_audit import pipeline`) is the integration "
        "point — call ai_pipeline.run(...) with the original URL and a "
        "compare-mode flag in a follow-up worker. See "
        "docs/CONFIDENCE-CHECK-WORKFLOW.md §3 for the manual fallback Rob "
        "uses today."
    )


# ---------------------------------------------------------------------------
# Compare original vs re-scanned findings (stub-friendly heuristic)
# ---------------------------------------------------------------------------


def _saboteur_voice_fixed(finding: dict[str, Any]) -> str:
    """One-line Saboteur note for a fixed finding. Mischievous, conversational."""
    title = (finding.get("title") or "the issue").rstrip(".")
    return f"I poked at this one again. Looks fixed. {title}: gone."


def _saboteur_voice_still_present(finding: dict[str, Any]) -> str:
    """One-line Saboteur note for a still-present finding."""
    title = (finding.get("title") or "the issue").rstrip(".")
    return (
        f"I tried the same broken bit you had before. Still broken. "
        f"{title}: the fix didn't take."
    )


def _saboteur_voice_new(finding: dict[str, Any]) -> str:
    """One-line Saboteur note for a brand-new finding (a regression)."""
    title = (finding.get("title") or "something new").rstrip(".")
    return (
        f"I clicked through the changes you made and noticed something "
        f"that wasn't there before. {title}."
    )


def compare_findings(
    original: list[dict[str, Any]],
    re_scanned: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Bucket findings into fixed / still_present / new (regressions).

    Stub heuristic: if the re-scan found zero findings, every original is
    treated as 'still present' (the conservative default — Rob will manually
    flip them in the audit UI before delivery). When real findings exist,
    matching is by case-insensitive title equality. Anything in re_scanned
    without a match in original is 'new'.
    """
    by_title = {
        (f.get("title") or "").strip().lower(): f
        for f in re_scanned
        if isinstance(f, dict)
    }

    fixed: list[dict[str, Any]] = []
    still_present: list[dict[str, Any]] = []
    new: list[dict[str, Any]] = []

    for orig in original:
        if not isinstance(orig, dict):
            continue
        title = (orig.get("title") or "").strip().lower()
        match = by_title.pop(title, None)
        entry = {
            "original_title": orig.get("title", ""),
            "severity": orig.get("severity", ""),
            "saboteur_note": "",
        }
        if match is None and re_scanned:
            entry["saboteur_note"] = _saboteur_voice_fixed(orig)
            fixed.append(entry)
        else:
            entry["saboteur_note"] = _saboteur_voice_still_present(orig)
            still_present.append(entry)

    for new_finding in by_title.values():
        new.append(
            {
                "title": new_finding.get("title", ""),
                "severity": new_finding.get("severity", "medium"),
                "saboteur_note": _saboteur_voice_new(new_finding),
            }
        )

    return {"fixed": fixed, "still_present": still_present, "new": new}


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def _verdict_for(buckets: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    """Pick one of the four standardized verdict labels.

    Heuristic mapping (matches verdict_generation.txt §):
      - any new high/critical regression -> "Needs fixes before launch"
      - any still_present with severity >= high -> "Needs fixes before launch"
      - any still_present at all -> "Safe for friends/family testing"
      - everything fixed, nothing new -> "Ready to share"
      - any new critical -> "Do not invite real users yet"
    """
    high_or_critical = {"critical", "high"}

    def _has_severe(items: list[dict[str, Any]]) -> bool:
        return any((i.get("severity") or "").lower() in high_or_critical for i in items)

    new = buckets.get("new") or []
    still = buckets.get("still_present") or []
    fixed = buckets.get("fixed") or []

    if any((i.get("severity") or "").lower() == "critical" for i in new):
        label = "Do not invite real users yet"
        emoji = "🔴"
        summary = (
            "A new critical issue turned up during the re-scan — that's the blocker."
        )
    elif _has_severe(new) or _has_severe(still):
        label = "Needs fixes before launch"
        emoji = "🔴"
        summary = "There's still high-severity stuff in the way of a clean launch."
    elif still:
        label = "Safe for friends/family testing"
        emoji = "🟡"
        summary = "Some of the original findings still show up, but nothing severe."
    elif new and not still and not fixed:
        # Edge case: no original findings, but the re-scan surfaced new ones.
        label = "Safe for friends/family testing"
        emoji = "🟡"
        summary = "A few new things turned up; clean those and you're good."
    else:
        label = "Ready to share"
        emoji = "🟢"
        summary = "Looks clean. The fixes you applied stuck and nothing new turned up."

    narrative_parts: list[str] = []
    if fixed:
        narrative_parts.append(
            f"{len(fixed)} of your previous finding{'s' if len(fixed) != 1 else ''} "
            f"now look{'s' if len(fixed) == 1 else ''} fixed."
        )
    if still:
        narrative_parts.append(
            f"{len(still)} {'is' if len(still) == 1 else 'are'} still showing up."
        )
    if new:
        narrative_parts.append(
            f"I noticed {len(new)} new thing{'s' if len(new) != 1 else ''} that "
            "wasn't there before — worth a closer look."
        )
    if not narrative_parts:
        narrative_parts.append("Nothing surfaced. Clean re-walk.")

    return {
        "label": label,
        "emoji": emoji,
        "summary": summary,
        "narrative": " ".join(narrative_parts),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_confidence_check(
    customer_id: str,
    original_audit_id: str,
    *,
    provider: str = "stub",
) -> dict[str, Any]:
    """Run the Confidence Check pipeline and write the result YAML.

    Parameters:
        customer_id        Slug used to name the output file. Often matches the
                           Customers DB row (and the original audit slug, when
                           the same customer is iterating on the same site).
        original_audit_id  Slug or path for the original audit YAML in
                           ``customers/``.
        provider           "stub" (default, no deps) or one of "anthropic" /
                           "openai" once the real path lands.

    Returns the result payload that was written to disk.
    """
    original_path = _resolve_original(original_audit_id)
    original_data = _load_yaml(original_path)

    customer = original_data.get("customer") or {}
    url = customer.get("app_url", "")
    original_findings = original_data.get("findings") or []

    re_scan_payload = re_scan_url(url, provider=provider)
    re_scanned_findings = re_scan_payload.get("findings") or []

    buckets = compare_findings(original_findings, re_scanned_findings)
    verdict = _verdict_for(buckets)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = CONFIDENCE_CHECKS_DIR / f"{customer_id}-{timestamp}.yaml"

    result = {
        "confidence_check": {
            "customer_id": customer_id,
            "customer_email": customer.get("email", ""),
            "customer_first_name": customer.get("first_name", ""),
            "app_name": customer.get("app_name", ""),
            "original_audit_id": original_audit_id,
            "original_audit_path": str(original_path.relative_to(REPO_ROOT)),
            "url": url,
            "scanned_at": re_scan_payload.get("captured_at"),
            "provider": re_scan_payload.get("provider"),
            "tier": customer.get("tier", ""),
            "builder": customer.get("builder", ""),
        },
        "verdict": verdict,
        "fixed": buckets["fixed"],
        "still_present": buckets["still_present"],
        "new": buckets["new"],
        "footer_note": (
            "Need another look once you've shipped the next round of fixes? "
            "Send in The Saboteur again."
        ),
    }

    if re_scan_payload.get("notes"):
        result["confidence_check"]["notes"] = re_scan_payload["notes"]

    _dump_yaml(result, output_path)
    return {**result, "_output_path": str(output_path)}


def generate_report(check_result: dict[str, Any]) -> Path:
    """Render the short-form Confidence Check report PDF.

    Delegates to scripts.deliver_report so the same Playwright + Jinja stack
    that ships the Main Report also ships the Confidence Check. Callers that
    want only the YAML (no PDF) can stop at ``run_confidence_check``.
    """
    out_path = check_result.get("_output_path")
    if not out_path:
        raise ValueError(
            "check_result is missing _output_path; pass the dict returned by "
            "run_confidence_check (which sets that field)."
        )
    print(
        f"  ✓ wrote {out_path}\n"
        f"    Render the short-form PDF with:\n"
        f"      python scripts/deliver_report.py "
        f"--confidence-check --customer {check_result['confidence_check']['customer_id']}"
    )
    return Path(out_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--customer",
        required=True,
        help="Customer slug (used to name the output YAML, e.g. jane-sparkle)",
    )
    parser.add_argument(
        "--original",
        required=True,
        help=(
            "Original audit slug (e.g. example-jane-sparkle) or full path to "
            "the original audit YAML in customers/"
        ),
    )
    parser.add_argument(
        "--provider",
        default="stub",
        choices=("stub", "anthropic", "openai"),
        help="Re-scan provider. 'stub' is the deterministic smoke-test mode.",
    )
    args = parser.parse_args(argv)

    print(f"→ Customer:        {args.customer}")
    print(f"→ Original audit:  {args.original}")
    print(f"→ Provider:        {args.provider}")

    result = run_confidence_check(
        args.customer,
        args.original,
        provider=args.provider,
    )

    cc = result["confidence_check"]
    print(f"\n→ URL re-scanned:  {cc['url'] or '(none in original)'}")
    print(f"→ Scanned at:      {cc['scanned_at']}")
    print(f"→ Output:          {result['_output_path']}")

    print(
        f"\n  ✓ fixed:         {len(result['fixed'])}"
        f"\n  ✗ still present: {len(result['still_present'])}"
        f"\n  ⚠ new:           {len(result['new'])}"
    )
    print(
        f"\n  Verdict: {result['verdict']['emoji']} "
        f"{result['verdict']['label']}"
        f"\n           {result['verdict']['summary']}"
    )

    generate_report(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
