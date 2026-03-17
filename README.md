# Atelier Pipeline

A multi-agent orchestration system for Claude Code that replaces chaotic AI-assisted development with a structured, quality-gated engineering workflow.

## What is this?

Atelier Pipeline gives Claude Code eight specialized agent personas — a product officer, UX designer, architect, engineer, QA engineer, documentation specialist, commit manager, and a central orchestrator — each with clear responsibilities, strict boundaries, and independent quality verification. The result is AI-assisted development that actually works like a real engineering team: specs get written, designs get validated, tests get authored before code, every change passes independent QA, and nothing ships without review.

## Why?

Unstructured AI-assisted development has predictable failure modes:

- **Self-review is no review.** When the same agent writes code and writes its own tests, it controls what "correct" means. Bugs get codified as "behavioral quirks" rather than caught. In our early runs, an agent found 6 bugs in shared utilities and adjusted test expectations to match them rather than fixing them.

- **Context evaporates between sessions.** Claude Code has no memory across conversations. Without explicit state management, a 3-day feature build loses all architectural decisions, user corrections, and rejected alternatives every time you close a terminal.

- **No quality gates means no quality.** Without structural enforcement, the fastest path is always "generate code, hope it works, commit." There is no mechanism to catch spec gaps, security oversights, or silent requirement drops — until production.

- **Flat prompting hits a ceiling.** A single "build this feature" prompt cannot hold product requirements, architectural constraints, UX specifications, test coverage targets, and code quality standards simultaneously. The context window overflows, priorities blur, and output quality degrades with complexity.

Atelier Pipeline solves these by separating concerns across specialized agents, enforcing independent verification at every phase transition, and maintaining recoverable state on disk.

## The Pipeline

```
                         Idea
                          |
                     Robert (spec)
                       /      \
                      /        \
              Sable (UX)    Agatha (doc plan)         --- parallel
                      \        /
                       \      /
                    Colby (mockup)
                          |
                     User UAT review
                          |
                Cal (architecture + test spec)
                          |
                  Roz (test spec review)
                          |
                  Roz (test authoring)
                       /      \
                      /        \
      Colby (build) <-> Roz (QA)    Agatha (docs)    --- parallel + interleaved
                      \        /
                       \      /
                Ellis (commit + changelog)
```

The build/QA cycle is not one pass — it interleaves per ADR step:

```
  Roz writes tests (step 1)  -->  Colby builds (step 1)  -->  Roz reviews (step 1)
  Roz writes tests (step 2)  -->  Colby builds (step 2)  -->  Roz reviews (step 2)
  ...repeat for each ADR step...
  Roz final sweep (full integration review)
```

**Phase sizing keeps it pragmatic.** Small fixes (bug fix, single file) skip straight to Colby -> Roz -> Ellis. Medium features add architecture. Only large, multi-concern features run the full pipeline. Smart ceremony, not bureaucratic ceremony.

## Agent Roster

| Agent | Role | When | Type | Pronouns |
|-------|------|------|------|----------|
| **Eva** | Pipeline Orchestrator / DevOps | Always active — routes, tracks state, enforces gates | Skill (main thread) | -- |
| **Robert** | Chief Product Officer | Feature discovery through spec | Skill | -- |
| **Sable** | Senior UI/UX Designer | Spec through UX design document | Skill | -- |
| **Cal** | Senior Software Architect | Design through ADR production | Skill / Subagent | -- |
| **Colby** | Senior Software Engineer | Mockup and build phases | Subagent | she/her |
| **Roz** | QA Engineer | Test authoring, code review, verification | Subagent | she/her |
| **Agatha** | Documentation Specialist | Doc planning and writing (parallel with build) | Skill / Subagent | -- |
| **Ellis** | Commit and Changelog Manager | Post-QA through git commit | Subagent | -- |

**Skills** run in the main Claude Code thread for conversational, back-and-forth work.
**Subagents** run in their own context windows for focused execution tasks.

## Key Principles

### Roz-First TDD

Roz writes test assertions before Colby writes any implementation code. Tests define what correct domain behavior looks like. Colby's job is to make those tests pass — she is forbidden from modifying Roz's assertions. If a test fails against existing code, the code has a bug, not the test. This eliminates the structural conflict of interest where an agent controls both the implementation and the definition of "correct."

### Continuous QA, Not Batch QA

Each ADR step is a work unit. For every unit: Roz authors tests, Colby implements, Roz reviews. Issues are caught at the unit level and fixed immediately — not accumulated into a massive end-of-feature review where problems compound and root causes are buried.

### Definition of Ready / Definition of Done

Every agent output starts with a DoR section (requirements extracted from upstream artifacts, proving the agent actually read the spec) and ends with a DoD section (coverage verification mapping every requirement to evidence). Eva spot-checks the DoR at phase transitions. Roz independently verifies Colby's DoD against the actual code. No hand-waving, no silent requirement drops.

### Four-Layer Investigation Discipline

