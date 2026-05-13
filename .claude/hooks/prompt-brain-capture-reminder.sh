#!/bin/bash
# prompt-brain-capture-reminder.sh -- PreToolUse prompt hook on Agent.
#
# Soft reminder injected into Eva's context when a brain capture is
# pending. Fires before enforce-brain-capture-gate.sh so Eva receives
# curated guidance rather than only the hard-block error message.
#
# Always exits 0. Never blocks -- that is enforce-brain-capture-gate.sh's job.
# Honors the same sentinels as the gate (.brain-unavailable, .brain-not-installed).

set -euo pipefail

[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
[ -f "${PROJECT_ROOT}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || true)
[ "$TOOL_NAME" != "Agent" ] && exit 0

# Only enforce from the main thread (Eva). Subagents pass through.
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null || true)
[ -n "$AGENT_ID" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

PIPELINE_DIR=$(jq -r '.pipeline_state_dir // "docs/pipeline"' "$CONFIG" 2>/dev/null || echo "docs/pipeline")
case "$PIPELINE_DIR" in
  /*) ;;
  *) PIPELINE_DIR="${PROJECT_ROOT}/${PIPELINE_DIR}" ;;
esac

PENDING_FILE="${PIPELINE_DIR}/.pending-brain-capture.json"
SENTINEL_FILE="${PIPELINE_DIR}/.brain-unavailable"
NOT_INSTALLED_FILE="${PIPELINE_DIR}/.brain-not-installed"

[ ! -f "$PENDING_FILE" ] && exit 0
[ -f "$SENTINEL_FILE" ] && exit 0
[ -f "$NOT_INSTALLED_FILE" ] && exit 0

PENDING_AGENT=$(jq -r '.agent_type // "unknown"' "$PENDING_FILE" 2>/dev/null || echo "unknown")

cat <<EOF
[brain-capture-reminder] A brain capture is pending for the previous agent (${PENDING_AGENT}).
Call agent_capture with a curated thought (decision, pattern, or lesson — 1-3 sentences) before
spawning the next agent. The hard gate will block the invocation until the capture is recorded.
Do not proceed to the next Agent call without capturing first.
EOF

exit 0
