/**
 * Site config — copy to config.local.js and fill in real values.
 * config.local.js is gitignored; falls back to placeholders if missing.
 */
window.LAUNCHLOOK_CONFIG = {
  domain: "launchlook.app",
  supportEmail: "hello@launchlook.app",
  intakeFormUrl: "https://tally.so/r/9qodVE",
  tallyThanksUrl: "https://tally.so/r/Y5xO5J",
  stripe: {
    // Starter and Scale Up still point at the pre-bump $9 / $29 CAD Payment
    // Links. The May 2026 price-bump worker is responsible for the $19 / $49
    // USD replacements (see docs/MANUAL-TASKS-PRICE-BUMP.md). Rob: leave
    // these alone until the new tier Payment Links exist and you can swap
    // both at once.
    starter: "https://buy.stripe.com/8x200i8cJ0bigo3fkY3cc01",
    scaleup: "https://buy.stripe.com/cNi7sK3Wtgag9ZFc8M3cc02",
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
    // handle_handoff_report_purchase. NOTE: landing/index.html currently
    // advertises Handoff at $99; this $49 price was requested by the May
    // 2026 batch run mission and is flagged for Rob's eyes in
    // docs/MANUAL-APPROVAL-2026-05-26.md.
    handoff: "https://buy.stripe.com/3cIdR864B3nu7Rx4Gk3cc06",
    // LaunchLook Verified badge $9 re-verification (q17). Payment Link
    // metadata includes product=reverify so the webhook routes to
    // handle_reverify_purchase. Optional metadata customer_slug (or the
    // session client_reference_id) lets Rob look up the badge directly.
    // See docs/VERIFIED-BADGE-WORKFLOW.md.
    reverify: "https://buy.stripe.com/00wfZgeB72jq9ZF3Cg3cc07",
  },
  githubChecklist: "https://github.com/romado33/launchlook-prelaunch-checklist",
  linkedinUrl: "https://www.linkedin.com/in/rob-dods/",
};
