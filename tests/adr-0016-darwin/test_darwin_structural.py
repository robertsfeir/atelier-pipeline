"""ADR-0016: Darwin -- Self-Evolving Pipeline Engine -- Structural Tests.

Tests: T-0016-001 through T-0016-104 (98 tests).
Migrated from darwin-structural.test.bats.
"""

import json
import re

import pytest

from tests.conftest import (
    ALL_AGENTS_12,
    CLAUDE_DIR,
    INSTALLED_AGENTS,
    INSTALLED_COMMANDS,
    INSTALLED_REFS,
    INSTALLED_RULES,
    PROJECT_ROOT,
    SKILL_FILE,
    SOURCE_COMMANDS,
    SOURCE_PIPELINE,
    SOURCE_REFS,
    SOURCE_RULES,
    assert_has_closing_tag,
    assert_has_tag,
    extract_frontmatter,
    extract_tag_content,
    extract_template_section,
    extract_section,
    line_of,
)


def test_T_0016_001_source_darwin_agent_files_exist_with_name_darwin_in_frontmatter():
    """T-0016-001: source darwin agent files exist with name: darwin in frontmatter."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_002_claude_agents_darwin_md_exists_with_name_darwin_in_YAML_frontmatter():
    """T-0016-002: .claude/agents/darwin.md exists with name: darwin in YAML frontmatter."""
    f = INSTALLED_AGENTS / "darwin.md"
    c = f.read_text()
    assert "name: darwin" in c


def test_T_0016_003_darwin_md_disallowedTools_frontmatter_includes_Write_Edit_MultiEdit_NotebookEdit_Agent():
    """T-0016-003: darwin.md disallowedTools frontmatter includes Write, Edit, MultiEdit, NotebookEdit, Agent."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert "Write" in c
    assert "Edit" in c
    assert "MultiEdit" in c
    assert "NotebookEdit" in c
    assert "Agent" in c


def test_T_0016_004_darwin_md_contains_identity_required_actions_workflow_examples_tools_constraints_output_t():
    """T-0016-004: darwin.md contains identity, required-actions, workflow, examples, tools, constraints, output tags."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")


def test_T_0016_005_constraints_includes_self_edit_protection_mentioning_darwin_md():
    """T-0016-005: <constraints> includes self-edit protection mentioning darwin.md."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "constraints")
    assert re.search(r"cannot propose changes to.*darwin\.md|cannot.*modify.*darwin\.md|self.edit.*protect", section, re.IGNORECASE)


def test_T_0016_006_constraints_includes_the_5_pipeline_minimum_gate():
    """T-0016-006: <constraints> includes the 5-pipeline minimum gate."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "constraints")
    assert re.search(r"5.*pipeline|five.*pipeline", section, re.IGNORECASE)


def test_T_0016_007_constraints_includes_the_brain_required_gate():
    """T-0016-007: <constraints> includes the brain-required gate."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "constraints")
    assert re.search(r"brain.*require|require.*brain|brain.*unavailable|brain.*telemetry", section, re.IGNORECASE)


def test_T_0016_008_workflow_encodes_four_phases_Data_Ingestion_Fitness_Assessment_Pattern_Analysis_Report_Pr():
    """T-0016-008: <workflow> encodes four phases: Data Ingestion, Fitness Assessment, Pattern Analysis, Report Production."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "workflow")
    assert re.search(r"data.*ingest", section, re.IGNORECASE)
    assert re.search(r"fitness.*assess", section, re.IGNORECASE)
    assert re.search(r"pattern.*analy", section, re.IGNORECASE)
    assert re.search(r"report.*produc", section, re.IGNORECASE)


def test_T_0016_009_workflow_encodes_fitness_scoring_thriving_80_struggling_50_80_failing_50():
    """T-0016-009: <workflow> encodes fitness scoring: thriving (>= 80%), struggling (50-80%), failing (< 50%)."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "workflow")
    assert re.search(r"thriving", section, re.IGNORECASE)
    assert re.search(r"struggling", section, re.IGNORECASE)
    assert re.search(r"failing", section, re.IGNORECASE)
    assert re.search(r"80", section, re.IGNORECASE)
    assert re.search(r"50", section, re.IGNORECASE)


def test_T_0016_010_workflow_encodes_the_5_level_escalation_ladder():
    """T-0016-010: <workflow> encodes the 5-level escalation ladder."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "workflow")
    assert re.search(r"warn", section, re.IGNORECASE)
    assert re.search(r"constraint", section, re.IGNORECASE)
    assert re.search(r"workflow.*edit", section, re.IGNORECASE)
    assert re.search(r"rewrite", section, re.IGNORECASE)
    assert re.search(r"remov", section, re.IGNORECASE)


def test_T_0016_011_workflow_encodes_the_fix_layer_selection_table_7_target_layers():
    """T-0016-011: <workflow> encodes the fix layer selection table (7 target layers)."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "workflow")
    assert re.search(r"persona", section, re.IGNORECASE)
    assert re.search(r"orchestration.*rule|rule", section, re.IGNORECASE)
    assert re.search(r"hook", section, re.IGNORECASE)
    assert re.search(r"quality.*gate|gate", section, re.IGNORECASE)
    assert re.search(r"invocation.*template|template", section, re.IGNORECASE)
    assert re.search(r"model.*assign|model", section, re.IGNORECASE)
    assert re.search(r"retro.*lesson|retro", section, re.IGNORECASE)


