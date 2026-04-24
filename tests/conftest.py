"""Project-level conftest.py: shared path constants and structural assertion helpers.

Migrated from tests/xml-prompt-structure/test_helper.bash.
Provides the same paths, constants, and helpers used by all structural/content tests.
"""

import json
import re
import subprocess
from pathlib import Path

import pytest


# ── Project Paths ────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Installed (assembled) file trees
INSTALLED_AGENTS = PROJECT_ROOT / ".claude" / "agents"
INSTALLED_COMMANDS = PROJECT_ROOT / ".claude" / "commands"
INSTALLED_REFS = PROJECT_ROOT / ".claude" / "references"
INSTALLED_RULES = PROJECT_ROOT / ".claude" / "rules"
INSTALLED_HOOKS = PROJECT_ROOT / ".claude" / "hooks"

# Source directory root
SOURCE_DIR = PROJECT_ROOT / "source"

# Post-ADR-0022 split directories
SHARED_DIR = SOURCE_DIR / "shared"
CLAUDE_DIR = SOURCE_DIR / "claude"
CURSOR_DIR = SOURCE_DIR / "cursor"

# Source file trees -- point to shared/ (the canonical location post-ADR-0022).
# The bats test_helper.bash used $PROJECT_ROOT/source/agents etc., but after
# the source split (ADR-0022), all shared content lives under source/shared/.
SOURCE_AGENTS = SHARED_DIR / "agents"
SOURCE_COMMANDS = SHARED_DIR / "commands"
SOURCE_REFS = SHARED_DIR / "references"
SOURCE_RULES = SHARED_DIR / "rules"
SOURCE_HOOKS = SHARED_DIR / "hooks"
SOURCE_PIPELINE = SHARED_DIR / "pipeline"

# Aliases for tests that explicitly reference the shared paths
SHARED_AGENTS = SOURCE_AGENTS
SHARED_REFS = SOURCE_REFS
SHARED_RULES = SOURCE_RULES
SHARED_HOOKS = SOURCE_HOOKS

# Skills
SKILLS_DIR = PROJECT_ROOT / "skills"
SKILL_FILE = SKILLS_DIR / "pipeline-setup" / "SKILL.md"

# Cursor plugin
CURSOR_PLUGIN_DIR = PROJECT_ROOT / ".cursor-plugin"
CURSOR_AGENTS = CURSOR_PLUGIN_DIR / "agents"
CLAUDE_PLUGIN_DIR = PROJECT_ROOT / ".claude-plugin"


# ── File Lists ───────────────────────────────────────────────────────────

# All 9 original agent file basenames (ADR-0005 era)
AGENT_FILES = [
    "cal.md", "colby.md", "roz.md", "agatha.md", "ellis.md",
    "robert.md", "sable.md", "investigator.md", "distillator.md",
]

# All core agent filenames (post ADR-0045 Slice 4: darwin + deps removed, sherlock added)
ALL_AGENTS_CORE = [
    "cal.md", "colby.md", "roz.md", "agatha.md", "ellis.md",
    "robert.md", "sable.md", "investigator.md", "sentinel.md",
    "distillator.md", "sherlock.md",
]

# All 6 command file basenames (post ADR-0045 Slice 4: debug removed -- bug investigation routes through Sherlock subagent, not /debug skill)
COMMAND_FILES = [
    "pm.md", "ux.md", "docs.md", "architect.md",
    "pipeline.md", "devops.md",
]

# Brain-context-capable agents
BRAIN_AGENTS = ["cal", "colby", "roz", "agatha", "robert", "sable", "ellis"]

# Agents without brain context
NO_BRAIN_AGENTS = ["investigator", "distillator"]

# The 6 persona tags in required order (tools removed per ADR-0023)
PERSONA_TAGS = [
    "identity", "required-actions", "workflow",
    "examples", "constraints", "output",
]

# The skill command tags in required order
SKILL_TAGS = [
    "identity", "required-actions", "required-reading",
    "behavior", "output", "constraints",
]


# ── Cognitive Directive Lookup ───────────────────────────────────────────

COGNITIVE_DIRECTIVES = {
    "cal": "Never design against assumed codebase structure.",
    "architect": "Never design against assumed codebase structure.",
    "colby": "never assume code structure from the ADR alone",
    "roz": "Never flag a violation based on the diff alone.",
    "debug": "Never flag a violation based on the diff alone.",
    "agatha": "Never document behavior from the spec alone.",
    "docs": "Never document behavior from the spec alone.",
    "robert": "Never accept or reject based on spec text alone.",
    "pm": "Never accept or reject based on spec text alone.",
    "sable": "Never accept or reject based on the UX doc alone.",
    "ux": "Never accept or reject based on the UX doc alone.",
    "ellis": "Never write a commit message from the task description alone.",
    "investigator": "Never flag findings without verifying them against the codebase.",
    "distillator": "Never compress content you haven't fully read.",
    "pipeline": "Never route work or form hypotheses without reading the relevant code first.",
    "devops": "Never diagnose infrastructure issues from logs alone.",
}


