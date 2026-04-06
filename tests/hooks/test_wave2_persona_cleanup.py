"""Tests for ADR-0024 Wave 2: Behavioral brain capture text removal from personas and preamble.

Covers T-0024-016 through T-0024-025.

These tests verify ABSENCE of behavioral brain capture text after Wave 2.
All tests should FAIL before Wave 2 is implemented (the text is still present
in source/ files at this point).

Colby MUST NOT modify these assertions.
"""

import re
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


# ── Paths ─────────────────────────────────────────────────────────────────

SHARED_AGENTS = PROJECT_ROOT / "source" / "shared" / "agents"
SHARED_REFERENCES = PROJECT_ROOT / "source" / "shared" / "references"

CAL_PERSONA    = SHARED_AGENTS / "cal.md"
COLBY_PERSONA  = SHARED_AGENTS / "colby.md"
ROZ_PERSONA    = SHARED_AGENTS / "roz.md"
AGATHA_PERSONA = SHARED_AGENTS / "agatha.md"
AGENT_PREAMBLE = SHARED_REFERENCES / "agent-preamble.md"


# ═══════════════════════════════════════════════════════════════════════
# T-0024-016: Cal source persona has no "## Brain Access" section
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_016_cal_no_brain_access_section():
    """source/shared/agents/cal.md must not contain a '## Brain Access' section.

    This section contained behavioral instructions for calling agent_capture.
    After Wave 2, the mechanical SubagentStop hook replaces all behavioral
    brain capture instructions (ADR-0024 R5, AC-13).
    """
    assert CAL_PERSONA.exists(), f"Cal persona not found at {CAL_PERSONA}"
    text = CAL_PERSONA.read_text()
    assert "## Brain Access" not in text, (
        "Cal source persona still contains '## Brain Access' section. "
        "Wave 2 Step 2a must remove this section (ADR-0024 R5, AC-13)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-017: Colby source persona has no "## Brain Access" section
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_017_colby_no_brain_access_section():
    """source/shared/agents/colby.md must not contain a '## Brain Access' section."""
    assert COLBY_PERSONA.exists(), f"Colby persona not found at {COLBY_PERSONA}"
    text = COLBY_PERSONA.read_text()
    assert "## Brain Access" not in text, (
        "Colby source persona still contains '## Brain Access' section. "
        "Wave 2 Step 2a must remove this section (ADR-0024 R5, AC-13)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-018: Roz source persona has no "## Brain Access" section
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_018_roz_no_brain_access_section():
    """source/shared/agents/roz.md must not contain a '## Brain Access' section."""
    assert ROZ_PERSONA.exists(), f"Roz persona not found at {ROZ_PERSONA}"
    text = ROZ_PERSONA.read_text()
    assert "## Brain Access" not in text, (
        "Roz source persona still contains '## Brain Access' section. "
        "Wave 2 Step 2a must remove this section (ADR-0024 R5, AC-13)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-019: Agatha source persona has no "## Brain Access" section
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_019_agatha_no_brain_access_section():
    """source/shared/agents/agatha.md must not contain a '## Brain Access' section."""
    assert AGATHA_PERSONA.exists(), f"Agatha persona not found at {AGATHA_PERSONA}"
    text = AGATHA_PERSONA.read_text()
    assert "## Brain Access" not in text, (
        "Agatha source persona still contains '## Brain Access' section. "
        "Wave 2 Step 2a must remove this section (ADR-0024 R5, AC-13)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-020: Agatha source persona has no agent_capture reference
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_020_agatha_no_agent_capture_reference():
    """source/shared/agents/agatha.md must not contain any agent_capture reference.

    Agatha's DoD previously included: "Capture reasoning via `agent_capture` per..."
    This instruction is removed in Wave 2 Step 2a (ADR-0024 R5, step 2a AC).
    """
    assert AGATHA_PERSONA.exists(), f"Agatha persona not found at {AGATHA_PERSONA}"
    text = AGATHA_PERSONA.read_text()
    assert "agent_capture" not in text, (
        "Agatha source persona still contains 'agent_capture'. "
        "The DoD 'Capture reasoning via agent_capture...' line must be removed "
        "in Wave 2 Step 2a (ADR-0024 step 2a AC)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-021: No cal/colby/roz/agatha source persona references thought_type for brain capture
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("agent_name,persona_path", [
    ("cal",   CAL_PERSONA),
    ("colby", COLBY_PERSONA),
    ("roz",   ROZ_PERSONA),
    ("agatha",AGATHA_PERSONA),
])
def test_T_0024_021_no_thought_type_in_agent_personas(agent_name, persona_path):
    """source/shared/agents/{agent}.md must not reference thought_type for brain capture.

    After Wave 2, the agent-to-thought_type mapping lives exclusively in the
    brain-extractor persona. The source agent personas must not contain these
    mappings (they would be redundant at best, confusing at worst).
    ADR-0024 Step 2a AC: 'grep thought_type source/shared/agents/{cal,colby,roz,agatha}.md
    returns no matches'.
    """
    assert persona_path.exists(), f"{agent_name} persona not found at {persona_path}"
    text = persona_path.read_text()
    # thought_type references in the context of brain capture instructions
    # Note: exclude any occurrences that are in comments or in the text describing
    # what NOT to do -- we check for the presence of thought_type as a capture instruction
    assert "thought_type" not in text, (
        f"source/shared/agents/{agent_name}.md still references 'thought_type'. "
        f"The thought_type mapping belongs in brain-extractor.md only (ADR-0024 Step 2a)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-022: agent-preamble.md has no <protocol id="brain-capture"> section
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_022_preamble_no_brain_capture_protocol():
    """source/shared/references/agent-preamble.md must not contain <protocol id="brain-capture">.

    Wave 2 Step 2b removes the entire brain-capture protocol section from the
    shared preamble (~30 lines). After removal, agents no longer receive
    behavioral instructions to call agent_capture (ADR-0024 R6, AC-15).
    """
    assert AGENT_PREAMBLE.exists(), f"agent-preamble.md not found at {AGENT_PREAMBLE}"
    text = AGENT_PREAMBLE.read_text()
    assert '<protocol id="brain-capture">' not in text, (
        "agent-preamble.md still contains '<protocol id=\"brain-capture\">'. "
        "Wave 2 Step 2b must remove the entire brain-capture protocol section "
        "(ADR-0024 R6, AC-15)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-023: agent-preamble.md step 4 does not mention "capture domain-specific knowledge directly"
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_023_preamble_step4_no_capture_instruction():
    """agent-preamble.md step 4 must not instruct agents to capture domain-specific knowledge.

    The step 4 brain context review step should retain only the read/consumption
    instruction (how to use brain context). The 'also capture domain-specific
    knowledge directly via agent_capture' language must be removed.
    ADR-0024 Step 2b AC: step 4 retains only the read/consumption instruction.
    """
    assert AGENT_PREAMBLE.exists(), f"agent-preamble.md not found at {AGENT_PREAMBLE}"
    text = AGENT_PREAMBLE.read_text()
    # The specific phrase that must be absent after cleanup
    assert "capture domain-specific knowledge directly" not in text, (
        "agent-preamble.md still contains 'capture domain-specific knowledge directly'. "
        "Step 4 must be updated to remove the capture instruction "
        "(ADR-0024 Step 2b AC)."
    )
    # Also check for the broader capture-via-agent_capture instruction
    assert "also capture" not in text.lower() or "agent_capture" not in text, (
        "agent-preamble.md appears to retain 'also capture ... agent_capture' language. "
        "After Wave 2, agents no longer self-capture -- the extractor hook handles it."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-024: agent-preamble.md has no "How to Capture" subsection
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_024_preamble_no_how_to_capture_subsection():
    """agent-preamble.md must not contain a 'How to Capture' subsection.

    This was a subsection of the <protocol id="brain-capture"> block.
    Its removal is part of Wave 2 Step 2b (ADR-0024 Step 2b AC).
    """
    assert AGENT_PREAMBLE.exists(), f"agent-preamble.md not found at {AGENT_PREAMBLE}"
    text = AGENT_PREAMBLE.read_text()
    assert "### How to Capture" not in text, (
        "agent-preamble.md still contains '### How to Capture' subsection. "
        "This subsection is part of the brain-capture protocol removed in "
        "Wave 2 Step 2b (ADR-0024 Step 2b AC)."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0024-025: agent-preamble.md has no "Capture Gates" subsection
# ═══════════════════════════════════════════════════════════════════════


def test_T_0024_025_preamble_no_capture_gates_subsection():
    """agent-preamble.md must not contain a 'Capture Gates' subsection.

    This was a subsection of the <protocol id="brain-capture"> block.
    Its removal is part of Wave 2 Step 2b (ADR-0024 Step 2b AC).
    """
    assert AGENT_PREAMBLE.exists(), f"agent-preamble.md not found at {AGENT_PREAMBLE}"
    text = AGENT_PREAMBLE.read_text()
    assert "### Capture Gates" not in text, (
        "agent-preamble.md still contains '### Capture Gates' subsection. "
        "This subsection is part of the brain-capture protocol removed in "
        "Wave 2 Step 2b (ADR-0024 Step 2b AC)."
    )
