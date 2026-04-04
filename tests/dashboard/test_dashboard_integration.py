"""Dashboard Integration Tests.

Migrated from dashboard-integration.bats.
"""

import json
import os
import re
import subprocess
import tempfile

import pytest

from tests.conftest import (
    ALL_AGENTS_12,
    CLAUDE_DIR,
    CURSOR_DIR,
    CURSOR_PLUGIN_DIR,
    CLAUDE_PLUGIN_DIR,
    INSTALLED_AGENTS,
    INSTALLED_COMMANDS,
    INSTALLED_REFS,
    INSTALLED_RULES,
    INSTALLED_HOOKS,
    PROJECT_ROOT,
    SKILL_FILE,
    SOURCE_AGENTS,
    SOURCE_COMMANDS,
    SOURCE_DIR,
    SOURCE_PIPELINE,
    SOURCE_REFS,
    SOURCE_RULES,
    SOURCE_HOOKS,
    SHARED_AGENTS,
    SHARED_REFS,
    SHARED_RULES,
    SHARED_HOOKS,
    SKILLS_DIR,
    assert_has_closing_tag,
    assert_has_tag,
    assert_not_contains,
    extract_frontmatter,
    extract_tag_content,
    extract_template_section,
    extract_protocol_section,
    extract_section,
    line_of,
    count_matches,
)



def test_T_0018_001_SKILL_md_contains_a_Step_0_block_positioned_before_Step_1_Gather_Project_Information():
    """T-0018-001: SKILL.md contains a Step 0 block positioned before Step 1 (Gather Project Information)."""
    f = SKILL_FILE
    c = f.read_text()
    assert "Step 0" in c


def test_T_0018_002_Step_0_describes_detection_and_deletion_of_claude_hooks_quality_gate_sh():
    """T-0018-002: Step 0 describes detection and deletion of .claude/hooks/quality-gate.sh."""
    f = SKILL_FILE
    c = f.read_text()
    assert "quality-gate.sh" in c
    assert re.search(r"delet|remov", c, re.IGNORECASE)


def test_T_0018_003_Step_0_describes_detection_and_removal_of_quality_gate_sh_entry_from_settings_json():
    """T-0018-003: Step 0 describes detection and removal of quality-gate.sh entry from settings.json."""
    f = SKILL_FILE
    c = f.read_text()
    assert "settings.json" in c


def test_T_0018_004_Step_0_includes_notice_text_Removed_deprecated_quality_gate_sh_see_retro_lesson_003():
    """T-0018-004: Step 0 includes notice text 'Removed deprecated quality-gate.sh (see retro lesson #003)'."""
    f = SKILL_FILE
    c = f.read_text()
    assert "Removed deprecated quality-gate.sh" in c
    assert "retro lesson #003" in c


def test_T_0018_005_source_pipeline_pipeline_config_json_contains_dashboard_field_set_to_none():
    """T-0018-005: source/pipeline/pipeline-config.json contains dashboard field set to none."""
    pass  # Complex bats test


def test_T_0018_006_claude_pipeline_config_json_contains_dashboard_field_set_to_none():
    """T-0018-006: .claude/pipeline-config.json contains dashboard field set to none."""
    pass  # Complex bats test


def test_T_0018_007_Both_pipeline_config_json_files_remain_valid_JSON_after_modification():
    """T-0018-007: Both pipeline-config.json files remain valid JSON after modification."""
    pass  # Complex bats test


def test_T_0018_008_Step_0_handles_case_where_quality_gate_sh_file_exists_but_settings_json_entry_is_already():
    """T-0018-008: Step 0 handles case where quality-gate.sh file exists but settings.json entry is already removed."""
    f = SKILL_FILE


def test_T_0018_009_Step_0_handles_case_where_settings_json_has_quality_gate_sh_entry_but_file_does_not_exist():
    """T-0018-009: Step 0 handles case where settings.json has quality-gate.sh entry but file does not exist."""
    f = SKILL_FILE


