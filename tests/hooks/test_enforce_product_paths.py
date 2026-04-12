"""Tests for ADR-0034 Wave 2 Step 2.2: enforce-product-paths.sh.

Covers T-0034-031, T-0034-032, T-0034-033.

Follows the template established by test_enforce_colby_paths.py.

The product hook (enforce-product-paths.sh) covers the robert-spec producer
agent. Robert-spec is allowed to write only to docs/product/. Writes to any
other path must be blocked.

The hook already exists in source/claude/hooks/. These tests lock its behavior
so future refactors cannot accidentally open broader write access.

NOTE: enforcement-config.json does not carry a `product_allowed_paths` key.
The hook contains a hardcoded case statement: `docs/product/*) exit 0`.
T-0034-033 therefore verifies the hook source file directly.

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

HOOK = "enforce-product-paths.sh"
HOOK_PATH = PROJECT_ROOT / "source" / "claude" / "hooks" / HOOK
ENFORCEMENT_CONFIG = PROJECT_ROOT / "source" / "claude" / "hooks" / "enforcement-config.json"

# The prefix that robert-spec is allowed to write to.
PRODUCT_ALLOWED_PREFIX = "docs/product/"


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-031: enforce-product-paths.sh blocks a write outside docs/product/
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_031_product_blocked_from_source(tmp_path):
    """enforce-product-paths.sh must block a Write to source/shared/agents/roz.md.

    Robert-spec is the product spec producer. She must not write to source/,
    docs/architecture/, docs/ux/, or any path outside docs/product/.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "source/shared/agents/roz.md")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 2, (
        f"Expected BLOCKED (returncode 2) for robert-spec writing to source/shared/agents/roz.md. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-product-paths.sh must deny writes outside docs/product/."
    )
    assert "BLOCKED" in r.stdout, (
        f"Expected 'BLOCKED' in output. Got: {r.stdout!r}"
    )


def test_T_0034_031b_product_blocked_from_docs_architecture(tmp_path):
    """enforce-product-paths.sh must block a Write to docs/architecture/.

    docs/architecture/ belongs to Cal (ADR production). Robert-spec must not
    write there even though it is under docs/.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "docs/architecture/ADR-9999-test.md")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 2, (
        f"Expected BLOCKED (returncode 2) for robert-spec writing to docs/architecture/. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-product-paths.sh must deny writes to docs/architecture/."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-032: enforce-product-paths.sh allows a write inside docs/product/
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_032_product_allowed_in_docs_product(tmp_path):
    """enforce-product-paths.sh must allow a Write to docs/product/feature-spec.md.

    Writing product specs to docs/product/ is robert-spec's core job.
    The hook must exit 0 for any path under docs/product/.
    """
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config = json.loads(ENFORCEMENT_CONFIG.read_text()) if ENFORCEMENT_CONFIG.exists() else {}
    (tmp_path / "enforcement-config.json").write_text(json.dumps(config))

    inp = build_per_agent_input("Write", "docs/product/feature-spec.md")
    r = run_per_agent_hook(HOOK, inp, tmp_path)

    assert r.returncode == 0, (
        f"Expected ALLOWED (returncode 0) for robert-spec writing to docs/product/feature-spec.md. "
        f"Got returncode {r.returncode}. Output: {r.stdout!r}. "
        f"enforce-product-paths.sh must permit writes to docs/product/."
    )
    assert "BLOCKED" not in r.stdout, (
        f"Unexpected 'BLOCKED' in output for an allowed path. Output: {r.stdout!r}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-033: hook allowlist matches the expected docs/product/ prefix
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_033_product_hook_allows_docs_product_prefix():
    """enforce-product-paths.sh must contain a case arm that allows docs/product/* only.

    This is the parity check for the product enforcement hook. The hook's
    hardcoded allowlist prefix (`docs/product/`) must match PRODUCT_ALLOWED_PREFIX.

    NOTE: enforcement-config.json does not carry a `product_allowed_paths` key.
    The allowlist is hardcoded in the hook. This test verifies the hook source directly.
    """
    assert HOOK_PATH.exists(), (
        f"enforce-product-paths.sh missing at {HOOK_PATH}. "
        f"Wave 2 Step 2.2 should not be authoring a new hook — the hook already exists."
    )
    hook_text = HOOK_PATH.read_text()

    # The hook should contain: docs/product/*) exit 0
    assert "docs/product/*" in hook_text, (
        f"enforce-product-paths.sh does not contain 'docs/product/*' in its case statement. "
        f"Expected case arm: docs/product/*) exit 0 ;;"
    )

    # Verify the hook does NOT accidentally allow docs/architecture/ or docs/ux/
    assert "docs/architecture/*) exit 0" not in hook_text, (
        f"enforce-product-paths.sh accidentally allows docs/architecture/. "
        f"Robert-spec must write only to docs/product/."
    )
    assert "docs/ux/*) exit 0" not in hook_text, (
        f"enforce-product-paths.sh accidentally allows docs/ux/. "
        f"Robert-spec must write only to docs/product/."
    )
