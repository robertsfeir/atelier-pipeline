#!/bin/sh
# Ensure dependencies are installed before starting the brain MCP server.
# Solves the timing issue where plugin.json mcpServers spawns the server
# before the SessionStart hook runs npm install.

BRAIN_DIR="$(cd "$(dirname "$0")" && pwd)"

# Fallback exports for when plugin.json env ${VAR} references are unresolved
# (e.g. project-level config with no plugin context).
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$BRAIN_DIR/..}"
export CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/atelier-pipeline}"
export NODE_TLS_REJECT_UNAUTHORIZED="${NODE_TLS_REJECT_UNAUTHORIZED:-0}"

if [ ! -f "$BRAIN_DIR/node_modules/.package-lock.json" ]; then
  npm install --prefix "$BRAIN_DIR" --silent 2>/dev/null
fi

exec node "$BRAIN_DIR/server.mjs"