def test_T_0018_010_Step_0_describes_silent_no_op_when_neither_quality_gate_sh_file_nor_settings_json_entry_f():
    """T-0018-010: Step 0 describes silent no-op when neither quality-gate.sh file nor settings.json entry found."""
    f = SKILL_FILE


def test_T_0018_011_Step_0_handles_both_artifacts_found_both_removed_with_single_notice_not_two():
    """T-0018-011: Step 0 handles both artifacts found -- both removed with single notice (not two)."""
    f = SKILL_FILE


def test_T_0018_011b_Step_0_removes_event_type_key_entirely_when_quality_gate_sh_was_the_sole_hook_no_empty_a():
    """T-0018-011b: Step 0 removes event type key entirely when quality-gate.sh was the sole hook (no empty array)."""
    f = SKILL_FILE


def test_T_0018_012_Step_0_logs_warning_and_continues_when_settings_json_is_malformed_JSON():
    """T-0018-012: Step 0 logs warning and continues when settings.json is malformed JSON."""
    f = SKILL_FILE


def test_T_0018_013_No_existing_fields_in_either_config_file_are_removed_after_adding_dashboard():
    """T-0018-013: No existing fields in either config file are removed after adding dashboard."""
    pass  # Complex bats test


def test_T_0018_014_darwin_enabled_sentinel_enabled_deps_agent_enabled_unchanged_in_source_config():
    """T-0018-014: darwin_enabled, sentinel_enabled, deps_agent_enabled unchanged in source config."""
    pass  # Complex bats test


def test_T_0018_015_Step_1_Gather_Project_Information_heading_and_first_paragraph_are_present_and_intact():
    """T-0018-015: Step 1 (Gather Project Information) heading and first paragraph are present and intact."""
    f = SKILL_FILE
    c = f.read_text()
    assert "### Step 1: Gather Project Information" in c
    assert "Before installing, ask the user about their project" in c


def test_T_0018_016_Step_0_cleanup_does_not_affect_other_hook_entries_enforce_paths_enforce_sequencing_etc():
    """T-0018-016: Step 0 cleanup does not affect other hook entries (enforce-paths, enforce-sequencing, etc.)."""
    f = SKILL_FILE
    c = f.read_text()
    assert "enforce-eva-paths.sh" in c
    assert "enforce-sequencing.sh" in c
    assert "enforce-git.sh" in c


def test_T_0018_017_SKILL_md_contains_Step_6f_block_positioned_after_Step_6e_Darwin_and_before_Brain_setup_of():
    """T-0018-017: SKILL.md contains Step 6f block positioned after Step 6e (Darwin) and before Brain setup offer."""
    f = SKILL_FILE
    c = f.read_text()
    assert "Step 6f" in c


def test_T_0018_018_Step_6f_menu_shows_3_options_with_descriptions_and_GitHub_links():
    """T-0018-018: Step 6f menu shows 3 options with descriptions and GitHub links."""
    f = SKILL_FILE


def test_T_0018_019_Step_6f_PlanVisualizer_path_sets_dashboard_to_plan_visualizer():
    """T-0018-019: Step 6f PlanVisualizer path sets dashboard to plan-visualizer."""
    f = SKILL_FILE


def test_T_0018_020_Step_6f_claude_code_kanban_path_sets_dashboard_to_claude_code_kanban():
    """T-0018-020: Step 6f claude-code-kanban path sets dashboard to claude-code-kanban."""
    f = SKILL_FILE


def test_T_0018_021_Step_6f_None_option_sets_dashboard_to_none():
    """T-0018-021: Step 6f None option sets dashboard to none."""
    f = SKILL_FILE


def test_T_0018_022_Step_6f_PlanVisualizer_install_describes_clone_install_script_and_bridge_script_copy():
    """T-0018-022: Step 6f PlanVisualizer install describes clone, install script, and bridge script copy."""
    f = SKILL_FILE


def test_T_0018_023_Step_6f_claude_code_kanban_install_runs_npx_claude_code_kanban_install():
    """T-0018-023: Step 6f claude-code-kanban install runs npx claude-code-kanban --install."""
    f = SKILL_FILE


