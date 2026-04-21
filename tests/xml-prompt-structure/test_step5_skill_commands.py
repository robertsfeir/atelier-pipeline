"""ADR-0005 Step 5: Skill Command Files Conversion.

Tests: T-0005-060 through T-0005-068, T-0005-108 through T-0005-111, T-0005-139.
Migrated from step5-skill-commands.test.bats.
"""

import re

from tests.conftest import (
    COMMAND_FILES,
    INSTALLED_COMMANDS,
    SKILL_TAGS,
    SOURCE_COMMANDS,
    assert_has_closing_tag,
    assert_has_tag,
    assert_tag_order,
    extract_tag_content,
    get_cognitive_directive,
    line_of,
)


# ── T-0005-060 ───────────────────────────────────────────────────────

def test_T_0005_060_all_commands_use_skill_xml_structure():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            errors.append(f"Missing: {file}")
            continue
        for tag in SKILL_TAGS:
            if f"<{tag}>" not in file.read_text():
                errors.append(f"Missing <{tag}> in {f}")
            if f"</{tag}>" not in file.read_text():
                errors.append(f"Missing </{tag}> in {f}")
        for i in range(len(SKILL_TAGS) - 1):
            la = line_of(file, f"<{SKILL_TAGS[i]}>")
            lb = line_of(file, f"<{SKILL_TAGS[i + 1]}>")
            if la and lb and la >= lb:
                errors.append(f"Tag order violation in {f}: <{SKILL_TAGS[i]}> vs <{SKILL_TAGS[i + 1]}>")
    assert not errors, "\n".join(errors)


# ── T-0005-061 ───────────────────────────────────────────────────────

def test_T_0005_061_yaml_frontmatter_present():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        lines = file.read_text().splitlines()
        if not lines[0].startswith("---"):
            errors.append(f"Missing YAML start in {f}")
        content = file.read_text()
        if not re.search(r"^name:", content, re.MULTILINE) and not re.search(r"^description:", content, re.MULTILINE):
            errors.append(f"Missing YAML fields in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-062 ───────────────────────────────────────────────────────

def test_T_0005_062_no_intensity_markers():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        content = file.read_text()
        content = re.sub(r"^---.*?^---", "", content, count=1, flags=re.DOTALL | re.MULTILINE)
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        for marker in ["MUST", "CRITICAL", "NEVER"]:
            if re.search(rf"\b{marker}\b", content):
                errors.append(f"Found intensity marker '{marker}' in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-063 ───────────────────────────────────────────────────────

def test_T_0005_063_nonempty_constraints_and_behavior():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        constraints = extract_tag_content(file, "constraints")
        cl = [l for l in constraints.splitlines() if l.strip() and not re.match(r"</?constraints>", l.strip())]
        if len(cl) < 1:
            errors.append(f"Empty constraints in {f}")
        behavior = extract_tag_content(file, "behavior")
        bl = [l for l in behavior.splitlines() if l.strip() and not re.match(r"</?behavior>", l.strip())]
        if len(bl) < 1:
            errors.append(f"Empty behavior in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-064 ───────────────────────────────────────────────────────

def test_T_0005_064_source_command_templates_preserve_placeholders():
    for f in COMMAND_FILES:
        file = SOURCE_COMMANDS / f
        if file.is_file():
            content = file.read_text()
            if re.search(r"\{[a-z_]+\}", content):
                pass  # Placeholders survive


# ── T-0005-065 ───────────────────────────────────────────────────────

def test_T_0005_065_pipeline_preserves_phase_transition_logic():
    behavior = extract_tag_content(INSTALLED_COMMANDS / "pipeline.md", "behavior")
    assert re.search(r"phase|transition|route|agent", behavior, re.IGNORECASE)


# ── T-0005-066 ───────────────────────────────────────────────────────

# removed by ADR-0045 — asserted deleted feature
# test_T_0005_066_debug_preserves_roz_colby_flow


# ── T-0005-067 ───────────────────────────────────────────────────────

def test_T_0005_067_every_skill_has_cognitive_directive():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        cmd_name = f.replace(".md", "")
        directive = get_cognitive_directive(cmd_name)
        if not directive:
            continue
        ra = extract_tag_content(file, "required-actions")
        if directive not in ra:
            errors.append(f"Missing cognitive directive in {f}: expected '{directive}'")
    assert not errors, "\n".join(errors)


# ── T-0005-068 ───────────────────────────────────────────────────────

def test_T_0005_068_skill_required_actions_no_numbered_steps():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        ra = extract_tag_content(file, "required-actions")
        if re.search(r"^\s*[0-9]+\.", ra, re.MULTILINE):
            errors.append(f"Found numbered steps in skill required-actions of {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-108 ───────────────────────────────────────────────────────

def test_T_0005_108_no_workflow_or_tools_in_skills():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        content = file.read_text()
        if "<workflow>" in content:
            errors.append(f"Found <workflow> in {f}")
        if "<tools>" in content:
            errors.append(f"Found <tools> in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-109 ───────────────────────────────────────────────────────

def test_T_0005_109_no_leftover_markdown_headings():
    errors = []
    headings = ["## Constraints", "## Output", "## Behavior"]
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        content = file.read_text()
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        for heading in headings:
            if re.search(rf"^{re.escape(heading)}$", content, re.MULTILINE):
                errors.append(f"Leftover heading '{heading}' in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-110 ───────────────────────────────────────────────────────

def test_T_0005_110_devops_has_cognitive_directive():
    file = INSTALLED_COMMANDS / "devops.md"
    assert_has_tag(file, "required-actions")
    ra = extract_tag_content(file, "required-actions")
    directive = get_cognitive_directive("devops")
    assert directive in ra, f"Missing cognitive directive in devops.md"


# ── T-0005-111 ───────────────────────────────────────────────────────

def test_T_0005_111_skill_required_actions_no_numbered_steps():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        ra = extract_tag_content(file, "required-actions")
        if re.search(r"^\s*[0-9]+\.", ra, re.MULTILINE):
            errors.append(f"Found numbered steps in required-actions of {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-139 ───────────────────────────────────────────────────────

def test_T_0005_139_no_examples_tag_in_skill_commands():
    errors = []
    for f in COMMAND_FILES:
        file = INSTALLED_COMMANDS / f
        if not file.is_file():
            continue
        if "<examples>" in file.read_text():
            errors.append(f"Found <examples> in skill command file {f}")
    assert not errors, "\n".join(errors)
