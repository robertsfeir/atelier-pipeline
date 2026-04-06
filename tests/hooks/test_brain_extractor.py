"""Tests for ADR-0024 Wave 1: brain-extractor agent persona + SubagentStop hook wiring.

Covers T-0024-001 through T-0024-015.

These tests define correct behavior BEFORE Colby builds. All tests should
FAIL before Wave 1 is implemented (brain-extractor.md does not exist yet,
settings.json does not have the agent hook yet).

Colby MUST NOT modify these assertions.
"""

import json
import re
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


# ── Paths ─────────────────────────────────────────────────────────────────

SETTINGS_JSON = PROJECT_ROOT / ".claude" / "settings.json"
SHARED_AGENTS = PROJECT_ROOT / "source" / "shared" / "agents"
CLAUDE_AGENTS = PROJECT_ROOT / "source" / "claude" / "agents"

EXTRACTOR_PERSONA = SHARED_AGENTS / "brain-extractor.md"
EXTRACTOR_FRONTMATTER = CLAUDE_AGENTS / "brain-extractor.frontmatter.yml"

# ── Helpers ───────────────────────────────────────────────────────────────


def load_settings() -> dict:
    """Load and parse .claude/settings.json."""
    return json.loads(SETTINGS_JSON.read_text())


def get_subagent_stop_hooks(settings: dict) -> list:
    """Return the list of hooks in the SubagentStop block."""
    return settings["hooks"]["SubagentStop"][0]["hooks"]


def find_agent_hook(hooks: list) -> dict | None:
    """Return the first hook with type == 'agent', or None."""
    for h in hooks:
        if h.get("type") == "agent":
            return h
    return None


def extract_frontmatter_text(file_path: Path) -> str:
    """Extract raw YAML frontmatter text from a file.

    For pure YAML files (.yml/.yaml) with no --- delimiters, returns the full
    file content. For markdown files with --- frontmatter blocks, extracts the
    content between the first --- pair.
    """
    text = file_path.read_text()
    lines = text.splitlines()
    in_fm = False
    result = []
    for line in lines:
        if line.strip() == "---":
            if in_fm:
                break
            in_fm = True
            continue
        if in_fm:
            result.append(line)
    if not in_fm:
        # No --- delimiters found — treat entire file as YAML (pure overlay file)
        return text
    return "\n".join(result)


def parse_frontmatter(file_path: Path) -> dict:
    """Parse YAML frontmatter from a markdown file. Returns dict."""
    return yaml.safe_load(extract_frontmatter_text(file_path)) or {}


