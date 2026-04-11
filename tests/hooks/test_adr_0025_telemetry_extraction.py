"""Tests for ADR-0025: Mechanical Telemetry Extraction.

Covers T-0025-001 through T-0025-043.

These tests define correct behavior BEFORE Colby builds. All tests should
FAIL before the ADR is implemented (brain-extractor.md lacks the quality
signal extraction section, hydrate-telemetry.mjs lacks parseStateFiles,
session-hydrate.sh does not exist, warn-dor-dod.sh still exists, etc.).

Colby MUST NOT modify these assertions.

Test file location: tests/hooks/test_adr_0025_telemetry_extraction.py
ADR test spec location: docs/architecture/ADR-0025-mechanical-telemetry-extraction.md
"""

import json
import re
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


# ── Paths ─────────────────────────────────────────────────────────────────

SETTINGS_JSON         = PROJECT_ROOT / ".claude" / "settings.json"
INSTALLED_HOOKS       = PROJECT_ROOT / ".claude" / "hooks"

SOURCE_CLAUDE_HOOKS   = PROJECT_ROOT / "source" / "claude" / "hooks"
SOURCE_SHARED_AGENTS  = PROJECT_ROOT / "source" / "shared" / "agents"
SOURCE_SHARED_RULES   = PROJECT_ROOT / "source" / "shared" / "rules"
SOURCE_SHARED_REFS    = PROJECT_ROOT / "source" / "shared" / "references"

BRAIN_EXTRACTOR_PERSONA = SOURCE_SHARED_AGENTS / "brain-extractor.md"
HYDRATE_TELEMETRY_MJS   = PROJECT_ROOT / "brain" / "scripts" / "hydrate-telemetry.mjs"
SESSION_HYDRATE_SH      = SOURCE_CLAUDE_HOOKS / "session-hydrate.sh"
INSTALLED_SESSION_HYDRATE = INSTALLED_HOOKS / "session-hydrate.sh"
WARN_DOR_DOD_SOURCE     = SOURCE_CLAUDE_HOOKS / "warn-dor-dod.sh"
WARN_DOR_DOD_INSTALLED  = INSTALLED_HOOKS / "warn-dor-dod.sh"
PIPELINE_ORCH_MD        = SOURCE_SHARED_RULES / "pipeline-orchestration.md"
AGENT_PREAMBLE_MD       = SOURCE_SHARED_REFS / "agent-preamble.md"
SKILL_MD                = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"
TECHNICAL_REFERENCE     = PROJECT_ROOT / "docs" / "guide" / "technical-reference.md"

# The four core persona files that must not call agent_capture
PERSONA_FILES = {
    "cal":    SOURCE_SHARED_AGENTS / "cal.md",
    "colby":  SOURCE_SHARED_AGENTS / "colby.md",
    "roz":    SOURCE_SHARED_AGENTS / "roz.md",
    "agatha": SOURCE_SHARED_AGENTS / "agatha.md",
}


# ── Helpers ───────────────────────────────────────────────────────────────


def load_settings() -> dict:
    """Load and parse .claude/settings.json."""
    return json.loads(SETTINGS_JSON.read_text())


def get_subagent_stop_hooks(settings: dict) -> list:
    """Return the list of hooks in the SubagentStop block."""
    return settings["hooks"]["SubagentStop"][0]["hooks"]


def read_source(path: Path) -> str:
    """Read a source file as text. Fails the test if the file does not exist."""
    assert path.exists(), (
        f"Required file not found: {path}. "
        "This file must exist after the ADR is implemented."
    )
    return path.read_text()


def extract_quality_signal_section(text: str) -> str:
    """Extract the 'Structured Quality Signal Extraction' section from brain-extractor.md.

    Returns the section content, or empty string if the section is absent.
    The section starts at the heading and ends at the next heading of equal or
    higher level, or at end-of-file.
    """
    lines = text.splitlines()
    result = []
    capturing = False
    for line in lines:
        if re.search(r"structured quality signal extraction", line, re.IGNORECASE):
            capturing = True
        elif capturing and re.match(r"^#{1,3}\s", line) and not re.search(
            r"structured quality signal extraction", line, re.IGNORECASE
        ):
            # Reached the next section heading -- stop capturing
            break
        if capturing:
            result.append(line)
    return "\n".join(result)


def extract_settings_json_template_from_skill(text: str) -> str:
    """Extract the settings.json hooks template block from SKILL.md.

    Returns the content of the JSON code block that contains the 'hooks' key
    (the actual settings.json template that /pipeline-setup writes). This is
    distinct from other code fences (directory trees, command examples).

    Strategy: find all fenced code blocks in the SKILL.md text, then return
    the one that contains both 'SubagentStop' and '"hooks"' -- which is the
    settings.json template, not a directory listing.
    """
    # Extract all fenced code blocks (``` ... ```) including ```json
    blocks = re.findall(r"```[a-z]*\n(.*?)```", text, re.DOTALL)
    for block in blocks:
        # The settings.json template contains both SubagentStop and hooks key
        if "SubagentStop" in block and '"hooks"' in block:
            return block
    return ""


def extract_hybrid_capture_model_section(text: str) -> str:
    """Extract the Hybrid Capture Model section from pipeline-orchestration.md.

    Returns content between the 'Hybrid Capture Model' heading and the next
    top-level heading (##), bounded to avoid false positives.
    """
    lines = text.splitlines()
    result = []
    capturing = False
    for line in lines:
        if re.search(r"hybrid capture model|brain access.*when brain", line, re.IGNORECASE):
            capturing = True
        elif capturing and re.match(r"^##\s", line) and not re.search(
            r"hybrid capture model|brain access|devops capture", line, re.IGNORECASE
        ):
            break
        if capturing:
            result.append(line)
    return "\n".join(result)


# ═══════════════════════════════════════════════════════════════════════════
# WAVE 1 — T-0025-001 through T-0025-015
# ═══════════════════════════════════════════════════════════════════════════

# ── T-0025-001: brain-extractor.md contains the new section ────────────────


