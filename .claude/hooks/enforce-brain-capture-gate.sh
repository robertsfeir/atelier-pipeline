#!/bin/bash
# enforce-brain-capture-gate.sh -- PreToolUse hook on Agent (ADR-0053).
#
# Blocks main-thread Agent invocations when a brain capture is pending --
# i.e., the previous allowlisted agent stopped (via
# enforce-brain-capture-pending.sh) and Eva has not yet called
# agent_capture to flush the pending marker
# (clear-brain-capture-pending.sh deletes it on a successful capture).
#
# Pattern mirrors enforce-scout-swarm.sh:
#   - main-thread guard: agent_id must be empty (subagents pass through)
#   - fail-open on missing config / ATELIER_SETUP_MODE / setup-mode sentinel
#   - exit 2 with a stderr BLOCKED message on violation
#
# Sentinel escape hatch: if {pipeline_state_dir}/.brain-unavailable exists,
# the gate suppresses the block (atelier_stats unreachable; documented Eva
# protocol).

set -euo pipefail

[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
[ -f "${PROJECT_ROOT}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)

# jq missing -> fail-open with a clear error (matches enforce-scout-swarm.sh).
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[ "$TOOL_NAME" != "Agent" ] && exit 0

# Only enforce from the main thread (Eva). Subagents have agent_id set.
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty')
[ -n "$AGENT_ID" ] && exit 0

# Load config for pipeline_state_dir. Fail-open on missing config.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/enforcement-config.json"
[ ! -f "$CONFIG" ] && exit 0

PIPELINE_DIR=$(jq -r '.pipeline_state_dir // "docs/pipeline"' "$CONFIG" 2>/dev/null || echo "docs/pipeline")
case "$PIPELINE_DIR" in
  /*) ;;
  *) PIPELINE_DIR="${PROJECT_ROOT}/${PIPELINE_DIR}" ;;
esac

PENDING_FILE="${PIPELINE_DIR}/.pending-brain-capture.json"
SENTINEL_FILE="${PIPELINE_DIR}/.brain-unavailable"
NOT_INSTALLED_FILE="${PIPELINE_DIR}/.brain-not-installed"

# No pending capture -> nothing to gate.
[ ! -f "$PENDING_FILE" ] && exit 0

# Brain-unavailable sentinel honored: documented escape hatch when
# atelier_stats reports the brain unreachable.
[ -f "$SENTINEL_FILE" ] && exit 0

# Brain-not-installed sentinel honored (ADR-0055): pipeline runs with no
# brain plugin installed at all. Pass through so the pipeline does not
# deadlock on a capture that no tool can satisfy.
[ -f "$NOT_INSTALLED_FILE" ] && exit 0

# Best-effort: surface which agent's output is pending capture.
PENDING_AGENT=$(jq -r '.agent_type // "unknown"' "$PENDING_FILE" 2>/dev/null || echo "unknown")

cat >&2 <<EOF
BLOCKED: brain capture pending for previous agent (${PENDING_AGENT}).
Call agent_capture (via your brain plugin) with a curated thought
(decision/pattern/lesson, 1-3 sentences) before spawning the next agent.
The pending marker at ${PENDING_FILE} clears automatically on a
successful capture.

If the brain is genuinely unreachable, follow the Eva-only escape-hatch
protocol in pipeline-orchestration.md (touch ${SENTINEL_FILE}; clear on
next successful atelier_stats ping). If no brain plugin is installed at
all, touch ${NOT_INSTALLED_FILE} to suppress the gate permanently for
this project.
EOF
exit 2
