<!-- Part of atelier-pipeline. Boot sequence for Eva. Read once at session start, treat as consumed after. -->

<protocol id="boot-sequence">

## Session Boot Sequence (run on every new session)

**Steps 1-3d: Parse session-boot.sh output.** The `session-boot.sh` SessionStart
hook reads pipeline-state.md, context-brief.md, error-patterns.md,
pipeline-config.json, counts custom agents, and checks the CLAUDE_AGENT_TEAMS
env var. It outputs structured JSON with: `pipeline_active`, `phase`, `feature`,
`stale_context`, `warn_agents[]`, `branching_strategy`, `agent_teams_enabled`,
`agent_teams_env`, `custom_agent_count`, `ci_watch_enabled`, `darwin_enabled`,
`dashboard_mode`, `project_name`, `sentinel_enabled`, `deps_agent_enabled`,
`token_budget_warning_threshold` (number or null; absent key treated as null --
no budget gate for Medium, Large-only estimate with hard pause),
`stop_reason` (present when a previous terminal pipeline has a recorded stop reason,
or inferred as `"session_crashed"` when a stale pipeline is detected -- see
session_crashed inference rule below).
Eva parses this JSON to populate session state. Derive `agent_teams_available`
from `agent_teams_enabled && agent_teams_env`.

**`session_crashed` inference rule:** When session-boot detects a stale
pipeline (`stale_context: true` OR `pipeline_active: true` with a non-idle
`phase`), AND the PIPELINE_STATUS JSON in pipeline-state.md has no `stop_reason`
key (or its value is `null`), session-boot includes `"stop_reason":
"session_crashed"` in its JSON output. Eva uses this inferred stop reason when
announcing the stale pipeline to the user and when capturing T3 telemetry
retroactively (if applicable). The `session_crashed` value is inferred -- it
is never written to pipeline-state.md by Eva directly (Eva cannot write during
a crash). Eva may write `session_crashed` to pipeline-state.md after boot only
when she is explicitly recovering a stale pipeline and choosing to record the
inferred stop reason for posterity.

4. **Brain health check** -- call `atelier_stats`. Two gates:
   - Gate 1: Is the tool available? (If not → brain not configured, skip)
   - Gate 2: Does it return `brain_enabled: true`? (If not → brain disabled by user)
   - Both pass → set `brain_available: true` in pipeline state
   - Either fails → set `brain_available: false`, log reason, proceed baseline

4b. **Telemetry hydration** (if `brain_available: true`) -- call `atelier_hydrate` with the
    project sessions path. Derive the path from `CLAUDE_PROJECT_DIR` using the same
    convention session-hydrate.sh used:
    `~/.claude/projects/-{CLAUDE_PROJECT_DIR with / replaced by -}` (leading `/` becomes `-`).
    Example: `CLAUDE_PROJECT_DIR=/Users/alice/projects/myapp` →
    `~/.claude/projects/-Users-alice-projects-myapp`.
    Non-blocking: `atelier_hydrate` returns `{status: "queued"}` immediately.
    Do not await the result. Move directly to step 5 without waiting for hydration to complete.
    When `brain_available: false`: skip this step entirely.

5. **Brain context retrieval** (if `brain_available: true`) -- call `agent_search` with query
   derived from current feature area. Inject results alongside context-brief.md.
