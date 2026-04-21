"""ADR-0042 pre-build test assertions: Scout Synthesis Layer and
Model/Effort Tier Corrections.

42 tests total (IDs T-0042-001..044, gaps at 034 and 038).
Happy: 29.  Failure (anti-regression): 13.

Per Roz-first TDD (retro lesson 002), tests encode what the files MUST look
like AFTER Colby implements ADR-0042, not what they currently contain.
Pre-build: failure tests should PASS (banned strings absent, immutable files
unchanged) and happy tests should FAIL (new content not yet written).

Reference: ADR-0042 §Test Specification (T-0042-001 through T-0042-044).
"""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Absolute paths (tests may run from any working directory)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_RULE = PROJECT_ROOT / "source" / "shared" / "rules" / "pipeline-models.md"
CLAUDE_RULE = PROJECT_ROOT / ".claude" / "rules" / "pipeline-models.md"
CURSOR_RULE = PROJECT_ROOT / ".cursor-plugin" / "rules" / "pipeline-models.mdc"
INVOCATION_TEMPLATES = (
    PROJECT_ROOT / "source" / "shared" / "references" / "invocation-templates.md"
)
PIPELINE_ORCHESTRATION = (
    PROJECT_ROOT / "source" / "shared" / "rules" / "pipeline-orchestration.md"
)
ADR_0042 = (
    PROJECT_ROOT
    / "docs"
    / "architecture"
    / "ADR-0042-scout-synthesis-tier-correction.md"
)
ADR_0041 = (
    PROJECT_ROOT
    / "docs"
    / "architecture"
    / "ADR-0041-effort-per-agent-map.md"
)
HOOK_FILE = PROJECT_ROOT / "source" / "claude" / "hooks" / "enforce-scout-swarm.sh"
CLAUDE_AGENTS_DIR = PROJECT_ROOT / "source" / "claude" / "agents"
CURSOR_AGENTS_DIR = PROJECT_ROOT / "source" / "cursor" / "agents"

# ---------------------------------------------------------------------------
# Baseline fixture import (Step 0 snapshot)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(PROJECT_ROOT / "tests" / "fixtures"))
from adr_0042_baselines import (
    ADR_0041_BLOB_HASH,
    CHANGED_AGENT_EXPECTED,
    CHANGED_AGENT_STRUCTURAL_HASHES,
    HOOK_BLOB_HASH,
    MDC_WRAPPER_SNAPSHOT,
    UNCHANGED_AGENT_EXPECTED,
    UNCHANGED_AGENT_FULL_HASHES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"File not found: {path}")
    return path.read_text()


def _read_required(path: Path) -> str:
    """Like _read but fails (not skips) when the file is missing.
    Use for files that must exist as part of the ADR-0042 build."""
    if not path.exists():
        pytest.fail(
            f"Required file not found: {path}. "
            "This file must be created as part of ADR-0042 implementation."
        )
    return path.read_text()


