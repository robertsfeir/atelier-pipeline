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

# ─── Gate 1: Ellis requires Roz QA PASS ─────────────────────────────
# "Ellis commits. Eva does not." + "Roz verifies every Colby output."
# Ellis cannot be invoked unless pipeline-state.md contains a structured
# PIPELINE_STATUS marker with roz_qa set to exactly "PASS".
if [ "$SUBAGENT_TYPE" = "ellis" ]; then
  if [ ! -f "$STATE_FILE" ]; then
    echo "BLOCKED: Cannot invoke Ellis — no pipeline-state.md found. Roz must pass QA first." >&2
    exit 2
  fi
  ROZ_QA=$(parse_pipeline_status "roz_qa") || true
  if [ "$ROZ_QA" != "PASS" ]; then
    echo "BLOCKED: Cannot invoke Ellis — no Roz QA PASS found in pipeline-state.md. Roz must verify Colby's output before committing." >&2
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
