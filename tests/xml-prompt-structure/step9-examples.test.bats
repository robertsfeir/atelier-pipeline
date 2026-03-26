#!/usr/bin/env bats
# ADR-0005 Step 9: Agent Examples
# Tests: T-0005-130 through T-0005-145
# (T-0005-139 is in step5 since it tests skill commands)

load test_helper

# ── T-0005-130: All 9 agent files contain <examples> tag ────────────

@test "T-0005-130: all 9 agent files contain an <examples> tag" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || { echo "Missing: $file"; fail=1; continue; }
    assert_has_tag "$file" "examples" || fail=1
    assert_has_closing_tag "$file" "examples" || fail=1
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-131: <examples> appears between <workflow> and <tools> ────

@test "T-0005-131: <examples> tag appears between </workflow> and <tools>" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local workflow_end examples_start examples_end tools_start
    workflow_end=$(line_of "$file" '</workflow>')
    examples_start=$(line_of "$file" '<examples>')
    examples_end=$(line_of "$file" '</examples>')
    tools_start=$(line_of "$file" '<tools>')

    [ -n "$workflow_end" ] && [ -n "$examples_start" ] && [ -n "$examples_end" ] && [ -n "$tools_start" ] || {
      echo "Missing tags in $f for order check"
      fail=1
      continue
    }

    if [ "$workflow_end" -ge "$examples_start" ]; then
      echo "In $f: </workflow> (line $workflow_end) should come before <examples> (line $examples_start)"
      fail=1
    fi
    if [ "$examples_end" -ge "$tools_start" ]; then
      echo "In $f: </examples> (line $examples_end) should come before <tools> (line $tools_start)"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-132: At least 2 examples per agent ───────────────────────

@test "T-0005-132: every agent has at least 2 examples (bold-prefixed scenario headers)" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")
    local example_count
    example_count=$(echo "$examples_content" | grep -cE '^\s*\*\*' || echo 0)
    if [ "$example_count" -lt 2 ]; then
      echo "Only $example_count examples in $f (need at least 2)"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-133: No more than 3 examples per agent ───────────────────

@test "T-0005-133: no agent has more than 3 examples" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")
    local example_count
    example_count=$(echo "$examples_content" | grep -cE '^\s*\*\*' || echo 0)
    if [ "$example_count" -gt 3 ]; then
      echo "Too many examples ($example_count) in $f (max 3)"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-134: Brain-capable agents reference brain context in examples

