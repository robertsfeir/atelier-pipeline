#!/usr/bin/env bats
# ADR-0015: Predictive Dependency Management Agent (Deps) -- Structural Tests
# Tests: T-0015-001 through T-0015-064
#
# These tests verify the structural content of Deps agent deliverables:
# - deps.md agent persona (source + installed)
# - deps.md slash command (source + installed)
# - pipeline-config.json (deps_agent_enabled flag)
# - agent-system.md (subagent table, routing table, no-skill-tool gate)
# - invocation-templates.md (deps-scan, deps-migration-brief)
# - SKILL.md (Step 6d opt-in)

load ../xml-prompt-structure/test_helper

# ═══════════════════════════════════════════════════════════════════════
# Step 1: Agent Persona
# ═══════════════════════════════════════════════════════════════════════

# ── T-0015-001: Persona file exists in source with correct frontmatter ─

@test "T-0015-001: source deps agent files exist with name: deps in frontmatter" {
  local shared="$PROJECT_ROOT/source/shared/agents/deps.md"
  local frontmatter="$PROJECT_ROOT/source/claude/agents/deps.frontmatter.yml"
  [ -f "$shared" ]
  [ -f "$frontmatter" ]
  grep -q "^name: deps" "$frontmatter"
}

# ── T-0015-002: Installed copy exists with correct frontmatter ───────

@test "T-0015-002: .claude/agents/deps.md exists with name: deps in YAML frontmatter" {
  local installed="$INSTALLED_AGENTS/deps.md"
  [ -f "$installed" ]
  grep -q "name: deps" "$installed"
}

# ── T-0015-003: disallowedTools includes Write, Edit, MultiEdit ─────

@test "T-0015-003: deps.md disallowedTools frontmatter includes Write, Edit, MultiEdit" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local frontmatter
  frontmatter=$(sed -n '/^---$/,/^---$/p' "$file")

  echo "$frontmatter" | grep -q "Write"
  echo "$frontmatter" | grep -q "Edit"
  echo "$frontmatter" | grep -q "MultiEdit"
}

# ── T-0015-004: Persona contains all 6 required XML tags ────────────

@test "T-0015-004: deps.md contains identity, required-actions, workflow, tools, constraints, output tags" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local tags=(identity required-actions workflow tools constraints output)
  local fail=0
  for tag in "${tags[@]}"; do
    assert_has_tag "$file" "$tag" || { fail=1; }
    assert_has_closing_tag "$file" "$tag" || { fail=1; }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0015-005: Persona contains <examples> tag with content ────────

@test "T-0015-005: deps.md contains <examples> tag with at least two examples" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  assert_has_tag "$file" "examples"
  assert_has_closing_tag "$file" "examples"

  local examples
  examples=$(extract_tag_content "$file" "examples")
  local example_count
  example_count=$(echo "$examples" | grep -ciE "example|skip.*ecosystem|breakage.*predict|missing.*tool|cargo.*not found|go.*cve" || echo 0)
  [ "$example_count" -ge 2 ]
}

# ── T-0015-006: <tools> section lists correct tools ──────────────────

@test "T-0015-006: <tools> section lists Bash, Read, Grep, Glob, WebSearch, WebFetch" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local tools_section
  tools_section=$(extract_tag_content "$file" "tools")

  local required_tools=(Bash Read Grep Glob WebSearch WebFetch)
  local fail=0
  for tool in "${required_tools[@]}"; do
    echo "$tools_section" | grep -q "$tool" || {
      echo "Missing tool in <tools>: $tool"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]

  ! echo "$tools_section" | grep -qE "^[^#]*\bWrite\b" || {
    echo "Write tool listed in <tools> section -- should not be"
    false
  }
}

# ── T-0015-007: Workflow encodes Detect, Scan, Report phases ────────

@test "T-0015-007: <workflow> encodes Detect, Scan, Report phases" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local workflow
  workflow=$(extract_tag_content "$file" "workflow")

  echo "$workflow" | grep -qi "detect"
  echo "$workflow" | grep -qi "scan"
  echo "$workflow" | grep -qi "report"
}

# ── T-0015-008: Constraints include hang/stop rule ──────────────────

@test "T-0015-008: <constraints> includes 'if command hangs, STOP -- do not retry'" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")

  echo "$constraints" | grep -qiE "hang.*stop|stop.*do not retry|hang.*do not retry"
}

