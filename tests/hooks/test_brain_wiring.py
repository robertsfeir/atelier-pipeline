"""Tests for ADR-0021: Structural validation for brain wiring. Covers Steps 2a-2d, 4, 5a-5b, 6, cross-step."""

import re
import subprocess

import pytest
import yaml

from conftest import (
    PROJECT_ROOT,
    compare_with_placeholder_resolution,
    extract_frontmatter,
    run_hook_with_project_dir,
    write_pipeline_status,
)


# ── Helper ───────────────────────────────────────────────────────────────

def _extract_section(file_path, start_tag, end_tag):
    text = file_path.read_text()
    m = re.search(rf"({re.escape(start_tag)}.*?{re.escape(end_tag)})", text, re.DOTALL)
    return m.group(1) if m else ""


# ═══════════════════════════════════════════════════════════════════════
# Step 2a: Cal
# ═══════════════════════════════════════════════════════════════════════

BRAIN_AGENTS = [
    ("cal", "decision", "cal"),
    ("colby", "insight", "colby"),
    ("roz", "pattern", "roz"),
    ("agatha", "decision", "agatha"),
]


@pytest.mark.parametrize("agent,thought_type,source_agent", BRAIN_AGENTS)
def test_thought_type(agent, thought_type, source_agent):
    text = (PROJECT_ROOT / ".claude" / "agents" / f"{agent}.md").read_text()
    assert re.search(rf"thought_type.*{thought_type}|thought_type: '{thought_type}'|thought_type: \"{thought_type}\"", text)


@pytest.mark.parametrize("agent,thought_type,source_agent", BRAIN_AGENTS)
def test_source_agent(agent, thought_type, source_agent):
    text = (PROJECT_ROOT / ".claude" / "agents" / f"{agent}.md").read_text()
    assert re.search(rf"source_agent.*{source_agent}|source_agent: '{source_agent}'|source_agent: \"{source_agent}\"", text)


@pytest.mark.parametrize("agent,thought_type,source_agent", BRAIN_AGENTS)
def test_valid_yaml(agent, thought_type, source_agent):
    f = PROJECT_ROOT / ".claude" / "agents" / f"{agent}.md"
    fm = extract_frontmatter(f)
    yaml.safe_load(fm)


# Regression: Cal tools
def test_T_0021_022_cal_tools():
    fm = extract_frontmatter(PROJECT_ROOT / ".claude" / "agents" / "cal.md")
    assert "Read" in fm
    assert "Agent(roz)" in fm


def test_T_0021_023_cal_workflow():
    text = (PROJECT_ROOT / ".claude" / "agents" / "cal.md").read_text()
    assert "ADR Production" in text
    assert "Hard Gates" in text


# Regression: Colby tools
def test_T_0021_031_colby_tools():
    fm = extract_frontmatter(PROJECT_ROOT / ".claude" / "agents" / "colby.md")
    assert "Read" in fm
    assert "MultiEdit" in fm
    assert "Agent(roz, cal)" in fm


def test_T_0021_032_colby_workflow():
    text = (PROJECT_ROOT / ".claude" / "agents" / "colby.md").read_text()
    assert "Mockup Mode" in text
    assert re.search(r"Branch.*MR Mode|Branch & MR Mode", text)


# Regression: Roz
def test_T_0021_040_roz_disallowed():
    fm = extract_frontmatter(PROJECT_ROOT / ".claude" / "agents" / "roz.md")
    assert "Agent" in fm
    assert "Edit" in fm
    assert "MultiEdit" in fm
    assert "NotebookEdit" in fm


def test_T_0021_041_roz_workflow():
    text = (PROJECT_ROOT / ".claude" / "agents" / "roz.md").read_text()
    assert "Investigation Mode" in text
    assert "Code QA Mode" in text


# Regression: Agatha
def test_T_0021_049_agatha_disallowed():
    fm = extract_frontmatter(PROJECT_ROOT / ".claude" / "agents" / "agatha.md")
    assert "Agent" in fm
    assert "NotebookEdit" in fm


