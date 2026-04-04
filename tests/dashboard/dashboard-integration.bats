#!/usr/bin/env bats
# ADR-0018: Dashboard Integration + quality-gate.sh Cleanup -- Structural Tests
# Tests: T-0018-001 through T-0018-095 (103 tests total, including sub-IDs)
#
# These tests verify the structural content of dashboard integration deliverables:
# - SKILL.md: Step 0 (quality-gate.sh cleanup) + Step 6f (dashboard opt-in)
# - pipeline-config.json: dashboard field in source/ and .claude/ copies
# - telemetry-bridge.sh: bridge script existence and structure
# - pipeline-orchestration.md: Dashboard Bridge post-pipeline section
# - invocation-templates.md: dashboard-bridge template
#
# DoR: Requirements Extracted
# Source: ADR-0018, Spec (docs/product/dashboard-integration.md)
#
# | # | Requirement | Source |
# |---|-------------|--------|
# | R1 | Step 0 cleanup in SKILL.md before Step 1 | ADR Step 1, Spec AC-9/10/13 |
# | R2 | dashboard config field in both config files | ADR Step 1, Spec AC-2/3/4 |
# | R3 | Step 6f menu after Darwin, before Brain | ADR Step 2, Spec US-1 |
# | R4 | Bridge script exists and is executable | ADR Step 3, Spec AC-7 |
# | R5 | Dashboard Bridge in pipeline-orchestration.md | ADR Step 4 |
# | R6 | dashboard-bridge template in invocation-templates.md | ADR Step 4 |
# | R7 | Dual tree parity for modified files | ADR blast radius |
# | R8 | Existing content unchanged (regression) | ADR acceptance criteria |
#
# Retro risks: #003 (quality-gate.sh race condition) -- directly relevant

load ../xml-prompt-structure/test_helper

SKILL_FILE="$PROJECT_ROOT/skills/pipeline-setup/SKILL.md"
SOURCE_CONFIG="$PROJECT_ROOT/source/pipeline/pipeline-config.json"
INSTALLED_CONFIG="$PROJECT_ROOT/.claude/pipeline-config.json"
SOURCE_ORCH="$PROJECT_ROOT/source/rules/pipeline-orchestration.md"
INSTALLED_ORCH="$PROJECT_ROOT/.claude/rules/pipeline-orchestration.md"
SOURCE_TEMPLATES="$PROJECT_ROOT/source/references/invocation-templates.md"
INSTALLED_TEMPLATES="$PROJECT_ROOT/.claude/references/invocation-templates.md"
BRIDGE_SCRIPT="$PROJECT_ROOT/source/dashboard/telemetry-bridge.sh"

# ═══════════════════════════════════════════════════════════════════════
# Step 1 Tests: quality-gate.sh Cleanup + Config Flag
# ═══════════════════════════════════════════════════════════════════════

# ── T-0018-001: Step 0 positioned before Step 1 ──────────────────────

