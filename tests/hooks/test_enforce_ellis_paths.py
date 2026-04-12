"""Tests for ADR-0034 Wave 2 Step 2.2: enforce-ellis-paths.sh.

Covers T-0034-037, T-0034-038, T-0034-039.

Follows the template established by test_enforce_colby_paths.py.

IMPORTANT: S4 CONTRADICTION CONTEXT (ADR-0034 Notes for Colby #8):
ADR-0022 R20 established Ellis as a commit-only agent. The current
enforce-ellis-paths.sh allows writes to CHANGELOG.md, git config files
(.gitignore, .gitattributes, .gitmodules), AND all CI/CD paths (.github/,
.gitlab-ci*, .gitlab/, .circleci/, Jenkinsfile*, Dockerfile*, docker-compose*,
deploy/, infra/, terraform/, pulumi/, k8s/, kubernetes/).

The contradiction (S4) is: ADR-0022 R20 says Ellis writes only to
CHANGELOG.md and git config files, but the hook ALSO allows CI/CD paths.
This is not yet resolved. Wave 2 tests lock TODAY's hook behavior.
Resolution happens in Wave 4 via a new ADR.

These tests document what the hook currently does, not what the post-S4
resolution behavior will be. Do not change these tests when resolving S4 --
supersede them with new tests in the Wave 4 ADR.

Colby MUST NOT modify these assertions.
"""

import json
from pathlib import Path

import pytest

from conftest import (
    PROJECT_ROOT,
    build_per_agent_input,
    run_per_agent_hook,
)

HOOK = "enforce-ellis-paths.sh"
HOOK_PATH = PROJECT_ROOT / "source" / "claude" / "hooks" / HOOK
ENFORCEMENT_CONFIG = PROJECT_ROOT / "source" / "claude" / "hooks" / "enforcement-config.json"


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-037: enforce-ellis-paths.sh blocks a write to an application source file
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_037_ellis_blocked_from_application_source(tmp_path):
    """enforce-ellis-paths.sh must block a Write to src/api/server.js.

    Ellis is the commit agent. She may write to CHANGELOG.md, git config files,
    and CI/CD paths — but NOT to application source code.

    This test documents TODAY's behavior (before S4 resolution). The hook blocks
    any path not on its explicit allowlist; src/ is not on that list.

    See S4 contradiction context in module docstring above.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "src/api/server.js")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 2, (
        f"Expected BLOCKED (returncode 2) for Ellis writing to src/api/server.js. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-ellis-paths.sh must deny writes to application source files."
    )
    assert "BLOCKED" in r.stdout, (
        f"Expected 'BLOCKED' in output. Got: {r.stdout!r}"
    )


def test_T_0034_037b_ellis_blocked_from_docs(tmp_path):
    """enforce-ellis-paths.sh must block a Write to docs/architecture/ADR-9999.md.

    docs/ is not on Ellis's allowlist (Agatha owns docs/). This test confirms
    Ellis cannot write documentation files.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "docs/architecture/ADR-9999.md")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 2, (
        f"Expected BLOCKED (returncode 2) for Ellis writing to docs/architecture/. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-ellis-paths.sh must deny writes to docs/."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-038: enforce-ellis-paths.sh allows CHANGELOG.md (today's allowed path)
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_038_ellis_allowed_to_write_changelog(tmp_path):
    """enforce-ellis-paths.sh must allow a Write to CHANGELOG.md.

    CHANGELOG.md is Ellis's primary artifact. The hook must exit 0 for
    exactly this path.

    This test documents today's behavior per the current hook implementation.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "CHANGELOG.md")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 0, (
        f"Expected ALLOWED (returncode 0) for Ellis writing to CHANGELOG.md. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-ellis-paths.sh must permit writes to CHANGELOG.md."
    )
    assert "BLOCKED" not in r.stdout, (
        f"Unexpected 'BLOCKED' in output for CHANGELOG.md. Output: {r.stdout!r}"
    )


def test_T_0034_038b_ellis_allowed_to_write_gitignore(tmp_path):
    """enforce-ellis-paths.sh must allow a Write to .gitignore.

    Git config files are on Ellis's allowlist today. This test locks that behavior.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", ".gitignore")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 0, (
        f"Expected ALLOWED (returncode 0) for Ellis writing to .gitignore. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-ellis-paths.sh must permit writes to .gitignore."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-039: hook allowlist matches today's expected behavior
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_039_ellis_hook_allowlist_matches_today_behavior():
    """enforce-ellis-paths.sh allowlist must contain all the paths Ellis is
    currently permitted to write to, per today's hook implementation.

    This is the parity check for today's Ellis behavior (pre-S4 resolution).
    The test verifies the hook contains case arms for:
      - CHANGELOG.md
      - .gitignore, .gitattributes, .gitmodules (git config files)
      - .github/* (CI/CD -- part of the S4 contradiction; allowed today)

    When the S4 contradiction is resolved in Wave 4, supersede this test with
    a new one that locks the resolved behavior. Do NOT modify these assertions.

    NOTE: enforcement-config.json does not carry an `ellis_allowed_paths` key.
    Ellis's allowlist is hardcoded in the hook. This test verifies the source directly.
    """
    assert HOOK_PATH.exists(), (
        f"enforce-ellis-paths.sh missing at {HOOK_PATH}. "
        f"Wave 2 Step 2.2 should not be authoring a new hook — the hook already exists."
    )
    hook_text = HOOK_PATH.read_text()

    # Core allowlist items that must be present in today's hook
    required_case_arms = [
        "CHANGELOG.md",
        ".gitignore",
        ".gitattributes",
        ".gitmodules",
    ]
    for arm in required_case_arms:
        assert arm in hook_text, (
            f"enforce-ellis-paths.sh is missing case arm for '{arm}'. "
            f"Today's hook must allow Ellis to write to this path. "
            f"If this path was intentionally removed, update this test with ADR reference."
        )

    # Verify the hook still blocks application source files (regression guard)
    # The BLOCKED message must reference Ellis's role
    assert "BLOCKED" in hook_text and "Ellis" in hook_text, (
        f"enforce-ellis-paths.sh must contain a BLOCKED message referencing Ellis. "
        f"The block message is how engineers understand why a write was denied."
    )
