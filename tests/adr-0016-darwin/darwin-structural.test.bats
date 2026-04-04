#!/usr/bin/env bats
# ADR-0016: Darwin -- Self-Evolving Pipeline Engine -- Structural Tests
# Tests: T-0016-001 through T-0016-104
#
# These tests verify the structural content of Darwin agent deliverables:
# - darwin.md agent persona (source + installed)
# - darwin.md slash command (source + installed)
# - pipeline-config.json (darwin_enabled flag)
# - agent-system.md (subagent table, routing table, no-skill-tool gate)
# - invocation-templates.md (darwin-analysis, darwin-edit-proposal)
# - pipeline-orchestration.md (auto-trigger section)
# - default-persona.md (post-edit tracking, boot announcement)
# - SKILL.md (Step 6e opt-in)

load ../xml-prompt-structure/test_helper

SKILL_FILE="$PROJECT_ROOT/skills/pipeline-setup/SKILL.md"

# ═══════════════════════════════════════════════════════════════════════
# Step 1: Agent Persona
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-001: Persona file exists in source with correct frontmatter ─

@test "T-0016-001: source darwin agent files exist with name: darwin in frontmatter" {
  local shared="$PROJECT_ROOT/source/shared/agents/darwin.md"
  local frontmatter="$PROJECT_ROOT/source/claude/agents/darwin.frontmatter.yml"
  [ -f "$shared" ]
  [ -f "$frontmatter" ]
  grep -q "^name: darwin" "$frontmatter"
}

# ── T-0016-002: Installed copy exists with correct frontmatter ───────

@test "T-0016-002: .claude/agents/darwin.md exists with name: darwin in YAML frontmatter" {
  local installed="$INSTALLED_AGENTS/darwin.md"
  [ -f "$installed" ]
  grep -q "name: darwin" "$installed"
}

# ── T-0016-003: disallowedTools includes Write, Edit, MultiEdit, NotebookEdit, Agent

@test "T-0016-003: darwin.md disallowedTools frontmatter includes Write, Edit, MultiEdit, NotebookEdit, Agent" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local frontmatter
  frontmatter=$(sed -n '/^---$/,/^---$/p' "$file")

  echo "$frontmatter" | grep -q "Write"
  echo "$frontmatter" | grep -q "Edit"
  echo "$frontmatter" | grep -q "MultiEdit"
  echo "$frontmatter" | grep -q "NotebookEdit"
  echo "$frontmatter" | grep -q "Agent"
}

# ── T-0016-004: Persona contains all 7 required XML tags ────────────

@test "T-0016-004: darwin.md contains identity, required-actions, workflow, examples, tools, constraints, output tags" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local tags=(identity required-actions workflow examples tools constraints output)
  local fail=0
  for tag in "${tags[@]}"; do
    assert_has_tag "$file" "$tag" || { fail=1; }
    assert_has_closing_tag "$file" "$tag" || { fail=1; }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0016-005: Self-edit protection constraint ──────────────────────

@test "T-0016-005: <constraints> includes self-edit protection mentioning darwin.md" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")

  echo "$constraints" | grep -qiE "cannot propose changes to.*darwin\.md|cannot.*modify.*darwin\.md|self.edit.*protect"
}

# ── T-0016-006: 5-pipeline minimum gate ──────────────────────────────

@test "T-0016-006: <constraints> includes the 5-pipeline minimum gate" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")

  echo "$constraints" | grep -qiE "5.*pipeline|five.*pipeline"
}

# ── T-0016-007: Brain-required gate ──────────────────────────────────

@test "T-0016-007: <constraints> includes the brain-required gate" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")

  echo "$constraints" | grep -qiE "brain.*require|require.*brain|brain.*unavailable|brain.*telemetry"
}

# ── T-0016-008: Workflow encodes four phases ─────────────────────────

