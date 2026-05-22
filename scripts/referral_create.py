"""
referral_create.py — BL-12

Create a Stripe coupon code per customer and write it back to the Notion
Customers database. Pattern: {FIRST_NAME}5 (random suffix if name collides).

Coupon: $5 off, one-time use, applies to any of the three LaunchLook products.

Usage:
    python scripts/referral_create.py --customer-id <notion_page_id>
    python scripts/referral_create.py --first-name Sarah --email sarah@example.com

The first form looks up the customer in Notion and updates the same row.
The second form is for manual one-off coupon creation; you copy the code to Notion yourself.

Requires:
    STRIPE_SECRET_KEY in .env
    NOTION_TOKEN in .env
    NOTION_CUSTOMERS_DB_ID in .env (only if using --customer-id)
"""

from __future__ import annotations

import argparse
import os
import secrets
import string
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent

COUPON_AMOUNT_OFF_CENTS = 500  # $5.00
COUPON_DURATION = "once"


def require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        sys.exit(f"ERROR: {key} not set in environment or .env")
    return val


def generate_code(first_name: str, suffix_length: int = 0) -> str:
    """Generate a coupon code. Default: SARAH5. With suffix: SARAH5-A7K2."""
    base = "".join(c for c in first_name.upper() if c.isalpha())[:12] or "FRIEND"
    if suffix_length == 0:
        return f"{base}5"
    alphabet = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(suffix_length))
    return f"{base}5-{suffix}"


def create_stripe_coupon(code: str, first_name: str, email: str | None) -> str:
    """Create a Stripe promotion code. Returns the created code string."""
    try:
        import stripe
    except ImportError:
        sys.exit("ERROR: stripe package not installed. Run: pip install -e \".\"")

    stripe.api_key = require_env("STRIPE_SECRET_KEY")

    # Create a Coupon (reusable rule) then a Promotion Code (the human-readable code)
    coupon = stripe.Coupon.create(
        amount_off=COUPON_AMOUNT_OFF_CENTS,
        currency="usd",
        duration=COUPON_DURATION,
        name=f"LaunchLook referral — {first_name}",
        max_redemptions=10,
        metadata={
            "referrer_first_name": first_name,
            "referrer_email": email or "",
            "source": "referral_create.py",
        },
    )

    promo = stripe.PromotionCode.create(
        coupon=coupon.id,
        code=code,
        max_redemptions=10,
        metadata={"referrer_first_name": first_name},
    )

    return promo.code


def update_notion_customer(page_id: str, referral_code: str) -> None:
    """Write the referral code back to the Customers DB row."""
    try:
        from notion_client import Client
    except ImportError:
        sys.exit("ERROR: notion-client package not installed. Run: pip install -e \".\"")

    notion = Client(auth=require_env("NOTION_TOKEN"))
    notion.pages.update(
        page_id=page_id,
        properties={
            "Referral Code": {
                "rich_text": [{"text": {"content": referral_code}}]
            }
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--customer-id", help="Notion page ID of the customer row")
    parser.add_argument("--first-name", help="Customer first name (used as coupon prefix)")
    parser.add_argument("--email", help="Customer email (stored in coupon metadata)")
    parser.add_argument("--collision-suffix", type=int, default=0, help="Add a random N-char suffix (use 4 if you've hit a name collision)")
    parser.add_argument("--dry-run", action="store_true", help="Print the would-be code without calling Stripe")

    args = parser.parse_args()

    if not args.first_name and not args.customer_id:
        sys.exit("ERROR: provide either --first-name or --customer-id")

    first_name = args.first_name
    email = args.email

    if args.customer_id and not first_name:
        # Look up first name from Notion
        try:
            from notion_client import Client
        except ImportError:
            sys.exit("ERROR: notion-client package not installed.")
        notion = Client(auth=require_env("NOTION_TOKEN"))
        page = notion.pages.retrieve(args.customer_id)
        # Adjust property name based on actual Notion schema
        title_property = page["properties"].get("Name", {}).get("title", [])
        first_name = title_property[0]["plain_text"] if title_property else "Friend"
        email_property = page["properties"].get("Email", {}).get("email")
        email = email or email_property

    code = generate_code(first_name, suffix_length=args.collision_suffix)

    if args.dry_run:
        print(f"DRY RUN — would create Stripe promotion code: {code}")
        if args.customer_id:
            print(f"DRY RUN — would update Notion page: {args.customer_id}")
        return 0

    print(f"Creating Stripe promotion code: {code}")
    actual_code = create_stripe_coupon(code, first_name, email)
    print(f"Created: {actual_code}")

    if args.customer_id:
        print(f"Updating Notion customer row: {args.customer_id}")
        update_notion_customer(args.customer_id, actual_code)
        print("Notion updated.")
    else:
        print(f"\nManual step: copy this code into the customer's Notion row → Referral Code:")
        print(f"  {actual_code}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
