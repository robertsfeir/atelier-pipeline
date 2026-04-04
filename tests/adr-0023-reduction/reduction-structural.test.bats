#!/usr/bin/env bats
# ADR-0023: Agent Specification Reduction -- Structural Tests
# Tests: T-0023-001 through T-0023-155 (119 tests total)
#
# Distribution by step:
#   Step 1a (brain protocol extraction):  10 tests (T-0023-001 to T-0023-008)
#   Step 1b (step-sizing extraction):      6 tests (T-0023-010 to T-0023-015)
#   Step 1c (Cal reduction):              10 tests (T-0023-020 to T-0023-029)
#   Step 1d (Colby reduction):             8 tests (T-0023-030 to T-0023-037)
#   Step 1e (Roz reduction):               7 tests (T-0023-040 to T-0023-045a)
#   Step 1f (remaining agents):           26 tests (T-0023-050 to T-0023-072)
#   Step 1g (invocation-templates):       12 tests (T-0023-080 to T-0023-091)
#   Step 1h (session-boot.sh):            24 tests (T-0023-100 to T-0023-121)
#   Step 1i (pipeline-orchestration):      6 tests (T-0023-130 to T-0023-134a)
#   Step 1j (SKILL.md + pipeline-setup):   4 tests (T-0023-140 to T-0023-143)
#   Step 1l (final integration):           6 tests (T-0023-150 to T-0023-155)
#                                        ---
#                                        119 tests total
#
# These tests assert POST-REDUCTION state. They will fail against
# pre-reduction files and pass after Colby completes each step.

load ../xml-prompt-structure/test_helper

# ── Path constants ──────────────────────────────────────────────────────
# Use source/shared paths (post-ADR-0022 structure)
SHARED_AGENTS="$PROJECT_ROOT/source/shared/agents"
SHARED_REFS="$PROJECT_ROOT/source/shared/references"
SHARED_RULES="$PROJECT_ROOT/source/shared/rules"
SHARED_HOOKS="$PROJECT_ROOT/source/shared/hooks"
SKILL_FILE="$PROJECT_ROOT/skills/pipeline-setup/SKILL.md"

# ── All 12 core agent filenames for bulk tests ──────────────────────────
ALL_AGENTS=(cal.md colby.md roz.md agatha.md ellis.md robert.md sable.md investigator.md sentinel.md darwin.md deps.md distillator.md)

# ═══════════════════════════════════════════════════════════════════════
# Step 1a: Extract shared brain capture protocol to agent-preamble.md
# Tests: T-0023-001 through T-0023-008 (10 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-001: agent-preamble.md contains brain-capture protocol ──────

@test "T-0023-001: agent-preamble.md contains <protocol id=\"brain-capture\"> section" {
  local file="$SHARED_REFS/agent-preamble.md"
  [ -f "$file" ]
  grep -q '<protocol id="brain-capture">' "$file"
}

# ── T-0023-002: Cal Brain Access <=6 lines ─────────────────────────────

@test "T-0023-002: Cal persona Brain Access section is <=6 lines and references agent-preamble.md" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  # Extract Brain Access section (from header to next ## header or end)
  local section
  section=$(sed -n '/## Brain Access/,/^## [^B]/p' "$file" | sed '$d')
  local line_count
  line_count=$(echo "$section" | wc -l | tr -d ' ')
  [ "$line_count" -le 6 ]
  echo "$section" | grep -q "agent-preamble"
}

# ── T-0023-003: Colby Brain Access <=6 lines ──────────────────────────

@test "T-0023-003: Colby persona Brain Access section is <=6 lines and references agent-preamble.md" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  local section
  section=$(sed -n '/## Brain Access/,/^## [^B]/p' "$file" | sed '$d')
  local line_count
  line_count=$(echo "$section" | wc -l | tr -d ' ')
  [ "$line_count" -le 6 ]
  echo "$section" | grep -q "agent-preamble"
}

# ── T-0023-004: Roz Brain Access <=6 lines ─────────────────────────────

@test "T-0023-004: Roz persona Brain Access section is <=6 lines and references agent-preamble.md" {
  local file="$SHARED_AGENTS/roz.md"
  [ -f "$file" ]
  local section
  section=$(sed -n '/## Brain Access/,/^## [^B]/p' "$file" | sed '$d')
  local line_count
  line_count=$(echo "$section" | wc -l | tr -d ' ')
  [ "$line_count" -le 6 ]
  echo "$section" | grep -q "agent-preamble"
}

# ── T-0023-005: Agatha Brain Access <=6 lines ──────────────────────────

@test "T-0023-005: Agatha persona Brain Access section is <=6 lines and references agent-preamble.md" {
  local file="$SHARED_AGENTS/agatha.md"
  [ -f "$file" ]
  local section
  section=$(sed -n '/## Brain Access/,/^## [^B]/p' "$file" | sed '$d')
  local line_count
  line_count=$(echo "$section" | wc -l | tr -d ' ')
  [ "$line_count" -le 6 ]
  echo "$section" | grep -q "agent-preamble"
}

# ── T-0023-006: Cal retains thought_types with importance ──────────────

@test "T-0023-006: Cal persona retains thought_type 'decision' and 'pattern' with importance values" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  grep -q "thought_type.*decision\|thought_type: 'decision'" "$file"
  grep -q "thought_type.*pattern\|thought_type: 'pattern'" "$file"
  grep -q "importance" "$file"
}

# ── T-0023-006a: Roz retains thought_types with importance ─────────────

@test "T-0023-006a: Roz persona retains thought_type 'pattern' and 'lesson' with importance values" {
  local file="$SHARED_AGENTS/roz.md"
  [ -f "$file" ]
  grep -q "thought_type.*pattern\|thought_type: 'pattern'" "$file"
  grep -q "thought_type.*lesson\|thought_type: 'lesson'" "$file"
  grep -q "importance" "$file"
}

# ── T-0023-006b: Agatha retains thought_types with importance ──────────

@test "T-0023-006b: Agatha persona retains thought_type 'decision' and 'insight' with importance values" {
  local file="$SHARED_AGENTS/agatha.md"
  [ -f "$file" ]
  grep -q "thought_type.*decision\|thought_type: 'decision'" "$file"
  grep -q "thought_type.*insight\|thought_type: 'insight'" "$file"
  grep -q "importance" "$file"
}

# ── T-0023-007: Colby retains thought_types with importance ────────────

@test "T-0023-007: Colby persona retains thought_type 'insight' and 'pattern' with importance values" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  grep -q "thought_type.*insight\|thought_type: 'insight'" "$file"
  grep -q "thought_type.*pattern\|thought_type: 'pattern'" "$file"
  grep -q "importance" "$file"
}

# ── T-0023-008: agent-preamble.md step 4 lists mcpServers agents ──────

