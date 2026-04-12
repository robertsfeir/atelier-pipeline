## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Eva produces a heuristic estimate before Large (and optionally Medium) pipelines | ADR-0029, R1 |
| 2 | Estimate based on pipeline sizing, agent roster size, ADR step count if known, and hardcoded sizing model | ADR-0029, R2 |
| 3 | `token_budget_warning_threshold` added to pipeline-config.json template | ADR-0029, R3 |
| 4 | When threshold is set, Eva shows estimate AND compares to threshold before proceeding | ADR-0029, R4 |
| 5 | When threshold is absent or null, Eva shows estimate for Large only (no gate) | ADR-0029, R5 |
| 6 | Hard pause on Large pipelines before first agent invocation | ADR-0029, R6 |
| 7 | User sees: sizing, estimated range, threshold status if configured, explicit proceed/cancel | ADR-0029, R7 |
| 8 | Estimate clearly labeled as "order-of-magnitude — not billing" | ADR-0029, R10 |
| 9 | Track A only — no live token accumulation, no threshold gate based on real spend | ADR-0029, R11 |
| 10 | Micro and Small pipelines: no gate, no estimate | ADR-0029, R9 |
| 11 | Budget estimate fields added to T3 telemetry capture for post-hoc accuracy analysis | ADR-0029, R2 (brain integration) |
| 12 | Cancellation after estimate produces `budget_threshold_reached` stop reason (soft dependency on ADR-0028) | ADR-0029, R13 |

**Retro risks:** None directly applicable. The estimate gate is a behavioral procedure — no hook enforcement in Track A.

---

# Feature Spec: Token Budget Estimate Gate

**Author:** Robert (CPO) | **Date:** 2026-04-12
**Status:** Draft
**ADR:** [ADR-0029](../architecture/ADR-0029-token-budget-estimate-gate.md)

## The Problem

Large pipelines are expensive. A pipeline with 5+ ADR steps, running Cal (Opus), Colby (Opus), Roz, Poirot, Robert, and Sable at full ceremony easily costs 10x a Small pipeline. Eva currently presents sizing as a choice list and proceeds immediately after the user selects. There is no estimate of what "Large" will cost and no gate to confirm the user wants to spend that much.

Users have no information to make a cost-informed decision at sizing time. They discover the cost after the pipeline completes.

## Who Is This For

Pipeline operators running Large or Medium pipelines who want to make an informed cost decision before committing. Particularly useful for operators managing shared API keys, teams with budget constraints, and users evaluating whether a feature warrants full pipeline ceremony.

## Business Value

- **Cost transparency** — users see an order-of-magnitude cost range before committing to a Large pipeline
- **Budget control** — configurable threshold extends the gate to Medium pipelines for cost-conscious teams
- **No friction for small work** — Micro and Small pipelines are unaffected
- **Self-correcting accuracy** — when brain is available, Eva can compare estimates to actual T3 costs over time and announce historical accuracy

**KPIs:**
| KPI | Measurement | Acceptance |
|-----|------------|------------|
| Large pipelines with estimate shown | % of Large pipelines where estimate is displayed before first agent invocation | 100% |
| Medium pipelines with threshold configured | % of Medium pipelines (with threshold set) where estimate is displayed | 100% |
| Estimate accuracy over time | `actual_cost / budget_estimate_high` ratio after 5+ pipelines | Tracked in T3 telemetry, surfaced by Eva |

## Personas

**Pipeline operator (cost-conscious):** Configures `token_budget_warning_threshold: 5.0` in pipeline-config.json. When a Medium or Large pipeline estimate exceeds $5.00, Eva shows the estimate with a "EXCEEDS threshold" warning and waits for explicit confirmation.

**Pipeline operator (unconfigured):** Does not set a threshold. Eva shows the estimate for Large pipelines only, without a threshold comparison. Eva proceeds after explicit "yes" / "cancel" / "downsize to Medium" from the user.

**Pipeline operator (Micro/Small work):** Never sees the estimate gate. No friction for quick fixes and small features.

## User Flow

### Large Pipeline (threshold not configured)

After the user selects Large sizing:

```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Large | Steps: TBD -- estimated after Cal | Agents: 12
  Estimated cost: $4.20 -- $9.00 (based on sizing heuristics and model assignments)

Proceed? (yes / cancel / downsize to Medium)
```

Eva waits for an explicit response before invoking the first agent.

### Large Pipeline (threshold configured, estimate exceeds)

```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Large | Steps: 6 (from ADR) | Agents: 12
  Estimated cost: $4.20 -- $9.00 (based on sizing heuristics and model assignments)
  Threshold: $5.00 -- estimate EXCEEDS threshold

Proceed? (yes / cancel / downsize to Medium)
```

### Medium Pipeline (threshold configured, estimate within)

```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Medium | Steps: TBD | Agents: 8
  Estimated cost: $1.10 -- $2.40
  Threshold: $5.00 -- within threshold

Proceed? (yes / cancel)
```

### Cancellation Flow

When user cancels after seeing the estimate:
1. Eva writes `stop_reason: budget_threshold_reached` to pipeline-state.md
2. Eva announces: "Pipeline cancelled. Stop reason: budget threshold. Consider: (a) downsizing to Medium/Small, (b) breaking the feature into smaller increments, (c) adjusting the threshold in pipeline-config.json."
3. Pipeline transitions to idle.

