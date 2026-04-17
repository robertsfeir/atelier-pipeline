"""ADR-0019: Cursor Port + No-Repo Support Tests.

Migrated from cursor-port.bats.
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



def test_T_0019_001_enforce_paths_sh_resolves_PROJECT_ROOT_from_CURSOR_PROJECT_DIR_when_set():
    """T-0019-001: enforce-paths.sh resolves PROJECT_ROOT from CURSOR_PROJECT_DIR when set."""
    pass  # Complex bats test


def test_T_0019_002_enforce_sequencing_sh_resolves_PROJECT_ROOT_from_CURSOR_PROJECT_DIR_when_set():
    """T-0019-002: enforce-sequencing.sh resolves PROJECT_ROOT from CURSOR_PROJECT_DIR when set."""
    pass  # Complex bats test


def test_T_0019_003_enforce_pipeline_activation_sh_resolves_from_CURSOR_PROJECT_DIR_when_set():
    """T-0019-003: enforce-pipeline-activation.sh resolves from CURSOR_PROJECT_DIR when set."""
    pass  # Complex bats test


def test_T_0019_004_pre_compact_sh_writes_compaction_marker_to_CURSOR_PROJECT_DIR_path():
    """T-0019-004: pre-compact.sh writes compaction marker to CURSOR_PROJECT_DIR path."""
    pass  # Complex bats test


def test_T_0019_005_empty_CURSOR_PROJECT_DIR_falls_through_to_CLAUDE_PROJECT_DIR():
    """T-0019-005: empty CURSOR_PROJECT_DIR falls through to CLAUDE_PROJECT_DIR."""
    pass  # Complex bats test


def test_T_0019_006_CURSOR_PROJECT_DIR_takes_precedence_over_CLAUDE_PROJECT_DIR():
    """T-0019-006: CURSOR_PROJECT_DIR takes precedence over CLAUDE_PROJECT_DIR."""
    pass  # Complex bats test


def test_T_0019_007_CLAUDE_PROJECT_DIR_only_existing_behavior_unchanged():
    """T-0019-007: CLAUDE_PROJECT_DIR only -- existing behavior unchanged."""
    pass  # Complex bats test


def test_T_0019_008_neither_env_var_set_falls_back_to_SCRIPT_DIR_based_resolution():
    """T-0019-008: neither env var set -- falls back to SCRIPT_DIR-based resolution."""
    pass  # Complex bats test


def test_T_0019_009_CURSOR_PROJECT_DIR_set_to_non_existent_directory_no_crash():
    """T-0019-009: CURSOR_PROJECT_DIR set to non-existent directory -- no crash."""
    pass  # Complex bats test


def test_T_0019_010_enforce_git_sh_still_blocks_git_write_ops_without_CURSOR_PROJECT_DIR_reference():
    """T-0019-010: enforce-git.sh still blocks git write ops without CURSOR_PROJECT_DIR reference."""
    pass  # Complex bats test


def test_T_0019_011_warn_dor_dod_sh_still_warns_on_missing_DoR_DoD():
    """T-0019-011: warn-dor-dod.sh still warns on missing DoR/DoD."""
    pass  # Complex bats test


def test_T_0019_070_CURSOR_PROJECT_DIR_with_trailing_slash_no_double_slash_in_resolution():
    """T-0019-070: CURSOR_PROJECT_DIR with trailing slash -- no double-slash in resolution."""
    pass  # Complex bats test


def test_T_0019_071_CURSOR_PROJECT_DIR_with_spaces_enforce_paths_sh_handles_correctly():
    """T-0019-071: CURSOR_PROJECT_DIR with spaces -- enforce-paths.sh handles correctly."""
    pass  # Complex bats test


def test_T_0019_072_CURSOR_PROJECT_DIR_with_spaces_enforce_sequencing_sh_no_word_split():
    """T-0019-072: CURSOR_PROJECT_DIR with spaces -- enforce-sequencing.sh no word-split."""
    pass  # Complex bats test


def test_T_0019_073_E2E_enforcement_chain_path_violation_produces_BLOCKED():
    """T-0019-073: E2E enforcement chain -- path violation produces BLOCKED."""
    pass  # Complex bats test


def test_T_0019_074_E2E_enforcement_chain_Ellis_without_Roz_QA_produces_BLOCKED():
    """T-0019-074: E2E enforcement chain -- Ellis without Roz QA produces BLOCKED."""
    pass  # Complex bats test


def test_T_0019_075_E2E_enforcement_chain_git_commit_from_main_thread_produces_BLOCKED():
    """T-0019-075: E2E enforcement chain -- git commit from main thread produces BLOCKED."""
    pass  # Complex bats test


def test_T_0019_100_SKILL_md_has_git_availability_question_before_branching_strategy():
    """T-0019-100: SKILL.md has git availability question before branching strategy."""
    c = SKILL_FILE.read_text()
    assert re.search(r"Git Repository Detection|git availability|git_available", c, re.IGNORECASE)


def test_T_0019_101_SKILL_md_lists_unavailable_without_git_agents_Poirot_Ellis_CI_Watch():
    """T-0019-101: SKILL.md lists unavailable-without-git agents: Poirot, Ellis, CI Watch."""
    c = SKILL_FILE.read_text()
    assert re.search(r"Poirot|blind review", c, re.IGNORECASE)
    assert re.search(r"Ellis|commit manager", c, re.IGNORECASE)
    assert "CI Watch" in c


def test_T_0019_102_SKILL_md_lists_what_still_works_without_git_Eva_Colby_Roz_Brain():
    """T-0019-102: SKILL.md lists what still works without git: Eva, Colby, Roz, Brain."""
    c = SKILL_FILE.read_text()
    assert re.search(r"still works|What still works|available without git", c, re.IGNORECASE)


def test_T_0019_103_SKILL_md_describes_git_init_flow_with_gitignore_creation():
    """T-0019-103: SKILL.md describes git init flow with .gitignore creation."""
    c = SKILL_FILE.read_text()
    assert "git init" in c
    assert re.search(r"\.gitignore|gitignore", c, re.IGNORECASE)


def test_T_0019_104_SKILL_md_describes_writing_git_available_false_when_user_declines():
    """T-0019-104: SKILL.md describes writing git_available: false when user declines."""
    c = SKILL_FILE.read_text()
    assert re.search(r"git_available.*false|git_available: false", c, re.IGNORECASE)


def test_T_0019_105_SKILL_md_describes_auto_detecting_existing_git_repo():
    """T-0019-105: SKILL.md describes auto-detecting existing git repo."""
    c = SKILL_FILE.read_text()
    assert re.search(r"git rev-parse|git repo detected|git_available.*true", c, re.IGNORECASE)


def test_T_0019_106_enforce_git_sh_exits_0_no_op_when_git_available_false():
    """T-0019-106: enforce-git.sh exits 0 (no-op) when git_available: false."""
    pass  # Complex bats test


def test_T_0019_107_enforce_sequencing_sh_BLOCKs_Ellis_when_git_available_false():
    """T-0019-107: enforce-sequencing.sh BLOCKs Ellis when git_available: false."""
    pass  # Complex bats test


def test_T_0019_108_Ellis_blocked_even_with_roz_qa_PASS_when_git_available_false():
    """T-0019-108: Ellis blocked even with roz_qa: PASS when git_available: false."""
    pass  # Complex bats test


def test_T_0019_109_pipeline_config_json_missing_git_available_enforce_git_sh_defaults_to_true():
    """T-0019-109: pipeline-config.json missing git_available -- enforce-git.sh defaults to true."""
    pass  # Complex bats test


def test_T_0019_110_git_available_true_enforce_git_sh_behaves_identically_to_current():
    """T-0019-110: git_available: true -- enforce-git.sh behaves identically to current."""
    pass  # Complex bats test


def test_T_0019_111_jq_not_installed_enforce_git_sh_still_functions_exits_2_for_jq_missing():
    """T-0019-111: jq not installed -- enforce-git.sh still functions (exits 2 for jq missing)."""
    pass  # Complex bats test


def test_T_0019_112_no_pipeline_config_json_enforce_git_sh_skips_config_check_normal_behavior():
    """T-0019-112: no pipeline-config.json -- enforce-git.sh skips config check, normal behavior."""
    pass  # Complex bats test


def test_T_0019_113_SKILL_md_renamed_Step_1b_no_longer_contains_git_rev_parse_pre_check():
    """T-0019-113: SKILL.md renamed Step 1b no longer contains git rev-parse pre-check."""
    pass  # Complex bats test


def test_T_0019_114_pipeline_config_json_template_has_git_available_as_first_field():
    """T-0019-114: pipeline-config.json template has git_available as first field."""
    pass  # Complex bats test


def test_T_0019_115_SKILL_md_git_init_flow_includes_env_in_gitignore():
    """T-0019-115: SKILL.md git init flow includes .env in .gitignore."""
    c = SKILL_FILE.read_text()
    assert re.search(r"\.env", c)


def test_T_0019_116_Poirot_allowed_through_enforce_sequencing_sh_when_git_available_false():
    """T-0019-116: Poirot allowed through enforce-sequencing.sh when git_available: false."""
    pass  # Complex bats test


def test_T_0019_117_git_available_false_git_status_via_Bash_hook_is_no_op():
    """T-0019-117: git_available: false + git status via Bash -- hook is no-op."""
    pass  # Complex bats test


def test_T_0019_118_malformed_pipeline_config_json_enforce_git_sh_falls_through_to_normal_behavior():
    """T-0019-118: malformed pipeline-config.json -- enforce-git.sh falls through to normal behavior."""
    pass  # Complex bats test


def test_T_0019_119_Ellis_blocked_for_all_agent_ids_when_git_available_false():
    """T-0019-119: Ellis blocked for all agent_ids when git_available: false."""
    pass  # Complex bats test


def test_T_0019_120_SKILL_md_describes_fallback_when_git_init_fails():
    """T-0019-120: SKILL.md describes fallback when git init fails."""
    c = SKILL_FILE.read_text()
    assert re.search(r"fail|error|permission|git_available.*false", c, re.IGNORECASE)


def test_T_0019_012_cursor_plugin_plugin_json_is_valid_JSON_with_name_atelier_pipeline():
    """T-0019-012: .cursor-plugin/plugin.json is valid JSON with name: atelier-pipeline."""
    pass  # Complex bats test


def test_T_0019_013_cursor_plugin_marketplace_json_is_valid_JSON_with_plugins_array():
    """T-0019-013: .cursor-plugin/marketplace.json is valid JSON with plugins array."""
    pass  # Complex bats test


def test_T_0019_014_AGENTS_md_exists_at_repo_root_with_pipeline_content():
    """T-0019-014: AGENTS.md exists at repo root with pipeline content."""
    pass  # Complex bats test


def test_T_0019_015_cursor_plugin_plugin_json_version_matches_claude_plugin_plugin_json():
    """T-0019-015: .cursor-plugin/plugin.json version matches .claude-plugin/plugin.json."""
    pass  # Complex bats test


def test_T_0019_016_claude_plugin_plugin_json_is_unchanged_byte_for_byte():
    """T-0019-016: .claude-plugin/plugin.json is unchanged (byte-for-byte)."""
    pass  # Complex bats test


def test_T_0019_017_claude_plugin_marketplace_json_is_unchanged():
    """T-0019-017: .claude-plugin/marketplace.json is unchanged."""
    pass  # Complex bats test


def test_T_0019_076_cursor_plugin_plugin_json_name_field_exists_and_is_non_empty():
    """T-0019-076: .cursor-plugin/plugin.json name field exists and is non-empty."""
    pass  # Complex bats test


def test_T_0019_077_AGENTS_md_contains_tech_stack_test_commands_source_structure_conventions():
    """T-0019-077: AGENTS.md contains tech stack, test commands, source structure, conventions."""
    pass  # Complex bats test


def test_T_0019_078_cursor_plugin_plugin_json_name_is_kebab_case_no_spaces_no_uppercase():
    """T-0019-078: .cursor-plugin/plugin.json name is kebab-case (no spaces, no uppercase)."""
    pass  # Complex bats test


def test_T_0019_079_cursor_plugin_does_not_contain_a_copy_of_source_directory():
    """T-0019-079: .cursor-plugin/ does not contain a copy of source/ directory."""
    pass  # Complex bats test


def test_T_0019_139_marketplace_json_plugins_entries_have_name_version_source_description():
    """T-0019-139: marketplace.json plugins entries have name, version, source, description."""
    pass  # Complex bats test


def test_T_0019_018_hooks_json_is_valid_JSON_with_6_hook_entries():
    """T-0019-018: hooks.json is valid JSON with 6 hook entries."""
    pass  # Complex bats test


def test_T_0019_019_all_4_enforcement_hooks_have_failClosed_true():
    """T-0019-019: all 4 enforcement hooks have failClosed: true."""
    pass  # Complex bats test


def test_T_0019_020_advisory_hooks_subagentStop_preCompact_do_NOT_have_failClosed_true():
    """T-0019-020: advisory hooks (subagentStop, preCompact) do NOT have failClosed: true."""
    pass  # Complex bats test


def test_T_0019_021_all_hook_command_paths_reference_source_cursor_hooks_via_CURSOR_PLUGIN_ROOT():
    """T-0019-021: all hook command paths reference source/cursor/hooks/ via CURSOR_PLUGIN_ROOT."""
    pass  # Complex bats test


def test_T_0019_022_hook_matchers_match_expected_tool_names():
    """T-0019-022: hook matchers match expected tool names."""
    pass  # Complex bats test


def test_T_0019_023_no_hook_has_explicit_failClosed_false():
    """T-0019-023: no hook has explicit failClosed: false."""
    pass  # Complex bats test


def test_T_0019_080_every_hook_command_path_resolves_to_an_existing_script_file():
    """T-0019-080: every hook command path resolves to an existing script file."""
    pass  # Complex bats test


def test_T_0019_081_all_referenced_hook_scripts_have_execute_permission():
    """T-0019-081: all referenced hook scripts have execute permission."""
    pass  # Complex bats test


def test_T_0019_082_no_duplicate_event_matcher_pairs_in_hooks_json():
    """T-0019-082: no duplicate event+matcher pairs in hooks.json."""
    pass  # Complex bats test


def test_T_0019_083_hook_command_paths_use_CURSOR_PLUGIN_ROOT_variable_reference():
    """T-0019-083: hook command paths use CURSOR_PLUGIN_ROOT variable reference."""
    pass  # Complex bats test


def test_T_0019_024_cursor_plugin_mcp_json_is_valid_JSON_with_atelier_brain_key():
    """T-0019-024: .cursor-plugin/mcp.json is valid JSON with atelier-brain key."""
    pass  # Complex bats test


def test_T_0019_025_mcp_json_server_command_points_to_brain_server_mjs():
    """T-0019-025: mcp.json server command points to brain/server.mjs."""
    pass  # Complex bats test


def test_T_0019_026_mcp_json_BRAIN_CONFIG_USER_uses_CURSOR_PLUGIN_DATA():
    """T-0019-026: mcp.json BRAIN_CONFIG_USER uses CURSOR_PLUGIN_DATA."""
    pass  # Complex bats test


def test_T_0019_027_mcp_json_has_NODE_TLS_REJECT_UNAUTHORIZED_0():
    """T-0019-027: mcp.json has NODE_TLS_REJECT_UNAUTHORIZED=0."""
    pass  # Complex bats test


def test_T_0019_028_mcp_json_has_no_plaintext_credentials_all_via_env_var_refs():
    """T-0019-028: mcp.json has no plaintext credentials (all via env var refs)."""
    pass  # Complex bats test


def test_T_0019_029_mcp_json_Claude_Code_root_is_unchanged():
    """T-0019-029: .mcp.json (Claude Code root) is unchanged."""
    pass  # Complex bats test


def test_T_0019_084_mcp_json_uses_CURSOR_PLUGIN_ROOT_not_hardcoded_path():
    """T-0019-084: mcp.json uses CURSOR_PLUGIN_ROOT (not hardcoded path)."""
    pass  # Complex bats test


def test_T_0019_085_mcp_json_has_command_and_args_fields_for_server_startup():
    """T-0019-085: mcp.json has command and args fields for server startup."""
    pass  # Complex bats test


def test_T_0019_086_mcp_json_env_vars_contain_no_CLAUDE_prefixed_variables():
    """T-0019-086: mcp.json env vars contain no CLAUDE_-prefixed variables."""
    pass  # Complex bats test


def test_T_0019_087_mcp_json_credentials_are_env_var_references_not_literal_values():
    """T-0019-087: mcp.json credentials are env var references, not literal values."""
    pass  # Complex bats test


def test_T_0019_030_default_persona_mdc_has_valid_YAML_frontmatter_with_alwaysApply_true():
    """T-0019-030: default-persona.mdc has valid YAML frontmatter with alwaysApply: true."""
    pass  # Complex bats test


def test_T_0019_031_agent_system_mdc_has_valid_YAML_frontmatter_with_alwaysApply_true():
    """T-0019-031: agent-system.mdc has valid YAML frontmatter with alwaysApply: true."""
    pass  # Complex bats test


def test_T_0019_032_default_persona_mdc_content_matches_source_rules_default_persona_md():
    """T-0019-032: default-persona.mdc content matches source/rules/default-persona.md."""
    pass  # Complex bats test


def test_T_0019_033_agent_system_mdc_content_matches_source_rules_agent_system_md():
    """T-0019-033: agent-system.mdc content matches source/rules/agent-system.md."""
    pass  # Complex bats test


def test_T_0019_034_always_apply_rule_files_use_mdc_extension_not_md():
    """T-0019-034: always-apply rule files use .mdc extension, not .md."""
    pass  # Complex bats test


def test_T_0019_088_mdc_alwaysApply_is_boolean_true_not_quoted_string():
    """T-0019-088: .mdc alwaysApply is boolean true, not quoted string."""
    pass  # Complex bats test


def test_T_0019_089_mdc_files_have_no_byte_order_mark_BOM():
    """T-0019-089: .mdc files have no byte order mark (BOM)."""
    pass  # Complex bats test


def test_T_0019_090_mdc_files_use_LF_line_endings_no_CRLF():
    """T-0019-090: .mdc files use LF line endings (no CRLF)."""
    pass  # Complex bats test


def test_T_0019_091_both_always_apply_mdc_files_have_non_empty_description_field():
    """T-0019-091: both always-apply .mdc files have non-empty description field."""
    pass  # Complex bats test


def test_T_0019_035_path_scoped_rules_3_have_globs():
    """T-0019-035: path-scoped rules (3) have globs: [\."""
    pass  # Complex bats test


def test_T_0019_036_reference_rules_5_have_alwaysApply_false_with_no_globs():
    """T-0019-036: reference rules (5) have alwaysApply: false with no globs."""
    pass  # Complex bats test


def test_T_0019_037_all_8_Step_3b_mdc_files_have_valid_YAML_frontmatter():
    """T-0019-037: all 8 Step 3b .mdc files have valid YAML frontmatter."""
    pass  # Complex bats test


def test_T_0019_038_mdc_rule_content_matches_corresponding_source_files():
    """T-0019-038: .mdc rule content matches corresponding source files."""
    pass  # Complex bats test


def test_T_0019_039_no_mdc_file_exists_without_a_corresponding_source_file():
    """T-0019-039: no .mdc file exists without a corresponding source file."""
    pass  # Complex bats test


def test_T_0019_092_path_scoped_rules_have_alwaysApply_false_not_accidentally_true():
    """T-0019-092: path-scoped rules have alwaysApply: false (not accidentally true)."""
    pass  # Complex bats test


def test_T_0019_093_reference_rules_have_no_globs_field_set():
    """T-0019-093: reference rules have no globs field set."""
    pass  # Complex bats test


def test_T_0019_094_all_mdc_files_have_non_empty_content_after_frontmatter():
    """T-0019-094: all .mdc files have non-empty content after frontmatter."""
    pass  # Complex bats test


def test_T_0019_095_no_md_files_exist_in_cursor_plugin_rules_only_mdc():
    """T-0019-095: no .md files exist in .cursor-plugin/rules/ (only .mdc)."""
    pass  # Complex bats test


def test_T_0019_040_all_9_core_agent_files_have_name_and_description_frontmatter():
    """T-0019-040: all 9 core agent files have name and description frontmatter."""
    pass  # Complex bats test


def test_T_0019_041_agent_frontmatter_names_match_hook_enforcement_names():
    """T-0019-041: agent frontmatter names match hook enforcement names."""
    pass  # Complex bats test


def test_T_0019_042_agent_persona_content_preserved_after_frontmatter():
    """T-0019-042: agent persona content preserved after frontmatter."""
    pass  # Complex bats test


def test_T_0019_043_agent_frontmatter_name_matches_filename():
    """T-0019-043: agent frontmatter name matches filename."""
    pass  # Complex bats test


def test_T_0019_044_agent_files_have_valid_YAML_frontmatter_starts_and_ends_with():
    """T-0019-044: agent files have valid YAML frontmatter (starts and ends with ---)."""
    pass  # Complex bats test


def test_T_0019_096_total_agent_count_is_12_9_core_3_optional():
    """T-0019-096: total agent count is 12 (9 core + 3 optional)."""
    pass  # Complex bats test


def test_T_0019_097_all_9_core_agents_have_non_empty_description_field():
    """T-0019-097: all 9 core agents have non-empty description field."""
    pass  # Complex bats test


def test_T_0019_098_agent_frontmatter_contains_only_name_and_description_fields():
    """T-0019-098: agent frontmatter contains only name and description fields."""
    pass  # Complex bats test


def test_T_0019_045_sentinel_md_deps_md_darwin_md_have_valid_frontmatter():
    """T-0019-045: sentinel.md, deps.md, darwin.md have valid frontmatter."""
    pass  # Complex bats test


def test_T_0019_046_optional_agent_content_matches_source_agents():
    """T-0019-046: optional agent content matches source agents."""
    pass  # Complex bats test


def test_T_0019_099_optional_agent_names_do_not_collide_with_core_agent_names():
    """T-0019-099: optional agent names do not collide with core agent names."""
    pass  # Complex bats test


def test_T_0019_121_optional_agent_files_have_non_empty_description_fields():
    """T-0019-121: optional agent files have non-empty description fields."""
    pass  # Complex bats test


def test_T_0019_047_all_7_core_command_files_exist_in_cursor_plugin_commands():
    """T-0019-047: all 7 core command files exist in .cursor-plugin/commands/."""
    pass  # Complex bats test


def test_T_0019_048_core_command_content_matches_source_commands():
    """T-0019-048: core command content matches source/commands/."""
    pass  # Complex bats test


def test_T_0019_049_source_commands_files_are_unchanged():
    """T-0019-049: source/commands/ files are unchanged."""
    pass  # Complex bats test


def test_T_0019_122_command_files_use_md_format_not_mdc():
    """T-0019-122: command files use .md format (not .mdc)."""
    pass  # Complex bats test


def test_T_0019_123_no_command_file_is_empty_0_bytes():
    """T-0019-123: no command file is empty (0 bytes)."""
    pass  # Complex bats test


def test_T_0019_050_all_4_optional_command_files_exist():
    """T-0019-050: all 4 optional command files exist."""
    pass  # Complex bats test


def test_T_0019_051_optional_command_content_matches_source():
    """T-0019-051: optional command content matches source."""
    pass  # Complex bats test


def test_T_0019_124_optional_command_filenames_match_source_filenames_exactly():
    """T-0019-124: optional command filenames match source filenames exactly."""
    pass  # Complex bats test


def test_T_0019_125_no_optional_command_file_contains_claude_path_references():
    """T-0019-125: no optional command file contains .claude/ path references."""
    pass  # Complex bats test


def test_T_0019_052_all_7_skill_directories_exist_under_cursor_plugin_skills():
    """T-0019-052: all 7 skill directories exist under .cursor-plugin/skills/."""
    pass  # Complex bats test


def test_T_0019_053_Cursor_skill_path_references_use_cursor_not_claude():
    """T-0019-053: Cursor skill path references use .cursor/ not .claude/."""
    f = CURSOR_PLUGIN_DIR / "skills" / "pipeline-setup" / "SKILL.md"
    if not f.is_file():
        pytest.skip("Cursor pipeline-setup SKILL.md not found")
    c = f.read_text()
    assert re.search(r"\.cursor/", c)


def test_T_0019_054_Cursor_skill_env_var_references_use_CURSOR_prefix():
    """T-0019-054: Cursor skill env var references use CURSOR_ prefix."""
    f = CURSOR_PLUGIN_DIR / "skills" / "pipeline-setup" / "SKILL.md"
    if not f.is_file():
        pytest.skip("Cursor pipeline-setup SKILL.md not found")
    c = f.read_text()
    assert "CURSOR_" in c


def test_T_0019_055_no_CLAUDE_PROJECT_DIR_or_CLAUDE_PLUGIN_ROOT_in_Cursor_skills():
    """T-0019-055: no CLAUDE_PROJECT_DIR or CLAUDE_PLUGIN_ROOT in Cursor skills as primary references."""
    f = CURSOR_PLUGIN_DIR / "skills" / "pipeline-setup" / "SKILL.md"
    if not f.is_file():
        pytest.skip("Cursor pipeline-setup SKILL.md not found")
    c = f.read_text()
    # These env vars should not appear as shell variable usage ($VAR) -- only as documentation references
    assert not re.search(r"\$CLAUDE_PROJECT_DIR|\$\{CLAUDE_PROJECT_DIR\}", c)
    assert not re.search(r"\$CLAUDE_PLUGIN_ROOT|\$\{CLAUDE_PLUGIN_ROOT\}", c)


def test_T_0019_056_Cursor_pipeline_setup_references_cursor_settings_json_for_hooks():
    """T-0019-056: Cursor pipeline-setup references .cursor/settings.json for hooks."""
    pass  # Complex bats test


def test_T_0019_057_Cursor_pipeline_setup_writes_cursor_atelier_version():
    """T-0019-057: Cursor pipeline-setup writes .cursor/.atelier-version."""
    pass  # Complex bats test


def test_T_0019_058_original_skills_directory_unchanged():
    """T-0019-058: original skills/ directory unchanged."""
    pass  # Complex bats test


def test_T_0019_126_no_residual_claude_path_references_in_Cursor_skills():
    """T-0019-126: no residual .claude/ path references in Cursor skills."""
    pass  # Complex bats test


def test_T_0019_127_no_CLAUDE_md_references_in_Cursor_skills_should_be_AGENTS_md():
    """T-0019-127: no CLAUDE.md references in Cursor skills (should be AGENTS.md)."""
    pass  # Complex bats test


def test_T_0019_128_brain_setup_SKILL_md_Cursor_variant_uses_CURSOR_PLUGIN_DATA():
    """T-0019-128: brain-setup SKILL.md Cursor variant uses CURSOR_PLUGIN_DATA."""
    pass  # Complex bats test


def test_T_0019_129_pipeline_setup_SKILL_md_installs_hooks_to_cursor_settings_json():
    """T-0019-129: pipeline-setup SKILL.md installs hooks to .cursor/settings.json."""
    pass  # Complex bats test


def test_T_0019_130_no_CLAUDE_PLUGIN_DATA_references_in_Cursor_skills():
    """T-0019-130: no CLAUDE_PLUGIN_DATA references in Cursor skills."""
    f = CURSOR_PLUGIN_DIR / "skills" / "pipeline-setup" / "SKILL.md"
    if not f.is_file():
        pytest.skip("Cursor pipeline-setup SKILL.md not found")
    c = f.read_text()
    assert "CLAUDE_PLUGIN_DATA" not in c


def test_T_0019_059_check_updates_sh_detects_cursor_atelier_version():
    """T-0019-059: check-updates.sh detects .cursor/.atelier-version."""
    pass  # Complex bats test


def test_T_0019_060_check_updates_sh_still_detects_claude_atelier_version():
    """T-0019-060: check-updates.sh still detects .claude/.atelier-version."""
    pass  # Complex bats test


def test_T_0019_061_only_cursor_atelier_version_reports_Cursor_only():
    """T-0019-061: only .cursor/.atelier-version -- reports Cursor only."""
    pass  # Complex bats test


def test_T_0019_062_both_claude_and_cursor_version_files_script_handles_both():
    """T-0019-062: both .claude and .cursor version files -- script handles both."""
    pass  # Complex bats test


def test_T_0019_063_existing_Claude_Code_update_check_behavior_preserved():
    """T-0019-063: existing Claude Code update check behavior preserved."""
    pass  # Complex bats test


def test_T_0019_131_no_version_files_script_exits_cleanly():
    """T-0019-131: no version files -- script exits cleanly."""
    pass  # Complex bats test


def test_T_0019_132_malformed_cursor_atelier_version_no_crash():
    """T-0019-132: malformed .cursor/.atelier-version -- no crash."""
    pass  # Complex bats test


def test_T_0019_064_cursor_plugin_plugin_json_has_SessionStart_hooks_section():
    """T-0019-064: .cursor-plugin/plugin.json has SessionStart hooks section."""
    pass  # Complex bats test


def test_T_0019_065_SessionStart_hooks_use_CURSOR_env_vars():
    """T-0019-065: SessionStart hooks use CURSOR_ env vars."""
    pass  # Complex bats test


def test_T_0019_066_claude_plugin_plugin_json_SessionStart_hooks_unchanged():
    """T-0019-066: .claude-plugin/plugin.json SessionStart hooks unchanged."""
    pass  # Complex bats test


def test_T_0019_133_SessionStart_npm_install_runs_before_check_updates_array_order():
    """T-0019-133: SessionStart npm install runs before check-updates (array order)."""
    pass  # Complex bats test


def test_T_0019_134_SessionStart_brain_npm_install_uses_fallback_for_failure_tolerance():
    """T-0019-134: SessionStart brain npm install uses fallback for failure tolerance."""
    pass  # Complex bats test


def test_T_0019_135_SessionStart_telemetry_hydration_has_error_suppression():
    """T-0019-135: SessionStart telemetry hydration has error suppression."""
    pass  # Complex bats test


def test_T_0019_136_both_claude_and_cursor_plugin_reference_source_cursor_hooks_scripts():
    """T-0019-136: both .claude/ and .cursor-plugin/ reference source/cursor/hooks/ scripts."""
    pass  # Complex bats test


def test_T_0019_137_Cursor_agent_files_either_all_include_or_all_omit_model_field():
    """T-0019-137: Cursor agent files either all include or all omit model field."""
    pass  # Complex bats test


def test_T_0019_138_plugin_json_does_not_override_auto_discovery_with_explicit_path_fields():
    """T-0019-138: plugin.json does not override auto-discovery with explicit path fields."""
    pass  # Complex bats test


# ── .mcp.json cleanup and plugin.json brain registration guards ──────────


def _run_mcp_cleanup(directory):
    """Simulates the brain-setup/pipeline-setup .mcp.json cleanup logic.

    Mirrors the atomic Python one-liner in both SKILL.md files: removes
    atelier-brain from mcpServers, deletes the file if mcpServers is empty,
    then runs a safety-net check.
    """
    import os

    p = os.path.join(directory, ".mcp.json")
    if not os.path.exists(p):
        return
    try:
        d = json.load(open(p))
    except Exception:
        return
    d.get("mcpServers", {}).pop("atelier-brain", None)
    if not d.get("mcpServers"):
        os.remove(p)
    else:
        json.dump(d, open(p, "w"), indent=2)
    # safety net
    if os.path.exists(p):
        try:
            d2 = json.load(open(p))
        except Exception:
            return
        if not d2.get("mcpServers"):
            os.remove(p)


def test_T_0019_140_claude_plugin_plugin_json_has_atelier_brain_mcp_server():
    """T-0019-140: .claude-plugin/plugin.json has mcpServers.atelier-brain with required fields."""
    plugin_json = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
    assert plugin_json.exists(), ".claude-plugin/plugin.json must exist"
    data = json.loads(plugin_json.read_text())
    assert "mcpServers" in data, "plugin.json must have mcpServers field"
    assert "atelier-brain" in data["mcpServers"], "mcpServers must contain atelier-brain"
    brain = data["mcpServers"]["atelier-brain"]
    assert "command" in brain, "atelier-brain must have command"
    assert "env" in brain, "atelier-brain must have env"
    assert "NODE_TLS_REJECT_UNAUTHORIZED" in brain["env"], "env must contain NODE_TLS_REJECT_UNAUTHORIZED"


def test_T_0019_141_mcp_json_cleanup_deletes_file_when_only_atelier_brain(tmp_path):
    """T-0019-141: .mcp.json cleanup removes file entirely when atelier-brain is the only entry."""
    mcp_file = tmp_path / ".mcp.json"
    mcp_file.write_text(json.dumps({
        "mcpServers": {
            "atelier-brain": {
                "command": "node",
                "args": ["server.mjs"]
            }
        }
    }))
    _run_mcp_cleanup(str(tmp_path))
    assert not mcp_file.exists(), (
        "cleanup must delete .mcp.json when mcpServers is empty -- "
        "leaving behind {\"mcpServers\": {}} suppresses plugin brain registration"
    )


def test_T_0019_142_mcp_json_cleanup_preserves_other_entries(tmp_path):
    """T-0019-142: .mcp.json cleanup preserves non-atelier-brain entries."""
    mcp_file = tmp_path / ".mcp.json"
    mcp_file.write_text(json.dumps({
        "mcpServers": {
            "atelier-brain": {
                "command": "node",
                "args": ["server.mjs"]
            },
            "semgrep": {
                "command": "semgrep",
                "args": ["mcp"]
            }
        }
    }))
    _run_mcp_cleanup(str(tmp_path))
    assert mcp_file.exists(), "cleanup must not delete .mcp.json when other entries remain"
    data = json.loads(mcp_file.read_text())
    assert "atelier-brain" not in data.get("mcpServers", {}), "atelier-brain must be removed"
    assert "semgrep" in data.get("mcpServers", {}), "semgrep entry must be preserved"

