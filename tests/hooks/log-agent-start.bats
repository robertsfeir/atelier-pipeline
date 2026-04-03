#!/usr/bin/env bats
# Tests for ADR-0020 Step 2a: SubagentStart Telemetry Hook (log-agent-start.sh)
# Covers: T-0020-011 through T-0020-025
#
# log-agent-start.sh fires on SubagentStart. It appends a JSON line to
# .claude/telemetry/session-hooks.jsonl with event, agent_type, agent_id,
# session_id, and timestamp. It must exit 0 always (non-enforcement hook).

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Step 2a: SubagentStart Hook
# ═══════════════════════════════════════════════════════════════════════

# ── T-0020-011: Happy -- creates directory and appends one JSON line ──

@test "T-0020-011: log-agent-start.sh creates .claude/telemetry/ dir and appends exactly one JSON line" {
  # Ensure telemetry dir does not exist
  [ ! -d "$TEST_TMPDIR/.claude/telemetry" ]

  local input
  input=$(build_subagent_start_input "colby" "agent-abc123" "session-xyz789")
  run run_hook_with_project_dir "log-agent-start.sh" "$input"
  [ "$status" -eq 0 ]

  # Directory was created
  [ -d "$TEST_TMPDIR/.claude/telemetry" ]

  # Exactly one line in the JSONL file
  local line_count
  line_count=$(wc -l < "$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl")
  [ "$line_count" -eq 1 ]
}

# ── T-0020-012: Happy -- JSON line has all required fields ──

@test "T-0020-012: appended JSON line is valid and contains event, agent_type, agent_id, session_id, timestamp" {
  local input
  input=$(build_subagent_start_input "colby" "agent-abc123" "session-xyz789")
  run run_hook_with_project_dir "log-agent-start.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  [ -f "$jsonl_file" ]

  # Parse with jq -- must be valid JSON
  local line
  line=$(head -1 "$jsonl_file")
  echo "$line" | jq . >/dev/null 2>&1

  # Check all required fields
  local event agent_type agent_id session_id timestamp
  event=$(echo "$line" | jq -r '.event')
  agent_type=$(echo "$line" | jq -r '.agent_type')
  agent_id=$(echo "$line" | jq -r '.agent_id')
  session_id=$(echo "$line" | jq -r '.session_id')
  timestamp=$(echo "$line" | jq -r '.timestamp')

  [ "$event" = "start" ]
  [ "$agent_type" = "colby" ]
  [ "$agent_id" = "agent-abc123" ]
  [ "$session_id" = "session-xyz789" ]
  [ -n "$timestamp" ]
}

# ── T-0020-013: Failure -- exits 0 when parent directory is unwritable ──

@test "T-0020-013: exits 0 when telemetry parent dir is unwritable and no JSONL file is created" {
  # Point CLAUDE_PROJECT_DIR to a read-only location
  local readonly_dir="$TEST_TMPDIR/readonly_project"
  mkdir -p "$readonly_dir/.claude"
  chmod 444 "$readonly_dir/.claude"

  local input
  input=$(build_subagent_start_input "colby" "agent-abc123" "session-xyz789")
  prepare_hook "log-agent-start.sh"
  run bash -c "echo '$input' | CLAUDE_PROJECT_DIR='$readonly_dir' bash '$TEST_TMPDIR/log-agent-start.sh'"
  [ "$status" -eq 0 ]

  # No JSONL file should exist
  [ ! -f "$readonly_dir/.claude/telemetry/session-hooks.jsonl" ]

  # Restore permissions for cleanup
  chmod 755 "$readonly_dir/.claude"
}

# ── T-0020-014: Failure -- exits 0 without jq and still writes valid JSON via printf ──

@test "T-0020-014: exits 0 when jq missing and writes valid JSON line via printf fallback" {
  hide_jq

  local input
  input=$(build_subagent_start_input "roz" "agent-def456" "session-aaa111")
  run run_hook_with_project_dir "log-agent-start.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  [ -f "$jsonl_file" ]

  # Restore jq to validate the output
  restore_jq
  local line
  line=$(head -1 "$jsonl_file")
  echo "$line" | jq . >/dev/null 2>&1

  local event
  event=$(echo "$line" | jq -r '.event')
  [ "$event" = "start" ]
}

