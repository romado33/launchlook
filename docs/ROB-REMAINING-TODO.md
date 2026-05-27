# Everything left for Rob — LaunchLook

**Last updated:** May 27, 2026  
**Site:** https://launchlook.app · **Repo:** `romado33/launchlook`

This file is the **source of truth** for what you still need to do manually. Product/code decisions live in [`PRODUCT-DECISIONS.md`](PRODUCT-DECISIONS.md).

---

## Shipped recently (May 26–27, 2026)

- Landing **simplified** to 3 sections (hero → how it works → pricing); wider `page-wrap` column; no standalone `/checklist` page
- **Pre-Launch Checklist PDF** bundled on every paid tier (not sold separately on the site)
- **Verified badge** removed end-to-end
- **Delivery SLA clocks** removed from customer copy (“when it’s ready, usually within a few days”)
- **Plausible script** removed (CTA classes kept for easy re-enable)
- **GitHub auto-issues** removed from Pro promise (scripts dormant in repo)
- **Persona names** hidden on customer reports (internal scanning unchanged)
- **Fix Check** (was Confidence Check) — offer only in post-delivery email/PDF footer, not on landing pricing
- `/sample` → redirects to `/r/jane-sparkle-marketplace.html`
- `followup-d3` / `followup-d7` email templates removed

---

## Your next 3 actions

1. **Tally `QKOX1A`** — In the editor: update tier names (Starter $19 / Scale Up $49 / Pro $99), add Webflow to Q7, fix conditional logic (Scale Up + Pro test-account questions, not “Full Package”), notifications → `hello@launchlook.app`, after-submit → `https://launchlook.app/thanks`. Paste buffers: [`TALLY-PASTE-ONLY.txt`](TALLY-PASTE-ONLY.txt) · [`TALLY-INTAKE-PASTE.txt`](TALLY-INTAKE-PASTE.txt) (update SLA + credential wording to match site before pasting).
2. **Stripe** — Confirm Payment Links in `landing/assets/config.js` match live $19 / $49 / $99 products. **Deactivate** dead links: old $9/$29 tiers, **$9 re-verify badge** (feature removed). Keep Fix Check ($19 / $9 within 14 days) and Handoff ($49) links.
3. **End-to-end test** — Incognito: free audit form → paid checkout → `/thanks` → Tally intake → email arrives at `hello@launchlook.app`.

---

## Blocking — before cold outreach

### 1. Tally intake (~20 min)

- [ ] Form `QKOX1A` published (not draft)
- [ ] Tier question matches **Starter / Scale Up / Pro** at $19 / $49 / $99
- [ ] Q7 includes **Webflow**
- [ ] Conditional logic: test-account questions for Scale Up + Pro only
- [ ] Thank-you redirect → `https://launchlook.app/thanks`
- [ ] Notifications → `hello@launchlook.app`

Guides: [`TALLY-INTAKE-SETUP.md`](TALLY-INTAKE-SETUP.md) · API rebuild: `python scripts/tally_create_intake.py`

### 2. Stripe Payment Links (~10 min)

- [ ] `config.js` URLs work for `starter`, `scaleup`, `pro`, `handoff_report`, Fix Check SKUs
- [ ] Success URL → `https://launchlook.app/thanks`
- [ ] Dead Payment Links archived in Stripe Dashboard

### 3. Email (~15 min)

- [ ] `hello@launchlook.app` forwards to an inbox you check
- [ ] Test send + Tally notification received
- [ ] Resend domain verified; `STRIPE_WEBHOOK_SECRET` + Notion DB IDs in Vercel

### 4. Smoke URLs

- [ ] `/`, `/faq`, `/webflow`, `/thanks`, `/privacy`, `/terms`, `/r/jane-sparkle-marketplace.html` → 200
- [ ] `/sample` → redirects to sample report
- [ ] Hard-refresh homepage after deploy (Ctrl+Shift+R)

---

## First paying customer delivery

- [ ] `python scripts/customers_track.py add` after each payment
- [ ] Notion **LaunchLook Ops**: Customers DB — add **Scale Up Package** + **Webflow** to select options if missing
- [ ] Deliver: Main Report + QSG + Pre-Launch Checklist PDFs (`scripts/deliver_report.py`)
- [ ] Env: `NOTION_FREE_AUDIT_DB_ID`, `NOTION_CONFIDENCE_CHECK_DB_ID` on Vercel

---

## Optional / deferred

- [ ] **Plausible** — only if you want conversion data at ≥10 customers ([§ in old notes below — script is off, classes dormant](PRODUCT-DECISIONS.md))
- [ ] **60-second Loom** on homepage (replaces text explainer when recorded)
- [ ] **GitHub PAT** for Pro — only if a Pro buyer asks (`GITHUB_PAT` in `.env.example` future-use section)
- [ ] **PSI_API_KEY** — only at higher audit volume
- [ ] Webflow community outreach ([`OUTREACH-PLAYBOOK.md`](OUTREACH-PLAYBOOK.md) §7b)

---

## Quick reference

| Item | Value |
|------|--------|
| Intake | `https://tally.so/r/QKOX1A` |
| Tiers | Starter **$19**, Scale Up **$49**, Pro **$99** |
| Support | hello@launchlook.app |
| Config | `landing/assets/config.js` |
| Build | `node scripts/copy-landing-for-vercel.mjs` → `dist/` |

---

*When §1–4 blocking items are done, you’re in outreach mode — not “one more site tweak” mode.*
