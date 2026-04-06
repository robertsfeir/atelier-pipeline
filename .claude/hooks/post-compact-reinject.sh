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

PIPELINE_DIR="$PROJECT_DIR/docs/pipeline"
STATE_FILE="$PIPELINE_DIR/pipeline-state.md"
BRIEF_FILE="$PIPELINE_DIR/context-brief.md"

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
echo "## From: docs/pipeline/pipeline-state.md"
echo ""
cat "$STATE_FILE" 2>/dev/null || true

# Output context-brief.md if it exists and is readable
if [ -f "$BRIEF_FILE" ] && [ -r "$BRIEF_FILE" ]; then
  echo ""
  echo "## From: docs/pipeline/context-brief.md"
  echo ""
  cat "$BRIEF_FILE" 2>/dev/null || true
fi

echo ""
echo "## Brain Protocol Reminder"
echo ""
echo "- Prefetch hook: prompt-brain-prefetch.sh (before Agent) injects brain context for cal/colby/roz/agatha."
echo "- Mechanical capture: brain-extractor SubagentStop hook fires after cal/colby/roz/agatha and captures decisions/patterns/lessons automatically."
echo "- Eva cross-cutting: Eva captures user decisions, phase transitions, and cross-agent patterns (best-effort)."
echo ""
echo "---"

exit 0
