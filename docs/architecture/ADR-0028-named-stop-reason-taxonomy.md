# ADR-0028: Named Stop Reason Taxonomy

## DoR: Requirements Extracted

**Sources:** User task description (Feature A), `source/shared/pipeline/pipeline-state.md` (template),
`source/shared/rules/pipeline-orchestration.md` (terminal transitions), `source/shared/references/telemetry-metrics.md`
(T3 schema), `source/shared/agents/darwin.md` (pattern detection), `source/shared/references/pipeline-operations.md`
(PIPELINE_STATUS marker format), `docs/pipeline/pipeline-state.md` (live instance showing actual Eva write format),
`.claude/references/retro-lessons.md`

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Closed enum of named stop reasons written by Eva on every terminal pipeline transition | Task spec | Feature A, paragraph 1 |
| R2 | Minimum enum values: `completed_clean`, `roz_blocked`, `user_cancelled`, `hook_violation`, `budget_threshold_reached`, `brain_unavailable`, `session_crashed`, `scope_changed` | Task spec | Feature A, enum list |
| R3 | `stop_reason` field added to pipeline-state.md template | Task spec | Feature A, "Where it lands" bullet 1 |
| R4 | Eva's orchestration writes `stop_reason` on every terminal transition | Task spec | Feature A, "Where it lands" bullet 2 |
| R5 | T3 telemetry gains a `stop_reason` field | Task spec | Feature A, "Where it lands" bullet 3 |
| R6 | Darwin can filter by stop reason across pipeline history via `agent_search` on T3 metadata | Task spec | Feature A, "Where it lands" bullet 4 |
| R7 | Every terminal pipeline-state.md has a `stop_reason` field from the defined enum | Task spec | Feature A, acceptance criteria 1 |
| R8 | `agent_search` can filter by stop reason (T3 metadata field, no brain schema changes) | Task spec | Feature A, acceptance criteria 3 |
| R9 | Upgrade safety: absent `stop_reason` read as `legacy_unknown`, no crash | Task spec | Feature A, acceptance criteria 4 |

**Retro risks:**
- **Lesson #005 (Frontend Wiring Omission):** Stop reason is a producer (Eva writes) with consumers (T3 telemetry, Darwin, session recovery). All consumers must be wired in the same or adjacent steps. Verified: Step 1 produces, Step 2 consumes.
- **Lesson #001 (Sensitive Data in Return Shapes):** Stop reason is operational metadata, not sensitive. Tagged `public-safe`.

**Spec challenge:** The spec assumes Eva reliably reaches every terminal transition point to write `stop_reason`. If wrong (session crash, context window overflow, forced quit), the design fails because `stop_reason` is never written, leaving pipeline-state.md in a non-terminal state without a reason. **Mitigation:** `session_crashed` is the fallback -- `session-boot.sh` detects stale pipelines at session start (existing `stale_context` detection) and can infer `session_crashed` when a pipeline is in a non-terminal phase without a `stop_reason`. This is already partially handled by existing stale pipeline detection. The design accounts for this by having the hydrator treat absent `stop_reason` on a stale pipeline as `session_crashed` rather than requiring Eva to write it at crash time (which is impossible).

**SPOF:** Eva's state write to pipeline-state.md at terminal transition. Failure mode: Eva's context is exhausted or session ends before the write completes. Graceful degradation: `session-boot.sh` already detects stale pipelines (phase != idle, stale_context flag). A missing `stop_reason` on a stale pipeline is inferred as `session_crashed` at next boot. Pre-ADR-0028 pipelines lack the field entirely and are read as `legacy_unknown`.

**Anti-goals:**

1. Anti-goal: Stop reason as a PreToolUse hook enforcement (blocking agent invocations when pipeline-state.md lacks a stop_reason at terminal transition). Reason: The stop_reason write is a single field addition to Eva's existing terminal state write. Hook enforcement would require parsing pipeline-state.md on every tool call to verify stop_reason presence, which is disproportionate overhead for a behavioral field that Eva already writes at the same moment she writes `phase: idle`. Revisit: If Eva demonstrably skips writing stop_reason on 3+ pipelines (tracked via Darwin or retro).

2. Anti-goal: Automated remediation based on stop reason (e.g., auto-retry on `brain_unavailable`). Reason: Stop reasons are diagnostic signals, not triggers. Automated remediation changes pipeline control flow and requires separate design for each reason. Revisit: If Darwin proposes remediation strategies and the user wants automated retry for specific stop reasons.