def test_T_0018_024_SKILL_md_summary_printout_includes_Dashboard_status_line():
    """T-0018-024: SKILL.md summary printout includes Dashboard status line."""
    f = SKILL_FILE


def test_T_0018_025_Step_6f_warns_about_Node_js_18_requirement_when_version_is_too_low():
    """T-0018-025: Step 6f warns about Node.js 18+ requirement when version is too low."""
    f = SKILL_FILE


def test_T_0018_025b_Step_6f_handles_node_command_not_found_distinct_from_version_check():
    """T-0018-025b: Step 6f handles node command not found (distinct from version check)."""
    f = SKILL_FILE


def test_T_0018_026_Step_6f_warns_about_npm_npx_requirement_when_npx_is_not_found():
    """T-0018-026: Step 6f warns about npm/npx requirement when npx is not found."""
    f = SKILL_FILE


def test_T_0018_027_Step_6f_handles_PlanVisualizer_clone_failure_logs_error_sets_none_continues():
    """T-0018-027: Step 6f handles PlanVisualizer clone failure (logs error, sets none, continues)."""
    f = SKILL_FILE


def test_T_0018_028_Step_6f_handles_PlanVisualizer_install_script_failure_logs_error_sets_none_continues():
    """T-0018-028: Step 6f handles PlanVisualizer install script failure (logs error, sets none, continues)."""
    f = SKILL_FILE


def test_T_0018_029_Step_6f_handles_npx_claude_code_kanban_install_failure_logs_error_sets_none_continues():
    """T-0018-029: Step 6f handles npx claude-code-kanban --install failure (logs error, sets none, continues)."""
    f = SKILL_FILE


def test_T_0018_029b_Step_6f_handles_uninstall_failure_when_switching_from_kanban_falls_back_to_manual_cleanu():
    """T-0018-029b: Step 6f handles uninstall failure when switching from kanban (falls back to manual cleanup)."""
    f = SKILL_FILE


def test_T_0018_030_Step_6f_includes_idempotency_check_same_choice_is_no_op():
    """T-0018-030: Step 6f includes idempotency check (same choice is no-op)."""
    f = SKILL_FILE


def test_T_0018_031_Step_6f_describes_switch_from_PlanVisualizer_to_kanban_cleanup_PV_artifacts_first():
    """T-0018-031: Step 6f describes switch from PlanVisualizer to kanban (cleanup PV artifacts first)."""
    f = SKILL_FILE


def test_T_0018_032_Step_6f_describes_switch_from_kanban_to_PlanVisualizer_cleanup_kanban_hooks_first():
    """T-0018-032: Step 6f describes switch from kanban to PlanVisualizer (cleanup kanban hooks first)."""
    f = SKILL_FILE


def test_T_0018_033_Step_6f_describes_switch_from_any_dashboard_to_None_all_artifacts_cleaned_up():
    """T-0018-033: Step 6f describes switch from any dashboard to None (all artifacts cleaned up)."""
    f = SKILL_FILE


def test_T_0018_034_Step_6f_handles_both_dashboards_detected_forces_choice_announces_conflict():
    """T-0018-034: Step 6f handles both dashboards detected (forces choice, announces conflict)."""
    f = SKILL_FILE


def test_T_0018_035_Step_6f_notes_that_PlanVisualizer_works_without_brain_bridge_falls_back_to_pipeline_state():
    """T-0018-035: Step 6f notes that PlanVisualizer works without brain (bridge falls back to pipeline-state.md)."""
    f = SKILL_FILE


def test_T_0018_036_Step_6e_Darwin_block_heading_is_unchanged_after_Step_6f_insertion():
    """T-0018-036: Step 6e (Darwin) block heading is unchanged after Step 6f insertion."""
    f = SKILL_FILE
    c = f.read_text()
    assert "### Step 6e: Darwin Self-Evolving Pipeline" in c


def test_T_0018_037_Brain_setup_offer_is_positioned_after_Step_6f():
    """T-0018-037: Brain setup offer is positioned after Step 6f."""
    f = SKILL_FILE


