#!/bin/bash
# PostToolUse hook on Edit|Write|MultiEdit: Check file complexity after changes.
# Warns (non-blocking) if a file exceeds complexity thresholds.
# Uses complexity_command from enforcement-config.json.

set -euo pipefail

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
case "$TOOL_NAME" in
  Write|Edit|MultiEdit) ;;
  *) exit 0 ;;
esac

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

# Skip non-source files
case "$FILE_PATH" in
  *.md|*.json|*.yml|*.yaml|*.toml|*.cfg|*.ini|*.txt|*.sh) exit 0 ;;
esac

# Load config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

COMPLEXITY_COMMAND=$(jq -r '.complexity_command // empty' "$CONFIG")
[ -z "$COMPLEXITY_COMMAND" ] && exit 0
[ "$COMPLEXITY_COMMAND" = "null" ] && exit 0

# Run complexity check — substitute {file} with the actual file path
CMD=$(echo "$COMPLEXITY_COMMAND" | sed "s|{file}|$FILE_PATH|g")
OUTPUT=$(eval "$CMD" 2>&1) || true

if [ -n "$OUTPUT" ]; then
  echo "WARNING: Complexity check flagged issues in $FILE_PATH:" >&2
  echo "$OUTPUT" >&2
fi

# Always non-blocking
exit 0
