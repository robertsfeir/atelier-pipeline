#!/bin/bash
# enforce-brain-capture-pending.sh -- SubagentStop hook (ADR-0053).
#
# Co-fires with log-agent-stop.sh on every SubagentStop. When the stopping
# agent is in the brain-grade allowlist, writes a pending-capture marker at
# {pipeline_state_dir}/.pending-brain-capture.json so the PreToolUse gate
# (enforce-brain-capture-gate.sh) can block Eva's next Agent invocation
# until she calls agent_capture (cleared by clear-brain-capture-pending.sh).
#
# Allowlist (mirrors the original brain-extractor `if:` clause):
#   sarah, colby, agatha, robert, robert-spec, sable, sable-ux, ellis
# Excluded (verification/investigation/scout output is logged elsewhere or
# is ephemeral): poirot, sherlock, sentinel, scout, distillator,
# brain-extractor, discovered agents, unknown.
#
# Contract: SubagentStop hooks must NEVER exit 2 -- this script exits 0
# always. Failure to write the pending file is logged to stderr but never
# blocks the agent stop.

# Do NOT use set -e -- we want to continue past write failures.
set -uo pipefail

[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0

PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
[ -f "${PROJECT_ROOT}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)

# jq missing -> fail open silently (do not block the stop).
if ! command -v jq &>/dev/null; then
  exit 0
fi

# Source shared hook library for hook_lib_get_agent_type.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/hook-lib.sh" ]; then
  source "$SCRIPT_DIR/hook-lib.sh" 2>/dev/null || true
fi

# Extract agent_type. Use hook-lib if available, otherwise fall back to the
# same composite jq expression hook_lib_get_agent_type uses.
if declare -f hook_lib_get_agent_type >/dev/null 2>&1; then
  AGENT_TYPE=$(echo "$INPUT" | hook_lib_get_agent_type 2>/dev/null || true)
else
  AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // empty' 2>/dev/null || true)
fi

# Allowlist gate. Anything outside the 8 brain-grade producers exits silently.
case "$AGENT_TYPE" in
  sarah|colby|agatha|robert|robert-spec|sable|sable-ux|ellis) ;;
  *) exit 0 ;;
esac

# Resolve pipeline_state_dir from enforcement-config.json. Fail-open on a
# missing config -- this hook must never block the stop.
CONFIG="$SCRIPT_DIR/enforcement-config.json"
if [ -f "$CONFIG" ]; then
  PIPELINE_DIR=$(jq -r '.pipeline_state_dir // "docs/pipeline"' "$CONFIG" 2>/dev/null || echo "docs/pipeline")
else
  PIPELINE_DIR="docs/pipeline"
fi

# Make pipeline_state_dir an absolute path under PROJECT_ROOT when relative.
case "$PIPELINE_DIR" in
  /*) ;;
  *) PIPELINE_DIR="${PROJECT_ROOT}/${PIPELINE_DIR}" ;;
esac

mkdir -p "$PIPELINE_DIR" 2>/dev/null || {
  echo "WARNING: enforce-brain-capture-pending.sh: cannot create $PIPELINE_DIR" >&2
  exit 0
}

# Short-circuit when either sentinel is present (ADR-0055 + ADR-0053):
#   .brain-unavailable    -> brain installed but unreachable (Eva escape hatch).
#   .brain-not-installed  -> no brain plugin installed at all.
# Writing a pending file in either case would deadlock the gate, since no
# agent_capture call can reach a brain that does not exist or is down.
if [ -f "${PIPELINE_DIR}/.brain-unavailable" ] || [ -f "${PIPELINE_DIR}/.brain-not-installed" ]; then
  exit 0
fi

PENDING_FILE="${PIPELINE_DIR}/.pending-brain-capture.json"

# Pull transcript_path (best-effort; SubagentStop payload includes it on
# Claude Code, may be absent on Cursor). Empty string is fine.
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null || true)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Write the pending-capture marker. Use jq to compose to guarantee valid
# JSON regardless of escapes in transcript_path.
jq -n \
  --arg agent_type "$AGENT_TYPE" \
  --arg transcript_path "$TRANSCRIPT_PATH" \
  --arg timestamp "$TIMESTAMP" \
  '{agent_type: $agent_type, transcript_path: $transcript_path, timestamp: $timestamp}' \
  > "$PENDING_FILE" 2>/dev/null || {
    echo "WARNING: enforce-brain-capture-pending.sh: failed to write $PENDING_FILE" >&2
  }

exit 0
