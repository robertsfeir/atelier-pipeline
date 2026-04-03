#!/usr/bin/env bats
# Tests for ADR-0020 Step 5: Documentation and File Sync
# Covers: T-0020-064 through T-0020-069
#
# Step 5 verifies that documentation references all hooks, installed copies
# match source, and Cursor plugin stays in sync with Claude Code plugin.

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Step 5: Documentation and Sync
# ═══════════════════════════════════════════════════════════════════════

# ── T-0020-064: Happy -- technical-reference.md documents all 10 hooks ──

@test "T-0020-064: technical-reference.md documents all 10 hooks with event type and script name" {
  local doc_file="$PROJECT_ROOT/docs/guide/technical-reference.md"
  [ -f "$doc_file" ]

  # Existing 6 hooks
  grep -q "enforce-paths.sh" "$doc_file"
  grep -q "enforce-sequencing.sh" "$doc_file"
  grep -q "enforce-pipeline-activation.sh" "$doc_file"
  grep -q "enforce-git.sh" "$doc_file"
  grep -q "warn-dor-dod.sh" "$doc_file"
  grep -q "pre-compact.sh" "$doc_file"

  # New 4 hooks
  grep -q "log-agent-start.sh" "$doc_file"
  grep -q "log-agent-stop.sh" "$doc_file"
  grep -q "post-compact-reinject.sh" "$doc_file"
  grep -q "log-stop-failure.sh" "$doc_file"

  # Event types should be documented
  grep -q "PreToolUse" "$doc_file"
  grep -q "SubagentStart" "$doc_file"
  grep -q "SubagentStop" "$doc_file"
  grep -q "PostCompact" "$doc_file"
  grep -q "StopFailure" "$doc_file"
}

# ── T-0020-065: Happy -- user-guide.md mentions if conditionals and new events ──

@test "T-0020-065: user-guide.md mentions if conditionals and lists the 4 new hook events" {
  local doc_file="$PROJECT_ROOT/docs/guide/user-guide.md"
  [ -f "$doc_file" ]

  # Should mention `if` conditionals
  grep -qi "if.*conditional\|conditional.*if\|\"if\".*field\|if.*filter" "$doc_file"

  # Should mention the new hook events
  grep -q "SubagentStart" "$doc_file"
  grep -q "PostCompact" "$doc_file"
  grep -q "StopFailure" "$doc_file"
}

# ── T-0020-066: Failure -- detect source/hooks/ script without .claude/hooks/ copy ──

@test "T-0020-066: every source/hooks/*.sh file has a corresponding .claude/hooks/ installed copy" {
  local source_dir="$PROJECT_ROOT/source/hooks"
  local installed_dir="$PROJECT_ROOT/.claude/hooks"

  [ -d "$source_dir" ]
  [ -d "$installed_dir" ]

  # Get list of .sh files in source/hooks/
  local missing=0
  for source_file in "$source_dir"/*.sh; do
    local basename
    basename=$(basename "$source_file")
    if [ ! -f "$installed_dir/$basename" ]; then
      echo "MISSING installed copy: $basename" >&2
      missing=$((missing + 1))
    fi
  done

  [ "$missing" -eq 0 ]
}

# ── T-0020-067: Failure -- detect Cursor SKILL.md hook entry absent from Claude Code SKILL.md ──

@test "T-0020-067: Cursor plugin SKILL.md hook entries are all present in Claude Code SKILL.md" {
  local cc_skill="$PROJECT_ROOT/skills/pipeline-setup/SKILL.md"
  local cursor_skill="$PROJECT_ROOT/.cursor-plugin/skills/pipeline-setup/SKILL.md"

  [ -f "$cc_skill" ]
  [ -f "$cursor_skill" ]

  # Extract all hook script names mentioned in each file
  local cursor_hooks cc_hooks
  cursor_hooks=$(grep -oE '[a-z]+-[a-z-]+\.sh' "$cursor_skill" | sort -u)
  cc_hooks=$(grep -oE '[a-z]+-[a-z-]+\.sh' "$cc_skill" | sort -u)

  # Every hook in cursor SKILL.md must also be in cc SKILL.md
  local divergence=0
  while IFS= read -r hook; do
    if ! echo "$cc_hooks" | grep -qF "$hook"; then
      echo "DIVERGENCE: $hook in Cursor SKILL.md but not in Claude Code SKILL.md" >&2
      divergence=$((divergence + 1))
    fi
  done <<< "$cursor_hooks"

  [ "$divergence" -eq 0 ]
}

# ── T-0020-068: Regression -- all .claude/hooks/ files are byte-identical to source/hooks/ ──

@test "T-0020-068: all installed .claude/hooks/ files are byte-identical to source/hooks/ counterparts" {
  local source_dir="$PROJECT_ROOT/source/hooks"
  local installed_dir="$PROJECT_ROOT/.claude/hooks"

  [ -d "$source_dir" ]
  [ -d "$installed_dir" ]

  local mismatch=0
  for source_file in "$source_dir"/*.sh; do
    local basename
    basename=$(basename "$source_file")
    local installed_file="$installed_dir/$basename"

    if [ -f "$installed_file" ]; then
      if ! cmp -s "$source_file" "$installed_file"; then
        echo "MISMATCH: $basename differs between source/ and .claude/hooks/" >&2
        mismatch=$((mismatch + 1))
      fi
    fi
  done

  # Also check enforcement-config.json if it exists in both places
  if [ -f "$source_dir/enforcement-config.json" ] && [ -f "$installed_dir/enforcement-config.json" ]; then
    if ! cmp -s "$source_dir/enforcement-config.json" "$installed_dir/enforcement-config.json"; then
      echo "MISMATCH: enforcement-config.json differs between source/ and .claude/hooks/" >&2
      mismatch=$((mismatch + 1))
    fi
  fi

  [ "$mismatch" -eq 0 ]
}

# ── T-0020-069: Regression -- Cursor SKILL.md hook registration matches Claude Code SKILL.md ──

@test "T-0020-069: Cursor plugin SKILL.md hook registration section matches Claude Code SKILL.md" {
  local cc_skill="$PROJECT_ROOT/skills/pipeline-setup/SKILL.md"
  local cursor_skill="$PROJECT_ROOT/.cursor-plugin/skills/pipeline-setup/SKILL.md"

  [ -f "$cc_skill" ]
  [ -f "$cursor_skill" ]

  # Extract hook registration JSON blocks from both files and compare
  # Both files should list the same hooks in their registration template
  local cc_hook_names cursor_hook_names
  cc_hook_names=$(grep -oE '[a-z]+-[a-z-]+\.sh' "$cc_skill" | sort -u)
  cursor_hook_names=$(grep -oE '[a-z]+-[a-z-]+\.sh' "$cursor_skill" | sort -u)

  # Compare the sorted hook name lists
  [ "$cc_hook_names" = "$cursor_hook_names" ]
}
