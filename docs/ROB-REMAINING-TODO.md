# Everything left for Rob — LaunchLook

**Last updated:** May 25, 2026  
**Site:** https://launchlook.app · **Repo:** `romado33/launchlook`

Use this as your single owner checklist. Code/deploy items below marked ✅ are already in GitHub unless noted.

### Your next 3 actions (in order)

1. **Tally** — Pick a form to use, then finish setup in Tally UI:
   - New rebuilt API form `QKOX1A` (DRAFT, May 25) — edit at https://tally.so/forms/QKOX1A/edit, **OR**
   - Existing form `9qodVE` (already wired into `config.js`)
   - Either way, in Tally UI: add Notifications → `hello@launchlook.app`, After-submit redirect → `https://tally.so/r/Y5xO5J`, and conditional logic for Q9–Q11 (Full Package + Pro Package / "Yes" to test accounts). Click-by-click steps for `QKOX1A` are in §1 below.
2. **Tracker** — `python scripts/customers_track.py init` then `add` for your two test payments (or real ones).
3. **Notion ops** — LaunchLook Ops workspace so you can deliver the first real checkup.

**Doc index:** [`docs/README.md`](README.md) · **Tally paste file:** [`TALLY-COPY-PASTE.md`](TALLY-COPY-PASTE.md)

---

## Already done (don’t redo)

- [x] Landing site live (Vercel, clean URLs, security headers)
- [x] Starter Package **$19** / Full Package **$49** / Pro Package **$99** on homepage; Stripe **public** links in `landing/assets/config.js` (Pro link still pending — see `docs/MANUAL-TASKS-PRICE-BUMP.md`)
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
- [x] Stripe checkout tested for the original $9 / $29 prices (May 2026); $19 / $49 / $99 retest pending (see `docs/MANUAL-TASKS-PRICE-BUMP.md`)

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

2. **Rule 1 — show Q9 only for Full / Pro Package buyers** (place this `/logic` block right after Q8)
   - Type `/logic` → Conditional logic
   - IF `Which tier did you purchase?` **is** `Full Package ($49)` OR **is** `Pro Package ($99)`
   - THEN **Show blocks** → select `Can we use test accounts?`
   - (After the price bump, the Tally tier dropdown needs updating in the form editor — see `docs/MANUAL-TASKS-PRICE-BUMP.md`. Same rule, just the option labels move from `$29` → `$49` plus a new `$99` Pro option.)

3. **Rule 2 — show Q10 when Q9 = Yes** (place this `/logic` block right after Q9)
   - Type `/logic` → Conditional logic
   - IF `Can we use test accounts?` **is** `Yes — I'll provide two test accounts`
   - THEN **Show blocks** → select `Test account 1 — email and password`

4. **Rule 3 — show Q11 when Q9 = Yes** (same `/logic` block as Rule 2, OR a second one right after Rule 2)
   - IF `Can we use test accounts?` **is** `Yes — I'll provide two test accounts`
   - THEN **Show blocks** → select `Test account 2 — email and password`

Three rules total. There is no need to re-gate Q10/Q11 by Q8 — Q9 is already hidden unless Q8 = Full Package or Pro Package, so Q10/Q11 inherit that gate transitively (if Q9 is hidden, no one can answer "Yes" on it, so Q10/Q11 stay hidden).

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

