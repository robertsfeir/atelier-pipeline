"""Tests for Colby/Ellis CI/CD path enforcement split.

Colby must be blocked from CI/CD paths (.github/workflows/ci.yml).
Ellis must be allowed to write CI/CD paths (.github/workflows/ci.yml).
Ellis must be blocked from source code paths (source/main.py).

Uses per-agent hook runners with enforcement-config.json that includes .github/ in colby_blocked_paths.

Covers:
  (d) enforce-colby-paths.sh BLOCKS .github/workflows/ci.yml
  (e) enforce-ellis-paths.sh ALLOWS .github/workflows/ci.yml
  (f) enforce-ellis-paths.sh BLOCKS source/main.py
"""

import json

import pytest

from conftest import (
    PROJECT_ROOT,
    SIMPLIFIED_CONFIG,
    build_per_agent_input,
    run_per_agent_hook,
)

COLBY_HOOK = "enforce-colby-paths.sh"
ELLIS_HOOK = "enforce-ellis-paths.sh"

# Enforcement config that has .github/ in colby_blocked_paths (matching installed config)
CICD_CONFIG = {
    **SIMPLIFIED_CONFIG,
    "colby_blocked_paths": [
        "docs/",
        ".github/",
        ".gitlab-ci",
        ".circleci/",
        "Jenkinsfile",
        "Dockerfile",
        "docker-compose",
        ".gitlab/",
        "deploy/",
        "infra/",
        "terraform/",
        "pulumi/",
        "k8s/",
        "kubernetes/",
    ],
}


@pytest.fixture
def cicd_env(tmp_path):
    """Test environment with CI/CD paths in colby_blocked_paths."""
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    (tmp_path / "enforcement-config.json").write_text(json.dumps(CICD_CONFIG, indent=2))
    return tmp_path


# ── (d) Colby is BLOCKED from .github/workflows/ci.yml ───────────────────


def test_colby_blocks_github_workflows_ci(cicd_env):
    """Colby must be blocked from writing to .github/workflows/ci.yml (CI/CD path)."""
    inp = build_per_agent_input("Write", ".github/workflows/ci.yml")
    r = run_per_agent_hook(COLBY_HOOK, inp, cicd_env)
    assert r.returncode == 2, (
        f"Expected returncode 2 (BLOCKED), got {r.returncode}. Output: {r.stdout!r}"
    )
    assert "BLOCKED" in r.stdout, (
        f"Expected 'BLOCKED' in output. Got: {r.stdout!r}"
    )


def test_colby_blocks_github_any_path(cicd_env):
    """Colby is blocked from any .github/ path, not just ci.yml."""
    inp = build_per_agent_input("Edit", ".github/CODEOWNERS")
    r = run_per_agent_hook(COLBY_HOOK, inp, cicd_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_colby_blocks_docs_path(cicd_env):
    """Colby is blocked from docs/ (existing baseline behavior preserved)."""
    inp = build_per_agent_input("Write", "docs/architecture/ADR-0042.md")
    r = run_per_agent_hook(COLBY_HOOK, inp, cicd_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_colby_allows_source_code(cicd_env):
    """Colby can write source code files outside blocked paths."""
    inp = build_per_agent_input("Write", "src/main.py")
    r = run_per_agent_hook(COLBY_HOOK, inp, cicd_env)
    assert r.returncode == 0, (
        f"Expected returncode 0 (allowed), got {r.returncode}. Output: {r.stdout!r}"
    )


# ── (e) Ellis is ALLOWED to write .github/workflows/ci.yml ───────────────


def test_ellis_allows_github_workflows_ci(cicd_env):
    """Ellis must be allowed to write to .github/workflows/ci.yml (CI/CD path)."""
    inp = build_per_agent_input("Write", ".github/workflows/ci.yml")
    r = run_per_agent_hook(ELLIS_HOOK, inp, cicd_env)
    assert r.returncode == 0, (
        f"Expected returncode 0 (allowed), got {r.returncode}. Output: {r.stdout!r}"
    )


def test_ellis_allows_github_any_subpath(cicd_env):
    """Ellis can write any file under .github/."""
    inp = build_per_agent_input("Edit", ".github/CODEOWNERS")
    r = run_per_agent_hook(ELLIS_HOOK, inp, cicd_env)
    assert r.returncode == 0


def test_ellis_allows_changelog(cicd_env):
    """Ellis can write CHANGELOG.md (core commit target)."""
    inp = build_per_agent_input("Write", "CHANGELOG.md")
    r = run_per_agent_hook(ELLIS_HOOK, inp, cicd_env)
    assert r.returncode == 0


def test_ellis_allows_gitlab_ci(cicd_env):
    """Ellis can write .gitlab-ci.yml (CI/CD path)."""
    inp = build_per_agent_input("Write", ".gitlab-ci.yml")
    r = run_per_agent_hook(ELLIS_HOOK, inp, cicd_env)
    assert r.returncode == 0


def test_ellis_allows_dockerfile(cicd_env):
    """Ellis can write Dockerfile (CI/CD path)."""
    inp = build_per_agent_input("Write", "Dockerfile")
    r = run_per_agent_hook(ELLIS_HOOK, inp, cicd_env)
    assert r.returncode == 0


# ── (f) Ellis is BLOCKED from source/main.py ─────────────────────────────


def test_ellis_blocks_source_main_py(cicd_env):
    """Ellis must be blocked from writing source/main.py (not a commit target)."""
    inp = build_per_agent_input("Write", "source/main.py")
    r = run_per_agent_hook(ELLIS_HOOK, inp, cicd_env)
    assert r.returncode == 2, (
        f"Expected returncode 2 (BLOCKED), got {r.returncode}. Output: {r.stdout!r}"
    )
    assert "BLOCKED" in r.stdout, (
        f"Expected 'BLOCKED' in output. Got: {r.stdout!r}"
    )


def test_ellis_blocks_arbitrary_source_file(cicd_env):
    """Ellis is blocked from arbitrary source code files."""
    inp = build_per_agent_input("Edit", "src/app/routes.py")
    r = run_per_agent_hook(ELLIS_HOOK, inp, cicd_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_ellis_blocks_tests_dir(cicd_env):
    """Ellis is blocked from writing test files."""
    inp = build_per_agent_input("Write", "tests/test_feature.py")
    r = run_per_agent_hook(ELLIS_HOOK, inp, cicd_env)
    assert r.returncode == 2
    assert "BLOCKED" in r.stdout


def test_ellis_allows_gitignore(cicd_env):
    """Ellis can write .gitignore (git config file)."""
    inp = build_per_agent_input("Edit", ".gitignore")
    r = run_per_agent_hook(ELLIS_HOOK, inp, cicd_env)
    assert r.returncode == 0
