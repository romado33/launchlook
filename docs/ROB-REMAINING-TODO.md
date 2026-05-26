# Everything left for Rob â€” LaunchLook

**Last updated:** May 25, 2026  
**Site:** https://launchlook.app Â· **Repo:** `romado33/launchlook`

Use this as your single owner checklist. Code/deploy items below marked âœ… are already in GitHub unless noted.

### Your next 3 actions (in order)

1. **Tally** â€” Pick a form to use, then finish setup in Tally UI:
   - New rebuilt API form `QKOX1A` (DRAFT, May 25) â€” edit at https://tally.so/forms/QKOX1A/edit, **OR**
   - Existing form `9qodVE` (already wired into `config.js`)
   - Either way, in Tally UI: add Notifications â†’ `hello@launchlook.app`, After-submit redirect â†’ `https://tally.so/r/Y5xO5J`, and conditional logic for Q9â€“Q11 (Full Package only / "Yes" to test accounts). Click-by-click steps for `QKOX1A` are in Â§1 below.
2. **Tracker** â€” `python scripts/customers_track.py init` then `add` for your two test payments (or real ones).
3. **Notion ops** â€” LaunchLook Ops workspace so you can deliver the first real checkup.

**Doc index:** [`docs/README.md`](README.md) Â· **Tally paste file:** [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md)

---

