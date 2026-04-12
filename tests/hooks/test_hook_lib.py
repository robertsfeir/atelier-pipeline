"""Tests for ADR-0034 Wave 2 Step 2.1: hook-lib.sh shared function library.

Covers T-0034-021 through T-0034-027.

Tests define the contract for `source/shared/hooks/hook-lib.sh` -- a file
that does NOT yet exist. All function-invocation tests (T-0034-021 through
T-0034-025) will FAIL until Colby ships the library.

T-0034-026 and T-0034-027 are deduplication-verification tests that grep the
source tree. They will also fail until Colby rewires the hooks to use the library.

Colby MUST NOT modify these assertions.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT

# ── Paths ─────────────────────────────────────────────────────────────────────

HOOK_LIB_PATH = PROJECT_ROOT / "source" / "shared" / "hooks" / "hook-lib.sh"
SOURCE_CLAUDE_HOOKS = PROJECT_ROOT / "source" / "claude" / "hooks"


# ── Helper: source hook-lib.sh and call a function ────────────────────────────


def call_hook_lib_function(function_name: str, args: list[str], stdin_data: str) -> subprocess.CompletedProcess:
    """Source hook-lib.sh in a subprocess, call function_name with args, pipe stdin_data in.

    If hook-lib.sh does not exist, the script will fail with a non-zero exit
    and an error message -- that is the expected red-bar state before Colby builds.

    Returns CompletedProcess with combined stdout+stderr.
    """
    # Build a small bash driver that sources the lib, then calls the function
    script = f"""
#!/bin/bash
set -uo pipefail
HOOK_LIB="{HOOK_LIB_PATH}"
if [ ! -f "$HOOK_LIB" ]; then
  echo "ERROR: hook-lib.sh not found at $HOOK_LIB -- Wave 2 Step 2.1 not yet implemented" >&2
  exit 99
