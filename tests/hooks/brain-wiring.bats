#!/usr/bin/env bats
# Tests for ADR-0021: Structural validation for brain wiring changes
# Covers Steps 2a-2d (frontmatter + persona), Step 4 (preamble/template),
# Steps 5a-5b (dead prose removal), Step 6 (post-compact enhancement),
# and cross-step tests.
#
# T-IDs: T-0021-016 through T-0021-051 (Steps 2a-2d)
#        T-0021-062 through T-0021-067, T-0021-118, T-0021-119 (Step 4)
#        T-0021-068 through T-0021-091, T-0021-111, T-0021-112, T-0021-113 (Steps 5a-5b)
#        T-0021-092 through T-0021-098, T-0021-114 (Step 6)
#        T-0021-101 through T-0021-104, T-0021-108, T-0021-115 (Cross-step)

load test_helper

# Absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BATS_TEST_FILENAME}")/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════════
# Helper: extract YAML frontmatter from a markdown file
# Usage: extract_frontmatter "/path/to/file.md"
# Returns the content between the first pair of --- delimiters
# macOS-compatible sed expression.
# ═══════════════════════════════════════════════════════════════════════

extract_frontmatter() {
  local file="$1"
  sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Helper: compare files with placeholder resolution
# Usage: compare_with_placeholder_resolution "$claude_file" "$source_file"
# Resolves {config_dir} and other placeholders in source_file, then compares
# Returns 0 if files match (with placeholders resolved), non-zero otherwise
# ═══════════════════════════════════════════════════════════════════════

compare_with_placeholder_resolution() {
  local claude_file="$1"
  local source_file="$2"
  local resolved
  resolved=$(mktemp)
  
  # Resolve placeholders in source file
  sed -e 's|{config_dir}|.claude|g' \
      -e 's|{pipeline_state_dir}|docs/pipeline|g' \
      -e 's|{architecture_dir}|docs/architecture|g' \
      -e 's|{product_specs_dir}|docs/product|g' \
      -e 's|{ux_docs_dir}|docs/ux|g' \
      -e 's|{features_dir}|source|g' \
      -e 's|{source_dir}|source|g' \
      -e 's|{conventions_file}|docs/CONVENTIONS.md|g' \
      -e 's|{changelog_file}|CHANGELOG.md|g' \
      "$source_file" > "$resolved"
  
  cmp -s "$claude_file" "$resolved"
  local result=$?
  rm -f "$resolved"
  return $result
}

# ═══════════════════════════════════════════════════════════════════════
# Step 2a: Cal Frontmatter + Brain Access Section
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-016: Happy -- Cal .claude frontmatter has mcpServers atelier-brain ──

@test "T-0021-016: .claude/agents/cal.md YAML frontmatter contains mcpServers with atelier-brain" {
  local file="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "mcpServers"
  echo "$frontmatter" | grep -q "atelier-brain"
}

# ── T-0021-017: Happy -- Cal source frontmatter has mcpServers atelier-brain ──

@test "T-0021-017: source/agents/cal.md YAML frontmatter contains mcpServers with atelier-brain" {
  local file="$PROJECT_ROOT/source/agents/cal.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "mcpServers"
  echo "$frontmatter" | grep -q "atelier-brain"
}

# ── T-0021-018: Happy -- Cal has brain-access protocol section ──

@test "T-0021-018: .claude/agents/cal.md contains a protocol id brain-access section" {
  local file="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$file" ]
  grep -q '<protocol id="brain-access">' "$file"
}

# ── T-0021-019: Happy -- Cal Brain Access mentions thought_type decision ──

@test "T-0021-019: Cal Brain Access section mentions thought_type decision as a capture gate" {
  local file="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$file" ]
  grep -q "thought_type.*decision\|thought_type: 'decision'\|thought_type: \"decision\"" "$file"
}

# ── T-0021-020: Happy -- Cal Brain Access mentions source_agent cal ──

@test "T-0021-020: Cal Brain Access section mentions source_agent cal" {
  local file="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$file" ]
  grep -q "source_agent.*cal\|source_agent: 'cal'\|source_agent: \"cal\"" "$file"
}

# ── T-0021-021: Failure -- Cal Brain Access contains unavailable clause ──

@test "T-0021-021: Cal Brain Access section contains When brain is unavailable clause" {
  local file="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$file" ]
  grep -qi "When brain is unavailable" "$file"
}

# ── T-0021-022: Regression -- Cal tools frontmatter unchanged ──

@test "T-0021-022: Cal tools frontmatter still includes Read, Write, Edit, Glob, Grep, Bash, Agent(roz)" {
  local file="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "tools:.*Read"
  echo "$frontmatter" | grep -q "Agent(roz)"
}

# ── T-0021-023: Regression -- Cal existing workflow content is unchanged ──
# Note: We verify key landmark strings exist, not byte-identical content
# (since the test runs before build, we check structural integrity)

@test "T-0021-023: Cal workflow section still contains ADR Production and Hard Gates landmarks" {
  local file="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$file" ]
  grep -q "ADR Production" "$file"
  grep -q "Hard Gates" "$file"
}

# ── T-0021-024: Boundary -- Cal Brain Access sections identical between .claude and source ──

