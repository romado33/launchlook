/**
 * Applies LAUNCHLOOK_CONFIG to data-launchlook-* elements on the page.
 * Load after config.js (and optional config.local.js).
 */
(function () {
  var cfg = window.LAUNCHLOOK_CONFIG || {};
  var stripe = cfg.stripe || {};
  var starterUrl = stripe.starter || stripe.quickCheckup;
  var launchUrl = stripe.launch || stripe.launchPack;

  function setHref(selector, url) {
    if (!url) return;
    document.querySelectorAll(selector).forEach(function (el) {
      el.setAttribute("href", url);
      el.classList.remove("opacity-50", "pointer-events-none");
      el.removeAttribute("title");
    });
  }

  setHref("[data-launchlook-stripe='starter']", starterUrl);
  setHref("[data-launchlook-stripe='quick']", starterUrl);
  setHref("[data-launchlook-stripe='launch']", launchUrl);

  if (cfg.githubChecklist) {
    document.querySelectorAll("[data-launchlook-github='checklist']").forEach(function (el) {
      el.setAttribute("href", cfg.githubChecklist);
    });
  }

  if (cfg.supportEmail) {
    document.querySelectorAll("[data-launchlook-email='support']").forEach(function (el) {
      var mailto = "mailto:" + cfg.supportEmail;
      el.setAttribute("href", mailto);
      if (el.textContent.indexOf("@") === -1 && !el.getAttribute("data-launchlook-keep-text")) {
        el.textContent = cfg.supportEmail;
      }
    });
  }

  if (cfg.intakeFormUrl) {
    document.querySelectorAll("[data-launchlook-intake]").forEach(function (el) {
      el.setAttribute("href", cfg.intakeFormUrl);
      el.classList.remove("opacity-50", "pointer-events-none");
      el.removeAttribute("title");
    });
  }

  // Legacy onceover-* attributes (thanks.html older deploys)
  setHref("[data-onceover-stripe='starter']", starterUrl);
  setHref("[data-onceover-stripe='quick']", starterUrl);
  setHref("[data-onceover-stripe='launch']", launchUrl);
  if (cfg.githubChecklist) {
    document.querySelectorAll("[data-onceover-github='checklist']").forEach(function (el) {
      el.setAttribute("href", cfg.githubChecklist);
    });
  }
  if (cfg.supportEmail) {
    document.querySelectorAll("[data-onceover-email='support']").forEach(function (el) {
      el.setAttribute("href", "mailto:" + cfg.supportEmail);
    });
  }
  if (cfg.intakeFormUrl) {
    document.querySelectorAll("[data-onceover-intake]").forEach(function (el) {
      el.setAttribute("href", cfg.intakeFormUrl);
      el.classList.remove("opacity-50", "pointer-events-none");
    });
  }
})();
