# ADR-0010: Agent Teams -- Experimental Opt-In Support for Parallel Wave Execution

## Status

Proposed

## DoR: Requirements Extracted

| # | Requirement | Source | Notes |
|---|-------------|--------|-------|
| R1 | Agent Teams is EXPERIMENTAL and OPT-IN -- gated behind env var `CLAUDE_AGENT_TEAMS=1` and a `pipeline-config.json` flag `agent_teams_enabled` | context-brief.md | Two gates: env var (Claude Code feature) + config flag (pipeline-level) |
| R2 | Eva acts as Team Lead; Colby instances run as Teammates in worktrees | brain-context (roadmap item #13) | Eva coordinates via shared task list, Colby instances execute build units |
| R3 | Pipeline must work identically when Agent Teams is disabled -- zero behavioral change | constraints | Fallback to current sequential subagent invocation |
| R4 | All changes target `source/` and `skills/` directories only | context-brief.md, constraints | Not `.claude/` -- dual tree convention |
| R5 | This is a non-code ADR -- changes are to persona files, rules, config templates, setup skill | context-brief.md | Skip Roz test spec/authoring; Colby implements, Roz verifies against ADR |
| R6 | Shared task list via TaskCreate/TaskUpdate/TaskGet for coordination | context-brief.md (Claude Code Agent Teams docs) | Eva creates tasks, teammates update them |
| R7 | TaskCreated/TaskCompleted hooks fire on the Team Lead (Eva) | context-brief.md (Claude Code Agent Teams docs) | Eva can react to teammate completion events |
| R8 | Each teammate gets its own worktree (isolated git copy) | context-brief.md (Claude Code Agent Teams docs) | Aligns with existing worktree integration rules |
| R9 | Behavioral constraints need mechanical enforcement via hooks | brain-context (retro lesson), MEMORY.md | Teammates in worktrees still need `enforce-paths.sh` and `enforce-sequencing.sh` |
| R10 | Subagents do not inherit parent system prompt | brain-context | Teammates will need explicit constraints in their invocation; however, `.claude/` files ARE loaded per-worktree |
| R11 | Setup asks user about Agent Teams during `/pipeline-setup`, warns experimental | context-brief.md | After Sentinel opt-in, before brain setup |
| R12 | Wave execution currently describes parallel execution conceptually but uses sequential subagent invocation; Agent Teams enables true parallel execution | pipeline-operations.md `<operations id="wave-execution">` | Existing wave grouping algorithm is preserved; execution backend changes |
| R13 | Existing worktree integration rules (git merge, one merge at a time, test suite between merges) must be preserved | pipeline-operations.md `<operations id="worktree-rules">` | Agent Teams worktrees follow same rules |
| R14 | `maxTurns` frontmatter is the only hard limit on runaway iterations for subagents | brain-context | Teammates need explicit `maxTurns` to prevent runaway execution |

### Retro Risks

| Lesson | Risk to this feature | Mitigation |
|--------|---------------------|------------|
| #003 (Stop hook race condition) | TaskCompleted hooks fire on Eva per-teammate; multiple concurrent completions could cause race conditions in state updates | Eva processes TaskCompleted events sequentially (queue, not parallel). State updates to `pipeline-state.md` are serialized. |
| #004 (Hung process retry loop) | Teammates in worktrees could hang on builds, consuming resources indefinitely | Teammate invocations include explicit `maxTurns` limit. Eva monitors task durations; if no TaskCompleted within a reasonable timeframe, Eva does not retry -- she reports the stuck teammate. |
| Behavioral constraints ignored (brain lesson) | Teammates might bypass path restrictions if running in isolated worktrees | Hooks are installed per-project in `.claude/hooks/` and `.claude/settings.json`. Worktrees share `.claude/` via the git worktree mechanism (it links to the main repo's `.claude/`). Hooks remain active. |
| Subagents don't inherit parent prompt (brain lesson) | Teammates are separate Claude Code instances, not subagents -- they load their own `.claude/rules/` and `.claude/agents/` from the worktree. However, Eva's invocation context (brain-context, constraints, specific ADR step) must be communicated via the task description. | Task descriptions carry structured context. Teammate persona files include explicit constraints. |
| #005 (Frontend wiring omission) | Parallel execution exacerbates cross-unit wiring gaps -- teammates cannot see each other's output shapes | Eva's post-wave merge + Roz final sweep + Poirot blind review catch wiring gaps. The review juncture is unchanged. Contract shapes documented in ADR steps remain the wiring contract. |

## Context

The pipeline currently executes wave units sequentially: Eva invokes one Colby subagent at a time, waits for completion, runs Roz QA, then moves to the next unit. The wave execution section of `pipeline-operations.md` describes grouping independent steps into waves, but execution within a wave is sequential because Claude Code's Agent tool creates one subagent at a time in the current thread.

Claude Code's Agent Teams feature (experimental, requires `CLAUDE_AGENT_TEAMS=1` env var) introduces a Team Lead / Teammate model where the main Claude Code instance (Team Lead) coordinates multiple Teammate instances, each running in its own git worktree. Teammates share a task list (TaskCreate/TaskUpdate/TaskGet) and can send peer-to-peer messages. The Team Lead receives TaskCreated and TaskCompleted hook events.

This maps naturally to the pipeline's existing architecture: Eva is already the central orchestrator who creates tasks, tracks state, and coordinates agents. Colby instances building independent ADR steps in parallel worktrees is exactly the wave execution model the pipeline describes but cannot currently execute.

The feature is experimental because Agent Teams itself is experimental in Claude Code. The pipeline must degrade gracefully: when Agent Teams is unavailable (env var unset, config flag false, or runtime detection fails), Eva falls back to the current sequential subagent model with zero behavioral change.

### Spec Challenge

**The spec assumes** that Claude Code's Agent Teams feature provides worktree-isolated Teammate instances that share the project's `.claude/` directory (hooks, settings, rules, agent personas). If this is wrong (because worktrees do not share `.claude/` or because hooks do not fire in worktree contexts), the design fails because teammates would lack enforcement hooks and agent personas. **Are we confident?** Partially. Git worktrees share the `.git` directory but `.claude/` is a regular directory at the project root -- its availability in worktrees depends on whether Claude Code copies or symlinks project configuration to worktrees. The opt-in flow must validate this at setup time. The experimental warning covers this risk.

**SPOF:** Eva's TaskCompleted event processing loop. **Failure mode:** If Eva fails to process a TaskCompleted event (context overflow, crash, hook error), the teammate's work sits in its worktree unmerged, and subsequent dependent waves cannot start. **Graceful degradation:** Eva's boot sequence reads `pipeline-state.md` and can detect unmerged teammate work. On session recovery, Eva can manually check worktree status and merge completed work. The worst case is falling back to sequential execution for the remainder of the pipeline -- not data loss.

## Decision

Implement Agent Teams as an experimental opt-in capability for wave execution. Eva acts as Team Lead, creating Teammate instances for Colby build units within a wave. When Agent Teams is unavailable or disabled, Eva falls back to sequential subagent invocation with zero behavioral change.

### Activation Model (Two Gates)

1. **Environment gate:** `CLAUDE_AGENT_TEAMS=1` must be set (Claude Code feature flag)
2. **Config gate:** `agent_teams_enabled: true` in `pipeline-config.json` (pipeline flag set during `/pipeline-setup`)

Both gates must pass for Agent Teams execution. Eva checks both at pipeline start (boot sequence step 3b, when reading `pipeline-config.json`). If either fails, Eva uses sequential subagent invocation.

### Execution Model

When Agent Teams is active, Eva's wave execution changes as follows:

**Current (sequential):**
```
Wave 1: Colby(Step A) -> Roz QA -> Colby(Step B) -> Roz QA -> ...
Wave 2: Colby(Step C) -> Roz QA -> ...
```

**With Agent Teams (parallel within wave):**
```
Wave 1: [Teammate-Colby(Step A) | Teammate-Colby(Step B)] -> merge all -> Roz QA per unit -> ...
Wave 2: [Teammate-Colby(Step C) | ...] -> merge all -> Roz QA per unit -> ...
```

Key changes:
- Eva creates one Teammate per wave unit, each with a task describing the ADR step, constraints, and test files
- Each Teammate runs Colby's persona in its own worktree
- Eva waits for all TaskCompleted events in the wave before proceeding
- After all teammates complete, Eva merges each worktree sequentially (one merge at a time, test suite between merges -- existing worktree rules)
- Roz QA runs per-unit on the merged result (unchanged)
- Poirot blind review runs per-unit on the merged result (unchanged)

### What Does NOT Change

- Wave grouping algorithm (Eva still extracts file deps, builds adjacency, topological sorts)
- Roz QA per unit (still runs after each unit merges, not in parallel)
- Poirot blind review per unit (still runs after each unit, not in parallel)
- Review juncture (still runs after all waves complete)
- Mandatory gates 1-12 (all preserved)
- Per-unit Ellis commits (still happen after each Roz QA PASS)
- Sequential fallback on file overlap detection

### Teammate Task Contract

Eva creates tasks for teammates using a structured format in the task description:

```
ADR: ADR-NNNN Step N
Files to create: [list]
Files to modify: [list]
Test files: [list]
Constraints: [from ADR step acceptance criteria]
Wave: N of M, Unit: K of L
```

The teammate (Colby instance) reads its task, executes the build, runs the lint command, and marks the task complete. The teammate does NOT run the full test suite -- that is Eva's responsibility after merge (mandatory gate 3).

### Timeout and Failure Handling

- Teammates get a `maxTurns` limit (configurable, default 25) to prevent runaway execution
- If a teammate does not complete within the turn limit, Eva marks it as failed and falls back to sequential execution for that unit
- If any teammate in a wave fails, Eva completes the successful teammates' merges, then runs the failed unit sequentially as a normal Colby subagent
- 3-failure loop-breaker (gate 12) still applies per unit, not per teammate

## Alternatives Considered

### A1: Parallel Subagents Without Agent Teams (Multiple Agent Tool Calls)

Use Claude Code's existing Agent tool to invoke multiple Colby subagents simultaneously, each told to work on a specific step.

**Pros:** No dependency on experimental feature. Works today.
**Cons:** Standard Agent tool invocations are sequential in Claude Code -- the tool call blocks until the subagent returns. There is no mechanism for Eva to invoke multiple Agent calls in parallel. Even if multiple calls were issued, they would share the same working directory, creating file conflicts. No worktree isolation.

**Rejected:** The Agent tool does not support true parallel execution. Issuing multiple Agent calls is sequential by design.

### A2: Eva Manually Creates Worktrees and Invokes Subagents

Eva uses Bash to create git worktrees, then invokes Colby subagents one at a time, each told to work in a specific worktree directory.

**Pros:** Works without Agent Teams. Uses existing worktree rules.
**Cons:** Still sequential -- Eva invokes one subagent at a time. Subagents in manually-created worktrees may not have `.claude/` configuration available. Eva managing worktree lifecycle (create, merge, delete) via Bash is fragile and violates the "Eva never runs git on code" gate (gate 2). Also increases Eva's context load significantly.

**Rejected:** Sequential execution, potential hook/config issues, and Eva would need to run git commands (violating gate 2).

### A3: Always-On Agent Teams (No Opt-In)

Make Agent Teams the default execution model, falling back silently when the env var is unset.

**Pros:** Simpler mental model -- wave execution "just works" when Agent Teams is available.
**Cons:** Agent Teams is experimental. Making it the default means pipeline behavior changes unexpectedly when users set or unset the env var. The pipeline's behavior should be deterministic and user-controlled. Silent feature activation based on environment variables is a debugging nightmare.

**Rejected:** Experimental features must be explicitly opted into, not silently activated. The user must understand they are enabling an experimental capability.

## Consequences

### Positive

- Enables true parallel wave execution, reducing build time for multi-step features proportionally to wave width
- Natural mapping: Eva as Team Lead mirrors her existing orchestrator role; teammates in worktrees mirror the existing worktree integration rules
- All mandatory gates preserved -- no quality regression
- Graceful degradation to sequential execution when Agent Teams is unavailable
- Task-based coordination (TaskCreate/TaskUpdate) aligns with Eva's existing TaskCreate/TaskUpdate tools for kanban observability

### Negative

- Dependency on experimental Claude Code feature -- API surface may change
- Merging multiple worktrees after parallel execution is more complex than sequential application of changes
- Token consumption increases: N parallel teammates consume N times the tokens of sequential execution (same total work, but concurrent billing)
- Hook behavior in worktrees is an assumption that must be validated per Claude Code version

### Neutral

- No database changes -- no brain schema changes
- No new agents -- Colby's persona is reused; teammates are Colby instances
- No new hooks -- existing hooks apply in worktrees (assumption validated at setup)
- `enforce-paths.sh` catch-all does not need changes -- teammate agents use `colby` as their agent_type, which has full write access (line 81-84)

## Implementation Plan

### Step 0: Pipeline Config Template Update

Add `agent_teams_enabled` field to the `pipeline-config.json` template.

**Files to modify:**
- `source/pipeline/pipeline-config.json`

**Acceptance criteria:**
- New field `"agent_teams_enabled": false` added to the JSON template
- Default is `false` (opt-in, not opt-out)
- Field is after `sentinel_enabled`, before the closing brace
- JSON is valid and parseable by `jq`

**Estimated complexity:** Low (add one JSON field)

### Step 1: Eva Boot Sequence Update -- Agent Teams Detection

Update `default-persona.md` boot sequence to detect Agent Teams availability at session start.

**Files to modify:**
- `source/rules/default-persona.md` -- add step 3d to boot sequence

**Acceptance criteria:**
- New step 3d (after 3c agent discovery, before step 4 brain health check): "Read `agent_teams_enabled` from `.claude/pipeline-config.json`. If `true`, check environment for Agent Teams availability (the feature is active when teammate creation succeeds or when the env var `CLAUDE_AGENT_TEAMS` is set). Set `agent_teams_available: true | false` in session state. If config is `false` or env var is unset, set `agent_teams_available: false`."
- Session state announcement (step 6) updated: append "Agent Teams: active (experimental)" or "Agent Teams: disabled" when the config flag is true. Omit the line entirely when config flag is false (user never opted in, do not announce).
- No changes to any existing boot sequence steps (1, 2, 3, 3b, 3c, 4, 5, 6)

**Estimated complexity:** Low (add one detection step and one announcement line)

### Step 2: Wave Execution Update -- Agent Teams Execution Path

Update `pipeline-operations.md` wave execution section to add the Agent Teams execution path alongside the existing sequential path.

**Files to modify:**
- `source/references/pipeline-operations.md` -- update `<operations id="wave-execution">`

**Acceptance criteria:**
- Existing wave extraction algorithm (steps 1-5) is unchanged
- New section after step 5: "Wave execution backend" with two paths:
  - **Sequential (default):** Current behavior -- Eva invokes Colby subagent per unit, one at a time. Describes current sequential flow.
  - **Agent Teams (when `agent_teams_available: true`):** Eva creates one Teammate per wave unit using the teammate task contract format. Eva waits for all TaskCompleted events. After all complete, Eva merges worktrees sequentially (one merge at a time, test suite between merges). If any teammate fails or times out, Eva falls back to sequential for remaining units in this wave.
- Teammate task contract format documented (ADR step, files, test files, constraints, wave/unit IDs)
- Timeout handling: default `maxTurns: 25` for teammates. If teammate does not complete, Eva marks unit as failed, falls back to sequential.
- Existing "Constraint preservation within waves" section updated: add note that Agent Teams does not change per-unit QA flow (Roz + Poirot still run per-unit after merge, not per-teammate)
- Brain integration section updated: wave decision capture includes execution backend used ("sequential" or "agent-teams")

**Estimated complexity:** Medium (new execution path alongside existing, must preserve all constraints)

### Step 3: Worktree Integration Rules Update

Update `pipeline-operations.md` worktree rules to address Agent Teams worktrees specifically.

**Files to modify:**
- `source/references/pipeline-operations.md` -- update `<operations id="worktree-rules">`

**Acceptance criteria:**
- Existing four worktree rules unchanged
- New subsection: "Agent Teams Worktrees" with:
  - Agent Teams worktrees are managed by Claude Code, not by Eva via Bash (unlike manual worktrees)
  - Merge order within a wave: Eva merges teammates' worktrees one at a time, in the order tasks were created (preserves deterministic merge order)
  - Test suite between each teammate merge (existing rule 3 applies)
  - If merge conflict detected: Eva falls back to sequential for the conflicting unit, routes conflict resolution to Colby, runs Roz before advancing (existing rule 2 applies)
  - Worktree cleanup: Claude Code manages worktree lifecycle; Eva does not delete worktrees manually

**Estimated complexity:** Low (additive subsection, existing rules preserved)

### Step 4: Pipeline Orchestration Update -- Agent Teams in Mandatory Gates

Update `pipeline-orchestration.md` to note Agent Teams interactions with mandatory gates.

**Files to modify:**
- `source/rules/pipeline-orchestration.md` -- update gate 2 (Ellis commits), gate 3 (full test suite), gate 5 (Poirot)

**Acceptance criteria:**
- Gate 2 note: "When Agent Teams is active, teammates do NOT commit. Eva merges teammate worktrees, then routes to Ellis for per-unit commits on the integrated result. The teammate -> merge -> Ellis flow is the same as the existing worktree -> merge -> Ellis flow."
- Gate 3 note: "When Agent Teams is active, teammates run lint but NOT the full test suite. The full test suite runs on the integrated codebase after each teammate's worktree is merged. This is the same rule as for any worktree-based change."
- Gate 5 note: "When Agent Teams is active, Poirot blind-reviews the merged diff per-unit, not the teammate's isolated diff. The review happens after merge, ensuring Poirot sees the integrated result."
- All notes are conditional: "When Agent Teams is active..." -- no behavioral change when Agent Teams is disabled
- No gate numbers change, no gates removed or weakened

**Estimated complexity:** Low (add conditional notes to existing gates)

### Step 5: Agent System Update -- Agent Teams Architecture Section

Add an Agent Teams section to `agent-system.md` describing the Team Lead / Teammate model.

**Files to modify:**
- `source/rules/agent-system.md` -- add new `<section id="agent-teams">` after `<section id="agent-discovery">`

**Acceptance criteria:**
- New section titled "Agent Teams (Experimental)" with:
  - Feature description: Eva as Team Lead, Colby instances as Teammates in worktrees
  - Activation: two gates (env var + config flag)
  - Scope: wave execution only -- Agent Teams does NOT replace subagent invocations for Roz, Poirot, Robert, Sable, Ellis, Agatha, Cal, Sentinel, or any non-build agent
  - Teammate identity: teammates run Colby's persona (`.claude/agents/colby.md`). They are Colby instances, not a new agent type.
  - Task lifecycle: Eva creates tasks -> teammates execute -> TaskCompleted fires on Eva -> Eva merges
  - Fallback: when Agent Teams is unavailable, Eva uses sequential subagent invocation (current behavior)
- Section is clearly marked experimental with a warning: "This section describes an experimental feature. Agent Teams is subject to change as Claude Code's Agent Teams feature evolves."
- Eva's tools list updated to include TaskGet (already has TaskCreate, TaskUpdate)

**Estimated complexity:** Medium (new section, must integrate cleanly with existing architecture description)

### Step 6: Pipeline-Setup Opt-In Flow

Update `skills/pipeline-setup/SKILL.md` to add the Agent Teams opt-in step after Sentinel opt-in and before brain setup.

**Files to modify:**
- `skills/pipeline-setup/SKILL.md` -- add Step 6b: Agent Teams opt-in

**Acceptance criteria:**
- Step 6b is positioned after Step 6a (Sentinel) and before "Brain setup offer"
- Eva asks: "Would you like to enable **Agent Teams** -- experimental parallel wave execution? When Claude Code's Agent Teams feature is active (`CLAUDE_AGENT_TEAMS=1`), Eva can run multiple Colby build units in parallel using git worktrees. This is experimental and the pipeline works identically without it."
- If user says yes:
  1. Set `agent_teams_enabled: true` in `.claude/pipeline-config.json`
  2. Print: "Agent Teams: enabled (experimental). Set `CLAUDE_AGENT_TEAMS=1` in your environment to activate. The pipeline will fall back to sequential execution if the env var is unset."
- If user says no: skip entirely, `agent_teams_enabled` remains `false`. Print: "Agent Teams: not enabled"
- No dependency checks needed (unlike Sentinel, no external tool to install)
- Setup summary updated to show Agent Teams status
- Installation manifest is NOT expanded (no new files to copy -- Agent Teams uses existing Colby persona)

**Estimated complexity:** Low (simple config flag toggle, no file installation)

### Step 7: Invocation Template for Teammate Tasks

Add an `agent-teams-task` invocation template to `invocation-templates.md` documenting the teammate task contract.

**Files to modify:**
- `source/references/invocation-templates.md` -- add `<template id="agent-teams-task">` section

**Acceptance criteria:**
- Template documents the task description format Eva uses when creating teammate tasks:
  - ADR reference (number + step)
  - Files to create and modify
  - Test files to target
  - Acceptance criteria from ADR step
  - Wave and unit identifiers
  - `maxTurns` recommendation
- Template includes explicit constraints for teammates: "Run lint after implementation. Do NOT run the full test suite. Do NOT commit. Do NOT modify files outside your assigned scope. If you encounter a file that should exist but does not, mark the task as blocked with a description of what is missing."
- Template notes that teammates load Colby's persona from `.claude/agents/colby.md` and project rules from `.claude/rules/`
- Template follows existing XML structure

**Estimated complexity:** Low (follows established template pattern)

### Step 8: Context Hygiene Update

Update `pipeline-operations.md` context hygiene section to address Agent Teams context implications.

**Files to modify:**
- `source/references/pipeline-operations.md` -- update `<section id="context-hygiene">`

**Acceptance criteria:**
- New row in "What Eva Carries vs. What Subagents Carry" table: `| Teammate task description | Creates (via TaskCreate) | Consumes (read from task) |`
- Note in Compaction Strategy: "Agent Teams teammates have fresh context per task (each is a new Claude Code instance). No compaction needed for teammates -- they are inherently fresh."
- Note: "Eva's context load increases with Agent Teams because she processes multiple TaskCompleted events per wave. The context cleanup advisory threshold (10 major handoffs) counts teammate completions individually."

**Estimated complexity:** Low (add table row and notes)

## Comprehensive Test Specification

### Step 0 Tests: Pipeline Config Template

| ID | Category | Description |
|----|----------|-------------|
| T-0010-001 | Happy | `source/pipeline/pipeline-config.json` contains `"agent_teams_enabled": false` field |
| T-0010-002 | Boundary | JSON is valid and parseable by `jq` after the addition |
| T-0010-003 | Regression | All existing fields in `pipeline-config.json` are unchanged: `branching_strategy`, `platform`, `platform_cli`, `mr_command`, `merge_command`, `environment_branches`, `base_branch`, `integration_branch`, `sentinel_enabled` |

### Step 1 Tests: Eva Boot Sequence Update

| ID | Category | Description |
|----|----------|-------------|
| T-0010-010 | Happy | `source/rules/default-persona.md` boot sequence contains step 3d that reads `agent_teams_enabled` from `pipeline-config.json` |
| T-0010-011 | Happy | Step 3d sets `agent_teams_available` in session state based on config flag AND environment detection |
| T-0010-012 | Failure | When `agent_teams_enabled` is `false` in config, `agent_teams_available` is `false` regardless of env var |
| T-0010-013 | Failure | When `agent_teams_enabled` is `true` but env var `CLAUDE_AGENT_TEAMS` is unset, `agent_teams_available` is `false` |
| T-0010-014 | Happy | Session state announcement includes "Agent Teams: active (experimental)" when both gates pass |
| T-0010-015 | Boundary | Session state announcement omits Agent Teams line entirely when `agent_teams_enabled` is `false` |
| T-0010-016 | Regression | All existing boot sequence steps (1, 2, 3, 3b, 3c, 4, 5, 6) are unchanged |
| T-0010-017 | Failure | If `pipeline-config.json` is missing `agent_teams_enabled` field entirely, default to `false` (backward compatible) |

### Step 2 Tests: Wave Execution Update

| ID | Category | Description |
|----|----------|-------------|
| T-0010-020 | Happy | `pipeline-operations.md` wave execution section contains "Wave execution backend" with two paths: sequential and Agent Teams |
| T-0010-021 | Happy | Sequential path describes current behavior (Eva invokes Colby subagent per unit, one at a time) |
| T-0010-022 | Happy | Agent Teams path describes: create one Teammate per wave unit, wait for TaskCompleted events, merge sequentially |
| T-0010-023 | Happy | Teammate task contract format is documented with: ADR reference, files, test files, constraints, wave/unit IDs |
| T-0010-024 | Failure | Timeout handling documented: default `maxTurns: 25`, teammate timeout = mark failed, fall back to sequential |
| T-0010-025 | Failure | Partial wave failure: if one teammate fails, successful teammates' merges complete, failed unit runs sequentially |
| T-0010-026 | Regression | Existing wave extraction algorithm (steps 1-5) is unchanged |
| T-0010-027 | Boundary | Agent Teams does NOT change per-unit QA flow: Roz + Poirot still run after merge, not per-teammate |
| T-0010-028 | Happy | Brain integration captures execution backend ("sequential" or "agent-teams") in wave decision |
| T-0010-029 | Boundary | All Agent Teams execution is conditional on `agent_teams_available: true` |

### Step 3 Tests: Worktree Integration Rules Update

| ID | Category | Description |
|----|----------|-------------|
| T-0010-030 | Happy | `pipeline-operations.md` worktree rules contain "Agent Teams Worktrees" subsection |
| T-0010-031 | Happy | Subsection states Agent Teams worktrees are managed by Claude Code, not Eva via Bash |
| T-0010-032 | Happy | Merge order documented: one at a time, in task creation order |
| T-0010-033 | Happy | Test suite between each teammate merge is explicitly stated |
| T-0010-034 | Failure | Merge conflict handling: fallback to sequential, Colby resolves, Roz verifies |
| T-0010-035 | Regression | Existing four worktree rules are unchanged |

### Step 4 Tests: Pipeline Orchestration Update

| ID | Category | Description |
|----|----------|-------------|
| T-0010-040 | Happy | Gate 2 (Ellis commits) has Agent Teams note: teammates do NOT commit, Ellis commits after merge |
| T-0010-041 | Happy | Gate 3 (full test suite) has Agent Teams note: teammates run lint only, full suite after merge |
| T-0010-042 | Happy | Gate 5 (Poirot) has Agent Teams note: Poirot reviews merged diff, not isolated teammate diff |
| T-0010-043 | Boundary | All gate notes are conditional: "When Agent Teams is active..." |
| T-0010-044 | Regression | All mandatory gates (1-12) retain their existing behavior; no gate is removed or weakened |
| T-0010-045 | Regression | Gate numbers do not change |

### Step 5 Tests: Agent System Update

| ID | Category | Description |
|----|----------|-------------|
| T-0010-050 | Happy | `source/rules/agent-system.md` contains `<section id="agent-teams">` |
| T-0010-051 | Happy | Section describes Eva as Team Lead, Colby instances as Teammates |
| T-0010-052 | Happy | Two-gate activation documented (env var + config flag) |
| T-0010-053 | Happy | Scope: wave execution only -- explicitly states Agent Teams does NOT replace subagent invocations for non-build agents |
| T-0010-054 | Happy | Teammate identity: explicitly states teammates run Colby's persona |
| T-0010-055 | Happy | Task lifecycle documented: Eva creates -> teammates execute -> TaskCompleted -> Eva merges |
| T-0010-056 | Failure | Fallback documented: when unavailable, sequential subagent invocation |
| T-0010-057 | Happy | Section marked experimental with warning |
| T-0010-058 | Boundary | Eva's tools list includes TaskGet alongside existing TaskCreate, TaskUpdate |
| T-0010-059 | Regression | All existing sections in `agent-system.md` are unchanged |

### Step 6 Tests: Pipeline-Setup Opt-In

| ID | Category | Description |
|----|----------|-------------|
| T-0010-060 | Happy | SKILL.md contains Step 6b positioned after Step 6a (Sentinel) and before brain setup offer |
| T-0010-061 | Happy | Step 6b asks user about Agent Teams with explanation and experimental warning |
| T-0010-062 | Happy | "Yes" path: sets `agent_teams_enabled: true` in `pipeline-config.json`, prints activation instructions |
| T-0010-063 | Happy | Activation instructions mention the `CLAUDE_AGENT_TEAMS=1` env var requirement |
| T-0010-064 | Failure | "No" path: skips entirely, `agent_teams_enabled` remains `false` |
| T-0010-065 | Happy | Setup summary includes Agent Teams status line |
| T-0010-066 | Regression | Existing SKILL.md steps 1-6a are unchanged |
| T-0010-067 | Regression | Brain setup offer position is unchanged (still last) |
| T-0010-068 | Boundary | No new files installed for Agent Teams (no installation manifest expansion) |

### Step 7 Tests: Invocation Template

| ID | Category | Description |
|----|----------|-------------|
| T-0010-070 | Happy | `source/references/invocation-templates.md` contains `<template id="agent-teams-task">` section |
| T-0010-071 | Happy | Template documents teammate task description format with ADR reference, files, test files, constraints, wave/unit IDs |
| T-0010-072 | Happy | Template includes explicit teammate constraints: run lint, no full test suite, no commit, no out-of-scope files |
| T-0010-073 | Happy | Template includes `maxTurns` recommendation |
| T-0010-074 | Happy | Template notes teammates load Colby persona and project rules from `.claude/` |
| T-0010-075 | Failure | Template includes blocked-task instruction: if missing dependency, mark task as blocked |
| T-0010-076 | Regression | All existing templates in `invocation-templates.md` are unchanged |

### Step 8 Tests: Context Hygiene Update

| ID | Category | Description |
|----|----------|-------------|
| T-0010-080 | Happy | Context hygiene table has teammate task description row |
| T-0010-081 | Happy | Compaction strategy notes teammates have inherently fresh context |
| T-0010-082 | Happy | Context cleanup advisory counts teammate completions toward handoff threshold |
| T-0010-083 | Regression | All existing context hygiene content is unchanged |

### Step 0-8 Telemetry

| Step | Telemetry | Trigger | Absence Means |
|------|-----------|---------|---------------|
| Step 0 | `pipeline-config.json` contains `agent_teams_enabled` field | Every pipeline boot (Eva reads config) | Config template not updated |
| Step 1 | Eva announcement: "Agent Teams: active (experimental)" or "Agent Teams: disabled" | Session start when `agent_teams_enabled: true` | Detection step silently skipped |
| Step 2 | Eva announcement: "Wave N executing via Agent Teams: [K teammates]" or "Wave N executing sequentially" | Wave execution start | Eva not announcing execution backend |
| Step 2 | Brain capture: "Wave grouping: ... Execution: agent-teams/sequential" | After wave grouping (brain available) | Brain capture missing execution backend |
| Step 4 | Eva log: "Teammate [task-id] completed. Merging worktree." | TaskCompleted event processing | TaskCompleted events not being processed |
| Step 6 | Setup summary: "Agent Teams: enabled (experimental)/not enabled" | Every `/pipeline-setup` run | Opt-in step silently skipped |
| Step 7 | Task description matches documented contract format | Every teammate task creation | Contract format not followed |

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `pipeline-config.json` (`agent_teams_enabled`) | Boolean flag | Eva boot sequence (gates Agent Teams behavior) | Step 0, Step 1 |
| Eva (TaskCreate) | Teammate task: `{adr_ref, files_create, files_modify, test_files, constraints, wave_id, unit_id, maxTurns}` | Colby Teammate instance (reads task, executes build) | Step 2, Step 7 |
| Colby Teammate (TaskUpdate on completion) | Task status: `completed` with output summary | Eva (TaskCompleted hook, triggers merge) | Step 2 |
| Colby Teammate worktree | Git branch with changes | Eva (merges via git operations) | Step 3 |
| Eva (merged diff per unit) | `git diff` output | Roz QA + Poirot blind review (unchanged) | Step 4 |
| `/pipeline-setup` opt-in | Sets config flag | Runtime pipeline | Step 6 -> all other steps |

## Anti-Goals

1. **Anti-goal: Replacing subagent invocations for non-Colby agents with Agent Teams.** Reason: Agent Teams is for parallel build execution (Colby). Roz, Poirot, Ellis, Agatha, Robert, Sable, Cal, and Sentinel are invoked sequentially or in their existing parallel patterns (review juncture). These agents do not benefit from worktree isolation -- they read and verify, they do not write code to separate branches. Revisit: if Agent Teams supports non-worktree Teammates that can share a working directory for read-only parallel verification.

2. **Anti-goal: Peer-to-peer messaging between teammates.** Reason: The current design has teammates operating independently on isolated ADR steps within a wave. By definition, wave units have zero file overlap. There is no need for teammates to communicate with each other -- Eva coordinates all cross-unit concerns after merge. Adding peer-to-peer messaging would create implicit coupling between supposedly independent units. Revisit: if a future wave grouping algorithm allows overlapping steps with defined merge protocols.

3. **Anti-goal: Automatic scaling of wave width based on available resources.** Reason: Wave width is determined by file dependency analysis, not resource availability. Eva creates one teammate per wave unit. Adding resource-aware scaling (e.g., limit to 3 concurrent teammates) introduces a configuration dimension that is premature for an experimental feature. Revisit: if token consumption monitoring shows that large waves (5+ teammates) cause billing concerns or Claude Code instance limits.

## Blast Radius

### Files Created

None. Agent Teams reuses existing agent personas and infrastructure.

### Files Modified

| File | Change Type | Impact |
|------|-------------|--------|
| `source/pipeline/pipeline-config.json` | Add `agent_teams_enabled` field | Config template for all target projects |
| `source/rules/default-persona.md` | Add boot step 3d, update announcement | Eva boot sequence for all target projects |
| `source/references/pipeline-operations.md` | Update wave execution, worktree rules, context hygiene | Operational procedures for all target projects |
| `source/rules/pipeline-orchestration.md` | Add Agent Teams notes to gates 2, 3, 5 | Pipeline flow documentation for all target projects |
| `source/rules/agent-system.md` | Add `<section id="agent-teams">` | Agent architecture documentation for all target projects |
| `skills/pipeline-setup/SKILL.md` | Add Step 6b opt-in flow | Setup user experience |
| `source/references/invocation-templates.md` | Add agent-teams-task template | Eva invocation reference |

### Files NOT Modified (verified no changes needed)

| File | Reason |
|------|--------|
| `source/agents/colby.md` | Colby's persona is unchanged. Teammates load it as-is from `.claude/agents/colby.md`. No teammate-specific behavior needed in the persona -- constraints come from the task description. |
| `source/agents/*.md` (all other agents) | No agent personas change. Agent Teams affects only Eva's orchestration layer. |
| `source/hooks/enforce-paths.sh` | Teammates use `colby` as agent_type (line 81-84: full write access). No hook changes needed. |
| `source/hooks/enforce-sequencing.sh` | Teammates are not invoked via the Agent tool on Eva's thread -- they are Claude Code instances. Sequencing hooks fire on Eva's thread, not on teammate threads. However, `.claude/settings.json` is shared via worktree, so hooks ARE active per-teammate. No changes needed. |
| `source/hooks/enforce-git.sh` | Teammates should not run git commit (Eva merges). This is enforced by the task description constraint, not by the hook. The git hook blocks main-thread git operations. In a worktree, the teammate IS the main thread of its instance -- this hook would block teammate git operations, which is correct behavior (teammates should not commit). |
| `source/hooks/enforcement-config.json` | No new config keys needed. |
| `source/commands/*.md` | No new slash command for Agent Teams. |
| `source/rules/pipeline-models.md` | Teammates are Colby instances -- existing model selection applies. No new model table entries. |
| `source/references/agent-preamble.md` | Teammates reference preamble via Colby's persona. No changes needed. |

### Consumers of Modified Files

| File | Consumers |
|------|-----------|
| `source/pipeline/pipeline-config.json` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/`), Eva boot sequence |
| `source/rules/default-persona.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/rules/`), Claude Code (always loaded) |
| `source/references/pipeline-operations.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/references/`), Eva at pipeline start |
| `source/rules/pipeline-orchestration.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/rules/`), Eva when reading `docs/pipeline/` files |
| `source/rules/agent-system.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/rules/`), all target projects |
| `skills/pipeline-setup/SKILL.md` | Plugin skill system (invoked via `/pipeline-setup`) |
| `source/references/invocation-templates.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/references/`), Eva when constructing invocations |

## Data Sensitivity

Not applicable -- Agent Teams does not introduce data access methods, stores, or persistent state. Task descriptions contain ADR step references and file paths, which are project-internal and not sensitive.

## Notes for Colby

1. **Step ordering matters.** Step 0 (config) should be first because all other steps reference `agent_teams_enabled`. Steps 1-5 and 7-8 can be done in any order after 0. Step 6 (SKILL.md) should be last because it references the config field and must be positioned after 6a (Sentinel).

2. **Conditional language pattern.** Every mention of Agent Teams in modified files must be conditional: "When Agent Teams is active..." or "(when `agent_teams_available: true`)" or "(experimental)". Follow the same pattern used for Sentinel: always make it clear that disabled = zero change.

3. **Existing worktree rules are the foundation.** The four rules in `<operations id="worktree-rules">` already describe the correct behavior for merging worktree changes. Agent Teams worktrees follow these same rules. The new subsection is additive -- it addresses Agent Teams-specific concerns (who manages the worktree lifecycle, merge order) without duplicating the base rules.

4. **Teammates are Colby, not a new agent.** Do not create a new persona file, a new agent type, or a new case in `enforce-paths.sh`. Teammates ARE Colby instances. They load `colby.md`, they match the `colby)` case in the hook, they follow Colby's constraints. The differentiation is in the task description (which comes from Eva), not in the persona.

5. **Gate notes are informational, not new gates.** When adding Agent Teams notes to gates 2, 3, and 5 in `pipeline-orchestration.md`, these are clarifying notes within existing gates, not new mandatory gates. Format them as indented notes: "Note (Agent Teams): When Agent Teams is active, [clarification]." Do not change gate numbering or gate behavior.

6. **Boot sequence step 3d placement.** Step 3d goes after 3c (agent discovery) and before 4 (brain health check). This is because Agent Teams detection reads `pipeline-config.json` (same file as step 3b) and does not depend on brain availability. It is purely a config + env var check.

7. **SKILL.md placement.** Step 6b goes after Step 6a (Sentinel) and before the brain setup offer. The ordering is: required setup -> optional security (Sentinel) -> optional parallel execution (Agent Teams) -> optional memory (Brain). Agent Teams before Brain because Agent Teams has no external dependencies (unlike Sentinel which needs pip, or Brain which needs PostgreSQL).

8. **TaskGet in Eva's tools.** When updating Eva's tools list in `agent-system.md`, add `TaskGet` alongside the existing `TaskCreate, TaskUpdate`. Eva needs `TaskGet` to check teammate task status during wave execution. This is a minor addition to an existing line, not a new section.

9. **The `enforce-git.sh` hook interaction.** In a worktree, the teammate's Claude Code instance has its own "main thread." The `enforce-git.sh` hook blocks git write operations from the main thread. Since teammates ARE main-thread instances in their worktrees, `enforce-git.sh` will block them from running `git commit` -- this is CORRECT behavior. Teammates should not commit. Eva merges and Ellis commits. Do not add an exception for teammates.

10. **Brain thought from roadmap item #13 confirmed the design.** The brain captured this as a strategic roadmap item: "Eva as Team Lead, Colby instances as Teammates in worktrees with shared task list. TaskCompleted hooks enforce DoD. True parallel execution without Eva carrying inter-unit state." This ADR implements exactly that design.

## DoD: Verification

| Requirement | Step | Test IDs | Status |
|-------------|------|----------|--------|
| R1: Experimental, opt-in, two gates (env var + config flag) | Step 0, Step 1, Step 6 | T-0010-001, T-0010-010 through T-0010-017, T-0010-060 through T-0010-068 | Designed |
| R2: Eva as Team Lead, Colby as Teammates in worktrees | Step 2, Step 5 | T-0010-020 through T-0010-029, T-0010-050 through T-0010-059 | Designed |
| R3: Pipeline works identically when disabled | Step 1, Step 2 | T-0010-012, T-0010-013, T-0010-015, T-0010-017, T-0010-021, T-0010-029 | Designed |
| R4: All changes in `source/` and `skills/` only | All | Blast radius table | Designed |
| R5: Non-code ADR (persona files, rules, config) | All | All test categories confirm file types | Designed |
| R6: Shared task list via TaskCreate/TaskUpdate/TaskGet | Step 2, Step 5, Step 7 | T-0010-022, T-0010-055, T-0010-058, T-0010-070 through T-0010-076 | Designed |
| R7: TaskCompleted hooks fire on Eva | Step 2 | T-0010-022, telemetry (Step 4) | Designed |
| R8: Each teammate gets own worktree | Step 2, Step 3 | T-0010-022, T-0010-030 through T-0010-035 | Designed |
| R9: Mechanical enforcement via hooks in worktrees | Step 4, blast radius (no hook changes) | T-0010-040 through T-0010-045, Notes for Colby #9 | Designed |
| R10: Teammates need explicit constraints in invocation | Step 7 | T-0010-070 through T-0010-076 | Designed |
| R11: Setup asks user, warns experimental | Step 6 | T-0010-060 through T-0010-068 | Designed |
| R12: Wave execution uses Agent Teams when available, sequential when not | Step 2 | T-0010-020 through T-0010-029 | Designed |
| R13: Existing worktree rules preserved | Step 3 | T-0010-030 through T-0010-035 | Designed |
| R14: `maxTurns` for teammate runaway prevention | Step 2, Step 7 | T-0010-024, T-0010-073 | Designed |

### Architectural Decisions Not in Spec

1. **Two-gate activation model (env var + config flag):** The context-brief mentions "env var" and "pipeline-config flag" but does not specify that BOTH must pass. This ADR requires both because: the env var gates Claude Code's feature availability, the config flag gates the user's intent. A user who set `agent_teams_enabled: true` but later unsets the env var should not see unexpected behavior.

2. **Teammates run lint but not the full test suite:** This is derived from mandatory gate 3 (full test suite on integrated codebase after merge). Teammates work in isolated worktrees and cannot run the full suite meaningfully -- their results would not reflect the integrated state. Lint is a fast, local check that catches basic errors before merge.

3. **Merge order is task creation order:** When merging multiple teammate worktrees, Eva merges in the order she created the tasks. This ensures deterministic behavior -- the same wave with the same units always merges in the same order, making `git bisect` predictable.

4. **Partial wave failure does not abort the wave:** If one teammate fails, Eva still merges the successful teammates' work and runs the failed unit sequentially. This maximizes the work preserved from parallel execution rather than discarding all parallel results on a single failure.

5. **Eva's tools list gains TaskGet:** Eva already has TaskCreate and TaskUpdate. TaskGet is needed to check teammate task status. This is a minor correction to an existing capability, not a new tool grant.

### Rejected During Design

1. **Adding a `colby-teammate` agent type:** Would require a new persona file, new hook cases, new model table entries. Teammates ARE Colby -- no new agent type needed.
2. **Roz running in parallel in teammate worktrees:** Would violate gate 1 (Roz verifies on integrated codebase) and gate 5 (Poirot reviews merged diff). QA must happen post-merge.
3. **Auto-detecting Agent Teams without config flag:** Would make pipeline behavior non-deterministic based on environment alone. Users must explicitly opt in.

### Technical Constraints Discovered

1. `enforce-paths.sh` line 81-84: Colby has full write access. Teammates (as Colby instances) inherit this. No hook changes needed.
2. `enforce-git.sh` blocks main-thread git write operations. In worktree contexts, this correctly prevents teammates from committing. Desirable behavior.
3. `pipeline-config.json` is already read by Eva at boot step 3b. Adding `agent_teams_enabled` to the same file means no new file read needed.
4. Eva's tools already include TaskCreate and TaskUpdate (agent-system.md line 74, default-persona.md line 109). Adding TaskGet is a natural extension.

---

ADR saved to `docs/architecture/ADR-0010-agent-teams.md`. 9 steps (0-8), 60 total tests. Next: Roz reviews the test spec.