# ═══════════════════════════════════════════════════════════════════════
# T-0024-001: settings.json SubagentStop has "type": "agent" entry for brain-extractor
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_001_settings_has_agent_hook():
    """settings.json SubagentStop block must have a hook with type='agent' pointing at brain-extractor."""
    settings = load_settings()
    hooks = get_subagent_stop_hooks(settings)
    agent_hook = find_agent_hook(hooks)
    assert agent_hook is not None, (
        "SubagentStop block has no hook with type='agent'. "
        "Expected: {\"type\": \"agent\", \"agent\": \"brain-extractor\", \"if\": \"...\"}"
    )
    assert agent_hook.get("agent") == "brain-extractor", (
        f"agent hook points at '{agent_hook.get('agent')}', expected 'brain-extractor'"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-002: brain-extractor NOT in hook's if: condition (loop prevention -- primary)
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_002_brain_extractor_excluded_from_if_condition():
    """brain-extractor must NOT appear in the agent hook's if: condition.

    Rationale (Retro #003): if brain-extractor matched the condition that fires
    SubagentStop, the extractor's own completion would re-trigger the hook,
    causing an infinite capture loop. This is the primary loop prevention guard.
    """
    settings = load_settings()
    hooks = get_subagent_stop_hooks(settings)
    agent_hook = find_agent_hook(hooks)
    assert agent_hook is not None, "No agent hook found in SubagentStop -- T-0024-001 must pass first"
    condition = agent_hook.get("if", "")
    assert "brain-extractor" not in condition, (
        f"LOOP PREVENTION VIOLATED: 'brain-extractor' found in if: condition '{condition}'. "
        "The extractor must be excluded to prevent infinite SubagentStop loops (Retro #003)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-003: if: condition includes exactly cal/colby/roz/agatha, no others
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_003_if_condition_includes_exactly_four_agents():
    """The agent hook if: condition must reference exactly cal, colby, roz, agatha.

    No other agent types (ellis, poirot, robert, sable, sentinel, etc.) should appear.
    Exact expected form:
      agent_type == 'cal' || agent_type == 'colby' || agent_type == 'roz' || agent_type == 'agatha'
    """
    settings = load_settings()
    hooks = get_subagent_stop_hooks(settings)
    agent_hook = find_agent_hook(hooks)
    assert agent_hook is not None, "No agent hook found -- T-0024-001 must pass first"
    condition = agent_hook.get("if", "")

    # All four must be present
    for expected_agent in ["cal", "colby", "roz", "agatha"]:
        assert expected_agent in condition, (
            f"Expected agent '{expected_agent}' not found in if: condition '{condition}'"
        )

    # No unintended agents
    unintended = ["ellis", "poirot", "robert", "sable", "sentinel", "darwin", "deps",
                  "investigator", "distillator", "brain-extractor"]
    for agent in unintended:
        assert agent not in condition, (
            f"Unintended agent '{agent}' found in if: condition '{condition}'. "
            "Only cal/colby/roz/agatha should appear."
        )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-004: brain-extractor.md exists in source/shared/agents/
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_004_extractor_persona_file_exists():
    """source/shared/agents/brain-extractor.md must exist."""
    assert EXTRACTOR_PERSONA.exists(), (
        f"brain-extractor.md not found at {EXTRACTOR_PERSONA}. "
        "Colby must create this file in Wave 1 Step 1a."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-005: brain-extractor frontmatter specifies model: haiku
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_005_extractor_model_is_haiku():
    """brain-extractor frontmatter must specify model: haiku (or a haiku variant).

    The extractor is a minimal extraction agent -- Opus/Sonnet would be wasteful
    and inconsistent with the ADR decision rationale.
    """
    assert EXTRACTOR_FRONTMATTER.exists(), (
        f"brain-extractor.frontmatter.yml not found -- T-0024-015 must pass first"
    )
    fm = parse_frontmatter(EXTRACTOR_FRONTMATTER)
    model = fm.get("model", "")
    assert re.search(r"haiku", str(model), re.IGNORECASE), (
        f"brain-extractor model is '{model}', expected a haiku model. "
        "ADR-0024 specifies Haiku for cost-efficient extraction."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-006: brain-extractor frontmatter specifies maxTurns <= 5
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_006_extractor_max_turns_lte_5():
    """brain-extractor maxTurns must be <= 5.

    The extractor does one thing: read hook input, call agent_capture.
    A high maxTurns would allow runaway token spend on a background hook.
    ADR-0024 Step 1a acceptance criteria specifies maxTurns: 5.
    """
    assert EXTRACTOR_FRONTMATTER.exists(), "brain-extractor.frontmatter.yml not found"
    fm = parse_frontmatter(EXTRACTOR_FRONTMATTER)
    max_turns = fm.get("maxTurns")
    assert max_turns is not None, "brain-extractor frontmatter missing maxTurns field"
    assert max_turns <= 5, (
        f"brain-extractor maxTurns is {max_turns}, expected <= 5. "
        "The extractor should complete in 1-3 turns maximum."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-007: disallowedTools blocks Write/Edit/MultiEdit/NotebookEdit/Agent
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_007_extractor_disallowed_tools():
    """brain-extractor must disallow Write, Edit, MultiEdit, NotebookEdit, Agent.

    The extractor must be read-only + MCP-only. It must not write files, must
    not spawn sub-agents (which would trigger more SubagentStop events), and
    must not modify notebooks.
    """
    assert EXTRACTOR_FRONTMATTER.exists(), "brain-extractor.frontmatter.yml not found"
    fm_text = extract_frontmatter_text(EXTRACTOR_FRONTMATTER)
    fm = parse_frontmatter(EXTRACTOR_FRONTMATTER)

    # disallowedTools can be a list in YAML or a comma-separated string
    disallowed_raw = fm.get("disallowedTools", "")
    disallowed_str = (
        ", ".join(disallowed_raw) if isinstance(disallowed_raw, list) else str(disallowed_raw)
    )

    for required_blocked in ["Write", "Edit", "MultiEdit", "NotebookEdit", "Agent"]:
        assert required_blocked in disallowed_str, (
            f"'{required_blocked}' not found in brain-extractor disallowedTools: '{disallowed_str}'. "
            f"All five tools must be blocked. ADR-0024 Step 1a acceptance criteria."
        )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-008: persona contains agent-to-metadata mapping for all 4 agents
# ═══════════════════════════════════════════════════════════════════════


EXPECTED_AGENT_MAPPINGS = [
    # (agent_type, source_agent, source_phase)
    ("cal",   "cal",   "design"),
    ("colby", "colby", "build"),
    ("roz",   "roz",   "qa"),
    ("agatha","agatha","docs"),
]


@pytest.mark.parametrize("agent_type,source_agent,source_phase", EXPECTED_AGENT_MAPPINGS)
def test_T_0024_008_extractor_agent_metadata_mapping(agent_type, source_agent, source_phase):
    """brain-extractor persona must contain the agent-to-metadata mapping for each target agent.

    The mapping determines what source_agent/source_phase are used when the extractor
    calls agent_capture on behalf of a given parent agent.
    """
    assert EXTRACTOR_PERSONA.exists(), "brain-extractor.md not found"
    text = EXTRACTOR_PERSONA.read_text()
    # Each mapping entry must mention the agent_type, its source_agent, and source_phase
    assert agent_type in text, f"agent_type '{agent_type}' not found in brain-extractor.md"
    assert source_agent in text, f"source_agent '{source_agent}' not found in brain-extractor.md"
    assert source_phase in text, f"source_phase '{source_phase}' not found in brain-extractor.md"


# ═══════════════════════════════════════════════════════════════════════
# T-0024-009: persona contains early-exit guard for unknown agent_type
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_009_extractor_early_exit_guard():
    """brain-extractor persona must instruct the agent to exit immediately for unknown agent_type.

    This is the secondary loop-prevention defense (Retro #003). The primary defense is
    the if: condition on the hook. The secondary defense ensures that even if the if:
    condition were misconfigured, the extractor itself would not capture for unknown agents.
    """
    assert EXTRACTOR_PERSONA.exists(), "brain-extractor.md not found"
    text = EXTRACTOR_PERSONA.read_text()
    # The guard should instruct the agent to exit/skip/produce zero captures
    # for agent_type values that are not in the four target agents
    assert re.search(
        r"not.*(cal|colby|roz|agatha).*exit|exit.*not.*(cal|colby|roz|agatha)|"
        r"zero captures.*exit|unknown.*agent.*exit|agent_type.*not.*target|"
        r"not a target|not one of|not in.*cal.*colby|stop.*immediately|early.?exit",
        text,
        re.IGNORECASE | re.DOTALL,
    ), (
        "brain-extractor.md missing early-exit guard for unrecognized agent_type. "
        "The persona must instruct the agent to produce zero captures and exit "
        "if agent_type is not cal/colby/roz/agatha (secondary loop prevention, Retro #003)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-010: persona contains brain unavailability instruction
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_010_extractor_brain_unavailability_instruction():
    """brain-extractor persona must contain instruction to handle brain unavailability gracefully.

    When the brain MCP server is unavailable, the extractor must exit cleanly
    with zero captures -- it must never block the pipeline (ADR-0024 R10).
    """
    assert EXTRACTOR_PERSONA.exists(), "brain-extractor.md not found"
    text = EXTRACTOR_PERSONA.read_text()
    assert re.search(
        r"unavailable|brain.*not.*available|mcp.*unavailable|"
        r"skip.*capture|zero capture.*unavail|graceful|exit.*0|clean exit",
        text,
        re.IGNORECASE,
    ), (
        "brain-extractor.md missing brain unavailability instruction. "
        "The persona must describe graceful handling when agent_capture fails "
        "or the MCP server is unreachable (ADR-0024 R10, AC-7)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-011: persona contains all 3 extraction categories
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("thought_type", ["decision", "pattern", "lesson", "seed"])
def test_T_0024_011_extractor_extraction_categories(thought_type):
    """brain-extractor persona must mention all four extraction thought_type categories.

    The extractor must know to extract decisions, patterns, lessons, and seeds --
    mapping to the four thought_types the brain stores (ADR-0024 extractor design).
    """
    assert EXTRACTOR_PERSONA.exists(), "brain-extractor.md not found"
    text = EXTRACTOR_PERSONA.read_text()
    assert thought_type in text, (
        f"brain-extractor.md missing thought_type '{thought_type}'. "
        "All three extraction categories (decision, pattern, lesson) must be present."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-012: persona references importance values 0.7, 0.5, 0.6
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("importance", ["0.7", "0.5", "0.6"])
def test_T_0024_012_extractor_importance_values(importance):
    """brain-extractor persona must specify the importance values for all four thought_types.

    Per ADR-0024 extractor design: decision -> 0.7, pattern -> 0.5, lesson -> 0.6, seed -> 0.5.
    These values determine brain retrieval ranking.
    """
    assert EXTRACTOR_PERSONA.exists(), "brain-extractor.md not found"
    text = EXTRACTOR_PERSONA.read_text()
    assert importance in text, (
        f"brain-extractor.md missing importance value '{importance}'. "
        "Expected: decision=0.7, pattern=0.5, lesson=0.6 (ADR-0024 extractor design)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-014: settings.json is valid JSON after Wave 1 modification
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_014_settings_json_valid():
    """settings.json must be valid JSON after adding the agent hook entry.

    A JSON parse error would silently break all hook enforcement in the project.
    """
    try:
        data = json.loads(SETTINGS_JSON.read_text())
    except json.JSONDecodeError as e:
        pytest.fail(f"settings.json is invalid JSON after Wave 1 modification: {e}")
    # Also verify the hooks key structure is intact
    assert "hooks" in data
    assert "SubagentStop" in data["hooks"]


# ═══════════════════════════════════════════════════════════════════════
# T-0024-015: brain-extractor.frontmatter.yml exists in source/claude/agents/
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_015_extractor_frontmatter_file_exists():
    """source/claude/agents/brain-extractor.frontmatter.yml must exist.

    The Claude Code overlay frontmatter file is required for the agent to be
    assembled correctly by /pipeline-setup (source/claude/agents/ + source/shared/agents/).
    """
    assert EXTRACTOR_FRONTMATTER.exists(), (
        f"brain-extractor.frontmatter.yml not found at {EXTRACTOR_FRONTMATTER}. "
        "Colby must create this file in Wave 1 Step 1a."
    )

# ═══════════════════════════════════════════════════════════════════════
# T-0024-028b: .claude/hooks/prompt-brain-capture.sh does not exist (installed dir)
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_028b_installed_prompt_brain_capture_absent():
    """The installed .claude/hooks/prompt-brain-capture.sh must not exist.

    T-0024-028 asserts the source script is deleted. This companion test asserts
    the installed copy is also absent -- so the hook is gone from both source/
    and the installed .claude/ directory (ADR-0024 R7, AC-12).
    """
    hook_path = PROJECT_ROOT / ".claude" / "hooks" / "prompt-brain-capture.sh"
    assert not hook_path.exists(), (
        f".claude/hooks/prompt-brain-capture.sh still exists at {hook_path}. "
        "Wave 3 cleanup must remove this script from the installed directory "
        "as well as source/claude/hooks/ (ADR-0024 R7, AC-12)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-029b: .claude/hooks/warn-brain-capture.sh does not exist (installed dir)
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_029b_installed_warn_brain_capture_absent():
    """The installed .claude/hooks/warn-brain-capture.sh must not exist.

    T-0024-029 asserts the source script is deleted. This companion test asserts
    the installed copy is also absent -- so the hook is gone from both source/
    and the installed .claude/ directory (ADR-0024 R8, AC-11).
    """
    hook_path = PROJECT_ROOT / ".claude" / "hooks" / "warn-brain-capture.sh"
    assert not hook_path.exists(), (
        f".claude/hooks/warn-brain-capture.sh still exists at {hook_path}. "
        "Wave 3 cleanup must remove this script from the installed directory "
        "as well as source/claude/hooks/ (ADR-0024 R8, AC-11)."
    )
