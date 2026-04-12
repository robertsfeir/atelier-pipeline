#!/bin/bash
# hook-lib.sh -- Shared hook utility library (ADR-0034 Wave 2 Step 2.1)
#
# Source this file from any hook that needs the shared parsers:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   if [ -f "$SCRIPT_DIR/hook-lib.sh" ]; then
#     source "$SCRIPT_DIR/hook-lib.sh"
#   fi
#
# All functions read from stdin when they need input. Callers pipe data in:
#   echo "$INPUT" | hook_lib_get_agent_type
#   cat "$STATE_FILE" | hook_lib_pipeline_status_field phase
#
# Non-blocking by design: all functions exit 0 on parse failure and return
# empty output. Callers treat empty output as "field absent / fail-open".
# Retro lesson #003 compliant.

# ─── hook_lib_pipeline_status_field <field> ───────────────────────────────────
#
# Reads stdin, finds the PIPELINE_STATUS JSON marker, and returns the value
# of the named field. Uses jq which is brace-aware (fixes the S22 regression
# where grep -o cut off on embedded } in field values).
#
# Format expected on stdin:
#   <!-- PIPELINE_STATUS: {"phase":"build","feature":"x",...} -->
#
# Usage:
#   value=$(cat "$STATE_FILE" | hook_lib_pipeline_status_field phase)
#
# Returns empty and exits 1 when field is absent or JSON is malformed.

hook_lib_pipeline_status_field() {
  local field="$1"
  local line json value

  # Read stdin line by line; find the PIPELINE_STATUS marker line
  while IFS= read -r line; do
    if [[ "$line" == *"PIPELINE_STATUS: {"* ]]; then
      # Strip everything before the opening { of the JSON object
      json="${line#*PIPELINE_STATUS: }"
      # Strip the trailing HTML comment suffix --> (and any whitespace)
      json="${json% -->}"
      # Also strip bare --> without leading space (avoids quoting issue with }
      # inside the parameter expansion by using a variable for the suffix)
      _suffix='-->'
      json="${json%"$_suffix"}"
      break
    fi
  done

  [ -z "$json" ] && return 1

  value=$(printf '%s' "$json" | jq -r --arg f "$field" '.[$f] // empty' 2>/dev/null) || return 1
  [ -z "$value" ] && return 1
  printf '%s\n' "$value"
}

# ─── hook_lib_json_escape ─────────────────────────────────────────────────────
#
# Reads a raw string from stdin and outputs a valid JSON string literal
# (including the surrounding double-quotes). Uses jq -Rs to handle all
# special characters: newlines, tabs, backslashes, quotes, unicode.
#
# This replaces the broken sed-based json_escape in session-boot.sh (S22).
#
# Usage:
#   escaped=$(printf '%s' "$value" | hook_lib_json_escape)
#
# The output is a complete JSON string literal, e.g.: "line1\nline2"

hook_lib_json_escape() {
  jq -Rs '.' 2>/dev/null
}

# ─── hook_lib_get_agent_type ──────────────────────────────────────────────────
#
# Reads JSON from stdin, returns the agent type string.
# Priority: .agent_type (top-level) > .tool_input.subagent_type
# Returns empty string when neither field is present.
#
# Usage:
#   agent=$(echo "$INPUT" | hook_lib_get_agent_type)

hook_lib_get_agent_type() {
  jq -r '.agent_type // .tool_input.subagent_type // empty' 2>/dev/null
}

# ─── hook_lib_assert_agent_type <expected> ────────────────────────────────────
#
# Reads JSON from stdin. Calls hook_lib_get_agent_type and compares to
# the expected value. Exits non-zero with a message if mismatch.
#
# Usage:
#   echo "$INPUT" | hook_lib_assert_agent_type "ellis"

hook_lib_assert_agent_type() {
  local expected="$1"
  local actual
  actual=$(hook_lib_get_agent_type)
  if [ "$actual" != "$expected" ]; then
    echo "ERROR: Expected agent_type '$expected' but got '${actual:-<empty>}'" >&2
    return 1
  fi
}

# ─── hook_lib_emit_deny <message> ─────────────────────────────────────────────
#
# Emits the standard Claude hook JSON deny response to stdout.
# Callers should exit 2 after calling this function.
#
# Usage:
#   hook_lib_emit_deny "BLOCKED: reason"
#   exit 2

hook_lib_emit_deny() {
  local message="$1"
  local escaped_message
  escaped_message=$(printf '%s' "$message" | jq -Rs '.' 2>/dev/null || printf '"%s"' "$message")
  printf '{"decision":"block","reason":%s}\n' "$escaped_message"
}

# ─── hook_lib_emit_allow ──────────────────────────────────────────────────────
#
# Emits the standard Claude hook JSON allow response to stdout.
#
# Usage:
#   hook_lib_emit_allow

hook_lib_emit_allow() {
  printf '{"decision":"allow"}\n'
}