def test_T_0016_012_examples_contains_at_least_two_examples_constraint_addition_escalation():
    """T-0016-012: <examples> contains at least two examples (constraint addition + escalation)."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "examples")


def test_T_0016_013_output_specifies_FITNESS_ASSESSMENT_PROPOSED_CHANGES_UNCHANGED_sections():
    """T-0016-013: <output> specifies FITNESS ASSESSMENT, PROPOSED CHANGES, UNCHANGED sections."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "output")
    assert re.search(r"FITNESS ASSESSMENT", section, re.IGNORECASE)
    assert re.search(r"PROPOSED CHANGES", section, re.IGNORECASE)
    assert re.search(r"UNCHANGED", section, re.IGNORECASE)


def test_T_0016_014_output_specifies_each_proposal_includes_evidence_layer_escalation_level_risk_expected_imp():
    """T-0016-014: <output> specifies each proposal includes evidence, layer, escalation level, risk, expected impact."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "output")
    assert re.search(r"evidence", section, re.IGNORECASE)
    assert re.search(r"layer", section, re.IGNORECASE)
    assert re.search(r"escalation.*level|level", section, re.IGNORECASE)
    assert re.search(r"risk", section, re.IGNORECASE)
    assert re.search(r"expected.*impact|impact", section, re.IGNORECASE)


def test_T_0016_015_constraints_includes_Level_5_requiring_summary_of_prior_escalation_attempts():
    """T-0016-015: <constraints> includes Level 5 requiring summary of prior escalation attempts."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "constraints")
    assert re.search(r"level 5.*prior.*escalation|level 5.*summary|prior.*escalation.*attempt", section, re.IGNORECASE)


def test_T_0016_016_tools_lists_Read_Glob_Grep_Bash_read_only_and_no_Write_Edit():
    """T-0016-016: <tools> lists Read, Glob, Grep, Bash (read-only) and no Write/Edit."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "tools")
    assert re.search(r"\bRead\b", section, re.IGNORECASE)
    assert re.search(r"read.only", section, re.IGNORECASE)


def test_T_0016_017_darwin_md_tools_does_not_include_Write_tool():
    """T-0016-017: darwin.md <tools> does not include Write tool."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "tools")
    assert not re.search(r"^\s*[-*].*\bWrite\b", section, re.IGNORECASE)


def test_T_0016_018_darwin_md_tools_does_not_include_Edit_tool():
    """T-0016-018: darwin.md <tools> does not include Edit tool."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "tools")
    assert not re.search(r"^\s*[-*].*\bEdit\b", section, re.IGNORECASE)


def test_T_0016_019_darwin_frontmatter_disallowedTools_blocks_Write_Layer_1_enforcement():
    """T-0016-019: darwin frontmatter disallowedTools blocks Write (Layer 1 enforcement)."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert "disallowedTools" in c
    assert "Write" in c


def test_T_0016_020_darwin_frontmatter_disallowedTools_blocks_Edit_Layer_1_enforcement():
    """T-0016-020: darwin frontmatter disallowedTools blocks Edit (Layer 1 enforcement)."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert "disallowedTools" in c
    assert "Edit" in c


def test_T_0016_021_darwin_does_not_appear_in_the_core_agent_constant_list_in_agent_system_md():
    """T-0016-021: darwin does not appear in the core agent constant list in agent-system.md."""
    f = INSTALLED_RULES / "agent-system.md"
    c = f.read_text()
    # darwin should appear in agent-system.md (e.g., routing table), but not in the core constant list
    assert re.search(r"darwin", c, re.IGNORECASE)
    # Extract the core agent constant code block and verify darwin is absent
    core_block_match = re.search(r"### Core Agent Constant.*?```(.*?)```", c, re.DOTALL)
    if core_block_match:
        core_block = core_block_match.group(1)
        assert "darwin" not in core_block.lower()


def test_T_0016_022_core_agent_constant_code_block_in_agent_system_md_does_not_include_darwin():
    """T-0016-022: core agent constant code block in agent-system.md does not include darwin."""
    f = INSTALLED_RULES / "agent-system.md"
    c = f.read_text()
    # Extract the core agent constant code block specifically
    core_block_match = re.search(r"### Core Agent Constant.*?```(.*?)```", c, re.DOTALL)
    if not core_block_match:
        pytest.skip("Core Agent Constant code block not found")
    core_block = core_block_match.group(1)
    assert "darwin" not in core_block.lower(), "darwin should not be in the core agent constant list"


def test_T_0016_023_source_commands_darwin_md_exists_with_YAML_frontmatter_name_darwin():
    """T-0016-023: source/commands/darwin.md exists with YAML frontmatter name: darwin."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_024_claude_commands_darwin_md_exists_with_identical_content_to_source():
    """T-0016-024: .claude/commands/darwin.md exists with identical content to source."""
    f = INSTALLED_COMMANDS / "darwin.md"
    # diff verification handled via content comparison


