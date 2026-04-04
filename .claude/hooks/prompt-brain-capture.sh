#!/bin/bash
# Brain capture advisory prompt hook
# SubagentStop prompt hook -- fires when any subagent completes
#
# Outputs advisory text reminding Eva to call agent_capture for the key
# finding/decision from this agent's output. Only fires for capture-capable
# agents (cal, colby, roz, agatha). Exits 0 always.
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

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null || true)

# Exit silently if agent_type is empty or missing
if [ -z "$AGENT_TYPE" ]; then
  exit 0
fi

# Output advisory for capture-capable agents; execution confirmation for others
case "$AGENT_TYPE" in
  cal|colby|roz|agatha)
    echo "BRAIN CAPTURE REMINDER: $AGENT_TYPE just returned. In the distributed capture model, $AGENT_TYPE captures domain-specific knowledge directly via agent_capture. Eva captures cross-cutting concerns only (user decisions, phase transitions, cross-agent patterns). Review $AGENT_TYPE's output for any cross-cutting insights to capture with source_agent: 'eva'."
    ;;
  *)
    # Non-capture-capable agents: log execution confirmation without advisory
    echo "[SubagentStop hook executed] agent_type: $AGENT_TYPE"
    ;;
esac

exit 0
