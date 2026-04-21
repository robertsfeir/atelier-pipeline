# Pipeline Model Selection (Mechanical -- Eva Does Not Choose)

Loads automatically when Eva reads `docs/pipeline/` files. Model and
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
| Tier 1 | Mechanical -- no reasoning | Sonnet / Haiku | low | Ellis, Explore (haiku), Distillator, brain-extractor | -- (stays low) |
| Tier 2 | Supporting reasoning -- review / acceptance / compliance / synthesis | Sonnet / Opus | medium | Robert (acceptance), Sable (acceptance), Sentinel, Agatha, Synthesis, Colby (rework), Colby (first-build Small) | Read-only / mechanical -- -1 rung (floor low) |
| Tier 3 | Critical-path reasoning -- creates / verifies shipped artifact | Opus | high / medium | Colby (first-build Medium+), Poirot, Darwin | Poirot at final juncture (-> xhigh) |
| Tier 4 | Architectural design | Opus | xhigh | Sarah | (already at ceiling; `xhigh` is the ceiling value) |

</model-table>

### Adaptive-Thinking Rationale

Per Anthropic's Opus 4.7 guidance, `effort` controls a model's propensity to
think adaptively, not a fixed thinking budget. **Fixed thinking budgets are unsupported** in Opus 4.7.
At `medium`, adaptive-thinking capacity is bounded
even when the model wants to reach for more -- appropriate for coverage-oriented
review where over-reading inflates false positives (Poirot standard review). At `high`,
full adaptive thinking is available -- appropriate for execution with branching
sub-decisions (Colby first-build, Poirot standard review). At `xhigh`, the
model deliberates fully -- the default for coding and architecture (Sarah,
Poirot at final juncture). `max` is evaluation-only: prone to overthinking and
degraded production output. Ceiling stays `xhigh`.

<model-table id="promotion-signals">

## Promotion Signals (one rung each)

| Signal | Applies to tier | Effect |
|--------|-----------------|--------|
| Poirot at final-juncture blind review | 3 only | +1 rung (high -> xhigh) |
| Task is read-only evidence collection (no ADR, no code) | 2 | -1 rung (floor low) |
| Task is mechanical (format, rename, config-only) | 2, 3 | -1 rung (floor low) |

**Rules:**

1. Promotions stack to a maximum of one rung above base per signal. If two
   signals both apply, effort still goes up exactly one rung (not two). The
   table is not additive; signals are existence-checks, not scores.
2. **Floor: `low`. Ceiling: `xhigh`.** Effort is never below `low` and never
   above `xhigh`. Demotions cannot take effort below the floor; promotions
   cannot take it above the ceiling. **`max` is forbidden** (see Enforcement
   Rule 5).
3. Tier 1 effort does not adjust -- base `low` is both floor and ceiling for
   this tier. The pattern-matching surface is bounded; more effort does not
   rescue mechanical misapplication, and demotion below `low` is impossible.
4. Tier 4 (Sarah) is already at `xhigh` base; further signals have no effect.

</model-table>

<model-table id="agent-assignments">

## Per-Agent Assignment Table

Authoritative runtime lookup. Eva sets `model` and `effort` in every Agent
tool invocation based on this table plus the promotion signals above.

| Agent | Tier | Base model | Base effort | Rationale (one line) |
|-------|------|------------|-------------|----------------------|
| **Sarah** | 4 | opus | xhigh | Architectural deliberation dominates pattern-matching; thinking tokens pay for themselves |
| **Colby** | 3 (build) / 2 (rework, small first-build) | opus | high / medium | Critical-path artifact; high exposes adaptive thinking on execution sub-decisions |

| **Poirot (investigator)** | 3 | opus | high (xhigh at final juncture) | Blind diff review; final juncture = last defense, deliberation worth it |
| **Sherlock** | 3 | opus | high | Diagnose-only bug hunt with fresh general-purpose isolation; no final-juncture promotion (runs before fix, not at review); isolation from session context is the load-bearing property |
| **Robert (acceptance)** | 2 | sonnet | medium | Spec-vs-implementation diff; structured review is Sonnet-capable |
| **robert-spec (producer)** | 2 | opus | medium | Spec authoring requires generative capability |
| **Sable (acceptance)** | 2 | sonnet | medium | UX-vs-implementation diff; structured review is Sonnet-capable |
| **sable-ux (producer)** | 2 | opus | medium | UX doc authoring requires generative capability |
| **Sentinel** | 2 | opus | low | Pattern-matching on Semgrep output; excess thinking produces false positives. Mechanical task signal -- effort demoted medium→low. |
| **Agatha** | 2 | opus | medium | Documentation authoring; conceptual reasoning. Always Tier 2 (no runtime override) |
| **Synthesis** (new) | 2 | sonnet | low | Filter/rank/trim of scout output; no judgment, no opinions |
| **Ellis** | 1 | sonnet | low | Commit-message composition; Sonnet/low cheaper per successful pass than Haiku rework |
| **Distillator** | 1 | sonnet | low | Structured compression; Sonnet/low preserves load-bearing facts Haiku drops |
| **brain-extractor** (hook) | 1 | sonnet | low | Mechanical extraction from SubagentStop payload; Sonnet/low less error-prone than Haiku |
| **Explore** (scouts) | 1 | haiku | low | File/grep/read only; no synthesis |

</model-table>

## Runtime Lookup Procedure

For every Agent tool invocation:

1. Identify the agent and the task class it is performing on this run
   (for example, Colby first-build Medium is a Tier 3 task; Colby rework is
   a Tier 2 task).
2. Look up the base `model` + base `effort` in the Per-Agent Assignment Table.
3. Apply promotion signals from the Promotion Signals table; effort moves by
   at most one rung regardless of how many signals fire.
4. Clamp to the floor (`low`) and ceiling (`xhigh`). `max` is forbidden.
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
5. **max effort is forbidden.** Per Anthropic's Opus 4.7 adaptive-thinking
   guidance, `max` is evaluation-only: prone to overthinking and degraded
   output on production workloads. Ceiling is `xhigh`. Eva MUST NOT invoke
   any agent at `effort: max`. Hypothetical invocations with `max` in a draft
   prompt are a configuration error, same class as omitting `effort`.

</gate>
