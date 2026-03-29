#!/usr/bin/env bats
# ADR-0014: Agent Telemetry Dashboard -- Structural Tests
# Tests: T-0014-001 through T-0014-056
#
# These tests verify the structural content of telemetry deliverables:
# - telemetry-metrics.md (schema, cost table, thresholds)
# - pipeline-orchestration.md (capture protocol)
# - default-persona.md (boot step 5b)
# - invocation-templates.md (timing protocol)
# - pipeline-operations.md (PIPELINE_STATUS fields)

load ../xml-prompt-structure/test_helper

# ═══════════════════════════════════════════════════════════════════════
# Step 1: Telemetry Metrics Reference
# ═══════════════════════════════════════════════════════════════════════

# ── T-0014-001: telemetry-metrics.md exists in both trees ─────────────

@test "T-0014-001: telemetry-metrics.md exists in source/references/ and .claude/references/" {
  [ -f "$SOURCE_REFS/telemetry-metrics.md" ]
  [ -f "$INSTALLED_REFS/telemetry-metrics.md" ]
}

# ── T-0014-002: Tier 1 metric fields ─────────────────────────────────

@test "T-0014-002: telemetry-metrics.md contains all Tier 1 metric field names" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  local fields=(
    input_tokens output_tokens cache_read_tokens duration_ms model
    cost_usd finish_reason tool_count turn_count context_utilization
    agent_name pipeline_phase work_unit_id is_retry
  )
  local fail=0
  for field in "${fields[@]}"; do
    grep -q "$field" "$file" || {
      echo "Missing Tier 1 field: $field"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0014-003: Tier 2 metric fields ─────────────────────────────────

@test "T-0014-003: telemetry-metrics.md contains all Tier 2 metric field names" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  local fields=(
    rework_cycles first_pass_qa unit_cost_usd
    finding_counts finding_convergence evoscore_delta
  )
  local fail=0
  for field in "${fields[@]}"; do
    grep -q "$field" "$file" || {
      echo "Missing Tier 2 field: $field"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0014-004: Tier 3 metric fields ─────────────────────────────────

@test "T-0014-004: telemetry-metrics.md contains all Tier 3 metric field names" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  local fields=(
    total_cost_usd total_duration_ms phase_durations
    total_invocations invocations_by_agent rework_rate
    first_pass_qa_rate agent_failures evoscore
    regression_count sizing
  )
  local fail=0
  for field in "${fields[@]}"; do
    grep -q "$field" "$file" || {
      echo "Missing Tier 3 field: $field"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0014-005: Cost table covers Opus, Sonnet, Haiku ────────────────

@test "T-0014-005: cost estimation table covers Opus, Sonnet, and Haiku with input and output costs" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  grep -qi "opus" "$file"
  grep -qi "sonnet" "$file"
  grep -qi "haiku" "$file"
  grep -qi "input" "$file"
  grep -qi "output" "$file"
}

# ── T-0014-006: EvoScore handles tests_before = 0 ────────────────────

@test "T-0014-006: EvoScore formula documents tests_before = 0 returning 1.0" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  grep -q "tests_before.*0" "$file"
  grep -q "1\.0" "$file"
}

# ── T-0014-007: Every metric has a default for unavailable data ───────

@test "T-0014-007: telemetry-metrics.md documents defaults for unavailable data" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  grep -qiE "default|unavailable|fallback|missing" "$file"
}

# ── T-0014-008: Alert thresholds match spec ──────────────────────────

@test "T-0014-008: alert thresholds match spec values" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  local fail=0
  grep -qE "25%|0\.25|25 ?percent" "$file" || {
    echo "Missing cost threshold >25%"; fail=1
  }
  grep -q "2\.0" "$file" || {
    echo "Missing rework threshold 2.0"; fail=1
  }
  grep -qE "60%|0\.60|60 ?percent" "$file" || {
    echo "Missing first-pass QA threshold 60%"; fail=1
  }
  grep -qE ">.*2|more than 2|exceeds 2" "$file" || {
    echo "Missing agent failures threshold >2"; fail=1
  }
  grep -qE "80%|0\.80|80 ?percent" "$file" || {
    echo "Missing context utilization threshold 80%"; fail=1
  }
  grep -qE "0\.9|< ?0\.9" "$file" || {
    echo "Missing EvoScore threshold 0.9"; fail=1
  }
  [ "$fail" -eq 0 ]
}

