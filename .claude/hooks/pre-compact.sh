#!/bin/bash
# PreCompact hook -- pipeline state preservation
# Fires before Claude Code compacts the context window.
#
# Appends a timestamped compaction marker to pipeline-state.md so Eva's
# boot sequence can detect that compaction occurred. Lightweight by design
# (ADR-0012, retro lesson #003): no brain calls, no subagent invocations,
# no test runs. Exits 0 always -- never blocks compaction.

PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
STATE_FILE="$PROJECT_ROOT/docs/pipeline/pipeline-state.md"

# Clean up ADR-0050 Colby verify-attempt counter files (session-scoped temp state).
# These accumulate across compaction boundaries if not pruned. Best-effort: ignore
# errors so this never blocks compaction.
rm -f "$PROJECT_ROOT/docs/pipeline/.colby-verify-attempts-"* 2>/dev/null || true

# No-op if pipeline-state.md does not exist (non-pipeline sessions)
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

echo "<!-- COMPACTION: $(date -u +%Y-%m-%dT%H:%M:%SZ) -->" >> "$STATE_FILE"

exit 0
