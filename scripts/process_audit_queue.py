#!/usr/bin/env python3
"""Process pending audit jobs from Notion (run locally or on a schedule).

Vercel webhooks only write Notion rows; this script runs the heavy AI pipeline,
form smoke tests, and optional email round-trips. It never calls deliver_report --send.

Usage:
    python scripts/process_audit_queue.py              # one job (oldest first)
    python scripts/process_audit_queue.py --limit 3
    python scripts/process_audit_queue.py --slug acme-example-com
    python scripts/process_audit_queue.py --list
    python scripts/process_audit_queue.py --dry-run --slug test

Requires .env: NOTION_TOKEN, NOTION_*_DB_ID, ANTHROPIC_API_KEY or OPENAI_API_KEY,
RESEND_API_KEY, ADMIN_EMAIL, Playwright for capture/form smoke.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from scripts.audit_automation.discover import discover_all  # noqa: E402
from scripts.audit_automation.worker import process_job  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process LaunchLook audit automation queue")
    parser.add_argument("--limit", type=int, default=1, help="Max jobs to run (default 1)")
    parser.add_argument("--slug", help="Process only this customer slug")
    parser.add_argument("--list", action="store_true", help="List pending jobs and exit")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run pipeline without Notion/email side effects"
    )
    parser.add_argument("--provider", default="auto", choices=["auto", "claude", "gpt", "stub"])
    args = parser.parse_args(argv)

    jobs = discover_all()
    if args.slug:
        jobs = [j for j in jobs if j.slug == args.slug]
    if args.list:
        if not jobs:
            print("No pending jobs.")
            return 0
        for j in jobs:
            print(f"  {j.kind.value:4}  {j.slug:40}  {j.tier:18}  {j.url}")
        return 0

    if not jobs:
        print("Queue empty (free: Status=queued; paid: Intake Received + intake checkbox).")
        return 0

    ok = 0
    for job in jobs[: max(1, args.limit)]:
        if process_job(job, provider=args.provider, dry_run=args.dry_run):
            ok += 1
    print(f"Finished {ok}/{min(len(jobs), args.limit)} job(s).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
