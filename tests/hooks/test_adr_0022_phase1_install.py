"""ADR-0022 Phase 1: Pipeline-setup, documentation, validation.
Steps 1d-1f. Tests T-0022-030 through T-0022-058."""

import re
import subprocess

import pytest

from conftest import (
    AGENTS_12,
    CLAUDE_DIR,
    CURSOR_DIR,
    PROJECT_ROOT,
    SHARED_DIR,
    SOURCE_AGENTS,
    SOURCE_COMMANDS,
    SOURCE_DASHBOARD,
    SOURCE_DIR,
    SOURCE_HOOKS,
    SOURCE_PIPELINE,
    SOURCE_REFERENCES,
    SOURCE_RULES,
    SOURCE_VARIANTS,
    assemble_agent,
)


# ═══ Step 1d: /pipeline-setup install logic ══════════════════════════


def test_T_0022_030_skill_md_shared():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "source/shared/" in skill


def test_T_0022_031_skill_md_shared_claude():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert re.search(r"source/shared/.*\.claude|\.claude.*source/shared/", skill)


def test_T_0022_032_skill_md_overlay():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    found = ("frontmatter" in skill and "content" in skill) or ("overlay" in skill and "assembl" in skill)
    assert found


def test_T_0022_033_cursor_detection():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "CURSOR_PROJECT_DIR" in skill


def test_T_0022_033a_claude_overlays(tmp_path):
    output = tmp_path / "colby_claude.md"
    assert assemble_agent("claude", "colby", output)
    assert output.exists()
    assert (CLAUDE_DIR / "agents" / "colby.frontmatter.yml").exists()


def test_T_0022_033b_cursor_overlays(tmp_path):
    output = tmp_path / "colby_cursor.md"
    assert assemble_agent("cursor", "colby", output)
    assert output.exists()
    assert (CURSOR_DIR / "agents" / "colby.frontmatter.yml").exists()


def test_T_0022_033c_cursor_precedence():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "CURSOR_PROJECT_DIR" in skill


def test_T_0022_033d_claude_hooks_cursor_no_hooks():
    claude_fm = (CLAUDE_DIR / "agents" / "colby.frontmatter.yml").read_text()
    cursor_fm = (CURSOR_DIR / "agents" / "colby.frontmatter.yml").read_text()
    assert "hooks:" in claude_fm
    assert "hooks:" not in cursor_fm


def test_T_0022_034_missing_overlay(tmp_path):
    output = tmp_path / "nonexistent_assembled.md"
    assert not assemble_agent("claude", "nonexistent-agent", output)
    assert not output.exists() or output.stat().st_size == 0


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_034a_deterministic_assembly(agent, tmp_path):
    a1 = tmp_path / f"{agent}_asm1.md"
    a2 = tmp_path / f"{agent}_asm2.md"
    assert assemble_agent("claude", agent, a1)
    assert assemble_agent("claude", agent, a2)
    assert a1.read_text() == a2.read_text()


def test_T_0022_035_skill_md_install_count():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert re.search(r"install|Install|INSTALL", skill)


def test_T_0022_036_cursor_sync():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert re.search(r"source/cursor|cursor.*hooks|\.cursor", skill)


def test_T_0022_037_cursor_skill_mirrors():
    cursor_skill = PROJECT_ROOT / ".cursor-plugin" / "skills" / "pipeline-setup" / "SKILL.md"
    assert cursor_skill.exists()
    text = cursor_skill.read_text()
    assert re.search(r"source/shared|source/cursor", text)


# ═══ Step 1e: Documentation and Path References ═════════════════════


def test_T_0022_040_claude_md():
    text = (PROJECT_ROOT / "CLAUDE.md").read_text()
    assert "source/shared/" in text
    assert "source/claude/" in text
    assert "source/cursor/" in text


def test_T_0022_041_test_helper_hooks_dir():
    helper = PROJECT_ROOT / "tests" / "hooks" / "test_helper.bash"
    if helper.exists():
        assert "source/claude/hooks" in helper.read_text()


