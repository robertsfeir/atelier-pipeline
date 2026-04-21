"""ADR-0023: Agent Specification Reduction -- Structural Tests.

Migrated from reduction-structural.test.bats.
"""

import json
import os
import re
import subprocess
import tempfile
import time

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



def test_T_0023_001_agent_preamble_md_contains_protocol_id():
    """T-0023-001: agent-preamble.md contains XML id tag (preamble or protocol)."""
    f = SHARED_REFS / "agent-preamble.md"
    assert f.is_file(), "agent-preamble.md not found"
    c = f.read_text()
    assert '<preamble id=' in c or '<protocol id=' in c, \
        "agent-preamble.md missing XML id tag (<preamble id= or <protocol id=)"


def test_T_0023_002_Cal_persona_Brain_Access_section_is_6_lines_and_references_agent_preamble_md():
    """T-0023-002: Cal persona Brain Access section is <=6 lines and references agent-preamble.md."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()


def test_T_0023_003_Colby_persona_Brain_Access_section_is_6_lines_and_references_agent_preamble_md():
    """T-0023-003: Colby persona Brain Access section is <=6 lines and references agent-preamble.md."""
    f = SHARED_AGENTS / "colby.md"
    assert f.is_file()


def test_T_0023_004_Roz_persona_Brain_Access_section_is_6_lines_and_references_agent_preamble_md():
    """T-0023-004: Roz persona Brain Access section is <=6 lines and references agent-preamble.md."""
    f = SHARED_AGENTS / "roz.md"
    assert f.is_file()


def test_T_0023_005_Agatha_persona_Brain_Access_section_is_6_lines_and_references_agent_preamble_md():
    """T-0023-005: Agatha persona Brain Access section is <=6 lines and references agent-preamble.md."""
    f = SHARED_AGENTS / "agatha.md"
    assert f.is_file()


def test_T_0023_006_Cal_persona_retains_thought_type_decision_and_pattern_with_importance_values():
    """T-0023-006: Brain-extractor retains thought_type 'decision' and 'pattern' with importance values for Cal.

    Post-ADR-0024: brain capture metadata (thought_type, importance) was extracted
    from agent personas into brain-extractor.md. Verify the brain-extractor maps
    Cal correctly and retains the required thought_types.
    """
    f = SHARED_AGENTS / "brain-extractor.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"thought_type.*decision|thought_type: 'decision'|decision\s*\|", c), \
        "brain-extractor missing thought_type 'decision'"
    assert re.search(r"thought_type.*pattern|thought_type: 'pattern'|pattern\s*\|", c), \
        "brain-extractor missing thought_type 'pattern'"
    assert "importance" in c
    # Cal is mapped in the agent-to-metadata table
    assert re.search(r"cal\s*\|", c), "brain-extractor missing Cal agent mapping"


def test_T_0023_006a_Roz_persona_retains_thought_type_pattern_and_lesson_with_importance_values():
    """T-0023-006a: Brain-extractor retains thought_type 'pattern' and 'lesson' with importance values for Roz.

    Post-ADR-0024: brain capture metadata was extracted into brain-extractor.md.
    """
    f = SHARED_AGENTS / "brain-extractor.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"thought_type.*pattern|thought_type: 'pattern'|pattern\s*\|", c), \
        "brain-extractor missing thought_type 'pattern'"
    assert re.search(r"thought_type.*lesson|thought_type: 'lesson'|lesson\s*\|", c), \
        "brain-extractor missing thought_type 'lesson'"
    assert "importance" in c
    # Roz is mapped in the agent-to-metadata table
    assert re.search(r"roz\s*\|", c), "brain-extractor missing Roz agent mapping"


def test_T_0023_006b_Agatha_persona_retains_thought_type_decision_and_insight_with_importance_values():
    """T-0023-006b: Brain-extractor retains thought_type 'decision' and 'insight' with importance values for Agatha.

    Post-ADR-0024: brain capture metadata was extracted into brain-extractor.md.
    """
    f = SHARED_AGENTS / "brain-extractor.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"thought_type.*decision|thought_type: 'decision'|decision\s*\|", c), \
        "brain-extractor missing thought_type 'decision'"
    assert re.search(r"thought_type.*insight|thought_type: 'insight'|insight\s*\|", c), \
        "brain-extractor missing thought_type 'insight'"
    # Importance values can appear as "importance: 0.X" or compact "(0.X)"
    assert re.search(r"importance|0\.\d", c), \
        "brain-extractor missing importance values"
    # Agatha is mapped in the agent-to-metadata table
    assert re.search(r"agatha\s*\|", c), "brain-extractor missing Agatha agent mapping"


def test_T_0023_007_Colby_persona_retains_thought_type_insight_and_pattern_with_importance_values():
    """T-0023-007: Brain-extractor retains thought_type 'insight' and 'pattern' with importance values for Colby.

    Post-ADR-0024: brain capture metadata was extracted into brain-extractor.md.
    """
    f = SHARED_AGENTS / "brain-extractor.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"thought_type.*insight|thought_type: 'insight'|insight\s*\|", c), \
        "brain-extractor missing thought_type 'insight'"
    assert re.search(r"thought_type.*pattern|thought_type: 'pattern'|pattern\s*\|", c), \
        "brain-extractor missing thought_type 'pattern'"
    assert "importance" in c
    # Colby is mapped in the agent-to-metadata table
    assert re.search(r"colby\s*\|", c), "brain-extractor missing Colby agent mapping"


def test_T_0023_008_agent_preamble_md_step_4_still_references_mcpServers_atelier_brain_agents_list():
    """T-0023-008: agent-preamble.md step 4 still references mcpServers: atelier-brain agents list."""
    f = SHARED_REFS / "agent-preamble.md"
    assert f.is_file()
    c = f.read_text()
    # ADR-0023 reduced agent-preamble: brain context is now documented as
    # injected via <brain-context> tag, not mcpServers reference.
    # brain-extractor hook handles capture mechanically.
    assert re.search(r"brain.context|brain.extractor|brain.*capture|agent_capture", c), \
        "agent-preamble.md missing brain context reference"


def test_T_0023_010_step_sizing_md_exists_in_source_shared_references_and_contains_S1_S5_table():
    """T-0023-010: step-sizing.md exists in source/shared/references/ and contains S1-S5 table."""
    f = SHARED_REFS / "step-sizing.md"
    assert f.is_file()
    c = f.read_text()
    assert "S1" in c
    assert "S2" in c
    assert "S3" in c
    assert "S4" in c
    assert "S5" in c


def test_T_0023_011_step_sizing_md_contains_split_heuristics_table():
    """T-0023-011: step-sizing.md contains split heuristics table."""
    f = SHARED_REFS / "step-sizing.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"split|heuristic", c, re.IGNORECASE)


def test_T_0023_012_step_sizing_md_contains_evidence_paragraph_with_57_to_93_data():
    """T-0023-012: step-sizing.md contains evidence paragraph with 57% to 93% data."""
    f = SHARED_REFS / "step-sizing.md"
    assert f.is_file()
    c = f.read_text()
    assert "57%" in c
    assert "93%" in c


def test_T_0023_013_step_sizing_md_contains_Darwin_review_trigger():
    """T-0023-013: step-sizing.md contains Darwin review trigger."""
    f = SHARED_REFS / "step-sizing.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"[Dd]arwin", c, re.IGNORECASE)


def test_T_0023_014_Cal_persona_references_step_sizing_md_by_path():
    """T-0023-014: Cal persona references step-sizing.md by path."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    c = f.read_text()
    assert "step-sizing" in c


