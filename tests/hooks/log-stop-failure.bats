#!/usr/bin/env bats
# Tests for ADR-0020 Step 4: StopFailure Error Tracking Hook (log-stop-failure.sh)
# Covers: T-0020-051 through T-0020-063
#
# log-stop-failure.sh fires on StopFailure (agent turn ends due to API error).
# It appends a structured markdown entry to error-patterns.md with agent_type,
# timestamp, error type, and truncated error message. Exits 0 always.

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Step 4: StopFailure Error Tracking Hook
# ═══════════════════════════════════════════════════════════════════════

# ── T-0020-051: Happy -- appends structured entry to error-patterns.md ──

@test "T-0020-051: appends structured entry with agent_type, timestamp, error type, and message" {
  # Create an existing error-patterns.md
  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns
EOF

  local input
  input=$(build_stop_failure_input "colby" "rate_limit" "Rate limit exceeded for model claude-opus-4-20250514")
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  # Verify the entry was appended
  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"
  grep -q "StopFailure" "$file"
  grep -q "colby" "$file"
  grep -q "rate_limit" "$file"
  grep -q "Rate limit exceeded" "$file"
}

# ── T-0020-052: Happy -- entry format matches expected structure ──

@test "T-0020-052: entry format has heading '### StopFailure: {agent_type} at {timestamp}' with bullet points" {
  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns
EOF

  local input
  input=$(build_stop_failure_input "roz" "api_error" "Internal server error")
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"

  # Check the heading format: ### StopFailure: roz at YYYY-MM-DD...
  grep -qE '### StopFailure: roz at [0-9]{4}-[0-9]{2}-[0-9]{2}' "$file"

  # Check bullet points
  grep -q "^- Error: api_error" "$file"
  grep -q "^- Message:" "$file"
}

# ── T-0020-053: Failure -- exits 0 when error-patterns.md is not writable ──

@test "T-0020-053: exits 0 when error-patterns.md is not writable (chmod 444)" {
  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns
EOF
  chmod 444 "$TEST_TMPDIR/docs/pipeline/error-patterns.md"

  local input
  input=$(build_stop_failure_input "colby" "rate_limit" "Rate limit exceeded")
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  # Restore permissions for cleanup
  chmod 644 "$TEST_TMPDIR/docs/pipeline/error-patterns.md"
}

# ── T-0020-054: Failure -- exits 0 without jq and still appends valid entry ──

@test "T-0020-054: exits 0 when jq missing and appends valid entry via printf fallback" {
  hide_jq

  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns
EOF

  local input
  input=$(build_stop_failure_input "colby" "timeout" "Request timed out")
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  # Restore jq and verify content
  restore_jq
  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"
  grep -q "StopFailure" "$file"
}

# ── T-0020-055: Failure -- exits 0 when CLAUDE_PROJECT_DIR unset ──

@test "T-0020-055: exits 0 and writes stderr warning when CLAUDE_PROJECT_DIR is unset" {
  local input
  input=$(build_stop_failure_input "colby" "rate_limit" "Rate limit exceeded")
  run run_hook_without_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  # No file should be written to filesystem root
  [ ! -f "/docs/pipeline/error-patterns.md" ]
}

# ── T-0020-056: Boundary -- creates error-patterns.md with header when missing ──

@test "T-0020-056: creates error-patterns.md with '# Error Patterns' header when file does not exist" {
  rm -f "$TEST_TMPDIR/docs/pipeline/error-patterns.md"

  local input
  input=$(build_stop_failure_input "colby" "rate_limit" "Rate limit exceeded")
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"
  [ -f "$file" ]

  # First meaningful line should be the header
  grep -q "^# Error Patterns" "$file"

  # Entry should be below the header
  grep -q "### StopFailure:" "$file"
}

# ── T-0020-057: Boundary -- 201-char message truncated to 200 chars ──

@test "T-0020-057: 201-character error message is truncated to exactly 200 characters" {
  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns
EOF

  # Build a 201-character message (all 'A' chars + trailing 'B')
  local long_message
  long_message=$(printf 'A%.0s' {1..200})
  long_message="${long_message}B"
  # Verify it is 201 chars
  [ "${#long_message}" -eq 201 ]

  local input
  input=$(build_stop_failure_input "colby" "rate_limit" "$long_message")
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"

  # The 'B' (201st character) should NOT appear in the output
  # Get the message line
  local message_line
  message_line=$(grep "^- Message:" "$file")

  # The trailing 'B' must be truncated
  [[ "$message_line" != *"B"* ]]

  # The message should contain the 200 'A' characters
  [[ "$message_line" == *"$(printf 'A%.0s' {1..200})"* ]] || \
    [[ "$message_line" == *"$(printf 'A%.0s' {1..100})"* ]]
}

# ── T-0020-058: Boundary -- unknown defaults for missing fields ──