3. Anti-goal: Per-phase stop reasons (capturing why each phase ended, not just the pipeline). Reason: Per-phase granularity multiplies the state surface without clear consumer demand. T1/T2 telemetry already captures per-invocation outcomes. The pipeline-level stop reason is the missing piece. Revisit: If Darwin analysis shows that pipeline-level stop reasons are insufficient to diagnose recurring failure patterns.

---

## Status

Proposed

## Context

Every pipeline run ends in one of several terminal states, but Eva currently records only `phase: idle` in pipeline-state.md when a pipeline completes. There is no structured record of *why* the pipeline ended. A clean completion, a user cancellation, a Roz blocker that halted progress, and a session crash all look identical in pipeline-state.md after the fact.

This gap has three consequences:

1. **Session recovery ambiguity.** When Eva boots into a stale pipeline, she cannot distinguish "user cancelled mid-build" from "session crashed during QA" from "Roz blocked and user never returned." All three require different recovery strategies.

2. **Telemetry blindness.** T3 per-pipeline captures (telemetry-metrics.md) record cost, duration, rework rate, and EvoScore, but not outcome. A pipeline that cost $5 and completed cleanly is indistinguishable from one that cost $5 and was abandoned due to scope change. Darwin cannot filter "show me pipelines that failed due to QA blockers" because the stop reason is not in the T3 metadata.

3. **Pattern detection gaps.** Error-patterns.md captures *what went wrong*, but not *how the pipeline ended*. If 3 of the last 5 pipelines ended with `roz_blocked`, that is a signal Darwin should surface. Today, that signal is invisible.

The existing PIPELINE_STATUS JSON comment in pipeline-state.md (line 6 of the live instance) already carries structured fields (`phase`, `sizing`, `roz_qa`, `telemetry_captured`). The `stop_reason` field joins this set as a terminal-transition marker.

## Decision

Add a closed `stop_reason` enum to Eva's terminal pipeline transition protocol. Eva writes the field to pipeline-state.md as both a markdown field and a PIPELINE_STATUS JSON value. The T3 telemetry capture includes `stop_reason` in its metadata for brain queryability.

### Stop Reason Enum

| Value | When Eva writes it | Terminal? |
|-------|-------------------|-----------|
| `completed_clean` | Pipeline reaches Ellis final commit/push successfully | Yes |
| `completed_with_warnings` | Pipeline completes but Agatha divergence report or Robert/Sable DRIFT was accepted (not fixed) | Yes |
| `roz_blocked` | Roz BLOCKER that the user chose not to fix, or loop-breaker (gate 12) fired | Yes |
| `user_cancelled` | User explicitly says "stop", "cancel", "abandon" during an active pipeline | Yes |
| `hook_violation` | A PreToolUse hook blocks an agent action that cannot be retried (e.g., path violation) and user abandons | Yes |
| `budget_threshold_reached` | User declines to proceed after token budget estimate gate (ADR-0029) | Yes |
| `brain_unavailable` | Pipeline requires brain (e.g., Darwin auto-trigger) and brain is down; user abandons rather than continuing baseline | Yes |
| `session_crashed` | Inferred at next session boot when a stale pipeline has no `stop_reason` | Yes (retroactive) |
| `scope_changed` | Cal discovers scope-changing information and user decides to re-plan rather than continue | Yes |
| `legacy_unknown` | Read-only sentinel for pre-ADR-0028 pipelines that lack the field | N/A (inferred) |

**Extension rule:** New stop reasons are added by appending to this table in a new ADR that supersedes the enum section. The enum is closed within each ADR version -- Eva does not invent reasons at runtime.

### State Transition Table

| Current Phase | Trigger | Stop Reason | Next State |
|--------------|---------|-------------|------------|
| Any active phase | Ellis final commit succeeds | `completed_clean` | idle |
| Any active phase | Ellis final commit succeeds + accepted drift/divergence | `completed_with_warnings` | idle |
| build / review | Roz BLOCKER + user abandons, or gate 12 fires + user abandons | `roz_blocked` | idle |
| Any active phase | User says "stop" / "cancel" / "abandon" | `user_cancelled` | idle |
| Any active phase | Hook blocks + unrecoverable + user abandons | `hook_violation` | idle |
| pre-pipeline (sizing) | User declines after budget estimate gate | `budget_threshold_reached` | idle |
| Any active phase | Brain required + unavailable + user abandons | `brain_unavailable` | idle |
| Any active phase | Session ends without clean transition | `session_crashed` (inferred at boot) | stale -> idle |
| architecture | Cal scope-changing discovery + user re-plans | `scope_changed` | idle |

