"""
qsg_compose_prompt.py — BL-09 (manual workflow)

Composes a ready-to-paste Quick Start Guide prompt for the customer.
You then paste the system prompt + this composed user message into chatgpt.com
(or the Anthropic Workbench), edit the output, and drop it into the customer's
Notion Launch Pack report.

Usage:
    python scripts/qsg_compose_prompt.py \\
        --app-name "TaskRoom" \\
        --description "A simple shared to-do list for small teams." \\
        --target-user "Small business owners and team leads" \\
        --workflow "Create a task, assign it, mark it done" \\
        --platform Lovable \\
        --homepage "TaskRoom — shared tasks for small teams..." \\
        --postsignup "Welcome to TaskRoom. Create your first task..." \\
        --nav "Tasks, Team, Settings, Help" \\
        --ctas "Add Task, Assign, Mark Done, Invite Teammate, Sign Out" \\
        --support hello@taskroom.app \\
        --notes "Most users invite 2-5 teammates. No Slack integration yet."

Pipe to a file:
    python scripts/qsg_compose_prompt.py ... > output/scans/customer/qsg_prompt.txt

Then in ChatGPT, paste:
    1. The contents of prompts/quickstart_system.txt as your opening message
    2. The composed prompt from this script
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
USER_TEMPLATE_PATH = REPO_ROOT / "prompts" / "quickstart_user.txt"
SYSTEM_PROMPT_PATH = REPO_ROOT / "prompts" / "quickstart_system.txt"

FORBIDDEN_WORDS = [
    "leverage",
    "seamless",
    "robust",
    "cutting-edge",
    "innovative",
    "streamline",
    "powerful",
    "elevate",
    "empower",
    "unlock",
    "supercharge",
    "revolutionize",
    "best-in-class",
    "world-class",
]


def read_or_inline(value: str | None, file_arg: str | None, field_name: str) -> str:
    """Resolve --field VALUE or --field-file PATH into a string."""
    if file_arg:
        path = Path(file_arg)
        if not path.exists():
            sys.exit(f"ERROR: --{field_name}-file path not found: {file_arg}")
        return path.read_text(encoding="utf-8").strip()
    return (value or "").strip()


def check_forbidden(text: str) -> list[str]:
    """Return list of forbidden words found in text (case-insensitive)."""
    lower = text.lower()
    return sorted({w for w in FORBIDDEN_WORDS if w in lower})


def compose(args: argparse.Namespace) -> str:
    template = USER_TEMPLATE_PATH.read_text(encoding="utf-8")

    homepage_text = read_or_inline(args.homepage, args.homepage_file, "homepage")
    postsignup_text = read_or_inline(args.postsignup, args.postsignup_file, "postsignup")

    substitutions = {
        "app_name": args.app_name,
        "one_line_description": args.description,
        "target_user_description": args.target_user,
        "main_workflow_description": args.workflow,
        "platform": args.platform,
        "homepage_text": homepage_text or "(no homepage copy captured — REVIEWER must fill)",
        "post_signup_text": postsignup_text
        or "(no post-signup copy captured — REVIEWER must fill)",
        "nav_labels": args.nav or "(none captured)",
        "cta_labels": args.ctas or "(none captured)",
        "support_contact": args.support or "(none provided — REVIEWER must add)",
        "founder_notes": args.notes or "(none)",
    }

    # Sanity check: any forbidden words in the input that will poison the prompt?
    combined_input = "\n".join(str(v) for v in substitutions.values())
    flagged = check_forbidden(combined_input)
    if flagged:
        print(
            "WARN: forbidden marketing words present in input — will likely propagate "
            f"into the QSG. Consider rephrasing intake: {flagged}",
            file=sys.stderr,
        )

    # Simple {key} substitution (Python str.format() is too brittle with the prompt's curly-braced examples)
    composed = template
    for key, val in substitutions.items():
        composed = composed.replace("{" + key + "}", str(val))

    # Catch any unfilled placeholders
    unfilled = re.findall(r"\{([a-z_]+)\}", composed)
    if unfilled:
        print(f"WARN: unfilled placeholders in output: {sorted(set(unfilled))}", file=sys.stderr)

    return composed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--app-name", required=True, help="App name (e.g. 'TaskRoom')")
    parser.add_argument("--description", required=True, help="One-line description")
    parser.add_argument("--target-user", required=True, help="Who the target user is")
    parser.add_argument("--workflow", required=True, help="Main workflow users do")
    parser.add_argument(
        "--platform", required=True, help="Lovable / Bolt / Base44 / Replit / v0 / Other"
    )

    parser.add_argument("--homepage", help="Crawled homepage copy (inline)")
    parser.add_argument("--homepage-file", help="Path to file with crawled homepage copy")
    parser.add_argument("--postsignup", help="Crawled post-signup copy (inline)")
    parser.add_argument("--postsignup-file", help="Path to file with crawled post-signup copy")

    parser.add_argument("--nav", help="Visible nav labels, comma-separated")
    parser.add_argument("--ctas", help="Visible CTA / button labels, comma-separated")
    parser.add_argument("--support", help="Support email or contact info")
    parser.add_argument("--notes", help="Founder notes from intake form")

    parser.add_argument(
        "--with-system-prompt",
        action="store_true",
        help="Prepend the system prompt at the top of stdout (useful for one-shot paste)",
    )

    args = parser.parse_args()

    composed_user = compose(args)

    if args.with_system_prompt:
        system = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
        print(
            "=== SYSTEM PROMPT (paste this first in ChatGPT, then send the USER MESSAGE below) ===\n"
        )
        print(system)
        print("\n=== USER MESSAGE ===\n")

    print(composed_user)

    print("\n# --- DONE. Steps from here: ---", file=sys.stderr)
    print("# 1. Open chatgpt.com (or claude.ai), start a new chat.", file=sys.stderr)
    print(
        "# 2. Paste the contents of prompts/quickstart_system.txt as the first message.",
        file=sys.stderr,
    )
    print("# 3. Paste the composed user message above as the second message.", file=sys.stderr)
    print("# 4. Edit the returned Markdown. Verify no forbidden words remain.", file=sys.stderr)
    print(
        "# 5. Paste edited Markdown into the customer's Notion Launch Pack report (Part 2).",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
