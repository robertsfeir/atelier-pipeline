#!/usr/bin/env bats
# Tests for ADR-0020 Step 1: `if` Conditionals on Existing Hooks
# Covers: T-0020-001 through T-0020-010
#
# These tests verify that settings.json and SKILL.md contain the correct
# `if` conditional fields on hook entries. No hook script changes are
# involved -- the `if` field is a Claude Code engine feature that prevents
# process spawning when the condition does not match.

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Step 1: `if` Conditionals
# ═══════════════════════════════════════════════════════════════════════

# ── T-0020-001: Happy -- enforce-git.sh has `if` field in settings.json ──

@test "T-0020-001: settings.json enforce-git.sh hook entry has if field with tool_input.command.includes('git ')" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  # Find the Bash matcher hook entry and check for the `if` field
  # The if field should be on the hook entry for enforce-git.sh
  local if_value
  if_value=$(jq -r '
    .hooks.PreToolUse[]
    | select(.matcher == "Bash")
    | .hooks[]
    | select(.command | contains("enforce-git.sh"))
    | .["if"] // empty
  ' "$settings_file")

  [ -n "$if_value" ]
  [[ "$if_value" == *"tool_input.command"* ]]
  [[ "$if_value" == *"git "* ]]
}

# ── T-0020-002: Happy -- warn-dor-dod.sh has `if` field in settings.json ──

@test "T-0020-002: settings.json warn-dor-dod.sh hook entry has if field matching colby or roz agent_type" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  local if_value
  if_value=$(jq -r '
    .hooks.SubagentStop[]
    | .hooks[]
    | select(.command != null)
    | select(.command | contains("warn-dor-dod.sh"))
    | .["if"] // empty
  ' "$settings_file")

  [ -n "$if_value" ]
  [[ "$if_value" == *"agent_type"* ]]
  [[ "$if_value" == *"colby"* ]]
  [[ "$if_value" == *"roz"* ]]
}

# ── T-0020-003: Regression -- existing enforce-git.bats tests pass ──
# Note: This is verified by running the full test suite. The test here
# confirms the hook itself has not changed behavior.

@test "T-0020-003: enforce-git.sh still blocks git commit from main thread after if-conditional changes" {
  local input
  input=$(build_bash_input "git commit -m test")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0020-004: Regression -- enforce-paths.sh still works ──

@test "T-0020-004: enforce-paths.sh still blocks colby writing to docs after settings.json changes" {
  local input
  input=$(build_tool_input "Write" "docs/guide/foo.md" "colby")
  run run_hook_with_input "enforce-paths.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0020-005: Regression -- enforce-sequencing.sh still works ──

@test "T-0020-005: enforce-sequencing.sh still blocks Ellis without Roz QA PASS" {
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

# ── T-0020-006: Regression -- enforce-pipeline-activation.sh still works ──

@test "T-0020-006: enforce-pipeline-activation.sh still blocks Colby without active pipeline" {
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
}

# ── T-0020-007: Boundary -- SKILL.md template matches settings.json ──

@test "T-0020-007: SKILL.md hook registration template contains same if values as installed settings.json" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  local skill_file="$PROJECT_ROOT/skills/pipeline-setup/SKILL.md"
  [ -f "$settings_file" ]
  [ -f "$skill_file" ]

  # Extract if value from settings.json for enforce-git.sh
  local git_if
  git_if=$(jq -r '
    .hooks.PreToolUse[]
    | select(.matcher == "Bash")
    | .hooks[]
    | select(.command | contains("enforce-git.sh"))
    | .["if"] // empty
  ' "$settings_file")

  # Verify SKILL.md contains the same if value
  [ -n "$git_if" ]
  grep -qF "$git_if" "$skill_file"

  # Extract if value from settings.json for warn-dor-dod.sh
  local dod_if
  dod_if=$(jq -r '
    .hooks.SubagentStop[]
    | .hooks[]
    | select(.command != null)
    | select(.command | contains("warn-dor-dod.sh"))
    | .["if"] // empty
  ' "$settings_file")

  [ -n "$dod_if" ]
  grep -qF "$dod_if" "$skill_file"
}

# ── T-0020-008: Failure -- enforce-git.sh direct call still enforces ──

@test "T-0020-008: enforce-git.sh called directly (bypassing if filter) with git commit still exits 2 BLOCKED" {
  # This verifies the `if` optimization did not alter the script's enforcement.
  # Even though the `if` conditional would normally prevent spawning for
  # non-git commands, when the script IS spawned, it must still enforce.
  local input
  input=$(build_bash_input "git commit -m 'test message'")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0020-009: Failure -- enforce-git.sh if field is a valid non-empty string ──

@test "T-0020-009: settings.json enforce-git.sh hook entry if field is a non-empty string" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  # Verify the if field exists, is a string, and is not empty
  local if_type
  if_type=$(jq -r '
    .hooks.PreToolUse[]
    | select(.matcher == "Bash")
    | .hooks[]
    | select(.command | contains("enforce-git.sh"))
    | .["if"]
    | type
  ' "$settings_file")
  [ "$if_type" = "string" ]

  local if_length
  if_length=$(jq -r '
    .hooks.PreToolUse[]
    | select(.matcher == "Bash")
    | .hooks[]
    | select(.command | contains("enforce-git.sh"))
    | .["if"]
    | length
  ' "$settings_file")
  [ "$if_length" -gt 0 ]
}

# ── T-0020-010: Failure -- warn-dor-dod.sh if field is a valid non-empty string ──

@test "T-0020-010: settings.json warn-dor-dod.sh hook entry if field is a non-empty string" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  local if_type
  if_type=$(jq -r '
    .hooks.SubagentStop[]
    | .hooks[]
    | select(.command != null)
    | select(.command | contains("warn-dor-dod.sh"))
    | .["if"]
    | type
  ' "$settings_file")
  [ "$if_type" = "string" ]

  local if_length
  if_length=$(jq -r '
    .hooks.SubagentStop[]
    | .hooks[]
    | select(.command != null)
    | select(.command | contains("warn-dor-dod.sh"))
    | .["if"]
    | length
  ' "$settings_file")
  [ "$if_length" -gt 0 ]
}