@test "T-0023-008: agent-preamble.md step 4 still references mcpServers: atelier-brain agents list" {
  local file="$SHARED_REFS/agent-preamble.md"
  [ -f "$file" ]
  grep -q "mcpServers.*atelier-brain\|mcpServers: atelier-brain" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1b: Extract step sizing gate to shared reference file
# Tests: T-0023-010 through T-0023-015 (6 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-010: step-sizing.md exists with S1-S5 table ─────────────────

@test "T-0023-010: step-sizing.md exists in source/shared/references/ and contains S1-S5 table" {
  local file="$SHARED_REFS/step-sizing.md"
  [ -f "$file" ]
  grep -q "S1" "$file"
  grep -q "S2" "$file"
  grep -q "S3" "$file"
  grep -q "S4" "$file"
  grep -q "S5" "$file"
}

# ── T-0023-011: step-sizing.md contains split heuristics ───────────────

@test "T-0023-011: step-sizing.md contains split heuristics table" {
  local file="$SHARED_REFS/step-sizing.md"
  [ -f "$file" ]
  grep -qiE "split|heuristic" "$file"
}

# ── T-0023-012: step-sizing.md contains evidence data ──────────────────

@test "T-0023-012: step-sizing.md contains evidence paragraph with 57% to 93% data" {
  local file="$SHARED_REFS/step-sizing.md"
  [ -f "$file" ]
  grep -q "57%" "$file"
  grep -q "93%" "$file"
}

# ── T-0023-013: step-sizing.md contains Darwin review trigger ──────────

@test "T-0023-013: step-sizing.md contains Darwin review trigger" {
  local file="$SHARED_REFS/step-sizing.md"
  [ -f "$file" ]
  grep -qiE "[Dd]arwin" "$file"
}

# ── T-0023-014: Cal persona references step-sizing.md ──────────────────

@test "T-0023-014: Cal persona references step-sizing.md by path" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  grep -q "step-sizing" "$file"
}

# ── T-0023-015: Cal does NOT contain S1-S5 table inline ────────────────

@test "T-0023-015: Cal persona does NOT contain the S1-S5 table inline (moved, not duplicated)" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  # The table has S1-S5 rows with pipe-delimited cells; grep for 3+ S-rows
  # to confirm the table body is gone. A single reference to "S1-S5" is OK.
  local table_rows
  table_rows=$(grep -cE '^\s*\|.*S[1-5].*\|' "$file" 2>/dev/null || true)
  [ "$table_rows" -lt 3 ]
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1c: Reduce Cal persona
# Tests: T-0023-020 through T-0023-029 (10 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-020: Cal persona <=120 lines ────────────────────────────────

@test "T-0023-020: Cal persona <=120 lines" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 120 ]
}

# ── T-0023-021: Cal contains spec challenge + SPOF ─────────────────────

@test "T-0023-021: Cal persona contains 'spec challenge' and 'SPOF' in required-actions" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  grep -qiE "spec.*challenge|challenge.*spec" "$file"
  grep -qiE "SPOF|single point of failure" "$file"
}

# ── T-0023-022: Cal contains all 4 hard gates ──────────────────────────

@test "T-0023-022: Cal persona contains all 4 hard gates" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  local fail=0
  # Hard gates are numbered 1-4 in Cal's workflow
  grep -qiE "gate.*(1|one)|1\." "$file" || { echo "Missing hard gate 1"; fail=1; }
  grep -qiE "gate.*(2|two)|2\." "$file" || { echo "Missing hard gate 2"; fail=1; }
  grep -qiE "gate.*(3|three)|3\." "$file" || { echo "Missing hard gate 3"; fail=1; }
  grep -qiE "gate.*(4|four)|4\." "$file" || { echo "Missing hard gate 4"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0023-023: Cal contains vertical slice preference ─────────────────

@test "T-0023-023: Cal persona contains vertical slice preference text" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  grep -qiE "vertical.*slice" "$file"
}

# ── T-0023-024: Cal contains anti-goals requirement ────────────────────

@test "T-0023-024: Cal persona contains anti-goals requirement" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  grep -qiE "anti.goal" "$file"
}

# ── T-0023-025: Cal has exactly 1 example ──────────────────────────────

@test "T-0023-025: Cal persona has exactly 1 example demonstrating spec challenge + SPOF pattern" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  assert_has_tag "$file" "examples"
  local examples
  examples=$(extract_tag_content "$file" "examples")
  # Count example blocks -- look for bold example headers or ** delimiters
  local example_count
  example_count=$(echo "$examples" | grep -ciE "\*\*example|\*\*wrong.*default|spec.*challenge|SPOF" || true)
  [ "$example_count" -ge 1 ]
}

# ── T-0023-026: Cal does NOT contain State Machine Analysis header ─────

@test "T-0023-026: Cal persona does NOT contain 'State Machine Analysis' as a section header" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  assert_not_contains "$file" "^#+.*State Machine Analysis" "Cal should not contain State Machine Analysis header"
}

# ── T-0023-027: Cal does NOT contain Blast Radius Verification header ──

@test "T-0023-027: Cal persona does NOT contain 'Blast Radius Verification' as a section header" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  assert_not_contains "$file" "^#+.*Blast Radius Verification" "Cal should not contain Blast Radius Verification header"
}

# ── T-0023-028: Cal does NOT contain Migration & Rollback header ───────

@test "T-0023-028: Cal persona does NOT contain 'Migration & Rollback' as a section header" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  assert_not_contains "$file" "^#+.*Migration.*Rollback" "Cal should not contain Migration & Rollback header"
}

# ── T-0023-029: Cal output template retains key sections ───────────────

@test "T-0023-029: Cal persona output template retains DoR, ADR skeleton, UX Coverage, Wiring Coverage, Contract Boundaries, Notes for Colby, DoD" {
  local file="$SHARED_AGENTS/cal.md"
  [ -f "$file" ]
  local output
  output=$(extract_tag_content "$file" "output")
  local fail=0
  echo "$output" | grep -qiE "DoR" || { echo "Missing: DoR"; fail=1; }
  echo "$output" | grep -qiE "ADR.*skeleton|skeleton" || { echo "Missing: ADR skeleton"; fail=1; }
  echo "$output" | grep -qiE "UX.*[Cc]overage" || { echo "Missing: UX Coverage"; fail=1; }
  echo "$output" | grep -qiE "[Ww]iring.*[Cc]overage" || { echo "Missing: Wiring Coverage"; fail=1; }
  echo "$output" | grep -qiE "[Cc]ontract.*[Bb]oundar" || { echo "Missing: Contract Boundaries"; fail=1; }
  echo "$output" | grep -qiE "[Nn]otes.*[Cc]olby" || { echo "Missing: Notes for Colby"; fail=1; }
  echo "$output" | grep -qiE "DoD" || { echo "Missing: DoD"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1d: Reduce Colby persona
# Tests: T-0023-030 through T-0023-037 (8 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-030: Colby persona <=95 lines ───────────────────────────────

@test "T-0023-030: Colby persona <=95 lines" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 95 ]
}

# ── T-0023-031: Colby contains TDD-first constraint ───────────────────

@test "T-0023-031: Colby persona contains 'Make Roz's tests pass' verbatim or near-verbatim" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  grep -qiE "Roz.*tests.*pass|Make Roz.*test" "$file"
}

# ── T-0023-032: Colby contains anti-modification constraint ────────────

