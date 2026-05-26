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
    // Pre-price-bump links remain wired up so old amounts ($9 / $29) still
    // map cleanly. Rob: replace with new $19 / $49 / $99 Payment Links once
    // they're created in Stripe (see docs/MANUAL-TASKS-PRICE-BUMP.md).
    starter: "https://buy.stripe.com/8x200i8cJ0bigo3fkY3cc01",
    scaleup: "https://buy.stripe.com/cNi7sK3Wtgag9ZFc8M3cc02",
    pro: "",
    // Confidence Check / Saboteur re-scan add-on (q6). The landing CTA
    // always points at the $19 standalone link. The $9 within-14-days
    // link is sent by Rob via the post-delivery email (manual for now).
    // Both Payment Links must carry metadata product=confidence_check
    // so the webhook routes to handle_confidence_check_purchase. See
    // docs/CONFIDENCE-CHECK-WORKFLOW.md.
    saboteur: "",
    saboteurDiscounted: "",
    // LaunchLook Verified badge $9 re-verification (q17). Payment Link
    // metadata MUST include product=reverify so the webhook routes to
    // handle_reverify_purchase. Optional metadata customer_slug (or the
    // session client_reference_id) lets Rob look up the badge directly.
    // Empty until Rob creates the link; the verify page falls back to a
    // mailto in the meantime. See docs/VERIFIED-BADGE-WORKFLOW.md.
    reverify: "",
  },
  githubChecklist: "https://github.com/romado33/launchlook-prelaunch-checklist",
  linkedinUrl: "https://www.linkedin.com/in/rob-dods/",
};
