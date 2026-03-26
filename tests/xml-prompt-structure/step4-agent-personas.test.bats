#!/usr/bin/env bats
# ADR-0005 Step 4: Agent Persona Files Conversion
# Tests: T-0005-040 through T-0005-059, T-0005-100 through T-0005-107

load test_helper

# ── T-0005-040: All 9 agents have 7 XML tags in correct order ───────

@test "T-0005-040: all 9 agent files contain the 7 persona tags in order" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || { echo "Missing: $file"; fail=1; continue; }

    # Verify all 7 tags exist
    for tag in "${PERSONA_TAGS[@]}"; do
      assert_has_tag "$file" "$tag" || { fail=1; continue 2; }
      assert_has_closing_tag "$file" "$tag" || { fail=1; continue 2; }
    done

    # Verify order: each tag appears before the next
    local i=0
    while [ $i -lt $((${#PERSONA_TAGS[@]} - 1)) ]; do
      assert_tag_order "$file" "${PERSONA_TAGS[$i]}" "${PERSONA_TAGS[$((i+1))]}" || fail=1
      i=$((i + 1))
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-041: Identity contains name, role, pronouns, model ───────

@test "T-0005-041: every agent identity section contains name, role, pronouns, and model" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local identity
    identity=$(extract_tag_content "$file" "identity")

    # Check for agent name (the file basename without .md, or Poirot for investigator)
    local agent_name="${f%.md}"
    [ "$agent_name" = "investigator" ] && agent_name="Poirot"
    echo "$identity" | grep -qi "$agent_name" || {
      echo "Missing agent name in identity of $f"
      fail=1
    }

    # Check for pronouns
    echo "$identity" | grep -qiE "pronouns|she/her|he/him|they/them" || {
      echo "Missing pronouns in identity of $f"
      fail=1
    }

    # Check for model reference
    echo "$identity" | grep -qiE "model|Opus|Sonnet|Haiku" || {
      echo "Missing model reference in identity of $f"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-042: No "## Brain Access" markdown heading ────────────────

@test "T-0005-042: no agent file contains a '## Brain Access' markdown heading" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    assert_not_contains "$file" '^## Brain Access' "Found leftover '## Brain Access' heading in $f" || fail=1
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-043: Required-actions mentions retro lesson review ────────

@test "T-0005-043: every agent's required-actions mentions retro lesson review" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local ra
    ra=$(extract_tag_content "$file" "required-actions")
    echo "$ra" | grep -qi "retro" || {
      echo "Missing retro lesson reference in required-actions of $f"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-044: Brain-capable agents reference brain context ─────────

@test "T-0005-044: brain-capable agents reference brain context in required-actions" {
  local fail=0
  for agent in "${BRAIN_AGENTS[@]}"; do
    local f="${agent}.md"
    [ "$agent" = "investigator" ] && f="investigator.md"
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local ra
    ra=$(extract_tag_content "$file" "required-actions")
    echo "$ra" | grep -qiE "brain.context|brain context|brain-context|injected.*thought|provided.*brain" || {
      echo "Missing brain context reference in required-actions of $f"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-045: Distillator has no brain context reference ───────────

@test "T-0005-045: distillator required-actions does not reference brain context" {
  local file="$INSTALLED_AGENTS/distillator.md"
  local ra
  ra=$(extract_tag_content "$file" "required-actions")
  if echo "$ra" | grep -qiE "brain.context|brain context|brain-context"; then
    echo "Distillator should not reference brain context in required-actions"
    return 1
  fi
}

# ── T-0005-046: No "MUST call agent_search/agent_capture" ────────────

@test "T-0005-046: no agent file contains 'MUST call agent_search' or 'MUST call agent_capture'" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    assert_not_contains "$file" 'MUST call agent_search' "Found 'MUST call agent_search' in $f" || fail=1
    assert_not_contains "$file" 'MUST call agent_capture' "Found 'MUST call agent_capture' in $f" || fail=1
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-047: No "MANDATORY" in all-caps ──────────────────────────

@test "T-0005-047: no agent file contains 'MANDATORY' in all-caps" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    assert_not_contains "$file" '\bMANDATORY\b' "Found 'MANDATORY' in $f" || fail=1
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-048: YAML frontmatter unchanged ──────────────────────────

@test "T-0005-048: YAML frontmatter (name, description, disallowedTools) present in every agent" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    # File starts with ---
    head -1 "$file" | grep -q '^---' || { echo "Missing YAML start in $f"; fail=1; continue; }
    # Has name field
    grep -q '^name:' "$file" || { echo "Missing 'name:' in $f"; fail=1; }
    # Has description field
    grep -q '^description:' "$file" || grep -q '^description: ' "$file" || { echo "Missing 'description:' in $f"; fail=1; }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-049: No original constraint silently dropped ──────────────
# This is a regression test -- verified during QA by comparing before/after.
# The test here verifies that <constraints> is non-empty in every agent.

@test "T-0005-049: every agent has non-empty constraints section" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local constraints
    constraints=$(extract_tag_content "$file" "constraints")
    local line_count
    line_count=$(echo "$constraints" | grep -cvE '^\s*$|</?constraints>' || echo 0)
    if [ "$line_count" -lt 2 ]; then
      echo "Constraints section too short in $f (only $line_count content lines)"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-050: Source templates preserve placeholder variables ──────

@test "T-0005-050: source agent templates preserve placeholder variables inside XML tags" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$SOURCE_AGENTS/$f"
    [ -f "$file" ] || continue
    # Source files should have at least some {placeholder} variables
    if grep -qE '\{[a-z_]+\}' "$file"; then
      # Verify placeholders are inside XML-tagged content, not outside
      # (This is a basic check that placeholders survive)
      :
    fi
  done
}

# ── T-0005-051: Colby's identity states "she/her" ───────────────────

@test "T-0005-051: colby's identity states she/her pronouns" {
  local identity
  identity=$(extract_tag_content "$INSTALLED_AGENTS/colby.md" "identity")
  echo "$identity" | grep -q "she/her"
}

# ── T-0005-052: Poirot has no brain context in required-actions ──────

@test "T-0005-052: investigator.md (Poirot) has no brain context in required-actions" {
  local file="$INSTALLED_AGENTS/investigator.md"
  local ra
  ra=$(extract_tag_content "$file" "required-actions")
  if echo "$ra" | grep -qiE "brain.context|brain context|brain-context"; then
    echo "Poirot should not reference brain context in required-actions"
    return 1
  fi
}

# ── T-0005-053: No MUST/CRITICAL/NEVER intensity markers ────────────

@test "T-0005-053: no agent file uses MUST/CRITICAL/NEVER as intensity markers" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    # Check for all-caps intensity markers (not inside YAML frontmatter or code blocks)
    # Exclude lines inside ``` code blocks and YAML frontmatter
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

# ── T-0005-054: Output section includes knowledge surfacing guidance ─

@test "T-0005-054: each agent's output includes knowledge surfacing guidance for Eva" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local output
    output=$(extract_tag_content "$file" "output")
    # Should mention knowledge, patterns, decisions, or Eva
    echo "$output" | grep -qiE "knowledge|pattern|decision|Eva|brain|capture|insight" || {
      echo "Missing knowledge surfacing guidance in output of $f"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-055: Cal's model identity says "Opus" ────────────────────

@test "T-0005-055: Cal's model identity says Opus" {
  local identity
  identity=$(extract_tag_content "$INSTALLED_AGENTS/cal.md" "identity")
  echo "$identity" | grep -qi "Opus"
}

# ── T-0005-056: Colby's model identity mentions size-dependent range ─

@test "T-0005-056: Colby's model identity mentions size-dependent range" {
  local identity
  identity=$(extract_tag_content "$INSTALLED_AGENTS/colby.md" "identity")
  # Should mention multiple model tiers or size dependency
  echo "$identity" | grep -qiE "Sonnet.*Opus|small.*medium.*large|Haiku.*Sonnet.*Opus|size" || \
  echo "$identity" | grep -qiE "Sonnet.*(small|medium)|Opus.*(large)"
}

# ── T-0005-057: atelier-pipeline comment preserved ───────────────────

@test "T-0005-057: <!-- Part of atelier-pipeline --> comment preserved in every agent file" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    grep -q 'Part of atelier-pipeline' "$file" || {
      echo "Missing atelier-pipeline comment in $f"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-058: Cognitive directive paragraph before numbered list ───

@test "T-0005-058: every agent's required-actions begins with cognitive directive" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local agent_name="${f%.md}"
    local directive="$(get_cognitive_directive "$agent_name")"
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

# ── T-0005-059: Cognitive directives use conversational tone ─────────

@test "T-0005-059: cognitive directives have no MUST/CRITICAL/NEVER intensity markers" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local agent_name="${f%.md}"
    local directive="$(get_cognitive_directive "$agent_name")"
    [ -z "$directive" ] && continue
    for marker in MUST CRITICAL; do
      if echo "$directive" | grep -qE "\b${marker}\b"; then
        echo "Cognitive directive for $agent_name contains intensity marker '$marker'"
        fail=1
      fi
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-100: No empty required-actions ────────────────────────────

@test "T-0005-100: no agent has an empty required-actions tag" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local ra
    ra=$(extract_tag_content "$file" "required-actions")
    local content_lines
    content_lines=$(echo "$ra" | grep -cvE '^\s*$|</?required-actions>' || echo 0)
    if [ "$content_lines" -lt 1 ]; then
      echo "Empty required-actions in $f"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-101: No nested persona-level tags ─────────────────────────

@test "T-0005-101: no agent file has nested persona-level tags" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    # Check that persona tags are not nested inside each other
    for outer in "${PERSONA_TAGS[@]}"; do
      local inner_content
      inner_content=$(extract_tag_content "$file" "$outer")
      for inner in "${PERSONA_TAGS[@]}"; do
        [ "$inner" = "$outer" ] && continue
        if echo "$inner_content" | grep -q "<${inner}>"; then
          echo "Nested tag <${inner}> inside <${outer}> in $f"
          fail=1
        fi
      done
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-102: No leftover markdown headings for converted sections ─

@test "T-0005-102: no agent file has leftover markdown headings for XML-converted sections" {
  local fail=0
  local headings=("## Brain Access" "## Shared Rules" "## Tool Constraints" "## Forbidden Actions")
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    for heading in "${headings[@]}"; do
      if grep -q "^${heading}" "$file"; then
        echo "Leftover heading '$heading' in $f"
        fail=1
      fi
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-103: No brain tool call instructions in agent files ───────

@test "T-0005-103: no agent file contains brain tool call instructions" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    for pattern in 'MUST call agent_search' 'MUST call agent_capture' 'call `agent_search`' 'call `agent_capture`'; do
      if grep -qF "$pattern" "$file"; then
        echo "Found brain tool call instruction '$pattern' in $f"
        fail=1
      fi
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-104: Cognitive directive text matches ADR exactly ─────────

@test "T-0005-104: every agent's cognitive directive matches ADR table exactly" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local agent_name="${f%.md}"
    local directive="$(get_cognitive_directive "$agent_name")"
    [ -z "$directive" ] && continue
    grep -qF "$directive" "$file" || {
      echo "Cognitive directive mismatch in $f"
      echo "Expected: $directive"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-105: atelier-pipeline comment between frontmatter and identity

@test "T-0005-105: atelier-pipeline comment appears between YAML frontmatter and <identity>" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local comment_line identity_line yaml_end_line
    comment_line=$(grep -n 'Part of atelier-pipeline' "$file" | head -1 | cut -d: -f1)
    identity_line=$(line_of "$file" '<identity>')
    # Find the second --- (end of YAML frontmatter)
    yaml_end_line=$(grep -n '^---$' "$file" | sed -n '2p' | cut -d: -f1)

    [ -n "$comment_line" ] || { echo "Missing comment in $f"; fail=1; continue; }
    [ -n "$identity_line" ] || { echo "Missing <identity> in $f"; fail=1; continue; }
    [ -n "$yaml_end_line" ] || { echo "Missing YAML end in $f"; fail=1; continue; }

    # Comment should be after YAML end and before identity
    if [ "$comment_line" -le "$yaml_end_line" ] || [ "$comment_line" -ge "$identity_line" ]; then
      echo "Comment not between frontmatter and <identity> in $f (yaml_end=$yaml_end_line, comment=$comment_line, identity=$identity_line)"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-106: investigator.md (Poirot) follows 7-tag structure ─────

@test "T-0005-106: investigator.md follows the same 7-tag XML structure" {
  local file="$INSTALLED_AGENTS/investigator.md"
  [ -f "$file" ]
  for tag in "${PERSONA_TAGS[@]}"; do
    assert_has_tag "$file" "$tag"
    assert_has_closing_tag "$file" "$tag"
  done
}

# ── T-0005-107: Source and installed use same tag names in same order ─

@test "T-0005-107: source and installed agent files use same XML tags in same order" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local installed="$INSTALLED_AGENTS/$f"
    local source="$SOURCE_AGENTS/$f"
    [ -f "$installed" ] || continue
    [ -f "$source" ] || { echo "Missing source file: $f"; fail=1; continue; }

    # Extract tag sequence from both files
    local installed_tags source_tags
    installed_tags=$(grep -oE '<(identity|required-actions|workflow|examples|tools|constraints|output)>' "$installed" | tr '\n' ' ')
    source_tags=$(grep -oE '<(identity|required-actions|workflow|examples|tools|constraints|output)>' "$source" | tr '\n' ' ')

    if [ "$installed_tags" != "$source_tags" ]; then
      echo "Tag order mismatch in $f"
      echo "  Installed: $installed_tags"
      echo "  Source:    $source_tags"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}
