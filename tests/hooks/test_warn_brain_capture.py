"""Tests for ADR-0021 Step 3: warn-brain-capture.sh. Covers T-0021-052 through T-0021-061, T-0021-106, -107, -110, -116."""

import subprocess

from conftest import (
    PROJECT_ROOT,
    build_subagent_stop_input,
    hide_jq_env,
    prepare_hook,
    run_hook,
)
import json


def _run_stderr(hook_env, inp):
    """Run the hook and capture stderr separately."""
    hook_path = prepare_hook("warn-brain-capture.sh", hook_env)
    r = subprocess.run(
        ["bash", str(hook_path)], input=inp,
        capture_output=True, text=True, timeout=30,
    )
    return r


def test_T_0021_052_agent_capture_present_no_stderr(hook_env):
    inp = build_subagent_stop_input("cal", "agent-cal123", "session-xyz789", "## DoR: Decisions\nCalled agent_capture for ADR decision.\n## DoD: Done")
    r = _run_stderr(hook_env, inp)
    assert r.returncode == 0
    assert r.stderr.strip() == ""


def test_T_0021_053_agent_capture_absent_warns_colby(hook_env):
    inp = build_subagent_stop_input("colby", "agent-colby456", "session-xyz789", "## DoR: Requirements\nBuilt the feature.\n## DoD: Done")
    r = _run_stderr(hook_env, inp)
    assert "colby" in r.stderr
    assert "brain" in r.stderr or "capture" in r.stderr or "agent_capture" in r.stderr
    # Must exit 0
    assert r.returncode == 0


def test_T_0021_054_ellis_silent(hook_env):
    inp = build_subagent_stop_input("ellis", "agent-ellis789", "session-xyz789", "Committed changes without agent_capture")
    r = _run_stderr(hook_env, inp)
    assert r.returncode == 0
    assert r.stderr.strip() == ""


def test_T_0021_055_poirot_silent(hook_env):
    inp = build_subagent_stop_input("poirot", "agent-poirot123", "session-xyz789", "Review findings without agent_capture")
    r = _run_stderr(hook_env, inp)
    assert r.returncode == 0
    assert r.stderr.strip() == ""


def test_T_0021_056_agent_capture_in_code_block(hook_env):
    msg = "## DoR: QA\nFound patterns.\n```\nagent_capture called with thought_type pattern\n```\n## DoD: Done"
    inp = build_subagent_stop_input("roz", "agent-roz456", "session-xyz789", msg)
    r = _run_stderr(hook_env, inp)
    assert r.returncode == 0
    assert r.stderr.strip() == ""


def test_T_0021_057_missing_message_warns(hook_env):
    inp = build_subagent_stop_input("cal", "agent-cal789", "session-xyz789")  # no message
    r = _run_stderr(hook_env, inp)
    assert r.returncode == 0
    assert r.stderr.strip() != ""


def test_T_0021_058_jq_missing(hook_env):
    env = hide_jq_env(hook_env)
    hook_path = prepare_hook("warn-brain-capture.sh", hook_env)
    inp = build_subagent_stop_input("cal", "agent-cal123", "session-xyz789", "Some output without capture")
    r = subprocess.run(["bash", str(hook_path)], input=inp, capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_059_settings_json_if_condition():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    stop_matchers = settings["hooks"].get("SubagentStop", [])
    bc_hooks = [
        h for m in stop_matchers for h in m.get("hooks", [])
        if h.get("command") and "warn-brain-capture.sh" in h["command"]
    ]
    assert len(bc_hooks) >= 1
    if_val = bc_hooks[0].get("if", "")
    assert if_val
    assert "cal" in if_val
    assert "colby" in if_val
    assert "roz" in if_val
    assert "agatha" in if_val


def test_T_0021_060_exits_0_on_absent_capture(hook_env):
    inp = build_subagent_stop_input("colby", "agent-colby789", "session-xyz789", "Built feature without brain calls")
    r = run_hook("warn-brain-capture.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0021_061_source_identical():
    source = PROJECT_ROOT / "source" / "claude" / "hooks" / "warn-brain-capture.sh"
    installed = PROJECT_ROOT / ".claude" / "hooks" / "warn-brain-capture.sh"
    assert source.exists()
    assert installed.exists()
    assert source.read_bytes() == installed.read_bytes()


def test_T_0021_106_roz_warns(hook_env):
    inp = build_subagent_stop_input("roz", "agent-roz123", "session-xyz789", "## QA Report\nAll checks pass.\n## DoD: Done")
    r = _run_stderr(hook_env, inp)
    assert r.returncode == 0
    assert "roz" in r.stderr


def test_T_0021_107_agatha_warns(hook_env):
    inp = build_subagent_stop_input("agatha", "agent-agatha456", "session-xyz789", "## Docs Updated\nWrote the guide.\n## DoD: Done")
    r = _run_stderr(hook_env, inp)
    assert r.returncode == 0
    assert "agatha" in r.stderr


def test_T_0021_110_empty_stdin(hook_env):
    hook_path = prepare_hook("warn-brain-capture.sh", hook_env)
    r = subprocess.run(["bash", str(hook_path)], input="", capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_116_source_hook_executable():
    assert (PROJECT_ROOT / "source" / "claude" / "hooks" / "warn-brain-capture.sh").stat().st_mode & 0o111