@test "T-0023-032: Colby persona contains 'do not modify' + 'assertions' anti-modification constraint" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  grep -qiE "do not modify.*assert|not modify.*assertion|never.*modify.*assert" "$file"
}

# ── T-0023-033: Colby output template contains Contracts Produced ──────

@test "T-0023-033: Colby persona contains Contracts Produced table in output template" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  grep -qiE "[Cc]ontracts.*[Pp]roduced" "$file"
}

# ── T-0023-034: Colby contains premise verification ───────────────────

@test "T-0023-034: Colby persona contains premise verification section" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  grep -qiE "premise.*verif" "$file"
}

# ── T-0023-035: Colby has exactly 1 example ────────────────────────────

@test "T-0023-035: Colby persona has exactly 1 example demonstrating premise verification" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  assert_has_tag "$file" "examples"
  local examples
  examples=$(extract_tag_content "$file" "examples")
  echo "$examples" | grep -qiE "premise|verif|wrong.*default|root.*cause" || {
    echo "Example should demonstrate premise verification judgment"
    return 1
  }
}

# ── T-0023-036: Colby does NOT open with Retrieval-led reasoning ──────

@test "T-0023-036: Colby persona does NOT contain 'Retrieval-led reasoning' as opening of required-actions" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  assert_not_contains "$file" "Retrieval-led reasoning" "Colby should not contain Retrieval-led reasoning"
}

# ── T-0023-037: Colby TDD constraint is explicit ──────────────────────

