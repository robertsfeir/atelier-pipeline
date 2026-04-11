"""Tests for enforce-roz-paths.sh (PreToolUse hook on Write).

Roz can only Write test files and docs/pipeline/. Edit and MultiEdit are
blocked at Layer 1 by Roz's disallowedTools in her frontmatter; the hook
registers only on Write. Non-Write TOOL_NAME values exit 0 immediately.

Test IDs: T-ROZ-001 through T-ROZ-003
"""

import json

from conftest import build_tool_input, run_hook, run_hook_with_project_dir

HOOK = "enforce-roz-paths.sh"


# ── T-ROZ-001: Edit on a test file → exit 0 (hook only fires on Write) ───────

def test_T_ROZ_001_edit_call_exits_zero(hook_env):
    """Edit tool call on a test file exits 0.

    Roz's disallowedTools blocks Edit at Layer 1 so this hook never sees it in
    production. When it does arrive (e.g. test harness), TOOL_NAME != 'Write'
    so the hook exits 0 without path enforcement. Confirms no unreachable-code
    side effects and no infinite loop.
    """
    inp = build_tool_input("Edit", "tests/hooks/test_enforce_roz_paths.py")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 0


# ── T-ROZ-002: Write on a test file → exit 0 (allowed path) ──────────────────

def test_T_ROZ_002_write_test_file_allowed(hook_env):
    """Write to a test file is allowed — test_patterns in config match /tests/."""
    inp = build_tool_input("Write", "tests/hooks/test_feature.py")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 0


# ── T-ROZ-003: Write to a source file → blocked ──────────────────────────────

def test_T_ROZ_003_write_source_file_blocked(hook_env):
    """Write to a source file is blocked — Roz must not touch implementation code."""
    inp = build_tool_input("Write", "source/shared/agents/colby.md")
    r = run_hook_with_project_dir(HOOK, inp, hook_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout
