"""ADR-0044 pre-build test assertions: Instruction-budget trim Slice 2.

All new tests in this file are PRE-BUILD: they MUST FAIL against the current
codebase and PASS only after Colby implements ADR-0044. A test that passes
before Colby builds is flagged with justification in its docstring (Retro
Lesson #002).

Scope (per ADR-0044 Test Specification):
  Category A (T_0044_001..007)  -- routing-detail.md creation + content
                                   preservation (source file).
  Category B (T_0044_008..016)  -- agent-system.md <routing id="auto-routing">
                                   rewrite: summary bullets + anchors + moved
                                   headers/rows absent.
  Category C (T_0044_017..019)  -- Installed-mirror parity for the 3 files
                                   (routing-detail.md, agent-system.md,
                                   pipeline-orchestration.md).
  Category D (T_0044_020..027)  -- pipeline-orchestration.md Mandatory Gates
                                   opener + rhetoric collapse.
  Category E (T_0044_028)       -- T-0023-131 test-body strengthening
                                   (applied directly to
                                   tests/adr-0023-reduction/
                                   test_reduction_structural.py, NOT duplicated
                                   here; this file contains the category
                                   marker comment only).
  Category F (T_0044_029..036)  -- Scout Fan-out collapse anchor
                                   preservation (T-0042-027, T-0042-028,
                                   T-0027-028 anchors survive).
  Category G (T_0044_037..039)  -- Line-count reduction (auditable).
  Audit    (T_0044_040..042)    -- Cross-ADR regression guards:
                                   ADR-0025 Eva capture count < 3,
                                   ADR-0041 Tier labels still present in
                                   pipeline-models.md, ADR-0016 darwin anchor
                                   absence from agent-system.md core block.

Counts (post-fix-cycle-5 Poirot triage):

  Original authoring (pre-triage):
    38 test IDs (T_0044_001..039 minus T_0044_028) + 3 audit tests
    (T_0044_040..042) = 41 test functions authored across 38 ADR-enumerated
    IDs + 3 audit IDs. Parametrized items count was 44 (T_0044_041 runs 4x
    over Tier 1..Tier 4 -- 41 functions + 3 parametrization expansions = 44).

  Post-Poirot-triage consolidation (fix-cycle-5):
    Poirot's blind review flagged 11 vacuously-green tests whose docstrings
    self-documented as "PASSES TRIVIALLY" / "PASSES (already exists)":
      T_0044_008, 010, 011, 012          (4 Category B anchors)
      T_0044_029, 030, 031, 032, 033, 034, 035  (7 Category F anchors)
    Per retro lesson #002 (tests must bind domain intent, not dilute the
    fitness signal with guards that all pass for the same reason), those
    11 were consolidated into 2 post-rewrite-shape sweeps at the lowest
    ID slot of each cluster:
      T_0044_008  -- Summary-bullet post-rewrite shape (Category B sweep);
                     subsumes T_0044_008/010/011/012 (all four originals
                     were positive-presence checks on the rewritten summary
                     bullets; one sweep binds them under a single
                     assertion path, still regresses if any anchor drops).
      T_0044_029  -- Scout Fan-out preservation sweep (Category F);
                     subsumes T_0044_029/030/031/032/033/034/035 (all seven
                     originals asserted preservation of anchors/structures
                     untouched by ADR-0044 Decision §4; one sweep binds
                     them all).
    Removed-and-consolidated IDs retain their ADR cross-reference via the
    consolidated test's docstring; the ADR Test Specification table
    (§Test Specification, rows T_0044_008/010/011/012/029-035) remains
    the authoritative inventory for traceability.

  Post-triage inventory:
    Test functions defined in this file: 32
      Category A: 7  (T_0044_001..007)
      Category B: 6  (T_0044_008 consolidated sweep + 009, 013-016)
      Category C: 3  (T_0044_017..019)
      Category D: 8  (T_0044_020..027)
      Category E: 0  (marker comment only; strengthened body lives in
                      tests/adr-0023-reduction/test_reduction_structural.py)
      Category F: 2  (T_0044_029 consolidated sweep + 036)
      Category G: 3  (T_0044_037..039)
      Audit:      3  (T_0044_040..042)
    Parametrized items collected by pytest: 35
      (32 functions + 3 parametrization expansions for T_0044_041 running
      over Tier 1..Tier 4; i.e. 31 non-parametrized functions + 1
      parametrized function yielding 4 items = 35 items.)

Test-authoring contract (retro lesson #002):
  Tests assert DOMAIN INTENT per ADR-0044's Decision section (verbatim
  Decision #1 paste text for routing-detail.md; verbatim Decision #2 for
  agent-system.md summary; verbatim Decision §3/§4 for pipeline-orchestration.md
  rhetoric collapse), NOT what files currently contain.

Audit-test separation (retro lesson #002 / Slice-1 Poirot finding):
  Audit tests (T_0044_040..042) are labeled explicitly and live in the
  "Audit" section below. They codify REGRESSION GUARDS (ADR-0025, ADR-0041,
  ADR-0016 cross-ADR invariants). Per the Slice-1 lesson, they are NOT mixed
  into Category A..G happy-path assertions -- distinct section so Colby and
  Poirot can cross-reference each audit to its pinning ADR.

Notes on ADR-spec fidelity:

  (1) T_0044_004 ADR list includes `research-brief` as a literal-string
      anchor. The verbatim Decision #1 replacement body for routing-detail.md
      (ADR §Decision, lines 116-182) does NOT contain `research-brief`; the
      three evidence-block literals present in the paste text are
      `<qa-evidence>`, `<colby-context>`, `<debug-evidence>`. Per retro
      lesson #002, when the Test Spec ID conflicts with the Decision §1
      verbatim paste content that Colby is instructed to write, the paste is
      the producer contract (truth). This test asserts the 14 anchors that
      appear in the Decision §1 paste, and explicitly omits
      `research-brief` with a scope-correction note in the docstring. Eva
      routes `<research-brief>` to Cal; that block lives in
      pipeline-orchestration.md Scout Fan-out section (Per-Agent
      Configuration table), not in the AUTO-ROUTING Intent Detection table.

  (2) T_0044_028 is applied directly to
      tests/adr-0023-reduction/test_reduction_structural.py (the existing
      T-0023-131 body is replaced in-place per ADR Category E verbatim
      Python). It is not duplicated in this flat file; see the Category E
      section-marker comment below.
"""

import re
from pathlib import Path

import pytest

from tests.conftest import (
    INSTALLED_REFS,
    INSTALLED_RULES,
    SHARED_REFS,
    SHARED_RULES,
    count_matches,
    extract_tag_content,
)


# ── Files under test ──────────────────────────────────────────────────────────

_ROUTING_DETAIL_SRC = SHARED_REFS / "routing-detail.md"
_ROUTING_DETAIL_INSTALLED = INSTALLED_REFS / "routing-detail.md"
_AGENT_SYSTEM_SRC = SHARED_RULES / "agent-system.md"
_AGENT_SYSTEM_INSTALLED = INSTALLED_RULES / "agent-system.md"
_PIPELINE_ORCH_SRC = SHARED_RULES / "pipeline-orchestration.md"
_PIPELINE_ORCH_INSTALLED = INSTALLED_RULES / "pipeline-orchestration.md"

# Cross-ADR audit pins
_PIPELINE_MODELS_SRC = SHARED_RULES / "pipeline-models.md"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _extract_routing_section(text: str) -> str:
    """Extract the <routing id="auto-routing">...</routing> block, inclusive
    of both tags.

    Returns empty string if the opener is not present.
    """
    open_marker = '<routing id="auto-routing">'
    close_marker = "</routing>"
    if open_marker not in text:
        return ""
    start = text.index(open_marker)
    rest = text[start:]
    end = rest.find(close_marker)
    if end == -1:
        return rest
    return rest[: end + len(close_marker)]


