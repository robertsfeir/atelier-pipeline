#!/usr/bin/env bats
# Tests for check-complexity.sh (PostToolUse hook)
# Covers: T-0003-002, T-0003-010 through T-0003-013

load test_helper

# ── T-0003-002: Security -- no eval() in the file ────────────────────

@test "T-0003-002: check-complexity.sh contains no eval() calls" {
  run grep -n 'eval ' "$HOOKS_DIR/check-complexity.sh"
  [ "$status" -ne 0 ]
}

# ── T-0003-010: Happy -- runs complexity command with file path ──────

@test "T-0003-010: with complexity command set, runs command with file path substituted" {
  # Create a marker file that the complexity command writes to
  local marker="$TEST_TMPDIR/complexity_ran"

  cat > "$TEST_TMPDIR/enforcement-config.json" << EOF
{
  "complexity_command": "touch $marker && echo checked {file}"
}
EOF

  local input
  input=$(build_tool_input "Write" "/project/src/feature.js")
  run run_hook_with_input "check-complexity.sh" "$input"
  [ "$status" -eq 0 ]
  [ -f "$marker" ]
}

# ── T-0003-011: Failure -- jq missing, exits 2 ──────────────────────

@test "T-0003-011: with jq missing, exits 2 with error message" {
  hide_jq
  local input
  input=$(build_tool_input "Write" "/project/src/feature.js")
  run run_hook_with_input "check-complexity.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"jq"* ]]
}

# ── T-0003-012: Boundary -- non-write tool exits 0 ──────────────────

@test "T-0003-012: tool_name is Read (not Write/Edit/MultiEdit), exits 0 without running" {
  cat > "$TEST_TMPDIR/enforcement-config.json" << 'EOF'
{
  "complexity_command": "exit 1"
}
EOF

  local input
  input=$(build_tool_input "Read" "/project/src/feature.js")
  run run_hook_with_input "check-complexity.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-013: Boundary -- .md file exits 0 ────────────────────────

@test "T-0003-013: file is .md (non-source), exits 0 without running" {
  cat > "$TEST_TMPDIR/enforcement-config.json" << 'EOF'
{
  "complexity_command": "exit 1"
}
EOF

  local input
  input=$(build_tool_input "Write" "/project/docs/readme.md")
  run run_hook_with_input "check-complexity.sh" "$input"
  [ "$status" -eq 0 ]
}
