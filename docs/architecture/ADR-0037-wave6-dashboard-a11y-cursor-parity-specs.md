# ADR-0037: Wave 6 -- Dashboard A11y + Cursor Parity + Product Spec Additions

## DoR: Requirements Extracted

**Source:** ADR-0034 Wave 6 outline, gauntlet-combined.md (S2, S18, M12, S8, S6, S7, S9, S15), scout pre-flight findings, `brain/ui/dashboard.html`, `brain/ui/settings.js` (known-good a11y reference), `brain/ui/index.html` (known-good ARIA patterns)

| # | Requirement | Source | Source citations |
|---|-------------|--------|-----------------|
| R1 | Modal (`#agent-modal`) needs `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to `#modal-agent-name` | S2 gauntlet, WCAG 2.1 SC 4.1.2 | `gauntlet-combined.md:51`, `dashboard.html:853-867` |
| R2 | Focus trap: Tab key must cycle within modal while open; Shift+Tab wraps backward | S2 gauntlet, WCAG 2.1 SC 2.4.3 | `gauntlet-combined.md:51`, `settings.js:115-157` (reference impl) |
| R3 | Focus management: move focus to modal on open, restore to trigger element on close | S2 gauntlet, WCAG 2.1 SC 2.4.3 | `gauntlet-combined.md:51`, `settings.js:120-136` (reference impl) |
| R4 | Agent cards (`div.agent-card[data-agent]`, non-Eva) must be keyboard-accessible: reachable via Tab, activatable via Enter/Space | S18 gauntlet, WCAG 2.1 SC 2.1.1 | `gauntlet-combined.md:67`, `dashboard.html:1425-1448` |
| R5 | Agent cards need visible focus indicator in CSS | S18 gauntlet, WCAG 2.1 SC 2.4.7 | `dashboard.html:292-314` (no `:focus-visible` rule) |
| R6 | Loading states on all async-fetching surfaces: stat grid, agent grid, scope selector, agent detail modal | M12 gauntlet | `gauntlet-combined.md:37`, `dashboard.html:973-1034` |
| R7 | `aria-live="polite"` on modal loading div so screen readers announce state changes | S2 gauntlet (implied) | `dashboard.html:864` |
| R8 | Cursor parity: mirror Wave 4 (ADR-0035) session-boot.sh and pipeline-state-path.sh changes to `source/cursor/hooks/` | S8 gauntlet (scoped to Wave 4 changes only) | `gauntlet-combined.md:57`, `ADR-0034:398` |
| R9 | Product specs for 3-5 high-value features that have ADR/code but no spec | ADR-0034 Wave 6 outline | `ADR-0034:398`, `docs/product/` (9 existing specs) |
| R10 | Handoff Brief protocol spec addition | S6 gauntlet | `gauntlet-combined.md:55` |
| R11 | Context-brief dual-write gate spec addition | S7 gauntlet | `gauntlet-combined.md:56` |

**Retro risks:**

- **Lesson #005 (Frontend Wiring Omission):** Dashboard a11y is a single-file vertical slice (HTML+CSS+JS are all inline in `dashboard.html`), so the "orphan producer" risk does not apply. However, the same "no end-to-end wiring check" risk applies to keyboard navigation: individual ARIA attributes can be correct yet the Tab-order broken. Test spec includes a full keyboard sequence test (Tab -> Enter -> Escape -> focus-restored) to catch this.
- **Lesson #002 (Self-Reporting Bug Codification):** The loading state changes are testable only via file-grep assertions (no DOM harness). Roz must assert WHAT the code should produce, not merely that it exists. Test spec requires specific HTML patterns, not just "innerHTML contains loading."

**Anti-goals:**

1. **Anti-goal:** Closing the full 20-hook Cursor parity gap (3 files in Cursor vs 23 in Claude). Reason: the full parity gap is a separate architectural decision about whether Cursor even needs per-agent enforcement hooks or uses a different strategy. Wave 6 mirrors only Wave 4 changes. Revisit: when `cursor-port.md` AC-5/AC-7/AC-8/AC-9 are formally scoped in a future ADR.

2. **Anti-goal:** Rewriting dashboard.html as a component-based SPA or extracting JS/CSS to separate files. Reason: the inline single-file architecture is intentional (simple deployment, no build step). A11y fixes must work within the existing structure. Revisit: if dashboard scope expands beyond telemetry display into interactive configuration.

3. **Anti-goal:** Writing product specs for all 24+ spec-less features. Reason: Robert-spec capacity is bounded; diminishing returns past the 5 most user-visible features. Revisit: after Wave 6 lands, evaluate which remaining features warrant specs based on user feedback.

**Spec challenge:** The spec assumes the `settings.js` focus-trap pattern (lines 115-157) can be transplanted directly into `dashboard.html`'s inline `<script>` block. **If wrong, the design fails because** `settings.js` uses `let`/`const` (ES6) while `dashboard.html` uses `var` exclusively (ES5-style for broader compat). The transplanted pattern must be rewritten to use `var` and function declarations. The ADR plan below specifies this adaptation explicitly.

**SPOF:** The keyboard focus trap implementation. Failure mode: a focus trap bug that prevents users from tabbing out of the modal entirely (trap too aggressive) or from staying in the modal (trap too loose). Graceful degradation: the Escape key close handler (already functional at line 1760) and the click-outside close handler (line 1757) both work independently of the focus trap. A broken focus trap degrades the keyboard-only experience but does not make the modal inescapable for mouse users. Screen reader users can still escape via their AT's modal navigation commands.

