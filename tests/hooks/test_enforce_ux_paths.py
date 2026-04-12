"""Tests for ADR-0034 Wave 2 Step 2.2: enforce-ux-paths.sh.

Covers T-0034-034, T-0034-035, T-0034-036.

Follows the template established by test_enforce_colby_paths.py.

The UX hook (enforce-ux-paths.sh) covers the sable-ux producer agent.
Sable-ux is allowed to write only to docs/ux/. Writes to any other path
must be blocked.

The hook already exists in source/claude/hooks/. These tests lock its behavior
so future refactors cannot accidentally open broader write access.

NOTE: enforcement-config.json does not carry a `ux_allowed_paths` key.
The hook contains a hardcoded case statement: `docs/ux/*) exit 0`.
T-0034-036 therefore verifies the hook source file directly.

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

HOOK = "enforce-ux-paths.sh"
HOOK_PATH = PROJECT_ROOT / "source" / "claude" / "hooks" / HOOK
ENFORCEMENT_CONFIG = PROJECT_ROOT / "source" / "claude" / "hooks" / "enforcement-config.json"

# The prefix that sable-ux is allowed to write to.
UX_ALLOWED_PREFIX = "docs/ux/"


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-034: enforce-ux-paths.sh blocks a write outside docs/ux/
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_034_ux_blocked_from_source(tmp_path):
    """enforce-ux-paths.sh must block a Write to source/shared/agents/cal.md.

    Sable-ux is the UX design producer. She must not write to source/,
    docs/product/, docs/architecture/, or any path outside docs/ux/.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "source/shared/agents/cal.md")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 2, (
        f"Expected BLOCKED (returncode 2) for sable-ux writing to source/shared/agents/cal.md. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-ux-paths.sh must deny writes outside docs/ux/."
    )
    assert "BLOCKED" in r.stdout, (
        f"Expected 'BLOCKED' in output. Got: {r.stdout!r}"
    )


def test_T_0034_034b_ux_blocked_from_docs_product(tmp_path):
    """enforce-ux-paths.sh must block a Write to docs/product/.

    docs/product/ belongs to robert-spec. Sable-ux must not write there
    even though it is under docs/.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "docs/product/my-feature.md")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 2, (
        f"Expected BLOCKED (returncode 2) for sable-ux writing to docs/product/. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-ux-paths.sh must deny writes to docs/product/."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-035: enforce-ux-paths.sh allows a write inside docs/ux/
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_035_ux_allowed_in_docs_ux(tmp_path):
    """enforce-ux-paths.sh must allow a Write to docs/ux/wireframes.md.

    Writing UX design docs to docs/ux/ is sable-ux's core job.
    The hook must exit 0 for any path under docs/ux/.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "docs/ux/wireframes.md")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 0, (
        f"Expected ALLOWED (returncode 0) for sable-ux writing to docs/ux/wireframes.md. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-ux-paths.sh must permit writes to docs/ux/."
    )
    assert "BLOCKED" not in r.stdout, (
        f"Unexpected 'BLOCKED' in output for an allowed path. Output: {r.stdout!r}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-036: hook allowlist matches the expected docs/ux/ prefix
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_036_ux_hook_allows_docs_ux_prefix():
    """enforce-ux-paths.sh must contain a case arm that allows docs/ux/* only.

    This is the parity check for the UX enforcement hook. The hook's
    hardcoded allowlist prefix (`docs/ux/`) must match UX_ALLOWED_PREFIX.

    NOTE: enforcement-config.json does not carry a `ux_allowed_paths` key.
    The allowlist is hardcoded in the hook. This test verifies the hook source directly.
    """
    assert HOOK_PATH.exists(), (
        f"enforce-ux-paths.sh missing at {HOOK_PATH}. "
        f"Wave 2 Step 2.2 should not be authoring a new hook — the hook already exists."
    )
    hook_text = HOOK_PATH.read_text()

    # The hook should contain: docs/ux/*) exit 0
    assert "docs/ux/*" in hook_text, (
        f"enforce-ux-paths.sh does not contain 'docs/ux/*' in its case statement. "
        f"Expected case arm: docs/ux/*) exit 0 ;;"
    )

    # Verify the hook does NOT accidentally allow docs/product/ or docs/architecture/
    assert "docs/product/*) exit 0" not in hook_text, (
        f"enforce-ux-paths.sh accidentally allows docs/product/. "
        f"Sable-ux must write only to docs/ux/."
    )
    assert "docs/architecture/*) exit 0" not in hook_text, (
        f"enforce-ux-paths.sh accidentally allows docs/architecture/. "
        f"Sable-ux must write only to docs/ux/."
    )