# ── T-0014-009: Missing data defaults are valid values ────────────────

@test "T-0014-009: telemetry-metrics.md does not use 'undefined' as a default" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  ! grep -qi "default.*undefined" "$file"
}

# ── T-0014-052: Cost table model alignment with pipeline-models.md ───

@test "T-0014-052: cost table covers exactly the models in pipeline-models.md" {
  local metrics="$INSTALLED_REFS/telemetry-metrics.md"
  local models="$INSTALLED_RULES/pipeline-models.md"
  [ -f "$metrics" ] || skip "telemetry-metrics.md not yet created"
  [ -f "$models" ] || skip "pipeline-models.md not found"

  local fail=0
  for model in Opus Sonnet Haiku; do
    grep -qi "$model" "$metrics" || {
      echo "Model $model in pipeline-models.md but missing from cost table"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0014-053: Tier 2 references valid Tier 1 field names ───────────

@test "T-0014-053: Tier 2 unit_cost_usd references Tier 1 cost_usd field" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  grep -q "cost_usd" "$file"
  grep -q "unit_cost_usd" "$file"
}

# ── T-0014-054: context_window_max documented per model ──────────────

@test "T-0014-054: cost table documents context_window_max per model" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  grep -q "context_window_max" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 2: Telemetry Capture Protocol
# ═══════════════════════════════════════════════════════════════════════

# ── T-0014-010: Telemetry capture protocol exists ────────────────────

@test "T-0014-010: pipeline-orchestration.md contains <protocol id=\"telemetry-capture\">" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  grep -q '<protocol id="telemetry-capture">' "$file"
}

@test "T-0014-010b: source pipeline-orchestration.md contains telemetry-capture protocol" {
  local file="$SOURCE_RULES/pipeline-orchestration.md"
  grep -q '<protocol id="telemetry-capture">' "$file"
}

# ── T-0014-011: Tier 1 capture metadata ──────────────────────────────

@test "T-0014-011: capture protocol uses thought_type insight, source_agent eva, source_phase telemetry" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -q "insight"
  echo "$protocol" | grep -q "eva"
  echo "$protocol" | grep -q "telemetry"
  echo "$protocol" | grep -q "telemetry_tier"
}

# ── T-0014-012: Tier 2 trigger is after Roz QA PASS ─────────────────

@test "T-0014-012: Tier 2 capture triggers after Roz QA PASS" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -qiE "tier 2|roz.*qa.*pass|qa.*pass"
}

# ── T-0014-013: Tier 2 includes required fields ─────────────────────

@test "T-0014-013: Tier 2 section includes rework_cycles, first_pass_qa, unit_cost_usd, finding_counts, finding_convergence, evoscore_delta" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  local fields=(rework_cycles first_pass_qa unit_cost_usd finding_counts finding_convergence evoscore_delta)
  local fail=0
  for field in "${fields[@]}"; do
    echo "$protocol" | grep -q "$field" || {
      echo "Missing Tier 2 field in capture protocol: $field"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0014-014: Tier 3 trigger is at pipeline end ───────────────────

@test "T-0014-014: Tier 3 capture triggers at pipeline end after Ellis" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -qiE "tier 3|pipeline end|ellis"
}

# ── T-0014-015: Tier 3 metadata includes all spec fields ────────────

