# LaunchLook documentation index

Read in order for full context, or jump to what you need.

## Start here

| Doc | Who | Purpose |
|-----|-----|---------|
| [`00-START-HERE.md`](00-START-HERE.md) | Everyone | Product summary, status, constraints |
| [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) | **Rob** | **Single owner checklist — what's left** |
| [`07-launchlook-go-live.md`](07-launchlook-go-live.md) | Rob | Deploy, Stripe, Tally, E2E smoke test |

## Build the business

| Doc | Purpose |
|-----|---------|
| [`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt) | **Manual Tally editor** — all fields + thank-you (`>>> PASTE START`) |
| [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md) | Build checklist |
| [`SHARE-AND-REVIEWS.md`](SHARE-AND-REVIEWS.md) | Share links, quotes, weekly outreach rhythm |
| [`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md) | Paying customer tracker (CLI + Notion) |
| [`CUSTOMER-10-RUNBOOK.md`](CUSTOMER-10-RUNBOOK.md) | What to do at 10 paying customers (BL-14/15) |
| [`01-product-spec.md`](01-product-spec.md) | Tiers, deliverables, positioning |
| [`02-strategy-and-context.md`](02-strategy-and-context.md) | Why manual-first, competitive context |
| [`03-build-queue.md`](03-build-queue.md) | BL-XX tickets and gates |
| [`04-content-and-copy.md`](04-content-and-copy.md) | Homepage copy, outreach, Notion schemas |

## Technical

| Doc | Purpose |
|-----|---------|
| [`05-technical-architecture.md`](05-technical-architecture.md) | Scripts, QSG pipeline, env vars |
| [`06-findings-library.md`](06-findings-library.md) | Finding categories and maintenance |
| [`08-launchlook-security.md`](08-launchlook-security.md) | CSP, headers, config safety |

## Templates (outside `docs/`)

| Path | Purpose |
|------|---------|
| [`templates/intake-form-spec.md`](../templates/intake-form-spec.md) | Intake BL-07 spec |
| [`templates/email/`](../templates/email/) | Welcome, delivery, follow-ups |
| [`templates/notion/`](../templates/notion/) | Report templates, Customers CSV |
| [`templates/manual-audit-checklist.md`](../templates/manual-audit-checklist.md) | Rob's ~15 min audit pass |
| [`templates/cold-outreach-loom-script.md`](../templates/cold-outreach-loom-script.md) | Week 1 Loom + DM |

## Repo status (code vs Rob)

| Done in repo | Still on Rob |
|--------------|--------------|
| Landing site, checklist, sample, security headers | Publish Tally + `intakeFormUrl` |
| Stripe link URLs in `config.js` | Stripe success URLs in dashboard |
| LinkedIn, email wiring, growth templates | Confirm `hello@launchlook.app` receives mail |
| `customers_track.py` + milestone config | Run `customers_track.py init` locally |
| Customer 10 runbook (BL-14/15 prep) | Notion ops workspace |
| | E2E pay → thanks → intake |
| | First paying customers + outreach |

Always treat [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) as the live owner checklist.
