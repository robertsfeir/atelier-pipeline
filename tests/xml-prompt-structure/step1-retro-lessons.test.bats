#!/usr/bin/env bats
# ADR-0005 Step 1: Retro Lessons Conversion
# Tests: T-0005-010 through T-0005-019

load test_helper

# ── T-0005-010: Root tag wrapping ────────────────────────────────────

@test "T-0005-010: retro-lessons.md contains <retro-lessons> root tag" {
  assert_has_tag "$INSTALLED_REFS/retro-lessons.md" "retro-lessons"
  assert_has_closing_tag "$INSTALLED_REFS/retro-lessons.md" "retro-lessons"
}

# ── T-0005-011: Lesson tags with id and agents attributes ────────────

@test "T-0005-011: each lesson has <lesson> tag with id (3-digit) and agents attributes" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  # Every <lesson> tag must have id="NNN" and agents="..."
  local lessons
  lessons=$(grep -c '<lesson ' "$file")
  [ "$lessons" -gt 0 ]

  # All lesson tags have id attribute with 3-digit format
  local ids_with_format
  ids_with_format=$(grep -cE '<lesson [^>]*id="[0-9]{3}"' "$file")
  [ "$lessons" -eq "$ids_with_format" ]

  # All lesson tags have agents attribute
  local with_agents
  with_agents=$(grep -cE '<lesson [^>]*agents="' "$file")
  [ "$lessons" -eq "$with_agents" ]
}

# ── T-0005-012: Rule tags with agent attribute ───────────────────────

@test "T-0005-012: each rule within a lesson has <rule agent=\"name\"> tag" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  local rules
  rules=$(grep -c '<rule ' "$file")
  [ "$rules" -gt 0 ]

  # Every <rule> has an agent attribute
  local with_agent
  with_agent=$(grep -cE '<rule agent="[a-z]+"' "$file")
  [ "$rules" -eq "$with_agent" ]
}

# ── T-0005-013: Introductory prose and CONFIGURE comment outside tag ─

@test "T-0005-013: CONFIGURE comment exists outside (above) the <retro-lessons> tag" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  local configure_line retro_line
  configure_line=$(line_of "$file" "CONFIGURE")
  retro_line=$(line_of "$file" "<retro-lessons>")
  [ -n "$configure_line" ]
  [ -n "$retro_line" ]
  [ "$configure_line" -lt "$retro_line" ]
}

@test "T-0005-013b: introductory prose exists outside (above) the <retro-lessons> tag" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  local retro_line
  retro_line=$(line_of "$file" "<retro-lessons>")
  # There should be non-empty lines of prose before the tag (not just comments)
  local prose_lines
  prose_lines=$(head -n "$((retro_line - 1))" "$file" | grep -cvE '^\s*$|^\s*<!--|^\s*#' || echo 0)
  [ "$prose_lines" -gt 0 ]
}

# ── T-0005-014: Agent consistency between lesson and rules ───────────

@test "T-0005-014: no lesson contains a rule for an agent not listed in its agents attribute" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  local fail=0

  # Extract each lesson block and check consistency
  local in_lesson=0 lesson_agents=""
  while IFS= read -r line; do
    if echo "$line" | grep -qE '<lesson [^>]*agents="([^"]*)"'; then
      in_lesson=1
      lesson_agents=$(echo "$line" | grep -oE 'agents="[^"]*"' | sed 's/agents="//;s/"//')
    fi
    if [ "$in_lesson" -eq 1 ] && echo "$line" | grep -qE '<rule agent="([^"]*)"'; then
      local rule_agent
      rule_agent=$(echo "$line" | grep -oE 'agent="[^"]*"' | sed 's/agent="//;s/"//')
      if ! echo ", $lesson_agents," | grep -q ", *${rule_agent} *,\|, *${rule_agent}$\|^${rule_agent} *,"; then
        # More robust check: split agents and compare
        local found=0
        IFS=',' read -ra agent_list <<< "$lesson_agents"
        for a in "${agent_list[@]}"; do
          a=$(echo "$a" | tr -d ' ')
          if [ "$a" = "$rule_agent" ]; then
            found=1
            break
          fi
        done
        if [ "$found" -eq 0 ]; then
          echo "Rule agent='$rule_agent' not in lesson agents='$lesson_agents'"
          fail=1
        fi
      fi
    fi
    if echo "$line" | grep -q '</lesson>'; then
      in_lesson=0
      lesson_agents=""
    fi
  done < "$file"
  [ "$fail" -eq 0 ]
}

