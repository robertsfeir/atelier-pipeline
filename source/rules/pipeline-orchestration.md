---
paths:
  - "docs/pipeline/**"
---

# Pipeline Orchestration -- Operational Procedures

Loads automatically when Eva reads `{pipeline_state_dir}/` files. Contains
mandatory gates, brain capture model, investigation discipline, pipeline
flow, agent standards, and verification procedures.

<section id="loading-strategy">

## Loading Strategy

This file uses just-in-time (JIT) loading. Sections marked `[ALWAYS]` are loaded when the file first loads (pipeline activation). Sections marked `[JIT]` are loaded only when their trigger condition is met. Eva reads the section headers to know what exists, then reads the full section content on demand.

| Section | Load | Trigger |
|---------|------|---------|
| Brain Access | ALWAYS | Pipeline activation |
| Observation Masking | ALWAYS | Pipeline activation |
| Mandatory Gates | ALWAYS | Pipeline activation |
| Telemetry Capture | JIT | After first agent returns |
| Darwin Auto-Trigger | JIT | Pipeline end + degradation detected |
| Pattern Staleness | JIT | Pipeline end |
| Dashboard Bridge | JIT | Pipeline end |
| Investigation Discipline | JIT | Debug flow entered |
| State File Descriptions | JIT | First state write |
| Phase Sizing Rules | JIT | Pipeline sizing decision |

</section>

<protocol id="brain-capture">

## Brain Access (when brain is available)

When `brain_available: true`, Eva performs these brain operations at mechanical gates. Agent domain-specific captures are wired via `mcpServers: atelier-brain` frontmatter -- see agent personas (Cal, Colby, Roz, Agatha) for capture gates.

### Hybrid Capture Model

Agents write their own domain-specific captures directly (Cal captures decisions, Colby captures implementation insights, Roz captures QA findings, etc.). Each agent uses their own name as `source_agent` so the brain tracks who learned what. Eva does NOT duplicate agent captures.

Eva captures **cross-cutting concerns only** — things no single agent owns:

**Reads:**
- Pipeline start: calls `agent_search` with query derived from current feature area + scope. Injects results into pipeline state alongside context-brief.md.
- Before each wave: calls `agent_search` once for the wave's feature area. Injects results into all agent invocations within that wave. Does NOT call `agent_search` per individual agent invocation.
- Health check: calls `atelier_stats` at pipeline start to verify brain is live.

**Writes (cross-cutting only, best-effort -- reinforced by prompt hook):**
- User decisions: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'decision'` when the user expresses a preference, correction, or override during conversation.
- Phase transitions: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'decision'` at each pipeline phase transition with outcome summary.
- Cross-agent patterns: when the same issue is found by multiple reviewers (e.g., Roz and Robert both flag the same drift), calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'` noting the convergence.
- Deploy/infra outcomes: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'lesson'` after deploy attempts (pass or fail) and infrastructure changes.
- Creates cross-agent relations via `atelier_relation`: drift finding `triggered_by` review juncture, correction `supersedes` prior reasoning, HALT resolution `triggered_by` AMBIGUOUS finding.
- Captures Poirot's findings post-review via `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'` (Poirot himself never touches brain).
- Pipeline end: calls `agent_capture` with `thought_type: 'decision'` for session summary linking key decisions from the run.
- Wave decisions: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'decision'`, `source_phase: 'build'` after wave grouping with step-to-wave mapping and rationale.
- Model-vs-outcome: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'lesson'`, `source_phase: 'build'` after each Colby unit completes QA, recording: model used, step description, Roz verdict, issue count.

### /devops Capture Gates

When Eva operates in /devops mode, `agent_capture` fires after: every deploy attempt (`lesson`), every infra config change (`decision`), every DB operation (`decision`), every external service config (`decision`). All use `source_agent: 'eva'`, `source_phase: 'devops'`.

When brain is unavailable, Eva skips all brain steps. No pipeline run fails because of the brain.

### Seed Capture (shared agent behavior)

Any agent can capture a seed when an out-of-scope idea surfaces during work.
Seeds are prospective — they capture what *should* happen next, not what happened.
When an agent discovers an idea outside the current pipeline's scope:
- Call `agent_capture` with `thought_type: 'seed'`, `source_agent: '{current_agent}'`,
  `source_phase: '{current_phase}'`, `importance: 0.5`.
- Include in metadata: `trigger_when` (keyword or feature area that should surface
  this seed), `origin_pipeline` (current ADR number), `origin_context` (one-line
  description of what prompted the idea).
- Seeds have NULL TTL (permanent) but can be manually invalidated.

### Seed Surfacing (Eva boot sequence)

During Eva's boot sequence step 5 (Brain context retrieval), after the general
`agent_search`, Eva runs a second search: `agent_search` filtered to
`thought_type: 'seed'` with query matching the current feature area. If seeds
are found, Eva announces to the user: "Brain surfaced [N] seed ideas related
to this area: [list with one-line summaries]. Want to incorporate any into this
pipeline?" The user decides — seeds are suggestions, not requirements.

</protocol>

<protocol id="telemetry-capture">

## Telemetry Capture Protocol (when brain is available)

Eva captures quantitative pipeline metrics at three gates. All captures use:
- `thought_type: 'insight'`
- `source_agent: 'eva'`
- `source_phase: 'telemetry'`
- `metadata.pipeline_id` (set at pipeline start: `{feature_name}_{ISO_timestamp}`)

Eva reads `telemetry-metrics.md` at pipeline start alongside `pipeline-operations.md`
to load metric schemas and cost estimation tables.

Telemetry captures are additive -- they do not replace existing brain captures
(phase transitions, model-vs-outcome, seeds, etc.).

When `brain_available: false`, skip all telemetry capture gates entirely.
In-memory accumulators still run for the pipeline-end summary display.

### Tier 1 Gate (per-invocation) -- After Every Agent Returns

After every Agent tool completion, Eva records metrics in the in-memory
accumulator only. Eva does NOT call `agent_capture` per invocation. Tier 1
data is captured in bulk at wave end as part of the Tier 2 capture.

1. Records wall-clock duration (`end_time - start_time` in ms). Duration is always computable.
2. Extracts available metadata from Agent tool result: `model`, `input_tokens`, `output_tokens`,
   `cache_read_tokens`, `finish_reason`, `tool_count`, `turn_count`.
   - If token counts unavailable: log `0`, note "token counts unavailable from Agent tool" in accumulator.
   - If model unavailable: set `"unknown"`, skip `context_utilization` and `cost_usd` computation.
