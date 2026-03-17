---
name: pipeline-setup
description: Use when users want to install or set up the atelier-pipeline multi-agent orchestration system in their project. Bootstraps all agent personas, rules, commands, references, and pipeline state files. Works for new and existing projects.
---

# Atelier Pipeline -- Setup

This skill installs the full Atelier Pipeline multi-agent orchestration system into the user's project.

## Setup Procedure

### Step 1: Gather Project Information

Before installing, ask the user about their project. Ask these questions conversationally, one at a time -- do not dump a list.

**Required information:**

1. **Tech stack** -- Language, framework, runtime (e.g., "React 19 with Vite, Express.js backend, PostgreSQL")
2. **Test framework** -- What testing library/runner (e.g., "Vitest", "Jest", "pytest", "cargo test")
3. **Test commands** -- The exact commands for:
   - Linting (e.g., `npm run lint`)
   - Type checking (e.g., `npm run typecheck`)
   - Running the full test suite (e.g., `npm test` or `npx vitest run`)
   - Running a single test file (e.g., `npx vitest run path/to/file`)
4. **Source structure** -- Where features, components, services, and routes live (e.g., "src/features/<feature>/ for frontend, services/api/ for backend")
5. **Database/store pattern** -- How database access is structured (e.g., "Factory functions with closures over DB client", "Prisma ORM", "raw SQL with pg")
6. **Build/deploy commands** -- How the project builds and ships (e.g., `npm run build`, Docker, Podman Compose)
7. **Coverage thresholds** -- If they have existing targets (statement, branch, function, line percentages)
8. **Complexity limits** -- If they have cyclomatic complexity thresholds (e.g., TSX CCN <= 18)

If the user does not have answers for optional items (coverage, complexity), use sensible defaults.

### Step 2: Read Templates

Read the template files from the plugin's templates directory. These serve as the base for each installed file:

```
plugins/atelier-pipeline/templates/
  rules/
    default-persona.md            # Eva orchestrator persona
    agent-system.md               # Full orchestration rules, routing, gates
  agents/
    cal.md                        # Architect subagent
    colby.md                      # Engineer subagent
    roz.md                        # QA subagent
    ellis.md                      # Commit manager subagent
    documentation-expert.md       # Documentation subagent
  commands/
    pm.md                         # /pm -- Robert (product)
    ux.md                         # /ux -- Sable (UX design)
    architect.md                  # /architect -- Cal (architecture)
    debug.md                      # /debug -- Roz -> Colby -> Roz
    pipeline.md                   # /pipeline -- Eva (orchestration)
    devops.md                     # /devops -- Eva (infrastructure)
    docs.md                       # /docs -- Agatha (documentation)
  references/
    dor-dod.md                    # Definition of Ready / Definition of Done framework
    retro-lessons.md              # Retro lessons template (starts empty)
    invocation-templates.md       # Subagent invocation examples
    cloud-architecture.md         # Cloud/IaC reference patterns
  pipeline/
    pipeline-state.md             # Session recovery state template
    context-brief.md              # Context preservation template
    error-patterns.md             # Error pattern log template
    investigation-ledger.md       # Debug hypothesis tracking template
    last-qa-report.md             # QA report template
```

### Step 3: Install Files

Copy each template to its destination in the user's project, customizing placeholders with the project-specific values gathered in Step 1.

**Installation manifest:**

| Template Source | Destination | Purpose |
|----------------|-------------|---------|
| `templates/rules/default-persona.md` | `.claude/rules/default-persona.md` | Eva persona -- always loaded by Claude Code |
| `templates/rules/agent-system.md` | `.claude/rules/agent-system.md` | Orchestration rules, routing table, quality gates |
| `templates/agents/cal.md` | `.claude/agents/cal.md` | Architect subagent persona |
| `templates/agents/colby.md` | `.claude/agents/colby.md` | Engineer subagent persona |
| `templates/agents/roz.md` | `.claude/agents/roz.md` | QA subagent persona |
| `templates/agents/ellis.md` | `.claude/agents/ellis.md` | Commit manager subagent persona |
| `templates/agents/documentation-expert.md` | `.claude/agents/documentation-expert.md` | Documentation subagent persona |
| `templates/commands/pm.md` | `.claude/commands/pm.md` | /pm slash command |
| `templates/commands/ux.md` | `.claude/commands/ux.md` | /ux slash command |
| `templates/commands/architect.md` | `.claude/commands/architect.md` | /architect slash command |
| `templates/commands/debug.md` | `.claude/commands/debug.md` | /debug slash command |
| `templates/commands/pipeline.md` | `.claude/commands/pipeline.md` | /pipeline slash command |
| `templates/commands/devops.md` | `.claude/commands/devops.md` | /devops slash command |
| `templates/commands/docs.md` | `.claude/commands/docs.md` | /docs slash command |
| `templates/references/dor-dod.md` | `.claude/references/dor-dod.md` | Quality framework |
| `templates/references/retro-lessons.md` | `.claude/references/retro-lessons.md` | Shared lessons (empty template) |
| `templates/references/invocation-templates.md` | `.claude/references/invocation-templates.md` | Subagent invocation examples |
| `templates/references/cloud-architecture.md` | `.claude/references/cloud-architecture.md` | Cloud/IaC patterns |
| `templates/pipeline/pipeline-state.md` | `docs/pipeline/pipeline-state.md` | Session recovery state |
| `templates/pipeline/context-brief.md` | `docs/pipeline/context-brief.md` | Context preservation |
| `templates/pipeline/error-patterns.md` | `docs/pipeline/error-patterns.md` | Error pattern tracking |
| `templates/pipeline/investigation-ledger.md` | `docs/pipeline/investigation-ledger.md` | Debug hypothesis tracking |
| `templates/pipeline/last-qa-report.md` | `docs/pipeline/last-qa-report.md` | QA report persistence |

