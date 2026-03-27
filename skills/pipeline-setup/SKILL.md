---
name: pipeline-setup
description: Use when users want to install or set up the atelier-pipeline multi-agent orchestration system in their project. Bootstraps all agent personas, rules, commands, references, and pipeline state files. Works for new and existing projects.
---

# Atelier Pipeline -- Setup

This skill installs the full Atelier Pipeline multi-agent orchestration system into the user's project.

<procedure id="setup">

## Setup Procedure

### Step 1: Gather Project Information

Before installing, ask the user about their project. Ask these questions conversationally, one at a time -- do not dump a list.

**Required information:**

1. **Tech stack** -- Language, framework, runtime (e.g., "React 19 with Vite, Express.js backend, PostgreSQL")
2. **Test framework** -- What testing library/runner (e.g., "Vitest", "Jest", "pytest", "cargo test")
3. **Test commands** -- The exact commands for:
   - **Lint command** -- fast lint/typecheck checks with no DB or external dependencies, used by agents during their workflow (e.g., `npm run lint && tsc --noEmit`, `black --check . && ruff check . && mypy .`).
   - **Full test suite** -- the complete test suite including DB-dependent and integration tests, used by Roz for QA verification (e.g., `npm test`, `pytest --cov`). Runs once per work unit.
   - Running a single test file (e.g., `npx vitest run path/to/file`)
4. **Source structure** -- Where features, components, services, and routes live (e.g., "src/features/<feature>/ for frontend, services/api/ for backend")
5. **Database/store pattern** -- How database access is structured (e.g., "Factory functions with closures over DB client", "Prisma ORM", "raw SQL with pg")
6. **Build/deploy commands** -- How the project builds and ships (e.g., `npm run build`, Docker, Podman Compose)
7. **Coverage thresholds** -- If they have existing targets (statement, branch, function, line percentages)

If the user does not have answers for optional items (coverage), use sensible defaults.

### Step 1b: Branching Strategy Selection

**Pre-checks (before asking):**

1. Check `git rev-parse --git-dir` -- if no git repo, skip branching question entirely. Default to trunk-based, do not write pipeline-config.json.
2. Check `git remote get-url origin` -- if no remote, auto-select trunk-based with message: "No remote detected -- defaulting to trunk-based. Run setup again after adding a remote to configure MR-based flows." Skip to next step.

**If git + remote exist, ask the user (one question, not a list dump):**

> Which branching strategy should the pipeline use?
> - **Trunk-Based Development** (Recommended for solo/small teams) -- Commit directly to main. Simplest setup.
> - **GitHub Flow** -- Feature branches + merge requests. Main is always deployable.
> - **GitLab Flow** -- GitHub Flow + environment branches (staging, production). For staged deployments.
> - **GitFlow** -- Formal release cycle with develop + main. For versioned software with scheduled releases.

**Follow-up per strategy:**

- **Trunk-based:** No follow-up needed.
- **GitHub Flow / GitLab Flow / GitFlow:** Detect platform from remote URL (github -> `gh`, gitlab -> `glab`). If unrecognizable, ask user. Then check CLI availability (`which gh` or `which glab`). If missing, detect package manager (try `which brew`, `which apt-get`, `which dnf` in order). If package manager found, offer: "[Strategy] requires `[cli]` CLI, which isn't installed. Install with `[pm] install [cli]`?" Options: "Install it for me" / "I'll install it later". If no package manager found: "Please install `[cli]` CLI before running the pipeline. See [install URL]."
- **GitLab Flow additional:** Ask "What are your environment branch names?" Default: staging, production.
- **GitFlow:** Platform detection only, no additional questions (conventions are standardized). Integration branch is `develop`.

**Store selection:** Write `.claude/pipeline-config.json` with the appropriate values from `source/pipeline/pipeline-config.json` as the template, filled with the user's selections.

### Step 2: Read Templates

Read the template files from the plugin's templates directory. These serve as the base for each installed file:

