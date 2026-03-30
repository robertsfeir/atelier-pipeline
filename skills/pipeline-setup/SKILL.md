---
name: pipeline-setup
description: Use when users want to install or set up the atelier-pipeline multi-agent orchestration system in their project. Bootstraps all agent personas, rules, commands, references, and pipeline state files. Works for new and existing projects.
---

# Atelier Pipeline -- Setup

This skill installs the full Atelier Pipeline multi-agent orchestration system into the user's project.

<procedure id="setup">

## Setup Procedure

### Where Files Are Installed

Before gathering project information, understand where the pipeline installs files and how they interact with your project:

| Location | What Goes There | Git Status | Shared With Team? |
|----------|----------------|------------|-------------------|
| `.claude/rules/` | Eva persona, orchestration rules, model selection, branch lifecycle | Project-local, committed to repo | Yes -- team members get the same pipeline rules |
| `.claude/agents/` | Agent persona files (Cal, Colby, Roz, etc.) | Project-local, committed to repo | Yes -- consistent agent behavior across the team |
| `.claude/commands/` | Slash command definitions (/pm, /pipeline, etc.) | Project-local, committed to repo | Yes -- same commands available to all |
| `.claude/references/` | Quality framework, retro lessons, invocation templates | Project-local, committed to repo | Yes -- shared knowledge base |
| `.claude/hooks/` | Enforcement scripts (path, sequencing, git guards) | Project-local, committed to repo | Yes -- same guardrails for everyone |
| `.claude/pipeline-config.json` | Branching strategy, feature flags | Project-local, committed to repo | Yes -- team-wide configuration |
| `.claude/settings.json` | Hook registrations (tells Claude Code to run the hooks) | Project-local, committed to repo | Yes -- hooks activate for all team members |
| `docs/pipeline/` | Pipeline state, context brief, error patterns, QA reports | Project-local, committed to repo | Yes -- session recovery works across machines |
| `CLAUDE.md` | Pipeline section appended to project instructions | Project-local, committed to repo | Yes -- Claude Code reads this automatically |

**Key points:**
- All installed files live inside the project directory -- nothing is written to `~/.claude/` or other user-level locations.
- Everything is designed to be committed to git so team members inherit the pipeline when they clone.
- The plugin itself (installed via `claude plugin add`) is user-level, but the project files it generates are project-level.
- To remove all installed files later, use the `/pipeline-uninstall` skill.

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
    agent-preamble.md             # Shared agent required actions (DoR/DoD, retro, brain)
    qa-checks.md                  # Roz QA check procedures (Tier 1, Tier 2, test spec review, scoped re-run)
    branch-mr-mode.md             # Colby branch/MR procedures for MR-based strategies
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
| `source/references/agent-preamble.md` | `.claude/references/agent-preamble.md` | Shared agent required actions |
| `source/references/qa-checks.md` | `.claude/references/qa-checks.md` | Roz QA check procedures |
| `source/references/branch-mr-mode.md` | `.claude/references/branch-mr-mode.md` | Colby branch/MR procedures |
| `source/references/telemetry-metrics.md` | `.claude/references/telemetry-metrics.md` | Telemetry metric schemas, cost table, alert thresholds |
| `source/pipeline/pipeline-state.md` | `docs/pipeline/pipeline-state.md` | Session recovery state |
| `source/pipeline/context-brief.md` | `docs/pipeline/context-brief.md` | Context preservation |
| `source/pipeline/error-patterns.md` | `docs/pipeline/error-patterns.md` | Error pattern tracking |
| `source/pipeline/investigation-ledger.md` | `docs/pipeline/investigation-ledger.md` | Debug hypothesis tracking |
| `source/pipeline/last-qa-report.md` | `docs/pipeline/last-qa-report.md` | QA report persistence |
| `source/pipeline/pipeline-config.json` | `.claude/pipeline-config.json` | Branching strategy configuration |
| `source/variants/branch-lifecycle-{strategy}.md` | `.claude/rules/branch-lifecycle.md` | Branch lifecycle rules (selected variant only) |

