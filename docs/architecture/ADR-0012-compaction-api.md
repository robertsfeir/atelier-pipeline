# ADR-0012: Compaction API Integration for Long Pipeline Sessions

## Status

Proposed

## DoR: Requirements Extracted

| # | Requirement | Source | Notes |
|---|-------------|--------|-------|
| R1 | Enable Anthropic's server-side context management (`context_management.edits` with `compact_20260112` strategy) for Eva's session | Issue #21, context | Anthropic platform feature -- we configure it, not implement it |
| R2 | Remove manual `/compact` handling and related advisory language | Issue #21 | Context Cleanup Advisory section becomes compaction-aware |
| R3 | pipeline-state.md remains as the cross-session recovery mechanism; compaction is within-session only | Issue #21, constraints | Compaction does not replace state files |
| R4 | Document how Eva preserves critical state before/after compaction events | Issue #21 | Rules files survive compaction (path-scoped, re-injected from disk per ADR-0004) |
| R5 | Document what Eva must write to pipeline-state.md to survive compaction | Issue #21 | State file is the compaction safety net |
| R6 | Update the context cleanup advisory to reflect compaction handling what `/compact` used to handle | Issue #21 | Advisory goes from "suggest fresh session" to "compaction handles this; state file is your safety net" |
| R7 | Consider PreCompact/PostCompact hooks for state preservation | Issue #21 | Hooks are the mechanism for writing state before compaction fires |
| R8 | All changes target `source/` only (not `.claude/`) | constraints, context-brief.md | Dual tree convention |
| R9 | This is a non-code ADR -- changes to Eva's rules and pipeline operations docs | constraints | Skip Roz test spec/authoring; Colby implements, Roz verifies against ADR |
| R10 | Combined with observation masking (#10) for subagent contexts | Issue #21 | #10 is a separate ADR in the same batch; this ADR does not depend on #10 |

### Retro Risks

| Lesson | Risk to this feature | Mitigation |
|--------|---------------------|------------|
| #003 (Stop hook race condition) | A PreCompact hook that is too heavy (writes + brain capture) could cause hangs or timeouts analogous to the Stop hook race condition | PreCompact hook must be lightweight -- write pipeline-state.md only. No brain calls, no test runs, no subagent invocations. |
| #004 (Hung process retry loop) | Compaction events could interrupt Eva mid-invocation; if Eva retries the interrupted invocation after compaction, this could create a loop | Eva does not retry interrupted invocations. After compaction, Eva reads pipeline-state.md and resumes from the last recorded state, not from mid-invocation. |
| Brain lesson: auto-compact infinite retry (Claude Code issue #22758) | 27 compact agents spawned, 695M cache-read tokens consumed in 2.5 hours. Server-side compaction should be safer but could introduce analogous failure modes. | Server-side compaction (Compaction API) is fundamentally different from client-side auto-compact. It runs server-side within the API response, not by spawning compact agents. The infinite retry bug was a client-side Claude Code issue, not an API issue. However, we document graceful degradation: if compaction produces unexpected state, Eva falls back to pipeline-state.md recovery. |

### Anti-goals

1. **Anti-goal: Implementing the Compaction API ourselves.** Reason: The Compaction API is an Anthropic platform feature handled by Claude Code. We document how Eva behaves around it, not how to build it. Revisit: if Anthropic deprecates server-side compaction and we need a custom solution.

2. **Anti-goal: Eliminating pipeline-state.md as a recovery mechanism.** Reason: Compaction is within-session only. Cross-session recovery still requires state files on disk. Revisit: if Anthropic provides persistent session state across restarts.

3. **Anti-goal: Applying compaction to subagent contexts.** Reason: Each subagent invocation gets a fresh context window. Compaction applies to Eva's main thread only. Subagent context management is #10 (observation masking), a separate concern. Revisit: if subagent invocations become long-lived enough to need compaction.

## Spec Challenge

**The spec assumes** that Anthropic's Compaction API fires compaction events that are detectable via hooks (PreCompact/PostCompact), allowing Eva to write state before context is compacted. If this is wrong -- if compaction happens silently server-side with no hook notification -- the design fails because Eva cannot proactively save state before compaction discards context. **Are we confident?** Partially. Claude Code's hook system supports PreCompact and PostCompact hooks (documented in Claude Code's settings.json schema). However, if the Compaction API operates at the API layer before the hook system fires, hooks may not trigger. Mitigation: Eva writes pipeline-state.md at every phase transition anyway (existing behavior), so the worst case is losing state from the current in-progress phase -- Eva resumes from the last completed phase, not from scratch.

**SPOF:** The PreCompact hook's ability to fire and complete before compaction discards context. **Failure mode:** If the PreCompact hook does not fire (or fires but is interrupted by compaction), Eva loses in-progress state for the current phase. Pipeline-state.md has the last completed phase. **Graceful degradation:** Eva resumes from the last completed phase recorded in pipeline-state.md. The current in-progress phase is re-executed. This is the same recovery mechanism used for session crashes today -- compaction failure is no worse than a crash.

## Context

### Current State

Eva manages long pipeline sessions through two mechanisms:

1. **Path-scoped rules files** (ADR-0004): `pipeline-orchestration.md` and `pipeline-models.md` are path-scoped rules that survive `/compact` because Claude Code re-injects them from disk after compaction. This protects mandatory gates, triage logic, and model selection tables from lossy summarization.

2. **Context Cleanup Advisory**: After 10 major agent handoffs, Eva suggests a fresh session. Pipeline-state.md and context-brief.md preserve state across sessions. This is advisory -- Eva never forces a break.

3. **Manual `/compact`**: Users can run `/compact` to free context. Rules files survive, but Read-tool content (agent outputs, investigation results, intermediate state) is summarized lossily.

### Problem

Large pipelines (5+ ADR steps, multiple waves, review juncture with 5 parallel reviewers) consume Eva's context window long before the pipeline completes. The manual approach -- suggesting fresh sessions at 10 handoffs -- forces users to break flow, restart sessions, and wait for Eva's boot sequence. This is especially painful for Agent Teams pipelines where Eva processes multiple TaskCompleted events per wave.

### Solution: Compaction API

Anthropic's Compaction API (`context_management.edits` with the `compact_20260112` strategy) provides server-side context management. When enabled, the API automatically compacts context when it approaches the limit, preserving the system prompt and recent turns while summarizing older content. This eliminates the need for manual `/compact` and reduces the urgency of "suggest fresh session" advisories.

Key properties of the Compaction API relevant to the pipeline:
- **Server-side**: Runs within the API, not by spawning compact agents (avoids the infinite retry bug from Claude Code issue #22758)
- **System prompt preserved**: Always-loaded rules (default-persona.md, agent-system.md) are always intact
- **Path-scoped rules preserved**: Re-injected from disk on every turn (ADR-0004 design)
- **Read-tool content summarized**: Agent outputs, investigation results, intermediate findings are lossily compressed
- **Within-session only**: No cross-session persistence -- pipeline-state.md remains essential

### Relationship to Observation Masking (#10)

Issue #10 (observation masking) addresses subagent context -- reducing the output Eva receives from subagent invocations by masking verbose tool observations. This ADR (#21) addresses Eva's main thread context -- how Eva manages her own context window over a long pipeline. They are complementary:
- **#10 (observation masking)**: Reduces context input per subagent return
- **#21 (compaction API)**: Manages total context accumulation over the full pipeline

Neither depends on the other. Both can be implemented independently.

## Decision

Integrate the Compaction API into Eva's pipeline behavior by updating three areas: (1) the context hygiene strategy in `pipeline-operations.md`, (2) the context cleanup advisory in `pipeline-orchestration.md`, and (3) a PreCompact hook configuration that writes pipeline state before compaction fires.

### What Changes

1. **Compaction Strategy section** is rewritten: the current manual "recommend fresh session at 60%" becomes "Compaction API handles context automatically; Eva writes state proactively at every phase transition; PreCompact hook ensures state is saved before compaction fires."

2. **Context Cleanup Advisory** is updated: the current "suggest fresh session after 10 handoffs" becomes "Compaction API manages context within the session; Eva no longer suggests session breaks for context reasons. Eva still suggests session breaks for truly massive pipelines (20+ handoffs) where even compacted context quality degrades."

3. **PreCompact hook** is added: a lightweight shell script that writes a compaction marker to pipeline-state.md. This is a safety net, not the primary mechanism -- Eva already writes state at every phase transition.

### What Does NOT Change

- Pipeline-state.md as the cross-session recovery mechanism
- Eva's boot sequence (reads pipeline-state.md, context-brief.md, error-patterns.md)
- Path-scoped rules surviving compaction (ADR-0004 design, still works)
- Subagent invocations getting fresh context (each is a new context window)
- Any mandatory gate behavior
- Brain capture/read patterns

## Alternatives Considered

### A1: Keep Manual `/compact` Advisory Only (Status Quo)

Continue with the current approach: Eva suggests fresh sessions at 10 handoffs, users manually run `/compact` when needed, rules files survive via path-scoped injection.

**Pros:** No changes needed. Proven to work. No new hooks.
**Cons:** User friction on large pipelines. Session breaks disrupt flow. Context degrades silently before the 10-handoff advisory fires. Agent Teams pipelines hit context limits faster (multiple TaskCompleted events per wave).

**Rejected:** The Compaction API is available, server-side, and eliminates the user friction without adding complexity. The status quo works but is strictly worse when the API is available.

### A2: Full State Serialization on Every Turn

Write complete pipeline state (including in-progress invocation details, current agent context, pending findings) to disk on every turn, enabling lossless recovery from any compaction event.

**Pros:** Zero information loss on compaction. Recovery is always from the exact point of interruption.
**Cons:** Massive write overhead -- every Eva turn would write a full state dump. Pipeline-state.md would become enormous. The Write tool calls would themselves consume context. Most writes are wasted (compaction is infrequent). This is the same anti-pattern as the Stop hook (retro lesson #003) -- doing expensive work on every event "just in case."

**Rejected:** The overhead is disproportionate to the benefit. Phase-transition writes (current behavior) plus a lightweight PreCompact hook provide sufficient recovery without the cost.

### A3: PostCompact Hook Instead of PreCompact

Use a PostCompact hook that reads pipeline-state.md after compaction and re-injects critical context, rather than a PreCompact hook that saves state before compaction.

**Pros:** Simpler -- no need to race compaction. PostCompact fires after context is already compacted, so timing is not an issue.
**Cons:** After compaction, Eva's context is already summarized. A PostCompact hook that reads pipeline-state.md would inject the state file into the already-compacted context, which is useful but does not prevent information loss from the pre-compaction context. Also, path-scoped rules already handle re-injection of critical rules content.

**Considered but deferred:** A PostCompact hook could be useful as a complement to PreCompact (re-inject pipeline state after compaction). However, the path-scoped rules mechanism already re-injects the critical operational content. Adding a PostCompact re-injection of pipeline-state.md is a nice-to-have that can be added later if compaction recovery proves insufficient.

## Consequences

### Positive

- Eliminates manual `/compact` handling and "suggest fresh session" friction for most pipelines
- Server-side compaction avoids the infinite retry bug that plagued client-side auto-compact
- Path-scoped rules (ADR-0004) continue to protect mandatory gates and triage logic through compaction
- Pipeline-state.md continues to provide cross-session recovery
- PreCompact hook provides a safety net for in-progress state

### Negative

- Compaction may summarize Eva's accumulated context about agent outputs, investigation findings, and triage decisions -- Eva must rely on pipeline-state.md and brain for recovery of this information
- PreCompact hook adds a new shell script to maintain and test
- If the Compaction API changes behavior (e.g., different summarization strategy), Eva's context quality after compaction could degrade without warning
- Compaction is opaque -- Eva cannot control what gets summarized or preserved (unlike manual `/compact` where the user had some control over timing)

### Neutral

- No database changes
- No new agents
- No changes to mandatory gates
- No changes to subagent invocations
- Brain capture/read patterns unchanged
- Agent Teams behavior unchanged (teammates have fresh context regardless)

### Finding: No Graceful Degradation for Compaction Quality

If the Compaction API produces a poor summary (loses critical triage findings, misrepresents phase state), Eva has no way to detect this. She would proceed with incorrect context. The pipeline-state.md safety net covers "what phase am I in" but not "what did the reviewers find." This is not unique to compaction -- the same risk exists with manual `/compact`. The mitigation is the same: brain captures preserve decisions and findings across compaction events, and Roz's final sweep catches issues that earlier QA found but compaction lost.

## Implementation Plan

### Step 1: Compaction Strategy Update in Pipeline Operations

Update the Context Hygiene section in `pipeline-operations.md` to replace the manual compaction strategy with Compaction API awareness.

**Files to modify:**
- `source/references/pipeline-operations.md` -- rewrite `### Compaction Strategy` within `<section id="context-hygiene">`

**Acceptance criteria:**
- Existing "Compaction Strategy" subsection is replaced with an updated version that:
  - States: "When the Compaction API is active (`context_management.edits` enabled), server-side compaction manages Eva's context automatically. Eva does not need to track context usage percentage or suggest session breaks for context reasons."
  - States: "Path-scoped rules (`pipeline-orchestration.md`, `pipeline-models.md`) survive compaction -- they are re-injected from disk on every turn (ADR-0004 design)."
  - States: "Eva writes pipeline-state.md at every phase transition (existing behavior). This is the primary compaction safety net -- if compaction summarizes away in-progress details, Eva can recover from the last recorded phase."
  - States: "Brain captures (when available) provide a secondary recovery path -- decisions, findings, and lessons captured during the pipeline are queryable after compaction via `agent_search`."
  - Preserves the existing bullet: "Between major phases: start fresh subagent sessions. Pipeline-state.md is the recovery mechanism."
  - Preserves the existing bullet about Colby+Roz interleaving (fresh context per unit)
  - Preserves the Agent Teams teammate note (fresh context per task)
  - Preserves the "Never carry Roz reports" rule
- The "60% context usage" trigger for fresh session recommendation is removed (compaction handles this)
- New bullet: "Eva herself: Compaction API manages context automatically. Eva no longer tracks context usage percentage. For very large pipelines (20+ agent handoffs), Eva may still suggest a fresh session if response quality visibly degrades -- but this is a quality signal, not a context-counting heuristic."

**Estimated complexity:** Low (rewrite one subsection, preserve surrounding content)

### Step 2: Context Cleanup Advisory Update in Pipeline Orchestration

Update the Context Cleanup Advisory section in `pipeline-orchestration.md` to reflect Compaction API handling.

**Files to modify:**
- `source/rules/pipeline-orchestration.md` -- rewrite `### Context Cleanup Advisory` within `<section id="pipeline-flow">`

**Acceptance criteria:**
- Existing advisory is replaced with an updated version that:
  - States: "Server-side compaction (Compaction API) manages Eva's context window automatically during long pipeline sessions. Eva does not suggest session breaks based on handoff counts."
  - States: "Eva still suggests a fresh session when: (a) response quality visibly degrades (Eva's own output becomes repetitive, contradictory, or misses obvious pipeline state), or (b) the pipeline spans multiple days and pipeline-state.md plus context-brief.md provide sufficient recovery context."
  - Preserves the statement that pipeline state is preserved in pipeline-state.md and context-brief.md
  - Preserves the statement that Eva never forces a session break
- The "10 major agent invocations" threshold is removed (replaced by quality-based assessment)
- The "estimated context usage" check is removed (compaction handles context management)

**Estimated complexity:** Low (rewrite one subsection)

### Step 3: PreCompact Hook Script

Create a PreCompact hook script that writes a compaction marker to pipeline-state.md before compaction fires.

**Files to create:**
- `source/claude/hooks/pre-compact.sh`

**Files to modify:**
- `source/claude/hooks/enforcement-config.json` -- add PreCompact hook entry (if hook registration is config-driven)

**Acceptance criteria:**
- Script is a lightweight shell script (under 20 lines) that:
  - Reads the current pipeline-state.md
  - Appends a timestamped compaction marker: `<!-- COMPACTION: {timestamp} -->`
  - Exits 0 (never blocks compaction -- same philosophy as warn-dor-dod.sh)
  - Does NOT invoke brain, run tests, invoke subagents, or do any heavy work
  - Does NOT fail if pipeline-state.md does not exist (no-op for non-pipeline sessions)
- Hook is a PreCompact hook (fires before context is compacted, not after)
- Hook follows the existing hook pattern in `source/claude/hooks/` (see `warn-dor-dod.sh` for the warn-only pattern)
- `enforcement-config.json` updated if it tracks hook registration; otherwise hook is registered via the setup skill's settings.json generation

**Estimated complexity:** Low (lightweight shell script following established pattern)

### Step 4: Pipeline-Setup Skill Update for Compaction API Configuration

Update the pipeline-setup skill to configure the Compaction API settings and register the PreCompact hook.

**Files to modify:**
- `skills/pipeline-setup/SKILL.md` -- add Compaction API configuration step

**Acceptance criteria:**
- During setup, after hook installation and before brain setup, the setup skill:
  - Enables the PreCompact hook in `.claude/settings.json` (or equivalent hook registration)
  - Documents the Compaction API configuration in the setup summary
  - States: "Compaction API: PreCompact hook installed for pipeline state preservation"
- No user opt-in required -- this is a quality-of-life improvement, not an experimental feature
- The PreCompact hook is installed alongside existing hooks (enforce-paths.sh, enforce-sequencing.sh, enforce-git.sh, warn-dor-dod.sh)
- Setup summary includes Compaction API status

**Estimated complexity:** Low (add hook registration to existing setup flow)

### Step 5: Technical Reference and User Guide Updates (Agatha)

Update documentation to reflect the Compaction API integration.

**Files to modify:**
- `docs/guide/technical-reference.md` -- update Context Hygiene / Compaction Strategy section
- `docs/guide/user-guide.md` -- update context cleanup advisory description

**Acceptance criteria:**
- Technical reference reflects the updated Compaction Strategy (server-side compaction, PreCompact hook, phase-transition writes)
- User guide reflects the updated advisory behavior (no more "suggest fresh session after 10 handoffs")
- Both documents mention that pipeline-state.md remains the cross-session recovery mechanism
- Both documents mention that path-scoped rules survive compaction (existing ADR-0004 reference preserved)

**Estimated complexity:** Low (update two prose sections to match new behavior)

## Comprehensive Test Specification

### Step 1 Tests: Compaction Strategy Update

| ID | Category | Description |
|----|----------|-------------|
| T-0012-001 | Happy | `source/references/pipeline-operations.md` Compaction Strategy subsection mentions "Compaction API" and "context_management.edits" |
| T-0012-002 | Happy | Subsection states path-scoped rules survive compaction with explicit reference to ADR-0004 |
| T-0012-003 | Happy | Subsection states Eva writes pipeline-state.md at every phase transition as the primary compaction safety net |
| T-0012-004 | Happy | Subsection states brain captures provide secondary recovery path when available |
| T-0012-005 | Regression | Existing bullet "Between major phases: start fresh subagent sessions" is preserved |
| T-0012-006 | Regression | Existing bullet about Colby+Roz interleaving (fresh context per unit) is preserved |
| T-0012-007 | Regression | Agent Teams teammate note (fresh context per task) is preserved |
| T-0012-008 | Regression | "Never carry Roz reports in Eva's context" rule is preserved |
| T-0012-009 | Failure | The "60% context usage" trigger is removed -- no reference to percentage-based context monitoring |
| T-0012-010 | Boundary | New "20+ agent handoffs" quality-based advisory mentioned as fallback for very large pipelines |

### Step 2 Tests: Context Cleanup Advisory Update

| ID | Category | Description |
|----|----------|-------------|
| T-0012-011 | Happy | `source/rules/pipeline-orchestration.md` Context Cleanup Advisory references server-side compaction |
| T-0012-012 | Happy | Advisory states Eva does not suggest session breaks based on handoff counts |
| T-0012-013 | Happy | Advisory preserves "Eva never forces a session break" |
| T-0012-014 | Happy | Advisory lists quality-based triggers for fresh session suggestion (response degradation, multi-day pipeline) |
| T-0012-015 | Failure | The "10 major agent invocations" threshold is removed -- no reference to counting handoffs |
| T-0012-016 | Failure | The "estimated context usage" check is removed -- no reference to estimating context percentage |
| T-0012-017 | Regression | Pipeline-state.md and context-brief.md mentioned as recovery mechanisms |

### Step 3 Tests: PreCompact Hook Script

| ID | Category | Description |
|----|----------|-------------|
| T-0012-018 | Happy | `source/claude/hooks/pre-compact.sh` exists and is executable |
| T-0012-019 | Happy | Script appends a timestamped compaction marker (`<!-- COMPACTION: ... -->`) to pipeline-state.md |
| T-0012-020 | Happy | Script exits 0 (never blocks compaction) |
| T-0012-021 | Failure | Script is a no-op (exits 0, no error) when pipeline-state.md does not exist |
| T-0012-022 | Failure | Script does not invoke brain, run tests, or invoke subagents (grep for `agent_capture`, `agent_search`, test commands) |
| T-0012-023 | Boundary | Script is under 20 lines |
| T-0012-024 | Regression | Existing hooks (enforce-paths.sh, enforce-sequencing.sh, enforce-git.sh, warn-dor-dod.sh) are unchanged |
| T-0012-025 | Security | Script does not write to any file outside the pipeline state directory |

### Step 4 Tests: Pipeline-Setup Skill Update

| ID | Category | Description |
|----|----------|-------------|
| T-0012-026 | Happy | `skills/pipeline-setup/SKILL.md` includes a step for PreCompact hook registration |
| T-0012-027 | Happy | Setup installs pre-compact.sh alongside existing hooks |
| T-0012-028 | Happy | Setup summary includes Compaction API status |
| T-0012-029 | Failure | No user opt-in prompt for Compaction API (unlike Sentinel and Agent Teams, this is not experimental) |
| T-0012-030 | Regression | Existing setup steps are unchanged (Sentinel opt-in, Agent Teams opt-in, brain setup) |

### Step 5 Tests: Documentation Updates

| ID | Category | Description |
|----|----------|-------------|
| T-0012-031 | Happy | `docs/guide/technical-reference.md` Context Hygiene section references Compaction API |
| T-0012-032 | Happy | `docs/guide/user-guide.md` context cleanup advisory reflects new behavior |
| T-0012-033 | Regression | Both docs preserve pipeline-state.md as cross-session recovery mechanism |
| T-0012-034 | Regression | Both docs preserve ADR-0004 path-scoped rules compaction resilience reference |

### Step 1 Telemetry

Telemetry: Log line "Compaction API: context managed server-side" in Eva's boot announcement when compaction is active. Trigger: every session start with compaction enabled. Absence means: compaction is not configured or the setting is not being read.

### Step 2 Telemetry

Telemetry: Absence of "suggest fresh session" messages during pipelines under 20 handoffs. Trigger: Eva should NOT emit context-based session break suggestions during normal-length pipelines. Absence of absence means: the old advisory logic was not removed.

### Step 3 Telemetry

Telemetry: `<!-- COMPACTION: {timestamp} -->` marker in pipeline-state.md after a compaction event. Trigger: PreCompact hook fires. Absence means: PreCompact hook did not fire or pipeline-state.md did not exist.

### Step 4 Telemetry

Telemetry: "Compaction API: PreCompact hook installed" in setup summary. Trigger: pipeline-setup completion. Absence means: setup skill was not updated.

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `pre-compact.sh` (hook) | Appends `<!-- COMPACTION: {ISO timestamp} -->` to pipeline-state.md | Eva boot sequence (reads pipeline-state.md) | Step 3 produces, Step 1 documents the recovery read |
| `pipeline-operations.md` Compaction Strategy section | Prose rules for Eva's compaction behavior | Eva runtime (loaded via path-scoped rules when reading `docs/pipeline/`) | Step 1 produces, consumed at runtime |
| `pipeline-orchestration.md` Context Cleanup Advisory | Prose rules for when Eva suggests session breaks | Eva runtime (always-loaded via path-scoped rules) | Step 2 produces, consumed at runtime |
| `pipeline-setup SKILL.md` hook registration | Hook entry in `.claude/settings.json` | Claude Code hook system (fires PreCompact) | Step 4 produces, Claude Code consumes |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `pre-compact.sh` | Compaction marker in pipeline-state.md | Eva boot sequence / pipeline-state.md reader | Step 3 -> Step 1 (documented recovery path) |
| Compaction Strategy (pipeline-operations.md) | Behavioral rules | Eva runtime | Step 1 -> runtime |
| Context Cleanup Advisory (pipeline-orchestration.md) | Behavioral rules | Eva runtime | Step 2 -> runtime |
| Hook registration (SKILL.md) | settings.json entry | Claude Code PreCompact hook system | Step 4 -> Claude Code |
| Technical reference + user guide updates | User-facing docs | Human readers | Step 5 -> users |

No orphan producers. Every artifact has a consumer.

## Blast Radius

### Files Modified

| File | Section Changed | Impact |
|------|----------------|--------|
| `source/references/pipeline-operations.md` | `### Compaction Strategy` within `<section id="context-hygiene">` | Eva's context management behavior during pipelines |
| `source/rules/pipeline-orchestration.md` | `### Context Cleanup Advisory` within `<section id="pipeline-flow">` | Eva's session break suggestion behavior |
| `skills/pipeline-setup/SKILL.md` | Hook installation section | Setup flow gains one hook |
| `docs/guide/technical-reference.md` | Context Hygiene section | Documentation only |
| `docs/guide/user-guide.md` | Context cleanup advisory description | Documentation only |

### Files Created

| File | Purpose |
|------|---------|
| `source/claude/hooks/pre-compact.sh` | PreCompact hook for pipeline state preservation |

### Files NOT Changed (verified)

- `source/rules/default-persona.md` -- boot sequence reads pipeline-state.md already; no changes needed
- `source/rules/agent-system.md` -- no compaction-related content
- `source/claude/hooks/enforce-paths.sh` -- no path enforcement changes
- `source/claude/hooks/enforce-sequencing.sh` -- no sequencing changes
- `source/claude/hooks/enforce-git.sh` -- no git enforcement changes
- `source/claude/hooks/warn-dor-dod.sh` -- no DoR/DoD changes
- `.claude/` anything -- changes target `source/` only
- Brain schema -- no database changes

### CI/CD Impact

None. No new dependencies, no new test commands, no build changes.

## Migration & Rollback

### Migration Plan

1. Colby creates `source/claude/hooks/pre-compact.sh`
2. Colby updates `source/references/pipeline-operations.md` Compaction Strategy
3. Colby updates `source/rules/pipeline-orchestration.md` Context Cleanup Advisory
4. Colby updates `skills/pipeline-setup/SKILL.md` for hook registration
5. Agatha updates `docs/guide/technical-reference.md` and `docs/guide/user-guide.md`
6. Existing projects pick up changes on next `/pipeline-setup` run (setup resync copies `source/` to `.claude/`)

### Rollback Strategy

Revert the commit. The pipeline continues to function with the old manual `/compact` advisory behavior. The PreCompact hook is inert if reverted (Claude Code ignores unregistered hooks). No data loss -- pipeline-state.md is additive (compaction markers are HTML comments, ignored by readers).

### Rollback Window

Indefinite. Changes are behavioral documentation and a lightweight hook. No data migration, no schema changes, no state format changes.

## Notes for Colby

1. **pre-compact.sh must be trivially simple.** The entire script should be: check if pipeline-state.md exists, append a compaction marker, exit 0. No conditionals beyond the existence check. No brain calls. No subprocess invocations. Reference `warn-dor-dod.sh` for the warn-only pattern (always exit 0).

2. **The pipeline-state.md path.** The hook needs to know where pipeline-state.md lives. In installed projects this is `docs/pipeline/pipeline-state.md` relative to the project root. The hook should use `$CLAUDE_PROJECT_DIR` or equivalent to find the project root, falling back to the current working directory.

3. **Compaction marker format.** Use `<!-- COMPACTION: $(date -u +%Y-%m-%dT%H:%M:%SZ) -->` -- an HTML comment that is invisible to markdown readers but detectable by Eva's boot sequence if needed for debugging.

4. **The "10 major handoffs" and "60% context" numbers are in two files.** The count-based threshold is in `pipeline-orchestration.md` (Context Cleanup Advisory). The percentage-based threshold is in `pipeline-operations.md` (Compaction Strategy). Both must be updated. The Agent Teams note about counting teammate completions individually should be updated to reflect that compaction handles this automatically now.

5. **Preserve surrounding content carefully.** Both the Context Hygiene section and the Context Cleanup Advisory are surrounded by other sections. Only the specific subsections noted in the acceptance criteria should change. The XML section tags and surrounding sections must be preserved exactly.

6. **Hook registration in settings.json.** Check how existing hooks are registered in the setup skill. The PreCompact hook follows the same pattern. Claude Code's hook types include `PreCompact` and `PostCompact` -- we use `PreCompact` only.

7. **Brain context from this ADR session.** The brain contains a lesson about the auto-compact infinite retry bug (Claude Code issue #22758). This is relevant background but does not affect implementation -- server-side compaction is a different mechanism. Do not over-engineer safeguards against a bug that applies to client-side compaction only.

## DoD: Verification Table

| # | Requirement | Covered By | Notes |
|---|-------------|------------|-------|
| R1 | Enable Compaction API for Eva's session | Step 1 (strategy docs), Step 4 (setup) | Configuration documented; setup enables |
| R2 | Remove manual `/compact` handling | Step 1 (remove 60% trigger), Step 2 (remove 10-handoff threshold) | Both manual triggers removed |
| R3 | pipeline-state.md remains cross-session recovery | Step 1 (explicitly preserved), Step 3 (PreCompact writes to it) | Compaction is within-session only -- stated in Step 1 |
| R4 | Document Eva's state preservation around compaction | Step 1 (full strategy), Step 3 (PreCompact hook) | Phase-transition writes + PreCompact hook |
| R5 | Document what Eva must write to pipeline-state.md | Step 1 (strategy), existing behavior (phase transition writes) | No new writes needed -- existing behavior is sufficient |
| R6 | Update context cleanup advisory | Step 2 (rewrite advisory) | Handoff-counting replaced by quality-based assessment |
| R7 | PreCompact/PostCompact hook consideration | Step 3 (PreCompact hook), A3 (PostCompact considered, deferred) | PreCompact chosen; PostCompact deferred with rationale |
| R8 | Changes target source/ only | All steps | Verified: all modifications in `source/`, `skills/`, `docs/guide/` |
| R9 | Non-code ADR | All steps | Roz test spec/authoring skipped; Colby implements, Roz verifies |
| R10 | Relationship to #10 documented | Context section | Explicitly documented as complementary, independent |

### Architectural Decisions Not in Spec

- **PreCompact over PostCompact:** The spec mentioned both. This ADR chose PreCompact as the primary mechanism and deferred PostCompact. Rationale: PreCompact saves state before loss; PostCompact would re-inject after loss but path-scoped rules already handle that.
- **Quality-based advisory over count-based:** The spec said "remove manual /compact handling." This ADR replaced the count-based threshold (10 handoffs) with a quality-based assessment (visible degradation, multi-day pipelines) rather than eliminating the advisory entirely. Rationale: very large pipelines may still benefit from a fresh session even with compaction.
- **20-handoff fallback threshold:** New number not in the spec. This is a soft heuristic, not a hard gate. It exists because compacted context quality degrades with scale even when compaction is working correctly.

### Rejected Alternatives

- A1 (status quo) rejected: user friction on large pipelines
- A2 (full state serialization every turn) rejected: retro lesson #003 pattern (expensive work on every event)
- A3 (PostCompact hook) deferred: path-scoped rules already handle critical content re-injection

### Technical Constraints Discovered

- Compaction API operates server-side, so the infinite retry bug (issue #22758) does not apply -- that was a client-side Claude Code issue with spawning compact agents
- PreCompact hook timing is an assumption -- if compaction fires before hooks, the hook is inert. Mitigated by existing phase-transition writes to pipeline-state.md
- Subagent contexts are unaffected by compaction (fresh per invocation) -- confirmed by brain context
