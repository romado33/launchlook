"""
qsg_generate.py — BL-09 (API-automated workflow, future)

Generates a Quick Start Guide Markdown file by calling an LLM API directly.
Currently a thin wrapper that supports either OpenAI or Anthropic depending
on which API key is set in .env.

Default workflow at MVP is MANUAL — use scripts/qsg_compose_prompt.py instead
and paste into chatgpt.com. This script exists so the switch to automation
is a one-line config change later.

Usage:
    python scripts/qsg_generate.py --input intake.json --output quickstart.md

Where intake.json is:
    {
      "app_name": "TaskRoom",
      "description": "A simple shared to-do list for small teams.",
      "target_user": "Small business owners and team leads",
      "workflow": "Create a task, assign it, mark it done",
      "platform": "Lovable",
      "homepage_text": "...",
      "post_signup_text": "...",
      "nav_labels": "Tasks, Team, Settings, Help",
      "cta_labels": "Add Task, Assign, Mark Done",
      "support_contact": "hello@taskroom.app",
      "founder_notes": ""
    }
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # .env optional

REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEM_PROMPT_PATH = REPO_ROOT / "prompts" / "quickstart_system.txt"
USER_TEMPLATE_PATH = REPO_ROOT / "prompts" / "quickstart_user.txt"

FORBIDDEN_WORDS = [
    "leverage", "seamless", "robust", "cutting-edge", "innovative",
    "streamline", "powerful", "elevate", "empower", "unlock",
    "supercharge", "revolutionize", "best-in-class", "world-class",
]


def build_messages(intake: dict) -> tuple[str, str]:
    """Return (system_prompt, user_message) ready for an LLM call."""
    system = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    template = USER_TEMPLATE_PATH.read_text(encoding="utf-8")

    user = template
    for key, val in intake.items():
        user = user.replace("{" + key + "}", str(val))

    return system, user


def call_openai(system: str, user: str, model: str = "gpt-5-medium") -> str:
    """Call OpenAI. Requires OPENAI_API_KEY in env and `openai` package installed."""
    try:
        from openai import OpenAI  # noqa: F401
    except ImportError:
        sys.exit("ERROR: openai package not installed. Run: pip install -e \".[ai]\"")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("ERROR: OPENAI_API_KEY not set in environment or .env")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.5,
        max_tokens=2000,
    )
    return response.choices[0].message.content or ""


def call_anthropic(system: str, user: str, model: str = "claude-sonnet-4-5") -> str:
    """Call Anthropic. Requires ANTHROPIC_API_KEY in env and `anthropic` package installed."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        sys.exit("ERROR: anthropic package not installed. Run: pip install -e \".[ai]\"")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set in environment or .env")

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=2000,
        temperature=0.5,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def check_forbidden(text: str) -> list[str]:
    lower = text.lower()
    return sorted({w for w in FORBIDDEN_WORDS if w in lower})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to intake JSON file")
    parser.add_argument("--output", required=True, help="Path to write the Markdown QSG")
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "auto"],
        default="auto",
        help="Which LLM provider to use. 'auto' picks based on which API key is set.",
    )
    parser.add_argument("--model", default=None, help="Override the default model name")
    args = parser.parse_args()

    intake_path = Path(args.input)
    if not intake_path.exists():
        sys.exit(f"ERROR: --input file not found: {args.input}")

    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    system, user = build_messages(intake)

    provider = args.provider
    if provider == "auto":
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        else:
            sys.exit(
                "ERROR: no API key set. Either:\n"
                "  - Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env, or\n"
                "  - Use the manual workflow: python scripts/qsg_compose_prompt.py ..."
            )

    print(f"Generating Quick Start Guide via {provider}...", file=sys.stderr)

    if provider == "openai":
        markdown = call_openai(system, user, model=args.model or "gpt-5-medium")
    else:
        markdown = call_anthropic(system, user, model=args.model or "claude-sonnet-4-5")

    flagged = check_forbidden(markdown)
    if flagged:
        print(f"WARN: forbidden marketing words detected in output: {flagged}", file=sys.stderr)
        print("WARN: edit before sending to customer.", file=sys.stderr)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote {output_path} ({len(markdown.split())} words)", file=sys.stderr)
    print("Next: open in editor, spot-edit, paste into customer's Notion Launch Pack report.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