**Stuck states:** None by design. Every non-idle phase has at least one trigger that transitions to idle with a stop reason. The `session_crashed` inference covers the case where Eva cannot write a stop reason (session death). The only state that persists across sessions is `stale` (detected by session-boot.sh), which is resolved to `session_crashed` at boot.

**Silent upserts:** The PIPELINE_STATUS JSON comment is overwritten (not appended) on every state update. This is existing behavior. The `stop_reason` field follows the same pattern -- it is set once at terminal transition and persists until the next pipeline starts and resets the state.

## Alternatives Considered

**Alternative A: Free-form stop reason string.** Eva writes a natural language description of why the pipeline ended. Rejected: not queryable, not filterable, not machine-parseable. Darwin cannot `agent_search` with `filter: { stop_reason: 'roz_blocked' }` against free-form text. The enum is the right abstraction for a finite, well-defined set of terminal states.

**Alternative B: Stop reason in PIPELINE_STATUS JSON only (no markdown field).** Simpler to implement but invisible to human readers scanning pipeline-state.md. The markdown field (`**Stop Reason:** completed_clean`) is human-readable; the JSON field is machine-readable. Both are cheap to write. Rejected for human readability.

**Alternative C: Stop reason as a brain-only capture (not in pipeline-state.md).** Requires brain availability for session recovery, which contradicts the brain-as-optional design principle. Rejected because session recovery must work without brain.

## Consequences

**Positive:**
- Session recovery can distinguish crash from cancellation from completion
- T3 telemetry includes structured outcome, enabling Darwin pattern detection ("3 of last 5 pipelines ended with roz_blocked")
- `agent_search` filter on `stop_reason` works immediately (T3 metadata field, no brain schema changes)
- Upgrade-safe: absent field reads as `legacy_unknown`, no crash

**Negative:**
- Eva must remember to write `stop_reason` at every terminal transition point (8 distinct code paths in pipeline-orchestration.md). Mitigation: the behavioral burden is low because Eva already writes pipeline-state.md at terminal transitions -- this adds one field to existing writes.
- `session_crashed` is always inferred retroactively, never written in real time. This is a design limitation, not a bug -- Eva cannot write to disk during a crash.

**Neutral:**
- `legacy_unknown` is a permanent sentinel in the system. Pre-ADR-0028 T3 captures in the brain will always lack `stop_reason`. Darwin must treat absent and `legacy_unknown` identically.

---

## Implementation Plan

### Step 1: Schema additions and terminal transition protocol (pipeline-state.md template + orchestration rules + T3 telemetry)

**Files to modify:**
1. `source/shared/pipeline/pipeline-state.md` -- add `stop_reason` field with default placeholder
2. `source/shared/rules/pipeline-orchestration.md` -- add terminal transition protocol section documenting when Eva writes each stop reason value
3. `source/shared/references/telemetry-metrics.md` -- add `stop_reason` field to T3 table
4. `source/shared/references/pipeline-operations.md` -- add `stop_reason` to PIPELINE_STATUS field table; add upgrade safety rule for absent field

**Files to create:** None

**Acceptance criteria:**
- pipeline-state.md template includes `**Stop Reason:** (none -- pipeline active)` placeholder and `stop_reason` in PIPELINE_STATUS JSON comment
- Pipeline-orchestration.md has a `<protocol id="terminal-transition">` section listing each stop reason, its trigger condition, and the state write procedure
- T3 table in telemetry-metrics.md includes `stop_reason | string | From pipeline-state.md at terminal transition | "legacy_unknown"`
- PIPELINE_STATUS field table in pipeline-operations.md includes `stop_reason` with type, description, and default
- Upgrade safety rule documented: absent `stop_reason` in PIPELINE_STATUS reads as `legacy_unknown`; `session_crashed` inferred when `stale_context: true` and no `stop_reason` present
- Enum values are exactly the 10 listed in the Decision section
- No new files created; all changes are additions to existing files

