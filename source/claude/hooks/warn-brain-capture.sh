#!/bin/bash
# Brain capture compliance warning hook
# SubagentStop hook -- fires when brain-access agents complete
#
# Checks last_assistant_message for the string "agent_capture" and warns
# on stderr when absent. Only fires for brain-access agents (cal, colby,
# roz, agatha). Exits 0 always.
#
# Follows warn-dor-dod.sh pattern exactly.
# Non-enforcement hook: exits 0 always. No brain calls, no blocking.
# Retro lesson #003 compliant.

set -euo pipefail

INPUT=$(cat)

# Graceful degradation: no jq -> no inspection
if ! command -v jq &>/dev/null; then
  exit 0
fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null || true)

# Only inspect brain-access agents
case "$AGENT_TYPE" in
  cal|colby|roz|agatha) ;;
  *) exit 0 ;;
esac

OUTPUT=$(echo "$INPUT" | jq -r '.last_assistant_message // empty' 2>/dev/null || true)

# Handle missing output
if [ -z "$OUTPUT" ]; then
  echo "WARNING: $AGENT_TYPE completed but output not available for brain capture inspection." >&2
  exit 0
fi

# Check for agent_capture string in output
if ! echo "$OUTPUT" | grep -q "agent_capture"; then
  echo "WARNING: $AGENT_TYPE output does not mention agent_capture. Brain capture may have been skipped." >&2
fi

unset OUTPUT
exit 0
