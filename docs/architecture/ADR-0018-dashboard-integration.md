# ADR-0018: Dashboard Integration + quality-gate.sh Cleanup

## Status

Proposed

---

## DoR: Requirements Extracted

| # | Requirement | Source | Notes |
|---|-------------|--------|-------|
| R1 | Two mutually exclusive dashboard options during /pipeline-setup | Spec US-1, context-brief | User picks one or neither -- never both |
| R2 | PlanVisualizer: static project dashboard with 7 tabs, kanban, cost trends | Spec US-2, brain ecb6afe9 | Needs bridge script (brain telemetry to PIPELINE_PLAN.md) |
| R3 | claude-code-kanban: real-time session dashboard via filesystem watchers + SSE | Spec US-3, brain c0cb471f | Reads Claude Code native files directly |
| R4 | Setup menu with 3 options (PlanVisualizer, claude-code-kanban, None) with GitHub links | Spec AC-1, AC-5, AC-6 | Follows Step 6a-6e pattern |
| R5 | Config flag: `dashboard_mode` field in pipeline-config.json with values "plan-visualizer", "claude-code-kanban", "none" | Spec AC-2, AC-3, AC-4 | Added to both source/ and .claude/ config |
| R6 | PlanVisualizer bridge script: brain telemetry (T1/T2/T3) to PIPELINE_PLAN.md in PV format | Spec AC-7, US-2 | Falls back to pipeline-state.md when brain unavailable (AC-8) |
| R7 | claude-code-kanban: npx install + hook registration | Spec AC-6 | Hooks in ~/.claude/hooks/ (user-level, not project-level) |
| R8 | Neither tool's source code is modified | Spec NFR | We feed them data in their expected formats |
| R9 | quality-gate.sh auto-removed from hooks directory during /pipeline-setup | Spec AC-9, retro #003 | File deleted, no prompt |
| R10 | quality-gate.sh registration auto-removed from settings.json | Spec AC-10, retro #003 | Entry removed, no prompt |
| R11 | One-line notice when quality-gate.sh is cleaned up | Spec AC-13 | "Removed deprecated quality-gate.sh (see retro lesson #003)" |
| R12 | Re-running setup with different dashboard cleans up old choice | Spec AC-11, US-5 | Old artifacts removed, new installed |
| R13 | Dashboard failure never blocks /pipeline-setup or pipeline runs | Spec AC-12, NFR | Dashboard is strictly non-blocking |
| R14 | Idempotency: re-running with same dashboard is a no-op | Spec NFR | Same as Sentinel/Deps pattern |
| R15 | Bridge script fallback to pipeline-state.md when brain unavailable | Spec AC-8 | Less data but still functional |
| R16 | Edge cases: Node.js < 18 warn, npx missing warn, brain not configured fallback, both dashboards detected | Spec Edge Cases table | All handled gracefully |
| R17 | Eva post-pipeline wiring: bridge runs after Ellis, dashboard regenerated | Spec runtime flow | PlanVisualizer only -- kanban is passive |
| R18 | Enforcement hooks bypass during /pipeline-setup via ATELIER_SETUP_MODE=1 env var | Task constraint | Hooks block .claude/ writes; setup needs to write there |

### Retro Risks

| Lesson | Risk to this feature | Mitigation |
|--------|---------------------|------------|
| #003 (Stop hook race) | Directly relevant -- quality-gate.sh cleanup is part of this ADR | Cleanup is silent auto-removal, not a new hook |
| #004 (Hung process retry loop) | Bridge script or dashboard install could hang | Bridge script runs node, not a long-lived process. Install failures are caught and skipped. |
| #005 (Frontend wiring omission) | Bridge script is a producer with no consumer in-repo | Consumer is PlanVisualizer itself (external). Eva's post-pipeline wiring is the integration point. |

---

## Context

Pipeline users have no visual way to track pipeline runs. Two open-source tools address this from different angles: PlanVisualizer provides a static project-level dashboard (EPICs, kanban, cost trends, traceability across runs), while claude-code-kanban offers real-time session observation (live task movement, agent lifecycle via filesystem watchers). Neither is wired into atelier-pipeline today.

Separately, users who installed atelier-pipeline before v3.4 may still have the deprecated `quality-gate.sh` stop hook. Per retro lesson #003, this hook caused infinite retry loops by running the full test suite on every conversation stop. The hook was removed from source templates but there is no automated cleanup path for existing installations.

The Sentinel opt-in pattern (ADR-0009, implemented in Steps 6a-6e of SKILL.md) established the convention: config flag in pipeline-config.json, setup step in SKILL.md, idempotency checks, cleanup on switch. This ADR follows that pattern exactly, adding Step 6f after Darwin and before Brain.

### Spec Challenge

