"""ADR-0022 Phase 2: Robert-spec/Sable-ux personas + permissionMode.
Steps 2c-2d. Tests T-0022-100 through T-0022-126."""

import re

import pytest

from conftest import (
    CLAUDE_DIR,
    CURSOR_DIR,
    PERMISSION_MODE_AGENTS,
    PROJECT_ROOT,
    READ_ONLY_AGENTS,
    SHARED_DIR,
)


# ═══ Step 2c: Robert-spec and Sable-ux Personas ═════════════════════


def test_T_0022_100_robert_spec_producer():
    text = (SHARED_DIR / "agents" / "robert-spec.md").read_text()
    has_producer = bool(
        re.search(r"writes to docs/product/", text, re.IGNORECASE)
        or re.search(r"spec writing", text, re.IGNORECASE)
        or re.search(r"discovery", text, re.IGNORECASE)
    )
    assert has_producer
    assert not re.search(r"DRIFT", text)
    assert not re.search(r"AMBIGUOUS", text)
    assert not re.search(r"acceptance criteria verdict", text, re.IGNORECASE)


def test_T_0022_101_sable_ux_producer():
    text = (SHARED_DIR / "agents" / "sable-ux.md").read_text()
    has_producer = bool(
        re.search(r"writes to docs/ux/", text, re.IGNORECASE)
        or re.search(r"design doc", text, re.IGNORECASE)
        or re.search(r"user flow", text, re.IGNORECASE)
    )
    assert has_producer
    assert not re.search(r"DRIFT", text)
    assert not re.search(r"MISSING", text)
    assert not re.search(r"acceptance criteria verdict", text, re.IGNORECASE)


def test_T_0022_102_robert_spec_frontmatter():
    fm = (CLAUDE_DIR / "agents" / "robert-spec.frontmatter.yml").read_text()
    assert "tools:" in fm
    assert "Read" in fm
    assert "Write" in fm
    assert "Edit" in fm
    assert "enforce-product-paths.sh" in fm


def test_T_0022_103_sable_ux_frontmatter():
    fm = (CLAUDE_DIR / "agents" / "sable-ux.frontmatter.yml").read_text()
    assert "tools:" in fm
    assert "Read" in fm
    assert "Write" in fm
    assert "Edit" in fm
    assert "enforce-ux-paths.sh" in fm


def test_T_0022_104_robert_spec_cursor_no_hooks():
    fm = (CURSOR_DIR / "agents" / "robert-spec.frontmatter.yml").read_text()
    assert "tools:" in fm
    assert "hooks:" not in fm


def test_T_0022_105_sable_ux_cursor_no_hooks():
    fm = (CURSOR_DIR / "agents" / "sable-ux.frontmatter.yml").read_text()
    assert "tools:" in fm
    assert "hooks:" not in fm


def test_T_0022_106_agent_system_new_agents():
    text = (SHARED_DIR / "rules" / "agent-system.md").read_text()
    assert "robert-spec" in text
    assert "sable-ux" in text


def test_T_0022_107_agent_system_table():
    text = (SHARED_DIR / "rules" / "agent-system.md").read_text()
    assert re.search(r"robert-spec", text, re.IGNORECASE)
    assert re.search(r"sable-ux", text, re.IGNORECASE)


def test_T_0022_108_skill_md_new_agents():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "robert-spec" in skill
    assert "sable-ux" in skill


def test_T_0022_109_robert_spec_name():
    fm = (CLAUDE_DIR / "agents" / "robert-spec.frontmatter.yml").read_text()
    name = [l for l in fm.splitlines() if l.startswith("name:")][0].split(":", 1)[1].strip()
    assert name == "robert-spec"


def test_T_0022_110_sable_ux_name():
    fm = (CLAUDE_DIR / "agents" / "sable-ux.frontmatter.yml").read_text()
    name = [l for l in fm.splitlines() if l.startswith("name:")][0].split(":", 1)[1].strip()
    assert name == "sable-ux"


def test_T_0022_111_robert_reviewer_unchanged():
    fm = (CLAUDE_DIR / "agents" / "robert.frontmatter.yml").read_text()
    assert "disallowedTools:" in fm
    assert "Write" in fm


def test_T_0022_112_sable_reviewer_unchanged():
    fm = (CLAUDE_DIR / "agents" / "sable.frontmatter.yml").read_text()
    assert "disallowedTools:" in fm
    assert "Write" in fm


def test_T_0022_113_pm_routing():
    text = (SHARED_DIR / "rules" / "agent-system.md").read_text()
    assert re.search(r"/pm.*robert-spec|robert-spec.*/pm", text)


def test_T_0022_114_ux_routing():
    text = (SHARED_DIR / "rules" / "agent-system.md").read_text()
    assert re.search(r"/ux.*sable-ux|sable-ux.*/ux", text)


def test_T_0022_115_robert_spec_no_qa():
    text = (SHARED_DIR / "agents" / "robert-spec.md").read_text()
    assert "last-qa-report" not in text


def test_T_0022_116_sable_ux_no_product():
    text = (SHARED_DIR / "agents" / "sable-ux.md").read_text()
    assert "docs/product/" not in text
    assert "last-qa-report" not in text


# ═══ Step 2d: permissionMode ════════════════════════════════════════


@pytest.mark.parametrize("agent", PERMISSION_MODE_AGENTS)
def test_T_0022_120_to_123_permission_mode(agent):
    fm = (CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml").read_text()
    assert "permissionMode: acceptEdits" in fm


def test_T_0022_124_no_cursor_permission_mode():
    for fm_file in (CURSOR_DIR / "agents").glob("*.frontmatter.yml"):
        assert "permissionMode" not in fm_file.read_text(), f"Found in {fm_file.name}"


@pytest.mark.parametrize("agent", READ_ONLY_AGENTS)
def test_T_0022_125_no_read_only_permission_mode(agent):
    fm_file = CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml"
    if fm_file.exists():
        assert "permissionMode" not in fm_file.read_text()


@pytest.mark.parametrize("agent", ["robert-spec", "sable-ux"])
def test_T_0022_126_producers_no_permission_mode(agent):
    fm_file = CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml"
    if fm_file.exists():
        assert "permissionMode" not in fm_file.read_text()