# ── T-0015-009: Constraints include 'Never modify files' ────────────

@test "T-0015-009: <constraints> includes 'Never modify files'" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")

  echo "$constraints" | grep -qiE "never.*modify|never.*write|read.only|no.*file.*modif"
}

# ── T-0015-010: Constraints include WebFetch degradation ────────────

@test "T-0015-010: <constraints> includes WebFetch unavailability degradation instruction" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")

  echo "$constraints" | grep -qiE "webfetch.*unavailable|webfetch.*degrad|changelog.*unavailable"
}

# ── T-0015-011: Output specifies four risk sections ──────────────────

@test "T-0015-011: <output> specifies CVE Alerts, Needs Review, Safe to Upgrade, No Action Needed" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local output_section
  output_section=$(extract_tag_content "$file" "output")

  local sections=("CVE" "Needs Review" "Safe to Upgrade" "No Action")
  local fail=0
  for section in "${sections[@]}"; do
    echo "$output_section" | grep -qi "$section" || {
      echo "Missing output section: $section"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0015-012: Workflow encodes all edge cases from spec ────────────

@test "T-0015-012: <workflow> encodes edge cases: no manifest, missing tools, offline, monorepo, private registry" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local workflow
  workflow=$(extract_tag_content "$file" "workflow")

  local fail=0
  echo "$workflow" | grep -qiE "no manifest|manifest.*not found|no.*dependency" || {
    echo "Missing edge case: no manifest"; fail=1
  }
  echo "$workflow" | grep -qiE "missing.*tool|tool.*not found|not.*installed" || {
    echo "Missing edge case: missing tools"; fail=1
  }
  echo "$workflow" | grep -qiE "offline|network|internet|connectivity" || {
    echo "Missing edge case: offline"; fail=1
  }
  echo "$workflow" | grep -qiE "monorepo|multiple.*manifest|workspace" || {
    echo "Missing edge case: monorepo"; fail=1
  }
  echo "$workflow" | grep -qiE "private.*registry|private.*repo|auth" || {
    echo "Missing edge case: private registry"; fail=1
  }
  [ "$fail" -eq 0 ]
}

# ── T-0015-013: Constraints contain Bash command whitelist and blocklist

@test "T-0015-013: <constraints> contains explicit Bash command whitelist and prohibition" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local constraints
  constraints=$(extract_tag_content "$file" "constraints")

  local fail=0
  for cmd in "npm outdated" "npm audit" "pip-audit" "cargo audit" "cargo outdated" "go list"; do
    echo "$constraints" | grep -qi "$cmd" || {
      echo "Missing whitelisted command: $cmd"; fail=1
    }
  done

  for cmd in "npm install" "pip install" "cargo update" "go get"; do
    echo "$constraints" | grep -qi "$cmd" || {
      echo "Missing blocklisted command: $cmd"; fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0015-014: Go ecosystem handling states no CVE audit tool ──────

@test "T-0015-014: <workflow> states Go has no CVE audit tool and CVE section is omitted" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local workflow
  workflow=$(extract_tag_content "$file" "workflow")

  echo "$workflow" | grep -qiE "go.*no.*audit|go.*cve.*unavailable|no.*go.*audit|go.*cve.*omit"
  echo "$workflow" | grep -q "go list" || echo "$workflow" | grep -q "go list -m -u all"
}

# ── T-0015-015: Persona does NOT include Write in tools ──────────────

@test "T-0015-015: deps.md <tools> does not include Write tool" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local tools_section
  tools_section=$(extract_tag_content "$file" "tools")

  ! echo "$tools_section" | grep -qE "^\s*[-*].*\bWrite\b" || {
    echo "Write tool found as a listed item in <tools>"; false
  }
}

# ── T-0015-016: Persona does NOT include Edit in tools ──────────────

@test "T-0015-016: deps.md <tools> does not include Edit tool" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"

  local tools_section
  tools_section=$(extract_tag_content "$file" "tools")

  ! echo "$tools_section" | grep -qE "^\s*[-*].*\bEdit\b" || {
    echo "Edit tool found as a listed item in <tools>"; false
  }
}

# ── T-0015-019: deps is not in core agent constant list ─────────────