- [ ] **Three** links: $19 Starter, $49 Full, $99 Pro — see `docs/MANUAL-TASKS-PRICE-BUMP.md` for the price-bump migration steps
- [x] Success URL returns customers to `/thanks` (verified via live test)
- [ ] Cancel URL (if offered): `https://launchlook.app/#pricing` (optional)
- [x] URLs match `config.js` (`stripe.starter`, `stripe.launch`); add `stripe.pro` once the Pro payment link exists
- [ ] **Confidence Check $19 standalone** — Create Stripe Payment Link with metadata `product=confidence_check`. Paste price/link URL into `STRIPE_PAYMENT_LINK_SABOTEUR` in Vercel env AND into `landing/assets/config.js` under `stripe.saboteur`. Details in [`CONFIDENCE-CHECK-WORKFLOW.md`](CONFIDENCE-CHECK-WORKFLOW.md) §2.
- [ ] **Confidence Check $9 within 14 days** — Create Stripe Payment Link with metadata `product=confidence_check`. Paste URL into `STRIPE_PAYMENT_LINK_SABOTEUR_DISCOUNTED` in Vercel env AND into `config.js` under `stripe.saboteurDiscounted`. This link is sent manually in post-delivery emails (not exposed on the landing page).
- [ ] **Notion 'Confidence Checks' DB** — Create the database with the schema in [`CONFIDENCE-CHECK-WORKFLOW.md`](CONFIDENCE-CHECK-WORKFLOW.md) §3 (`customer_email`, `original_audit_id`, `paid_at`, `price_paid`, `status`). Share with the LaunchLook integration. Paste DB ID into `NOTION_CONFIDENCE_CHECK_DB_ID` in Vercel env.

### 3. Email receiving (~15–30 min)

Site and templates use **hello@launchlook.app** (matches launchlook.app). If you set up a different address, align DNS + Tally notifications + `supportEmail` in `config.js`.

- [ ] **hello@launchlook.app** forwards to an inbox you actually check (ImprovMX, GoDaddy forward, or Google Workspace)
- [ ] Send a test email from another account and confirm delivery
- [ ] Tally test submission arrives at that inbox

### 4. End-to-end payment test (~20 min)

Use **incognito** on desktop and once on your **phone**. Detail: [`07-launchlook-go-live.md`](07-launchlook-go-live.md) §8.

**Starter ($19)**

- [ ] Click **Get Starter Package — $19** → Stripe opens
- [ ] Complete payment (live retest pending after price bump)
- [ ] Land on `https://launchlook.app/thanks` (not 404)
- [ ] Intake opens **Tally** (not only mailto)
- [ ] Submit test intake → you receive it at hello@launchlook.app
- [ ] Form only asks safe fields; security checkbox required

**Full ($49)**

- [ ] Same flow for **Get Full Package — $49** (live retest pending after price bump)
- [ ] Full Package shows test-account questions when selected

**Pro ($99)**

- [ ] Same flow for **Get Pro Package — $99** (new tier — Stripe product not yet created; see `docs/MANUAL-TASKS-PRICE-BUMP.md`)
- [ ] Pro Package shows test-account questions when selected (same as Full)
- [ ] Pro Package customers receive email confirming the 30-min Loom walkthrough scheduling step

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
- [ ] **Weekly: AI margin check** — `python scripts/ai_costs_report.py --summary --days 7` and confirm margin > 70%. Full playbook in [`AI-COST-MONITORING.md`](AI-COST-MONITORING.md). If margin dips, run `--alert --days 7` to find the outlier(s).
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

## 🟠 Free-audit operational tasks (new with q4)

The free 3-finding audit hero on the landing page (and on `/webflow`)
is the primary CTA. Per `docs/FREE-AUDIT-WORKFLOW.md`, the full flow is
manual until volume justifies automation. Daily ritual:

- [ ] **Create the Notion DB** "Free Audit Requests" with the schema in
  `docs/FREE-AUDIT-WORKFLOW.md` §2 and share it with the LaunchLook
  integration. Set `NOTION_FREE_AUDIT_DB_ID` in `.env` AND in Vercel
  env. Until this is set, the serverless function logs a warning and
  silently skips the Notion write (the submitter still gets a
  confirmation email).
- [ ] **Confirm Resend domain + API key.** The free-audit confirmation
  uses `RESEND_API_KEY` + `EMAIL_FROM` from the existing setup. Send a
  test submit through the live form to confirm the founder-voice
  confirmation lands in inbox (not spam).
- [ ] **Daily (≤ 24h SLA):** open Notion → free-audit DB → filter
  `Status = queued` → triage abuse, run the pipeline, review in the
  audit UI, deliver, write fingerprints back to the Notion row, mark
  `Status = delivered`. See `FREE-AUDIT-WORKFLOW.md` §3 for the exact
  commands.