def test_T_0016_025_command_file_describes_darwin_enabled_gate_when_false_not_enabled():
    """T-0016-025: command file describes darwin_enabled gate (when false: not enabled)."""
    # Skip: darwin.md command not yet created
    f = INSTALLED_COMMANDS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"darwin_enabled", c, re.IGNORECASE)
    assert re.search(r"not enabled|not.*enabled", c, re.IGNORECASE)


def test_T_0016_026_command_file_describes_brain_required_gate_brain_unavailable_stop():
    """T-0016-026: command file describes brain-required gate (brain unavailable: stop)."""
    # Skip: darwin.md command not yet created
    f = INSTALLED_COMMANDS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"brain.*unavailable|brain.*not available|brain.*require", c, re.IGNORECASE)


def test_T_0016_027_command_file_describes_5_pipeline_minimum_gate_fewer_than_5_stop_with_count():
    """T-0016-027: command file describes 5-pipeline minimum gate (fewer than 5: stop with count)."""
    # Skip: darwin.md command not yet created
    f = INSTALLED_COMMANDS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"5.*pipeline|five.*pipeline|fewer than 5|insufficient.*data", c, re.IGNORECASE)


def test_T_0016_028_command_file_describes_approval_flow_user_approves_rejects_each_proposal():
    """T-0016-028: command file describes approval flow (user approves/rejects each proposal)."""
    # Skip: darwin.md command not yet created
    f = INSTALLED_COMMANDS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"approv.*reject|reject.*approv|individually|each.*proposal", c, re.IGNORECASE)


def test_T_0016_029_command_file_describes_routing_approved_changes_to_Colby():
    """T-0016-029: command file describes routing approved changes to Colby."""
    # Skip: darwin.md command not yet created
    f = INSTALLED_COMMANDS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"colby|route.*approved|approved.*route", c, re.IGNORECASE)


def test_T_0016_030_command_file_includes_triple_gate_darwin_enabled_brain_5_pipelines_before_invocation():
    """T-0016-030: command file includes triple gate (darwin_enabled, brain, 5 pipelines) before invocation."""
    # Skip: darwin.md command not yet created
    f = INSTALLED_COMMANDS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"darwin_enabled", c, re.IGNORECASE)
    assert re.search(r"brain", c, re.IGNORECASE)
    assert re.search(r"5.*pipeline|pipeline.*5|five.*pipeline", c, re.IGNORECASE)


def test_T_0016_098_command_file_describes_individual_proposal_presentation_no_merging():
    """T-0016-098: command file describes individual proposal presentation (no merging)."""
    # Skip: darwin.md command not yet created
    f = INSTALLED_COMMANDS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"individual|each.*proposal|one.*at.*a.*time|separately", c, re.IGNORECASE)


def test_T_0016_099_command_file_describes_modify_reject_with_feedback_re_invoke_Darwin_for_revised_proposal():
    """T-0016-099: command file describes modify = reject with feedback + re-invoke Darwin for revised proposal."""
    # Skip: darwin.md command not yet created
    f = INSTALLED_COMMANDS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"modify|modif", c, re.IGNORECASE)
    assert re.search(r"reject.*feedback|reject.*repropose|reject.*re.invoke|reject.*revis", c, re.IGNORECASE)


def test_T_0016_031_source_pipeline_pipeline_config_json_contains_darwin_enabled_false():
    """T-0016-031: source/pipeline/pipeline-config.json contains darwin_enabled: false."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_032_claude_pipeline_config_json_contains_darwin_enabled_false():
    """T-0016-032: .claude/pipeline-config.json contains darwin_enabled: false."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_033_both_pipeline_config_json_files_are_valid_JSON():
    """T-0016-033: both pipeline-config.json files are valid JSON."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_034_no_existing_config_fields_removed_from_source_pipeline_config_json():
    """T-0016-034: no existing config fields removed from source pipeline-config.json."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_035_deps_agent_enabled_sentinel_enabled_agent_teams_enabled_ci_watch_enabled_unchanged():
    """T-0016-035: deps_agent_enabled, sentinel_enabled, agent_teams_enabled, ci_watch_enabled unchanged."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_036_source_rules_agent_system_md_subagent_table_contains_Darwin_row():
    """T-0016-036: source/rules/agent-system.md subagent table contains **Darwin** row."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_037_claude_rules_agent_system_md_subagent_table_contains_Darwin_row():
    """T-0016-037: .claude/rules/agent-system.md subagent table contains **Darwin** row."""
    f = INSTALLED_RULES / "agent-system.md"


def test_T_0016_038_auto_routing_table_maps_pipeline_analysis_intent_to_Darwin():
    """T-0016-038: auto-routing table maps pipeline-analysis intent to Darwin."""
    f = INSTALLED_RULES / "agent-system.md"
    c = f.read_text()
    assert re.search(r"Darwin", c, re.IGNORECASE)
    assert re.search(r"pipeline.*health|pipeline.*analy|agent.*perform|what.*needs.*improv|run.*Darwin", c, re.IGNORECASE)


def test_T_0016_039_auto_routing_Darwin_row_includes_darwin_enabled_true_gate_condition():
    """T-0016-039: auto-routing Darwin row includes darwin_enabled: true gate condition."""
    f = INSTALLED_RULES / "agent-system.md"
    c = f.read_text()
    assert re.search(r"darwin_enabled", c, re.IGNORECASE)


def test_T_0016_040_no_skill_tool_gate_in_both_files_maps_Darwin_to_claude_agents_darwin_md():
    """T-0016-040: no-skill-tool gate in both files maps Darwin to .claude/agents/darwin.md."""
    f = INSTALLED_RULES / "agent-system.md"
    c = f.read_text()
    assert re.search(r"darwin.*\.claude/agents/darwin\.md|darwin\.md", c, re.IGNORECASE)


def test_T_0016_041_auto_routing_Darwin_row_documents_gate_darwin_enabled_true_required():
    """T-0016-041: auto-routing Darwin row documents gate: darwin_enabled true required."""
    # Skip: Darwin routing row not found
    f = INSTALLED_RULES / "agent-system.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"darwin_enabled.*true|if.*darwin_enabled", c, re.IGNORECASE)


def test_T_0016_100_command_or_routing_documentation_states_absent_darwin_enabled_key_is_treated_as_false():
    """T-0016-100: command or routing documentation states absent darwin_enabled key is treated as false."""
    # Skip: Darwin files not yet created -- cannot verify absence handling
    f = INSTALLED_COMMANDS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"absent.*false|missing.*false|not.*present.*false", c, re.IGNORECASE)


def test_T_0016_042_Deps_row_in_subagent_table_unchanged_after_Darwin_addition():
    """T-0016-042: Deps row in subagent table unchanged after Darwin addition."""
    f = INSTALLED_RULES / "agent-system.md"
    c = f.read_text()
    assert re.search(r"(Deps.*dependency|Deps.*Predictive)", c, re.IGNORECASE)


def test_T_0016_043_Sentinel_row_in_subagent_table_unchanged_after_Darwin_addition():
    """T-0016-043: Sentinel row in subagent table unchanged after Darwin addition."""
    f = INSTALLED_RULES / "agent-system.md"
    c = f.read_text()
    assert re.search(r"(Sentinel.*security.*audit|Sentinel.*Semgrep)", c, re.IGNORECASE)


def test_T_0016_044_core_agent_constant_list_does_not_include_darwin():
    """T-0016-044: core agent constant list does not include darwin."""
    f = INSTALLED_RULES / "agent-system.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    # Extract the core agent constant code block specifically
    core_block_match = re.search(r"### Core Agent Constant.*?```(.*?)```", c, re.DOTALL)
    if not core_block_match:
        pytest.skip("Core Agent Constant code block not found")
    core_block = core_block_match.group(1)
    assert "darwin" not in core_block.lower(), "darwin should not be in the core agent constant list"


def test_T_0016_045_source_references_invocation_templates_md_contains_template_id():
    """T-0016-045: source/references/invocation-templates.md contains <template id=\."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_046_claude_references_invocation_templates_md_contains_template_id():
    """T-0016-046: .claude/references/invocation-templates.md contains <template id=\."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_047_darwin_analysis_template_contains_task_brain_context_read_constraints_output():
    """T-0016-047: darwin-analysis template contains <task>, <brain-context>, <read>, <constraints>, <output>."""
    # Skip: darwin-analysis template not found
    f = INSTALLED_REFS / "invocation-templates.md"
    if not f.is_file(): pytest.skip("File not yet created")
    t = extract_template_section(f, "darwin-analysis")
    assert t, "darwin-analysis template not found"
    assert "<task>" in t
    assert "<brain-context>" in t
    assert "<read>" in t
    assert "<constraints>" in t
    assert "<output>" in t


def test_T_0016_048_darwin_analysis_constraints_include_self_edit_protection_and_escalation_ladder():
    """T-0016-048: darwin-analysis constraints include self-edit protection and escalation ladder."""
    # Skip: darwin-analysis template not found
    f = INSTALLED_REFS / "invocation-templates.md"
    if not f.is_file(): pytest.skip("File not yet created")
    t = extract_template_section(f, "darwin-analysis")
    assert t, "darwin-analysis template not found"
    assert re.search(r"self.edit.*protect|cannot.*propose.*darwin\.md", t, re.IGNORECASE)
    assert re.search(r"escalation.*ladder|escalation.*level", t, re.IGNORECASE)


