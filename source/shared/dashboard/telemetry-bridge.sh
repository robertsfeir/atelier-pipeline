#!/usr/bin/env bash
# telemetry-bridge.sh -- Atelier Pipeline dashboard bridge
#
# Reads brain telemetry via the brain REST API (if configured and reachable),
# falls back to parsing {pipeline_state_dir}/pipeline-state.md, and writes
# PIPELINE_PLAN.md in PlanVisualizer's expected format.
#
# Usage:
#   ./telemetry-bridge.sh [--brain-url URL] [--pipeline-state PATH]
#                          [--output PATH] [--skip-generate]
#
# Exits 0 in all code paths (non-blocking).

set -uo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
BRAIN_URL=""
PIPELINE_STATE_PATH="{pipeline_state_dir}/pipeline-state.md"
OUTPUT_PATH="./PIPELINE_PLAN.md"
SKIP_GENERATE=false
BRAIN_TIMEOUT=5  # seconds
ATELIER_TMPDIR=""     # initialized in main(); cleaned up by EXIT trap
BRAIN_FETCH_RESULT="" # set by fetch_brain_telemetry(): "ok" or ""

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --brain-url)
      [ $# -ge 2 ] || { _log "Missing value for $1"; shift; continue; }
      BRAIN_URL="$2"
      shift 2
      ;;
    --pipeline-state)
      [ $# -ge 2 ] || { _log "Missing value for $1"; shift; continue; }
      PIPELINE_STATE_PATH="$2"
      shift 2
      ;;
    --output)
      [ $# -ge 2 ] || { _log "Missing value for $1"; shift; continue; }
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --skip-generate)
      SKIP_GENERATE=true
      shift
      ;;
    *)
      shift
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_log() {
  echo "[telemetry-bridge] $*" >&2
}

# Write the final PIPELINE_PLAN.md content atomically.
# Uses a temp file + move to avoid partial writes on permission errors.
write_output() {
  local content="$1"
  local tmp_file
  tmp_file=$(mktemp) || { _log "cannot write PIPELINE_PLAN.md -- mktemp failed"; return 0; }
  printf '%s' "$content" > "$tmp_file" 2>/dev/null || {
    _log "cannot write to temp file -- PIPELINE_PLAN.md not updated"
    rm -f "$tmp_file"
    return 0
  }
  mv "$tmp_file" "$OUTPUT_PATH" 2>/dev/null || {
    _log "cannot write PIPELINE_PLAN.md -- permission denied or path not writable"
    rm -f "$tmp_file"
    return 0
  }
}

# ---------------------------------------------------------------------------
# Brain URL resolution
# ---------------------------------------------------------------------------

resolve_brain_url() {
  # Returns the brain base URL via stdout -- callers capture with $()
  # The value is never printed to user-visible output (no credentials exposed)

  # If provided on CLI, use it directly
  if [[ -n "$BRAIN_URL" ]]; then
    printf '%s' "$BRAIN_URL"
    return
  fi

  # Derive URL from PORT env var (matching brain/server.mjs: process.env.PORT || 8788)
  printf '%s' "http://localhost:${PORT:-8788}"
}

# ---------------------------------------------------------------------------
# Brain telemetry fetch (T3 summaries + T1 agent detail)
# ---------------------------------------------------------------------------

