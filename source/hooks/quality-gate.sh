#!/bin/bash
# Stop hook: Quality gate — runs fast lint/typecheck checks before allowing agent to finish.
# If checks fail, exit 2 forces the agent to continue working.
# Uses lint_command from enforcement-config.json (falls back to test_command for backward compat).
# Guard against infinite loops with ATELIER_STOP_HOOK_ACTIVE env var.

set -euo pipefail

# Prevent infinite loop — if this hook already fired and we're re-entering, allow stop
if [ "${ATELIER_STOP_HOOK_ACTIVE:-}" = "1" ]; then
  exit 0
fi

# Load config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

# Ensure CWD is the project root — hooks may inherit an arbitrary CWD
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
cd "$PROJECT_ROOT"

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

# Read lint_command; fall back to test_command for backward compatibility
LINT_COMMAND=$(jq -r '.lint_command // empty' "$CONFIG")
if [ -z "$LINT_COMMAND" ] || [ "$LINT_COMMAND" = "null" ]; then
  LINT_COMMAND=$(jq -r '.test_command // empty' "$CONFIG")
fi
[ -z "$LINT_COMMAND" ] && exit 0
[ "$LINT_COMMAND" = "null" ] && exit 0

# Skip if lint command is a placeholder
case "$LINT_COMMAND" in
  *"no test"*|*"no lint"*|*"not configured"*|*"echo"*) exit 0 ;;
esac

# Skip if no uncommitted source file changes
# Exclude: docs/**, .claude/**, root *.md, docs/pipeline/**
SOURCE_CHANGES=$(git diff --name-only HEAD 2>/dev/null \
  | grep -v '^docs/' \
  | grep -v '^\.claude/' \
  | grep -v '^[^/]*\.md$' || true)
SOURCE_STAGED=$(git diff --name-only --cached 2>/dev/null \
  | grep -v '^docs/' \
  | grep -v '^\.claude/' \
  | grep -v '^[^/]*\.md$' || true)
SOURCE_UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null \
  | grep -v '^docs/' \
  | grep -v '^\.claude/' \
  | grep -v '^[^/]*\.md$' || true)
if [ -z "$SOURCE_CHANGES" ] && [ -z "$SOURCE_STAGED" ] && [ -z "$SOURCE_UNTRACKED" ]; then
  exit 0
fi

# Detect timeout command (Linux: timeout, macOS coreutils: gtimeout)
TIMEOUT_CMD=""
command -v timeout &>/dev/null && TIMEOUT_CMD="timeout 30"
command -v gtimeout &>/dev/null && TIMEOUT_CMD="gtimeout 30"

# Run lint checks with loop guard and timeout
export ATELIER_STOP_HOOK_ACTIVE=1
if ! $TIMEOUT_CMD bash -c "$LINT_COMMAND" 2>&1; then
  LINT_EXIT=$?
  if [ "$LINT_EXIT" -eq 124 ]; then
    echo "BLOCKED: Lint command timed out after 30 seconds. Command: $LINT_COMMAND" >&2
  else
    echo "BLOCKED: Lint checks failed. Fix lint/typecheck errors before finishing. Command: $LINT_COMMAND" >&2
  fi
  exit 2
fi

exit 0
