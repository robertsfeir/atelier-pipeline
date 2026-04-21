# Telemetry Metrics Reference

Eva reads this file at pipeline start alongside `pipeline-operations.md` to load
metric schemas, cost estimation tables, and alert thresholds for telemetry capture.

---

## Tier 1: Per-Invocation Metrics

Captured after every Agent tool completion by Eva.

| Field | Type | Source | Default When Unavailable |
|-------|------|--------|--------------------------|
| `agent_name` | string | Agent tool call context | Required -- always known |
| `pipeline_phase` | string | Eva pipeline state | Required -- always known |
| `work_unit_id` | string | ADR step ID (e.g., "ADR-0014-Step-1") | Required -- always known |
| `is_retry` | boolean | Rework cycle count > 0 for this unit | `false` |
| `duration_ms` | integer | Wall-clock end_time - start_time | Always computable |
| `model` | string | Agent tool result metadata | `"unknown"` |
| `input_tokens` | integer | Agent tool result metadata | `0` (log "unavailable") |
| `output_tokens` | integer | Agent tool result metadata | `0` (log "unavailable") |
| `cache_read_tokens` | integer | Agent tool result metadata | `0` |
| `finish_reason` | string | Agent tool result metadata | `"unknown"` |
| `tool_count` | integer | Agent tool result metadata | `0` |
| `turn_count` | integer | Agent tool result metadata | `0` |
| `context_utilization` | float | `(input_tokens + output_tokens) / context_window_max` | `null` when tokens unavailable |
| `cost_usd` | float or null | Computed from cost estimation table | `null` when model unknown or pricing unavailable |

### Missing Data Handling (Tier 1)

- `input_tokens` / `output_tokens` unavailable: log `0`, append to content "token counts unavailable from Agent tool"
- `cost_usd` unavailable: set `null`, log "Cost unavailable -- token counts not exposed by Agent tool"
- `model` unavailable: set `"unknown"`, skip `context_utilization` and `cost_usd` computation
- `context_utilization` unavailable: set `null` (do not guess; requires both tokens and model)

---

## Tier 2: Per-Unit Metrics

Captured after each work unit completes Poirot verification PASS. Aggregated from Tier 1.
Skipped on Micro pipelines.

| Field | Type | Aggregation Rule | Default When Unavailable |
|-------|------|-----------------|--------------------------|
| `work_unit_id` | string | Same as Tier 1 `work_unit_id` | Required |
| `rework_cycles` | integer | Count of Colby re-invocations after first on this unit (0 = first-pass QA) | `0` |
| `first_pass_qa` | boolean | `rework_cycles == 0` (zero re-invocations, not one) | `false` |
| `unit_cost_usd` | float or null | Sum of Tier 1 `cost_usd` for all invocations with this `work_unit_id` | `null` when any Tier 1 cost was null |
| `finding_counts` | object | `{poirot: N, robert: N, sable: N, sentinel: N}` count per reviewer | `{poirot: 0, robert: 0, sable: 0, sentinel: 0}` |
| `finding_convergence` | integer | Findings flagged independently by both Poirot | `0` |
| `evoscore_delta` | float | `(tests_after - tests_broken) / tests_before` for this unit; `1.0` when `tests_before == 0` | `null` when test counts unavailable |

---

## Tier 3: Per-Pipeline Metrics

Captured at pipeline end, after Ellis final commit. Aggregated from Tier 2 + in-memory accumulators.
Skipped on Micro pipelines.

