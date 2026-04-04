# ADR-0016: Darwin -- Self-Evolving Pipeline Engine

## DoR: Requirements Extracted

| # | Requirement | Source | Priority |
|---|-------------|--------|----------|
| R1 | Darwin agent persona at `source/shared/agents/darwin.md` + `.claude/agents/darwin.md` | Spec AC#1, context | Must |
| R2 | `darwin_enabled` config flag in `pipeline-config.json`, default `false` | Spec AC#2, context | Must |
| R3 | Setup Step 6e offers Darwin opt-in (after Deps Step 6d, before Brain) | Spec AC#3, context | Must |
| R4 | `/darwin` slash command for on-demand invocation, gated on `darwin_enabled` | Spec AC#4, context | Must |
| R5 | Darwin reads brain telemetry (Tier 1-3) via `agent_search` with telemetry filters | Spec AC#5, data sources table | Must |
| R6 | Fitness assessment: thriving/struggling/failing per agent based on telemetry metrics | Spec AC#6, fitness scoring table | Must |
| R7 | Multi-layer fix proposals: agent personas, orchestration rules, hooks, quality gates, invocation templates, model assignment, retro lessons | Spec AC#7, fix layer table | Must |
| R8 | Each proposal includes evidence, layer, escalation level, risk, expected impact | Spec AC#8, report format | Must |
| R9 | User approves/rejects each proposal individually -- no auto-edits | Spec AC#9, user flow | Must |
| R10 | Approved changes routed to Colby for implementation | Spec AC#10, user flow | Must |
| R11 | Post-edit tracking: brain captures approved edits with metadata linking to proposal; telemetry measures improvement | Spec AC#11, context | Must |
| R12 | Auto-trigger at pipeline end when degradation alert fired | Spec AC#12, context | Must |
| R13 | Conservative 5-level escalation ladder: WARN -> constraint -> workflow edit -> rewrite -> removal | Spec AC#13, escalation table | Must |
| R14 | Darwin is read-only (no file modifications) -- enforced by disallowedTools + enforce-paths.sh catch-all | Spec AC#14, context | Must |
| R15 | Self-edit protection: Darwin cannot propose changes to its own persona file | Spec AC#15, edge cases | Must |
| R16 | Requires brain available + 5+ pipelines of Tier 3 telemetry data | Spec dependencies, edge cases | Must |
| R17 | Darwin is a discovered agent (not added to core constant list) | Context constraint | Must |
| R18 | Dual tree: source/ templates and .claude/ installed copies | Project convention | Must |
| R19 | Invocation templates: `darwin-analysis` (full report) and `darwin-edit-proposal` (per-change brief for Colby) | Context constraint | Must |
| R20 | Level 5 (agent replacement) requires double confirmation | Spec edge cases | Must |
| R21 | Post-edit metric regression: Darwin flags and proposes revert | Spec edge cases | Should |
| R22 | All agents thriving: "No changes proposed" report | Spec edge cases | Must |
| R23 | User rejects all proposals: record rejections with reasons in brain | Spec edge cases | Should |

**Retro risks:**

| Lesson | Risk to this feature | Mitigation |
|--------|---------------------|------------|
| #005 (Frontend Wiring Omission) | Vertical slice principle: each step must wire producer to consumer | ADR steps are vertical -- persona + command + routing in one plan |
| Behavioral constraints ignored | Darwin's read-only constraint relies on behavioral compliance | Mechanically enforced by `enforce-paths.sh` catch-all + `disallowedTools` frontmatter |
| v3.3.0 manual Darwin loop | Eva manually identified pattern and edited 4 personas -- Darwin automates this but bad edits could compound | User approval gate + post-edit tracking + revert proposals |

---

## Status

Proposed

## Context

The pipeline captures rich telemetry data (ADR-0014, shipped v3.8.0) and codifies operational lessons in `retro-lessons.md` and `error-patterns.md`, but the feedback loop from diagnosis to structural fix is open. When Colby repeatedly misses contracts tables, the system warns her (WARN injection from `error-patterns.md` with 3+ recurrences) but never changes the actual persona constraint that would prevent the failure. Today this requires manual diagnosis by the human operator: read telemetry trends, cross-reference error patterns, identify the correct system layer, edit the persona/rule file. Darwin closes this loop by proposing evidence-backed structural changes at the correct layer.

This is a pipeline infrastructure feature. All deliverables are markdown files (agent persona, command, rules, references) -- no application code. The existing `enforce-paths.sh` catch-all already blocks all discovered agents from writing, so no hook changes are needed.

Sentinel (ADR-0009) and Deps (ADR-0015) established the opt-in agent pattern: a config flag, a setup step, a persona, a command, routing updates, and invocation templates. Darwin follows this pattern. Unlike those agents, Darwin has a unique pipeline integration point: auto-trigger at pipeline end when degradation alerts fire, and a post-edit tracking loop that links approved changes to future telemetry outcomes.

### Spec Challenge

The spec assumes Darwin can reliably distinguish signal from noise in telemetry data -- that 5+ pipelines of Tier 3 metrics, combined with error-patterns.md and brain decisions, provide enough signal to propose correct structural fixes. If this is wrong -- if telemetry noise (varying feature complexity, model randomness, team workflow changes) masks the actual agent-level signal -- the design fails because Darwin's proposals would be incorrect or irrelevant, driving acceptance rates below the 50% KPI threshold.

Mitigation: The 5-pipeline minimum is a data floor, not a guarantee of signal quality. The conservative escalation ladder (WARN before constraint before edit) means early Darwin proposals are low-risk additive constraints, not destructive rewrites. The user approval gate prevents bad proposals from shipping. Post-edit tracking measures actual impact, and Darwin flags proposals that worsened metrics. The system is designed to fail safely: a Darwin run that produces zero useful proposals wastes one agent invocation, not pipeline integrity.

**SPOF:** The `agent_search` call that retrieves telemetry data for Darwin's analysis. If brain queries fail or return incomplete data, Darwin cannot compute fitness scores or identify patterns. **Failure mode:** Darwin reports "Insufficient data" and produces no proposals. The pipeline continues unchanged -- Darwin's failure is never a pipeline blocker. **Graceful degradation:** When brain is unavailable, Darwin is skipped entirely (both on-demand and auto-trigger). When brain returns partial data (<5 pipelines), Darwin reports the data gap and exits. The pipeline operates identically to pre-Darwin state.

### Anti-Goals

Anti-goal: Auto-applying changes without user approval. Reason: structural pipeline edits have compounding effects across all future pipelines. Even with post-edit tracking, the blast radius of a bad persona edit is unbounded until the next pipeline validates it. The human approval gate is the safety boundary. Revisit: when post-edit tracking demonstrates >90% acceptance rate and >80% positive metric impact over 20+ Darwin runs.

Anti-goal: Cross-project Darwin (analyzing telemetry from multiple repositories). Reason: Darwin operates on pipeline-local telemetry and pipeline-local files. Cross-repo analysis requires a telemetry aggregation layer and cross-repo file access that do not exist. Revisit: when a centralized brain instance serves multiple projects and a multi-repo Darwin scope is requested.

Anti-goal: A/B testing of persona variations. Reason: running two versions of an agent persona in parallel requires infrastructure (routing by variant, outcome tracking by variant) that is orthogonal to Darwin's analysis-and-propose model. Darwin proposes one change; A/B testing proposes two. Revisit: when Agent Teams supports heterogeneous Teammate configurations.

---

## Decision

Implement Darwin as an opt-in, read-only, on-demand + auto-triggered analysis agent following the Sentinel/Deps pattern. All changes are additive and gated behind `darwin_enabled: true` in `pipeline-config.json`. The agent is installed via `/pipeline-setup` Step 6e.

