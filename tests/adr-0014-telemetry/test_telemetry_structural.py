"""ADR-0014: Agent Telemetry Dashboard -- Structural Tests.

Tests: T-0014-001 through T-0014-056 (62 tests).
Migrated from telemetry-structural.test.bats.
"""

import re

import pytest

from tests.conftest import (
    INSTALLED_REFS,
    INSTALLED_RULES,
    PROJECT_ROOT,
    SOURCE_REFS,
    SOURCE_RULES,
    extract_protocol_section,
    extract_section,
)


# ═══════════════════════════════════════════════════════════════════════
# Step 1: Telemetry Metrics Reference
# ═══════════════════════════════════════════════════════════════════════

def test_T_0014_001_telemetry_metrics_exists():
    assert (SOURCE_REFS / "telemetry-metrics.md").is_file()
    assert (INSTALLED_REFS / "telemetry-metrics.md").is_file()


def test_T_0014_002_tier_1_metric_fields():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text()
    fields = ["input_tokens", "output_tokens", "cache_read_tokens", "duration_ms", "model",
              "cost_usd", "finish_reason", "tool_count", "turn_count", "context_utilization",
              "agent_name", "pipeline_phase", "work_unit_id", "is_retry"]
    errors = [f"Missing Tier 1 field: {f}" for f in fields if f not in content]
    assert not errors, "\n".join(errors)


def test_T_0014_003_tier_2_metric_fields():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text()
    fields = ["rework_cycles", "first_pass_qa", "unit_cost_usd",
              "finding_counts", "finding_convergence", "evoscore_delta"]
    errors = [f"Missing Tier 2 field: {f}" for f in fields if f not in content]
    assert not errors, "\n".join(errors)


def test_T_0014_004_tier_3_metric_fields():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text()
    fields = ["total_cost_usd", "total_duration_ms", "phase_durations",
              "total_invocations", "invocations_by_agent", "rework_rate",
              "first_pass_qa_rate", "agent_failures", "evoscore",
              "regression_count", "sizing"]
    errors = [f"Missing Tier 3 field: {f}" for f in fields if f not in content]
    assert not errors, "\n".join(errors)


def test_T_0014_005_cost_table_covers_models():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text().lower()
    assert "opus" in content
    assert "sonnet" in content
    assert "haiku" in content
    assert "input" in content
    assert "output" in content


def test_T_0014_006_evoscore_tests_before_zero():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text()
    assert "tests_before" in content and "0" in content
    assert "1.0" in content


def test_T_0014_007_defaults_for_unavailable_data():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text().lower()
    assert re.search(r"default|unavailable|fallback|missing", content)


def test_T_0014_008_alert_thresholds():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text()
    errors = []
    if not re.search(r"25%|0\.25|25 ?percent", content): errors.append("Missing cost threshold >25%")
    if "2.0" not in content: errors.append("Missing rework threshold 2.0")
    if not re.search(r"60%|0\.60|60 ?percent", content): errors.append("Missing first-pass QA threshold 60%")
    if not re.search(r">.*2|more than 2|exceeds 2", content): errors.append("Missing agent failures threshold >2")
    if not re.search(r"80%|0\.80|80 ?percent", content): errors.append("Missing context utilization threshold 80%")
    if not re.search(r"0\.9|< ?0\.9", content): errors.append("Missing EvoScore threshold 0.9")
    assert not errors, "\n".join(errors)


def test_T_0014_009_no_undefined_default():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text().lower()
    assert not re.search(r"default.*undefined", content)


def test_T_0014_052_cost_table_model_alignment():
    metrics = (INSTALLED_REFS / "telemetry-metrics.md").read_text().lower()
    for model in ["opus", "sonnet", "haiku"]:
        assert model in metrics, f"Model {model} missing from cost table"


def test_T_0014_053_tier_2_references_tier_1():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text()
    assert "cost_usd" in content
    assert "unit_cost_usd" in content


def test_T_0014_054_context_window_max():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text()
    assert "context_window_max" in content


# ═══════════════════════════════════════════════════════════════════════
# Step 2: Telemetry Capture Protocol
# ═══════════════════════════════════════════════════════════════════════

def test_T_0014_010_telemetry_capture_protocol_exists():
    content = (INSTALLED_RULES / "pipeline-orchestration.md").read_text()
    assert '<protocol id="telemetry-capture">' in content


