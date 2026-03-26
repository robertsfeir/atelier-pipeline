---
name: pipeline-overview
description: Use when users ask about the atelier-pipeline system, how it works, what agents do, or how to use the multi-agent orchestration pipeline. Covers agent roster, pipeline flow, quality gates, and key principles.
---

# Atelier Pipeline -- Overview

Atelier Pipeline is a multi-agent orchestration system for Claude Code. Eight specialized agents with clear boundaries, quality gates, and a central orchestrator turn AI-assisted development into a structured engineering workflow.

<section id="system-overview">

## Agent Roster

| Agent | Role | Type | When Active |
|-------|------|------|-------------|
| **Eva** | Pipeline Orchestrator and DevOps | Skill (main thread) | Always -- routes work, tracks state, enforces gates |
| **Robert** | Chief Product Officer | Skill | Feature discovery through spec writing |
| **Sable** | Senior UI/UX Designer | Skill | Spec through UX design document |
| **Cal** | Senior Software Architect | Skill / Subagent | Design through ADR (Architecture Decision Record) production |
| **Colby** | Senior Software Engineer (she/her) | Subagent | Mockup and build phases |
| **Roz** | QA Engineer (she/her) | Subagent | Test authoring, code review, verification |
| **Agatha** | Documentation Specialist | Skill / Subagent | Doc planning and writing (parallel with build) |
| **Ellis** | Commit and Changelog Manager | Subagent | Post-QA through git commit |

**Skills** run in the main Claude Code thread for conversational work.
**Subagents** run in isolated context windows for focused execution.

## Pipeline Flow

```
Idea -> Robert (spec) -> Sable (UX) + Agatha (doc plan)  [parallel]
  -> Colby (mockup) -> User UAT -> Cal (architecture + test spec)
  -> Roz (test spec review) -> Roz (test authoring)
  -> Colby (build) <-> Roz (QA)  [interleaved per ADR step]
  -> Agatha (docs) -> Ellis (commit)
```

Not every feature runs the full pipeline. Eva sizes the work and adjusts:

| Size | Criteria | Phases |
|------|----------|--------|
| **Small** | Bug fix, single file, fewer than 3 files | Colby -> Roz -> Ellis |
| **Medium** | 2-4 ADR steps, typical feature | Cal -> Colby <-> Roz -> Agatha -> Ellis |
| **Large** | 5+ ADR steps, new system | Full pipeline |

## Slash Commands

Use these to invoke agents directly:

| Command | Agent | Purpose |
|---------|-------|---------|
| `/pm` | Robert | Feature discovery and product spec |
| `/ux` | Sable | UI/UX design |
| `/architect` | Cal | Architecture clarification and ADR production |
| `/debug` | Roz -> Colby -> Roz | Bug investigation, fix, verification |
| `/pipeline` | Eva | Full pipeline orchestration |
| `/devops` | Eva | Infrastructure and deployment |
| `/docs` | Agatha | Documentation planning and writing |

You do not need slash commands for normal use. Eva auto-routes based on intent:

- "What if we added..." routes to Robert (product)
- "Build this feature" routes to Colby (implementation)
- "This is broken" routes to Roz (investigation) then Colby (fix) then Roz (verification)
- "Ship it" routes to Ellis (commit)
- Simple questions are handled directly by Eva without routing

</section>

<section id="key-principles">

## Key Principles

### Roz-First TDD

Roz writes test assertions before Colby writes implementation code. Tests define correct domain behavior. Colby makes them pass without modifying Roz's assertions. If a test fails against existing code, the code has a bug -- not the test. This eliminates the conflict of interest where the same agent writes code and defines what "correct" means.

### Continuous QA

Each ADR step is a work unit: Roz authors tests, Colby implements, Roz reviews. Issues are caught and fixed at the unit level, not accumulated into a batch review at the end.

### Definition of Ready / Definition of Done (DoR/DoD)

Every agent output starts with DoR (requirements extracted from upstream artifacts) and ends with DoD (coverage verification). Eva spot-checks at phase transitions. Roz independently verifies Colby's claims against actual code.

### Four-Layer Investigation Discipline

Debug flows check: Application -> Transport -> Infrastructure -> Environment. Two rejected hypotheses at one layer forces escalation to the next. Prevents tunnel vision.

### Retro Lessons

Error patterns are logged after each run. Patterns recurring 3+ times get injected as warnings into future agent prompts. The system learns from its mistakes.

### Mandatory Gates (Never Skippable)

1. **Roz verifies every Colby output.** No self-review.
2. **Ellis commits.** Eva never runs git commands on code.
3. **Full test suite between work units.** On the integrated codebase, not self-reported results.
4. **User approves bug fix approach.** Roz diagnoses, user reviews, then Colby fixes.

</section>

<section id="getting-started">

## Starting a Pipeline

To run a full pipeline from an idea:

```
I have a feature idea: [describe it]
```

Eva will size it and route to the appropriate starting agent.

To start from an existing spec:

```
Here is the spec: docs/product/my-feature.md -- let's build it
```

Eva detects existing artifacts and skips completed phases.

To run a quick fix:

```
This function in src/features/foo/bar.ts has a bug: [describe symptom]
```

Eva routes to Roz for investigation, presents the diagnosis, and routes to Colby after your approval.

</section>

<section id="state-recovery">

## State Recovery

Pipeline state is persisted to `docs/pipeline/pipeline-state.md`. If Claude Code is closed mid-pipeline, Eva reads this file at session start and resumes from the last completed phase. No work is lost.

Additional state files:

- `docs/pipeline/context-brief.md` -- decisions, corrections, preferences from conversation
- `docs/pipeline/error-patterns.md` -- error pattern tracking for retro lessons
- `docs/pipeline/investigation-ledger.md` -- hypothesis tracking during debug flows
- `docs/pipeline/last-qa-report.md` -- Roz's most recent QA report

</section>

<section id="advanced-concepts">

## Cognitive Independence

Eva's diagnostic conclusions are evidence-based. User disagreement without new evidence does not change a diagnosis. Agents challenge specs rather than rubber-stamping them. When findings contradict the user's theory, Eva presents the evidence and asks for the user's reasoning.

## Worktree Integration

Agents can work in isolated git worktrees. Changes merge via `git merge` (never file copying). Conflicts surface explicitly and get resolved before advancing. One worktree merges at a time, with the full test suite running between each merge.

</section>