```
plugins/atelier-pipeline/source/
  rules/
    default-persona.md            # Eva orchestrator persona
    agent-system.md               # Full orchestration rules, routing, gates
  agents/
    cal.md                        # Architect subagent
    colby.md                      # Engineer subagent
    roz.md                        # QA subagent
    robert.md                     # Product reviewer subagent
    sable.md                      # UX reviewer subagent
    investigator.md               # Poirot (blind investigator) subagent
    distillator.md                # Compression engine subagent
    ellis.md                      # Commit manager subagent
    agatha.md                     # Documentation subagent
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
    pipeline-operations.md        # Operational procedures (model selection, QA flow, feedback loops)
  pipeline/
    pipeline-state.md             # Session recovery state template
    context-brief.md              # Context preservation template
    error-patterns.md             # Error pattern log template
    investigation-ledger.md       # Debug hypothesis tracking template
    last-qa-report.md             # QA report template
    pipeline-config.json          # Branching strategy configuration
  variants/
    branch-lifecycle-trunk-based.md   # Trunk-based branch lifecycle
    branch-lifecycle-github-flow.md   # GitHub Flow branch lifecycle
    branch-lifecycle-gitlab-flow.md   # GitLab Flow branch lifecycle
    branch-lifecycle-gitflow.md       # GitFlow branch lifecycle
```

### Step 3: Install Files

Copy each template to its destination in the user's project, customizing placeholders with the project-specific values gathered in Step 1.

**Installation manifest:**

| Template Source | Destination | Purpose |
|----------------|-------------|---------|
| `source/rules/default-persona.md` | `.claude/rules/default-persona.md` | Eva persona -- always loaded by Claude Code |
| `source/rules/agent-system.md` | `.claude/rules/agent-system.md` | Orchestration rules, routing table, quality gates |
| `source/rules/pipeline-orchestration.md` | `.claude/rules/pipeline-orchestration.md` | Pipeline operations (path-scoped) |
| `source/rules/pipeline-models.md` | `.claude/rules/pipeline-models.md` | Model selection (path-scoped) |
| `source/agents/cal.md` | `.claude/agents/cal.md` | Architect subagent persona |
| `source/agents/colby.md` | `.claude/agents/colby.md` | Engineer subagent persona |
| `source/agents/roz.md` | `.claude/agents/roz.md` | QA subagent persona |
| `source/agents/robert.md` | `.claude/agents/robert.md` | Product reviewer subagent persona |
| `source/agents/sable.md` | `.claude/agents/sable.md` | UX reviewer subagent persona |
| `source/agents/investigator.md` | `.claude/agents/investigator.md` | Blind investigator subagent persona |
| `source/agents/distillator.md` | `.claude/agents/distillator.md` | Compression engine subagent persona |
| `source/agents/ellis.md` | `.claude/agents/ellis.md` | Commit manager subagent persona |
| `source/agents/agatha.md` | `.claude/agents/agatha.md` | Documentation subagent persona |
| `source/commands/pm.md` | `.claude/commands/pm.md` | /pm slash command |
| `source/commands/ux.md` | `.claude/commands/ux.md` | /ux slash command |
| `source/commands/architect.md` | `.claude/commands/architect.md` | /architect slash command |
| `source/commands/debug.md` | `.claude/commands/debug.md` | /debug slash command |
| `source/commands/pipeline.md` | `.claude/commands/pipeline.md` | /pipeline slash command |
| `source/commands/devops.md` | `.claude/commands/devops.md` | /devops slash command |
| `source/commands/docs.md` | `.claude/commands/docs.md` | /docs slash command |
| `source/references/dor-dod.md` | `.claude/references/dor-dod.md` | Quality framework |
| `source/references/retro-lessons.md` | `.claude/references/retro-lessons.md` | Shared lessons (empty template) |
| `source/references/invocation-templates.md` | `.claude/references/invocation-templates.md` | Subagent invocation examples |
| `source/references/pipeline-operations.md` | `.claude/references/pipeline-operations.md` | Operational procedures (model selection, QA, feedback, batch, worktree, context) |
| `source/pipeline/pipeline-state.md` | `docs/pipeline/pipeline-state.md` | Session recovery state |
| `source/pipeline/context-brief.md` | `docs/pipeline/context-brief.md` | Context preservation |
| `source/pipeline/error-patterns.md` | `docs/pipeline/error-patterns.md` | Error pattern tracking |
| `source/pipeline/investigation-ledger.md` | `docs/pipeline/investigation-ledger.md` | Debug hypothesis tracking |
| `source/pipeline/last-qa-report.md` | `docs/pipeline/last-qa-report.md` | QA report persistence |
| `source/pipeline/pipeline-config.json` | `.claude/pipeline-config.json` | Branching strategy configuration |
| `source/variants/branch-lifecycle-{strategy}.md` | `.claude/rules/branch-lifecycle.md` | Branch lifecycle rules (selected variant only) |

