"""ADR-0005 Step 0: XML Tag Vocabulary Reference.

Tests: T-0005-001 through T-0005-006.
Migrated from step0-schema.test.bats.
"""

import re

from tests.conftest import (
    AGENT_FILES,
    INSTALLED_AGENTS,
    INSTALLED_REFS,
    SOURCE_REFS,
)


# ── T-0005-001: Schema file exists in both trees ─────────────────────

def test_T_0005_001_schema_exists_in_both_trees():
    assert (SOURCE_REFS / "xml-prompt-schema.md").is_file()
    assert (INSTALLED_REFS / "xml-prompt-schema.md").is_file()


# ── T-0005-002: Every tag name used in Steps 1-8 is defined ──────────

def _schema_defines_tag(schema: str, tag: str) -> bool:
    return (f"<{tag}>" in schema or f"`<{tag}>`" in schema or f"`{tag}`" in schema)


def test_T_0005_002_schema_defines_all_persona_file_tags():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    for tag in ["identity", "required-actions", "workflow", "examples", "tools", "constraints", "output"]:
        assert _schema_defines_tag(schema, tag), f"Tag '{tag}' not defined in schema"


def test_T_0005_002b_schema_defines_all_invocation_tags():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    for tag in ["task", "brain-context", "context", "hypotheses", "read", "warn"]:
        assert _schema_defines_tag(schema, tag), f"Tag '{tag}' not defined in schema"


def test_T_0005_002c_schema_defines_all_retro_lessons_tags():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    for tag in ["retro-lessons", "lesson", "what-happened", "root-cause", "rules", "rule"]:
        assert _schema_defines_tag(schema, tag), f"Tag '{tag}' not defined in schema"


def test_T_0005_002d_schema_defines_skill_command_tags():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    for tag in ["required-reading", "behavior"]:
        assert _schema_defines_tag(schema, tag), f"Tag '{tag}' not defined in schema"


def test_T_0005_002e_schema_defines_brain_context_thought_tag():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    assert "thought" in schema


# ── T-0005-003: Schema defines valid values for every attribute ───────

def test_T_0005_003_schema_defines_thought_type_attribute_values():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    for value in ["decision", "pattern", "lesson", "correction", "drift", "insight", "handoff", "rejection", "preference"]:
        assert value in schema, f"Thought type value '{value}' not defined in schema"


def test_T_0005_003b_schema_defines_thought_phase_attribute_values():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    for value in ["design", "build", "qa", "review", "reconciliation", "retro", "handoff"]:
        assert value in schema, f"Phase value '{value}' not defined in schema"


def test_T_0005_003c_schema_defines_lesson_tag_attributes():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    assert re.search(r"\bid\b", schema), "Missing 'id' attribute in schema"
    assert re.search(r"\bagents\b", schema), "Missing 'agents' attribute in schema"


def test_T_0005_003d_schema_defines_rule_tag_agent_attribute():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    assert re.search(r"rule.*agent|agent.*rule", schema, re.IGNORECASE)


def test_T_0005_003e_schema_defines_thought_tag_relevance_attribute():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    assert "relevance" in schema


# ── T-0005-004: No undocumented tags in converted files ──────────────

def test_T_0005_004_no_undocumented_tags_in_agent_files():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    fail = False
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        content = file.read_text()
        tags = set(re.findall(r"<([a-z][a-z-]*)>", content))
        for tag in tags:
            if tag not in schema and f"`<{tag}>`" not in schema and f"<{tag}>" not in schema:
                errors.append(f"Undocumented tag <{tag}> in {f}")
                fail = True
    assert not fail, "\n".join(errors)


# ── T-0005-005: Schema specifies tag ordering rules ──────────────────

def test_T_0005_005_schema_documents_tag_ordering_for_persona_files():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    assert re.search(r"order", schema, re.IGNORECASE)
    assert re.search(r"identity.*first|first.*identity|identity.*required-actions", schema, re.IGNORECASE)


def test_T_0005_005b_schema_documents_tag_ordering_for_invocations():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    assert re.search(r"task.*first|first.*task", schema, re.IGNORECASE) or "<task>" in schema


# ── T-0005-006: Every schema tag appears in at least one converted file

def test_T_0005_006_every_persona_tag_used_in_at_least_one_agent():
    for tag in ["identity", "required-actions", "workflow", "examples", "tools", "constraints", "output"]:
        found = False
        for f in AGENT_FILES:
            file = INSTALLED_AGENTS / f
            if file.is_file() and f"<{tag}>" in file.read_text():
                found = True
                break
        assert found, f"Schema tag <{tag}> not used in any agent file"


def test_T_0005_006b_retro_lessons_tags_used():
    file = INSTALLED_REFS / "retro-lessons.md"
    content = file.read_text()
    for tag in ["retro-lessons", "lesson", "what-happened", "root-cause", "rules", "rule"]:
        assert f"<{tag}" in content, f"Schema tag <{tag}> not used in retro-lessons.md"
