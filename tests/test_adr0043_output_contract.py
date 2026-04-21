"""ADR-0043 pre-build test assertions: Agent return condensation + filepath:line citation mandate.

All tests in this file are PRE-BUILD: they MUST FAIL against the current codebase
and PASS only after Colby implements ADR-0043. A test that passes before Colby
builds is flagged with justification in its docstring (Retro Lesson #002).

Test authoring contract (Retro Lesson #002):
  Tests assert what the files SHOULD contain per ADR-0043's Decision section
  (verbatim preamble text + verbatim `<output>` one-liners), NOT what they
  currently contain.

Coverage (28 assertions per ADR §Test Specification):
  Category A (T_0043_001..005)  -- Preamble mandate presence
  Category B (T_0043_006..010)  -- Cal `<output>` condensation
  Category C (T_0043_011..015)  -- Colby `<output>` condensation
  Category D (T_0043_016..020)  -- Roz `<output>` condensation
  Category E (T_0043_021..022)  -- Cross-reference / preamble pointer
  Category F (T_0043_023..026)  -- Installed-copy parity
  Category G (T_0043_027..028)  -- Cursor overlay untouched (scope guard)

Implementation notes on ADR-spec fidelity:

  (1) ADR T_0043_023..026 say `diff <source> <installed>` returns empty. The
      installed copies under `.claude/` carry a YAML frontmatter overlay and
      `{config_dir}` -> `.claude` placeholder substitutions applied at install
      time per ADR-0022. A literal byte-equal diff cannot pass and the ADR
      would codify a bug (Retro Lesson #002). The DOMAIN intent per CLAUDE.md
      "Triple target" convention and the existing ADR-0041
      `test_claude_mirror_equals_source` pattern is body-parity after frontmatter
      strip and placeholder substitution. Parity tests here follow that pattern
      so they catch real body drift post-implementation without false-positiving
      on the install mechanism.

  (2) ADR T_0043_027 says `git diff --name-only <pre-ADR-0043-ref>..HEAD --
      source/cursor/** .cursor-plugin/**` returns no cal/colby/roz/preamble
      basenames. A pre-ADR ref is not captured as a baseline fixture in this
      repo, and comparing against `HEAD` pre-implementation is vacuous. The
      domain intent is "Cursor overlays were not edited by this ADR." The
      equivalent static check: the Cursor overlay files for cal/colby/roz are
      pure YAML frontmatter (`.yml`) with no `<output>` content at all and no
      `return-condensation` mandate text. Asserting that the Cursor overlays
      do NOT gain either kind of content verifies the scope guard without
      requiring a git baseline.

  (3) ADR T_0043_028 asks for git hash-object baseline fixtures of the three
      cursor frontmatter files. Without pre-build capture those hashes cannot
      exist yet; Colby captures them in Step 1 per the ADR. This test asserts
      the current cursor frontmatter files remain YAML-only (no `<output>`
      block, no return-condensation mandate) -- structurally equivalent to
      "not touched for output-contract content." If Colby adds baseline hash
      fixtures during implementation, a follow-up test run will be extended.
"""

from pathlib import Path

import pytest

from tests.conftest import (
    CURSOR_DIR,
    INSTALLED_AGENTS,
    INSTALLED_REFS,
    SOURCE_AGENTS,
    SOURCE_REFS,
    count_matches,
    extract_tag_content,
)


# ── Files under test ──────────────────────────────────────────────────────────

_PREAMBLE_SRC = SOURCE_REFS / "agent-preamble.md"
_CAL_SRC = SOURCE_AGENTS / "cal.md"
_COLBY_SRC = SOURCE_AGENTS / "colby.md"
_ROZ_SRC = SOURCE_AGENTS / "roz.md"

_PREAMBLE_INSTALLED = INSTALLED_REFS / "agent-preamble.md"
_CAL_INSTALLED = INSTALLED_AGENTS / "cal.md"
_COLBY_INSTALLED = INSTALLED_AGENTS / "colby.md"
_ROZ_INSTALLED = INSTALLED_AGENTS / "roz.md"

_CURSOR_AGENTS = CURSOR_DIR / "agents"
_CURSOR_CAL = _CURSOR_AGENTS / "cal.frontmatter.yml"
_CURSOR_COLBY = _CURSOR_AGENTS / "colby.frontmatter.yml"
_CURSOR_ROZ = _CURSOR_AGENTS / "roz.frontmatter.yml"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_return_condensation_section(text: str) -> str:
    """Extract the content of the <preamble id="return-condensation"> ... </preamble>
    block from a preamble file's full text.

    Returns the content between the opening tag (inclusive) and the FIRST
    following `</preamble>` closer (inclusive). Returns empty string if the
    opening tag is not present.

    The existing `<preamble id="shared-actions">` section appears before the
    new section per ADR-0043 Decision #1, so the "first following closer"
    logic is safe: we search only from the id="return-condensation" opener
    forward.
    """
    open_tag = '<preamble id="return-condensation">'
    close_tag = "</preamble>"
    if open_tag not in text:
        return ""
    start = text.index(open_tag)
    rest = text[start:]
    end = rest.find(close_tag)
    if end == -1:
        return rest
    return rest[: end + len(close_tag)]