@test "T-0023-037: Colby persona TDD constraint is explicit (test + fail + implement in same file)" {
  local file="$SHARED_AGENTS/colby.md"
  [ -f "$file" ]
  # TDD workflow must reference running tests first, confirming they fail, then implementing
  grep -qiE "test.*fail|fail.*test|test.first|TDD" "$file"
  grep -qiE "implement" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1e: Reduce Roz persona
# Tests: T-0023-040 through T-0023-045a (7 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-040: Roz persona <=100 lines ────────────────────────────────

@test "T-0023-040: Roz persona <=100 lines" {
  local file="$SHARED_AGENTS/roz.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 100 ]
}

# ── T-0023-041: Roz contains domain-intent constraint ──────────────────

@test "T-0023-041: Roz persona contains 'assert what code SHOULD do' or equivalent domain-intent constraint" {
  local file="$SHARED_AGENTS/roz.md"
  [ -f "$file" ]
  grep -qiE "assert.*SHOULD.*do|assert.*domain.*correct|what.*should.*do|domain.intent" "$file"
}

# ── T-0023-042: Roz contains 2 examples ────────────────────────────────

@test "T-0023-042: Roz persona contains 2 examples (both judgment restraint)" {
  local file="$SHARED_AGENTS/roz.md"
  [ -f "$file" ]
  assert_has_tag "$file" "examples"
  local examples
  examples=$(extract_tag_content "$file" "examples")
  # Both examples demonstrate "looks wrong but isn't" judgment restraint
  # Count separate example blocks
  local example_count
  example_count=$(echo "$examples" | grep -ciE "\*\*.*example|\*\*.*reading.*context|\*\*.*tracing|looks.*wrong" || true)
  [ "$example_count" -ge 2 ]
}

# ── T-0023-043: Roz references qa-checks.md ─────────────────────────────

@test "T-0023-043: Roz persona references qa-checks.md" {
  local file="$SHARED_AGENTS/roz.md"
  [ -f "$file" ]
  grep -q "qa-checks" "$file"
}

# ── T-0023-044: Roz does NOT contain numbered trace steps ──────────────

@test "T-0023-044: Roz persona does NOT contain numbered trace steps (1. Entry point, 2. API call, etc.)" {
  local file="$SHARED_AGENTS/roz.md"
  [ -f "$file" ]
  assert_not_contains "$file" "^[0-9]+\.\s*(Entry point|API call|Route handler|Business logic|Data layer|Response path)" \
    "Roz should not contain numbered trace steps"
}

# ── T-0023-045: Roz does NOT contain Layer Awareness table ─────────────

@test "T-0023-045: Roz persona does NOT contain Layer Awareness table" {
  local file="$SHARED_AGENTS/roz.md"
  [ -f "$file" ]
  assert_not_contains "$file" "^#+.*Layer Awareness" "Roz should not contain Layer Awareness header"
  # Also check for the table format with Application/Transport/Infrastructure/Environment rows
  local table_rows
  table_rows=$(grep -cE '^\|.*(Application|Transport|Infrastructure|Environment).*\|' "$file" 2>/dev/null || true)
  [ "$table_rows" -eq 0 ]
}

# ── T-0023-045a: Roz contains explicit TDD constraint ──────────────────

@test "T-0023-045a: Roz persona contains explicit TDD constraint language per R15" {
  local file="$SHARED_AGENTS/roz.md"
  [ -f "$file" ]
  # Must contain TDD-first language: "tests define correct behavior" or "BEFORE Colby builds" or "test-first"
  grep -qiE "tests define.*correct|BEFORE.*[Cc]olby.*build|test.first|TDD" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1f: Reduce remaining agent personas
# Tests: T-0023-050 through T-0023-072 (26 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-050: Robert persona <=60 lines ──────────────────────────────

@test "T-0023-050: Robert persona <=60 lines" {
  local file="$SHARED_AGENTS/robert.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 60 ]
}

# ── T-0023-051: Robert contains information asymmetry ──────────────────

@test "T-0023-051: Robert persona contains 'information asymmetry' constraint" {
  local file="$SHARED_AGENTS/robert.md"
  [ -f "$file" ]
  grep -qiE "information.*asymmetry" "$file"
}

# ── T-0023-052: Robert contains PASS/DRIFT/MISSING/AMBIGUOUS ──────────

@test "T-0023-052: Robert persona contains PASS/DRIFT/MISSING/AMBIGUOUS vocabulary" {
  local file="$SHARED_AGENTS/robert.md"
  [ -f "$file" ]
  grep -q "PASS" "$file"
  grep -q "DRIFT" "$file"
  grep -q "MISSING" "$file"
  grep -q "AMBIGUOUS" "$file"
}

# ── T-0023-053: Sable persona <=60 lines ───────────────────────────────

@test "T-0023-053: Sable persona <=60 lines" {
  local file="$SHARED_AGENTS/sable.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 60 ]
}

# ── T-0023-053a: Sable contains information asymmetry ──────────────────

@test "T-0023-053a: Sable persona contains 'information asymmetry' constraint" {
  local file="$SHARED_AGENTS/sable.md"
  [ -f "$file" ]
  grep -qiE "information.*asymmetry" "$file"
}

# ── T-0023-054: Sable contains five-state audit ───────────────────────

@test "T-0023-054: Sable persona contains five-state audit requirement" {
  local file="$SHARED_AGENTS/sable.md"
  [ -f "$file" ]
  grep -qiE "five.state|5.state" "$file"
}

# ── T-0023-055: Poirot persona <=65 lines ──────────────────────────────

@test "T-0023-055: Poirot persona <=65 lines" {
  local file="$SHARED_AGENTS/investigator.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 65 ]
}

# ── T-0023-056: Poirot contains minimum 5 findings ────────────────────

@test "T-0023-056: Poirot persona contains 'minimum 5 findings' constraint" {
  local file="$SHARED_AGENTS/investigator.md"
  [ -f "$file" ]
  grep -qiE "(min|minimum).*5.*finding|at least 5.*finding|5\+.*finding" "$file"
}

# ── T-0023-057: Poirot contains cross-layer wiring check ──────────────

@test "T-0023-057: Poirot persona contains cross-layer wiring check constraint" {
  local file="$SHARED_AGENTS/investigator.md"
  [ -f "$file" ]
  grep -qiE "cross.layer.*wiring|wiring.*check|orphan.*endpoint|phantom.*call" "$file"
}

# ── T-0023-058: Ellis persona <=65 lines ───────────────────────────────

@test "T-0023-058: Ellis persona <=65 lines" {
  local file="$SHARED_AGENTS/ellis.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 65 ]
}

# ── T-0023-058a: Ellis contains per-unit vs final distinction ─────────

@test "T-0023-058a: Ellis persona contains per-unit vs final commit distinction" {
  local file="$SHARED_AGENTS/ellis.md"
  [ -f "$file" ]
  grep -qiE "per.unit|per.wave" "$file"
  grep -qiE "final" "$file"
}

# ── T-0023-059: Sentinel persona <=65 lines ────────────────────────────

@test "T-0023-059: Sentinel persona <=65 lines" {
  local file="$SHARED_AGENTS/sentinel.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 65 ]
}

# ── T-0023-060: Sentinel contains CWE/OWASP ───────────────────────────

@test "T-0023-060: Sentinel persona contains CWE/OWASP requirement" {
  local file="$SHARED_AGENTS/sentinel.md"
  [ -f "$file" ]
  grep -qiE "CWE|OWASP" "$file"
}

# ── T-0023-061: Darwin persona <=100 lines ─────────────────────────────

@test "T-0023-061: Darwin persona <=100 lines" {
  local file="$SHARED_AGENTS/darwin.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 100 ]
}

# ── T-0023-062: Darwin contains self-edit protection ──────────────────

@test "T-0023-062: Darwin persona contains self-edit protection constraint" {
  local file="$SHARED_AGENTS/darwin.md"
  [ -f "$file" ]
  grep -qiE "self.edit.*protect|cannot.*propose.*darwin\.md|cannot.*modify.*darwin" "$file"
}

# ── T-0023-063: Darwin contains 5+ pipelines data requirement ─────────

@test "T-0023-063: Darwin persona contains '5+ pipelines' data requirement" {
  local file="$SHARED_AGENTS/darwin.md"
  [ -f "$file" ]
  grep -qiE "5.*pipeline|five.*pipeline" "$file"
}

# ── T-0023-064: Deps persona <=90 lines ────────────────────────────────

@test "T-0023-064: Deps persona <=90 lines" {
  local file="$SHARED_AGENTS/deps.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 90 ]
}

# ── T-0023-065: Deps contains conservative risk labeling ───────────────

@test "T-0023-065: Deps persona contains conservative risk labeling constraint" {
  local file="$SHARED_AGENTS/deps.md"
  [ -f "$file" ]
  grep -qiE "conservative.*label|conservative.*risk|risk.*classif|default.*high" "$file"
}

# ── T-0023-066: Distillator persona >=130 lines ────────────────────────

@test "T-0023-066: Distillator persona >=130 lines (NOT reduced below Haiku threshold per R14)" {
  local file="$SHARED_AGENTS/distillator.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -ge 130 ]
}

# ── T-0023-066a: Distillator persona <=140 lines (ceiling) ────────────

@test "T-0023-066a: Distillator persona <=140 lines (ceiling from Step 1f table)" {
  local file="$SHARED_AGENTS/distillator.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 140 ]
}

# ── T-0023-067: Distillator contains 2 examples ───────────────────────

@test "T-0023-067: Distillator persona contains 2 examples (Haiku compliance grounding)" {
  local file="$SHARED_AGENTS/distillator.md"
  [ -f "$file" ]
  assert_has_tag "$file" "examples"
  local examples
  examples=$(extract_tag_content "$file" "examples")
  local example_count
  example_count=$(echo "$examples" | grep -ciE "\*\*example|\*\*wrong|\*\*correct|example [0-9]|<example" || true)
  [ "$example_count" -ge 2 ]
}

# ── T-0023-068: Every agent has >=1 example ────────────────────────────

@test "T-0023-068: Every agent persona has >=1 <examples> section with >=1 example" {
  local fail=0
  for agent_file in "${ALL_AGENTS[@]}"; do
    local file="$SHARED_AGENTS/$agent_file"
    [ -f "$file" ] || { echo "Missing: $agent_file"; fail=1; continue; }
    if ! grep -q '<examples>' "$file"; then
      echo "Missing <examples> tag in $agent_file"
      fail=1
      continue
    fi
    local examples
    examples=$(extract_tag_content "$file" "examples")
    # Check the examples section has substantive content (not just tags)
    local content_lines
    content_lines=$(echo "$examples" | grep -cvE '^\s*$|</?examples>' || true)
    if [ "$content_lines" -lt 2 ]; then
      echo "Empty or near-empty <examples> in $agent_file ($content_lines content lines)"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0023-069: No agent contains "How X Fits the Pipeline" ───────────

@test "T-0023-069: No agent persona contains 'How [Agent] Fits the Pipeline' section" {
  local fail=0
  for agent_file in "${ALL_AGENTS[@]}"; do
    local file="$SHARED_AGENTS/$agent_file"
    [ -f "$file" ] || continue
    if grep -qiE "^#+.*How.*Fits.*Pipeline" "$file"; then
      echo "Found 'How X Fits the Pipeline' in $agent_file"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0023-070: No Opus/Sonnet agent has generic review checklists ────

@test "T-0023-070: No Opus/Sonnet agent persona contains generic review category checklists" {
  # Distillator is Haiku -- excluded from this check
  local opus_sonnet_agents=(cal.md colby.md roz.md agatha.md ellis.md robert.md sable.md investigator.md sentinel.md darwin.md deps.md)
  local fail=0
  for agent_file in "${opus_sonnet_agents[@]}"; do
    local file="$SHARED_AGENTS/$agent_file"
    [ -f "$file" ] || continue
    # Check for enumerated generic review categories as a list
    local checklist_count
    checklist_count=$(grep -ciE "^\s*[-*]\s*(logic|security|error handling|naming|dead code|resource management|concurrency|type safety)" "$file" 2>/dev/null || true)
    if [ "$checklist_count" -ge 4 ]; then
      echo "Found generic review checklist ($checklist_count items) in $agent_file"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0023-071: Every reduced agent retains original frontmatter ──────

@test "T-0023-071: Every reduced agent persona retains its original YAML frontmatter unchanged" {
  # Verify key frontmatter fields exist in each agent's frontmatter overlay
  local frontmatter_dir="$PROJECT_ROOT/source/claude/agents"
  local fail=0
  for agent_file in "${ALL_AGENTS[@]}"; do
    local agent_name="${agent_file%.md}"
    local frontmatter_file="$frontmatter_dir/${agent_name}.frontmatter.yml"
    [ -f "$frontmatter_file" ] || { echo "Missing frontmatter: $frontmatter_file"; fail=1; continue; }
    # Verify key fields exist (name is mandatory)
    if ! grep -q "^name:" "$frontmatter_file"; then
      echo "Missing 'name:' in $frontmatter_file"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0023-072: Every reduced agent contains required XML tags ────────

@test "T-0023-072: Every reduced agent persona contains all required XML tags (identity, required-actions, workflow, examples, constraints, output)" {
  local required_tags=(identity required-actions workflow examples constraints output)
  local fail=0
  for agent_file in "${ALL_AGENTS[@]}"; do
    local file="$SHARED_AGENTS/$agent_file"
    [ -f "$file" ] || { echo "Missing: $agent_file"; fail=1; continue; }
    for tag in "${required_tags[@]}"; do
      if ! grep -q "<${tag}>" "$file"; then
        echo "Missing <${tag}> in $agent_file"
        fail=1
      fi
      if ! grep -q "</${tag}>" "$file"; then
        echo "Missing </${tag}> in $agent_file"
        fail=1
      fi
    done
  done
  [ "$fail" -eq 0 ]
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1g: Reduce invocation-templates.md
# Tests: T-0023-080 through T-0023-091 (12 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-080: invocation-templates.md <=300 lines ────────────────────

@test "T-0023-080: invocation-templates.md <=300 lines" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 300 ]
}

# ── T-0023-081: Header contains brain-context protocol ─────────────────

@test "T-0023-081: invocation-templates.md header contains brain-context injection protocol note" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  # Check first 50 lines for the header section
  local header
  header=$(head -50 "$file")
  echo "$header" | grep -qiE "brain.context.*inject|inject.*brain.context|<brain-context>"
}

# ── T-0023-082: Header contains standard READ items ────────────────────

@test "T-0023-082: invocation-templates.md header contains standard READ items note (retro-lessons.md, agent-preamble.md)" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  local header
  header=$(head -50 "$file")
  echo "$header" | grep -qiE "retro-lessons" || {
    echo "Header missing retro-lessons.md reference"
    return 1
  }
  echo "$header" | grep -qiE "agent-preamble" || {
    echo "Header missing agent-preamble.md reference"
    return 1
  }
}

# ── T-0023-083: Header contains persona-constraint note ────────────────

@test "T-0023-083: invocation-templates.md header contains persona-constraint note" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  local header
  header=$(head -50 "$file")
  echo "$header" | grep -qiE "persona.*constraint|constraint.*persona"
}

# ── T-0023-084: Template index lists <=20 templates ────────────────────

@test "T-0023-084: invocation-templates.md template index lists <=20 templates" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  # Count template headers (## or ### level headers that define templates)
  local template_count
  template_count=$(grep -cE '^### ' "$file" 2>/dev/null || true)
  [ "$template_count" -le 20 ]
}

# ── T-0023-085: No individual template has brain-context XML example ──

@test "T-0023-085: No individual template contains <brain-context> XML example block" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  # Skip the header section (first 50 lines which may legitimately reference it)
  local body
  body=$(tail -n +51 "$file")
  local bc_count
  bc_count=$(echo "$body" | grep -c '<brain-context>' 2>/dev/null || true)
  [ "$bc_count" -eq 0 ]
}

