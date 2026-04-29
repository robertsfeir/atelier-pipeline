"""Structural tests for the ADR-0053 three-hook brain-capture gate.

ADR-0053 supersedes the ADR-0024 brain-extractor agent with a closed-loop
mechanical gate composed of three `type: command` hooks:

1. SubagentStop -> enforce-brain-capture-pending.sh
   Writes {pipeline_state_dir}/.pending-brain-capture.json whenever an agent
   in the 8-agent allowlist (sarah, colby, agatha, robert, robert-spec,
   sable, sable-ux, ellis) finishes.

2. PreToolUse on Agent -> enforce-brain-capture-gate.sh
   Blocks Eva's next Agent invocation while the pending file exists, forcing
   her to call agent_capture with curated content first.

3. PostToolUse on agent_capture -> clear-brain-capture-pending.sh
   Deletes the pending file on successful capture, releasing the gate.

These tests are pure file/JSON assertions -- they verify the hook scripts
exist, are executable, are wired in settings.json, the allowlist is correct,
and that the deleted brain-extractor agent files do NOT come back. No hook
execution is performed here; behavioral coverage of the individual scripts
lives in their dedicated test files.
"""

import json
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


# ── Paths ─────────────────────────────────────────────────────────────────

SETTINGS_JSON = PROJECT_ROOT / ".claude" / "settings.json"

SOURCE_HOOKS_DIR = PROJECT_ROOT / "source" / "claude" / "hooks"
INSTALLED_HOOKS_DIR = PROJECT_ROOT / ".claude" / "hooks"

PENDING_HOOK = "enforce-brain-capture-pending.sh"
GATE_HOOK = "enforce-brain-capture-gate.sh"
CLEAR_HOOK = "clear-brain-capture-pending.sh"

ALLOWLIST_AGENTS = [
    "sarah",
    "colby",
    "agatha",
    "robert",
    "robert-spec",
    "sable",
    "sable-ux",
    "ellis",
]


def _settings() -> dict:
    return json.loads(SETTINGS_JSON.read_text())


# ═══════════════════════════════════════════════════════════════════════
# Hook script presence (source + installed)
# ═══════════════════════════════════════════════════════════════════════


def test_pending_hook_exists_in_source_and_installed():
    """enforce-brain-capture-pending.sh must exist in both source/claude/hooks/
    and the installed .claude/hooks/."""
    assert (SOURCE_HOOKS_DIR / PENDING_HOOK).is_file(), (
        f"missing {SOURCE_HOOKS_DIR / PENDING_HOOK}"
    )
    assert (INSTALLED_HOOKS_DIR / PENDING_HOOK).is_file(), (
        f"missing {INSTALLED_HOOKS_DIR / PENDING_HOOK}"
    )


def test_gate_hook_exists_in_source_and_installed():
    """enforce-brain-capture-gate.sh must exist in both source/claude/hooks/
    and the installed .claude/hooks/."""
    assert (SOURCE_HOOKS_DIR / GATE_HOOK).is_file(), (
        f"missing {SOURCE_HOOKS_DIR / GATE_HOOK}"
    )
    assert (INSTALLED_HOOKS_DIR / GATE_HOOK).is_file(), (
        f"missing {INSTALLED_HOOKS_DIR / GATE_HOOK}"
    )


def test_clear_hook_exists_in_source_and_installed():
    """clear-brain-capture-pending.sh must exist in both source/claude/hooks/
    and the installed .claude/hooks/."""
    assert (SOURCE_HOOKS_DIR / CLEAR_HOOK).is_file(), (
        f"missing {SOURCE_HOOKS_DIR / CLEAR_HOOK}"
    )
    assert (INSTALLED_HOOKS_DIR / CLEAR_HOOK).is_file(), (
        f"missing {INSTALLED_HOOKS_DIR / CLEAR_HOOK}"
    )


# ═══════════════════════════════════════════════════════════════════════
# Installed hook executability
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "hook_name",
    [PENDING_HOOK, GATE_HOOK, CLEAR_HOOK],
)
def test_installed_hooks_are_executable(hook_name):
    """All three installed hooks must be executable (any of u/g/o execute bits)."""
    path = INSTALLED_HOOKS_DIR / hook_name
    assert path.is_file(), f"missing {path}"
    mode = path.stat().st_mode
    assert mode & 0o111, (
        f"{path} is not executable (mode={oct(mode)}). "
        "Hooks must have at least one execute bit set so the runtime can spawn them."
    )


