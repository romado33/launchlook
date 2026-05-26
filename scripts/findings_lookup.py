"""
findings_lookup.py — search the findings library from the CLI.

Usage:
    python scripts/findings_lookup.py placeholder
    python scripts/findings_lookup.py --id FL-036
    python scripts/findings_lookup.py --severity Critical
    python scripts/findings_lookup.py --category "Broken functionality"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_PATH = REPO_ROOT / "findings_library" / "findings.json"


def load_library() -> dict:
    return json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))


def print_finding(f: dict) -> None:
    print(f"\n{f['id']} — {f['name']} [{f['severity']}]")
    print(f"  Category: {f['category']}")
    print(f"  {f['explanation']}")
    prompts = f.get("fix_prompts") or {}
    for platform, prompt in prompts.items():
        if prompt:
            preview = prompt[:120] + ("..." if len(prompt) > 120 else "")
            print(f"  Fix ({platform}): {preview}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="Search name, explanation, or notes")
    parser.add_argument("--id", help="Exact finding ID (e.g. FL-011)")
    parser.add_argument("--severity", choices=["Critical", "High", "Medium", "Low"])
    parser.add_argument("--category", help="Exact category name")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    data = load_library()
    findings = data["findings"]

    if args.id:
        matches = [f for f in findings if f["id"] == args.id]
    else:
        matches = findings
        if args.severity:
            matches = [f for f in matches if f["severity"] == args.severity]
        if args.category:
            matches = [f for f in matches if f["category"] == args.category]
        if args.query:
            q = args.query.lower()
            matches = [
                f
                for f in matches
                if q in f["name"].lower()
                or q in f["explanation"].lower()
                or q in (f.get("notes") or "").lower()
                or q in f["category"].lower()
            ]

    if args.json:
        print(json.dumps(matches, indent=2))
        return 0

    if not matches:
        print("No findings matched.", file=sys.stderr)
        return 1

    print(
        f"Found {len(matches)} finding(s) (library v{data.get('version', '?')}, {len(findings)} total)"
    )
    for f in matches:
        print_finding(f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