@test "T-0021-024: .claude/agents/cal.md and source/agents/cal.md Brain Access sections are identical" {
  local claude_file="$PROJECT_ROOT/.claude/agents/cal.md"
  local source_file="$PROJECT_ROOT/source/agents/cal.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]

  # Extract the brain-access protocol section from both files
  local claude_section source_section
  claude_section=$(sed -n '/<protocol id="brain-access">/,/<\/protocol>/p' "$claude_file")
  source_section=$(sed -n '/<protocol id="brain-access">/,/<\/protocol>/p' "$source_file")

  [ -n "$claude_section" ]
  [ "$claude_section" = "$source_section" ]
}

# ── T-0021-101: Error -- Cal frontmatter is valid YAML ──

@test "T-0021-101: .claude/agents/cal.md YAML frontmatter is valid YAML" {
  local file="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  # Use python3 yaml parser if available, otherwise basic syntax check
  if command -v python3 &>/dev/null; then
    echo "$frontmatter" | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)"
  else
    echo "$frontmatter" | grep -qE '^[a-zA-Z_]+:'
  fi
}

# ── T-0021-115: Boundary -- Cal brain-access section placement after workflow, before examples ──

@test "T-0021-115: Cal brain-access protocol section appears after </workflow> and before <examples>" {
  local file="$PROJECT_ROOT/.claude/agents/cal.md"
  [ -f "$file" ]

  # Get line numbers
  local workflow_end brain_start examples_start
  workflow_end=$(grep -n '</workflow>' "$file" | tail -1 | cut -d: -f1)
  brain_start=$(grep -n '<protocol id="brain-access">' "$file" | head -1 | cut -d: -f1)
  examples_start=$(grep -n '<examples>' "$file" | head -1 | cut -d: -f1)

  [ -n "$workflow_end" ]
  [ -n "$brain_start" ]
  [ -n "$examples_start" ]

  # brain-access must come after workflow end and before examples
  [ "$brain_start" -gt "$workflow_end" ]
  [ "$brain_start" -lt "$examples_start" ]
}

# ═══════════════════════════════════════════════════════════════════════
# Step 2b: Colby Frontmatter + Brain Access Section
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-025: Happy -- Colby .claude frontmatter has mcpServers atelier-brain ──

@test "T-0021-025: .claude/agents/colby.md YAML frontmatter contains mcpServers with atelier-brain" {
  local file="$PROJECT_ROOT/.claude/agents/colby.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "mcpServers"
  echo "$frontmatter" | grep -q "atelier-brain"
}

# ── T-0021-026: Happy -- Colby source frontmatter has mcpServers atelier-brain ──

@test "T-0021-026: source/agents/colby.md YAML frontmatter contains mcpServers with atelier-brain" {
  local file="$PROJECT_ROOT/source/agents/colby.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "mcpServers"
  echo "$frontmatter" | grep -q "atelier-brain"
}

# ── T-0021-027: Happy -- Colby has brain-access protocol section ──

@test "T-0021-027: .claude/agents/colby.md contains a protocol id brain-access section" {
  local file="$PROJECT_ROOT/.claude/agents/colby.md"
  [ -f "$file" ]
  grep -q '<protocol id="brain-access">' "$file"
}

# ── T-0021-028: Happy -- Colby Brain Access mentions thought_type insight ──

@test "T-0021-028: Colby Brain Access section mentions thought_type insight as a capture gate" {
  local file="$PROJECT_ROOT/.claude/agents/colby.md"
  [ -f "$file" ]
  grep -q "thought_type.*insight\|thought_type: 'insight'\|thought_type: \"insight\"" "$file"
}

# ── T-0021-029: Happy -- Colby Brain Access mentions source_agent colby ──

@test "T-0021-029: Colby Brain Access section mentions source_agent colby" {
  local file="$PROJECT_ROOT/.claude/agents/colby.md"
  [ -f "$file" ]
  grep -q "source_agent.*colby\|source_agent: 'colby'\|source_agent: \"colby\"" "$file"
}

# ── T-0021-030: Failure -- Colby Brain Access contains unavailable clause ──

@test "T-0021-030: Colby Brain Access section contains When brain is unavailable clause" {
  local file="$PROJECT_ROOT/.claude/agents/colby.md"
  [ -f "$file" ]
  grep -qi "When brain is unavailable" "$file"
}

# ── T-0021-031: Regression -- Colby tools frontmatter unchanged ──

@test "T-0021-031: Colby tools frontmatter still includes Read, Write, Edit, MultiEdit, Glob, Grep, Bash, Agent(roz, cal)" {
  local file="$PROJECT_ROOT/.claude/agents/colby.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "tools:.*Read"
  echo "$frontmatter" | grep -q "MultiEdit"
  echo "$frontmatter" | grep -q "Agent(roz, cal)"
}

# ── T-0021-032: Regression -- Colby existing workflow content is unchanged ──

@test "T-0021-032: Colby workflow section still contains Mockup Mode and Branch & MR Mode landmarks" {
  local file="$PROJECT_ROOT/.claude/agents/colby.md"
  [ -f "$file" ]
  grep -q "Mockup Mode" "$file"
  grep -q "Branch.*MR Mode\|Branch & MR Mode" "$file"
}

# ── T-0021-033: Boundary -- Colby Brain Access sections identical between .claude and source ──

@test "T-0021-033: .claude/agents/colby.md and source/agents/colby.md Brain Access sections are identical" {
  local claude_file="$PROJECT_ROOT/.claude/agents/colby.md"
  local source_file="$PROJECT_ROOT/source/agents/colby.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]

  local claude_section source_section
  claude_section=$(sed -n '/<protocol id="brain-access">/,/<\/protocol>/p' "$claude_file")
  source_section=$(sed -n '/<protocol id="brain-access">/,/<\/protocol>/p' "$source_file")

  [ -n "$claude_section" ]
  [ "$claude_section" = "$source_section" ]
}

