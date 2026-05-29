/*
 * r.js: progressive client-side renderer for /r/{slug}.
 *
 * The per-customer HTML at /r/{slug}.html bakes in the social-share meta
 * tags so OG scrapers (Reddit, Twitter, LinkedIn) preview correctly.
 * This script then populates the body content from
 * /data/reports/{slug}.json, respects ``is_public``, and shows the
 * appropriate state (private / public / missing / error).
 *
 * Discipline notes:
 *   - Privacy by default. If ``is_public`` is false, we render the
 *     gentle "private" message and DO NOT show any finding text, even
 *     though the JSON file is readable in the network tab. The JSON
 *     never contains the customer's URL or email (sanitized at delivery
 *     time by scripts/sanitize_for_public.py).
 *   - We never fetch screenshots. The screenshots stay on disk in the
 *     customer's output/ directory, never shipped to the public surface.
 *   - Plausible custom event ``ReportView`` fires once with the state
 *     and slug so we can watch traffic without server logs.
 */

(function () {
  "use strict";

  var STATES = ["loading", "private", "missing", "public", "error"];

  function show(state) {
    STATES.forEach(function (key) {
      var el = document.querySelector('[data-r-state="' + key + '"]');
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
      window.plausible("ReportView", {
        props: { state: state, slug: readSlug() },
      });
    } catch (e) {
      /* analytics is best-effort, never break the page */
    }
  }

  function readSlug() {
    // Per-customer pages set <body data-slug="..."> via the delivery
    // script. The catch-all r.html reads ?slug= from the query string.
    var rootBody = document.body;
    if (rootBody && rootBody.dataset && rootBody.dataset.slug) {
      return rootBody.dataset.slug.trim();
    }
    try {
      var qs = new URLSearchParams(window.location.search);
      return (qs.get("slug") || "").trim();
    } catch (e) {
      return "";
    }
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

  function flowText(value) {
    return String(value == null ? "" : value)
      .replace(/\s*\n+\s*/g, " ")
      .replace(/\s{2,}/g, " ")
      .trim();
  }

  function setText(selector, value) {
    var el = document.querySelector(selector);
    if (el) el.textContent = value == null ? "" : value;
  }

  // The 7-persona named labels (The Tourist / Skeptic / Klutz / Snoop /
  // Phone-First Friend / Saboteur / Stranger) were pulled from customer
  // surfaces in the May 2026 simplification pass. The CSS classes in
  // assets/site.css and the personaClass helper below are kept dormant
  // so re-enabling display is a one-line change in renderPublic().
  function personaClass(tag) {
    if (!tag) return "";
    if (tag.indexOf("Skeptic") !== -1) return "persona-skeptic";
    if (tag.indexOf("Klutz") !== -1) return "persona-klutz";
    if (tag.indexOf("Tourist") !== -1) return "persona-tourist";
    if (tag.indexOf("Snoop") !== -1) return "persona-snoop";
    if (tag.indexOf("Phone-First Friend") !== -1)
      return "persona-phone-first-friend";
    if (tag.indexOf("Saboteur") !== -1) return "persona-saboteur";
    if (tag.indexOf("Stranger") !== -1) return "persona-stranger";
    return "";
  }

  function renderPublic(slug, data) {
    var appName =
      data.app_name || (data.customer && data.customer.app_name) || "this app";
    var tier = data.tier || (data.customer && data.customer.tier) || "audit";
    var tierShort = tier.replace(/\s+Package$/i, "");

    document.title = "LaunchLook audit: " + appName;

    var isSample =
      (document.body && document.body.dataset.isSample === "true") ||
      slug === "jane-sparkle-marketplace";
    setText(
      "[data-r-eyebrow]",
      isSample
        ? "LaunchLook \u00b7 sample audit"
        : "LaunchLook \u00b7 " + tierShort + " audit",
    );
    setText("[data-r-app-name]", appName);
    var auditLine =
      "Pre-launch audit prepared " + humanDate(data.audit_date || "") + ".";
    if (data.customer && data.customer.builder) {
      auditLine = auditLine + " Built with " + data.customer.builder + ".";
    }
    setText("[data-r-audit-line]", auditLine);

    var verdict = data.verdict || {};
    setText("[data-r-verdict-label]", verdict.label || verdict.summary || "");
    if (verdict.label && verdict.summary && verdict.label !== verdict.summary) {
      setText("[data-r-verdict-summary]", verdict.summary);
    } else {
      setText("[data-r-verdict-summary]", "");
    }
    setText("[data-r-verdict-narrative]", verdict.narrative || "");

    var passed = data.passed_checks || [];
    if (passed.length) {
      var wrap = document.querySelector("[data-r-passed-wrap]");
      var list = document.querySelector("[data-r-passed]");
      if (wrap && list) {
        passed.forEach(function (item) {
          var li = document.createElement("li");
          li.className = "flex gap-2 text-ink";
          var check = document.createElement("span");
          check.className = "text-accent font-semibold";
          check.setAttribute("aria-hidden", "true");
          check.textContent = "\u2713";
          var text = document.createElement("span");
          text.textContent = item;
          li.appendChild(check);
          li.appendChild(text);
          list.appendChild(li);
        });
        wrap.classList.remove("hidden");
      }
    }

    if (isSample) {
      var intro = document.querySelector("[data-r-sample-intro]");
      if (intro) intro.classList.remove("hidden");

      var statsEl = document.querySelector("[data-r-stats]");
      var findingsForStats = data.findings || [];
      if (statsEl && findingsForStats.length) {
        var counts = { critical: 0, high: 0, medium: 0, low: 0 };
        findingsForStats.forEach(function (f) {
          var s = (f.severity || "low").toLowerCase();
          if (counts[s] != null) counts[s] += 1;
        });
        var parts = [];
        if (counts.critical) parts.push(counts.critical + " critical");
        if (counts.high) parts.push(counts.high + " high");
        if (counts.medium) parts.push(counts.medium + " medium");
        if (counts.low) parts.push(counts.low + " low");
        statsEl.textContent =
          findingsForStats.length +
          " findings" +
          (parts.length ? " · " + parts.join(" · ") : "");
      }
    }

    var findings = data.findings || [];
    if (findings.length) {
      var fwrap = document.querySelector("[data-r-findings-wrap]");
      var fcontainer = document.querySelector("[data-r-findings]");
      if (fwrap && fcontainer) {
        // Sort by severity, mirroring the PDF order.
        var sevOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        findings
          .slice()
          .sort(function (a, b) {
            var av = sevOrder[a.severity] == null ? 99 : sevOrder[a.severity];
            var bv = sevOrder[b.severity] == null ? 99 : sevOrder[b.severity];
            return av - bv;
          })
          .forEach(function (f, idx) {
            var card = document.createElement("article");
            var sev = (f.severity || "low").toLowerCase();
            card.className =
              "rounded-xl border border-line bg-white p-5 shadow-sm shadow-ink/5 finding-card finding-" +
              sev;
            card.setAttribute("data-severity", sev);

            var head = document.createElement("div");
            head.className = "flex flex-wrap items-baseline gap-2 mb-2";

            var sevPill = document.createElement("span");
            sevPill.className =
              "text-[10px] font-semibold uppercase tracking-widest text-muted";
            sevPill.textContent = sev;
            head.appendChild(sevPill);

            var title = document.createElement("h3");
            title.className = "font-medium text-base text-ink flex-1";
            title.textContent = f.title || "Finding " + (idx + 1);
            head.appendChild(title);

            // f.tag (e.g. "Caught by The Snoop") is intentionally NOT
            // rendered on customer surfaces as of the May 2026
            // simplification pass. Backend still tags findings internally
            // for routing; only the visible pill is gone.

            card.appendChild(head);

            if (f.what_we_saw) {
              var p1 = document.createElement("p");
              p1.className =
                "mt-2 text-sm text-muted leading-relaxed report-body-copy";
              var label1 = document.createElement("strong");
              label1.className = "text-ink";
              label1.textContent = "What I saw. ";
              p1.appendChild(label1);
              p1.appendChild(document.createTextNode(flowText(f.what_we_saw)));
              card.appendChild(p1);
            }
            if (f.why_it_matters) {
              var p2 = document.createElement("p");
              p2.className =
                "mt-2 text-sm text-muted leading-relaxed report-body-copy";
              var label2 = document.createElement("strong");
              label2.className = "text-ink";
              label2.textContent = "Why it matters. ";
              p2.appendChild(label2);
              p2.appendChild(document.createTextNode(flowText(f.why_it_matters)));
              card.appendChild(p2);
            }
            if (isSample && f.fix_prompt) {
              var prompt = document.createElement("details");
              prompt.className = "report-fix-prompt";
              var summary = document.createElement("summary");
              summary.textContent = "Paste into your AI builder to fix this";
              prompt.appendChild(summary);
              var pre = document.createElement("pre");
              pre.textContent = String(f.fix_prompt).trim();
              prompt.appendChild(pre);
              card.appendChild(prompt);
            }
            fcontainer.appendChild(card);
          });
        fwrap.classList.remove("hidden");
      }
    }

    // Handoff Report download. Pro tier + customer opted in via
    // scripts/share_report.py --share-handoff.
    var handoff = data.handoff_report || {};
    if (handoff.available && handoff.shared) {
      var hwrap = document.querySelector("[data-r-handoff]");
      var hlink = document.querySelector("[data-r-handoff-link]");
      if (hwrap && hlink) {
        hlink.setAttribute(
          "href",
          "/data/handoff/" + encodeURIComponent(slug) + ".pdf",
        );
        hwrap.classList.remove("hidden");
      }
    }

    if (isSample) {
      document.querySelectorAll("[data-r-sample-cta]").forEach(function (el) {
        el.remove();
      });
    }

    show("public");
  }

  function fetchReport(slug) {
    var url = "/data/reports/" + encodeURIComponent(slug) + ".json";
    return fetch(url, {
      headers: { Accept: "application/json" },
      credentials: "omit",
      cache: "no-cache",
    })
      .then(function (res) {
        return { status: res.status, body: res.ok ? res.json() : null };
      })
      .then(function (resp) {
        if (!resp.body) {
          return { status: resp.status, body: null };
        }
        return resp.body.then(function (json) {
          return { status: resp.status, body: json };
        });
      });
  }

  function applyReviewerFooter() {
    var cfg = window.LAUNCHLOOK_CONFIG || {};
    var name = ((cfg.reviewerName || cfg.founderName || "") + "").trim();
    var line = name
      ? "Reviewed by " + name + " before delivery."
      : "Reviewed by a human reviewer.";
    document.querySelectorAll("[data-r-reviewer-line]").forEach(function (el) {
      el.textContent = line;
    });
  }

  function init() {
    applyReviewerFooter();
    var slug = readSlug();
    if (!slug) {
      show("missing");
      return;
    }
    show("loading");
    fetchReport(slug)
      .then(function (resp) {
        if (resp.status === 404 || !resp.body) {
          show("missing");
          return;
        }
        var data = resp.body;
        if (data.is_public !== true) {
          show("private");
          return;
        }
        renderPublic(slug, data);
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