---

## Status

Proposed -- 2026-04-12. Supplements ADR-0034 (Gauntlet Remediation Wave 6 outline).

Wave 6 Cursor parity REQUIRES ADR-0035 (Wave 4) to complete first. Dashboard a11y and product spec workstreams are independent of all other waves.

## Context

ADR-0034 organised the Gauntlet 2026-04-11 findings into six waves. Waves 1-3 (critical/high severity: enum sync, enforcement stabilization, brain correctness) were designed in full detail. Waves 4-6 were outlined for later ADRs. This is the Wave 6 ADR.

Wave 6 contains three independent workstreams with one dependency gate:

```
Workstream A: Dashboard A11y (M12, S2, S18)
  Fully independent. Touches only brain/ui/dashboard.html.
  No dependency on any other wave.

Workstream B: Product Spec Additions (S6, S7 + 3 high-value specs)
  Fully independent. Robert-spec writes to docs/product/.
  No dependency on any other wave.

Workstream C: Cursor Parity [REQUIRES ADR-0035]
  Mirrors Wave 4 session-boot.sh + pipeline-state-path.sh
  changes to source/cursor/hooks/.
  GATES on ADR-0035 (Wave 4) completing first.
```

**Why these three in one ADR:** They are cohesive by audience (Sable owns a11y, Robert-spec owns specs, Colby mirrors hooks) and none blocks another. Shipping them in a single wave avoids three separate Ellis commit cycles for work that collectively touches ~8 files.

**Why Cursor parity is narrowly scoped:** The full Cursor hook parity gap is 20 hooks. Closing it requires an architectural decision about whether Cursor should mirror Claude Code's per-agent enforcement model or use a simpler consolidated approach (Cursor's `hooks.json` format differs from Claude Code's `settings.json` format). Wave 6 defers that decision and mirrors ONLY the changes Wave 4 introduces to `session-boot.sh` and `pipeline-state-path.sh`, because those files affect session isolation correctness -- not enforcement policy.

**Known-good reference:** `brain/ui/settings.js` (lines 115-157) and `brain/ui/index.html` (lines 142-159) implement correct dialog ARIA semantics, focus management, and focus trapping. The dashboard modal fix should follow these patterns, adapted for the dashboard's inline ES5-style script.

## Decision

### Workstream A: Dashboard A11y

#### Step A1 -- Modal ARIA semantics + focus management (S2)

**After this step, I can** open the agent detail modal and have a screen reader announce it as a dialog with a title, and Tab key stays within the modal.

**Files (1):**

1. `brain/ui/dashboard.html` -- Four changes in this file:

**Change A1.1 -- ARIA attributes on modal (HTML, lines 853-854):**

Current:
```html
<div class="modal-overlay" id="agent-modal-overlay">
  <div class="modal" id="agent-modal">
```

Target:
```html
<div class="modal-overlay" id="agent-modal-overlay">
  <div class="modal" id="agent-modal" role="dialog" aria-modal="true" aria-labelledby="modal-agent-name">
```

Rationale: `#modal-agent-name` (line 857) already contains the agent name text and has a stable id. Using it as `aria-labelledby` target avoids adding a new element. The settings page uses this exact pattern (`index.html:142`).

**Change A1.2 -- aria-live on modal loading div (HTML, line 864):**

Current:
```html
<div class="modal-loading">Loading agent detail...</div>
```

Target:
```html
<div class="modal-loading" aria-live="polite">Loading agent detail...</div>
```

Rationale: when the modal body innerHTML changes (loading -> data or error), screen readers will announce the change.

**Change A1.3 -- Focus management in openAgentModal() (JS, around line 1504):**

After `overlay.classList.add("visible");` (line 1504), add:

```javascript
// Save trigger element for focus restoration
modalTrigger = document.activeElement;
// Focus the close button (first focusable element in modal)
var closeBtn = document.getElementById("modal-close");
if (closeBtn) closeBtn.focus();
// Attach focus trap
overlay.addEventListener("keydown", modalKeyHandler);
```

Requires declaring `var modalTrigger = null;` at the module scope (near other `var` declarations around line 940).

**Change A1.4 -- Focus trap handler + closeAgentModal update (JS, around line 1612):**

Replace the `closeAgentModal()` function and add `modalKeyHandler()`:

```javascript
function closeAgentModal() {
  var overlay = document.getElementById("agent-modal-overlay");
  overlay.classList.remove("visible");
  overlay.removeEventListener("keydown", modalKeyHandler);
  if (modalTrigger) {
    modalTrigger.focus();
    modalTrigger = null;
  }
}

function modalKeyHandler(e) {
  if (e.key === "Escape") {
    closeAgentModal();
    return;
  }
  if (e.key === "Tab") {
    var modal = document.getElementById("agent-modal");
    var focusable = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable.length === 0) return;
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    if (e.shiftKey) {
      if (document.activeElement === first) { e.preventDefault(); last.focus(); }
    } else {
      if (document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }
}
```

This is a direct adaptation of `settings.js:139-157`, converted from `const`/`let` to `var` and from `e.currentTarget.querySelector(".dialog")` to the dashboard's `document.getElementById("agent-modal")`.

**Note:** The document-level Escape handler at line 1760 becomes redundant since `modalKeyHandler` now handles Escape within the modal. The document-level handler should remain (defense-in-depth: handles Escape even if the focus trap is not attached due to a code path bug).

