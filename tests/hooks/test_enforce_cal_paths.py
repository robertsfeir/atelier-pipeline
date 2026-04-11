"""Tests for ADR-0033 Step 5 (m2): enforce-cal-paths.sh dead MultiEdit branch removal.

Covers T-0033-025.

Cal's frontmatter registers the hook on Write|Edit only — MultiEdit is
unreachable. The existing hook has `case "$TOOL_NAME" in Write|Edit|MultiEdit)`
with a dead MultiEdit arm; the fix removes MultiEdit.

This is a regression test: the hook's BEHAVIOR doesn't change (MultiEdit
cannot reach this case statement at runtime), but the source file's dead
code is eliminated and future readers won't be misled.

Colby MUST NOT modify these assertions.
"""

import re

from conftest import PROJECT_ROOT

HOOK = PROJECT_ROOT / "source" / "claude" / "hooks" / "enforce-cal-paths.sh"


# ═══════════════════════════════════════════════════════════════════════
# T-0033-025: case statement must not include MultiEdit
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_025_cal_case_statement_no_multiedit():
    """enforce-cal-paths.sh TOOL_NAME case statement must match Write|Edit only.

    Scans the source file for any `case ... in` line that includes
    `Write|Edit|MultiEdit` — that pattern must not exist after the Step 5 (m2) fix.
    The expected form is `Write|Edit)` (no MultiEdit).
    """
    assert HOOK.exists(), f"enforce-cal-paths.sh missing at {HOOK}"
    text = HOOK.read_text()

    # Find the TOOL_NAME case line(s).
    case_lines = [
        line for line in text.splitlines()
        if "case " in line and "TOOL_NAME" in line
    ]
    assert case_lines, (
        "Could not find a `case \"$TOOL_NAME\" in ...` line in enforce-cal-paths.sh"
    )

    # Assert MultiEdit does not appear on the case line.
    for line in case_lines:
        assert "MultiEdit" not in line, (
            f"enforce-cal-paths.sh still has dead MultiEdit branch in case statement:\n"
            f"  {line}\n"
            f"ADR-0033 Step 5 (m2) removes MultiEdit — it's unreachable because "
            f"Cal's frontmatter registers the hook on Write|Edit only."
        )
        # Positive check: Write and Edit should both still be present.
        assert re.search(r"\bWrite\b", line), (
            f"Write missing from case statement: {line}"
        )
        assert re.search(r"\bEdit\b", line), (
            f"Edit missing from case statement: {line}"
        )
