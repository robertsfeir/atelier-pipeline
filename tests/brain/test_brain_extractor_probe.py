"""Behavioral tests for the three-hook mechanical brain-capture gate (ADR-0053).

The pre-ADR-0053 design used a `type: agent` SubagentStop hook to dispatch a
brain-extractor subagent; that mechanism was silently broken in Claude Code
2.1.121 (GitHub Issue #40010). ADR-0053 replaces it with three `type: command`
hooks forming a closed loop:

  1. SubagentStop (enforce-brain-capture-pending.sh) — gates internally on the
     8-agent allowlist and writes docs/pipeline/.pending-brain-capture.json.
     Never exits 2 (SubagentStop contract).
  2. PreToolUse on Agent (enforce-brain-capture-gate.sh) — main-thread only,
     blocks (exit 2) when the pending file exists and the .brain-unavailable
     sentinel does NOT.
  3. PostToolUse on agent_capture (clear-brain-capture-pending.sh) — deletes
     the pending file. Idempotent.

These tests exercise the actual scripts in .claude/hooks/ via subprocess,
asserting the three required behaviors from the ADR plus the surrounding
contract (allowlist coverage, exclusion list, main-thread guard, setup-mode
bypass, sentinel suppression).
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HOOKS_DIR = PROJECT_ROOT / ".claude" / "hooks"
PENDING_HOOK = HOOKS_DIR / "enforce-brain-capture-pending.sh"
GATE_HOOK = HOOKS_DIR / "enforce-brain-capture-gate.sh"
CLEAR_HOOK = HOOKS_DIR / "clear-brain-capture-pending.sh"

PIPELINE_DIR = PROJECT_ROOT / "docs" / "pipeline"
PENDING_FILE = PIPELINE_DIR / ".pending-brain-capture.json"
SENTINEL_FILE = PIPELINE_DIR / ".brain-unavailable"

ALLOWLISTED_AGENTS = [
    "sarah", "colby", "agatha", "robert",
    "robert-spec", "sable", "sable-ux", "ellis",
]
EXCLUDED_AGENTS = [
    "poirot", "sherlock", "sentinel", "scout",
    "distillator", "brain-extractor", "unknown-agent",
]


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def clean_pipeline_state():
    """Ensure no stale pending/sentinel files leak between tests.

    Snapshots the two files before the test, removes them, runs the test,
    then restores the snapshot so a developer running with a real pending
    capture does not lose state.
    """
    pending_snapshot = PENDING_FILE.read_bytes() if PENDING_FILE.exists() else None
    sentinel_snapshot = SENTINEL_FILE.read_bytes() if SENTINEL_FILE.exists() else None

    PENDING_FILE.unlink(missing_ok=True)
    SENTINEL_FILE.unlink(missing_ok=True)

    try:
        yield
    finally:
        PENDING_FILE.unlink(missing_ok=True)
        SENTINEL_FILE.unlink(missing_ok=True)
        if pending_snapshot is not None:
            PENDING_FILE.write_bytes(pending_snapshot)
        if sentinel_snapshot is not None:
            SENTINEL_FILE.write_bytes(sentinel_snapshot)


def _run(script: Path, payload: dict, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(PROJECT_ROOT)
    # Strip ATELIER_SETUP_MODE so its accidental presence in the dev shell
    # doesn't mask block behavior. Tests opt in explicitly via overrides.
    env.pop("ATELIER_SETUP_MODE", None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── Scripts exist and are executable ────────────────────────────────────────


@pytest.mark.parametrize("script", [PENDING_HOOK, GATE_HOOK, CLEAR_HOOK])
def test_hook_script_is_executable(script):
    assert script.exists(), f"Hook script missing: {script}"
    assert os.access(script, os.X_OK), f"Hook script not executable: {script}"


# ── enforce-brain-capture-pending.sh (SubagentStop) ─────────────────────────


@pytest.mark.parametrize("agent_type", ALLOWLISTED_AGENTS)
def test_pending_hook_writes_marker_for_allowlisted_agents(clean_pipeline_state, agent_type):
    """All 8 allowlisted agents trigger a pending-capture marker write."""
    payload = {
        "agent_type": agent_type,
        "agent_id": "abc123",
        "session_id": "test-session",
        "transcript_path": "/tmp/transcript.jsonl",
    }
    result = _run(PENDING_HOOK, payload)
    assert result.returncode == 0, (
        f"SubagentStop hook returned non-zero for {agent_type}: rc={result.returncode}, "
        f"stderr={result.stderr}"
    )
    assert PENDING_FILE.exists(), (
        f"Pending file not written for allowlisted agent {agent_type}."
    )
    parsed = json.loads(PENDING_FILE.read_text())
    assert parsed["agent_type"] == agent_type
    assert "timestamp" in parsed
    assert "transcript_path" in parsed


@pytest.mark.parametrize("agent_type", EXCLUDED_AGENTS)
def test_pending_hook_skips_excluded_agents(clean_pipeline_state, agent_type):
    """Excluded agents (poirot, sherlock, sentinel, scout, distillator,
    brain-extractor, discovered) must NOT write the pending file."""
    payload = {
        "agent_type": agent_type,
        "agent_id": "abc123",
        "session_id": "test-session",
    }
    result = _run(PENDING_HOOK, payload)
    assert result.returncode == 0, f"Hook returned non-zero for excluded {agent_type}"
    assert not PENDING_FILE.exists(), (
        f"Pending file written for excluded agent {agent_type} -- allowlist breach."
    )


def test_pending_hook_never_exits_2():
    """SubagentStop contract: hook must never exit 2 (would falsely block the stop).

    Stress with malformed and empty inputs to make sure no error path returns 2.
    """
    cases = [
        b"",
        b"not-json-at-all",
        b'{"agent_type":null}',
        b'{"agent_type":"colby","transcript_path":null}',
        b'{}',
    ]
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(PROJECT_ROOT)
    env.pop("ATELIER_SETUP_MODE", None)
    for payload in cases:
        result = subprocess.run(
            [str(PENDING_HOOK)],
            input=payload,
            capture_output=True,
            env=env,
            timeout=10,
        )
        assert result.returncode != 2, (
            f"SubagentStop hook exited 2 on input {payload!r} -- contract violation. "
            f"stderr={result.stderr.decode(errors='replace')}"
        )


def test_pending_hook_setup_mode_bypass(clean_pipeline_state):
    """ATELIER_SETUP_MODE=1 must short-circuit the hook before any write."""
    payload = {"agent_type": "colby", "agent_id": "abc"}
    result = _run(PENDING_HOOK, payload, env_overrides={"ATELIER_SETUP_MODE": "1"})
    assert result.returncode == 0
    assert not PENDING_FILE.exists(), (
        "Pending file written under ATELIER_SETUP_MODE=1 -- setup bypass missing."
    )


# ── enforce-brain-capture-gate.sh (PreToolUse on Agent) ─────────────────────


def test_gate_blocks_when_pending_exists(clean_pipeline_state):
    """ADR-0053 assertion (a): PreToolUse blocks Agent invocation when the
    pending file exists."""
    PENDING_FILE.write_text(json.dumps({
        "agent_type": "colby",
        "transcript_path": "",
        "timestamp": "2026-04-28T12:00:00Z",
    }))
    payload = {
        "tool_name": "Agent",
        "agent_id": "",  # main thread
        "tool_input": {"subagent_type": "sarah"},
    }
    result = _run(GATE_HOOK, payload)
    assert result.returncode == 2, (
        f"Gate did not block on pending capture: rc={result.returncode}, "
        f"stderr={result.stderr}"
    )
    assert "BLOCKED" in result.stderr
    assert "agent_capture" in result.stderr


def test_gate_passes_when_no_pending(clean_pipeline_state):
    """No pending file -> gate must pass cleanly."""
    payload = {
        "tool_name": "Agent",
        "agent_id": "",
        "tool_input": {"subagent_type": "sarah"},
    }
    result = _run(GATE_HOOK, payload)
    assert result.returncode == 0, (
        f"Gate blocked with no pending file: stderr={result.stderr}"
    )


def test_gate_sentinel_suppresses_block(clean_pipeline_state):
    """ADR-0053 assertion (c): .brain-unavailable sentinel suppresses the block."""
    PENDING_FILE.write_text(json.dumps({
        "agent_type": "colby",
        "transcript_path": "",
        "timestamp": "2026-04-28T12:00:00Z",
    }))
    SENTINEL_FILE.write_text("brain unreachable\n")
    payload = {
        "tool_name": "Agent",
        "agent_id": "",
        "tool_input": {"subagent_type": "sarah"},
    }
    result = _run(GATE_HOOK, payload)
    assert result.returncode == 0, (
        f"Gate did not honor .brain-unavailable sentinel: rc={result.returncode}, "
        f"stderr={result.stderr}"
    )


def test_gate_passes_when_agent_id_nonempty(clean_pipeline_state):
    """Subagent (agent_id set) invocations must pass through -- gate is
    main-thread only."""
    PENDING_FILE.write_text(json.dumps({
        "agent_type": "colby",
        "transcript_path": "",
        "timestamp": "2026-04-28T12:00:00Z",
    }))
    payload = {
        "tool_name": "Agent",
        "agent_id": "subagent-uuid-abc",
        "tool_input": {"subagent_type": "scout"},
    }
    result = _run(GATE_HOOK, payload)
    assert result.returncode == 0, (
        "Gate blocked a subagent (agent_id set) -- should be main-thread only."
    )


def test_gate_setup_mode_bypass(clean_pipeline_state):
    """ATELIER_SETUP_MODE=1 must short-circuit the gate."""
    PENDING_FILE.write_text(json.dumps({
        "agent_type": "colby",
        "transcript_path": "",
        "timestamp": "2026-04-28T12:00:00Z",
    }))
    payload = {
        "tool_name": "Agent",
        "agent_id": "",
        "tool_input": {"subagent_type": "sarah"},
    }
    result = _run(GATE_HOOK, payload, env_overrides={"ATELIER_SETUP_MODE": "1"})
    assert result.returncode == 0, (
        f"Gate did not bypass under ATELIER_SETUP_MODE=1: stderr={result.stderr}"
    )


def test_gate_ignores_non_agent_tool(clean_pipeline_state):
    """Gate must short-circuit on tool_name != Agent (e.g., Bash, Write)."""
    PENDING_FILE.write_text(json.dumps({
        "agent_type": "colby",
        "transcript_path": "",
        "timestamp": "2026-04-28T12:00:00Z",
    }))
    payload = {
        "tool_name": "Bash",
        "agent_id": "",
        "tool_input": {"command": "ls"},
    }
    result = _run(GATE_HOOK, payload)
    assert result.returncode == 0, (
        f"Gate blocked a non-Agent tool with pending capture: stderr={result.stderr}"
    )


# ── clear-brain-capture-pending.sh (PostToolUse on agent_capture) ───────────


def test_clear_hook_deletes_pending_file(clean_pipeline_state):
    """ADR-0053 assertion (b): PostToolUse on a successful agent_capture
    deletes the pending file."""
    PENDING_FILE.write_text(json.dumps({
        "agent_type": "colby",
        "transcript_path": "",
        "timestamp": "2026-04-28T12:00:00Z",
    }))
    assert PENDING_FILE.exists()

    # PostToolUse stdin shape includes tool_name and tool_response; the script
    # only acts on file deletion, so a minimal payload suffices.
    payload = {
        "tool_name": "mcp__plugin_atelier-pipeline_atelier-brain__agent_capture",
        "tool_response": {"ok": True},
    }
    result = _run(CLEAR_HOOK, payload)
    assert result.returncode == 0, f"Clear hook failed: stderr={result.stderr}"
    assert not PENDING_FILE.exists(), (
        "Clear hook did not delete the pending file -- gate would deadlock."
    )


def test_clear_hook_is_idempotent(clean_pipeline_state):
    """Clear hook must succeed when the pending file is absent (idempotent)."""
    assert not PENDING_FILE.exists()
    payload = {
        "tool_name": "mcp__plugin_atelier-pipeline_atelier-brain__agent_capture",
        "tool_response": {"ok": True},
    }
    result = _run(CLEAR_HOOK, payload)
    assert result.returncode == 0, (
        f"Clear hook non-idempotent: rc={result.returncode}, stderr={result.stderr}"
    )


# ── End-to-end loop: stop -> gate blocks -> capture clears -> gate passes ──


def test_full_capture_loop(clean_pipeline_state):
    """Integration: a stop writes pending, gate blocks, clear deletes, gate passes."""
    # 1. Allowlisted SubagentStop writes the pending marker.
    stop_result = _run(PENDING_HOOK, {
        "agent_type": "sarah",
        "agent_id": "sarah-uuid",
        "session_id": "loop-test",
        "transcript_path": "/tmp/sarah.jsonl",
    })
    assert stop_result.returncode == 0
    assert PENDING_FILE.exists()

    # 2. Gate blocks the next main-thread Agent invocation.
    gate_blocked = _run(GATE_HOOK, {
        "tool_name": "Agent",
        "agent_id": "",
        "tool_input": {"subagent_type": "colby"},
    })
    assert gate_blocked.returncode == 2

    # 3. PostToolUse on agent_capture clears the pending marker.
    clear_result = _run(CLEAR_HOOK, {
        "tool_name": "mcp__plugin_atelier-pipeline_atelier-brain__agent_capture",
        "tool_response": {"ok": True},
    })
    assert clear_result.returncode == 0
    assert not PENDING_FILE.exists()

    # 4. Gate now passes the next Agent invocation.
    gate_passes = _run(GATE_HOOK, {
        "tool_name": "Agent",
        "agent_id": "",
        "tool_input": {"subagent_type": "colby"},
    })
    assert gate_passes.returncode == 0, (
        f"Gate still blocking after clear: stderr={gate_passes.stderr}"
    )