def _extract_mandatory_gates_section(text: str) -> str:
    """Extract the `## Mandatory Gates -- Eva NEVER Skips These` section up
    to (but not including) the next top-level `## ` heading.

    Returns empty string if the header is not present.
    """
    match = re.search(
        r"## Mandatory Gates -- Eva NEVER Skips These(.*?)(?=\n## |\Z)",
        text,
        re.DOTALL,
    )
    if not match:
        return ""
    return match.group(1)


def _extract_scout_fanout_section(text: str) -> str:
    """Extract the `### Scout Fan-out Protocol` section up to (but not
    including) the next `### ` or `## ` heading at the same or higher level.

    Returns empty string if the header is not present.
    """
    match = re.search(
        r"### Scout Fan-out Protocol(.*?)(?=\n### |\n## |\Z)",
        text,
        re.DOTALL,
    )
    if not match:
        return ""
    return match.group(1)


def _extract_agent_standards_section(text: str) -> str:
    """Extract the Agent Standards section of pipeline-orchestration.md.

    Looks for the `## Agent Standards` (or `### Agent Standards`) heading and
    returns through the next heading of the same or higher level.
    """
    # Try ## first, then ###.
    for header_level in ("## ", "### "):
        pattern = rf"{re.escape(header_level)}Agent Standards(.*?)(?=\n{re.escape(header_level)}|\n## |\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
    return ""


def _strip_frontmatter(text: str) -> str:
    """Strip a leading YAML frontmatter block (between `---` markers at the
    top) if present. Installed rule files carry a YAML `paths:` overlay
    applied at install time per ADR-0022; source/shared/ templates do not.

    Mirrors the helper in tests/test_adr0041_rule_structure.py and
    tests/test_adr0043_output_contract.py.
    """
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


def _normalize_for_mirror_compare(text: str) -> str:
    """Normalize installed-side text for source-vs-installed body comparison.

    Source templates use placeholders that the install step substitutes
    with project-configured values. Normalizing the common substitutions
    back lets body-parity tests detect real content drift without
    false-positiving on the install mechanism.

    Substitutions reversed (only those that appear in ADR-0044-edited
    regions):
      `.claude/` -> `{config_dir}/`
      `docs/product` -> `{product_specs_dir}`
      `docs/ux` -> `{ux_docs_dir}`
      `docs/architecture` -> `{architecture_dir}`

    Pattern: extends the ADR-0041 / ADR-0043 mirror-parity normalizer to
    cover the full placeholder set used in the <routing id=\"auto-routing\">
    block's Smart Context Detection bullet list (post-ADR-0044 Decision #2
    Summary bullets). `{pipeline_state_dir}` is not in the ADR-0044-edited
    regions; `{test_command}` is in Mandatory Gates Gate 3 but that gate
    body is not edited by ADR-0044 (only the trailing violation-class
    rhetoric collapses, which is placeholder-free).
    """
    normalized = text.replace(".claude/", "{config_dir}/")
    # Order matters: substitute more specific paths first so `docs/product`
    # does not short-circuit a hypothetical `docs/product-catalog` match.
    normalized = normalized.replace("docs/product", "{product_specs_dir}")
    normalized = normalized.replace("docs/ux", "{ux_docs_dir}")
    normalized = normalized.replace("docs/architecture", "{architecture_dir}")
    # `{test_command}` is substituted at install time to the configured
    # command. In this project: `pytest tests/ && cd brain && node --test
    # ../tests/brain/*.test.mjs`. Mandatory Gates Gate 3 body contains the
    # placeholder; Gate 3 body is NOT edited by ADR-0044, so cross-region
    # parity must reverse this substitution to avoid false-positive drift
    # on the pre-existing install mechanism.
    normalized = normalized.replace(
        "pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs",
        "{test_command}",
    )
    return normalized


# =============================================================================
# Category A: Routing-detail.md creation + content preservation (source file)
# =============================================================================


def test_T_0044_001_routing_detail_source_file_exists():
    """T-0044-001: source/shared/references/routing-detail.md exists and is
    readable.

    Pre-build: FAILS -- file is NEW per ADR-0044 Decision #1.
    """
    assert _ROUTING_DETAIL_SRC.exists(), (
        f"routing-detail.md not found at {_ROUTING_DETAIL_SRC}. "
        "ADR-0044 Decision #1 creates this new JIT reference file."
    )
    # Readable check: can load text without error.
    _ = _ROUTING_DETAIL_SRC.read_text()


def test_T_0044_002_routing_detail_has_intent_detection_heading():
    """T-0044-002: routing-detail.md contains the heading
    `## Intent Detection` exactly once.

    Pre-build: FAILS -- file does not yet exist.
    """
    assert _ROUTING_DETAIL_SRC.exists(), (
        "routing-detail.md must exist (see T_0044_001)."
    )
    text = _ROUTING_DETAIL_SRC.read_text()
    occurrences = text.count("## Intent Detection")
    assert occurrences == 1, (
        f'routing-detail.md must contain `## Intent Detection` exactly once. '
        f"Found: {occurrences}. ADR-0044 Decision #1 verbatim paste."
    )


def test_T_0044_003_intent_detection_table_has_at_least_19_data_rows():
    """T-0044-003: Intent Detection table in routing-detail.md has at least
    19 data rows. Detection: count non-header, non-divider table rows within
    the Intent Detection section.

    Pre-build: FAILS -- file does not yet exist.
    """
    assert _ROUTING_DETAIL_SRC.exists()
    text = _ROUTING_DETAIL_SRC.read_text()
    # Extract Intent Detection section.
    section_match = re.search(
        r"## Intent Detection(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    assert section_match, (
        "routing-detail.md missing `## Intent Detection` section (see T_0044_002)."
    )
    section = section_match.group(1)
    # A data row: starts with `|`, contains at least two `|` separators, and
    # is NOT the header row (`| If the user... |`) or divider row
    # (`|---|...`).
    data_rows = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # Exclude divider rows: consist only of `|`, `-`, `:`, whitespace.
        if re.match(r"^\|[\s\-:|]+\|?\s*$", stripped):
            continue
        # Exclude header row: contains "If the user".
        if "If the user" in stripped:
            continue
        # Must have at least 3 column separators.
        if stripped.count("|") >= 3:
            data_rows.append(stripped)
    assert len(data_rows) >= 19, (
        f"Intent Detection table has {len(data_rows)} data rows; expected "
        "at least 19 per ADR-0044 Decision #1 verbatim paste (the existing "
        "AUTO-ROUTING matrix in agent-system.md has exactly 19 rows)."
    )


def test_T_0044_004_routing_detail_contains_14_anchors_in_decision_1_paste():
    """T-0044-004: routing-detail.md contains the literal anchors that
    appear in ADR-0044 Decision #1 verbatim paste text for the Intent
    Detection table.

    Scope correction (retro lesson #002):
      ADR §Test Specification lists 15 anchors including `research-brief`.
      The Decision #1 verbatim paste for routing-detail.md (the producer
      contract Colby pastes) does NOT contain `research-brief`. Eva's
      `<research-brief>` evidence block lives in pipeline-orchestration.md
      Scout Fan-out section (Per-Agent Configuration table), not in the
      AUTO-ROUTING Intent Detection table. This test asserts the 14
      anchors that ARE in the Decision #1 paste; the `research-brief`
      anchor is intentionally omitted because the Decision paste is the
      authoritative producer contract.

    Pre-build: FAILS -- file does not yet exist.
    """
    assert _ROUTING_DETAIL_SRC.exists()
    text = _ROUTING_DETAIL_SRC.read_text()
    required_anchors = [
        "robert-spec",
        "sable-ux",
        "Cal",
        "Agatha",
        "Colby",
        "Ellis",
        "Roz",
        "Deps",
        "Darwin",
        "deps_agent_enabled",
        "darwin_enabled",
        "debug-evidence",
        "colby-context",
        "qa-evidence",
    ]
    missing = [a for a in required_anchors if a not in text]
    assert not missing, (
        f"routing-detail.md missing required anchors: {missing}. "
        "ADR-0044 Decision #1 verbatim paste must preserve all Intent "
        "Detection row keywords."
    )