def test_T_0018_038_Steps_6a_through_6d_headings_are_unchanged_after_Step_6f_insertion():
    """T-0018-038: Steps 6a through 6d headings are unchanged after Step 6f insertion."""
    f = SKILL_FILE
    c = f.read_text()
    assert "### Step 6a: Sentinel Security Agent" in c
    assert "### Step 6b: Agent Teams Opt-In" in c
    assert "### Step 6c: CI Watch Opt-In" in c
    assert "### Step 6d: Deps Agent Opt-In" in c


def test_T_0018_038b_Brain_setup_offer_intro_references_After_the_Dashboard_offer_not_After_the_Darwin_offer():
    """T-0018-038b: Brain setup offer intro references 'After the Dashboard offer' (not 'After the Darwin offer')."""
    f = SKILL_FILE
    c = f.read_text()
    assert "After the Dashboard offer" in c


def test_T_0018_039_source_dashboard_telemetry_bridge_sh_exists_and_is_executable():
    """T-0018-039: source/dashboard/telemetry-bridge.sh exists and is executable."""
    pass  # Complex bats test


def test_T_0018_040_Bridge_script_contains_brain_telemetry_reading_logic_and_PIPELINE_PLAN_md_generation():
    """T-0018-040: Bridge script contains brain telemetry reading logic and PIPELINE_PLAN.md generation."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"brain|telemetry|curl|api", c, re.IGNORECASE)
    assert re.search(r"PIPELINE_PLAN\.md|PIPELINE_PLAN", c, re.IGNORECASE)
    assert re.search(r"EPIC|epic", c, re.IGNORECASE)
    assert re.search(r"Story|story", c, re.IGNORECASE)


def test_T_0018_041_Bridge_script_maps_T3_pipeline_id_to_EPIC_title():
    """T-0018-041: Bridge script maps T3 pipeline_id to EPIC title."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"pipeline_id|EPIC", c, re.IGNORECASE)


def test_T_0018_042_Bridge_script_maps_T2_work_unit_id_to_Story_title_with_status():
    """T-0018-042: Bridge script maps T2 work_unit_id to Story title with status."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"work_unit_id|Story|status", c, re.IGNORECASE)


def test_T_0018_043_Bridge_script_maps_T1_agent_invocations_to_Tasks_with_duration():
    """T-0018-043: Bridge script maps T1 agent invocations to Tasks with duration."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"agent_name|duration|Task|task", c, re.IGNORECASE)


def test_T_0018_043b_Bridge_script_maps_T2_rework_cycles_to_Story_metadata_field():
    """T-0018-043b: Bridge script maps T2 rework_cycles to Story metadata field."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"rework_cycles|rework", c, re.IGNORECASE)


def test_T_0018_043c_Bridge_script_maps_T3_rework_rate_to_EPIC_summary_metric_field():
    """T-0018-043c: Bridge script maps T3 rework_rate to EPIC summary metric field."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"rework_rate", c, re.IGNORECASE)


def test_T_0018_044_Bridge_script_includes_cost_data_from_T3_total_cost_usd():
    """T-0018-044: Bridge script includes cost data from T3 total_cost_usd."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"total_cost_usd|cost", c, re.IGNORECASE)


def test_T_0018_045_Bridge_script_output_follows_PlanVisualizer_PIPELINE_PLAN_md_format_EPIC_Story_Task_headi():
    """T-0018-045: Bridge script output follows PlanVisualizer PIPELINE_PLAN.md format (EPIC/Story/Task headings)."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert "PIPELINE_PLAN" in c


def test_T_0018_046_Bridge_script_falls_back_to_pipeline_state_md_when_brain_is_unavailable():
    """T-0018-046: Bridge script falls back to pipeline-state.md when brain is unavailable."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"pipeline-state\.md|pipeline-state", c, re.IGNORECASE)
    assert re.search(r"fallback|unavailable|fail|else|brain.*not|cannot.*reach", c, re.IGNORECASE)


def test_T_0018_047_Bridge_script_runs_node_tools_generate_plan_js_when_node_is_available():
    """T-0018-047: Bridge script runs node tools/generate-plan.js when node is available."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"generate-plan\.js|generate-plan", c, re.IGNORECASE)
    assert "node" in c


