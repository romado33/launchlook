"""Thin CLI around ``scripts/github_integration.py``.

Usage::

    # Dry-run preview (no API calls)
    python scripts/github_push.py --customer customers/example-pro-package.yaml --dry-run

    # Live create issues
    python scripts/github_push.py --customer customers/example-pro-package.yaml

    # Also post a PR comment summarizing the findings (uses pr_number from YAML
    # by default, or --pr to override)
    python scripts/github_push.py --customer customers/example-pro-package.yaml --pr 42

Library code lives in ``scripts/github_integration.py``. This file is
deliberately thin so the integration is testable in isolation and the
CLI is never asked to import-time anything that needs the network.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional convenience
    pass


for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from scripts.github_integration import (  # noqa: E402
    add_pr_comment,
    create_all_issues,
    load_customer_yaml,
    resolve_token_from_yaml,
)


def _print_summary_table(results: list[dict], out=sys.stdout) -> None:
    """Print a finding-title → issue-URL table after a live run."""
    if not results:
        return
    print("\nSummary:", file=out)
    width = max(len(r.get("title", "")) for r in results)
    width = min(width, 80)
    for r in results:
        title = (r.get("title") or "").strip()
        if len(title) > width:
            title = title[: width - 1] + "…"
        url = r.get("issue_url") or "(dry-run)"
        print(f"  {title.ljust(width)}  {url}", file=out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--customer", required=True, help="Path to customer YAML")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print issue previews without calling the GitHub API",
    )
    parser.add_argument(
        "--pr",
        type=int,
        default=None,
        help="PR number to comment on after issues are created (overrides github.pr_number in YAML)",
    )
    parser.add_argument(
        "--labels",
        default="launchlook,audit-finding",
        help="Comma-separated labels to apply to every created issue",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt before live issue creation",
    )
    args = parser.parse_args()

    yaml_path = Path(args.customer).resolve()
    try:
        data = load_customer_yaml(yaml_path)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    github_block = data.get("github") or {}
    repo_url = github_block.get("repo")
    if not repo_url:
        print(
            f"ERROR: {yaml_path.name} has no github.repo block. "
            "GitHub integration is opt-in — only customers who provided a "
            "repo URL during intake should have this block.",
            file=sys.stderr,
        )
        return 2

    tier = (data.get("customer") or {}).get("tier", "(unknown)")
    if tier != "Pro Package":
        print(
            f"WARN: customer tier is {tier!r}, not 'Pro Package'. GitHub "
            "integration is a Pro tier feature; continuing anyway since Rob "
            "ran this CLI manually.",
            file=sys.stderr,
        )

    labels = [s.strip() for s in args.labels.split(",") if s.strip()]
    pr_number = args.pr if args.pr is not None else github_block.get("pr_number")

    if args.dry_run:
        # Dry-run never reads the PAT, so an unset env var is fine.
        results = create_all_issues(
            repo_url=repo_url,
            token="",  # unused in dry_run
            audit_yaml_path=yaml_path,
            dry_run=True,
            labels=labels,
        )
        print(
            f"Dry-run complete: {len(results)} issue(s) would be created on {repo_url}."
        )
        if pr_number:
            print(
                f"PR comment would target #{pr_number} on the same repo "
                "(rerun without --dry-run to actually post)."
            )
        return 0

    try:
        token, env_var = resolve_token_from_yaml(data)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"→ Repo:     {repo_url}")
    print(
        f"→ YAML:     {yaml_path.relative_to(REPO_ROOT) if yaml_path.is_relative_to(REPO_ROOT) else yaml_path}"
    )
    print(f"→ Findings: {len(data.get('findings') or [])}")
    print(f"→ Labels:   {', '.join(labels) or '(none)'}")
    print(f"→ Token:    via env var {env_var} (value redacted)")
    if pr_number:
        print(f"→ PR:       #{pr_number} (summary comment will be posted after issues)")

    if not args.yes:
        confirm = (
            input(
                "\nThis will create one GitHub issue per finding (no undo — "
                "re-running creates duplicates). Type 'push' to confirm: "
            )
            .strip()
            .lower()
        )
        if confirm != "push":
            print("Aborted. No issues were created.")
            return 1

    try:
        results = create_all_issues(
            repo_url=repo_url,
            token=token,
            audit_yaml_path=yaml_path,
            dry_run=False,
            labels=labels,
        )
    except Exception as exc:
        print(f"ERROR during issue creation: {exc}", file=sys.stderr)
        return 1

    _print_summary_table(results)

    if pr_number:
        try:
            add_pr_comment(
                repo_url=repo_url,
                pr_number=int(pr_number),
                token=token,
                audit_yaml_path=yaml_path,
                issue_urls=[r.get("issue_url") for r in results],
            )
        except Exception as exc:
            print(f"ERROR posting PR comment: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