# ── T-0020-015: Failure -- exits 0 with stderr warning when CLAUDE_PROJECT_DIR unset ──

@test "T-0020-015: exits 0 and writes stderr warning when CLAUDE_PROJECT_DIR is unset" {
  local input
  input=$(build_subagent_start_input "colby" "agent-abc123" "session-xyz789")
  run run_hook_without_project_dir "log-agent-start.sh" "$input"
  [ "$status" -eq 0 ]

  # No file should be written to filesystem root
  [ ! -f "/.claude/telemetry/session-hooks.jsonl" ]
}

# ── T-0020-016: Boundary -- unknown for empty/missing agent_type ──

@test "T-0020-016: writes 'unknown' for agent_type when input has empty agent_type field" {
  local input='{"agent_type":"","agent_id":"agent-123","session_id":"sess-456"}'
  run run_hook_with_project_dir "log-agent-start.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  [ -f "$jsonl_file" ]

  local agent_type
  agent_type=$(head -1 "$jsonl_file" | jq -r '.agent_type')
  [ "$agent_type" = "unknown" ]
}

# ── T-0020-017: Boundary -- unknown for absent session_id ──

@test "T-0020-017: writes 'unknown' for session_id when key is absent from input" {
  local input='{"agent_type":"colby","agent_id":"agent-123"}'
  run run_hook_with_project_dir "log-agent-start.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  [ -f "$jsonl_file" ]

  local session_id
  session_id=$(head -1 "$jsonl_file" | jq -r '.session_id')
  [ "$session_id" = "unknown" ]
}

# ── T-0020-018: Boundary -- 3 invocations produce 3 lines (append) ──

@test "T-0020-018: 3 sequential invocations produce exactly 3 lines in JSONL file" {
  local input1 input2 input3
  input1=$(build_subagent_start_input "colby" "agent-1" "sess-1")
  input2=$(build_subagent_start_input "roz" "agent-2" "sess-1")
  input3=$(build_subagent_start_input "ellis" "agent-3" "sess-1")

  run run_hook_with_project_dir "log-agent-start.sh" "$input1"
  [ "$status" -eq 0 ]
  run run_hook_with_project_dir "log-agent-start.sh" "$input2"
  [ "$status" -eq 0 ]
  run run_hook_with_project_dir "log-agent-start.sh" "$input3"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  local line_count
  line_count=$(wc -l < "$jsonl_file" | tr -d ' ')
  [ "$line_count" -eq 3 ]
}

# ── T-0020-019: Boundary -- timestamp matches ISO8601 format ──

@test "T-0020-019: timestamp field matches ISO8601 format (YYYY-MM-DDTHH:MM:SS)" {
  local input
  input=$(build_subagent_start_input "colby" "agent-abc123" "session-xyz789")
  run run_hook_with_project_dir "log-agent-start.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  local timestamp
  timestamp=$(head -1 "$jsonl_file" | jq -r '.timestamp')

  # Verify ISO8601 format: YYYY-MM-DDTHH:MM:SS (may have Z or timezone suffix)
  [[ "$timestamp" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2} ]]
}

# ── T-0020-020: Boundary -- path with spaces works correctly ──

@test "T-0020-020: writes JSONL correctly when CLAUDE_PROJECT_DIR path contains a space" {
  local spaced_dir="$TEST_TMPDIR/my project"
  mkdir -p "$spaced_dir"

  local input
  input=$(build_subagent_start_input "colby" "agent-abc" "sess-xyz")
  prepare_hook "log-agent-start.sh"
  run bash -c "echo '$input' | CLAUDE_PROJECT_DIR='$spaced_dir' bash '$TEST_TMPDIR/log-agent-start.sh'"
  [ "$status" -eq 0 ]

  local jsonl_file="$spaced_dir/.claude/telemetry/session-hooks.jsonl"
  [ -f "$jsonl_file" ]

  # Verify the line is valid JSON
  head -1 "$jsonl_file" | jq . >/dev/null 2>&1
}

