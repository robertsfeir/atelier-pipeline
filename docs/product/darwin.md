## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Multi-layer fix targets: agent personas, orchestration rules, hooks, quality gates, invocation templates, model assignment, retro lessons | Issue #7 expanded scope |
| 2 | Agent fitness evaluation: thriving/struggling/failing based on telemetry metrics | Issue #7 fitness section |
| 3 | Darwin Report format with fitness assessment + proposed changes + risk levels | Issue #7 report format |
| 4 | User approves every change individually — no auto-edits | Issue #7 constraints |
| 5 | Read-only agent — Darwin analyzes, Colby implements approved changes | Issue #7 constraints |
| 6 | Opt-in via pipeline-config.json flag (darwin_enabled), Setup Step 6e | Issue #7 implementation |
| 7 | /darwin command for on-demand invocation | Issue #7 implementation |
| 8 | Auto-trigger at pipeline end when telemetry shows degradation | Issue #7 implementation |
| 9 | Conservative escalation: WARN → constraint → workflow edit → persona rewrite → agent removal | Issue #7 constraints |
| 10 | Post-edit tracking: telemetry measures whether approved edits improved metrics | Issue #7 constraints |
| 11 | Needs 5+ pipelines of telemetry data to be useful | Issue #7 dependencies |
| 12 | Telemetry dashboard (#18) provides fitness metrics | Dependency (shipped v3.8.0) |

**Retro risks:** The v3.3.0 wiring enforcement fix was a manual Darwin loop — Eva identified pattern, edited 4 agent personas. Darwin automates this but adds risk of bad edits compounding across pipelines.

---

# Feature Spec: Darwin — Self-Evolving Pipeline Engine

**Author:** Robert (CPO) | **Date:** 2026-03-29
**Status:** Draft
**Issue:** #7

## The Problem

Pipeline failures recur because the system doesn't learn structurally. Retro lessons and WARN injection are informational — they tell agents "watch out" but don't change actual behavior. When Colby keeps missing contracts tables, the fix isn't a warning — it's adding a required field to Colby's output section. Today this requires manual diagnosis across telemetry data, error patterns, and brain lessons, followed by manual persona/rule edits. The feedback loop is open.

## Who Is This For

Pipeline operators who want the system to improve itself over time. Darwin turns operational data (telemetry, error patterns, QA findings) into structural improvements (persona edits, rule changes, enforcement additions) — closing the feedback loop that today requires manual intervention.

## Business Value

- **Self-improving pipeline** — recurring failures get fixed at the source, not papered over with warnings
- **Reduced manual maintenance** — persona and rule edits proposed automatically
- **Data-driven evolution** — changes backed by telemetry evidence, not gut feel
- **Agent accountability** — fitness evaluation surfaces underperforming agents before quality degrades

**KPIs:**
| KPI | Measurement | Timeframe | Acceptance |
|-----|------------|-----------|------------|
| Proposed changes accepted rate | Approved / total proposed | Per Darwin run | > 50% (proposals are useful) |
| Post-edit metric improvement | Metric delta after approved edit | Next 3 pipelines | > 0 improvement in target metric |
| Recurring pattern reduction | Patterns with 3+ recurrences before vs after Darwin | Per quarter | Decreasing trend |
| Time to structural fix | Pipelines from pattern detection to approved fix | Per pattern | < 3 pipelines |

## User Stories

1. **As a pipeline operator**, I want Darwin to analyze my last N pipelines and tell me which agents are thriving, struggling, or failing so I can prioritize improvements.
2. **As a pipeline operator**, when Darwin identifies a recurring failure, I want it to propose the specific fix at the correct system layer (persona, rules, hooks, etc.) so I don't have to diagnose it myself.
3. **As a pipeline operator**, I want to approve or reject each proposed change individually so I stay in control of pipeline evolution.
4. **As a pipeline operator**, after approving a Darwin edit, I want telemetry to track whether it actually improved the metric so I know if the fix worked.

## User Flow

### On-Demand Darwin Run
```
User: /darwin
Eva: Routing to Darwin for pipeline analysis.

Darwin analyzes last 10 pipelines → produces report:

Darwin Report (last 10 pipelines)
==================================

FITNESS ASSESSMENT:
  Thriving: Roz (98% first-pass), Ellis (100%), Cal (92%)
  Struggling: Colby (first-pass QA dropped 80% → 55%)
  Failing: [none]

PROPOSED CHANGES:
  1. [Agent] Colby <constraints>: add "Every build unit must include a
     Contracts Produced table in DoD"
     Evidence: 3/5 recent Roz findings cite missing wiring (T-0013-064 pattern)
     Layer: agent persona
     Escalation: constraint addition (level 2 of 5)
     Risk: LOW (additive, non-breaking)
     Expected impact: first-pass QA +15-20%

  2. [Hook] enforce-paths.sh: add explicit Colby block for docs/ directory
     Evidence: 2 incidents of Colby writing to spec files during build phase
     Layer: mechanical enforcement
     Escalation: enforcement addition (level 3 of 5)
     Risk: LOW (restrictive, prevents known bad behavior)
     Expected impact: eliminate spec modification during build

UNCHANGED: Roz, Cal, Ellis, Robert, Sable, Poirot, Agatha, Sentinel, Deps

Eva: Review each proposal individually. Approve, reject, or modify?
User: Approve #1, reject #2 (I want Colby to update specs sometimes)
Eva: Routes #1 to Colby for implementation. #2 noted as rejected with reason.
```

### Auto-Triggered Darwin (at pipeline end)
```
Pipeline complete. Telemetry summary: [...]
  ⚠ Rework rate above 2.0 for 3 consecutive pipelines.

Eva: Degradation detected. Running Darwin analysis...
Darwin: [abbreviated report focusing on degradation cause]

PROPOSED FIX:
  1. [Agent] Colby <workflow>: add step "Run lint before submitting"
     Evidence: 4/6 rework cycles were lint failures caught by Roz
     ...

Eva: Approve this fix? (yes/no/modify)
```

### Post-Edit Tracking
```
[3 pipelines later, at boot]
Telemetry: Last 5 pipelines — avg $3.80, 38 min. Rework: 1.1/unit. First-pass QA: 78%.
  ✓ Darwin edit #47 (Colby contracts table): first-pass QA improved 55% → 78% over 3 pipelines.
```

## Darwin's Analysis Model

### Data Sources
| Source | What Darwin reads | Why |
|--------|------------------|-----|
| Brain telemetry (Tier 1-3) | Per-invocation/unit/pipeline metrics | Fitness scoring, trend detection |
| error-patterns.md | Recurring categorized failures | Pattern identification |
| retro-lessons.md | Codified lessons from past runs | Existing knowledge |
| Brain decisions/lessons | Historical decisions and outcomes | Context for proposals |
| Agent personas (.claude/agents/) | Current agent behavior | Understanding what to change |
| Pipeline rules (.claude/rules/) | Current orchestration | Understanding where to change |
| Hooks (.claude/hooks/) | Current enforcement | Identifying enforcement gaps |
| References (.claude/references/) | Current quality framework | Identifying coverage gaps |

### Fitness Scoring
| Category | Criteria | Metrics Used |
|----------|----------|-------------|
| **Thriving** | First-pass QA ≥ 80%, rework ≤ 1.0, no recurring patterns | first_pass_qa_rate, rework_rate, error_patterns count |
| **Struggling** | First-pass QA 50-80% OR rework 1.0-2.0 OR 2+ recurring patterns | Same + trend direction |
| **Failing** | First-pass QA < 50% OR rework > 2.0 OR no improvement after 2 Darwin edits | Same + edit history |

### Escalation Ladder (conservative by default)
| Level | Action | When |
|-------|--------|------|
| 1 | WARN injection (existing) | First occurrence of a pattern |
| 2 | Constraint addition | Pattern recurs 3+ times despite WARN |
| 3 | Workflow/enforcement edit | Constraint didn't help after 2 pipelines |
| 4 | Persona rewrite (section) | Structural issue in agent's approach |
| 5 | Agent replacement/removal | Persistent failure despite all edits |

Level 5 requires explicit user confirmation with a summary of all prior escalation attempts.

### Fix Layer Selection
Darwin determines the correct layer by analyzing the failure pattern:

| Pattern Signal | Fix Layer | Example |
|---------------|-----------|---------|
| Agent output consistently missing X | Agent persona (constraints/output) | Missing contracts table → add to Colby output |
| Same issue caught by multiple reviewers | Quality gate (qa-checks.md) | Wiring gaps → add wiring check to Roz Tier 1 |
| Agent does something hooks should prevent | Hook enforcement | Colby writes to docs/ → add enforce-paths case |
| Eva routes incorrectly or misses context | Invocation templates | Missing brain context → update template |
| Wrong model causes rework | Model assignment | Sonnet rework > 2x Opus → bump classifier score |
| Repeated across multiple agents | Pipeline orchestration rules | Sequencing gap → add mandatory gate |
| Knowledge not persisting | Retro lessons | Codify new lesson from pattern |

## Edge Cases and Error Handling

| Edge Case | Handling |
|-----------|----------|
| Fewer than 5 pipelines of telemetry data | "Insufficient data for Darwin analysis. Need 5+ pipelines." Skip. |
| Brain unavailable | "Darwin requires brain telemetry data. Running in baseline mode." Skip. |
| All agents thriving | "All agents performing well. No changes proposed." |
| User rejects all proposals | Record rejections with reasons in brain. Darwin adjusts future proposals based on rejection patterns. |
| Proposed edit would conflict with another proposal | Present both, note the conflict, let user choose. |
| Level 5 (agent replacement) proposed | Require double confirmation: "This proposes replacing [agent]. Are you sure? This will rewrite the persona from scratch." |
| Darwin proposes editing Darwin | Block. Darwin cannot modify its own persona. User must edit Darwin manually. |
| Post-edit metric worsened | Darwin flags: "Edit #N may have caused regression. Revert?" |

## Acceptance Criteria

| # | Criterion | Measurable |
|---|-----------|------------|
| 1 | Darwin agent persona exists | File inspection |
| 2 | darwin_enabled flag in pipeline-config.json, default false | Config inspection |
| 3 | Setup Step 6e offers Darwin opt-in | Setup flow observation |
| 4 | /darwin command invokes analysis | Command observation |
| 5 | Darwin reads telemetry data from brain | Brain query observation |
| 6 | Darwin produces fitness assessment (thriving/struggling/failing) | Report output |
| 7 | Darwin proposes fixes at the correct system layer | Report output |
| 8 | Each proposal includes evidence, layer, escalation level, risk, expected impact | Report output |
| 9 | User approves/rejects each proposal individually | Interaction observation |
| 10 | Approved changes routed to Colby for implementation | Agent routing observation |
| 11 | Post-edit tracking: telemetry measures improvement | Boot summary observation |
| 12 | Auto-trigger at pipeline end when degradation detected | Pipeline completion observation |
| 13 | Conservative escalation: follows 5-level ladder | Escalation level in proposals |
| 14 | Darwin is read-only (no file modifications) | Hook enforcement |
| 15 | Darwin cannot modify its own persona | Constraint enforcement |

## Scope

### In Scope
- Darwin agent persona (read-only, analysis + proposals)
- /darwin command for on-demand invocation
- Auto-trigger at pipeline end on degradation
- Fitness evaluation from telemetry data
- Multi-layer fix proposals (7 target layers)
- 5-level escalation ladder
- Post-edit tracking via telemetry
- Setup Step 6e opt-in
- Brain integration (reads telemetry, captures proposals and outcomes)

### Out of Scope
- Auto-applying changes without user approval
- Darwin editing its own persona
- Cross-project Darwin (analyzing multiple repos)
- Training/fine-tuning models based on Darwin data
- A/B testing of persona variations

## Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Analysis time | < 30s for 10 pipelines of telemetry data |
| Report readability | Structured, scannable, with evidence links |
| No file modifications | Darwin is read-only (Colby implements) |
| Brain query efficiency | Single agent_search with filter, not N+1 queries |

## Dependencies

| Dependency | Status | Risk |
|------------|--------|------|
| Agent Telemetry Dashboard (#18) | Shipped v3.8.0 | None |
| Brain with 5+ pipelines of data | Runtime | Low — Darwin skips gracefully |
| error-patterns.md | Exists | None |
| retro-lessons.md | Exists | None |

## Risks and Open Questions

| Risk | Mitigation |
|------|------------|
| Bad persona edit degrades agent across all future pipelines | User approval gate + post-edit tracking. Darwin flags regressions and proposes revert. |
| Darwin proposals become noise (low acceptance rate) | Track acceptance rate. If < 30% over 5 runs, Darwin self-adjusts proposal threshold. |
| Escalation to level 5 (agent removal) is drastic | Double confirmation + summary of all prior attempts. Level 5 is rare. |
| Darwin cannot self-improve (no self-editing) | Intentional constraint. Darwin persona is maintained by the human operator. |
| Insufficient telemetry data for new pipelines | Hard minimum: 5 pipelines. Darwin is transparent about data requirements. |

## Timeline Estimate

Single slice — Small/Medium sizing. Agent persona + command + setup + auto-trigger + routing.

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Agent persona | Pending | |
| 2 | Config flag | Pending | |
| 3 | Setup Step 6e | Pending | |
| 4 | /darwin command | Pending | |
| 5 | Telemetry data reading | Pending | |
| 6 | Fitness assessment | Pending | |
| 7 | Multi-layer fix proposals | Pending | |
| 8 | Evidence + risk in proposals | Pending | |
| 9 | Individual approval flow | Pending | |
| 10 | Colby routing for approved changes | Pending | |
| 11 | Post-edit tracking | Pending | |
| 12 | Auto-trigger on degradation | Pending | |
| 13 | Conservative escalation | Pending | |
| 14 | Read-only enforcement | Pending | |
| 15 | Self-edit protection | Pending | |
| 16 | Docs updated | Pending | |