3. Computes `cost_usd` using the cost table from `telemetry-metrics.md`.
   If model unknown or not in the pricing table: set `cost_usd: null`, log "Cost unavailable -- model not in pricing table".
4. Computes `context_utilization` as `(input_tokens + output_tokens) / context_window_max`
   (model-dependent from `telemetry-metrics.md`). Set `null` when tokens unavailable.
5. Adds to in-memory accumulators: `total_cost`, `total_invocations`, `invocations_by_agent`, `invocations_by_model`,
   and per-invocation records (agent, phase, duration, model, tokens, cost) for bulk capture.

**Micro pipelines:** Tier 1 captures run as normal. Micro pipelines capture Tier 1 only --
skip Tier 2 and Tier 3. Micro runs do not contribute to boot trend data (which queries Tier 3).

### Tier 2 Gate (per-wave, best-effort) -- After Each Wave Passes Roz QA PASS

After each wave passes Roz QA, Eva captures a single Tier 2 record covering
all units in the wave. The capture includes per-unit breakdowns (rework cycles,
first-pass QA, costs) as array fields in metadata.

1. For each unit in the wave:
   a. Counts `rework_cycles`: number of Colby re-invocations after the first
      on the same `work_unit_id`. A unit that passes on its first Colby invocation has `rework_cycles == 0`.
   b. Determines `first_pass_qa` (`rework_cycles == 0`).
   c. Sums `unit_cost_usd` from in-memory Tier 1 accumulator for this `work_unit_id`. Set `null` if any Tier 1 cost was null.
2. Tallies `finding_counts` from Roz, Poirot for the wave.
3. Computes `finding_convergence` (findings flagged independently by both Roz and Poirot).
4. Computes `evoscore_delta` from Roz's wave QA report (test counts before/after the wave).
   Formula: `(tests_after - tests_broken) / tests_before`. When `tests_before == 0`: `evoscore_delta = 1.0`.
5. Calls `agent_capture` (single call for the entire wave):
   - `content`: `"Telemetry T2: wave {wave_id} units={N} rework={total_rework} first_pass={first_pass_count}/{total_units}"`
   - `importance: 0.5`
   - `scope: ["{pipeline_project_name}"]`
   - `metadata`: full Tier 2 schema populated, plus `telemetry_tier: 2`, `pipeline_id`,
     `wave_id`, and `unit_breakdowns` array containing per-unit records
     (work_unit_id, rework_cycles, first_pass_qa, unit_cost_usd).
     Also includes bulk Tier 1 data: `tier1_invocations` array with all
     per-invocation records accumulated during this wave.
6. On failure: log and continue -- `"Telemetry T2 capture failed: {reason}. Continuing."` Never block the pipeline.

**Skipped on Micro pipelines.**

### Tier 3 Gate (per-pipeline, best-effort) -- At Pipeline End After Ellis Final Commit

At pipeline end, after Ellis final commit and before end-of-pipeline checks, Eva:

1. Aggregates from in-memory accumulators + Tier 2 captures.
2. Computes `phase_durations` from Tier 1 timestamps grouped by `pipeline_phase`.
3. Computes `rework_rate`: total `rework_cycles` / total units.
4. Computes `first_pass_qa_rate`: units with `first_pass_qa == true` / total units.
5. Computes aggregate `evoscore` from average of Tier 2 `evoscore_delta` values.
6. Calls `agent_capture`:
   - `content`: `"Telemetry T3: {pipeline_id} cost=${total_cost_usd} rework={rework_rate} evoscore={evoscore}"`
   - `importance: 0.7`
   - `scope: ["{pipeline_project_name}"]`
   - `metadata`: full Tier 3 schema populated, plus `telemetry_tier: 3` and `pipeline_id`
   - Fields: `total_cost_usd`, `total_duration_ms`, `phase_durations`, `total_invocations`,
     `invocations_by_agent`, `invocations_by_model`, `total_tokens`, `rework_rate`,
     `first_pass_qa_rate`, `agent_failures`, `evoscore`, `regression_count`, `sizing`, `project_name`
7. On failure: log and continue -- `"Telemetry T3 capture failed: {reason}. Continuing."` Never block the pipeline.
   Pipeline-end summary still prints from in-memory accumulators.
8. After a successful Tier 3 capture, Eva sets `telemetry_captured: true` in PIPELINE_STATUS.
   This is required -- the enforce-sequencing hook blocks Ellis unless this flag is set.
   Eva must also set it in the accumulator fields alongside `roz_qa`.
   If the T3 capture fails (step 7), Eva does NOT set `telemetry_captured: true` -- the gate
   will block Ellis, prompting Eva to retry or surface the failure to the user.

**Skipped on Micro pipelines.** Micro pipelines exclude from trend data -- Tier 3 skip means
Micro runs do not appear in boot trend queries.

### Pipeline-End Telemetry Summary

After the Tier 3 capture (or after Ellis on Micro pipelines), Eva prints a telemetry summary
to the user. Source data: in-memory accumulators (always available) supplemented by Tier 2
captures for finding details (best-effort).

**Standard (non-Micro) format:**
```
Pipeline complete. Telemetry summary:
  Cost: ${total_cost_usd} ({agent}: ${agent_cost}, ...)
  Duration: {total_duration_min} min ({phase}: {phase_duration_min} min, ...)
  Rework: {rework_rate} cycles/unit ({total_units} units, {first_pass_count} first-pass QA)
  EvoScore: {evoscore} ({tests_before} tests before, {tests_after} after, {tests_broken} broken)
  Findings: Roz {N}, Poirot {N}, Robert {N} (convergence: {N} shared)
```

**Micro format (abbreviated):**
```
Telemetry: {invocation_count} invocations, {total_duration_min} min
```
Micro pipelines print invocation count and duration only -- no rework, EvoScore, or findings.

**Fallback rules:**
- Cost unavailable (token counts not exposed by Agent tool): print "Cost: unavailable (token counts not exposed)"
- Brain unavailable: in-memory accumulator fallback -- summary still prints; finding details may be approximate

### Post-Pipeline Telemetry Reminder

After the pipeline-end summary, Eva appends a one-line reminder:
"Tip: Run /telemetry-hydrate to capture detailed token usage from this session into the brain."

This is advisory only -- the SessionStart hook will hydrate automatically on the next session.
Do not block the pipeline on this reminder.

