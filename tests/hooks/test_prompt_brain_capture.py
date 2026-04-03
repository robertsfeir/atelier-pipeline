"""Tests for ADR-0021 Step 1: prompt-brain-capture.sh. Covers T-0021-002, -004, -007, -009, -010, -011, -012, -014, -105, -109."""

import json
import subprocess

from conftest import (
    PROJECT_ROOT,
    build_subagent_stop_input,
    prepare_hook,
    run_hook,
)


def test_T_0021_002_advisory_for_cal(hook_env):
    inp = build_subagent_stop_input("cal", "agent-abc123", "session-xyz789", "## DoR: Requirements\nSome output here")
    r = run_hook("prompt-brain-capture.sh", inp, hook_env)
    assert r.returncode == 0
    assert "agent_capture" in r.stdout


def test_T_0021_004_empty_agent_type(hook_env):
    inp = build_subagent_stop_input("", "agent-abc123", "session-xyz789", "Some output")
    r = run_hook("prompt-brain-capture.sh", inp, hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_007_sentinel_no_output(hook_env):
    inp = build_subagent_stop_input("sentinel", "agent-sec456", "session-xyz789", "Security audit results")
    r = run_hook("prompt-brain-capture.sh", inp, hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_009_malformed_json(hook_env):
    hook_path = prepare_hook("prompt-brain-capture.sh", hook_env)
    r = subprocess.run(
        ["bash", str(hook_path)], input="this is not json {{{{",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_010_settings_both_prompt_hooks():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    # prefetch on PreToolUse Agent with type "prompt"
    pre_matchers = [e for e in settings["hooks"]["PreToolUse"] if e.get("matcher") == "Agent"]
    prefetch_hooks = [
        h for m in pre_matchers for h in m.get("hooks", [])
        if "prompt-brain-prefetch.sh" in h.get("prompt", "")
    ]
    assert len(prefetch_hooks) >= 1
    assert prefetch_hooks[0].get("type") == "prompt"

    # capture on SubagentStop with type "prompt"
    stop_matchers = settings["hooks"].get("SubagentStop", [])
    capture_hooks = [
        h for m in stop_matchers for h in m.get("hooks", [])
        if "prompt-brain-capture.sh" in h.get("prompt", "")
    ]
    assert len(capture_hooks) >= 1
    assert capture_hooks[0].get("type") == "prompt"


def test_T_0021_011_prefetch_on_pretooluse_agent():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    pre_matchers = [e for e in settings["hooks"]["PreToolUse"] if e.get("matcher") == "Agent"]
    prefetch_hooks = [
        h for m in pre_matchers for h in m.get("hooks", [])
        if "prompt-brain-prefetch.sh" in h.get("prompt", "")
    ]
    assert len(prefetch_hooks) >= 1
    assert "prompt-brain-prefetch.sh" in prefetch_hooks[0]["prompt"]


def test_T_0021_012_capture_on_subagent_stop():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    stop_matchers = settings["hooks"].get("SubagentStop", [])
    capture_hooks = [
        h for m in stop_matchers for h in m.get("hooks", [])
        if "prompt-brain-capture.sh" in h.get("prompt", "")
    ]
    assert len(capture_hooks) >= 1
    assert "prompt-brain-capture.sh" in capture_hooks[0]["prompt"]


def test_T_0021_014_advisory_for_roz(hook_env):
    inp = build_subagent_stop_input("roz", "agent-roz789", "session-xyz789", "## DoR: QA Results\nAll checks pass")
    r = run_hook("prompt-brain-capture.sh", inp, hook_env)
    assert r.returncode == 0
    assert "agent_capture" in r.stdout
    assert "roz" in r.stdout


def test_T_0021_105_settings_json_valid():
    settings_path = PROJECT_ROOT / ".claude" / "settings.json"
    assert settings_path.exists()
    json.loads(settings_path.read_text())  # must parse


def test_T_0021_109_empty_stdin(hook_env):
    hook_path = prepare_hook("prompt-brain-capture.sh", hook_env)
    r = subprocess.run(["bash", str(hook_path)], input="", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
    assert r.returncode == 0
    assert r.stdout.strip() == ""