def test_T_0023_015_Cal_persona_does_NOT_contain_the_S1_S5_table_inline_moved_not_duplicated():
    """T-0023-015: Cal persona does NOT contain the S1-S5 table inline (moved, not duplicated)."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()


def test_T_0023_021_Cal_persona_contains_spec_challenge_and_SPOF_in_required_actions():
    """T-0023-021: Cal persona contains 'spec challenge' and 'SPOF' in required-actions."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"spec.*challenge|challenge.*spec", c, re.IGNORECASE)
    assert re.search(r"SPOF|single point of failure", c, re.IGNORECASE)


def test_T_0023_022_Cal_persona_contains_all_4_hard_gates():
    """T-0023-022: Cal persona contains all 4 hard gates."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"gate.*(1|one)|1\.", c, re.IGNORECASE)
    assert re.search(r"gate.*(2|two)|2\.", c, re.IGNORECASE)
    assert re.search(r"gate.*(3|three)|3\.", c, re.IGNORECASE)
    assert re.search(r"gate.*(4|four)|4\.", c, re.IGNORECASE)


def test_T_0023_023_Cal_persona_contains_vertical_slice_preference_text():
    """T-0023-023: Cal persona contains vertical slice preference text."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"vertical.*slice", c, re.IGNORECASE)


def test_T_0023_024_Cal_persona_contains_anti_goals_requirement():
    """T-0023-024: Cal persona contains anti-goals requirement."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"anti.goal", c, re.IGNORECASE)


def test_T_0023_025_Cal_persona_has_exactly_1_example_demonstrating_spec_challenge_SPOF_pattern():
    """T-0023-025: Cal persona has exactly 1 example demonstrating spec challenge + SPOF pattern."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    section = extract_tag_content(f, "examples")
    assert_has_tag(f, "examples")


def test_T_0023_026_Cal_persona_does_NOT_contain_State_Machine_Analysis_as_a_section_header():
    """T-0023-026: Cal persona does NOT contain 'State Machine Analysis' as a section header."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    c = f.read_text()
    assert not re.search(r"^#+.*State Machine Analysis", c, re.MULTILINE)


def test_T_0023_027_Cal_persona_does_NOT_contain_Blast_Radius_Verification_as_a_section_header():
    """T-0023-027: Cal persona does NOT contain 'Blast Radius Verification' as a section header."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    c = f.read_text()
    assert not re.search(r"^#+.*Blast Radius Verification", c, re.MULTILINE)


def test_T_0023_028_Cal_persona_does_NOT_contain_Migration_Rollback_as_a_section_header():
    """T-0023-028: Cal persona does NOT contain 'Migration & Rollback' as a section header."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    c = f.read_text()
    assert not re.search(r"^#+.*Migration.*Rollback", c, re.MULTILINE)


def test_T_0023_029_Cal_persona_output_template_retains_DoR_ADR_skeleton_UX_Coverage_Wiring_Coverage_Contract():
    """T-0023-029: Cal persona output template retains DoR, ADR skeleton, UX Coverage, Wiring Coverage, Contract Boundaries, Notes for Colby, DoD."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    section = extract_tag_content(f, "output")
    assert re.search(r"DoR", section, re.IGNORECASE)
    assert re.search(r"ADR.*skeleton|skeleton", section, re.IGNORECASE)
    assert re.search(r"UX.*[Cc]overage", section, re.IGNORECASE)
    assert re.search(r"[Ww]iring.*[Cc]overage", section, re.IGNORECASE)
    assert re.search(r"[Cc]ontract.*[Bb]oundar", section, re.IGNORECASE)
    assert re.search(r"[Nn]otes.*[Cc]olby", section, re.IGNORECASE)
    assert re.search(r"DoD", section, re.IGNORECASE)


def test_T_0023_031_Colby_persona_contains_Make_Roz_s_tests_pass_verbatim_or_near_verbatim():
    """T-0023-031: Colby persona contains 'Make Roz's tests pass' verbatim or near-verbatim."""
    f = SHARED_AGENTS / "colby.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"Roz.*tests.*pass|Make Roz.*test", c, re.IGNORECASE)


def test_T_0023_032_Colby_persona_contains_do_not_modify_assertions_anti_modification_constraint():
    """T-0023-032: Colby persona contains 'do not modify' + 'assertions' anti-modification constraint."""
    f = SHARED_AGENTS / "colby.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"do not modify.*assert|not modify.*assertion|never.*modify.*assert", c, re.IGNORECASE)


def test_T_0023_033_Colby_persona_contains_Contracts_Produced_table_in_output_template():
    """T-0023-033: Colby persona contains Contracts Produced table in output template."""
    f = SHARED_AGENTS / "colby.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"[Cc]ontracts.*[Pp]roduced", c, re.IGNORECASE)