@test "T-0015-019: deps does not appear in the core agent constant list in agent-system.md" {
  local file="$INSTALLED_RULES/agent-system.md"
  local core_list
  core_list=$(grep -A2 "core agents" "$file" | grep -oE "cal, colby.*distillator" || true)
  if [ -n "$core_list" ]; then
    ! echo "$core_list" | grep -q "deps"
  fi
}

# ── T-0015-020: name: deps not in core constant ─────────────────────

@test "T-0015-020: core agent constant in agent-system.md does not include deps" {
  local file="$INSTALLED_RULES/agent-system.md"
  local constant_block
  constant_block=$(sed -n '/^```$/,/^```$/p' "$file" | grep -E "cal.*colby.*roz" || true)
  if [ -n "$constant_block" ]; then
    ! echo "$constant_block" | grep -q "deps"
  fi
}

# ═══════════════════════════════════════════════════════════════════════
# Step 1 Hook Tests (Layer 1 disallowedTools enforcement)
# ═══════════════════════════════════════════════════════════════════════

# ── T-0015-017: deps has disallowedTools blocking Write ──────────────

@test "T-0015-017: deps frontmatter disallowedTools blocks Write (Layer 1 enforcement)" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"
  local frontmatter
  frontmatter=$(sed -n '/^---$/,/^---$/p' "$file")
  echo "$frontmatter" | grep -q "disallowedTools"
  echo "$frontmatter" | grep -q "Write"
}

# ── T-0015-018: deps has disallowedTools blocking Edit ───────────────