def _extract_roz_oneliner(output: str) -> str:
    """Extract Roz's condensed one-liner return-to-Eva from her <output> block.

    The one-liner is the backticked sentence whose leading marker is
    `Roz Wave N PASS/FAIL`. In the landed `<output>` it appears on its own
    line wrapped in backticks, e.g.:

        `Roz Wave N PASS/FAIL. N BLOCKERs, N FIX-REQUIREDs. Report: ....`

    Returns the one-liner text WITHOUT the surrounding backticks. Returns
    empty string if the one-liner marker is not found.

    Scoping the severity-tier absence guard to the one-liner (rather than
    the entire `<output>` block) is deliberate: the full on-disk QA report
    structure legitimately lists Suggestions as a section heading (along
    with Checks table, Requirements Verification, etc.), but the CONDENSED
    return to Eva carries only BLOCKERs + FIX-REQUIREDs counts. The
    unsupported-tier regression guard belongs on the one-liner, not on the
    prose describing what the full report file contains.
    """
    marker = "Roz Wave N PASS/FAIL"
    idx = output.find(marker)
    if idx == -1:
        return ""
    # Walk back to the nearest preceding backtick on the same line (the
    # opening `` ` `` of the one-liner), then forward to the next backtick
    # after the marker.
    line_start = output.rfind("\n", 0, idx) + 1
    # Find opening backtick between line_start and idx.
    open_bt = output.rfind("`", line_start, idx)
    if open_bt == -1:
        # Fall back: return from marker to end-of-line if backticks missing.
        line_end = output.find("\n", idx)
        return output[idx:line_end] if line_end != -1 else output[idx:]
    close_bt = output.find("`", idx)
    if close_bt == -1:
        return output[open_bt + 1 :]
    return output[open_bt + 1 : close_bt]