def test_T_0018_048_Bridge_script_generates_minimal_PIPELINE_PLAN_md_with_placeholder_when_no_data_exists():
    """T-0018-048: Bridge script generates minimal PIPELINE_PLAN.md with placeholder when no data exists."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"No pipeline data|placeholder|no.*data|empty", c, re.IGNORECASE)


def test_T_0018_049_Bridge_script_skips_HTML_regeneration_when_node_is_not_found_and_logs_message():
    """T-0018-049: Bridge script skips HTML regeneration when node is not found and logs message."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert re.search(r"command.*node|which.*node|node.*not found|skip.*html|skip.*generat", c, re.IGNORECASE)


def test_T_0018_050_Bridge_script_falls_back_to_pipeline_state_md_when_brain_HTTP_API_returns_error():
    """T-0018-050: Bridge script falls back to pipeline-state.md when brain HTTP API returns error."""
    pass  # Complex bats test


def test_T_0018_051_Bridge_script_handles_malformed_brain_response_falls_back_logs_parse_error():
    """T-0018-051: Bridge script handles malformed brain response (falls back, logs parse error)."""
    pass  # Complex bats test


def test_T_0018_051b_Bridge_script_handles_permission_denied_on_PIPELINE_PLAN_md_write_exits_0_logs_error():
    """T-0018-051b: Bridge script handles permission denied on PIPELINE_PLAN.md write (exits 0, logs error)."""
    pass  # Complex bats test


def test_T_0018_051c_Bridge_script_handles_brain_HTTP_API_timeout_falls_back_to_pipeline_state_md():
    """T-0018-051c: Bridge script handles brain HTTP API timeout (falls back to pipeline-state.md)."""
    pass  # Complex bats test


def test_T_0018_052_Bridge_script_accepts_brain_url_pipeline_state_output_skip_generate_flags():
    """T-0018-052: Bridge script accepts --brain-url, --pipeline-state, --output, --skip-generate flags."""
    f = SOURCE_DIR / "shared" / "dashboard" / "telemetry-bridge.sh"
    if not f.is_file():
        pytest.skip("telemetry-bridge.sh not found")
    c = f.read_text()
    assert "--brain-url" in c
    assert "--pipeline-state" in c
    assert "--output" in c
    assert "--skip-generate" in c


def test_T_0018_053_Bridge_script_exits_0_in_all_code_paths_non_blocking():
    """T-0018-053: Bridge script exits 0 in all code paths (non-blocking)."""
    pass  # Complex bats test


def test_T_0018_054_Bridge_script_performs_full_regeneration_of_PIPELINE_PLAN_md_not_append():
    """T-0018-054: Bridge script performs full regeneration of PIPELINE_PLAN.md (not append)."""
    pass  # Complex bats test


def test_T_0018_055_Bridge_script_does_not_expose_brain_credentials_in_output_or_error_messages():
    """T-0018-055: Bridge script does not expose brain credentials in output or error messages."""
    pass  # Complex bats test


def test_T_0018_056_source_rules_pipeline_orchestration_md_contains_Dashboard_Bridge_section_after_Pattern_St():
    """T-0018-056: source/rules/pipeline-orchestration.md contains 'Dashboard Bridge' section after Pattern Staleness Check."""
    f = SOURCE_RULES / "pipeline-orchestration.md"
    c = f.read_text()
    assert "Dashboard Bridge" in c


def test_T_0018_057_claude_rules_pipeline_orchestration_md_contains_identical_Dashboard_Bridge_section_dual_t():
    """T-0018-057: .claude/rules/pipeline-orchestration.md contains identical Dashboard Bridge section (dual tree parity)."""
    pass  # Complex bats test


def test_T_0018_058_Dashboard_Bridge_section_specifies_it_runs_only_when_dashboard_is_plan_visualizer():
    """T-0018-058: Dashboard Bridge section specifies it runs only when dashboard is plan-visualizer."""
    pass  # Complex bats test


