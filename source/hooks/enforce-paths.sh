#!/bin/bash
# Phase 1: File path enforcement per agent
# PreToolUse hook on Write|Edit|MultiEdit
#
# Checks agent_type (from subagent frontmatter name) and file_path
# against allowed paths per agent. Blocks violations with exit code 2.
#
# Main thread (no agent_id): Eva + Robert-skill + Sable-skill
# Subagents: identified by agent_type matching frontmatter name

set -euo pipefail

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty')

# Only check Write/Edit/MultiEdit
case "$TOOL_NAME" in
  Write|Edit|MultiEdit) ;;
  *) exit 0 ;;
esac

# Need a file path to check
[ -z "$FILE_PATH" ] && exit 0

# Load config — allow if config missing (not yet set up)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

# Ensure CWD is the project root — hooks may inherit an arbitrary CWD
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
cd "$PROJECT_ROOT"

# Normalize absolute paths to project-relative
FILE_PATH="${FILE_PATH#"$PWD"/}"

# If path is still absolute after normalization, it's outside the project root
# Only ellis (full access) is allowed to write outside the project
if [[ "$FILE_PATH" == /* ]] && [ "$AGENT_TYPE" != "ellis" ]; then
  echo "BLOCKED: File is outside the project root. Attempted: $FILE_PATH" >&2
  exit 2
fi

PIPELINE_DIR=$(jq -r '.pipeline_state_dir' "$CONFIG")
ARCH_DIR=$(jq -r '.architecture_dir' "$CONFIG")
PRODUCT_DIR=$(jq -r '.product_specs_dir' "$CONFIG")
UX_DIR=$(jq -r '.ux_docs_dir' "$CONFIG")

# Check if file path matches any of the given prefixes
path_matches() {
  local file="$1"
  shift
  for prefix in "$@"; do
    case "$file" in
      "$prefix"*) return 0 ;;
    esac
  done
  return 1
}

# Check if file matches test patterns from config.
# Patterns are matched as substrings. For patterns starting with /
# (e.g., /tests/), we also check if the path starts with the pattern
# sans the leading slash (e.g., tests/) to catch root-level test dirs.
is_test_file() {
  local file="$1"
  while IFS= read -r pattern; do
    case "$file" in
      *"$pattern"*) return 0 ;;
    esac
    # Handle root-level paths: /tests/ should also match tests/ at path start
    if [[ "$pattern" == /* ]]; then
      local stripped="${pattern#/}"
      case "$file" in
        "$stripped"*) return 0 ;;
      esac
    fi
  done < <(jq -r '.test_patterns[]' "$CONFIG" 2>/dev/null)
  return 1
}

# Check if file is in a colby_blocked_paths prefix
is_colby_blocked() {
  local file="$1"
  while IFS= read -r prefix; do
    case "$file" in
      "$prefix"*) return 0 ;;
    esac
  done < <(jq -r '.colby_blocked_paths[]' "$CONFIG" 2>/dev/null)
  return 1
}

case "$AGENT_TYPE" in
  cal)
    path_matches "$FILE_PATH" "$ARCH_DIR" || {
      echo "BLOCKED: Cal can only write to $ARCH_DIR/. Route documentation to Agatha, source code to Colby. Attempted: $FILE_PATH" >&2
      exit 2
    }
    ;;

  colby)
    # Colby can write to most paths but is blocked from docs, CI/CD config,
    # and infrastructure files (colby_blocked_paths in config)
    if is_colby_blocked "$FILE_PATH"; then
      echo "BLOCKED: Colby cannot write to blocked path. Route documentation to Agatha, infrastructure to DevOps. Attempted: $FILE_PATH" >&2
      exit 2
    fi
    ;;

  roz)
    # Roz can only write test files (matching test_patterns) and docs/pipeline
    if path_matches "$FILE_PATH" "$PIPELINE_DIR"; then
      exit 0
    fi
    if is_test_file "$FILE_PATH"; then
      exit 0
    fi
    echo "BLOCKED: Roz can only write test files and $PIPELINE_DIR/. Attempted: $FILE_PATH" >&2
    exit 2
    ;;

  ellis)
    # Ellis has full write access — commit agent stages and commits all files
    exit 0
    ;;

  agatha)
    path_matches "$FILE_PATH" "docs/" || {
      echo "BLOCKED: Agatha can only write to docs/. Source code and config changes go to Colby. Attempted: $FILE_PATH" >&2
      exit 2
    }
    ;;

  "")
    # Main thread: Eva + Robert-skill + Sable-skill share this context
    # Eva: docs/pipeline/*   Robert-skill: docs/product/*   Sable-skill: docs/ux/*
    path_matches "$FILE_PATH" "$PIPELINE_DIR" "$PRODUCT_DIR" "$UX_DIR" || {
      echo "BLOCKED: Main thread (Eva/Robert/Sable) can only write to $PIPELINE_DIR/, $PRODUCT_DIR/, or $UX_DIR/. Route source code changes to Colby, architecture to Cal, documentation to Agatha. Attempted: $FILE_PATH" >&2
      exit 2
    }
    ;;

  *)
    # Unknown or read-only agents (sable subagent, robert subagent,
    # investigator, distillator) — their disallowedTools should already
    # block Write/Edit, but enforce here as safety net
    echo "BLOCKED: Agent '$AGENT_TYPE' does not have write access. Attempted: $FILE_PATH" >&2
    exit 2
    ;;
esac

exit 0