### Darwin Auto-Trigger (at pipeline end)

After the pipeline-end telemetry summary, if ALL of the following conditions are true:
1. `darwin_enabled: true` in `pipeline-config.json`
2. `brain_available: true`
3. At least one degradation alert fired in the telemetry summary
4. Pipeline sizing is not Micro (Micro pipelines skip Darwin auto-trigger)

Then Eva announces: "Degradation detected. Running Darwin analysis..." and invokes
Darwin using the `darwin-analysis` invocation template.

When `darwin_enabled: false` or absent (absent treated as false): skip this section entirely.

Eva pre-fetches brain context for Darwin:
- `agent_search` with `source_phase: 'telemetry'`, `telemetry_tier: 3`, limit 10
- `agent_search` with `thought_type: 'decision'`, metadata filter for
  `darwin_proposal_id` (prior Darwin proposals and outcomes)
- Error-patterns.md content (read from disk, not brain)

After Darwin returns its report, Eva presents it to the user. The user
approves, rejects (with reason), or modifies each proposal individually.
**Modify** is a reject-then-repropose cycle: Eva captures the rejection with
the user's modification feedback, then re-invokes Darwin for a revised proposal
on the same target. This is a hard pause -- Eva does not auto-advance past
Darwin proposals.

For each approved proposal:
1. Eva captures the approval via `agent_capture`:
   - `thought_type: 'decision'`
   - `source_agent: 'eva'`
   - `source_phase: 'darwin'`
   - `importance: 0.7`
   - `content`: "Darwin edit approved: {one-line description}"
   - `metadata`: `{ darwin_proposal_id: "{pipeline_id}_{proposal_number}",
     target_file: "{path}", target_metric: "{metric_name}",
     escalation_level: {N}, expected_impact: "{description}",
     baseline_value: {current_metric_value} }`
2. Eva routes to Colby with the `darwin-edit-proposal` invocation template.
   One Colby invocation per approved proposal -- each proposal is atomic and
   implemented separately.
3. Roz verifies Colby's edit (mandatory gate 1 applies).
4. Ellis commits the approved edit.

For each rejected proposal:
- Eva captures the rejection via `agent_capture`:
  - `thought_type: 'decision'`
  - `source_agent: 'eva'`
  - `source_phase: 'darwin'`
  - `importance: 0.5`
  - `content`: "Darwin edit rejected: {one-line description}. Reason: {user's reason}"
  - `metadata`: `{ darwin_proposal_id: "{pipeline_id}_{proposal_number}",
    rejected: true, rejection_reason: "{reason}" }`

Darwin auto-trigger does not block pipeline completion. If the user dismisses
all proposals or says "skip Darwin", Eva proceeds to the pattern staleness check.

### Pattern Staleness Check (pipeline end)

After each pipeline completes (and after the Darwin auto-trigger if applicable),
Eva checks all `thought_type: 'pattern'` thoughts whose `metadata.files`
reference files modified in this pipeline. For each pattern:
1. Run `git log --stat --since="<pattern.created_at>" -- <metadata.files>` to measure churn.
2. If >50% of lines in the referenced files changed since the pattern was captured,
   the pattern is stale. Eva invalidates it via `agent_capture` with a new thought
   that `supersedes` the original (using `atelier_relation`), and logs:
   "Pattern [id] invalidated — source files changed significantly since capture."
3. If churn is moderate (20-50%), Eva appends a warning to the pattern's next
   surfacing: "Pattern may be outdated — source files have been modified."

### Dashboard Bridge (post-pipeline, PlanVisualizer only)

After the Pattern Staleness Check (and Darwin auto-trigger if applicable), if
`dashboard_mode` is set to `"plan-visualizer"` in `pipeline-config.json`, Eva runs
the bridge script:

1. Eva runs `{config_dir}/dashboard/telemetry-bridge.sh` via Bash.
2. If the script succeeds: Eva logs "Dashboard updated -- PIPELINE_PLAN.md regenerated."
3. If the script fails: Eva logs "Dashboard update failed: [reason]. Pipeline complete." and continues.

Dashboard bridge failure is never a pipeline blocker.

When `dashboard_mode` is `"claude-code-kanban"` or `"none"`: skip this section entirely.
claude-code-kanban is passive (watches files in real-time) and requires no post-pipeline action.
When `dashboard_mode` is absent from `pipeline-config.json`: skip (treat as `"none"`).

**Eva boot announcement for dashboard:**

Eva reads `dashboard_mode` from `pipeline-config.json` at boot (step 3b) and appends a
conditional line to the session state announcement (step 6):
- `dashboard_mode: "plan-visualizer"` -> append "Dashboard: PlanVisualizer"
- `dashboard_mode: "claude-code-kanban"` -> append "Dashboard: claude-code-kanban"
- `dashboard_mode: "none"` or absent -> omit the dashboard line entirely

</protocol>

<gate id="mandatory-gates">

## Mandatory Gates -- Eva NEVER Skips These

Eva manages phase transitions. Some phases are skippable based on sizing
(see agent-system.md). These twelve gates are NEVER skippable. No exceptions.
No "it's just a small fix." No "I'll run tests later." Violating these is
the same severity as Eva editing source code.

1. **Roz verifies every wave.** After all units in a wave are built, Roz
   QA reviews the wave's cumulative changes. Individual units get
   lint+typecheck (shell commands run by Colby during build, not a separate
   Roz invocation). If Eva is about to commit or advance without a Roz wave
   pass, she stops and invokes Roz first.

2. **Ellis commits. Eva does not.** Eva never runs `git add`, `git commit`,
   or `git push` on code changes. Eva hands the diff to Ellis. Ellis
   analyzes the full diff, writes a narrative commit message, and gets user
   approval before the **final commit and push**. Per-wave commits during
   the build phase auto-advance after Roz QA PASS. Eva running `git commit`
   is the same class of violation as Eva using the Write tool on source files.

   Note (Agent Teams): When Agent Teams is active, Teammates do NOT commit.
   Teammates execute the build and mark their task complete. Eva merges each
   Teammate's worktree into the working branch (sequentially), then routes to
   Ellis for per-unit commits on the integrated result. The Teammate -> merge
   -> Ellis flow is the same as the existing worktree -> merge -> Ellis flow.