**Complexity:** Low. Four file edits, all additive (new sections/rows, no restructuring). Total ~60 lines of markdown additions.

**After this step, I can:** see the stop reason enum defined in the pipeline template, understand when each reason fires from the orchestration rules, and find the stop reason in T3 telemetry captures.

### Step 2: Darwin integration and session-boot inference (darwin.md + session-boot references)

**Files to modify:**
1. `source/shared/agents/darwin.md` -- add stop reason as a fitness signal (Darwin can query T3 for `stop_reason` distribution and flag patterns like "3+ roz_blocked in last 5 pipelines")
2. `source/shared/references/session-boot.md` -- add `session_crashed` inference rule: when `stale_context: true` and pipeline has no `stop_reason`, session-boot reports `stop_reason: session_crashed`
3. `source/shared/commands/pipeline.md` -- add `stop_reason` to the Pipeline Complete report format

**Files to create:** None

**Acceptance criteria:**
- Darwin's persona includes a "Stop Reason Signals" section describing how to query and interpret stop reason distribution in T3 telemetry
- Session-boot.md includes a rule: "If pipeline is stale (non-idle phase without stop_reason), infer `session_crashed` and include in boot state"
- Pipeline Complete report format includes `**Stop Reason:** {stop_reason}` in the final report table
- Darwin's workflow references stop reason as a supplementary fitness signal (not a primary classification axis -- primary remains QA rate and rework rate)
- No brain schema changes anywhere

**Complexity:** Low. Three file edits, all additive. Total ~30 lines of markdown additions.

**After this step, I can:** see Darwin use stop reason patterns in fitness analysis, see session-boot infer `session_crashed` for stale pipelines, and see the stop reason in the Pipeline Complete report.

---

## Test Specification

| ID | Category | Description |
|----|----------|-------------|
| T-0028-001 | Schema | pipeline-state.md template contains `stop_reason` placeholder field |
| T-0028-002 | Schema | pipeline-state.md template PIPELINE_STATUS JSON comment contains `stop_reason` key |
| T-0028-003 | Schema | T3 table in telemetry-metrics.md contains `stop_reason` row with type `string` and default `"legacy_unknown"` |
| T-0028-004 | Schema | PIPELINE_STATUS field table in pipeline-operations.md contains `stop_reason` row |
| T-0028-005 | Enum completeness | Orchestration rules list exactly 10 stop reason values: `completed_clean`, `completed_with_warnings`, `roz_blocked`, `user_cancelled`, `hook_violation`, `budget_threshold_reached`, `brain_unavailable`, `session_crashed`, `scope_changed`, `legacy_unknown` |
| T-0028-006 | Enum closure | No stop reason value outside the defined enum appears in any source file |
| T-0028-007 | Trigger coverage | Each non-inferred stop reason (all except `session_crashed` and `legacy_unknown`) has a documented trigger condition in the terminal transition protocol |
| T-0028-008 | Trigger coverage | `session_crashed` has a documented inference rule in session-boot.md |
| T-0028-009 | Upgrade safety | pipeline-operations.md documents that absent `stop_reason` reads as `legacy_unknown` |
| T-0028-010 | Upgrade safety | session-boot.md documents that stale pipeline without `stop_reason` infers `session_crashed` |
| T-0028-011 | Failure: missing stop reason | No terminal transition in pipeline-orchestration.md transitions to idle without writing `stop_reason` |
| T-0028-012 | Failure: invalid enum value | Grep across all source/ files confirms no stop_reason value outside the defined enum |
| T-0028-013 | Failure: silent drop | Pipeline Complete report format in pipeline.md includes `stop_reason` field |
| T-0028-014 | Darwin integration | darwin.md references stop_reason as a queryable T3 metadata field |
| T-0028-015 | Darwin integration | darwin.md does NOT add stop_reason as a primary fitness classification signal (supplementary only) |
| T-0028-016 | Consistency | Every file that references `stop_reason` uses the exact enum values from the canonical list in pipeline-orchestration.md |
| T-0028-017 | Failure: orphan producer | T3 `stop_reason` field has at least one documented consumer (Darwin query, session-boot inference) |
| T-0028-018 | Negative: no brain schema | No file in `brain/` is modified |
| T-0028-019 | Negative: no new files | No new files created by this ADR |
| T-0028-020 | State transition | State transition table covers all active phases reaching idle with a stop reason |