def get_cognitive_directive(name: str) -> str:
    """Return the cognitive directive for a given agent or skill command name."""
    return COGNITIVE_DIRECTIVES.get(name, "")


# ── Structural Assertion Helpers ─────────────────────────────────────────


def assert_has_tag(file: Path, tag: str) -> None:
    """Assert a file contains an opening XML tag."""
    content = file.read_text()
    assert f"<{tag}>" in content, f"Missing <{tag}> in {file.name}"


def assert_has_closing_tag(file: Path, tag: str) -> None:
    """Assert a file contains a closing XML tag."""
    content = file.read_text()
    assert f"</{tag}>" in content, f"Missing </{tag}> in {file.name}"


def assert_not_contains(file: Path, pattern: str, msg: str = "") -> None:
    """Assert a file does NOT contain a regex pattern."""
    content = file.read_text()
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        default_msg = f"Found forbidden pattern '{pattern}' in {file.name}"
        raise AssertionError(msg or default_msg)


def line_of(file: Path, pattern: str) -> int | None:
    """Get the 1-based line number of the first occurrence of pattern. Returns None if not found."""
    for i, line in enumerate(file.read_text().splitlines(), start=1):
        if re.search(pattern, line):
            return i
    return None


def assert_tag_order(file: Path, tag_a: str, tag_b: str) -> None:
    """Assert tag_a appears before tag_b in a file."""
    line_a = line_of(file, f"<{tag_a}>")
    line_b = line_of(file, f"<{tag_b}>")
    assert line_a is not None, f"Cannot find <{tag_a}> in {file.name}"
    assert line_b is not None, f"Cannot find <{tag_b}> in {file.name}"
    assert line_a < line_b, (
        f"Tag order violation in {file.name}: <{tag_a}> (line {line_a}) "
        f"should come before <{tag_b}> (line {line_b})"
    )


def extract_tag_content(file: Path, tag: str) -> str:
    """Extract content between opening and closing tags (inclusive) from a file."""
    content = file.read_text()
    # Use a regex that handles attributes on the opening tag
    pattern = rf"<{tag}(?:\s[^>]*)?>.*?</{tag}>"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(0)
    return ""


def count_matches(file: Path, pattern: str) -> int:
    """Count occurrences of a regex pattern in a file."""
    content = file.read_text()
    return len(re.findall(pattern, content))


def extract_frontmatter(file: Path) -> str:
    """Extract YAML frontmatter from a markdown file (between first pair of ---)."""
    lines = file.read_text().splitlines()
    in_frontmatter = False
    result = []
    for line in lines:
        if line.strip() == "---":
            if in_frontmatter:
                break
            in_frontmatter = True
            continue
        if in_frontmatter:
            result.append(line)
    return "\n".join(result)


def get_content_after_frontmatter(file: Path) -> str:
    """Get content after YAML frontmatter (after the second --- line)."""
    lines = file.read_text().splitlines()
    count = 0
    result = []
    found = False
    for line in lines:
        if line.strip() == "---":
            count += 1
            if count == 2:
                found = True
                continue
        if found:
            result.append(line)
    return "\n".join(result)


def extract_section(content: str, start_pattern: str, end_pattern: str, max_lines: int = 80) -> str:
    """Extract a section of text between two patterns (for use in grep-like section extraction)."""
    lines = content.splitlines()
    result = []
    capturing = False
    for line in lines:
        if not capturing:
            if re.search(start_pattern, line, re.IGNORECASE):
                capturing = True
                result.append(line)
        else:
            if re.search(end_pattern, line, re.IGNORECASE) and len(result) > 1:
                break
            result.append(line)
            if len(result) >= max_lines:
                break
    return "\n".join(result)


def extract_protocol_section(file: Path, protocol_id: str) -> str:
    """Extract content of a <protocol id="...">...</protocol> section."""
    content = file.read_text()
    pattern = rf'<protocol id="{protocol_id}">.*?</protocol>'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else ""


def extract_template_section(file: Path, template_id: str) -> str:
    """Extract content of a <template id="...">...</template> section."""
    content = file.read_text()
    pattern = rf'<template id="{template_id}">.*?</template>'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else ""