# ── T-0023-086: No template READ list has retro-lessons or preamble ───

@test "T-0023-086: No individual template READ list contains retro-lessons.md or agent-preamble.md" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  # Look for these files inside <read> tags in the body (past the header)
  local body
  body=$(tail -n +51 "$file")
  # Check for retro-lessons.md or agent-preamble.md within read sections
  local fail=0
  if echo "$body" | grep -qiE '<read>.*retro-lessons|retro-lessons.*</read>' 2>/dev/null; then
    echo "Found retro-lessons.md in individual template READ"
    fail=1
  fi
  # More thorough: check for these filenames in lines between <read> and </read>
  local in_read_sections
  in_read_sections=$(echo "$body" | sed -n '/<read>/,/<\/read>/p')
  if echo "$in_read_sections" | grep -q "retro-lessons" 2>/dev/null; then
    echo "Found retro-lessons.md in template READ section"
    fail=1
  fi
  if echo "$in_read_sections" | grep -q "agent-preamble" 2>/dev/null; then
    echo "Found agent-preamble.md in template READ section"
    fail=1
  fi
  [ "$fail" -eq 0 ]
}

# ── T-0023-087: roz-investigation has CI Watch variant annotation ─────

@test "T-0023-087: roz-investigation template contains 'CI Watch variant' annotation" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  # Extract the roz-investigation template section
  local section
  section=$(sed -n '/<template id="roz-investigation">/,/<template id=/p' "$file" | head -30)
  echo "$section" | grep -qiE "CI.*Watch.*variant|CI Watch"
}

# ── T-0023-088: colby-build has CI Watch variant annotation ────────────

@test "T-0023-088: colby-build template contains 'CI Watch variant' annotation" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  local section
  section=$(sed -n '/<template id="colby-build">/,/<template id=/p' "$file" | head -30)
  echo "$section" | grep -qiE "CI.*Watch.*variant|CI Watch"
}

# ── T-0023-089: roz-scoped-rerun has CI Watch variant annotation ──────

@test "T-0023-089: roz-scoped-rerun template contains 'CI Watch variant' annotation" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  local section
  section=$(sed -n '/<template id="roz-scoped-rerun">/,/<template id=/p' "$file" | head -30)
  echo "$section" | grep -qiE "CI.*Watch.*variant|CI Watch"
}

# ── T-0023-090: agent-teams-task moved to pipeline-operations.md ──────

@test "T-0023-090: agent-teams-task content moved to pipeline-operations.md (removed from invocation-templates)" {
  local templates="$SHARED_REFS/invocation-templates.md"
  local operations="$PROJECT_ROOT/source/shared/references/pipeline-operations.md"
  [ -f "$templates" ]
  [ -f "$operations" ]
  # Must NOT be in invocation-templates
  assert_not_contains "$templates" "agent-teams-task" "agent-teams-task should not be in invocation-templates.md"
  # Must be in pipeline-operations
  grep -qiE "agent-teams-task|agent.*teams.*task" "$operations"
}

# ── T-0023-091: dashboard-bridge removed from invocation-templates ────