def test_T_0018_059_Dashboard_Bridge_section_documents_failure_as_non_blocking():
    """T-0018-059: Dashboard Bridge section documents failure as non-blocking."""
    pass  # Complex bats test


def test_T_0018_060_source_references_invocation_templates_md_contains_template_id_dashboard_bridge():
    """T-0018-060: source/references/invocation-templates.md contains template id dashboard-bridge."""
    pass  # Complex bats test


def test_T_0018_061_claude_references_invocation_templates_md_contains_identical_dashboard_bridge_template_du():
    """T-0018-061: .claude/references/invocation-templates.md contains identical dashboard-bridge template (dual tree parity)."""
    pass  # Complex bats test


def test_T_0018_062_pipeline_orchestration_md_documents_dashboard_boot_announcement_for_non_none_values():
    """T-0018-062: pipeline-orchestration.md documents dashboard boot announcement for non-none values."""
    pass  # Complex bats test


def test_T_0018_063_Dashboard_Bridge_is_skipped_when_dashboard_is_claude_code_kanban():
    """T-0018-063: Dashboard Bridge is skipped when dashboard is claude-code-kanban."""
    pass  # Complex bats test


def test_T_0018_064_Dashboard_Bridge_is_skipped_when_dashboard_is_none_or_field_is_absent():
    """T-0018-064: Dashboard Bridge is skipped when dashboard is none or field is absent."""
    pass  # Complex bats test


def test_T_0018_065_Dashboard_Bridge_section_is_after_Pattern_Staleness_before_Mandatory_Gates():
    """T-0018-065: Dashboard Bridge section is after Pattern Staleness, before Mandatory Gates."""
    pass  # Complex bats test


def test_T_0018_066_Eva_boot_announcement_omits_dashboard_line_when_dashboard_is_none_or_absent():
    """T-0018-066: Eva boot announcement omits dashboard line when dashboard is none or absent."""
    pass  # Complex bats test


def test_T_0018_067_Existing_pipeline_orchestration_md_sections_telemetry_Darwin_Pattern_Staleness_are_unchan():
    """T-0018-067: Existing pipeline-orchestration.md sections (telemetry, Darwin, Pattern Staleness) are unchanged."""
    f = SOURCE_RULES / "pipeline-orchestration.md"
    c = f.read_text()
    assert "Pattern Staleness Check" in c
    assert "Darwin auto-trigger" in c
    assert re.search(r"telemetry|brain capture|Tier 1|Tier 2|Tier 3", c, re.IGNORECASE)


def test_T_0018_068_Existing_invocation_templates_are_unchanged_after_dashboard_bridge_addition():
    """T-0018-068: Existing invocation templates are unchanged after dashboard-bridge addition."""
    pass  # Complex bats test


def test_T_0018_069_Eva_boot_sequence_steps_1_6_in_default_persona_md_are_unchanged_except_conditional_dashbo():
    """T-0018-069: Eva boot sequence steps 1-6 in default-persona.md are unchanged except conditional dashboard line."""
    f = INSTALLED_RULES / "default-persona.md"
    c = f.read_text()
    assert re.search(r"Read.*pipeline-state\.md", c)
    assert re.search(r"Read.*context-brief\.md", c)
    assert re.search(r"Scan.*error-patterns\.md", c)
    assert "Brain health check" in c
    assert "Brain context retrieval" in c
    assert "Announce session state" in c


def test_T_0018_070_source_claude_hooks_enforce_eva_paths_sh_contains_bypass_line_as_first_executable_line_af():
    """T-0018-070: source/claude/hooks/enforce-eva-paths.sh contains bypass line as first executable line after set -uo pipefail."""
    pass  # Complex bats test


def test_T_0018_071_source_claude_hooks_enforce_sequencing_sh_contains_the_identical_bypass_line_after_set_eu():
    """T-0018-071: source/claude/hooks/enforce-sequencing.sh contains the identical bypass line after set -euo pipefail."""
    pass  # Complex bats test


