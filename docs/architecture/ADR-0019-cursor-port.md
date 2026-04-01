# ADR-0019: Port Atelier Pipeline to Cursor IDE

## Status

Proposed

## DoR: Requirements Extracted

**Source:** `docs/product/cursor-port.md` (Robert's spec), brain research (19bee288, b6f772c2, e099e4dc, a96a961a)

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| 1 | Single repo, dual-target -- same source files serve both Claude Code and Cursor | Spec R-1 | cursor-port.md:6 |
| 2 | Full parity -- all 12 agents, enforcement hooks, brain MCP, all commands | Spec R-2 | cursor-port.md:7 |
| 3 | .cursor-plugin/plugin.json manifest with valid Cursor Marketplace format | Spec AC-1 | cursor-port.md:101 |
| 4 | Cursor auto-discovers all 12 agent personas from agents/ | Spec AC-2 | cursor-port.md:102 |
| 5 | Cursor auto-discovers all rules from rules/ (always-apply and path-scoped) | Spec AC-3 | cursor-port.md:103 |
| 6 | Cursor auto-discovers all commands from commands/ | Spec AC-4 | cursor-port.md:104 |
| 7 | hooks/hooks.json registers all enforcement hooks with failClosed: true | Spec AC-5 | cursor-port.md:105 |
| 8 | mcp.json registers brain MCP server | Spec AC-6 | cursor-port.md:106 |
| 9 | Enforcement hooks block path violations | Spec AC-7 | cursor-port.md:107 |
| 10 | Enforcement hooks block sequencing violations | Spec AC-8 | cursor-port.md:108 |
| 11 | Enforcement hooks block git ops from main thread | Spec AC-9 | cursor-port.md:109 |
| 12 | Eva orchestration works via always-apply rules | Spec AC-10 | cursor-port.md:110 |
| 13 | /pipeline-setup skill configures project for Cursor | Spec AC-11 | cursor-port.md:111 |
| 14 | Brain MCP connects and brain tools work | Spec AC-12 | cursor-port.md:112 |
| 15 | Existing Claude Code files unchanged -- zero delta | Spec AC-13 | cursor-port.md:113 |
| 16 | source/ directory is shared -- not duplicated | Spec AC-14 | cursor-port.md:114 |
| 17 | Platform detection in hook scripts (CURSOR_PROJECT_DIR / CLAUDE_PROJECT_DIR) | Spec NFR | cursor-port.md:146 |
| 18 | failClosed: true for enforcement hooks | Spec edge cases | cursor-port.md:91 |
| 19 | AGENTS.md as Cursor equivalent of CLAUDE.md | Spec R-8 | cursor-port.md:8 |
| 20 | /pipeline-setup adapted for Cursor target | Spec US-6 | cursor-port.md:66-68 |
| 21 | No-repo support: /pipeline-setup asks git availability before branching strategy, degrades gracefully when git unavailable | User decision | context-brief.md:23 |

**Retro risks:**
- Lesson #005 (behavioral constraints ignored): Enforcement hooks are the only reliable constraint. Cursor port must preserve all hook enforcement -- no behavior-only fallback.
- Brain research confirms Cursor hooks support `failClosed: true`, which is strictly better than Claude Code's fail-open default. Adopt it.

---

## Spec Challenge

**The spec assumes Cursor's hook stdin JSON format uses the same field names (`tool_name`, `tool_input.file_path`, `agent_type`, `agent_id`, `tool_input.subagent_type`, `tool_input.command`) as Claude Code.** If this is wrong, the design fails because all 4 enforcement scripts (enforce-paths.sh, enforce-sequencing.sh, enforce-pipeline-activation.sh, enforce-git.sh) parse these exact field names via `jq -r '.tool_name // empty'` etc. The scripts would extract empty strings, fall through every check, and exit 0 -- failing open. No enforcement would exist.

**Mitigation:** Step 1 includes a mandatory stdin format validation test. If field names differ, we add a normalization shim (a small wrapper script that translates Cursor's JSON to the expected format before piping to the real script). This adds one file but preserves all shared logic.

**SPOF:** The hook stdin format compatibility. If Cursor's JSON schema is different, all four enforcement hooks silently fail open. **Failure mode:** Agents write wherever they want, Ellis commits without QA, Eva runs git directly. **Graceful degradation:** Behavioral rules in markdown still instruct agents, but per retro lesson #005, these are unreliable. The system would function but without guardrails -- unacceptable for production. This is why Step 1 validates format before proceeding.

## Anti-Goals

**Anti-goal: Cursor Marketplace publication.** Reason: The spec explicitly scopes this to feature branch testing by 3+ colleagues. Publication requires Cursor's manual review process, open-source compliance checks, and marketplace metadata that are premature before tester validation. Revisit: After 3+ testers complete a full pipeline run and report zero blockers.

**Anti-goal: Cursor-specific features not in Claude Code (prompt hooks, Cursor-native Agent Teams differences, Cursor-specific model routing).** Reason: The goal is feature parity, not feature expansion. Cursor may offer capabilities Claude Code lacks, but exploiting them creates maintenance divergence. Revisit: After dual-target is stable for 2+ releases and users request Cursor-specific capabilities.

**Anti-goal: Modifying existing Claude Code plugin structure (.claude-plugin/, .claude/, CLAUDE.md).** Reason: Additive-only constraint from the user. The Cursor port must not introduce any regression risk to the existing working plugin. Revisit: Never -- this is a hard constraint, not a deferral.

## Context

Atelier Pipeline currently ships as a Claude Code plugin only. Cursor IDE has near-identical primitives (rules, agents, commands, hooks, MCP, plugins) and a growing marketplace. No production-grade multi-agent orchestration pipeline exists for Cursor. Users who prefer Cursor or work in mixed-IDE teams cannot use atelier-pipeline.

The codebase already uses a dual-tree architecture: `source/` contains templates, `.claude/` contains installed copies. The Cursor port extends this to a triple concern: `source/` (shared truth), `.claude-plugin/` (Claude Code packaging), `.cursor-plugin/` (Cursor packaging). The `source/` directory is never duplicated -- both plugin manifests reference it.

### Key Architectural Observations

1. **Hook scripts already use fallback project dir detection.** All enforcement scripts use `PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"`. Cursor provides `CURSOR_PROJECT_DIR` as an alias. The scripts need one line changed to check `CURSOR_PROJECT_DIR` first, then `CLAUDE_PROJECT_DIR`, then fallback.

2. **Brain MCP server has zero platform coupling.** `brain/server.mjs` and `brain/lib/config.mjs` do not reference `CLAUDE_PROJECT_DIR` or any Claude-specific env vars. The MCP registration in `.mcp.json` uses `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`, but Cursor's mcp.json uses the same flat format with its own env vars.

3. **Plugin.json is the only Claude-specific packaging artifact.** Everything else (rules, agents, commands, hooks, skills) uses standard markdown and shell scripts.

4. **Cursor's hooks.json is structurally different from Claude Code's settings.json hooks.** Claude Code registers hooks in `.claude/settings.json` per event type with matchers. Cursor uses a dedicated `hooks/hooks.json` file with a different schema (array of hook objects with `event`, `matcher`, `command`, `failClosed` fields).

5. **Cursor rules use `.mdc` extension with YAML frontmatter.** Claude Code rules are plain `.md` in `.claude/rules/`. Cursor rules are `.mdc` in `rules/` with frontmatter fields: `description`, `alwaysApply`, `globs`. This means rules cannot be shared as-is -- they need frontmatter wrappers.

### Blast Radius

Files/modules affected by this change:

| File/Module | Change Type | Impact |
|-------------|-------------|--------|
| `source/hooks/enforce-paths.sh` | Modify (1 line) | Add CURSOR_PROJECT_DIR to fallback chain |
| `source/hooks/enforce-sequencing.sh` | Modify (1 line) | Add CURSOR_PROJECT_DIR to fallback chain |
| `source/hooks/enforce-pipeline-activation.sh` | Modify (1 line) | Add CURSOR_PROJECT_DIR to fallback chain |
| `source/hooks/pre-compact.sh` | Modify (1 line) | Add CURSOR_PROJECT_DIR to fallback chain |
| `.cursor-plugin/plugin.json` | Create | Cursor Marketplace manifest |
| `.cursor-plugin/marketplace.json` | Create | Multi-plugin marketplace config |
| `.cursor-plugin/rules/` | Create (6 files) | .mdc wrappers referencing source/ content |
| `.cursor-plugin/agents/` | Create (12 files) | Agent frontmatter wrappers for Cursor |
| `.cursor-plugin/commands/` | Create (10+ files) | Command files for Cursor auto-discovery |
| `.cursor-plugin/hooks/hooks.json` | Create | Cursor hook registration |
| `.cursor-plugin/mcp.json` | Create | Brain MCP registration for Cursor |
| `AGENTS.md` | Create | Cursor project instructions (equivalent of CLAUDE.md) |
| `skills/pipeline-setup/SKILL.md` | Modify | Add Cursor target detection and .cursor/ installation path; add no-repo detection flow before branching strategy |
| `source/pipeline/pipeline-config.json` | Modify | Add `git_available: true` field to template |
| `source/hooks/enforce-git.sh` | Modify (conditional) | No-op when `git_available: false` in pipeline-config.json |
| `source/hooks/enforce-sequencing.sh` | Modify (conditional) | Skip Ellis gate when `git_available: false` |
| `source/rules/default-persona.md` | Noted | Eva boot sequence skips git-related checks when `git_available: false` (behavioral, no file change needed -- Eva reads config) |
| `scripts/check-updates.sh` | Modify | Support .cursor/.atelier-version alongside .claude/.atelier-version |
| `.claude-plugin/plugin.json` | **No change** | Verified: additive-only constraint |
| `.claude/settings.json` | **No change** | Verified: additive-only constraint |
| `.mcp.json` | **No change** | Verified: additive-only constraint |

**Consumers of modified hook scripts (blast radius of env var change):**
- `.claude/settings.json` hooks -> calls `enforce-paths.sh`, `enforce-sequencing.sh`, `enforce-pipeline-activation.sh`, `enforce-git.sh`, `pre-compact.sh`, `warn-dor-dod.sh`
- `.cursor-plugin/hooks/hooks.json` -> calls the same scripts
- Both paths are backwards-compatible because the change uses the existing `:-` fallback pattern

**Grep verification of all CLAUDE_PROJECT_DIR references in hooks:**
- `source/hooks/enforce-paths.sh:39` -- `PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-...}"`
- `source/hooks/enforce-sequencing.sh:37` -- `PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-...}"`
- `source/hooks/enforce-pipeline-activation.sh:43` -- `PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-...}"`
- `source/hooks/pre-compact.sh:10` -- `STATE_FILE="${CLAUDE_PROJECT_DIR:-$PWD}/..."`
- `source/hooks/enforce-git.sh` -- Does NOT reference CLAUDE_PROJECT_DIR (no change needed)
- `source/hooks/warn-dor-dod.sh` -- Does NOT reference CLAUDE_PROJECT_DIR (no change needed)

## Decision

**Create a Cursor plugin alongside the existing Claude Code plugin, sharing the same `source/` templates.** The `.cursor-plugin/` directory contains Cursor-specific packaging (plugin.json, hooks.json, mcp.json) plus thin wrapper files that adapt `source/` content for Cursor's format requirements (`.mdc` frontmatter for rules, agent frontmatter for agents). Hook shell scripts are shared -- both plugins call the same `source/hooks/*.sh` scripts. The 4 hook scripts that reference `CLAUDE_PROJECT_DIR` get a one-line change to also check `CURSOR_PROJECT_DIR`.

### Architecture

```
atelier-pipeline/
  source/                          # Shared source of truth (unchanged role)
    rules/   agents/   commands/   hooks/   references/   pipeline/   variants/
  .claude-plugin/                  # Claude Code packaging (unchanged)
    plugin.json   marketplace.json
  .cursor-plugin/                  # NEW: Cursor packaging
    plugin.json                    # Cursor Marketplace manifest
    marketplace.json               # Multi-plugin config
    rules/                         # .mdc wrappers with frontmatter
      default-persona.mdc          # alwaysApply: true, includes source/rules/default-persona.md
      agent-system.mdc             # alwaysApply: true, includes source/rules/agent-system.md
      pipeline-orchestration.mdc   # alwaysApply: false, globs: ["docs/pipeline/**"]
      pipeline-models.mdc          # alwaysApply: false, globs: ["docs/pipeline/**"]
      branch-lifecycle.mdc         # alwaysApply: false, globs: ["docs/pipeline/**"]
      (references as non-always rules)
    agents/                        # .md with Cursor frontmatter
      cal.md  colby.md  roz.md  ellis.md  agatha.md  robert.md
      sable.md  investigator.md  distillator.md
      sentinel.md  deps.md  darwin.md
    commands/                      # Same .md format (compatible)
      pm.md  ux.md  architect.md  debug.md  pipeline.md
      devops.md  docs.md  deps.md  darwin.md  telemetry-hydrate.md
    hooks/
      hooks.json                   # Cursor hook registration
    skills/                        # Symlinks or copies of skills/
      pipeline-setup/SKILL.md
      brain-setup/SKILL.md
      brain-hydrate/SKILL.md
      pipeline-overview/SKILL.md
      dashboard/SKILL.md
      brain-uninstall/SKILL.md
      pipeline-uninstall/SKILL.md
    mcp.json                       # Brain MCP for Cursor
  brain/                           # Unchanged -- MCP server
  skills/                          # Unchanged -- shared skill definitions
  AGENTS.md                        # NEW: Cursor project instructions
```

### Key Design Decisions

**D1: Rules as .mdc wrappers, not duplicated content.** Cursor rules require `.mdc` extension with YAML frontmatter (`description`, `alwaysApply`, `globs`). Rather than duplicating the full markdown content, each `.mdc` file contains the frontmatter plus an `@include` or inline copy of the source content. Since Cursor rules auto-discovery reads the file content directly, we include the full content (copied at plugin build/release time or included as the body after frontmatter). This means `.cursor-plugin/rules/*.mdc` files contain frontmatter + the same content as `source/rules/*.md`. Updates to `source/` must be propagated to `.cursor-plugin/rules/` -- a build step or manual sync.

**D2: Agent files need Cursor-specific frontmatter.** Cursor agents use frontmatter fields: `name`, `description`, `model` (optional), `readonly` (optional), `is_background` (optional). Claude Code agents currently have no frontmatter (or have it in the XML prompt structure). The `.cursor-plugin/agents/` files add this frontmatter while preserving the full persona content from `source/agents/`.

**D3: Commands are format-compatible.** Both Claude Code and Cursor use the same markdown format for commands. The `.cursor-plugin/commands/` files can be direct copies or symlinks from `source/commands/`.

**D4: hooks.json references source/hooks/ scripts directly.** The hooks.json file in `.cursor-plugin/hooks/` points to `source/hooks/*.sh` using relative paths from the plugin root. This means the exact same shell scripts run for both platforms.

**D5: AGENTS.md is a thin Cursor-specific project instructions file.** Cursor reads `AGENTS.md` the way Claude Code reads `CLAUDE.md`. It contains the same pipeline section content tailored for Cursor's context. This file is additive -- CLAUDE.md is untouched.

**D6: mcp.json uses Cursor env vars.** Cursor provides `CURSOR_PLUGIN_ROOT` and `CURSOR_PLUGIN_DATA` as equivalents of `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`. The `.cursor-plugin/mcp.json` uses these Cursor-specific vars.

**D7: /pipeline-setup detects target platform.** The setup skill detects whether it is running in Claude Code or Cursor (via `CLAUDE_PROJECT_DIR` vs `CURSOR_PROJECT_DIR` env var presence) and installs to `.claude/` or `.cursor/` accordingly. The hook registration goes to `.claude/settings.json` or `.cursor/settings.json` respectively.

## Alternatives Considered

### Alternative A: Symlink-based sharing (Rejected)

Use symlinks from `.cursor-plugin/rules/` to `source/rules/` etc.

**Pros:** Zero duplication. Changes to source/ propagate instantly.
**Cons:** (1) Cursor plugin auto-discovery may not follow symlinks. (2) Rules need `.mdc` extension with frontmatter -- can't symlink a `.md` to serve as `.mdc`. (3) Git handles symlinks poorly on Windows. (4) Plugin marketplace packaging may not resolve symlinks.

**Decision:** Rejected. Format differences between Claude Code and Cursor (`.md` vs `.mdc`, different frontmatter requirements) make symlinks impractical for rules. Commands could use symlinks but mixing strategies adds complexity.

### Alternative B: Build script that generates .cursor-plugin/ from source/ (Considered)

A build step (shell script or Node.js) that reads `source/` and generates `.cursor-plugin/` with proper frontmatter and formatting.

**Pros:** Single source of truth with mechanical guarantee. Changes to source/ automatically propagate via build. No risk of drift.
**Cons:** (1) Adds a build step to a project that currently has none. (2) Build artifacts in git are a maintenance burden. (3) Plugin marketplace may expect committed files, not generated ones. (4) Adds complexity for contributors.

**Decision:** Deferred. This is the right long-term solution but premature for a feature branch validation. Start with manually-maintained `.cursor-plugin/` files (Step 1-5), then add a build script as a follow-up if drift becomes a problem. The file count is manageable (~30 files) and changes to source/ are infrequent.

### Alternative C: Single plugin directory with platform detection (Rejected)

One plugin directory that serves both Claude Code and Cursor, with runtime detection.

**Pros:** True single source. No sync needed.
**Cons:** (1) Claude Code reads `.claude-plugin/plugin.json`, Cursor reads `.cursor-plugin/plugin.json` -- different discovery paths, impossible to share. (2) Rules format differs (`.md` vs `.mdc`). (3) Hook registration differs (settings.json vs hooks.json). (4) Plugin manifests have different schemas.

**Decision:** Rejected. Platform differences make a single directory impossible.

## Consequences

**Positive:**
- First-to-market multi-agent orchestration pipeline for Cursor
- Zero changes to existing Claude Code users -- purely additive
- Shared hook scripts mean enforcement logic is maintained in one place
- Brain MCP server works unchanged on both platforms

**Negative:**
- ~30 new files in `.cursor-plugin/` that must stay in sync with `source/`
- Rules content is duplicated (source/ .md + .cursor-plugin/ .mdc) -- drift risk until build script is added
- /pipeline-setup skill grows in complexity with platform detection logic and no-repo branching

**Risk: Hook stdin format incompatibility.** If Cursor's hook stdin JSON uses different field names than Claude Code's, all enforcement fails silently. Step 1 validates this early. If incompatible, a normalization shim adds one file and a ~5 line wrapper per hook invocation in hooks.json.

**Risk: .mdc frontmatter evolution.** Cursor may change its `.mdc` format or add required fields. The wrapper files are thin enough to update quickly, but this is ongoing maintenance.

---

## Implementation Plan

### Step 1: Hook Platform Compatibility (foundation)

**After this step, I can:** verify that enforcement hooks work in Cursor by running them with Cursor's env vars and confirming they parse stdin correctly.

**Files to modify:**
1. `source/hooks/enforce-paths.sh` -- Add `CURSOR_PROJECT_DIR` to fallback chain
2. `source/hooks/enforce-sequencing.sh` -- Add `CURSOR_PROJECT_DIR` to fallback chain
3. `source/hooks/enforce-pipeline-activation.sh` -- Add `CURSOR_PROJECT_DIR` to fallback chain
4. `source/hooks/pre-compact.sh` -- Add `CURSOR_PROJECT_DIR` to fallback chain

**Change detail:** In each script, change:
```bash
# Before
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# After
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
```

For `pre-compact.sh`:
```bash
# Before
STATE_FILE="${CLAUDE_PROJECT_DIR:-$PWD}/docs/pipeline/pipeline-state.md"

# After
STATE_FILE="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}/docs/pipeline/pipeline-state.md"
```

**Acceptance criteria:**
- AC-1: All 4 hook scripts resolve project root from `CURSOR_PROJECT_DIR` when set
- AC-2: All 4 hook scripts still resolve from `CLAUDE_PROJECT_DIR` when `CURSOR_PROJECT_DIR` is unset (backwards compatibility)
- AC-3: All 4 hook scripts still use `$(cd "$SCRIPT_DIR/../.." && pwd)` fallback when neither env var is set
- AC-4: Existing bats tests pass unchanged (no regression)
- AC-5: `enforce-git.sh` and `warn-dor-dod.sh` are NOT modified (they don't use the env var)

**Estimated complexity:** Low (4 one-line changes + tests)

---

### Step 1b: No-Repo Support in Pipeline Setup

**After this step, I can:** run /pipeline-setup in a project with no git repository and get a gracefully degraded pipeline (no Ellis, no Poirot, no branching strategy, no CI Watch) with clear messaging about what works and what does not.

**Files to modify:**
1. `skills/pipeline-setup/SKILL.md` -- Add git availability question to Step 1, before branching strategy
2. `source/pipeline/pipeline-config.json` -- Add `git_available: true` field to template
3. `source/hooks/enforce-git.sh` -- Early exit (no-op) when `git_available: false` in pipeline-config.json
4. `source/hooks/enforce-sequencing.sh` -- Skip Ellis gate when `git_available: false`

**Change detail:**

**SKILL.md Step 1 addition (insert before Step 1b: Branching Strategy Selection):**

Add a new question between the existing Step 1 (Gather Project Information) and Step 1b (Branching Strategy Selection). Rename existing Step 1b to Step 1c. The new Step 1b:

```markdown
### Step 1b: Git Repository Detection

Before asking about branching strategy, determine git availability.

1. Run `git rev-parse --git-dir 2>/dev/null`. If this succeeds, set `git_available: true` and proceed to Step 1c (Branching Strategy).

2. If no git repo detected, inform the user:

> This project does not have a git repository.
>
> **What still works without git:**
> Eva (orchestrator), Robert (product), Sable (UX), Cal (architect), Colby (engineer), Roz (QA), Sentinel (security), Agatha (docs), Brain (memory), enforcement hooks
>
> **What is unavailable without git:**
> Poirot (blind review -- needs git diff), Ellis (commit manager -- needs git), CI Watch (needs git + platform CLI), branch lifecycle management
>
> Would you like to create a git repository now?

3. **If user says yes:** Run `git init`, create a sensible `.gitignore` (node_modules/, .env, dist/, etc. based on detected tech stack), run `git add .gitignore && git commit -m "Initial commit"`. Set `git_available: true`, proceed to Step 1c (Branching Strategy).

4. **If user says no:** Set `git_available: false` in pipeline-config.json. Skip Step 1c (Branching Strategy Selection) entirely. Skip platform CLI detection. Skip CI Watch offer (Step 6c). Log: "Git unavailable -- skipping branching strategy, platform CLI, and CI Watch configuration."
```

**Rename existing Step 1b (Branching Strategy Selection) to Step 1c.** Update the pre-checks in the existing branching strategy section to remove the git detection logic (lines 58-59 of current SKILL.md) since the new Step 1b now handles it. The existing Step 1b pre-check `Check git rev-parse --git-dir` becomes unnecessary -- by the time we reach branching strategy, git is confirmed available.

**pipeline-config.json template change:**
```json
{
  "git_available": true,
  "branching_strategy": "trunk-based",
  ...
}
```

The `git_available` field defaults to `true` (backwards compatible -- existing installs have git). When the user declines git init, setup writes `false`.

**enforce-git.sh change:**
Add an early exit after PROJECT_ROOT resolution:
```bash
# No-op when git is not available
CONFIG_FILE="${PROJECT_ROOT}/.claude/pipeline-config.json"
if [ -f "$CONFIG_FILE" ] && command -v jq >/dev/null 2>&1; then
  GIT_AVAILABLE=$(jq -r '.git_available // "true"' "$CONFIG_FILE")
  if [ "$GIT_AVAILABLE" = "false" ]; then
    exit 0
  fi
fi
```
This makes the hook a no-op when git is unavailable. The `// "true"` default ensures backwards compatibility with configs that lack the field.

**enforce-sequencing.sh change:**
In the Ellis gate section, add a check:
```bash
# Skip Ellis gate when git is not available (Ellis is disabled)
GIT_AVAILABLE=$(jq -r '.git_available // "true"' "$CONFIG_FILE")
if [ "$GIT_AVAILABLE" = "false" ] && [ "$AGENT" = "ellis" ]; then
  echo "BLOCKED: Ellis is unavailable -- no git repository configured. Files were written directly to disk." >&2
  exit 1
fi
```
This blocks Ellis invocation entirely (not silently passes it) when git is unavailable, producing a clear error message if Eva accidentally tries to invoke Ellis.

**Runtime behavior documentation (behavioral, no file changes -- Eva reads config):**
- Eva boot: reads `git_available` from pipeline-config.json. When `false`: skips branch strategy announcement, skips `git diff` context gathering, skips `git log` for brain context.
- Roz: uses `find` + file listing instead of `git diff --stat` when `git_available: false`.
- Poirot: Eva skips invocation entirely, announces "Poirot skipped -- no git repository."
- Ellis: Eva skips invocation entirely, announces "Ellis skipped -- no git repository. Files written to disk."
- Pipeline end: skips commit phase entirely. Pipeline ends after review juncture + Agatha docs.

**Acceptance criteria:**
- AC-1: SKILL.md asks git availability question before branching strategy
- AC-2: When user has no git and declines init, `git_available: false` is written to pipeline-config.json
- AC-3: When user has no git and accepts init, `git init` runs, .gitignore is created, initial commit is made, pipeline proceeds normally with `git_available: true`
- AC-4: When user already has git, no question is asked -- `git_available: true` is set silently
- AC-5: enforce-git.sh exits 0 (no-op) when `git_available: false`
- AC-6: enforce-sequencing.sh blocks Ellis with clear error when `git_available: false`
- AC-7: pipeline-config.json template includes `git_available: true` as first field
- AC-8: Existing SKILL.md Step 1b pre-checks (git rev-parse) are removed (redundant with new Step 1b)
- AC-9: No changes to .claude-plugin/ files (additive-only constraint preserved)

**Estimated complexity:** Medium (4 files modified, behavioral documentation for Eva/Roz/Poirot/Ellis runtime changes)

---

### Step 2a: Cursor Plugin Manifest and Project Instructions

**After this step, I can:** install atelier-pipeline in Cursor via the local testing path (symlink) and see it recognized as a valid plugin.

**Files to create:**
1. `.cursor-plugin/plugin.json` -- Cursor Marketplace manifest
2. `.cursor-plugin/marketplace.json` -- Multi-plugin config
3. `AGENTS.md` -- Cursor project instructions (equivalent of CLAUDE.md)

**File shapes:**

`.cursor-plugin/plugin.json`:
```json
{
  "name": "atelier-pipeline",
  "version": "3.12.2",
  "description": "Multi-agent orchestration with quality gates, continuous QA, and persistent institutional memory across sessions",
  "license": "Apache-2.0",
  "author": {
    "name": "Robert Sfeir",
    "email": "robert@sfeir.design"
  }
}
```

`.cursor-plugin/marketplace.json`:
```json
{
  "name": "atelier-pipeline",
  "description": "Multi-agent orchestration plugins for Cursor IDE with quality gates, continuous QA, and persistent institutional memory",
  "owner": {
    "name": "Robert Sfeir",
    "email": "robert@sfeir.design"
  },
  "plugins": [
    {
      "name": "atelier-pipeline",
      "version": "3.12.2",
      "source": "./",
      "description": "Multi-agent orchestration with quality gates, continuous QA, and persistent institutional memory across sessions"
    }
  ]
}
```

`AGENTS.md`: Pipeline section content mirroring CLAUDE.md's pipeline section, adapted for Cursor conventions.

**Acceptance criteria:**
- AC-1: `.cursor-plugin/plugin.json` is valid JSON with required `name` field (kebab-case)
- AC-2: Version matches `.claude-plugin/plugin.json` version
- AC-3: `AGENTS.md` exists at repo root with pipeline instructions
- AC-4: Symlink `ln -s /path/to/atelier-pipeline ~/.cursor/plugins/local/atelier-pipeline` results in Cursor recognizing the plugin
- AC-5: No changes to `.claude-plugin/` files

**Estimated complexity:** Low (3 new files, known formats)

---

### Step 2b: Cursor Hook Registration

**After this step, I can:** see all enforcement hooks registered in Cursor with failClosed: true, pointing to the shared shell scripts.

**Files to create:**
1. `.cursor-plugin/hooks/hooks.json` -- Cursor hook registration

**File shape:**

```json
{
  "hooks": [
    {
      "event": "preToolUse",
      "matcher": "Write|Edit|MultiEdit",
      "command": "bash \"${CURSOR_PLUGIN_ROOT}/source/hooks/enforce-paths.sh\"",
      "failClosed": true
    },
    {
      "event": "preToolUse",
      "matcher": "Agent",
      "command": "bash \"${CURSOR_PLUGIN_ROOT}/source/hooks/enforce-sequencing.sh\"",
      "failClosed": true
    },
    {
      "event": "preToolUse",
      "matcher": "Agent",
      "command": "bash \"${CURSOR_PLUGIN_ROOT}/source/hooks/enforce-pipeline-activation.sh\"",
      "failClosed": true
    },
    {
      "event": "preToolUse",
      "matcher": "Bash",
      "command": "bash \"${CURSOR_PLUGIN_ROOT}/source/hooks/enforce-git.sh\"",
      "failClosed": true
    },
    {
      "event": "subagentStop",
      "command": "bash \"${CURSOR_PLUGIN_ROOT}/source/hooks/warn-dor-dod.sh\""
    },
    {
      "event": "preCompact",
      "command": "bash \"${CURSOR_PLUGIN_ROOT}/source/hooks/pre-compact.sh\""
    }
  ]
}
```

**Note:** The `failClosed: true` flag is set only on enforcement hooks (preToolUse), not on advisory hooks (subagentStop, preCompact). This is an improvement over Claude Code's fail-open default.

**Note:** The exact hooks.json schema must be validated against Cursor's documentation. If the schema differs (e.g., array vs object, different field names), adjust accordingly. The brain research (b6f772c2) indicates this format but it has not been verified against a running Cursor instance.

**Acceptance criteria:**
- AC-1: `.cursor-plugin/hooks/hooks.json` is valid JSON
- AC-2: All 6 hook scripts from source/hooks/ are registered
- AC-3: Enforcement hooks (4) have `failClosed: true`
- AC-4: Advisory hooks (2) do NOT have `failClosed: true`
- AC-5: All command paths reference `source/hooks/` via `CURSOR_PLUGIN_ROOT`
- AC-6: Matchers match the same tool names as `.claude/settings.json`

**Estimated complexity:** Low (1 new file, known format)

---

### Step 2c: Cursor Brain MCP Registration

**After this step, I can:** connect the brain MCP server in Cursor and run brain tools (agent_capture, agent_search, atelier_stats).

**Files to create:**
1. `.cursor-plugin/mcp.json` -- Brain MCP registration for Cursor

**File shape:**

```json
{
  "atelier-brain": {
    "command": "node",
    "args": ["${CURSOR_PLUGIN_ROOT}/brain/server.mjs"],
    "env": {
      "CURSOR_PLUGIN_ROOT": "${CURSOR_PLUGIN_ROOT}",
      "CURSOR_PLUGIN_DATA": "${CURSOR_PLUGIN_DATA}",
      "BRAIN_CONFIG_USER": "${CURSOR_PLUGIN_DATA}/brain-config.json",
      "ATELIER_BRAIN_DB_PASSWORD": "${ATELIER_BRAIN_DB_PASSWORD}",
      "ATELIER_BRAIN_DATABASE_URL": "${ATELIER_BRAIN_DATABASE_URL}",
      "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
      "NODE_TLS_REJECT_UNAUTHORIZED": "0"
    }
  }
}
```

**Note:** `brain/lib/config.mjs` resolves config from `BRAIN_CONFIG_PROJECT`, then `$CWD/.claude/brain-config.json`, then `BRAIN_CONFIG_USER`. The CWD path hardcodes `.claude/` -- this needs to also check `.cursor/brain-config.json`. This is a brain-side change that should be flagged for a follow-up (not in scope of this ADR per anti-goal, but noted as a gap).

**Actually, correction:** The brain config resolution checks `$CWD/.claude/brain-config.json` but the primary path is `BRAIN_CONFIG_USER` which is set to `${CURSOR_PLUGIN_DATA}/brain-config.json`. The /brain-setup skill writes config to `BRAIN_CONFIG_USER` (plugin data dir), not to `.claude/`. So the Cursor mcp.json setting `BRAIN_CONFIG_USER` to `${CURSOR_PLUGIN_DATA}/brain-config.json` is sufficient. No brain code change needed.

**Acceptance criteria:**
- AC-1: `.cursor-plugin/mcp.json` is valid JSON in flat format
- AC-2: Server command points to `brain/server.mjs` via `CURSOR_PLUGIN_ROOT`
- AC-3: `BRAIN_CONFIG_USER` uses `CURSOR_PLUGIN_DATA`
- AC-4: `NODE_TLS_REJECT_UNAUTHORIZED=0` is preserved (per user requirement)
- AC-5: All credential env vars are passed through

**Estimated complexity:** Low (1 new file, known format)

---

### Step 3a: Cursor Rules (.mdc wrappers for always-apply rules)

**After this step, I can:** see Eva's persona and orchestration rules loaded automatically in every Cursor conversation.

**Files to create:**
1. `.cursor-plugin/rules/default-persona.mdc` -- Eva persona (alwaysApply: true)
2. `.cursor-plugin/rules/agent-system.mdc` -- Orchestration rules (alwaysApply: true)

**File structure (each .mdc file):**

```markdown
---
description: Eva Pipeline Orchestrator -- always-loaded default persona
alwaysApply: true
---

[Full content from source/rules/default-persona.md]
```

**Acceptance criteria:**
- AC-1: Both files have valid YAML frontmatter with `alwaysApply: true`
- AC-2: Content matches `source/rules/default-persona.md` and `source/rules/agent-system.md` respectively
- AC-3: Files use `.mdc` extension
- AC-4: Cursor loads these rules on every conversation start

**Estimated complexity:** Low (2 new files, copy + frontmatter)

---

### Step 3b: Cursor Rules (.mdc wrappers for path-scoped and reference rules)

**After this step, I can:** see pipeline-orchestration, pipeline-models, and branch-lifecycle rules load when accessing docs/pipeline/ in Cursor.

**Files to create:**
1. `.cursor-plugin/rules/pipeline-orchestration.mdc` -- Path-scoped to docs/pipeline/
2. `.cursor-plugin/rules/pipeline-models.mdc` -- Path-scoped to docs/pipeline/
3. `.cursor-plugin/rules/branch-lifecycle.mdc` -- Path-scoped to docs/pipeline/

**Additionally, reference files as non-always-apply rules:**
4. `.cursor-plugin/rules/dor-dod.mdc` -- alwaysApply: false (loaded by agents)
5. `.cursor-plugin/rules/retro-lessons.mdc` -- alwaysApply: false
6. `.cursor-plugin/rules/invocation-templates.mdc` -- alwaysApply: false
7. `.cursor-plugin/rules/pipeline-operations.mdc` -- alwaysApply: false
8. `.cursor-plugin/rules/agent-preamble.mdc` -- alwaysApply: false

**File structure:**

```markdown
---
description: Pipeline orchestration operations -- loaded when working with pipeline state
alwaysApply: false
globs: ["docs/pipeline/**"]
---

[Full content from source/rules/pipeline-orchestration.md]
```

For reference rules (no globs, agent-requested):
```markdown
---
description: Definition of Ready / Definition of Done framework
alwaysApply: false
---

[Full content from source/references/dor-dod.md]
```

**Acceptance criteria:**
- AC-1: Path-scoped rules (3) have `globs: ["docs/pipeline/**"]`
- AC-2: Reference rules (5) have `alwaysApply: false` with no globs
- AC-3: All 8 files have valid YAML frontmatter
- AC-4: Content matches corresponding `source/` files

**Note on sizing:** This step has 8 files to create but they are all mechanical (frontmatter + copy). Each file creation is identical in pattern. The cognitive load is a single pattern repeated 8 times, not 8 distinct decisions.

**Estimated complexity:** Low-medium (8 files, but mechanical pattern)

---

### Step 4a: Cursor Agent Personas (core 9)

**After this step, I can:** invoke all 9 core agents in Cursor with correct persona behavior.

**Files to create:**
1. `.cursor-plugin/agents/cal.md`
2. `.cursor-plugin/agents/colby.md`
3. `.cursor-plugin/agents/roz.md`
4. `.cursor-plugin/agents/ellis.md`
5. `.cursor-plugin/agents/agatha.md`
6. `.cursor-plugin/agents/robert.md`
7. `.cursor-plugin/agents/sable.md`
8. `.cursor-plugin/agents/investigator.md`
9. `.cursor-plugin/agents/distillator.md` (but listed as 1 file below for count)

**Note:** The existing `source/agents/*.md` files may already have frontmatter suitable for Cursor, or they may use Claude Code's XML structure without YAML frontmatter. Each file needs YAML frontmatter (`name`, `description`) added if not present, with the full persona content preserved.

**Wait -- re-examining the source agents.** Reading the brain research: "Cursor agents use .md with frontmatter (name, description)." The source agents currently use XML `<identity>` tags, not YAML frontmatter. The `.cursor-plugin/agents/` files need YAML frontmatter prepended. The body content (XML prompt structure) should still work -- Cursor reads the full file content as the agent's system prompt.

**File structure:**

```markdown
---
name: cal
description: Senior Software Architect -- explores codebases, designs solutions, writes test specs, produces ADR documents
---

[Full content from source/agents/cal.md]
```

**Acceptance criteria:**
- AC-1: All 9 agent files have valid YAML frontmatter with `name` and `description`
- AC-2: `name` values match the agent names used in enforcement hooks (cal, colby, roz, ellis, agatha, robert, sable, investigator, distillator)
- AC-3: Full persona content from `source/agents/*.md` is preserved after frontmatter
- AC-4: Cursor discovers all 9 agents

**Note on sizing:** 9 files but same mechanical pattern. Each requires reading the source file to extract the agent description from `<identity>`, then prepending frontmatter. Low cognitive load per file.

**Estimated complexity:** Low-medium (9 files, mechanical pattern)

---

### Step 4b: Cursor Agent Personas (optional 3)

**After this step, I can:** invoke Sentinel, Deps, and Darwin agents in Cursor when enabled.

**Files to create:**
1. `.cursor-plugin/agents/sentinel.md`
2. `.cursor-plugin/agents/deps.md`
3. `.cursor-plugin/agents/darwin.md`

Same pattern as Step 4a -- YAML frontmatter + source content.

**Acceptance criteria:**
- AC-1: All 3 files have valid YAML frontmatter
- AC-2: Content matches `source/agents/{sentinel,deps,darwin}.md`
- AC-3: These agents are discoverable in Cursor alongside core agents

**Estimated complexity:** Low (3 files, same pattern as 4a)

---

### Step 5a: Cursor Commands (core 7)

**After this step, I can:** type /pm, /ux, /architect, /debug, /pipeline, /devops, /docs in Cursor and get the correct command behavior.

**Files to create:**
1. `.cursor-plugin/commands/pm.md`
2. `.cursor-plugin/commands/ux.md`
3. `.cursor-plugin/commands/architect.md`
4. `.cursor-plugin/commands/debug.md`
5. `.cursor-plugin/commands/pipeline.md`
6. `.cursor-plugin/commands/devops.md`
7. `.cursor-plugin/commands/docs.md`

**Key insight:** Both Claude Code and Cursor use the same markdown format for commands. These files can be direct copies from `source/commands/`. No format conversion needed.

**Acceptance criteria:**
- AC-1: All 7 command files exist in `.cursor-plugin/commands/`
- AC-2: Content matches `source/commands/*.md` exactly
- AC-3: Commands are accessible via / prefix in Cursor

**Estimated complexity:** Low (7 files, direct copy)

---

### Step 5b: Cursor Commands (optional + setup-related)

**After this step, I can:** use /deps, /darwin, /telemetry-hydrate, and /create-agent commands in Cursor.

**Files to create:**
1. `.cursor-plugin/commands/deps.md`
2. `.cursor-plugin/commands/darwin.md`
3. `.cursor-plugin/commands/telemetry-hydrate.md`
4. `.cursor-plugin/commands/create-agent.md`

**Acceptance criteria:**
- AC-1: All 4 command files exist in `.cursor-plugin/commands/`
- AC-2: Content matches `source/commands/*.md`

**Estimated complexity:** Low (4 files, direct copy)

---

### Step 5c: Cursor Skills

**After this step, I can:** use /pipeline-setup, /brain-setup, and other skills in Cursor.

**Files to create:**
1. `.cursor-plugin/skills/pipeline-setup/SKILL.md`
2. `.cursor-plugin/skills/brain-setup/SKILL.md`
3. `.cursor-plugin/skills/brain-hydrate/SKILL.md`
4. `.cursor-plugin/skills/pipeline-overview/SKILL.md`
5. `.cursor-plugin/skills/dashboard/SKILL.md`
6. `.cursor-plugin/skills/brain-uninstall/SKILL.md`
7. `.cursor-plugin/skills/pipeline-uninstall/SKILL.md`

**Key decision:** Skills for Cursor need to install to `.cursor/` instead of `.claude/`. The pipeline-setup skill currently hardcodes `.claude/` paths throughout. Options:

**Option A:** Copy skills and replace `.claude/` with `.cursor/` in Cursor-specific copies.
**Option B:** Modify skills to detect platform and use the correct prefix.

**Decision:** Option A for this step. The skills are already substantial markdown documents. Mechanical find-replace of `.claude/` to `.cursor/` and `CLAUDE_` to `CURSOR_` env var references produces working Cursor-specific skills. Option B (single skill with platform detection) is a follow-up optimization.

**Acceptance criteria:**
- AC-1: All 7 skill directories exist under `.cursor-plugin/skills/`
- AC-2: Each contains a `SKILL.md` file
- AC-3: Path references use `.cursor/` instead of `.claude/`
- AC-4: Env var references use `CURSOR_PLUGIN_ROOT`, `CURSOR_PLUGIN_DATA`, `CURSOR_PROJECT_DIR`
- AC-5: Hook registration instructions reference `.cursor/settings.json` (or Cursor's equivalent)
- AC-6: Version marker writes to `.cursor/.atelier-version`

**Note on sizing:** 7 files but each is a mechanical find-replace of a known set of strings. The cognitive challenge is ensuring completeness of the replacement, not decision-making.

**Estimated complexity:** Medium (7 files, mechanical but large -- skill files are 200-600 lines each)

---

### Step 6: Update Check Script for Dual Platform

**After this step, I can:** get update notifications for both Claude Code and Cursor installed pipeline files.

**Files to modify:**
1. `scripts/check-updates.sh` -- Add `.cursor/.atelier-version` check

**Change detail:** The script currently checks `.claude/.atelier-version`. Add a parallel check for `.cursor/.atelier-version` that runs the same comparison logic.

**Acceptance criteria:**
- AC-1: Script checks both `.claude/.atelier-version` and `.cursor/.atelier-version`
- AC-2: Reports updates for each platform independently
- AC-3: Gracefully handles when only one platform is installed (no error for missing version file)
- AC-4: Existing Claude Code update check behavior unchanged

**Estimated complexity:** Low (1 file, ~20 lines added)

---

### Step 7: SessionStart Hook for Cursor

**After this step, I can:** have brain auto-installed, update checks, and telemetry hydration run on Cursor session start.

**Modification to `.cursor-plugin/plugin.json`** (created in Step 2a, updated here):

Add SessionStart hooks that mirror `.claude-plugin/plugin.json`:

```json
{
  "name": "atelier-pipeline",
  "version": "3.12.2",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "test -d \"${CURSOR_PLUGIN_ROOT}/brain/node_modules\" || npm install --prefix \"${CURSOR_PLUGIN_ROOT}/brain\" --silent"
          },
          {
            "type": "command",
            "command": "bash \"${CURSOR_PLUGIN_ROOT}/scripts/check-updates.sh\" \"${CURSOR_PLUGIN_ROOT}\""
          },
          {
            "type": "command",
            "command": "node \"${CURSOR_PLUGIN_ROOT}/brain/scripts/hydrate-telemetry.mjs\" \"${CURSOR_PROJECT_DIR}\" --silent 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

**Acceptance criteria:**
- AC-1: SessionStart hooks in `.cursor-plugin/plugin.json` mirror `.claude-plugin/plugin.json`
- AC-2: All env var references use `CURSOR_` prefix
- AC-3: Brain npm install, update check, and telemetry hydration all fire on session start

**Estimated complexity:** Low (1 file modification)

---

## Comprehensive Test Specification

### Step 1 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-001 | Happy | enforce-paths.sh resolves PROJECT_ROOT from CURSOR_PROJECT_DIR when set (export CURSOR_PROJECT_DIR=/tmp/test-project, pipe valid JSON with tool_name=Write, file_path outside allowed, verify BLOCKED output includes the /tmp/test-project-relative path) |
| T-0019-002 | Happy | enforce-sequencing.sh resolves PROJECT_ROOT from CURSOR_PROJECT_DIR when set (set env var, pipe Agent tool input for ellis with no pipeline state, verify BLOCKED) |
| T-0019-003 | Happy | enforce-pipeline-activation.sh resolves from CURSOR_PROJECT_DIR (set env var, verify it reads pipeline-state.md from that path) |
| T-0019-004 | Happy | pre-compact.sh writes compaction marker to $CURSOR_PROJECT_DIR/docs/pipeline/pipeline-state.md |
| T-0019-005 | Boundary | CURSOR_PROJECT_DIR set but empty string -- falls through to CLAUDE_PROJECT_DIR |
| T-0019-006 | Boundary | Both CURSOR_PROJECT_DIR and CLAUDE_PROJECT_DIR set -- CURSOR_PROJECT_DIR takes precedence |
| T-0019-007 | Regression | CLAUDE_PROJECT_DIR only (no CURSOR_PROJECT_DIR) -- existing behavior unchanged |
| T-0019-008 | Regression | Neither env var set -- falls back to SCRIPT_DIR-based resolution |
| T-0019-009 | Failure | CURSOR_PROJECT_DIR set to non-existent directory -- script handles gracefully (no crash, exits non-zero or falls through to fallback) |
| T-0019-010 | Regression | enforce-git.sh unchanged -- verify it still blocks git write ops without CURSOR_PROJECT_DIR reference |
| T-0019-011 | Regression | warn-dor-dod.sh unchanged -- verify it still warns on missing DoR/DoD |
| T-0019-070 | Failure | CURSOR_PROJECT_DIR with trailing slash (e.g. "/tmp/test-project/") -- path concatenation does not produce double-slash "//" in BLOCKED output or file resolution (F1) |
| T-0019-071 | Failure | CURSOR_PROJECT_DIR containing spaces (e.g. "/tmp/my project") -- enforce-paths.sh resolves and reports paths correctly without word-splitting errors (F2) |
| T-0019-072 | Failure | CURSOR_PROJECT_DIR containing spaces -- enforce-sequencing.sh reads pipeline-state.md from the space-containing path without error (F2) |
| T-0019-073 | E2E-Enforcement | End-to-end enforcement chain for path violations: hooks.json registers enforce-paths.sh with failClosed:true, script receives stdin JSON `{tool_name: "Write", tool_input: {file_path: "/outside/lane/file.txt"}, agent_type: "subagent", agent_id: "colby"}`, script parses via jq, outputs "BLOCKED" to stdout. Verifies the full chain from registration to BLOCKED output (B3, AC-7) |
| T-0019-074 | E2E-Enforcement | End-to-end enforcement chain for sequencing violations: hooks.json registers enforce-sequencing.sh with failClosed:true, script receives stdin JSON `{tool_name: "Agent", tool_input: {subagent_type: "ellis"}, agent_id: "eva"}` with no Roz QA pass in pipeline-state.md, outputs "BLOCKED" (B3, AC-8) |
| T-0019-075 | E2E-Enforcement | End-to-end enforcement chain for git ops: hooks.json registers enforce-git.sh with failClosed:true, script receives stdin JSON `{tool_name: "Bash", tool_input: {command: "git commit -m test"}, agent_id: ""}` (empty agent_id = main thread), outputs "BLOCKED" (B3, AC-9) |

### Step 1 Telemetry

Telemetry: Log line `"Hook resolved project root from CURSOR_PROJECT_DIR"` (or absence of errors in hook stderr). Trigger: Any hook invocation in Cursor. Absence means: Hook is silently falling back to a different resolution path or failing.

### Step 1b Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-100 | Happy | SKILL.md contains git availability question positioned before branching strategy section |
| T-0019-101 | Happy | In a directory with no .git, setup flow shows "unavailable without git" list including Poirot, Ellis, CI Watch, and branch lifecycle |
| T-0019-102 | Happy | In a directory with no .git, setup flow shows "still works" list including Eva, Robert, Sable, Cal, Colby, Roz, Sentinel, Agatha, Brain |
| T-0019-103 | Happy | User accepts git init: `git init` runs, .gitignore created, initial commit created, `git_available: true` in config |
| T-0019-104 | Happy | User declines git init: `git_available: false` written to pipeline-config.json, branching strategy skipped |
| T-0019-105 | Happy | Existing git repo detected: no question asked, `git_available: true` set silently |
| T-0019-106 | Failure | enforce-git.sh with `git_available: false` in config exits 0 (no-op) on any git write operation |
| T-0019-107 | Failure | enforce-sequencing.sh blocks Ellis invocation with clear BLOCKED message when `git_available: false` |
| T-0019-108 | Failure | enforce-sequencing.sh blocks Ellis even when `roz_qa: PASS` is set (git_available=false overrides QA gate) |
| T-0019-109 | Boundary | pipeline-config.json missing `git_available` field entirely -- enforce-git.sh defaults to `true` (backwards compat) |
| T-0019-110 | Boundary | pipeline-config.json has `git_available: true` -- enforce-git.sh behaves identically to current behavior (no regression) |
| T-0019-111 | Boundary | jq not installed -- enforce-git.sh skips the config check and proceeds with normal behavior (does not crash) |
| T-0019-112 | Boundary | pipeline-config.json does not exist -- enforce-git.sh skips config check, falls through to normal behavior |
| T-0019-113 | Regression | SKILL.md existing Step 1b (now Step 1c) no longer contains `git rev-parse --git-dir` pre-check (removed, handled by new Step 1b) |
| T-0019-114 | Regression | pipeline-config.json template has `git_available` as first field, all existing fields preserved |
| T-0019-115 | Security | .gitignore created by git init includes .env (no secrets committed by default) |
| T-0019-116 | Failure | Poirot invocation with `git_available: false` -- enforce-sequencing.sh allows Poirot through (hook does not block), but Poirot's `git diff` fails at OS level. Verify hook exits 0 and the failure surfaces from git, not from the hook (F3) |
| T-0019-117 | Failure | `git_available: false` + user runs `git status` via Bash -- enforce-git.sh is a no-op (exits 0), git command fails at OS level with a system error. Verify no hook crash and the OS error is not swallowed (F4) |
| T-0019-118 | Failure | enforce-git.sh with malformed pipeline-config.json (invalid JSON) -- jq parse fails, hook falls through to normal behavior (does not crash, does not silently disable enforcement) |
| T-0019-119 | Failure | enforce-sequencing.sh with `git_available: false` blocks Ellis for ALL agent_id values (not just eva), verifying the check is agent-agnostic |
| T-0019-120 | Failure | SKILL.md git init failure (permissions error on `git init`) -- setup informs user and falls back to `git_available: false` rather than crashing |

### Step 1b Telemetry

Telemetry: Config field `git_available` in pipeline-config.json. Trigger: /pipeline-setup completion. Absence means: Setup did not complete or field was dropped during config write. Value `false` means: User is running pipeline without git -- expect no Ellis/Poirot invocations in telemetry.

### Step 2a Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-012 | Happy | .cursor-plugin/plugin.json is valid JSON with "name": "atelier-pipeline" |
| T-0019-013 | Happy | .cursor-plugin/marketplace.json is valid JSON with plugins array |
| T-0019-014 | Happy | AGENTS.md exists at repo root and contains pipeline section |
| T-0019-015 | Boundary | Version in .cursor-plugin/plugin.json matches .claude-plugin/plugin.json |
| T-0019-016 | Regression | .claude-plugin/plugin.json is unchanged (byte-for-byte) |
| T-0019-017 | Regression | .claude-plugin/marketplace.json is unchanged |
| T-0019-076 | Failure | .cursor-plugin/plugin.json missing "name" field -- JSON is valid but plugin manifest is incomplete. Verify "name" key exists and is non-empty (F5) |
| T-0019-077 | Failure | AGENTS.md content completeness -- verify it contains equivalent sections to CLAUDE.md: tech stack, test commands, source structure, key conventions (not just a pipeline section header) (F6) |
| T-0019-078 | Failure | .cursor-plugin/plugin.json "name" field uses kebab-case (no spaces, no uppercase) -- invalid naming would cause Cursor discovery failure |
| T-0019-079 | Happy | source/ directory is shared, not duplicated -- verify .cursor-plugin/ does not contain a copy of source/ directory; hooks.json commands reference source/hooks/ paths; mcp.json references brain/ directly (AC-14) |
| T-0019-139 | Failure | .cursor-plugin/marketplace.json plugins array is non-empty and each entry has required fields (name, version, source, description) -- malformed marketplace entries would prevent Cursor from listing the plugin |

### Step 2a Telemetry

Telemetry: Structural -- plugin.json presence. Trigger: Cursor plugin load. Absence means: Plugin manifest missing or unparseable.

### Step 2b Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-018 | Happy | hooks.json is valid JSON with 6 hook entries |
| T-0019-019 | Happy | All 4 enforcement hooks have failClosed: true |
| T-0019-020 | Happy | Advisory hooks (subagentStop, preCompact) do NOT have failClosed: true |
| T-0019-021 | Happy | All command paths reference source/hooks/ via CURSOR_PLUGIN_ROOT |
| T-0019-022 | Boundary | Matchers match exact tool names: Write\|Edit\|MultiEdit, Agent, Bash |
| T-0019-023 | Security | No hook has failClosed: false explicitly (absence = fail-open, which is OK for advisory; explicit false would be suspicious) |
| T-0019-080 | Failure | hooks.json with script path that does not exist (e.g. source/hooks/nonexistent.sh) + failClosed: true -- Cursor blocks ALL tool calls matching that event/matcher. Verify by checking the command path resolves to an actual file for every hook entry (B2, F7) |
| T-0019-081 | Failure | hooks.json with script that lacks execute permission + failClosed: true -- script fails to run, failClosed causes Cursor to block the tool call. Verify all referenced scripts have +x permission (B2) |
| T-0019-082 | Failure | Duplicate event+matcher combination in hooks.json -- verify no two hook entries share the same (event, matcher) pair, which could cause undefined execution order (F8) |
| T-0019-083 | Failure | hooks.json command path with unresolvable CURSOR_PLUGIN_ROOT (env var not set) -- verify the path pattern is correct and would resolve given standard Cursor plugin root |

### Step 2b Telemetry

Telemetry: Structural -- hooks.json parsed by Cursor. Trigger: Any preToolUse event. Absence means: hooks.json missing, malformed, or not discovered by Cursor.

### Step 2c Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-024 | Happy | mcp.json is valid JSON in flat format with atelier-brain key |
| T-0019-025 | Happy | Server command points to brain/server.mjs |
| T-0019-026 | Happy | BRAIN_CONFIG_USER uses CURSOR_PLUGIN_DATA |
| T-0019-027 | Happy | NODE_TLS_REJECT_UNAUTHORIZED=0 is present |
| T-0019-028 | Security | No plaintext credentials in mcp.json (all secrets via env var references) |
| T-0019-029 | Regression | .mcp.json (Claude Code) is unchanged |
| T-0019-084 | Failure | CURSOR_PLUGIN_ROOT not set -- mcp.json server command resolves to bare "/brain/server.mjs" (absolute root path). Verify the env var reference `${CURSOR_PLUGIN_ROOT}` is present and not hardcoded (F9) |
| T-0019-085 | Failure | Brain MCP not configured (no brain-config.json at CURSOR_PLUGIN_DATA) -- verify mcp.json structure still allows Cursor to start the server process, which then reports brain_enabled: false (graceful baseline mode) (spec edge case: Brain MCP not configured) |
| T-0019-086 | Failure | mcp.json env vars section contains no CLAUDE_-prefixed env vars (should be all CURSOR_-prefixed, confirming platform-correct registration) |
| T-0019-087 | Failure | mcp.json ATELIER_BRAIN_DB_PASSWORD and ATELIER_BRAIN_DATABASE_URL are env var references (${...} syntax), not literal values -- prevents accidental credential commit |

### Step 2c Telemetry

Telemetry: MCP connection health. Trigger: Brain tool call in Cursor. Absence means: MCP server not started or mcp.json not discovered.

### Step 3a Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-030 | Happy | default-persona.mdc has valid YAML frontmatter with alwaysApply: true |
| T-0019-031 | Happy | agent-system.mdc has valid YAML frontmatter with alwaysApply: true |
| T-0019-032 | Happy | Content after frontmatter matches source/rules/default-persona.md |
| T-0019-033 | Happy | Content after frontmatter matches source/rules/agent-system.md |
| T-0019-034 | Boundary | Files use .mdc extension, not .md |
| T-0019-088 | Failure | .mdc file with `alwaysApply` as string "true" instead of boolean true -- verify frontmatter uses boolean true, not quoted string, since Cursor may be type-strict (F10) |
| T-0019-089 | Failure | .mdc file with BOM (byte order mark U+FEFF) at file start -- verify generated .mdc files do not have BOM, which could break YAML frontmatter parsing (F11) |
| T-0019-090 | Failure | .mdc file with CRLF line endings -- verify .mdc files use LF line endings to avoid frontmatter parse issues on Unix-based Cursor installs (F11) |
| T-0019-091 | Failure | .mdc file with missing description field in frontmatter -- verify both files have the `description` field populated (Cursor may require it for discovery display) |

### Step 3a Telemetry

Telemetry: Structural -- rules loaded in Cursor context. Trigger: New Cursor conversation. Absence means: .mdc files not discovered or frontmatter invalid.

### Step 3b Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-035 | Happy | Path-scoped rules (3) have globs: ["docs/pipeline/**"] |
| T-0019-036 | Happy | Reference rules (5) have alwaysApply: false with no globs |
| T-0019-037 | Happy | All 8 files have valid YAML frontmatter |
| T-0019-038 | Happy | Content matches corresponding source/ files |
| T-0019-039 | Failure | Missing source file -- build/copy step reports error, does not create empty .mdc |
| T-0019-092 | Failure | Path-scoped rule with alwaysApply accidentally set to true -- verify all 3 path-scoped rules have alwaysApply: false (they use globs instead) |
| T-0019-093 | Failure | Reference rule with globs accidentally set -- verify all 5 reference rules have no globs field (they are agent-requested, not path-triggered) |
| T-0019-094 | Failure | .mdc file where content body is empty (frontmatter present but no content after `---` closer) -- verify every .mdc file has non-empty content after frontmatter |
| T-0019-095 | Failure | All 8 .mdc files use .mdc extension, not .md -- verify no .md files were accidentally created in .cursor-plugin/rules/ alongside .mdc files |

### Step 3b Telemetry

Telemetry: Structural -- path-scoped rules trigger on docs/pipeline/ access. Trigger: Agent reads pipeline state file. Absence means: globs pattern not matched or Cursor not loading path-scoped rules.

### Step 4a Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-040 | Happy | All 9 agent files have YAML frontmatter with name and description |
| T-0019-041 | Happy | name values match enforcement hook expectations: cal, colby, roz, ellis, agatha, robert, sable, investigator, distillator |
| T-0019-042 | Happy | Full persona content preserved after frontmatter |
| T-0019-043 | Boundary | Agent name in frontmatter matches filename (cal.md has name: cal) |
| T-0019-044 | Failure | Agent file with malformed frontmatter -- Cursor still loads file content (graceful degradation). Note: this tests aspirational Cursor behavior; flag if unverifiable |
| T-0019-096 | Failure | Total agent count across 4a + 4b = 12 (9 core + 3 optional). Verify `ls .cursor-plugin/agents/*.md | wc -l` equals 12 after both steps complete (F12) |
| T-0019-097 | Failure | Agent description field is non-empty for all 9 agents -- verify no agent has `description: ""` or missing description, which would produce blank entries in Cursor's agent picker |
| T-0019-098 | Failure | Agent frontmatter contains no unknown fields that could conflict with Cursor's agent schema -- verify only `name` and `description` are present (no `model`, `readonly`, etc. unless explicitly required) |

### Step 4a Telemetry

Telemetry: Structural -- agent count in Cursor discovery. Trigger: Cursor agent list query. Absence means: agents/ directory not discovered or frontmatter invalid.

### Step 4b Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-045 | Happy | sentinel.md, deps.md, darwin.md have valid frontmatter |
| T-0019-046 | Happy | Content matches source agents |
| T-0019-099 | Failure | Optional agent names (sentinel, deps, darwin) do not collide with core agent names -- verify uniqueness across all 12 agent name fields |
| T-0019-121 | Failure | Optional agent files have non-empty description fields matching their source persona identity sections |

### Step 4b Telemetry

Telemetry: Structural -- optional agent availability. Trigger: User invokes /deps, /darwin, or Sentinel scan. Absence means: Agent persona not discovered.

### Step 5a Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-047 | Happy | All 7 command files exist in .cursor-plugin/commands/ |
| T-0019-048 | Happy | Content matches source/commands/*.md |
| T-0019-049 | Regression | source/commands/ files unchanged |
| T-0019-122 | Failure | Command files are .md format (not .mdc) -- verify Cursor command discovery does not require a different extension |
| T-0019-123 | Failure | No command file is empty (0 bytes) -- verify each file has content that defines the command behavior |

### Step 5a Telemetry

Telemetry: Structural -- command availability. Trigger: User types / in Cursor command palette. Absence means: commands/ directory not discovered.

### Step 5b Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-050 | Happy | All 4 optional command files exist |
| T-0019-051 | Happy | Content matches source |
| T-0019-124 | Failure | Optional command filenames match source filenames exactly (deps.md, darwin.md, telemetry-hydrate.md, create-agent.md) -- mismatched names would break / prefix routing |
| T-0019-125 | Failure | No optional command file contains references to .claude/ paths -- verify commands work in Cursor context without Claude-specific path leakage |

### Step 5b Telemetry

Telemetry: Structural -- optional command availability. Trigger: User types /deps, /darwin, etc. Absence means: Command file not discovered.

### Step 5c Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-052 | Happy | All 7 skill directories exist with SKILL.md files |
| T-0019-053 | Happy | Path references use .cursor/ not .claude/ |
| T-0019-054 | Happy | Env var references use CURSOR_ prefix not CLAUDE_ |
| T-0019-055 | Failure | No residual CLAUDE_PROJECT_DIR or CLAUDE_PLUGIN_ROOT references in Cursor skills (grep check) |
| T-0019-056 | Happy | Hook registration instructions reference .cursor/settings.json |
| T-0019-057 | Happy | Version marker path is .cursor/.atelier-version |
| T-0019-058 | Regression | Original skills/ directory unchanged |
| T-0019-126 | Failure | No residual `.claude/` path references in Cursor skills beyond env var names -- grep for `.claude/` in all .cursor-plugin/skills/*/SKILL.md files, expect 0 matches. Catches in-comment and doc-string contexts that a simple env var replacement would miss (F13) |
| T-0019-127 | Failure | No residual `CLAUDE.md` references in Cursor skills -- should reference `AGENTS.md` instead |
| T-0019-128 | Failure | brain-setup SKILL.md Cursor variant writes brain-config.json to CURSOR_PLUGIN_DATA path (not CLAUDE_PLUGIN_DATA) -- verify the brain config output path references the correct Cursor plugin data directory (F14) |
| T-0019-129 | Failure | pipeline-setup SKILL.md Cursor variant installs hooks to .cursor/settings.json (not .claude/settings.json) -- verify the hook registration target path is Cursor-correct |
| T-0019-130 | Failure | No residual `CLAUDE_PLUGIN_DATA` references in Cursor skills -- all data path references use CURSOR_PLUGIN_DATA |

### Step 5c Telemetry

Telemetry: Structural -- skill availability. Trigger: User invokes /pipeline-setup in Cursor. Absence means: skills/ directory not discovered or SKILL.md missing.

### Step 6 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-059 | Happy | Script detects .cursor/.atelier-version and reports updates |
| T-0019-060 | Happy | Script still detects .claude/.atelier-version (backwards compat) |
| T-0019-061 | Boundary | Only .cursor/.atelier-version exists (no .claude/) -- reports Cursor only |
| T-0019-062 | Boundary | Both version files exist -- reports both independently |
| T-0019-063 | Regression | Existing Claude Code update check behavior unchanged |
| T-0019-131 | Failure | Neither .cursor/.atelier-version nor .claude/.atelier-version exists -- script exits cleanly with no error output (no crash on missing version files) |
| T-0019-132 | Failure | .cursor/.atelier-version contains malformed version string (e.g. "not-a-version") -- script handles gracefully, does not crash |

### Step 6 Telemetry

Telemetry: Update check output on session start. Trigger: SessionStart hook. Absence means: check-updates.sh not called or version file missing.

### Step 7 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-064 | Happy | plugin.json has SessionStart hooks section |
| T-0019-065 | Happy | All 3 SessionStart hooks use CURSOR_ env vars |
| T-0019-066 | Regression | .claude-plugin/plugin.json SessionStart hooks unchanged |
| T-0019-133 | Failure | SessionStart npm install hook runs before check-updates hook -- verify hook array order: npm install is index 0, check-updates is index 1 (F15, dependency: check-updates.sh may need brain node_modules) |
| T-0019-134 | Failure | SessionStart brain npm install failure (e.g. no network) -- session still starts because hook command uses `|| true` fallback or equivalent error suppression (F16) |
| T-0019-135 | Failure | SessionStart telemetry hydration failure -- session still starts because hydrate command uses `2>/dev/null || true` (verify error suppression pattern present) |

### Cross-Step Integration Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0019-136 | E2E-Enforcement | Both .claude/ and .cursor/ coexist in same project -- verify .claude/settings.json hooks and .cursor-plugin/hooks/hooks.json both reference the same source/hooks/ scripts, no path conflicts (spec edge case: both IDEs in same project) |
| T-0019-137 | Boundary | Cursor agent frontmatter includes optional `model` field -- verify .cursor-plugin/agents/ files either include model frontmatter or omit it consistently, matching Cursor's agent schema expectations (spec edge case: model routing differs) |
| T-0019-138 | Boundary | Plugin auto-discovery vs manifest: verify .cursor-plugin/plugin.json does NOT contain explicit agents/rules/commands path fields that would override Cursor's auto-discovery of the directories (spec edge case: auto-discovery conflict) |

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `.cursor-plugin/hooks/hooks.json` | `{hooks: [{event, matcher, command, failClosed}]}` | Cursor IDE hook runtime | 2b |
| `.cursor-plugin/mcp.json` | `{"atelier-brain": {command, args, env}}` | Cursor IDE MCP runtime | 2c |
| `.cursor-plugin/plugin.json` | `{name, version, hooks: {SessionStart}}` | Cursor IDE plugin loader | 2a + 7 |
| `source/hooks/enforce-paths.sh` (stdin) | `{tool_name, tool_input: {file_path}, agent_type}` | Both Claude Code and Cursor hook runtimes | 1 |
| `source/hooks/enforce-sequencing.sh` (stdin) | `{tool_name, tool_input: {subagent_type}, agent_id}` | Both hook runtimes | 1 |
| `source/pipeline/pipeline-config.json` (`git_available`) | `boolean` (default `true`) | enforce-git.sh, enforce-sequencing.sh, Eva boot, Roz QA context | 1b |
| `source/hooks/enforce-git.sh` (reads `git_available`) | no-op when `false` | Both hook runtimes | 1b |
| `source/hooks/enforce-sequencing.sh` (reads `git_available`) | BLOCKED for Ellis when `false` | Both hook runtimes | 1b |
| `skills/pipeline-setup/SKILL.md` (Step 1b flow) | git availability question + config write | User interaction at setup time | 1b |
| `.cursor-plugin/agents/*.md` (frontmatter) | `{name: string, description: string}` | Cursor IDE agent discovery | 4a, 4b |
| `.cursor-plugin/rules/*.mdc` (frontmatter) | `{description, alwaysApply, globs?}` | Cursor IDE rules loader | 3a, 3b |
| `AGENTS.md` (content) | Markdown project instructions | Cursor IDE context loader | 2a |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `.cursor-plugin/plugin.json` | Plugin manifest | Cursor plugin loader | 2a |
| `.cursor-plugin/marketplace.json` | Multi-plugin manifest | Cursor Marketplace | 2a |
| `.cursor-plugin/hooks/hooks.json` | Hook registrations | Cursor hook runtime -> source/hooks/*.sh | 2b |
| `.cursor-plugin/mcp.json` | MCP server config | Cursor MCP runtime -> brain/server.mjs | 2c |
| `.cursor-plugin/rules/*.mdc` (10 files) | Always-apply and path-scoped rules | Cursor rules loader -> Eva conversation context | 3a, 3b |
| `.cursor-plugin/agents/*.md` (12 files) | Agent personas with frontmatter | Cursor agent discovery -> subagent invocation | 4a, 4b |
| `.cursor-plugin/commands/*.md` (11 files) | Slash command definitions | Cursor command palette -> user invocation | 5a, 5b |
| `.cursor-plugin/skills/*/SKILL.md` (7 files) | Skill definitions | Cursor skill runtime -> user invocation | 5c |
| `scripts/check-updates.sh` | Version comparison output | SessionStart hook -> user notification | 6, 7 |
| `.cursor-plugin/plugin.json` (SessionStart) | Hook commands | Cursor session lifecycle | 7 |
| `AGENTS.md` | Project instructions | Cursor context loader | 2a |

| `source/pipeline/pipeline-config.json` (`git_available`) | Boolean config field | enforce-git.sh, enforce-sequencing.sh, Eva boot sequence, Roz QA context | 1b |
| `skills/pipeline-setup/SKILL.md` (git question flow) | Interactive setup flow | pipeline-config.json writer, git init runner | 1b |

No orphan producers. Every file created or modified has a direct consumer in Cursor's runtime or the pipeline setup flow.

---

## Data Sensitivity

No stores are introduced or modified. Brain MCP server is unchanged. The `.cursor-plugin/mcp.json` passes credential env vars by reference (not by value) -- no secrets in committed files.

---

## Notes for Colby

### No-repo support implementation (Step 1b)

The git availability question goes in SKILL.md between the current Step 1 (Gather Project Information) and the current Step 1b (Branching Strategy Selection). The current Step 1b becomes Step 1c. Update both the heading and any internal references.

For the SKILL.md edit:
- The existing Step 1b pre-checks (lines 57-61) that run `git rev-parse --git-dir` must be removed because they are now handled by the new Step 1b. The new Step 1b replaces the silent fallback ("skip branching question entirely, default to trunk-based") with an interactive flow that informs the user and offers git init.
- The existing Step 1b's second pre-check (`git remote get-url origin`) stays in the renamed Step 1c -- it is a remote check, not a git existence check.

For enforce-git.sh:
- The config read must use the same `PROJECT_ROOT` variable already resolved by the existing CURSOR_PROJECT_DIR/CLAUDE_PROJECT_DIR fallback chain. Place the no-op check AFTER `PROJECT_ROOT` is resolved but BEFORE any git operation checks.
- Use `jq -r '.git_available // "true"'` for backwards compatibility. If jq is not installed or the config file is missing, do NOT crash -- fall through to normal behavior.

For enforce-sequencing.sh:
- The Ellis block when `git_available: false` should produce a BLOCKED message to stderr (not a silent exit 0). This is intentional -- if Eva accidentally tries to invoke Ellis without git, she gets an error she can handle. This differs from enforce-git.sh (which goes no-op) because Ellis invocation is a logic error, while git write operations just have nothing to enforce.

For pipeline-config.json template:
- Add `"git_available": true` as the FIRST field. Existing installs that lack this field will be handled by the `// "true"` jq default in the hooks.

This is a SHARED change -- it lives in `source/` and `skills/`, so it affects BOTH Claude Code and Cursor targets. The Cursor-specific skill copies in Step 5c will inherit the change automatically since they are created from the modified SKILL.md.

### Critical: Hook stdin format validation

Before implementing Step 2b, manually test a Cursor hook by creating a minimal hooks.json with a single hook that dumps stdin to a temp file:

```json
{
  "hooks": [
    {
      "event": "preToolUse",
      "matcher": "Bash",
      "command": "cat > /tmp/cursor-hook-stdin.json"
    }
  ]
}
```

Then trigger a Bash tool call in Cursor and inspect `/tmp/cursor-hook-stdin.json`. Compare the field names against what `enforce-git.sh` expects:
- `tool_name` (should be "Bash")
- `tool_input.command` (the command string)
- `agent_id` (empty for main thread, set for subagents)

If any field name differs, create a normalization shim script (`source/hooks/cursor-shim.sh`) that translates the JSON before piping to the real hook. Update hooks.json to call the shim instead of the scripts directly.

### Mechanical pattern for .mdc files

Each .mdc file follows this exact pattern:
```
---
description: [one-line description]
alwaysApply: [true|false]
globs: ["pattern"] # only for path-scoped rules
---

[exact content of source file, unmodified]
```

Read the source file with `Read`, prepend the frontmatter, write to `.cursor-plugin/rules/`. Do not modify the source content in any way.

### Agent frontmatter extraction

For each agent in `source/agents/*.md`, the `name` field must match exactly what enforcement hooks check. The mapping is:
- `cal.md` -> `name: cal`
- `colby.md` -> `name: colby`
- `roz.md` -> `name: roz`
- etc.

The `description` field should be extracted from the `<identity>` section of each agent persona. Keep it to one line.

### Version sync discipline

When bumping the version in `.claude-plugin/plugin.json`, also bump `.cursor-plugin/plugin.json` and `.cursor-plugin/marketplace.json`. This is a manual step until a build script automates it.

### Skills find-replace scope

For Step 5c, the find-replace in skill files is:
- `.claude/` -> `.cursor/` (directory paths)
- `CLAUDE_PLUGIN_ROOT` -> `CURSOR_PLUGIN_ROOT`
- `CLAUDE_PLUGIN_DATA` -> `CURSOR_PLUGIN_DATA`
- `CLAUDE_PROJECT_DIR` -> `CURSOR_PROJECT_DIR`
- `.claude-plugin/plugin.json` -> `.cursor-plugin/plugin.json` (version marker reads)
- `CLAUDE.md` -> `AGENTS.md` (project instructions file)

Do NOT replace:
- References to `.claude/brain-config.json` in brain config resolution (brain/lib/config.mjs is shared code, not Cursor-specific)
- `CLAUDE_PROJECT_DIR` in hook scripts (those are modified in Step 1, not in skills)

### E2E-Enforcement tests (T-0019-073, T-0019-074, T-0019-075)

These three tests validate the full enforcement chain: hooks.json registration -> shell script invocation -> stdin JSON parsing -> BLOCKED output. They are the most critical tests in the spec because they validate the SPOF identified in the Spec Challenge section (hook stdin format compatibility).

Implementation approach for Roz: each test should:
1. Set CURSOR_PROJECT_DIR to a temp directory with the necessary pipeline state files
2. Pipe a synthetic JSON payload (matching Cursor's expected stdin format) to the hook script via stdin
3. Assert the script's exit code and stdout/stderr contain "BLOCKED"

These tests serve double duty: they validate enforcement AND they validate the stdin JSON field names (`tool_name`, `tool_input`, `agent_type`, `agent_id`). If Cursor's stdin format differs, these tests fail first -- before any real enforcement gap manifests.

### Hook path/permission validation (T-0019-080, T-0019-081)

These tests address the highest-risk failure mode: `failClosed: true` combined with a broken script path or missing execute permission blocks ALL matching tool calls. Roz should verify:
1. Every `command` path in hooks.json resolves to an existing file (test against the actual repo structure)
2. Every referenced script has executable permission (`test -x`)

These are static validation tests, not runtime tests -- they can run without Cursor.

### Residual path grep (T-0019-126, T-0019-127, T-0019-130)

The find-replace in Step 5c (`.claude/` -> `.cursor/`, `CLAUDE_` -> `CURSOR_`) is mechanical but error-prone in large files. These grep-based tests catch references the find-replace missed. Roz should grep the full SKILL.md content, not just env var lines -- in-comment references like "# See .claude/brain-config.json" or doc-string paths are common miss patterns.

### Brain research insights (from brain context)

- Cursor plugin auto-discovery works with: `rules/` (.md/.mdc), `agents/` (.md), `commands/` (.md/.txt), `skills/` (subdirs with SKILL.md), `hooks/hooks.json`, `mcp.json`
- Specifying a manifest field in plugin.json REPLACES auto-discovery for that category
- Cursor provides `CURSOR_PROJECT_DIR` as alias for `CLAUDE_PROJECT_DIR`
- Cursor hooks support `failClosed: true` (use it for all enforcement hooks)
- Cursor's `.mdc` frontmatter: `description` (string), `alwaysApply` (bool), `globs` (string array)

### File count per step

| Step | Create | Modify | Total | Passes S2 (<=8)? |
|------|--------|--------|-------|-------------------|
| 1 | 0 | 4 | 4 | Yes |
| 1b | 0 | 4 | 4 | Yes |
| 2a | 3 | 0 | 3 | Yes |
| 2b | 1 | 0 | 1 | Yes |
| 2c | 1 | 0 | 1 | Yes |
| 3a | 2 | 0 | 2 | Yes |
| 3b | 8 | 0 | 8 | Yes (mechanical) |
| 4a | 9 | 0 | 9 | Exceeds, justified: mechanical pattern, single template repeated 9x |
| 4b | 3 | 0 | 3 | Yes |
| 5a | 7 | 0 | 7 | Yes |
| 5b | 4 | 0 | 4 | Yes |
| 5c | 7 | 0 | 7 | Yes |
| 6 | 0 | 1 | 1 | Yes |
| 7 | 0 | 1 | 1 | Yes |

Step 4a exceeds 8 files. Justification: all 9 files follow an identical pattern (read source agent, extract description from `<identity>`, prepend YAML frontmatter, write to `.cursor-plugin/agents/`). Splitting into two sub-steps would add orchestration overhead with no cognitive benefit. A single invocation can handle the repetition.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Single repo, dual-target | Done | source/ shared, two plugin dirs (.claude-plugin/, .cursor-plugin/) |
| 2 | Full parity (12 agents) | Done | Steps 4a (9 core) + 4b (3 optional) = 12 agents |
| 3 | .cursor-plugin/plugin.json | Done | Step 2a |
| 4 | Auto-discovers agents | Done | Step 4a, 4b |
| 5 | Auto-discovers rules | Done | Steps 3a, 3b |
| 6 | Auto-discovers commands | Done | Steps 5a, 5b |
| 7 | hooks.json with failClosed | Done | Step 2b |
| 8 | mcp.json for brain | Done | Step 2c |
| 9 | Path violation enforcement | Done | Step 1 (platform compat) + Step 2b (registration) |
| 10 | Sequencing enforcement | Done | Step 1 + Step 2b |
| 11 | Git ops enforcement | Done | Step 2b (enforce-git.sh needs no platform change) |
| 12 | Eva orchestration | Done | Step 3a (always-apply rules) |
| 13 | /pipeline-setup for Cursor | Done | Step 5c |
| 14 | Brain MCP works | Done | Step 2c |
| 15 | Claude Code unchanged | Done | Anti-goal + AC-16 in Step 2a, AC-29 in Step 2c |
| 16 | source/ shared | Done | All steps reference source/, no duplication of logic |
| 17 | Platform detection in hooks | Done | Step 1 |
| 18 | failClosed enforcement | Done | Step 2b |
| 19 | AGENTS.md | Done | Step 2a |
| 20 | /pipeline-setup adapted | Done | Step 5c |
| 21 | No-repo support | Done | Step 1b (setup flow, config field, hook degradation, runtime behavior) |

**Architectural decisions not in spec:**
- D1: Rules as .mdc wrappers with full content copy (not symlinks, not build-generated). Reason: format incompatibility (.md vs .mdc) makes symlinks impossible; build script premature for feature branch validation.
- D6: Separate mcp.json with Cursor env vars (not shared with Claude Code). Reason: env var names differ between platforms.
- D7: Skills duplicated with find-replace (not unified with platform detection). Reason: simpler for initial port; platform detection is a follow-up optimization.
- D8: No-repo support as a shared source/ change (not Cursor-specific). Reason: User decided during spec phase that git availability detection benefits both platforms equally. enforce-git.sh becomes a no-op and enforce-sequencing.sh blocks Ellis when `git_available: false`. Eva, Roz, and other agents degrade gracefully at runtime via behavioral config read.

**Rejected alternatives:**
- Symlink-based sharing: Rejected because .mdc format requires frontmatter that .md files don't have.
- Single plugin directory: Rejected because platform discovery paths are incompatible.
- Build script generation: Deferred, not rejected. Right solution long-term but premature.

**Technical constraints discovered:**
- Brain config resolution hardcodes `.claude/brain-config.json` in CWD check (brain/lib/config.mjs:41). This path won't find Cursor-installed brain config. Not a blocker because `BRAIN_CONFIG_USER` env var takes priority, but noted for future cleanup.
- Hook stdin format is unverified. All enforcement depends on it matching Claude Code's format. Step 1 includes validation.

**Grep check:** TODO/FIXME/HACK/XXX in this document -> 0
**Template:** All sections filled -- no TBD, no placeholders.

---

**Total: 14 steps, 136 tests (48 Happy, 54 Failure, 4 E2E-Enforcement, 14 Boundary, 13 Regression, 3 Security). Failure:Happy ratio 58:48 (counting E2E-Enforcement as enforcement-path failures) -- passes Cal DoD globally and per step.**

Handoff: ADR saved to `docs/architecture/ADR-0019-cursor-port.md`. 14 steps, 136 total tests. Next: Roz reviews the test spec.
