#!/bin/bash
# Phase 3: Pipeline activation enforcement
# PreToolUse hook on Agent
#
# Blocks invocation of Colby or Ellis when no active pipeline exists
# in docs/pipeline/pipeline-state.md. This ensures telemetry capture
# and quality gates are not bypassed by ad-hoc agent invocations.
#
# Only enforces from the main thread (Eva orchestrates). Subagents
# spawning other subagents is already blocked by disallowedTools: Agent.

set -euo pipefail

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[ "$TOOL_NAME" != "Agent" ] && exit 0

# Only enforce from main thread (Eva orchestrates)
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty')
[ -n "$AGENT_ID" ] && exit 0

SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty')
[ -z "$SUBAGENT_TYPE" ] && exit 0

# Only enforce for colby and ellis
case "$SUBAGENT_TYPE" in
  colby|ellis) ;;
  *) exit 0 ;;
esac

# Load config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

# Ensure CWD is the project root -- hooks may inherit an arbitrary CWD
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
cd "$PROJECT_ROOT"

PIPELINE_DIR=$(jq -r '.pipeline_state_dir' "$CONFIG")
STATE_FILE="$PIPELINE_DIR/pipeline-state.md"

# No pipeline-state.md -> no active pipeline -> block
if [ ! -f "$STATE_FILE" ]; then
  echo "BLOCKED: Invoking $SUBAGENT_TYPE without an active pipeline. No telemetry will be captured. Size the work (Micro/Small/Medium/Large) and activate with /pipeline first." >&2
  exit 2
fi

# Snapshot state file to avoid partial-read race
STATE_SNAPSHOT=$(mktemp)
trap 'rm -f "$STATE_SNAPSHOT"' EXIT
cp "$STATE_FILE" "$STATE_SNAPSHOT" 2>/dev/null || {
  rm -f "$STATE_SNAPSHOT"
  echo "BLOCKED: Invoking $SUBAGENT_TYPE without an active pipeline. No telemetry will be captured. Size the work (Micro/Small/Medium/Large) and activate with /pipeline first." >&2
  exit 2
}

# Extract phase from PIPELINE_STATUS JSON marker
PHASE_JSON=$(grep -o 'PIPELINE_STATUS: {[^}]*}' "$STATE_SNAPSHOT" 2>/dev/null | tail -1 | sed 's/PIPELINE_STATUS: //') || true

# No PIPELINE_STATUS marker -> no active pipeline -> block
if [ -z "$PHASE_JSON" ]; then
  echo "BLOCKED: Invoking $SUBAGENT_TYPE without an active pipeline. No telemetry will be captured. Size the work (Micro/Small/Medium/Large) and activate with /pipeline first." >&2
  exit 2
fi

# Parse phase field from JSON
PHASE=$(echo "$PHASE_JSON" | jq -r '.phase // empty' 2>/dev/null) || true

# No phase or empty phase -> no active pipeline -> block
if [ -z "$PHASE" ]; then
  echo "BLOCKED: Invoking $SUBAGENT_TYPE without an active pipeline. No telemetry will be captured. Size the work (Micro/Small/Medium/Large) and activate with /pipeline first." >&2
  exit 2
fi

# Normalize phase to lowercase for comparison
PHASE=$(echo "$PHASE" | tr '[:upper:]' '[:lower:]')

# Inactive phases -> no active pipeline -> block
case "$PHASE" in
  none|idle|complete)
    echo "BLOCKED: Invoking $SUBAGENT_TYPE without an active pipeline. No telemetry will be captured. Size the work (Micro/Small/Medium/Large) and activate with /pipeline first." >&2
    exit 2
    ;;
esac

# Active pipeline phase found -> allow
exit 0