def test_T_0021_050_agatha_workflow():
    text = (PROJECT_ROOT / ".claude" / "agents" / "agatha.md").read_text()
    assert "Documentation Process" in text
    assert "Audience Types" in text


# ═══════════════════════════════════════════════════════════════════════
# Step 4: Preamble
# ═══════════════════════════════════════════════════════════════════════


def test_T_0021_063_source_preamble_matches():
    claude = PROJECT_ROOT / ".claude" / "references" / "agent-preamble.md"
    source = PROJECT_ROOT / "source" / "references" / "agent-preamble.md"
    if source.exists():
        assert compare_with_placeholder_resolution(claude, source)


def test_T_0021_064_preamble_step_order():
    text = (PROJECT_ROOT / ".claude" / "references" / "agent-preamble.md").read_text()
    assert "DoR first" in text
    assert "upstream artifacts" in text
    assert "retro lessons" in text
    assert re.search(r"brain context", text, re.IGNORECASE)
    assert "DoD last" in text
    dor = text.index("DoR first")
    dod = text.index("DoD last")
    assert dor < dod


def test_T_0021_065_ellis_no_old_brain_line():
    text = (PROJECT_ROOT / ".claude" / "agents" / "ellis.md").read_text()
    assert "Eva uses these to capture knowledge to the brain" not in text


def test_T_0021_066_invocation_templates():
    text = (PROJECT_ROOT / ".claude" / "references" / "invocation-templates.md").read_text()
    head = "\n".join(text.splitlines()[:60])
    assert re.search(r"brain-context", head, re.IGNORECASE)
    assert re.search(r"agent_capture|capture directly|capture independently", text, re.IGNORECASE)


def test_T_0021_067_source_invocation_templates():
    claude = PROJECT_ROOT / ".claude" / "references" / "invocation-templates.md"
    source = PROJECT_ROOT / "source" / "references" / "invocation-templates.md"
    if source.exists():
        assert compare_with_placeholder_resolution(claude, source)


def test_T_0021_118_preamble_updated():
    text = (PROJECT_ROOT / ".claude" / "references" / "agent-preamble.md").read_text()
    if "they do not call agent_search themselves" in text:
        assert re.search(r"capture directly|mcpServers|agent_capture|brain access", text, re.IGNORECASE)


