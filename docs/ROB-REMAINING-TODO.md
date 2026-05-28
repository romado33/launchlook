# Everything left for Rob — LaunchLook

**Last updated:** May 28, 2026 (cleanup + value-scaling + competitive session)
**Site:** https://launchlook.app · **Repo:** `romado33/launchlook`

This file is the **source of truth** for what you still need to do manually. Product/code decisions live in [`PRODUCT-DECISIONS.md`](PRODUCT-DECISIONS.md).

> **Starting the next app?** Read [`LESSONS-LEARNED.md`](LESSONS-LEARNED.md) first
> and copy [`.cursor/rules/launchlook-defaults.mdc`](../.cursor/rules/launchlook-defaults.mdc)
> into the new repo (rename it). Those two files encode every recurring correction and pitfall
> from building LaunchLook v1 so the next project ships faster.

---

## Shipped May 28, 2026 — edge-case hardening (live test run)

**Bug fix + P0/P1 pipeline hardening (automated):**
- **`notion_helpers.py`**: `intake_received_at` field type changed from `"date"` to `"rich_text"` — live Notion column is a rich-text field, not a Date column; the old mapping caused a 400 on every Tally write (discovered during live integration test)
- **`free_audit_lookup.py`**: `recent_delivery()` now skips rows with non-delivered status (`queued`, `processing`, `failed`, etc.). Stale/crashed jobs no longer permanently block new lead captures (P0 fix)
- **`slug.py`**: Email-derived 6-char SHA-256 hex suffix appended to all new slugs — prevents two different accounts on the same hostname from colliding on disk (P0 fix)
- **`discover.py`**: Stale `[automation:processing]` lock reclaim after 2 hours; paid jobs query now includes `processing` status so crashed runs are recovered; `_is_stale_processing()` helper added (P0 fix)
- **`worker.py`**: `_mark_paid_processing()` writes `[automation:processing]` lock immediately so concurrent runs skip the job (P0 fix)
- **`pipeline.py`**: Prior free-audit fingerprint exclusions injected into finding prompt for paid runs — prevents duplicate findings when same customer re-buys (P0 dedup fix)
- **`deliver_report.py`**: Attachment size guard — strips PDFs and adds a "reply for transfer link" note when base64-encoded total exceeds 9 MB (P1 fix)
- **`free_audit_lookup.py`**: `recent_delivery()` stale-status filter updated and tested
- **Tests**: 34 new edge-case tests added (31 new + 3 revised), all 280 pass

**Conversion + value-scaling pass:**
- **Launch Readiness Score** (1.0–10.0) added to every report — `compute_readiness_score()` in `pipeline.py`, score badge on verdict block, stored in shareable page data
- **First-user framing** — severity headings and verdict meta reframed as "what your first users will hit"; delivery email opens with same frame
- **Vibe-coding mistakes section** on landing (named, specific real examples replacing generic bullet list)
- **Sample report** upgraded to a visible CTA button in the hero
- **Urgency windows section** — four cards (Product Hunt / investor demo / beta users / real customers) between hero and How It Works
- **"Already ran a scanner?" callout** — positions LaunchLook vs PageLens and VibeDoctor above pricing
- **Tier cards rewritten** on both `index.html` and `webflow.html` — all deliverables listed, cumulative framing, Scale Up badged "Most popular"
- **Wall of Launches** page created (`landing/wall.html`) — empty-state + opt-in CTA
- **Referral credit** added to delivery email (`delivery_pdf.html.j2` + `.txt.j2`)
- **SUCCESS-METRICS.md** created with §0 Lorelight problem-validation test as primary gate
- **VibeDoctor competitive analysis** completed — positioned as complementary, not competing

**Documentation cleanup:**
- Deleted four stale one-time docs (`MANUAL-APPROVAL-2026-05-26.md`, `AGENT-ACTION-LOG-2026-05-26.md`, `SHIPMENT-VERIFICATION-PARTIAL-2026-05-26.md`, `MANUAL-TASKS-PRICE-BUMP.md`)
- `LESSONS-LEARNED.md` updated with 7 new lessons (Part 11)
- `PRODUCT-DECISIONS.md` §9 changelog updated

---

## Your next action (updated May 28, 2026)

**Decide Loom walkthrough duration.** PRODUCT-DECISIONS.md §8 says "5 to 10 minutes" but the old landing page said "30-min". Pick one and update `docs/PRODUCT-DECISIONS.md` §8. The landing cards currently say "Rob walks you through the report on video" without a time — update to the chosen duration.

