"""Tests for hook wiring audit: SessionStart and SubagentStop registration correctness.

Verifies:
  (a) session-hydrate.sh (no-op) is NOT registered in SessionStart
  (b) prompt-compact-advisory.sh IS registered in SubagentStop with ellis `if` condition
  (c) session-hydrate-enforcement.sh IS registered in SessionStart

Both the installed .claude/settings.json and the SKILL.md template are checked.
"""

import json
import re
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT

SETTINGS_PATH = PROJECT_ROOT / ".claude" / "settings.json"
SKILL_PATH = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"


def _load_settings() -> dict:
    return json.loads(SETTINGS_PATH.read_text())


def _session_start_commands(settings: dict) -> list[str]:
    """Return all command strings registered under SessionStart."""
    return [
        h.get("command", h.get("prompt", ""))
        for m in settings["hooks"].get("SessionStart", [])
        for h in m.get("hooks", [])
    ]


def _subagent_stop_hooks(settings: dict) -> list[dict]:
    """Return all hook entries registered under SubagentStop."""
    return [
        h
        for m in settings["hooks"].get("SubagentStop", [])
        for h in m.get("hooks", [])
    ]


# ── (a) session-hydrate.sh NOT in SessionStart ───────────────────────────


def test_session_hydrate_noop_not_in_session_start_installed():
    """session-hydrate.sh (intentional no-op) must NOT be registered in SessionStart."""
    settings = _load_settings()
    commands = _session_start_commands(settings)
    noop_registrations = [c for c in commands if "session-hydrate.sh" in c and "enforcement" not in c]
    assert noop_registrations == [], (
        f"session-hydrate.sh (no-op) must not be in SessionStart. Found: {noop_registrations}"
    )


def test_session_hydrate_noop_not_in_skill_template():
    """SKILL.md template must not register session-hydrate.sh (no-op) in SessionStart."""
    skill_text = SKILL_PATH.read_text()
    # Extract just the SessionStart block to avoid false positives in comments/tables
    session_start_match = re.search(
        r'"SessionStart":\s*\[.*?\]', skill_text, re.DOTALL
    )
    assert session_start_match, "SessionStart block not found in SKILL.md"
    session_block = session_start_match.group(0)
    # session-hydrate.sh should not appear in the SessionStart block
    # (session-hydrate-enforcement.sh is fine -- it contains "hydrate" but also "enforcement")
    noop_refs = [
        line for line in session_block.splitlines()
        if "session-hydrate.sh" in line and "enforcement" not in line
    ]
    assert noop_refs == [], (
        f"session-hydrate.sh (no-op) must not appear in SKILL.md SessionStart block. Found: {noop_refs}"
    )


# ── (b) prompt-compact-advisory.sh in SubagentStop with ellis condition ───


def test_compact_advisory_in_subagent_stop_installed():
    """prompt-compact-advisory.sh must be registered in SubagentStop."""
    settings = _load_settings()
    hooks = _subagent_stop_hooks(settings)
    advisory_hooks = [
        h for h in hooks
        if "prompt-compact-advisory.sh" in h.get("prompt", "")
        or "prompt-compact-advisory.sh" in h.get("command", "")
    ]
    assert len(advisory_hooks) >= 1, (
        f"prompt-compact-advisory.sh not found in SubagentStop. All hooks: {hooks}"
    )


def test_compact_advisory_has_ellis_if_condition_installed():
    """prompt-compact-advisory.sh SubagentStop entry must have `if` condition scoped to ellis."""
    settings = _load_settings()
    hooks = _subagent_stop_hooks(settings)
    advisory_hooks = [
        h for h in hooks
        if "prompt-compact-advisory.sh" in h.get("prompt", "")
        or "prompt-compact-advisory.sh" in h.get("command", "")
    ]
    assert advisory_hooks, "prompt-compact-advisory.sh not in SubagentStop"
    if_val = advisory_hooks[0].get("if", "")
    assert if_val, "prompt-compact-advisory.sh hook missing `if` condition"
    assert "ellis" in if_val, (
        f"prompt-compact-advisory.sh `if` condition must reference 'ellis'. Got: {if_val!r}"
    )


def test_compact_advisory_in_skill_template():
    """SKILL.md SubagentStop block must include prompt-compact-advisory.sh."""
    skill_text = SKILL_PATH.read_text()
    # Locate the SubagentStop block
    subagent_stop_match = re.search(
        r'"SubagentStop":\s*\[.*?\]', skill_text, re.DOTALL
    )
    assert subagent_stop_match, "SubagentStop block not found in SKILL.md"
    block = subagent_stop_match.group(0)
    assert "prompt-compact-advisory.sh" in block, (
        "prompt-compact-advisory.sh not found in SKILL.md SubagentStop block"
    )
    assert "ellis" in block, (
        "Ellis `if` condition not found in SKILL.md SubagentStop compact-advisory entry"
    )


# ── (c) session-hydrate-enforcement.sh in SessionStart ───────────────────


def test_enforcement_hydrate_in_session_start_installed():
    """session-hydrate-enforcement.sh must be registered in SessionStart."""
    settings = _load_settings()
    commands = _session_start_commands(settings)
    enforcement_hooks = [c for c in commands if "session-hydrate-enforcement.sh" in c]
    assert len(enforcement_hooks) >= 1, (
        f"session-hydrate-enforcement.sh not found in SessionStart. Commands: {commands}"
    )


def test_enforcement_hydrate_in_skill_template():
    """SKILL.md SessionStart block must include session-hydrate-enforcement.sh."""
    skill_text = SKILL_PATH.read_text()
    session_start_match = re.search(
        r'"SessionStart":\s*\[.*?\]', skill_text, re.DOTALL
    )
    assert session_start_match, "SessionStart block not found in SKILL.md"
    block = session_start_match.group(0)
    assert "session-hydrate-enforcement.sh" in block, (
        "session-hydrate-enforcement.sh not found in SKILL.md SessionStart block"
    )


def test_boot_before_enforcement_in_session_start():
    """session-boot.sh must appear before session-hydrate-enforcement.sh in SessionStart."""
    settings = _load_settings()
    commands = _session_start_commands(settings)
    boot_indices = [i for i, c in enumerate(commands) if "session-boot.sh" in c]
    enforcement_indices = [i for i, c in enumerate(commands) if "session-hydrate-enforcement.sh" in c]
    assert boot_indices, "session-boot.sh not found in SessionStart"
    assert enforcement_indices, "session-hydrate-enforcement.sh not found in SessionStart"
    assert min(boot_indices) < min(enforcement_indices), (
        "session-boot.sh must come before session-hydrate-enforcement.sh in SessionStart"
    )
