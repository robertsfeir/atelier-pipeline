"""Tests for ADR-0021 Step 1: prompt-brain-prefetch.sh.

Covers T-0021-001, -003, -005, -006, -008, -013, -015, -099, -100, -117 and
ADR-0033 T-0033-016, T-0033-017.

ADR-0033 Step 6 (m4/G2) narrows the hook's scope from cal/colby/roz/agatha
to cal/colby/roz only — paired with scout swarm enforcement which also only
gates those three agents. T-0021-015 is FLIPPED in this file to assert the
new (empty) behavior for agatha.
"""

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
    """FLIPPED by ADR-0033 Step 6 (m4/G2).

    The prefetch hook is now narrowed to cal/colby/roz only — matches scout
    swarm enforcement scope. Invoking Agatha must produce EMPTY output, not
    a reminder. Agatha has no scout evidence requirement, so the paired
    prefetch reminder makes no sense for her. This is the "silent drop" we
    explicitly want: Agatha falls into the wildcard branch of the case
    statement and exits 0 with no output.
    """
    r = run_hook("prompt-brain-prefetch.sh", build_agent_input("agatha"), hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == "", (
        f"Agatha should produce empty output after ADR-0033 Step 6 narrowing. "
        f"Got: {r.stdout!r}"
    )


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


# ═══════════════════════════════════════════════════════════════════════
# ADR-0033 Step 6 (m4/G2): narrow scope to scout-gated agents
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_016_agatha_produces_empty_output(hook_env):
    """T-0033-016: prompt-brain-prefetch.sh must produce EMPTY output when
    invoked with subagent_type=agatha (ADR-0033 Step 6 narrowing).

    This is the explicit empty-output assertion for agatha — a direct
    companion to the flipped T-0021-015. Keeping both tests guards against
    a future "restore agatha" revert going unnoticed in either file.
    """
    r = run_hook("prompt-brain-prefetch.sh", build_agent_input("agatha"), hook_env)
    assert r.returncode == 0
    assert r.stdout.strip() == "", (
        f"Agatha should fall into the wildcard case and exit silently. "
        f"Got: {r.stdout!r}"
    )


def test_T_0033_017_cal_colby_roz_still_produce_reminder(hook_env):
    """T-0033-017: prompt-brain-prefetch.sh still produces reminder output for
    cal, colby, and roz after the ADR-0033 Step 6 narrowing. Regression
    protection — make sure we narrow the scope without breaking the three
    scout-gated agents.
    """
    for agent in ("cal", "colby", "roz"):
        r = run_hook("prompt-brain-prefetch.sh", build_agent_input(agent), hook_env)
        assert r.returncode == 0, (
            f"prompt-brain-prefetch.sh failed for {agent}: returncode {r.returncode}, "
            f"output {r.stdout!r}"
        )
        assert "agent_search" in r.stdout, (
            f"{agent} should still receive the BRAIN PREFETCH REMINDER after "
            f"ADR-0033 Step 6 narrowing. Got: {r.stdout!r}"
        )
        assert agent in r.stdout, (
            f"Reminder for {agent} should mention the agent name. Got: {r.stdout!r}"
        )
