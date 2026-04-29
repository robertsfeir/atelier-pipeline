"""Residual tests from ADR-0024 brain-extractor agent (deleted in v4.1.0).

The brain-extractor agent was superseded by the three-hook capture gate
(ADR-0053): SubagentStop writes a pending marker, PreToolUse on Agent blocks
Eva until she calls agent_capture, PostToolUse clears the marker. The
brain-extractor.md persona and brain-extractor.frontmatter.yml overlay no
longer exist on disk; the bulk of the original test_brain_extractor.py was
removed alongside them.

The three tests retained here are still load-bearing:

- T-0024-014 verifies settings.json remains valid JSON with the SubagentStop
  hooks block intact (the new ADR-0053 SubagentStop entry replaced the old
  brain-extractor agent entry, but the structural assertion still applies).
- T-0024-028b / T-0024-029b verify the obsolete prompt-brain-capture.sh and
  warn-brain-capture.sh scripts stay deleted from the installed
  .claude/hooks/ directory (ADR-0024 R7/R8 cleanup, still in force).

New ADR-0053 structural coverage lives in
tests/hooks/test_adr_0053_brain_capture_gate.py.
"""

import json

import pytest

from conftest import PROJECT_ROOT


# ── Paths ─────────────────────────────────────────────────────────────────

SETTINGS_JSON = PROJECT_ROOT / ".claude" / "settings.json"
SHARED_AGENTS = PROJECT_ROOT / "source" / "shared" / "agents"
CLAUDE_AGENTS = PROJECT_ROOT / "source" / "claude" / "agents"


# ── Helpers ───────────────────────────────────────────────────────────────


def load_settings() -> dict:
    """Load and parse .claude/settings.json."""
    return json.loads(SETTINGS_JSON.read_text())


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
