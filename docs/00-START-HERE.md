# LaunchLook — Start Here

## What this is

LaunchLook is a manual service (with growing automation) that gives non-technical founders a friendly pre-launch checkup of their vibe-coded apps. The founder pays (Starter Package $9 or Full Package $29), sends a URL, and gets back:

- A Notion report with 5-10 findings (broken stuff, placeholder content, missing trust pages)
- Copy-paste fix prompts tailored to their AI builder
- (At higher tiers) An AI-generated Quick Start Guide they can give their users

The product solves the moment of pre-launch anxiety: "I'm about to share this with real users and I have no idea if it's ready."

## Who it's for

Non-technical founders who built an app with Lovable, Bolt, Base44, or Replit and are about to share it with real users for the first time. They are anxious, time-constrained, and don't know what they don't know. They are not developers and won't open a terminal.

## What it explicitly is not

- Not a security scanner. VAS, VibeEval, and Escape.tech compete in that space and would crush us on technical depth.
- Not a code audit service. Sherlock Forensics, Beesoul, and others do that at $1,500+ per audit.
- Not a documentation platform. CodeGuide and others target developer-facing docs.
- Not an automated SaaS yet. The product is currently a human service. Automation is being built in the background.

## Current status (May 2026)

**Owner checklist (what Rob still does):** [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md)  
**Doc index:** [`docs/README.md`](README.md)

### Done in repo / on site

- ✅ Product strategy (`02-strategy-and-context.md`)
- ✅ Pricing: **Starter Package $9** / **Full Package $29**
- ✅ Findings library (~35 entries, `06-findings-library.md`)
- ✅ Landing live: launchlook.app — clean URLs, security headers, sample, privacy/terms
- ✅ Free checklist: `/checklist` + GitHub mirror
- ✅ Stripe Payment Link URLs in `landing/assets/config.js`
- ✅ LinkedIn, site-wide `hello@launchlook.app`, growth email/report templates
- ✅ **Tally URLs in config:** intake `9qodVE`, post-intake thanks `Y5xO5J` ([`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) for editor paste)
- ✅ Landing CTAs: consistent button styling on homepage
- ✅ **Customer tracker CLI:** `scripts/customers_track.py` ([`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md))
- ✅ **Customer 10 runbook:** [`CUSTOMER-10-RUNBOOK.md`](CUSTOMER-10-RUNBOOK.md) (BL-14/15 gate)

### Still blocking launch / outreach

- ❌ Tally form **content** in dashboard (paste, conditionals, notifications, redirect to `Y5xO5J`) — URLs already on site
- ✅ Stripe checkout: $9 and $29 tested successfully → `/thanks`
- ❌ E2E: intake submit → Tally thanks `Y5xO5J` → email in inbox
- ❌ `hello@launchlook.app` confirmed receiving mail
- ❌ Notion **LaunchLook Ops** workspace (Customers, reports)
- ❌ `python scripts/customers_track.py init` run locally
- ❌ Zero paying customers yet
- ❌ Playwright crawler (deliberately after ~customer 10)

## Constraints

- Owner has 5 hours/week to spend on this project.
- Owner is Rob, a senior technical writer at TrueContext with 15 years of experience in technical writing, REST API documentation, AI-readiness for content, MadCap Flare, and Claude Code workflows.
- Owner is fluent in Spanish (potentially useful for v1 internationalization, but not relevant to MVP).
- Owner has solid Claude Code skills. Python/Playwright is acceptable tech stack.

## 60-day success criteria

- **8 paying customers minimum** (mix of Starter Package $9 and Full Package $29)
- **6 of 8 report the checkup as "useful" or better** on follow-up
- **At least 2 referrals from existing customers**

If hit: keep going, start light automation, raise prices.
If missed: the pitch or audience is wrong — iterate before building more.

## What Cursor should do

Read all docs in order. Then:

1. Confirm understanding before writing any code.
2. Focus on the build queue in `03-build-queue.md`, in order.
3. Do not skip ahead to the scanner, dashboard, or any user-facing automation. Those are deliberately deferred.
4. Prioritize: domain setup → landing page → Notion templates → Stripe → Quick Start Guide pipeline. In that order.

## What Rob should do (in order)

1. **Blocking:** [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md) §1–4 — finish Tally in dashboard (paste + redirect `Y5xO5J`), Stripe success URLs, confirm email, E2E test.
2. **Delivery:** Notion workspace + first customer report (`templates/notion/`, `manual-audit-checklist.md`).
3. **Outreach:** [`SHARE-AND-REVIEWS.md`](SHARE-AND-REVIEWS.md) + 5 Looms (`templates/cold-outreach-loom-script.md`) — lead with `launchlook.app/checklist`.
4. Track each payment: `python scripts/customers_track.py add ...` and mirror in Notion **Customers** ([`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md)).

## Anti-patterns to avoid

- Building automation before validating demand.
- Adding features that "would be cool" before the existing scope is shipped.
- Competing on security with VAS/VibeEval.
- Using marketing words like "leverage," "seamless," "robust" anywhere in product copy.
- Letting the technical work crowd out customer relationship work.
- Raising prices before customers say the product is worth more.
- Building a dashboard before there's something to put in it.

## Glossary

- **Vibe coder** — A non-technical person building software with AI tools like Lovable, Bolt, Base44, Replit, v0. The target customer.
- **Vibe-coded app** — A web application built primarily through AI prompting rather than hand-written code.
- **Checkup** — The core deliverable. A Notion report with findings and fix prompts.
- **Quick Start Guide** — A one-page user-facing doc generated for the customer's app, included in the $29+ tier.
- **Findings Library** — The Notion database of every issue type, with detection methods and fix prompts. Documented in `06-findings-library.md`.
