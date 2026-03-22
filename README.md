# Atelier Pipeline

A Claude Code plugin that provides multi-agent orchestration with quality gates, continuous QA, and persistent memory across sessions.

## What It Does

Atelier Pipeline installs ten specialized agent personas into your Claude Code project — each with clear responsibilities, strict boundaries, and independent quality verification. Eva orchestrates, Robert handles product, Sable designs UX, Cal architects, Colby builds, Roz tests, Poirot blind-reviews, Agatha documents, Ellis commits, and Distillator compresses. The result: specs get written, designs get validated, tests get authored before code, every change passes independent QA, and nothing ships without review.

The plugin includes an optional persistent memory layer (Atelier Brain) that preserves architectural decisions, user corrections, QA lessons, and rejected alternatives across sessions.

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

## Atelier Brain

Optional persistent memory layer that gives agents institutional memory across sessions. Without it, the pipeline works identically — the brain adds cross-session context, not runtime behavior.

**What it stores:** Architectural decisions, rejected alternatives, user corrections, QA lessons, spec drift history, and consolidated reflections.

**How it works:** MCP server backed by PostgreSQL + pgvector. Agents capture thoughts during pipeline runs and search for relevant context before making decisions. Write-time conflict detection catches contradictions. TTL decay expires stale knowledge. Background consolidation synthesizes raw observations into higher-level insights.

**Setup:** Run `/brain-setup` after installing the pipeline. Supports Docker (recommended) or local PostgreSQL. Requires an OpenRouter API key for embeddings.

**Hydration:** Run `/brain-hydrate` to import reasoning from existing project artifacts (ADRs, specs, UX docs, error patterns, git history) into a fresh brain.

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
