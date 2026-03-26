#!/usr/bin/env bats
# ADR-0005 Step 6: Eva's Rules Files Update
# Tests: T-0005-070 through T-0005-075, T-0005-112 through T-0005-113

load test_helper

# ── T-0005-070: agent-system.md shows XML invocation format ──────────

@test "T-0005-070: agent-system.md standardized template section shows XML format" {
  local file="$INSTALLED_RULES/agent-system.md"
  grep -q '<task>' "$file"
  grep -q '<constraints>' "$file"
  grep -q '<output>' "$file"
}

# ── T-0005-071: Shared Agent Behaviors references XML tag names ──────

@test "T-0005-071: agent-system.md shared behaviors references XML tag names" {
  local file="$INSTALLED_RULES/agent-system.md"
  # Should reference tag names like <required-actions>, <output>, etc.
  grep -qE '<required-actions>|<output>|<identity>|required-actions|`<' "$file" || \
  grep -qE 'XML.*tag|tag.*structure|persona.*tag' "$file"
}

# ── T-0005-072: Brain responsibility shift documented ────────────────

@test "T-0005-072: brain responsibility shift documented in agent-system.md" {
  local file="$INSTALLED_RULES/agent-system.md"
  # Eva pre-fetches brain context
  grep -qiE "pre.?fetch|prefetch|Eva.*brain.*context|brain.*context.*Eva" "$file" || \
  grep -qiE "Eva.*inject|inject.*brain|Eva.*capture" "$file"
}

# ── T-0005-073: No old flat invocation format ────────────────────────

@test "T-0005-073: agent-system.md does not contain old flat invocation format" {
  local file="$INSTALLED_RULES/agent-system.md"
  # The old format used lines like "TASK: [description]" or "> TASK:"
  # within the standardized template section
  # We look for the old-style uppercase markers used as format elements
  # Note: these may appear in prose discussing the old format -- check
  # the template section specifically
  local template_section
  template_section=$(sed -n '/Standardized Template/,/^## /p' "$file")
  if echo "$template_section" | grep -qE '^TASK:'; then
    echo "Old flat format 'TASK:' found in template section"
    return 1
  fi
}

# ── T-0005-074: pipeline-models.md notes model identity in persona files

@test "T-0005-074: pipeline-models.md notes model identity is also in persona files" {
  local file="$INSTALLED_RULES/pipeline-models.md"
  [ -f "$file" ] || skip "pipeline-models.md not found"
  grep -qiE "persona|identity|agent.*file" "$file"
}

# ── T-0005-075: Source copies updated in sync ────────────────────────

@test "T-0005-075: source/rules/ agent-system.md shows XML invocation format" {
  local file="$SOURCE_RULES/agent-system.md"
  grep -q '<task>' "$file"
  grep -q '<constraints>' "$file"
  grep -q '<output>' "$file"
}

# ── T-0005-112: No old flat-text invocation markers ──────────────────

@test "T-0005-112: agent-system.md does not use old flat-text markers as format elements" {
  local file="$INSTALLED_RULES/agent-system.md"
  # Check the template section for old-style line-starting markers
  local template_section
  template_section=$(sed -n '/Standardized Template/,/^## /p' "$file")
  for marker in "TASK:" "READ:" "CONTEXT:" "WARN:" "CONSTRAINTS:" "OUTPUT:"; do
    if echo "$template_section" | grep -qE "^${marker}"; then
      echo "Old flat marker '$marker' found as line-starting format element"
      return 1
    fi
  done
}

# ── T-0005-113: No "MUST call agent_search/agent_capture" ────────────

@test "T-0005-113: agent-system.md does not contain 'MUST call agent_search' or 'MUST call agent_capture'" {
  local file="$INSTALLED_RULES/agent-system.md"
  assert_not_contains "$file" 'MUST call agent_search' "Found 'MUST call agent_search'"
  assert_not_contains "$file" 'MUST call agent_capture' "Found 'MUST call agent_capture'"
}