| Field | Type | Aggregation Rule | Default When Unavailable |
|-------|------|-----------------|--------------------------|
| `pipeline_id` | string | `{feature_name}_{ISO_timestamp}` set at pipeline start | Required |
| `sizing` | string | `"micro"`, `"small"`, `"medium"`, or `"large"` | Required |
| `total_cost_usd` | float or null | Sum of all Tier 1 `cost_usd` | `null` if any cost was null |
| `total_duration_ms` | integer | Pipeline end_time - pipeline start_time (wall-clock) | Always computable |
| `phase_durations` | object | `{phase_name: duration_ms}` -- sum of Tier 1 `duration_ms` by `pipeline_phase` | `{}` |
| `total_invocations` | integer | Count of all Tier 1 captures | From in-memory accumulator |
| `invocations_by_agent` | object | `{agent_name: count}` | From in-memory accumulator |
| `invocations_by_model` | object | `{model_name: count}` from Tier 1 `model` field | `{"unknown": N}` when all models unavailable |
| `total_tokens` | integer or null | Sum of all Tier 1 `(input_tokens + output_tokens)` | `null` if any Tier 1 tokens were unavailable |
| `rework_rate` | float | `total_rework_cycles / total_units` | `0.0` when no units |
| `first_pass_qa_rate` | float | `units_with_first_pass_qa / total_units` | `null` when no units |
| `agent_failures` | object | `{agent_name: count}` of aborted/failed invocations | `{}` |
| `evoscore` | float | Average `evoscore_delta` across all Tier 2 captures | `null` when no units |
| `regression_count` | integer | Count of units where `evoscore_delta < 1.0` | `0` |
| `project_name` | string | From `pipeline_project_name` session state | Current directory basename |
| `stop_reason` | string | From pipeline-state.md at terminal transition (see pipeline-orchestration.md terminal-transition protocol for enum values) | `"legacy_unknown"` |
| `budget_estimate_low` | float or null | Eva's pre-pipeline heuristic estimate lower bound (USD); set at sizing gate, before first agent invocation. See Budget Estimate Heuristic section. | `null` |
| `budget_estimate_high` | float or null | Eva's pre-pipeline heuristic estimate upper bound (USD); set at sizing gate, before first agent invocation. See Budget Estimate Heuristic section. | `null` |

**T3 `budget_estimate_low` / `budget_estimate_high` producer:** Eva computes and stores the estimate at the sizing decision gate (before the first agent invocation). These fields are set in memory at that point and written to T3 brain capture at pipeline end. When the gate does not fire (Micro, Small, or Medium without threshold), both fields remain `null`.

---

## Tier 4: Over-Time Trend Queries

Not stored directly -- derived from brain queries at session boot (step 5b).
Eva queries brain for Tier 3 summaries: `agent_search` with `filter: { telemetry_tier: 3 }`,
`source_phase == 'telemetry'` client-side filter, limit 10.

Trends computed from last N Tier 3 summaries (N = up to 10 returned by query):
- Average cost, duration, rework rate, first-pass QA rate, EvoScore
- % change in cost over last 5 pipelines
- Rework rate direction (improving / stable / degrading)
- Per-agent failure counts across last 10 pipelines

---

## `pipeline_id` Generation Rule

Format: `{feature_name}_{ISO_timestamp}` where:
- `feature_name` is the slug from the feature spec filename or ADR title (lowercase, hyphens)
- `ISO_timestamp` is the pipeline start time in ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

Example: `agent-telemetry-dashboard_2026-03-29T14:30:00Z`

Created once at pipeline start. Used in every tier's metadata for grouping.

---

## Cost Estimation Table

Hardcoded estimates -- order-of-magnitude accuracy. Not for billing.
`context_window_max` is used by Tier 1 `context_utilization` computation.

| Model | `input_per_1k` (USD) | `output_per_1k` (USD) | `context_window_max` (tokens) |
|-------|----------------------|----------------------|-------------------------------|
| claude-opus-4 (Opus) | 0.015 | 0.075 | 200000 |
| claude-sonnet-4-5 (Sonnet) | 0.003 | 0.015 | 200000 |
| claude-haiku-3-5 (Haiku) | 0.001 | 0.005 | 200000 |
| claude-opus-4-7 (Opus 4.7) | 0.0175 | 0.0875 | 200000 |

**Cost formula:** `cost_usd = (input_tokens / 1000 * input_per_1k) + (output_tokens / 1000 * output_per_1k)`

### Observed Effective Per-M Rates (This Pipeline's Workload)

Distinct from the list-price per-1k table above. The numbers below are empirical per-million-token rates derived from Tier 1 brain telemetry for this pipeline's actual workload, which is characterized by heavy input-token caching (agent-preamble and rules reinjected across invocations) and sparse output. Cache reads are billed at a fraction of fresh-input price, so the effective per-M rate is well below what the list price would predict for an uncached workload.

| Model | Observed effective per-M rate |
|-------|-------------------------------|
| Haiku | ~$0.11/M |
| Sonnet | ~$0.33/M |
| Opus | ~$2.22/M |

Use these as rough-cut comparisons when reasoning about tier cost deltas in this pipeline. For any billing-grade or `cost_usd` computation, the per-1k list-price table above is authoritative -- the effective rates are a telemetry-derived planning figure, not a pricing contract.

