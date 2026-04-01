#!/bin/bash
# Phase 2 supplement: Prevent Eva from running git write operations or test suites directly
# PreToolUse hook on Bash
#
# Eva must route commits through Ellis. This hook blocks git add,
# git commit, and git push from the main thread. Subagents (Ellis)
# are allowed. Eva must also route test suite execution through Roz --
# this hook blocks test commands from the main thread.

set -euo pipefail
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
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
if echo "$COMMAND" | grep -qE "\bgit\s+(add|commit|push|reset|checkout\s+--|restore|clean)\b" 2>/dev/null; then
  echo "BLOCKED: Eva cannot run git write operations directly. Route commits through Ellis. Allowed: git status, git diff, git log, git branch." >&2
  exit 2
fi

# Block test execution from main thread -- Roz owns QA verification
if echo "$COMMAND" | grep -qE "\b(bats|pytest|jest|vitest|mocha|rspec|phpunit)\b|(\b(npm|yarn|pnpm)\s+test\b)|(\bnode\s+--test\b)|(\b(go|cargo|make|dotnet|gradle|mvn)\s+test\b)" 2>/dev/null; then
  echo "BLOCKED: Eva cannot run test suites directly. Route QA verification through Roz." >&2
  exit 2
fi

# Note: Both blocks above are defense-in-depth. They catch direct invocations
# of git/test commands but can be bypassed via indirection (bash -c, env, wrapper
# scripts). The behavioral rules in pipeline-orchestration.md are the primary
# constraint; these hooks are the mechanical backstop.
exit 0
