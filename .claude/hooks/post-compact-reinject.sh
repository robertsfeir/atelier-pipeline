#!/bin/bash
# PostCompact hook -- context preservation after compaction
# Fires after Claude Code compacts the context window. Outputs
# pipeline-state.md and context-brief.md to stdout for re-injection
# into the post-compaction context.
#
# Only outputs pipeline-state.md and context-brief.md (small, ~3KB).
# Does NOT output error-patterns.md, investigation-ledger.md, or
# last-qa-report.md (those are read on-demand).
#
# Non-enforcement hook: exits 0 always. No brain calls, no blocking.
# Retro lesson #003 compliant.

# Do NOT use set -e -- we want graceful degradation
set -uo pipefail

# Require CLAUDE_PROJECT_DIR (or CURSOR_PROJECT_DIR)
PROJECT_DIR="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-}}"
if [ -z "$PROJECT_DIR" ]; then
  exit 0
fi

# Source the pipeline-state-path helper (ADR-0032 implementation)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/pipeline-state-path.sh" ]; then
  # shellcheck source=pipeline-state-path.sh
  source "$SCRIPT_DIR/pipeline-state-path.sh" 2>/dev/null || true
fi

# Define fallback if helper did not load
# Fallback uses PROJECT_DIR to produce an absolute path so the hook resolves
# correctly regardless of the current working directory.
if ! command -v session_state_dir &>/dev/null; then
  session_state_dir() { echo "$PROJECT_DIR/docs/pipeline"; }
fi

# Resolve per-worktree state directory (ADR-0032)
STATE_DIR=$(session_state_dir)
STATE_FILE="$STATE_DIR/pipeline-state.md"
BRIEF_FILE="$STATE_DIR/context-brief.md"

# If pipeline-state.md does not exist, output nothing
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

# Check readability of pipeline-state.md
if [ ! -r "$STATE_FILE" ]; then
  exit 0
fi

# Output header marker
echo "--- Re-injected after compaction ---"

# Output pipeline-state.md
echo ""
echo "## From: $STATE_FILE"
echo ""
cat "$STATE_FILE" 2>/dev/null || true

# Output context-brief.md if it exists and is readable
if [ -f "$BRIEF_FILE" ] && [ -r "$BRIEF_FILE" ]; then
  echo ""
  echo "## From: $BRIEF_FILE"
  echo ""
  cat "$BRIEF_FILE" 2>/dev/null || true
fi

echo ""
echo "## Brain Protocol Reminder"
echo ""
echo "- Prefetch hook: prompt-brain-prefetch.sh (before Agent) reminds Eva to call agent_search for cal/colby/roz before invoking them. Eva injects results into <brain-context>."
echo "- Mechanical capture: brain-extractor SubagentStop hook fires after cal/colby/roz/agatha/robert/robert-spec/sable/sable-ux/ellis and captures decisions/patterns/lessons automatically."
echo "- Eva cross-cutting: Eva captures user decisions, phase transitions, and cross-agent patterns (best-effort)."
echo ""
echo "---"

exit 0
