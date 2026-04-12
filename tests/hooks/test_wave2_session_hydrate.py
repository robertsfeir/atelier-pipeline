"""Tests for ADR-0034 Wave 2 Step 2.4: session-hydrate.sh deletion deadline.

Covers T-0034-045.

Step 2.4 verification: SKILL.md Step 0c session-hydrate.sh removal instructions
must still be present and correct after Wave 2 ships. This test ensures the
removal block was not accidentally deleted during hook rewiring.

Colby MUST NOT modify these assertions.
"""

import re
from pathlib import Path

from conftest import PROJECT_ROOT

SKILL_MD_PATH = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"


# ═══════════════════════════════════════════════════════════════════════════════
# T-0034-045: SKILL.md Step 0c session-hydrate.sh removal block is present
# ═══════════════════════════════════════════════════════════════════════════════


def test_T_0034_045_skill_md_has_session_hydrate_removal_instructions():
    """SKILL.md Step 0c must still contain the session-hydrate.sh removal instructions.

    ADR-0034 Step 2.4 Acceptance Criteria:
      "SKILL.md's Step 1 session-hydrate.sh removal block is still present and correct."

    NOTE: The ADR uses "Step 1" loosely -- the block is actually labeled
    "Step 0c: Clean Up Orphan session-hydrate.sh Registration" in the current
    SKILL.md. This test checks for the canonical content, not the heading number,
    since headings may be renumbered.

    The block must contain all of the following elements:
    1. A reference to `session-hydrate.sh` being a no-op (superseded)
    2. The conditional check instruction (check settings.json for the registration)
    3. The removal instruction (remove the hook entry)
    4. The printed notice text: "Removed orphan session-hydrate.sh registration"
    5. A note that the FILE ITSELF is NOT deleted (backward-compat shim)

    If any element is missing, the cleanup step is broken and users on older
    installs will keep the dead hook registered.
    """
    assert SKILL_MD_PATH.exists(), (
        f"skills/pipeline-setup/SKILL.md not found at {SKILL_MD_PATH}. "
        f"This file must exist for the pipeline-setup skill to function."
    )

    text = SKILL_MD_PATH.read_text()

    # Element 1: session-hydrate.sh no-op context must be present
    assert "session-hydrate.sh" in text, (
        f"SKILL.md does not mention 'session-hydrate.sh' at all. "
        f"The Step 0c cleanup block has been removed. "
        f"ADR-0034 Step 2.4 requires this block to remain in place for backward compatibility."
    )

    # Element 2 + 3: the settings.json check-and-remove instruction
    has_settings_check = (
        "settings.json" in text and
        "session-hydrate.sh" in text
    )
    assert has_settings_check, (
        f"SKILL.md does not contain both 'settings.json' and 'session-hydrate.sh'. "
        f"The Step 0c block must instruct the skill to check settings.json for "
        f"a session-hydrate.sh registration and remove it."
    )

    # Element 4: the exact printed notice text
    expected_notice = "Removed orphan session-hydrate.sh registration"
    assert expected_notice in text, (
        f"SKILL.md is missing the exact print notice: '{expected_notice}'. "
        f"The Step 0c block must instruct the skill to print this exact string "
        f"when the entry is found and removed. "
        f"This message is used by users to confirm the cleanup ran."
    )

    # Element 5: note that the FILE is not deleted (backward-compat shim)
    # This prevents accidental deletion of the hook file itself
    has_not_deleted_note = (
        "NOT deleted" in text or
        "not deleted" in text or
        "NOT delete" in text or
        "is NOT deleted" in text
    )
    assert has_not_deleted_note, (
        f"SKILL.md is missing a note that the session-hydrate.sh FILE is NOT deleted "
        f"(only the settings.json registration is removed). "
        f"Without this note, a future editor might remove the backward-compat shim "
        f"prematurely and break installs that rely on the file being present."
    )

    # Bonus check: confirm the step heading or section context is still recognizable
    has_step_context = (
        "Step 0c" in text or
        "session-hydrate.sh Registration" in text or
        "Orphan session-hydrate" in text
    )
    assert has_step_context, (
        f"SKILL.md is missing the Step 0c heading or 'Orphan session-hydrate' context. "
        f"The removal block may have been reformatted without preserving its meaning. "
        f"Expected one of: 'Step 0c', 'session-hydrate.sh Registration', "
        f"or 'Orphan session-hydrate' to appear as a section marker."
    )
