"""ADR-0041 pre-build test assertions: docs and cost-table updates.

Covers the documentation and telemetry ramifications of ADR-0041:
- telemetry-metrics.md cost-estimation rows for Haiku/Sonnet/Opus pricing
- user-facing guides updated for the tier model
- pipeline-setup SKILL.md carries the Claude Code version check soft-warning
- ADR-0041 file exists with an `Accepted` status line

Pre-build: most of these FAIL until Colby completes Steps 5, 7, and 8. That
is the expected pre-build signal per Roz-first TDD.
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TELEMETRY_METRICS = (
    PROJECT_ROOT / "source" / "shared" / "references" / "telemetry-metrics.md"
)
TECHNICAL_REFERENCE = PROJECT_ROOT / "docs" / "guide" / "technical-reference.md"
USER_GUIDE = PROJECT_ROOT / "docs" / "guide" / "user-guide.md"
PIPELINE_SETUP_SKILL = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"
ADR_FILE = PROJECT_ROOT / "docs" / "architecture" / "ADR-0041-effort-per-agent-map.md"
PIPELINE_ORCHESTRATION_SOURCE = (
    PROJECT_ROOT / "source" / "shared" / "rules" / "pipeline-orchestration.md"
)
PIPELINE_ORCHESTRATION_INSTALLED = (
    PROJECT_ROOT / ".claude" / "rules" / "pipeline-orchestration.md"
)


def _read(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"File not found: {path}")
    return path.read_text()


# ─────────────────────────────────────────────────────────────────────────────
# Telemetry cost rows
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "per_m_token_rate,family",
    [
        ("0.11", "Haiku"),
        ("0.33", "Sonnet"),
        ("2.22", "Opus"),
    ],
)
def test_telemetry_contains_per_m_token_rate(per_m_token_rate, family):
    """telemetry-metrics.md must contain the per-M-token cost figure for each
    model family -- the Haiku/Sonnet/Opus rates ADR-0041 §Step 5 carries.

    Pre-build: FAILS until Colby updates the cost-estimation table.
    """
    text = _read(TELEMETRY_METRICS)
    assert per_m_token_rate in text, (
        f"source/shared/references/telemetry-metrics.md does not contain the "
        f"per-M-token rate '{per_m_token_rate}' for {family}. ADR-0041 Step 5 "
        "updates the cost-estimation rows; the Haiku/Sonnet/Opus rates must "
        "all appear."
    )


def test_telemetry_metrics_opus47_row():
    """Cost Estimation Table in telemetry-metrics.md must contain a
    claude-opus-4-7 row reflecting the new model variant introduced in
    ADR-0041 Step 5.

    Finding: F-2 (scout swarm confirmed absence of claude-opus-4-7).
    Pre-build: FAILS until Colby adds the row.
    """
    text = _read(TELEMETRY_METRICS)
    # Extract the Cost Estimation Table section only (between the section
    # heading and the next `---` horizontal rule).
    marker = "## Cost Estimation Table"
    if marker not in text:
        pytest.fail(
            "source/shared/references/telemetry-metrics.md does not contain "
            f"a '{marker}' heading -- table structure is broken."
        )
    section_start = text.index(marker)
    # Find the next `---` separator after the section heading.
    rest = text[section_start:]
    sep_pos = rest.find("\n---")
    cost_table_section = rest[:sep_pos] if sep_pos != -1 else rest
    assert "claude-opus-4-7" in cost_table_section, (
        "Cost Estimation Table must contain claude-opus-4-7 row "
        "(F-2, ADR-0041 §Step 5)"
    )


def test_telemetry_metrics_adr0041_footnote():
    """Per-Invocation Cost Estimates section in telemetry-metrics.md must
    cite ADR-0041 as the tier epoch (the revision that introduced the
    4-tier effort model).

    Finding: F-2 (scout swarm confirmed ADR-0041 absent from that section).
    Pre-build: FAILS until Colby annotates the section per ADR-0041 Step 5.
    """
    text = _read(TELEMETRY_METRICS)
    # Match either heading variant (with or without "by Model" suffix).
    heading_variants = [
        "### Per-Invocation Cost Estimates",
        "Per-Invocation Cost Estimates by Model",
        "Per-Invocation Cost Estimates",
    ]
    section_start = -1
    for variant in heading_variants:
        if variant in text:
            section_start = text.index(variant)
            break
    if section_start == -1:
        pytest.fail(
            "source/shared/references/telemetry-metrics.md does not contain "
            "a 'Per-Invocation Cost Estimates' heading -- section is missing."
        )
    per_invocation_section = text[section_start:]
    assert "ADR-0041" in per_invocation_section, (
        "Per-Invocation Cost Estimates section must cite ADR-0041 as tier "
        "epoch (F-2)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Technical reference -- tier model present, classifier framing gone
# ─────────────────────────────────────────────────────────────────────────────


def test_technical_reference_describes_tier_model():
    """docs/guide/technical-reference.md must describe the new tier model
    using one of the canonical phrasings from ADR-0041.

    Pre-build: FAILS until Colby runs Step 8.
    """
    text = _read(TECHNICAL_REFERENCE)
    phrasings = ["Task-class", "tier model", "4-tier"]
    assert any(p in text for p in phrasings), (
        "docs/guide/technical-reference.md does not describe the tier model. "
        f"Expected one of: {phrasings!r}. ADR-0041 Step 8 updates this file."
    )


def test_technical_reference_drops_universal_classifier():
    """docs/guide/technical-reference.md must no longer reference the
    superseded 'universal scope classifier' framing.

    Pre-build: FAILS (stale phrasing still present) until Colby runs Step 8.
    """
    text = _read(TECHNICAL_REFERENCE)
    assert "universal scope classifier" not in text, (
        "docs/guide/technical-reference.md still contains 'universal scope "
        "classifier'. ADR-0041 Step 8 removes this stale framing."
    )


# ─────────────────────────────────────────────────────────────────────────────
# User guide -- effort and tier model mentioned
# ─────────────────────────────────────────────────────────────────────────────


def test_user_guide_mentions_effort():
    """docs/guide/user-guide.md must mention the `effort` concept and the
    4-tier / task-class framing from ADR-0041, and must not retain stale
    'universal scope classifier' language.

    Finding: F-8/T-0041-056 (single `effort` check was insufficient; no
    negative assertion for stale classifier language; no 4-tier/task-class
    check).
    Pre-build: FAILS until Colby runs Step 8.
    """
    text = _read(USER_GUIDE)
    assert "universal scope classifier" not in text, (
        "user-guide.md must not contain stale classifier language"
    )
    assert "effort" in text.lower(), (
        "docs/guide/user-guide.md does not mention 'effort'. ADR-0041 Step 8 "
        "updates user-guide.md line ~1021 to cite tier-based assignment."
    )
    assert any(p in text.lower() for p in ["4-tier", "task class", "task-class"]), (
        "user-guide.md must mention '4-tier' or 'task class' per ADR-0041 Step 8"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline-setup SKILL.md -- Claude Code version check AND effort mention
# ─────────────────────────────────────────────────────────────────────────────


def test_pipeline_setup_skill_carries_version_and_adr_citation():
    """skills/pipeline-setup/SKILL.md must carry BOTH the `2.1.89` version
    check AND an explicit citation of `ADR-0041` per §Compatibility
    soft-warning. The prior `or` was too permissive -- the ADR requires both.

    Finding: F-4/T-0041-049 (original assertion used `or` not `and`).
    Pre-build: FAILS until Colby runs Step 7.
    """
    text = _read(PIPELINE_SETUP_SKILL)
    assert ("2.1.89" in text) and ("ADR-0041" in text), (
        "skills/pipeline-setup/SKILL.md must contain both '2.1.89' and "
        "'ADR-0041'"
    )


# ─────────────────────────────────────────────────────────────────────────────
# ADR file present + status
# ─────────────────────────────────────────────────────────────────────────────


def test_adr_file_exists_and_is_accepted():
    """The ADR file must exist at the expected path and carry an `Accepted`
    status line once the proposal lands.

    Pre-build: MAY fail if the ADR file is still in `Proposed` status. Passes
    once Eva marks it Accepted post-review.
    """
    assert ADR_FILE.exists(), (
        f"ADR file missing: {ADR_FILE}. Cal's ADR must be on disk for the "
        "pipeline to reference."
    )
    text = ADR_FILE.read_text()
    assert "Accepted" in text, (
        f"{ADR_FILE} does not contain 'Accepted' -- status line still reads "
        "something else (likely 'Proposed'). ADR-0041 must be marked Accepted "
        "before Colby builds against it."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Regression: pipeline-orchestration.md must not contain old classifier terms
# ─────────────────────────────────────────────────────────────────────────────


def test_pipeline_orchestration_no_classifier_score():
    """source/shared/rules/pipeline-orchestration.md must not contain the
    stale 'classifier score' framing removed by ADR-0041.

    Finding: F-6 regression (scout swarm confirmed already clean -- GREEN
    regression protection).
    """
    text = _read(PIPELINE_ORCHESTRATION_SOURCE)
    assert "classifier score" not in text, (
        "source/shared/rules/pipeline-orchestration.md must not contain "
        "'classifier score' -- this framing was superseded by ADR-0041's "
        "4-tier task-class model."
    )


def test_pipeline_orchestration_no_sonnet_classifier():
    """source/shared/rules/pipeline-orchestration.md must not contain the
    stale 'Sonnet (classifier)' role label removed by ADR-0041.

    Finding: F-6 regression (scout swarm confirmed already clean -- GREEN
    regression protection).
    """
    text = _read(PIPELINE_ORCHESTRATION_SOURCE)
    assert "Sonnet (classifier)" not in text, (
        "source/shared/rules/pipeline-orchestration.md must not contain "
        "'Sonnet (classifier)' -- this model role was removed by ADR-0041."
    )


def test_installed_orchestration_no_classifier_score():
    """Installed mirror .claude/rules/pipeline-orchestration.md must not
    contain the stale 'classifier score' framing.

    Finding: F-6 regression -- the installed mirror must track the source
    (GREEN regression protection for the installed copy).
    """
    text = _read(PIPELINE_ORCHESTRATION_INSTALLED)
    assert "classifier score" not in text, (
        ".claude/rules/pipeline-orchestration.md must not contain "
        "'classifier score' -- installed mirror must be free of the stale "
        "classifier framing superseded by ADR-0041."
    )
