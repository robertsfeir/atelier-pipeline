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

# Source shared hook library (ADR-0034 Wave 2 Step 2.1)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/hook-lib.sh" ]; then
  source "$SCRIPT_DIR/hook-lib.sh" 2>/dev/null || true
fi

AGENT_TYPE=$(echo "$INPUT" | hook_lib_get_agent_type 2>/dev/null || echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // empty' 2>/dev/null || true)
[ -n "$AGENT_TYPE" ] && exit 0

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
case "$TOOL_NAME" in Write|Edit|MultiEdit) ;; *) exit 0 ;; esac

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
# Exception 1: Eva's auto-memory system writes to $HOME/.claude/projects/.../memory/.
# Allow writes only to the memory subdirectory path pattern — not arbitrary .claude/ paths.
# Exception 2: ADR-0032 out-of-repo session state lives at ~/.atelier/pipeline/{slug}/{hash}/.
# The pattern {slug}/{hash} means exactly two additional path components after the base.
# Format: $HOME/.atelier/pipeline/<one-component>/<one-component>/<file>
if [[ "$FILE_PATH" == /* ]] || [[ "$FILE_PATH" =~ ^[A-Za-z]:/ ]]; then
  if [[ "$FILE_PATH" == ${HOME}/.claude/projects/*/memory/* ]]; then
    exit 0
  fi
  if [[ "$FILE_PATH" == ${HOME}/.atelier/pipeline/*/*/* ]]; then
    exit 0
  fi
  echo "BLOCKED: File is outside the project root. Attempted: $FILE_PATH" >&2
  exit 2
fi

case "$FILE_PATH" in docs/pipeline/*) exit 0 ;; esac
echo "BLOCKED: Eva can only write to docs/pipeline/. Attempted: $FILE_PATH" >&2
exit 2