def test_T_0014_010b_source_has_telemetry_capture():
    content = (SOURCE_RULES / "pipeline-orchestration.md").read_text()
    assert '<protocol id="telemetry-capture">' in content


def test_T_0014_011_tier_1_capture_metadata():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol, "telemetry-capture protocol not found"
    assert "insight" in protocol
    assert "eva" in protocol
    assert "telemetry" in protocol
    assert "telemetry_tier" in protocol


def test_T_0014_012_tier_2_triggers_after_qa_pass():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert re.search(r"tier 2|roz.*qa.*pass|qa.*pass", protocol, re.IGNORECASE)


def test_T_0014_013_tier_2_includes_required_fields():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    fields = ["rework_cycles", "first_pass_qa", "unit_cost_usd", "finding_counts", "finding_convergence", "evoscore_delta"]
    errors = [f"Missing Tier 2 field: {f}" for f in fields if f not in protocol]
    assert not errors, "\n".join(errors)


def test_T_0014_014_tier_3_triggers_at_pipeline_end():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert re.search(r"tier 3|pipeline end|ellis", protocol, re.IGNORECASE)


def test_T_0014_015_tier_3_includes_required_fields():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    fields = ["total_cost_usd", "total_duration_ms", "rework_rate", "first_pass_qa_rate", "evoscore"]
    errors = [f"Missing Tier 3 field: {f}" for f in fields if f not in protocol]
    assert not errors, "\n".join(errors)


def test_T_0014_016_log_and_continue():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert re.search(r"log.*continue|continue.*never.*block|non.?blocking", protocol, re.IGNORECASE)


def test_T_0014_017_brain_unavailable_skips():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert re.search(r"brain.*unavailable.*skip|brain_available.*false.*skip", protocol, re.IGNORECASE)


def test_T_0014_018_micro_tier_1_only():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert re.search(r"micro.*tier 1|micro.*skip.*tier 2|micro.*skip.*tier 3", protocol, re.IGNORECASE)


def test_T_0014_019_tier_1_failure_not_blocking():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert re.search(r"log.*continue|fail.*continue|never.*block", protocol, re.IGNORECASE)


def test_T_0014_020_references_metrics():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert "telemetry-metrics.md" in protocol


def test_T_0014_021_additive():
    """Tier 2 captures are additive (bulk-captured, not replacing prior data)."""
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert re.search(r"additive|do not replace|not.*replace|bulk.captured|includes bulk", protocol, re.IGNORECASE)


def test_T_0014_022_pipeline_id_format():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text()
    assert "pipeline_id" in content
    assert re.search(r"feature.*timestamp|feature_name.*iso|feature_name.*time", content, re.IGNORECASE)


def test_T_0014_023_brain_capture_protocol_unchanged():
    content = (INSTALLED_RULES / "pipeline-orchestration.md").read_text()
    assert '<protocol id="brain-capture">' in content


def test_T_0014_055_importance_graduation():
    """Importance values graduate by tier: T2=0.5, T3=0.7 (T1 is in-memory only, no importance)."""
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert "0.5" in protocol
    assert "0.7" in protocol


# ═══════════════════════════════════════════════════════════════════════
# Step 3: Pipeline-End Summary + Boot Trend Query
# ═══════════════════════════════════════════════════════════════════════

def test_T_0014_024_telemetry_summary_exists():
    content = (INSTALLED_RULES / "pipeline-orchestration.md").read_text()
    assert re.search(r"telemetry summary", content, re.IGNORECASE)


def test_T_0014_025_summary_includes_key_terms():
    content = (INSTALLED_RULES / "pipeline-orchestration.md").read_text()
    summary = extract_section(content, r"telemetry summary", r"^##")
    errors = [f"Missing: {t}" for t in ["cost", "duration", "rework", "EvoScore", "findings"]
              if not re.search(t, summary, re.IGNORECASE)]
    assert not errors, "\n".join(errors)


def test_T_0014_026_boot_step_5b():
    """Boot step 5b (telemetry trend query) is in session-boot.md."""
    content = (INSTALLED_REFS / "session-boot.md").read_text()
    assert re.search(r"[Ss]tep 5b|^5b\.|^\*\*5b", content, re.MULTILINE)
    step5b = extract_section(content, r"[Ss]tep 5b", r"^[0-9]+\.|^##")
    assert re.search(r"telemetry", step5b, re.IGNORECASE)


