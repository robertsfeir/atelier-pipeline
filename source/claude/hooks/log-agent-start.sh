#!/bin/bash
# SubagentStart telemetry hook -- logs agent start events
# Fires on SubagentStart. Appends a JSON line to
# {config_dir}/telemetry/session-hooks.jsonl with event, agent_type,
# agent_id, session_id, and timestamp.
#
# Non-enforcement hook: exits 0 always. No brain calls, no blocking.
# Retro lesson #003 compliant.

# Do NOT use set -e -- we want to continue on write failure
set -uo pipefail

# Derive config directory from this script's location.
# Hook lives at {config_dir}/hooks/log-agent-start.sh, so dirname "$0"/.. gives config dir.
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

# Create telemetry directory if needed
if ! mkdir -p "$TELEMETRY_DIR" 2>/dev/null; then
  echo "WARNING: log-agent-start.sh: Cannot create telemetry directory." >&2
  exit 0
fi

# Generate ISO8601 timestamp
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Parse fields -- try jq first, fall back to grep/sed
if command -v jq &>/dev/null; then
  AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null || true)
  AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null || true)
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null || true)
else
  # jq-free fallback: extract values using grep/sed
  AGENT_TYPE=$(echo "$INPUT" | grep -o '"agent_type":"[^"]*"' | sed 's/"agent_type":"//;s/"$//' || true)
  AGENT_ID=$(echo "$INPUT" | grep -o '"agent_id":"[^"]*"' | sed 's/"agent_id":"//;s/"$//' || true)
  SESSION_ID=$(echo "$INPUT" | grep -o '"session_id":"[^"]*"' | sed 's/"session_id":"//;s/"$//' || true)
fi

# Default empty fields to "unknown"
[ -z "$AGENT_TYPE" ] && AGENT_TYPE="unknown"
[ -z "$AGENT_ID" ] && AGENT_ID="unknown"
[ -z "$SESSION_ID" ] && SESSION_ID="unknown"

# Write JSONL line via printf (works with or without jq)
LINE=$(printf '{"event":"start","agent_type":"%s","agent_id":"%s","session_id":"%s","timestamp":"%s"}' \
  "$AGENT_TYPE" "$AGENT_ID" "$SESSION_ID" "$TIMESTAMP")

# Append atomically -- >> is append-only
echo "$LINE" >> "$JSONL_FILE" 2>/dev/null || {
  echo "WARNING: log-agent-start.sh: Failed to write to JSONL file." >&2
}

exit 0