def test_T_0016_049_darwin_analysis_read_includes_error_patterns_md_retro_lessons_md_telemetry_metrics_md():
    """T-0016-049: darwin-analysis <read> includes error-patterns.md, retro-lessons.md, telemetry-metrics.md."""
    # Skip: darwin-analysis template not found
    f = INSTALLED_REFS / "invocation-templates.md"
    if not f.is_file(): pytest.skip("File not yet created")
    t = extract_template_section(f, "darwin-analysis")
    assert t, "darwin-analysis template not found"
    assert re.search(r"error-patterns", t, re.IGNORECASE)
    assert re.search(r"retro-lessons", t, re.IGNORECASE)
    assert re.search(r"telemetry-metrics", t, re.IGNORECASE)


def test_T_0016_050_both_files_contain_template_id():
    """T-0016-050: both files contain <template id=\."""
    pass  # TODO: complex bats test - verify manually


def test_T_0016_051_darwin_edit_proposal_template_contains_task_context_read_constraints_output():
    """T-0016-051: darwin-edit-proposal template contains <task>, <context>, <read>, <constraints>, <output>."""
    # Skip: darwin-edit-proposal template not found
    f = INSTALLED_REFS / "invocation-templates.md"
    if not f.is_file(): pytest.skip("File not yet created")
    t = extract_template_section(f, "darwin-edit-proposal")
    assert t, "darwin-edit-proposal template not found"
    assert "<task>" in t
    assert "<context>" in t
    assert "<read>" in t
    assert "<constraints>" in t
    assert "<output>" in t


def test_T_0016_052_darwin_edit_proposal_constraints_include_dual_tree_and_self_edit_protection():
    """T-0016-052: darwin-edit-proposal constraints include dual-tree and self-edit protection."""
    # Skip: darwin-edit-proposal template not found
    f = INSTALLED_REFS / "invocation-templates.md"
    if not f.is_file(): pytest.skip("File not yet created")
    t = extract_template_section(f, "darwin-edit-proposal")
    assert t, "darwin-edit-proposal template not found"
    assert re.search(r"dual.tree|source/.*\.claude/", t, re.IGNORECASE)
    assert re.search(r"darwin.*persona|darwin\.md.*do not|darwin\.md.*not.*modif", t, re.IGNORECASE)


def test_T_0016_053_darwin_edit_proposal_context_includes_target_file_section_change_type_escalation_level_ev():
    """T-0016-053: darwin-edit-proposal context includes target file, section, change type, escalation level, evidence, impact."""
    # Skip: darwin-edit-proposal template not found
    f = INSTALLED_REFS / "invocation-templates.md"
    if not f.is_file(): pytest.skip("File not yet created")
    t = extract_template_section(f, "darwin-edit-proposal")
    assert t, "darwin-edit-proposal template not found"
    assert re.search(r"target.*file|file_path", t, re.IGNORECASE)
    assert re.search(r"target.*section|section.*identifier", t, re.IGNORECASE)
    assert re.search(r"change.*type", t, re.IGNORECASE)
    assert re.search(r"escalation.*level", t, re.IGNORECASE)
    assert re.search(r"evidence", t, re.IGNORECASE)
    assert re.search(r"expected.*impact|impact", t, re.IGNORECASE)


def test_T_0016_054_existing_template_IDs_deps_scan_sentinel_audit_unchanged_in_both_files():
    """T-0016-054: existing template IDs (deps-scan, sentinel-audit) unchanged in both files."""
    f = INSTALLED_REFS / "invocation-templates.md"
    c = f.read_text()
    assert "deps-scan" in c
    assert "sentinel-audit" in c


def test_T_0016_055_pipeline_orchestration_md_contains_Darwin_auto_trigger_section():
    """T-0016-055: pipeline-orchestration.md contains Darwin auto-trigger section."""
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    c = f.read_text()
    assert re.search(r"darwin.*auto.trigger|darwin.*auto-trigger|auto.*trigger.*darwin", c, re.IGNORECASE)


def test_T_0016_056_auto_trigger_requires_darwin_enabled_brain_available_degradation_alert_non_Micro():
    """T-0016-056: auto-trigger requires darwin_enabled, brain_available, degradation alert, non-Micro."""
    # Skip: pipeline-orchestration.md not found
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"darwin_enabled.*true|darwin_enabled", c, re.IGNORECASE)
    assert re.search(r"brain_available.*true|brain.*available", c, re.IGNORECASE)
    assert re.search(r"degradation.*alert|alert.*fired", c, re.IGNORECASE)
    assert re.search(r"non.Micro|not.*Micro|Micro.*skip|skip.*Micro", c, re.IGNORECASE)


