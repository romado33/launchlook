/**
 * Renders LAUNCHLOOK_E2E.SECTIONS into #checklist-root. Load after e2e-checklist-data.js.
 */
(function () {
  function renderChecklist() {
    var cfg = window.LAUNCHLOOK_E2E;
    var root = document.getElementById("checklist-root");
    var resetBtn = document.getElementById("reset-btn");
    if (!cfg || !root || !cfg.SECTIONS) return;

    var STORAGE_KEY = cfg.STORAGE_KEY;
    var SECTIONS = cfg.SECTIONS;

    function loadState() {
      try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      } catch (e) {
        return {};
      }
    }

    function saveState(state) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }

    function allItems() {
      var items = [];
      SECTIONS.forEach(function (s) {
        s.items.forEach(function (item) {
          items.push(item);
        });
      });
      return items;
    }

    function updateProgress(state) {
      var items = allItems();
      var done = items.filter(function (i) {
        return state[i.id];
      }).length;
      var total = items.length;
      var pct = total ? Math.round((done / total) * 100) : 0;
      var label = document.getElementById("progress-label");
      var bar = document.getElementById("progress-bar");
      if (label) label.textContent = done + " / " + total;
      if (bar) bar.style.width = pct + "%";
    }

    function render() {
      var state = loadState();
      root.innerHTML = "";

      SECTIONS.forEach(function (section) {
        var sec = document.createElement("section");
        sec.className = "rounded-xl border border-line bg-white px-4 py-4 sm:px-5 sm:py-5";
        sec.id = section.id;

        var h2 = document.createElement("h2");
        h2.className = "font-serif text-lg text-ink";
        h2.textContent = section.title;
        sec.appendChild(h2);

        var ul = document.createElement("ul");
        ul.className = "mt-4 space-y-3";

        section.items.forEach(function (item) {
          var li = document.createElement("li");
          li.className = "check-row flex gap-3 items-start text-sm";

          var input = document.createElement("input");
          input.type = "checkbox";
          input.id = item.id;
          input.checked = !!state[item.id];
          input.className =
            "mt-1 h-4 w-4 rounded border-line text-accent focus:ring-accent/60 shrink-0 cursor-pointer";
          input.addEventListener("change", function () {
            var s = loadState();
            s[item.id] = input.checked;
            saveState(s);
            updateProgress(s);
          });

          var wrap = document.createElement("div");
          var label = document.createElement("label");
          label.htmlFor = item.id;
          label.className = "text-ink cursor-pointer leading-relaxed";
          label.textContent = item.label;
          wrap.appendChild(label);
          if (item.hint) {
            var hint = document.createElement("p");
            hint.className = "hint text-xs text-muted mt-0.5";
            hint.textContent = item.hint;
            wrap.appendChild(hint);
          }

          li.appendChild(input);
          li.appendChild(wrap);
          ul.appendChild(li);
        });

        sec.appendChild(ul);
        root.appendChild(sec);
      });

      updateProgress(state);
    }

    if (resetBtn && !resetBtn.dataset.e2eBound) {
      resetBtn.dataset.e2eBound = "1";
      resetBtn.addEventListener("click", function () {
        if (!confirm("Clear all checkmarks in this browser?")) return;
        localStorage.removeItem(STORAGE_KEY);
        render();
      });
    }

    render();
  }

  window.launchlookE2eRenderChecklist = renderChecklist;
})();
