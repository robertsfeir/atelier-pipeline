### Step 3a: Install Enforcement Hooks

Copy the hook scripts from the plugin's `source/claude/hooks/` directory to `.claude/hooks/`
in the project. These hooks mechanically enforce agent boundaries — they are not
optional and must be installed for the pipeline to function correctly.

| Template Source | Destination | Purpose |
|----------------|-------------|---------|
| `source/claude/hooks/enforce-eva-paths.sh` | `.claude/hooks/enforce-eva-paths.sh` | Blocks main thread (Eva) Write/Edit outside docs/pipeline/ |
| `source/claude/hooks/enforce-sarah-paths.sh` | `.claude/hooks/enforce-sarah-paths.sh` | Per-agent: Sarah can only write to docs/architecture/ |
| `source/claude/hooks/enforce-colby-paths.sh` | `.claude/hooks/enforce-colby-paths.sh` | Per-agent: Colby blocked from colby_blocked_paths |
| `source/claude/hooks/enforce-agatha-paths.sh` | `.claude/hooks/enforce-agatha-paths.sh` | Per-agent: Agatha can only write to docs/ |
| `source/claude/hooks/enforce-product-paths.sh` | `.claude/hooks/enforce-product-paths.sh` | Per-agent: Robert-spec can only write to docs/product/ |
| `source/claude/hooks/enforce-ux-paths.sh` | `.claude/hooks/enforce-ux-paths.sh` | Per-agent: Sable-ux can only write to docs/ux/ |
| `source/claude/hooks/enforce-ellis-paths.sh` | `.claude/hooks/enforce-ellis-paths.sh` | Per-agent: Ellis can only write to CHANGELOG.md, git config files, and CI/CD paths |
| `source/claude/hooks/enforce-sequencing.sh` | `.claude/hooks/enforce-sequencing.sh` | Blocks out-of-order agent invocations (e.g., Ellis without Poirot verification) |
| `source/claude/hooks/enforce-pipeline-activation.sh` | `.claude/hooks/enforce-pipeline-activation.sh` | Blocks Colby/Ellis invocation when no active pipeline exists |
| `source/claude/hooks/enforce-scout-swarm.sh` | `.claude/hooks/enforce-scout-swarm.sh` | Blocks Sarah/Colby/Poirot invocations missing the required scout evidence block (research-brief, colby-context, debug-evidence, qa-evidence) |
| `source/claude/hooks/enforce-git.sh` | `.claude/hooks/enforce-git.sh` | Blocks git write operations from main thread (must go through Ellis) |
| `source/claude/hooks/session-hydrate.sh` | `.claude/hooks/session-hydrate.sh` | Intentional no-op — superseded by atelier_hydrate MCP tool. Installed for backward-compatibility only; NOT registered in settings.json. |
| `source/claude/hooks/pre-compact.sh` | `.claude/hooks/pre-compact.sh` | Writes compaction marker to pipeline-state.md before context is compacted (PreCompact) |
| `source/claude/hooks/log-agent-start.sh` | `.claude/hooks/log-agent-start.sh` | Logs agent start events to JSONL telemetry file (SubagentStart) |
| `source/claude/hooks/log-agent-stop.sh` | `.claude/hooks/log-agent-stop.sh` | Logs agent stop events to JSONL telemetry file (SubagentStop) |
| `source/claude/hooks/enforce-colby-stop-verify.sh` | `.claude/hooks/enforce-colby-stop-verify.sh` | Runs verify_commands.format + verify_commands.typecheck after Colby stops; exits 2 on typecheck failure to re-engage Colby (SubagentStop, ADR-0050). **Claude Code only -- Cursor does not support SubagentStop** (see `source/cursor/agents/brain-extractor.frontmatter.yml`); Cursor installs intentionally omit this hook. |
| `source/claude/hooks/post-compact-reinject.sh` | `.claude/hooks/post-compact-reinject.sh` | Re-injects pipeline-state.md and context-brief.md after compaction (PostCompact) |
| `source/claude/hooks/log-stop-failure.sh` | `.claude/hooks/log-stop-failure.sh` | Appends error entry to error-patterns.md on agent failure (StopFailure) |
| `source/claude/hooks/prompt-brain-prefetch.sh` | `.claude/hooks/prompt-brain-prefetch.sh` | Brain prefetch prompt injection (Prompt) |
| `source/claude/hooks/prompt-compact-advisory.sh` | `.claude/hooks/prompt-compact-advisory.sh` | Wave-boundary compaction advisory (SubagentStop) |
| `source/claude/hooks/prompt-brain-capture-reminder.sh` | `.claude/hooks/prompt-brain-capture-reminder.sh` | Soft prompt reminder when brain capture is pending — fires before enforce-brain-capture-gate.sh so Eva sees guidance before the hard block (PreToolUse Agent, Prompt) |
| `source/claude/hooks/enforce-brain-capture-gate.sh` | `.claude/hooks/enforce-brain-capture-gate.sh` | Blocks Agent invocations when a brain capture is pending — fires first in the Agent PreToolUse chain, before enforce-sequencing.sh (ADR-0053) |
| `source/claude/hooks/enforce-brain-capture-pending.sh` | `.claude/hooks/enforce-brain-capture-pending.sh` | Writes .pending-brain-capture.json marker when an allowlisted agent stops (SubagentStop, ADR-0053) |
| `source/claude/hooks/clear-brain-capture-pending.sh` | `.claude/hooks/clear-brain-capture-pending.sh` | Deletes .pending-brain-capture.json when agent_capture succeeds — suffix-matches *__agent_capture to support any plugin prefix (PostToolUse, ADR-0053) |
| `source/shared/agents/brain-extractor.md` | `.claude/agents/brain-extractor.md` | Brain knowledge extractor agent (assembled with frontmatter overlay below) |
| `source/claude/agents/brain-extractor.frontmatter.yml` | (assembled with above into `.claude/agents/brain-extractor.md`) | Claude Code frontmatter for brain-extractor agent |
| `source/cursor/agents/brain-extractor.frontmatter.yml` | `.cursor-plugin/agents/brain-extractor.md` | Cursor frontmatter for brain-extractor agent |
| `source/shared/hooks/session-boot.sh` | `.claude/hooks/session-boot.sh` | Session boot data collector (SessionStart) -- reads pipeline state and config |
| `source/shared/hooks/hook-lib.sh` | `.claude/hooks/hook-lib.sh` | Shared hook utility library — JSON parsers, agent type extraction, deny/allow emitters (sourced by enforcement and telemetry hooks) |
| `source/shared/hooks/pipeline-state-path.sh` | `.claude/hooks/pipeline-state-path.sh` | Per-worktree session state path resolver — session_state_dir() and error_patterns_path() (sourced by session-boot, post-compact-reinject, prompt-compact-advisory) |
| `source/claude/hooks/enforcement-config.json` | `.claude/hooks/enforcement-config.json` | Project-specific paths and agent rules |

