/**
 * Applies LAUNCHLOOK_CONFIG to data-launchlook-* elements.
 * Load after config.js and optional config.local.js.
 */
(function () {
  var cfg = window.LAUNCHLOOK_CONFIG || {};
  var stripe = cfg.stripe || {};
  var starterUrl = stripe.starter || stripe.quickCheckup || "";
  var launchUrl = stripe.launch || stripe.launchPack || stripe.full || "";

  function $(selector) {
    return document.querySelectorAll(selector);
  }

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

  function setLinkState(selector, url, disabledTitle) {
    $(selector).forEach(function (el) {
      if (url) {
        el.setAttribute("href", url);
        el.classList.remove("opacity-50", "pointer-events-none");
        el.removeAttribute("title");
        el.removeAttribute("aria-disabled");
        return;
      }
      el.setAttribute("href", "#");
      el.classList.add("opacity-50", "pointer-events-none");
      el.setAttribute("title", disabledTitle);
      el.setAttribute("aria-disabled", "true");
    });
  }

  setLinkState("[data-launchlook-stripe='starter'], [data-launchlook-stripe='quick']", safeHttpsUrl(starterUrl), "Payment link not configured");
  setLinkState("[data-launchlook-stripe='launch'], [data-launchlook-stripe='full']", safeHttpsUrl(launchUrl), "Payment link not configured");

  var checklistUrl = safeHttpsUrl(cfg.githubChecklist);
  if (checklistUrl) {
    $("[data-launchlook-github='checklist']").forEach(function (el) {
      el.setAttribute("href", checklistUrl);
      el.removeAttribute("aria-disabled");
    });
  }

  function intakeMailto(email) {
    var subject = encodeURIComponent("LaunchLook intake");
    var body = encodeURIComponent(
      "App URL:\n\nOne-line description:\n\nBuilder (Lovable, Bolt, v0, Cursor, etc.):\n\nTier purchased (Starter Package / Full Package):\n"
    );
    return "mailto:" + email + "?subject=" + subject + "&body=" + body;
  }

  if (cfg.supportEmail) {
    var mailto = "mailto:" + cfg.supportEmail;
    $("[data-launchlook-email='support']").forEach(function (el) {
      el.setAttribute("href", mailto);
      if (!el.getAttribute("data-launchlook-keep-text")) {
        el.textContent = cfg.supportEmail;
      }
    });
    $("[data-launchlook-email-display]").forEach(function (el) {
      el.textContent = cfg.supportEmail;
    });
  }

  var linkedinUrl = safeHttpsUrl(cfg.linkedinUrl);
  $("[data-launchlook-linkedin-wrap]").forEach(function (wrap) {
    var link = wrap.querySelector("[data-launchlook-linkedin]");
    if (!linkedinUrl || !link) {
      wrap.classList.add("hidden");
      return;
    }
    wrap.classList.remove("hidden");
    link.setAttribute("href", linkedinUrl);
    link.setAttribute("rel", "noopener noreferrer");
  });

  var intakeUrl = safeIntakeUrl(cfg.intakeFormUrl);
  var intakeEls = $("[data-launchlook-intake]");
  if (intakeUrl) {
    intakeEls.forEach(function (el) {
      el.setAttribute("href", intakeUrl);
      el.setAttribute("target", "_blank");
      el.setAttribute("rel", "noopener noreferrer");
      if (!el.getAttribute("data-launchlook-keep-text")) {
        el.textContent = "Complete intake form";
      }
      el.classList.remove("opacity-50", "pointer-events-none");
      el.removeAttribute("title");
      el.removeAttribute("aria-disabled");
    });
    $("[data-launchlook-intake-email-hint]").forEach(function (el) {
      el.classList.add("hidden");
    });
  } else if (cfg.supportEmail) {
    var intakeMail = intakeMailto(cfg.supportEmail);
    intakeEls.forEach(function (el) {
      el.setAttribute("href", intakeMail);
      el.removeAttribute("target");
      el.removeAttribute("rel");
      if (!el.getAttribute("data-launchlook-keep-text")) {
        el.textContent = "Email your intake details";
      }
      el.classList.remove("opacity-50", "pointer-events-none");
      el.removeAttribute("title");
      el.removeAttribute("aria-disabled");
    });
    $("[data-launchlook-intake-email-hint]").forEach(function (el) {
      el.classList.remove("hidden");
    });
  }
})();