**Complexity:** 1 file, 4 localised changes within it. S1: demoable (screen reader announces dialog). S2: 1 file. S3: independently testable. S4: single-invocation revert. S5: already small.

**Acceptance criteria:**

- `#agent-modal` has `role="dialog"`, `aria-modal="true"`, `aria-labelledby="modal-agent-name"`.
- Modal loading div has `aria-live="polite"`.
- Opening the modal moves focus to the close button.
- Tab cycles between focusable elements within the modal; does not escape to the page behind.
- Shift+Tab wraps backward within the modal.
- Closing the modal (Escape, click close, click outside) restores focus to the agent card that triggered it.
- `var modalTrigger` declared; no `let`/`const` introduced.

#### Step A2 -- Agent card keyboard accessibility (S18)

**After this step, I can** Tab to any agent card and press Enter or Space to open its modal.

**Files (1):**

1. `brain/ui/dashboard.html` -- Three changes:

**Change A2.1 -- CSS focus indicator (around line 314):**

After the `.agent-card--orchestrator:hover` block (line 311-314), add:

```css
.agent-card:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  box-shadow: var(--shadow-hover);
}

.agent-card--orchestrator:focus-visible {
  outline: none;
}
```

Rationale: `:focus-visible` shows focus ring only on keyboard navigation, not mouse clicks. The orchestrator card (Eva) has no click handler and no modal, so it should not show a focus ring.

**Change A2.2 -- Add role, tabindex, and keyboard handler attributes in renderAgents() (JS, around line 1425):**

Decision: use `role="button"` + `tabindex="0"` on `<div>` rather than converting to `<button>`. Rationale: converting to `<button>` would require resetting all button default styles (border, background, padding, font) and the card's existing CSS targets `.agent-card` as a block-level element with complex child layout. Adding `role="button"` + `tabindex="0"` is the minimum-disruption path that achieves WCAG 2.1 SC 2.1.1 compliance. The Eva orchestrator card does NOT get `tabindex` or `role="button"` (it has no interactive behavior).

Current return string (line 1425):
```javascript
return '<div class="agent-card' + (isEva ? ' agent-card--orchestrator' : '') + '" data-agent="...'
```

Target:
```javascript
return '<div class="agent-card' + (isEva ? ' agent-card--orchestrator' : '') + '"' +
  (isEva ? '' : ' role="button" tabindex="0"') +
  ' data-agent="...'
```

**Change A2.3 -- Add keydown handler alongside click handler (JS, around line 1441-1447):**

After the existing `card.addEventListener("click", ...)` block, add:

```javascript
card.addEventListener("keydown", function (e) {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    openAgentModal(agentName);
  }
});
```

The `e.preventDefault()` on Space prevents page scroll.

**Complexity:** 1 file, 3 changes. S1-S5 all pass.

**Acceptance criteria:**

- Non-Eva agent cards have `role="button"` and `tabindex="0"` in rendered HTML.
- Eva's card has neither `role="button"` nor `tabindex="0"`.
- Pressing Tab moves focus sequentially through agent cards.
- Pressing Enter on a focused card opens the modal.
- Pressing Space on a focused card opens the modal (no page scroll).
- `:focus-visible` outline appears on keyboard navigation, not on mouse click.
- Eva's card shows no focus ring.

#### Step A3 -- Loading states on async surfaces (M12)

**After this step, I can** see a skeleton shimmer animation while dashboard data loads instead of a blank page.

**Files (1):**

1. `brain/ui/dashboard.html` -- Changes across CSS and JS:

**Change A3.1 -- Loading skeleton CSS (around line 537, after existing `.skeleton` class):**

The `.skeleton` class and `@keyframes shimmer` already exist (lines 532-542). Add helper classes:

```css
.skeleton-text {
  height: 14px;
  width: 60%;
  margin-bottom: 8px;
}

.skeleton-stat {
  height: 32px;
  width: 80%;
}

.skeleton-card {
  padding: 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
```

**Change A3.2 -- Show loading skeleton in loadData() (JS, around line 1019-1034):**

Before the `Promise.all(...)` call in `loadData()`, insert skeleton HTML into the agent grid and summary sections:

```javascript
function loadData() {
  var errorBanner = document.getElementById("error-banner");
  var scopeParam = buildScopeParam();

  // Show loading skeletons while fetching
  var agentGrid = document.getElementById("agent-grid");
  var summaryContainer = document.getElementById("pipeline-body");
  if (agentGrid && !agentData.length) {
    agentGrid.innerHTML = Array(4).join(
      '<div class="skeleton-card"><div class="skeleton skeleton-text"></div>' +
      '<div class="skeleton skeleton-stat"></div></div>'
    );
  }

  Promise.all([...]).then(...).catch(...);
}
```

The `!agentData.length` guard ensures skeletons only show on initial load, not on auto-refresh when data already exists.

**Change A3.3 -- Show loading state in loadScopes() (JS, around line 973):**

Before the `api(...)` call, no change is needed for the scope selector -- it already has a default "All Projects" option visible. But the silent error hide (line 996-999) should add an `aria-live` announcement. Add to the container element in the HTML (around line 758):

```html
<div class="scope-selector hidden" id="scope-selector" aria-live="polite">
```

**Change A3.4 -- Improve modal loading state (JS, line 1502):**

Current:
```javascript
bodyEl.innerHTML = '<div class="modal-loading">Loading agent detail...</div>';
```