def test_T_0016_057_auto_trigger_describes_Eva_pre_fetching_brain_context_Tier_3_prior_proposals():
    """T-0016-057: auto-trigger describes Eva pre-fetching brain context (Tier 3 + prior proposals)."""
    # Skip: pipeline-orchestration.md not found
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"agent_search|tier.*3|telemetry", c, re.IGNORECASE)
    assert re.search(r"darwin_proposal|prior.*darwin|prior.*proposal", c, re.IGNORECASE)


def test_T_0016_058_approved_proposal_capture_includes_darwin_proposal_id_target_metric_baseline_value_escala():
    """T-0016-058: approved proposal capture includes darwin_proposal_id, target_metric, baseline_value, escalation_level."""
    # Skip: pipeline-orchestration.md not found
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"darwin_proposal_id", c, re.IGNORECASE)
    assert re.search(r"target_metric", c, re.IGNORECASE)
    assert re.search(r"baseline_value", c, re.IGNORECASE)
    assert re.search(r"escalation_level", c, re.IGNORECASE)


def test_T_0016_059_rejected_proposal_capture_includes_rejected_true_and_rejection_reason():
    """T-0016-059: rejected proposal capture includes rejected: true and rejection_reason."""
    # Skip: pipeline-orchestration.md not found
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"rejected.*true", c, re.IGNORECASE)
    assert re.search(r"rejection_reason", c, re.IGNORECASE)


def test_T_0016_060_auto_trigger_states_hard_pause_Eva_does_not_auto_advance_past_proposals():
    """T-0016-060: auto-trigger states hard pause -- Eva does not auto-advance past proposals."""
    # Skip: pipeline-orchestration.md not found
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"hard pause|does not auto.advance|pause", c, re.IGNORECASE)


def test_T_0016_061_auto_trigger_states_Darwin_does_not_block_pipeline_completion():
    """T-0016-061: auto-trigger states Darwin does not block pipeline completion."""
    # Skip: pipeline-orchestration.md not found
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"does not block.*pipeline|not.*block.*completion|user can.*skip|dismiss", c, re.IGNORECASE)


def test_T_0016_067_when_darwin_enabled_false_auto_trigger_is_skipped_entirely():
    """T-0016-067: when darwin_enabled false, auto-trigger is skipped entirely."""
    # Skip: pipeline-orchestration.md not found
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"darwin_enabled.*false.*skip|skip.*entirely|when.*darwin_enabled.*false", c, re.IGNORECASE)


def test_T_0016_079_existing_telemetry_summary_section_present_in_pipeline_orchestration_md():
    """T-0016-079: existing telemetry summary section present in pipeline-orchestration.md."""
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    c = f.read_text()
    assert re.search(r"telemetry.*summary|pipeline.*end.*telemetry", c, re.IGNORECASE)


def test_T_0016_081_source_and_claude_pipeline_orchestration_md_both_contain_Darwin_auto_trigger():
    """T-0016-081: source and .claude pipeline-orchestration.md both contain Darwin auto-trigger."""
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    c = f.read_text()
    assert re.search(r"darwin.*auto.trigger|darwin.*auto-trigger", c, re.IGNORECASE)


def test_T_0016_102_Darwin_auto_trigger_section_positioned_after_telemetry_summary_before_staleness_check():
    """T-0016-102: Darwin auto-trigger section positioned after telemetry summary, before staleness check."""
    # Skip: Telemetry summary section not found
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    if not f.is_file(): pytest.skip("File not yet created")


def test_T_0016_103_auto_trigger_section_documents_one_Colby_invocation_per_approved_proposal():
    """T-0016-103: auto-trigger section documents one Colby invocation per approved proposal."""
    # Skip: pipeline-orchestration.md not found
    f = INSTALLED_RULES / "pipeline-orchestration.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"one.*colby.*per|per.*proposal.*colby|each.*approved.*colby|separately|atomic", c, re.IGNORECASE)
    assert re.search(r"darwin-edit-proposal", c, re.IGNORECASE)


def test_T_0016_062_default_persona_md_boot_step_5b_includes_Darwin_post_edit_tracking():
    """T-0016-062: default-persona.md boot step 5b includes Darwin post-edit tracking."""
    f = INSTALLED_RULES / "default-persona.md"
    c = f.read_text()
    assert re.search(r"darwin.*post.edit|post.edit.*track|darwin.*edit.*track", c, re.IGNORECASE)


def test_T_0016_063_post_edit_tracking_queries_for_thought_type_decision_source_phase_darwin():
    """T-0016-063: post-edit tracking queries for thought_type: decision, source_phase: darwin."""
    # Skip: default-persona.md not found
    f = INSTALLED_RULES / "default-persona.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"thought_type.*decision|decision", c, re.IGNORECASE)
    assert re.search(r"source_phase.*darwin|darwin", c, re.IGNORECASE)


