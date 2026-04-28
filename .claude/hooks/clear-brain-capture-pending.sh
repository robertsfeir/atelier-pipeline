#!/bin/bash
# clear-brain-capture-pending.sh -- PostToolUse hook on agent_capture (ADR-0053).
#
# Scoped in settings.json to the matcher
# mcp__plugin_atelier-pipeline_atelier-brain__agent_capture. On a
# successful capture (the only path the matcher fires on), deletes
# {pipeline_state_dir}/.pending-brain-capture.json so the PreToolUse
# gate (enforce-brain-capture-gate.sh) lets Eva spawn the next agent.
#
# Idempotent: exits 0 cleanly when the file is absent (it always exits 0,
# never blocks -- PostToolUse is observation, not enforcement).

set -uo pipefail

[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
[ -f "${PROJECT_ROOT}/docs/pipeline/.setup-mode" ] && exit 0

# Drain stdin so the hook runtime gets a clean EOF; we do not consume the
# tool result, but reading is harmless and matches the SubagentStop pattern.
INPUT=$(cat 2>/dev/null || true)
: "${INPUT:=}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"

if [ -f "$CONFIG" ] && command -v jq &>/dev/null; then
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
