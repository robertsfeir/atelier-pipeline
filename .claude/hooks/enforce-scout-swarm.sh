#!/bin/bash
# enforce-scout-swarm.sh -- PreToolUse hook on Agent tool
#
# Blocks invocations of cal, roz, and colby when the required scout evidence
# block is absent from the prompt. The scout fan-out protocol (pipeline-orchestration.md
# §Scout Fan-out Protocol) requires Eva to populate a named block before invoking
# any primary agent. This hook makes that behavioral requirement mechanical.
#
# Required blocks per agent:
#   cal    → <research-brief>
#   roz    → <debug-evidence> OR <qa-evidence>
#   colby  → <colby-context>
#
# Skip conditions (read from PIPELINE_STATUS in pipeline-state.md):
#   sizing=micro           → skip colby enforcement
#   sizing=small           → skip cal enforcement
#   scoped_rerun=true      → skip roz enforcement
#
# Fail-open: if pipeline-state.md is unreadable, all agents are allowed through.
# Only fires from the main thread (Eva). Subagent-spawned agents already blocked
# by disallowedTools: Agent in persona files.

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

# Only enforce for the three primary production agents
case "$SUBAGENT_TYPE" in
  cal|roz|colby) ;;
  *) exit 0 ;;
esac

# Load config for pipeline_state_dir
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
cd "$PROJECT_ROOT"

PIPELINE_DIR=$(jq -r '.pipeline_state_dir' "$CONFIG")
STATE_FILE="$PIPELINE_DIR/pipeline-state.md"

# ─── Parse PIPELINE_STATUS for skip conditions ─────────────────────────
# Fail-open: if state file is missing or unreadable, allow through.
# Scout evidence is only meaningful during an active pipeline. Without a
# state file, we cannot determine if a pipeline is active — allow through.
SIZING=""
SCOPED_RERUN=""
STATE_READABLE=false

if [ -f "$STATE_FILE" ]; then
  STATE_SNAPSHOT=$(mktemp)
  trap 'rm -f "$STATE_SNAPSHOT"' EXIT
  cp "$STATE_FILE" "$STATE_SNAPSHOT" 2>/dev/null || { rm -f "$STATE_SNAPSHOT"; exit 0; }
  STATE_READABLE=true

  JSON=$(grep -o 'PIPELINE_STATUS: {[^}]*}' "$STATE_SNAPSHOT" 2>/dev/null | tail -1 | sed 's/PIPELINE_STATUS: //') || true
  if [ -n "$JSON" ]; then
    JQERR=$(mktemp)
    SIZING=$(echo "$JSON" | jq -r '.sizing // empty' 2>"$JQERR" | tr '[:upper:]' '[:lower:]') || true
    SCOPED_RERUN=$(echo "$JSON" | jq -r '.scoped_rerun // empty' 2>>"$JQERR" | tr '[:upper:]' '[:lower:]') || true
    [ -s "$JQERR" ] && echo "WARNING: Pipeline state JSON parse error: $(cat "$JQERR")" >&2
    rm -f "$JQERR"
  fi
fi

# If pipeline-state.md is missing/unreadable, we cannot confirm an active pipeline.
# Allow through — enforcement is only meaningful when a pipeline is running.
[ "$STATE_READABLE" = "false" ] && exit 0

# ─── Apply skip conditions before block check ───────────────────────────
# micro pipeline  → skip colby enforcement
if [ "$SUBAGENT_TYPE" = "colby" ] && [ "$SIZING" = "micro" ]; then
  exit 0
fi

# small pipeline  → skip cal enforcement
if [ "$SUBAGENT_TYPE" = "cal" ] && [ "$SIZING" = "small" ]; then
  exit 0
fi

# scoped-rerun mode → skip roz enforcement
if [ "$SUBAGENT_TYPE" = "roz" ] && [ "$SCOPED_RERUN" = "true" ]; then
  exit 0
fi

# ─── Check for required evidence block in prompt ─────────────────────────
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty')

# Empty prompt — fail-open (no block to check)
[ -z "$PROMPT" ] && exit 0

