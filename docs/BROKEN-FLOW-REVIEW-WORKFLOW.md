# Broken Flow Review — workflow

## What it is

A **$49 post-launch add-on** for founders who already shipped but have **one
named flow** that fails (signup, checkout, onboarding blank screen, form with
no email, etc.). Not a full Starter / Scale Up / Pro audit.

Deliverable:

- Short PDF scoped to that flow
- Up to **~5 focused findings**, each with paste-into-builder fix text
- Desktop + mobile walkthrough of the named path only

## What it is not

- Full-site pre-launch audit (10 / 30 / 40 findings)
- Data isolation check, User Guide, Loom, Handoff Report, or Fix Check bundle
- Listed on the main landing pricing grid (FAQ `#broken-flow-review` + footer link only)

## Stripe

1. Create a **$49 USD** Payment Link in Stripe Dashboard (or `scripts/stripe_payment_links.py` when wired).
2. **Required metadata:** `product` = `broken_flow_review`
3. Paste the URL into `landing/assets/config.js` → `stripe.brokenFlowReview` (or `config.local.js`).

**Why metadata is mandatory:** `amount_total` = 4900 collides with Scale Up Package and Handoff Report add-on. The webhook routes via `is_broken_flow_review_session()` in `api/stripe-webhook.py`, same pattern as Handoff and Fix Check.

On `checkout.session.completed`:

- `handle_broken_flow_review_purchase` upserts Notion with `[broken_flow_review_paid]` note
- Admin alert email fires (same `_send_purchase_alert` path as Handoff)

## Customer journey

1. Pay via FAQ CTA or footer link → `/thanks` (standard)
2. Complete Tally intake — **name the broken flow** in Launch Concern / notes
3. Rob delivers scoped PDF within 48 hours (manual delivery until a dedicated template exists)

## Ops checklist

- [ ] Payment Link live with `product=broken_flow_review`
- [ ] URL in `config.js` or `config.local.js`
- [ ] Test checkout in Stripe test mode → webhook returns `broken_flow_review_recorded`
- [ ] Intake form captures: live URL, platform, **which flow is broken**, test accounts if needed

## Related docs

- `docs/PRODUCT-DECISIONS.md` §1 add-ons table
- `docs/HANDOFF-REPORT-WORKFLOW.md` (different $49 product — dev handoff, not flow triage)
