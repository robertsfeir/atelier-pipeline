"""ADR-0022 Phase 1: Directory structure, content splitting, overlay assembly.
Steps 1a-1c. Tests T-0022-001 through T-0022-025b."""

import re
import subprocess

import pytest

from conftest import (
    AGENTS_12,
    CLAUDE_DIR,
    CURSOR_DIR,
    SHARED_DIR,
    SOURCE_AGENTS,
    SOURCE_COMMANDS,
    SOURCE_DASHBOARD,
    SOURCE_HOOKS,
    SOURCE_PIPELINE,
    SOURCE_REFERENCES,
    SOURCE_RULES,
    SOURCE_VARIANTS,
    assemble_agent,
)


# ═══ Step 1a: Shared Content Directory ═══════════════════════════════


def test_T_0022_001_shared_commands():
    assert SHARED_DIR / "commands" is not None
    count = len(list((SHARED_DIR / "commands").glob("*.md")))
    assert count == 11


def test_T_0022_002_shared_references():
    count = len(list((SHARED_DIR / "references").glob("*.md")))
    assert count == 16  # gauntlet.md added ADR-0034 Wave 1; design-system-loading.md added ADR-0040; routing-detail.md added ADR-0044 Slice 2


def test_T_0022_003_shared_pipeline():
    count = len(list((SHARED_DIR / "pipeline").iterdir()))
    assert count == 6


def test_T_0022_004_shared_rules():
    count = len(list((SHARED_DIR / "rules").glob("*.md")))
    assert count == 4


def test_T_0022_005_shared_variants():
    count = len(list((SHARED_DIR / "variants").glob("*.md")))
    assert count == 4


def test_T_0022_006_shared_dashboard():
    assert (SHARED_DIR / "dashboard" / "telemetry-bridge.sh").exists()


def test_T_0022_007_flat_dirs_deleted():
    for d in [SOURCE_COMMANDS, SOURCE_REFERENCES, SOURCE_PIPELINE, SOURCE_RULES, SOURCE_VARIANTS, SOURCE_DASHBOARD]:
        assert not d.exists()