**Total: 34 mandatory files across 5 directories (before hooks and config).**

### Step 3a: Install Enforcement Hooks

Copy the hook scripts from the plugin's `source/hooks/` directory to `.claude/hooks/`
in the project. These hooks mechanically enforce agent boundaries — they are not
optional and must be installed for the pipeline to function correctly.

| Template Source | Destination | Purpose |
|----------------|-------------|---------|
| `source/hooks/enforce-paths.sh` | `.claude/hooks/enforce-paths.sh` | Blocks Write/Edit outside each agent's allowed file paths |
| `source/hooks/enforce-sequencing.sh` | `.claude/hooks/enforce-sequencing.sh` | Blocks out-of-order agent invocations (e.g., Ellis without Roz QA) |
| `source/hooks/enforce-git.sh` | `.claude/hooks/enforce-git.sh` | Blocks git write operations from main thread (must go through Ellis) |
| `source/hooks/warn-dor-dod.sh` | `.claude/hooks/warn-dor-dod.sh` | Warns when Colby/Roz output missing DoR/DoD sections (SubagentStop) |
| `source/hooks/pre-compact.sh` | `.claude/hooks/pre-compact.sh` | Writes compaction marker to pipeline-state.md before context is compacted (PreCompact) |
| `source/hooks/enforcement-config.json` | `.claude/hooks/enforcement-config.json` | Project-specific paths and agent rules |

After copying, make the `.sh` files executable: `chmod +x .claude/hooks/*.sh`

**Validate enforcement-config.json** after copying and customizing. Read the installed `.claude/hooks/enforcement-config.json` and check the following required fields:

| Field | Type | Requirement |
|-------|------|-------------|
| `pipeline_state_dir` | string | Non-empty |
| `architecture_dir` | string | Non-empty |
| `product_specs_dir` | string | Non-empty |
| `ux_docs_dir` | string | Non-empty |
| `test_command` | string | Non-empty -- critical: Roz cannot run tests without this |
| `test_patterns` | array | Non-empty -- at least one pattern required |

Also check `lint_command`: if the field is absent or empty, warn (but do not block) -- Eva's quality gate will fall back to `test_command`.

Print the validation result:
- **All required fields valid:** `Enforcement config validated — all required fields present.`
- **Any required field missing or empty:** `WARNING: enforcement-config.json is missing required fields: [list]. Pipeline enforcement may not work correctly. Re-run /pipeline-setup to fix.`
- **Only lint_command empty/absent:** `NOTE: lint_command is not set — Eva will fall back to test_command for quality checks.`

Do not block installation on validation failure. The warning is informational -- the fix is re-running setup.

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
    ],
    "SubagentStop": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/warn-dor-dod.sh"}]
      }
    ],
    "PreCompact": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-compact.sh"}]
      }
    ]
  }
}
```

**Important:** These hooks require `jq` to be installed. Check with `command -v jq`.
If `jq` is not available, tell the user: "Install jq for pipeline enforcement hooks:
`brew install jq` (macOS) or `apt install jq` (Linux)."

**Total with hooks: 40 mandatory files across 7 directories.**

#### Custom Agent Discovery

The pipeline supports custom agents beyond the core 9. To add a custom agent:

- **Drop a file:** Place any `.md` file into `.claude/agents/` with YAML
  frontmatter (`name`, `description`) and Eva will discover it automatically
  at session start.
- **Paste markdown:** Paste a raw agent definition into the chat and Eva will
  offer to convert it to the pipeline's XML format and write it as a proper
  agent file.
- **Read-only by default:** Discovered agents cannot use Write, Edit, or
  MultiEdit tools. To grant write access, add an explicit case to
  `.claude/hooks/enforce-paths.sh` for the agent's name.

See the "Agent Discovery" section in `agent-system.md` for full details.

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

### Step 6: Print Summary and Offer Optional Features

After installation, print:

1. A count of files installed (40 mandatory files across 7 directories, plus any optional tech-stack references)
2. The directory tree showing what was created
3. The configured branching strategy and any CI recommendations
4. A reminder of available slash commands
5. Instructions to start their first pipeline run
6. **Offer optional features** -- Sentinel security agent, Agent Teams parallel execution, CI Watch automated CI monitoring, Deps Agent dependency scanning, Darwin self-evolving pipeline, and Atelier Brain persistent memory (Steps 6a through 6e)

**Example summary:**

```
Atelier Pipeline installed successfully.

