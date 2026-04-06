#!/bin/bash
# Per-agent path enforcement: Eva (main thread)
# PreToolUse hook on Write|Edit|MultiEdit -- Eva can only write to docs/pipeline/
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

# Reject path traversal before any exception checks — must run on all paths
[[ "$FILE_PATH" == *..* ]] && { echo "BLOCKED: Path traversal detected in $FILE_PATH" >&2; exit 2; }

# If still absolute after normalization, it's outside the project root.
# Exception: Eva's auto-memory system writes to $HOME/.claude/projects/.../memory/.
# Allow writes only to the memory subdirectory path pattern — not arbitrary .claude/ paths.
if [[ "$FILE_PATH" == /* ]]; then
  if [[ "$FILE_PATH" == ${HOME}/.claude/projects/*/memory/* ]]; then
    exit 0
  fi
  echo "BLOCKED: File is outside the project root. Attempted: $FILE_PATH" >&2
  exit 2
fi

case "$FILE_PATH" in docs/pipeline/*) exit 0 ;; esac
echo "BLOCKED: Eva can only write to docs/pipeline/. Attempted: $FILE_PATH" >&2
exit 2