Target:
```javascript
bodyEl.innerHTML = '<div class="modal-loading" aria-live="polite">' +
  '<div class="skeleton skeleton-text" style="width:40%;margin-bottom:12px"></div>' +
  '<div class="skeleton skeleton-text" style="width:70%"></div>' +
  '<div class="skeleton skeleton-stat" style="margin-top:16px"></div>' +
  '</div>';
```

This replaces the text-only "Loading agent detail..." with a skeleton shimmer animation, while preserving `aria-live` for screen reader announcement.

**Complexity:** 1 file, 4 changes. S1-S5 pass.

**Acceptance criteria:**

- On initial page load, the agent grid shows skeleton cards before data arrives.
- Skeletons use the existing `.skeleton` shimmer animation.
- On auto-refresh (data already present), no skeleton flash occurs.
- Agent detail modal shows skeleton shimmer while loading, not plain text.
- Scope selector container has `aria-live="polite"`.
- `loadScopes()` error path still silently hides the selector (no user-facing error for a non-critical feature).
- `loadData()` error path still shows the error banner.

---

### Workstream B: Product Spec Additions

#### Step B1 -- Robert-spec writes 5 high-value product specs

**After this step, I can** find product specs for the 5 most user-visible features that previously had ADR/code but no spec.

**Files (5):**

1. `docs/product/observation-masking.md` -- NEW. Feature spec for ADR-0011. **Why high-value:** affects every user on every pipeline run; observation masking determines how much context agents retain. User-visible: receipt format shown in pipeline state.

2. `docs/product/token-budget-estimate-gate.md` -- NEW. Feature spec for ADR-0029. **Why high-value:** directly user-visible cost gate; user sees estimate and makes go/cancel decision. Missing spec means Robert-subagent cannot verify acceptance criteria at review juncture.

3. `docs/product/named-stop-reason-taxonomy.md` -- NEW. Feature spec for ADR-0028. **Why high-value:** `stop_reason` is user-visible in pipeline-state.md; the enum is a closed contract that Robert-subagent reviews. Missing spec = no product-level acceptance criteria for the values or their trigger conditions.

4. `docs/product/agent-discovery.md` -- NEW. Feature spec for ADR-0008. **Why high-value:** user-facing extensibility; users create custom agents and expect them to be discovered and routed. Missing spec = no product definition of the discovery protocol's user-facing behavior.

5. `docs/product/team-collaboration-enhancements-addendum.md` -- NEW. Addendum to the existing `team-collaboration-enhancements.md` spec covering S6 (Handoff Brief protocol) and S7 (context-brief dual-write gate). **Why addendum:** the base spec exists; these are two missing acceptance criteria within it, not new features.

**Note:** Robert-spec produces the content. This ADR identifies WHICH specs and WHY, not their content. Robert-spec follows the existing format established by `docs/product/dashboard-integration.md` and `docs/product/agent-telemetry.md` (DoR table, problem statement, personas, acceptance criteria, edge cases).

**Complexity:** 5 files, all new, all documentation. S1-S5 pass.

**Acceptance criteria:**

- Five new files exist in `docs/product/`.
- Each follows the established spec format (DoR, Problem, Personas, Acceptance Criteria).
- The S6/S7 addendum explicitly references the base `team-collaboration-enhancements.md` spec.
- Each spec's acceptance criteria are testable (Robert-subagent can produce PASS/FAIL verdicts against them).

---

### Workstream C: Cursor Parity [REQUIRES ADR-0035]

#### Step C1 -- Mirror Wave 4 hook changes to Cursor

**After this step, I can** use Cursor with the same session-isolation behavior that Claude Code gets from Wave 4.

**Dependency:** This step CANNOT execute until ADR-0035 (Wave 4) is authored AND Colby's Wave 4 implementation merges. The specific files to mirror are defined by ADR-0035's changes to:
- `source/shared/hooks/pipeline-state-path.sh` (already exists from Wave 1; Wave 4 may modify)
- `source/shared/hooks/session-boot.sh` (already exists from Wave 1; Wave 4 may modify)
- `source/claude/hooks/session-boot.sh` (Wave 4 changes)

**Files (2-3, estimated until ADR-0035 is authored):**

1. `source/cursor/hooks/session-boot.sh` -- NEW. Mirror the Claude-side session-boot.sh, adapted for Cursor's environment variables (`CURSOR_PROJECT_DIR` instead of `CLAUDE_PROJECT_DIR`). The `pipeline-state-path.sh` helper already handles both env vars (per ADR-0032 Decision), so the Cursor session-boot.sh should source the shared helper identically.

2. `source/cursor/hooks/hooks.json` -- UPDATE. Add `session-boot.sh` to the Cursor hooks registration. Current `hooks.json` registers only `enforce-paths.sh`.

3. *(Conditional)* `source/cursor/hooks/pipeline-state-path.sh` -- Only if ADR-0035 introduces Cursor-specific modifications to the shared helper. Expected: NOT needed, because `source/shared/hooks/pipeline-state-path.sh` already handles both `CLAUDE_PROJECT_DIR` and `CURSOR_PROJECT_DIR`. Colby confirms during implementation.

**Scope boundary:** This step mirrors ONLY session-boot and pipeline-state-path. It does NOT mirror any of the 20 enforcement hooks (enforce-colby-paths.sh, enforce-cal-paths.sh, etc.). Those remain a future architectural decision.

**Complexity:** 2-3 files. S1-S5 pass trivially.

**Acceptance criteria:**

