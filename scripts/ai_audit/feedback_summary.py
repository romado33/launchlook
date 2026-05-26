"""Print AI-quality summary stats across all customers reviewed so far.

Usage::

    python -m scripts.ai_audit.feedback_summary
    python scripts/ai_audit/feedback_summary.py --since 2026-05-01

Reads ``data/ai_feedback/*.json`` and prints:

* total drafts reviewed
* % approved without edits
* % edited (with severity drift breakdown)
* % rejected
* avg regenerations per draft
* most-rejected finding titles (top 10)
* most-edited title pairs (AI title → Rob's final title)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FEEDBACK_DIR = REPO_ROOT / "data" / "ai_feedback"


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{100 * part / total:.1f}%"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--since", help="Only count drafts reviewed on/after this ISO date (e.g. 2026-05-01)")
    args = parser.parse_args(argv)

    if not FEEDBACK_DIR.exists():
        print(f"No feedback yet — {FEEDBACK_DIR.relative_to(REPO_ROOT)} is empty.")
        return 0

    cutoff = _parse_iso(args.since) if args.since else None
    if args.since and not cutoff:
        print(f"WARN: could not parse --since {args.since!r}, ignoring", file=sys.stderr)

    actions_total = Counter()
    severity_drift = Counter()           # ai_sev -> final_sev
    rejected_titles = Counter()
    edited_pairs: list[tuple[str, str]] = []
    regenerations: list[int] = []
    drafts_count = 0
    drafts_by_provider: Counter = Counter()
    drafts_by_tier: Counter = Counter()

    for path in sorted(FEEDBACK_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue

        reviewed_at = _parse_iso(data.get("reviewed_at") or data.get("ai_generated_at") or "")
        if cutoff and reviewed_at and reviewed_at < cutoff.replace(tzinfo=cutoff.tzinfo or timezone.utc):
            continue

        drafts_count += 1
        drafts_by_provider[data.get("provider", "?")] += 1
        drafts_by_tier[data.get("tier", "?")] += 1

        for entry in data.get("actions", []):
            action = entry.get("action") or "draft"
            actions_total[action] += 1

            if action == "rejected":
                title = entry.get("ai_title") or "(unknown)"
                rejected_titles[title] += 1
            elif action == "edited":
                ai_t = entry.get("ai_title") or "(unknown)"
                final_t = entry.get("final_title") or ai_t
                edited_pairs.append((ai_t, final_t))
                ai_sev = entry.get("ai_severity") or "?"
                final_sev = entry.get("final_severity") or ai_sev
                if ai_sev != final_sev:
                    severity_drift[f"{ai_sev}→{final_sev}"] += 1
            regenerations.append(int(entry.get("regen_count", 0)))

    if drafts_count == 0:
        print("No drafts matched the filter.")
        return 0

    total_actions = sum(actions_total.values()) or 1
    approved = actions_total.get("approved", 0)
    edited = actions_total.get("edited", 0)
    rejected = actions_total.get("rejected", 0)
    regenerated = actions_total.get("regenerated", 0)
    drafts = actions_total.get("draft", 0)

    avg_regens = sum(regenerations) / len(regenerations) if regenerations else 0.0
    approved_or_draft = approved + drafts   # silent approves count as approvals

    print()
    print("LaunchLook AI quality summary")
    print("=" * 56)
    print(f"  Drafts reviewed:  {drafts_count}")
    print(f"  Total findings:   {total_actions}")
    print()
    print("  Provider mix:")
    for provider, count in drafts_by_provider.most_common():
        print(f"    - {provider:<12} {count}")
    print("  Tier mix:")
    for tier, count in drafts_by_tier.most_common():
        print(f"    - {tier:<16} {count}")

    print()
    print("Per-finding outcomes")
    print("-" * 56)
    print(f"  Approved (no edits):      {approved_or_draft:>4}  {_pct(approved_or_draft, total_actions)}")
    print(f"  Edited before ship:       {edited:>4}  {_pct(edited, total_actions)}")
    print(f"  Rejected (deleted):       {rejected:>4}  {_pct(rejected, total_actions)}")
    print(f"  Regeneration requests:    {regenerated:>4}  (cumulative, separate from above)")
    print(f"  Avg regens per finding:   {avg_regens:.2f}")

    if severity_drift:
        print()
        print("Severity edits (AI → final)")
        print("-" * 56)
        for drift, count in severity_drift.most_common(10):
            print(f"  {drift:<16} {count}")

    if rejected_titles:
        print()
        print("Most-rejected AI titles (top 10)")
        print("-" * 56)
        for title, count in rejected_titles.most_common(10):
            print(f"  [{count}]  {title}")

    if edited_pairs:
        print()
        print("Edited titles (AI → final, first 10)")
        print("-" * 56)
        for ai_t, final_t in edited_pairs[:10]:
            if ai_t != final_t:
                print(f"  AI:    {ai_t}")
                print(f"  Final: {final_t}")
                print()

    print()
    print(f"Feedback files: {FEEDBACK_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