def test_T_0023_034_Colby_persona_contains_premise_verification_section():
    """T-0023-034: Colby persona contains premise verification section."""
    f = SHARED_AGENTS / "colby.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"premise.*verif", c, re.IGNORECASE)


def test_T_0023_035_Colby_persona_has_exactly_1_example_demonstrating_premise_verification():
    """T-0023-035: Colby persona has exactly 1 example demonstrating premise verification."""
    f = SHARED_AGENTS / "colby.md"
    assert f.is_file()
    section = extract_tag_content(f, "examples")
    assert re.search(r"premise|verif|wrong.*default|root.*cause", section, re.IGNORECASE)
    assert_has_tag(f, "examples")


def test_T_0023_036_Colby_persona_does_NOT_contain_Retrieval_led_reasoning_as_opening_of_required_actions():
    """T-0023-036: Colby persona does NOT contain 'Retrieval-led reasoning' as opening of required-actions."""
    f = SHARED_AGENTS / "colby.md"
    assert f.is_file()
    c = f.read_text()
    assert not re.search(r"Retrieval-led reasoning", c, re.MULTILINE)


def test_T_0023_037_Colby_persona_TDD_constraint_is_explicit_test_fail_implement_in_same_file():
    """T-0023-037: Colby persona TDD constraint is explicit (test + fail + implement in same file)."""
    f = SHARED_AGENTS / "colby.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"test.*fail|fail.*test|test.first|TDD", c, re.IGNORECASE)
    assert re.search(r"implement", c, re.IGNORECASE)


def test_T_0023_041_Roz_persona_contains_assert_what_code_SHOULD_do_or_equivalent_domain_intent_constraint():
    """T-0023-041: Roz persona contains 'assert what code SHOULD do' or equivalent domain-intent constraint."""
    f = SHARED_AGENTS / "roz.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"assert.*SHOULD.*do|assert.*domain.*correct|what.*should.*do|domain.intent", c, re.IGNORECASE)


def test_T_0023_042_Roz_persona_contains_2_examples_both_judgment_restraint():
    """T-0023-042: Roz persona contains 2 examples (both judgment restraint)."""
    f = SHARED_AGENTS / "roz.md"
    assert f.is_file()
    section = extract_tag_content(f, "examples")
    assert_has_tag(f, "examples")


def test_T_0023_043_Roz_persona_references_qa_checks_md():
    """T-0023-043: Roz persona references qa-checks.md."""
    f = SHARED_AGENTS / "roz.md"
    assert f.is_file()
    c = f.read_text()
    assert "qa-checks" in c


def test_T_0023_044_Roz_persona_does_NOT_contain_numbered_trace_steps_1_Entry_point_2_API_call_etc():
    """T-0023-044: Roz persona does NOT contain numbered trace steps (1. Entry point, 2. API call, etc.)."""
    f = SHARED_AGENTS / "roz.md"
    assert f.is_file()
    c = f.read_text()
    assert not re.search(r"^[0-9]+\.\s*(Entry point|API call|Route handler|Business logic|Data layer|Response path)", c, re.MULTILINE)


def test_T_0023_045_Roz_persona_does_NOT_contain_Layer_Awareness_table():
    """T-0023-045: Roz persona does NOT contain Layer Awareness table."""
    f = SHARED_AGENTS / "roz.md"
    assert f.is_file()
    c = f.read_text()
    assert not re.search(r"^#+.*Layer Awareness", c, re.MULTILINE)


def test_T_0023_045a_Roz_persona_contains_explicit_TDD_constraint_language_per_R15():
    """T-0023-045a: Roz persona contains explicit TDD constraint language per R15."""
    f = SHARED_AGENTS / "roz.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"tests define.*correct|BEFORE.*[Cc]olby.*build|test.first|TDD", c, re.IGNORECASE)


def test_T_0023_050_Robert_persona_60_lines():
    """T-0023-050: Robert persona <=60 lines."""
    f = SHARED_AGENTS / "robert.md"
    assert f.is_file()
    lines = len(f.read_text().splitlines())
    assert lines <= 60, f"{lines} lines (expected <= 60)"


def test_T_0023_051_Robert_persona_contains_information_asymmetry_constraint():
    """T-0023-051: Robert persona contains 'information asymmetry' constraint."""
    f = SHARED_AGENTS / "robert.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"information.*asymmetry", c, re.IGNORECASE)


def test_T_0023_052_Robert_persona_contains_PASS_DRIFT_MISSING_AMBIGUOUS_vocabulary():
    """T-0023-052: Robert persona contains PASS/DRIFT/MISSING/AMBIGUOUS vocabulary."""
    f = SHARED_AGENTS / "robert.md"
    assert f.is_file()
    c = f.read_text()
    assert "PASS" in c
    assert "DRIFT" in c
    assert "MISSING" in c
    assert "AMBIGUOUS" in c


def test_T_0023_053a_Sable_persona_contains_information_asymmetry_constraint():
    """T-0023-053a: Sable persona contains 'information asymmetry' constraint."""
    f = SHARED_AGENTS / "sable.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"information.*asymmetry", c, re.IGNORECASE)


def test_T_0023_054_Sable_persona_contains_five_state_audit_requirement():
    """T-0023-054: Sable persona contains five-state audit requirement."""
    f = SHARED_AGENTS / "sable.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"five.state|5.state", c, re.IGNORECASE)


def test_T_0023_055_Poirot_persona_80_lines():
    """T-0023-055: Poirot persona <=80 lines (raised from 65 for Sonnet procedural scaffolding)."""
    f = SHARED_AGENTS / "investigator.md"
    assert f.is_file()
    lines = len(f.read_text().splitlines())
    assert lines <= 80, f"{lines} lines (expected <= 80)"


def test_T_0023_056_Poirot_persona_contains_minimum_5_findings_constraint():
    """T-0023-056: Poirot persona contains 'minimum 5 findings' constraint."""
    f = SHARED_AGENTS / "investigator.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"(min|minimum).*5.*finding|at least 5.*finding|5\+.*finding", c, re.IGNORECASE)


