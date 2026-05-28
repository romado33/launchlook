/**
 * LaunchLook E2E checklist items — shared by /e2e and docs/e2e-checklist.html.
 * Bump STORAGE_KEY when item ids change so progress resets intentionally.
 */
window.LAUNCHLOOK_E2E = {
  STORAGE_KEY: "launchlook-e2e-checklist-v5",
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
          id: "pf-stripe-tax-off",
          label: "automatic_tax disabled on API Payment Links (no tax at checkout)",
          hint: "python scripts/stripe_payment_links.py disable-tax",
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
          id: "st-no-tax",
          label: "Checkout shows listed price only (no automatic tax line)",
          hint: "automatic_tax should be off on Payment Links",
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
    {
      id: "edge",
      title: "I. Edge cases (~15 min)",
      items: [
        {
          id: "ec-bare-domain",
          label: "Free form: submit bare domain without https:// (e.g. mysite.com) → queues normally",
          hint: "Normalization runs both client-side (free-audit.js) and server-side (api/free-audit.py)",
        },
        {
          id: "ec-http",
          label: "Free form: submit http:// URL → queues normally (http scheme is accepted)",
          hint: "",
        },
        {
          id: "ec-dedup",
          label: "Free form: same email + same URL submitted twice within 30 days → upsell email, NO second Notion row",
          hint: "Check Notion Free Audit DB — row count must stay at 1",
        },
        {
          id: "ec-rate-email",
          label: "Free form: same email submitted 3 times in 30 days → 4th submission blocked with email-rate message",
          hint: "Use 3 different URLs for first 3. 4th with same email returns 429.",
        },
        {
          id: "ec-nojs",
          label: "Free form with JS disabled → native POST redirects to /thanks-free-audit (no blank screen)",
          hint: "Disable JS in DevTools → Network tab, submit form, expect HTTP 303",
        },
        {
          id: "ec-tally-tier-starter",
          label: "Click Starter buy button → land on /thanks?tier=starter → Tally intake pre-fills tier=starter (hidden field)",
          hint: "Confirm hidden field is set in Tally's URL params",
        },
        {
          id: "ec-tally-tier-scaleup",
          label: "Click Scale Up buy button → /thanks?tier=scale_up → Tally tier=scale_up",
          hint: "",
        },
        {
          id: "ec-tally-tier-pro",
          label: "Click Pro buy button → /thanks?tier=pro → Tally tier=pro",
          hint: "",
        },
        {
          id: "ec-tally-no-tier",
          label: "Open /thanks (no ?tier= param) → Tally intake still opens; tier field empty in Notion (not a crash)",
          hint: "Simulates customer who bookmarked the page without the tier param",
        },
        {
          id: "ec-stripe-duplicate",
          label: "Stripe Dashboard: resend the same checkout.session.completed webhook twice → Notion shows 1 row (updated), not 2",
          hint: "Dashboard → Developers → Webhooks → click event → Resend",
        },
        {
          id: "ec-stripe-unknown-amount",
          label: "Stripe test checkout for an unusual amount (e.g. $77.77 gift) → Notion row created with Notes hint about unknown amount",
          hint: "Would need a test Stripe Price. Just verify the webhook code path via the existing unit test if skipping live.",
        },
        {
          id: "ec-email-html",
          label: "Open draft-ready founder email in Gmail → HTML version renders with 3 clickable buttons (Refine, Preview, Open delivery draft)",
          hint: "Plain-text fallback in the same email should show compact mailto, not a broken long URL",
        },
        {
          id: "ec-email-mailto",
          label: "Click 'Open delivery draft →' button in HTML email → Gmail compose opens with subject + findings pre-filled",
          hint: "mailto: body may be truncated by browser URL limits; subject + first finding is the minimum",
        },
        {
          id: "ec-form-smoke-ran",
          label: "Run audit worker on a site with a contact form → founder email shows 'Form smoke: ran ✓'",
          hint: "Playwright must be installed. Use a test site with a visible <form>.",
        },
        {
          id: "ec-form-smoke-skipped",
          label: "Run audit on a site with no detectable forms → founder email shows 'not run (Playwright unavailable or no forms detected)'",
          hint: "Not an error — just confirms the status message is correct",
        },
        {
          id: "ec-slug-collision",
          label: "Known limitation documented: two customers with same email local-part + same hostname get the same slug (YAML overwrite risk)",
          hint: "Do not test destructively. Mitigate by processing one customer at a time. See docs/LESSONS-LEARNED.md Part 2 (slug collision).",
        },
        {
          id: "ec-resend-domain",
          label: "FROM_EMAIL domain is verified in Resend → send a test free-audit submission and confirm delivery (not bounced)",
          hint: "If FROM_EMAIL ever changes, re-verify the domain in Resend before pushing to production",
        },
      ],
    },
  ],
};