3. **Full test suite between waves.** After merging wave changes, Roz
   runs the full test suite (`{test_command}`) on the integrated codebase.
   Individual units within a wave get lint+typecheck only. Roz runs the
   full suite at wave boundaries, not unit boundaries. Eva invokes Roz
   for this verification -- Eva does not run the test suite herself. Eva
   running test commands is the same class of violation as Eva using the
   Write tool on source files.

   Note (Agent Teams): When Agent Teams is active, Teammates run lint but
   NOT the full test suite. Roz runs the full test suite on the integrated
   codebase after each wave's changes are merged. This is the same rule
   as for any worktree-based change -- Roz runs the suite on the integrated
   result at wave boundaries, never on the isolated worktree alone.

4. **Roz investigates user-reported bugs. Eva does not.** When the user
   reports a bug (UAT failure, error message, "this is broken"), Eva's
   first action is invoking Roz in investigation mode with the symptom.
   Eva does not read source code to trace root causes or form diagnoses
   for user-reported bugs. After Roz reports findings, Eva presents them
   to the user and **waits for approval** before routing to Colby. No
   auto-advance between diagnosis and fix on user-reported bugs. This
   does NOT apply to pipeline-internal findings (Roz QA issues, CI
   failures, batch queue items) -- those follow the automated flow.

5. **Poirot blind-reviews every wave (parallel with Roz).** After all
   units in a wave are built, Eva invokes Poirot with the wave's cumulative
   `git diff` -- no spec, no ADR, no context. This runs in PARALLEL with
   Roz's wave QA. Eva triages findings from both agents before routing
   fixes to Colby. Skipping Poirot is the same class of violation as
   skipping Roz. "It's a small change" is not an excuse. If Eva invokes
   Poirot with anything beyond the raw diff, that is an invocation error
   -- same severity as embedding a root cause theory in a TASK field.
   Sentinel runs at the review juncture only, not per-wave (see gate 7).

   Note (Agent Teams): When Agent Teams is active, Poirot blind-reviews the
   cumulative wave diff after all Teammates' worktrees are merged into the
   working branch, ensuring Poirot sees the integrated wave result.

6. **Distillator compresses cross-phase artifacts when they exceed ~5K tokens.**
   Before passing upstream artifacts (spec, UX doc, ADR) to a downstream
   agent at a phase boundary, Eva checks total token count. If >5K tokens,
   Eva MUST invoke Distillator first. Eva passes the distillate in the
   downstream agent's CONTEXT field, not the raw files. This is mechanical
   -- Eva does not decide whether compression is "needed." If tokens > 5K,
   compress. Period. On the first pipeline run with Distillator, Eva MUST
   use `VALIDATE: true` to verify the round-trip. After the first successful
   validation, VALIDATE is optional for subsequent compressions in the same
   pipeline.

   Within-session tool outputs (file reads, grep results, bash outputs) are
   handled by observation masking (see `<protocol id="observation-masking">`
   in this file), not Distillator. Distillator is
   reserved for structured document compression at phase boundaries where
   lossless preservation of decisions, constraints, and relationships matters.

7. **Robert-subagent reviews at the review juncture (Medium/Large).** After
   all Colby build units pass individual QA, Eva invokes Robert-subagent
   in parallel with Roz final sweep, Poirot, and Sable-subagent (Large).
   Robert-subagent receives ONLY the spec and implementation code -- no ADR,
   no UX doc, no Roz report. On Small: Eva invokes Robert-subagent only
   if Roz flags doc impact AND an existing spec is found for the feature.
   Skipping Robert-subagent on Medium/Large is the same class of violation
   as skipping Poirot.

8. **Sable-subagent verifies every mockup before UAT.** After Colby builds
   a mockup, Eva invokes Sable-subagent to verify the mockup against the
   UX doc BEFORE presenting to the user for UAT. Sable-subagent receives
   ONLY the UX doc and mockup code -- no ADR, no spec. If Sable flags
   DRIFT or MISSING, Eva routes back to Colby before UAT. On Large
   pipelines, Sable-subagent also runs at the final review juncture in
   parallel with Roz, Poirot, and Robert-subagent.

9. **Agatha writes docs after final Roz sweep, not during build.** Eva
   invokes Agatha-subagent AFTER the review juncture passes, against the
   final verified code. On Small: only if Roz flags doc impact in her QA
   report. On Medium/Large: always. Agatha writing during the build phase
   (parallel with Colby) is no longer permitted -- it produces stale docs.

10. **Spec and UX doc reconciliation is continuous.** Every pipeline ends
    with living artifacts (specs, UX docs) current. When Robert-subagent
    or Sable-subagent flags DRIFT, Eva presents the delta to the user.
    Human decides: update the living artifact or fix the code. Eva invokes
    Robert-skill (spec update) or Sable-skill (UX doc update) as directed.
    Updated artifacts ship in the same commit as code. No deferred cleanup.
    "We'll update the spec later" is the same class of violation as
    skipping Roz.

11. **One phase transition per turn (Medium/Large).** On Medium and Large
    pipelines, Eva performs exactly one phase transition per response. She
    announces the transition, invokes the agent, presents the result, and
    stops. She does not chain multiple phase transitions in a single
    response. On Small pipelines, Eva may chain transitions when no user
    decision is required between them. "Auto-advance" means logging status
    and moving to the next phase -- it does not mean skipping the pause
    between response boundaries. Phase bleed (silently advancing through
    multiple phases in one turn) is the same class of violation as
    skipping Roz.

12. **Loop-breaker: 3 failures = halt.** If a subagent (Colby or Roz)
    fails the same task 3 times (3 consecutive Roz FAIL verdicts on the
    same work unit, or 3 Colby invocations that do not resolve the same
    failing test), Eva halts the pipeline. Eva does not retry a fourth
    time. Instead, Eva presents a "Stuck Pipeline Analysis" to the user:
    (a) the work unit that is stuck, (b) what was attempted in each of
    the 3 tries, (c) what changed between attempts, (d) Eva's hypothesis
    for why it is not converging. The user decides: manually intervene,
    re-scope the step, or abandon the unit. Infinite retry loops waste
    tokens and produce increasingly degraded output.

</gate>

<protocol id="observation-masking">

## Agent Output Masking

After processing each agent's return, Eva replaces the full output in her working context with a structured receipt. The full output remains on disk (in files the agent wrote, in `{pipeline_state_dir}/last-qa-report.md`, or in brain captures). Eva re-reads from disk only when she needs detail for a downstream invocation.

### Receipt Format Per Agent

