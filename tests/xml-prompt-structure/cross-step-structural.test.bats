#!/usr/bin/env bats
# ADR-0005 Cross-Step Structural Tests
# Tests: T-0005-120 through T-0005-123

load test_helper

# ── T-0005-120: Every opening tag has a matching closing tag ─────────

@test "T-0005-120: every opening XML tag has a matching closing tag in agent files" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    # Extract all tag names from opening tags
    while IFS= read -r tag; do
      if ! grep -q "</${tag}>" "$file"; then
        echo "Unclosed tag <${tag}> in $f"
        fail=1
      fi
    done < <(grep -oE '<[a-z][a-z-]*>' "$file" | sed 's/[<>]//g' | sort -u)
  done
  [ "$fail" -eq 0 ]
}

@test "T-0005-120b: every opening XML tag has a matching closing tag in command files" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    while IFS= read -r tag; do
      if ! grep -q "</${tag}>" "$file"; then
        echo "Unclosed tag <${tag}> in $f"
        fail=1
      fi
    done < <(grep -oE '<[a-z][a-z-]*>' "$file" | sed 's/[<>]//g' | sort -u)
  done
  [ "$fail" -eq 0 ]
}

@test "T-0005-120c: every opening XML tag has a matching closing tag in retro-lessons.md" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  local fail=0
  while IFS= read -r tag; do
    local open_count close_count
    open_count=$(grep -c "<${tag}[ >]" "$file" 2>/dev/null || grep -c "<${tag}>" "$file" 2>/dev/null || echo 0)
    close_count=$(grep -c "</${tag}>" "$file" 2>/dev/null || echo 0)
    if [ "$open_count" -ne "$close_count" ]; then
      echo "Tag mismatch for <${tag}> in retro-lessons.md: $open_count opens vs $close_count closes"
      fail=1
    fi
  done < <(grep -oE '<[a-z][a-z-]*[ >]' "$file" | sed 's/[ >]//g' | sort -u)
  [ "$fail" -eq 0 ]
}

# ── T-0005-121: Thought type values match brain thought_type enum ────

@test "T-0005-121: thought type values in schema/templates match brain enum" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  # Check that the thought tag examples/documentation include all enum values
  local expected_types="decision pattern lesson correction drift insight handoff rejection preference"
  for type in $expected_types; do
    grep -q "$type" "$file" || grep -q "$type" "$INSTALLED_REFS/xml-prompt-schema.md" || {
      echo "Thought type '$type' not found in templates or schema"
      return 1
    }
  done
}

# ── T-0005-122: Thought agent values include all 10 agents ──────────

@test "T-0005-122: thought agent attribute values include all 10 agents in schema" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  local all_agents="cal colby roz agatha robert sable eva poirot ellis distillator"
  local fail=0
  for agent in $all_agents; do
    grep -q "$agent" "$schema" || {
      echo "Agent '$agent' not listed in schema's thought agent values"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-123: No persona-level tags nested inside other persona tags

@test "T-0005-123: no persona-level tags nested inside other persona-level tags" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    for outer in "${PERSONA_TAGS[@]}"; do
      local content
      content=$(extract_tag_content "$file" "$outer")
      for inner in "${PERSONA_TAGS[@]}"; do
        [ "$inner" = "$outer" ] && continue
        if echo "$content" | grep -q "<${inner}>"; then
          echo "Nested <${inner}> inside <${outer}> in $f"
          fail=1
        fi
      done
    done
  done
  [ "$fail" -eq 0 ]
}
