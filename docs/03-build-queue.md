# LaunchLook — Build Queue

This is the prioritized list of things to build. Items are ordered by dependency and impact. Do not skip ahead.

Each item has:
- **ID** for tracking
- **What to build**
- **Acceptance criteria** (when it's "done")
- **Who builds it** (Rob = manual/decision work; Cursor = code/setup)
- **Estimated effort**
- **Dependencies** (other IDs that must complete first)

## Phase 0 — Setup (days 1-3)

### BL-01 — Domain and infrastructure setup
- **What**: ~~Buy `launchlook.app`~~ ✅ Purchased. Set up DNS pointing to Vercel (landing host).
- **Acceptance**: Domain resolves to production landing (`launchlook.app`, optional `www` redirect).
- **Who**: Rob
- **Effort**: 30 minutes
- **Depends on**: nothing

### BL-02 — Stripe account and payment links
- **What**: Stripe account active. Three Payment Links created for Quick Checkup ($7), Launch Pack ($29), Launch Pack + Polish ($59). Webhook setup to forward purchase notifications to Rob's email.
- **Acceptance**: Test purchase completes end-to-end with Stripe test card. Webhook fires.
- **Who**: Rob (Cursor can help with webhook setup if needed)
- **Effort**: 1 hour
- **Depends on**: nothing

### BL-03 — Notion workspace setup
- **What**: Create Notion workspace `LaunchLook Ops`. Inside it:
  - `Customers` database (name, email, app URL, tier, payment date, delivery date, status, follow-up status, referral code, notes)
  - `Findings Library` database (seeded from `06-findings-library.md`)
  - `Report Templates` page (one for each tier — Cursor builds these in BL-08)
  - `Outreach Tracker` database (prospect name, app URL, channel, sent date, opened, replied, paid, notes)
  - `Crawler Wishlist` page (running notes during manual audits)
- **Acceptance**: All databases exist with correct schema. Findings Library has 35 entries from `06-findings-library.md`.
- **Who**: Cursor (Rob reviews)
- **Effort**: 2 hours
- **Depends on**: BL-01

### BL-04 — Notion API integration setup
- **What**: Create a Notion integration token. Share the three core databases (Customers, Findings Library, Outreach Tracker) with the integration. Store token securely (1Password or env var, never committed).
- **Acceptance**: Can run a Python script that reads from Customers database via Notion API.
- **Who**: Cursor (Rob provides token)
- **Effort**: 30 minutes
- **Depends on**: BL-03

## Phase 1 — Landing page and copy (days 3-5)

### BL-05 — Landing page (single page, no JS framework)
- **What**: Single-page HTML/Tailwind landing page deployed to Vercel or Cloudflare Pages. Sections:
  - Hero with tagline and three-tier pricing
  - "What we check" section (Polish / Placeholders / Sharing Risks / Quick Start Guide)
  - Sample report screenshot (placeholder until real sample exists)
  - Three pricing cards with Stripe Payment Link CTAs
  - FAQ section
  - Footer with `/checklist` and contact email
- **Acceptance**:
  - Lighthouse Performance score >85
  - Mobile-responsive (no horizontal scroll at 375px)
  - All three Stripe links functional
  - Loads in <2 seconds
  - Uses copy from `04-content-and-copy.md` verbatim
- **Who**: Cursor (Rob reviews copy)
- **Effort**: 4 hours
- **Depends on**: BL-01, BL-02

### BL-06 — `/checklist` page with the free public checklist
- **What**: A second route on the landing site at `/checklist` hosting the free Pre-Launch Checkup checklist. Same styling as main site. Includes a CTA at the bottom: "Want help running this? LaunchLook does it for $7."
- **Acceptance**: Page loads, mobile-responsive, full checklist visible, CTA links to home pricing.
- **Who**: Cursor (Rob reviews copy)
- **Effort**: 1 hour
- **Depends on**: BL-05

### BL-07 — Intake form
- **What**: A simple form (Tally.so or Google Forms — not custom code) that captures the data needed for an audit. Linked from Stripe success page. Fields per `04-content-and-copy.md` intake spec.
- **Acceptance**: Form submission emails Rob the responses and optionally writes to Notion Customers database (via Zapier/Make or Notion API).
- **Who**: Cursor (Rob configures)
- **Effort**: 1 hour
- **Depends on**: BL-03

## Phase 2 — Report templates and Quick Start Guide pipeline (days 5-10)

### BL-08 — Notion report templates
- **What**: Three master Notion templates Rob duplicates per customer:
  - `Template — Quick Checkup` (5-7 findings structure)
  - `Template — Launch Pack` (full findings + Quick Start Guide section)
  - `Template — Launch Pack + Polish` (full + follow-up section)
- Each template includes:
  - Cover section (customer name, app, date, summary verdict)
  - Severity legend
  - Findings sections (Critical / High / Medium / Low)
  - Standard finding structure (screenshot → explanation → why it matters → fix prompt)
  - "What's next" closing
  - Referral footer (with `{REFERRAL_CODE}` placeholder)
- **Acceptance**: Rob can duplicate a template, fill in 5 findings, and deliver to a customer in under 25 minutes.
- **Who**: Cursor (initial templates) + Rob (fills with sample content to test)
- **Effort**: 3 hours
- **Depends on**: BL-03

### BL-09 — Quick Start Guide generation script
- **What**: A Python script that:
  1. Takes inputs: app URL, intake form responses, support email
  2. Crawls the URL with Playwright to capture: homepage text, post-signup text (if test credentials provided), visible nav labels, visible CTAs
  3. Calls Claude API with the system prompt from `05-technical-architecture.md`
  4. Outputs a Markdown file ready for Rob's editing pass
- **Acceptance**:
  - Script runs from CLI: `python qsg.py <url> <intake_json>`
  - Produces clean Markdown in `output/<customer>/quickstart.md`
  - No marketing words in output (verified by post-process check)
  - Total runtime under 90 seconds
- **Who**: Cursor
- **Effort**: 4-6 hours
- **Depends on**: BL-03, anthropic API key in env

### BL-10 — Quick Start Guide → HTML rendering
- **What**: A second script that takes the Markdown QSG and renders it as a styled HTML page using a simple Tailwind template. Output is a single self-contained HTML file the customer can host or embed.
- **Acceptance**: Markdown in, HTML out. HTML file under 50KB, mobile-responsive, uses customer-provided primary color if supplied.
- **Who**: Cursor
- **Effort**: 2 hours
- **Depends on**: BL-09

## Phase 3 — Outreach tooling (days 5-10, parallel to Phase 2)

### BL-11 — Loom outreach tracker integration
- **What**: A Google Sheet or Notion database template Rob fills in per outreach attempt. Columns: prospect name, app URL, channel, Loom URL, sent date, opened (Loom analytics), replied (Y/N), paid (Y/N), notes.
- **Acceptance**: Rob can log a new outreach in under 60 seconds.
- **Who**: Cursor (template) + Rob (use)
- **Effort**: 30 minutes
- **Depends on**: BL-03

### BL-12 — Referral code generator
- **What**: A script that creates a Stripe coupon code per customer and writes it to the Customers database in Notion. Pattern: `{FIRST_NAME}5` or randomized if name collides.
- **Acceptance**: Given a customer first name, script creates a Stripe coupon and stores it on the customer record.
- **Who**: Cursor
- **Effort**: 1 hour
- **Depends on**: BL-02, BL-03

### BL-13 — Day-3 follow-up email automation
- **What**: A scheduled script (cron, GitHub Actions, or Zapier) that checks the Customers database daily, finds customers whose delivery date was 3 days ago, and sends the day-3 follow-up email template from `04-content-and-copy.md` with their referral code filled in.
- **Acceptance**: Email sends automatically. Customer record marked `follow-up sent` after sending.
- **Who**: Cursor
- **Effort**: 2 hours
- **Depends on**: BL-12

## Phase 4 — Light scanner (defer until customer 10)

### BL-14 — Playwright crawler v0.1
- **What**: The Python crawler skeleton from `05-technical-architecture.md`. Single command: `python crawler.py <url>`. Outputs JSON of raw observations (screenshots, console errors, network failures, links, buttons, placeholder pattern matches, trust page status, logged-out access checks).
- **Acceptance**:
  - Runs against any URL without modification
  - Outputs valid JSON
  - Captures screenshots in both 1920px and 375px viewports
  - Detects all placeholder patterns from `06-findings-library.md`
  - Checks all trust pages and protected routes
- **Who**: Cursor
- **Effort**: 6-8 hours
- **Depends on**: 10+ manual audits completed (Rob's gating)

### BL-15 — Crawler output → Notion finding ingestion
- **What**: A script that takes a crawler JSON output and a target Notion report page, and pre-populates findings sections based on matches in the Findings Library. Rob curates, edits, and adds qualitative findings on top.
- **Acceptance**:
  - JSON in, Notion page populated with severity-sorted findings
  - Every finding has its standard structure
  - Fix prompts pulled from Findings Library based on issue type and customer's platform
- **Who**: Cursor
- **Effort**: 4 hours
- **Depends on**: BL-14, BL-08

## Phase 5 — Open-source checklist publishing (day 7)

### BL-16 — GitHub repo for free checklist
- **What**: Create public GitHub repo `launchlook-prelaunch-checklist`. README is the full checklist (from `04-content-and-copy.md`). License: CC-BY or similar permissive. Link from LaunchLook footer.
- **Acceptance**: Repo public, README renders correctly, license file present, link from LaunchLook landing footer.
- **Who**: Cursor (Rob reviews)
- **Effort**: 30 minutes
- **Depends on**: BL-05

## Anti-queue: Things explicitly NOT to build

The following ideas may seem helpful but are out of scope until explicitly added:

- Customer login / dashboard — Notion link delivery is sufficient
- Custom report PDF export — Notion's built-in PDF export is fine
- Multi-language support — English only at MVP
- Mobile app — web only
- API for third parties — no
- Slack / Discord bot — no
- Browser extension — no
- Auto-fix feature — no, we give prompts only
- Anonymous public scanner — no, requires signup
- Self-serve scan UI — defer until customer 30 minimum
- A/B testing framework — no, manual tracking is fine
- Email marketing automation beyond follow-ups — no
- CRM — Notion is the CRM

If a feature isn't listed in BL-01 through BL-16, it's not in scope. If Cursor or Rob feels it's needed, document the case in `02-strategy-and-context.md` and explicitly add it to this queue with an ID before building.

## Sequencing summary

```
Day 1-3:    BL-01, BL-02, BL-03, BL-04
Day 3-5:    BL-05, BL-06, BL-07
Day 5-10:   BL-08, BL-09, BL-10, BL-11, BL-12, BL-13
Day 7:      BL-16 (publish checklist)
Day 30-40:  Customer 10 reached → unlock BL-14, BL-15
```

## Effort summary

| Phase | Effort (Cursor) | Effort (Rob) |
|-------|-----------------|--------------|
| Phase 0 — Setup | 2.5 hrs | 1.5 hrs |
| Phase 1 — Landing | 6 hrs | review only |
| Phase 2 — Templates + QSG | 9-11 hrs | review + iterate |
| Phase 3 — Outreach | 3.5 hrs | use daily |
| Phase 4 — Scanner | 10-12 hrs | gates on customer 10 |
| Phase 5 — Checklist | 30 min | review |

Total Cursor effort to MVP-ready: ~22-26 hours of focused work.
Total Rob effort at 5hrs/week: customer work, not building.
