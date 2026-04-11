"""Tests for ADR-0033 Step 4: enforce-colby-paths.sh with `.github/` blocked.

Covers T-0033-014, T-0033-015, T-0033-030.

Step 4 adds `.github/` to `colby_blocked_paths` in BOTH
`source/claude/hooks/enforcement-config.json` AND
`tests/hooks/conftest.py` DEFAULT_CONFIG. These tests assert the FIXED state
of both files (the parity of the two is the purpose of T-0033-030).

Unlike tests/hooks/test_enforce_paths.py which uses a per-test CICD_CONFIG
mock, these tests use the SHIPPED DEFAULT_CONFIG — they fail if `.github/`
is missing from the actual mirror in conftest.py.

Colby MUST NOT modify these assertions.
"""

import json
from pathlib import Path

from conftest import (
    DEFAULT_CONFIG,
    PROJECT_ROOT,
    build_per_agent_input,
    run_per_agent_hook,
)

HOOK = "enforce-colby-paths.sh"
ENFORCEMENT_CONFIG = (
    PROJECT_ROOT / "source" / "claude" / "hooks" / "enforcement-config.json"
)


# ═══════════════════════════════════════════════════════════════════════
# T-0033-014: Colby blocked from .github/workflows/ci.yml using DEFAULT_CONFIG
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_014_colby_blocked_from_github_workflows(tmp_path):
    """enforce-colby-paths.sh must block a Write to .github/workflows/ci.yml
    when the shipped DEFAULT_CONFIG (mirror of enforcement-config.json) is
    used as the enforcement config.

    This is distinct from test_enforce_paths.py::test_colby_blocks_github_workflows_ci
    which uses a custom CICD_CONFIG. This test uses the actual DEFAULT_CONFIG
    from conftest.py, so it fails if `.github/` has not been added to the
    shipped mirror (M1 fix).
    """
    # Set up env with DEFAULT_CONFIG in enforcement-config.json
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    (tmp_path / "enforcement-config.json").write_text(
        json.dumps(DEFAULT_CONFIG, indent=2)
    )
    inp = build_per_agent_input("Write", ".github/workflows/ci.yml")
    r = run_per_agent_hook(HOOK, inp, tmp_path)
    assert r.returncode == 2, (
        f"Expected BLOCKED (returncode 2). Got {r.returncode}. "
        f"Output: {r.stdout!r}. "
        f"Check: is `.github/` present in conftest.py DEFAULT_CONFIG colby_blocked_paths?"
    )
    assert "BLOCKED" in r.stdout, (
        f"Expected 'BLOCKED' in output. Got: {r.stdout!r}"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0033-015: enforcement-config.json parses and contains `.github/`
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_015_enforcement_config_has_github_blocker():
    """source/claude/hooks/enforcement-config.json must:
      (a) parse as valid JSON, and
      (b) contain `.github/` inside colby_blocked_paths.

    Failing (a) breaks every Colby hook invocation because the script reads
    the file via jq. Failing (b) means Colby can write .github/workflows/
    on fresh installs — M1 regression.
    """
    assert ENFORCEMENT_CONFIG.exists(), (
        f"enforcement-config.json missing at {ENFORCEMENT_CONFIG}"
    )
    try:
        cfg = json.loads(ENFORCEMENT_CONFIG.read_text())
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"enforcement-config.json is invalid JSON: {e}"
        ) from e
    blocked = cfg.get("colby_blocked_paths", [])
    assert isinstance(blocked, list), (
        f"colby_blocked_paths should be a list, got {type(blocked).__name__}"
    )
    assert ".github/" in blocked, (
        f"`.github/` missing from colby_blocked_paths. Current list: {blocked}. "
        f"ADR-0033 Step 4 (M1) requires `.github/` to be present so fresh "
        f"installs block Colby from writing CI workflow files."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0033-030: conftest.py DEFAULT_CONFIG mirrors enforcement-config.json
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_030_conftest_default_config_mirrors_enforcement_config():
    """conftest.py DEFAULT_CONFIG colby_blocked_paths must exactly match
    the list in source/claude/hooks/enforcement-config.json.

    The two lists are a manual mirror — see ADR-0033 `Notes for Colby`
    item 6. This test locks the mirror so future edits to either file
    force an update of the other.

    Note: this test uses DEFAULT_CONFIG, NOT SIMPLIFIED_CONFIG. SIMPLIFIED_CONFIG
    already contained .github/ before this ADR (it was designed as a "simplified"
    minimum baseline). The drift is specifically in DEFAULT_CONFIG.
    """
    shipped = json.loads(ENFORCEMENT_CONFIG.read_text())
    shipped_blocked = shipped.get("colby_blocked_paths", [])
    mirror_blocked = DEFAULT_CONFIG.get("colby_blocked_paths", [])
    # order-insensitive: enforcement behavior doesn't depend on list order
    assert sorted(shipped_blocked) == sorted(mirror_blocked), (
        f"DRIFT between enforcement-config.json and conftest.py DEFAULT_CONFIG:\n"
        f"  shipped (enforcement-config.json): {shipped_blocked}\n"
        f"  mirror (conftest.py DEFAULT_CONFIG): {mirror_blocked}\n"
        f"Update BOTH files to match (ADR-0033 Step 4, Notes for Colby #6)."
    )
