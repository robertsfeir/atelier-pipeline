#!/bin/bash
# session-hydrate-enforcement.sh -- SessionStart hook (called from session-hydrate.sh)
# Reads today's enforcement audit log, filters for blocked decisions, and
# bulk-captures them into the brain as 'insight' thoughts with
# metadata.enforcement_event: true.
#
# Fail-open: exits 0 always. Skip silently if log absent or brain unavailable.
# No retry logic (Retro #004).
#
# ADR: docs/architecture/ADR-0031-permission-audit-trail.md
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-${CURSOR_PROJECT_DIR:-}}"
[ -n "$PROJECT_DIR" ] || exit 0

HYDRATE_SCRIPT="$PROJECT_DIR/brain/scripts/hydrate-enforcement.mjs"
[ -f "$HYDRATE_SCRIPT" ] || exit 0

# Skip silently if no enforcement log exists for today
LOG_FILE="$HOME/.claude/logs/enforcement-$(date -u +%Y-%m-%d).jsonl"
[ -f "$LOG_FILE" ] || exit 0

node "$HYDRATE_SCRIPT" --silent >/dev/null 2>&1 || true
exit 0
