"""Tests for ADR-0032 implementation: pipeline-state-path.sh helper.

Covers T-0034-014, T-0034-015, T-0034-016, T-0034-017, T-0034-018,
       T-0034-019, T-0034-020, T-0034-064.

T-0034-064 (Roz): the exported API of pipeline-state-path.sh exposes TWO
distinct shell functions: session_state_dir and error_patterns_path. Sourcing
the file and calling each function by name produces different paths.

Colby MUST NOT modify these assertions.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT

SHARED_HOOKS_DIR = PROJECT_ROOT / "source" / "shared" / "hooks"
HELPER_PATH = SHARED_HOOKS_DIR / "pipeline-state-path.sh"
CLAUDE_HOOKS_DIR = PROJECT_ROOT / "source" / "claude" / "hooks"
SESSION_BOOT_PATH = CLAUDE_HOOKS_DIR / "session-boot.sh"
POST_COMPACT_PATH = CLAUDE_HOOKS_DIR / "post-compact-reinject.sh"


# ─── Helpers ──────────────────────────────────────────────────────────────────


def source_and_call(function_name: str, env: dict | None = None, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Source the helper and call the named function. Returns CompletedProcess."""
    cmd = ["bash", "-c", f'source "{HELPER_PATH}" && {function_name}']
    run_env = os.environ.copy()
    # Clear project dir vars by default so tests start clean
    run_env.pop("CLAUDE_PROJECT_DIR", None)
    run_env.pop("CURSOR_PROJECT_DIR", None)
    if env:
        run_env.update(env)
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=run_env,
        cwd=cwd,
        timeout=10,
    )


# ═══════════════════════════════════════════════════════════════════════
# Precondition: helper file exists
# ═══════════════════════════════════════════════════════════════════════


def test_helper_file_exists():
    """pipeline-state-path.sh exists at source/shared/hooks/."""
    assert HELPER_PATH.exists(), (
        f"pipeline-state-path.sh not found at {HELPER_PATH}. "
        "ADR-0032 Step 1 requires this file to be created."
    )


