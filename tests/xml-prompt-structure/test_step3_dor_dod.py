"""ADR-0005 Step 3: DoR/DoD Reference Conversion.

Tests: T-0005-030 through T-0005-035.
Migrated from step3-dor-dod.test.bats.
"""

import re

from tests.conftest import INSTALLED_REFS, SOURCE_REFS, line_of


# ── T-0005-030 ───────────────────────────────────────────────────────

def test_T_0005_030_dor_dod_references_output_tag():
    content = (INSTALLED_REFS / "dor-dod.md").read_text()
    assert re.search(r"<output>|`<output>`", content)


# ── T-0005-031 ───────────────────────────────────────────────────────

def test_T_0005_031_dor_before_dod_in_templates():
    f = INSTALLED_REFS / "dor-dod.md"
    content = f.read_text()
    dor_lines = [i for i, l in enumerate(content.splitlines(), 1) if "DoR" in l]
    dod_lines = [i for i, l in enumerate(content.splitlines(), 1) if "DoD" in l]
    assert dor_lines, "No DoR found"
    assert dod_lines, "No DoD found"
    assert dor_lines[0] < dod_lines[-1]


# ── T-0005-032 ───────────────────────────────────────────────────────

def test_T_0005_032_existing_field_definitions_preserved():
    content = (INSTALLED_REFS / "dor-dod.md").read_text().lower()
    for field in ["retro risks", "source citations", "status"]:
        assert field.lower() in content, f"Missing field definition: {field}"


# ── T-0005-033 ───────────────────────────────────────────────────────

def test_T_0005_033_dor_dod_within_output_context():
    content = (INSTALLED_REFS / "dor-dod.md").read_text()
    assert re.search(r"<output>|`<output>`|output.*tag", content, re.IGNORECASE)


# ── T-0005-034 ───────────────────────────────────────────────────────

def test_T_0005_034_no_original_field_missing():
    content = (INSTALLED_REFS / "dor-dod.md").read_text().lower()
    for field in ["requirements", "dor", "dod", "verification", "deferred"]:
        assert field in content, f"Missing field: {field}"


# ── T-0005-035 ───────────────────────────────────────────────────────

def test_T_0005_035_no_standalone_dor_dod_headings():
    content = (INSTALLED_REFS / "dor-dod.md").read_text()
    in_code = False
    fail = False
    errors = []
    for line in content.splitlines():
        if re.match(r"^\s*```", line):
            in_code = not in_code
        if not in_code and re.match(r"^## DoR\b|^## DoD\b", line):
            errors.append(f"Found top-level heading outside code block: {line}")
            fail = True
    assert not fail, "\n".join(errors)


# ── Source/installed sync ────────────────────────────────────────────

def test_T_0005_030b_source_dor_dod_references_output_tag():
    content = (SOURCE_REFS / "dor-dod.md").read_text()
    assert re.search(r"<output>|`<output>`", content)
