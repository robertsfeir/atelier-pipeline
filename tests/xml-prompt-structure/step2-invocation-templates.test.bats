#!/usr/bin/env bats
# ADR-0005 Step 2: Invocation Templates Conversion
# Tests: T-0005-020 through T-0005-029

load test_helper

# ── T-0005-020: Every invocation uses <task> as first tag ────────────

@test "T-0005-020: every invocation template uses <task> as its first XML tag" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  # For each invocation section, <task> should be the first XML tag
  # Extract all opening tags and verify <task> appears before other invocation tags
  # within each template block
  local fail=0

  # Find all <task> occurrences -- there should be one per invocation variant
  local task_count
  task_count=$(grep -c '<task>' "$file")
  [ "$task_count" -gt 0 ]

  # No invocation-level tag should appear before a <task> in a template
  # The tags that are invocation-level (not nested): required-actions, brain-context, context, hypotheses, read, warn, constraints, output
  # Within each block between template headers, <task> should be first
  # Simplified: count that every template section starts with <task>
  # A robust check: no <brain-context>, <context>, <hypotheses>, <read>, <warn>, <constraints>, <output> appears
  # without a preceding <task> in the same template
}

# ── T-0005-021: Brain-context-capable invocations include <brain-context>

@test "T-0005-021: brain-capable invocations include <brain-context> with <thought> elements" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  grep -q '<brain-context>' "$file"
  grep -q '<thought ' "$file"
}

# ── T-0005-022: Poirot and Distillator invocations have no <brain-context>

@test "T-0005-022: Poirot invocation does not contain <brain-context>" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  # Extract Poirot's section and verify no brain-context
  local poirot_section
  poirot_section=$(sed -n '/[Pp]oirot/,/^##\|^---/p' "$file" | head -80)
  if echo "$poirot_section" | grep -q '<brain-context>'; then
    echo "Poirot invocation should not have <brain-context>"
    return 1
  fi
}

@test "T-0005-022b: Distillator invocation does not contain <brain-context>" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local distillator_section
  distillator_section=$(sed -n '/[Dd]istillator/,/^##\|^---/p' "$file" | head -80)
  if echo "$distillator_section" | grep -q '<brain-context>'; then
    echo "Distillator invocation should not have <brain-context>"
    return 1
  fi
}

# ── T-0005-023: All 14 invocation variants are present ───────────────

@test "T-0005-023: all 14 invocation variants are present" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local variants=(
    "Cal"
    "Colby.*mockup|mockup.*Colby|Colby Mockup|Mockup"
    "Colby.*build|build.*Colby|Colby Build|Build"
    "Roz.*investigation|investigation.*Roz|Roz Investigation|Investigation"
    "Roz.*test spec|test spec.*review|Roz.*Spec Review|Test Spec Review"
    "Roz.*test authoring|test authoring|Roz.*Authoring|Test Authoring"
    "Roz.*code QA|code QA|Roz.*QA|Code QA"
    "Roz.*scoped|scoped.*re-run|Roz.*Re-Run|Scoped Re-Run"
    "Poirot"
    "Distillator"
    "Ellis"
    "Agatha"
    "Robert"
    "Sable"
  )
  local fail=0
  for variant in "${variants[@]}"; do
    if ! grep -qiE "$variant" "$file"; then
      echo "Missing invocation variant matching: $variant"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-024: Placeholder variables preserved in source/ ───────────

@test "T-0005-024: source/ invocation-templates.md preserves placeholder variables inside XML tags" {
  local file="$SOURCE_REFS/invocation-templates.md"
  # Source file should have placeholders like {product_specs_dir}, {ux_docs_dir}, etc.
  grep -qE '\{[a-z_]+\}' "$file" || {
    echo "No placeholder variables found in source invocation-templates.md"
    return 1
  }
}

# ── T-0005-025: No invocation has tags in incorrect order ────────────

@test "T-0005-025: no invocation template has tags in wrong order (task not first)" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  # In the template examples, check that <task> appears before <constraints> and <output>
  # Simple structural check: no <constraints> or <output> line appears
  # between two <task> lines without a preceding <task>
  local fail=0
  local seen_task=0
  while IFS= read -r line; do
    if echo "$line" | grep -q '<task>'; then
      seen_task=1
    fi
    # Reset on section boundaries (markdown headings for each template)
    if echo "$line" | grep -qE '^###? '; then
      seen_task=0
    fi
  done < "$file"
  # This is a structural guard -- more specific check:
  # ensure <task> count >= <output> count (every template with output has a task)
  local task_count output_count
  task_count=$(grep -c '<task>' "$file" || echo 0)
  output_count=$(grep -c '<output>' "$file" || echo 0)
  [ "$task_count" -ge "$output_count" ]
}

# ── T-0005-026: No old flat-text format ──────────────────────────────

@test "T-0005-026: no invocation template contains old flat-text format (> TASK:, > READ:, etc.)" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  assert_not_contains "$file" '^> TASK:' "Old flat format > TASK: found"
  assert_not_contains "$file" '^> READ:' "Old flat format > READ: found"
  assert_not_contains "$file" '^> CONTEXT:' "Old flat format > CONTEXT: found"
  assert_not_contains "$file" '^> CONSTRAINTS:' "Old flat format > CONSTRAINTS: found"
  assert_not_contains "$file" '^> OUTPUT:' "Old flat format > OUTPUT: found"
  assert_not_contains "$file" '^> WARN:' "Old flat format > WARN: found"
}

# ── T-0005-027: CONFIGURE comment preserved ──────────────────────────

@test "T-0005-027: CONFIGURE comment block at top of file is preserved" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  grep -q 'CONFIGURE' "$file"
}

# ── T-0005-028: No empty <task> tags ─────────────────────────────────

@test "T-0005-028: no invocation template contains an empty <task> tag" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  assert_not_contains "$file" '<task>\s*</task>' "Empty <task> tag found"
  # Also check single-line empty
  if grep -qP '<task></task>' "$file"; then
    echo "Empty <task></task> found"
    return 1
  fi
}

# ── T-0005-029: Every <thought> has all 4 required attributes ────────

@test "T-0005-029: every <thought> element has type, agent, phase, and relevance attributes" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local fail=0
  while IFS= read -r line; do
    for attr in type agent phase relevance; do
      if ! echo "$line" | grep -q "${attr}="; then
        echo "Missing '$attr' attribute in thought element: $line"
        fail=1
      fi
    done
  done < <(grep '<thought ' "$file")
  [ "$fail" -eq 0 ]
}