**Second priority: record the Loom.** Once Pro is live with a real customer, record the Pro-tier Loom. Screen-capture: show the delivery email, click the review link, walk the top 3 findings. Post it above the pricing section on `/`. Estimated +30% Pro checkout conversion.

---

## Shipped today (May 27, 2026)

**Automation pipeline — fully wired, tested, and self-service for review:**
- **AI audit pipeline** end-to-end: Playwright screenshots → crawl → prescreen → security-lite → GPT-4o findings → YAML written
- **3 free audits** and **3 paid audits** (Starter / Scale Up / Pro) processed successfully on test sites
- **OpenAI (`gpt-4o`) wired** — `OPENAI_API_KEY` in `.env`, provider=auto falls back to GPT when no Anthropic key
- **Resend Cloudflare WAF fix** — custom `User-Agent` header in `notify.py` (was HTTP 403 before)
- **Draft-ready emails** now include inline findings, a Notion link, **plus three clickable workflow links**:
  - `http://localhost:8000/review/<slug>` → opens AI review UI for that customer
  - `http://localhost:8000/preview/<slug>` → live HTML preview of the report (same Jinja templates as the PDF)
  - `mailto:` link → pre-composed delivery draft to the customer once you approve
- `ADMIN_EMAIL=romado33@gmail.com`, `FROM_EMAIL=hello@launchlook.app` confirmed working
- **OpenAI structured-output schema fix** — `screenshot_caption` added to `required` array (gpt-4o strict mode)
- **Tally hidden-tier (Q8 replacement)** — all code shipped:
  - Stripe Payment Links get per-tier success URLs (`?tier=starter` / `scale_up` / `pro`)
  - `personalize.js` reads `?tier=`, stores in sessionStorage, forwards to Tally URL
  - `config.js` wired with `tallyPrefill.tier = "tier"`
  - `tally-webhook.py` TIER_MAP updated with hidden-field slug values
  - `thanks.html` shows "Your Starter/Scale Up/Pro checkup" from URL param
  - **Manual Tally step still needed** — see Blocking §1 below
- **Free trial changed 3 → 2 findings** across all copy, emails, config, docs
- **`TIER_NORMALIZE`** extended in `discover.py` to handle all `($XX)` suffix variants
- **`_test_accounts_checkbox`** updated to accept both Notion values and raw slugs
- **`scripts/stripe_payment_links.py`** — new `update-success-urls` subcommand

**Audit UI (new this session):**
- `/review/<slug>` route — direct deep-link into the AI review UI; loads customer YAML even when the server wasn't started with `--review-ai`
- `/preview/<slug>` route — server-side renders the Main Report, Quick Start Guide, or Pre-Launch Checklist HTML using the same Jinja templates as the PDF generator, with a fixed top nav to switch documents

**Landing:**
- Hero trust bar centered
- Desktop/mobile copy clarified throughout (browser width testing, not native apps)
- "Trust gaps" → "trust issues" / "embarrassing bugs"; "AI builders" → "similar platforms"
- FAQ: PageLens comparison question added (links to `/vs-pagelens`)

**Docs:**
- `docs/TALLY-INTAKE-SETUP.md` rewritten with hidden-tier setup guide
- `docs/FREE-AUDIT-WORKFLOW.md`, `docs/AI-AUDIT-PIPELINE.md`, `docs/PRODUCT-DECISIONS.md` updated
- `docs/AUTOMATION-PIPELINE.md` added

**Code hygiene:**
- Ruff lint + format clean across repo (127 tests passing)
- Removed scratch scripts (`_replay_draft_ready_emails.py`, `_check_*` helpers used during diagnosis)

---

## Shipped recently (May 26, 2026)

- Landing simplified to 3 sections; pre-launch checklist bundled on paid tiers
- Verified badge removed; delivery SLA clocks stripped; Plausible removed
- `/sample` → shareable sample report; sample JSON deploys correctly
- `automatic_tax` disabled on all Payment Links; repo cleanup; E2E v3

---

## Your next action

**Record the 60-second Loom** and put it above the pricing section on `/`. This is the single highest-leverage thing left — estimated +30% checkout conversion. Screen-capture: show the email arriving with findings, click the review link, show the report. 60 seconds max.

---

## Blocking — DONE ✅ (2026-05-28)