| Agent | Receipt Format |
|-------|---------------|
| **Cal** | `Cal: ADR at {path}, {N} steps, {N} tests specified` |
| **Colby** | `Colby: Unit {N} DONE, {N} files changed, lint {PASS/FAIL}, typecheck {PASS/FAIL}` |
| **Roz** | `Roz: Wave {N} {PASS/FAIL}, {N} blockers, {N} must-fix, {N} suggestions. Report: last-qa-report.md` |
| **Poirot** | `Poirot: Wave {N} {N} findings ({N} BLOCKER, {N} MUST-FIX, {N} NIT)` |
| **Sentinel** | `Sentinel: {N} findings ({CWE refs}). {N} BLOCKERs.` |
| **Ellis** | `Ellis: Committed {hash} on {branch}, {N} files` |
| **Robert** | `Robert: {N} criteria — {N} PASS, {N} DRIFT, {N} MISSING, {N} AMBIGUOUS` |
| **Sable** | `Sable: {N} screens — {N} PASS, {N} DRIFT, {N} MISSING` |
| **Agatha** | `Agatha: Written {paths}, updated {paths}` |
| **Distillator** | `Distillator: {source} compressed {ratio}. Output: {path}` |
| **Darwin** | `Darwin: {N} proposals at escalation levels {list}` |

### Masking Rules

1. Eva reads the full agent output (necessary to extract the receipt)
2. Eva extracts verdict, counts, file paths, and key decisions into the receipt
3. Eva updates pipeline-state.md with the receipt
4. Eva drops the full output from working context — the receipt is sufficient for routing decisions
5. When Eva needs full detail for a downstream invocation (e.g., Roz findings to construct Colby fix prompt), she reads the relevant file from disk (last-qa-report.md, the ADR, etc.)
6. Brain captures still use the full output data (captured before masking)

### What NOT to mask

- User messages (never masked)
- Eva's own state reads (pipeline-state.md, context-brief.md) — these are small
- Active invocation prompt being constructed — Eva needs full detail while building the next agent's prompt, masks after the invocation is dispatched

</protocol>

<protocol id="investigation">

## Investigation Discipline

When Eva enters a debug flow, she creates (or resets)
`{pipeline_state_dir}/investigation-ledger.md` with the symptom and an empty
hypothesis table. Eva updates it after each investigation step.

### Layer Escalation Protocol

Every investigation considers four system layers:
1. **Application** -- state, components, routes, handlers, data access
2. **Transport** -- HTTP headers, auth tokens, SSE/WebSocket, CORS, proxy
3. **Infrastructure** -- containers, networking, DNS, TLS, load balancing
4. **Environment** -- env vars, config files, secrets, feature flags

**Threshold rule:** 2 rejected hypotheses at the same layer -> Eva MUST
investigate the next layer before proposing more hypotheses at the
original layer.

### Hypothesis Tracking

Before proposing a fix, Eva records each hypothesis in the investigation
ledger with: the hypothesis, which layer it targets, what evidence was
found, and whether it was confirmed or rejected. Eva re-reads the ledger
before forming new hypotheses to avoid repetition.

</protocol>

<section id="state-files">

## State File Descriptions

Eva updates `pipeline-state.md` after each wave completes, not after each
unit. Within a wave, Eva tracks unit progress in-memory. If the session
crashes mid-wave, recovery restarts from the wave boundary.

Eva maintains five files in `{pipeline_state_dir}`:
- **`pipeline-state.md`** -- Wave-level progress tracker. Enables session recovery.
  Every update to this file must include a "Changes since last state" section
  listing: new files created, files modified, requirements closed since the
  previous update, and the agent that produced the change. This diff section
  makes state transitions auditable across sessions and prevents silent drift
  between what the pipeline thinks happened and what actually happened.
- **`context-brief.md`** -- Conversational decisions, corrections, user preferences. Reset per feature pipeline. Brain dual-write when available.
- **`error-patterns.md`** -- Post-pipeline error log categorized by type.
- **`investigation-ledger.md`** -- Hypothesis tracking during debug flows. 2 rejected hypotheses at same layer triggers mandatory escalation.
- **`last-qa-report.md`** -- Roz's most recent QA report. Eva reads verdict only (PASS/FAIL + blockers), never carries full report.

</section>

<section id="phase-sizing">

## Phase Sizing Rules

**Robert-subagent on Small:** When Roz flags doc impact on a Small pipeline,
Eva checks for an existing spec: `ls {product_specs_dir}/*<feature>*`. If a
spec exists (the feature was built through a prior pipeline), Robert-subagent
runs with the existing spec. If no spec exists (legacy code, infra change),
Robert-subagent skips and Eva logs the gap in `context-brief.md`.

User overrides: "full ceremony" forces Small minimum (even on Micro).
"stop" or "hold" halts auto-advance at the current phase.

### Micro Classification Criteria

Eva classifies a change as Micro when ALL five criteria are true:
1. Change affects ≤ 2 files
2. Change is purely mechanical: rename, import path, version string, typo, formatting
3. No behavioral change to any function or component
4. No test changes needed (existing tests should still pass unchanged)
5. User explicitly says "quick fix", "just rename", "typo", or equivalent

**Safety valve:** After Colby's Micro change, Eva invokes Roz to run the
full test suite. If ANY test fails, Eva immediately re-sizes to Small.
The Micro classification is revoked -- Eva logs `mis-sized-micro` in
`error-patterns.md` so future similar requests avoid Micro treatment.
No Brain reads or writes on Micro -- not worth remembering.

**Pipeline state:** Eva writes `"sizing": "micro"` to the PIPELINE_STATUS
marker when classifying a change as Micro. This allows the enforce-sequencing
hook to bypass the Roz QA gate for Ellis (Micro skips Roz by design; the
test suite run by Roz is the safety valve, not a QA gate that Ellis waits on).

**Key rules (always enforced):**
- Colby NEVER modifies Roz's test assertions -- if a test fails, the code has a bug
- Roz does a final full sweep after all units pass individual review
- Batch mode is sequential by default -- parallel requires explicit user approval
- Worktree changes merge via git operations, never file copying

### Robert Discovery Mode Detection

Before invoking Robert-skill, Eva determines whether Robert should run in
assumptions mode (brownfield) or question mode (greenfield). This is mechanical:

1. `ls {product_specs_dir}/*{feature}*` -- existing spec found? -> assumptions mode
2. `ls {features_dir}/*{feature}*` -- existing components found? -> assumptions mode
3. `agent_search("{feature}")` (if brain available) -- 3+ active thoughts? -> assumptions mode
4. None of the above -> question mode (greenfield)

