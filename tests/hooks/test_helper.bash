#!/bin/bash
# Shared test helper for bats hook tests
# Provides setup/teardown, JSON input builders, and jq manipulation helpers.

# Absolute path to the hooks source directory
HOOKS_DIR="$(cd "$(dirname "${BATS_TEST_FILENAME}")"/../../source/hooks && pwd)"

# ── Setup / Teardown ─────────────────────────────────────────────────

setup() {
  # Create a temp directory for each test
  TEST_TMPDIR="$(mktemp -d)"
  export TEST_TMPDIR

  # Create a mock enforcement-config.json in the temp directory
  create_default_config

  # Create a mock pipeline state directory
  mkdir -p "$TEST_TMPDIR/docs/pipeline"
}

teardown() {
  # Clean up temp directory
  if [ -n "$TEST_TMPDIR" ] && [ -d "$TEST_TMPDIR" ]; then
    rm -rf "$TEST_TMPDIR"
  fi

  # Restore PATH if it was modified
  if [ -n "$ORIGINAL_PATH" ]; then
    export PATH="$ORIGINAL_PATH"
    unset ORIGINAL_PATH
  fi
}

# ── Default Config ───────────────────────────────────────────────────

create_default_config() {
  cat > "$TEST_TMPDIR/enforcement-config.json" << 'CFGEOF'
{
  "pipeline_state_dir": "docs/pipeline",
  "architecture_dir": "docs/architecture",
  "product_specs_dir": "docs/product",
  "ux_docs_dir": "docs/ux",
  "colby_blocked_paths": [
    "docs/",
    ".github/",
    ".gitlab-ci",
    ".circleci/",
    "Jenkinsfile",
    "Dockerfile",
    "docker-compose",
    ".gitlab/",
    "deploy/",
    "infra/",
    "terraform/",
    "pulumi/",
    "k8s/",
    "kubernetes/"
  ],
  "test_command": "",
  "test_patterns": [
    ".test.",
    ".spec.",
    "/tests/",
    "/__tests__/",
    "/test_",
    "_test.",
    "conftest"
  ]
}
CFGEOF
}

# ── JSON Input Builders ─────────────────────────────────────────────

# Build a PreToolUse-style JSON input for Write/Edit/MultiEdit hooks
# Usage: build_tool_input "Write" "/path/to/file" "colby"
build_tool_input() {
  local tool_name="${1:-Write}"
  local file_path="${2:-}"
  local agent_type="${3:-}"

  if [ -n "$agent_type" ]; then
    printf '{"tool_name":"%s","tool_input":{"file_path":"%s"},"agent_type":"%s"}' \
      "$tool_name" "$file_path" "$agent_type"
  else
    printf '{"tool_name":"%s","tool_input":{"file_path":"%s"}}' \
      "$tool_name" "$file_path"
  fi
}

# Build a PreToolUse-style JSON input for Agent tool (enforce-sequencing)
# Usage: build_agent_input "ellis" "" (main thread) or build_agent_input "ellis" "sub-123"
build_agent_input() {
  local subagent_type="${1:-}"
  local agent_id="${2:-}"

  if [ -n "$agent_id" ]; then
    printf '{"tool_name":"Agent","tool_input":{"subagent_type":"%s"},"agent_type":"","agent_id":"%s"}' \
      "$subagent_type" "$agent_id"
  else
    printf '{"tool_name":"Agent","tool_input":{"subagent_type":"%s"}}' \
      "$subagent_type"
  fi
}