# ── T-0021-102: Error -- Colby frontmatter is valid YAML ──

@test "T-0021-102: .claude/agents/colby.md YAML frontmatter is valid YAML" {
  local file="$PROJECT_ROOT/.claude/agents/colby.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  if command -v python3 &>/dev/null; then
    echo "$frontmatter" | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)"
  else
    echo "$frontmatter" | grep -qE '^[a-zA-Z_]+:'
  fi
}

# ═══════════════════════════════════════════════════════════════════════
# Step 2c: Roz Frontmatter + Brain Access Section
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-034: Happy -- Roz .claude frontmatter has mcpServers atelier-brain ──

@test "T-0021-034: .claude/agents/roz.md YAML frontmatter contains mcpServers with atelier-brain" {
  local file="$PROJECT_ROOT/.claude/agents/roz.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "mcpServers"
  echo "$frontmatter" | grep -q "atelier-brain"
}

# ── T-0021-035: Happy -- Roz source frontmatter has mcpServers atelier-brain ──

@test "T-0021-035: source/agents/roz.md YAML frontmatter contains mcpServers with atelier-brain" {
  local file="$PROJECT_ROOT/source/agents/roz.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "mcpServers"
  echo "$frontmatter" | grep -q "atelier-brain"
}

# ── T-0021-036: Happy -- Roz has brain-access protocol section ──

@test "T-0021-036: .claude/agents/roz.md contains a protocol id brain-access section" {
  local file="$PROJECT_ROOT/.claude/agents/roz.md"
  [ -f "$file" ]
  grep -q '<protocol id="brain-access">' "$file"
}

# ── T-0021-037: Happy -- Roz Brain Access mentions thought_type pattern ──

@test "T-0021-037: Roz Brain Access section mentions thought_type pattern for recurring failure patterns" {
  local file="$PROJECT_ROOT/.claude/agents/roz.md"
  [ -f "$file" ]
  grep -q "thought_type.*pattern\|thought_type: 'pattern'\|thought_type: \"pattern\"" "$file"
}

# ── T-0021-038: Happy -- Roz Brain Access mentions source_agent roz ──

@test "T-0021-038: Roz Brain Access section mentions source_agent roz" {
  local file="$PROJECT_ROOT/.claude/agents/roz.md"
  [ -f "$file" ]
  grep -q "source_agent.*roz\|source_agent: 'roz'\|source_agent: \"roz\"" "$file"
}

# ── T-0021-039: Failure -- Roz Brain Access contains unavailable clause ──

@test "T-0021-039: Roz Brain Access section contains When brain is unavailable clause" {
  local file="$PROJECT_ROOT/.claude/agents/roz.md"
  [ -f "$file" ]
  grep -qi "When brain is unavailable" "$file"
}

# ── T-0021-040: Regression -- Roz disallowedTools frontmatter unchanged ──

@test "T-0021-040: Roz disallowedTools frontmatter still includes Agent, Edit, MultiEdit, NotebookEdit" {
  local file="$PROJECT_ROOT/.claude/agents/roz.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "disallowedTools:.*Agent"
  echo "$frontmatter" | grep -q "Edit"
  echo "$frontmatter" | grep -q "MultiEdit"
  echo "$frontmatter" | grep -q "NotebookEdit"
}

# ── T-0021-041: Regression -- Roz existing workflow content is unchanged ──

@test "T-0021-041: Roz workflow section still contains Investigation Mode and Code QA Mode landmarks" {
  local file="$PROJECT_ROOT/.claude/agents/roz.md"
  [ -f "$file" ]
  grep -q "Investigation Mode" "$file"
  grep -q "Code QA Mode" "$file"
}

# ── T-0021-042: Boundary -- Roz Brain Access sections identical between .claude and source ──

@test "T-0021-042: .claude/agents/roz.md and source/agents/roz.md Brain Access sections are identical" {
  local claude_file="$PROJECT_ROOT/.claude/agents/roz.md"
  local source_file="$PROJECT_ROOT/source/agents/roz.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]

  local claude_section source_section
  claude_section=$(sed -n '/<protocol id="brain-access">/,/<\/protocol>/p' "$claude_file")
  source_section=$(sed -n '/<protocol id="brain-access">/,/<\/protocol>/p' "$source_file")

  [ -n "$claude_section" ]
  [ "$claude_section" = "$source_section" ]
}

# ── T-0021-103: Error -- Roz frontmatter is valid YAML ──

@test "T-0021-103: .claude/agents/roz.md YAML frontmatter is valid YAML" {
  local file="$PROJECT_ROOT/.claude/agents/roz.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  if command -v python3 &>/dev/null; then
    echo "$frontmatter" | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)"
  else
    echo "$frontmatter" | grep -qE '^[a-zA-Z_]+:'
  fi
}

# ═══════════════════════════════════════════════════════════════════════
# Step 2d: Agatha Frontmatter + Brain Access Section
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-043: Happy -- Agatha .claude frontmatter has mcpServers atelier-brain ──

@test "T-0021-043: .claude/agents/agatha.md YAML frontmatter contains mcpServers with atelier-brain" {
  local file="$PROJECT_ROOT/.claude/agents/agatha.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "mcpServers"
  echo "$frontmatter" | grep -q "atelier-brain"
}

# ── T-0021-044: Happy -- Agatha source frontmatter has mcpServers atelier-brain ──