def test_helper_is_executable():
    """pipeline-state-path.sh has execute permission."""
    assert os.access(HELPER_PATH, os.X_OK), (
        f"pipeline-state-path.sh at {HELPER_PATH} is not executable."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-014: happy path with CLAUDE_PROJECT_DIR
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_014_session_state_dir_happy_path(tmp_path):
    """T-0034-014: session_state_dir() with CLAUDE_PROJECT_DIR set returns
    a path under ~/.atelier/pipeline/{slug}/{8-char-hash}/.
    """
    project_dir = str(tmp_path)
    result = source_and_call(
        "session_state_dir",
        env={"CLAUDE_PROJECT_DIR": project_dir},
    )
    assert result.returncode == 0, f"session_state_dir exited non-zero: {result.stderr}"
    output = result.stdout.strip()
    assert output, "session_state_dir returned empty output"

    # Must be under ~/.atelier/pipeline/
    home = os.path.expanduser("~")
    expected_prefix = os.path.join(home, ".atelier", "pipeline")
    assert output.startswith(expected_prefix), (
        f"session_state_dir output does not start with {expected_prefix}. "
        f"Got: {output!r}"
    )

    # Must contain exactly 3 path components after the prefix:
    # ~/.atelier/pipeline/{slug}/{hash}
    rel = output[len(expected_prefix):].lstrip("/")
    parts = [p for p in rel.split("/") if p]
    assert len(parts) == 2, (
        f"Expected ~/.atelier/pipeline/{{slug}}/{{hash}}, "
        f"got {len(parts)} path components after prefix: {output!r}"
    )

    # The hash component must be exactly 8 chars
    hash_part = parts[1]
    assert len(hash_part) == 8, (
        f"Worktree hash must be 8 chars, got {len(hash_part)!r}: {hash_part!r}"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-015: fallback when no env vars and pwd is unavailable
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_015_fallback_when_env_missing():
    """T-0034-015: session_state_dir() with no env vars exits 0 and returns
    a non-empty path (falls back to docs/pipeline or uses pwd).
    """
    # Remove both project dir env vars; let the helper use pwd
    env_override = {
        "HOME": os.path.expanduser("~"),  # keep HOME for ~/ resolution
    }
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("CURSOR_PROJECT_DIR", None)
    env.update(env_override)

    result = subprocess.run(
        ["bash", "-c", f'source "{HELPER_PATH}" && session_state_dir'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        timeout=10,
    )
    assert result.returncode == 0, (
        f"session_state_dir must exit 0 even when env vars missing. "
        f"Exit code: {result.returncode}. stderr: {result.stderr}"
    )
    output = result.stdout.strip()
    assert output, "session_state_dir must return non-empty output even in fallback"


# ═══════════════════════════════════════════════════════════════════════
# T-0034-016: two different paths hash to different 8-char prefixes
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_016_different_paths_hash_differently(tmp_path):
    """T-0034-016: two different absolute paths produce different 8-char
    worktree hashes (collision probability is negligible).
    """
    dir_a = tmp_path / "worktreeA"
    dir_b = tmp_path / "worktreeB"
    dir_a.mkdir()
    dir_b.mkdir()

    result_a = source_and_call("session_state_dir", env={"CLAUDE_PROJECT_DIR": str(dir_a)})
    result_b = source_and_call("session_state_dir", env={"CLAUDE_PROJECT_DIR": str(dir_b)})

    assert result_a.returncode == 0
    assert result_b.returncode == 0

    path_a = result_a.stdout.strip()
    path_b = result_b.stdout.strip()

    assert path_a != path_b, (
        f"Two different worktree paths produced the same state dir: {path_a!r}. "
        "Hash collision (should be ~impossible for distinct paths)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-017: error_patterns_path() returns in-repo path
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_017_error_patterns_path_in_repo(tmp_path):
    """T-0034-017: error_patterns_path() returns docs/pipeline/error-patterns.md
    regardless of session state dir. Stays in-repo per ADR-0032 Decision.
    """
    result = source_and_call(
        "error_patterns_path",
        env={"CLAUDE_PROJECT_DIR": str(tmp_path)},
    )
    assert result.returncode == 0, f"error_patterns_path exited non-zero: {result.stderr}"
    output = result.stdout.strip()
    assert output == "docs/pipeline/error-patterns.md", (
        f"error_patterns_path must return 'docs/pipeline/error-patterns.md' "
        f"(in-repo per ADR-0032). Got: {output!r}"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-018: session-boot.sh under CLAUDE_PROJECT_DIR uses state dir
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_018_session_boot_uses_state_dir(tmp_path):
    """T-0034-018: session-boot.sh sources pipeline-state-path.sh and resolves
    PIPELINE_STATE_FILE via session_state_dir, not a hardcoded docs/pipeline/.

    Verification: the source text of session-boot.sh must not contain the
    hardcoded string 'docs/pipeline/pipeline-state.md' as a literal assignment.
    """
    content = SESSION_BOOT_PATH.read_text()
    assert 'PIPELINE_STATE_FILE="docs/pipeline/pipeline-state.md"' not in content, (
        "session-boot.sh still has hardcoded PIPELINE_STATE_FILE assignment. "
        "ADR-0032 Step 1 requires using the pipeline-state-path.sh helper."
    )
    # Must source the helper
    assert "pipeline-state-path.sh" in content, (
        "session-boot.sh does not source pipeline-state-path.sh. "
        "ADR-0032 Step 1 requires the helper to be sourced."
    )
    # Must use session_state_dir
    assert "session_state_dir" in content, (
        "session-boot.sh does not call session_state_dir(). "
        "ADR-0032 Step 1 requires this call."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-019: two worktrees produce disjoint state directories
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_019_worktrees_produce_disjoint_state_dirs(tmp_path):
    """T-0034-019: two different CLAUDE_PROJECT_DIR values produce state dirs
    that do not overlap. Mechanism: create sentinel.txt in dirA; assert
    sentinel.txt is absent from dirB.
    """
    dir_a = tmp_path / "projectA"
    dir_b = tmp_path / "projectB"
    dir_a.mkdir()
    dir_b.mkdir()

    result_a = source_and_call("session_state_dir", env={"CLAUDE_PROJECT_DIR": str(dir_a)})
    result_b = source_and_call("session_state_dir", env={"CLAUDE_PROJECT_DIR": str(dir_b)})

    assert result_a.returncode == 0
    assert result_b.returncode == 0

    state_a = Path(result_a.stdout.strip())
    state_b = Path(result_b.stdout.strip())

    assert state_a != state_b, "Two different project dirs must produce different state dirs"

    # Create sentinel.txt in dirA's state directory
    state_a.mkdir(parents=True, exist_ok=True)
    sentinel = state_a / "sentinel.txt"
    sentinel.touch()

    # Assert sentinel.txt is NOT present in dirB's state directory
    assert not (state_b / "sentinel.txt").exists(), (
        f"sentinel.txt written to {state_a} was found at {state_b / 'sentinel.txt'}. "
        "State dirs must be disjoint — a write to one must never appear in the other."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-020: post-compact-reinject.sh uses same helper
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_020_post_compact_uses_helper():
    """T-0034-020: post-compact-reinject.sh sources pipeline-state-path.sh
    and reads from session_state_dir output (same helper as session-boot.sh).
    """
    assert POST_COMPACT_PATH.exists(), f"post-compact-reinject.sh not found at {POST_COMPACT_PATH}"
    content = POST_COMPACT_PATH.read_text()
    assert "pipeline-state-path.sh" in content, (
        "post-compact-reinject.sh does not source pipeline-state-path.sh. "
        "ADR-0032 Step 1 requires both hooks to use the same helper."
    )
    assert "session_state_dir" in content, (
        "post-compact-reinject.sh does not call session_state_dir(). "
        "ADR-0032 Step 1 requires this call."
    )
    # Must not use hardcoded docs/pipeline/ for state file
    # (the old PIPELINE_DIR = "$PROJECT_DIR/docs/pipeline" pattern)
    assert 'PIPELINE_DIR="$PROJECT_DIR/docs/pipeline"' not in content, (
        "post-compact-reinject.sh still has hardcoded PIPELINE_DIR path. "
        "Must use session_state_dir() instead."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-064 (Roz): helper exposes TWO distinct functions
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_064_helper_exports_two_distinct_functions(tmp_path):
    """T-0034-064: sourcing pipeline-state-path.sh and calling session_state_dir
    and error_patterns_path by their distinct names produces different paths.

    Validates the ADR-0032 'two-function API' contract:
    - session_state_dir() -> per-worktree, out-of-repo
    - error_patterns_path() -> in-repo, docs/pipeline/error-patterns.md

    Regression guard: Colby must not expose a single function that branches
    on an argument instead of two named functions.
    """
    env = {"CLAUDE_PROJECT_DIR": str(tmp_path)}

    state_result = source_and_call("session_state_dir", env=env)
    error_result = source_and_call("error_patterns_path", env=env)

    assert state_result.returncode == 0, f"session_state_dir failed: {state_result.stderr}"
    assert error_result.returncode == 0, f"error_patterns_path failed: {error_result.stderr}"

    state_path = state_result.stdout.strip()
    error_path = error_result.stdout.strip()

    assert state_path, "session_state_dir returned empty output"
    assert error_path, "error_patterns_path returned empty output"

    # The two paths must differ
    assert state_path != error_path, (
        f"session_state_dir and error_patterns_path returned the same path: {state_path!r}. "
        "These must be distinct per ADR-0032 Decision."
    )

    # error_patterns_path must return the in-repo path
    assert error_path == "docs/pipeline/error-patterns.md", (
        f"error_patterns_path must return 'docs/pipeline/error-patterns.md' "
        f"(in-repo, unchanged per ADR-0032). Got: {error_path!r}"
    )

    # session_state_dir must return something under ~/.atelier/pipeline/
    home = os.path.expanduser("~")
    expected_prefix = os.path.join(home, ".atelier", "pipeline")
    # Note: may fall back to 'docs/pipeline' if sha tools unavailable
    assert state_path.startswith(expected_prefix) or state_path == "docs/pipeline", (
        f"session_state_dir must return either a path under {expected_prefix} "
        f"or 'docs/pipeline' (fallback). Got: {state_path!r}"
    )