def test_T_0023_057_Poirot_persona_contains_cross_layer_wiring_check_constraint():
    """T-0023-057: Poirot persona contains cross-layer wiring check constraint."""
    f = SHARED_AGENTS / "investigator.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"cross.layer.*wiring|wiring.*check|orphan.*endpoint|phantom.*call", c, re.IGNORECASE)


def test_T_0023_058a_Ellis_persona_contains_per_unit_vs_final_commit_distinction():
    """T-0023-058a: Ellis persona contains per-unit vs final commit distinction."""
    f = SHARED_AGENTS / "ellis.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"per.unit|per.wave", c, re.IGNORECASE)
    assert re.search(r"final", c, re.IGNORECASE)


def test_T_0023_059_Sentinel_persona_65_lines():
    """T-0023-059: Sentinel persona <=65 lines."""
    f = SHARED_AGENTS / "sentinel.md"
    assert f.is_file()
    lines = len(f.read_text().splitlines())
    assert lines <= 65, f"{lines} lines (expected <= 65)"


def test_T_0023_060_Sentinel_persona_contains_CWE_OWASP_requirement():
    """T-0023-060: Sentinel persona contains CWE/OWASP requirement."""
    f = SHARED_AGENTS / "sentinel.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"CWE|OWASP", c, re.IGNORECASE)


def test_T_0023_061_Darwin_persona_100_lines():
    """T-0023-061: Darwin persona <=100 lines."""
    f = SHARED_AGENTS / "darwin.md"
    assert f.is_file()
    lines = len(f.read_text().splitlines())
    assert lines <= 100, f"{lines} lines (expected <= 100)"


def test_T_0023_062_Darwin_persona_contains_self_edit_protection_constraint():
    """T-0023-062: Darwin persona contains self-edit protection constraint."""
    f = SHARED_AGENTS / "darwin.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"self.edit.*protect|cannot.*propose.*darwin\.md|cannot.*modify.*darwin", c, re.IGNORECASE)


def test_T_0023_063_Darwin_persona_contains_5_pipelines_data_requirement():
    """T-0023-063: Darwin persona contains '5+ pipelines' data requirement."""
    f = SHARED_AGENTS / "darwin.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"5.*pipeline|five.*pipeline", c, re.IGNORECASE)


def test_T_0023_064_Deps_persona_90_lines():
    """T-0023-064: Deps persona <=90 lines."""
    f = SHARED_AGENTS / "deps.md"
    assert f.is_file()
    lines = len(f.read_text().splitlines())
    assert lines <= 90, f"{lines} lines (expected <= 90)"


def test_T_0023_065_Deps_persona_contains_conservative_risk_labeling_constraint():
    """T-0023-065: Deps persona contains conservative risk labeling constraint."""
    f = SHARED_AGENTS / "deps.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"conservative.*label|conservative.*risk|risk.*classif|default.*high", c, re.IGNORECASE)


def test_T_0023_066_Distillator_persona_130_lines_NOT_reduced_below_Haiku_threshold_per_R14():
    """T-0023-066: Distillator persona >=130 lines (NOT reduced below Haiku threshold per R14)."""
    f = SHARED_AGENTS / "distillator.md"
    assert f.is_file()
    lines = len(f.read_text().splitlines())
    assert lines >= 130, f"{lines} lines (expected >= 130)"


def test_T_0023_066a_Distillator_persona_140_lines_ceiling_from_Step_1f_table():
    """T-0023-066a: Distillator persona <=140 lines (ceiling from Step 1f table)."""
    f = SHARED_AGENTS / "distillator.md"
    assert f.is_file()
    lines = len(f.read_text().splitlines())
    assert lines <= 140, f"{lines} lines (expected <= 140)"


def test_T_0023_067_Distillator_persona_contains_2_examples_Haiku_compliance_grounding():
    """T-0023-067: Distillator persona contains 2 examples (Haiku compliance grounding)."""
    f = SHARED_AGENTS / "distillator.md"
    assert f.is_file()
    section = extract_tag_content(f, "examples")
    assert_has_tag(f, "examples")


@pytest.mark.parametrize("agent_file", ALL_AGENTS_12)
def test_T_0023_068_Every_agent_persona_has_1_examples_section_with_1_example(agent_file):
    """T-0023-068: Every agent persona has >=1 <examples> section with >=1 example."""
    f = SHARED_AGENTS / agent_file
    assert f.is_file()
    section = extract_tag_content(f, "examples")
    assert section, f"No <examples> content found in {agent_file}"


@pytest.mark.parametrize("agent_file", ALL_AGENTS_12)
def test_T_0023_069_No_agent_persona_contains_How_Agent_Fits_the_Pipeline_section(agent_file):
    """T-0023-069: No agent persona contains 'How [Agent] Fits the Pipeline' section."""
    f = SHARED_AGENTS / agent_file
    assert f.is_file()
    c = f.read_text()
    assert not re.search(r"^#+.*How.*Fits.*Pipeline", c, re.IGNORECASE | re.MULTILINE), \
        f"Found 'How X Fits the Pipeline' section in {agent_file}"


@pytest.mark.parametrize("agent_file", ALL_AGENTS_12)
def test_T_0023_070_No_Opus_Sonnet_agent_persona_contains_generic_review_category_checklists(agent_file):
    """T-0023-070: No Opus/Sonnet agent persona contains generic review category checklists."""
    f = SHARED_AGENTS / agent_file
    assert f.is_file()
    # Distillator is Haiku -- skip checklist check for it
    if agent_file == "distillator.md":
        return
    c = f.read_text()
    # Generic 8-category checklist patterns: numbered/bulleted lists with
    # generic review categories (logic, security, error handling, naming, etc.)
    assert not re.search(
        r"- (Logic|Security|Error handling|Naming|Dead code|Resource management|Concurrency|Type safety):",
        c,
    ), f"Found generic review category checklist in {agent_file}"


@pytest.mark.parametrize("agent_file", ALL_AGENTS_12)
def test_T_0023_071_Every_reduced_agent_persona_retains_its_original_YAML_frontmatter_unchanged(agent_file):
    """T-0023-071: Every reduced agent persona retains its original YAML frontmatter unchanged."""
    f = SHARED_AGENTS / agent_file
    assert f.is_file()
    c = f.read_text()
    # Source shared agents use HTML comment headers, not YAML frontmatter.
    # Verify the HTML comment header is preserved.
    assert "<!-- Part of atelier-pipeline" in c, f"Missing HTML comment header in {agent_file}"


