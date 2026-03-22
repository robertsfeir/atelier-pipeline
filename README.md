# Atelier Pipeline

A Claude Code plugin that provides multi-agent orchestration with quality gates, continuous QA, and persistent institutional memory across sessions.

## What It Does

Atelier Pipeline has two core systems:

**Multi-Agent Orchestration.** Ten specialized agent personas with clear responsibilities, strict boundaries, and independent quality verification. Eva orchestrates, Robert handles product, Sable designs UX, Cal architects, Colby builds, Roz tests, Poirot blind-reviews, Agatha documents, Ellis commits, and Distillator compresses. Specs get written, designs get validated, tests get authored before code, every change passes independent QA, and nothing ships without review.

**Atelier Brain.** A persistent memory layer backed by PostgreSQL and vector embeddings that gives your agents institutional memory across sessions. Without it, every time you close a terminal you lose the architectural decisions that shaped your implementation, the user corrections that steered scope, the rejected alternatives that explain why you didn't go a different way, and the QA lessons that prevent recurring bugs. The brain captures all of this during pipeline runs and surfaces it automatically when agents need context. It includes write-time conflict detection, TTL-based knowledge decay, and background consolidation that synthesizes raw observations into higher-level insights. The pipeline works without the brain — but with it, session 12 of a feature build has the same context as session 1.

## Install

### As a Claude Code Plugin

```
/plugin marketplace add robertsfeir/atelier-pipeline
/plugin install atelier-pipeline
```

Then run the setup skill in your project:

```
/pipeline-setup
```

Claude walks you through project configuration (tech stack, test commands, source structure) and installs 27 files. At the end, it offers to set up the Atelier Brain for persistent memory.

### Manual Setup (without plugin system)

```bash
git clone https://github.com/robertsfeir/atelier-pipeline.git /tmp/atelier-pipeline
```

Then in Claude Code:

```
Read /tmp/atelier-pipeline/skills/pipeline-setup/SKILL.md and follow its
instructions to install the pipeline in this project
```

## Skills

The plugin provides four skills:

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/pipeline-setup` | "set up the pipeline", "install atelier" | Installs all agent personas, commands, references, and state files into your project |
| `/pipeline-overview` | "how does the pipeline work", "explain atelier" | Quick reference for the pipeline system, agents, and principles |
| `/brain-setup` | "set up the brain", "configure brain" | Configures the Atelier Brain persistent memory (Docker or local PostgreSQL) |
| `/brain-hydrate` | "hydrate brain", "seed memory", "import history" | Imports existing project knowledge (ADRs, specs, git history) into the brain |

## The Pipeline

```
                       Idea
                        |
                   Robert (spec)
                     /      \
              Sable (UX)    Agatha (doc plan)         --- parallel
                     \      /
                  Colby (mockup)
                        |
               Sable verifies mockup                  --- UX acceptance
                        |
                   User UAT review
                        |
              Cal (architecture + test spec)
                        |
                Roz (test spec review)
                        |
                Roz (test authoring)
                        |
    Colby (build) <-> Roz (QA) + Poirot               --- interleaved per ADR step
                        |
    Roz + Poirot + Robert + Sable                      --- review juncture (parallel)
                        |
                 Agatha (docs)                         --- against final verified code
                        |
             Robert verifies docs                      --- product acceptance
                        |
         Spec/UX reconciliation (if drift)             --- living artifacts updated
                        |
              Ellis (commit + changelog)               --- one atomic commit
