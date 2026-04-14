#!/bin/bash
# Per-agent path enforcement: Roz
# PreToolUse hook on Write -- Roz can only write test files + docs/pipeline/
set -uo pipefail
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
[ -f "${CLAUDE_PROJECT_DIR:-.}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
# Roz's disallowedTools blocks Edit/MultiEdit at Layer 1; frontmatter registers on Write only
case "$TOOL_NAME" in Write) ;; *) exit 0 ;; esac

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

# Normalize absolute paths to project-relative (Windows-compatible)
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-.}}"
# Normalize path separators for Windows compatibility
FILE_PATH="${FILE_PATH//\\//}"
PROJECT_ROOT="${PROJECT_ROOT//\\//}"
# Case-insensitive strip to handle Windows drive letter casing (C: vs c:)
FILE_PATH_LOWER="${FILE_PATH,,}"
PROJECT_ROOT_LOWER="${PROJECT_ROOT,,}"
if [[ "$FILE_PATH_LOWER" == "${PROJECT_ROOT_LOWER}/"* ]]; then
  FILE_PATH="${FILE_PATH:${#PROJECT_ROOT}+1}"
fi

# Reject path traversal before any exception checks — must run on all paths
[[ "$FILE_PATH" == *..* ]] && { echo "BLOCKED: Path traversal detected in $FILE_PATH" >&2; exit 2; }

# If still absolute after normalization, it's outside the project root.
# Exception: ADR-0032 out-of-repo session state lives at ~/.atelier/pipeline/{slug}/{hash}/.
# Roz does not write pipeline state, but the architectural intent is that both enforcement
# hooks recognise the out-of-repo path so any future Roz state writes are not silently
# routed to the docs/pipeline/ fallback instead of the correct out-of-repo location.
if [[ "$FILE_PATH" == /* ]] || [[ "$FILE_PATH" =~ ^[A-Za-z]:/ ]]; then
  if [[ "$FILE_PATH" == ${HOME}/.atelier/pipeline/*/*/* ]]; then
    exit 0
  fi
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