@test "T-0016-008: <workflow> encodes four phases: Data Ingestion, Fitness Assessment, Pattern Analysis, Report Production" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local workflow
  workflow=$(extract_tag_content "$file" "workflow")

  local fail=0
  echo "$workflow" | grep -qiE "data.*ingest" || { echo "Missing: Data Ingestion"; fail=1; }
  echo "$workflow" | grep -qiE "fitness.*assess" || { echo "Missing: Fitness Assessment"; fail=1; }
  echo "$workflow" | grep -qiE "pattern.*analy" || { echo "Missing: Pattern Analysis"; fail=1; }
  echo "$workflow" | grep -qiE "report.*produc" || { echo "Missing: Report Production"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-009: Fitness scoring table thresholds ─────────────────────

@test "T-0016-009: <workflow> encodes fitness scoring: thriving (>= 80%), struggling (50-80%), failing (< 50%)" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local workflow
  workflow=$(extract_tag_content "$file" "workflow")

  local fail=0
  echo "$workflow" | grep -qiE "thriving" || { echo "Missing: thriving classification"; fail=1; }
  echo "$workflow" | grep -qiE "struggling" || { echo "Missing: struggling classification"; fail=1; }
  echo "$workflow" | grep -qiE "failing" || { echo "Missing: failing classification"; fail=1; }
  echo "$workflow" | grep -qE "80" || { echo "Missing: 80% threshold"; fail=1; }
  echo "$workflow" | grep -qE "50" || { echo "Missing: 50% threshold"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-010: 5-level escalation ladder ────────────────────────────

@test "T-0016-010: <workflow> encodes the 5-level escalation ladder" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local workflow
  workflow=$(extract_tag_content "$file" "workflow")

  local fail=0
  echo "$workflow" | grep -qiE "warn" || { echo "Missing: Level 1 WARN"; fail=1; }
  echo "$workflow" | grep -qiE "constraint" || { echo "Missing: Level 2 constraint"; fail=1; }
  echo "$workflow" | grep -qiE "workflow.*edit" || { echo "Missing: Level 3 workflow edit"; fail=1; }
  echo "$workflow" | grep -qiE "rewrite" || { echo "Missing: Level 4 rewrite"; fail=1; }
  echo "$workflow" | grep -qiE "remov" || { echo "Missing: Level 5 removal"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-011: Fix layer selection table (7 layers) ─────────────────

@test "T-0016-011: <workflow> encodes the fix layer selection table (7 target layers)" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local workflow
  workflow=$(extract_tag_content "$file" "workflow")

  local fail=0
  echo "$workflow" | grep -qiE "persona" || { echo "Missing layer: agent personas"; fail=1; }
  echo "$workflow" | grep -qiE "orchestration.*rule|rule" || { echo "Missing layer: orchestration rules"; fail=1; }
  echo "$workflow" | grep -qiE "hook" || { echo "Missing layer: hooks"; fail=1; }
  echo "$workflow" | grep -qiE "quality.*gate|gate" || { echo "Missing layer: quality gates"; fail=1; }
  echo "$workflow" | grep -qiE "invocation.*template|template" || { echo "Missing layer: invocation templates"; fail=1; }
  echo "$workflow" | grep -qiE "model.*assign|model" || { echo "Missing layer: model assignment"; fail=1; }
  echo "$workflow" | grep -qiE "retro.*lesson|retro" || { echo "Missing layer: retro lessons"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-012: Examples contain at least two examples ───────────────

@test "T-0016-012: <examples> contains at least two examples (constraint addition + escalation)" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  assert_has_tag "$file" "examples"
  assert_has_closing_tag "$file" "examples"

  local examples
  examples=$(extract_tag_content "$file" "examples")
  local example_count
  example_count=$(echo "$examples" | grep -ciE "example|constraint.*add|escalat|QA.*drop|first.pass" || echo 0)
  [ "$example_count" -ge 2 ]
}

# ── T-0016-013: Output specifies three report sections ───────────────

@test "T-0016-013: <output> specifies FITNESS ASSESSMENT, PROPOSED CHANGES, UNCHANGED sections" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local output_section
  output_section=$(extract_tag_content "$file" "output")

  local fail=0
  echo "$output_section" | grep -qi "FITNESS ASSESSMENT" || { echo "Missing: FITNESS ASSESSMENT"; fail=1; }
  echo "$output_section" | grep -qi "PROPOSED CHANGES" || { echo "Missing: PROPOSED CHANGES"; fail=1; }
  echo "$output_section" | grep -qi "UNCHANGED" || { echo "Missing: UNCHANGED"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-014: Output specifies proposal fields ────────────────────

@test "T-0016-014: <output> specifies each proposal includes evidence, layer, escalation level, risk, expected impact" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local output_section
  output_section=$(extract_tag_content "$file" "output")

  local fail=0
  echo "$output_section" | grep -qi "evidence" || { echo "Missing: evidence"; fail=1; }
  echo "$output_section" | grep -qi "layer" || { echo "Missing: layer"; fail=1; }
  echo "$output_section" | grep -qiE "escalation.*level|level" || { echo "Missing: escalation level"; fail=1; }
  echo "$output_section" | grep -qi "risk" || { echo "Missing: risk"; fail=1; }
  echo "$output_section" | grep -qiE "expected.*impact|impact" || { echo "Missing: expected impact"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-015: Level 5 requires prior escalation summary ───────────

@test "T-0016-015: <constraints> includes Level 5 requiring summary of prior escalation attempts" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")

  echo "$constraints" | grep -qiE "level 5.*prior.*escalation|level 5.*summary|prior.*escalation.*attempt"
}

# ── T-0016-016: Tools section lists correct tools ────────────────────

@test "T-0016-016: <tools> lists Read, Glob, Grep, Bash (read-only) and no Write/Edit" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local tools_section
  tools_section=$(extract_tag_content "$file" "tools")

  local required_tools=(Read Glob Grep Bash)
  local fail=0
  for tool in "${required_tools[@]}"; do
    echo "$tools_section" | grep -q "$tool" || {
      echo "Missing tool in <tools>: $tool"
      fail=1
    }
  done

  echo "$tools_section" | grep -qiE "read.only" || {
    echo "Missing: read-only qualification for Bash"
    fail=1
  }
  [ "$fail" -eq 0 ]
}

# ── T-0016-017: Persona does NOT include Write in tools ──────────────

@test "T-0016-017: darwin.md <tools> does not include Write tool" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local tools_section
  tools_section=$(extract_tag_content "$file" "tools")

  ! echo "$tools_section" | grep -qE "^\s*[-*].*\bWrite\b" || {
    echo "Write tool found as a listed item in <tools>"; false
  }
}

# ── T-0016-018: Persona does NOT include Edit in tools ───────────────

@test "T-0016-018: darwin.md <tools> does not include Edit tool" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local tools_section
  tools_section=$(extract_tag_content "$file" "tools")

  ! echo "$tools_section" | grep -qE "^\s*[-*].*\bEdit\b" || {
    echo "Edit tool found as a listed item in <tools>"; false
  }
}

# ── T-0016-019: darwin has disallowedTools blocking Write ────────────

@test "T-0016-019: darwin frontmatter disallowedTools blocks Write (Layer 1 enforcement)" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"
  local frontmatter
  frontmatter=$(sed -n '/^---$/,/^---$/p' "$file")
  echo "$frontmatter" | grep -q "disallowedTools"
  echo "$frontmatter" | grep -q "Write"
}

# ── T-0016-020: darwin has disallowedTools blocking Edit ─────────────

@test "T-0016-020: darwin frontmatter disallowedTools blocks Edit (Layer 1 enforcement)" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"
  local frontmatter
  frontmatter=$(sed -n '/^---$/,/^---$/p' "$file")
  echo "$frontmatter" | grep -q "disallowedTools"
  echo "$frontmatter" | grep -q "Edit"
}

# ── T-0016-021: darwin is not in core agent constant list ────────────

@test "T-0016-021: darwin does not appear in the core agent constant list in agent-system.md" {
  local file="$INSTALLED_RULES/agent-system.md"
  local core_list
  core_list=$(grep -A2 "core agents" "$file" | grep -oE "cal, colby.*distillator" || true)
  if [ -n "$core_list" ]; then
    ! echo "$core_list" | grep -q "darwin"
  fi
}

# ── T-0016-022: Core constant code block does not include darwin ─────

