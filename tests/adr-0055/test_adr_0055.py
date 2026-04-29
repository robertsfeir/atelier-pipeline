"""Behavioral tests for ADR-0055 Phase 1: brain/pipeline separation.

Phase 1 decouples the brain capture gate from the bundled atelier-brain plugin
prefix and adds a `.brain-not-installed` sentinel so pipelines can run with no
brain plugin at all.

These tests invoke the actual hook scripts via subprocess against an isolated
CLAUDE_PROJECT_DIR with a controlled stdin payload. Each test asserts on exit
code and side-effects (presence/absence of pending file).

Coverage:
1. clear-brain-capture-pending.sh deletes the pending file when tool_name
   ends with `__agent_capture` (suffix-match across plugin prefixes).
2. clear-brain-capture-pending.sh does NOT delete the pending file when
   tool_name has no `__agent_capture` suffix (false-positive guard).
3. enforce-brain-capture-gate.sh passes through (exit 0) when
   `.brain-not-installed` sentinel is present (deadlock avoidance).
4. enforce-brain-capture-pending.sh writes nothing when
   `.brain-not-installed` sentinel is present (do not write a marker that
   no tool can clear).
5. enforce-brain-capture-gate.sh still passes through when `.brain-unavailable`
   is present (regression guard for the existing escape hatch).
6. enforce-brain-capture-pending.sh still short-circuits for `.brain-unavailable`
   (regression guard).
"""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_HOOKS = PROJECT_ROOT / "source" / "claude" / "hooks"
SHARED_HOOKS = PROJECT_ROOT / "source" / "shared" / "hooks"

CLEAR_HOOK = "clear-brain-capture-pending.sh"
GATE_HOOK = "enforce-brain-capture-gate.sh"
PENDING_HOOK = "enforce-brain-capture-pending.sh"
HOOK_LIB_FILES = ["hook-lib.sh"]


# ── Test scaffolding ────────────────────────────────────────────────────


def _prepare_env(tmp_path: Path) -> Path:
    """Set up an isolated CLAUDE_PROJECT_DIR with all three brain hooks and
    a minimal enforcement-config.json. Returns the .claude/hooks dir.
    """
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    for hook in (CLEAR_HOOK, GATE_HOOK, PENDING_HOOK):
        src = SOURCE_HOOKS / hook
        dst = hooks_dir / hook
        shutil.copy2(src, dst)
        dst.chmod(dst.stat().st_mode | stat.S_IEXEC)

    # Copy shared hook library so SCRIPT_DIR-relative source resolves.
    for lib_name in HOOK_LIB_FILES:
        lib_src = SHARED_HOOKS / lib_name
        if lib_src.exists():
            shutil.copy2(lib_src, hooks_dir / lib_name)

    # Minimal enforcement-config.json for pipeline_state_dir resolution.
    (hooks_dir / "enforcement-config.json").write_text(
        json.dumps({"pipeline_state_dir": "docs/pipeline"}, indent=2)
    )

    (tmp_path / "docs" / "pipeline").mkdir(parents=True, exist_ok=True)
    return hooks_dir