def test_T_0022_043_no_flat_agents_in_docs():
    # Use concatenation to avoid self-matching by cleanup tests (T-0022-164/165)
    flat_agents = "source/" + "agents/"
    result = subprocess.run(
        ["grep", "-r", flat_agents,
         str(PROJECT_ROOT / "CLAUDE.md"),
         str(PROJECT_ROOT / "README.md"),
         str(PROJECT_ROOT / "docs")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30,
    )
    stale = [l for l in result.stdout.splitlines()
             if "source/shared/agents" not in l and "source/claude/agents" not in l
             and "source/cursor/agents" not in l and "ADR-0022" not in l]
    assert stale == []


def test_T_0022_044_no_flat_hooks_in_docs():
    # Use concatenation to avoid self-matching by cleanup tests (T-0022-164/166)
    flat_hooks = "source/" + "hooks/"
    result = subprocess.run(
        ["grep", "-r", flat_hooks,
         str(PROJECT_ROOT / "CLAUDE.md"),
         str(PROJECT_ROOT / "README.md"),
         str(PROJECT_ROOT / "docs"),
         str(PROJECT_ROOT / "tests" / "hooks" / "test_helper.bash") if (PROJECT_ROOT / "tests" / "hooks" / "test_helper.bash").exists() else "/dev/null"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30,
    )
    stale = [l for l in result.stdout.splitlines()
             if "source/claude/hooks" not in l and "source/cursor/hooks" not in l and "ADR-0022" not in l]
    assert stale == []


def test_T_0022_045_readme_no_old_paths():
    readme = (PROJECT_ROOT / "README.md").read_text()
    flat_pattern = "source/" + r"agents/|source/" + r"hooks/|source/" + r"commands/|source/" + r"references/"
    result = subprocess.run(
        ["grep", "-E", flat_pattern],
        input=readme, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    stale = [l for l in result.stdout.splitlines()
             if "source/shared/" not in l and "source/claude/" not in l and "source/cursor/" not in l]
    assert stale == []


# ═══ Step 1f: Phase 1 Validation ════════════════════════════════════


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_050_validate_claude(agent, tmp_path):
    output = tmp_path / f"{agent}_validate.md"
    assert assemble_agent("claude", agent, output)
    text = output.read_text()
    # Extract frontmatter region
    lines = text.splitlines()
    in_fm = False
    fm_lines = []
    for l in lines:
        if l.strip() == "---":
            if in_fm:
                break
            in_fm = True
            continue
        if in_fm:
            fm_lines.append(l)
    assert fm_lines


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_051_validate_cursor(agent, tmp_path):
    output = tmp_path / f"{agent}_cursor_validate.md"
    assert assemble_agent("cursor", agent, output)
    lines = output.read_text().splitlines()
    in_fm = False
    fm_lines = []
    for l in lines:
        if l.strip() == "---":
            if in_fm:
                break
            in_fm = True
            continue
        if in_fm:
            fm_lines.append(l)
    assert fm_lines


def test_T_0022_052_all_dirs():
    for d in ["agents", "commands", "references", "pipeline", "rules", "variants", "dashboard"]:
        assert (SHARED_DIR / d).is_dir()
    assert (CLAUDE_DIR / "agents").is_dir()
    assert (CLAUDE_DIR / "hooks").is_dir()
    assert (CURSOR_DIR / "agents").is_dir()
    assert (CURSOR_DIR / "hooks").is_dir()


def test_T_0022_053_deprecated_paths():
    for d in [SOURCE_AGENTS, SOURCE_HOOKS, SOURCE_COMMANDS, SOURCE_REFERENCES, SOURCE_PIPELINE, SOURCE_RULES, SOURCE_VARIANTS, SOURCE_DASHBOARD]:
        assert not d.exists()


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_054_no_delimiters_in_frontmatter(agent):
    fm = (CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml").read_text()
    assert fm.splitlines()[0] != "---"
    assert "---" not in [l.strip() for l in fm.splitlines()]


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_055_no_frontmatter_in_shared(agent):
    content = (SHARED_DIR / "agents" / f"{agent}.md").read_text()
    assert content.splitlines()[0] != "---"


def test_T_0022_056_no_injection():
    found = []
    for fm_file in list((CLAUDE_DIR / "agents").glob("*.frontmatter.yml")) + list((CURSOR_DIR / "agents").glob("*.frontmatter.yml")):
        text = fm_file.read_text()
        if re.search(r"\$\(|`|^eval |^exec |!!", text, re.MULTILINE):
            found.append(fm_file.name)
    assert found == []


def test_T_0022_057_total_file_count():
    count = sum(1 for _ in SOURCE_DIR.rglob("*") if _.is_file())
    assert count >= 80


@pytest.mark.parametrize("agent", ["robert-spec", "sable-ux"])
def test_T_0022_058_producer_agents(agent, tmp_path):
    output = tmp_path / f"{agent}_assembled.md"
    assert assemble_agent("claude", agent, output)
    assert output.exists()
    lines = output.read_text().splitlines()
    assert lines[0] == "---"
    assert sum(1 for l in lines if l.strip() == "---") >= 2
    fm = (CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml").read_text()
    assert "name:" in fm
    assert "description:" in fm
    assert "model:" in fm
    assert "tools:" in fm
    assert (SHARED_DIR / "agents" / f"{agent}.md").stat().st_size > 0