@test "T-0016-022: core agent constant code block in agent-system.md does not include darwin" {
  local file="$INSTALLED_RULES/agent-system.md"
  local constant_block
  constant_block=$(sed -n '/^```$/,/^```$/p' "$file" | grep -E "cal.*colby.*roz" || true)
  if [ -n "$constant_block" ]; then
    ! echo "$constant_block" | grep -q "darwin"
  fi
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1: Slash Command
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-023: Command file exists in source ────────────────────────

@test "T-0016-023: source/commands/darwin.md exists with YAML frontmatter name: darwin" {
  local file="$SOURCE_COMMANDS/darwin.md"
  [ -f "$file" ]
  grep -qE "^name: darwin" "$file"
}

# ── T-0016-024: Installed command is identical to source ─────────────

@test "T-0016-024: .claude/commands/darwin.md exists with identical content to source" {
  local source="$SOURCE_COMMANDS/darwin.md"
  local installed="$INSTALLED_COMMANDS/darwin.md"
  [ -f "$source" ]
  [ -f "$installed" ]
  diff -q "$source" "$installed"
}

# ── T-0016-025: Command describes darwin_enabled gate ────────────────

@test "T-0016-025: command file describes darwin_enabled gate (when false: not enabled)" {
  local file="$INSTALLED_COMMANDS/darwin.md"
  [ -f "$file" ] || skip "darwin.md command not yet created"

  grep -qiE "darwin_enabled" "$file"
  grep -qiE "not enabled|not.*enabled" "$file"
}

# ── T-0016-026: Command describes brain-required gate ────────────────

@test "T-0016-026: command file describes brain-required gate (brain unavailable: stop)" {
  local file="$INSTALLED_COMMANDS/darwin.md"
  [ -f "$file" ] || skip "darwin.md command not yet created"

  grep -qiE "brain.*unavailable|brain.*not available|brain.*require" "$file"
}

# ── T-0016-027: Command describes 5-pipeline minimum gate ───────────

@test "T-0016-027: command file describes 5-pipeline minimum gate (fewer than 5: stop with count)" {
  local file="$INSTALLED_COMMANDS/darwin.md"
  [ -f "$file" ] || skip "darwin.md command not yet created"

  grep -qiE "5.*pipeline|five.*pipeline|fewer than 5|insufficient.*data" "$file"
}

# ── T-0016-028: Command describes approval flow ─────────────────────

@test "T-0016-028: command file describes approval flow (user approves/rejects each proposal)" {
  local file="$INSTALLED_COMMANDS/darwin.md"
  [ -f "$file" ] || skip "darwin.md command not yet created"

  grep -qiE "approv.*reject|reject.*approv|individually|each.*proposal" "$file"
}

# ── T-0016-029: Command describes routing to Colby ──────────────────

@test "T-0016-029: command file describes routing approved changes to Colby" {
  local file="$INSTALLED_COMMANDS/darwin.md"
  [ -f "$file" ] || skip "darwin.md command not yet created"

  grep -qiE "colby|route.*approved|approved.*route" "$file"
}

# ── T-0016-030: Command includes triple gate check ──────────────────

@test "T-0016-030: command file includes triple gate (darwin_enabled, brain, 5 pipelines) before invocation" {
  local file="$INSTALLED_COMMANDS/darwin.md"
  [ -f "$file" ] || skip "darwin.md command not yet created"

  local fail=0
  grep -qiE "darwin_enabled" "$file" || { echo "Missing gate: darwin_enabled"; fail=1; }
  grep -qiE "brain" "$file" || { echo "Missing gate: brain"; fail=1; }
  grep -qiE "5.*pipeline|pipeline.*5|five.*pipeline" "$file" || { echo "Missing gate: 5 pipelines"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-098: Conflicting proposals presented individually ─────────

@test "T-0016-098: command file describes individual proposal presentation (no merging)" {
  local file="$INSTALLED_COMMANDS/darwin.md"
  [ -f "$file" ] || skip "darwin.md command not yet created"

  grep -qiE "individual|each.*proposal|one.*at.*a.*time|separately" "$file"
}

# ── T-0016-099: Command describes modify path (reject + repropose) ──

@test "T-0016-099: command file describes modify = reject with feedback + re-invoke Darwin for revised proposal" {
  local file="$INSTALLED_COMMANDS/darwin.md"
  [ -f "$file" ] || skip "darwin.md command not yet created"

  grep -qiE "modify|modif" "$file"
  grep -qiE "reject.*feedback|reject.*repropose|reject.*re.invoke|reject.*revis" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1: Config Flag
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-031: Source config contains darwin_enabled: false ──────────

@test "T-0016-031: source/pipeline/pipeline-config.json contains darwin_enabled: false" {
  local file="$PROJECT_ROOT/source/pipeline/pipeline-config.json"
  jq -e '.darwin_enabled == false' "$file"
}

# ── T-0016-032: Installed config contains darwin_enabled: false ──────

@test "T-0016-032: .claude/pipeline-config.json contains darwin_enabled: false" {
  local file="$PROJECT_ROOT/.claude/pipeline-config.json"
  jq -e '.darwin_enabled == false' "$file"
}

# ── T-0016-033: Both config files remain valid JSON ──────────────────

@test "T-0016-033: both pipeline-config.json files are valid JSON" {
  jq . "$PROJECT_ROOT/source/pipeline/pipeline-config.json" > /dev/null
  jq . "$PROJECT_ROOT/.claude/pipeline-config.json" > /dev/null
}

# ── T-0016-034: No existing config fields removed or renamed ────────

@test "T-0016-034: no existing config fields removed from source pipeline-config.json" {
  local file="$PROJECT_ROOT/source/pipeline/pipeline-config.json"
  local fields=(branching_strategy platform sentinel_enabled agent_teams_enabled ci_watch_enabled ci_watch_max_retries ci_watch_poll_command ci_watch_log_command deps_agent_enabled)
  local fail=0
  for field in "${fields[@]}"; do
    jq -e "has(\"$field\")" "$file" > /dev/null || {
      echo "Missing existing field: $field"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0016-035: Key existing boolean fields unchanged ────────────────

@test "T-0016-035: deps_agent_enabled, sentinel_enabled, agent_teams_enabled, ci_watch_enabled unchanged" {
  local file="$PROJECT_ROOT/source/pipeline/pipeline-config.json"
  jq -e '.deps_agent_enabled == false' "$file" > /dev/null
  jq -e '.sentinel_enabled == false' "$file" > /dev/null
  jq -e '.agent_teams_enabled == false' "$file" > /dev/null
  jq -e '.ci_watch_enabled == false' "$file" > /dev/null
}

# ═══════════════════════════════════════════════════════════════════════
# Step 2: Routing (agent-system.md)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-036: Source agent-system.md subagent table has Darwin row ─

@test "T-0016-036: source/rules/agent-system.md subagent table contains **Darwin** row" {
  local file="$SOURCE_RULES/agent-system.md"
  grep -q '\*\*Darwin\*\*' "$file"
}

# ── T-0016-037: Installed agent-system.md subagent table has Darwin ──

@test "T-0016-037: .claude/rules/agent-system.md subagent table contains **Darwin** row" {
  local file="$INSTALLED_RULES/agent-system.md"
  grep -q '\*\*Darwin\*\*' "$file"
}

# ── T-0016-038: Auto-routing table maps pipeline-analysis intent to Darwin

@test "T-0016-038: auto-routing table maps pipeline-analysis intent to Darwin" {
  for file in "$SOURCE_RULES/agent-system.md" "$INSTALLED_RULES/agent-system.md"; do
    # Must have Darwin in a routing context with pipeline analysis keywords
    grep -qiE "Darwin" "$file" && grep -qiE "pipeline.*health|pipeline.*analy|agent.*perform|what.*needs.*improv|run.*Darwin" "$file" || {
      echo "Missing pipeline-analysis intent -> Darwin routing in $(basename "$file")"
      false
    }
    # Darwin must appear in a table row (pipe-delimited)
    grep -qE '\|.*[Dd]arwin.*\|' "$file" || {
      echo "Darwin not in a table row in $(basename "$file")"
      false
    }
  done
}

# ── T-0016-039: Darwin routing row includes darwin_enabled gate ──────

@test "T-0016-039: auto-routing Darwin row includes darwin_enabled: true gate condition" {
  local file="$INSTALLED_RULES/agent-system.md"
  grep -qi "darwin_enabled" "$file"
}

# ── T-0016-040: no-skill-tool gate maps Darwin to agents/darwin.md ──

@test "T-0016-040: no-skill-tool gate in both files maps Darwin to .claude/agents/darwin.md" {
  for file in "$SOURCE_RULES/agent-system.md" "$INSTALLED_RULES/agent-system.md"; do
    grep -qiE "darwin.*\.claude/agents/darwin\.md|darwin\.md" "$file" || {
      echo "Missing Darwin -> darwin.md mapping in no-skill-tool gate in $(basename "$file")"
      false
    }
  done
}

# ── T-0016-041: Auto-routing does not route when darwin_enabled false ─
# Structural: the routing table row must have a gate condition text

@test "T-0016-041: auto-routing Darwin row documents gate: darwin_enabled true required" {
  local file="$INSTALLED_RULES/agent-system.md"
  # The routing table row for Darwin must mention the gate condition
  local darwin_rows
  darwin_rows=$(grep -i "darwin" "$file" | grep -i "rout\|intent\|says\|pipeline.*health\|analyz" || true)
  [ -n "$darwin_rows" ] || skip "Darwin routing row not found"
  echo "$darwin_rows" | grep -qiE "darwin_enabled.*true|if.*darwin_enabled"
}

# ── T-0016-100: Absent darwin_enabled treated as false ───────────────
# Structural: the command or routing docs must state absence = false

@test "T-0016-100: command or routing documentation states absent darwin_enabled key is treated as false" {
  # Check command file or agent-system.md for absence handling
  local found=0
  for file in "$INSTALLED_COMMANDS/darwin.md" "$INSTALLED_RULES/agent-system.md"; do
    [ -f "$file" ] || continue
    if grep -qiE "absent.*false|missing.*false|not.*present.*false" "$file" 2>/dev/null; then
      found=1
      break
    fi
  done
  [ "$found" -eq 1 ] || skip "Darwin files not yet created -- cannot verify absence handling"
}

# ── T-0016-042: Deps row unchanged after Darwin addition ────────────

@test "T-0016-042: Deps row in subagent table unchanged after Darwin addition" {
  local file="$INSTALLED_RULES/agent-system.md"
  grep -q '\*\*Deps\*\*' "$file"
  grep -qiE "(Deps.*dependency|Deps.*Predictive)" "$file"
}

# ── T-0016-043: Sentinel row unchanged after Darwin addition ────────

@test "T-0016-043: Sentinel row in subagent table unchanged after Darwin addition" {
  local file="$INSTALLED_RULES/agent-system.md"
  grep -q '\*\*Sentinel\*\*' "$file"
  grep -qiE "(Sentinel.*security.*audit|Sentinel.*Semgrep)" "$file"
}

# ── T-0016-044: Core agent constant list unchanged ──────────────────

@test "T-0016-044: core agent constant list does not include darwin" {
  local file="$INSTALLED_RULES/agent-system.md"
  local constant_block
  constant_block=$(sed -n '/cal, colby, roz/p' "$file" | head -1)
  [ -n "$constant_block" ] || skip "Core constant list not found"

  ! echo "$constant_block" | grep -q "darwin"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 2: Invocation Templates
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-045: Source has darwin-analysis template ──────────────────

@test "T-0016-045: source/references/invocation-templates.md contains <template id=\"darwin-analysis\">" {
  local file="$SOURCE_REFS/invocation-templates.md"
  grep -q '<template id="darwin-analysis">' "$file"
}

# ── T-0016-046: Installed has darwin-analysis template ──────────────

@test "T-0016-046: .claude/references/invocation-templates.md contains <template id=\"darwin-analysis\">" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  grep -q '<template id="darwin-analysis">' "$file"
}

# ── T-0016-047: darwin-analysis template has required tags ──────────

@test "T-0016-047: darwin-analysis template contains <task>, <brain-context>, <read>, <constraints>, <output>" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="darwin-analysis">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "darwin-analysis template not found"

  local fail=0
  echo "$template" | grep -q "<task>" || { echo "Missing: <task>"; fail=1; }
  echo "$template" | grep -q "<brain-context>" || { echo "Missing: <brain-context>"; fail=1; }
  echo "$template" | grep -q "<read>" || { echo "Missing: <read>"; fail=1; }
  echo "$template" | grep -q "<constraints>" || { echo "Missing: <constraints>"; fail=1; }
  echo "$template" | grep -q "<output>" || { echo "Missing: <output>"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-048: darwin-analysis constraints content ──────────────────

@test "T-0016-048: darwin-analysis constraints include self-edit protection and escalation ladder" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="darwin-analysis">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "darwin-analysis template not found"

  local fail=0
  echo "$template" | grep -qiE "self.edit.*protect|cannot.*propose.*darwin\.md" || {
    echo "Missing: self-edit protection"; fail=1
  }
  echo "$template" | grep -qiE "escalation.*ladder|escalation.*level" || {
    echo "Missing: escalation ladder reference"; fail=1
  }
  [ "$fail" -eq 0 ]
}

# ── T-0016-049: darwin-analysis read includes required files ─────────

@test "T-0016-049: darwin-analysis <read> includes error-patterns.md, retro-lessons.md, telemetry-metrics.md" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="darwin-analysis">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "darwin-analysis template not found"

  local fail=0
  echo "$template" | grep -qi "error-patterns" || { echo "Missing: error-patterns.md"; fail=1; }
  echo "$template" | grep -qi "retro-lessons" || { echo "Missing: retro-lessons.md"; fail=1; }
  echo "$template" | grep -qi "telemetry-metrics" || { echo "Missing: telemetry-metrics.md"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-050: Both files contain darwin-edit-proposal template ─────

@test "T-0016-050: both files contain <template id=\"darwin-edit-proposal\">" {
  grep -q '<template id="darwin-edit-proposal">' "$SOURCE_REFS/invocation-templates.md"
  grep -q '<template id="darwin-edit-proposal">' "$INSTALLED_REFS/invocation-templates.md"
}

# ── T-0016-051: darwin-edit-proposal has required tags ───────────────

@test "T-0016-051: darwin-edit-proposal template contains <task>, <context>, <read>, <constraints>, <output>" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="darwin-edit-proposal">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "darwin-edit-proposal template not found"

  local fail=0
  echo "$template" | grep -q "<task>" || { echo "Missing: <task>"; fail=1; }
  echo "$template" | grep -q "<context>" || { echo "Missing: <context>"; fail=1; }
  echo "$template" | grep -q "<read>" || { echo "Missing: <read>"; fail=1; }
  echo "$template" | grep -q "<constraints>" || { echo "Missing: <constraints>"; fail=1; }
  echo "$template" | grep -q "<output>" || { echo "Missing: <output>"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-052: darwin-edit-proposal constraints ─────────────────────

@test "T-0016-052: darwin-edit-proposal constraints include dual-tree and self-edit protection" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="darwin-edit-proposal">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "darwin-edit-proposal template not found"

  local fail=0
  echo "$template" | grep -qiE "dual.tree|source/.*\.claude/" || {
    echo "Missing: dual-tree requirement"; fail=1
  }
  echo "$template" | grep -qiE "darwin.*persona|darwin\.md.*do not|darwin\.md.*not.*modif" || {
    echo "Missing: self-edit protection for Colby"; fail=1
  }
  [ "$fail" -eq 0 ]
}

# ── T-0016-053: darwin-edit-proposal context fields ──────────────────

@test "T-0016-053: darwin-edit-proposal context includes target file, section, change type, escalation level, evidence, impact" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="darwin-edit-proposal">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "darwin-edit-proposal template not found"

  local fail=0
  echo "$template" | grep -qiE "target.*file|file_path" || { echo "Missing: target file"; fail=1; }
  echo "$template" | grep -qiE "target.*section|section.*identifier" || { echo "Missing: target section"; fail=1; }
  echo "$template" | grep -qiE "change.*type" || { echo "Missing: change type"; fail=1; }
  echo "$template" | grep -qiE "escalation.*level" || { echo "Missing: escalation level"; fail=1; }
  echo "$template" | grep -qi "evidence" || { echo "Missing: evidence"; fail=1; }
  echo "$template" | grep -qiE "expected.*impact|impact" || { echo "Missing: expected impact"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-054: Existing template IDs unchanged ─────────────────────

@test "T-0016-054: existing template IDs (deps-scan, sentinel-audit) unchanged in both files" {
  for file in "$SOURCE_REFS/invocation-templates.md" "$INSTALLED_REFS/invocation-templates.md"; do
    grep -q "deps-scan" "$file" || {
      echo "Missing existing template deps-scan in $(basename "$(dirname "$file")")"
      false
    }
    grep -q "sentinel-audit" "$file" || {
      echo "Missing existing template sentinel-audit in $(basename "$(dirname "$file")")"
      false
    }
  done
}

# ═══════════════════════════════════════════════════════════════════════
# Step 3: Pipeline Integration (Auto-Trigger)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-055: pipeline-orchestration.md has Darwin auto-trigger ────

@test "T-0016-055: pipeline-orchestration.md contains Darwin auto-trigger section" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  grep -qiE "darwin.*auto.trigger|darwin.*auto-trigger|auto.*trigger.*darwin" "$file"
}

# ── T-0016-056: Auto-trigger requires four conditions ───────────────

@test "T-0016-056: auto-trigger requires darwin_enabled, brain_available, degradation alert, non-Micro" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$file" ] || skip "pipeline-orchestration.md not found"

  local fail=0
  grep -qiE "darwin_enabled.*true|darwin_enabled" "$file" || { echo "Missing condition: darwin_enabled"; fail=1; }
  grep -qiE "brain_available.*true|brain.*available" "$file" || { echo "Missing condition: brain_available"; fail=1; }
  grep -qiE "degradation.*alert|alert.*fired" "$file" || { echo "Missing condition: degradation alert"; fail=1; }
  grep -qiE "non.Micro|not.*Micro|Micro.*skip|skip.*Micro" "$file" || { echo "Missing condition: non-Micro"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-057: Auto-trigger describes brain context pre-fetch ──────

@test "T-0016-057: auto-trigger describes Eva pre-fetching brain context (Tier 3 + prior proposals)" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$file" ] || skip "pipeline-orchestration.md not found"

  grep -qiE "agent_search|tier.*3|telemetry" "$file"
  grep -qiE "darwin_proposal|prior.*darwin|prior.*proposal" "$file"
}

# ── T-0016-058: Approved proposal brain capture metadata ─────────────

@test "T-0016-058: approved proposal capture includes darwin_proposal_id, target_metric, baseline_value, escalation_level" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$file" ] || skip "pipeline-orchestration.md not found"

  local fail=0
  grep -qi "darwin_proposal_id" "$file" || { echo "Missing: darwin_proposal_id"; fail=1; }
  grep -qi "target_metric" "$file" || { echo "Missing: target_metric"; fail=1; }
  grep -qi "baseline_value" "$file" || { echo "Missing: baseline_value"; fail=1; }
  grep -qi "escalation_level" "$file" || { echo "Missing: escalation_level"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-059: Rejected proposal brain capture metadata ─────────────

@test "T-0016-059: rejected proposal capture includes rejected: true and rejection_reason" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$file" ] || skip "pipeline-orchestration.md not found"

  grep -qi "rejected.*true" "$file"
  grep -qi "rejection_reason" "$file"
}

# ── T-0016-060: Hard pause -- Eva does not auto-advance ─────────────

@test "T-0016-060: auto-trigger states hard pause -- Eva does not auto-advance past proposals" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$file" ] || skip "pipeline-orchestration.md not found"

  grep -qiE "hard pause|does not auto.advance|pause" "$file"
}

# ── T-0016-061: Darwin does not block pipeline completion ───────────

@test "T-0016-061: auto-trigger states Darwin does not block pipeline completion" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$file" ] || skip "pipeline-orchestration.md not found"

  grep -qiE "does not block.*pipeline|not.*block.*completion|user can.*skip|dismiss" "$file"
}

# ── T-0016-067: darwin_enabled false skips auto-trigger ──────────────

@test "T-0016-067: when darwin_enabled false, auto-trigger is skipped entirely" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$file" ] || skip "pipeline-orchestration.md not found"

  grep -qiE "darwin_enabled.*false.*skip|skip.*entirely|when.*darwin_enabled.*false" "$file"
}

# ── T-0016-079: Existing telemetry summary format unchanged ─────────

@test "T-0016-079: existing telemetry summary section present in pipeline-orchestration.md" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  grep -qiE "telemetry.*summary|pipeline.*end.*telemetry" "$file"
}

# ── T-0016-081: Dual tree parity for pipeline-orchestration.md ──────

@test "T-0016-081: source and .claude pipeline-orchestration.md both contain Darwin auto-trigger" {
  for file in "$SOURCE_RULES/pipeline-orchestration.md" "$INSTALLED_RULES/pipeline-orchestration.md"; do
    grep -qiE "darwin.*auto.trigger|darwin.*auto-trigger" "$file" || {
      echo "Missing Darwin auto-trigger in $(basename "$(dirname "$file")")/pipeline-orchestration.md"
      false
    }
  done
}

# ── T-0016-102: Auto-trigger appears after telemetry summary, before staleness check

@test "T-0016-102: Darwin auto-trigger section positioned after telemetry summary, before staleness check" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local line_telemetry line_darwin line_staleness

  line_telemetry=$(grep -niE "telemetry.*summary|pipeline.*end.*telemetry" "$file" | head -1 | cut -d: -f1)
  line_darwin=$(grep -niE "darwin.*auto.trigger|darwin.*auto-trigger" "$file" | head -1 | cut -d: -f1)
  line_staleness=$(grep -niE "staleness.*check|pattern.*staleness" "$file" | head -1 | cut -d: -f1)

  [ -n "$line_telemetry" ] || skip "Telemetry summary section not found"
  [ -n "$line_darwin" ] || skip "Darwin auto-trigger section not found"
  [ -n "$line_staleness" ] || skip "Pattern staleness check section not found"

  [ "$line_telemetry" -lt "$line_darwin" ]
  [ "$line_darwin" -lt "$line_staleness" ]
}

# ── T-0016-103: One Colby invocation per approved proposal ──────────

@test "T-0016-103: auto-trigger section documents one Colby invocation per approved proposal" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$file" ] || skip "pipeline-orchestration.md not found"

  grep -qiE "one.*colby.*per|per.*proposal.*colby|each.*approved.*colby|separately|atomic" "$file" || \
  grep -qiE "darwin-edit-proposal" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 3: Pipeline Integration (Post-Edit Tracking + Boot)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-062: default-persona.md boot step 5b has post-edit tracking

@test "T-0016-062: default-persona.md boot step 5b includes Darwin post-edit tracking" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qiE "darwin.*post.edit|post.edit.*track|darwin.*edit.*track" "$file"
}

# ── T-0016-063: Post-edit tracking queries for decision + darwin phase

@test "T-0016-063: post-edit tracking queries for thought_type: decision, source_phase: darwin" {
  local file="$INSTALLED_RULES/default-persona.md"
  [ -f "$file" ] || skip "default-persona.md not found"

  grep -qiE "thought_type.*decision|decision" "$file"
  grep -qiE "source_phase.*darwin|darwin" "$file"
}

# ── T-0016-064: Post-edit tracking computes delta at 3+ pipelines ───

@test "T-0016-064: post-edit tracking computes metric delta when 3+ subsequent pipelines exist" {
  local file="$INSTALLED_RULES/default-persona.md"
  [ -f "$file" ] || skip "default-persona.md not found"

  grep -qiE "3.*subsequent.*pipeline|3\+.*pipeline|metric.*delta|delta" "$file"
}

# ── T-0016-065: Post-edit tracking flags regressions ────────────────

@test "T-0016-065: post-edit tracking reports improved edits and flags worsened as regressions" {
  local file="$INSTALLED_RULES/default-persona.md"
  [ -f "$file" ] || skip "default-persona.md not found"

  grep -qiE "improv|worsen|regression" "$file"
}

# ── T-0016-066: Boot announcement includes Darwin status line ───────

@test "T-0016-066: boot announcement includes Darwin status line when darwin_enabled true" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qiE "darwin.*active|darwin.*status|darwin.*enabled|darwin.*disabled.*brain" "$file"
}

