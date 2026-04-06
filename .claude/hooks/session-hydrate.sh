#!/bin/bash
# session-hydrate.sh -- SessionStart hook
# Runs hydrate-telemetry.mjs for T1 JSONL hydration and state-file parsing.
# Non-blocking: exits 0 always.
set -uo pipefail
PLUGIN_BRAIN="$CLAUDE_PROJECT_DIR/brain/scripts/hydrate-telemetry.mjs"
[ -f "$PLUGIN_BRAIN" ] || exit 0
PROJECT_PATH=$(echo "$CLAUDE_PROJECT_DIR" | sed 's|/|-|g' | sed 's/^-//')
SESSION_PATH="$HOME/.claude/projects/-$PROJECT_PATH"
STATE_DIR="$CLAUDE_PROJECT_DIR/docs/pipeline"
node "$PLUGIN_BRAIN" "$SESSION_PATH" --silent --state-dir "$STATE_DIR" >/dev/null 2>&1 || true
exit 0
