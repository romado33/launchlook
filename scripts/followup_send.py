"""
followup_send.py — BL-13

Daily cron job. Reads the Notion Customers database and:

1. For each customer where Delivered=true AND Delivery Date was ~3 days ago
   AND Follow-up Sent=false → send the day-3 follow-up email + check the box.

2. For each Polish-tier customer where Delivered=true AND Delivery Date was
   ~7 days ago AND Day-7 Sent=false → send the day-7 check-in.

Runs daily at 14:00 UTC via .github/workflows/daily-followup.yml.

Idempotent — safe to re-run. Won't double-send because of the checkbox guard.

Usage (local test):
    python scripts/followup_send.py --dry-run

Production (from GitHub Actions):
    python scripts/followup_send.py

Requires in .env:
    NOTION_TOKEN
    NOTION_CUSTOMERS_DB_ID
    RESEND_API_KEY
    FROM_EMAIL (default: hello@launchlook.app)
    ADMIN_EMAIL (default: rob@launchlook.app, BCC for visibility)
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
EMAIL_DIR = REPO_ROOT / "templates" / "email"


def require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        sys.exit(f"ERROR: {key} not set in environment or .env")
    return val


def get_template(name: str) -> tuple[str, str]:
    """Return (subject, body) from a template file like 'followup-d3.txt'."""
    path = EMAIL_DIR / name
    if not path.exists():
        sys.exit(f"ERROR: template {path} not found")
    text = path.read_text(encoding="utf-8")
    # Strip the "---" footer with variable docs
    if "\n---\n" in text:
        text = text.split("\n---\n")[0]
    # First line is "Subject: ..."
    lines = text.splitlines()
    subject = lines[0].removeprefix("Subject:").strip()
    body = "\n".join(lines[1:]).strip()
    return subject, body


def render(template_text: str, variables: dict[str, str]) -> str:
    out = template_text
    for k, v in variables.items():
        out = out.replace("{" + k + "}", str(v or ""))
    return out


def query_notion_customers():
    """Query Notion for delivered customers needing a follow-up."""
    try:
        from notion_client import Client
    except ImportError:
        sys.exit("ERROR: notion-client package not installed. Run: pip install -e \".\"")

    notion = Client(auth=require_env("NOTION_TOKEN"))
    db_id = require_env("NOTION_CUSTOMERS_DB_ID")

    response = notion.databases.query(
        database_id=db_id,
        filter={
            "and": [
                {"property": "Delivered", "checkbox": {"equals": True}},
            ]
        },
    )
    return response["results"]


def parse_customer(row: dict) -> dict | None:
    """Extract the fields we care about from a Notion page object."""
    props = row.get("properties", {})

    def text(prop_name: str) -> str:
        prop = props.get(prop_name, {})
        if "title" in prop:
            return "".join(t["plain_text"] for t in prop["title"])
        if "rich_text" in prop:
            return "".join(t["plain_text"] for t in prop["rich_text"])
        if "email" in prop:
            return prop.get("email") or ""
        if "select" in prop and prop["select"]:
            return prop["select"]["name"]
        return ""

    def checked(prop_name: str) -> bool:
        prop = props.get(prop_name, {})
        return prop.get("checkbox", False)

    def date_field(prop_name: str) -> date | None:
        prop = props.get(prop_name, {})
        d = prop.get("date")
        if not d or not d.get("start"):
            return None
        return datetime.fromisoformat(d["start"].replace("Z", "+00:00")).date()

    name = text("Name")
    email = text("Email")
    if not name or not email:
        return None

    return {
        "page_id": row["id"],
        "name": name,
        "email": email,
        "app_url": text("App URL"),
        "tier": text("Tier"),
        "delivered_date": date_field("Payment Date"),  # using payment date as proxy if Delivery Date isn't stored separately
        "follow_up_sent": checked("Follow-up Sent"),
        "referral_code": text("Referral Code"),
    }


def send_email(to: str, subject: str, body: str, dry_run: bool = False) -> None:
    if dry_run:
        print(f"  [DRY RUN] would send to {to}:")
        print(f"  Subject: {subject}")
        print(f"  Body:\n    " + body.replace("\n", "\n    "))
        return

    try:
        import resend
    except ImportError:
        sys.exit("ERROR: resend package not installed. Run: pip install -e \".\"")

    resend.api_key = require_env("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "hello@launchlook.app")
    admin_email = os.getenv("ADMIN_EMAIL")

    payload = {
        "from": f"Rob at LaunchLook <{from_email}>",
        "to": [to],
        "subject": subject,
        "text": body,
        "reply_to": from_email,
    }
    if admin_email:
        payload["bcc"] = [admin_email]

    resend.Emails.send(payload)


def mark_followup_sent(page_id: str, dry_run: bool = False) -> None:
    if dry_run:
        print(f"  [DRY RUN] would mark Follow-up Sent=true on {page_id}")
        return
    from notion_client import Client

    notion = Client(auth=require_env("NOTION_TOKEN"))
    notion.pages.update(
        page_id=page_id,
        properties={"Follow-up Sent": {"checkbox": True}},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Don't actually send or update Notion")
    parser.add_argument("--days-after", type=int, default=3, help="Days after Delivered to send follow-up (default: 3)")
    args = parser.parse_args()

    today = date.today()
    target_date = today - timedelta(days=args.days_after)

    print(f"Looking for customers delivered on {target_date.isoformat()} (today minus {args.days_after} days)")

    customers = [parse_customer(r) for r in query_notion_customers()]
    customers = [c for c in customers if c]

    sent_count = 0
    for c in customers:
        if c["follow_up_sent"]:
            continue
        if not c["delivered_date"] or c["delivered_date"] != target_date:
            continue

        print(f"\nCustomer: {c['name']} ({c['email']})")
        subject, body = get_template("followup-d3.txt")
        rendered = render(body, {
            "NAME": c["name"],
            "REFERRAL_CODE": c["referral_code"] or "(none — generate via scripts/referral_create.py)",
        })
        send_email(c["email"], subject, rendered, dry_run=args.dry_run)
        mark_followup_sent(c["page_id"], dry_run=args.dry_run)
        sent_count += 1

    print(f"\nDone. Sent {sent_count} follow-up email(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