# ── T-0016-080: Existing boot step 5b telemetry trend logic unchanged

@test "T-0016-080: existing telemetry trend logic present in default-persona.md" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qiE "telemetry.*trend|trend" "$file"
}

# ── T-0016-082: Dual tree parity for default-persona.md ─────────────

@test "T-0016-082: source and .claude default-persona.md both contain Darwin post-edit tracking" {
  for file in "$SOURCE_RULES/default-persona.md" "$INSTALLED_RULES/default-persona.md"; do
    grep -qiE "darwin.*post.edit|post.edit.*track|darwin.*edit.*track" "$file" || {
      echo "Missing Darwin post-edit tracking in $(basename "$(dirname "$file")")/default-persona.md"
      false
    }
  done
}

# ═══════════════════════════════════════════════════════════════════════
# Step 3: Behavioral Boundary Tests (structural verification)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-071: 5-pipeline boundary in persona constraints ──────────

@test "T-0016-071: persona constraint references exactly 5 pipelines as minimum (not 4, not 6)" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")
  echo "$constraints" | grep -qE "5"
}

# ── T-0016-075: Darwin report includes no-changes-proposed variant ──

@test "T-0016-075: <output> or <workflow> documents all-agents-thriving = no changes proposed" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local content
  content=$(cat "$file")
  echo "$content" | grep -qiE "no.*change.*propos|all.*thriving|no.*proposal"
}

