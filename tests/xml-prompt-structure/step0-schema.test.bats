#!/usr/bin/env bats
# ADR-0005 Step 0: XML Tag Vocabulary Reference
# Tests: T-0005-001 through T-0005-006

load test_helper

# ── T-0005-001: Schema file exists in both trees ─────────────────────

@test "T-0005-001: xml-prompt-schema.md exists in both source/references/ and .claude/references/" {
  [ -f "$SOURCE_REFS/xml-prompt-schema.md" ]
  [ -f "$INSTALLED_REFS/xml-prompt-schema.md" ]
}

# ── T-0005-002: Every tag name used in Steps 1-8 is defined ─────────

@test "T-0005-002: schema defines all persona file tags" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  for tag in identity required-actions workflow examples tools constraints output; do
    grep -q "<${tag}>" "$schema" || grep -q "\`<${tag}>\`" "$schema" || grep -q "\`${tag}\`" "$schema" || {
      echo "Tag '${tag}' not defined in schema"
      return 1
    }
  done
}

@test "T-0005-002b: schema defines all invocation tags" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  for tag in task brain-context context hypotheses read warn; do
    grep -q "<${tag}>" "$schema" || grep -q "\`<${tag}>\`" "$schema" || grep -q "\`${tag}\`" "$schema" || {
      echo "Tag '${tag}' not defined in schema"
      return 1
    }
  done
}

@test "T-0005-002c: schema defines all retro-lessons tags" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  for tag in retro-lessons lesson what-happened root-cause rules rule; do
    grep -q "<${tag}>" "$schema" || grep -q "\`<${tag}>\`" "$schema" || grep -q "\`${tag}\`" "$schema" || {
      echo "Tag '${tag}' not defined in schema"
      return 1
    }
  done
}

@test "T-0005-002d: schema defines skill command tags" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  for tag in required-reading behavior; do
    grep -q "<${tag}>" "$schema" || grep -q "\`<${tag}>\`" "$schema" || grep -q "\`${tag}\`" "$schema" || {
      echo "Tag '${tag}' not defined in schema"
      return 1
    }
  done
}

@test "T-0005-002e: schema defines brain-context thought tag" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  grep -q "thought" "$schema"
}

# ── T-0005-003: Schema defines valid values for every attribute ──────

@test "T-0005-003: schema defines thought tag type attribute values" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  for value in decision pattern lesson correction drift insight handoff rejection preference; do
    grep -q "$value" "$schema" || {
      echo "Thought type value '$value' not defined in schema"
      return 1
    }
  done
}

@test "T-0005-003b: schema defines thought tag phase attribute values" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  for value in design build qa review reconciliation retro handoff; do
    grep -q "$value" "$schema" || {
      echo "Phase value '$value' not defined in schema"
      return 1
    }
  done
}

@test "T-0005-003c: schema defines lesson tag attributes (id, agents)" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  grep -q '\bid\b' "$schema"
  grep -q '\bagents\b' "$schema"
}

@test "T-0005-003d: schema defines rule tag agent attribute" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  grep -qE 'rule.*agent|agent.*rule' "$schema"
}

@test "T-0005-003e: schema defines thought tag relevance attribute" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  grep -qE "relevance" "$schema"
}

# ── T-0005-004: No undocumented tags in converted files ──────────────

@test "T-0005-004: no XML tags in agent files that are not in the schema" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  local fail=0
  for f in "${AGENT_FILES[@]}"; do
    local file="$INSTALLED_AGENTS/$f"
    [ -f "$file" ] || continue
    # Extract all opening tag names (lowercase, with hyphens)
    while IFS= read -r tag; do
      if ! grep -qE "(${tag})" "$schema" && \
         ! grep -q "\`<${tag}>\`" "$schema" && \
         ! grep -q "<${tag}>" "$schema"; then
        echo "Undocumented tag <${tag}> in $file"
        fail=1
      fi
    done < <(grep -oE '<[a-z][a-z-]*>' "$file" | sed 's/[<>]//g' | sort -u)
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-005: Schema specifies tag ordering rules ──────────────────

@test "T-0005-005: schema documents tag ordering for persona files" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  # Schema must discuss ordering and list identity as first
  grep -qi "order" "$schema"
  grep -qE "identity.*first|first.*identity|identity.*required-actions" "$schema"
}

@test "T-0005-005b: schema documents tag ordering for invocations (task first)" {
  local schema="$INSTALLED_REFS/xml-prompt-schema.md"
  grep -qE "task.*first|first.*task" "$schema" || grep -q "<task>" "$schema"
}

# ── T-0005-006: Every schema tag appears in at least one converted file

@test "T-0005-006: every persona tag from schema is used in at least one agent file" {
  for tag in identity required-actions workflow examples tools constraints output; do
    local found=0
    for f in "${AGENT_FILES[@]}"; do
      if [ -f "$INSTALLED_AGENTS/$f" ] && grep -q "<${tag}>" "$INSTALLED_AGENTS/$f"; then
        found=1
        break
      fi
    done
    [ "$found" -eq 1 ] || {
      echo "Schema tag <${tag}> not used in any agent file"
      return 1
    }
  done
}

@test "T-0005-006b: retro-lessons tags are used in retro-lessons.md" {
  local file="$INSTALLED_REFS/retro-lessons.md"
  for tag in retro-lessons lesson what-happened root-cause rules rule; do
    grep -q "<${tag}" "$file" || {
      echo "Schema tag <${tag}> not used in retro-lessons.md"
      return 1
    }
  done
}
