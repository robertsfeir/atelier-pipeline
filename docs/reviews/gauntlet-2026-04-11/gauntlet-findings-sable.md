# Sable — Frontend & UX Quality

**Reviewer:** Sable (UX Acceptance, Subagent Mode)
**Date:** 2026-04-11
**Round:** Gauntlet Round 5 — Frontend & UX Quality
**Mode:** Spec-blind review (no `docs/ux/` baseline; only partial UX doc at `docs/brain/atelier-brain-settings-ux.md`)
**Scope:** `brain/ui/dashboard.html`, `brain/ui/index.html`, `brain/ui/settings.js`, `brain/ui/settings.css`, plus serving layer (`brain/lib/static.mjs`, `brain/lib/rest-api.mjs`)

---

## Summary

The brain UI is split between two distinct surfaces with **inconsistent quality**:

- **Settings (`index.html` + `settings.js` + `settings.css`)** is a model implementation: semantic `fieldset`/`legend`, full label associations, focus-trapped accessible dialogs, `role="switch"` toggles, an `aria-live` status bar, keyboard-operable inline-edit table cells, and a thoughtful 480px responsive table-to-card transformation. It maps cleanly to `atelier-brain-settings-ux.md` and substantially satisfies that doc's DoD checklist.

- **Dashboard (`dashboard.html`, single 1760-line file)** is an a11y regression relative to settings: the modal has no `role="dialog"`, no focus trap, no focus restoration, no `<h2>` heading, the agent cards are `<div>`s wired with click handlers but no `tabindex`/keyboard support, the `<canvas>` charts have no text alternative, the `<select>` scope picker has no `<label>`, the error banner is not a live region, and the `.skeleton` shimmer class is defined but never used — the dashboard has **no loading state at all**, only a flicker from "empty" to "populated".

The dashboard appears to have been built without the same UX rigor as the settings page, and there is **no UX spec for the dashboard at all** (`docs/ux/` does not exist). This is the most important finding: a 1760-line user-facing surface with five distinct screens (overview, charts, agent fitness, alerts, pipelines table, agent detail modal) is shipping without a design baseline, which is why the regressions below were never caught.

There are also several silent-failure UX patterns in `settings.js` (consolidation saves, threshold saves, brain toggle reverts) where errors are swallowed with `catch {}` and the user is given no feedback that an action failed.

**Tally:** 1 Critical, 9 High, 12 Medium, 6 Low. Settings page is broadly healthy. Dashboard requires a dedicated UX-and-a11y pass.

---

## UX Spec Alignment Matrix

