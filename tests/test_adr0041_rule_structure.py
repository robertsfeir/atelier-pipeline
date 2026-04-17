"""ADR-0041 pre-build test assertions: rule-file structure.

These tests assert the post-build shape of the pipeline-models.md rule file
and its installed mirrors. Per Roz-first TDD (retro lesson 002), tests
encode what the file MUST look like AFTER Colby implements ADR-0041, not
what it currently contains. Pre-build: the majority FAIL -- that is the
expected signal.

Reference: ADR-0041 §Test Specification (T-0041-001 through T-0041-017)
and §Implementation Steps 1 and 6.
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_RULE = PROJECT_ROOT / "source" / "shared" / "rules" / "pipeline-models.md"
CLAUDE_RULE = PROJECT_ROOT / ".claude" / "rules" / "pipeline-models.md"
CURSOR_RULE = PROJECT_ROOT / ".cursor-plugin" / "rules" / "pipeline-models.mdc"


def _read(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"Rule file not found: {path}")
    return path.read_text()


def _strip_frontmatter(text: str) -> str:
    """Strip a leading YAML frontmatter block (between `---` markers at the
    very top of the file) if present. Installed `.claude/rules/*.md` files
    carry a `paths:` frontmatter overlay applied at install time; the
    corresponding `source/shared/rules/*.md` authoring template does not.
    Body comparison is what the architecture guarantees -- not byte
    equality including the platform-specific overlay.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != "---":
        return text
    for idx in range(1, len(lines)):
        if lines[idx].rstrip("\n") == "---":
            # Drop frontmatter lines (0 through idx inclusive) and any
            # single blank line immediately following the closing marker.
            rest = lines[idx + 1:]
            if rest and rest[0].strip() == "":
                rest = rest[1:]
            return "".join(rest)
    # Unterminated frontmatter -- leave the text untouched rather than
    # silently swallow content.
    return text


def _extract_promotion_signals_section(text: str) -> str:
    """Extract the content of the <model-table id="promotion-signals"> block.

    Returns the text between the opening tag and the closing </model-table>
    tag (exclusive). Returns an empty string if the section is not found.
    """
    open_tag = '<model-table id="promotion-signals">'
    close_tag = "</model-table>"
    if open_tag not in text:
        return ""
    start = text.index(open_tag)
    # Search for closing tag after the opening tag.
    rest = text[start:]
    end = rest.find(close_tag)
    if end == -1:
        return rest  # Unclosed tag -- return everything after open tag.
    return rest[:end + len(close_tag)]