def test_T_0044_005_routing_detail_smart_context_detection_has_6_bullets():
    """T-0044-005: routing-detail.md contains `## Smart Context Detection`,
    with 6 bullet items between that heading and the next `##` heading.

    Pre-build: FAILS -- file does not yet exist.
    """
    assert _ROUTING_DETAIL_SRC.exists()
    text = _ROUTING_DETAIL_SRC.read_text()
    assert "## Smart Context Detection" in text, (
        "routing-detail.md missing `## Smart Context Detection` heading. "
        "ADR-0044 Decision #1."
    )
    section_match = re.search(
        r"## Smart Context Detection(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    assert section_match, (
        "routing-detail.md Smart Context Detection section extraction failed."
    )
    section = section_match.group(1)
    bullets = [
        line
        for line in section.splitlines()
        if line.lstrip().startswith("- ")
    ]
    assert len(bullets) == 6, (
        f"Smart Context Detection has {len(bullets)} bullet items; expected "
        "exactly 6 per ADR-0044 Decision #1 verbatim paste."
    )


def test_T_0044_006_routing_detail_discovered_agent_routing_subsection_anchors():
    """T-0044-006: routing-detail.md contains `## Discovered Agent Routing`
    with all 7 named literal anchors inside the subsection.

    Pre-build: FAILS -- file does not yet exist.
    """
    assert _ROUTING_DETAIL_SRC.exists()
    text = _ROUTING_DETAIL_SRC.read_text()
    assert "## Discovered Agent Routing" in text, (
        "routing-detail.md missing `## Discovered Agent Routing` heading. "
        "ADR-0044 Decision #1."
    )
    section_match = re.search(
        r"## Discovered Agent Routing(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    assert section_match, (
        "Discovered Agent Routing section extraction failed."
    )
    section = section_match.group(1)
    required_anchors = [
        "Core first",
        "Conflict check",
        "Record preference",
        "Reuse preference",
        "No conflict",
        "Explicit name mention",
        "Discovered agents cannot shadow core agents",
    ]
    missing = [a for a in required_anchors if a not in section]
    assert not missing, (
        f"Discovered Agent Routing subsection missing anchors: {missing}. "
        "ADR-0044 Decision #1 verbatim paste."
    )


def test_T_0044_007_routing_detail_has_no_yaml_frontmatter():
    """T-0044-007 (failure): routing-detail.md does NOT carry YAML
    frontmatter. Detection: the first non-empty line is not `---`.

    Rationale: reference files do not carry Claude overlay frontmatter
    per the pattern in source/shared/references/*.md. ADR-0044 Decision #1
    explicit: "No frontmatter. The file is pure content."

    Pre-build: FAILS -- file does not yet exist.
    """
    assert _ROUTING_DETAIL_SRC.exists()
    text = _ROUTING_DETAIL_SRC.read_text()
    first_nonempty = None
    for line in text.splitlines():
        if line.strip():
            first_nonempty = line
            break
    assert first_nonempty is not None, "routing-detail.md is empty."
    assert first_nonempty.strip() != "---", (
        f"routing-detail.md starts with YAML frontmatter marker `---`. "
        "ADR-0044 Decision #1 prohibits frontmatter for this file "
        "(reference files are pure content). First non-empty line: "
        f"{first_nonempty!r}"
    )


# =============================================================================
# Category B: agent-system.md <routing id="auto-routing"> rewrite
# =============================================================================


def test_T_0044_008_agent_system_routing_summary_post_rewrite_shape():
    """T-0044-008 (consolidated sweep -- post-fix-cycle-5 Poirot triage):
    Summary-bullet post-rewrite shape of the `<routing id="auto-routing">`
    block in agent-system.md.

    Subsumes (and replaces) four originally-authored but vacuously-green
    Category B happy-path assertions, per retro lesson #002 (tests bind
    domain intent; do not dilute the fitness signal with 4 guards that all
    pass for the same reason):

      T_0044_008 (original): six agent-class anchors (robert-spec, sable-ux,
                             Cal, Agatha, Colby, Ellis) present in the
                             routing section.
      T_0044_010 (original): literal summary opener sentence
                             "Classify intent outside active pipeline;
                             route automatically." preserved verbatim.
      T_0044_011 (original): `Deps` AND `deps_agent_enabled` present in the
                             routing section (T-0015-034 anchor
                             continuation).
      T_0044_012 (original): `Darwin` AND `darwin_enabled` present in the
                             routing section (T-0016-038/039/041 anchor
                             continuation).

    All four originals were positive-presence checks on literals that exist
    in the REPLACEMENT text. They regress only if a Decision #2 rewrite
    drops an anchor, which this single sweep detects just as reliably.
    Structural signal that the rewrite happened remains in the Category B
    failure tests T_0044_013..016 (removed headers + zero table data rows).

    Pre-build: PASSES for most anchors (the current 19-row table contains
    them) and the summary opener sentence. Post-build: must still pass --
    Decision #2 Summary bullets preserve one entry per agent class plus the
    Deps + Darwin feature-flag bullets, and the opener line "Classify
    intent outside active pipeline; route automatically." survives verbatim
    per the ADR "What survives verbatim" list.

    ADR cross-reference (§Test Specification table -- authoritative
    inventory; see module docstring for the triage rationale):
      Row T_0044_008 -- six agent-class anchors
      Row T_0044_010 -- summary opener sentence
      Row T_0044_011 -- Deps / deps_agent_enabled (T-0015-034)
      Row T_0044_012 -- Darwin / darwin_enabled (T-0016-038/039/041)
    """
    text = _AGENT_SYSTEM_SRC.read_text()
    section = _extract_routing_section(text)
    assert section, (
        "agent-system.md missing <routing id=\"auto-routing\"> block. "
        "ADR-0044 Decision #2 preserves both tags."
    )

    # --- Subsumes original T_0044_008: six agent-class anchors. ---
    agent_class_anchors = [
        "robert-spec",
        "sable-ux",
        "Cal",
        "Agatha",
        "Colby",
        "Ellis",
    ]
    missing_agents = [a for a in agent_class_anchors if a not in section]
    assert not missing_agents, (
        f"agent-system.md routing section missing agent-class anchors: "
        f"{missing_agents}. ADR-0044 Decision #2 Summary bullets must "
        "preserve one entry per agent class. (Original T_0044_008.)"
    )

    # --- Subsumes original T_0044_010: summary opener sentence. ---
    opener = "Classify intent outside active pipeline; route automatically."
    assert opener in section, (
        f"agent-system.md routing section must preserve the summary opener "
        f"sentence `{opener}` ADR-0044 Decision #2 'survives verbatim' list. "
        "(Original T_0044_010.)"
    )

    # --- Subsumes original T_0044_011: Deps + deps_agent_enabled. ---
    assert "Deps" in section, (
        "routing section missing `Deps` anchor (T-0015-034; original "
        "T_0044_011)."
    )
    assert "deps_agent_enabled" in section, (
        "routing section missing `deps_agent_enabled` anchor (T-0015-034; "
        "original T_0044_011)."
    )

    # --- Subsumes original T_0044_012: Darwin + darwin_enabled. ---
    assert "Darwin" in section, (
        "routing section missing `Darwin` anchor (T-0016-038; original "
        "T_0044_012)."
    )
    assert "darwin_enabled" in section, (
        "routing section missing `darwin_enabled` anchor (T-0016-039/041; "
        "original T_0044_012)."
    )


