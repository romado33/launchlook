# LaunchLook — Self-checkup (LaunchLook.app)

> **Tier:** Practice audit (Starter Package lens) · **URL:** https://launchlook.app/ · **Date:** May 2026

---

## Summary

**Overall verdict:** 🟡 Fix a few things before heavy cold outreach

The homepage is strong — clear value prop, Starter Package / Ship Package pricing, sample teaser, and real privacy/terms content. The main gaps are **routing** (several clean URLs 404 while `.html` paths work), **post-pay intake** still on email fallback until Tally is wired, and a few **trust polish** items you'd flag on any vibe-coded site.

**6 findings** below (what LaunchLook would report to a paying customer).

---

## 🔴 Critical

### 1 — `/sample`, `/thanks`, `/checklist` return 404 (clean URLs)

**What we saw**  
`https://launchlook.app/sample` and `/thanks` return Vercel 404.  
`https://launchlook.app/sample.html` returns 200.

**Why it matters**  
Homepage links to `/sample` twice as a trust signal. Broken sample = worse than no sample.

**Fix**  
In `landing/vercel.json`, add rewrites from extensionless paths to `.html` (or fix `cleanUrls` on Vercel). Redeploy and verify all footer links without `.html`.

---

## 🟠 High

### 2 — Post-payment intake not on Tally yet

**What we saw**  
`intakeFormUrl` is still empty in `config.js`. Thanks page falls back to mailto.

**Why it matters**  
Pay → friction → email is OK for day 1, but strangers expect a form immediately after Stripe.

**Fix**  
Publish Tally form from `templates/intake-form-spec.md`, paste URL into `config.js`, test Stripe → `/thanks` → Tally.

### 3 — "Who's behind this" lacked a human name (fixed in repo)

**What we saw**  
Anonymous "technical writer" copy — fine for $9, weak for Ship Package + test credentials.

**Fix**  
Use first name ("Rob") + one credential line. Optional: LinkedIn link.

### 4 — Verify `og.png` loads in link previews

**What we saw**  
`og:image` points to `/images/og.png`. Confirm 200 after deploy (file added in repo).

**Fix**  
Share link in Slack/iMessage once; use opengraph.xyz if preview is blank.

---

## 🟡 Medium

### 5 — Pricing badge on wrong tier (fixed in repo)

**What we saw**  
"Best before launch" on Ship Package while Starter had no anchor — confusing for first-time readers.

**Fix**  
"Most popular" on Ship Package; keep Starter without competing badge.

### 6 — Dogfood irony: you sell mobile checks

**What we saw**  
Product promises phone-width review; homepage should pass tap-target and stacking checks on a real device.

**Fix**  
15-minute pass on iPhone: pricing grid, CTAs ≥44px, FAQ accordions.

---

## 🟢 What's already good

- Plain-English hero and platform breadth ("and more")
- Starter Package / Ship Package naming matches Stripe intent
- Privacy & terms are real LaunchLook policies (not Onceover leftovers)
- Stripe URLs in `config.js`; pricing CTAs wire via `apply-config.js`
- Public checklist repo linked from config
- Free checklist page is substantial (`/checklist.html`)

---

## What a paid customer would get

| Tier | For LaunchLook.app today |
|------|---------------------------|
| **Starter Package $9** | Findings 1–4 + 6 + QSG for "how to use LaunchLook" |
| **Ship Package $29** | Above + deeper pass; N/A cross-user (no auth on marketing site) |

---

*Practice audit for internal use. Re-run after each production deploy.*