def test_T_0021_119_ellis_still_mentions_brain():
    text = (PROJECT_ROOT / ".claude" / "agents" / "ellis.md").read_text()
    assert re.search(r"brain", text, re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════════════
# Step 5a: Dead prose cleanup
# ═══════════════════════════════════════════════════════════════════════


def test_T_0021_069_brain_config_four_agents():
    section = _extract_section(
        PROJECT_ROOT / ".claude" / "rules" / "agent-system.md",
        '<section id="brain-config">', '</section>',
    )
    for agent in ["Cal", "Colby", "Roz", "Agatha"]:
        assert re.search(agent, section, re.IGNORECASE)


def test_T_0021_071_no_mandatory_brain_access():
    text = (PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md").read_text()
    assert not re.search(r"Brain Access.*MANDATORY|MANDATORY.*Brain Access", text)


def test_T_0021_072_best_effort():
    text = (PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md").read_text()
    assert re.search(r"best-effort", text, re.IGNORECASE)


def test_T_0021_073_no_spot_check():
    text = (PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md").read_text()
    assert not re.search(r"Verification.*spot.check", text, re.IGNORECASE)


def test_T_0021_075_shared_behaviors_brain():
    section = _extract_section(
        PROJECT_ROOT / ".claude" / "rules" / "agent-system.md",
        '<section id="shared-behaviors">', '</section>',
    )
    assert re.search(r"brain context", section, re.IGNORECASE)


def test_T_0021_076_seed_devops():
    text = (PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md").read_text()
    assert "Seed Capture" in text
    assert re.search(r"devops Capture Gates|/devops Capture Gates", text)


def test_T_0021_077_tier1():
    text = (PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md").read_text()
    assert re.search(r"Tier 1", text, re.IGNORECASE)


def test_T_0021_078_source_agent_system():
    claude = PROJECT_ROOT / ".claude" / "rules" / "agent-system.md"
    source = PROJECT_ROOT / "source" / "rules" / "agent-system.md"
    if source.exists():
        cs = _extract_section(claude, '<section id="brain-config">', '</section>')
        ss = _extract_section(source, '<section id="brain-config">', '</section>')
        assert cs == ss


def test_T_0021_079_source_pipeline_orchestration():
    claude = PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md"
    source = PROJECT_ROOT / "source" / "rules" / "pipeline-orchestration.md"
    if source.exists():
        ch = [l for l in claude.read_text().splitlines() if "Brain Access" in l]
        sh = [l for l in source.read_text().splitlines() if "Brain Access" in l]
        assert ch and sh
        assert ch[0] == sh[0]


def test_T_0021_080_no_mandatory_telemetry():
    text = (PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md").read_text()
    assert not re.search(r"Telemetry Capture.*MANDATORY|MANDATORY.*Telemetry Capture", text)


def test_T_0021_111_seed_capture():
    assert "Seed Capture" in (PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md").read_text()


def test_T_0021_112_devops_capture():
    text = (PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md").read_text()
    assert re.search(r"devops Capture Gates|/devops Capture Gates", text)


# ═══════════════════════════════════════════════════════════════════════
# Step 5b
# ═══════════════════════════════════════════════════════════════════════


def test_T_0021_081_context_eviction_brain():
    text = (PROJECT_ROOT / ".claude" / "rules" / "default-persona.md").read_text()
    assert re.search(r"brain capture protocol|brain capture.*awareness|brain.*protocol.*awareness", text, re.IGNORECASE)


def test_T_0021_082_no_evict_telemetry():
    text = (PROJECT_ROOT / ".claude" / "rules" / "default-persona.md").read_text()
    assert "Telemetry trend computation logic" not in text


def test_T_0021_084_pipeline_models_best_effort():
    text = (PROJECT_ROOT / ".claude" / "rules" / "pipeline-models.md").read_text()
    assert re.search(r"best-effort", text, re.IGNORECASE)


def test_T_0021_085_pipeline_ops_prefetch():
    text = (PROJECT_ROOT / ".claude" / "references" / "pipeline-operations.md").read_text()
    assert "prompt-brain-prefetch.sh" in text


def test_T_0021_086_pipeline_ops_hybrid():
    text = (PROJECT_ROOT / ".claude" / "references" / "pipeline-operations.md").read_text()
    assert re.search(r"hybrid|agents with brain access|capture directly|self-capture|agents.*capture", text, re.IGNORECASE)


def test_T_0021_087_boot_steps():
    text = (PROJECT_ROOT / ".claude" / "rules" / "default-persona.md").read_text()
    assert "Brain health check" in text
    assert re.search(r"Brain context retrieval|context retrieval", text, re.IGNORECASE)


def test_T_0021_088_model_tables():
    text = (PROJECT_ROOT / ".claude" / "rules" / "pipeline-models.md").read_text()
    for word in ["opus", "sonnet", "haiku"]:
        assert re.search(word, text, re.IGNORECASE)


def test_T_0021_089_source_default_persona():
    claude = PROJECT_ROOT / ".claude" / "rules" / "default-persona.md"
    source = PROJECT_ROOT / "source" / "rules" / "default-persona.md"
    if source.exists():
        ce = _extract_section(claude, '<protocol id="context-eviction">', '</protocol>')
        se = _extract_section(source, '<protocol id="context-eviction">', '</protocol>')
        assert ce == se


def test_T_0021_090_source_pipeline_models():
    claude = PROJECT_ROOT / ".claude" / "rules" / "pipeline-models.md"
    source = PROJECT_ROOT / "source" / "rules" / "pipeline-models.md"
    if source.exists():
        import subprocess
        cb = subprocess.run(["grep", "-A5", "Brain Integration", str(claude)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        sb = subprocess.run(["grep", "-A5", "Brain Integration", str(source)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert cb.stdout == sb.stdout


def test_T_0021_091_source_pipeline_ops():
    claude = PROJECT_ROOT / ".claude" / "references" / "pipeline-operations.md"
    source = PROJECT_ROOT / "source" / "references" / "pipeline-operations.md"
    if source.exists():
        ce = _extract_section(claude, '<protocol id="brain-prefetch">', '</protocol>')
        se = _extract_section(source, '<protocol id="brain-prefetch">', '</protocol>')
        assert ce == se


def test_T_0021_113_boot_sequence():
    text = (PROJECT_ROOT / ".claude" / "rules" / "default-persona.md").read_text()
    assert "atelier_stats" in text
    assert "agent_search" in text


# ═══════════════════════════════════════════════════════════════════════
# Step 6: PostCompact Enhancement
# ═══════════════════════════════════════════════════════════════════════


def test_T_0021_092_brain_reminder(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nFeature: Hook modernization\nPhase: build\n")
    (hook_env / "docs" / "pipeline" / "context-brief.md").write_text("# Context\n\nWorking on hook changes.\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert "Pipeline State" in r.stdout
    assert re.search(r"[Bb]rain|capture", r.stdout)


def test_T_0021_093_three_mechanisms(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nFeature: Hook modernization\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert "prompt" in r.stdout or "hook" in r.stdout
    assert "agent" in r.stdout or "capture" in r.stdout
    assert "Eva" in r.stdout or "best-effort" in r.stdout or "cross-cutting" in r.stdout


def test_T_0021_094_brain_reminder_concise(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nFeature: Hook modernization\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    brain_lines = sum(
        1 for l in r.stdout.splitlines()
        if re.search(r"brain|capture.*agent|agent.*capture|prompt.*hook|hook.*prompt|best.effort|cross.cutting", l, re.IGNORECASE)
    )
    assert brain_lines < 10


def test_T_0021_095_state_before_brain(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nFeature: Hook modernization\n")
    (hook_env / "docs" / "pipeline" / "context-brief.md").write_text("# Context Brief\n\nWorking on hook modernization.\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert "Pipeline State" in r.stdout
    assert "Context Brief" in r.stdout


def test_T_0021_096_regression_state_and_brief(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nSCOPE_CHECK_PS\n")
    (hook_env / "docs" / "pipeline" / "context-brief.md").write_text("# Context Brief\n\nSCOPE_CHECK_CB\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert "SCOPE_CHECK_PS" in r.stdout
    assert "SCOPE_CHECK_CB" in r.stdout


def test_T_0021_097_missing_both_files(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink(missing_ok=True)
    (hook_env / "docs" / "pipeline" / "context-brief.md").unlink(missing_ok=True)
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0


def test_T_0021_098_unset_project_dir(hook_env):
    from conftest import run_hook_without_project_dir
    r = run_hook_without_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0


def test_T_0021_114_brain_reminder_present(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").write_text("# Pipeline State\n\nFeature: Test\n")
    r = run_hook_with_project_dir("post-compact-reinject.sh", "", hook_env)
    assert r.returncode == 0
    assert re.search(r"brain|capture", r.stdout, re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════════════
# Cross-step
# ═══════════════════════════════════════════════════════════════════════

def test_T_0021_108_non_brain_agents_no_mcpServers():
    for agent in ["robert", "sable", "investigator", "distillator", "sentinel", "darwin", "deps"]:
        f = PROJECT_ROOT / ".claude" / "agents" / f"{agent}.md"
        if f.exists():
            fm = extract_frontmatter(f)
            assert "atelier-brain" not in fm, f"{agent} should not have atelier-brain"
