"""Regression tests for ADR-0038: git worktree commands must NOT be blocked by enforce-git.sh.

T-0038-018  git worktree add exits 0 for main thread (agent_type absent -- Eva)
T-0038-018b git worktree add exits 0 for agent_type="colby"
T-0038-019  git worktree remove exits 0 for agent_type="ellis"
T-0038-020  git worktree list exits 0 for any agent_type
T-0038-021  git add still exits 2 for main thread (regression guard)
T-0038-022  git commit still exits 2 for agent_type="colby" (regression guard)
T-0038-023  enforce-git.sh contains ADR-0038 comment documenting intentional allowance
"""

import pytest

from conftest import (
    build_bash_input,
    run_hook,
    HOOKS_DIR,
)


# ── T-0038-023: Comment presence ─────────────────────────────────────────────

def test_T_0038_023_adr_comment_present():
    """enforce-git.sh must contain the ADR-0038 intentional-allowance comment."""
    hook_text = (HOOKS_DIR / "enforce-git.sh").read_text()
    assert "ADR-0038" in hook_text
    assert "worktree" in hook_text


# ── T-0038-018: git worktree add -- main thread (Eva, agent_type absent) ─────

def test_T_0038_018_worktree_add_main_thread_allowed(hook_env):
    """git worktree add must not be blocked for the main thread (Eva, no agent_type key)."""
    inp = build_bash_input("git worktree add -b session/a1b2c3d4 ../test-repo-a1b2c3d4")
    # agent_type omitted → absent key → main thread (T-0038-018 spec: agent_type=None)
    r = run_hook("enforce-git.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-0038-018b: git worktree add -- colby ───────────────────────────────────

def test_T_0038_018b_worktree_add_colby_allowed(hook_env):
    """git worktree add must not be blocked for agent_type='colby'."""
    inp = build_bash_input(
        "git worktree add -b session/a1b2c3d4 ../test-repo-a1b2c3d4",
        "colby-456",
        "colby",
    )
    r = run_hook("enforce-git.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-0038-019: git worktree remove -- ellis ─────────────────────────────────

def test_T_0038_019_worktree_remove_ellis_allowed(hook_env):
    """git worktree remove must not be blocked for agent_type='ellis'."""
    inp = build_bash_input(
        "git worktree remove --force ../test-repo-a1b2c3d4",
        "ellis-123",
        "ellis",
    )
    r = run_hook("enforce-git.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0038_019_worktree_remove_main_thread_allowed(hook_env):
    """git worktree remove must not be blocked for the main thread."""
    inp = build_bash_input("git worktree remove --force ../test-repo-a1b2c3d4")
    r = run_hook("enforce-git.sh", inp, hook_env)
    assert r.returncode == 0


# ── T-0038-020: git worktree list -- any agent ───────────────────────────────

def test_T_0038_020_worktree_list_main_thread_allowed(hook_env):
    """git worktree list must not be blocked for the main thread."""
    r = run_hook("enforce-git.sh", build_bash_input("git worktree list"), hook_env)
    assert r.returncode == 0


def test_T_0038_020_worktree_list_colby_allowed(hook_env):
    """git worktree list must not be blocked for colby."""
    r = run_hook(
        "enforce-git.sh",
        build_bash_input("git worktree list", "colby-456", "colby"),
        hook_env,
    )
    assert r.returncode == 0


def test_T_0038_020_worktree_list_roz_allowed(hook_env):
    """git worktree list must not be blocked for roz."""
    r = run_hook(
        "enforce-git.sh",
        build_bash_input("git worktree list", "roz-789", "roz"),
        hook_env,
    )
    assert r.returncode == 0


def test_T_0038_020_worktree_list_cal_allowed(hook_env):
    """git worktree list must not be blocked for cal."""
    r = run_hook(
        "enforce-git.sh",
        build_bash_input("git worktree list", "cal-111", "cal"),
        hook_env,
    )
    assert r.returncode == 0


# ── T-0038-021: git add regression guard -- main thread blocked ──────────────

def test_T_0038_021_git_add_main_thread_still_blocked(hook_env):
    """git add must still be blocked for the main thread (regression guard)."""
    r = run_hook("enforce-git.sh", build_bash_input("git add ."), hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


# ── T-0038-022: git commit regression guard -- colby blocked ─────────────────

def test_T_0038_022_git_commit_colby_still_blocked(hook_env):
    """git commit must still be blocked for colby (regression guard)."""
    r = run_hook(
        "enforce-git.sh",
        build_bash_input('git commit -m "test"', "colby-456", "colby"),
        hook_env,
    )
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
