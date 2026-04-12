# Atelier Pipeline -- Technical Reference

Version: 3.26.0

This document is the comprehensive technical reference for the atelier-pipeline plugin. It covers plugin architecture, agent system design, orchestration logic, brain infrastructure, and customization points. The pipeline runs on both Claude Code and Cursor with near-complete feature parity. For usage-oriented documentation, see [the user guide](user-guide.md).

---

## Platform Differences

| Feature | Claude Code | Cursor |
|---------|------------|--------|
| Agent Teams (parallel wave execution) | Yes (experimental) | Not available |
| Distributed routing (Agent spawning by Cal/Colby) | Yes | Not available |
| Telemetry hydration | Automatic (SessionStart) + manual | Automatic (SessionStart) + manual |
| Worktrees | Yes | Not available |
| Hook enforcement | Full (20 hooks) | Full (20 hooks) |
| Brain integration | Full | Full |
| All 14 agents | Full | Full |
| Installed file directory | `.claude/` | `.cursor/` |
| Rules file extension | `.md` | `.mdc` (with frontmatter) |
| Project env variable | `$CLAUDE_PROJECT_DIR` | `$CURSOR_PROJECT_DIR` |
| Plugin root env variable | `$CLAUDE_PLUGIN_ROOT` | `$CURSOR_PLUGIN_ROOT` |
| Project instructions file | `CLAUDE.md` | `AGENTS.md` |
| Settings file | `.claude/settings.json` | `.cursor/settings.json` |
| Plugin metadata location | `.claude-plugin/plugin.json` | `.cursor-plugin/plugin.json` |

Throughout this document, paths like `.claude/` refer to `.cursor/` on Cursor, and `$CLAUDE_PROJECT_DIR` refers to `$CURSOR_PROJECT_DIR` on Cursor, unless explicitly noted otherwise.

---

## Table of Contents

