"""JSON draft persistence for in-flight audits.

Drafts live at ``drafts/{slug}.json`` (gitignored). Each draft holds the
full form payload plus a timestamp so the UI can offer to restore it on
the next page load.

Saves are atomic: we write to a temp file in the same directory and then
``os.replace`` it onto the target path. Reads tolerate missing files and
return ``None``.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SAFE_SLUG = re.compile(r"[^a-z0-9._-]+")


def safe_slug(slug: str) -> str:
    """Sanitize a slug so it can be used as a filename."""
    cleaned = SAFE_SLUG.sub("-", (slug or "").lower()).strip("-")
    return cleaned or "untitled"


def draft_path(drafts_dir: Path, slug: str) -> Path:
    return drafts_dir / f"{safe_slug(slug)}.json"


def save_draft(drafts_dir: Path, slug: str, payload: dict[str, Any]) -> Path:
    drafts_dir.mkdir(parents=True, exist_ok=True)
    target = draft_path(drafts_dir, slug)

    record = {
        "slug": safe_slug(slug),
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }

    fd, tmp_name = tempfile.mkstemp(prefix=".draft-", suffix=".json", dir=str(drafts_dir))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    return target


def load_draft(drafts_dir: Path, slug: str) -> dict[str, Any] | None:
    target = draft_path(drafts_dir, slug)
    if not target.exists():
        return None
    try:
        with target.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or "payload" not in data:
        return None
    return data


def delete_draft(drafts_dir: Path, slug: str) -> bool:
    target = draft_path(drafts_dir, slug)
    if not target.exists():
        return False
    try:
        target.unlink()
        return True
    except OSError:
        return False
