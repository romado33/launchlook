# Everything left for Rob — LaunchLook

**Last updated:** May 2026  
**Site:** https://launchlook.app · **Repo:** `romado33/launchlook`

Use this as your single owner checklist. Code/deploy items below marked ✅ are already in GitHub unless noted.

**Doc index:** [`docs/README.md`](README.md) · **Tally paste file:** [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md)

---

## Already done (don’t redo)

- [x] Landing site live (Vercel, clean URLs, security headers)
- [x] Starter Package **$9** / Full Package **$29** on homepage; Stripe **public** links in `landing/assets/config.js`
- [x] Privacy, terms, sample report, free checklist, OG/logo (Option A)
- [x] Report templates + plain-language voice guide for customers
- [x] Findings library (35 entries) in repo
- [x] Public checklist repo linked from footer
- [x] Simplified free checklist (`/checklist`) + extended README on GitHub
- [x] LinkedIn in `config.js` + footer + Who's behind section
- [x] Site-wide email via `supportEmail` + thanks intake mailto fallback
- [x] Homepage: free checklist band, share/referral FAQ, honest proof section
- [x] Delivery email + Notion reports: share lines, quote ask, referral
- [x] [`SHARE-AND-REVIEWS.md`](SHARE-AND-REVIEWS.md) growth playbook

---

## 🔴 Blocking — before cold outreach

Do these in order. Nothing else on the site matters until the pay → intake → you-get-notified loop works.

### 1. Tally intake form (~30–45 min)

**Paste every block from:** [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md)  
**Checkbox walkthrough:** [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md) · Spec: [`templates/intake-form-spec.md`](../templates/intake-form-spec.md)

