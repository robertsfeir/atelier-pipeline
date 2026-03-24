#!/bin/bash
# Stop hook: Quality gate — runs test suite before allowing agent to finish.
# If tests fail, exit 2 forces the agent to continue working.
# Uses test_command from enforcement-config.json.
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

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TEST_COMMAND=$(jq -r '.test_command // empty' "$CONFIG")
[ -z "$TEST_COMMAND" ] && exit 0
[ "$TEST_COMMAND" = "null" ] && exit 0

# Skip if test command is a placeholder
case "$TEST_COMMAND" in
  *"no test"*|*"not configured"*|*"echo"*) exit 0 ;;
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

# Run tests with loop guard
export ATELIER_STOP_HOOK_ACTIVE=1
if ! bash -c "$TEST_COMMAND" 2>&1; then
  echo "BLOCKED: Test suite failed. Fix failing tests before finishing. Command: $TEST_COMMAND" >&2
  exit 2
fi

exit 0
