#!/bin/bash
# DELETE BEFORE: 2026-07-01 — see ADR-0034 Wave 2 (backward-compat shim, one-quarter retention period)
# NOT REGISTERED in settings.json — intentional no-op. See comment below.
# session-hydrate.sh -- SessionStart hook
#
# Hydration is now handled by the atelier_hydrate MCP tool, which runs
# through the already-running brain server and uses its authenticated
# connection pool. See source/shared/references/session-boot.md step 4b.
#
# Previously this hook invoked hydrate-telemetry.mjs directly:
#   node "$PLUGIN_BRAIN" "$SESSION_PATH" --silent --state-dir "$STATE_DIR"
# That approach required a standalone DB connection which failed when the
# brain server used credential injection via .mcp.json.
#
# This hook is intentionally a no-op.
exit 0