def test_T_0014_026b_source_boot_step_5b():
    """Source session-boot.md also contains step 5b."""
    content = (SOURCE_REFS / "session-boot.md").read_text()
    assert re.search(r"[Ss]tep 5b|^5b\.|^\*\*5b", content, re.MULTILINE)


def test_T_0014_027_boot_telemetry_trend():
    content = (INSTALLED_RULES / "default-persona.md").read_text()
    assert re.search(r"telemetry.*trend|trend.*telemetry|pipeline.*telemetry.*line|telemetry.*line", content, re.IGNORECASE)


def test_T_0014_028_no_prior_data():
    """Session boot handles the no-prior-data case."""
    content = (INSTALLED_REFS / "session-boot.md").read_text()
    assert re.search(r"no prior.*pipeline.*data|no.*telemetry.*data|first.*pipeline.*telemetry|no.*trend.*data|No prior pipeline data", content, re.IGNORECASE)


def test_T_0014_029_micro_abbreviated():
    content = (INSTALLED_RULES / "pipeline-orchestration.md").read_text()
    assert re.search(r"micro.*abbreviated|micro.*invocation.*count|micro.*duration.*only", content, re.IGNORECASE)


def test_T_0014_030_in_memory_accumulators():
    content = (INSTALLED_RULES / "pipeline-orchestration.md").read_text()
    assert re.search(r"in.memory.*accumulator|accumulator.*brain.*unavail|accumulator.*fallback", content, re.IGNORECASE)


def test_T_0014_031_omit_telemetry_brain_unavailable():
    """Session boot omits telemetry when brain unavailable."""
    content = (INSTALLED_REFS / "session-boot.md").read_text()
    assert re.search(r"brain.*unavailable.*omit.*telemetry|omit.*telemetry.*brain|telemetry.*omit.*brain|skip.*telemetry.*brain.*unavail|brain unavailable.*skip|omit telemetry line entirely", content, re.IGNORECASE)


def test_T_0014_032_degradation_3_consecutive():
    """Session boot describes degradation alert threshold of 3 consecutive."""
    content = (INSTALLED_REFS / "session-boot.md").read_text()
    assert re.search(r"degrad.*3.*consecutive|3.*consecutive.*breach|alert.*3.*consecutive|consecutive.*threshold|3\+.*consecutive", content, re.IGNORECASE)


def test_T_0014_033_threshold_is_3_consecutive():
    content = (INSTALLED_REFS / "telemetry-metrics.md").read_text()
    assert re.search(r"3.*consecutive|consecutive.*3", content)


def test_T_0014_034_cost_unavailable():
    protocol = extract_protocol_section(INSTALLED_RULES / "pipeline-orchestration.md", "telemetry-capture")
    assert protocol
    assert re.search(r"cost.*unavailable|token.*count.*not.*exposed|cost.*null", protocol, re.IGNORECASE)


def test_T_0014_035_source_placeholder():
    content = (SOURCE_RULES / "default-persona.md").read_text()
    assert "{pipeline_state_dir}" in content


def test_T_0014_036_installed_literal_path():
    content = (INSTALLED_RULES / "default-persona.md").read_text()
    assert "docs/pipeline" in content


def test_T_0014_037_existing_boot_step_1():
    assert "pipeline-state.md" in (INSTALLED_RULES / "default-persona.md").read_text()


def test_T_0014_037b_existing_boot_step_4():
    """Boot step 4 (brain health check via atelier_stats) is in session-boot.md."""
    assert "atelier_stats" in (INSTALLED_REFS / "session-boot.md").read_text()


def test_T_0014_038_brain_capture_protocol_still_exists():
    assert '<protocol id="brain-capture">' in (INSTALLED_RULES / "pipeline-orchestration.md").read_text()


def test_T_0014_039_boot_telemetry_tier_3():
    """Boot step 5b references telemetry tier 3."""
    content = (INSTALLED_REFS / "session-boot.md").read_text()
    assert re.search(r"telemetry_tier.*3|telemetry.*tier.*3", content, re.IGNORECASE)


def test_T_0014_040_single_pipeline_no_trend():
    """Session boot handles single-pipeline case (no trend comparison)."""
    content = (INSTALLED_REFS / "session-boot.md").read_text()
    assert re.search(r"single.*pipeline.*trend|1.*pipeline.*no.*trend|no.*trend.*percentage|need.*2.*pipeline|2\+.*for.*comparison|single-pipeline|exactly 1 result", content, re.IGNORECASE)