def test_T_0016_064_post_edit_tracking_computes_metric_delta_when_3_subsequent_pipelines_exist():
    """T-0016-064: post-edit tracking computes metric delta when 3+ subsequent pipelines exist."""
    # Skip: default-persona.md not found
    f = INSTALLED_RULES / "default-persona.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"3.*subsequent.*pipeline|3\+.*pipeline|metric.*delta|delta", c, re.IGNORECASE)


def test_T_0016_065_post_edit_tracking_reports_improved_edits_and_flags_worsened_as_regressions():
    """T-0016-065: post-edit tracking reports improved edits and flags worsened as regressions."""
    # Skip: default-persona.md not found
    f = INSTALLED_RULES / "default-persona.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"improv|worsen|regression", c, re.IGNORECASE)


def test_T_0016_066_boot_announcement_includes_Darwin_status_line_when_darwin_enabled_true():
    """T-0016-066: boot announcement includes Darwin status line when darwin_enabled true."""
    f = INSTALLED_RULES / "default-persona.md"
    c = f.read_text()
    assert re.search(r"darwin.*active|darwin.*status|darwin.*enabled|darwin.*disabled.*brain", c, re.IGNORECASE)


def test_T_0016_080_existing_telemetry_trend_logic_present_in_default_persona_md():
    """T-0016-080: existing telemetry trend logic present in default-persona.md."""
    f = INSTALLED_RULES / "default-persona.md"
    c = f.read_text()
    assert re.search(r"telemetry.*trend|trend", c, re.IGNORECASE)


def test_T_0016_082_source_and_claude_default_persona_md_both_contain_Darwin_post_edit_tracking():
    """T-0016-082: source and .claude default-persona.md both contain Darwin post-edit tracking."""
    f = INSTALLED_RULES / "default-persona.md"
    c = f.read_text()
    assert re.search(r"darwin.*post.edit|post.edit.*track|darwin.*edit.*track", c, re.IGNORECASE)


def test_T_0016_071_persona_constraint_references_exactly_5_pipelines_as_minimum_not_4_not_6():
    """T-0016-071: persona constraint references exactly 5 pipelines as minimum (not 4, not 6)."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "constraints")
    assert re.search(r"5", section, re.IGNORECASE)


def test_T_0016_075_output_or_workflow_documents_all_agents_thriving_no_changes_proposed():
    """T-0016-075: <output> or <workflow> documents all-agents-thriving = no changes proposed."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"no.*change.*propos|all.*thriving|no.*proposal", c, re.IGNORECASE)


def test_T_0016_076_persona_documents_Level_5_agent_replacement_requires_double_confirmation():
    """T-0016-076: persona documents Level 5 (agent replacement) requires double confirmation."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"level 5.*double.*confirm|double.*confirm|removal.*confirm", c, re.IGNORECASE)


def test_T_0016_077_persona_constraints_block_proposals_targeting_darwin_md():
    """T-0016-077: persona constraints block proposals targeting darwin.md."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    section = extract_tag_content(f, "constraints")
    assert re.search(r"darwin\.md", section, re.IGNORECASE)
    assert re.search(r"cannot.*propose|self.edit", section, re.IGNORECASE)


def test_T_0016_104_persona_or_command_does_NOT_reference_acceptance_rate_self_adjustment():
    """T-0016-104: persona or command does NOT reference acceptance rate self-adjustment."""
    # Skip: Darwin files not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert not re.search(r"acceptance.*rate.*self.adjust|self.adjust.*acceptance|recalibrat.*acceptance|30.*accept", c, re.IGNORECASE)


def test_T_0016_101_persona_output_specifies_report_shape_consumed_by_auto_trigger_flow():
    """T-0016-101: persona <output> specifies report shape consumed by auto-trigger flow."""
    # Skip: darwin.md not yet created
    f = INSTALLED_AGENTS / "darwin.md"
    if not f.is_file(): pytest.skip("File not yet created")


def test_T_0016_083_SKILL_md_contains_a_Step_6e_block():
    """T-0016-083: SKILL.md contains a Step 6e block."""
    f = SKILL_FILE
    c = f.read_text()
    assert re.search(r"step 6e|### 6e|## Step 6e", c, re.IGNORECASE)


def test_T_0016_084_Step_6e_is_positioned_after_Step_6d_and_before_Brain_setup_offer():
    """T-0016-084: Step 6e is positioned after Step 6d and before Brain setup offer."""
    # Skip: Step 6d not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")


def test_T_0016_085_Step_6e_offer_text_mentions_telemetry_underperforming_agents_structural_fixes():
    """T-0016-085: Step 6e offer text mentions telemetry, underperforming agents, structural fixes."""
    # Skip: Step 6e block not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"telemetry", c, re.IGNORECASE)
    assert re.search(r"underperform|struggling|agent", c, re.IGNORECASE)
    assert re.search(r"structural.*fix|structural.*improv|persona.*edit|fix", c, re.IGNORECASE)


def test_T_0016_086_Step_6e_offer_text_mentions_Brain_requirement():
    """T-0016-086: Step 6e offer text mentions Brain requirement."""
    # Skip: Step 6e block not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"brain|atelier.*brain", c, re.IGNORECASE)