Debug flows systematically check four layers: Application, Transport, Infrastructure, Environment. If two hypotheses are rejected at the same layer, the investigation must escalate to the next layer before proposing more theories at the original level. This prevents tunnel vision — the most common failure mode in AI-assisted debugging.

### Retro Lessons

After each pipeline run, error patterns are categorized and logged. Patterns that recur three or more times get injected as explicit warnings into future agent prompts. The system learns from its own mistakes. Categories include: hallucinated-api, wrong-logic, pattern-drift, security-blindspot, over-engineering, stale-context, missing-state, and test-gap.

### Mandatory Gates

Four gates that are never skippable, regardless of phase sizing:

1. **Roz verifies every Colby output.** No agent self-reviews.
2. **Ellis commits. Eva never runs git.** Separation of orchestration and execution.
3. **Full test suite between work units.** On the actual integrated codebase, not self-reported results.
4. **User approves bug fix approach.** Roz diagnoses, the user reviews, then Colby fixes. No auto-advance on user-reported bugs.

## Quick Start

### Option A: Clone and set up (recommended)

```bash
git clone https://github.com/robertsfeir/atelier-pipeline.git /tmp/atelier-pipeline
```

Then open Claude Code in your project and say:

```
Read /tmp/atelier-pipeline/skills/pipeline-setup/SKILL.md and follow its
instructions to install the pipeline in this project
```

Claude will walk you through project configuration (tech stack, test commands, source structure) and install all 24 files.

### Option B: EPAM CoE Marketplace

If you have access to the EPAM Claude Code CoE:

```bash
/plugin marketplace add https://git.epam.com/epm-cipr1/claude-code-coe.git
```

Then ask Claude to set up atelier-pipeline in your project.

## What Gets Installed

```
your-project/
  .claude/
    rules/
      default-persona.md          # Eva persona (always loaded by Claude Code)
      agent-system.md             # Full orchestration rules, routing, gates
    agents/
      cal.md                      # Architect subagent persona
      colby.md                    # Engineer subagent persona
      roz.md                      # QA subagent persona
      ellis.md                    # Commit manager subagent persona
      documentation-expert.md     # Documentation subagent persona
    commands/
      pm.md                       # /pm command (Robert)
      ux.md                       # /ux command (Sable)
      architect.md                # /architect command (Cal)
      debug.md                    # /debug command (Roz -> Colby -> Roz)
      pipeline.md                 # /pipeline command (Eva)
      devops.md                   # /devops command (Eva)
      docs.md                     # /docs command (Agatha)
    references/
      dor-dod.md                  # Quality framework
      retro-lessons.md            # Shared lessons (starts with template)
      invocation-templates.md     # Subagent invocation examples
      cloud-architecture.md       # Cloud/IaC reference patterns
  docs/
    pipeline/
      pipeline-state.md           # Session recovery state
      context-brief.md            # Cross-session context preservation
      error-patterns.md           # Error pattern tracking
      investigation-ledger.md     # Debug hypothesis tracking
      last-qa-report.md           # Roz's most recent QA report
```

## Customization

During setup, you configure project-specific values that get wired into the agent personas:

- **Test commands** — lint, typecheck, and test suite commands (e.g., `npm run lint`, `pytest`, `cargo test`)
- **Source structure** — where features, components, and services live
- **Database/store patterns** — factory functions, ORMs, raw SQL, whatever your project uses
- **Coverage thresholds** — statement, branch, function, and line targets
- **Complexity thresholds** — cyclomatic complexity limits for your codebase
- **Build and deploy commands** — how your project builds and ships

The system adapts to your stack. It has been developed on a React/Express/PostgreSQL project but the orchestration patterns, quality gates, and agent boundaries are stack-agnostic.

## Phase Sizing

| Size | Criteria | Phases Run |
|------|----------|-----------|
| **Small** | Single file change, bug fix, test addition, or fewer than 3 files | Colby -> Roz -> Ellis |
| **Medium** | 2-4 ADR steps, typical feature work | Cal -> Colby <-> Roz -> Agatha -> Ellis |
| **Large** | 5+ ADR steps, new system, multi-concern feature | Robert -> Sable -> Agatha -> Colby (mockup) -> Cal -> Roz <-> Colby -> Agatha -> Ellis |

Eva assesses scope at the start and adjusts automatically. Users can override with "full ceremony" (forces all pauses) or "stop" / "hold" (halts auto-advance).

## Slash Commands

| Command | Agent | Purpose |
|---------|-------|---------|
| `/pm` | Robert | Feature discovery and product spec |
| `/ux` | Sable | UI/UX design and interaction patterns |
| `/architect` | Cal | Architecture clarification and ADR production |
| `/debug` | Roz -> Colby -> Roz | Investigation, fix, verification chain |
| `/pipeline` | Eva | Full pipeline orchestration |
| `/devops` | Eva | Infrastructure and deployment |
| `/docs` | Agatha | Documentation planning and writing |

## Credits

Built and battle-tested on a real production project over dozens of pipeline runs. Every principle, gate, and lesson in this system came from an actual failure that was diagnosed, fixed, and prevented from recurring.

**Author:** Robert Sfeir