@test "T-0015-018: deps frontmatter disallowedTools blocks Edit (Layer 1 enforcement)" {
  local file="$INSTALLED_AGENTS/deps.md"
  [ -f "$file" ] || skip "deps.md not yet created"
  local frontmatter
  frontmatter=$(sed -n '/^---$/,/^---$/p' "$file")
  echo "$frontmatter" | grep -q "disallowedTools"
  echo "$frontmatter" | grep -q "Edit"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 2: Slash Command
# ═══════════════════════════════════════════════════════════════════════

# ── T-0015-021: Command file exists in source ───────────────────────

@test "T-0015-021: source/commands/deps.md exists with YAML frontmatter name: deps" {
  local file="$SOURCE_COMMANDS/deps.md"
  [ -f "$file" ]
  grep -qE "^name: deps" "$file"
}

# ── T-0015-022: Installed command is identical to source ─────────────

@test "T-0015-022: .claude/commands/deps.md exists with identical content to source" {
  local source="$SOURCE_COMMANDS/deps.md"
  local installed="$INSTALLED_COMMANDS/deps.md"
  [ -f "$source" ]
  [ -f "$installed" ]
  diff -q "$source" "$installed"
}

# ── T-0015-023: Command describes Flow A (scan and report) ──────────

@test "T-0015-023: command file describes scan-and-report flow" {
  local file="$INSTALLED_COMMANDS/deps.md"
  [ -f "$file" ] || skip "deps.md command not yet created"

  grep -qiE "deps_agent_enabled|scan|report" "$file"
}

# ── T-0015-024: Command describes Flow B (migration ADR brief) ──────

@test "T-0015-024: command file describes migration ADR brief flow" {
  local file="$INSTALLED_COMMANDS/deps.md"
  [ -f "$file" ] || skip "deps.md command not yet created"

  grep -qiE "migration.*adr|migration.*brief|cal" "$file"
}

# ── T-0015-025: Command includes deps_agent_enabled gate ────────────

@test "T-0015-025: command file includes gate for deps_agent_enabled false" {
  local file="$INSTALLED_COMMANDS/deps.md"
  [ -f "$file" ] || skip "deps.md command not yet created"

  grep -qiE "deps_agent_enabled.*false|not enabled|not.*enabled" "$file"
}

# ── T-0015-026: Command format matches debug.md structure ───────────

@test "T-0015-026: command file has structured behavior block (not raw prose)" {
  local file="$INSTALLED_COMMANDS/deps.md"
  [ -f "$file" ] || skip "deps.md command not yet created"

  head -1 "$file" | grep -q "^---"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 3: Config Flag
# ═══════════════════════════════════════════════════════════════════════

# ── T-0015-027: Source config contains deps_agent_enabled: false ─────

@test "T-0015-027: source/pipeline/pipeline-config.json contains deps_agent_enabled: false" {
  local file="$PROJECT_ROOT/source/pipeline/pipeline-config.json"
  jq -e '.deps_agent_enabled == false' "$file"
}

# ── T-0015-028: Installed config contains deps_agent_enabled: false ──

@test "T-0015-028: .claude/pipeline-config.json contains deps_agent_enabled: false" {
  local file="$PROJECT_ROOT/.claude/pipeline-config.json"
  jq -e '.deps_agent_enabled == false' "$file"
}

# ── T-0015-029: Both config files remain valid JSON ──────────────────

@test "T-0015-029: both pipeline-config.json files are valid JSON" {
  jq . "$PROJECT_ROOT/source/pipeline/pipeline-config.json" > /dev/null
  jq . "$PROJECT_ROOT/.claude/pipeline-config.json" > /dev/null
}

# ── T-0015-030: No existing config fields removed or renamed ────────

@test "T-0015-030: no existing config fields removed from source pipeline-config.json" {
  local file="$PROJECT_ROOT/source/pipeline/pipeline-config.json"
  local fields=(branching_strategy platform sentinel_enabled agent_teams_enabled ci_watch_enabled ci_watch_max_retries ci_watch_poll_command ci_watch_log_command)
  local fail=0
  for field in "${fields[@]}"; do
    jq -e "has(\"$field\")" "$file" > /dev/null || {
      echo "Missing existing field: $field"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0015-031: Sentinel, agent_teams, ci_watch fields unchanged ────

@test "T-0015-031: sentinel_enabled, agent_teams_enabled, ci_watch_enabled unchanged in source config" {
  local file="$PROJECT_ROOT/source/pipeline/pipeline-config.json"
  jq -e '.sentinel_enabled == false' "$file" > /dev/null
  jq -e '.agent_teams_enabled == false' "$file" > /dev/null
  jq -e '.ci_watch_enabled == false' "$file" > /dev/null
}

# ═══════════════════════════════════════════════════════════════════════
# Step 4: Auto-Routing Update
# ═══════════════════════════════════════════════════════════════════════

# ── T-0015-032: Source agent-system.md subagent table has Deps row ───
# Tightened: looks for **Deps** (bold markdown) which is the subagent
# table format, not just "deps" appearing anywhere in the file.

@test "T-0015-032: source/rules/agent-system.md subagent table contains **Deps** row" {
  local file="$SOURCE_RULES/agent-system.md"
  grep -q '\*\*Deps\*\*' "$file"
}

# ── T-0015-033: Installed agent-system.md subagent table has Deps row ─

@test "T-0015-033: .claude/rules/agent-system.md subagent table contains **Deps** row" {
  local file="$INSTALLED_RULES/agent-system.md"
  grep -q '\*\*Deps\*\*' "$file"
}

# ── T-0015-034: Auto-routing table has dependency intent row ────────
# Tightened: must have Deps (capitalized, as agent name) alongside
# dependency-related terms, not just "dependency" appearing generically.

@test "T-0015-034: auto-routing table maps dependency intent to Deps agent" {
  for file in "$SOURCE_RULES/agent-system.md" "$INSTALLED_RULES/agent-system.md"; do
    # Must have Deps in a routing context with dependency keywords
    grep -qiE "Deps" "$file" && grep -qiE "dependenc|outdated|upgrade|cve|vulnerability" "$file" || {
      echo "Missing dependency intent -> Deps routing in $(basename "$file")"
      false
    }
    # And specifically, Deps must appear in a table row (pipe-delimited)
    grep -qE '\|.*[Dd]eps.*\|' "$file" || {
      echo "Deps not in a table row in $(basename "$file")"
      false
    }
  done
}

# ── T-0015-035: Deps routing row includes deps_agent_enabled gate ───

@test "T-0015-035: auto-routing Deps row includes deps_agent_enabled gate condition" {
  local file="$INSTALLED_RULES/agent-system.md"
  grep -qi "deps_agent_enabled" "$file"
}

# ── T-0015-036: no-skill-tool gate maps Deps to .claude/agents/deps.md

@test "T-0015-036: no-skill-tool gate in both files maps Deps to .claude/agents/deps.md" {
  for file in "$SOURCE_RULES/agent-system.md" "$INSTALLED_RULES/agent-system.md"; do
    grep -qiE "deps.*\.claude/agents/deps\.md|deps\.md" "$file" || {
      echo "Missing Deps -> deps.md mapping in no-skill-tool gate in $(basename "$file")"
      false
    }
  done
}

# ── T-0015-037: Auto-routing documents deps_agent_enabled gate ──────

@test "T-0015-037: auto-routing documents that deps intent is gated by deps_agent_enabled" {
  local file="$INSTALLED_RULES/agent-system.md"
  grep -qiE "deps_agent_enabled" "$file"
}

# ── T-0015-038: Deps subagent tools list is correct ──────────────────

@test "T-0015-038: Deps row in subagent table lists Read, Glob, Grep, Bash, WebSearch, WebFetch" {
  local file="$INSTALLED_RULES/agent-system.md"
  local deps_row
  deps_row=$(grep -i '\*\*Deps\*\*' "$file" | head -1)
  [ -n "$deps_row" ] || skip "Deps subagent row not found"

  echo "$deps_row" | grep -qi "Read"
  echo "$deps_row" | grep -qi "Glob"
  echo "$deps_row" | grep -qi "Grep"
  echo "$deps_row" | grep -qi "Bash"
  echo "$deps_row" | grep -qi "WebSearch"
  echo "$deps_row" | grep -qi "WebFetch"
}

# ── T-0015-039: Sentinel row unchanged after Step 4 edits ───────────

@test "T-0015-039: Sentinel row in subagent table is unchanged" {
  local file="$INSTALLED_RULES/agent-system.md"
  grep -q '\*\*Sentinel\*\*' "$file"
  grep -qiE "(Sentinel.*security.*audit|Sentinel.*Semgrep)" "$file"
}

# ── T-0015-040: Core agent constant list unchanged ──────────────────

@test "T-0015-040: core agent constant list does not include deps" {
  local file="$INSTALLED_RULES/agent-system.md"
  local constant_block
  constant_block=$(sed -n '/cal, colby, roz/p' "$file" | head -1)
  [ -n "$constant_block" ] || skip "Core constant list not found"

  ! echo "$constant_block" | grep -q "deps"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 5: Invocation Templates
# ═══════════════════════════════════════════════════════════════════════

# ── T-0015-041: Source invocation-templates.md has deps-scan template ─

@test "T-0015-041: source/references/invocation-templates.md contains <template id=\"deps-scan\">" {
  local file="$SOURCE_REFS/invocation-templates.md"
  grep -q '<template id="deps-scan">' "$file"
}

# ── T-0015-042: Installed invocation-templates.md has deps-scan ──────

@test "T-0015-042: .claude/references/invocation-templates.md contains <template id=\"deps-scan\">" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  grep -q '<template id="deps-scan">' "$file"
}

# ── T-0015-043: deps-scan template has task, constraints, output ────

@test "T-0015-043: deps-scan template contains <task>, <constraints>, <output> tags" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="deps-scan">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "deps-scan template not found"

  echo "$template" | grep -q "<task>"
  echo "$template" | grep -q "<constraints>"
  echo "$template" | grep -q "<output>"
}

# ── T-0015-044: deps-scan constraints include key rules ─────────────

@test "T-0015-044: deps-scan constraints include skip, degrade, stop, no-modify rules" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="deps-scan">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "deps-scan template not found"

  local fail=0
  echo "$template" | grep -qiE "skip.*missing|missing.*ecosystem" || {
    echo "Missing: skip missing ecosystems"; fail=1
  }
  echo "$template" | grep -qiE "degrade|webfetch.*unavailable" || {
    echo "Missing: degrade if WebFetch unavailable"; fail=1
  }
  echo "$template" | grep -qiE "hang|stop" || {
    echo "Missing: stop on hang"; fail=1
  }
  echo "$template" | grep -qiE "no.*modif|never.*modif|read.only" || {
    echo "Missing: no file modifications"; fail=1
  }
  [ "$fail" -eq 0 ]
}

# ── T-0015-045: deps-scan output specifies four risk sections ───────

@test "T-0015-045: deps-scan output specifies risk sections and DoR/DoD" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="deps-scan">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "deps-scan template not found"

  echo "$template" | grep -qiE "CVE|risk|section"
  echo "$template" | grep -qiE "DoR|DoD"
}

# ── T-0015-046: Both files contain deps-migration-brief template ────

@test "T-0015-046: both files contain <template id=\"deps-migration-brief\">" {
  grep -q '<template id="deps-migration-brief">' "$SOURCE_REFS/invocation-templates.md"
  grep -q '<template id="deps-migration-brief">' "$INSTALLED_REFS/invocation-templates.md"
}

# ── T-0015-047: deps-migration-brief is scoped to single package ────

@test "T-0015-047: deps-migration-brief template is scoped to a single named package" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="deps-migration-brief">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "deps-migration-brief template not found"

  echo "$template" | grep -qiE "single.*package|named.*package|specific.*package|package.*name"
}

