"""Tests for ADR-0020 Step 1: `if` conditionals on existing hooks. Covers T-0020-001 through T-0020-010."""

import json
import subprocess

from conftest import (
    PROJECT_ROOT,
    build_agent_input,
    build_bash_input,
    build_tool_input,
    run_hook,
    write_pipeline_status,
)


def test_T_0020_001_enforce_git_if_field():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    bash_matchers = [e for e in settings["hooks"]["PreToolUse"] if e.get("matcher") == "Bash"]
    git_hooks = [
        h for m in bash_matchers for h in m.get("hooks", [])
        if "enforce-git.sh" in h.get("command", "")
    ]
    assert len(git_hooks) >= 1
    if_val = git_hooks[0].get("if", "")
    assert if_val
    assert "tool_input.command" in if_val
    assert "git " in if_val


# ADR-0025 supersedes: warn-dor-dod.sh deleted from SubagentStop; replaced by session-hydrate.sh in SessionStart (ADR-0025 R11, R9)
def test_T_0020_002_warn_dor_dod_if_field():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    stop_matchers = settings["hooks"].get("SubagentStop", [])
    # warn-dor-dod.sh must be absent from SubagentStop after ADR-0025
    dod_hooks = [
        h for m in stop_matchers for h in m.get("hooks", [])
        if h.get("command") and "warn-dor-dod.sh" in h["command"]
    ]
    assert len(dod_hooks) == 0, (
        "warn-dor-dod.sh must not appear in SubagentStop after ADR-0025 deleted it. "
        f"Found: {dod_hooks}"
    )
    # Replacement: session-hydrate.sh must be wired in SessionStart
    session_start = settings["hooks"].get("SessionStart", [])
    hydrate_hooks = [
        h for m in session_start for h in m.get("hooks", [])
        if h.get("command") and "session-hydrate.sh" in h["command"]
    ]
    assert len(hydrate_hooks) >= 1, (
        "session-hydrate.sh must be present in SessionStart after ADR-0025 R9. "
        f"SessionStart hooks: {session_start}"
    )


def test_T_0020_003_regression_enforce_git(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git commit -m test"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0020_004_regression_enforce_paths(hook_env):
    r = run_hook("enforce-eva-paths.sh", build_tool_input("Write", "docs/guide/foo.md", ""), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0020_005_regression_enforce_sequencing(hook_env):
    write_pipeline_status(hook_env, '{"roz_qa":"FAIL","phase":"review"}')
    (hook_env / "enforcement-config.json").write_text(
        json.dumps({"pipeline_state_dir": str(hook_env / "docs" / "pipeline")})
    )
    r = run_hook("enforce-sequencing.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0020_006_regression_enforce_pipeline_activation(hook_env):
    (hook_env / "docs" / "pipeline" / "pipeline-state.md").unlink(missing_ok=True)
    (hook_env / "enforcement-config.json").write_text(
        json.dumps({"pipeline_state_dir": str(hook_env / "docs" / "pipeline")})
    )
    r = run_hook("enforce-pipeline-activation.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0020_007_skill_md_if_values():
    settings_file = PROJECT_ROOT / ".claude" / "settings.json"
    skill_file = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"
    assert settings_file.exists()
    assert skill_file.exists()

    settings = json.loads(settings_file.read_text())
    skill_text = skill_file.read_text()

    # Extract if value for enforce-git.sh
    bash_matchers = [e for e in settings["hooks"]["PreToolUse"] if e.get("matcher") == "Bash"]
    git_hooks = [
        h for m in bash_matchers for h in m.get("hooks", [])
        if "enforce-git.sh" in h.get("command", "")
    ]
    git_if = git_hooks[0].get("if", "")
    assert git_if
    assert git_if in skill_text

    # Extract if value for warn-dor-dod.sh
    stop_matchers = settings["hooks"].get("SubagentStop", [])
    dod_hooks = [
        h for m in stop_matchers for h in m.get("hooks", [])
        if h.get("command") and "warn-dor-dod.sh" in h["command"]
    ]
    dod_if = dod_hooks[0].get("if", "")
    assert dod_if
    assert dod_if in skill_text


def test_T_0020_008_enforce_git_direct_call(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git commit -m 'test message'"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_0020_009_enforce_git_if_field_type():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    bash_matchers = [e for e in settings["hooks"]["PreToolUse"] if e.get("matcher") == "Bash"]
    git_hooks = [
        h for m in bash_matchers for h in m.get("hooks", [])
        if "enforce-git.sh" in h.get("command", "")
    ]
    if_val = git_hooks[0].get("if")
    assert isinstance(if_val, str)
    assert len(if_val) > 0


# ADR-0025 supersedes: warn-dor-dod.sh deleted from SubagentStop; SessionStart carries session-hydrate.sh instead (ADR-0025 R11, R9)
def test_T_0020_010_warn_dor_dod_if_field_type():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    stop_matchers = settings["hooks"].get("SubagentStop", [])
    # warn-dor-dod.sh must not be present in SubagentStop after ADR-0025
    dod_hooks = [
        h for m in stop_matchers for h in m.get("hooks", [])
        if h.get("command") and "warn-dor-dod.sh" in h["command"]
    ]
    assert len(dod_hooks) == 0, (
        "warn-dor-dod.sh must not appear in SubagentStop after ADR-0025 deleted it."
    )
    # Replacement: session-hydrate.sh command must be a non-empty string in SessionStart
    session_start = settings["hooks"].get("SessionStart", [])
    hydrate_hooks = [
        h for m in session_start for h in m.get("hooks", [])
        if h.get("command") and "session-hydrate.sh" in h["command"]
    ]
    assert len(hydrate_hooks) >= 1
    cmd_val = hydrate_hooks[0].get("command")
    assert isinstance(cmd_val, str)
    assert len(cmd_val) > 0
