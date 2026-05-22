"""
customers_track.py — paying customer / subscriber tracker (local JSON + milestone gate)

Single source of truth on disk: data/customers.json (gitignored).
Mirror the same fields in Notion **Customers** when your workspace is ready.

Usage:
    python scripts/customers_track.py init
    python scripts/customers_track.py add --name Alex --email a@x.com --tier starter --app-url https://...
    python scripts/customers_track.py list
    python scripts/customers_track.py stats
    python scripts/customers_track.py show cust_20260522_abc123
    python scripts/customers_track.py update cust_... --status delivered --notion-report-url https://...
    python scripts/customers_track.py mark-intake cust_...
    python scripts/customers_track.py mark-delivered cust_... --notion-report-url https://...
    python scripts/customers_track.py acknowledge-milestone-10
    python scripts/customers_track.py export-csv

At 10 paying customers, read docs/CUSTOMER-10-RUNBOOK.md before starting BL-14/BL-15.
"""

from __future__ import annotations

import argparse
import csv
import json
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CUSTOMERS_PATH = DATA_DIR / "customers.json"
EXAMPLE_PATH = DATA_DIR / "customers.example.json"
MILESTONES_PATH = DATA_DIR / "milestones.json"
EXPORT_CSV_PATH = DATA_DIR / "customers-export.csv"

TIER_ALIASES = {
    "starter": "starter",
    "9": "starter",
    "starter package ($9)": "starter",
    "starter package": "starter",
    "full": "full",
    "29": "full",
    "launch": "full",
    "full package ($29)": "full",
    "full package": "full",
}

TIER_TURNAROUND_HOURS = {"starter": 24, "full": 12}

