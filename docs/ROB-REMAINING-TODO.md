# Everything left for Rob — LaunchLook

**Last updated:** May 27, 2026  
**Site:** https://launchlook.app · **Repo:** `romado33/launchlook`

This file is the **source of truth** for what you still need to do manually. Product/code decisions live in [`PRODUCT-DECISIONS.md`](PRODUCT-DECISIONS.md).

---

## Shipped recently (May 26–27, 2026)

**Product / landing**
- Landing **simplified** to 3 sections (hero → how it works → pricing); wider `page-wrap` column; no standalone `/checklist` page
- **Pre-Launch Checklist PDF** bundled on every paid tier (not sold separately on the site)
- **Verified badge** removed end-to-end (`reverify` dropped from `config.js`)
- **Delivery SLA clocks** removed from customer copy (“when it’s ready, usually within a few days”)
- **Plausible script** removed (CTA classes kept for easy re-enable)
- **GitHub auto-issues** removed from Pro promise (scripts dormant in repo)
- **Persona names** hidden on customer reports (internal scanning unchanged)
- **Fix Check** (was Confidence Check) — offer only in post-delivery email/PDF footer, not on landing pricing
- `/sample` → redirects to `/r/jane-sparkle-marketplace.html`; sample JSON deploys correctly
- Header tagline on all pages; top nav trimmed (no “Free audit” in nav); no Scale Up “Popular” badge
- Free-audit form wired to JS (`data-free-audit-form`); hero/footer sample links use `/sample`
- `privacy` / `terms` footers fixed (no dead `/checklist` link)

**Ops / infra (code)**
- **`automatic_tax` disabled** on all 6 API Payment Links (listed price at checkout; no Stripe Tax)
- Repo cleanup: removed `checklist_tokens.json`, external GitHub checklist mirror, dead config keys
- **E2E checklist v3** — https://launchlook.app/e2e · [`E2E-CHECKLIST.md`](E2E-CHECKLIST.md) · `landing/assets/e2e-checklist-data.js`
- `followup-d3` / `followup-d7` email templates removed

---

## Your next 3 actions

1. **Tally `QKOX1A`** — In the editor: tier names **Starter $19 / Scale Up $49 / Pro $99**, Webflow in Q7, conditional logic (Scale Up + Pro test-account questions only), notifications → `hello@launchlook.app`, after-submit → `https://launchlook.app/thanks`. Paste buffers: [`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) · [`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt).
2. **Run E2E v3** — https://launchlook.app/e2e (`E2E_CHECKLIST_PASSWORD` in Vercel). Work through all sections in incognito; one real Starter checkout if you’re comfortable with a live charge.
3. **Deactivate old Stripe links** — CAD $9 / $29 tiers if still active (Dashboard).

---

## Blocking — before cold outreach

### 1. Tally intake (~20 min) — **you**

- [ ] Form `QKOX1A` published (not draft)
- [ ] Tier question matches **Starter / Scale Up / Pro** at $19 / $49 / $99
- [ ] Q7 includes **Webflow**
- [ ] Conditional logic: test-account questions for Scale Up + Pro only
- [ ] Thank-you redirect → `https://launchlook.app/thanks`
- [ ] Notifications → `hello@launchlook.app`

Guides: [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md) · API rebuild: `python scripts/tally_create_intake.py`

### 2. Stripe (~10 min) — **mostly done in code; verify in Dashboard**

- [x] `config.js` wired: `starter`, `scaleup`, `pro`, `handoff`, `saboteur`, `saboteurDiscounted` (no `reverify`)
- [x] `automatic_tax` on active Payment Links (API, May 27)
- [x] $9 re-verify Payment Link **inactive** in Stripe
- [ ] **Stripe Tax registrations** complete for your selling regions
- [ ] Spot-check checkout: billing address + tax line when applicable
- [ ] Old CAD $9 / $29 Payment Links **deactivated** (if still active)
- [ ] Success URL on all live links → `https://launchlook.app/thanks`

### 3. Email & Vercel env (~15 min) — **you**

- [ ] `hello@launchlook.app` forwards to an inbox you check
- [ ] Test free-audit email + Tally notification received
- [ ] Resend domain verified
- [ ] Vercel env present: `STRIPE_WEBHOOK_SECRET`, `NOTION_TOKEN`, `NOTION_CUSTOMERS_DB_ID`, `NOTION_FREE_AUDIT_DB_ID`, `NOTION_CONFIDENCE_CHECK_DB_ID`, `RESEND_API_KEY`, `TALLY_WEBHOOK_TOKEN`, `E2E_CHECKLIST_PASSWORD`

### 4. Site smoke — **run via /e2e or quick manual pass**

- [x] Code/deploy: sample report JSON public; `/checklist` → `/`; free-audit JS; pricing bullets
- [ ] You confirm in incognito: `/`, `/faq`, `/webflow`, `/thanks`, `/thanks-free-audit`, `/privacy`, `/terms`, `/sample` → sample findings visible
- [ ] You confirm: Get Starter / Scale Up / Pro → `buy.stripe.com` (not grayed `#`)
- [ ] Hard-refresh after latest deploy (Ctrl+Shift+R)

---

## First paying customer delivery

- [ ] `python scripts/customers_track.py add` after each payment
- [ ] Notion **LaunchLook Ops**: Customers DB — **Scale Up Package** + **Webflow** on tier/platform selects if missing
- [ ] Deliver: Main Report + QSG + Pre-Launch Checklist PDFs (`scripts/deliver_report.py`)
- [ ] Post-delivery email mentions **Fix Check** (reply recheck), not a landing upsell

---

## Optional / deferred

- [ ] **Plausible** — only if you want conversion data at ≥10 customers ([`PRODUCT-DECISIONS.md`](PRODUCT-DECISIONS.md))
- [ ] **60-second Loom** on homepage (replaces text explainer when recorded)
- [ ] **GitHub PAT** for Pro — only if a Pro buyer asks
- [ ] **PSI_API_KEY** — only at higher audit volume
- [ ] Webflow hero sample link → `/sample` (main site already uses `/sample`; low priority)
- [ ] Webflow community outreach ([`OUTREACH-PLAYBOOK.md`](OUTREACH-PLAYBOOK.md) §7b)

---

## Quick reference

| Item | Value |
|------|--------|
| Intake | `https://tally.so/r/QKOX1A` |
| Tiers | Starter **$19**, Scale Up **$49**, Pro **$99** |
| Support | hello@launchlook.app |
| Config | `landing/assets/config.js` |
| E2E | https://launchlook.app/e2e · [`E2E-CHECKLIST.md`](E2E-CHECKLIST.md) |
| Stripe tax script | `python scripts/stripe_payment_links.py enable-tax` |
| Build | `node scripts/copy-landing-for-vercel.mjs` → `dist/` |

---

## Done = outreach mode

When **Tally §1**, **Stripe registrations + one checkout spot-check**, **email/env §3**, and **E2E v3** are checked off, you’re in outreach mode — not “one more site tweak” mode.
