# ADR-0029: Token Budget Estimate Gate (Track A -- Heuristic Pre-Run)

## DoR: Requirements Extracted

**Sources:** User task description (Feature B), `source/shared/pipeline/pipeline-config.json` (current config schema),
`source/shared/rules/pipeline-orchestration.md` (phase sizing, sizing choice presentation),
`source/shared/references/telemetry-metrics.md` (cost estimation table, T3 schema),
`source/shared/commands/pipeline.md` (sizing presentation format), `source/shared/rules/pipeline-models.md`
(model assignment tables), `docs/pipeline/pipeline-state.md` (live PIPELINE_STATUS format),
`~/.claude/projects/.../memory/project_pipeline_cost_optimization.md` (user intent),
`.claude/references/retro-lessons.md`, ADR-0028 (stop reason: `budget_threshold_reached`)

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Eva produces a heuristic estimate before Large (and optionally Medium) pipelines | Task spec | Feature B, "What to build" bullet 1 |
| R2 | Estimate based on: pipeline sizing, agent roster size, number of ADR steps (if known), hardcoded sizing model | Task spec | Feature B, "What to build" bullet 2 |
| R3 | `token_budget_warning_threshold` added to pipeline-config.json template | Task spec | Feature B, "What to build" bullet 3 |
| R4 | When threshold is set, Eva shows estimate AND compares to threshold before proceeding | Task spec | Feature B, "What to build" bullet 3 |
| R5 | When threshold is absent/null, Eva shows estimate for Large only (no gate) | Task spec | Feature B, "What to build" bullet 3 |
| R6 | Hard pause on Large pipelines before first agent invocation | Task spec | Feature B, "What to build" bullet 4 |
| R7 | User sees: sizing, estimated range, threshold status (if configured), explicit proceed/cancel | Task spec | Feature B, "What to build" bullet 4 |
| R8 | If threshold is set and estimate exceeds it, Eva produces a structured pause | Task spec | Feature B, acceptance criteria 3 |
| R9 | Micro/Small pipelines: no gate, no estimate | Task spec | Feature B, acceptance criteria 4 |
| R10 | Estimate clearly labeled as "order-of-magnitude -- not billing" | Task spec | Feature B, acceptance criteria 5 |
| R11 | Track A only -- no live token accumulation, no threshold gate based on real spend | Task spec | Feature B, IMPORTANT CONSTRAINT |
| R12 | Use existing cost estimation tables plus per-agent-invocation average token estimate | Task spec | Feature B, "Sizing model" paragraph |
| R13 | Soft dependency: `budget_threshold_reached` stop reason from ADR-0028 | ADR-0028 | Stop reason enum |

**Retro risks:**
- **Lesson #005 (Frontend Wiring Omission):** The estimate formula is a producer; the sizing presentation UI (pipeline.md) is the consumer. Both must be defined in the same step.
- **Lesson #003 (Stop Hook Race Condition):** The budget gate must not block pipeline startup mechanically (no hook). It is behavioral: Eva checks the estimate and pauses. No PreToolUse hook enforcement.

**Spec challenge:** The spec assumes a heuristic formula based on sizing + agent roster + step count can produce a useful order-of-magnitude estimate. If wrong (estimate is off by 5x or more), the design fails because users either ignore it (always too high) or get false confidence (always too low), making the gate pure friction with no signal. **Mitigation:** The estimate is explicitly labeled "order-of-magnitude" and presented as a range (low-high), not a point estimate. The range width absorbs inaccuracy. The formula uses the existing cost estimation table from telemetry-metrics.md (which is already labeled "not for billing"), so the estimate inherits the same accuracy caveat. If brain telemetry is available, Eva can compare the estimate to actual T3 `total_cost_usd` from prior pipelines of the same sizing tier and announce the delta, which self-corrects over time.

