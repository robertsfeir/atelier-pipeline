# Pipeline Orchestration -- Operational Procedures

Loads automatically when Eva reads `{pipeline_state_dir}/` files. Contains
mandatory gates, brain capture model, investigation discipline, pipeline
flow, agent standards, and verification procedures.

<section id="loading-strategy">

## Loading Strategy

JIT loading. `[ALWAYS]` sections load at pipeline activation. `[JIT]` sections load on trigger.

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

All captures use `thought_type: 'insight'`, `source_agent: 'eva'`,
`source_phase: 'telemetry'`, `metadata.pipeline_id` (set at pipeline start).
Eva reads `telemetry-metrics.md` at pipeline start for metric schemas and cost tables.
When `brain_available: false`, skip all captures. In-memory accumulators still run.

### Tier 1 (per-invocation, in-memory only)

After every Agent tool completion: record duration, extract model/tokens/cost
from result, add to accumulators (`total_cost`, `total_invocations`,
`invocations_by_agent/model`, per-invocation records). NOT captured to brain
individually -- bulk-captured at Tier 2. Micro pipelines: Tier 1 only.

### Tier 2 (per-wave, best-effort)

After each wave passes Roz QA, single `agent_capture` per wave:
- Per-unit: `rework_cycles`, `first_pass_qa`, `unit_cost_usd`
- Wave: `finding_counts`, `finding_convergence`, `evoscore_delta`
- `importance: 0.5`, `metadata.telemetry_tier: 2`, includes bulk T1 data
- `evoscore_delta = (tests_after - tests_broken) / tests_before` (0 tests = 1.0)
- On failure: log and continue. Skipped on Micro.

### Tier 3 (per-pipeline, best-effort)

At pipeline end after Ellis final commit:
- Aggregate from accumulators + T2: `rework_rate`, `first_pass_qa_rate`, `evoscore`,
  `phase_durations`, `total_cost_usd`, `total_duration_ms`, `agent_failures`
- `importance: 0.7`, `metadata.telemetry_tier: 3`
- On success: set `telemetry_captured: true` in PIPELINE_STATUS (required for Ellis gate)
- On failure: do NOT set flag -- gate blocks Ellis, prompting retry
- Skipped on Micro.

### Pipeline-End Telemetry Summary

Standard format:
```
Pipeline complete. Telemetry summary:
  Cost: ${total_cost_usd} ({agent}: ${agent_cost}, ...)
  Duration: {total_duration_min} min ({phase}: {phase_duration_min} min, ...)
  Rework: {rework_rate} cycles/unit ({total_units} units, {first_pass_count} first-pass QA)
  EvoScore: {evoscore} ({tests_before} tests before, {tests_after} after, {tests_broken} broken)
  Findings: Roz {N}, Poirot {N}, Robert {N} (convergence: {N} shared)
```
Micro: `Telemetry: {invocation_count} invocations, {total_duration_min} min`
Cost unavailable: print "Cost: unavailable (token counts not exposed)".
Post-summary: "Tip: Run /telemetry-hydrate to capture detailed token usage."

### Darwin Auto-Trigger (at pipeline end)

Fires when ALL: `darwin_enabled: true`, `brain_available: true`, degradation
alert fired, sizing != Micro. Eva pre-fetches T3 telemetry + prior Darwin
proposals + error-patterns.md, invokes Darwin. User approves/rejects/modifies
each proposal individually (hard pause). Approved: capture + route to Colby
+ Roz verify + Ellis commit. Rejected: capture with reason. Does not block
pipeline completion.

### Pattern Staleness Check (pipeline end)

After pipeline (and Darwin if applicable): check `thought_type: 'pattern'`
thoughts referencing files modified in this pipeline. >50% churn since capture
= invalidate via `atelier_relation` supersedes. 20-50% churn = append warning.

### Dashboard Bridge (post-pipeline, PlanVisualizer only)

If `dashboard_mode: "plan-visualizer"`: run `{config_dir}/dashboard/telemetry-bridge.sh`.
Failure is never a blocker. `claude-code-kanban` or `none`: skip entirely.

Eva boot dashboard announcement: `plan-visualizer` -> "Dashboard: PlanVisualizer",
`claude-code-kanban` -> "Dashboard: claude-code-kanban", `none`/absent -> omit.

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
unit. Within a wave, Eva tracks unit progress in-memory.

Eva maintains five files in `{pipeline_state_dir}`:
- **`pipeline-state.md`** -- Wave-level progress tracker with "Changes since last state" section.
- **`context-brief.md`** -- Conversational decisions, corrections, user preferences. Reset per feature.
- **`error-patterns.md`** -- Post-pipeline error log categorized by type.
- **`investigation-ledger.md`** -- Hypothesis tracking during debug flows.
- **`last-qa-report.md`** -- Roz's most recent QA report. Eva reads verdict only.

</section>

<section id="phase-sizing">

## Phase Sizing Rules

**Robert-subagent on Small:** When Roz flags doc impact, Eva checks for an
existing spec: `ls {product_specs_dir}/*<feature>*`. Spec exists -> run Robert.
No spec -> skip, log gap.

User overrides: "full ceremony" forces Small minimum. "stop"/"hold" halts auto-advance.

### Micro Classification Criteria

ALL five must be true: (1) <=2 files, (2) purely mechanical, (3) no behavioral
change, (4) no test changes needed, (5) user says "quick fix"/"typo"/equivalent.

