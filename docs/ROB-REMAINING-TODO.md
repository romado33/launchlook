# Everything left for Rob — LaunchLook

**Last updated:** May 25, 2026  
**Site:** https://launchlook.app · **Repo:** `romado33/launchlook`

Use this as your single owner checklist. Code/deploy items below marked ✅ are already in GitHub unless noted.

### Your next 3 actions (in order)

1. **Tally** — Pick a form to use, then finish setup in Tally UI:
   - New rebuilt API form `QKOX1A` (DRAFT, May 25) — edit at https://tally.so/forms/QKOX1A/edit, **OR**
   - Existing form `9qodVE` (already wired into `config.js`)
   - Either way, in Tally UI: add Notifications → `hello@launchlook.app`, After-submit redirect → `https://tally.so/r/Y5xO5J`, and conditional logic for Q9–Q11 (Full Package only / "Yes" to test accounts). Click-by-click steps for `QKOX1A` are in §1 below.
2. **Tracker** — `python scripts/customers_track.py init` then `add` for your two test payments (or real ones).
3. **Notion ops** — LaunchLook Ops workspace so you can deliver the first real checkup.

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
- [x] Paying-customer tracker: `scripts/customers_track.py` + [`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md)
- [x] Customer 10 prep: [`CUSTOMER-10-RUNBOOK.md`](CUSTOMER-10-RUNBOOK.md) + `data/milestones.json`
- [x] Tally URLs in `config.js`: intake `9qodVE`, post-intake thanks `Y5xO5J` (deployed)
- [x] Homepage CTAs use shared button styles (all primary actions look clickable)
- [x] Stripe checkout tested: **Starter $9** and **Full $29** both complete successfully (May 2026)

---

## 🔴 Blocking — before cold outreach

Do these in order. Nothing else on the site matters until the pay → intake → you-get-notified loop works.

### 1. Tally intake form (~15–30 min)

**Two options now:**
- **(A) New API-built form `QKOX1A`** (DRAFT, rebuilt May 25). Edit: https://tally.so/forms/QKOX1A/edit · Preview: https://tally.so/r/QKOX1A
- **(B) Existing manual form `9qodVE`** (already wired into `config.js`)

The old API form `GxQkOL` has been **deleted and replaced by `QKOX1A`**. The rebuild fixes the previous problem where Tally's logic dropdown showed each question's help text instead of its title — each question is now a single TITLE block with the description inlined as a smaller second line, so the logic editor lists real question names.

**Paste references (only needed for option B):** [`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) · **Block guide:** [`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt) · **Setup steps:** [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md)

**To re-create or replace the form via API:**
- Fresh form: `python scripts/tally_create_intake.py`
- Replace an existing form (DELETE then POST): `python scripts/tally_create_intake.py --replace <FORM_ID>`

Both read `TALLY_API_KEY` from `.env`.

#### Conditional logic — how Tally actually works

Per Tally's docs, conditional show/hide is **not** a per-block menu item. The right-click on a question only has Delete / Duplicate / Hide / Turn into — that's why Q10 and Q11 didn't expose a "Logic" option. The flow is always:

1. **Hide the target question(s) by default.** Click the 6-dot drag handle (`⋮⋮`) at the left of the block → **Hide**. Shortcut: `Ctrl+Shift+H`. Clicking the question's TITLE selects every block inside that group (input + options), so one Hide call hides the whole question.
2. **Add a `/logic` block upstream.** Place your cursor on a blank line above where the form should branch, type `/logic`, and pick **Conditional logic**.
3. **Configure the IF / THEN.** `IF <upstream question> = <option value>` → action **Show blocks** → pick the hidden question(s).

This pattern works for any block type, including TEXTAREA (so Q10 and Q11 don't need any special treatment).

#### Three rules to add in `QKOX1A`

In the editor (https://tally.so/forms/QKOX1A/edit), do these in order. The dropdown will now show each question by its TITLE (e.g. "Can we use test accounts?") instead of the old help text.

1. **Hide Q9, Q10, Q11 by default**
   - On Q9 (`Can we use test accounts?`): `⋮⋮` → **Hide**
   - On Q10 (`Test account 1 — email and password`): `⋮⋮` → **Hide**
   - On Q11 (`Test account 2 — email and password`): `⋮⋮` → **Hide**

2. **Rule 1 — show Q9 only for Full Package buyers** (place this `/logic` block right after Q8)
   - Type `/logic` → Conditional logic
   - IF `Which tier did you purchase?` **is** `Full Package ($29)`
   - THEN **Show blocks** → select `Can we use test accounts?`

3. **Rule 2 — show Q10 when Q9 = Yes** (place this `/logic` block right after Q9)
   - Type `/logic` → Conditional logic
   - IF `Can we use test accounts?` **is** `Yes — I'll provide two test accounts`
   - THEN **Show blocks** → select `Test account 1 — email and password`

4. **Rule 3 — show Q11 when Q9 = Yes** (same `/logic` block as Rule 2, OR a second one right after Rule 2)
   - IF `Can we use test accounts?` **is** `Yes — I'll provide two test accounts`
   - THEN **Show blocks** → select `Test account 2 — email and password`

Three rules total. There is no need to re-gate Q10/Q11 by Q8 — Q9 is already hidden unless Q8 = Full Package, so Q10/Q11 inherit that gate transitively (if Q9 is hidden, no one can answer "Yes" on it, so Q10/Q11 stay hidden).

#### Checklist

- [x] `intakeFormUrl` = `https://tally.so/r/9qodVE` in `config.js` (live on site)
- [x] `tallyThanksUrl` = `https://tally.so/r/Y5xO5J` in `config.js` (reference for redirect)
- [x] **Rebuilt API form `QKOX1A` created** (May 25, replaces `GxQkOL`) — 15 questions, no separate LABEL blocks, descriptions inlined into TITLEs
- [ ] **Pick one form** to keep; if switching to `QKOX1A`, update `intakeFormUrl` in `landing/assets/config.js`
- [ ] In Tally UI on the chosen form: hide Q9/Q10/Q11 + add the 3 `/logic` blocks above
- [ ] Thank-you message (paste from file) + **after submit redirect** → `https://tally.so/r/Y5xO5J`
- [ ] Notifications → **hello@launchlook.app** (all answers)
- [ ] Test Starter path (Q9–Q11 hidden) and Full path (Q9 visible; Q10/Q11 visible only after picking "Yes")
- [ ] If keeping `QKOX1A`: **Publish** it (currently DRAFT)
- [ ] (Optional) Tally → Notion **Customers**

### 2. Stripe Payment Links (~15 min)

Dashboard: [dashboard.stripe.com](https://dashboard.stripe.com) → **Payment Links** (live mode when ready)

- [x] Exactly **two** links: $9 Starter, $29 Full — both checkout successfully
- [x] Success URL returns customers to `/thanks` (verified via live test)
- [ ] Cancel URL (if offered): `https://launchlook.app/#pricing` (optional)
- [x] URLs match `config.js` (`stripe.starter`, `stripe.launch`)

### 3. Email receiving (~15–30 min)

Site and templates use **hello@launchlook.app** (matches launchlook.app). If you set up a different address, align DNS + Tally notifications + `supportEmail` in `config.js`.

- [ ] **hello@launchlook.app** forwards to an inbox you actually check (ImprovMX, GoDaddy forward, or Google Workspace)
- [ ] Send a test email from another account and confirm delivery
- [ ] Tally test submission arrives at that inbox

### 4. End-to-end payment test (~20 min)

Use **incognito** on desktop and once on your **phone**. Detail: [`07-launchlook-go-live.md`](07-launchlook-go-live.md) §8.

**Starter ($9)**

- [x] Click **Get Starter Package — $9** → Stripe opens
- [x] Complete payment (live test May 2026)
- [x] Land on `https://launchlook.app/thanks` (not 404)
- [ ] Intake opens **Tally** (not only mailto)
- [ ] Submit test intake → you receive it at hello@launchlook.app
- [ ] Form only asks safe fields; security checkbox required

**Full ($29)**

- [x] Same flow for **Get Full Package — $29** (live test May 2026)
- [ ] Full Package shows test-account questions when selected

**Quick URL check**

- [ ] `/`, `/sample`, `/thanks`, `/checklist`, `/privacy`, `/terms` → all 200
- [ ] Footer **GitHub** link works
- [ ] Hard-refresh homepage after last deploy (Ctrl+Shift+R)

---

## 🟠 Important — first paying customer delivery

### 5. Customer tracker (local — 2 min once)

Guide: [`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md)

- [ ] `python scripts/customers_track.py init` (creates gitignored `data/customers.json`)
- [ ] After each Stripe payment: `customers_track.py add ...`
- [ ] After intake: `mark-intake` · after report: `mark-delivered`
- [ ] Weekly: `customers_track.py stats` (progress toward 8 and **10** paying)
- [ ] At **10 paying**: read [`CUSTOMER-10-RUNBOOK.md`](CUSTOMER-10-RUNBOOK.md) → `acknowledge-milestone-10` → start BL-14/15

### 6. Notion ops workspace

Guide: [`03-build-queue.md`](03-build-queue.md) BL-03, BL-08 · Templates: [`templates/notion/`](../templates/notion/)

- [ ] Workspace **LaunchLook Ops**
- [ ] Databases: **Customers**, **Findings Library** (import/sync from `findings_library/`), **Outreach Tracker**
- [ ] Duplicate report templates into Notion:
  - Starter → `templates/notion/report-quick-checkup.md`
  - Full → `templates/notion/report-launch-pack.md`
- [ ] Before each delivery: read [`templates/report-voice-guide.md`](../templates/report-voice-guide.md) (plain English for founders)

### 7. Delivering a checkup (manual workflow)

- [ ] Audit pass: [`templates/manual-audit-checklist.md`](../templates/manual-audit-checklist.md) (~15 min)
- [ ] Fill Notion report; paste fix prompts from `findings_library/findings.json`
- [ ] Starter: include Quick Start Guide (prompt in `prompts/`, architecture in `05-technical-architecture.md`)
- [ ] Email customer: [`templates/email/delivery.txt`](../templates/email/delivery.txt) (includes quote + share asks)
- [ ] Optional 48h later: [`templates/email/ask-for-quote.txt`](../templates/email/ask-for-quote.txt)

### 8. Resend (welcome / delivery automation)

- [ ] [resend.com](https://resend.com) — verify domain **launchlook.app**
- [ ] `.env` (never commit): `RESEND_API_KEY`, `FROM_EMAIL=hello@launchlook.app`, `ADMIN_EMAIL=…`
- [ ] Test welcome email after purchase ([`templates/email/welcome.txt`](../templates/email/welcome.txt))
- [ ] Optional: wire Stripe webhook or manual send for week 1

### 9. Vercel dashboard sanity check (5 min)

- [ ] Project **Root Directory** = empty (repo root), **not** `landing`
- [ ] Build: `node scripts/copy-landing-for-vercel.mjs` · Output: `dist`
- [ ] Production branch: `main`

---

## 🟣 LaunchLook for Webflow SKU (parallel landing at `/webflow`)

The Webflow SKU shipped as code (landing page, platform-aware fix prompts, finding categories, outreach playbook). Three manual items remain to switch it fully on:

- [ ] **Tally Q7**: open the intake form in Tally → click Q7 (`Which platform built it?`) → **Edit options** → add `Webflow` between `v0` and `Other`. ~5 min. See [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md) §"Webflow option for Q7" for the exact new list. No conditional logic changes are needed.
- [ ] **Webflow community validation outreach**: post in 2–3 Webflow communities to validate demand and find your first Webflow customer. Use the three Webflow pitches in [`OUTREACH-PLAYBOOK.md`](OUTREACH-PLAYBOOK.md) §7b. Targets: [forum.webflow.com](https://forum.webflow.com), [r/Webflow](https://reddit.com/r/Webflow), Webflow Community Slack/Discord. The "post-Nov 2024 silent form failure" hook is the most specific opener; lead with it.
- [ ] **(Optional) Stripe success URL for Webflow buyers** — by default Stripe redirects all paid customers to `/thanks` (whose copy is platform-agnostic, so this works fine out of the box). If you want a dedicated Webflow thanks experience, duplicate `landing/thanks.html` to `landing/webflow/thanks.html` (or just `landing/webflow-thanks.html`), point a third Stripe Payment Link at it, and update `landing/assets/config.js`. Skip until you have ≥3 paying Webflow customers — same product, different vanity URL.

Code that already shipped (verify with `git log --oneline` if you doubt):

- `landing/webflow.html` (dedicated page, $19 / $49 / $99, Webflow-flavored copy)
- `scripts/ai_audit.py --platform webflow` (Designer-flavored fix prompts)
- `scripts/ai_audit/prompts/fix_prompt_webflow.txt` (platform appendix)
- `scripts/audit_ui/` Platform dropdown (vibe-coder / webflow, default vibe-coder)
- `templates/report/report.html.j2` ("LaunchLook for Webflow" header, Designer fix-prompt label)
- `docs/WEBFLOW-EXPANSION.md` (single source of truth for the SKU)

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
| Tally paste (text only) | [`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) |
| Customer tracking | [`CUSTOMER-TRACKING.md`](CUSTOMER-TRACKING.md) · `python scripts/customers_track.py stats` |
| At 10 paying | [`CUSTOMER-10-RUNBOOK.md`](CUSTOMER-10-RUNBOOK.md) |
| Intake form (Tally) | `https://tally.so/r/9qodVE` → wired in `config.js` |
| After intake (Tally thanks) | `https://tally.so/r/Y5xO5J` → set as redirect on form 9qodVE in Tally |
| Site after Stripe | `https://launchlook.app/thanks` → button opens intake 9qodVE |

---

## Cursor / repo — nothing blocking you

- Tally intake + thanks URLs are already in `landing/assets/config.js` — no need to ask Cursor to wire them.
- If you change Tally publish URLs, update `config.js` and push (or ask Cursor to push).
- When **hello@launchlook.app** reliably receives Tally + test mail, check off §3 and note the date here.

---


*When §1–4 are checked off, you’re in outreach mode — not “one more site tweak” mode.*