- [ ] **Weekly:** scan for abuse patterns (repeated hostnames, throwaway
  email domains, IP bursts). Set `Status = abuse` on any rows that look
  off, and consider tightening the rate limits in `api/free-audit.py`
  if it's chronic.
- [ ] **After each Scale Up Package or Pro Package Stripe purchase:**
  manually grant a checklist token. Open
  `landing/data/checklist_tokens.json`, append a short opaque string
  (uuid prefix or stripe charge id), commit, push. Email the customer
  `https://launchlook.app/checklist?token=<value>`. The token unlocks
  the full checklist; without it, visitors see truncated previews + an
  upsell. Trial token `test` is in the file for QA only — remove it
  before any aggressive launch.
- [ ] **Automate the fingerprint write-back** (defer until ≥ 5 free
  audits / week). Today, after the deliver step Rob copies the 3
  fingerprints from the pipeline log into the Notion row's
  `Finding Fingerprints` column by hand (semicolon-separated). The
  helper `scripts/ai_audit/free_audit_lookup.persist_free_audit_fingerprints`
  already does the write — wire it into `scripts/deliver_report.py
  --free` when the free-tier deliver path lands.
- [ ] **Automate the Stripe → checklist token grant** (defer until ≥ 3
  Scale Up purchases). The Stripe webhook in `api/stripe-webhook.py`
  could append to `landing/data/checklist_tokens.json` directly (or
  better, move tokens to Notion and have `checklist.html` fetch via
  API). For now, manual is fine.
- [ ] **Watch the LLM bill on the free tier.** Each delivered free
  audit burns ~one full Starter-cap LLM run that earns $0. If the
  monthly free-audit count × per-run cost exceeds ~$50, batch process
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

## 🟡 Optional — trust & polish

