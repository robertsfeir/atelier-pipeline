"""ADR-0005 Step 8: Pipeline Operations Reference Update.

Tests: T-0005-090 through T-0005-095.
Migrated from step8-pipeline-operations.test.bats.
"""

import re

from tests.conftest import (
    INSTALLED_REFS,
    SOURCE_REFS,
    assert_not_contains,
)


# ── T-0005-090 ───────────────────────────────────────────────────────

def test_T_0005_090_pipeline_operations_references_xml():
    content = (INSTALLED_REFS / "pipeline-operations.md").read_text()
    assert re.search(r"<task>|<constraints>|<output>|XML.*invocation|invocation.*XML|XML.*tag", content, re.IGNORECASE)


# ── T-0005-091 ───────────────────────────────────────────────────────

def test_T_0005_091_brain_prefetch_documented():
    content = (INSTALLED_REFS / "pipeline-operations.md").read_text()
    assert re.search(r"Eva.*brain|brain.*prefetch|pre.?fetch|Eva.*inject|brain-context", content, re.IGNORECASE)


# ── T-0005-092 ───────────────────────────────────────────────────────

def test_T_0005_092_all_named_sections_preserved():
    content = (INSTALLED_REFS / "pipeline-operations.md").read_text().lower()
    errors = []
    for section in ["continuous qa", "feedback loop", "batch mode", "worktree", "triage"]:
        if section not in content:
            errors.append(f"Missing section: {section}")
    assert not errors, "\n".join(errors)


# ── T-0005-093 ───────────────────────────────────────────────────────

def test_T_0005_093_no_old_flat_text_markers():
    content = (INSTALLED_REFS / "pipeline-operations.md").read_text()
    for marker in ["TASK:", "READ:", "CONTEXT:"]:
        assert not re.search(rf"^\s*{marker}", content, re.MULTILINE), \
            f"Old flat marker '{marker}' found as format element"


# ── T-0005-094 ───────────────────────────────────────────────────────

def test_T_0005_094_brain_prefetch_in_invocation_area():
    content = (INSTALLED_REFS / "pipeline-operations.md").read_text()
    assert re.search(r"prefetch|pre-fetch|brain-context|brain context.*inject", content, re.IGNORECASE)


# ── T-0005-095 ───────────────────────────────────────────────────────

def test_T_0005_095_no_agent_initiated_brain_calls():
    f = INSTALLED_REFS / "pipeline-operations.md"
    assert_not_contains(f, "agent calls agent_search", "Found agent-initiated brain call phrasing")
    assert_not_contains(f, "agent calls agent_capture", "Found agent-initiated brain capture phrasing")


# ── Source sync ──────────────────────────────────────────────────────

def test_T_0005_090b_source_pipeline_operations_xml_format():
    content = (SOURCE_REFS / "pipeline-operations.md").read_text()
    assert re.search(r"<task>|<constraints>|<output>|XML.*invocation|invocation.*XML|XML.*tag", content, re.IGNORECASE)