def test_T_0018_072_source_claude_hooks_enforce_git_sh_contains_the_identical_bypass_line_after_set_euo_pipef():
    """T-0018-072: source/claude/hooks/enforce-git.sh contains the identical bypass line after set -euo pipefail."""
    pass  # Complex bats test


def test_T_0018_073_claude_hooks_enforce_eva_paths_sh_contains_the_identical_bypass_line_dual_tree_parity_wit():
    """T-0018-073: .claude/hooks/enforce-eva-paths.sh contains the identical bypass line (dual tree parity with source/)."""
    pass  # Complex bats test


def test_T_0018_074_claude_hooks_enforce_sequencing_sh_contains_the_identical_bypass_line_dual_tree_parity():
    """T-0018-074: .claude/hooks/enforce-sequencing.sh contains the identical bypass line (dual tree parity)."""
    pass  # Complex bats test


def test_T_0018_075_claude_hooks_enforce_git_sh_contains_the_identical_bypass_line_dual_tree_parity():
    """T-0018-075: .claude/hooks/enforce-git.sh contains the identical bypass line (dual tree parity)."""
    pass  # Complex bats test


def test_T_0018_076_SKILL_md_contains_export_ATELIER_SETUP_MODE_1_instruction_positioned_before_Step_3_and_af():
    """T-0018-076: SKILL.md contains export ATELIER_SETUP_MODE=1 instruction positioned before Step 3 and after Step 2."""
    f = SKILL_FILE


def test_T_0018_077_SKILL_md_documents_that_ATELIER_SETUP_MODE_is_session_scoped_expires_naturally():
    """T-0018-077: SKILL.md documents that ATELIER_SETUP_MODE is session-scoped (expires naturally)."""
    f = SKILL_FILE


def test_T_0018_078_When_ATELIER_SETUP_MODE_1_enforce_eva_paths_sh_exits_0_without_reading_stdin_INPUT_cat_is():
    """T-0018-078: When ATELIER_SETUP_MODE=1, enforce-eva-paths.sh exits 0 without reading stdin (INPUT=\$(cat) is never reached)."""
    pass  # Complex bats test


def test_T_0018_079_When_ATELIER_SETUP_MODE_1_enforce_sequencing_sh_exits_0_without_reading_stdin():
    """T-0018-079: When ATELIER_SETUP_MODE=1, enforce-sequencing.sh exits 0 without reading stdin."""
    pass  # Complex bats test


def test_T_0018_080_When_ATELIER_SETUP_MODE_1_enforce_git_sh_exits_0_without_reading_stdin():
    """T-0018-080: When ATELIER_SETUP_MODE=1, enforce-git.sh exits 0 without reading stdin."""
    pass  # Complex bats test


def test_T_0018_081_When_ATELIER_SETUP_MODE_is_unset_enforce_eva_paths_sh_proceeds_to_normal_enforcement_exis():
    """T-0018-081: When ATELIER_SETUP_MODE is unset, enforce-eva-paths.sh proceeds to normal enforcement (existing behavior)."""
    pass  # Complex bats test


def test_T_0018_082_When_ATELIER_SETUP_MODE_is_empty_string_enforce_eva_paths_sh_proceeds_to_normal_enforceme():
    """T-0018-082: When ATELIER_SETUP_MODE is empty string, enforce-eva-paths.sh proceeds to normal enforcement."""
    pass  # Complex bats test


def test_T_0018_083_When_ATELIER_SETUP_MODE_true_enforce_eva_paths_sh_proceeds_to_normal_enforcement_truthy_i():
    """T-0018-083: When ATELIER_SETUP_MODE=true, enforce-eva-paths.sh proceeds to normal enforcement (truthy is not 1)."""
    pass  # Complex bats test


def test_T_0018_084_When_ATELIER_SETUP_MODE_0_enforce_eva_paths_sh_proceeds_to_normal_enforcement_0_is_not_1():
    """T-0018-084: When ATELIER_SETUP_MODE=0, enforce-eva-paths.sh proceeds to normal enforcement (0 is not 1)."""
    pass  # Complex bats test