@test "T-0021-044: source/agents/agatha.md YAML frontmatter contains mcpServers with atelier-brain" {
  local file="$PROJECT_ROOT/source/agents/agatha.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "mcpServers"
  echo "$frontmatter" | grep -q "atelier-brain"
}

# ── T-0021-045: Happy -- Agatha has brain-access protocol section ──

@test "T-0021-045: .claude/agents/agatha.md contains a protocol id brain-access section" {
  local file="$PROJECT_ROOT/.claude/agents/agatha.md"
  [ -f "$file" ]
  grep -q '<protocol id="brain-access">' "$file"
}

# ── T-0021-046: Happy -- Agatha Brain Access mentions thought_type decision ──

@test "T-0021-046: Agatha Brain Access section mentions thought_type decision for doc structure decisions" {
  local file="$PROJECT_ROOT/.claude/agents/agatha.md"
  [ -f "$file" ]
  grep -q "thought_type.*decision\|thought_type: 'decision'\|thought_type: \"decision\"" "$file"
}

# ── T-0021-047: Happy -- Agatha Brain Access mentions source_agent agatha ──

@test "T-0021-047: Agatha Brain Access section mentions source_agent agatha" {
  local file="$PROJECT_ROOT/.claude/agents/agatha.md"
  [ -f "$file" ]
  grep -q "source_agent.*agatha\|source_agent: 'agatha'\|source_agent: \"agatha\"" "$file"
}

# ── T-0021-048: Failure -- Agatha Brain Access contains unavailable clause ──

@test "T-0021-048: Agatha Brain Access section contains When brain is unavailable clause" {
  local file="$PROJECT_ROOT/.claude/agents/agatha.md"
  [ -f "$file" ]
  grep -qi "When brain is unavailable" "$file"
}

# ── T-0021-049: Regression -- Agatha disallowedTools frontmatter unchanged ──

@test "T-0021-049: Agatha disallowedTools frontmatter still includes Agent, NotebookEdit" {
  local file="$PROJECT_ROOT/.claude/agents/agatha.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  echo "$frontmatter" | grep -q "disallowedTools:.*Agent"
  echo "$frontmatter" | grep -q "NotebookEdit"
}

# ── T-0021-050: Regression -- Agatha existing workflow content is unchanged ──

@test "T-0021-050: Agatha workflow section still contains Documentation Process and Audience Types landmarks" {
  local file="$PROJECT_ROOT/.claude/agents/agatha.md"
  [ -f "$file" ]
  grep -q "Documentation Process" "$file"
  grep -q "Audience Types" "$file"
}

# ── T-0021-051: Boundary -- Agatha Brain Access sections identical between .claude and source ──

@test "T-0021-051: .claude/agents/agatha.md and source/agents/agatha.md Brain Access sections are identical" {
  local claude_file="$PROJECT_ROOT/.claude/agents/agatha.md"
  local source_file="$PROJECT_ROOT/source/agents/agatha.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]

  local claude_section source_section
  claude_section=$(sed -n '/<protocol id="brain-access">/,/<\/protocol>/p' "$claude_file")
  source_section=$(sed -n '/<protocol id="brain-access">/,/<\/protocol>/p' "$source_file")

  [ -n "$claude_section" ]
  [ "$claude_section" = "$source_section" ]
}

# ── T-0021-104: Error -- Agatha frontmatter is valid YAML ──

@test "T-0021-104: .claude/agents/agatha.md YAML frontmatter is valid YAML" {
  local file="$PROJECT_ROOT/.claude/agents/agatha.md"
  [ -f "$file" ]

  local frontmatter
  frontmatter=$(extract_frontmatter "$file")

  if command -v python3 &>/dev/null; then
    echo "$frontmatter" | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)"
  else
    echo "$frontmatter" | grep -qE '^[a-zA-Z_]+:'
  fi
}

# ═══════════════════════════════════════════════════════════════════════
# Step 4: Shared Preamble and Output Boilerplate Update
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-062: Happy -- agent-preamble.md step 4 references mcpServers ──

@test "T-0021-062: .claude/references/agent-preamble.md step 4 contains mcpServers or mcpServers: atelier-brain" {
  local file="$PROJECT_ROOT/.claude/references/agent-preamble.md"
  [ -f "$file" ]
  grep -qi "mcpServers" "$file"
}

# ── T-0021-063: Happy -- source preamble matches .claude preamble ──

@test "T-0021-063: source/references/agent-preamble.md matches .claude/references/agent-preamble.md" {
  local claude_file="$PROJECT_ROOT/.claude/references/agent-preamble.md"
  local source_file="$PROJECT_ROOT/source/references/agent-preamble.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]
  compare_with_placeholder_resolution "$claude_file" "$source_file"
}

# ── T-0021-064: Regression -- agent-preamble.md still has steps 1-5 in order ──

@test "T-0021-064: agent-preamble.md still contains DoR, upstream, retro, brain, DoD steps in order" {
  local file="$PROJECT_ROOT/.claude/references/agent-preamble.md"
  [ -f "$file" ]

  # Verify key step landmarks exist
  grep -q "DoR first" "$file"
  grep -q "upstream artifacts" "$file"
  grep -q "retro lessons" "$file"
  grep -qi "brain context" "$file"
  grep -q "DoD last" "$file"

  # Verify ordering: DoR before DoD
  local dor_line dod_line
  dor_line=$(grep -n "DoR first" "$file" | head -1 | cut -d: -f1)
  dod_line=$(grep -n "DoD last" "$file" | head -1 | cut -d: -f1)
  [ "$dor_line" -lt "$dod_line" ]
}