fetch_brain_telemetry() {
  # Called directly (not in a subshell) so ATELIER_TMPDIR propagates to callers.
  # Returns via the global BRAIN_FETCH_RESULT variable: "ok" or "".
  local base_url="$1"
  BRAIN_FETCH_RESULT=""

  # Health check first
  local health_response
  health_response=$(curl -s \
    --connect-timeout "$BRAIN_TIMEOUT" \
    --max-time "$BRAIN_TIMEOUT" \
    "${base_url}/api/health" 2>/dev/null) || {
    _log "brain unavailable -- falling back to pipeline-state.md"
    return
  }

  local brain_enabled
  brain_enabled=$(echo "$health_response" | jq -r '.brain_enabled // false' 2>/dev/null) || {
    _log "malformed brain health response -- falling back to pipeline-state.md"
    return
  }

  if [[ "$brain_enabled" != "true" ]]; then
    _log "brain disabled -- falling back to pipeline-state.md"
    return
  fi

  # Fetch T3 telemetry summaries (pipeline-level)
  # Use -s (silent) without -f so we can inspect the HTTP status code ourselves.
  # Capture HTTP code via -w "%{http_code}" directly into a variable; body goes
  # to a temp file. 2>/dev/null suppresses curl progress/error noise from stderr.
  local t3_file="${ATELIER_TMPDIR}/t3.json"
  local http_code
  http_code=$(curl -s \
    --connect-timeout "$BRAIN_TIMEOUT" \
    --max-time "$((BRAIN_TIMEOUT * 2))" \
    -w "%{http_code}" \
    -o "$t3_file" \
    "${base_url}/api/telemetry/summary" 2>/dev/null) || {
    _log "brain HTTP API request failed -- falling back to pipeline-state.md"
    return
  }

  if [[ "$http_code" != "200" ]]; then
    _log "brain API returned status $http_code -- falling back to pipeline-state.md"
    return
  fi

  # Validate JSON
  if ! jq empty "$t3_file" 2>/dev/null; then
    _log "malformed brain API response (JSON parse error) -- falling back to pipeline-state.md"
    return
  fi

  # Fetch T1 agent invocation metrics
  local t1_file="${ATELIER_TMPDIR}/t1.json"
  local t1_http_code
  t1_http_code=$(curl -s \
    --connect-timeout "$BRAIN_TIMEOUT" \
    --max-time "$((BRAIN_TIMEOUT * 2))" \
    -w "%{http_code}" \
    -o "$t1_file" \
    "${base_url}/api/telemetry/agents" 2>/dev/null) || true

  if [[ "$t1_http_code" != "200" ]] || ! jq empty "$t1_file" 2>/dev/null; then
    _log "T1 agent metrics unavailable -- using T3 only"
    echo '[]' > "$t1_file"
  fi

  BRAIN_FETCH_RESULT="ok"
}

# ---------------------------------------------------------------------------
# Build PIPELINE_PLAN.md from brain telemetry (T3 data)
# ---------------------------------------------------------------------------

build_from_brain() {
  local t3_file="${ATELIER_TMPDIR}/t3.json"
  local t1_file="${ATELIER_TMPDIR}/t1.json"

  local row_count
  row_count=$(jq 'length' "$t3_file" 2>/dev/null) || row_count=0

  if [[ "$row_count" -eq 0 ]]; then
    _log "no brain telemetry data -- generating placeholder"
    generate_placeholder
    return
  fi

  local plan="# Pipeline Plan\n\n"
  plan+="<!-- Generated by telemetry-bridge.sh from Atelier Brain telemetry -->\n"
  plan+="<!-- Full regeneration: $(date -u +%Y-%m-%dT%H:%M:%SZ) -->\n\n"

  # Iterate T3 rows -- each row is one pipeline run (one EPIC)
  local epic_num=1
  while IFS= read -r row; do
    local pipeline_id sizing total_cost rework_rate first_pass_qa_rate
    pipeline_id=$(echo "$row" | jq -r '.metadata.pipeline_id // "pipeline-unknown"' 2>/dev/null) || pipeline_id="pipeline-unknown"
    sizing=$(echo "$row" | jq -r '.metadata.sizing // "unknown"' 2>/dev/null) || sizing="unknown"
    total_cost=$(echo "$row" | jq -r '.metadata.total_cost_usd // "0"' 2>/dev/null) || total_cost="0"
    rework_rate=$(echo "$row" | jq -r '.metadata.rework_rate // "0"' 2>/dev/null) || rework_rate="0"
    first_pass_qa_rate=$(echo "$row" | jq -r '.metadata.first_pass_qa_rate // "0"' 2>/dev/null) || first_pass_qa_rate="0"

    # Derive a human-readable title from pipeline_id (strip timestamp suffix)
    local epic_title
    epic_title=$(echo "$pipeline_id" | sed 's/_[0-9T:Z-]*$//' | tr '_' ' ')

    plan+="## EPIC-${epic_num}: ${epic_title} (${sizing})\n"
    plan+="Status: Done\n"
    plan+="\n"
    plan+="- **Cost:** \$${total_cost}\n"
    plan+="- **Rework Rate:** ${rework_rate}\n"
    plan+="- **First-pass QA Rate:** ${first_pass_qa_rate}\n"
    plan+="\n"

    # Add agent Stories from T1 data
    local story_num=1
    local agents_data
    agents_data=$(cat "$t1_file" 2>/dev/null) || agents_data="[]"
    while IFS= read -r agent_row; do
      local agent_name invocations avg_duration total_agent_cost
      agent_name=$(echo "$agent_row" | jq -r '.agent // "unknown"' 2>/dev/null) || agent_name="unknown"
      invocations=$(echo "$agent_row" | jq -r '.invocations // 0' 2>/dev/null) || invocations=0
      avg_duration=$(echo "$agent_row" | jq -r '.avg_duration_ms // 0' 2>/dev/null) || avg_duration=0
      total_agent_cost=$(echo "$agent_row" | jq -r '.total_cost // "0"' 2>/dev/null) || total_agent_cost="0"

      local work_unit_id="${pipeline_id}/${agent_name}"

      plan+="### US-${epic_num}-${story_num}: ${agent_name} invocations\n"
      plan+="- **Status:** Done\n"
      plan+="- **Priority:** P2\n"
      plan+="- **Estimate:** ${invocations}\n"
      plan+="- **Agent:** ${agent_name}\n"
      plan+="- **Work Unit:** ${work_unit_id}\n"
      plan+="\n"
      plan+="#### Tasks:\n"
      plan+="- [ ] ${agent_name} build -- ${avg_duration}ms avg\n"
      plan+="\n"

      story_num=$((story_num + 1))
    done < <(echo "$agents_data" | jq -c '.[]' 2>/dev/null)

    epic_num=$((epic_num + 1))
  done < <(jq -c '.[]' "$t3_file" 2>/dev/null)

  printf '%b' "$plan"
}

