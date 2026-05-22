# LaunchLook — Start Here

## What this is

LaunchLook is a manual service (with growing automation) that gives non-technical founders a friendly pre-launch checkup of their vibe-coded apps. The founder pays (Starter Package $9 or Ship Package $29), sends a URL, and gets back:

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

## Current status (as of project handoff)

- ✅ Product strategy defined (see `02-strategy-and-context.md`)
- ✅ Pricing locked: **$9 Starter** / **$29 Launch** (two tiers; follow-up re-scan on request)
- ✅ Name locked: LaunchLook
- ✅ Findings library seeded with 35 entries (see `06-findings-library.md`)
- ✅ Quick Start Guide prompt drafted (see `05-technical-architecture.md`)
- ✅ Free public checklist drafted (see `04-content-and-copy.md`)
- ✅ Domain purchased: **launchlook.app**
- ✅ Landing page built (deploy to Vercel when ready — see `07-launchlook-go-live.md`)
- ✅ Rebrand complete: Onceover → LaunchLook in repo
- ❌ Stripe payment links not yet set up
- ❌ Notion workspace not yet set up
- ❌ Zero paying customers yet
- ❌ Playwright crawler not yet built (deliberately — not until customer 10)

## Constraints

- Owner has 5 hours/week to spend on this project.
- Owner is Rob, a senior technical writer at TrueContext with 15 years of experience in technical writing, REST API documentation, AI-readiness for content, MadCap Flare, and Claude Code workflows.
- Owner is fluent in Spanish (potentially useful for v1 internationalization, but not relevant to MVP).
- Owner has solid Claude Code skills. Python/Playwright is acceptable tech stack.

## 60-day success criteria

- **8 paying customers minimum** (mix of Starter Package $9 and Ship Package $29)
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

## What Rob should do (in parallel)

1. Buy the domain.
2. Audit 5 real vibe-coded apps manually this weekend (see `03-build-queue.md` item BL-01).
3. Send 5 cold outreach Looms.
4. Participate in Lovable Discord daily.
5. Track every customer interaction in a Google Sheet (template in `04-content-and-copy.md`).

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