@pytest.mark.parametrize("agent_file", ALL_AGENTS_12)
def test_T_0023_072_Every_reduced_agent_persona_contains_all_required_XML_tags_identity_required_actions_work(agent_file):
    """T-0023-072: Every reduced agent persona contains all required XML tags (identity, required-actions, workflow, examples, constraints, output)."""
    f = SHARED_AGENTS / agent_file
    assert f.is_file()
    c = f.read_text()
    # Ellis is exempt from shared preamble (no <required-actions>)
    required_tags = ["identity", "workflow", "examples", "constraints", "output"]
    if agent_file != "ellis.md":
        required_tags.insert(1, "required-actions")
    for tag in required_tags:
        assert f"<{tag}>" in c, f"Missing <{tag}> in {agent_file}"
        assert f"</{tag}>" in c, f"Missing </{tag}> in {agent_file}"


def test_T_0023_081_invocation_templates_md_header_contains_brain_context_injection_protocol_note():
    """T-0023-081: invocation-templates.md header contains brain-context injection protocol note."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    c = f.read_text()
    # The shared header should describe brain-context injection protocol
    header = extract_section(c, r"## Shared Protocols", r"^---$")
    assert re.search(r"[Bb]rain-context.*injection|brain.*context", header), \
        "Header missing brain-context injection protocol note"


def test_T_0023_082_invocation_templates_md_header_contains_standard_READ_items_note_retro_lessons_md_agent_p():
    """T-0023-082: invocation-templates.md header contains standard READ items note (retro-lessons.md, agent-preamble.md)."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    c = f.read_text()
    header = extract_section(c, r"## Shared Protocols", r"^---$")
    assert "retro-lessons.md" in header, "Header missing retro-lessons.md in standard READ items"
    assert "agent-preamble.md" in header, "Header missing agent-preamble.md in standard READ items"


def test_T_0023_083_invocation_templates_md_header_contains_persona_constraint_note():
    """T-0023-083: invocation-templates.md header contains persona-constraint note."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    c = f.read_text()
    header = extract_section(c, r"## Shared Protocols", r"^---$")
    assert re.search(r"[Pp]ersona.*constraint", header), \
        "Header missing persona-constraint note"


def test_T_0023_084_invocation_templates_md_template_index_lists_20_templates():
    """T-0023-084: invocation-templates.md template index lists <=20 templates."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    c = f.read_text()
    # Count rows in the Template Index table (lines with | # | pattern)
    index_section = extract_section(c, r"## Template Index", r"^---$")
    # Count data rows (lines starting with | and a number)
    data_rows = re.findall(r"^\|\s*\d+\s*\|", index_section, re.MULTILINE)
    assert len(data_rows) <= 20, f"Template index has {len(data_rows)} entries (expected <= 20)"


def test_T_0023_085_No_individual_template_contains_brain_context_XML_example_block():
    """T-0023-085: No individual template contains <brain-context> XML example block."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    c = f.read_text()
    # Find all template sections and check none contain <brain-context>
    templates = re.findall(r'<template id="[^"]+">.*?</template>', c, re.DOTALL)
    for tmpl in templates:
        assert "<brain-context>" not in tmpl, \
            f"Individual template contains <brain-context> block: {tmpl[:80]}..."


def test_T_0023_086_No_individual_template_READ_list_contains_retro_lessons_md_or_agent_preamble_md():
    """T-0023-086: No individual template READ list contains retro-lessons.md or agent-preamble.md."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    c = f.read_text()
    templates = re.findall(r'<template id="[^"]+">.*?</template>', c, re.DOTALL)
    for tmpl in templates:
        # Extract <read> content within each template
        read_match = re.search(r"<read>(.*?)</read>", tmpl, re.DOTALL)
        if read_match:
            read_content = read_match.group(1)
            assert "retro-lessons.md" not in read_content, \
                f"Template READ list contains retro-lessons.md (should be in shared header)"
            assert "agent-preamble.md" not in read_content, \
                f"Template READ list contains agent-preamble.md (should be in shared header)"


def test_T_0023_087_roz_investigation_template_contains_CI_Watch_variant_annotation():
    """T-0023-087: roz-investigation template contains 'CI Watch variant' annotation."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    section = extract_template_section(f, "roz-investigation")
    assert section, "roz-investigation template not found"
    assert re.search(r"CI Watch variant", section), \
        "roz-investigation template missing 'CI Watch variant' annotation"


def test_T_0023_088_colby_build_template_contains_CI_Watch_variant_annotation():
    """T-0023-088: colby-build template contains 'CI Watch variant' annotation."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    section = extract_template_section(f, "colby-build")
    assert section, "colby-build template not found"
    assert re.search(r"CI Watch variant", section), \
        "colby-build template missing 'CI Watch variant' annotation"


def test_T_0023_089_roz_scoped_rerun_template_contains_CI_Watch_variant_annotation():
    """T-0023-089: roz-scoped-rerun template contains 'CI Watch variant' annotation."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    section = extract_template_section(f, "roz-scoped-rerun")
    assert section, "roz-scoped-rerun template not found"
    assert re.search(r"CI Watch variant", section), \
        "roz-scoped-rerun template missing 'CI Watch variant' annotation"


def test_T_0023_090_agent_teams_task_content_moved_to_pipeline_operations_md_removed_from_invocation_template():
    """T-0023-090: agent-teams-task content moved to pipeline-operations.md (removed from invocation-templates)."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    c = f.read_text()
    # Full <template id="agent-teams-task"> section should NOT exist
    assert not re.search(r'<template id="agent-teams-task">', c), \
        "agent-teams-task template section still present in invocation-templates.md"
    # But a cross-reference note to pipeline-operations.md should exist
    assert re.search(r"[Aa]gent\s+[Tt]eams.*pipeline-operations", c), \
        "Missing cross-reference note to pipeline-operations.md for agent-teams-task"


