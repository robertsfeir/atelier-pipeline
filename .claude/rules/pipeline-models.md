---
paths:
  - "docs/pipeline/**"
---
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

| Tier | Task class | Model | Base effort | Typical agents | Effort +1 when |
|------|------------|-------|-------------|----------------|----------------|
| Tier 1 | Mechanical -- no reasoning | Haiku | low | Ellis, Explore, Distillator, Agatha (reference), brain-extractor | -- (stays low) |
| Tier 2 | Supporting reasoning -- review / acceptance / compliance | Opus | medium | Robert (any), Sable (any), Sentinel, Deps, Agatha (conceptual), Colby (rework), Colby (first-build Small), Roz (scoped rerun) | Large pipeline OR auth / security / crypto |
| Tier 3 | Critical-path reasoning -- creates / verifies shipped artifact | Opus | high | Colby (first-build Medium+), Roz (full sweep Medium+), Poirot, Darwin | Auth / security / crypto OR Large pipeline OR Poirot at final juncture (-> xhigh) |
| Tier 4 | Architectural design | Opus | xhigh | Cal | Large + new module (already at ceiling; xhigh is max) |

</model-table>

<model-table id="promotion-signals">

## Promotion Signals (one rung each)

| Signal | Applies to tier | Effect |
|--------|-----------------|--------|
| Auth / security / crypto files touched | 2, 3 | +1 rung (medium -> high -> xhigh) |
| Pipeline sizing = Large | 2, 3 | +1 rung |
| New module / service creation | 3 | +1 rung |
| Poirot at final-juncture blind review | 3 only | +1 rung (high -> xhigh) |
| Task is read-only evidence collection (no ADR, no code) | 2 | -1 rung (floor low) |
| Task is mechanical (format, rename, config-only) | 2, 3 | -1 rung (floor low) |

**Rules:**

1. Promotions stack to a maximum of one rung above base per signal. If two
   signals both apply, effort still goes up exactly one rung (not two). The
   table is not additive; signals are existence-checks, not scores.
2. **Floor: `low`. Ceiling: `xhigh`.** Effort is never below `low` and never
   above `xhigh` (max). Demotions cannot take effort below the floor;
   promotions cannot take it above the ceiling.
3. Tier 1 effort does not adjust -- base `low` is both floor and ceiling for
   this tier. Haiku base means the pattern-matching surface is bounded; more
   effort does not rescue mechanical misapplication, and demotion below `low`
   is impossible.
4. Tier 4 (Cal) is already at `xhigh` base; further signals have no effect.

</model-table>

<model-table id="agent-assignments">

## Per-Agent Assignment Table

Authoritative runtime lookup. Eva sets `model` and `effort` in every Agent
tool invocation based on this table plus the promotion signals above.

| Agent | Tier | Base model | Base effort | Rationale (one line) |
|-------|------|------------|-------------|----------------------|
| **Cal** | 4 | opus | xhigh | Architectural deliberation dominates pattern-matching; thinking tokens pay for themselves |
| **Colby** | 3 (build) / 2 (rework, small first-build) | opus | high / medium | Critical-path artifact; rework or small scope = bounded |
| **Roz** | 3 (sweep Medium+) / 2 (scoped rerun, small sweep) | opus | high / medium | Verifies shipped artifact; scoped rerun = bounded |
| **Poirot (investigator)** | 3 | opus | high (xhigh at final juncture) | Blind diff review; final juncture = last defense, deliberation worth it |
| **Darwin** | 3 | opus | high | Analyzes pipeline fitness; shapes future structural proposals |
| **Robert (acceptance)** | 2 | opus | medium (high on Large / auth) | Spec-vs-implementation diff; capability-bounded review |
| **robert-spec (producer)** | 2 | opus | medium (high on Large / auth) | Spec production; capability-bounded authoring |
| **Sable (acceptance)** | 2 | opus | medium (high on Large / auth) | UX-vs-implementation diff |
| **sable-ux (producer)** | 2 | opus | medium (high on Large / auth) | UX doc authoring |
| **Sentinel** | 2 | opus | medium (high on auth / crypto) | Pattern-matching on Semgrep output; excess thinking -> false positives. **Effort demotion vs prior** |
| **Deps** | 2 | opus | medium | Version diff + CVE lookup; bounded judgment |
| **Agatha (conceptual docs)** | 2 | opus | medium | Architecture guides, onboarding; bounded reasoning. **Frontmatter default** |
| **Agatha (reference docs)** | 1 | haiku | low | Reference lookup-and-emit. Runtime override by Eva when task is reference-typed |
| **Ellis** | 1 | haiku | low | Commit-message composition is mechanical. **Effort demotion vs prior** |
| **Distillator** | 1 | haiku | low | Structured compression. **Effort demotion vs prior** |
| **brain-extractor** (hook) | 1 | haiku | low | Mechanical extraction from SubagentStop payload |
| **Explore** (discovered) | 1 | haiku | low | File collection only; no synthesis |

</model-table>

## Runtime Lookup Procedure

For every Agent tool invocation:

1. Identify the agent and the task class it is performing on this run
   (for example, Colby first-build Medium is a Tier 3 task; Colby rework is
   a Tier 2 task).
2. Look up the base `model` + base `effort` in the Per-Agent Assignment Table.
3. Apply promotion signals from the Promotion Signals table; effort moves by
   at most one rung regardless of how many signals fire.
4. Clamp to the floor (`low`) and ceiling (`xhigh`).
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
3. **Ambiguous sizing defaults UP.** If Eva has not yet confirmed the pipeline
   sizing (Small / Medium / Large), she MUST assume Large for promotion
   purposes: Tier 2 and Tier 3 agents both get the `+1 rung` Large signal,
   effort is clamped at ceiling, and the higher tier is used for any agent
   that occupies multiple tiers (Colby, Roz). Once sizing is confirmed,
   subsequent invocations use the correct tier and signal set.
4. **Sizing changes propagate immediately.** If Eva re-sizes a pipeline
   mid-flight (e.g., Small escalates to Medium after discovering scope), all
   subsequent invocations use the new sizing's tier / signal lookup.
   Already-completed invocations are not re-run.

</gate>