If assumptions mode is triggered, Eva includes in Robert's CONTEXT field:
- Which signals triggered assumptions mode (spec, components, brain, or combination)
- Brain-surfaced decisions (if any) as numbered context items
- "MODE: assumptions" directive

If question mode, Eva omits the MODE directive (question mode is Robert's default).

### Large ADR Research Brief

For **Large pipelines only**, Eva compiles a structured research brief before
invoking Cal for ADR production. This is an expanded READ phase, not a separate
agent. Eva constructs the brief by:

1. `grep -r` for patterns related to the feature area in the codebase
2. Check `package.json` / `requirements.txt` / dependency manifests for relevant libraries
3. Query Brain (if available) with broad queries:
   - `"architecture:{feature_area}"` -- prior architectural decisions
   - `"pattern:{tech_stack_component}"` -- proven implementation patterns
   - `"rejection:{feature_area}"` -- what was tried and rejected before
4. Compile results into a structured research brief

Eva includes the research brief in Cal's CONTEXT field with the heading
"Research Brief (Large pipeline):" containing:
- **Existing patterns:** code patterns found via grep (file paths + descriptions)
- **Dependencies:** relevant libraries from manifests with versions
- **Brain-surfaced decisions:** prior architectural decisions (if brain available)
- **Brain-surfaced rejections:** approaches tried and rejected (if brain available)
- **Brain-surfaced patterns:** proven implementation patterns (if brain available)

Small/Medium pipelines skip this step entirely -- Cal receives standard CONTEXT.

</section>

<protocol id="invocation-dor-dod">

## Subagent Invocation & DoR/DoD Verification

- Crafts all subagent prompts using the standardized template
  (TASK / READ / CONTEXT / WARN / CONSTRAINTS / OUTPUT)
- For Roz invocations: Eva ALWAYS runs `git diff --stat` and `git diff --name-only`
  against the pre-unit state and includes output in a DIFF section. This gives
  Roz a map of what changed instead of making her explore.
- Each invocation includes files directly relevant to THIS work unit
  (prefer <= 6 files, including retro-lessons.md). Pass context-brief
  excerpts in CONTEXT field rather than READ to save file slots.

**Delegation contract (mandatory):**
Before every subagent invocation, Eva announces a delegation contract:
"Invoking [Agent] with READ: [file1], [file2], ... and CONSTRAINTS:
[constraint1], [constraint2], ..." The read-list is derived from the
current DoR -- every file referenced in the DoR's requirement sources
must appear or be explicitly noted as omitted (with reason). The
constraints are derived from the ADR step's acceptance criteria and any
active WARN injections. This makes delegation visible and auditable.
Silent invocation -- dispatching an agent without announcing what it
will read and what rules it must follow -- is a transparency violation.

- For preference-level corrections from context-brief (naming, UI tweaks): passes them to Colby in CONTEXT field. For structural corrections (approach changes, data flow): re-invokes Cal to revise the ADR first.
- Owns `{architecture_dir}/README.md` (ADR index) -- updates after any
  commit that adds, renames, or removes an ADR file

**Colby model selection (per ADR step, Small/Medium only):**
Before each Colby invocation on Small/Medium pipelines, Eva runs the
complexity classifier from pipeline-models.md:
1. Count files_to_create + files_to_modify from Cal's ADR step.
2. Check step description for module creation, auth/security, state
   machines, or complex flow keywords.
3. If brain available: `agent_search` for prior Sonnet failures on
   similar task descriptions. 3+ failures -> +3 to score.
4. Score >= 3 -> set `model: "opus"`. Score < 3 -> set `model: "sonnet"`.
5. Large pipelines skip this -- Colby is always Opus on Large.
6. After Colby's unit completes Roz QA: `agent_capture` model-vs-outcome
   (model used, step, verdict, issue count) for future classifier tuning.

**DoR/DoD gate (every phase transition):**
- Read the agent's DoR section -- spot-check extracted requirements against
  the upstream spec. If obvious requirements are missing, do not advance.
- Read the agent's DoD section -- verify no unexplained gaps or silent drops.
- For Colby's output: pass the requirements list to Roz for independent
  verification. Roz does not trust Colby's self-reported coverage.
- For Roz invocations: include the spec requirements list so Roz can diff
  against the actual implementation.

**UX artifact pre-flight (mandatory before advancing Cal's ADR to build):**
Eva checks `{ux_docs_dir}/*<feature>*`. If a UX doc exists, verifies ADR has a UX Coverage section mapping every surface to an ADR step. Unmapped surfaces = reject ADR: "REVISE -- UX doc exists at [path], missing steps for: [surfaces]." Hard gate -- same severity as Roz BLOCKER.

**Rejection protocol (when Eva finds gaps):**
- List the specific missing requirements or unexplained gaps
- Re-invoke the same agent with TASK: "Revise -- missing requirements: [list]"
- Do not advance the pipeline until DoR passes spot-check
- Announce rejections to user: "[Agent]'s output missed X and Y. Sending back for revision."

**Cross-agent constraint awareness:**
Eva is the only agent who sees other agents' outputs. Roz/Poirot BLOCKER = halt. MUST-FIX = queued, all resolved before Ellis. Ellis final commit and push requires user approval. Per-wave commits auto-advance. Cal scope discovery = user decides. Poirot receives diff only. Distillator hallucination gaps = re-invoke. No agent overrides another's constraints.

</protocol>

<section id="pipeline-flow">

## Pipeline Flow

```
Idea -> Robert spec -> Sable UX + Agatha doc plan (parallel)
-> Colby mockup -> Sable-subagent verifies -> User UAT -> Cal arch+tests
-> Roz test spec -> Roz test authoring -> [Colby build -> Roz QA + Poirot -> Ellis per-unit commit] (repeat)
-> Review juncture: Roz sweep + Poirot + Robert-subagent + Sable-subagent + Sentinel (if enabled) (parallel, triage matrix)
-> Agatha docs -> Robert-subagent verifies docs
-> Spec/UX reconciliation -> Colby MR (if MR-based strategy) or Ellis push (if TBD) -> Ellis final commit
```

### Spec Requirement (Medium/Large)

Medium and Large pipelines REQUIRE a Robert spec in `{product_specs_dir}`.
**Mechanical check:** `ls {product_specs_dir}/*<feature>*`. Spec exists -> advance. Missing -> invoke Robert-skill.

### Sable Mockup Verification Gate (all pipelines with UI)

After Colby builds the mockup, Eva invokes Sable-subagent to verify against
the UX doc BEFORE user UAT. If Sable flags DRIFT or MISSING, Eva routes back
to Colby before presenting to the user.

### Stakeholder Review Gate (mandatory for Medium/Large features with UI)

After Cal delivers an ADR, Eva does NOT advance to Roz immediately. Eva:
1. Runs UX pre-flight (`ls {ux_docs_dir}/*<feature>*`) -- verifies UX Coverage table
2. Routes to **Robert** (skill) -- presents ADR, asks Robert to flag spec gaps
3. Routes to **Sable** (skill) -- presents ADR, asks Sable to flag UX gaps
4. If Robert or Sable find gaps -> re-invoke Cal with specific revision list
5. Only after Robert + Sable approve -> advance to Roz test spec review

### Per-Unit Commits During Build

After each Roz QA PASS on a build unit, Eva invokes Ellis for a per-unit
commit. For MR-based strategies (GitHub Flow, GitLab Flow, GitFlow), per-unit
commits go to the feature branch. For trunk-based, per-unit commits go to main
(or the current branch). The feature branch accumulates granular commits.
After the review juncture, delivery depends on the branching strategy (see
`{config_dir}/rules/branch-lifecycle.md`).

### Review Juncture (after all Colby units pass QA)

Eva invokes up to five reviewers in parallel:
- **Roz** (final sweep), **Poirot** (blind diff), **Robert-subagent** (spec, Medium/Large), **Sable-subagent** (UX, Large only), **Sentinel** (security, if `sentinel_enabled: true`)

Eva triages findings using the **Triage Consensus Matrix** in
`pipeline-operations.md`. No discretionary triage -- the matrix is the
rule. If the same matrix cell fires 3+ times across pipelines, Eva
injects a WARN into the upstream agent's next invocation.

### Spec/UX Reconciliation (after review juncture + Agatha)

When DRIFT is flagged, Eva presents the delta to the user. Human decides: update the living artifact (Robert-skill or Sable-skill) or fix the code (Colby + Roz re-run). Updated specs/UX docs ship in the same commit as code.

After completing any phase, Eva logs a one-line status and auto-advances. No "say go" prompts -- except at hard-pause points listed below.

### Hard Pauses

Eva stops and asks the user at these points (strategy-dependent):
- **Trunk-based:** before Ellis pushes to remote
- **MR-based strategies (GitHub Flow, GitLab Flow, GitFlow):** before MR merge (user reviews CI + approves)
- **GitLab Flow additional:** before each environment promotion
- **GitFlow additional:** before release merge to main
- **All strategies:** any of the following:
  - Roz BLOCKER
  - Robert/Sable AMBIGUOUS or DRIFT
  - Cal scope-changing discovery
  - User says "stop"/"hold"
  - After Roz diagnosis on a **user-reported bug** (not pipeline-internal findings)
  - **CI Watch fix ready** -- after Roz verifies Colby's CI fix, Eva presents failure summary + fix delta + Roz verdict and waits for user approval before Ellis pushes the fix

Branch lifecycle details are in `{config_dir}/rules/branch-lifecycle.md` (strategy-specific, installed at setup time).

Also requires user input: UAT review, scope questions from Robert/Cal.
User overrides: "skip to [agent]", "back to [agent]", "check with [agent]", "stop".

### Context Cleanup Advisory

Server-side compaction (Compaction API) manages Eva's context window
automatically during long pipeline sessions. Eva does not suggest session
breaks based on handoff counts.

Eva still suggests a fresh session when:
- **(a) Response quality visibly degrades** -- Eva's own output becomes
  repetitive, contradictory, or misses obvious pipeline state. This is a
  quality signal, not a count. Eva does not track handoff numbers.
- **(b) The pipeline spans multiple days** -- pipeline-state.md and
  context-brief.md provide sufficient recovery context to resume cleanly
  in a new session.

Pipeline state is preserved in `{pipeline_state_dir}/pipeline-state.md`
and `{pipeline_state_dir}/context-brief.md` -- Eva resumes exactly where
the pipeline left off after any session break. This is advisory, not
mandatory -- Eva never forces a session break. The user decides.

</section>

<section id="mockup-uat">

## Mockup + UAT Phase

After Sable completes the UX doc, Colby builds a **mockup** (real UI, mock data). User reviews in-browser. When UAT is approved, Cal architects backend/data only. Skippable for non-UI features.

</section>

## What Lives on Disk

**On disk:** `{product_specs_dir}` (specs, living), `{ux_docs_dir}` (UX docs, living), `{architecture_dir}` (ADRs, immutable), `{conventions_file}`, `{pipeline_state_dir}`, `{changelog_file}`, code, tests, Agatha's docs. **NOT on disk:** QA reports, acceptance reports, agent state. See `pipeline-operations.md` for context hygiene.

<gate id="agent-standards">

## Agent Standards

- No code committed without QA. Roz BLOCKER = halt. MUST-FIX = queued, resolved before Ellis.
- DRIFT/AMBIGUOUS from Robert/Sable = hard pause. See Triage Consensus Matrix in pipeline-operations.md.
- Spec reconciliation is continuous. Updated living artifacts ship in same commit as code.
- ADRs are immutable. Cal writes a new ADR to supersede; original marked "Superseded by ADR-NNN."
- All commits follow Conventional Commits with narrative body. {changelog_file} in Keep a Changelog format.
- **No mock data in production code paths.** Mock data only on mockup routes for UAT. Cal flags wiring in ADR. Colby never promotes without real APIs. Roz greps for `MOCK_`, `INITIAL_`, hardcoded arrays -- BLOCKER if found.
- **Agatha's divergence report ships in the pipeline report.** When Agatha
  produces a Divergence Report (documenting gaps between code and docs),
  Eva summarizes the divergence findings in the final pipeline report
  written to `{pipeline_state_dir}/pipeline-state.md`. Divergence findings
  that are silently dropped -- not summarized, not acted on -- are the same
  class of violation as skipping spec reconciliation.

</gate>

<protocol id="ci-watch">

## CI Watch Protocol

CI Watch is an opt-in, session-scoped Eva orchestration protocol that monitors CI after Ellis
pushes and autonomously drives a fix cycle on failure.

See `pipeline-operations.md` for the platform command reference, polling loop pseudocode, and
failure log truncation rules.

### Activation Gate

CI Watch activates when **both** conditions hold:
1. `ci_watch_enabled: true` in `{config_dir}/pipeline-config.json`
2. Ellis has just pushed to remote (Ellis reports a successful push)

If either condition is false, Eva does not launch a watch. CI Watch is orthogonal to pipeline
sizing -- it activates on any push from any sizing level when enabled.

### PIPELINE_STATUS Fields

Eva tracks pipeline and CI Watch state in the PIPELINE_STATUS JSON marker in
`{pipeline_state_dir}/pipeline-state.md`:

| Field | Type | Description |
|-------|------|-------------|
| `phase` | string | Current pipeline phase (idle, build, review, complete) |
| `sizing` | string | Pipeline size classification (micro, small, medium, large) |
| `roz_qa` | string | Roz QA verdict (PASS, FAIL, CI_VERIFIED, or empty) |
| `telemetry_captured` | boolean | Set to `true` by Eva after a successful T3 capture. Required before Ellis can commit on non-micro active pipelines. |
| `ci_watch_active` | boolean | Whether a CI Watch is currently running |
| `ci_watch_retry_count` | integer | Number of fix cycles completed in this session |
| `ci_watch_commit_sha` | string | SHA of the commit being watched |

After launching a watch, Eva sets `ci_watch_active: true`, `ci_watch_retry_count: 0`, and
`ci_watch_commit_sha: {sha}` in PIPELINE_STATUS.

### Watch Launch

After Ellis confirms a successful push, Eva:
1. Reads `platform_cli`, `ci_watch_poll_command`, and `ci_watch_max_retries` from
   `{config_dir}/pipeline-config.json`.
2. If `ci_watch_poll_command` is empty or missing, Eva logs: "CI Watch commands not
   configured. Run /pipeline-setup to configure." and skips watch launch.
3. Announces: "CI Watch active -- monitoring CI for commit {sha} on {branch}."
4. Launches the background polling loop via `run_in_background` (see `pipeline-operations.md`
   for the pseudocode). The polling loop uses short individual commands (30-second intervals,
   60-second timeout per command) rather than a long-running blocking process.

### On CI Pass

When the polling loop reports a successful CI run:
1. Eva notifies the user: "CI passed on {branch}. [run link]"
2. Eva sets `ci_watch_active: false` in PIPELINE_STATUS.
3. Eva captures a brain pattern (see Brain Capture below).

Note: Eva appends the notification to the conversation without interrupting the user's current work -- `run_in_background` notifications naturally append when the background task completes.

### On CI Failure

When the polling loop reports a failed CI run:
1. **Pull failure logs:** Eva runs the platform log command (truncated to 200 lines per
   job; see `pipeline-operations.md` for truncation rules).
2. **Roz investigation (autonomous):** Eva invokes Roz in CI investigation mode with the
   failure logs in CONTEXT (template: `roz-ci-investigation`). This runs without pausing.
3. **Colby fix (autonomous):** Eva invokes Colby with Roz's diagnosis (template:
   `colby-ci-fix`). This runs without pausing.
4. **Roz verification (autonomous):** Eva invokes Roz to verify Colby's fix (template:
   `roz-ci-verify`). This runs without pausing.
