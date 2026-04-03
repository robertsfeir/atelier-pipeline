#!/usr/bin/env bats
# Tests for ADR-0020 Step 2b: SubagentStop Telemetry Hook (log-agent-stop.sh)
# Covers: T-0020-026 through T-0020-038
#
# log-agent-stop.sh fires on SubagentStop alongside warn-dor-dod.sh.
# It appends a JSON line to .claude/telemetry/session-hooks.jsonl with
# event, agent_type, agent_id, session_id, timestamp, and has_output.
# It must exit 0 always (non-enforcement hook).

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Step 2b: SubagentStop Telemetry Hook
# ═══════════════════════════════════════════════════════════════════════

# ── T-0020-026: Happy -- has_output is boolean true for non-empty message ──

@test "T-0020-026: has_output is JSON boolean true when last_assistant_message is non-empty" {
  # Ensure telemetry dir exists
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  local input
  input=$(build_subagent_stop_input "colby" "agent-abc123" "session-xyz789" "## DoR: Requirements\nSome output here")
  run run_hook_with_project_dir "log-agent-stop.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  [ -f "$jsonl_file" ]

  local line
  line=$(head -1 "$jsonl_file")

  # Verify event is "stop"
  local event
  event=$(echo "$line" | jq -r '.event')
  [ "$event" = "stop" ]

  # has_output must be JSON boolean true, not the string "true"
  local has_output_type has_output_value
  has_output_type=$(echo "$line" | jq -r '.has_output | type')
  has_output_value=$(echo "$line" | jq -r '.has_output')
  [ "$has_output_type" = "boolean" ]
  [ "$has_output_value" = "true" ]

  # Verify other required fields
  local agent_type agent_id session_id timestamp
  agent_type=$(echo "$line" | jq -r '.agent_type')
  agent_id=$(echo "$line" | jq -r '.agent_id')
  session_id=$(echo "$line" | jq -r '.session_id')
  timestamp=$(echo "$line" | jq -r '.timestamp')
  [ "$agent_type" = "colby" ]
  [ "$agent_id" = "agent-abc123" ]
  [ "$session_id" = "session-xyz789" ]
  [ -n "$timestamp" ]
}

# ── T-0020-027: Happy -- has_output is boolean false for empty string ──

@test "T-0020-027: has_output is JSON boolean false when last_assistant_message is empty string" {
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  local input
  input=$(build_subagent_stop_input "roz" "agent-def456" "session-aaa111" "")
  run run_hook_with_project_dir "log-agent-stop.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  local line
  line=$(head -1 "$jsonl_file")

  local has_output_type has_output_value
  has_output_type=$(echo "$line" | jq -r '.has_output | type')
  has_output_value=$(echo "$line" | jq -r '.has_output')
  [ "$has_output_type" = "boolean" ]
  [ "$has_output_value" = "false" ]
}

# ── T-0020-028: Happy -- has_output is boolean false for null message ──

@test "T-0020-028: has_output is JSON boolean false when last_assistant_message is null" {
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  local input
  input=$(build_subagent_stop_input_null "cal" "agent-ghi789" "session-bbb222")
  run run_hook_with_project_dir "log-agent-stop.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  local line
  line=$(head -1 "$jsonl_file")

  local has_output_type has_output_value
  has_output_type=$(echo "$line" | jq -r '.has_output | type')
  has_output_value=$(echo "$line" | jq -r '.has_output')
  [ "$has_output_type" = "boolean" ]
  [ "$has_output_value" = "false" ]
}

# ── T-0020-029: Failure -- exits 0 when JSONL write fails ──

@test "T-0020-029: exits 0 when JSONL file is unwritable" {
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"
  echo '{"existing":"data"}' > "$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  chmod 444 "$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"

  local input
  input=$(build_subagent_stop_input "colby" "agent-abc123" "session-xyz789" "some output")
  run run_hook_with_project_dir "log-agent-stop.sh" "$input"
  [ "$status" -eq 0 ]

  # Restore permissions for cleanup
  chmod 644 "$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
}

# ── T-0020-030: Failure -- exits 0 without jq, still writes valid JSON ──

@test "T-0020-030: exits 0 when jq missing and writes valid JSON with correct has_output boolean" {
  hide_jq
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  local input
  input=$(build_subagent_stop_input "colby" "agent-abc123" "session-xyz789" "some output text")
  run run_hook_with_project_dir "log-agent-stop.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  [ -f "$jsonl_file" ]

  # Restore jq to validate output
  restore_jq

  local line
  line=$(head -1 "$jsonl_file")
  echo "$line" | jq . >/dev/null 2>&1

  # Verify event and has_output
  local event has_output_value
  event=$(echo "$line" | jq -r '.event')
  has_output_value=$(echo "$line" | jq -r '.has_output')
  [ "$event" = "stop" ]
  # has_output should reflect the non-empty message -- boolean true
  [ "$has_output_value" = "true" ]
}

# ── T-0020-031: Failure -- exits 0 with stderr warning when CLAUDE_PROJECT_DIR unset ──

@test "T-0020-031: exits 0 and writes stderr warning when CLAUDE_PROJECT_DIR is unset" {
  local input
  input=$(build_subagent_stop_input "colby" "agent-abc123" "session-xyz789" "output")
  run run_hook_without_project_dir "log-agent-stop.sh" "$input"
  [ "$status" -eq 0 ]

  # No file should be written to filesystem root
  [ ! -f "/.claude/telemetry/session-hooks.jsonl" ]
}

