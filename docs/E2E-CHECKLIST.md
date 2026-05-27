# LaunchLook E2E checklist

**Interactive version (saves progress in your browser):** open [`docs/e2e-checklist.html`](e2e-checklist.html) in Chrome/Edge — double-click the file or drag it into a browser tab.

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
- [ ] Vercel env: `STRIPE_WEBHOOK_SECRET`, `NOTION_TOKEN`, `NOTION_CUSTOMERS_DB_ID`, `NOTION_FREE_AUDIT_DB_ID`, `RESEND_API_KEY`, `TALLY_WEBHOOK_TOKEN`
- [ ] `hello@launchlook.app` forwards to an inbox you check
- [ ] Tally `QKOX1A` published (not draft)
- [ ] Tally notifications → `hello@launchlook.app`
- [ ] Tally after-submit redirect → `https://launchlook.app/thanks`
- [ ] Tally webhook URL with `?t=` token; test event returns 200

---

## A. Site smoke (~5 min)

- [ ] `/` loads; pricing shows $19 / $49 / $99
- [ ] `/faq`, `/webflow`, `/thanks`, `/privacy`, `/terms` → 200
- [ ] `/r/jane-sparkle-marketplace.html` loads
- [ ] `/sample` redirects to sample report
- [ ] `/checklist` redirects to `/`
- [ ] Footer GitHub link works
- [ ] Pricing mentions fix prompts on all paid tiers

---

## B. Free audit path (~10 min)

- [ ] Homepage form: URL + email submits successfully
- [ ] Success message or redirect to `/thanks-free-audit`
- [ ] Resend confirmation email arrives
- [ ] Notion Free Audit DB: new row (status queued)
- [ ] (Optional) Same email+URL resubmit → duplicate/upsell behavior

---

## C. Paid path — Starter $19 (~15 min)

- [ ] **Get Starter** → Stripe Checkout shows $19
- [ ] After pay → lands on `https://launchlook.app/thanks`
- [ ] Stripe receipt email arrives
- [ ] Notion Customers: row with Starter Package tier
- [ ] **Complete intake** opens Tally (`QKOX1A`), not mailto-only
- [ ] Submit Starter intake — no test-account password fields
- [ ] Tally notification email to `hello@launchlook.app`
- [ ] Notion Customers: intake fields + intake received (via tally-webhook)

**Note:** Post-purchase welcome email from your app is **not** automated — Stripe receipt only.

---

## D. Paid path — Scale Up $49 (optional, ~10 min)

- [ ] Checkout $49 → `/thanks` → Tally
- [ ] Tier question shows Scale Up $49
- [ ] Test-account questions only for Scale Up + “Yes” answer
- [ ] Notion: Scale Up Package tier; notes if test accounts provided

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
- [ ] PDF footer mentions Fix Check (“reply recheck”), not landing add-on

---

## G. Add-ons (only if testing those SKUs)

- [ ] Handoff $49 checkout → Notion / manual handoff delivery
- [ ] Fix Check $19 checkout → Confidence Checks Notion DB row
- [ ] Old **$9 re-verify badge** link deactivated (feature removed)

---

## H. Mobile pass (~5 min)

- [ ] Homepage free audit form works on phone
- [ ] One Starter checkout + Tally intake on phone

---

*Last updated: May 27, 2026 · See also [`ROB-REMAINING-TODO.md`](ROB-REMAINING-TODO.md)*