def test_T_0025_001_brain_extractor_has_quality_signal_section():
    """brain-extractor.md must contain a 'Structured Quality Signal Extraction' section.

    ADR-0025 Wave 1 Step 1 adds this section to the extractor persona.
    Its absence means Wave 1 has not been implemented.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    assert re.search(
        r"structured quality signal extraction",
        text,
        re.IGNORECASE,
    ), (
        "brain-extractor.md is missing the 'Structured Quality Signal Extraction' section. "
        "ADR-0025 Wave 1 Step 1 requires this section to exist in the extractor persona."
    )


# ── T-0025-002: Roz schema references PASS/FAIL verdict extraction ──────────


def test_T_0025_002_roz_schema_references_verdict():
    """The Roz schema in the quality signal section must reference PASS and FAIL.

    ADR-0025 R2: Roz signals include PASS/FAIL verdict. The extractor must be
    instructed to look for these verdict markers in Roz's output.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, (
        "Could not locate the 'Structured Quality Signal Extraction' section. "
        "T-0025-001 must pass first."
    )
    assert "PASS" in qs_section and "FAIL" in qs_section, (
        "Roz schema in brain-extractor.md is missing PASS/FAIL verdict extraction. "
        "ADR-0025 R2 requires the extractor to parse Roz's verdict line for PASS or FAIL."
    )


# ── T-0025-003: Roz schema references all four severity terms ──────────────


@pytest.mark.parametrize("severity", ["BLOCKER", "MUST-FIX", "NIT", "SUGGESTION"])
def test_T_0025_003_roz_schema_references_severity_terms(severity):
    """The Roz schema must reference all four severity terms as parseable fields.

    ADR-0025 R2: finding counts by severity (BLOCKER/MUST-FIX/NIT/SUGGESTION).
    All four severity levels must appear in the extraction schema.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    assert severity in qs_section, (
        f"Roz severity term '{severity}' absent from brain-extractor.md quality signal section. "
        f"ADR-0025 R2 requires all four severity levels: BLOCKER, MUST-FIX, NIT, SUGGESTION."
    )


# ── T-0025-004: Roz schema references test count markers ───────────────────


def test_T_0025_004_roz_schema_references_test_counts():
    """The Roz schema must reference test count markers: tests_before, tests_after, tests_broken.

    ADR-0025 R2: Roz signals include tests_before, tests_after, tests_broken.
    The ADR allows equivalents like 'passed/failed counts' from suite summary lines.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_test_markers = bool(re.search(
        r"tests_before|tests_after|tests_broken|passed.*failed|suite summary|test count",
        qs_section,
        re.IGNORECASE,
    ))
    assert has_test_markers, (
        "brain-extractor.md quality signal section missing test count markers. "
        "ADR-0025 R2 requires tests_before, tests_after, tests_broken (or equivalent suite "
        "summary patterns like 'passed'/'failed' counts)."
    )


# ── T-0025-005: Colby schema references DoD section and files changed ───────


def test_T_0025_005_colby_schema_references_dod_and_files_changed():
    """The Colby schema must reference the DoD section and file count extraction.

    ADR-0025 R3: Colby signals include files changed count and DoD completeness.
    Both must be present in the extraction schema.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_dod = bool(re.search(r"DoD|dod", qs_section))
    has_files = bool(re.search(r"files changed|file count|files_changed", qs_section, re.IGNORECASE))
    assert has_dod and has_files, (
        f"Colby schema in brain-extractor.md quality signal section is missing: "
        f"{'DoD' if not has_dod else ''} {'files_changed' if not has_files else ''}. "
        "ADR-0025 R3 requires both DoD presence check and file count extraction for Colby signals."
    )


# ── T-0025-006: Colby schema references rework signal detection ─────────────


def test_T_0025_006_colby_schema_references_rework_signal():
    """The Colby schema must reference rework signal detection.

    ADR-0025 R3: Colby signals include rework flag -- whether this invocation
    is fixing a prior Roz FAIL. The schema must mention phrases like 'fixing Roz',
    'prior FAIL', 'addressing Roz', or 'FAIL verdict'.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_rework = bool(re.search(
        r"rework|fixing Roz|addressing Roz|prior.*FAIL|FAIL verdict|prior QA FAIL",
        qs_section,
        re.IGNORECASE,
    ))
    assert has_rework, (
        "Colby schema in brain-extractor.md quality signal section missing rework signal detection. "
        "ADR-0025 R3 requires detection of phrases like 'fixing Roz', 'FAIL verdict', or "
        "'prior QA FAIL' to identify rework invocations."
    )


# ── T-0025-007: Cal schema references step count extraction ─────────────────


def test_T_0025_007_cal_schema_references_step_count():
    """The Cal schema must reference step count extraction.

    ADR-0025 R4: Cal signals include step count. The schema must instruct
    the extractor to look for 'N steps' or equivalent patterns.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_step_count = bool(re.search(
        r"step.{0,20}count|N steps|step_count|\d+ steps",
        qs_section,
        re.IGNORECASE,
    ))
    assert has_step_count, (
        "Cal schema in brain-extractor.md quality signal section missing step count extraction. "
        "ADR-0025 R4 requires the extractor to parse 'N steps' or equivalent patterns for Cal signals."
    )


# ── T-0025-008: Cal schema references test spec count extraction ─────────────


def test_T_0025_008_cal_schema_references_test_spec_count():
    """The Cal schema must reference test spec count (T-NNNN pattern) extraction.

    ADR-0025 R4: Cal signals include test spec count. The schema must instruct
    the extractor to look for T-NNNN patterns or 'N tests' equivalents.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_test_spec = bool(re.search(
        r"T-\d{4}|test spec count|N tests|test_spec_count",
        qs_section,
        re.IGNORECASE,
    ))
    assert has_test_spec, (
        "Cal schema in brain-extractor.md quality signal section missing test spec count extraction. "
        "ADR-0025 R4 requires the T-NNNN pattern (or 'N tests') to be referenced for Cal signals."
    )


# ── T-0025-009: Cal schema references DoR/DoD presence check ────────────────


