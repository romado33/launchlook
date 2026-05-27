/**
 * LaunchLook post-submit personalization (thanks pages + intake prefill).
 *
 * Persists { url, email, hostname, platform } after the free-audit form,
 * then applies it on /thanks-free-audit and /thanks.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "launchlook_audit_context";
  var cfg = window.LAUNCHLOOK_CONFIG || {};

  function safeUrl(url) {
    if (!url || typeof url !== "string") return "";
    try {
      var parsed = new URL(url.trim());
      if (parsed.protocol === "http:" || parsed.protocol === "https:") {
        return parsed.href;
      }
    } catch (e) {
      return "";
    }
    return "";
  }

  function hostnameFromUrl(url) {
    var https = safeUrl(url);
    if (!https) return "";
    try {
      return new URL(https).hostname || "";
    } catch (e) {
      return "";
    }
  }

  function readContext() {
    var fromQuery = contextFromQuery();
    if (fromQuery.hostname || fromQuery.url) {
      saveContext(fromQuery);
      return fromQuery;
    }
    try {
      var raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return {};
      var parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (e) {
      return {};
    }
  }

  // Canonical tier slugs passed from the Stripe success URL (?tier=starter etc.)
  // Map to the exact Tally hidden-field value that drives Q9–Q12 conditionals.
  var TIER_SLUG_MAP = {
    starter: "starter",
    scale_up: "scale_up",
    pro: "pro",
  };

  function contextFromQuery() {
    try {
      var qs = new URLSearchParams(window.location.search);
      var site = (qs.get("site") || "").trim();
      var url = safeUrl(qs.get("url") || "");
      if (!url && site) {
        url = safeUrl("https://" + site.replace(/^\/+/, ""));
      }
      var tierRaw = (qs.get("tier") || "").trim().toLowerCase();
      var tier = TIER_SLUG_MAP[tierRaw] || tierRaw || "";
      return {
        url: url,
        email: (qs.get("email") || "").trim(),
        hostname: site || hostnameFromUrl(url),
        platform: (qs.get("platform") || "").trim(),
        tier: tier,
      };
    } catch (e) {
      return {};
    }
  }

  function saveContext(ctx) {
    var url = safeUrl(ctx && ctx.url);
    var email = ((ctx && ctx.email) || "").trim();
    var hostname = ((ctx && ctx.hostname) || hostnameFromUrl(url)).trim();
    if (!url && !email && !hostname) return;
    var payload = {
      url: url,
      email: email,
      hostname: hostname,
      platform: ((ctx && ctx.platform) || "").trim(),
      tier: ((ctx && ctx.tier) || "").trim(),
      savedAt: Date.now(),
    };
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (e) {
      /* private mode / blocked storage */
    }
  }

  function reviewerLine() {
    var name = ((cfg.reviewerName || cfg.founderName || "") + "").trim();
    if (name) {
      return "Reviewed by " + name + " before delivery.";
    }
    return "Reviewed by a human reviewer.";
  }

  function applyReviewerFooters() {
    var line = reviewerLine();
    document.querySelectorAll("[data-launchlook-reviewer]").forEach(function (el) {
      el.textContent = line;
    });
    document.querySelectorAll("[data-r-reviewer-line]").forEach(function (el) {
      el.textContent = line;
    });
  }

  function applyThanksPage() {
    var ctx = readContext();
    var host = (ctx.hostname || "").trim();
    var displayHost = host || "your site";

    document.querySelectorAll("[data-launchlook-site-host]").forEach(function (el) {
      el.textContent = displayHost;
    });

    var isPaidThanks = window.location.pathname.indexOf("thanks-free") === -1;
    document.querySelectorAll("[data-launchlook-thanks-lead]").forEach(function (el) {
      if (!host) return;
      if (isPaidThanks) {
        el.innerHTML =
          "Thanks for your purchase. Open the intake below — we&rsquo;ll pre-fill <strong class=\"text-ink\">" +
          escapeHtml(host) +
          "</strong> when your earlier free audit is still in this browser.";
      } else {
        el.innerHTML =
          "We queued your checkup for <strong class=\"text-ink\">" +
          escapeHtml(host) +
          "</strong>. A human tests your key workflows and reviews every finding before you see it, usually within a few days.";
      }
    });

    var intakeNote = document.querySelector("[data-launchlook-intake-prefill-note]");
    if (intakeNote) {
      if (host && ctx.url) {
        intakeNote.textContent =
          "Your intake form will open with " +
          host +
          " and your email pre-filled when Tally supports it.";
        intakeNote.classList.remove("hidden");
      } else {
        intakeNote.classList.add("hidden");
      }
    }
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function buildIntakeUrl(baseUrl, ctx) {
    if (!baseUrl) return "";
    try {
      var u = new URL(baseUrl);
      var prefill = cfg.tallyPrefill || {};
      if (ctx.email && prefill.email !== false) {
        u.searchParams.set("email", ctx.email);
      }
      var appKey = (prefill.appUrl || "").trim();
      if (appKey && ctx.url) {
        u.searchParams.set(appKey, ctx.url);
      }
      // Forward the tier slug into the Tally hidden field so Q9-Q12 conditionals
      // fire without requiring the customer to re-select their tier (removes Q8).
      var tierKey = (prefill.tier || "").trim();
      if (tierKey && ctx.tier) {
        u.searchParams.set(tierKey, ctx.tier);
      }
      return u.toString();
    } catch (e) {
      return baseUrl;
    }
  }

  function enhanceIntakeLinks() {
    var ctx = readContext();
    if (!ctx.url && !ctx.email) return;
    document.querySelectorAll("[data-launchlook-intake]").forEach(function (el) {
      var base = el.getAttribute("data-launchlook-intake-base") || el.getAttribute("href") || "";
      if (!base || base === "#") return;
      var next = buildIntakeUrl(base, ctx);
      if (next) {
        el.setAttribute("href", next);
        el.setAttribute("target", "_blank");
        el.setAttribute("rel", "noopener noreferrer");
      }
    });
  }

  function init() {
    applyReviewerFooters();
    if (document.body && document.body.dataset.launchlookPersonalize === "thanks") {
      applyThanksPage();
      enhanceIntakeLinks();
    }
  }

  window.LaunchLookPersonalize = {
    saveContext: saveContext,
    hostnameFromUrl: hostnameFromUrl,
    readContext: readContext,
    buildIntakeUrl: buildIntakeUrl,
    reviewerLine: reviewerLine,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
