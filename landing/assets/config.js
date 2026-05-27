/**
 * Site config — copy to config.local.js and fill in real values.
 * config.local.js is gitignored; falls back to placeholders if missing.
 */
window.LAUNCHLOOK_CONFIG = {
  domain: "launchlook.app",
  supportEmail: "hello@launchlook.app",
  // Verified live via Tally API 2026-05-26 (2 submissions on file).
  // The prior "9qodVE" slug returns HTTP 404 both via API and at
  // https://tally.so/r/9qodVE in incognito — replaced with the real
  // form id "QKOX1A" (status: PUBLISHED). See
  // docs/AGENT-ACTION-LOG-2026-05-26.md NEEDS YOUR APPROVAL item 3 for
  // the full audit trail, in case 9qodVE was supposed to live in a
  // different Tally workspace and just lost its share.
  intakeFormUrl: "https://tally.so/r/QKOX1A",
  // The prior "Y5xO5J" Tally slug also returned 404. Falling back to
  // the existing static thanks page rather than a non-existent Tally
  // form. Replace if/when a branded post-intake confirmation form is
  // created (it's a UI-only task; Tally API has no form-mutation
  // endpoint on this plan).
  tallyThanksUrl: "https://launchlook.app/thanks",
  stripe: {
    // Starter Package $19 USD main-tier Payment Link (created 2026-05-26).
    // Stripe Product prod_UaZvTiEzXRtvkT / Price price_1TbOlzBxCiPye3m0bd7mDaLj.
    // Metadata: product=starter_package, tier=starter. Webhook routes via
    // CENTS_TO_TIER (1900 -> Starter Package) since none of the add-on
    // metadata gates (handoff_report / confidence_check) match.
    starter: "https://buy.stripe.com/28EdR81OlbU00p51u83cc08",
    // Scale Up Package $49 USD main-tier Payment Link (created 2026-05-26).
    // Stripe Product prod_UaZvI1jMiz3qQq / Price price_1TbOm0BxCiPye3m0mbEUxjcU.
    // Metadata: product=scale_up_package, tier=scale_up. Webhook routes via
    // CENTS_TO_TIER (4900 -> Scale Up Package). The metadata.product value
    // is "scale_up_package", NOT "handoff_report", so is_handoff_report_session
    // returns False and the $49 add-on collision is avoided.
    scaleup: "https://buy.stripe.com/7sY4gy0KhaPWfjZa0E3cc09",
    // Legacy CAD Payment Links (prod_UZ48FKGhAH3ANB, prod_UZ49fFi5Clxxgk)
    // remain active in Stripe for historical receipt continuity but are no
    // longer wired to any customer surface.
    // Pro Package $99 USD Payment Link (created 2026-05-26).
    // Stripe Product prod_UaYW9iZCtYvqyw / Price price_1TbNP5BxCiPye3m0Pn5T4zFJ.
    // Metadata: product=pro_package, tier=pro.
    pro: "https://buy.stripe.com/9B600idx36zG3Bha0E3cc03",
    // Confidence Check / Saboteur re-scan add-on (q6). The landing CTA
    // always points at the $19 standalone link. The $9 within-14-days
    // link is sent by Rob via the post-delivery email (manual for now).
    // Both Payment Links carry metadata product=confidence_check so the
    // webhook routes to handle_confidence_check_purchase. See
    // docs/CONFIDENCE-CHECK-WORKFLOW.md.
    saboteur: "https://buy.stripe.com/3cI28q3Wt5vCb3J2yc3cc04",
    saboteurDiscounted: "https://buy.stripe.com/aFadR864BbU05JpdcQ3cc05",
    // Handoff Report add-on (q18). Single $49 USD Payment Link. Carries
    // metadata product=handoff_report so the webhook routes to
    // handle_handoff_report_purchase. landing/index.html, faq.html,
    // and the templates were swept from $99 → $49 on 2026-05-26 to match
    // this link; see docs/PRODUCT-DECISIONS.md §9 for the upsell-ladder
    // rationale (Scale Up + Handoff = $98, intentionally $1 below Pro).
    handoff: "https://buy.stripe.com/3cIdR864B3nu7Rx4Gk3cc06",
  },
  linkedinUrl: "https://www.linkedin.com/in/rob-dods/",
};