# Build a Bash tool input for enforce-git
# Usage: build_bash_input "git commit -m test" "" "" (main thread)
#        build_bash_input "git commit -m test" "ellis-123" "ellis" (Ellis subagent)
#        build_bash_input "git commit -m test" "colby-456" "colby" (Colby subagent)
build_bash_input() {
  local command="${1:-}"
  local agent_id="${2:-}"
  local agent_type="${3:-}"

  if [ -n "$agent_id" ] && [ -n "$agent_type" ]; then
    printf '{"tool_name":"Bash","tool_input":{"command":"%s"},"agent_id":"%s","agent_type":"%s"}' \
      "$command" "$agent_id" "$agent_type"
  elif [ -n "$agent_id" ]; then
    printf '{"tool_name":"Bash","tool_input":{"command":"%s"},"agent_id":"%s"}' \
      "$command" "$agent_id"
  else
    printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' \
      "$command"
  fi
}

# Build a SubagentStart-style JSON input for log-agent-start hooks
# Usage: build_subagent_start_input "colby" "agent-abc123" "session-xyz789"
build_subagent_start_input() {
  local agent_type="${1:-}"
  local agent_id="${2:-}"
  local session_id="${3:-}"

  printf '{"agent_type":"%s","agent_id":"%s","session_id":"%s"}' \
    "$agent_type" "$agent_id" "$session_id"
}