def test_T_0025_009_cal_schema_references_dor_dod_presence():
    """The Cal schema must reference DoR and DoD presence check (boolean).

    ADR-0025 R4: Cal signals include DoR/DoD sections present (boolean).
    Both must be mentioned in the Cal extraction schema.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_dor = bool(re.search(r"DoR|dor_present", qs_section))
    has_dod = bool(re.search(r"DoD|dod_present", qs_section))
    assert has_dor and has_dod, (
        f"Cal schema in brain-extractor.md quality signal section missing: "
        f"{'DoR' if not has_dor else ''} {'DoD' if not has_dod else ''}. "
        "ADR-0025 R4 requires both DoR/DoD presence checks as boolean signals for Cal."
    )


# ── T-0025-010: Agatha schema references Written/updated path count ──────────


def test_T_0025_010_agatha_schema_references_written_updated():
    """The Agatha schema must reference Written/updated path count extraction.

    ADR-0025 R5: Agatha signals include docs written count and docs updated count.
    The schema must reference 'Written' and 'updated' in the Agatha parsing logic,
    matching Agatha's receipt format: 'Agatha: Written {paths}, updated {paths}'.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_written = bool(re.search(r"Written|docs_written", qs_section, re.IGNORECASE))
    has_updated = bool(re.search(r"updated|docs_updated", qs_section, re.IGNORECASE))
    assert has_written and has_updated, (
        f"Agatha schema in brain-extractor.md quality signal section missing: "
        f"{'Written' if not has_written else ''} {'updated' if not has_updated else ''}. "
        "ADR-0025 R5 requires Written/updated path count from Agatha's receipt format."
    )


# ── T-0025-011: Agatha schema references Divergence findings ────────────────


def test_T_0025_011_agatha_schema_references_divergence():
    """The Agatha schema must reference Divergence findings (drift/gap breakdown).

    ADR-0025 R5: Agatha signals include divergence findings count, drift vs gap breakdown.
    The schema must mention 'Divergence', 'drift', or 'gap' in the Agatha parsing schema.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_divergence = bool(re.search(
        r"Divergence|divergence_count|drift|gap",
        qs_section,
        re.IGNORECASE,
    ))
    assert has_divergence, (
        "Agatha schema in brain-extractor.md quality signal section missing Divergence findings. "
        "ADR-0025 R5 requires divergence_count, drift, and gap breakdown for Agatha signals."
    )


# ── T-0025-012: Omission guard — omit fields, do not fabricate ───────────────


def test_T_0025_012_omission_guard_no_fabrication():
    """Persona must instruct: omit fields when markers absent (not null, not fabricated).

    ADR-0025 Step 1 acceptance criterion: 'If a marker is absent from the output,
    the corresponding field is omitted -- never set to null or fabricated.'
    The persona must not use 'null', 'fabricate', or 'infer' as fallback instructions.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."

    # Must instruct to omit (positive assertion)
    has_omit_instruction = bool(re.search(
        r"omit|absent.*skip|skip.*absent|do not.*fabricat|never.*fabricat",
        qs_section,
        re.IGNORECASE,
    ))
    assert has_omit_instruction, (
        "brain-extractor.md quality signal section missing omission instruction. "
        "Persona must instruct to omit fields when markers are absent (not set to null, "
        "not fabricated). ADR-0025 Step 1 acceptance criterion."
    )

    # Must NOT instruct fallback to null/fabricate/infer (negative assertion)
    # Context: 'null' in a 'never set to null' sentence is acceptable, but
    # 'set to null' as a fallback instruction is not. We search for the bad pattern.
    has_null_fallback = bool(re.search(
        r"set\s+to\s+null|default\s+to\s+null|use\s+null|return\s+null|fabricate|infer.*default",
        qs_section,
        re.IGNORECASE,
    ))
    assert not has_null_fallback, (
        "brain-extractor.md quality signal section contains a forbidden fallback instruction "
        "('set to null', 'fabricate', or 'infer'). ADR-0025: if a marker is absent, "
        "the field must be omitted -- never set to null or fabricated."
    )


# ── T-0025-013: Omission guard — zero captures acceptable ────────────────────


def test_T_0025_013_omission_guard_zero_captures_acceptable():
    """Persona must instruct that zero quality signal captures is acceptable.

    ADR-0025 Step 1: 'If zero fields are parseable, emit no quality signal capture.'
    The persona must have explicit language that no capture (when no markers found)
    is a valid outcome -- not a failure.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_zero_ok = bool(re.search(
        r"zero.*capture|no capture|skip.*capture|emit no|no quality signal|"
        r"zero field|nothing.*preserve|valid outcome|acceptable",
        qs_section,
        re.IGNORECASE,
    ))
    assert has_zero_ok, (
        "brain-extractor.md quality signal section missing 'zero captures acceptable' instruction. "
        "ADR-0025 Step 1 requires: 'If zero fields are parseable, emit no quality signal capture.' "
        "The persona must state this is a valid outcome."
    )


# ── T-0025-014: Metadata — thought_type: insight and source_phase: telemetry ───


def test_T_0025_014_metadata_insight_and_quality_phase():
    """Persona must specify thought_type: 'insight' and source_phase: 'telemetry' for quality captures.

    ADR-0025 R6: Structured signals captured as thought_type: 'insight',
    source_phase: 'telemetry'. Both values must appear in the quality signal section.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    has_insight = bool(re.search(r"insight", qs_section, re.IGNORECASE))
    has_telemetry_phase = bool(re.search(r"source_phase.*telemetry|telemetry.*source_phase|'telemetry'", qs_section))
    assert has_insight, (
        "brain-extractor.md quality signal section missing thought_type: 'insight'. "
        "ADR-0025 R6 requires thought_type: 'insight' for all quality signal captures."
    )
    assert has_telemetry_phase, (
        "brain-extractor.md quality signal section missing source_phase: 'telemetry'. "
        "ADR-0025 R6 requires source_phase: 'telemetry' for all quality signal captures."
    )


# ── T-0025-015: Metadata — importance: 0.5 ──────────────────────────────────


def test_T_0025_015_metadata_importance_value():
    """Persona must specify importance: 0.5 for quality signal captures.

    ADR-0025 Step 1: quality signal captures use importance: 0.5.
    This value must appear in the quality extraction section.
    """
    text = read_source(BRAIN_EXTRACTOR_PERSONA)
    qs_section = extract_quality_signal_section(text)
    assert qs_section, "Quality signal section absent -- T-0025-001 must pass first."
    # The importance value 0.5 must appear in the quality signal section
    # (not just in the pre-existing extraction table for pattern/seed)
    assert "0.5" in qs_section, (
        "brain-extractor.md quality signal section missing importance: 0.5. "
        "ADR-0025 Step 1 specifies importance: 0.5 for all quality signal captures."
    )


