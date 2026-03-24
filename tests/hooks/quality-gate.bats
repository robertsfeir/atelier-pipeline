#!/usr/bin/env bats
# Tests for quality-gate.sh (Stop hook)
# Covers: T-0003-001, T-0003-003 through T-0003-009

load test_helper

# ── T-0003-001: Security -- no eval() in the file ────────────────────

@test "T-0003-001: quality-gate.sh contains no eval() calls" {
  run grep -n 'eval ' "$HOOKS_DIR/quality-gate.sh"
  [ "$status" -ne 0 ]
}

# ── T-0003-003: Happy -- runs test command and exits 0 ──────────────

@test "T-0003-003: with test command set and source changes, runs tests and exits 0" {
  # Set up a git repo with source changes
  cd "$TEST_TMPDIR"
  git init -q
  git config user.email "test@test.com"
  git config user.name "Test"
  echo "baseline" > src_file.js
  git add src_file.js
  git commit -q -m "init"
  # Create a source change (modified tracked file)
  echo "changed" > src_file.js

  # Configure a test command that succeeds
  cat > "$TEST_TMPDIR/enforcement-config.json" << 'EOF'
{
  "test_command": "true"
}
EOF

  prepare_hook "quality-gate.sh"
  run bash "$TEST_TMPDIR/quality-gate.sh"
  [ "$status" -eq 0 ]
}

# ── T-0003-004: Happy -- no source changes, exits 0 ─────────────────

@test "T-0003-004: with no source changes, exits 0 without running tests" {
  cd "$TEST_TMPDIR"
  git init -q
  git config user.email "test@test.com"
  git config user.name "Test"
  # Create initial file and commit -- repo is clean after this
  echo "baseline" > src_file.js
  git add src_file.js
  git commit -q -m "init"
  # Add the enforcement config (untracked, but excluded by .md/.json patterns)
  # Actually, the hook checks for source changes excluding docs/, .claude/, root *.md
  # enforcement-config.json is at root, so it would match as an untracked file
  # unless we add it to .gitignore or commit it
  git add enforcement-config.json
  git commit -q -m "add config"

  # Configure a test command that would fail if run
  cat > "$TEST_TMPDIR/enforcement-config.json" << 'EOF'
{
  "test_command": "exit 1"
}
EOF
  # Stage the config change so it's not untracked
  git add enforcement-config.json

  # The only changes are enforcement-config.json (a .json file) -- but wait,
  # quality-gate only excludes docs/, .claude/, and root *.md. JSON files are not excluded.
  # So we need a truly clean repo. Commit everything.
  git commit -q -m "config update"

  prepare_hook "quality-gate.sh"
  # The hook also checks for quality-gate.sh itself as an untracked file
  # Add it to .gitignore
  echo "quality-gate.sh" > .gitignore
  git add .gitignore
  git commit -q -m "gitignore"

  run bash "$TEST_TMPDIR/quality-gate.sh"
  [ "$status" -eq 0 ]
}

# ── T-0003-005: Failure -- jq missing, exits 2 ──────────────────────

@test "T-0003-005: with jq missing, exits 2 with error message containing jq" {
  hide_jq
  unset ATELIER_STOP_HOOK_ACTIVE
  prepare_hook "quality-gate.sh"
  run bash "$TEST_TMPDIR/quality-gate.sh"
  [ "$status" -eq 2 ]
  [[ "$output" == *"jq"* ]]
}

# ── T-0003-006: Failure -- test command fails, exits 2 ──────────────

@test "T-0003-006: test command fails, exits 2 with BLOCKED message" {
  cd "$TEST_TMPDIR"
  git init -q
  git config user.email "test@test.com"
  git config user.name "Test"
  echo "baseline" > src_file.js
  git add src_file.js
  git commit -q -m "init"
  echo "changed" > src_file.js

  cat > "$TEST_TMPDIR/enforcement-config.json" << 'EOF'
{
  "test_command": "exit 1"
}
EOF

  prepare_hook "quality-gate.sh"
  run bash "$TEST_TMPDIR/quality-gate.sh"
  [ "$status" -eq 2 ]
  [[ "$output" == *"BLOCKED"* ]]
}

# ── T-0003-007: Boundary -- loop guard exits 0 ──────────────────────

@test "T-0003-007: ATELIER_STOP_HOOK_ACTIVE=1 exits 0 immediately" {
  export ATELIER_STOP_HOOK_ACTIVE=1
  prepare_hook "quality-gate.sh"
  run bash "$TEST_TMPDIR/quality-gate.sh"
  [ "$status" -eq 0 ]
  unset ATELIER_STOP_HOOK_ACTIVE
}

# ── T-0003-008: Boundary -- empty TEST_COMMAND exits 0 ──────────────

@test "T-0003-008: TEST_COMMAND is empty string, exits 0" {
  cd "$TEST_TMPDIR"
  git init -q
  git config user.email "test@test.com"
  git config user.name "Test"
  echo "x" > src_file.js
  git add src_file.js
  git commit -q -m "init"
  echo "y" > src_file.js

  cat > "$TEST_TMPDIR/enforcement-config.json" << 'EOF'
{
  "test_command": ""
}
EOF

  prepare_hook "quality-gate.sh"
  run bash "$TEST_TMPDIR/quality-gate.sh"
  [ "$status" -eq 0 ]
}

# ── T-0003-009: Boundary -- placeholder "echo skip" exits 0 ─────────

@test "T-0003-009: TEST_COMMAND is 'echo skip', exits 0 (placeholder skip)" {
  cd "$TEST_TMPDIR"
  git init -q
  git config user.email "test@test.com"
  git config user.name "Test"
  echo "x" > src_file.js
  git add src_file.js
  git commit -q -m "init"
  echo "y" > src_file.js

  cat > "$TEST_TMPDIR/enforcement-config.json" << 'EOF'
{
  "test_command": "echo skip"
}
EOF

  prepare_hook "quality-gate.sh"
  run bash "$TEST_TMPDIR/quality-gate.sh"
  [ "$status" -eq 0 ]
}
