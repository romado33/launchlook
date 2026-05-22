/**
 * Site config — copy to config.local.js and fill in real values.
 * config.local.js is gitignored; falls back to placeholders if missing.
 */
window.LAUNCHLOOK_CONFIG = {
  domain: "launchlook.app",
  supportEmail: "hello@launchlook.app",
  intakeFormUrl: "", // Tally.so URL after BL-07
  stripe: {
    quickCheckup: "", // https://buy.stripe.com/...
    launchPack: "",
    polish: "",
  },
  githubChecklist: "", // https://github.com/you/launchlook-prelaunch-checklist
};