**Total: 31 files across 5 directories (before hooks and config).**

### Step 3a: Install Enforcement Hooks

Copy the hook scripts from the plugin's `source/hooks/` directory to `.claude/hooks/`
in the project. These hooks mechanically enforce agent boundaries — they are not
optional and must be installed for the pipeline to function correctly.

| Template Source | Destination | Purpose |
|----------------|-------------|---------|
| `source/hooks/enforce-paths.sh` | `.claude/hooks/enforce-paths.sh` | Blocks Write/Edit outside each agent's allowed file paths |
| `source/hooks/enforce-sequencing.sh` | `.claude/hooks/enforce-sequencing.sh` | Blocks out-of-order agent invocations (e.g., Ellis without Roz QA) |
| `source/hooks/enforce-git.sh` | `.claude/hooks/enforce-git.sh` | Blocks git write operations from main thread (must go through Ellis) |
| `source/hooks/enforcement-config.json` | `.claude/hooks/enforcement-config.json` | Project-specific paths and agent rules |

After copying, make the `.sh` files executable: `chmod +x .claude/hooks/*.sh`

**Customize enforcement-config.json** with the project-specific values from Step 1:
- `pipeline_state_dir`: the pipeline state directory (default: `docs/pipeline`)
- `architecture_dir`: the ADR directory (default: `docs/architecture`)
- `product_specs_dir`: the specs directory (default: `docs/product`)
- `ux_docs_dir`: the UX docs directory (default: `docs/ux`)
- `test_patterns`: array of patterns matching the project's test files (e.g., `[".test.", ".spec.", "/tests/", "conftest"]`)
- `test_command`: full test suite command from Step 1 -- used by Roz for QA verification (e.g., `npm test`, `pytest`)

**Register hooks in `.claude/settings.json`** — merge with existing settings if the
file already exists. Add this hooks section:

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

**Important:** These hooks require `jq` to be installed. Check with `command -v jq`.
If `jq` is not available, tell the user: "Install jq for pipeline enforcement hooks:
`brew install jq` (macOS) or `apt install jq` (Linux)."

**Total with hooks: 35 files across 7 directories.**

### Step 3b: Write Version Marker

After copying all template files, write the current plugin version to `.claude/.atelier-version`:

```bash
# Read version from plugin.json and write to project
grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json" | head -1 | grep -o '"[^"]*"$' | tr -d '"' > .claude/.atelier-version
```

This file is used by the SessionStart hook to detect when the plugin has been updated and the project's pipeline files may be outdated. The hook compares this version against the plugin's current version and notifies the user if an update is available.

**Important:** Always write this file, even on reinstalls. It must reflect the version of the templates that were actually installed.

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

### Step 6: Print Summary and Offer Brain Setup

After installation, print:

