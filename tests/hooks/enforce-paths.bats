#!/usr/bin/env bats
# Tests for enforce-paths.sh (PreToolUse hook)
# Covers: T-0003-014 through T-0003-029

load test_helper

# ── T-0003-014: Happy -- cal writing to docs/architecture ───────────

@test "T-0003-014: cal writing to docs/architecture/foo.md exits 0" {
  local input
  input=$(build_tool_input "Write" "docs/architecture/foo.md" "cal")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-015: Failure -- cal writing to src ────────────────────────

@test "T-0003-015: cal writing to src/main.js exits 2 with BLOCKED" {
  local input
  input=$(build_tool_input "Write" "src/main.js" "cal")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-016: Security -- path anchoring ──────────────────────────

@test "T-0003-016: absolute path not anchored to project root is blocked for cal" {
  # A path like "/home/user/docs/architecture/evil" should NOT match
  # because enforce-paths normalizes absolute paths by stripping $PWD prefix.
  # If the path is outside $PWD, it stays absolute and won't match "docs/architecture".
  local input
  input=$(build_tool_input "Write" "/home/user/docs/architecture/evil" "cal")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-017: Happy -- colby writing to src ────────────────────────

@test "T-0003-017: colby writing to src/feature.js exits 0" {
  local input
  input=$(build_tool_input "Write" "src/feature.js" "colby")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-018: Failure -- colby writing to docs ─────────────────────

@test "T-0003-018: colby writing to docs/guide/foo.md exits 2 with BLOCKED" {
  local input
  input=$(build_tool_input "Write" "docs/guide/foo.md" "colby")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-019: Failure -- jq missing ───────────────────────────────

@test "T-0003-019: with jq missing, exits 2" {
  hide_jq
  local input
  input=$(build_tool_input "Write" "src/main.js" "colby")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"jq"* ]]
}

# ── T-0003-020: Happy -- roz writing test file ──────────────────────

@test "T-0003-020: roz writing to tests/foo.test.js exits 0" {
  local input
  input=$(build_tool_input "Write" "tests/foo.test.js" "roz")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-021: Failure -- roz writing to src ────────────────────────

@test "T-0003-021: roz writing to src/main.js exits 2" {
  local input
  input=$(build_tool_input "Write" "src/main.js" "roz")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-022: Happy -- main thread writing to docs/pipeline ───────

@test "T-0003-022: main thread writing to docs/pipeline/state.md exits 0" {
  local input
  input=$(build_tool_input "Write" "docs/pipeline/state.md" "")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-023: Failure -- main thread writing to src ────────────────

@test "T-0003-023: main thread writing to src/main.js exits 2" {
  local input
  input=$(build_tool_input "Write" "src/main.js" "")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-024: Boundary -- unknown agent ────────────────────────────

@test "T-0003-024: unknown agent type writing any file exits 2" {
  local input
  input=$(build_tool_input "Write" "anything.txt" "unknown_agent")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-025: Happy -- ellis writing to any file ──────────────────

@test "T-0003-025: ellis writing to any file exits 0" {
  local input
  input=$(build_tool_input "Write" "src/main.js" "ellis")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-026: Happy -- agatha writing to docs ─────────────────────

@test "T-0003-026: agatha writing to docs/guide/foo.md exits 0" {
  local input
  input=$(build_tool_input "Write" "docs/guide/foo.md" "agatha")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-027: Failure -- agatha writing to src ─────────────────────

@test "T-0003-027: agatha writing to src/main.js exits 2" {
  local input
  input=$(build_tool_input "Write" "src/main.js" "agatha")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-028: Security -- word splitting in test_patterns ─────────

@test "T-0003-028: word splitting in test_patterns does not cause unexpected matching" {
  # Add a test pattern with spaces to config -- the while-read loop should
  # handle it correctly without word splitting
  cat > "$TEST_TMPDIR/enforcement-config.json" << 'EOF'
{
  "pipeline_state_dir": "docs/pipeline",
  "architecture_dir": "docs/architecture",
  "product_specs_dir": "docs/product",
  "ux_docs_dir": "docs/ux",
  "colby_blocked_paths": ["docs/"],
  "test_patterns": [".test.", "space pattern", "/tests/"],
  "brain_required_agents": []
}
EOF

  # A file that does NOT match any test pattern should be blocked for roz
  local input
  input=$(build_tool_input "Write" "src/space.js" "roz")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]

  # A file that matches a normal test pattern should still work
  input=$(build_tool_input "Write" "src/foo.test.js" "roz")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 0 ]
}

# ── T-0003-029: Security -- word splitting in colby_blocked_paths ───

@test "T-0003-029: word splitting in colby_blocked_paths does not cause unexpected matching" {
  cat > "$TEST_TMPDIR/enforcement-config.json" << 'EOF'
{
  "pipeline_state_dir": "docs/pipeline",
  "architecture_dir": "docs/architecture",
  "product_specs_dir": "docs/product",
  "ux_docs_dir": "docs/ux",
  "colby_blocked_paths": ["docs/", "path with spaces/"],
  "test_patterns": [".test."],
  "brain_required_agents": []
}
EOF

  # A normal source file should NOT be blocked
  local input
  input=$(build_tool_input "Write" "src/feature.js" "colby")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 0 ]

  # A file in docs/ should still be blocked
  input=$(build_tool_input "Write" "docs/readme.md" "colby")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
}
