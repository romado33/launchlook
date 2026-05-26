"""Toggle public/private state on a hosted report page.

Per ``docs/SHAREABLE-REPORT-WORKFLOW.md``, every delivered audit gets a
private URL at ``launchlook.app/r/{slug}``. Default is private. Customer
opts in by replying ``share`` to the delivery email; Rob then runs::

    python scripts/share_report.py --slug jane-sparkle-marketplace --public
    python scripts/share_report.py --slug jane-sparkle-marketplace --private
    python scripts/share_report.py --slug jane-sparkle-marketplace --status

Pro tier customers also get the Handoff Report download toggle::

    python scripts/share_report.py --slug jane-sparkle-marketplace --share-handoff
    python scripts/share_report.py --slug jane-sparkle-marketplace --hide-handoff

The script never silently flips public on its own. Every flip is a
deliberate Rob-typed CLI invocation, which is the privacy-by-default
discipline rule from ``docs/SIMPLICITY-GUARDRAILS.md`` section 3 and
section 5 (no surprises, respect the customer's URL).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Windows consoles default to cp1252; force UTF-8 so unicode is safe to print.
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass


REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "landing" / "data" / "reports"
SHAREABLE_PAGES_DIR = REPO_ROOT / "landing" / "r"


# ---------------------------------------------------------------------------
# JSON load / save
# ---------------------------------------------------------------------------


def _report_path(slug: str) -> Path:
    return REPORTS_DIR / f"{slug}.json"


def _shareable_html_path(slug: str) -> Path:
    return SHAREABLE_PAGES_DIR / f"{slug}.html"


def load_report(slug: str) -> dict[str, Any]:
    path = _report_path(slug)
    if not path.exists():
        try:
            shown: Path | str = path.relative_to(REPO_ROOT)
        except ValueError:
            shown = path
        sys.exit(
            f"ERROR: no report found for slug {slug!r} at {shown}.\n"
            "Run scripts/deliver_report.py first to generate it."
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_report(slug: str, data: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _report_path(slug)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    return path


# ---------------------------------------------------------------------------
# State changes
# ---------------------------------------------------------------------------


def _stamp_history(data: dict[str, Any], event: str) -> None:
    history = data.setdefault("share_history", [])
    history.append(
        {
            "event": event,
            "at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    )


def set_public(slug: str, data: dict[str, Any]) -> dict[str, Any]:
    if data.get("is_public") is True:
        print(f"  - already public ({slug})")
        return data
    data["is_public"] = True
    _stamp_history(data, "set_public")
    return data


def set_private(slug: str, data: dict[str, Any]) -> dict[str, Any]:
    if data.get("is_public") is False:
        print(f"  - already private ({slug})")
        return data
    data["is_public"] = False
    _stamp_history(data, "set_private")
    return data


def set_handoff_shared(slug: str, data: dict[str, Any], shared: bool) -> dict[str, Any]:
    handoff = data.setdefault("handoff_report", {"available": False, "shared": False})
    if not handoff.get("available"):
        sys.exit(
            "ERROR: this customer does not have a Handoff Report available "
            "(Pro tier only). Use scripts/deliver_report.py --handoff-report "
            "for Pro customers, or the $99 add-on for Starter/Scale Up first."
        )
    if bool(handoff.get("shared")) == shared:
        state = "shared" if shared else "hidden"
        print(f"  - Handoff Report already {state} ({slug})")
        return data
    handoff["shared"] = shared
    _stamp_history(data, "share_handoff" if shared else "hide_handoff")
    return data


# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------


def git_commit(paths: list[Path], message: str) -> None:
    """Stage + commit the listed paths. No-op if not a git repo."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ! not inside a git repo, skipping commit", file=sys.stderr)
        return

    rels = [str(p.relative_to(REPO_ROOT)) for p in paths if p.exists()]
    if not rels:
        return
    subprocess.run(["git", "add", *rels], cwd=REPO_ROOT, check=True)
    subprocess.run(
        ["git", "commit", "-m", message, "--", *rels],
        cwd=REPO_ROOT,
        check=False,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _show_status(slug: str, data: dict[str, Any]) -> None:
    handoff = data.get("handoff_report") or {}
    print(f"Slug:              {slug}")
    print(f"Public:            {'yes' if data.get('is_public') else 'no'}")
    print(f"Tier:              {data.get('tier', '?')}")
    print(f"Audit date:        {data.get('audit_date', '?')}")
    print(f"App name:          {data.get('app_name', '?')}")
    print(f"Handoff available: {'yes' if handoff.get('available') else 'no'}")
    print(f"Handoff shared:    {'yes' if handoff.get('shared') else 'no'}")
    public_url = f"https://launchlook.app/r/{slug}"
    print(f"Public URL:        {public_url}")
    history = data.get("share_history") or []
    if history:
        print("Recent history:")
        for entry in history[-5:]:
            print(f"  - {entry.get('at', '?')}  {entry.get('event', '?')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--slug", required=True, help="Customer slug (e.g. jane-sparkle-marketplace)"
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--public", action="store_true", help="Make the report visible at /r/{slug}"
    )
    action.add_argument(
        "--private",
        action="store_true",
        help="Revert the report to private (gentle message shown)",
    )
    action.add_argument(
        "--status", action="store_true", help="Print the current state and exit"
    )
    action.add_argument(
        "--share-handoff",
        action="store_true",
        help="Make the Handoff Report PDF downloadable on the public page (Pro tier only)",
    )
    action.add_argument(
        "--hide-handoff",
        action="store_true",
        help="Hide the Handoff Report download from the public page",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Skip the automatic git commit (use this when piloting from a notebook)",
    )

    args = parser.parse_args(argv)

    slug = args.slug.strip()
    if not slug:
        sys.exit("ERROR: --slug is required and must not be empty")

    data = load_report(slug)

    if args.status:
        _show_status(slug, data)
        return 0

    if args.public:
        data = set_public(slug, data)
        message = f"Toggle /r/{slug} to public (q22 share_report.py)"
    elif args.private:
        data = set_private(slug, data)
        message = f"Toggle /r/{slug} to private (q22 share_report.py)"
    elif args.share_handoff:
        data = set_handoff_shared(slug, data, shared=True)
        message = f"Share Handoff Report for /r/{slug} (q22 share_report.py)"
    elif args.hide_handoff:
        data = set_handoff_shared(slug, data, shared=False)
        message = f"Hide Handoff Report for /r/{slug} (q22 share_report.py)"
    else:
        # argparse covers this but mypy doesn't know that
        parser.error("no action specified")
        return 2

    path = save_report(slug, data)
    try:
        rel: Path | str = path.relative_to(REPO_ROOT)
    except ValueError:
        rel = path
    print(f"  ✓ wrote {rel}")

    if not args.no_commit:
        git_commit([path], message)

    print("\nDone. Verify the public URL renders the expected state:")
    print(f"  https://launchlook.app/r/{slug}")
    html_path = _shareable_html_path(slug)
    if html_path.exists():
        try:
            preview = html_path.relative_to(REPO_ROOT)
        except ValueError:
            preview = html_path
        print(f"\nLocal preview: open {preview} in a browser.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
