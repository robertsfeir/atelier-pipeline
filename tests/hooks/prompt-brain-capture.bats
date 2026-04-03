#!/usr/bin/env bats
# Tests for ADR-0021 Step 1: prompt-brain-capture.sh (SubagentStop prompt hook)
# Covers: T-0021-002, T-0021-004, T-0021-007, T-0021-009, T-0021-010,
#         T-0021-011, T-0021-012, T-0021-014, T-0021-105, T-0021-109
#
# prompt-brain-capture.sh fires on SubagentStop as a "type": "prompt" hook.
# It outputs advisory text reminding Eva to call agent_capture for the key
# finding/decision from this agent's output. Exits 0 always.

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Step 1: prompt-brain-capture.sh Tests
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-002: Happy -- outputs advisory for capture-capable agent (cal) ──

@test "T-0021-002: prompt-brain-capture.sh outputs advisory text containing agent_capture for agent_type cal, exits 0" {
  local input
  input=$(build_subagent_stop_input "cal" "agent-abc123" "session-xyz789" "## DoR: Requirements\nSome output here")
  run run_hook_with_input "prompt-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]
  [[ "$output" == *"agent_capture"* ]]
}

# ── T-0021-004: Failure -- empty agent_type, exits 0 with no output ──

@test "T-0021-004: prompt-brain-capture.sh exits 0 with no output when agent_type is empty string" {
  local input
  input=$(build_subagent_stop_input "" "agent-abc123" "session-xyz789" "Some output")
  run run_hook_with_input "prompt-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0021-007: Boundary -- read-only agent (sentinel) gets no output ──

@test "T-0021-007: prompt-brain-capture.sh outputs nothing for read-only agent sentinel, exits 0" {
  local input
  input=$(build_subagent_stop_input "sentinel" "agent-sec456" "session-xyz789" "Security audit results")
  run run_hook_with_input "prompt-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0021-009: Error -- malformed JSON on stdin, graceful exit ──

@test "T-0021-009: prompt-brain-capture.sh exits 0 with no output when stdin contains malformed JSON" {
  prepare_hook "prompt-brain-capture.sh"
  run bash -c "echo 'this is not json {{{{' | bash '$TEST_TMPDIR/prompt-brain-capture.sh'"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0021-010: Regression -- settings.json has both prompt hooks with type "prompt" ──

@test "T-0021-010: settings.json contains both prompt hooks registered with type prompt" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  # Check prompt-brain-prefetch.sh is registered with type "prompt"
  # prompt-type hooks use .prompt field (not .command) for the script path
  local prefetch_type
  prefetch_type=$(jq -r '
    .hooks.PreToolUse[]
    | select(.matcher == "Agent")
    | .hooks[]
    | select((.prompt // "") | contains("prompt-brain-prefetch.sh"))
    | .type
  ' "$settings_file" 2>/dev/null)
  [ "$prefetch_type" = "prompt" ]

  # Check prompt-brain-capture.sh is registered with type "prompt"
  local capture_type
  capture_type=$(jq -r '
    .hooks.SubagentStop[]
    | .hooks[]
    | select((.prompt // "") | contains("prompt-brain-capture.sh"))
    | .type
  ' "$settings_file" 2>/dev/null)
  [ "$capture_type" = "prompt" ]
}

# ── T-0021-011: Regression -- prefetch hook registered on PreToolUse Agent matcher ──

@test "T-0021-011: prompt-brain-prefetch.sh is registered on PreToolUse matcher Agent in settings.json" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  # The hook must be under PreToolUse with matcher "Agent"
  # prompt-type hooks use .prompt field (not .command) for the script path
  local hook_command
  hook_command=$(jq -r '
    .hooks.PreToolUse[]
    | select(.matcher == "Agent")
    | .hooks[]
    | select((.prompt // "") | contains("prompt-brain-prefetch.sh"))
    | .prompt
  ' "$settings_file" 2>/dev/null)

  [ -n "$hook_command" ]
  [[ "$hook_command" == *"prompt-brain-prefetch.sh"* ]]
}

# ── T-0021-012: Regression -- capture hook registered on SubagentStop event ──

@test "T-0021-012: prompt-brain-capture.sh is registered on SubagentStop event in settings.json" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  # prompt-type hooks use .prompt field (not .command) for the script path
  local hook_command
  hook_command=$(jq -r '
    .hooks.SubagentStop[]
    | .hooks[]
    | select((.prompt // "") | contains("prompt-brain-capture.sh"))
    | .prompt
  ' "$settings_file" 2>/dev/null)

  [ -n "$hook_command" ]
  [[ "$hook_command" == *"prompt-brain-capture.sh"* ]]
}

# ── T-0021-014: Happy -- outputs advisory for roz, mentioning roz and agent_capture ──

@test "T-0021-014: prompt-brain-capture.sh outputs advisory mentioning roz and agent_capture for agent_type roz, exits 0" {
  local input
  input=$(build_subagent_stop_input "roz" "agent-roz789" "session-xyz789" "## DoR: QA Results\nAll checks pass")
  run run_hook_with_input "prompt-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]
  [[ "$output" == *"agent_capture"* ]]
  [[ "$output" == *"roz"* ]]
}

# ── T-0021-105: Regression -- settings.json is valid JSON after all hook registrations ──

@test "T-0021-105: settings.json is valid JSON parseable by jq after all ADR-0021 hook registrations" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  # jq . will exit non-zero if the JSON is malformed
  run jq '.' "$settings_file"
  [ "$status" -eq 0 ]
}

# ── T-0021-109: Error -- completely empty stdin, graceful exit ──

@test "T-0021-109: prompt-brain-capture.sh exits 0 with no output when stdin is completely empty" {
  prepare_hook "prompt-brain-capture.sh"
  run bash -c "echo -n '' | bash '$TEST_TMPDIR/prompt-brain-capture.sh'"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