- [x] **LinkedIn** on homepage (Who's behind + footer)
- [ ] Paste `https://launchlook.app/` in Slack/iMessage — confirm OG image looks right
- [ ] Rename Stripe **product** display names to Starter Package / Full Package (cosmetic)
- [ ] Notion API token + share DBs with integration ([`03-build-queue.md`](03-build-queue.md) BL-04) — for scripts later
- [ ] Stripe webhook → email you on purchase (optional MVP)
- [ ] Sync [`external/launchlook-prelaunch-checklist`](../external/launchlook-prelaunch-checklist) if you changed checklist copy locally

---

## 🟢 Shmoozing — when §1–4 are green

Goal: **3 strangers pay $19** — then stop polishing the site.

- [ ] Read: [`SHARE-AND-REVIEWS.md`](SHARE-AND-REVIEWS.md) (weekly rhythm + what to link)
- [ ] Script: [`templates/cold-outreach-loom-script.md`](../templates/cold-outreach-loom-script.md)
- [ ] Free sample playbook: [`templates/week-1-free-sample-playbook.md`](../templates/week-1-free-sample-playbook.md)
- [ ] Track prospects in Notion **Outreach Tracker**
- [ ] **30** targeted DMs/Looms (quality over volume)
- [ ] Offer $19 Starter first; upsell Full ($49) when they’re launching this week, or Pro ($99) for founders going to investor demo / paid traffic

---

## 60-day targets (reminder)

From [`00-START-HERE.md`](00-START-HERE.md):

| Target | Number |
|--------|--------|
| Paying customers | **8+** (mix $19 / $49 / $99) |
| “Useful” or better | **6 of 8** |
| Referrals | **2+** |

---

## Quick reference

| Item | Value |
|------|--------|
| Domain | launchlook.app |
| Support | hello@launchlook.app |
| Tiers | Starter **$19** (cap 10) · Scale Up **$49** (cap 30) · Pro **$99** (cap 40) |
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

## q-final-audit follow-ups (May 26, 2026) — resolved by q-final-lint

The `q-final-audit` worker ran a full consistency scan against the canonical docs (`docs/SIMPLICITY-GUARDRAILS.md` §6, `docs/PRODUCT-DECISIONS.md` §1/§7, `docs/TESTERS-CAST.md`) and shipped `scripts/consistency_check.py` + `docs/CONSISTENCY-AUDIT-REPORT.md`. The `q-final-lint` worker swept the human-review deltas the next pass:

- [x] **"Priority triage" tagline (5 instances in `landing/index.html`):** rewritten to "The 10 things to fix first" / "the 10 most important findings" (canonical Starter cap = 10).
- [x] **"Comprehensive audit" tagline (4 instances in `landing/index.html`):** rewritten to "Ready for real users" (Scale Up card, outcome framing) and "Full audit" elsewhere; only "comprehensive checklist" remains, which is allowed per §6.
- [x] **Stale finding caps `7` / `25` in tier-card prose:** bumped to canonical `10` / `30` from `PRODUCT-DECISIONS.md` §1.
- [x] **"safe synthetic values" in The Stranger blurb (`landing/index.html` line 622 + `landing/webflow.html` line 475):** rewritten to "safe test data".
- [x] **3 prose em-dashes in `landing/index.html`:** eliminated naturally by the tier-card copy rewrites above.
- [x] **16 UI placeholder em-dashes in table cells + `landing/r.html` + `templates/r/shareable.html.j2`:** swapped to ASCII `-` for consistency. See `docs/REFACTOR-NOTES.md` for the global find-replace.

Remaining deltas (deferred, low priority — not shipping blockers):

- [x] **landing/index.html line 124:** "Trust gaps" rewritten to "Trust signals and legal pages" per `finding_categories.yaml` (q-deferred-cleanup, 2026-05-26).
- [x] **landing/index.html (5 instances of Cross-user data check + 2 prose mentions) and landing/vs-pagelens.html (2 Mobile audit + 1 Broken CTAs):** swapped to buyer-facing display names from `finding_categories.yaml` ("user data isolation", "mobile layout issues", "broken buttons and dead links"). See `docs/CONSISTENCY-AUDIT-REPORT.md` Cleanup-pass section for the full before/after table.
- [x] **Customer YAML caps (cap 7 / cap 25):** verified clean. `customers/example-jane-sparkle.yaml` already says "Starter caps at 10; this YAML deliberately ships 7 to show well-under-cap output"; `customers/example-pro-package.yaml` already says "Cap raised to 40 findings (this example uses 14 to show depth, not volume)". Canonical caps (10/30/40) already in place; the original flag was stale.

Re-run `python scripts/consistency_check.py --report-only` after any of these are applied to verify the count drops. Exit code is 0 unless a `critical` issue appears; the script is wireable as a pre-commit hook later.

## q-final-lint follow-ups (May 26, 2026)

The `q-final-lint` worker linted Python (`ruff` + `black` + `mypy`) + frontend (`prettier` JS only — HTML left alone to avoid `prettier` default churn), refactored for clarity, fixed the q18 Handoff Report CLI regression, swept forbidden vocab + em-dashes, and ran a full smoke-test pass (124/124 tests passing, all 12 smoke commands green). No new blocking items surfaced. Full notes in `docs/REFACTOR-NOTES.md`. Open follow-ups:

- [ ] **HTML prettier opt-in.** `landing/*.html` was not auto-formatted because `prettier`'s default reflow would noisily diverge from the existing hand-tuned 2-space style. If we want HTML formatted consistently later, add `.prettierrc.json` with `printWidth: 120` + `htmlWhitespaceSensitivity: ignore` and run it as one-shot pass (review the diff carefully — Jinja2 `{{ ... }}` placeholders inside `<script>` blocks need to be verified).
- [x] **`scripts/share_report.py --no-commit` flag.** Shipped by q-deferred-cleanup (2026-05-26). When passed, the script applies the JSON state change to disk but skips `git add` + `git commit`. Default behavior unchanged (still auto-commits). Documented in `docs/SHAREABLE-REPORT-WORKFLOW.md` 3 and covered by `tests/test_share_report.py::test_no_commit_flag_suppresses_git_commit` + `test_default_behavior_still_commits`.

---


*When §1–4 are checked off, you’re in outreach mode — not “one more site tweak” mode.*