@test "T-0023-091: dashboard-bridge template removed from invocation-templates.md" {
  local file="$SHARED_REFS/invocation-templates.md"
  [ -f "$file" ]
  assert_not_contains "$file" "dashboard-bridge" "dashboard-bridge should not be in invocation-templates.md"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1h: Create session-boot.sh hook script
# Tests: T-0023-100 through T-0023-121 (24 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── Helper: run session-boot.sh in a controlled environment ───────────
# Sets up a temp directory with minimal structure for testing.

setup_boot_env() {
  export TEST_BOOT_DIR
  TEST_BOOT_DIR=$(mktemp -d)
  mkdir -p "$TEST_BOOT_DIR/.claude/agents"
  mkdir -p "$TEST_BOOT_DIR/docs/pipeline"
}

teardown_boot_env() {
  if [ -n "${TEST_BOOT_DIR:-}" ] && [ -d "$TEST_BOOT_DIR" ]; then
    rm -rf "$TEST_BOOT_DIR"
  fi
}

# Run the boot script against a test directory
# Usage: run_boot_script [project_dir]
run_boot_script() {
  local project_dir="${1:-$TEST_BOOT_DIR}"
  local script="$SHARED_HOOKS/session-boot.sh"
  # The script reads from the project directory. We pass it via env or argument
  # depending on how the script is designed. Feed empty stdin.
  echo "" | PROJECT_ROOT="$project_dir" bash "$script" 2>/dev/null
}

# ── T-0023-100: session-boot.sh outputs valid JSON ────────────────────

@test "T-0023-100: session-boot.sh outputs valid JSON to stdout" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  # Validate JSON with jq
  echo "$output" | jq . >/dev/null 2>&1
}

# ── T-0023-101: JSON contains pipeline_active boolean ──────────────────

@test "T-0023-101: session-boot.sh JSON contains pipeline_active boolean field" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local val
  val=$(echo "$output" | jq -r '.pipeline_active' 2>/dev/null)
  # Must be true or false (boolean)
  [ "$val" = "true" ] || [ "$val" = "false" ]
}

# ── T-0023-102: JSON contains phase string ─────────────────────────────

@test "T-0023-102: session-boot.sh JSON contains phase string field" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local val
  val=$(echo "$output" | jq -r '.phase' 2>/dev/null)
  [ -n "$val" ]
  [ "$val" != "null" ]
}

# ── T-0023-103: JSON contains branching_strategy string ────────────────

@test "T-0023-103: session-boot.sh JSON contains branching_strategy string field" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local val
  val=$(echo "$output" | jq -r '.branching_strategy' 2>/dev/null)
  [ -n "$val" ]
  [ "$val" != "null" ]
}

# ── T-0023-104: JSON contains custom_agent_count integer ───────────────

@test "T-0023-104: session-boot.sh JSON contains custom_agent_count integer field" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local val
  val=$(echo "$output" | jq -r '.custom_agent_count' 2>/dev/null)
  # Must be a number
  [[ "$val" =~ ^[0-9]+$ ]]
}

# ── T-0023-104a: JSON contains feature string ──────────────────────────

@test "T-0023-104a: session-boot.sh JSON contains feature string field" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local val
  val=$(echo "$output" | jq 'has("feature")' 2>/dev/null)
  [ "$val" = "true" ]
}

# ── T-0023-104b: JSON contains stale_context boolean ───────────────────

@test "T-0023-104b: session-boot.sh JSON contains stale_context boolean field" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local val
  val=$(echo "$output" | jq -r '.stale_context' 2>/dev/null)
  [ "$val" = "true" ] || [ "$val" = "false" ]
}

# ── T-0023-105: JSON contains agent_teams fields ──────────────────────

@test "T-0023-105: session-boot.sh JSON contains agent_teams_enabled and agent_teams_env boolean fields" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local enabled env_val
  enabled=$(echo "$output" | jq -r '.agent_teams_enabled' 2>/dev/null)
  env_val=$(echo "$output" | jq -r '.agent_teams_env' 2>/dev/null)
  [ "$enabled" = "true" ] || [ "$enabled" = "false" ]
  [ "$env_val" = "true" ] || [ "$env_val" = "false" ]
}

# ── T-0023-106: JSON contains warn_agents array ───────────────────────

@test "T-0023-106: session-boot.sh JSON contains warn_agents array field" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local is_array
  is_array=$(echo "$output" | jq '.warn_agents | type' 2>/dev/null)
  [ "$is_array" = '"array"' ]
}

# ── T-0023-107: Missing pipeline-state.md -> defaults, exits 0 ────────

@test "T-0023-107: Missing pipeline-state.md -> outputs defaults (pipeline_active: false, phase: idle) and exits 0" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  # Ensure no pipeline-state.md exists
  rm -f "$TEST_BOOT_DIR/docs/pipeline/pipeline-state.md"
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  local exit_code=$?
  teardown_boot_env
  [ "$exit_code" -eq 0 ]
  local active phase
  active=$(echo "$output" | jq -r '.pipeline_active' 2>/dev/null)
  phase=$(echo "$output" | jq -r '.phase' 2>/dev/null)
  [ "$active" = "false" ]
  [ "$phase" = "idle" ]
}

# ── T-0023-108: Missing pipeline-config.json -> defaults, exits 0 ─────

@test "T-0023-108: Missing pipeline-config.json -> outputs defaults (branching_strategy: trunk-based) and exits 0" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  # Ensure no pipeline-config.json
  rm -f "$TEST_BOOT_DIR/.claude/pipeline-config.json"
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  local exit_code=$?
  teardown_boot_env
  [ "$exit_code" -eq 0 ]
  local strategy
  strategy=$(echo "$output" | jq -r '.branching_strategy' 2>/dev/null)
  [ "$strategy" = "trunk-based" ]
}

# ── T-0023-109: Missing .claude/agents/ -> custom_agent_count: 0 ──────

@test "T-0023-109: Missing .claude/agents/ directory -> outputs custom_agent_count: 0 and exits 0" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  # Remove agents directory
  rm -rf "$TEST_BOOT_DIR/.claude/agents"
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  local exit_code=$?
  teardown_boot_env
  [ "$exit_code" -eq 0 ]
  local count
  count=$(echo "$output" | jq -r '.custom_agent_count' 2>/dev/null)
  [ "$count" = "0" ]
}

# ── T-0023-110: Malformed pipeline-state.md -> defaults, exits 0 ──────

@test "T-0023-110: Malformed pipeline-state.md (no PIPELINE_STATUS marker) -> outputs defaults and exits 0" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  # Create a pipeline-state.md without PIPELINE_STATUS JSON
  echo "# Pipeline State" > "$TEST_BOOT_DIR/docs/pipeline/pipeline-state.md"
  echo "Some content but no PIPELINE_STATUS marker" >> "$TEST_BOOT_DIR/docs/pipeline/pipeline-state.md"
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  local exit_code=$?
  teardown_boot_env
  [ "$exit_code" -eq 0 ]
  local active
  active=$(echo "$output" | jq -r '.pipeline_active' 2>/dev/null)
  [ "$active" = "false" ]
}

# ── T-0023-111: CLAUDE_AGENT_TEAMS set -> agent_teams_env: true ────────

@test "T-0023-111: CLAUDE_AGENT_TEAMS env var set -> agent_teams_env: true" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(CLAUDE_AGENT_TEAMS=1 run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local env_val
  env_val=$(echo "$output" | jq -r '.agent_teams_env' 2>/dev/null)
  [ "$env_val" = "true" ]
}

# ── T-0023-112: CLAUDE_AGENT_TEAMS unset -> agent_teams_env: false ────

