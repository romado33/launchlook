"""
generate_verified_badge.py: produce a LaunchLook Verified badge for a customer.

Given a customer YAML (the same one ``scripts/deliver_report.py`` consumes),
this script emits:

    landing/images/badges/{slug}/light.svg
    landing/images/badges/{slug}/dark.svg
    landing/images/badges/{slug}/light.png       (optional, requires Pillow)
    landing/images/badges/{slug}/dark.png        (optional, requires Pillow)
    landing/data/verified/{slug}.json            (the verify.json record)

The SVG is the primary asset that customers embed on their site footer. The
PNG is a fallback for email clients or contexts that do not render SVG. The
``verify.json`` record is what ``api/verify.py`` checks against.

Two badge variants:
  * ``light`` -- dark ink on a light card, for light-background sites.
  * ``dark``  -- light ink on a dark card, for dark-background sites.

Design discipline per ``docs/SIMPLICITY-GUARDRAILS.md`` section 2.1: small,
monochrome, professional. Not a giant corporate seal.

Usage:

    # Generate badges for a single customer.
    python scripts/generate_verified_badge.py --customer customers/example-jane-sparkle.yaml

    # Same customer, but re-verify (fresh dates, same slug). Used by
    # the $9 re-verification flow after the original validity window
    # expires.
    python scripts/generate_verified_badge.py \\
        --customer customers/example-jane-sparkle.yaml \\
        --re-verify

    # Stamp the badge at a fixed date (deterministic for tests).
    python scripts/generate_verified_badge.py \\
        --customer customers/example-jane-sparkle.yaml \\
        --verified-at 2026-05-26

Re-running ``--re-verify`` against an existing ``verify.json`` is the same
operation as a fresh run plus a small ``previous_verified_at`` field on the
new record (so we can show the customer that this is their second checkup).
If there is no prior ``verify.json`` the script exits non-zero -- the $9
re-verify SKU is only valid for customers who had an active or expired
badge previously.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


REPO_ROOT = Path(__file__).resolve().parent.parent
BADGE_OUTPUT_ROOT = REPO_ROOT / "landing" / "images" / "badges"
VERIFY_DATA_ROOT = REPO_ROOT / "landing" / "data" / "verified"
DEFAULT_DOMAIN = "launchlook.app"

# Validity window per tier, in days. Both the canonical names from
# docs/PRODUCT-DECISIONS.md section 1 (Starter / Scale Up / Pro) and the
# legacy display names that still appear in some customer YAML files
# (Starter Package / Full Package / Pro Package) resolve to the same
# validity window. If a future tier renames cleanly, add the new name here
# and leave the old key for backward compatibility.
TIER_VALIDITY_DAYS: dict[str, int] = {
    "starter": 30,
    "starter package": 30,
    "scale up": 90,
    "scale up package": 90,
    "full": 90,
    "full package": 90,
    "pro": 180,
    "pro package": 180,
}

# Canonical display name used inside the verify.json + verify landing page.
# Maps any input tier alias to the preferred buyer-facing string.
TIER_DISPLAY_NAMES: dict[str, str] = {
    "starter": "Starter Package",
    "starter package": "Starter Package",
    "scale up": "Scale Up Package",
    "scale up package": "Scale Up Package",
    "full": "Scale Up Package",
    "full package": "Scale Up Package",
    "pro": "Pro Package",
    "pro package": "Pro Package",
}


# ---------------------------------------------------------------------------
# Tier + slug helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BadgeContext:
    """Everything the renderer + verify.json writer need."""

    customer_slug: str
    tier: str
    tier_display: str
    verified_at: date
    expires_at: date
    domain: str
    customer_url: str
    issued_by: str = "LaunchLook"

    @property
    def verified_at_str(self) -> str:
        return self.verified_at.isoformat()

    @property
    def expires_at_str(self) -> str:
        return self.expires_at.isoformat()

    @property
    def verified_at_short(self) -> str:
        # "May 2026" -- short, friendly, plain English. Used on the badge.
        return self.verified_at.strftime("%b %Y")

    @property
    def verify_url(self) -> str:
        return f"https://{self.domain}/verify?slug={self.customer_slug}"


def slugify(*parts: str) -> str:
    """Identical rule to scripts/deliver_report.py so badges line up with reports."""
    text = "-".join(p for p in parts if p)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "customer"


def normalize_tier(tier_raw: str) -> tuple[str, int]:
    """Resolve a tier alias to (display_name, validity_days).

    Raises SystemExit if the tier is unknown so the operator notices instead
    of silently shipping a badge with no expiry.
    """
    key = (tier_raw or "").strip().lower()
    if key not in TIER_VALIDITY_DAYS:
        sys.exit(
            f"ERROR: unknown tier {tier_raw!r}. "
            f"Allowed: {sorted(set(TIER_DISPLAY_NAMES.values()))}"
        )
    return TIER_DISPLAY_NAMES[key], TIER_VALIDITY_DAYS[key]


# ---------------------------------------------------------------------------
# verify.json
# ---------------------------------------------------------------------------


def build_verify_record(
    ctx: BadgeContext,
    previous_verified_at: str | None = None,
) -> dict[str, Any]:
    """Build the dict that becomes ``landing/data/verified/{slug}.json``.

    The ``checksum`` is over the deterministic subset of fields (slug, tier,
    verified_at, expires_at, issued_by, customer_url) so two calls with the
    same inputs produce the same hash. Tests rely on this.
    """
    record: dict[str, Any] = {
        "customer_slug": ctx.customer_slug,
        "verified_at": ctx.verified_at_str,
        "tier": ctx.tier_display,
        "expires_at": ctx.expires_at_str,
        "issued_by": ctx.issued_by,
        "customer_url": ctx.customer_url,
    }
    if previous_verified_at:
        record["previous_verified_at"] = previous_verified_at

    record["checksum"] = compute_checksum(record)
    return record


def compute_checksum(record: dict[str, Any]) -> str:
    """SHA-256 over the canonical JSON of the verifiable fields only.

    ``customer_url`` is included because it is what the verification page
    surfaces to the public visitor. ``previous_verified_at`` is excluded so
    fresh and re-verify badges with the same dates produce the same hash
    if the underlying audit data is the same.
    """
    canonical = {
        "customer_slug": record["customer_slug"],
        "verified_at": record["verified_at"],
        "tier": record["tier"],
        "expires_at": record["expires_at"],
        "issued_by": record["issued_by"],
        "customer_url": record["customer_url"],
    }
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------


# Per SIMPLICITY-GUARDRAILS section 2.1 the badge stays small and
# understated. Width is fixed at 220pt so the typography breathes; height
# is 56pt so it slots into a footer without forcing a row reflow. No
# gradients, no shadows, no icons beyond a tiny checkmark glyph.
BADGE_WIDTH = 220
BADGE_HEIGHT = 56


def render_svg(ctx: BadgeContext, variant: str) -> str:
    """Return the SVG markup for ``light`` or ``dark`` variant."""
    if variant not in ("light", "dark"):
        sys.exit(f"ERROR: variant must be 'light' or 'dark', got {variant!r}")

    if variant == "light":
        bg = "#FAF7F2"
        border = "#E7E0D6"
        ink = "#1F1B16"
        muted = "#6B6359"
        check = "#1F1B16"
    else:
        bg = "#1F1B16"
        border = "#2B2620"
        ink = "#FAF7F2"
        muted = "#B8B0A2"
        check = "#FAF7F2"

    primary_text = "LaunchLook Verified"
    secondary_text = f"Verified {ctx.verified_at_short} \u00b7 {ctx.tier_display}"
    aria_label = (
        f"LaunchLook Verified badge for {ctx.customer_slug}, "
        f"verified {ctx.verified_at_short}, {ctx.tier_display}, "
        f"valid through {_human_date(ctx.expires_at)}."
    )

    # Pure-text SVG so it renders identically wherever it is dropped in.
    # System font stack keeps the asset under 1.5 KB.
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{BADGE_WIDTH}" height="{BADGE_HEIGHT}" '
        f'viewBox="0 0 {BADGE_WIDTH} {BADGE_HEIGHT}" '
        f'role="img" aria-label="{_xml_escape(aria_label)}">\n'
        f'  <title>{_xml_escape(primary_text)} ({_xml_escape(ctx.tier_display)})</title>\n'
        f'  <rect x="0.5" y="0.5" width="{BADGE_WIDTH - 1}" height="{BADGE_HEIGHT - 1}" '
        f'rx="6" ry="6" fill="{bg}" stroke="{border}" stroke-width="1"/>\n'
        # Small check glyph (no third-party icon font).
        f'  <g transform="translate(14,18)" fill="none" stroke="{check}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n'
        f'    <circle cx="10" cy="10" r="9" fill="none" stroke="{check}" stroke-width="1.5"/>\n'
        f'    <polyline points="6,10.5 9,13.5 14,7.5"/>\n'
        f'  </g>\n'
        f'  <text x="46" y="24" '
        f'font-family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" '
        f'font-size="13" font-weight="600" fill="{ink}" letter-spacing="0.01em">'
        f'{_xml_escape(primary_text)}</text>\n'
        f'  <text x="46" y="40" '
        f'font-family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" '
        f'font-size="10" font-weight="400" fill="{muted}" letter-spacing="0.02em">'
        f'{_xml_escape(secondary_text)}</text>\n'
        f'</svg>\n'
    )


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _human_date(d: date) -> str:
    """Return a plain-English date like 'August 24, 2026' (no leading zero).

    ``%-d`` is GNU-only and breaks on Windows, so this helper strips the
    leading zero explicitly.
    """
    month = d.strftime("%B")
    return f"{month} {d.day}, {d.year}"


# ---------------------------------------------------------------------------
# PNG fallback (best-effort, optional)
# ---------------------------------------------------------------------------


def render_png(svg_text: str, out_path: Path, variant: str, ctx: BadgeContext) -> bool:
    """Try to write a PNG sibling for the SVG.

    Strategy:
      1. Pillow (PIL) if available -- pure-Python text rasterization.
      2. Otherwise: print a warning and skip (SVG is still the primary
         asset; almost every embed surface accepts SVG today).

    Returns True if a PNG was written, False otherwise.
    """
    try:
        from PIL import Image, ImageDraw  # type: ignore
    except ImportError:
        print(
            f"  ! Pillow not installed -- skipping {out_path.name} (SVG is primary). "
            "To enable PNG fallback: pip install Pillow",
            file=sys.stderr,
        )
        return False

    if variant == "light":
        bg = (250, 247, 242, 255)
        border = (231, 224, 214, 255)
        ink = (31, 27, 22, 255)
        muted = (107, 99, 89, 255)
    else:
        bg = (31, 27, 22, 255)
        border = (43, 38, 32, 255)
        ink = (250, 247, 242, 255)
        muted = (184, 176, 162, 255)

    scale = 2  # Retina-friendly. Final 440x112 px PNG.
    w, h = BADGE_WIDTH * scale, BADGE_HEIGHT * scale
    img = Image.new("RGBA", (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Rounded rectangle frame.
    radius = 6 * scale
    draw.rounded_rectangle(
        [(1, 1), (w - 2, h - 2)],
        radius=radius,
        outline=border,
        width=max(1, scale // 2),
    )

    # Small check circle (approx. SVG glyph at 14,18 box of 20x20).
    cx, cy = 14 * scale + 10 * scale, 18 * scale + 10 * scale
    r = 9 * scale
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=ink, width=max(1, scale // 2))
    pts = [
        (14 * scale + 6 * scale, 18 * scale + int(10.5 * scale)),
        (14 * scale + 9 * scale, 18 * scale + int(13.5 * scale)),
        (14 * scale + 14 * scale, 18 * scale + int(7.5 * scale)),
    ]
    draw.line(pts, fill=ink, width=max(2, scale))

    primary_text = "LaunchLook Verified"
    secondary_text = f"Verified {ctx.verified_at_short} \u00b7 {ctx.tier_display}"

    primary_font = _load_font(13 * scale, weight=600)
    secondary_font = _load_font(10 * scale, weight=400)

    draw.text((46 * scale, 11 * scale), primary_text, fill=ink, font=primary_font)
    draw.text((46 * scale, 30 * scale), secondary_text, fill=muted, font=secondary_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return True


def _load_font(size: int, weight: int = 400):
    """Best-effort cross-platform font loader for the PNG fallback."""
    try:
        from PIL import ImageFont  # type: ignore
    except ImportError:
        return None

    if weight >= 600:
        candidates = [
            "Inter-SemiBold.ttf",
            "Inter-Bold.ttf",
            "SegoeUI-Semibold.ttf",
            "Arial Bold.ttf",
            "DejaVuSans-Bold.ttf",
        ]
    else:
        candidates = [
            "Inter-Regular.ttf",
            "SegoeUI.ttf",
            "Arial.ttf",
            "Helvetica.ttf",
            "DejaVuSans.ttf",
        ]

    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# YAML loading
# ---------------------------------------------------------------------------


def load_customer_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        sys.exit("ERROR: pyyaml not installed. Run: pip install -r requirements.txt")

    if not path.exists():
        sys.exit(f"ERROR: customer file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        sys.exit(f"ERROR: {path} did not parse as a YAML mapping")

    return data


def build_context_from_yaml(
    data: dict[str, Any],
    verified_at: date,
    domain: str,
) -> BadgeContext:
    customer = data.get("customer") or {}
    for key in ("first_name", "app_name", "tier"):
        if not customer.get(key):
            sys.exit(f"ERROR: customer.{key} is required to mint a badge")

    slug = slugify(customer.get("first_name", ""), customer.get("app_name", ""))
    tier_display, validity_days = normalize_tier(customer["tier"])
    expires_at = verified_at + timedelta(days=validity_days)
    customer_url = (customer.get("app_url") or "").strip()

    return BadgeContext(
        customer_slug=slug,
        tier=customer["tier"],
        tier_display=tier_display,
        verified_at=verified_at,
        expires_at=expires_at,
        domain=domain,
        customer_url=customer_url,
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def write_badge_assets(
    ctx: BadgeContext,
    out_root: Path = BADGE_OUTPUT_ROOT,
    verify_root: Path = VERIFY_DATA_ROOT,
    previous_verified_at: str | None = None,
    skip_png: bool = False,
) -> dict[str, Path]:
    """Write SVG + PNG + verify.json for ``ctx``. Returns paths written."""
    out_dir = out_root / ctx.customer_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    verify_root.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}

    for variant in ("light", "dark"):
        svg_text = render_svg(ctx, variant)
        svg_path = out_dir / f"{variant}.svg"
        svg_path.write_text(svg_text, encoding="utf-8")
        written[f"{variant}_svg"] = svg_path

        if not skip_png:
            png_path = out_dir / f"{variant}.png"
            if render_png(svg_text, png_path, variant, ctx):
                written[f"{variant}_png"] = png_path

    record = build_verify_record(ctx, previous_verified_at=previous_verified_at)
    verify_path = verify_root / f"{ctx.customer_slug}.json"
    verify_path.write_text(
        json.dumps(record, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    written["verify_json"] = verify_path
    return written


def load_existing_verify(slug: str, verify_root: Path = VERIFY_DATA_ROOT) -> dict[str, Any] | None:
    path = verify_root / f"{slug}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--customer",
        required=True,
        help="Path to the customer YAML file (same shape deliver_report.py reads).",
    )
    parser.add_argument(
        "--re-verify",
        action="store_true",
        help=(
            "Reset verified_at to today and write a fresh expires_at. "
            "Requires an existing landing/data/verified/{slug}.json -- the "
            "$9 re-verify SKU is only valid for customers with a prior badge."
        ),
    )
    parser.add_argument(
        "--verified-at",
        default=None,
        help=(
            "Override the verification date (YYYY-MM-DD). Default: today. "
            "Use for deterministic regeneration during tests."
        ),
    )
    parser.add_argument(
        "--domain",
        default=DEFAULT_DOMAIN,
        help=f"Domain that hosts the verify endpoint (default: {DEFAULT_DOMAIN}).",
    )
    parser.add_argument(
        "--skip-png",
        action="store_true",
        help="Skip PNG generation even if Pillow is installed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.verified_at:
        try:
            verified_at = datetime.strptime(args.verified_at, "%Y-%m-%d").date()
        except ValueError:
            sys.exit(f"ERROR: --verified-at must be YYYY-MM-DD, got {args.verified_at!r}")
    else:
        verified_at = date.today()

    customer_path = Path(args.customer).resolve()
    data = load_customer_yaml(customer_path)
    ctx = build_context_from_yaml(data, verified_at=verified_at, domain=args.domain)

    previous_verified_at: str | None = None
    if args.re_verify:
        existing = load_existing_verify(ctx.customer_slug)
        if not existing:
            sys.exit(
                f"ERROR: --re-verify requested but no prior verify.json found at "
                f"landing/data/verified/{ctx.customer_slug}.json. The $9 re-verify "
                f"SKU only applies to customers with an active or expired badge. "
                f"Run without --re-verify to issue a fresh badge."
            )
        previous_verified_at = existing.get("verified_at")

    print(f"-> Customer:    {ctx.customer_slug}")
    print(f"-> Tier:        {ctx.tier_display}  ({ctx.expires_at - ctx.verified_at})")
    print(f"-> Verified:    {ctx.verified_at_str}")
    print(f"-> Expires:     {ctx.expires_at_str}")
    if previous_verified_at:
        print(f"-> Re-verify:   prior verified_at = {previous_verified_at}")

    written = write_badge_assets(
        ctx,
        previous_verified_at=previous_verified_at,
        skip_png=args.skip_png,
    )
    for label, path in written.items():
        print(f"  ok {label:13s} {path.relative_to(REPO_ROOT)}")

    print("\nEmbed snippet (copy into the customer's site footer):")
    print(
        f'  <a href="https://{ctx.domain}/verify?slug={ctx.customer_slug}" '
        f'target="_blank" rel="noopener">\n'
        f'    <img src="https://{ctx.domain}/images/badges/{ctx.customer_slug}/light.svg" '
        f'alt="LaunchLook Verified" height="48">\n'
        f"  </a>"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
