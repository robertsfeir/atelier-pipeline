"""ADR-0005 Step 6: Eva's Rules Files Update.

Tests: T-0005-070 through T-0005-075, T-0005-112 through T-0005-113.
Migrated from step6-eva-rules.test.bats.
"""

import re

from tests.conftest import (
    INSTALLED_RULES,
    SOURCE_RULES,
    assert_not_contains,
    extract_section,
)


# ── T-0005-070 ───────────────────────────────────────────────────────

def test_T_0005_070_agent_system_shows_xml_format():
    content = (INSTALLED_RULES / "agent-system.md").read_text()
    assert "<task>" in content
    assert "<constraints>" in content
    assert "<output>" in content


# ── T-0005-071 ───────────────────────────────────────────────────────

def test_T_0005_071_shared_behaviors_references_xml_tags():
    content = (INSTALLED_RULES / "agent-system.md").read_text()
    assert (re.search(r"<required-actions>|<output>|<identity>|required-actions|`<", content) or
            re.search(r"XML.*tag|tag.*structure|persona.*tag", content, re.IGNORECASE))


# ── T-0005-072 ───────────────────────────────────────────────────────

def test_T_0005_072_brain_responsibility_shift_documented():
    content = (INSTALLED_RULES / "agent-system.md").read_text()
    assert (re.search(r"pre.?fetch|prefetch|Eva.*brain.*context|brain.*context.*Eva", content, re.IGNORECASE) or
            re.search(r"Eva.*inject|inject.*brain|Eva.*capture", content, re.IGNORECASE))


# ── T-0005-073 ───────────────────────────────────────────────────────

def test_T_0005_073_no_old_flat_invocation_format():
    content = (INSTALLED_RULES / "agent-system.md").read_text()
    # Extract template section
    section = extract_section(content, r"Standardized Template", r"^## ")
    assert not re.search(r"^TASK:", section, re.MULTILINE), "Old flat format 'TASK:' found in template section"


# ── T-0005-074 ───────────────────────────────────────────────────────

def test_T_0005_074_pipeline_models_notes_persona_files():
    f = INSTALLED_RULES / "pipeline-models.md"
    if not f.is_file():
        return  # skip equivalent
    content = f.read_text()
    assert re.search(r"persona|identity|agent.*file", content, re.IGNORECASE)


# ── T-0005-075 ───────────────────────────────────────────────────────

def test_T_0005_075_source_agent_system_xml_format():
    content = (SOURCE_RULES / "agent-system.md").read_text()
    assert "<task>" in content
    assert "<constraints>" in content
    assert "<output>" in content


# ── T-0005-112 ───────────────────────────────────────────────────────

def test_T_0005_112_no_old_flat_text_markers():
    content = (INSTALLED_RULES / "agent-system.md").read_text()
    section = extract_section(content, r"Standardized Template", r"^## ")
    for marker in ["TASK:", "READ:", "CONTEXT:", "WARN:", "CONSTRAINTS:", "OUTPUT:"]:
        assert not re.search(rf"^{marker}", section, re.MULTILINE), \
            f"Old flat marker '{marker}' found as line-starting format element"


# ── T-0005-113 ───────────────────────────────────────────────────────

def test_T_0005_113_no_must_call_brain_tools():
    f = INSTALLED_RULES / "agent-system.md"
    assert_not_contains(f, "MUST call agent_search", "Found 'MUST call agent_search'")
    assert_not_contains(f, "MUST call agent_capture", "Found 'MUST call agent_capture'")
