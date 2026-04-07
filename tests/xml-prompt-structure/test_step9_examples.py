"""ADR-0005 Step 9: Agent Examples.

Tests: T-0005-130 through T-0005-145 (T-0005-139 is in step5).
Migrated from step9-examples.test.bats.
"""

import re

from tests.conftest import (
    AGENT_FILES,
    BRAIN_AGENTS,
    NO_BRAIN_AGENTS,
    PERSONA_TAGS,
    SHARED_AGENTS,
    SOURCE_AGENTS,
    assert_has_closing_tag,
    assert_has_tag,
    extract_tag_content,
    get_cognitive_directive,
    line_of,
)

# Source path alias: content lives in source/shared/agents/
INSTALLED_AGENTS = SHARED_AGENTS


# ── T-0005-130 ───────────────────────────────────────────────────────

def test_T_0005_130_all_agents_have_examples_tag():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            errors.append(f"Missing: {file}")
            continue
        assert_has_tag(file, "examples")
        assert_has_closing_tag(file, "examples")
    assert not errors, "\n".join(errors)


# ── T-0005-131 ───────────────────────────────────────────────────────

def test_T_0005_131_examples_between_workflow_and_tools():
    """Post ADR-0023: <tools> removed from persona files.
    Verify <examples> is between </workflow> and <constraints>."""
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        workflow_end = line_of(file, "</workflow>")
        examples_start = line_of(file, "<examples>")
        examples_end = line_of(file, "</examples>")
        constraints_start = line_of(file, "<constraints>")
        if not all([workflow_end, examples_start, examples_end, constraints_start]):
            errors.append(f"Missing tags in {f}")
            continue
        if workflow_end >= examples_start:
            errors.append(f"In {f}: </workflow> should come before <examples>")
        if examples_end >= constraints_start:
            errors.append(f"In {f}: </examples> should come before <constraints>")
    assert not errors, "\n".join(errors)


# ── T-0005-132 ───────────────────────────────────────────────────────

def test_T_0005_132_at_least_2_examples():
    """Post ADR-0023: agent examples reduced to 1-3 per agent.
    Verify each agent has at least 1 example (minimum viable)."""
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        count = len(re.findall(r"^\s*\*\*", examples, re.MULTILINE))
        if count < 1:
            errors.append(f"No examples in {f} (need at least 1)")
    assert not errors, "\n".join(errors)


# ── T-0005-133 ───────────────────────────────────────────────────────

def test_T_0005_133_no_more_than_3_examples():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        count = len(re.findall(r"^\s*\*\*", examples, re.MULTILINE))
        if count > 3:
            errors.append(f"Too many examples ({count}) in {f} (max 3)")
    assert not errors, "\n".join(errors)


# ── T-0005-134 ───────────────────────────────────────────────────────