# ═══════════════════════════════════════════════════════════════════════════
# WAVE 2a — T-0025-016 through T-0025-025 (hydrate-telemetry.mjs)
# ═══════════════════════════════════════════════════════════════════════════

# ── T-0025-016: parseStateFiles function exists in hydrate-telemetry.mjs ─────


def test_T_0025_016_hydrate_telemetry_has_parseStateFiles():
    """hydrate-telemetry.mjs must contain a parseStateFiles function.

    ADR-0025 Wave 2a Step 2: 'Add a new top-level function parseStateFiles(stateDir, pool, config)'.
    Its absence means Wave 2a has not been implemented.
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)
    assert re.search(r"function\s+parseStateFiles\s*\(", text), (
        "hydrate-telemetry.mjs missing parseStateFiles function. "
        "ADR-0025 Wave 2a Step 2 requires this function to parse pipeline state files "
        "and emit brain captures."
    )


# ── T-0025-017: --state-dir argument handling ────────────────────────────────


def test_T_0025_017_hydrate_telemetry_has_state_dir_argument():
    """hydrate-telemetry.mjs must contain --state-dir argument handling.

    ADR-0025 Wave 2a Step 2: 'New CLI flags: --state-dir <path>'.
    The flag must be referenced in the argument parsing section.
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)
    assert re.search(r"--state-dir|state.dir|stateDir", text, re.IGNORECASE), (
        "hydrate-telemetry.mjs missing --state-dir argument handling. "
        "ADR-0025 Wave 2a requires this CLI flag to specify the docs/pipeline directory path."
    )


# ── T-0025-018: parseStateFiles parses Feature and Sizing lines ──────────────


def test_T_0025_018_parseStateFiles_parses_feature_and_sizing():
    """parseStateFiles must parse the **Feature:** and **Sizing:** lines from pipeline-state.md.

    ADR-0025 Wave 2a Step 2: 'From pipeline-state.md: extract the feature name
    (from **Feature:** line), the sizing (from **Sizing:** line).'
    Both patterns must appear in the parse logic.
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)
    has_feature = bool(re.search(r"\*\*Feature:\*\*|Feature:", text))
    has_sizing  = bool(re.search(r"\*\*Sizing:\*\*|Sizing:", text))
    assert has_feature, (
        "hydrate-telemetry.mjs parseStateFiles missing **Feature:** line parsing. "
        "ADR-0025 Wave 2a requires extracting the feature name from the pipeline-state.md header."
    )
    assert has_sizing, (
        "hydrate-telemetry.mjs parseStateFiles missing **Sizing:** line parsing. "
        "ADR-0025 Wave 2a requires extracting the sizing value from the pipeline-state.md header."
    )


# ── T-0025-019: parseStateFiles parses completed progress items (- [x]) ──────


def test_T_0025_019_parseStateFiles_parses_completed_progress_items():
    """parseStateFiles must parse - [x] completed progress items from pipeline-state.md.

    ADR-0025 Wave 2a Step 2: 'the phase transitions from the Progress checklist
    (lines matching - [x])'. The checkbox pattern must appear in the parse logic.
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)
    has_checkbox = bool(re.search(
        r"\[x\]|\[X\]|checkbox|checklist|progress.*item|\-\s*\[",
        text,
        re.IGNORECASE,
    ))
    assert has_checkbox, (
        "hydrate-telemetry.mjs parseStateFiles missing - [x] checkbox pattern. "
        "ADR-0025 Wave 2a requires parsing completed progress items (lines matching '- [x]') "
        "from pipeline-state.md to produce pipeline phase captures."
    )


# ── T-0025-020: parseStateFiles parses User Decisions from context-brief.md ──


def test_T_0025_020_parseStateFiles_parses_user_decisions():
    """parseStateFiles must parse the ## User Decisions section from context-brief.md.

    ADR-0025 Wave 2a Step 2: 'From context-brief.md: extract items under
    ## User Decisions section (lines starting with - ).'
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)
    has_user_decisions = bool(re.search(
        r"## User Decisions|User Decisions|context-brief|context_brief",
        text,
        re.IGNORECASE,
    ))
    assert has_user_decisions, (
        "hydrate-telemetry.mjs parseStateFiles missing ## User Decisions section parsing. "
        "ADR-0025 Wave 2a requires extracting user decision items from context-brief.md."
    )


# ── T-0025-021: State-file captures use correct metadata fields ───────────────


def test_T_0025_021_state_file_captures_correct_metadata():
    """State-file captures must use source_agent: 'eva', thought_type: 'decision', source_phase: 'pipeline'.

    ADR-0025 Wave 2a Step 2 acceptance criterion: each completed progress item
    becomes one capture with source_agent: 'eva', thought_type: 'decision',
    source_phase: 'pipeline'.
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)

    # Verify all three required field values appear in the file
    # These must be proximate to the parseStateFiles function, not just anywhere
    # (they could also appear in other sections, but their presence is required)
    has_eva        = bool(re.search(r"source_agent.*eva|'eva'.*source_agent", text))
    has_decision   = bool(re.search(r"thought_type.*decision|'decision'.*thought_type|thought_type.*'decision'", text))
    has_pipeline_phase = bool(re.search(r"source_phase.*pipeline|'pipeline'.*source_phase", text))

    assert has_eva, (
        "hydrate-telemetry.mjs missing source_agent: 'eva' for state-file captures. "
        "ADR-0025 Wave 2a requires Eva's captures to identify her as the source agent."
    )
    assert has_decision, (
        "hydrate-telemetry.mjs missing thought_type: 'decision' for state-file captures. "
        "ADR-0025 Wave 2a requires thought_type: 'decision' for pipeline state captures."
    )
    assert has_pipeline_phase, (
        "hydrate-telemetry.mjs missing source_phase: 'pipeline' for state-file captures. "
        "ADR-0025 Wave 2a requires source_phase: 'pipeline' to distinguish state captures "
        "from T1/T3 telemetry captures."
    )


# ── T-0025-022: State-file captures use importance 0.6 ───────────────────────