@test "T-0018-001: SKILL.md contains a Step 0 block positioned before Step 1 (Gather Project Information)" {
  [ -f "$SKILL_FILE" ]
  # Step 0 must exist
  grep -q "Step 0" "$SKILL_FILE"
  # Step 0 must appear before Step 1
  local line_step0 line_step1
  line_step0=$(grep -n "Step 0" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_step1=$(grep -n "### Step 1:" "$SKILL_FILE" | head -1 | cut -d: -f1)
  [ -n "$line_step0" ]
  [ -n "$line_step1" ]
  [ "$line_step0" -lt "$line_step1" ]
}

# ── T-0018-002: Step 0 detects and deletes quality-gate.sh ───────────

@test "T-0018-002: Step 0 describes detection and deletion of .claude/hooks/quality-gate.sh" {
  [ -f "$SKILL_FILE" ]
  # The Step 0 section must reference quality-gate.sh file detection and deletion
  grep -q "quality-gate.sh" "$SKILL_FILE"
  # Must reference the hooks directory path
  grep -q '\.claude/hooks/quality-gate\.sh' "$SKILL_FILE"
  # Must reference deletion/removal of the file
  grep -qi "delet\|remov" "$SKILL_FILE"
}

# ── T-0018-003: Step 0 detects quality-gate.sh in settings.json ──────

@test "T-0018-003: Step 0 describes detection and removal of quality-gate.sh entry from settings.json" {
  [ -f "$SKILL_FILE" ]
  # Must reference settings.json cleanup
  grep -q "settings.json" "$SKILL_FILE"
  # Must reference quality-gate in the context of settings.json hooks
  local step0_content
  step0_content=$(sed -n '/Step 0/,/### Step 1/p' "$SKILL_FILE")
  echo "$step0_content" | grep -q "quality-gate"
  echo "$step0_content" | grep -q "settings.json"
}

# ── T-0018-004: Step 0 prints removal notice ─────────────────────────

@test "T-0018-004: Step 0 includes notice text 'Removed deprecated quality-gate.sh (see retro lesson #003)'" {
  [ -f "$SKILL_FILE" ]
  grep -q "Removed deprecated quality-gate.sh" "$SKILL_FILE"
  grep -q "retro lesson #003" "$SKILL_FILE"
}

# ── T-0018-005: Source config has dashboard field ─────────────────────

@test "T-0018-005: source/pipeline/pipeline-config.json contains dashboard field set to none" {
  [ -f "$SOURCE_CONFIG" ]
  local val
  val=$(jq -r '.dashboard_mode' "$SOURCE_CONFIG")
  [ "$val" = "none" ]
}

# ── T-0018-006: Installed config has dashboard field ──────────────────

@test "T-0018-006: .claude/pipeline-config.json contains dashboard field set to none" {
  [ -f "$INSTALLED_CONFIG" ]
  local val
  val=$(jq -r '.dashboard_mode' "$INSTALLED_CONFIG")
  [ "$val" = "none" ]
}

# ── T-0018-007: Both config files are valid JSON ─────────────────────

@test "T-0018-007: Both pipeline-config.json files remain valid JSON after modification" {
  jq . "$SOURCE_CONFIG" > /dev/null 2>&1
  jq . "$INSTALLED_CONFIG" > /dev/null 2>&1
}

# ── T-0018-008: File exists but settings.json entry already removed ──

@test "T-0018-008: Step 0 handles case where quality-gate.sh file exists but settings.json entry is already removed" {
  [ -f "$SKILL_FILE" ]
  # Step 0 section must describe handling the file-only case
  local step0_content
  step0_content=$(sed -n '/Step 0/,/### Step 1/p' "$SKILL_FILE")
  # Must mention checking for both artifacts independently (not requiring both)
  echo "$step0_content" | grep -qi "file.*exist\|check.*quality-gate\|if.*found"
}

# ── T-0018-009: Settings entry exists but file does not ──────────────

@test "T-0018-009: Step 0 handles case where settings.json has quality-gate.sh entry but file does not exist" {
  [ -f "$SKILL_FILE" ]
  local step0_content
  step0_content=$(sed -n '/Step 0/,/### Step 1/p' "$SKILL_FILE")
  # Must reference checking settings.json independently of file existence
  echo "$step0_content" | grep -q "settings.json"
}

# ── T-0018-010: Neither artifact found = silent no-op ────────────────

@test "T-0018-010: Step 0 describes silent no-op when neither quality-gate.sh file nor settings.json entry found" {
  [ -f "$SKILL_FILE" ]
  local step0_content
  step0_content=$(sed -n '/Step 0/,/### Step 1/p' "$SKILL_FILE")
  # Must mention the no-op / silent / neither-found case
  echo "$step0_content" | grep -qi "no-op\|silent\|neither.*found\|not found"
}

# ── T-0018-011: Both found = both removed, single notice ────────────

@test "T-0018-011: Step 0 handles both artifacts found -- both removed with single notice (not two)" {
  [ -f "$SKILL_FILE" ]
  local step0_content
  step0_content=$(sed -n '/Step 0/,/### Step 1/p' "$SKILL_FILE")
  # Must mention both file and settings.json removal
  echo "$step0_content" | grep -q "quality-gate"
  # The notice is printed once -- the word "either" indicates the condition
  echo "$step0_content" | grep -qi "either.*found\|both\|single"
}

# ── T-0018-011b: Empty hooks array cleanup ───────────────────────────

@test "T-0018-011b: Step 0 removes event type key entirely when quality-gate.sh was the sole hook (no empty array)" {
  [ -f "$SKILL_FILE" ]
  local step0_content
  step0_content=$(sed -n '/Step 0/,/### Step 1/p' "$SKILL_FILE")
  # Must mention handling empty hooks arrays or removing event type
  echo "$step0_content" | grep -qi "empty.*array\|empty hooks\|event type\|remove.*entry"
}

# ── T-0018-012: Malformed settings.json handling ─────────────────────

@test "T-0018-012: Step 0 logs warning and continues when settings.json is malformed JSON" {
  [ -f "$SKILL_FILE" ]
  local step0_content
  step0_content=$(sed -n '/Step 0/,/### Step 1/p' "$SKILL_FILE")
  # Must reference error handling for malformed JSON
  echo "$step0_content" | grep -qi "malformed\|invalid.*json\|warn\|error.*continu\|does not block"
}

# ── T-0018-013: No existing config fields removed ────────────────────

@test "T-0018-013: No existing fields in either config file are removed after adding dashboard" {
  [ -f "$SOURCE_CONFIG" ]
  [ -f "$INSTALLED_CONFIG" ]
  # Check that all pre-existing fields still exist in source config
  for field in branching_strategy platform platform_cli mr_command merge_command \
    environment_branches base_branch integration_branch sentinel_enabled \
    agent_teams_enabled ci_watch_enabled ci_watch_max_retries \
    ci_watch_poll_command ci_watch_log_command deps_agent_enabled darwin_enabled; do
    jq -e "has(\"$field\")" "$SOURCE_CONFIG" > /dev/null 2>&1 || {
      echo "Missing field '$field' in source config"
      return 1
    }
  done
}

# ── T-0018-014: Existing boolean flags unchanged ─────────────────────

@test "T-0018-014: darwin_enabled, sentinel_enabled, deps_agent_enabled unchanged in source config" {
  [ -f "$SOURCE_CONFIG" ]
  # Source template should have these as false (defaults)
  local darwin sentinel deps
  darwin=$(jq -r '.darwin_enabled' "$SOURCE_CONFIG")
  sentinel=$(jq -r '.sentinel_enabled' "$SOURCE_CONFIG")
  deps=$(jq -r '.deps_agent_enabled' "$SOURCE_CONFIG")
  [ "$darwin" = "false" ]
  [ "$sentinel" = "false" ]
  [ "$deps" = "false" ]
}

# ── T-0018-015: Step 1 unchanged after Step 0 insertion ──────────────

@test "T-0018-015: Step 1 (Gather Project Information) heading and first paragraph are present and intact" {
  [ -f "$SKILL_FILE" ]
  grep -q "### Step 1: Gather Project Information" "$SKILL_FILE"
  # The first sentence of Step 1 should still reference asking the user about their project
  grep -q "Before installing, ask the user about their project" "$SKILL_FILE"
}

# ── T-0018-016: Other hook entries unaffected ────────────────────────

@test "T-0018-016: Step 0 cleanup does not affect other hook entries (enforce-paths, enforce-sequencing, etc.)" {
  [ -f "$SKILL_FILE" ]
  local step0_content
  step0_content=$(sed -n '/Step 0/,/### Step 1/p' "$SKILL_FILE")
  # The Step 0 section must specifically target quality-gate, not all hooks
  echo "$step0_content" | grep -q "quality-gate"
  # Enforce hooks should still be referenced in Step 3a (unchanged)
  grep -q "enforce-eva-paths.sh" "$SKILL_FILE"
  grep -q "enforce-sequencing.sh" "$SKILL_FILE"
  grep -q "enforce-git.sh" "$SKILL_FILE"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 2 Tests: Dashboard Setup Step 6f
# ═══════════════════════════════════════════════════════════════════════

# ── T-0018-017: Step 6f positioned after Darwin, before Brain ────────

@test "T-0018-017: SKILL.md contains Step 6f block positioned after Step 6e (Darwin) and before Brain setup offer" {
  [ -f "$SKILL_FILE" ]
  grep -q "Step 6f" "$SKILL_FILE"
  # Step 6f must appear after Step 6e
  local line_6e line_6f line_brain
  line_6e=$(grep -n "Step 6e" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_6f=$(grep -n "Step 6f" "$SKILL_FILE" | head -1 | cut -d: -f1)
  # Brain setup offer must appear after Step 6f
  line_brain=$(grep -n "Brain setup offer\|set up the.*Atelier Brain\|brain-setup" "$SKILL_FILE" | tail -1 | cut -d: -f1)
  [ -n "$line_6e" ]
  [ -n "$line_6f" ]
  [ -n "$line_brain" ]
  [ "$line_6e" -lt "$line_6f" ]
  [ "$line_6f" -lt "$line_brain" ]
}

# ── T-0018-018: Menu shows 3 options with GitHub links ───────────────

@test "T-0018-018: Step 6f menu shows 3 options with descriptions and GitHub links" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  # Three options
  echo "$step6f_content" | grep -qi "PlanVisualizer"
  echo "$step6f_content" | grep -qi "claude-code-kanban"
  echo "$step6f_content" | grep -qi "None"
  # GitHub links
  echo "$step6f_content" | grep -q "https://github.com/ksyed0/PlanVisualizer"
  echo "$step6f_content" | grep -q "https://github.com/NikiforovAll/claude-code-kanban"
}

# ── T-0018-019: PlanVisualizer sets plan-visualizer config ───────────

@test "T-0018-019: Step 6f PlanVisualizer path sets dashboard to plan-visualizer" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -q '"plan-visualizer"\|plan-visualizer'
}

# ── T-0018-020: claude-code-kanban sets config ───────────────────────

@test "T-0018-020: Step 6f claude-code-kanban path sets dashboard to claude-code-kanban" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -q '"claude-code-kanban"\|dashboard.*claude-code-kanban'
}

# ── T-0018-021: None sets dashboard to none ──────────────────────────

@test "T-0018-021: Step 6f None option sets dashboard to none" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -q '"none"\|dashboard.*none'
}

# ── T-0018-022: PlanVisualizer install path details ──────────────────

@test "T-0018-022: Step 6f PlanVisualizer install describes clone, install script, and bridge script copy" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  # Must mention cloning
  echo "$step6f_content" | grep -qi "clone"
  # Must mention install script
  echo "$step6f_content" | grep -qi "install"
  # Must mention bridge script copy
  echo "$step6f_content" | grep -qi "bridge"
}

# ── T-0018-023: claude-code-kanban install path ──────────────────────

@test "T-0018-023: Step 6f claude-code-kanban install runs npx claude-code-kanban --install" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -q "npx claude-code-kanban --install"
}

# ── T-0018-024: Summary includes dashboard line ──────────────────────

@test "T-0018-024: SKILL.md summary printout includes Dashboard status line" {
  [ -f "$SKILL_FILE" ]
  # The summary section should include a Dashboard line
  grep -q 'Dashboard:' "$SKILL_FILE"
}

# ── T-0018-025: Node.js < 18 warning for PlanVisualizer ─────────────

@test "T-0018-025: Step 6f warns about Node.js 18+ requirement when version is too low" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -qi "Node.js 18\|node.*18"
  echo "$step6f_content" | grep -qi "Skipping\|skip"
}

# ── T-0018-025b: Node command not found ──────────────────────────────

@test "T-0018-025b: Step 6f handles node command not found (distinct from version check)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  # Must reference checking if node exists (command -v or similar)
  echo "$step6f_content" | grep -qi "node.*not found\|node.*version\|command.*node\|Node.js 18"
}

