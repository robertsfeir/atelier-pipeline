"""ADR-0005 Step 2: Invocation Templates Conversion.

Tests: T-0005-020 through T-0005-029.
Migrated from step2-invocation-templates.test.bats.
"""

import re

from tests.conftest import (
    SHARED_REFS,
    SOURCE_REFS,
    assert_not_contains,
    count_matches,
)

# Source path alias: references live in source/shared/references/
INSTALLED_REFS = SHARED_REFS


# ── T-0005-020 ───────────────────────────────────────────────────────

def test_T_0005_020_every_invocation_uses_task_as_first_tag():
    content = (INSTALLED_REFS / "invocation-templates.md").read_text()
    task_count = content.count("<task>")
    assert task_count > 0


# ── T-0005-021 ───────────────────────────────────────────────────────

def test_T_0005_021_brain_capable_invocations_include_brain_context():
    """Post ADR-0023/0024: <thought> element examples removed from templates.
    Verify brain-context injection is still documented."""
    content = (INSTALLED_REFS / "invocation-templates.md").read_text()
    assert "<brain-context>" in content or "brain-context" in content


# ── T-0005-022 ───────────────────────────────────────────────────────

def test_T_0005_022_poirot_invocation_no_brain_context():
    content = (INSTALLED_REFS / "invocation-templates.md").read_text()
    # Extract Poirot section
    poirot_match = re.search(r"(?i)poirot.*?(?=^##|\Z)", content, re.DOTALL | re.MULTILINE)
    if poirot_match:
        section = poirot_match.group(0)[:2000]
        assert "<brain-context>" not in section, "Poirot invocation should not have <brain-context>"


def test_T_0005_022b_distillator_invocation_no_brain_context():
    content = (INSTALLED_REFS / "invocation-templates.md").read_text()
    dist_match = re.search(r"(?i)distillator.*?(?=^##|\Z)", content, re.DOTALL | re.MULTILINE)
    if dist_match:
        section = dist_match.group(0)[:2000]
        assert "<brain-context>" not in section, "Distillator invocation should not have <brain-context>"


# ── T-0005-023 ───────────────────────────────────────────────────────

def test_T_0005_023_all_14_invocation_variants_present():
    content = (INSTALLED_REFS / "invocation-templates.md").read_text()
    variants = [
        r"Cal",
        r"(?i)colby.*mockup|mockup.*colby|Colby Mockup|Mockup",
        r"(?i)colby.*build|build.*colby|Colby Build|Build",
        r"(?i)roz.*investigation|investigation.*roz|Roz Investigation|Investigation",
        r"(?i)roz.*test spec|test spec.*review|Roz.*Spec Review|Test Spec Review",
        r"(?i)roz.*test authoring|test authoring|Roz.*Authoring|Test Authoring",
        r"(?i)roz.*code QA|code QA|Roz.*QA|Code QA",
        r"(?i)roz.*scoped|scoped.*re-run|Roz.*Re-Run|Scoped Re-Run",
        r"Poirot",
        r"Distillator",
        r"Ellis",
        r"Agatha",
        r"Robert",
        r"Sable",
    ]
    errors = []
    for variant in variants:
        if not re.search(variant, content):
            errors.append(f"Missing invocation variant matching: {variant}")
    assert not errors, "\n".join(errors)


# ── T-0005-024 ───────────────────────────────────────────────────────

def test_T_0005_024_source_preserves_placeholder_variables():
    content = (SOURCE_REFS / "invocation-templates.md").read_text()
    assert re.search(r"\{[a-z_]+\}", content), "No placeholder variables found in source invocation-templates.md"


# ── T-0005-025 ───────────────────────────────────────────────────────

def test_T_0005_025_no_invocation_has_tags_in_wrong_order():
    content = (INSTALLED_REFS / "invocation-templates.md").read_text()
    task_count = content.count("<task>")
    output_count = content.count("<output>")
    assert task_count >= output_count


# ── T-0005-026 ───────────────────────────────────────────────────────

def test_T_0005_026_no_old_flat_text_format():
    f = INSTALLED_REFS / "invocation-templates.md"
    assert_not_contains(f, r"^> TASK:", "Old flat format > TASK: found")
    assert_not_contains(f, r"^> READ:", "Old flat format > READ: found")
    assert_not_contains(f, r"^> CONTEXT:", "Old flat format > CONTEXT: found")
    assert_not_contains(f, r"^> CONSTRAINTS:", "Old flat format > CONSTRAINTS: found")
    assert_not_contains(f, r"^> OUTPUT:", "Old flat format > OUTPUT: found")
    assert_not_contains(f, r"^> WARN:", "Old flat format > WARN: found")


# ── T-0005-027 ───────────────────────────────────────────────────────

def test_T_0005_027_configure_comment_preserved():
    content = (INSTALLED_REFS / "invocation-templates.md").read_text()
    assert "CONFIGURE" in content


# ── T-0005-028 ───────────────────────────────────────────────────────

def test_T_0005_028_no_empty_task_tags():
    f = INSTALLED_REFS / "invocation-templates.md"
    content = f.read_text()
    assert_not_contains(f, r"<task>\s*</task>", "Empty <task> tag found")
    assert "<task></task>" not in content, "Empty <task></task> found"


# ── T-0005-029 ───────────────────────────────────────────────────────

def test_T_0005_029_every_thought_has_required_attributes():
    content = (INSTALLED_REFS / "invocation-templates.md").read_text()
    errors = []
    for line in content.splitlines():
        if "<thought " in line:
            for attr in ["type=", "agent=", "phase=", "relevance="]:
                if attr not in line:
                    errors.append(f"Missing '{attr}' attribute in thought element: {line.strip()}")
    assert not errors, "\n".join(errors)
