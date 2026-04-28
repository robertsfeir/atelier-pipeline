# Pipeline Model Selection (Mechanical -- Eva Does Not Choose)

Loads automatically when Eva reads `{pipeline_state_dir}/` files. Model and
effort assignment follows a 4-tier task-class model: the agent's task class
determines the base `model` + `effort` pair, and a small set of promotion
signals adjust `effort` by exactly one rung. Eva sets both parameters
explicitly in every Agent tool invocation by looking up the tables below.
There is no discretion, no judgment call, no "this one feels complex enough
for Opus." The tables are the rule.

Each agent's persona frontmatter also declares its base `model` and `effort`
so the runtime has a sane fallback. The tables below remain the authoritative
source for Eva's invocation-time selection.

Model follows task class, not agent identity. A single agent can occupy
different task classes on different runs. Pipeline sizing is a tier-picker
signal only; it does not set the model.

<model-table id="task-class-tiers">

## Four-Tier Task-Class Model

| Tier | Task class | Model | Base effort | Typical agents | Effort adjustment signal |
|------|------------|-------|-------------|----------------|--------------------------|
| Tier 1 | Mechanical -- no reasoning | Sonnet / Haiku | low | Ellis, scout (haiku), Distillator | -- (stays low) |
| Tier 2 | Supporting reasoning -- review / acceptance / compliance / synthesis | Sonnet / Opus | medium | Robert (acceptance), Sable (acceptance), Sentinel, Agatha, Synthesis, Colby (rework), Colby (first-build Small) | Read-only / mechanical -- -1 rung (floor low) |
| Tier 3 | Critical-path reasoning -- creates / verifies shipped artifact | Opus | high / medium | Colby (first-build Medium+), Poirot, Darwin | (no further promotion -- `high` is ceiling) |
| Tier 4 | Architectural design | Opus | high | Sarah | (already at ceiling; `high` is the ceiling value) |

</model-table>

### Adaptive-Thinking Rationale

Per Anthropic's Opus 4.7 guidance, `effort` controls a model's propensity to
think adaptively, not a fixed thinking budget. **Fixed thinking budgets are unsupported** in Opus 4.7.
At `medium`, adaptive-thinking capacity is bounded
even when the model wants to reach for more -- appropriate for coverage-oriented
review where over-reading inflates false positives (Poirot standard review). At `high`,
full adaptive thinking is available -- appropriate for execution with branching
sub-decisions (Colby first-build, Poirot standard review). `max` is evaluation-only: prone to overthinking and
degraded production output. Ceiling stays `high`. `xhigh` and `max` are forbidden on production workloads -- both cause excessive context burn without quality gain.

### Opus 4.7 Web-Search Regression

Opus 4.7 has a known regression on agentic web search. No pipeline agent
tool list includes `WebSearch` or `WebFetch`. Eva's auto-routing must not
synthesize these tools into agent invocations -- if a task genuinely
requires live web data, surface that as a constraint to the user rather
than routing to an agent that will silently degrade.

<model-table id="promotion-signals">

## Promotion Signals (one rung each)

| Signal | Applies to tier | Effect |
|--------|-----------------|--------|
| Task is read-only evidence collection (no ADR, no code) | 2 | -1 rung (floor low) |
| Task is mechanical (format, rename, config-only) | 2, 3 | -1 rung (floor low) |

**Rules:**

1. Promotions stack to a maximum of one rung above base per signal. If two
   signals both apply, effort still goes up exactly one rung (not two). The
   table is not additive; signals are existence-checks, not scores.
2. **Floor: `low`. Ceiling: `high`.** Effort is never below `low` and never
   above `high`. Demotions cannot take effort below the floor; promotions
   cannot take it above the ceiling. **`xhigh` and `max` are forbidden** (see Enforcement
   Rule 5).
3. Tier 1 effort does not adjust -- base `low` is both floor and ceiling for
   this tier. The pattern-matching surface is bounded; more effort does not
   rescue mechanical misapplication, and demotion below `low` is impossible.
4. Tier 4 (Sarah) is already at `high` base; further signals have no effect.

</model-table>

<model-table id="agent-assignments">

## Per-Agent Assignment Table

Authoritative runtime lookup. Eva sets `model` and `effort` in every Agent
tool invocation based on this table plus the promotion signals above.

| Agent | Tier | Base model | Base effort | Rationale (one line) |
|-------|------|------------|-------------|----------------------|
| **Sarah** | 4 | opus | high | Architectural deliberation dominates pattern-matching; `high` is sufficient for ADR-scale deliberation |
| **Colby** | 3 (build) / 2 (rework, small first-build) | opus | high / medium | Critical-path artifact; high exposes adaptive thinking on execution sub-decisions |

