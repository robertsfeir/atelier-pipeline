#!/bin/bash
# SubagentStop verification hook -- typecheck + auto-format after Colby stops (ADR-0050).
#
# Gates internally on agent_type == "colby"; exits 0 immediately for any other agent.
# Loads verify_commands.format and verify_commands.typecheck from pipeline-config.json
# (precedence: .cursor/pipeline-config.json then .claude/pipeline-config.json).
#
# Behavior on a Colby stop:
#   1. Per-session FAILURE counter at docs/pipeline/.colby-verify-attempts-${session_id}.
#      Counter increments only on typecheck failure (exit 2 path); on typecheck success
#      the counter file is deleted (reset to zero). If the counter has already reached
#      verify_max_attempts (default 3) on entry, exits 0 with a stderr warning --
#      prevents an infinite Colby<->hook loop on type errors Colby cannot resolve.
#   2. Runs verify_commands.format in-place. Format failures are logged to stderr but
#      never block (formatting is a courtesy, not a gate). Format never increments the
#      counter.
#   3. Runs verify_commands.typecheck. On failure: prints the last ~40 lines of the
#      compiler output on stderr, increments the failure counter, and exits 2 --
#      Claude Code surfaces stderr to the agent and re-engages Colby. On success:
#      deletes the counter file and exits 0 silently (no stdout, no stderr).
#
# Missing verify_commands in pipeline-config.json exits 0 cleanly (opt-in only).
#
# Type: command (per feedback_no_background_agents.md -- type: agent SubagentStop is banned).
# Pattern: stdin parse + agent_type gating from enforce-colby-paths.sh; SubagentStop
# stdin shape from log-agent-stop.sh.

# Do NOT use set -e -- we want failures in format/typecheck to be inspected, not abort the script.
set -uo pipefail

[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
[ -f "${PROJECT_ROOT}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)

# jq missing → fail open (do not block Colby on tooling absence)
if ! command -v jq &>/dev/null; then
  exit 0
fi

# ─── Agent gating ─────────────────────────────────────────────────────
# Only Colby triggers verification. Any other agent_type exits 0 silently.
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null || true)
[ "$AGENT_TYPE" = "colby" ] || exit 0

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null || true)
[ -z "$SESSION_ID" ] && SESSION_ID="unknown"

# ─── Config load ──────────────────────────────────────────────────────
# Precedence matches enforce-sequencing.sh: .cursor/ first, then .claude/.
if [ -f "${PROJECT_ROOT}/.cursor/pipeline-config.json" ]; then
  PIPELINE_CONFIG="${PROJECT_ROOT}/.cursor/pipeline-config.json"
elif [ -f "${PROJECT_ROOT}/.claude/pipeline-config.json" ]; then
  PIPELINE_CONFIG="${PROJECT_ROOT}/.claude/pipeline-config.json"
else
  # No pipeline-config.json at all -- not an opted-in project.
  exit 0
fi

FORMAT_CMD=$(jq -r '.verify_commands.format // empty' "$PIPELINE_CONFIG" 2>/dev/null || true)
TYPECHECK_CMD=$(jq -r '.verify_commands.typecheck // empty' "$PIPELINE_CONFIG" 2>/dev/null || true)
MAX_ATTEMPTS=$(jq -r '.verify_max_attempts // 3' "$PIPELINE_CONFIG" 2>/dev/null || echo "3")

# Validate MAX_ATTEMPTS is a positive integer; fall back to 3 otherwise.
case "$MAX_ATTEMPTS" in
  ''|*[!0-9]*) MAX_ATTEMPTS=3 ;;
esac

# Both verify_commands fields absent → not opted in, exit silently.
if [ -z "$FORMAT_CMD" ] && [ -z "$TYPECHECK_CMD" ]; then
  exit 0
fi

# ─── Loop cap (FAILURE counter) ───────────────────────────────────────
# Per-session FAILURE counter file. Increments ONLY on typecheck failure;
# typecheck success deletes the file (reset to zero). Format never touches it.
# Once the counter has already reached MAX_ATTEMPTS on entry, we stop re-engaging
# Colby and let the work proceed (the type error may be outside her reach).
COUNTER_DIR="${PROJECT_ROOT}/docs/pipeline"
mkdir -p "$COUNTER_DIR" 2>/dev/null || true
COUNTER_FILE="${COUNTER_DIR}/.colby-verify-attempts-${SESSION_ID}"

CURRENT=0
if [ -f "$COUNTER_FILE" ]; then
  CURRENT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
  case "$CURRENT" in
    ''|*[!0-9]*) CURRENT=0 ;;
  esac
fi

if [ "$CURRENT" -ge "$MAX_ATTEMPTS" ]; then
  echo "WARNING: enforce-colby-stop-verify.sh: verify_max_attempts ($MAX_ATTEMPTS) reached for session $SESSION_ID. Skipping verification to break loop." >&2
  exit 0
fi

# ─── Run formatter (never blocks, never touches the counter) ──────────
if [ -n "$FORMAT_CMD" ]; then
  FORMAT_OUTPUT=$(cd "$PROJECT_ROOT" && eval "$FORMAT_CMD" 2>&1)
  FORMAT_RC=$?
  if [ "$FORMAT_RC" -ne 0 ]; then
    echo "WARNING: enforce-colby-stop-verify.sh: format command failed (exit $FORMAT_RC). Output:" >&2
    echo "$FORMAT_OUTPUT" | tail -n 20 >&2
    # Do not block on format failures.
  fi
fi

# ─── Run typechecker (gating; only this path touches the counter) ─────
if [ -n "$TYPECHECK_CMD" ]; then
  TYPECHECK_OUTPUT=$(cd "$PROJECT_ROOT" && eval "$TYPECHECK_CMD" 2>&1)
  TYPECHECK_RC=$?
  if [ "$TYPECHECK_RC" -ne 0 ]; then
    # Failure: increment the counter, then surface stderr and exit 2 to re-engage Colby.
    NEXT=$((CURRENT + 1))
    echo "$NEXT" > "$COUNTER_FILE" 2>/dev/null || true
    echo "BLOCKED: typecheck failed (exit $TYPECHECK_RC). Last output:" >&2
    echo "$TYPECHECK_OUTPUT" | tail -n 40 >&2
    exit 2
  fi
fi

# Success: delete the counter file (full reset) and exit silently.
rm -f "$COUNTER_FILE" 2>/dev/null || true
exit 0
