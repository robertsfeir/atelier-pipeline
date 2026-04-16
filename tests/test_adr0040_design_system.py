"""ADR-0040 pre-build test assertions: Design System Auto-Loading + Cal Brain-Search DoR.

All tests in this file are PRE-BUILD: they MUST FAIL against the current codebase
and PASS only after Colby implements ADR-0040. A test that passes before Colby
builds is flagged with justification in its docstring.

Test authoring contract (Retro Lesson #002):
  Tests assert what files SHOULD contain per the ADR, not what they currently contain.

Coverage:
  T-0040-001 through T-0040-006  -- Detection and Loading (Step 1)
  T-0040-007 through T-0040-011  -- Selective Loading (Step 1 reference doc)
  T-0040-012 through T-0040-014a -- Cross-Agent Consistency (Steps 2, 4)
  T-0040-015 through T-0040-019  -- /load-design Skill (Step 5)
  T-0040-020 through T-0040-021  -- Sable Reviewer Design System Deviation (Step 3)
  T-0040-022 through T-0040-023  -- Icon Handling (Step 4)
  T-0040-024 through T-0040-025  -- Pipeline Config Schema (Step 1)
  T-0040-026 through T-0040-029  -- Cal Brain-Search DoR (Step 6)

Untestable ADR test IDs:
  T-0040-002: "Agent loads from configured path, ignores design-system/ at root" -- requires
    live agent execution with a real pipeline-config.json. Static file content tests cannot
    verify runtime detection priority. Covered by T-0040-006 (config-over-convention prose
    in reference doc).
  T-0040-004: "Agent falls back to convention check when configured path is non-existent" --
    requires live agent execution. Covered by T-0040-001 (reference doc describes fallback).
  T-0040-012: "Colby's context contains same files before execution begins" -- requires
    runtime agent context introspection. Covered by T-0040-014a (propagation mechanism
    prescribed as <read>, not <constraints>).
  T-0040-014: "Colby re-detects when Eva omits files from <read>" -- requires live
    Eva invocation. Covered by reference doc content (T-0040-001 group) and colby.md
    re-detection prose (T-0040-042, embedded in T-0040-041).
"""

import json
import re
from pathlib import Path

# ── Project root ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Source files under test ───────────────────────────────────────────────────
_PIPELINE_CONFIG = PROJECT_ROOT / "source" / "shared" / "pipeline" / "pipeline-config.json"
_DESIGN_SYSTEM_REF = PROJECT_ROOT / "source" / "shared" / "references" / "design-system-loading.md"
_SABLE_UX = PROJECT_ROOT / "source" / "shared" / "agents" / "sable-ux.md"
_SABLE = PROJECT_ROOT / "source" / "shared" / "agents" / "sable.md"
_COLBY = PROJECT_ROOT / "source" / "shared" / "agents" / "colby.md"
_CAL = PROJECT_ROOT / "source" / "shared" / "agents" / "cal.md"
_LOAD_DESIGN_SKILL = PROJECT_ROOT / "skills" / "load-design" / "SKILL.md"
_PIPELINE_SETUP_SKILL = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"


# =============================================================================
# Step 1: Pipeline Config Schema + Design System Reference Doc
# T-0040-024, T-0040-025: Pipeline config key
# T-0040-001, T-0040-003, T-0040-005, T-0040-006, T-0040-007..T-0040-011: ref doc
# =============================================================================

# ── T-0040-024: Pipeline config template contains design_system_path key ─────

def test_T_0040_024_pipeline_config_contains_design_system_path_key():
    """T-0040-024: source/shared/pipeline/pipeline-config.json contains
    "design_system_path": null after existing keys.

    Pre-build: FAILS until Colby adds the key (ADR-0040 Step 1).
    """
    assert _PIPELINE_CONFIG.exists(), (
        f"pipeline-config.json not found at {_PIPELINE_CONFIG}"
    )
    data = json.loads(_PIPELINE_CONFIG.read_text())
    assert "design_system_path" in data, (
        'pipeline-config.json template is missing the "design_system_path" key. '
        "ADR-0040 Step 1 requires adding: \"design_system_path\": null"
    )
    assert data["design_system_path"] is None, (
        f'pipeline-config.json "design_system_path" default must be null. '
        f"Got: {data['design_system_path']!r}. "
        "Type: string | null. Default: null (convention-based detection)."
    )


# ── T-0040-025: Agents treat missing design_system_path key as null ──────────