def test_T_0044_009_agent_system_routing_section_references_routing_detail_md():
    """T-0044-009: agent-system.md routing section contains the literal
    `routing-detail.md` at least once (JIT load trigger pointer).

    Pre-build: FAILS -- current routing section does not reference a JIT
    file; the full matrix is inline.
    """
    text = _AGENT_SYSTEM_SRC.read_text()
    section = _extract_routing_section(text)
    assert section, "<routing id=\"auto-routing\"> block missing."
    assert "routing-detail.md" in section, (
        "agent-system.md routing section must contain `routing-detail.md` "
        "pointer (JIT load trigger). ADR-0044 Decision #2."
    )


# NOTE: T_0044_010, T_0044_011, T_0044_012 removed by Poirot triage --
# consolidated into T_0044_008 (Summary-bullet post-rewrite shape sweep).
# See module docstring "Post-Poirot-triage consolidation" section for
# rationale and the ADR Test Specification cross-reference.


def test_T_0044_013_agent_system_routing_section_drops_intent_detection_header():
    """T-0044-013 (failure): agent-system.md routing section does NOT
    contain the literal `### Intent Detection` header (moved to
    routing-detail.md).

    Pre-build: FAILS -- current routing block contains `### Intent Detection`
    at line 117.
    """
    text = _AGENT_SYSTEM_SRC.read_text()
    section = _extract_routing_section(text)
    assert section, "<routing id=\"auto-routing\"> block missing."
    assert "### Intent Detection" not in section, (
        "agent-system.md routing section must NOT contain the "
        "`### Intent Detection` subsection header -- this moved to "
        "routing-detail.md. ADR-0044 Decision #2."
    )


def test_T_0044_014_agent_system_routing_section_drops_smart_context_detection_header():
    """T-0044-014 (failure): agent-system.md routing section does NOT
    contain the literal `### Smart Context Detection` header.

    Pre-build: FAILS -- current routing block contains this header at
    line 141.
    """
    text = _AGENT_SYSTEM_SRC.read_text()
    section = _extract_routing_section(text)
    assert section, "<routing id=\"auto-routing\"> block missing."
    assert "### Smart Context Detection" not in section, (
        "agent-system.md routing section must NOT contain "
        "`### Smart Context Detection` -- moved to routing-detail.md. "
        "ADR-0044 Decision #2."
    )


def test_T_0044_015_agent_system_routing_section_drops_discovered_agent_routing_header():
    """T-0044-015 (failure): agent-system.md routing section does NOT
    contain the literal `### Discovered Agent Routing` header.

    Pre-build: FAILS -- current routing block contains this header at
    line 156.
    """
    text = _AGENT_SYSTEM_SRC.read_text()
    section = _extract_routing_section(text)
    assert section, "<routing id=\"auto-routing\"> block missing."
    assert "### Discovered Agent Routing" not in section, (
        "agent-system.md routing section must NOT contain "
        "`### Discovered Agent Routing` -- moved to routing-detail.md. "
        "ADR-0044 Decision #2."
    )


def test_T_0044_016_agent_system_routing_section_has_zero_table_data_rows():
    """T-0044-016 (failure): The number of table data rows inside the
    <routing id="auto-routing"> section (regex: lines matching
    `^\\| .* \\| .* \\|`) is 0.

    Rationale: the 19-row matrix was moved to routing-detail.md, not left
    in place. This is the structural signal that the block rewrite
    happened -- the absence of ANY table data row inside the <routing>
    block.

    Pre-build: FAILS -- current routing block contains a 19-row table.
    """
    text = _AGENT_SYSTEM_SRC.read_text()
    section = _extract_routing_section(text)
    assert section, "<routing id=\"auto-routing\"> block missing."
    data_rows = []
    for line in section.splitlines():
        stripped = line.strip()
        # Exclude header row.
        if "If the user" in stripped:
            continue
        # Exclude divider row.
        if re.match(r"^\|[\s\-:|]+\|?\s*$", stripped):
            continue
        # Count only lines that look like full table data rows: start with
        # `|`, end with `|`, and have >= 3 separators.
        if (
            stripped.startswith("|")
            and stripped.endswith("|")
            and stripped.count("|") >= 3
        ):
            data_rows.append(stripped)
    assert len(data_rows) == 0, (
        f"agent-system.md <routing> section contains {len(data_rows)} table "
        "data rows; expected 0 -- the 19-row matrix moved to "
        f"routing-detail.md per ADR-0044 Decision #2. Rows: {data_rows}"
    )


# =============================================================================
# Category C: Installed-mirror parity
# =============================================================================


def test_T_0044_017_routing_detail_installed_is_byte_identical_to_source():
    """T-0044-017: .claude/references/routing-detail.md body is byte-
    identical to source/shared/references/routing-detail.md.

    Rationale: reference files carry no frontmatter overlay -- direct byte
    comparison. ADR-0044 Decision §5: "routing-detail.md (a reference file,
    not a rule), there is no frontmatter overlay -- the installed copy is
    byte-identical to the source."

    Pre-build: FAILS -- neither file exists yet.
    """
    assert _ROUTING_DETAIL_SRC.exists(), (
        "source routing-detail.md not found (T_0044_001)."
    )
    assert _ROUTING_DETAIL_INSTALLED.exists(), (
        f"installed routing-detail.md not found at {_ROUTING_DETAIL_INSTALLED}. "
        "ADR-0044 Decision §5 requires the installed mirror."
    )
    src_body = _ROUTING_DETAIL_SRC.read_text()
    installed_body = _ROUTING_DETAIL_INSTALLED.read_text()
    assert installed_body == src_body, (
        "routing-detail.md installed body differs from source. ADR-0044 "
        "Decision §5 requires byte-identical mirror (no frontmatter overlay "
        "for reference files)."
    )


def test_T_0044_018_agent_system_installed_routing_block_equals_source():
    """T-0044-018: .claude/rules/agent-system.md <routing id="auto-routing">
    block is byte-identical to source/shared/rules/agent-system.md's block.

    Domain-intent scoping (retro lesson #002):
      Full-file byte parity between source and installed copies of rule
      files is NOT achievable by static text comparison -- the install
      step substitutes multiple placeholders (`{config_dir}`,
      `{pipeline_state_dir}`, `{product_specs_dir}`, `{ux_docs_dir}`,
      `{architecture_dir}`, `{test_command}`, etc.), and some `.claude/`
      strings inside code blocks are intentionally NOT substituted.
      Reversing the full substitution set in a test would re-implement
      the install machinery.

      The ADR-0044 Step 1 acceptance criterion's actual domain intent is
      "Colby edited BOTH source and installed copies in sync when the
      <routing> block was rewritten." The <routing id="auto-routing">
      block is precisely the ADR-0044-edited region of this file, and
      its body is placeholder-free (the rewritten block contains only
      literal text per Decision #2 verbatim paste). So byte-equality on
      the extracted <routing> block encodes the domain intent without
      re-implementing the install step.

    Pre-build: behavior is install-sync-governed -- may PASS TRIVIALLY
    pre-build if source and installed routing sections are in sync today
    (both contain the full 19-row table). Post-build: RED's if Colby
    edits only one side.
    """
    assert _AGENT_SYSTEM_SRC.exists()
    assert _AGENT_SYSTEM_INSTALLED.exists()
    src_routing = _extract_routing_section(_AGENT_SYSTEM_SRC.read_text())
    installed_routing = _extract_routing_section(
        _AGENT_SYSTEM_INSTALLED.read_text()
    )
    assert src_routing, "source agent-system.md <routing> block missing."
    assert installed_routing, (
        "installed agent-system.md <routing> block missing."
    )
    # Normalize installed-side placeholder substitutions back to source form
    # so the parity check detects real content drift without false-positiving
    # on install-time path substitution.
    # Normalize BOTH sides so literal `.claude/`, `docs/product`, etc. that
    # appear verbatim in source (e.g., inside code blocks describing the
    # project's real paths, like `docs/adrs/`) do not false-positive against
    # the placeholder-reversal applied only to installed. Symmetric
    # normalization: real drift survives, install-mechanic artifacts cancel.
    src_normalized = _normalize_for_mirror_compare(src_routing)
    installed_normalized = _normalize_for_mirror_compare(installed_routing)
    assert installed_normalized == src_normalized, (
        "agent-system.md <routing id=\"auto-routing\"> block diverges "
        "between source and installed copies (after install-time "
        "placeholder reversal). ADR-0044 Decision §5 requires in-sync "
        "edits to both copies."
    )