**Test counts:** 20 total. 10 happy path, 10 failure/negative/consistency. Failure >= happy path: satisfied.

---

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| Eva (terminal transition) | `stop_reason: string` (enum value) in pipeline-state.md markdown + PIPELINE_STATUS JSON | Session recovery (session-boot.md), T3 capture, Darwin |
| Eva (T3 capture) | `metadata.stop_reason: string` in brain thought | `agent_search` filter, Darwin telemetry queries |
| session-boot.sh | `stop_reason: "session_crashed"` (inferred, added to boot JSON output) | Eva session recovery |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| pipeline-state.md template | `stop_reason` field (placeholder) | Eva state writes (pipeline-orchestration.md) | Step 1 |
| pipeline-orchestration.md terminal transition protocol | stop reason enum + trigger rules | Eva behavioral (runtime) | Step 1 |
| telemetry-metrics.md T3 row | `stop_reason: string, default "legacy_unknown"` | T3 brain capture (pipeline-orchestration.md Tier 3 protocol) | Step 1 |
| pipeline-operations.md PIPELINE_STATUS table | `stop_reason` field definition | Eva state write format (runtime) | Step 1 |
| darwin.md stop reason signals | query instructions for T3 stop_reason | Darwin agent (runtime) | Step 2 |
| session-boot.md inference rule | `session_crashed` inference logic | session-boot.sh (runtime) | Step 2 |
| pipeline.md report format | `stop_reason` in Pipeline Complete | Eva pipeline report (runtime) | Step 2 |

No orphan producers. Every producer has a documented consumer in the same or adjacent step.

---

## Data Sensitivity

| Method/Field | Classification | Rationale |
|-------------|---------------|-----------|
| `stop_reason` in pipeline-state.md | `public-safe` | Operational metadata, no PII, no secrets |
| `stop_reason` in T3 brain capture metadata | `public-safe` | Enum value, no user content |
| `session_crashed` inference | `public-safe` | Derived from pipeline phase state, no sensitive data |

---

## Notes for Colby

- **Pattern to follow:** The PIPELINE_STATUS JSON comment format is established in `docs/pipeline/pipeline-state.md` line 6. New fields are added to the JSON object inside the HTML comment. Follow the existing format exactly: `"stop_reason": "completed_clean"`.
- **Template vs live:** The *template* at `source/shared/pipeline/pipeline-state.md` is the file Colby edits. The *live* file at `docs/pipeline/pipeline-state.md` is Eva's working copy and is NOT edited by Colby.
- **Enum values are strings, not constants.** There is no code file defining these as an enum type. They are string literals documented in markdown. Colby greps to ensure consistency, not compiles.
- **The terminal transition protocol section in pipeline-orchestration.md should be placed after the existing `<gate id="mandatory-gates">` section** and before `<protocol id="observation-masking">`. It is an [ALWAYS]-loaded section (Eva needs it at any terminal transition).
- **Do not modify `session-boot.sh` (the shell script).** Step 2 modifies `session-boot.md` (the reference doc that describes boot behavior). The shell script changes are a follow-up if the inference logic needs mechanical enforcement.
- **Retro lesson #005 applies:** The stop_reason field is a data contract. Document the enum values once (pipeline-orchestration.md) and reference that canonical location everywhere else. Do not duplicate the full enum in multiple files -- reference it.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Closed enum written by Eva on every terminal transition | Done | Terminal transition protocol in pipeline-orchestration.md, Step 1 |
| R2 | Minimum enum values present | Done | 10 values defined (8 required + 2 additions: `completed_with_warnings`, `legacy_unknown`), Step 1 |
| R3 | `stop_reason` in pipeline-state.md template | Done | Step 1, file 1 |
| R4 | Eva's orchestration writes `stop_reason` | Done | Terminal transition protocol, Step 1 file 2 |
| R5 | T3 telemetry gains `stop_reason` | Done | Step 1, file 3 |
| R6 | Darwin can filter by stop reason | Done | Step 2, file 1 |
| R7 | Every terminal state has `stop_reason` | Done | State transition table covers all active phases |
| R8 | `agent_search` can filter by stop reason | Done | T3 metadata field, no brain schema changes needed |
| R9 | Upgrade safety for absent field | Done | Step 1 file 4 (pipeline-operations.md) + Step 2 file 2 (session-boot.md) |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled, no TBD, no placeholders
