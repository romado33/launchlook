"""Tests for scripts/fix_pack.py — Fix Pack Markdown + paste-first wrappers."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.fix_pack import (  # noqa: E402
    enrich_findings_for_templates,
    paste_first_line,
    render_builder_memory,
    render_fix_pack_markdown,
    wrap_fix_prompt,
)


def _sample_data(tier: str = "Starter Package") -> dict:
    return {
        "customer": {
            "first_name": "Jane",
            "app_name": "Sparkle",
            "builder": "Lovable",
            "tier": tier,
            "app_url": "https://sparkle.lovable.app",
        },
        "verdict": {"summary": "Needs fixes before launch"},
        "findings": [
            {
                "severity": "high",
                "title": "Broken footer link",
                "what_we_saw": "Privacy 404.",
                "why_it_matters": "Trust gap.",
                "fix_prompt": "Add /privacy route.",
            },
            {
                "severity": "critical",
                "title": "Dev bypass live",
                "fix_prompt": "Remove dev bypass.",
            },
        ],
    }


def test_paste_first_line_lovable() -> None:
    line = paste_first_line({"builder": "Lovable"})
    assert "Paste this first" in line
    assert "Lovable" in line


def test_paste_first_line_webflow() -> None:
    line = paste_first_line({"builder": "Webflow", "platform": "webflow"})
    assert "Webflow Designer" in line
    assert "Publish" in line


def test_wrap_fix_prompt_prepends_instruction() -> None:
    wrapped = wrap_fix_prompt({"builder": "Bolt"}, "Fix the footer.")
    assert wrapped.startswith("Paste this first:")
    assert "Fix the footer." in wrapped


def test_render_fix_pack_markdown_sorted_and_includes_findings() -> None:
    md = render_fix_pack_markdown(_sample_data(), "2026-05-28")
    assert "# Fix Pack — Sparkle" in md
    assert "Dev bypass live" in md
    # critical before high in output
    assert md.index("Dev bypass live") < md.index("Broken footer link")
    assert "```" in md
    assert "Add /privacy route." in md


def test_enrich_findings_adds_display_field() -> None:
    customer = {"builder": "Lovable"}
    out = enrich_findings_for_templates(_sample_data()["findings"], customer)
    assert out[0]["fix_prompt_display"].startswith("Paste this first:")


def test_builder_memory_explicit_yaml() -> None:
    text = render_builder_memory(
        {"tier": "Starter Package"},
        explicit="Custom memory for the builder.",
    )
    assert text == "Custom memory for the builder."


def test_builder_memory_pro_auto_template() -> None:
    text = render_builder_memory(
        {
            "tier": "Pro Package",
            "app_name": "Sparkle",
            "builder": "Lovable",
            "app_url": "https://sparkle.lovable.app",
        }
    )
    assert text is not None
    assert "Sparkle" in text
    assert "Fix Pack" in text


def test_builder_memory_starter_returns_none_without_explicit() -> None:
    assert render_builder_memory({"tier": "Starter Package"}) is None