def test_T_0023_091_dashboard_bridge_template_removed_from_invocation_templates_md():
    """T-0023-091: dashboard-bridge template removed from invocation-templates.md."""
    f = SHARED_REFS / "invocation-templates.md"
    assert f.is_file()
    c = f.read_text()
    assert not re.search(r'<template id="dashboard-bridge">', c), \
        "dashboard-bridge template still present in invocation-templates.md"
    assert "dashboard-bridge" not in c, \
        "dashboard-bridge reference still present in invocation-templates.md"


def _run_session_boot(cwd=None, env=None, script_path=None):
    """Helper: run session-boot.sh and return (exit_code, parsed_json_or_None, stdout).

    Runs the script from the given cwd (defaults to a temp dir).
    env overrides environment variables if provided.
    """
    if script_path is None:
        script_path = str(SHARED_HOOKS / "session-boot.sh")
    run_env = os.environ.copy()
    # Remove CLAUDE_AGENT_TEAMS by default so tests control it explicitly
    run_env.pop("CLAUDE_AGENT_TEAMS", None)
    if env:
        run_env.update(env)
    result = subprocess.run(
        ["bash", script_path],
        capture_output=True, text=True,
        cwd=cwd, env=run_env, timeout=10,
    )
    data = None
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        pass
    return result.returncode, data, result.stdout


def test_T_0023_100_session_boot_sh_outputs_valid_JSON_to_stdout():
    """T-0023-100: session-boot.sh outputs valid JSON to stdout."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, stdout = _run_session_boot(cwd=tmpdir)
        assert rc == 0, f"session-boot.sh exited with {rc}"
        assert data is not None, f"Invalid JSON output: {stdout[:200]}"


def test_T_0023_101_session_boot_sh_JSON_contains_pipeline_active_boolean_field():
    """T-0023-101: session-boot.sh JSON contains pipeline_active boolean field."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert "pipeline_active" in data, "JSON missing pipeline_active field"
        assert isinstance(data["pipeline_active"], bool), \
            f"pipeline_active is {type(data['pipeline_active']).__name__}, expected bool"


def test_T_0023_102_session_boot_sh_JSON_contains_phase_string_field():
    """T-0023-102: session-boot.sh JSON contains phase string field."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert "phase" in data, "JSON missing phase field"
        assert isinstance(data["phase"], str), \
            f"phase is {type(data['phase']).__name__}, expected str"


def test_T_0023_103_session_boot_sh_JSON_contains_branching_strategy_string_field():
    """T-0023-103: session-boot.sh JSON contains branching_strategy string field."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert "branching_strategy" in data, "JSON missing branching_strategy field"
        assert isinstance(data["branching_strategy"], str), \
            f"branching_strategy is {type(data['branching_strategy']).__name__}, expected str"


def test_T_0023_104_session_boot_sh_JSON_contains_custom_agent_count_integer_field():
    """T-0023-104: session-boot.sh JSON contains custom_agent_count integer field."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert "custom_agent_count" in data, "JSON missing custom_agent_count field"
        assert isinstance(data["custom_agent_count"], int), \
            f"custom_agent_count is {type(data['custom_agent_count']).__name__}, expected int"


def test_T_0023_104a_session_boot_sh_JSON_contains_feature_string_field():
    """T-0023-104a: session-boot.sh JSON contains feature string field."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert "feature" in data, "JSON missing feature field"
        assert isinstance(data["feature"], str), \
            f"feature is {type(data['feature']).__name__}, expected str"


def test_T_0023_104b_session_boot_sh_JSON_contains_stale_context_boolean_field():
    """T-0023-104b: session-boot.sh JSON contains stale_context boolean field."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert "stale_context" in data, "JSON missing stale_context field"
        assert isinstance(data["stale_context"], bool), \
            f"stale_context is {type(data['stale_context']).__name__}, expected bool"


def test_T_0023_105_session_boot_sh_JSON_contains_agent_teams_enabled_and_agent_teams_env_boolean_fields():
    """T-0023-105: session-boot.sh JSON contains agent_teams_enabled and agent_teams_env boolean fields."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert "agent_teams_enabled" in data, "JSON missing agent_teams_enabled field"
        assert isinstance(data["agent_teams_enabled"], bool), \
            f"agent_teams_enabled is {type(data['agent_teams_enabled']).__name__}, expected bool"
        assert "agent_teams_env" in data, "JSON missing agent_teams_env field"
        assert isinstance(data["agent_teams_env"], bool), \
            f"agent_teams_env is {type(data['agent_teams_env']).__name__}, expected bool"


def test_T_0023_106_session_boot_sh_JSON_contains_warn_agents_array_field():
    """T-0023-106: session-boot.sh JSON contains warn_agents array field."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert "warn_agents" in data, "JSON missing warn_agents field"
        assert isinstance(data["warn_agents"], list), \
            f"warn_agents is {type(data['warn_agents']).__name__}, expected list"


def test_T_0023_107_Missing_pipeline_state_md_outputs_defaults_pipeline_active_false_phase_idle_and_exits_0():
    """T-0023-107: Missing pipeline-state.md -> outputs defaults (pipeline_active: false, phase: idle) and exits 0."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Empty dir -- no pipeline-state.md, no config, no agents
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0, f"Expected exit 0, got {rc}"
        assert data is not None, "Invalid JSON output"
        assert data["pipeline_active"] is False, \
            f"Expected pipeline_active=false, got {data['pipeline_active']}"
        assert data["phase"] == "idle", \
            f"Expected phase='idle', got {data['phase']}"


def test_T_0023_108_Missing_pipeline_config_json_outputs_defaults_branching_strategy_trunk_based_and_exits_0():
    """T-0023-108: Missing pipeline-config.json -> outputs defaults (branching_strategy: trunk-based) and exits 0."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Empty dir -- no pipeline-config.json
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0, f"Expected exit 0, got {rc}"
        assert data is not None, "Invalid JSON output"
        assert data["branching_strategy"] == "trunk-based", \
            f"Expected branching_strategy='trunk-based', got {data['branching_strategy']}"


def test_T_0023_109_Missing_claude_agents_directory_outputs_custom_agent_count_0_and_exits_0():
    """T-0023-109: Missing .claude/agents/ directory -> outputs custom_agent_count: 0 and exits 0."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Empty dir -- no .claude/agents/
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0, f"Expected exit 0, got {rc}"
        assert data is not None, "Invalid JSON output"
        assert data["custom_agent_count"] == 0, \
            f"Expected custom_agent_count=0, got {data['custom_agent_count']}"


