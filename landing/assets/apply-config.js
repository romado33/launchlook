/**
 * Applies LAUNCHLOOK_CONFIG to data-launchlook-* (and legacy data-onceover-*) elements.
 * Load after config.js and optional config.local.js.
 */
(function () {
  var cfg = window.LAUNCHLOOK_CONFIG || {};
  var stripe = cfg.stripe || {};
  var starterUrl = stripe.starter || stripe.quickCheckup || "";
  var launchUrl = stripe.launch || stripe.launchPack || "";

  function setHref(selector, url) {
    if (!url) return;
    document.querySelectorAll(selector).forEach(function (el) {
      el.setAttribute("href", url);
      el.classList.remove("opacity-50", "pointer-events-none");
      el.removeAttribute("title");
      el.removeAttribute("aria-disabled");
    });
  }

  function markDisabled(selector, title) {
    document.querySelectorAll(selector).forEach(function (el) {
      el.setAttribute("href", "#");
      el.classList.add("opacity-50", "pointer-events-none");
      el.setAttribute("title", title);
      el.setAttribute("aria-disabled", "true");
    });
  }

  var stripeSelectors = {
    starter: "[data-launchlook-stripe='starter'], [data-launchlook-stripe='quick'], [data-onceover-stripe='starter'], [data-onceover-stripe='quick']",
    launch: "[data-launchlook-stripe='launch'], [data-onceover-stripe='launch']",
  };

  setHref(stripeSelectors.starter, starterUrl);
  setHref(stripeSelectors.launch, launchUrl);
  if (!starterUrl) {
    markDisabled(stripeSelectors.starter, "Payment link not configured");
  }
  if (!launchUrl) {
    markDisabled(stripeSelectors.launch, "Payment link not configured");
  }

  if (cfg.githubChecklist) {
    document.querySelectorAll("[data-launchlook-github='checklist'], [data-onceover-github='checklist']").forEach(function (el) {
      el.setAttribute("href", cfg.githubChecklist);
      el.removeAttribute("aria-disabled");
    });
  }

  if (cfg.supportEmail) {
    var mailto = "mailto:" + cfg.supportEmail;
    document.querySelectorAll("[data-launchlook-email='support'], [data-onceover-email='support']").forEach(function (el) {
      el.setAttribute("href", mailto);
      if (el.textContent.indexOf("@") === -1 && !el.getAttribute("data-launchlook-keep-text")) {
        el.textContent = cfg.supportEmail;
      }
    });
  }

  if (cfg.intakeFormUrl) {
    document.querySelectorAll("[data-launchlook-intake], [data-onceover-intake]").forEach(function (el) {
      el.setAttribute("href", cfg.intakeFormUrl);
      el.classList.remove("opacity-50", "pointer-events-none");
      el.removeAttribute("title");
      el.removeAttribute("aria-disabled");
    });
  }
})();