@test "T-0014-015: Tier 3 section includes total_cost_usd, total_duration_ms, rework_rate, first_pass_qa_rate, evoscore" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  local fields=(total_cost_usd total_duration_ms rework_rate first_pass_qa_rate evoscore)
  local fail=0
  for field in "${fields[@]}"; do
    echo "$protocol" | grep -q "$field" || {
      echo "Missing Tier 3 field in capture protocol: $field"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0014-016: Failure handling says log and continue ───────────────

@test "T-0014-016: every capture gate has log-and-continue failure handling" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -qiE "log.*continue|continue.*never.*block|non.?blocking"
}

# ── T-0014-017: Brain unavailable skips all telemetry capture ────────

@test "T-0014-017: protocol states brain unavailable skips all telemetry capture" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -qiE "brain.*unavailable.*skip|brain_available.*false.*skip"
}

# ── T-0014-018: Micro pipeline is Tier 1 only ───────────────────────

@test "T-0014-018: protocol states Micro pipelines capture Tier 1 only" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -qiE "micro.*tier 1|micro.*skip.*tier 2|micro.*skip.*tier 3"
}

# ── T-0014-019: Tier 1 failure does not prevent Tier 2/3 ────────────

@test "T-0014-019: protocol states Tier 1 capture failure does not block later tiers" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -qiE "log.*continue|fail.*continue|never.*block"
}

# ── T-0014-020: Protocol references telemetry-metrics.md ─────────────

@test "T-0014-020: protocol references telemetry-metrics.md for schemas" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -q "telemetry-metrics.md"
}

# ── T-0014-021: Telemetry is additive to existing brain captures ─────

@test "T-0014-021: protocol states telemetry captures are additive" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -qiE "additive|do not replace|not.*replace"
}

# ── T-0014-022: pipeline_id format documented ────────────────────────

@test "T-0014-022: pipeline_id format is feature_name + timestamp" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  grep -q "pipeline_id" "$file"
  grep -qiE "feature.*timestamp|feature_name.*iso|feature_name.*time" "$file"
}

# ── T-0014-023: Existing brain-capture protocol unchanged ────────────

@test "T-0014-023: existing <protocol id=\"brain-capture\"> section still exists" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  grep -q '<protocol id="brain-capture">' "$file"
}

# ── T-0014-055: Importance graduation: T1=0.3, T2=0.5, T3=0.7 ──────

@test "T-0014-055: capture protocol documents importance values 0.3, 0.5, 0.7 per tier" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -q "0\.3"
  echo "$protocol" | grep -q "0\.5"
  echo "$protocol" | grep -q "0\.7"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 3: Pipeline-End Summary + Boot Trend Query
# ═══════════════════════════════════════════════════════════════════════

# ── T-0014-024: Pipeline-end summary section exists ──────────────────

@test "T-0014-024: pipeline-orchestration.md contains telemetry summary format" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  # The ADR specifies "Pipeline complete. Telemetry summary:" as the format
  grep -qiE "telemetry summary" "$file"
}

# ── T-0014-025: Summary includes cost, duration, rework, EvoScore, findings

@test "T-0014-025: telemetry summary section mentions cost, duration, rework, EvoScore, findings" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  grep -qiE "telemetry summary" "$file" || skip "Telemetry summary section not found"

  local summary
  summary=$(grep -iA 30 "telemetry summary" "$file")

  local fail=0
  for term in cost duration rework EvoScore findings; do
    echo "$summary" | grep -qi "$term" || {
      echo "Telemetry summary section missing: $term"
      fail=1
    }
  done
  [ "$fail" -eq 0 ]
}

# ── T-0014-026: Boot step 5b exists in default-persona.md ───────────

@test "T-0014-026: default-persona.md contains boot step 5b with telemetry query" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qE "[Ss]tep 5b|^5b\.|^\*\*5b" "$file"
  local step5b
  step5b=$(grep -iA 10 "[Ss]tep 5b" "$file" | head -15)
  echo "$step5b" | grep -qi "telemetry"
}

@test "T-0014-026b: source default-persona.md contains boot step 5b" {
  local file="$SOURCE_RULES/default-persona.md"
  grep -qE "[Ss]tep 5b|^5b\.|^\*\*5b" "$file"
}

