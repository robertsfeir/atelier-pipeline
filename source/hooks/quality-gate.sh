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
  exit 0
fi

TEST_COMMAND=$(jq -r '.test_command // empty' "$CONFIG")
[ -z "$TEST_COMMAND" ] && exit 0
[ "$TEST_COMMAND" = "null" ] && exit 0

# Skip if test command is a placeholder
case "$TEST_COMMAND" in
  *"no test"*|*"not configured"*|*"echo"*) exit 0 ;;
esac

# Run tests with loop guard
export ATELIER_STOP_HOOK_ACTIVE=1
if ! eval "$TEST_COMMAND" 2>&1; then
  echo "BLOCKED: Test suite failed. Fix failing tests before finishing. Command: $TEST_COMMAND" >&2
  exit 2
fi

exit 0
