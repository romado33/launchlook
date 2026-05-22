# Customer / subscriber tracking

LaunchLook uses **paying customers** (one-time purchases), not recurring subscriptions. This doc covers how to track them from first payment through delivery and milestones.

## Two layers (use both)

| Layer | Purpose | Where |
|-------|---------|--------|
| **Local tracker** | Fast CLI, milestone count, private JSON on your machine | `data/customers.json` + `scripts/customers_track.py` |
| **Notion Customers** | Reports, team view, Tally integration | Notion **LaunchLook Ops** — import [`templates/notion/customers-db.csv`](../templates/notion/customers-db.csv) |

**Rule:** When Stripe shows a new payment, add the row locally **and** in Notion (or Tally → Notion if wired). Run `customers_track.py stats` weekly.

---

## Setup (once)

```powershell
cd c:\Users\RobDods\Apps\Cursor\onceover
python -m venv .venv
.venv\Scripts\activate
pip install -e .

python scripts/customers_track.py init
```

Creates `data/customers.json` (gitignored — never commit real emails).

---

## Lifecycle statuses

| Status | Meaning |
|--------|---------|
| `lead` | Interested, not paid |
| `paid` | Stripe payment received, intake not yet in |
| `intake_received` | Tally (or email) intake complete |
| `auditing` | You're actively writing the report |
| `delivered` | Notion report link sent |
| `refunded` | Excluded from paying-customer milestone count |

---

## Daily workflow

### 1. New payment (Stripe email / dashboard)

```bash
python scripts/customers_track.py add \
  --name "Sam" \
  --email "sam@founder.com" \
  --tier starter \
  --app-url "https://their-app.vercel.app" \
  --platform Lovable \
  --stripe-payment-id "pi_xxx"
```

Also create a Notion **Customers** row with the same fields.

### 2. Intake received (Tally email)

```bash
python scripts/customers_track.py mark-intake cust_20260522_a1b2c3
python scripts/customers_track.py update cust_20260522_a1b2c3 --status auditing
```

### 3. Report delivered

```bash
python scripts/customers_track.py mark-delivered cust_20260522_a1b2c3 \
  --notion-report-url "https://notion.so/..."
```

Then send [`templates/email/delivery.txt`](../templates/email/delivery.txt).

### 4. Referral code

```bash
python scripts/referral_create.py --first-name Sam --email sam@founder.com
python scripts/customers_track.py update cust_... --referral-code SAM5
```

### 5. Check progress

```bash
python scripts/customers_track.py stats
python scripts/customers_track.py list
python scripts/customers_track.py list --status delivered
```

---

## Milestones (`data/milestones.json`)

| Count | Meaning |
|-------|---------|
| **8 paying** | 60-day success target ([`00-START-HERE.md`](00-START-HERE.md)) |
| **10 paying** | **Unlock automation** — BL-14 crawler + BL-15 Notion pre-fill ([`CUSTOMER-10-RUNBOOK.md`](CUSTOMER-10-RUNBOOK.md)) |
| **30 paying** | Earliest consideration for self-serve scan UI (explicitly deferred) |

**Paying customer** = has `payment_date` and status is not `lead` or `refunded`.

When `stats` shows 10/10:

```bash
python scripts/customers_track.py acknowledge-milestone-10
```

Then follow the customer-10 runbook before writing crawler code.

---

## Notion column mapping

Import CSV, then align property names:

| Local / CLI field | Notion property |
|-------------------|-----------------|
| `name` | Name |
| `email` | Email |
| `app_url` | App URL |
| `tier` | Tier (Starter Package $9 / Full Package $29) |
| `payment_date` | Payment Date |
| `intake_received` | Intake Received |
| `delivery_due` | Delivery Due |
| `delivered_at` | Delivered (checkbox or date) |
| `notion_report_url` | Notes or Report URL column |
| `referral_code` | Referral Code |
| `status` | Notes prefix or add Status select |

Tally-only fields (anxiety, test accounts) → **Notes** until you add columns.

---

## Export

```bash
python scripts/customers_track.py export-csv
```

Writes `data/customers-export.csv` (gitignored) for backup or Sheets import.

---

## What we are not building yet

- Supabase / Postgres CRM
- Customer login dashboard
- Stripe webhook → auto-insert (optional later; manual `add` is fine for customer 1–10)

See [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) for go-live blockers.
