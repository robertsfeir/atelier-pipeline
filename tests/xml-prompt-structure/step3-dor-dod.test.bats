#!/usr/bin/env bats
# ADR-0005 Step 3: DoR/DoD Reference Conversion
# Tests: T-0005-030 through T-0005-035

load test_helper

# ── T-0005-030: dor-dod.md references <output> tag ──────────────────

@test "T-0005-030: dor-dod.md references the <output> tag as container for DoR/DoD" {
  local file="$INSTALLED_REFS/dor-dod.md"
  grep -qE '<output>|`<output>`' "$file"
}

# ── T-0005-031: DoR first, DoD last in output template ───────────────

@test "T-0005-031: example output templates show DoR as first content and DoD as last" {
  local file="$INSTALLED_REFS/dor-dod.md"
  # DoR should appear before DoD in the file's template examples
  local dor_line dod_line
  dor_line=$(grep -n 'DoR' "$file" | head -1 | cut -d: -f1)
  dod_line=$(grep -n 'DoD' "$file" | tail -1 | cut -d: -f1)
  [ -n "$dor_line" ]
  [ -n "$dod_line" ]
  [ "$dor_line" -lt "$dod_line" ]
}

# ── T-0005-032: All existing DoR/DoD field definitions preserved ────

@test "T-0005-032: existing DoR/DoD field definitions are preserved" {
  local file="$INSTALLED_REFS/dor-dod.md"
  # Key field names that must survive conversion
  for field in "Retro risks" "Source citations" "Status"; do
    grep -qi "$field" "$file" || {
      echo "Missing field definition: $field"
      return 1
    }
  done
}

# ── T-0005-033: DoR template not outside <output> context ────────────

@test "T-0005-033: dor-dod.md positions DoR/DoD within <output> context guidance" {
  local file="$INSTALLED_REFS/dor-dod.md"
  # The file should reference <output> as the container
  grep -qE '<output>|`<output>`|output.*tag' "$file"
}

# ── T-0005-034: No original field definition is missing ──────────────

@test "T-0005-034: no original DoR/DoD field definition is missing in converted version" {
  local file="$INSTALLED_REFS/dor-dod.md"
  # Core fields from original DoR/DoD framework
  local fields=("Requirements" "DoR" "DoD" "Verification" "Deferred")
  for field in "${fields[@]}"; do
    grep -qi "$field" "$file" || {
      echo "Missing field: $field"
      return 1
    }
  done
}

# ── T-0005-035: No standalone ## DoR/## DoD headings at top level ────

@test "T-0005-035: no standalone ## DoR or ## DoD as top-level document headings" {
  local file="$INSTALLED_REFS/dor-dod.md"
  # These headings should be inside <output> examples or code blocks, not as
  # top-level document structure. Check for lines starting with ## DoR or ## DoD
  # that are NOT inside a code block (``` ... ```)
  local in_code=0 fail=0
  while IFS= read -r line; do
    if echo "$line" | grep -qE '^\s*```'; then
      in_code=$((1 - in_code))
    fi
    if [ "$in_code" -eq 0 ] && echo "$line" | grep -qE '^## DoR\b|^## DoD\b'; then
      echo "Found top-level heading outside code block: $line"
      fail=1
    fi
  done < "$file"
  [ "$fail" -eq 0 ]
}

# ── Source/installed sync ────────────────────────────────────────────

@test "T-0005-030b: source dor-dod.md also references <output> tag" {
  local file="$SOURCE_REFS/dor-dod.md"
  grep -qE '<output>|`<output>`' "$file"
}
