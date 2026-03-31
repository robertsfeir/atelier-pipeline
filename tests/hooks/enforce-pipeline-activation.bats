#!/usr/bin/env bats
# Tests for enforce-pipeline-activation.sh (PreToolUse hook on Agent)
# Blocks Colby/Ellis invocation when no active pipeline exists.

load test_helper

# ── Happy path: active pipeline allows Colby ──────────────────────────

@test "Colby allowed when pipeline has active phase (build)" {
  write_pipeline_status '{"phase":"build","roz_qa":""}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── Happy path: active pipeline allows Ellis ──────────────────────────

@test "Ellis allowed when pipeline has active phase (review)" {
  write_pipeline_status '{"phase":"review","roz_qa":"PASS"}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── Blocked: no pipeline-state.md file ────────────────────────────────

@test "Colby blocked when pipeline-state.md does not exist" {
  rm -f "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
  [[ "$output" == *"colby"* ]]
  [[ "$output" == *"/pipeline"* ]]
}

# ── Blocked: pipeline-state.md exists but no PIPELINE_STATUS marker ───

@test "Ellis blocked when pipeline-state.md has no PIPELINE_STATUS marker" {
  write_pipeline_freeform "Pipeline is running. Phase: review."

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
  [[ "$output" == *"ellis"* ]]
}

# ── Blocked: phase is idle ────────────────────────────────────────────

@test "Colby blocked when phase is idle" {
  write_pipeline_status '{"phase":"idle","roz_qa":""}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
  [[ "$output" == *"colby"* ]]
}

# ── Blocked: phase is complete ────────────────────────────────────────

@test "Ellis blocked when phase is complete" {
  write_pipeline_status '{"phase":"complete","roz_qa":"PASS"}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
  [[ "$output" == *"ellis"* ]]
}

# ── Blocked: phase is none ────────────────────────────────────────────

@test "Colby blocked when phase is none" {
  write_pipeline_status '{"phase":"none","roz_qa":""}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── Blocked: phase is COMPLETE (case-insensitive) ─────────────────────

@test "Colby blocked when phase is COMPLETE (uppercase)" {
  write_pipeline_status '{"phase":"COMPLETE","roz_qa":"PASS"}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── Allow: non-colby/ellis agents always pass ─────────────────────────

@test "Roz allowed even without active pipeline" {
  rm -f "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "roz")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

@test "Cal allowed even without active pipeline" {
  rm -f "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "cal")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

@test "Agatha allowed even without active pipeline" {
  rm -f "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "agatha")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── Allow: non-main-thread (subagent context) always passes ───────────

@test "Colby from subagent context (agent_id set) always exits 0" {
  rm -f "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby" "subagent-123")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── Allow: config missing (not yet set up) ────────────────────────────

@test "Hook exits 0 when enforcement-config.json is missing" {
  rm -f "$TEST_TMPDIR/enforcement-config.json"

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── Failure: jq missing ──────────────────────────────────────────────

@test "Hook exits 2 when jq is missing" {
  hide_jq
  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"jq"* ]]
}

# ── Blocked: malformed JSON in PIPELINE_STATUS ────────────────────────

@test "Colby blocked when PIPELINE_STATUS contains malformed JSON" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

<!-- PIPELINE_STATUS: {phase: broken, not json} -->
EOF

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── Happy path: architecture phase is active ──────────────────────────

@test "Colby allowed when phase is architecture" {
  write_pipeline_status '{"phase":"architecture","roz_qa":""}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── Happy path: implement phase is active ─────────────────────────────

@test "Ellis allowed when phase is implement" {
  write_pipeline_status '{"phase":"implement","roz_qa":"PASS","telemetry_captured":"true"}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── Non-Agent tool ignored ────────────────────────────────────────────

@test "Non-Agent tool (Write) is ignored by this hook" {
  local input
  input=$(build_tool_input "Write" "src/test.js" "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── Blocked message includes agent name ───────────────────────────────

@test "Block message names colby when colby is blocked" {
  write_pipeline_status '{"phase":"complete","roz_qa":"PASS"}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"colby"* ]]
}

@test "Block message names ellis when ellis is blocked" {
  write_pipeline_status '{"phase":"idle","roz_qa":""}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "ellis")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"ellis"* ]]
}

# ── Blocked: phase is IDLE (mixed case) ──────────────────────────────

@test "Colby blocked when phase is Idle (mixed case)" {
  write_pipeline_status '{"phase":"Idle","roz_qa":""}'

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "pipeline_state_dir": "$TEST_TMPDIR/docs/pipeline"
}
EOF

  local input
  input=$(build_agent_input "colby")
  run run_hook_with_input "enforce-pipeline-activation.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}