# ── T-0018-026: npx not found warning for kanban ─────────────────────

@test "T-0018-026: Step 6f warns about npm/npx requirement when npx is not found" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -qi "npm/npx\|npx.*not.*found\|requires.*npx"
}

# ── T-0018-027: PlanVisualizer clone failure ─────────────────────────

@test "T-0018-027: Step 6f handles PlanVisualizer clone failure (logs error, sets none, continues)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  # Must reference failure handling that sets dashboard to none
  echo "$step6f_content" | grep -qi "fail\|error"
  echo "$step6f_content" | grep -qi "continu\|never block"
}

# ── T-0018-028: PlanVisualizer install script failure ────────────────

@test "T-0018-028: Step 6f handles PlanVisualizer install script failure (logs error, sets none, continues)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -qi "install.*fail\|fail.*install\|error.*none\|dashboard.*none"
}

# ── T-0018-029: npx install failure ──────────────────────────────────

@test "T-0018-029: Step 6f handles npx claude-code-kanban --install failure (logs error, sets none, continues)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  # Generic error handling covers all install failures
  echo "$step6f_content" | grep -qi "fail\|error"
  echo "$step6f_content" | grep -qi "none"
}

# ── T-0018-029b: Uninstall failure during switch ─────────────────────

@test "T-0018-029b: Step 6f handles uninstall failure when switching from kanban (falls back to manual cleanup)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  # Must reference uninstall or cleanup of old dashboard during switch
  echo "$step6f_content" | grep -qi "uninstall\|clean.*up\|switch\|remov"
}

# ── T-0018-030: Idempotency ──────────────────────────────────────────

@test "T-0018-030: Step 6f includes idempotency check (same choice is no-op)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -qi "idempoten\|already set\|already.*match\|no-op"
}

# ── T-0018-031: Switch PlanVisualizer to kanban ──────────────────────

@test "T-0018-031: Step 6f describes switch from PlanVisualizer to kanban (cleanup PV artifacts first)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  # Must reference switch/cleanup logic for PlanVisualizer artifacts
  echo "$step6f_content" | grep -qi "switch\|clean.*up\|remov.*plan-visualizer\|\.plan-visualizer"
}

# ── T-0018-032: Switch kanban to PlanVisualizer ──────────────────────

@test "T-0018-032: Step 6f describes switch from kanban to PlanVisualizer (cleanup kanban hooks first)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  # Must reference cleanup of kanban hooks during switch
  echo "$step6f_content" | grep -qi "kanban.*clean\|uninstall.*kanban\|hook.*remov\|switch.*from.*kanban"
}

# ── T-0018-033: Switch to None ───────────────────────────────────────

@test "T-0018-033: Step 6f describes switch from any dashboard to None (all artifacts cleaned up)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  # None option should reference cleanup of existing dashboard
  echo "$step6f_content" | grep -qi "None"
  echo "$step6f_content" | grep -qi "clean.*up\|remov"
}

# ── T-0018-034: Both dashboards detected ─────────────────────────────

@test "T-0018-034: Step 6f handles both dashboards detected (forces choice, announces conflict)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -qi "both.*dashboard\|both.*detected\|conflict"
}

# ── T-0018-035: Brain not configured + PlanVisualizer ────────────────

@test "T-0018-035: Step 6f notes that PlanVisualizer works without brain (bridge falls back to pipeline-state.md)" {
  [ -f "$SKILL_FILE" ]
  local step6f_content
  step6f_content=$(sed -n '/Step 6f/,/^### /p' "$SKILL_FILE")
  echo "$step6f_content" | grep -qi "brain.*not\|fallback\|pipeline-state\|without.*brain"
}

# ── T-0018-036: Step 6e unchanged ────────────────────────────────────

@test "T-0018-036: Step 6e (Darwin) block heading is unchanged after Step 6f insertion" {
  [ -f "$SKILL_FILE" ]
  grep -q "### Step 6e: Darwin Self-Evolving Pipeline" "$SKILL_FILE"
}

# ── T-0018-037: Brain offer after Step 6f ────────────────────────────

@test "T-0018-037: Brain setup offer is positioned after Step 6f" {
  [ -f "$SKILL_FILE" ]
  local line_6f line_brain
  line_6f=$(grep -n "Step 6f" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_brain=$(grep -n "set up the.*Atelier Brain\|brain-setup\|Brain setup offer" "$SKILL_FILE" | tail -1 | cut -d: -f1)
  [ -n "$line_6f" ]
  [ -n "$line_brain" ]
  [ "$line_6f" -lt "$line_brain" ]
}

# ── T-0018-038: Steps 6a-6d unchanged ────────────────────────────────

@test "T-0018-038: Steps 6a through 6d headings are unchanged after Step 6f insertion" {
  [ -f "$SKILL_FILE" ]
  grep -q "### Step 6a: Sentinel Security Agent" "$SKILL_FILE"
  grep -q "### Step 6b: Agent Teams Opt-In" "$SKILL_FILE"
  grep -q "### Step 6c: CI Watch Opt-In" "$SKILL_FILE"
  grep -q "### Step 6d: Deps Agent Opt-In" "$SKILL_FILE"
}

# ── T-0018-038b: Brain offer paragraph updated ───────────────────────

@test "T-0018-038b: Brain setup offer intro references 'After the Dashboard offer' (not 'After the Darwin offer')" {
  [ -f "$SKILL_FILE" ]
  # The Brain offer paragraph should reference Dashboard, not Darwin
  grep -q "After the Dashboard offer" "$SKILL_FILE"
  # The old phrasing should be gone from the Brain offer context
  # (Note: "After the Darwin offer" may still exist in Darwin's own section, but not in Brain intro)
  local brain_section
  brain_section=$(sed -n '/Brain setup offer/,/### Step 7/p' "$SKILL_FILE")
  if echo "$brain_section" | grep -q "After the Darwin offer"; then
    echo "Brain setup offer still references 'After the Darwin offer' instead of 'After the Dashboard offer'"
    return 1
  fi
}

# ═══════════════════════════════════════════════════════════════════════
# Step 3 Tests: Bridge Script
# ═══════════════════════════════════════════════════════════════════════

# ── T-0018-039: Bridge script exists and is executable ───────────────

@test "T-0018-039: source/dashboard/telemetry-bridge.sh exists and is executable" {
  [ -f "$BRIDGE_SCRIPT" ]
  [ -x "$BRIDGE_SCRIPT" ]
}

# ── T-0018-040: Bridge reads brain and generates PIPELINE_PLAN.md ────

@test "T-0018-040: Bridge script contains brain telemetry reading logic and PIPELINE_PLAN.md generation" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # Must reference brain API / telemetry reading
  grep -qi "brain\|telemetry\|curl\|api" "$BRIDGE_SCRIPT"
  # Must reference PIPELINE_PLAN.md output
  grep -q "PIPELINE_PLAN.md\|PIPELINE_PLAN" "$BRIDGE_SCRIPT"
  # Must contain EPIC/Story/Task structure markers
  grep -qi "EPIC\|epic" "$BRIDGE_SCRIPT"
  grep -qi "Story\|story" "$BRIDGE_SCRIPT"
}

# ── T-0018-041: T3 pipeline_id maps to EPIC title ───────────────────

@test "T-0018-041: Bridge script maps T3 pipeline_id to EPIC title" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -qi "pipeline_id\|EPIC" "$BRIDGE_SCRIPT"
}

# ── T-0018-042: T2 work_unit_id maps to Story title ─────────────────

@test "T-0018-042: Bridge script maps T2 work_unit_id to Story title with status" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -qi "work_unit_id\|Story\|status" "$BRIDGE_SCRIPT"
}

# ── T-0018-043: T1 agent invocations map to Tasks ───────────────────

