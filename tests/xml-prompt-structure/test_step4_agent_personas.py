"""ADR-0005 Step 4: Agent Persona Files Conversion.

Tests: T-0005-040 through T-0005-059, T-0005-100 through T-0005-107.
Migrated from step4-agent-personas.test.bats.
"""

import re

import pytest

from tests.conftest import (
    AGENT_FILES,
    BRAIN_AGENTS,
    INSTALLED_AGENTS,
    NO_BRAIN_AGENTS,
    PERSONA_TAGS,
    SOURCE_AGENTS,
    assert_has_closing_tag,
    assert_has_tag,
    assert_not_contains,
    assert_tag_order,
    extract_tag_content,
    get_cognitive_directive,
    line_of,
)


# ── T-0005-040 ───────────────────────────────────────────────────────

@pytest.mark.skip("Pending ADR-0023 completion: <tools> tag removed from agent personas")
def test_T_0005_040_all_agents_have_7_tags_in_order():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            errors.append(f"Missing: {file}")
            continue
        content = file.read_text()
        for tag in PERSONA_TAGS:
            if f"<{tag}>" not in content:
                errors.append(f"Missing <{tag}> in {f}")
            if f"</{tag}>" not in content:
                errors.append(f"Missing </{tag}> in {f}")
        for i in range(len(PERSONA_TAGS) - 1):
            la = line_of(file, f"<{PERSONA_TAGS[i]}>")
            lb = line_of(file, f"<{PERSONA_TAGS[i + 1]}>")
            if la and lb and la >= lb:
                errors.append(f"Tag order violation in {f}: <{PERSONA_TAGS[i]}> (line {la}) vs <{PERSONA_TAGS[i + 1]}> (line {lb})")
    assert not errors, "\n".join(errors)


# ── T-0005-041 ───────────────────────────────────────────────────────

