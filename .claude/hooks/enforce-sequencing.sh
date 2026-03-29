#!/bin/bash
# Phase 2: Pipeline sequencing enforcement
# PreToolUse hook on Agent
#
# Reads docs/pipeline/pipeline-state.md to determine current phase.
# Blocks out-of-order agent invocations. Enforces the mandatory gates
# from Eva's persona (the ones marked "same severity as editing source code").
#
# Only enforces from the main thread (Eva). Subagents spawning other
# subagents is already blocked by disallowedTools: Agent.

set -euo pipefail

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[ "$TOOL_NAME" != "Agent" ] && exit 0

# Only enforce from main thread (Eva orchestrates)
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty')
[ -n "$AGENT_ID" ] && exit 0

SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty')
[ -z "$SUBAGENT_TYPE" ] && exit 0

# Load config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

# Ensure CWD is the project root — hooks may inherit an arbitrary CWD
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
cd "$PROJECT_ROOT"

PIPELINE_DIR=$(jq -r '.pipeline_state_dir' "$CONFIG")
STATE_FILE="$PIPELINE_DIR/pipeline-state.md"

# ─── Snapshot state file to avoid partial-read race ───────────────────
# Eva may be mid-write to pipeline-state.md when this hook fires.
# Copying to a temp file gives a consistent snapshot for parsing.
STATE_SNAPSHOT=$(mktemp)
trap 'rm -f "$STATE_SNAPSHOT"' EXIT
cp "$STATE_FILE" "$STATE_SNAPSHOT" 2>/dev/null || { rm -f "$STATE_SNAPSHOT"; exit 0; }

# ─── Structured state parser ─────────────────────────────────────────
# Reads the machine-readable PIPELINE_STATUS JSON marker from the snapshot.
# Format: <!-- PIPELINE_STATUS: {"roz_qa": "PASS", "phase": "review", "timestamp": "..."} -->
# Returns empty string if marker is absent or JSON is malformed.
parse_pipeline_status() {
  local field="$1"
  local json
  json=$(grep -o 'PIPELINE_STATUS: {[^}]*}' "$STATE_SNAPSHOT" 2>/dev/null | tail -1 | sed 's/PIPELINE_STATUS: //')
  [ -z "$json" ] && return 1
  local value jq_stderr
  jq_stderr=$(mktemp)
  value=$(echo "$json" | jq -r --arg f "$field" '.[$f] // empty' 2>"$jq_stderr")
  if [ -s "$jq_stderr" ]; then
    echo "WARNING: Pipeline state JSON parse error: $(cat "$jq_stderr")" >&2
  fi
  rm -f "$jq_stderr"
  [ -z "$value" ] && return 1
  echo "$value"
}

# ─── Gate 1: Ellis requires Roz QA PASS during active pipelines ─────
# "Ellis commits. Eva does not." + "Roz verifies every Colby output."
# During an active pipeline, Ellis cannot be invoked unless roz_qa is PASS.
# Outside an active pipeline (no state file, no marker, idle/complete phase),
# Ellis is allowed through for infrastructure, doc-only, and setup commits.
if [ "$SUBAGENT_TYPE" = "ellis" ]; then
  # No pipeline-state.md -> no active pipeline -> allow
  if [ ! -f "$STATE_FILE" ]; then
    exit 0
  fi

  # No PIPELINE_STATUS marker -> no active pipeline -> allow
  PHASE=$(parse_pipeline_status "phase") || true
  if [ -z "$PHASE" ]; then
    exit 0
  fi

  # Normalize phase to lowercase for comparison
  PHASE=$(echo "$PHASE" | tr '[:upper:]' '[:lower:]')

  # Inactive phases -> allow (pipeline not running)
  if [ "$PHASE" = "idle" ] || [ "$PHASE" = "complete" ]; then
    exit 0
  fi

  # Micro pipelines skip Roz -- test suite is the safety valve
  SIZING=$(parse_pipeline_status "sizing") || true
  SIZING=$(echo "$SIZING" | tr '[:upper:]' '[:lower:]')
  if [ "$SIZING" = "micro" ]; then
    exit 0
  fi

  # Active phase -> enforce Roz QA PASS
  ROZ_QA=$(parse_pipeline_status "roz_qa") || true
  if [ "$ROZ_QA" != "PASS" ]; then
    echo "BLOCKED: Cannot invoke Ellis — pipeline is active (phase: $PHASE) but no Roz QA PASS found. Roz must verify Colby's output before committing." >&2
    exit 2
  fi
fi

# ─── Gate 2: Agatha after Roz, not during build ─────────────────────
# "Agatha writes docs after final Roz sweep, not during build."
# Uses the structured PIPELINE_STATUS phase field instead of grep.
if [ "$SUBAGENT_TYPE" = "agatha" ]; then
  if [ -f "$STATE_FILE" ]; then
    CURRENT_PHASE=$(parse_pipeline_status "phase") || true
    CURRENT_PHASE=$(echo "$CURRENT_PHASE" | tr '[:upper:]' '[:lower:]')
    if [ "$CURRENT_PHASE" = "build" ] || [ "$CURRENT_PHASE" = "implement" ]; then
      echo "BLOCKED: Cannot invoke Agatha during the build phase. Agatha writes docs after Roz's final sweep against verified code." >&2
      exit 2
    fi
  fi
fi

# ─── Gate 3: No git commands from main thread ────────────────────────
# "Eva never runs git add, git commit, or git push on code changes."
# This gate catches Eva trying to use Bash for git operations instead
# of invoking Ellis. Checked via the Bash hook below, not here.
# (This hook only fires on the Agent tool.)

# ─── Gate 4: Removed ──────────────────────────────────────────────────
# Previously checked if Colby was invoked for "build" without an ADR.
# Removed: keyword matching on prompts was fragile, and ADR file naming
# varies by project. The real enforcement is Gate 1 (Ellis requires Roz
# QA PASS) — if Colby builds something bad, it can't ship without QA.

exit 0