# ── T-0020-021: Concurrency -- two simultaneous invocations produce 2 valid lines ──

@test "T-0020-021: two simultaneous invocations produce two independently valid JSON lines" {
  prepare_hook "log-agent-start.sh"
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"

  local input1 input2
  input1=$(build_subagent_start_input "colby" "agent-1" "sess-concurrent")
  input2=$(build_subagent_start_input "roz" "agent-2" "sess-concurrent")

  # Launch both in background
  echo "$input1" | CLAUDE_PROJECT_DIR="$TEST_TMPDIR" bash "$TEST_TMPDIR/log-agent-start.sh" &
  local pid1=$!
  echo "$input2" | CLAUDE_PROJECT_DIR="$TEST_TMPDIR" bash "$TEST_TMPDIR/log-agent-start.sh" &
  local pid2=$!

  wait "$pid1"
  wait "$pid2"

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  [ -f "$jsonl_file" ]

  # Each line should be independently valid JSON
  local line_count
  line_count=$(wc -l < "$jsonl_file" | tr -d ' ')
  [ "$line_count" -eq 2 ]

  # Both lines must parse as valid JSON
  while IFS= read -r line; do
    echo "$line" | jq . >/dev/null 2>&1
  done < "$jsonl_file"
}

# ── T-0020-022: Security -- no prompt/context content in JSONL ──

@test "T-0020-022: JSONL line contains only the 5 contract fields, no agent prompt or context" {
  local input
  input=$(build_subagent_start_input "colby" "agent-abc123" "session-xyz789")
  run run_hook_with_project_dir "log-agent-start.sh" "$input"
  [ "$status" -eq 0 ]

  local jsonl_file="$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  local line
  line=$(head -1 "$jsonl_file")

  # Verify exactly 5 keys (event, agent_type, agent_id, session_id, timestamp)
  local key_count
  key_count=$(echo "$line" | jq 'keys | length')
  [ "$key_count" -eq 5 ]

  # Verify the keys are exactly the contract fields
  echo "$line" | jq -e 'has("event")' >/dev/null
  echo "$line" | jq -e 'has("agent_type")' >/dev/null
  echo "$line" | jq -e 'has("agent_id")' >/dev/null
  echo "$line" | jq -e 'has("session_id")' >/dev/null
  echo "$line" | jq -e 'has("timestamp")' >/dev/null
}

# ── T-0020-023: Happy -- settings.json contains SubagentStart hook entry ──

@test "T-0020-023: settings.json contains a SubagentStart hook entry for log-agent-start.sh" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  # Check for SubagentStart event with log-agent-start.sh
  local hook_command
  hook_command=$(jq -r '
    .hooks.SubagentStart[]
    | .hooks[]
    | .command
    | select(contains("log-agent-start.sh"))
  ' "$settings_file" 2>/dev/null)

  [ -n "$hook_command" ]
}

# ── T-0020-024: Happy -- SKILL.md includes log-agent-start.sh ──

@test "T-0020-024: SKILL.md installation manifest includes log-agent-start.sh as SubagentStart hook" {
  local skill_file="$PROJECT_ROOT/skills/pipeline-setup/SKILL.md"
  [ -f "$skill_file" ]

  # SKILL.md should reference log-agent-start.sh
  grep -q "log-agent-start.sh" "$skill_file"

  # SKILL.md should reference SubagentStart event
  grep -q "SubagentStart" "$skill_file"
}

# ── T-0020-025: Failure -- exits 0 when JSONL file exists but is not writable ──

@test "T-0020-025: exits 0 when JSONL file exists but is not writable (chmod 444)" {
  # Create the telemetry dir and an unwritable JSONL file
  mkdir -p "$TEST_TMPDIR/.claude/telemetry"
  echo '{"existing":"data"}' > "$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
  chmod 444 "$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"

  local input
  input=$(build_subagent_start_input "colby" "agent-abc123" "session-xyz789")
  run run_hook_with_project_dir "log-agent-start.sh" "$input"
  [ "$status" -eq 0 ]

  # Restore permissions for cleanup
  chmod 644 "$TEST_TMPDIR/.claude/telemetry/session-hooks.jsonl"
}