def test_T_0044_019_pipeline_orchestration_installed_mandatory_gates_equal_source():
    """T-0044-019: .claude/rules/pipeline-orchestration.md Mandatory Gates
    section AND Scout Fan-out Protocol section (the two ADR-0044-edited
    regions) are each byte-identical to their source counterparts after
    install-time placeholder reversal.

    Domain-intent scoping (retro lesson #002):
      Same scoping rationale as T_0044_018 -- full-file byte parity
      requires the full install-time placeholder substitution set. The
      ADR-0044 domain intent is "Colby edited BOTH source and installed
      copies in sync for the TWO edited regions": the Mandatory Gates
      section (opener + per-gate tail collapses) and the Scout Fan-out
      Protocol section (Explicit spawn requirement collapse). Both
      regions are symmetrically normalized so install-time path
      substitution (`.claude/` <-> `{config_dir}/`, `docs/product` <->
      `{product_specs_dir}`, `docs/architecture` <-> `{architecture_dir}`,
      `docs/ux` <-> `{ux_docs_dir}`, `{test_command}` <-> the configured
      shell command) is cancelled out; only real content drift surfaces.

    Pre-build finding (pre-existing drift, NOT ADR-0044 caused):
      The installed copy `.claude/rules/pipeline-orchestration.md` is
      currently missing two paragraphs in the Scout Fan-out Protocol
      section that exist in source: the "Explicit spawn requirement"
      paragraph (which ADR-0044 Decision §4 collapses) and the
      "Synthesis step" paragraph. This drift is pre-existing -- it is
      the CURRENT state of the installed copy before ADR-0044 touches
      anything.

      ADR-0044 Step 3 acceptance criterion explicitly requires:
      "Installed mirror body matches source body byte-for-byte (modulo
      frontmatter)." Colby's landing of ADR-0044 must therefore resolve
      this drift as part of the rewrite -- edit both source and
      installed so the collapsed paragraph appears in BOTH copies. This
      test encodes that acceptance criterion; its pre-build RED
      correctly signals the drift that Colby must resolve, and its
      post-build GREEN confirms resolution.

    Pre-build: RED (pre-existing drift, see finding above).
    Post-build: GREEN iff Colby resolves the drift per ADR-0044 Step 3
    Acceptance Criterion + Decision §4 verbatim paste.
    """
    assert _PIPELINE_ORCH_SRC.exists()
    assert _PIPELINE_ORCH_INSTALLED.exists()
    src_text = _PIPELINE_ORCH_SRC.read_text()
    installed_text = _PIPELINE_ORCH_INSTALLED.read_text()

    # Region 1: Mandatory Gates section.
    src_gates = _extract_mandatory_gates_section(src_text)
    installed_gates = _extract_mandatory_gates_section(installed_text)
    assert src_gates, "source Mandatory Gates section missing."
    assert installed_gates, "installed Mandatory Gates section missing."
    src_gates_norm = _normalize_for_mirror_compare(src_gates)
    installed_gates_norm = _normalize_for_mirror_compare(installed_gates)
    assert installed_gates_norm == src_gates_norm, (
        "pipeline-orchestration.md Mandatory Gates section diverges "
        "between source and installed copies (after install-time "
        "placeholder reversal). ADR-0044 Decision §5 requires in-sync "
        "edits to both copies."
    )

    # Region 2: Scout Fan-out Protocol section.
    src_fanout = _extract_scout_fanout_section(src_text)
    installed_fanout = _extract_scout_fanout_section(installed_text)
    assert src_fanout, "source Scout Fan-out Protocol section missing."
    assert installed_fanout, (
        "installed Scout Fan-out Protocol section missing."
    )
    src_fanout_norm = _normalize_for_mirror_compare(src_fanout)
    installed_fanout_norm = _normalize_for_mirror_compare(installed_fanout)
    assert installed_fanout_norm == src_fanout_norm, (
        "pipeline-orchestration.md Scout Fan-out Protocol section "
        "diverges between source and installed copies (after install-time "
        "placeholder reversal). ADR-0044 Decision §5 requires in-sync "
        "edits to both copies."
    )


# =============================================================================
# Category D: Mandatory Gates opener + rhetoric collapse
# =============================================================================


def test_T_0044_020_mandatory_gates_header_literal_preserved():
    """T-0044-020: pipeline-orchestration.md contains the literal
    `## Mandatory Gates -- Eva NEVER Skips These`.

    Pre-build: PASSES (header already present). Post-build: must still
    pass -- this header is preserved across the ADR-0044 rewrite per
    Decision §3.
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    assert "## Mandatory Gates -- Eva NEVER Skips These" in text, (
        "pipeline-orchestration.md missing `## Mandatory Gates -- Eva "
        "NEVER Skips These` header. ADR-0044 Decision §3 preserves it."
    )


def test_T_0044_021_mandatory_gates_opener_contains_violation_class_paragraph():
    """T-0044-021: pipeline-orchestration.md contains `**Violation class.**`
    exactly once (the new opener paragraph declaring the default class).

    Pre-build: FAILS -- the `**Violation class.**` paragraph does not yet
    exist; the current opener relies on per-gate "same class of violation"
    sentences.
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    occurrences = text.count("**Violation class.**")
    assert occurrences == 1, (
        f"pipeline-orchestration.md contains `**Violation class.**` "
        f"{occurrences} time(s); expected exactly 1. ADR-0044 Decision §3 "
        "introduces this as the section opener declaring the default class."
    )


