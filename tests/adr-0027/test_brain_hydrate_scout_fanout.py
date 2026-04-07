"""ADR-0027: Brain-Hydrate Scout Fan-Out and Model Demotion -- Pre-Build TDD.

Tests: T-0027-001 through T-0027-031 (31 structural/preservation/edge/integration tests).

These tests define CORRECT behavior BEFORE Colby implements it.
Every test should FAIL on the current SKILL.md (which has no scout-fanout protocol).
A test that passes before implementation is suspicious -- see comments where pre-existing
behavior is asserted so those passes are expected and documented.

Files under test:
  - skills/brain-hydrate/SKILL.md
  - source/shared/rules/pipeline-orchestration.md
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_MD = PROJECT_ROOT / "skills" / "brain-hydrate" / "SKILL.md"
PIPELINE_ORCH = PROJECT_ROOT / "source" / "shared" / "rules" / "pipeline-orchestration.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def skill_content() -> str:
    assert SKILL_MD.is_file(), f"SKILL.md not found at {SKILL_MD}"
    return SKILL_MD.read_text()


def orch_content() -> str:
    assert PIPELINE_ORCH.is_file(), f"pipeline-orchestration.md not found at {PIPELINE_ORCH}"
    return PIPELINE_ORCH.read_text()


def extract_protocol(content: str, protocol_id: str) -> str:
    """Extract the full content of <protocol id="...">...</protocol>."""
    pattern = rf'<protocol id="{protocol_id}">.*?</protocol>'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else ""


def extract_procedure(content: str, procedure_id: str) -> str:
    """Extract the full content of <procedure id="...">...</procedure>."""
    pattern = rf'<procedure id="{procedure_id}">.*?</procedure>'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else ""


# ===========================================================================
# STRUCTURAL TESTS (T-0027-001 through T-0027-010)
# ===========================================================================


def test_T_0027_001_skill_md_contains_scout_fanout_protocol():
    """T-0027-001: SKILL.md contains <protocol id="scout-fanout"> section.

    AC1 from ADR-0027. This is the primary structural gate -- if this fails,
    all downstream scout-fanout tests will also fail.
    """
    content = skill_content()
    assert '<protocol id="scout-fanout">' in content, (
        'SKILL.md missing <protocol id="scout-fanout"> section. '
        "ADR-0027 Step 1 requires adding this protocol between Phase 1 and Phase 2."
    )


def test_T_0027_002_scout_fanout_defines_exactly_five_scout_categories():
    """T-0027-002: Scout-fanout protocol defines exactly 5 scout categories: ADR, Specs, UX, Pipeline, Git.

    ADR-0027 Decision section: five categories listed in the scout table.
    """
    content = skill_content()
    fanout = extract_protocol(content, "scout-fanout")
    assert fanout, "scout-fanout protocol not found -- cannot verify scout categories"

    # The five category names that MUST appear in the protocol
    required_categories = ["ADR", "Specs", "UX", "Pipeline", "Git"]
    for category in required_categories:
        assert category in fanout, (
            f"Scout category '{category}' not found in scout-fanout protocol. "
            f"ADR-0027 requires exactly 5 categories: {required_categories}"
        )


def test_T_0027_003_scout_fanout_specifies_explore_haiku_invocation():
    """T-0027-003: Each scout category specifies Agent(subagent_type: "Explore", model: "haiku").

    AC1 and R3 from ADR-0027. Must match the existing pipeline Scout Fan-out Protocol.
    """
    content = skill_content()
    fanout = extract_protocol(content, "scout-fanout")
    assert fanout, "scout-fanout protocol not found"

    # Must reference both the subagent_type and model assignment
    assert "Explore" in fanout, (
        'scout-fanout protocol must specify subagent_type: "Explore" for scout invocations'
    )
    assert "haiku" in fanout, (
        'scout-fanout protocol must specify model: "haiku" for scout invocations'
    )


def test_T_0027_004_scout_content_format_uses_file_delimiters():
    """T-0027-004: Scout content format uses === FILE: ... === / === END FILE === delimiters.

    AC3 from ADR-0027. The extraction agent must be able to parse these delimiters
    to process each file individually.
    """
    content = skill_content()
    assert "=== FILE:" in content, (
        "SKILL.md missing file delimiter '=== FILE:'. "
        "ADR-0027 specifies scouts return content with '=== FILE: path ===' / '=== END FILE ===' delimiters."
    )
    assert "=== END FILE ===" in content, (
        "SKILL.md missing closing file delimiter '=== END FILE ==='. "
        "Both opening and closing delimiters must be documented."
    )


def test_T_0027_005_file_count_gate_documented_twenty_files():
    """T-0027-005: File-count gate documented: >20 files per category triggers scout splitting.

    AC4 from ADR-0027. Mitigates haiku context window exhaustion on large categories.
    """
    content = skill_content()
    fanout = extract_protocol(content, "scout-fanout")
    assert fanout, "scout-fanout protocol not found"

    # Must mention the >20 file threshold and splitting
    assert re.search(r"20\s*files?|>20|more than 20", fanout, re.IGNORECASE), (
        "scout-fanout protocol missing file-count gate. "
        "ADR-0027 requires: if a single scout would read >20 files, split into sub-scouts."
    )


def test_T_0027_006_phase2_extract_capture_specifies_sonnet_subagent():
    """T-0027-006: Phase 2 (extract-capture) specifies Agent(model: "sonnet") for extraction.

    AC2 from ADR-0027 and R2. Extraction must move from main thread (Opus) to Sonnet subagent.
    """
    content = skill_content()
    procedure = extract_procedure(content, "extract-capture")
    assert procedure, "extract-capture procedure not found"

    assert "sonnet" in procedure.lower(), (
        'extract-capture procedure missing Agent(model: "sonnet") specification. '
        "ADR-0027 requires extraction to run as a Sonnet subagent, not on the main thread."
    )
    # Explicitly must NOT still say extraction happens on the main thread without qualification
    # The procedure must reference subagent or Agent() invocation
    assert re.search(r"Agent\s*\(|subagent", procedure, re.IGNORECASE), (
        "extract-capture procedure must explicitly invoke a subagent for extraction, "
        "not perform extraction directly on the main thread."
    )


def test_T_0027_007_extraction_agent_prompt_shape_includes_hydration_content_block():
    """T-0027-007: Extraction agent prompt shape includes <hydration-content> block with 5 child elements.

    AC10 from ADR-0027. The prompt shape must be documented with all five child elements.
    """
    content = skill_content()
    assert "<hydration-content>" in content, (
        "SKILL.md missing <hydration-content> block definition. "
        "ADR-0027 requires the extraction agent prompt shape to include this block."
    )

    # All five child element names must appear in proximity to hydration-content
    hydration_block_area = re.search(
        r"<hydration-content>.*?</hydration-content>",
        content,
        re.DOTALL,
    )
    assert hydration_block_area, "<hydration-content>...</hydration-content> block not found"
    block = hydration_block_area.group(0)

    required_children = ["<adrs>", "<specs>", "<ux-docs>", "<pipeline-artifacts>", "<git-history>"]
    for child in required_children:
        assert child in block, (
            f"<hydration-content> block missing child element '{child}'. "
            f"ADR-0027 specifies 5 children: {required_children}"
        )


def test_T_0027_008_dedup_logic_assigned_to_extraction_subagent():
    """T-0027-008: Dedup logic (agent_search threshold 0.85) explicitly assigned to extraction subagent.

    AC5 from ADR-0027. Dedup must move from main thread to subagent. The 0.85 threshold
    must be referenced in the context of the extraction agent's operation, not the main thread.
    """
    content = skill_content()
    procedure = extract_procedure(content, "extract-capture")
    assert procedure, "extract-capture procedure not found"

    assert "0.85" in procedure, (
        "extract-capture procedure missing 0.85 dedup threshold. "
        "ADR-0027 requires agent_search at 0.85 threshold assigned to extraction subagent."
    )
    assert "agent_search" in procedure, (
        "extract-capture procedure missing agent_search reference. "
        "Dedup logic must be explicitly assigned to the extraction subagent."
    )


def test_T_0027_009_hundred_thought_cap_assigned_to_extraction_subagent():
    """T-0027-009: 100-thought cap is explicitly assigned to extraction subagent.

    AC6 from ADR-0027. The cap must be enforced by the subagent, not the main thread.
    """
    content = skill_content()
    procedure = extract_procedure(content, "extract-capture")
    assert procedure, "extract-capture procedure not found"

    assert re.search(r"100\s*thoughts?|cap.*100|maximum.*100", procedure, re.IGNORECASE), (
        "extract-capture procedure missing 100-thought cap assignment. "
        "ADR-0027 requires the extraction subagent to enforce the 100-thought cap."
    )


def test_T_0027_010_incremental_rehydration_references_subagent():
    """T-0027-010: Incremental re-hydration section references subagent execution.

    AC8 from ADR-0027. The incremental-rehydration protocol must clarify that
    dedup is performed by the extraction subagent, not the main thread.
    """
    content = skill_content()
    rehydration = extract_protocol(content, "incremental-rehydration")
    assert rehydration, "incremental-rehydration protocol not found"

    assert re.search(r"subagent|extraction agent|Agent\s*\(", rehydration, re.IGNORECASE), (
        "incremental-rehydration protocol must reference subagent execution. "
        "ADR-0027 Step 1 requires updating this section to clarify dedup runs in the extraction subagent."
    )


# ===========================================================================
# PRESERVATION TESTS (T-0027-011 through T-0027-019)
# These assert existing correct behavior that MUST be preserved.
# All should PASS before and after implementation -- they guard against regression.
# ===========================================================================


def test_T_0027_011_all_seven_extraction_source_types_present():
    """T-0027-011: All 7 extraction source types preserved.

    Pre-existing behavior that must survive the refactor.
    Expected: PASS before and after implementation (regression guard).
    """
    content = skill_content()
    required_sources = [
        "ADR",
        "Feature spec",  # or "Specs" -- allow either
        "UX doc",        # or "UX" -- allow either
        "Error pattern",
        "Retro lesson",
        "Context brief",
        "Git history",
    ]
    # Use fuzzy matching since these may appear as section headers
    source_patterns = [
        r"ADRs?\b",
        r"[Ff]eature\s+[Ss]pecs?|[Ss]pec\s+files?|docs/product",
        r"UX\s+[Dd]ocs?|docs/ux",
        r"[Ee]rror\s+[Pp]attern",
        r"[Rr]etro\s+[Ll]esson",
        r"[Cc]ontext\s+[Bb]rief",
        r"[Gg]it\s+[Hh]istory|git\s+log",
    ]
    for pattern in source_patterns:
        assert re.search(pattern, content), (
            f"SKILL.md missing extraction source type matching '{pattern}'. "
            "All 7 source types must be preserved per ADR-0027 R8."
        )


def test_T_0027_012_all_thought_type_assignments_preserved():
    """T-0027-012: All thought_type assignments preserved per source type.

    Pre-existing behavior. SKILL.md must still specify decision, rejection, insight,
    lesson, correction, preference thought_types.
    Expected: PASS before and after implementation (regression guard).
    """
    content = skill_content()
    required_types = ["decision", "rejection", "insight", "lesson", "correction", "preference"]
    for thought_type in required_types:
        assert thought_type in content, (
            f"SKILL.md missing thought_type '{thought_type}'. "
            "All thought_type assignments must be preserved per ADR-0027 R8."
        )


def test_T_0027_013_all_importance_scores_preserved():
    """T-0027-013: All importance scores preserved per extraction rule.

    Pre-existing behavior. The extraction rules specify importance 0.9, 0.8, 0.7, 0.6, 0.5.
    Expected: PASS before and after implementation (regression guard).
    """
    content = skill_content()
    required_scores = ["0.9", "0.8", "0.7", "0.6", "0.5"]
    for score in required_scores:
        assert score in content, (
            f"SKILL.md missing importance score '{score}'. "
            "All importance values must be preserved per ADR-0027 R8."
        )


def test_T_0027_014_source_agent_assignments_preserved():
    """T-0027-014: All source_agent assignments preserved per source type.

    Pre-existing behavior. Checks cal, robert, sable, roz, eva, colby assignments.
    Expected: PASS before and after implementation (regression guard).
    """
    content = skill_content()
    required_agents = [
        ("cal", "ADR decisions"),
        ("robert", "feature spec decisions"),
        ("roz", "error patterns"),
        ("eva", "retro lessons / context brief"),
        ("colby", "git history"),
    ]
    for agent, context in required_agents:
        assert f'"{agent}"' in content or f"source_agent: \"{agent}\"" in content or f"''{agent}''" in content or agent in content, (
            f"SKILL.md missing source_agent assignment for '{agent}' ({context}). "
            "All source_agent assignments must be preserved per ADR-0027 R8."
        )


def test_T_0027_015_scope_controls_table_preserved():
    """T-0027-015: Scope controls table preserved with all five scope variants.

    Pre-existing behavior. SKILL.md must still support: "only ADRs", "skip git history",
    "since January", single-file, "dry run".
    Expected: PASS before and after implementation (regression guard).
    """
    content = skill_content()
    scope_phrases = [
        "only ADRs",
        "skip git history",
        "since",       # "since January" variant
        "dry run",
    ]
    for phrase in scope_phrases:
        assert phrase in content, (
            f"SKILL.md missing scope control phrase '{phrase}'. "
            "All scope controls must be preserved per ADR-0027 R8."
        )


def test_T_0027_016_all_six_guardrails_preserved():
    """T-0027-016: All 6 guardrails preserved.

    Pre-existing behavior. Guards against: verbatim copy, code capture, overwrite,
    respect conflicts, 100-cap, verify stats.
    Expected: PASS before and after implementation (regression guard).
    """
    content = skill_content()
    guardrail_patterns = [
        (r"verbatim|copy.paste|not.*copy", "no verbatim capture guardrail"),
        (r"[Nn]ever capture code|no.*(function|SQL|schema|config snippet)", "no code capture guardrail"),
        (r"[Nn]ever overwrite|additive|not.*delete", "no overwrite guardrail"),
        (r"conflict.*detect|agent_capture.*return.*conflict", "respect conflict detection guardrail"),
        (r"100\s*thoughts?|[Mm]aximum.*100|[Cc]ap.*100", "100-thought cap guardrail"),
        (r"atelier_stats.*after|verify.*stat|confirm.*count", "verify-at-end guardrail"),
    ]
    for pattern, description in guardrail_patterns:
        assert re.search(pattern, content, re.IGNORECASE | re.DOTALL), (
            f"SKILL.md missing guardrail: {description}. "
            "All 6 guardrails must be preserved per ADR-0027 R8."
        )


def test_T_0027_017_conversational_flow_preserved_with_user_approval_gate():
    """T-0027-017: Conversational flow preserved: Phase 1 scan + user approval gate before Phase 2.

    Pre-existing behavior (R5). Brain-hydrate must remain conversational -- no silent auto-run.
    Expected: PASS before and after implementation (regression guard).
    """
    content = skill_content()
    # Phase 1 scan must still exist
    assert "scan-inventory" in content or "Scan & Inventory" in content, (
        "SKILL.md missing Phase 1 scan section. Conversational flow must be preserved."
    )
    # User approval gate must still exist
    assert re.search(r"[Rr]eady to hydrate|user.*approv|approv.*proceed|[Aa]pproval", content), (
        "SKILL.md missing user approval gate. "
        "ADR-0027 R5 requires: scan, present inventory, user approves, execute."
    )
    # Conversational note must be present
    assert "conversational" in content.lower(), (
        "SKILL.md missing 'conversational' note. "
        "The skill must document that it presents scan results and waits for approval."
    )


def test_T_0027_018_phase3_summary_format_preserved():
    """T-0027-018: Phase 3 summary format preserved with thought breakdown and top themes.

    Pre-existing behavior. The final summary structure must survive the refactor.
    Expected: PASS before and after implementation (regression guard).
    """
    content = skill_content()
    # Phase 3 / progress-summary section must exist
    assert "progress-summary" in content or "Phase 3" in content, (
        "SKILL.md missing Phase 3 / progress-summary section."
    )
    # Summary must include thought type breakdown
    assert re.search(r"[Bb]reakdown|decisions.*rejections|thought.*breakdown", content), (
        "SKILL.md Phase 3 summary missing thought breakdown. "
        "Summary must show per-type counts (decisions, rejections, preferences, lessons, etc.)"
    )
    # Top themes must be present
    assert re.search(r"[Tt]op\s+themes?", content), (
        "SKILL.md Phase 3 summary missing 'Top themes' section."
    )


def test_T_0027_019_relation_types_preserved():
    """T-0027-019: Relation types preserved: evolves_from, contradicts, triggered_by, supports.

    Pre-existing behavior. All four relation types must remain in extraction rules.
    Expected: PASS before and after implementation (regression guard).
    """
    content = skill_content()
    required_relations = ["evolves_from", "contradicts", "triggered_by", "supports"]
    for relation in required_relations:
        assert relation in content, (
            f"SKILL.md missing relation type '{relation}'. "
            "All relation types must be preserved per ADR-0027 R8."
        )


# ===========================================================================
# FAILURE / EDGE CASE TESTS (T-0027-020 through T-0027-027)
# ===========================================================================


def test_T_0027_020_scout_fanout_documents_empty_category_skip_behavior():
    """T-0027-020: Scout returns empty content (0 files) -- extraction agent skips that source gracefully.

    The skip condition for zero files must be documented in the scout-fanout protocol.
    """
    content = skill_content()
    fanout = extract_protocol(content, "scout-fanout")
    assert fanout, "scout-fanout protocol not found"

    assert re.search(r"zero\s*files?|0\s*files?|no\s*files?|empty.*skip|skip.*empty|skip.*zero", fanout, re.IGNORECASE), (
        "scout-fanout protocol missing zero-files skip condition. "
        "ADR-0027: if a category has zero files, that scout is skipped."
    )


def test_T_0027_021_scout_failure_behavior_no_retry():
    """T-0027-021: Scout failure (timeout/error) -- Eva reports which category failed, does not retry.

    Anti-goal #2 from ADR-0027: no automatic re-invocation of scouts on partial failure.
    Consistent with retro lesson #004 (no retry loops).
    """
    content = skill_content()
    # Must document failure behavior (report + no retry)
    assert re.search(
        r"[Ss]cout.*fail|fail.*scout|[Ss]cout.*error|[Tt]imeout",
        content,
        re.IGNORECASE,
    ), (
        "SKILL.md missing scout failure handling documentation. "
        "ADR-0027 anti-goal #2: scout failures must be reported to user, not retried."
    )
    # Must NOT document a retry loop
    assert not re.search(
        r"retry.*scout|re-invoke.*scout|scout.*retry",
        content,
        re.IGNORECASE,
    ), (
        "SKILL.md contains scout retry logic. "
        "ADR-0027 anti-goal #2 prohibits automatic scout re-invocation."
    )


def test_T_0027_022_extraction_agent_mid_run_failure_documents_recovery():
    """T-0027-022: Extraction agent fails mid-run -- Eva reports captured-vs-expected, suggests re-run.

    SPOF section from ADR-0027. The SKILL.md must document this graceful degradation path.

    IMPORTANT: Must NOT use re.DOTALL -- patterns must match on a single line or short span
    to avoid false positives from existing SKILL.md sections (eva + agent_capture appear many
    lines apart in the extraction rules; "run again" appears in guardrail #5 for batching).

    The correct implementation will add new text explicitly calling out extraction agent
    failure and graceful degradation (the SPOF section in the ADR).
    """
    content = skill_content()
    # Line-by-line check: scan all lines for failure recovery language
    # Must contain a line that references the extraction agent or subagent in a failure context
    failure_patterns = [
        re.compile(r"extraction\s+agent.*fail", re.IGNORECASE),
        re.compile(r"subagent.*fail", re.IGNORECASE),
        re.compile(r"fail.*extraction\s+agent", re.IGNORECASE),
        re.compile(r"fail.*subagent", re.IGNORECASE),
        re.compile(r"captured.*vs.*expected|expected.*vs.*captured", re.IGNORECASE),
        re.compile(r"eva.*detect.*fail", re.IGNORECASE),
    ]
    lines = content.splitlines()
    found = any(
        any(p.search(line) for p in failure_patterns)
        for line in lines
    )
    assert found, (
        "SKILL.md missing extraction agent failure recovery documentation. "
        "ADR-0027 SPOF: if extraction agent fails mid-run, Eva detects the failure, "
        "reports captured-vs-expected count, and suggests re-run (dedup makes this safe). "
        "Must be documented with line-level explicit language about the extraction agent failing -- "
        "not generic 'partial match' (dedup) or 'run again' (batching) language from other sections."
    )


def test_T_0027_023_scope_narrowing_fires_only_matching_scout():
    """T-0027-023: User narrows scope to single source -- only that scout fires, others skipped.

    Scope controls must integrate with scout fan-out: narrowed scope skips irrelevant scouts.
    """
    content = skill_content()
    fanout = extract_protocol(content, "scout-fanout")
    assert fanout, "scout-fanout protocol not found"

    # The skip condition based on user scope exclusion must be documented
    assert re.search(
        r"user.*exclu|scope.*exclu|exclu.*source|only.*scout|skip.*scout|user.*narrow",
        fanout,
        re.IGNORECASE,
    ), (
        "scout-fanout protocol missing scope-based skip condition. "
        "ADR-0027: if user excludes a source type, only the matching scout fires."
    )


def test_T_0027_024_dry_run_scope_does_not_call_agent_capture():
    """T-0027-024: User requests 'dry run' -- extraction agent does NOT call agent_capture.

    Pre-existing scope control that must integrate correctly with the new three-tier model.
    In dry run mode, scouts may fire for preview but agent_capture must not be called.
    """
    content = skill_content()
    # Dry run must still be documented
    assert "dry run" in content.lower(), (
        "SKILL.md missing 'dry run' scope control. This must be preserved post-refactor."
    )
    # The dry run behavior description must reference the no-capture constraint
    dry_run_area = re.search(
        r"dry\s*run.*?\n(?:.*?\n){0,5}",
        content,
        re.IGNORECASE | re.DOTALL,
    )
    if dry_run_area:
        dry_run_text = dry_run_area.group(0)
        assert re.search(r"not.*write|don't.*capture|without.*captur|scan.*show|WOULD\s+be\s+captured", dry_run_text, re.IGNORECASE), (
            "SKILL.md dry run description must clarify that agent_capture is not called. "
            "The extraction agent must be aware of dry run mode."
        )


def test_T_0027_025_file_count_gate_split_produces_disjoint_sets():
    """T-0027-025: Category with >20 files -- scouts split into sub-scouts with disjoint file sets.

    The file-count gate must specify disjoint (non-overlapping) file sets for sub-scouts.
    Dedup rule R4: each file read by at most one scout.
    """
    content = skill_content()
    fanout = extract_protocol(content, "scout-fanout")
    assert fanout, "scout-fanout protocol not found"

    # Must mention both the split and the disjoint/non-overlapping requirement
    assert re.search(r"split|sub.scout", fanout, re.IGNORECASE), (
        "scout-fanout protocol missing sub-scout split documentation for >20 file gate."
    )
    assert re.search(r"disjoint|non.overlapping|each file.*one scout|one scout.*each file", fanout, re.IGNORECASE), (
        "scout-fanout protocol missing disjoint file set requirement for sub-scouts. "
        "ADR-0027 R4: each file read by exactly one scout."
    )


def test_T_0027_026_rehydration_all_thoughts_captured_reports_zero():
    """T-0027-026: Re-hydration when all thoughts already captured -- reports 'Skipped N, captured 0'.

    The extraction subagent must complete normally even when all candidates are skipped.
    """
    content = skill_content()
    rehydration = extract_protocol(content, "incremental-rehydration")
    assert rehydration, "incremental-rehydration protocol not found"

    # Must document the "all already captured" case
    assert re.search(r"[Ss]kipped.*already|already.*[Cc]aptured|[Ss]kip.*count", rehydration), (
        "incremental-rehydration protocol missing 'all already captured' case documentation. "
        "Must report skip count; extraction agent must complete normally with captured=0."
    )


def test_T_0027_027_git_scout_empty_returns_no_significant_commits():
    """T-0027-027: Git scout finds no significant commits -- returns empty, extraction skips git source.

    The git scout special case must document the no-significant-commits path.
    """
    content = skill_content()
    fanout = extract_protocol(content, "scout-fanout")
    assert fanout, "scout-fanout protocol not found"

    # Git scout must reference filtering for significant commits
    assert re.search(r"[Ss]ignificant\s+commit|filter.*commit|no.*commit|empty.*git", fanout, re.IGNORECASE), (
        "scout-fanout protocol missing git scout significant-commit filtering documentation. "
        "ADR-0027: git scout filters for significant commits; if none found, returns empty."
    )


# ===========================================================================
# INTEGRATION TESTS -- pipeline-orchestration.md (T-0027-028 through T-0027-031)
# ===========================================================================


def test_T_0027_028_pipeline_orchestration_scout_table_contains_brain_hydrate_row():
    """T-0027-028: pipeline-orchestration.md Scout Fan-out table contains brain-hydrate row.

    AC7 from ADR-0027. The Per-Agent Configuration table must include brain-hydrate.
    """
    content = orch_content()
    # The table header must exist (already passes -- pre-existing)
    assert "Per-Agent Configuration" in content, (
        "pipeline-orchestration.md missing 'Per-Agent Configuration' section."
    )
    # brain-hydrate row must be present
    assert "brain-hydrate" in content, (
        "pipeline-orchestration.md Scout Fan-out table missing 'brain-hydrate' row. "
        "ADR-0027 Step 1 requires adding this row to the Per-Agent Configuration table."
    )


def test_T_0027_029_brain_hydrate_row_specifies_hydration_content_block():
    """T-0027-029: brain-hydrate scout row specifies <hydration-content> as block name.

    AC from ADR-0027 Integration test T-0027-029. The row must name the block correctly.
    """
    content = orch_content()
    # Find the brain-hydrate section of the table
    brain_hydrate_area = re.search(
        r"brain-hydrate.*?\n",
        content,
        re.IGNORECASE,
    )
    assert brain_hydrate_area, (
        "brain-hydrate row not found in pipeline-orchestration.md -- cannot verify block name."
    )
    row_line = brain_hydrate_area.group(0)
    assert "hydration-content" in row_line, (
        "brain-hydrate row in pipeline-orchestration.md must specify '<hydration-content>' as block name. "
        "ADR-0027 T-0027-029."
    )


def test_T_0027_030_brain_hydrate_row_lists_all_five_scout_categories():
    """T-0027-030: brain-hydrate scout row lists all 5 scout categories.

    ADR-0027 T-0027-030. The row must enumerate all five source types.
    """
    content = orch_content()
    # Extract context around the brain-hydrate table row
    # The row may span one line or the surrounding table area
    brain_hydrate_section = re.search(
        r"brain-hydrate.{0,500}",
        content,
        re.IGNORECASE | re.DOTALL,
    )
    assert brain_hydrate_section, "brain-hydrate entry not found in pipeline-orchestration.md"
    section_text = brain_hydrate_section.group(0)

    required_scouts = ["ADR", "Spec", "UX", "Pipeline", "Git"]
    for scout in required_scouts:
        assert re.search(scout, section_text, re.IGNORECASE), (
            f"brain-hydrate entry in pipeline-orchestration.md missing scout category '{scout}'. "
            f"ADR-0027 T-0027-030 requires all 5 categories: {required_scouts}"
        )


def test_T_0027_031_brain_hydrate_skip_condition_is_scope_dependent():
    """T-0027-031: brain-hydrate skip condition documented as scope-dependent.

    ADR-0027 T-0027-031. The Per-Agent Configuration table row must document the
    skip condition: per-source skip when user excludes source type or scan finds 0 files.
    """
    content = orch_content()
    # Extract context around the brain-hydrate table row (wider window for table row)
    brain_hydrate_section = re.search(
        r"brain-hydrate.{0,800}",
        content,
        re.IGNORECASE | re.DOTALL,
    )
    assert brain_hydrate_section, "brain-hydrate entry not found in pipeline-orchestration.md"
    section_text = brain_hydrate_section.group(0)

    # Skip condition must reference scope exclusion or zero-file case
    assert re.search(
        r"scope|exclu|zero\s*files?|0\s*files?|source\s*type",
        section_text,
        re.IGNORECASE,
    ), (
        "brain-hydrate entry in pipeline-orchestration.md missing scope-dependent skip condition. "
        "ADR-0027: skip condition is 'per-source skip when user excludes source type or scan finds 0 files'."
    )


# ===========================================================================
# ADDITIONAL GAPS FOUND BY ROZ (not in Cal's 31 tests)
# ===========================================================================


def test_T_0027_ROZ_001_scout_fanout_appears_between_phase1_and_extract_capture():
    """ROZ-001: scout-fanout protocol appears BETWEEN scan-inventory and extract-capture.

    Cal's test spec only checks section presence, not ordering. The ADR Decision
    section explicitly states Phase 2a (scouts) comes after Phase 1 approval and
    before Phase 2b (extraction). Ordering matters for the conversational flow.
    """
    content = skill_content()
    scan_pos = content.find("scan-inventory")
    fanout_pos = content.find('protocol id="scout-fanout"')
    extract_pos = content.find("extract-capture")

    assert scan_pos != -1, "scan-inventory not found"
    assert fanout_pos != -1, (
        'scout-fanout protocol not found -- cannot verify ordering. '
        'ADR-0027 requires it between scan-inventory and extract-capture.'
    )
    assert extract_pos != -1, "extract-capture not found"

    assert scan_pos < fanout_pos < extract_pos, (
        "scout-fanout protocol must appear BETWEEN scan-inventory and extract-capture. "
        f"Positions: scan-inventory={scan_pos}, scout-fanout={fanout_pos}, extract-capture={extract_pos}. "
        "ADR-0027 Decision section defines the three-tier execution order."
    )


def test_T_0027_ROZ_002_extraction_agent_has_no_bash_access():
    """ROZ-002: Extraction agent must NOT require Bash tool access.

    ADR-0027 anti-goal #3 + Notes for Colby #3: the extraction agent does NOT
    need Bash because it works from scout-collected content. Git commands are
    the git scout's job. Documenting Bash access for the extraction agent would
    create an incorrect specification.
    """
    content = skill_content()
    procedure = extract_procedure(content, "extract-capture")
    if not procedure:
        pytest.skip("extract-capture procedure not yet implemented -- skip Bash access check")

    # The extraction agent description must not grant Bash access
    assert not re.search(
        r"[Ee]xtraction\s+agent.*[Bb]ash|[Ee]xtraction\s+agent.*git\s+log",
        content,
        re.IGNORECASE | re.DOTALL,
    ), (
        "SKILL.md incorrectly grants Bash access to the extraction agent. "
        "ADR-0027 Notes for Colby #3: the extraction agent works from scout content only. "
        "Git commands are run by the Git scout, not the extraction agent."
    )


def test_T_0027_ROZ_003_completeness_check_before_extraction_invocation():
    """ROZ-003: Eva must verify scout file counts against Phase 1 inventory before invoking extraction agent.

    ADR-0027 Consequences (Negative): if a scout missed a file, extraction is incomplete.
    The Consequences section states: 'Mitigated by Eva verifying scout output completeness
    against the Phase 1 inventory before invoking the extraction agent.'
    This completeness check must be documented in the scout-fanout protocol.
    """
    content = skill_content()
    fanout = extract_protocol(content, "scout-fanout")
    assert fanout, "scout-fanout protocol not found"

    assert re.search(
        r"complete|completeness|verif.*scout|scout.*verif|count.*match|inventory.*match",
        fanout,
        re.IGNORECASE,
    ), (
        "scout-fanout protocol missing completeness check. "
        "ADR-0027: Eva must verify scout file counts match Phase 1 inventory "
        "before invoking the extraction agent."
    )


def test_T_0027_ROZ_004_model_assignment_note_in_hydration_notes():
    """ROZ-004: SKILL.md hydration-notes section contains model assignment summary.

    ADR-0027 Step 1 item 4: 'Add a note to <section id="hydration-notes"> about model assignment:
    scouts are Haiku, extraction is Sonnet, scan/summary are main thread (Opus).'
    Cal's test spec does not cover this required doc note.
    """
    content = skill_content()
    # Find the hydration-notes section
    notes_section = re.search(
        r'<section id="hydration-notes">.*?</section>',
        content,
        re.DOTALL,
    )
    assert notes_section, "<section id=\"hydration-notes\"> not found in SKILL.md"
    notes_text = notes_section.group(0)

    # Must mention model assignments
    assert re.search(r"[Hh]aiku|scout.*model|model.*scout", notes_text), (
        'hydration-notes section missing Haiku model assignment note. '
        "ADR-0027 Step 1 item 4 requires adding model assignment documentation to this section."
    )
    assert re.search(r"[Ss]onnet|extraction.*model|model.*extraction", notes_text), (
        'hydration-notes section missing Sonnet model assignment note. '
        "ADR-0027 Step 1 item 4 requires scouts=Haiku, extraction=Sonnet to be documented here."
    )


def test_T_0027_ROZ_005_extraction_agent_prompt_shape_includes_constraints_tag():
    """ROZ-005: Extraction agent prompt shape includes <constraints> tag with dedup and cap rules.

    ADR-0027 Extraction Agent Prompt Shape section specifies a <constraints> tag.
    Cal's T-0027-007 only checks for <hydration-content> but the prompt shape has more required elements.
    """
    content = skill_content()
    # The prompt shape is documented near the hydration-content block
    # Check that constraints are shown as part of the extraction agent prompt
    hydration_area = re.search(
        r"<hydration-content>.*?(?:</hydration-content>|$).{0,500}",
        content,
        re.DOTALL,
    )
    if not hydration_area:
        pytest.skip("hydration-content block not yet implemented -- skip prompt shape check")

    surrounding = hydration_area.group(0)
    assert re.search(r"<constraints>|<read>", surrounding, re.IGNORECASE), (
        "Extraction agent prompt shape missing <constraints> or <read> elements. "
        "ADR-0027 Extraction Agent Prompt Shape requires: task, hydration-content, read, constraints, output."
    )
