"""
email_render.py — render email templates with variables for manual send.

Usage:
    python scripts/email_render.py welcome --name Rob --app-name LiLo --turnaround "24 hours" --intake-link https://tally.so/r/xxx
    python scripts/email_render.py delivery --name Rob --app-name LiLo --report-link https://notion.so/... --platform Lovable

Note (May 2026): the followup-d3 / followup-d7 templates and their cron
runner were removed. The post-delivery email now carries the Fix Check
offer; a separate cadence wasn't earning its keep.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EMAIL_DIR = REPO_ROOT / "templates" / "email"

TEMPLATE_VARS: dict[str, list[str]] = {
    "welcome": ["NAME", "APP_NAME", "TURNAROUND", "INTAKE_FORM_LINK"],
    "delivery": ["NAME", "APP_NAME", "NOTION_REPORT_LINK", "PLATFORM"],
    "free-sample-outreach": ["NAME", "APP_NAME", "PLATFORM", "NOTION_REPORT_LINK"],
}


def load_template(name: str) -> tuple[str, str]:
    path = EMAIL_DIR / f"{name}.txt"
    if not path.exists():
        sys.exit(f"ERROR: template not found: {path}")
    text = path.read_text(encoding="utf-8")
    if "\n---\n" in text:
        text = text.split("\n---\n")[0]
    lines = text.splitlines()
    subject = lines[0].removeprefix("Subject:").strip()
    body = "\n".join(lines[1:]).strip()
    return subject, body


def render(text: str, variables: dict[str, str]) -> str:
    out = text
    for key, val in variables.items():
        out = out.replace("{" + key + "}", val)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", choices=list(TEMPLATE_VARS.keys()))
    parser.add_argument("--name", default="")
    parser.add_argument("--app-name", default="")
    parser.add_argument("--turnaround", default="")
    parser.add_argument("--intake-link", default="")
    parser.add_argument("--report-link", default="")
    parser.add_argument("--platform", default="Lovable")
    parser.add_argument("--referral-code", default="")
    args = parser.parse_args()

    variables = {
        "NAME": args.name,
        "APP_NAME": args.app_name,
        "TURNAROUND": args.turnaround,
        "INTAKE_FORM_LINK": args.intake_link,
        "NOTION_REPORT_LINK": args.report_link,
        "PLATFORM": args.platform,
        "REFERRAL_CODE": args.referral_code,
    }

    subject, body = load_template(args.template)
    rendered_subject = render(subject, variables)
    rendered_body = render(body, variables)

    print(f"Subject: {rendered_subject}\n")
    print(rendered_body)

    needed = TEMPLATE_VARS[args.template]
    missing = [v for v in needed if not variables.get(v)]
    if missing:
        print(f"\nWARN: empty variables: {missing}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