# ── T-0015-048: Migration brief output includes required sections ───

@test "T-0015-048: deps-migration-brief output specifies breaking changes, usage, approach, effort" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  local template
  template=$(sed -n '/<template id="deps-migration-brief">/,/<\/template>/p' "$file")
  [ -n "$template" ] || skip "deps-migration-brief template not found"

  local fail=0
  echo "$template" | grep -qiE "breaking.*change" || {
    echo "Missing: breaking changes table"; fail=1
  }
  echo "$template" | grep -qiE "usage.*inventory|file.*line" || {
    echo "Missing: usage inventory"; fail=1
  }
  echo "$template" | grep -qiE "migration.*approach" || {
    echo "Missing: migration approach"; fail=1
  }
  echo "$template" | grep -qiE "effort|estimate" || {
    echo "Missing: estimated effort"; fail=1
  }
  [ "$fail" -eq 0 ]
}

# ── T-0015-049: Existing template IDs unchanged ─────────────────────

@test "T-0015-049: existing template IDs (sentinel-audit) unchanged in both files" {
  for file in "$SOURCE_REFS/invocation-templates.md" "$INSTALLED_REFS/invocation-templates.md"; do
    grep -q "sentinel-audit" "$file" || {
      echo "Missing existing template sentinel-audit in $(basename "$(dirname "$file")")"
      false
    }
  done
}

