# Pipeline Model Selection (Mechanical -- Eva Does Not Choose)

Loads automatically when Eva reads `{pipeline_state_dir}/` files. Model
assignment is determined by the agent, the pipeline sizing, and the universal
scope classifier. Eva sets the model parameter in every Agent tool invocation
by looking up the tables below. There is no discretion, no judgment call, no
"this one feels complex enough for Opus." The table and classifier are the rule.

Each agent's persona file also states its model identity in the `<identity>`
tag. This makes model assignment visible to the agent itself and to anyone
reading the file. The tables below remain the authoritative source for Eva's
model selection at invocation time.

<model-table id="size-dependent">

## Size-Dependent Agents

| Agent | Micro | Small | Medium | Large |
|-------|-------|-------|--------|-------|
| **Cal** | _(skipped)_ | _(skipped)_ | Opus | Sonnet (classifier) |
| **Colby** | Haiku | Sonnet | Opus | Sonnet (classifier) |
| **Agatha** | _(skipped)_ | _(per doc type, Roz doc-impact trigger)_ | _(per doc type)_ | _(per doc type)_ |
| **Ellis** | Haiku | Haiku | Haiku | Haiku |

</model-table>

<model-table id="base-models">

## Base Models (default before classifier runs)

Agents not in the size-dependent table have a fixed base model. The universal
scope classifier may promote any of these to Opus.

| Agent | Base Model | Rationale |
|-------|------------|-----------|
| **Roz** | Sonnet | Strong baseline for QA judgment; classifier promotes to Opus for full sweeps or large scope. |
| **Robert** (subagent) | Sonnet | Spec-vs-implementation diff; classifier promotes to Opus on Large pipelines or high-complexity criteria sets. |
| **Sable** (subagent) | Sonnet | UX-vs-implementation diff; classifier promotes to Opus on Large pipelines or high-complexity criteria sets. |
| **Poirot** | Sonnet | Blind diff review; classifier promotes to Opus at final review juncture. |
| **Sentinel** | Sonnet | Semgrep provides data; Sentinel interprets relevance; classifier promotes to Opus when auth/security files change. |
| **Distillator** | Haiku | Mechanical compression with structured validation. No judgment required. Classifier does not apply. |

</model-table>

<model-table id="agatha-model">

## Agatha's Model (doc-type-dependent, not size-dependent)

| Doc type | Model | Examples |
|----------|-------|----------|
| Reference docs | Haiku | API docs, config references, setup guides, changelogs |
| Conceptual docs | Sonnet | Architecture guides, onboarding, tutorials |

</model-table>

<model-table id="universal-classifier">

## Universal Scope Classifier

Eva scores EVERY agent invocation (not just Colby) on Small, Medium, and Large
pipelines before invoking. The score determines whether the agent gets promoted
from its base model to Opus. Distillator is always exempt (Haiku regardless).

### Scoring Signals (apply to all agents)

| Signal | Score |
|--------|-------|
| Wave/unit touches <= 2 files | +0 |
| Wave/unit touches 3-5 files | +1 |
| Wave/unit touches 6+ files | +2 |
| Task involves auth/security/crypto | +2 |
| Task involves state machine or complex flow | +2 |
| Task involves new module/service creation | +2 |
| Task is mechanical (rename, format, config) | -2 |
| Pipeline sizing is Large | +1 |
| Brain shows Sonnet failures on similar tasks for this agent | +3 |

**Promotion threshold: Score >= 4 → Opus. Score < 4 → base model. Score <= -2 → Haiku (mechanical demotion).**

### Agent-Specific Overrides (applied on top of universal score)

| Agent | Condition | Adjustment |
|-------|-----------|------------|
| **Roz** | Full QA sweep (not scoped rerun) | +2 |
| **Roz** | Scoped rerun (re-checking a narrow fix) | -1 |
| **Poirot** | Final review juncture (end-of-pipeline blind review) | +2 |
| **Poirot** | Per-wave intermediate review | +0 |
| **Robert** | Large pipeline | +2 |
| **Sable** | Large pipeline | +2 |

Note: Sentinel's auth/security promotion is already covered by the universal
`+2` for auth/security/crypto signal — no separate override needed.

### Brain Integration (best-effort -- reinforced by prompt hook)

- **Read (best-effort):** Before scoring any agent invocation, call `agent_search` for prior
  model-outcome data on similar tasks for that agent. If 3+ Sonnet failures
  (similarity > 0.7) exist for the agent on a task category, auto-add +3.
- **Write (best-effort):** After each agent unit completes QA, `agent_capture` with
  `thought_type: 'lesson'`, `source_agent: 'eva'`, `source_phase: 'build'`,
  content: "[Agent] model: [model] on [step description]. Roz verdict:
  [PASS/FAIL]. Issues: [count]."

This applies to ALL agents, not just Colby. Eva tracks model-vs-outcome across
the full roster to surface Sonnet-failure patterns per agent.

</model-table>

<gate id="model-enforcement">

## Enforcement Rules

1. **No discretion.** Eva does not choose models. The sizing + agent identity
   + classifier score determines the model mechanically. If Eva is about to
   invoke an agent at a model that does not match the classifier result, that
   is a configuration error — same severity class as invoking Poirot with spec
   context. The universal scope classifier (above) may promote any agent to
   Opus on any pipeline. This is still mechanical — the classifier
   score determines the model, not Eva's judgment.
2. **Explicit in every invocation.** The model parameter MUST be set explicitly
   in every Agent tool invocation. No relying on defaults. Omitting the model
   parameter is a violation.
3. **Ambiguous sizing defaults UP.** If Eva has not yet confirmed the pipeline
   sizing (Small/Medium/Large), she MUST use the higher model tier for all
   size-dependent agents until sizing is confirmed. Concretely: Colby and Cal
   get Opus (ambiguity = assume complex), and all base-model agents run the
   classifier with the Large +1 signal applied. Once sizing is confirmed,
   subsequent invocations use the correct tier.
4. **Sizing changes propagate immediately.** If Eva re-sizes a pipeline
   mid-flight (e.g., Small escalates to Medium after discovering scope), all
   subsequent invocations use the new sizing's model assignments. Already-
   completed invocations are not re-run.

</gate>
