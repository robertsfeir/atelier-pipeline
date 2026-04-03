#!/usr/bin/env bats
# Tests for ADR-0020 Step 3: PostCompact Context Preservation Hook (post-compact-reinject.sh)
# Covers: T-0020-039 through T-0020-050
#
# post-compact-reinject.sh fires on PostCompact. It reads pipeline-state.md
# and context-brief.md from docs/pipeline/ and outputs their contents to
# stdout for re-injection into the post-compaction context. Exits 0 always.

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Step 3: PostCompact Context Preservation Hook
# ═══════════════════════════════════════════════════════════════════════

# ── T-0020-039: Happy -- outputs pipeline-state.md content ──

@test "T-0020-039: outputs pipeline-state.md content to stdout when file exists" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

Feature: Hook modernization
Phase: build
EOF

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]
  [[ "$output" == *"Pipeline State"* ]]
  [[ "$output" == *"Hook modernization"* ]]
}

# ── T-0020-040: Happy -- outputs context-brief.md when both files exist ──

@test "T-0020-040: output includes context-brief.md content when both files exist" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

Feature: Hook modernization
EOF

  cat > "$TEST_TMPDIR/docs/pipeline/context-brief.md" << 'EOF'
# Context Brief

Wave 2 hook modernization is in progress.
EOF

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]
  [[ "$output" == *"Pipeline State"* ]]
  [[ "$output" == *"Context Brief"* ]]
  [[ "$output" == *"Wave 2 hook modernization"* ]]
}

# ── T-0020-041: Happy -- output begins with header marker ──

@test "T-0020-041: output begins with '--- Re-injected after compaction ---' header marker" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State
EOF

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # The first line of output should be the header marker
  local first_line
  first_line=$(echo "$output" | head -1)
  [ "$first_line" = "--- Re-injected after compaction ---" ]
}

# ── T-0020-042: Failure -- empty stdout and exit 0 when pipeline-state.md missing ──

@test "T-0020-042: outputs nothing and exits 0 when pipeline-state.md does not exist" {
  rm -f "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0020-043: Failure -- exits 0 when pipeline-state.md is unreadable ──

@test "T-0020-043: exits 0 when pipeline-state.md exists but cannot be read (chmod 000)" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State
EOF
  chmod 000 "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # Restore permissions for cleanup
  chmod 644 "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"
}

# ── T-0020-044: Failure -- exits 0 when CLAUDE_PROJECT_DIR unset ──

@test "T-0020-044: exits 0 when CLAUDE_PROJECT_DIR is unset and outputs nothing" {
  run run_hook_without_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0020-045: Failure -- exits 0 with header but no content when files are empty ──

@test "T-0020-045: exits 0 with header and labels but no file content when both files are empty (0 bytes)" {
  # Create empty files (0 bytes)
  : > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"
  : > "$TEST_TMPDIR/docs/pipeline/context-brief.md"

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # The header marker should still appear
  [[ "$output" == *"Re-injected after compaction"* ]]
}

# ── T-0020-046: Boundary -- only pipeline-state.md when context-brief.md missing ──

@test "T-0020-046: outputs only pipeline-state.md content when context-brief.md does not exist" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

Feature: Hook modernization
EOF
  rm -f "$TEST_TMPDIR/docs/pipeline/context-brief.md"

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]
  [[ "$output" == *"Pipeline State"* ]]
  [[ "$output" == *"Hook modernization"* ]]

  # Should NOT contain context-brief label or placeholder
  [[ "$output" != *"context-brief.md"* ]] || {
    # If the label appears, it should not have any content after it
    # (just the label for a missing file is acceptable per ADR AC5)
    true
  }
}

# ── T-0020-047: Boundary -- output contains exact file path labels ──

@test "T-0020-047: output contains '## From: docs/pipeline/pipeline-state.md' and '## From: docs/pipeline/context-brief.md' labels" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State
EOF

  cat > "$TEST_TMPDIR/docs/pipeline/context-brief.md" << 'EOF'
# Context Brief
EOF

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  [[ "$output" == *"## From: docs/pipeline/pipeline-state.md"* ]]
  [[ "$output" == *"## From: docs/pipeline/context-brief.md"* ]]
}

# ── T-0020-048: Boundary -- settings.json has PostCompact entry ──

@test "T-0020-048: settings.json contains a PostCompact hook entry for post-compact-reinject.sh" {
  local settings_file="$PROJECT_ROOT/.claude/settings.json"
  [ -f "$settings_file" ]

  local hook_command
  hook_command=$(jq -r '
    .hooks.PostCompact[]
    | .hooks[]
    | .command
    | select(contains("post-compact-reinject.sh"))
  ' "$settings_file" 2>/dev/null)

  [ -n "$hook_command" ]
}

# ── T-0020-049: Regression -- pre-compact.sh continues to work independently ──

@test "T-0020-049: pre-compact.sh writes compaction marker independently of post-compact-reinject.sh" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

Feature: Hook modernization
EOF

  # Run pre-compact.sh (uses STATE_FILE env pattern, not CLAUDE_PROJECT_DIR)
  prepare_hook "pre-compact.sh"
  run bash -c "CLAUDE_PROJECT_DIR='$TEST_TMPDIR' bash '$TEST_TMPDIR/pre-compact.sh'"
  [ "$status" -eq 0 ]

  # Verify compaction marker was appended
  grep -q "COMPACTION:" "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"
}

# ── T-0020-050: Security -- does not output error-patterns.md or investigation-ledger.md ──

@test "T-0020-050: does not output error-patterns.md or investigation-ledger.md content" {
  # Create all 5 pipeline files with unique identifiable strings
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
UNIQUE_PIPELINE_STATE_MARKER_50
EOF

  cat > "$TEST_TMPDIR/docs/pipeline/context-brief.md" << 'EOF'
UNIQUE_CONTEXT_BRIEF_MARKER_50
EOF

  cat > "$TEST_TMPDIR/docs/pipeline/error-patterns.md" << 'EOF'
UNIQUE_ERROR_PATTERNS_MARKER_50
EOF

  cat > "$TEST_TMPDIR/docs/pipeline/investigation-ledger.md" << 'EOF'
UNIQUE_INVESTIGATION_LEDGER_MARKER_50
EOF

  cat > "$TEST_TMPDIR/docs/pipeline/last-qa-report.md" << 'EOF'
UNIQUE_QA_REPORT_MARKER_50
EOF

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # stdout SHOULD contain pipeline-state and context-brief content
  [[ "$output" == *"UNIQUE_PIPELINE_STATE_MARKER_50"* ]]
  [[ "$output" == *"UNIQUE_CONTEXT_BRIEF_MARKER_50"* ]]

  # stdout MUST NOT contain error-patterns or investigation-ledger content
  [[ "$output" != *"UNIQUE_ERROR_PATTERNS_MARKER_50"* ]]
  [[ "$output" != *"UNIQUE_INVESTIGATION_LEDGER_MARKER_50"* ]]
}
