#!/usr/bin/env bats
# ADR-0005 Step 8: Pipeline Operations Reference Update
# Tests: T-0005-090 through T-0005-095

load test_helper

# ── T-0005-090: pipeline-operations.md references XML invocation format

@test "T-0005-090: pipeline-operations.md references XML invocation format" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  grep -qE '<task>|<constraints>|<output>|XML.*invocation|invocation.*XML|XML.*tag' "$file"
}

# ── T-0005-091: Brain prefetch documented as Eva's responsibility ────

@test "T-0005-091: brain prefetch documented as Eva's responsibility" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  grep -qiE "Eva.*brain|brain.*prefetch|pre.?fetch|Eva.*inject|brain-context" "$file"
}

# ── T-0005-092: All named sections preserved ─────────────────────────

@test "T-0005-092: pipeline-operations.md preserves all named sections" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  local sections=("Continuous QA" "Feedback Loop" "Batch Mode" "Worktree" "Triage")
  local fail=0
  for section in "${sections[@]}"; do
    grep -qi "$section" "$file" || {
      echo "Missing section: $section"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0005-093: No old flat-text invocation format markers ───────────

@test "T-0005-093: pipeline-operations.md does not contain old flat-text format markers" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  # Check for old-style markers used as format elements (not in prose discussion)
  for marker in "TASK:" "READ:" "CONTEXT:"; do
    if grep -qE "^\s*${marker}" "$file"; then
      echo "Old flat marker '$marker' found as format element"
      return 1
    fi
  done
}

# ── T-0005-094: Brain prefetch documented in invocation preparation ──

@test "T-0005-094: brain prefetch or brain-context documented in invocation area" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  grep -qiE "prefetch|pre-fetch|brain-context|brain context.*inject" "$file"
}

# ── T-0005-095: No phrasing assigning brain calls to agents ──────────

@test "T-0005-095: no phrasing assigning brain tool calls to agents instead of Eva" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  assert_not_contains "$file" 'agent calls agent_search' "Found agent-initiated brain call phrasing"
  assert_not_contains "$file" 'agent calls agent_capture' "Found agent-initiated brain capture phrasing"
}

# ── Source sync ──────────────────────────────────────────────────────

@test "T-0005-090b: source pipeline-operations.md also references XML format" {
  local file="$SOURCE_REFS/pipeline-operations.md"
  grep -qE '<task>|<constraints>|<output>|XML.*invocation|invocation.*XML|XML.*tag' "$file"
}