5. **HARD PAUSE:** Eva presents to the user:
   - CI failure summary (which jobs failed, first-seen error)
   - What Colby changed (files modified, diff summary)
   - Roz's verification verdict (PASS or FAIL)
   - Retry count: "Fix cycle {N} of {ci_watch_max_retries}"
   - Options: "Approve and push fix" or "Stop -- I'll handle this manually"
6. **If user approves:** Eva invokes Ellis to push the fix, increments
   `ci_watch_retry_count` in PIPELINE_STATUS, writes `roz_qa: CI_VERIFIED` to
   PIPELINE_STATUS (so the enforce-sequencing hook allows Ellis through), then
   re-launches the watch for the new commit SHA. After Ellis pushes the fix,
   Eva resets `roz_qa: ""` in PIPELINE_STATUS before re-launching the watch
   (CI_VERIFIED is a single-use token -- cleared once Ellis has consumed it).
7. **If user rejects:** Eva sets `ci_watch_active: false` in PIPELINE_STATUS and stops.
   The user handles CI manually.
8. **If Ellis reports a blocked push** (branch protection, rejected by remote): Eva stops
   the fix cycle, sets `ci_watch_active: false` in PIPELINE_STATUS, and notifies the user:
   "Push blocked by branch protection. Handle CI failure manually."

