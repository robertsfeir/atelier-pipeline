#!/bin/sh
# Ensure dependencies are installed before starting the brain MCP server.
# Solves the timing issue where .mcp.json spawns the server before the
# SessionStart hook runs npm install.

BRAIN_DIR="$(dirname "$0")"

if [ ! -d "$BRAIN_DIR/node_modules" ]; then
  npm install --prefix "$BRAIN_DIR" --silent 2>/dev/null
fi

exec node "$BRAIN_DIR/server.mjs"
