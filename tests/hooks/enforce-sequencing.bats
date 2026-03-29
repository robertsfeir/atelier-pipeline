#!/usr/bin/env bats
# Tests for enforce-sequencing.sh (PreToolUse hook on Agent)
# Covers: T-0003-030, T-0003-042 through T-0003-048, T-0003-057
# Covers: T-0013-051 through T-0013-058 (ADR-0013 CI Watch gate)

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

# ── T-0003-044: Boundary -- Ellis with no PIPELINE_STATUS marker ────
# No structured marker means no active pipeline -- hook fails open (exit 0).
# This is intentional: free-form text in pipeline-state.md does not constitute
# a machine-readable pipeline status. See also T-0013-058 for malformed JSON.

@test "T-0003-044: Ellis invocation with no PIPELINE_STATUS marker exits 0 (fail-open)" {
  write_pipeline_freeform "Pipeline is running. Phase: review."

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

# ── T-0003-045: Boundary -- Ellis with malformed JSON ───────────────
# Malformed JSON in PIPELINE_STATUS cannot be parsed, so parse_pipeline_status
# returns empty. No parseable phase means no active pipeline -- fail-open.
# Consistent with T-0013-058.

@test "T-0003-045: Ellis invocation with malformed JSON in PIPELINE_STATUS exits 0 (fail-open)" {
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
  [ "$status" -eq 0 ]
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

# ── T-0003-057: Boundary -- free-form text fails open ───────────────
# Free-form text like "roz passed QA" has no structured PIPELINE_STATUS
# marker, so the hook treats it as no active pipeline -- fail-open (exit 0).
# The gate requires the machine-readable marker, not prose.

@test "T-0003-057: free-form text 'roz passed QA' does NOT satisfy the Ellis gate but fails open" {
  write_pipeline_freeform "roz passed QA with flying colors. Everything looks great."

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

# ═══════════════════════════════════════════════════════════════════════
# ADR-0013 CI Watch -- Step 6: Enforce-Sequencing Hook Gate
# Tests T-0013-051 through T-0013-058
# ═══════════════════════════════════════════════════════════════════════

# ── T-0013-051: Happy -- Ellis allowed with CI Watch active + CI_VERIFIED ──

@test "T-0013-051: Ellis allowed when ci_watch_active=true and roz_qa=CI_VERIFIED" {
  write_pipeline_status '{"roz_qa":"CI_VERIFIED","phase":"review","ci_watch_active":true,"ci_watch_retry_count":1}'

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

# ── T-0013-052: Failure -- Ellis blocked when CI Watch active but roz_qa empty ──

@test "T-0013-052: Ellis blocked when ci_watch_active=true but roz_qa is empty" {
  write_pipeline_status '{"roz_qa":"","phase":"review","ci_watch_active":true,"ci_watch_retry_count":0}'

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

# ── T-0013-053: Failure -- Ellis blocked when CI Watch inactive and roz_qa not PASS ──

@test "T-0013-053: Ellis blocked when ci_watch_active=false and roz_qa is not PASS" {
  write_pipeline_status '{"roz_qa":"FAIL","phase":"build","ci_watch_active":false}'

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

# ── T-0013-054: Happy -- Ellis allowed when CI Watch inactive and roz_qa=PASS ──

@test "T-0013-054: Ellis allowed when ci_watch_active=false and roz_qa=PASS (normal flow)" {
  write_pipeline_status '{"roz_qa":"PASS","phase":"review","ci_watch_active":false}'

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

# ── T-0013-055: Regression -- existing Gate 1 behavior unchanged ──

@test "T-0013-055: Ellis still blocked during active pipeline without Roz QA PASS (regression)" {
  write_pipeline_status '{"roz_qa":"","phase":"build"}'

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

# ── T-0013-056: Regression -- existing Gate 2 behavior unchanged ──

@test "T-0013-056: Agatha still blocked during build phase (regression)" {
  write_pipeline_status '{"roz_qa":"","phase":"build","ci_watch_active":true}'

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

# ── T-0013-057: Boundary -- PIPELINE_STATUS with CI Watch fields parses correctly ──

@test "T-0013-057: PIPELINE_STATUS JSON with ci_watch_active and roz_qa fields parses correctly" {
  # This test verifies the hook can parse the extended PIPELINE_STATUS JSON
  # that includes CI Watch fields alongside existing fields.
  # Uses roz_qa=PASS (normal flow) with ci_watch_active present but false --
  # hook should allow Ellis (PASS is still valid regardless of ci_watch_active).
  write_pipeline_status '{"roz_qa":"PASS","phase":"review","ci_watch_active":false,"ci_watch_retry_count":0,"ci_watch_commit_sha":"abc123"}'

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

# ── T-0013-059: Boundary -- CI_VERIFIED only works when ci_watch_active=true ──

@test "T-0013-059: Ellis blocked when ci_watch_active=false but roz_qa=CI_VERIFIED" {
  # CI_VERIFIED is only a valid pass token when ci_watch_active=true.
  # If ci_watch_active is false, CI_VERIFIED must NOT unlock Ellis --
  # this prevents a stale CI_VERIFIED from bypassing the gate.
  write_pipeline_status '{"roz_qa":"CI_VERIFIED","phase":"review","ci_watch_active":false}'

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

# ── T-0013-058: Failure -- malformed PIPELINE_STATUS JSON fails open ──

@test "T-0013-058: malformed PIPELINE_STATUS JSON with CI Watch fields exits 0 (fail-open)" {
  # When PIPELINE_STATUS contains malformed JSON, parse_pipeline_status returns
  # empty. With no parseable phase, the hook treats it as "no active pipeline"
  # and allows Ellis through (fail-open, existing behavior).
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

<!-- PIPELINE_STATUS: {"roz_qa":"CI_VERIFIED","ci_watch_active":true, broken -->
EOF

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