**Total: 24 files across 5 directories.**

### Step 4: Customize Placeholders

The following placeholders in template files must be replaced with project-specific values:

| Placeholder | Replaced With | Example |
|-------------|---------------|---------|
| `{{TECH_STACK}}` | Project tech stack description | "React 19 (Vite), Express.js, PostgreSQL" |
| `{{LINT_COMMAND}}` | Lint command | `npm run lint` |
| `{{TYPECHECK_COMMAND}}` | Type check command | `npm run typecheck` |
| `{{TEST_COMMAND}}` | Full test suite command | `npm test` |
| `{{TEST_SINGLE_COMMAND}}` | Single file test command | `npx vitest run` |
| `{{SOURCE_STRUCTURE}}` | Feature/source directory layout | "src/features/<feature>/ for UI, services/api/ for backend" |
| `{{DB_PATTERN}}` | Database access pattern | "Factory functions with closures over DB client" |
| `{{BUILD_COMMAND}}` | Build command | `npm run build` |
| `{{COVERAGE_THRESHOLDS}}` | Coverage targets | "stmt=70, branch=65, fn=75, lines=70" |
| `{{COMPLEXITY_THRESHOLDS}}` | Complexity limits | "TSX CCN <= 18, TS/JS CCN <= 12" |

### Step 5: Update CLAUDE.md

If the project already has a `CLAUDE.md` file, append the pipeline section to it. If no `CLAUDE.md` exists, create one with the full template.

**Section to add:**

```markdown
## Pipeline System (Atelier Pipeline)

This project uses a multi-agent orchestration pipeline for structured development.

**Agents:** Eva (orchestrator), Robert (product), Sable (UX), Cal (architect), Colby (engineer), Roz (QA), Agatha (docs), Ellis (commit)

**Commands:** /pm, /ux, /architect, /debug, /pipeline, /devops, /docs

**Pipeline state:** docs/pipeline/ -- Eva reads this at session start for recovery

**Key rules:**
- Roz writes tests before Colby builds (Roz-first TDD)
- Roz verifies every Colby output (no self-review)
- Ellis commits (Eva never runs git on code)
- Full test suite between work units
```

### Step 6: Print Summary

After installation, print:

1. A count of files installed (24 files across 5 directories)
2. The directory tree showing what was created
3. A reminder of available slash commands
4. Instructions to start their first pipeline run

**Example summary:**

```
Atelier Pipeline installed successfully.

Files installed: 24
  .claude/rules/       -- 2 files (Eva persona, orchestration rules)
  .claude/agents/      -- 5 files (Cal, Colby, Roz, Ellis, Agatha)
  .claude/commands/    -- 7 files (/pm, /ux, /architect, /debug, /pipeline, /devops, /docs)
  .claude/references/  -- 4 files (quality framework, retro lessons, invocation templates, cloud patterns)
  docs/pipeline/       -- 5 files (state tracking for session recovery)
  CLAUDE.md            -- updated with pipeline section

Available commands:
  /pm          -- Feature discovery and product spec (Robert)
  /ux          -- UI/UX design (Sable)
  /architect   -- Architecture and ADR production (Cal)
  /debug       -- Bug investigation and fix chain (Roz -> Colby -> Roz)
  /pipeline    -- Full pipeline orchestration (Eva)
  /devops      -- Infrastructure and deployment (Eva)
  /docs        -- Documentation planning and writing (Agatha)

To start your first pipeline:
  Describe a feature idea, or say "let's build [feature name]"
  Eva will size the work and route to the right starting agent.
```

## Important Notes

- **Do not overwrite existing files without asking.** If `.claude/rules/` or `.claude/agents/` already exists with content, ask the user whether to merge or replace.
- **Git-track the installed files.** Recommend the user commits the pipeline files so the system persists across clones and team members.
- **Templates are the source of truth.** If a template file is missing from the plugin's templates directory, report which file is missing and skip it rather than generating content from scratch.
- **Validate after install.** After writing all files, verify that Claude Code recognizes the slash commands by listing them. If the rules files are not being loaded, check that they are in `.claude/rules/` (Claude Code auto-loads all files in this directory).

## What Each Directory Does

| Directory | Loaded By | Purpose |
|-----------|-----------|---------|
| `.claude/rules/` | Claude Code automatically (every conversation) | Eva persona and orchestration rules -- always active |
| `.claude/agents/` | Claude Code when subagents are invoked | Agent personas for execution tasks |
| `.claude/commands/` | Claude Code when user types a slash command | Manual agent invocation overrides |
| `.claude/references/` | Agents when they need shared knowledge | Quality framework, lessons, templates |
| `docs/pipeline/` | Eva at session start | State recovery, context preservation, error tracking |
