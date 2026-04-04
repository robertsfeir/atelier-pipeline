#!/bin/bash
# prompt-compact-advisory.sh -- SubagentStop prompt hook
# Detects Ellis per-wave commit during build and advises Eva to suggest /compact.
# Purely advisory, never blocks. Exits 0 always. Retro lesson #003 compliant.
# Do NOT use set -e -- we want graceful degradation (retro lesson #003)
set -uo pipefail
INPUT=$(cat 2>/dev/null) || true
if [ -z "$INPUT" ]; then exit 0; fi
if ! command -v jq &>/dev/null; then exit 0; fi
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null || true)
if [ "$AGENT_TYPE" != "ellis" ]; then exit 0; fi
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-${CURSOR_PROJECT_DIR:-.}}"
STATE_FILE="$PROJECT_DIR/docs/pipeline/pipeline-state.md"
if [ ! -f "$STATE_FILE" ]; then exit 0; fi
PHASE=$(grep -o 'PIPELINE_STATUS: {[^}]*}' "$STATE_FILE" 2>/dev/null \
  | tail -1 | sed 's/PIPELINE_STATUS: //' \
  | jq -r '.phase // empty' 2>/dev/null || true)
case "$PHASE" in
  build|implement)
    echo 'WAVE BOUNDARY: Ellis completed a per-wave commit. Pipeline state is fully persisted. Before starting the next wave, suggest to the user: "This is a good moment to run /compact -- wave state is saved and the next wave will start with cleaner context." Do not auto-compact; this is the user'"'"'s decision.'
    ;;
esac
exit 0
