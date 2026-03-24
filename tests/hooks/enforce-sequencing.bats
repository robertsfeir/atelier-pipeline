#!/usr/bin/env bats
# Tests for enforce-sequencing.sh (PreToolUse hook on Agent)
# Covers: T-0003-030, T-0003-042 through T-0003-048, T-0003-057

load test_helper

# ── T-0003-030: Failure -- jq missing ───────────────────────────────

@test "T-0003-030: with jq missing, exits 2" {
  hide_jq
  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-sequencing.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"jq"* ]]
}

# ── T-0003-042: Happy -- Ellis with roz_qa=PASS ─────────────────────

@test "T-0003-042: Ellis invocation with roz_qa=PASS exits 0" {
  write_pipeline_status '{"roz_qa":"PASS","phase":"review"}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-sequencing.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-043: Failure -- Ellis with roz_qa=FAIL ───────────────────

@test "T-0003-043: Ellis invocation with roz_qa=FAIL exits 2" {
  write_pipeline_status '{"roz_qa":"FAIL","phase":"review"}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-sequencing.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-044: Failure -- Ellis with no PIPELINE_STATUS marker ─────

@test "T-0003-044: Ellis invocation with no PIPELINE_STATUS marker exits 2" {
  write_pipeline_freeform "Pipeline is running. Phase: review."

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-sequencing.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-045: Failure -- Ellis with malformed JSON ────────────────

@test "T-0003-045: Ellis invocation with malformed JSON in PIPELINE_STATUS exits 2" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

<!-- PIPELINE_STATUS: {roz_qa: PASS, broken json} -->
EOF

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-sequencing.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-046: Boundary -- Agatha during build phase ───────────────

@test "T-0003-046: Agatha invocation during build phase exits 2" {
  write_pipeline_status '{"roz_qa":"","phase":"build"}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "agatha")
  run run_hook_with_input "enforce-sequencing.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
  [[ "$output" == *"Agatha"* ]]
}

# ── T-0003-047: Happy -- Agatha during review phase ────────────────

@test "T-0003-047: Agatha invocation during review phase exits 0" {
  write_pipeline_status '{"roz_qa":"PASS","phase":"review"}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "agatha")
  run run_hook_with_input "enforce-sequencing.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-048: Happy -- non-main-thread always exits 0 ────────────

@test "T-0003-048: non-main-thread (agent_id set) invocations always exit 0" {
  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis" "subagent-123")
  run run_hook_with_input "enforce-sequencing.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-057: Regression -- free-form text doesn't satisfy gate ───

@test "T-0003-057: free-form text 'roz passed QA' does NOT satisfy the Ellis gate" {
  write_pipeline_freeform "roz passed QA with flying colors. Everything looks great."

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-sequencing.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}
