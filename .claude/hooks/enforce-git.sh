#!/bin/bash
# Phase 2 supplement: Prevent unauthorized agents from running git write operations or test suites
# PreToolUse hook on Bash
#
# Performance: This hook has an `if` conditional in settings.json:
#   "if": "tool_input.command.includes('git ')"
# Claude Code evaluates this before spawning the process, skipping ~90%
# of Bash calls that have no git commands. When the `if` passes (command
# contains 'git '), this script runs and enforces the full check.
#
# Git write operations (add, commit, push, reset, checkout --, restore, clean)
# are allowed ONLY for Ellis. All other agents and the main thread (Eva) are blocked.
#
# Test suite execution is allowed ONLY for Poirot and Colby. All other agents
# and the main thread (Eva) are blocked.

set -euo pipefail
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
[ -f "${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-.}}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

# Source shared hook library (ADR-0034 Wave 2 Step 2.1)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/hook-lib.sh" ]; then
  source "$SCRIPT_DIR/hook-lib.sh" 2>/dev/null || true
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[ "$TOOL_NAME" != "Bash" ] && exit 0

AGENT_TYPE=$(echo "$INPUT" | hook_lib_get_agent_type 2>/dev/null || echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // empty' 2>/dev/null || true)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$COMMAND" ] && exit 0

# No-op when git is not available
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
# Try .cursor/ first (Cursor), fall back to .claude/ (Claude Code)
if [ -f "${PROJECT_ROOT}/.cursor/pipeline-config.json" ]; then
  CONFIG_FILE="${PROJECT_ROOT}/.cursor/pipeline-config.json"
else
  CONFIG_FILE="${PROJECT_ROOT}/.claude/pipeline-config.json"
fi
if [ -f "$CONFIG_FILE" ]; then
  GIT_AVAILABLE=$(jq -r 'if .git_available == false then "false" else "true" end' "$CONFIG_FILE" 2>/dev/null) || true
  if [ "$GIT_AVAILABLE" = "false" ]; then
    exit 0
  fi
fi

# Block git write operations -- only Ellis is allowed
# Allow git status, git diff, git log, git branch (read-only git operations) for everyone
if echo "$COMMAND" | grep -qE "\bgit\s+(add|commit|push|reset|checkout\s+--|restore|clean)\b" 2>/dev/null; then
  if [ "$AGENT_TYPE" = "ellis" ]; then
    exit 0
  fi
  echo "BLOCKED: Only Ellis can run git write operations. Route commits through Ellis. Allowed for all: git status, git diff, git log, git branch." >&2
  exit 2
fi

# NOTE (ADR-0038): git worktree add/remove are intentionally NOT blocked.
# Eva creates worktrees at pipeline start for session isolation.
# Do NOT add 'worktree' to the blocked operations regex above.

# Block test execution -- only Poirot and Colby are allowed.
# The anchor (^|&&|\|\||;|\||\n)\s* ensures we only match test runners that are
# actually being invoked as commands, not referenced as string values inside echo,
# variable assignments, or installation scripts. Without the anchor, a command like
# `echo "run pytest to verify"` would produce a false positive and block Eva from
# running diagnostic scripts that mention test tool names.
if echo "$COMMAND" | grep -qE "(^|&&|\|\||;|\||\n|\()\s*(bats|pytest|jest|vitest|mocha|rspec|phpunit)\b|(^|&&|\|\||;|\||\n|\()\s*(npm|yarn|pnpm)\s+test\b|(^|&&|\|\||;|\||\n|\()\s*node\s+--test\b|(^|&&|\|\||;|\||\n|\()\s*(go|cargo|make|dotnet|gradle|mvn)\s+test\b" 2>/dev/null; then
  if [ "$AGENT_TYPE" = "colby" ]; then
    exit 0
  fi
  echo "BLOCKED: Only Poirot and Colby can run test suites. Route QA verification through Poirot." >&2
  exit 2
fi

# Note: Both blocks above are defense-in-depth. They catch direct invocations
# of git/test commands but can be bypassed via indirection (bash -c, env, wrapper
# scripts). The behavioral rules in pipeline-orchestration.md are the primary
# constraint; these hooks are the mechanical backstop.
# agent_type comes from the subagent's frontmatter name field; empty for
# the main thread (Eva).
exit 0