@test "T-0018-043: Bridge script maps T1 agent invocations to Tasks with duration" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -qi "agent_name\|duration\|Task\|task" "$BRIDGE_SCRIPT"
}

# ── T-0018-043b: T2 rework_cycles maps to Story metadata ────────────

@test "T-0018-043b: Bridge script maps T2 rework_cycles to Story metadata field" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -qi "rework_cycles\|rework" "$BRIDGE_SCRIPT"
}

# ── T-0018-043c: T3 rework_rate maps to EPIC summary ────────────────

@test "T-0018-043c: Bridge script maps T3 rework_rate to EPIC summary metric field" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -qi "rework_rate" "$BRIDGE_SCRIPT"
}

# ── T-0018-044: Cost data from T3 ───────────────────────────────────

@test "T-0018-044: Bridge script includes cost data from T3 total_cost_usd" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -qi "total_cost_usd\|cost" "$BRIDGE_SCRIPT"
}

# ── T-0018-045: Output parseable by PlanVisualizer ───────────────────

@test "T-0018-045: Bridge script output follows PlanVisualizer PIPELINE_PLAN.md format (EPIC/Story/Task headings)" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # The script must produce markdown with the expected heading structure
  # Check that it generates lines matching PlanVisualizer's expected format
  grep -q "PIPELINE_PLAN" "$BRIDGE_SCRIPT"
  # Must contain format-producing logic (echo/printf/cat with markdown headings)
  grep -qE '##.*EPIC|##.*Story|PIPELINE_PLAN' "$BRIDGE_SCRIPT"
}

# ── T-0018-046: Fallback to pipeline-state.md ────────────────────────

@test "T-0018-046: Bridge script falls back to pipeline-state.md when brain is unavailable" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -q "pipeline-state.md\|pipeline-state" "$BRIDGE_SCRIPT"
  # Must have conditional logic for brain unavailability
  grep -qi "fallback\|unavailable\|fail\|else\|brain.*not\|cannot.*reach" "$BRIDGE_SCRIPT"
}

# ── T-0018-047: Runs generate-plan.js when node available ────────────

@test "T-0018-047: Bridge script runs node tools/generate-plan.js when node is available" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -q "generate-plan.js\|generate-plan" "$BRIDGE_SCRIPT"
  grep -q "node" "$BRIDGE_SCRIPT"
}

# ── T-0018-048: No data = minimal placeholder ────────────────────────

@test "T-0018-048: Bridge script generates minimal PIPELINE_PLAN.md with placeholder when no data exists" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -qi "No pipeline data\|placeholder\|no.*data\|empty" "$BRIDGE_SCRIPT"
}

# ── T-0018-049: Node not found = write markdown, skip HTML ──────────

@test "T-0018-049: Bridge script skips HTML regeneration when node is not found and logs message" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # Must check for node availability
  grep -qi "command.*node\|which.*node\|node.*not found\|skip.*html\|skip.*generat" "$BRIDGE_SCRIPT"
}

# ── T-0018-050: Brain API error = fallback ───────────────────────────

@test "T-0018-050: Bridge script falls back to pipeline-state.md when brain HTTP API returns error" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # Must have error handling for HTTP responses (curl exit code or HTTP status)
  grep -qE 'curl.*-[sfSw]|http_code|status|exit.*code|\$\?' "$BRIDGE_SCRIPT"
}

# ── T-0018-051: Malformed brain response = fallback ──────────────────

@test "T-0018-051: Bridge script handles malformed brain response (falls back, logs parse error)" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # Must have JSON parsing with error handling (jq with error check or similar)
  grep -qE 'jq|parse|json|malformed' "$BRIDGE_SCRIPT"
}

# ── T-0018-051b: Permission denied on output ─────────────────────────

@test "T-0018-051b: Bridge script handles permission denied on PIPELINE_PLAN.md write (exits 0, logs error)" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # Script must not exit non-zero on write failure
  # Check for write error handling (redirect error check or trap)
  grep -qE 'permission|cannot write|write.*fail|> .*PIPELINE|tee|2>' "$BRIDGE_SCRIPT"
}

# ── T-0018-051c: Brain API timeout ──────────────────────────────────

@test "T-0018-051c: Bridge script handles brain HTTP API timeout (falls back to pipeline-state.md)" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # Must have a timeout on the HTTP request (curl --connect-timeout or --max-time)
  grep -qE 'timeout|max-time|connect-timeout' "$BRIDGE_SCRIPT"
}

# ── T-0018-052: CLI flags supported ─────────────────────────────────

@test "T-0018-052: Bridge script accepts --brain-url, --pipeline-state, --output, --skip-generate flags" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  grep -q "\-\-brain-url" "$BRIDGE_SCRIPT"
  grep -q "\-\-pipeline-state" "$BRIDGE_SCRIPT"
  grep -q "\-\-output" "$BRIDGE_SCRIPT"
  grep -q "\-\-skip-generate" "$BRIDGE_SCRIPT"
}

# ── T-0018-053: Always exits 0 ──────────────────────────────────────

@test "T-0018-053: Bridge script exits 0 in all code paths (non-blocking)" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # Check that exit statements use 0 (or there are no non-zero exit calls)
  # Any explicit exit with non-zero is a failure
  if grep -qE 'exit [1-9]' "$BRIDGE_SCRIPT"; then
    echo "Bridge script contains non-zero exit codes"
    grep -n 'exit [1-9]' "$BRIDGE_SCRIPT"
    return 1
  fi
}

# ── T-0018-054: Full regeneration (not append) ──────────────────────

@test "T-0018-054: Bridge script performs full regeneration of PIPELINE_PLAN.md (not append)" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # Must use overwrite (>) not append (>>) for the output file
  # Or must write to a temp file and move, or use a variable that is written at once
  # Should NOT have >> PIPELINE_PLAN.md as the primary write pattern
  if grep -qE '>>\s*.*PIPELINE_PLAN' "$BRIDGE_SCRIPT"; then
    echo "Bridge script appends to PIPELINE_PLAN.md instead of overwriting"
    grep -n '>>' "$BRIDGE_SCRIPT"
    return 1
  fi
}

# ── T-0018-055: No credentials in output ─────────────────────────────

@test "T-0018-055: Bridge script does not expose brain credentials in output or error messages" {
  [ -f "$BRIDGE_SCRIPT" ] || skip "Bridge script not yet created"
  # Check that error messages/logs do not echo the brain URL with credentials
  # The brain URL should be used for the request but not printed verbatim
  # Look for patterns that would print the full URL in error messages
  if grep -qE 'echo.*\$.*brain.*url|echo.*\$.*BRAIN.*URL|printf.*brain.*url' "$BRIDGE_SCRIPT"; then
    # If it prints the URL, it must be masked or truncated
    local url_prints
    url_prints=$(grep -nE 'echo.*\$.*brain.*url|echo.*\$.*BRAIN.*URL' "$BRIDGE_SCRIPT")
    # Check if the print is masked (contains ... or [redacted] or similar)
    if ! echo "$url_prints" | grep -qi 'redact\|mask\|\.\.\.\|truncat'; then
      echo "Bridge script may expose brain credentials in output"
      echo "$url_prints"
      return 1
    fi
  fi
}

# ═══════════════════════════════════════════════════════════════════════
# Step 4 Tests: Post-Pipeline Wiring + Eva Announcement
# ═══════════════════════════════════════════════════════════════════════

# ── T-0018-056: Dashboard Bridge section in source orchestration ─────

@test "T-0018-056: source/rules/pipeline-orchestration.md contains 'Dashboard Bridge' section after Pattern Staleness Check" {
  [ -f "$SOURCE_ORCH" ]
  grep -q "Dashboard Bridge" "$SOURCE_ORCH"
  # Must appear after Pattern Staleness Check
  local line_staleness line_dashboard
  line_staleness=$(grep -n "Pattern Staleness Check" "$SOURCE_ORCH" | head -1 | cut -d: -f1)
  line_dashboard=$(grep -n "Dashboard Bridge" "$SOURCE_ORCH" | head -1 | cut -d: -f1)
  [ -n "$line_staleness" ]
  [ -n "$line_dashboard" ]
  [ "$line_staleness" -lt "$line_dashboard" ]
}

