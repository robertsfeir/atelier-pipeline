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

# Require jq — degrade gracefully if missing
if ! command -v jq &>/dev/null; then
  exit 0
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
      *"$prefix"*) return 0 ;;
    esac
  done
  return 1
}

# Check if file matches test patterns from config
is_test_file() {
  local file="$1"
  local patterns
  patterns=$(jq -r '.test_patterns[]' "$CONFIG" 2>/dev/null)
  for pattern in $patterns; do
    case "$file" in
      *"$pattern"*) return 0 ;;
    esac
  done
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
    path_matches "$FILE_PATH" "docs/" && {
      echo "BLOCKED: Colby cannot write to docs/. Route documentation changes to Agatha. Attempted: $FILE_PATH" >&2
      exit 2
    }
    ;;

  roz)
    if ! is_test_file "$FILE_PATH" && ! path_matches "$FILE_PATH" "$PIPELINE_DIR/last-qa-report"; then
      echo "BLOCKED: Roz can only write test files and docs/pipeline/last-qa-report.md. Production code is read-only. Attempted: $FILE_PATH" >&2
      exit 2
    fi
    ;;

  ellis)
    # Ellis has full write access — commit agent stages and commits all files
    exit 0
    ;;

  documentation-expert|agatha)
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
