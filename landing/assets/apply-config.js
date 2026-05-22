/**
 * Applies LAUNCHLOOK_CONFIG to data-launchlook-* (and legacy data-onceover-*) elements.
 * Load after config.js and optional config.local.js.
 */
(function () {
  var cfg = window.LAUNCHLOOK_CONFIG || {};
  var stripe = cfg.stripe || {};
  var starterUrl = stripe.starter || stripe.quickCheckup || "";
  var launchUrl = stripe.launch || stripe.launchPack || "";

  /** Block javascript: and other non-http(s) URLs if config is ever tampered with. */
  function safeHttpsUrl(url) {
    if (!url || typeof url !== "string") return "";
    try {
      var parsed = new URL(url);
      if (parsed.protocol === "https:") return parsed.href;
    } catch (e) {
      return "";
    }
    return "";
  }

  function safeIntakeUrl(url) {
    var https = safeHttpsUrl(url);
    if (!https) return "";
    try {
      var host = new URL(https).hostname;
      if (host === "tally.so" || host.endsWith(".tally.so")) return https;
    } catch (e) {
      return "";
    }
    return "";
  }

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
    launch: "[data-launchlook-stripe='launch'], [data-launchlook-stripe='full'], [data-onceover-stripe='launch']",
  };

  setHref(stripeSelectors.starter, safeHttpsUrl(starterUrl));
  setHref(stripeSelectors.launch, safeHttpsUrl(launchUrl));
  if (!starterUrl) {
    markDisabled(stripeSelectors.starter, "Payment link not configured");
  }
  if (!launchUrl) {
    markDisabled(stripeSelectors.launch, "Payment link not configured");
  }

  var checklistUrl = safeHttpsUrl(cfg.githubChecklist);
  if (checklistUrl) {
    document.querySelectorAll("[data-launchlook-github='checklist'], [data-onceover-github='checklist']").forEach(function (el) {
      el.setAttribute("href", checklistUrl);
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

  var intakeUrl = safeIntakeUrl(cfg.intakeFormUrl);
  if (intakeUrl) {
    document.querySelectorAll("[data-launchlook-intake], [data-onceover-intake]").forEach(function (el) {
      el.setAttribute("href", intakeUrl);
      el.classList.remove("opacity-50", "pointer-events-none");
      el.removeAttribute("title");
      el.removeAttribute("aria-disabled");
    });
  }
})();