When model is `"unknown"` or not in this table: set `cost_usd: null`, log "Cost unavailable -- model not in pricing table".

---

## EvoScore Formula

```
EvoScore = (tests_after - tests_broken) / tests_before
```

- `tests_before`: number of passing tests before Colby's build unit
- `tests_after`: number of passing tests after Colby's build unit
- `tests_broken`: number of previously-passing tests now failing

**Edge case: `tests_before == 0`**: EvoScore = `1.0` (no regression possible when starting from zero tests)

**Interpretation:**
- `1.0` = no regressions, test count maintained or grew
- `> 1.0` = new tests added, no regressions (valid)
- `< 1.0` = regressions detected
- `0.9` = degradation threshold (see alerts below)

---

## Degradation Alert Thresholds

Alerts fire only when a threshold is exceeded for **3+ consecutive pipelines**.
Two consecutive breaches do NOT fire an alert.

| Alert | Metric | Threshold | Consecutive Pipelines Required |
|-------|--------|-----------|-------------------------------|
| Cost spike | Total pipeline cost | >25% above rolling average | 3 |
| Rework accumulation | Rework rate | >2.0 cycles/unit | 3 |
| First-pass QA degradation | First-pass QA rate | <60% | 3 |
| Agent failure pattern | Failures for same agent | >2 over last 10 pipelines | N/A (window-based) |
| Context pressure | Context utilization | >80% per invocation | 3 consecutive invocations (within one pipeline) |
| EvoScore degradation | EvoScore | <0.9 | 3 |

**Alert format (when threshold exceeded for 3+ consecutive pipelines):**
```
Warning: [metric] above/below threshold for [N] consecutive pipelines.
Last [N]: [values]. [suggestion].
```

**Anti-fatigue rule:** Track the streak count for each alert type. Reset to 0 when a pipeline passes the threshold. Only fire the alert announcement at the 3rd consecutive breach and again every 3 breaches thereafter (not on every pipeline once triggered).

---

## Budget Estimate Heuristic

Order-of-magnitude estimates for the pre-pipeline token budget gate (see `<gate id="budget-estimate">` in `pipeline-orchestration.md`). Not for billing. These numbers are rough averages -- actual usage varies by context fill, tool calls, rework, and output length.

### Per-Invocation Cost Estimates by Model

Derived from the Cost Estimation Table above using typical context window utilization rates.

| Model | Avg input tokens | Avg output tokens | Typical cost per invocation (USD) |
|-------|-----------------|-------------------|------------------------------------|
| claude-opus-4 (Opus) | 50,000 | 8,000 | ~$1.35 |
| claude-sonnet-4-5 (Sonnet) | 40,000 | 6,000 | ~$0.21 |
| claude-haiku-3-5 (Haiku) | 20,000 | 3,000 | ~$0.035 |

> Tier model introduced by ADR-0041. Per-agent effort assignments determine which row applies at invocation time.

These estimates are order-of-magnitude -- not billing. Per-model pricing comes from the Cost Estimation Table above. If that table is updated with new pricing, these per-invocation estimates inherit the change.

### Agent Roster by Sizing Tier

Typical agent invocation counts per sizing tier. Used as the base input to the estimate formula when step count is not yet known.

| Sizing | Agent Invocations (typical range) | Notes |
|--------|-----------------------------------|-------|
| Micro | 1--2 (Colby + Poirot) | No estimate shown |
| Small | 3--5 (Sarah skill + Colby + Poirot + Ellis) | No estimate shown |
| Medium | 8--15 (Robert? + Sable? + Sarah + Poirot test + Colby*N + Poirot verification*N + Poirot + Ellis) | Estimate shown only if `token_budget_warning_threshold` is set |
| Large | 15--30+ (full ceremony: Robert + Sable + Agatha plan + Colby mockup + Sable verify + Sarah + Poirot test + Colby*N + Poirot verification*N + Poirot*N + Robert review + Sable review + Sentinel? + Agatha docs + Ellis) | Estimate always shown |

### Estimate Formula

```
low_estimate  = sum(agent_count_by_model[model] * cost_per_invocation[model]) * 0.7
high_estimate = sum(agent_count_by_model[model] * cost_per_invocation[model]) * 1.5
```

Where `agent_count_by_model` is derived from the agent roster table above, mapping each agent to its model tier per `pipeline-models.md` at the current sizing.