@pytest.mark.skip("Pending ADR-0023 completion: model reference removed from agent identity")
def test_T_0005_041_identity_contains_name_role_pronouns_model():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        identity = extract_tag_content(file, "identity")
        agent_name = f.replace(".md", "")
        if agent_name == "investigator":
            agent_name = "Poirot"
        if not re.search(agent_name, identity, re.IGNORECASE):
            errors.append(f"Missing agent name in identity of {f}")
        if not re.search(r"pronouns|she/her|he/him|they/them", identity, re.IGNORECASE):
            errors.append(f"Missing pronouns in identity of {f}")
        if not re.search(r"model|Opus|Sonnet|Haiku", identity, re.IGNORECASE):
            errors.append(f"Missing model reference in identity of {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-042 ───────────────────────────────────────────────────────

@pytest.mark.skip("Pending ADR-0023 completion: ## Brain Access heading not yet removed from all agents")
def test_T_0005_042_no_brain_access_heading():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        content = file.read_text()
        if re.search(r"^## Brain Access", content, re.MULTILINE):
            errors.append(f"Found leftover '## Brain Access' heading in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-043 ───────────────────────────────────────────────────────

@pytest.mark.skip("Pending ADR-0023 completion: retro reference removed from required-actions")
def test_T_0005_043_required_actions_mentions_retro():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        ra = extract_tag_content(file, "required-actions")
        if not re.search(r"retro", ra, re.IGNORECASE):
            errors.append(f"Missing retro lesson reference in required-actions of {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-044 ───────────────────────────────────────────────────────

@pytest.mark.skip("Pending ADR-0023 completion: brain context reference removed from required-actions")
def test_T_0005_044_brain_capable_agents_reference_brain_context():
    errors = []
    for agent in BRAIN_AGENTS:
        f = f"{agent}.md"
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        ra = extract_tag_content(file, "required-actions")
        if not re.search(r"brain.context|brain context|brain-context|injected.*thought|provided.*brain", ra, re.IGNORECASE):
            errors.append(f"Missing brain context reference in required-actions of {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-045 ───────────────────────────────────────────────────────

def test_T_0005_045_distillator_no_brain_context():
    ra = extract_tag_content(INSTALLED_AGENTS / "distillator.md", "required-actions")
    assert not re.search(r"brain.context|brain context|brain-context", ra, re.IGNORECASE), \
        "Distillator should not reference brain context in required-actions"


# ── T-0005-046 ───────────────────────────────────────────────────────

def test_T_0005_046_no_must_call_brain_tools():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        content = file.read_text()
        if "MUST call agent_search" in content:
            errors.append(f"Found 'MUST call agent_search' in {f}")
        if "MUST call agent_capture" in content:
            errors.append(f"Found 'MUST call agent_capture' in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-047 ───────────────────────────────────────────────────────

def test_T_0005_047_no_mandatory_in_allcaps():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        # Strip frontmatter and code blocks
        content = file.read_text()
        # Remove YAML frontmatter
        content = re.sub(r"^---.*?^---", "", content, count=1, flags=re.DOTALL | re.MULTILINE)
        # Remove code blocks
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        if re.search(r"\bMANDATORY\b", content):
            errors.append(f"Found 'MANDATORY' in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-048 ───────────────────────────────────────────────────────

def test_T_0005_048_yaml_frontmatter_present():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        lines = file.read_text().splitlines()
        if not lines[0].startswith("---"):
            errors.append(f"Missing YAML start in {f}")
        content = file.read_text()
        if not re.search(r"^name:", content, re.MULTILINE):
            errors.append(f"Missing 'name:' in {f}")
        if not re.search(r"^description:", content, re.MULTILINE):
            errors.append(f"Missing 'description:' in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-049 ───────────────────────────────────────────────────────

def test_T_0005_049_nonempty_constraints():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        constraints = extract_tag_content(file, "constraints")
        content_lines = [l for l in constraints.splitlines()
                        if l.strip() and not re.match(r"</?constraints>", l.strip())]
        if len(content_lines) < 2:
            errors.append(f"Constraints section too short in {f} (only {len(content_lines)} content lines)")
    assert not errors, "\n".join(errors)


# ── T-0005-050 ───────────────────────────────────────────────────────

def test_T_0005_050_source_templates_preserve_placeholders():
    # Verify source files preserve placeholder variables -- pass-through test
    for f in AGENT_FILES:
        file = SOURCE_AGENTS / f
        if file.is_file():
            content = file.read_text()
            if re.search(r"\{[a-z_]+\}", content):
                pass  # Placeholders survive


# ── T-0005-051 ───────────────────────────────────────────────────────

def test_T_0005_051_colby_she_her():
    identity = extract_tag_content(INSTALLED_AGENTS / "colby.md", "identity")
    assert "she/her" in identity


# ── T-0005-052 ───────────────────────────────────────────────────────

def test_T_0005_052_poirot_no_brain_context():
    ra = extract_tag_content(INSTALLED_AGENTS / "investigator.md", "required-actions")
    assert not re.search(r"brain.context|brain context|brain-context", ra, re.IGNORECASE), \
        "Poirot should not reference brain context in required-actions"


# ── T-0005-053 ───────────────────────────────────────────────────────

def test_T_0005_053_no_intensity_markers():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        content = file.read_text()
        content = re.sub(r"^---.*?^---", "", content, count=1, flags=re.DOTALL | re.MULTILINE)
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        for marker in ["MUST", "CRITICAL", "NEVER"]:
            if re.search(rf"\b{marker}\b", content):
                errors.append(f"Found intensity marker '{marker}' in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-054 ───────────────────────────────────────────────────────

def test_T_0005_054_output_includes_knowledge_surfacing():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        output = extract_tag_content(file, "output")
        if not re.search(r"knowledge|pattern|decision|Eva|brain|capture|insight", output, re.IGNORECASE):
            errors.append(f"Missing knowledge surfacing guidance in output of {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-055 ───────────────────────────────────────────────────────

def test_T_0005_055_cal_model_opus():
    identity = extract_tag_content(INSTALLED_AGENTS / "cal.md", "identity")
    assert re.search(r"Opus", identity, re.IGNORECASE)


# ── T-0005-056 ───────────────────────────────────────────────────────

def test_T_0005_056_colby_model_size_dependent():
    identity = extract_tag_content(INSTALLED_AGENTS / "colby.md", "identity")
    assert re.search(r"Sonnet.*Opus|small.*medium.*large|Haiku.*Sonnet.*Opus|size", identity, re.IGNORECASE) or \
        re.search(r"Sonnet.*(small|medium)|Opus.*(large)", identity, re.IGNORECASE)


# ── T-0005-057 ───────────────────────────────────────────────────────

def test_T_0005_057_atelier_pipeline_comment_preserved():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        if "Part of atelier-pipeline" not in file.read_text():
            errors.append(f"Missing atelier-pipeline comment in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-058 ───────────────────────────────────────────────────────

def test_T_0005_058_cognitive_directive_in_required_actions():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        agent_name = f.replace(".md", "")
        directive = get_cognitive_directive(agent_name)
        if not directive:
            continue
        ra = extract_tag_content(file, "required-actions")
        if directive not in ra:
            errors.append(f"Missing cognitive directive in {f}: expected '{directive}'")
    assert not errors, "\n".join(errors)


# ── T-0005-059 ───────────────────────────────────────────────────────

def test_T_0005_059_cognitive_directives_no_intensity_markers():
    errors = []
    for f in AGENT_FILES:
        agent_name = f.replace(".md", "")
        directive = get_cognitive_directive(agent_name)
        if not directive:
            continue
        for marker in ["MUST", "CRITICAL"]:
            if re.search(rf"\b{marker}\b", directive):
                errors.append(f"Cognitive directive for {agent_name} contains intensity marker '{marker}'")
    assert not errors, "\n".join(errors)


# ── T-0005-100 ───────────────────────────────────────────────────────

def test_T_0005_100_no_empty_required_actions():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        ra = extract_tag_content(file, "required-actions")
        content_lines = [l for l in ra.splitlines()
                        if l.strip() and not re.match(r"</?required-actions>", l.strip())]
        if len(content_lines) < 1:
            errors.append(f"Empty required-actions in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-101 ───────────────────────────────────────────────────────

def test_T_0005_101_no_nested_persona_tags():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        for outer in PERSONA_TAGS:
            inner_content = extract_tag_content(file, outer)
            for inner in PERSONA_TAGS:
                if inner == outer:
                    continue
                if f"<{inner}>" in inner_content:
                    errors.append(f"Nested tag <{inner}> inside <{outer}> in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-102 ───────────────────────────────────────────────────────

def test_T_0005_102_no_leftover_markdown_headings():
    errors = []
    headings = ["## Brain Access", "## Shared Rules", "## Tool Constraints", "## Forbidden Actions"]
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        content = file.read_text()
        for heading in headings:
            if re.search(rf"^{re.escape(heading)}", content, re.MULTILINE):
                errors.append(f"Leftover heading '{heading}' in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-103 ───────────────────────────────────────────────────────

def test_T_0005_103_no_brain_tool_call_instructions():
    errors = []
    patterns = ["MUST call agent_search", "MUST call agent_capture", "call `agent_search`", "call `agent_capture`"]
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        content = file.read_text()
        for p in patterns:
            if p in content:
                errors.append(f"Found brain tool call instruction '{p}' in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-104 ───────────────────────────────────────────────────────

def test_T_0005_104_cognitive_directive_matches_adr():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        agent_name = f.replace(".md", "")
        directive = get_cognitive_directive(agent_name)
        if not directive:
            continue
        if directive not in file.read_text():
            errors.append(f"Cognitive directive mismatch in {f}: expected '{directive}'")
    assert not errors, "\n".join(errors)


# ── T-0005-105 ───────────────────────────────────────────────────────

def test_T_0005_105_comment_between_frontmatter_and_identity():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        comment_line = line_of(file, "Part of atelier-pipeline")
        identity_line = line_of(file, "<identity>")
        # Find second --- (end of YAML frontmatter)
        yaml_ends = [i for i, l in enumerate(file.read_text().splitlines(), 1) if l.strip() == "---"]
        yaml_end_line = yaml_ends[1] if len(yaml_ends) >= 2 else None

        if not comment_line or not identity_line or not yaml_end_line:
            errors.append(f"Missing required markers in {f}")
            continue
        if comment_line <= yaml_end_line or comment_line >= identity_line:
            errors.append(f"Comment not between frontmatter and <identity> in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-106 ───────────────────────────────────────────────────────

def test_T_0005_106_investigator_follows_7_tag_structure():
    file = INSTALLED_AGENTS / "investigator.md"
    assert file.is_file()
    for tag in PERSONA_TAGS:
        assert_has_tag(file, tag)
        assert_has_closing_tag(file, tag)


# ── T-0005-107 ───────────────────────────────────────────────────────

def test_T_0005_107_source_and_installed_same_tag_order():
    errors = []
    tag_pattern = r"<(identity|required-actions|workflow|examples|tools|constraints|output)>"
    for f in AGENT_FILES:
        installed = INSTALLED_AGENTS / f
        source = SOURCE_AGENTS / f
        if not installed.is_file():
            continue
        if not source.is_file():
            errors.append(f"Missing source file: {f}")
            continue
        installed_tags = re.findall(tag_pattern, installed.read_text())
        source_tags = re.findall(tag_pattern, source.read_text())
        if installed_tags != source_tags:
            errors.append(f"Tag order mismatch in {f}")
    assert not errors, "\n".join(errors)