#### ADR-0050 verify_commands keys (`enforce-colby-stop-verify.sh`, opt-in)

The Claude Code-only `enforce-colby-stop-verify.sh` hook (SubagentStop) reads
three keys from `.claude/pipeline-config.json` (or `.cursor/pipeline-config.json`,
checked first). All three are opt-in -- absent or empty values turn the
behavior off without warnings.

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `verify_commands.format` | string | (missing) | Auto-format command run after every Colby stop. **Empty string = no-op** (skip the format step). **Missing key = silent skip** (same as empty). Format failures are logged to stderr but never block. |
| `verify_commands.typecheck` | string | (missing) | Typecheck command run after format. **Empty string = no-op** (skip the typecheck step). **Missing key = silent skip**. On non-zero exit the hook prints the last ~40 lines of output on stderr and exits 2 to re-engage Colby. |
| `verify_max_attempts` | integer | `3` | Maximum number of consecutive **typecheck failures** in a single session before the hook stops re-engaging Colby and exits 0 with a warning. The counter increments on failure only; a successful typecheck deletes the counter file (full reset). Format failures never touch the counter. |

If both `verify_commands.format` and `verify_commands.typecheck` are missing
or empty, the hook exits 0 immediately -- the project is treated as not
opted in. To opt in to typecheck-only enforcement, set
`verify_commands.typecheck` and leave `verify_commands.format` empty (or
omit it entirely).

