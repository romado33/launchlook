/*
 * verify.js: progressive enhancement for /verify.
 *
 * Reads ?slug= from the query string, calls /api/verify, and reveals the
 * matching state section. Plain English copy lives in the HTML -- this file
 * just toggles visibility and fills in the data.
 *
 * Keeps the page useful for non-JS visitors too: the loading state is what
 * they see and the page never claims a verdict it has not received.
 *
 * Discipline notes:
 *   * No certification language anywhere in this file. The strings the
 *     visitor sees come from /verify.html or the /api/verify JSON response.
 *   * Plausible custom event ('VerifyView') fires on every render so we can
 *     watch traffic to expired vs valid vs unknown without server logs.
 */

(function () {
  "use strict";

  var STATES = [
    "loading",
    "no-slug",
    "valid",
    "expired",
    "unknown",
    "rate-limited",
    "error",
  ];

  function show(state) {
    STATES.forEach(function (key) {
      var el = document.querySelector('[data-verify-state="' + key + '"]');
      if (!el) return;
      if (key === state) {
        el.classList.remove("hidden");
      } else {
        el.classList.add("hidden");
      }
    });
    track(state);
  }

  function track(state) {
    if (typeof window.plausible !== "function") return;
    try {
      window.plausible("VerifyView", { props: { state: state } });
    } catch (e) {
      /* analytics is best-effort, never break the page */
    }
  }

  function setText(selector, value) {
    var el = document.querySelector(selector);
    if (el && value != null && value !== "") {
      el.textContent = value;
    }
  }

  function setTextAll(selector, value) {
    var els = document.querySelectorAll(selector);
    els.forEach(function (el) {
      if (value != null && value !== "") el.textContent = value;
    });
  }

  function humanDate(iso) {
    if (!iso) return "";
    var parts = iso.split("-");
    if (parts.length !== 3) return iso;
    var months = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    var month = months[parseInt(parts[1], 10) - 1] || "";
    var day = parseInt(parts[2], 10);
    var year = parts[0];
    if (!month) return iso;
    return month + " " + day + ", " + year;
  }

  function readSlug() {
    try {
      var qs = new URLSearchParams(window.location.search);
      var raw = qs.get("slug") || "";
      return raw.trim();
    } catch (e) {
      return "";
    }
  }

  function setReverifyHref(slug) {
    var cfg = window.LAUNCHLOOK_CONFIG || {};
    var stripe = cfg.stripe || {};
    var url = (stripe.reverify || "").trim();
    document
      .querySelectorAll('[data-launchlook-stripe="reverify"]')
      .forEach(function (el) {
        if (url && /^https:\/\//.test(url)) {
          var withSlug = url;
          try {
            var u = new URL(url);
            if (slug) {
              u.searchParams.set("client_reference_id", slug);
            }
            withSlug = u.toString();
          } catch (err) {
            /* keep original */
          }
          el.setAttribute("href", withSlug);
          el.classList.remove("opacity-50", "pointer-events-none");
          el.removeAttribute("aria-disabled");
          el.removeAttribute("title");
        } else {
          el.setAttribute(
            "href",
            "mailto:hello@launchlook.app?subject=" +
              encodeURIComponent("LaunchLook badge re-verification") +
              "&body=" +
              encodeURIComponent(
                "Slug: " +
                  slug +
                  "\n\nI want to renew my LaunchLook Verified badge.",
              ),
          );
          el.setAttribute(
            "title",
            "Re-verification payment link pending; emails Rob instead.",
          );
        }
      });
  }

  function renderValid(body) {
    var headlineParts = ["LaunchLook Verified"];
    if (body.tier) headlineParts.push(body.tier);
    setText("[data-verify-headline]", headlineParts.join(" \u00b7 "));

    var verifiedHuman = humanDate(body.verified_at);
    var expiresHuman = humanDate(body.expires_at);
    var detail =
      (body.tier ? body.tier + " audit " : "Audit ") +
      "completed " +
      verifiedHuman +
      (body.customer_url ? " for " + body.customer_url + "." : ".") +
      " Valid through " +
      expiresHuman +
      ".";
    setText("[data-verify-detail]", detail);
    setTextAll("[data-verify-tier]", body.tier || "");
    setTextAll("[data-verify-verified-at]", verifiedHuman);
    setText("[data-verify-expires-at]", expiresHuman);
    setText("[data-verify-customer-url]", body.customer_url || "not on file");
    show("valid");
  }

  function renderExpired(body) {
    setTextAll("[data-verify-tier]", body.tier || "");
    setTextAll("[data-verify-verified-at]", humanDate(body.verified_at));
    setText(
      "[data-verify-expired-on]",
      humanDate(body.expired_on || body.expires_at),
    );
    setReverifyHref(body.customer_slug || "");
    show("expired");
  }

  function renderUnknown(slug) {
    setText("[data-verify-requested-slug]", slug);
    show("unknown");
  }

  function renderRateLimited(body) {
    var seconds = parseInt(body.retry_after_seconds, 10);
    var msg;
    if (isFinite(seconds) && seconds > 0) {
      msg = seconds + " second" + (seconds === 1 ? "" : "s");
    } else {
      msg = "a moment";
    }
    setText("[data-verify-retry-after]", msg);
    show("rate-limited");
  }

  function fetchVerify(slug) {
    var url = "/api/verify?slug=" + encodeURIComponent(slug);
    return fetch(url, {
      headers: { Accept: "application/json" },
      credentials: "omit",
    }).then(function (res) {
      return res.json().then(function (body) {
        return { status: res.status, body: body || {} };
      });
    });
  }

  function init() {
    var slug = readSlug();
    if (!slug) {
      show("no-slug");
      return;
    }
    show("loading");
    setReverifyHref(slug);

    fetchVerify(slug)
      .then(function (resp) {
        var status = resp.status;
        var body = resp.body || {};
        if (status === 200 && body.valid === true) {
          renderValid(body);
        } else if (
          status === 200 &&
          body.valid === false &&
          body.reason === "expired"
        ) {
          renderExpired(body);
        } else if (status === 404) {
          renderUnknown(slug);
        } else if (status === 429) {
          renderRateLimited(body);
        } else {
          show("error");
        }
      })
      .catch(function () {
        show("error");
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