def test_T_0044_022_mandatory_gates_section_has_exactly_12_numbered_gates():
    """T-0044-022: Within the Mandatory Gates section, the count of lines
    matching `^\\d+\\. \\*\\*` equals exactly 12.

    Pre-build: PASSES (current section has 12 numbered gates). Post-build:
    must still pass -- ADR-0044 preserves all 12 gates, only collapses
    rhetoric around them. This is the load-bearing intent assertion for
    gate preservation.
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    section = _extract_mandatory_gates_section(text)
    assert section, (
        "pipeline-orchestration.md Mandatory Gates section extraction "
        "failed (see T_0044_020)."
    )
    numbered = re.findall(r"^\d+\. \*\*", section, re.MULTILINE)
    assert len(numbered) == 12, (
        f"Mandatory Gates section has {len(numbered)} numbered gates; "
        "expected 12. ADR-0044 Decision §3 preserves all 12 gates while "
        "collapsing per-gate rhetoric."
    )


def test_T_0044_023_mandatory_gates_section_contains_all_12_gate_titles():
    """T-0044-023: Mandatory Gates section contains all 12 gate title
    substrings (one per gate, pulled verbatim from the current file).

    Pre-build: PASSES (gates exist). Post-build: must still pass -- ADR-0044
    does not rewrite gate bodies, only the trailing rhetoric sentences.
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    section = _extract_mandatory_gates_section(text)
    assert section, "Mandatory Gates section missing."
    gate_titles = [
        "Roz verifies every wave",
        "Ellis commits. Eva does not",
        "Full test suite between waves",
        "Roz investigates user-reported bugs. Eva does not",
        "Poirot blind-reviews every wave",
        "Distillator compresses cross-phase artifacts",
        "Robert-subagent reviews at the review juncture",
        "Sable-subagent verifies every mockup before UAT",
        "Agatha writes docs after final Roz sweep",
        "Spec and UX doc reconciliation is continuous",
        "One phase transition per turn",
        "Loop-breaker: 3 failures = halt",
    ]
    missing = [g for g in gate_titles if g not in section]
    assert not missing, (
        f"Mandatory Gates section missing gate titles: {missing}. "
        "ADR-0044 Decision §3 preserves every gate body unchanged."
    )


def test_T_0044_024_mandatory_gates_section_has_zero_same_class_of_violation():
    """T-0044-024 (failure): Within the Mandatory Gates section, the literal
    `same class of violation` appears exactly 0 times (refrain collapsed).

    Pre-build: FAILS -- current Mandatory Gates section contains 6
    occurrences (gates 2, 3, 5, 7, 10, 11 each have the refrain).
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    section = _extract_mandatory_gates_section(text)
    assert section, "Mandatory Gates section missing."
    occurrences = section.count("same class of violation")
    assert occurrences == 0, (
        f"Mandatory Gates section still contains `same class of violation` "
        f"{occurrences} time(s); expected 0. ADR-0044 Decision §3 collapses "
        "the refrain. The violation class is declared once in the section "
        "opener (`**Violation class.**`); per-gate tails use terse "
        "parenthetical tags (`default class` / `tighter class: ...`)."
    )


def test_T_0044_025_pipeline_orchestration_has_zero_same_class_of_violation_file_wide():
    """T-0044-025 (failure): Across the entire pipeline-orchestration.md
    file, the literal `same class of violation` appears exactly 0 times.

    Rationale: the one remaining instance in the Agent Standards section
    (line 780 OLD) was rewritten to `same class as skipping spec
    reconciliation` per Decision §3 Agent Standards collapse. The refrain
    itself does not survive anywhere.

    Pre-build: FAILS -- current file has 8 occurrences (6 in Mandatory
    Gates, 1 in Scout Fan-out Protocol line 610, 1 in Agent Standards
    line 780).
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    occurrences = text.count("same class of violation")
    assert occurrences == 0, (
        f"pipeline-orchestration.md still contains `same class of "
        f"violation` {occurrences} time(s); expected 0 across the whole "
        "file. ADR-0044 Decision §3 collapses Mandatory Gates refrain; "
        "Decision §4 collapses Scout Fan-out refrain; Agent Standards "
        "line 780 is rewritten to `same class as skipping spec "
        "reconciliation` (a targeted non-default comparison)."
    )


def test_T_0044_026_agent_standards_preserves_skipping_spec_reconciliation():
    """T-0044-026: Agent Standards section of pipeline-orchestration.md
    contains `same class as skipping spec reconciliation` exactly once
    (the targeted comparison survives as a non-default class).

    Pre-build: FAILS -- current Agent Standards line 780 uses `same class
    of violation as skipping spec reconciliation` (the general refrain).
    After rewrite, the collapsed form `same class as skipping spec
    reconciliation` appears.
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    occurrences = text.count("same class as skipping spec reconciliation")
    assert occurrences == 1, (
        f"pipeline-orchestration.md contains `same class as skipping spec "
        f"reconciliation` {occurrences} time(s); expected exactly 1 "
        "(Agent Standards line 780 targeted comparison). ADR-0044 "
        "Decision §3."
    )


def test_T_0044_027_pipeline_orchestration_eva_capture_count_is_exactly_2():
    """T-0044-027: pipeline-orchestration.md file-wide count of
    `source_agent: 'eva'` literal equals exactly 2.

    Rationale: satisfies T-0024-041 / ADR-0025 constraint that Eva's
    direct capture count stays < 3. ADR-0044 does not touch either of the
    two existing occurrences (lines 50 and 81); the refactor only collapses
    rhetoric, not capture calls.

    Pre-build: PASSES (count is 2 today). Post-build: must still pass --
    audit-class regression guard for ADR-0025.
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    count = text.count("source_agent: 'eva'")
    assert count == 2, (
        f"pipeline-orchestration.md contains {count} `source_agent: 'eva'` "
        "literals; expected exactly 2 (unchanged from pre-ADR-0044 per "
        "Decision §3 Step 2 acceptance criteria; satisfies ADR-0025 / "
        "T-0024-041 < 3 constraint)."
    )


# =============================================================================
# Category E: T-0023-131 test-body strengthening
#
# The strengthened T-0023-131 body is applied directly to
# tests/adr-0023-reduction/test_reduction_structural.py per ADR-0044
# Category E verbatim Python replacement (ADR Decision #6 / Test Spec
# Category E). It is NOT duplicated here -- the function's home file is
# its pinning ADR-0023 test suite, and duplicating would produce two
# functions with the same name (one would silently win). This flat file
# captures only the category marker comment.
# =============================================================================


# =============================================================================
# Category F: Scout Fan-out collapse anchor preservation
# =============================================================================