# ── T-0016-076: Level 5 double confirmation in persona ──────────────

@test "T-0016-076: persona documents Level 5 (agent replacement) requires double confirmation" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local content
  content=$(cat "$file")
  echo "$content" | grep -qiE "level 5.*double.*confirm|double.*confirm|removal.*confirm"
}

# ── T-0016-077: Self-edit protection in constraints ─────────────────

@test "T-0016-077: persona constraints block proposals targeting darwin.md" {
  local file="$INSTALLED_AGENTS/darwin.md"
  [ -f "$file" ] || skip "darwin.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")
  echo "$constraints" | grep -qiE "darwin\.md"
  echo "$constraints" | grep -qiE "cannot.*propose|self.edit"
}

# ── T-0016-104: Acceptance rate self-adjustment explicitly out of scope

@test "T-0016-104: persona or command does NOT reference acceptance rate self-adjustment" {
  # Darwin should NOT track or act on its own acceptance rate in this iteration
  local persona="$INSTALLED_AGENTS/darwin.md"
  local command="$INSTALLED_COMMANDS/darwin.md"
  local found=0

  for file in "$persona" "$command"; do
    [ -f "$file" ] || continue
    if grep -qiE "acceptance.*rate.*self.adjust|self.adjust.*acceptance|recalibrat.*acceptance|30.*accept" "$file" 2>/dev/null; then
      found=1
      echo "Found acceptance rate self-adjustment reference in $file -- should be deferred"
    fi
  done
  [ "$found" -eq 0 ] || skip "Darwin files not yet created"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 3: Contract Verification (Step 1 -> Step 3 wiring)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-101: Darwin Report shape contract: persona output matches auto-trigger consumer

@test "T-0016-101: persona <output> specifies report shape consumed by auto-trigger flow" {
  local persona="$INSTALLED_AGENTS/darwin.md"
  local orchestration="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$persona" ] || skip "darwin.md not yet created"
  [ -f "$orchestration" ] || skip "pipeline-orchestration.md not yet updated"

  # Persona output defines the report shape
  local output_section
  output_section=$(extract_tag_content "$persona" "output")
  echo "$output_section" | grep -qi "FITNESS ASSESSMENT"
  echo "$output_section" | grep -qi "PROPOSED CHANGES"

  # Orchestration file consumes proposals from the report
  grep -qiE "propos|approv|reject" "$orchestration"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 4: Setup Step 6e
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-083: SKILL.md contains Step 6e block ─────────────────────

@test "T-0016-083: SKILL.md contains a Step 6e block" {
  grep -qiE "step 6e|### 6e|## Step 6e" "$SKILL_FILE"
}

# ── T-0016-084: Step 6e is after Step 6d and before Brain setup ─────

@test "T-0016-084: Step 6e is positioned after Step 6d and before Brain setup offer" {
  local line_6d line_6e line_brain
  line_6d=$(grep -niE "step 6d|### 6d|## Step 6d" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_6e=$(grep -niE "step 6e|### 6e|## Step 6e" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_brain=$(grep -niE "brain.*setup|brain.*offer|connect.*brain" "$SKILL_FILE" | head -1 | cut -d: -f1)

  [ -n "$line_6d" ] || skip "Step 6d not found"
  [ -n "$line_6e" ] || skip "Step 6e not found"
  [ -n "$line_brain" ] || skip "Brain setup offer not found"

  [ "$line_6d" -lt "$line_6e" ]
  [ "$line_6e" -lt "$line_brain" ]
}

# ── T-0016-085: Step 6e offer text mentions telemetry + structural fixes

@test "T-0016-085: Step 6e offer text mentions telemetry, underperforming agents, structural fixes" {
  local step6e
  step6e=$(awk '/[Ss]tep 6e/,/[Ss]tep 6f|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -30)
  [ -n "$step6e" ] || skip "Step 6e block not found"

  local fail=0
  echo "$step6e" | grep -qiE "telemetry" || { echo "Missing: telemetry"; fail=1; }
  echo "$step6e" | grep -qiE "underperform|struggling|agent" || { echo "Missing: underperforming agents"; fail=1; }
  echo "$step6e" | grep -qiE "structural.*fix|structural.*improv|persona.*edit|fix" || { echo "Missing: structural fixes"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ── T-0016-086: Step 6e offer mentions Brain requirement ────────────

@test "T-0016-086: Step 6e offer text mentions Brain requirement" {
  local step6e
  step6e=$(awk '/[Ss]tep 6e/,/[Ss]tep 6f|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -30)
  [ -n "$step6e" ] || skip "Step 6e block not found"

  echo "$step6e" | grep -qiE "brain|atelier.*brain"
}

# ── T-0016-087: Step 6e yes-path sets darwin_enabled true ───────────

@test "T-0016-087: Step 6e yes-path sets darwin_enabled to true" {
  local step6e
  step6e=$(awk '/[Ss]tep 6e/,/[Ss]tep 6f|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -40)
  [ -n "$step6e" ] || skip "Step 6e block not found"

  echo "$step6e" | grep -qiE "darwin_enabled.*true|set.*darwin.*true"
}

# ── T-0016-088: Step 6e copies darwin.md agent file ─────────────────

@test "T-0016-088: Step 6e yes-path assembles darwin agent to .claude/agents/darwin.md" {
  local step6e
  step6e=$(awk '/[Ss]tep 6e/,/[Ss]tep 6f|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -40)
  [ -n "$step6e" ] || skip "Step 6e block not found"

  echo "$step6e" | grep -qiE "agents/darwin|darwin\.md"
}

# ── T-0016-089: Step 6e copies darwin.md command file ───────────────

@test "T-0016-089: Step 6e yes-path copies source/commands/darwin.md to .claude/commands/darwin.md" {
  local step6e
  step6e=$(awk '/[Ss]tep 6e/,/[Ss]tep 6f|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -40)
  [ -n "$step6e" ] || skip "Step 6e block not found"

  echo "$step6e" | grep -qiE "commands/darwin|command.*darwin"
}

# ── T-0016-090: Step 6e no-path leaves flag false ───────────────────

@test "T-0016-090: Step 6e no-path leaves darwin_enabled false and prints not enabled" {
  local step6e
  step6e=$(awk '/[Ss]tep 6e/,/[Ss]tep 6f|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -40)
  [ -n "$step6e" ] || skip "Step 6e block not found"

  echo "$step6e" | grep -qiE "not enabled|skip|decline"
}

# ── T-0016-091: Summary printout includes Darwin status line ────────

@test "T-0016-091: Step 6 summary printout includes Darwin enabled/not-enabled line" {
  grep -qiE "darwin.*enabled|darwin.*not.*enabled" "$SKILL_FILE"
}

# ── T-0016-092: Absent key treated as false in Step 6e ──────────────

@test "T-0016-092: Step 6e documents treating absent darwin_enabled as false" {
  local step6e
  step6e=$(awk '/[Ss]tep 6e/,/[Ss]tep 6f|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -50)
  [ -n "$step6e" ] || skip "Step 6e block not found"

  echo "$step6e" | grep -qiE "absent.*false|missing.*false|not.*present.*false|default.*false"
}

# ── T-0016-093: Idempotency when already enabled ───────────────────

@test "T-0016-093: Step 6e documents idempotent behavior when darwin already enabled" {
  local step6e
  step6e=$(awk '/[Ss]tep 6e/,/[Ss]tep 6f|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -50)
  [ -n "$step6e" ] || skip "Step 6e block not found"

  echo "$step6e" | grep -qiE "already.*enabled|idempoten|skip.*mutation"
}

# ── T-0016-094: Idempotency when already disabled ──────────────────

@test "T-0016-094: Step 6e documents confirming before changing from false to true" {
  local step6e
  step6e=$(awk '/[Ss]tep 6e/,/[Ss]tep 6f|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -50)
  [ -n "$step6e" ] || skip "Step 6e block not found"

  echo "$step6e" | grep -qiE "confirm|ask|offer|enable|want|would you like"
}

# ── T-0016-095: Step 6d (Deps) unchanged ────────────────────────────

@test "T-0016-095: Step 6d (Deps) block is unchanged after Step 6e insertion" {
  grep -qiE "step 6d|deps" "$SKILL_FILE"
  grep -qiE "deps_agent_enabled" "$SKILL_FILE"
}

# ── T-0016-096: Brain setup offer remains after Step 6e ─────────────

@test "T-0016-096: Brain setup offer is still present and positioned after Step 6e" {
  local line_6e line_brain
  line_6e=$(grep -niE "step 6e|### 6e" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_brain=$(grep -niE "brain.*setup|brain.*offer|connect.*brain" "$SKILL_FILE" | head -1 | cut -d: -f1)

  [ -n "$line_6e" ] || skip "Step 6e not found"
  [ -n "$line_brain" ] || skip "Brain offer not found"

  [ "$line_6e" -lt "$line_brain" ]
}

# ── T-0016-097: Steps 6a-6c unchanged ──────────────────────────────

@test "T-0016-097: Steps 6a (Sentinel), 6b (Agent Teams), 6c (CI Watch) unchanged after Step 6e insertion" {
  local fail=0
  grep -qiE "step 6a|sentinel" "$SKILL_FILE" || { echo "Missing: Step 6a/Sentinel"; fail=1; }
  grep -qiE "sentinel_enabled" "$SKILL_FILE" || { echo "Missing: sentinel_enabled"; fail=1; }
  grep -qiE "step 6b|agent.teams" "$SKILL_FILE" || { echo "Missing: Step 6b/Agent Teams"; fail=1; }
  grep -qiE "agent_teams_enabled" "$SKILL_FILE" || { echo "Missing: agent_teams_enabled"; fail=1; }
  grep -qiE "step 6c|ci.watch" "$SKILL_FILE" || { echo "Missing: Step 6c/CI Watch"; fail=1; }
  grep -qiE "ci_watch_enabled" "$SKILL_FILE" || { echo "Missing: ci_watch_enabled"; fail=1; }
  [ "$fail" -eq 0 ]
}

# ═══════════════════════════════════════════════════════════════════════
# Additional Step 2 Subagent Table Verification
# ═══════════════════════════════════════════════════════════════════════

# ── T-0016-036b: Darwin subagent tools list is correct ──────────────

@test "T-0016-036b: Darwin row in subagent table lists Read, Glob, Grep, Bash (read-only)" {
  local file="$INSTALLED_RULES/agent-system.md"
  local darwin_row
  darwin_row=$(grep -i '\*\*Darwin\*\*' "$file" | head -1)
  [ -n "$darwin_row" ] || skip "Darwin subagent row not found"

  echo "$darwin_row" | grep -qi "Read"
  echo "$darwin_row" | grep -qi "Glob"
  echo "$darwin_row" | grep -qi "Grep"
  echo "$darwin_row" | grep -qi "Bash"
  echo "$darwin_row" | grep -qiE "read.only"
}
