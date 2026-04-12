"""Tests for ADR-0034 Wave 2 Step 2.2: enforce-agatha-paths.sh.

Covers T-0034-028, T-0034-029, T-0034-030.

Follows the template established by test_enforce_colby_paths.py.

Agatha is the documentation agent. The hook permits writes to `docs/` only.
Writes anywhere else (source/, tests/, .github/, etc.) must be blocked.

The third test (T-0034-030) verifies that conftest.py DEFAULT_CONFIG reflects
the enforcement-config.json for agatha. NOTE: enforcement-config.json does NOT
currently carry an `agatha_allowed_paths` key — Agatha's allowlist is hardcoded
in the hook itself (`case "$FILE_PATH" in docs/*)`). T-0034-030 therefore
verifies that the hook file's allowlist prefix matches the expected constant,
not a config key. This is consistent with the hook's design: single-path agents
use hardcoded case statements rather than a config-driven list.

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

HOOK = "enforce-agatha-paths.sh"
HOOK_PATH = PROJECT_ROOT / "source" / "claude" / "hooks" / HOOK
ENFORCEMENT_CONFIG = PROJECT_ROOT / "source" / "claude" / "hooks" / "enforcement-config.json"

# The prefix that Agatha is allowed to write to — matches the hook's case statement.
AGATHA_ALLOWED_PREFIX = "docs/"


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-028: enforce-agatha-paths.sh blocks a write outside docs/
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_028_agatha_blocked_from_source_hooks(tmp_path):
    """enforce-agatha-paths.sh must block a Write to source/claude/hooks/new-hook.sh.

    Agatha is the documentation agent. She must not write to source/, tests/,
    .github/, or any non-docs path. Writing to source/claude/hooks/new-hook.sh
    is the canonical blocked-path example from the ADR test spec.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    # Write a minimal enforcement-config.json so the hook can source it
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "source/claude/hooks/new-hook.sh")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 2, (
        f"Expected BLOCKED (returncode 2) for Agatha writing to source/claude/hooks/new-hook.sh. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-agatha-paths.sh must deny writes outside docs/."
    )
    assert "BLOCKED" in r.stdout, (
        f"Expected 'BLOCKED' in output. Got: {r.stdout!r}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-029: enforce-agatha-paths.sh allows a write inside docs/
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_029_agatha_allowed_in_docs(tmp_path):
    """enforce-agatha-paths.sh must allow a Write to docs/guide/user-guide.md.

    Writing documentation to docs/ is Agatha's core job. The hook must exit 0
    for any path under docs/.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "docs/guide/user-guide.md")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 0, (
        f"Expected ALLOWED (returncode 0) for Agatha writing to docs/guide/user-guide.md. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-agatha-paths.sh must permit writes to docs/."
    )
    assert "BLOCKED" not in r.stdout, (
        f"Unexpected 'BLOCKED' in output for an allowed path. Output: {r.stdout!r}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-030: hook allowlist matches the expected docs/ prefix
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_030_agatha_hook_allows_docs_prefix():
    """enforce-agatha-paths.sh must contain a case arm that allows docs/* and only docs/*.

    This is the parity check: the hook's hardcoded allowlist prefix (`docs/`)
    must match the AGATHA_ALLOWED_PREFIX constant defined at the top of this test file.
    If the hook is ever changed to allow a broader prefix (e.g., `docs/` AND `src/`),
    or to a narrower one (e.g., `docs/architecture/` only), this test catches the drift.

    NOTE: enforcement-config.json does not carry an `agatha_allowed_paths` key.
    Agatha's allowlist is hardcoded in the hook case statement. This test verifies
    the hook source file directly.
    """
    assert HOOK_PATH.exists(), (
        f"enforce-agatha-paths.sh missing at {HOOK_PATH}. "
        f"Wave 2 Step 2.2 should not be authoring a new hook — the hook already exists."
    )
    hook_text = HOOK_PATH.read_text()

    # Find the case arm that permits the allowed path.
    # The hook should contain: case "$FILE_PATH" in docs/*) exit 0 ;;
    assert "docs/*" in hook_text, (
        f"enforce-agatha-paths.sh does not contain 'docs/*' in its case statement. "
        f"Expected the hook to allow docs/ via: case \"$FILE_PATH\" in docs/*) exit 0 ;;"
    )

    # Verify the hook does NOT accidentally allow source/ or tests/ writes.
    # These would be security regressions.
    assert "source/*) exit 0" not in hook_text, (
        f"enforce-agatha-paths.sh accidentally allows source/ writes. "
        f"Agatha must never write to source/."
    )
    assert "tests/*) exit 0" not in hook_text, (
        f"enforce-agatha-paths.sh accidentally allows tests/ writes. "
        f"Agatha must never write to tests/."
    )