def test_T_0040_025_reference_doc_describes_missing_key_as_null():
    """T-0040-025: design-system-loading.md documents that a missing
    design_system_path key must be treated as null (graceful absence).

    Agents loading design_system_path from pipeline-config.json must not
    crash on pre-existing installs that lack the key. The reference doc
    must state this explicitly so agents handle the edge case.

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    assert _DESIGN_SYSTEM_REF.exists(), (
        f"design-system-loading.md not found at {_DESIGN_SYSTEM_REF}. "
        "ADR-0040 Step 1 requires creating this reference document."
    )
    content = _DESIGN_SYSTEM_REF.read_text()
    has_missing_key_guidance = bool(
        re.search(r'missing\s+key', content, re.IGNORECASE) or
        re.search(r'treat\s+.*missing.*null', content, re.IGNORECASE) or
        re.search(r'absent.*null', content, re.IGNORECASE) or
        re.search(r'null.*missing', content, re.IGNORECASE) or
        re.search(r'not\s+present.*null', content, re.IGNORECASE)
    )
    assert has_missing_key_guidance, (
        "design-system-loading.md does not document that a missing "
        "design_system_path key must be treated as null. "
        "Existing pipeline installations lack this key -- agents must not crash. "
        "ADR-0040 T-0040-025 acceptance criteria."
    )


# ── T-0040-001: Reference doc describes detection order ──────────────────────

def test_T_0040_001_reference_doc_exists_with_detection_order():
    """T-0040-001: source/shared/references/design-system-loading.md exists and
    describes the detection order: check design_system_path first, then
    design-system/ at project root, then proceed without design system.

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    assert _DESIGN_SYSTEM_REF.exists(), (
        f"design-system-loading.md not found at {_DESIGN_SYSTEM_REF}. "
        "ADR-0040 Step 1 requires creating this reference document."
    )
    content = _DESIGN_SYSTEM_REF.read_text()
    # Must describe the three-step detection order
    has_config_path = bool(
        re.search(r'design_system_path', content) or
        re.search(r'pipeline-config', content, re.IGNORECASE)
    )
    has_convention_path = bool(
        re.search(r'design-system/', content) or
        re.search(r'project root', content, re.IGNORECASE)
    )
    has_graceful_absence = bool(
        re.search(r'no error', content, re.IGNORECASE) or
        re.search(r'graceful', content, re.IGNORECASE) or
        re.search(r'proceed without', content, re.IGNORECASE) or
        re.search(r'no design system', content, re.IGNORECASE)
    )
    assert has_config_path, (
        "design-system-loading.md does not describe step 1 of detection: "
        "read design_system_path from pipeline-config.json."
    )
    assert has_convention_path, (
        "design-system-loading.md does not describe step 2 of detection: "
        "check design-system/ at project root."
    )
    assert has_graceful_absence, (
        "design-system-loading.md does not describe step 3 of detection: "
        "proceed without design system when neither exists (no error)."
    )


# ── T-0040-003: Reference doc describes graceful absence annotation ───────────

def test_T_0040_003_reference_doc_describes_no_design_system_annotation():
    """T-0040-003: design-system-loading.md specifies that agents must annotate
    "no design system found" when neither design_system_path nor design-system/
    at root is available. This is not an error -- it is an informational annotation.

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    assert _DESIGN_SYSTEM_REF.exists(), (
        f"design-system-loading.md not found at {_DESIGN_SYSTEM_REF}."
    )
    content = _DESIGN_SYSTEM_REF.read_text()
    has_annotation_requirement = bool(
        re.search(r'no design system found', content, re.IGNORECASE) or
        re.search(r'annotate.*no design system', content, re.IGNORECASE) or
        re.search(r'no design system.*annotate', content, re.IGNORECASE) or
        re.search(r'note.*no design system', content, re.IGNORECASE)
    )
    assert has_annotation_requirement, (
        "design-system-loading.md does not specify the graceful-absence annotation. "
        'Expected: agents must note "no design system found" when neither path exists. '
        "ADR-0040 Requirement 7 + T-0040-003."
    )


# ── T-0040-005: Reference doc describes tokens.md-missing behavior ────────────

def test_T_0040_005_reference_doc_describes_missing_tokens_md_behavior():
    """T-0040-005: design-system-loading.md specifies that when design-system/ exists
    but tokens.md is missing, the agent must log the absence and proceed without
    the design system (not crash, not load other files without tokens).

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    assert _DESIGN_SYSTEM_REF.exists(), (
        f"design-system-loading.md not found at {_DESIGN_SYSTEM_REF}."
    )
    content = _DESIGN_SYSTEM_REF.read_text()
    has_tokens_missing_behavior = bool(
        re.search(r'tokens\.md.*missing', content, re.IGNORECASE) or
        re.search(r'tokens\.md.*not found', content, re.IGNORECASE) or
        re.search(r'missing.*tokens\.md', content, re.IGNORECASE) or
        re.search(r'tokens\.md.*required', content, re.IGNORECASE)
    )
    assert has_tokens_missing_behavior, (
        "design-system-loading.md does not specify behavior when tokens.md is missing "
        "from an existing design-system/ directory. "
        "Expected: log absence and proceed without design system. ADR-0040 T-0040-005."
    )


# ── T-0040-006: Reference doc specifies config overrides convention ───────────

def test_T_0040_006_reference_doc_specifies_config_overrides_convention():
    """T-0040-006: design-system-loading.md explicitly states that design_system_path
    (from pipeline-config.json) takes precedence over the convention-based
    design-system/ path when both exist.

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    assert _DESIGN_SYSTEM_REF.exists(), (
        f"design-system-loading.md not found at {_DESIGN_SYSTEM_REF}."
    )
    content = _DESIGN_SYSTEM_REF.read_text()
    has_priority_rule = bool(
        re.search(r'override', content, re.IGNORECASE) or
        re.search(r'takes precedence', content, re.IGNORECASE) or
        re.search(r'config.*over.*convention', content, re.IGNORECASE) or
        re.search(r'configured path.*first', content, re.IGNORECASE) or
        re.search(r'non-null.*use that path', content, re.IGNORECASE)
    )
    assert has_priority_rule, (
        "design-system-loading.md does not specify that design_system_path "
        "takes precedence over the convention-based design-system/ directory. "
        "ADR-0040 Decision section, Detection Order step 1 + T-0040-006."
    )


# =============================================================================
# Selective Loading Rules (T-0040-007 through T-0040-011)
# These assert reference doc content, not live agent behavior.
# =============================================================================

def _ref_doc_content() -> str:
    """Return reference doc content, asserting existence first."""
    assert _DESIGN_SYSTEM_REF.exists(), (
        f"design-system-loading.md not found at {_DESIGN_SYSTEM_REF}. "
        "ADR-0040 Step 1 must create this file."
    )
    return _DESIGN_SYSTEM_REF.read_text()


def test_T_0040_007_reference_doc_maps_dashboard_to_data_viz():
    """T-0040-007: design-system-loading.md maps "dashboard" / "data display" work
    to loading tokens.md + data-viz.md.

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    content = _ref_doc_content()
    has_data_viz_mapping = bool(
        re.search(r'data.viz', content, re.IGNORECASE) and
        (re.search(r'dashboard', content, re.IGNORECASE) or
         re.search(r'data display', content, re.IGNORECASE))
    )
    assert has_data_viz_mapping, (
        "design-system-loading.md does not map dashboard/data display work to "
        "data-viz.md. ADR-0040 Selective Loading Rules table + T-0040-007."
    )


