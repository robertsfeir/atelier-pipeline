#!/bin/bash
# DoR/DoD compliance warning hook
# SubagentStop hook -- fires when any subagent completes
#
# Checks Colby and Roz output for ## DoR and ## DoD section headers.
# Warns on stderr when missing. NEVER blocks (exit 0 always).
# This is a safety net -- Eva's DoR/DoD gate is the primary enforcement.

set -euo pipefail

INPUT=$(cat)

# Graceful degradation: no jq -> no inspection
if ! command -v jq &>/dev/null; then
  exit 0
fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null || true)

# Only inspect Colby and Roz output
case "$AGENT_TYPE" in
  colby|roz) ;;
  *) exit 0 ;;
esac

OUTPUT=$(echo "$INPUT" | jq -r '.last_assistant_message // empty' 2>/dev/null || true)

# Handle missing output
if [ -z "$OUTPUT" ]; then
  echo "WARNING: $AGENT_TYPE completed but output not available for DoR/DoD inspection." >&2
  exit 0
fi

# Case-insensitive check for DoR section header (allows suffixes like "## DoR: Requirements Extracted")
if ! echo "$OUTPUT" | grep -qi "^## DoR"; then
  echo "WARNING: $AGENT_TYPE output missing '## DoR' section. DoR/DoD framework requires DoR as the first output section." >&2
fi

# Case-insensitive check for DoD section header (allows suffixes like "## DoD: Verification")
if ! echo "$OUTPUT" | grep -qi "^## DoD"; then
  echo "WARNING: $AGENT_TYPE output missing '## DoD' section. DoR/DoD framework requires DoD as the last output section." >&2
fi

unset OUTPUT
exit 0
