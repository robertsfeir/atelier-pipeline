#!/usr/bin/env bash
# Checks if installed pipeline files are outdated vs the plugin version.
# Called by SessionStart hook with $1 = CLAUDE_PLUGIN_ROOT.
# Outputs a message for Eva when updates are available; silent otherwise.

set -euo pipefail

PLUGIN_ROOT="${1:?missing CLAUDE_PLUGIN_ROOT}"
VERSION_FILE=".claude/.atelier-version"
PLUGIN_VERSION_FILE="${PLUGIN_ROOT}/.claude-plugin/plugin.json"

# Only run in projects that have the pipeline installed
[ -f "$VERSION_FILE" ] || exit 0

# Read installed version
INSTALLED_VERSION=$(cat "$VERSION_FILE" 2>/dev/null | tr -d '[:space:]')
[ -n "$INSTALLED_VERSION" ] || exit 0

# Read current plugin version
PLUGIN_VERSION=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$PLUGIN_VERSION_FILE" | head -1 | grep -o '"[^"]*"$' | tr -d '"')
[ -n "$PLUGIN_VERSION" ] || exit 0

# Compare
if [ "$INSTALLED_VERSION" != "$PLUGIN_VERSION" ]; then
  # Build list of changed template files (skip pipeline state files — those are user data)
  CHANGED=""
  for dir in agents commands rules references; do
    src_dir="${PLUGIN_ROOT}/source/${dir}"
    dst_dir=".claude/${dir}"
    [ -d "$src_dir" ] && [ -d "$dst_dir" ] || continue
    for src_file in "$src_dir"/*.md; do
      [ -f "$src_file" ] || continue
      filename=$(basename "$src_file")
      dst_file="${dst_dir}/${filename}"
      [ -f "$dst_file" ] || { CHANGED="${CHANGED:+$CHANGED, }${dir}/${filename} (new)"; continue; }
    done
  done

  # Detect stale files that have been removed from the plugin but still exist in .claude/
  # Hardcoded list of files removed from source/ in past versions, keyed as dir/filename.
  # Add entries here when a template is removed in a new plugin version.
  REMOVED_TEMPLATES="
agents/docker-infrastructure.md
agents/python-fastapi.md
agents/nextjs-app-router.md
agents/react-frontend.md
"
  STALE=""
  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    dst_file=".claude/${entry}"
    [ -f "$dst_file" ] && STALE="${STALE:+$STALE, }${entry}"
  done <<< "$REMOVED_TEMPLATES"

  echo "[atelier-pipeline] Update available: installed v${INSTALLED_VERSION}, plugin v${PLUGIN_VERSION}."
  if [ -n "$CHANGED" ]; then
    echo "New templates: ${CHANGED}."
  fi
  if [ -n "$STALE" ]; then
    echo "Stale files from previous versions: ${STALE}. These files have been removed from the plugin and can be safely deleted."
  fi
  echo "Ask the user if they want to update their pipeline files. Use /pipeline-setup to reinstall, or selectively copy changed templates from the plugin's source/ directory."
fi
