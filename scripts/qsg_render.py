"""
qsg_render.py — BL-10

Renders an edited Quick Start Guide Markdown file to a self-contained HTML page
customers can host, embed, or link from their Notion report.

Usage:
    python scripts/qsg_render.py \\
        --input output/scans/taskroom/quickstart.md \\
        --output output/scans/taskroom/quickstart.html \\
        --app-name TaskRoom \\
        --color "#0d9488"

Requires: pip install -e .  (markdown + jinja2 in core deps)
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown import markdown

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "templates" / "qsg"

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


def extract_title(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def highlight_reviewer_markers(html: str) -> str:
    """Wrap [REVIEWER: ...] markers in a visible callout."""
    return re.sub(
        r"\[REVIEWER:[^\]]+\]",
        r'<p class="reviewer">\g<0></p>',
        html,
        flags=re.IGNORECASE,
    )


def check_forbidden(text: str) -> list[str]:
    lower = text.lower()
    return sorted({w for w in FORBIDDEN_WORDS if w in lower})


def render(
    md_path: Path,
    output_path: Path,
    app_name: str,
    primary_color: str | None,
) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    title = extract_title(md_text, app_name)

    body_html = markdown(
        md_text,
        extensions=["extra", "smarty", "sane_lists"],
        output_format="html5",
    )
    body_html = highlight_reviewer_markers(body_html)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("qsg.html.j2")
    html = template.render(
        title=title,
        body_html=body_html,
        primary_color=primary_color or "#B45309",
        generated_date=date.today().isoformat(),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    size_kb = len(html.encode("utf-8")) / 1024
    print(f"Wrote {output_path} ({size_kb:.1f} KB)", file=sys.stderr)
    if size_kb > 50:
        print(
            "WARN: HTML exceeds 50KB target — consider trimming the QSG.",
            file=sys.stderr,
        )

    flagged = check_forbidden(md_text)
    if flagged:
        print(f"WARN: forbidden words in source Markdown: {flagged}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--input", required=True, help="Path to edited quickstart.md")
    parser.add_argument("--output", required=True, help="Path to write quickstart.html")
    parser.add_argument(
        "--app-name", default="App", help="Fallback title if Markdown has no # heading"
    )
    parser.add_argument("--color", help="Primary accent color hex (e.g. #0d9488)")
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        sys.exit(f"ERROR: input not found: {args.input}")

    render(md_path, Path(args.output), args.app_name, args.color)
    return 0


if __name__ == "__main__":
    sys.exit(main())