Example (`pipeline-config.json` fragment):

```json
{
  "verify_commands": {
    "format": "npm run format",
    "typecheck": "npm run typecheck"
  },
  "verify_max_attempts": 3
}
```

After copying, make the `.sh` files executable: `chmod +x .claude/hooks/*.sh`

**Validate enforcement-config.json** after copying and customizing. Read the installed `.claude/hooks/enforcement-config.json` and check the following required fields:

| Field | Type | Requirement |
|-------|------|-------------|
| `pipeline_state_dir` | string | Non-empty |
| `test_command` | string | Non-empty -- critical: Poirot cannot run tests without this |
| `test_patterns` | array | Non-empty -- at least one pattern required |

Also check `lint_command`: if the field is absent or empty, warn (but do not block) -- Eva's quality gate will fall back to `test_command`.

Print the validation result:
- **All required fields valid:** `Enforcement config validated — all required fields present.`
- **Any required field missing or empty:** `WARNING: enforcement-config.json is missing required fields: [list]. Pipeline enforcement may not work correctly. Re-run /pipeline-setup to fix.`
- **Only lint_command empty/absent:** `NOTE: lint_command is not set — Eva will fall back to test_command for quality checks.`

Do not block installation on validation failure. The warning is informational -- the fix is re-running setup.

**Customize enforcement-config.json** with the project-specific values from Step 1:
- `pipeline_state_dir`: the pipeline state directory (default: `docs/pipeline`)
- `colby_blocked_paths`: array of path prefixes Colby cannot write to (default includes `docs/`, `.github/`, infrastructure paths)
- `test_patterns`: array of patterns matching the project's test files (e.g., `[".test.", ".spec.", "/tests/", "conftest"]`)
- `test_command`: full test suite command from Step 1 -- used by Poirot for QA verification (e.g., `npm test`, `pytest`)