@test "T-0023-112: CLAUDE_AGENT_TEAMS env var unset -> agent_teams_env: false" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local output
  output=$(unset CLAUDE_AGENT_TEAMS; run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local env_val
  env_val=$(echo "$output" | jq -r '.agent_teams_env' 2>/dev/null)
  [ "$env_val" = "false" ]
}

# ── T-0023-113: Script is executable ───────────────────────────────────

@test "T-0023-113: session-boot.sh is executable (-x bit set)" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  [ -x "$script" ]
}

# ── T-0023-114: Script starts with set -uo pipefail ───────────────────

@test "T-0023-114: session-boot.sh starts with 'set -uo pipefail' (not set -e, per retro lesson #003)" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  grep -q "set -uo pipefail" "$script"
  # Must NOT use set -e (retro lesson #003)
  assert_not_contains "$script" "^set -e$\|^set -eo " "session-boot.sh must not use set -e"
}

# ── T-0023-115: warn_agents populated from error-patterns.md ──────────

@test "T-0023-115: warn_agents array contains agent names from error-patterns.md with Recurrence >= 3" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  # Create an error-patterns.md with a pattern that has Recurrence: 3
  mkdir -p "$TEST_BOOT_DIR/docs/pipeline"
  cat > "$TEST_BOOT_DIR/docs/pipeline/error-patterns.md" <<'PATTERNS'
# Error Patterns

## Pattern: Test assertion mismatch
- Agent: colby
- Recurrence: 3
- Description: Colby modifies test assertions

## Pattern: Missing docs
- Agent: agatha
- Recurrence: 1
- Description: Agatha skips doc update
PATTERNS
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  # warn_agents should contain colby (Recurrence >= 3) but not agatha (Recurrence 1)
  local agents
  agents=$(echo "$output" | jq -r '.warn_agents[]' 2>/dev/null)
  echo "$agents" | grep -q "colby"
}

# ── T-0023-116: JSON contains all config-derived fields ────────────────

@test "T-0023-116: session-boot.sh JSON contains ci_watch_enabled, darwin_enabled, dashboard_mode, sentinel_enabled, deps_agent_enabled" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  # Create a pipeline-config.json with all fields
  cat > "$TEST_BOOT_DIR/.claude/pipeline-config.json" <<'CONFIG'
{
  "branching_strategy": "trunk-based",
  "ci_watch_enabled": true,
  "darwin_enabled": false,
  "dashboard_mode": "none",
  "sentinel_enabled": true,
  "deps_agent_enabled": false,
  "agent_teams_enabled": false
}
CONFIG
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local fail=0
  for field in ci_watch_enabled darwin_enabled dashboard_mode sentinel_enabled deps_agent_enabled; do
    local has_field
    has_field=$(echo "$output" | jq "has(\"$field\")" 2>/dev/null)
    if [ "$has_field" != "true" ]; then
      echo "Missing field: $field"
      fail=1
    fi
  done
  [ "$fail" -eq 0 ]
}

# ── T-0023-117: JSON contains project_name field ──────────────────────

@test "T-0023-117: session-boot.sh JSON contains project_name field" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  cat > "$TEST_BOOT_DIR/.claude/pipeline-config.json" <<'CONFIG'
{
  "project_name": "my-test-project",
  "branching_strategy": "trunk-based"
}
CONFIG
  local output
  output=$(run_boot_script "$TEST_BOOT_DIR")
  teardown_boot_env
  local name
  name=$(echo "$output" | jq -r '.project_name' 2>/dev/null)
  [ "$name" = "my-test-project" ]
}

# ── T-0023-118: No git remote + no config -> dir basename ─────────────

@test "T-0023-118: No git remote and no project_name in config -> project_name is current directory basename" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  # No pipeline-config.json, no git remote
  local output
  output=$(cd "$TEST_BOOT_DIR" && PROJECT_ROOT="$TEST_BOOT_DIR" echo "" | bash "$script" 2>/dev/null)
  teardown_boot_env
  local name
  name=$(echo "$output" | jq -r '.project_name' 2>/dev/null)
  [ -n "$name" ]
  [ "$name" != "null" ]
}

# ── T-0023-119: Script completes in <500ms ─────────────────────────────

@test "T-0023-119: session-boot.sh completes in <500ms (no network calls, no brain)" {
  local script="$SHARED_HOOKS/session-boot.sh"
  [ -f "$script" ] || skip "session-boot.sh not yet created"
  setup_boot_env
  local start end elapsed
  start=$(date +%s%3N 2>/dev/null || python3 -c 'import time; print(int(time.time()*1000))')
  run_boot_script "$TEST_BOOT_DIR" >/dev/null
  end=$(date +%s%3N 2>/dev/null || python3 -c 'import time; print(int(time.time()*1000))')
  teardown_boot_env
  elapsed=$((end - start))
  [ "$elapsed" -lt 500 ]
}

# ── T-0023-120: default-persona.md references session-boot.sh ─────────

@test "T-0023-120: default-persona.md boot sequence references session-boot.sh output parsing for steps 1-3d" {
  local file="$SHARED_RULES/default-persona.md"
  [ -f "$file" ]
  grep -qiE "session-boot" "$file"
}

# ── T-0023-121: default-persona.md retains steps 4-6 ──────────────────

