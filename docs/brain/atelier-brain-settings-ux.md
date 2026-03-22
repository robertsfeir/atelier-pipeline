# UX Design: Atelier Brain Settings

**Designer:** Sable | **Date:** 2026-03-21
**Feature Spec:** docs/product/atelier-brain-feature-spec.md

---

## DoR: Requirements Extracted

| # | Requirement | Source |
|---|---|---|
| R1 | Brain is opt-in, disabled by default | US-7 AC |
| R2 | TTL lifespans configurable per thought type without code changes | US-4 AC |
| R3 | Consolidation timer interval configurable | US-5 AC |
| R4 | Scope path configurable per project | US-6 AC |
| R5 | Brain health visible to user | US-7 AC |
| R6 | Conflict detection can be disabled | Technical spec, conflict detection slice |
| R7 | Settings UI must be simple — this is a developer tool, not a consumer app | User directive |
| R8 | Solo developer is primary user today; team settings are future | Feature spec, Users table |
| R9 | Three deployment tiers: solo personal, team isolated, team shared | Feature spec, US-8/US-9/US-10 |
| R10 | Config priority: project-level > user-level > none | Feature spec, US-10 AC |
| R11 | Shared config: Database URL and Scope are read-only (team setting), credentials via env vars | Feature spec, US-9 AC |

---

## Design Intent

A single-page settings interface for the atelier brain. The user is a developer — they understand configuration. The design respects that: no wizards, no onboarding tours, no unnecessary chrome. Show the current state, let them change it, confirm the change. Every setting maps directly to a database row or a config value. Nothing is hidden.

The mental model: **a control panel for the brain, not a brain explorer.** Browsing thoughts, tracing chains, searching memory — those happen through the agents and MCP tools. This UI is strictly for configuration and health monitoring.

## Jobs-to-be-Done

**When** I'm setting up atelier-pipeline on a new project,
**I want** to enable the brain and configure its scope,
**So I can** start capturing institutional memory from the first pipeline run.

**When** I notice the brain feels noisy or stale,
**I want** to adjust TTL lifespans and consolidation frequency,
**So that** search results stay relevant without me manually pruning.

**When** something feels wrong with agent context,
**I want** to see brain health at a glance — is it connected, how many thoughts, last consolidation,
**So I can** quickly determine if the brain is the issue or something else.

## User Journey Map

| Stage | Doing | Thinking | Feeling |
|---|---|---|---|
| **First setup** | Runs brain-setup skill, then opens settings to verify | "Did it actually connect?" | Cautious, wants confirmation |
| **Daily use** | Doesn't touch settings. Brain works in background. | Nothing — that's the point. | Invisible is correct |
| **Tuning** | Notices stale results. Opens settings. Adjusts TTL or consolidation. | "90 days is too long for drift findings" | In control, surgical |
| **Troubleshooting** | Pipeline feels slow or agents seem contextless. Checks health. | "Is the brain even running?" | Wants a quick binary answer |

## User Flow

```
Developer opens Settings
        │
        ├── Brain Status (always visible at top)
        │   └── Connected / Disconnected + thought count + last consolidation
        │
        ├── Enable / Disable toggle
        │   └── If disabling: confirm dialog ("Pipeline will run without brain context")
        │
        ├── Connection section
        │   ├── Database URL (read-only, set via env)
        │   ├── Scope path (editable, ltree format)
        │   └── Test Connection button → success/failure indicator
        │
        ├── Thought Lifecycle section
        │   ├── Table: thought type | default TTL | default importance
        │   ├── Each row editable inline
        │   └── Save → updates thought_type_config table
        │
        ├── Consolidation section
        │   ├── Timer interval (minutes, number input)
        │   ├── Min thoughts per pass (number input)
        │   ├── Max thoughts per pass (number input)
        │   └── Last run timestamp + next scheduled
        │
        ├── Conflict Detection section
        │   ├── Enable / Disable toggle
        │   ├── Similarity threshold for duplicate (default 0.9)
        │   ├── Similarity threshold for candidate (default 0.7)
        │   └── LLM classification enable / disable
        │
        └── Danger Zone
            └── Purge expired thoughts (keeps active + reflections)
```

## Screen-by-Screen Design

### Screen 1: Brain Settings (Single Page)

