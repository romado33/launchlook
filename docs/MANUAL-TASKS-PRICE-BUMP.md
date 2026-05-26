# Manual External Tasks — Price Bump + Pro Tier Launch

These are the manual actions Rob needs to complete in external services (Stripe,
Tally, Notion) to fully ship the price bump and the new Pro tier. The codebase
changes (landing pages, comparison table, FAQ, deliver_report.py cap validator,
docs) are handled automatically by the price-bump worker once it runs.

**When to do these:** After the price-bump worker lands its commit on `main`.
Until then, the new prices and Pro tier copy aren't live anywhere customer-facing,
so there's no rush to update Stripe/Tally/Notion first.

---

## Checklist

| Done | Manual external task | Where | Time |
|---|---|---|---|
| ☐ | Create new **Pro Package** product in Stripe ($99) | Stripe Dashboard → Products | ~3 min |
| ☐ | Add **Pro Package** payment link | Stripe → Payment Links | ~2 min |
| ☐ | Update **Starter Package** product price ($9 → $19) | Stripe → Products | ~1 min |
| ☐ | Update **Full Package** product price ($29 → $49) | Stripe → Products | ~1 min |
| ☐ | Update Tally form to add **Pro Package** tier option | Tally form editor | ~3 min |
| ☐ | Update Notion DB to allow **Pro Package** as a tier value | Notion DB schema | ~1 min |

**Total time:** ~11 minutes once you sit down to do them.

---

## Tips per task

### Stripe — new Pro Package product

Set the product description to match the new copy (worker will draft this; copy
the exact wording from the updated `landing/index.html` Pro pricing card so the
Stripe receipt matches the landing page promise).

Suggested baseline description:

> Comprehensive pre-launch audit for vibe-coded apps. Up to 40 findings across
> every category, AI-powered analysis with founder-curated quality. Includes
> cross-user data check (2 test accounts), integrations review, Quick Start
> Guide PDF, and a 30-minute Loom walkthrough. Delivered within 24 hours
> (usually within 12).

### Stripe — payment link redirect

Don't forget to set the **after-payment redirect** to `https://launchlook.app/thanks`
in the payment link's "After payment" settings, same as you did for Starter and
Full. Otherwise customers see Stripe's default confirmation page instead of the
intake-form CTA on `/thanks`.

### Stripe — updating Starter and Full prices

Stripe doesn't let you edit a price; you have to:

1. Create a new price ($19 / $49) on the existing product
2. Set the new price as default
3. Archive the old price (don't delete — keeps historical receipts intact)
4. Verify the existing payment link automatically uses the new price (it should,
   if it references the product not the specific price)

### Tally — Pro Package tier option

The intake form currently asks which tier the customer purchased. Add **Pro
Package** as a third option to that question. Also extend the conditional logic
so the test-account-credential fields (currently shown for Full Package) ALSO
show for Pro Package — since Pro includes the cross-user data check.

### Notion — Pro Package tier value

In the Customers database, the `Tier` property is currently a Select with two
options (Starter Package, Full Package). Add **Pro Package** as a third option.
Pick a distinct color so Pro customers stand out in the dashboard.

Also: the Stripe webhook (`api/stripe-webhook.py`) infers tier from amount in
cents. After the price bump it'll need updating to recognize:

- 1900 cents → Starter Package
- 4900 cents → Full Package
- 9900 cents → Pro Package

The price-bump worker should handle this code change; just verify it after the
commit lands.

---

## Verification

After completing all manual tasks, run one end-to-end test purchase per tier
(refund afterwards) to confirm:

- [ ] Stripe checkout shows the correct price for each tier
- [ ] After-payment redirect lands on `/thanks` for each tier
- [ ] Tally form shows the correct tier-conditional fields when you select Pro
- [ ] Stripe webhook fires and creates a Notion row with `Tier: Pro Package`
- [ ] Stripe receipt email matches the landing page copy

Total verification time: ~10 minutes for all three tiers.