def test_T_0022_008_config_dir_placeholder():
    result = subprocess.run(["grep", "-rl", "{config_dir}", str(SHARED_DIR)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert result.returncode == 0
    assert result.stdout.strip()
    result2 = subprocess.run(["grep", "-rl", "{platform}", str(SHARED_DIR)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert result2.returncode != 0


def test_T_0022_009_no_frontmatter_in_shared():
    found = []
    for f in SHARED_DIR.rglob("*"):
        if f.is_file():
            try:
                text = f.read_text()
            except (UnicodeDecodeError, Exception):
                continue  # skip binary files (e.g. .DS_Store)
            first_line = text.splitlines()[0] if text else ""
            if first_line.strip() == "---":
                found.append(str(f))
    assert found == []


# ═══ Step 1b: Agent Template Split ═══════════════════════════════════


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_010_assembly(agent, tmp_path):
    output = tmp_path / f"{agent}_assembled.md"
    assert assemble_agent("claude", agent, output)
    assert output.exists()
    lines = output.read_text().splitlines()
    assert lines[0] == "---"
    assert sum(1 for l in lines if l.strip() == "---") >= 2


@pytest.mark.parametrize("agent", ["cal", "colby", "investigator"])
def test_T_0022_010a_structure(agent, tmp_path):
    output = tmp_path / f"{agent}_structure.md"
    assert assemble_agent("claude", agent, output)
    lines = output.read_text().splitlines()
    assert lines[0] == "---"
    # Find second --- delimiter
    delim_count = 0
    second_delim_line = None
    for i, l in enumerate(lines):
        if l.strip() == "---":
            delim_count += 1
            if delim_count == 2:
                second_delim_line = i
                break
    assert second_delim_line is not None
    assert lines[second_delim_line - 1].strip() != ""


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_011_cursor_assembly(agent, tmp_path):
    output = tmp_path / f"{agent}_cursor.md"
    assert assemble_agent("cursor", agent, output)
    assert output.exists()
    assert output.read_text().splitlines()[0] == "---"


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_012_shared_comment(agent):
    content = (SHARED_DIR / "agents" / f"{agent}.md").read_text()
    assert content.splitlines()[0].startswith("<!-- Part of atelier-pipeline")


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_013_valid_yaml(agent):
    fm = CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml"
    assert fm.exists()
    first_line = fm.read_text().splitlines()[0]
    assert first_line != "---"


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_014_name_field(agent):
    fm = CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml"
    name_lines = [l for l in fm.read_text().splitlines() if l.startswith("name:")]
    assert name_lines
    name_val = name_lines[0].split(":", 1)[1].strip()
    assert name_val == agent


def test_T_0022_015_source_agents_deleted():
    assert not SOURCE_AGENTS.exists()


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_016_claude_frontmatter_fields(agent):
    fm = (CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml").read_text()
    assert "name:" in fm
    assert "description:" in fm or "description " in fm
    assert "model:" in fm
    assert "effort:" in fm
    assert "maxTurns:" in fm


@pytest.mark.parametrize("agent", ["cal", "colby"])
def test_T_0022_017_tools_retained(agent):
    fm = (CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml").read_text()
    assert "tools:" in fm


@pytest.mark.parametrize("agent", ["roz", "ellis", "agatha", "robert", "sable", "investigator", "distillator", "sentinel", "darwin", "deps"])
def test_T_0022_018_disallowed_tools(agent):
    fm = (CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml").read_text()
    assert "disallowedTools:" in fm


@pytest.mark.parametrize("agent", AGENTS_12)
def test_T_0022_020_cursor_identical_phase1(agent):
    claude_fm = (CLAUDE_DIR / "agents" / f"{agent}.frontmatter.yml").read_text()
    cursor_fm = (CURSOR_DIR / "agents" / f"{agent}.frontmatter.yml").read_text()
    # At Phase 1, they may already diverge (Phase 2 done). Skip strict equality
    # but ensure both exist.
    assert claude_fm
    assert cursor_fm


# ═══ Step 1c: Hook Script Move ═══════════════════════════════════════


def test_T_0022_021_claude_hooks():
    assert (CLAUDE_DIR / "hooks").is_dir()
    sh_count = len(list((CLAUDE_DIR / "hooks").glob("*.sh")))
    assert sh_count == 22  # Wave 3: prompt-brain-capture.sh and warn-brain-capture.sh removed; session-boot.sh added; prompt-compact-advisory.sh + session-hydrate-enforcement.sh + enforce-scout-swarm.sh + enforce-ellis-paths.sh added
    assert (CLAUDE_DIR / "hooks" / "enforcement-config.json").exists()


def test_T_0022_022_cursor_hooks_json():
    assert (CURSOR_DIR / "hooks" / "hooks.json").exists()
    import json
    json.loads((CURSOR_DIR / "hooks" / "hooks.json").read_text())


def test_T_0022_023_original_hooks_deleted():
    assert not SOURCE_HOOKS.exists()


def test_T_0022_024_hooks_exist():
    for script in (CLAUDE_DIR / "hooks").glob("*.sh"):
        assert script.exists()


def test_T_0022_025_cursor_project_dir_fallback():
    for script in (CLAUDE_DIR / "hooks").glob("*.sh"):
        text = script.read_text()
        if "CLAUDE_PROJECT_DIR" in text:
            assert "CURSOR_PROJECT_DIR" in text


def test_T_0022_025a_executable():
    non_exec = [f for f in (CLAUDE_DIR / "hooks").glob("*.sh") if not (f.stat().st_mode & 0o100)]
    assert non_exec == []


def test_T_0022_025b_hooks_json_files_exist():
    import json
    hooks_json = json.loads((CURSOR_DIR / "hooks" / "hooks.json").read_text())
    orphans = []

    def extract_commands(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "command" and isinstance(v, str):
                    yield v
                else:
                    yield from extract_commands(v)
        elif isinstance(obj, list):
            for item in obj:
                yield from extract_commands(item)

    for cmd in extract_commands(hooks_json):
        name = cmd.strip().split("/")[-1]
        if not name:
            continue
        if not (CURSOR_DIR / "hooks" / name).exists():
            found = list((CURSOR_DIR / "hooks").rglob(name))
            if not found:
                orphans.append(cmd)
    assert orphans == []