### Architecture

```
Pipeline end -> Eva prints telemetry summary -> Degradation alert fired?
  |                                                    |
  no -> done                                          yes -> darwin_enabled?
                                                       |           |
                                                      no -> done  yes -> Eva invokes Darwin
                                                                   |
User: /darwin -------------------------------------------------->  |
                                                                   v
                                              Darwin reads: brain telemetry (T1-T3),
                                              error-patterns.md, retro-lessons.md,
                                              agent personas, pipeline rules, hooks, refs
                                                                   |
                                                                   v
                                              Darwin produces: FITNESS ASSESSMENT +
                                              PROPOSED CHANGES (evidence, layer, level, risk)
                                                                   |
                                                                   v
                                              Eva presents report -> User approves/rejects each
                                                                   |
                                              Approved -> Eva routes to Colby per-proposal
                                                          Eva captures approved edit in brain
                                                          (metadata: darwin_proposal_id, target_metric)
                                                                   |
                                              Next pipelines -> telemetry tracks metric delta
                                                                -> boot summary shows edit outcomes
```

### Key Design Choices

- **Discovered agent, not core.** Darwin is not added to the core agent constant list. It is discovered at boot via the standard agent discovery scan. This is consistent with Sentinel and Deps.
- **Brain-mandatory.** Unlike other agents that degrade gracefully without brain, Darwin is brain-dependent by design. It cannot function without telemetry data stored in brain. When brain is unavailable, Darwin is simply not invoked.
- **Two invocation templates.** `darwin-analysis` is the full analysis prompt. `darwin-edit-proposal` is a per-change brief that Eva passes to Colby when routing an approved change. The second template ensures Colby gets structured context about what to change, where, why, and what the expected metric impact is.
- **Auto-trigger is advisory, not mandatory.** When a degradation alert fires at pipeline end, Eva announces it and invokes Darwin. But the user can dismiss or ignore Darwin's proposals. The auto-trigger does not block pipeline completion.
- **Post-edit tracking via brain metadata.** When Eva captures an approved Darwin edit in brain, the metadata includes `darwin_proposal_id` and `target_metric`. At boot, Eva queries for Darwin edits and checks subsequent telemetry for metric delta. This is a read-side query pattern -- no new brain schema required.

### Agent Design

Darwin is a read-only subagent (`disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit`). It receives telemetry data, error patterns, and pipeline file context via Eva's invocation prompt. It produces a structured Darwin Report with fitness assessment and proposed changes.

Workflow:
1. Read injected brain telemetry data (Tier 3 summaries from last N pipelines).
2. Read `error-patterns.md` and `retro-lessons.md` for existing codified knowledge.
3. Read agent persona files for agents flagged by telemetry.
4. Read pipeline rules, hooks, references as needed for fix layer analysis.
5. Compute per-agent fitness scores based on telemetry metrics.
6. Identify recurring patterns and map each to the correct fix layer.
7. Apply the escalation ladder to determine the appropriate intervention level.
8. Produce the Darwin Report.

### Pipeline Integration

**On-demand:** User types `/darwin`. Eva checks `darwin_enabled`, checks brain availability, checks 5+ pipeline minimum, invokes Darwin.

**Auto-trigger:** After the pipeline-end telemetry summary (existing protocol in `pipeline-orchestration.md`), if any degradation alert fired AND `darwin_enabled: true` AND `brain_available: true`, Eva announces: "Degradation detected. Running Darwin analysis..." and invokes Darwin.

**Post-edit tracking at boot:** During boot step 5b (telemetry trend query), after computing trends, Eva also queries for approved Darwin edits (`agent_search` with `thought_type: 'decision'`, metadata filter `darwin_proposal_id`). For each edit with 3+ subsequent pipelines of data, Eva computes metric delta and reports: "Darwin edit #{id} ({description}): {metric} improved/worsened {value} over {N} pipelines."

---

## Alternatives Considered

### Alternative A: Extend Eva's existing WARN injection to auto-escalate

Eva already tracks recurrence counts in `error-patterns.md` and injects WARNs at 3+ recurrences. We could extend this: at 5+ recurrences, Eva auto-proposes a constraint addition; at 8+, a workflow edit. No new agent needed.

Rejected. Eva's WARN injection is a one-dimensional escalation (same pattern, increasing urgency). It lacks: (1) cross-metric analysis (rework rate + first-pass QA + error patterns together), (2) fix layer selection (WARNs are always informational, never structural), (3) fitness scoring across agents. The analysis work is non-trivial and benefits from a dedicated context window. Eva as orchestrator should not carry the cognitive load of telemetry analysis alongside pipeline management.

### Alternative B: Darwin as a skill (main thread, conversational)

Run Darwin analysis in Eva's main thread as a conversational skill, similar to `/pm` or `/architect`. No subagent invocation overhead.

Rejected. Darwin needs to read multiple files (agent personas, rules, hooks, references) and process significant telemetry data. This is an execution task, not a conversational one. Running it in Eva's main thread would consume significant context and compete with pipeline state management. Subagent invocation gives Darwin a clean context window for analysis. The Deps agent (ADR-0015) made the same architectural choice for the same reason.

---

## Consequences

Positive:
- Closes the feedback loop from telemetry diagnosis to structural fix.
- Evidence-based proposals reduce guesswork in pipeline maintenance.
- Post-edit tracking validates that changes actually improve metrics.
- Zero impact on users who do not opt in -- all behavior gated behind config flag.
- Conservative escalation ladder prevents drastic changes on weak signal.

Negative:
- Brain-mandatory dependency means Darwin provides no value in baseline mode.
- Analysis quality depends on telemetry data quality, which depends on brain reliability.
- Auto-trigger at pipeline end adds one more step for users who have Darwin enabled.
- Compounding risk: a bad Darwin edit that passes approval degrades all future pipelines until the regression is detected (minimum 3 pipelines for detection).

Architectural decision not in spec: Darwin's auto-trigger check happens after the telemetry summary print and before the pattern staleness check. This ordering ensures Darwin has access to the just-computed degradation alerts but does not delay the staleness check.

---

## Blast Radius

| File | Change | Impact |
|------|--------|--------|
| `source/shared/agents/darwin.md` | CREATE | New agent persona template |
| `.claude/agents/darwin.md` | CREATE | Installed copy (dual tree) |
| `source/commands/darwin.md` | CREATE | New slash command template |
| `.claude/commands/darwin.md` | CREATE | Installed copy (dual tree) |
| `source/pipeline/pipeline-config.json` | MODIFY | Add `darwin_enabled: false` |
| `.claude/pipeline-config.json` | MODIFY | Add `darwin_enabled: false` |
| `skills/pipeline-setup/SKILL.md` | MODIFY | Add Step 6e opt-in block |
| `source/rules/agent-system.md` | MODIFY | Add Darwin to subagent table + no-skill-tool table + auto-routing table |
| `.claude/rules/agent-system.md` | MODIFY | Installed copy (dual tree) |
| `source/references/invocation-templates.md` | MODIFY | Add `darwin-analysis` + `darwin-edit-proposal` templates |
| `.claude/references/invocation-templates.md` | MODIFY | Installed copy (dual tree) |
| `source/rules/pipeline-orchestration.md` | MODIFY | Add Darwin auto-trigger after telemetry summary |
| `.claude/rules/pipeline-orchestration.md` | MODIFY | Installed copy (dual tree) |
| `source/rules/default-persona.md` | MODIFY | Add Darwin post-edit tracking to boot step 5b |
| `.claude/rules/default-persona.md` | MODIFY | Installed copy (dual tree) |
| `source/claude/hooks/enforce-paths.sh` | NO CHANGE | Catch-all `*` case already blocks discovered agents |
| `.claude/hooks/enforce-paths.sh` | NO CHANGE | Same |