**SPOF:** Eva's behavioral compliance with the estimate gate. Failure mode: Eva skips the estimate on Large pipelines and invokes the first agent directly (behavioral non-compliance, same class as skipping Roz). Graceful degradation: the gate is a hard pause instruction in the orchestration rules (same enforcement level as gate 11: one phase transition per turn). Eva cannot mechanically enforce it against herself, but it is documented as a mandatory gate for Large pipelines. A future PreToolUse hook could enforce it (check pipeline sizing + phase + estimate_shown flag), but that is out of scope for Track A.

**Anti-goals:**

1. Anti-goal: Live token accumulation with mid-pipeline threshold checking. Reason: The Agent tool does not reliably expose token counts (telemetry-metrics.md documents `input_tokens` / `output_tokens` default to `0` with "unavailable" log). Designing a live threshold gate against unreliable data produces false alarms or silent failures. Revisit: When the Agent tool reliably exposes token counts in result metadata (verify by checking 10+ invocations all return non-zero values).

2. Anti-goal: Automatic pipeline downsizing when estimate exceeds threshold (e.g., auto-suggest "decompose this Large into 3 Smalls"). Reason: Decomposition requires understanding feature dependencies, which is Cal's job, not a mechanical sizing rule. The user memory entry (`project_pipeline_cost_optimization.md`) lists decomposition guidance as a separate concern. This ADR handles the estimate gate only. Revisit: If a follow-up ADR designs decomposition guidance as a Cal behavior (not Eva automation).

3. Anti-goal: Hook-enforced budget gate (PreToolUse hook that blocks agent invocations when estimate is not shown). Reason: Track A is behavioral. Adding a hook requires state tracking (has estimate been shown?), which creates a new PIPELINE_STATUS field and hook infrastructure. The behavioral gate (documented in mandatory gates) is sufficient for the first iteration. Revisit: If Eva demonstrably skips the estimate gate on 3+ pipelines (tracked by Darwin or retro).

---

## Status

Proposed

**Depends on (soft):** ADR-0028 (Named Stop Reason Taxonomy) -- for the `budget_threshold_reached` stop reason value. If ADR-0028 is not yet implemented, the budget gate still functions (Eva pauses, user cancels) but the cancellation is recorded as `user_cancelled` rather than `budget_threshold_reached`. The gate behavior is independent; only the stop reason label depends on ADR-0028.

## Context

Large pipelines are expensive. A pipeline with 5+ ADR steps, running Cal (Opus), Colby (Opus), Roz (Sonnet+), Poirot (Sonnet+), Robert (Sonnet), and Sable (Sonnet) at full ceremony, easily costs 10x a Small pipeline (user observation from `project_pipeline_cost_optimization.md`). Eva currently presents sizing as a choice list and proceeds immediately after the user picks. There is no estimate of what "Large" will cost in tokens and no gate to confirm the user actually wants to spend that much.

The existing cost estimation table in `telemetry-metrics.md` provides per-model per-1k-token pricing. The model assignment tables in `pipeline-models.md` define which model each agent gets at each sizing tier. Combined with an average tokens-per-invocation heuristic and the number of agents in the roster, Eva can produce an order-of-magnitude estimate before invoking the first agent.

This is Track A: a purely behavioral, heuristic pre-run estimate. It does not track live token usage during the pipeline, does not enforce a budget ceiling, and does not auto-cancel pipelines that exceed the estimate. It is informational (with a hard pause on Large) so the user can make an informed decision.

### Why a Range, Not a Point Estimate

Token usage per invocation varies dramatically based on context window fill, tool calls, retries, and output length. A point estimate ("this will cost $4.50") implies false precision. A range ("$2--$8 based on sizing heuristics") communicates the uncertainty. The range bounds are computed from the formula below using optimistic (fewer invocations, smaller context) and pessimistic (more invocations, larger context) multipliers.

## Decision

### Sizing Model (Heuristic Formula)

The estimate uses three inputs:

