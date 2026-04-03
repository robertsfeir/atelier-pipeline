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

Captured after each work unit completes Roz QA PASS. Aggregated from Tier 1.
Skipped on Micro pipelines.

| Field | Type | Aggregation Rule | Default When Unavailable |
|-------|------|-----------------|--------------------------|
| `work_unit_id` | string | Same as Tier 1 `work_unit_id` | Required |
| `rework_cycles` | integer | Count of Colby re-invocations after first on this unit (0 = first-pass QA) | `0` |
| `first_pass_qa` | boolean | `rework_cycles == 0` (zero re-invocations, not one) | `false` |
| `unit_cost_usd` | float or null | Sum of Tier 1 `cost_usd` for all invocations with this `work_unit_id` | `null` when any Tier 1 cost was null |
| `finding_counts` | object | `{roz: N, poirot: N, robert: N, sable: N, sentinel: N}` count per reviewer | `{roz: 0, poirot: 0, robert: 0, sable: 0, sentinel: 0}` |
| `finding_convergence` | integer | Findings flagged independently by both Roz and Poirot | `0` |
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

**Cost formula:** `cost_usd = (input_tokens / 1000 * input_per_1k) + (output_tokens / 1000 * output_per_1k)`

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