# ── T-0021-065: Regression -- Ellis output no longer has old brain line ──

@test "T-0021-065: .claude/agents/ellis.md does NOT contain Eva uses these to capture knowledge to the brain" {
  local file="$PROJECT_ROOT/.claude/agents/ellis.md"
  [ -f "$file" ]

  # This exact string should have been replaced with updated phrasing
  ! grep -qF "Eva uses these to capture knowledge to the brain" "$file"
}

# ── T-0021-066: Boundary -- invocation-templates.md references both brain-context and agent_capture ──

@test "T-0021-066: .claude/references/invocation-templates.md references brain-context and agent_capture as distinct operations" {
  local file="$PROJECT_ROOT/.claude/references/invocation-templates.md"
  [ -f "$file" ]

  # The file header/preamble (first 60 lines) should reference both concepts
  # after Step 4 updates the brain-context tag documentation
  head -60 "$file" | grep -qi "brain-context"
  grep -qi "agent_capture\|capture directly\|capture independently" "$file"
}

# ── T-0021-067: Regression -- source invocation-templates matches .claude ──

@test "T-0021-067: source/references/invocation-templates.md matches .claude/references/invocation-templates.md" {
  local claude_file="$PROJECT_ROOT/.claude/references/invocation-templates.md"
  local source_file="$PROJECT_ROOT/source/references/invocation-templates.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]
  compare_with_placeholder_resolution "$claude_file" "$source_file"
}

# ── T-0021-118: Failure -- preamble step 4 updated from Eva-only framing ──

@test "T-0021-118: agent-preamble.md step 4 does NOT contain they do not call agent_search themselves as sole brain instruction" {
  local file="$PROJECT_ROOT/.claude/references/agent-preamble.md"
  [ -f "$file" ]

  # The old Eva-only framing should be updated to reflect hybrid model
  # If this exact phrase still exists as the ONLY brain instruction, preamble was not updated
  if grep -qF "they do not call agent_search themselves" "$file"; then
    # The phrase exists -- check that it's not the sole instruction
    # (there should also be references to agents capturing directly)
    grep -qi "capture directly\|mcpServers\|agent_capture\|brain access" "$file"
  fi
}

# ── T-0021-119: Failure -- Ellis output still mentions brain (line updated, not deleted) ──

@test "T-0021-119: .claude/agents/ellis.md output section still contains the word brain" {
  local file="$PROJECT_ROOT/.claude/agents/ellis.md"
  [ -f "$file" ]

  # The brain line was updated (not deleted), so "brain" should still appear
  grep -qi "brain" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 5a: Dead Prose Cleanup -- agent-system.md + pipeline-orchestration.md
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-068: Happy -- agent-system.md Brain Config references mcpServers ──

@test "T-0021-068: .claude/rules/agent-system.md Brain Configuration section references mcpServers: atelier-brain" {
  local file="$PROJECT_ROOT/.claude/rules/agent-system.md"
  [ -f "$file" ]

  # Extract the brain-config section and check for mcpServers
  sed -n '/<section id="brain-config">/,/<\/section>/p' "$file" | grep -qi "mcpServers.*atelier-brain\|mcpServers: atelier-brain"
}

# ── T-0021-069: Happy -- agent-system.md Brain Config names the four brain-access agents ──

@test "T-0021-069: .claude/rules/agent-system.md Brain Configuration names Cal, Colby, Roz, Agatha" {
  local file="$PROJECT_ROOT/.claude/rules/agent-system.md"
  [ -f "$file" ]

  local brain_section
  brain_section=$(sed -n '/<section id="brain-config">/,/<\/section>/p' "$file")

  echo "$brain_section" | grep -qi "Cal"
  echo "$brain_section" | grep -qi "Colby"
  echo "$brain_section" | grep -qi "Roz"
  echo "$brain_section" | grep -qi "Agatha"
}

# ── T-0021-070: Happy -- agent-system.md Brain Config references both prompt hook scripts ──

@test "T-0021-070: .claude/rules/agent-system.md Brain Configuration references prompt-brain-prefetch.sh and prompt-brain-capture.sh" {
  local file="$PROJECT_ROOT/.claude/rules/agent-system.md"
  [ -f "$file" ]

  local brain_section
  brain_section=$(sed -n '/<section id="brain-config">/,/<\/section>/p' "$file")

  echo "$brain_section" | grep -q "prompt-brain-prefetch.sh"
  echo "$brain_section" | grep -q "prompt-brain-capture.sh"
}

# ── T-0021-071: Happy -- pipeline-orchestration.md Brain Access heading has no MANDATORY ──

@test "T-0021-071: .claude/rules/pipeline-orchestration.md Brain Access heading does NOT contain MANDATORY" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  [ -f "$file" ]

  # The heading line for Brain Access should not contain MANDATORY
  ! grep -q "Brain Access.*MANDATORY\|MANDATORY.*Brain Access" "$file"
}

# ── T-0021-072: Happy -- pipeline-orchestration.md Brain Access contains best-effort ──

@test "T-0021-072: .claude/rules/pipeline-orchestration.md Brain Access section contains best-effort for Eva cross-cutting" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  [ -f "$file" ]

  grep -qi "best-effort" "$file"
}

# ── T-0021-073: Happy -- pipeline-orchestration.md has no Verification (spot-check) ──

