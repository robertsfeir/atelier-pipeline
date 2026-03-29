# ADR-0014: Agent Telemetry Dashboard

## DoR: Requirements Extracted

| # | Requirement | Source | Priority |
|---|-------------|--------|----------|
| R1 | Tier 1 per-invocation metrics: input/output/cache tokens, duration, model, cost, finish reason, tool count, turn count, context utilization, agent name, phase, work unit ID, is_retry | Spec Tier 1 table | Must |
| R2 | Tier 2 per-unit metrics: rework cycles, first-pass QA, unit cost, finding counts by reviewer, finding convergence, EvoScore delta | Spec Tier 2 table | Must |
| R3 | Tier 3 per-pipeline metrics: total cost/duration, phase durations, invocation counts, rework rate, first-pass QA rate, agent failures, EvoScore, regression count, sizing | Spec Tier 3 table | Must |
| R4 | Tier 4 over-time trends: cost, rework, first-pass QA, agent failure, model efficiency, context pressure, EvoScore -- queried at boot | Spec Tier 4 table | Must |
| R5 | Eva surfaces trend summary at session boot (step 6) | Spec AC#4 | Must |
| R6 | All metrics stored in brain via `agent_capture` with `thought_type: 'insight'`, `source_phase: 'telemetry'` | Context constraint, Spec AC#1-3 | Must |
| R7 | Degradation alerts fire when thresholds exceeded for 3+ consecutive pipelines | Spec AC#5 | Must |
| R8 | Pipeline end summary printed with cost, duration, rework, EvoScore, findings | Spec AC#6 | Must |
| R9 | Non-blocking: brain failure never blocks pipeline | Spec AC#7 | Must |
| R10 | Token counts unavailable: log zero, mark "unavailable" | Spec edge case | Must |
| R11 | First pipeline (no trend data): boot summary says "No prior pipeline data" | Spec edge case | Must |
| R12 | Micro pipeline: Tier 1 only (skip Tier 2/3) | Spec edge case | Must |
| R13 | Cost calculation without pricing: use tokens only, log "Cost unavailable" | Spec edge case | Must |
| R14 | Degradation alert fatigue: alerts only after 3+ consecutive threshold breaches | Spec edge case | Must |
| R15 | Dual-tree: source/ templates + .claude/ installed copies in sync | Project convention | Must |
| R16 | All 4 tiers ship together (no piecemeal) | User directive | Must |
| R17 | Folds in #12 (EvoScore) and #14 (eval-driven outcome metrics) | User directive | Must |
| R18 | Capture overhead < 2s per invocation | Spec NFR | Should |
| R19 | Boot trend query < 5s | Spec NFR | Should |
| R20 | No external dashboard -- brain queries + Eva boot summary only | User decision | Must |

**Retro risks:**
- Lesson #005 (Frontend Wiring Omission): Not directly applicable (no UI), but the vertical-slice principle applies -- each step that introduces a capture gate must also include the consumer (boot summary, pipeline-end summary) or the capture data is orphaned.
- No prior telemetry retro lessons exist. This is a greenfield protocol addition.

---

## Status

Proposed

## Context

Eva currently captures qualitative knowledge (decisions, lessons, patterns) in the brain but zero quantitative data about pipeline performance. There is no way to answer "Is the pipeline getting faster? Cheaper? Are we doing less rework?" This ADR adds structured metrics capture at four tiers: per-invocation, per-unit, per-pipeline, and over-time trends. It folds in Issue #12 (EvoScore) and Issue #14 (eval-driven outcome metrics) into a unified telemetry framework.

This is a pipeline infrastructure feature. All deliverables are markdown files (rules, references) -- no application code, no hooks, no brain schema changes. The brain's existing `agent_capture` tool with its freeform `metadata` JSON field is the storage mechanism.

### Spec Challenge

The spec assumes Eva can reliably extract token counts, duration, model, and cost from Agent tool result metadata after every subagent invocation. If this is wrong -- if Claude Code's Agent tool does not expose token counts or timing data in its return value -- the design fails because Tier 1 metrics (the foundation all other tiers aggregate from) would have no source data.

Mitigation: the spec explicitly acknowledges this risk ("Token counts unavailable from Agent tool: Log zero, mark as unavailable"). The design captures whatever is available and degrades gracefully. Duration can always be measured via wall-clock timing (Eva records start/end timestamps). Token counts and cost are best-effort. The protocol instructions tell Eva to log what is observable and skip what is not, with no pipeline impact.

