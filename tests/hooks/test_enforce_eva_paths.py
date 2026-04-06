"""Tests for enforce-eva-paths.sh (PreToolUse hook on Write|Edit|MultiEdit).

Eva can only write to docs/pipeline/ within the project root.
Exceptions: $HOME/.claude/projects/.../memory/ paths (auto-memory system).
Path traversal is always blocked regardless of exception status.

Covers: T-EVA-001 through T-EVA-010
"""

import os
from pathlib import Path

from conftest import build_tool_input, run_hook, run_hook_with_project_dir

HOOK = "enforce-eva-paths.sh"


# ── Traversal blocking ────────────────────────────────────────────────────


def test_T_EVA_001_traversal_path_blocked(hook_env):
    """Bare traversal path like ../../../etc/passwd is blocked."""
    inp = build_tool_input("Write", "../../../etc/passwd")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_EVA_002_absolute_path_with_traversal_after_strip_blocked(hook_env):
    """Path that after stripping PROJECT_ROOT contains .. is blocked.

    e.g. PROJECT_ROOT=/proj, path=/proj/../etc/passwd
    After stripping prefix -> ../etc/passwd which contains ..
    """
    project_root = str(hook_env)
    crafted_path = project_root + "/../etc/passwd"
    inp = build_tool_input("Write", crafted_path)
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_EVA_003_memory_path_traversal_blocked(hook_env):
    """Crafted memory path with traversal is blocked even though it starts like a valid memory path.

    e.g. $HOME/.claude/projects/myproj/memory/../../../../etc/shadow
    The traversal check must fire before the memory exception.
    """
    home = os.environ.get("HOME", "/tmp")
    crafted_path = f"{home}/.claude/projects/myprojname/memory/../../../../etc/shadow"
    inp = build_tool_input("Write", crafted_path)
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


# ── Allowed paths ─────────────────────────────────────────────────────────


def test_T_EVA_004_memory_path_allowed(hook_env):
    """Valid memory path $HOME/.claude/projects/myprojname/memory/foo.md is allowed."""
    home = os.environ.get("HOME", "/tmp")
    memory_path = f"{home}/.claude/projects/myprojname/memory/foo.md"
    inp = build_tool_input("Write", memory_path)
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 0


def test_T_EVA_005_docs_pipeline_allowed(hook_env):
    """docs/pipeline/foo.md is allowed normally."""
    inp = build_tool_input("Write", "docs/pipeline/pipeline-state.md")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 0


def test_T_EVA_006_docs_pipeline_subdir_allowed(hook_env):
    """docs/pipeline/last-qa-report.md is allowed."""
    inp = build_tool_input("Write", "docs/pipeline/last-qa-report.md")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 0


# ── Blocked paths ─────────────────────────────────────────────────────────


def test_T_EVA_007_source_path_blocked(hook_env):
    """Writing to source/ is blocked — Eva must not touch source files."""
    inp = build_tool_input("Write", "source/shared/agents/colby.md")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_T_EVA_008_docs_product_blocked(hook_env):
    """docs/product/ is blocked — only docs/pipeline/ is allowed."""
    inp = build_tool_input("Write", "docs/product/FEATURE.md")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


# ── Tool filtering ────────────────────────────────────────────────────────


def test_T_EVA_009_read_tool_ignored(hook_env):
    """Read tool calls are ignored by this hook (Write|Edit|MultiEdit only)."""
    inp = build_tool_input("Read", "source/shared/agents/colby.md")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 0


def test_T_EVA_010_edit_tool_blocked_outside_pipeline(hook_env):
    """Edit tool on non-pipeline path is also blocked."""
    inp = build_tool_input("Edit", "src/app.py")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
