"""Tests for ADR-0021 Step 1: prompt-brain-prefetch.sh. Covers T-0021-001, -003, -005, -006, -008, -013, -015, -099, -100, -117."""

import subprocess

from conftest import (
    PROJECT_ROOT,
    build_agent_input,
    hide_jq_env,
    prepare_hook,
    run_hook,
)


def test_T_0021_001_advisory_for_colby(hook_env):
    r = run_hook("prompt-brain-prefetch.sh", build_agent_input("colby"), hook_env)
    assert r.returncode == 0
    assert "agent_search" in r.stdout


def test_T_0021_003_missing_tool_input(hook_env):
    r = run_hook("prompt-brain-prefetch.sh", '{"tool_name":"Agent"}', hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_005_ellis_no_output(hook_env):
    r = run_hook("prompt-brain-prefetch.sh", build_agent_input("ellis"), hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_006_poirot_no_output(hook_env):
    r = run_hook("prompt-brain-prefetch.sh", build_agent_input("poirot"), hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_008_jq_missing(hook_env):
    env = hide_jq_env(hook_env)
    hook_path = prepare_hook("prompt-brain-prefetch.sh", hook_env)
    r = subprocess.run(
        ["bash", str(hook_path)], input=build_agent_input("colby"),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_013_advisory_for_cal(hook_env):
    r = run_hook("prompt-brain-prefetch.sh", build_agent_input("cal"), hook_env)
    assert r.returncode == 0
    assert "agent_search" in r.stdout
    assert "cal" in r.stdout


def test_T_0021_015_advisory_for_agatha(hook_env):
    r = run_hook("prompt-brain-prefetch.sh", build_agent_input("agatha"), hook_env)
    assert r.returncode == 0
    assert "agent_search" in r.stdout


def test_T_0021_099_empty_stdin(hook_env):
    hook_path = prepare_hook("prompt-brain-prefetch.sh", hook_env)
    r = subprocess.run(["bash", str(hook_path)], input="", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_T_0021_100_installed_hooks_executable():
    """prompt-brain-prefetch.sh must be executable. prompt-brain-capture.sh was removed by ADR-0024 R7
    (brain capture now handled mechanically by brain-extractor SubagentStop hook)."""
    assert (PROJECT_ROOT / ".claude" / "hooks" / "prompt-brain-prefetch.sh").stat().st_mode & 0o111
    # Verify brain-extractor exists as the replacement mechanism
    assert (PROJECT_ROOT / "source" / "shared" / "agents" / "brain-extractor.md").is_file()


def test_T_0021_117_source_hooks_executable():
    # Wave 3: prompt-brain-capture.sh removed from source/ (ADR-0024 R7)
    assert (PROJECT_ROOT / "source" / "claude" / "hooks" / "prompt-brain-prefetch.sh").stat().st_mode & 0o111