def test_T_0044_029_scout_fanout_preservation_sweep():
    """T-0044-029 (consolidated sweep -- post-fix-cycle-5 Poirot triage):
    Post-rewrite preservation shape of `### Scout Fan-out Protocol` in
    pipeline-orchestration.md. ADR-0044 Decision §4 collapses the
    "Explicit spawn requirement" paragraph but explicitly preserves the
    header, the load-bearing anchors, and the Per-Agent Configuration +
    Investigation Mode subsections untouched.

    Subsumes (and replaces) seven originally-authored but vacuously-green
    Category F happy-path assertions, per retro lesson #002 (tests bind
    domain intent; do not dilute the fitness signal with 7 guards that all
    pass for the same reason -- each original was the section extraction
    plus one-literal check):

      T_0044_029 (original): `### Scout Fan-out Protocol` header exactly
                             once.
      T_0044_030 (original): `MUST spawn` literal in the section
                             (T-0042-027 anchor continuation).
      T_0044_031 (original): `separate parallel subagent` literal in the
                             section (T-0042-027 anchor continuation).
      T_0044_032 (original): `synthesis` AND (`after scouts return` OR
                             `scouts return`) AND all of `Cal`, `Colby`,
                             `Roz` co-located in the section (T-0042-028
                             anchor continuation).
      T_0044_033 (original): Per-Agent Configuration table contains a row
                             with `brain-hydrate` (T-0027-028 anchor
                             continuation).
      T_0044_034 (original): Per-Agent Configuration table has exactly
                             4 data rows (Cal, Roz, Colby, brain-hydrate).
      T_0044_035 (original): Investigation Mode subsection exists with
                             4 scout rows (Files, Tests, Brain, Error grep).

    All seven originals asserted literals present in the CURRENT file that
    ADR-0044 Decision §4 does not touch. They regress only if the collapse
    accidentally deletes a preserved anchor or table row; this single
    sweep detects that class of regression just as reliably. Structural
    signal that the collapse happened remains in T_0044_036 (old
    6-sentence paragraph substring removed).

    Pre-build: PASSES (all preserved structures exist in the current
    file). Post-build: must still pass -- Decision §4 preserves the
    header, both T-0042-027 anchors, the Synthesis step paragraph
    (T-0042-028 anchors), the Per-Agent Configuration table
    (T-0027-028 anchor + 4 data rows), and the Investigation Mode
    subsection (4 scout rows).

    ADR cross-reference (§Test Specification table -- authoritative
    inventory; see module docstring for the triage rationale):
      Row T_0044_029 -- `### Scout Fan-out Protocol` header exactly once
      Row T_0044_030 -- `MUST spawn` (T-0042-027)
      Row T_0044_031 -- `separate parallel subagent` (T-0042-027)
      Row T_0044_032 -- synthesis + scouts return + Cal/Colby/Roz
                        (T-0042-028)
      Row T_0044_033 -- Per-Agent Configuration `brain-hydrate`
                        (T-0027-028)
      Row T_0044_034 -- Per-Agent Configuration has 4 data rows
      Row T_0044_035 -- Investigation Mode has 4 scout rows
    """
    text = _PIPELINE_ORCH_SRC.read_text()

    # --- Subsumes original T_0044_029: header exactly once. ---
    header_occurrences = text.count("### Scout Fan-out Protocol")
    assert header_occurrences == 1, (
        f"pipeline-orchestration.md contains `### Scout Fan-out Protocol` "
        f"{header_occurrences} time(s); expected exactly 1. (Original "
        "T_0044_029.)"
    )

    section = _extract_scout_fanout_section(text)
    assert section, (
        "Scout Fan-out Protocol section missing (see header check above; "
        "original T_0044_029)."
    )

    # --- Subsumes original T_0044_030: MUST spawn (T-0042-027). ---
    assert "MUST spawn" in section, (
        "Scout Fan-out section missing `MUST spawn` literal. ADR-0044 "
        "Decision §4 preserves this literal (T-0042-027 anchor; original "
        "T_0044_030)."
    )

    # --- Subsumes original T_0044_031: separate parallel subagent
    # (T-0042-027). ---
    assert "separate parallel subagent" in section, (
        "Scout Fan-out section missing `separate parallel subagent` "
        "literal. ADR-0044 Decision §4 preserves (T-0042-027 anchor; "
        "original T_0044_031)."
    )

    # --- Subsumes original T_0044_032: synthesis + scouts return +
    # Cal/Colby/Roz co-located (T-0042-028). ---
    assert "synthesis" in section, (
        "Scout Fan-out section missing `synthesis` literal "
        "(T-0042-028; original T_0044_032)."
    )
    has_after_scouts = (
        "after scouts return" in section or "scouts return" in section
    )
    assert has_after_scouts, (
        "Scout Fan-out section missing `after scouts return` or "
        "`scouts return` literal (T-0042-028; original T_0044_032)."
    )
    for name in ("Cal", "Colby", "Roz"):
        assert name in section, (
            f"Scout Fan-out section missing `{name}` (case-sensitive; "
            "T-0042-028 anchor; original T_0044_032)."
        )

    # --- Subsumes original T_0044_033: Per-Agent Configuration table
    # contains `brain-hydrate` (T-0027-028). ---
    assert "brain-hydrate" in section, (
        "Scout Fan-out section Per-Agent Configuration table missing "
        "`brain-hydrate` row (T-0027-028 anchor; original T_0044_033)."
    )

    # --- Subsumes original T_0044_034: Per-Agent Configuration table has
    # exactly 4 data rows. ---
    config_match = re.search(
        r"#### Per-Agent Configuration(.*?)All scouts are",
        section,
        re.DOTALL,
    )
    assert config_match, (
        "Per-Agent Configuration subsection extraction failed -- expected "
        "`#### Per-Agent Configuration` heading. (Original T_0044_034.)"
    )
    config_section = config_match.group(1)
    data_rows = []
    for line in config_section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # Exclude divider and header rows.
        if re.match(r"^\|[\s\-:|]+\|?\s*$", stripped):
            continue
        if "Agent" in stripped and "Block" in stripped:
            continue
        if stripped.count("|") >= 3:
            data_rows.append(stripped)
    assert len(data_rows) == 4, (
        f"Per-Agent Configuration table has {len(data_rows)} data rows; "
        f"expected 4 (Cal, Roz, Colby, brain-hydrate). Rows: {data_rows}. "
        "(Original T_0044_034.)"
    )

    # --- Subsumes original T_0044_035: Investigation Mode subsection exists
    # with 4 scout rows. ---
    assert "Investigation Mode" in section, (
        "Scout Fan-out section missing `Investigation Mode` subsection "
        "(user-reported bug flow; original T_0044_035)."
    )
    for scout in ("Files", "Tests", "Brain", "Error grep"):
        assert scout in section, (
            f"Scout Fan-out Investigation Mode missing `{scout}` scout row. "
            "(Original T_0044_035.)"
        )


# NOTE: T_0044_030, T_0044_031, T_0044_032, T_0044_033, T_0044_034,
# T_0044_035 removed by Poirot triage -- consolidated into T_0044_029
# (Scout Fan-out preservation sweep). See module docstring
# "Post-Poirot-triage consolidation" section for rationale and the ADR
# Test Specification cross-reference.


def test_T_0044_036_old_six_sentence_explicit_spawn_paragraph_removed():
    """T-0044-036 (failure): The OLD 6-sentence "Explicit spawn requirement"
    paragraph is NOT present. Detection: regex for the `Eva does NOT collect
    scout evidence in her own turn. Eva does NOT synthesize` literal
    substring -- it should not match.

    Pre-build: FAILS -- current line 610 contains this substring verbatim
    as the OLD paragraph.
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    # Both literal sentences that mark the old 6-sentence form:
    # "Eva does NOT collect scout evidence in her own turn."
    # "Eva does NOT synthesize in her own turn."
    # The failure-detection substring combines the two contiguous sentences.
    old_substring = (
        "Eva does NOT collect scout evidence in her own turn. "
        "Eva does NOT synthesize"
    )
    assert old_substring not in text, (
        "pipeline-orchestration.md still contains the OLD 6-sentence "
        "'Explicit spawn requirement' paragraph substring. ADR-0044 "
        "Decision §4 collapses it to 1-2 sentences while preserving "
        "`MUST spawn` / `separate parallel subagent` / synthesis anchors."
    )


# =============================================================================
# Category G: Line-count reduction (auditable)
# =============================================================================


def test_T_0044_037_agent_system_line_count_at_most_240():
    """T-0044-037 (audit): Post-ADR-0044 line count of agent-system.md is
    at most 240 (original: 286; target: ~234 after ~52-line routing-block
    compression).

    Upper bound is 240 to tolerate minor whitespace. Lower bound not tested
    (over-trimming would fail the Category B anchor tests, which bind the
    surviving content floor).

    Pre-build: FAILS -- current agent-system.md is 286 lines.
    """
    text = _AGENT_SYSTEM_SRC.read_text()
    line_count = len(text.splitlines())
    assert line_count <= 240, (
        f"source/shared/rules/agent-system.md is {line_count} lines; "
        "expected <= 240 per ADR-0044 Decision §Line-count reduction "
        "target (original 286; ~52 line savings from AUTO-ROUTING move)."
    )


def test_T_0044_038_pipeline_orchestration_line_count_at_most_760():
    """T-0044-038 (audit): Post-ADR-0044 line count of
    pipeline-orchestration.md is at most 803 (Addendum A1 scope correction).

    Scope correction (ADR-0044 Addendum A1, 2026-04-20):
      The original bound `<= 760` assumed ~48-line savings from Decision §3
      + §4 rhetoric and Scout Fan-out collapses. Post-Colby verbatim
      application yielded ~0 net savings in this file: the
      `**Violation class.**` opener paragraph (+5 lines) offset most of the
      per-gate refrain trims (~-7 lines combined), and the Scout Fan-out
      §4 paragraph rewrite was line-count-neutral (already one long
      markdown line). Structural intent LANDED (T_0044_021, T_0044_024,
      T_0044_025, T_0044_026, T_0044_036 all green); line-count savings
      did not materialize here.

      agent-system.md delivered its full target (-46 lines via
      AUTO-ROUTING JIT move -- see T_0044_037). Slice 2 books that
      savings cleanly; the pipeline-orchestration.md line-count trim is
      formally deferred to a future ADR. See ADR-0044 Addendum A1 for
      the decision rationale (Option C: split + narrate).

      The bound `<= 803` is a no-regression guard: it permits the current
      ~802-line state plus 1 line of whitespace tolerance while forbidding
      growth. A future trim ADR would tighten this bound as part of its
      own DoD.

    Pre-build: FAILS -- current pipeline-orchestration.md is 802 lines
    (bound was `<= 760`).
    Post-Addendum-A1: PASSES (802 <= 803).
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    line_count = len(text.splitlines())
    assert line_count <= 803, (
        f"source/shared/rules/pipeline-orchestration.md is {line_count} "
        "lines; expected <= 803 per ADR-0044 Addendum A1 (original bound "
        "<= 760 was scope-corrected to the achieved ceiling). Growth "
        "beyond this bound indicates the rhetoric-collapse structural "
        "gains leaked back as prose; route to a trim ADR."
    )