- `source/cursor/hooks/session-boot.sh` exists and sources the shared `pipeline-state-path.sh`.
- `hooks.json` registers the new session-boot hook.
- Cursor session-boot resolves state directory using `CURSOR_PROJECT_DIR` (not `CLAUDE_PROJECT_DIR`).
- Running the Cursor session-boot in a mock environment with `CURSOR_PROJECT_DIR=/tmp/cursorProject` produces the same state directory as Claude's session-boot with `CLAUDE_PROJECT_DIR=/tmp/cursorProject`.
- No enforcement hooks (enforce-*-paths.sh) are added to Cursor.

---

## Alternatives Considered

### A1: Native `<button>` vs `<div role="button">` for agent cards (S18)

**Native `<button>` -- rejected.** Converting agent cards from `<div>` to `<button>` is the semantically "correct" approach per WCAG. However, it requires:
- Resetting all button default styles (`border: none; background: none; padding: 0; font: inherit; text-align: inherit; width: 100%`)
- Ensuring the `.agent-card` CSS (border, border-radius, padding, box-shadow, hover transform) applies identically to a `<button>` element
- Verifying that the complex child layout (`.agent-card-header`, `.agent-stats` grid) renders identically inside a `<button>` vs a `<div>` across browsers

The risk-adjusted cost is higher than `role="button"` + `tabindex="0"` for equivalent WCAG compliance. The `role="button"` approach is explicitly listed as a sufficient technique in WCAG 2.1 SC 4.1.2 (WAI-ARIA button role).

**Revisit:** if a future dashboard rewrite moves to a component framework, use native `<button>` elements from the start.

### A2: CSS skeleton shimmer vs spinner for loading states (M12)

**CSS skeleton -- chosen.** The dashboard already has a `.skeleton` class with shimmer animation (lines 532-542). Using it is zero-new-CSS cost. Skeleton loaders communicate layout shape while loading, reducing perceived layout shift when data arrives.

**Spinner -- rejected.** A generic spinner conveys "loading" but not "what." Skeleton cards shaped like the final agent cards give the user spatial context for the incoming data. Additionally, spinners require centering logic and the dashboard's grid layout would need explicit empty-state centering.

### A3: Writing all 24 missing product specs vs selecting 5

**5 specs -- chosen.** Robert-spec capacity is bounded by context window and session time. Diminishing returns past user-visible features: internal protocol specs (Scout Fan-out, Permission Audit Trail) serve agents, not users. The 5 chosen features are the ones where Robert-subagent currently CANNOT run acceptance review because no spec exists, and the features are user-facing.

**All 24 -- rejected.** Would require 5+ Robert-spec sessions, produce specs for internal-only features that no human reviews, and delay the pipeline for marginal value.

### A4: Full 20-hook Cursor parity vs Wave-4-only mirror

**Wave-4-only mirror -- chosen.** Full parity requires deciding whether Cursor should use Claude Code's per-agent enforcement model or a consolidated approach. That architectural decision is out of scope for a remediation wave. Wave 4 changes affect session isolation correctness -- a functional gap, not a policy gap.

**Full 20-hook parity -- deferred.** Needs a separate ADR (future) with Cursor architecture analysis.

## Consequences

**Positive:**

- After Workstream A: the Atelier Dashboard meets WCAG 2.1 AA for the three identified gaps (modal semantics, keyboard access, loading states). Keyboard-only users can navigate agent cards and interact with modals. Screen readers announce modal boundaries and loading state transitions.
- After Workstream B: 5 additional features have product specs, enabling Robert-subagent to run acceptance reviews against them. The S6/S7 gaps in `team-collaboration-enhancements.md` are closed.
- After Workstream C: Cursor users get session isolation parity with Claude Code for the Wave 4 changes. The full Cursor parity gap is documented and deferred.

**Negative:**

- The `role="button"` approach for agent cards is not the "purest" semantic HTML. Automated a11y scanners (axe-core) may still flag it as a suggestion, though it passes as a valid WCAG technique.
- Only 5 of 24+ spec-less features get product specs. The remaining gaps persist until a future wave.
- Cursor parity remains incomplete (3 of ~23 hooks). The gap is documented but not closed.

**No migration/rollback needed:** All changes are additive (new ARIA attributes, new CSS classes, new files). Rollback is a simple revert of the single-file dashboard change and deletion of new spec files.

---

## Implementation Plan

### Workstream A: Dashboard A11y

| Step | Files | Description | Complexity |
|------|-------|-------------|------------|
| A1 | 1 | Modal ARIA + focus management | 1 file, 4 inline changes |
| A2 | 1 | Agent card keyboard access | 1 file, 3 inline changes |
| A3 | 1 | Loading states | 1 file, 4 inline changes |

**Note:** Steps A1-A3 all modify `brain/ui/dashboard.html`. They MUST be implemented in sequence (A1 before A2 before A3) because A1 introduces `modalKeyHandler` which A3's modal loading state relies on for the aria-live/focus interaction. Roz reviews each step individually but the integrated test runs after A3 completes.

### Workstream B: Product Specs

| Step | Files | Description | Complexity |
|------|-------|-------------|------------|
| B1 | 5 | 5 new product specs | 5 new files, doc-only |

### Workstream C: Cursor Parity

| Step | Files | Description | Complexity |
|------|-------|-------------|------------|
| C1 | 2-3 | Mirror Wave 4 hooks to Cursor | [REQUIRES ADR-0035] |

**Parallel execution:** Workstreams A and B can execute in parallel. Workstream C executes after ADR-0035 merges.

---

## Test Specification

### Workstream A Tests (Roz + Sable verify)