Safety valve: Roz runs full suite after Micro. ANY test fail -> re-size to Small,
log `mis-sized-micro`. No brain on Micro.

**Key rules:** Colby NEVER modifies Roz's assertions. Roz does final sweep after
all units. Batch sequential by default. Worktree changes merge via git, not copying.

### Robert Discovery Mode Detection

Mechanical: (1) existing spec? (2) existing components? (3) brain 3+ thoughts?
Any -> assumptions mode. None -> question mode (default).

### Large ADR Research Brief

Eva compiles research brief before Cal: grep patterns, check manifests, query
brain for architecture/pattern/rejection. Included in Cal's CONTEXT.
Small/Medium skip this.

</section>

<protocol id="invocation-dor-dod">

## Subagent Invocation & DoR/DoD Verification

- Crafts prompts using standardized template (TASK/READ/CONTEXT/WARN/CONSTRAINTS/OUTPUT)
- For Roz: always include `git diff --stat` and `git diff --name-only`
- Prefer <=6 files per invocation. Context-brief excerpts in CONTEXT, not READ.

**Delegation contract (mandatory):** Before every invocation, Eva announces:
"Invoking [Agent] with READ: [...] and CONSTRAINTS: [...]". Silent invocation
is a transparency violation.

**Colby model selection:** See pipeline-models.md. Score files + complexity
signals. Score >=3 -> Opus. Brain failures +3. Large always Opus.

**DoR/DoD gate:** Spot-check DoR against spec. Verify DoD has no silent drops.
Pass Colby's requirements to Roz for independent verification.

**UX pre-flight:** Check `{ux_docs_dir}/*<feature>*`. UX doc exists -> ADR
must have UX Coverage section. Unmapped surfaces = reject ADR.

**Rejection protocol:** List gaps, re-invoke with "Revise -- missing: [list]".
Announce rejections to user.

**Cross-agent awareness:** Roz/Poirot BLOCKER = halt. MUST-FIX queued before
Ellis. Poirot receives diff only. Distillator gaps = re-invoke.

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

`ls {product_specs_dir}/*<feature>*`. Exists -> advance. Missing -> invoke Robert-skill.

### Sable Mockup Verification Gate

After mockup, Sable verifies against UX doc BEFORE UAT. DRIFT/MISSING -> back to Colby.

### Stakeholder Review Gate (Medium/Large with UI)

After Cal's ADR: (1) UX pre-flight, (2) Robert flags spec gaps, (3) Sable flags
UX gaps, (4) gaps -> re-invoke Cal, (5) both approve -> advance to Roz.

### Per-Unit Commits During Build

After Roz QA PASS: Ellis per-unit commit. MR-based -> feature branch.
Trunk-based -> main. Review juncture delivery per branching strategy.

### Review Juncture

Up to five parallel: Roz (sweep), Poirot (blind), Robert (spec, Med/Large),
Sable (UX, Large), Sentinel (security, if enabled). Triage via Consensus
Matrix in `pipeline-operations.md`.

### Hard Pauses

- **Trunk-based:** before Ellis pushes to remote
- **MR-based:** before MR merge
- **All strategies:** Roz BLOCKER, Robert/Sable AMBIGUOUS/DRIFT, Cal scope
  discovery, user "stop"/"hold", after Roz diagnosis on user-reported bug,
  CI Watch fix ready

User overrides: "skip to [agent]", "back to [agent]", "stop".

### Context Cleanup Advisory

Compaction API manages context automatically. Eva suggests fresh session only
when: (a) response quality visibly degrades, (b) pipeline spans multiple days.
Pipeline state preserved in `{pipeline_state_dir}` for recovery.

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

Opt-in, session-scoped protocol that monitors CI after Ellis pushes. See
`pipeline-operations.md` for platform commands, polling pseudocode, log truncation.

### Activation & State

Activates when `ci_watch_enabled: true` AND Ellis just pushed. PIPELINE_STATUS
fields: `ci_watch_active`, `ci_watch_retry_count`, `ci_watch_commit_sha`,
plus standard `phase`, `sizing`, `roz_qa`, `telemetry_captured`.

### Watch Launch

Eva reads config, announces watch, launches background polling (30s intervals,
60s timeout per command). If `ci_watch_poll_command` unconfigured: skip.

### On CI Pass

Notify user, set `ci_watch_active: false`, capture brain pattern.

### On CI Failure

1. Pull logs (200 lines/job) -> 2. Roz diagnoses (autonomous) -> 3. Colby fixes
(autonomous) -> 4. Roz verifies (autonomous) -> 5. **HARD PAUSE**: present
summary + fix + verdict + retry count to user.
- User approves: Ellis pushes, increment retry, `roz_qa: CI_VERIFIED` (single-use),
  re-launch watch for new SHA. Reset `roz_qa` after Ellis consumes.
- User rejects: stop watch, user handles manually.
- Ellis push blocked: stop watch, notify user.

### Timeout / Exhaustion / Agent Failure

30 min timeout -> prompt keep/abandon. Retry exhaustion -> stop + cumulative
summary. Roz/Colby failure during auto-fix -> stop immediately, user handles.

### Watch Replacement

New push while active: replace watch, reset retry count. One watch at a time.

### Brain Capture

After resolution: `agent_capture` with `thought_type: 'pattern'`,
`source_phase: 'ci-watch'`, content: failure pattern + fix + outcome.

</protocol>