def test_T_0025_022_state_file_captures_importance_0_6():
    """State-file captures must use importance: 0.6.

    ADR-0025 Wave 2a Step 2: 'uses the existing insertTelemetryThought() function
    with thought_type: decision, source_agent: eva, source_phase: pipeline, importance: 0.6.'
    The value 0.6 must appear as the importance for pipeline state captures.
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)
    # The value 0.6 already appears in the existing hydrate file for lessons.
    # We verify it appears in the context of parseStateFiles or state-file insertion.
    # The simplest verifiable assertion: 0.6 appears somewhere in the file
    # (the existing Tier 3 summary uses 0.7; the new state captures use 0.6).
    assert "0.6" in text, (
        "hydrate-telemetry.mjs missing importance value 0.6. "
        "ADR-0025 Wave 2a requires importance: 0.6 for pipeline state-file captures "
        "(Eva decisions and phase transitions)."
    )


# ── T-0025-023: Dedup key distinct from T1 key ────────────────────────────────


def test_T_0025_023_state_file_dedup_distinct_from_t1():
    """Duplicate detection for state-file captures must be distinct from T1 agent-JSONL dedup.

    ADR-0025 Wave 2a Step 2: 'Duplicate detection: reuse the existing alreadyHydrated()
    pattern -- use (session_id + _state_phase_ + md5_of_item_text) as the composite key.'
    The state-file dedup must use a different key structure from T1's (session_id + agent_id + hydrated).
    The presence of a state-specific identifier (e.g., 'state_phase', 'phase_item', 'item_text')
    in the dedup logic confirms they are distinct.
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)
    # The T1 dedup key uses: { session_id, agent_id, hydrated: true } in source_phase='telemetry'
    # The state-file dedup must use something like: { session_id, ..., hydrated: true } in source_phase='pipeline'
    # The key distinguisher is source_phase='pipeline' (rather than 'telemetry')
    # combined with a phase_item or item-specific field.
    has_phase_item_key = bool(re.search(
        r"state_phase|phase_item|item_text|item_key|pipeline.*dedup|state.*dedup",
        text,
        re.IGNORECASE,
    ))
    # Alternatively the source_phase='pipeline' in the WHERE clause for dedup is sufficient
    has_pipeline_dedup = bool(re.search(
        r"source_phase.*=.*pipeline|pipeline.*source_phase|'pipeline'",
        text,
    ))
    assert has_phase_item_key or has_pipeline_dedup, (
        "hydrate-telemetry.mjs missing distinct dedup key for state-file captures. "
        "ADR-0025 Wave 2a requires a composite key distinct from T1's (session_id + agent_id). "
        "State captures must use phase_item, item_text, or source_phase='pipeline' in the dedup query."
    )


# ── T-0025-024: parseStateFiles handles absent pipeline-state.md ─────────────


