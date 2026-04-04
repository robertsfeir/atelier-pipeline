#!/bin/bash
# Per-agent path enforcement: Colby
# PreToolUse hook on Write|Edit|MultiEdit -- Colby is blocked from colby_blocked_paths
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

if [ -f "$CONFIG" ]; then
  while IFS= read -r prefix; do
    case "$FILE_PATH" in "$prefix"*) echo "BLOCKED: Colby cannot write to blocked path. Attempted: $FILE_PATH" >&2; exit 2 ;; esac
  done < <(jq -r '.colby_blocked_paths[]' "$CONFIG" 2>/dev/null)
fi

exit 0