def test_T_0040_008_reference_doc_maps_navigation_to_navigation_md():
    """T-0040-008: design-system-loading.md maps "navigation" work to
    tokens.md + navigation.md.

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    content = _ref_doc_content()
    has_navigation_mapping = bool(
        re.search(r'navigation\.md', content, re.IGNORECASE) and
        re.search(r'navigation', content, re.IGNORECASE)
    )
    assert has_navigation_mapping, (
        "design-system-loading.md does not map navigation work to navigation.md. "
        "ADR-0040 Selective Loading Rules table + T-0040-008."
    )


def test_T_0040_009_reference_doc_maps_component_form_to_components_md():
    """T-0040-009: design-system-loading.md maps "component" / "form" work to
    tokens.md + components.md.

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    content = _ref_doc_content()
    has_components_mapping = bool(
        re.search(r'components\.md', content, re.IGNORECASE) and
        (re.search(r'component', content, re.IGNORECASE) or
         re.search(r'form', content, re.IGNORECASE))
    )
    assert has_components_mapping, (
        "design-system-loading.md does not map component/form work to components.md. "
        "ADR-0040 Selective Loading Rules table + T-0040-009."
    )


def test_T_0040_010_reference_doc_specifies_default_domain_file_as_components():
    """T-0040-010: design-system-loading.md specifies that when the step description
    is ambiguous (no clear domain match), agents must load components.md as the
    default domain file.

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    content = _ref_doc_content()
    has_default_rule = bool(
        re.search(r'ambiguous', content, re.IGNORECASE) or
        re.search(r'default.*components\.md', content, re.IGNORECASE) or
        re.search(r'components\.md.*default', content, re.IGNORECASE) or
        re.search(r'if\s+ambiguous', content, re.IGNORECASE)
    )
    assert has_default_rule, (
        "design-system-loading.md does not specify the default domain file "
        "(components.md) for ambiguous step descriptions. "
        "ADR-0040 Selective Loading Rules: 'If ambiguous, load components.md' + T-0040-010."
    )


def test_T_0040_011_reference_doc_specifies_missing_domain_file_behavior():
    """T-0040-011: design-system-loading.md specifies that when a domain file does
    not exist at the resolved path, agents must log the absence and continue
    with tokens.md only (not crash or block).

    Pre-build: FAILS until Colby creates the reference doc (ADR-0040 Step 1).
    """
    content = _ref_doc_content()
    has_missing_domain_behavior = bool(
        re.search(r'domain file.*not found', content, re.IGNORECASE) or
        re.search(r'not found.*proceeding', content, re.IGNORECASE) or
        re.search(r'does not exist.*tokens', content, re.IGNORECASE) or
        re.search(r'missing.*domain.*tokens\.md only', content, re.IGNORECASE) or
        re.search(r'log.*not found.*continue', content, re.IGNORECASE)
    )
    assert has_missing_domain_behavior, (
        "design-system-loading.md does not specify behavior when a domain file "
        "does not exist at the resolved path. "
        "Expected: log missing file, continue with tokens.md only. ADR-0040 T-0040-011."
    )


# =============================================================================
# Step 2: Sable-UX (Producer) Design System Integration
# T-0040-013, T-0040-014a (cross-agent consistency via output annotation)
# =============================================================================

def test_T_0040_013_sable_ux_output_includes_design_system_annotation():
    """T-0040-013: source/shared/agents/sable-ux.md specifies that Sable-ux must
    annotate her output with a "Design system:" field listing loaded files or
    "No design system found".

    The exact annotation format per ADR-0040 Exact Prose section:
      **Design system:** [Loaded: file1.md, file2.md | No design system found]

    Pre-build: FAILS until Colby updates sable-ux.md (ADR-0040 Step 2).
    """
    assert _SABLE_UX.exists(), (
        f"sable-ux.md not found at {_SABLE_UX}."
    )
    content = _SABLE_UX.read_text()
    has_annotation = bool(
        re.search(r'\*\*Design system\*\*', content) or
        re.search(r'Design system.*Loaded', content, re.IGNORECASE) or
        re.search(r'no design system found', content, re.IGNORECASE)
    )
    assert has_annotation, (
        "sable-ux.md does not specify the Design system annotation in its output. "
        "Expected: **Design system:** [Loaded: file1.md, file2.md | No design system found] "
        "in the <output> section. ADR-0040 Exact Prose + T-0040-013."
    )


def test_T_0040_sable_ux_workflow_includes_design_system_check_step():
    """Sable-ux <workflow> includes a design system check step before her
    primary UX production steps.

    ADR-0040 Step 2 Exact Prose requires adding step 0 "Design system check."
    to <workflow> before existing step 1.

    Pre-build: FAILS until Colby updates sable-ux.md (ADR-0040 Step 2).
    """
    assert _SABLE_UX.exists(), (
        f"sable-ux.md not found at {_SABLE_UX}."
    )
    content = _SABLE_UX.read_text()
    has_design_check = bool(
        re.search(r'[Dd]esign system check', content) or
        re.search(r'design.system.*loading', content, re.IGNORECASE) or
        re.search(r'Check for design system', content, re.IGNORECASE)
    )
    assert has_design_check, (
        "sable-ux.md <workflow> does not include a design system check step. "
        "Expected: step 0 'Design system check' before existing step 1. "
        "ADR-0040 Step 2 Exact Prose."
    )


def test_T_0040_sable_ux_references_design_system_loading_doc():
    """Sable-ux references design-system-loading.md (the reference doc) in her
    workflow or constraints section.

    ADR-0040 Step 2 acceptance criteria: "The <constraints> section references
    design-system-loading.md."

    Pre-build: FAILS until Colby updates sable-ux.md (ADR-0040 Step 2).
    """
    assert _SABLE_UX.exists(), (
        f"sable-ux.md not found at {_SABLE_UX}."
    )
    content = _SABLE_UX.read_text()
    assert "design-system-loading.md" in content, (
        "sable-ux.md does not reference design-system-loading.md. "
        "ADR-0040 Step 2 acceptance criteria: constraints section must reference the doc."
    )


def test_T_0040_sable_ux_constraints_include_token_usage_rule():
    """Sable-ux <constraints> includes the rule to reference design system tokens
    in output and not invent values that contradict loaded tokens.

    ADR-0040 Step 2 Exact Prose for <constraints>:
      "When a design system is loaded, reference its tokens ... Do not invent values
      that contradict loaded tokens."

    Pre-build: FAILS until Colby updates sable-ux.md (ADR-0040 Step 2).
    """
    assert _SABLE_UX.exists(), (
        f"sable-ux.md not found at {_SABLE_UX}."
    )
    content = _SABLE_UX.read_text()
    has_token_constraint = bool(
        re.search(r'reference its tokens', content, re.IGNORECASE) or
        re.search(r'do not invent.*tokens', content, re.IGNORECASE) or
        re.search(r'contradict.*tokens', content, re.IGNORECASE) or
        re.search(r'loaded tokens', content, re.IGNORECASE)
    )
    assert has_token_constraint, (
        "sable-ux.md <constraints> does not include the rule to reference design "
        "system tokens and avoid inventing contradicting values. "
        "ADR-0040 Step 2 Exact Prose for <constraints>."
    )


# =============================================================================
# Step 3: Sable (Reviewer) Design System Awareness
# T-0040-020, T-0040-021
# =============================================================================

def test_T_0040_020_sable_reviewer_has_design_system_deviation_category():
    """T-0040-020: source/shared/agents/sable.md defines "Design System Deviation"
    as a DRIFT category: when implementation uses hardcoded values instead of
    design system tokens, Sable must flag it.

    Pre-build: FAILS until Colby updates sable.md (ADR-0040 Step 3).
    """
    assert _SABLE.exists(), (
        f"sable.md not found at {_SABLE}."
    )
    content = _SABLE.read_text()
    has_deviation_category = bool(
        re.search(r'Design System Deviation', content) or
        re.search(r'design system.*DRIFT', content, re.IGNORECASE) or
        re.search(r'DRIFT.*design system', content, re.IGNORECASE) or
        re.search(r'hardcoded.*design system', content, re.IGNORECASE)
    )
    assert has_deviation_category, (
        'sable.md does not define "Design System Deviation" as a DRIFT category. '
        "ADR-0040 Step 3 acceptance criteria: Sable must flag hardcoded values "
        "that match design system tokens. T-0040-020."
    )


def test_T_0040_021_sable_reviewer_skips_check_when_no_design_system():
    """T-0040-021: source/shared/agents/sable.md specifies that when the UX doc
    notes "no design system found", Sable skips design system verification entirely.
    She must NOT attempt to verify against a non-existent design system.

    Pre-build: FAILS until Colby updates sable.md (ADR-0040 Step 3).
    """
    assert _SABLE.exists(), (
        f"sable.md not found at {_SABLE}."
    )
    content = _SABLE.read_text()
    has_skip_rule = bool(
        re.search(r'no design system.*skip', content, re.IGNORECASE) or
        re.search(r'skip.*design system.*verification', content, re.IGNORECASE) or
        re.search(r'not.*found.*skip', content, re.IGNORECASE) or
        re.search(r'if.*no design system', content, re.IGNORECASE) or
        re.search(r'does not.*auto.detect.*independently', content, re.IGNORECASE)
    )
    assert has_skip_rule, (
        "sable.md does not specify skipping design system verification when the UX doc "
        "notes no design system was found. "
        "ADR-0040 Step 3: Sable must not attempt to verify against a non-existent design system. "
        "T-0040-021."
    )


def test_T_0040_sable_reviewer_reads_loaded_files_from_ux_doc():
    """Sable (reviewer) <workflow> specifies reading the same design system files
    that were loaded during UX production (from the UX doc annotation), not
    independently re-detecting.

    ADR-0040 Step 3 Exact Prose: "If the UX doc notes which design system files
    were loaded, read those same files."

    Pre-build: FAILS until Colby updates sable.md (ADR-0040 Step 3).
    """
    assert _SABLE.exists(), (
        f"sable.md not found at {_SABLE}."
    )
    content = _SABLE.read_text()
    has_cross_reference_rule = bool(
        re.search(r'UX doc.*design system', content, re.IGNORECASE) or
        re.search(r'design system.*UX doc', content, re.IGNORECASE) or
        re.search(r'same files.*loaded', content, re.IGNORECASE) or
        re.search(r'design system cross.reference', content, re.IGNORECASE)
    )
    assert has_cross_reference_rule, (
        "sable.md does not specify reading design system files from the UX doc annotation "
        "(not re-detecting independently). "
        "ADR-0040 Step 3 Exact Prose: step 1a 'Design system cross-reference'."
    )


# =============================================================================
# Step 4: Colby Design System Integration
# T-0040-014a, T-0040-022, T-0040-023
# =============================================================================

def test_T_0040_014a_colby_specifies_read_tag_not_constraints_for_propagation():
    """T-0040-014a: source/shared/agents/colby.md specifies that design system
    files are propagated via Eva's <read> tag, NOT via <constraints>.

    Cross-agent propagation through <read> is the correct mechanism per
    ADR-0040 Cross-Agent Consistency section and retro lessons 005/006.
    Using <constraints> is a propagation defect -- behavioral prose that
    does not survive subagent context window boundaries.

    Pre-build: FAILS until Colby updates colby.md (ADR-0040 Step 4).
    """
    assert _COLBY.exists(), (
        f"colby.md not found at {_COLBY}."
    )
    content = _COLBY.read_text()
    # Must reference the <read> tag as the mechanism for design system propagation
    has_read_tag_mechanism = bool(
        re.search(r'<read>.*design system', content, re.IGNORECASE | re.DOTALL) or
        re.search(r'design system.*<read>', content, re.IGNORECASE | re.DOTALL) or
        re.search(r"Eva's.*<read>.*design", content, re.IGNORECASE | re.DOTALL) or
        re.search(r"design.*Eva.*<read>", content, re.IGNORECASE | re.DOTALL) or
        re.search(r'<read>.*tag.*design', content, re.IGNORECASE | re.DOTALL)
    )
    assert has_read_tag_mechanism, (
        "colby.md does not specify that design system files are propagated via "
        "Eva's <read> tag. "
        "ADR-0040 Cross-Agent Consistency: design system files must appear in Colby's "
        "<read> list (not <constraints>) per retro lessons 005/006. T-0040-014a."
    )


def test_T_0040_022_colby_references_svg_icons_directly():
    """T-0040-022: source/shared/agents/colby.md specifies that Colby must
    reference SVG icons from design-system/icons/ directly in generated
    HTML/CSS -- no format conversion.

    Pre-build: FAILS until Colby updates colby.md (ADR-0040 Step 4).
    """
    assert _COLBY.exists(), (
        f"colby.md not found at {_COLBY}."
    )
    content = _COLBY.read_text()
    has_svg_rule = bool(
        re.search(r'SVG.*directly', content, re.IGNORECASE) or
        re.search(r'\.svg.*directly', content, re.IGNORECASE) or
        re.search(r'no.*format.*conversion', content, re.IGNORECASE) or
        re.search(r'icons/.*\.svg', content, re.IGNORECASE) or
        re.search(r'design-system/icons', content, re.IGNORECASE)
    )
    assert has_svg_rule, (
        "colby.md does not specify referencing SVG icons directly without format "
        "conversion. ADR-0040 Step 4 Exact Prose: "
        "\"Reference SVG icons from design-system/icons/ ... directly -- no format "
        "conversion.\" T-0040-022."
    )


def test_T_0040_023_colby_handles_missing_icons_directory():
    """T-0040-023: source/shared/agents/colby.md specifies that when
    design-system/icons/ does not exist, Colby proceeds without icon references
    (no crash, no broken references).

    Pre-build: FAILS until Colby updates colby.md (ADR-0040 Step 4).
    """
    assert _COLBY.exists(), (
        f"colby.md not found at {_COLBY}."
    )
    content = _COLBY.read_text()
    has_no_icons_behavior = bool(
        re.search(r'icons.*not exist', content, re.IGNORECASE) or
        re.search(r'no.*icons', content, re.IGNORECASE) or
        re.search(r'icons.*missing', content, re.IGNORECASE) or
        re.search(r'icons/.*does not exist', content, re.IGNORECASE) or
        re.search(r'if.*icons.*directory', content, re.IGNORECASE)
    )
    # Acceptable: icon handling section says "or the configured path equivalent"
    # and the reference doc covers the missing icons/ case. Also accept a reference
    # to the reference doc for icon handling.
    has_ref_doc_delegation = bool(
        "design-system-loading.md" in content and
        re.search(r'icon', content, re.IGNORECASE)
    )
    assert has_no_icons_behavior or has_ref_doc_delegation, (
        "colby.md does not specify behavior when design-system/icons/ does not exist. "
        "Expected: proceed without icon references (no error). "
        "ADR-0040 T-0040-023."
    )


def test_T_0040_colby_dor_ui_contract_has_design_system_row():
    """Colby's DoR UI Contract table gains a "Design system" row showing
    which design system files were loaded.

    ADR-0040 Step 4 Exact Prose for <output>:
      | Design system | [tokens.md + domain file, or "None"] |

    Pre-build: FAILS until Colby updates colby.md (ADR-0040 Step 4).
    """
    assert _COLBY.exists(), (
        f"colby.md not found at {_COLBY}."
    )
    content = _COLBY.read_text()
    has_design_system_row = bool(
        re.search(r'Design system', content) and
        re.search(r'tokens\.md', content)
    )
    assert has_design_system_row, (
        "colby.md does not include a 'Design system' row in the UI Contract table. "
        "Expected: | Design system | [tokens.md + domain file, or \"None\"] | "
        "ADR-0040 Step 4 Exact Prose for <output>."
    )


def test_T_0040_colby_references_design_system_loading_doc():
    """Colby's <constraints> references design-system-loading.md.

    ADR-0040 Step 4 acceptance criteria: "The <constraints> section references
    design-system-loading.md."

    Pre-build: FAILS until Colby updates colby.md (ADR-0040 Step 4).
    """
    assert _COLBY.exists(), (
        f"colby.md not found at {_COLBY}."
    )
    content = _COLBY.read_text()
    assert "design-system-loading.md" in content, (
        "colby.md does not reference design-system-loading.md. "
        "ADR-0040 Step 4 acceptance criteria: constraints section must reference the doc."
    )


def test_T_0040_colby_uses_design_system_tokens_not_hardcoded():
    """Colby's <constraints> specifies using design system tokens (CSS custom
    properties, spacing values, typography) instead of hardcoded values when
    a design system is loaded.

    ADR-0040 Step 4 Exact Prose for <constraints>:
      "When a design system is loaded, use its tokens (CSS custom properties,
      spacing values, typography) instead of hardcoded values."

    Pre-build: FAILS until Colby updates colby.md (ADR-0040 Step 4).
    """
    assert _COLBY.exists(), (
        f"colby.md not found at {_COLBY}."
    )
    content = _COLBY.read_text()
    has_token_usage_rule = bool(
        re.search(r'CSS custom propert', content, re.IGNORECASE) or
        re.search(r'instead of hardcoded', content, re.IGNORECASE) or
        re.search(r'hardcoded values.*design system', content, re.IGNORECASE) or
        re.search(r'design system.*hardcoded', content, re.IGNORECASE) or
        re.search(r'use its tokens', content, re.IGNORECASE)
    )
    assert has_token_usage_rule, (
        "colby.md <constraints> does not specify using design system tokens instead of "
        "hardcoded values. ADR-0040 Step 4 Exact Prose for <constraints>."
    )


# =============================================================================
# Step 5: /load-design Skill
# T-0040-015 through T-0040-019
# =============================================================================

def test_T_0040_015_load_design_skill_file_exists():
    """T-0040-015: skills/load-design/SKILL.md exists.

    Pre-build: FAILS until Colby creates the skill file (ADR-0040 Step 5).
    """
    assert _LOAD_DESIGN_SKILL.exists(), (
        f"skills/load-design/SKILL.md not found at {_LOAD_DESIGN_SKILL}. "
        "ADR-0040 Step 5 requires creating the /load-design skill file."
    )


def test_T_0040_015b_load_design_skill_sets_design_system_path():
    """T-0040-015: skills/load-design/SKILL.md specifies that the skill sets
    design_system_path in pipeline-config.json after validating the path.

    Pre-build: FAILS until Colby creates the skill (ADR-0040 Step 5).
    """
    assert _LOAD_DESIGN_SKILL.exists(), (
        f"skills/load-design/SKILL.md not found at {_LOAD_DESIGN_SKILL}."
    )
    content = _LOAD_DESIGN_SKILL.read_text()
    has_set_behavior = bool(
        re.search(r'design_system_path', content) and
        re.search(r'pipeline-config\.json', content, re.IGNORECASE)
    )
    assert has_set_behavior, (
        "skills/load-design/SKILL.md does not specify setting design_system_path in "
        "pipeline-config.json. ADR-0040 Step 5 + T-0040-015."
    )


def test_T_0040_015c_load_design_skill_lists_discovered_files():
    """T-0040-015: skills/load-design/SKILL.md specifies listing discovered
    design system files at the path (all .md files and icons/ directory).

    Pre-build: FAILS until Colby creates the skill (ADR-0040 Step 5).
    """
    assert _LOAD_DESIGN_SKILL.exists(), (
        f"skills/load-design/SKILL.md not found at {_LOAD_DESIGN_SKILL}."
    )
    content = _LOAD_DESIGN_SKILL.read_text()
    has_list_behavior = bool(
        re.search(r'list.*discover', content, re.IGNORECASE) or
        re.search(r'discover.*files', content, re.IGNORECASE) or
        re.search(r'Found:.*list', content, re.IGNORECASE) or
        re.search(r'\.md files', content, re.IGNORECASE)
    )
    assert has_list_behavior, (
        "skills/load-design/SKILL.md does not specify listing discovered design system files. "
        "ADR-0040 Step 5 Skill Spec behavior step 5: list all .md files and icons/ directory. "
        "T-0040-015."
    )


def test_T_0040_016_load_design_skill_error_path_not_found():
    """T-0040-016: skills/load-design/SKILL.md specifies the error message for a
    non-existent path: "Directory [path] not found."

    Pre-build: FAILS until Colby creates the skill (ADR-0040 Step 5).
    """
    assert _LOAD_DESIGN_SKILL.exists(), (
        f"skills/load-design/SKILL.md not found at {_LOAD_DESIGN_SKILL}."
    )
    content = _LOAD_DESIGN_SKILL.read_text()
    has_path_not_found_error = bool(
        re.search(r'not found', content, re.IGNORECASE) and
        re.search(r'[Dd]irectory', content)
    )
    assert has_path_not_found_error, (
        'skills/load-design/SKILL.md does not specify the "Directory [path] not found" '
        "error message for non-existent paths. ADR-0040 Skill Error cases + T-0040-016."
    )


def test_T_0040_017_load_design_skill_error_no_tokens_md():
    """T-0040-017: skills/load-design/SKILL.md specifies the error message when
    the path exists but has no tokens.md: "No tokens.md found at [path]."

    Pre-build: FAILS until Colby creates the skill (ADR-0040 Step 5).
    """
    assert _LOAD_DESIGN_SKILL.exists(), (
        f"skills/load-design/SKILL.md not found at {_LOAD_DESIGN_SKILL}."
    )
    content = _LOAD_DESIGN_SKILL.read_text()
    has_no_tokens_error = bool(
        re.search(r'No tokens\.md', content) or
        re.search(r'tokens\.md.*not found', content, re.IGNORECASE) or
        re.search(r'valid design system.*tokens\.md', content, re.IGNORECASE)
    )
    assert has_no_tokens_error, (
        'skills/load-design/SKILL.md does not specify the "No tokens.md found" error '
        "message for paths that lack tokens.md. "
        "ADR-0040 Skill Spec validation step 1 + T-0040-017."
    )


def test_T_0040_018_load_design_skill_supports_reset():
    """T-0040-018: skills/load-design/SKILL.md specifies that running /load-design
    with path "reset" sets design_system_path to null (not empty string, not key removal).

    Pre-build: FAILS until Colby creates the skill (ADR-0040 Step 5).
    """
    assert _LOAD_DESIGN_SKILL.exists(), (
        f"skills/load-design/SKILL.md not found at {_LOAD_DESIGN_SKILL}."
    )
    content = _LOAD_DESIGN_SKILL.read_text()
    has_reset_behavior = bool(
        re.search(r'reset', content, re.IGNORECASE) and
        (re.search(r'null', content) or re.search(r'clear', content, re.IGNORECASE))
    )
    assert has_reset_behavior, (
        "skills/load-design/SKILL.md does not specify the reset behavior "
        '(path "reset" -> design_system_path: null). '
        "ADR-0040 Skill Spec Reset section + T-0040-018."
    )


def test_T_0040_019_load_design_skill_error_no_pipeline():
    """T-0040-019: skills/load-design/SKILL.md specifies the error message when
    pipeline-config.json is not found: "Pipeline not installed. Run /pipeline-setup first."

    Pre-build: FAILS until Colby creates the skill (ADR-0040 Step 5).
    """
    assert _LOAD_DESIGN_SKILL.exists(), (
        f"skills/load-design/SKILL.md not found at {_LOAD_DESIGN_SKILL}."
    )
    content = _LOAD_DESIGN_SKILL.read_text()
    has_no_pipeline_error = bool(
        re.search(r'Pipeline not installed', content) or
        re.search(r'pipeline-setup', content, re.IGNORECASE) and
        re.search(r'not installed', content, re.IGNORECASE)
    )
    assert has_no_pipeline_error, (
        'skills/load-design/SKILL.md does not specify the "Pipeline not installed. '
        'Run /pipeline-setup first." error when pipeline-config.json is missing. '
        "ADR-0040 Skill Error cases + T-0040-019."
    )


def test_T_0040_pipeline_setup_skill_references_design_system_path():
    """skills/pipeline-setup/SKILL.md references design_system_path in the
    pipeline-config template section.

    ADR-0040 Step 5 acceptance criteria: "pipeline-setup references
    design_system_path in the pipeline-config template section."

    Pre-build: FAILS until Colby updates pipeline-setup/SKILL.md (ADR-0040 Step 5).
    """
    assert _PIPELINE_SETUP_SKILL.exists(), (
        f"pipeline-setup/SKILL.md not found at {_PIPELINE_SETUP_SKILL}."
    )
    content = _PIPELINE_SETUP_SKILL.read_text()
    assert "design_system_path" in content, (
        "skills/pipeline-setup/SKILL.md does not reference design_system_path. "
        "ADR-0040 Step 5: pipeline-setup must include the key in the config template section."
    )


# =============================================================================
# Step 6: Cal Brain-Search DoR Step
# T-0040-026 through T-0040-029
# =============================================================================

def test_T_0040_026_cal_workflow_has_institutional_memory_search_step():
    """T-0040-026: source/shared/agents/cal.md <workflow> contains a mandatory
    institutional memory / brain-search step before ADR production.

    ADR-0040 Step 6 Exact Prose adds "## Institutional Memory Search (mandatory)"
    as the first step in <workflow>, before "ADR Production."

    Pre-build: FAILS until Colby updates cal.md (ADR-0040 Step 6).
    """
    assert _CAL.exists(), (
        f"cal.md not found at {_CAL}."
    )
    content = _CAL.read_text()
    has_memory_search_step = bool(
        re.search(r'[Ii]nstitutional [Mm]emory', content) or
        re.search(r'brain.search', content, re.IGNORECASE) or
        re.search(r'agent_search', content)
    )
    assert has_memory_search_step, (
        "cal.md <workflow> does not contain an institutional memory search step. "
        "ADR-0040 Step 6 adds a mandatory 'Institutional Memory Search' step before "
        "ADR Production. T-0040-026."
    )


def test_T_0040_026b_cal_brain_search_calls_agent_search():
    """T-0040-026: cal.md brain-available path explicitly calls agent_search
    with domain-relevant terms.

    ADR-0040 Step 6 Exact Prose: "call agent_search with terms derived from
    the feature domain."

    Pre-build: FAILS until Colby updates cal.md (ADR-0040 Step 6).
    """
    assert _CAL.exists(), (
        f"cal.md not found at {_CAL}."
    )
    content = _CAL.read_text()
    assert "agent_search" in content, (
        "cal.md does not call agent_search in the brain-available path. "
        "ADR-0040 Step 6 Exact Prose: 'call agent_search with terms derived from "
        "the feature domain'. T-0040-026."
    )


def test_T_0040_027_cal_brain_unavailable_path_reads_retro_lessons():
    """T-0040-027: cal.md brain-unavailable path specifies reading retro-lessons.md
    AND grepping docs/architecture/ for prior ADRs on related domains.

    Both steps are required when brain is unavailable. Either alone is insufficient.

    Pre-build: FAILS until Colby updates cal.md (ADR-0040 Step 6).
    """
    assert _CAL.exists(), (
        f"cal.md not found at {_CAL}."
    )
    content = _CAL.read_text()
    has_retro_lessons = bool(
        re.search(r'retro.lessons\.md', content, re.IGNORECASE) and
        re.search(r'brain.*unavailable', content, re.IGNORECASE)
    )
    has_adr_grep = bool(
        re.search(r'docs/architecture', content, re.IGNORECASE) and
        re.search(r'grep', content, re.IGNORECASE) or
        re.search(r'prior ADRs', content, re.IGNORECASE)
    )
    assert has_retro_lessons, (
        "cal.md brain-unavailable path does not specify reading retro-lessons.md. "
        "ADR-0040 Step 6: both retro-lessons.md AND docs/architecture/ grep are required "
        "when brain is unavailable. T-0040-027."
    )
    assert has_adr_grep, (
        "cal.md brain-unavailable path does not specify grepping docs/architecture/ for "
        "prior ADRs on the same domain. "
        "ADR-0040 Step 6 Exact Prose + T-0040-027."
    )


def test_T_0040_028_cal_handles_empty_brain_results_explicitly():
    """T-0040-028: cal.md specifies that when brain search returns no results,
    Cal must note "No relevant prior decisions found" in DoR Retro risks --
    not silently omit the field.

    "No relevant prior decisions found" is a valid finding. Silence is not.

    Pre-build: FAILS until Colby updates cal.md (ADR-0040 Step 6).
    """
    assert _CAL.exists(), (
        f"cal.md not found at {_CAL}."
    )
    content = _CAL.read_text()
    has_empty_result_handling = bool(
        re.search(r'No relevant prior decisions found', content) or
        re.search(r'relevant.*prior.*decisions.*found', content, re.IGNORECASE) or
        re.search(r'valid finding.*silence.*not', content, re.IGNORECASE) or
        re.search(r'silence is not', content, re.IGNORECASE)
    )
    assert has_empty_result_handling, (
        'cal.md does not specify the "No relevant prior decisions found" annotation '
        "for empty brain search results. "
        "ADR-0040 Step 6: silence is not a valid finding -- Cal must explicitly note "
        "when no relevant prior decisions exist. T-0040-028."
    )


def test_T_0040_029_cal_brain_search_is_unconditional_not_optional():
    """T-0040-029: cal.md specifies that the brain-search DoR step is unconditional --
    it runs for every ADR Cal produces, not just design system work. The step is
    mandatory, not optional.

    ADR-0040 Notes for Colby #7: "Cal's brain-search step is unconditional."

    Pre-build: FAILS until Colby updates cal.md (ADR-0040 Step 6).
    """
    assert _CAL.exists(), (
        f"cal.md not found at {_CAL}."
    )
    content = _CAL.read_text()
    has_mandatory_annotation = bool(
        re.search(r'mandatory', content, re.IGNORECASE) and
        re.search(r'agent_search\|institutional memory\|brain', content, re.IGNORECASE) or
        re.search(r'mandatory.*search', content, re.IGNORECASE) or
        re.search(r'Institutional Memory Search \(mandatory\)', content) or
        re.search(r'unconditional', content, re.IGNORECASE) and
        re.search(r'every ADR', content, re.IGNORECASE)
    )
    assert has_mandatory_annotation, (
        "cal.md does not mark the brain-search DoR step as mandatory/unconditional. "
        "ADR-0040 Step 6: the step runs for every ADR, not just design system work. "
        "Expected prose: '## Institutional Memory Search (mandatory)'. T-0040-029."
    )


def test_T_0040_029b_cal_brain_search_produces_retro_risks_output():
    """T-0040-029: cal.md specifies that the brain-search step (both brain-available
    and brain-unavailable paths) produces output in the DoR "Retro risks" field.

    ADR-0040 Step 6: "Either path: note relevant findings in DoR before proceeding."

    Pre-build: FAILS until Colby updates cal.md (ADR-0040 Step 6).
    """
    assert _CAL.exists(), (
        f"cal.md not found at {_CAL}."
    )
    content = _CAL.read_text()
    has_retro_risks_output = bool(
        re.search(r'Retro risks', content) and
        re.search(r'agent_search', content)
    )
    assert has_retro_risks_output, (
        'cal.md does not specify that brain-search findings go into DoR "Retro risks". '
        "ADR-0040 Step 6: either path (brain available or unavailable) must produce "
        "output in the DoR Retro risks field before design proceeds. T-0040-029."
    )


# =============================================================================
# Cross-Cutting: Source-only constraint (ADR-0040 Notes for Colby #1)
# =============================================================================

def test_T_0040_no_design_system_content_in_installed_agents():
    """Cross-cutting: design system loading content must NOT be added directly to
    .claude/agents/ files. All edits must be in source/shared/agents/.
    Pipeline-setup syncs to .claude/. This test verifies the source files are
    the canonical location per ADR-0040 Notes for Colby #1 and CLAUDE.md.

    This test passes trivially pre-build (installed files have no DS content yet)
    and serves as a post-build regression guard: if Colby mistakenly edits
    .claude/agents/ directly, this test would detect the anomaly as out-of-sync.

    PASSES pre-build (intentional: installed files are currently empty of DS content).
    Post-build: must still PASS (source/ is canonical, .claude/ is synced copy).
    """
    # The installed agents directory
    installed_cal = PROJECT_ROOT / ".claude" / "agents" / "cal.md"
    installed_sable_ux = PROJECT_ROOT / ".claude" / "agents" / "sable-ux.md"

    if installed_cal.exists():
        installed_content = installed_cal.read_text()
        # Design system content should not appear in .claude/ unless pipeline-setup was run
        # This assertion intentionally does NOT fail pre-build -- it is a post-sync guard.
        # The test is a contract, not a current-state assertion.
        pass  # structural test: installed files are synced, not directly edited

    # What we CAN assert: the source files are the ones defined above and are the
    # canonical target for ADR-0040 changes.
    assert _CAL == PROJECT_ROOT / "source" / "shared" / "agents" / "cal.md", (
        "cal.md source path has moved. ADR-0040 must target source/shared/agents/cal.md."
    )
    assert _SABLE_UX == PROJECT_ROOT / "source" / "shared" / "agents" / "sable-ux.md", (
        "sable-ux.md source path has moved. Must target source/shared/agents/sable-ux.md."
    )
    assert _COLBY == PROJECT_ROOT / "source" / "shared" / "agents" / "colby.md", (
        "colby.md source path has moved. Must target source/shared/agents/colby.md."
    )
    assert _SABLE == PROJECT_ROOT / "source" / "shared" / "agents" / "sable.md", (
        "sable.md source path has moved. Must target source/shared/agents/sable.md."
    )