**Purpose:** All brain configuration on one scrollable page. No tabs, no navigation — the settings surface is small enough for one view.

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│  Atelier Brain Settings                             │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ ● Connected (project) 1,247 thoughts Last sync:│  │
│  │                                  2 min ago     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  Brain ─────────────────────────────── [Enabled ●]  │
│                                                     │
│  ── Connection ──────────────────────────────────── │
│                                                     │
│  Database    postgresql://localhost:5432/atelier     │
│  Scope       [ acme.payments                    ]   │
│             └ ltree path (e.g. org.product.team)    │
│  [ Test Connection ]  ✓ Connected                   │
│                                                     │
│  ── Thought Lifecycle ───────────────────────────── │
│                                                     │
│  Type          │ TTL (days) │ Default Importance     │
│  ─────────────────────────────────────────────────  │
│  decision      │ ∞          │ 0.9                    │
│  preference    │ ∞          │ 1.0                    │
│  lesson        │ 365        │ 0.7                    │
│  rejection     │ 180        │ 0.5                    │
│  drift         │ 90         │ 0.8                    │
│  correction    │ 90         │ 0.7                    │
│  insight       │ 180        │ 0.6                    │
│  reflection    │ ∞          │ 0.85                   │
│                                          [ Save ]   │
│                                                     │
│  ── Consolidation ───────────────────────────────── │
│                                                     │
│  Run every     [ 30 ] minutes                       │
│  Min thoughts  [ 3  ] per pass                      │
│  Max thoughts  [ 20 ] per pass                      │
│  Last run: 2026-03-21 08:15    Next: 08:45          │
│                                                     │
│  ── Conflict Detection ──────────────────────────── │
│                                                     │
│  Conflict detection ──────────────── [Enabled ●]    │
│  Duplicate threshold   [ 0.9 ]                      │
│  Candidate threshold   [ 0.7 ]                      │
│  LLM classification ─────────────── [Enabled ●]     │
│                                                     │
│  ── Danger Zone ─────────────────────────────────── │
│                                                     │
│  [ Purge Expired Thoughts ]  Removes thoughts past  │
│   their TTL. Active thoughts and reflections are    │
│   preserved. This cannot be undone.                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**States:**