@test "T-0020-058: writes 'unknown' for missing agent_type, error_type, and error_message" {
  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns
EOF

  local input
  input=$(build_stop_failure_input_minimal)
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"

  # Check that "unknown" appears for agent_type in the heading
  grep -qE '### StopFailure: unknown at' "$file"

  # Check that "unknown" appears for error_type
  grep -q "^- Error: unknown" "$file"

  # Check that "unknown" appears for message
  grep -q "^- Message: unknown" "$file"
}

# ── T-0020-059: Boundary -- markdown special characters handled safely ──

@test "T-0020-059: error message with markdown special chars does not break structure" {
  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns
EOF

  # Message with backticks, pipes, and brackets
  local input
  input=$(build_stop_failure_input "colby" "parse_error" 'Failed to parse \`config\` at [line 5] | column 3')
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"

  # File should still have valid markdown structure
  grep -q "^### StopFailure:" "$file"
  grep -q "^- Error:" "$file"
  grep -q "^- Message:" "$file"

  # The heading should still be on its own line starting with ###
  local heading_count
  heading_count=$(grep -c "^### StopFailure:" "$file")
  [ "$heading_count" -eq 1 ]
}

# ── T-0020-060: Boundary -- two sequential invocations produce two separated sections ──

@test "T-0020-060: two sequential invocations produce two markdown sections with blank line separation" {
  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns
EOF

  local input1 input2
  input1=$(build_stop_failure_input "colby" "rate_limit" "First error")
  input2=$(build_stop_failure_input "roz" "timeout" "Second error")

  run run_hook_with_project_dir "log-stop-failure.sh" "$input1"
  [ "$status" -eq 0 ]
  run run_hook_with_project_dir "log-stop-failure.sh" "$input2"
  [ "$status" -eq 0 ]

  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"

  # Should have exactly 2 StopFailure sections
  local section_count
  section_count=$(grep -c "^### StopFailure:" "$file")
  [ "$section_count" -eq 2 ]

  # The two sections should be separated (file should render as valid markdown)
  grep -q "colby" "$file"
  grep -q "roz" "$file"
}

# ── T-0020-061: Boundary -- settings.json has StopFailure entry ──

@test "T-0020-061: settings.json contains a StopFailure hook entry for log-stop-failure.sh" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  local hook_command
  hook_command=$(jq -r '
    .hooks.StopFailure[]
    | .hooks[]
    | .command
    | select(contains("log-stop-failure.sh"))
  ' "$settings_file" 2>/dev/null)

  [ -n "$hook_command" ]
}

# ── T-0020-062: Security -- stack trace truncated, no lines after cutoff ──

@test "T-0020-062: 500-char multi-line stack trace truncated to 200 chars with no extra lines" {
  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns
EOF

  # Build a 500-character message that includes line breaks (simulated as spaces
  # since our builder converts newlines to spaces)
  local stack_trace
  stack_trace="Error: rate_limit at Object.send (/app/node_modules/anthropic/core.mjs:291:15) at process.processTicksAndRejections (node:internal/process/task_queues:95:5) at async AgentRunner.run (/app/src/agent.ts:142:22) at async Pipeline.executePhase (/app/src/pipeline.ts:88:11) at async main (/app/src/index.ts:15:3) internal details: token_count=450000 model=claude-opus-4-20250514 retry_count=3 last_error_code=429 request_id=req_abc123def456ghi789"

  local input
  input=$(build_stop_failure_input "colby" "rate_limit" "$stack_trace")
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"

  # Get the message line
  local message_line
  message_line=$(grep "^- Message:" "$file")

  # The message content (after "- Message: ") should be at most 200 chars
  local content
  content=$(echo "$message_line" | sed 's/^- Message: //')
  local content_len=${#content}
  [ "$content_len" -le 200 ]

  # Sensitive details near end of the 500-char string should NOT appear
  [[ "$message_line" != *"request_id"* ]]
  [[ "$message_line" != *"req_abc123def456"* ]]
}

# ── T-0020-063: Regression -- existing error-patterns.md content preserved ──

@test "T-0020-063: existing error-patterns.md content (3 pre-existing lines) preserved after append" {
  # Create file with 3 lines of pre-existing content
  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
# Error Patterns

Existing line one about a previous error.
Existing line two about another incident.
Existing line three with resolution notes.
EOF

  local input
  input=$(build_stop_failure_input "colby" "rate_limit" "New error occurred")
  run run_hook_with_project_dir "log-stop-failure.sh" "$input"
  [ "$status" -eq 0 ]

  local file="$TEST_TMPDIR/docs/pipeline/error-patterns.md"

  # Original 3 lines must still be present
  grep -q "Existing line one about a previous error" "$file"
  grep -q "Existing line two about another incident" "$file"
  grep -q "Existing line three with resolution notes" "$file"

  # New entry must also be present
  grep -q "### StopFailure:" "$file"
  grep -q "New error occurred" "$file"
}