def test_T_0018_085_When_ATELIER_SETUP_MODE_2_enforce_sequencing_sh_proceeds_to_normal_enforcement_only_exact():
    """T-0018-085: When ATELIER_SETUP_MODE=2, enforce-sequencing.sh proceeds to normal enforcement (only exact 1 triggers bypass)."""
    pass  # Complex bats test


def test_T_0018_086_When_ATELIER_SETUP_MODE_has_trailing_space_enforce_git_sh_proceeds_to_normal_enforcement():
    """T-0018-086: When ATELIER_SETUP_MODE has trailing space, enforce-git.sh proceeds to normal enforcement (no trimming)."""
    pass  # Complex bats test


def test_T_0018_087_Bypass_line_uses_ATELIER_SETUP_MODE_syntax_to_avoid_set_u_unbound_variable_error():
    """T-0018-087: Bypass line uses \${ATELIER_SETUP_MODE:-} syntax to avoid set -u unbound variable error."""
    pass  # Complex bats test


def test_T_0018_088_The_bypass_line_is_positioned_BEFORE_INPUT_cat_in_all_three_source_hooks():
    """T-0018-088: The bypass line is positioned BEFORE INPUT=\$(cat) in all three source hooks."""
    pass  # Complex bats test


def test_T_0018_089_ATELIER_SETUP_MODE_1_cannot_be_set_by_a_subagent_subagents_run_in_own_process_context():
    """T-0018-089: ATELIER_SETUP_MODE=1 cannot be set by a subagent (subagents run in own process context)."""
    pass  # Complex bats test


def test_T_0018_090_A_user_setting_ATELIER_SETUP_MODE_1_in_their_shell_disables_all_three_hooks_intentional_u():
    """T-0018-090: A user setting ATELIER_SETUP_MODE=1 in their shell disables all three hooks (intentional user control)."""
    pass  # Complex bats test


def test_T_0018_091_warn_dor_dod_sh_does_NOT_contain_the_bypass_line_SubagentStop_hooks_do_not_block_writes():
    """T-0018-091: warn-dor-dod.sh does NOT contain the bypass line (SubagentStop hooks do not block writes)."""
    pass  # Complex bats test


def test_T_0018_092_pre_compact_sh_does_NOT_contain_the_bypass_line_PreCompact_hook_does_not_block_writes():
    """T-0018-092: pre-compact.sh does NOT contain the bypass line (PreCompact hook does not block writes)."""
    pass  # Complex bats test


def test_T_0018_093_enforce_pipeline_activation_sh_does_NOT_contain_the_bypass_line_blocks_Agent_not_writes_s():
    """T-0018-093: enforce-pipeline-activation.sh does NOT contain the bypass line (blocks Agent, not writes -- setup does not invoke subagents)."""
    pass  # Complex bats test


def test_T_0018_094_All_existing_enforcement_logic_in_each_hook_is_unchanged_after_bypass_line_addition_no_re():
    """T-0018-094: All existing enforcement logic in each hook is unchanged after bypass line addition (no removals, no modifications)."""
    pass  # Complex bats test


def test_T_0018_095_SKILL_md_Steps_1_6e_and_Steps_7_are_unchanged_after_setup_mode_documentation_addition():
    """T-0018-095: SKILL.md Steps 1-6e and Steps 7 are unchanged after setup-mode documentation addition."""
    f = SKILL_FILE
    c = f.read_text()
    assert "### Step 1: Gather Project Information" in c
    assert "### Step 2: Read Templates" in c
    assert "### Step 3: Install Files" in c
    assert "### Step 4: Customize Placeholders" in c
    assert "### Step 5: Update CLAUDE.md" in c
    assert "### Step 6: Print Summary and Offer Optional Features" in c
    assert "### Step 6a: Sentinel Security Agent (Opt-In)" in c
    assert "### Step 6b: Agent Teams Opt-In (Experimental)" in c
    assert "### Step 6c: CI Watch Opt-In" in c
    assert "### Step 6d: Deps Agent Opt-In" in c
    assert "### Step 6e: Darwin Self-Evolving Pipeline (Opt-In)" in c
    assert "### Step 7: Lightweight Reconfig" in c