# ═══════════════════════════════════════════════════════════════════════
# settings.json wiring
# ═══════════════════════════════════════════════════════════════════════


def _hook_command_strings(block: list) -> list[str]:
    """Flatten a settings.json hook matcher block into the list of `command` strings."""
    out = []
    for entry in block:
        for hook in entry.get("hooks", []):
            cmd = hook.get("command")
            if cmd:
                out.append(cmd)
    return out


def test_settings_subagentstop_includes_pending_hook():
    """settings.json SubagentStop hooks must invoke enforce-brain-capture-pending.sh."""
    settings = _settings()
    subagent_stop = settings["hooks"].get("SubagentStop", [])
    commands = _hook_command_strings(subagent_stop)
    assert any(PENDING_HOOK in c for c in commands), (
        f"SubagentStop block does not invoke {PENDING_HOOK}. "
        f"Commands present: {commands}"
    )


def test_settings_pretooluse_agent_includes_gate_hook():
    """settings.json PreToolUse on Agent must invoke enforce-brain-capture-gate.sh."""
    settings = _settings()
    pre = settings["hooks"].get("PreToolUse", [])
    agent_blocks = [b for b in pre if b.get("matcher") == "Agent"]
    assert agent_blocks, "settings.json PreToolUse has no `matcher: Agent` block"
    commands = _hook_command_strings(agent_blocks)
    assert any(GATE_HOOK in c for c in commands), (
        f"PreToolUse/Agent block does not invoke {GATE_HOOK}. "
        f"Commands present: {commands}"
    )


def test_settings_posttooluse_includes_clear_hook():
    """settings.json PostToolUse must invoke clear-brain-capture-pending.sh.

    Per ADR-0055, the PostToolUse entry omits the `matcher` field so the hook
    fires on every PostToolUse event; the script then filters internally on
    the `__agent_capture` tool-name suffix. This decouples the gate from a
    specific MCP server name (the prior `mcp__plugin_atelier-pipeline_atelier-brain__agent_capture`
    exact match).
    """
    settings = _settings()
    post = settings["hooks"].get("PostToolUse", [])
    commands = _hook_command_strings(post)
    assert any(CLEAR_HOOK in c for c in commands), (
        f"PostToolUse block does not invoke {CLEAR_HOOK}. "
        f"Commands present: {commands}"
    )


# ═══════════════════════════════════════════════════════════════════════
# Allowlist coverage in the SubagentStop pending hook
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("agent", ALLOWLIST_AGENTS)
def test_pending_hook_allowlist_includes_agent(agent):
    """All 8 brain-grade producers must appear in the SubagentStop pending hook
    so SubagentStop writes a pending marker for them."""
    text = (SOURCE_HOOKS_DIR / PENDING_HOOK).read_text()
    assert agent in text, (
        f"{PENDING_HOOK} does not mention `{agent}` in its allowlist. "
        f"Expected all 8 brain-grade agents: {ALLOWLIST_AGENTS}"
    )


# ═══════════════════════════════════════════════════════════════════════
# Deleted brain-extractor artifacts must stay deleted
# ═══════════════════════════════════════════════════════════════════════


def test_brain_extractor_persona_is_deleted():
    """source/shared/agents/brain-extractor.md must NOT exist.

    The brain-extractor agent was superseded by the ADR-0053 three-hook gate.
    Re-introducing the persona file would imply a parallel, potentially
    looping capture path.
    """
    path = PROJECT_ROOT / "source" / "shared" / "agents" / "brain-extractor.md"
    assert not path.exists(), (
        f"brain-extractor.md unexpectedly present at {path}. "
        "ADR-0053 deleted this agent; do not re-introduce it."
    )


def test_brain_extractor_frontmatter_is_deleted():
    """source/claude/agents/brain-extractor.frontmatter.yml must NOT exist.

    Companion to the persona-deleted test above. The frontmatter overlay is
    only meaningful when paired with a body in shared/agents/, so its
    presence alone would be a partial-resurrection hazard.
    """
    path = (
        PROJECT_ROOT
        / "source"
        / "claude"
        / "agents"
        / "brain-extractor.frontmatter.yml"
    )
    assert not path.exists(), (
        f"brain-extractor.frontmatter.yml unexpectedly present at {path}. "
        "ADR-0053 deleted this overlay; do not re-introduce it."
    )
