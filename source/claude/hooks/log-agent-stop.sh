#!/bin/bash
# SubagentStop telemetry hook -- logs agent stop events
# Fires on SubagentStop. Appends a JSON line
# to {config_dir}/telemetry/session-hooks.jsonl with event, agent_type,
# agent_id, session_id, timestamp, and has_output (boolean).
#
# Does NOT inspect or log last_assistant_message content (privacy).
# Non-enforcement hook: exits 0 always. No brain calls, no blocking.
# Retro lesson #003 compliant.

# Do NOT use set -e -- we want to continue on write failure
set -uo pipefail

# Derive config directory from this script's location.
# Hook lives at {config_dir}/hooks/log-agent-stop.sh, so dirname "$0"/.. gives config dir.
# Follow symlinks to handle both direct execution and symlinked invocation.
SCRIPT_PATH="$0"
# If symlinked, resolve to canonical path
if [ -L "$SCRIPT_PATH" ]; then
  SCRIPT_PATH="$(cd "$(dirname "$SCRIPT_PATH")" && readlink -f "$SCRIPT_PATH")"
fi
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
CONFIG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

TELEMETRY_DIR="$CONFIG_DIR/telemetry"
JSONL_FILE="$TELEMETRY_DIR/session-hooks.jsonl"

# Read stdin
INPUT=$(cat)

# Source shared hook library (ADR-0034 Wave 2 Step 2.1)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/hook-lib.sh" ]; then
  source "$SCRIPT_DIR/hook-lib.sh" 2>/dev/null || true
fi

# Create telemetry directory if needed
if ! mkdir -p "$TELEMETRY_DIR" 2>/dev/null; then
  echo "WARNING: log-agent-stop.sh: Cannot create telemetry directory." >&2
  exit 0
fi

# Generate ISO8601 timestamp
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Parse fields and determine has_output -- try jq first, fall back to grep/sed
if command -v jq &>/dev/null; then
  AGENT_TYPE=$(echo "$INPUT" | hook_lib_get_agent_type 2>/dev/null || true)
  AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null || true)
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null || true)
  # Check if last_assistant_message is a non-empty, non-null string
  HAS_OUTPUT_RAW=$(echo "$INPUT" | jq -r '
    if .last_assistant_message == null then "false"
    elif (.last_assistant_message | type) != "string" then "false"
    elif (.last_assistant_message | length) == 0 then "false"
    else "true"
    end
  ' 2>/dev/null || echo "false")
else
  # jq-free fallback: extract values using grep/sed
  AGENT_TYPE=$(echo "$INPUT" | grep -o '"agent_type":"[^"]*"' | sed 's/"agent_type":"//;s/"$//' || true)
  AGENT_ID=$(echo "$INPUT" | grep -o '"agent_id":"[^"]*"' | sed 's/"agent_id":"//;s/"$//' || true)
  SESSION_ID=$(echo "$INPUT" | grep -o '"session_id":"[^"]*"' | sed 's/"session_id":"//;s/"$//' || true)
  # Check for non-empty last_assistant_message via grep
  # Match "last_assistant_message":"<something non-empty>"
  if echo "$INPUT" | grep -qE '"last_assistant_message":"[^"]' 2>/dev/null; then
    HAS_OUTPUT_RAW="true"
  else
    HAS_OUTPUT_RAW="false"
  fi
fi

# Default empty fields to "unknown"
[ -z "$AGENT_TYPE" ] && AGENT_TYPE="unknown"
[ -z "$AGENT_ID" ] && AGENT_ID="unknown"
[ -z "$SESSION_ID" ] && SESSION_ID="unknown"

# Write JSONL line -- has_output is an unquoted JSON boolean
LINE=$(printf '{"event":"stop","agent_type":"%s","agent_id":"%s","session_id":"%s","timestamp":"%s","has_output":%s}' \
  "$AGENT_TYPE" "$AGENT_ID" "$SESSION_ID" "$TIMESTAMP" "$HAS_OUTPUT_RAW")

# Append atomically
echo "$LINE" >> "$JSONL_FILE" 2>/dev/null || {
  echo "WARNING: log-agent-stop.sh: Failed to write to JSONL file." >&2
}

exit 0