```

**Phase sizing keeps it pragmatic:**

| Size | Criteria | What Runs |
|------|----------|-----------|
| **Small** | Bug fix, single file, < 3 files | Colby -> Roz -> (Agatha if doc impact) -> Ellis |
| **Medium** | 2-4 ADR steps, typical feature | Robert spec -> Cal -> Colby <-> Roz + Poirot -> Robert review -> Agatha -> Ellis |
| **Large** | 5+ ADR steps, new system | Full pipeline including Sable mockup + UX acceptance |

## Agents

| Agent | Role | Type |
|-------|------|------|
| **Eva** | Pipeline Orchestrator / DevOps | Skill (main thread) |
| **Robert** | Chief Product Officer | Skill + Subagent |
| **Sable** | Senior UI/UX Designer | Skill + Subagent |
| **Cal** | Senior Software Architect | Skill + Subagent |
| **Colby** | Senior Software Engineer | Subagent |
| **Roz** | QA Engineer | Subagent |
| **Poirot** | Blind Code Investigator | Subagent |
| **Agatha** | Documentation Specialist | Skill + Subagent |
| **Ellis** | Commit and Changelog Manager | Subagent |
| **Distillator** | Compression Engine | Subagent |

**Skills** run in the main Claude Code thread for conversational work. **Subagents** run in their own context windows for focused execution. Some agents have both modes — conversational for authoring, subagent for verification.

## Slash Commands

These are installed into your project by `/pipeline-setup`:

| Command | Agent | Purpose |
|---------|-------|---------|
| `/pm` | Robert | Feature discovery and product spec |
| `/ux` | Sable | UI/UX design and interaction patterns |
| `/architect` | Cal | Architecture clarification and ADR production |
| `/debug` | Roz -> Colby -> Roz | Investigation, fix, verification chain |
| `/pipeline` | Eva | Full pipeline orchestration |
| `/devops` | Eva | Infrastructure and deployment |
| `/docs` | Agatha | Documentation planning and writing |

## Atelier Brain Setup

The brain is an MCP server with 6 tools (`agent_capture`, `agent_search`, `atelier_browse`, `atelier_stats`, `atelier_relation`, `atelier_trace`) that agents use automatically during pipeline runs.

**Getting started:**

1. **`/brain-setup`** — Configures the database and connection. Supports Docker (recommended) or local PostgreSQL. Requires an OpenRouter API key for embeddings. Supports personal (local, not committed) or shared (team, committed) configurations.

2. **`/brain-hydrate`** — Imports reasoning from existing project artifacts into a fresh brain. Scans ADRs, feature specs, UX docs, error patterns, retro lessons, and git history. Extracts the *why* behind decisions, not the content itself. Safe to re-run — duplicate detection prevents re-importing.

## What Gets Installed

`/pipeline-setup` installs 27 files into your project:

```
your-project/
  .claude/
    rules/                       # Always loaded by Claude Code
      default-persona.md         # Eva orchestrator persona
      agent-system.md            # Orchestration rules, routing, gates
    agents/                      # Loaded when subagents are invoked
      cal.md                     # Architect
      colby.md                   # Engineer
      roz.md                     # QA
      robert.md                  # Product reviewer
      sable.md                   # UX reviewer
      investigator.md            # Poirot (blind investigator)
      distillator.md             # Compression engine
      ellis.md                   # Commit manager
      documentation-expert.md    # Agatha (documentation)
    commands/                    # Loaded when user types slash command
      pm.md                      # /pm (Robert)
      ux.md                      # /ux (Sable)
      architect.md               # /architect (Cal)
      debug.md                   # /debug (Roz -> Colby -> Roz)
      pipeline.md                # /pipeline (Eva)
      devops.md                  # /devops (Eva)
      docs.md                    # /docs (Agatha)
    references/                  # Loaded by agents on demand
      dor-dod.md                 # Quality framework
      retro-lessons.md           # Shared lessons (starts empty)
      invocation-templates.md    # Subagent invocation examples
      pipeline-operations.md     # Model selection, QA flow, feedback loops
  docs/
    pipeline/                    # Eva reads at session start for recovery
      pipeline-state.md          # Session recovery state
      context-brief.md           # Cross-session context
      error-patterns.md          # Error pattern tracking
      investigation-ledger.md    # Debug hypothesis tracking
      last-qa-report.md          # Roz's most recent QA report
```

## Key Principles

- **Roz-First TDD.** Roz writes tests before Colby builds. Colby cannot modify Roz's assertions.
- **Continuous QA.** Each ADR step is a work unit with its own test-build-review cycle.
- **DoR/DoD.** Every agent proves it read upstream artifacts (DoR) and covers all requirements (DoD).
- **Information asymmetry.** Three parallel reviewers see constrained context to prevent anchoring — Poirot sees only the diff, Robert sees only the spec, Sable sees only the UX doc.
- **Four-layer investigation.** Debug flows check Application, Transport, Infrastructure, Environment. Two rejected hypotheses at one layer forces escalation.
- **Living artifacts.** Specs and UX docs are updated at pipeline end. ADRs are immutable records.
- **Retro lessons.** Error patterns recurring 3+ times get injected as warnings into future agent prompts.

## Customization

During setup, you configure project-specific values:

- Test commands (lint, typecheck, test suite)
- Source structure (where features, components, services live)
- Database/store patterns
- Coverage and complexity thresholds
- Build and deploy commands

The orchestration patterns and quality gates are stack-agnostic.

## Author

Robert Sfeir
