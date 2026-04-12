"""Wave 3 Step 3.1 triage tests — ADR-0034.

Covers T-0034-046, T-0034-047, T-0034-048.

These tests define correct behavior BEFORE Colby builds. They are expected to
be RED (failing) until Colby completes Step 3.1 of Wave 3.

T-0034-046: Full test suite exits 0 with zero failures.
T-0034-047: T-0024-048 does not exist (deleted from test_wave3_hook_removal.py).
T-0034-048: T-0024-050 asserts == 3 (not 2) and docstring references ADR-0034.

ADR ref: docs/architecture/ADR-0034-gauntlet-remediation.md Wave 3 Step 3.1
Authored by Roz before Colby builds (ADR-0034 constraint: Roz-first TDD).
Colby MUST NOT modify these assertions.
"""

import subprocess
import ast
import re
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT

# ── Paths ──────────────────────────────────────────────────────────────────

WAVE3_HOOK_REMOVAL_FILE = (
    PROJECT_ROOT / "tests" / "hooks" / "test_wave3_hook_removal.py"
)


# ═══════════════════════════════════════════════════════════════════════
# T-0034-046: Full test suite exits 0 with zero failures
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_046_full_pytest_suite_passes():
    """pytest tests/ && node --test tests/brain/*.test.mjs both exit 0.

    After Colby completes Wave 3 Step 3.1 (red test triage), the full test
    suite must be green with zero failures.

    ADR-0034 Wave 3 Step 3.1 acceptance criterion:
      `pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs`
      exits 0 with zero failures.

    Note: this test intentionally excludes itself from the inner pytest run
    to avoid recursion. A pass here proves no OTHER test in tests/ is failing.
    """
    # Run pytest (excluding this file to prevent infinite recursion)
    pytest_result = subprocess.run(
        [
            "pytest",
            "tests/",
            "-q",
            "--tb=short",
            f"--ignore={str(WAVE3_HOOK_REMOVAL_FILE.relative_to(PROJECT_ROOT))}",
            "--ignore=tests/hooks/test_wave3_adr0034_triage.py",
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=180,
    )
    assert pytest_result.returncode == 0, (
        f"pytest tests/ failed (exit code {pytest_result.returncode}). "
        f"ADR-0034 Wave 3 Step 3.1 requires all tests to pass after red test triage.\n"
        f"stdout:\n"
        f"{pytest_result.stdout[-4000:] if len(pytest_result.stdout) > 4000 else pytest_result.stdout}\n"
        f"stderr:\n"
        f"{pytest_result.stderr[-1000:] if len(pytest_result.stderr) > 1000 else pytest_result.stderr}"
    )

    # Run node test runner for brain tests
    node_result = subprocess.run(
        ["node", "--test", "tests/brain/*.test.mjs"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT / "brain"),
        timeout=120,
        shell=False,
    )
    # node --test with glob may require shell=True for glob expansion
    if node_result.returncode != 0 and "No test files found" not in node_result.stderr:
        # Try with shell=True for glob expansion
        node_result_shell = subprocess.run(
            "node --test ../tests/brain/*.test.mjs",
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT / "brain"),
            timeout=120,
            shell=True,
        )
        assert node_result_shell.returncode == 0, (
            f"node --test brain/*.test.mjs failed (exit code {node_result_shell.returncode}). "
            f"ADR-0034 Wave 3 Step 3.1 requires all brain tests to pass.\n"
            f"stdout:\n"
            f"{node_result_shell.stdout[-4000:] if len(node_result_shell.stdout) > 4000 else node_result_shell.stdout}\n"
            f"stderr:\n"
            f"{node_result_shell.stderr[-2000:] if len(node_result_shell.stderr) > 2000 else node_result_shell.stderr}"
        )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-047: T-0024-048 does not exist (deleted)
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_047_T0024_048_deleted():
    """T-0024-048 (self-referential pytest gate) must be deleted from the test suite.

    ADR-0034 Wave 3 Step 3.1 mandates DELETE T-0024-048. The test is a
    self-referential gate that always passes trivially (the assertion is
    "pytest is running, therefore pytest passes") and produces false confidence.

    This test checks that neither the function `test_T_0024_048_full_pytest_suite_passes`
    nor the string literal "T-0024-048" appear as a live test definition in
    test_wave3_hook_removal.py after Colby's triage step.

    Replacement path: document as a CI job entry (not a pytest test). See
    ADR-0034 Wave 3 Step 3.1 notes.
    """
    assert WAVE3_HOOK_REMOVAL_FILE.exists(), (
        f"test_wave3_hook_removal.py not found at {WAVE3_HOOK_REMOVAL_FILE}. "
        "Cannot verify T-0024-048 deletion."
    )

    source = WAVE3_HOOK_REMOVAL_FILE.read_text()

    # The function definition must not exist
    assert "def test_T_0024_048" not in source, (
        "T-0024-048 self-referential gate still exists in test_wave3_hook_removal.py. "
        "ADR-0034 Wave 3 Step 3.1 mandates its deletion. "
        "Replace with a CI job entry or a note in Notes for Colby for a future CI ADR."
    )

    # No live test function should reference T-0024-048 in its name
    assert "test_T_0024_048" not in source, (
        "Found test_T_0024_048 reference in test_wave3_hook_removal.py. "
        "The self-referential gate must be removed entirely — comments referencing "
        "the deleted test ID are acceptable, but function definitions are not."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-048: T-0024-050 asserts == 3 and docstring references ADR-0034
# ═══════════════════════════════════════════════════════════════════════


def test_T_0034_048_T0024_050_updated_to_3_with_adr0034_ref():
    """T-0024-050 must assert == 3 SubagentStop hooks and reference ADR-0034.

    After Wave 1 of ADR-0034, settings.json registers 3 SubagentStop hooks:
      1. log-agent-stop.sh
      2. brain-extractor agent hook (9 agents: the original 4 + 5 newly added)
      3. ellis-specific SubagentStop hook (or aggregate)

    T-0024-050 was authored against ADR-0025 and expected == 2 hooks. Wave 1
    changed the SubagentStop registration count to 3. Colby must update the
    assertion to == 3 AND add a docstring mention of ADR-0034.

    ADR-0034 Wave 3 Step 3.1 acceptance criterion:
      T-0024-050 asserts `== 3` and docstring references ADR-0034.
    """
    assert WAVE3_HOOK_REMOVAL_FILE.exists(), (
        f"test_wave3_hook_removal.py not found at {WAVE3_HOOK_REMOVAL_FILE}. "
        "Cannot verify T-0024-050 update."
    )

    source = WAVE3_HOOK_REMOVAL_FILE.read_text()

    # The function must still exist (not deleted)
    assert "def test_T_0024_050_subagent_stop_has_exactly_3_hooks" in source or (
        "def test_T_0024_050" in source
    ), (
        "T-0024-050 function not found in test_wave3_hook_removal.py. "
        "This test must be updated (not deleted) — it is a regression guard for "
        "the SubagentStop hook count after Wave 1."
    )

    # The assertion value must be 3, not 2
    # Find the test function body and check for == 3 assertion
    assert "== 3" in source, (
        "T-0024-050 does not assert == 3 SubagentStop hooks. "
        "After ADR-0034 Wave 1, settings.json has 3 SubagentStop hooks. "
        "The assertion must be updated from == 2 to == 3."
    )

    # The docstring or comment must reference ADR-0034
    assert "ADR-0034" in source, (
        "T-0024-050 (or its docstring) does not reference ADR-0034. "
        "The update rationale must link to ADR-0034 so future readers understand "
        "why the count changed from 2 to 3."
    )

    # Belt-and-suspenders: confirm the old '== 2' assertion for hook count
    # is no longer present in the context of the T-0024-050 function body.
    # We parse the AST to find the function and inspect its assertions.
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"test_wave3_hook_removal.py has a syntax error: {e}")

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and "0024_050" in node.name:
            func_src_lines = source.splitlines()
            # Extract the function source
            func_lines = func_src_lines[node.lineno - 1:node.end_lineno]
            func_text = "\n".join(func_lines)
            # The == 2 pattern for hook_count must not appear as the expectation
            # (allowing "expected exactly 2" in OLD docstring to be replaced)
            assert "hook_count == 2" not in func_text, (
                f"T-0024-050 still asserts hook_count == 2 in function body. "
                f"Must be updated to == 3. "
                f"Function source (first 500 chars):\n{func_text[:500]}"
            )
            break
