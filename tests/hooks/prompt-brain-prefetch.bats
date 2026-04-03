#!/usr/bin/env bats
# Tests for ADR-0021 Step 1: prompt-brain-prefetch.sh (PreToolUse prompt hook)
# Covers: T-0021-001, T-0021-003, T-0021-005, T-0021-006, T-0021-008,
#         T-0021-013, T-0021-015, T-0021-099, T-0021-100, T-0021-117
#
# prompt-brain-prefetch.sh fires on PreToolUse(Agent) as a "type": "prompt"
# hook. It outputs advisory text reminding Eva to call agent_search before
# constructing the invocation. Exits 0 always.

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Step 1: prompt-brain-prefetch.sh Tests
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-001: Happy -- outputs advisory for capture-capable agent (colby) ──

@test "T-0021-001: prompt-brain-prefetch.sh outputs advisory text containing agent_search for agent_type colby, exits 0" {
  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "prompt-brain-prefetch.sh" "$input"
  [ "$status" -eq 0 ]
  [[ "$output" == *"agent_search"* ]]
}

# ── T-0021-003: Failure -- missing tool_input field, graceful degradation ──

@test "T-0021-003: prompt-brain-prefetch.sh exits 0 with no output when tool_input field is missing" {
  local input='{"tool_name":"Agent"}'
  run run_hook_with_input "prompt-brain-prefetch.sh" "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0021-005: Boundary -- read-only agent (ellis) gets no output ──

@test "T-0021-005: prompt-brain-prefetch.sh outputs nothing for read-only agent ellis, exits 0" {
  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "prompt-brain-prefetch.sh" "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0021-006: Boundary -- read-only agent (poirot/investigator) gets no output ──

@test "T-0021-006: prompt-brain-prefetch.sh outputs nothing for read-only agent poirot, exits 0" {
  local input
  input=$(build_agent_input "poirot")
  run run_hook_with_input "prompt-brain-prefetch.sh" "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0021-008: Error -- no jq installed, graceful exit ──

@test "T-0021-008: prompt-brain-prefetch.sh exits 0 with no output when jq is not available" {
  hide_jq
  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "prompt-brain-prefetch.sh" "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
  restore_jq
}

# ── T-0021-013: Happy -- outputs advisory for capture-capable agent (cal) ──

@test "T-0021-013: prompt-brain-prefetch.sh outputs advisory mentioning cal and agent_search for agent_type cal, exits 0" {
  local input
  input=$(build_agent_input "cal")
  run run_hook_with_input "prompt-brain-prefetch.sh" "$input"
  [ "$status" -eq 0 ]
  [[ "$output" == *"agent_search"* ]]
  [[ "$output" == *"cal"* ]]
}

# ── T-0021-015: Happy -- outputs advisory for capture-capable agent (agatha) ──

@test "T-0021-015: prompt-brain-prefetch.sh outputs advisory text for agent_type agatha, exits 0" {
  local input
  input=$(build_agent_input "agatha")
  run run_hook_with_input "prompt-brain-prefetch.sh" "$input"
  [ "$status" -eq 0 ]
  [[ "$output" == *"agent_search"* ]]
}

# ── T-0021-099: Error -- completely empty stdin, graceful exit ──

@test "T-0021-099: prompt-brain-prefetch.sh exits 0 with no output when stdin is completely empty" {
  prepare_hook "prompt-brain-prefetch.sh"
  run bash -c "echo -n '' | bash '$TEST_TMPDIR/prompt-brain-prefetch.sh'"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0021-100: Regression -- installed hooks are executable ──

@test "T-0021-100: .claude/hooks/prompt-brain-prefetch.sh and prompt-brain-capture.sh are executable" {
  [ -x "$PROJECT_ROOT/.claude/hooks/prompt-brain-prefetch.sh" ]
  [ -x "$PROJECT_ROOT/.claude/hooks/prompt-brain-capture.sh" ]
}

# ── T-0021-117: Regression -- source hooks are executable ──

@test "T-0021-117: source/hooks/prompt-brain-prefetch.sh and prompt-brain-capture.sh are executable" {
  [ -x "$PROJECT_ROOT/source/hooks/prompt-brain-prefetch.sh" ]
  [ -x "$PROJECT_ROOT/source/hooks/prompt-brain-capture.sh" ]
}