check_block_present() {
  local tag="$1"
  # Match opening tag (self-closing or with attributes)
  echo "$PROMPT" | grep -qF "<${tag}" 2>/dev/null
}

# Check that a block both exists and has sufficient content (>= 50 chars).
# Strategy: collapse the prompt to a single line so sed can match across
# newlines, wrap the capture in sentinels to distinguish "matched empty" from
# "no match", then measure content length. Fails-open if no match (closing tag
# absent or structure ambiguous). Blocks empty/whitespace-only blocks and
# blocks with extracted content under 50 chars.
# Returns 0 if block has sufficient content or extraction is ambiguous, 1 if too short.
check_block_content() {
  local tag="$1"
  local min_len=50
  local sentinel_start="__BLOCK_START__"
  local sentinel_end="__BLOCK_END__"

  # Block must be present at all (opening tag check)
  if ! check_block_present "$tag"; then
    return 1
  fi

  # Collapse to one line so sed can match across newlines.
  local one_line result content
  one_line=$(echo "$PROMPT" | tr '\n' '\001') || true

  # Wrap captured content in sentinels so we can distinguish empty-match from no-match.
  result=$(echo "$one_line" | sed -n "s/.*<${tag}[^>]*>\(.*\)<\/${tag}>.*/${sentinel_start}\1${sentinel_end}/p" | tr '\001' '\n') || true

  # No match → closing tag absent or structure ambiguous — fail-open.
  if [[ "$result" != "${sentinel_start}"*"${sentinel_end}" ]]; then
    return 0
  fi

  # Strip sentinels to get raw content.
  content="${result#"${sentinel_start}"}"
  content="${content%"${sentinel_end}"}"

  # Strip whitespace to check for an effectively-empty block.
  local trimmed
  trimmed=$(echo "$content" | tr -d '[:space:]') || true

  # Empty or whitespace-only block → block it (0 chars is < 50).
  [ -z "$trimmed" ] && return 1

  # Measure actual content length. Under 50 chars → block.
  local len
  len=${#content}
  [ "$len" -lt "$min_len" ] && return 1

  return 0
}

case "$SUBAGENT_TYPE" in
  cal)
    if ! check_block_present "research-brief"; then
      echo "BLOCKED: Cannot invoke Cal without a <research-brief> block. Run scout fan-out first to populate research evidence (pipeline-orchestration.md §Scout Fan-out Protocol)." >&2
      exit 2
    fi
    if ! check_block_content "research-brief"; then
      echo "BLOCKED: <research-brief> block is empty or too short (< 50 chars). Run the scout fan-out to generate real search results before invoking Cal." >&2
      exit 2
    fi
    ;;
  roz)
    if ! check_block_present "debug-evidence" && ! check_block_present "qa-evidence"; then
      echo "BLOCKED: Cannot invoke Roz without a <debug-evidence> or <qa-evidence> block. Run scout fan-out first to populate QA evidence (pipeline-orchestration.md §Scout Fan-out Protocol)." >&2
      exit 2
    fi
    # At least one block must have >= 50 chars of content.
    debug_ok=false
    qa_ok=false
    check_block_content "debug-evidence" && debug_ok=true || true
    check_block_content "qa-evidence" && qa_ok=true || true
    if [ "$debug_ok" = "false" ] && [ "$qa_ok" = "false" ]; then
      echo "BLOCKED: <debug-evidence> and <qa-evidence> blocks are empty or too short (< 50 chars). Run the scout fan-out to generate real search results before invoking Roz." >&2
      exit 2
    fi
    ;;
  colby)
    if ! check_block_present "colby-context"; then
      echo "BLOCKED: Cannot invoke Colby without a <colby-context> block. Run scout fan-out first to populate implementation context (pipeline-orchestration.md §Scout Fan-out Protocol)." >&2
      exit 2
    fi
    if ! check_block_content "colby-context"; then
      echo "BLOCKED: <colby-context> block is empty or too short (< 50 chars). Run the scout fan-out to generate real search results before invoking Colby." >&2
      exit 2
    fi
    ;;
esac

exit 0