1. **Agent roster by sizing tier.** Derived from the phase sizing rules and model assignment tables:

   | Sizing | Agent Invocations (typical) | Notes |
   |--------|---------------------------|-------|
   | Micro | 1-2 (Colby + Roz) | No estimate shown |
   | Small | 3-5 (Cal skill + Colby + Roz + Ellis) | No estimate shown |
   | Medium | 8-15 (Robert? + Sable? + Cal + Roz test + Colby*N + Roz QA*N + Poirot + Ellis) | Estimate shown only if threshold set |
   | Large | 15-30+ (full ceremony: Robert + Sable + Agatha plan + Colby mockup + Sable verify + Cal + Roz test + Colby*N + Roz QA*N + Poirot*N + Robert review + Sable review + Sentinel? + Agatha docs + Ellis) | Estimate always shown |

2. **Per-invocation token estimate by model tier.** Average tokens per invocation (input + output), derived from the cost estimation table context windows and typical utilization:

   | Model | Avg input tokens | Avg output tokens | Cost per invocation (USD) |
   |-------|-----------------|-------------------|--------------------------|
   | Opus | 50,000 | 8,000 | ~$1.35 |
   | Sonnet | 40,000 | 6,000 | ~$0.21 |
   | Haiku | 20,000 | 3,000 | ~$0.035 |

   These are rough averages. Actual usage varies. The formula uses these as the "typical" multiplier.

3. **Step count multiplier (when known).** If Cal has produced an ADR with N steps, the Colby+Roz cycle runs N times (plus rework). The formula applies:
   - Colby invocations: N * 1.3 (30% rework assumption)
   - Roz QA invocations: N * 1.1 (10% scoped re-run assumption)
   - Poirot invocations: ceil(N / wave_size) where wave_size defaults to 3

   When step count is not yet known (estimate runs before Cal), use the sizing-tier defaults from the table above.

### Estimate Formula

```
low_estimate = sum(agent_count_by_model[model] * cost_per_invocation[model]) * 0.7
high_estimate = sum(agent_count_by_model[model] * cost_per_invocation[model]) * 1.5
```

Where `agent_count_by_model` is derived from the agent roster table above, mapping each agent to its model tier per `pipeline-models.md` at the current sizing.

The 0.7x (optimistic) and 1.5x (pessimistic) multipliers account for:
- Optimistic: fewer tool calls, smaller context windows, no rework
- Pessimistic: full context windows, rework cycles, retries, larger outputs

### Estimate Presentation Format

Shown after sizing choice, before first agent invocation:

```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Large | Steps: [N or "TBD -- estimated after Cal"] | Agents: [roster count]
  Estimated cost: $X.XX -- $Y.YY (based on sizing heuristics and model assignments)
  [Threshold: $Z.ZZ -- estimate EXCEEDS threshold]  <-- only if threshold configured and exceeded
  [Threshold: $Z.ZZ -- within threshold]              <-- only if threshold configured and within

Proceed? (yes / cancel / downsize to Medium)
```

For Medium with threshold configured:
```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Medium | Steps: [N or "TBD"] | Agents: [roster count]
  Estimated cost: $X.XX -- $Y.YY
  Threshold: $Z.ZZ -- [within / EXCEEDS]

Proceed? (yes / cancel)
```

For Large without threshold: estimate shown, proceed/cancel offered, no threshold line.

### Gate Rules

| Sizing | Threshold absent/null | Threshold configured |
|--------|----------------------|---------------------|
| Micro | No gate, no estimate | No gate, no estimate |
| Small | No gate, no estimate | No gate, no estimate |
| Medium | No gate, no estimate | Estimate shown + gate fires if exceeded |
| Large | Estimate shown + hard pause (always) | Estimate shown + gate fires if exceeded + hard pause (always) |

"Gate fires" means Eva shows the estimate with threshold comparison and waits for explicit proceed/cancel. "Hard pause" means Eva will not invoke the first agent until the user responds.

### Configuration

`token_budget_warning_threshold` added to `pipeline-config.json`:

```json
{
  "token_budget_warning_threshold": null
}
```

