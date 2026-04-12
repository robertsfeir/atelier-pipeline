"""Tests for scripts/check-updates.sh path and hooks detection fixes.

T-NEW-001: source/shared/agents/ is checked, not the incorrect flat location
T-NEW-002: hooks directory is checked for new files
T-NEW-003: .sh files in source/shared/hooks/ missing from .claude/hooks/ are detected
T-NEW-004: version match produces no output
T-NEW-005: version mismatch with no new files produces update notice without "New templates:" line
T-NEW-006: hooks-only update (e.g., new hook-lib.sh) is detected and reported
"""

import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHECK_UPDATES_SH = PROJECT_ROOT / "scripts" / "check-updates.sh"

PLUGIN_VERSION = "9.9.9"
OLD_VERSION = "9.9.0"


def _make_plugin_json(plugin_root: Path, version: str = PLUGIN_VERSION) -> None:
    """Create a minimal .claude-plugin/plugin.json with the given version."""
    plugin_dir = plugin_root / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "plugin.json").write_text(f'{{"name":"atelier-pipeline","version":"{version}"}}\n')


def _run_script(plugin_root: Path, cwd: Path) -> subprocess.CompletedProcess:
    """Run check-updates.sh with PLUGIN_ROOT from the given cwd."""
    env = os.environ.copy()
    return subprocess.run(
        ["bash", str(CHECK_UPDATES_SH), str(plugin_root)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=15,
    )


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def plugin_root(tmp_path):
    """A minimal PLUGIN_ROOT with plugin.json and source directory structure."""
    _make_plugin_json(tmp_path)

    # source/shared/{agents,commands,rules,references}/
    for d in ("agents", "commands", "rules", "references"):
        (tmp_path / "source" / "shared" / d).mkdir(parents=True)

    # source/shared/hooks/ with one .sh file
    shared_hooks = tmp_path / "source" / "shared" / "hooks"
    shared_hooks.mkdir(parents=True)
    (shared_hooks / "hook-lib.sh").write_text("#!/bin/bash\n# hook-lib\n")

    # source/claude/hooks/ with one .sh file and one .json file
    claude_hooks = tmp_path / "source" / "claude" / "hooks"
    claude_hooks.mkdir(parents=True)
    (claude_hooks / "enforce-colby-paths.sh").write_text("#!/bin/bash\n# enforce colby\n")
    (claude_hooks / "enforcement-config.json").write_text('{"version":1}\n')

    return tmp_path


@pytest.fixture
def project_root(tmp_path, plugin_root):
    """A project root with .claude/ installed at OLD_VERSION."""
    claude_dir = tmp_path / ".claude"
    (claude_dir / "agents").mkdir(parents=True)
    (claude_dir / "commands").mkdir(parents=True)
    (claude_dir / "rules").mkdir(parents=True)
    (claude_dir / "references").mkdir(parents=True)
    (claude_dir / "hooks").mkdir(parents=True)
    (claude_dir / ".atelier-version").write_text(OLD_VERSION + "\n")
    return tmp_path


# ── T-NEW-001: correct shared path is checked ────────────────────────────────

def test_T_NEW_001_source_shared_agents_checked_not_source_agents(plugin_root, tmp_path):
    """T-NEW-001: source/shared/agents/ is checked, not the incorrect flat location.

    Add a new agent md to source/shared/agents/ — should appear in output.
    If the script were still using the incorrect flat path it would never find it.
    """
    # Place a new agent file in source/shared/agents/
    (plugin_root / "source" / "shared" / "agents" / "new-agent.md").write_text("# new agent\n")

    # Set up .claude with OLD_VERSION but WITHOUT the new agent installed
    claude_dir = tmp_path / ".claude"
    for d in ("agents", "commands", "rules", "references", "hooks"):
        (claude_dir / d).mkdir(parents=True)
    (claude_dir / ".atelier-version").write_text(OLD_VERSION + "\n")

    result = _run_script(plugin_root, tmp_path)
    assert result.returncode == 0
    assert "new-agent.md" in result.stdout, (
        f"Expected new-agent.md to be detected via source/shared/agents/. "
        f"Output was:\n{result.stdout}"
    )
    assert "agents/new-agent.md (new)" in result.stdout


def test_T_NEW_001b_script_does_not_look_at_nonexistent_source_agents(plugin_root, tmp_path):
    """T-NEW-001b: script silently skips the incorrect flat location (doesn't exist) — no crash."""
    # Ensure the incorrect flat location does NOT exist (only source/shared/agents/ does)
    assert not (plugin_root / "source" / "agents").exists()

    claude_dir = tmp_path / ".claude"
    for d in ("agents", "commands", "rules", "references", "hooks"):
        (claude_dir / d).mkdir(parents=True)
    (claude_dir / ".atelier-version").write_text(OLD_VERSION + "\n")

    result = _run_script(plugin_root, tmp_path)
    # Script must not crash — exit 0 expected
    assert result.returncode == 0


# ── T-NEW-002: hooks directory is checked ────────────────────────────────────

def test_T_NEW_002_hooks_directory_is_checked_for_new_files(plugin_root, tmp_path):
    """T-NEW-002: hooks directory is checked for new files on Claude Code platform."""
    # .claude/hooks/ exists but is missing hook-lib.sh (which is in source/shared/hooks/)
    claude_dir = tmp_path / ".claude"
    for d in ("agents", "commands", "rules", "references", "hooks"):
        (claude_dir / d).mkdir(parents=True)
    (claude_dir / ".atelier-version").write_text(OLD_VERSION + "\n")

    result = _run_script(plugin_root, tmp_path)
    assert result.returncode == 0
    # hook-lib.sh is in source/shared/hooks/ but not in .claude/hooks/ — must be detected
    assert "hook-lib.sh" in result.stdout, (
        f"Expected hook-lib.sh to be detected. Output:\n{result.stdout}"
    )


def test_T_NEW_002b_hooks_not_checked_for_cursor_platform(plugin_root, tmp_path):
    """T-NEW-002b: hooks directory is NOT checked for Cursor platform."""
    # Set up .cursor with OLD_VERSION, with hooks dir missing source hooks
    cursor_dir = tmp_path / ".cursor"
    for d in ("agents", "commands", "rules", "references", "hooks"):
        (cursor_dir / d).mkdir(parents=True)
    (cursor_dir / ".atelier-version").write_text(OLD_VERSION + "\n")

    result = _run_script(plugin_root, tmp_path)
    assert result.returncode == 0
    # hook-lib.sh must NOT appear — Cursor doesn't get hook checks
    assert "hook-lib.sh" not in result.stdout, (
        f"hook-lib.sh should not be detected for Cursor platform. Output:\n{result.stdout}"
    )


# ── T-NEW-003: .sh files in source/shared/hooks/ missing from .claude/hooks/ ─

def test_T_NEW_003_sh_files_missing_from_claude_hooks_detected(plugin_root, tmp_path):
    """T-NEW-003: .sh files in source/shared/hooks/ missing from .claude/hooks/ are detected."""
    claude_dir = tmp_path / ".claude"
    for d in ("agents", "commands", "rules", "references", "hooks"):
        (claude_dir / d).mkdir(parents=True)
    # Intentionally do NOT create hook-lib.sh in .claude/hooks/
    (claude_dir / ".atelier-version").write_text(OLD_VERSION + "\n")

    result = _run_script(plugin_root, tmp_path)
    assert result.returncode == 0
    assert "hook-lib.sh" in result.stdout

    # Also check that source/claude/hooks/ files are detected
    # enforce-colby-paths.sh is in source/claude/hooks/ but not in .claude/hooks/
    assert "enforce-colby-paths.sh" in result.stdout, (
        f"Expected enforce-colby-paths.sh (source/claude/hooks/) to be detected. "
        f"Output:\n{result.stdout}"
    )


def test_T_NEW_003b_json_files_in_claude_hooks_detected(plugin_root, tmp_path):
    """T-NEW-003b: .json files (e.g., enforcement-config.json) missing from .claude/hooks/ are detected."""
    claude_dir = tmp_path / ".claude"
    for d in ("agents", "commands", "rules", "references", "hooks"):
        (claude_dir / d).mkdir(parents=True)
    (claude_dir / ".atelier-version").write_text(OLD_VERSION + "\n")

    result = _run_script(plugin_root, tmp_path)
    assert result.returncode == 0
    assert "enforcement-config.json" in result.stdout, (
        f"Expected enforcement-config.json to be detected. Output:\n{result.stdout}"
    )


# ── T-NEW-004: version match produces no output ───────────────────────────────

def test_T_NEW_004_version_match_produces_no_output(plugin_root, tmp_path):
    """T-NEW-004: version match produces no output (silent)."""
    claude_dir = tmp_path / ".claude"
    for d in ("agents", "commands", "rules", "references", "hooks"):
        (claude_dir / d).mkdir(parents=True)
    # Install ALL source files so nothing is missing
    (claude_dir / "hooks" / "hook-lib.sh").write_text("installed\n")
    (claude_dir / "hooks" / "pipeline-state-path.sh").write_text("installed\n")
    (claude_dir / "hooks" / "session-boot.sh").write_text("installed\n")
    (claude_dir / "hooks" / "enforce-colby-paths.sh").write_text("installed\n")
    (claude_dir / "hooks" / "enforcement-config.json").write_text("installed\n")
    # Write CURRENT version — should produce no output
    (claude_dir / ".atelier-version").write_text(PLUGIN_VERSION + "\n")

    result = _run_script(plugin_root, tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "", (
        f"Expected silent output on version match. Got:\n{result.stdout}"
    )


# ── T-NEW-005: version mismatch with no new files ────────────────────────────

def test_T_NEW_005_version_mismatch_no_new_files_no_new_templates_line(plugin_root, tmp_path):
    """T-NEW-005: version mismatch with no new files produces update notice without 'New templates:' line."""
    claude_dir = tmp_path / ".claude"
    for d in ("agents", "commands", "rules", "references", "hooks"):
        (claude_dir / d).mkdir(parents=True)
    # Install ALL source files so nothing is missing
    (claude_dir / "hooks" / "hook-lib.sh").write_text("installed\n")
    (claude_dir / "hooks" / "pipeline-state-path.sh").write_text("installed\n")
    (claude_dir / "hooks" / "session-boot.sh").write_text("installed\n")
    (claude_dir / "hooks" / "enforce-colby-paths.sh").write_text("installed\n")
    (claude_dir / "hooks" / "enforcement-config.json").write_text("installed\n")
    # Write OLD version — triggers mismatch but no new files
    (claude_dir / ".atelier-version").write_text(OLD_VERSION + "\n")

    result = _run_script(plugin_root, tmp_path)
    assert result.returncode == 0
    assert "[atelier-pipeline]" in result.stdout
    assert "update available" in result.stdout
    assert "New templates:" not in result.stdout, (
        f"'New templates:' line should not appear when no files are missing. "
        f"Output:\n{result.stdout}"
    )


# ── T-NEW-006: hooks-only update is detected ─────────────────────────────────

def test_T_NEW_006_hooks_only_update_detected_and_reported(plugin_root, tmp_path):
    """T-NEW-006: hooks-only update (e.g., new hook-lib.sh) is detected and reported."""
    # Place a brand-new hook in source/shared/hooks/ that doesn't exist in .claude/hooks/
    new_hook = plugin_root / "source" / "shared" / "hooks" / "new-shared-hook.sh"
    new_hook.write_text("#!/bin/bash\n# new hook\n")

    claude_dir = tmp_path / ".claude"
    for d in ("agents", "commands", "rules", "references", "hooks"):
        (claude_dir / d).mkdir(parents=True)
    # Install the previously-known hooks but NOT new-shared-hook.sh
    (claude_dir / "hooks" / "hook-lib.sh").write_text("installed\n")
    (claude_dir / "hooks" / "pipeline-state-path.sh").write_text("installed\n")
    (claude_dir / "hooks" / "session-boot.sh").write_text("installed\n")
    (claude_dir / "hooks" / "enforce-colby-paths.sh").write_text("installed\n")
    (claude_dir / "hooks" / "enforcement-config.json").write_text("installed\n")
    (claude_dir / ".atelier-version").write_text(OLD_VERSION + "\n")

    result = _run_script(plugin_root, tmp_path)
    assert result.returncode == 0
    assert "new-shared-hook.sh" in result.stdout, (
        f"Expected new-shared-hook.sh to be detected as new hook. Output:\n{result.stdout}"
    )
    assert "New templates:" in result.stdout
    assert "hooks/new-shared-hook.sh (new)" in result.stdout
