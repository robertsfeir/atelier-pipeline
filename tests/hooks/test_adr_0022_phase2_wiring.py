"""ADR-0022 Phase 2: Frontmatter hooks wiring + monolith deletion, Eva routing + docs.
Steps 2e-2f. Tests T-0022-130 through T-0022-157."""

import re
import subprocess

import pytest

from conftest import (
    ALL_HOOK_SCRIPT_NAMES,
    CLAUDE_DIR,
    CURSOR_DIR,
    PROJECT_ROOT,
    SHARED_DIR,
)


# ═══ Step 2e: Frontmatter Hooks Wiring ══════════════════════════════


def test_T_0022_130_roz_hooks():
    fm = (CLAUDE_DIR / "agents" / "roz.frontmatter.yml").read_text()
    assert "hooks:" in fm
    assert "enforce-roz-paths.sh" in fm
    assert re.search(r"matcher:.*Write", fm)
    assert "PreToolUse" in fm


def test_T_0022_131_cal_hooks():
    fm = (CLAUDE_DIR / "agents" / "cal.frontmatter.yml").read_text()
    assert "hooks:" in fm
    assert "enforce-cal-paths.sh" in fm
    assert re.search(r"matcher:.*Write.*Edit|matcher:.*Write\|Edit", fm)
    assert "PreToolUse" in fm


def test_T_0022_132_colby_hooks():
    fm = (CLAUDE_DIR / "agents" / "colby.frontmatter.yml").read_text()
    assert "hooks:" in fm
    assert "enforce-colby-paths.sh" in fm
    assert re.search(r"matcher:.*Write.*Edit.*MultiEdit|matcher:.*Write\|Edit\|MultiEdit", fm)
    assert "PreToolUse" in fm


def test_T_0022_133_agatha_hooks():
    fm = (CLAUDE_DIR / "agents" / "agatha.frontmatter.yml").read_text()
    assert "hooks:" in fm
    assert "enforce-agatha-paths.sh" in fm
    assert re.search(r"matcher:.*Write.*Edit.*MultiEdit|matcher:.*Write\|Edit\|MultiEdit", fm)


def test_T_0022_134_robert_spec_hooks():
    fm = (CLAUDE_DIR / "agents" / "robert-spec.frontmatter.yml").read_text()
    assert "hooks:" in fm
    assert "enforce-product-paths.sh" in fm
    assert re.search(r"matcher:.*Write.*Edit|matcher:.*Write\|Edit", fm)


def test_T_0022_135_sable_ux_hooks():
    fm = (CLAUDE_DIR / "agents" / "sable-ux.frontmatter.yml").read_text()
    assert "hooks:" in fm
    assert "enforce-ux-paths.sh" in fm
    assert re.search(r"matcher:.*Write.*Edit|matcher:.*Write\|Edit", fm)


def test_T_0022_136_enforce_paths_deleted():
    assert not (CLAUDE_DIR / "hooks" / "enforce-paths.sh").exists()


def test_T_0022_137_enforce_paths_cursor_retained():
    assert (CURSOR_DIR / "hooks" / "enforce-paths.sh").exists()


def test_T_0022_137a_cursor_enforce_paths_complete():
    text = (CURSOR_DIR / "hooks" / "enforce-paths.sh").read_text()
    for pattern in ["cal)", "colby)", "roz)", "ellis)", "agatha)"]:
        assert pattern in text
    assert (CURSOR_DIR / "hooks" / "enforce-paths.sh").stat().st_mode & 0o111


def test_T_0022_138_skill_md_eva_paths():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "enforce-eva-paths.sh" in skill
    assert re.search(r"Write\|Edit\|MultiEdit|Write.*Edit.*MultiEdit", skill)


def test_T_0022_139_skill_md_no_enforce_paths():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    claude_refs = [
        l for l in skill.splitlines()
        if "enforce-paths.sh" in l and "cursor" not in l.lower()
        and ("settings.json" in l.lower() or "PreToolUse" in l or "matcher" in l.lower())
    ]
    assert claude_refs == []


@pytest.mark.parametrize("hook_name", ALL_HOOK_SCRIPT_NAMES)
def test_T_0022_140_skill_md_per_agent_scripts(hook_name):
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert hook_name in skill


