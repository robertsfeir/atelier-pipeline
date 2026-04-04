"""Mechanical enforcement: zero .bats files in the project.

All tests must be pytest. Bats files are invisible to the standard test
command and create false coverage. This test fails if any .bats file or
bats helper (test_helper.bash) exists anywhere in the repo.
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_no_bats_files_in_repo():
    """No .bats files anywhere in the project."""
    bats_files = sorted(PROJECT_ROOT.rglob("*.bats"))
    assert bats_files == [], (
        f"Found {len(bats_files)} .bats file(s) — all tests must be pytest:\n"
        + "\n".join(f"  {f.relative_to(PROJECT_ROOT)}" for f in bats_files)
    )


def test_no_bats_helper_in_repo():
    """No test_helper.bash (bats shared helper) in the project."""
    helpers = sorted(PROJECT_ROOT.rglob("test_helper.bash"))
    assert helpers == [], (
        f"Found bats helper(s) — remove and use conftest.py instead:\n"
        + "\n".join(f"  {f.relative_to(PROJECT_ROOT)}" for f in helpers)
    )