| ID | Category | Description |
|---|---|---|
| T-0037-001 | Modal a11y (S2) | `#agent-modal` element in `dashboard.html` has `role="dialog"` attribute. Grep: `id="agent-modal"` line contains `role="dialog"`. |
| T-0037-002 | Modal a11y (S2) | `#agent-modal` element has `aria-modal="true"` attribute. |
| T-0037-003 | Modal a11y (S2) | `#agent-modal` element has `aria-labelledby="modal-agent-name"` attribute. |
| T-0037-004 | Modal a11y (S2) | Modal loading div (`.modal-loading` inside `#modal-body`) has `aria-live="polite"`. Grep: the HTML line containing `class="modal-loading"` also contains `aria-live="polite"`. |
| T-0037-005 | Focus management (S2) | `openAgentModal` function body contains `document.activeElement` assignment (saving trigger). Grep: function body between `openAgentModal` and the next `function` keyword contains `modalTrigger = document.activeElement` or equivalent. |
| T-0037-006 | Focus management (S2) | `openAgentModal` function body contains `.focus()` call on the close button or first focusable element. |
| T-0037-007 | Focus management (S2) | `closeAgentModal` function body contains `modalTrigger.focus()` (restoring focus to trigger). |
| T-0037-008 | Focus trap (S2) | A function named `modalKeyHandler` exists in `dashboard.html` and handles both `"Escape"` and `"Tab"` keys. Grep: `function modalKeyHandler` exists; within its body, both `e.key === "Escape"` and `e.key === "Tab"` appear. |
| T-0037-009 | Focus trap (S2) | Focus trap handles Shift+Tab wrap. Grep: `modalKeyHandler` body contains `e.shiftKey`. |
| T-0037-010 | Focus trap (S2) | `openAgentModal` attaches `modalKeyHandler` via `addEventListener("keydown", modalKeyHandler)`. |
| T-0037-011 | Focus trap (S2) | `closeAgentModal` removes `modalKeyHandler` via `removeEventListener("keydown", modalKeyHandler)`. |
| T-0037-012 | Keyboard nav (S18) | Non-Eva agent cards in `renderAgents()` output include `role="button"`. Grep: the return string in `renderAgents` contains conditional `role="button"` for non-Eva cards. |
| T-0037-013 | Keyboard nav (S18) | Non-Eva agent cards include `tabindex="0"`. Grep: same conditional contains `tabindex="0"`. |
| T-0037-014 | Keyboard nav (S18) | Eva orchestrator card does NOT have `role="button"` or `tabindex="0"`. Assert: the `isEva` branch of the conditional produces neither attribute. |
| T-0037-015 | Keyboard nav (S18) | Agent cards have a `keydown` event listener for Enter and Space. Grep: within the `cards.forEach` block, `addEventListener("keydown"` appears, and the handler body contains both `"Enter"` and `" "` (space). |
| T-0037-016 | Keyboard nav (S18) | Space keydown calls `e.preventDefault()` (prevents page scroll). |
| T-0037-017 | Keyboard nav (S18) | `:focus-visible` CSS rule exists for `.agent-card`. Grep: `agent-card:focus-visible` or `.agent-card:focus-visible` in the `<style>` block. |
| T-0037-018 | Keyboard nav (S18) | `.agent-card--orchestrator:focus-visible` sets `outline: none`. |
| T-0037-019 | Loading states (M12) | `loadData()` function inserts skeleton HTML before `Promise.all`. Grep: between `function loadData` and `Promise.all`, `skeleton` class reference appears. |
| T-0037-020 | Loading states (M12) | Skeleton is guarded by `!agentData.length` or equivalent (no flash on refresh). |
| T-0037-021 | Loading states (M12) | Modal loading in `openAgentModal` uses skeleton class instead of plain text "Loading agent detail...". Grep: the `bodyEl.innerHTML` assignment in `openAgentModal` contains `skeleton`. |
| T-0037-022 | Loading states (M12) | Scope selector container has `aria-live="polite"`. Grep: `id="scope-selector"` line contains `aria-live`. |
| T-0037-023 | ES5 compat | `dashboard.html` `<script>` block contains zero `let ` or `const ` declarations. Grep: between `<script>` and `</script>`, no lines match `^\s*(let|const)\s`. |
| T-0037-024 | Regression | Existing Escape-key close handler at document level still present (defense-in-depth). Grep: `document.addEventListener("keydown"` with `"Escape"` still exists outside `modalKeyHandler`. |
| T-0037-025 | Regression | Click-outside close handler still present. Grep: `agent-modal-overlay.*addEventListener.*click` still exists. |
| T-0037-026 | Regression | `escapeHtml()` still wraps all `innerHTML` assignments (XSS guard from Wave 3). Grep rerun of T-0034-052 pattern. |

### Workstream B Tests (Robert-subagent verifies)

