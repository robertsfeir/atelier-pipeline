"""Tests for ADR-0020 Step 2a: SubagentStart telemetry hook. Covers T-0020-011 through T-0020-025."""

import json
import os
import re
import shutil
import subprocess
import stat

from conftest import (
    HOOKS_DIR,
    PROJECT_ROOT,
    build_subagent_start_input,
    hide_jq_env,
    prepare_hook,
    run_hook_with_project_dir,
    run_hook_without_project_dir,
)


def test_T_0020_011_creates_dir_and_one_line(hook_env):
    assert not (hook_env / ".claude" / "telemetry").exists()
    inp = build_subagent_start_input("colby", "agent-abc123", "session-xyz789")
    r = run_hook_with_project_dir("log-agent-start.sh", inp, hook_env)
    assert r.returncode == 0
    assert (hook_env / ".claude" / "telemetry").is_dir()
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    lines = jsonl.read_text().strip().splitlines()
    assert len(lines) == 1


def test_T_0020_012_json_fields(hook_env):
    inp = build_subagent_start_input("colby", "agent-abc123", "session-xyz789")
    r = run_hook_with_project_dir("log-agent-start.sh", inp, hook_env)
    assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    data = json.loads(jsonl.read_text().strip().splitlines()[0])
    assert data["event"] == "start"
    assert data["agent_type"] == "colby"
    assert data["agent_id"] == "agent-abc123"
    assert data["session_id"] == "session-xyz789"
    assert data["timestamp"]


def test_T_0020_013_unwritable_parent(hook_env):
    readonly_dir = hook_env / "readonly_project"
    (readonly_dir / ".claude").mkdir(parents=True)
    (readonly_dir / ".claude").chmod(0o444)
    inp = build_subagent_start_input("colby", "agent-abc123", "session-xyz789")
    hook_path = prepare_hook("log-agent-start.sh", hook_env)
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(readonly_dir)
    r = subprocess.run(["bash", str(hook_env / "log-agent-start.sh")], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 0
    assert not (readonly_dir / ".claude" / "telemetry" / "session-hooks.jsonl").exists()
    (readonly_dir / ".claude").chmod(0o755)


def test_T_0020_014_jq_missing_printf_fallback(hook_env):
    env = hide_jq_env(hook_env)
    env["CLAUDE_PROJECT_DIR"] = str(hook_env)
    inp = build_subagent_start_input("roz", "agent-def456", "session-aaa111")
    hook_path = prepare_hook("log-agent-start.sh", hook_env)
    r = subprocess.run(["bash", str(hook_path)], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    assert jsonl.exists()
    data = json.loads(jsonl.read_text().strip().splitlines()[0])
    assert data["event"] == "start"


def test_T_0020_015_unset_project_dir(hook_env):
    inp = build_subagent_start_input("colby", "agent-abc123", "session-xyz789")
    r = run_hook_without_project_dir("log-agent-start.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0020_016_empty_agent_type(hook_env):
    inp = '{"agent_type":"","agent_id":"agent-123","session_id":"sess-456"}'
    r = run_hook_with_project_dir("log-agent-start.sh", inp, hook_env)
    assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    data = json.loads(jsonl.read_text().strip().splitlines()[0])
    assert data["agent_type"] == "unknown"


def test_T_0020_017_absent_session_id(hook_env):
    inp = '{"agent_type":"colby","agent_id":"agent-123"}'
    r = run_hook_with_project_dir("log-agent-start.sh", inp, hook_env)
    assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    data = json.loads(jsonl.read_text().strip().splitlines()[0])
    assert data["session_id"] == "unknown"


def test_T_0020_018_three_invocations_three_lines(hook_env):
    for agent, aid in [("colby", "agent-1"), ("roz", "agent-2"), ("ellis", "agent-3")]:
        inp = build_subagent_start_input(agent, aid, "sess-1")
        r = run_hook_with_project_dir("log-agent-start.sh", inp, hook_env)
        assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    assert len(jsonl.read_text().strip().splitlines()) == 3


def test_T_0020_019_timestamp_iso8601(hook_env):
    inp = build_subagent_start_input("colby", "agent-abc123", "session-xyz789")
    r = run_hook_with_project_dir("log-agent-start.sh", inp, hook_env)
    assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    data = json.loads(jsonl.read_text().strip().splitlines()[0])
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", data["timestamp"])


def test_T_0020_020_path_with_spaces(hook_env):
    spaced_dir = hook_env / "my project"
    (spaced_dir / ".claude" / "hooks").mkdir(parents=True)
    inp = build_subagent_start_input("colby", "agent-abc", "sess-xyz")
    shutil.copy2(HOOKS_DIR / "log-agent-start.sh", spaced_dir / ".claude" / "hooks" / "log-agent-start.sh")
    r = subprocess.run(
        ["bash", str(spaced_dir / ".claude" / "hooks" / "log-agent-start.sh")],
        input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30,
    )
    assert r.returncode == 0
    jsonl = spaced_dir / ".claude" / "telemetry" / "session-hooks.jsonl"
    assert jsonl.exists()
    json.loads(jsonl.read_text().strip().splitlines()[0])  # validates JSON


def test_T_0020_021_concurrent_invocations(hook_env):
    prepare_hook("log-agent-start.sh", hook_env)
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    inp1 = build_subagent_start_input("colby", "agent-1", "sess-concurrent")
    inp2 = build_subagent_start_input("roz", "agent-2", "sess-concurrent")
    hook_path = str(hook_env / ".claude" / "hooks" / "log-agent-start.sh")
    p1 = subprocess.Popen(["bash", hook_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p2 = subprocess.Popen(["bash", hook_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p1.communicate(input=inp1, timeout=30)
    p2.communicate(input=inp2, timeout=30)
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    lines = jsonl.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # validates JSON


def test_T_0020_022_only_contract_fields(hook_env):
    inp = build_subagent_start_input("colby", "agent-abc123", "session-xyz789")
    r = run_hook_with_project_dir("log-agent-start.sh", inp, hook_env)
    assert r.returncode == 0
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    data = json.loads(jsonl.read_text().strip().splitlines()[0])
    assert len(data) == 5
    assert set(data.keys()) == {"event", "agent_type", "agent_id", "session_id", "timestamp"}


def test_T_0020_023_settings_json_subagent_start():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    start_matchers = settings["hooks"].get("SubagentStart", [])
    hook_commands = [
        h.get("command", "")
        for m in start_matchers for h in m.get("hooks", [])
    ]
    assert any("log-agent-start.sh" in c for c in hook_commands)


def test_T_0020_024_skill_md_includes_hook():
    skill = (PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md").read_text()
    assert "log-agent-start.sh" in skill
    assert "SubagentStart" in skill


def test_T_0020_025_unwritable_jsonl(hook_env):
    (hook_env / ".claude" / "telemetry").mkdir(parents=True, exist_ok=True)
    jsonl = hook_env / ".claude" / "telemetry" / "session-hooks.jsonl"
    jsonl.write_text('{"existing":"data"}\n')
    jsonl.chmod(0o444)
    inp = build_subagent_start_input("colby", "agent-abc123", "session-xyz789")
    r = run_hook_with_project_dir("log-agent-start.sh", inp, hook_env)
    assert r.returncode == 0
    jsonl.chmod(0o644)