def _strip_frontmatter(text: str) -> str:
    """Strip a leading YAML frontmatter block (between `---` markers at the top)
    if present. Installed files carry a YAML frontmatter overlay applied at
    install time per ADR-0022; the source/shared/ templates do not. Mirrors
    the pattern used in tests/test_adr0041_rule_structure.py.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != "---":
        return text
    for idx in range(1, len(lines)):
        if lines[idx].rstrip("\n") == "---":
            rest = lines[idx + 1:]
            if rest and rest[0].strip() == "":
                rest = rest[1:]
            return "".join(rest)
    return text


def _normalize_for_mirror_compare(text: str) -> str:
    """Normalize text for source-vs-installed body comparison.

    Source templates use the `{config_dir}` placeholder; installed copies
    have it substituted to `.claude` (for Claude Code) at install time.
    Normalizing `.claude` -> `{config_dir}` on the installed side lets
    body-parity tests detect real content drift without false-positiving
    on the install-time substitution.

    Frontmatter is already stripped by the caller before this runs.
    """
    return text.replace(".claude/", "{config_dir}/")


# =============================================================================
# Category A: Preamble mandate presence (producer contract)
# =============================================================================

def test_T_0043_001_preamble_contains_return_condensation_id_tag():
    """T-0043-001: source/shared/references/agent-preamble.md contains the
    literal string `<preamble id="return-condensation">` exactly once.

    Pre-build: FAILS -- preamble currently has only the shared-actions section.
    """
    assert _PREAMBLE_SRC.exists(), f"preamble not found at {_PREAMBLE_SRC}"
    text = _PREAMBLE_SRC.read_text()
    occurrences = text.count('<preamble id="return-condensation">')
    assert occurrences == 1, (
        f'agent-preamble.md must contain exactly one `<preamble id="return-condensation">` '
        f"opener (ADR-0043 Decision #1). Found: {occurrences}."
    )


def test_T_0043_002_return_condensation_section_contains_condensed_self_report():
    """T-0043-002: Within the return-condensation preamble section, the literal
    string `Condensed self-report` appears (rule 1 heading anchor).

    Pre-build: FAILS -- section does not exist yet.
    """
    text = _PREAMBLE_SRC.read_text()
    section = _extract_return_condensation_section(text)
    assert section, (
        '<preamble id="return-condensation"> section not found in agent-preamble.md. '
        "ADR-0043 Decision #1 requires this section."
    )
    assert "Condensed self-report" in section, (
        'return-condensation section must contain the literal string "Condensed self-report" '
        "(rule 1 heading). ADR-0043 Decision #1."
    )


def test_T_0043_003_return_condensation_section_uses_file_line_citation_format():
    """T-0043-003: Within the return-condensation preamble section, the citation
    format mandated for code claims is the literal token `file:line`, and the
    alternative form `filepath:line` MUST be absent.

    Domain intent (post-Poirot F2 fix):
      ADR-0043 Decision #1 rule 2 specifies the citation format producer
      agents use for code-claim evidence. The project's established term
      (used by robert.md and sable.md reviewer personas) is `file:line`.
      An earlier draft of this ADR used `filepath:line` -- a third term
      that conflicted with the reviewer-persona vocabulary. Poirot F2
      flagged this as a vocabulary drift; Cal accepted the finding and
      landed the preamble with `file:line`. This test asserts the corrected
      term is present AND guards against re-introduction of `filepath:line`.

    History: an earlier revision of T_0043_003 asserted `filepath:line`
    verbatim. After the F2 rename, that assertion codified the rejected
    term (Retro Lesson #002: assert domain intent, not current-file-state
    at authoring time). The test was rewritten to the corrected term and
    extended with an absence guard.

    Pre-build / post-F2: FAILS only if the preamble loses the `file:line`
    token or re-introduces `filepath:line`. Current landed state: PASSES.
    """
    text = _PREAMBLE_SRC.read_text()
    section = _extract_return_condensation_section(text)
    assert section, '<preamble id="return-condensation"> section not found in agent-preamble.md.'
    assert "file:line" in section, (
        'return-condensation section must contain the literal string "file:line" '
        "(rule 2 citation format, post-Poirot-F2 term). ADR-0043 Decision #1."
    )
    # Regression guard (Poirot F2): the rejected term `filepath:line` must
    # not re-appear in the preamble section. The project-wide vocabulary
    # is `file:line` (aligned with robert.md / sable.md reviewer personas).
    assert "filepath:line" not in section, (
        'return-condensation section must NOT contain "filepath:line" -- the '
        "project's established citation term is `file:line` (used by reviewer "
        "personas robert.md and sable.md). ADR-0043 Decision #1 post-F2 fix; "
        "regression guard against re-introducing the rejected third term."
    )


def test_T_0043_004_return_condensation_section_contains_ellis_exemption():
    """T-0043-004: Within the return-condensation preamble section, the literal
    string `Ellis` appears (exemption anchor).

    Pre-build: FAILS -- section does not exist yet.
    """
    text = _PREAMBLE_SRC.read_text()
    section = _extract_return_condensation_section(text)
    assert section, '<preamble id="return-condensation"> section not found in agent-preamble.md.'
    assert "Ellis" in section, (
        'return-condensation section must contain the literal string "Ellis" (exemption '
        "anchor). ADR-0043 Decision #1 Exemption clause."
    )


@pytest.mark.parametrize(
    "placeholder",
    ["TODO", "FIXME", "to be determined", "TBD"],
)
def test_T_0043_005_return_condensation_section_has_no_placeholders(placeholder):
    """T-0043-005 (failure): the return-condensation preamble section must not
    contain any of these placeholder strings: TODO, FIXME, to be determined, TBD.
    Verifies the section landed as final text, not a draft.

    Pre-build: PASSES TRIVIALLY (section does not yet exist, so no placeholder
    can be present inside it). Post-build: must still pass. This test is a
    regression guard for draft text leaking into the final preamble.
    """
    text = _PREAMBLE_SRC.read_text()
    section = _extract_return_condensation_section(text)
    # When the section does not exist, "not in empty string" is True -- test passes.
    # Post-implementation, the section must exist (T-0043-002) and must not contain placeholders.
    assert placeholder not in section, (
        f'return-condensation section contains placeholder string "{placeholder}". '
        "Final text required per ADR-0043 Decision #1 verbatim paste."
    )


# =============================================================================
# Category B: Cal `<output>` condensation
# =============================================================================

def test_T_0043_006_cal_output_contains_adr_saved_phrase():
    """T-0043-006: source/shared/agents/cal.md `<output>` block contains the
    literal string `ADR-NNNN saved to`.

    Pre-build: FAILS -- current `<output>` has a multi-line handoff, not the
    condensed one-liner.
    """
    assert _CAL_SRC.exists(), f"cal.md not found at {_CAL_SRC}"
    output = extract_tag_content(_CAL_SRC, "output")
    assert output, "cal.md has no extractable <output>...</output> block."
    assert "ADR-NNNN saved to" in output, (
        'cal.md <output> must contain the literal phrase "ADR-NNNN saved to" '
        "per ADR-0043 Decision #2 verbatim one-liner."
    )


def test_T_0043_007_cal_output_contains_steps_and_tests_count():
    """T-0043-007: cal.md `<output>` contains the literal string `N steps, M tests`.

    Pre-build: FAILS -- current text says "N steps, M total tests" (different
    phrasing) inside a larger handoff paragraph.
    """
    output = extract_tag_content(_CAL_SRC, "output")
    assert output, "cal.md has no extractable <output>...</output> block."
    assert "N steps, M tests" in output, (
        'cal.md <output> must contain the literal phrase "N steps, M tests" '
        "per ADR-0043 Decision #2 verbatim one-liner."
    )


def test_T_0043_008_cal_output_contains_next_roz_pointer():
    """T-0043-008: cal.md `<output>` contains the literal string `Next: Roz`.

    Pre-build: PASSES TRIVIALLY (current multi-line handoff text contains
    "Next: Roz reviews the test spec" -- substring "Next: Roz" matches).
    Post-build: must still pass as presence check. The condensation removal
    of the verbose surrounding handoff is caught by T-0043-009 (failure test
    on the ADR skeleton) and T-0043-010 (DoR count threshold). Per ADR-0043
    Test Spec this is the specified happy-path substring check.
    """
    output = extract_tag_content(_CAL_SRC, "output")
    assert output, "cal.md has no extractable <output>...</output> block."
    assert "Next: Roz" in output, (
        'cal.md <output> must contain the literal phrase "Next: Roz" '
        "per ADR-0043 Decision #2 verbatim one-liner."
    )


def test_T_0043_009_cal_output_does_not_contain_adr_skeleton_header():
    """T-0043-009 (failure): cal.md `<output>` must NOT contain the literal
    string `# ADR-NNNN:` -- the ADR skeleton code block that belongs in the ADR
    file on disk, not in the return contract.

    Pre-build: FAILS -- current `<output>` contains the full ADR skeleton
    (line 133: `# ADR-NNNN: [Title]`).
    """
    output = extract_tag_content(_CAL_SRC, "output")
    assert output, "cal.md has no extractable <output>...</output> block."
    assert "# ADR-NNNN:" not in output, (
        'cal.md <output> must NOT contain "# ADR-NNNN:" -- the ADR skeleton belongs '
        "in the on-disk ADR file, not in the return contract. ADR-0043 Decision #2, "
        "Anti-goal 1."
    )


def test_T_0043_010_cal_output_does_not_inline_dor_table():
    """T-0043-010 (failure): cal.md `<output>` mentions `DoR` at most 3 times --
    guard against the current inline DoR table being retained. The new one-liner
    references the DoR only as prose ("DoR, ... DoD") within the file-pointer
    sentence; the inline DoR table is forbidden.

    Pre-build: PASSES TRIVIALLY (current `<output>` opens with "**DoR**
    (first):" -- 1 occurrence, well below the <=3 threshold). Post-build: must
    still pass. The threshold guards against regression where a full inline
    DoR TABLE (which would generate 5-10+ DoR mentions across its rows) is
    re-added to the return contract. The complementary inline-table failure
    signal for the Build Output block is caught by T-0043-014 (colby).

    The threshold is <=3 (mandate prose + cross-reference + 1-buffer) per the
    ADR-0043 Test Spec note.
    """
    output = extract_tag_content(_CAL_SRC, "output")
    assert output, "cal.md has no extractable <output>...</output> block."
    dor_count = output.count("DoR")
    assert dor_count <= 3, (
        f'cal.md <output> mentions "DoR" {dor_count} times -- must be <= 3 per '
        "ADR-0043 T_0043_010. Current value suggests an inline DoR table still "
        "lives in the return contract; the DoR belongs in the ADR file on disk."
    )


# =============================================================================
# Category C: Colby `<output>` condensation
# =============================================================================

def test_T_0043_011_colby_output_contains_unit_done_phrase():
    """T-0043-011: source/shared/agents/colby.md `<output>` contains the literal
    string `Unit N DONE`.

    Pre-build: FAILS -- current `<output>` closes with "**Step N complete.**"
    and "Implementation complete for ADR-NNNN" -- no Unit N DONE phrase.
    """
    assert _COLBY_SRC.exists(), f"colby.md not found at {_COLBY_SRC}"
    output = extract_tag_content(_COLBY_SRC, "output")
    assert output, "colby.md has no extractable <output>...</output> block."
    assert "Unit N DONE" in output, (
        'colby.md <output> must contain the literal phrase "Unit N DONE" '
        "per ADR-0043 Decision #3 verbatim one-liner."
    )


def test_T_0043_012_colby_output_contains_lint_and_typecheck_fields():
    """T-0043-012: colby.md `<output>` contains BOTH `Lint PASS/FAIL` AND
    `Typecheck PASS/FAIL`.

    Pre-build: FAILS -- current `<output>` does not declare these fields; they
    are refinements per ADR-0043 Decision #6 to match Eva's receipt format.
    """
    output = extract_tag_content(_COLBY_SRC, "output")
    assert output, "colby.md has no extractable <output>...</output> block."
    assert "Lint PASS/FAIL" in output, (
        'colby.md <output> must contain "Lint PASS/FAIL" per ADR-0043 Decision #3.'
    )
    assert "Typecheck PASS/FAIL" in output, (
        'colby.md <output> must contain "Typecheck PASS/FAIL" per ADR-0043 Decision #3.'
    )


def test_T_0043_013_colby_output_contains_ready_for_roz_field():
    """T-0043-013: colby.md `<output>` contains the literal string `Ready for Roz`.

    Pre-build: FAILS -- current output says "Ready for Roz." at the end of a
    narrative sentence only in the context of the overall "Implementation
    complete ... Ready for Roz." line. After rewrite this phrase appears as a
    structured `Ready for Roz: Y/N` field within the condensed one-liner.

    NOTE (pre-build pass risk): the current closing line "... Ready for Roz."
    does contain the literal substring "Ready for Roz", so this test could
    pass trivially pre-build. That is acceptable because T-0043-014 and
    T-0043-015 specifically assert removal of the inline Build Output code
    block -- the structural signal of the condensation is caught there.
    This test is a positive-presence check on the REPLACEMENT text; combined
    with the failure tests below, the overall test set binds the full shape.
    """
    output = extract_tag_content(_COLBY_SRC, "output")
    assert output, "colby.md has no extractable <output>...</output> block."
    assert "Ready for Roz" in output, (
        'colby.md <output> must contain "Ready for Roz" per ADR-0043 Decision #3 '
        "verbatim one-liner."
    )


def test_T_0043_014_colby_output_does_not_contain_dor_header():
    """T-0043-014 (failure): colby.md `<output>` must NOT contain the literal
    string `## DoR: Requirements Extracted` -- the full Build Output code block
    header that ADR-0043 replaces.

    Pre-build: FAILS -- current `<output>` contains the full Build Output block
    starting with "## DoR: Requirements Extracted" (line 113).
    """
    output = extract_tag_content(_COLBY_SRC, "output")
    assert output, "colby.md has no extractable <output>...</output> block."
    assert "## DoR: Requirements Extracted" not in output, (
        'colby.md <output> must NOT contain "## DoR: Requirements Extracted" -- the '
        "Build Output code block belongs in the implementation commit messages or "
        "pipeline-state.md, not in the return contract. ADR-0043 Decision #3."
    )


def test_T_0043_015_colby_output_does_not_contain_ui_contract_table_header():
    """T-0043-015 (failure): colby.md `<output>` must NOT contain the inline UI
    Contract table header row `| Concern | Declaration |`. The UI Contract can
    be referenced as a pointer phrase but the table rows must live in
    pipeline-state.md, not in the return.

    Pre-build: FAILS -- current `<output>` contains the full UI Contract table
    (line 120: `| Concern | Declaration |`).
    """
    output = extract_tag_content(_COLBY_SRC, "output")
    assert output, "colby.md has no extractable <output>...</output> block."
    header_count = output.count("| Concern | Declaration |")
    assert header_count == 0, (
        f"colby.md <output> contains the UI Contract table header "
        f'"| Concern | Declaration |" {header_count} time(s). The UI Contract table '
        "belongs in pipeline-state.md per ADR-0043 Decision #3; the return contract "
        "may reference UI Contract as a pointer only. Count must be 0."
    )


# =============================================================================
# Category D: Roz `<output>` condensation
# =============================================================================

def test_T_0043_016_roz_output_contains_roz_wave_phrase():
    """T-0043-016: source/shared/agents/roz.md `<output>` contains the literal
    string `Roz Wave N PASS/FAIL`.

    Pre-build: FAILS -- current `<output>` contains a full QA Report code block;
    no `Roz Wave N PASS/FAIL` one-liner.
    """
    assert _ROZ_SRC.exists(), f"roz.md not found at {_ROZ_SRC}"
    output = extract_tag_content(_ROZ_SRC, "output")
    assert output, "roz.md has no extractable <output>...</output> block."
    assert "Roz Wave N PASS/FAIL" in output, (
        'roz.md <output> must contain "Roz Wave N PASS/FAIL" per ADR-0043 '
        "Decision #4 verbatim one-liner."
    )


def test_T_0043_017_roz_output_uses_only_blockers_and_fix_required():
    """T-0043-017: Roz's condensed return-to-Eva one-liner (the backticked
    sentence opening `Roz Wave N PASS/FAIL`) contains the literal count-field
    strings `BLOCKERs` and `FIX-REQUIREDs`, and does NOT contain any form of
    `Suggestion`/`suggestion`. Roz's persona defines only two severity tiers
    (BLOCKER, FIX-REQUIRED); a "Suggestions" tier was never part of the
    one-liner contract.

    Domain intent (post-Poirot F1 fix):
      The CONDENSED one-liner is a structured receipt to Eva carrying only
      the two persona-recognized severity counts. The full on-disk QA report
      (`{pipeline_state_dir}/last-qa-report.md`) is a separate artifact with
      its own sections; the absence guard here targets the one-liner only.

    History: an earlier draft of T_0043_017 asserted `Suggestions` as a
    one-liner field (mirroring a proposed Eva receipt-format field). Poirot
    F1 flagged this as codifying an unsupported severity tier -- the
    persona's `<constraints>`/`<output>` only recognize BLOCKER (pipeline
    halts) and FIX-REQUIRED (queued before commit). Cal accepted the
    finding; the Roz one-liner was corrected to
    `N BLOCKERs, N FIX-REQUIREDs` only, and this test was rewritten to
    guard against re-introduction of the unsupported tier.

    Scope note (Retro Lesson #002): the absence guard is scoped to the
    ONE-LINER (extracted by `_extract_roz_oneliner`), not to the entire
    `<output>` block. The `<output>` block prose that describes what the
    full QA report file on disk contains legitimately mentions Suggestions
    alongside other report section headings (Checks table, Requirements
    Verification, etc.). Applying the guard at the `<output>` level would
    codify the wrong domain -- it would forbid even narrative mention of
    the full-report's on-disk structure. The unsupported-tier regression
    guard belongs specifically on the structured condensed return.

    Corrected contract (ADR-0043 Decision #4, post-F1 fix):
      `Roz Wave N PASS/FAIL. N BLOCKERs, N FIX-REQUIREDs. Report: {pipeline_state_dir}/last-qa-report.md.`
    """
    output = extract_tag_content(_ROZ_SRC, "output")
    assert output, "roz.md has no extractable <output>...</output> block."
    oneliner = _extract_roz_oneliner(output)
    assert oneliner, (
        "roz.md <output> has no extractable Roz-Wave one-liner. ADR-0043 "
        "Decision #4 requires a backticked one-liner opening "
        '`Roz Wave N PASS/FAIL`.'
    )
    assert "BLOCKERs" in oneliner, (
        'roz.md <output> one-liner must contain "BLOCKERs" (plural count '
        'field) per ADR-0043 Decision #4 corrected one-liner. One-liner: '
        f"{oneliner!r}"
    )
    assert "FIX-REQUIREDs" in oneliner, (
        'roz.md <output> one-liner must contain "FIX-REQUIREDs" (plural '
        'count field) per ADR-0043 Decision #4 corrected one-liner. '
        f"One-liner: {oneliner!r}"
    )
    # Regression guard (Poirot F1): the Roz persona recognizes only two
    # severity tiers (BLOCKER, FIX-REQUIRED). `Suggestion`/`suggestion` must
    # not appear in the one-liner. Case-insensitive check catches both
    # capitalized ("N Suggestions") and lowercased ("N suggestions")
    # re-introductions of the unsupported tier.
    assert "suggestion" not in oneliner.lower(), (
        'roz.md <output> one-liner must NOT contain "Suggestion"/"suggestions" '
        "-- the Roz persona defines only two severity tiers "
        '(BLOCKER, FIX-REQUIRED). A "Suggestions" tier was never part of the '
        "one-liner contract. ADR-0043 Decision #4 post-F1 fix; regression "
        f"guard against re-introducing the unsupported tier. One-liner: {oneliner!r}"
    )


def test_T_0043_018_roz_output_preserves_last_qa_report_persistence_pointer():
    """T-0043-018: roz.md `<output>` contains the literal string `last-qa-report.md`
    -- the persistence pointer is preserved.

    Pre-build: PASSES (the current persistence instruction "Report persistence:
    write QA report to `{pipeline_state_dir}/last-qa-report.md`." is already
    present inside the <output> block). Post-build: must still pass; ADR-0043
    preserves this line explicitly (Decision #4 "Write the full QA report ... to
    `{pipeline_state_dir}/last-qa-report.md`.").

    This test guards against accidental removal of the persistence pointer
    during the condensation rewrite.
    """
    output = extract_tag_content(_ROZ_SRC, "output")
    assert output, "roz.md has no extractable <output>...</output> block."
    assert "last-qa-report.md" in output, (
        'roz.md <output> must contain "last-qa-report.md" -- the QA report '
        "persistence pointer is preserved across the condensation rewrite. "
        "ADR-0043 Decision #4 + DoR R11."
    )


def test_T_0043_019_roz_output_does_not_contain_qa_report_header():
    """T-0043-019 (failure): roz.md `<output>` must NOT contain the literal
    string `## QA Report`. The full QA Report code block belongs in
    `last-qa-report.md`, not in the return.

    Pre-build: FAILS -- current `<output>` opens with "## QA Report -- [Date]"
    inside a fenced code block.
    """
    output = extract_tag_content(_ROZ_SRC, "output")
    assert output, "roz.md has no extractable <output>...</output> block."
    assert "## QA Report" not in output, (
        'roz.md <output> must NOT contain "## QA Report" -- the full QA Report '
        "structure belongs in last-qa-report.md, not in the return contract. "
        "ADR-0043 Decision #4."
    )


def test_T_0043_020_roz_output_does_not_contain_checks_table_header():
    """T-0043-020 (failure): roz.md `<output>` must NOT contain the inline
    Checks table header `| Check | Status | Details |`.

    Pre-build: FAILS -- current `<output>` contains `| Check | Status | Details |`
    as part of the inline QA Report block.
    """
    output = extract_tag_content(_ROZ_SRC, "output")
    assert output, "roz.md has no extractable <output>...</output> block."
    assert "| Check | Status | Details |" not in output, (
        'roz.md <output> must NOT contain the Checks table header '
        '"| Check | Status | Details |". The table belongs in last-qa-report.md '
        "per ADR-0043 Decision #4."
    )


# =============================================================================
# Category E: Cross-reference / preamble pointer
# =============================================================================

@pytest.mark.parametrize(
    "agent_file",
    [_CAL_SRC, _COLBY_SRC, _ROZ_SRC],
    ids=["cal", "colby", "roz"],
)
def test_T_0043_021_agent_output_references_preamble_mandate(agent_file):
    """T-0043-021: Each of cal.md, colby.md, roz.md `<output>` blocks references
    `agent-preamble.md` OR `return-condensation` (pointer back to the shared
    mandate).

    Parameterized over the three source agent files; all three must pass.

    Pre-build: FAILS for all three -- current `<output>` blocks do not reference
    the preamble mandate (the mandate does not yet exist).
    """
    assert agent_file.exists(), f"agent file not found: {agent_file}"
    output = extract_tag_content(agent_file, "output")
    assert output, f"{agent_file.name} has no extractable <output>...</output> block."
    has_preamble_reference = (
        "agent-preamble.md" in output or "return-condensation" in output
    )
    assert has_preamble_reference, (
        f"{agent_file.name} <output> must reference either `agent-preamble.md` or "
        '`return-condensation` to point agents at the shared mandate. ADR-0043 '
        "Decision sections 2-4 each include this pointer in the verbatim text."
    )


def test_T_0043_022_preamble_return_condensation_section_is_singleton():
    """T-0043-022 (failure): agent-preamble.md contains exactly ONE
    `<preamble id="return-condensation">` opener and exactly ONE matching
    `</preamble>` closer after it (no duplication from careless copy-paste).

    Pre-build: FAILS -- the section is absent (0 != 1 opener count).
    Post-build: must pass with exactly one opener and at least one closer after
    the opener.

    Implementation: count opener occurrences of the attributed tag, and assert
    that exactly one `</preamble>` appears in the extracted section text
    (the extraction stops at the FIRST closer, so if extraction succeeds we
    necessarily have at least one; and counting all closers in the file and
    comparing to the count of all openers catches duplicate blocks).
    """
    text = _PREAMBLE_SRC.read_text()
    opener_count = text.count('<preamble id="return-condensation">')
    assert opener_count == 1, (
        f'agent-preamble.md must contain exactly one `<preamble id="return-condensation">` '
        f"opener. Found: {opener_count}. ADR-0043 Decision #1."
    )
    # Every <preamble id="..."> opener must have one </preamble> closer.
    # Count all openers (any id) and all closers; they must match.
    all_openers = count_matches(_PREAMBLE_SRC, r"<preamble id=\"[^\"]+\">")
    all_closers = count_matches(_PREAMBLE_SRC, r"</preamble>")
    assert all_openers == all_closers, (
        f"agent-preamble.md has {all_openers} <preamble id=...> openers but "
        f"{all_closers} </preamble> closers. Every preamble block must be balanced. "
        "ADR-0043 Decision #1 Acceptance Criteria."
    )


# =============================================================================
# Category F: Installed-copy parity (mirror sync)
#
# Implementation note: installed copies under .claude/ carry install-time
# overlays (frontmatter + `{config_dir}` -> `.claude` substitutions) per
# ADR-0022. A literal byte-equal diff will not pass and would codify the
# opposite of the triple-target convention. Parity tests compare the body
# (post-frontmatter-strip) after normalizing the installed side's `.claude/`
# back to `{config_dir}/`. Pattern taken from the ADR-0041 mirror-parity
# test (`test_claude_mirror_equals_source`). Catches real content drift
# without false-positiving on the install mechanism.
# =============================================================================

@pytest.mark.parametrize(
    "source_path,installed_path,basename",
    [
        (_PREAMBLE_SRC, _PREAMBLE_INSTALLED, "agent-preamble.md"),
        (_CAL_SRC, _CAL_INSTALLED, "cal.md"),
        (_COLBY_SRC, _COLBY_INSTALLED, "colby.md"),
        (_ROZ_SRC, _ROZ_INSTALLED, "roz.md"),
    ],
    ids=["preamble", "cal", "colby", "roz"],
)
def test_T_0043_023_through_026_installed_copy_body_mirrors_source(
    source_path, installed_path, basename
):
    """T-0043-023 (preamble), T-0043-024 (cal), T-0043-025 (colby),
    T-0043-026 (roz): the installed copy under .claude/ mirrors the source
    template's body.

    Comparison rule (per CLAUDE.md triple-target + ADR-0022 install overlay):
    strip the installed copy's leading YAML frontmatter, normalize `.claude/`
    back to `{config_dir}/` on the installed side, and compare to the source
    template body verbatim. Body parity is the architectural contract;
    frontmatter and placeholder substitution are overlay artifacts of the
    install step, not content.

    Pre-build: FAILS for all four -- the source templates have not yet been
    updated for ADR-0043, but even now the installed copies' `{config_dir}`
    -> `.claude` substitution means source and installed differ on every
    body line that contains `{config_dir}` (preamble's lines 4, 19, 26, 37
    are the immediate drift). The test correctly RED's these files now; after
    Colby's edits land in both source and installed copies in sync, the test
    goes green.
    """
    assert source_path.exists(), f"source template not found: {source_path}"
    assert installed_path.exists(), f"installed copy not found: {installed_path}"
    source_body = source_path.read_text()
    installed_raw = installed_path.read_text()
    installed_body = _strip_frontmatter(installed_raw)
    installed_normalized = _normalize_for_mirror_compare(installed_body)
    assert installed_normalized == source_body, (
        f"Installed copy {installed_path} diverges from source {source_path} "
        "after frontmatter strip and `.claude/` -> `{config_dir}/` normalization. "
        "ADR-0043 Step 1 acceptance criteria: "
        f"diff <source> <installed> returns empty (body-wise). basename={basename}."
    )


# =============================================================================
# Category G: Cursor overlay untouched (scope guard)
#
# Implementation note: ADR T_0043_027 specifies a git-diff-against-pre-ADR-ref
# check; ADR T_0043_028 specifies git hash-object baseline fixtures. Neither
# baseline is captured pre-build in this repo, and comparing against HEAD
# pre-implementation is vacuous. The domain intent is "Cursor overlays were
# not edited for `<output>` content or return-condensation mandate as part
# of this ADR." The equivalent static assertion: the Cursor overlay files
# (which are pure YAML frontmatter -- verified via a directory listing of
# source/cursor/agents/) must NOT gain an `<output>` block or a
# `return-condensation` reference. This tests the SCOPE at the file-content
# level without requiring a git baseline.
# =============================================================================

@pytest.mark.parametrize(
    "cursor_path,basename",
    [
        (_CURSOR_CAL, "cal.frontmatter.yml"),
        (_CURSOR_COLBY, "colby.frontmatter.yml"),
        (_CURSOR_ROZ, "roz.frontmatter.yml"),
    ],
    ids=["cursor_cal", "cursor_colby", "cursor_roz"],
)
def test_T_0043_027_cursor_overlays_do_not_contain_output_content(
    cursor_path, basename
):
    """T-0043-027 (failure / scope guard): Cursor overlay files for cal, colby,
    roz contain NO `<output>` content -- the ADR scope is "Cursor overlays are
    not edited for <output> blocks under this ADR."

    Cursor overlays are YAML frontmatter only (`.yml` extension, no markdown
    body). Any appearance of an `<output>` tag or the return-condensation
    mandate phrases in these files would indicate scope creep.

    Pre-build: PASSES (Cursor overlays currently have no `<output>` or mandate
    content). Post-build: must still pass as a scope regression guard.
    """
    assert cursor_path.exists(), (
        f"Cursor overlay expected at {cursor_path}. ADR-0043 Anti-goal 2 and "
        "scope guard require this file to exist and remain YAML-frontmatter-only."
    )
    content = cursor_path.read_text()
    assert "<output>" not in content, (
        f"Cursor overlay {basename} contains an <output> tag. "
        "ADR-0043 Step 1 'Explicitly NOT edited' lists source/cursor/**; "
        "Cursor overlays must remain frontmatter-only per ADR-0022."
    )
    assert "</output>" not in content, (
        f"Cursor overlay {basename} contains a closing </output> tag. "
        "ADR-0043 scope guard: Cursor overlays must remain frontmatter-only."
    )
    assert "return-condensation" not in content, (
        f"Cursor overlay {basename} references `return-condensation`. "
        "The mandate belongs in source/shared/references/agent-preamble.md only; "
        "Cursor overlays are out of scope for ADR-0043."
    )


@pytest.mark.parametrize(
    "cursor_path,basename",
    [
        (_CURSOR_CAL, "cal.frontmatter.yml"),
        (_CURSOR_COLBY, "colby.frontmatter.yml"),
        (_CURSOR_ROZ, "roz.frontmatter.yml"),
    ],
    ids=["cursor_cal", "cursor_colby", "cursor_roz"],
)
def test_T_0043_028_cursor_overlays_remain_pure_frontmatter(cursor_path, basename):
    """T-0043-028 (failure / scope guard): Cursor overlay files for cal, colby,
    roz remain pure YAML frontmatter content -- no markdown body, no persona
    `<output>` block, no return-condensation prose.

    The ADR (Decision #5 + DoR R8) states Cursor overlays do not carry
    `<output>` content for these agents; this ADR must not change that.
    Structural signature of "pure frontmatter": the file contains YAML key:value
    pairs (`name:`, `description:`, `model:`) and NO markdown tag-based content
    (no `##` headers, no `<identity>`, `<workflow>`, `<output>` tags, no
    `**bold**` prose sentences).

    This test is the static equivalent of ADR's git-hash-object baseline
    fixture for Cursor overlays: if the files gain any markdown-style prose
    during Colby's implementation, the scope has drifted.

    Pre-build: PASSES (Cursor overlays are currently YAML-only).
    Post-build: must still pass; Cursor overlays remain untouched by this ADR.
    """
    assert cursor_path.exists(), f"Cursor overlay not found: {cursor_path}"
    content = cursor_path.read_text()
    # Must have a recognizable YAML frontmatter signal.
    assert "name:" in content, (
        f"Cursor overlay {basename} is missing `name:` YAML key -- "
        "file appears not to be a valid frontmatter overlay. ADR-0022."
    )
    # Must NOT contain persona-body XML tags (those belong in source/shared/).
    forbidden_tags = ["<identity>", "<workflow>", "<constraints>", "<output>", "<examples>"]
    for tag in forbidden_tags:
        assert tag not in content, (
            f"Cursor overlay {basename} contains persona-body tag `{tag}`. "
            "Cursor overlays are frontmatter-only per ADR-0022; persona bodies "
            "live in source/shared/agents/. ADR-0043 does not change this."
        )
