"""ai_audit.py — generate a draft LaunchLook audit YAML from a live URL.

This is the foundational entry point for the AI-first delivery pipeline:

    URL  →  screenshots + prescreener + HTML extract  →  LLM (Claude/GPT)
         →  customers/{slug}.yaml  →  audit_ui --review-ai (spot-check)
         →  deliver_report.py (PDFs + email)

Usage (smoke test):

    python scripts/ai_audit.py \\
        --slug ai-test \\
        --url https://example.com \\
        --tier "Starter Package" \\
        --builder Lovable \\
        --name "Test" \\
        --email test@test.com \\
        --app-name "TestApp" \\
        --provider stub \\
        --dry-run

Usage (real customer with Claude):

    # 1) Add ANTHROPIC_API_KEY to .env
    # 2) Run end-to-end:
    python scripts/ai_audit.py \\
        --slug jane-smith \\
        --url https://jane.lovable.app \\
        --tier "Scale Up Package" \\
        --builder Lovable \\
        --name "Jane Smith" \\
        --email jane@example.com \\
        --app-name "Sparkle"

    # 3) Spot-check in the audit UI:
    python scripts/audit_ui.py --slug jane-smith --review-ai

    # 4) Approve all & ship (button in the UI footer), or:
    python scripts/deliver_report.py --customer customers/jane-smith.yaml --send

Provider selection (--provider):
    auto    — Claude if ANTHROPIC_API_KEY, else GPT (default)
    claude  — force Anthropic
    gpt     — force OpenAI
    stub    — offline placeholder generator (smoke testing only)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Force UTF-8 console output on Windows so emoji print safely.
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


from scripts.ai_audit import pipeline as ai_pipeline  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a draft LaunchLook audit YAML from a customer URL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--slug", required=True, help="Customer slug (filename for customers/<slug>.yaml)")
    parser.add_argument("--url", required=True, help="Customer app URL (https://...)")
    parser.add_argument(
        "--tier",
        required=True,
        choices=["Starter Package", "Scale Up Package", "Pro Package"],
        help="Tier purchased",
    )
    parser.add_argument("--builder", required=True, help="Builder (Lovable, Bolt, v0, Cursor, Replit, Base44, Other)")
    parser.add_argument("--name", default="", help='Customer full name (e.g. "Jane Smith")')
    parser.add_argument("--first-name", default="", dest="first_name", help="Override first name")
    parser.add_argument("--last-name", default="", dest="last_name", help="Override last name")
    parser.add_argument("--email", default="", help="Customer email")
    parser.add_argument("--app-name", required=True, dest="app_name", help="Customer app/product name")
    parser.add_argument("--intake-notes", default="", dest="intake_notes", help="Optional intake notes pulled from Tally")
    parser.add_argument(
        "--platform",
        default="vibe-coder",
        choices=["vibe-coder", "webflow"],
        help=(
            "Customer's editing platform. 'vibe-coder' (default) covers "
            "Lovable / Bolt / v0 / Cursor / Replit / Base44 and uses the "
            "builder-aware fix prompts. 'webflow' switches fix prompts to "
            "Webflow Designer language and enables Webflow-specific check "
            "categories (form submission, noindex, schema, breakpoints)."
        ),
    )
    parser.add_argument(
        "--provider",
        default="auto",
        choices=["auto", "claude", "gpt", "stub"],
        help="LLM provider. auto picks Claude if available, then GPT. stub runs offline (smoke test).",
    )
    parser.add_argument("--skip-capture", action="store_true", help="Skip screenshot capture (use existing screenshots)")
    parser.add_argument("--skip-prescreen", action="store_true", help="Skip regex prescreener")
    parser.add_argument("--dry-run", action="store_true", help="Do not write YAML; print to stdout")
    parser.add_argument("--max-findings", type=int, default=None, help="Cap findings count (default: tier cap)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    ctx = ai_pipeline.context_from_kwargs(
        slug=args.slug,
        url=args.url,
        tier=args.tier,
        builder=args.builder,
        name=args.name,
        first_name=args.first_name,
        last_name=args.last_name,
        email=args.email,
        app_name=args.app_name,
        intake_notes=args.intake_notes,
        platform=args.platform,
    )

    print()
    print("LaunchLook AI audit pipeline")
    print(f"  Slug:      {ctx.slug}")
    print(f"  URL:       {ctx.url}")
    print(f"  Tier:      {ctx.tier}")
    print(f"  Platform:  {ctx.platform}")
    print(f"  Builder:   {ctx.builder}")
    print(f"  Customer:  {ctx.first_name} {ctx.last_name} <{ctx.email}>")
    print(f"  App:       {ctx.app_name}")
    print(f"  Provider:  {args.provider}")
    print(f"  Dry run:   {args.dry_run}")
    print()

    try:
        result = ai_pipeline.run(
            ctx,
            provider=args.provider,
            skip_capture=args.skip_capture,
            skip_prescreen=args.skip_prescreen,
            dry_run=args.dry_run,
            max_findings=args.max_findings,
        )
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"\nFATAL: pipeline failed: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 2

    print()
    print("-" * 60)
    print(f"  Provider used:   {result.provider}")
    print(f"  Model:           {result.model}")
    print(f"  Findings:        {result.findings_count}")
    print(f"  Prescreen hits:  {len(result.prescreener_hits)}")
    print(f"  Pages scraped:   {len(result.pages)}")
    if result.yaml_path:
        print(f"  YAML written:    {result.yaml_path.relative_to(REPO_ROOT)}")
    print("-" * 60)

    if args.dry_run:
        print("\n--- DRAFT YAML (dry-run, not written) ---\n")
        print(result.yaml_text)
        print("\n--- END YAML ---\n")
        return 0

    print()
    print("Next:")
    print(f"  python scripts/audit_ui.py --slug {ctx.slug} --review-ai")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
