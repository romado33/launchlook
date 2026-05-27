# Everything left for Rob — LaunchLook

**Last updated:** May 27, 2026 (evening — refactor + review session)
**Site:** https://launchlook.app · **Repo:** `romado33/launchlook`

This file is the **source of truth** for what you still need to do manually. Product/code decisions live in [`PRODUCT-DECISIONS.md`](PRODUCT-DECISIONS.md).

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

## Your next 3 actions (do in this order)

1. **Fix Vercel `FROM_EMAIL`** — currently set to `hello@launchlook.com` (unverified in Resend → all production emails silently failing). Change to `hello@launchlook.app` in Vercel Dashboard → Settings → Environment Variables.
2. **Tally hidden-tier setup** (~10 min in QKOX1A editor) — see §1 below.
3. **Run Stripe success-URL update** once locally: `python scripts/stripe_payment_links.py update-success-urls`

---

## Blocking — before cold outreach

### 1. Tally hidden-tier setup (~10 min) — **you**

Replace Q8 ("Which tier?") with a hidden field populated from the Stripe redirect URL.

- [ ] Open `https://tally.so/r/QKOX1A` in edit mode
- [ ] Add **Hidden field**, label `tier`, URL-param key `tier`
- [ ] Delete **Q8**
- [ ] Q9–Q12 conditionals: change "show when Q8 = …" → "show when [hidden tier] = `scale_up` OR `pro`"
- [ ] Run: `python scripts/stripe_payment_links.py update-success-urls` (updates 3 Stripe links)

Full guide: [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md) → "Hidden-tier setup" section.

### 2. Vercel environment variables (~5 min) — **you**

- [ ] `FROM_EMAIL` → `hello@launchlook.app` (currently `launchlook.com` — unverified, breaks all emails)
- [ ] `ADMIN_EMAIL` → `romado33@gmail.com`
- [ ] Confirm `OPENAI_API_KEY` is set (automation worker uses it locally; not needed on Vercel unless running pipeline there)
- [ ] Confirm present: `STRIPE_WEBHOOK_SECRET`, `NOTION_TOKEN`, `NOTION_CUSTOMERS_DB_ID`, `NOTION_FREE_AUDIT_DB_ID`, `RESEND_API_KEY`, `TALLY_WEBHOOK_TOKEN`

### 3. Schedule local automation worker (~5 min) — **you**

Run the worker automatically so new free-audit signups process without you opening a terminal.

```powershell
# Register Windows Task Scheduler entry (run this once in an admin PowerShell):
schtasks /create /tn "LaunchLook Audit Queue" /tr "python C:\Users\RobDods\Apps\Cursor\onceover\scripts\process_audit_queue.py --provider gpt --limit 5" /sc minute /mo 30 /st 00:00 /ru SYSTEM
```

Or use the `.ps1` helper at `scripts/schedule_worker.ps1`.

### 4. Site smoke — **run in incognito**

- [x] Code/deploy: free-audit JS wired; pricing bullets; sample report public
- [ ] You confirm: `/`, `/faq`, `/webflow`, `/thanks`, `/thanks-free-audit` → load
- [ ] You confirm: Starter / Scale Up / Pro buy buttons → `buy.stripe.com`
- [ ] Hard-refresh after latest deploy (Ctrl+Shift+R)

---

## Delivery ops

- [ ] Unsuppress `rob@launchlook.app` in Resend dashboard if needed (bounced during testing — safe to ignore since we're using `romado33@gmail.com` as ADMIN_EMAIL now)
- [ ] Old CAD $9 / $29 Stripe Payment Links — deactivate in Dashboard if still active
- [ ] Spot-check checkout: **$19 total only** (no tax line)
- [ ] Delete 2 stale `romado33` test rows in Customers DB once Tally hidden-tier is live (search by email + missing Tally response timestamp)
- [ ] For each completed audit, your workflow is now: start `python scripts/audit_ui.py`, then click the `/review/<slug>` and `/preview/<slug>` links in the draft-ready email → approve findings → click the `mailto:` link in the same email to send delivery

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
