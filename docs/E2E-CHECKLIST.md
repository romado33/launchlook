# LaunchLook E2E checklist

**Interactive (password + progress):** https://launchlook.app/e2e — set `E2E_CHECKLIST_PASSWORD` in Vercel.

**Local (no password):** open [`docs/e2e-checklist.html`](e2e-checklist.html) from the repo.

Run in **incognito** on desktop, then repeat the paid path on your phone.  
Tiers: **Starter $19** · **Scale Up $49** · **Pro $99**.

---

## Go-live ready when

- [ ] Free audit → Resend email + Notion Free Audit row
- [ ] Paid Starter → Stripe + `/thanks` + Tally + email to you + Notion intake
- [ ] Scale Up conditional test-account questions work (if you sell that tier)
- [ ] You can generate + send PDFs for a test customer

---

## 0. Pre-flight (before testing)

- [ ] Vercel production on latest `main` (hard-refresh launchlook.app)
- [ ] Vercel env: `STRIPE_WEBHOOK_SECRET`, `NOTION_TOKEN`, `NOTION_CUSTOMERS_DB_ID`, `NOTION_FREE_AUDIT_DB_ID`, `NOTION_CONFIDENCE_CHECK_DB_ID`, `RESEND_API_KEY`, `TALLY_WEBHOOK_TOKEN`
- [ ] `E2E_CHECKLIST_PASSWORD` set; https://launchlook.app/e2e unlocks
- [ ] `hello@launchlook.app` forwards to an inbox you check
- [ ] Tally `QKOX1A` published (not draft)
- [ ] Tally tier question: **Starter $19 / Scale Up $49 / Pro $99**; Q7 includes **Webflow**
- [ ] Tally notifications → `hello@launchlook.app`
- [ ] Tally after-submit redirect → `https://launchlook.app/thanks`
- [ ] Tally webhook URL with `?t=` token; test event returns 200
- [ ] Stripe **live mode** for real-money smoke (or use test mode knowingly)
- [ ] `landing/assets/config.js` URLs match Dashboard (`starter`, `scaleup`, `pro`, `handoff`, `saboteur`, `saboteurDiscounted` — **no `reverify`**)
- [ ] Active Payment Links: success URL → `https://launchlook.app/thanks`
- [ ] **Stripe Tax registrations** complete (regions you collect in)
- [ ] **automatic_tax** on active links: `python scripts/stripe_payment_links.py enable-tax`
- [ ] Dead Payment Links **deactivated**: $9 re-verify badge, old CAD $9/$29 tiers

---

## A. Site smoke (~8 min)

- [ ] `/` loads; pricing shows $19 / $49 / $99 with **bulleted** tier features
- [ ] Scale Up card has **no** “Popular” badge or accent bar
- [ ] **Get Starter / Scale Up / Pro** open `buy.stripe.com` (not grayed `#` placeholders)
- [ ] **Handoff Report $49** add-on link in pricing opens Stripe
- [ ] `/faq`, `/webflow`, `/thanks`, `/thanks-free-audit`, `/privacy`, `/terms` → 200
- [ ] Header tagline **“One last look before you launch.”** on `/`, `/faq`, `/webflow` (hidden &lt;640px by design)
- [ ] Top nav: **Pricing, FAQ, Webflow** only (free audit is hero/footer, not top nav)
- [ ] `/sample` → **Sparkle Marketplace** report (findings visible — not “report not found”)
- [ ] `/data/reports/jane-sparkle-marketplace.json` → 200
- [ ] `/checklist` redirects to `/`
- [ ] Footer **Sample report** works; **no** GitHub link; privacy/terms have **no** dead `/checklist` link
- [ ] Pricing mentions fix prompts on paid tiers; **Fix Check** not sold on landing (post-delivery only)

---

## B. Free audit path (~10 min)

- [ ] Homepage form: URL + email submits successfully
- [ ] Invalid URL shows **inline error** on homepage — does not redirect to thanks
- [ ] Success → `/thanks-free-audit`
- [ ] Resend confirmation email arrives
- [ ] Notion Free Audit DB: new row (status queued)
- [ ] (Optional) Same email+URL resubmit → duplicate/upsell behavior

---

## C. Paid path — Starter $19 (~15 min)

- [ ] **Get Starter** → Stripe Checkout shows **$19 USD**
- [ ] Checkout shows **$19 only** (no automatic tax line)
- [ ] After pay → `https://launchlook.app/thanks`
- [ ] Stripe receipt email arrives
- [ ] Notion Customers: row with **Starter Package** tier
- [ ] **Complete intake** opens Tally (`QKOX1A`), not mailto-only
- [ ] Submit Starter intake — no test-account password fields
- [ ] Tally notification email to `hello@launchlook.app`
- [ ] Notion Customers: intake fields + intake received (via tally-webhook)

**Note:** Post-purchase welcome email from your app is **not** automated — Stripe receipt only.

---

## D. Paid path — Scale Up $49 (optional, ~10 min)

- [ ] Checkout $49 → `/thanks` → Tally
- [ ] Tally tier question shows **Scale Up $49** (not old Full/Scale names)
- [ ] Test-account questions only for Scale Up + “Yes”
- [ ] Notion: **Scale Up Package** tier; notes if test accounts provided

---

## E. Stripe webhook sanity (~2 min)

- [ ] Stripe Dashboard → webhook → send test `checkout.session.completed` → 200
- [ ] After real test payment: event succeeded (no repeated failures)

---

## F. Delivery dry-run (optional, ~10 min)

```powershell
python scripts/deliver_report.py --customer customers/<your-test>.yaml
python scripts/deliver_report.py --customer customers/<your-test>.yaml --send
```

- [ ] Main Report + QSG + Pre-Launch Checklist PDFs render
- [ ] `--send` delivers to test inbox via Resend
- [ ] PDF footer mentions **Fix Check** (“reply recheck”), not a landing pricing row

---

## G. Add-ons (only if testing those SKUs)

- [ ] Handoff $49 checkout → webhook / manual handoff delivery
- [ ] Fix Check $19 checkout → Confidence Checks Notion DB row
- [ ] Old **$9 re-verify** Payment Link inactive (Verified badge removed; not in `config.js`)

---

## H. Mobile pass (~5 min)

- [ ] Homepage free audit form works on phone
- [ ] One Starter checkout + Tally intake on phone

---

## Not E2E blockers (track elsewhere)

| Item | Where to track |
|------|----------------|
| Plausible / Vercel Analytics | Deferred — funnel in **Notion** (Free Audit + Customers DBs) |
| Hero screenshot / testimonial quotes | After deliveries #1–5 on homepage |
| Mobile header tagline hidden | Intentional below 640px width |
| Webflow footer “Free 3-finding audit” | Intentional link to vibe-coder hero |
| Webflow hero still links to `/r/jane-sparkle-marketplace.html` | Low priority; `/sample` works on main SKU |

---

*Last updated: May 27, 2026 · Source of interactive items: `landing/assets/e2e-checklist-data.js` · See also [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md)*
