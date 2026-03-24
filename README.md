# Atelier Pipeline

A Claude Code plugin that provides multi-agent orchestration with quality gates, continuous QA, and persistent institutional memory across sessions.

## What It Does

Atelier Pipeline has two core systems:

**Multi-Agent Orchestration.** Ten specialized agent personas with clear responsibilities, strict boundaries, and independent quality verification. Eva orchestrates, Robert handles product, Sable designs UX, Cal architects, Colby builds, Roz tests, Poirot blind-reviews, Agatha documents, Ellis commits, and Distillator compresses. Specs get written, designs get validated, tests get authored before code, every change passes independent QA, and nothing ships without review.

**Atelier Brain.** A persistent memory layer backed by PostgreSQL and vector embeddings that gives your agents institutional memory across sessions. Without it, every time you close a terminal you lose the architectural decisions that shaped your implementation, the user corrections that steered scope, the rejected alternatives that explain why you didn't go a different way, and the QA lessons that prevent recurring bugs. The brain captures all of this during pipeline runs and surfaces it automatically when agents need context. It includes write-time conflict detection, TTL-based knowledge decay, and background consolidation that synthesizes raw observations into higher-level insights. The pipeline works without the brain — but with it, session 12 of a feature build has the same context as session 1.

For full documentation, see the [User Guide](docs/guide/user-guide.md) and [Technical Reference](docs/guide/technical-reference.md).

## Getting Started

### 1. Install the Plugin

Add the marketplace and install:

```
/plugin marketplace add robertsfeir/atelier-pipeline
/plugin install atelier-pipeline@atelier-pipeline
```

Restart Claude Code after install.

### 2. Set Up the Pipeline

Open Claude Code in your project and run:

```
/pipeline-setup
```

Claude walks you through project configuration one question at a time:
- Tech stack and framework
- Test commands (lint, typecheck, test suite)
- Source structure and database patterns
- Coverage and complexity thresholds

It then installs 36 files into your project (agent personas, commands, references, enforcement hooks, pipeline state). At the end, it offers to set up the Atelier Brain.

### 3. Set Up the Brain (optional but recommended)

If you skipped the brain offer during pipeline setup, run it separately:

```
/brain-setup
```

The setup asks:

1. **Personal or shared?** Personal config stays local (never committed). Shared config is committed to the repo with `${ENV_VAR}` placeholders — no bare secrets.
2. **Docker, local PostgreSQL, or remote PostgreSQL?** Docker is one command (`docker compose up`). Local PostgreSQL requires pgvector and ltree extensions. Remote PostgreSQL (RDS, Supabase, etc.) connects to an existing managed database — setup verifies the connection, checks for required extensions, and applies the schema if needed.
3. **OpenRouter API key.** Needed for vector embeddings. Get one at https://openrouter.ai/keys and set `export OPENROUTER_API_KEY="sk-or-..."` in your shell profile.
4. **Scope path.** A dot-separated namespace like `myorg.myproduct` that organizes knowledge.

Setup verifies the connection and confirms:

```
Brain is live.
  Tools available: 6
  Scope: myorg.myproduct
  Config: personal (~/.claude/plugins/data/atelier-pipeline/brain-config.json)
  Database: Local PostgreSQL (myproject_brain)
```

**Teammate onboarding:** If a shared brain config already exists in the repo, `/brain-setup` detects it automatically and tells the new team member which environment variables to set. No interactive setup needed.

### 4. Hydrate the Brain (optional)

For existing projects with ADRs, specs, or git history:

```
/brain-hydrate
```

Scans your project artifacts, extracts the reasoning behind decisions (not the content itself), and imports it as brain thoughts. Safe to re-run — duplicate detection prevents re-importing.

### 5. Start Building

Describe a feature idea, or type `/pipeline` to start Eva. She sizes the work and routes to the right agent.

## Updating the Plugin

```
claude plugin marketplace update atelier-pipeline
claude plugin update atelier-pipeline@atelier-pipeline
```