- [x] `FROM_EMAIL` → `hello@launchlook.app` in Vercel (was `launchlook.com`)
- [x] Tally hidden-tier field added; Q8 deleted; conditionals updated
- [x] Stripe success URLs updated (`?tier=starter/scale_up/pro`)
- [x] Windows Task Scheduler registered — runs every 30 min while logged in
- [x] Site smoke — pages loading, buy buttons wired

**You are in outreach mode.**

---

## Delivery ops

- [ ] Unsuppress `rob@launchlook.app` in Resend dashboard if needed (bounced during testing — safe to ignore since we're using `romado33@gmail.com` as ADMIN_EMAIL now)
- [ ] Old CAD $9 / $29 Stripe Payment Links — deactivate in Dashboard if still active
- [ ] Spot-check checkout: **$19 total only** (no tax line)
- [ ] Delete 2 stale `romado33` test rows in Customers DB once Tally hidden-tier is live (search by email + missing Tally response timestamp)
- [ ] For each completed audit, your workflow is now: start `python scripts/audit_ui.py`, then click the `/review/<slug>` and `/preview/<slug>` links in the draft-ready email → approve findings → click the `mailto:` link in the same email to send delivery

---

## Edge case testing (manual — E2E section I)

These can't be unit-tested automatically. Run them once before your first real customer, then spot-check after any change to the form, webhook, or email code. Full steps are in the E2E checklist at `launchlook.app/e2e` section I.

**Free audit form**
- [ ] Submit bare domain `mysite.com` (no `https://`) → queues normally
- [ ] Submit `http://` URL → queues normally (not rejected)
- [ ] Same email + same URL within 30 days → upsell email arrives, Notion row count stays at 1
- [ ] Same email submitted 4th time in 30 days → blocked with email-rate message (not generic error)
- [ ] Submit with JavaScript disabled → 303 redirect to `/thanks-free-audit` (no blank page)

**Tally hidden tier**
- [ ] Starter buy button → `/thanks?tier=starter` → Tally hidden field receives `starter`
- [ ] Scale Up buy button → `/thanks?tier=scale_up` → Tally hidden field receives `scale_up`
- [ ] Pro buy button → `/thanks?tier=pro` → Tally hidden field receives `pro`
- [ ] Open `/thanks` with no `?tier=` param → Tally still opens, tier is blank in Notion (not a crash)

**Stripe webhook**
- [ ] Resend same `checkout.session.completed` webhook twice from Stripe Dashboard → Notion shows 1 updated row, not 2 rows

**Emails**
- [ ] Open draft-ready founder email in Gmail → HTML renders with 3 clickable buttons; plain-text shows compact mailto (no broken long URL)
- [ ] Click "Open delivery draft →" button → Gmail compose opens with subject + findings pre-filled
- [ ] `FROM_EMAIL` domain verified in Resend → test free-audit submission delivers (not bounced)

**Pipeline / form smoke**
- [ ] Run worker on a site with a contact form → founder email shows `Form smoke: ran ✓`
- [ ] Run worker on a site with no forms → founder email shows `not run (no forms detected)` (not an error)

**Known limitation (no fix needed, just be aware)**
- ⚠️ Two customers with the same email local-part + same hostname get the same YAML slug → second run overwrites first. Mitigation: process one customer at a time, or rename the YAML before queuing the second.

---

## Optional / deferred

- [ ] **Plausible** — only if you want conversion data at ≥10 customers
- [ ] **60-second Loom** on homepage
- [ ] **GitHub PAT** for Pro — only if a Pro buyer asks
- [ ] **PSI_API_KEY** — only at higher audit volume
- [ ] Wire `persist_free_audit_fingerprints` into free-delivery flow (currently manual)

---

## Quick reference

| Item | Value |
|------|--------|
| Intake | `https://tally.so/r/QKOX1A` |
| Tiers | Starter **$19**, Scale Up **$49**, Pro **$99** |
| Admin email | `romado33@gmail.com` |
| Sending email | `hello@launchlook.app` (Resend-verified) |
| Config | `landing/assets/config.js` |
| Run queue | `python scripts/process_audit_queue.py --provider gpt --limit 5` |
| Review draft | `python scripts/audit_ui.py --slug <slug> --review-ai` |
| Stripe tax script | `python scripts/stripe_payment_links.py enable-tax` |
| Stripe tier URLs | `python scripts/stripe_payment_links.py update-success-urls` |

---

## Done = outreach mode

When **Vercel FROM_EMAIL fixed**, **Tally hidden-tier §1**, and **one checkout spot-check** are checked off, you're in outreach mode.