# ── T-0018-057: Dual tree parity for orchestration ──────────────────

@test "T-0018-057: .claude/rules/pipeline-orchestration.md contains identical Dashboard Bridge section (dual tree parity)" {
  [ -f "$SOURCE_ORCH" ]
  [ -f "$INSTALLED_ORCH" ]
  # Extract Dashboard Bridge sections from both and compare
  local source_section installed_section
  source_section=$(sed -n '/Dashboard Bridge/,/^###\|^<\//p' "$SOURCE_ORCH" | head -20)
  installed_section=$(sed -n '/Dashboard Bridge/,/^###\|^<\//p' "$INSTALLED_ORCH" | head -20)
  [ -n "$source_section" ]
  [ -n "$installed_section" ]
  [ "$source_section" = "$installed_section" ]
}

# ── T-0018-058: Bridge runs only for plan-visualizer ─────────────────

@test "T-0018-058: Dashboard Bridge section specifies it runs only when dashboard is plan-visualizer" {
  [ -f "$SOURCE_ORCH" ]
  local dashboard_section
  dashboard_section=$(sed -n '/Dashboard Bridge/,/^###\|^<\//p' "$SOURCE_ORCH")
  [ -n "$dashboard_section" ]
  echo "$dashboard_section" | grep -qi "plan-visualizer"
}

# ── T-0018-059: Bridge failure is non-blocking ──────────────────────

@test "T-0018-059: Dashboard Bridge section documents failure as non-blocking" {
  [ -f "$SOURCE_ORCH" ]
  local dashboard_section
  dashboard_section=$(sed -n '/Dashboard Bridge/,/^###\|^<\//p' "$SOURCE_ORCH")
  [ -n "$dashboard_section" ]
  echo "$dashboard_section" | grep -qi "never.*block\|non-blocking\|not.*blocker\|fail.*continu"
}

# ── T-0018-060: dashboard-bridge template in source invocation templates

@test "T-0018-060: source/references/invocation-templates.md contains template id dashboard-bridge" {
  [ -f "$SOURCE_TEMPLATES" ]
  grep -q '<template id="dashboard-bridge">' "$SOURCE_TEMPLATES"
}

# ── T-0018-061: Dual tree parity for invocation templates ────────────

@test "T-0018-061: .claude/references/invocation-templates.md contains identical dashboard-bridge template (dual tree parity)" {
  [ -f "$SOURCE_TEMPLATES" ]
  [ -f "$INSTALLED_TEMPLATES" ]
  # Both must have the template
  grep -q '<template id="dashboard-bridge">' "$INSTALLED_TEMPLATES"
  # Extract and compare template blocks
  local source_tmpl installed_tmpl
  source_tmpl=$(sed -n '/<template id="dashboard-bridge">/,/<\/template>/p' "$SOURCE_TEMPLATES")
  installed_tmpl=$(sed -n '/<template id="dashboard-bridge">/,/<\/template>/p' "$INSTALLED_TEMPLATES")
  [ -n "$source_tmpl" ]
  [ -n "$installed_tmpl" ]
  [ "$source_tmpl" = "$installed_tmpl" ]
}

# ── T-0018-062: Eva boot announcement for dashboard ──────────────────

@test "T-0018-062: pipeline-orchestration.md documents dashboard boot announcement for non-none values" {
  # Dashboard announcement is documented in pipeline-orchestration.md (not default-persona.md)
  [ -f "$SOURCE_ORCH" ]
  # Must have a section describing dashboard announcement at boot
  # Check specifically within or near the Dashboard Bridge section
  local dashboard_content
  dashboard_content=$(sed -n '/Dashboard Bridge/,/^## [^#]\|^<gate\|^<protocol/p' "$SOURCE_ORCH")
  [ -n "$dashboard_content" ]
  echo "$dashboard_content" | grep -qi "boot\|announcement\|announc\|Dashboard:.*PlanVisualizer\|Dashboard:.*claude-code-kanban"
}

# ── T-0018-063: Bridge skipped for kanban ────────────────────────────

@test "T-0018-063: Dashboard Bridge is skipped when dashboard is claude-code-kanban" {
  [ -f "$SOURCE_ORCH" ]
  local dashboard_section
  dashboard_section=$(sed -n '/Dashboard Bridge/,/^###\|^<\//p' "$SOURCE_ORCH")
  [ -n "$dashboard_section" ]
  # Must explicitly mention kanban is passive / skipped
  echo "$dashboard_section" | grep -qi "kanban\|passive\|skip"
}

# ── T-0018-064: Bridge skipped for none ──────────────────────────────

@test "T-0018-064: Dashboard Bridge is skipped when dashboard is none or field is absent" {
  [ -f "$SOURCE_ORCH" ]
  local dashboard_section
  dashboard_section=$(sed -n '/Dashboard Bridge/,/^###\|^<\//p' "$SOURCE_ORCH")
  [ -n "$dashboard_section" ]
  echo "$dashboard_section" | grep -qi "none\|absent\|skip"
}

# ── T-0018-065: Dashboard Bridge positioned correctly ────────────────

@test "T-0018-065: Dashboard Bridge section is after Pattern Staleness, before Mandatory Gates" {
  [ -f "$SOURCE_ORCH" ]
  local line_staleness line_dashboard
  line_staleness=$(grep -n "Pattern Staleness Check" "$SOURCE_ORCH" | head -1 | cut -d: -f1)
  line_dashboard=$(grep -n "Dashboard Bridge" "$SOURCE_ORCH" | head -1 | cut -d: -f1)
  [ -n "$line_staleness" ]
  [ -n "$line_dashboard" ]
  [ "$line_staleness" -lt "$line_dashboard" ]
  # Dashboard Bridge should be before mandatory gates
  local line_gates
  line_gates=$(grep -n "Mandatory Gates" "$SOURCE_ORCH" | head -1 | cut -d: -f1)
  if [ -n "$line_gates" ]; then
    [ "$line_dashboard" -lt "$line_gates" ]
  fi
}

# ── T-0018-066: Boot omits dashboard line for none ───────────────────

@test "T-0018-066: Eva boot announcement omits dashboard line when dashboard is none or absent" {
  [ -f "$SOURCE_ORCH" ]
  # Must check specifically in the Dashboard section (not elsewhere in the file)
  local dashboard_content
  dashboard_content=$(sed -n '/Dashboard Bridge/,/^## [^#]\|^<gate\|^<protocol/p' "$SOURCE_ORCH")
  # If Dashboard Bridge section does not exist yet, this test should fail
  [ -n "$dashboard_content" ]
  # The dashboard section must describe omission for "none" or absent
  echo "$dashboard_content" | grep -qi 'none.*omit\|none.*skip\|absent\|omit.*dashboard\|"none"'
}

# ── T-0018-067: Existing orchestration sections unchanged ────────────

@test "T-0018-067: Existing pipeline-orchestration.md sections (telemetry, Darwin, Pattern Staleness) are unchanged" {
  [ -f "$SOURCE_ORCH" ]
  # Key existing sections must still be present
  grep -q "Pattern Staleness Check" "$SOURCE_ORCH"
  grep -q "Darwin auto-trigger" "$SOURCE_ORCH"
  # The telemetry section header (varies; check for brain/telemetry capture)
  grep -qi "telemetry\|brain capture\|Tier 1\|Tier 2\|Tier 3" "$SOURCE_ORCH"
}

# ── T-0018-068: Existing invocation templates unchanged ──────────────

