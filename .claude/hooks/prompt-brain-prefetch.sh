#!/bin/bash
# Brain prefetch advisory prompt hook
# PreToolUse(Agent) prompt hook -- fires before every Agent tool invocation
#
# Outputs advisory text reminding Eva to call agent_search before
# constructing the invocation. Only fires for scout-capable agents
# (sarah, colby — matches scout swarm enforcement scope). Exits 0 always.
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
  sarah|colby) ;;
  *) exit 0 ;;
esac

echo "BRAIN PREFETCH REMINDER: You are about to invoke $SUBAGENT_TYPE. Call agent_search with (a) a query relevant to this work unit AND (b) the scope for this project. Derive scope from .claude/brain-config.json (the \`scope\` key written by brain-setup). Scope matters: an unscoped agent_search returns entries from every project sharing this brain instance, which leaks unrelated codebases into this invocation's <brain-context>. Inject results into the <brain-context> tag."

exit 0