---

## Implementation Plan

### Step 1: Agent Persona + Slash Command + Config Flag

**Files to create:**
- `source/shared/agents/darwin.md` -- template persona
- `.claude/agents/darwin.md` -- installed copy
- `source/commands/darwin.md` -- slash command template
- `.claude/commands/darwin.md` -- installed copy

**Files to modify:**
- `source/pipeline/pipeline-config.json` -- add `"darwin_enabled": false`
- `.claude/pipeline-config.json` -- add `"darwin_enabled": false`

**Agent persona content:**

YAML frontmatter:
```yaml
---
name: darwin
description: >
  Self-evolving pipeline engine. Analyzes telemetry data and error patterns
  to propose structural improvements across agent personas, orchestration
  rules, hooks, quality gates, invocation templates, model assignment, and
  retro lessons. Opt-in via pipeline-config.json. Read-only -- proposes
  changes, never modifies files.
disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit
---
```

The persona XML structure follows the established pattern:

- `<identity>`: Darwin is the Self-Evolving Pipeline Engine. Pronouns: they/them. Read-only analysis agent. Produces evidence-backed structural improvement proposals. Runs on Opus model (heavyweight analysis requiring cross-metric reasoning).
- `<required-actions>`: (1) DoR -- list data sources available, pipeline count, agents evaluated, retro risks. (2) Follow agent-preamble.md steps. (3) Review injected brain context (telemetry data from Eva's prefetch). (4) Compute per-agent fitness scores. (5) Identify patterns and map to fix layers. (6) Apply escalation ladder. (7) Produce Darwin Report. (8) DoD.
- `<workflow>`: Four phases -- Data Ingestion, Fitness Assessment, Pattern Analysis, Report Production. Data Ingestion: process injected telemetry (Tier 3 summaries), read error-patterns.md, read retro-lessons.md, read agent personas for flagged agents. Fitness Assessment: compute per-agent metrics (first-pass QA rate, rework rate, recurring patterns), classify as thriving/struggling/failing per the fitness scoring table from spec. Pattern Analysis: for each struggling/failing agent, identify the recurring failure pattern, determine the correct fix layer using the fix layer selection table from spec, apply the escalation ladder to determine intervention level. Report Production: produce the structured Darwin Report.
- `<examples>`: (a) Colby's first-pass QA dropped from 80% to 55% over 5 pipelines, 3/5 Roz findings cite missing contracts tables -- Darwin proposes adding a constraint to Colby's `<constraints>`: "Every build unit must include a Contracts Produced table in DoD." Level 2 (constraint addition), LOW risk. (b) Same agent, same pattern, constraint was added 2 pipelines ago but metric did not improve -- Darwin escalates to Level 3: propose a workflow edit adding an explicit contracts verification step.
- `<tools>`: Read, Glob, Grep, Bash (read-only diagnostics only).
- `<constraints>`: (1) Never modify files -- analysis and proposal only. (2) Cannot propose changes to own persona file (`darwin.md`) -- self-edit protection. (3) Requires 5+ pipelines of Tier 3 telemetry data; if fewer, report "Insufficient data" and exit. (4) Requires brain telemetry; if brain unavailable, report "Brain required" and exit. (5) Every proposal must include: evidence (metric values, pattern references), target layer, escalation level, risk assessment (LOW/MEDIUM/HIGH), expected metric impact. (6) Level 5 proposals (agent replacement) must include a summary of all prior escalation attempts on that agent. (7) Conservative default: when uncertain about the correct fix layer, propose the lower escalation level. (8) If a Bash command hangs or times out, STOP -- do not retry.
- `<output>`: Darwin Report format with three sections: FITNESS ASSESSMENT (per-agent: thriving/struggling/failing with metrics), PROPOSED CHANGES (numbered list, each with evidence, layer, escalation level, risk, expected impact), UNCHANGED (agents with no issues). Plus DoR/DoD sections.

**Slash command content (`source/commands/darwin.md`):**

YAML frontmatter: `name: darwin`, description one-liner.

The command file tells Eva how to handle `/darwin`:
1. Read `darwin_enabled` from `pipeline-config.json`. If `false`: "Darwin is not enabled. Run `/pipeline-setup` and enable it in Step 6e." Stop.
2. Check `brain_available`. If `false`: "Darwin requires brain telemetry data. Brain is not available." Stop.
3. Query brain for Tier 3 telemetry summaries (`agent_search` with telemetry filter, limit 10). If fewer than 5 results: "Insufficient data for Darwin analysis. Need 5+ pipelines of telemetry data. Currently have {N}." Stop.
4. Invoke Darwin subagent with the `darwin-analysis` invocation template, injecting telemetry data in `<brain-context>`.
5. Present the Darwin Report to the user.
6. For each proposed change: user approves, rejects (with reason), or modifies.
   - **Modify** = reject the current proposal with feedback + Darwin proposes a revised version. This is not a third state -- it is a reject-then-repropose cycle. Eva captures the rejection (with the user's modification feedback as the reason), then re-invokes Darwin with the feedback for a revised proposal on the same target. The revised proposal goes through the same approve/reject/modify flow.
7. For each approved change: Eva captures the approval in brain (`agent_capture` with `thought_type: 'decision'`, `source_agent: 'eva'`, metadata: `darwin_proposal_id`, `target_metric`, `target_file`, `escalation_level`, `expected_impact`). Eva routes to Colby with the `darwin-edit-proposal` invocation template.

**Config flag:** Add `"darwin_enabled": false` after `deps_agent_enabled` in both config files.

**Acceptance criteria:**
- `source/shared/agents/darwin.md` and `.claude/agents/darwin.md` exist with correct YAML frontmatter (`name: darwin`, `disallowedTools` set).
- Persona contains `<identity>`, `<required-actions>`, `<workflow>`, `<examples>`, `<tools>`, `<constraints>`, `<output>` tags.
- Self-edit protection constraint is explicitly present: "Cannot propose changes to own persona file."
- `<constraints>` includes the 5-pipeline minimum and brain-required gates.
- `source/commands/darwin.md` and `.claude/commands/darwin.md` exist with `darwin_enabled` gate.
- Both config files contain `"darwin_enabled": false` and remain valid JSON.
- No existing fields in config files are modified or removed.

**Estimated complexity:** Medium. Persona is substantive -- fitness scoring logic, escalation ladder, fix layer selection all encoded in the persona. More complex than Deps persona.

---

### Step 2: Routing + Invocation Templates

**Files to modify:**
- `source/rules/agent-system.md` + `.claude/rules/agent-system.md` -- three changes each
- `source/references/invocation-templates.md` + `.claude/references/invocation-templates.md` -- two templates each

**agent-system.md changes (three changes per file):**

Change A -- Subagent table (under `### Subagents (own context window)`): add row after Deps:
```
| **Darwin** | Self-evolving pipeline engine -- telemetry analysis, fitness evaluation, structural improvement proposals | Read, Glob, Grep, Bash (read-only) |
```

Change B -- `no-skill-tool` table (gate section): add row:
```
| Darwin (pipeline evolution) | `.claude/agents/darwin.md` |
```

Change C -- Auto-routing intent table: add row:
```
| Says "analyze the pipeline", "how are agents performing", "pipeline health", "run Darwin", "what needs improving" | **Darwin** (if `darwin_enabled: true`) or suggest enabling | subagent |
```

**Invocation templates (two templates):**

Template A -- `darwin-analysis` (full analysis):
```xml
<template id="darwin-analysis">

### Darwin (Pipeline Analysis)

Eva invokes Darwin when the user types `/darwin` or when a degradation alert
fires at pipeline end (when `darwin_enabled: true` in `pipeline-config.json`).
Requires brain and 5+ pipelines of Tier 3 telemetry data.

<task>Analyze pipeline telemetry and propose structural improvements.</task>

<brain-context>
[Eva injects Tier 3 telemetry summaries from last N pipelines via agent_search.
Also injects prior Darwin proposals and their outcomes if any exist.]
</brain-context>

<read>docs/pipeline/error-patterns.md, .claude/references/retro-lessons.md,
.claude/references/telemetry-metrics.md, .claude/references/agent-preamble.md,
[agent persona files for agents flagged by telemetry]</read>

<constraints>
- Compute per-agent fitness: thriving/struggling/failing per fitness scoring table
- For each struggling/failing agent: identify pattern, select fix layer, apply escalation ladder
- Every proposal must include: evidence, layer, escalation level, risk, expected impact
- Cannot propose changes to your own persona file (darwin.md) -- self-edit protection
- Level 5 proposals require summary of all prior escalation attempts
- Conservative: when uncertain, propose the lower escalation level
</constraints>

<output>Darwin Report with FITNESS ASSESSMENT + PROPOSED CHANGES + UNCHANGED sections. DoR/DoD.</output>

</template>
```

Template B -- `darwin-edit-proposal` (per-change brief for Colby):
```xml
<template id="darwin-edit-proposal">

### Darwin Edit Proposal (Colby Implementation)

Eva routes an approved Darwin proposal to Colby for implementation.
One proposal per Colby invocation.

<task>Implement Darwin proposal #{id}: {one-line description}</task>

<context>
Darwin proposal:
  Target file: {file_path}
  Target section: {section identifier}
  Change type: {constraint addition | workflow edit | enforcement addition | ...}
  Escalation level: {1-5}
  Evidence: {metric values, pattern references}
  Expected impact: {metric + expected delta}

Current content of target section:
[Eva pastes the current content of the section being modified]
</context>

<read>{target_file}, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<constraints>
- Make exactly the change described in the proposal -- no scope expansion
- Dual tree: if modifying source/{path}, also modify .claude/{path}
- Preserve existing content structure (XML tags, heading levels, list formatting)
- Do not modify Darwin's own persona file even if the proposal somehow references it
</constraints>

<output>Files changed, diff summary, DoR/DoD sections</output>

</template>
```

**Acceptance criteria:**
- Both `agent-system.md` files updated with Darwin in subagent table, no-skill-tool gate, and auto-routing table.
- Auto-routing row includes `darwin_enabled: true` gate condition.
- Both `invocation-templates.md` files contain `<template id="darwin-analysis">` and `<template id="darwin-edit-proposal">` blocks.
- Templates follow established XML tag format.
- Existing templates and routing entries are unchanged.

**Estimated complexity:** Low-Medium. Mostly additive content following established patterns.

---

### Step 3: Pipeline Integration (Auto-Trigger + Post-Edit Tracking)

**Files to modify:**
- `source/rules/pipeline-orchestration.md` + `.claude/rules/pipeline-orchestration.md` -- add Darwin auto-trigger after telemetry summary
- `source/rules/default-persona.md` + `.claude/rules/default-persona.md` -- add post-edit tracking to boot step 5b, add Darwin status to boot announcement

**pipeline-orchestration.md change:**

After the `Pipeline-End Telemetry Summary` section (after the fallback rules), add a new protocol section:

```markdown
### Darwin Auto-Trigger (at pipeline end)

After the pipeline-end telemetry summary, if ALL of the following conditions are true:
1. `darwin_enabled: true` in `pipeline-config.json`
2. `brain_available: true`
3. At least one degradation alert fired in the telemetry summary
4. Pipeline sizing is not Micro (Micro pipelines skip Darwin auto-trigger)

Then Eva announces: "Degradation detected. Running Darwin analysis..." and invokes
Darwin using the `darwin-analysis` invocation template.

Eva pre-fetches brain context for Darwin:
- `agent_search` with `source_phase: 'telemetry'`, `telemetry_tier: 3`, limit 10
- `agent_search` with `thought_type: 'decision'`, metadata filter for
  `darwin_proposal_id` (prior Darwin proposals and outcomes)
- Error-patterns.md content (read from disk, not brain)

After Darwin returns its report, Eva presents it to the user. The user
approves, rejects (with reason), or modifies each proposal individually.
**Modify** is a reject-then-repropose cycle: Eva captures the rejection with
the user's modification feedback, then re-invokes Darwin for a revised proposal
on the same target. This is a hard pause -- Eva does not auto-advance past
Darwin proposals.

For each approved proposal:
1. Eva captures the approval via `agent_capture`:
   - `thought_type: 'decision'`
   - `source_agent: 'eva'`
   - `source_phase: 'darwin'`
   - `importance: 0.7`
   - `content`: "Darwin edit approved: {one-line description}"
   - `metadata`: `{ darwin_proposal_id: "{pipeline_id}_{proposal_number}",
     target_file: "{path}", target_metric: "{metric_name}",
     escalation_level: {N}, expected_impact: "{description}",
     baseline_value: {current_metric_value} }`
2. Eva routes to Colby with the `darwin-edit-proposal` invocation template.
3. Roz verifies Colby's edit (mandatory gate 1 applies).
4. Ellis commits the approved edit.

For each rejected proposal:
- Eva captures the rejection via `agent_capture`:
  - `thought_type: 'decision'`
  - `source_agent: 'eva'`
  - `source_phase: 'darwin'`
  - `importance: 0.5`
  - `content`: "Darwin edit rejected: {one-line description}. Reason: {user's reason}"
  - `metadata`: `{ darwin_proposal_id: "{pipeline_id}_{proposal_number}",
    rejected: true, rejection_reason: "{reason}" }`

Darwin auto-trigger does not block pipeline completion. If the user dismisses
all proposals or says "skip Darwin", Eva proceeds to pattern staleness check.

When `darwin_enabled: false` or brain unavailable: skip this section entirely.
```

**default-persona.md change (boot step 5b extension):**

After the existing telemetry trend computation in step 5b, add:

```markdown
    **Darwin post-edit tracking** (if `darwin_enabled: true` and trend data exists):
    - Query brain: `agent_search` with `thought_type: 'decision'`,
      `source_phase: 'darwin'`, filtered to non-rejected proposals.
    - For each approved Darwin edit with `baseline_value` in metadata:
      find the target metric in subsequent Tier 3 summaries (pipelines after the edit).
      If 3+ subsequent pipelines exist:
      - Compute metric delta: current average vs baseline_value.
      - If improved: note for announcement.
      - If worsened: flag for announcement as potential regression.
    - Include in boot announcement after telemetry trend line.
```

**default-persona.md change (boot step 6 announcement):**

Add a Darwin status line to the boot announcement:
```
   - Darwin: when `darwin_enabled: true` in config, append "Darwin: active" if
     `brain_available: true`, or "Darwin: disabled (brain required)" if
     `brain_available: false`. Omit this line entirely when `darwin_enabled: false`.
   - Darwin edits: when darwin post-edit tracking found results, append on
     separate lines: "Darwin edit #{id} ({description}): {metric} {improved/worsened}
     {delta} over {N} pipelines." If any edit worsened metrics, append:
     "Warning: Darwin edit #{id} may have caused regression. Consider reverting."
```

**Acceptance criteria:**
- `pipeline-orchestration.md` contains Darwin auto-trigger section after telemetry summary.
- Auto-trigger requires all four conditions (darwin_enabled, brain_available, degradation alert, non-Micro).
- Approved proposal capture includes `darwin_proposal_id`, `target_metric`, `baseline_value` in metadata.
- Rejected proposal capture includes `rejection_reason`.
- `default-persona.md` boot step 5b includes Darwin post-edit tracking query.
- Boot announcement includes Darwin status line when `darwin_enabled: true`.
- Dual tree: both source/ and .claude/ copies updated.

**Estimated complexity:** Medium. Integrates with existing telemetry protocol, boot sequence, and brain capture patterns.

---

### Step 4: Setup Step 6e

**File to modify:**
- `skills/pipeline-setup/SKILL.md`

Add Step 6e block after Step 6d (Deps), before the Brain setup offer. Also update the summary printout.

**Content to add:**

```markdown
### Step 6e: Darwin Self-Evolving Pipeline (Opt-In)

After the Deps Agent offer (whether user said yes or no), offer the optional Darwin agent:

> Would you also like to enable **Darwin** -- the self-evolving pipeline engine?
> It analyzes your pipeline telemetry to identify underperforming agents and proposes
> structural fixes (persona edits, rule changes, enforcement additions) backed by evidence.
> Requires the Atelier Brain with 5+ pipelines of telemetry data. Optional -- the
> pipeline works fine without it.

**If user says yes:**

1. Set `darwin_enabled: true` in `.claude/pipeline-config.json`.
2. Copy `source/shared/agents/darwin.md` to `.claude/agents/darwin.md`.
3. Copy `source/commands/darwin.md` to `.claude/commands/darwin.md`.
4. Print: "Darwin: enabled. Use /darwin to analyze pipeline performance, or Darwin will auto-trigger when degradation is detected."

**Idempotency:** If `darwin_enabled` already exists in `pipeline-config.json`
and is `true`, skip mutation and inform: "Darwin is already enabled." If it
exists and is `false`, confirm before changing. If the key is absent, treat
as `false` and proceed with the offer.

**If user says no:** Skip entirely. `darwin_enabled` remains `false`.
Print: "Darwin: not enabled"

**Installation manifest addition (conditional):**

| Template Source | Destination | Install When |
|----------------|-------------|-------------|
| `source/shared/agents/darwin.md` | `.claude/agents/darwin.md` | User enables Darwin in Step 6e |
| `source/commands/darwin.md` | `.claude/commands/darwin.md` | User enables Darwin in Step 6e |
```

Also update the **summary printout** in Step 6 to add a line:
```
Darwin: [enabled | not enabled]
```

**Acceptance criteria:**
- Step 6e block exists in SKILL.md, positioned after Step 6d and before the Brain setup offer.
- The block follows the exact pattern of Step 6d (Deps): offer text, yes-path with numbered steps, idempotency check, no-path, conditional manifest table.
- The step sets the config flag AND copies both files (persona + command).
- The summary printout line is added.
- Existing steps 6a-6d and Brain offer are unchanged.

**Estimated complexity:** Low. Follows established Step 6d pattern exactly.

---

## Comprehensive Test Specification

### Step 1 Tests: Agent Persona + Command + Config

| ID | Category | Description |
|----|----------|-------------|
| T-0016-001 | Happy | `source/shared/agents/darwin.md` exists and contains YAML frontmatter with `name: darwin` |
| T-0016-002 | Happy | `.claude/agents/darwin.md` exists and content is identical to `source/shared/agents/darwin.md` |
| T-0016-003 | Happy | `disallowedTools` frontmatter includes `Write`, `Edit`, `MultiEdit`, `NotebookEdit`, `Agent` |
| T-0016-004 | Happy | Persona contains `<identity>`, `<required-actions>`, `<workflow>`, `<examples>`, `<tools>`, `<constraints>`, `<output>` tags |
| T-0016-005 | Happy | `<constraints>` includes self-edit protection: text matching "cannot propose changes to" and "darwin.md" |
| T-0016-006 | Happy | `<constraints>` includes the 5-pipeline minimum gate |
| T-0016-007 | Happy | `<constraints>` includes the brain-required gate |
| T-0016-008 | Happy | `<workflow>` encodes four phases: Data Ingestion, Fitness Assessment, Pattern Analysis, Report Production |
| T-0016-009 | Happy | `<workflow>` encodes the fitness scoring table: thriving (first-pass QA >= 80%, rework <= 1.0), struggling (50-80% or 1.0-2.0), failing (< 50% or > 2.0) |
| T-0016-010 | Happy | `<workflow>` encodes the 5-level escalation ladder with level descriptions matching the spec |
| T-0016-011 | Happy | `<workflow>` encodes the fix layer selection table (7 target layers) |
| T-0016-012 | Happy | `<examples>` contains at least two examples (constraint addition + escalation from constraint to workflow edit) |
| T-0016-013 | Happy | `<output>` specifies three report sections: FITNESS ASSESSMENT, PROPOSED CHANGES, UNCHANGED |
| T-0016-014 | Happy | `<output>` specifies each proposal includes: evidence, layer, escalation level, risk, expected impact |
| T-0016-015 | Happy | `<constraints>` includes "Level 5 proposals require summary of all prior escalation attempts" |
| T-0016-016 | Happy | `<tools>` lists Read, Glob, Grep, Bash (read-only) and no Write/Edit tools |
| T-0016-017 | Failure | Persona does NOT include Write in `<tools>` section |
| T-0016-018 | Failure | Persona does NOT include Edit in `<tools>` section |
| T-0016-019 | Security | `enforce-paths.sh` catch-all (`*` case) blocks a Write tool call from agent_type `darwin` -- exit code 2 |
| T-0016-020 | Security | `enforce-paths.sh` catch-all blocks an Edit tool call from agent_type `darwin` -- exit code 2 |
| T-0016-021 | Boundary | Eva boot-sequence discovery scan detects `darwin` as a non-core discovered agent |
| T-0016-022 | Regression | `name: darwin` does not appear in the core agent constant list in `agent-system.md` |
| T-0016-023 | Happy | `source/commands/darwin.md` exists with YAML frontmatter `name: darwin` |
| T-0016-024 | Happy | `.claude/commands/darwin.md` exists with identical content to source |
| T-0016-025 | Happy | Command file describes `darwin_enabled` gate: when false, respond "not enabled" and stop |
| T-0016-026 | Happy | Command file describes brain-required gate: when brain unavailable, respond and stop |
| T-0016-027 | Happy | Command file describes 5-pipeline minimum gate: when fewer than 5, respond with count and stop |
| T-0016-028 | Happy | Command file describes approval flow: user approves/rejects each proposal individually |
| T-0016-029 | Happy | Command file describes routing approved changes to Colby |
| T-0016-030 | Failure | Command file includes triple gate check (darwin_enabled, brain, 5 pipelines) before invocation -- no silent bypass |
| T-0016-031 | Happy | `source/pipeline/pipeline-config.json` contains `"darwin_enabled": false` |
| T-0016-032 | Happy | `.claude/pipeline-config.json` contains `"darwin_enabled": false` |
| T-0016-033 | Happy | Both config files remain valid JSON after modification |
| T-0016-034 | Regression | No existing fields in either config file are removed or renamed |
| T-0016-035 | Regression | `deps_agent_enabled`, `sentinel_enabled`, `agent_teams_enabled`, `ci_watch_enabled` fields unchanged |
| T-0016-098 | Boundary | Conflicting proposals: when Darwin produces two proposals targeting the same file and same section, each is presented individually and user can approve one, reject the other -- approvals do not merge |
| T-0016-099 | Happy | Command file describes "modify" path: modify = reject current proposal with feedback + re-invoke Darwin for a revised proposal on the same target, cycling through approve/reject/modify again |

### Step 2 Tests: Routing + Invocation Templates

| ID | Category | Description |
|----|----------|-------------|
| T-0016-036 | Happy | `source/rules/agent-system.md` subagent table contains a `Darwin` row with tools Read, Glob, Grep, Bash (read-only) |
| T-0016-037 | Happy | `.claude/rules/agent-system.md` subagent table contains matching `Darwin` row (dual tree parity) |
| T-0016-038 | Happy | Auto-routing table in both files contains a row matching pipeline-analysis intent to Darwin |
| T-0016-039 | Happy | Auto-routing Darwin row includes `darwin_enabled: true` gate condition |
| T-0016-040 | Happy | `no-skill-tool` gate in both files maps Darwin to `.claude/agents/darwin.md` |
| T-0016-041 | Failure | Auto-routing does NOT route Darwin intent when `darwin_enabled` is explicitly `false` -- Eva presents "not enabled" message |
| T-0016-100 | Failure | Auto-routing does NOT route Darwin intent when `darwin_enabled` key is entirely absent from `pipeline-config.json` -- Eva treats absence as `false` and presents "not enabled" message (no crash, no silent bypass) |
| T-0016-042 | Regression | Deps row in subagent table unchanged after Darwin addition |
| T-0016-043 | Regression | Sentinel row in subagent table unchanged after Darwin addition |
| T-0016-044 | Regression | Core agent constant list unchanged (no `darwin` entry) |
| T-0016-045 | Happy | `source/references/invocation-templates.md` contains `<template id="darwin-analysis">` block |
| T-0016-046 | Happy | `.claude/references/invocation-templates.md` contains matching `darwin-analysis` template (dual tree) |
| T-0016-047 | Happy | `darwin-analysis` template contains `<task>`, `<brain-context>`, `<read>`, `<constraints>`, `<output>` tags |
| T-0016-048 | Happy | `darwin-analysis` constraints include self-edit protection and escalation ladder rules |
| T-0016-049 | Happy | `darwin-analysis` `<read>` includes error-patterns.md, retro-lessons.md, telemetry-metrics.md |
| T-0016-050 | Happy | Both files contain `<template id="darwin-edit-proposal">` block |
| T-0016-051 | Happy | `darwin-edit-proposal` template contains `<task>`, `<context>`, `<read>`, `<constraints>`, `<output>` tags |
| T-0016-052 | Happy | `darwin-edit-proposal` constraints include dual-tree requirement and self-edit protection |
| T-0016-053 | Happy | `darwin-edit-proposal` context includes: target file, target section, change type, escalation level, evidence, expected impact |
| T-0016-054 | Regression | Existing template IDs (`deps-scan`, `sentinel-audit`, etc.) unchanged in both files |

### Step 3 Tests: Pipeline Integration (Auto-Trigger + Post-Edit Tracking)

| ID | Category | Description |
|----|----------|-------------|
| T-0016-055 | Happy | `pipeline-orchestration.md` contains Darwin auto-trigger section after the pipeline-end telemetry summary |
| T-0016-056 | Happy | Auto-trigger requires four conditions: darwin_enabled, brain_available, degradation alert, non-Micro |
| T-0016-057 | Happy | Auto-trigger describes Eva pre-fetching brain context (Tier 3 telemetry + prior Darwin proposals) |
| T-0016-058 | Happy | Approved proposal brain capture includes `darwin_proposal_id`, `target_metric`, `baseline_value`, `escalation_level` in metadata |
| T-0016-059 | Happy | Rejected proposal brain capture includes `rejected: true` and `rejection_reason` in metadata |
| T-0016-060 | Happy | Auto-trigger section states "hard pause" -- Eva does not auto-advance past Darwin proposals |
| T-0016-061 | Happy | Auto-trigger section states Darwin does not block pipeline completion (user can skip) |
| T-0016-062 | Happy | `default-persona.md` boot step 5b includes Darwin post-edit tracking query |
| T-0016-063 | Happy | Post-edit tracking queries for `thought_type: 'decision'`, `source_phase: 'darwin'` |
| T-0016-064 | Happy | Post-edit tracking computes metric delta when 3+ subsequent pipelines exist |
| T-0016-065 | Happy | Post-edit tracking reports improved edits and flags worsened edits as potential regressions |
| T-0016-066 | Happy | Boot announcement includes Darwin status line when `darwin_enabled: true` |
| T-0016-067 | Failure | When `darwin_enabled: false`, auto-trigger section is skipped entirely -- no Darwin invocation at pipeline end |
| T-0016-068 | Failure | When brain unavailable, auto-trigger is skipped -- Darwin is not invoked |
| T-0016-069 | Failure | When no degradation alert fired, auto-trigger is skipped -- Darwin is not invoked |
| T-0016-070 | Failure | When pipeline is Micro, auto-trigger is skipped |
| T-0016-071 | Boundary | When exactly 5 pipelines of telemetry data exist, Darwin proceeds (minimum met) |
| T-0016-072 | Boundary | When 4 pipelines of telemetry data exist, Darwin reports "Insufficient data" with count |
| T-0016-073 | Boundary | When 0 approved Darwin edits exist, post-edit tracking produces no output (no error) |
| T-0016-074 | Boundary | When approved edit has fewer than 3 subsequent pipelines, tracking reports "pending" (not enough data) |
| T-0016-075 | Boundary | All agents thriving: Darwin report says "No changes proposed" -- no proposals section |
| T-0016-076 | Boundary | Level 5 proposal: Darwin report includes summary of all prior escalation attempts and double confirmation requirement text |
| T-0016-077 | Boundary | Darwin proposes editing darwin.md: self-edit protection blocks the proposal -- it does not appear in report |
| T-0016-078 | Boundary | User rejects all proposals: Eva captures each rejection with reason; no Colby invocations |
| T-0016-079 | Regression | Existing telemetry summary format unchanged |
| T-0016-080 | Regression | Existing boot step 5b telemetry trend logic unchanged |
| T-0016-081 | Regression | Dual tree parity: `source/rules/pipeline-orchestration.md` and `.claude/rules/pipeline-orchestration.md` both contain Darwin auto-trigger |
| T-0016-082 | Regression | Dual tree parity: `source/rules/default-persona.md` and `.claude/rules/default-persona.md` both contain post-edit tracking |
| T-0016-101 | Contract | Eva can parse Darwin Report shape: report contains FITNESS ASSESSMENT section (per-agent status), PROPOSED CHANGES section (numbered list with evidence/layer/level/risk/impact per item), and UNCHANGED section -- validates Step 1 persona output contract consumed by Step 3 approval flow |
| T-0016-102 | Regression | Darwin auto-trigger section appears AFTER the pipeline-end telemetry summary section and BEFORE the pattern staleness check section in `pipeline-orchestration.md` -- ordering verified by section heading positions |
| T-0016-103 | Happy | One Colby invocation per approved proposal: when user approves N proposals, Eva routes exactly N separate Colby subagent invocations using the `darwin-edit-proposal` template -- no batching of multiple proposals into a single Colby call |
| T-0016-104 | Boundary | Acceptance rate self-adjustment (<30% approval rate triggers Darwin recalibration) is explicitly out of scope. Darwin does not track or act on its own acceptance rate. Deferred until post-edit tracking demonstrates a pattern of low acceptance over 10+ Darwin runs |

### Step 4 Tests: Setup Step 6e

| ID | Category | Description |
|----|----------|-------------|
| T-0016-083 | Happy | `skills/pipeline-setup/SKILL.md` contains a `### Step 6e` block |
| T-0016-084 | Happy | Step 6e is positioned after Step 6d and before the Brain setup offer |
| T-0016-085 | Happy | Step 6e offer text mentions telemetry, underperforming agents, and structural fixes |
| T-0016-086 | Happy | Step 6e offer text mentions Brain requirement |
| T-0016-087 | Happy | Step 6e yes-path sets `darwin_enabled: true` in config |
| T-0016-088 | Happy | Step 6e yes-path copies `source/shared/agents/darwin.md` to `.claude/agents/darwin.md` |
| T-0016-089 | Happy | Step 6e yes-path copies `source/commands/darwin.md` to `.claude/commands/darwin.md` |
| T-0016-090 | Happy | Step 6e no-path leaves `darwin_enabled: false` and prints "Darwin: not enabled" |
| T-0016-091 | Happy | Summary printout in Step 6 includes "Darwin: [enabled | not enabled]" line |
| T-0016-092 | Failure | First-time setup where `darwin_enabled` key is absent: Step 6e treats absence as `false`, offers opt-in, writes key on acceptance |
| T-0016-093 | Boundary | Idempotency: if `darwin_enabled: true` already set, Step 6e skips mutation and announces "already enabled" |
| T-0016-094 | Boundary | Idempotency: if `darwin_enabled: false` already set, Step 6e confirms before changing |
| T-0016-095 | Regression | Step 6d (Deps) block unchanged after Step 6e insertion |
| T-0016-096 | Regression | Brain setup offer remains positioned after Step 6e |
| T-0016-097 | Regression | Steps 6a-6c unchanged after Step 6e insertion |

### Step N Telemetry

**Step 1 (Persona + Command + Config):**
Telemetry: Eva boot-sequence log announces "Discovered 1 custom agent(s): darwin -- [description]". Trigger: every session boot when `darwin_enabled: true` and `.claude/agents/darwin.md` exists. Absence means: agent file missing or malformed frontmatter.

Telemetry: When `/darwin` is typed and `darwin_enabled: false`, Eva responds with "Darwin is not enabled." When `darwin_enabled: true` but brain unavailable, Eva responds with "Darwin requires brain telemetry data." When enabled and brain available but <5 pipelines, Eva responds with insufficient data message. Trigger: user invokes `/darwin`. Absence means: command file missing or gate logic not implemented.

Telemetry: `jq .darwin_enabled .claude/pipeline-config.json` returns `false` (default) or `true` (after Step 6e). Absence means: config key not written.

**Step 2 (Routing + Templates):**
Telemetry: Eva announces routing decision when user asks pipeline health question: "Routing to Darwin for pipeline analysis." Trigger: auto-routing intent match. Absence means: routing row missing or `darwin_enabled` gate blocks silently.

Telemetry: Eva's invocation prompt for Darwin subagent includes `darwin-analysis` template content. Trigger: every Darwin subagent invocation. Absence means: Eva not loading invocation-templates.md.

**Step 3 (Pipeline Integration):**
Telemetry: After pipeline-end telemetry summary with degradation alert, Eva announces "Degradation detected. Running Darwin analysis..." Trigger: degradation alert + darwin_enabled + brain_available + non-Micro. Absence means: auto-trigger conditions not evaluated or section missing from orchestration rules.

Telemetry: `agent_capture` with `source_phase: 'darwin'` and `darwin_proposal_id` in metadata. Trigger: each approved/rejected Darwin proposal. Absence means: brain capture not wired after approval/rejection flow.

Telemetry: Boot announcement includes "Darwin edit #{id}: {metric} improved/worsened" lines. Trigger: boot step 5b post-edit tracking finds approved edits with 3+ subsequent pipelines. Absence means: post-edit tracking query not implemented in boot sequence.

**Step 4 (Setup):**
Telemetry: After `/pipeline-setup` Step 6e acceptance, `jq .darwin_enabled .claude/pipeline-config.json` returns `true`, and both agent/command files exist. Trigger: user completes Step 6e opt-in. Absence means: Step 6e failed to write config or copy files.

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `source/shared/agents/darwin.md` (persona) | XML-structured markdown with YAML frontmatter | Eva subagent invocation + `/darwin` command dispatch | Step 1 + Step 2 |
| `source/commands/darwin.md` (command) | YAML frontmatter + behavior block | Eva reads command file on `/darwin` | Step 1 + Step 2 |
| `darwin_enabled` flag (pipeline-config.json) | boolean | Eva auto-routing gate, `/darwin` gate, auto-trigger gate, SKILL.md Step 6e | Step 1 + Step 2 + Step 3 + Step 4 |
| `darwin-analysis` template (invocation-templates.md) | XML template with task/brain-context/read/constraints/output | Eva constructs Darwin invocation prompt | Step 2 + Step 3 |
| `darwin-edit-proposal` template (invocation-templates.md) | XML template with task/context/read/constraints/output | Eva constructs Colby invocation for approved proposals | Step 2 + Step 3 |
| Darwin Report (Darwin agent output) | Structured markdown: FITNESS ASSESSMENT + PROPOSED CHANGES + UNCHANGED | Eva presents to user, processes approval/rejection | Step 1 (producer) + Step 3 (consumer) |
| `agent_capture` with `darwin_proposal_id` metadata (brain) | decision thought with structured metadata | Boot step 5b post-edit tracking query | Step 3 (producer) + Step 3 (consumer) |
| Darwin auto-trigger section (pipeline-orchestration.md) | Protocol section consumed by Eva at pipeline end | Eva pipeline-end flow | Step 3 |
| Darwin status line in boot announcement (default-persona.md) | Text appended to step 6 output | User-facing session boot | Step 3 |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `source/shared/agents/darwin.md` | Agent persona (XML/YAML) | Eva subagent invocation via `darwin-analysis` template | Step 1 -> Step 2 |
| `source/commands/darwin.md` | Command definition | Eva reads on `/darwin` -> invokes Darwin subagent | Step 1 -> Step 2 |
| `darwin_enabled` config flag | boolean in JSON | SKILL.md Step 6e (write), Eva routing (read), auto-trigger (read) | Step 1 -> Step 2, Step 3, Step 4 |
| `darwin-analysis` invocation template | XML template | Eva invokes Darwin (on-demand + auto-trigger) | Step 2 -> Step 3 |
| `darwin-edit-proposal` invocation template | XML template | Eva invokes Colby with approved proposal | Step 2 -> Step 3 |
| Darwin Report output | Structured markdown | Eva presents to user, captures in brain | Step 1 (produces) -> Step 3 (consumes) |
| `agent_capture` (darwin proposal) | Brain thought with metadata | Boot step 5b post-edit tracking | Step 3 (produces) -> Step 3 (consumes) |
| Auto-trigger protocol | Orchestration rule | Eva pipeline-end flow | Step 3 (self-contained) |
| Boot announcement Darwin line | Text output | User session start | Step 3 (self-contained) |
| SKILL.md Step 6e | Setup procedure | User runs `/pipeline-setup` | Step 4 (self-contained) |

No orphan producers. Every endpoint/template/config flag has at least one consumer in the same or prior step.

---

## Notes for Colby

1. **Dual-tree discipline is critical.** Every file in `source/` has a corresponding `.claude/` copy. The source/ copy is the template (with `{placeholders}` if applicable -- Darwin has none since it is pipeline infrastructure, not project-specific). The .claude/ copy is the installed version used by this project. Both must be created/modified in the same step.

2. **Persona complexity.** Darwin's persona is more complex than Deps or Sentinel because it encodes domain-specific analysis logic: fitness scoring thresholds, escalation ladder levels, fix layer selection heuristics. These are not arbitrary -- they come directly from the spec tables. Encode them as structured content in the `<workflow>` section, not as prose. Use tables in the workflow section to match the spec's tabular format.

3. **Self-edit protection.** The constraint "Cannot propose changes to own persona file (darwin.md)" must appear in both the `<constraints>` section of the persona AND in the `darwin-edit-proposal` Colby template. Belt and suspenders -- Darwin should not propose it, and Colby should not implement it even if it somehow appears.

4. **Brain capture metadata shape.** The `darwin_proposal_id` format is `{pipeline_id}_{proposal_number}` where pipeline_id is the existing Tier 3 pipeline_id format and proposal_number is a sequential integer (1, 2, 3...) within a Darwin run. This format enables querying all proposals from a specific pipeline and tracking individual proposal outcomes.

5. **Config flag ordering.** Add `"darwin_enabled": false` after `"deps_agent_enabled": false` in both config files. Maintain the established ordering: sentinel, agent_teams, ci_watch, deps, darwin.

6. **SKILL.md insertion point.** Step 6e goes after Step 6d (Deps) and before the "Brain setup offer (always ask)" block. The Brain offer must remain the last optional feature offered.

7. **Auto-trigger ordering in pipeline-orchestration.md.** The Darwin auto-trigger section goes after the `Pipeline-End Telemetry Summary` section and before the existing `Pattern Staleness Check` section. This ensures Darwin has access to computed degradation alerts but does not delay staleness checking.

8. **Model selection.** Darwin runs on Opus. The analysis requires cross-metric reasoning, pattern identification, and fix layer selection -- this is not a mechanical task. Encode "Runs on Opus model" in the `<identity>` section.

9. **Modify = reject + repropose.** The command file's approval flow has three user options (approve/reject/modify) but "modify" is not a third state. It is a reject with feedback followed by a Darwin re-invocation for a revised proposal. The rejection is captured in brain with the user's feedback as the reason. The revised proposal goes through the same approve/reject/modify cycle. Encode this clearly in the command file.

10. **One Colby invocation per approved proposal.** Do not batch multiple approved proposals into a single Colby call. Each proposal is a separate `darwin-edit-proposal` invocation. This keeps edits atomic and independently verifiable by Roz.

11. **Post-edit tracking is read-side only.** No new brain schema. Eva queries existing `agent_capture` entries with `source_phase: 'darwin'` metadata. The query pattern is: filter by `thought_type: 'decision'` + `source_phase: 'darwin'` + `rejected: false` (or absent). Cross-reference `darwin_proposal_id` with `target_metric` and find subsequent Tier 3 summaries for metric comparison.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Agent persona exists (dual tree) | Covered | Step 1: T-0016-001, T-0016-002, T-0016-004 |
| R2 | Config flag defaults false | Covered | Step 1: T-0016-031, T-0016-032 |
| R3 | Setup Step 6e opt-in | Covered | Step 4: T-0016-083 through T-0016-097 |
| R4 | /darwin command with triple gate | Covered | Step 1: T-0016-023 through T-0016-030 |
| R5 | Reads brain telemetry | Covered | Step 2: T-0016-049; Step 3: T-0016-057 |
| R6 | Fitness assessment | Covered | Step 1: T-0016-009 |
| R7 | Multi-layer fix proposals | Covered | Step 1: T-0016-011 |
| R8 | Evidence + risk in proposals | Covered | Step 1: T-0016-014 |
| R9 | Individual approval flow | Covered | Step 1: T-0016-028; Step 3: T-0016-060 |
| R10 | Approved changes routed to Colby | Covered | Step 1: T-0016-029; Step 2: T-0016-050 through T-0016-053 |
| R11 | Post-edit tracking | Covered | Step 3: T-0016-062 through T-0016-065 |
| R12 | Auto-trigger on degradation | Covered | Step 3: T-0016-055 through T-0016-061, T-0016-067 through T-0016-070 |
| R13 | 5-level escalation ladder | Covered | Step 1: T-0016-010 |
| R14 | Read-only enforcement | Covered | Step 1: T-0016-017 through T-0016-020 |
| R15 | Self-edit protection | Covered | Step 1: T-0016-005; Step 3: T-0016-077 |
| R16 | 5+ pipeline minimum | Covered | Step 1: T-0016-006, T-0016-027; Step 3: T-0016-071, T-0016-072 |
| R17 | Discovered agent (not core) | Covered | Step 1: T-0016-021, T-0016-022; Step 2: T-0016-044 |
| R18 | Dual tree sync | Covered | Step 1: T-0016-002, T-0016-024; Step 2: T-0016-037, T-0016-046; Step 3: T-0016-081, T-0016-082 |
| R19 | Two invocation templates | Covered | Step 2: T-0016-045 through T-0016-054 |
| R20 | Level 5 double confirmation | Covered | Step 3: T-0016-076 |
| R21 | Post-edit regression flagging | Covered | Step 3: T-0016-065 |
| R22 | All-thriving report | Covered | Step 3: T-0016-075 |
| R23 | Rejection recording | Covered | Step 3: T-0016-059, T-0016-078 |
| R9a | Modify path in approval flow | Covered | Step 1: T-0016-099 (modify = reject + repropose cycle) |
| R2a | Absent config key handling | Covered | Step 2: T-0016-100 (absence treated as false) |
| R8a | Conflicting proposals edge case | Covered | Step 1: T-0016-098 (presented individually, no merge) |
| R1a | Darwin Report contract (Step 1 -> Step 3 wiring) | Covered | Step 3: T-0016-101 |
| R12a | Auto-trigger ordering guarantee | Covered | Step 3: T-0016-102 |
| R10a | One Colby invocation per proposal (atomicity) | Covered | Step 3: T-0016-103 |
| -- | Acceptance rate self-adjustment | Deferred | T-0016-104: out of scope until 10+ Darwin runs show low acceptance pattern |

**Architectural decisions not in spec:**
- Darwin auto-trigger ordering: placed after telemetry summary, before pattern staleness check. Rationale: Darwin needs computed degradation alerts; staleness check is independent.
- `darwin_proposal_id` format: `{pipeline_id}_{proposal_number}`. Rationale: enables per-pipeline grouping and individual proposal tracking.
- Colby receives one proposal per invocation via `darwin-edit-proposal` template. Rationale: keeps each edit atomic and independently verifiable by Roz.
- Darwin runs on Opus. Rationale: cross-metric reasoning and fix layer selection is heavyweight analysis, not mechanical.
- "Modify" in the approval flow is not a third state: it is a reject-then-repropose cycle. Rationale: avoids a third approval state with ambiguous semantics. The user's modification feedback is captured as the rejection reason, then Darwin re-proposes.
- Acceptance rate self-adjustment (<30% threshold) is explicitly deferred. Darwin does not track or act on its own acceptance rate in this iteration. Revisit after 10+ Darwin runs demonstrate a pattern.
- Absent `darwin_enabled` key is treated as `false` in all gates (auto-routing, command, auto-trigger). No crash or silent bypass on missing key.

**Rejected alternative:** Extending Eva's WARN injection to auto-escalate. Rationale: WARN injection is one-dimensional (same pattern, increasing urgency). Darwin provides multi-dimensional analysis (cross-metric, cross-agent, fix-layer-aware).

**Technical constraints discovered:**
- Brain is mandatory for Darwin (unlike all other agents that degrade gracefully). This is intentional -- Darwin without telemetry data is meaningless.
- The 5-pipeline minimum is a hard gate in the command, persona, and auto-trigger. There is no "partial analysis" mode for fewer pipelines.
- `enforce-paths.sh` catch-all already handles Darwin -- no hook changes needed. Verified by reading the existing catch-all pattern.