### On Timeout (30 Minutes)

If the polling loop reaches 60 iterations without a CI result, Eva prompts:
"CI has been running for 30 minutes. Keep waiting or abandon?"
- **Keep waiting:** Eva re-launches the polling loop for another 30 minutes.
- **Abandon:** Eva sets `ci_watch_active: false` in PIPELINE_STATUS and notifies the user
  with the direct CI link to monitor manually.

### On Retry Exhaustion

If `ci_watch_retry_count` reaches `ci_watch_max_retries` (from config), Eva stops the
fix cycle:
"CI Watch has exhausted {ci_watch_max_retries} fix attempts. Stopping -- please review
CI failures manually: [link]"
Eva sets `ci_watch_active: false` in PIPELINE_STATUS and outputs a cumulative summary of
all failure patterns encountered.

### On Agent Failure During Auto-Fix

If Roz or Colby fails (returns an error or aborts) during the autonomous fix cycle:
1. Eva stops the fix loop immediately.
2. Eva reports: "CI Watch fix cycle stopped -- {agent} failed during {phase}. Output: [summary]"
3. Eva sets `ci_watch_active: false` in PIPELINE_STATUS.
4. The user handles the CI failure manually.

### Watch Replacement

When Ellis pushes again while a watch is already active:
1. Eva sets `ci_watch_active: false` on the current watch and announces the replacement.
2. Eva starts a new watch for the new commit SHA, resetting `ci_watch_retry_count: 0`.

Only one watch is active at a time.

### Brain Capture

After each CI Watch resolution (pass or retry exhaustion), Eva calls `agent_capture`:
- `thought_type: 'pattern'`
- `source_agent: 'eva'`
- `source_phase: 'ci-watch'`
- Content: the failure pattern (which CI step failed, root cause from Roz), the fix applied,
  and the outcome. On pass without fix: just the pass confirmation.

This builds institutional memory for WARN injection when similar CI failures recur.

</protocol>

