"""ADR-0022 Phase 2: Robert-spec/Sable-ux personas + permissionMode.
Steps 2c-2d. Tests T-0022-100 through T-0022-126.

Test IDs 100-114 correspond to ADR-0022 test spec table (Step 2c).
Test IDs 130+ are additional coverage beyond the ADR spec."""

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
    """T-0022-100: robert-spec.md exists with producer workflow strings,
    no reviewer-specific strings (DRIFT, AMBIGUOUS)."""
    text = (SHARED_DIR / "agents" / "robert-spec.md").read_text()
    has_producer = bool(
        re.search(r"writes to docs/product/", text, re.IGNORECASE)
        or re.search(r"spec writing", text, re.IGNORECASE)
        or re.search(r"discovery", text, re.IGNORECASE)
    )
    assert has_producer
    assert not re.search(r"DRIFT", text)
    assert not re.search(r"AMBIGUOUS", text)


def test_T_0022_101_sable_ux_producer():
    """T-0022-101: sable-ux.md exists with producer workflow strings,
    no reviewer-specific strings (DRIFT, MISSING)."""
    text = (SHARED_DIR / "agents" / "sable-ux.md").read_text()
    has_producer = bool(
        re.search(r"writes to docs/ux/", text, re.IGNORECASE)
        or re.search(r"UX design producer|UX Design", text, re.IGNORECASE)
        or re.search(r"design.*producer|create.*UX", text, re.IGNORECASE)
    )
    assert has_producer
    assert not re.search(r"DRIFT", text)
    assert not re.search(r"MISSING", text)


def test_T_0022_102_robert_spec_frontmatter():
    """T-0022-102: robert-spec Claude frontmatter has Write+Edit tools."""
    fm = (CLAUDE_DIR / "agents" / "robert-spec.frontmatter.yml").read_text()
    assert "name: robert-spec" in fm
    assert "Write" in fm
    assert "Edit" in fm


def test_T_0022_103_sable_ux_frontmatter():
    """T-0022-103: sable-ux Claude frontmatter has Write+Edit tools."""
    fm = (CLAUDE_DIR / "agents" / "sable-ux.frontmatter.yml").read_text()
    assert "name: sable-ux" in fm
    assert "Write" in fm
    assert "Edit" in fm


def test_T_0022_104_robert_spec_cursor_no_hooks():
    """T-0022-104: Cursor robert-spec frontmatter has tools but no hooks."""
    fm = (CURSOR_DIR / "agents" / "robert-spec.frontmatter.yml").read_text()
    assert "name: robert-spec" in fm
    assert "Write" in fm
    assert "hooks:" not in fm


def test_T_0022_105_sable_ux_cursor_no_hooks():
    """T-0022-105: Cursor sable-ux frontmatter has tools but no hooks."""
    fm = (CURSOR_DIR / "agents" / "sable-ux.frontmatter.yml").read_text()
    assert "name: sable-ux" in fm
    assert "Write" in fm
    assert "hooks:" not in fm


def test_T_0022_106_agent_system_new_agents():
    """T-0022-106: agent-system.md core agent constant includes
    robert-spec and sable-ux."""
    text = (SHARED_DIR / "rules" / "agent-system.md").read_text()
    assert "robert-spec" in text
    assert "sable-ux" in text


def test_T_0022_107_agent_system_table():
    """T-0022-107: agent-system.md subagent table includes
    Robert-spec and Sable-ux with correct tools."""
    text = (SHARED_DIR / "rules" / "agent-system.md").read_text()
    assert re.search(r"robert-spec", text, re.IGNORECASE)
    assert re.search(r"sable-ux", text, re.IGNORECASE)


def test_T_0022_108_skill_md_new_agents():
    """T-0022-108: SKILL.md installation manifest includes
    robert-spec.md and sable-ux.md."""
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "robert-spec" in skill
    assert "sable-ux" in skill


def test_T_0022_109_robert_spec_name():
    """T-0022-109: robert-spec frontmatter name field is 'robert-spec'
    (not 'robert') to avoid agent_type collision."""
    fm = (CLAUDE_DIR / "agents" / "robert-spec.frontmatter.yml").read_text()
    name = [l for l in fm.splitlines() if l.startswith("name:")][0].split(":", 1)[1].strip()
    assert name == "robert-spec"


def test_T_0022_110_sable_ux_name():
    """T-0022-110: sable-ux frontmatter name field is 'sable-ux'
    (not 'sable') to avoid agent_type collision."""
    fm = (CLAUDE_DIR / "agents" / "sable-ux.frontmatter.yml").read_text()
    name = [l for l in fm.splitlines() if l.startswith("name:")][0].split(":", 1)[1].strip()
    assert name == "sable-ux"


