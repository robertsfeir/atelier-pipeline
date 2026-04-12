"""Tests for ADR-0035 Wave 4: Consumer path wiring, hydrate-telemetry state dir, S4 resolution.

Step 1 Tests (T-0035-001 through T-0035-008): Verify that hardcoded
``docs/pipeline/`` references in source/shared/ have been replaced with
``{pipeline_state_dir}`` placeholders for session-specific files.

Step 3 structural checks (T-0035-022 through T-0035-027): Verify
enforce-ellis-paths.sh header, test docstring, pipeline-orchestration.md
concurrent-session protocol.

Test IDs in scope:
  T-0035-001  No hardcoded docs/pipeline/pipeline-state.md in consumer dirs
  T-0035-002  No hardcoded docs/pipeline/context-brief.md in consumer dirs
  T-0035-003  No hardcoded docs/pipeline/last-qa-report.md in consumer dirs
  T-0035-004  No hardcoded docs/pipeline/investigation-ledger.md in consumer dirs
  T-0035-005  error-patterns.md references preserved (exactly 2 in pipeline.md)
  T-0035-006  post-compact-reinject.sh has no hardcoded '## From: docs/pipeline/' comments
  T-0035-007  session-boot.sh JSON output template contains "state_dir" field
  T-0035-008  Directly affected hook tests pass (enforce-eva-paths, enforce-ellis-paths)
  T-0035-022  enforce-ellis-paths.sh header contains ADR-0035 supersession comment
  T-0035-023  test_enforce_ellis_paths.py docstring references ADR-0035
  T-0035-024  pipeline-orchestration.md contains concurrent-session-hard-pause protocol
  T-0035-025  Concurrent-session protocol specifies exactly 3 user options
  T-0035-026  pipeline-orchestration.md state-files section uses {pipeline_state_dir}
  T-0035-027  Directly affected hook tests pass (regression gate after Step 3)
"""

import re
import subprocess
import sys
from pathlib import Path

from conftest import PROJECT_ROOT, SOURCE_DIR

# ── Directories to scan for hardcoded session-specific state paths ──────────

CONSUMER_DIRS = [
    SOURCE_DIR / "shared" / "agents",
    SOURCE_DIR / "shared" / "commands",
    SOURCE_DIR / "shared" / "rules",
    SOURCE_DIR / "shared" / "references",
    SOURCE_DIR / "shared" / "dashboard",
]

# Test files directly affected by ADR-0035 changes, used for targeted regression.
# Running the full 819-test suite in a subprocess would exceed timeout limits.
AFFECTED_TEST_FILES = [
    "tests/hooks/test_enforce_eva_paths.py",
    "tests/hooks/test_enforce_ellis_paths.py",
    "tests/hooks/test_session_boot.py",
    "tests/hooks/test_post_compact_reinject.py",
]

# ── Helpers ─────────────────────────────────────────────────────────────────


def _grep_in_dirs(pattern: str, dirs: list[Path]) -> list[str]:
    """Return matching lines across all files in the given directories.

    Uses simple Python text search -- no external grep dependency.
    Returns a list of 'filepath:lineno:line' strings.
    """
    matches = []
    for d in dirs:
        if not d.is_dir():
            continue
        for fpath in sorted(d.rglob("*")):
            if not fpath.is_file():
                continue
            try:
                text = fpath.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if re.search(pattern, line):
                    matches.append(f"{fpath}:{lineno}:{line.strip()}")
    return matches