- Type: `number | null`
- Units: USD (matches the cost estimation table units)
- Default: `null` (no threshold, Large-only estimate, no Medium gate)
- Example: `5.0` (Eva warns when estimate exceeds $5.00)

### User Cancellation Flow

When user cancels after seeing the estimate:
1. Eva writes `stop_reason: budget_threshold_reached` to pipeline-state.md (if ADR-0028 is implemented)
2. Eva announces: "Pipeline cancelled. Stop reason: budget threshold. Consider: (a) downsizing to Medium/Small, (b) breaking the feature into smaller increments, (c) adjusting the threshold in pipeline-config.json."
3. Pipeline transitions to idle.

### Brain Integration (when available)

After the estimate is shown and user proceeds:
- Eva includes the estimate range in the T3 capture at pipeline end: `metadata.budget_estimate_low`, `metadata.budget_estimate_high`
- This enables post-hoc comparison: `actual_cost / budget_estimate_high` > 2.0 means the formula is badly calibrated

After 5+ pipelines with both estimate and actual cost data:
- Eva can announce at boot: "Historical accuracy: estimates have been within Xx of actual costs" (computed from T3 data)
- This is informational only, not a formula auto-tune

## Alternatives Considered

**Alternative A: Mandatory gate on all sizings.** Show estimate for every pipeline, including Micro and Small. Rejected: Micro and Small are cheap by definition (1-5 invocations, mostly Haiku/Sonnet). The friction of a gate outweighs the information value. The user specifically requested no friction for small work.

**Alternative B: Formula based on actual telemetry from prior pipelines of the same sizing tier.** Instead of a hardcoded formula, use the average T3 `total_cost_usd` from prior pipelines of the same sizing. Rejected for Track A: this requires brain availability and 5+ prior pipelines. Track A must work on day one with no history. The brain comparison is added as an optional enhancement (see Brain Integration section).

**Alternative C: Token budget as a pipeline-config flag with automatic cancellation.** `token_budget_hard_limit: 10.0` that auto-cancels the pipeline mid-run when estimated cost exceeds the limit. Rejected: this requires live token tracking (Track B), which depends on reliable token count exposure from the Agent tool. The spec explicitly constrains this ADR to Track A (heuristic pre-run only).

## Consequences

**Positive:**
- Users see an order-of-magnitude cost estimate before committing to Large pipelines
- Configurable threshold extends the gate to Medium pipelines for cost-conscious teams
- No new infrastructure: pure behavioral change in Eva's orchestration rules
- Upgrade-safe: absent `token_budget_warning_threshold` defaults to null (no gate change for existing users)
- Brain integration enables self-correcting accuracy over time

**Negative:**
- Heuristic accuracy is inherently limited. The formula will be wrong by 2-5x in edge cases (deeply nested rework, unusually large context windows). The range presentation and "order-of-magnitude" label mitigate user expectations.
- Behavioral compliance risk: Eva may skip the gate. No hook enforcement in Track A.

**Neutral:**
- The per-invocation token estimates in the sizing model will drift as models change pricing. The cost estimation table in telemetry-metrics.md is the single source of truth -- when it is updated, the estimate formula inherits the new pricing.

---

## Implementation Plan

### Step 1: Config schema and estimate formula (pipeline-config.json + telemetry-metrics.md + pipeline-orchestration.md)

**Files to modify:**
1. `source/shared/pipeline/pipeline-config.json` -- add `token_budget_warning_threshold: null`
2. `source/shared/references/telemetry-metrics.md` -- add "Budget Estimate Heuristic" section with the per-invocation token estimates, the formula, and the multipliers. Add `budget_estimate_low` and `budget_estimate_high` to T3 metadata fields.
3. `source/shared/rules/pipeline-orchestration.md` -- add `<gate id="budget-estimate">` section documenting the gate rules table, estimate presentation format, and gate trigger conditions. Place after the phase sizing section. Mark as [JIT] loaded at pipeline sizing decision.

**Files to create:** None

