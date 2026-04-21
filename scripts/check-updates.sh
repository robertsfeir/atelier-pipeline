#!/usr/bin/env bash
# Checks if installed pipeline files are outdated vs the plugin version.
# Called by SessionStart hook with $1 = CLAUDE_PLUGIN_ROOT.
# Outputs a message for Eva when updates are available; silent otherwise.

set -euo pipefail

PLUGIN_ROOT="${1:?missing PLUGIN_ROOT}"

# Read current plugin version (shared across both platforms)
PLUGIN_VERSION_FILE="${PLUGIN_ROOT}/.claude-plugin/plugin.json"
PLUGIN_VERSION=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$PLUGIN_VERSION_FILE" | head -1 | grep -o '"[^"]*"$' | tr -d '"')
[ -n "$PLUGIN_VERSION" ] || exit 0

# Hardcoded list of files removed from source/ in past versions, keyed as dir/filename.
# Add entries here when a template is removed in a new plugin version.
REMOVED_TEMPLATES="
agents/docker-infrastructure.md
agents/python-fastapi.md
agents/nextjs-app-router.md
agents/react-frontend.md
agents/roz.md
agents/cal.md
references/qa-checks.md
references/retro-lessons.md
pipeline/last-qa-report.md
hooks/enforce-roz-paths.sh
hooks/enforce-cal-paths.sh
commands/debug.md
"

# check_platform PLATFORM_DIR PLATFORM_LABEL
# Checks a single platform's installed version against the plugin version.
check_platform() {
  local platform_dir="$1"
  local platform_label="$2"
  local version_file="${platform_dir}/.atelier-version"

  [ -f "$version_file" ] || return 0

  local installed_version
  installed_version=$(cat "$version_file" 2>/dev/null | tr -d '[:space:]')
  [ -n "$installed_version" ] || return 0

  if [ "$installed_version" != "$PLUGIN_VERSION" ]; then
    # Build list of changed template files (skip pipeline state files — those are user data)
    local changed=""
    for dir in agents commands rules references; do
      local src_dir="${PLUGIN_ROOT}/source/shared/${dir}"
      local dst_dir="${platform_dir}/${dir}"
      [ -d "$src_dir" ] && [ -d "$dst_dir" ] || continue
      for src_file in "$src_dir"/*.md; do
        [ -f "$src_file" ] || continue
        local filename
        filename=$(basename "$src_file")
        local dst_file="${dst_dir}/${filename}"
        [ -f "$dst_file" ] || { changed="${changed:+$changed, }${dir}/${filename} (new)"; continue; }
      done
    done

    # Check hooks directory — only for Claude Code (.claude/), not Cursor
    # Hooks come from two source dirs: source/shared/hooks/ and source/claude/hooks/
    if [ "$(basename "$platform_dir")" = ".claude" ]; then
      local dst_hooks="${platform_dir}/hooks"
      for hooks_src_dir in "${PLUGIN_ROOT}/source/shared/hooks" "${PLUGIN_ROOT}/source/claude/hooks"; do
        [ -d "$hooks_src_dir" ] && [ -d "$dst_hooks" ] || continue
        for src_file in "$hooks_src_dir"/*; do
          [ -f "$src_file" ] || continue
          local filename
          filename=$(basename "$src_file")
          local dst_file="${dst_hooks}/${filename}"
          [ -f "$dst_file" ] || { changed="${changed:+$changed, }hooks/${filename} (new)"; continue; }
        done
      done
    fi

    # Detect stale files that have been removed from the plugin
    local stale=""
    while IFS= read -r entry; do
      [ -n "$entry" ] || continue
      local dst_file="${platform_dir}/${entry}"
      [ -f "$dst_file" ] && stale="${stale:+$stale, }${entry}"
    done <<< "$REMOVED_TEMPLATES"

    echo "[atelier-pipeline] ${platform_label} update available: installed v${installed_version}, plugin v${PLUGIN_VERSION}."
    if [ -n "$changed" ]; then
      echo "New templates: ${changed}."
    fi
    if [ -n "$stale" ]; then
      echo "Stale files from previous versions: ${stale}. These files have been removed from the plugin and can be safely deleted."
    fi
    echo "Ask the user if they want to update their pipeline files. Use /pipeline-setup to reinstall, or selectively copy changed templates from the plugin's source/ directory."
  fi
}

# Check Claude Code installation (.claude/.atelier-version)
check_platform ".claude" "Claude Code"

# Check Cursor installation (.cursor/.atelier-version)
check_platform ".cursor" "Cursor"