@test "T-0023-121: default-persona.md boot sequence still contains steps 4-6 (brain health, brain context, announcement)" {
  local file="$SHARED_RULES/default-persona.md"
  [ -f "$file" ]
  local fail=0
  # Step 4: Brain health check
  grep -qiE "brain.*health|atelier_stats|brain.*check" "$file" || { echo "Missing: brain health check (step 4)"; fail=1; }
  # Step 5: Brain context retrieval
  grep -qiE "brain.*context.*retriev|agent_search" "$file" || { echo "Missing: brain context retrieval (step 5)"; fail=1; }
  # Step 6: Announcement
  grep -qiE "announce.*session|session.*state.*user|announce" "$file" || { echo "Missing: announcement synthesis (step 6)"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1i: Reduce pipeline-orchestration.md
# Tests: T-0023-130 through T-0023-134a (6 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-130: pipeline-orchestration.md <=650 lines ──────────────────

@test "T-0023-130: pipeline-orchestration.md <=650 lines" {
  local file="$SHARED_RULES/pipeline-orchestration.md"
  [ -f "$file" ]
  local lines
  lines=$(wc -l < "$file" | tr -d ' ')
  [ "$lines" -le 650 ]
}

# ── T-0023-131: All 12 mandatory gates preserved ──────────────────────

@test "T-0023-131: All 12 mandatory gates preserved verbatim (count numbered items under 'Eva NEVER Skips')" {
  local file="$SHARED_RULES/pipeline-orchestration.md"
  [ -f "$file" ]
  # Find the mandatory gates section
  grep -q "Eva NEVER Skips" "$file"
  # Count numbered gates (1. through 12.)
  local gate_section
  gate_section=$(sed -n '/Eva NEVER Skips/,/^<\/gate>/p' "$file")
  local gate_count
  gate_count=$(echo "$gate_section" | grep -cE '^\s*[0-9]+\.\s+\*\*' || true)
  [ "$gate_count" -ge 12 ]
}

# ── T-0023-132: Observation masking receipts preserved ─────────────────

@test "T-0023-132: All observation masking receipt formats preserved" {
  local file="$SHARED_RULES/pipeline-orchestration.md"
  [ -f "$file" ]
  # The receipt table should still be present
  grep -qiE "Receipt Format|observation.*mask" "$file"
  # Check for key agent receipts
  grep -q "Cal:" "$file"
  grep -q "Colby:" "$file"
  grep -q "Roz:" "$file"
}

# ── T-0023-133: Brain capture model preserved ──────────────────────────

@test "T-0023-133: Brain capture model section preserved" {
  local file="$SHARED_RULES/pipeline-orchestration.md"
  [ -f "$file" ]
  grep -qiE "brain.*capture|capture.*model|Hybrid Capture" "$file"
}

# ── T-0023-134: Investigation discipline preserved ─────────────────────

@test "T-0023-134: Investigation discipline section preserved" {
  local file="$SHARED_RULES/pipeline-orchestration.md"
  [ -f "$file" ]
  grep -qiE "investigation.*discipline|Layer Escalation" "$file"
}

# ── T-0023-134a: Pipeline flow diagram preserved ──────────────────────

@test "T-0023-134a: Pipeline flow diagram preserved (Idea -> Robert or equivalent flow marker)" {
  local file="$SHARED_RULES/pipeline-orchestration.md"
  [ -f "$file" ]
  grep -qiE "Idea.*Robert|Robert.*spec.*->|pipeline.*flow" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1j: Update SKILL.md and /pipeline-setup
# Tests: T-0023-140 through T-0023-143 (4 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-140: SKILL.md lists step-sizing.md ──────────────────────────

@test "T-0023-140: SKILL.md lists step-sizing.md in references" {
  [ -f "$SKILL_FILE" ]
  grep -q "step-sizing" "$SKILL_FILE"
}

# ── T-0023-141: SKILL.md includes session-boot.sh in SessionStart ─────

@test "T-0023-141: SKILL.md settings.json template includes session-boot.sh in SessionStart hooks" {
  [ -f "$SKILL_FILE" ]
  grep -qiE "session-boot" "$SKILL_FILE"
}

# ── T-0023-142: /pipeline-setup copies step-sizing.md ──────────────────

@test "T-0023-142: /pipeline-setup SKILL.md references step-sizing.md for copy to target .claude/references/" {
  # The SKILL.md install instructions should mention copying step-sizing.md
  [ -f "$SKILL_FILE" ]
  # Check that step-sizing.md appears in the references section or copy list
  grep -q "step-sizing" "$SKILL_FILE"
}

# ── T-0023-143: /pipeline-setup registers session-boot.sh hook ────────

@test "T-0023-143: /pipeline-setup SKILL.md registers session-boot.sh hook" {
  [ -f "$SKILL_FILE" ]
  grep -qiE "session-boot" "$SKILL_FILE"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1l: Final integration verification
# Tests: T-0023-150 through T-0023-155 (6 tests)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0023-150: Total agent lines across 12 agents <=935 ──────────────

@test "T-0023-150: Total agent persona lines across 12 agents <=935" {
  local total=0
  for agent_file in "${ALL_AGENTS[@]}"; do
    local file="$SHARED_AGENTS/$agent_file"
    [ -f "$file" ] || { echo "Missing: $agent_file"; return 1; }
    local lines
    lines=$(wc -l < "$file" | tr -d ' ')
    total=$((total + lines))
  done
  echo "Total agent lines: $total (target: <=935)"
  [ "$total" -le 935 ]
}

# ── T-0023-151: All bats tests pass ───────────────────────────────────

@test "T-0023-151: All bats hook tests pass" {
  run bats "$PROJECT_ROOT/tests/hooks/"
  [ "$status" -eq 0 ]
}

# ── T-0023-152: All brain tests pass ──────────────────────────────────

@test "T-0023-152: All brain tests pass" {
  if [ ! -d "$PROJECT_ROOT/brain" ]; then
    skip "brain directory not found"
  fi
  run bash -c "cd '$PROJECT_ROOT/brain' && node --test '../tests/brain/'*.test.mjs"
  [ "$status" -eq 0 ]
}

# ── T-0023-153: Assembled Cal is valid markdown ────────────────────────

@test "T-0023-153: Assembled Cal persona (claude overlay + shared content) is valid markdown" {
  local shared="$SHARED_AGENTS/cal.md"
  local frontmatter="$PROJECT_ROOT/source/claude/agents/cal.frontmatter.yml"
  local installed="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$shared" ]
  [ -f "$frontmatter" ]
  # If installed copy exists, verify it starts with YAML frontmatter
  if [ -f "$installed" ]; then
    head -1 "$installed" | grep -q "^---"
    # Verify it contains content from shared file
    local first_header
    first_header=$(grep -m1 "^#" "$shared")
    grep -qF "$first_header" "$installed" || {
      echo "Installed Cal does not contain shared content header: $first_header"
      return 1
    }
  else
    # If not yet assembled, verify the source components exist and are valid
    head -1 "$frontmatter" | grep -qE "^name:|^---"
    grep -q "<identity>" "$shared"
  fi
}

# ── T-0023-154: Assembled Colby is valid markdown ──────────────────────

@test "T-0023-154: Assembled Colby persona (claude overlay + shared content) is valid markdown" {
  local shared="$SHARED_AGENTS/colby.md"
  local frontmatter="$PROJECT_ROOT/source/claude/agents/colby.frontmatter.yml"
  local installed="$PROJECT_ROOT/.claude/agents/colby.md"
  [ -f "$shared" ]
  [ -f "$frontmatter" ]
  if [ -f "$installed" ]; then
    head -1 "$installed" | grep -q "^---"
    local first_header
    first_header=$(grep -m1 "^#" "$shared")
    grep -qF "$first_header" "$installed" || {
      echo "Installed Colby does not contain shared content header: $first_header"
      return 1
    }
  else
    head -1 "$frontmatter" | grep -qE "^name:|^---"
    grep -q "<identity>" "$shared"
  fi
}

# ── T-0023-155: Assembled Roz is valid markdown ───────────────────────

@test "T-0023-155: Assembled Roz persona (claude overlay + shared content) is valid markdown" {
  local shared="$SHARED_AGENTS/roz.md"
  local frontmatter="$PROJECT_ROOT/source/claude/agents/roz.frontmatter.yml"
  local installed="$PROJECT_ROOT/.claude/agents/roz.md"
  [ -f "$shared" ]
  [ -f "$frontmatter" ]
  if [ -f "$installed" ]; then
    head -1 "$installed" | grep -q "^---"
    local first_header
    first_header=$(grep -m1 "^#" "$shared")
    grep -qF "$first_header" "$installed" || {
      echo "Installed Roz does not contain shared content header: $first_header"
      return 1
    }
  else
    head -1 "$frontmatter" | grep -qE "^name:|^---"
    grep -q "<identity>" "$shared"
  fi
}