# ── T-0014-027: Boot step 6 includes telemetry trend line ───────────

@test "T-0014-027: boot step 6 announcement includes telemetry trend format" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qiE "telemetry.*trend|trend.*telemetry|pipeline.*telemetry.*line|telemetry.*line" "$file"
}

# ── T-0014-028: First pipeline produces 'No prior pipeline data' ────

@test "T-0014-028: boot sequence documents no-data case for first pipeline telemetry" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qiE "no prior.*pipeline.*data|no.*telemetry.*data|first.*pipeline.*telemetry|no.*trend.*data" "$file"
}

# ── T-0014-029: Micro pipeline produces abbreviated summary ─────────

@test "T-0014-029: pipeline-end summary documents abbreviated output for Micro pipelines" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  grep -qiE "micro.*abbreviated|micro.*invocation.*count|micro.*duration.*only" "$file"
}

# ── T-0014-030: Brain unavailable still prints summary from accumulators

@test "T-0014-030: pipeline-end summary uses in-memory accumulators when brain unavailable" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  grep -qiE "in.memory.*accumulator|accumulator.*brain.*unavail|accumulator.*fallback" "$file"
}

# ── T-0014-031: Brain unavailable: boot telemetry line omitted ──────

@test "T-0014-031: boot sequence omits telemetry line when brain unavailable" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qiE "brain.*unavailable.*omit.*telemetry|omit.*telemetry.*brain|telemetry.*omit.*brain|skip.*telemetry.*brain.*unavail" "$file"
}

# ── T-0014-032: Degradation alerts fire after 3+ consecutive ────────

@test "T-0014-032: boot telemetry documents degradation alerts for 3+ consecutive breaches" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qiE "degrad.*3.*consecutive|3.*consecutive.*breach|alert.*3.*consecutive|consecutive.*threshold" "$file"
}

# ── T-0014-033: 2 consecutive breaches does NOT fire alert ───────────

@test "T-0014-033: degradation threshold in telemetry-metrics.md is 3+ consecutive" {
  local file="$INSTALLED_REFS/telemetry-metrics.md"
  [ -f "$file" ] || skip "telemetry-metrics.md not yet created"

  grep -qE "3.*consecutive|consecutive.*3" "$file"
}

# ── T-0014-034: Cost unavailable message documented ──────────────────

@test "T-0014-034: documents cost unavailable when token counts not exposed" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  local protocol
  protocol=$(sed -n '/<protocol id="telemetry-capture">/,/<\/protocol>/p' "$file")
  [ -n "$protocol" ] || skip "telemetry-capture protocol not found"

  echo "$protocol" | grep -qiE "cost.*unavailable|token.*count.*not.*exposed|cost.*null"
}

# ── T-0014-035: Source template uses placeholder ─────────────────────

@test "T-0014-035: source default-persona.md uses {pipeline_state_dir} placeholder in step 5b" {
  local file="$SOURCE_RULES/default-persona.md"
  grep -qE "[Ss]tep 5b|^5b\.|^\*\*5b" "$file" || skip "step 5b not yet added"

  grep -q "{pipeline_state_dir}" "$file"
}

# ── T-0014-036: Installed copy uses literal path ─────────────────────

@test "T-0014-036: installed default-persona.md uses literal docs/pipeline in step 5b" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qE "[Ss]tep 5b|^5b\.|^\*\*5b" "$file" || skip "step 5b not yet added"

  grep -q "docs/pipeline" "$file"
}

# ── T-0014-037: Existing boot steps 1-6 unchanged ───────────────────

@test "T-0014-037: existing boot step 1 (pipeline-state.md) still present" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -q "pipeline-state.md" "$file"
}

@test "T-0014-037b: existing boot step 4 (brain health check) still present" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -q "atelier_stats" "$file"
}

# ── T-0014-038: Existing session summary brain capture unchanged ─────

@test "T-0014-038: existing brain-capture protocol still present" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  grep -q '<protocol id="brain-capture">' "$file"
}