**Acceptance criteria:**
- pipeline-config.json template includes `"token_budget_warning_threshold": null`
- telemetry-metrics.md has a "Budget Estimate Heuristic" section with: per-invocation cost table (Opus/Sonnet/Haiku), agent roster table by sizing tier, formula with 0.7x/1.5x multipliers, step count multiplier rules
- T3 metadata table in telemetry-metrics.md includes `budget_estimate_low` and `budget_estimate_high` with type `float | null` and default `null`
- pipeline-orchestration.md has a `<gate id="budget-estimate">` section with: gate rules table (Micro=none, Small=none, Medium=threshold-only, Large=always), estimate presentation format, user cancellation flow
- The budget-estimate gate is documented as [JIT] loaded at "Pipeline sizing decision" (same trigger as Phase Sizing Rules)
- No new files created

**Complexity:** Low-Medium. Three file edits. The formula documentation is the largest addition (~40 lines in telemetry-metrics.md, ~30 lines in pipeline-orchestration.md). pipeline-config.json is a one-line addition.

**After this step, I can:** see the estimate formula defined, understand when the gate fires, and find the threshold config in pipeline-config.json.

### Step 2: Pipeline command integration and session-boot config loading (pipeline.md + session-boot.md)

**Files to modify:**
1. `source/shared/commands/pipeline.md` -- add estimate presentation to the sizing choice flow. After the user picks a sizing, if the sizing triggers the gate (Large always, Medium with threshold), Eva shows the estimate. Add the presentation format after the existing sizing choice example.
2. `source/shared/references/session-boot.md` -- add `token_budget_warning_threshold` to the list of fields session-boot.sh reads from pipeline-config.json and includes in its output JSON. This makes the threshold available to Eva at boot without a separate file read.

**Files to create:** None

**Acceptance criteria:**
- pipeline.md's Process section includes the estimate gate between sizing choice and first agent invocation
- pipeline.md documents: "After user selects sizing, if sizing is Large or (Medium with threshold configured), Eva computes and displays the budget estimate before invoking the first agent"
- session-boot.md lists `token_budget_warning_threshold` in the JSON output fields
- The estimate presentation in pipeline.md matches the format defined in pipeline-orchestration.md (single source of truth for the format, pipeline.md references it)
- No new files created

**Complexity:** Low. Two file edits, both additive. Total ~20 lines of markdown additions.

**After this step, I can:** see the estimate gate in the pipeline command flow, see the threshold loaded at session boot, and trace the full user experience from sizing choice to estimate to proceed/cancel.

---

## Test Specification

