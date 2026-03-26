#!/bin/bash
# Phase 3: Brain context consumption visibility
# PostToolUse hook on Agent
#
# After a subagent completes, checks if the agent has brain access
# requirements and whether brain context was consumed in the output.
# Brain reads are now Eva's responsibility (pre-fetched and injected
# via <brain-context> tag). This hook checks for evidence that agents
# consumed the injected context, not that they called brain tools.
# Non-blocking — emits warnings only (exit 0 always).

set -euo pipefail

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[ "$TOOL_NAME" != "Agent" ] && exit 0

SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty')
[ -z "$SUBAGENT_TYPE" ] && exit 0

# Load config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

# Ensure CWD is the project root — hooks may inherit an arbitrary CWD
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
cd "$PROJECT_ROOT"

# Check if brain is available (skip warning if brain isn't configured)
PIPELINE_DIR=$(jq -r '.pipeline_state_dir' "$CONFIG")
STATE_FILE="$PIPELINE_DIR/pipeline-state.md"
if [ -f "$STATE_FILE" ]; then
  if ! grep -qi "brain.*available.*true\|brain_available.*true" "$STATE_FILE" 2>/dev/null; then
    # Brain not available — skip check
    exit 0
  fi
fi

# Check if this agent requires brain access
REQUIRES_BRAIN=false
while IFS= read -r agent; do
  [ "$agent" = "$SUBAGENT_TYPE" ] && REQUIRES_BRAIN=true
done < <(jq -r '.brain_required_agents[]' "$CONFIG" 2>/dev/null)
[ "$REQUIRES_BRAIN" = false ] && exit 0

# Get the tool result text
TOOL_RESULT=$(echo "$INPUT" | jq -r '
  if .tool_result then
    if .tool_result.content then
      if (.tool_result.content | type) == "array" then
        [.tool_result.content[] | .text // empty] | join(" ")
      elif (.tool_result.content | type) == "string" then
        .tool_result.content
      else
        ""
      end
    else
      .tool_result | tostring
    end
  else
    ""
  end
')

# Check for evidence of brain context consumption in the output.
# Since brain reads are now Eva-injected data (via <brain-context> tag),
# we look for evidence that the agent referenced or consumed the injected
# context — not that the agent called brain tools directly.
CONSUMPTION_PATTERNS="brain.context|brain context|brain-context|prior.*decision|prior.*pattern|injected.*thought|provided.*brain|thought.*type|Brain context"

if ! echo "$TOOL_RESULT" | grep -qiE "$CONSUMPTION_PATTERNS" 2>/dev/null; then
  echo "WARNING: $SUBAGENT_TYPE completed without evidence of brain context consumption. Eva injected brain context via <brain-context> tag — verify that $SUBAGENT_TYPE reviewed the injected thoughts for relevant prior decisions, patterns, and lessons." >&2
fi

# Always non-blocking
exit 0