1. [Plugin Architecture](#plugin-architecture)
    - [Triple-Source Assembly Model](#triple-source-assembly-model)
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
    - [Enforcement Audit Trail](#enforcement-audit-trail)
    - [Adding a New Enforcement Hook](#adding-a-new-enforcement-hook)
18. [Sentinel Security Agent](#sentinel-security-agent)
19. [Agent Teams](#agent-teams)
20. [CI Watch](#ci-watch)
21. [Deps Agent](#deps-agent)
22. [Darwin Agent](#darwin-agent)
23. [Agent Telemetry](#agent-telemetry)
24. [Dashboard](#dashboard)
    - [REST Authentication](#rest-authentication)
25. [Telemetry Hydration](#telemetry-hydration)
26. [Agent Discovery](#agent-discovery)
27. [Observation Masking and Context Hygiene](#observation-masking-and-context-hygiene)
28. [Compaction API Integration](#compaction-api-integration)
29. [Customization Points](#customization-points)
30. [Pipeline Stop Reasons](#pipeline-stop-reasons)
31. [Token Budget Estimate Gate](#token-budget-estimate-gate)

---

## Plugin Architecture

Atelier Pipeline is a plugin for Claude Code and Cursor distributed via the plugin marketplace. It consists of two subsystems:

1. **Multi-agent orchestration** -- template files installed into the target project's `.claude/` (Claude Code) or `.cursor/` (Cursor) directory, plus `docs/pipeline/`. These define agent personas, slash commands, quality references, and state files.
2. **Atelier Brain** -- an MCP server (`brain/server.mjs`) that runs as a sidecar, providing persistent institutional memory backed by PostgreSQL and vector embeddings.

The plugin itself lives in the IDE's plugin directory. On Claude Code, this is typically `~/.claude/plugins/atelier-pipeline/`. Plugin metadata is in `.claude-plugin/plugin.json` (Claude Code) or `.cursor-plugin/plugin.json` (Cursor).

### Plugin-Level Files (stay in the plugin directory)

```
atelier-pipeline/                         # Plugin root (CLAUDE_PLUGIN_ROOT)
  .claude-plugin/
    plugin.json                           # Plugin metadata, hooks, version
  source/                                 # Template files -- copied to target project
    rules/
      default-persona.md
      agent-system.md
      pipeline-orchestration.md           # Path-scoped to docs/pipeline/**
      pipeline-models.md                  # Path-scoped to docs/pipeline/**
    agents/
      cal.md, colby.md, roz.md, robert.md,
      sable.md, investigator.md, distillator.md,
      ellis.md, agatha.md, sentinel.md, deps.md,
      darwin.md
    commands/
      pm.md, ux.md, architect.md, debug.md,
      pipeline.md, devops.md, docs.md, deps.md,
      telemetry-hydrate.md
    references/
      dor-dod.md, retro-lessons.md,
      invocation-templates.md, pipeline-operations.md,
      agent-preamble.md, qa-checks.md,
      branch-mr-mode.md, telemetry-metrics.md
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
      enforce-eva-paths.sh                # Main thread (Eva) path enforcement
      enforce-roz-paths.sh                # Per-agent: Roz path enforcement
      enforce-cal-paths.sh                # Per-agent: Cal path enforcement
      enforce-colby-paths.sh              # Per-agent: Colby path enforcement
      enforce-agatha-paths.sh             # Per-agent: Agatha path enforcement
      enforce-product-paths.sh            # Per-agent: Robert-spec path enforcement
      enforce-ux-paths.sh                 # Per-agent: Sable-ux path enforcement
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
    scripts/
      hydrate-telemetry.mjs               # Telemetry hydration (SessionStart + /telemetry-hydrate)
    ui/                                   # Dashboard + Settings UI
  skills/                                 # Plugin skills (run in main thread)
    pipeline-setup/SKILL.md               # /pipeline-setup
    pipeline-uninstall/SKILL.md           # /pipeline-uninstall
    brain-setup/SKILL.md                  # /brain-setup
    brain-uninstall/SKILL.md              # /brain-uninstall
    brain-hydrate/SKILL.md                # /brain-hydrate
    dashboard/SKILL.md                    # /dashboard
    telemetry-hydrate/SKILL.md            # /telemetry-hydrate (also source/commands/)
  scripts/
    check-updates.sh                      # SessionStart hook -- detects plugin updates
```

### Hooks

The plugin registers a `SessionStart` hook in `plugin.json` that runs three commands on every session start (both Claude Code and Cursor):

1. **Dependency install** -- runs `npm install` in the `brain/` directory if `node_modules` does not exist.
2. **Update check** -- runs `scripts/check-updates.sh` to compare the installed template version (`.claude/.atelier-version` or `.cursor/.atelier-version`) against the current plugin version. If they differ, it notifies the user that pipeline files may be outdated.
3. **Telemetry hydration** -- runs `brain/scripts/hydrate-telemetry.mjs` in `--silent` mode to capture per-agent telemetry from any new session JSONL files into the brain. Uses `$CLAUDE_PROJECT_DIR` (Claude Code) or `$CURSOR_PROJECT_DIR` (Cursor) to locate the project. Errors are suppressed (`2>/dev/null || true`) so hydration never blocks session startup.

### Triple-Source Assembly Model

Agent persona files, slash commands, rules, and references are assembled at install time from three source directories:

| Directory | Contains | YAML frontmatter? |
|-----------|----------|--------------------|
| `source/shared/` | Platform-agnostic content bodies (agent prose, command logic, reference text) | No |
| `source/claude/` | Claude Code frontmatter overlays (tool restrictions, hooks, model assignment) | Yes (pure YAML) |
| `source/cursor/` | Cursor frontmatter overlays (tool restrictions, model assignment -- no per-agent hooks field) | Yes (pure YAML) |

**How assembly works.** When you run `/pipeline-setup`, the skill reads each frontmatter overlay from the target platform directory (e.g., `source/claude/agents/cal.frontmatter.yml`), reads the corresponding shared content body (e.g., `source/shared/agents/cal.md`), and writes the combined output to the installed location (e.g., `.claude/agents/cal.md`). The frontmatter YAML becomes the file header; the shared content body becomes everything below the `---` separator.

**Concrete example:**

```
source/claude/agents/cal.frontmatter.yml   (YAML: name, model, tools, hooks, maxTurns)
  +
source/shared/agents/cal.md               (prose: identity, workflow, constraints, output)
  =
.claude/agents/cal.md                      (installed agent persona: frontmatter + content)
```

**Why three directories?** Agents share the same behavioral content (identity, constraints, workflow) across platforms, but each platform has different frontmatter fields. Claude Code agents declare `hooks:` for per-agent enforcement scripts; Cursor agents do not (Cursor uses a separate `hooks.json` model). Splitting the overlay from the content body avoids duplicating 14 agent files when only the frontmatter differs.

**Hooks are platform-specific.** Enforcement hook scripts live in `source/claude/hooks/` and `source/cursor/hooks/`, not in `source/shared/`, because hook implementations differ between platforms. Claude Code uses per-file shell scripts registered in frontmatter; Cursor uses a centralized `hooks.json` file.

**Important for contributors:** Editing files in `.claude/` (or `.cursor/`) directly is overwritten the next time `/pipeline-setup` runs. To make permanent changes, edit the source files in `source/shared/` (for content) or `source/claude/` / `source/cursor/` (for frontmatter), then re-run `/pipeline-setup` to install.

---

## File Tree -- What Lives Where

After running `/pipeline-setup`, 41 mandatory files are installed into the target project (plus optional agent files). The plugin templates remain in the plugin directory and are never modified. Files install into `.claude/` (Claude Code) or `.cursor/` (Cursor).

### Target Project (installed by /pipeline-setup)

```
your-project/
  .claude/ (or .cursor/)
    .atelier-version                      # Plugin version marker for update detection
    rules/                                # Always loaded by the IDE
      default-persona.md (.mdc on Cursor) # Eva orchestrator persona (identity)
      agent-system.md (.mdc on Cursor)    # Orchestration rules, routing (identity)
      pipeline-orchestration.md (.mdc)    # Mandatory gates, triage, wave execution (path-scoped: docs/pipeline/**)
      pipeline-models.md (.mdc)           # Model selection, Micro tier, complexity classifier (path-scoped: docs/pipeline/**)
      branch-lifecycle.md (.mdc)          # Branch lifecycle rules for selected strategy (path-scoped: docs/pipeline/**)
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
      telemetry-metrics.md                # Telemetry metric schemas, cost table, alert thresholds
    hooks/                                # Mechanical enforcement (PreToolUse + SubagentStop + PreCompact)
      enforce-eva-paths.sh                # Main thread (Eva) path enforcement -- docs/pipeline/ only
      enforce-{agent}-paths.sh            # Per-agent frontmatter hooks (roz, cal, colby, agatha, product, ux)
      enforce-sequencing.sh               # Blocks out-of-order agent invocations
      enforce-git.sh                      # Blocks git write ops from main thread
      session-hydrate.sh                  # Runs telemetry hydration at SessionStart
      pre-compact.sh                      # Writes compaction marker to pipeline-state.md before compaction
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

**Total: 41 mandatory files across 7 directories, plus the `.atelier-version` marker and an update to `CLAUDE.md` (Claude Code) or `AGENTS.md` (Cursor).** The `telemetry-metrics.md` reference file provides metric schemas, cost estimation tables, and degradation alert thresholds. Optional files: Sentinel persona (`sentinel.md`, Step 6a), Deps persona + command (`deps.md`, Step 6d).

### What Does NOT Live on Disk

- QA reports (returned by Roz, read by Eva, not persisted except `last-qa-report.md`)
- Robert-subagent and Sable-subagent acceptance reports (returned, triaged by Eva)
- Agent state or conversation history (subagent context windows are ephemeral)

---

## Loading Mechanics -- What Loads When

Both Claude Code and Cursor have specific loading behaviors for each directory under `.claude/` (or `.cursor/`):

| Directory | When Loaded | Loaded By | Scope |
|-----------|-------------|-----------|-------|
| `rules/` | **Every conversation**, automatically | IDE runtime | Global -- all messages see these files |
| `agents/` | When a subagent is invoked via the Agent tool | IDE Agent tool | Per-subagent -- only the invoked agent's file |
| `commands/` | When the user types a `/command` | IDE command system | Per-command -- only the triggered command's file |
| `references/` | On demand, when an agent reads them | Agents via `Read` tool | Per-read -- loaded just-in-time |
| `docs/pipeline/` | At session start by Eva, during pipeline | Eva via `Read` tool | Per-read |

**Critical implication:** `default-persona.md` (or `.mdc` on Cursor) and `agent-system.md` are always in context. This is why Eva is the default persona -- she is present in every conversation whether or not `/pipeline` is invoked. All other files are loaded only when needed, keeping context usage efficient.

**Eva's always-loaded context** consists of exactly three files: `default-persona.md`, `agent-system.md`, and `CLAUDE.md` (Claude Code) or `AGENTS.md` (Cursor). She does NOT pre-load `CONVENTIONS.md`, `dor-dod.md`, or `retro-lessons.md` -- those are subagent concerns.

### Path-Scoped Rules (Identity vs. Operations Split)

Eva's rules are split into two categories to stay under Anthropic's recommended ~200 lines per rules file:

**Identity files** (always-loaded via `rules/`):
- `default-persona.md` (`.mdc` on Cursor) -- who Eva is, what she never does, session boot sequence
- `agent-system.md` (`.mdc` on Cursor) -- architecture, agent tables, routing, sizing, invocation template

**Operations files** (path-scoped via YAML frontmatter):
- `pipeline-orchestration.md` (`.mdc` on Cursor) -- mandatory gates, brain capture model, wave execution, observation masking, investigation discipline, agent standards, review juncture, reconciliation. Uses just-in-time (JIT) section loading: sections marked `[ALWAYS]` load at pipeline activation; sections marked `[JIT]` load only when their trigger condition is met (e.g., investigation discipline loads only when a debug flow is entered). Eva reads section headers to know what exists without loading every section at activation.
- `pipeline-models.md` (`.mdc` on Cursor) -- universal scope classifier, size-dependent model tables, Agatha doc-type model, enforcement rules
- `branch-lifecycle.md` (`.mdc` on Cursor) -- branching strategy lifecycle rules (selected variant only: trunk-based, github-flow, gitlab-flow, or gitflow)

Operations files use a `paths: ["docs/pipeline/**"]` frontmatter declaration (or the Cursor equivalent `globs: ["docs/pipeline/**"]`). The IDE loads them automatically when any file matching that glob is read. Since Eva's boot sequence reads `docs/pipeline/pipeline-state.md` on every session with an active pipeline, the operational rules load exactly when needed.

**Why this matters:**
- **Compaction resilience.** Rules files are re-injected from disk after compaction on both Claude Code and Cursor. Content loaded via the Read tool gets summarized (potentially lossy). For mandatory gates and triage logic, lossy summarization is unacceptable.
- **Context efficiency.** Casual Eva (no active pipeline) carries only identity + routing (~350 lines). Active-pipeline Eva gets the full operational ruleset (~430 additional lines) loaded on demand.
- **Feature isolation.** New pipeline features (wave execution, triage matrix, model routing) land in the operations files, not the always-loaded identity files.

### XML Tag Structure (ADR-0006)

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

**Skills** run in the main IDE thread (Claude Code or Cursor). They are conversational, support back-and-forth with the user, and share the main context window. When Eva adopts a skill persona (e.g., Robert for `/pm`), she reads the command file and behaves as that agent within the main thread.

**Subagents** run in their own context windows via the IDE's Agent tool. They receive focused prompts, execute their task, and return results. Their context window is isolated -- they cannot see what other agents produced unless Eva includes it in their invocation prompt.

Some agents operate in both modes:
- **Robert**: skill mode for spec authoring (`/pm`), subagent mode for product acceptance review
- **Sable**: skill mode for UX design (`/ux`), subagent mode for mockup/implementation verification
- **Cal**: skill mode for conversational clarification (`/architect`), subagent mode for ADR production
- **Agatha**: skill mode for doc planning (`/docs`), subagent mode for doc writing

### Custom Commands Are Not Skills

The slash commands (`/pm`, `/ux`, `/docs`, `/architect`, `/debug`, `/pipeline`, `/devops`) are **custom agent persona commands**, not IDE skills. The `Skill` tool must not be invoked for them. When the user types one, Eva reads the corresponding `commands/*.md` file (from `.claude/commands/` or `.cursor/commands/`) and adopts that agent's persona. This distinction matters because skills use the `Skill` tool invocation path, while custom commands trigger persona adoption in the main thread.

The eight actual plugin skills (`/pipeline-setup`, `/pipeline-uninstall`, `/pipeline-overview`, `/brain-setup`, `/brain-uninstall`, `/brain-hydrate`, `/dashboard`, `/telemetry-hydrate`) live in the plugin's `skills/` directory and are invoked through the `Skill` tool.

---

## Agent Reference Table

Most agent persona files use `disallowedTools` (denylist) in their frontmatter. This ensures subagents inherit MCP tools (including brain tools) from the parent session -- a `tools` allowlist would block MCP tool inheritance because only explicitly listed tools would be available to the subagent.

**Cal and Colby are exceptions.** These two agents use an explicit `tools` allowlist instead of `disallowedTools`. Their allowlists include scoped `Agent(...)` access, which grants them the ability to spawn specific subagents directly without routing through Eva. Cal can spawn Roz for inline test spec review; Colby can spawn Roz for per-unit QA and Cal for architectural questions. The `Agent(specific)` syntax is enforced by the Claude Code runtime -- Cal cannot spawn Colby, and Colby cannot spawn Ellis. All 10 other agents retain `disallowedTools: Agent` and cannot spawn subagents at all.

| Agent | Role | Execution Mode | Tools | Write Access | Brain Access | Model |
|-------|------|---------------|-------|-------------|--------------|-------|
| **Eva** | Pipeline Orchestrator / DevOps | Main thread (always loaded) | Read, Glob, Grep, Bash, TaskCreate, TaskUpdate | `docs/pipeline/` state files ONLY | Reads: `agent_search`, `atelier_stats`. Writes: cross-cutting decisions, phase transitions, Poirot findings. | N/A (orchestrator) |
| **Robert** (skill) | CPO -- spec authoring | Main thread (`/pm`) | Full conversational | Spec files | Reads: prior specs, corrections. Writes: spec rationale, corrections. | N/A (skill) |
| **Robert** (subagent) | Product acceptance reviewer | Subagent | Read, Glob, Grep, Bash | **None** (read-only) | Reads: spec evolution, prior drift. Writes: drift findings, pass verdicts. | Sonnet base; Opus on Large (classifier +2) |
| **Sable** (skill) | UX Designer -- doc authoring | Main thread (`/ux`) | Full conversational | UX docs | Reads: prior UX decisions, a11y. Writes: UX rationale, corrections. | N/A (skill) |
| **Sable** (subagent) | UX acceptance reviewer | Subagent | Read, Glob, Grep, Bash | **None** (read-only) | Reads: UX doc evolution. Writes: drift/missing verdicts, five-state audit. | Sonnet base; Opus on Large (classifier +2) |
| **Cal** (skill) | Architect -- conversational | Main thread (`/architect`) | Full conversational | None during conversation | Reads: prior decisions, constraints. | N/A (skill) |
| **Cal** (subagent) | Architect -- ADR production | Subagent | Read, Write, Edit, Glob, Grep, Bash, Agent(roz) | ADR files | Reads: prior decisions, rejected approaches. Writes: mechanical via brain-extractor (decisions, rejections, insights). | Opus (Medium/Large) |
| **Colby** | Senior Software Engineer | Subagent | Read, Write, Edit, MultiEdit, Glob, Grep, Bash, Agent(roz, cal) | Source files, test files | Reads: implementation patterns, gotchas. Writes: mechanical via brain-extractor (implementation insights, workarounds). | Haiku (Micro), Sonnet (Small/Medium), Opus (Large) |
| **Roz** | QA Engineer | Subagent | Read, Write, Glob, Grep, Bash | **Test files ONLY** | Reads: QA patterns, fragile areas. Writes: mechanical via brain-extractor (recurring patterns, investigation findings, doc impact). | Sonnet base; classifier promotes to Opus (+2 full sweep, -1 scoped rerun) |
| **Poirot** | Blind Code Investigator | Subagent | Read, Glob, Grep, Bash | **None** (read-only) | **None** -- Poirot never touches brain. Eva captures his findings. | Sonnet base; Opus at final review juncture (classifier +2) |
| **Agatha** (skill) | Documentation -- planning | Main thread (`/docs`) | Full conversational | None during planning | N/A | N/A (skill) |
| **Agatha** (subagent) | Documentation -- writing | Subagent | Read, Write, Edit, MultiEdit, Grep, Glob, Bash | Documentation files | Reads: prior doc reasoning, drift patterns. Writes: mechanical via brain-extractor (doc update reasoning, gap findings). | Haiku (reference docs), Sonnet (conceptual docs) |
| **brain-extractor** | Mechanical brain capture extractor | SubagentStop hook (Haiku) | `agent_capture` (brain MCP only) | **None** | **Writes only** -- two-pass extraction per completion: (1) decisions/patterns/lessons/seeds; (2) structured quality signals per agent type (`metadata.quality_signals`). Never reads files. | Haiku (fixed) |
| **Ellis** | Commit and Changelog Manager | Subagent | Read, Write, Edit, Glob, Grep, Bash | Git operations, changelog | N/A | Haiku (fixed) |
| **Distillator** | Lossless Compression Engine | Subagent | Read, Glob, Grep, Bash | **None** (read-only, output returned to Eva) | **None** | Haiku (fixed; classifier exempt) |
| **Sentinel** | Security Audit (opt-in) | Subagent | Read, Glob, Grep, Bash + Semgrep MCP (`semgrep_scan`, `semgrep_findings`) | **None** (read-only) | **None** -- Eva captures findings post-review. | Sonnet base; Opus when auth/security files change (classifier +2) |
| **Deps** | Dependency Management (opt-in) | Subagent | Read, Glob, Grep, Bash (read-only), WebSearch, WebFetch | **None** (read-only) | Reads: prior dependency decisions. Writes: scan results, upgrade risk assessments. | Sonnet (fixed) |
| **Darwin** | Self-Evolving Pipeline Engine (opt-in) | Subagent | Read, Glob, Grep, Bash (read-only) | **None** (read-only) | Reads: Tier 3 telemetry, prior Darwin proposals, error patterns. Eva captures proposals post-review. | Opus (fixed -- cross-metric analysis) |

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
| **Sentinel** | Read spec/ADR/UX docs. Write/Edit anything. Report findings from unchanged code (must filter to diff only). Classify pre-existing issues as new findings. Touch brain directly (Eva captures findings). |
| **Deps** | Write/Edit/MultiEdit any file. Run `npm install`, `pip install`, `cargo update`, `go get`, or any command that modifies dependency files. Classify uncertain upgrades as "Safe to Upgrade" (must use "Needs Review"). |
| **Darwin** | Write/Edit/MultiEdit any file. Implement proposals directly (Colby implements). Touch the brain directly (Eva captures proposals). Auto-approve proposals without user review. Reuse a `darwin_proposal_id` that already exists in the brain (each proposal is unique). |
| **Ellis** | Commit without QA passing. Use generic commit messages. Commit without user approval. Use `git add -A` or `git add .`. |

### Cal: ADR Production Requirements

Every ADR Cal produces must include these sections:

**Anti-goals.** Cal lists exactly three things the design will NOT address, with reasoning and a "revisit when" condition. If Cal cannot name three anti-goals, the scope is either trivially small or dangerously unbounded. Eva uses this section to prevent scope creep during implementation.

**SPOF identification.** After identifying the riskiest assumption in the spec, Cal identifies the single point of failure in the proposed design: the one component whose failure would cascade. The output states the failure mode and how the system degrades gracefully with reduced capability. If no graceful degradation path exists, Cal flags it in Consequences -- this is a finding, not something to omit.

**Migration and rollback.** For changes that affect database schema, shared state, or cross-service contracts, Cal includes: (a) a migration plan with ordered steps including data backfill if applicable; (b) a single-step rollback strategy ("restore from backup" is not accepted); (c) a rollback window stating how long after deployment the rollback remains safe. Stateless changes (pure functions, UI components, config) skip this section.

**Telemetry per step.** Each ADR implementation step specifies what log line, metric, or event proves the step succeeded in production. Format: "Telemetry: [what]. Trigger: [when emitted]. Absence means: [failure mode]." Purely structural steps (file moves, renames) may omit this.

### Colby: Build Mode Requirements

**Retrieval-led reasoning.** Colby reads actual project files before writing implementation. She never assumes code structure from the ADR alone, never guesses at function signatures, and does not rely on training-data patterns when the local codebase has an established convention. CLAUDE.md and the local project are primary sources; training data is a fallback.

**Failing test first.** Before implementing any ADR step, Colby runs Roz's pre-written tests to confirm they fail for the right reason. A test that passes before any implementation is flagged -- either the test is wrong or the feature already exists.

**Minimal implementation.** Colby implements the minimum code necessary to pass the current failing test. Helper functions, utility abstractions, and convenience wrappers not required by the ADR step or failing test are noted in the DoD under "Implementation decisions not in the ADR" -- not built.

### Agent Persona Frontmatter Fields

Every agent persona file declares four standard fields in its YAML frontmatter. These fields drive mechanical behavior in the Claude Code runtime and in Eva's orchestration logic.

| Field | Type | Purpose |
|-------|------|---------|
| `model` | string alias (`opus`, `sonnet`, `haiku`) | Base model for this agent. Eva overrides at invocation time using the classifier from `pipeline-models.md`. The frontmatter value is the default; the classifier result is authoritative. |
| `effort` | string (`low`, `medium`, `high`) | Signals expected work intensity. Used by the runtime for resource hints. |
| `maxTurns` | integer | Maximum conversation turns before the subagent is forced to return. Prevents runaway agents. |
| `color` | string (CSS color name) | Terminal color for agent output display. Present on 6 core agents (Cal, Colby, Roz, Ellis, Robert, Sable). Omitted on agents where visual distinction is less critical. |

**`model` vs `pipeline-models.md`:** The frontmatter `model` field is the base/default. Eva always runs the universal scope classifier from `pipeline-models.md` before every invocation and sets the model parameter explicitly in the Agent tool call. The classifier result can promote an agent from its base model to Opus. On Large pipelines, all agents run at Opus regardless of frontmatter. Eva is required to set the model parameter explicitly in every invocation -- omitting it is a violation even if the frontmatter declares a default.

**Distributed routing (Cal and Colby, Claude Code only):** Instead of `disallowedTools`, Cal and Colby declare an explicit `tools` allowlist with scoped `Agent(...)` entries. All other 10 agents use `disallowedTools: Agent` (or its equivalent denylist) and cannot spawn subagents. Distributed routing is available on Claude Code only. On Cursor, Eva routes all agent invocations centrally.

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
3b. Read branching strategy from `.claude/pipeline-config.json`. Announce strategy.
3c. Discover custom agents -- scan `.claude/agents/` (Claude Code) or `.cursor/agents/` (Cursor) for non-core persona files. Compare against core agent constant (cal, colby, roz, ellis, agatha, robert, sable, investigator, distillator). Announce discovered agents.
3d. Detect Agent Teams availability -- read `agent_teams_enabled` from config. If `true`, check `CLAUDE_AGENT_TEAMS` env var. Both must pass for `agent_teams_available: true`. On Cursor, Agent Teams is not available regardless of config.
4. Brain health check -- call `atelier_stats`. Two gates: tool available? returns `brain_enabled: true`? Both pass = `brain_available: true`
5. Brain context retrieval (if available) -- call `agent_search` with query from current feature area. Also search for seed thoughts matching current feature.
6. Announce session state to user (including brain status, custom agent count, Agent Teams status)

### Phase Sizing

Eva assesses scope at pipeline start and adjusts ceremony:

| Size | Criteria | Pipeline |
|------|----------|----------|
| **Micro** | ≤2 files, mechanical only (rename, typo, import fix, version bump), no behavioral change | Colby -> Roz test suite -> Ellis. Test failure auto-re-sizes to Small. |
| **Small** | Bug fix, single file, < 3 files, user says "quick fix" | Colby -> Roz wave QA -> (Agatha if Roz flags doc impact) -> (Robert-subagent verifies docs if Agatha ran) -> Ellis |
| **Medium** | 2-4 ADR steps, typical feature | Robert spec -> Cal -> Roz test authoring (per wave) -> [Colby units (lint+typecheck only) -> Roz wave QA + Poirot -> Ellis per-wave] -> Review juncture (Roz + Poirot + Robert-subagent) -> Agatha -> Robert-subagent (docs) -> Ellis final |
| **Large** | 5+ ADR steps, new system, multi-concern | Full pipeline including Sable mockup + Sable at final review juncture. Sentinel at review juncture. |

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
- Before first agent invocation on Large pipelines (token budget estimate gate -- always fires)
- Before first agent invocation on Medium pipelines when `token_budget_warning_threshold` is configured and the estimate exceeds it

### Mandatory Gates (12 gates, never skippable, same severity as Eva writing code)

1. Roz verifies every wave (not per unit -- individual units get lint+typecheck from Colby, not a Roz invocation)
2. Ellis commits (Eva never runs git on code). Ellis commits per wave after Roz QA PASS, plus a final commit at pipeline end
3. Full test suite between waves (Roz runs the suite at wave boundaries, not unit boundaries -- Eva running tests is the same class of violation as Eva writing code)
4. Roz investigates user-reported bugs (Eva does not)
5. Poirot blind-reviews every wave (cumulative wave diff only, parallel with Roz). When `sentinel_enabled: true`, Sentinel runs at the review juncture only -- not per wave.
6. Distillator compresses upstream artifacts when >5K tokens (within-session tool outputs use observation masking instead)
7. Robert-subagent reviews at review juncture (Medium/Large)
8. Sable-subagent verifies every mockup before UAT
9. Agatha writes docs after final Roz sweep, not during build
10. Spec/UX reconciliation is continuous (living artifacts updated in same commit)
11. One phase transition per turn on Medium/Large pipelines -- Eva announces, invokes, presents result, and stops. Phase bleed is the same class of violation as skipping Roz.
12. Loop-breaker: 3 consecutive failures on the same task = halt. Eva presents a Stuck Pipeline Analysis (what was attempted, what changed, why it is not converging). User decides: intervene, re-scope, or abandon.

### Model Selection

Model assignment is mechanical -- determined by the agent identity, pipeline sizing, and the universal scope classifier. Eva looks up the tables in `pipeline-models.md`. There is no discretion.

**Size-dependent agents (base models):**

| Agent | Micro | Small | Medium | Large |
|-------|-------|-------|--------|-------|
| Cal | (skipped) | (skipped) | Opus | Opus |
| Colby | Haiku | Sonnet | Sonnet | Opus |
| Ellis | Haiku | Haiku | Haiku | Haiku |
| Agatha | (skipped) | Per doc type | Per doc type | Per doc type |

Agatha uses Haiku for reference docs (API, config, changelogs) and Sonnet for conceptual docs (architecture guides, tutorials).

**Base-model agents (before classifier runs):**

| Agent | Base Model | Classifier override |
|-------|------------|---------------------|
| Roz | Sonnet | +2 full sweep, -1 scoped rerun |
| Poirot | Sonnet | +2 at final review juncture |
| Robert (subagent) | Sonnet | +2 on Large pipeline |
| Sable (subagent) | Sonnet | +2 on Large pipeline |
| Sentinel | Sonnet | +2 from universal auth/security signal |
| Distillator | Haiku | Classifier exempt -- always Haiku |

**Universal scope classifier** (applies to all non-exempt agents on Small/Medium pipelines; Large skips the classifier and runs every agent at Opus):

| Signal | Score |
|--------|-------|
| Wave/unit touches <= 2 files | +0 |
| Wave/unit touches 3-5 files | +1 |
| Wave/unit touches 6+ files | +2 |
| Task involves auth/security/crypto | +2 |
| Task involves state machine or complex flow | +2 |
| Task involves new module/service creation | +2 |
| Task is mechanical (rename, format, config) | -2 |
| Brain shows Sonnet failures on similar tasks for this agent | +3 |

Score >= 3 promotes to Opus. Score < 3 uses the base model. Agent-specific overrides are applied on top of the universal score.

**Enforcement rules:**
- Ambiguous sizing defaults UP (Opus until confirmed; all base-model agents treated as Large)
- Sizing changes propagate immediately to subsequent invocations
- Explicit model parameter required in every Agent tool invocation

### State Management

Eva maintains five files in `docs/pipeline/`:

| File | Purpose | Reset Behavior |
|------|---------|----------------|
| `pipeline-state.md` | Wave-level progress tracker. Updated after each wave completes (not after each unit -- unit progress is tracked in memory within a wave). Every update includes a "Changes since last state" section: new files created, files modified, requirements closed, and the agent that produced the change. If the session crashes mid-wave, recovery restarts from the wave boundary. | Never reset automatically |
| `context-brief.md` | Conversational decisions, corrections, user preferences, rejected alternatives. | Reset at start of each new feature pipeline |
| `error-patterns.md` | Post-pipeline error log categorized by type. Recurrence tracking for WARN injection. | Append-only |
| `investigation-ledger.md` | Debug hypothesis tracking. Records each theory, layer, evidence, outcome. | Reset at start of each new investigation |
| `last-qa-report.md` | Roz's most recent QA report. Persisted so scoped re-runs can reference previous findings. | Overwritten on each Roz QA pass |

### Stop Reason Field

Every terminal pipeline transition writes a `stop_reason` field to `pipeline-state.md` (both as a human-readable markdown field and inside the `PIPELINE_STATUS` JSON comment). The field is a closed enum -- Eva never invents values outside this list.

| Value | Trigger | Written by |
|-------|---------|------------|
| `completed_clean` | Ellis final commit and push succeeded | Eva at terminal transition |
| `completed_with_warnings` | Pipeline completed, but an Agatha divergence report or Robert/Sable DRIFT was accepted rather than fixed | Eva at terminal transition |
| `roz_blocked` | Roz returned a BLOCKER verdict and the user abandoned, or the loop-breaker gate (gate 12) fired and the user abandoned | Eva at terminal transition |
| `user_cancelled` | User explicitly said "stop", "cancel", or "abandon" during an active pipeline | Eva at terminal transition |
| `hook_violation` | A PreToolUse hook blocked an agent action that could not be retried, and the user abandoned | Eva at terminal transition |
| `budget_threshold_reached` | User declined to proceed after the token budget estimate gate (ADR-0029) | Eva at pre-pipeline sizing gate |
| `brain_unavailable` | Pipeline required the brain (e.g., Darwin auto-trigger) and the brain was down; user abandoned rather than continuing baseline | Eva at terminal transition |
| `scope_changed` | Cal discovered scope-changing information and the user chose to re-plan rather than continue | Eva at terminal transition |
| `session_crashed` | Inferred at next session boot when a stale pipeline (non-idle phase) has no `stop_reason` field | session-boot.sh at next boot; never written by Eva in real time |
| `legacy_unknown` | Read-only inference for pre-ADR-0028 pipelines that lack the field entirely | Read-only; never written by Eva |

**Upgrade safety:** Absent `stop_reason` reads as `legacy_unknown`. Pre-ADR-0028 pipelines do not crash.

**`legacy_unknown` is read-only.** It is an inference for pipelines that ran before the named stop reason taxonomy was introduced. Eva never writes this value -- it surfaces only when the field is missing from an older pipeline record.

**`session_crashed` is always retroactive.** Eva cannot write a stop reason during a crash. `session-boot.sh` detects stale pipelines (non-idle phase, no `stop_reason`) at the start of the next session and infers `session_crashed` in the boot state report.

**T3 telemetry inclusion:** The `stop_reason` field is included in the Tier 3 brain capture at pipeline end (as `metadata.stop_reason`), enabling Darwin to filter and pattern-match by outcome (`agent_search` with `filter: { stop_reason: 'roz_blocked' }`).

**Extension rule:** New stop reason values are added by a new ADR that supersedes the enum section. Eva never invents reasons at runtime.

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

The build phase is organized into waves. Each wave contains one or more ADR steps (work units) that are independent of each other. Ceremony is batched at wave boundaries rather than applied per unit -- this reduces total agent invocations on multi-step features while keeping quality gates intact.

### Pre-Build: Roz Test Authoring (per wave)

1. Eva batches ADR steps into waves based on independence (no shared files between units in the same wave)
2. Eva invokes Roz in Test Authoring Mode once for all units in the wave
3. Roz reads Cal's test specs, existing code, and the product spec for all units in the wave
4. Roz writes test files for every unit in the wave. Tests are expected to fail -- they define the target state, not current behavior
5. Roz asserts what code SHOULD do (domain intent), not what it currently does

### Build Phase (per unit within a wave)

1. Eva invokes Colby for each unit with Roz's test files as the target
2. Colby runs lint and typecheck only (not the full test suite) after each unit build -- fast mechanical checks, not a QA gate
3. Colby implements to make Roz's tests pass (may add edge-case tests, but NEVER modifies Roz's assertions)

### Wave QA (at wave boundary)

After all units in the wave are built:

4. Eva invokes **Roz** (full context, full test suite) and **Poirot** (cumulative wave diff only) in PARALLEL
5. Eva triages findings from both agents, deduplicates, classifies severity
6. If Roz or Poirot flags issues, Eva queues fixes to Colby. All fixes resolved before advancing to the next wave
7. Eva invokes **Ellis** for a per-wave commit after Roz QA PASS
8. Eva writes `pipeline-state.md` once per wave (not per unit)

### Post-Build Pipeline Tail

9. Review juncture: Roz final sweep + Poirot + Robert-subagent + Sable-subagent (Large) + Sentinel (if enabled) in parallel
10. Eva triages all findings, routes fixes to Colby if needed, re-runs Roz
11. Agatha writes/updates docs against final verified code
12. Robert-subagent verifies Agatha's docs against spec
13. If DRIFT flagged: hard pause, human decides fix code or update living artifact
14. Ellis final commit: code + docs + updated specs/UX in one atomic commit

### Non-Code Steps

ADR steps that produce no testable application code (schema DDL, agent instruction files, configuration, migration scripts) follow a different flow. Eva identifies these at wave-grouping time and handles them separately:

1. Roz test authoring is skipped for non-code steps in the wave
2. Colby implements the non-code steps
3. Roz reviews in verification mode at wave boundary -- checking ADR acceptance criteria are met, not running code QA checks
4. Agatha runs after Roz passes, sequentially (no parallel launch because there is no Roz test spec approval to gate it)

Mixed ADRs (some code steps, some non-code steps) are split across waves or handled within the same wave with separate Roz invocation modes. Both must pass before advancing to the review juncture and Ellis.

### Key Rules

- **Colby NEVER modifies Roz's test assertions.** If a test fails against existing code, the code has a bug -- Colby fixes the code.
- **Roz test authoring is batched per wave.** Roz authors tests for all units in the wave upfront, not one unit at a time.
- **Roz QA and Poirot run at wave boundaries.** Individual units get lint+typecheck from Colby (fast feedback), not a full Roz invocation.
- **Sentinel runs at the review juncture only.** Sentinel does not run per-wave alongside Roz and Poirot.
- **Ellis commits per wave.** Ellis commits after each wave's Roz QA PASS, then again at pipeline end for the full tail (docs, reconciliation).
- **State writes are batched per wave.** Eva writes `pipeline-state.md` once per wave, not after each unit. Unit progress is tracked in memory.
- **Brain prefetch is per wave.** Eva calls `agent_search` once at the start of each wave and injects results into all agent invocations within that wave. There is no per-invocation brain prefetch.
- **Roz final sweep is mandatory** at the review juncture, even after all waves pass, to catch cross-wave integration issues.
- **Pre-commit sweep:** Eva checks all Roz reports for unresolved MUST-FIX items. Zero open items required before Ellis final commit.

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

A recurring pattern where Colby built strong backends but forgot to wire frontend consumers led to four structural safeguards:

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

### HTTP Transport, CORS, and Server Robustness

The brain server implements a dual-transport architecture: stdio for MCP communication and HTTP for dashboard/REST API access.

**HTTP Server Behavior:**
- Listens on `http://localhost:PORT` (configured via `ATELIER_BRAIN_PORT`, default 8877)
- Routes:
  - `/ui` -- static HTML dashboard
  - `/api/health` -- server status and thought count
  - `/api/config`, `/api/config` (PUT) -- brain configuration
  - `/api/stats` -- telemetry statistics and agent fitness
  - `/api/telemetry/*` -- scoped agent and pipeline metrics
  - All other paths -- MCP request relay

**CORS Headers:** All HTTP responses include CORS headers to permit localhost tools to make cross-origin requests:
- `Access-Control-Allow-Origin: http://localhost:PORT` (localhost-only)
- `Access-Control-Allow-Headers: Content-Type, Authorization, mcp-session-id`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`

OPTIONS requests return 204 No Content for preflight handling.

**Process-Level Crash Guards (ADR-0034):**
The brain server installs handlers for all 6 process-level crash vectors to ensure it remains available for the full session duration:
1. `uncaughtException` -- logs and survives
2. `unhandledRejection` -- logs and survives
3. EPIPE on stdout (Claude Code disconnects) -- graceful shutdown
4. stderr errors -- swallowed silently (can't log to broken stderr)
5. stdin EOF (MCP SDK #1814 workaround) -- graceful shutdown
6. SIGHUP / SIGTERM / SIGINT -- graceful shutdown

Graceful shutdown stops timers, closes the DB pool with async drain, and enforces a 3-second deadman timeout (using `Promise.race()`) to prevent zombie processes if the pool stalls. See `brain/lib/crash-guards.mjs` for implementation details.

### Brain Server Modules

The brain server is composed of several hardened modules:

| Module | Purpose |
|--------|---------|
| `server.mjs` | Main entry point. HTTP server, MCP transport relay, startup orchestration. Installs crash guards. |
| `db.mjs` | PostgreSQL connection pool with explicit configuration (5 max connections, 5s timeout, 30s idle timeout). Auto-migration on startup. |
| `rest-api.mjs` | HTTP route handlers for dashboard settings UI and telemetry API endpoints. Authentication via `Authorization: Bearer {token}`. |
| `config.mjs` | Enums and Zod schemas for thought types, source agents, and source phases. Single source of truth for valid values. |
| `conflict.mjs` | Detects duplicate or conflicting thoughts at write time using semantic search + optional LLM classification. Uses `llm-response.mjs` for safe LLM response parsing. |
| `consolidation.mjs` | Periodic synthesis task: groups similar active thoughts and generates reflection summaries using OpenRouter API. Uses `llm-response.mjs` for safe parsing. |
| `llm-response.mjs` | Null-guard helper for safely extracting content from OpenRouter / OpenAI chat-completion responses. Prevents crashes on malformed responses. Exported `assertLlmContent(data, context)` validates response shape and throws named Error if invalid. |
| `ttl.mjs` | Periodic TTL enforcement: marks thoughts past their type's TTL as expired, excludes them from searches. |
| `crash-guards.mjs` | Process-level error handlers, graceful shutdown, deadman timeout logic. Injected into `server.mjs` for testability. |

**LLM Response Parsing Safety:**
Both `conflict.mjs` and `consolidation.mjs` use the `llm-response.mjs` module's `assertLlmContent()` function to safely extract synthesis results from OpenRouter responses. This ensures that malformed responses (null `data`, empty `choices` array, missing `message` or `content` field) throw a named Error with context and a truncated payload dump, rather than crashing the process with an unhandled TypeError.

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

Brain writes from Cal, Colby, Roz, Agatha, Robert, Robert-spec, Sable, Sable-ux, and Ellis are **mechanical**: when any of these nine agents completes, a `SubagentStop` `"type": "agent"` hook launches a lightweight Haiku extractor (`brain-extractor`). The extractor reads the parent agent's `last_assistant_message`, identifies decisions, patterns, lessons, and seeds worth preserving, and calls `agent_capture` using the correct `source_agent`, `thought_type`, `source_phase`, and `importance` values. No agent instruction is required -- the pipeline captures knowledge automatically on every completion.

**Agent-to-metadata mapping (extractor-assigned):**

| Agent | `source_agent` | `source_phase` |
|-------|----------------|----------------|
| Cal   | `cal`          | `design`       |
| Colby | `colby`        | `build`        |
| Roz   | `roz`          | `qa`           |
| Agatha | `agatha`      | `handoff`      |
| Robert | `robert`      | `product`      |
| Robert-spec | `robert-spec` | `product`  |
| Sable | `sable`        | `ux`           |
| Sable-ux | `sable-ux`  | `ux`           |
| Ellis | `ellis`        | `commit`       |

**Extractor behavior:**
- Captures only what the parent agent explicitly stated -- never fabricates
- Produces zero captures if no extractable content is present -- a valid outcome
- Exits cleanly when brain is unavailable -- never blocks the pipeline
- The extractor's own `SubagentStop` does not trigger another extractor (loop prevention via `if:` condition scope)

### Structured Quality Signal Extraction

After extracting decisions/patterns/lessons/seeds, the extractor performs a second best-effort pass to capture structured quality signals from the same `last_assistant_message`. Both passes run independently -- the second does not gate or replace the first.

Quality signal captures use `thought_type: 'insight'`, `source_phase: 'telemetry'`, `importance: 0.5`, and store parsed fields under `metadata.quality_signals`. The `metadata.quality_signals` key distinguishes these captures from Tier 1/Tier 3 telemetry (which use `metadata.telemetry_tier`). Darwin's telemetry queries filter by `metadata.telemetry_tier` and do not include quality signal captures.

**Per-agent parsing schema:**

| Agent | Fields extracted |
|-------|----------------|
| **Roz** | `verdict` (`PASS`/`FAIL` from verdict line near end of output); `blocker_count`, `must_fix_count`, `nit_count`, `suggestion_count` (from severity count patterns like "2 BLOCKERs", "MUST-FIX: 1"); `tests_before`, `tests_after`, `tests_broken` (from suite summary labels or pytest format: "X passed" → `tests_after`, "Y failed" → `tests_broken`) |
| **Colby** | `dod_present` (true when `## DoD` section header is present); `files_changed` (integer from "Files Changed" row in DoD table or summary line); `rework` (true when DoR or message contains phrases indicating this invocation is fixing a prior Roz FAIL: "fixing Roz", "addressing Roz", "FAIL verdict", "prior QA FAIL") |
| **Cal** | `step_count` (highest step number from "N steps" or "Step N" patterns); `test_spec_count` (count of distinct T-NNNN pattern references); `adr_revision` (integer from "Revision N" in DoR); `dor_present` (true when `## DoR` header present); `dod_present` (true when `## DoD` header present) |
| **Agatha** | `docs_written` (count of paths after "Written" in receipt format `Agatha: Written {paths}, updated {paths}`); `docs_updated` (count of paths after "updated"); `divergence_count` (count of data rows in `## Divergence Report` table, when the section is present) |

**Omission rule:** If a marker is absent from the output, the corresponding field is omitted from `quality_signals` entirely -- never set to null, never fabricated. If zero fields are parseable, no quality signal capture is emitted. Zero captures is a valid outcome.

Eva captures **cross-cutting concerns only** -- things no single agent owns. As of ADR-0025, user decisions, phase transitions, and context brief entries are captured mechanically by the hydrator (state-file parsing) rather than by Eva calling `agent_capture` directly. Eva still captures:

- Cross-agent pattern convergence (e.g., Roz and Robert both flag the same drift)
- Deploy/infra outcomes (in `/devops` mode)
- Poirot's findings (Poirot himself never touches brain)
- Handoff briefs at pipeline end or on explicit handoff trigger

Phase transitions and user decisions are captured by `hydrate-telemetry.mjs` at `SessionStart` via state-file parsing -- see [State-File Hydration](#state-file-hydration-evas-pipeline-decisions).

**Brain operations are batched per wave.** Eva calls `agent_search` once at the start of each wave (not per agent invocation) and injects the results into all invocations within that wave. Tier 1 telemetry is accumulated in-memory only during a wave (no per-invocation brain capture). Tier 2 is captured once per wave after Roz QA PASS. State writes to `pipeline-state.md` happen at wave boundaries, not unit boundaries.

---

## Team Collaboration Internals

### Human Attribution (`captured_by`)

Every thought stored in the brain includes a `captured_by` text column identifying who produced it. The server resolves this value at capture time using the following priority:

1. `ATELIER_BRAIN_USER` environment variable (if set)
2. Git config `user.name` (resolved via `git config user.name`)

The value is stored on the `thoughts` table and included in the return type of `match_thoughts_scored`, `atelier_browse`, and `atelier_stats`.

### Auto-Migration System

The brain server runs migrations automatically on every startup via the generic file-loop runner in `brain/lib/db.mjs`. The runner is idempotent and safe to run repeatedly.

#### Migration runner design

The `runMigrations()` function executes on startup:

1. **Creates the tracking table** if it does not exist: `schema_migrations` with columns `version TEXT PRIMARY KEY`, `applied_at TIMESTAMPTZ`, and `checksum TEXT`.
2. **Scans** `brain/migrations/*.sql` sorted alphabetically by filename.
3. **Checks** `schema_migrations` for each filename. If a row exists with that filename as `version`, the migration is skipped.
4. **Executes** new migration files in order, then records each in `schema_migrations` with the filename as `version` and a truncated SHA-256 hash of the file contents as `checksum`.

The checksum column is informational only -- the runner does not re-run a migration if its checksum changes. It only checks whether the `version` string (filename) is already present.

**Fail-soft behavior.** Each migration file is wrapped in its own try/catch. A failed migration logs an error but does not prevent subsequent migrations from running. This ensures a single broken migration does not block the entire startup sequence.

**Idempotency guarantee.** Every migration file uses idempotent SQL patterns: `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, `ADD VALUE IF NOT EXISTS` for enum extensions. A migration that is not idempotent is a blocker -- it would cause errors on re-runs.

**Fresh installs vs. upgrades.** For fresh databases, `brain/schema.sql` is the canonical schema and already includes all columns, enum values, and config rows. Migrations exist solely for upgrading existing databases that were created from an earlier version of the schema.

#### Migration files

| File | What It Does | ADR |
|------|-------------|-----|
| `001-add-captured-by.sql` | Adds `captured_by TEXT` column to `thoughts`. Replaces `match_thoughts_scored` to include `captured_by` in return type. | -- |
| `002-add-handoff-enums.sql` | Adds `'handoff'` to `thought_type` and `source_phase` enums. Inserts `thought_type_config` row for handoff. | ADR-0002 |
| `003-add-devops-phase.sql` | Adds `'devops'` to `source_phase` enum. | -- |
| `004-add-pattern-and-seed-types.sql` | Adds `'pattern'` and `'seed'` to `thought_type` enum. Inserts `thought_type_config` rows for each. | ADR-0004 |
| `005-add-telemetry-phases.sql` | Adds `'telemetry'` and `'ci-watch'` to `source_phase` enum. | ADR-0014, ADR-0013 |
| `006-add-pipeline-phase.sql` | Adds `'pipeline'` to `source_phase` enum. | -- |
| `007-beads-provenance-noop.sql` | No-op documentation file. Beads provenance uses existing `metadata` JSONB -- no schema change needed. | ADR-0026 |
| `008-extend-agent-and-phase-enums.sql` | Adds `sentinel`, `darwin`, `deps`, `brain-extractor`, `robert-spec`, `sable-ux` to `source_agent`. Adds `product`, `ux`, `commit` to `source_phase`. | ADR-0034 |
| `009-schema-migrations-table.sql` | Creates `schema_migrations` table. Backfills version rows for migrations 001-008 that were applied before tracking existed. | ADR-0034 |

#### Adding a new migration

1. **Pick the next sequence number.** Migration files are sorted lexicographically, so use a 3-digit zero-padded number (current highest: `009`, so next is `010`).
2. **Create the file** in `brain/migrations/` with the naming pattern `NNN-description.sql`.
3. **Write idempotent SQL.** Use `IF NOT EXISTS` guards for all DDL. Wrap DDL in a transaction where possible so partial failures roll back cleanly.
4. **No registration step needed.** The runner discovers files automatically at the next brain server startup.

To apply immediately without waiting for a restart, restart the brain server process. There is no separate migration CLI.

### State-File Hydration (Eva's Pipeline Decisions)

Eva writes `pipeline-state.md` and `context-brief.md` reliably because those files drive pipeline recovery. ADR-0025 converts those reliable file writes into brain captures without requiring any behavioral change from Eva: `hydrate-telemetry.mjs` parses these files at `SessionStart` and emits brain captures for every completed phase transition and user decision it finds.

**What is parsed:**

| File | Extracted items | Capture metadata |
|------|----------------|-----------------|
| `pipeline-state.md` | Each completed progress item (`- [x]` lines); feature name and sizing from `**Feature:**` and `**Sizing:**` fields | `thought_type: 'decision'`, `source_agent: 'eva'`, `source_phase: 'pipeline'`, `importance: 0.6`; metadata includes `feature`, `sizing`, `phase_item` |
| `context-brief.md` | Bullet items under the `## User Decisions` section | `thought_type: 'decision'`, `source_agent: 'eva'`, `source_phase: 'pipeline'`, `importance: 0.6`; metadata includes `section: 'user_decisions'` |

Duplicate detection uses a content hash keyed on `(feature + phase_item)` for pipeline-state items and on the decision text for context-brief items. State-file captures are idempotent -- re-running hydration never inserts duplicates.

This hydration runs at `SessionStart` via `session-hydrate.sh` with the `--state-dir` flag pointing to `docs/pipeline/`. It captures decisions from the previous session when a new session begins. All errors are caught and logged; the function never throws and always exits 0 (Retro #003).

The files remain the source of truth for in-session recovery. Brain capture is additive for cross-session and cross-teammate discovery.

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

1. **`pipeline-state.md`** tells Eva the current feature, phase, and wave-by-wave progress
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

Server-side compaction (Compaction API) manages Eva's context window automatically during long pipeline sessions. Eva no longer counts agent handoffs or estimates context usage percentage -- the Compaction API handles context management transparently.

Within a session, Eva uses **observation masking** as the primary context hygiene mechanism: superseded tool outputs are replaced with structured placeholders containing re-read commands. This is mechanical substitution, not intelligent compression. Distillator is reserved for structured document compression at phase boundaries. See the [Observation Masking and Context Hygiene](#observation-masking-and-context-hygiene) section for details.

Eva still suggests a fresh session when response quality visibly degrades (repetitive, contradictory, or missing obvious pipeline state) or when a pipeline spans multiple days. This is a quality-based signal, not a count. Pipeline state is preserved in `docs/pipeline/pipeline-state.md` and `docs/pipeline/context-brief.md` -- Eva resumes exactly where you left off. This is advisory -- Eva never forces a session break. The user decides.

Path-scoped rules (`pipeline-orchestration.md`, `pipeline-models.md`) survive compaction because Claude Code re-injects them from disk on every turn (ADR-0004 design). Mandatory gates and triage logic are always intact after compaction.

The PreCompact hook (`pre-compact.sh`) appends a timestamped `<!-- COMPACTION: ... -->` marker to `pipeline-state.md` before compaction fires. This marker is visible during debugging -- it signals that context was compacted between phase transitions. Brain captures provide a secondary recovery path -- decisions, findings, and lessons captured during the pipeline are queryable after compaction via `agent_search`.

---

## Setup and Install System

### /pipeline-setup

The `pipeline-setup` skill is conversational and works identically on Claude Code and Cursor. All files it installs are project-local (inside the project directory), committed to git, and shared with team members when they clone the repository. Nothing is written to `~/.claude/` (Claude Code) or `~/.cursor/` (Cursor) or other user-level locations. The plugin itself is user-level, but the project files it generates are project-level.

The skill:

1. **Gathers project information** one question at a time: tech stack, test framework, test commands, source structure, database patterns, build/deploy commands, coverage thresholds, complexity limits, and branching strategy.
2. **Reads template files** from `source/` in the plugin directory.
3. **Copies ~45 files** to the target project (28 template files + 3 path-scoped rules + 10 enforcement hooks + 1 branching config + 1 branching variant + settings + version marker), replacing placeholders with project-specific values. The branching strategy variant file is selected from `source/variants/` and installed as `.claude/rules/branch-lifecycle.md`. Optional: Sentinel persona (`sentinel.md`, Step 6a), Deps agent persona + command (`deps.md`, Step 6d).
4. **Customizes enforcement hooks** in the project's hooks directory (`.claude/hooks/` or `.cursor/hooks/`) -- sets project-specific paths and test commands in `enforcement-config.json`, registers hooks in the settings file (`.claude/settings.json` or `.cursor/settings.json`), and makes scripts executable. After copying and customizing, setup validates `enforcement-config.json` by checking that all required fields are present and non-empty: `pipeline_state_dir`, `architecture_dir`, `product_specs_dir`, `ux_docs_dir`, `test_command`, `test_patterns`. An absent or empty `lint_command` produces a note (not a blocker). Validation failure prints a warning but does not block installation.
5. **Writes version marker** to `.claude/.atelier-version` (Claude Code) or `.cursor/.atelier-version` (Cursor) for update detection.
6. **Updates `CLAUDE.md`** (Claude Code) or **`AGENTS.md`** (Cursor) with a pipeline section.
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

### /pipeline-uninstall

Removes all pipeline files installed by `/pipeline-setup`. The skill:

1. **Inventories** installed files against the core pipeline manifest (rules, agents, commands, references, hooks, state files, config, version marker)
2. **Separates** user-created custom agents (non-core `.md` files in `.claude/agents/`) -- these are never removed
3. **Presents** a full removal plan before touching any files
4. **Offers to back up** `retro-lessons.md` if it contains accumulated knowledge (copies to `docs/retro-lessons-backup.md`)
5. **Requires explicit confirmation** before proceeding
6. **Removes** files in order: hook registrations from `.claude/settings.json`, pipeline section from `CLAUDE.md`, core pipeline files, then empty directories
7. **Does not remove** the plugin itself (`claude plugin remove atelier-pipeline` is separate) or the Atelier Brain database

### /brain-uninstall

Removes or disconnects the Atelier Brain persistent memory layer. The skill:

1. **Detects** the brain config file (shared in `.claude/brain-config.json` or personal in `${CLAUDE_PLUGIN_DATA}/brain-config.json`) and infers the database strategy from the `database_url` field
2. **Offers two paths:**
   - **Disconnect only** -- removes the config file, leaves the database untouched
   - **Full uninstall** -- removes the config file and cleans up the database (Docker: stops container, optionally removes volume; Local PG: optionally drops database; Remote PG: optionally drops brain tables)
3. **Requires explicit confirmation** for every destructive database operation
4. **Handles unreachable databases** gracefully -- removes config and provides manual cleanup instructions
5. **Does not remove** the `brain/` directory (plugin code, not user data) or the plugin itself

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
  "integration_branch": "main",
  "sentinel_enabled": false,
  "agent_teams_enabled": false,
  "deps_agent_enabled": false,
  "darwin_enabled": false,
  "dashboard_mode": "none",
  "token_budget_warning_threshold": null
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
| `sentinel_enabled` | Enable Sentinel security agent. Set by `/pipeline-setup` Step 6a. Default: `false` |
| `agent_teams_enabled` | Enable Agent Teams parallel wave execution. Set by `/pipeline-setup` Step 6b. Default: `false` |
| `deps_agent_enabled` | Enable Deps dependency scan agent. Set by `/pipeline-setup` Step 6d. Default: `false` |
| `darwin_enabled` | Enable Darwin self-evolving pipeline engine. Requires brain. Set by `/pipeline-setup`. Default: `false` |
| `dashboard_mode` | Dashboard display mode. Default: `"none"`. |
| `token_budget_warning_threshold` | Type: `number \| null`. Units: USD. Default: `null`. When set to a number (e.g., `10.0`), Eva shows the pre-pipeline cost estimate and fires the budget gate on Medium pipelines when the estimate exceeds the threshold. When `null`, the estimate is shown on Large pipelines only with no threshold comparison. Upgrade-safe: absent key treated as `null`. |

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

The enforcement hooks are shell scripts registered as PreToolUse hooks on both Claude Code and Cursor. They run automatically on every tool invocation and mechanically enforce agent boundaries that persona instructions describe but cannot guarantee. Behavioral guidance tells agents what to do; hooks ensure they cannot do what they should not.

The PreToolUse scripts require `jq` for JSON parsing. If `jq` is not installed, the hooks degrade gracefully (exit 0, allowing the action) rather than blocking all tool calls.

### Hook Scripts

| Script | Hook Type | Trigger | Purpose |
|--------|-----------|---------|---------|
| `enforce-eva-paths.sh` | PreToolUse | `Write\|Edit\|MultiEdit` | Main thread (Eva): blocks writes outside docs/pipeline/ |
| `enforce-{agent}-paths.sh` | PreToolUse (frontmatter) | `Write\|Edit\|MultiEdit` | Per-agent hooks wired via frontmatter (roz, cal, colby, agatha, product, ux) |
| `enforce-sequencing.sh` | PreToolUse | `Agent` | Blocks out-of-order agent invocations from the main thread |
| `enforce-git.sh` | PreToolUse | `Bash` | Blocks git write operations (`add`, `commit`, `push`, `reset`, `checkout --`, `restore`, `clean`) and test commands from the main thread |
| `enforce-pipeline-activation.sh` | PreToolUse | `Agent` | Blocks Colby and Ellis invocations when no active pipeline exists |
| `session-hydrate.sh` | SessionStart | *(session start)* | Runs telemetry hydration (JSONL + state-file parsing) at session start |
| `log-agent-start.sh` | SubagentStart | *(all subagent starts)* | Logs agent start events to `.claude/telemetry/session-hooks.jsonl` |
| `log-agent-stop.sh` | SubagentStop | *(all subagent completions)* | Logs agent stop events to `.claude/telemetry/session-hooks.jsonl` |
| `pre-compact.sh` | PreCompact | *(compaction events)* | Writes a timestamped compaction marker to `pipeline-state.md` before context is compacted |
| `post-compact-reinject.sh` | PostCompact | *(after compaction)* | Re-injects `pipeline-state.md` and `context-brief.md` into post-compaction context |
| `log-stop-failure.sh` | StopFailure | *(agent API failures)* | Appends structured error entries to `error-patterns.md` when an agent turn fails |

### How Hooks Identify the Caller

The IDE (Claude Code or Cursor) passes a JSON payload to each hook via stdin. Two fields identify who is calling:

- **`agent_type`** -- the subagent's frontmatter name (e.g., `colby`, `roz`, `ellis`, `cal`, `agatha`). Empty string for the main thread.
- **`agent_id`** -- a unique identifier for the subagent instance. Empty string for the main thread.

The hooks use these fields to apply agent-specific rules. Per-agent path enforcement hooks are wired via frontmatter `hooks:` field (Layer 2) and fire only for that specific agent -- no `agent_type` check or case statement needed. Cross-cutting hooks (`enforce-git.sh`, `enforce-sequencing.sh`) enforce from the main thread (where `agent_id` is empty), since subagents are already constrained by their `disallowedTools` frontmatter and per-agent hooks.

### Three-Layer Enforcement Pyramid

Path enforcement uses a three-layer pyramid: Layer 1 (`tools`/`disallowedTools` in frontmatter), Layer 2 (per-agent frontmatter hooks), Layer 3 (global hooks in settings.json).

**Layer 2: Per-agent frontmatter hooks (Claude Code only)**

Each write-capable agent has a dedicated enforcement hook wired via the `hooks:` field in its frontmatter overlay. These scripts are self-contained (~15-20 lines), have no `agent_type` check or case statement, and enforce that agent's allowed write paths.

| Agent | Script | Allowed Write Paths |
|-------|--------|---------------------|
| **Eva** (main thread) | `enforce-eva-paths.sh` | `docs/pipeline/` only |
| **Cal** | `enforce-cal-paths.sh` | `docs/architecture/` only |
| **Colby** | `enforce-colby-paths.sh` | Everything except `colby_blocked_paths` from config |
| **Roz** | `enforce-roz-paths.sh` | Test files (matched by `test_patterns` from config) + `docs/pipeline/` |
| **Agatha** | `enforce-agatha-paths.sh` | `docs/` only |
| **Robert-spec** | `enforce-product-paths.sh` | `docs/product/` only |
| **Sable-ux** | `enforce-ux-paths.sh` | `docs/ux/` only |
| **Ellis** | *(none)* | Full write access (sequencing at Layer 3) |

Test files are identified by patterns configured in `enforcement-config.json` (e.g., `.test.`, `.spec.`, `/tests/`, `/__tests__/`, `conftest`). These patterns are customized during `/pipeline-setup` to match the project's test file conventions.

### Pipeline Sequencing Enforcement (`enforce-sequencing.sh`)

This hook intercepts Agent tool calls from the main thread and enforces three mandatory gates by reading `docs/pipeline/pipeline-state.md`:

**Gate 1 -- Ellis requires Roz QA PASS (active pipelines only).** During an active pipeline (phase is `build`, `implement`, `review`, `qa`, `test-authoring`, etc.), Eva cannot invoke Ellis unless the `PIPELINE_STATUS` JSON marker in `pipeline-state.md` has `roz_qa` set to `"PASS"`. When no pipeline is active -- missing state file, missing `PIPELINE_STATUS` marker, or phase is `idle`/`complete` -- Ellis is allowed through for infrastructure, doc-only, and setup commits.

**Gate 2 -- Agatha blocked during build phase.** Eva cannot invoke Agatha (or `agatha`) while `pipeline-state.md` indicates the current phase is `build` or `implement`. Agatha writes docs after Roz's final sweep against verified code, not during active construction.

**Gate 3 -- Ellis requires telemetry capture.** During an active non-Micro pipeline, Eva cannot invoke Ellis unless the `PIPELINE_STATUS` JSON marker has `telemetry_captured` set to `"true"`. Eva must capture T3 telemetry before committing to ensure quality metrics (rework rate, first-pass QA, EvoScore) are never lost. Exempt when `sizing` is `"micro"`, when `ci_watch_active` is `"true"` (CI Watch fix cycles have their own flow), or when `sizing` is absent (fail-open when pipeline size is unknown).

The hook only enforces from the main thread (empty `agent_id`). Most subagents cannot invoke other subagents because the Agent tool is in their `disallowedTools` list. Cal and Colby are the only exceptions on Claude Code: they use explicit `tools` allowlists that include scoped `Agent(...)` access. The `Agent(roz)` and `Agent(roz, cal)` grants are mechanically enforced by the Claude Code runtime, so Cal and Colby can only spawn the agents named in their allowlist -- they cannot invoke each other arbitrarily or reach Ellis, Poirot, or any other agent. On Cursor, distributed routing is not available, so Eva routes all agent invocations centrally. Eva's wave-level gates, phase transitions, and mandatory gates are unaffected by this difference.

### Git Operation Guard (`enforce-git.sh`)

This hook intercepts Bash tool calls from the main thread and blocks git write operations: `git add`, `git commit`, `git push`, `git reset`, `git checkout --`, `git restore`, and `git clean`. Read-only git operations (`git status`, `git diff`, `git log`, `git branch`) are allowed. The hook also blocks test suite execution from the main thread (`bats`, `pytest`, `jest`, `vitest`, `mocha`, `npm test`, etc.) -- Roz owns QA verification.

Ellis, running as a subagent (non-empty `agent_id`), is not affected by this hook. This ensures that all code commits flow through Ellis, who applies Conventional Commits formatting and verifies QA status.

**Performance optimization.** This hook has an `if` conditional in `settings.json`: `"if": "tool_input.command.includes('git ')"`. The IDE evaluates this expression before spawning the hook process, skipping the vast majority of Bash calls that contain no git commands. When the `if` condition passes, the full script runs and enforces both git and test command checks.

### Pipeline Activation Guard (`enforce-pipeline-activation.sh`)

This hook intercepts Agent tool calls from the main thread and blocks invocation of Colby or Ellis when no active pipeline exists. It ensures telemetry capture and quality gates are not bypassed by ad-hoc agent invocations. The hook reads `pipeline-state.md` and checks for a `PIPELINE_STATUS` marker with an active phase. Phases `none`, `idle`, and `complete` are treated as inactive. A missing state file or missing marker also triggers a block.

### Session Hydration (`session-hydrate.sh`)

This hook fires on SessionStart and invokes `hydrate-telemetry.mjs` with `--silent` and `--state-dir` flags. It hydrates T1 JSONL telemetry data and parses pipeline state files (`pipeline-state.md`, `context-brief.md`) to capture Eva's pipeline decisions and phase transitions into the brain. The hook exits 0 on all paths (non-blocking) -- any hydration errors are suppressed via `|| true`.

### Agent Start Telemetry (`log-agent-start.sh`)

This hook fires on SubagentStart and appends a JSON line to the telemetry JSONL file (`.claude/telemetry/session-hooks.jsonl` on Claude Code, `.cursor/telemetry/session-hooks.jsonl` on Cursor) with the event type (`start`), `agent_type`, `agent_id`, `session_id`, and an ISO 8601 timestamp. It is a non-enforcement hook (exit 0 always) and does not require `jq` -- it falls back to `grep`/`sed` parsing when `jq` is unavailable. Uses `$CLAUDE_PROJECT_DIR` (Claude Code) or `$CURSOR_PROJECT_DIR` (Cursor) to locate the telemetry directory.

### Agent Stop Telemetry (`log-agent-stop.sh`)

This hook fires on SubagentStop and appends a JSON line to `.claude/telemetry/session-hooks.jsonl` with the event type (`stop`), `agent_type`, `agent_id`, `session_id`, timestamp, and a `has_output` boolean indicating whether the agent produced non-empty output. The hook does not inspect or log the `last_assistant_message` content for privacy. It is a non-enforcement hook (exit 0 always) and does not require `jq`.

### Context Re-injection (`post-compact-reinject.sh`)

This hook fires on PostCompact (after Claude Code compacts the context window) and outputs `pipeline-state.md` and `context-brief.md` to stdout for re-injection into the post-compaction context. Only these two small files (~3KB total) are re-injected -- larger pipeline files (`error-patterns.md`, `investigation-ledger.md`, `last-qa-report.md`) are read on-demand. The hook exits 0 always and outputs nothing if `pipeline-state.md` does not exist.

### Agent Failure Tracking (`log-stop-failure.sh`)

This hook fires on StopFailure (when an agent turn ends due to an API error) and appends a structured markdown entry to `error-patterns.md` with the `agent_type`, timestamp, error type, and a truncated error message (200 characters max). It creates `error-patterns.md` with a header if the file does not exist. It is a non-enforcement hook (exit 0 always) and does not require `jq`.

### Configuration (`enforcement-config.json`)

The configuration file lives at `.claude/hooks/enforcement-config.json` (Claude Code) or `.cursor/hooks/enforcement-config.json` (Cursor) and is customized during `/pipeline-setup` with project-specific values:

```json
{
  "pipeline_state_dir": "docs/pipeline",
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
| `pipeline_state_dir` | `enforce-eva-paths.sh`, `enforce-sequencing.sh` | Eva's write boundary and pipeline state location |
| `colby_blocked_paths` | `enforce-colby-paths.sh` | Array of path prefixes Colby cannot write to. Default includes `docs/`, CI/CD paths, container files, and infra directories. Customized during `/pipeline-setup`. |
| `test_command` | Roz (QA verification) | Full test suite command (e.g., `npm test`, `pytest`). Used by Roz for QA verification. |
| `test_patterns` | `enforce-roz-paths.sh` | Patterns identifying test files for Roz's write boundary |

### Hook Registration

`/pipeline-setup` merges the hook registration into the project's settings file. The format is the same on both platforms, but uses the platform-appropriate project directory variable.

**Claude Code** (`.claude/settings.json`, uses `$CLAUDE_PROJECT_DIR`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-eva-paths.sh"}]
      },
      {
        "matcher": "Agent",
        "hooks": [
          {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-sequencing.sh"},
          {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-pipeline-activation.sh"}
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-git.sh", "if": "tool_input.command.includes('git ')"}]
      }
    ],
    "SubagentStart": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/log-agent-start.sh"}]
      }
    ],
    "SessionStart": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-hydrate.sh"}]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/log-agent-stop.sh"}
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-compact.sh"}]
      }
    ],
    "PostCompact": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-compact-reinject.sh"}]
      }
    ],
    "StopFailure": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/log-stop-failure.sh"}]
      }
    ]
  }
}
```

**Cursor** (`.cursor/settings.json`, uses `$CURSOR_PROJECT_DIR`): Identical structure with `$CURSOR_PROJECT_DIR` and `.cursor/hooks/` paths instead.

Each matcher determines which tool invocations trigger the hook. The pipe-separated `Write|Edit|MultiEdit` matcher on the main thread fires `enforce-eva-paths.sh` on any file write operation. Per-agent enforcement hooks (e.g., `enforce-colby-paths.sh`, `enforce-cal-paths.sh`) are wired through each agent's frontmatter overlay, not through settings.json. The `"if"` property is a JavaScript expression evaluated by the IDE before spawning the hook process -- when it evaluates to false, the hook is skipped entirely, reducing overhead on high-frequency tool calls. Existing settings in the file are preserved during the merge.

### Blocking vs. Non-Blocking

Hooks signal their result via exit code:

- **Exit 0** -- action allowed (or hook not applicable)
- **Exit 2** -- action blocked; the reason message on stderr is shown to the agent

The PreToolUse enforcement hooks (per-agent `enforce-{agent}-paths.sh`, `enforce-sequencing.sh`, `enforce-git.sh`, `enforce-pipeline-activation.sh`) exit 2 on violations. The telemetry hooks (`log-agent-start.sh`, `log-agent-stop.sh`, `log-stop-failure.sh`, `session-hydrate.sh`) exit 0 always -- they are observability hooks, not gates. The compaction hooks (`pre-compact.sh`, `post-compact-reinject.sh`) exit 0 always -- they are side-effect hooks, not gates.

The PreToolUse enforcement hooks exit 0 immediately when `jq` is not installed, when the config file is missing, or when the tool call is not one they care about. This ensures the hooks never interfere with unrelated tool usage or with projects that have not yet run `/pipeline-setup`. The telemetry and compaction hooks do not require `jq` -- they fall back to `grep`/`sed` parsing when `jq` is unavailable. All hooks work identically on Claude Code and Cursor.

### Enforcement Audit Trail

Every enforcement hook decision is appended to a local JSONL log and, at session start, blocked events are captured to the brain for pattern analysis. This is implemented by ADR-0031.

#### Log file

Each hook writes one JSON line per decision to `~/.claude/logs/enforcement-YYYY-MM-DD.jsonl` (user-level, date-partitioned, UTC). The file is created if absent. Writes use `|| true` so write failures are silent and never affect the enforcement exit code.

#### Log schema

```json
{
  "timestamp": "2026-04-07T14:30:00Z",
  "tool_name": "Write",
  "agent_type": "colby",
  "decision": "blocked",
  "reason": "Colby cannot write to blocked path. Attempted: docs/pipeline/state.md",
  "hook_name": "enforce-colby-paths"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 UTC |
| `tool_name` | string | The tool intercepted: `Write`, `Edit`, `MultiEdit`, `Bash`, or `Agent` |
| `agent_type` | string | Subagent frontmatter name (e.g., `colby`, `roz`). Empty string for main thread (Eva). |
| `decision` | string | `"blocked"` or `"allowed"` |
| `reason` | string | Human-readable reason -- for blocked decisions, this is the BLOCKED message |
| `hook_name` | string | Script basename without `.sh` extension (e.g., `enforce-colby-paths`) |

Both `"blocked"` and `"allowed"` decisions are logged locally. Only `"blocked"` decisions are brain-captured (allowed decisions are high-volume, low-signal).

#### Brain capture

`session-hydrate-enforcement.sh` is called by `session-hydrate.sh` at session start. It reads the current day's enforcement log, filters for `"decision":"blocked"` lines, and inserts each into the brain database via `brain/scripts/hydrate-enforcement.mjs`.

Brain capture shape:

| Field | Value |
|-------|-------|
| `thought_type` | `'insight'` |
| `source_agent` | `'eva'` |
| `source_phase` | `'qa'` |
| `importance` | `0.4` |
| `content` | `"Enforcement: [hook_name] blocked [agent_type] from [tool_name]. Reason: [reason]"` |
| `metadata.enforcement_event` | `true` |
| `metadata.hook_name` | hook basename |
| `metadata.agent_type` | agent identifier |
| `metadata.tool_name` | tool name |
| `metadata.decision` | `"blocked"` |
| `metadata.reason` | reason string |
| `metadata.session_date` | `"YYYY-MM-DD"` |

Note: `thought_type: 'insight'` with `metadata.enforcement_event: true` is used rather than a dedicated enum value. The brain schema uses closed PostgreSQL enums; adding `'enforcement'` would require a migration. The metadata tag is sufficient for `agent_search` queries and Darwin filtering. See ADR-0031 for the full rationale.

#### Querying enforcement data

```
agent_search: "enforcement blocked colby"
atelier_browse: filter by metadata.enforcement_event = true
```

Captures are idempotent. Each blocked event is hashed; re-running hydration on the same log file skips already-captured entries.

#### Fail-open guarantees

- Log write failure: silent (`|| true`), enforcement decision unaffected
- Brain unavailable during hydration: skipped, exit 0
- Log file absent: hydration skipped, exit 0
- Any hydration error: exit 0, never blocks session startup
- No retry logic (Retro lesson #004: hung process retry loop)

### Adding a New Enforcement Hook

Follow this procedure when you need a new mechanical enforcement rule. Hooks are organized into a three-layer pyramid; start by choosing the right layer.

**Step 1 -- Decide which layer.**

| Layer | Mechanism | When to use | Example |
|-------|-----------|-------------|---------|
| Layer 1 | Frontmatter `tools` / `disallowedTools` | Tool-level restrictions on a specific agent | Prevent Roz from using `Write` except on test files |
| Layer 2 | Per-agent frontmatter hook | Path-based enforcement on a specific agent | Block Colby from writing to `docs/pipeline/` |
| Layer 3 | Global hook in `settings.json` | Cross-cutting enforcement on the main thread (Eva) or all agents | Pipeline sequencing gates, git write guards |

Layer 1 is the lightest (no script needed). Layer 2 fires only for the named agent. Layer 3 fires on every tool invocation in the main thread.

**Step 2 -- Write the hook script.** Create the script in `source/claude/hooks/` (and optionally `source/cursor/hooks/` for Cursor parity). Source `hook-lib.sh` for shared parsing functions. Follow the standard pattern:

```bash
#!/bin/bash
# Per-agent path enforcement: {agent_name}
# PreToolUse hook on {tools} -- {description}
set -uo pipefail
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0

INPUT=$(cat)
if ! command -v jq &>/dev/null; then exit 0; fi

# Source shared hook library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/hook-lib.sh" ]; then
  source "$SCRIPT_DIR/hook-lib.sh" 2>/dev/null || true
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
# Filter for relevant tools only -- exit 0 for everything else
case "$TOOL_NAME" in Write|Edit|MultiEdit) ;; *) exit 0 ;; esac

# Your enforcement logic here
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

# Block or allow
echo "BLOCKED: {reason}" >&2
exit 2
```

Key conventions:
- Exit 0 when `jq` is missing, when config is missing, or when the tool call is irrelevant to the hook's concern. Hooks must never block unrelated operations.
- Exit 2 with a reason message on stderr to block an action. The reason is shown to the agent.
- Use `hook_lib_get_agent_type` to detect the current agent from the JSON input.
- Use `hook_lib_pipeline_status_field` to read pipeline state fields when decisions depend on pipeline phase.

**Step 3 -- Register the hook.** For Layer 2: add a `hooks:` entry in the agent's frontmatter overlay (`source/claude/agents/{agent}.frontmatter.yml`) specifying the hook event (`PreToolUse`), the `if` conditional (matching tool names), and the command path. For Layer 3: add an entry to the `settings.json` template in `skills/pipeline-setup/SKILL.md`.

**Step 4 -- Write a pytest.** Create `tests/hooks/test_{hook_name}.py` following the patterns in `tests/hooks/conftest.py`. Test at minimum: one blocked path, one allowed path, and config parity with `enforcement-config.json`.

**Step 5 -- Run /pipeline-setup.** The hook is installed to `.claude/hooks/` (or `.cursor/hooks/`) only after `/pipeline-setup` re-runs. Editing `.claude/hooks/` directly is overwritten on the next setup.

**Step 6 -- Document the hook.** Add a row to the Hook Scripts table and a description subsection in this section of technical-reference.md.

---

## Sentinel Security Agent

### Overview

Sentinel is an opt-in security audit agent backed by Semgrep MCP static analysis. It operates under partial information asymmetry: Sentinel receives the diff and Semgrep scan results, but no spec, ADR, or UX doc. It evaluates security independently of what the code was "intended" to do.

**Model:** Opus (fixed). **Pronouns:** they/them.

### Execution Points

Sentinel runs at one point in the pipeline:

1. **Review juncture only:** In parallel with Roz final sweep, Poirot, Robert-subagent, and Sable-subagent. Sentinel does not run per-wave alongside Roz and Poirot -- the review juncture is the single security gate.

### Workflow

1. Receives the `git diff` for changed files
2. Runs `semgrep_scan` on changed files via Semgrep MCP tools
3. Retrieves structured results via `semgrep_findings`
4. Cross-references findings against the diff to filter noise from unchanged code
5. Classifies each finding: BLOCKER (exploitable vulnerability), MUST-FIX (security concern), NIT (hardening suggestion)
6. Cross-references CWE and OWASP identifiers

### Triage Integration

Sentinel findings are triaged via the triage consensus matrix alongside Roz and Poirot:

| Sentinel | Other Reviewers | Action |
|----------|----------------|--------|
| BLOCKER | any | HALT -- Eva verifies finding is not false positive, then treats as Roz BLOCKER |
| MUST-FIX | Roz PASS, Poirot PASS | SECURITY CONCERN -- queue fix, Colby priority |
| MUST-FIX | Roz/Poirot also flag | CONVERGENT SECURITY -- high-confidence fix needed |

### Configuration

- **Enable:** `sentinel_enabled: true` in `.claude/pipeline-config.json`
- **Prerequisite:** The Semgrep MCP plugin must be installed before enabling Sentinel: `claude mcp add semgrep semgrep mcp`. A free [semgrep.dev](https://semgrep.dev/login) account is required (`semgrep login`). This is not managed by `/pipeline-setup`.
- **Install:** `/pipeline-setup` Step 6a copies `sentinel.md` and sets `sentinel_enabled: true`. It does not install Semgrep or register the MCP server.
- **Legacy cleanup:** Older versions of `/pipeline-setup` added a `semgrep` entry to the project `.mcp.json`. That entry is no longer managed by setup. If present, it can be removed -- `claude mcp add semgrep semgrep mcp` (above) registers Semgrep globally and supersedes it.
- **Disable:** When `sentinel_enabled: false`, Sentinel is completely absent. No extra tool calls, no triage column.

### Failure Handling

If Sentinel invocation fails (MCP server down, Semgrep scan error), Eva logs "Sentinel audit skipped: [reason]" and proceeds. Sentinel failure is never a pipeline blocker.

### Brain Integration

Sentinel does not touch the brain directly. Eva captures Sentinel findings post-review via `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'` (same pattern as Poirot).

---

## Agent Teams

### Overview

> **Claude Code only.** Agent Teams requires the Claude Code Agent Teams runtime. On Cursor, the pipeline always runs sequentially with identical output and quality gates.

Agent Teams is an experimental feature that enables parallel wave execution during the Colby build phase using Claude Code's Agent Teams runtime. When multiple ADR steps within a wave are independent (no shared files), Eva creates Colby Teammate instances that execute those steps simultaneously.

### Activation (Two Gates)

Both gates must pass for `agent_teams_available: true`:

| Gate | Source | Check |
|------|--------|-------|
| Config gate | `.claude/pipeline-config.json` (Claude Code) or `.cursor/pipeline-config.json` (Cursor) | `agent_teams_enabled: true` (set during `/pipeline-setup` Step 6b) |
| Environment gate | Shell environment | `CLAUDE_AGENT_TEAMS=1` (Claude Code feature flag -- not available on Cursor) |

Eva checks both gates at session boot (step 3d). If either fails, `agent_teams_available: false` and Eva uses sequential subagent invocation. On Cursor, the environment gate always fails, so Agent Teams is never active.

### Scope

Agent Teams applies exclusively to Colby build units within a wave. All other agents (Roz, Poirot, Robert, Sable, Ellis, Agatha, Cal, Sentinel, discovered agents) are invoked sequentially.

### Teammate Identity

Teammates are Colby instances. They load Colby's persona from `.claude/agents/colby.md` (Claude Code) and are subject to `enforce-colby-paths.sh` via Colby's frontmatter hooks. No new persona file exists for Teammates.

### Task Lifecycle

1. Eva creates one task per wave unit via `TaskCreate`
2. Teammate instances pick up tasks and execute build units
3. Each Teammate marks its task complete via `TaskUpdate`
4. `TaskCompleted` events fire on Eva (Team Lead). Eva processes them sequentially.
5. After all Teammates in the wave complete, Eva merges each worktree sequentially (deterministic merge order matches task creation order)
6. Roz wave QA + Poirot blind review run after all Teammates in the wave merge (wave boundary, same as sequential flow)

### Worktree Rules

- Worktrees are managed by Claude Code, not by Eva via Bash
- Merge order is deterministic: task creation order, not completion order
- Full test suite runs between each Teammate merge (rule 3 applies)
- Merge conflicts trigger fallback to sequential for the conflicting unit

### Fallback

When `agent_teams_available: false`, Eva falls back to sequential subagent invocation. Pipeline output is identical -- Agent Teams affects execution speed, not correctness.

### Mandatory Gate Notes

- Gate 2 (Ellis commits): Teammates do NOT commit. They execute the build and mark task complete. Eva merges worktrees, then routes to Ellis for per-wave commits after Roz QA PASS on the integrated result.
- Gate 3 (test suite): Teammates run lint+typecheck only. Roz runs the full suite on the integrated codebase after all Teammate worktrees in the wave are merged (wave boundary, not unit boundary).
- Gate 5 (Poirot): Poirot blind-reviews the cumulative wave diff after all Teammates' worktrees are merged, not the individual Teammate worktree diff.

---

## CI Watch

### Overview

CI Watch is an opt-in, session-scoped Eva orchestration protocol that monitors CI after Ellis pushes and autonomously drives a fix cycle on failure. It uses a background polling loop with short individual commands rather than long-running blocking processes, providing resilience across both GitHub Actions and GitLab CI.

Design rationale: ADR-0013. The polling approach (not `gh run watch`) was chosen for platform uniformity -- `glab` has no equivalent to `gh run watch` -- and for resilience against `run_in_background` timeout constraints.

### Configuration Fields

All fields are in `.claude/pipeline-config.json`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ci_watch_enabled` | boolean | `false` | Master toggle. CI Watch only activates when `true`. |
| `ci_watch_max_retries` | integer | `3` | Maximum fix cycles before CI Watch gives up. Set during `/pipeline-setup` Step 6c. Minimum: 1. |
| `ci_watch_poll_command` | string | `""` | Platform-specific CI status check command. Computed at setup time from `platform_cli`. |
| `ci_watch_log_command` | string | `""` | Platform-specific failure log retrieval command. Computed at setup time from `platform_cli`. |

Platform commands are computed during setup:

| Operation | GitHub (`gh`) | GitLab (`glab`) |
|-----------|--------------|-----------------|
| Poll status | `gh run list --commit {sha} --json status,conclusion,url,databaseId --limit 1` | `glab ci list --branch {branch} -o json \| head -1` |
| Get failure logs | `gh run view {run_id} --log-failed \| tail -200` | `glab ci trace {job_id} \| tail -200` |
| Auth check | `gh auth status` | `glab auth status` |

### Setup Gate (Step 6c)

CI Watch is offered during `/pipeline-setup` after Agent Teams (Step 6b). Two prerequisites gate enablement:

1. **Platform CLI configured:** `platform_cli` must be set in `pipeline-config.json`. If empty, setup blocks with a message to configure a platform first.
2. **CLI authenticated:** `gh auth status` or `glab auth status` must succeed. If auth fails, setup directs the user to authenticate and re-run setup.

The auth check happens at setup time, not at watch time. This catches authentication issues early rather than failing silently during a CI watch.

### Activation Gate

CI Watch activates when **both** conditions hold:
1. `ci_watch_enabled: true` in `pipeline-config.json`
2. Ellis has just pushed to remote (Ellis reports a successful push)

CI Watch is orthogonal to pipeline sizing -- it activates on any push from any sizing level when enabled.

### PIPELINE_STATUS Fields

Eva tracks CI Watch state in the PIPELINE_STATUS JSON marker in `pipeline-state.md`:

| Field | Type | Description |
|-------|------|-------------|
| `ci_watch_active` | boolean | Whether a watch is currently running |
| `ci_watch_retry_count` | integer | Number of fix cycles completed in this session |
| `ci_watch_commit_sha` | string | SHA of the commit being watched |

### Polling Loop

The background polling loop runs via `run_in_background` Bash (not Agent `run_in_background`):

- **Interval:** 30 seconds between polls
- **Timeout per command:** 60 seconds
- **Max iterations:** 60 (30 minutes total)
- **Error handling:** 3 consecutive polling errors triggers a connection-lost abort. The error streak counter resets on any successful poll. This is distinct from `ci_watch_max_retries` (fix cycle cap).

### Fix Cycle

On CI failure:
1. Eva pulls failure logs (truncated to last 200 lines per failed job; multiple jobs concatenated with headers, total cap 400 lines)
2. Roz investigates using the `roz-ci-investigation` invocation template (logs passed in CONTEXT, not as files)
3. Colby fixes using the `colby-ci-fix` template with Roz's diagnosis
4. Roz verifies using the `roz-ci-verify` template
5. **HARD PAUSE** -- Eva presents failure summary, fix delta, Roz verdict, and retry count
6. User approves: Eva writes `roz_qa: CI_VERIFIED` to PIPELINE_STATUS (single-use token for the enforce-sequencing hook), Ellis pushes, Eva clears `CI_VERIFIED`, increments retry count, re-launches watch
7. User rejects: watch stops, user handles manually

### Enforce-Sequencing Hook Integration

The enforce-sequencing hook (Gate 1: Ellis requires Roz QA) has a CI Watch exemption. When `ci_watch_active: true` and `roz_qa: CI_VERIFIED`, Ellis is allowed through. `CI_VERIFIED` is intentionally distinct from `PASS` to prevent a CI Watch verification from satisfying the build-phase gate (different quality context). Eva clears `CI_VERIFIED` after Ellis consumes it.

### Edge Cases

| Scenario | Handling |
|----------|----------|
| No CI run found for commit | Watch stops: "No CI run found for commit [sha]. Does this repo have CI configured?" |
| User mid-conversation when result arrives | `run_in_background` notifications append naturally without interrupting current work |
| Branch protection blocks push | Ellis reports the block, CI Watch stops, user handles manually |
| Agent failure during fix cycle | Loop stops immediately with a report identifying which agent failed and its output |
| New Ellis push during active watch | Old watch replaced, new watch starts with reset retry count |
| Dead watch (35+ minutes without reporting) | Eva checks `ci_watch_active` on next user interaction and declares watch dead |

### Brain Integration

After each CI Watch resolution (pass or fix exhaustion), Eva captures via `agent_capture`:
- `thought_type: 'pattern'`, `source_agent: 'eva'`, `source_phase: 'ci-watch'`
- Content: failure pattern, root cause from Roz, fix applied, outcome

This builds institutional memory for CI failure patterns. Eva can inject WARN context into future agent invocations when the same CI failure pattern recurs.

---

## Deps Agent

### Overview

The Deps agent is an opt-in, read-only dependency management agent that scans dependency manifests, checks CVEs via audit tools, predicts upgrade breakage by cross-referencing code usage against changelogs, and produces structured risk-grouped reports. It follows the Sentinel opt-in pattern: config flag, conditional install during setup, and auto-routing with a pre-flight gate.

Design rationale: ADR-0015. The agent is analysis-only -- it never modifies dependency files.

**Model:** Sonnet (fixed). **Pronouns:** they/them.

### Agent Persona

The persona file is `source/shared/agents/deps.md` (installed to `.claude/agents/deps.md` when enabled). Key characteristics:

- **disallowedTools:** `Agent, Write, Edit, MultiEdit, NotebookEdit` (read-only by default)
- **Permitted Bash commands:** Explicit whitelist -- `npm outdated --json`, `npm audit --json`, `pip list --outdated`, `pip-audit`, `cargo outdated`, `cargo audit --json`, `go list -m -u all`, and version checks
- **Prohibited Bash commands:** Explicit blocklist -- `npm install`, `pip install`, `cargo update`, `go get`, `go mod tidy`, and any command with `--save`, `--write`, or file redirection
- **Conservative labeling:** When uncertain (changelog unavailable, tool missing, private registry), always uses "Needs Review" rather than "Safe to Upgrade"

### Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `deps_agent_enabled` | boolean | `false` | Master toggle. Deps agent only activates when `true`. |

### Setup Gate (Step 6d)

The Deps agent is offered during `/pipeline-setup` after CI Watch (Step 6c). When the user enables it:

1. `deps_agent_enabled` is set to `true` in `.claude/pipeline-config.json`
2. `source/shared/agents/deps.md` is copied to `.claude/agents/deps.md`
3. `source/commands/deps.md` is copied to `.claude/commands/deps.md`

Idempotency: if `deps_agent_enabled` already exists and is `true`, setup skips mutation. If it exists and is `false`, setup confirms before changing. If absent, it defaults to `false`.

### Command: /deps

The `/deps` command file (`.claude/commands/deps.md`) defines two flows:

- **Flow A (Full Scan):** Triggered by `/deps` or auto-routed dependency questions. Eva invokes the Deps subagent, which produces a risk-grouped report.
- **Flow B (Migration ADR Brief):** Triggered when the user asks for a migration ADR for a specific package. Deps produces a structured migration brief (breaking changes, affected files, estimated effort), which Eva hands to Cal for ADR production.

### Auto-Routing

Eva routes dependency-related questions to the Deps agent when `deps_agent_enabled: true`:

| User intent pattern | Route |
|-------------------|-------|
| "Is [package] safe to upgrade?" | Deps |
| "Do we have any CVEs?" | Deps |
| "What dependencies need updates?" | Deps |
| "Check my deps" | Deps |

The `deps_agent_enabled` gate applies to auto-routed requests. When the agent is disabled, Eva suggests enabling it via `/pipeline-setup`.

### Workflow

The agent operates in three phases:

1. **Detect** -- Glob for manifest files, verify package manager tool availability via version checks
2. **Scan** -- Run outdated checks, CVE audits, and breakage prediction (changelog fetch + grep for breaking API usage)
3. **Classify and Report** -- Group dependencies by risk level (CVE Alert, Needs Review, Safe to Upgrade, No Action Needed)

### Risk Classification

| Risk Level | Criteria |
|------------|----------|
| **CVE Alert** | CVSS >= 7.0, or any CVE in a directly used package |
| **Needs Review** | Major version bump with breaking changes found in codebase, or changelog fetch failed |
| **Safe to Upgrade** | Minor/patch bump, no breaking changes in changelog or codebase usage |
| **No Action Needed** | Already at latest version |

### Supported Ecosystems

| Ecosystem | Manifest | Outdated | CVE Audit | Notes |
|-----------|----------|----------|-----------|-------|
| Node.js | `package.json` | `npm outdated --json` | `npm audit --json` | Full support |
| Python | `requirements.txt` | `pip list --outdated --format=json` | `pip-audit --format=json` | `pip-audit` must be installed separately |
| Rust | `Cargo.toml` | `cargo outdated` | `cargo audit --json` | `cargo-outdated` and `cargo-audit` must be installed |
| Go | `go.mod` | `go list -m -u all` | None | No standard Go CVE audit tool -- report notes the gap |

### Invocation Templates

Eva uses two templates for Deps invocations:

- **`deps-scan`** -- Full dependency scan. Task: "Scan all dependency manifests and produce a risk-grouped report."
- **`deps-migration-brief`** -- Scoped to a specific package. Task: "Produce a migration brief for [package] [current] to [target]."

### Failure Handling

| Scenario | Handling |
|----------|----------|
| No manifest found | Report: "No dependency manifests detected" -- stop |
| Package manager not installed | Skip that ecosystem, note the gap |
| Network error (WebFetch/WebSearch) | Breakage prediction unavailable -- report outdated and CVE data from local tools |
| Private registry auth failure | Note failure, CVE data unavailable for that ecosystem |
| Bash command timeout | Stop immediately, report partial results (retro lessons #003, #004) |

### Brain Integration

Deps does not touch the brain directly. Eva captures scan results post-invocation via `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'`, following the same pattern as Poirot and Sentinel.

---

## Darwin Agent

### Overview

Darwin is an opt-in, read-only pipeline evolution agent. It analyzes telemetry data (all three tiers) and error patterns to produce evidence-backed structural improvement proposals targeting agent personas, orchestration rules, invocation templates, model assignments, and quality gates. Darwin never modifies files -- all proposals require user approval and are implemented by Colby.

Design rationale: ADR-0016. Darwin is activated automatically at pipeline end when degradation alerts fire, or invoked on demand.

**Model:** Opus (fixed). **Pronouns:** they/them.

### Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `darwin_enabled` | boolean | `false` | Master toggle. Darwin only activates when `true` and `brain_available: true`. |

### Auto-Trigger (at pipeline end)

After the pipeline-end telemetry summary, Darwin auto-triggers when all of the following are true:
1. `darwin_enabled: true` in `pipeline-config.json`
2. `brain_available: true`
3. At least one degradation alert fired in the telemetry summary
4. Pipeline sizing is not Micro

When auto-triggered, Eva announces: "Degradation detected. Running Darwin analysis..." and invokes Darwin using the `darwin-analysis` invocation template.

### On-Demand Invocation

Eva routes to Darwin on these user intent patterns (when `darwin_enabled: true`):

| User intent | Route |
|-------------|-------|
| "Analyze the pipeline" | Darwin |
| "How are agents performing?" | Darwin |
| "Pipeline health" | Darwin |
| "Run Darwin" | Darwin |
| "What needs improving?" | Darwin |

When `darwin_enabled: false`, Eva suggests enabling it via `/pipeline-setup`.

### Workflow

1. Darwin reads injected Tier 3 telemetry from the last N pipelines (provided by Eva in the invocation)
2. Darwin reads `error-patterns.md` for recurring failure patterns and recurrence counts
3. Darwin reads `retro-lessons.md` for codified operational lessons
4. Darwin reads prior Darwin proposals and their outcomes (from brain)
5. Darwin evaluates agent fitness across metrics (first-pass QA rate, rework rate, EvoScore)
6. Darwin produces proposals ranked by expected impact at escalating intervention levels

### Proposal Handling

Eva presents proposals to the user one at a time. Each proposal can be approved, rejected (with reason), or modified (reject-then-repropose cycle). This is a hard pause -- Eva does not auto-advance past Darwin proposals.

For approved proposals: Eva captures the approval, routes to Colby for implementation, Roz verifies, Ellis commits.

For rejected proposals: Eva captures the rejection with the user's reason. Rejection metadata includes `rejected: true` and the rejection reason, so future Darwin sessions know what was already tried.

### Brain Integration

Darwin does not touch the brain directly. Eva captures proposals and their outcomes via `agent_capture` with `source_agent: 'eva'`, `source_phase: 'darwin'`, using `thought_type: 'decision'` for approved proposals and for rejections. Metadata includes `darwin_proposal_id` for traceability and, for approved proposals, a `baseline_value` of the target metric at approval time for future post-edit tracking.

---

## Agent Telemetry

### Overview

Agent Telemetry is Eva's quantitative metrics capture and trend analysis system. It captures cost, duration, rework rates, and quality scores across pipeline runs and surfaces trends at session boot. All telemetry data is stored in the Atelier Brain -- when the brain is unavailable, telemetry capture is skipped entirely with no behavioral change to the pipeline.

Design rationale: ADR-0014. This feature subsumes the previously separate EvoScore (#12) and eval-driven outcome metrics (#14) proposals into a unified telemetry system.

### Metric Tiers

Telemetry is organized into four tiers, each captured at a different granularity:

#### Tier 1: Per-Invocation (in-memory only)

Accumulated after every Agent tool completion. Eva does NOT call `agent_capture` per invocation -- Tier 1 data is held in-memory and captured in bulk as part of the Tier 2 record at wave end. Key fields:

| Field | Type | Source |
|-------|------|--------|
| `agent_name` | string | Agent identity |
| `duration_ms` | integer | Wall-clock timing |
| `model` | string | Agent tool result metadata |
| `input_tokens` / `output_tokens` | integer | Agent tool result metadata (0 when unavailable -- see note below) |
| `cost_usd` | float or null | Computed from cost estimation table |
| `context_utilization` | float or null | `(input + output tokens) / context_window_max` |
| `is_retry` | boolean | Whether this is a rework invocation |

**Token exposure gap (ADR-0030).** The Claude Code Agent tool does not expose per-agent `input_tokens` or `output_tokens` in real time. This was probed and confirmed unavailable as of 2026-04-07. Eva cannot accumulate a live running cost during a pipeline. The `input_tokens` / `output_tokens` fields default to `0` during live pipeline execution. Accurate token counts and cost figures are computed post-session by `hydrate-telemetry.mjs`, which reads the session JSONL files and extracts per-turn token usage. The pipeline-end telemetry summary reflects these post-hoc figures, not live Agent tool metadata. `cost_usd` is `null` for live Tier 1 captures and is populated by `hydrate-telemetry.mjs` after the session ends.

Full schema: `.claude/references/telemetry-metrics.md`.

#### Tier 2: Per-Wave

Captured once after each wave passes Roz QA PASS (not per unit). Includes per-unit breakdowns as array fields in metadata. Aggregated from in-memory Tier 1 accumulator. Key fields:

| Field | Type | Description |
|-------|------|-------------|
| `rework_cycles` | integer | Colby re-invocations after first (0 = first-pass QA) |
| `first_pass_qa` | boolean | `rework_cycles == 0` |
| `unit_cost_usd` | float or null | Sum of Tier 1 costs for this unit |
| `finding_counts` | object | `{roz: N, poirot: N, robert: N, sable: N, sentinel: N}` |
| `evoscore_delta` | float | `(tests_after - tests_broken) / tests_before` |

Skipped on Micro pipelines.

#### Tier 3: Per-Pipeline

Captured at pipeline end, after Ellis final commit. Aggregated from Tier 1 and Tier 2. Key fields:

| Field | Type | Description |
|-------|------|-------------|
| `total_cost_usd` | float or null | Sum of all invocation costs |
| `total_duration_ms` | integer | Pipeline start to Ellis final commit |
| `rework_rate` | float | Total rework cycles / total units |
| `first_pass_qa_rate` | float | Units passing first try / total units |
| `evoscore` | float | Average EvoScore delta across all units |
| `sizing` | string | micro / small / medium / large |

Skipped on Micro pipelines. Micro runs do not appear in boot trend data.

#### Tier 4: Over-Time Trends

Not stored directly -- derived from brain queries at session boot. Eva queries the last 10 Tier 3 summaries and computes averages, percentage changes, and degradation alerts.

### Capture Protocol

All telemetry captures use:
- `thought_type: 'insight'`
- `source_agent: 'eva'`
- `source_phase: 'telemetry'`
- `metadata.pipeline_id` (format: `{feature_name}_{ISO_timestamp}`)

Eva reads `telemetry-metrics.md` at pipeline start to load metric schemas, the cost estimation table, and alert thresholds.

On capture failure at any tier: Eva logs the failure and continues. Telemetry never blocks the pipeline.

### Cost Estimation Table

Hardcoded estimates for order-of-magnitude accuracy (not for billing):

| Model | Input per 1K tokens | Output per 1K tokens | Context window |
|-------|---------------------|---------------------|----------------|
| Opus | $0.015 | $0.075 | 200K |
| Sonnet | $0.003 | $0.015 | 200K |
| Haiku | $0.001 | $0.005 | 200K |

When model is unknown or not in the table: `cost_usd` is set to `null`.

### EvoScore

```
EvoScore = (tests_after - tests_broken) / tests_before
```

- `1.0` = no regressions, test count maintained or grew
- `> 1.0` = new tests added, no regressions
- `< 1.0` = regressions detected
- Edge case: `tests_before == 0` yields EvoScore `1.0` (no regression possible)

### Degradation Alert Thresholds

Alerts fire only when a threshold is exceeded for 3+ consecutive pipelines. Two consecutive breaches do NOT fire an alert (anti-fatigue rule).

| Alert | Threshold | Consecutive Required |
|-------|-----------|---------------------|
| Cost spike | >25% above rolling average | 3 |
| Rework accumulation | >2.0 cycles/unit | 3 |
| First-pass QA degradation | <60% | 3 |
| Agent failure pattern | >2 failures for same agent over last 10 pipelines | N/A (window-based) |
| Context pressure | >80% utilization per invocation | 3 consecutive invocations |
| EvoScore degradation | <0.9 | 3 |

### Boot Trend Query (Step 5b)

At session boot, when `brain_available: true`, Eva queries the brain for Tier 3 summaries (`agent_search` with `filter: { telemetry_tier: 3 }`, limit 10). Results are filtered client-side for `source_phase == 'telemetry'`.

| Prior pipelines found | Boot announcement |
|----------------------|-------------------|
| 2+ | `"Telemetry: Last {N} pipelines -- avg ${cost}, {duration} min. Rework: {rate}/unit. First-pass QA: {pct}%."` plus any degradation alerts |
| 1 | `"Telemetry: 1 prior pipeline -- ${cost}, {duration} min. Trends appear after 2+ pipelines for comparison."` |
| 0 | `"Telemetry: No prior pipeline data. Trends will appear after 2+ pipelines."` |
| Brain unavailable | Telemetry line omitted entirely |

### Pipeline-End Summary Format

Standard (non-Micro):
```
Pipeline complete. Telemetry summary:
  Cost: ${total_cost_usd} ({agent}: ${agent_cost}, ...)
  Duration: {total_duration_min} min ({phase}: {phase_duration_min} min, ...)
  Rework: {rework_rate} cycles/unit ({total_units} units, {first_pass_count} first-pass QA)
  EvoScore: {evoscore} ({tests_before} tests before, {tests_after} after, {tests_broken} broken)
  Findings: Roz {N}, Poirot {N}, Robert {N} (convergence: {N} shared)
```

Micro (abbreviated):
```
Telemetry: {invocation_count} invocations, {total_duration_min} min
```

Fallback: when token counts are unavailable, prints "Cost: unavailable (token counts not exposed)". When brain is unavailable, the summary still prints from in-memory accumulators.

### Missing Data Handling

| Data | When unavailable | Behavior |
|------|-----------------|----------|
| Token counts | Agent tool does not expose them | Log `0`, note "unavailable" in content |
| Model | Agent tool does not expose it | Set `"unknown"`, skip cost and context utilization |
| Cost | Tokens or model unavailable | Set `null`, log reason |
| Context utilization | Tokens or model unavailable | Set `null` |

### `pipeline_id` Generation

Format: `{feature_name}_{ISO_timestamp}`

- `feature_name`: slug from feature spec filename or ADR title (lowercase, hyphens)
- `ISO_timestamp`: pipeline start time in `YYYY-MM-DDTHH:MM:SSZ`

Example: `agent-telemetry-dashboard_2026-03-29T14:30:00Z`

---

## Dashboard

### Overview

The Atelier Dashboard (`/dashboard` skill) is a browser-based telemetry visualization page served by the brain HTTP server at `http://localhost:8788/ui/dashboard.html`. It displays pipeline cost, quality trends, agent fitness, and degradation alerts. The skill starts the brain HTTP server if it is not running and opens the dashboard in the default browser.

### REST API Endpoints

The brain HTTP server exposes 11 REST API endpoints (`brain/lib/rest-api.mjs`). The dashboard uses the telemetry endpoints; the settings UI uses the config and thought-type endpoints; the remaining endpoints support operations and diagnostics.

| Endpoint | Method | Auth | Purpose | Response |
|----------|--------|------|---------|----------|
| `/api/health` | GET | Exempt | Server health check | `{connected, brain_enabled, brain_name, config_source, thought_count, consolidation_interval_minutes, last_consolidation, next_consolidation_at}` |
| `/api/config` | GET | Required | Read brain configuration | brain_config row (all columns from `brain_config` table) |
| `/api/config` | PUT | Required | Update brain configuration | `{updated: true}` |
| `/api/thought-types` | GET | Required | List thought type configurations | `{thought_type, default_ttl_days, default_importance, description}[]` -- all rows from `thought_type_config` |
| `/api/thought-types/:type` | PUT | Required | Update a thought type's TTL, importance, or description | `{updated: true, type: "<name>"}` |
| `/api/purge-expired` | POST | Required | Delete expired thoughts and orphaned relations | `{purged_thoughts: <count>, purged_relations: <count>}` |
| `/api/stats` | GET | Required | Brain statistics summary | `{by_type, by_status, by_agent, by_human}` -- each is an object mapping names to counts |
| `/api/telemetry/scopes` | GET | Required | List distinct project scopes with telemetry data | `string[]` -- array of scope values |
| `/api/telemetry/summary` | GET | Required | Fetch Tier 3 (per-pipeline) telemetry summaries | `{content, metadata, created_at}[]` -- up to 100 most recent T3 thoughts |
| `/api/telemetry/agents` | GET | Required | Aggregate Tier 1 data per agent (invocations, duration, cost, tokens) | `{agent, invocations, avg_duration_ms, total_cost, avg_input_tokens, avg_output_tokens, metadata}[]` |
| `/api/telemetry/agent-detail` | GET | Required | Per-agent invocation detail (up to 20 most recent) | `{description, duration_ms, cost_usd, input_tokens, output_tokens, model, created_at}[]` |

The four telemetry endpoints accept an optional `?scope=<scope>` query parameter to filter by project. When `scope` is absent or `all`, no filter is applied. The scope filter uses PostgreSQL's `@>` array containment operator on the `scope` ltree column. The `/api/telemetry/agent-detail` endpoint also requires a `?name=<agent>` query parameter.

The `/api/config` PUT endpoint accepts a JSON body with any subset of these fields: `brain_enabled`, `consolidation_interval_minutes`, `consolidation_min_thoughts`, `consolidation_max_thoughts`, `conflict_detection_enabled`, `conflict_duplicate_threshold`, `conflict_candidate_threshold`, `conflict_llm_enabled`, `default_scope`. Numeric fields must be non-negative; threshold fields must be between 0 and 1.

### REST Authentication

All REST API endpoints except `/api/health` require an `Authorization: Bearer {token}` header.

**Token source.** The token is set via the `apiToken` field in the brain configuration (typically configured during `/brain-setup` or manually in the brain config file). The brain server reads this value at startup from the config resolution chain (environment variable, config file, or database row).

**Auth bypass.** When `apiToken` is `null` or unset, authentication is bypassed entirely -- all endpoints are open without a token. This is the default for local development.

**Auth enforcement.** When `apiToken` is set to a non-null string, every request to an auth-required endpoint must include the header `Authorization: Bearer {token}`. Requests with a missing or incorrect token receive a `401 Unauthorized` response:

```json
{"error": "Unauthorized"}
```

**Dashboard auth.** The dashboard HTML page stores the API token in the browser's `localStorage` and includes it in all fetch requests to the REST API. The settings UI provides a field to enter or update the token.

**`/api/health` exemption.** The health endpoint is always open regardless of auth configuration. This allows external monitoring tools to check server status without credentials.

### Dashboard Sections

**Pipeline Overview** -- summary stat cards computed from Tier 3 data: all-time totals (total cost, total pipelines, total invocations) plus per-pipeline averages (avg cost, avg duration). Duration cards show min and max across all pipelines when more than one pipeline exists. Empty state: "Awaiting pipeline data."

**Cost Trend** -- line chart of daily aggregated pipeline cost. Each data point sums cost across all pipelines on that calendar day. Tooltips show dollar amount and pipeline count. Empty state: "Cost trends appear after your first pipeline."

**Quality Trend** -- line chart tracking first-pass QA rate and rework rate over time. Requires pipeline-level quality telemetry (T3 summaries with `first_pass_qa_rate` and `rework_rate` metadata). Empty state: "Quality metrics not yet available" with an explanation of what is needed.

**Agent Fitness** -- grid of agent cards built from the `/api/telemetry/agents` response. Each card shows invocation count, average duration, total cost, and average token counts. Cards display a fitness badge:

| Badge | Condition |
|-------|-----------|
| **Thriving** | First-pass QA rate >= 80% and rework rate <= 1.0 |
| **Nominal** | Within acceptable range |
| **Struggling** | QA rate between 50--80% or rework rate between 1.0--2.0 |
| **Processing** | No quality telemetry data available yet |

Eva's card shows "ORCHESTRATOR" instead of a fitness badge. Clicking any non-Eva agent card opens a detail modal with that agent's recent invocations from `/api/telemetry/agent-detail` (the "Recent Activity" section shows description, duration, cost, model, and date per invocation).

**Degradation Alerts** -- active alerts from the telemetry alert threshold system.

### Project Scope Selector

When the brain contains telemetry from multiple projects, the `/api/telemetry/scopes` endpoint returns multiple scope values. The dashboard renders a scope selector in the header. Selecting a scope re-fetches all sections filtered to that project. When only one scope exists, the selector is hidden.

### Auto-Refresh

The dashboard auto-refreshes every 10 minutes. A green dot in the header indicates auto-refresh is active. The "Updated" timestamp shows the last data load time.

### Security: XSS Prevention and Input Escaping

The dashboard dynamically renders user-controlled data (agent names, metadata fields, metrics). All interpolations into `innerHTML` are wrapped in the `escapeHtml()` function to prevent XSS attacks.

**Implementation:**
- `escapeHtml(s)` (line 952 of `brain/ui/dashboard.html`) safely escapes text by setting a temporary DOM element's `textContent` and reading back the escaped `innerHTML`
- Every `innerHTML =` assignment is marked with an inline comment indicating whether the content is static (`/* trusted: ... */`) or escaped (`escapeHtml()` wraps all user fields)
- ~40+ call sites throughout the dashboard apply this pattern to agent names, labels, timestamps, cost/duration metrics, and other dynamic content

**Example pattern:**
```javascript
// Trusted static markup (no interpolation)
grid.innerHTML = /* trusted: static literal markup */ '<div class="card">...';

// Escaped user fields
grid.innerHTML = stats.map((s) =>
  '<div>' + escapeHtml(s.label) + '</div>'
).join('');
```

This ensures that if brain metadata contains HTML or JavaScript payloads, they are rendered as text rather than executed.

---

## Telemetry Hydration

### Overview

Telemetry hydration (`brain/scripts/hydrate-telemetry.mjs`) performs two tasks on each run:

1. **JSONL hydration** -- reads Claude Code session JSONL files and inserts per-agent token usage, cost, and duration into the brain as Tier 1 telemetry thoughts, then generates Tier 3 session summaries.
2. **State-file parsing** (when `--state-dir` is provided) -- parses `pipeline-state.md` and `context-brief.md` from the project's `docs/pipeline/` directory and emits `source_agent: 'eva'` brain captures for completed pipeline phases and user decisions. See [State-File Hydration](#state-file-hydration-evas-pipeline-decisions) under Brain Architecture for the full parsing schema.

### CLI Flags

| Flag | Description |
|------|-------------|
| `<project-sessions-path>` | Required positional: path to the Claude Code project sessions directory (e.g., `~/.claude/projects/-Users-you-yourproject`) |
| `--silent` | Suppresses all stdout output; errors still go to stderr |
| `--state-dir <path>` | Absolute path to `docs/pipeline/`. When provided, parses `pipeline-state.md` and `context-brief.md` after JSONL hydration. When absent, state-file parsing is skipped entirely. |

### Invocation Methods

| Method | When | Mode |
|--------|------|------|
| **SessionStart hook** (`session-hydrate.sh`) | Every session start (Claude Code and Cursor) | Silent (`--silent`), with `--state-dir docs/pipeline`, errors suppressed, non-blocking |
| **`/telemetry-hydrate` command** | Manual, on-demand | Verbose, reports summary to user |

The `session-hydrate.sh` SessionStart hook (registered in `.claude/settings.json`) is the primary invocation path. It passes both `--silent` and `--state-dir`:

```bash
node "$PLUGIN_BRAIN" "$SESSION_PATH" --silent --state-dir "$STATE_DIR" >/dev/null 2>&1 || true
```

Where `SESSION_PATH` is derived from `$CLAUDE_PROJECT_DIR` by replacing `/` with `-` and prepending `~/.claude/projects/-`, and `STATE_DIR` is `$CLAUDE_PROJECT_DIR/docs/pipeline`.

The `/telemetry-hydrate` command constructs the project sessions path from `CLAUDE_PROJECT_DIR` and runs the script without `--silent` (omitting `--state-dir` for the manual JSONL-only path).

### JSONL File Discovery

The script processes two types of files under `~/.claude/projects/-{project-path}/`:

| File Type | Location | Agent ID Format |
|-----------|----------|----------------|
| **Eva (parent session)** | `{sessionId}.jsonl` at the project root | `eva-{sessionId}` |
| **Subagent** | `{sessionId}/subagents/{agentId}.jsonl` | The filename stem (e.g., `colby-abc123`) |

For each JSONL file, the script parses all lines to extract: model (from the first assistant message), input/output/cache-read/cache-creation tokens (summed across all turns), and turn count. Duration is estimated from file timestamps (birth time to last modification).

### Cost Computation

Cost is computed using a built-in pricing table:

| Model Family | Input (per 1M tokens) | Output (per 1M tokens) |
|-------------|----------------------|----------------------|
| Opus | $15.00 | $75.00 |
| Sonnet | $3.00 | $15.00 |
| Haiku | $0.80 | $4.00 |

Cache read tokens are priced at 10% of the input rate; cache creation tokens at 25%. When the model is unknown or not in the table, cost is set to `null`.

### Duplicate Detection

Before inserting, the script queries the brain for existing thoughts matching `(session_id, agent_id)` in the metadata with `hydrated: true`. Already-hydrated agents are skipped. Hydration is idempotent.

### Tier 3 Summary Generation

After all Tier 1 insertions, the script calls `generateTier3Summaries()`. For each session that has Tier 1 data but no Tier 3 summary, it aggregates total cost, total duration, total invocations, and invocations-by-agent into a single Tier 3 thought. These summaries are what the dashboard's Pipeline Overview and trend charts consume.

### Storage Format

**JSONL telemetry thoughts (Tier 1 and Tier 3):**
- `thought_type: 'insight'`, `source_agent: 'eva'`, `source_phase: 'telemetry'`
- `importance: 0.3` (Tier 1) or `0.7` (Tier 3)
- `metadata.hydrated: true` (distinguishes hydrated data from live capture)
- `metadata.telemetry_tier: '1'` or `'3'`

**State-file thoughts (pipeline phases and user decisions):**
- `thought_type: 'decision'`, `source_agent: 'eva'`, `source_phase: 'pipeline'`
- `importance: 0.6`
- `metadata.hydrated: true`
- `metadata.state_capture_key` -- content-hash-based deduplication key (format: `state_phase_{hash16}` or `state_decision_{hash16}`)
- Pipeline-state items also include `metadata.feature`, `metadata.sizing`, `metadata.phase_item`
- Context-brief items also include `metadata.section: 'user_decisions'`

Embeddings are generated via OpenRouter when an API key is configured; otherwise a zero vector fallback is used. Zero-vector entries are still queryable via metadata filters.

---

## Agent Discovery

### Overview

Eva discovers custom agents at session boot by scanning `.claude/agents/` for non-core persona files. Discovered agents are additive only -- they never replace core agent routing.

### Core Agent Constant

The following 9 agents are hardcoded core agents: `cal`, `colby`, `roz`, `ellis`, `agatha`, `robert`, `sable`, `investigator`, `distillator`. Plus `sentinel` when enabled. Any `.md` file in `.claude/agents/` whose YAML frontmatter `name` field does not match one of these names is a discovered agent.

### Discovery Protocol

1. Run `Glob(".claude/agents/*.md")` to list all agent files
2. Read the YAML frontmatter `name` field from each file
3. Compare against the core agent constant
4. For non-core agents, read the `description` field
5. If brain is available, query `agent_search` for existing routing preferences
6. Announce: "Discovered N custom agent(s): [name] -- [description]"
7. On error: log and proceed with core agents only (never blocks boot)

### Routing Rules

- Core agents always have priority in the routing table
- Discovered agents with no domain overlap are available via explicit name mention only
- Discovered agents with overlapping domains trigger a one-time conflict prompt per (intent, agent) pair
- User preference is persisted via brain (`thought_type: 'preference'`) or `context-brief.md`

### Inline Agent Creation

When a user pastes markdown containing an agent definition pattern, Eva recognizes it and offers conversion to a pipeline agent persona file. The conversion follows `.claude/references/xml-prompt-schema.md` tag vocabulary. Name collisions with core agents are rejected. File writing is routed to Colby. Default access is read-only (`disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit`).

---

## Observation Masking and Context Hygiene

### Overview

Observation masking is Eva's primary within-session context hygiene procedure. It replaces full agent outputs with structured receipts after Eva processes them, and replaces superseded tool outputs with structured placeholders.

**Design principle:** Mechanical substitution, not intelligent compression. The full agent output remains available on disk or in the brain. Eva re-reads from disk only when constructing a downstream invocation.

### Agent Output Masking (receipts)

After processing each agent's return, Eva replaces the full output in her working context with a structured receipt. The full output remains on disk (in files the agent wrote, in `docs/pipeline/last-qa-report.md`, or in brain captures). Eva re-reads from disk only when she needs detail for a downstream invocation.

**Receipt format per agent:**

| Agent | Receipt Format |
|-------|---------------|
| **Cal** | `Cal: ADR at {path}, {N} steps, {N} tests specified` |
| **Colby** | `Colby: Unit {N} DONE, {N} files changed, lint {PASS/FAIL}, typecheck {PASS/FAIL}` |
| **Roz** | `Roz: Wave {N} {PASS/FAIL}, {N} blockers, {N} must-fix, {N} suggestions. Report: last-qa-report.md` |
| **Poirot** | `Poirot: Wave {N} {N} findings ({N} BLOCKER, {N} MUST-FIX, {N} NIT)` |
| **Sentinel** | `Sentinel: {N} findings ({CWE refs}). {N} BLOCKERs.` |
| **Ellis** | `Ellis: Committed {hash} on {branch}, {N} files` |
| **Robert** | `Robert: {N} criteria -- {N} PASS, {N} DRIFT, {N} MISSING, {N} AMBIGUOUS` |
| **Sable** | `Sable: {N} screens -- {N} PASS, {N} DRIFT, {N} MISSING` |
| **Agatha** | `Agatha: Written {paths}, updated {paths}` |
| **Distillator** | `Distillator: {source} compressed {ratio}. Output: {path}` |
| **Darwin** | `Darwin: {N} proposals at escalation levels {list}` |

Eva extracts the verdict, counts, file paths, and key decisions into the receipt, updates `pipeline-state.md`, and drops the full output from working context. Brain captures still use the full output data (captured before masking).

### Tool Output Masking (placeholders)

Never mask:
1. All agent reasoning, analysis, decisions, and conclusions
2. The most recent instance of each unique file read (keyed by file path)
3. The most recent Bash output for each distinct command
4. The most recent Grep result for each distinct query
5. Any tool output referenced in an active BLOCKER or MUST-FIX finding
6. Content of `pipeline-state.md` and `context-brief.md` (always-live state)

Mask (replace with placeholder):
1. File read outputs superseded by a more recent read of the same path
2. Tool outputs from completed pipeline phases
3. Verbose Bash outputs (build logs, test suite outputs) after Eva has extracted the verdict
4. Git diff outputs after Roz and Poirot have completed their wave review

Placeholder format:
```
[masked: {tool} {target}, {size} lines, turn {N}. Re-read: {recovery_command}]
```

### Scope: Distillator vs. Observation Masking

| Context type | Mechanism | When |
|-------------|-----------|------|
| Within-session tool outputs (file reads, grep, bash) | Observation masking | Before each subagent invocation and at phase transitions |
| Full agent outputs | Agent output masking (receipts) | After processing each agent return |
| Cross-phase structured documents (spec, UX doc, ADR) | Distillator compression | At phase boundaries when documents exceed ~5K tokens |

Distillator is reserved for structured document compression where lossless preservation of decisions, constraints, and relationships matters. Within-session tool outputs and agent outputs use masking.

---

## Compaction API Integration

### Overview

The Compaction API provides server-side context management. On Claude Code, this uses the Compaction API. On Cursor, an equivalent compaction mechanism performs the same function. When the context window fills, compaction fires automatically on both platforms. The pipeline is designed to survive compaction with zero data loss.

### Survival Mechanisms

| Mechanism | What it protects | How |
|-----------|-----------------|-----|
| Path-scoped rules | Mandatory gates, triage logic | Re-injected from disk on every turn on both platforms (ADR-0004 design) |
| Pipeline state files | Phase progress, decisions | Written to disk at every phase transition |
| Brain captures | Decisions, findings, lessons | Queryable after compaction via `agent_search` |
| PreCompact hook | Compaction visibility | Writes timestamped marker to `pipeline-state.md` before compaction |
| PostCompact hook | State continuity | Re-injects `pipeline-state.md` and `context-brief.md` into post-compaction context |

### PreCompact Hook (`pre-compact.sh`)

Fires before Claude Code compacts the context window. Appends a timestamped `<!-- COMPACTION: ... -->` HTML comment to `pipeline-state.md`. Lightweight by design: no brain calls, no subagent invocations, no test runs. Exits 0 always -- never blocks compaction.

### PostCompact Hook (`post-compact-reinject.sh`)

Fires after Claude Code compacts the context window. Outputs the contents of `pipeline-state.md` and `context-brief.md` to stdout for re-injection into the post-compaction context, ensuring Eva retains pipeline progress and conversational decisions. Only these two small files are re-injected -- larger pipeline files are read on-demand. Exits 0 always.

### Behavioral Changes

- Eva no longer tracks context usage percentage or handoff counts
- Eva no longer suggests session breaks based on context metrics
- Eva may still suggest a fresh session based on quality degradation signals (repetitive, contradictory, or missing obvious pipeline state)
- Agent Teams Teammates have inherently fresh context per task -- no compaction needed

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

> **Claude Code only.** Worktrees require Claude Code's worktree support. On Cursor, worktrees are not available and the pipeline runs without them.

When agents work in isolated git worktrees (Claude Code only):
- Changes integrate via `git merge` or `git cherry-pick`, never file copying
- Conflicts are resolved before advancing (route to Colby, then Roz)
- One worktree merge at a time with test suite between each
- Worktree agents do not see each other's changes

When Agent Teams is active (Claude Code only), worktrees are managed by Claude Code (not by Eva via Bash). Merge order is deterministic (task creation order). Full test suite runs between each Teammate merge. Merge conflicts trigger fallback to sequential for the conflicting unit.

---

## Pipeline Stop Reasons

Design rationale: ADR-0028.

Every pipeline run ends by writing a `stop_reason` field to `pipeline-state.md` -- both as a human-readable markdown field (`**Stop Reason:** completed_clean`) and as a key in the `PIPELINE_STATUS` JSON comment. The field is a closed enum. Eva never invents values outside this list.

### Stop Reason Enum

| Value | When Eva writes it | Terminal? |
|-------|--------------------|-----------|
| `completed_clean` | Pipeline reaches Ellis final commit and push successfully | Yes |
| `completed_with_warnings` | Pipeline completes but an Agatha divergence report or Robert/Sable DRIFT was accepted (not fixed) | Yes |
| `roz_blocked` | Roz BLOCKER that the user chose not to fix, or the loop-breaker gate (gate 12) fired and the user abandoned | Yes |
| `user_cancelled` | User explicitly said "stop", "cancel", or "abandon" during an active pipeline | Yes |
| `hook_violation` | A PreToolUse hook blocked an agent action that could not be retried (path violation) and the user abandoned | Yes |
| `budget_threshold_reached` | User declined to proceed after the token budget estimate gate (ADR-0029) | Yes |
| `brain_unavailable` | Pipeline required the brain (e.g., Darwin auto-trigger) and the brain was down; user abandoned rather than continuing in baseline mode | Yes |
| `scope_changed` | Cal discovered scope-changing information and the user chose to re-plan rather than continue | Yes |
| `session_crashed` | Inferred at next session boot when a stale pipeline (non-idle phase) has no `stop_reason` | Yes (retroactive) |
| `legacy_unknown` | Read-only inference for pre-ADR-0028 pipelines that lack the field entirely | N/A (inferred, read-only) |

### Implementation Rules

**`legacy_unknown` is never written by Eva.** It is a read-only sentinel that session-boot.sh and the hydrator apply when the `stop_reason` field is absent from an older pipeline record. Darwin treats absent and `legacy_unknown` identically.

**`session_crashed` is always retroactive.** Eva cannot write a stop reason during a crash. At next session boot, `session-boot.sh` detects stale pipelines (non-idle phase, no `stop_reason`) and reports `stop_reason: session_crashed` in its boot JSON output.

**Extension rule:** New stop reason values require a new ADR that supersedes the enum section. Eva never invents reasons at runtime.

### State Write Format

Eva writes `stop_reason` on every terminal transition -- at the same time she writes `phase: idle`. The value appears in two places in `pipeline-state.md`:

1. A markdown field: `**Stop Reason:** completed_clean`
2. The `PIPELINE_STATUS` JSON comment: `"stop_reason": "completed_clean"`

### T3 Telemetry Inclusion

The `stop_reason` value is included in the Tier 3 brain capture at pipeline end under `metadata.stop_reason`. Darwin can filter by this field using `agent_search` with `filter: { stop_reason: 'roz_blocked' }`. No brain schema changes are required -- it is a metadata field on the existing Tier 3 thought.

### Upgrade Safety

Pre-ADR-0028 pipeline state files lack the `stop_reason` field. Absent field reads as `legacy_unknown`. The pipeline never crashes on a missing field. Old T3 brain captures that lack `metadata.stop_reason` are treated identically to `legacy_unknown` by Darwin queries.

---

## Token Budget Estimate Gate

Design rationale: ADR-0029. This is Track A (heuristic pre-run estimate only). Track B (live token accumulation) is out of scope for this release.

### Overview

Before invoking the first agent on a Large pipeline, Eva shows a pre-run cost estimate. The estimate is labeled "order-of-magnitude -- not billing" and presented as a range to communicate inherent uncertainty. When `token_budget_warning_threshold` is configured, the gate also fires on Medium pipelines when the estimate exceeds the threshold.

This is a behavioral gate -- no PreToolUse hook enforces it. Eva is required to show the estimate and wait for the user to respond before invoking any agent.

### Gate Rules

| Sizing | No threshold (`null`) | Threshold configured |
|--------|----------------------|---------------------|
| Micro | No gate, no estimate | No gate, no estimate |
| Small | No gate, no estimate | No gate, no estimate |
| Medium | No gate, no estimate | Estimate shown; hard pause if threshold exceeded |
| Large | Estimate always shown; hard pause | Estimate always shown; hard pause |

"Hard pause" means Eva will not invoke the first agent until the user explicitly responds.

For Medium pipelines with a threshold: if the estimate is within the threshold, Eva shows the estimate with a "within threshold" note but does not hard pause. If the estimate exceeds the threshold, Eva hard pauses.

### Estimate Presentation Format

```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Large | Steps: [N or "TBD -- estimated after Cal"] | Agents: [roster count]
  Estimated cost: $X.XX -- $Y.YY (based on sizing heuristics and model assignments)
  [Threshold: $Z.ZZ -- estimate EXCEEDS threshold]  <- only when threshold configured and exceeded
  [Threshold: $Z.ZZ -- within threshold]             <- only when threshold configured and within

Proceed? (yes / cancel / downsize to Medium)
```

The "downsize to Medium" option appears only on Large pipelines. Medium proceed/cancel prompts do not include a downsize option.

### Sizing Model

The estimate formula uses three inputs:

**1. Agent roster by sizing tier:**

| Sizing | Typical agent invocations |
|--------|--------------------------|
| Micro | 1-2 (Colby + Roz) |
| Small | 3-5 (Cal skill + Colby + Roz + Ellis) |
| Medium | 8-15 (Robert? + Sable? + Cal + Roz test + Colby*N + Roz QA*N + Poirot + Ellis) |
| Large | 15-30+ (full ceremony: Robert + Sable + Agatha plan + Colby mockup + Sable verify + Cal + Roz test + Colby*N + Roz QA*N + Poirot*N + Robert review + Sable review + Sentinel? + Agatha docs + Ellis) |

**2. Per-invocation token estimate by model tier:**

| Model | Avg input tokens | Avg output tokens | Cost per invocation |
|-------|-----------------|-------------------|---------------------|
| Opus | 50,000 | 8,000 | ~$1.35 |
| Sonnet | 40,000 | 6,000 | ~$0.21 |
| Haiku | 20,000 | 3,000 | ~$0.035 |

These are order-of-magnitude averages. Actual usage varies by feature complexity, context window fill, tool calls, and rework cycles.

**3. Step count multiplier (when known):**

When Cal has already produced an ADR with N steps:
- Colby invocations: `N * 1.3` (30% rework assumption)
- Roz QA invocations: `N * 1.1` (10% scoped re-run assumption)
- Poirot invocations: `ceil(N / wave_size)` where `wave_size` defaults to 3

When step count is not yet known (estimate runs before Cal), the sizing-tier defaults from the table above apply.

**Formula:**

```
low_estimate  = sum(agent_count_by_model[model] * cost_per_invocation[model]) * 0.7
high_estimate = sum(agent_count_by_model[model] * cost_per_invocation[model]) * 1.5
```

The 0.7x multiplier models optimistic conditions (smaller context windows, no rework). The 1.5x multiplier models pessimistic conditions (full context windows, rework cycles, retries).

### Configuration

`token_budget_warning_threshold` in `pipeline-config.json`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `token_budget_warning_threshold` | `number \| null` | `null` | Cost threshold in USD. When set, Eva shows the estimate and fires the gate on Medium pipelines when the estimate exceeds this value. When `null`, the estimate is shown on Large pipelines only with no threshold comparison. Upgrade-safe: absent key treated as `null`. |

### Cancellation Flow

When the user cancels after the estimate:

1. Eva writes `stop_reason: budget_threshold_reached` to `pipeline-state.md`
2. Eva announces: "Pipeline cancelled. Stop reason: budget threshold. Consider: (a) downsizing to Medium/Small, (b) breaking the feature into smaller increments, (c) adjusting `token_budget_warning_threshold` in `pipeline-config.json`."
3. Pipeline transitions to idle.

### T3 Telemetry Inclusion

After the estimate is shown and the user proceeds, Eva includes the estimate range in the Tier 3 capture at pipeline end:
- `metadata.budget_estimate_low`: the low-end USD estimate
- `metadata.budget_estimate_high`: the high-end USD estimate

This enables post-hoc calibration: `actual_cost / budget_estimate_high > 2.0` indicates the formula is significantly under-estimating.

### Anti-Goals (Track A)

- **No live token accumulation.** The Agent tool does not reliably expose token counts during execution. The gate is pre-run only.
- **No automatic pipeline downsizing.** Decomposition of a Large feature into multiple Smalls is a Cal responsibility, not a mechanical sizing rule.
- **No hook enforcement.** The gate is behavioral. A future PreToolUse hook could enforce it, but that is out of scope for Track A.

---

## Cross-References

### Installed files

- **User guide:** [docs/guide/user-guide.md](user-guide.md)
- **Agent system rules:** `.claude/rules/agent-system.md`
- **Default persona:** `.claude/rules/default-persona.md`
- **Quality framework:** `.claude/references/dor-dod.md`
- **Operational procedures:** `.claude/references/pipeline-operations.md`
- **Invocation templates:** `.claude/references/invocation-templates.md`
- **Shared agent preamble:** `.claude/references/agent-preamble.md`
- **QA check procedures:** `.claude/references/qa-checks.md`
- **Branch/MR procedures:** `.claude/references/branch-mr-mode.md`
- **Sentinel persona (opt-in):** `.claude/agents/sentinel.md`
- **Brain schema:** `brain/schema.sql` (in plugin directory)
- **Plugin metadata:** `.claude-plugin/plugin.json`

### Architecture Decision Records

Full ADR index: [docs/architecture/README.md](../architecture/README.md)

**Brain:** ADR-0001 (Atelier Brain), ADR-0017 (Brain Hardening), ADR-0021 (Mechanical Brain Wiring), ADR-0024 (Mechanical Brain Writes), ADR-0026 (Beads Provenance Records), ADR-0027 (Brain-Hydrate Scout Fan-Out)

**Agents and Personas:** ADR-0005 (XML-Based Prompt Structure), ADR-0006 (XML Tag Migration), ADR-0008 (Agent Discovery), ADR-0023 (Agent Specification Reduction)

**Enforcement and Hooks:** ADR-0007 (DoR/DoD Warning Hook), ADR-0020 (Wave 2 Hook Modernization), ADR-0022 (Wave 3 Native Enforcement Redesign), ADR-0031 (Permission Audit Trail), ADR-0033 (Hook Enforcement Audit Fixes)

**Telemetry and Dashboard:** ADR-0014 (Agent Telemetry Dashboard), ADR-0018 (Dashboard Integration), ADR-0025 (Mechanical Telemetry Extraction), ADR-0030 (Token Exposure Probe and Accumulator)

**Pipeline Features:** ADR-0002 (Team Collaboration), ADR-0009 (Sentinel Security Agent), ADR-0010 (Agent Teams), ADR-0013 (CI Watch), ADR-0015 (Deps Agent), ADR-0016 (Darwin Self-Evolving Pipeline), ADR-0028 (Named Stop Reason Taxonomy), ADR-0029 (Token Budget Estimate Gate), ADR-0032 (Pipeline State Session Isolation)

**Codebase:** ADR-0003 (Code Quality Overhaul), ADR-0004 (Pipeline Evolution), ADR-0011 (Observation Masking), ADR-0012 (Compaction API), ADR-0019 (Cursor Port)

**Remediation:** ADR-0034 (Gauntlet Remediation), ADR-0035 (Wave 4 Consumer Wiring), ADR-0036 (Wave 5 Documentation Sweep), ADR-0037 (Wave 6 Dashboard A11y and Cursor Parity)
