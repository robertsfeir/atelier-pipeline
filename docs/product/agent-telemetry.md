## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Per-invocation metrics: tokens, duration, model, cost, finish reason, tool count, turn count, cache ratio, context utilization | Brain research b76441a1 |
| 2 | Per-unit metrics: rework cycles, first-pass QA, cost per unit, finding counts, convergence, EvoScore delta | Brain research |
| 3 | Per-pipeline metrics: total cost/duration, phase breakdown, rework rate, agent failures, regression rate | Brain research |
| 4 | Over-time trends: cost/quality/rework trends, degradation alerts | Brain research |
| 5 | Eva surfaces trends at session boot | Issue #18 |
| 6 | All metrics stored in brain via agent_capture | Issue #18 |
| 7 | Folds in #12 (EvoScore) and #14 (eval-driven outcome metrics) | Brain decision, user directive |
| 8 | No external dashboard — brain queries + Eva boot summary only | User decision (first slice) |
| 9 | No piecemeal metrics — comprehensive or not at all | User directive (brain) |

**Retro risks:** None directly applicable. Brain context shows prior decision to reject standalone EvoScore (#12) and eval output checks (#14) in favor of this unified dashboard.

---

# Feature Spec: Agent Telemetry Dashboard

**Author:** Robert (CPO) | **Date:** 2026-03-29
**Status:** Draft
**Issue:** #18 (includes folded #12, #14)

## The Problem

No visibility into pipeline efficiency. Can't answer: "Is the pipeline getting faster? Cheaper? Are we doing less rework?" Agent invocations are fire-and-forget — Eva captures qualitative knowledge (decisions, lessons) but zero quantitative data (tokens, cost, duration, rework rates).

## Who Is This For

Pipeline operators who want to optimize cost, identify underperforming agents, and track quality trends across sessions. Also enables model selection tuning (did Opus actually reduce rework vs Sonnet?).

## Business Value

- **Cost control** — know what each pipeline costs, where money goes
- **Quality tracking** — rework rate trending up means agent personas need revision
- **Model optimization** — data-driven model assignment instead of gut feel
- **Regression detection** — catch quality degradation before it compounds

**KPIs:**
| KPI | Measurement | Timeframe | Acceptance |
|-----|------------|-----------|------------|
| Cost per pipeline | Sum of all invocation costs | Per pipeline | Tracked and surfaced at boot |
| First-pass QA rate | Units passing Roz on first try / total units | Per pipeline + trend | Tracked and surfaced at boot |
| Rework rate | Total Colby re-invocations / total units | Per pipeline + trend | Tracked and surfaced at boot |
| Boot summary latency | Time to query and display trends | Per session | < 5 seconds |

## User Stories

1. **As a pipeline operator**, after each pipeline completes, I want a summary of cost, duration, and quality metrics so I can track efficiency.
2. **As a pipeline operator**, at session boot, I want to see trends from the last N pipelines so I can spot degradation.
3. **As a pipeline operator**, I want to know which agents cost the most and which have the highest rework rates so I can optimize.
4. **As a pipeline operator**, I want EvoScore tracking so I can detect when agents are breaking more tests than they fix.

## User Flow

### Pipeline End Summary
```
Pipeline complete. Telemetry summary:
  Cost: $3.42 (Colby: $1.80, Roz: $0.95, Cal: $0.45, Ellis: $0.12, Poirot: $0.10)
  Duration: 34 min (build: 18 min, QA: 10 min, review: 4 min, docs: 2 min)
  Rework: 1.5 cycles/unit (3 units, 2 first-pass QA)
  EvoScore: 1.0 (24 tests before, 28 after, 0 broken)
  Findings: Roz 4, Poirot 2, Robert 0 (convergence: 1 shared finding)
```

### Session Boot Summary
```
Brain: active (My Noodle, 342 thoughts)
Telemetry: Last 5 pipelines — avg $4.10, 41 min. Rework: 1.2/unit. First-pass QA: 73%.
  ⚠ Cost trending up (+18% over last 5). Colby token usage increasing.
```

### Degradation Alert (at boot, when triggered)
```
⚠ Telemetry alert: Rework rate above 2.0 for 3 consecutive pipelines.
  Last 3: 2.1, 2.3, 2.5. Colby may need persona revision or model upgrade.
```

## Metrics Taxonomy

### Tier 1: Per-Invocation (captured after every agent returns)
| Metric | Type | Source |
|--------|------|--------|
| input_tokens | integer | Agent tool result metadata |
| output_tokens | integer | Agent tool result metadata |
| cache_read_tokens | integer | Agent tool result metadata |
| duration_ms | integer | Wall-clock timing |
| model | string | Eva's invocation parameter |
| cost_usd | float | Calculated: tokens × model pricing |
| finish_reason | string | stop, max_tokens, tool_calls |
| tool_invocation_count | integer | Count from agent output |
| turn_count | integer | LLM round-trips within invocation |
| context_utilization | float | tokens_used / context_window_max |
| agent_name | string | Agent identity |
| pipeline_phase | string | Current phase |
| work_unit_id | string | Links to ADR step |
| is_retry | boolean | Whether this is a rework invocation |

### Tier 2: Per-Unit (captured after each work unit completes QA)
| Metric | Type | Source |
|--------|------|--------|
| rework_cycles | integer | Count of Colby re-invocations for same unit |
| first_pass_qa | boolean | Did Roz pass Colby on first try? |
| unit_cost_usd | float | Sum of all invocation costs for this unit |
| finding_counts | object | {roz: N, poirot: N, robert: N, sable: N, sentinel: N} |
| finding_convergence | integer | Findings flagged by both Roz and Poirot independently |
| evoscore_delta | float | (tests_after - tests_broken) / tests_before |

### Tier 3: Per-Pipeline (captured at pipeline end)
| Metric | Type | Source |
|--------|------|--------|
| total_cost_usd | float | Sum of all invocation costs |
| total_duration_ms | integer | Pipeline start to Ellis final commit |
| phase_durations | object | {spec: ms, arch: ms, build: ms, qa: ms, review: ms, docs: ms} |
| total_invocations | integer | All agent invocations |
| invocations_by_agent | object | {colby: N, roz: N, cal: N, ...} |
| rework_rate | float | Total rework cycles / total units |
| first_pass_qa_rate | float | Units with first_pass_qa=true / total units |
| agent_failure_count | integer | Timeouts, crashes, missing DoR/DoD |
| evoscore | float | Aggregate test regression ratio |
| regression_count | integer | Tests broken by agent changes |
| sizing | string | micro/small/medium/large |

### Tier 4: Over-Time Trends (queried from brain at boot)
| Metric | Query | Alert Threshold |
|--------|-------|-----------------|
| Cost trend | Last 5 pipeline costs, compute % change | > 25% increase |
| Rework trend | Last 5 rework rates | > 2.0 for 3 consecutive |
| First-pass QA trend | Last 5 first-pass rates | < 60% for 3 consecutive |
| Agent failure trend | Failures per agent over last 10 | > 2 failures same agent |
| Model efficiency | Rework rate by model assignment | Sonnet rework > 2× Opus rework |
| Context pressure | Context utilization above 80% | > 80% for 3+ invocations |
| EvoScore trend | Last 5 pipeline EvoScores | < 0.9 for 3 consecutive |

## Edge Cases and Error Handling

| Edge Case | Handling |
|-----------|----------|
| Token counts unavailable from Agent tool | Log zero, mark as "unavailable" — do not fail the pipeline |
| Brain unavailable | Skip all telemetry capture. Pipeline works identically without metrics. |
| First pipeline (no trend data) | Boot summary: "Telemetry: No prior pipeline data. Trends will appear after 2+ pipelines." |
| Micro pipeline | Capture Tier 1 only (per-invocation). Skip Tier 2/3 (no units, no QA). |
| Cost calculation — model pricing unknown | Use token counts only. Log: "Cost unavailable — model pricing not configured." |
| Degradation alert fatigue | Alerts fire only when threshold exceeded for 3+ consecutive pipelines. One bad pipeline is noise, not signal. |

## Acceptance Criteria

| # | Criterion | Measurable |
|---|-----------|------------|
| 1 | Eva captures Tier 1 metrics after every agent invocation | Brain query for thought_type='insight', source_phase='telemetry' |
| 2 | Eva captures Tier 2 metrics after each work unit QA | Brain query filtered by work_unit_id |
| 3 | Eva captures Tier 3 metrics at pipeline end | Brain query for pipeline summary |
| 4 | Eva surfaces trend summary at session boot (step 6) | Boot announcement observation |
| 5 | Degradation alerts fire when thresholds exceeded for 3+ consecutive pipelines | Alert observation after threshold breach |
| 6 | Pipeline end summary printed with cost, duration, rework, EvoScore, findings | Pipeline completion observation |
| 7 | Metrics capture does not block pipeline on failure | Brain unavailable → pipeline continues |
| 8 | Token counts, duration, model captured for every invocation | Brain data inspection |
| 9 | Rework cycles and first-pass QA tracked per unit | Brain data inspection |
| 10 | EvoScore calculated per pipeline | Brain data inspection |

## Scope

### In Scope
- Brain-based metrics capture (agent_capture with structured metadata)
- Eva boot trend summary (query brain, format, display)
- Pipeline end summary (aggregate and display)
- Degradation alerts at boot
- All 4 metric tiers
- Folded #12 (EvoScore) and #14 (outcome quality metrics)

### Out of Scope
- External dashboard or web UI
- REST API export from brain
- Real-time metrics streaming
- Cost optimization recommendations (just track, don't advise)
- Model pricing configuration (use hardcoded estimates, refine later)
- Per-developer metrics (no user attribution)

## Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Capture overhead | < 2s per invocation (brain write) |
| Boot trend query | < 5s (brain search + aggregation) |
| Storage | ~1KB per invocation, ~5KB per pipeline summary |
| No pipeline blocking | Brain failure never blocks pipeline |

## Dependencies

| Dependency | Status | Risk |
|------------|--------|------|
| Atelier Brain (agent_capture, agent_search) | Exists | None — graceful degradation if unavailable |
| Pipeline-orchestration rules | Exists | Low — additive protocol changes |
| Eva boot sequence | Exists | Low — additional step |

## Risks and Open Questions

| Risk | Mitigation |
|------|------------|
| Token counts may not be available from Agent tool metadata | Design for missing data — log what's available, skip what's not |
| Model pricing changes over time | Use rough estimates initially; make pricing a config value later |
| Brain storage growth from high-frequency captures | One thought per invocation is small (~1KB). 100 invocations per pipeline × 50 pipelines = 5MB. Acceptable. |
| Trend queries may be slow with many data points | Limit to last 10 pipelines for trends. Brain search has limit parameter. |

## Timeline Estimate

Single slice — all tiers ship together per the "no piecemeal" directive.

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Tier 1 per-invocation capture | Pending | |
| 2 | Tier 2 per-unit capture | Pending | |
| 3 | Tier 3 per-pipeline capture | Pending | |
| 4 | Boot trend summary | Pending | |
| 5 | Degradation alerts | Pending | |
| 6 | Pipeline end summary | Pending | |
| 7 | Non-blocking on failure | Pending | |
| 8 | EvoScore tracking | Pending | |
| 9 | Docs updated | Pending | |