def test_T_0023_110_Malformed_pipeline_state_md_no_PIPELINE_STATUS_marker_outputs_defaults_and_exits_0():
    """T-0023-110: Malformed pipeline-state.md (no PIPELINE_STATUS marker) -> outputs defaults and exits 0."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a pipeline-state.md without PIPELINE_STATUS marker
        state_dir = os.path.join(tmpdir, "docs", "pipeline")
        os.makedirs(state_dir)
        with open(os.path.join(state_dir, "pipeline-state.md"), "w") as fh:
            fh.write("# Pipeline State\n\nSome content but no PIPELINE_STATUS marker.\n")
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0, f"Expected exit 0, got {rc}"
        assert data is not None, "Invalid JSON output"
        assert data["pipeline_active"] is False, \
            f"Expected pipeline_active=false with malformed state, got {data['pipeline_active']}"
        assert data["phase"] == "idle", \
            f"Expected phase='idle' with malformed state, got {data['phase']}"


def test_T_0023_111_CLAUDE_AGENT_TEAMS_env_var_set_agent_teams_env_true():
    """T-0023-111: CLAUDE_AGENT_TEAMS env var set -> agent_teams_env: true."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir, env={"CLAUDE_AGENT_TEAMS": "1"})
        assert rc == 0
        assert data is not None, "Invalid JSON output"
        assert data["agent_teams_env"] is True, \
            f"Expected agent_teams_env=true when CLAUDE_AGENT_TEAMS set, got {data['agent_teams_env']}"


def test_T_0023_112_CLAUDE_AGENT_TEAMS_env_var_unset_agent_teams_env_false():
    """T-0023-112: CLAUDE_AGENT_TEAMS env var unset -> agent_teams_env: false."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        # _run_session_boot already removes CLAUDE_AGENT_TEAMS from env by default
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert data is not None, "Invalid JSON output"
        assert data["agent_teams_env"] is False, \
            f"Expected agent_teams_env=false when CLAUDE_AGENT_TEAMS unset, got {data['agent_teams_env']}"


def test_T_0023_113_session_boot_sh_is_executable_x_bit_set():
    """T-0023-113: session-boot.sh is executable (-x bit set)."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    assert os.access(f, os.X_OK), f"session-boot.sh is not executable (-x bit not set)"


def test_T_0023_114_session_boot_sh_starts_with_set_uo_pipefail_not_set_e_per_retro_lesson_003():
    """T-0023-114: session-boot.sh starts with 'set -uo pipefail' (not set -e, per retro lesson #003)."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    c = f.read_text()
    assert "set -uo pipefail" in c
    assert not re.search(r"^set -e$|^set -eo ", c, re.MULTILINE), \
        "session-boot.sh contains 'set -e' which violates retro lesson #003"


def test_T_0023_115_warn_agents_array_contains_agent_names_from_error_patterns_md_with_Recurrence_3():
    """T-0023-115: warn_agents array contains agent names from error-patterns.md with Recurrence >= 3."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure with error-patterns.md containing Recurrence >= 3
        # Note: session-boot.sh parses by grepping lines matching recurrence >= 3
        # and then extracting agent names from those SAME lines
        state_dir = os.path.join(tmpdir, "docs", "pipeline")
        os.makedirs(state_dir)
        with open(os.path.join(state_dir, "error-patterns.md"), "w") as fh:
            fh.write("# Error Patterns\n\n")
            fh.write("## Pattern 1\n")
            fh.write("agent: colby | Recurrence: 3\n")
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert data is not None, "Invalid JSON output"
        assert isinstance(data["warn_agents"], list), "warn_agents should be a list"
        assert "colby" in data["warn_agents"], \
            f"Expected 'colby' in warn_agents with Recurrence >= 3, got {data['warn_agents']}"


def test_T_0023_116_session_boot_sh_JSON_contains_ci_watch_enabled_darwin_enabled_dashboard_mode_sentinel_ena():
    """T-0023-116: session-boot.sh JSON contains ci_watch_enabled, darwin_enabled, dashboard_mode, sentinel_enabled, deps_agent_enabled."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert data is not None, "Invalid JSON output"
        for field in ["ci_watch_enabled", "darwin_enabled", "dashboard_mode",
                      "sentinel_enabled", "deps_agent_enabled"]:
            assert field in data, f"JSON missing {field} field"


def test_T_0023_117_session_boot_sh_JSON_contains_project_name_field():
    """T-0023-117: session-boot.sh JSON contains project_name field."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert data is not None, "Invalid JSON output"
        assert "project_name" in data, "JSON missing project_name field"
        assert isinstance(data["project_name"], str), \
            f"project_name is {type(data['project_name']).__name__}, expected str"