5b. **Telemetry trend query** (OPTIONAL -- skip unless a pipeline is about to
    start or the user explicitly asks about pipeline trends) -- if `brain_available: true`,
    call `agent_search` with query `"telemetry pipeline summary"`,
    `filter: { telemetry_tier: 3 }`, limit 10.
    Filter results client-side: keep only records where `source_phase == 'telemetry'`.

    If 2+ results found:
    - Compute averages: avg cost, avg duration, avg rework rate, avg first-pass QA rate
    - Compute trends: % change in cost over last 5, rework rate direction
    - Check degradation alert thresholds (from `telemetry-metrics.md`):
      - Cost trending up >25% over last 5 pipelines
      - Rework rate >2.0 for 3 consecutive pipelines
      - First-pass QA rate <60% for 3 consecutive pipelines
      - Agent failures >2 for same agent over last 10 pipelines
      - EvoScore <0.9 for 3 consecutive pipelines
    - Degradation alerts fire only when threshold exceeded for 3+ consecutive pipelines
      (consecutive threshold). Two consecutive breaches do NOT fire an alert.
    - Alert format: "Warning: [metric] above/below threshold for [N] consecutive pipelines.
      Last [N]: [values]. [suggestion]."

    If exactly 1 result found:
    - Data exists but no trend percentage change is computable (need 2+ pipelines for comparison).
      Show single-pipeline data without trend comparisons.

    If 0 results found (first pipeline, no prior trend data):
    - Note for step 6 announcement: "Telemetry: No prior pipeline data. Trends will appear after 2+ pipelines."

    When brain unavailable: skip this step entirely. Omit telemetry line from step 6 announcement.

    **Darwin post-edit tracking** (OPTIONAL -- skip unless a pipeline is about to
    start or the user explicitly asks; requires `darwin_enabled: true` and trend data):
    - Query brain: `agent_search` with `thought_type: 'decision'`,
      `source_phase: 'darwin'`, filtered to non-rejected proposals
      (exclude entries where metadata contains `rejected: true`).
    - For each approved Darwin edit with `baseline_value` in metadata:
      find the target metric in subsequent Tier 3 summaries (pipelines after the edit).
      If 3+ subsequent pipelines exist:
      - Compute metric delta: current average vs baseline_value.
      - If improved: note for announcement: "Darwin edit #{id} ({description}):
        {metric} improved {before} -> {after}"
      - If worsened: flag for announcement as potential regression:
        "Warning: Darwin edit #{id} may have caused regression. {metric} dropped
        {before} -> {after}. Consider reverting."
    - If fewer than 3 subsequent pipelines: skip (insufficient data for delta).
    - When `darwin_enabled: false` or brain unavailable: skip this step entirely.

6. **Announce session state to user:**
   - Active pipeline: "Resuming [feature] at [phase]. [N agents complete, M remaining.]"
   - No active pipeline: "No active pipeline. What are we working on?"
   - Stale context detected: "Found stale context-brief from [old feature]. Resetting."
   - Brain status: append "Brain: active ([N] thoughts)" or "Brain: baseline mode"
   - Custom agents: append "Custom agents: N discovered" when discovered agent count > 0 (omit line when zero)
   - Agent Teams: when `agent_teams_enabled: true` in config, append "Agent Teams: active (experimental)" if `agent_teams_available: true`, or "Agent Teams: disabled" if `agent_teams_available: false`. Omit this line entirely when `agent_teams_enabled: false` (user never opted in).
   - CI Watch: when `ci_watch_enabled: true` in config, append "CI Watch: active (max retries: N)" where N is `ci_watch_max_retries` from config. Omit this line entirely when `ci_watch_enabled: false`.
   - Darwin: when `darwin_enabled: true` in config, append "Darwin: active" if
     `brain_available: true`, or "Darwin: disabled (brain required)" if
     `brain_available: false`. Omit this line entirely when `darwin_enabled: false`.
   - Darwin edits: when Darwin post-edit tracking found results, append on
     separate lines: "Darwin edit #{id} ({description}): {metric} {improved/worsened}
     {delta} over {N} pipelines." If any edit worsened metrics, append:
     "Warning: Darwin edit #{id} may have caused regression. Consider reverting."
   - Telemetry trend line (from step 5b): when `brain_available: true` and trend data exists (2+ pipelines),
     append "Telemetry: Last {N} pipelines -- avg ${cost}, {duration} min. Rework: {rate}/unit. First-pass QA: {pct}%."
     followed by any degradation alerts on separate lines.
     When only 1 pipeline of data exists: "Telemetry: 1 prior pipeline -- ${cost}, {duration} min. Trends appear after 2+ pipelines for comparison."
     When no prior trend data (0 results): "Telemetry: No prior pipeline data. Trends will appear after 2+ pipelines."
     When brain unavailable: omit telemetry line entirely.

</protocol>
