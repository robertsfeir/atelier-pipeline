## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Closed enum of named stop reasons written by Eva on every terminal pipeline transition | ADR-0028, R1 |
| 2 | Minimum enum values: `completed_clean`, `roz_blocked`, `user_cancelled`, `hook_violation`, `budget_threshold_reached`, `brain_unavailable`, `session_crashed`, `scope_changed` | ADR-0028, R2 |
| 3 | `stop_reason` field added to pipeline-state.md template | ADR-0028, R3 |
| 4 | Eva writes `stop_reason` on every terminal transition | ADR-0028, R4 |
| 5 | T3 telemetry gains a `stop_reason` field | ADR-0028, R5 |
| 6 | Darwin can filter by stop reason across pipeline history via `agent_search` on T3 metadata | ADR-0028, R6 |
| 7 | Upgrade safety: absent `stop_reason` read as `legacy_unknown`, no crash | ADR-0028, R9 |
| 8 | `session_crashed` is inferred retroactively at next session boot (never written in real time) | ADR-0028, Decision |
| 9 | Extension rule: new stop reasons added only via a new superseding ADR, never invented at runtime | ADR-0028, Decision |

**Retro risks:** None directly applicable. The stop reason enum is a data contract — enum values are string literals in markdown, verified by grep.

---

# Feature Spec: Named Stop Reason Taxonomy

**Author:** Robert (CPO) | **Date:** 2026-04-12
**Status:** Draft
**ADR:** [ADR-0028](../architecture/ADR-0028-named-stop-reason-taxonomy.md)

## The Problem

Every pipeline run ends in a terminal state, but Eva currently records only `phase: idle` in pipeline-state.md when a pipeline completes. There is no structured record of why the pipeline ended. A clean completion, a user cancellation, a Roz blocker that halted progress, and a session crash all look identical in pipeline-state.md after the fact.

This gap has three consequences:

1. **Session recovery ambiguity.** When Eva boots into a stale pipeline, she cannot distinguish "user cancelled mid-build" from "session crashed during QA" from "Roz blocked and user never returned." These require different recovery strategies.

2. **Telemetry blindness.** T3 per-pipeline captures record cost, duration, and rework rate, but not outcome. A pipeline that cost $5 and completed cleanly is indistinguishable from one that cost $5 and was abandoned due to scope change.

3. **Pattern detection gaps.** If 3 of the last 5 pipelines ended with `roz_blocked`, that is a signal Darwin should surface. Today that signal is invisible.

## Personas

**Eva (orchestrator):** Writes `stop_reason` at every terminal pipeline transition.

**Darwin:** Queries T3 metadata for stop reason distribution to surface patterns like "3 of last 5 pipelines ended with roz_blocked."

**Pipeline operators:** See the stop reason in the Pipeline Complete report so they know how the pipeline ended at a glance.

**Session recovery:** `session-boot.sh` uses the stop reason to distinguish crash from cancellation from completion when booting into a stale pipeline.

## Stop Reason Enum

The following values are the complete, closed set. Eva writes exactly one of these values at every terminal transition. Eva does not invent new values at runtime.

| Value | When Eva writes it |
|-------|-------------------|
| `completed_clean` | Pipeline reaches Ellis final commit/push successfully |
| `completed_with_warnings` | Pipeline completes but accepted Agatha divergence or Robert/Sable DRIFT was not fixed |
| `roz_blocked` | Roz BLOCKER that the user chose not to fix, or loop-breaker (gate 12) fired and user abandoned |
| `user_cancelled` | User explicitly says "stop", "cancel", "abandon" during an active pipeline |
| `hook_violation` | A PreToolUse hook blocks an agent action that cannot be retried, and user abandons |
| `budget_threshold_reached` | User declines to proceed after seeing the token budget estimate gate |
| `brain_unavailable` | Pipeline requires brain (e.g., Darwin auto-trigger) and brain is down; user abandons |
| `session_crashed` | Inferred at next session boot when a stale pipeline has no `stop_reason` |
| `scope_changed` | Cal discovers scope-changing information and user decides to re-plan rather than continue |
| `legacy_unknown` | Read-only sentinel for pre-ADR-0028 pipelines that lack the field (never written by Eva) |

## Acceptance Criteria

