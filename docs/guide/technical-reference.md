# Atelier Pipeline -- Technical Reference

Version: 3.4.0

This document is the comprehensive technical reference for the atelier-pipeline Claude Code plugin. It covers plugin architecture, agent system design, orchestration logic, brain infrastructure, and customization points. For usage-oriented documentation, see [the user guide](user-guide.md).

---

## Table of Contents

1. [Plugin Architecture](#plugin-architecture)
2. [File Tree -- What Lives Where](#file-tree----what-lives-where)
3. [Loading Mechanics -- What Loads When](#loading-mechanics----what-loads-when)
4. [Agent System Design](#agent-system-design)
5. [Agent Reference Table](#agent-reference-table)
6. [Information Asymmetry Design](#information-asymmetry-design)
7. [Eva's Orchestration Logic](#evas-orchestration-logic)
8. [Invocation Template System](#invocation-template-system)
9. [DoR/DoD Framework](#dordod-framework)
10. [Continuous QA Flow](#continuous-qa-flow)
11. [Error Pattern Tracking and Retro Lessons](#error-pattern-tracking-and-retro-lessons)
12. [Brain Architecture](#brain-architecture)
13. [Team Collaboration Internals](#team-collaboration-internals)
14. [Pipeline State Files and Session Recovery](#pipeline-state-files-and-session-recovery)
15. [Setup and Install System](#setup-and-install-system)
16. [Branching Strategy Variants](#branching-strategy-variants)
17. [Enforcement Hooks](#enforcement-hooks)
18. [Customization Points](#customization-points)

---

## Plugin Architecture

Atelier Pipeline is a Claude Code plugin distributed via the plugin marketplace. It consists of two subsystems:

1. **Multi-agent orchestration** -- template files installed into the target project's `.claude/` and `docs/pipeline/` directories. These define agent personas, slash commands, quality references, and state files.
2. **Atelier Brain** -- an MCP server (`brain/server.mjs`) that runs as a sidecar, providing persistent institutional memory backed by PostgreSQL and vector embeddings.

The plugin itself lives in the Claude Code plugin directory (typically `~/.claude/plugins/atelier-pipeline/`). The plugin metadata is in `.claude-plugin/plugin.json`.

### Plugin-Level Files (stay in the plugin directory)

```
atelier-pipeline/                         # Plugin root (CLAUDE_PLUGIN_ROOT)
  .claude-plugin/
    plugin.json                           # Plugin metadata, hooks, version (3.4.0)
  source/                                 # Template files -- copied to target project
    rules/
      default-persona.md
      agent-system.md
      pipeline-orchestration.md           # Path-scoped to docs/pipeline/**
      pipeline-models.md                  # Path-scoped to docs/pipeline/**
    agents/
      cal.md, colby.md, roz.md, robert.md,
      sable.md, investigator.md, distillator.md,
      ellis.md, agatha.md
    commands/
      pm.md, ux.md, architect.md, debug.md,
      pipeline.md, devops.md, docs.md
    references/
      dor-dod.md, retro-lessons.md,
      invocation-templates.md, pipeline-operations.md,
      agent-preamble.md, qa-checks.md,
      branch-mr-mode.md
    pipeline/
      pipeline-state.md, context-brief.md, error-patterns.md,
      investigation-ledger.md, last-qa-report.md,
      pipeline-config.json                # Branching strategy configuration template
    variants/                             # Branch lifecycle strategy variants
      branch-lifecycle-trunk-based.md     # Trunk-based (default)
      branch-lifecycle-github-flow.md     # GitHub Flow
      branch-lifecycle-gitlab-flow.md     # GitLab Flow
      branch-lifecycle-gitflow.md         # GitFlow
    hooks/                                # Enforcement hook templates
      enforce-paths.sh                    # File path enforcement per agent
      enforce-sequencing.sh               # Pipeline sequencing gates
      enforce-git.sh                      # Git write operation guard
      enforcement-config.json             # Project-specific paths and rules
  brain/                                  # MCP server -- runs as sidecar
    start.sh                              # Wrapper script -- installs node_modules then starts server
    server.mjs                            # Main server (MCP + REST API, auto-migration)
    schema.sql                            # PostgreSQL schema (canonical for fresh installs)
    migrations/                           # Idempotent SQL migrations for existing databases
      001-add-captured-by.sql             # Adds captured_by column, updates match function
      002-add-handoff-enums.sql           # Adds handoff to thought_type and source_phase enums
    docker-compose.yml                    # Docker setup for brain database
    docker-entrypoint.sh
    package.json
    ui/                                   # Settings UI (Phase 2)
  skills/                                 # Plugin skills (run in main thread)
    pipeline-setup/SKILL.md               # /pipeline-setup
    brain-setup/SKILL.md                  # /brain-setup
    brain-hydrate/SKILL.md                # /brain-hydrate
  scripts/
    check-updates.sh                      # SessionStart hook -- detects plugin updates
```

### Hooks

The plugin registers a `SessionStart` hook in `plugin.json` that runs two commands on every Claude Code session start:

1. **Dependency install** -- runs `npm install` in the `brain/` directory if `node_modules` does not exist.
2. **Update check** -- runs `scripts/check-updates.sh` to compare the installed template version (`.claude/.atelier-version`) against the current plugin version. If they differ, it notifies the user that pipeline files may be outdated.

---

## File Tree -- What Lives Where

After running `/pipeline-setup`, 38 files are installed into the target project. The plugin templates remain in the plugin directory and are never modified.

### Target Project (installed by /pipeline-setup)

```
your-project/
  .claude/
    .atelier-version                      # Plugin version marker for update detection
    rules/                                # Always loaded by Claude Code
      default-persona.md                  # Eva orchestrator persona (identity)
      agent-system.md                     # Orchestration rules, routing (identity)
      pipeline-orchestration.md           # Mandatory gates, triage, wave execution (path-scoped: docs/pipeline/**)
      pipeline-models.md                  # Model selection, Micro tier, complexity classifier (path-scoped: docs/pipeline/**)
      branch-lifecycle.md                 # Branch lifecycle rules for selected strategy (path-scoped: docs/pipeline/**)
    agents/                               # Loaded when subagents are invoked
      cal.md                              # Architect
      colby.md                            # Engineer
      roz.md                              # QA
      robert.md                           # Product reviewer
      sable.md                            # UX reviewer
      investigator.md                     # Poirot (blind investigator)
      distillator.md                      # Compression engine
      ellis.md                            # Commit manager
      agatha.md                            # Agatha (documentation)
    commands/                             # Loaded when user types slash command
      pm.md                               # /pm (Robert)
      ux.md                               # /ux (Sable)
      architect.md                        # /architect (Cal)
      debug.md                            # /debug (Roz -> Colby -> Roz)
      pipeline.md                         # /pipeline (Eva)
      devops.md                           # /devops (Eva)
      docs.md                             # /docs (Agatha)
    references/                           # Loaded by agents on demand
      dor-dod.md                          # Quality framework
      retro-lessons.md                    # Shared lessons (starts empty)
      invocation-templates.md             # Subagent invocation examples
      pipeline-operations.md              # Model selection, QA flow, feedback loops
      agent-preamble.md                   # Shared required actions (DoR/DoD, retro, brain)
      qa-checks.md                        # Roz QA check procedures (Tier 1 + Tier 2)
      branch-mr-mode.md                   # Colby branch creation and MR procedures
    hooks/                                # Mechanical enforcement (PreToolUse)
      enforce-paths.sh                    # Blocks Write/Edit outside agent's allowed paths
      enforce-sequencing.sh               # Blocks out-of-order agent invocations
      enforce-git.sh                      # Blocks git write ops from main thread
      enforcement-config.json             # Project-specific paths and rules
    pipeline-config.json                    # Branching strategy configuration
    settings.json                         # Hook registration
  docs/
    pipeline/                             # Eva reads at session start for recovery
      pipeline-state.md                   # Session recovery state
      context-brief.md                    # Cross-session context
      error-patterns.md                   # Error pattern tracking
      investigation-ledger.md             # Debug hypothesis tracking
      last-qa-report.md                   # Roz's most recent QA report
```

**Total: 38 files across 6 directories, plus the `.atelier-version` marker and an update to `CLAUDE.md`.** Three new reference files (`agent-preamble.md`, `qa-checks.md`, `branch-mr-mode.md`) extract shared behaviors from agent persona files to reduce duplication. The two additional files compared to v3.0 are `.claude/pipeline-config.json` (branching strategy configuration) and `.claude/rules/branch-lifecycle.md` (selected strategy's lifecycle rules).

### What Does NOT Live on Disk

- QA reports (returned by Roz, read by Eva, not persisted except `last-qa-report.md`)
- Robert-subagent and Sable-subagent acceptance reports (returned, triaged by Eva)
- Agent state or conversation history (subagent context windows are ephemeral)

---

## Loading Mechanics -- What Loads When

Claude Code has specific loading behaviors for each directory under `.claude/`:

| Directory | When Loaded | Loaded By | Scope |
|-----------|-------------|-----------|-------|
| `.claude/rules/` | **Every conversation**, automatically | Claude Code runtime | Global -- all messages see these files |
| `.claude/agents/` | When a subagent is invoked via the Agent tool | Claude Code Agent tool | Per-subagent -- only the invoked agent's file |
| `.claude/commands/` | When the user types a `/command` | Claude Code command system | Per-command -- only the triggered command's file |
| `.claude/references/` | On demand, when an agent reads them | Agents via `Read` tool | Per-read -- loaded just-in-time |
| `docs/pipeline/` | At session start by Eva, during pipeline | Eva via `Read` tool | Per-read |

**Critical implication:** `default-persona.md` and `agent-system.md` are always in context. This is why Eva is the default persona -- she is present in every conversation whether or not `/pipeline` is invoked. All other files are loaded only when needed, keeping context usage efficient.

**Eva's always-loaded context** consists of exactly three files: `default-persona.md`, `agent-system.md`, and `CLAUDE.md`. She does NOT pre-load `CONVENTIONS.md`, `dor-dod.md`, or `retro-lessons.md` -- those are subagent concerns.

### Path-Scoped Rules (Identity vs. Operations Split)

Eva's rules are split into two categories to stay under Anthropic's recommended ~200 lines per rules file:

**Identity files** (always-loaded via `.claude/rules/`):
- `default-persona.md` -- who Eva is, what she never does, session boot sequence
- `agent-system.md` -- architecture, agent tables, routing, sizing, invocation template

**Operations files** (path-scoped via YAML frontmatter):
- `pipeline-orchestration.md` -- mandatory gates, triage consensus matrix, wave execution, per-unit commit flow, investigation discipline, agent standards, review juncture, reconciliation
- `pipeline-models.md` -- model selection tables, Micro-tier criteria, Colby complexity classifier
- `branch-lifecycle.md` -- branching strategy lifecycle rules (selected variant only: trunk-based, github-flow, gitlab-flow, or gitflow)

Operations files use a `paths: ["docs/pipeline/**"]` frontmatter declaration. Claude Code loads them automatically when any file matching that glob is read. Since Eva's boot sequence reads `docs/pipeline/pipeline-state.md` on every session with an active pipeline, the operational rules load exactly when needed.

**Why this matters:**
- **Compaction resilience.** Rules files are re-injected from disk after `/compact`. Content loaded via the Read tool gets summarized (potentially lossy). For mandatory gates and triage logic, lossy summarization is unacceptable.
- **Context efficiency.** Casual Eva (no active pipeline) carries only identity + routing (~350 lines). Active-pipeline Eva gets the full operational ruleset (~430 additional lines) loaded on demand.
- **Feature isolation.** New pipeline features (wave execution, triage matrix, model routing) land in the operations files, not the always-loaded identity files.

### XML Tag Structure (v2.4 -- ADR-0006)

All agent-facing instruction files use semantic XML tags per Anthropic's recommendation. Tags wrap logical sections that benefit from unambiguous boundaries: gates, protocols, routing tables, operation blocks. Short, self-contained sections that are already clear from their `##` headers do not need wrapping.

**Tag vocabulary by file type:**

| File type | Tags used | Purpose |
|-----------|-----------|---------|
| Rules files (`rules/*.md`) | `<gate>`, `<protocol>`, `<routing>`, `<model-table>`, `<section>` | Mandatory gates, ordered procedures, lookup tables, protocol definitions |
| Reference files (`references/*.md`) | `<framework>`, `<agent-dod>`, `<template>`, `<operations>`, `<matrix>`, `<section>` | Framework definitions, per-agent DoD blocks, invocation templates, operation procedures, decision matrices |
| Agent personas (`agents/*.md`) | `<identity>`, `<required-actions>`, `<workflow>`, `<examples>`, `<tools>`, `<constraints>`, `<output>` | Persona structure (unchanged from ADR-0005) |
| Skill commands (`commands/*.md`) | `<procedure>`, `<gate>`, `<error-handling>`, `<protocol>`, `<section>` | Skill structure (unchanged from ADR-0005) |

The full tag vocabulary is documented in `.claude/references/xml-prompt-schema.md`. This is a structural change only -- no behavioral changes were made during the migration.

---

## Agent System Design

### Skills vs. Subagents

The system uses a hybrid architecture with two execution modes:

**Skills** run in the main Claude Code thread. They are conversational, support back-and-forth with the user, and share the main context window. When Eva adopts a skill persona (e.g., Robert for `/pm`), she reads the command file and behaves as that agent within the main thread.

**Subagents** run in their own context windows via Claude Code's Agent tool. They receive focused prompts, execute their task, and return results. Their context window is isolated -- they cannot see what other agents produced unless Eva includes it in their invocation prompt.

Some agents operate in both modes:
- **Robert**: skill mode for spec authoring (`/pm`), subagent mode for product acceptance review
- **Sable**: skill mode for UX design (`/ux`), subagent mode for mockup/implementation verification
- **Cal**: skill mode for conversational clarification (`/architect`), subagent mode for ADR production
- **Agatha**: skill mode for doc planning (`/docs`), subagent mode for doc writing

### Custom Commands Are Not Skills

The slash commands (`/pm`, `/ux`, `/docs`, `/architect`, `/debug`, `/pipeline`, `/devops`) are **custom agent persona commands**, not Claude Code skills. The `Skill` tool must not be invoked for them. When the user types one, Eva reads the corresponding `.claude/commands/*.md` file and adopts that agent's persona. This distinction matters because skills use the `Skill` tool invocation path, while custom commands trigger persona adoption in the main thread.

The four actual plugin skills (`/pipeline-setup`, `/pipeline-overview`, `/brain-setup`, `/brain-hydrate`) live in the plugin's `skills/` directory and are invoked through the `Skill` tool.

---

## Agent Reference Table

Agent persona files use `disallowedTools` (denylist) in their frontmatter rather than a `tools` allowlist. This ensures subagents inherit MCP tools (including brain tools) from the parent session -- a `tools` allowlist would block MCP tool inheritance because only explicitly listed tools would be available to the subagent.

| Agent | Role | Execution Mode | Tools | Write Access | Brain Access | Model (Fixed/Size-Dependent) |
|-------|------|---------------|-------|-------------|--------------|------------------------------|
| **Eva** | Pipeline Orchestrator / DevOps | Main thread (always loaded) | Read, Glob, Grep, Bash, TaskCreate, TaskUpdate | `docs/pipeline/` state files ONLY | Reads: `agent_search`, `atelier_stats`. Writes: cross-cutting decisions, phase transitions, Poirot findings. | N/A (orchestrator) |
| **Robert** (skill) | CPO -- spec authoring | Main thread (`/pm`) | Full conversational | Spec files | Reads: prior specs, corrections. Writes: spec rationale, corrections. | N/A (skill) |
| **Robert** (subagent) | Product acceptance reviewer | Subagent | Read, Glob, Grep, Bash | **None** (read-only) | Reads: spec evolution, prior drift. Writes: drift findings, pass verdicts. | Opus (fixed) |
| **Sable** (skill) | UX Designer -- doc authoring | Main thread (`/ux`) | Full conversational | UX docs | Reads: prior UX decisions, a11y. Writes: UX rationale, corrections. | N/A (skill) |
| **Sable** (subagent) | UX acceptance reviewer | Subagent | Read, Glob, Grep, Bash | **None** (read-only) | Reads: UX doc evolution. Writes: drift/missing verdicts, five-state audit. | Opus (fixed) |
| **Cal** (skill) | Architect -- conversational | Main thread (`/architect`) | Full conversational | None during conversation | Reads: prior decisions, constraints. | N/A (skill) |
| **Cal** (subagent) | Architect -- ADR production | Subagent | Read, Write, Edit, Glob, Grep, Bash | ADR files | Reads: prior decisions, rejected approaches. Writes: decisions, rejections, insights. | Opus (fixed for Medium/Large) |
| **Colby** | Senior Software Engineer | Subagent | Read, Write, Edit, MultiEdit, Glob, Grep, Bash | Source files, test files | Reads: implementation patterns, gotchas. Writes: implementation insights, workarounds. | Sonnet (Small/Medium), Opus (Large) |
| **Roz** | QA Engineer | Subagent | Read, Write, Glob, Grep, Bash | **Test files ONLY** | Reads: QA patterns, fragile areas. Writes: recurring patterns, investigation findings, doc impact. | Opus (fixed) |
| **Poirot** | Blind Code Investigator | Subagent | Read, Glob, Grep, Bash | **None** (read-only) | **None** -- Poirot never touches brain. Eva captures his findings. | Opus (fixed) |
| **Agatha** (skill) | Documentation -- planning | Main thread (`/docs`) | Full conversational | None during planning | N/A | N/A (skill) |
| **Agatha** (subagent) | Documentation -- writing | Subagent | Read, Write, Edit, MultiEdit, Grep, Glob, Bash | Documentation files | Reads: prior doc reasoning, drift patterns. Writes: doc update reasoning, gap findings. | Haiku (reference docs), Sonnet (conceptual docs) |
| **Ellis** | Commit and Changelog Manager | Subagent | Read, Write, Edit, Glob, Grep, Bash | Git operations, changelog | N/A | Sonnet (fixed) |
| **Distillator** | Lossless Compression Engine | Subagent | Read, Glob, Grep, Bash | **None** (read-only, output returned to Eva) | **None** | Haiku (fixed) |

### Forbidden Actions by Agent

| Agent | Forbidden Actions |
|-------|-------------------|
| **Eva** | Write/Edit/MultiEdit/NotebookEdit on ANY file outside `docs/pipeline/`. Never writes code. Never runs `git add`/`commit`/`push`. Never investigates user-reported bugs (Roz does). Never embeds root cause in TASK field. |
| **Robert** (subagent) | Read ADR files, UX docs, or Roz reports. Write/Edit anything. Ask for more context. Produce blanket approvals. Decide whether to update spec or fix code (reports delta, human decides). |
| **Sable** (subagent) | Read ADR files, product specs, or Roz reports. Write/Edit anything. Interpret ambiguous UX docs (HALTs instead). Decide whether to update UX doc or fix code. |
| **Cal** | Write implementation code. Say "it depends" without deciding. Hand-wave ("best practice" is not a reason). Deliver ADR with placeholder steps. Omit anti-goals (must list 3). Omit SPOF identification for non-trivial designs. Skip migration and rollback sections when database schema or shared state is involved. Omit telemetry specification from ADR steps (except purely structural steps). |
| **Colby** | Modify Roz's test assertions. Leave TODO/FIXME/HACK. Report complete with unimplemented functionality. Move pages from `/mock/*` to production without real APIs. Add helper functions or abstractions not required by the ADR step or failing test. Guess at function signatures or code structure from the ADR alone without reading actual project files first. |
| **Roz** | Write to non-test files. Approve failing code. Skip checks. Trust self-reported coverage. Assert what code currently does when it contradicts domain intent. |
| **Poirot** | Read spec/ADR/product/UX docs. Ask for context. Write/Edit anything. Produce fewer than 5 findings without HALT. Write prose paragraphs. |
| **Distillator** | Drop decisions, rejected alternatives, or scope boundaries. Editorialize. Produce prose paragraphs. Modify source files. |
| **Ellis** | Commit without QA passing. Use generic commit messages. Commit without user approval. Use `git add -A` or `git add .`. |

### Cal: ADR Production Requirements (v2.4)

Every ADR Cal produces must include these sections:

**Anti-goals.** Cal lists exactly three things the design will NOT address, with reasoning and a "revisit when" condition. If Cal cannot name three anti-goals, the scope is either trivially small or dangerously unbounded. Eva uses this section to prevent scope creep during implementation.

**SPOF identification.** After identifying the riskiest assumption in the spec, Cal identifies the single point of failure in the proposed design: the one component whose failure would cascade. The output states the failure mode and how the system degrades gracefully with reduced capability. If no graceful degradation path exists, Cal flags it in Consequences -- this is a finding, not something to omit.

**Migration and rollback.** For changes that affect database schema, shared state, or cross-service contracts, Cal includes: (a) a migration plan with ordered steps including data backfill if applicable; (b) a single-step rollback strategy ("restore from backup" is not accepted); (c) a rollback window stating how long after deployment the rollback remains safe. Stateless changes (pure functions, UI components, config) skip this section.

**Telemetry per step.** Each ADR implementation step specifies what log line, metric, or event proves the step succeeded in production. Format: "Telemetry: [what]. Trigger: [when emitted]. Absence means: [failure mode]." Purely structural steps (file moves, renames) may omit this.

### Colby: Build Mode Requirements (v2.4)

**Retrieval-led reasoning.** Colby reads actual project files before writing implementation. She never assumes code structure from the ADR alone, never guesses at function signatures, and does not rely on training-data patterns when the local codebase has an established convention. CLAUDE.md and the local project are primary sources; training data is a fallback.

**Failing test first.** Before implementing any ADR step, Colby runs Roz's pre-written tests to confirm they fail for the right reason. A test that passes before any implementation is flagged -- either the test is wrong or the feature already exists.

**Minimal implementation.** Colby implements the minimum code necessary to pass the current failing test. Helper functions, utility abstractions, and convenience wrappers not required by the ADR step or failing test are noted in the DoD under "Implementation decisions not in the ADR" -- not built.

---

## Information Asymmetry Design

Three parallel reviewers (Poirot, Robert-subagent, Sable-subagent) are deliberately given constrained context to prevent anchoring bias. This is not a limitation -- it is the core design principle for independent verification.

### How It Works

| Reviewer | Receives | Does NOT Receive | Why |
|----------|----------|------------------|-----|
| **Poirot** | Raw `git diff` output only | Spec, ADR, UX doc, Eva framing, Colby self-report | Evaluates what was ACTUALLY built, not what was INTENDED. Prevents anchoring to the author's reasoning. |
| **Robert** (subagent) | Product spec + implemented code/docs | ADR, UX doc, Roz report, Colby self-report | Compares implementation against original product intent. If the ADR reframed 9 of 10 criteria but missed the 10th, Robert catches it because he reads the original spec, not the intermediary. |
| **Sable** (subagent) | UX design doc + implemented code | ADR, product spec, Roz report, Colby self-report | Compares implementation against original UX intent. If the ADR simplified an interaction during architectural planning, Sable catches the drift. |

### Enforcement

All three agents have READ audit rules in their persona files. If Eva accidentally includes non-permitted context in their invocation, they log: "Received non-[expected] context. Ignoring per information asymmetry constraint." This makes constraint violations visible rather than silently corrupting the review.

### Eva's Triage of Parallel Findings

After the review juncture (all three reviewers run in parallel with Roz's final sweep), Eva triages findings:

- **Findings in multiple reviewers** = high-confidence issues
- **Findings unique to Robert** = spec drift that survived ADR interpretation
- **Findings unique to Sable** = UX drift that survived ADR interpretation
- **Findings unique to Poirot** = context-anchoring misses (things Roz missed because she had too much context)
- **AMBIGUOUS from Robert or Sable** = hard pause, human decides

---

## Eva's Orchestration Logic

### Session Boot Sequence

Eva runs this sequence on every new session:

1. Read `docs/pipeline/pipeline-state.md` -- detect in-progress pipeline
2. Read `docs/pipeline/context-brief.md` -- verify it matches pipeline-state's feature (stale = reset)
3. Scan `docs/pipeline/error-patterns.md` -- note entries with recurrence count >= 3 for WARN injection
4. Brain health check -- call `atelier_stats`. Two gates: tool available? returns `brain_enabled: true`? Both pass = `brain_available: true`
5. Brain context retrieval (if available) -- call `agent_search` with query from current feature area
6. Announce session state to user

### Phase Sizing

Eva assesses scope at pipeline start and adjusts ceremony:

| Size | Criteria | Pipeline |
|------|----------|----------|
| **Micro** | ≤2 files, mechanical only (rename, typo, import fix, version bump), no behavioral change | Colby -> test suite -> Ellis. Test failure auto-re-sizes to Small. |
| **Small** | Bug fix, single file, < 3 files, user says "quick fix" | Colby -> Roz -> (Agatha if Roz flags doc impact) -> (Robert-subagent verifies docs if Agatha ran) -> Ellis |
| **Medium** | 2-4 ADR steps, typical feature | Robert spec -> Cal -> Roz test spec review -> Roz test authoring -> Colby <-> Roz + Poirot -> Review juncture (Roz + Poirot + Robert-subagent) -> Agatha -> Robert-subagent (docs) -> Ellis |
| **Large** | 5+ ADR steps, new system, multi-concern | Full pipeline including Sable mockup + Sable at final review juncture |

**The minimum pipeline is always Colby -> Roz -> Ellis.** No sizing level skips Roz or Ellis.

**Non-code ADR steps:** When an ADR step produces only non-code artifacts (schema DDL, agent instruction files, configuration, migration scripts), Eva skips Roz test spec review and test authoring for that step. Colby implements, then Roz reviews against ADR requirements in verification mode (not code QA). Agatha runs after Roz passes -- sequentially, not in parallel, because no Roz test spec approval gates the parallel launch. If an ADR mixes code and non-code steps, Eva splits them: code steps use the standard TDD flow, non-code steps use this flow.

### Auto-Routing

When no pipeline is active, Eva classifies every user message against the intent detection table in `agent-system.md` and routes automatically:

- High confidence: route directly, announce which agent and why
- Ambiguous: ask ONE clarifying question with a proposed action and an alternative
- Always mention slash commands as manual overrides

### Hard Pauses (Eva stops and asks the user)

- Before Ellis pushes to remote
- Roz returns BLOCKER verdict
- Robert-subagent or Sable-subagent returns AMBIGUOUS
- Robert-subagent or Sable-subagent flags DRIFT (human decides: fix code or update spec/UX)
- Cal reports a scope-changing discovery
- User says "stop" or "hold"
- After Roz's diagnosis on a user-reported bug (user must approve fix approach)

### Mandatory Gates (never skippable, same severity as Eva writing code)

1. Roz verifies every Colby output
2. Ellis commits (Eva never runs git on code)
3. Full test suite between work units
4. Roz investigates user-reported bugs (Eva does not)
5. Poirot blind-reviews every Colby output (parallel with Roz)
6. Distillator compresses upstream artifacts when >5K tokens
7. Robert-subagent reviews at review juncture (Medium/Large)
8. Sable-subagent verifies every mockup before UAT
9. Agatha writes docs after final Roz sweep, not during build
10. Spec/UX reconciliation is continuous (living artifacts updated in same commit)
11. One phase transition per turn on Medium/Large pipelines -- Eva announces, invokes, presents result, and stops. Phase bleed is the same class of violation as skipping Roz.
12. Loop-breaker: 3 consecutive failures on the same task = halt. Eva presents a Stuck Pipeline Analysis (what was attempted, what changed, why it is not converging). User decides: intervene, re-scope, or abandon.

### Model Selection

Model assignment is mechanical -- determined by agent identity and pipeline sizing. Eva looks up the model table in `pipeline-operations.md`. There is no discretion.

**Fixed-model agents:**

| Agent | Model | Rationale |
|-------|-------|-----------|
| Roz | Opus | QA judgment is non-negotiable |
| Robert (subagent) | Opus | Product acceptance requires strong reasoning |
| Sable (subagent) | Opus | UX acceptance requires strong reasoning |
| Poirot | Opus | Blind review with no context requires strongest reasoning |
| Distillator | Haiku | Mechanical compression, no judgment needed |
| Ellis | Sonnet | Read diff, write message, run git -- zero ambiguity |

**Size-dependent agents:**

| Agent | Small | Medium | Large |
|-------|-------|--------|-------|
| Cal | (skipped) | Opus | Opus |
| Colby | Sonnet | Sonnet | Opus |
| Agatha | Per doc type | Per doc type | Per doc type |

Agatha uses Haiku for reference docs (API, config, changelogs) and Sonnet for conceptual docs (architecture guides, tutorials).

**Enforcement rules:**
- Ambiguous sizing defaults UP (Opus until confirmed)
- Sizing changes propagate immediately to subsequent invocations
- Explicit model parameter required in every Agent tool invocation

### State Management

Eva maintains five files in `docs/pipeline/`:

| File | Purpose | Reset Behavior |
|------|---------|----------------|
| `pipeline-state.md` | Unit-by-unit progress tracker. Updated after each phase transition. Enables session recovery. Every update includes a "Changes since last state" section: new files created, files modified, requirements closed, and the agent that produced the change. This makes transitions auditable and prevents silent drift. | Never reset automatically |
| `context-brief.md` | Conversational decisions, corrections, user preferences, rejected alternatives. | Reset at start of each new feature pipeline |
| `error-patterns.md` | Post-pipeline error log categorized by type. Recurrence tracking for WARN injection. | Append-only |
| `investigation-ledger.md` | Debug hypothesis tracking. Records each theory, layer, evidence, outcome. | Reset at start of each new investigation |
| `last-qa-report.md` | Roz's most recent QA report. Persisted so scoped re-runs can reference previous findings. | Overwritten on each Roz QA pass |

---

## Invocation Template System

All subagent invocations follow a standardized template:

```
TASK: [observed symptom -- what is happening, not why]
HYPOTHESES: [Eva's theory AND at least one alternative at a different system layer -- omit for non-debug]
READ: [files directly relevant to THIS work unit (prefer <= 6), always include retro-lessons.md]
CONTEXT: [one-line summary from context-brief.md if relevant, otherwise omit]
BRAIN: available | unavailable [agents with Brain Access sections use this flag]
WARN: [specific retro-lesson if pattern matches from error-patterns.md, otherwise omit]
CONSTRAINTS: [3-5 bullets -- what to do and what NOT to do]
OUTPUT: [what to produce, what format, where to write it -- must include DoR and DoD sections]
```

### Key Design Rules

- **Anti-framing rule:** TASK describes the observed symptom, not Eva's theory. Embedding a root cause theory in TASK anchors the subagent to Eva's framing (sycophancy risk). Theories go in HYPOTHESES.
- **READ budget:** Prefer <= 6 files. Always include `retro-lessons.md`. Pass context-brief excerpts in CONTEXT, not READ, to save file slots. Eva also includes `agent-preamble.md` in READ for all non-asymmetry agents, and `qa-checks.md` for Roz QA invocations.
- **DIFF section (Roz-specific):** Eva always runs `git diff --stat` and `git diff --name-only` and includes the output so Roz has a map of what changed.
- **DIFF section (Poirot-specific):** Eva pastes the raw `git diff` output. Nothing else. No spec, no ADR, no framing.
- **WARN injection:** When `error-patterns.md` shows a pattern recurring 3+ times, Eva adds a targeted warning to the relevant agent's invocation.
- **Delegation contract (mandatory):** Before every subagent invocation, Eva announces: "Invoking [Agent] with READ: [file1], [file2], ... and CONSTRAINTS: [constraint1], [constraint2], ..." Every file referenced in the DoR's requirement sources must appear in the READ list or be explicitly noted as omitted with a reason. Silent invocation -- dispatching an agent without announcing what it will read and what rules it must follow -- is a transparency violation.

The full invocation examples for each agent are in `.claude/references/invocation-templates.md`, loaded by Eva just-in-time when constructing prompts.

---

## DoR/DoD Framework

The Definition of Ready / Definition of Done framework in `.claude/references/dor-dod.md` replaces procedural checklists with structural output requirements.

### How It Works

- **DoR** (Definition of Ready) is the **first section** of every agent's output. It proves the agent read upstream artifacts by extracting specific requirements into a table with source citations.
- **DoD** (Definition of Done) is the **last section** of every agent's output. It proves coverage by mapping every DoR requirement to a status (Done or Deferred with explicit reason).
- Eva verifies both at phase transitions. Roz independently verifies Colby's DoD against actual code.

### Universal Conditions (every agent, every time)

1. Every DoR requirement has a status in DoD (Done or Deferred with explicit reason)
2. No silent drops -- missing = Deferred with reason, not absent
3. No TODO/FIXME/HACK in delivered output
4. Output template complete -- every section filled

### Roz's Special Role in DoD Enforcement

Roz does not trust self-reported coverage. Eva includes the requirements list in Roz's invocation, and Roz diffs requirements against actual implementation:

- Self-reported "Done" that doesn't match code = BLOCKER
- Requirements in the spec/ADR that Colby didn't even list in her DoR = BLOCKER (silent drop)
- Roz does not trust coverage tables -- she verifies them

### Shared Agent Preamble (`.claude/references/agent-preamble.md`)

Agent persona files reference a shared preamble for the five standard required actions (DoR, read upstream, retro lessons, brain context, DoD). Each agent keeps only its unique cognitive directive and domain-specific actions in its persona file. This eliminates ~100 lines of duplication across 9 agents while keeping critical behavioral instructions in the high-attention system prompt position.

### QA Check Procedures (`.claude/references/qa-checks.md`)

Roz's 18 QA checks (6 Tier 1 mechanical + 12 Tier 2 judgment) are extracted to a dedicated reference file. Roz's persona retains her investigation mode, test authoring mode, and identity -- the procedural checklist loads on demand via Eva's invocation `<read>` tag. This reduces Roz's persona from 290 to 200 lines.

---

## Continuous QA Flow

The continuous QA model replaces the old batch model (Colby builds everything, then Roz reviews everything). Cal's ADR steps become work units, and each unit goes through its own build-test cycle.

### Pre-Build: Roz-First TDD

1. Eva invokes Roz in Test Authoring Mode for unit N's ADR step
2. Roz reads Cal's test spec, existing code, and the product spec
3. Roz writes test files with concrete assertions defining correct behavior
4. Tests are expected to fail -- they define the target state, not current behavior
5. Roz asserts what code SHOULD do (domain intent), not what it currently does

### Build + QA Interleaving

1. Eva invokes Colby for unit 1 with Roz's test files as the target
2. Colby runs Roz's tests first to confirm they fail for the right reason (missing implementation, not a test bug or environment issue). If a test passes before any implementation, Colby flags it.
3. Colby implements to make Roz's tests pass (may add edge-case tests, but NEVER modifies Roz's assertions)
4. When Colby finishes unit 1, Eva invokes **Roz** (full context) and **Poirot** (diff only) in PARALLEL
5. Eva triages findings from both agents, deduplicates, classifies severity
6. If Roz or Poirot flags issues, Eva queues fixes. Colby finishes current unit, then addresses fixes before starting the next unit
7. Eva updates `pipeline-state.md` after each unit transition

### Post-Build Pipeline Tail

7. Review juncture: Roz final sweep + Poirot + Robert-subagent + Sable-subagent (Large) in parallel
8. Eva triages all findings, routes fixes to Colby if needed, re-runs Roz
9. Agatha writes/updates docs against final verified code
10. Robert-subagent verifies Agatha's docs against spec
11. If DRIFT flagged: hard pause, human decides fix code or update living artifact
12. Ellis commits: code + docs + updated specs/UX in one atomic commit

### Non-Code Steps

ADR steps that produce no testable application code (schema DDL, agent instruction files, configuration, migration scripts) follow a different flow. Eva identifies these at the start of the build phase and handles them separately:

1. Roz test spec review and test authoring are skipped for those steps
2. Colby implements the non-code step
3. Roz reviews in verification mode -- checking ADR acceptance criteria are met, not running code QA checks
4. Agatha runs after Roz passes, sequentially (no parallel launch because there is no Roz test spec approval to gate it)

Mixed ADRs (some code steps, some non-code steps) are split: code steps follow the standard TDD flow above, non-code steps follow this flow. Both must pass before advancing to the review juncture and Ellis.

### Key Rules

- **Colby NEVER modifies Roz's test assertions.** If a test fails against existing code, the code has a bug -- Colby fixes the code.
- **Roz final sweep is mandatory** even after all units pass individual review, to catch cross-unit integration issues.
- **Pre-commit sweep:** Eva checks all Roz reports for unresolved MUST-FIX items. Zero open items required before Ellis.

### Feedback Loop Routing

| Trigger | Route |
|---------|-------|
| UAT feedback (UI tweaks) | Colby mockup fix -> Sable-subagent re-verify -> re-UAT |
| UAT feedback (spec change) | Robert -> Sable -> re-mockup -> Sable-subagent verify |
| Roz test spec gaps | Cal subagent (revise) -> Roz (re-review) |
| Roz code QA (minor) | Colby fix -> Roz scoped re-run |
| Roz code QA (structural) | Cal subagent (revise) -> Colby -> Roz full run |
| Robert-subagent spec DRIFT | Hard pause -> human decides -> Robert-skill updates spec OR Colby fixes code |
| Sable-subagent UX DRIFT | Hard pause -> human decides -> Sable-skill updates UX doc OR Colby fixes code |
| User reports a bug | Roz (investigate + diagnose) -> Hard pause (user approves approach) -> Colby (fix) -> Roz (verify) |

---

## Error Pattern Tracking and Retro Lessons

### Error Patterns (`docs/pipeline/error-patterns.md`)

After each pipeline completion (successful commit), Eva appends to this file with what Roz found, categorized as one of: `hallucinated-api`, `wrong-logic`, `pattern-drift`, `security-blindspot`, `over-engineering`, `stale-context`, `missing-state`, `test-gap`.

Each entry includes a `Recurrence count: N` field. Eva increments this when the same category pattern appears in a new pipeline run. At the start of each pipeline, Eva scans for entries with count >= 3 and notes which agents need WARN injection.

### Retro Lessons (`.claude/references/retro-lessons.md`)

Systemic lessons (not one-off bugs) are captured in this file using a standard format:

- **What happened** -- the symptom
- **Root cause** -- why it happened
- **Rules derived** -- per-agent rules to prevent recurrence

### Dual-Write Pattern

When a pipeline reveals a systemic lesson, Eva writes it to two places:

1. **Always:** Append to `retro-lessons.md` (git-trackable, works without brain)
2. **If brain is available:** Also call `agent_capture` with `thought_type: 'lesson'`, `source_agent: 'eva'`, `source_phase: 'retro'`

This ensures lessons are both version-controlled and brain-searchable. Agents search the brain first (if available) for relevant retro lessons, then also read the markdown file as a fallback.

### Cross-Layer Wiring Enforcement

A recurring pattern where Colby built strong backends but forgot to wire frontend consumers led to four structural safeguards (v3.3.0):

1. **Cal: Vertical slice design.** ADR steps must include both producer (API/store) and consumer (UI/caller) in the same step. A new Hard Gate (#4) rejects plans with orphan producers. A Wiring Coverage section maps every endpoint to its consumer.
2. **Colby: Contract artifacts.** DoD includes Contracts Produced and Contracts Consumed tables documenting exact response shapes. Eva injects prior step's contracts into downstream invocations.
3. **Roz: Wiring verification (QA check #18).** Greps for orphan endpoints (backend routes nothing calls) and phantom calls (frontend calling non-existent endpoints). Blocker severity.
4. **Poirot: Cross-layer check.** Flags API endpoints in the diff that nothing calls, frontend calls to missing endpoints, and type mismatches between response shapes and UI expectations.

Root cause analysis and external research (CleanAim, APImatic, Addy Osmani) documented in retro lesson #005. A FE/BE Colby split (separate frontend and backend agents) is held in reserve if the pattern persists.

The same dual-write pattern applies to context brief entries. Eva always writes to `context-brief.md` and, when brain is available, also captures the entry to the brain with the appropriate `thought_type` (`preference`, `correction`, or `rejection`). See [Team Collaboration Internals](#team-collaboration-internals) for the classification table and capture parameters.

---

## Brain Architecture

### Overview

The Atelier Brain is an MCP server (`brain/server.mjs`) backed by PostgreSQL with pgvector and ltree extensions. It provides persistent institutional memory that survives across sessions. The pipeline works without it, but with it, session 12 of a feature build has the same context as session 1.

### Startup

The brain server is launched via `brain/start.sh`, a shell wrapper that installs `node_modules` (if missing) before starting the Node.js server. This solves a first-session timing issue where the project `.mcp.json` would spawn the server before the `SessionStart` hook had a chance to run `npm install`. The wrapper makes the server self-bootstrapping regardless of hook execution order.

### MCP Transport and Project Registration

The plugin's `.mcp.json` supports HTTP transport only. The brain server uses stdio transport, which requires registration in the project-level `.mcp.json` with absolute paths (tilde `~` does not expand in `.mcp.json`). The `/brain-setup` skill handles this automatically: it locates the plugin install path, resolves absolute paths, and adds an `atelier-brain` entry to the project's `.mcp.json` using `sh` as the command with `start.sh` as the argument. Environment variables for config paths, database credentials, and the OpenRouter API key are passed through the `env` block. Existing entries in the project `.mcp.json` are preserved during this merge.

### Database Schema

**Required extensions:** `vector` (pgvector), `ltree`

**Core tables:**

| Table | Purpose |
|-------|---------|
| `thoughts` | Core knowledge store. Each row is a thought with content, embedding (1536-dimensional vector), metadata, type, source agent/phase, importance score, status, scope, `captured_by` (human attribution), and timestamps. |
| `thought_relations` | Typed edges between thoughts. Convention: `source_id` = newer/derived thought, `target_id` = older/original thought. |
| `thought_type_config` | Lookup table for TTL and default importance per thought type. |
| `brain_config` | Singleton configuration row controlling conflict detection thresholds, consolidation settings, and default scope. |

**Thought types (enum):**

| Type | Default TTL | Default Importance | Description |
|------|-------------|-------------------|-------------|
| `decision` | Never expires | 0.9 | Architectural or product decisions |
| `preference` | Never expires | 1.0 | Human preferences and HALT resolutions |
| `lesson` | 365 days | 0.7 | Retro learnings and patterns |
| `rejection` | 180 days | 0.5 | Alternatives considered and discarded |
| `drift` | 90 days | 0.8 | Spec/UX drift findings |
| `correction` | 90 days | 0.7 | Fixes applied after drift detection |
| `insight` | 180 days | 0.6 | Mid-task discoveries |
| `reflection` | Never expires | 0.85 | Consolidation-generated synthesis |
| `handoff` | Never expires | 0.9 | Structured handoff briefs for team collaboration |

**Source phases (enum):** `design`, `build`, `qa`, `review`, `reconciliation`, `setup`, `handoff`

**Relation types (enum):** `supersedes`, `triggered_by`, `evolves_from`, `contradicts`, `supports`, `synthesized_from`

### MCP Tools

The brain exposes 6 tools via MCP:

| Tool | Purpose | Key Parameters |
|------|---------|---------------|
| `agent_capture` | Store a thought with schema-enforced metadata, dedup, conflict detection, and auto-supersession. Human attribution (`captured_by`) is resolved automatically from git config or `ATELIER_BRAIN_USER` env var. | `content`, `thought_type`, `source_agent`, `source_phase`, `importance` (0-1), optional `supersedes_id`, `scope`, `metadata` |
| `agent_search` | Semantic search using three-axis scoring. Updates `last_accessed_at` on returned results. | `query`, `threshold` (default 0.2), `limit` (default 10), `scope`, `include_invalidated`, `filter` |
| `atelier_browse` | Paginated browse by type or status. | Type/status filter, pagination |
| `atelier_stats` | Brain health check. Returns thought count, config, status, and `brain_name`. | None |
| `atelier_relation` | Create typed edges between thoughts. | `source_id`, `target_id`, `relation_type`, `context` |
| `atelier_trace` | Walk relation chains from a thought. Recursive traversal. | Starting thought ID, direction |

### Three-Axis Scoring

The `match_thoughts_scored` PostgreSQL function ranks search results using three weighted factors:

```
score = (0.5 * recency_decay) + (2.0 * importance) + (3.0 * cosine_similarity)
```

- **Relevance (weight 3.0):** cosine similarity between query embedding and thought embedding. What you're asking about matters most.
- **Importance (weight 2.0):** the thought's importance score. Decisions outrank tactical findings.
- **Recency (weight 0.5):** exponential decay based on `last_accessed_at`. Tiebreaker only -- old decisions still surface.

Recency decay formula: `0.995 ^ hours_since_last_access`

The function's return type includes `captured_by`, so search results show who produced each thought.

### Write-Time Conflict Detection

When `agent_capture` receives a new `decision` or `preference` thought:

1. **Search** for similar active thoughts in overlapping scopes using the candidate threshold (default 0.7)
2. **Tier 1 -- Duplicate (>0.9 similarity):** Merge into existing thought. Update content if new importance is higher, merge metadata, bump `last_accessed_at`.
3. **Tier 2 -- Candidate (0.7-0.9 similarity):** If LLM classification is enabled, call GPT-4o-mini to classify as DUPLICATE, CONTRADICTION, COMPLEMENT, SUPERSESSION, or NOVEL.
   - DUPLICATE: merge
   - CONTRADICTION (same scope): auto-supersede (newest wins)
   - CONTRADICTION (cross-scope): mark both as `conflicted`, create `contradicts` relation
   - SUPERSESSION: auto-supersede, create `supersedes` relation
   - COMPLEMENT/NOVEL: store normally, record related ID
4. **Tier 3 -- Novel (<0.7 similarity):** Store normally with no conflict flag.

### TTL-Based Knowledge Decay

Each thought type has a configured TTL in `thought_type_config`. Thoughts past their TTL transition to `expired` status and are excluded from default searches (unless `include_invalidated` is set).

### Config Resolution

The brain server resolves its configuration using a priority chain:

1. **Project config** (`BRAIN_CONFIG_PROJECT` env var -> `.claude/brain-config.json`) -- shared team config
2. **Personal config** (`BRAIN_CONFIG_USER` env var -> `~/.claude/plugins/data/atelier-pipeline/brain-config.json`) -- local-only
3. **Environment variables** (`DATABASE_URL` or `ATELIER_BRAIN_DATABASE_URL`, `OPENROUTER_API_KEY`) -- fallback
4. **No config found** -- exit cleanly, brain disabled

Config files support `${ENV_VAR}` placeholders for secrets. Shared configs never contain bare secret values.

The config file also supports an optional `brain_name` field -- a display name for the brain (e.g., "My Noodle", "Cortex"). When set, Eva uses this name in pipeline announcements and reports instead of the generic "Brain". The value flows through `atelier_stats` and `/api/health` responses as `brain_name`, defaulting to `"Brain"` when omitted.

### Hybrid Capture Model

Agents write their own domain-specific captures directly using their own `source_agent` name. Eva does NOT duplicate agent captures. Eva captures only cross-cutting concerns:

- User decisions and preferences (things no single agent owns)
- Phase transitions with outcome summaries
- Cross-agent pattern convergence (e.g., Roz and Robert both flag the same drift)
- Deploy/infra outcomes
- Poirot's findings (Poirot himself never touches brain)
- Context brief entries (preferences, corrections, rejected alternatives)
- Handoff briefs at pipeline end or on explicit handoff trigger
- Pipeline-end session summaries

Eva spot-checks that agents performed their brain captures but does not re-capture on their behalf.

---

## Team Collaboration Internals

### Human Attribution (`captured_by`)

Every thought stored in the brain includes a `captured_by` text column identifying who produced it. The server resolves this value at capture time using the following priority:

1. `ATELIER_BRAIN_USER` environment variable (if set)
2. Git config `user.name` (resolved via `git config user.name`)

The value is stored on the `thoughts` table and included in the return type of `match_thoughts_scored`, `atelier_browse`, and `atelier_stats`.

### Auto-Migration System

The brain server runs migrations automatically on startup. Each migration is an idempotent SQL file in `brain/migrations/`. The server checks whether a migration has already been applied by inspecting the schema state (column existence, enum value presence) and runs it only if needed.

**Migration files:**

| File | What It Does |
|------|-------------|
| `brain/migrations/001-add-captured-by.sql` | Adds the `captured_by TEXT` column to the `thoughts` table. Replaces the `match_thoughts_scored` function to include `captured_by` in the return type. |
| `brain/migrations/002-add-handoff-enums.sql` | Adds `'handoff'` to the `thought_type` and `source_phase` PostgreSQL enums. Inserts a `thought_type_config` row for `handoff` (NULL TTL, 0.9 importance). |

Migration 001 is triggered when the `captured_by` column does not exist on the `thoughts` table. Migration 002 is triggered when the `handoff` value is not present in the `thought_type` enum. Both use `IF NOT EXISTS` or equivalent idempotent patterns and are safe to run multiple times.

For fresh installs, `brain/schema.sql` is the canonical schema and already includes all columns, enum values, and config rows. Migrations exist solely for upgrading existing databases.

### Context Brief Dual-Write

Eva dual-writes context brief entries to the brain using the same pattern as retro lessons: always write to the file, also capture to brain if available.

When Eva appends an entry to `docs/pipeline/context-brief.md`, she also calls `agent_capture` with the entry classified by type:

| Context brief entry type | `thought_type` |
|--------------------------|---------------|
| User preference or constraint | `preference` |
| Mid-course correction | `correction` |
| Rejected alternative with reasoning | `rejection` |
| Cross-agent resolution | `preference` |

All captures use `source_agent: 'eva'`, the current pipeline phase as `source_phase`, and metadata tags including the feature name and `context-brief`. The importance value follows the `thought_type_config` defaults (preference: 1.0, correction: 0.7, rejection: 0.5).

If the `agent_capture` call fails (brain went down mid-pipeline), Eva continues without error. The file remains the source of truth for the current session. Brain capture is additive for cross-session and cross-teammate discovery.

### Handoff Brief Generation

Eva generates a structured handoff brief in two cases:

1. **Automatic** -- pipeline reaches the Final Report phase
2. **Explicit** -- user says "hand off," "someone else is picking this up," or equivalent

The handoff brief is captured as a single brain thought with:

- `thought_type: 'handoff'`
- `source_agent: 'eva'`
- `source_phase: 'handoff'`
- `importance: 0.9`
- Metadata tags: feature name, ADR reference, `handoff`

The `handoff` thought type has the same importance tier as `decision` (0.9) and never expires (NULL TTL), ensuring handoff briefs rank alongside architectural decisions in search results.

**Content structure:** Eva synthesizes the brief from the session's `context-brief.md`, `pipeline-state.md`, and any brain thoughts captured during the run. The brief contains six sections: completed work (with ADR step references), unfinished work, key decisions, surprises, user corrections, and warnings for the next developer.

**Skip conditions:** Eva does not generate a handoff brief when brain is unavailable, when the session produced zero ADR step completions and zero context brief entries, or when the user explicitly declines ("no handoff" / "skip handoff").

**Failure handling:** If `agent_capture` fails at pipeline end, Eva logs a warning ("Handoff brief not captured -- brain unavailable") and the Final Report renders normally. No pipeline disruption.

**Mid-pipeline handoff:** When triggered explicitly, Eva generates the brief from current state, captures it, announces "Handoff brief captured," and ends the pipeline without proceeding to Final Report.

### New Enum Values

Two enum values were added to support handoff briefs:

- `thought_type` enum: `'handoff'` (added after `'reflection'`)
- `source_phase` enum: `'handoff'` (added after `'setup'`)

The server's `THOUGHT_TYPES` and `SOURCE_PHASES` Zod validation arrays in `brain/server.mjs` include these values, allowing `agent_capture` to accept them without validation errors.

---

## Pipeline State Files and Session Recovery

### Recovery Mechanism

If Claude Code is closed mid-pipeline and reopened, Eva recovers by reading the state files:

1. **`pipeline-state.md`** tells Eva the current feature, phase, and unit-by-unit progress
2. **`context-brief.md`** restores conversational decisions and user preferences
3. **`error-patterns.md`** identifies recurring issues for WARN injection
4. **Existing artifacts on disk** (specs, ADRs, code changes) confirm what has been produced

Eva announces the recovery: "Resuming [feature] at [phase]. [N agents complete, M remaining.]"

### Stale Context Detection

If `context-brief.md` references a different feature than `pipeline-state.md`, Eva treats it as stale and resets it before proceeding.

### Context Hygiene

Eva manages context aggressively to prevent context window exhaustion:

| Context | Eva Carries | Subagents Carry |
|---------|------------|-----------------|
| `pipeline-state.md` | Always | Never (they get their unit scope) |
| `context-brief.md` | Summary only | Relevant excerpt in CONTEXT field |
| `CONVENTIONS.md` | Never | Only when writing code |
| `dor-dod.md` | Never | In their persona file |
| `retro-lessons.md` | Never | Always (included in every READ) |
| Feature spec | Never | Only if directly relevant |
| ADR | Never | Only the relevant step |

Between major phases, subagent sessions start fresh. Within Colby+Roz interleaving, each unit is a separate subagent invocation with fresh context. Eva never carries Roz reports in her context -- she reads the verdict (PASS/FAIL + blockers), not the full report.

### Context Cleanup Advisory

After each major phase crossing (Robert -> Sable, Cal -> Roz, review juncture -> Agatha), Eva checks estimated context usage. If the session has exceeded 10 major agent invocations, Eva suggests a fresh session: "This session has [N] agent handoffs. Consider starting a fresh session to clear context. Pipeline state is preserved in `docs/pipeline/pipeline-state.md` and `docs/pipeline/context-brief.md` -- I will resume exactly where we left off." This is advisory -- the user decides. Eva never forces a session break.

---

## Setup and Install System

### /pipeline-setup

The `pipeline-setup` skill is conversational. It:

1. **Gathers project information** one question at a time: tech stack, test framework, test commands, source structure, database patterns, build/deploy commands, coverage thresholds, complexity limits, and branching strategy.
2. **Reads template files** from `source/` in the plugin directory.
3. **Copies 35 files** to the target project (27 template files + 3 path-scoped rules + 4 enforcement hooks + 1 branching config), replacing placeholders with project-specific values. The branching strategy variant file is selected from `source/variants/` and installed as `.claude/rules/branch-lifecycle.md`.
4. **Customizes enforcement hooks** in `.claude/hooks/` -- sets project-specific paths and test commands in `enforcement-config.json`, registers hooks in `.claude/settings.json`, and makes scripts executable.
5. **Writes version marker** to `.claude/.atelier-version` for update detection.
6. **Updates `CLAUDE.md`** with a pipeline section.
7. **Offers brain setup** at the end.

Placeholder replacement:

| Placeholder | Example Value |
|-------------|---------------|
| `{test_command}` | `npm test` |
| `{lint_command}` | `npm run lint` |
| `{typecheck_command}` | `npm run typecheck` |
| `{fast_test_command}` | `npx vitest run` |
| `{source_dir}` | `src/` |
| `{features_dir}` | `src/features/` |
| `{architecture_dir}` | `docs/architecture/` |
| `{product_specs_dir}` | `docs/product/` |
| `{ux_docs_dir}` | `docs/ux/` |
| `{pipeline_state_dir}` | `docs/pipeline/` |
| `{changelog_file}` | `CHANGELOG.md` |
| `{conventions_file}` | `docs/CONVENTIONS.md` |
| `{mockup_route_prefix}` | `/mock/` |

### /brain-setup

The `brain-setup` skill handles two paths:

**Path A -- First-Time Setup:**
1. Personal or shared config
2. Database strategy: Docker, local PostgreSQL, or remote PostgreSQL
3. OpenRouter API key verification
4. Scope path configuration
5. Brain name (optional display name, defaults to "Brain")
6. Connection verification via `atelier_stats`
7. Config file written (personal to plugin data dir, shared to `.claude/brain-config.json`)
8. MCP server registered in project `.mcp.json` with absolute paths (stdio transport)
9. Brain enabled in database
10. Confirmation with tool count and scope

**Path B -- Colleague Onboarding:**
If `.claude/brain-config.json` already exists, the skill reads it, checks which environment variables are set, and either connects automatically or tells the colleague which variables to set. The skill also registers the MCP server in the colleague's project `.mcp.json` if the entry is missing. Non-interactive.

### /brain-hydrate

Seeds the brain with existing project knowledge:

1. **Scan** -- inventories ADRs, specs, UX docs, error patterns, retro lessons, context briefs, git history
2. **Present** -- shows scan results and estimated thought count, gets user approval
3. **Extract** -- reads each artifact, synthesizes reasoning (never verbatim content), captures as brain thoughts with proper types, importance scores, and relations
4. **Incremental** -- safe to re-run. Duplicate detection (>0.85 similarity = skip, 0.7-0.85 = new thought with `evolves_from` relation)
5. **Capped** -- maximum 100 thoughts per hydration run

---

## Branching Strategy Variants

### Variant System

The branching strategy feature uses a variant installation pattern. Four strategy-specific Markdown files exist in `source/variants/` in the plugin directory:

```
source/variants/
  branch-lifecycle-trunk-based.md
  branch-lifecycle-github-flow.md
  branch-lifecycle-gitlab-flow.md
  branch-lifecycle-gitflow.md
```

During `/pipeline-setup`, the user selects a strategy. The setup copies only the selected variant file to `.claude/rules/branch-lifecycle.md` in the target project. The other three variants are never installed. This means the installed rules contain only the lifecycle rules relevant to the project's chosen strategy -- agents never see conflicting instructions from other strategies.

All four variant files are path-scoped to `docs/pipeline/**`, which means they load automatically when Eva reads pipeline state at session start.

### Configuration File

The selected strategy is persisted in `.claude/pipeline-config.json`:

```json
{
  "branching_strategy": "trunk-based",
  "platform": "",
  "platform_cli": "",
  "mr_command": "",
  "merge_command": "",
  "environment_branches": [],
  "base_branch": "main",
  "integration_branch": "main"
}
```

| Field | Purpose |
|-------|---------|
| `branching_strategy` | Strategy identifier: `trunk-based`, `github-flow`, `gitlab-flow`, `gitflow` |
| `platform` | Detected platform: `github`, `gitlab`, or empty |
| `platform_cli` | CLI tool for MR operations: `gh`, `glab`, or empty |
| `mr_command` | Command to create merge requests (populated by setup) |
| `merge_command` | Command to merge (populated by setup) |
| `environment_branches` | GitLab Flow only: list of environment branch names (e.g., `["staging", "production"]`) |
| `base_branch` | Primary branch name (default: `main`) |
| `integration_branch` | Branch that receives feature work. Same as `base_branch` for most strategies; `develop` for GitFlow |

Eva reads this file during the session boot sequence. Colby reads it to determine branch naming conventions and merge targets. Ellis reads it to determine commit targets.

### Lightweight Reconfig

Users can change strategies without re-running full setup. Eva's reconfig procedure:

1. Reads `.claude/pipeline-config.json`
2. Confirms no active pipeline (blocks if one is running)
3. Asks the user for the new strategy
4. Rewrites `.claude/pipeline-config.json` with updated values
5. Installs the new variant file to `.claude/rules/branch-lifecycle.md`

Only these two files are modified during reconfig.

### Agent Responsibilities

| Agent | Branching Role |
|-------|---------------|
| **Colby** | Creates feature/hotfix/release branches. Creates merge requests via platform CLI. |
| **Ellis** | Commits to the current branch (feature branch or main, depending on strategy). Never pushes to main directly when using an MR-based strategy. |
| **Eva** | Reads strategy at boot. Cleans up branches after merge. Offers environment promotion (GitLab Flow). |

### Strategy-Specific Behaviors

**Trunk-Based Development.** No branch creation by default. Ellis pushes to main. Optional short-lived branches on user request.

**GitHub Flow.** Colby creates `feature/<name>` before building. Ellis commits to the feature branch. Colby creates a merge request after the review juncture. Hard pause before merge. Eva deletes the branch after merge.

**GitLab Flow.** Same as GitHub Flow, plus environment promotion. After MR merges to main, Eva offers promotion to staging, then production. Each promotion is a hard pause.

**GitFlow.** Feature branches branch from `develop`, not `main`. Release branches (`release/<version>`) are created from develop. Hotfix branches merge to both main and develop. Eva tags releases and back-merges to develop.

---

## Enforcement Hooks

### Overview

The enforcement hooks are shell scripts registered as Claude Code PreToolUse hooks. They run automatically on every tool invocation and mechanically enforce agent boundaries that persona instructions describe but cannot guarantee. Behavioral guidance tells agents what to do; hooks ensure they cannot do what they should not.

All three scripts require `jq` for JSON parsing. If `jq` is not installed, the hooks degrade gracefully (exit 0, allowing the action) rather than blocking all tool calls.

### The Three Hook Scripts

| Script | Hook Type | Trigger | Purpose |
|--------|-----------|---------|---------|
| `enforce-paths.sh` | PreToolUse | `Write\|Edit\|MultiEdit` | Blocks file writes outside each agent's allowed directory paths |
| `enforce-sequencing.sh` | PreToolUse | `Agent` | Blocks out-of-order agent invocations from the main thread |
| `enforce-git.sh` | PreToolUse | `Bash` | Blocks git write operations (`add`, `commit`, `push`, `reset`, `checkout --`, `restore`, `clean`) from the main thread |

### How Hooks Identify the Caller

Claude Code passes a JSON payload to each hook via stdin. Two fields identify who is calling:

- **`agent_type`** -- the subagent's frontmatter name (e.g., `colby`, `roz`, `ellis`, `cal`, `agatha`). Empty string for the main thread.
- **`agent_id`** -- a unique identifier for the subagent instance. Empty string for the main thread.

The hooks use these fields to apply agent-specific rules. For example, `enforce-paths.sh` checks `agent_type` against a case statement to determine which directories the caller can write to. `enforce-git.sh` and `enforce-sequencing.sh` only enforce from the main thread (where `agent_id` is empty), since subagents are already constrained by their `disallowedTools` frontmatter.

### File Path Enforcement (`enforce-paths.sh`)

This hook intercepts every Write, Edit, and MultiEdit call and checks the target file path against the calling agent's allowed directories.

| Agent | Allowed Write Paths | Blocked From |
|-------|---------------------|-------------|
| **Main thread** (Eva, Robert-skill, Sable-skill) | `docs/pipeline/`, `docs/product/`, `docs/ux/` | Source code, architecture docs, test files, config files |
| **Cal** | `docs/architecture/` (ADR directory) | Source code, pipeline state, other docs |
| **Colby** | Everything except paths in `colby_blocked_paths` | Docs, CI/CD configs, container files, infra paths (configurable -- see `enforcement-config.json`) |
| **Roz** | Test files (matched by config patterns) and `docs/pipeline/last-qa-report.md` | Production source code, documentation |
| **Ellis** | Full write access | Nothing (commit agent needs to stage all files) |
| **Agatha** (`agatha`) | `docs/` | Source code, config files |
| **All other agents** (Poirot, Distillator, Robert-subagent, Sable-subagent) | None (read-only) | Everything -- their `disallowedTools` already blocks writes, this is a safety net |

**The main thread limitation.** Eva, Robert-skill, and Sable-skill share the main Claude Code thread. The hook cannot distinguish between them because all three have an empty `agent_type`. The solution is to allow all three agents' write directories: `docs/pipeline/` (Eva), `docs/product/` (Robert-skill), and `docs/ux/` (Sable-skill). This is a pragmatic trade-off -- the alternative would be blocking legitimate writes from one of the three.

Test files are identified by patterns configured in `enforcement-config.json` (e.g., `.test.`, `.spec.`, `/tests/`, `/__tests__/`, `conftest`). These patterns are customized during `/pipeline-setup` to match the project's test file conventions.

### Pipeline Sequencing Enforcement (`enforce-sequencing.sh`)

This hook intercepts Agent tool calls from the main thread and enforces two mandatory gates by reading `docs/pipeline/pipeline-state.md`:

**Gate 1 -- Ellis requires Roz QA PASS (active pipelines only).** During an active pipeline (phase is `build`, `implement`, `review`, `qa`, `test-authoring`, etc.), Eva cannot invoke Ellis unless the `PIPELINE_STATUS` JSON marker in `pipeline-state.md` has `roz_qa` set to `"PASS"`. When no pipeline is active -- missing state file, missing `PIPELINE_STATUS` marker, or phase is `idle`/`complete` -- Ellis is allowed through for infrastructure, doc-only, and setup commits.

**Gate 2 -- Agatha blocked during build phase.** Eva cannot invoke Agatha (or `agatha`) while `pipeline-state.md` indicates the current phase is `build` or `implement`. Agatha writes docs after Roz's final sweep against verified code, not during active construction.

The hook only enforces from the main thread (empty `agent_id`). Subagents cannot invoke other subagents because the Agent tool is already in their `disallowedTools` list.

### Git Operation Guard (`enforce-git.sh`)

This hook intercepts Bash tool calls from the main thread and blocks git write operations: `git add`, `git commit`, `git push`, `git reset`, `git checkout --`, `git restore`, and `git clean`. Read-only git operations (`git status`, `git diff`, `git log`, `git branch`) are allowed.

Ellis, running as a subagent (non-empty `agent_id`), is not affected by this hook. This ensures that all code commits flow through Ellis, who applies Conventional Commits formatting and verifies QA status.

### Configuration (`enforcement-config.json`)

The configuration file lives at `.claude/hooks/enforcement-config.json` and is customized during `/pipeline-setup` with project-specific values:

```json
{
  "pipeline_state_dir": "docs/pipeline",
  "architecture_dir": "docs/architecture",
  "product_specs_dir": "docs/product",
  "ux_docs_dir": "docs/ux",
  "colby_blocked_paths": [
    "docs/", ".github/", ".gitlab-ci", ".circleci/",
    "Jenkinsfile", "Dockerfile", "docker-compose",
    ".gitlab/", "deploy/", "infra/", "terraform/",
    "pulumi/", "k8s/", "kubernetes/"
  ],
  "test_command": "npm test",
  "test_patterns": [
    ".test.", ".spec.", "/tests/", "/__tests__/",
    "/test_", "_test.", "conftest"
  ]
}
```

| Field | Used By | Purpose |
|-------|---------|---------|
| `pipeline_state_dir` | `enforce-paths.sh`, `enforce-sequencing.sh` | Main thread write boundary and pipeline state location |
| `architecture_dir` | `enforce-paths.sh` | Cal's write boundary |
| `product_specs_dir` | `enforce-paths.sh` | Robert-skill's write boundary (main thread) |
| `ux_docs_dir` | `enforce-paths.sh` | Sable-skill's write boundary (main thread) |
| `colby_blocked_paths` | `enforce-paths.sh` | Array of path prefixes Colby cannot write to. Default includes `docs/`, CI/CD paths, container files, and infra directories. Customized during `/pipeline-setup`. |
| `test_command` | Roz (QA verification) | Full test suite command (e.g., `npm test`, `pytest`). Used by Roz for QA verification. |
| `test_patterns` | `enforce-paths.sh` | Patterns identifying test files for Roz's write boundary |

### Hook Registration in `.claude/settings.json`

`/pipeline-setup` merges the hook registration into the project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-paths.sh"}]
      },
      {
        "matcher": "Agent",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-sequencing.sh"}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-git.sh"}]
      }
    ]
  }
}
```

Each matcher determines which tool invocations trigger the hook. The pipe-separated `Write|Edit|MultiEdit` matcher fires `enforce-paths.sh` on any file write operation. Existing settings in the file are preserved during the merge.

### Blocking vs. Non-Blocking

Hooks signal their result via exit code:

- **Exit 0** -- action allowed (or hook not applicable)
- **Exit 2** -- action blocked; the reason message on stderr is shown to the agent

All three PreToolUse hooks (`enforce-paths.sh`, `enforce-sequencing.sh`, `enforce-git.sh`) exit 2 on violations.

All three hooks exit 0 immediately when `jq` is not installed, when the config file is missing, or when the tool call is not one they care about. This ensures the hooks never interfere with unrelated tool usage or with projects that have not yet run `/pipeline-setup`.

---

## Customization Points

### CLAUDE.md Placeholders

During `/pipeline-setup`, the skill writes a pipeline section into `CLAUDE.md` with project-specific values. These values propagate to agent persona files through placeholder replacement. The key customization surface is the initial setup interview.

### What Is Stack-Agnostic

The orchestration patterns, quality gates, phase sizing, agent boundaries, and DoR/DoD framework are all stack-agnostic. They work identically regardless of whether the project uses React, Django, Rust, or any other stack.

### What Is Stack-Specific

- Test commands (lint, typecheck, test suite, single-file test)
- Source directory structure and feature directory patterns
- Database access patterns
- Build and deploy commands
- Coverage and complexity thresholds
- Mockup route prefix

### User Overrides During Pipeline

- "full ceremony" forces pauses at every transition
- "fast track this" forces Small sizing
- "stop" or "hold" halts auto-advance at current phase
- "skip to [agent]", "back to [agent]", "check with [agent]" for manual routing
- "skip mockup" to bypass UI mockup phase for non-UI features

### Brain Configuration

Brain behavior is controlled via the `brain_config` singleton row:

| Setting | Default | Purpose |
|---------|---------|---------|
| `brain_enabled` | `false` | Master switch |
| `consolidation_interval_minutes` | 30 | How often consolidation runs |
| `consolidation_min_thoughts` | 3 | Minimum thoughts needed to trigger consolidation |
| `consolidation_max_thoughts` | 20 | Maximum thoughts processed per consolidation run |
| `conflict_detection_enabled` | `true` | Enable write-time conflict detection |
| `conflict_duplicate_threshold` | 0.9 | Similarity above which thoughts are merged |
| `conflict_candidate_threshold` | 0.7 | Similarity above which LLM classifies the conflict |
| `conflict_llm_enabled` | `true` | Enable LLM-based conflict classification |
| `default_scope` | `default` | Default ltree scope for thoughts |

### Debug Flow Customization

The four-layer investigation protocol (Application -> Transport -> Infrastructure -> Environment) with its 2-rejected-hypotheses escalation threshold is fixed. The investigation ledger format and layer definitions are not configurable -- they encode hard-won lessons about where bugs actually live.

### Batch Mode

When Eva receives multiple issues at once:
- Default execution is sequential with full pipeline per issue
- Full test suite between issues
- Parallelization requires explicit user approval AND zero file overlap confirmation
- No silent reordering

### Worktree Integration

When agents work in isolated git worktrees:
- Changes integrate via `git merge` or `git cherry-pick`, never file copying
- Conflicts are resolved before advancing (route to Colby, then Roz)
- One worktree merge at a time with test suite between each
- Worktree agents do not see each other's changes

---

## Cross-References

- **User guide:** [docs/guide/user-guide.md](user-guide.md)
- **Agent system rules (installed):** `.claude/rules/agent-system.md`
- **Default persona (installed):** `.claude/rules/default-persona.md`
- **Quality framework (installed):** `.claude/references/dor-dod.md`
- **Operational procedures (installed):** `.claude/references/pipeline-operations.md`
- **Invocation templates (installed):** `.claude/references/invocation-templates.md`
- **Shared agent preamble (installed):** `.claude/references/agent-preamble.md`
- **QA check procedures (installed):** `.claude/references/qa-checks.md`
- **Branch/MR procedures (installed):** `.claude/references/branch-mr-mode.md`
- **Brain schema:** `brain/schema.sql` (in plugin directory)
- **Plugin metadata:** `.claude-plugin/plugin.json`