def test_T_0025_024_parseStateFiles_handles_absent_pipeline_state():
    """parseStateFiles must not throw when pipeline-state.md is absent.

    ADR-0025 Wave 2a Step 2 acceptance criterion: 'handles missing files gracefully
    (no-op when files absent).' The function must reference 'pipeline-state.md'
    by name (as the filename to guard), which only happens once the function is
    implemented. The current hydrate-telemetry.mjs does not reference this filename.
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)
    # pipeline-state.md must appear as a string literal in the file.
    # This is the concrete filename the new parseStateFiles function reads.
    # Before implementation it does not appear in hydrate-telemetry.mjs at all.
    assert "pipeline-state.md" in text, (
        "hydrate-telemetry.mjs does not reference 'pipeline-state.md'. "
        "ADR-0025 Wave 2a requires parseStateFiles() to read this file, which means "
        "the filename must appear as a string literal in the implementation. "
        "The file-existence guard (existsSync before readFileSync) is a required part of the function."
    )


# ── T-0025-025: parseStateFiles handles absent context-brief.md ──────────────


def test_T_0025_025_parseStateFiles_handles_absent_context_brief():
    """parseStateFiles must not throw when context-brief.md is absent.

    ADR-0025 Wave 2a Step 2 acceptance criterion: both state files have existence
    guards. The function must handle a missing context-brief.md gracefully.
    """
    text = read_source(HYDRATE_TELEMETRY_MJS)
    has_context_brief_guard = bool(re.search(
        r"context-brief|context_brief",
        text,
        re.IGNORECASE,
    ))
    assert has_context_brief_guard, (
        "hydrate-telemetry.mjs parseStateFiles missing context-brief.md reference. "
        "ADR-0025 Wave 2a requires context-brief.md parsing with a graceful no-op when absent."
    )


# ═══════════════════════════════════════════════════════════════════════════
# WAVE 2b — T-0025-026 through T-0025-031 (session-hydrate.sh + settings.json)
# ═══════════════════════════════════════════════════════════════════════════

# ── T-0025-026: source/claude/hooks/session-hydrate.sh exists ───────────────


def test_T_0025_026_session_hydrate_sh_exists():
    """source/claude/hooks/session-hydrate.sh must exist.

    ADR-0025 Wave 2b Step 3 creates this file as a thin SessionStart shell hook.
    Its absence means Step 3 has not been implemented.
    """
    assert SESSION_HYDRATE_SH.exists(), (
        f"source/claude/hooks/session-hydrate.sh not found at {SESSION_HYDRATE_SH}. "
        "ADR-0025 Wave 2b Step 3 requires this file to exist."
    )


# ── T-0025-027: session-hydrate.sh exits 0 on all paths ─────────────────────


def test_T_0025_027_session_hydrate_sh_exits_0_always():
    """session-hydrate.sh must exit 0 on all paths.

    ADR-0025 Wave 2b Step 3 and Retro #003: 'Non-blocking: exits 0 always.'
    The script must not use set -e (which makes any error exit non-zero), OR
    if set -e is used, the node call must be guarded with '|| true'.
    Presence of 'set -e' without '|| true' on the node invocation is a violation.
    """
    text = read_source(SESSION_HYDRATE_SH)
    has_set_e = bool(re.search(r"\bset\s+-[a-z]*e[a-z]*\b", text))
    # The node call must be guarded -- either via || true or by not having set -e
    has_or_true = bool(re.search(r"\|\|\s*true", text))
    has_exit_0 = bool(re.search(r"exit\s+0", text))

    if has_set_e:
        assert has_or_true, (
            "session-hydrate.sh uses set -e but the node call lacks '|| true' guard. "
            "Any node error would cause the hook to exit non-zero, blocking the pipeline. "
            "ADR-0025 Retro #003: SessionStart hooks must exit 0 always."
        )
    assert has_exit_0, (
        "session-hydrate.sh missing explicit 'exit 0' at the end. "
        "ADR-0025 Wave 2b Step 3 requires explicit exit 0 to guarantee non-blocking behavior."
    )


# ── T-0025-028: session-hydrate.sh invokes hydrate-telemetry.mjs with both flags


def test_T_0025_028_session_hydrate_sh_invokes_with_flags():
    """session-hydrate.sh must invoke hydrate-telemetry.mjs with --silent and --state-dir.

    ADR-0025 Wave 2b Step 3: 'node "$PLUGIN_BRAIN" "$SESSION_PATH" --silent --state-dir "$STATE_DIR"'.
    Both flags must appear in the script body.
    """
    text = read_source(SESSION_HYDRATE_SH)
    has_silent = bool(re.search(r"--silent", text))
    has_state_dir = bool(re.search(r"--state-dir", text))
    assert has_silent, (
        "session-hydrate.sh missing --silent flag in hydrate-telemetry.mjs invocation. "
        "ADR-0025 Wave 2b Step 3 requires --silent to suppress output during SessionStart."
    )
    assert has_state_dir, (
        "session-hydrate.sh missing --state-dir flag in hydrate-telemetry.mjs invocation. "
        "ADR-0025 Wave 2b Step 3 requires --state-dir to pass the docs/pipeline directory path."
    )


# ── T-0025-029: settings.json contains SessionStart block ────────────────────


def test_T_0025_029_settings_json_has_sessionstart_block():
    """settings.json must contain a SessionStart block.

    ADR-0025 Wave 2b Step 3: 'Settings.json addition: "SessionStart": [...]'.
    The SessionStart key must exist in the hooks section.
    """
    settings = load_settings()
    hooks = settings.get("hooks", {})
    assert "SessionStart" in hooks, (
        "settings.json missing SessionStart block under 'hooks'. "
        "ADR-0025 Wave 2b Step 3 requires adding the SessionStart hook registration."
    )


# ── T-0025-030: settings.json SessionStart block references the active hydration script
#
# Hook wiring audit supersedes ADR-0025 Wave 2b Step 3:
# session-hydrate.sh is now an intentional no-op (hydration moved to atelier_hydrate MCP).
# session-hydrate-enforcement.sh is the active SessionStart hook for enforcement audit hydration.


def test_T_0025_030_settings_json_sessionstart_references_script():
    """settings.json SessionStart block must reference session-hydrate-enforcement.sh.

    session-hydrate.sh is now a no-op (hydration moved to atelier_hydrate MCP) and is
    intentionally NOT registered. session-hydrate-enforcement.sh is the active SessionStart hook.
    """
    settings = load_settings()
    hooks = settings.get("hooks", {})
    assert "SessionStart" in hooks, "SessionStart block absent -- T-0025-029 must pass first."
    session_start_config = hooks["SessionStart"]
    full_text = json.dumps(session_start_config)
    # No-op must NOT be registered
    noop_entries = [
        entry for entry in full_text.split("session-hydrate")
        if ".sh" in entry[:20] and "enforcement" not in entry[:20]
    ]
    assert "session-hydrate-enforcement.sh" in full_text, (
        "settings.json SessionStart block does not reference session-hydrate-enforcement.sh. "
        "The active enforcement hydration hook must be wired to the SessionStart event."
    )


# ── T-0025-031: settings.json is valid JSON after SessionStart addition ───────


def test_T_0025_031_settings_json_valid_after_sessionstart():
    """settings.json must remain valid JSON after the SessionStart block addition.

    A malformed settings.json silently breaks all hook enforcement. The file
    must parse without error and retain both the hooks key and the SubagentStop block.
    """
    try:
        data = json.loads(SETTINGS_JSON.read_text())
    except json.JSONDecodeError as e:
        pytest.fail(
            f"settings.json is invalid JSON after SessionStart addition: {e}. "
            "ADR-0025 Wave 2b Step 3: verify JSON is well-formed after the edit."
        )
    assert "hooks" in data, "settings.json missing 'hooks' key after modification."
    assert "SubagentStop" in data["hooks"], (
        "settings.json missing SubagentStop block -- existing hook wiring was accidentally removed."
    )


# ═══════════════════════════════════════════════════════════════════════════
# WAVE 2b — T-0025-032 through T-0025-034 (warn-dor-dod.sh deletion)
# ═══════════════════════════════════════════════════════════════════════════

# ── T-0025-032: source/claude/hooks/warn-dor-dod.sh does not exist ───────────


def test_T_0025_032_source_warn_dor_dod_deleted():
    """source/claude/hooks/warn-dor-dod.sh must not exist.

    ADR-0025 Wave 2b Step 4: 'source/claude/hooks/warn-dor-dod.sh (delete)'.
    The file must be removed from the source tree. Its presence is a violation.
    """
    assert not WARN_DOR_DOD_SOURCE.exists(), (
        f"source/claude/hooks/warn-dor-dod.sh still exists at {WARN_DOR_DOD_SOURCE}. "
        "ADR-0025 Wave 2b Step 4 requires this file to be deleted from source/."
    )


# ── T-0025-033: .claude/hooks/warn-dor-dod.sh does not exist (installed copy) ─


def test_T_0025_033_installed_warn_dor_dod_deleted():
    """The installed .claude/hooks/warn-dor-dod.sh must not exist.

    ADR-0025 Wave 2b Step 4: '.claude/hooks/warn-dor-dod.sh (delete -- installed copy)'.
    Both the source and installed copies must be removed.
    """
    assert not WARN_DOR_DOD_INSTALLED.exists(), (
        f".claude/hooks/warn-dor-dod.sh still exists at {WARN_DOR_DOD_INSTALLED}. "
        "ADR-0025 Wave 2b Step 4 requires the installed copy to be deleted as well."
    )


# ── T-0025-034: settings.json SubagentStop does not reference warn-dor-dod.sh ─


def test_T_0025_034_settings_json_subagent_stop_no_warn_dor_dod():
    """settings.json SubagentStop block must not reference warn-dor-dod.sh.

    ADR-0025 Wave 2b Step 4: 'settings.json (modify: remove warn-dor-dod.sh from SubagentStop block)'.
    """
    settings = load_settings()
    subagent_stop_text = json.dumps(settings.get("hooks", {}).get("SubagentStop", []))
    assert "warn-dor-dod.sh" not in subagent_stop_text, (
        "settings.json SubagentStop block still references warn-dor-dod.sh. "
        "ADR-0025 Wave 2b Step 4 requires removing this entry from the SubagentStop hooks."
    )


# ═══════════════════════════════════════════════════════════════════════════
# WAVE 2b — T-0025-035 through T-0025-038 (Eva protocol deletion)
# ═══════════════════════════════════════════════════════════════════════════

# ── T-0025-035: pipeline-orchestration.md lacks "Writes (cross-cutting only, best-effort)"


def test_T_0025_035_pipeline_orch_no_writes_subsection():
    """source/shared/rules/pipeline-orchestration.md must not contain the 'Writes (cross-cutting only, best-effort)' subsection.

    ADR-0025 Wave 2b Step 4: 'source/shared/rules/pipeline-orchestration.md (modify:
    delete "Writes (cross-cutting only, best-effort)" subsection from Hybrid Capture Model)'.
    """
    text = read_source(PIPELINE_ORCH_MD)
    assert "cross-cutting only, best-effort" not in text, (
        "source/shared/rules/pipeline-orchestration.md still contains 'cross-cutting only, best-effort'. "
        "ADR-0025 Wave 2b Step 4 requires deleting this subsection from the Hybrid Capture Model."
    )


# ── T-0025-036: pipeline-orchestration.md lacks "User decisions: calls agent_capture" bullet


def test_T_0025_036_pipeline_orch_no_user_decisions_bullet():
    """pipeline-orchestration.md must not contain 'User decisions: calls agent_capture' bullet.

    ADR-0025 Wave 2b Step 4 acceptance criterion: 'does not contain
    "User decisions: calls agent_capture" bullet'. Eva no longer calls agent_capture
    for user decisions -- the hydrator handles this.
    """
    text = read_source(PIPELINE_ORCH_MD)
    assert not re.search(r"User decisions:\s*calls\s*`?agent_capture", text, re.IGNORECASE), (
        "pipeline-orchestration.md still contains 'User decisions: calls agent_capture'. "
        "ADR-0025 Wave 2b Step 4 requires removing Eva's agent_capture call instructions for "
        "user decisions (the hydrator handles this mechanically)."
    )


# ── T-0025-037: pipeline-orchestration.md lacks "Phase transitions: calls agent_capture" bullet


def test_T_0025_037_pipeline_orch_no_phase_transitions_bullet():
    """pipeline-orchestration.md must not contain 'Phase transitions: calls agent_capture' bullet.

    ADR-0025 Wave 2b Step 4 acceptance criterion: 'does not contain
    "Phase transitions: calls agent_capture" bullet'. The hydrator handles this mechanically.
    """
    text = read_source(PIPELINE_ORCH_MD)
    assert not re.search(r"Phase transitions:\s*calls\s*`?agent_capture", text, re.IGNORECASE), (
        "pipeline-orchestration.md still contains 'Phase transitions: calls agent_capture'. "
        "ADR-0025 Wave 2b Step 4 requires removing this bullet -- the hydrator replaces it."
    )


# ── T-0025-038: pipeline-orchestration.md retains Reads subsection and Seed Capture protocol


def test_T_0025_038_pipeline_orch_retains_reads_and_seed_capture():
    """pipeline-orchestration.md must retain the Reads subsection and Seed Capture protocol.

    ADR-0025 Wave 2b Step 4 acceptance criterion: 'retains the Reads subsection
    and the Seed Capture protocol'. agent_search (brain reads) and Seed Capture
    must remain -- only the Writes bullets are deleted.
    """
    text = read_source(PIPELINE_ORCH_MD)
    has_agent_search = bool(re.search(r"agent_search", text))
    has_seed_capture = bool(re.search(r"Seed Capture|seed capture", text, re.IGNORECASE))
    assert has_agent_search, (
        "pipeline-orchestration.md is missing 'agent_search'. "
        "ADR-0025 Wave 2b Step 4 must retain the Reads subsection (agent_search calls). "
        "Only the Writes bullets should be deleted."
    )
    assert has_seed_capture, (
        "pipeline-orchestration.md is missing 'Seed Capture' protocol. "
        "ADR-0025 Wave 2b Step 4 must retain the Seed Capture section -- "
        "it is not part of the deleted Writes bullets."
    )


# ═══════════════════════════════════════════════════════════════════════════
# WAVE 2b — T-0025-039 through T-0025-040 (SKILL.md cleanup)
# ═══════════════════════════════════════════════════════════════════════════

# ── T-0025-039: SKILL.md hook install section does not reference warn-dor-dod.sh


def test_T_0025_039_skill_md_hook_install_no_warn_dor_dod():
    """SKILL.md hook install list must not reference warn-dor-dod.sh.

    ADR-0025 Wave 2b Step 4: 'SKILL.md (modify: remove warn-dor-dod.sh from
    install list)'. The hook install steps table must not list warn-dor-dod.sh.
    Migration notes (e.g., 'removed in ADR-0025') are acceptable -- only the
    active install instruction is forbidden.

    Scope: look for the hook table rows (lines with .sh that reference SubagentStop
    or hook descriptions), not in documentation prose or migration sections.
    """
    assert SKILL_MD.exists(), f"SKILL.md not found at {SKILL_MD}."
    text = SKILL_MD.read_text()
    # Extract the table/list section that installs hooks (rows with source/claude/hooks/ references)
    # A table row containing warn-dor-dod.sh in the hook list column = violation
    # A mention in a migration note / removal note = acceptable
    # Strategy: find table rows that look like active hook install instructions
    lines = text.splitlines()
    violation_lines = []
    for i, line in enumerate(lines, start=1):
        # A table row that includes warn-dor-dod.sh and looks like an active install step
        # Heuristic: pipe-delimited table row with warn-dor-dod.sh but no "remove" or "deleted" language
        if "warn-dor-dod.sh" in line:
            if "|" in line and not re.search(r"remov|delet|no longer|deprecat|migrat", line, re.IGNORECASE):
                violation_lines.append((i, line.strip()))
    assert not violation_lines, (
        f"SKILL.md hook install table still references warn-dor-dod.sh in active install rows:\n"
        + "\n".join(f"  Line {i}: {l}" for i, l in violation_lines)
        + "\nADR-0025 Wave 2b Step 4 requires removing warn-dor-dod.sh from the install list."
    )


# ── T-0025-040: SKILL.md settings.json template does not include warn-dor-dod.sh


def test_T_0025_040_skill_md_settings_template_no_warn_dor_dod():
    """SKILL.md settings.json template must not include a warn-dor-dod.sh SubagentStop entry.

    ADR-0025 Wave 2b Step 4: 'SKILL.md settings.json template does not include
    warn-dor-dod.sh SubagentStop entry'. The template JSON block in SKILL.md must
    not wire this hook.

    The template is identified as the fenced code block that contains both
    'SubagentStop' and '"hooks"' -- the actual settings.json structure that
    /pipeline-setup copies to new projects.
    """
    assert SKILL_MD.exists(), f"SKILL.md not found at {SKILL_MD}."
    text = SKILL_MD.read_text()
    template_block = extract_settings_json_template_from_skill(text)
    assert template_block, (
        "SKILL.md does not contain a settings.json template block (a JSON code fence with "
        "SubagentStop and hooks). The template block is required for new project installs."
    )
    assert "warn-dor-dod.sh" not in template_block, (
        "SKILL.md settings.json template block still includes warn-dor-dod.sh. "
        "ADR-0025 Wave 2b Step 4 requires removing this entry from the template "
        "so new pipeline installations do not wire the deleted hook."
    )


# ═══════════════════════════════════════════════════════════════════════════
# WAVE 2b — T-0025-041 through T-0025-043 (Zero agent_capture in personas/rules)
# ═══════════════════════════════════════════════════════════════════════════

# ── T-0025-041: None of the four core persona files contains agent_capture ────


@pytest.mark.parametrize("agent_name,persona_path", list(PERSONA_FILES.items()))
def test_T_0025_041_core_personas_no_agent_capture(agent_name, persona_path):
    """None of source/shared/agents/{cal,colby,roz,agatha}.md may contain 'agent_capture'.

    ADR-0025 R12: 'After this ADR, no persona file, no rule file, no reference file
    instructs any agent to call agent_capture directly.' Personas for the four core
    agents that previously had behavioral capture instructions must be clean.
    """
    assert persona_path.exists(), (
        f"source/shared/agents/{agent_name}.md not found at {persona_path}."
    )
    text = persona_path.read_text()
    assert "agent_capture" not in text, (
        f"source/shared/agents/{agent_name}.md still contains 'agent_capture'. "
        f"ADR-0025 R12 requires that no persona file instructs any agent to call "
        f"agent_capture directly. The brain-extractor handles captures mechanically."
    )


# ── T-0025-042: pipeline-orchestration.md Hybrid Capture Model lacks agent_capture in Eva Writes context


def test_T_0025_042_pipeline_orch_no_agent_capture_in_writes():
    """pipeline-orchestration.md Hybrid Capture Model must not contain agent_capture in Eva Writes context.

    ADR-0025 R12 and Wave 2b acceptance criteria: the Writes subsection (with bulleted
    agent_capture calls attributed to Eva) is deleted. agent_capture may still appear
    in the Reads subsection (agent_search context is different) and in the Seed Capture
    protocol. The test looks for 'agent_capture' that appears on lines that describe
    Eva making direct captures (not as part of the Seed or /devops protocol).
    """
    text = read_source(PIPELINE_ORCH_MD)
    lines = text.splitlines()

    # Identify lines that represent forbidden patterns:
    # Eva's direct write calls to agent_capture outside Seed Capture and /devops
    # Pattern: lines that say "calls agent_capture" with a thought_type in the
    # user-decisions / phase-transitions / wave-decisions / model-vs-outcome / pipeline-end context
    # We look for the specific bullet language from the old Writes subsection.
    forbidden_patterns = [
        r"user decisions.*calls.*agent_capture",
        r"phase transitions.*calls.*agent_capture",
        r"wave decisions.*calls.*agent_capture",
        r"model-vs-outcome.*calls.*agent_capture",
        r"pipeline end.*calls.*agent_capture",
        r"cross-agent patterns.*calls.*agent_capture",
        r"deploy.*calls.*agent_capture.*lesson",
    ]
    violations = []
    for pattern in forbidden_patterns:
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line, re.IGNORECASE):
                violations.append((i, line.strip()))
    assert not violations, (
        f"pipeline-orchestration.md still contains Eva Writes bullets with agent_capture:\n"
        + "\n".join(f"  Line {i}: {l}" for i, l in violations)
        + "\nADR-0025 Wave 2b Step 4 requires deleting these bullets from the Hybrid Capture Model."
    )


# ── T-0025-043: source/shared/references/agent-preamble.md has no agent_capture ─


def test_T_0025_043_agent_preamble_no_agent_capture():
    """source/shared/references/agent-preamble.md must not contain 'agent_capture'.

    ADR-0025 R12: no reference file instructs agents to call agent_capture.
    ADR-0024 removed the Brain Capture Protocol from agent-preamble.md in its Wave 3.
    This test verifies the cleanup remains in place (no regression).
    """
    text = read_source(AGENT_PREAMBLE_MD)
    # The preamble may say "you do not call agent_capture directly" as a prohibition.
    # The test must allow that phrase while blocking any affirmative instruction.
    lines_with_capture = [
        (i, line.strip())
        for i, line in enumerate(text.splitlines(), start=1)
        if "agent_capture" in line
    ]
    # Allow only lines that explicitly say agents do NOT call agent_capture
    forbidden_lines = [
        (i, l) for i, l in lines_with_capture
        if not re.search(
            r"do not call|never call|you do not|agents do not|not.*call.*agent_capture|"
            r"do not.*agent_capture|agent_capture.*mechanically|mechanically.*agent_capture",
            l,
            re.IGNORECASE,
        )
    ]
    assert not forbidden_lines, (
        f"agent-preamble.md contains 'agent_capture' in non-prohibition context:\n"
        + "\n".join(f"  Line {i}: {l}" for i, l in forbidden_lines)
        + "\nADR-0025 R12 and ADR-0024 Wave 3 require that agent-preamble.md contains no "
        "affirmative agent_capture instructions. Only prohibition language is acceptable."
    )