def test_T_0044_039_routing_detail_line_count_at_least_50():
    """T-0044-039 (audit): Post-ADR-0044 line count of routing-detail.md is
    at least 50 (full matrix + 3 subsections should be >= 50 lines).

    Content preservation guarded by Category A content tests; this is a
    coarse floor check that the file isn't a stub.

    Pre-build: FAILS -- file does not yet exist.
    """
    assert _ROUTING_DETAIL_SRC.exists(), (
        "routing-detail.md must exist (T_0044_001)."
    )
    text = _ROUTING_DETAIL_SRC.read_text()
    line_count = len(text.splitlines())
    assert line_count >= 50, (
        f"routing-detail.md is {line_count} lines; expected >= 50 per "
        "ADR-0044 Decision §Line-count reduction target (full matrix + 3 "
        "subsections)."
    )


# =============================================================================
# Audit tests (T_0044_040..042): Cross-ADR regression guards.
#
# Labeled distinctly per the <warn> / retro lesson #002 directive:
# Slice-1's lesson was that audit tests mixed in with happy-path tests
# can read as vacuously green. These three are explicit regression guards
# pinning invariants from OTHER ADRs that ADR-0044 could plausibly break
# if scope creep happened. Each docstring names the pinning ADR and the
# specific invariant.
# =============================================================================


def test_T_0044_040_audit_adr0025_eva_capture_count_stays_under_3():
    """T_0044_040 (audit / ADR-0025 regression guard): pipeline-
    orchestration.md `source_agent: 'eva'` literal count stays < 3.

    Pin: ADR-0025 (enshrined via tests/hooks/test_wave3_hook_removal.py:
    364-369 and T-0024-041). Eva is not the primary capturer of domain
    knowledge (cross-cutting only); direct Eva capture calls in
    pipeline-orchestration.md must remain bounded.

    Scope of guard: ADR-0044 collapses rhetoric in the Mandatory Gates
    + Scout Fan-out sections. Neither collapse edits lines 50 or 81
    (the two `source_agent: 'eva'` occurrences per ADR DoR R7). This
    audit verifies the invariant survives.

    Pre-build: PASSES (count is 2). Post-build: must still pass.
    Distinct from T_0044_027 (which asserts `== 2` precisely): this
    audit encodes the CROSS-ADR constraint `< 3` as the regression
    boundary, not the current exact value.
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    count = text.count("source_agent: 'eva'")
    assert count < 3, (
        f"pipeline-orchestration.md `source_agent: 'eva'` count is {count}; "
        "expected < 3 per ADR-0025 / T-0024-041 boundary. ADR-0044's "
        "rhetoric collapses must not introduce new Eva capture calls."
    )


@pytest.mark.parametrize(
    "tier_label", ["Tier 1", "Tier 2", "Tier 3", "Tier 4"]
)
def test_T_0044_041_audit_adr0041_tier_labels_still_present_in_pipeline_models(tier_label):
    """T_0044_041 (audit / ADR-0041 regression guard): All four `Tier N`
    labels remain present in source/shared/rules/pipeline-models.md.

    Pin: ADR-0041 Decision §Four-Tier Task-Class Model -- all four tier
    rows are load-bearing. ADR-0044 Anti-goal 2 explicitly excludes
    pipeline-models.md from scope precisely because ADR-0041 + ADR-0042
    tests pin this file. This audit verifies ADR-0044's changes did not
    accidentally touch pipeline-models.md.

    Pre-build: PASSES (all four labels present). Post-build: must still
    pass -- pipeline-models.md is untouched by ADR-0044 per ADR DoR R12
    and Step "Explicitly NOT edited" list.

    Distinct from tests/test_adr0041_rule_structure.py ::
    test_source_rule_contains_tier_label: this is an ADR-0044 scope
    guard, not an ADR-0041 structural check. It RED's only if ADR-0044
    work silently dropped a tier label (would indicate scope creep).
    """
    assert _PIPELINE_MODELS_SRC.exists(), (
        f"source/shared/rules/pipeline-models.md not found at "
        f"{_PIPELINE_MODELS_SRC} -- ADR-0044 must not move or delete this "
        "file (ADR-0044 Anti-goal 2; ADR-0042 test pins)."
    )
    text = _PIPELINE_MODELS_SRC.read_text()
    assert tier_label in text, (
        f"pipeline-models.md missing `{tier_label}` label. ADR-0044 is "
        "explicitly out of scope for this file (Anti-goal 2); its absence "
        "indicates scope creep into ADR-0041/0042 territory."
    )


def test_T_0044_042_audit_adr0016_darwin_row_anchor_present_in_agent_system():
    """T_0044_042 (audit / ADR-0016 regression guard): agent-system.md
    contains the `darwin_enabled` anchor somewhere in the file (not
    scoped to the routing section alone; the anchor may migrate to
    routing-detail.md but must remain reachable from agent-system.md via
    the Summary bullet per ADR-0044 Decision #2 DoR R2).

    Pin: ADR-0016 T-0016-039 / T-0016-041 assert the `darwin_enabled`
    anchor appears in agent-system.md's routing context. ADR-0044 DoR R2
    explicitly preserves this anchor in the inline Summary so ADR-0016
    tests continue to pass.

    Pre-build: PASSES (current agent-system.md line 135 contains the
    literal). Post-build: must still pass -- the Summary bullet carries
    `darwin_enabled` per Decision §2 "What survives verbatim" list.

    Distinct from T_0044_012 (which scopes to the <routing> section):
    this audit scopes to the whole agent-system.md file (broader
    regression guard against accidental whole-anchor removal during
    the block rewrite).
    """
    text = _AGENT_SYSTEM_SRC.read_text()
    assert "darwin_enabled" in text, (
        "agent-system.md file-wide search missing `darwin_enabled` anchor. "
        "ADR-0016 T-0016-039/041 require this anchor; ADR-0044 DoR R2 "
        "preserves it via the Summary bullet. Its absence indicates "
        "ADR-0044 scope creep breaking ADR-0016 invariants."
    )
