#!/bin/bash
# Phase 3: Brain usage visibility
# PostToolUse hook on Agent
#
# After a subagent completes, checks if the agent has brain access
# requirements and whether brain tools appear in the output.
# Non-blocking — emits warnings only (exit 0 always).

set -euo pipefail

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[ "$TOOL_NAME" != "Agent" ] && exit 0

SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty')
[ -z "$SUBAGENT_TYPE" ] && exit 0

# Load config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

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
BRAIN_AGENTS=$(jq -r '.brain_required_agents[]' "$CONFIG" 2>/dev/null)
for agent in $BRAIN_AGENTS; do
  [ "$agent" = "$SUBAGENT_TYPE" ] && REQUIRES_BRAIN=true
done
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

# Check for evidence of brain tool usage in the output
BRAIN_PATTERNS="agent_search|agent_capture|atelier_trace|atelier_relation|atelier_browse|brain.*search|brain.*capture|searched.*brain|captured.*brain"

if ! echo "$TOOL_RESULT" | grep -qiE "$BRAIN_PATTERNS" 2>/dev/null; then
  echo "WARNING: $SUBAGENT_TYPE completed without evidence of brain tool usage. Brain access is MANDATORY when brain is available. Verify that $SUBAGENT_TYPE performed required brain reads (agent_search) and writes (agent_capture) per its Brain Access section." >&2
fi

# Always non-blocking
exit 0