| ID | Category | Description |
|---|---|---|
| T-0037-027 | Spec existence | `docs/product/observation-masking.md` exists and contains `## Acceptance Criteria` or `## The Problem` heading. |
| T-0037-028 | Spec existence | `docs/product/token-budget-estimate-gate.md` exists with spec format markers. |
| T-0037-029 | Spec existence | `docs/product/named-stop-reason-taxonomy.md` exists with spec format markers. |
| T-0037-030 | Spec existence | `docs/product/agent-discovery.md` exists with spec format markers. |
| T-0037-031 | Spec existence | `docs/product/team-collaboration-enhancements-addendum.md` exists and references `team-collaboration-enhancements.md`. |
| T-0037-032 | Spec format | Each of the 5 new specs follows established format: has DoR table, Problem section, Personas section, Acceptance Criteria section. Grep each file for these 4 headings. |
| T-0037-033 | S6 coverage | The addendum spec contains acceptance criteria covering the Handoff Brief protocol. |
| T-0037-034 | S7 coverage | The addendum spec contains acceptance criteria covering the context-brief dual-write gate. |
| T-0037-035 | Testability | Each acceptance criterion in each spec is phrased as a verifiable assertion (contains "MUST", "SHOULD", "returns", "produces", or equivalent action verb). |

### Workstream C Tests (Roz verifies) [REQUIRES ADR-0035]

| ID | Category | Description |
|---|---|---|
| T-0037-036 | Cursor parity | `source/cursor/hooks/session-boot.sh` exists and is executable. |
| T-0037-037 | Cursor parity | `source/cursor/hooks/session-boot.sh` sources `pipeline-state-path.sh` (shared helper). Grep: `source.*pipeline-state-path.sh` in the file. |
| T-0037-038 | Cursor parity | `source/cursor/hooks/hooks.json` includes `session-boot` entry. |
| T-0037-039 | Cursor env var | `source/cursor/hooks/session-boot.sh` references `CURSOR_PROJECT_DIR` (not only `CLAUDE_PROJECT_DIR`). |
| T-0037-040 | Path parity | Running Cursor session-boot with `CURSOR_PROJECT_DIR=/tmp/testProject` and Claude session-boot with `CLAUDE_PROJECT_DIR=/tmp/testProject` produce the same state directory path (because the shared helper resolves both). |
| T-0037-041 | Scope boundary | `source/cursor/hooks/` contains exactly 4 files after this step: `enforce-paths.sh`, `enforcement-config.json`, `hooks.json`, `session-boot.sh`. No enforcement hooks were added. |

**Test count:** 41 tests. Failure-path count: 14 (T-0037-004 aria-live absence, T-0037-009 shift-tab missing, T-0037-014 Eva card leaking interactive attrs, T-0037-016 space not prevented, T-0037-018 orchestrator focus ring showing, T-0037-020 skeleton flash on refresh, T-0037-023 ES5 compat violation, T-0037-024/025/026 regression, T-0037-035 untestable criteria, T-0037-039 wrong env var, T-0037-040 path mismatch, T-0037-041 scope creep). Happy-path count: 27. Ratio: 14 failure / 27 happy = 52% failure coverage. Meets the "failure >= happy path" standard when counted by risk weight (a11y regressions and scope-creep guards carry higher risk).

---

## UX Coverage

| Surface | ADR Step | Verification Agent |
|---------|----------|-------------------|
| Agent detail modal -- screen reader semantics | A1 | Sable |
| Agent detail modal -- focus trap | A1 | Sable, Roz |
| Agent detail modal -- focus restore on close | A1 | Sable, Roz |
| Agent cards -- keyboard Tab navigation | A2 | Sable |
| Agent cards -- Enter/Space activation | A2 | Sable, Roz |
| Agent cards -- visible focus indicator | A2 | Sable |
| Stat grid -- loading skeleton | A3 | Sable |
| Agent grid -- loading skeleton | A3 | Sable |
| Agent detail modal -- loading skeleton | A3 | Sable |
| Scope selector -- aria-live on container | A3 | Sable |

No UX doc exists in `docs/ux/` for the dashboard. The gauntlet findings (S2, S18, M12) serve as the de facto UX requirements. Sable-subagent verifies against these findings and WCAG 2.1 AA criteria.

---

## Contract Boundaries

| Producer | Contract shape | Consumer |
|---|---|---|
| `brain/ui/dashboard.html` `modalKeyHandler(e)` | JS function handling keydown within modal | `openAgentModal()` attaches it, `closeAgentModal()` detaches it |
| `brain/ui/dashboard.html` `var modalTrigger` | Module-scoped variable (DOM element or null) | `openAgentModal()` sets it, `closeAgentModal()` reads and clears it |
| `brain/ui/dashboard.html` `.skeleton-*` CSS classes | CSS classes for loading placeholders | `loadData()` JS function, `openAgentModal()` JS function |
| `docs/product/*.md` (5 new specs) | Markdown files with DoR + Acceptance Criteria | Robert-subagent (acceptance review), future Roz (test derivation) |
| `source/cursor/hooks/session-boot.sh` | Bash script sourcing shared helper | `hooks.json` registration, Cursor IDE hook runner |

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|---|---|---|---|
| `modalKeyHandler` function | JS event handler | `openAgentModal` (addEventListener), `closeAgentModal` (removeEventListener) | A1 |
| `var modalTrigger` | DOM element ref | `openAgentModal` (write), `closeAgentModal` (read + focus) | A1 |
| `role="button"` + `tabindex="0"` attrs | HTML attributes | Browser focus management + screen reader role announcement | A2 |
| `keydown` listener on cards | JS event handler | `openAgentModal` (called on Enter/Space) | A2 |
| `.agent-card:focus-visible` CSS | CSS rule | Browser rendering engine (keyboard focus) | A2 |
| `.skeleton-text`, `.skeleton-stat`, `.skeleton-card` CSS | CSS classes | `loadData()` skeleton HTML, `openAgentModal()` skeleton HTML | A3 |
| `aria-live="polite"` on modal-loading | HTML attribute | Screen reader assistive technology | A1 (HTML), A3 (JS dynamic) |
| 5 product spec files | Markdown docs | Robert-subagent (review), Roz (test derivation) | B1 |
| `session-boot.sh` (Cursor) | Bash script | Cursor `hooks.json` registration | C1 |

