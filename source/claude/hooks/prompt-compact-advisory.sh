#!/bin/bash
# prompt-compact-advisory.sh -- SubagentStop prompt hook
# Detects Ellis per-wave commit during build and advises Eva to suggest /compact.
# Purely advisory, never blocks. Exits 0 always. Retro lesson #003 compliant.
# Do NOT use set -e -- we want graceful degradation (retro lesson #003)
set -uo pipefail
INPUT=$(cat 2>/dev/null) || true
if [ -z "$INPUT" ]; then exit 0; fi
if ! command -v jq &>/dev/null; then exit 0; fi

# Source shared hook library (ADR-0034 Wave 2 Step 2.1)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/hook-lib.sh" ]; then
  source "$SCRIPT_DIR/hook-lib.sh" 2>/dev/null || true
fi
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/pipeline-state-path.sh" ]; then
  source "$SCRIPT_DIR/pipeline-state-path.sh" 2>/dev/null || true
fi
STATE_DIR=$(session_state_dir 2>/dev/null || echo "docs/pipeline")
STATE_FILE="$STATE_DIR/pipeline-state.md"

AGENT_TYPE=$(echo "$INPUT" | hook_lib_get_agent_type 2>/dev/null || echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // empty' 2>/dev/null || true)
if [ "$AGENT_TYPE" != "ellis" ]; then exit 0; fi
if [ ! -f "$STATE_FILE" ]; then exit 0; fi
PHASE=$(cat "$STATE_FILE" | hook_lib_pipeline_status_field phase 2>/dev/null || true)
case "$PHASE" in
  build|implement)
    echo 'WAVE BOUNDARY: Ellis completed a per-wave commit. Pipeline state is fully persisted. Before starting the next wave, suggest to the user: "This is a good moment to run /compact -- wave state is saved and the next wave will start with cleaner context." Do not auto-compact; this is the user'"'"'s decision.'
    ;;
esac
exit 0