# ─────────────────────────────────────────────────────────────────────────────
# Tier labels present
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("tier_label", ["Tier 1", "Tier 2", "Tier 3", "Tier 4"])
def test_source_rule_contains_tier_label(tier_label):
    """Source rule file must contain each of the four tier labels.

    Pre-build: FAILS until Colby rewrites pipeline-models.md per ADR-0041 Step 1.
    """
    text = _read(SOURCE_RULE)
    assert tier_label in text, (
        f"source/shared/rules/pipeline-models.md does not contain '{tier_label}'. "
        "ADR-0041 Decision §Four-Tier Task-Class Model requires all four tier rows."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tier -> model/effort row mapping (proximity check)
# ─────────────────────────────────────────────────────────────────────────────


def _line_with(text: str, needle: str) -> int:
    """Return the 0-based line index of the first occurrence of `needle`,
    or -1 if not found."""
    for idx, line in enumerate(text.splitlines()):
        if needle in line:
            return idx
    return -1


def _tier_row_has_tokens(text: str, tier_label: str, *tokens: str) -> tuple[bool, str]:
    """A tier row correctly maps if every required token (model, effort)
    appears on the same line as the tier label (or an adjacent line -- allow
    +/- 1 line to account for wrapped rows). Returns (passed, detail)."""
    lines = text.splitlines()
    anchor = _line_with(text, tier_label)
    if anchor < 0:
        return False, f"Tier label '{tier_label}' not found"
    # Window: anchor line +/- 1
    start = max(0, anchor - 1)
    end = min(len(lines), anchor + 2)
    window = "\n".join(lines[start:end])
    missing = [t for t in tokens if t.lower() not in window.lower()]
    if missing:
        return False, (
            f"Tier row for '{tier_label}' (lines {start}-{end - 1}) missing "
            f"tokens: {missing}. Window content: {window!r}"
        )
    return True, ""


def test_tier_1_row_maps_to_haiku_low():
    """Tier 1 row mentions Haiku and low effort.

    Pre-build: FAILS until Colby writes the Four-Tier table.
    """
    text = _read(SOURCE_RULE)
    ok, detail = _tier_row_has_tokens(text, "Tier 1", "Haiku", "low")
    assert ok, detail


def test_tier_2_row_maps_to_opus_medium():
    """Tier 2 row mentions Opus and medium effort."""
    text = _read(SOURCE_RULE)
    ok, detail = _tier_row_has_tokens(text, "Tier 2", "Opus", "medium")
    assert ok, detail


def test_tier_3_row_maps_to_opus_high():
    """Tier 3 row mentions Opus and high effort."""
    text = _read(SOURCE_RULE)
    ok, detail = _tier_row_has_tokens(text, "Tier 3", "Opus", "high")
    assert ok, detail


def test_tier_4_row_maps_to_opus_xhigh():
    """Tier 4 row mentions Opus and xhigh effort."""
    text = _read(SOURCE_RULE)
    ok, detail = _tier_row_has_tokens(text, "Tier 4", "Opus", "xhigh")
    assert ok, detail


# ─────────────────────────────────────────────────────────────────────────────
# Supersession -- old classifier / base-model tables removed
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "banned_marker",
    [
        '<model-table id="size-dependent">',
        '<model-table id="universal-classifier">',
        '<model-table id="base-models">',
        "Score >= 4",
        "Score <= -2",
    ],
)
def test_source_rule_does_not_contain_banned_marker(banned_marker):
    """Old classifier/base-models identifiers and score thresholds must be
    removed by ADR-0041 Step 1.

    Pre-build: FAILS (old content still present) until Colby rewrites the file.
    """
    text = _read(SOURCE_RULE)
    assert banned_marker not in text, (
        f"source/shared/rules/pipeline-models.md still contains banned marker "
        f"'{banned_marker}'. ADR-0041 §Decision requires removal of the "
        "size-dependent, universal-classifier, and base-models tables and of "
        "the classifier-score thresholds."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Promotion signals present (broad presence check)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "signal_phrase",
    ["auth", "security", "Large", "final juncture", "new module"],
)
def test_source_rule_mentions_promotion_signal(signal_phrase):
    """The Promotion Signals table must carry the signals ADR-0041 enumerates.

    Pre-build: FAILS until Colby writes the promotion-signals section.
    """
    text = _read(SOURCE_RULE)
    assert signal_phrase in text, (
        f"source/shared/rules/pipeline-models.md does not mention promotion "
        f"signal '{signal_phrase}'. ADR-0041 Decision §Promotion Signals "
        "requires auth/security, Large, Poirot final juncture, and new-module."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Promotion signals -- new module must be an explicit Tier 3 row
# ─────────────────────────────────────────────────────────────────────────────


def _new_module_tier3_row_in_section(section: str) -> bool:
    """Return True if the promotion-signals section contains a table row where
    both 'new module' (case-insensitive) AND '3' appear on the same line.

    This encodes that 'new module' must be an explicit Tier 3 promotion signal
    row, not merely mentioned somewhere in the file.
    """
    for line in section.splitlines():
        line_lower = line.lower()
        if "new module" in line_lower and "3" in line:
            return True
    return False


def test_promotion_signals_new_module_tier3_row_source():
    """promotion-signals table in source/shared/rules/pipeline-models.md must
    have an explicit Tier 3 row for 'new module'.

    The scout swarm found the existing file has exactly 5 rows and 'new module'
    does NOT appear as a row -- it was only referenced in the Tier 4 task-class
    table parenthetically. The promotion-signals section requires a dedicated
    row with explicit Tier 3 scope.

    Finding: F-5 (T-0041 §Promotion Signals).
    Pre-build: FAILS until Colby adds the row.
    """
    text = _read(SOURCE_RULE)
    section = _extract_promotion_signals_section(text)
    if not section:
        pytest.fail(
            'source/shared/rules/pipeline-models.md is missing the '
            '<model-table id="promotion-signals"> section entirely.'
        )
    assert _new_module_tier3_row_in_section(section), (
        "promotion-signals table must have an explicit Tier 3 row for "
        "'new module' (F-5, ADR-0041 §Promotion Signals)"
    )


def test_promotion_signals_new_module_tier3_row_installed():
    """Installed mirror .claude/rules/pipeline-models.md must also have an
    explicit Tier 3 'new module' row in the promotion-signals section.

    Same requirement as the source check (F-5) applied to the installed mirror
    after /pipeline-setup sync. Frontmatter is stripped before inspection.

    Finding: F-5, installed-mirror parity.
    Pre-build: FAILS until Colby propagates the rewritten file via Step 6.
    """
    if not CLAUDE_RULE.exists():
        pytest.skip(f"Installed mirror not found: {CLAUDE_RULE}")
    raw = CLAUDE_RULE.read_text()
    text = _strip_frontmatter(raw)
    section = _extract_promotion_signals_section(text)
    if not section:
        pytest.fail(
            '.claude/rules/pipeline-models.md is missing the '
            '<model-table id="promotion-signals"> section entirely.'
        )
    assert _new_module_tier3_row_in_section(section), (
        "promotion-signals table in .claude/rules/pipeline-models.md must "
        "have an explicit Tier 3 row for 'new module' (F-5, ADR-0041 "
        "§Promotion Signals)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Floor/ceiling language present
# ─────────────────────────────────────────────────────────────────────────────


def test_source_rule_has_floor_and_ceiling_framing():
    """Rule file must frame `low` as a floor and `xhigh` as a ceiling.

    The framing may appear as: 'floor', 'ceiling', 'never below', 'never above',
    'Floor: low', 'Ceiling: xhigh', or any equivalent. This test requires
    both 'low' and a 'max'-family token to appear near a framing keyword.
    """
    text = _read(SOURCE_RULE).lower()
    assert "low" in text and "max" in text, (
        "source/shared/rules/pipeline-models.md is missing either 'low' or "
        "'max' -- ADR-0041 §Decision Rule 2 requires explicit floor/ceiling "
        "framing (Floor: low, Ceiling: xhigh)."
    )
    framing_keywords = ["floor", "ceiling", "never below", "never above"]
    assert any(kw in text for kw in framing_keywords), (
        "source/shared/rules/pipeline-models.md does not use any of "
        f"{framing_keywords!r}. ADR-0041 Decision Rule 2 requires explicit "
        "floor/ceiling language."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Installed-mirror parity
# ─────────────────────────────────────────────────────────────────────────────


def test_claude_mirror_equals_source():
    """`.claude/rules/pipeline-models.md` must mirror the source's body
    per ADR-0041 Step 6. The installed mirror carries a YAML `paths:`
    frontmatter overlay (platform-specific, applied at install time so
    Claude Code auto-attaches the rule to `docs/pipeline/**`); the source
    template does not. Body parity is the architectural contract --
    frontmatter is overlay, not content.

    Pre-build: FAILS until Colby propagates the rewritten file.
    """
    source_text = _read(SOURCE_RULE)
    if not CLAUDE_RULE.exists():
        pytest.skip(f"Installed mirror not found: {CLAUDE_RULE}")
    mirror_text = CLAUDE_RULE.read_text()
    mirror_body = _strip_frontmatter(mirror_text)
    assert mirror_body == source_text, (
        f".claude/rules/pipeline-models.md body diverges from "
        "source/shared/rules/pipeline-models.md. ADR-0041 Step 6 requires "
        "the installed mirror's body (post-frontmatter) to equal the source "
        "template verbatim."
    )


def test_cursor_mirror_exists_and_contains_tier_labels():
    """`.cursor-plugin/rules/pipeline-models.mdc` must exist and contain at
    least the Tier 1 and Tier 4 labels (tier table propagated modulo .mdc
    wrapper).

    Pre-build: FAILS until Colby propagates the rewritten file.
    """
    if not CURSOR_RULE.exists():
        pytest.fail(
            f"Cursor installed mirror missing: {CURSOR_RULE}. "
            "ADR-0041 Step 6 requires both installed mirrors."
        )
    text = CURSOR_RULE.read_text()
    assert "Tier 1" in text, (
        ".cursor-plugin/rules/pipeline-models.mdc does not contain 'Tier 1'."
    )
    assert "Tier 4" in text, (
        ".cursor-plugin/rules/pipeline-models.mdc does not contain 'Tier 4'."
    )