| ID | Category | Description |
|----|----------|-------------|
| T-0029-001 | Schema | pipeline-config.json template contains `token_budget_warning_threshold` key with value `null` |
| T-0029-002 | Schema | T3 metadata in telemetry-metrics.md contains `budget_estimate_low` and `budget_estimate_high` fields |
| T-0029-003 | Formula | telemetry-metrics.md contains a "Budget Estimate Heuristic" section with per-invocation cost table |
| T-0029-004 | Formula | Per-invocation cost table references the same models as the existing Cost Estimation Table (Opus, Sonnet, Haiku) |
| T-0029-005 | Formula | Formula uses 0.7x (optimistic) and 1.5x (pessimistic) multipliers |
| T-0029-006 | Formula | Agent roster table by sizing tier is present with Micro, Small, Medium, Large rows |
| T-0029-007 | Gate rules | pipeline-orchestration.md contains a `budget-estimate` gate section |
| T-0029-008 | Gate rules | Gate rules table specifies: Micro=no gate, Small=no gate, Medium=threshold-only, Large=always |
| T-0029-009 | Gate rules | Budget-estimate gate is documented as [JIT] loaded at "Pipeline sizing decision" in the loading strategy table |
| T-0029-010 | Presentation | Estimate presentation format includes "order-of-magnitude -- not billing" label |
| T-0029-011 | Presentation | Estimate presentation includes: sizing, step count (or TBD), agent roster count, cost range |
| T-0029-012 | Presentation | Threshold line in presentation shown only when threshold is configured |
| T-0029-013 | Presentation | Proceed/cancel options shown after estimate |
| T-0029-014 | Config | `token_budget_warning_threshold` type is documented as `number | null` |
| T-0029-015 | Config | Default value for `token_budget_warning_threshold` is `null` |
| T-0029-016 | Failure: Micro triggers gate | No code path shows estimate for Micro pipelines |
| T-0029-017 | Failure: Small triggers gate | No code path shows estimate for Small pipelines |
| T-0029-018 | Failure: Medium without threshold triggers gate | Medium pipeline without threshold configured does NOT show estimate |
| T-0029-019 | Failure: estimate missing accuracy label | Every estimate presentation format includes "order-of-magnitude" or "not billing" |
| T-0029-020 | Failure: threshold absent crashes | Absent `token_budget_warning_threshold` treated as null (no gate for Medium, estimate-only for Large) |
| T-0029-021 | Integration | pipeline.md documents estimate gate between sizing choice and first agent invocation |
| T-0029-022 | Integration | session-boot.md lists `token_budget_warning_threshold` in JSON output fields |
| T-0029-023 | Cancellation | User cancellation flow documented (references ADR-0028 `budget_threshold_reached` stop reason) |
| T-0029-024 | Negative: no live tracking | No file references "live token accumulation", "mid-pipeline threshold", or "auto-cancel based on spend" |
| T-0029-025 | Negative: no hook enforcement | No PreToolUse hook created for budget gate enforcement |
| T-0029-026 | Negative: no new files | No new files created by this ADR |
| T-0029-027 | Consistency | Per-invocation cost estimates use the same model names as telemetry-metrics.md Cost Estimation Table |
| T-0029-028 | Wiring | T3 `budget_estimate_low` / `budget_estimate_high` fields have a documented producer (Eva at pipeline end) |
| T-0029-029 | Gate rules | Medium pipeline with threshold configured and estimate EXCEEDING threshold triggers structured pause (hard pause); Medium pipeline with threshold configured and estimate WITHIN threshold does NOT trigger hard pause -- both sub-cases documented in gate section |
| T-0029-030 | Presentation | Large pipeline proceed/cancel prompt includes "downsize to Medium" option; Medium pipeline proceed/cancel prompt does NOT include downsize option -- asymmetry documented |
| T-0029-031 | Formula | telemetry-metrics.md documents step count multiplier rules: Colby invocations = N * 1.3, Roz invocations = N * 1.1, Poirot invocations = ceil(N / wave_size); default wave_size value is documented |

**Test counts:** 31 total. 17 happy path, 14 failure/negative/consistency. Failure >= happy path: satisfied.

---

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| pipeline-config.json | `token_budget_warning_threshold: number \| null` | Eva at sizing decision (pipeline-orchestration.md gate) |
| session-boot.sh JSON output | `token_budget_warning_threshold: number \| null` | Eva session state |
| Eva (estimate computation) | `{ low: float, high: float, sizing: string, agents: int, steps: int \| "TBD" }` | Estimate presentation (pipeline.md format), T3 capture metadata |
| Eva (T3 capture) | `metadata.budget_estimate_low: float`, `metadata.budget_estimate_high: float` | Brain queries, Darwin, post-hoc accuracy analysis |
| telemetry-metrics.md | Per-invocation cost table, formula, multipliers | Eva estimate computation (runtime) |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| pipeline-config.json template | `"token_budget_warning_threshold": null` | session-boot.sh, Eva config reads | Step 1 |
| telemetry-metrics.md Budget Estimate Heuristic | formula + per-invocation costs + multipliers | Eva estimate computation (pipeline-orchestration.md gate) | Step 1 |
| pipeline-orchestration.md budget-estimate gate | gate rules + presentation format + cancellation flow | Eva behavioral (runtime) | Step 1 |
| T3 metadata fields | `budget_estimate_low`, `budget_estimate_high` | Brain queries, Darwin | Step 1 |
| pipeline.md estimate presentation | sizing flow integration | Eva pipeline command (runtime) | Step 2 |
| session-boot.md config fields | `token_budget_warning_threshold` in boot JSON | Eva session state | Step 2 |

