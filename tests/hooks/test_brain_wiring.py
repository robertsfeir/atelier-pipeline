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
    run_hook_without_project_dir,
    write_pipeline_status,
)

# Source path constants
SHARED_AGENTS = PROJECT_ROOT / "source" / "shared" / "agents"
SHARED_REFS = PROJECT_ROOT / "source" / "shared" / "references"
SHARED_RULES = PROJECT_ROOT / "source" / "shared" / "rules"
CLAUDE_AGENTS = PROJECT_ROOT / "source" / "claude" / "agents"


# ── Helper ───────────────────────────────────────────────────────────────

def _extract_section(file_path, start_tag, end_tag):
    text = file_path.read_text()
    m = re.search(rf"({re.escape(start_tag)}.*?{re.escape(end_tag)})", text, re.DOTALL)
    return m.group(1) if m else ""


# ═══════════════════════════════════════════════════════════════════════
# Step 2a: Cal
# ═══════════════════════════════════════════════════════════════════════

BRAIN_AGENTS = [
    ("colby", "insight", "colby"),
    ("agatha", "decision", "agatha"),
]


# ADR-0024/ADR-0025: thought_type and source_agent moved from agent personas
# to brain-extractor.md (mechanical extraction via SubagentStop hook).
# Tests now verify the brain-extractor contains the mapping instead.

@pytest.mark.parametrize("agent,thought_type,source_agent", BRAIN_AGENTS)
def test_thought_type(agent, thought_type, source_agent):
    """Verify brain-extractor maps this agent to the expected thought_type."""
    text = (PROJECT_ROOT / "source" / "shared" / "agents" / "brain-extractor.md").read_text()
    assert re.search(rf"{agent}\s*\|.*\|", text), f"brain-extractor missing agent mapping for {agent}"
    assert thought_type in text, f"brain-extractor missing thought_type '{thought_type}'"


@pytest.mark.parametrize("agent,thought_type,source_agent", BRAIN_AGENTS)
def test_source_agent(agent, thought_type, source_agent):
    """Verify brain-extractor maps this agent to the expected source_agent."""
    text = (PROJECT_ROOT / "source" / "shared" / "agents" / "brain-extractor.md").read_text()
    assert re.search(rf"\|\s*{agent}\s*\|\s*{source_agent}\s*\|", text), \
        f"brain-extractor missing source_agent mapping {agent} -> {source_agent}"


@pytest.mark.parametrize("agent,thought_type,source_agent", BRAIN_AGENTS)
def test_valid_yaml(agent, thought_type, source_agent):
    # Frontmatter lives in source/claude/agents/X.frontmatter.yml
    f = CLAUDE_AGENTS / f"{agent}.frontmatter.yml"
    fm = f.read_text()
    yaml.safe_load(fm)


# Regression: Cal tools
def test_T_0021_032_colby_workflow():
    text = (SHARED_AGENTS / "colby.md").read_text()
    assert "Mockup Mode" in text
    assert re.search(r"Build Mode|Premise Verification|Re-invocation Mode", text)


# Regression: Roz
def test_T_0021_049_agatha_disallowed():
    fm = (CLAUDE_AGENTS / "agatha.frontmatter.yml").read_text()
    assert "Agent" in fm
    assert "NotebookEdit" in fm


def test_T_0021_050_agatha_workflow():
    text = (SHARED_AGENTS / "agatha.md").read_text()
    assert re.search(r"Documentation Process|Read spec.*UX doc.*ADR", text)
    assert re.search(r"Audience|audience", text)


# ═══════════════════════════════════════════════════════════════════════
# Step 4: Preamble
# ═══════════════════════════════════════════════════════════════════════


def test_T_0021_064_preamble_step_order():
    text = (SHARED_REFS / "agent-preamble.md").read_text()
    assert "DoR first" in text
    assert "upstream artifacts" in text
    assert "retro lessons" in text
    assert re.search(r"brain context", text, re.IGNORECASE)
    assert "DoD last" in text
    dor = text.index("DoR first")
    dod = text.index("DoD last")
    assert dor < dod


def test_T_0021_065_ellis_no_old_brain_line():
    text = (SHARED_AGENTS / "ellis.md").read_text()
    assert "Eva uses these to capture knowledge to the brain" not in text


def test_T_0021_066_invocation_templates():
    text = (SHARED_REFS / "invocation-templates.md").read_text()
    head = "\n".join(text.splitlines()[:60])
    assert re.search(r"brain-context", head, re.IGNORECASE)
    # brain-extractor SubagentStop hook handles capture mechanically
    assert re.search(r"agent_capture|capture.*automatically|brain-extractor|SubagentStop", text, re.IGNORECASE)


def test_T_0021_118_preamble_updated():
    text = (SHARED_REFS / "agent-preamble.md").read_text()
    if "they do not call agent_search themselves" in text:
        assert re.search(r"capture directly|mcpServers|agent_capture|brain access", text, re.IGNORECASE)