- [ ] Create form at [tally.so](https://tally.so) — paste Block 0 + Questions 1–15 from **TALLY-COPY-PASTE.md**
- [ ] Set conditionals (Q9–Q12 Full only; Q10–Q11 when “Yes — I'll provide two test accounts”)
- [ ] Paste thank-you page + enable email to **hello@launchlook.app**
- [ ] (Optional) Tally → Notion **Customers**
- [ ] Publish → copy URL → `landing/assets/config.js` → `intakeFormUrl` → push (or send URL to Cursor)

### 2. Stripe Payment Links (~15 min)

Dashboard: [dashboard.stripe.com](https://dashboard.stripe.com) → **Payment Links** (live mode when ready)

- [ ] Exactly **two** links: $9 Starter, $29 Full (names in Stripe can differ)
- [ ] **Success URL** on both: `https://launchlook.app/thanks`
- [ ] Cancel URL (if offered): `https://launchlook.app/#pricing`
- [ ] Confirm URLs still match `config.js` (`stripe.starter`, `stripe.launch`)

### 3. Email receiving (~15–30 min)

Site and templates use **hello@launchlook.app** (matches launchlook.app). If you set up a different address, align DNS + Tally notifications + `supportEmail` in `config.js`.

- [ ] **hello@launchlook.app** forwards to an inbox you actually check (ImprovMX, GoDaddy forward, or Google Workspace)
- [ ] Send a test email from another account and confirm delivery
- [ ] Tally test submission arrives at that inbox

### 4. End-to-end payment test (~20 min)

Use **incognito** on desktop and once on your **phone**. Detail: [`07-launchlook-go-live.md`](07-launchlook-go-live.md) §8.

**Starter ($9)**

- [ ] Click **Get Starter Package — $9** → Stripe opens
- [ ] Complete payment (test or live)
- [ ] Land on `https://launchlook.app/thanks` (not 404)
- [ ] Intake opens **Tally** (not only mailto)
- [ ] Submit test intake → you receive it at hello@launchlook.app
- [ ] Form only asks safe fields; security checkbox required

**Full ($29)**

- [ ] Same flow for **Get Full Package — $29**
- [ ] Full Package shows test-account questions when selected

**Quick URL check**

- [ ] `/`, `/sample`, `/thanks`, `/checklist`, `/privacy`, `/terms` → all 200
- [ ] Footer **GitHub** link works
- [ ] Hard-refresh homepage after last deploy (Ctrl+Shift+R)

---

## 🟠 Important — first paying customer delivery

### 5. Notion ops workspace

Guide: [`03-build-queue.md`](03-build-queue.md) BL-03, BL-08 · Templates: [`templates/notion/`](../templates/notion/)

- [ ] Workspace **LaunchLook Ops**
- [ ] Databases: **Customers**, **Findings Library** (import/sync from `findings_library/`), **Outreach Tracker**
- [ ] Duplicate report templates into Notion:
  - Starter → `templates/notion/report-quick-checkup.md`
  - Full → `templates/notion/report-launch-pack.md`
- [ ] Before each delivery: read [`templates/report-voice-guide.md`](../templates/report-voice-guide.md) (plain English for founders)

### 6. Delivering a checkup (manual workflow)

- [ ] Audit pass: [`templates/manual-audit-checklist.md`](../templates/manual-audit-checklist.md) (~15 min)
- [ ] Fill Notion report; paste fix prompts from `findings_library/findings.json`
- [ ] Starter: include Quick Start Guide (prompt in `prompts/`, architecture in `05-technical-architecture.md`)
- [ ] Email customer: [`templates/email/delivery.txt`](../templates/email/delivery.txt) (includes quote + share asks)
- [ ] Optional 48h later: [`templates/email/ask-for-quote.txt`](../templates/email/ask-for-quote.txt)

### 7. Resend (welcome / delivery automation)

- [ ] [resend.com](https://resend.com) — verify domain **launchlook.app**
- [ ] `.env` (never commit): `RESEND_API_KEY`, `FROM_EMAIL=hello@launchlook.app`, `ADMIN_EMAIL=…`
- [ ] Test welcome email after purchase ([`templates/email/welcome.txt`](../templates/email/welcome.txt))
- [ ] Optional: wire Stripe webhook or manual send for week 1

### 8. Vercel dashboard sanity check (5 min)

- [ ] Project **Root Directory** = empty (repo root), **not** `landing`
- [ ] Build: `node scripts/copy-landing-for-vercel.mjs` · Output: `dist`
- [ ] Production branch: `main`

---

## 🟡 Optional — trust & polish

- [x] **LinkedIn** on homepage (Who's behind + footer)
- [ ] Paste `https://launchlook.app/` in Slack/iMessage — confirm OG image looks right
- [ ] Rename Stripe **product** display names to Starter Package / Full Package (cosmetic)
- [ ] Notion API token + share DBs with integration ([`03-build-queue.md`](03-build-queue.md) BL-04) — for scripts later
- [ ] Stripe webhook → email you on purchase (optional MVP)
- [ ] Sync [`external/launchlook-prelaunch-checklist`](../external/launchlook-prelaunch-checklist) if you changed checklist copy locally

---

## 🟢 Shmoozing — when §1–4 are green

Goal: **3 strangers pay $9** — then stop polishing the site.

- [ ] Read: [`SHARE-AND-REVIEWS.md`](SHARE-AND-REVIEWS.md) (weekly rhythm + what to link)
- [ ] Script: [`templates/cold-outreach-loom-script.md`](../templates/cold-outreach-loom-script.md)
- [ ] Free sample playbook: [`templates/week-1-free-sample-playbook.md`](../templates/week-1-free-sample-playbook.md)
- [ ] Track prospects in Notion **Outreach Tracker**
- [ ] **30** targeted DMs/Looms (quality over volume)
- [ ] Offer $9 Starter first; upsell Full when they’re launching this week

---

## 60-day targets (reminder)

From [`00-START-HERE.md`](00-START-HERE.md):

| Target | Number |
|--------|--------|
| Paying customers | **8+** (mix $9 / $29) |
| “Useful” or better | **6 of 8** |
| Referrals | **2+** |

---

## Quick reference

| Item | Value |
|------|--------|
| Domain | launchlook.app |
| Support | hello@launchlook.app |
| Tiers | Starter Package **$9**, Full Package **$29** |
| Config file | `landing/assets/config.js` |
| Go-live detail | [`07-launchlook-go-live.md`](07-launchlook-go-live.md) |
| Security posture | [`08-launchlook-security.md`](08-launchlook-security.md) |
| Tally copy-paste | [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md) |
| `intakeFormUrl` in repo | **Empty until you publish Tally** |

---

## What to send Cursor (one message)

When Tally is ready:

> Tally URL: `https://tally.so/r/________` — wire `intakeFormUrl` and push.

If email inbox is confirmed working, say so and we can note it in this file.

---


*When this file is mostly checked off, you’re in outreach mode — not “one more site tweak” mode.*