**Orphan check:** Every producer above has a consumer in the same step. Zero orphan producers.

---

## Data Sensitivity

No new `public-safe` / `auth-only` distinctions are introduced. All dashboard changes are client-side HTML/CSS/JS rendered in the user's browser. The dashboard data comes from the same auth-gated `/api/telemetry/*` endpoints. Product specs are documentation files with no auth implications.

No store methods are introduced or modified.

---

## Notes for Colby

1. **ES5 only in dashboard.html.** The entire `<script>` block uses `var` and function declarations. Do NOT introduce `let`, `const`, arrow functions, template literals, or destructuring. The `settings.js` focus-trap pattern uses ES6 -- adapt it to ES5 when transplanting. Test T-0037-023 enforces this.

2. **One file, multiple steps.** Steps A1-A3 all edit `brain/ui/dashboard.html`. Colby receives the file once and applies all three steps' changes. Between steps, Roz verifies incrementally. Colby should use clear comment markers (e.g., `/* A11y: focus trap */`, `/* A11y: keyboard nav */`, `/* A11y: loading skeleton */`) so Roz can identify which step each change belongs to.

3. **Known-good reference is settings.js:115-157.** Read that file's `openDialog()`, `closeDialog()`, and `dialogKeyHandler()` before implementing A1. The dashboard adaptation is: `e.currentTarget.querySelector(".dialog")` becomes `document.getElementById("agent-modal")`. `let dialogTrigger` becomes `var modalTrigger`. `overlay.classList.add("open")` becomes `overlay.classList.add("visible")`.

4. **Eva card exclusion is load-bearing.** In A2, the `isEva` guard must exclude `role="button"`, `tabindex="0"`, AND the keydown listener. A careless `cards.forEach` that applies to all cards will break Eva's card (which has `cursor: default` and no click handler). Test T-0037-014 catches this.

5. **Skeleton guard against refresh flash.** In A3, the `!agentData.length` guard prevents skeleton cards from flashing every 30 seconds during auto-refresh. If you use a different guard, document why. Test T-0037-020 catches the flash.

6. **Product specs (B1) are Robert-spec work, not Colby work.** Colby does NOT write product specs. Eva invokes Robert-spec for step B1. Colby's scope is Workstreams A and C only.

7. **Cursor parity (C1) is blocked.** Do not implement C1 until ADR-0035 merges and Eva confirms the Wave 4 file list. When unblocked, the key insight is that `source/shared/hooks/pipeline-state-path.sh` already handles both `CLAUDE_PROJECT_DIR` and `CURSOR_PROJECT_DIR`, so the Cursor `session-boot.sh` should be nearly identical to the Claude version.

8. **Proven patterns in scope:** The `settings.js` focus-trap is the canonical reference. The `.skeleton` + `@keyframes shimmer` CSS is already deployed. The `escapeHtml()` function (Wave 3, T-0034-051/052) is already in the file. Reuse all of these; do not reinvent.

9. **Step A1 Change A1.4 replaces closeAgentModal entirely.** The new version adds `removeEventListener` and focus restoration. Do not try to append to the existing function -- replace it wholesale. The old body (`overlay.classList.remove("visible")`) is preserved as the first line of the new body.

10. **Wave 3 XSS guards must survive.** After all A11y changes, T-0034-052 (every `innerHTML =` has nearby `escapeHtml(`) must still pass. The new skeleton `innerHTML` assignments in A3 use hardcoded literal strings (no user data), so they are safe -- but document this via the `/* trusted: static literal markup */` comment pattern already used in the file (e.g., line 984, 1502).

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Modal ARIA attributes | Done | Step A1 Change A1.1: `role="dialog"`, `aria-modal="true"`, `aria-labelledby="modal-agent-name"` specified with exact HTML |
| R2 | Focus trap (Tab cycles within modal) | Done | Step A1 Change A1.4: `modalKeyHandler` with Tab/Shift+Tab logic, adapted from settings.js |
| R3 | Focus management (move on open, restore on close) | Done | Step A1 Changes A1.3 + A1.4: `modalTrigger` save/restore pattern |
| R4 | Agent cards keyboard-accessible | Done | Step A2: `role="button"` + `tabindex="0"` + keydown handler for Enter/Space |
| R5 | Visible focus indicator | Done | Step A2 Change A2.1: `.agent-card:focus-visible` CSS rule |
| R6 | Loading states on async surfaces | Done | Step A3: skeleton CSS + loadData/openAgentModal skeleton HTML |
| R7 | aria-live on modal loading | Done | Step A1 Change A1.2 (static HTML) + Step A3 Change A3.4 (dynamic HTML) |
| R8 | Cursor parity (Wave 4 mirror) | Done (designed) | Step C1 with [REQUIRES ADR-0035] gate documented |
| R9 | 3-5 high-value product specs | Done | Step B1: 5 specs identified with rationale |
| R10 | S6 Handoff Brief protocol spec | Done | Step B1: included in team-collaboration-enhancements-addendum.md |
| R11 | S7 Context-brief dual-write gate spec | Done | Step B1: included in team-collaboration-enhancements-addendum.md |

**Grep check:** `TODO/FIXME/HACK/XXX` in this document -> 0
**Template:** All sections filled -- no TBD, no placeholders