def _run(hook_path: Path, stdin: str, project_dir: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env.pop("CURSOR_PROJECT_DIR", None)
    env.pop("ATELIER_SETUP_MODE", None)
    return subprocess.run(
        ["bash", str(hook_path)],
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        timeout=30,
    )


def _write_pending(project_dir: Path, agent_type: str = "colby") -> Path:
    """Drop a pending-capture marker into the isolated pipeline state dir."""
    pending = project_dir / "docs" / "pipeline" / ".pending-brain-capture.json"
    pending.write_text(
        json.dumps(
            {
                "agent_type": agent_type,
                "transcript_path": "",
                "timestamp": "2026-04-29T00:00:00Z",
            }
        )
    )
    return pending


# ── Test 1: clear hook deletes pending on __agent_capture suffix ───────


def test_clear_hook_deletes_pending_on_agent_capture_suffix(tmp_path):
    """Suffix-match: any plugin prefix is acceptable as long as the tool name
    ends in __agent_capture (ADR-0055 §Decision)."""
    hooks_dir = _prepare_env(tmp_path)
    pending = _write_pending(tmp_path)
    assert pending.exists()

    # Use a non-bundled prefix to prove the suffix match (not the old exact
    # mcp__plugin_atelier-pipeline_atelier-brain__agent_capture name).
    stdin = json.dumps({"tool_name": "mcp__plugin_mybrain__agent_capture"})
    r = _run(hooks_dir / CLEAR_HOOK, stdin, tmp_path)

    assert r.returncode == 0, (
        f"clear hook exited {r.returncode}; stderr={r.stderr!r}"
    )
    assert not pending.exists(), (
        "clear hook did not delete pending file on __agent_capture suffix"
    )


# ── Test 2: clear hook is a no-op for unrelated tools ──────────────────


def test_clear_hook_does_not_delete_pending_for_unrelated_tool(tmp_path):
    """Tools without the __agent_capture suffix must leave the pending file
    intact (false-positive guard for the suffix match)."""
    hooks_dir = _prepare_env(tmp_path)
    pending = _write_pending(tmp_path)
    assert pending.exists()

    stdin = json.dumps({"tool_name": "Edit"})
    r = _run(hooks_dir / CLEAR_HOOK, stdin, tmp_path)

    assert r.returncode == 0, (
        f"clear hook exited {r.returncode}; stderr={r.stderr!r}"
    )
    assert pending.exists(), (
        "clear hook deleted pending file for an unrelated tool name -- "
        "suffix match is too loose"
    )


# ── Test 3: gate passes through when .brain-not-installed exists ───────


def test_gate_passes_through_when_brain_not_installed(tmp_path):
    """ADR-0055: a project with no brain plugin at all touches
    .brain-not-installed; the gate must exit 0 even with a pending file."""
    hooks_dir = _prepare_env(tmp_path)
    _write_pending(tmp_path)
    sentinel = tmp_path / "docs" / "pipeline" / ".brain-not-installed"
    sentinel.touch()

    stdin = json.dumps({"tool_name": "Agent", "agent_id": ""})
    r = _run(hooks_dir / GATE_HOOK, stdin, tmp_path)

    assert r.returncode == 0, (
        f"gate hook should pass through when .brain-not-installed is set; "
        f"got exit {r.returncode}, stderr={r.stderr!r}"
    )


# ── Test 4: pending hook writes nothing when .brain-not-installed exists ─


def test_pending_hook_short_circuits_on_brain_not_installed(tmp_path):
    """ADR-0055: SubagentStop must not write a marker that no tool can
    clear. With .brain-not-installed present, the hook exits 0 without
    creating the pending file."""
    hooks_dir = _prepare_env(tmp_path)
    sentinel = tmp_path / "docs" / "pipeline" / ".brain-not-installed"
    sentinel.touch()

    pending = tmp_path / "docs" / "pipeline" / ".pending-brain-capture.json"
    assert not pending.exists()

    stdin = json.dumps(
        {
            "agent_type": "colby",
            "transcript_path": "/tmp/transcript.jsonl",
        }
    )
    r = _run(hooks_dir / PENDING_HOOK, stdin, tmp_path)

    assert r.returncode == 0, (
        f"pending hook exited {r.returncode}; stderr={r.stderr!r}"
    )
    assert not pending.exists(), (
        "pending hook wrote a marker even though .brain-not-installed is set "
        "-- no tool can clear it, the gate would deadlock"
    )


# ── Test 5: gate still honors .brain-unavailable (regression) ──────────


def test_gate_passes_through_when_brain_unavailable(tmp_path):
    """Existing escape hatch (ADR-0053): atelier_stats unreachable. The gate
    must keep passing through. Regression guard for the ADR-0055 change."""
    hooks_dir = _prepare_env(tmp_path)
    _write_pending(tmp_path)
    sentinel = tmp_path / "docs" / "pipeline" / ".brain-unavailable"
    sentinel.touch()

    stdin = json.dumps({"tool_name": "Agent", "agent_id": ""})
    r = _run(hooks_dir / GATE_HOOK, stdin, tmp_path)

    assert r.returncode == 0, (
        f"gate hook should pass through when .brain-unavailable is set; "
        f"got exit {r.returncode}, stderr={r.stderr!r}"
    )


# ── Test 6: pending hook still honors .brain-unavailable (regression) ──


def test_pending_hook_short_circuits_on_brain_unavailable(tmp_path):
    """Regression: ADR-0055 added .brain-not-installed alongside the existing
    .brain-unavailable. The original sentinel must still suppress the marker."""
    hooks_dir = _prepare_env(tmp_path)
    sentinel = tmp_path / "docs" / "pipeline" / ".brain-unavailable"
    sentinel.touch()

    pending = tmp_path / "docs" / "pipeline" / ".pending-brain-capture.json"
    assert not pending.exists()

    stdin = json.dumps(
        {
            "agent_type": "colby",
            "transcript_path": "/tmp/transcript.jsonl",
        }
    )
    r = _run(hooks_dir / PENDING_HOOK, stdin, tmp_path)

    assert r.returncode == 0, (
        f"pending hook exited {r.returncode}; stderr={r.stderr!r}"
    )
    assert not pending.exists(), (
        "pending hook wrote a marker despite .brain-unavailable being set"
    )