@test "T-0021-073: .claude/rules/pipeline-orchestration.md does NOT contain Verification spot-check subsection" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  [ -f "$file" ]

  ! grep -qi "Verification (spot-check\|Verification.*spot.check" "$file"
}

# ── T-0021-074: Happy -- pipeline-orchestration.md Brain Access references agent personas ──

@test "T-0021-074: .claude/rules/pipeline-orchestration.md Brain Access section references agent personas for domain-specific capture gates" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  [ -f "$file" ]

  grep -qi "agent persona\|agent personas\|mcpServers: atelier-brain" "$file"
}

# ── T-0021-075: Regression -- agent-system.md Shared Agent Behaviors still lists brain context ──

@test "T-0021-075: .claude/rules/agent-system.md Shared Agent Behaviors still lists brain context consumption" {
  local file="$PROJECT_ROOT/.claude/rules/agent-system.md"
  [ -f "$file" ]

  local shared_section
  shared_section=$(sed -n '/<section id="shared-behaviors">/,/<\/section>/p' "$file")

  echo "$shared_section" | grep -qi "brain context"
}

# ── T-0021-076: Regression -- pipeline-orchestration.md preserves Seed Capture and /devops Capture Gates ──

@test "T-0021-076: .claude/rules/pipeline-orchestration.md preserves Seed Capture and devops Capture Gates subsections" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  [ -f "$file" ]

  grep -q "Seed Capture" "$file"
  grep -q "devops Capture Gates\|/devops Capture Gates" "$file"
}

# ── T-0021-077: Regression -- pipeline-orchestration.md Telemetry Tier 1 section preserved ──

@test "T-0021-077: .claude/rules/pipeline-orchestration.md Telemetry Tier 1 section is preserved" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  [ -f "$file" ]

  grep -qi "Tier 1" "$file"
}

# ── T-0021-078: Boundary -- source agent-system.md matches .claude copy ──

@test "T-0021-078: source/rules/agent-system.md matches .claude/rules/agent-system.md for modified brain sections" {
  local claude_file="$PROJECT_ROOT/.claude/rules/agent-system.md"
  local source_file="$PROJECT_ROOT/source/rules/agent-system.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]

  # Extract brain-config sections from both
  local claude_section source_section
  claude_section=$(sed -n '/<section id="brain-config">/,/<\/section>/p' "$claude_file")
  source_section=$(sed -n '/<section id="brain-config">/,/<\/section>/p' "$source_file")

  [ "$claude_section" = "$source_section" ]
}

# ── T-0021-079: Boundary -- source pipeline-orchestration.md matches .claude copy ──

@test "T-0021-079: source/rules/pipeline-orchestration.md matches .claude/rules/pipeline-orchestration.md for Brain Access section" {
  local claude_file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  local source_file="$PROJECT_ROOT/source/rules/pipeline-orchestration.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]

  # Check that the Brain Access heading treatment matches
  local claude_heading source_heading
  claude_heading=$(grep "Brain Access" "$claude_file" | head -1)
  source_heading=$(grep "Brain Access" "$source_file" | head -1)

  [ "$claude_heading" = "$source_heading" ]
}

# ── T-0021-080: Regression -- pipeline-orchestration.md Telemetry Capture heading has no MANDATORY ──

@test "T-0021-080: .claude/rules/pipeline-orchestration.md Telemetry Capture heading does NOT contain MANDATORY" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  [ -f "$file" ]

  ! grep -q "Telemetry Capture.*MANDATORY\|MANDATORY.*Telemetry Capture\|Telemetry Capture Protocol.*MANDATORY" "$file"
}

# ── T-0021-111: Failure -- Seed Capture heading preserved ──

@test "T-0021-111: .claude/rules/pipeline-orchestration.md still contains the heading Seed Capture" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  [ -f "$file" ]
  grep -q "Seed Capture" "$file"
}

# ── T-0021-112: Failure -- /devops Capture Gates heading preserved ──

@test "T-0021-112: .claude/rules/pipeline-orchestration.md still contains devops Capture Gates heading" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
  [ -f "$file" ]
  grep -q "devops Capture Gates\|/devops Capture Gates" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 5b: Dead Prose Cleanup -- default-persona.md, pipeline-models.md,
#          pipeline-operations.md
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-081: Happy -- default-persona.md context eviction retention includes brain capture ──

@test "T-0021-081: .claude/rules/default-persona.md context eviction retention list includes brain capture protocol awareness" {
  local file="$PROJECT_ROOT/.claude/rules/default-persona.md"
  [ -f "$file" ]

  grep -qi "brain capture protocol\|brain capture.*awareness\|brain.*protocol.*awareness" "$file"
}

# ── T-0021-082: Happy -- default-persona.md context eviction does NOT evict telemetry trend logic ──

@test "T-0021-082: .claude/rules/default-persona.md context eviction does NOT contain Telemetry trend computation logic as eviction target" {
  local file="$PROJECT_ROOT/.claude/rules/default-persona.md"
  [ -f "$file" ]

  # The eviction section should not list this as something to evict
  ! grep -q "Telemetry trend computation logic" "$file"
}

# ── T-0021-083: Happy -- default-persona.md Brain Access section references hooks and frontmatter ──

@test "T-0021-083: .claude/rules/default-persona.md Brain Access or brain section references hooks and agent frontmatter" {
  local file="$PROJECT_ROOT/.claude/rules/default-persona.md"
  [ -f "$file" ]

  # After Step 5b, the brain section should reference prompt-brain hooks or mcpServers frontmatter
  grep -qi "prompt-brain\|mcpServers\|frontmatter.*brain\|brain.*frontmatter" "$file"
}