Files installed: 40 (mandatory)
  .claude/rules/       -- 5 files (Eva persona, orchestration rules, pipeline operations, model selection, branch lifecycle)
  .claude/agents/      -- 9 files (Cal, Colby, Roz, Robert, Sable, Poirot, Distillator, Ellis, Agatha)
  .claude/commands/    -- 7 files (/pm, /ux, /architect, /debug, /pipeline, /devops, /docs)
  .claude/references/  -- 8 files (quality framework, retro lessons, invocation templates, pipeline operations, agent preamble, QA checks, branch/MR mode, telemetry metrics)
  .claude/hooks/       -- 6 files (path enforcement, sequencing, git guard, DoR/DoD warning, pre-compact, config)
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

Sentinel security agent: [enabled (Semgrep MCP) | not enabled]
Agent Teams: [enabled (experimental) | not enabled]
CI Watch: [enabled (max retries: N) | not enabled]
Deps agent: [enabled | not enabled]
Darwin: [enabled | not enabled]
Compaction API: PreCompact hook installed for pipeline state preservation

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

### Step 6a: Sentinel Security Agent (Opt-In)

After printing the summary, offer the optional Sentinel security agent:

> Would you also like to enable **Sentinel** -- the security audit agent?
> It uses Semgrep to scan your code for vulnerabilities during QA.
> Requires the Semgrep MCP server (free). Optional -- the pipeline works fine without it.

**If user says yes:**

1. **Clean up legacy Sentinel install** (if present) — previous versions of pipeline-setup installed the deprecated `semgrep-mcp` PyPI package and registered it manually in `.mcp.json`. Check and clean up:
   - Run `command -v semgrep-mcp`. If found: run `pipx uninstall semgrep-mcp` (or `pip3 uninstall semgrep-mcp -y` if pipx is not available). Tell user: "Removed deprecated semgrep-mcp package — Sentinel now uses the official Semgrep plugin."
   - Check `.mcp.json` for a `"semgrep-mcp"` or `"semgrep"` entry that was manually added (command is `"semgrep-mcp"` or command is `"semgrep"` with args `["mcp"]`). If found: remove the entry. If `.mcp.json` is now empty (`{}` or `{"mcpServers": {}}`), delete the file.
   - This cleanup is safe to run even if the user never had the old install — all checks are no-ops when nothing is found.