@test "T-0018-068: Existing invocation templates are unchanged after dashboard-bridge addition" {
  [ -f "$SOURCE_TEMPLATES" ]
  # Spot-check that established templates still exist
  grep -q '<template id="cal-adr">' "$SOURCE_TEMPLATES"
  grep -q '<template id="colby-build">' "$SOURCE_TEMPLATES"
  grep -q '<template id="roz-code-qa">' "$SOURCE_TEMPLATES"
  grep -q '<template id="ellis-commit">' "$SOURCE_TEMPLATES"
  grep -q '<template id="darwin-analysis">' "$SOURCE_TEMPLATES"
  grep -q '<template id="darwin-edit-proposal">' "$SOURCE_TEMPLATES"
}

# ── T-0018-069: Eva boot steps 1-6 unchanged ────────────────────────

@test "T-0018-069: Eva boot sequence steps 1-6 in default-persona.md are unchanged except conditional dashboard line" {
  local eva_file="$PROJECT_ROOT/.claude/rules/default-persona.md"
  [ -f "$eva_file" ]
  # Boot sequence steps should be intact
  grep -q "Read.*pipeline-state.md" "$eva_file"
  grep -q "Read.*context-brief.md" "$eva_file"
  grep -q "Scan.*error-patterns.md" "$eva_file"
  grep -q "Brain health check" "$eva_file"
  grep -q "Brain context retrieval" "$eva_file"
  grep -q "Announce session state" "$eva_file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 5 Tests: Enforcement Hook Bypass for /pipeline-setup
# ═══════════════════════════════════════════════════════════════════════

SOURCE_ENFORCE_PATHS="$PROJECT_ROOT/source/claude/hooks/enforce-eva-paths.sh"
SOURCE_ENFORCE_SEQ="$PROJECT_ROOT/source/claude/hooks/enforce-sequencing.sh"
SOURCE_ENFORCE_GIT="$PROJECT_ROOT/source/claude/hooks/enforce-git.sh"
INSTALLED_ENFORCE_PATHS="$PROJECT_ROOT/.claude/hooks/enforce-eva-paths.sh"
INSTALLED_ENFORCE_SEQ="$PROJECT_ROOT/.claude/hooks/enforce-sequencing.sh"
INSTALLED_ENFORCE_GIT="$PROJECT_ROOT/.claude/hooks/enforce-git.sh"
SOURCE_WARN_DOD="$PROJECT_ROOT/source/claude/hooks/warn-dor-dod.sh"
SOURCE_PRE_COMPACT="$PROJECT_ROOT/source/claude/hooks/pre-compact.sh"
SOURCE_ENFORCE_ACTIVATION="$PROJECT_ROOT/source/claude/hooks/enforce-pipeline-activation.sh"

# ── T-0018-070: Bypass line in source enforce-eva-paths.sh ──────────

@test "T-0018-070: source/claude/hooks/enforce-eva-paths.sh contains bypass line as first executable line after set -uo pipefail" {
  [ -f "$SOURCE_ENFORCE_PATHS" ]
  # The bypass line must exist
  grep -q '"\${ATELIER_SETUP_MODE:-}" = "1"' "$SOURCE_ENFORCE_PATHS"
  # It must be the first executable line after set -uo pipefail
  # Extract lines between 'set -uo pipefail' and 'INPUT=$(cat)'
  local between
  between=$(sed -n '/^set -uo pipefail$/,/^INPUT=\$(cat)$/p' "$SOURCE_ENFORCE_PATHS" | sed '1d;$d')
  # The first non-blank, non-comment line in that range must be the bypass
  local first_exec
  first_exec=$(echo "$between" | grep -v '^\s*$' | grep -v '^\s*#' | head -1)
  echo "$first_exec" | grep -q 'ATELIER_SETUP_MODE'
}

# ── T-0018-071: Bypass line in source enforce-sequencing.sh ─────────

@test "T-0018-071: source/claude/hooks/enforce-sequencing.sh contains the identical bypass line after set -euo pipefail" {
  [ -f "$SOURCE_ENFORCE_SEQ" ]
  grep -q '"\${ATELIER_SETUP_MODE:-}" = "1"' "$SOURCE_ENFORCE_SEQ"
  # Verify positioning: between set -euo pipefail and INPUT=$(cat)
  local between
  between=$(sed -n '/^set -euo pipefail$/,/^INPUT=\$(cat)$/p' "$SOURCE_ENFORCE_SEQ" | sed '1d;$d')
  local first_exec
  first_exec=$(echo "$between" | grep -v '^\s*$' | grep -v '^\s*#' | head -1)
  echo "$first_exec" | grep -q 'ATELIER_SETUP_MODE'
}

# ── T-0018-072: Bypass line in source enforce-git.sh ────────────────

@test "T-0018-072: source/claude/hooks/enforce-git.sh contains the identical bypass line after set -euo pipefail" {
  [ -f "$SOURCE_ENFORCE_GIT" ]
  grep -q '"\${ATELIER_SETUP_MODE:-}" = "1"' "$SOURCE_ENFORCE_GIT"
  local between
  between=$(sed -n '/^set -euo pipefail$/,/^INPUT=\$(cat)$/p' "$SOURCE_ENFORCE_GIT" | sed '1d;$d')
  local first_exec
  first_exec=$(echo "$between" | grep -v '^\s*$' | grep -v '^\s*#' | head -1)
  echo "$first_exec" | grep -q 'ATELIER_SETUP_MODE'
}

# ── T-0018-073: Dual tree parity for enforce-eva-paths.sh ──────────

@test "T-0018-073: .claude/hooks/enforce-eva-paths.sh contains the identical bypass line (dual tree parity with source/)" {
  [ -f "$INSTALLED_ENFORCE_PATHS" ]
  grep -q '"\${ATELIER_SETUP_MODE:-}" = "1"' "$INSTALLED_ENFORCE_PATHS"
  # Verify the bypass line is identical to the source copy
  local source_line installed_line
  source_line=$(grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_PATHS")
  installed_line=$(grep 'ATELIER_SETUP_MODE' "$INSTALLED_ENFORCE_PATHS")
  [ "$source_line" = "$installed_line" ]
}

# ── T-0018-074: Dual tree parity for enforce-sequencing.sh ─────────

@test "T-0018-074: .claude/hooks/enforce-sequencing.sh contains the identical bypass line (dual tree parity)" {
  [ -f "$INSTALLED_ENFORCE_SEQ" ]
  grep -q '"\${ATELIER_SETUP_MODE:-}" = "1"' "$INSTALLED_ENFORCE_SEQ"
  local source_line installed_line
  source_line=$(grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_SEQ")
  installed_line=$(grep 'ATELIER_SETUP_MODE' "$INSTALLED_ENFORCE_SEQ")
  [ "$source_line" = "$installed_line" ]
}

# ── T-0018-075: Dual tree parity for enforce-git.sh ────────────────

@test "T-0018-075: .claude/hooks/enforce-git.sh contains the identical bypass line (dual tree parity)" {
  [ -f "$INSTALLED_ENFORCE_GIT" ]
  grep -q '"\${ATELIER_SETUP_MODE:-}" = "1"' "$INSTALLED_ENFORCE_GIT"
  local source_line installed_line
  source_line=$(grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_GIT")
  installed_line=$(grep 'ATELIER_SETUP_MODE' "$INSTALLED_ENFORCE_GIT")
  [ "$source_line" = "$installed_line" ]
}

# ── T-0018-076: SKILL.md exports ATELIER_SETUP_MODE before Step 3 ──

@test "T-0018-076: SKILL.md contains export ATELIER_SETUP_MODE=1 instruction positioned before Step 3 and after Step 2" {
  [ -f "$SKILL_FILE" ]
  # Must contain the export instruction
  grep -q 'export ATELIER_SETUP_MODE=1' "$SKILL_FILE"
  # Must appear after Step 2 and before Step 3
  local line_step2 line_export line_step3
  line_step2=$(grep -n "### Step 2:" "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_export=$(grep -n 'ATELIER_SETUP_MODE' "$SKILL_FILE" | head -1 | cut -d: -f1)
  line_step3=$(grep -n "### Step 3:" "$SKILL_FILE" | head -1 | cut -d: -f1)
  [ -n "$line_step2" ]
  [ -n "$line_export" ]
  [ -n "$line_step3" ]
  [ "$line_step2" -lt "$line_export" ]
  [ "$line_export" -lt "$line_step3" ]
}

# ── T-0018-077: SKILL.md documents session-scoped variable ─────────

@test "T-0018-077: SKILL.md documents that ATELIER_SETUP_MODE is session-scoped (expires naturally)" {
  [ -f "$SKILL_FILE" ]
  # The documentation near the export must mention session scope
  local setup_mode_context
  setup_mode_context=$(grep -A 5 -B 5 'ATELIER_SETUP_MODE' "$SKILL_FILE")
  echo "$setup_mode_context" | grep -qi "session.scoped\|session scope\|expires.*natural\|session ends"
}

# ── T-0018-078: Bypass exits before INPUT=$(cat) in enforce-eva-paths

@test "T-0018-078: When ATELIER_SETUP_MODE=1, enforce-eva-paths.sh exits 0 without reading stdin (INPUT=\$(cat) is never reached)" {
  [ -f "$SOURCE_ENFORCE_PATHS" ]
  # Verify bypass line appears BEFORE INPUT=$(cat)
  local line_bypass line_input
  line_bypass=$(grep -n 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_PATHS" | head -1 | cut -d: -f1)
  line_input=$(grep -n 'INPUT=\$(cat)' "$SOURCE_ENFORCE_PATHS" | head -1 | cut -d: -f1)
  [ -n "$line_bypass" ]
  [ -n "$line_input" ]
  [ "$line_bypass" -lt "$line_input" ]
  # Verify the bypass line exits 0 (contains 'exit 0')
  grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_PATHS" | grep -q 'exit 0'
}

# ── T-0018-079: Bypass exits before INPUT=$(cat) in enforce-seq ─────

@test "T-0018-079: When ATELIER_SETUP_MODE=1, enforce-sequencing.sh exits 0 without reading stdin" {
  [ -f "$SOURCE_ENFORCE_SEQ" ]
  local line_bypass line_input
  line_bypass=$(grep -n 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_SEQ" | head -1 | cut -d: -f1)
  line_input=$(grep -n 'INPUT=\$(cat)' "$SOURCE_ENFORCE_SEQ" | head -1 | cut -d: -f1)
  [ -n "$line_bypass" ]
  [ -n "$line_input" ]
  [ "$line_bypass" -lt "$line_input" ]
  grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_SEQ" | grep -q 'exit 0'
}

# ── T-0018-080: Bypass exits before INPUT=$(cat) in enforce-git ─────

@test "T-0018-080: When ATELIER_SETUP_MODE=1, enforce-git.sh exits 0 without reading stdin" {
  [ -f "$SOURCE_ENFORCE_GIT" ]
  local line_bypass line_input
  line_bypass=$(grep -n 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_GIT" | head -1 | cut -d: -f1)
  line_input=$(grep -n 'INPUT=\$(cat)' "$SOURCE_ENFORCE_GIT" | head -1 | cut -d: -f1)
  [ -n "$line_bypass" ]
  [ -n "$line_input" ]
  [ "$line_bypass" -lt "$line_input" ]
  grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_GIT" | grep -q 'exit 0'
}

# ── T-0018-081: Unset variable = normal enforcement ─────────────────

@test "T-0018-081: When ATELIER_SETUP_MODE is unset, enforce-eva-paths.sh proceeds to normal enforcement (existing behavior)" {
  [ -f "$SOURCE_ENFORCE_PATHS" ]
  # Run the hook with unset ATELIER_SETUP_MODE and a blocked write
  # The hook should block (exit 2) for writes outside docs/pipeline/
  local result
  unset ATELIER_SETUP_MODE
  result=$(echo '{"tool_name":"Write","tool_input":{"file_path":"src/main.js"}}' \
    | CLAUDE_PROJECT_DIR="$PROJECT_ROOT" bash "$SOURCE_ENFORCE_PATHS" 2>&1; echo "EXIT:$?")
  # Should be blocked (exit 2) -- Eva can only write to docs/pipeline/
  echo "$result" | grep -q "EXIT:2"
}

# ── T-0018-082: Empty string = normal enforcement ───────────────────

@test "T-0018-082: When ATELIER_SETUP_MODE is empty string, enforce-eva-paths.sh proceeds to normal enforcement" {
  [ -f "$SOURCE_ENFORCE_PATHS" ]
  local result
  result=$(echo '{"tool_name":"Write","tool_input":{"file_path":"src/main.js"}}' \
    | ATELIER_SETUP_MODE="" CLAUDE_PROJECT_DIR="$PROJECT_ROOT" bash "$SOURCE_ENFORCE_PATHS" 2>&1; echo "EXIT:$?")
  echo "$result" | grep -q "EXIT:2"
}

# ── T-0018-083: "true" = normal enforcement ─────────────────────────

@test "T-0018-083: When ATELIER_SETUP_MODE=true, enforce-eva-paths.sh proceeds to normal enforcement (truthy is not 1)" {
  [ -f "$SOURCE_ENFORCE_PATHS" ]
  local result
  result=$(echo '{"tool_name":"Write","tool_input":{"file_path":"src/main.js"}}' \
    | ATELIER_SETUP_MODE="true" CLAUDE_PROJECT_DIR="$PROJECT_ROOT" bash "$SOURCE_ENFORCE_PATHS" 2>&1; echo "EXIT:$?")
  echo "$result" | grep -q "EXIT:2"
}

# ── T-0018-084: "0" = normal enforcement ────────────────────────────

@test "T-0018-084: When ATELIER_SETUP_MODE=0, enforce-eva-paths.sh proceeds to normal enforcement (0 is not 1)" {
  [ -f "$SOURCE_ENFORCE_PATHS" ]
  local result
  result=$(echo '{"tool_name":"Write","tool_input":{"file_path":"src/main.js"}}' \
    | ATELIER_SETUP_MODE="0" CLAUDE_PROJECT_DIR="$PROJECT_ROOT" bash "$SOURCE_ENFORCE_PATHS" 2>&1; echo "EXIT:$?")
  echo "$result" | grep -q "EXIT:2"
}

# ── T-0018-085: "2" = normal enforcement in enforce-sequencing ──────

@test "T-0018-085: When ATELIER_SETUP_MODE=2, enforce-sequencing.sh proceeds to normal enforcement (only exact 1 triggers bypass)" {
  [ -f "$SOURCE_ENFORCE_SEQ" ]
  # The bypass line checks for exact "1" -- "2" should not trigger it
  # Verify structurally: the bypass condition requires = "1"
  grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_SEQ" | grep -q '= "1"'
  # The condition is an exact string match, so "2" will not match
  # Verify by checking the bypass line syntax uses = not -n or -z
  local bypass_line
  bypass_line=$(grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_SEQ")
  # Must use = "1" (exact match), not just -n (non-empty check)
  echo "$bypass_line" | grep -qv '\-n'
  echo "$bypass_line" | grep -qv '\-z'
}

# ── T-0018-086: Trailing space = normal enforcement in enforce-git ──

@test "T-0018-086: When ATELIER_SETUP_MODE has trailing space, enforce-git.sh proceeds to normal enforcement (no trimming)" {
  [ -f "$SOURCE_ENFORCE_GIT" ]
  # The bypass uses [ "${ATELIER_SETUP_MODE:-}" = "1" ] which is an exact match
  # "1 " (with trailing space) does not equal "1"
  # Verify structurally: the comparison is exact string = "1"
  local bypass_line
  bypass_line=$(grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_GIT")
  # Must be = "1" comparison (shell [ ] does exact string matching)
  echo "$bypass_line" | grep -q '= "1"'
  # Must NOT contain any trim/strip/sed logic
  echo "$bypass_line" | grep -qv 'sed\|tr\|trim\|strip'
}

# ── T-0018-087: Uses ${:-} syntax for set -u safety ────────────────

@test "T-0018-087: Bypass line uses \${ATELIER_SETUP_MODE:-} syntax to avoid set -u unbound variable error" {
  [ -f "$SOURCE_ENFORCE_PATHS" ]
  [ -f "$SOURCE_ENFORCE_SEQ" ]
  [ -f "$SOURCE_ENFORCE_GIT" ]
  # All three hooks must use the :- default syntax
  grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_PATHS" | grep -q ':-}'
  grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_SEQ" | grep -q ':-}'
  grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_GIT" | grep -q ':-}'
}

# ── T-0018-088: Bypass line before INPUT=$(cat) in all hooks ────────

@test "T-0018-088: The bypass line is positioned BEFORE INPUT=\$(cat) in all three source hooks" {
  for hook in "$SOURCE_ENFORCE_PATHS" "$SOURCE_ENFORCE_SEQ" "$SOURCE_ENFORCE_GIT"; do
    [ -f "$hook" ]
    local line_bypass line_input
    line_bypass=$(grep -n 'ATELIER_SETUP_MODE' "$hook" | head -1 | cut -d: -f1)
    line_input=$(grep -n 'INPUT=\$(cat)' "$hook" | head -1 | cut -d: -f1)
    [ -n "$line_bypass" ] || { echo "Missing bypass line in $hook"; return 1; }
    [ -n "$line_input" ] || { echo "Missing INPUT=\$(cat) in $hook"; return 1; }
    [ "$line_bypass" -lt "$line_input" ] || {
      echo "Bypass line (L$line_bypass) is NOT before INPUT=\$(cat) (L$line_input) in $hook"
      return 1
    }
  done
}

# ── T-0018-089: Subagent cannot set env var in parent shell ─────────

@test "T-0018-089: ATELIER_SETUP_MODE=1 cannot be set by a subagent (subagents run in own process context)" {
  # This is a structural/documentation test -- subagents are separate processes
  # and cannot modify the parent shell's environment.
  # Verify the bypass uses an environment variable (not a file flag or shared state)
  [ -f "$SOURCE_ENFORCE_PATHS" ]
  local bypass_line
  bypass_line=$(grep 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_PATHS")
  # Uses ${ } env var syntax -- not a file check, not a shared-memory check
  echo "$bypass_line" | grep -q '\${'
  # Does not reference any file path or temp directory
  echo "$bypass_line" | grep -qv '/tmp\|mktemp\|touch\|\.flag'
}

# ── T-0018-090: User can intentionally set ATELIER_SETUP_MODE=1 ────

@test "T-0018-090: A user setting ATELIER_SETUP_MODE=1 in their shell disables all three hooks (intentional user control)" {
  # This is by design: users have full control over their hooks
  # Verify each hook's bypass line would trigger on ATELIER_SETUP_MODE=1
  for hook in "$SOURCE_ENFORCE_PATHS" "$SOURCE_ENFORCE_SEQ" "$SOURCE_ENFORCE_GIT"; do
    [ -f "$hook" ]
    # Each hook must have the bypass that exits 0 when ATELIER_SETUP_MODE=1
    grep 'ATELIER_SETUP_MODE' "$hook" | grep -q 'exit 0' || {
      echo "Hook $hook does not exit 0 on ATELIER_SETUP_MODE=1"
      return 1
    }
  done
}

# ── T-0018-091: warn-dor-dod.sh does NOT have bypass line ──────────

@test "T-0018-091: warn-dor-dod.sh does NOT contain the bypass line (SubagentStop hooks do not block writes)" {
  [ -f "$SOURCE_WARN_DOD" ]
  if grep -q 'ATELIER_SETUP_MODE' "$SOURCE_WARN_DOD"; then
    echo "warn-dor-dod.sh should NOT contain ATELIER_SETUP_MODE bypass"
    return 1
  fi
}

# ── T-0018-092: pre-compact.sh does NOT have bypass line ───────────

@test "T-0018-092: pre-compact.sh does NOT contain the bypass line (PreCompact hook does not block writes)" {
  [ -f "$SOURCE_PRE_COMPACT" ]
  if grep -q 'ATELIER_SETUP_MODE' "$SOURCE_PRE_COMPACT"; then
    echo "pre-compact.sh should NOT contain ATELIER_SETUP_MODE bypass"
    return 1
  fi
}

# ── T-0018-093: enforce-pipeline-activation.sh does NOT have bypass ─

@test "T-0018-093: enforce-pipeline-activation.sh does NOT contain the bypass line (blocks Agent, not writes -- setup does not invoke subagents)" {
  [ -f "$SOURCE_ENFORCE_ACTIVATION" ]
  if grep -q 'ATELIER_SETUP_MODE' "$SOURCE_ENFORCE_ACTIVATION"; then
    echo "enforce-pipeline-activation.sh should NOT contain ATELIER_SETUP_MODE bypass"
    return 1
  fi
}

# ── T-0018-094: Existing enforcement logic unchanged ────────────────

@test "T-0018-094: All existing enforcement logic in each hook is unchanged after bypass line addition (no removals, no modifications)" {
  # Verify key logic landmarks in each hook still exist
  # enforce-eva-paths.sh: Eva main thread path enforcement (docs/pipeline/ only)
  [ -f "$SOURCE_ENFORCE_PATHS" ]
  grep -q 'docs/pipeline/' "$SOURCE_ENFORCE_PATHS"
  grep -q 'BLOCKED' "$SOURCE_ENFORCE_PATHS"
  grep -q 'jq' "$SOURCE_ENFORCE_PATHS"

  # enforce-sequencing.sh: Ellis gate, Agatha gate, telemetry gate
  [ -f "$SOURCE_ENFORCE_SEQ" ]
  grep -q 'Gate 1.*Ellis' "$SOURCE_ENFORCE_SEQ"
  grep -q 'Gate 2.*Agatha' "$SOURCE_ENFORCE_SEQ"
  grep -q 'Gate 3.*Ellis.*telemetry' "$SOURCE_ENFORCE_SEQ"

  # enforce-git.sh: git command block and test execution block
  [ -f "$SOURCE_ENFORCE_GIT" ]
  grep -q 'git.*(add|commit|push' "$SOURCE_ENFORCE_GIT"
  grep -q 'bats\|pytest\|jest' "$SOURCE_ENFORCE_GIT"
}

# ── T-0018-095: SKILL.md Steps 1-6e and 7 unchanged ────────────────

@test "T-0018-095: SKILL.md Steps 1-6e and Steps 7 are unchanged after setup-mode documentation addition" {
  [ -f "$SKILL_FILE" ]
  # Verify all major step headings still exist
  grep -q "### Step 1: Gather Project Information" "$SKILL_FILE"
  grep -q "### Step 2: Read Templates" "$SKILL_FILE"
  grep -q "### Step 3: Install Files" "$SKILL_FILE"
  grep -q "### Step 4: Customize Placeholders" "$SKILL_FILE"
  grep -q "### Step 5: Update CLAUDE.md" "$SKILL_FILE"
  grep -q "### Step 6: Print Summary and Offer Optional Features" "$SKILL_FILE"
  grep -q "### Step 6a: Sentinel Security Agent (Opt-In)" "$SKILL_FILE"
  grep -q "### Step 6b: Agent Teams Opt-In (Experimental)" "$SKILL_FILE"
  grep -q "### Step 6c: CI Watch Opt-In" "$SKILL_FILE"
  grep -q "### Step 6d: Deps Agent Opt-In" "$SKILL_FILE"
  grep -q "### Step 6e: Darwin Self-Evolving Pipeline (Opt-In)" "$SKILL_FILE"
  grep -q "### Step 7: Lightweight Reconfig" "$SKILL_FILE"
}
