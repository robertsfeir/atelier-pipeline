---
paths:
  - "docs/pipeline/**"
---

# Pipeline Model Selection (Mechanical -- Eva Does Not Choose)

Loads automatically when Eva reads `{pipeline_state_dir}/` files. Model
assignment is determined by the agent and the pipeline sizing. Eva sets
the model parameter in every Agent tool invocation by looking up the
tables below. There is no discretion, no judgment call, no "this one
feels complex enough for Opus." The table is the rule.

## Fixed-Model Agents (always the same, regardless of sizing)

| Agent | Model | Rationale |
|-------|-------|-----------|
| **Roz** | Opus | QA judgment is non-negotiable. Sonnet missed bugs in past runs (see retro: Self-Reporting Bug Codification). |
| **Robert** (subagent) | Opus | Product acceptance review requires strong reasoning to diff spec intent against implementation. |
| **Sable** (subagent) | Opus | UX acceptance review requires strong reasoning to diff UX intent against implementation. |
| **Poirot** | Opus | Blind review with no context requires the strongest reasoning to find issues from a raw diff alone. |
| **Distillator** | Haiku | Mechanical compression with structured validation. No judgment required. |
| **Ellis** | Sonnet | Reads diff, writes commit message, runs git. Zero ambiguity in the task. |

## Size-Dependent Agents

| Agent | Small | Medium | Large |
|-------|-------|--------|-------|
| **Cal** | _(skipped)_ | Opus | Opus |
| **Colby** | Sonnet | Sonnet | Opus |
| **Agatha** | _(per doc type, Roz doc-impact trigger)_ | _(per doc type)_ | _(per doc type)_ |

## Agatha's Model (doc-type-dependent, not size-dependent)

| Doc type | Model | Examples |
|----------|-------|----------|
| Reference docs | Haiku | API docs, config references, setup guides, changelogs |
| Conceptual docs | Sonnet | Architecture guides, onboarding, tutorials |

## Enforcement Rules

1. **No discretion.** Eva does not choose models. The sizing + agent
   identity determines the model mechanically. If Eva is about to invoke
   Colby on a Small pipeline with `model: "opus"`, that is a configuration
   error -- same severity class as invoking Poirot with spec context.
2. **Explicit in every invocation.** The model parameter MUST be set
   explicitly in every Agent tool invocation. No relying on defaults.
   Omitting the model parameter is a violation.
3. **Ambiguous sizing defaults UP.** If Eva has not yet confirmed the
   pipeline sizing (Small/Medium/Large), she MUST use the higher model
   tier for size-dependent agents until sizing is confirmed. Concretely:
   Colby gets Opus, Cal gets Opus. Once sizing is confirmed, subsequent
   invocations use the correct tier.
4. **Sizing changes propagate immediately.** If Eva re-sizes a pipeline
   mid-flight (e.g., Small escalates to Medium after discovering scope),
   all subsequent invocations use the new sizing's model assignments.
   Already-completed invocations are not re-run.
