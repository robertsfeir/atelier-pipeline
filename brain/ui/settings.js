/**
 * Atelier Brain Settings — Client-side logic
 * Vanilla JS, no frameworks. Polls /api/health every 30s.
 */

(function () {
  "use strict";

  // =========================================================================
  // DOM References
  // =========================================================================

  const $ = (sel) => document.querySelector(sel);
  const statusBar = $("#status-bar");
  const statusIcon = $("#status-icon");
  const statusText = $("#status-text");
  const setupHelper = $("#setup-helper");

  const brainToggle = $("#brain-toggle");
  const toggleLabel = $("#toggle-label");

  const dbUrlInput = $("#db-url");
  const scopeInput = $("#scope-input");
  const scopeGroup = $("#scope-group");
  const testConnectionBtn = $("#test-connection-btn");
  const testResult = $("#test-result");

  const lifecycleTbody = $("#lifecycle-tbody");
  const saveLifecycleBtn = $("#save-lifecycle-btn");
  const lifecycleSaved = $("#lifecycle-saved");

  const consolInterval = $("#consol-interval");
  const consolMin = $("#consol-min");
  const consolMax = $("#consol-max");
  const consolidationInfo = $("#consolidation-info");

  const conflictToggle = $("#conflict-toggle");
  const conflictToggleLabel = $("#conflict-toggle-label");
  const dupThreshold = $("#dup-threshold");
  const candThreshold = $("#cand-threshold");
  const llmToggle = $("#llm-toggle");
  const llmToggleLabel = $("#llm-toggle-label");

  const purgeBtn = $("#purge-btn");

  // Dialogs
  const disableDialog = $("#disable-dialog");
  const disableCancel = $("#disable-cancel");
  const disableConfirm = $("#disable-confirm");
  const purgeDialog = $("#purge-dialog");
  const purgeCancel = $("#purge-cancel");
  const purgeConfirm = $("#purge-confirm");
  const purgeDialogBody = $("#purge-dialog-body");

  // All fieldsets (for dimming)
  const sections = [
    $("#section-toggle"),
    $("#section-connection"),
    $("#section-lifecycle"),
    $("#section-consolidation"),
    $("#section-conflict"),
    $("#section-danger"),
  ];

  // =========================================================================
  // State
  // =========================================================================

  let currentState = "loading"; // empty | loading | populated | shared-missing | shared-connected | error
  let healthData = null;
  let configData = null;
  let lifecycleData = []; // rows from /api/thought-types
  let dirtyRows = new Set(); // thought types with unsaved changes
  let toggleDebounceTimer = null;
  let pendingToggleState = null;

  // =========================================================================
  // Utility
  // =========================================================================

  // Auth token injected by server into window global (when configured)
  const API_TOKEN = window.__ATELIER_API_TOKEN__ || null;

  function api(method, path, body) {
    const headers = { "Content-Type": "application/json" };
    if (API_TOKEN) {
      headers["Authorization"] = "Bearer " + API_TOKEN;
    }
    const opts = { method, headers };
    if (body !== undefined) opts.body = JSON.stringify(body);
    return fetch(path, opts).then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    });
  }

  function flashSaved(el, text) {
    el.textContent = text || "Saved \u2713";
    el.classList.add("visible");
    setTimeout(() => el.classList.remove("visible"), 2000);
  }

  function formatTime(ts) {
    if (!ts) return "never";
    const d = new Date(ts);
    return d.toLocaleString();
  }

  function validateScope(val) {
    if (!val) return true; // empty is ok (optional)
    return /^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$/.test(val);
  }

  // =========================================================================
  // Dialog management (focus trap, Escape)
  // =========================================================================

  let dialogTrigger = null;

  function openDialog(overlay) {
    dialogTrigger = document.activeElement;
    overlay.classList.add("open");
    // Focus first button in dialog
    const firstBtn = overlay.querySelector("button");
    if (firstBtn) firstBtn.focus();
    // Trap focus and listen for Escape
    overlay.addEventListener("keydown", dialogKeyHandler);
  }

  function closeDialog(overlay) {
    overlay.classList.remove("open");
    overlay.removeEventListener("keydown", dialogKeyHandler);
    if (dialogTrigger) {
      dialogTrigger.focus();
      dialogTrigger = null;
    }
  }

  function dialogKeyHandler(e) {
    if (e.key === "Escape") {
      closeDialog(e.currentTarget);
      return;
    }
    // Focus trap
    if (e.key === "Tab") {
      const dialog = e.currentTarget.querySelector(".dialog");
      const focusable = dialog.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    }
  }

  // =========================================================================
  // State management
  // =========================================================================

  function setState(state) {
    currentState = state;
    // Remove all status classes
    statusBar.className = "status-bar";

    switch (state) {
      case "empty":
        statusBar.classList.add("status-not-configured");
        statusIcon.textContent = "\u25CB";
        statusText.textContent = "Not configured";
        setupHelper.hidden = false;
        setAllFieldsDisabled(true);
        sections.forEach((s) => s.classList.add("dimmed"));
        break;

      case "loading":
        statusBar.classList.add("status-connecting");
        statusIcon.textContent = "\u25D0";
        statusText.textContent = "Connecting...";
        setupHelper.hidden = true;
        setAllFieldsDisabled(true);
        sections.forEach((s) => s.classList.remove("dimmed"));
        break;

      case "populated":
        statusBar.classList.add("status-connected");
        statusIcon.textContent = "\u25CF";
        statusText.textContent = buildConnectedText("personal");
        setupHelper.hidden = true;
        setAllFieldsDisabled(false);
        sections.forEach((s) => s.classList.remove("dimmed"));
        break;

      case "shared-missing":
        statusBar.classList.add("status-missing-env");
        statusIcon.textContent = "\u25CB";
        statusText.textContent = "Config found \u2014 missing credentials";
        setupHelper.hidden = true;
        brainToggle.disabled = true;
        setAllFieldsDisabled(true);
        sections.forEach((s) => s.classList.remove("dimmed"));
        break;

      case "shared-connected":
        statusBar.classList.add("status-connected");
        statusIcon.textContent = "\u25CF";
        statusText.textContent = buildConnectedText("project");
        setupHelper.hidden = true;
        setAllFieldsDisabled(false);
        dbUrlInput.readOnly = true;
        scopeInput.readOnly = true;
        sections.forEach((s) => s.classList.remove("dimmed"));
        break;

      case "error":
        statusBar.classList.add("status-error");
        statusIcon.textContent = "\u25CF";
        statusText.textContent = "Disconnected \u2014 pipeline will use baseline mode";
        setupHelper.hidden = true;
        setAllFieldsDisabled(false);
        sections.forEach((s) => s.classList.remove("dimmed"));
        break;
    }
  }

  function buildConnectedText(source) {
    const count = healthData ? healthData.thought_count : 0;
    const lastSync = healthData && healthData.last_consolidation
      ? formatTime(healthData.last_consolidation)
      : "never";
    return `\u25CF Connected (${source}) \u00B7 ${count} thoughts \u00B7 Last sync: ${lastSync}`;
  }

  function setAllFieldsDisabled(disabled) {
    const inputs = document.querySelectorAll("input, button");
    inputs.forEach((el) => {
      // Skip dialog buttons
      if (el.closest(".dialog-overlay")) return;
      el.disabled = disabled;
    });
  }

  // =========================================================================
  // Data loading
  // =========================================================================

  async function loadHealth() {
    try {
      healthData = await api("GET", "/api/health");
      if (!healthData.connected) {
        setState("error");
        return;
      }
      const source = healthData.config_source;
      if (source === "project") {
        setState("shared-connected");
      } else {
        setState("populated");
      }
    } catch {
      setState("error");
    }
  }

  async function loadConfig() {
    try {
      configData = await api("GET", "/api/config");
      populateConfig(configData);
    } catch {
      // Config unavailable — likely not connected
    }
  }

  async function loadThoughtTypes() {
    try {
      lifecycleData = await api("GET", "/api/thought-types");
      renderLifecycleTable();
    } catch {
      // Unavailable
    }
  }

  function populateConfig(cfg) {
    if (!cfg) return;

    // Brain toggle
    brainToggle.checked = cfg.brain_enabled;
    toggleLabel.textContent = cfg.brain_enabled ? "Brain enabled" : "Brain disabled";

    // Connection
    dbUrlInput.value = cfg.database_url || DATABASE_URL_DISPLAY || "(not set)";
    scopeInput.value = cfg.default_scope || "";

    // Add shared badge if project config
    if (healthData && healthData.config_source === "project") {
      addBadge(dbUrlInput.parentElement, "shared");
      addBadge(scopeInput.parentElement, "shared");
    }

    // Consolidation
    consolInterval.value = cfg.consolidation_interval_minutes || "";
    consolMin.value = cfg.consolidation_min_thoughts || "";
    consolMax.value = cfg.consolidation_max_thoughts || "";

    if (healthData) {
      const last = healthData.last_consolidation ? formatTime(healthData.last_consolidation) : "never";
      const next = healthData.next_consolidation_at ? formatTime(healthData.next_consolidation_at) : "N/A";
      consolidationInfo.textContent = `Last run: ${last} \u00B7 Next: ${next}`;
    }

    // Conflict detection
    conflictToggle.checked = cfg.conflict_detection_enabled;
    conflictToggleLabel.textContent = cfg.conflict_detection_enabled
      ? "Conflict detection enabled"
      : "Conflict detection disabled";
    dupThreshold.value = cfg.conflict_duplicate_threshold ?? "";
    candThreshold.value = cfg.conflict_candidate_threshold ?? "";
    llmToggle.checked = cfg.conflict_llm_enabled;
    llmToggleLabel.textContent = cfg.conflict_llm_enabled
      ? "LLM classification enabled"
      : "LLM classification disabled";
  }

  // Placeholder for masking DB URL in display
  const DATABASE_URL_DISPLAY = "";

  function addBadge(parentEl, type) {
    // Remove existing badge if any
    const existing = parentEl.querySelector(".badge");
    if (existing) existing.remove();

    const badge = document.createElement("span");
    badge.className = "badge";
    if (type === "shared") {
      badge.textContent = "(shared)";
    } else if (type === "override") {
      badge.className = "badge badge-override";
      badge.textContent = "(local override)";
    }
    const label = parentEl.querySelector("label");
    if (label) label.appendChild(badge);
  }

  // =========================================================================
  // Lifecycle table
  // =========================================================================

  function renderLifecycleTable() {
    lifecycleTbody.innerHTML = "";
    dirtyRows.clear();
    saveLifecycleBtn.disabled = true;

    const types = ["decision", "preference", "lesson", "rejection", "drift", "correction", "insight", "reflection"];

    types.forEach((type) => {
      const row = lifecycleData.find((r) => r.thought_type === type) || {
        thought_type: type,
        default_ttl_days: null,
        default_importance: 0.5,
      };

      const tr = document.createElement("tr");

      // Type cell
      const tdType = document.createElement("td");
      tdType.className = "type-cell";
      tdType.setAttribute("data-label", "Type");
      tdType.textContent = type;
      tr.appendChild(tdType);

      // TTL cell
      const tdTTL = document.createElement("td");
      tdTTL.className = "editable-cell";
      tdTTL.setAttribute("data-label", "TTL (days)");
      tdTTL.setAttribute("data-field", "default_ttl_days");
      tdTTL.setAttribute("data-type", type);
      tdTTL.setAttribute("tabindex", "0");
      tdTTL.setAttribute("role", "button");
      tdTTL.setAttribute("aria-label", `TTL for ${type}: ${row.default_ttl_days === null ? "never" : row.default_ttl_days + " days"}`);
      tdTTL.textContent = row.default_ttl_days === null ? "\u221E" : row.default_ttl_days;
      tr.appendChild(tdTTL);

      // Importance cell
      const tdImp = document.createElement("td");
      tdImp.className = "editable-cell";
      tdImp.setAttribute("data-label", "Default Importance");
      tdImp.setAttribute("data-field", "default_importance");
      tdImp.setAttribute("data-type", type);
      tdImp.setAttribute("tabindex", "0");
      tdImp.setAttribute("role", "button");
      tdImp.setAttribute("aria-label", `Default importance for ${type}: ${row.default_importance}`);
      tdImp.textContent = row.default_importance;
      tr.appendChild(tdImp);

      lifecycleTbody.appendChild(tr);
    });
  }

  function startInlineEdit(cell) {
    if (cell.querySelector("input")) return; // Already editing

    const field = cell.getAttribute("data-field");
    const type = cell.getAttribute("data-type");
    const currentRow = lifecycleData.find((r) => r.thought_type === type) || {};
    const currentVal = currentRow[field];

    const input = document.createElement("input");
    input.type = "number";
    if (field === "default_ttl_days") {
      input.min = "1";
      input.step = "1";
      input.placeholder = "never";
      input.value = currentVal === null ? "" : currentVal;
    } else {
      input.min = "0";
      input.max = "1";
      input.step = "0.01";
      input.value = currentVal ?? "";
    }

    cell.textContent = "";
    cell.appendChild(input);
    input.focus();
    input.select();

    input.addEventListener("blur", () => finishInlineEdit(cell, input, field, type, currentVal));
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") input.blur();
      if (e.key === "Escape") {
        // Restore original
        input.value = field === "default_ttl_days" && currentVal === null ? "" : (currentVal ?? "");
        input.blur();
      }
    });
  }

  function finishInlineEdit(cell, input, field, type, originalVal) {
    let newVal = input.value.trim();

    if (field === "default_ttl_days") {
      newVal = newVal === "" ? null : parseInt(newVal, 10);
      if (newVal !== null && (isNaN(newVal) || newVal < 1)) newVal = originalVal;
    } else {
      newVal = newVal === "" ? originalVal : parseFloat(newVal);
      if (isNaN(newVal) || newVal < 0 || newVal > 1) newVal = originalVal;
    }

    // Update local data
    const row = lifecycleData.find((r) => r.thought_type === type);
    if (row) row[field] = newVal;

    // Display
    if (field === "default_ttl_days") {
      cell.textContent = newVal === null ? "\u221E" : newVal;
    } else {
      cell.textContent = newVal;
    }

    // Mark dirty?
    if (newVal !== originalVal) {
      dirtyRows.add(type);
      // Add dirty marker
      if (!cell.querySelector(".dirty-marker")) {
        const marker = document.createElement("span");
        marker.className = "dirty-marker";
        marker.title = "Unsaved change";
        cell.appendChild(marker);
      }
    }

    saveLifecycleBtn.disabled = dirtyRows.size === 0;
  }

  // Event delegation for inline editing
  lifecycleTbody.addEventListener("click", (e) => {
    const cell = e.target.closest(".editable-cell");
    if (cell) startInlineEdit(cell);
  });

  lifecycleTbody.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      const cell = e.target.closest(".editable-cell");
      if (cell && !cell.querySelector("input")) {
        e.preventDefault();
        startInlineEdit(cell);
      }
    }
  });

  // Save lifecycle changes
  saveLifecycleBtn.addEventListener("click", async () => {
    saveLifecycleBtn.disabled = true;
    const promises = [];

    for (const type of dirtyRows) {
      const row = lifecycleData.find((r) => r.thought_type === type);
      if (!row) continue;
      promises.push(
        api("PUT", `/api/thought-types/${type}`, {
          default_ttl_days: row.default_ttl_days,
          default_importance: row.default_importance,
        })
      );
    }

    try {
      await Promise.all(promises);
      dirtyRows.clear();
      // Remove all dirty markers
      lifecycleTbody.querySelectorAll(".dirty-marker").forEach((m) => m.remove());
      flashSaved(lifecycleSaved, "Saved \u2713");
    } catch {
      lifecycleSaved.textContent = "Error saving";
      lifecycleSaved.classList.add("visible");
      setTimeout(() => lifecycleSaved.classList.remove("visible"), 2000);
      saveLifecycleBtn.disabled = false;
    }
  });

  // =========================================================================
  // Brain toggle (with debounce & confirmation)
  // =========================================================================

  brainToggle.addEventListener("change", () => {
    const wantEnabled = brainToggle.checked;

    if (!wantEnabled) {
      // Revert toggle visually while we show dialog
      brainToggle.checked = true;
      openDialog(disableDialog);
      return;
    }

    // Enabling — debounce
    scheduleBrainToggle(true);
  });

  disableCancel.addEventListener("click", () => closeDialog(disableDialog));
  disableConfirm.addEventListener("click", () => {
    closeDialog(disableDialog);
    brainToggle.checked = false;
    scheduleBrainToggle(false);
  });

  function scheduleBrainToggle(enabled) {
    pendingToggleState = enabled;
    clearTimeout(toggleDebounceTimer);
    toggleDebounceTimer = setTimeout(() => {
      executeBrainToggle(pendingToggleState);
    }, 300);
  }

  async function executeBrainToggle(enabled) {
    try {
      await api("PUT", "/api/config", { brain_enabled: enabled });
      toggleLabel.textContent = enabled ? "Brain enabled" : "Brain disabled";
      brainToggle.setAttribute("aria-checked", enabled);
    } catch {
      // Revert on error
      brainToggle.checked = !enabled;
      toggleLabel.textContent = !enabled ? "Brain enabled" : "Brain disabled";
    }
  }

  // =========================================================================
  // Scope validation
  // =========================================================================

  scopeInput.addEventListener("blur", async () => {
    const val = scopeInput.value.trim();
    if (val && !validateScope(val)) {
      scopeGroup.classList.add("has-error");
      return;
    }
    scopeGroup.classList.remove("has-error");
    if (val && configData && val !== configData.default_scope) {
      try {
        await api("PUT", "/api/config", { default_scope: val });
        configData.default_scope = val;
        // Show local override badge if shared config
        if (healthData && healthData.config_source === "project") {
          addBadge(scopeInput.parentElement, "override");
        }
      } catch {
        // Failed to save
      }
    }
  });

  // =========================================================================
  // Test Connection
  // =========================================================================

  testConnectionBtn.addEventListener("click", async () => {
    testResult.className = "test-result";
    testResult.innerHTML = '<span class="spinner"></span> Testing...';
    testConnectionBtn.disabled = true;

    try {
      const res = await api("GET", "/api/health");
      if (res.connected) {
        testResult.className = "test-result success";
        testResult.textContent = "\u2713 Connected";
      } else {
        testResult.className = "test-result error";
        testResult.textContent = "\u2717 Not connected";
      }
    } catch (err) {
      testResult.className = "test-result error";
      testResult.textContent = "\u2717 Error: " + err.message;
    } finally {
      testConnectionBtn.disabled = false;
    }
  });

  // =========================================================================
  // Consolidation inputs (save on blur)
  // =========================================================================

  function consolBlurHandler(input, configKey, savedEl) {
    input.addEventListener("blur", async () => {
      const val = parseInt(input.value, 10);
      if (isNaN(val) || val < 1) return;
      if (configData && val === configData[configKey]) return;
      try {
        await api("PUT", "/api/config", { [configKey]: val });
        if (configData) configData[configKey] = val;
        flashSaved(savedEl);
      } catch {
        // Failed
      }
    });
  }

  consolBlurHandler(consolInterval, "consolidation_interval_minutes", $("#consol-interval-saved"));
  consolBlurHandler(consolMin, "consolidation_min_thoughts", $("#consol-min-saved"));
  consolBlurHandler(consolMax, "consolidation_max_thoughts", $("#consol-max-saved"));

  // =========================================================================
  // Conflict Detection
  // =========================================================================

  conflictToggle.addEventListener("change", async () => {
    const enabled = conflictToggle.checked;
    try {
      await api("PUT", "/api/config", { conflict_detection_enabled: enabled });
      conflictToggleLabel.textContent = enabled
        ? "Conflict detection enabled"
        : "Conflict detection disabled";
    } catch {
      conflictToggle.checked = !enabled;
    }
  });

  llmToggle.addEventListener("change", async () => {
    const enabled = llmToggle.checked;
    try {
      await api("PUT", "/api/config", { conflict_llm_enabled: enabled });
      llmToggleLabel.textContent = enabled
        ? "LLM classification enabled"
        : "LLM classification disabled";
    } catch {
      llmToggle.checked = !enabled;
    }
  });

  function thresholdBlurHandler(input, configKey, savedEl) {
    input.addEventListener("blur", async () => {
      const val = parseFloat(input.value);
      if (isNaN(val) || val < 0 || val > 1) return;
      if (configData && val === configData[configKey]) return;
      try {
        await api("PUT", "/api/config", { [configKey]: val });
        if (configData) configData[configKey] = val;
        flashSaved(savedEl);
      } catch {
        // Failed
      }
    });
  }

  thresholdBlurHandler(dupThreshold, "conflict_duplicate_threshold", $("#dup-threshold-saved"));
  thresholdBlurHandler(candThreshold, "conflict_candidate_threshold", $("#cand-threshold-saved"));

  // =========================================================================
  // Purge expired thoughts
  // =========================================================================

  purgeBtn.addEventListener("click", async () => {
    // First, get count of expired thoughts
    try {
      const stats = await api("GET", "/api/stats");
      const expiredCount = stats.by_status && stats.by_status.expired ? stats.by_status.expired : 0;
      purgeDialogBody.textContent =
        `Permanently remove ${expiredCount} expired thoughts? Active thoughts and reflections are preserved. This cannot be undone.`;
      openDialog(purgeDialog);
    } catch {
      purgeDialogBody.textContent =
        "Permanently remove expired thoughts? Active thoughts and reflections are preserved. This cannot be undone.";
      openDialog(purgeDialog);
    }
  });

  purgeCancel.addEventListener("click", () => closeDialog(purgeDialog));
  purgeConfirm.addEventListener("click", async () => {
    closeDialog(purgeDialog);
    purgeBtn.disabled = true;
    try {
      const result = await api("POST", "/api/purge-expired");
      purgeBtn.disabled = false;
      // Refresh health to update count
      await loadHealth();
    } catch {
      purgeBtn.disabled = false;
    }
  });

  // =========================================================================
  // Health polling (every 30s)
  // =========================================================================

  let healthInterval = null;

  async function pollHealth() {
    try {
      healthData = await api("GET", "/api/health");
      if (!healthData.connected) {
        if (currentState !== "error") setState("error");
        return;
      }
      // Update status text
      const source = healthData.config_source;
      if (source === "project" && currentState !== "shared-connected") {
        setState("shared-connected");
      } else if (source !== "project" && currentState !== "populated") {
        setState("populated");
      } else {
        // Just update the text
        statusText.textContent = buildConnectedText(source === "project" ? "project" : "personal");
      }
      // Update consolidation info
      if (configData) {
        const last = healthData.last_consolidation ? formatTime(healthData.last_consolidation) : "never";
        const next = healthData.next_consolidation_at ? formatTime(healthData.next_consolidation_at) : "N/A";
        consolidationInfo.textContent = `Last run: ${last} \u00B7 Next: ${next}`;
      }
    } catch {
      if (currentState !== "error") setState("error");
    }
  }

  // =========================================================================
  // Init
  // =========================================================================

  async function init() {
    setState("loading");
    try {
      await loadHealth();
      if (currentState === "error") {
        // Still try to load config/types in case they are cached
      }
      await Promise.all([loadConfig(), loadThoughtTypes()]);
    } catch {
      setState("error");
    }

    // Start polling
    healthInterval = setInterval(pollHealth, 30000);
  }

  init();
})();