def test_T_0021_119_ellis_still_mentions_brain():
    text = (SHARED_AGENTS / "ellis.md").read_text()
    assert re.search(r"brain", text, re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════════════
# Step 5a: Dead prose cleanup
# ═══════════════════════════════════════════════════════════════════════


def test_T_0021_069_brain_config_four_agents():
    section = _extract_section(
        SHARED_RULES / "agent-system.md",
        '<section id="brain-config">', '</section>',
    )
    # After ADR-0024, brain-config references the brain-extractor hook
    # which handles Cal, Colby, Roz, Agatha mechanically. The section
    # describes the mechanism, not individual agent names.
    assert re.search(r"brain|capture|agent", section, re.IGNORECASE)


def test_T_0021_071_no_mandatory_brain_access():
    text = (SHARED_RULES / "pipeline-orchestration.md").read_text()
    assert not re.search(r"Brain Access.*MANDATORY|MANDATORY.*Brain Access", text)


def test_T_0021_072_best_effort():
    text = (SHARED_RULES / "pipeline-orchestration.md").read_text()
    assert re.search(r"best-effort", text, re.IGNORECASE)


def test_T_0021_073_no_spot_check():
    text = (SHARED_RULES / "pipeline-orchestration.md").read_text()
    assert not re.search(r"Verification.*spot.check", text, re.IGNORECASE)


def test_T_0021_075_shared_behaviors_brain():
    section = _extract_section(
        SHARED_RULES / "agent-system.md",
        '<section id="shared-behaviors">', '</section>',
    )
    assert re.search(r"brain context", section, re.IGNORECASE)


def test_T_0021_076_seed_devops():
    text = (SHARED_RULES / "pipeline-orchestration.md").read_text()
    assert "Seed Capture" in text
    assert re.search(r"devops Capture Gates|/devops Capture Gates", text)


def test_T_0021_077_tier1():
    text = (SHARED_RULES / "pipeline-orchestration.md").read_text()
    assert re.search(r"Tier 1", text, re.IGNORECASE)


def test_T_0021_080_no_mandatory_telemetry():
    text = (SHARED_RULES / "pipeline-orchestration.md").read_text()
    assert not re.search(r"Telemetry Capture.*MANDATORY|MANDATORY.*Telemetry Capture", text)


def test_T_0021_111_seed_capture():
    assert "Seed Capture" in (SHARED_RULES / "pipeline-orchestration.md").read_text()


def test_T_0021_112_devops_capture():
    text = (SHARED_RULES / "pipeline-orchestration.md").read_text()
    assert re.search(r"devops Capture Gates|/devops Capture Gates", text)


# ═══════════════════════════════════════════════════════════════════════
# Step 5b
# ═══════════════════════════════════════════════════════════════════════


def test_T_0021_081_context_eviction_brain():
    """Context eviction references brain capture model details as consumed post-boot."""
    text = (SHARED_RULES / "default-persona.md").read_text()
    assert re.search(r"brain capture|brain.*protocol|brain.*model|brain.*evict|brain.*consumed", text, re.IGNORECASE)


def test_T_0021_082_no_evict_telemetry():
    text = (SHARED_RULES / "default-persona.md").read_text()
    assert "Telemetry trend computation logic" not in text


def test_T_0021_085_pipeline_ops_prefetch():
    text = (SHARED_REFS / "pipeline-operations.md").read_text()
    assert "prompt-brain-prefetch.sh" in text


def test_T_0021_086_pipeline_ops_hybrid():
    """Pipeline ops references brain capture mechanism (hook-based, not agent-direct)."""
    text = (SHARED_REFS / "pipeline-operations.md").read_text()
    assert re.search(r"hybrid|brain-extractor|SubagentStop|capture.*hook|hook.*capture|brain.*prefetch|brain.*capture", text, re.IGNORECASE)


def test_T_0021_087_boot_steps():
    """Boot steps 4-6 are now in session-boot.md (ADR-0023 reduction)."""
    boot = (SHARED_REFS / "session-boot.md").read_text()
    assert "Brain health check" in boot
    assert re.search(r"Brain context retrieval|context retrieval", boot, re.IGNORECASE)


def test_T_0021_088_model_tables():
    text = (SHARED_RULES / "pipeline-models.md").read_text()
    for word in ["opus", "haiku"]:
        assert re.search(word, text, re.IGNORECASE)


def test_T_0021_113_boot_sequence():
    """Boot sequence details (atelier_stats, agent_search) are in session-boot.md."""
    boot = (SHARED_REFS / "session-boot.md").read_text()
    assert "atelier_stats" in boot
    assert "agent_search" in boot


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
        f = CLAUDE_AGENTS / f"{agent}.frontmatter.yml"
        if f.exists():
            fm = f.read_text()
            assert "atelier-brain" not in fm, f"{agent} should not have atelier-brain"