@test "T-0005-134: brain-capable agents include brain context reference in examples" {
  local fail=0
  for agent in "${BRAIN_AGENTS[@]}"; do
    local f="${agent}.md"
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")
    echo "$examples_content" | grep -qiE "brain.context|brain context|prior.*decision|injected.*thought|prior.*pattern|brain-context" || {
      echo "Missing brain context reference in examples of $f"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-135: Poirot and Distillator examples have no brain refs ───

@test "T-0005-135: investigator and distillator examples do not reference brain context" {
  local fail=0
  for agent in "${NO_BRAIN_AGENTS[@]}"; do
    local f="${agent}.md"
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")
    if echo "$examples_content" | grep -qiE "brain.context|brain context|brain-context|injected.*thought"; then
      echo "Found brain context reference in examples of $f (should not have one)"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-136: Source template files contain <examples> ─────────────

@test "T-0005-136: source agent templates contain <examples> tags" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$SOURCE_AGENTS/$f"
    [ -f "$file" ] || continue
    assert_has_tag "$file" "examples" || fail=1
    assert_has_closing_tag "$file" "examples" || fail=1
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-137: No intensity markers in examples ────────────────────

@test "T-0005-137: no <examples> tag contains MUST/CRITICAL/NEVER" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")
    for marker in MUST CRITICAL NEVER; do
      if echo "$examples_content" | grep -qE "\b${marker}\b"; then
        echo "Found intensity marker '$marker' in examples of $f"
        fail=1
      fi
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-138: No imperative instructions in examples ──────────────

@test "T-0005-138: no <examples> tag contains imperative instructions" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")
    # Check for imperative voice patterns (excluding bold headers which may start with verbs)
    # Look for lines starting with "You must", "Always ", "Never " (imperative, not narration)
    if echo "$examples_content" | grep -qE '^\s*You must\b|^\s*Always\s|^\s*Never\s'; then
      echo "Found imperative instruction in examples of $f"
      echo "$examples_content" | grep -E '^\s*You must\b|^\s*Always\s|^\s*Never\s' | head -3
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-140: No example scenario exceeds 5 lines ─────────────────

@test "T-0005-140: no example scenario exceeds 5 content lines" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")

    # Split by bold headers and count lines in each scenario
    local current_lines=0
    local in_scenario=0
    local scenario_header=""
    while IFS= read -r line; do
      if echo "$line" | grep -qE '^\s*\*\*'; then
        # New scenario header
        if [ "$in_scenario" -eq 1 ] && [ "$current_lines" -gt 5 ]; then
          echo "Example '$scenario_header' in $f has $current_lines lines (max 5)"
          fail=1
        fi
        scenario_header="$line"
        current_lines=0
        in_scenario=1
      elif [ "$in_scenario" -eq 1 ]; then
        # Count non-empty lines as content
        if echo "$line" | grep -qvE '^\s*$|</?examples>'; then
          current_lines=$((current_lines + 1))
        fi
      fi
    done <<< "$examples_content"
    # Check last scenario
    if [ "$in_scenario" -eq 1 ] && [ "$current_lines" -gt 5 ]; then
      echo "Example '$scenario_header' in $f has $current_lines lines (max 5)"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-141: Examples demonstrate cognitive directive behavior ────

@test "T-0005-141: every example demonstrates cognitive directive behavior (tool usage)" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")
    # Every example should involve a tool action (Read, Grep, Glob, etc.)
    # that demonstrates the "investigate before acting" directive
    echo "$examples_content" | grep -qiE "Read|Grep|Glob|Bash|Write|Edit|grep|read|check|verify" || {
      echo "No tool usage found in examples of $f"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-142: No empty <examples> tags ─────────────────────────────

@test "T-0005-142: no agent has an empty <examples> tag" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")
    local content_lines
    content_lines=$(echo "$examples_content" | grep -cvE '^\s*$|</?examples>' || echo 0)
    if [ "$content_lines" -lt 2 ]; then
      echo "Empty or near-empty <examples> in $f ($content_lines content lines)"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-143: Source and installed have <examples> in same position ─

@test "T-0005-143: source and installed files both have <examples> in same tag order" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local installed="$INSTALLED_AGENTS/$f"
    local source="$SOURCE_AGENTS/$f"
    [ -f "$installed" ] && [ -f "$source" ] || continue

    # Both should have examples between workflow and tools
    for file in "$installed" "$source"; do
      local workflow_end examples_start tools_start
      workflow_end=$(line_of "$file" '</workflow>')
      examples_start=$(line_of "$file" '<examples>')
      tools_start=$(line_of "$file" '<tools>')
      if [ -z "$examples_start" ]; then
        echo "Missing <examples> in $file"
        fail=1
      elif [ -n "$workflow_end" ] && [ "$workflow_end" -ge "$examples_start" ]; then
        echo "<examples> not after </workflow> in $file"
        fail=1
      elif [ -n "$tools_start" ] && [ "$examples_start" -ge "$tools_start" ]; then
        echo "<examples> not before <tools> in $file"
        fail=1
      fi
    done
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-144: Each example shows concrete tool usage ───────────────

@test "T-0005-144: each example mentions a concrete tool name" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")

    # Check each scenario block for at least one tool reference
    local in_scenario=0
    local scenario_has_tool=0
    local scenario_header=""
    while IFS= read -r line; do
      if echo "$line" | grep -qE '^\s*\*\*'; then
        if [ "$in_scenario" -eq 1 ] && [ "$scenario_has_tool" -eq 0 ]; then
          echo "Example '$scenario_header' in $f has no tool reference"
          fail=1
        fi
        scenario_header="$line"
        in_scenario=1
        scenario_has_tool=0
      elif [ "$in_scenario" -eq 1 ]; then
        if echo "$line" | grep -qiE '\bRead\b|\bGrep\b|\bGlob\b|\bBash\b|\bWrite\b|\bEdit\b|git diff|git log'; then
          scenario_has_tool=1
        fi
      fi
    done <<< "$examples_content"
    # Check last scenario
    if [ "$in_scenario" -eq 1 ] && [ "$scenario_has_tool" -eq 0 ]; then
      echo "Example '$scenario_header' in $f has no tool reference"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-145: Examples do not duplicate workflow or directive text ──

@test "T-0005-145: examples do not restate cognitive directive text verbatim" {
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    local agent_name="${f%.md}"
    local directive="$(get_cognitive_directive "$agent_name")"
    [ -z "$directive" ] && continue

    local examples_content
    examples_content=$(extract_tag_content "$file" "examples")
    if echo "$examples_content" | grep -qF "$directive"; then
      echo "Examples in $f restate cognitive directive verbatim"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}