## Already done (donâ€™t redo)

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
- [x] Paying-customer tracker: `scripts/customers_track.py` + [`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md)
- [x] Customer 10 prep: [`CUSTOMER-10-RUNBOOK.md`](CUSTOMER-10-RUNBOOK.md) + `data/milestones.json`
- [x] Tally URLs in `config.js`: intake `9qodVE`, post-intake thanks `Y5xO5J` (deployed)
- [x] Homepage CTAs use shared button styles (all primary actions look clickable)
- [x] Stripe checkout tested: **Starter $9** and **Full $29** both complete successfully (May 2026)

---

## ðŸ”´ Blocking â€” before cold outreach

Do these in order. Nothing else on the site matters until the pay â†’ intake â†’ you-get-notified loop works.

### 1. Tally intake form (~15â€“30 min)

**Two options now:**
- **(A) New API-built form `QKOX1A`** (DRAFT, rebuilt May 25). Edit: https://tally.so/forms/QKOX1A/edit Â· Preview: https://tally.so/r/QKOX1A
- **(B) Existing manual form `9qodVE`** (already wired into `config.js`)

The old API form `GxQkOL` has been **deleted and replaced by `QKOX1A`**. The rebuild fixes the previous problem where Tally's logic dropdown showed each question's help text instead of its title â€” each question is now a single TITLE block with the description inlined as a smaller second line, so the logic editor lists real question names.

**Paste references (only needed for option B):** [`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) Â· **Block guide:** [`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt) Â· **Setup steps:** [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md)

**To re-create or replace the form via API:**
- Fresh form: `python scripts/tally_create_intake.py`
- Replace an existing form (DELETE then POST): `python scripts/tally_create_intake.py --replace <FORM_ID>`

Both read `TALLY_API_KEY` from `.env`.

#### Conditional logic â€” how Tally actually works

Per Tally's docs, conditional show/hide is **not** a per-block menu item. The right-click on a question only has Delete / Duplicate / Hide / Turn into â€” that's why Q10 and Q11 didn't expose a "Logic" option. The flow is always:

1. **Hide the target question(s) by default.** Click the 6-dot drag handle (`â‹®â‹®`) at the left of the block â†’ **Hide**. Shortcut: `Ctrl+Shift+H`. Clicking the question's TITLE selects every block inside that group (input + options), so one Hide call hides the whole question.
2. **Add a `/logic` block upstream.** Place your cursor on a blank line above where the form should branch, type `/logic`, and pick **Conditional logic**.
3. **Configure the IF / THEN.** `IF <upstream question> = <option value>` â†’ action **Show blocks** â†’ pick the hidden question(s).

This pattern works for any block type, including TEXTAREA (so Q10 and Q11 don't need any special treatment).

#### Three rules to add in `QKOX1A`

In the editor (https://tally.so/forms/QKOX1A/edit), do these in order. The dropdown will now show each question by its TITLE (e.g. "Can we use test accounts?") instead of the old help text.

1. **Hide Q9, Q10, Q11 by default**
   - On Q9 (`Can we use test accounts?`): `â‹®â‹®` â†’ **Hide**
   - On Q10 (`Test account 1 â€” email and password`): `â‹®â‹®` â†’ **Hide**
   - On Q11 (`Test account 2 â€” email and password`): `â‹®â‹®` â†’ **Hide**

2. **Rule 1 â€” show Q9 only for Full Package buyers** (place this `/logic` block right after Q8)
   - Type `/logic` â†’ Conditional logic
   - IF `Which tier did you purchase?` **is** `Full Package ($29)`
   - THEN **Show blocks** â†’ select `Can we use test accounts?`

3. **Rule 2 â€” show Q10 when Q9 = Yes** (place this `/logic` block right after Q9)
   - Type `/logic` â†’ Conditional logic
   - IF `Can we use test accounts?` **is** `Yes â€” I'll provide two test accounts`
   - THEN **Show blocks** â†’ select `Test account 1 â€” email and password`

4. **Rule 3 â€” show Q11 when Q9 = Yes** (same `/logic` block as Rule 2, OR a second one right after Rule 2)
   - IF `Can we use test accounts?` **is** `Yes â€” I'll provide two test accounts`
   - THEN **Show blocks** â†’ select `Test account 2 â€” email and password`

Three rules total. There is no need to re-gate Q10/Q11 by Q8 â€” Q9 is already hidden unless Q8 = Full Package, so Q10/Q11 inherit that gate transitively (if Q9 is hidden, no one can answer "Yes" on it, so Q10/Q11 stay hidden).

#### Checklist

- [x] `intakeFormUrl` = `https://tally.so/r/9qodVE` in `config.js` (live on site)
- [x] `tallyThanksUrl` = `https://tally.so/r/Y5xO5J` in `config.js` (reference for redirect)
- [x] **Rebuilt API form `QKOX1A` created** (May 25, replaces `GxQkOL`) â€” 15 questions, no separate LABEL blocks, descriptions inlined into TITLEs
- [ ] **Pick one form** to keep; if switching to `QKOX1A`, update `intakeFormUrl` in `landing/assets/config.js`
- [ ] In Tally UI on the chosen form: hide Q9/Q10/Q11 + add the 3 `/logic` blocks above
- [ ] Thank-you message (paste from file) + **after submit redirect** â†’ `https://tally.so/r/Y5xO5J`
- [ ] Notifications â†’ **hello@launchlook.app** (all answers)
- [ ] Test Starter path (Q9â€“Q11 hidden) and Full path (Q9 visible; Q10/Q11 visible only after picking "Yes")
- [ ] If keeping `QKOX1A`: **Publish** it (currently DRAFT)
- [ ] (Optional) Tally â†’ Notion **Customers**

### 2. Stripe Payment Links (~15 min)

Dashboard: [dashboard.stripe.com](https://dashboard.stripe.com) â†’ **Payment Links** (live mode when ready)

- [x] Exactly **two** links: $9 Starter, $29 Full â€” both checkout successfully
- [x] Success URL returns customers to `/thanks` (verified via live test)
- [ ] Cancel URL (if offered): `https://launchlook.app/#pricing` (optional)
- [x] URLs match `config.js` (`stripe.starter`, `stripe.launch`)

### 3. Email receiving (~15â€“30 min)

Site and templates use **hello@launchlook.app** (matches launchlook.app). If you set up a different address, align DNS + Tally notifications + `supportEmail` in `config.js`.

- [ ] **hello@launchlook.app** forwards to an inbox you actually check (ImprovMX, GoDaddy forward, or Google Workspace)
- [ ] Send a test email from another account and confirm delivery
- [ ] Tally test submission arrives at that inbox

### 4. End-to-end payment test (~20 min)

Use **incognito** on desktop and once on your **phone**. Detail: [`07-launchlook-go-live.md`](07-launchlook-go-live.md) Â§8.

**Starter ($9)**

- [x] Click **Get Starter Package â€” $9** â†’ Stripe opens
- [x] Complete payment (live test May 2026)
- [x] Land on `https://launchlook.app/thanks` (not 404)
- [ ] Intake opens **Tally** (not only mailto)
- [ ] Submit test intake â†’ you receive it at hello@launchlook.app
- [ ] Form only asks safe fields; security checkbox required

**Full ($29)**

- [x] Same flow for **Get Full Package â€” $29** (live test May 2026)
- [ ] Full Package shows test-account questions when selected

**Quick URL check**

- [ ] `/`, `/sample`, `/thanks`, `/checklist`, `/privacy`, `/terms` â†’ all 200
- [ ] Footer **GitHub** link works
- [ ] Hard-refresh homepage after last deploy (Ctrl+Shift+R)

---

## ðŸŸ  Important â€” first paying customer delivery

### 5. Customer tracker (local â€” 2 min once)

Guide: [`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md)

- [ ] `python scripts/customers_track.py init` (creates gitignored `data/customers.json`)
- [ ] After each Stripe payment: `customers_track.py add ...`
- [ ] After intake: `mark-intake` Â· after report: `mark-delivered`
- [ ] Weekly: `customers_track.py stats` (progress toward 8 and **10** paying)
- [ ] **Weekly: AI margin check** â€” python scripts/ai_costs_report.py --summary --days 7 and confirm margin > 70%. Full playbook in [AI-COST-MONITORING.md](AI-COST-MONITORING.md). If margin dips, run --alert --days 7 to find the outlier(s).
- [ ] At **10 paying**: read [`CUSTOMER-10-RUNBOOK.md`](CUSTOMER-10-RUNBOOK.md) â†’ `acknowledge-milestone-10` â†’ start BL-14/15

### 6. Notion ops workspace

Guide: [`03-build-queue.md`](03-build-queue.md) BL-03, BL-08 Â· Templates: [`templates/notion/`](../templates/notion/)

- [ ] Workspace **LaunchLook Ops**
- [ ] Databases: **Customers**, **Findings Library** (import/sync from `findings_library/`), **Outreach Tracker**
- [ ] Duplicate report templates into Notion:
  - Starter â†’ `templates/notion/report-quick-checkup.md`
  - Full â†’ `templates/notion/report-launch-pack.md`
- [ ] Before each delivery: read [`templates/report-voice-guide.md`](../templates/report-voice-guide.md) (plain English for founders)

### 7. Delivering a checkup (manual workflow)

- [ ] Audit pass: [`templates/manual-audit-checklist.md`](../templates/manual-audit-checklist.md) (~15 min)
- [ ] Fill Notion report; paste fix prompts from `findings_library/findings.json`
- [ ] Starter: include Quick Start Guide (prompt in `prompts/`, architecture in `05-technical-architecture.md`)
- [ ] Email customer: [`templates/email/delivery.txt`](../templates/email/delivery.txt) (includes quote + share asks)
- [ ] Optional 48h later: [`templates/email/ask-for-quote.txt`](../templates/email/ask-for-quote.txt)

### 8. Resend (welcome / delivery automation)

- [ ] [resend.com](https://resend.com) â€” verify domain **launchlook.app**
- [ ] `.env` (never commit): `RESEND_API_KEY`, `FROM_EMAIL=hello@launchlook.app`, `ADMIN_EMAIL=â€¦`
- [ ] Test welcome email after purchase ([`templates/email/welcome.txt`](../templates/email/welcome.txt))
- [ ] Optional: wire Stripe webhook or manual send for week 1

### 9. Vercel dashboard sanity check (5 min)

- [ ] Project **Root Directory** = empty (repo root), **not** `landing`
- [ ] Build: `node scripts/copy-landing-for-vercel.mjs` Â· Output: `dist`
- [ ] Production branch: `main`

---

## ðŸŸ£ LaunchLook for Webflow SKU (parallel landing at `/webflow`)

The Webflow SKU shipped as code (landing page, platform-aware fix prompts, finding categories, outreach playbook). Three manual items remain to switch it fully on:

- [ ] **Tally Q7**: open the intake form in Tally â†’ click Q7 (`Which platform built it?`) â†’ **Edit options** â†’ add `Webflow` between `v0` and `Other`. ~5 min. See [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md) Â§"Webflow option for Q7" for the exact new list. No conditional logic changes are needed.
- [ ] **Webflow community validation outreach**: post in 2â€“3 Webflow communities to validate demand and find your first Webflow customer. Use the three Webflow pitches in [`OUTREACH-PLAYBOOK.md`](OUTREACH-PLAYBOOK.md) Â§7b. Targets: [forum.webflow.com](https://forum.webflow.com), [r/Webflow](https://reddit.com/r/Webflow), Webflow Community Slack/Discord. The "post-Nov 2024 silent form failure" hook is the most specific opener; lead with it.
- [ ] **(Optional) Stripe success URL for Webflow buyers** â€” by default Stripe redirects all paid customers to `/thanks` (whose copy is platform-agnostic, so this works fine out of the box). If you want a dedicated Webflow thanks experience, duplicate `landing/thanks.html` to `landing/webflow/thanks.html` (or just `landing/webflow-thanks.html`), point a third Stripe Payment Link at it, and update `landing/assets/config.js`. Skip until you have â‰¥3 paying Webflow customers â€” same product, different vanity URL.

Code that already shipped (verify with `git log --oneline` if you doubt):

- `landing/webflow.html` (dedicated page, $19 / $49 / $99, Webflow-flavored copy)
- `scripts/ai_audit.py --platform webflow` (Designer-flavored fix prompts)
- `scripts/ai_audit/prompts/fix_prompt_webflow.txt` (platform appendix)
- `scripts/audit_ui/` Platform dropdown (vibe-coder / webflow, default vibe-coder)
- `templates/report/report.html.j2` ("LaunchLook for Webflow" header, Designer fix-prompt label)
- `docs/WEBFLOW-EXPANSION.md` (single source of truth for the SKU)

---

## Free-audit operational tasks (new with q4)

The free 3-finding audit hero on the landing page (and on `/webflow`)
is the primary CTA. Per `docs/FREE-AUDIT-WORKFLOW.md`, the full flow is
manual until volume justifies automation. Daily ritual:

- [ ] **Create the Notion DB** "Free Audit Requests" with the schema
  in `docs/FREE-AUDIT-WORKFLOW.md` section 2 and share it with the
  LaunchLook integration. Set `NOTION_FREE_AUDIT_DB_ID` in `.env` AND
  in Vercel env. Until this is set, the serverless function logs a
  warning and skips the Notion write (the submitter still gets a
  confirmation email).
- [ ] **Confirm Resend domain + API key.** The free-audit confirmation
  uses `RESEND_API_KEY` + `EMAIL_FROM` from the existing setup. Send a
  test submit through the live form to confirm the founder-voice
  confirmation lands in inbox (not spam).
- [ ] **Daily (<= 24h SLA):** open Notion -> free-audit DB -> filter
  `Status = queued` -> triage abuse, run the pipeline, review in the
  audit UI, deliver, write fingerprints back to the Notion row, mark
  `Status = delivered`. See `FREE-AUDIT-WORKFLOW.md` section 3 for the
  exact commands.
- [ ] **Weekly:** scan for abuse patterns (repeated hostnames,
  throwaway email domains, IP bursts). Set `Status = abuse` on any
  rows that look off, and consider tightening the rate limits in
  `api/free-audit.py` if it's chronic.
- [ ] **After each Scale Up Package or Pro Package Stripe purchase:**
  manually grant a checklist token. Open
  `landing/data/checklist_tokens.json`, append a short opaque string
  (uuid prefix or stripe charge id), commit, push. Email the customer
  `https://launchlook.app/checklist?token=<value>`. The token unlocks
  the full checklist; without it, visitors see truncated previews and
  an upsell. Trial token `test` is in the file for QA only -- remove
  it before any aggressive launch.
- [ ] **Automate the fingerprint write-back** (defer until >= 5 free
  audits / week). Today, after the deliver step Rob copies the 3
  fingerprints from the pipeline log into the Notion row's
  `Finding Fingerprints` column by hand (semicolon-separated). The
  helper `scripts/ai_audit/free_audit_lookup.persist_free_audit_fingerprints`
  already does the write -- wire it into `scripts/deliver_report.py
  --free` when the free-tier deliver path lands.
- [ ] **Automate the Stripe -> checklist token grant** (defer until
  >= 3 Scale Up purchases). The Stripe webhook in
  `api/stripe-webhook.py` could append to
  `landing/data/checklist_tokens.json` directly (or better, move
  tokens to Notion and have `checklist.html` fetch via API). For now,
  manual is fine.
- [ ] **Watch the LLM bill on the free tier.** Each delivered free
  audit burns ~one full Starter-cap LLM run that earns $0. If the
  monthly free-audit count x per-run cost exceeds ~$50, batch process
  every 2 to 3 days instead of daily, OR drop the cap to 3 (matching
  the deliverable) and skip the prescreener entirely. Numbers and
  levers live in `docs/AI-AUDIT-PIPELINE.md`.
- [ ] **When first Pro customer opts in to GitHub integration:** ask
  them for their repo URL + a fine-grained PAT with `Issues: read+write`
  scope on that single repo (30-day expiry). Add a `github:` block to
  `customers/<slug>.yaml` (`repo` + `token_env`, optionally
  `commit_sha` and `pr_number`). Export the PAT as
  `<CUSTOMER_SLUG>_GITHUB_PAT` in your shell. Always dry-run first:
  `python scripts/github_push.py --customer customers/<slug>.yaml --dry-run`.
  Full playbook in `docs/GITHUB-INTEGRATION.md`. Never auto-runs from
  the delivery pipeline; you trigger it by hand after spot-checking.

---

## ðŸŸ¡ Optional â€” trust & polish

- [x] **LinkedIn** on homepage (Who's behind + footer)
- [ ] Paste `https://launchlook.app/` in Slack/iMessage â€” confirm OG image looks right
- [ ] Rename Stripe **product** display names to Starter Package / Full Package (cosmetic)
- [ ] Notion API token + share DBs with integration ([`03-build-queue.md`](03-build-queue.md) BL-04) â€” for scripts later
- [ ] Stripe webhook â†’ email you on purchase (optional MVP)
- [ ] Sync [`external/launchlook-prelaunch-checklist`](../external/launchlook-prelaunch-checklist) if you changed checklist copy locally

---

## ðŸŸ¢ Shmoozing â€” when Â§1â€“4 are green

Goal: **3 strangers pay $9** â€” then stop polishing the site.

- [ ] Read: [`SHARE-AND-REVIEWS.md`](SHARE-AND-REVIEWS.md) (weekly rhythm + what to link)
- [ ] Script: [`templates/cold-outreach-loom-script.md`](../templates/cold-outreach-loom-script.md)
- [ ] Free sample playbook: [`templates/week-1-free-sample-playbook.md`](../templates/week-1-free-sample-playbook.md)
- [ ] Track prospects in Notion **Outreach Tracker**
- [ ] **30** targeted DMs/Looms (quality over volume)
- [ ] Offer $9 Starter first; upsell Full when theyâ€™re launching this week

---

## 60-day targets (reminder)

From [`00-START-HERE.md`](00-START-HERE.md):

| Target | Number |
|--------|--------|
| Paying customers | **8+** (mix $9 / $29) |
| â€œUsefulâ€ or better | **6 of 8** |
| Referrals | **2+** |

---

## Plausible analytics setup

The Plausible script is installed across all landing pages. To activate:

1. Sign up at https://plausible.io (or self-host)
2. Add `launchlook.app` as a site
3. Configure goals in Plausible dashboard (must match these exact names):
   - FreeAuditSignup
   - StarterCheckout
   - ScaleUpCheckout
   - ProCheckout
   - IntakeFormStart
   - RescanAddOn
4. Optionally add `launchlook.app/webflow` as a goal-only filter for Webflow-specific funnel measurement
5. Verify data flowing by visiting a landing page in incognito and watching the Plausible realtime view

If using a different analytics tool, replace the script tag in every `landing/*.html` file. No other code depends on Plausible.

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
| Tally paste (text only) | [`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) |
| Customer tracking | [`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md) Â· `python scripts/customers_track.py stats` |
| At 10 paying | [`CUSTOMER-10-RUNBOOK.md`](CUSTOMER-10-RUNBOOK.md) |
| Intake form (Tally) | `https://tally.so/r/9qodVE` â†’ wired in `config.js` |
| After intake (Tally thanks) | `https://tally.so/r/Y5xO5J` â†’ set as redirect on form 9qodVE in Tally |
| Site after Stripe | `https://launchlook.app/thanks` â†’ button opens intake 9qodVE |

---

## Cursor / repo â€” nothing blocking you

- Tally intake + thanks URLs are already in `landing/assets/config.js` â€” no need to ask Cursor to wire them.
- If you change Tally publish URLs, update `config.js` and push (or ask Cursor to push).
- When **hello@launchlook.app** reliably receives Tally + test mail, check off Â§3 and note the date here.

---


*When Â§1â€“4 are checked off, youâ€™re in outreach mode â€” not â€œone more site tweakâ€ mode.*

## Confidence Check / Saboteur re-scan add-on (q6)

- [ ] **Confidence Check / Saboteur re-scan add-on (q6)** - three setup tasks below.
- [ ] Stripe Payment Link **$19** (Confidence Check standalone): create in dashboard with metadata `product=confidence_check`. Paste URL into Vercel env `STRIPE_PAYMENT_LINK_SABOTEUR` and into `landing/assets/config.js` `stripe.saboteur`. See `docs/CONFIDENCE-CHECK-WORKFLOW.md` Â§2.
- [ ] Stripe Payment Link **$9** (Confidence Check within-14-days): create in dashboard with metadata `product=confidence_check`. Paste URL into Vercel env `STRIPE_PAYMENT_LINK_SABOTEUR_DISCOUNTED`. Sent manually via the post-delivery email until automation lands.
- [ ] Notion **Confidence Checks** database: create with schema `customer_email` (email), `original_audit_id` (text), `paid_at` (date), `price_paid` (number, cents), `status` (select: `queued` / `delivered`). Paste DB ID into Vercel env `NOTION_CONFIDENCE_CHECK_DB_ID`. See `docs/CONFIDENCE-CHECK-WORKFLOW.md` Â§3.


## Placeholder swaps

- [ ] Swap `landing/images/rob.jpg` placeholder (200x200, generated by the q5+q13 worker on 2026-05-26) with a real headshot. The 'Made by Rob' section in `landing/index.html` and `landing/webflow.html` uses this asset; sizing is 96x96 rendered, so a 192x192 (2x) source is ideal. No client work depends on this; ship whenever a usable photo is ready.


## LaunchLook Verified badge (q17)

- [ ] Stripe Payment Link **$9** (badge re-verification): create in dashboard with metadata `product=reverify`. Paste URL into Vercel env `STRIPE_PAYMENT_LINK_REVERIFY` and into `landing/assets/config.js` `stripe.reverify`. See `docs/VERIFIED-BADGE-WORKFLOW.md` A3.
- [ ] First Verified customer: after Rob ships their badge, hit `https://launchlook.app/verify?slug={their_slug}` on prod to confirm the page renders the green check + tier + validity window. Then paste the embed snippet back to the customer (already in the delivery email but worth a sanity check on the first one).
- [ ] Optional: when `verify.json` count exceeds ~25-50 records, migrate `landing/data/verified/` to Notion / D1 so we can mint badges without a deploy. Not urgent.

### Handoff Report add-on (q18)

- [ ] Create Stripe Payment Link for the $99 Handoff Report add-on. Attach metadata `product=handoff_report` so the webhook routes via `handle_handoff_report_purchase` instead of the Pro Package SKU. Paste the resulting price ID into the Vercel env (`STRIPE_HANDOFF_REPORT`) and into `landing/index.html` + `landing/webflow.html`.
- [ ] Add the Plausible goal `HandoffReportAddOn` in the Plausible dashboard so the existing `plausible-event-name` attribute fires.