def test_T_0022_141_no_claude_overlay_enforce_paths():
    for fm in (CLAUDE_DIR / "agents").glob("*.frontmatter.yml"):
        assert "enforce-paths.sh" not in fm.read_text(), f"Found in {fm.name}"


def test_T_0022_142_cursor_hooks_json_enforce_paths():
    text = (CURSOR_DIR / "hooks" / "hooks.json").read_text()
    assert "enforce-paths" in text


def test_T_0022_143_cross_cutting_hooks():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "enforce-sequencing.sh" in skill
    assert "enforce-pipeline-activation.sh" in skill
    assert "enforce-git.sh" in skill


def test_T_0022_144_lifecycle_hooks():
    # warn-dor-dod.sh and prompt-brain-capture.sh were deprecated (ADR-0024).
    # Check currently deployed lifecycle hooks instead.
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "log-agent-start.sh" in skill
    assert "log-agent-stop.sh" in skill
    assert "session-hydrate.sh" in skill
    assert "prompt-brain-prefetch.sh" in skill


def test_T_0022_145_ellis_hooks():
    # Ellis now has path enforcement -- gap closed by enforce-ellis-paths.sh
    fm = (CLAUDE_DIR / "agents" / "ellis.frontmatter.yml").read_text()
    assert "hooks:" in fm
    assert "enforce-ellis-paths.sh" in fm
    assert re.search(r"matcher:.*Write.*Edit.*MultiEdit|matcher:.*Write\|Edit\|MultiEdit", fm)
    assert "PreToolUse" in fm


# ═══ Step 2f: Eva Routing + Documentation ════════════════════════════


def test_T_0022_150_persona_docs_pipeline():
    text = (SHARED_DIR / "rules" / "default-persona.md").read_text()
    assert "docs/pipeline" in text


def test_T_0022_151_persona_no_product_ux():
    text = (SHARED_DIR / "rules" / "default-persona.md").read_text()
    # Extract "Eva may" section
    result = subprocess.run(
        ["sed", "-n", "/Eva may/,/Eva must.*NEVER/p", str(SHARED_DIR / "rules" / "default-persona.md")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    may_section = result.stdout
    assert "docs/product/" not in may_section
    assert "docs/ux/" not in may_section


def test_T_0022_152_pm_md_robert_spec():
    text = (SHARED_DIR / "commands" / "pm.md").read_text()
    assert re.search(r"robert-spec", text, re.IGNORECASE)


def test_T_0022_153_ux_md_sable_ux():
    text = (SHARED_DIR / "commands" / "ux.md").read_text()
    assert re.search(r"sable-ux", text, re.IGNORECASE)


# removed by ADR-0045 — asserted deleted feature
# test_T_0022_154_create_agent_per_agent


def test_T_0022_155_tech_ref_pyramid():
    text = (PROJECT_ROOT / "docs" / "guide" / "technical-reference.md").read_text()
    assert re.search(r"layer|pyramid|enforcement", text, re.IGNORECASE)
    assert re.search(r"per-agent|frontmatter.*hook", text, re.IGNORECASE)


def test_T_0022_156_no_enforce_paths_in_docs():
    found = []
    for search_path in [SHARED_DIR, CLAUDE_DIR, PROJECT_ROOT / "docs" / "guide", PROJECT_ROOT / "CLAUDE.md"]:
        if search_path.is_file():
            if "enforce-paths.sh" in search_path.read_text():
                found.append(str(search_path))
        elif search_path.is_dir():
            result = subprocess.run(["grep", "-rl", "enforce-paths.sh", str(search_path)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if result.stdout.strip():
                found.extend(result.stdout.strip().splitlines())
    assert found == []


def test_T_0022_156a_cursor_retains_enforce_paths():
    result = subprocess.run(["grep", "-rl", "enforce-paths.sh", str(CURSOR_DIR)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert result.returncode == 0
    assert result.stdout.strip()


def test_T_0022_157_claude_md_roster():
    text = (PROJECT_ROOT / "CLAUDE.md").read_text()
    assert re.search(r"agent", text, re.IGNORECASE)
    assert re.search(r"robert-spec|sable-ux", text)
