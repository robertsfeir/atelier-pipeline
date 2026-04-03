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
# Test suite execution is allowed ONLY for Roz and Colby. All other agents
# and the main thread (Eva) are blocked.

set -euo pipefail
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
[ -f "${CLAUDE_PROJECT_DIR:-.}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[ "$TOOL_NAME" != "Bash" ] && exit 0

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$COMMAND" ] && exit 0

# No-op when git is not available
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
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

# Block test execution -- only Roz and Colby are allowed
if echo "$COMMAND" | grep -qE "\b(bats|pytest|jest|vitest|mocha|rspec|phpunit)\b|(\b(npm|yarn|pnpm)\s+test\b)|(\bnode\s+--test\b)|(\b(go|cargo|make|dotnet|gradle|mvn)\s+test\b)" 2>/dev/null; then
  if [ "$AGENT_TYPE" = "roz" ] || [ "$AGENT_TYPE" = "colby" ]; then
    exit 0
  fi
  echo "BLOCKED: Only Roz and Colby can run test suites. Route QA verification through Roz." >&2
  exit 2
fi

# Note: Both blocks above are defense-in-depth. They catch direct invocations
# of git/test commands but can be bypassed via indirection (bash -c, env, wrapper
# scripts). The behavioral rules in pipeline-orchestration.md are the primary
# constraint; these hooks are the mechanical backstop.
# agent_type comes from the subagent's frontmatter name field; empty for
# the main thread (Eva).
exit 0