**Register hooks in `.claude/settings.json`** — merge with existing settings if the
file already exists. Add this hooks section:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-eva-paths.sh"}]
      },
      {
        "matcher": "Agent",
        "hooks": [{"type": "prompt", "prompt": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-brain-capture-reminder.sh"}, {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-brain-capture-gate.sh"}, {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-sequencing.sh"}, {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-pipeline-activation.sh"}, {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-scout-swarm.sh", "if": "tool_input.subagent_type == 'sarah' || tool_input.subagent_type == 'colby' || tool_input.subagent_type == 'scout'"}, {"type": "prompt", "prompt": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-brain-prefetch.sh", "if": "tool_input.subagent_type == 'sarah' || tool_input.subagent_type == 'colby' || tool_input.subagent_type == 'poirot'"}]
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
        "hooks": [
          {"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-boot.sh"}
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/log-agent-stop.sh"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-colby-stop-verify.sh"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-brain-capture-pending.sh"
          },
          {
            "type": "prompt",
            "prompt": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-compact-advisory.sh",
            "if": "agent_type == 'ellis'"
          },
          {
            "type": "agent",
            "agent": "brain-extractor",
            "prompt": "Extract decisions, patterns, and lessons from the completed agent's output and capture them to the brain via agent_capture.",
            "if": "agent_type == 'sarah' || agent_type == 'colby' || agent_type == 'agatha' || agent_type == 'robert' || agent_type == 'robert-spec' || agent_type == 'sable' || agent_type == 'sable-ux' || agent_type == 'ellis'"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/clear-brain-capture-pending.sh"}]
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

**Important:** These hooks require `jq` to be installed. Check with `command -v jq`.
If `jq` is not available, tell the user: "Install jq for pipeline enforcement hooks:
`brew install jq` (macOS) or `apt install jq` (Linux)."

**Total with hooks: 38 mandatory files across 7 directories.**

#### Custom Agent Discovery

The pipeline supports custom agents beyond the core 9. To add a custom agent:

- **Drop a file:** Place any `.md` file into `.claude/agents/` with YAML
  frontmatter (`name`, `description`) and Eva will discover it automatically
  at session start.
- **Paste markdown:** Paste a raw agent definition into the chat and Eva will
  offer to convert it to the pipeline's XML format and write it as a proper
  agent file.
- **Read-only by default:** Discovered agents cannot use Write, Edit, or
  MultiEdit tools. To grant write access, add a per-agent frontmatter hook
  (enforce-{name}-paths.sh) to the agent's frontmatter overlay.

See the "Agent Discovery" section in `agent-system.md` for full details.

### Step 3b: Write Version Marker

After copying all template files, write the current plugin version to `.claude/.atelier-version`:

```bash
# Read version from plugin.json and write to project
grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json" | head -1 | grep -o '"[^"]*"$' | tr -d '"' > .claude/.atelier-version
```

This file is used by the SessionStart hook to detect when the plugin has been updated and the project's pipeline files may be outdated. The hook compares this version against the plugin's current version and notifies the user if an update is available.

**Important:** Always write this file, even on reinstalls. It must reflect the version of the templates that were actually installed.

### Step 3c: Cursor Plugin Rules Sync (.mdc wrappers for reference docs)

When running inside Cursor (detected via `CURSOR_PROJECT_DIR` env var), create `.mdc` wrappers
for reference documents so Cursor can discover and load them. Each wrapper adds YAML frontmatter
to the source content. All reference rules use `alwaysApply: false` -- they are loaded on demand
by agents, not injected into every conversation.

**File structure (each reference .mdc wrapper):**

```markdown
---
description: [short description of the document]
alwaysApply: false
---

[Full content from source/shared/references/<file>.md]
```

**Reference docs to sync (alwaysApply: false):**

| Source | Destination | Description |
|--------|-------------|-------------|
| `source/shared/references/dor-dod.md` | `.cursor-plugin/rules/dor-dod.mdc` | Definition of Ready / Definition of Done framework |
| `source/shared/references/invocation-templates.md` | `.cursor-plugin/rules/invocation-templates.mdc` | Invocation templates -- standardized XML tag patterns for subagent invocation |
| `source/shared/references/pipeline-operations.md` | `.cursor-plugin/rules/pipeline-operations.mdc` | Pipeline operations -- continuous QA, feedback loops, batch mode, and worktree rules |
| `source/shared/references/agent-preamble.md` | `.cursor-plugin/rules/agent-preamble.mdc` | Agent preamble -- shared actions and protocols for all pipeline agents |
| `source/shared/references/branch-mr-mode.md` | `.cursor-plugin/rules/branch-mr-mode.mdc` | Branch and MR mode -- Colby branch creation and MR procedures for MR-based strategies |
| `source/shared/references/telemetry-metrics.md` | `.cursor-plugin/rules/telemetry-metrics.mdc` | Telemetry metrics -- metric schemas, cost table, alert thresholds, JIT telemetry-capture protocol |
| `source/shared/references/pipeline-phases.md` | `.cursor-plugin/rules/pipeline-phases.mdc` | JIT phase sizing, budget gate, investigation discipline, concurrent session detection, state file descriptions |
| `source/shared/references/worktree-isolation.md` | `.cursor-plugin/rules/worktree-isolation.mdc` | JIT worktree-per-session protocol (ADR-0038) |
| `source/shared/references/xml-prompt-schema.md` | `.cursor-plugin/rules/xml-prompt-schema.mdc` | XML prompt schema -- tag vocabulary for agent persona files |
| `source/shared/references/cloud-architecture.md` | `.cursor-plugin/rules/cloud-architecture.mdc` | Cloud architecture -- reference for cloud-native deployment patterns |
| `source/shared/references/step-sizing.md` | `.cursor-plugin/rules/step-sizing.mdc` | ADR step sizing gate (S1-S5) and split heuristics |
| `source/shared/references/routing-detail.md` | `.cursor-plugin/rules/routing-detail.mdc` | Auto-routing intent detection matrix -- loaded JIT when Eva encounters edge-case routing decisions |

**Skip when:** Running in Claude Code (no `CURSOR_PROJECT_DIR` env var). Claude Code reads `.claude/references/*.md` directly without `.mdc` wrappers.