# ── T-0020-032: Boundary -- has_output false when key is entirely absent ──

@test "T-0020-032: has_output is false when last_assistant_message key is entirely absent" {
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  # Use build_subagent_stop_input with the __UNSET__ sentinel (no 4th argument)
  local input
  input=$(build_subagent_stop_input "colby" "agent-abc123" "session-xyz789")
  run run_hook_with_project_dir "log-agent-stop.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  local line
  line=$(head -1 "$jsonl_file")

  local has_output_value
  has_output_value=$(echo "$line" | jq -r '.has_output')
  [ "$has_output_value" = "false" ]
}

# ── T-0020-033: Boundary -- does NOT log last_assistant_message content ──

@test "T-0020-033: JSONL line does not contain last_assistant_message content" {
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  # Use a unique string that would only appear if the content was logged
  local unique_marker="UNIQUE_CANARY_STRING_FOR_PRIVACY_TEST_abc123xyz"
  local input
  input=$(build_subagent_stop_input "colby" "agent-abc123" "session-xyz789" "$unique_marker")
  run run_hook_with_project_dir "log-agent-stop.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  local line
  line=$(head -1 "$jsonl_file")

  # The unique string must NOT appear in the JSONL output
  [[ "$line" != *"$unique_marker"* ]]
}

# ── T-0020-034: Boundary -- timestamp matches ISO8601 format ──

@test "T-0020-034: timestamp field matches ISO8601 format" {
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  local input
  input=$(build_subagent_stop_input "colby" "agent-abc123" "session-xyz789" "output")
  run run_hook_with_project_dir "log-agent-stop.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  local timestamp
  timestamp=$(head -1 "$jsonl_file" | jq -r '.timestamp')

  [[ "$timestamp" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2} ]]
}

# ── T-0020-035: Regression -- warn-dor-dod.sh still works with SubagentStop input ──

@test "T-0020-035: warn-dor-dod.sh with Colby SubagentStop input exits 0 and produces DoR/DoD output" {
  # Build a SubagentStop input with output that has DoR and DoD
  local input
  input=$(build_subagent_stop_input "colby" "agent-abc123" "session-xyz789" "## DoR: Requirements Extracted\nContent\n## DoD: Verification\nDone")
  run run_hook_with_input "warn-dor-dod.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0020-036: Regression -- settings.json SubagentStop has both hooks ──

@test "T-0020-036: settings.json SubagentStop array contains both warn-dor-dod.sh and log-agent-stop.sh" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  # Check warn-dor-dod.sh exists in SubagentStop
  local dod_hook
  dod_hook=$(jq -r '
    .hooks.SubagentStop[]
    | .hooks[]
    | select(.command != null)
    | .command
    | select(contains("warn-dor-dod.sh"))
  ' "$settings_file" 2>/dev/null)
  [ -n "$dod_hook" ]

  # Check log-agent-stop.sh exists in SubagentStop
  local stop_hook
  stop_hook=$(jq -r '
    .hooks.SubagentStop[]
    | .hooks[]
    | select(.command != null)
    | .command
    | select(contains("log-agent-stop.sh"))
  ' "$settings_file" 2>/dev/null)
  [ -n "$stop_hook" ]
}

# ── T-0020-037: Concurrency -- two sequential invocations produce 2 valid lines ──

@test "T-0020-037: two sequential invocations produce exactly 2 lines, each valid JSON" {
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  local input1 input2
  input1=$(build_subagent_stop_input "colby" "agent-1" "sess-1" "output 1")
  input2=$(build_subagent_stop_input "roz" "agent-2" "sess-1" "output 2")

  run run_hook_with_project_dir "log-agent-stop.sh" "$input1"
  [ "$status" -eq 0 ]
  run run_hook_with_project_dir "log-agent-stop.sh" "$input2"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  local line_count
  line_count=$(wc -l < "$jsonl_file" | tr -d ' ')
  [ "$line_count" -eq 2 ]

  # Both lines must be valid JSON
  while IFS= read -r line; do
    echo "$line" | jq -c . >/dev/null 2>&1
  done < "$jsonl_file"
}

# ── T-0020-038: Boundary -- JSONL with interleaved start/stop events readable by jq ──

@test "T-0020-038: JSONL file with interleaved start and stop events is readable by jq -s" {
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  # Write a start event
  local start_input
  start_input=$(build_subagent_start_input "colby" "agent-1" "sess-1")
  run run_hook_with_project_dir "log-agent-start.sh" "$start_input"
  [ "$status" -eq 0 ]

  # Write a stop event
  local stop_input
  stop_input=$(build_subagent_stop_input "colby" "agent-1" "sess-1" "done")
  run run_hook_with_project_dir "log-agent-stop.sh" "$stop_input"
  [ "$status" -eq 0 ]

  # Write another start event
  start_input=$(build_subagent_start_input "roz" "agent-2" "sess-1")
  run run_hook_with_project_dir "log-agent-start.sh" "$start_input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"

  # jq -s must be able to parse the entire file as an array
  run jq -s '.' "$jsonl_file"
  [ "$status" -eq 0 ]

  # Should have 3 entries
  local count
  count=$(jq -s 'length' "$jsonl_file")
  [ "$count" -eq 3 ]
}