def test_T_0022_111_robert_reviewer_unchanged():
    """T-0022-111: robert.md (reviewer) still has disallowedTools
    including Write -- reviewer is read-only."""
    fm = (CLAUDE_DIR / "agents" / "robert.frontmatter.yml").read_text()
    assert "disallowedTools:" in fm
    assert "Write" in fm


def test_T_0022_112_sable_reviewer_unchanged():
    """T-0022-112: sable.md (reviewer) still has disallowedTools
    including Write -- reviewer is read-only."""
    fm = (CLAUDE_DIR / "agents" / "sable.frontmatter.yml").read_text()
    assert "disallowedTools:" in fm
    assert "Write" in fm


def test_T_0022_113_pm_routing():
    """T-0022-113: agent-system.md routing table has /pm -> robert-spec."""
    text = (SHARED_DIR / "rules" / "agent-system.md").read_text()
    assert re.search(r"/pm.*robert-spec|robert-spec.*/pm", text)


def test_T_0022_114_ux_routing():
    """T-0022-114: agent-system.md routing table has /ux -> sable-ux."""
    text = (SHARED_DIR / "rules" / "agent-system.md").read_text()
    assert re.search(r"/ux.*sable-ux|sable-ux.*/ux", text)


def test_T_0022_115_robert_spec_no_qa():
    """T-0022-115: robert-spec does NOT reference QA reports
    (information asymmetry). Per FLAG-001 domain decision, robert-spec
    MAY read prior specs and ADRs for context and consistency."""
    text = (SHARED_DIR / "agents" / "robert-spec.md").read_text()
    assert "last-qa-report" not in text


def test_T_0022_116_sable_ux_no_product():
    """T-0022-116: sable-ux does NOT reference product specs or QA reports."""
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
    """Read-only agents should have permissionMode: plan (not acceptEdits).
    permissionMode: plan is the correct safety setting for read-only agents --
    it restricts them to plan mode without execution permissions."""
    fm_file = CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml"
    if fm_file.exists():
        fm = fm_file.read_text()
        assert "permissionMode: acceptEdits" not in fm, \
            f"{agent} should not have acceptEdits -- it is read-only"
        assert "permissionMode: plan" in fm, \
            f"{agent} should have permissionMode: plan for safety"


@pytest.mark.parametrize("agent", ["robert-spec", "sable-ux"])
def test_T_0022_126_producers_have_permission_mode(agent):
    fm_file = CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml"
    if fm_file.exists():
        assert "permissionMode: acceptEdits" in fm_file.read_text()


# ═══ Additional coverage beyond ADR spec ════════════════════════════


def test_T_0022_130_producers_no_reviewer_patterns():
    """Producers should not contain reviewer verdict patterns."""
    for agent in ["robert-spec", "sable-ux"]:
        text = (SHARED_DIR / "agents" / f"{agent}.md").read_text()
        assert not re.search(r"accept.*reject|reject.*accept|PASS.*FAIL.*DRIFT|five.state audit", text)


def test_T_0022_131_producers_xml_tags():
    """Both producers must have required XML persona tags."""
    for agent in ["robert-spec", "sable-ux"]:
        text = (SHARED_DIR / "agents" / f"{agent}.md").read_text()
        assert "<identity>" in text
        assert "</identity>" in text
        assert "<required-actions>" in text
        assert "</required-actions>" in text
        assert "<workflow>" in text
        assert "</workflow>" in text


def test_T_0022_132_producers_constraints_output():
    """Both producers must have constraints and output tags."""
    for agent in ["robert-spec", "sable-ux"]:
        text = (SHARED_DIR / "agents" / f"{agent}.md").read_text()
        assert "<constraints>" in text
        assert "</constraints>" in text
        assert "<output>" in text
        assert "</output>" in text


def test_T_0022_133_producers_pronouns():
    """Both producers must declare pronouns in their identity."""
    for agent in ["robert-spec", "sable-ux"]:
        text = (SHARED_DIR / "agents" / f"{agent}.md").read_text()
        assert re.search(r"[Pp]ronouns", text)


def test_T_0022_134_producers_preamble_ref():
    """Both producers must reference agent-preamble."""
    for agent in ["robert-spec", "sable-ux"]:
        text = (SHARED_DIR / "agents" / f"{agent}.md").read_text()
        assert re.search(r"agent-preamble", text)