1. A count of files installed (35 files across 7 directories)
2. The directory tree showing what was created
3. The configured branching strategy and any CI recommendations
4. A reminder of available slash commands
5. Instructions to start their first pipeline run
6. **Offer to set up the Atelier Brain** -- persistent memory across sessions

**Example summary:**

```
Atelier Pipeline installed successfully.

Files installed: 35
  .claude/rules/       -- 5 files (Eva persona, orchestration rules, pipeline operations, model selection, branch lifecycle)
  .claude/agents/      -- 9 files (Cal, Colby, Roz, Robert, Sable, Poirot, Distillator, Ellis, Agatha)
  .claude/commands/    -- 7 files (/pm, /ux, /architect, /debug, /pipeline, /devops, /docs)
  .claude/references/  -- 4 files (quality framework, retro lessons, invocation templates, pipeline operations)
  .claude/hooks/       -- 4 files (path enforcement, sequencing, git guard, config)
  docs/pipeline/       -- 5 files (state tracking for session recovery)
  .claude/pipeline-config.json -- branching strategy configuration
  .claude/settings.json -- updated with hook registration
  CLAUDE.md            -- updated with pipeline section

Branching strategy: [selected strategy]
  [CI template recommendations -- advisory, printed not written to files:
   - Trunk-based: Run CI on every push to main.
   - GitHub Flow: Run CI on MR events + push to main. Protect main.
   - GitLab Flow: Same + CI on push to staging/production. Protect all env branches.
   - GitFlow: CI on MR events for develop AND main. Protect both.]

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

**Brain setup offer (always ask):**

After printing the summary, ask the user:

> The pipeline is ready. Would you also like to set up the **Atelier Brain**?
> It gives your agents persistent memory across sessions -- architectural
> decisions, user corrections, QA lessons, and rejected alternatives survive
> when you close the terminal. It's optional and the pipeline works fine
> without it.

If the user says yes, invoke the `brain-setup` skill. If no, finish.

### Step 7: Lightweight Reconfig

Users can change branching strategy without full reinstall by asking Eva to
"change branching strategy" or "switch to GitHub Flow".

**Procedure:**
1. Eva reads `.claude/pipeline-config.json`
2. Eva confirms no active pipeline. If active, return error: "Cannot change
   branching strategy mid-pipeline. Complete or abandon the current pipeline
   first."
3. Eva asks the new strategy question (same as Step 1b)
4. Eva rewrites `.claude/pipeline-config.json` and
   `.claude/rules/branch-lifecycle.md` only (installs the selected variant)
5. Eva announces the change and any new CI recommendations

No other files are modified during reconfig.

</procedure>

<gate id="setup-constraints">

## Important Notes

- **Do not overwrite existing files without asking.** If `.claude/rules/` or `.claude/agents/` already exists with content, ask the user whether to merge or replace.
- **Git-track the installed files.** Recommend the user commits the pipeline files so the system persists across clones and team members.
- **Templates are the source of truth.** If a template file is missing from the plugin's templates directory, report which file is missing and skip it rather than generating content from scratch.
- **Validate after install.** After writing all files, verify that Claude Code recognizes the slash commands by listing them. If the rules files are not being loaded, check that they are in `.claude/rules/` (Claude Code auto-loads all files in this directory).

</gate>

<section id="directory-map">

## What Each Directory Does

| Directory | Loaded By | Purpose |
|-----------|-----------|---------|
| `.claude/rules/` | Claude Code automatically (every conversation) | Eva persona and orchestration rules -- always active |
| `.claude/agents/` | Claude Code when subagents are invoked | Agent personas for execution tasks |
| `.claude/commands/` | Claude Code when user types a slash command | Manual agent invocation overrides |
| `.claude/references/` | Agents when they need shared knowledge | Quality framework, lessons, templates |
| `.claude/hooks/` | Claude Code on every tool call (PreToolUse) | Mechanical enforcement of agent boundaries, sequencing, and git operations |
| `docs/pipeline/` | Eva at session start | State recovery, context preservation, error tracking |

</section>