## Acceptance Criteria

**Gate trigger rules:**
- AC-1: Micro pipelines MUST NOT show an estimate or gate, regardless of threshold configuration.
- AC-2: Small pipelines MUST NOT show an estimate or gate, regardless of threshold configuration.
- AC-3: Medium pipelines with no threshold configured MUST NOT show an estimate or gate.
- AC-4: Medium pipelines with threshold configured MUST show the estimate and gate ONLY when the estimate exceeds the threshold.
- AC-5: Large pipelines MUST always show the estimate and hard pause before the first agent invocation, regardless of threshold configuration.

**Estimate presentation:**
- AC-6: The estimate MUST include the label "order-of-magnitude -- not billing" or equivalent language making clear this is not a billing amount.
- AC-7: The estimate MUST show a cost range (low–high), not a point estimate.
- AC-8: The estimate MUST display: sizing tier, step count (or "TBD -- estimated after Cal" when unknown), agent roster count, cost range.
- AC-9: When threshold is configured, the estimate MUST display the threshold value and whether the estimate is within or exceeds it.
- AC-10: When threshold is not configured, the estimate MUST NOT show a threshold line.
- AC-11: The Large pipeline proceed prompt MUST offer "downsize to Medium" as an option in addition to "yes" and "cancel". The Medium pipeline prompt MUST NOT offer a downsize option.

**Formula inputs:**
- AC-12: The estimate MUST use per-invocation cost averages from the Budget Estimate Heuristic table in telemetry-metrics.md (Opus ~$1.35, Sonnet ~$0.21, Haiku ~$0.035 per invocation).
- AC-13: Low estimate MUST use a 0.7x multiplier (optimistic). High estimate MUST use a 1.5x multiplier (pessimistic).
- AC-14: When ADR step count is known, the Colby invocation count MUST use N * 1.3 (30% rework assumption). Roz QA invocations MUST use N * 1.1.
- AC-15: When step count is not yet known, the estimate MUST use sizing-tier defaults from the agent roster table.

**Configuration:**
- AC-16: `pipeline-config.json` MUST contain `"token_budget_warning_threshold": null` as the default.
- AC-17: When `token_budget_warning_threshold` is absent from pipeline-config.json, Eva MUST treat it as null (no Medium gate, Large-only estimate).
- AC-18: The threshold value MUST be in USD, matching the units of the cost estimation table.

**Brain integration:**
- AC-19: At pipeline end, Eva MUST include `budget_estimate_low` and `budget_estimate_high` in the T3 brain capture metadata (both as float, null when estimate was not shown).
- AC-20: When brain is available and 5+ prior pipelines have both estimate and actual cost data, Eva SHOULD announce historical accuracy at pipeline start: "Historical accuracy: estimates have been within Xx of actual costs."

**Track A constraint:**
- AC-21: Eva MUST NOT track live token accumulation mid-pipeline. The gate is pre-run and heuristic only.
- AC-22: Eva MUST NOT auto-cancel pipelines that exceed the estimate at runtime. The gate is informational with a hard pause at sizing time.

## Configuration Reference

Add to `pipeline-config.json`:
```json
{
  "token_budget_warning_threshold": null
}
```

- Type: `number | null`
- Units: USD
- Default: `null` (no threshold; Large-only estimate, no Medium gate)
- Example value: `5.0` (Eva warns when estimate exceeds $5.00)

## Edge Cases

**Step count unavailable:** Eva shows "TBD — estimated after Cal" and uses the sizing-tier agent roster defaults. The estimate is shown before Cal runs, so step count is often unknown on first invocation.

**User downsizes to Medium:** Eva recomputes the estimate for Medium sizing and shows the new range. If Medium also exceeds the threshold, Eva shows a second estimate gate for Medium.

**ADR-0028 not yet implemented:** When `budget_threshold_reached` stop reason is not available, Eva writes `user_cancelled` instead. Gate behavior is identical; only the stop reason label differs.

**Brain unavailable:** Estimate still shown and gate still fires. T3 brain capture fields are skipped. No impact on gate behavior.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Heuristic estimate before Large and optionally Medium pipelines | Done | Gate rules in pipeline-orchestration.md budget-estimate gate section |
| 2 | Estimate based on sizing, roster, steps, and sizing model | Done | Formula in telemetry-metrics.md Budget Estimate Heuristic section |
| 3 | `token_budget_warning_threshold` in pipeline-config.json | Done | Default null in template |
| 4 | Threshold comparison when threshold is set | Done | Gate rules table: Medium=threshold-only, Large=always |
| 5 | Large-only estimate when threshold absent | Done | Gate rules table |
| 6 | Hard pause on Large before first agent invocation | Done | Gate section in pipeline-orchestration.md |
| 7 | User sees sizing, range, threshold status, proceed/cancel | Done | Estimate presentation format |
| 8 | "Order-of-magnitude — not billing" label | Done | Required in every estimate presentation |
| 9 | Micro/Small: no gate, no estimate | Done | Gate rules table |
| 10 | T3 telemetry includes budget estimate fields | Done | telemetry-metrics.md T3 metadata fields |
| 11 | Cancellation flow references ADR-0028 stop reason | Done | Cancellation flow in pipeline-orchestration.md |
| 12 | Track A only — no live tracking | Done | Anti-goal: no live accumulation anywhere |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled — no TBD, no placeholders
