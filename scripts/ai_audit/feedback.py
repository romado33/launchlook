"""Per-customer AI-feedback log used by the audit UI review mode.

Each AI-generated draft gets one record at ``data/ai_feedback/{slug}.json``::

    {
      "slug": "jane-smith",
      "ai_generated_at": "2026-05-25T22:30:00Z",
      "provider": "claude",
      "model": "claude-sonnet-4-5-20250929",
      "reviewed_at": "2026-05-25T22:38:00Z",
      "actions": [
        {"finding_idx": 0, "action": "approved", "ai_title": "...", "ai_severity": "critical"},
        {"finding_idx": 1, "action": "edited",   "ai_title": "...", "final_title": "...", "ai_severity": "high", "final_severity": "medium"},
        {"finding_idx": 2, "action": "rejected", "ai_title": "..."},
        {"finding_idx": 3, "action": "regenerated", "regen_count": 2}
      ]
    }

The file is the source of truth for AI quality measurements over time.
Reads tolerate missing files (treated as no prior actions).
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def feedback_path(repo_root: Path, slug: str) -> Path:
    return repo_root / "data" / "ai_feedback" / f"{slug}.json"


def load(repo_root: Path, slug: str) -> dict[str, Any]:
    target = feedback_path(repo_root, slug)
    if not target.exists():
        return {}
    try:
        with target.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_atomic(target: Path, data: dict[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=".aifeedback-", suffix=".json", dir=str(target.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=False)
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def initialize(
    repo_root: Path,
    slug: str,
    *,
    findings: list[dict[str, Any]],
    provider: str,
    model: str,
    tier: str,
) -> Path:
    """Record the AI-generated baseline. Called once by ai_audit.py.

    Each finding starts with status ``"draft"``. The UI mutates this as
    Rob reviews. We intentionally store ai_title / ai_severity (a snapshot
    of what the LLM produced) so edits later can be diffed against it.
    """
    target = feedback_path(repo_root, slug)
    data = {
        "slug": slug,
        "ai_generated_at": _now(),
        "provider": provider,
        "model": model,
        "tier": tier,
        "reviewed_at": None,
        "actions": [
            {
                "finding_idx": i,
                "action": "draft",
                "ai_title": (f.get("title") or "").strip(),
                "ai_severity": (f.get("severity") or "").strip().lower(),
                "regen_count": 0,
            }
            for i, f in enumerate(findings)
        ],
    }
    _save_atomic(target, data)
    return target


def record_action(
    repo_root: Path,
    slug: str,
    finding_idx: int,
    action: str,
    *,
    ai_title: str | None = None,
    ai_severity: str | None = None,
    final_title: str | None = None,
    final_severity: str | None = None,
) -> None:
    """Append or update a single action.

    Recognized actions:
    * ``"approved"``    — Rob accepted without edits.
    * ``"edited"``      — Rob accepted with edits. ``final_*`` capture the
      post-edit state.
    * ``"rejected"``    — Rob deleted the finding.
    * ``"regenerated"`` — Rob asked the LLM to redo it; we bump
      ``regen_count`` and keep prior ai_title/severity.
    """
    data = load(repo_root, slug)
    if not data:
        return  # uninitialized; UI must call /api/feedback only after ai_audit ran

    actions = data.setdefault("actions", [])
    while len(actions) <= finding_idx:
        actions.append({"finding_idx": len(actions), "action": "draft"})

    entry = actions[finding_idx]
    entry["finding_idx"] = finding_idx
    entry["action"] = action

    if ai_title is not None:
        entry.setdefault("ai_title", ai_title)
    if ai_severity is not None:
        entry.setdefault("ai_severity", ai_severity)

    if final_title is not None:
        entry["final_title"] = final_title
    if final_severity is not None:
        entry["final_severity"] = final_severity

    if action == "regenerated":
        entry["regen_count"] = int(entry.get("regen_count", 0)) + 1

    data["reviewed_at"] = _now()
    _save_atomic(feedback_path(repo_root, slug), data)


def finalize(
    repo_root: Path,
    slug: str,
    *,
    final_findings: list[dict[str, Any]] | None = None,
) -> None:
    """Stamp ``reviewed_at`` and snapshot the final findings (post-approve-all).

    Called from the UI's "Approve All Remaining & Ship" handler. We diff
    the snapshot against ai_title/severity to infer per-finding actions
    that weren't already recorded (silent edits, etc).
    """
    data = load(repo_root, slug)
    if not data:
        return

    data["reviewed_at"] = _now()

    if final_findings is not None:
        actions = data.setdefault("actions", [])
        for i, finding in enumerate(final_findings):
            while len(actions) <= i:
                actions.append({"finding_idx": i, "action": "draft"})
            entry = actions[i]
            final_title = (finding.get("title") or "").strip()
            final_severity = (finding.get("severity") or "").strip().lower()

            # If the entry was still a "draft" or "approved", determine
            # whether the final state matches the AI-generated state.
            if entry.get("action") in (None, "draft", "approved"):
                ai_title = entry.get("ai_title") or final_title
                ai_severity = entry.get("ai_severity") or final_severity
                if final_title == ai_title and final_severity == ai_severity:
                    entry["action"] = "approved"
                else:
                    entry["action"] = "edited"
                    entry["final_title"] = final_title
                    entry["final_severity"] = final_severity

    _save_atomic(feedback_path(repo_root, slug), data)
