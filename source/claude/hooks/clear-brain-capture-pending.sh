#!/bin/bash
# clear-brain-capture-pending.sh -- PostToolUse hook (ADR-0053, decoupled per ADR-0055).
#
# Per ADR-0055, this hook is no longer scoped to a specific brain MCP
# server name in settings.json. Its PostToolUse registration omits the
# `matcher` field, so it fires on every PostToolUse event. Internally,
# the hook reads `tool_name` from the stdin payload and only acts when
# the tool name ends with the suffix `__agent_capture` -- the brain
# protocol's `agent_capture` tool, regardless of which plugin or
# `claude mcp add` registration produced it.
#
# On a matching tool name, deletes
# {pipeline_state_dir}/.pending-brain-capture.json so the PreToolUse
# gate (enforce-brain-capture-gate.sh) lets Eva spawn the next agent.
#
# Idempotent: exits 0 cleanly when the file is absent. Always exits 0,
# never blocks -- PostToolUse is observation, not enforcement.

set -uo pipefail

[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
[ -f "${PROJECT_ROOT}/docs/pipeline/.setup-mode" ] && exit 0

# Read stdin so we can inspect tool_name. Drain even on parse failure to
# give the hook runtime a clean EOF.
INPUT=$(cat 2>/dev/null || true)
: "${INPUT:=}"

# jq missing -> fail-open (do not delete; cannot verify the tool name).
if ! command -v jq &>/dev/null; then
  exit 0
fi

# Extract tool_name from stdin. Suffix-match the brain protocol's
# agent_capture tool so any plugin/registration prefix is acceptable.
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || true)
case "$TOOL_NAME" in
  *__agent_capture) ;;
  *) exit 0 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"

if [ -f "$CONFIG" ]; then
  PIPELINE_DIR=$(jq -r '.pipeline_state_dir // "docs/pipeline"' "$CONFIG" 2>/dev/null || echo "docs/pipeline")
else
  PIPELINE_DIR="docs/pipeline"
fi

case "$PIPELINE_DIR" in
  /*) ;;
  *) PIPELINE_DIR="${PROJECT_ROOT}/${PIPELINE_DIR}" ;;
esac

PENDING_FILE="${PIPELINE_DIR}/.pending-brain-capture.json"

# Idempotent delete -- absent file is success.
rm -f "$PENDING_FILE" 2>/dev/null || true

exit 0