2. **Check for Semgrep MCP** — verify the Semgrep MCP server is available. Run a quick check: `command -v semgrep && semgrep mcp --version`.
   - If not available, tell user: "Sentinel requires the Semgrep MCP server. Set it up with: `claude mcp add semgrep semgrep mcp` — then re-run `/pipeline-setup` to enable Sentinel." Skip Sentinel setup.
   - If semgrep is installed but not authenticated: tell user to run `semgrep login` first (opens browser, free account at https://semgrep.dev/login). Skip Sentinel setup.

3. Copy `source/agents/sentinel.md` to `.claude/agents/sentinel.md` (with placeholder customization, same as other agent personas).

4. Set `sentinel_enabled: true` in `.claude/pipeline-config.json`.

5. Update installation summary: "Sentinel security agent: enabled (Semgrep MCP)"

**If user says no:** Skip entirely. `sentinel_enabled` remains `false` in `pipeline-config.json`. Print: "Sentinel security agent: not enabled"

**Installation manifest addition (conditional):**

| Template Source | Destination | Install When |
|----------------|-------------|-------------|
| `source/agents/sentinel.md` | `.claude/agents/sentinel.md` | User enables Sentinel in Step 6a |

### Step 6b: Agent Teams Opt-In (Experimental)

After the Sentinel offer (whether user said yes or no), offer the optional Agent Teams feature:

> Would you also like to enable **Agent Teams** -- experimental parallel wave execution?
> When Claude Code's Agent Teams feature is active (`CLAUDE_AGENT_TEAMS=1`), Eva can run
> multiple Colby build units in parallel using git worktrees. This is experimental and the
> pipeline works identically without it.

**If user says yes:**

1. Set `agent_teams_enabled: true` in `.claude/pipeline-config.json`.
2. Print: "Agent Teams: enabled (experimental). Set `CLAUDE_AGENT_TEAMS=1` in your environment
   to activate. The pipeline will fall back to sequential execution if the env var is unset."

**Idempotency:** If `agent_teams_enabled` already exists in `pipeline-config.json` and is `true`, skip the mutation and inform the user: "Agent Teams is already enabled." If it exists and is `false`, confirm with the user before changing.

**If user says no:** Skip entirely. `agent_teams_enabled` remains `false` in
`pipeline-config.json`. Print: "Agent Teams: not enabled"

**No dependency checks needed** -- unlike Sentinel (Semgrep MCP) or Brain (PostgreSQL), Agent Teams
has no external tools to install. The feature is entirely runtime-activated via the env var.

**No installation manifest expansion** -- Agent Teams uses the existing Colby persona
(`.claude/agents/colby.md`). No new files are installed.

### Step 6c: CI Watch Opt-In

After the Agent Teams offer (whether user said yes or no), offer the optional CI Watch feature:

> Would you also like to enable **CI Watch** -- automated post-push CI monitoring?
> After Ellis pushes, Eva watches your CI run and autonomously fixes failures via Roz and Colby,
> pausing for your approval before pushing a fix. Requires `gh` (GitHub) or `glab` (GitLab) CLI.

**Platform CLI gate:** Read `platform_cli` from `.claude/pipeline-config.json`.
- If `platform_cli` is empty or missing, block with message: "CI Watch requires `gh` or `glab`. Configure a platform CLI first (run `/pipeline-setup` and set a platform)." Skip CI Watch setup.
- If `platform_cli` is set, continue.

**If user says yes:**

1. **Check CLI authentication:** run `gh auth status` (GitHub) or `glab auth status` (GitLab).
   - If auth check fails, tell user: "CI Watch requires an authenticated `{platform_cli}` session. Run `{platform_cli} auth login` first, then re-run `/pipeline-setup` to enable CI Watch." Skip CI Watch setup.

2. **Ask max retries:** "How many times should the fix cycle retry before stopping? (default: 3, minimum: 1)"
   - Accept an integer >= 1. If user presses Enter, use 3.

3. **Set config values:** in `.claude/pipeline-config.json`:
   - `ci_watch_enabled: true`
   - `ci_watch_max_retries: N` (the value from step 2)

4. **Compute and store platform commands** in `.claude/pipeline-config.json`:
   - `ci_watch_poll_command`: `gh run list --commit {sha} --json status,conclusion,url,databaseId --limit 1` (GitHub) or `glab ci list --branch {branch} -o json | head -1` (GitLab)
   - `ci_watch_log_command`: `gh run view {run_id} --log-failed | tail -200` (GitHub) or `glab ci trace {job_id} | tail -200` (GitLab)

5. Print: "CI Watch: enabled (max retries: N)"

**Idempotency:** If `ci_watch_enabled` already exists in `pipeline-config.json` and is `true`, skip the mutation and inform the user: "CI Watch is already enabled (max retries: {current_value})." If it exists and is `false`, confirm with the user before changing.

**If user says no:** Skip entirely. `ci_watch_enabled` remains `false` in `pipeline-config.json`. Print: "CI Watch: not enabled"

**No new agent files installed** -- CI Watch uses existing Roz, Colby, and Ellis personas.

### Step 6d: Deps Agent Opt-In

After the CI Watch offer (whether user said yes or no), offer the optional Deps agent:

> Would you also like to enable the **Deps agent** -- predictive dependency management?
> It scans your dependencies for CVEs, checks for outdated packages, and predicts
> breakage risk before you upgrade. No external tools required beyond your existing
> package managers. Optional -- the pipeline works fine without it.

**If user says yes:**

1. Set `deps_agent_enabled: true` in `.claude/pipeline-config.json`.
2. Copy `source/agents/deps.md` to `.claude/agents/deps.md`.
3. Copy `source/commands/deps.md` to `.claude/commands/deps.md`.
4. Print: "Deps agent: enabled. Use /deps to scan your dependencies."

**Idempotency:** If `deps_agent_enabled` already exists in `pipeline-config.json`
and is `true`, skip mutation and inform: "Deps agent is already enabled." If it
exists and is `false`, confirm before changing. If the key is absent (missing from
the config), treat as `false` (default false) and proceed with the offer.

**If user says no:** Skip entirely. `deps_agent_enabled` remains `false`.
Print: "Deps agent: not enabled"

**Installation manifest addition (conditional):**

| Template Source | Destination | Install When |
|----------------|-------------|-------------|
| `source/agents/deps.md` | `.claude/agents/deps.md` | User enables Deps in Step 6d |
| `source/commands/deps.md` | `.claude/commands/deps.md` | User enables Deps in Step 6d |

### Step 6e: Darwin Self-Evolving Pipeline (Opt-In)

After the Deps Agent offer (whether user said yes or no), offer the optional Darwin agent:

> Would you also like to enable **Darwin** -- the self-evolving pipeline engine?
> It analyzes your pipeline telemetry to identify underperforming agents and proposes
> structural fixes (persona edits, rule changes, enforcement additions) backed by evidence.
> Requires persistent memory with 5+ pipelines of telemetry data. Optional -- the
> pipeline works fine without it.

**If user says yes:**

1. Set `darwin_enabled: true` in `.claude/pipeline-config.json`.
2. Copy `source/agents/darwin.md` to `.claude/agents/darwin.md`.
3. Copy `source/commands/darwin.md` to `.claude/commands/darwin.md`.
4. Print: "Darwin: enabled. Use /darwin to analyze pipeline performance, or Darwin will auto-trigger when degradation is detected."

**Idempotency:** If `darwin_enabled` already exists in `pipeline-config.json`
and is `true`, skip mutation and inform: "Darwin is already enabled." If it
exists and is `false`, confirm before changing. If the key is absent (missing from
the config), treat as `false` (default false) and proceed with the offer.

**If user says no:** Skip entirely. `darwin_enabled` remains `false`.
Print: "Darwin: not enabled"

**Dependency:** Darwin requires the Atelier Brain for telemetry data. If no
brain is configured (`.claude/brain-config.json` absent), inform user: "Darwin
requires the Atelier Brain for telemetry data. Set up brain first, then re-run
setup."

**Installation manifest addition (conditional):**

| Template Source | Destination | Install When |
|----------------|-------------|-------------|
| `source/agents/darwin.md` | `.claude/agents/darwin.md` | User enables Darwin in Step 6e |
| `source/commands/darwin.md` | `.claude/commands/darwin.md` | User enables Darwin in Step 6e |

**Brain setup offer (always ask):**

After the Darwin offer (whether user said yes or no), ask the user:

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