| State | Appearance |
|---|---|
| **Empty (first visit, brain not set up)** | Status bar shows "○ Not configured". Enable toggle is off. Connection section shows empty fields with helper text: "Run /brain-setup to configure, or enter connection details below." All other sections are collapsed/dimmed. |
| **Loading (connecting)** | Status bar shows "◐ Connecting..." with subtle pulse animation. All fields disabled. |
| **Populated (normal operation)** | As shown in layout above. Status bar green. All sections editable. |
| **Shared config, missing env vars** | Status bar shows "○ Config found — missing credentials". Helper text: "Project brain config detected. Set OPENROUTER_API_KEY in your environment to connect." Enable toggle disabled until env vars are resolved. Connection section shows database URL from project config (read-only), scope from project config (read-only — team setting). |
| **Shared config, connected** | Same as Populated, but Database URL and Scope show "(shared)" badge. These fields are read-only — the team lead set them. Lifecycle, consolidation, and conflict detection settings remain editable — changes write to `${CLAUDE_PLUGIN_DATA}/brain-overrides.json` (personal, not committed), NOT to the project config. A "(local override)" label appears next to any setting that differs from the project defaults. |
| **Error (brain unreachable)** | Status bar shows "● Disconnected — pipeline will use baseline mode" in amber. Test Connection shows failure reason. Enable toggle remains on (doesn't auto-disable). All config sections remain editable (settings persist even if brain is temporarily down). |
| **Overflow (N/A)** | Not applicable — this is a settings page with fixed content. Scrolls naturally on small viewports. |

**Interactions:**

| Element | Interaction | Feedback |
|---|---|---|
| Enable/Disable toggle | Click | Calls `PUT /api/config` { brain_enabled: true/false }. If disabling: confirmation dialog. Toggle animates. Status bar updates. |
| Scope path input | Edit + blur | Validates ltree format (alphanumeric + dots). Red border + inline error if invalid. |
| Test Connection button | Click | Button shows spinner. Result appears inline: ✓ Connected (green) or ✗ Error message (red). |
| TTL table cells | Click to edit inline | Number input appears. ∞ shown as empty field with placeholder "never". Tab to next cell. |
| Save button (lifecycle) | Click | Calls `PUT /api/thought-types/:type` for each changed row. Button briefly shows "Saved ✓" then returns to "Save". |
| Consolidation inputs | Edit + blur | Validates positive integers. Saves on blur. Shows "Saved" confirmation. |
| Threshold sliders/inputs | Edit + blur | Validates 0-1 range. Saves on blur. |
| Purge button | Click | Confirmation dialog: "This will permanently remove [N] expired thoughts. Active thoughts and reflections are preserved. This cannot be undone." Shows count before confirming. |

**Accessibility:**

| Requirement | Implementation |
|---|---|
| Keyboard navigation | All inputs tab-reachable in visual order. Toggles activated with Space. Buttons with Enter. |
| Screen reader | Status bar is `role="status"` (live region, announced on change). Sections use `fieldset` + `legend`. Toggle states announced ("Brain enabled" / "Brain disabled"). Table uses proper `th` scope. |
| Visual | All text meets 4.5:1 contrast. Status colors (green/amber/red) paired with icons (●/◐/○) — never color-only. Focus indicators visible on all interactive elements. |
| Text resize | Layout flows single-column. Table wraps on narrow viewports. All text resizable to 200% without horizontal scroll. |

**Responsive:**

| Viewport | Adaptation |
|---|---|
| Desktop (>768px) | Full layout as shown. Comfortable whitespace. |
| Tablet (768px) | Same layout, slightly reduced margins. Table stays tabular. |
| Mobile (<480px) | Status bar stacks (count below connection state). Lifecycle table becomes card layout (one type per card: type name as header, TTL and importance as labeled fields). Sections have slightly more vertical spacing for touch targets (min 44px). |

## Component Inventory

| Component | Instances | Notes |
|---|---|---|
| Status bar | 1 | Custom — connection indicator + stats. `role="status"` live region. |
| Toggle switch | 3 | Brain enable, conflict detection enable, LLM classification enable. Labeled, accessible. |
| Text input | 1 | Scope path. Validated on blur. |
| Number input | 7 | TTL values (×7 in table, but shown inline), consolidation timer/min/max, thresholds. |
| Inline editable table | 1 | Thought lifecycle config. 8 rows × 3 columns. |
| Button (primary) | 2 | Test Connection, Save. |
| Button (danger) | 1 | Purge Expired Thoughts. Red outline, not filled — destructive actions are visually distinct but not dominant. |
| Confirmation dialog | 2 | Disable brain, purge thoughts. Modal, focus-trapped, Escape to dismiss. |
| Section divider | 5 | Thin horizontal rule with section label. Low-contrast, structural not decorative. |
| Inline validation | 2 | Scope path format, number range validation. Red border + message below field. |

## Content & Copy

| Element | Copy |
|---|---|
| Page title | Atelier Brain Settings |
| Status: connected (personal) | ● Connected (personal) · [N] thoughts · Last sync: [time] |
| Status: connected (project) | ● Connected (project) · [N] thoughts · Last sync: [time] |
| Status: disconnected | ● Disconnected — pipeline will use baseline mode |
| Status: not configured | ○ Not configured |
| Status: connecting | ◐ Connecting... |
| Status: missing env vars | ○ Config found — missing credentials |
| Shared config helper | Project brain config detected. Set OPENROUTER_API_KEY in your environment to connect. |
| Shared badge | (shared) — displayed next to Database URL and Scope when using project-level config |
| Enable toggle label | Brain |
| Disable confirmation | Disable the brain? The pipeline will run without institutional memory. Agents will still function using files on disk. |
| Scope helper text | ltree path (e.g. org.product.team) |
| Scope validation error | Invalid scope format. Use lowercase letters separated by dots (e.g. acme.payments.auth) |
| TTL "never" | ∞ (displayed) / empty field with placeholder "never" (edit mode) |
| Save confirmation | Saved ✓ (inline, fades after 2s) |
| Consolidation "last run" | Last run: [timestamp] · Next: [timestamp] |
| Purge confirmation | Permanently remove [N] expired thoughts? Active thoughts and reflections are preserved. This cannot be undone. |
| Purge button | Purge Expired Thoughts |
| Danger zone description | Removes thoughts past their TTL. Active thoughts and reflections are preserved. This cannot be undone. |

## Design Decisions & Rationale

| Decision | Rationale |
|---|---|
| Single page, no tabs | The settings surface is ~15 inputs total. Tabs add navigation overhead for minimal content. One scrollable page is faster to scan and doesn't hide anything. |
| Database URL is read-only | Connection strings contain credentials. They should be set via environment variables, not typed into a UI. Display for verification only. |
| Config source shown in status bar | The developer needs to know WHICH brain they're connected to — personal or project. "(personal)" or "(project)" appears after "Connected" in the status bar. This prevents confusion when both configs exist and project wins silently. |
| No "reset to defaults" button | Defaults are in the `thought_type_config` table. A reset would need to know original values. Showing current values is sufficient — the developer can manually restore defaults. If we find this is needed later, it's a single button + migration. |
| Confirmation on disable only, not enable | Enabling the brain has no destructive consequences. Disabling means losing brain-enhanced context for future pipeline runs. Asymmetric risk → asymmetric friction. |
| Status bar is always visible | The #1 question when troubleshooting is "is the brain running?" The answer should never be more than a glance away. |
| Purge in danger zone, not per-type | Per-type purge adds complexity for a rare action. If the developer wants to purge only drift-type thoughts, they can adjust the TTL to 1 day and wait, or run a SQL query directly. The UI handles the common case. |
| No thought browser | Browsing, searching, and tracing thoughts is what the MCP tools are for. The settings UI manages configuration. Mixing concerns would bloat the interface and duplicate functionality that agents already have. |
| Inline edit for table | Modal-per-row would be heavy for simple number changes. Inline edit is faster and keeps context visible. |

## Notes for Cal

- The settings page needs a backend API to read/write `thought_type_config`, `brain_config`, and to execute brain health checks. Consider whether this is a thin REST layer over the existing MCP tools or a separate endpoint.
- The purge operation should be a database function, not application-layer iteration. `DELETE FROM thoughts WHERE status = 'expired'` with cascading relation cleanup.
- Status bar polling: consider a lightweight `/health` endpoint on the brain MCP server that returns connection state, thought count, and last consolidation timestamp. Polling interval: 30s is sufficient.

## Notes for Colby

- Use the project's existing component library for inputs, toggles, and buttons. Don't invent new components.
- The lifecycle table inline edit should use controlled inputs — click cell → show input → blur → save. No "edit mode" button per row.
- Status bar live region: use `aria-live="polite"` so screen reader announces changes without interrupting. Don't use `assertive`.
- The ∞ symbol in the TTL column: render as text, not a special character. Fall back to "never" if the font doesn't support it.
- Confirmation dialogs: focus-trap the modal. Return focus to the trigger button on dismiss. Escape key closes.
- Purge should show the count of expired thoughts BEFORE the user confirms. Query the count, display it in the dialog, then execute only on confirm.

---

## DoD: Verification

| # | Criterion | Verified |
|---|---|---|
| D1 | All 5 states designed (empty, loading, populated, error, overflow/N/A) | ☐ |
| D2 | Keyboard navigation covers all interactive elements | ☐ |
| D3 | Screen reader annotations specified for all dynamic content | ☐ |
| D4 | Contrast ratios meet 4.5:1 minimum | ☐ |
| D5 | Touch targets ≥44px on mobile | ☐ |
| D6 | Responsive behavior specified for desktop, tablet, mobile | ☐ |
| D7 | All copy written (no placeholder text) | ☐ |
| D8 | Destructive actions have confirmation | ☐ |
| D9 | Error states designed with recovery guidance | ☐ |
| D10 | Maps to feature spec user stories (US-4, US-5, US-6, US-7, US-8, US-9, US-10) | ☐ |
| D11 | Shared config state designed (missing env vars, connected with shared badge) | ☐ |
| D12 | Read-only fields in shared mode clearly indicated | ☐ |
| D13 | Config source (personal/project) visible in status bar | ☐ |
| D14 | Local overrides in shared mode write to personal file, not project config | ☐ |
| D15 | "(local override)" label shown next to settings that differ from project defaults | ☐ |
