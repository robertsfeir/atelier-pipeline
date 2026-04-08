# ADR-0030: Token Exposure Probe and Live Accumulator (Conditional)

## DoR: Requirements Extracted

**Sources:** Brain planning decisions (deferred from planning review), `source/shared/references/telemetry-metrics.md` (T1 schema, cost estimation table), `source/shared/rules/pipeline-orchestration.md` (telemetry capture protocol, T1 per-invocation), ADR-0029 (budget estimate gate -- anti-goal #1 references this probe), `source/claude/hooks/log-agent-stop.sh` (existing SubagentStop JSONL logging), `.claude/references/retro-lessons.md`

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Step 1 is a probe: verify whether Claude Code Agent tool exposes `input_tokens` / `output_tokens` in subagent result metadata | Task spec | ADR-0030 design constraint, bullet 1 |
| R2 | If tokens ARE exposed (Step 2a): add live token accumulation to PIPELINE_STATUS after each agent completion | Task spec | ADR-0030 design constraint, Step 2a |
| R3 | Schema already exists: `telemetry_total_cost_usd`, T1 fields in telemetry-metrics.md | Task spec | ADR-0030 design constraint, Step 2a |
| R4 | Step 2a is a behavioral change to Eva's orchestration rules only -- no new infrastructure | Task spec | ADR-0030 design constraint, Step 2a |
| R5 | If tokens NOT exposed (Step 2b): document the gap in telemetry-metrics.md, add "Token Exposure Gap" note, close ADR | Task spec | ADR-0030 design constraint, Step 2b |
| R6 | Conditional branching must be explicit in the Implementation Plan | Task spec | ADR-0030 constraint, bullet 3 |

**Retro risks:**
- **Lesson #003 (Stop Hook Race Condition):** The probe must not block anything. It is a research step, not a gate.
- **Lesson #005 (Frontend Wiring Omission):** If Step 2a fires, the accumulator (producer) must wire to its consumer (PIPELINE_STATUS, T3 capture) in the same step.

**Spec challenge:** The spec assumes the Claude Code Agent tool either reliably exposes token counts or reliably does not. If the exposure is inconsistent (some models return tokens, some do not; some invocations return tokens, some return null/0), the design fails because Step 2a's accumulator would produce partial sums labeled as totals, which is worse than "unavailable." **Mitigation:** The probe checks N >= 3 invocations across different models. If any return 0/null, the result is "not reliably exposed" and Step 2b fires. Partial exposure is treated as no exposure.

**SPOF:** The probe itself. If the probe runs but misinterprets the Agent tool's response structure (e.g., tokens are nested differently than expected), the conditional branch goes wrong. Failure mode: Step 2b fires when tokens ARE available, or Step 2a fires when they are not. Graceful degradation: Step 2a's accumulator already has fallback behavior defined in telemetry-metrics.md (tokens unavailable -> `0`, cost -> `null`). A wrong branch means either unnecessary documentation of a gap (recoverable by re-running the probe) or an accumulator that defaults to `null` (safe, same as current behavior).

**Anti-goals:**

1. Anti-goal: Building a custom token counting system (intercepting API calls, parsing response bodies, estimating from character counts). Reason: The question is specifically whether the existing Agent tool result metadata exposes tokens. If it does not, the answer is "wait for the platform to add it," not "build our own estimator." Revisit: Never -- this is a platform capability question, not a build decision.

2. Anti-goal: Enforcing a hard budget ceiling that auto-cancels pipelines mid-run. Reason: ADR-0029 explicitly deferred live enforcement to "when the Agent tool reliably exposes token counts." Even if this probe succeeds, the first iteration is an accumulator (informational), not a gate. Revisit: After the accumulator runs for 5+ pipelines and the data proves reliable.

3. Anti-goal: Modifying the SubagentStop hook (log-agent-stop.sh) to extract token data. Reason: The hook is a non-enforcement telemetry logger that deliberately avoids inspecting response content. Token accumulation belongs in Eva's behavioral layer (pipeline-orchestration.md), not in hooks. Revisit: If Eva's behavioral compliance with accumulation is demonstrably unreliable across 3+ pipelines.

---

## Status

Accepted (gap documented, closed -- Step 2b executed 2026-04-07)

**Depends on (soft):** ADR-0029 (Token Budget Estimate Gate) -- ADR-0029's anti-goal #1 explicitly defers live token accumulation to this ADR. If tokens are exposed, this ADR enables the "Track B" path that ADR-0029 left for the future.

## Context

The telemetry-metrics.md Tier 1 schema defines `input_tokens` and `output_tokens` fields with the default-when-unavailable note: "0 (log 'unavailable')". The `cost_usd` field is computed from tokens and model pricing, defaulting to `null` when tokens are unavailable. ADR-0029 was designed as "Track A" (heuristic-only) specifically because token exposure was assumed unreliable.

Nobody has actually verified whether the Claude Code Agent tool returns token counts in its result metadata. The telemetry-metrics.md documentation was written defensively with fallback defaults, but the actual runtime behavior is unknown. This ADR resolves the question with a probe and branches accordingly.

If tokens are exposed, the high-value unlock is live cost tracking: Eva can show actual spend alongside the heuristic estimate, improving the budget gate from "order-of-magnitude guess" to "order-of-magnitude guess + actual running total."

## Decision

### Conditional Architecture

```
Step 1: Probe
  |
  +-- tokens exposed reliably --> Step 2a: Build accumulator
  |
  +-- tokens NOT exposed      --> Step 2b: Document gap, close ADR
```

### Step 2a Design (if tokens exposed)

Eva's telemetry capture protocol (pipeline-orchestration.md, Tier 1 section) already defines in-memory accumulators for `total_cost`, `total_invocations`, etc. The change is:

1. After each Agent tool completion, Eva extracts `input_tokens`, `output_tokens`, and `model` from the result metadata.
2. Eva computes `cost_usd` using the cost estimation table in telemetry-metrics.md.
3. Eva updates the PIPELINE_STATUS accumulator field `telemetry_total_cost_usd` with the running sum.
4. At pipeline end, the T3 capture includes the actual `total_cost_usd` (sum of real token costs, not the heuristic estimate).

This is a behavioral change to Eva's orchestration rules. No new files, no new hooks, no schema changes.

### Step 2b Design (if tokens not exposed)

Add a "Token Exposure Gap" callout to telemetry-metrics.md documenting: what was tested, when, what the Agent tool returned, and the conclusion. Update the `input_tokens` / `output_tokens` default-when-unavailable notes to reference the gap callout. Close the ADR.

## Alternatives Considered

**Alternative A: Skip the probe, assume tokens are unavailable, close immediately.** Rejected: ADR-0029 was built on this assumption, but it was never verified. The probe is cheap (one Haiku invocation + inspection). The potential unlock (live cost tracking) justifies the cost.

**Alternative B: Build the accumulator speculatively, let it default to null if tokens are unavailable.** Rejected: Adding behavioral complexity to Eva's orchestration rules for a feature that may produce only null values is net-negative. The probe gates the investment.

## Consequences

**Positive:**
- Resolves a documented unknown in telemetry-metrics.md (tokens available or not)
- If tokens exposed: enables live cost tracking, improves ADR-0029 budget gate accuracy
- If tokens not exposed: closes the question definitively, prevents future speculation

**Negative:**
- Step 1 consumes one pipeline session to run the probe (cannot be done offline)
- Conditional branching means the ADR scope is not fully known until Step 1 completes

**Neutral:**
- The accumulator (Step 2a) or gap doc (Step 2b) are both small. Either branch is low-effort.

---

## Implementation Plan

### Step 1: Token Exposure Probe

**Files to modify:** None (this is a research step)

**Files to create:** None

**What happens:**
Colby writes a small diagnostic script (or reads existing session log files from `~/.claude/projects/*/` and `log-agent-stop.sh` JSONL output) to determine what metadata the Claude Code Agent tool returns after subagent completion. Specifically:

1. Check `log-agent-stop.sh` JSONL output (`{config_dir}/telemetry/session-hooks.jsonl`) -- does the SubagentStop event payload include token fields?
2. Check Claude Code's own session JSONL files (if they exist) for agent completion records with token metadata.
3. If neither surface exposes tokens, run a trivial Agent invocation (Explore/Haiku, "echo hello") and inspect the raw result structure.

**Probe success criteria:** At least 3 agent completion records found with non-zero `input_tokens` AND `output_tokens` values. If any return 0/null/absent, the result is "not reliably exposed."

**Acceptance criteria:**
- A written finding: "Tokens [ARE / ARE NOT] reliably exposed by the Claude Code Agent tool. Evidence: [what was checked, what was found]."
- The finding includes which fields are present, their locations in the result structure, and whether they are consistently populated.

**Complexity:** Trivial. One Haiku invocation (read files, possibly run one test invocation).

**After this step, I can:** decide whether to proceed to Step 2a or Step 2b.

### Step 2a: Live Token Accumulator (conditional -- tokens exposed)

**Gating condition:** Step 1 finding is "tokens ARE reliably exposed."

**Files to modify:**
1. `source/shared/rules/pipeline-orchestration.md` -- update Tier 1 capture section to include token extraction procedure (which fields, where in result metadata, how to compute cost_usd)
2. `source/shared/references/telemetry-metrics.md` -- update `input_tokens` / `output_tokens` default-when-unavailable from "0 (log 'unavailable')" to actual extraction instructions; update Missing Data Handling section
3. `source/shared/references/pipeline-operations.md` -- add `telemetry_total_cost_usd` to PIPELINE_STATUS field table (if not already present)

**Files to create:** None

**Acceptance criteria:**
- pipeline-orchestration.md Tier 1 section documents token extraction from Agent tool result metadata (field names, location, fallback)
- telemetry-metrics.md Missing Data Handling section updated to reflect actual availability
- PIPELINE_STATUS includes `telemetry_total_cost_usd` field (running accumulator)
- No new files, no new hooks, no brain schema changes
- Accumulator is behavioral (Eva does it), not mechanical (no hook enforcement)

**Complexity:** Low. Three file edits, all additive. ~20 lines total.

**After this step, I can:** see Eva tracking live token spend during a pipeline run and reporting actual cost in the telemetry summary.

### Step 2b: Document Token Exposure Gap (conditional -- tokens NOT exposed)

**Gating condition:** Step 1 finding is "tokens are NOT reliably exposed."

**Files to modify:**
1. `source/shared/references/telemetry-metrics.md` -- add a "Token Exposure Gap" callout box after the Tier 1 table, documenting: date of probe, what was tested, what was found, conclusion. Update the `input_tokens` / `output_tokens` default-when-unavailable notes to reference the gap callout.

**Files to create:** None

**Acceptance criteria:**
- telemetry-metrics.md contains a "Token Exposure Gap" section with probe date, method, findings
- `input_tokens` / `output_tokens` rows reference the gap section
- No behavioral changes to Eva's orchestration
- ADR status updated to "Accepted (gap documented, closed)"

**Complexity:** Trivial. One file edit, ~10 lines.

**After this step, I can:** see the definitive answer to "are tokens available?" documented in the telemetry reference, preventing future re-investigation.

---

## Test Specification

| ID | Category | Description |
|----|----------|-------------|
| T-0030-001 | Probe | Step 1 produces a written finding with "ARE" or "ARE NOT" verdict |
| T-0030-002 | Probe | Step 1 finding includes evidence (field names, locations, sample values) |
| T-0030-003 | Probe | Step 1 finding covers >= 3 agent completion records |
| T-0030-004 | Branch | Implementation Plan explicitly documents Step 2a and Step 2b as conditional |
| T-0030-005 | Branch | Step 2a gating condition documented: "tokens ARE reliably exposed" |
| T-0030-006 | Branch | Step 2b gating condition documented: "tokens are NOT reliably exposed" |
| T-0030-007 | 2a: Schema | (If 2a) PIPELINE_STATUS includes `telemetry_total_cost_usd` field |
| T-0030-008 | 2a: Wiring | (If 2a) pipeline-orchestration.md Tier 1 documents token extraction fields and location |
| T-0030-009 | 2a: Wiring | (If 2a) telemetry-metrics.md Missing Data Handling updated to reflect actual availability |
| T-0030-010 | 2a: Negative | (If 2a) No new files created |
| T-0030-011 | 2a: Negative | (If 2a) No new hooks created |
| T-0030-012 | 2a: Negative | (If 2a) No brain schema changes |
| T-0030-013 | 2b: Gap doc | (If 2b) telemetry-metrics.md contains "Token Exposure Gap" section |
| T-0030-014 | 2b: Gap doc | (If 2b) Gap section includes probe date and method |
| T-0030-015 | 2b: Gap doc | (If 2b) `input_tokens` / `output_tokens` rows reference the gap section |
| T-0030-016 | 2b: Negative | (If 2b) No behavioral changes to pipeline-orchestration.md |
| T-0030-017 | Failure: partial exposure treated as unavailable | Probe interprets inconsistent results (some 0, some non-zero) as "NOT reliably exposed" |
| T-0030-018 | Failure: accumulator without probe | No Step 2a work occurs before Step 1 finding is produced |
| T-0030-019 | Failure: silent branch | The branch decision (2a or 2b) is announced with evidence, not silently taken |
| T-0030-020 | Consistency | Cost computation (if 2a) uses the same cost estimation table as telemetry-metrics.md |
| T-0030-021 | Probe: SPOF | Probe interpretation contract: if token fields are present at any non-zero value across 3+ sampled records, the verdict is "exposed" regardless of nesting path. This behavioral contract (not a specific implementation path) is documented in the probe's output specification (Step 1 acceptance criteria). |
| T-0030-022 | 2a: Negative | (If 2a) When token extraction succeeds but the model string is not in the pricing table, the accumulator sets `cost_usd: null` (not crash, not garbage). This path is documented in the Step 2a specification, consistent with telemetry-metrics.md rule: "When model is 'unknown' or not in this table: set cost_usd: null." |

**Test counts:** 22 total. 10 happy path, 12 failure/negative/conditional. Failure >= happy path: satisfied.

---

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| Step 1 probe | `{ verdict: "exposed" \| "not_exposed", evidence: string, fields: string[], sample_count: int }` | Step 2a or 2b gating decision |
| (If 2a) Eva Tier 1 extraction | `{ input_tokens: int, output_tokens: int, model: string }` | cost_usd computation, PIPELINE_STATUS accumulator |
| (If 2a) PIPELINE_STATUS | `telemetry_total_cost_usd: float \| null` | T3 capture, pipeline summary, budget gate comparison |
| (If 2b) telemetry-metrics.md | "Token Exposure Gap" section | Future probe attempts, ADR-0029 accuracy analysis |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| Step 1 probe finding | verdict + evidence | Branch decision (Eva) | Step 1 |
| (If 2a) pipeline-orchestration.md Tier 1 | token extraction procedure | Eva behavioral (runtime) | Step 2a |
| (If 2a) telemetry-metrics.md | updated Missing Data Handling | Eva cost computation (runtime) | Step 2a |
| (If 2a) PIPELINE_STATUS | `telemetry_total_cost_usd` | T3 capture (pipeline-orchestration.md Tier 3) | Step 2a |
| (If 2b) telemetry-metrics.md | Token Exposure Gap section | Future investigators | Step 2b |

No orphan producers. Every producer has a documented consumer.

---

## Data Sensitivity

| Method/Field | Classification | Rationale |
|-------------|---------------|-----------|
| Token counts (input_tokens, output_tokens) | `public-safe` | Usage metrics, no PII |
| `telemetry_total_cost_usd` | `public-safe` | Derived cost estimate, no billing data |
| Probe findings | `public-safe` | Platform capability documentation |

---

## Notes for Colby

- **Step 1 is research, not build.** Colby reads existing JSONL files and/or runs a trivial agent invocation to inspect the result structure. No code is written. The output is a text finding.
- **Model recommendation: Haiku for Step 1.** This is mechanical file reading and field inspection. Score: -2 (mechanical). No Opus needed.
- **Model recommendation: Haiku for Step 2a or 2b.** Both branches are small additive edits to existing markdown files. Score: -2 (mechanical).
- **Scout swarm for Step 1:** Single "Existing-code" scout reads `{config_dir}/telemetry/session-hooks.jsonl` and any Claude session JSONL files. No blast-radius or pattern scouts needed.
- **Scout swarm for Step 2a:** Single "Existing-code" scout reads `pipeline-orchestration.md` Tier 1 section and `telemetry-metrics.md` Tier 1 table. One "Patterns" scout greps for `telemetry_total_cost_usd` across source/.
- **Scout swarm for Step 2b:** None needed. Single file edit.
- **Where to look for session data:** `~/.claude/projects/-Users-*-projects-*/` contains per-session directories. Inside each: JSONL files with agent invocation records. Also check `{config_dir}/telemetry/session-hooks.jsonl` (written by `log-agent-stop.sh`).
- **Partial exposure = not exposed.** If the probe finds some invocations with tokens and some without, the verdict is "NOT reliably exposed." Do not build an accumulator that works "sometimes."
- **Do not edit log-agent-stop.sh.** The probe reads its output; it does not modify the hook.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Step 1 is a probe that verifies token exposure | Done | Step 1 in Implementation Plan |
| R2 | Step 2a adds live accumulator if tokens exposed | Done | Step 2a in Implementation Plan, conditional on Step 1 |
| R3 | Schema already exists (telemetry_total_cost_usd, T1 fields) | Done | Referenced in Step 2a, no new schema created |
| R4 | Step 2a is behavioral only -- no new infrastructure | Done | Step 2a modifies orchestration rules and metrics docs only |
| R5 | Step 2b documents gap if tokens not exposed | Done | Step 2b in Implementation Plan, conditional on Step 1 |
| R6 | Conditional branching explicit in Implementation Plan | Done | Step 2a/2b gating conditions documented, decision tree shown |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled, no TBD, no placeholders
