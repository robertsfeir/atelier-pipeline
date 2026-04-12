#!/bin/bash
# Brain prefetch advisory prompt hook
# PreToolUse(Agent) prompt hook -- fires before every Agent tool invocation
#
# Outputs advisory text reminding Eva to call agent_search before
# constructing the invocation. Only fires for capture-capable agents
# (cal, colby, roz — matches scout swarm enforcement scope). Exits 0 always.
#
# Non-blocking prompt hook: exits 0 always. No brain calls, no blocking.
# Retro lesson #003 compliant.

# Do NOT use set -e -- we want graceful degradation (retro lesson #003)
set -uo pipefail

INPUT=$(cat 2>/dev/null) || true

# Graceful degradation: empty stdin -> no output
if [ -z "$INPUT" ]; then
  exit 0
fi

# Graceful degradation: no jq -> no inspection
if ! command -v jq &>/dev/null; then
  exit 0
fi

SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty' 2>/dev/null || true)

# Only output advisory for capture-capable agents
case "$SUBAGENT_TYPE" in
  cal|colby|roz) ;;
  *) exit 0 ;;
esac

echo "BRAIN PREFETCH REMINDER: You are about to invoke $SUBAGENT_TYPE. Call agent_search with a query relevant to this work unit before constructing the invocation prompt. Inject results into the <brain-context> tag."

exit 0
