/* LaunchLook Audit UI — single-file front-end controller.
 *
 * Responsibilities:
 *   - Load bootstrap data (prefill, draft offer, tier caps).
 *   - Manage the form state in a single mutable object (state.payload).
 *   - Render dynamic finding cards + QSG step cards from <template> tags.
 *   - Sort findings live by severity for the visible preview.
 *   - Debounced auto-save (1s) + periodic 30s heartbeat save to the backend.
 *   - Drag-and-drop screenshot upload tied to a finding index.
 *   - Generate YAML, "Save + send PDFs" with live deliver-log polling.
 *   - Open-existing-customer modal.
 *
 * No frameworks — vanilla JS, DOM-driven.
 */

(function () {
  "use strict";

  const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  // ---------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------

  const state = {
    slug: "",
    tierCaps: window.AUDIT_UI_BOOTSTRAP?.tier_caps || { "Starter Package": 10, "Scale Up Package": 30, "Pro Package": 40 },
    payload: blankPayload(),
    autosaveTimer: null,
    autosaveHeartbeat: null,
    deliverPollTimer: null,
    deliverOffset: 0,
    pendingScreenshotUploads: 0,
    reviewAi: !!window.AUDIT_UI_BOOTSTRAP?.review_ai,
    reviewStatus: [],   // per-finding-index: "draft" | "approved" | "edited" | "rejected"
    aiBaseline: [],     // per-finding-index: snapshot of AI title/severity at load
    regenInFlight: new Set(),
  };

  function blankPayload() {
    return {
      customer: {
        first_name: "",
        last_name: "",
        email: "",
        app_name: "",
        app_url: "",
        url_redacted: false,
        tier: "",
        builder: "",
        platform: (window.AUDIT_UI_BOOTSTRAP && window.AUDIT_UI_BOOTSTRAP.default_platform) || "vibe-coder",
      },
      verdict: { emoji: "", summary: "", narrative: "" },
      findings: [],
      quick_start_guide: { title: "", intro: "", steps: [], footer_note: "" },
    };
  }

  function newFinding() {
    return {
      severity: "",
      title: "",
      what_we_saw: "",
      why_it_matters: "",
      screenshot_path: "",
      screenshot_caption: "",
      fix_prompt: "",
      category: "",
      tag: "",
    };
  }

  function newStep() {
    return { title: "", body: "" };
  }

  // ---------------------------------------------------------------------
  // Boot
  // ---------------------------------------------------------------------

  document.addEventListener("DOMContentLoaded", boot);

  async function boot() {
    bindStaticHandlers();

    // /review/<slug> passes review_slug via the page bootstrap; fetch with it so
    // api/bootstrap loads customer data even if the server wasn't started with --review-ai.
    const pageReviewSlug = window.AUDIT_UI_BOOTSTRAP?.review_slug || null;
    const bootstrapUrl = pageReviewSlug
      ? `/api/bootstrap?slug=${encodeURIComponent(pageReviewSlug)}&review_ai=1`
      : "/api/bootstrap";

    let bootstrap = null;
    try {
      bootstrap = await fetch(bootstrapUrl).then((r) => r.json());
    } catch (err) {
      setStatus("Failed to load bootstrap: " + err.message, "error");
      return;
    }
    if (bootstrap.tier_caps) state.tierCaps = bootstrap.tier_caps;
    state.reviewAi = !!bootstrap.review_ai;

    if (bootstrap.prefill && Object.keys(bootstrap.prefill).length) {
      applyPrefill(bootstrap.prefill);
    }

    state.slug = (bootstrap.slug || "").trim();
    if (state.slug) {
      const slugInput = $('[data-field="slug"]');
      if (slugInput && !slugInput.value) slugInput.value = state.slug;
    }
    updateSlugDisplay();

    // Review mode: prefer the existing customer YAML over a stale draft.
    if (state.reviewAi && bootstrap.customer && bootstrap.customer.payload) {
      state.payload = mergePayload(blankPayload(), bootstrap.customer.payload);
      initializeReviewBaseline(bootstrap.feedback);
      writePayloadToForm();
      showYamlPreview(bootstrap.customer.yaml || "");
      setStatus(`Loaded AI draft → customers/${state.slug}.yaml`, "success");
    } else if (bootstrap.draft && bootstrap.draft.payload) {
      offerDraftRestore(bootstrap.draft);
    } else {
      writePayloadToForm();
    }

    refreshFindingsCounter();
    refreshQsgVisibility();
    refreshReviewBanner();
    if (!state.reviewAi) setStatus("Ready.", "");

    state.autosaveHeartbeat = setInterval(autosaveNow, 30000);
  }

  function initializeReviewBaseline(feedback) {
    const findings = state.payload.findings || [];
    state.aiBaseline = findings.map((f) => ({
      title: f.title || "",
      severity: f.severity || "",
    }));
    state.reviewStatus = findings.map(() => "draft");

    // Replay any previously-recorded actions so a re-opened review keeps
    // its "✓ approved" highlights across page reloads.
    if (feedback && Array.isArray(feedback.actions)) {
      feedback.actions.forEach((entry) => {
        const idx = entry.finding_idx;
        if (typeof idx !== "number" || idx < 0 || idx >= state.reviewStatus.length) return;
        const action = (entry.action || "draft").toLowerCase();
        if (action === "approved" || action === "edited" || action === "rejected") {
          state.reviewStatus[idx] = action;
        }
      });
    }
  }

  function applyPrefill(prefill) {
    if (prefill.slug) state.slug = prefill.slug;
    const c = state.payload.customer;
    if (prefill.first_name) c.first_name = prefill.first_name;
    if (prefill.last_name) c.last_name = prefill.last_name;
    if (prefill.email) c.email = prefill.email;
    if (prefill.app_name) c.app_name = prefill.app_name;
    if (prefill.app_url) c.app_url = prefill.app_url;
    if (prefill.tier) c.tier = prefill.tier;
    if (prefill.builder) c.builder = prefill.builder;
    if (prefill.platform) c.platform = prefill.platform;
    if (typeof prefill.url_redacted === "boolean") c.url_redacted = prefill.url_redacted;

    if (prefill.first_name || prefill.email) {
      const card = $('[data-section="customer"]');
      if (card) card.classList.add("is-collapsed");
      const toggle = $(".card__toggle", card);
      if (toggle) {
        toggle.setAttribute("aria-expanded", "false");
        toggle.textContent = "Show";
      }
    }
  }

  // ---------------------------------------------------------------------
  // Event wiring
  // ---------------------------------------------------------------------

  function bindStaticHandlers() {
    document.addEventListener("input", onFormInput, true);
    document.addEventListener("change", onFormChange, true);
    document.addEventListener("click", onFormClick);

    document.addEventListener("dragover", (ev) => {
      const drop = ev.target.closest("[data-screenshot-drop]");
      if (drop) {
        ev.preventDefault();
        drop.classList.add("is-dragover");
      }
    });
    document.addEventListener("dragleave", (ev) => {
      const drop = ev.target.closest("[data-screenshot-drop]");
      if (drop && !drop.contains(ev.relatedTarget)) {
        drop.classList.remove("is-dragover");
      }
    });
    document.addEventListener("drop", (ev) => {
      const drop = ev.target.closest("[data-screenshot-drop]");
      if (!drop) return;
      ev.preventDefault();
      drop.classList.remove("is-dragover");
      const file = ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0];
      const card = drop.closest("[data-finding]");
      if (file && card) handleScreenshotFile(card, file);
    });
  }

  function onFormInput(ev) {
    const target = ev.target;
    if (!(target instanceof HTMLElement)) return;
    if (handleNamedField(target)) {
      scheduleAutosave();
    }
  }

  function onFormChange(ev) {
    const target = ev.target;
    if (!(target instanceof HTMLElement)) return;
    if (target.matches('[data-field="screenshot_file"]')) {
      const file = target.files && target.files[0];
      const card = target.closest("[data-finding]");
      if (file && card) handleScreenshotFile(card, file);
      return;
    }
    if (handleNamedField(target)) {
      if (target.dataset.field === "customer.tier") refreshQsgVisibility();
      if (target.dataset.field === "severity") {
        // re-sort findings live as severities change
        sortAndRenderFindings();
      }
      scheduleAutosave();
    }
  }

  function onFormClick(ev) {
    const action = ev.target.closest("[data-action]");
    if (!action) return;
    const which = action.dataset.action;

    switch (which) {
      case "toggle-section":
        toggleSection(action);
        break;
      case "add-finding":
        addFinding();
        break;
      case "remove-finding":
        removeFinding(action.closest("[data-finding]"));
        break;
      case "add-step":
        addStep();
        break;
      case "remove-step":
        removeStep(action.closest("[data-step]"));
        break;
      case "remove-screenshot":
        removeScreenshot(action.closest("[data-finding]"));
        break;
      case "save-draft":
        autosaveNow(true);
        break;
      case "generate-yaml":
        generateYaml({ andDeliver: false });
        break;
      case "deliver-send":
        generateYaml({ andDeliver: true });
        break;
      case "approve-finding":
        approveFinding(action.closest("[data-finding]"));
        break;
      case "reject-finding":
        rejectFinding(action.closest("[data-finding]"));
        break;
      case "regenerate-finding":
        regenerateFinding(action.closest("[data-finding]"));
        break;
      case "approve-all-ship":
        approveAllAndShip();
        break;
      case "open-customer":
        openCustomerModal();
        break;
      case "close-modal":
        closeCustomerModal();
        break;
    }
  }

  function handleNamedField(el) {
    const key = el.dataset.field;
    if (!key) return false;

    if (key === "slug") {
      state.slug = el.value.trim();
      updateSlugDisplay();
      return true;
    }

    const card = el.closest("[data-finding]");
    if (card) {
      const idx = parseInt(card.dataset.findingIndex, 10);
      const finding = state.payload.findings[idx];
      if (!finding) return false;
      if (key === "severity") {
        finding.severity = el.value;
        card.dataset.severity = el.value;
      } else if (key in finding) {
        finding[key] = el.value;
      }
      if (state.reviewAi && (key === "title" || key === "severity")) {
        markEditedIfChanged(idx);
      }
      return true;
    }

    const stepEl = el.closest("[data-step]");
    if (stepEl) {
      const idx = parseInt(stepEl.dataset.stepIndex, 10);
      const step = state.payload.quick_start_guide.steps[idx];
      if (!step) return false;
      if (key in step) step[key] = el.value;
      return true;
    }

    if (key.startsWith("customer.")) {
      const prop = key.slice("customer.".length);
      if (el.type === "checkbox") {
        state.payload.customer[prop] = el.checked;
      } else if (el.type === "radio") {
        if (el.checked) state.payload.customer[prop] = el.value;
      } else {
        state.payload.customer[prop] = el.value;
      }
      return true;
    }

    if (key.startsWith("verdict.")) {
      const prop = key.slice("verdict.".length);
      if (el.type === "radio") {
        if (el.checked) state.payload.verdict[prop] = el.value;
      } else {
        state.payload.verdict[prop] = el.value;
      }
      return true;
    }

    if (key.startsWith("qsg.")) {
      const prop = key.slice("qsg.".length);
      if (prop in state.payload.quick_start_guide) {
        state.payload.quick_start_guide[prop] = el.value;
      }
      return true;
    }

    if (key === "url_redacted") {
      state.payload.customer.url_redacted = el.checked;
      return true;
    }

    return false;
  }

  // ---------------------------------------------------------------------
  // Findings list
  // ---------------------------------------------------------------------

  function addFinding(initial) {
    const cap = currentTierCap();
    if (cap && state.payload.findings.length >= cap) {
      setStatus(`At cap: ${cap} findings for ${state.payload.customer.tier || "this tier"}.`, "error");
      return;
    }
    state.payload.findings.push(initial || newFinding());
    state.aiBaseline.push({ title: "", severity: "" });
    state.reviewStatus.push("draft");
    renderFindings();
    refreshFindingsCounter();
    refreshReviewBanner();
    scheduleAutosave();
  }

  function removeFinding(card) {
    if (!card) return;
    const idx = parseInt(card.dataset.findingIndex, 10);
    if (Number.isNaN(idx)) return;
    state.payload.findings.splice(idx, 1);
    if (state.aiBaseline.length > idx) state.aiBaseline.splice(idx, 1);
    if (state.reviewStatus.length > idx) state.reviewStatus.splice(idx, 1);
    renderFindings();
    refreshFindingsCounter();
    refreshReviewBanner();
    scheduleAutosave();
  }

  function sortAndRenderFindings() {
    // When sorting we also keep aiBaseline / reviewStatus aligned with the
    // re-ordered findings, so each card's "edited vs AI" comparison and
    // review badge follow it.
    const tagged = state.payload.findings.map((f, idx) => ({
      finding: f,
      baseline: state.aiBaseline[idx] || { title: f.title || "", severity: f.severity || "" },
      status: state.reviewStatus[idx] || "draft",
    }));
    tagged.sort((a, b) => {
      const ao = SEVERITY_ORDER[a.finding.severity] ?? 99;
      const bo = SEVERITY_ORDER[b.finding.severity] ?? 99;
      return ao - bo;
    });
    state.payload.findings = tagged.map((t) => t.finding);
    state.aiBaseline = tagged.map((t) => t.baseline);
    state.reviewStatus = tagged.map((t) => t.status);
    renderFindings();
  }

  function renderFindings() {
    const list = $("[data-findings-list]");
    if (!list) return;
    list.innerHTML = "";
    const tpl = $("#tpl-finding-card");
    state.payload.findings.forEach((finding, idx) => {
      const node = tpl.content.firstElementChild.cloneNode(true);
      node.dataset.findingIndex = String(idx);
      node.dataset.severity = finding.severity || "";
      $("[data-finding-index]", node).textContent = String(idx + 1);

      $('[data-field="severity"]', node).value = finding.severity || "";
      $('[data-field="title"]', node).value = finding.title || "";
      $('[data-field="what_we_saw"]', node).value = finding.what_we_saw || "";
      $('[data-field="why_it_matters"]', node).value = finding.why_it_matters || "";
      $('[data-field="screenshot_caption"]', node).value = finding.screenshot_caption || "";
      $('[data-field="fix_prompt"]', node).value = finding.fix_prompt || "";

      const preview = $("[data-screenshot-preview]", node);
      const previewImg = $("[data-screenshot-img]", node);
      const previewName = $("[data-screenshot-filename]", node);
      const hint = $(".screenshot-drop__hint", node);

      if (finding.screenshot_path) {
        if (preview) preview.hidden = false;
        if (hint) hint.style.display = "none";
        if (previewImg) previewImg.src = "/" + finding.screenshot_path;
        if (previewName) previewName.textContent = finding.screenshot_path;
      }

      applyReviewVisuals(node, idx);
      list.appendChild(node);
    });
  }

  function applyReviewVisuals(card, idx) {
    const reviewActions = card.querySelector("[data-review-actions]");
    const legacyRemove = card.querySelector('[data-action="remove-finding"][data-non-review]');
    const badge = card.querySelector("[data-review-badge]");

    if (state.reviewAi) {
      if (reviewActions) reviewActions.hidden = false;
      if (legacyRemove) legacyRemove.hidden = true;
      const status = state.reviewStatus[idx] || "draft";
      card.dataset.reviewStatus = status;
      if (badge) {
        badge.hidden = status === "draft";
        if (status === "approved") badge.textContent = "✓ approved";
        else if (status === "edited") badge.textContent = "✎ edited";
        else if (status === "rejected") badge.textContent = "× rejected";
        else badge.textContent = "";
      }
      if (state.regenInFlight.has(idx)) {
        card.classList.add("is-regenerating");
      } else {
        card.classList.remove("is-regenerating");
      }
    } else {
      if (reviewActions) reviewActions.hidden = true;
      if (legacyRemove) legacyRemove.hidden = false;
      if (badge) badge.hidden = true;
    }
  }

  function refreshFindingsCounter() {
    const counter = $("[data-findings-counter]");
    if (!counter) return;
    const cap = currentTierCap();
    const n = state.payload.findings.length;
    counter.textContent = cap ? `${n} / ${cap} findings` : `${n} findings`;
    counter.classList.toggle("is-cap", !!(cap && n >= cap));

    const addBtn = $('[data-action="add-finding"]');
    if (addBtn) addBtn.disabled = !!(cap && n >= cap);
  }

  function currentTierCap() {
    const tier = state.payload.customer.tier;
    if (!tier) return null;
    return state.tierCaps[tier] || null;
  }

  // ---------------------------------------------------------------------
  // QSG + steps
  // ---------------------------------------------------------------------

  function refreshQsgVisibility() {
    const qsgCard = $('[data-section="qsg"]');
    if (!qsgCard) return;
    const tier = state.payload.customer.tier;
    const showQsg = (
      tier === "Starter Package" ||
      tier === "Scale Up Package" ||
      tier === "Pro Package"
    );
    qsgCard.hidden = !showQsg;
    refreshFindingsCounter();
  }

  function addStep(initial) {
    state.payload.quick_start_guide.steps.push(initial || newStep());
    renderSteps();
    scheduleAutosave();
  }

  function removeStep(card) {
    if (!card) return;
    const idx = parseInt(card.dataset.stepIndex, 10);
    if (Number.isNaN(idx)) return;
    state.payload.quick_start_guide.steps.splice(idx, 1);
    renderSteps();
    scheduleAutosave();
  }

  function renderSteps() {
    const list = $("[data-steps-list]");
    if (!list) return;
    list.innerHTML = "";
    const tpl = $("#tpl-step-card");
    state.payload.quick_start_guide.steps.forEach((step, idx) => {
      const node = tpl.content.firstElementChild.cloneNode(true);
      node.dataset.stepIndex = String(idx);
      $("[data-step-index]", node).textContent = String(idx + 1);
      $('[data-field="title"]', node).value = step.title || "";
      $('[data-field="body"]', node).value = step.body || "";
      list.appendChild(node);
    });
  }

  // ---------------------------------------------------------------------
  // Section toggling
  // ---------------------------------------------------------------------

  function toggleSection(button) {
    const card = button.closest(".card");
    if (!card) return;
    const collapsed = card.classList.toggle("is-collapsed");
    button.setAttribute("aria-expanded", collapsed ? "false" : "true");
    button.textContent = collapsed ? "Show" : "Hide";
  }

  // ---------------------------------------------------------------------
  // Slug display
  // ---------------------------------------------------------------------

  function updateSlugDisplay() {
    const el = $("[data-slug-display]");
    if (!el) return;
    el.textContent = state.slug ? `customers/${state.slug}.yaml` : "(no slug)";
  }

  // ---------------------------------------------------------------------
  // Form ↔ payload sync
  // ---------------------------------------------------------------------

  function writePayloadToForm() {
    const c = state.payload.customer;

    setVal('[data-field="slug"]', state.slug || "");
    setVal('[data-field="customer.first_name"]', c.first_name);
    setVal('[data-field="customer.last_name"]', c.last_name);
    setVal('[data-field="customer.email"]', c.email);
    setVal('[data-field="customer.app_name"]', c.app_name);
    setVal('[data-field="customer.app_url"]', c.app_url);
    setVal('[data-field="customer.builder"]', c.builder);
    setVal('[data-field="customer.platform"]', c.platform || (bootstrap.default_platform || "vibe-coder"));
    setRadio('[data-field="customer.tier"]', c.tier);
    setCheckbox('[data-field="url_redacted"]', !!c.url_redacted);

    const v = state.payload.verdict;
    setRadio('[data-field="verdict.emoji"]', v.emoji);
    setVal('[data-field="verdict.summary"]', v.summary);
    setVal('[data-field="verdict.narrative"]', v.narrative);

    const q = state.payload.quick_start_guide;
    setVal('[data-field="qsg.title"]', q.title || "");
    setVal('[data-field="qsg.intro"]', q.intro || "");
    setVal('[data-field="qsg.footer_note"]', q.footer_note || "");

    renderFindings();
    renderSteps();
    refreshQsgVisibility();
    refreshFindingsCounter();
  }

  function setVal(sel, value) {
    const el = $(sel);
    if (el) el.value = value || "";
  }

  function setRadio(sel, value) {
    $$(sel).forEach((el) => {
      el.checked = el.value === value;
    });
  }

  function setCheckbox(sel, value) {
    const el = $(sel);
    if (el) el.checked = !!value;
  }

  // ---------------------------------------------------------------------
  // Auto-save (debounced + heartbeat)
  // ---------------------------------------------------------------------

  function scheduleAutosave() {
    clearTimeout(state.autosaveTimer);
    setAutosaveStatus("saving");
    state.autosaveTimer = setTimeout(() => autosaveNow(false), 1000);
  }

  async function autosaveNow(viaButton) {
    if (!state.slug) {
      setAutosaveStatus("idle");
      if (viaButton) setStatus("Set a slug before saving a draft.", "error");
      return;
    }
    try {
      const resp = await fetch("/api/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug: state.slug, payload: state.payload }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Save failed");
      setAutosaveStatus("saved");
      if (viaButton) setStatus(`Draft saved → ${data.path}`, "success");
    } catch (err) {
      setAutosaveStatus("idle");
      if (viaButton) setStatus("Save failed: " + err.message, "error");
    }
  }

  function setAutosaveStatus(state_) {
    const el = $("[data-autosave-status]");
    if (!el) return;
    el.classList.remove("is-saving", "is-saved");
    if (state_ === "saving") {
      el.classList.add("is-saving");
      el.textContent = "Saving…";
    } else if (state_ === "saved") {
      el.classList.add("is-saved");
      el.textContent = "Draft saved";
    } else {
      el.textContent = "idle";
    }
  }

  function offerDraftRestore(draftRecord) {
    const toast = $("[data-toast]");
    const body = $("[data-toast-body]");
    const confirm = $("[data-toast-confirm]");
    const dismiss = $("[data-toast-dismiss]");
    if (!toast) return;

    body.textContent = `Found an unsaved draft for "${state.slug}" from ${formatDate(draftRecord.saved_at)}. Restore?`;
    toast.hidden = false;

    confirm.onclick = () => {
      restorePayload(draftRecord.payload);
      toast.hidden = true;
      setStatus("Draft restored.", "success");
    };
    dismiss.onclick = () => {
      toast.hidden = true;
      writePayloadToForm();
    };
  }

  function restorePayload(payload) {
    state.payload = mergePayload(blankPayload(), payload || {});
    writePayloadToForm();
  }

  function mergePayload(base, incoming) {
    base.customer = { ...base.customer, ...(incoming.customer || {}) };
    base.verdict = { ...base.verdict, ...(incoming.verdict || {}) };
    base.findings = (incoming.findings || []).map((f) => ({ ...newFinding(), ...f }));
    const qsg = incoming.quick_start_guide || {};
    base.quick_start_guide = {
      title: qsg.title || "",
      intro: qsg.intro || "",
      footer_note: qsg.footer_note || "",
      steps: (qsg.steps || []).map((s) => ({ ...newStep(), ...s })),
    };
    return base;
  }

  function formatDate(iso) {
    try {
      const d = new Date(iso);
      return d.toLocaleString();
    } catch (e) {
      return iso;
    }
  }

  // ---------------------------------------------------------------------
  // Screenshot upload
  // ---------------------------------------------------------------------

  async function handleScreenshotFile(card, file) {
    if (!state.slug) {
      setStatus("Set a slug before uploading screenshots.", "error");
      return;
    }
    const idx = parseInt(card.dataset.findingIndex, 10);
    if (Number.isNaN(idx)) return;

    const fd = new FormData();
    fd.append("slug", state.slug);
    fd.append("index", String(idx));
    fd.append("file", file);

    state.pendingScreenshotUploads += 1;
    setStatus(`Uploading screenshot for finding ${idx + 1}…`, "");
    try {
      const resp = await fetch("/api/screenshot", { method: "POST", body: fd });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Upload failed");
      const finding = state.payload.findings[idx];
      if (finding) {
        finding.screenshot_path = data.path;
        if (!finding.screenshot_caption) {
          finding.screenshot_caption = `Screenshot of ${data.filename}`;
        }
      }
      renderFindings();
      setStatus(`Screenshot saved → ${data.path}`, "success");
      scheduleAutosave();
    } catch (err) {
      setStatus("Screenshot upload failed: " + err.message, "error");
    } finally {
      state.pendingScreenshotUploads -= 1;
    }
  }

  function removeScreenshot(card) {
    if (!card) return;
    const idx = parseInt(card.dataset.findingIndex, 10);
    if (Number.isNaN(idx)) return;
    const finding = state.payload.findings[idx];
    if (!finding) return;
    finding.screenshot_path = "";
    finding.screenshot_caption = "";
    renderFindings();
    scheduleAutosave();
  }

  // ---------------------------------------------------------------------
  // Generate YAML + deliver
  // ---------------------------------------------------------------------

  async function generateYaml({ andDeliver }) {
    clearFieldErrors();
    if (!state.slug) {
      setStatus("Slug is required.", "error");
      const el = $('[data-field="slug"]');
      if (el) el.focus();
      return;
    }

    setStatus(andDeliver ? "Generating YAML, then delivering…" : "Generating YAML…", "");
    try {
      const resp = await fetch("/api/yaml", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug: state.slug, payload: state.payload }),
      });
      const data = await resp.json();
      if (!resp.ok || !data.ok) {
        if (data.errors) showFieldErrors(data.errors);
        setStatus(`Validation failed (${(data.errors || []).length} errors). See inline messages.`, "error");
        return;
      }
      showYamlPreview(data.yaml);
      setStatus(`YAML written → ${data.path}`, "success");

      if (andDeliver) {
        await runDeliver(true);
      }
    } catch (err) {
      setStatus("Generate failed: " + err.message, "error");
    }
  }

  function showYamlPreview(text) {
    selectPreviewTab("yaml");
    const pane = $('[data-pane="yaml"] code');
    if (pane) pane.textContent = text;
  }

  async function runDeliver(send) {
    setStatus("Starting deliver_report.py…", "");
    selectPreviewTab("log");
    const logPane = $('[data-pane="log"] code');
    if (logPane) logPane.textContent = "";
    state.deliverOffset = 0;

    try {
      const resp = await fetch("/api/deliver", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug: state.slug, send: !!send }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setStatus(data.error || "Deliver failed to start.", "error");
        return;
      }
      pollDeliverLog();
    } catch (err) {
      setStatus("Deliver failed: " + err.message, "error");
    }
  }

  function pollDeliverLog() {
    clearTimeout(state.deliverPollTimer);
    state.deliverPollTimer = setTimeout(async () => {
      try {
        const resp = await fetch(`/api/deliver/log?since=${state.deliverOffset}`);
        const data = await resp.json();
        const pane = $('[data-pane="log"] code');
        if (pane && data.lines && data.lines.length) {
          pane.textContent += data.lines.join("\n") + "\n";
          pane.parentElement.scrollTop = pane.parentElement.scrollHeight;
        }
        state.deliverOffset = data.next_offset || state.deliverOffset;

        if (data.running) {
          pollDeliverLog();
        } else {
          if (data.exit_code === 0) {
            setStatus("Deliver complete (exit 0).", "success");
          } else if (typeof data.exit_code === "number") {
            setStatus(`Deliver failed (exit ${data.exit_code}). See log pane for details.`, "error");
          }
        }
      } catch (err) {
        setStatus("Log polling failed: " + err.message, "error");
      }
    }, 600);
  }

  function selectPreviewTab(name) {
    $$(".preview__tab").forEach((tab) => {
      tab.classList.toggle("is-active", tab.dataset.tab === name);
      tab.onclick = () => selectPreviewTab(tab.dataset.tab);
    });
    $$("[data-pane]").forEach((pane) => {
      pane.hidden = pane.dataset.pane !== name;
    });
  }

  // ---------------------------------------------------------------------
  // Field errors
  // ---------------------------------------------------------------------

  function clearFieldErrors() {
    $$(".has-error").forEach((el) => el.classList.remove("has-error"));
    $$("[data-error]").forEach((el) => {
      el.hidden = true;
      el.textContent = "";
    });
  }

  function showFieldErrors(errors) {
    let firstFieldEl = null;
    errors.forEach((err) => {
      const sel = errorFieldSelector(err.field);
      const el = sel ? $(sel) : null;
      if (el) {
        const wrap = el.closest(".field");
        if (wrap) wrap.classList.add("has-error");
        if (!firstFieldEl) firstFieldEl = el;
        const inlineMsg = wrap ? wrap.querySelector(".field__error") : null;
        if (wrap && !inlineMsg) {
          const msg = document.createElement("div");
          msg.className = "field__error";
          msg.textContent = err.message;
          wrap.appendChild(msg);
        } else if (inlineMsg) {
          inlineMsg.textContent = err.message;
        }
      } else {
        const errBox = $('[data-error="findings"]');
        if (errBox && err.field === "findings") {
          errBox.hidden = false;
          errBox.textContent = err.message;
        }
      }
    });
    if (firstFieldEl) {
      try { firstFieldEl.focus(); } catch (e) { /* ignore */ }
    }
  }

  function errorFieldSelector(field) {
    if (!field) return null;
    if (field.startsWith("findings[")) {
      // e.g. findings[2].title
      const match = field.match(/^findings\[(\d+)\]\.(\w+)$/);
      if (match) {
        return `[data-finding][data-finding-index="${match[1]}"] [data-field="${match[2]}"]`;
      }
      return null;
    }
    if (field === "qsg.title" || field === "qsg.intro" || field === "qsg.footer_note") {
      return `[data-field="${field}"]`;
    }
    if (field === "qsg.steps") {
      return null;
    }
    if (field === "findings") return null;
    return `[data-field="${field}"]`;
  }

  // ---------------------------------------------------------------------
  // Open existing customer
  // ---------------------------------------------------------------------

  async function openCustomerModal() {
    const modal = $("[data-modal]");
    const list = $("[data-customer-list]");
    if (!modal || !list) return;
    modal.hidden = false;
    list.innerHTML = "<li class='customer-list__empty'>Loading…</li>";
    try {
      const resp = await fetch("/api/customers");
      const data = await resp.json();
      if (!data.customers || !data.customers.length) {
        list.innerHTML = "<li class='customer-list__empty'>No customer YAML files found in customers/.</li>";
        return;
      }
      list.innerHTML = "";
      data.customers.forEach((c) => {
        const li = document.createElement("li");
        const left = document.createElement("span");
        left.textContent = c.filename;
        const right = document.createElement("span");
        right.className = "meta";
        right.textContent = formatDate(c.modified);
        li.appendChild(left);
        li.appendChild(right);
        li.onclick = () => loadCustomer(c.slug);
        list.appendChild(li);
      });
    } catch (err) {
      list.innerHTML = `<li class='customer-list__empty'>Error: ${err.message}</li>`;
    }
  }

  function closeCustomerModal() {
    const modal = $("[data-modal]");
    if (modal) modal.hidden = true;
  }

  async function loadCustomer(slug) {
    try {
      const resp = await fetch(`/api/customers/${encodeURIComponent(slug)}`);
      const data = await resp.json();
      if (!resp.ok) {
        setStatus(data.error || "Failed to load customer.", "error");
        return;
      }
      state.slug = data.slug;
      state.payload = mergePayload(blankPayload(), data.payload);
      writePayloadToForm();
      updateSlugDisplay();
      showYamlPreview(data.yaml);
      closeCustomerModal();
      setStatus(`Loaded customers/${data.slug}.yaml`, "success");
    } catch (err) {
      setStatus("Load failed: " + err.message, "error");
    }
  }

  // ---------------------------------------------------------------------
  // Status bar
  // ---------------------------------------------------------------------

  function setStatus(msg, kind) {
    const el = $("[data-status]");
    if (!el) return;
    el.classList.remove("is-error", "is-success");
    if (kind === "error") el.classList.add("is-error");
    if (kind === "success") el.classList.add("is-success");
    el.textContent = msg;
  }

  // ---------------------------------------------------------------------
  // AI review mode
  // ---------------------------------------------------------------------

  function approveFinding(card) {
    if (!card || !state.reviewAi) return;
    const idx = parseInt(card.dataset.findingIndex, 10);
    if (Number.isNaN(idx)) return;
    state.reviewStatus[idx] = "approved";
    card.dataset.reviewStatus = "approved";
    applyReviewVisuals(card, idx);
    postFeedback({ finding_idx: idx, action: "approved" }, idx);
    refreshReviewBanner();
  }

  function rejectFinding(card) {
    if (!card || !state.reviewAi) return;
    const idx = parseInt(card.dataset.findingIndex, 10);
    if (Number.isNaN(idx)) return;
    const finding = state.payload.findings[idx];
    if (!finding) return;
    const title = finding.title ? `"${finding.title}"` : "this finding";
    if (!confirm(`Reject and remove ${title}? This deletes it from the YAML.`)) return;

    postFeedback({ finding_idx: idx, action: "rejected", ai_title: finding.title || "" }, idx);

    state.payload.findings.splice(idx, 1);
    if (state.aiBaseline.length > idx) state.aiBaseline.splice(idx, 1);
    if (state.reviewStatus.length > idx) state.reviewStatus.splice(idx, 1);
    renderFindings();
    refreshFindingsCounter();
    refreshReviewBanner();
    scheduleAutosave();
    setStatus(`Rejected: ${title}.`, "success");
  }

  async function regenerateFinding(card) {
    if (!card || !state.reviewAi) return;
    const idx = parseInt(card.dataset.findingIndex, 10);
    if (Number.isNaN(idx)) return;
    const finding = state.payload.findings[idx];
    if (!finding) return;

    state.regenInFlight.add(idx);
    applyReviewVisuals(card, idx);
    setStatus(`Regenerating finding ${idx + 1}…`, "");

    try {
      const resp = await fetch("/api/regenerate-finding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slug: state.slug,
          finding: finding,
          customer: state.payload.customer,
          provider: "auto",
        }),
      });
      const data = await resp.json();
      if (!resp.ok || !data.ok) {
        setStatus("Regenerate failed: " + (data.error || resp.statusText), "error");
        return;
      }
      const replacement = data.finding || {};
      Object.assign(finding, {
        severity: replacement.severity || finding.severity,
        title: replacement.title || finding.title,
        what_we_saw: replacement.what_we_saw || finding.what_we_saw,
        why_it_matters: replacement.why_it_matters || finding.why_it_matters,
        screenshot_caption: replacement.screenshot_caption || finding.screenshot_caption,
        fix_prompt: replacement.fix_prompt || finding.fix_prompt,
      });
      state.aiBaseline[idx] = { title: finding.title, severity: finding.severity };
      state.reviewStatus[idx] = "draft";
      postFeedback({ finding_idx: idx, action: "regenerated" }, idx);
      renderFindings();
      refreshReviewBanner();
      setStatus(`Regenerated finding ${idx + 1}.`, "success");
    } catch (err) {
      setStatus("Regenerate failed: " + err.message, "error");
    } finally {
      state.regenInFlight.delete(idx);
      const refreshedCard = $(`[data-finding][data-finding-index="${idx}"]`);
      if (refreshedCard) applyReviewVisuals(refreshedCard, idx);
    }
  }

  function markEditedIfChanged(idx) {
    const finding = state.payload.findings[idx];
    const baseline = state.aiBaseline[idx];
    if (!finding || !baseline) return;
    const titleChanged = (finding.title || "") !== (baseline.title || "");
    const sevChanged = (finding.severity || "") !== (baseline.severity || "");
    const current = state.reviewStatus[idx] || "draft";
    if ((titleChanged || sevChanged) && current !== "rejected") {
      if (current !== "edited") {
        state.reviewStatus[idx] = "edited";
        postFeedback({
          finding_idx: idx,
          action: "edited",
          ai_title: baseline.title,
          ai_severity: baseline.severity,
          final_title: finding.title,
          final_severity: finding.severity,
        }, idx);
      }
      const card = $(`[data-finding][data-finding-index="${idx}"]`);
      if (card) applyReviewVisuals(card, idx);
      refreshReviewBanner();
    }
  }

  async function postFeedback(body, idx) {
    if (!state.reviewAi || !state.slug) return;
    const finding = state.payload.findings[idx];
    const enriched = {
      slug: state.slug,
      ai_title: state.aiBaseline[idx]?.title,
      ai_severity: state.aiBaseline[idx]?.severity,
      final_title: finding?.title,
      final_severity: finding?.severity,
      ...body,
    };
    try {
      await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(enriched),
      });
    } catch (err) {
      // non-fatal: feedback is best-effort
      console.warn("feedback post failed", err);
    }
  }

  function refreshReviewBanner() {
    if (!state.reviewAi) return;
    const stats = $("[data-ai-banner-stats]");
    if (!stats) return;
    const total = state.payload.findings.length;
    const reviewed = state.reviewStatus.filter((s) => s === "approved" || s === "edited").length;
    stats.textContent = `${reviewed} / ${total} reviewed`;
    stats.classList.toggle("is-complete", total > 0 && reviewed === total);
  }

  async function approveAllAndShip() {
    if (!state.reviewAi) return;
    if (!state.slug) {
      setStatus("Slug is required before shipping.", "error");
      return;
    }
    if (!state.payload.findings.length) {
      setStatus("No findings to ship.", "error");
      return;
    }
    const unreviewed = state.reviewStatus
      .map((s, i) => (s === "draft" ? i : -1))
      .filter((i) => i >= 0);
    if (unreviewed.length) {
      const ok = confirm(
        `Mark ${unreviewed.length} un-reviewed finding(s) as approved and send the PDFs?`
      );
      if (!ok) return;
    } else {
      const ok = confirm("Send the Main Report and Quick Start Guide PDFs to the customer now?");
      if (!ok) return;
    }
    unreviewed.forEach((i) => {
      state.reviewStatus[i] = "approved";
      const card = $(`[data-finding][data-finding-index="${i}"]`);
      if (card) applyReviewVisuals(card, i);
    });
    refreshReviewBanner();

    try {
      await fetch("/api/feedback/finalize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slug: state.slug,
          final_findings: state.payload.findings,
        }),
      });
    } catch (err) {
      console.warn("feedback finalize failed", err);
    }

    // Use the existing generate-yaml-and-deliver pipeline (with --send).
    await generateYaml({ andDeliver: true });
  }

})();
