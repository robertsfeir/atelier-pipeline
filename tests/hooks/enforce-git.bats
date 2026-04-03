#!/usr/bin/env bats
# Tests for enforce-git.sh (PreToolUse hook on Bash)
# Covers: T-0003-031

load test_helper

# ── T-0003-031: Failure -- jq missing ───────────────────────────────

@test "T-0003-031: with jq missing, exits 2" {
  hide_jq
  local input
  input=$(build_bash_input "git status")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"jq"* ]]
}

# ── Additional coverage: git write operations blocked from main thread

@test "enforce-git: git commit from main thread exits 2 with BLOCKED" {
  local input
  input=$(build_bash_input "git commit -m test")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

@test "enforce-git: git push from main thread exits 2 with BLOCKED" {
  local input
  input=$(build_bash_input "git push origin main")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

@test "enforce-git: git add from main thread exits 2 with BLOCKED" {
  local input
  input=$(build_bash_input "git add .")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

@test "enforce-git: git status from main thread exits 0 (read-only)" {
  local input
  input=$(build_bash_input "git status")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 0 ]
}

@test "enforce-git: git diff from main thread exits 0 (read-only)" {
  local input
  input=$(build_bash_input "git diff --stat")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 0 ]
}

@test "enforce-git: git commit from Ellis (agent_type=ellis) exits 0" {
  local input
  input=$(build_bash_input "git commit -m test" "ellis-123" "ellis")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 0 ]
}

@test "enforce-git: git commit from Colby (agent_type=colby) exits 2 BLOCKED" {
  local input
  input=$(build_bash_input "git commit -m test" "colby-456" "colby")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

@test "enforce-git: git commit from Roz (agent_type=roz) exits 2 BLOCKED" {
  local input
  input=$(build_bash_input "git commit -m test" "roz-789" "roz")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

@test "enforce-git: git push from Ellis (agent_type=ellis) exits 0" {
  local input
  input=$(build_bash_input "git push origin main" "ellis-123" "ellis")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 0 ]
}

@test "enforce-git: git add from Cal (agent_type=cal) exits 2 BLOCKED" {
  local input
  input=$(build_bash_input "git add ." "cal-111" "cal")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

@test "enforce-git: git status from Colby (read-only) exits 0" {
  local input
  input=$(build_bash_input "git status" "colby-456" "colby")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 0 ]
}

@test "enforce-git: test execution from Roz (agent_type=roz) exits 0" {
  local input
  input=$(build_bash_input "bats tests/hooks/enforce-git.bats" "roz-789" "roz")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 0 ]
}

@test "enforce-git: test execution from Colby (agent_type=colby) exits 0" {
  local input
  input=$(build_bash_input "jest --testPathPattern=foo.test.ts" "colby-456" "colby")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 0 ]
}

@test "enforce-git: test execution from Cal (agent_type=cal) exits 2 BLOCKED" {
  local input
  input=$(build_bash_input "pytest tests/" "cal-111" "cal")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

@test "enforce-git: subagent with agent_id but no agent_type is blocked" {
  local input
  input=$(build_bash_input "git commit -m test" "unknown-999")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

@test "enforce-git: non-Bash tool_name exits 0" {
  prepare_hook "enforce-git.sh"
  local input='{"tool_name":"Write","tool_input":{"command":"git commit -m test"}}'
  run bash -c "echo '$input' | bash '$TEST_TMPDIR/enforce-git.sh'"
  [ "$status" -eq 0 ]
}

@test "enforce-git: git reset from main thread exits 2 with BLOCKED" {
  local input
  input=$(build_bash_input "git reset --hard HEAD")
  run run_hook_with_input "enforce-git.sh" "$input"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}
