#!/bin/bash
# Per-agent path enforcement: Roz
# PreToolUse hook on Write|Edit -- Roz can only write test files + docs/pipeline/
set -uo pipefail
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
[ -f "${CLAUDE_PROJECT_DIR:-.}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
case "$TOOL_NAME" in Write|Edit|MultiEdit) ;; *) exit 0 ;; esac

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

# Normalize absolute paths to project-relative
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-.}}"
FILE_PATH="${FILE_PATH#"$PROJECT_ROOT"/}"

# If still absolute after normalization, it's outside the project root
if [[ "$FILE_PATH" == /* ]]; then
  echo "BLOCKED: File is outside the project root. Attempted: $FILE_PATH" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"

case "$FILE_PATH" in docs/pipeline/*) exit 0 ;; esac

if [ -f "$CONFIG" ]; then
  while IFS= read -r pattern; do
    case "$FILE_PATH" in *"$pattern"*) exit 0 ;; esac
    if [[ "$pattern" == /* ]]; then
      local_stripped="${pattern#/}"
      case "$FILE_PATH" in "$local_stripped"*) exit 0 ;; esac
    fi
  done < <(jq -r '.test_patterns[]' "$CONFIG" 2>/dev/null)
fi

echo "BLOCKED: Roz can only write test files and docs/pipeline/. Attempted: $FILE_PATH" >&2
exit 2