The spec assumes PlanVisualizer's markdown format (PIPELINE_PLAN.md) is stable and parseable by their `parse-release-plan.js`. If PlanVisualizer releases a breaking change to their parser or markdown schema, the bridge script produces output that PlanVisualizer cannot render. The design fails because the bridge is tightly coupled to an external project's undocumented format. Are we confident? Partially. Mitigation: the bridge script targets a pinned version/tag of PlanVisualizer (spec Risk #3), and the format is reverse-engineered from their parser source. The bridge output is validated against a known-good PlanVisualizer parse in the test spec.

SPOF: The bridge script (`telemetry-bridge.sh`). Failure mode: if the bridge fails (brain unavailable AND pipeline-state.md is empty, or node is missing, or the script has a bug), no PIPELINE_PLAN.md is generated, and the PlanVisualizer dashboard shows stale or no data. Graceful degradation: Eva logs the failure ("Bridge script failed: [reason]. Dashboard not updated.") and continues. The pipeline run itself is unaffected. The user can re-run the bridge manually. Dashboard failure is never a blocker (spec NFR, AC-12).

---

## Decision

Implement dashboard integration as a Step 6f opt-in in /pipeline-setup, following the established optional feature pattern. Add quality-gate.sh cleanup as a pre-step (Step 0) that runs unconditionally at the start of every /pipeline-setup invocation. The bridge script lives in `source/dashboard/` as a template, installed to the project by /pipeline-setup when PlanVisualizer is chosen.

### Anti-Goals

Anti-goal: Custom dashboard themes or branding. Reason: we do not modify either dashboard's source code -- we feed them data in their expected formats. Revisit: if users request atelier-branded visuals and both projects accept upstream contributions.

Anti-goal: Automatic dashboard opening during pipeline runs. Reason: the spec explicitly excludes this (Out of scope). The user runs the dashboard manually in a separate terminal. Revisit: when Eva gains a post-pipeline hook mechanism that can safely launch browser processes.

Anti-goal: Merging features from both dashboards into one unified view. Reason: the two tools serve different use cases (project-level vs session-level) and have incompatible data models. Forcing a merger would require maintaining a fork. Revisit: if a third-party tool emerges that natively combines both views.

### Data Flow

**PlanVisualizer path:**
```
Pipeline run -> Eva captures telemetry (T1/T2/T3 in brain, pipeline-state.md on disk)
  -> After Ellis commit (Eva's post-pipeline wiring):
    -> Bridge script reads brain T1/T2/T3 via atelier_browse (or pipeline-state.md fallback)
    -> Generates PIPELINE_PLAN.md in PlanVisualizer's expected format:
       - Each pipeline run = one EPIC
       - Each agent phase = one Story under the EPIC
       - Task statuses mapped: Colby-done -> "In Progress", Roz-pass -> "Done", etc.
       - Cost data from T3 summaries
    -> Runs `node tools/generate-plan.js` to regenerate dashboard HTML
```

**claude-code-kanban path:**
```
Pipeline run -> Eva uses TaskCreate/TaskUpdate as usual
  -> claude-code-kanban watches ~/.claude/tasks/ via Chokidar filesystem watcher
  -> Agent lifecycle tracked via SubagentStart/Stop hooks (installed by npx --install)
  -> User runs `npx claude-code-kanban --open` in separate terminal
```

**Bridge script telemetry-to-markdown mapping:**

| Brain Telemetry Source | PIPELINE_PLAN.md Field | Fallback (no brain) |
|----------------------|----------------------|-------------------|
| T3 `pipeline_id` | EPIC title | pipeline-state.md feature name + date |
| T3 `sizing` | EPIC label | pipeline-state.md sizing |
| T2 `work_unit_id` | Story title | pipeline-state.md progress table rows |
| T2 `rework_cycles` | Story metadata | "0" (unknown) |
| T1 `agent_name` + `pipeline_phase` | Task under Story | pipeline-state.md agent column |
| T1 `duration_ms` | Task duration | omitted |
| T3 `total_cost_usd` | EPIC cost field | omitted |
| T2 `first_pass_qa` | Story status (Done vs Rework) | pipeline-state.md status column |
| T3 `rework_rate` | EPIC summary metric | omitted |

---

## Alternatives Considered

### Alternative A: Single dashboard choice (PlanVisualizer only)

PlanVisualizer covers the most ground (7 tabs, kanban, cost trends). Skip claude-code-kanban to reduce integration surface.

Rejected. The two tools serve fundamentally different use cases: PlanVisualizer is post-hoc project tracking (static HTML, regenerated after runs), while claude-code-kanban is live session observation (real-time SSE, watching files as they change). A solo developer who wants to watch agents work in real-time has no use for a static dashboard. Offering both as mutually exclusive options lets users pick the tool that matches their workflow.

### Alternative B: Install both dashboards simultaneously (non-exclusive)

Let users run both tools -- PlanVisualizer for project-level and claude-code-kanban for session-level.

Rejected. Both tools register hooks in settings.json / ~/.claude/hooks/. The spec identifies potential hook collision as a risk (Risk #2). More importantly, the cognitive overhead of maintaining two dashboard configurations, two sets of artifacts, and two potential failure paths outweighs the benefit. Users who want both can manually install the second tool outside the pipeline -- we do not prevent it, we just do not automate it.

### Alternative C: Build a custom dashboard from scratch

Build an atelier-native dashboard that combines project tracking and live session observation.

Rejected. This is a months-long effort for a feature that two existing open-source tools already solve. The pipeline's value is orchestration, not UI. Integrating existing tools (zero source modification, feed data in their expected formats) delivers value in days.

---

## Consequences

Positive:
- Users get visual pipeline tracking with zero custom UI development.
- Two options cover both use cases (project-level tracking and real-time observation).
- quality-gate.sh cleanup eliminates a known bug for users with older installations.
- All changes are additive and gated behind config flags -- zero impact on users who do not opt in.

Negative:
- Bridge script is tightly coupled to PlanVisualizer's undocumented markdown format. Breaking changes upstream require bridge updates.
- claude-code-kanban installs hooks at the user level (~/.claude/hooks/), not the project level. This is outside our normal installation scope and is not cleaned up by /pipeline-uninstall (project-scoped).
- The bridge script adds a post-pipeline step that increases pipeline end time (marginal -- single node script execution).

---

## Blast Radius

| File | Change | Impact |
|------|--------|--------|
| `source/dashboard/telemetry-bridge.sh` | CREATE | Bridge script template (brain telemetry to PIPELINE_PLAN.md) |
| `source/pipeline/pipeline-config.json` | MODIFY | Add `"dashboard_mode": "none"` field |
| `.claude/pipeline-config.json` | MODIFY | Add `"dashboard_mode": "none"` field |
| `skills/pipeline-setup/SKILL.md` | MODIFY | Add Step 0 (quality-gate cleanup) + Step 6f (dashboard opt-in) + summary update |
| `source/rules/pipeline-orchestration.md` | MODIFY | Add post-pipeline bridge wiring section |
| `.claude/rules/pipeline-orchestration.md` | MODIFY | Installed copy (dual tree) |
| `source/references/invocation-templates.md` | MODIFY | Add `dashboard-bridge` invocation template |
| `.claude/references/invocation-templates.md` | MODIFY | Installed copy (dual tree) |
| `source/hooks/enforce-paths.sh` | MODIFY | Add `ATELIER_SETUP_MODE` bypass line |
| `source/hooks/enforce-sequencing.sh` | MODIFY | Add `ATELIER_SETUP_MODE` bypass line |
| `source/hooks/enforce-git.sh` | MODIFY | Add `ATELIER_SETUP_MODE` bypass line |
| `.claude/hooks/enforce-paths.sh` | MODIFY | Installed copy (dual tree) |
| `.claude/hooks/enforce-sequencing.sh` | MODIFY | Installed copy (dual tree) |
| `.claude/hooks/enforce-git.sh` | MODIFY | Installed copy (dual tree) |

Consumer mapping:
- `source/dashboard/telemetry-bridge.sh` (producer: bridge script) -> consumed by Eva's post-pipeline wiring (pipeline-orchestration.md) and by /pipeline-setup Step 6f (copies to project)
- `dashboard_mode` config flag (producer: pipeline-config.json) -> consumed by SKILL.md Step 6f (install gate), Eva's post-pipeline wiring (conditional bridge invocation), Eva boot announcement
- `dashboard-bridge` invocation template -> consumed by Eva when running the bridge after Ellis commit
- Step 0 cleanup (producer: SKILL.md) -> consumed by every /pipeline-setup invocation (unconditional)
- `ATELIER_SETUP_MODE` bypass line (producer: hook scripts) -> consumed by SKILL.md `export ATELIER_SETUP_MODE=1` before write operations; triggered by /pipeline-setup on re-install/update of existing installation

---

## Implementation Plan

### Step 1: quality-gate.sh Cleanup + Config Flag

**After this step, I can:** Re-run /pipeline-setup and any leftover quality-gate.sh from pre-v3.4 installs is automatically detected and removed. The `dashboard_mode` config field exists with default value "none".

**Files to modify:**
- `skills/pipeline-setup/SKILL.md` -- add Step 0 (quality-gate.sh cleanup) at the top of the setup procedure, before Step 1
- `source/pipeline/pipeline-config.json` -- add `"dashboard_mode": "none"` field
- `.claude/pipeline-config.json` -- add `"dashboard_mode": "none"` field

**Step 0 content (quality-gate.sh cleanup):**

Before Step 1 (Gather Project Information), /pipeline-setup runs this unconditionally on every invocation:

1. Check if `.claude/hooks/quality-gate.sh` exists. If found: delete the file.
2. Check if `.claude/settings.json` contains a hook entry referencing `quality-gate.sh`. If found: remove that hook entry from the JSON. If the removal leaves an empty hooks array for that event type, remove the event type entry.
3. If either artifact was found and removed: print "Removed deprecated quality-gate.sh (see retro lesson #003)."
4. If neither found: silent no-op.

**Config flag addition:**

Add `"dashboard_mode": "none"` to both config files after the `darwin_enabled` field. This follows the established field ordering convention.

**Acceptance criteria:**
- Step 0 block exists in SKILL.md, positioned before Step 1
- Step 0 handles all four edge cases from the spec: neither found, file only, settings.json entry only, both found
- Both pipeline-config.json files contain `"dashboard_mode": "none"`
- Both config files remain valid JSON
- No existing fields are modified or removed

**Estimated complexity:** Low. Three files modified, straightforward detection logic.

---

### Step 2: Dashboard Setup Step 6f (Menu + Install/Uninstall)

**After this step, I can:** Run /pipeline-setup and see a 3-option dashboard menu after the Darwin offer. Choosing an option sets the config flag and runs the appropriate install command.

**Files to modify:**
- `skills/pipeline-setup/SKILL.md` -- add Step 6f block after Step 6e (Darwin), before Brain setup offer. Update summary printout to include dashboard line.

**Step 6f content:**

After the Darwin offer (whether user said yes or no), offer dashboard integration:

```
Dashboard integration (optional):
  1. PlanVisualizer -- project-level tracking with kanban, cost trends,
     traceability across pipeline runs
     https://github.com/ksyed0/PlanVisualizer
  2. claude-code-kanban -- real-time session dashboard, watch agents
     work live (lightweight, instant setup)
     https://github.com/NikiforovAll/claude-code-kanban
  3. None

Choose [1/2/3]:
```

**If user picks 1 (PlanVisualizer):**
1. Check Node.js version: `node --version`. If < 18 or node not found: warn "PlanVisualizer requires Node.js 18+. Skipping." Set `dashboard_mode: "none"`.
2. If switching from claude-code-kanban: clean up kanban hooks (run `npx claude-code-kanban --uninstall` if available, or manually remove hooks from `~/.claude/hooks/`).
3. Clone PlanVisualizer to a project-local directory (e.g., `.plan-visualizer/`). Pin to a known-good tag if available.
4. Run PlanVisualizer's install script.
5. Copy bridge script: `source/dashboard/telemetry-bridge.sh` -> project's `.claude/dashboard/telemetry-bridge.sh`.
6. Set `dashboard_mode: "plan-visualizer"` in `.claude/pipeline-config.json`.
7. Print: "Dashboard: PlanVisualizer installed. Run `node tools/generate-plan.js` to view."

**If user picks 2 (claude-code-kanban):**
1. Check npx availability: `command -v npx`. If not found: warn "claude-code-kanban requires npm/npx. Skipping." Set `dashboard_mode: "none"`.
2. If switching from PlanVisualizer: remove `.plan-visualizer/` directory and bridge script.
3. Run `npx claude-code-kanban --install` to register hooks.
4. Set `dashboard_mode: "claude-code-kanban"` in `.claude/pipeline-config.json`.
5. Print: "Dashboard: claude-code-kanban installed. Run `npx claude-code-kanban --open` to view."

**If user picks 3 (None):**
1. If switching from an existing dashboard: clean up old artifacts (same as switch logic above).
2. Set `dashboard_mode: "none"` in `.claude/pipeline-config.json`.
3. Print: "Dashboard: not enabled"

**Idempotency:** If `dashboard_mode` already matches the user's choice, skip mutation and announce: "Dashboard is already set to [choice]."

**Error handling:** If any install step fails (clone, npx, install script), log the error, set `dashboard_mode: "none"`, and continue setup. Print: "Dashboard install failed: [reason]. Skipping."

**Both dashboards detected:** If both `.plan-visualizer/` and claude-code-kanban hooks exist, force choice: "Both dashboards detected. Pick one or remove both."

**Summary update:** Add to the summary printout:
```
Dashboard: [PlanVisualizer | claude-code-kanban | not enabled]
```

**Acceptance criteria:**
- Step 6f block exists in SKILL.md, after Step 6e (Darwin), before Brain offer
- Menu shows 3 options with GitHub links
- PlanVisualizer path: Node.js check, clone, install, bridge copy, config flag
- claude-code-kanban path: npx check, install, config flag
- Switch path: old dashboard cleaned up before new installed
- Failure handling: install error sets config to "none", never blocks
- Summary line added
- Idempotency check present

**Estimated complexity:** Medium. One file modified, but the step logic is the most complex in the ADR (three install paths, switch logic, error handling).

---

### Step 3: Bridge Script (telemetry-bridge.sh)

**After this step, I can:** Run the bridge script and it generates a valid PIPELINE_PLAN.md from brain telemetry data (or from pipeline-state.md as fallback).

**Files to create:**
- `source/dashboard/telemetry-bridge.sh` -- template bridge script

**Bridge script design:**

The script is a Bash wrapper that:
1. Reads brain telemetry data via the brain HTTP API (if brain is configured and reachable).
2. Falls back to parsing `docs/pipeline/pipeline-state.md` if brain is unavailable.
3. Transforms the data into PlanVisualizer's expected PIPELINE_PLAN.md format.
4. Writes PIPELINE_PLAN.md to the project root (where PlanVisualizer expects it). **The bridge generates a complete PIPELINE_PLAN.md from all available telemetry data each time (full regeneration, not append).** Every invocation queries all T3/T2/T1 data and produces the full file from scratch. This avoids stale-data accumulation and keeps the bridge script stateless.
5. Optionally runs `node tools/generate-plan.js` to regenerate the dashboard HTML.

**Input sources (in priority order):**
1. Brain HTTP API: query T3 summaries for EPICs, T2 for Stories, T1 for Tasks.
2. pipeline-state.md: parse the progress table for unit names, agents, statuses.

**Output format (PIPELINE_PLAN.md):**

```markdown
# Pipeline Plan

## EPIC: {pipeline_id} ({sizing})

### Story: {work_unit_id}
- **Status:** {Done|In Progress|Blocked|To Do}
- **Agent:** {agent_name}
- **Rework:** {rework_cycles}

#### Tasks:
- [ ] {agent_name} {phase} -- {duration_ms}ms
```

The exact format must match what PlanVisualizer's `parse-release-plan.js` expects. The bridge reverse-engineers this from PlanVisualizer's parser source (read at implementation time, not assumed here).

**Fallback behavior:**
- Brain unavailable: use pipeline-state.md. Generate EPIC from feature name + date. Stories from progress table rows. No cost data, no duration data, no rework counts.
- pipeline-state.md empty: generate minimal valid file with "No pipeline data yet" placeholder.
- Node not found (cannot run generate-plan.js): write PIPELINE_PLAN.md but skip HTML regeneration. Log: "node not found -- PIPELINE_PLAN.md written but HTML not regenerated."

**Script parameters:**
- `--brain-url` (optional): brain HTTP API URL. Read from `.claude/brain-config.json` if not provided.
- `--pipeline-state` (optional): path to pipeline-state.md. Defaults to `docs/pipeline/pipeline-state.md`.
- `--output` (optional): path to write PIPELINE_PLAN.md. Defaults to `./PIPELINE_PLAN.md`.
- `--skip-generate` (optional): write markdown only, skip HTML regeneration.

**Acceptance criteria:**
- `source/dashboard/telemetry-bridge.sh` exists and is executable
- Script reads brain telemetry when available and produces valid PIPELINE_PLAN.md
- Script falls back to pipeline-state.md parsing when brain unavailable
- Script produces minimal valid PIPELINE_PLAN.md when no data exists
- Script exits 0 even when brain is unavailable or node is missing (non-blocking)
- Output format is parseable by PlanVisualizer's parse-release-plan.js

**Estimated complexity:** Medium. Single file creation, but the telemetry-to-markdown mapping is the architecturally interesting piece.

---

### Step 4: Post-Pipeline Wiring + Eva Announcement

**After this step, I can:** Complete a pipeline run with PlanVisualizer enabled and the dashboard is automatically regenerated after Ellis commits. Eva announces dashboard status at session boot.

**Files to modify:**
- `source/rules/pipeline-orchestration.md` -- add post-pipeline bridge section after Pattern Staleness Check
- `.claude/rules/pipeline-orchestration.md` -- installed copy (dual tree)
- `source/references/invocation-templates.md` -- add `dashboard-bridge` invocation template
- `.claude/references/invocation-templates.md` -- installed copy (dual tree)

**Post-pipeline bridge wiring (pipeline-orchestration.md):**

After the Pattern Staleness Check section, add:

```
### Dashboard Bridge (post-pipeline, PlanVisualizer only)

After the Pattern Staleness Check (and Darwin auto-trigger if applicable), if
`dashboard_mode` is set to `"plan-visualizer"` in `pipeline-config.json`, Eva runs
the bridge script:

1. Eva runs `.claude/dashboard/telemetry-bridge.sh` via Bash.
2. If the script succeeds: Eva logs "Dashboard updated -- PIPELINE_PLAN.md regenerated."
3. If the script fails: Eva logs "Dashboard update failed: [reason]. Pipeline complete." and continues.

Dashboard bridge failure is never a pipeline blocker.

When `dashboard_mode` is `"claude-code-kanban"` or `"none"`: skip this section entirely.
claude-code-kanban is passive (watches files in real-time) and requires no post-pipeline action.
```

**Eva boot announcement update:**

The existing boot sequence (default-persona.md step 6) needs a `dashboard_mode` line. However, default-persona.md is an always-loaded rule file that Cal cannot modify (enforce-paths.sh blocks Cal from `.claude/rules/`). Instead, the dashboard announcement is documented in pipeline-orchestration.md as a conditional boot step. Eva reads `dashboard_mode` from pipeline-config.json at boot and appends:
- `dashboard_mode: "plan-visualizer"` -> "Dashboard: PlanVisualizer"
- `dashboard_mode: "claude-code-kanban"` -> "Dashboard: claude-code-kanban"
- `dashboard_mode: "none"` or absent -> omit line

**Invocation template (dashboard-bridge):**

```xml
<template id="dashboard-bridge">

### Dashboard Bridge (Eva self-invocation via Bash)

Eva runs this after Ellis commit when `dashboard_mode: "plan-visualizer"`.
Not a subagent invocation -- Eva runs the bridge script directly via Bash.

<task>Run the telemetry bridge script to regenerate PIPELINE_PLAN.md for PlanVisualizer.</task>

<constraints>
- Run `.claude/dashboard/telemetry-bridge.sh` via Bash.
- If the script fails, log the error and continue. Never block the pipeline.
- This is a Bash command, not a subagent invocation.
</constraints>

<output>PIPELINE_PLAN.md written to project root. Dashboard HTML regenerated (if node available).</output>

</template>
```

**Acceptance criteria:**
- pipeline-orchestration.md contains Dashboard Bridge section after Pattern Staleness Check
- Both source/ and .claude/ copies are updated (dual tree)
- invocation-templates.md contains `dashboard-bridge` template in both copies
- Bridge runs only when `dashboard_mode: "plan-visualizer"` -- not for kanban or none
- Failure handling documented as non-blocking
- Eva boot announcement documented for dashboard status

**Estimated complexity:** Low. Four files modified (two pairs of dual-tree copies), additive sections only.

---

### Step 5: Enforcement Hook Bypass for /pipeline-setup

**After this step, I can:** Run /pipeline-setup on a project with existing enforcement hooks installed, and the setup process can write to `.claude/` paths without being blocked by its own hooks.

**Problem:** The enforcement hooks (enforce-paths.sh, enforce-sequencing.sh, enforce-git.sh) block writes to `.claude/` paths and restrict tool usage during active pipelines. When /pipeline-setup runs, it legitimately writes to `.claude/rules/`, `.claude/agents/`, `.claude/commands/`, `.claude/references/`, `.claude/hooks/`, and `.claude/pipeline-config.json`. On a fresh install there are no hooks yet, but on a re-install or update, the already-installed hooks block the setup process from updating the very files it needs to update.

**Solution:** An `ATELIER_SETUP_MODE` environment variable that each hook checks at the top. When `ATELIER_SETUP_MODE=1`, the hook exits 0 immediately (allow all). The variable is set by SKILL.md before its first write operation and is session-scoped (expires naturally when the Claude Code session ends -- no explicit unset needed).

**Files to modify:**
- `source/hooks/enforce-paths.sh` -- add bypass check after `set -euo pipefail` / before `INPUT=$(cat)`
- `source/hooks/enforce-sequencing.sh` -- add bypass check after `set -euo pipefail` / before `INPUT=$(cat)`
- `source/hooks/enforce-git.sh` -- add bypass check after `set -euo pipefail` / before `INPUT=$(cat)`
- `.claude/hooks/enforce-paths.sh` -- installed copy (dual tree)
- `.claude/hooks/enforce-sequencing.sh` -- installed copy (dual tree)
- `.claude/hooks/enforce-git.sh` -- installed copy (dual tree)
- `skills/pipeline-setup/SKILL.md` -- add `ATELIER_SETUP_MODE=1` export before Step 3 (Install Files), document session scope

**Hook modification (identical one-liner in each hook, after `set -euo pipefail`):**
```bash
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
```

This line:
1. Uses `${ATELIER_SETUP_MODE:-}` to avoid `set -u` (unbound variable) errors when the variable is not set.
2. Checks for exact string match `"1"` -- not truthy, not non-empty, exactly `"1"`.
3. Exits 0 (allow) immediately, skipping all subsequent checks.

**SKILL.md modification:**

Before Step 3 (Install Files), add a setup-mode activation note:

```
**Setup mode activation:** Before writing any files, export `ATELIER_SETUP_MODE=1`
to bypass enforcement hooks that may already be installed from a previous setup.
This variable is session-scoped and expires naturally when the session ends.

```bash
export ATELIER_SETUP_MODE=1
```
```

This is placed after Step 2 (Read Templates) and before Step 3 (Install Files) because Step 2 is read-only (no writes) and Step 3 is the first step that writes files.

**Acceptance criteria:**
- All three source/ hook scripts contain the bypass line as the first executable line after `set -euo pipefail`
- All three .claude/ hook scripts contain the identical bypass line (dual tree parity)
- SKILL.md documents `ATELIER_SETUP_MODE=1` export before Step 3
- SKILL.md documents that the variable is session-scoped
- When `ATELIER_SETUP_MODE=1`, each hook exits 0 without reading stdin or parsing JSON
- When `ATELIER_SETUP_MODE` is unset or any value other than `"1"`, hooks behave identically to current behavior
- No other hook files are modified (warn-dor-dod.sh, pre-compact.sh, enforce-pipeline-activation.sh are unaffected)

**Estimated complexity:** Low. Six files get a one-line addition, one file gets a documentation paragraph. No logic changes to existing hook behavior.

---

## Comprehensive Test Specification

### Step 1 Tests: quality-gate.sh Cleanup + Config Flag

| ID | Category | Description |
|----|----------|-------------|
| T-0018-001 | Happy | SKILL.md contains a Step 0 block positioned before Step 1 (Gather Project Information) |
| T-0018-002 | Happy | Step 0 detects `.claude/hooks/quality-gate.sh` and deletes it when present |
| T-0018-003 | Happy | Step 0 detects quality-gate.sh entry in `.claude/settings.json` hooks and removes it |
| T-0018-004 | Happy | Step 0 prints "Removed deprecated quality-gate.sh (see retro lesson #003)" when either artifact is found |
| T-0018-005 | Happy | `source/pipeline/pipeline-config.json` contains `"dashboard_mode": "none"` |
| T-0018-006 | Happy | `.claude/pipeline-config.json` contains `"dashboard_mode": "none"` |
| T-0018-007 | Happy | Both config files remain valid JSON after modification (`jq . file` exits 0) |
| T-0018-008 | Boundary | quality-gate.sh file exists but settings.json entry already removed: only file is deleted, no settings.json error |
| T-0018-009 | Boundary | settings.json has quality-gate.sh entry but file does not exist: only entry is removed, no file-not-found error |
| T-0018-010 | Boundary | Neither quality-gate.sh file nor settings.json entry found: silent no-op, no output printed |
| T-0018-011 | Boundary | Both quality-gate.sh file and settings.json entry found: both removed, single notice printed (not two) |
| T-0018-011b | Boundary | Removing quality-gate.sh entry that is the sole hook for its event type removes the event type key entirely (no empty hooks array left in settings.json) |
| T-0018-012 | Failure | settings.json is malformed JSON: Step 0 logs warning and continues setup (does not block) |
| T-0018-013 | Regression | No existing fields in either config file are removed or renamed after adding `dashboard_mode` |
| T-0018-014 | Regression | `darwin_enabled`, `sentinel_enabled`, `deps_agent_enabled` fields are unchanged in both config files |
| T-0018-015 | Regression | Step 1 (Gather Project Information) is unchanged after Step 0 insertion |
| T-0018-016 | Regression | Removal of settings.json hook entry does not affect other hook entries (enforce-paths, enforce-sequencing, etc.) |

### Step 2 Tests: Dashboard Setup Step 6f

| ID | Category | Description |
|----|----------|-------------|
| T-0018-017 | Happy | SKILL.md contains a `### Step 6f` block positioned after Step 6e (Darwin) and before Brain setup offer |
| T-0018-018 | Happy | Step 6f menu shows 3 options with descriptions and GitHub links for PlanVisualizer and claude-code-kanban |
| T-0018-019 | Happy | Choosing PlanVisualizer sets `dashboard_mode: "plan-visualizer"` in pipeline-config.json |
| T-0018-020 | Happy | Choosing claude-code-kanban sets `dashboard_mode: "claude-code-kanban"` in pipeline-config.json |
| T-0018-021 | Happy | Choosing None sets `dashboard_mode: "none"` in pipeline-config.json |
| T-0018-022 | Happy | PlanVisualizer install path: clones repo, runs install script, copies bridge script |
| T-0018-023 | Happy | claude-code-kanban install path: runs `npx claude-code-kanban --install` |
| T-0018-024 | Happy | Summary printout includes "Dashboard: [PlanVisualizer / claude-code-kanban / not enabled]" line |
| T-0018-025 | Failure | PlanVisualizer chosen but Node.js < 18: warns "requires Node.js 18+. Skipping.", sets `dashboard_mode: "none"` |
| T-0018-025b | Failure | PlanVisualizer chosen but `node` command not found: warns "requires Node.js 18+. Skipping.", sets `dashboard_mode: "none"` (distinct code path from version check -- `command -v node` fails before `node --version` runs) |
| T-0018-026 | Failure | claude-code-kanban chosen but npx not found: warns "requires npm/npx. Skipping.", sets `dashboard_mode: "none"` |
| T-0018-027 | Failure | PlanVisualizer clone fails (network error): logs error, sets `dashboard_mode: "none"`, continues setup |
| T-0018-028 | Failure | PlanVisualizer install script fails: logs error, sets `dashboard_mode: "none"`, continues setup |
| T-0018-029 | Failure | npx claude-code-kanban --install fails: logs error, sets `dashboard_mode: "none"`, continues setup |
| T-0018-029b | Failure | Switch from claude-code-kanban to PlanVisualizer but `npx claude-code-kanban --uninstall` fails: logs uninstall error, falls back to manual hook file removal from `~/.claude/hooks/`, continues with PlanVisualizer install |
| T-0018-030 | Boundary | Idempotency: re-running with same `dashboard_mode` choice is a no-op, announces "Dashboard is already set to [choice]" |
| T-0018-031 | Boundary | Switch from PlanVisualizer to claude-code-kanban: PlanVisualizer artifacts cleaned up before kanban installed |
| T-0018-032 | Boundary | Switch from claude-code-kanban to PlanVisualizer: kanban hooks cleaned up before PlanVisualizer installed |
| T-0018-033 | Boundary | Switch from either dashboard to None: all dashboard artifacts cleaned up |
| T-0018-034 | Boundary | Both dashboards detected (manual tampering): forces choice, announces conflict |
| T-0018-035 | Boundary | Brain not configured + PlanVisualizer chosen: install succeeds, bridge falls back to pipeline-state.md |
| T-0018-036 | Regression | Step 6e (Darwin) block is unchanged after Step 6f insertion |
| T-0018-037 | Regression | Brain setup offer remains positioned after Step 6f |
| T-0018-038 | Regression | Step 6a-6d blocks are unchanged after Step 6f insertion |
| T-0018-038b | Regression | Brain setup offer intro paragraph references "After the Dashboard offer" (not "After the Darwin offer") since Step 6f is now positioned between Darwin and Brain |

### Step 3 Tests: Bridge Script

| ID | Category | Description |
|----|----------|-------------|
| T-0018-039 | Happy | `source/dashboard/telemetry-bridge.sh` exists and is executable (chmod +x) |
| T-0018-040 | Happy | Bridge script reads brain telemetry and generates PIPELINE_PLAN.md with EPIC/Story/Task structure |
| T-0018-041 | Happy | Bridge script maps T3 pipeline_id to EPIC title |
| T-0018-042 | Happy | Bridge script maps T2 work_unit_id to Story title with correct status |
| T-0018-043 | Happy | Bridge script maps T1 agent invocations to Tasks with duration |
| T-0018-043b | Happy | Bridge script maps T2 rework_cycles to Story metadata field (displays per-unit rework count) |
| T-0018-043c | Happy | Bridge script maps T3 rework_rate to EPIC summary metric field (displays aggregate rework rate) |
| T-0018-044 | Happy | Bridge script includes cost data from T3 total_cost_usd |
| T-0018-045 | Happy | Bridge script output is parseable by PlanVisualizer's parse-release-plan.js |
| T-0018-046 | Happy | Bridge script falls back to pipeline-state.md when brain is unavailable and produces valid output |
| T-0018-047 | Happy | Bridge script runs `node tools/generate-plan.js` when node is available |
| T-0018-048 | Failure | Brain unavailable AND pipeline-state.md empty: generates minimal PIPELINE_PLAN.md with placeholder |
| T-0018-049 | Failure | Node not found: writes PIPELINE_PLAN.md but skips HTML regeneration, logs message |
| T-0018-050 | Failure | Brain HTTP API returns error: falls back to pipeline-state.md without crashing |
| T-0018-051 | Failure | Malformed brain response: falls back to pipeline-state.md, logs parse error |
| T-0018-051b | Failure | Bridge script cannot write to output path (permission denied on PIPELINE_PLAN.md): exits 0, logs "Cannot write PIPELINE_PLAN.md: permission denied" |
| T-0018-051c | Failure | Brain HTTP API timeout (connection hangs, distinct from refused/unavailable): bridge times out after configured threshold, falls back to pipeline-state.md, logs "Brain API timeout" |
| T-0018-052 | Boundary | Bridge script accepts --brain-url, --pipeline-state, --output, --skip-generate flags |
| T-0018-053 | Boundary | Bridge script exits 0 in all failure cases (non-blocking) |
| T-0018-054 | Boundary | Multiple pipeline runs: bridge regenerates complete PIPELINE_PLAN.md from all available telemetry data (full regeneration, not append). Running bridge twice with the same data produces identical output. |
| T-0018-055 | Security | Bridge script does not expose brain credentials in output or error messages |

### Step 4 Tests: Post-Pipeline Wiring + Eva Announcement

| ID | Category | Description |
|----|----------|-------------|
| T-0018-056 | Happy | `source/rules/pipeline-orchestration.md` contains "Dashboard Bridge" section after Pattern Staleness Check |
| T-0018-057 | Happy | `.claude/rules/pipeline-orchestration.md` contains identical Dashboard Bridge section (dual tree parity) |
| T-0018-058 | Happy | Dashboard Bridge runs only when `dashboard_mode: "plan-visualizer"` in pipeline-config.json |
| T-0018-059 | Happy | Dashboard Bridge is documented as non-blocking (failure logged, pipeline continues) |
| T-0018-060 | Happy | `source/references/invocation-templates.md` contains `<template id="dashboard-bridge">` block |
| T-0018-061 | Happy | `.claude/references/invocation-templates.md` contains identical template (dual tree parity) |
| T-0018-062 | Happy | Eva boot announcement includes dashboard status line when `dashboard_mode` is not "none" |
| T-0018-063 | Failure | Dashboard Bridge skipped when `dashboard_mode: "claude-code-kanban"` (kanban is passive, no post-pipeline action) |
| T-0018-064 | Failure | Dashboard Bridge skipped when `dashboard_mode: "none"` or field absent |
| T-0018-065 | Boundary | Dashboard Bridge section positioned correctly: after Pattern Staleness, before pipeline completion |
| T-0018-066 | Boundary | Eva boot omits dashboard line when `dashboard_mode: "none"` or field absent |
| T-0018-067 | Regression | Existing pipeline-orchestration.md sections (telemetry, Darwin, Pattern Staleness) unchanged |
| T-0018-068 | Regression | Existing invocation templates unchanged after dashboard-bridge addition |
| T-0018-069 | Regression | Eva boot sequence steps 1-6 are unchanged except for the conditional dashboard line |

### Step 5 Tests: Enforcement Hook Bypass for /pipeline-setup

| ID | Category | Description |
|----|----------|-------------|
| T-0018-070 | Happy | `source/hooks/enforce-paths.sh` contains `[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0` as the first executable line after `set -euo pipefail` |
| T-0018-071 | Happy | `source/hooks/enforce-sequencing.sh` contains the identical bypass line after `set -euo pipefail` |
| T-0018-072 | Happy | `source/hooks/enforce-git.sh` contains the identical bypass line after `set -euo pipefail` |
| T-0018-073 | Happy | `.claude/hooks/enforce-paths.sh` contains the identical bypass line (dual tree parity with source/) |
| T-0018-074 | Happy | `.claude/hooks/enforce-sequencing.sh` contains the identical bypass line (dual tree parity) |
| T-0018-075 | Happy | `.claude/hooks/enforce-git.sh` contains the identical bypass line (dual tree parity) |
| T-0018-076 | Happy | SKILL.md contains `export ATELIER_SETUP_MODE=1` instruction positioned before Step 3 (Install Files) and after Step 2 (Read Templates) |
| T-0018-077 | Happy | SKILL.md documents that `ATELIER_SETUP_MODE` is session-scoped (expires naturally) |
| T-0018-078 | Happy | When `ATELIER_SETUP_MODE=1`, enforce-paths.sh exits 0 without reading stdin (`INPUT=$(cat)` is never reached) |
| T-0018-079 | Happy | When `ATELIER_SETUP_MODE=1`, enforce-sequencing.sh exits 0 without reading stdin |
| T-0018-080 | Happy | When `ATELIER_SETUP_MODE=1`, enforce-git.sh exits 0 without reading stdin |
| T-0018-081 | Failure | When `ATELIER_SETUP_MODE` is unset, enforce-paths.sh proceeds to normal enforcement (existing behavior unchanged) |
| T-0018-082 | Failure | When `ATELIER_SETUP_MODE=""` (empty string), enforce-paths.sh proceeds to normal enforcement (empty is not "1") |
| T-0018-083 | Failure | When `ATELIER_SETUP_MODE=true`, enforce-paths.sh proceeds to normal enforcement (truthy is not "1") |
| T-0018-084 | Failure | When `ATELIER_SETUP_MODE=0`, enforce-paths.sh proceeds to normal enforcement ("0" is not "1") |
| T-0018-085 | Failure | When `ATELIER_SETUP_MODE=2`, enforce-sequencing.sh proceeds to normal enforcement (only exact "1" triggers bypass) |
| T-0018-086 | Failure | When `ATELIER_SETUP_MODE=1 ` (trailing space), enforce-git.sh proceeds to normal enforcement (no trimming) |
| T-0018-087 | Boundary | Bypass line uses `${ATELIER_SETUP_MODE:-}` syntax (not `$ATELIER_SETUP_MODE`) to avoid `set -u` unbound variable error when the variable is not set |
| T-0018-088 | Boundary | The bypass line is positioned BEFORE `INPUT=$(cat)` in all three hooks (stdin is not consumed when bypassing, avoiding a blocked read on empty stdin) |
| T-0018-089 | Security | `ATELIER_SETUP_MODE=1` cannot be set by a subagent -- subagents run in their own process context and cannot modify the parent shell's environment |
| T-0018-090 | Security | A user manually setting `ATELIER_SETUP_MODE=1` in their shell disables all three hooks -- this is intentional (user has full control over their own hooks) |
| T-0018-091 | Regression | `warn-dor-dod.sh` does NOT contain the bypass line (SubagentStop hooks do not block writes) |
| T-0018-092 | Regression | `pre-compact.sh` does NOT contain the bypass line (PreCompact hook does not block writes) |
| T-0018-093 | Regression | `enforce-pipeline-activation.sh` does NOT contain the bypass line (pipeline-activation blocks Agent invocations, not writes -- setup does not invoke subagents) |
| T-0018-094 | Regression | All existing enforcement logic in each hook is unchanged after the bypass line addition (no lines removed, no lines modified, no reordering) |
| T-0018-095 | Regression | SKILL.md Steps 1-6e and Steps 7 are unchanged after the setup-mode documentation addition |

### Step N Telemetry

**Step 1 (Cleanup + Config):**
Telemetry: When quality-gate.sh is found and removed, /pipeline-setup prints "Removed deprecated quality-gate.sh (see retro lesson #003)." Trigger: every /pipeline-setup invocation where the deprecated hook exists. Absence means: Step 0 is not running or the detection logic is broken.

Telemetry: `jq .dashboard_mode .claude/pipeline-config.json` returns `"none"` (default). Trigger: after Step 1 runs. Absence means: config field was not written.

**Step 2 (Setup Step 6f):**
Telemetry: After /pipeline-setup Step 6f acceptance, `jq .dashboard_mode .claude/pipeline-config.json` returns the chosen value. Trigger: user completes Step 6f. Absence means: Step 6f failed to write config.

Telemetry: Summary printout includes "Dashboard: [value]" line. Trigger: every /pipeline-setup completion. Absence means: summary was not updated.

**Step 3 (Bridge Script):**
Telemetry: Bridge script logs "PIPELINE_PLAN.md written: {path}" on success, or "Bridge failed: {reason}" on failure. Trigger: script execution. Absence means: script is not running or is crashing silently.

**Step 4 (Post-Pipeline Wiring):**
Telemetry: Eva logs "Dashboard updated -- PIPELINE_PLAN.md regenerated." after successful bridge execution. Trigger: pipeline end when `dashboard_mode: "plan-visualizer"`. Absence means: post-pipeline wiring section missing from pipeline-orchestration.md or Eva is not reading the dashboard_mode config.

Telemetry: Eva boot announcement includes "Dashboard: PlanVisualizer" or "Dashboard: claude-code-kanban" line. Trigger: session boot when dashboard is configured. Absence means: boot announcement logic not updated.

**Step 5 (Enforcement Hook Bypass):**
Telemetry: Each hook logs nothing and exits 0 when `ATELIER_SETUP_MODE=1`. Trigger: /pipeline-setup invocation on a project with hooks already installed. Absence means: bypass line is missing or not being evaluated (the symptom would be /pipeline-setup failing with BLOCKED errors when updating an existing installation).

---

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `source/dashboard/telemetry-bridge.sh` | Bash script: reads brain HTTP API or pipeline-state.md, writes PIPELINE_PLAN.md | Eva post-pipeline wiring (pipeline-orchestration.md), /pipeline-setup Step 6f (copies to project) | Step 3 |
| `dashboard_mode` config flag (pipeline-config.json) | String JSON field: "plan-visualizer" / "claude-code-kanban" / "none" | SKILL.md Step 6f install gate, Eva post-pipeline bridge (Step 4), Eva boot announcement (Step 4) | Step 1 |
| `dashboard-bridge` invocation template | XML `<template>` with `<task>`, `<constraints>`, `<output>` | Eva when running bridge after Ellis commit | Step 4 |
| Step 0 cleanup logic (SKILL.md) | Procedural: detect + remove quality-gate.sh file and settings.json entry | Every /pipeline-setup invocation (unconditional) | Step 1 |
| PIPELINE_PLAN.md (bridge output) | Markdown in PlanVisualizer's expected format: EPICs, Stories, Tasks | PlanVisualizer's parse-release-plan.js (external tool) | Step 3 |
| Dashboard Bridge section (pipeline-orchestration.md) | Procedural: Eva's post-pipeline behavior when `dashboard_mode: "plan-visualizer"` | Eva at pipeline end | Step 4 |
| `ATELIER_SETUP_MODE` bypass (enforce-paths.sh, enforce-sequencing.sh, enforce-git.sh) | One-line env var check: `[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0` | SKILL.md `export ATELIER_SETUP_MODE=1` before Step 3 writes | Step 5 |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `source/dashboard/telemetry-bridge.sh` | Bridge script template | /pipeline-setup copies to `.claude/dashboard/telemetry-bridge.sh`; Eva runs at pipeline end | Step 3, Step 2, Step 4 |
| `dashboard_mode` (pipeline-config.json) | String: "plan-visualizer"/"claude-code-kanban"/"none" | SKILL.md Step 6f (install gate), Eva post-pipeline (bridge conditional), Eva boot (announcement) | Step 1 |
| `dashboard-bridge` template (invocation-templates.md) | Eva self-invocation template | Eva uses to run bridge script after Ellis commit | Step 4 |
| Step 0 cleanup (SKILL.md) | Detection + removal | Consumed implicitly by every /pipeline-setup run | Step 1 |
| PIPELINE_PLAN.md | PlanVisualizer markdown format | PlanVisualizer's parse-release-plan.js (external) | Step 3 |

| `ATELIER_SETUP_MODE` bypass (3 hook scripts) | Env var check, exit 0 on match | SKILL.md sets the env var before file writes | Step 5 |

No orphan producers. Every artifact created in Steps 1-5 has a consumer in the same or later step.

---

## Data Sensitivity

No data stores involved. The bridge script reads telemetry from the brain HTTP API (metrics data: cost, duration, agent names, pipeline IDs) and pipeline-state.md (feature names, agent statuses). None of this data is sensitive. PIPELINE_PLAN.md is written to the project directory and committed to git (same visibility as pipeline-state.md). No fields require `auth-only` tagging.

The brain HTTP API URL (from brain-config.json) is read by the bridge script but not written to PIPELINE_PLAN.md or any output file.

---

## Notes for Colby

**Dual tree discipline:** pipeline-config.json exists in both `source/pipeline/` and `.claude/`. Both must be updated in Step 1. pipeline-orchestration.md exists in both `source/rules/` and `.claude/rules/`. Both must be updated in Step 4. invocation-templates.md exists in both `source/references/` and `.claude/references/`. Both must be updated in Step 4.

**Config field ordering:** The existing convention ends at `darwin_enabled`. Add `"dashboard_mode": "none"` after `darwin_enabled` in both config files.

**SKILL.md Step 0 positioning:** Step 0 runs before Step 1 (Gather Project Information). It is the very first action in /pipeline-setup. It has no user prompt -- it is silent unless it finds artifacts to clean up. This means every /pipeline-setup invocation benefits from cleanup, even if the user is just re-running to change branching strategy.

**SKILL.md Step 6f positioning:** Insert after the Step 6e (Darwin) block and before the paragraph starting "After the Darwin offer (whether user said yes or no), ask the user:" which is the Brain setup offer. The Brain offer must remain the last item. Update the paragraph intro to read "After the Dashboard offer" instead of "After the Darwin offer" since Step 6f is now between them.

**quality-gate.sh settings.json cleanup:** The deprecated hook would have been registered as a Stop or SubagentStop hook. The exact event type may vary by installation version. When scanning settings.json, check ALL hook event types for any entry containing "quality-gate" in the command string. Use `jq` to filter and remove matching entries. Handle the case where removing the last hook in an event type leaves an empty array.

**Bridge script is Bash, not Node:** The bridge script is a Bash shell script that uses `curl` (for brain HTTP API) and text processing to generate markdown. It only invokes Node at the end to run PlanVisualizer's `generate-plan.js`. This avoids adding a Node dependency to the bridge itself (the user may not have Node, and the bridge should still write PIPELINE_PLAN.md).

**PlanVisualizer format reverse-engineering:** At implementation time, Colby must read PlanVisualizer's `parse-release-plan.js` to determine the exact markdown format expected. Do not assume the format shown in this ADR is correct -- verify against the actual parser. The format in the Data Flow section is illustrative, not prescriptive.

**claude-code-kanban hooks go to user-level (~/.claude/hooks/), not project-level:** This is the one piece of the integration that lives outside the project directory. Document this in the SKILL.md Step 6f description so users understand the scope. /pipeline-uninstall (project-scoped) cannot clean these up -- note this limitation.

**Brain context from prior pipelines:** The brain research insights (ecb6afe9 for PlanVisualizer, c0cb471f for claude-code-kanban) contain detailed analysis of both tools' data models and installation patterns. These should be injected into Colby's invocation context when building Steps 2 and 3.

**Eva's boot announcement for dashboard:** The dashboard announcement is documented in pipeline-orchestration.md (Step 4) rather than modifying default-persona.md. This is because default-persona.md is an always-loaded rule file that already contains a complex boot sequence. Adding another conditional line is better done in the operations file (which Eva loads at boot when reading pipeline-state.md) to keep the boot sequence maintainable.

**ATELIER_SETUP_MODE bypass placement:** The bypass line must be the FIRST executable line after `set -euo pipefail` in each hook -- specifically BEFORE `INPUT=$(cat)`. This is critical because `INPUT=$(cat)` reads from stdin, which blocks if stdin is empty. During normal hook execution, Claude Code pipes JSON to stdin. But if the bypass exits before reading stdin, there is no hang risk. The line is identical across all three hooks: `[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0`.

**Dual tree for hooks:** The `.claude/hooks/` copies must be identical to `source/hooks/` copies. After modifying source/, diff to verify parity. The simplest approach: modify source/ first, then copy to .claude/hooks/.

**SKILL.md setup-mode export:** The `export ATELIER_SETUP_MODE=1` instruction goes between Step 2 (Read Templates, read-only) and Step 3 (Install Files, first write). This ensures the variable is set before any tool call that might trigger a hook. The export is documented as session-scoped -- no `unset` is needed because the variable disappears when the session ends.

**Why not bypass enforce-pipeline-activation.sh:** This hook only fires on the Agent tool for colby/ellis subagent types. /pipeline-setup does not invoke Colby or Ellis as subagents, so the hook never triggers during setup. Adding an unnecessary bypass would widen the attack surface for no benefit.

---

## DoD: Verification

| # | Requirement | ADR Step | Evidence |
|---|-------------|----------|----------|
| R1 | Two mutually exclusive dashboard options during /pipeline-setup | Step 2 | Step 6f menu with 3 choices, T-0018-017/018 |
| R2 | PlanVisualizer static dashboard integration | Step 2, Step 3 | Install path + bridge script, T-0018-022/039 |
| R3 | claude-code-kanban real-time dashboard integration | Step 2 | Install path via npx, T-0018-023 |
| R4 | Setup menu with 3 options and GitHub links | Step 2 | Menu text in Step 6f, T-0018-018 |
| R5 | Config flag `dashboard_mode` in pipeline-config.json | Step 1 | Both files updated, T-0018-005/006 |
| R6 | PlanVisualizer bridge script | Step 3 | telemetry-bridge.sh exists, T-0018-039/045 |
| R7 | claude-code-kanban npx install | Step 2 | Install path, T-0018-023 |
| R8 | No source modification to either tool | All | Design constraint -- we feed data, not fork |
| R9 | quality-gate.sh auto-removed from hooks directory | Step 1 | Step 0 cleanup, T-0018-002 |
| R10 | quality-gate.sh registration removed from settings.json | Step 1 | Step 0 cleanup, T-0018-003 |
| R11 | One-line notice on cleanup | Step 1 | Step 0 prints message, T-0018-004 |
| R12 | Re-running with different dashboard cleans up old choice | Step 2 | Switch logic, T-0018-031/032/033 |
| R13 | Dashboard failure never blocks setup or pipeline | Step 2, Step 4 | Error handling sets "none" (Step 2), bridge failure logged (Step 4), T-0018-027/028/029/059 |
| R14 | Idempotency on re-run | Step 2 | Idempotency check, T-0018-030 |
| R15 | Bridge fallback to pipeline-state.md | Step 3 | Fallback path, T-0018-046 |
| R16 | Edge cases handled | Step 1, Step 2, Step 3 | All spec edge cases covered in test spec |
| R17 | Eva post-pipeline bridge wiring | Step 4 | pipeline-orchestration.md section, T-0018-056/058 |
| R18 | Enforcement hooks do not block /pipeline-setup writes to .claude/ | Step 5 | ATELIER_SETUP_MODE bypass in 3 hooks + SKILL.md export, T-0018-070 through T-0018-095 |

**Architectural decisions not in the spec:**
- Step 0 (quality-gate.sh cleanup) runs unconditionally at the start of every /pipeline-setup, not as a separate step at the end. Reason: cleanup should happen as early as possible, before any hooks are registered, to prevent the deprecated hook from interfering with the setup process itself.
- Bridge script is Bash (not Node.js). Reason: avoids a hard dependency on Node for the bridge, which should work even when the user has a broken Node installation (the bridge writes markdown, not HTML).
- Dashboard announcement lives in pipeline-orchestration.md rather than default-persona.md. Reason: keeps the always-loaded boot sequence lean. The operations file loads automatically when Eva reads pipeline state.
- The `dashboard-bridge` invocation template is for Eva's self-reference (Bash command), not a subagent invocation. Reason: the bridge is a simple script execution, not a task requiring a dedicated agent context window.
- Enforcement hook bypass uses an environment variable (`ATELIER_SETUP_MODE=1`) rather than a file-based flag or hook argument. Reason: env vars are session-scoped by default (no cleanup needed), cannot be set by subagents (process isolation), and require only a one-line check in each hook. The exact-match check (`= "1"`, not truthy) prevents accidental activation.

**Rejected alternatives:**
- Single dashboard (PlanVisualizer only) rejected: ignores the real-time observation use case that claude-code-kanban uniquely serves.
- Both dashboards simultaneously rejected: hook collision risk and maintenance burden outweigh marginal benefit.
- Custom dashboard rejected: months of UI work for a feature two existing tools already solve.

**Technical constraints discovered:**
- claude-code-kanban hooks install to ~/.claude/hooks/ (user-level), which is outside /pipeline-uninstall's project-level scope. This limitation is documented.
- PlanVisualizer's markdown format is undocumented. The bridge script must reverse-engineer the format from `parse-release-plan.js` at implementation time.
- enforce-paths.sh does not need changes -- the bridge script is run by Eva via Bash, not by a subagent with Write access. PIPELINE_PLAN.md is written by the script process, not by a Claude Code tool call.
- The existing SKILL.md Step 6 summary printout needs a new line added, and the Brain setup offer's intro paragraph needs rewording (from "After the Darwin offer" to "After the Dashboard offer").
- Only 3 of 7 hooks need the ATELIER_SETUP_MODE bypass: enforce-paths.sh (blocks Write/Edit), enforce-sequencing.sh (blocks Agent), enforce-git.sh (blocks Bash git ops). The remaining hooks (warn-dor-dod.sh, pre-compact.sh, enforce-pipeline-activation.sh) either do not block writes or only fire on events that /pipeline-setup does not trigger.

---

ADR saved to `docs/architecture/ADR-0018-dashboard-integration.md`. 5 steps, 103 total tests. Next: Roz reviews the test spec.