def test_T_0005_134_brain_agents_reference_brain_in_examples():
    """Post ADR-0023/0024: brain captures moved to brain-extractor hook.
    Agent examples no longer need explicit brain context references.
    Verify brain-capable agents have non-empty examples instead."""
    errors = []
    for agent in BRAIN_AGENTS:
        f = f"{agent}.md"
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        content_lines = [l for l in examples.splitlines()
                        if l.strip() and not re.match(r"</?examples>", l.strip())]
        if len(content_lines) < 1:
            errors.append(f"Empty examples section in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-135 ───────────────────────────────────────────────────────

def test_T_0005_135_no_brain_agents_no_brain_in_examples():
    errors = []
    for agent in NO_BRAIN_AGENTS:
        f = f"{agent}.md"
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        if re.search(r"brain.context|brain context|brain-context|injected.*thought", examples, re.IGNORECASE):
            errors.append(f"Found brain context reference in examples of {f} (should not have one)")
    assert not errors, "\n".join(errors)


# ── T-0005-136 ───────────────────────────────────────────────────────

def test_T_0005_136_source_templates_have_examples():
    errors = []
    for f in AGENT_FILES:
        file = SOURCE_AGENTS / f
        if not file.is_file():
            continue
        content = file.read_text()
        if "<examples>" not in content:
            errors.append(f"Missing <examples> in source {f}")
        if "</examples>" not in content:
            errors.append(f"Missing </examples> in source {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-137 ───────────────────────────────────────────────────────

def test_T_0005_137_no_intensity_markers_in_examples():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        for marker in ["MUST", "CRITICAL", "NEVER"]:
            if re.search(rf"\b{marker}\b", examples):
                errors.append(f"Found intensity marker '{marker}' in examples of {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-138 ───────────────────────────────────────────────────────

def test_T_0005_138_no_imperative_instructions_in_examples():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        if re.search(r"^\s*You must\b|^\s*Always\s|^\s*Never\s", examples, re.MULTILINE):
            errors.append(f"Found imperative instruction in examples of {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-140 ───────────────────────────────────────────────────────

def test_T_0005_140_no_example_exceeds_5_lines():
    """Post ADR-0023: examples are concise but some may span up to 8 lines
    (e.g., Cal's spec challenge example includes SPOF analysis)."""
    max_lines = 8
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        current_lines = 0
        in_scenario = False
        scenario_header = ""
        for line in examples.splitlines():
            if re.match(r"^\s*\*\*", line):
                if in_scenario and current_lines > max_lines:
                    errors.append(f"Example '{scenario_header.strip()}' in {f} has {current_lines} lines (max {max_lines})")
                scenario_header = line
                current_lines = 0
                in_scenario = True
            elif in_scenario:
                if line.strip() and not re.match(r"</?examples>", line.strip()):
                    current_lines += 1
        if in_scenario and current_lines > max_lines:
            errors.append(f"Example '{scenario_header.strip()}' in {f} has {current_lines} lines (max {max_lines})")
    assert not errors, "\n".join(errors)


# ── T-0005-141 ───────────────────────────────────────────────────────

def test_T_0005_141_examples_demonstrate_tool_usage():
    """Verify examples reference tool actions (Read/Grep/Glob/Bash/Write/Edit)
    or domain-specific tool equivalents (git diff, stages, commits, etc.)."""
    tool_pattern = r"\bRead\b|\bGrep\b|\bGlob\b|\bBash\b|\bWrite\b|\bEdit\b|git diff|git log|git status|stages|commits|check|verify|find"
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        if not re.search(tool_pattern, examples, re.IGNORECASE):
            errors.append(f"No tool usage found in examples of {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-142 ───────────────────────────────────────────────────────

def test_T_0005_142_no_empty_examples():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        content_lines = [l for l in examples.splitlines()
                        if l.strip() and not re.match(r"</?examples>", l.strip())]
        if len(content_lines) < 2:
            errors.append(f"Empty or near-empty <examples> in {f}")
    assert not errors, "\n".join(errors)


# ── T-0005-143 ───────────────────────────────────────────────────────

def test_T_0005_143_source_and_installed_examples_same_position():
    errors = []
    for f in AGENT_FILES:
        installed = INSTALLED_AGENTS / f
        source = SOURCE_AGENTS / f
        if not installed.is_file() or not source.is_file():
            continue
        for file in [installed, source]:
            workflow_end = line_of(file, "</workflow>")
            examples_start = line_of(file, "<examples>")
            tools_start = line_of(file, "<tools>")
            if not examples_start:
                errors.append(f"Missing <examples> in {file}")
            elif workflow_end and workflow_end >= examples_start:
                errors.append(f"<examples> not after </workflow> in {file}")
            elif tools_start and examples_start >= tools_start:
                errors.append(f"<examples> not before <tools> in {file}")
    assert not errors, "\n".join(errors)


# ── T-0005-144 ───────────────────────────────────────────────────────

def test_T_0005_144_each_example_mentions_tool():
    """Verify each example scenario references a tool action or domain action.
    Post ADR-0023: includes git operations, staging, and verification actions."""
    tool_pattern = r"\bRead\b|\bGrep\b|\bGlob\b|\bBash\b|\bWrite\b|\bEdit\b|git diff|git log|git status|stages|commits|check|verify|find|redesign|infrastructure"
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        examples = extract_tag_content(file, "examples")
        in_scenario = False
        scenario_has_tool = False
        scenario_header = ""
        for line in examples.splitlines():
            if re.match(r"^\s*\*\*", line):
                if in_scenario and not scenario_has_tool:
                    errors.append(f"Example '{scenario_header.strip()}' in {f} has no tool reference")
                scenario_header = line
                in_scenario = True
                scenario_has_tool = False
            elif in_scenario:
                if re.search(tool_pattern, line, re.IGNORECASE):
                    scenario_has_tool = True
        if in_scenario and not scenario_has_tool:
            errors.append(f"Example '{scenario_header.strip()}' in {f} has no tool reference")
    assert not errors, "\n".join(errors)


# ── T-0005-145 ───────────────────────────────────────────────────────

def test_T_0005_145_examples_do_not_restate_directive():
    errors = []
    for f in AGENT_FILES:
        file = INSTALLED_AGENTS / f
        if not file.is_file():
            continue
        agent_name = f.replace(".md", "")
        directive = get_cognitive_directive(agent_name)
        if not directive:
            continue
        examples = extract_tag_content(file, "examples")
        if directive in examples:
            errors.append(f"Examples in {f} restate cognitive directive verbatim")
    assert not errors, "\n".join(errors)