# ── T-0021-084: Happy -- pipeline-models.md Brain Integration contains best-effort ──

@test "T-0021-084: .claude/rules/pipeline-models.md Brain Integration subsection contains best-effort" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-models.md"
  [ -f "$file" ]

  grep -qi "best-effort" "$file"
}

# ── T-0021-085: Happy -- pipeline-operations.md brain prefetch references prompt hook ──

@test "T-0021-085: .claude/references/pipeline-operations.md brain prefetch protocol references prompt-brain-prefetch.sh" {
  local file="$PROJECT_ROOT/.claude/references/pipeline-operations.md"
  [ -f "$file" ]

  grep -q "prompt-brain-prefetch.sh" "$file"
}

# ── T-0021-086: Happy -- pipeline-operations.md brain prefetch references hybrid model ──

@test "T-0021-086: .claude/references/pipeline-operations.md brain prefetch protocol references hybrid model or agent self-capture" {
  local file="$PROJECT_ROOT/.claude/references/pipeline-operations.md"
  [ -f "$file" ]

  grep -qi "hybrid\|agents with brain access\|capture directly\|self-capture\|agents.*capture" "$file"
}

# ── T-0021-087: Regression -- default-persona.md boot sequence steps 4-5 preserved ──

@test "T-0021-087: .claude/rules/default-persona.md boot sequence steps 4 (brain health check) and 5 (context retrieval) are preserved" {
  local file="$PROJECT_ROOT/.claude/rules/default-persona.md"
  [ -f "$file" ]

  grep -q "Brain health check" "$file"
  grep -qi "Brain context retrieval\|context retrieval" "$file"
}

# ── T-0021-088: Regression -- pipeline-models.md model tables unmodified ──

@test "T-0021-088: .claude/rules/pipeline-models.md model tables are unmodified (contains Opus, Sonnet, Haiku)" {
  local file="$PROJECT_ROOT/.claude/rules/pipeline-models.md"
  [ -f "$file" ]

  grep -qi "opus" "$file"
  grep -qi "sonnet" "$file"
  grep -qi "haiku" "$file"
}

# ── T-0021-089: Boundary -- source default-persona.md matches .claude copy ──

@test "T-0021-089: source/rules/default-persona.md matches .claude/rules/default-persona.md for modified sections" {
  local claude_file="$PROJECT_ROOT/.claude/rules/default-persona.md"
  local source_file="$PROJECT_ROOT/source/rules/default-persona.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]

  # Check that context eviction sections match
  local claude_eviction source_eviction
  claude_eviction=$(sed -n '/<protocol id="context-eviction">/,/<\/protocol>/p' "$claude_file")
  source_eviction=$(sed -n '/<protocol id="context-eviction">/,/<\/protocol>/p' "$source_file")

  [ "$claude_eviction" = "$source_eviction" ]
}

# ── T-0021-090: Boundary -- source pipeline-models.md matches .claude copy ──

@test "T-0021-090: source/rules/pipeline-models.md matches .claude/rules/pipeline-models.md for brain integration section" {
  local claude_file="$PROJECT_ROOT/.claude/rules/pipeline-models.md"
  local source_file="$PROJECT_ROOT/source/rules/pipeline-models.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]

  # Check that Brain Integration sections match
  local claude_brain source_brain
  claude_brain=$(grep -A5 "Brain Integration" "$claude_file")
  source_brain=$(grep -A5 "Brain Integration" "$source_file")

  [ "$claude_brain" = "$source_brain" ]
}

# ── T-0021-091: Boundary -- source pipeline-operations.md matches .claude copy ──

@test "T-0021-091: source/references/pipeline-operations.md matches .claude/references/pipeline-operations.md for brain prefetch section" {
  local claude_file="$PROJECT_ROOT/.claude/references/pipeline-operations.md"
  local source_file="$PROJECT_ROOT/source/references/pipeline-operations.md"
  [ -f "$claude_file" ]
  [ -f "$source_file" ]

  # Check that brain prefetch protocol sections match
  local claude_prefetch source_prefetch
  claude_prefetch=$(sed -n '/<protocol id="brain-prefetch">/,/<\/protocol>/p' "$claude_file")
  source_prefetch=$(sed -n '/<protocol id="brain-prefetch">/,/<\/protocol>/p' "$source_file")

  [ "$claude_prefetch" = "$source_prefetch" ]
}

# ── T-0021-113: Failure -- boot sequence steps 4 and 5 still have atelier_stats and agent_search ──