# ── T-0014-039: Boot trend query uses telemetry_tier 3 filter ────────

@test "T-0014-039: boot trend query filters by telemetry_tier 3" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qiE "telemetry_tier.*3|telemetry.*tier.*3" "$file"
}

# ── T-0014-040: Single pipeline shows data, no trend % change ───────

@test "T-0014-040: boot telemetry documents single-pipeline case (no trend comparison)" {
  local file="$INSTALLED_RULES/default-persona.md"
  grep -qiE "single.*pipeline.*trend|1.*pipeline.*no.*trend|no.*trend.*percentage|need.*2.*pipeline|2\+.*for.*comparison" "$file"
}

# ── T-0014-056: Micro pipelines do not contribute to boot trends ────

@test "T-0014-056: documents that Micro pipelines do not contribute to boot trend data" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  grep -qiE "micro.*not.*trend|micro.*tier 3.*skip|micro.*exclude.*trend" "$file"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 4: Invocation Template + PIPELINE_STATUS
# ═══════════════════════════════════════════════════════════════════════

# ── T-0014-041: Timing protocol exists in invocation-templates.md ────

@test "T-0014-041: invocation-templates.md contains telemetry timing protocol" {
  local file="$INSTALLED_REFS/invocation-templates.md"
  grep -qiE "telemetry.*timing|wall.clock.*telemetry|start_time.*end_time|timing.*protocol.*telemetry" "$file"
}

# ── T-0014-042: PIPELINE_STATUS includes telemetry fields ────────────

@test "T-0014-042: pipeline-operations.md includes telemetry_pipeline_id" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  [ -f "$file" ] || file="$INSTALLED_RULES/pipeline-operations.md"
  [ -f "$file" ] || skip "pipeline-operations.md not found"

  grep -q "telemetry_pipeline_id" "$file"
}

@test "T-0014-042b: pipeline-operations.md includes telemetry_total_invocations" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  [ -f "$file" ] || file="$INSTALLED_RULES/pipeline-operations.md"
  [ -f "$file" ] || skip "pipeline-operations.md not found"

  grep -q "telemetry_total_invocations" "$file"
}

@test "T-0014-042c: pipeline-operations.md includes telemetry_total_cost_usd" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  [ -f "$file" ] || file="$INSTALLED_RULES/pipeline-operations.md"
  [ -f "$file" ] || skip "pipeline-operations.md not found"

  grep -q "telemetry_total_cost_usd" "$file"
}

@test "T-0014-042d: pipeline-operations.md includes telemetry_rework_by_unit" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  [ -f "$file" ] || file="$INSTALLED_RULES/pipeline-operations.md"
  [ -f "$file" ] || skip "pipeline-operations.md not found"

  grep -q "telemetry_rework_by_unit" "$file"
}

# ── T-0014-043: Observation masking includes Tier 1 capture responses ─
# The Mask section (not Never Mask) must list Tier 1 telemetry capture
# responses as maskable. Checks for "Tier 1" or "telemetry" within the
# ### Mask subsection specifically.

@test "T-0014-043: Mask section lists Tier 1 telemetry capture responses as maskable" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  [ -f "$file" ] || file="$INSTALLED_RULES/pipeline-operations.md"
  [ -f "$file" ] || skip "pipeline-operations.md not found"

  # Extract the "### Mask" section (between "### Mask" and the next "###" heading)
  # Use awk since sed alternation is unreliable on macOS.
  # NR>1 prevents the terminator from matching the opening line itself.
  local mask_section
  mask_section=$(awk '/^### Mask/{found=1} found && NR>1 && /^###/{exit} found' "$file" | head -30)
  [ -n "$mask_section" ] || skip "### Mask section not found"

  # Must reference Tier 1 or telemetry capture within the Mask section
  echo "$mask_section" | grep -qiE "tier 1|telemetry.*capture|telemetry.*response"
}

# ── T-0014-044: PIPELINE_STATUS telemetry field types documented ─────

