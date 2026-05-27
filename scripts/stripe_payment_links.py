"""Stripe Payment Link helpers for LaunchLook.

Requires STRIPE_SECRET_KEY in repo-root .env (live key for production links).

Usage:
  python scripts/stripe_payment_links.py disable-tax
  python scripts/stripe_payment_links.py disable-tax --dry-run
  python scripts/stripe_payment_links.py enable-tax
  python scripts/stripe_payment_links.py enable-tax --dry-run

By default, enable/disable-tax only touch Payment Links created via our API
scripts (metadata.product in API_PRODUCTS). Pass --all-active to affect every
active link instead.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(REPO_ROOT, ".env")
SUCCESS_URL = "https://launchlook.app/thanks"

# Fields applied on create (see _create_stripe*.py) — tax off by default.
PAYMENT_LINK_TAX_OFF: dict[str, str] = {
    "automatic_tax[enabled]": "false",
}

PAYMENT_LINK_TAX_ON: dict[str, str] = {
    "automatic_tax[enabled]": "true",
    "billing_address_collection": "auto",
}

# Payment Links created by _create_stripe.py / _create_stripe_maintier.py (May 2026).
API_PRODUCTS = frozenset(
    {
        "starter_package",
        "scale_up_package",
        "pro_package",
        "confidence_check",
        "handoff_report",
    }
)

REVERIFY_PRODUCT = "reverify"


def load_env() -> str:
    if not os.path.isfile(ENV_PATH):
        sys.exit(f"Missing {ENV_PATH} (need STRIPE_SECRET_KEY)")
    with open(ENV_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        sys.exit("STRIPE_SECRET_KEY missing from .env")
    if not key.startswith("sk_live"):
        sys.exit("Expected sk_live_* for production Payment Links")
    return key


def stripe_request(key: str, method: str, path: str, form: dict[str, str] | None = None):
    url = "https://api.stripe.com/v1/" + path
    data = urllib.parse.urlencode(form).encode("utf-8") if form else None
    headers = {
        "Authorization": f"Bearer {key}",
        "User-Agent": "launchlook-stripe-payment-links/1.0",
    }
    if data:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(body)
        except Exception:
            return exc.code, {"raw": body}


def list_all(key: str, path: str, params: dict[str, str] | None = None) -> list[dict]:
    items: list[dict] = []
    params = dict(params or {}, limit="100")
    starting_after = None
    while True:
        q = dict(params)
        if starting_after:
            q["starting_after"] = starting_after
        status, data = stripe_request(key, "GET", path + "?" + urllib.parse.urlencode(q))
        if status != 200:
            sys.exit(f"List {path} failed ({status}): {data}")
        items.extend(data["data"])
        if data.get("has_more"):
            starting_after = data["data"][-1]["id"]
        else:
            break
    return items


def payment_link_create_form(price_id: str, metadata: dict[str, str]) -> dict[str, str]:
    """Form fields for POST /v1/payment_links (new links)."""
    form: dict[str, str] = {
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "after_completion[type]": "redirect",
        "after_completion[redirect][url]": SUCCESS_URL,
        **PAYMENT_LINK_TAX_OFF,
    }
    for k, v in metadata.items():
        form[f"metadata[{k}]"] = v
    return form


def _is_api_link(pl: dict, all_active: bool) -> bool:
    if all_active:
        return True
    md = pl.get("metadata") or {}
    return md.get("product") in API_PRODUCTS


def enable_tax_on_link(key: str, plink_id: str, dry_run: bool) -> tuple[bool, str]:
    if dry_run:
        return True, "dry-run"
    status, data = stripe_request(
        key, "POST", f"payment_links/{plink_id}", dict(PAYMENT_LINK_TAX_ON)
    )
    if status != 200:
        err = data.get("error", data)
        return False, str(err.get("message", err) if isinstance(err, dict) else err)
    enabled = (data.get("automatic_tax") or {}).get("enabled")
    return bool(enabled), data.get("url", plink_id)


def disable_tax_on_link(key: str, plink_id: str, dry_run: bool) -> tuple[bool, str]:
    if dry_run:
        return True, "dry-run"
    status, data = stripe_request(
        key, "POST", f"payment_links/{plink_id}", dict(PAYMENT_LINK_TAX_OFF)
    )
    if status != 200:
        err = data.get("error", data)
        return False, str(err.get("message", err) if isinstance(err, dict) else err)
    enabled = (data.get("automatic_tax") or {}).get("enabled")
    return not enabled, data.get("url", plink_id)


def deactivate_link(key: str, plink_id: str, dry_run: bool) -> tuple[bool, str]:
    if dry_run:
        return True, "dry-run"
    status, data = stripe_request(key, "POST", f"payment_links/{plink_id}", {"active": "false"})
    if status != 200:
        err = data.get("error", data)
        return False, str(err.get("message", err) if isinstance(err, dict) else err)
    return not data.get("active", True), "deactivated"


def cmd_enable_tax(
    key: str, dry_run: bool, deactivate_reverify: bool, all_active: bool
) -> int:
    links = list_all(key, "payment_links", {"active": "true"})
    if not links:
        print("No active payment links found.")
        return 0

    tax_ok = tax_fail = deact_ok = deact_skip = skipped = 0
    for pl in links:
        pl_id = pl["id"]
        url = pl.get("url", "")
        md = pl.get("metadata") or {}
        product = md.get("product", "")
        tax_on = (pl.get("automatic_tax") or {}).get("enabled")

        if not _is_api_link(pl, all_active):
            skipped += 1
            continue

        if deactivate_reverify and product == REVERIFY_PRODUCT:
            if dry_run:
                print(f"  [dry-run] deactivate {pl_id}  {url}")
                deact_ok += 1
            else:
                ok, msg = deactivate_link(key, pl_id, dry_run=False)
                if ok:
                    print(f"  deactivated reverify  {pl_id}  {url}")
                    deact_ok += 1
                else:
                    print(f"  FAIL deactivate {pl_id}: {msg}")
            continue

        if tax_on:
            print(f"  skip (tax on)  {pl_id}  product={product or '-'}  {url}")
            deact_skip += 1
            continue

        ok, msg = enable_tax_on_link(key, pl_id, dry_run=dry_run)
        label = "would enable tax" if dry_run else "tax enabled"
        if ok:
            print(f"  {label}  {pl_id}  product={product or '-'}  {msg}")
            tax_ok += 1
        else:
            print(f"  FAIL {pl_id}  product={product or '-'}: {msg}")
            tax_fail += 1

    print(
        f"\nDone: tax enabled={tax_ok}, tax failed={tax_fail}, "
        f"already had tax={deact_skip}, skipped (not API link)={skipped}, "
        f"reverify deactivated={deact_ok}"
    )
    return 1 if tax_fail else 0


def cmd_disable_tax(key: str, dry_run: bool, all_active: bool) -> int:
    links = list_all(key, "payment_links", {"active": "true"})
    if not links:
        print("No active payment links found.")
        return 0

    tax_ok = tax_fail = tax_skip = skipped = 0
    for pl in links:
        if not _is_api_link(pl, all_active):
            skipped += 1
            continue

        pl_id = pl["id"]
        url = pl.get("url", "")
        product = (pl.get("metadata") or {}).get("product", "")
        tax_on = (pl.get("automatic_tax") or {}).get("enabled")

        if not tax_on:
            print(f"  skip (tax off)  {pl_id}  product={product or '-'}  {url}")
            tax_skip += 1
            continue

        ok, msg = disable_tax_on_link(key, pl_id, dry_run=dry_run)
        label = "would disable tax" if dry_run else "tax disabled"
        if ok:
            print(f"  {label}  {pl_id}  product={product or '-'}  {msg}")
            tax_ok += 1
        else:
            print(f"  FAIL {pl_id}  product={product or '-'}: {msg}")
            tax_fail += 1

    print(
        f"\nDone: tax disabled={tax_ok}, tax failed={tax_fail}, "
        f"already off={tax_skip}, skipped (not API link)={skipped}"
    )
    return 1 if tax_fail else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="LaunchLook Stripe Payment Link maintenance")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be updated without calling Stripe",
        )
        p.add_argument(
            "--all-active",
            action="store_true",
            help="Apply to every active Payment Link (default: API-created links only)",
        )

    disable = sub.add_parser(
        "disable-tax",
        help="Turn off automatic_tax on API-created Payment Links",
    )
    add_common_flags(disable)

    enable = sub.add_parser(
        "enable-tax",
        help="Turn on automatic_tax on API-created Payment Links",
    )
    add_common_flags(enable)
    enable.add_argument(
        "--deactivate-reverify",
        action="store_true",
        help="Deactivate active links with metadata product=reverify (feature removed)",
    )

    args = parser.parse_args()
    key = load_env()

    if args.command == "disable-tax":
        raise SystemExit(cmd_disable_tax(key, args.dry_run, args.all_active))
    if args.command == "enable-tax":
        raise SystemExit(
            cmd_enable_tax(key, args.dry_run, args.deactivate_reverify, args.all_active)
        )


if __name__ == "__main__":
    main()
