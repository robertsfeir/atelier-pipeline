"""Tests for ADR-0020 Step 2b: SubagentStop telemetry hook. Covers T-0020-026 through T-0020-038."""

import json
import re
import subprocess

from conftest import (
    PROJECT_ROOT,
    build_subagent_start_input,
    build_subagent_stop_input,
    hide_jq_env,
    prepare_hook,
    run_hook,
    run_hook_with_project_dir,
    run_hook_without_project_dir,
)


def test_T_0020_026_has_output_true(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    inp = build_subagent_stop_input("colby", "agent-abc123", "session-xyz789", "## DoR: Requirements\nSome output here")
    r = run_hook_with_project_dir("log-agent-stop.sh", inp, hook_env)
    assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    data = json.loads(jsonl.read_text().strip().splitlines()[0])
    assert data["event"] == "stop"
    assert data["has_output"] is True
    assert data["agent_type"] == "colby"
    assert data["agent_id"] == "agent-abc123"
    assert data["session_id"] == "session-xyz789"
    assert data["timestamp"]


def test_T_0020_027_has_output_false_empty(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    inp = build_subagent_stop_input("roz", "agent-def456", "session-aaa111", "")
    r = run_hook_with_project_dir("log-agent-stop.sh", inp, hook_env)
    assert r.returncode == 0
    data = json.loads((hook_env / ".claude" / "telemetry" / "session-hooks.jsonl").read_text().strip().splitlines()[0])
    assert data["has_output"] is False


def test_T_0020_028_has_output_false_null(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    inp = build_subagent_stop_input("cal", "agent-ghi789", "session-bbb222", None)
    r = run_hook_with_project_dir("log-agent-stop.sh", inp, hook_env)
    assert r.returncode == 0
    data = json.loads((hook_env / ".claude" / "telemetry" / "session-hooks.jsonl").read_text().strip().splitlines()[0])
    assert data["has_output"] is False


def test_T_0020_029_unwritable_jsonl(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    jsonl.write_text('{"existing":"data"}\n')
    jsonl.chmod(0o444)
    inp = build_subagent_stop_input("colby", "agent-abc123", "session-xyz789", "some output")
    r = run_hook_with_project_dir("log-agent-stop.sh", inp, hook_env)
    assert r.returncode == 0
    jsonl.chmod(0o644)


def test_T_0020_030_jq_missing_fallback(hook_env):
    env = hide_jq_env(hook_env)
    env["CLAUDE_PROJECT_DIR"] = str(hook_env)
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    inp = build_subagent_stop_input("colby", "agent-abc123", "session-xyz789", "some output text")
    hook_path = prepare_hook("log-agent-stop.sh", hook_env)
    r = subprocess.run(["bash", str(hook_path)], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    assert jsonl.exists()
    data = json.loads(jsonl.read_text().strip().splitlines()[0])
    assert data["event"] == "stop"
    assert data["has_output"] is True


def test_T_0020_031_unset_project_dir(hook_env):
    inp = build_subagent_stop_input("colby", "agent-abc123", "session-xyz789", "output")
    r = run_hook_without_project_dir("log-agent-stop.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0020_032_has_output_false_key_absent(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    inp = build_subagent_stop_input("colby", "agent-abc123", "session-xyz789")  # __UNSET__
    r = run_hook_with_project_dir("log-agent-stop.sh", inp, hook_env)
    assert r.returncode == 0
    data = json.loads((hook_env / ".claude" / "telemetry" / "session-hooks.jsonl").read_text().strip().splitlines()[0])
    assert data["has_output"] is False


def test_T_0020_033_no_message_content(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    marker = "UNIQUE_CANARY_STRING_FOR_PRIVACY_TEST_abc123xyz"
    inp = build_subagent_stop_input("colby", "agent-abc123", "session-xyz789", marker)
    r = run_hook_with_project_dir("log-agent-stop.sh", inp, hook_env)
    assert r.returncode == 0
    line = (hook_env / ".claude" / "telemetry" / "session-hooks.jsonl").read_text().strip().splitlines()[0]
    assert marker not in line


def test_T_0020_034_timestamp_iso8601(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    inp = build_subagent_stop_input("colby", "agent-abc123", "session-xyz789", "output")
    r = run_hook_with_project_dir("log-agent-stop.sh", inp, hook_env)
    assert r.returncode == 0
    data = json.loads((hook_env / ".claude" / "telemetry" / "session-hooks.jsonl").read_text().strip().splitlines()[0])
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", data["timestamp"])


def test_T_0020_035_regression_warn_dor_dod(hook_env):
    inp = build_subagent_stop_input("colby", "agent-abc123", "session-xyz789", "## DoR: Requirements Extracted\nContent\n## DoD: Verification\nDone")
    r = run_hook("warn-dor-dod.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0020_036_settings_subagent_stop_both_hooks():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    stop_matchers = settings["hooks"].get("SubagentStop", [])
    all_commands = [
        h.get("command", "") for m in stop_matchers for h in m.get("hooks", [])
    ]
    assert any("warn-dor-dod.sh" in c for c in all_commands)
    assert any("log-agent-stop.sh" in c for c in all_commands)


def test_T_0020_037_two_invocations_two_lines(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    for agent, aid, msg in [("colby", "agent-1", "output 1"), ("roz", "agent-2", "output 2")]:
        inp = build_subagent_stop_input(agent, aid, "sess-1", msg)
        r = run_hook_with_project_dir("log-agent-stop.sh", inp, hook_env)
        assert r.returncode == 0
    lines = (hook_env / ".claude" / "telemetry" / "session-hooks.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        json.loads(line)


def test_T_0020_038_interleaved_start_stop(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    # start
    r = run_hook_with_project_dir("log-agent-start.sh", build_subagent_start_input("colby", "agent-1", "sess-1"), hook_env)
    assert r.returncode == 0
    # stop
    r = run_hook_with_project_dir("log-agent-stop.sh", build_subagent_stop_input("colby", "agent-1", "sess-1", "done"), hook_env)
    assert r.returncode == 0
    # start again
    r = run_hook_with_project_dir("log-agent-start.sh", build_subagent_start_input("roz", "agent-2", "sess-1"), hook_env)
    assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    entries = [json.loads(line) for line in jsonl.read_text().strip().splitlines()]
    assert len(entries) == 3
