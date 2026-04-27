#!/bin/bash
# enforce-scout-swarm.sh -- PreToolUse hook on Agent
#
# Sizing-gated. Only enforces on Medium/Large pipelines. Micro/Small skip
# entirely — their ceremony cost exceeds the value of pre-collected scout
# evidence.
#
# When enforcing: blocks invocations of sarah or colby when the required
# scout evidence block is absent from the prompt.
#
# Required blocks per agent:
#   sarah  → <research-brief>
#   colby  → <colby-context>
#
# Setup mode, agent_id (non-main-thread), or missing pipeline-state.md —
# fail-open.

set -euo pipefail
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
[ -f "${CLAUDE_PROJECT_DIR:-.}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[ "$TOOL_NAME" != "Agent" ] && exit 0

# Only enforce from the main thread (Eva). Subagents have agent_id set.
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty')
[ -n "$AGENT_ID" ] && exit 0

SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty')

# ─── scout file-dump format contract ────────────────────────────────────
# Applies regardless of pipeline sizing. A scout that has a <read>
# block (file-reading scout) MUST include the '=== FILE:' delimiter format
# contract in its prompt so the downstream Sonnet extractor can parse output.
# Search/question scouts (no <read> block) are allowed through.
if [ "$SUBAGENT_TYPE" = "scout" ]; then
  PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty')
  if [ -n "$PROMPT" ]; then
    if echo "$PROMPT" | grep -qE '^[[:space:]]*<read[>[:space:]]'; then
      if ! echo "$PROMPT" | sed -n '/<output>/,/<\/output>/p' | grep -qF '=== FILE:'; then
        echo "BLOCKED: scout file-reading subagent missing output format contract. Add <output> block with '=== FILE: {path} ===' delimiter to the scout prompt (see skills/brain-hydrate/SKILL.md §Scout Invocation Template)." >&2
        exit 2
      fi
      # Post-pass guard: {FILES} placeholder was never substituted by Eva.
      if echo "$PROMPT" | grep -qF '{FILES}'; then
        echo "BLOCKED: scout prompt contains unsubstituted {FILES} placeholder. Eva must replace {FILES} with the actual file paths from Phase 1 inventory before invoking the scout." >&2
        exit 2
      fi
    fi
  fi
  exit 0
fi

# Only enforce for sarah and colby. Poirot is gone (v4.0); other agents have
# no scout evidence contract.
case "$SUBAGENT_TYPE" in
  sarah|colby) ;;
  *) exit 0 ;;
esac

# Load config for pipeline_state_dir
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
cd "$PROJECT_ROOT"

# Source shared hook library
if [ -f "$SCRIPT_DIR/hook-lib.sh" ]; then
  source "$SCRIPT_DIR/hook-lib.sh" 2>/dev/null || true
fi

PIPELINE_DIR=$(jq -r '.pipeline_state_dir' "$CONFIG")
STATE_FILE="$PIPELINE_DIR/pipeline-state.md"

# ─── Parse PIPELINE_STATUS for sizing gate ─────────────────────────────
# Fail-open: if state file is missing/unreadable, we cannot confirm an
# active pipeline — allow through.
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

STATE_SNAPSHOT=$(mktemp)
trap 'rm -f "$STATE_SNAPSHOT"' EXIT
cp "$STATE_FILE" "$STATE_SNAPSHOT" 2>/dev/null || { rm -f "$STATE_SNAPSHOT"; exit 0; }

SIZING=$(cat "$STATE_SNAPSHOT" | hook_lib_pipeline_status_field sizing 2>/dev/null | tr '[:upper:]' '[:lower:]') || true

# ─── v4.0 SIZING GATE ───────────────────────────────────────────────────
# Scouts are only valuable on Medium/Large pipelines. Micro/Small skip the
# hook entirely regardless of agent.
case "$SIZING" in
  micro|small|"")
    # Empty sizing → unknown pipeline stage → fail-open (no scout requirement).
    # Micro/Small → explicit skip.
    exit 0
    ;;
  medium|large)
    : # continue to block check
    ;;
  *)
    # Unknown sizing value → fail-open.
    exit 0
    ;;
esac

# ─── Check for required evidence block in prompt ─────────────────────────
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty')

# Empty prompt — fail-open (no block to check)
[ -z "$PROMPT" ] && exit 0

check_block_present() {
  local tag="$1"
  echo "$PROMPT" | grep -qF "<${tag}" 2>/dev/null
}

# Check that a block both exists and has sufficient content (>= 50 chars).
check_block_content() {
  local tag="$1"
  local min_len=50
  local sentinel_start="__BLOCK_START__"
  local sentinel_end="__BLOCK_END__"

  if ! check_block_present "$tag"; then
    return 1
  fi

  local one_line result content
  one_line=$(echo "$PROMPT" | tr '\n' '\001') || true

  result=$(echo "$one_line" | sed -n "s/.*<${tag}[^>]*>\(.*\)<\/${tag}>.*/${sentinel_start}\1${sentinel_end}/p" | tr '\001' '\n') || true

  if [[ "$result" != "${sentinel_start}"*"${sentinel_end}" ]]; then
    return 0
  fi

  content="${result#"${sentinel_start}"}"
  content="${content%"${sentinel_end}"}"

  local trimmed
  trimmed=$(echo "$content" | tr -d '[:space:]') || true

  [ -z "$trimmed" ] && return 1

  local len
  len=${#content}
  [ "$len" -lt "$min_len" ] && return 1

  return 0
}

case "$SUBAGENT_TYPE" in
  sarah)
    if ! check_block_present "research-brief"; then
      echo "BLOCKED: Cannot invoke Sarah on Medium/Large without a <research-brief> block. Run scout fan-out first to populate research evidence (pipeline-orchestration.md §Scout Fan-out Protocol)." >&2
      exit 2
    fi
    if ! check_block_content "research-brief"; then
      echo "BLOCKED: <research-brief> block is empty or too short (< 50 chars). Run the scout fan-out to generate real search results before invoking Sarah." >&2
      exit 2
    fi
    ;;
  colby)
    if ! check_block_present "colby-context"; then
      echo "BLOCKED: Cannot invoke Colby on Medium/Large without a <colby-context> block. Run scout fan-out first to populate implementation context (pipeline-orchestration.md §Scout Fan-out Protocol)." >&2
      exit 2
    fi
    if ! check_block_content "colby-context"; then
      echo "BLOCKED: <colby-context> block is empty or too short (< 50 chars). Run the scout fan-out to generate real search results before invoking Colby." >&2
      exit 2
    fi
    ;;
esac

exit 0