The first command refreshes the marketplace catalog. The second pulls the new plugin version. Restart Claude Code after updating.

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
| `/brain-setup` | "set up the brain", "configure brain" | Configures the Atelier Brain persistent memory (Docker, local PostgreSQL, or remote PostgreSQL) |
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
| **Micro** | ≤2 files, mechanical, no behavioral change | Colby → test suite → Ellis |
| **Small** | Bug fix, single file, < 3 files | Colby -> Roz -> (Agatha if doc impact) -> Ellis |
| **Medium** | 2-4 ADR steps, typical feature | Robert spec -> Cal -> Colby <-> Roz + Poirot -> Robert review -> Agatha -> Ellis |
| **Large** | 5+ ADR steps, new system | Full pipeline including Sable mockup + UX acceptance |

v2.3 adds wave-based parallel execution, per-unit commits, Robert assumptions-mode for brownfield features, triage consensus matrix, task-level model routing, and Brain pattern/seed capture. See ADR-0004 for details.

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

The brain is an MCP server with 6 tools that agents use automatically during pipeline runs:

| Tool | Purpose |
|------|---------|
| `agent_capture` | Save a decision, lesson, preference, or correction |
| `agent_search` | Semantic search across brain thoughts |
| `atelier_browse` | Paginated browse by type or status |
| `atelier_stats` | Brain health check (thought count, config, status) |
| `atelier_relation` | Create typed edges between thoughts (supersedes, contradicts, evolves_from) |
| `atelier_trace` | Walk relation chains from a thought |

Agents capture thoughts during pipeline runs and search for relevant context before making decisions. Write-time conflict detection catches contradictions (>0.9 similarity = duplicate, 0.7-0.9 = LLM-classified). TTL decay expires stale knowledge per thought type. Background consolidation synthesizes raw observations into reflections.

## What Gets Installed

`/pipeline-setup` installs 36 files into your project:

```
your-project/
  .claude/
    rules/                       # Always loaded by Claude Code
      default-persona.md         # Eva orchestrator persona
      agent-system.md            # Orchestration rules, routing, gates
      pipeline-orchestration.md  # Pipeline operations (path-scoped, loads during active pipelines)
      pipeline-models.md         # Model selection tables (path-scoped)
    agents/                      # Loaded when subagents are invoked
      cal.md                     # Architect
      colby.md                   # Engineer
      roz.md                     # QA
      robert.md                  # Product reviewer
      sable.md                   # UX reviewer
      investigator.md            # Poirot (blind investigator)
      distillator.md             # Compression engine
      ellis.md                   # Commit manager
      agatha.md                  # Agatha (documentation)
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
    hooks/                       # Mechanical enforcement (PreToolUse/PostToolUse)
      enforce-paths.sh           # Blocks Write/Edit outside agent's allowed paths
      enforce-sequencing.sh      # Blocks out-of-order agent invocations
      enforce-git.sh             # Blocks git write ops from main thread
      check-brain-usage.sh       # Warns when agents skip brain tools
      enforcement-config.json    # Project-specific paths and rules
    settings.json                # Hook registration
  docs/
    pipeline/                    # Eva reads at session start for recovery
      pipeline-state.md          # Session recovery state
      context-brief.md           # Cross-session context
      error-patterns.md          # Error pattern tracking
      investigation-ledger.md    # Debug hypothesis tracking
      last-qa-report.md          # Roz's most recent QA report
```

**Requires:** `jq` for hook enforcement (`brew install jq` on macOS, `apt install jq` on Linux).

## Key Principles

- **Roz-First TDD.** Roz writes tests before Colby builds. Colby cannot modify Roz's assertions.
- **Continuous QA.** Each ADR step is a work unit with its own test-build-review cycle.
- **DoR/DoD.** Every agent proves it read upstream artifacts (DoR) and covers all requirements (DoD).
- **Information asymmetry.** Three parallel reviewers see constrained context to prevent anchoring — Poirot sees only the diff, Robert sees only the spec, Sable sees only the UX doc.
- **Four-layer investigation.** Debug flows check Application, Transport, Infrastructure, Environment. Two rejected hypotheses at one layer forces escalation.
- **Living artifacts.** Specs and UX docs are updated at pipeline end. ADRs are immutable records.
- **Retro lessons.** Error patterns recurring 3+ times get injected as warnings into future agent prompts.
- **Mechanical enforcement.** PreToolUse hooks block agents from writing outside their designated paths, enforce pipeline sequencing (no commits without QA), and prevent Eva from running git operations directly. Behavioral guidance tells agents what to do; hooks ensure they can't do what they shouldn't.

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

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
