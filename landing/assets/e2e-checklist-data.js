/**
 * LaunchLook E2E checklist items — shared by /e2e and docs/e2e-checklist.html.
 * Bump STORAGE_KEY when item ids change so progress resets intentionally.
 */
window.LAUNCHLOOK_E2E = {
  STORAGE_KEY: "launchlook-e2e-checklist-v3",
  SECTIONS: [
    {
      id: "preflight",
      title: "0. Pre-flight (before testing)",
      items: [
        {
          id: "pf-deploy",
          label: "Vercel production on latest main",
          hint: "Hard-refresh launchlook.app (Ctrl+Shift+R)",
        },
        {
          id: "pf-env",
          label:
            "Vercel env: STRIPE_WEBHOOK_SECRET, NOTION_TOKEN, NOTION_CUSTOMERS_DB_ID, NOTION_FREE_AUDIT_DB_ID, NOTION_CONFIDENCE_CHECK_DB_ID, RESEND_API_KEY, TALLY_WEBHOOK_TOKEN",
          hint: "",
        },
        {
          id: "pf-e2e-password",
          label: "E2E_CHECKLIST_PASSWORD set; https://launchlook.app/e2e unlocks",
          hint: "POST /api/e2e-auth returns ok",
        },
        {
          id: "pf-email",
          label: "hello@launchlook.app forwards to an inbox you check",
          hint: "",
        },
        {
          id: "pf-tally-pub",
          label: "Tally QKOX1A published (not draft)",
          hint: "https://tally.so/forms/QKOX1A/edit",
        },
        {
          id: "pf-tally-tiers",
          label: "Tally tier question: Starter $19 / Scale Up $49 / Pro $99 (+ Webflow in Q7)",
          hint: "docs/TALLY-PASTE-ONLY.txt",
        },
        {
          id: "pf-tally-notify",
          label: "Tally notifications → hello@launchlook.app",
          hint: "",
        },
        {
          id: "pf-tally-thanks",
          label: "Tally after-submit redirect → https://launchlook.app/thanks",
          hint: "",
        },
        {
          id: "pf-tally-webhook",
          label: "Tally webhook URL with ?t= token; test event returns 200",
          hint: "GET /api/tally-webhook?t=… → status ok",
        },
        {
          id: "pf-stripe-live",
          label: "Stripe live mode for real-money smoke (or use test mode knowingly)",
          hint: "",
        },
        {
          id: "pf-stripe-config",
          label: "config.js Payment Links match Dashboard (starter, scaleup, pro, handoff, saboteur×2 — no reverify)",
          hint: "landing/assets/config.js",
        },
        {
          id: "pf-stripe-thanks",
          label: "Active Payment Links ($19/$49/$99 + add-ons): success URL → https://launchlook.app/thanks",
          hint: "",
        },
        {
          id: "pf-stripe-tax-reg",
          label: "Stripe Tax registrations complete (regions you sell into)",
          hint: "Dashboard → Settings → Tax",
        },
        {
          id: "pf-stripe-tax",
          label: "automatic_tax enabled on all active Payment Links",
          hint: "python scripts/stripe_payment_links.py enable-tax",
        },
        {
          id: "pf-stripe-dead",
          label: "Dead Payment Links deactivated: $9 re-verify badge, old CAD $9/$29 tiers",
          hint: "reverify link should show inactive in Stripe",
        },
      ],
    },
    {
      id: "smoke",
      title: "A. Site smoke (~8 min)",
      items: [
        {
          id: "sm-home",
          label: "/ loads; pricing shows $19 / $49 / $99 with bulleted tier features",
          hint: "",
        },
        {
          id: "sm-no-popular",
          label: "Scale Up card has no Popular badge or accent bar",
          hint: "",
        },
        {
          id: "sm-stripe-cta",
          label: "Get Starter / Scale Up / Pro open buy.stripe.com (not grayed # placeholders)",
          hint: "Requires config.js on deploy",
        },
        {
          id: "sm-handoff-cta",
          label: "Handoff Report $49 add-on link in pricing opens Stripe",
          hint: "data-launchlook-stripe=handoff_report",
        },
        {
          id: "sm-pages",
          label: "/faq, /webflow, /thanks, /thanks-free-audit, /privacy, /terms → 200",
          hint: "",
        },
        {
          id: "sm-tagline",
          label: "Header tagline “One last look before you launch.” on /, /faq, /webflow",
          hint: "Hidden below 640px by design",
        },
        {
          id: "sm-nav",
          label: "Top nav: Pricing, FAQ, Webflow only (free audit is hero/footer, not nav)",
          hint: "",
        },
        {
          id: "sm-sample",
          label: "/sample → Sparkle Marketplace report (findings visible)",
          hint: "Not “We don't have a report at that link”",
        },
        {
          id: "sm-sample-json",
          label: "/data/reports/jane-sparkle-marketplace.json → 200",
          hint: "vercelignore must use /data/ not data/",
        },
        {
          id: "sm-redirect-checklist",
          label: "/checklist redirects to /",
          hint: "",
        },
        {
          id: "sm-footer",
          label: "Footer Sample report works; no GitHub link; privacy/terms have no dead checklist link",
          hint: "",
        },
        {
          id: "sm-prompts",
          label: "Pricing mentions fix prompts on all paid tiers; Fix Check not sold on landing",
          hint: "",
        },
      ],
    },
    {
      id: "free",
      title: "B. Free audit path (~10 min)",
      items: [
        {
          id: "free-submit",
          label: "Homepage form: URL + email submits successfully",
          hint: "Use disposable email or +alias",
        },
        {
          id: "free-inline-error",
          label: "Invalid URL shows inline error on homepage (no redirect to thanks)",
          hint: "Try not-a-url — needs data-free-audit-form JS",
        },
        {
          id: "free-thanks",
          label: "Success → /thanks-free-audit (or inline success before redirect)",
          hint: "",
        },
        {
          id: "free-resend",
          label: "Resend confirmation email arrives",
          hint: "Check spam",
        },
        {
          id: "free-notion",
          label: "Notion Free Audit DB: new row (status queued)",
          hint: "",
        },
        {
          id: "free-dedupe",
          label: "(Optional) Same email+URL resubmit → duplicate/upsell behavior",
          hint: "",
        },
      ],
    },
    {
      id: "starter",
      title: "C. Paid path — Starter $19 (~15 min)",
      items: [
        {
          id: "st-checkout",
          label: "Get Starter → Stripe Checkout shows $19 USD",
          hint: "",
        },
        {
          id: "st-tax",
          label: "Checkout collects billing address; tax line appears when applicable",
          hint: "Depends on Stripe Tax registrations + customer location",
        },
        {
          id: "st-thanks",
          label: "After pay → https://launchlook.app/thanks",
          hint: "",
        },
        {
          id: "st-receipt",
          label: "Stripe receipt email arrives",
          hint: "",
        },
        {
          id: "st-notion-pay",
          label: "Notion Customers: row with Starter Package tier",
          hint: "",
        },
        {
          id: "st-intake-open",
          label: "Complete intake opens Tally (QKOX1A), not mailto-only",
          hint: "",
        },
        {
          id: "st-intake-fill",
          label: "Submit Starter intake — no test-account password fields",
          hint: "",
        },
        {
          id: "st-tally-email",
          label: "Tally notification email to hello@launchlook.app",
          hint: "",
        },
        {
          id: "st-notion-intake",
          label: "Notion Customers: intake fields + intake received",
          hint: "Via tally-webhook",
        },
      ],
    },
    {
      id: "scaleup",
      title: "D. Paid path — Scale Up $49 (optional, ~10 min)",
      items: [
        {
          id: "su-checkout",
          label: "Checkout $49 → /thanks → Tally",
          hint: "Different test email if possible",
        },
        {
          id: "su-tier-q",
          label: "Tally tier question shows Scale Up $49 (not old Full/Scale names)",
          hint: "",
        },
        {
          id: "su-test-q",
          label: "Test-account questions only for Scale Up + Yes",
          hint: "",
        },
        {
          id: "su-notion",
          label: "Notion: Scale Up Package tier; notes if test accounts provided",
          hint: "",
        },
      ],
    },
    {
      id: "webhook",
      title: "E. Stripe webhook sanity (~2 min)",
      items: [
        {
          id: "wh-test",
          label: "Stripe Dashboard → webhook → test checkout.session.completed → 200",
          hint: "",
        },
        {
          id: "wh-live",
          label: "After real test payment: event succeeded (no repeated failures)",
          hint: "",
        },
      ],
    },
    {
      id: "delivery",
      title: "F. Delivery dry-run (optional, ~10 min)",
      items: [
        {
          id: "del-render",
          label: "deliver_report.py renders Main Report + QSG + Pre-Launch Checklist PDFs",
          hint: "python scripts/deliver_report.py --customer customers/example-….yaml",
        },
        {
          id: "del-send",
          label: "--send delivers to test inbox via Resend",
          hint: "",
        },
        {
          id: "del-fixcheck",
          label: "PDF footer mentions Fix Check (reply recheck), not a landing pricing row",
          hint: "",
        },
      ],
    },
    {
      id: "addons",
      title: "G. Add-ons (only if testing those SKUs)",
      items: [
        {
          id: "ao-handoff",
          label: "Handoff $49 checkout → webhook / manual handoff delivery path",
          hint: "metadata product=handoff_report",
        },
        {
          id: "ao-fixcheck",
          label: "Fix Check $19 checkout → Confidence Checks Notion DB row",
          hint: "metadata product=confidence_check; offered post-delivery only on site",
        },
        {
          id: "ao-skip-reverify",
          label: "Old $9 re-verify Payment Link inactive (Verified badge removed)",
          hint: "Not in config.js",
        },
      ],
    },
    {
      id: "mobile",
      title: "H. Mobile pass (~5 min)",
      items: [
        {
          id: "mob-free",
          label: "Homepage free audit form works on phone",
          hint: "",
        },
        {
          id: "mob-paid",
          label: "One Starter checkout + Tally intake on phone",
          hint: "",
        },
      ],
    },
  ],
};
