# Notion templates

Files Rob imports into Notion to set up the **LaunchLook Ops** workspace (BL-03).

**Owner checklist:** [`docs/ROB-REMAINING-TODO.md`](../../docs/ROB-REMAINING-TODO.md) · **CLI tracker:** [`docs/CUSTOMER-TRACKING.md`](../../docs/CUSTOMER-TRACKING.md) · **Tally → Customers:** [`docs/TALLY-COPY-PASTE.md`](../../docs/TALLY-COPY-PASTE.md)

## Order of setup

1. Create a new Notion workspace called **LaunchLook Ops** (free tier is fine).
2. Inside it, create these as **full-page databases**:
   - `Customers` — import `customers-db.csv`
   - `Outreach Tracker` — import `outreach-db.csv`
   - `Findings Library` — import `../../findings_library/findings.csv`
3. Create a top-level page called **Report Templates**. Inside it, create three sub-pages — see **`REPORT-TEMPLATES-SETUP.md`** for the mapping:
   - `Template — Starter Package` ← `report-quick-checkup.md` ($19, up to 10 findings)
   - `Template — Scale Up Package` ← `report-launch-pack.md` ($49, up to 30; was "Full Package")
   - `Template — Pro Package` ← `report-pro-package.md` ($99, up to 40 + integrations + Loom + Handoff)
   - *(Optional)* `Template — Polish add-on` ← `report-polish.md` — legacy follow-up only; not on the current ladder.
4. Create a page called **Crawler Wishlist** (from `crawler-wishlist.md`).
5. Mark each report template page as a **Notion Template** so duplicating is one click per customer.

## How to import a Markdown template into Notion

Notion natively supports Markdown import on page creation:

1. New page → top of the page, click **Import** → **Markdown & CSV**
2. Drag the `.md` file in
3. Notion preserves headings, bullets, code blocks, dividers. You'll want to manually:
   - Convert finding sections (`## Finding 1 — ...`) into Notion toggle blocks for cleaner navigation
   - Make screenshot placeholder boxes into actual image upload zones
   - Color-code severity badges using Notion's color callouts

## Column type adjustments after CSV import

### Customers database

| Column | Notion type | Notes |
|--------|-------------|-------|
| Name | Title | The row title |
| Email | Email | |
| App URL | URL | |
| Platform | Select | Lovable / Bolt / Base44 / Replit / v0 / Cursor / Webflow / Other (drives whether the row routes to the vibe-coder or Webflow audit pipeline) |
| Tier | Select | Starter Package / Scale Up Package / Pro Package (legacy values still in DB: Full Package, Quick Checkup, Launch Pack, Polish) |
| Payment Date | Date | |
| Intake Received | Checkbox | |
| Delivery Due | Date | Formula: Payment Date + tier turnaround (typically within 48h of intake; often faster) |
| Delivered | Checkbox | |
| Follow-up Sent | Checkbox | Day-3 automation flips this |
| Feedback Received | Text | |
| Useful Rating | Select | Very useful / Useful / Mixed / Not useful / No response |
| Referral Code | Text | |
| Referrals | Number | Count of times code was used |
| Notes | Text | |

### Outreach Tracker

| Column | Notion type | Notes |
|--------|-------------|-------|
| Prospect | Title | Founder name or handle |
| App URL | URL | |
| Channel | Select | Lovable Discord / Bolt Discord / Twitter / Reddit / Product Hunt / Other |
| Date Sent | Date | |
| Loom URL | URL | |
| Opened | Checkbox | Loom analytics |
| Replied | Checkbox | |
| Paid | Checkbox | Converted to customer |
| Notes | Text | |

## What to share with the Notion integration (BL-04)

Before delivering any report, skim `templates/report-voice-guide.md` — findings use plain language; fix prompts can be technical.

When Rob creates the Notion integration token (`secret_...`), he must explicitly **share** each of these databases with the integration via the `Share` button:

- Customers
- Findings Library
- Outreach Tracker
- Report Templates (parent page — children inherit access)

Without this, the API gets `object_not_found` errors.