# ---------------------------------------------------------------------------
# Build PIPELINE_PLAN.md from pipeline-state.md (fallback)
# ---------------------------------------------------------------------------

build_from_pipeline_state() {
  if [[ ! -f "$PIPELINE_STATE_PATH" ]]; then
    _log "pipeline-state.md not found at $PIPELINE_STATE_PATH -- generating placeholder"
    generate_placeholder
    return
  fi

  # Parse the pipeline state file for feature name, status, and progress table
  local feature_name
  feature_name=$(grep -m1 '^\*\*Feature:\*\*' "$PIPELINE_STATE_PATH" 2>/dev/null | sed 's/\*\*Feature:\*\* //' | tr -d '\r') || feature_name="Unknown Feature"

  local started_date
  started_date=$(grep -m1 '^\*\*Started:\*\*' "$PIPELINE_STATE_PATH" 2>/dev/null | sed 's/\*\*Started:\*\* //' | tr -d '\r') || started_date="$(date +%Y-%m-%d)"

  local sizing
  sizing=$(grep -m1 '^\*\*Sizing:\*\*' "$PIPELINE_STATE_PATH" 2>/dev/null | sed 's/\*\*Sizing:\*\* //' | tr -d '\r') || sizing="unknown"

  # Check if there is any meaningful data
  if [[ -z "$feature_name" ]] || [[ "$feature_name" == "Unknown Feature" ]]; then
    local line_count
    line_count=$(wc -l < "$PIPELINE_STATE_PATH" 2>/dev/null) || line_count=0
    if [[ "$line_count" -lt 3 ]]; then
      _log "pipeline-state.md is empty -- generating placeholder"
      generate_placeholder
      return
    fi
  fi

  local plan="# Pipeline Plan\n\n"
  plan+="<!-- Generated by telemetry-bridge.sh from pipeline-state.md (brain fallback) -->\n"
  plan+="<!-- Full regeneration: $(date -u +%Y-%m-%dT%H:%M:%SZ) -->\n\n"

  local epic_title="${feature_name}"
  local pipeline_id="${feature_name// /-}_${started_date}"

  plan+="## EPIC-1: ${epic_title} (${sizing})\n"
  plan+="Status: In Progress\n"
  plan+="\n"

  # Parse progress table rows: | # | Unit | Agent | Status | Notes |
  local story_num=1
  while IFS='|' read -r _ unit_num unit_name agent_name status notes _; do
    # Skip header and separator rows
    unit_name=$(echo "$unit_name" | xargs 2>/dev/null) || continue
    agent_name=$(echo "$agent_name" | xargs 2>/dev/null) || continue
    status=$(echo "$status" | xargs 2>/dev/null) || continue

    [[ -z "$unit_name" ]] && continue
    [[ "$unit_name" == "#" ]] && continue
    [[ "$unit_name" =~ ^-+$ ]] && continue

    # Map status to PlanVisualizer status
    local pv_status="To Do"
    case "${status,,}" in
      done) pv_status="Done" ;;
      "in progress") pv_status="In Progress" ;;
      blocked) pv_status="Blocked" ;;
      *) pv_status="To Do" ;;
    esac

    local work_unit_id="${pipeline_id}/${unit_name// /-}"

    plan+="### US-1-${story_num}: ${unit_name}\n"
    plan+="- **Status:** ${pv_status}\n"
    plan+="- **Priority:** P2\n"
    plan+="- **Estimate:** 1\n"
    plan+="- **Agent:** ${agent_name}\n"
    plan+="- **Work Unit:** ${work_unit_id}\n"
    plan+="\n"
    plan+="#### Tasks:\n"
    plan+="- [ ] ${agent_name} ${unit_name}\n"
    plan+="\n"

    story_num=$((story_num + 1))
  done < <(sed -n '/^## Progress/,/^## /p' "$PIPELINE_STATE_PATH" 2>/dev/null | grep '^|' | grep -v '^| #' | grep -v '^|[-|]')

  if [[ $story_num -eq 1 ]]; then
    plan+="### US-0-0: No progress data\n"
    plan+="- **Status:** To Do\n"
    plan+="- **Priority:** P3\n"
    plan+="- **Estimate:** 0\n"
    plan+="\n"
  fi

  printf '%b' "$plan"
}

