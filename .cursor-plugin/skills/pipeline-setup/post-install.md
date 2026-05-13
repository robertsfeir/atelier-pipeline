### Step 5: Write CLAUDE.md

**If the project already has a `CLAUDE.md` file:**

1. Read the existing `CLAUDE.md`.
2. Extract any project-specific content that the pipeline does not cover. Content to carry forward includes: tech stack, language/framework versions, test commands, lint/typecheck commands, build commands, file/directory structure, repo conventions, coding style rules, database patterns, CI/CD notes, environment setup, and any other project-specific facts. Do NOT carry forward content the pipeline now owns: agent behavior instructions, commit workflow, pipeline/QA process, or any "how Claude should behave" sections.
3. Rename the existing file: `mv CLAUDE.md CLAUDE.md.orig` (use the Bash tool).
4. Write a new `CLAUDE.md` containing: (a) any carried-forward project-specific sections, followed by (b) the pipeline section below.

**If no `CLAUDE.md` exists:** create one with the pipeline section only.

**Pipeline section:**

```markdown
## Pipeline System (Atelier Pipeline)

This project uses a multi-agent orchestration pipeline for structured development.

**Agents:** Eva (orchestrator), Robert (product), Sable (UX), Sarah (architect), Colby (engineer), Poirot, Agatha (docs), Ellis (commit)

**Commands:** /pm, /ux, /architect, /pipeline, /devops, /docs

**Pipeline state:** docs/pipeline/ -- Eva reads this at session start for recovery

**Key rules:**
- Colby writes tests when Sarah names a failure mode before Colby builds ()
- Poirot verifies every Colby output (no self-review)
- Ellis commits (Eva never runs git on code)
- Full test suite between work units
```

### Step 6: Print Summary and Offer Optional Features

After installation, print:

1. A count of files installed (37 mandatory files across 7 directories, plus any optional tech-stack references)
2. The directory tree showing what was created
3. The configured branching strategy and any CI recommendations
4. A reminder of available slash commands
5. Instructions to start their first pipeline run
6. **Offer optional features** -- Sentinel security agent, Agent Teams parallel execution, CI Watch automated CI monitoring, Claude Code Agent Resume prerequisite, and Atelier Brain persistent memory (Steps 6a through 6d)

**Example summary:**