VALID_STATUSES = {
    "lead",
    "paid",
    "intake_received",
    "auditing",
    "delivered",
    "refunded",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_milestones_config() -> dict:
    if MILESTONES_PATH.exists():
        return json.loads(MILESTONES_PATH.read_text(encoding="utf-8"))
    return {
        "goals": {
            "paying_customers_60_day_target": 8,
            "paying_customers_automation_unlock": 10,
        }
    }


def normalize_tier(raw: str) -> str:
    key = raw.strip().lower()
    if key not in TIER_ALIASES:
        sys.exit(f"ERROR: tier must be starter or full (got {raw!r})")
    return TIER_ALIASES[key]


def load_store() -> dict:
    if not CUSTOMERS_PATH.exists():
        sys.exit(
            f"ERROR: {CUSTOMERS_PATH} not found. Run: python scripts/customers_track.py init"
        )
    return json.loads(CUSTOMERS_PATH.read_text(encoding="utf-8"))


def save_store(store: dict) -> None:
    store["updated_at"] = utc_now_iso()
    CUSTOMERS_PATH.write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")


def new_customer_id() -> str:
    day = date.today().strftime("%Y%m%d")
    suffix = secrets.token_hex(3)
    return f"cust_{day}_{suffix}"


def delivery_due_from_payment(payment_date: str, tier: str) -> str:
    d = date.fromisoformat(payment_date)
    hours = TIER_TURNAROUND_HOURS[tier]
    due = datetime.combine(d, datetime.min.time()) + timedelta(hours=hours)
    return due.date().isoformat()


def counts_paying(store: dict, cfg: dict) -> int:
    exclude = set(cfg.get("counts_as_paying", {}).get("exclude_statuses", ["lead", "refunded"]))
    require_payment = cfg.get("counts_as_paying", {}).get("requires_payment_date", True)
    n = 0
    for c in store.get("customers", []):
        if c.get("status") in exclude:
            continue
        if require_payment and not c.get("payment_date"):
            continue
        if c.get("status") == "lead" and not c.get("payment_date"):
            continue
        n += 1
    return n


def cmd_init(_: argparse.Namespace) -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CUSTOMERS_PATH.exists():
        print(f"Already exists: {CUSTOMERS_PATH}")
        return 0
    if EXAMPLE_PATH.exists():
        store = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        store["customers"] = []
        store["milestones"] = {
            "customer_10_unlock_acknowledged": False,
            "customer_10_unlocked_at": None,
        }
        store["updated_at"] = utc_now_iso()
    else:
        store = {
            "version": 1,
            "updated_at": utc_now_iso(),
            "milestones": {
                "customer_10_unlock_acknowledged": False,
                "customer_10_unlocked_at": None,
            },
            "customers": [],
        }
    save_store(store)
    print(f"Created {CUSTOMERS_PATH}")
    print("Add rows with: python scripts/customers_track.py add ...")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    store = load_store()
    tier = normalize_tier(args.tier)
    payment_date = args.payment_date or date.today().isoformat()
    cid = new_customer_id()
    row = {
        "id": cid,
        "name": args.name.strip(),
        "email": args.email.strip().lower(),
        "app_url": args.app_url.strip(),
        "app_name": (args.app_name or "").strip() or None,
        "platform": (args.platform or "").strip() or None,
        "tier": tier,
        "status": "paid",
        "payment_date": payment_date,
        "intake_received": False,
        "intake_received_at": None,
        "delivery_due": delivery_due_from_payment(payment_date, tier),
        "delivered_at": None,
        "notion_report_url": None,
        "notion_page_id": None,
        "stripe_payment_id": (args.stripe_payment_id or "").strip() or None,
        "referral_code": None,
        "referrals_count": 0,
        "followup_d3_sent": False,
        "followup_d7_sent": False,
        "feedback_received": False,
        "useful_rating": None,
        "notes": (args.notes or "").strip(),
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    store["customers"].append(row)
    save_store(store)
    print(f"Added {cid} — {row['name']} ({tier}) due {row['delivery_due']}")
    cmd_stats(argparse.Namespace())
    return 0


def find_customer(store: dict, customer_id: str) -> dict:
    for c in store["customers"]:
        if c["id"] == customer_id:
            return c
    sys.exit(f"ERROR: no customer {customer_id}")


def cmd_list(args: argparse.Namespace) -> int:
    store = load_store()
    rows = store.get("customers", [])
    if args.status:
        rows = [r for r in rows if r.get("status") == args.status]
    if not rows:
        print("(no customers)")
        return 0
    for c in sorted(rows, key=lambda x: x.get("payment_date") or "", reverse=True):
        intake = "✓" if c.get("intake_received") else "·"
        print(
            f"{c['id']}  {c.get('payment_date','?')}  {c.get('tier','?'):7}  "
            f"{c.get('status','?'):16}  intake{intake}  {c.get('name')}  <{c.get('email')}>"
        )
    return 0


def cmd_stats(_: argparse.Namespace) -> int:
    store = load_store()
    cfg = load_milestones_config()
    goals = cfg.get("goals", {})
    target_8 = goals.get("paying_customers_60_day_target", 8)
    target_10 = goals.get("paying_customers_automation_unlock", 10)
    paying = counts_paying(store, cfg)
    delivered = sum(1 for c in store["customers"] if c.get("status") == "delivered")
    auditing = sum(1 for c in store["customers"] if c.get("status") in ("auditing", "intake_received"))
    print(f"Paying customers (milestone count): {paying}")
    print(f"Delivered: {delivered}  |  In progress: {auditing}")
    print(f"60-day target: {paying}/{target_8}  |  Automation unlock: {paying}/{target_10}")
    ms = store.get("milestones", {})
    if paying >= target_10:
        if ms.get("customer_10_unlock_acknowledged"):
            print("Customer 10 gate: UNLOCKED (acknowledged)")
        else:
            print("Customer 10 gate: REACHED — run: python scripts/customers_track.py acknowledge-milestone-10")
            print("Then read: docs/CUSTOMER-10-RUNBOOK.md")
    else:
        print(f"Customer 10 gate: {target_10 - paying} paying customer(s) to go")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    store = load_store()
    c = find_customer(store, args.customer_id)
    print(json.dumps(c, indent=2))
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    store = load_store()
    c = find_customer(store, args.customer_id)
    if args.status:
        if args.status not in VALID_STATUSES:
            sys.exit(f"ERROR: status must be one of {sorted(VALID_STATUSES)}")
        c["status"] = args.status
    if args.tier:
        c["tier"] = normalize_tier(args.tier)
    if args.app_url:
        c["app_url"] = args.app_url
    if args.app_name:
        c["app_name"] = args.app_name
    if args.platform:
        c["platform"] = args.platform
    if args.notion_report_url:
        c["notion_report_url"] = args.notion_report_url
    if args.notion_page_id:
        c["notion_page_id"] = args.notion_page_id
    if args.stripe_payment_id:
        c["stripe_payment_id"] = args.stripe_payment_id
    if args.referral_code:
        c["referral_code"] = args.referral_code
    if args.useful_rating:
        c["useful_rating"] = args.useful_rating
    if args.notes is not None:
        c["notes"] = args.notes
    c["updated_at"] = utc_now_iso()
    save_store(store)
    print(f"Updated {args.customer_id}")
    return 0


def cmd_mark_intake(args: argparse.Namespace) -> int:
    store = load_store()
    c = find_customer(store, args.customer_id)
    c["intake_received"] = True
    c["intake_received_at"] = utc_now_iso()
    if c.get("status") == "paid":
        c["status"] = "intake_received"
    c["updated_at"] = utc_now_iso()
    save_store(store)
    print(f"Marked intake received: {args.customer_id}")
    return 0


def cmd_mark_delivered(args: argparse.Namespace) -> int:
    store = load_store()
    c = find_customer(store, args.customer_id)
    c["status"] = "delivered"
    c["delivered_at"] = utc_now_iso()
    if args.notion_report_url:
        c["notion_report_url"] = args.notion_report_url
    c["updated_at"] = utc_now_iso()
    save_store(store)
    print(f"Marked delivered: {args.customer_id}")
    return 0


def cmd_acknowledge_milestone_10(_: argparse.Namespace) -> int:
    store = load_store()
    cfg = load_milestones_config()
    target_10 = cfg.get("goals", {}).get("paying_customers_automation_unlock", 10)
    paying = counts_paying(store, cfg)
    if paying < target_10:
        sys.exit(f"ERROR: only {paying} paying customers — need {target_10} before acknowledging")
    store.setdefault("milestones", {})
    store["milestones"]["customer_10_unlock_acknowledged"] = True
    store["milestones"]["customer_10_unlocked_at"] = utc_now_iso()
    save_store(store)
    print("Customer 10 milestone acknowledged.")
    print("Next: docs/CUSTOMER-10-RUNBOOK.md")
    return 0


def cmd_export_csv(_: argparse.Namespace) -> int:
    store = load_store()
    rows = store.get("customers", [])
    fields = [
        "id",
        "name",
        "email",
        "app_url",
        "app_name",
        "platform",
        "tier",
        "status",
        "payment_date",
        "intake_received",
        "delivery_due",
        "delivered_at",
        "notion_report_url",
        "referral_code",
        "followup_d3_sent",
        "feedback_received",
        "useful_rating",
        "notes",
    ]
    with EXPORT_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for c in rows:
            w.writerow({k: c.get(k, "") for k in fields})
    print(f"Wrote {EXPORT_CSV_PATH} ({len(rows)} rows)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create data/customers.json from example").set_defaults(func=cmd_init)

    add = sub.add_parser("add", help="Register a new paying customer")
    add.add_argument("--name", required=True)
    add.add_argument("--email", required=True)
    add.add_argument("--app-url", required=True)
    add.add_argument("--tier", required=True, help="starter or full")
    add.add_argument("--payment-date", help="YYYY-MM-DD (default: today)")
    add.add_argument("--app-name")
    add.add_argument("--platform", help="Lovable, Bolt, etc.")
    add.add_argument("--stripe-payment-id")
    add.add_argument("--notes")
    add.set_defaults(func=cmd_add)

    lst = sub.add_parser("list", help="List customers")
    lst.add_argument("--status", choices=sorted(VALID_STATUSES))
    lst.set_defaults(func=cmd_list)

    sub.add_parser("stats", help="Paying count + milestone progress").set_defaults(func=cmd_stats)

    show = sub.add_parser("show", help="JSON for one customer")
    show.add_argument("customer_id")
    show.set_defaults(func=cmd_show)

    upd = sub.add_parser("update", help="Update fields on a customer")
    upd.add_argument("customer_id")
    upd.add_argument("--status", choices=sorted(VALID_STATUSES))
    upd.add_argument("--tier")
    upd.add_argument("--app-url")
    upd.add_argument("--app-name")
    upd.add_argument("--platform")
    upd.add_argument("--notion-report-url")
    upd.add_argument("--notion-page-id")
    upd.add_argument("--stripe-payment-id")
    upd.add_argument("--referral-code")
    upd.add_argument("--useful-rating")
    upd.add_argument("--notes")
    upd.set_defaults(func=cmd_update)

    mi = sub.add_parser("mark-intake", help="Intake form received")
    mi.add_argument("customer_id")
    mi.set_defaults(func=cmd_mark_intake)

    md = sub.add_parser("mark-delivered", help="Report sent")
    md.add_argument("customer_id")
    md.add_argument("--notion-report-url")
    md.set_defaults(func=cmd_mark_delivered)

    sub.add_parser("acknowledge-milestone-10", help="Record that you read the customer-10 runbook").set_defaults(
        func=cmd_acknowledge_milestone_10
    )

    sub.add_parser("export-csv", help="Write data/customers-export.csv").set_defaults(func=cmd_export_csv)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