def _strip_claude_frontmatter(text: str) -> str:
    """Strip the leading YAML frontmatter block (--- ... ---) from installed
    .claude/rules/*.md files.  Source templates carry no frontmatter.
    Returns body only."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != "---":
        return text
    for idx in range(1, len(lines)):
        if lines[idx].rstrip("\n") == "---":
            rest = lines[idx + 1 :]
            if rest and rest[0].strip() == "":
                rest = rest[1:]
            return "".join(rest)
    return text


def _strip_mdc_wrapper(mdc_text: str) -> str:
    """Strip the two leading ---...--- frontmatter blocks from a .mdc file
    and any immediately following blank line, returning the body.

    The Cursor .mdc file has two frontmatter blocks (Cursor MDC block +
    paths overlay), both must be stripped to get body parity with the .md
    source.
    """
    lines = mdc_text.splitlines(keepends=True)
    count = 0
    end = -1
    for i, line in enumerate(lines):
        if line.rstrip("\n") == "---":
            count += 1
            if count == 4:  # fourth --- closes second block
                end = i
                break
    if end < 0:
        return mdc_text
    rest = lines[end + 1 :]
    if rest and rest[0].strip() == "":
        rest = rest[1:]
    return "".join(rest)


def _extract_section(text: str, heading: str, next_heading_level: str = "##") -> str:
    """Extract text from `heading` (inclusive) to the next heading at the
    same or higher level (exclusive).  Returns empty string if not found."""
    pattern = re.compile(
        r"^" + re.escape(heading) + r"\s*$", re.MULTILINE
    )
    m = pattern.search(text)
    if not m:
        return ""
    start = m.start()
    rest = text[m.end() :]
    # Match next heading at the same level (## or ###)
    next_heading_re = re.compile(r"^" + re.escape(next_heading_level) + r" ", re.MULTILINE)
    nm = next_heading_re.search(rest)
    if nm:
        return text[start : m.end() + nm.start()]
    return text[start:]


def _extract_xml_section(text: str, tag_id: str) -> str:
    """Extract content of <template id="TAG_ID"> ... </template>."""
    open_tag = f'<template id="{tag_id}">'
    close_tag = "</template>"
    if open_tag not in text:
        return ""
    start = text.index(open_tag)
    rest = text[start:]
    end = rest.find(close_tag)
    if end == -1:
        return rest
    return rest[: end + len(close_tag)]


_MODEL_RE = re.compile(r"^model:\s*(\S+)\s*$", re.MULTILINE)
_EFFORT_RE = re.compile(r"^effort:\s*(\S+)\s*$", re.MULTILINE)


def _parse_frontmatter(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"Frontmatter file not found: {path}")
    text = path.read_text()
    out: dict = {}
    m = _MODEL_RE.search(text)
    if m:
        out["model"] = m.group(1).strip().strip("'\"")
    e = _EFFORT_RE.search(text)
    if e:
        out["effort"] = e.group(1).strip().strip("'\"")
    return out


def _model_matches(actual: str | None, expected_substring: str) -> bool:
    if actual is None:
        return False
    return expected_substring.lower() in actual.lower()


def _structural_hash(path: Path) -> str:
    """SHA-256 of file content with model: and effort: lines stripped."""
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    filtered = [ln for ln in lines if not re.match(r"^(model|effort):\s*\S", ln)]
    return hashlib.sha256("".join(filtered).encode()).hexdigest()


def _full_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_hash_object(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "hash-object", str(path)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None


def _count_table_data_rows(section: str) -> int:
    """Count non-header table rows (lines starting with | that are not all
    dashes/pipes, and not the header separator line)."""
    count = 0
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            # Skip header separator (|---|---| patterns)
            inner = stripped[1:-1]
            if re.match(r"^[\s\-:|]+$", inner):
                continue
            count += 1
    # The first counted row is the header row; subtract 1
    return max(0, count - 1)


# ===========================================================================
# Category A: Rule table contract
# ===========================================================================


def test_T_0042_001_per_agent_table_has_16_rows():
    """T-0042-001 (happy): Per-Agent Assignment Table has exactly 16 rows.

    Required agents: Cal, Colby, Roz, Poirot, Sherlock, Robert, robert-spec,
    Sable, sable-ux, Sentinel, Agatha, Ellis, Distillator,
    brain-extractor, Explore, Synthesis.

    Pre-build: FAILS until Colby rewrites the table per ADR-0042 Step 1.
    """
    text = _read(SOURCE_RULE)
    # Extract the Per-Agent Assignment Table section
    section = _extract_section(text, "## Per-Agent Assignment Table", "##")
    assert section, (
        "source/shared/rules/pipeline-models.md is missing the "
        "'## Per-Agent Assignment Table' section."
    )
    rows = _count_table_data_rows(section)
    assert rows == 16, (
        f"Per-Agent Assignment Table has {rows} data rows; expected 16. "
        "ADR-0042 Decision #2 requires: Cal, Colby, Roz, Poirot, Sherlock, "
        "Robert, robert-spec, Sable, sable-ux, Sentinel, Agatha, "
        "Ellis, Distillator, brain-extractor, Explore, Synthesis."
    )


def test_T_0042_002_promotion_signals_table_has_3_rows():
    """T-0042-002 (happy): Promotion Signals table has exactly 3 rows.

    Required rows: Poirot final-juncture, read-only evidence, mechanical task.

    Pre-build: FAILS until Colby rewrites the promotion-signals section.
    """
    text = _read(SOURCE_RULE)
    # Find the promotion-signals <model-table> section
    open_tag = '<model-table id="promotion-signals">'
    close_tag = "</model-table>"
    if open_tag not in text:
        pytest.fail(
            "source/shared/rules/pipeline-models.md is missing "
            '<model-table id="promotion-signals"> section.'
        )
    start = text.index(open_tag)
    rest = text[start:]
    end = rest.find(close_tag)
    section = rest[: end + len(close_tag)] if end != -1 else rest
    rows = _count_table_data_rows(section)
    assert rows == 3, (
        f"Promotion Signals table has {rows} data rows; expected 3. "
        "ADR-0042 Decision #3 keeps only: Poirot final-juncture, "
        "read-only evidence, mechanical task."
    )


def test_T_0042_003_promotion_signals_no_auth_security_string():
    """T-0042-003 (failure): 'Auth/security/crypto files touched' must NOT
    appear in the Promotion Signals section.

    Pre-build: PASSES (banned string not yet removed because it doesn't exist
    in that form), or PASSES because the old ADR-0041 section had it and
    ADR-0042 hasn't landed yet.  Either way, this is an anti-regression gate.
    """
    text = _read(SOURCE_RULE)
    # Extract Promotion Signals section between ## headings
    section = _extract_section(text, "## Promotion Signals (one rung each)", "##")
    if not section:
        # Try alternative heading from ADR-0042
        section = _extract_section(text, "## Promotion Signals", "##")
    if not section:
        # No section at all -- no banned string can be there
        return
    assert "Auth/security/crypto files touched" not in section, (
        "source/shared/rules/pipeline-models.md Promotion Signals section "
        "still contains 'Auth/security/crypto files touched'. "
        "ADR-0042 Decision #3 removes this signal -- route to Sentinel instead."
    )


def test_T_0042_004_promotion_signals_no_large_pipeline_string():
    """T-0042-004 (failure): 'Pipeline sizing = Large' must NOT appear in
    the Promotion Signals section.

    Pre-build: PASSES (anti-regression gate; banned string not in new content).
    """
    text = _read(SOURCE_RULE)
    section = _extract_section(text, "## Promotion Signals (one rung each)", "##")
    if not section:
        section = _extract_section(text, "## Promotion Signals", "##")
    if not section:
        return
    assert "Pipeline sizing = Large" not in section, (
        "source/shared/rules/pipeline-models.md Promotion Signals section "
        "still contains 'Pipeline sizing = Large'. "
        "ADR-0042 Decision #3 removes this signal."
    )


def test_T_0042_005_per_agent_table_no_agatha_reference_docs_row():
    """T-0042-005 (failure): 'Agatha (reference docs)' must NOT appear in
    the Per-Agent Assignment Table section.

    Pre-build: PASSES if ADR-0041 content still says 'Agatha (reference docs)'
    anywhere in the file, this test fails.  The test is an anti-regression gate
    that ensures the Tier-1 runtime-override row was removed per ADR-0042
    Decision #2.
    """
    text = _read(SOURCE_RULE)
    section = _extract_section(text, "## Per-Agent Assignment Table", "##")
    if not section:
        # If section doesn't exist pre-build, the table is wrong but the
        # banned string is also absent -- skip rather than false-pass.
        pytest.skip("Per-Agent Assignment Table section not found.")
    assert "Agatha (reference docs)" not in section, (
        "source/shared/rules/pipeline-models.md Per-Agent Assignment Table "
        "still contains 'Agatha (reference docs)'. "
        "ADR-0042 Decision #2 removes the Tier-1 runtime-override row entirely."
    )


def test_T_0042_006_no_max_effort_in_per_agent_table():
    """T-0042-006 (failure): No table row in the Per-Agent Assignment Table
    has 'max' as the effort cell value.  Enforcement Rule 5 may contain the
    word 'max' in prose -- that does NOT fail this test.

    Pre-build: PASSES (no current row uses max).
    """
    text = _read(SOURCE_RULE)
    section = _extract_section(text, "## Per-Agent Assignment Table", "##")
    if not section:
        return  # Section absent pre-build -- no rows can be wrong
    for line in section.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        # Skip separator rows
        inner = stripped[1:-1]
        if re.match(r"^[\s\-:|]+$", inner):
            continue
        cells = [c.strip() for c in inner.split("|")]
        # Effort is column index 3 (0-indexed: Agent, Tier, Base model, Base effort, ...)
        if len(cells) > 3:
            effort_cell = cells[3].lower()
            assert effort_cell != "max", (
                f"Per-Agent Assignment Table row has effort='max': {line!r}. "
                "ADR-0042 Enforcement Rule 5 forbids max effort entirely. "
                "Ceiling is xhigh."
            )


def test_T_0042_007_enforcement_rules_max_effort_forbidden():
    """T-0042-007 (happy): Enforcement Rules section contains the literal
    string 'max effort is forbidden'.

    Pre-build: FAILS until Colby adds Enforcement Rule 5.
    """
    text = _read(SOURCE_RULE)
    assert "max effort is forbidden" in text.lower(), (
        "source/shared/rules/pipeline-models.md does not contain the phrase "
        "'max effort is forbidden' (case-insensitive). "
        "ADR-0042 Decision #4 requires Enforcement Rule 5 verbatim."
    )


# ===========================================================================
# Category B: Frontmatter consistency
# ===========================================================================


def test_T_0042_008_roz_claude_frontmatter():
    """T-0042-008 (happy): roz.frontmatter.yml (Claude) has opus / medium."""
    fm = _parse_frontmatter(CLAUDE_AGENTS_DIR / "roz.frontmatter.yml")
    assert _model_matches(fm.get("model"), "opus"), (
        f"roz (Claude): expected model family 'opus', got {fm.get('model')!r}."
    )
    assert fm.get("effort") == "medium", (
        f"roz (Claude): expected effort 'medium', got {fm.get('effort')!r}. "
        "ADR-0042 Decision #2 demotes Roz effort high -> medium."
    )


def test_T_0042_009_robert_claude_frontmatter():
    """T-0042-009 (happy): robert.frontmatter.yml (Claude) has sonnet / medium."""
    fm = _parse_frontmatter(CLAUDE_AGENTS_DIR / "robert.frontmatter.yml")
    assert _model_matches(fm.get("model"), "sonnet"), (
        f"robert (Claude): expected model family 'sonnet', got {fm.get('model')!r}. "
        "ADR-0042 Decision #2 demotes Robert opus -> sonnet."
    )
    assert fm.get("effort") == "medium", (
        f"robert (Claude): expected effort 'medium', got {fm.get('effort')!r}."
    )


def test_T_0042_010_sable_claude_frontmatter():
    """T-0042-010 (happy): sable.frontmatter.yml (Claude) has sonnet / medium."""
    fm = _parse_frontmatter(CLAUDE_AGENTS_DIR / "sable.frontmatter.yml")
    assert _model_matches(fm.get("model"), "sonnet"), (
        f"sable (Claude): expected model family 'sonnet', got {fm.get('model')!r}. "
        "ADR-0042 Decision #2 demotes Sable opus -> sonnet."
    )
    assert fm.get("effort") == "medium", (
        f"sable (Claude): expected effort 'medium', got {fm.get('effort')!r}."
    )


def test_T_0042_011_sentinel_claude_frontmatter():
    """T-0042-011 (happy): sentinel.frontmatter.yml (Claude) has opus / low."""
    fm = _parse_frontmatter(CLAUDE_AGENTS_DIR / "sentinel.frontmatter.yml")
    assert _model_matches(fm.get("model"), "opus"), (
        f"sentinel (Claude): expected model family 'opus', got {fm.get('model')!r}."
    )
    assert fm.get("effort") == "low", (
        f"sentinel (Claude): expected effort 'low', got {fm.get('effort')!r}. "
        "ADR-0042 Decision #2 demotes Sentinel effort medium -> low."
    )


# T_0042_012 removed by ADR-0045 -- Deps agent and its frontmatter were removed.


def test_T_0042_013_ellis_claude_frontmatter():
    """T-0042-013 (happy): ellis.frontmatter.yml (Claude) has sonnet / low."""
    fm = _parse_frontmatter(CLAUDE_AGENTS_DIR / "ellis.frontmatter.yml")
    assert _model_matches(fm.get("model"), "sonnet"), (
        f"ellis (Claude): expected model family 'sonnet', got {fm.get('model')!r}. "
        "ADR-0042 Decision #2 promotes Ellis haiku -> sonnet."
    )
    assert fm.get("effort") == "low", (
        f"ellis (Claude): expected effort 'low', got {fm.get('effort')!r}."
    )


def test_T_0042_014_distillator_claude_frontmatter():
    """T-0042-014 (happy): distillator.frontmatter.yml (Claude) has sonnet / low."""
    fm = _parse_frontmatter(CLAUDE_AGENTS_DIR / "distillator.frontmatter.yml")
    assert _model_matches(fm.get("model"), "sonnet"), (
        f"distillator (Claude): expected model family 'sonnet', got {fm.get('model')!r}. "
        "ADR-0042 Decision #2 promotes Distillator haiku -> sonnet."
    )
    assert fm.get("effort") == "low", (
        f"distillator (Claude): expected effort 'low', got {fm.get('effort')!r}."
    )


def test_T_0042_015_brain_extractor_claude_frontmatter():
    """T-0042-015 (happy): brain-extractor.frontmatter.yml (Claude) has sonnet / low."""
    fm = _parse_frontmatter(CLAUDE_AGENTS_DIR / "brain-extractor.frontmatter.yml")
    assert _model_matches(fm.get("model"), "sonnet"), (
        f"brain-extractor (Claude): expected model family 'sonnet', got {fm.get('model')!r}. "
        "ADR-0042 Decision #2 promotes brain-extractor haiku -> sonnet."
    )
    assert fm.get("effort") == "low", (
        f"brain-extractor (Claude): expected effort 'low', got {fm.get('effort')!r}."
    )


@pytest.mark.parametrize(
    "agent",
    [
        "roz",
        "robert",
        "sable",
        "sentinel",
        "deps",
        "ellis",
        "distillator",
        "brain-extractor",
    ],
)
def test_T_0042_016_changed_agents_platform_parity(agent):
    """T-0042-016 (happy): For each changed agent, both Claude and Cursor
    frontmatter files have byte-identical model: and effort: values.

    Pre-build: FAILS for agents whose Cursor frontmatter still has old values.
    """
    claude_path = CLAUDE_AGENTS_DIR / f"{agent}.frontmatter.yml"
    cursor_path = CURSOR_AGENTS_DIR / f"{agent}.frontmatter.yml"
    if not claude_path.exists():
        pytest.skip(f"Claude frontmatter not found: {claude_path}")
    if not cursor_path.exists():
        # brain-extractor may be Claude-only -- see ADR-0042 Note 2
        pytest.skip(f"Cursor frontmatter not found: {cursor_path} (may be Claude-only)")

    claude_fm = _parse_frontmatter(claude_path)
    cursor_fm = _parse_frontmatter(cursor_path)

    assert claude_fm.get("model") == cursor_fm.get("model"), (
        f"{agent}: Claude model '{claude_fm.get('model')}' != "
        f"Cursor model '{cursor_fm.get('model')}'. "
        "ADR-0042 Step 2 requires identical model/effort across platforms."
    )
    assert claude_fm.get("effort") == cursor_fm.get("effort"), (
        f"{agent}: Claude effort '{claude_fm.get('effort')}' != "
        f"Cursor effort '{cursor_fm.get('effort')}'. "
        "ADR-0042 Step 2 requires identical model/effort across platforms."
    )


@pytest.mark.parametrize(
    "agent",
    ["cal", "colby", "investigator", "sherlock", "robert-spec", "sable-ux", "agatha"],
)
def test_T_0042_017_unchanged_agents_values_match_baseline(agent):
    """T-0042-017 (failure): Each of the 7 unchanged agents has the exact
    model and effort from the baseline table on BOTH platforms.  Any deviation
    on any of the 14 files (7 agents x 2 platforms) fails with the specific
    file and field named.

    Pre-build: PASSES (these agents should be untouched).
    """
    expected = UNCHANGED_AGENT_EXPECTED[agent]
    for platform, agents_dir in [("claude", CLAUDE_AGENTS_DIR), ("cursor", CURSOR_AGENTS_DIR)]:
        path = agents_dir / f"{agent}.frontmatter.yml"
        if not path.exists():
            pytest.skip(f"Frontmatter file not found: {path}")
        fm = _parse_frontmatter(path)
        actual_model = fm.get("model")
        actual_effort = fm.get("effort")
        assert _model_matches(actual_model, expected["model"]), (
            f"{path}: expected model family '{expected['model']}', "
            f"got '{actual_model}'. "
            "This is an UNCHANGED agent per ADR-0042; its model must not change."
        )
        assert actual_effort == expected["effort"], (
            f"{path}: expected effort '{expected['effort']}', "
            f"got '{actual_effort}'. "
            "This is an UNCHANGED agent per ADR-0042; its effort must not change."
        )


def test_T_0042_018_no_max_effort_in_any_frontmatter():
    """T-0042-018 (failure): No *.frontmatter.yml file under source/claude/agents/
    or source/cursor/agents/ contains 'effort: max'.

    Pre-build: PASSES (no existing frontmatter has max).
    """
    for agents_dir in [CLAUDE_AGENTS_DIR, CURSOR_AGENTS_DIR]:
        if not agents_dir.exists():
            continue
        for yml in agents_dir.glob("*.frontmatter.yml"):
            text = yml.read_text()
            assert "effort: max" not in text, (
                f"{yml} contains 'effort: max'. "
                "ADR-0042 Enforcement Rule 5 forbids max effort in all agents."
            )


@pytest.mark.parametrize(
    "agent",
    [
        "roz",
        "robert",
        "sable",
        "sentinel",
        "deps",
        "ellis",
        "distillator",
        "brain-extractor",
    ],
)
def test_T_0042_019_changed_agents_structural_hash(agent):
    """T-0042-019 (failure): For every frontmatter file changed by ADR-0042,
    strip model: and effort: lines then assert the structural hash matches
    the Step 0 baseline.  Verifies no tools:, hooks:, color:, maxTurns:,
    description:, name:, permissionMode:, or disallowedTools: fields changed.

    Pre-build: PASSES (no edits have landed yet, structure is unchanged).
    """
    for platform, agents_dir in [("claude", CLAUDE_AGENTS_DIR), ("cursor", CURSOR_AGENTS_DIR)]:
        path = agents_dir / f"{agent}.frontmatter.yml"
        if not path.exists():
            pytest.skip(f"Frontmatter not found: {path} (may be Claude-only for brain-extractor)")
        expected_hash = CHANGED_AGENT_STRUCTURAL_HASHES[agent][platform]
        actual_hash = _structural_hash(path)
        assert actual_hash == expected_hash, (
            f"{path}: structural hash mismatch. Expected {expected_hash}, "
            f"got {actual_hash}. "
            "Non-model/effort fields were modified. ADR-0042 Step 2 permits "
            "ONLY model: and/or effort: field changes per agent."
        )


# ===========================================================================
# Category C: Synthesis protocol contract
# ===========================================================================


def test_T_0042_020_template_2c_scout_synthesis_present():
    """T-0042-020 (happy): invocation-templates.md contains Template 2c
    with id 'scout-synthesis'.

    Pre-build: FAILS until Colby adds Template 2c in Step 3.
    """
    text = _read(INVOCATION_TEMPLATES)
    assert '<template id="scout-synthesis">' in text, (
        "source/shared/references/invocation-templates.md does not contain "
        '<template id="scout-synthesis">. '
        "ADR-0042 Step 3 adds Template 2c."
    )


def test_T_0042_021_template_2c_cal_synthesis_required_fields():
    """T-0042-021 (happy): Template 2c specifies Cal synthesis output with
    required field names: 'Top patterns', 'Confirmed blast-radius',
    'Manifest notes'.

    Pre-build: FAILS until Colby adds Template 2c.
    """
    text = _read(INVOCATION_TEMPLATES)
    section = _extract_xml_section(text, "scout-synthesis")
    if not section:
        pytest.fail(
            "Template 2c (scout-synthesis) not found in invocation-templates.md."
        )
    required = ["Top patterns", "Confirmed blast-radius", "Manifest notes"]
    for field in required:
        assert field in section, (
            f"Template 2c is missing Cal synthesis required field '{field}'. "
            "ADR-0042 Decision #1 Cal synthesis shape requires all three fields."
        )


def test_T_0042_022_template_2c_colby_synthesis_required_fields():
    """T-0042-022 (happy): Template 2c specifies Colby synthesis output with
    required field names: 'Key functions/blocks in scope',
    'Relevant patterns to replicate', 'Files pre-loaded'.

    Pre-build: FAILS until Colby adds Template 2c.
    """
    text = _read(INVOCATION_TEMPLATES)
    section = _extract_xml_section(text, "scout-synthesis")
    if not section:
        pytest.fail(
            "Template 2c (scout-synthesis) not found in invocation-templates.md."
        )
    required = [
        "Key functions/blocks in scope",
        "Relevant patterns to replicate",
        "Files pre-loaded",
    ]
    for field in required:
        assert field in section, (
            f"Template 2c is missing Colby synthesis required field '{field}'. "
            "ADR-0042 Decision #1 Colby synthesis shape requires all three fields."
        )


def test_T_0042_023_template_2c_roz_synthesis_required_fields():
    """T-0042-023 (happy): Template 2c specifies Roz synthesis output with
    required field names: 'Changed sections', 'Test baseline', 'Risk areas'.

    Pre-build: FAILS until Colby adds Template 2c.
    """
    text = _read(INVOCATION_TEMPLATES)
    section = _extract_xml_section(text, "scout-synthesis")
    if not section:
        pytest.fail(
            "Template 2c (scout-synthesis) not found in invocation-templates.md."
        )
    required = ["Changed sections", "Test baseline", "Risk areas"]
    for field in required:
        assert field in section, (
            f"Template 2c is missing Roz synthesis required field '{field}'. "
            "ADR-0042 Decision #1 Roz synthesis shape requires all three fields."
        )


def test_T_0042_024_template_2c_forbidden_full_file_contents():
    """T-0042-024 (failure): Template 2c must contain the literal string
    'Full file contents over 50 lines' (the prohibition on large file dumps).

    Pre-build: FAILS because Template 2c doesn't exist yet.  After landing:
    this is a content-presence check.
    """
    text = _read(INVOCATION_TEMPLATES)
    section = _extract_xml_section(text, "scout-synthesis")
    if not section:
        pytest.fail(
            "Template 2c (scout-synthesis) not found in invocation-templates.md."
        )
    assert "Full file contents over 50 lines" in section, (
        "Template 2c does not contain the prohibition 'Full file contents "
        "over 50 lines'. ADR-0042 Decision #1 Forbidden list requires this entry."
    )


def test_T_0042_025_template_2c_forbidden_design_and_ranked():
    """T-0042-025 (failure): Template 2c must contain both
    'Design proposals or architectural recommendations' AND
    'Ranked \"best approach\" narratives' in its Forbidden section.

    Pre-build: FAILS because Template 2c doesn't exist yet.
    """
    text = _read(INVOCATION_TEMPLATES)
    section = _extract_xml_section(text, "scout-synthesis")
    if not section:
        pytest.fail(
            "Template 2c (scout-synthesis) not found in invocation-templates.md."
        )
    assert "Design proposals or architectural recommendations" in section, (
        "Template 2c is missing forbidden item 'Design proposals or "
        "architectural recommendations'. ADR-0042 Decision #1."
    )
    assert "Ranked" in section and "best approach" in section, (
        "Template 2c is missing forbidden item containing 'Ranked' and "
        "'best approach'. ADR-0042 Decision #1 forbids ranked narratives."
    )


@pytest.mark.parametrize(
    "template_id",
    ["scout-research-brief", "colby-build", "roz-code-qa"],
)
def test_T_0042_026_templates_2a_4_8_reference_2c(template_id):
    """T-0042-026 (happy): Each of Templates 2a (scout-research-brief),
    4 (colby-build), 8 (roz-code-qa) references '2c' or 'scout-synthesis'
    within its own section.  File-wide presence is insufficient.

    Pre-build: FAILS for all three until Colby updates them in Step 4.
    """
    text = _read(INVOCATION_TEMPLATES)
    section = _extract_xml_section(text, template_id)
    if not section:
        pytest.fail(
            f"Template '{template_id}' not found in invocation-templates.md."
        )
    assert "2c" in section or "scout-synthesis" in section, (
        f"Template '{template_id}' does not reference '2c' or 'scout-synthesis'. "
        "ADR-0042 Step 4 requires Templates 2a, 4, 8 to explicitly reference "
        "Template 2c."
    )


def test_T_0042_027_scout_fanout_protocol_explicit_spawn_directive():
    """T-0042-027 (happy): Scout Fan-out Protocol section in
    pipeline-orchestration.md contains both 'MUST spawn' and
    'separate parallel subagent'.

    Pre-build: FAILS until Colby adds the explicit spawn directive in Step 4.
    """
    text = _read(PIPELINE_ORCHESTRATION)
    # Extract Scout Fan-out Protocol section (heading may vary in level)
    section = _extract_section(text, "### Scout Fan-out Protocol", "###")
    if not section:
        section = _extract_section(text, "## Scout Fan-out Protocol", "##")
    if not section:
        # Try to grab enough context around the heading
        if "Scout Fan-out Protocol" in text:
            idx = text.index("Scout Fan-out Protocol")
            section = text[max(0, idx - 10) : idx + 3000]
        else:
            pytest.fail(
                "pipeline-orchestration.md does not contain a "
                "'Scout Fan-out Protocol' section."
            )
    assert "MUST spawn" in section, (
        "Scout Fan-out Protocol section does not contain 'MUST spawn'. "
        "ADR-0042 Decision #6 requires an explicit spawn directive."
    )
    assert "separate parallel subagent" in section, (
        "Scout Fan-out Protocol section does not contain "
        "'separate parallel subagent'. "
        "ADR-0042 Decision #6 requires explicit separate-subagent language."
    )


def test_T_0042_028_scout_fanout_protocol_synthesis_row():
    """T-0042-028 (happy): Scout Fan-out Protocol section contains a note
    that synthesis fires after scouts return for Cal/Colby/Roz and before
    the primary agent.

    Match criteria: 'synthesis' AND ('after scouts' OR 'scouts return') AND
    ('Cal' AND 'Colby' AND 'Roz').

    Pre-build: FAILS until Colby adds the synthesis row in Step 4.
    """
    text = _read(PIPELINE_ORCHESTRATION)
    section = _extract_section(text, "### Scout Fan-out Protocol", "###")
    if not section:
        section = _extract_section(text, "## Scout Fan-out Protocol", "##")
    if not section:
        if "Scout Fan-out Protocol" in text:
            idx = text.index("Scout Fan-out Protocol")
            section = text[max(0, idx - 10) : idx + 3000]
        else:
            pytest.fail(
                "pipeline-orchestration.md does not contain a "
                "'Scout Fan-out Protocol' section."
            )
    has_synthesis = "synthesis" in section.lower()
    has_after_scouts = "after scouts" in section.lower() or "scouts return" in section.lower()
    has_all_agents = "Cal" in section and "Colby" in section and "Roz" in section
    assert has_synthesis and has_after_scouts and has_all_agents, (
        "Scout Fan-out Protocol section is missing the synthesis-row note. "
        "Required: 'synthesis' + ('after scouts' OR 'scouts return') + "
        "Cal + Colby + Roz. "
        "ADR-0042 Step 4 adds a synthesis row to the protocol."
    )


def test_T_0042_029_hook_file_unchanged():
    """T-0042-029 (failure): enforce-scout-swarm.sh git blob hash must equal
    the Step 0 baseline fixture.

    Pre-build: PASSES (hook is unchanged).  Post-build: MUST still pass.
    ADR-0042 Step 6 is read-only; any hook change is a violation.
    """
    if not HOOK_FILE.exists():
        pytest.skip(f"Hook file not found: {HOOK_FILE}")
    actual = _git_hash_object(HOOK_FILE)
    if actual is None:
        pytest.skip("git not available -- cannot compute blob hash.")
    assert actual == HOOK_BLOB_HASH, (
        f"enforce-scout-swarm.sh blob hash changed: expected {HOOK_BLOB_HASH}, "
        f"got {actual}. "
        "ADR-0042 Step 6 is read-only -- the hook MUST NOT be modified."
    )


# ===========================================================================
# Category D: Installed-mirror parity
# ===========================================================================


def test_T_0042_030_claude_mirror_body_equals_source():
    """T-0042-030 (happy): .claude/rules/pipeline-models.md body (frontmatter
    stripped) is byte-identical to source/shared/rules/pipeline-models.md.

    Pre-build: FAILS until Colby syncs the installed mirror in Step 1.
    """
    source_text = _read(SOURCE_RULE)
    if not CLAUDE_RULE.exists():
        pytest.skip(f"Installed mirror not found: {CLAUDE_RULE}")
    mirror_body = _strip_claude_frontmatter(CLAUDE_RULE.read_text())
    assert mirror_body == source_text, (
        ".claude/rules/pipeline-models.md body diverges from "
        "source/shared/rules/pipeline-models.md. "
        "ADR-0042 Step 1 (and Step 5 verification) requires byte-identical body."
    )


def test_T_0042_031_cursor_mirror_body_equals_source():
    """T-0042-031 (happy): .cursor-plugin/rules/pipeline-models.mdc body
    (both MDC wrapper frontmatter blocks stripped) is byte-identical to
    source/shared/rules/pipeline-models.md.

    Pre-build: FAILS until Colby syncs the Cursor mirror.
    """
    source_text = _read(SOURCE_RULE)
    if not CURSOR_RULE.exists():
        pytest.fail(
            f"Cursor installed mirror missing: {CURSOR_RULE}. "
            "ADR-0042 Step 1 requires both installed mirrors."
        )
    mdc_body = _strip_mdc_wrapper(CURSOR_RULE.read_text())
    assert mdc_body == source_text, (
        ".cursor-plugin/rules/pipeline-models.mdc body diverges from "
        "source/shared/rules/pipeline-models.md. "
        "ADR-0042 Step 1 requires byte-identical body (modulo MDC wrapper)."
    )


def test_T_0042_032_installed_mirrors_no_banned_promotion_strings():
    """T-0042-032 (failure): Neither .claude/rules/pipeline-models.md nor
    .cursor-plugin/rules/pipeline-models.mdc contains any of the three
    removed promotion strings.

    Pre-build: FAILS if the mirrors still carry ADR-0041 content.
    """
    banned = [
        "Auth/security/crypto files touched",
        "Pipeline sizing = Large",
        "New module / service creation",
    ]
    files_to_check = []
    if CLAUDE_RULE.exists():
        files_to_check.append(CLAUDE_RULE)
    if CURSOR_RULE.exists():
        files_to_check.append(CURSOR_RULE)
    if not files_to_check:
        pytest.skip("Installed mirror files not found.")
    for f in files_to_check:
        text = f.read_text()
        for s in banned:
            assert s not in text, (
                f"{f} still contains banned promotion string '{s}'. "
                "ADR-0042 Decision #3 removes auth/security, Large, and "
                "new-module promotion signals from all installed mirrors."
            )


def test_T_0042_042_cursor_mdc_wrapper_unchanged():
    """T-0042-042 (failure): .cursor-plugin/rules/pipeline-models.mdc MDC
    wrapper (first two ---...--- frontmatter blocks) must be byte-identical
    to the Step 0 baseline snapshot.  Verifies body-only update.

    Pre-build: PASSES (wrapper unchanged).  Post-build: MUST still pass.
    """
    if not CURSOR_RULE.exists():
        pytest.skip(f"Cursor mirror not found: {CURSOR_RULE}")
    mdc_text = CURSOR_RULE.read_text()
    lines = mdc_text.splitlines(keepends=True)
    # Extract up through the fourth --- (end of second frontmatter block)
    count = 0
    end = -1
    for i, line in enumerate(lines):
        if line.rstrip("\n") == "---":
            count += 1
            if count == 4:
                end = i
                break
    if end < 0:
        pytest.fail(
            ".cursor-plugin/rules/pipeline-models.mdc does not have two "
            "---...--- frontmatter blocks. MDC wrapper format unexpected."
        )
    actual_wrapper = "".join(lines[: end + 1])
    assert actual_wrapper == MDC_WRAPPER_SNAPSHOT, (
        ".cursor-plugin/rules/pipeline-models.mdc MDC wrapper changed. "
        f"Expected:\n{MDC_WRAPPER_SNAPSHOT!r}\nActual:\n{actual_wrapper!r}\n"
        "ADR-0042 Step 1 Note 6: preserve the wrapper; replace only the body."
    )


# ===========================================================================
# Category E: Supersession metadata
# ===========================================================================


def test_T_0042_033_adr_0042_status_supersession():
    """T-0042-033 (happy): ADR-0042 Status section contains the three
    required strings: 'Supersedes (portions of):', 'Per-Agent Assignment
    Table', and 'Promotion Signals'.

    Pre-build: FAILS until ADR-0042 is committed to the worktree.
    """
    text = _read_required(ADR_0042)
    assert "Supersedes (portions of):" in text, (
        "ADR-0042 Status section missing 'Supersedes (portions of):'. "
        "ADR-0042 §Status requires explicit supersession notation."
    )
    assert "Per-Agent Assignment Table" in text, (
        "ADR-0042 missing 'Per-Agent Assignment Table' in Status section."
    )
    assert "Promotion Signals" in text, (
        "ADR-0042 missing 'Promotion Signals' in Status section."
    )


def test_T_0042_035_adr_0041_file_unchanged():
    """T-0042-035 (failure): ADR-0041 file git blob hash must equal the Step 0
    baseline fixture.  ADR immutability -- ADR-0041 must not be modified.

    Pre-build: PASSES.  Post-build: MUST still pass.
    """
    if not ADR_0041.exists():
        pytest.skip(f"ADR-0041 file not found: {ADR_0041}")
    actual = _git_hash_object(ADR_0041)
    if actual is None:
        pytest.skip("git not available -- cannot compute blob hash.")
    assert actual == ADR_0041_BLOB_HASH, (
        f"ADR-0041 blob hash changed: expected {ADR_0041_BLOB_HASH}, "
        f"got {actual}. "
        "ADR immutability: ADR-0041 must not be modified. "
        "ADR-0042 supersedes it by reference; the original file is preserved."
    )


def test_T_0042_044_adr_0042_status_accepted():
    """T-0042-044 (happy): ADR-0042 Status section begins with 'Accepted'
    as the first non-whitespace token after the '## Status' heading.

    Pre-build: FAILS until ADR-0042 is committed to the worktree.
    """
    text = _read_required(ADR_0042)
    section = _extract_section(text, "## Status", "##")
    if not section:
        pytest.fail("ADR-0042 is missing the '## Status' section.")
    # Skip the heading line itself and find the first non-empty content line
    lines = section.splitlines()
    for line in lines[1:]:
        stripped = line.strip()
        if stripped:
            assert stripped.startswith("Accepted"), (
                f"ADR-0042 Status section first content line does not start with "
                f"'Accepted': {stripped!r}. "
                "ADR-0042 §Status should open with 'Accepted.'."
            )
            return
    pytest.fail("ADR-0042 Status section has no content after the heading.")


# ===========================================================================
# Category F: Synthesis skip-condition and tier-row coverage
# ===========================================================================


def test_T_0042_036_template_2c_skip_conditions():
    """T-0042-036 (happy): Template 2c documents synthesis skip conditions:
    Cal (Small/Micro), Colby (Micro + re-invocation), Roz (scoped re-run).

    Pre-build: FAILS until Colby adds Template 2c.
    """
    text = _read(INVOCATION_TEMPLATES)
    section = _extract_xml_section(text, "scout-synthesis")
    if not section:
        pytest.fail(
            "Template 2c (scout-synthesis) not found in invocation-templates.md."
        )
    section_lower = section.lower()
    # Cal: Small and Micro skip
    assert "small" in section_lower or "micro" in section_lower, (
        "Template 2c does not mention 'Small' or 'Micro' skip conditions for Cal. "
        "ADR-0042 Decision #1 Skip Conditions."
    )
    # Colby: Micro + re-invocation
    assert "micro" in section_lower, (
        "Template 2c does not mention 'Micro' skip condition for Colby. "
        "ADR-0042 Decision #1 Skip Conditions."
    )
    assert "re-invocation" in section_lower or "fix cycle" in section_lower, (
        "Template 2c does not mention re-invocation or fix cycle skip for Colby. "
        "ADR-0042 Decision #1 Skip Conditions."
    )
    # Roz: scoped re-run
    assert "scoped" in section_lower, (
        "Template 2c does not mention 'scoped' re-run skip for Roz. "
        "ADR-0042 Decision #1 Skip Conditions."
    )


def test_T_0042_037_synthesis_row_in_per_agent_table():
    """T-0042-037 (happy): Per-Agent Assignment Table contains a 'Synthesis'
    row with Tier 2, model sonnet, effort low.

    Pre-build: FAILS until Colby adds the Synthesis row.
    """
    text = _read(SOURCE_RULE)
    section = _extract_section(text, "## Per-Agent Assignment Table", "##")
    if not section:
        pytest.fail(
            "Per-Agent Assignment Table section missing in pipeline-models.md."
        )
    # Find the Synthesis row
    synthesis_row = None
    for line in section.splitlines():
        if "Synthesis" in line and line.strip().startswith("|"):
            synthesis_row = line
            break
    assert synthesis_row is not None, (
        "Per-Agent Assignment Table has no 'Synthesis' row. "
        "ADR-0042 Decision #2 adds Synthesis as a new Tier 2 agent."
    )
    row_lower = synthesis_row.lower()
    assert "2" in synthesis_row, (
        f"Synthesis row does not show Tier 2: {synthesis_row!r}."
    )
    assert "sonnet" in row_lower, (
        f"Synthesis row model is not 'sonnet': {synthesis_row!r}. "
        "ADR-0042 Decision #2: Synthesis = sonnet/low."
    )
    assert "low" in row_lower, (
        f"Synthesis row effort is not 'low': {synthesis_row!r}. "
        "ADR-0042 Decision #2: Synthesis = sonnet/low."
    )


# ===========================================================================
# Category G: Adaptive-thinking, block mapping, platform symmetry
# ===========================================================================


def test_T_0042_039_adaptive_thinking_rationale_paragraph():
    """T-0042-039 (happy): pipeline-models.md contains the literal string
    'Fixed thinking budgets are unsupported' (adaptive-thinking rationale
    paragraph from R12).

    Pre-build: FAILS until Colby adds the paragraph in Step 1.
    """
    text = _read(SOURCE_RULE)
    assert "Fixed thinking budgets are unsupported" in text, (
        "source/shared/rules/pipeline-models.md does not contain the phrase "
        "'Fixed thinking budgets are unsupported'. "
        "ADR-0042 Decision #5 (R12) requires an adaptive-thinking rationale "
        "paragraph citing this Anthropic Opus 4.7 guidance."
    )


def test_T_0042_040_template_2c_block_mappings():
    """T-0042-040 (happy): Template 2c explicitly names all three block
    mappings with each block name paired with its primary agent name:
    <research-brief> (Cal), <colby-context> (Colby), <qa-evidence> (Roz).

    Pre-build: FAILS until Colby adds Template 2c.
    """
    text = _read(INVOCATION_TEMPLATES)
    section = _extract_xml_section(text, "scout-synthesis")
    if not section:
        pytest.fail(
            "Template 2c (scout-synthesis) not found in invocation-templates.md."
        )
    # Each block name must appear in the section
    assert "<research-brief>" in section, (
        "Template 2c does not contain '<research-brief>' block mapping for Cal."
    )
    assert "<colby-context>" in section, (
        "Template 2c does not contain '<colby-context>' block mapping for Colby."
    )
    assert "<qa-evidence>" in section, (
        "Template 2c does not contain '<qa-evidence>' block mapping for Roz."
    )
    # Each block name must appear on or near a line that also names its agent
    def block_and_agent_paired(block: str, agent: str) -> bool:
        for line in section.splitlines():
            if block in line and agent in line:
                return True
        # Also accept if they are within the same paragraph (3-line window)
        lines = section.splitlines()
        for i, line in enumerate(lines):
            if block in line:
                window = "\n".join(lines[max(0, i - 1) : i + 3])
                if agent in window:
                    return True
        return False

    assert block_and_agent_paired("<research-brief>", "Cal"), (
        "Template 2c: '<research-brief>' not paired with 'Cal' in the same "
        "paragraph/bullet. ADR-0042 Decision #1 block-continuity requires "
        "explicit per-agent block mapping."
    )
    assert block_and_agent_paired("<colby-context>", "Colby"), (
        "Template 2c: '<colby-context>' not paired with 'Colby'."
    )
    assert block_and_agent_paired("<qa-evidence>", "Roz"), (
        "Template 2c: '<qa-evidence>' not paired with 'Roz'."
    )


def test_T_0042_041_template_2c_synthesis_invocation_params():
    """T-0042-041 (happy): Template 2c specifies the synthesis invocation
    parameters: model: sonnet (or "sonnet") AND effort: low (or "low").

    Pre-build: FAILS until Colby adds Template 2c.
    """
    text = _read(INVOCATION_TEMPLATES)
    section = _extract_xml_section(text, "scout-synthesis")
    if not section:
        pytest.fail(
            "Template 2c (scout-synthesis) not found in invocation-templates.md."
        )
    # Accept both quoted and unquoted forms
    has_model = 'model: "sonnet"' in section or "model: sonnet" in section
    has_effort = 'effort: "low"' in section or "effort: low" in section
    assert has_model, (
        "Template 2c does not specify synthesis invocation model 'sonnet'. "
        "Expected 'model: \"sonnet\"' or 'model: sonnet' in the template body. "
        "ADR-0042 Decision #1: synthesis agent is invoked at sonnet/low."
    )
    assert has_effort, (
        "Template 2c does not specify synthesis invocation effort 'low'. "
        "Expected 'effort: \"low\"' or 'effort: low' in the template body. "
        "ADR-0042 Decision #1: synthesis agent is invoked at sonnet/low."
    )


def test_T_0042_043_cursor_brain_extractor_frontmatter_exists():
    """T-0042-043 (happy): source/cursor/agents/brain-extractor.frontmatter.yml
    exists, confirming platform symmetry for the brain-extractor row of
    T-0042-016.  If this test fails, the brain-extractor row in T-0042-016
    would become vacuously true via skip -- this test prevents that silent pass.

    Pre-build: PASSES if the file currently exists on the Cursor platform.
    """
    path = CURSOR_AGENTS_DIR / "brain-extractor.frontmatter.yml"
    assert path.exists(), (
        f"{path} does not exist. "
        "ADR-0042 Note 2 states brain-extractor may be Claude-only. "
        "If it IS Claude-only, this test should be explicitly skipped and "
        "T-0042-016's brain-extractor row is documented as Claude-only in "
        "the commit message. The test exists to prevent a silent vacuous pass."
    )