```
Atelier Pipeline installed successfully.

Files installed: 36 (mandatory)
  .claude/rules/       -- 5 files (Eva persona, orchestration rules, pipeline operations, model selection, branch lifecycle)
  .claude/agents/      -- 9 files (Sarah, Colby, Robert, Sable, Poirot, Distillator, Ellis, Agatha)
  .claude/commands/    -- 6 files (/pm, /ux, /architect, /pipeline, /devops, /docs)
  .claude/references/  -- 6 files (quality framework, invocation templates, pipeline operations, agent preamble, branch/MR mode, telemetry metrics)
  .claude/hooks/       -- 6 files (path enforcement, sequencing, git guard, DoR/DoD warning, pre-compact, config)
  docs/pipeline/       -- 4 files (state tracking for session recovery)
  .claude/pipeline-config.json -- branching strategy configuration
  .claude/settings.json -- updated with hook registration
  CLAUDE.md            -- written fresh (project-specific content carried forward from CLAUDE.md.orig)

Branching strategy: [selected strategy]
  [CI template recommendations -- advisory, printed not written to files:
   - Trunk-based: Run CI on every push to main.
   - GitHub Flow: Run CI on MR events + push to main. Protect main.
   - GitLab Flow: Same + CI on push to staging/production. Protect all env branches.
   - GitFlow: CI on MR events for develop AND main. Protect both.]

Sentinel security agent: [enabled (Semgrep MCP) | not enabled]
Agent Teams: [enabled (experimental) | not enabled]
CI Watch: [enabled (max retries: N) | not enabled]
Compaction API: PreCompact hook installed for pipeline state preservation

Available commands:
  /pm          -- Feature discovery and product spec (Robert)
  /ux          -- UI/UX design (Sable)
  /architect   -- Architecture and ADR production (Sarah)
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

3. Assemble `source/shared/agents/sentinel.md` + `source/claude/agents/sentinel.frontmatter.yml` to `.claude/agents/sentinel.md` (with placeholder customization, same as other agent personas).

4. Set `sentinel_enabled: true` in `.claude/pipeline-config.json`.

5. Update installation summary: "Sentinel security agent: enabled (Semgrep MCP)"

**If user says no:** Skip entirely. `sentinel_enabled` remains `false` in `pipeline-config.json`. Print: "Sentinel security agent: not enabled"

**Installation manifest addition (conditional):**

| Template Source | Destination | Install When |
|----------------|-------------|-------------|
| `source/shared/agents/sentinel.md` + `source/claude/agents/sentinel.frontmatter.yml` | `.claude/agents/sentinel.md` | User enables Sentinel in Step 6a (overlay assembly) |

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
> After Ellis pushes, Eva watches your CI run and autonomously fixes failures via Poirot and Colby,
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

**No new agent files installed** -- CI Watch uses existing Poirot, Colby, and Ellis personas.

### Step 6d: Claude Code Agent Resume Prerequisite (Experimental)

After the CI Watch offer (whether user said yes or no), if the user is running Claude Code, offer one more experimental flag — ensure Claude Code's experimental
subagent-resume flag is enabled. This unlocks the `SendMessage` tool, which
the Agent tool advertises as the standard way to resume a spawned subagent
("use SendMessage with to: '<agentId>' to continue this agent"). Without
the flag, `SendMessage` is absent from the tool registry and every
follow-up to a subagent respawns a fresh agent that re-reads context from
scratch.

This is a Claude Code regression currently tracked at
[anthropics/claude-code#42737](https://github.com/anthropics/claude-code/issues/42737).
The atelier pipeline depends on cheap subagent resume for Sarah ADR
revisions, Colby rework cycles, and Poirot scoped re-runs.

**Check `~/.claude/settings.json` for the existing env var:**

```bash
jq -r '.env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS // empty' ~/.claude/settings.json
```

**If the value is already `1`, skip to the Brain setup offer.** (Idempotency.)

**Otherwise, always apply idempotently via jq:**

```bash
jq '. + {env: ((.env // {}) + {CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"})}' \
  ~/.claude/settings.json > ~/.claude/settings.json.tmp && \
  mv ~/.claude/settings.json.tmp ~/.claude/settings.json
```

Confirm: "`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set in `~/.claude/settings.json`. Restart Claude
Code for the change to take effect."

**No installation manifest expansion** -- this is a user-settings mutation,
not a pipeline file install.

**Brain plugin offer (conditional ask):**

After the Claude Code Agent Resume Prerequisite (Step 6d) offer (whether user said yes or no), check whether the user already has a brain plugin registered:

1. Probe ToolSearch for any tool name matching `mcp__*mybrain*` or `mcp__*atelier-brain__*` (suffix-match, so any plugin prefix is acceptable per ADR-0055).
2. If at least one match resolves: the user already has a brain plugin registered (either mybrain via the migration wizard in Step 0f, or an externally-installed equivalent). Print "Brain plugin already registered — skipping brain offer." Finish.
3. If no match resolves: the user has no brain plugin. Ask:

> The pipeline is ready. Would you also like to install the **mybrain** plugin?
> mybrain gives your agents persistent memory across sessions — architectural
> decisions, user corrections, QA lessons, and rejected alternatives survive
> when you close the terminal. It's optional and the pipeline works fine
> without it (per ADR-0055, the brain is now a separate plugin).

If the user says yes: print the install command and point them to the mybrain plugin's documentation:

```
Install mybrain in another terminal (or in this one after I finish):

  claude plugin install <mybrain-source-url>

See the mybrain plugin's README for the exact source URL. Once installed,
run `/brain-setup` from the mybrain plugin to configure the database
connection and provider settings.
```

If the user says no: print "OK — run `/pipeline-setup` again anytime if you change your mind. The pipeline runs fine without a brain plugin." Finish.

The pipeline-setup skill itself does NOT install or configure a brain — that responsibility moved to the standalone mybrain plugin in Phase 3 of ADR-0055.

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