**SPOF:** The `agent_capture` call at each telemetry gate. If `agent_capture` itself fails (brain connection lost mid-pipeline), all telemetry for the remainder of that pipeline is lost. **Failure mode:** brain writes fail silently; Eva logs "Telemetry capture failed: [reason]" and continues. Accumulated in-memory state (invocation count, rework counters) is still available for the pipeline-end summary display, but not persisted to brain. **Graceful degradation:** pipeline-end summary is still printed from in-memory accumulators. Over-time trends degrade (one pipeline's data missing from the trend). No pipeline blocking.

### Anti-Goals

1. **Anti-goal: External dashboard or web UI.** Reason: the first slice delivers brain-stored metrics queried via Eva's boot summary. A web dashboard would require a new service, auth, and frontend -- orthogonal to pipeline infrastructure. Revisit: if pipeline operators need to share metrics with non-pipeline users (managers, external stakeholders).

2. **Anti-goal: Cost optimization recommendations.** Reason: telemetry tracks what happened; advising what to change requires a separate analysis agent or heuristic engine. Tracking and advising are distinct concerns that should not be conflated. Revisit: if trend data reveals consistent cost outliers that a simple rule could catch (e.g., "Colby on Opus for CRUD tasks costs 3x more with no quality improvement").

3. **Anti-goal: Model pricing configuration file.** Reason: the spec says "use hardcoded estimates, refine later." A pricing config adds a maintenance burden (prices change frequently) for marginal accuracy gain in a first slice. Revisit: if users report that cost estimates are misleading enough to cause bad decisions.

## Decision

Implement Agent Telemetry as a set of protocol additions to Eva's existing orchestration rules. Metrics are captured via `agent_capture` with `thought_type: 'insight'` and `source_phase: 'telemetry'`, using the `metadata` field for structured metric payloads. The protocol adds:

1. **Telemetry capture gates** in `pipeline-orchestration.md` -- mechanical rules for when Eva captures each tier
2. **Telemetry reference** in `pipeline-operations.md` -- metric schemas, cost estimation formulas, aggregation logic, degradation alert thresholds
3. **Boot sequence extension** in `default-persona.md` -- step 5b for trend query and display
4. **Pipeline-end summary format** in `pipeline-orchestration.md` -- aggregation and display protocol

### Architecture

```
Every agent returns -> Eva captures Tier 1 (agent_capture, metadata: invocation metrics)
  |
Work unit completes QA -> Eva captures Tier 2 (agent_capture, metadata: unit metrics)
  |
Pipeline ends -> Eva aggregates Tier 3, captures (agent_capture, metadata: pipeline metrics)
                 Eva prints pipeline-end summary to user
  |
Next session boots -> Eva queries brain for Tier 4 trends (agent_search)
                      Eva computes alerts, prints boot telemetry line
```

All captures use:
- `thought_type: 'insight'`
- `source_agent: 'eva'`
- `source_phase: 'telemetry'`
- `metadata.telemetry_tier: 1|2|3` (for query filtering)
- `metadata.pipeline_id: '{feature_name}_{timestamp}'` (for grouping)

### Key Design Choices

- **Single `thought_type` and `source_phase`** for all telemetry: simplifies brain queries. Filter by `source_phase: 'telemetry'` + `metadata.telemetry_tier` to get exactly the tier you need.
- **No new brain schema**: the freeform `metadata` JSON field on `agent_capture` already supports structured data. No migration needed.
- **Eva-owned, not agent-owned**: telemetry is a cross-cutting concern. Agents do not capture their own metrics. Eva captures after every return, consistent with the hybrid capture model where Eva handles cross-cutting writes.
- **In-memory accumulators for pipeline-end summary**: Eva maintains running totals (total cost, invocation count, rework cycles per unit) during the pipeline. These are used for the pipeline-end display even if brain writes fail. They are NOT persisted to disk -- they live only in Eva's context for the current pipeline session.
- **Hardcoded cost estimates**: rough per-token costs embedded in the telemetry reference. No config file. Accuracy is "order of magnitude" -- sufficient for trend comparison, not billing.

## Alternatives Considered

### Alternative A: Separate Telemetry Agent

Create a new "Metrics" agent that handles all capture and aggregation.

**Pros:**
- Clean separation of concerns -- Eva stays lean
- Agent could have specialized analysis capabilities

**Cons:**
- Adds a new agent invocation after every existing agent return -- doubles invocation overhead
- Telemetry is inherently cross-cutting; a separate agent would need Eva's full context to compute metrics
- Violates the "Eva captures cross-cutting concerns" model already established for brain writes
- New agent file, new enforcement hook case, new model assignment -- significant infrastructure for what is essentially a protocol extension

**Rejected because:** the overhead of invoking a separate agent after every other agent return is prohibitive, and the capture logic is simple enough to be mechanical rules in Eva's protocol.

### Alternative B: Disk-Based Telemetry (JSON file instead of Brain)

Write metrics to a `docs/pipeline/telemetry.json` file instead of brain.

**Pros:**
- No brain dependency -- works in baseline mode
- Directly inspectable via file read
- Simpler implementation (file append vs. brain API calls)

**Cons:**
- No search/query capability -- trend analysis requires parsing the full file
- File grows unboundedly unless Eva manages rotation
- No cross-session querying without reading the full file into context
- Diverges from the established brain-as-knowledge-store pattern
- Eva's write constraints (`docs/pipeline` only) would need expansion or the file would need to live in `docs/pipeline`

**Rejected because:** brain already provides the storage, query, and cross-session persistence needed. Adding a parallel file-based store creates a second source of truth. The brain's `agent_search` with limit parameter handles trend queries efficiently. The non-blocking requirement is already met by the brain's existing failure-safe pattern.

## Consequences

**Positive:**
- Pipeline operators gain quantitative visibility into cost, quality, and efficiency trends
- EvoScore tracking (#12) and outcome metrics (#14) are delivered as part of a unified framework rather than piecemeal
- Brain's existing infrastructure handles storage and querying -- no new services
- Non-blocking design means zero risk to pipeline reliability
- Model-vs-outcome data enables data-driven model selection tuning over time

**Negative:**
- Adds ~120 lines of protocol to `pipeline-orchestration.md` (already the largest rules file)
- One `agent_capture` call per invocation adds ~1-2s latency per agent return (spec NFR allows this)
- If brain `agent_capture` is slow, the per-invocation overhead compounds across a pipeline with 20+ invocations
- Token count availability from Agent tool metadata is unverified -- Tier 1 metrics may be sparse initially
- The SPOF (brain connection) has graceful degradation for the pipeline-end summary (in-memory fallback) but not for over-time trends (trend data simply missing for that pipeline). This is acceptable per the spec's non-blocking requirement.

## Implementation Plan

### Step 1: Telemetry Metrics Reference (Schema + Cost Estimation)

Add a new reference file defining the telemetry metric schemas, cost estimation formulas, and degradation alert thresholds. This is the "data contract" that all subsequent steps consume.

**Files to create/modify:**
- Create `source/references/telemetry-metrics.md` (template)
- Create `.claude/references/telemetry-metrics.md` (installed copy, literal values)

**Content:**
- Tier 1 metric schema (field names, types, sources, defaults for unavailable data)
- Tier 2 metric schema (aggregation rules from Tier 1)
- Tier 3 metric schema (aggregation rules from Tier 2)
- Tier 4 query definitions (brain search queries, alert thresholds, consecutive-breach logic)
- Cost estimation table: hardcoded per-token costs per model (Opus, Sonnet, Haiku). Format: `{ model: { input_per_1k: float, output_per_1k: float, context_window_max: integer } }`. The `context_window_max` field is used by Tier 1's `context_utilization` computation
- `pipeline_id` generation rule: `{feature_name}_{ISO_timestamp}` created at pipeline start
- EvoScore formula: `(tests_after - tests_broken) / tests_before`. When `tests_before = 0`, EvoScore = 1.0 (no regression possible)
- Missing data handling rules per field (e.g., `cost_usd: null` when pricing unknown, `input_tokens: 0` when unavailable)

**Acceptance criteria:**
- Every metric from the spec's Tier 1-4 tables has a corresponding schema entry
- Cost estimation table covers exactly the models in `pipeline-models.md` (Opus, Sonnet, Haiku) -- bidirectional alignment
- Cost estimation table includes `context_window_max` per model for Tier 1 `context_utilization` computation
- EvoScore formula is unambiguous with edge case handling
- Missing data defaults specified for every field
- Alert thresholds match spec: cost >25%, rework >2.0 for 3 consecutive, first-pass QA <60% for 3 consecutive, agent failures >2 same agent, context utilization >80% for 3+ invocations, EvoScore <0.9 for 3 consecutive

**Estimated complexity:** Medium (2 new files, detailed schema work)

---

### Step 2: Telemetry Capture Protocol (pipeline-orchestration.md)

Add the telemetry capture gates to Eva's orchestration rules. This defines WHEN Eva captures each tier -- the mechanical triggers integrated into the existing pipeline flow.

**Files to modify:**
- `source/rules/pipeline-orchestration.md` -- add `<protocol id="telemetry-capture">` section after the existing `<protocol id="brain-capture">` section
- `.claude/rules/pipeline-orchestration.md` -- same addition (installed copy)

**Content of the telemetry-capture protocol:**

**Tier 1 gate (per-invocation):**
After every agent returns (every Agent tool completion), Eva:
1. Records wall-clock duration (end_time - start_time in ms)
2. Extracts available metadata from Agent tool result: token counts, model, finish reason, tool invocation count, turn count
3. Computes `cost_usd` using the cost table from `telemetry-metrics.md`. If model pricing unknown, sets `cost_usd: null`
4. Computes `context_utilization` as `(input_tokens + output_tokens) / context_window_max` where context_window_max is model-dependent (from telemetry-metrics.md)
5. Calls `agent_capture` with:
   - `content`: "Telemetry T1: {agent_name} {pipeline_phase} {duration_ms}ms {model}"
   - `thought_type: 'insight'`
   - `source_agent: 'eva'`
   - `source_phase: 'telemetry'`
   - `importance: 0.3`
   - `metadata`: full Tier 1 schema populated from available data
6. On `agent_capture` failure: log "Telemetry T1 capture failed: {reason}. Continuing." No pipeline impact.
7. Adds to in-memory accumulators: total_cost, total_invocations, invocations_by_agent

**Tier 2 gate (per-unit):**
After each work unit completes QA (Roz PASS on a Colby build unit), Eva:
1. Counts rework_cycles for this unit (number of Colby re-invocations after the first on the same work_unit_id; a unit that passes on its first Colby invocation has rework_cycles == 0)
2. Determines first_pass_qa (rework_cycles == 0)
3. Sums unit_cost_usd from all Tier 1 captures for this work_unit_id
4. Tallies finding_counts from Roz, Poirot, Robert, Sable, Sentinel for this unit
5. Computes finding_convergence (findings flagged by both Roz and Poirot independently)
6. Computes evoscore_delta: queries test count before and after this unit (from Roz's QA report)
7. Calls `agent_capture` with Tier 2 metadata, `importance: 0.5`
8. On failure: log and continue
9. Skipped on Micro pipelines (no formal work units)

**Micro pipeline trend implication:** Because Tier 2 and Tier 3 are skipped for Micro pipelines, Micro runs do NOT contribute to boot trend data (which queries Tier 3). Tier 1 per-invocation data is still captured for individual visibility but is excluded from trend aggregation.

**Tier 3 gate (per-pipeline):**
At pipeline end (after Ellis final commit, before pattern staleness check), Eva:
1. Aggregates from in-memory accumulators + Tier 2 captures
2. Computes phase_durations from Tier 1 timestamps grouped by pipeline_phase
3. Computes rework_rate: total rework_cycles / total units
4. Computes first_pass_qa_rate: units with first_pass_qa=true / total units
5. Computes aggregate evoscore from Tier 2 deltas
6. Calls `agent_capture` with Tier 3 metadata, `importance: 0.7`
7. On failure: log and continue (pipeline-end summary still prints from in-memory data)
8. Skipped on Micro pipelines

**General rules:**
- All telemetry `agent_capture` calls are wrapped in a try-equivalent: if the call fails, log and continue. Never block.
- Eva reads `telemetry-metrics.md` at pipeline start (alongside pipeline-operations.md) to load schemas and cost tables.
- Telemetry captures do NOT replace existing brain captures (phase transitions, model-vs-outcome, etc.). They are additive.
- When `brain_available: false`, all telemetry capture gates are skipped entirely. In-memory accumulators still work for the pipeline-end summary display.

**Acceptance criteria:**
- Tier 1 gate fires after every Agent tool completion (mechanical, not discretionary)
- Tier 2 gate fires after every Roz QA PASS on a build unit
- Tier 3 gate fires at pipeline end (after Ellis, before staleness check)
- All captures use `thought_type: 'insight'`, `source_phase: 'telemetry'`
- Each tier's metadata includes `telemetry_tier: N` and `pipeline_id`
- Failure handling: log and continue, never block
- Micro pipelines: Tier 1 only (Micro does not contribute to boot trend data)
- Importance graduation is explicit: Tier 1 = 0.3, Tier 2 = 0.5, Tier 3 = 0.7
- `first_pass_qa` defined as `rework_cycles == 0` (zero re-invocations, not one)
- Protocol references `telemetry-metrics.md` for schemas

**Estimated complexity:** High (2 files modified, ~120 lines of protocol, integrates with existing brain-capture and pipeline-flow sections)

---

### Step 3: Pipeline-End Summary + Boot Trend Query (Eva Protocol + Display)

Add the pipeline-end summary display protocol and the boot sequence extension for trend queries. This step wires the producers (Steps 1-2) to their consumers (the user-facing summaries).

**Files to modify:**
- `source/rules/pipeline-orchestration.md` -- add pipeline-end summary section inside `<section id="pipeline-flow">`, after the existing pipeline-end brain capture
- `.claude/rules/pipeline-orchestration.md` -- same (installed copy)
- `source/rules/default-persona.md` -- add step 5b in boot sequence, add telemetry line in step 6 announcement
- `.claude/rules/default-persona.md` -- same (installed copy)

**Pipeline-end summary (in pipeline-orchestration.md):**

After Ellis final commit (and after the existing pipeline-end `agent_capture` for session summary), Eva prints a telemetry summary block to the user:

```
Pipeline complete. Telemetry summary:
  Cost: ${total_cost_usd} ({agent}: ${agent_cost}, ...)
  Duration: {total_duration_min} min ({phase}: {phase_duration_min} min, ...)
  Rework: {rework_rate} cycles/unit ({total_units} units, {first_pass_count} first-pass QA)
  EvoScore: {evoscore} ({tests_before} tests before, {tests_after} after, {tests_broken} broken)
  Findings: Roz {N}, Poirot {N}, Robert {N} (convergence: {N} shared)
```

Rules:
- Source data: in-memory accumulators (always available) supplemented by brain query for finding details (best-effort)
- If cost data unavailable (no token counts): "Cost: unavailable (token counts not exposed)"
- If brain unavailable: summary still prints from in-memory accumulators; finding details may be approximate
- Micro pipelines: print only "Telemetry: {invocation_count} invocations, {total_duration_min} min" (no rework/EvoScore/findings)

**Boot sequence extension (in default-persona.md):**

Add step 5b after step 5 (Brain context retrieval):

```
5b. **Telemetry trend query** (if `brain_available: true`) -- call `agent_search`
    with query: "telemetry pipeline summary", limit 10.
    Note: `agent_search`'s `filter` parameter operates on `metadata` (JSONB
    containment), not top-level columns. Use `filter: { telemetry_tier: 3 }`
    to retrieve Tier 3 pipeline summaries server-side. Additionally, filter
    client-side by `source_phase == 'telemetry'` on the returned results to
    exclude any non-telemetry matches.

    If results found (2+ pipelines):
    - Compute averages: avg cost, avg duration, avg rework rate, avg first-pass QA rate
    - Compute trends: % change in cost over last 5, rework direction
    - Check degradation alert thresholds (from telemetry-metrics.md):
      - Cost trending up >25% over last 5 pipelines
      - Rework rate >2.0 for 3 consecutive
      - First-pass QA rate <60% for 3 consecutive
      - Agent failures >2 for same agent over last 10
      - EvoScore <0.9 for 3 consecutive

    If 0-1 pipelines: "Telemetry: No prior pipeline data. Trends appear after 2+ pipelines."

    Degradation alerts: only fire when threshold exceeded for 3+ consecutive pipelines.
    Format: "Warning: [metric] above/below threshold for [N] consecutive pipelines.
    Last [N]: [values]. [suggestion]."
```

Add telemetry line to step 6 announcement:
```
- Telemetry: when `brain_available: true` and trend data exists, append
  "Telemetry: Last {N} pipelines -- avg ${cost}, {duration} min.
  Rework: {rate}/unit. First-pass QA: {pct}%."
  followed by any degradation alerts on separate lines.
  When no trend data: "Telemetry: No prior data."
  When brain unavailable: omit telemetry line entirely.
```

**Acceptance criteria:**
- Pipeline-end summary prints after every non-Micro pipeline
- Pipeline-end summary prints a Micro-appropriate summary after Micro pipelines
- Boot sequence step 5b queries brain for Tier 3 data
- Boot announcement includes telemetry trend line when data exists
- Degradation alerts fire only on 3+ consecutive threshold breaches
- First pipeline shows "No prior pipeline data" message
- Brain unavailable: pipeline-end summary still prints from in-memory data; boot telemetry line omitted
- Source templates use `{pipeline_state_dir}` placeholder; installed copies use literal `docs/pipeline`

**Estimated complexity:** High (4 files modified, boot sequence change is a sensitive area, pipeline-end integration requires coordination with existing flow)

---

### Step 4: Invocation Template Update + PIPELINE_STATUS Fields

Update invocation templates and pipeline state to support telemetry tracking.

**Files to modify:**
- `source/references/invocation-templates.md` -- add timing annotation to all templates
- `.claude/references/invocation-templates.md` -- same (installed copy)
- `source/references/pipeline-operations.md` -- add telemetry state fields to PIPELINE_STATUS reference, add telemetry to observation masking rules
- `.claude/references/pipeline-operations.md` -- same (installed copy)

**Invocation template changes:**

Add a comment block at the top of invocation-templates.md:

```
<!-- Telemetry: Eva records wall-clock start time before every Agent tool
     invocation and end time after return. This is mechanical -- not a
     template change per se, but documented here as the timing protocol
     that feeds Tier 1 duration_ms. Eva does not add timing instructions
     to individual templates. -->
```

**PIPELINE_STATUS additions (in pipeline-operations.md):**

Add telemetry tracking fields to the PIPELINE_STATUS marker documentation:

| Field | Type | Description |
|-------|------|-------------|
| `telemetry_pipeline_id` | string | `{feature_name}_{ISO_timestamp}`, set at pipeline start |
| `telemetry_total_invocations` | integer | Running count of agent invocations |
| `telemetry_total_cost_usd` | float or null | Running cost total |
| `telemetry_rework_by_unit` | object | `{unit_id: rework_count}` per unit |

These fields are in-memory accumulators written to PIPELINE_STATUS at each phase transition (piggybacking on Eva's existing pipeline-state.md updates). They enable session recovery: if Eva restarts mid-pipeline, she reads the last PIPELINE_STATUS to restore telemetry accumulators.

**Upgrade safety:** On the first pipeline after upgrade, PIPELINE_STATUS will lack telemetry fields. Eva initializes all telemetry accumulators to zero defaults (`telemetry_total_invocations: 0`, `telemetry_total_cost_usd: null`, `telemetry_rework_by_unit: {}`) when the fields are absent. No crash, no undefined values.

**Observation masking addition:**

In the "Never Mask" section, add:
- Telemetry accumulators in PIPELINE_STATUS (always-live state, already covered by the pipeline-state.md rule)

In the "Mask" section, add:
- Individual Tier 1 `agent_capture` responses after Eva has updated accumulators (the brain response confirmation is transient)

**Acceptance criteria:**
- Telemetry timing protocol documented in invocation-templates.md
- PIPELINE_STATUS fields documented with types and update frequency
- Session recovery: telemetry accumulators survive session breaks via PIPELINE_STATUS
- Observation masking rules updated for telemetry capture responses
- Dual-tree: source/ and .claude/ copies in sync

**Estimated complexity:** Medium (4 files modified, additive changes, no structural refactoring)

---

### Step 5: Documentation Update (Agatha Scope)

Update user-facing documentation to describe the telemetry feature.

**Files to modify:**
- `docs/architecture/README.md` -- add ADR-0014 to the index
- User guide sections as identified by Agatha's doc plan (if produced)

**Content:**
- ADR index entry: "ADR-0014: Agent Telemetry Dashboard -- structured pipeline metrics capture and trend analysis"
- User guide: what telemetry tracks, how to read the boot summary, how to read the pipeline-end summary, what degradation alerts mean

**Acceptance criteria:**
- ADR-0014 appears in the architecture README index
- User-facing docs explain telemetry without requiring users to read the ADR

**Estimated complexity:** Low (1-2 files, standard doc update)

---

## Comprehensive Test Specification

### Step 1 Tests: Telemetry Metrics Reference

| ID | Category | Description |
|----|----------|-------------|
| T-0014-001 | Happy | `telemetry-metrics.md` exists in both `source/references/` and `.claude/references/` with identical structure (placeholders vs literals) |
| T-0014-002 | Happy | Every Tier 1 metric from the spec has a corresponding schema entry with field name, type, source, and default |
| T-0014-003 | Happy | Every Tier 2 metric from the spec has a corresponding schema entry with aggregation rule from Tier 1 |
| T-0014-004 | Happy | Every Tier 3 metric from the spec has a corresponding schema entry with aggregation rule from Tier 2 |
| T-0014-005 | Happy | Cost estimation table covers Opus, Sonnet, and Haiku with input and output per-1K-token costs |
| T-0014-006 | Boundary | EvoScore formula handles `tests_before = 0` by returning 1.0 |
| T-0014-007 | Boundary | Every metric field has a documented default for when the data source is unavailable |
| T-0014-008 | Happy | Alert thresholds match spec exactly: cost >25% over 5, rework >2.0 for 3, first-pass QA <60% for 3, agent failures >2 same agent over 10, context >80% for 3+, EvoScore <0.9 for 3 |
| T-0014-009 | Failure | Missing data defaults are all valid values for their type (no `undefined`, no missing keys) |
| T-0014-052 | Failure | Cost estimation table covers exactly the models in `pipeline-models.md` (Opus, Sonnet, Haiku) -- no model in cost table absent from pipeline-models.md, no model in pipeline-models.md absent from cost table |
| T-0014-053 | Failure | Every Tier 2 field that aggregates from Tier 1 references a Tier 1 field name that exists verbatim in the Tier 1 schema (e.g., Tier 2 `unit_cost_usd` aggregates Tier 1 `cost_usd`, not a renamed variant) |
| T-0014-054 | Happy | `telemetry-metrics.md` documents `context_window_max` per model (Opus, Sonnet, Haiku) alongside cost rates in the cost estimation table, used by Tier 1 `context_utilization` computation |

### Step 1 Telemetry

Telemetry: File existence check for `telemetry-metrics.md` in both trees. Trigger: at ADR step completion. Absence means: reference file not created or not synced.

### Step 2 Tests: Telemetry Capture Protocol

| ID | Category | Description |
|----|----------|-------------|
| T-0014-010 | Happy | Tier 1 capture gate section exists in `pipeline-orchestration.md` with trigger "after every Agent tool completion" |
| T-0014-011 | Happy | Tier 1 capture uses `thought_type: 'insight'`, `source_agent: 'eva'`, `source_phase: 'telemetry'`, `metadata.telemetry_tier: 1` |
| T-0014-012 | Happy | Tier 2 capture gate section exists with trigger "after Roz QA PASS on build unit" |
| T-0014-013 | Happy | Tier 2 capture includes rework_cycles, first_pass_qa, unit_cost_usd, finding_counts, finding_convergence, evoscore_delta |
| T-0014-014 | Happy | Tier 3 capture gate section exists with trigger "at pipeline end, after Ellis final commit" |
| T-0014-015 | Happy | Tier 3 metadata includes all fields from spec Tier 3 table |
| T-0014-016 | Failure | Every capture gate has explicit failure handling: "log and continue, never block" |
| T-0014-017 | Failure | Protocol states brain unavailable skips all telemetry capture gates |
| T-0014-018 | Boundary | Micro pipeline rule: Tier 1 only, Tier 2 and Tier 3 skipped |
| T-0014-019 | Failure | `agent_capture` failure on Tier 1 does not prevent Tier 2 or Tier 3 capture later |
| T-0014-020 | Happy | Protocol references `telemetry-metrics.md` for schemas (not inline definitions) |
| T-0014-021 | Happy | Telemetry captures are explicitly additive -- do not replace existing brain captures (phase transitions, model-vs-outcome) |
| T-0014-022 | Boundary | `pipeline_id` format is `{feature_name}_{ISO_timestamp}` and is included in every tier's metadata |
| T-0014-023 | Regression | Existing `<protocol id="brain-capture">` section is unchanged (telemetry is a new protocol, not a modification) |
| T-0014-055 | Happy | Capture protocol documents importance graduation: Tier 1 uses `importance: 0.3`, Tier 2 uses `importance: 0.5`, Tier 3 uses `importance: 0.7` -- values explicit in the protocol text |

### Step 2 Telemetry

Telemetry: Grep for `<protocol id="telemetry-capture">` in both trees of `pipeline-orchestration.md`. Trigger: at step completion. Absence means: capture protocol not added.

### Step 3 Tests: Pipeline-End Summary + Boot Trend Query

| ID | Category | Description |
|----|----------|-------------|
| T-0014-024 | Happy | Pipeline-end summary section exists in `pipeline-orchestration.md` with format matching spec's "Pipeline complete. Telemetry summary:" block |
| T-0014-025 | Happy | Pipeline-end summary includes: cost, duration, rework rate, EvoScore, findings |
| T-0014-026 | Happy | Boot sequence step 5b exists in `default-persona.md` with `agent_search` query for telemetry data |
| T-0014-027 | Happy | Boot step 6 announcement includes telemetry trend line format |
| T-0014-028 | Boundary | First pipeline (no trend data) produces "No prior pipeline data" message at boot |
| T-0014-029 | Boundary | Micro pipeline produces abbreviated summary (invocation count + duration only) |
| T-0014-030 | Failure | Brain unavailable: pipeline-end summary still prints from in-memory accumulators |
| T-0014-031 | Failure | Brain unavailable: boot telemetry line omitted entirely (not "unavailable") |
| T-0014-032 | Happy | Degradation alerts fire only when threshold exceeded for 3+ consecutive pipelines |
| T-0014-033 | Failure | Degradation alert with only 2 consecutive breaches does NOT fire |
| T-0014-034 | Failure | Cost unavailable (no token counts) produces "Cost: unavailable (token counts not exposed)" |
| T-0014-035 | Happy | Source template `default-persona.md` uses `{pipeline_state_dir}` placeholder in step 5b |
| T-0014-036 | Happy | Installed copy `.claude/rules/default-persona.md` uses literal `docs/pipeline` in step 5b |
| T-0014-037 | Regression | Existing boot sequence steps 1-6 are unchanged except additive step 5b and step 6 telemetry line |
| T-0014-038 | Regression | Existing pipeline-end brain capture (session summary with `thought_type: 'decision'`) is unchanged |
| T-0014-039 | Happy | Boot trend query uses `agent_search` with `filter: { telemetry_tier: 3 }` (server-side metadata filter) and `source_phase == 'telemetry'` (client-side column filter), limit 10 |
| T-0014-040 | Boundary | Single pipeline in brain: boot summary shows data for 1 pipeline, no trend % change (need 2+ for comparison) |
| T-0014-056 | Boundary | Micro pipelines do NOT contribute to boot trend data (Tier 3 is skipped for Micro; boot trends query Tier 3 only). Tier 1 data from Micro invocations is still captured for per-invocation visibility but does not appear in trend summaries |

### Step 3 Telemetry

Telemetry: Grep for "step 5b" in both trees of `default-persona.md`. Trigger: at step completion. Absence means: boot sequence not extended. Telemetry: Grep for "Telemetry summary" in both trees of `pipeline-orchestration.md`. Trigger: at step completion. Absence means: pipeline-end summary not added.

### Step 4 Tests: Invocation Template + PIPELINE_STATUS

| ID | Category | Description |
|----|----------|-------------|
| T-0014-041 | Happy | Timing protocol comment block exists in `invocation-templates.md` |
| T-0014-042 | Happy | PIPELINE_STATUS documentation in `pipeline-operations.md` includes `telemetry_pipeline_id`, `telemetry_total_invocations`, `telemetry_total_cost_usd`, `telemetry_rework_by_unit` |
| T-0014-043 | Happy | Observation masking "Mask" section includes Tier 1 capture responses |
| T-0014-044 | Happy | PIPELINE_STATUS telemetry fields have documented types matching the schema |
| T-0014-045 | Boundary | Session recovery: documentation states telemetry accumulators are restored from PIPELINE_STATUS on session resume |
| T-0014-046 | Regression | Existing PIPELINE_STATUS fields (phase, roz_qa, ci_watch_*) are unchanged |
| T-0014-047 | Happy | Dual-tree sync: source/ and .claude/ copies of modified files have matching structure |
| T-0014-050 | Failure | First pipeline after upgrade: PIPELINE_STATUS read with telemetry fields absent (pre-telemetry state file). Eva initializes accumulators to zero defaults -- no crash, no undefined values |
| T-0014-051 | Failure | Observation masking does NOT mask telemetry accumulators in PIPELINE_STATUS (listed in "Never Mask" section). Only individual Tier 1 `agent_capture` responses are masked |

### Step 4 Telemetry

Telemetry: Grep for `telemetry_pipeline_id` in both trees of `pipeline-operations.md`. Trigger: at step completion. Absence means: PIPELINE_STATUS fields not added.

### Step 5 Tests: Documentation

| ID | Category | Description |
|----|----------|-------------|
| T-0014-048 | Happy | ADR-0014 entry exists in `docs/architecture/README.md` |
| T-0014-049 | Happy | ADR index entry includes title and one-line description |

### Step 5 Telemetry

Telemetry: ADR-0014 entry in README.md. Trigger: at step completion. Absence means: ADR index not updated.

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `telemetry-metrics.md` (schema definitions) | Tier 1-4 field schemas, cost table, alert thresholds | `pipeline-orchestration.md` telemetry-capture protocol (reads schema) | Step 2 consumes Step 1 |
| `pipeline-orchestration.md` Tier 1 capture gate | `agent_capture` with `metadata.telemetry_tier: 1` | `pipeline-orchestration.md` Tier 2 gate (aggregates unit cost from Tier 1) | Step 2 internal |
| `pipeline-orchestration.md` Tier 2 capture gate | `agent_capture` with `metadata.telemetry_tier: 2` | `pipeline-orchestration.md` Tier 3 gate (aggregates pipeline metrics from Tier 2) | Step 2 internal |
| `pipeline-orchestration.md` Tier 3 capture gate | `agent_capture` with `metadata.telemetry_tier: 3` | `default-persona.md` boot step 5b (queries Tier 3 for trends) | Step 3 consumes Step 2 |
| `pipeline-orchestration.md` in-memory accumulators | Running totals during pipeline | `pipeline-orchestration.md` pipeline-end summary display | Step 3 consumes Step 2 |
| `telemetry-metrics.md` alert thresholds | Threshold values per metric | `default-persona.md` boot step 5b (evaluates alerts) | Step 3 consumes Step 1 |
| `pipeline-operations.md` PIPELINE_STATUS fields | Telemetry accumulator state | Eva session recovery (reads on resume) | Step 4 consumes Step 2 |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `telemetry-metrics.md` schemas | Metric field definitions (name, type, default) | Tier 1/2/3 capture gates in `pipeline-orchestration.md` | Step 1 -> Step 2 |
| `telemetry-metrics.md` cost table | `{ model: { input_per_1k, output_per_1k } }` | Tier 1 capture gate cost_usd computation | Step 1 -> Step 2 |
| `telemetry-metrics.md` alert thresholds | `{ metric: threshold, consecutive_count: N }` | Boot step 5b degradation check | Step 1 -> Step 3 |
| Tier 1 captures (brain) | `metadata.telemetry_tier: 1` per invocation | Tier 2 unit_cost_usd aggregation | Step 2 internal |
| Tier 2 captures (brain) | `metadata.telemetry_tier: 2` per unit | Tier 3 pipeline aggregation | Step 2 internal |
| Tier 3 captures (brain) | `metadata.telemetry_tier: 3` per pipeline | Boot step 5b trend query | Step 2 -> Step 3 |
| In-memory accumulators | Running totals in Eva context | Pipeline-end summary display | Step 2 -> Step 3 |
| PIPELINE_STATUS fields | Persisted accumulators | Session recovery on resume | Step 2 -> Step 4 |

No orphan producers. Every data producer has an identified consumer in the same or a prior step.

## Data Sensitivity

No stores are introduced. All data flows through the brain's existing `agent_capture` / `agent_search` interface. The telemetry metrics contain:

| Data | Classification | Notes |
|------|---------------|-------|
| Token counts | public-safe | Operational metric, no user data |
| Cost estimates | public-safe | Derived from token counts + public pricing |
| Agent names | public-safe | Pipeline agent identifiers |
| Model names | public-safe | Public model identifiers |
| Rework counts | public-safe | Operational metric |
| Finding counts | public-safe | Counts only, not finding content |
| EvoScore | public-safe | Ratio metric |
| Duration | public-safe | Timing data |
| Feature name (in pipeline_id) | public-safe | Feature name is already in pipeline-state.md |

No auth-only data. No sensitive fields. No user-attributable metrics (per spec out-of-scope).

## Notes for Colby

1. **Dual-tree sync is the primary gotcha.** Every file has a source/ template (with `{placeholders}`) and a .claude/ installed copy (with literal values like `docs/pipeline`). Forgetting one tree is the most likely failure mode. Grep for the placeholder to verify.

2. **Pipeline-orchestration.md is large.** The new `<protocol id="telemetry-capture">` section should go after `<protocol id="brain-capture">` and before `<gate id="mandatory-gates">`. Use the same XML section/protocol/gate pattern as existing content.

3. **Boot sequence step numbering.** The current boot sequence uses 1, 2, 3, 3b, 3c, 3d, 4, 5, 6. The new step is 5b (between brain context retrieval and announcement). This matches the established sub-step pattern (3b, 3c, 3d).

4. **In-memory accumulators are ephemeral.** They exist in Eva's context window during a pipeline run. They are NOT a new data structure or file. They are written to PIPELINE_STATUS at phase transitions for session recovery only. Do not create a new file or class for them.

5. **The `agent_capture` call pattern.** Use the exact same pattern as existing captures in brain-capture protocol. The only differences are `source_phase: 'telemetry'` (instead of 'build', 'devops', etc.) and the structured `metadata` payload.

6. **Cost table will be wrong.** Anthropic's pricing changes. The hardcoded values are intentionally rough. Do not over-engineer this. A comment saying "// Approximate as of 2026-03. Update as needed." is sufficient.

7. **EvoScore edge case.** When `tests_before = 0`, the formula `(tests_after - tests_broken) / tests_before` divides by zero. The spec does not address this. The schema in telemetry-metrics.md must specify: when `tests_before = 0`, EvoScore = 1.0 (no tests to regress against).

8. **Brain context confirmed.** The brain `agent_capture` tool accepts `content` (string), `thought_type` (enum including 'insight'), `source_agent` (string), `source_phase` (string), `importance` (float), `metadata` (freeform JSON), `scope` (string). The `metadata` field is where all structured metrics go. No schema changes needed.

9. **The telemetry-metrics.md file should NOT be path-scoped.** It is a reference file loaded on-demand (like invocation-templates.md), not an always-loaded rule. No YAML frontmatter `paths:` needed. Eva reads it at pipeline start alongside pipeline-operations.md.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Tier 1 per-invocation metrics schema | Pending | T-0014-001 through T-0014-009, T-0014-010, T-0014-011, T-0014-052, T-0014-053, T-0014-054 |
| R2 | Tier 2 per-unit metrics schema + capture | Pending | T-0014-003, T-0014-012, T-0014-013 |
| R3 | Tier 3 per-pipeline metrics schema + capture | Pending | T-0014-004, T-0014-014, T-0014-015 |
| R4 | Tier 4 over-time trends at boot | Pending | T-0014-026, T-0014-027, T-0014-039, T-0014-056 |
| R5 | Eva surfaces trends at boot | Pending | T-0014-026, T-0014-027, T-0014-028 |
| R6 | Brain storage via agent_capture | Pending | T-0014-011, T-0014-020, T-0014-055 |
| R7 | Degradation alerts (3+ consecutive) | Pending | T-0014-032, T-0014-033 |
| R8 | Pipeline end summary | Pending | T-0014-024, T-0014-025 |
| R9 | Non-blocking on failure | Pending | T-0014-016, T-0014-017, T-0014-030, T-0014-031, T-0014-050 |
| R10 | Token counts unavailable handling | Pending | T-0014-007, T-0014-034 |
| R11 | First pipeline (no trend data) | Pending | T-0014-028 |
| R12 | Micro pipeline: Tier 1 only | Pending | T-0014-018, T-0014-029, T-0014-056 |
| R13 | Cost without pricing handling | Pending | T-0014-005, T-0014-034 |
| R14 | Alert fatigue (3+ consecutive) | Pending | T-0014-032, T-0014-033 |
| R15 | Dual-tree sync | Pending | T-0014-001, T-0014-035, T-0014-036, T-0014-047 |
| R16 | All 4 tiers ship together | Pending | Steps 1-3 deliver all tiers |
| R17 | Folds #12 + #14 | Pending | T-0014-006 (EvoScore), T-0014-013 (evoscore_delta), T-0014-025 (EvoScore in summary) |
| R18 | Capture overhead < 2s | Pending | NFR -- verified by observation during first pipeline run |
| R19 | Boot trend query < 5s | Pending | NFR -- verified by observation during first pipeline run |
| R20 | No external dashboard | Pending | No files create any web UI or API endpoint |

**Architectural decisions not in spec:**
- `pipeline_id` format (`{feature_name}_{ISO_timestamp}`) -- invented here for brain query grouping
- In-memory accumulators persisted to PIPELINE_STATUS for session recovery -- not in spec but required for the session break scenario
- Telemetry captures as additive (not replacing existing brain captures) -- design decision to avoid breaking existing brain capture model
- Step 5b placement in boot sequence (after brain context retrieval, before announcement) -- follows the sub-step pattern established by 3b/3c/3d

**Rejected alternatives:**
- Separate Telemetry Agent: overhead of double invocations per agent return
- Disk-based telemetry JSON: diverges from brain-as-store pattern, no query capability

**Technical constraints discovered:**
- `pipeline-orchestration.md` is already the largest rules file; this adds ~120 lines. No structural solution beyond keeping the new protocol tightly scoped.
- Agent tool metadata availability (token counts, timing) is unverified. The design accounts for this but Tier 1 metrics may be sparse initially.
- EvoScore formula has a division-by-zero edge case when `tests_before = 0` that the spec does not address. Handled in the schema with a documented default.