| Screen / Flow | Spec Status | Implementation Status | Gap |
|---|---|---|---|
| Brain Settings — single page | **Partial spec** at `docs/brain/atelier-brain-settings-ux.md` (285 lines, dated 2026-03-21, Sable as designer) | Implemented in `index.html`/`settings.js` | DoD checklist in spec is **all unchecked** (D1–D15). Spec is treated as living doc but never closed out. |
| Brain Settings — empty state ("Not configured") | Specified (line 159) | Implemented (`setState("empty")`, settings.js:169) | PASS |
| Brain Settings — loading state ("Connecting…") | Specified (line 160) with pulse animation | Implemented (settings.js:178, CSS keyframes line 89-96) | PASS |
| Brain Settings — populated state | Specified (line 161) | Implemented (settings.js:187) | PASS |
| Brain Settings — shared-missing state | Specified (line 162) | Implemented (settings.js:196) but **`setAllFieldsDisabled(true)` is followed by no re-disable of toggle** — disabled order-dependent | DRIFT (see Finding #11) |
| Brain Settings — shared-connected state w/ "(shared)" badge | Specified (line 163) | Implemented (settings.js:206, addBadge:329) | PASS |
| Brain Settings — error state | Specified (line 164) | Implemented (settings.js:217) | PASS |
| Brain Settings — local override label | Specified (line 163, D15) | Implemented in `addBadge('override')` (settings.js:338), only triggered by scope edit | DRIFT — no override badge shown for lifecycle/consolidation/threshold edits |
| Brain Settings — disable confirmation dialog | Specified (line 226) | Implemented with full focus trap (settings.js:120-157) | PASS |
| Brain Settings — purge confirmation w/ count | Specified (line 232: "Permanently remove [N] expired thoughts?") | Implemented (settings.js:691-704) | PASS |
| Brain Settings — accessibility (kbd, ARIA, contrast, ≥44px touch) | Specified (lines 180-187) | Mostly implemented; gaps below | See Findings #8, #9, #10 |
| **Dashboard — overview, charts, agents, alerts, pipelines table, agent detail modal** | **NO SPEC — `docs/ux/` does not exist; no design doc anywhere** | Implemented in `dashboard.html` (1760 lines, vanilla + Chart.js CDN) | **Spec absent — inferred from code only.** All findings against the dashboard are based on baseline UX/a11y heuristics, not against an authored design. |
| Dashboard — loading state | No spec — inferred | **Not implemented.** `.skeleton` class defined (line 532) but never applied; sections are simply empty until first fetch resolves. | MISSING |
| Dashboard — empty state | No spec — inferred | Implemented per section via `emptyCard()` (line 1729) | PASS (functionally) |
| Dashboard — error state | No spec — inferred | `.error-banner` toggled by class (line 737), no live region, no retry CTA | DRIFT (see #4) |
| Dashboard — populated state | No spec — inferred | Implemented | PASS |
| Dashboard — overflow / pagination of pipelines table | No spec — inferred | All rows rendered unbounded; only `overflow-x:auto` for narrow viewports | MISSING (no pagination, no "showing N of M") |
| Dashboard — agent detail modal | No spec — inferred | Implemented with neither `role="dialog"`, focus trap, nor focus restoration | DRIFT (see #1, #2) |

---

## Findings

| # | Severity | Layer | Category | Finding | Location | Recommendation |
|---|---|---|---|---|---|---|
| 1 | **Critical** | Dashboard | Accessibility / Modal semantics | Agent detail modal has **no dialog semantics**: missing `role="dialog"`, `aria-modal="true"`, `aria-labelledby`. Wrapping element is plain `<div class="modal-overlay">`. Modal heading is a `<span class="modal-agent-name">`, not an `<h2>`. Screen reader users encounter the modal as ambient page content with no announcement. Settings.js implements all of this correctly (`index.html:142`), so the pattern is known to the codebase — the dashboard simply ignored it. | `brain/ui/dashboard.html:853-867` | Add `role="dialog" aria-modal="true" aria-labelledby="modal-agent-name"` to `#agent-modal-overlay` (or to inner `.modal`), promote `.modal-agent-name` to an `<h2 id="modal-agent-name">`, and copy the focus-trap helper from `settings.js:139-157`. |
| 2 | High | Dashboard | Accessibility / Focus management | Modal opens via `overlay.classList.add('visible')` (line 1496) with **no focus management**: focus is not moved into the modal, no Tab trap exists, and on close focus is **not restored** to the agent card that triggered it. Keyboard users are stranded. | `brain/ui/dashboard.html:1473-1509`, `1604-1607` | Capture `document.activeElement` on open, move focus to the close button, install a `keydown` Tab handler matching `settings.js:139`, restore focus on close. |
| 3 | High | Dashboard | Accessibility / Keyboard operation | Agent cards are clickable `<div class="agent-card">` (line 1417) with `cursor: pointer` and a `click` handler, but they have **no `tabindex`, no `role="button"`, no Enter/Space handler**. Keyboard users cannot open agent details at all. Settings.js solved exactly this problem for editable lifecycle cells (`settings.js:379-490`); the pattern was not applied here. | `brain/ui/dashboard.html:1417, 1432-1440` | Add `tabindex="0" role="button" aria-label="View {agent} detail"` to non-Eva cards and a `keydown` listener that triggers the same `openAgentModal` on Enter/Space. |
| 4 | High | Dashboard | Accessibility / Error feedback | Error banner is toggled via `.visible` class (`display:none` → `display:block`) with **no `role="alert"` or `aria-live`**. Screen reader users get no announcement when the brain server becomes unreachable. The text also hard-codes `localhost:8788`, which will be wrong for any non-default deployment. | `brain/ui/dashboard.html:737-739`, JS at `1020`, `1024` | Add `role="alert" aria-live="assertive"` to `#error-banner`. Replace the literal port with `${window.location.host}` interpolation, or omit the address. |
| 5 | High | Dashboard | Accessibility / Charts | Both `<canvas id="cost-chart">` and `<canvas id="quality-chart">` have **no text alternative whatsoever** — no `aria-label`, no fallback content inside the canvas, no `role="img"`, no adjacent summary table. Chart.js renders entirely to a bitmap; the data is invisible to screen readers and to printing. | `brain/ui/dashboard.html:800, 816` | At minimum add `role="img"` plus an `aria-label` summarising the latest values ("Cost trend, last value $X, peak $Y"). For a real fix, render an offscreen `<table>` with the same data and `aria-describedby` from the canvas. |
| 6 | High | Dashboard | Accessibility / Form controls | Scope `<select id="scope-select">` has **no `<label>`**. The visible text "Project:" is a `<span class="scope-label">` with no `for` attribute and no `aria-labelledby` link from the select. | `brain/ui/dashboard.html:759-764` | Either convert the span to `<label for="scope-select">` or add `aria-labelledby="scope-label"` to the select and `id="scope-label"` to the span. |
| 7 | High | Dashboard | State completeness / Loading | **No loading state for any data-fetching surface.** On first paint, `stat-grid`, both chart canvases, `agent-grid`, `alert-list`, and `pipelines-table-wrap` are empty `<div>`s. Until `loadData()` resolves, the user sees a header reading "Loading…" and a blank page. The `.skeleton` shimmer class is defined at `dashboard.html:532` but never applied. There is also a perceptible flicker where `summaryData.length === 0` triggers the "No pipeline data yet" empty state on initial render before the fetch completes — users see a misleading "no data" message during the load. | `dashboard.html:532` (unused class), `1011-1027` (loadData), `1054-1058` (renderOverview empty branch fires before fetch resolves) | Set an explicit `state = 'loading'` flag in `loadAll()` and render `<div class="skeleton" style="height:80px">` placeholders into each section before kicking off `Promise.all`. Only fall through to empty-state copy after the fetch resolves with `[]`. |
| 8 | High | Dashboard | Visual / Status indicator | The `.refresh-dot` (line 766) animates green continuously regardless of fetch state. When `loadData()` fails the dot keeps pulsing green next to "Auto-refresh", contradicting the red error banner above. | `dashboard.html:157-168, 766-770`, JS error path `1023-1026` | On `.catch`, add a `.failing` class to `.refresh-dot` that switches its background to `var(--red)` and disables the pulse animation. Restore on next successful fetch. |
| 9 | High | Settings | UX / Silent failures | Three save paths swallow errors with empty `catch {}` blocks and give the user **zero feedback** that the operation failed: `executeBrainToggle` (settings.js:560-564) reverts the toggle silently; `consolBlurHandler` (lines 631-633) silently keeps the rejected value in the input; `thresholdBlurHandler` (lines 678-680) the same. Compared with `saveLifecycleBtn`, which does flash "Error saving" (line 514-518), these are inconsistent and worse. | `brain/ui/settings.js:560-564, 631-633, 678-680` | Add a per-input `.saved-indicator` "Save failed" message in red on catch, mirroring the lifecycle pattern. Reuse `flashSaved()` with an error variant. |
| 10 | High | Settings | Accessibility / Validation | Scope validation error message lives in a `<div class="error-msg">` with **no `id` and no `aria-describedby` from `#scope-input`**. Screen reader users typing an invalid scope hear nothing — only sighted users see the red border + message. The pattern in the spec ("Red border + inline error if invalid") is partially honored but not announced. | `brain/ui/index.html:50-51`, JS scope handler `settings.js:571-590` | Add `id="scope-error"` to the error div, set `aria-describedby="scope-error"` on the input, and toggle `aria-invalid="true"` when `has-error` is applied. |
| 11 | Medium | Settings | State management | `setAllFieldsDisabled(disabled)` (settings.js:236) iterates **all** inputs/buttons and overwrites the disabled flag uniformly. In `shared-missing` state the code does `brainToggle.disabled = true; setAllFieldsDisabled(true);` (lines 201-202) — order works, but if any future code path calls `setAllFieldsDisabled(false)` first the toggle becomes enabled despite the missing-env precondition. Brittle order dependency. | `brain/ui/settings.js:196-204, 236-243` | Track disablement intent per-control rather than via a global sweep, or keep a separate `lockedControls` set that is reapplied after each broad toggle. |
| 12 | Medium | Settings | UX / Refresh | After `purgeConfirm` succeeds (settings.js:707-718) only `loadHealth()` is re-fetched. `lifecycleData` and any cached stats are stale until the user reloads. The thought count visible in the status bar updates, but if a future addition shows by-type counts in the lifecycle table they will diverge. | `brain/ui/settings.js:707-718` | Re-run `Promise.all([loadHealth(), loadConfig(), loadThoughtTypes()])` on purge success. |
| 13 | Medium | Settings | UX / DATABASE_URL_DISPLAY dead code | `populateConfig` (line 293) reads `DATABASE_URL_DISPLAY`, but that constant is declared on line 327 as `""` and never assigned elsewhere. The fallback chain `cfg.database_url \|\| DATABASE_URL_DISPLAY \|\| "(not set)"` is intentional masking-placeholder scaffolding that was never wired. | `brain/ui/settings.js:293, 327` | Either implement actual masking (`postgresql://****@host:port/db`) or remove `DATABASE_URL_DISPLAY` entirely. |
| 14 | Medium | Settings | Accessibility / Reduced motion | Neither stylesheet honors `@media (prefers-reduced-motion: reduce)`. The status-bar pulse (settings.css:89), spin (line 514), shimmer (dashboard.html:539), and pulse-dot (dashboard.html:165) all run unconditionally. WCAG 2.3.3 / 2.1 AAA. | `brain/ui/settings.css:89-96, 514-516`; `brain/ui/dashboard.html:165-168, 539-542` | Wrap each `@keyframes` consumer in a `prefers-reduced-motion: no-preference` query, or add `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }`. |
| 15 | Medium | Dashboard | Accessibility / Document structure | Dashboard has **no `<main>` landmark**. The body contains a single `<div class="dashboard">` wrapping a `<header>` and several `<section>` elements. Screen readers using landmark navigation cannot jump to main content. Settings page has the same issue (`<div class="settings-page">` instead of `<main>`). | `dashboard.html:735`; `index.html:10` | Replace `<div class="dashboard">` with `<main class="dashboard">`, same for `index.html`. |
| 16 | Medium | Dashboard | Visual contrast | `--text-light: #94a3b8` on `--bg: #f6f9fd` measures ≈ 2.6:1, used for `.stat-sub` (line 268), `.empty-state-icon` color, `.empty-state p` color via `--text-mid` cascade, and the `<select>` placeholder arrow. **Fails WCAG AA 4.5:1 for body text.** The settings stylesheet's `--color-dimmed: #999999` on `#fafafa` ≈ 2.85:1 is used for `input:disabled` text (settings.css:251-256) — disabled text is exempt by WCAG, but the secondary "sub" copy is not. | `dashboard.html:23 (var def), 268 (stat-sub)`; `settings.css:18, 251-256` | Darken `--text-light` to `#64748b` (≈ 4.6:1) or `#475569` (matches `--text-mid`). Reserve `--text-light` for decorative borders only. |
| 17 | Medium | Settings | UX / Test Connection | `testConnectionBtn` click handler hits the same `/api/health` endpoint that `pollHealth` already calls every 30s. The test does not actually test the credentials/scope the user just edited — the form values are not pushed to the server before the test runs. The button is misleading: it tests the *currently saved* state, not the *current form* state. | `brain/ui/settings.js:596-616` | Either save pending edits before testing, or rename to "Refresh status" and add an inline note. |
| 18 | Medium | Both | Resilience / CDN dependence | `dashboard.html` loads Chart.js (`<script src="https://cdn.jsdelivr.net/npm/chart.js">`, line 10) and Google Fonts (DM Sans, DM Serif Display, line 9) from public CDNs **without SRI integrity hashes** and without fallback. If either CDN is unreachable (offline dev, corporate proxy, CDN outage), the dashboard renders with broken fonts and zero charts — silently. The brain server is intended for local-first use; this is a regression. | `brain/ui/dashboard.html:7-10` | Vendor Chart.js into `brain/ui/vendor/chart.umd.js` and serve locally; same for the two font files. Add SRI integrity hashes if CDN is retained. |
| 19 | Medium | Settings | Accessibility / Live region | `consolidationInfo` div (`index.html:97`) is `aria-live="polite"` but its text is also assembled in `populateConfig` (settings.js:307-311) and again in `pollHealth` (744-748). Every 30-second poll re-announces "Last run: … Next: …" even when the values are unchanged. Polite live regions should re-announce only on change. | `brain/ui/settings.js:744-748` | Compare against the previous textContent before assignment; only update when changed. |
| 20 | Medium | Settings | UX / Polling cleanup | `setInterval(pollHealth, 30000)` (line 771) stores the handle in `healthInterval` but no `beforeunload`/`visibilitychange` cleanup. Background tabs continue polling, which on a developer machine across many open tabs can produce noise in server logs and waste CPU. | `brain/ui/settings.js:724, 771` | Pause the interval on `document.visibilitychange` when `document.hidden`; resume on visible. |
| 21 | Medium | Dashboard | UX / Pagination | `renderPipelinesTable` (line 1696) renders **all** rows from `summaryData` unbounded. With months of pipeline history this becomes a multi-thousand-row table. No pagination, no row cap, no "showing N of M". | `brain/ui/dashboard.html:1696-1725` | Cap at 50 most-recent rows by default with a "Show more" toggle, or paginate. |
| 22 | Medium | Dashboard | UX / Table semantics | `renderPipelinesTable` produces a `<table class="pipeline-table">` with `<thead>` but **no `scope` attributes on `<th>` and no `<caption>`**. Settings lifecycle table has both (`index.html:63-67`). Inconsistent. | `brain/ui/dashboard.html:1719-1724` | Add `scope="col"` to each header `<th>` and a `<caption class="visually-hidden">` describing the table. |
| 23 | Low | Settings | UX / Empty placeholder | When `cfg.database_url` is null, `dbUrlInput.value = "(not set)"` is written into a `type="url"` input (settings.js:293). HTML5 will mark "(not set)" as invalid (not a URL), which on some browsers triggers a red outline via `:invalid`. | `brain/ui/settings.js:293`; `index.html:44` | Change input type to `text` for display-only, or write empty string + `placeholder="not set"`. |
| 24 | Low | Settings | UX / Copy | Status text "Disconnected — pipeline will use baseline mode" (settings.js:220) provides graceful framing — good. But the test-result spinner span has the text "Testing..." inside a `.test-result` div without `role="status"`; the parent has `aria-live="polite"` which works, but the spinner SVG class is decorative and could announce as "image" on some readers. | `brain/ui/settings.js:598`; `index.html:55` | Add `aria-hidden="true"` to the spinner span. |
| 25 | Low | Both | UX / Focus visibility on dark backgrounds | `*:focus-visible { outline: 2px solid var(--color-focus) }` uses blue `#2563eb` on settings page (good) but on the dashboard the danger zone background `--red-bg #fef2f2` and modal overlay backdrop have no contrast check — focus rings on the modal close button against the dark `rgba(2,18,39,0.5)` overlay are fine, but on the agent cards `(--text-light)` border the focus outline reuses browser default (none defined for dashboard). | `dashboard.html` — no `*:focus-visible` rule defined | Add an explicit `*:focus-visible` outline rule to dashboard.html stylesheet matching settings.css line 551. |
| 26 | Low | Dashboard | UX / Tooltip on truncated descriptions | Modal table descriptions (`renderModalBodyActivity` line 1547) use `text-overflow: ellipsis` plus a `title` attribute. `title` tooltips are not keyboard-accessible and not announced by all screen readers. | `dashboard.html:682-687, 1547` | Replace `title` with a click-to-expand or use `aria-describedby` pointing at a hidden full-text element. |
| 27 | Low | Settings | UX / Responsive 44px | The CSS at `settings.css:617-628` enforces ≥44px touch targets at ≤480px viewport, but the Save button on lifecycle (`<button class="btn-primary">`) only inherits the base 36px `min-height` (line 271). At desktop the button is 36px which is below WCAG 2.5.5 AAA target size of 44×44 (AA is 24×24 — passes). | `brain/ui/settings.css:271` | Acceptable for AA. Note for AAA: bump base button `min-height` to 40px for breathing room. |
| 28 | Low | Dashboard | Resilience / Console | All `.catch` handlers in dashboard.html silently swallow errors (e.g., `loadScopes` line 988-991, `loadData` line 1023-1026). For developers debugging the dashboard, no console output is emitted. | `dashboard.html:988, 1023, 1506, 1748` | Add `console.warn('[atelier-dashboard]', err)` in catches; this is a developer tool. |

---

## Five-State Audit

### Brain Settings (`index.html`)

| Screen | Empty | Loading | Populated | Error | Overflow |
|---|---|---|---|---|---|
| Settings page | PASS — `setState('empty')` shows "Not configured" + setup helper, dims sections | PASS — `setState('loading')` with pulse animation, all fields disabled | PASS — `setState('populated')` / `setState('shared-connected')` | PASS — `setState('error')` with helpful copy "pipeline will use baseline mode" | N/A — fixed-content settings page; CSS handles narrow viewports via 480px breakpoint |
| Lifecycle table | PASS — fallback row template (settings.js:357-362) renders default placeholder if API returns empty | DRIFT — table is rendered into via JS after fetch; during fetch the `<tbody>` is empty with no skeleton | PASS | DRIFT — `loadThoughtTypes` catches all errors silently (line 280-282), table stays empty with no message | N/A |
| Disable confirmation | N/A | N/A | PASS | N/A | N/A |
| Purge confirmation | N/A | N/A | PASS — count fetched and displayed before confirm | DRIFT — if `/api/stats` fails, dialog falls back to generic copy without count (settings.js:699-703); user has no warning that count is unknown | N/A |

### Dashboard (`dashboard.html`)

| Screen | Empty | Loading | Populated | Error | Overflow |
|---|---|---|---|---|---|
| Pipeline Overview (stat-grid) | PASS — `emptyCard()` and "Awaiting pipeline data" branches | **MISSING** — no skeleton, sections empty until fetch resolves | PASS | DRIFT — banner shows but stat-grid retains last value (or empty) with no per-section error state | N/A |
| Cost Trend chart | PASS — `showChartEmpty()` displays empty card | **MISSING** — canvas is blank during fetch | PASS | DRIFT — on fetch failure, chart retains previous render or stays blank; no per-chart error state | N/A |
| Quality Trend chart | PASS — distinct empty state with explanatory copy ("require pipeline telemetry capture", line 1306-1308) | **MISSING** | PASS | DRIFT (same as cost) | N/A |
| Agent Fitness grid | PASS — `emptyCard("No agent data yet")` | **MISSING** | PASS | DRIFT | N/A — but cards lay out via auto-fill grid which handles many agents |
| Agent Detail modal | PASS — "No invocation data found" (line 1502) | PASS — "Loading agent detail..." text shown immediately on open (line 1494) | PASS | PASS — "Failed to load agent detail." in red (line 1507) | DRIFT — modal-table truncates description with `text-overflow: ellipsis` but no row cap; long agent histories scroll inside `max-height: 85vh` modal which is acceptable |
| Degradation Alerts | PASS — "All clear. No degradation thresholds breached." (line 1680); also a "≥3 pipeline runs" gate copy (line 1615-1617) | **MISSING** | PASS | DRIFT — same as overview | N/A |
| Recent Pipelines table | PASS — `emptyCard("No pipelines recorded")` | **MISSING** | PASS | DRIFT | **MISSING** — no pagination, no row cap (Finding #21) |

**Summary:** Dashboard has **no loading state on any of seven surfaces** despite having a defined `.skeleton` class. This is the most consistent state-completeness gap in the review.

---

## Accessibility Audit

| Requirement | Verdict | Evidence |
|---|---|---|
| **Settings — landmark structure** | DRIFT | `index.html:10` uses `<div class="settings-page">` instead of `<main>`. No `<header>`/`<nav>` landmarks. |
| **Settings — heading hierarchy** | PASS | `<h1>Atelier Brain Settings</h1>` (line 11), `<legend>` per fieldset, `<h2>` in dialogs (lines 144, 156). |
| **Settings — form labels** | PASS | Every `<input>` has matching `<label for>` (lines 43, 47, 83, 88, 93, 113, 118). |
| **Settings — fieldset/legend grouping** | PASS | All six sections use `<fieldset>` + `<legend>`. |
| **Settings — toggle semantics** | PASS | `role="switch"`, `aria-labelledby` on all three toggles (lines 33, 108, 127). `aria-checked` updated programmatically (settings.js:559). |
| **Settings — status live region** | PASS | `<div class="status-bar" role="status" aria-live="polite">` (line 14). |
| **Settings — dialog semantics** | PASS | `role="dialog" aria-modal="true" aria-labelledby` on both dialogs (lines 142, 154). |
| **Settings — focus trap in dialogs** | PASS | Implemented in `dialogKeyHandler` (settings.js:139-157), includes Escape and shift-Tab handling. |
| **Settings — focus restoration** | PASS | `dialogTrigger` captured and restored (settings.js:120-137). |
| **Settings — keyboard-operable inline edit cells** | PASS | `tabindex="0"`, `role="button"`, `aria-label`, Enter/Space handler (settings.js:379-490). |
| **Settings — validation announcement** | DRIFT | Scope `error-msg` div not associated via `aria-describedby` (Finding #10). |
| **Settings — focus indicators** | PASS | `*:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px }` (settings.css:551). |
| **Settings — color contrast (body)** | PASS | `#1a1a1a` on `#fafafa` ≈ 16:1; `#555555` on `#fafafa` ≈ 7.4:1. |
| **Settings — color contrast (dimmed)** | NOTE | `#999999` on `#fafafa` ≈ 2.85:1; used only for disabled inputs (WCAG-exempt) and the not-configured icon (decorative + adjacent text). |
| **Settings — touch targets ≥44px** | PASS | Enforced at `≤480px` viewport (settings.css:617-628). |
| **Settings — `prefers-reduced-motion`** | DRIFT | No motion-reduction query (Finding #14). |
| **Dashboard — landmark structure** | DRIFT | No `<main>`; only `<header>` and `<section>` (Finding #15). |
| **Dashboard — heading hierarchy** | PASS (structurally) | `<h1>` once, `<h2 class="section-title">` per section. |
| **Dashboard — form labels** | DRIFT | `<select id="scope-select">` has no `<label>` (Finding #6). |
| **Dashboard — modal semantics** | **CRITICAL FAIL** | No `role="dialog"`, no `aria-modal`, no `aria-labelledby`, heading is a `<span>` (Finding #1). |
| **Dashboard — modal focus trap** | FAIL | Not implemented (Finding #2). |
| **Dashboard — modal focus restoration** | FAIL | Not implemented (Finding #2). |
| **Dashboard — keyboard operation of cards** | FAIL | `<div>` cards with click handlers, no `tabindex`, no `role`, no kbd handler (Finding #3). |
| **Dashboard — error live region** | FAIL | `.error-banner` not a live region (Finding #4). |
| **Dashboard — chart text alternative** | FAIL | Both `<canvas>` elements have no text alternative (Finding #5). |
| **Dashboard — table semantics** | DRIFT | Pipeline table missing `scope` and `<caption>` (Finding #22). |
| **Dashboard — focus indicators** | DRIFT | No `*:focus-visible` rule defined; relies on browser default (Finding #25). |
| **Dashboard — color contrast (`--text-light`)** | FAIL | `#94a3b8` on `#f6f9fd` ≈ 2.6:1 — fails AA for `.stat-sub` body text (Finding #16). |
| **Dashboard — `prefers-reduced-motion`** | DRIFT | Pulse-dot, shimmer, transitions all unconditional (Finding #14). |

---

## Positive Observations

1. **`settings.js` dialog management is reference-quality.** `openDialog`/`closeDialog`/`dialogKeyHandler` (lines 120-157) implement focus capture, focus-into-first-button, full Tab focus trap (with shift+Tab), Escape-to-close, and focus restoration to the trigger element. This is exactly the pattern that the dashboard fails to copy. Use this as the template for fixing `dashboard.html`'s modal.

2. **`settings.js` keyboard-operable custom controls.** The lifecycle inline-edit cells (`renderLifecycleTable`, lines 350-399) decorate `<td>` elements as buttons with `tabindex="0"`, `role="button"`, descriptive `aria-label` strings rebuilt from current values, and an Enter/Space `keydown` handler (lines 482-490). Users can tab through, hit Enter to enter edit mode, type, hit Enter again to commit, Escape to cancel. This is the right way to do click-to-edit accessibly.

3. **`settings.html` semantic baseline.** Every input has a matching `<label for>`, every section is wrapped in `<fieldset>`/`<legend>`, all three toggles carry `role="switch"` and `aria-labelledby`, the status bar is `role="status" aria-live="polite"`, and inline status spans (`#lifecycle-saved`, `#consol-interval-saved`, etc.) are also `aria-live="polite"`. This is what a vanilla-HTML accessibility-first form looks like.

4. **Dashboard XSS hygiene is consistent.** Every `innerHTML` interpolation in `dashboard.html` runs untrusted strings through `escapeHtml()` (lines 944-948, used at 1160-1163, 1415-1429, 1547, 1594, 1689-1691, 1710). There is no raw concatenation of database-sourced text into HTML. Given how much rendering this file does via string templates, the discipline here is notable.

5. **Settings.css responsive table-to-card transformation.** The 480px breakpoint (settings.css:570-633) converts the lifecycle `<table>` into a stacked card layout via `display: block`, hides the `<thead>` off-screen with `position: absolute; left: -9999px`, and uses `td::before { content: attr(data-label) }` to surface the column header inside each cell. Combined with the `data-label` attribute set in `renderLifecycleTable` (settings.js:369, 376, 388), this is a clean, JS-light responsive table pattern that preserves semantics on desktop and readability on mobile, while enforcing 44px touch targets.

6. **Dashboard quality empty state has explanatory recovery text.** `renderQualityChart` distinguishes "no rows yet" from "rows exist but no quality telemetry" and renders a dedicated empty state (`dashboard.html:1299-1311`) explaining *why* the chart is empty ("Quality metrics require pipeline telemetry capture… will populate after your first pipeline run with v3.8.0+"). This is the right way to handle a "feature exists but data isn't there yet" state — most empty states in the codebase just say "no data".

7. **Both surfaces degrade to baseline behavior on fetch failure.** Settings transitions to an explicit `error` state with the recovery message "pipeline will use baseline mode" (settings.js:220). Dashboard shows an error banner with troubleshooting guidance and continues attempting to refresh on the 10-minute interval. Neither UI hard-crashes on a missing brain server, which matches the "brain is opt-in, non-blocking" architectural stance.

8. **Static serving prevents directory traversal and limits MIME types.** `brain/lib/static.mjs:46` rejects `filePath` not starting with `UI_DIR`, and the `MIME_TYPES` allowlist (lines 14-18) returns 404 for any extension not in `.html`/`.css`/`.js`. The token injection at line 61-66 only fires for `.html` and uses `JSON.stringify` for safe escaping. The serving layer is small and correct.

---

## Notes on Spec Absence

Per task instructions: `docs/ux/` does not exist on this project. The only partial UX doc is `docs/brain/atelier-brain-settings-ux.md`, which covers **only the settings page**, was authored 2026-03-21, and has its DoD checklist (D1-D15) entirely **unchecked**. The dashboard — by far the larger and more user-facing surface — has **no design doc anywhere in the repository**. All dashboard findings above were generated from baseline UX/a11y heuristics without a design baseline; some "DRIFT" / "MISSING" verdicts may instead reflect intentional product decisions that were never written down. This itself is a process gap worth noting to Eva: shipping 1760 lines of single-file UI without a UX spec is precisely how the regressions in Findings #1-5 made it past review.

The most actionable next step for Sable (producer mode) would be to author `docs/ux/dashboard.md` retroactively, then re-run this audit against the spec rather than against heuristics — at which point several of the "DRIFT" verdicts will firm up into "PASS" or "MISSING".
