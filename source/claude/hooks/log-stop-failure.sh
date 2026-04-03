#!/bin/bash
# StopFailure hook -- error tracking for agent API failures
# Fires when an agent turn ends due to an API error. Appends a
# structured markdown entry to error-patterns.md with agent_type,
# timestamp, error type, and truncated error message (200 chars max).
#
# Non-enforcement hook: exits 0 always. No brain calls, no blocking.
# Retro lesson #003 compliant.

# Do NOT use set -e -- we want to continue on write failure
set -uo pipefail

# Require CLAUDE_PROJECT_DIR (or CURSOR_PROJECT_DIR)
PROJECT_DIR="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-}}"
if [ -z "$PROJECT_DIR" ]; then
  echo "WARNING: log-stop-failure.sh: CLAUDE_PROJECT_DIR is not set. Skipping." >&2
  exit 0
fi

PIPELINE_DIR="$PROJECT_DIR/docs/pipeline"
ERROR_FILE="$PIPELINE_DIR/error-patterns.md"

# Read stdin
INPUT=$(cat)

# Generate ISO8601 timestamp
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Parse fields -- try jq first, fall back to grep/sed
if command -v jq &>/dev/null; then
  AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null || true)
  ERROR_TYPE=$(echo "$INPUT" | jq -r '.error_type // empty' 2>/dev/null || true)
  ERROR_MESSAGE=$(echo "$INPUT" | jq -r '.error_message // empty' 2>/dev/null || true)
else
  # jq-free fallback: extract values using grep/sed
  AGENT_TYPE=$(echo "$INPUT" | grep -o '"agent_type":"[^"]*"' | sed 's/"agent_type":"//;s/"$//' || true)
  ERROR_TYPE=$(echo "$INPUT" | grep -o '"error_type":"[^"]*"' | sed 's/"error_type":"//;s/"$//' || true)
  ERROR_MESSAGE=$(echo "$INPUT" | grep -o '"error_message":"[^"]*"' | sed 's/"error_message":"//;s/"$//' || true)
fi

# Default empty fields to "unknown"
[ -z "$AGENT_TYPE" ] && AGENT_TYPE="unknown"
[ -z "$ERROR_TYPE" ] && ERROR_TYPE="unknown"
[ -z "$ERROR_MESSAGE" ] && ERROR_MESSAGE="unknown"

# Truncate error message to 200 characters
if [ "${#ERROR_MESSAGE}" -gt 200 ]; then
  ERROR_MESSAGE="${ERROR_MESSAGE:0:200}"
fi

# Ensure pipeline directory exists
if ! mkdir -p "$PIPELINE_DIR" 2>/dev/null; then
  echo "WARNING: log-stop-failure.sh: Cannot create pipeline directory." >&2
  exit 0
fi

# Create error-patterns.md with header if it does not exist
if [ ! -f "$ERROR_FILE" ]; then
  printf '# Error Patterns\n' > "$ERROR_FILE" 2>/dev/null || {
    echo "WARNING: log-stop-failure.sh: Cannot create error-patterns.md." >&2
    exit 0
  }
fi

# Append structured entry
{
  printf '\n### StopFailure: %s at %s\n\n' "$AGENT_TYPE" "$TIMESTAMP"
  printf -- '- Error: %s\n' "$ERROR_TYPE"
  printf -- '- Message: %s\n' "$ERROR_MESSAGE"
} >> "$ERROR_FILE" 2>/dev/null || {
  echo "WARNING: log-stop-failure.sh: Failed to append to error-patterns.md." >&2
}

exit 0