**State field:**
- AC-1: `pipeline-state.md` template MUST contain a `**Stop Reason:**` markdown field with a placeholder value indicating the pipeline is active.
- AC-2: The PIPELINE_STATUS JSON comment in `pipeline-state.md` MUST contain a `stop_reason` key.
- AC-3: Eva MUST write `stop_reason` to both the markdown field and the PIPELINE_STATUS JSON at every terminal transition.

**Enum completeness:**
- AC-4: Eva MUST write a value from the defined enum at every terminal transition. No terminal transition to idle MUST exist in Eva's orchestration rules without a corresponding `stop_reason` write.
- AC-5: The enum MUST contain exactly the 10 values listed above: `completed_clean`, `completed_with_warnings`, `roz_blocked`, `user_cancelled`, `hook_violation`, `budget_threshold_reached`, `brain_unavailable`, `session_crashed`, `scope_changed`, `legacy_unknown`.
- AC-6: Eva MUST NOT invent stop reason values at runtime. New values require a new superseding ADR.

**Session recovery:**
- AC-7: When `session-boot.sh` detects a stale pipeline (non-idle phase) with no `stop_reason`, it MUST infer `session_crashed` and include this in the boot state output.
- AC-8: When `stop_reason` is absent from PIPELINE_STATUS on any pipeline-state.md (e.g., pre-ADR-0028 file), Eva MUST treat it as `legacy_unknown` without crashing or raising an error.

**Telemetry:**
- AC-9: The T3 telemetry capture schema MUST include a `stop_reason` field with type `string` and default `"legacy_unknown"`.
- AC-10: Eva MUST include the `stop_reason` from pipeline-state.md in the T3 brain capture metadata at pipeline end.

**Darwin integration:**
- AC-11: Darwin's persona MUST document stop reason as a queryable T3 metadata field for fitness analysis.
- AC-12: Darwin MUST treat stop reason as a supplementary fitness signal, not a primary classification axis (primary remains QA rate and rework rate).

**Pipeline Complete report:**
- AC-13: The Pipeline Complete report format MUST include `**Stop Reason:** {stop_reason}` in the final report table.

**Data integrity:**
- AC-14: `session_crashed` MUST only be written by the session-boot inference process, never by Eva directly at pipeline end.
- AC-15: `legacy_unknown` MUST be a read-only sentinel value — Eva MUST NOT write it as a stop reason.

## Edge Cases

**Session crash (Eva cannot write):** Eva cannot write to disk during a crash. `session_crashed` is always inferred retroactively at the next session boot by detecting a stale pipeline (non-idle phase without `stop_reason`). This is a design constraint, not a gap.

**Multiple terminal transitions (should not occur):** The PIPELINE_STATUS JSON comment is overwritten, not appended, on every state update. If Eva mistakenly writes idle twice, the second write wins. The stop reason from the last write persists.

**Brain unavailable at terminal transition:** `stop_reason` is written to `pipeline-state.md` (local file), not only to the brain. Session recovery works without brain. The T3 brain capture is the optional durability layer.

**Pre-ADR-0028 pipelines in brain:** T3 captures from before this ADR lack `stop_reason` in metadata. Darwin queries treat absent field and `legacy_unknown` identically.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Closed enum on every terminal transition | Done | Terminal transition protocol in pipeline-orchestration.md lists all 10 values with trigger conditions |
| 2 | All 10 enum values present | Done | State transition table covers all active phases reaching idle |
| 3 | `stop_reason` in pipeline-state.md template | Done | Both markdown field and PIPELINE_STATUS JSON key |
| 4 | Eva writes `stop_reason` at every terminal transition | Done | Terminal transition protocol in pipeline-orchestration.md |
| 5 | T3 telemetry gains `stop_reason` | Done | telemetry-metrics.md T3 table includes field |
| 6 | Darwin can filter by stop reason | Done | darwin.md Stop Reason Signals section |
| 7 | `session_crashed` inferred at boot for stale pipelines | Done | session-boot.md inference rule |
| 8 | Upgrade safety for absent field | Done | `legacy_unknown` sentinel; no crash on missing field |
| 9 | Pipeline Complete report includes stop reason | Done | pipeline.md Final Report table |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled — no TBD, no placeholders