No orphan producers. Every producer has a documented consumer in the same or adjacent step.

---

## Data Sensitivity

| Method/Field | Classification | Rationale |
|-------------|---------------|-----------|
| `token_budget_warning_threshold` | `public-safe` | Configuration value, no PII |
| Budget estimate (low/high) | `public-safe` | Heuristic cost range, no billing data |
| T3 `budget_estimate_low` / `budget_estimate_high` | `public-safe` | Derived from public model pricing |

---

## Notes for Colby

- **Pattern to follow for pipeline-config.json:** Existing fields use `snake_case` with JSON types. Add `"token_budget_warning_threshold": null` after the last existing field (`"dashboard_mode": "none"`). Maintain consistent formatting.
- **The formula lives in telemetry-metrics.md, not pipeline-orchestration.md.** telemetry-metrics.md is where the cost estimation table already lives. The formula is an extension of the cost table. pipeline-orchestration.md references the formula by section name ("see Budget Estimate Heuristic in telemetry-metrics.md"), not by inlining it.
- **The gate section in pipeline-orchestration.md uses the same XML tag pattern as existing gates:** `<gate id="budget-estimate">`. It is NOT a mandatory gate (not added to the "12 gates" list). It is a conditional gate triggered by sizing tier. Document it as a JIT-loaded section in the loading strategy table.
- **Do not add to the 12 mandatory gates.** The budget estimate gate is conditional (fires based on sizing and config). Mandatory gates are unconditional. These are different categories. The budget gate is a "sizing rule" that lives in the phase sizing section neighborhood.
- **Upgrade safety is trivial:** `null` default means no behavior change for existing users. Colby does not need to write migration logic. session-boot.sh should treat missing key as null (existing pattern for `dashboard_mode`).
- **ADR-0028 dependency is soft.** If implementing this ADR before ADR-0028, the cancellation flow writes `user_cancelled` (generic) instead of `budget_threshold_reached` (specific). The gate behavior is identical either way. Colby should include a comment: "When ADR-0028 stop reasons are implemented, this writes budget_threshold_reached."
- **The per-invocation token estimates (50k/40k/20k input, 8k/6k/3k output) are order-of-magnitude.** Do not overthink precision. These numbers come from typical context window fill rates observed in pipeline runs. They will be wrong for edge cases. That is acceptable for a heuristic.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Heuristic estimate before Large/Medium pipelines | Done | Gate rules in pipeline-orchestration.md, Step 1 |
| R2 | Estimate based on sizing + roster + steps + sizing model | Done | Formula in telemetry-metrics.md, Step 1 |
| R3 | `token_budget_warning_threshold` in pipeline-config.json | Done | Step 1, file 1 |
| R4 | Threshold comparison when set | Done | Gate rules table, Step 1 |
| R5 | Large-only estimate when threshold absent | Done | Gate rules table, Step 1 |
| R6 | Hard pause on Large before first agent | Done | Gate section in pipeline-orchestration.md, Step 1 |
| R7 | User sees sizing + range + threshold + proceed/cancel | Done | Presentation format in pipeline-orchestration.md, Step 1 |
| R8 | Structured pause when threshold exceeded | Done | Gate section, Step 1 |
| R9 | Micro/Small: no gate, no estimate | Done | Gate rules table, Step 1 |
| R10 | "Order-of-magnitude -- not billing" label | Done | Presentation format, Step 1 |
| R11 | Track A only -- no live tracking | Done | Anti-goal #1, no live tracking anywhere |
| R12 | Uses existing cost estimation tables | Done | Formula references Cost Estimation Table in telemetry-metrics.md |
| R13 | `budget_threshold_reached` stop reason referenced | Done | Cancellation flow in pipeline-orchestration.md, soft dependency noted |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled, no TBD, no placeholders