# Build a SubagentStop-style JSON input for log-agent-stop / warn-dor-dod hooks
# Usage: build_subagent_stop_input "colby" "agent-abc123" "session-xyz789" "output text"
# Pass "" for last_message to simulate empty output, or omit for null
build_subagent_stop_input() {
  local agent_type="${1:-}"
  local agent_id="${2:-}"
  local session_id="${3:-}"
  local last_message="${4-__UNSET__}"

  if [ "$last_message" = "__UNSET__" ]; then
    # No last_assistant_message key at all
    printf '{"agent_type":"%s","agent_id":"%s","session_id":"%s"}' \
      "$agent_type" "$agent_id" "$session_id"
  elif [ -z "$last_message" ]; then
    # Empty string last_assistant_message
    printf '{"agent_type":"%s","agent_id":"%s","session_id":"%s","last_assistant_message":""}' \
      "$agent_type" "$agent_id" "$session_id"
  else
    # Non-empty last_assistant_message -- escape embedded quotes
    local escaped_message
    escaped_message=$(printf '%s' "$last_message" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')
    printf '{"agent_type":"%s","agent_id":"%s","session_id":"%s","last_assistant_message":"%s"}' \
      "$agent_type" "$agent_id" "$session_id" "$escaped_message"
  fi
}

# Build a SubagentStop-style JSON input with null last_assistant_message
# Usage: build_subagent_stop_input_null "colby" "agent-abc123" "session-xyz789"
build_subagent_stop_input_null() {
  local agent_type="${1:-}"
  local agent_id="${2:-}"
  local session_id="${3:-}"

  printf '{"agent_type":"%s","agent_id":"%s","session_id":"%s","last_assistant_message":null}' \
    "$agent_type" "$agent_id" "$session_id"
}

# Build a StopFailure-style JSON input for log-stop-failure hooks
# Usage: build_stop_failure_input "colby" "rate_limit" "Rate limit exceeded for model"
build_stop_failure_input() {
  local agent_type="${1:-}"
  local error_type="${2:-}"
  local error_message="${3:-}"

  # Escape embedded quotes in error_message
  local escaped_message
  escaped_message=$(printf '%s' "$error_message" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' ' ')
  printf '{"agent_type":"%s","error_type":"%s","error_message":"%s"}' \
    "$agent_type" "$error_type" "$escaped_message"
}

# Build a StopFailure-style JSON input with missing fields
# Usage: build_stop_failure_input_minimal
build_stop_failure_input_minimal() {
  printf '{}'
}

# ── jq Manipulation ─────────────────────────────────────────────────

# Hide jq from PATH so hooks see it as missing.
# Creates a shadow directory that symlinks everything from jq's directory
# EXCEPT jq itself, then replaces that directory in PATH.
hide_jq() {
  export ORIGINAL_PATH="$PATH"
  local jq_path
  jq_path="$(command -v jq 2>/dev/null)" || return 0
  local jq_dir
  jq_dir="$(dirname "$jq_path")"

  # Create shadow directory
  local shadow="$TEST_TMPDIR/shadow_bin"
  mkdir -p "$shadow"

  # Symlink everything in jq's directory except jq
  for f in "$jq_dir"/*; do
    local name
    name="$(basename "$f")"
    [ "$name" = "jq" ] && continue
    ln -sf "$f" "$shadow/$name" 2>/dev/null || true
  done

  # Replace jq's directory with shadow in PATH
  local new_path=""
  local IFS=':'
  for dir in $PATH; do
    if [ "$dir" = "$jq_dir" ]; then
      dir="$shadow"
    fi
    if [ -z "$new_path" ]; then
      new_path="$dir"
    else
      new_path="$new_path:$dir"
    fi
  done
  export PATH="$new_path"
}

# Restore jq to PATH
restore_jq() {
  if [ -n "$ORIGINAL_PATH" ]; then
    export PATH="$ORIGINAL_PATH"
    unset ORIGINAL_PATH
  fi
}

# ── Pipeline State Helpers ───────────────────────────────────────────

# Write a pipeline-state.md with a PIPELINE_STATUS marker
# Usage: write_pipeline_status '{"roz_qa":"PASS","phase":"review"}'
write_pipeline_status() {
  local json="$1"
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << EOF
# Pipeline State

Some content here.

<!-- PIPELINE_STATUS: ${json} -->
EOF
}

# Write pipeline-state.md with free-form text (no structured marker)
# Usage: write_pipeline_freeform "roz passed QA with flying colors"
write_pipeline_freeform() {
  local text="$1"
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << EOF
# Pipeline State

${text}
EOF
}

# Write pipeline-state.md with brain availability info
# Usage: write_brain_state "true"
write_brain_state() {
  local available="$1"
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << EOF
# Pipeline State

brain_available: ${available}

<!-- PIPELINE_STATUS: {"phase":"review","roz_qa":"PASS"} -->
EOF
}

# ── Hook Runners ─────────────────────────────────────────────────────
# These run hooks with the correct SCRIPT_DIR pointing to our temp config.
# The hook's SCRIPT_DIR detection uses `dirname "$0"`, so we copy the hook
# to $TEST_TMPDIR (which already has enforcement-config.json).

# Prepare a hook for execution: copy it to $TEST_TMPDIR.
# Usage: prepare_hook "enforce-paths.sh"
prepare_hook() {
  local hook_name="$1"
  cp "$HOOKS_DIR/$hook_name" "$TEST_TMPDIR/$hook_name"
}

# Run a stdin-based hook with JSON piped in.
# Usage: run_hook_with_input "enforce-paths.sh" "$json_input"
# Must be called inside a bats `run` or used with `run`:
#   run run_hook_with_input "enforce-paths.sh" "$input"
run_hook_with_input() {
  local hook_name="$1"
  local input="$2"
  prepare_hook "$hook_name"
  echo "$input" | bash "$TEST_TMPDIR/$hook_name"
}

# Run a hook with CLAUDE_PROJECT_DIR set to TEST_TMPDIR.
# Usage: run_hook_with_project_dir "log-agent-start.sh" "$json_input"
# Used for hooks that reference $CLAUDE_PROJECT_DIR instead of SCRIPT_DIR.
run_hook_with_project_dir() {
  local hook_name="$1"
  local input="$2"
  prepare_hook "$hook_name"
  echo "$input" | CLAUDE_PROJECT_DIR="$TEST_TMPDIR" bash "$TEST_TMPDIR/$hook_name"
}

# Run a hook with CLAUDE_PROJECT_DIR unset.
# Usage: run_hook_without_project_dir "log-agent-start.sh" "$json_input"
run_hook_without_project_dir() {
  local hook_name="$1"
  local input="$2"
  prepare_hook "$hook_name"
  echo "$input" | env -u CLAUDE_PROJECT_DIR -u CURSOR_PROJECT_DIR bash "$TEST_TMPDIR/$hook_name"
}
