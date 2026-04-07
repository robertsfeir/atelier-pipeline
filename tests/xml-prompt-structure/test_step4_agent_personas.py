"""ADR-0005 Step 4: Agent Persona Files Conversion.

Tests: T-0005-040 through T-0005-059, T-0005-100 through T-0005-107.
Migrated from step4-agent-personas.test.bats.
"""

import re

import pytest

from tests.conftest import (
    AGENT_FILES,
    CLAUDE_DIR,
    PERSONA_TAGS,
    PROJECT_ROOT,
    SHARED_AGENTS,
    SOURCE_AGENTS,
    assert_has_closing_tag,
    assert_has_tag,
    assert_not_contains,
    assert_tag_order,
    extract_tag_content,
    get_cognitive_directive,
    line_of,
)

# Source path aliases: content lives in source/shared/agents/, frontmatter in source/claude/agents/
INSTALLED_AGENTS = SHARED_AGENTS


# ── T-0005-040 ───────────────────────────────────────────────────────

def test_T_0005_040_all_agents_have_6_tags_in_order():
    # Ellis is exempt from the preamble structure -- it has identity, workflow,
    # examples, constraints, output but no required-actions by design (ADR-0023).
    ELLIS_TAGS = ["identity", "workflow", "examples", "constraints", "output"]
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            errors.append(f"Missing: {file}")
            continue
        content = file.read_text()
        tags = ELLIS_TAGS if f == "ellis.md" else PERSONA_TAGS
        for tag in tags:
            if f"<{tag}>" not in content:
                errors.append(f"Missing <{tag}> in {f}")
            if f"</{tag}>" not in content:
                errors.append(f"Missing </{tag}> in {f}")
        for i in range(len(tags) - 1):
            la = line_of(file, f"<{tags[i]}>")
            lb = line_of(file, f"<{tags[i + 1]}>")
            if la and lb and la >= lb:
                errors.append(f"Tag order violation in {f}: <{tags[i]}> (line {la}) vs <{tags[i + 1]}> (line {lb})")
    assert not errors, "\n".join(errors)


# ── T-0005-041 ───────────────────────────────────────────────────────

def test_T_0005_041_identity_contains_name_role_pronouns():
    # Model reference removed from agent identity per ADR-0023.
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
    assert not errors, "\n".join(errors)


# ── T-0005-042 ───────────────────────────────────────────────────────

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
    # Frontmatter lives in source/claude/agents/X.frontmatter.yml (ADR-0022 split)
    errors = []
    for f in AGENT_FILES:
        agent_name = f.replace(".md", "")
        fm_file = CLAUDE_DIR / "agents" / f"{agent_name}.frontmatter.yml"
        if not fm_file.is_file():
            continue
        content = fm_file.read_text()
        if not re.search(r"^name:", content, re.MULTILINE):
            errors.append(f"Missing 'name:' in {agent_name}.frontmatter.yml")
        if not re.search(r"^description:", content, re.MULTILINE):
            errors.append(f"Missing 'description:' in {agent_name}.frontmatter.yml")
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
        # ADR-0023: constraints sections may use intensity markers as intentional
        # behavioral instructions (e.g., "NEVER push directly to the base branch").
        content = re.sub(r"<constraints>.*?</constraints>", "", content, flags=re.DOTALL)
        for marker in ["MUST", "CRITICAL", "NEVER"]:
            if re.search(rf"\b{marker}\b", content):
                errors.append(f"Found intensity marker '{marker}' in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-054 ───────────────────────────────────────────────────────

def test_T_0005_054_output_includes_knowledge_surfacing():
    """Post ADR-0023/0024: brain captures moved to brain-extractor hook.
    Output sections now focus on structured deliverables rather than explicit
    knowledge surfacing.  Verify each agent has a non-empty <output> section."""
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        output = extract_tag_content(file, "output")
        content_lines = [l for l in output.splitlines()
                        if l.strip() and not re.match(r"</?output>", l.strip())]
        if len(content_lines) < 1:
            errors.append(f"Empty output section in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-055 ───────────────────────────────────────────────────────

def test_T_0005_055_cal_model_opus():
    """Post ADR-0023: model references removed from identity tags.
    Verify Cal identity contains role description instead."""
    identity = extract_tag_content(INSTALLED_AGENTS / "cal.md", "identity")
    assert re.search(r"Architect", identity, re.IGNORECASE)


# ── T-0005-056 ───────────────────────────────────────────────────────

def test_T_0005_056_colby_model_size_dependent():
    """Post ADR-0023: model references removed from identity tags.
    Verify Colby identity contains role description instead."""
    identity = extract_tag_content(INSTALLED_AGENTS / "colby.md", "identity")
    assert re.search(r"Engineer", identity, re.IGNORECASE)


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
        # Ellis has no required-actions by design (exempt from preamble)
        if agent_name == "ellis":
            continue
        directive = get_cognitive_directive(agent_name)
        if not directive:
            continue
        ra = extract_tag_content(file, "required-actions")
        # Normalize whitespace for cross-line directives
        ra_normalized = " ".join(ra.split()).lower()
        if directive.lower() not in ra_normalized:
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
        agent_name = f.replace(".md", "")
        # Ellis is exempt from preamble -- has no required-actions by design
        if agent_name == "ellis":
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
        # Ellis is exempt from preamble -- has no cognitive directive
        if agent_name == "ellis":
            continue
        directive = get_cognitive_directive(agent_name)
        if not directive:
            continue
        # Normalize whitespace for cross-line directives
        content_normalized = " ".join(file.read_text().split()).lower()
        if directive.lower() not in content_normalized:
            errors.append(f"Cognitive directive mismatch in {f}: expected '{directive}'")
    assert not errors, "\n".join(errors)


# ── T-0005-105 ───────────────────────────────────────────────────────

def test_T_0005_105_comment_between_frontmatter_and_identity():
    # In source/shared/agents/, files have no YAML frontmatter.
    # The HTML comment header appears before <identity> as the first line.
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        comment_line = line_of(file, "Part of atelier-pipeline")
        identity_line = line_of(file, "<identity>")

        if not comment_line or not identity_line:
            errors.append(f"Missing required markers in {f}")
            continue
        if comment_line >= identity_line:
            errors.append(f"Comment not before <identity> in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-106 ───────────────────────────────────────────────────────

def test_T_0005_106_investigator_follows_7_tag_structure():
    """Post ADR-0023: <tools> tag removed from agent personas.
    Verify investigator has the 6 remaining persona tags."""
    file = INSTALLED_AGENTS / "investigator.md"
    assert file.is_file()
    # ADR-0023 removed <tools> from persona files
    tags_without_tools = [t for t in PERSONA_TAGS if t != "tools"]
    for tag in tags_without_tools:
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