fi
source "$HOOK_LIB"
{function_name} {' '.join(args)}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(script)
        script_path = f.name
    try:
        os.chmod(script_path, 0o755)
        result = subprocess.run(
            ["bash", script_path],
            input=stdin_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
        return result
    finally:
        os.unlink(script_path)


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-021: hook_lib_pipeline_status_field with embedded } brace in value
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_021_pipeline_status_field_handles_embedded_brace():
    """hook_lib_pipeline_status_field phase returns the correct field value when the
    JSON contains an embedded `}` brace inside a string value.

    This is the ADR-defined S22 regression test. The old `grep -o 'PIPELINE_STATUS' ...`
    parser breaks on values containing `}` because it matches only up to the first `}`.
    The new library function uses `jq -R 'fromjson? // empty'` which is JSON-aware
    and handles embedded braces correctly.

    Stdin format matches pipeline-state.md PIPELINE_STATUS marker:
      <!-- PIPELINE_STATUS: <json-object> -->
    The function reads stdin and extracts the named field from the JSON object.
    """
    # Input containing an embedded } in a string value (the brace-in-value edge case)
    pipeline_status_json = json.dumps({
        "phase": "build",
        "feature": "with } brace in value",
        "agent": "colby",
    })
    stdin_data = f"# Pipeline State\n\n<!-- PIPELINE_STATUS: {pipeline_status_json} -->\n"

    r = call_hook_lib_function("hook_lib_pipeline_status_field", ["phase"], stdin_data)

    assert r.returncode != 99, (
        "hook-lib.sh does not exist yet (Wave 2 Step 2.1 not implemented). "
        "This test is red until Colby ships source/shared/hooks/hook-lib.sh."
    )
    assert r.returncode == 0, (
        f"hook_lib_pipeline_status_field returned non-zero ({r.returncode}). "
        f"Output: {r.stdout!r}"
    )
    output = r.stdout.strip()
    assert output == "build", (
        f"Expected 'build' but got {output!r}. "
        f"The embedded '}}' brace in the 'feature' value must not corrupt 'phase' extraction. "
        f"Input JSON: {pipeline_status_json}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-022: hook_lib_json_escape handles special characters
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_022_json_escape_handles_special_characters():
    """hook_lib_json_escape produces valid JSON-escaped output for strings containing
    newline, double-quote, backslash, tab, and unicode (e.g. é).

    This is the S22 regression: the old sed-based json_escape in session-boot.sh
    was non-functional (it missed cases). The new jq-Rs-based implementation must
    correctly escape all of these and produce output that round-trips through
    JSON.parse.

    The function writes to stdout. We verify: (a) the output is valid JSON string
    (parseable by jq), and (b) the unescaped value round-trips correctly.
    """
    # String with all the edge-case characters the ADR specifies
    raw_input = 'line1\nline2\t"quoted"\\ and é'

    r = call_hook_lib_function("hook_lib_json_escape", [], raw_input)

    assert r.returncode != 99, (
        "hook-lib.sh does not exist yet (Wave 2 Step 2.1 not implemented). "
        "This test is red until Colby ships source/shared/hooks/hook-lib.sh."
    )
    assert r.returncode == 0, (
        f"hook_lib_json_escape returned non-zero ({r.returncode}). Output: {r.stdout!r}"
    )
    escaped = r.stdout.strip()

    # The escaped output must be a valid JSON string literal (parseable by Python json)
    try:
        parsed = json.loads(escaped)
    except json.JSONDecodeError as e:
        pytest.fail(
            f"hook_lib_json_escape output is not valid JSON: {escaped!r}. "
            f"Error: {e}. "
            f"The S22 regression fix must produce jq-Rs-escaped output."
        )

    # Round-trip: decoded value must match the original input
    assert parsed == raw_input, (
        f"Round-trip failed. Input: {raw_input!r}. "
        f"Escaped: {escaped!r}. "
        f"Decoded: {parsed!r}. "
        f"These must be identical."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-023: hook_lib_get_agent_type from tool_input.subagent_type
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_023_get_agent_type_from_tool_input_subagent_type():
    """hook_lib_get_agent_type returns the subagent_type from tool_input when
    top-level agent_type is absent.

    Input: {"tool_input": {"subagent_type": "roz"}}
    Expected output: roz
    """
    stdin_data = json.dumps({"tool_input": {"subagent_type": "roz"}})

    r = call_hook_lib_function("hook_lib_get_agent_type", [], stdin_data)

    assert r.returncode != 99, (
        "hook-lib.sh does not exist yet (Wave 2 Step 2.1 not implemented). "
        "This test is red until Colby ships source/shared/hooks/hook-lib.sh."
    )
    assert r.returncode == 0, (
        f"hook_lib_get_agent_type returned non-zero ({r.returncode}). Output: {r.stdout!r}"
    )
    assert r.stdout.strip() == "roz", (
        f"Expected 'roz' from tool_input.subagent_type, got {r.stdout.strip()!r}. "
        f"Input: {stdin_data}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-024: hook_lib_get_agent_type from top-level agent_type
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_024_get_agent_type_from_top_level():
    """hook_lib_get_agent_type returns the top-level agent_type field when present.

    Input: {"agent_type": "colby"}
    Expected output: colby
    """
    stdin_data = json.dumps({"agent_type": "colby"})

    r = call_hook_lib_function("hook_lib_get_agent_type", [], stdin_data)

    assert r.returncode != 99, (
        "hook-lib.sh does not exist yet (Wave 2 Step 2.1 not implemented). "
        "This test is red until Colby ships source/shared/hooks/hook-lib.sh."
    )
    assert r.returncode == 0, (
        f"hook_lib_get_agent_type returned non-zero ({r.returncode}). Output: {r.stdout!r}"
    )
    assert r.stdout.strip() == "colby", (
        f"Expected 'colby' from top-level agent_type, got {r.stdout.strip()!r}. "
        f"Input: {stdin_data}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-025: hook_lib_get_agent_type prefers top-level over tool_input fallback
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_025_get_agent_type_prefers_top_level_over_tool_input():
    """When both agent_type (top-level) and tool_input.subagent_type are present,
    hook_lib_get_agent_type returns the top-level agent_type.

    Input: {"agent_type": "colby", "tool_input": {"subagent_type": "roz"}}
    Expected output: colby   (top-level wins)

    The canonical jq expression `.agent_type // .tool_input.subagent_type // empty`
    returns the first non-null, which is agent_type.
    """
    stdin_data = json.dumps({
        "agent_type": "colby",
        "tool_input": {"subagent_type": "roz"},
    })

    r = call_hook_lib_function("hook_lib_get_agent_type", [], stdin_data)

    assert r.returncode != 99, (
        "hook-lib.sh does not exist yet (Wave 2 Step 2.1 not implemented). "
        "This test is red until Colby ships source/shared/hooks/hook-lib.sh."
    )
    assert r.returncode == 0, (
        f"hook_lib_get_agent_type returned non-zero ({r.returncode}). Output: {r.stdout!r}"
    )
    assert r.stdout.strip() == "colby", (
        f"Expected 'colby' (top-level agent_type wins over tool_input.subagent_type). "
        f"Got {r.stdout.strip()!r}. "
        f"Input: {stdin_data}. "
        f"jq expression must be: .agent_type // .tool_input.subagent_type // empty"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-026: PIPELINE_STATUS grep pattern is absent from all claude hooks
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_026_no_inline_pipeline_status_grep_in_claude_hooks():
    """After Wave 2 Step 2.1, no hook in source/claude/hooks/ should contain the
    inline PIPELINE_STATUS grep pattern. All parsers must delegate to hook-lib.sh.

    Pattern to check: `grep -o .PIPELINE_STATUS` (the old inline parser fragment).
    Zero matches = deduplication achieved.

    This test will FAIL until Colby rewires the hooks in Wave 2 Step 2.1.
    """
    assert SOURCE_CLAUDE_HOOKS.exists(), (
        f"source/claude/hooks/ directory not found at {SOURCE_CLAUDE_HOOKS}"
    )

    result = subprocess.run(
        ["grep", "-rn", "grep -o .PIPELINE_STATUS", str(SOURCE_CLAUDE_HOOKS)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
    )

    # grep returns 1 if no matches (success for our test), 0 if matches found (failure)
    matches = result.stdout.strip()
    assert not matches, (
        f"Found inline PIPELINE_STATUS grep pattern in source/claude/hooks/.\n"
        f"After Wave 2 Step 2.1, every hook must delegate to hook_lib_pipeline_status_field.\n"
        f"Matches:\n{matches}\n"
        f"Remove these inline parsers and source hook-lib.sh instead."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-027: inline jq agent_type extraction is absent from all claude hooks
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_027_no_inline_agent_type_jq_in_claude_hooks():
    """After Wave 2 Step 2.1, no hook in source/claude/hooks/ should contain the
    inline `jq -r '.agent_type // empty'` pattern. All extractions must delegate
    to hook_lib_get_agent_type from hook-lib.sh.

    Zero matches = deduplication achieved.

    This test will FAIL until Colby rewires the hooks in Wave 2 Step 2.1.
    """
    assert SOURCE_CLAUDE_HOOKS.exists(), (
        f"source/claude/hooks/ directory not found at {SOURCE_CLAUDE_HOOKS}"
    )

    result = subprocess.run(
        ["grep", "-rn", r"jq -r '\.agent_type // empty'", str(SOURCE_CLAUDE_HOOKS)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
    )

    matches = result.stdout.strip()
    assert not matches, (
        f"Found inline jq '.agent_type // empty' pattern in source/claude/hooks/.\n"
        f"After Wave 2 Step 2.1, every hook must delegate to hook_lib_get_agent_type.\n"
        f"Matches:\n{matches}\n"
        f"Remove these inline extractions and source hook-lib.sh instead."
    )