def test_T_0014_056_micro_not_in_trends():
    """Micro pipelines skip Tier 2/3 and trends (Tier 1 only)."""
    content = (INSTALLED_RULES / "pipeline-orchestration.md").read_text()
    assert re.search(r"micro.*not.*trend|micro.*tier 3.*skip|micro.*exclude.*trend|[Mm]icro.*[Tt]ier 1 only|Skipped on Micro|Micro.*Tier 1", content, re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════════════
# Step 4: Invocation Template + PIPELINE_STATUS
# ═══════════════════════════════════════════════════════════════════════

def test_T_0014_041_timing_protocol():
    content = (INSTALLED_REFS / "invocation-templates.md").read_text()
    assert re.search(r"telemetry.*timing|wall.clock.*telemetry|start_time.*end_time|timing.*protocol.*telemetry", content, re.IGNORECASE)


def _get_ops_file():
    f = INSTALLED_REFS / "pipeline-operations.md"
    if f.is_file():
        return f
    f = INSTALLED_RULES / "pipeline-operations.md"
    if f.is_file():
        return f
    pytest.skip("pipeline-operations.md not found")


def test_T_0014_042_pipeline_status_telemetry_id():
    assert "telemetry_pipeline_id" in _get_ops_file().read_text()


def test_T_0014_042b_pipeline_status_invocations():
    assert "telemetry_total_invocations" in _get_ops_file().read_text()


def test_T_0014_042c_pipeline_status_cost():
    assert "telemetry_total_cost_usd" in _get_ops_file().read_text()


def test_T_0014_042d_pipeline_status_rework():
    assert "telemetry_rework_by_unit" in _get_ops_file().read_text()


def test_T_0014_043_mask_section_lists_tier_1():
    content = _get_ops_file().read_text()
    mask_section = extract_section(content, r"^### Mask", r"^###")
    if not mask_section:
        pytest.skip("### Mask section not found")
    assert re.search(r"tier 1|telemetry.*capture|telemetry.*response", mask_section, re.IGNORECASE)


def test_T_0014_044_pipeline_status_field_types():
    content = _get_ops_file().read_text()
    assert "telemetry_pipeline_id" in content
    assert "telemetry_total_invocations" in content


def test_T_0014_045_session_recovery():
    content = _get_ops_file().read_text()
    assert re.search(r"telemetry.*recover|telemetry.*restore|telemetry.*resume|restore.*telemetry.*accumulator|accumulator.*restore", content, re.IGNORECASE)


def test_T_0014_046_roz_qa_still_present():
    assert "roz_qa" in (INSTALLED_RULES / "pipeline-orchestration.md").read_text()


def test_T_0014_047_dual_tree_sync():
    assert "telemetry-capture" in (INSTALLED_RULES / "pipeline-orchestration.md").read_text()
    assert "telemetry-capture" in (SOURCE_RULES / "pipeline-orchestration.md").read_text()


def test_T_0014_050_zero_default():
    content = _get_ops_file().read_text()
    assert re.search(r"telemetry.*absent.*zero|telemetry.*default.*0|telemetry.*initial.*zero|telemetry.*field.*absent|absent.*telemetry", content, re.IGNORECASE)


def test_T_0014_051_never_mask_telemetry():
    content = _get_ops_file().read_text()
    never_mask = extract_section(content, r"^### Never Mask", r"^###")
    if not never_mask:
        pytest.skip("### Never Mask section not found")
    assert re.search(r"telemetry|accumulator", never_mask, re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════════════
# Step 5: Documentation
# ═══════════════════════════════════════════════════════════════════════

def test_T_0014_048_adr_entry_in_readme():
    f = PROJECT_ROOT / "docs" / "architecture" / "README.md"
    if not f.is_file():
        pytest.skip("README.md not found")
    assert "ADR-0014" in f.read_text()


def test_T_0014_049_adr_entry_title():
    f = PROJECT_ROOT / "docs" / "architecture" / "README.md"
    if not f.is_file():
        pytest.skip("README.md not found")
    content = f.read_text()
    assert re.search(r"ADR-0014.*telemetry|telemetry.*ADR-0014", content, re.IGNORECASE)
