"""ADR-0005 Cross-Step Structural Tests.

Tests: T-0005-120 through T-0005-123.
Migrated from cross-step-structural.test.bats.
"""

import re

from tests.conftest import (
    AGENT_FILES,
    COMMAND_FILES,
    INSTALLED_AGENTS,
    INSTALLED_COMMANDS,
    INSTALLED_REFS,
    PERSONA_TAGS,
    extract_tag_content,
)


# ── T-0005-120 ───────────────────────────────────────────────────────

def test_T_0005_120_every_opening_tag_has_closing_in_agents():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        content = file.read_text()
        tags = set(re.findall(r"<([a-z][a-z-]*)>", content))
        for tag in tags:
            if f"</{tag}>" not in content:
                errors.append(f"Unclosed tag <{tag}> in {f}")
    assert not errors, "\n".join(errors)


def test_T_0005_120b_every_opening_tag_has_closing_in_commands():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        content = file.read_text()
        tags = set(re.findall(r"<([a-z][a-z-]*)>", content))
        for tag in tags:
            if f"</{tag}>" not in content:
                errors.append(f"Unclosed tag <{tag}> in {f}")
    assert not errors, "\n".join(errors)


def test_T_0005_120c_tag_matching_in_retro_lessons():
    file = INSTALLED_REFS / "retro-lessons.md"
    content = file.read_text()
    errors = []
    # Find all opening tags (handling tags with attributes)
    tags = set(re.findall(r"<([a-z][a-z-]*)[\s>]", content))
    for tag in tags:
        open_count = len(re.findall(rf"<{tag}[\s>]", content))
        close_count = content.count(f"</{tag}>")
        if open_count != close_count:
            errors.append(f"Tag mismatch for <{tag}>: {open_count} opens vs {close_count} closes")
    assert not errors, "\n".join(errors)


# ── T-0005-121 ───────────────────────────────────────────────────────

def test_T_0005_121_thought_type_values_match_brain_enum():
    templates = (INSTALLED_REFS / "invocation-templates.md").read_text()
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    expected_types = ["decision", "pattern", "lesson", "correction", "drift", "insight", "handoff", "rejection", "preference"]
    errors = []
    for t in expected_types:
        if t not in templates and t not in schema:
            errors.append(f"Thought type '{t}' not found in templates or schema")
    assert not errors, "\n".join(errors)


# ── T-0005-122 ───────────────────────────────────────────────────────

def test_T_0005_122_thought_agent_values_include_all_agents():
    schema = (INSTALLED_REFS / "xml-prompt-schema.md").read_text()
    all_agents = ["cal", "colby", "roz", "agatha", "robert", "sable", "eva", "poirot", "ellis", "distillator"]
    errors = []
    for agent in all_agents:
        if agent not in schema:
            errors.append(f"Agent '{agent}' not listed in schema's thought agent values")
    assert not errors, "\n".join(errors)


# ── T-0005-123 ───────────────────────────────────────────────────────

def test_T_0005_123_no_nested_persona_tags():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        for outer in PERSONA_TAGS:
            content = extract_tag_content(file, outer)
            for inner in PERSONA_TAGS:
                if inner == outer:
                    continue
                if f"<{inner}>" in content:
                    errors.append(f"Nested <{inner}> inside <{outer}> in {f}")
    assert not errors, "\n".join(errors)