# ── T-0005-015: Source and installed copies both converted ───────────

@test "T-0005-015: source and installed retro-lessons.md both have XML structure" {
  assert_has_tag "$SOURCE_REFS/retro-lessons.md" "retro-lessons"
  assert_has_closing_tag "$SOURCE_REFS/retro-lessons.md" "retro-lessons"
  assert_has_tag "$INSTALLED_REFS/retro-lessons.md" "retro-lessons"
  assert_has_closing_tag "$INSTALLED_REFS/retro-lessons.md" "retro-lessons"
}

# ── T-0005-016: Existing lesson content preserved ────────────────────

@test "T-0005-016: existing lesson content is preserved (spot check key phrases)" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  # Key phrases from existing lessons that must survive conversion
  grep -q "Sensitive Data in Return Shapes" "$file" || grep -q "sensitive.*return" "$file"
  grep -q "Self-Reporting Bug Codification" "$file" || grep -q "self-reporting" "$file"
  grep -q "Stop Hook Race Condition" "$file" || grep -q "stop.*hook.*race" "$file"
}

# ── T-0005-017: No lesson tag missing id attribute ───────────────────

@test "T-0005-017: no <lesson> tag is missing the id attribute" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  # Count lesson tags without id — use || true to suppress grep exit code 1 on zero matches
  local missing
  missing=$(grep -E '<lesson\b' "$file" | grep -cvE 'id=' || true)
  [ "$missing" -eq 0 ]
}

# ── T-0005-018: No duplicate lesson ids ──────────────────────────────

@test "T-0005-018: no two lesson elements share the same id value" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  local total_ids unique_ids
  total_ids=$(grep -oE 'id="[0-9]+"' "$file" | wc -l | tr -d ' ')
  unique_ids=$(grep -oE 'id="[0-9]+"' "$file" | sort -u | wc -l | tr -d ' ')
  [ "$total_ids" -eq "$unique_ids" ]
  [ "$total_ids" -gt 0 ]
}

# ── T-0005-019: Every agent in lesson's agents has a corresponding rule

@test "T-0005-019: every agent listed in a lesson's agents attribute has a <rule> child" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  local fail=0

  local in_lesson=0 lesson_agents="" rule_agents=""
  while IFS= read -r line; do
    if echo "$line" | grep -qE '<lesson [^>]*agents="([^"]*)"'; then
      in_lesson=1
      lesson_agents=$(echo "$line" | grep -oE 'agents="[^"]*"' | sed 's/agents="//;s/"//')
      rule_agents=""
    fi
    if [ "$in_lesson" -eq 1 ] && echo "$line" | grep -qE '<rule agent="([^"]*)"'; then
      local ra
      ra=$(echo "$line" | grep -oE 'agent="[^"]*"' | sed 's/agent="//;s/"//')
      rule_agents="$rule_agents $ra"
    fi
    if echo "$line" | grep -q '</lesson>'; then
      # Check each listed agent has a rule
      IFS=',' read -ra agent_list <<< "$lesson_agents"
      for a in "${agent_list[@]}"; do
        a=$(echo "$a" | tr -d ' ')
        if ! echo "$rule_agents" | grep -q "\b${a}\b"; then
          echo "Agent '$a' in lesson agents but no <rule agent=\"$a\"> found"
          fail=1
        fi
      done
      in_lesson=0
    fi
  done < "$file"
  [ "$fail" -eq 0 ]
}
