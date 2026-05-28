"""Product constants — canonical value + drift check vs. the API inline copy."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.launchlook_constants import FREE_AUDIT_DELIVER_COUNT

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_free_audit_deliver_count_is_two() -> None:
    assert FREE_AUDIT_DELIVER_COUNT == 2


def test_api_free_audit_inline_constant_matches() -> None:
    """``api/free-audit.py`` inlines ``FREE_AUDIT_DELIVER_COUNT`` to keep the
    Vercel serverless function self-contained. This test ensures the inline
    value never silently drifts from the canonical source.
    """
    src = (REPO_ROOT / "api" / "free-audit.py").read_text(encoding="utf-8")
    match = re.search(r"^FREE_AUDIT_DELIVER_COUNT\s*=\s*(\d+)", src, re.MULTILINE)
    assert match, "FREE_AUDIT_DELIVER_COUNT must be defined at module top in api/free-audit.py"
    assert int(match.group(1)) == FREE_AUDIT_DELIVER_COUNT, (
        f"Drift: api/free-audit.py inlines {match.group(1)} but "
        f"scripts/launchlook_constants.py says {FREE_AUDIT_DELIVER_COUNT}"
    )