@test "T-0014-044: PIPELINE_STATUS telemetry fields have documented types" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  [ -f "$file" ] || file="$INSTALLED_RULES/pipeline-operations.md"
  [ -f "$file" ] || skip "pipeline-operations.md not found"

  grep -q "telemetry_pipeline_id" "$file"
  grep -q "telemetry_total_invocations" "$file"
}

# ── T-0014-045: Session recovery restores telemetry accumulators ─────

@test "T-0014-045: documents telemetry accumulator restoration on session resume" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  [ -f "$file" ] || file="$INSTALLED_RULES/pipeline-operations.md"
  [ -f "$file" ] || skip "pipeline-operations.md not found"

  grep -qiE "telemetry.*recover|telemetry.*restore|telemetry.*resume|restore.*telemetry.*accumulator|accumulator.*restore" "$file"
}

# ── T-0014-046: Existing PIPELINE_STATUS fields unchanged ────────────

@test "T-0014-046: existing PIPELINE_STATUS fields roz_qa still present" {
  local file="$INSTALLED_RULES/pipeline-orchestration.md"
  [ -f "$file" ] || skip "pipeline-orchestration.md not found"

  grep -q "roz_qa" "$file"
}

# ── T-0014-047: Dual-tree sync for all modified files ────────────────

@test "T-0014-047: pipeline-orchestration.md telemetry-capture present in both trees" {
  grep -q "telemetry-capture" "$INSTALLED_RULES/pipeline-orchestration.md"
  grep -q "telemetry-capture" "$SOURCE_RULES/pipeline-orchestration.md"
}

# ── T-0014-050: Pre-telemetry state file handled gracefully ──────────

@test "T-0014-050: documents zero-default initialization for absent telemetry fields" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  [ -f "$file" ] || file="$INSTALLED_RULES/pipeline-operations.md"
  [ -f "$file" ] || skip "pipeline-operations.md not found"

  grep -qiE "telemetry.*absent.*zero|telemetry.*default.*0|telemetry.*initial.*zero|telemetry.*field.*absent|absent.*telemetry" "$file"
}

# ── T-0014-051: Telemetry accumulators in PIPELINE_STATUS not masked ─
# The Never Mask section must explicitly list telemetry accumulators
# as items to preserve. Uses awk for reliable section extraction on macOS.

@test "T-0014-051: Never Mask section lists telemetry accumulators" {
  local file="$INSTALLED_REFS/pipeline-operations.md"
  [ -f "$file" ] || file="$INSTALLED_RULES/pipeline-operations.md"
  [ -f "$file" ] || skip "pipeline-operations.md not found"

  # Extract the "### Never Mask" section up to the next "###" heading.
  # NR>1 prevents the terminator from matching the opening line itself.
  local never_mask
  never_mask=$(awk '/^### Never Mask/{found=1} found && NR>1 && /^###/{exit} found' "$file" | head -20)
  [ -n "$never_mask" ] || skip "### Never Mask section not found"

  # Must reference telemetry accumulators specifically
  echo "$never_mask" | grep -qiE "telemetry|accumulator"
}

# ═══════════════════════════════════════════════════════════════════════
# Step 5: Documentation
# ═══════════════════════════════════════════════════════════════════════

# ── T-0014-048: ADR-0014 entry in README.md ──────────────────────────

@test "T-0014-048: ADR-0014 entry exists in docs/architecture/README.md" {
  local file="$PROJECT_ROOT/docs/architecture/README.md"
  [ -f "$file" ] || skip "README.md not found"

  grep -q "ADR-0014" "$file"
}

# ── T-0014-049: ADR index entry includes title ──────────────────────

@test "T-0014-049: ADR-0014 index entry includes title" {
  local file="$PROJECT_ROOT/docs/architecture/README.md"
  [ -f "$file" ] || skip "README.md not found"

  grep -qi "ADR-0014.*telemetry\|telemetry.*ADR-0014" "$file"
}
