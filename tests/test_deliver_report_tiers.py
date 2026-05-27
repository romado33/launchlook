"""Regression tests for tier validation + alias map in deliver_report.py.

Why this file exists: the prior 126/126 green CI missed a critical bug where
``deliver_report.py`` had drifted out of sync with the canonical tier ladder
defined in ``scripts/ai_audit/pipeline.DEFAULT_TIER_CAPS`` and
``docs/PRODUCT-DECISIONS.md``:

* ``TIER_ALIAS_TO_CANONICAL`` normalised every "Scale Up" alias to
  "Full Package" (wrong direction; the canonical name is "Scale Up Package").
* ``VALID_TIERS`` rejected "Scale Up Package" outright, so every Scale Up
  customer's YAML hit ``sys.exit()`` in ``validate()`` before render.
* The cap dict still used stale 7/25/40 values; canonical is 10/30/40.

No test exercised ``deliver_report.validate()`` with a Scale Up YAML, so the
suite stayed green while the middle tier was silently broken. These tests
lock the three canonical tiers and the legacy alias coverage in place so
that failure mode cannot recur.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.deliver_report import (  # noqa: E402
    TIER_ALIAS_TO_CANONICAL,
    VALID_TIERS,
    validate,
)


def _make_data(tier: str, n_findings: int = 1) -> dict[str, Any]:
    """Build the smallest YAML payload that satisfies ``validate()``."""
    return {
        "customer": {
            "first_name": "Test",
            "email": "test@example.com",
            "app_name": "TestApp",
            "tier": tier,
            "builder": "lovable",
        },
        "findings": [{"severity": "high", "title": f"finding {i}"} for i in range(n_findings)],
        "verdict": {"summary": "test verdict"},
    }


def test_valid_tiers_set_is_canonical() -> None:
    """The canonical tier set is exactly the three names the customer surface uses."""
    assert VALID_TIERS == {"Starter Package", "Scale Up Package", "Pro Package"}


@pytest.mark.parametrize(
    "tier",
    ["Starter Package", "Scale Up Package", "Pro Package"],
)
def test_validate_accepts_each_canonical_tier(tier: str) -> None:
    """Each of the three tier names must pass validate() without raising."""
    validate(_make_data(tier))


def test_validate_rejects_unknown_tier() -> None:
    """An off-ladder tier must hit the SystemExit branch in validate()."""
    with pytest.raises(SystemExit):
        validate(_make_data("Premium Package"))


@pytest.mark.parametrize(
    "alias",
    ["full", "Full Package", "scaleup", "scale up", "scale up package"],
)
def test_alias_map_normalises_legacy_names_to_scale_up(alias: str) -> None:
    """Old "Full Package" YAMLs + every scale-up variant route to canonical."""
    canonical = TIER_ALIAS_TO_CANONICAL.get(alias.lower())
    assert canonical == "Scale Up Package", (
        f"Alias {alias!r} must normalise to 'Scale Up Package', got {canonical!r}"
    )


@pytest.mark.parametrize(
    ("tier", "expected_cap"),
    [
        ("Starter Package", 10),
        ("Scale Up Package", 30),
        ("Pro Package", 40),
    ],
)
def test_tier_caps_match_canonical_pipeline_values(
    tier: str, expected_cap: int, capsys: pytest.CaptureFixture[str]
) -> None:
    """The cap dict in validate() must match pipeline.DEFAULT_TIER_CAPS (10/30/40)."""
    data = _make_data(tier, n_findings=expected_cap + 1)
    validate(data)
    captured = capsys.readouterr()
    assert f"caps at {expected_cap}" in captured.err, (
        f"Expected '{tier}' cap of {expected_cap} in WARN stderr; got: {captured.err!r}"
    )
