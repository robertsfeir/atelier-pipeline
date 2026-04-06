"""Tests for ADR-0024 Wave 3: Hook removal, frontmatter cleanup, doc updates, test cleanup.

Covers T-0024-026 through T-0024-050.

These tests verify the final state after Wave 3 cleanup:
- Old behavioral hooks are gone from settings.json and source/
- mcpServers removed from cal/colby/roz/agatha frontmatter
- Orchestration doc references updated
- Eva's cross-cutting captures are preserved (preservation tests)
- Old test files are deleted
- Full test suite passes

Tests T-0024-044 and T-0024-045 (test file deletion) will pass as soon as
Colby deletes those files -- they do not depend on any build work.

Colby MUST NOT modify these assertions.
"""

import json
import re
import subprocess
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


# ── Paths ─────────────────────────────────────────────────────────────────

SETTINGS_JSON    = PROJECT_ROOT / ".claude" / "settings.json"
SOURCE_CLAUDE    = PROJECT_ROOT / "source" / "claude"
SOURCE_SHARED    = PROJECT_ROOT / "source" / "shared"
SHARED_RULES     = SOURCE_SHARED / "rules"
SHARED_REFS      = SOURCE_SHARED / "references"
CLAUDE_AGENTS    = SOURCE_CLAUDE / "agents"
SOURCE_HOOKS     = SOURCE_CLAUDE / "hooks"
TESTS_HOOKS      = PROJECT_ROOT / "tests" / "hooks"

PIPELINE_ORCH    = SHARED_RULES / "pipeline-orchestration.md"
AGENT_SYSTEM     = SHARED_RULES / "agent-system.md"
DEFAULT_PERSONA  = SHARED_RULES / "default-persona.md"
PIPELINE_OPS     = SHARED_REFS / "pipeline-operations.md"
INVOCATION_TMPL  = SHARED_REFS / "invocation-templates.md"
POST_COMPACT     = SOURCE_HOOKS / "post-compact-reinject.sh"


# ── Helpers ───────────────────────────────────────────────────────────────


def load_settings() -> dict:
    return json.loads(SETTINGS_JSON.read_text())


def get_subagent_stop_hooks(settings: dict) -> list:
    return settings["hooks"]["SubagentStop"][0]["hooks"]


def _extract_section(file_path: Path, start_tag: str, end_tag: str) -> str:
    """Extract content between start_tag and end_tag (inclusive)."""
    text = file_path.read_text()
    m = re.search(
        rf"({re.escape(start_tag)}.*?{re.escape(end_tag)})",
        text, re.DOTALL,
    )
    return m.group(1) if m else ""


