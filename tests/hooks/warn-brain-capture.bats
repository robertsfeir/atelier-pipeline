#!/usr/bin/env bats
# Tests for ADR-0021 Step 3: warn-brain-capture.sh (SubagentStop warning hook)
# Covers: T-0021-052, T-0021-053, T-0021-054, T-0021-055, T-0021-056,
#         T-0021-057, T-0021-058, T-0021-059, T-0021-060, T-0021-061,
#         T-0021-106, T-0021-107, T-0021-110, T-0021-116
#
# warn-brain-capture.sh fires on SubagentStop for brain-access agents
# (cal, colby, roz, agatha). It checks last_assistant_message for the
# string "agent_capture" and warns on stderr when absent. Exits 0 always.
# Follows warn-dor-dod.sh pattern exactly.

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Step 3: warn-brain-capture.sh Tests
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-052: Happy -- agent_capture present, no stderr output ──

@test "T-0021-052: warn-brain-capture.sh exits 0 with no stderr when cal output contains agent_capture" {
  local input
  input=$(build_subagent_stop_input "cal" "agent-cal123" "session-xyz789" "## DoR: Decisions\nCalled agent_capture for ADR decision.\n## DoD: Done")
  run run_hook_with_input "warn-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]

  # No warning should appear in output (bats captures both stdout and stderr
  # in $output when using run, but warnings go to stderr which we check below)
  # The hook should produce NO stdout and NO stderr when agent_capture is found
  prepare_hook "warn-brain-capture.sh"
  local stderr_output
  stderr_output=$(echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" 2>&1 1>/dev/null || true)
  [ -z "$stderr_output" ]
}

# ── T-0021-053: Happy -- agent_capture absent, warning on stderr mentioning colby ──

@test "T-0021-053: warn-brain-capture.sh warns on stderr mentioning colby and brain capture when agent_capture absent from colby output" {
  local input
  input=$(build_subagent_stop_input "colby" "agent-colby456" "session-xyz789" "## DoR: Requirements\nBuilt the feature.\n## DoD: Done")

  prepare_hook "warn-brain-capture.sh"
  local stderr_output
  stderr_output=$(echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" 2>&1 1>/dev/null || true)

  [[ "$stderr_output" == *"colby"* ]]
  [[ "$stderr_output" == *"brain"* ]] || [[ "$stderr_output" == *"capture"* ]] || [[ "$stderr_output" == *"agent_capture"* ]]

  # Must exit 0
  local exit_code
  echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" >/dev/null 2>/dev/null
  exit_code=$?
  [ "$exit_code" -eq 0 ]
}

# ── T-0021-054: Boundary -- non-brain-access agent (ellis), exits silently ──

@test "T-0021-054: warn-brain-capture.sh exits 0 with no output for read-only agent ellis" {
  local input
  input=$(build_subagent_stop_input "ellis" "agent-ellis789" "session-xyz789" "Committed changes without agent_capture")
  run run_hook_with_input "warn-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]

  prepare_hook "warn-brain-capture.sh"
  local stderr_output
  stderr_output=$(echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" 2>&1 1>/dev/null || true)
  [ -z "$stderr_output" ]
}

# ── T-0021-055: Boundary -- non-brain-access agent (poirot), exits silently ──

@test "T-0021-055: warn-brain-capture.sh exits 0 with no output for read-only agent poirot" {
  local input
  input=$(build_subagent_stop_input "poirot" "agent-poirot123" "session-xyz789" "Review findings without agent_capture")
  run run_hook_with_input "warn-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]

  prepare_hook "warn-brain-capture.sh"
  local stderr_output
  stderr_output=$(echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" 2>&1 1>/dev/null || true)
  [ -z "$stderr_output" ]
}

# ── T-0021-056: Boundary -- agent_capture inside code block still passes ──

@test "T-0021-056: warn-brain-capture.sh exits 0 with no stderr when roz output contains agent_capture in code block" {
  local message='## DoR: QA\nFound patterns.\n```\nagent_capture called with thought_type pattern\n```\n## DoD: Done'
  local input
  input=$(build_subagent_stop_input "roz" "agent-roz456" "session-xyz789" "$message")

  prepare_hook "warn-brain-capture.sh"
  local stderr_output
  stderr_output=$(echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" 2>&1 1>/dev/null || true)
  [ -z "$stderr_output" ]

  # Must exit 0
  run run_hook_with_input "warn-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0021-057: Error -- missing last_assistant_message, warns about missing output ──

@test "T-0021-057: warn-brain-capture.sh exits 0 and warns on stderr about missing output when last_assistant_message absent" {
  # Build input without last_assistant_message field
  local input
  input=$(build_subagent_stop_input "cal" "agent-cal789" "session-xyz789")

  prepare_hook "warn-brain-capture.sh"
  local stderr_output
  stderr_output=$(echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" 2>&1 1>/dev/null || true)

  # Should have a warning about missing output
  [ -n "$stderr_output" ]

  # Must exit 0
  local exit_code
  echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" >/dev/null 2>/dev/null
  exit_code=$?
  [ "$exit_code" -eq 0 ]
}

# ── T-0021-058: Error -- no jq installed, graceful exit ──

@test "T-0021-058: warn-brain-capture.sh exits 0 with no output when jq is not available" {
  hide_jq
  local input
  input=$(build_subagent_stop_input "cal" "agent-cal123" "session-xyz789" "Some output without capture")
  run run_hook_with_input "warn-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
  restore_jq
}

# ── T-0021-059: Regression -- settings.json SubagentStop has warn-brain-capture.sh with if condition ──

@test "T-0021-059: settings.json SubagentStop contains warn-brain-capture.sh with if condition for cal colby roz agatha" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  # Find the warn-brain-capture.sh hook entry and extract its if field
  local if_value
  if_value=$(jq -r '
    .hooks.SubagentStop[]
    | .hooks[]
    | select(.command != null)
    | select(.command | contains("warn-brain-capture.sh"))
    | .["if"] // empty
  ' "$settings_file" 2>/dev/null)

  [ -n "$if_value" ]

  # The if condition must reference all four brain-access agents
  [[ "$if_value" == *"cal"* ]]
  [[ "$if_value" == *"colby"* ]]
  [[ "$if_value" == *"roz"* ]]
  [[ "$if_value" == *"agatha"* ]]
}

# ── T-0021-060: Regression -- exits 0 in ALL code paths ──

@test "T-0021-060: warn-brain-capture.sh exits 0 when agent_capture is absent (warns but does not block)" {
  # Test with brain-access agent whose output lacks agent_capture
  local input
  input=$(build_subagent_stop_input "colby" "agent-colby789" "session-xyz789" "Built feature without brain calls")
  run run_hook_with_input "warn-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0021-061: Regression -- source/hooks copy identical to .claude/hooks copy ──

@test "T-0021-061: source/hooks/warn-brain-capture.sh exists and is identical to .claude/hooks/warn-brain-capture.sh" {
  local source_file="$PROJECT_ROOT/source/hooks/warn-brain-capture.sh"
  local installed_file="$PROJECT_ROOT/.claude/hooks/warn-brain-capture.sh"

  [ -f "$source_file" ]
  [ -f "$installed_file" ]
  cmp -s "$source_file" "$installed_file"
}

# ── T-0021-106: Failure -- roz output without agent_capture triggers warning ──

@test "T-0021-106: warn-brain-capture.sh warns on stderr mentioning roz when agent_capture absent from roz output" {
  local input
  input=$(build_subagent_stop_input "roz" "agent-roz123" "session-xyz789" "## QA Report\nAll checks pass.\n## DoD: Done")

  prepare_hook "warn-brain-capture.sh"
  local stderr_output
  stderr_output=$(echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" 2>&1 1>/dev/null || true)

  [[ "$stderr_output" == *"roz"* ]]

  # Must exit 0
  run run_hook_with_input "warn-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0021-107: Failure -- agatha output without agent_capture triggers warning ──

@test "T-0021-107: warn-brain-capture.sh warns on stderr mentioning agatha when agent_capture absent from agatha output" {
  local input
  input=$(build_subagent_stop_input "agatha" "agent-agatha456" "session-xyz789" "## Docs Updated\nWrote the guide.\n## DoD: Done")

  prepare_hook "warn-brain-capture.sh"
  local stderr_output
  stderr_output=$(echo "$input" | bash "$TEST_TMPDIR/warn-brain-capture.sh" 2>&1 1>/dev/null || true)

  [[ "$stderr_output" == *"agatha"* ]]

  # Must exit 0
  run run_hook_with_input "warn-brain-capture.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0021-110: Error -- completely empty stdin, graceful exit ──

@test "T-0021-110: warn-brain-capture.sh exits 0 with no output when stdin is completely empty" {
  prepare_hook "warn-brain-capture.sh"
  run bash -c "echo -n '' | bash '$TEST_TMPDIR/warn-brain-capture.sh'"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0021-116: Regression -- source hook is executable ──

@test "T-0021-116: source/hooks/warn-brain-capture.sh is executable" {
  [ -x "$PROJECT_ROOT/source/hooks/warn-brain-capture.sh" ]
}
