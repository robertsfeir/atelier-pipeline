#!/usr/bin/env bats
# Tests for check-brain-usage.sh (PostToolUse hook on Agent)
# Covers: T-0003-032, T-0003-033

load test_helper

# ── T-0003-032: Failure -- jq missing ───────────────────────────────

@test "T-0003-032: with jq missing, exits 2" {
  hide_jq
  local input
  input=$(build_brain_check_input "colby" "some output")
  run run_hook_with_input "check-brain-usage.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"jq"* ]]
}

# ── T-0003-033: Security -- word splitting in brain_required_agents ──

@test "T-0003-033: word splitting in brain_required_agents does not cause false matches" {
  # Create a config with an agent name that could be word-split
  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline",
  "brain_required_agents": ["cal", "colby roz"]
}
EOF

  # Write brain state as available
  write_brain_state "true"

  # "roz" alone should NOT match "colby roz" -- the while-read loop
  # compares the full array element, not individual words
  local input
  input=$(build_brain_check_input "roz" "did some work without brain")
  run run_hook_with_input "check-brain-usage.sh" "$input"
  # roz is not in the list (only "colby roz" as a single entry), so no warning
  [ "$status" -eq 0 ]
  [[ "$output" != *"WARNING"* ]]
}

# ── Additional coverage: brain usage detection ───────────────────────

@test "check-brain-usage: warns when brain-required agent has no brain evidence" {
  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline",
  "brain_required_agents": ["colby"]
}
EOF

  write_brain_state "true"

  local input
  input=$(build_brain_check_input "colby" "implemented the feature, all tests pass")
  run run_hook_with_input "check-brain-usage.sh" "$input"
  [ "$status" -eq 0 ]
  [[ "$output" == *"WARNING"* ]]
  [[ "$output" == *"colby"* ]]
}

@test "check-brain-usage: no warning when brain evidence is present" {
  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline",
  "brain_required_agents": ["colby"]
}
EOF

  write_brain_state "true"

  local input
  input=$(build_brain_check_input "colby" "called agent_search and found 3 results, then agent_capture to save insight")
  run run_hook_with_input "check-brain-usage.sh" "$input"
  [ "$status" -eq 0 ]
  [[ "$output" != *"WARNING"* ]]
}

@test "check-brain-usage: skips check when brain is not available" {
  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline",
  "brain_required_agents": ["colby"]
}
EOF

  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State
brain_available: false
EOF

  local input
  input=$(build_brain_check_input "colby" "no brain usage at all")
  run run_hook_with_input "check-brain-usage.sh" "$input"
  [ "$status" -eq 0 ]
  [[ "$output" != *"WARNING"* ]]
}

@test "check-brain-usage: skips check for non-brain-required agents" {
  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline",
  "brain_required_agents": ["colby"]
}
EOF

  write_brain_state "true"

  local input
  input=$(build_brain_check_input "distillator" "compressed the document")
  run run_hook_with_input "check-brain-usage.sh" "$input"
  [ "$status" -eq 0 ]
  [[ "$output" != *"WARNING"* ]]
}

@test "check-brain-usage: non-Agent tool_name exits 0 immediately" {
  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline",
  "brain_required_agents": ["colby"]
}
EOF

  prepare_hook "check-brain-usage.sh"
  local input='{"tool_name":"Write","tool_input":{"subagent_type":"colby"}}'
  run bash -c "echo '$input' | bash '$TEST_TMPDIR/check-brain-usage.sh'"
  [ "$status" -eq 0 ]
}
