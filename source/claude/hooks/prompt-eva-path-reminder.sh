#!/bin/bash
# prompt-eva-path-reminder.sh -- PreToolUse prompt hook on Write|Edit|MultiEdit.
#
# Soft reminder injected into Eva's context when she is about to write outside
# docs/pipeline/ on the main thread. Fires before enforce-eva-paths.sh so Eva
# receives routing guidance rather than only the hard-block error message.
#
# Always exits 0. Never blocks -- that is enforce-eva-paths.sh's job.

set -euo pipefail

[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
[ -f "${PROJECT_ROOT}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || true)
case "$TOOL_NAME" in Write|Edit|MultiEdit) ;; *) exit 0 ;; esac

# Only fire on the main thread (Eva). Subagents pass through.
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null || true)
[ -n "$AGENT_ID" ] && exit 0

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)
[ -z "$FILE_PATH" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

# Normalize path separators for Windows compatibility
FILE_PATH="${FILE_PATH//\\//}"
PROJECT_ROOT_NORM="${PROJECT_ROOT//\\//}"

# Strip project root prefix to get project-relative path
FILE_PATH_LOWER="$(echo "$FILE_PATH" | tr '[:upper:]' '[:lower:]')"
PROJECT_ROOT_LOWER="$(echo "$PROJECT_ROOT_NORM" | tr '[:upper:]' '[:lower:]')"
if [[ "$FILE_PATH_LOWER" == "${PROJECT_ROOT_LOWER}/"* ]]; then
  FILE_PATH="${FILE_PATH:${#PROJECT_ROOT_NORM}+1}"
fi

# Exception 1: Eva's auto-memory system writes to $HOME/.claude/projects/.../memory/
if [[ "$FILE_PATH" == ${HOME}/.claude/projects/*/memory/* ]]; then
  exit 0
fi

# Exception 2: ADR-0032 out-of-repo session state at ~/.atelier/pipeline/{slug}/{hash}/
if [[ "$FILE_PATH" == ${HOME}/.atelier/pipeline/*/*/* ]]; then
  exit 0
fi

# If the path is inside docs/pipeline/, that is Eva's allowed zone -- no reminder needed.
PIPELINE_DIR=$(jq -r '.pipeline_state_dir // "docs/pipeline"' "$CONFIG" 2>/dev/null || echo "docs/pipeline")
case "$FILE_PATH" in
  "${PIPELINE_DIR}/"*) exit 0 ;;
  "${PIPELINE_DIR}") exit 0 ;;
esac

# Absolute path still remaining means outside project root -- fire reminder.
# Also fire for any relative path not in the allowed zone.
cat <<EOF
[eva-path-reminder] This file is outside docs/pipeline/.
Eva does not edit this directly. Route to Colby (code, docs, config) or Ellis (git plumbing, version manifests, CHANGELOG, commits).
The hard gate (enforce-eva-paths.sh) will block this call. Do not retry -- re-plan with the correct agent.
EOF

exit 0