# ═══════════════════════════════════════════════════════════════════════
# Step 6: Setup Step 6d
# ═══════════════════════════════════════════════════════════════════════

SKILL_FILE="$PROJECT_ROOT/skills/pipeline-setup/SKILL.md"

# ── T-0015-050: SKILL.md contains Step 6d block ─────────────────────

@test "T-0015-050: SKILL.md contains a Step 6d block" {
  grep -qiE "step 6d|### 6d|## Step 6d" "$SKILL_FILE"
}

# ── T-0015-051: Step 6d is after Step 6c and before Brain setup ─────

@test "T-0015-051: Step 6d is positioned after Step 6c and before Brain setup offer" {
  local line_6c line_6d line_brain
  line_6c=$(grep -niE "step 6c|### 6c|## Step 6c" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_6d=$(grep -niE "step 6d|### 6d|## Step 6d" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_brain=$(grep -niE "brain.*setup|brain.*offer|connect.*brain" "$SKILL_FILE" | head -1 | cut -d: -f1)

  [ -n "$line_6c" ] || skip "Step 6c not found"
  [ -n "$line_6d" ] || skip "Step 6d not found"
  [ -n "$line_brain" ] || skip "Brain setup offer not found"

  [ "$line_6c" -lt "$line_6d" ]
  [ "$line_6d" -lt "$line_brain" ]
}

# ── T-0015-052: Step 6d offer text mentions CVE, outdated, breakage ─

@test "T-0015-052: Step 6d offer text mentions CVE, outdated packages, breakage risk" {
  local step6d
  step6d=$(awk '/[Ss]tep 6d/,/[Ss]tep 6e|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -30)
  [ -n "$step6d" ] || skip "Step 6d block not found"

  echo "$step6d" | grep -qiE "CVE|vulnerabilit"
  echo "$step6d" | grep -qiE "outdated|upgrade"
  echo "$step6d" | grep -qiE "breakage|breaking|risk"
}

# ── T-0015-053: Step 6d yes-path sets deps_agent_enabled: true ──────

@test "T-0015-053: Step 6d yes-path sets deps_agent_enabled to true" {
  local step6d
  step6d=$(awk '/[Ss]tep 6d/,/[Ss]tep 6e|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -40)
  [ -n "$step6d" ] || skip "Step 6d block not found"

  echo "$step6d" | grep -qiE "deps_agent_enabled.*true|set.*deps.*true"
}

# ── T-0015-054: Step 6d copies deps.md agent file ──────────────────

@test "T-0015-054: Step 6d yes-path assembles deps agent to .claude/agents/deps.md" {
  local step6d
  step6d=$(awk '/[Ss]tep 6d/,/[Ss]tep 6e|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -40)
  [ -n "$step6d" ] || skip "Step 6d block not found"

  echo "$step6d" | grep -qiE "deps\.md|agents/deps"
}

# ── T-0015-055: Step 6d copies deps.md command file ─────────────────

@test "T-0015-055: Step 6d yes-path copies source/commands/deps.md to .claude/commands/deps.md" {
  local step6d
  step6d=$(awk '/[Ss]tep 6d/,/[Ss]tep 6e|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -40)
  [ -n "$step6d" ] || skip "Step 6d block not found"

  echo "$step6d" | grep -qiE "commands/deps|command.*deps"
}

# ── T-0015-056: Step 6d no-path leaves flag false ──────────────────

@test "T-0015-056: Step 6d no-path leaves deps_agent_enabled false and prints not-enabled" {
  local step6d
  step6d=$(awk '/[Ss]tep 6d/,/[Ss]tep 6e|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -40)
  [ -n "$step6d" ] || skip "Step 6d block not found"

  echo "$step6d" | grep -qiE "not enabled|skip|decline"
}

# ── T-0015-057: Summary includes deps agent status line ─────────────

@test "T-0015-057: Step 6 summary printout includes deps agent enabled/not-enabled line" {
  grep -qiE "deps.*agent.*enabled|deps.*agent.*not.*enabled|deps.*enabled|deps.*not enabled" "$SKILL_FILE"
}

# ── T-0015-058: Absent key treated as false ──────────────────────────

@test "T-0015-058: Step 6d documents treating absent deps_agent_enabled as false" {
  local step6d
  step6d=$(awk '/[Ss]tep 6d/,/[Ss]tep 6e|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -40)
  [ -n "$step6d" ] || skip "Step 6d block not found"

  echo "$step6d" | grep -qiE "absent.*false|missing.*false|not.*present.*false|default.*false"
}

# ── T-0015-059: Idempotency when already enabled ───────────────────

@test "T-0015-059: Step 6d documents idempotent behavior when already enabled" {
  local step6d
  step6d=$(awk '/[Ss]tep 6d/,/[Ss]tep 6e|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -50)
  [ -n "$step6d" ] || skip "Step 6d block not found"

  echo "$step6d" | grep -qiE "already.*enabled|idempoten|skip.*mutation"
}

# ── T-0015-060: Idempotency when already disabled ──────────────────

@test "T-0015-060: Step 6d documents confirming before changing from false to true" {
  local step6d
  step6d=$(awk '/[Ss]tep 6d/,/[Ss]tep 6e|[Ss]tep 7|[Bb]rain/' "$SKILL_FILE" | head -50)
  [ -n "$step6d" ] || skip "Step 6d block not found"

  echo "$step6d" | grep -qiE "ask|offer|enable|want|would you like"
}

# ── T-0015-061: Step 6a (Sentinel) unchanged ────────────────────────

@test "T-0015-061: Step 6a (Sentinel) block is unchanged after Step 6d insertion" {
  grep -qiE "step 6a|sentinel" "$SKILL_FILE"
  grep -qiE "sentinel_enabled" "$SKILL_FILE"
}

# ── T-0015-062: Step 6b (Agent Teams) unchanged ────────────────────

@test "T-0015-062: Step 6b (Agent Teams) block is unchanged after Step 6d insertion" {
  grep -qiE "step 6b|agent.teams" "$SKILL_FILE"
  grep -qiE "agent_teams_enabled" "$SKILL_FILE"
}

# ── T-0015-063: Step 6c (CI Watch) unchanged ───────────────────────

@test "T-0015-063: Step 6c (CI Watch) block is unchanged after Step 6d insertion" {
  grep -qiE "step 6c|ci.watch" "$SKILL_FILE"
  grep -qiE "ci_watch_enabled" "$SKILL_FILE"
}

# ── T-0015-064: Brain setup offer remains after Step 6d ─────────────

@test "T-0015-064: Brain setup offer is still present and positioned after Step 6d" {
  local line_6d line_brain
  line_6d=$(grep -niE "step 6d|### 6d" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_brain=$(grep -niE "brain.*setup|brain.*offer|connect.*brain" "$SKILL_FILE" | head -1 | cut -d: -f1)

  [ -n "$line_6d" ] || skip "Step 6d not found"
  [ -n "$line_brain" ] || skip "Brain offer not found"

  [ "$line_6d" -lt "$line_brain" ]
}
