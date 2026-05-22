/**
 * Site config — copy to config.local.js and fill in real values.
 * config.local.js is gitignored; falls back to placeholders if missing.
 */
window.LAUNCHLOOK_CONFIG = {
  domain: "launchlook.app",
  supportEmail: "hello@launchlook.app",
  intakeFormUrl: "", // Paste Tally publish URL: https://tally.so/r/YOUR_FORM_ID
  stripe: {
    starter: "https://buy.stripe.com/8x200i8cJ0bigo3fkY3cc01",
    launch: "https://buy.stripe.com/cNi7sK3Wtgag9ZFc8M3cc02", // Launch tier ($29)
    // Legacy keys (optional): quickCheckup → starter, launchPack → launch
    quickCheckup: "https://buy.stripe.com/8x200i8cJ0bigo3fkY3cc01",
    launchPack: "https://buy.stripe.com/cNi7sK3Wtgag9ZFc8M3cc02",
  },
  githubChecklist: "https://github.com/romado33/launchlook-prelaunch-checklist",
};
