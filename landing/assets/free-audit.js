/*
 * free-audit.js — progressive enhancement for the free 3-finding audit form.
 *
 * Hijacks the form's submit so the page can POST JSON to /api/free-audit,
 * show a friendly error inline if rate-limited or invalid, and redirect to
 * /thanks-free-audit on success without a full page reload that would lose
 * the URL and email the customer just typed.
 *
 * Falls back gracefully: if JS is disabled or the fetch fails outright, the
 * native form POST still goes through and Vercel routes it to the serverless
 * function (the API returns 303 to /thanks-free-audit in that path).
 */

(function () {
  "use strict";

  function attach(form) {
    if (form.__launchlookFreeAuditBound) return;
    form.__launchlookFreeAuditBound = true;

    var errorEl = form.querySelector("[data-free-audit-status]");
    var submitBtn = form.querySelector('button[type="submit"]');

    function showError(msg) {
      if (!errorEl) return;
      errorEl.textContent = msg;
      errorEl.classList.remove("hidden");
    }

    function clearError() {
      if (!errorEl) return;
      errorEl.textContent = "";
      errorEl.classList.add("hidden");
    }

    function onSubmit(event) {
      event.preventDefault();
      clearError();
      if (submitBtn) {
        submitBtn.setAttribute("aria-disabled", "true");
        submitBtn.dataset.label =
          submitBtn.dataset.label || submitBtn.textContent;
        submitBtn.textContent = "Sending...";
      }

      var payload = {};
      // Pull every named input the form has (URL, email, optional platform).
      Array.prototype.forEach.call(form.elements, function (el) {
        if (!el.name) return;
        payload[el.name] = (el.value || "").trim();
      });

      fetch("/api/free-audit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(payload),
        credentials: "same-origin",
      })
        .then(function (res) {
          return res.json().then(function (data) {
            return { ok: res.ok, status: res.status, data: data };
          });
        })
        .then(function (resp) {
          if (
            resp.ok &&
            resp.data &&
            (resp.data.status === "queued" || resp.data.status === "duplicate")
          ) {
            window.location.assign("/thanks-free-audit");
            return;
          }
          var msg =
            (resp.data && resp.data.message) ||
            "Something went wrong on our end. Email hello@launchlook.app and we will sort it.";
          showError(msg);
          if (submitBtn) {
            submitBtn.removeAttribute("aria-disabled");
            submitBtn.textContent =
              submitBtn.dataset.label || "Get my free 3 findings";
          }
        })
        .catch(function () {
          // Network blip: fall back to a native form POST so the request still
          // reaches the serverless function.
          form.removeEventListener("submit", onSubmit);
          form.submit();
        });
    }

    form.addEventListener("submit", onSubmit);
  }

  function init() {
    var forms = document.querySelectorAll("form[data-free-audit-form]");
    Array.prototype.forEach.call(forms, attach);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
