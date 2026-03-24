---
paths:
  - "docs/pipeline/**"
---

# Pipeline Model Selection (Mechanical -- Eva Does Not Choose)

Loads automatically when Eva reads `docs/pipeline/` files. Model
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

| Agent | Micro | Small | Medium | Large |
|-------|-------|-------|--------|-------|
| **Cal** | _(skipped)_ | _(skipped)_ | Opus | Opus |
| **Colby** | Haiku | Sonnet | Sonnet | Opus |
| **Agatha** | _(skipped)_ | _(per doc type, Roz doc-impact trigger)_ | _(per doc type)_ | _(per doc type)_ |
| **Ellis** | Sonnet | Sonnet | Sonnet | Sonnet |

## Agatha's Model (doc-type-dependent, not size-dependent)

| Doc type | Model | Examples |
|----------|-------|----------|
| Reference docs | Haiku | API docs, config references, setup guides, changelogs |
| Conceptual docs | Sonnet | Architecture guides, onboarding, tutorials |

## Task-Level Complexity Classifier (Colby Only)

On Small and Medium pipelines, Eva scores each ADR step before invoking
Colby. The score determines whether Colby gets Opus (for that step) or
stays on Sonnet. This applies ONLY to Colby -- Roz, Poirot, Robert, and
Sable model assignments are never changed by this classifier.

| Signal | Score |
|--------|-------|
| <= 2 files modified | +0 |
| 3-5 files modified | +1 |
| 6+ files modified | +2 |
| Creates new module/service | +2 |
| Touches auth/security | +2 |
| State machine or complex flow | +2 |
| CRUD / standard pattern | +0 |
| Brain shows Sonnet failures on similar tasks | +3 |

**Score >= 3 -> Opus. Score < 3 -> Sonnet.** Large pipelines are already
all-Opus for Colby, so the classifier is skipped.

**Brain integration:**
- **Read:** Before scoring, `agent_search` for prior model-outcome data
  on similar tasks. 3+ Sonnet failures (similarity > 0.7) on a task
  category -> auto-add +3.
- **Write:** After each Colby unit completes QA, `agent_capture` with
  `thought_type: 'lesson'`, `source_agent: 'eva'`,
  `source_phase: 'build'`, content: "Colby model: [model] on
  [step description]. Roz verdict: [PASS/FAIL]. Issues: [count]."

## Enforcement Rules

1. **No discretion.** Eva does not choose models. The sizing + agent
   identity determines the model mechanically. If Eva is about to invoke
   Colby on a Small pipeline with `model: "opus"`, that is a configuration
   error -- same severity class as invoking Poirot with spec context.
   **Exception:** The task-level complexity classifier (above) may promote
   Colby to Opus on Small/Medium pipelines. This is still mechanical --
   the classifier score determines the model, not Eva's judgment.
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