**Multipliers:**
- `0.7x` (optimistic): fewer tool calls, smaller context windows, no rework
- `1.5x` (pessimistic): full context windows, rework cycles, retries, larger outputs

### Step Count Multiplier

When Sarah has already produced an ADR with N steps, apply these multipliers to the agent roster before computing the estimate. When step count is not yet known (estimate runs before Sarah), use the sizing-tier defaults from the agent roster table above.

| Agent | Invocation count with N steps |
|-------|-------------------------------|
| Colby | N * 1.3 (30% rework assumption) |
| Poirot | N * 1.1 (10% scoped re-run assumption) |
| Poirot | ceil(N / wave_size) where `wave_size` defaults to 3 |

**Default `wave_size`:** 3 (three ADR steps per wave before Poirot blind-review).

---

<protocol id="telemetry-capture">

## Telemetry Capture Protocol (when brain is available)

JIT-loaded from `pipeline-orchestration.md`. Triggered after the first agent
returns in an active pipeline. The `<protocol id="telemetry-capture">` anchor
is preserved for downstream references.

Captures use `thought_type: 'insight'`, `source_agent: 'eva'`, `source_phase: 'telemetry'`, `metadata.pipeline_id`. Eva reads `telemetry-metrics.md` at pipeline start. `brain_available: false` -> skip captures; in-memory accumulators still run.

**Tier 1 (per-invocation, in-memory):** After every Agent completion, record duration/model/tokens/cost into accumulators (`total_cost`, `total_invocations`, `invocations_by_agent/model`). NOT captured individually -- bulk-captured at T2. Micro: T1 only.

**Tier 2 (per-wave, best-effort):** Single `agent_capture` after each wave passes Poirot verification. Per-unit: `rework_cycles`, `first_pass_qa`, `unit_cost_usd`. Wave: `finding_counts`, `finding_convergence`, `evoscore_delta`. `importance: 0.5`, `metadata.telemetry_tier: 2`. `evoscore_delta = (tests_after - tests_broken) / tests_before` (0 tests = 1.0). On failure: log and continue. Skipped on Micro.

**Tier 3 (per-pipeline, best-effort):** At pipeline end after Ellis commit. Aggregate: `rework_rate`, `first_pass_qa_rate`, `evoscore`, `phase_durations`, `total_cost_usd`, `total_duration_ms`, `agent_failures`. `importance: 0.7`, `metadata.telemetry_tier: 3`. Success -> set `telemetry_captured: true` in PIPELINE_STATUS (Ellis gate requires it). Failure -> do NOT set flag. Skipped on Micro.

**Pipeline-End Summary format:**
```
Pipeline complete. Telemetry summary:
  Cost: ${total_cost_usd} ({agent}: ${agent_cost}, ...)
  Duration: {total_duration_min} min | Rework: {rework_rate} cycles/unit
  EvoScore: {evoscore} ({tests_before} before, {tests_after} after, {tests_broken} broken)
  Findings: Poirot {N}, Robert {N} (convergence: {N} shared)
```
Micro: `Telemetry: {invocation_count} invocations, {total_duration_min} min`. Cost unavailable: "Cost: unavailable". Post-summary: "Tip: Run /telemetry-hydrate to capture detailed token usage."

**Darwin Auto-Trigger:** Fires when ALL: `darwin_enabled: true`, `brain_available: true`, degradation alert fired, sizing != Micro. Eva pre-fetches T3 + prior Darwin proposals + error-patterns.md, invokes Darwin. User approves/rejects/modifies each proposal individually (hard pause). Approved: capture + route Colby + mechanical gate + Poirot + Ellis commit. Rejected: capture with reason. Does not block pipeline completion.

**Pattern Staleness (pipeline end):** Check `thought_type: 'pattern'` thoughts for files modified this pipeline. >50% churn -> invalidate via `atelier_relation` supersedes. 20-50% -> append warning.

**Dashboard Bridge (post-pipeline):** `dashboard_mode: "plan-visualizer"` -> run `{config_dir}/dashboard/telemetry-bridge.sh`. Never a blocker. `claude-code-kanban` or `none` -> skip. Boot announcement: `plan-visualizer` -> "Dashboard: PlanVisualizer", `claude-code-kanban` -> "Dashboard: claude-code-kanban", `none`/absent -> omit.

</protocol>