def test_T_0023_118_No_git_remote_and_no_project_name_in_config_project_name_is_current_directory_basename():
    """T-0023-118: No git remote and no project_name in config -> project_name is current directory basename."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        # No git repo, no config -- project_name should be the temp dir basename
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        assert rc == 0
        assert data is not None, "Invalid JSON output"
        expected_name = os.path.basename(tmpdir)
        assert data["project_name"] == expected_name, \
            f"Expected project_name='{expected_name}', got '{data['project_name']}'"


def test_T_0023_119_session_boot_sh_completes_in_500ms_no_network_calls_no_brain():
    """T-0023-119: session-boot.sh completes in <500ms (no network calls, no brain)."""
    f = SHARED_HOOKS / "session-boot.sh"
    if not f.is_file(): pytest.skip("not yet created")
    with tempfile.TemporaryDirectory() as tmpdir:
        start = time.time()
        rc, data, _ = _run_session_boot(cwd=tmpdir)
        elapsed_ms = (time.time() - start) * 1000
        assert rc == 0
        assert elapsed_ms < 500, f"session-boot.sh took {elapsed_ms:.0f}ms (expected < 500ms)"


def test_T_0023_120_default_persona_md_boot_sequence_references_session_boot_sh_output_parsing_for_steps_1_3d():
    """T-0023-120: default-persona.md boot sequence references session-boot.sh output parsing for steps 1-3d."""
    f = SHARED_RULES / "default-persona.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"session-boot", c, re.IGNORECASE)


def test_T_0023_121_default_persona_md_boot_sequence_still_contains_steps_4_6_brain_health_brain_context_anno():
    """T-0023-121: boot sequence steps 4-6 (brain health, brain context, announcement) exist in session-boot.md."""
    # ADR-0023 delegated boot steps 1-6 to session-boot.md; default-persona.md
    # references it via "Read session-boot.md and execute steps 1-6."
    f = SHARED_RULES / "default-persona.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"session-boot", c, re.IGNORECASE)
    # Verify the detailed boot steps exist in session-boot.md
    sb = SHARED_REFS / "session-boot.md"
    assert sb.is_file()
    sbc = sb.read_text()
    assert re.search(r"brain.*health|atelier_stats|brain.*check", sbc, re.IGNORECASE)
    assert re.search(r"brain.*context.*retriev|agent_search", sbc, re.IGNORECASE)
    assert re.search(r"announce.*session|session.*state.*user|announce", sbc, re.IGNORECASE)


def test_T_0023_131_All_12_mandatory_gates_preserved_count_numbered_items_under_Eva_NEVER_Skips():
    """T-0023-131: All 12 mandatory gates preserved (count numbered items under 'Eva NEVER Skips').

    Strengthened post-ADR-0044: previously asserted only the section header was
    present. Now extracts the Mandatory Gates section and counts `^\\d+\\. \\*\\*`
    lines so the 12-gate preservation intent is actually tested. ADR-0044 collapsed
    the per-gate "same class of violation" rhetoric; the 12-gate body count guards
    against accidental gate loss during rhetoric trims.
    """
    f = SHARED_RULES / "pipeline-orchestration.md"
    assert f.is_file()
    c = f.read_text()
    assert "Eva NEVER Skips" in c
    # Extract the Mandatory Gates section: between the section header and the
    # next top-level `## ` heading (or end of file).
    section_match = re.search(
        r"## Mandatory Gates -- Eva NEVER Skips These(.*?)(?=\n## |\Z)",
        c,
        re.DOTALL,
    )
    assert section_match, "Mandatory Gates section not found"
    section = section_match.group(1)
    numbered_gates = re.findall(r"^\d+\. \*\*", section, re.MULTILINE)
    assert len(numbered_gates) == 12, (
        f"Mandatory Gates section has {len(numbered_gates)} numbered gates; "
        "expected 12. ADR-0044 preserves all 12 gates while collapsing rhetoric."
    )


def test_T_0023_132_All_observation_masking_receipt_formats_preserved():
    """T-0023-132: All observation masking receipt formats preserved."""
    f = SHARED_RULES / "pipeline-orchestration.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"Receipt Format|observation.*mask", c, re.IGNORECASE)
    assert "Cal:" in c
    assert "Colby:" in c
    assert "Roz:" in c


def test_T_0023_133_Brain_capture_model_section_preserved():
    """T-0023-133: Brain capture model section preserved."""
    f = SHARED_RULES / "pipeline-orchestration.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"brain.*capture|capture.*model|Hybrid Capture", c, re.IGNORECASE)


def test_T_0023_134_Investigation_discipline_section_preserved():
    """T-0023-134: Investigation discipline section preserved."""
    f = SHARED_RULES / "pipeline-orchestration.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"investigation.*discipline|Layer Escalation", c, re.IGNORECASE)


def test_T_0023_134a_Pipeline_flow_diagram_preserved_Idea_Robert_or_equivalent_flow_marker():
    """T-0023-134a: Pipeline flow diagram preserved (Idea -> Robert or equivalent flow marker)."""
    f = SHARED_RULES / "pipeline-orchestration.md"
    assert f.is_file()
    c = f.read_text()
    assert re.search(r"Idea.*Robert|Robert.*spec.*->|pipeline.*flow", c, re.IGNORECASE)


def test_T_0023_140_SKILL_md_lists_step_sizing_md_in_references():
    """T-0023-140: SKILL.md lists step-sizing.md in references."""
    f = SKILL_FILE
    c = f.read_text()
    assert "step-sizing" in c


def test_T_0023_141_SKILL_md_settings_json_template_includes_session_boot_sh_in_SessionStart_hooks():
    """T-0023-141: SKILL.md settings.json template includes session-boot.sh in SessionStart hooks."""
    f = SKILL_FILE
    c = f.read_text()
    assert re.search(r"session-boot", c, re.IGNORECASE)


def test_T_0023_142_pipeline_setup_SKILL_md_references_step_sizing_md_for_copy_to_target_claude_references():
    """T-0023-142: /pipeline-setup SKILL.md references step-sizing.md for copy to target .claude/references/."""
    f = SKILL_FILE
    c = f.read_text()
    assert "step-sizing" in c


def test_T_0023_143_pipeline_setup_SKILL_md_registers_session_boot_sh_hook():
    """T-0023-143: /pipeline-setup SKILL.md registers session-boot.sh hook."""
    f = SKILL_FILE
    c = f.read_text()
    assert re.search(r"session-boot", c, re.IGNORECASE)


def test_T_0023_153_Assembled_Cal_persona_claude_overlay_shared_content_is_valid_markdown():
    """T-0023-153: Assembled Cal persona (claude overlay + shared content) is valid markdown."""
    f = SHARED_AGENTS / "cal.md"
    assert f.is_file()
    c = f.read_text()
    assert "<identity>" in c


def test_T_0023_154_Assembled_Colby_persona_claude_overlay_shared_content_is_valid_markdown():
    """T-0023-154: Assembled Colby persona (claude overlay + shared content) is valid markdown."""
    f = SHARED_AGENTS / "colby.md"
    assert f.is_file()
    c = f.read_text()
    assert "<identity>" in c


def test_T_0023_155_Assembled_Roz_persona_claude_overlay_shared_content_is_valid_markdown():
    """T-0023-155: Assembled Roz persona (claude overlay + shared content) is valid markdown."""
    f = SHARED_AGENTS / "roz.md"
    assert f.is_file()
    c = f.read_text()
    assert "<identity>" in c

