#!/bin/bash
# Shared test helper for ADR-0005 XML prompt structure tests.
# Provides path constants and structural assertion helpers.
# Compatible with bash 3.x (macOS default).

# Absolute paths to the two file trees
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"
INSTALLED_AGENTS="$PROJECT_ROOT/.claude/agents"
SOURCE_AGENTS="$PROJECT_ROOT/source/agents"
INSTALLED_COMMANDS="$PROJECT_ROOT/.claude/commands"
SOURCE_COMMANDS="$PROJECT_ROOT/source/commands"
INSTALLED_REFS="$PROJECT_ROOT/.claude/references"
SOURCE_REFS="$PROJECT_ROOT/source/references"
INSTALLED_RULES="$PROJECT_ROOT/.claude/rules"
SOURCE_RULES="$PROJECT_ROOT/source/rules"
INSTALLED_HOOKS="$PROJECT_ROOT/.claude/hooks"
SOURCE_HOOKS="$PROJECT_ROOT/source/hooks"

# All 9 agent file basenames
AGENT_FILES=(cal.md colby.md roz.md agatha.md ellis.md robert.md sable.md investigator.md distillator.md)

# All 7 command file basenames
COMMAND_FILES=(pm.md ux.md docs.md architect.md debug.md pipeline.md devops.md)

# Brain-context-capable agents (receive brain context in invocations)
BRAIN_AGENTS=(cal colby roz agatha robert sable ellis)

# Agents without brain context
NO_BRAIN_AGENTS=(investigator distillator)

# The 7 persona tags in required order
PERSONA_TAGS=(identity required-actions workflow examples tools constraints output)

# The skill command tags in required order
SKILL_TAGS=(identity required-actions required-reading behavior output constraints)

# ── Cognitive Directive Lookup (bash 3.x compatible) ──────────────────

# Returns the cognitive directive for a given agent or skill command name.
# Usage: directive=$(get_cognitive_directive "cal")
get_cognitive_directive() {
  local name="$1"
  case "$name" in
    cal|architect)   echo "Never design against assumed codebase structure." ;;
    colby)           echo "Never assume code structure from the ADR alone." ;;
    roz|debug)       echo "Never flag a violation based on the diff alone." ;;
    agatha|docs)     echo "Never document behavior from the spec alone." ;;
    robert|pm)       echo "Never accept or reject based on spec text alone." ;;
    sable|ux)        echo "Never accept or reject based on the UX doc alone." ;;
    ellis)           echo "Never write a commit message from the task description alone." ;;
    investigator)    echo "Never flag findings without verifying them against the codebase." ;;
    distillator)     echo "Never compress content you haven't fully read." ;;
    pipeline)        echo "Never route work or form hypotheses without reading the relevant code first." ;;
    devops)          echo "Never diagnose infrastructure issues from logs alone." ;;
    *)               echo "" ;;
  esac
}

# ── Helpers ───────────────────────────────────────────────────────────

# Assert a file contains a tag (opening)
assert_has_tag() {
  local file="$1" tag="$2"
  grep -q "<${tag}>" "$file" || {
    echo "Missing <${tag}> in $file"
    return 1
  }
}

# Assert a file contains a closing tag
assert_has_closing_tag() {
  local file="$1" tag="$2"
  grep -q "</${tag}>" "$file" || {
    echo "Missing </${tag}> in $file"
    return 1
  }
}

# Assert a file does NOT contain a pattern
assert_not_contains() {
  local file="$1" pattern="$2" msg="${3:-}"
  if grep -qE "$pattern" "$file"; then
    echo "${msg:-Found forbidden pattern '$pattern' in $file}"
    grep -nE "$pattern" "$file" | head -5
    return 1
  fi
}

# Get line number of a pattern in a file
line_of() {
  local file="$1" pattern="$2"
  grep -n "$pattern" "$file" | head -1 | cut -d: -f1
}

# Assert tag A appears before tag B in a file
assert_tag_order() {
  local file="$1" tag_a="$2" tag_b="$3"
  local line_a line_b
  line_a=$(line_of "$file" "<${tag_a}>")
  line_b=$(line_of "$file" "<${tag_b}>")
  if [ -z "$line_a" ] || [ -z "$line_b" ]; then
    echo "Cannot verify order: <${tag_a}> (line $line_a) vs <${tag_b}> (line $line_b) in $file"
    return 1
  fi
  if [ "$line_a" -ge "$line_b" ]; then
    echo "Tag order violation in $file: <${tag_a}> (line $line_a) should come before <${tag_b}> (line $line_b)"
    return 1
  fi
}

# Extract content between two tags (inclusive) from a file
extract_tag_content() {
  local file="$1" tag="$2"
  sed -n "/<${tag}>/,/<\/${tag}>/p" "$file"
}

# Count occurrences of a pattern in a file
count_matches() {
  local file="$1" pattern="$2"
  grep -cE "$pattern" "$file" 2>/dev/null || echo 0
}
