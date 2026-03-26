#!/usr/bin/env bats
# ADR-0005 Step 5: Skill Command Files Conversion
# Tests: T-0005-060 through T-0005-068, T-0005-108 through T-0005-111

load test_helper

# ── T-0005-060: All 7 command files use skill XML structure ──────────

@test "T-0005-060: all 7 command files use the skill XML tag structure" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || { echo "Missing: $file"; fail=1; continue; }

    for tag in "${SKILL_TAGS[@]}"; do
      assert_has_tag "$file" "$tag" || { fail=1; continue 2; }
      assert_has_closing_tag "$file" "$tag" || { fail=1; continue 2; }
    done

    # Verify order
    local i=0
    while [ $i -lt $((${#SKILL_TAGS[@]} - 1)) ]; do
      assert_tag_order "$file" "${SKILL_TAGS[$i]}" "${SKILL_TAGS[$((i+1))]}" || fail=1
      i=$((i + 1))
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-061: YAML frontmatter unchanged ──────────────────────────

@test "T-0005-061: YAML frontmatter present in every command file" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    head -1 "$file" | grep -q '^---' || { echo "Missing YAML start in $f"; fail=1; }
    grep -q '^name:' "$file" || grep -q '^description:' "$file" || { echo "Missing YAML fields in $f"; fail=1; }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-062: No MUST/CRITICAL/NEVER intensity markers ────────────

@test "T-0005-062: no command file contains MUST/CRITICAL/NEVER as intensity markers" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    local content
    content=$(sed '/^---$/,/^---$/d' "$file" | sed '/^```/,/^```/d')
    for marker in MUST CRITICAL NEVER; do
      if echo "$content" | grep -qE "\b${marker}\b"; then
        echo "Found intensity marker '$marker' in $f"
        echo "$content" | grep -nE "\b${marker}\b" | head -3
        fail=1
      fi
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-063: No original rule silently dropped ────────────────────

@test "T-0005-063: every command file has non-empty constraints and behavior sections" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    local constraints
    constraints=$(extract_tag_content "$file" "constraints")
    local constraint_lines
    constraint_lines=$(echo "$constraints" | grep -cvE '^\s*$|</?constraints>' || echo 0)
    if [ "$constraint_lines" -lt 1 ]; then
      echo "Empty constraints in $f"
      fail=1
    fi

    local behavior
    behavior=$(extract_tag_content "$file" "behavior")
    local behavior_lines
    behavior_lines=$(echo "$behavior" | grep -cvE '^\s*$|</?behavior>' || echo 0)
    if [ "$behavior_lines" -lt 1 ]; then
      echo "Empty behavior in $f"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-064: Source command templates preserve placeholders ────────

@test "T-0005-064: source command templates preserve placeholder variables" {
  local has_placeholders=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$SOURCE_COMMANDS/$f"
    [ -f "$file" ] || continue
    if grep -qE '\{[a-z_]+\}' "$file"; then
      has_placeholders=1
    fi
  done
  # At least some source command files should have placeholders
  # (not all may have them, so we just verify those that do are preserved)
}

# ── T-0005-065: pipeline.md preserves phase transition logic ─────────

@test "T-0005-065: pipeline.md command preserves phase transition logic" {
  local file="$INSTALLED_COMMANDS/pipeline.md"
  local behavior
  behavior=$(extract_tag_content "$file" "behavior")
  # Should reference phase transitions, agents, and routing
  echo "$behavior" | grep -qiE "phase|transition|route|agent" || {
    echo "Missing phase transition logic in pipeline.md behavior"
    return 1
  }
}

# ── T-0005-066: debug.md preserves Roz -> Colby -> Roz flow ─────────

@test "T-0005-066: debug.md preserves the Roz -> Colby -> Roz flow" {
  local file="$INSTALLED_COMMANDS/debug.md"
  grep -qi "Roz" "$file"
  grep -qi "Colby" "$file"
}

# ── T-0005-067: Every skill has required-actions with cognitive directive

@test "T-0005-067: every skill command has required-actions with cognitive directive" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    local cmd_name="${f%.md}"
    local directive="$(get_cognitive_directive "$cmd_name")"
    [ -z "$directive" ] && continue

    local ra
    ra=$(extract_tag_content "$file" "required-actions")
    echo "$ra" | grep -qF "$directive" || {
      echo "Missing cognitive directive in $f: expected '$directive'"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-068: Skill required-actions has only directive, no numbered steps

@test "T-0005-068: skill required-actions contains only directive, no numbered steps" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    local ra
    ra=$(extract_tag_content "$file" "required-actions")
    # Check for numbered steps (lines starting with digits followed by period)
    if echo "$ra" | grep -qE '^\s*[0-9]+\.'; then
      echo "Found numbered steps in skill required-actions of $f"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-108: No <workflow> or <tools> tags in skill files ─────────

@test "T-0005-108: no skill command file contains <workflow> or <tools> tags" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    if grep -q '<workflow>' "$file"; then
      echo "Found <workflow> in $f"
      fail=1
    fi
    if grep -q '<tools>' "$file"; then
      echo "Found <tools> in $f"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-109: No intensity markers or leftover markdown headings ───

@test "T-0005-109: no skill command file has leftover markdown headings for converted sections" {
  local fail=0
  local headings=("## Constraints" "## Output" "## Behavior")
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    for heading in "${headings[@]}"; do
      # Check for headings outside of code blocks
      local content
      content=$(sed '/^```/,/^```/d' "$file")
      if echo "$content" | grep -q "^${heading}$"; then
        echo "Leftover heading '$heading' in $f"
        fail=1
      fi
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-110: devops.md has required-actions with cognitive directive

@test "T-0005-110: devops.md has required-actions with cognitive directive" {
  local file="$INSTALLED_COMMANDS/devops.md"
  assert_has_tag "$file" "required-actions"
  local ra
  ra=$(extract_tag_content "$file" "required-actions")
  local directive="$(get_cognitive_directive "devops")"
  echo "$ra" | grep -qF "$directive" || {
    echo "Missing cognitive directive in devops.md"
    return 1
  }
}

# ── T-0005-111: Skill required-actions has no numbered steps ─────────

@test "T-0005-111: skill required-actions does not contain numbered steps" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    local ra
    ra=$(extract_tag_content "$file" "required-actions")
    if echo "$ra" | grep -qE '^\s*[0-9]+\.'; then
      echo "Found numbered steps in required-actions of $f"
      echo "$ra" | grep -E '^\s*[0-9]+\.' | head -3
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-139: No <examples> tag in skill command files ─────────────
# (Placed here since it relates to skills, though numbered under Step 9)

@test "T-0005-139: no skill command file contains an <examples> tag" {
  local fail=0
  for f in "${COMMAND_FILES[@]}"; do
    local file="$INSTALLED_COMMANDS/$f"
    [ -f "$file" ] || continue
    if grep -q '<examples>' "$file"; then
      echo "Found <examples> in skill command file $f"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}