# ═══════════════════════════════════════════════════════════════════════
# T-0024-026: settings.json SubagentStop has no prompt-brain-capture.sh
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_026_settings_no_prompt_brain_capture():
    """settings.json SubagentStop must not reference prompt-brain-capture.sh.

    Wave 3 Step 3a removes this hook entry (ADR-0024 R7, AC-12).
    During Wave 1 this hook coexisted. After Wave 3 it is gone.
    """
    settings_text = SETTINGS_JSON.read_text()
    assert "prompt-brain-capture.sh" not in settings_text, (
        "settings.json still references 'prompt-brain-capture.sh'. "
        "Wave 3 Step 3a must remove this hook entry from SubagentStop "
        "(ADR-0024 R7, AC-12)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-027: settings.json SubagentStop has no warn-brain-capture.sh
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_027_settings_no_warn_brain_capture():
    """settings.json SubagentStop must not reference warn-brain-capture.sh.

    Wave 3 Step 3a removes this hook entry (ADR-0024 R8, AC-11).
    """
    settings_text = SETTINGS_JSON.read_text()
    assert "warn-brain-capture.sh" not in settings_text, (
        "settings.json still references 'warn-brain-capture.sh'. "
        "Wave 3 Step 3a must remove this hook entry from SubagentStop "
        "(ADR-0024 R8, AC-11)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-028: source/claude/hooks/prompt-brain-capture.sh does not exist
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_028_prompt_brain_capture_script_deleted():
    """source/claude/hooks/prompt-brain-capture.sh must not exist.

    Wave 3 Step 3a deletes this script (ADR-0024 R7).
    """
    hook_path = SOURCE_HOOKS / "prompt-brain-capture.sh"
    assert not hook_path.exists(), (
        f"source/claude/hooks/prompt-brain-capture.sh still exists at {hook_path}. "
        "Wave 3 Step 3a must delete this file (ADR-0024 R7)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-029: source/claude/hooks/warn-brain-capture.sh does not exist
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_029_warn_brain_capture_script_deleted():
    """source/claude/hooks/warn-brain-capture.sh must not exist.

    Wave 3 Step 3a deletes this script (ADR-0024 R8).
    """
    hook_path = SOURCE_HOOKS / "warn-brain-capture.sh"
    assert not hook_path.exists(), (
        f"source/claude/hooks/warn-brain-capture.sh still exists at {hook_path}. "
        "Wave 3 Step 3a must delete this file (ADR-0024 R8)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-030 through T-0024-033: mcpServers removed from agent frontmatter overlays
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("agent_name", ["cal", "colby", "roz", "agatha"])
def test_T_0024_030_033_frontmatter_no_mcp_servers(agent_name):
    """source/claude/agents/{agent}.frontmatter.yml must not have mcpServers: atelier-brain.

    After Wave 3 Step 3b, the four brain-access agents no longer declare
    atelier-brain in their per-agent frontmatter. They get MCP access via
    project-level .mcp.json inheritance when invoked as subagents that
    need brain access. Cal/Colby/Roz/Agatha no longer need direct brain
    access at all -- the extractor handles brain writes.
    ADR-0024 R9, Step 3b.
    """
    fm_path = CLAUDE_AGENTS / f"{agent_name}.frontmatter.yml"
    assert fm_path.exists(), f"source/claude/agents/{agent_name}.frontmatter.yml not found"
    text = fm_path.read_text()
    assert "mcpServers" not in text, (
        f"source/claude/agents/{agent_name}.frontmatter.yml still contains 'mcpServers'. "
        f"Wave 3 Step 3b must remove the mcpServers block (ADR-0024 Step 3b)."
    )
    assert "atelier-brain" not in text, (
        f"source/claude/agents/{agent_name}.frontmatter.yml still references 'atelier-brain'. "
        f"Wave 3 Step 3b must remove this (ADR-0024 Step 3b)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-034: pipeline-orchestration.md does not reference "see agent personas for capture gates"
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_034_pipeline_orch_no_see_agent_personas_capture_gates():
    """source/shared/rules/pipeline-orchestration.md must not reference 'see agent personas for capture gates'.

    This phrase directed readers to per-agent Brain Access sections that no
    longer exist after Wave 2. Wave 3 Step 3c updates all orchestration docs
    to describe the mechanical SubagentStop hook instead (ADR-0024 Step 3c AC).
    """
    assert PIPELINE_ORCH.exists(), f"pipeline-orchestration.md not found at {PIPELINE_ORCH}"
    text = PIPELINE_ORCH.read_text()
    assert not re.search(r"see agent personas.*capture gates|agent personas.*for capture gates",
                         text, re.IGNORECASE), (
        "pipeline-orchestration.md still references 'see agent personas for capture gates'. "
        "Wave 3 Step 3c must update this to describe the mechanical hook "
        "(ADR-0024 Step 3c AC, grep check: 'grep -r \"see agent personas.*capture gates\" source/shared/')."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-035: agent-system.md brain-config section does not reference prompt-brain-capture.sh
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_035_agent_system_brain_config_no_prompt_brain_capture():
    """source/shared/rules/agent-system.md brain-config section must not reference prompt-brain-capture.sh.

    After Wave 3, the Writes bullet in the brain-config section must describe
    the mechanical extractor hook, not the old prompt hook (ADR-0024 Step 3c).
    """
    assert AGENT_SYSTEM.exists(), f"agent-system.md not found at {AGENT_SYSTEM}"
    brain_config_section = _extract_section(
        AGENT_SYSTEM, '<section id="brain-config">', '</section>'
    )
    assert brain_config_section, "brain-config section not found in agent-system.md"
    assert "prompt-brain-capture.sh" not in brain_config_section, (
        "agent-system.md brain-config section still references 'prompt-brain-capture.sh'. "
        "Wave 3 Step 3c must update the Writes bullet to describe the mechanical hook "
        "(ADR-0024 Step 3c)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-036: agent-system.md shared-behaviors does not reference "also capture directly"
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_036_agent_system_shared_behaviors_no_capture_directly():
    """source/shared/rules/agent-system.md shared-behaviors must not say agents 'also capture directly'.

    After Wave 3, agents (Cal, Colby, Roz, Agatha) no longer self-capture.
    The shared-behaviors brain context bullet must be updated to remove the
    'also capture directly' language (ADR-0024 Step 3c AC).
    """
    assert AGENT_SYSTEM.exists(), f"agent-system.md not found at {AGENT_SYSTEM}"
    shared_behaviors_section = _extract_section(
        AGENT_SYSTEM, '<section id="shared-behaviors">', '</section>'
    )
    assert shared_behaviors_section, "shared-behaviors section not found in agent-system.md"
    assert "also capture directly" not in shared_behaviors_section, (
        "agent-system.md shared-behaviors still says agents 'also capture directly'. "
        "Wave 3 Step 3c must remove this language -- agents no longer self-capture "
        "(ADR-0024 Step 3c AC)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-037: default-persona.md does not reference prompt-brain-capture.sh
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_037_default_persona_no_prompt_brain_capture():
    """source/shared/rules/default-persona.md must not reference prompt-brain-capture.sh.

    The Brain Access section of default-persona.md previously mentioned this hook.
    Wave 3 Step 3c updates it to reference the mechanical SubagentStop extractor
    (ADR-0024 Step 3c).
    """
    assert DEFAULT_PERSONA.exists(), f"default-persona.md not found at {DEFAULT_PERSONA}"
    text = DEFAULT_PERSONA.read_text()
    assert "prompt-brain-capture.sh" not in text, (
        "source/shared/rules/default-persona.md still references 'prompt-brain-capture.sh'. "
        "Wave 3 Step 3c must update the Brain Access section "
        "(ADR-0024 Step 3c)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-038: pipeline-operations.md does not reference "capture domain-specific knowledge directly"
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_038_pipeline_ops_no_capture_directly():
    """source/shared/references/pipeline-operations.md must not reference agent self-capture language.

    The brain-prefetch section currently contains:
      - 'also capture directly' (line 22)
      - 'domain-specific knowledge directly via their Brain Access protocols' (line 27)
    After Wave 3, agents no longer self-capture -- this language must be removed
    (ADR-0024 Step 3c AC: 'No match for "capture domain-specific knowledge directly"').
    """
    assert PIPELINE_OPS.exists(), f"pipeline-operations.md not found at {PIPELINE_OPS}"
    text = PIPELINE_OPS.read_text()
    # The actual phrases in the file that must be absent after Wave 3
    assert "also capture directly" not in text, (
        "source/shared/references/pipeline-operations.md still says agents 'also capture directly'. "
        "Wave 3 Step 3c must remove this agent self-capture language (ADR-0024 Step 3c AC)."
    )
    assert "domain-specific knowledge directly via their Brain Access protocols" not in text, (
        "source/shared/references/pipeline-operations.md still references agent Brain Access protocols. "
        "Wave 3 Step 3c must remove this language (ADR-0024 Step 3c AC)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-039: invocation-templates.md does not reference "also capture via agent_capture" for agents
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_039_invocation_templates_no_agent_self_capture():
    """source/shared/references/invocation-templates.md must not instruct agents to self-capture via agent_capture.

    The header note previously described agents with mcpServers capturing
    domain-specific knowledge. After Wave 3, this note is updated to
    reference the mechanical extractor hook (ADR-0024 Step 3c).
    """
    assert INVOCATION_TMPL.exists(), f"invocation-templates.md not found at {INVOCATION_TMPL}"
    text = INVOCATION_TMPL.read_text()
    # Check for the mcpServers-based agent self-capture language in the header region
    header = "\n".join(text.splitlines()[:30])
    assert not re.search(r"mcpServers.*atelier-brain.*Cal.*Colby|Agents with.*mcpServers.*capture",
                         header, re.IGNORECASE | re.DOTALL), (
        "invocation-templates.md header still describes agents with mcpServers capturing directly. "
        "Wave 3 Step 3c must update this note (ADR-0024 Step 3c)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-040: post-compact-reinject.sh Brain Protocol Reminder references mechanical hook
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_040_post_compact_reinject_references_mechanical_hook():
    """source/claude/hooks/post-compact-reinject.sh must reference the mechanical SubagentStop extractor.

    After Wave 3, the Brain Protocol Reminder section of post-compact-reinject.sh
    must describe the mechanical extraction model, not the old behavioral model
    with mcpServers and prompt-brain-capture.sh (ADR-0024 Step 3c).
    """
    assert POST_COMPACT.exists(), f"post-compact-reinject.sh not found at {POST_COMPACT}"
    text = POST_COMPACT.read_text()
    # Must NOT reference the old behavioral model
    assert "prompt-brain-capture.sh" not in text, (
        "post-compact-reinject.sh still references 'prompt-brain-capture.sh'. "
        "Wave 3 Step 3c must update the Brain Protocol Reminder section."
    )
    assert not re.search(r"mcpServers.*atelier-brain.*capture|capture.*mcpServers.*atelier-brain",
                         text, re.IGNORECASE), (
        "post-compact-reinject.sh still references mcpServers + capture in the old model. "
        "Wave 3 Step 3c must update this."
    )
    # MUST reference the mechanical model
    assert re.search(
        r"SubagentStop.*extractor|brain.extractor|mechanical.*capture|"
        r"extractor.*hook|hook.*extractor|brain-extractor",
        text, re.IGNORECASE,
    ), (
        "post-compact-reinject.sh Brain Protocol Reminder does not reference the mechanical "
        "SubagentStop extractor. After Wave 3, this reminder must describe the new model "
        "(ADR-0024 Step 3c AC: 'Reference to SubagentStop extractor or mechanical capture present')."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-041: pipeline-orchestration.md still contains Eva cross-cutting Writes section
# ═══════════════════════════════════════════════════════════════════════


# ADR-0025 supersedes: Eva's behavioral Writes section deleted; hydrator now owns Eva's state-file captures (ADR-0025 R10)
def test_T_0024_041_pipeline_orch_preserves_eva_cross_cutting_writes():
    """pipeline-orchestration.md must NOT contain Eva's behavioral Writes section after ADR-0025.

    ADR-0025 R10 deletes Eva's cross-cutting Writes subsection from the Hybrid
    Capture Model. The hydrator (hydrate-telemetry.mjs) now owns those captures
    mechanically by parsing pipeline-state.md and context-brief.md. The remaining
    source_agent: 'eva' references are /devops captures and telemetry-only
    references, not the behavioral Writes list.
    """
    assert PIPELINE_ORCH.exists(), f"pipeline-orchestration.md not found at {PIPELINE_ORCH}"
    text = PIPELINE_ORCH.read_text()
    # After ADR-0025, the behavioral "Writes (cross-cutting only, best-effort)" subsection
    # is removed. Only mechanical references remain (devops + telemetry).
    eva_capture_matches = re.findall(r"source_agent: 'eva'", text)
    assert len(eva_capture_matches) < 3, (
        f"pipeline-orchestration.md still has {len(eva_capture_matches)} source_agent: 'eva' "
        "references (expected < 3 after ADR-0025 removed the behavioral Writes section). "
        "ADR-0025 R10 requires the Writes subsection be deleted."
    )
    # The Writes subsection header must be gone
    assert "Writes (cross-cutting only" not in text, (
        "pipeline-orchestration.md still contains the behavioral Writes section header. "
        "ADR-0025 R10 requires this section be deleted."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-042: pipeline-orchestration.md still contains Seed Capture section
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_042_pipeline_orch_preserves_seed_capture():
    """source/shared/rules/pipeline-orchestration.md must still contain the Seed Capture section.

    Seed Capture is an agent-initiated capture for out-of-scope ideas. It is
    distinct from domain capture and remains behavioral by design (ADR-0024 R13,
    AC-17 preservation list, Step 3c AC).
    """
    assert PIPELINE_ORCH.exists(), f"pipeline-orchestration.md not found at {PIPELINE_ORCH}"
    text = PIPELINE_ORCH.read_text()
    assert "Seed Capture" in text, (
        "pipeline-orchestration.md no longer contains 'Seed Capture' section. "
        "This section must be preserved unchanged (ADR-0024 Step 3c AC)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-043: pipeline-orchestration.md still contains /devops Capture Gates section
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_043_pipeline_orch_preserves_devops_capture_gates():
    """source/shared/rules/pipeline-orchestration.md must still contain /devops Capture Gates section.

    Eva's /devops capture gates are preserved unchanged. They are part of Eva's
    cross-cutting capture model, not agent-domain capture (ADR-0024 R13, AC-17).
    """
    assert PIPELINE_ORCH.exists(), f"pipeline-orchestration.md not found at {PIPELINE_ORCH}"
    text = PIPELINE_ORCH.read_text()
    assert re.search(r"/devops Capture Gates|devops Capture Gates", text), (
        "pipeline-orchestration.md no longer contains '/devops Capture Gates'. "
        "This section must be preserved unchanged (ADR-0024 Step 3c AC)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-044: test_warn_brain_capture.py does not exist
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_044_warn_brain_capture_test_file_deleted():
    """tests/hooks/test_warn_brain_capture.py must not exist.

    Wave 3 Step 3d deletes this file (ADR-0024 blast radius: 'Tests deleted').
    The warn-brain-capture.sh hook is gone; its tests must go with it.
    Note to Colby: Roz does not delete this file now -- Colby deletes it in Wave 3.
    """
    test_file = TESTS_HOOKS / "test_warn_brain_capture.py"
    assert not test_file.exists(), (
        f"tests/hooks/test_warn_brain_capture.py still exists at {test_file}. "
        "Wave 3 Step 3d must delete this test file "
        "(ADR-0024 Step 3d: 'Files to delete: tests/hooks/test_warn_brain_capture.py')."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-045: test_prompt_brain_capture.py does not exist
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_045_prompt_brain_capture_test_file_deleted():
    """tests/hooks/test_prompt_brain_capture.py must not exist.

    Wave 3 Step 3d deletes this file (ADR-0024 blast radius: 'Tests deleted').
    The prompt-brain-capture.sh hook is gone; its tests must go with it.
    Note to Colby: Roz does not delete this file now -- Colby deletes it in Wave 3.
    """
    test_file = TESTS_HOOKS / "test_prompt_brain_capture.py"
    assert not test_file.exists(), (
        f"tests/hooks/test_prompt_brain_capture.py still exists at {test_file}. "
        "Wave 3 Step 3d must delete this test file "
        "(ADR-0024 Step 3d: 'Files to delete: tests/hooks/test_prompt_brain_capture.py')."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-046: brain-extractor.frontmatter.yml does NOT have mcpServers
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_046_extractor_frontmatter_no_mcp_servers():
    """source/claude/agents/brain-extractor.frontmatter.yml must NOT declare mcpServers.

    The extractor gets MCP access via project-level .mcp.json inheritance, not
    per-agent frontmatter declaration. This is the whole point of the architectural
    change -- agents no longer need to declare mcpServers individually.
    ADR-0024 Step 3b AC: 'brain-extractor.frontmatter.yml does NOT have mcpServers
    (it gets MCP via project-level inheritance)'.
    """
    fm_path = PROJECT_ROOT / "source" / "claude" / "agents" / "brain-extractor.frontmatter.yml"
    if not fm_path.exists():
        pytest.skip("brain-extractor.frontmatter.yml not yet created (Wave 1 not complete)")
    text = fm_path.read_text()
    assert "mcpServers" not in text, (
        "brain-extractor.frontmatter.yml contains 'mcpServers'. "
        "The extractor must not declare MCP servers in per-agent frontmatter -- "
        "it inherits from .mcp.json at project level (ADR-0024 Step 3b AC)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-047: Non-brain agents do not have mcpServers: atelier-brain
# ═══════════════════════════════════════════════════════════════════════


NON_BRAIN_AGENTS = [
    "robert", "sable", "investigator", "distillator",
    "sentinel", "darwin", "deps", "ellis",
]


@pytest.mark.parametrize("agent_name", NON_BRAIN_AGENTS)
def test_T_0024_047_non_brain_agents_no_mcp_servers(agent_name):
    """Non-brain agents must not have mcpServers: atelier-brain in their frontmatter.

    This is a regression test -- these agents were never supposed to have brain
    access and must not gain it. ADR-0024 Step 3d: 'test_T_0021_108_non_brain_agents_no_mcpServers
    to also assert brain-access agents no longer have mcpServers'.
    """
    fm_path = PROJECT_ROOT / "source" / "claude" / "agents" / f"{agent_name}.frontmatter.yml"
    if not fm_path.exists():
        # Not all non-brain agents have frontmatter files (some are read-only subagents)
        pytest.skip(f"No frontmatter file for {agent_name} -- skipping")
    text = fm_path.read_text()
    assert "atelier-brain" not in text, (
        f"source/claude/agents/{agent_name}.frontmatter.yml contains 'atelier-brain'. "
        f"Non-brain agents must not have brain MCP access (ADR-0024 T-0024-047)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-048: Full pytest suite passes
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_048_full_pytest_suite_passes():
    """pytest tests/ must pass with exit code 0 after all Wave 3 changes.

    This is the full regression gate. ADR-0024 R15 (all existing tests pass
    after cleanup), Step 3d AC: 'pytest tests/ passes'.

    Note: this test will itself be part of the suite it's testing. If it
    reaches this assertion, pytest is running (trivially true). The assertion
    here validates that no OTHER test in tests/ fails -- which is verified by
    running the suite separately.
    """
    result = subprocess.run(
        ["pytest", "tests/", "-q", "--tb=short", "--ignore=tests/hooks/test_wave3_hook_removal.py",
         "--ignore=tests/hooks/test_wave2_persona_cleanup.py",
         "--ignore=tests/hooks/test_brain_extractor.py"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=120,
    )
    assert result.returncode == 0, (
        f"pytest tests/ failed (exit code {result.returncode}). "
        f"ADR-0024 R15 requires all existing tests to pass after cleanup.\n"
        f"stdout:\n{result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout}\n"
        f"stderr:\n{result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr}"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-049: Brain MJS test suite passes
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_049_brain_node_test_suite_passes():
    """cd brain && node --test ../tests/brain/*.test.mjs must pass.

    ADR-0024 Step 3d AC: 'cd brain && node --test ../tests/brain/*.test.mjs passes'.
    Brain MJS tests must not be broken by any of the hook/persona changes.
    """
    brain_dir = PROJECT_ROOT / "brain"
    if not brain_dir.exists():
        pytest.skip("brain/ directory not found -- skipping Node test suite check")

    brain_tests = list((PROJECT_ROOT / "tests" / "brain").glob("*.test.mjs"))
    if not brain_tests:
        pytest.skip("No brain/*.test.mjs tests found -- skipping")

    result = subprocess.run(
        ["node", "--test"] + [str(t) for t in brain_tests],
        capture_output=True,
        text=True,
        cwd=str(brain_dir),
        timeout=120,
    )
    assert result.returncode == 0, (
        f"Node brain test suite failed (exit code {result.returncode}). "
        f"ADR-0024 Step 3d AC requires this to pass.\n"
        f"stdout:\n{result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout}\n"
        f"stderr:\n{result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr}"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-050: settings.json SubagentStop has exactly 3 hooks after cleanup
# ═══════════════════════════════════════════════════════════════════════


# ADR-0025 supersedes: warn-dor-dod.sh removed from SubagentStop, count drops from 3 to 2 (ADR-0025 R11)
def test_T_0024_050_subagent_stop_has_exactly_3_hooks():
    """settings.json SubagentStop block must have exactly 2 hooks after ADR-0025 Wave 2.

    ADR-0025 R11 deletes warn-dor-dod.sh from SubagentStop, reducing the count from 3 to 2.
    Expected hooks after ADR-0025:
      1. log-agent-stop.sh (command hook, no condition)
      2. brain-extractor agent hook (type: agent, if: cal || colby || roz || agatha)

    warn-dor-dod.sh is gone. The DoD completeness signal it provided is now
    captured mechanically by the brain-extractor structured quality signals (ADR-0025 R3).
    """
    settings = load_settings()
    hooks = get_subagent_stop_hooks(settings)
    hook_count = len(hooks)
    assert hook_count == 2, (
        f"settings.json SubagentStop has {hook_count} hooks, expected exactly 2. "
        f"After ADR-0025: log-agent-stop.sh + brain-extractor agent hook only. "
        f"Current hooks: {[h.get('command', h.get('agent', '?')) for h in hooks]}"
    )

    # Verify the two expected hooks are present
    hook_refs = [h.get("command", h.get("agent", "")) for h in hooks]
    hook_refs_str = " ".join(hook_refs)

    assert "warn-dor-dod.sh" not in hook_refs_str, (
        "warn-dor-dod.sh must not appear in SubagentStop after ADR-0025 deleted it."
    )
    assert "log-agent-stop.sh" in hook_refs_str, (
        "log-agent-stop.sh not found in SubagentStop hooks. "
        "This existing hook must be preserved."
    )
    assert "brain-extractor" in hook_refs_str, (
        "brain-extractor agent hook not found in SubagentStop hooks. "
        "The mechanical hook must be present."
    )