@test "T-0021-113: .claude/rules/default-persona.md boot sequence steps 4 and 5 still reference atelier_stats and agent_search" {
  local file="$PROJECT_ROOT/.claude/rules/default-persona.md"
  [ -f "$file" ]

  # These are operational boot steps, not dead prose -- must be preserved
  grep -q "atelier_stats" "$file"
  grep -q "agent_search" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 6: PostCompact Hook Enhancement
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-092: Happy -- post-compact-reinject.sh outputs brain protocol reminder ──

@test "T-0021-092: post-compact-reinject.sh outputs a brain protocol reminder section after pipeline state content" {
  # Use neutral fixture content (no brain-related words) so we can verify
  # the hook itself adds the brain reminder section
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

Feature: Hook modernization
Phase: build
EOF

  cat > "$TEST_TMPDIR/docs/pipeline/context-brief.md" << 'EOF'
# Context

Working on hook changes.
EOF

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # Output must contain the existing content (regression check)
  [[ "$output" == *"Pipeline State"* ]]

  # Output must ALSO contain a brain protocol reminder (new content from Step 6)
  # The hook should add brain-related reminder text beyond what's in the fixtures
  [[ "$output" == *"[Bb]rain"* ]] || [[ "$output" == *"brain"* ]] || [[ "$output" == *"Brain"* ]] || [[ "$output" == *"capture"* ]]
}

# ── T-0021-093: Happy -- brain reminder mentions three mechanisms ──

@test "T-0021-093: post-compact-reinject.sh brain reminder mentions prompt hooks, agent captures, Eva cross-cutting" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

Feature: Hook modernization
EOF

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # Must mention prompt hooks (or hook-related terms)
  [[ "$output" == *"prompt"* ]] || [[ "$output" == *"hook"* ]]

  # Must mention agent captures (cal/colby/roz/agatha or "agent capture")
  [[ "$output" == *"agent"* ]] || [[ "$output" == *"capture"* ]]

  # Must mention Eva cross-cutting or best-effort
  [[ "$output" == *"Eva"* ]] || [[ "$output" == *"best-effort"* ]] || [[ "$output" == *"cross-cutting"* ]]
}

# ── T-0021-094: Boundary -- brain reminder is less than 10 lines ──

@test "T-0021-094: post-compact-reinject.sh brain protocol reminder is less than 10 lines" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

Feature: Hook modernization
EOF

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # Count lines that are part of the brain reminder section
  # Look for lines containing brain/capture/prompt/hook keywords as part of the reminder
  local brain_lines
  brain_lines=$(echo "$output" | grep -ic "brain\|capture.*agent\|agent.*capture\|prompt.*hook\|hook.*prompt\|best.effort\|cross.cutting" || echo "0")

  # The brain reminder section itself should be concise -- less than 10 lines
  [ "$brain_lines" -lt 10 ]
}

# ── T-0021-095: Regression -- still outputs pipeline-state and context-brief before brain reminder ──

@test "T-0021-095: post-compact-reinject.sh still outputs pipeline-state.md and context-brief.md before brain reminder" {
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State

Feature: Hook modernization
EOF

  cat > "$TEST_TMPDIR/docs/pipeline/context-brief.md" << 'EOF'
# Context Brief

Working on hook modernization.
EOF

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # Existing functionality preserved
  [[ "$output" == *"Pipeline State"* ]]
  [[ "$output" == *"Context Brief"* ]]
  [[ "$output" == *"Re-injected after compaction"* ]]
}

# ── T-0021-096: Regression -- exits 0 in all code paths ──

@test "T-0021-096: post-compact-reinject.sh exits 0 in all code paths with brain reminder" {
  # Test with pipeline-state.md present
  cat > "$TEST_TMPDIR/docs/pipeline/pipeline-state.md" << 'EOF'
# Pipeline State
EOF
  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # Test without pipeline-state.md
  rm -f "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"
  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]

  # Test without CLAUDE_PROJECT_DIR
  run run_hook_without_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]
}

# ── T-0021-097: Error -- handles missing pipeline-state.md gracefully ──

@test "T-0021-097: post-compact-reinject.sh exits 0 with no brain reminder when pipeline-state.md missing" {
  rm -f "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── T-0021-098: Boundary -- source post-compact-reinject.sh matches .claude copy ──

@test "T-0021-098: source/hooks/post-compact-reinject.sh matches .claude/hooks/post-compact-reinject.sh" {
  local source_file="$PROJECT_ROOT/source/hooks/post-compact-reinject.sh"
  local installed_file="$PROJECT_ROOT/.claude/hooks/post-compact-reinject.sh"
  [ -f "$source_file" ]
  [ -f "$installed_file" ]
  cmp -s "$source_file" "$installed_file"
}

# ── T-0021-114: Failure -- no brain reminder when pipeline-state.md absent ──

@test "T-0021-114: post-compact-reinject.sh does NOT output brain reminder when pipeline-state.md does not exist" {
  rm -f "$TEST_TMPDIR/docs/pipeline/pipeline-state.md"

  run run_hook_with_project_dir "post-compact-reinject.sh" ""
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ═══════════════════════════════════════════════════════════════════════
# Cross-Step Tests
# ═══════════════════════════════════════════════════════════════════════

# ── T-0021-108: Boundary -- read-only agents do NOT have mcpServers in frontmatter ──

@test "T-0021-108: none of the read-only agent files contain mcpServers in YAML frontmatter" {
  local readonly_agents=(
    "$PROJECT_ROOT/.claude/agents/robert.md"
    "$PROJECT_ROOT/.claude/agents/sable.md"
    "$PROJECT_ROOT/.claude/agents/investigator.md"
    "$PROJECT_ROOT/.claude/agents/distillator.md"
    "$PROJECT_ROOT/.claude/agents/darwin.md"
    "$PROJECT_ROOT/.claude/agents/deps.md"
    "$PROJECT_ROOT/.claude/agents/sentinel.md"
    "$PROJECT_ROOT/.claude/agents/ellis.md"
  )

  local violations=0
  for agent_file in "${readonly_agents[@]}"; do
    if [ -f "$agent_file" ]; then
      local frontmatter
      frontmatter=$(extract_frontmatter "$agent_file")
      if echo "$frontmatter" | grep -q "mcpServers"; then
        echo "VIOLATION: $(basename "$agent_file") has mcpServers in frontmatter" >&2
        violations=$((violations + 1))
      fi
    fi
  done

  [ "$violations" -eq 0 ]
}