def _run_affected_hook_tests() -> subprocess.CompletedProcess:
    """Run hook tests directly affected by ADR-0035 changes.

    Targets test files for enforce-eva-paths, enforce-ellis-paths,
    session-boot, and post-compact-reinject -- the hooks modified by
    this ADR. Does not re-run the full 819-test suite (which exceeds
    subprocess timeout limits).
    """
    existing_files = [
        f for f in AFFECTED_TEST_FILES
        if (PROJECT_ROOT / f).is_file()
    ]
    if not existing_files:
        # If none of the targeted files exist, fall back to a smoke test
        existing_files = ["tests/hooks/test_enforce_eva_paths.py"]

    return subprocess.run(
        [sys.executable, "-m", "pytest"] + existing_files + ["-v", "--tb=short", "-q"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )


# ── Step 1: Consumer placeholder conversion ─────────────────────────────────


def test_T_0035_001_no_hardcoded_pipeline_state_md():
    """No hardcoded docs/pipeline/pipeline-state.md in consumer dirs.

    Expected: FAIL before Colby implements (source files still have hardcoded paths).
    """
    matches = _grep_in_dirs(r"docs/pipeline/pipeline-state\.md", CONSUMER_DIRS)
    assert matches == [], (
        f"Found {len(matches)} hardcoded docs/pipeline/pipeline-state.md reference(s) "
        f"that should use {{pipeline_state_dir}}/pipeline-state.md:\n"
        + "\n".join(matches)
    )


def test_T_0035_002_no_hardcoded_context_brief_md():
    """No hardcoded docs/pipeline/context-brief.md in consumer dirs.

    Expected: FAIL before Colby implements (source files still have hardcoded paths).
    """
    matches = _grep_in_dirs(r"docs/pipeline/context-brief\.md", CONSUMER_DIRS)
    assert matches == [], (
        f"Found {len(matches)} hardcoded docs/pipeline/context-brief.md reference(s) "
        f"that should use {{pipeline_state_dir}}/context-brief.md:\n"
        + "\n".join(matches)
    )


def test_T_0035_003_no_hardcoded_last_qa_report_md():
    """No hardcoded docs/pipeline/last-qa-report.md in consumer dirs.

    Expected: FAIL before Colby implements (source files still have hardcoded paths).
    """
    matches = _grep_in_dirs(r"docs/pipeline/last-qa-report\.md", CONSUMER_DIRS)
    assert matches == [], (
        f"Found {len(matches)} hardcoded docs/pipeline/last-qa-report.md reference(s) "
        f"that should use {{pipeline_state_dir}}/last-qa-report.md:\n"
        + "\n".join(matches)
    )


def test_T_0035_004_no_hardcoded_investigation_ledger_md():
    """No hardcoded docs/pipeline/investigation-ledger.md in consumer dirs.

    Expected: FAIL before Colby implements (source files still have hardcoded paths).
    """
    matches = _grep_in_dirs(r"docs/pipeline/investigation-ledger\.md", CONSUMER_DIRS)
    assert matches == [], (
        f"Found {len(matches)} hardcoded docs/pipeline/investigation-ledger.md reference(s) "
        f"that should use {{pipeline_state_dir}}/investigation-ledger.md:\n"
        + "\n".join(matches)
    )


def test_T_0035_005_error_patterns_preserved():
    """error-patterns.md references stay as docs/pipeline/error-patterns.md -- exactly 2 in pipeline.md.

    Per ADR-0032 Decision, error-patterns.md is a shared in-repo file and must NOT
    use {pipeline_state_dir}. Lines 21 and 153 of pipeline.md should keep the
    hardcoded docs/pipeline/error-patterns.md path.

    Expected: PASS currently (these refs should not be changed).
    """
    pipeline_md = SOURCE_DIR / "shared" / "commands" / "pipeline.md"
    assert pipeline_md.is_file(), f"Expected {pipeline_md} to exist"

    text = pipeline_md.read_text(encoding="utf-8")
    pattern = re.compile(r"docs/pipeline/error-patterns\.md")
    match_lines = [
        (i + 1) for i, line in enumerate(text.splitlines()) if pattern.search(line)
    ]

    assert len(match_lines) == 2, (
        f"Expected exactly 2 'docs/pipeline/error-patterns.md' references in pipeline.md "
        f"(shared file, must not be replaced with placeholder), found {len(match_lines)} "
        f"on lines: {match_lines}"
    )


def test_T_0035_006_post_compact_no_hardcoded_from_comment():
    """post-compact-reinject.sh must not contain hardcoded '## From: docs/pipeline/' comments.

    After Colby's fix, the comments should use variable interpolation
    (e.g. $STATE_FILE, $BRIEF_FILE) instead of hardcoded paths.

    Expected: FAIL before Colby implements (lines 57, 64 still hardcoded).
    """
    hook_file = SOURCE_DIR / "claude" / "hooks" / "post-compact-reinject.sh"
    assert hook_file.is_file(), f"Expected {hook_file} to exist"

    text = hook_file.read_text(encoding="utf-8")
    hardcoded_from_lines = [
        (i + 1, line.strip())
        for i, line in enumerate(text.splitlines())
        if "## From: docs/pipeline/" in line
    ]

    assert hardcoded_from_lines == [], (
        f"Found {len(hardcoded_from_lines)} hardcoded '## From: docs/pipeline/' comment(s) "
        f"in post-compact-reinject.sh. These should use variable interpolation ($STATE_FILE, $BRIEF_FILE):\n"
        + "\n".join(f"  line {ln}: {txt}" for ln, txt in hardcoded_from_lines)
    )


def test_T_0035_007_session_boot_has_state_dir_field():
    """session-boot.sh JSON output template must contain a "state_dir" field.

    Both source/shared/hooks/session-boot.sh and source/claude/hooks/session-boot.sh
    must include this field so Eva knows the resolved state directory at boot.

    Expected: FAIL before Colby implements (field does not exist yet).
    """
    for variant in ["shared", "claude"]:
        boot_file = SOURCE_DIR / variant / "hooks" / "session-boot.sh"
        assert boot_file.is_file(), f"Expected {boot_file} to exist"

        text = boot_file.read_text(encoding="utf-8")
        # The JSON template should contain "state_dir" as a key.
        # It could appear as "state_dir": "..." or similar.
        assert '"state_dir"' in text, (
            f'session-boot.sh ({variant}) JSON output must contain a "state_dir" field '
            f"so Eva knows the resolved state directory at boot. "
            f"ADR-0035 R11 requires this."
        )


def test_T_0035_008_affected_hook_tests_pass():
    """Hook tests directly affected by ADR-0035 must pass (regression gate).

    Runs targeted tests for enforce-eva-paths, enforce-ellis-paths,
    session-boot, and post-compact-reinject hooks. These are the hooks
    modified by ADR-0035. Does not re-run the full 819-test suite.

    Expected: PASS currently (no source changes yet).
    """
    result = _run_affected_hook_tests()
    assert result.returncode == 0, (
        f"Affected hook tests failed (exit {result.returncode}).\n"
        f"stdout:\n{result.stdout[-2000:]}\n"
        f"stderr:\n{result.stderr[-1000:]}"
    )


# ── Step 3: S4 resolution + structural checks ──────────────────────────────


def test_T_0035_022_ellis_hook_has_adr0035_comment():
    """enforce-ellis-paths.sh header must contain an ADR-0035 supersession comment.

    The comment documents that ADR-0022 R20 ("no path hooks for Ellis") is
    superseded by ADR-0035's decision to keep the hook as a safety net.

    Expected: FAIL before Colby implements (no ADR-0035 reference in header).
    """
    hook_file = SOURCE_DIR / "claude" / "hooks" / "enforce-ellis-paths.sh"
    assert hook_file.is_file(), f"Expected {hook_file} to exist"

    text = hook_file.read_text(encoding="utf-8")
    # Check for ADR-0035 reference in the comment header (first 10 lines)
    header_lines = text.splitlines()[:10]
    header_text = "\n".join(header_lines)

    assert "ADR-0035" in header_text, (
        f"enforce-ellis-paths.sh header (first 10 lines) must contain 'ADR-0035' "
        f"documenting the supersession of ADR-0022 R20. "
        f"Got header:\n{header_text}"
    )


def test_T_0035_023_ellis_test_docstring_references_adr0035():
    """test_enforce_ellis_paths.py docstring must reference ADR-0035.

    Expected: FAIL before Colby implements (docstring only references ADR-0034).
    """
    test_file = PROJECT_ROOT / "tests" / "hooks" / "test_enforce_ellis_paths.py"
    assert test_file.is_file(), f"Expected {test_file} to exist"

    text = test_file.read_text(encoding="utf-8")
    # The module docstring is the first triple-quoted string in the file.
    # Check that it contains ADR-0035.
    # Module docstring should be within the first 30 lines.
    first_30_lines = "\n".join(text.splitlines()[:30])

    assert "ADR-0035" in first_30_lines, (
        f"test_enforce_ellis_paths.py module docstring (first 30 lines) must reference "
        f"ADR-0035 S4 resolution. Current header does not contain 'ADR-0035'."
    )


def test_T_0035_024_pipeline_orchestration_has_concurrent_session_protocol():
    """pipeline-orchestration.md must contain the concurrent-session-hard-pause protocol.

    Expected: FAIL before Colby implements (protocol section does not exist yet).
    """
    orch_file = SOURCE_DIR / "shared" / "rules" / "pipeline-orchestration.md"
    assert orch_file.is_file(), f"Expected {orch_file} to exist"

    text = orch_file.read_text(encoding="utf-8")

    assert '<protocol id="concurrent-session-hard-pause">' in text, (
        "pipeline-orchestration.md must contain a "
        '<protocol id="concurrent-session-hard-pause"> section '
        "per ADR-0035 R9."
    )


def test_T_0035_025_concurrent_session_protocol_has_three_options():
    """Concurrent-session protocol must specify exactly 3 user options.

    The options per ADR-0035:
    1. Adopt existing state
    2. Archive and start fresh
    3. Cancel this session

    Expected: FAIL before Colby implements (protocol section does not exist yet).
    """
    orch_file = SOURCE_DIR / "shared" / "rules" / "pipeline-orchestration.md"
    assert orch_file.is_file(), f"Expected {orch_file} to exist"

    text = orch_file.read_text(encoding="utf-8")

    # Extract the concurrent-session-hard-pause protocol section
    protocol_start = text.find('<protocol id="concurrent-session-hard-pause">')
    assert protocol_start != -1, (
        "Cannot find concurrent-session-hard-pause protocol section in "
        "pipeline-orchestration.md (prerequisite for counting options)."
    )
    protocol_end = text.find("</protocol>", protocol_start)
    assert protocol_end != -1, (
        "concurrent-session-hard-pause protocol section has no closing </protocol> tag."
    )
    protocol_text = text[protocol_start:protocol_end]

    # Count numbered options (lines starting with "N. " where N is 1, 2, or 3)
    # The ADR specifies a numbered list: 1. Adopt..., 2. Archive..., 3. Cancel...
    option_pattern = re.compile(r"^\s*\d+\.\s+\*\*", re.MULTILINE)
    options = option_pattern.findall(protocol_text)

    assert len(options) == 3, (
        f"Concurrent-session protocol must specify exactly 3 user options "
        f"(Adopt, Archive, Cancel). Found {len(options)} numbered bold items."
    )


def test_T_0035_026_orchestration_state_files_uses_placeholder():
    """pipeline-orchestration.md state-files section must use {pipeline_state_dir}, not docs/pipeline.

    Expected: PASS currently (already converted in a prior wave).
    """
    orch_file = SOURCE_DIR / "shared" / "rules" / "pipeline-orchestration.md"
    assert orch_file.is_file(), f"Expected {orch_file} to exist"

    text = orch_file.read_text(encoding="utf-8")

    # The state-files section should reference {pipeline_state_dir}, not docs/pipeline
    # Look for the "Eva maintains five files" line
    maintains_pattern = re.compile(r"Eva maintains\b.*\bfiles\b.*\bin\b", re.IGNORECASE)
    maintains_matches = [
        (i + 1, line.strip())
        for i, line in enumerate(text.splitlines())
        if maintains_pattern.search(line)
    ]

    assert maintains_matches, (
        "Could not find 'Eva maintains ... files in ...' line in pipeline-orchestration.md"
    )

    for lineno, line in maintains_matches:
        # The line should contain {pipeline_state_dir}, not docs/pipeline
        assert "{pipeline_state_dir}" in line, (
            f"Line {lineno} in pipeline-orchestration.md state-files section "
            f"must use '{{pipeline_state_dir}}' placeholder, not hardcoded 'docs/pipeline'. "
            f"Got: {line}"
        )
        assert "docs/pipeline" not in line.replace("docs/pipeline/error-patterns", ""), (
            f"Line {lineno} still contains hardcoded 'docs/pipeline' reference "
            f"(excluding error-patterns.md which stays in-repo). Got: {line}"
        )


def test_T_0035_027_affected_hook_tests_pass():
    """Hook tests affected by ADR-0035 must pass -- regression gate for Step 3.

    Same targeted subset as T-0035-008. Run after Step 3 source changes.

    Expected: PASS currently (no source changes yet).
    """
    result = _run_affected_hook_tests()
    assert result.returncode == 0, (
        f"Affected hook tests failed after Step 3 changes (exit {result.returncode}).\n"
        f"stdout:\n{result.stdout[-2000:]}\n"
        f"stderr:\n{result.stderr[-1000:]}"
    )