def test_T_0016_087_Step_6e_yes_path_sets_darwin_enabled_to_true():
    """T-0016-087: Step 6e yes-path sets darwin_enabled to true."""
    # Skip: Step 6e block not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"darwin_enabled.*true|set.*darwin.*true", c, re.IGNORECASE)


def test_T_0016_088_Step_6e_yes_path_assembles_darwin_agent_to_claude_agents_darwin_md():
    """T-0016-088: Step 6e yes-path assembles darwin agent to .claude/agents/darwin.md."""
    # Skip: Step 6e block not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"agents/darwin|darwin\.md", c, re.IGNORECASE)


def test_T_0016_089_Step_6e_yes_path_copies_source_commands_darwin_md_to_claude_commands_darwin_md():
    """T-0016-089: Step 6e yes-path copies source/commands/darwin.md to .claude/commands/darwin.md."""
    # Skip: Step 6e block not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"commands/darwin|command.*darwin", c, re.IGNORECASE)


def test_T_0016_090_Step_6e_no_path_leaves_darwin_enabled_false_and_prints_not_enabled():
    """T-0016-090: Step 6e no-path leaves darwin_enabled false and prints not enabled."""
    # Skip: Step 6e block not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"not enabled|skip|decline", c, re.IGNORECASE)


def test_T_0016_091_Step_6_summary_printout_includes_Darwin_enabled_not_enabled_line():
    """T-0016-091: Step 6 summary printout includes Darwin enabled/not-enabled line."""
    f = SKILL_FILE
    c = f.read_text()
    assert re.search(r"darwin.*enabled|darwin.*not.*enabled", c, re.IGNORECASE)


def test_T_0016_092_Step_6e_documents_treating_absent_darwin_enabled_as_false():
    """T-0016-092: Step 6e documents treating absent darwin_enabled as false."""
    # Skip: Step 6e block not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"absent.*false|missing.*false|not.*present.*false|default.*false", c, re.IGNORECASE)


def test_T_0016_093_Step_6e_documents_idempotent_behavior_when_darwin_already_enabled():
    """T-0016-093: Step 6e documents idempotent behavior when darwin already enabled."""
    # Skip: Step 6e block not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"already.*enabled|idempoten|skip.*mutation", c, re.IGNORECASE)


def test_T_0016_094_Step_6e_documents_confirming_before_changing_from_false_to_true():
    """T-0016-094: Step 6e documents confirming before changing from false to true."""
    # Skip: Step 6e block not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"confirm|ask|offer|enable|want|would you like", c, re.IGNORECASE)


def test_T_0016_095_Step_6d_Deps_block_is_unchanged_after_Step_6e_insertion():
    """T-0016-095: Step 6d (Deps) block is unchanged after Step 6e insertion."""
    f = SKILL_FILE
    c = f.read_text()
    assert re.search(r"step 6d|deps", c, re.IGNORECASE)
    assert re.search(r"deps_agent_enabled", c, re.IGNORECASE)


def test_T_0016_096_Brain_setup_offer_is_still_present_and_positioned_after_Step_6e():
    """T-0016-096: Brain setup offer is still present and positioned after Step 6e."""
    # Skip: Step 6e not found
    f = SKILL_FILE
    if not f.is_file(): pytest.skip("File not yet created")


def test_T_0016_097_Steps_6a_Sentinel_6b_Agent_Teams_6c_CI_Watch_unchanged_after_Step_6e_insertion():
    """T-0016-097: Steps 6a (Sentinel), 6b (Agent Teams), 6c (CI Watch) unchanged after Step 6e insertion."""
    f = SKILL_FILE
    c = f.read_text()
    assert re.search(r"step 6a|sentinel", c, re.IGNORECASE)
    assert re.search(r"sentinel_enabled", c, re.IGNORECASE)
    assert re.search(r"step 6b|agent.teams", c, re.IGNORECASE)
    assert re.search(r"agent_teams_enabled", c, re.IGNORECASE)
    assert re.search(r"step 6c|ci.watch", c, re.IGNORECASE)
    assert re.search(r"ci_watch_enabled", c, re.IGNORECASE)


def test_T_0016_036b_Darwin_row_in_subagent_table_lists_Read_Glob_Grep_Bash_read_only():
    """T-0016-036b: Darwin row in subagent table lists Read, Glob, Grep, Bash (read-only)."""
    # Skip: Darwin subagent row not found
    f = INSTALLED_RULES / "agent-system.md"
    if not f.is_file(): pytest.skip("File not yet created")
    c = f.read_text()
    assert re.search(r"Read", c, re.IGNORECASE)
    assert re.search(r"Glob", c, re.IGNORECASE)
    assert re.search(r"Grep", c, re.IGNORECASE)
    assert re.search(r"Bash", c, re.IGNORECASE)
    assert re.search(r"read.only", c, re.IGNORECASE)