# ---------------------------------------------------------------------------
# Minimal placeholder when no data exists
# ---------------------------------------------------------------------------

generate_placeholder() {
  printf '# Pipeline Plan\n\n<!-- Generated by telemetry-bridge.sh -->\n<!-- Full regeneration: %s -->\n\n## EPIC-1: No pipeline data yet\nStatus: Planned\n\n### US-0-0: No pipeline data yet\n- **Status:** Planned\n- **Priority:** P3\n- **Estimate:** 0\n\n> No pipeline data available. Run a pipeline to populate this dashboard.\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

# ---------------------------------------------------------------------------
# HTML regeneration
# ---------------------------------------------------------------------------

run_generate() {
  if [[ "$SKIP_GENERATE" == "true" ]]; then
    return
  fi

  if ! command -v node > /dev/null 2>&1; then
    _log "node not found -- PIPELINE_PLAN.md written but HTML not regenerated"
    return
  fi

  if [[ ! -f ".plan-visualizer/tools/generate-plan.js" ]]; then
    # Also try relative path from script location
    if [[ ! -f "tools/generate-plan.js" ]]; then
      _log "generate-plan.js not found -- PIPELINE_PLAN.md written but HTML not regenerated"
      return
    fi
  fi

  local generate_script=".plan-visualizer/tools/generate-plan.js"
  [[ ! -f "$generate_script" ]] && generate_script="tools/generate-plan.js"

  node "$generate_script" 2>/dev/null || {
    _log "generate-plan.js failed -- PIPELINE_PLAN.md is up to date but HTML not regenerated"
  }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
  local plan_content=""

  # Create temp directory for brain fetch temp files; clean up on any exit.
  # Initialized here (parent shell) so ATELIER_TMPDIR is visible to
  # fetch_brain_telemetry and build_from_brain without subshell isolation.
  ATELIER_TMPDIR=$(mktemp -d) || {
    _log "mktemp -d failed -- continuing without temp directory"
    ATELIER_TMPDIR="/tmp/atelier_bridge_$$"
    mkdir -p "$ATELIER_TMPDIR" 2>/dev/null || true
  }
  trap 'rm -rf "$ATELIER_TMPDIR"' EXIT

  # Resolve brain URL from config or CLI
  local brain_url
  brain_url=$(resolve_brain_url)

  BRAIN_FETCH_RESULT=""
  if [[ -n "$brain_url" ]]; then
    fetch_brain_telemetry "$brain_url"
  else
    _log "no brain configured -- falling back to pipeline-state.md"
  fi

  if [[ "$BRAIN_FETCH_RESULT" == "ok" ]]; then
    plan_content=$(build_from_brain)
  else
    plan_content=$(build_from_pipeline_state)
  fi

  if [[ -z "$plan_content" ]]; then
    plan_content=$(generate_placeholder)
  fi

  write_output "$plan_content"

  run_generate

  _log "PIPELINE_PLAN.md written to $OUTPUT_PATH"
}

# Trap all errors so the script always exits 0
trap '_log "unexpected error -- exiting cleanly"; exit 0' ERR

main "$@"
exit 0