| **Poirot (investigator)** | 3 | opus | high | Blind diff review; `high` is ceiling, no further promotion |
| **Sherlock** | 3 | opus | high | Diagnose-only bug hunt with fresh general-purpose isolation; no final-juncture promotion (runs before fix, not at review); isolation from session context is the load-bearing property |
| **Robert (acceptance)** | 2 | sonnet | medium | Spec-vs-implementation diff; structured review is Sonnet-capable |
| **robert-spec (producer)** | 2 | opus | medium | Spec authoring requires generative capability |
| **Sable (acceptance)** | 2 | sonnet | medium | UX-vs-implementation diff; structured review is Sonnet-capable |
| **sable-ux (producer)** | 2 | opus | medium | UX doc authoring requires generative capability |
| **Sentinel** | 2 | sonnet | low | Pattern-matching SAST with effort: low suppresses Opus reasoning; Sonnet matches the actual workload. Mechanical task signal -- effort demoted medium→low. |
| **Agatha** | 2 | opus | medium | Documentation authoring; conceptual reasoning. Always Tier 2 (no runtime override) |
| **synthesis** | 2 | sonnet | low | Filter/rank/trim of scout output; no judgment, no opinions. Registered subagent (ADR-0048) — frontmatter pins `claude-sonnet-4-6`; invocation omits the `model` parameter |
| **Ellis** | 1 | sonnet | low | Commit-message composition; Sonnet/low cheaper per successful pass than Haiku rework |
| **Distillator** | 1 | sonnet | low | Structured compression; Sonnet/low preserves load-bearing facts Haiku drops |
| **scout** | 1 | haiku | low | File/grep/read only; no synthesis. Registered subagent (ADR-0048) — frontmatter pins `claude-haiku-4-5-20251001`; invocation omits the `model` parameter |

</model-table>

<model-table id="provider-shaped-model-ids">

## Provider-Shaped Model ID Translation (ADR-0054)

The tier table above uses logical names (opus/sonnet/haiku). Eva resolves
each logical name to a provider-shaped model ID at invocation time by
reading `model_provider` from `{pipeline_state_dir}/../pipeline-config.json`
(field default `anthropic`). Credentials remain in the Claude Code
environment configuration -- the pipeline emits IDs, it does not hold keys.

| Logical name | anthropic (default) | bedrock | vertex |
|--------------|---------------------|---------|--------|
| **opus** | `claude-opus-4-7` | `anthropic.claude-opus-4-7-20250514-v1:0` | `claude-opus@002` |
| **sonnet** | `claude-sonnet-4-6` | `anthropic.claude-sonnet-4-6-20250514-v1:0` | `claude-sonnet@001` |
| **haiku** | `claude-haiku-4-5-20251001` | `anthropic.claude-haiku-4-5-20251001-v1:0` | `claude-haiku@001` |

**Resolution rules:**

1. Eva reads `model_provider` from `pipeline-config.json` once at session
   boot and caches the value. Default is `anthropic` -- existing deployments
   are unaffected until they opt in.
2. For every Agent tool invocation, Eva translates the logical name from the
   per-agent assignment table to the provider-shaped ID using the row above.
3. Frontmatter-pinned subagents (scout, synthesis -- ADR-0048) are not
   re-translated by Eva. Their frontmatter holds the explicit `claude-*`
   Anthropic ID; Bedrock/Vertex deployments must rewrite those frontmatter
   values at install time, not at invocation time.
4. Unknown `model_provider` values are a configuration error. Eva does not
   fall back silently; she surfaces the unknown value and stops.

**Voyage AI is permanently excluded.** Gemini is deferred (768-dim
embeddings incompatible with the brain's `vector(1536)` schema, non-OpenAI
wire format) -- not because of routing complexity, but because the
schema-migration cost has not been paid. See ADR-0054 for the full decision.

</model-table>

## Runtime Lookup Procedure

For every Agent tool invocation:

1. Identify the agent and the task class it is performing on this run
   (for example, Colby first-build Medium is a Tier 3 task; Colby rework is
   a Tier 2 task).
2. Look up the base `model` + base `effort` in the Per-Agent Assignment Table.
3. Apply promotion signals from the Promotion Signals table; effort moves by
   at most one rung regardless of how many signals fire.
4. Clamp to the floor (`low`) and ceiling (`high`). `xhigh` and `max` are forbidden.
5. Set `model` and `effort` explicitly on the Agent tool call. Omission is a
   violation of the enforcement gate below.

<gate id="model-enforcement">

## Enforcement Rules

1. **No discretion.** Eva does not choose models or effort. The agent's task
   class determines the tier, the tier determines base `model` + base
   `effort`, and the promotion signals mechanically adjust effort by one rung.
   If Eva is about to invoke an agent at a `model` or `effort` that does not
   match the lookup, that is a configuration error -- same severity class as
   invoking Poirot with spec context.
2. **Explicit in every invocation.** Both the `model` and `effort` parameters
   MUST be set explicitly in every Agent tool invocation. No relying on
   frontmatter defaults. Omitting either parameter is a violation.
3. **Ambiguous sizing defaults to higher tier.** If Eva has not yet confirmed
   the pipeline sizing (Small / Medium / Large), she MUST treat sizing as
   Large for tier-selection purposes only: Colby uses its higher tier
   (Tier 3) on first-build. Effort is NOT affected by ambiguous sizing --
   the Large effort-promotion signal was removed by ADR-0042. Once sizing is
   confirmed, subsequent invocations use the correct tier.
4. **Sizing changes propagate immediately.** If Eva re-sizes a pipeline
   mid-flight (e.g., Small escalates to Medium after discovering scope), all
   subsequent invocations use the new sizing's tier / signal lookup.
   Already-completed invocations are not re-run.
5. **`xhigh` and `max` effort are forbidden.** Per Anthropic's Opus 4.7 adaptive-thinking
   guidance and tokenizer regression research, both `xhigh` and `max` cause excessive
   context burn on production workloads without quality gain. Ceiling is `high`. Eva MUST NOT invoke
   any agent at `effort: xhigh` or `effort: max`. Hypothetical invocations with either value are a configuration error, same class as omitting `effort`.

</gate>
