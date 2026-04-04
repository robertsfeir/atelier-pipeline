"""ADR-0005 Step 1: Retro Lessons Conversion.

Tests: T-0005-010 through T-0005-019.
Migrated from step1-retro-lessons.test.bats.
"""

import re

from tests.conftest import (
    INSTALLED_REFS,
    SOURCE_REFS,
    assert_has_closing_tag,
    assert_has_tag,
    line_of,
)


# ── T-0005-010: Root tag wrapping ────────────────────────────────────

def test_T_0005_010_retro_lessons_contains_root_tag():
    f = INSTALLED_REFS / "retro-lessons.md"
    assert_has_tag(f, "retro-lessons")
    assert_has_closing_tag(f, "retro-lessons")


# ── T-0005-011: Lesson tags with id and agents attributes ────────────

def test_T_0005_011_lesson_tags_have_id_and_agents():
    content = (INSTALLED_REFS / "retro-lessons.md").read_text()
    lessons = len(re.findall(r"<lesson ", content))
    assert lessons > 0
    ids_with_format = len(re.findall(r'<lesson [^>]*id="[0-9]{3}"', content))
    assert lessons == ids_with_format, f"Not all lessons have 3-digit ids: {ids_with_format}/{lessons}"
    with_agents = len(re.findall(r'<lesson [^>]*agents="', content))
    assert lessons == with_agents, f"Not all lessons have agents: {with_agents}/{lessons}"


# ── T-0005-012: Rule tags with agent attribute ────��──────────────────

def test_T_0005_012_rule_tags_have_agent_attribute():
    content = (INSTALLED_REFS / "retro-lessons.md").read_text()
    rules = len(re.findall(r"<rule ", content))
    assert rules > 0
    with_agent = len(re.findall(r'<rule agent="[a-z]+"', content))
    assert rules == with_agent


# ── T-0005-013: Introductory prose and CONFIGURE comment outside tag ─

def test_T_0005_013_configure_comment_above_retro_lessons_tag():
    f = INSTALLED_REFS / "retro-lessons.md"
    configure_line = line_of(f, "CONFIGURE")
    retro_line = line_of(f, "<retro-lessons>")
    assert configure_line is not None
    assert retro_line is not None
    assert configure_line < retro_line


def test_T_0005_013b_introductory_prose_above_retro_lessons_tag():
    f = INSTALLED_REFS / "retro-lessons.md"
    retro_line = line_of(f, "<retro-lessons>")
    assert retro_line is not None
    lines_before = f.read_text().splitlines()[: retro_line - 1]
    prose_lines = [
        l for l in lines_before
        if l.strip() and not l.strip().startswith("<!--") and not l.strip().startswith("#")
    ]
    assert len(prose_lines) > 0


# ── T-0005-014: Agent consistency between lesson and rules ───────────

def test_T_0005_014_no_rule_for_unlisted_agent():
    content = (INSTALLED_REFS / "retro-lessons.md").read_text()
    errors = []
    in_lesson = False
    lesson_agents: list[str] = []
    for line in content.splitlines():
        m_lesson = re.search(r'<lesson [^>]*agents="([^"]*)"', line)
        if m_lesson:
            in_lesson = True
            lesson_agents = [a.strip() for a in m_lesson.group(1).split(",")]
        if in_lesson:
            m_rule = re.search(r'<rule agent="([^"]*)"', line)
            if m_rule:
                rule_agent = m_rule.group(1)
                if rule_agent not in lesson_agents:
                    errors.append(f"Rule agent='{rule_agent}' not in lesson agents='{lesson_agents}'")
        if "</lesson>" in line:
            in_lesson = False
            lesson_agents = []
    assert not errors, "\n".join(errors)


# ── T-0005-015: Source and installed copies both converted ───────────

def test_T_0005_015_both_trees_have_xml_structure():
    for f in [SOURCE_REFS / "retro-lessons.md", INSTALLED_REFS / "retro-lessons.md"]:
        assert_has_tag(f, "retro-lessons")
        assert_has_closing_tag(f, "retro-lessons")


# ── T-0005-016: Existing lesson content preserved ────────────────────

def test_T_0005_016_existing_lesson_content_preserved():
    content = (INSTALLED_REFS / "retro-lessons.md").read_text()
    assert "Sensitive Data in Return Shapes" in content or "sensitive" in content.lower()
    assert "Self-Reporting Bug Codification" in content or "self-reporting" in content.lower()
    assert "Stop Hook Race Condition" in content or "stop" in content.lower()


# ── T-0005-017: No lesson tag missing id attribute ───────────────────

def test_T_0005_017_no_lesson_missing_id():
    content = (INSTALLED_REFS / "retro-lessons.md").read_text()
    lessons_without_id = [l for l in re.findall(r"<lesson\b[^>]*>", content) if "id=" not in l]
    assert len(lessons_without_id) == 0, f"Lessons missing id: {lessons_without_id}"


# ── T-0005-018: No duplicate lesson ids ──────────────────────────────

def test_T_0005_018_no_duplicate_lesson_ids():
    content = (INSTALLED_REFS / "retro-lessons.md").read_text()
    ids = re.findall(r'id="([0-9]+)"', content)
    assert len(ids) > 0
    assert len(ids) == len(set(ids)), f"Duplicate ids found: {[x for x in ids if ids.count(x) > 1]}"


# ── T-0005-019: Every agent in lesson's agents has a corresponding rule

def test_T_0005_019_every_listed_agent_has_rule():
    content = (INSTALLED_REFS / "retro-lessons.md").read_text()
    errors = []
    in_lesson = False
    lesson_agents: list[str] = []
    rule_agents: list[str] = []
    for line in content.splitlines():
        m_lesson = re.search(r'<lesson [^>]*agents="([^"]*)"', line)
        if m_lesson:
            in_lesson = True
            lesson_agents = [a.strip() for a in m_lesson.group(1).split(",")]
            rule_agents = []
        if in_lesson:
            m_rule = re.search(r'<rule agent="([^"]*)"', line)
            if m_rule:
                rule_agents.append(m_rule.group(1))
        if "</lesson>" in line and in_lesson:
            for a in lesson_agents:
                if a not in rule_agents:
                    errors.append(f"Agent '{a}' in lesson agents but no <rule agent=\"{a}\"> found")
            in_lesson = False
    assert not errors, "\n".join(errors)
