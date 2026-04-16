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
# User guide -- effort mentioned
# ─────────────────────────────────────────────────────────────────────────────


def test_user_guide_mentions_effort():
    """docs/guide/user-guide.md must mention the `effort` concept somewhere
    (generous match -- any context).

    Pre-build: FAILS until Colby runs Step 8.
    """
    text = _read(USER_GUIDE)
    assert "effort" in text.lower(), (
        "docs/guide/user-guide.md does not mention 'effort'. ADR-0041 Step 8 "
        "updates user-guide.md line ~1021 to cite tier-based assignment."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline-setup SKILL.md -- Claude Code version check / effort mention
# ─────────────────────────────────────────────────────────────────────────────


def test_pipeline_setup_skill_carries_version_or_effort_note():
    """skills/pipeline-setup/SKILL.md must carry either the `2.1.89` version
    check or a reference to `effort` per ADR-0041 §Compatibility soft-warning.

    Pre-build: FAILS until Colby runs Step 7.
    """
    text = _read(PIPELINE_SETUP_SKILL)
    assert ("2.1.89" in text) or ("effort" in text.lower()), (
        "skills/pipeline-setup/SKILL.md carries neither '2.1.89' nor "
        "'effort'. ADR-0041 Step 7 adds a non-blocking Claude Code version "
        "check referencing both."
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
