#!/bin/bash
# Phase 2 supplement: Prevent Eva from running git commit/push directly
# PreToolUse hook on Bash
#
# Eva must route commits through Ellis. This hook blocks git add,
# git commit, and git push from the main thread. Subagents (Ellis)
# are allowed.

set -euo pipefail

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[ "$TOOL_NAME" != "Bash" ] && exit 0

# Only block from main thread
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty')
[ -n "$AGENT_ID" ] && exit 0

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$COMMAND" ] && exit 0

# Block git add, git commit, git push from main thread
# Allow git status, git diff, git log, git branch (read-only git operations)
if echo "$COMMAND" | grep -qE "git\s+(add|commit|push|reset|checkout\s+--|restore|clean)" 2>/dev/null; then
  echo "BLOCKED: Eva cannot run git write operations directly. Route commits through Ellis. Allowed: git status, git diff, git log, git branch." >&2
  exit 2
fi

exit 0
