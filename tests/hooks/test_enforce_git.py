"""Tests for enforce-git.sh (PreToolUse hook on Bash). Covers T-0003-031."""

import subprocess

import pytest

from conftest import (
    build_bash_input,
    build_tool_input,
    hide_jq_env,
    prepare_hook,
    run_hook,
    HOOKS_DIR,
)


def test_T_0003_031_jq_missing(hook_env):
    env = hide_jq_env(hook_env)
    inp = build_bash_input("git status")
    hook_path = prepare_hook("enforce-git.sh", hook_env)
    r = subprocess.run(["bash", str(hook_path)], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 2
    assert "jq" in r.stdout or "jq" in r.stderr


def test_git_commit_main_thread_blocked(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git commit -m test"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_git_push_main_thread_blocked(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git push origin main"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_git_add_main_thread_blocked(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git add ."), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_git_status_main_thread_allowed(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git status"), hook_env)
    assert r.returncode == 0


def test_git_diff_main_thread_allowed(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git diff --stat"), hook_env)
    assert r.returncode == 0


def test_git_commit_ellis_allowed(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git commit -m test", "ellis-123", "ellis"), hook_env)
    assert r.returncode == 0


def test_git_commit_colby_blocked(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git commit -m test", "colby-456", "colby"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_git_commit_roz_blocked(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git commit -m test", "roz-789", "roz"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_git_push_ellis_allowed(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git push origin main", "ellis-123", "ellis"), hook_env)
    assert r.returncode == 0


def test_git_add_cal_blocked(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git add .", "cal-111", "cal"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_git_status_colby_readonly_allowed(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git status", "colby-456", "colby"), hook_env)
    assert r.returncode == 0


def test_bats_execution_roz_allowed(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("bats tests/hooks/enforce-git.bats", "roz-789", "roz"), hook_env)
    assert r.returncode == 0


def test_jest_execution_colby_allowed(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("jest --testPathPattern=foo.test.ts", "colby-456", "colby"), hook_env)
    assert r.returncode == 0


def test_pytest_execution_cal_blocked(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("pytest tests/", "cal-111", "cal"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_subagent_no_agent_type_blocked(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git commit -m test", "unknown-999"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_non_bash_tool_ignored(hook_env):
    hook_path = prepare_hook("enforce-git.sh", hook_env)
    inp = '{"tool_name":"Write","tool_input":{"command":"git commit -m test"}}'
    # Run from root-level copy for backward compat
    r = subprocess.run(
        ["bash", str(hook_env / "enforce-git.sh")],
        input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30,
    )
    assert r.returncode == 0


def test_git_reset_main_thread_blocked(hook_env):
    r = run_hook("enforce-git.sh", build_bash_input("git reset --hard HEAD"), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
