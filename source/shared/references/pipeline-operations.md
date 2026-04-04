# Pipeline Operations Reference

Eva reads this file at pipeline start for detailed operational procedures.

<section id="invocation-format">

## Invocation Format

All subagent invocations use XML tags. Eva constructs prompts with `<task>`,
`<brain-context>`, `<context>`, `<hypotheses>`, `<read>`, `<warn>`,
`<constraints>`, and `<output>` tags. See `{config_dir}/references/xml-prompt-schema.md`
and `{config_dir}/references/invocation-templates.md` for the full tag vocabulary
and per-agent examples.

</section>

<protocol id="brain-prefetch">

## Brain Context Prefetch

Eva prefetches brain context before invoking agents. Agents with brain access
also capture directly. Reinforced by `prompt-brain-prefetch.sh` PreToolUse hook.

1. Calls `agent_search` with a query derived from the feature area
2. Injects results into the `<brain-context>` tag in the invocation prompt
3. Agents with `mcpServers: atelier-brain` (Cal, Colby, Roz, Agatha) capture
   domain-specific knowledge directly via their Brain Access protocols

Eva captures cross-cutting concerns only (best-effort). See agent personas for
domain-specific capture gates.

</protocol>

<operations id="continuous-qa">

## Continuous QA (Wave-Level Roz + Colby)

Cal's ADR steps become work units grouped into waves. Roz writes tests per wave, Colby implements per unit, QA runs per wave.

**Pre-build test authoring (per wave, not per unit):**
1. Eva invokes Roz in Test Authoring Mode for ALL units in the wave at once
2. Roz reads Cal's test spec for all wave units + existing code + product spec
3. Roz writes test files for the entire wave -- concrete assertions per unit
4. Tests are expected to fail -- they define the target state for the wave

**Build (per unit within wave):**
1. Eva invokes Colby for each unit sequentially (or via Agent Teams in parallel)
2. Colby implements to make Roz's tests pass (may add additional tests)
3. After each Colby unit, Colby runs `lint + typecheck` as a fast sanity check
   (shell command in build flow, not a separate agent invocation)
4. If lint/typecheck fails, Colby fixes before marking unit complete

**Wave QA (per wave, not per unit):**
1. After ALL units in the wave are built, Eva invokes Roz for wave-level QA AND
   Poirot for wave-level blind diff review in PARALLEL. Roz gets full context for
   all units in the wave; Poirot gets ONLY the cumulative `git diff` for the wave.
2. Eva triages findings from both reviewers: deduplicates, classifies severity.
   Findings unique to Poirot get special attention.
3. If any findings require fixes, Eva routes to Colby. After fix, Eva invokes Roz
   for a scoped rerun on the affected unit(s) only.
4. **Sentinel does NOT run per-wave.** Sentinel runs once at the review juncture only.
5. **Eva invokes Ellis for a per-wave commit** on the feature branch after wave QA
   PASS. Ellis uses wave commit mode. Per-wave commits auto-advance after Roz
   QA PASS -- no user approval required. The final commit and push requires
   user approval (hard pause).
6. Eva updates `{pipeline_state_dir}/pipeline-state.md` after each wave completes

**Post-build pipeline tail (after all waves complete -- review juncture):**
7. Eva invokes the review juncture: Roz final sweep + Poirot + Robert-subagent
   + Sable-subagent (Large) + Sentinel (if `sentinel_enabled: true`) in parallel.
   Sentinel runs HERE (at review juncture) and not during the build phase.
   Eva triages findings using the Triage Consensus Matrix (see below). Routes
   fixes to Colby if needed, re-runs Roz. Eva captures Sentinel findings
   post-review via `agent_capture` with `source_agent: 'eva'`,
   `thought_type: 'insight'` (same pattern as Poirot -- Sentinel does not touch
   brain directly).
8. Eva invokes Agatha to write/update docs against the final verified code.
   On Small: only if Roz flagged doc impact. On Medium/Large: always.
9. Eva invokes Robert-subagent in doc review mode to verify Agatha's output
10. If Robert-subagent or Sable-subagent flagged DRIFT: hard pause. Human
    decides fix code or update spec/UX.
11. Final delivery (strategy-dependent, see `{config_dir}/rules/branch-lifecycle.md`):
    - **Trunk-based:** Eva invokes Ellis in standard mode. Ellis commits and
      pushes to main. Hard pause before push to remote.
    - **MR-based strategies (GitHub Flow, GitLab Flow, GitFlow):** Eva invokes
      Colby to create an MR via the configured platform CLI, targeting the
      integration branch. MR body includes: ADR reference, QA status, review
      juncture results. Hard pause -- user reviews CI and merges.
    - **GitLab Flow additional:** After MR merges, Eva offers environment
      promotion. Hard pause at each environment boundary.
    - After merge/push: Eva handles branch cleanup (deletes feature branch
      local + remote for MR-based strategies). Code + docs + updated specs/UX
      ship as one merge. Per-wave history is preserved on the feature branch
      for `git bisect`.

</operations>

<matrix id="triage-consensus">

## Triage Consensus Matrix

At every review juncture, Eva consults this matrix to determine the action.
No discretion -- the matrix is the rule.

| Roz | Poirot | Robert | Sable | Sentinel | Action |
|-----|--------|--------|-------|----------|--------|
| BLOCKER | any | any | any | -- | **HALT.** Roz BLOCKER is always authoritative. |
| any | BLOCKER | any | any | -- | **HALT.** Eva investigates Poirot's finding. If confirmed, same as Roz BLOCKER. |
| any | any | any | any | BLOCKER | **HALT.** Sentinel BLOCKER (exploitable vulnerability) is always authoritative. Eva verifies Semgrep finding is not false positive (check CWE, check if code path is reachable). If confirmed, same as Roz BLOCKER. |
| MUST-FIX | agrees | -- | -- | -- | **HIGH-CONFIDENCE.** Queue fix, Colby priority. |
| PASS | flags issue | -- | -- | -- | **CONTEXT-ANCHORING MISS.** Eva investigates -- Poirot caught what Roz's context biased her to miss. Treat as MUST-FIX minimum. |
| MUST-FIX | PASS | -- | -- | -- | **STANDARD.** Queue fix per normal flow. |
| PASS | PASS | -- | -- | MUST-FIX | **SECURITY CONCERN.** Queue fix, Colby priority. Sentinel caught what Roz and Poirot missed (SAST-specific finding). |
| MUST-FIX | flags issue | -- | -- | MUST-FIX | **CONVERGENT SECURITY.** Multiple reviewers flag security. High-confidence fix needed. |
| -- | -- | DRIFT | -- | -- | **HARD PAUSE.** Human decides: fix code or update spec. |
| -- | -- | AMBIGUOUS | -- | -- | **HARD PAUSE.** Human clarifies spec. |
| -- | -- | -- | DRIFT | -- | **HARD PAUSE.** Human decides: fix code or update UX doc. |
| -- | -- | DRIFT | DRIFT | -- | **CONVERGENT DRIFT.** High-confidence spec/UX misalignment. Escalate to human with both reports. |
| PASS | PASS | PASS | PASS | PASS | **ADVANCE.** All clear, proceed to Agatha. |

When `sentinel_enabled: false`, the Sentinel column is absent from triage -- Eva skips Sentinel entirely and the matrix behaves as it did before Sentinel was added.

**Brain capture gate (when brain_available: true):** After each triage,
Eva calls `agent_capture` with `thought_type: 'insight'`, content:
"Triage outcome: [matrix cell triggered]. Reviewers agreed/disagreed on
[issue]. Action taken: [action]." At review juncture start, Eva calls
`agent_search` for prior triage insights on the feature area. If a
recurring pattern exists, Eva adds a WARN to the relevant agent's invocation.

**Escalation rule:** If the same matrix cell fires 3+ times across
pipelines (tracked via Brain or error-patterns.md), Eva injects a WARN
into the upstream agent's next invocation. Example: persistent Roz-PASS +
Poirot-flags-issue on the same module -> WARN to Roz: "Poirot has caught
issues in this module that you've missed 3 times. Extra scrutiny warranted."

</matrix>

<section id="feedback-loops">

## Feedback Loops

| Trigger | Route |
|---------|-------|
| UAT feedback (UI tweaks) | Colby mockup fix -> Sable-subagent re-verify -> re-UAT |
| UAT feedback (spec change) | Robert -> Sable -> re-mockup -> Sable-subagent verify |
| UAT feedback (UX flow change) | Sable -> re-mockup -> Sable-subagent verify |
| Sable-subagent mockup DRIFT | Colby mockup fix -> Sable-subagent re-verify |
| Roz test spec gaps | Cal subagent (revise) -> Roz (re-review) |
| Roz code QA (minor) | Colby fix -> Roz scoped re-run |
| Roz code QA (structural) | Cal subagent (revise) -> Colby -> Roz full run |
| Robert-subagent spec DRIFT | Hard pause -> human decides -> Robert-skill updates spec OR Colby fixes code |
| Sable-subagent UX DRIFT | Hard pause -> human decides -> Sable-skill updates UX doc OR Colby fixes code |
| CI/CD issue | Colby (config) or Cal subagent (architectural) |
| User reports a bug | Roz (investigate + diagnose) -> Colby (fix) -> Roz (verify) |
| CI failure (watched) | Roz (CI investigate) -> Colby (CI fix) -> Roz (CI verify) -> hard pause -> Ellis (push fix) -> re-watch |

</section>

<section id="cross-agent-consultation">

## Cross-Agent Consultation

If any agent raises a concern about another agent's domain, Eva asks the
user if they want to loop that agent back in:
- Cal questions Robert's spec -> "Want me to check with Robert on this?"
- Sable's design implies arch changes -> "Cal should weigh in. Loop him in?"
- Roz finds a spec gap -> "This traces back to the spec. Want Robert to clarify?"

</section>

<operations id="batch-mode">

## Batch Mode (Multiple Issues)

Default execution model is **sequential with full pipeline per issue.**

1. **One issue at a time.** Eva does not start issue N+1 until issue N is committed and verified.
2. **Roz runs the full test suite between issues.** Eva invokes Roz between issues. If tests fail, Eva halts and routes the failure.
3. **Parallelization requires explicit user approval** and zero file overlap confirmation.
4. **No silent reordering.** Eva announces dependency-driven reorders.

</operations>

<operations id="worktree-rules">

## Worktree Integration Rules

Changes from isolated worktrees must be integrated using git operations -- **never naive file copying.**

1. **Use `git merge` or `git cherry-pick`** to bring worktree changes into the working branch.
2. **Resolve conflicts before advancing.** Route to Colby for resolution, run Roz before advancing.
3. **One worktree merges at a time.** Eva invokes Roz to run the test suite between each merge.
4. **Worktree agents do not see each other's changes.** Eva is responsible for the integration.

**Agent Teams Worktrees (when `agent_teams_available: true`, experimental):**

Agent Teams worktrees are managed by Claude Code, not by Eva via Bash. Eva
does not create or delete worktrees manually -- the Agent Teams runtime
handles worktree lifecycle.

- **Merge order:** Eva merges Teammates' worktrees one at a time, in the
  order tasks were created (deterministic merge order matches task creation
  order). This ensures reproducible integration regardless of Teammate
  completion order.
- **Test suite between merges:** Rule 3 applies unchanged -- Eva invokes
  Roz to run the full test suite on the integrated codebase between each
  Teammate merge.
- **Merge conflict handling:** If a conflict is detected during a Teammate
  merge, Eva falls back to sequential for the conflicting unit. Eva routes
  conflict resolution to Colby, runs Roz before advancing (Rule 2 applies).
- **Worktree cleanup:** Claude Code manages worktree lifecycle. Eva does not
  delete worktrees via Bash. After a successful merge and Roz QA PASS, the
  worktree is no longer needed -- Eva signals completion to the Agent Teams
  runtime rather than manually removing the directory.

</operations>

<operations id="wave-execution">

## Wave Execution (Parallel Build Units)

When an ADR has multiple steps, Eva analyzes file-level dependencies to
group independent steps into waves. Steps within a wave execute in
parallel; waves execute sequentially.

**Wave extraction algorithm (Eva, after Roz test spec is ready):**
1. For each ADR step, extract: `files_to_create`, `files_to_modify`
   (from Cal's plan).
2. Build adjacency: step A depends on step B if A modifies/reads a file
   that B creates or modifies.
3. Topological sort into waves -- steps with zero shared files land in
   the same wave.
4. Validate: confirm zero file overlap within each wave. If any two steps
   in a wave touch the same file, merge them into separate waves.
5. If overlap is detected AFTER Colby completes a unit (runtime conflict):
   fall back to sequential for remaining units, log as lesson in
   error-patterns.md.

**Sub-unit execution order:** When an ADR uses sub-sliced steps (e.g., 2a,
2b, 2c), sub-units within the same parent step execute sequentially — 2a
completes Colby/Roz/Ellis before 2b begins. Sub-units from different parent
steps (e.g., 2c and 3a) may be wave-grouped if they have zero file overlap,
following the standard wave extraction algorithm above.

**Brain integration (Eva, wave grouping):**
- **Read gate:** Before grouping, `agent_search` for prior wave decisions
  on this feature area. Reuse prior grouping as a starting point (still
  validate file overlap).
- **Write gate:** After grouping, `agent_capture` with
  `thought_type: 'decision'`, `source_agent: 'eva'`,
  `source_phase: 'build'`, content: "ADR-NNNN wave grouping:
  Wave 1 [steps ...], Wave 2 [steps ...]. Rationale: [file overlap].
  Execution: [sequential | agent-teams]."

**Wave execution backend:**

After the wave extraction algorithm completes, Eva executes the wave using
one of two backends:

**Sequential (default -- when `agent_teams_available: false`):**
Eva invokes one Colby subagent per unit, one at a time, waiting for each
to complete before starting the next. Current behavior -- no change.

**Agent Teams (when `agent_teams_available: true`, experimental):**
Eva creates one Teammate (Colby instance in a dedicated worktree) per wave
unit using `TaskCreate`. Each Teammate receives a structured task description
(see `invocation-templates.md`, template `agent-teams-task`). Eva then waits
for TaskCompleted events from all Teammates in the wave.

Teammate task contract format:
```
ADR: ADR-NNNN Step N
Files to create: [list]
Files to modify: [list]
Test files: [list]
Constraints: [from ADR step acceptance criteria]
Wave: N of M, Unit: K of L
maxTurns: 25
```

Teammates run Colby's persona (`{config_dir}/agents/colby.md`). They run lint
after implementation. They do NOT run the full test suite and do NOT commit.

After all TaskCompleted events arrive for the wave, Eva merges each worktree
sequentially -- one merge at a time, in the order tasks were created (see
Worktree Integration Rules). Eva invokes Roz to run the full test suite
between each merge.

**Timeout and failure handling (Agent Teams):**
- Default `maxTurns: 25` per Teammate. If a Teammate does not complete
  within its turn limit, Eva marks the unit as failed.
- If any Teammate in a wave fails or times out: Eva completes the merges
  for successful Teammates, then runs the failed unit sequentially as a
  normal Colby subagent invocation.
- Eva announces at wave start: "Wave N executing via Agent Teams:
  [K teammates]" or "Wave N executing sequentially."
- 3-failure loop-breaker (gate 12) applies per unit, not per Teammate.

**Constraint preservation within waves:**
- Each unit within a wave follows: Colby build + lint/typecheck. After all
  units in the wave complete: Roz wave QA + Poirot wave blind review.
  All mandatory gates apply per wave, not per unit.
- When Agent Teams is active, Roz and Poirot run after ALL Teammates'
  worktrees in the wave are merged -- they review the cumulative wave
  result, not individual worktree diffs.
- Roz and Poirot run once per wave on the cumulative wave diff.
  Cross-wave integration is the final review juncture.
- The final review juncture (Roz sweep + Poirot + Robert + Sable) runs
  AFTER all waves complete, not after each wave.
- Batch-mode rules still apply: parallel requires zero file overlap,
  sequential is the fallback. Eva announces wave grouping to the user
  before execution begins.

### Scope: Wave Execution Only

Agent Teams applies exclusively to Colby build units within a wave. Agent
Teams does NOT replace subagent invocations for any other agent:

- Roz, Poirot, Robert, Sable, Ellis, Agatha, Cal, Sentinel, and all
  discovered agents are invoked sequentially (existing behavior, unchanged).
- Agent Teams is not used for read-only verification agents, doc writers,
  commit agents, or any phase outside the Colby build step.

Revisit: if Agent Teams supports non-worktree Teammates for parallel
read-only review in a future version.

### Teammate Identity

Teammates are Colby instances. They are NOT a new agent type. Teammates load
Colby's persona from `{config_dir}/agents/colby.md` and project rules from
`{config_dir}/rules/`. No new persona file exists for Teammates. Teammates match
the `enforce-colby-paths.sh` per-agent hook and have full write access to the
codebase (same as a standard Colby subagent invocation).

### Task Lifecycle

1. Eva creates one task per wave unit via `TaskCreate` with a structured
   task description (see `invocation-templates.md`, template `agent-teams-task`).
2. Teammate instances pick up tasks and execute the build units.
3. Each Teammate marks its task complete via `TaskUpdate` when done.
4. `TaskCompleted` events fire on Eva (Team Lead). Eva processes them
   sequentially -- one at a time, not in parallel -- to avoid race
   conditions in state updates to `pipeline-state.md`.
5. After all Teammates in the wave complete (all TaskCompleted events
   received), Eva merges each worktree sequentially (see Worktree
   Integration Rules -- Agent Teams Worktrees subsection).
6. After all worktrees in the wave are merged, Roz wave QA + Poirot wave
   blind review run once on the cumulative wave diff (see Wave QA above).

Eva uses `TaskGet` to check Teammate task status during wave execution.

### Fallback Behavior

When `agent_teams_available: false` (config flag off, env var unset, or
runtime detection fails), Eva falls back to sequential subagent invocation.
The pipeline output is identical -- Agent Teams affects execution speed, not
correctness or quality.

</operations>

<operations id="ci-watch">

## CI Watch Operations

CI Watch activates after Ellis pushes when `ci_watch_enabled: true` in `pipeline-config.json`.
All platform commands are derived from `platform_cli` configured at setup time.

### Platform Command Reference

| Operation | GitHub (`gh`) | GitLab (`glab`) |
|-----------|--------------|-----------------|
| Check run status | `gh run list --commit {sha} --json status,conclusion,url,databaseId --limit 1` | `glab ci list --branch {branch} -o json \| head -1` |
| Get failure logs | `gh run view {run_id} --log-failed \| tail -200` | `glab ci trace {job_id} \| tail -200` |
| Get run URL | Included in `gh run list` JSON output (`url` field) | `glab ci view --branch {branch} --web` (URL in output) |
| Auth check | `gh auth status` | `glab auth status` |

### Polling Loop Pseudocode

Eva launches a background Bash polling loop via `run_in_background` after Ellis pushes:

```
# Read from pipeline-config.json at watch launch:
#   max_retries = ci_watch_max_retries  -- fix cycle cap (how many Roz->Colby->Roz cycles before giving up)
#   Note: max_errors below is a separate polling-health counter, not the fix cycle cap.

max_iterations = 60          # 30 minutes at 30-second intervals
poll_interval  = 30          # seconds between polls
error_streak   = 0           # consecutive polling errors (network/CLI health)
max_errors     = 3           # error streak threshold: 3 consecutive failures -> abandon watch
                             # DISTINCT from ci_watch_max_retries (fix cycle cap from config)

for i in 1..max_iterations:
  result = run(platform_poll_command, timeout=60s)
  if result is error:
    error_streak++
    if error_streak >= max_errors:
      notify("CI Watch lost connection to [platform]. Check CI status manually.")
      exit
    continue
  error_streak = 0
  if result is empty:
    notify("No CI run found for commit {sha}. Does this repo have CI configured?")
    exit
  status = parse(result)
  if status == "completed":
    if conclusion == "success":
      notify("CI passed on [branch]. [run_url]")
      capture_brain_pattern(outcome="pass")
      exit
    else:
      # Extract run/job ID from poll result for use in log command
      # GitHub: run_id = parse(result, "databaseId")
      # GitLab: job_id = parse(result, "id")
      # Then substitute into ci_watch_log_command before running
      logs = run(platform_log_command | tail -200, timeout=60s)
      # Return logs to Eva main thread; Eva checks ci_watch_retry_count < ci_watch_max_retries
      # before launching fix cycle. If retry cap reached, Eva stops and reports.
      return logs to Eva main thread for fix cycle
      exit
  sleep(poll_interval)

# timeout reached (30 minutes)
notify("CI has been running for 30 minutes. Keep waiting or abandon?")
wait for user input
```

### Failure Log Truncation Rules

- **Single failed job:** last 200 lines of the job log.
- **Multiple failed jobs:** concatenate logs with a job header line (`--- Job: {job_name} ---`) between each; total cap at 400 lines (200 per job, up to 2 jobs; if more than 2 jobs fail, take the first 2 failing jobs' logs).
- Logs are passed to Roz in the CONTEXT field of the `roz-ci-investigation` template, not written to disk.

### CI Watch State Fields (PIPELINE_STATUS marker in `{pipeline_state_dir}/pipeline-state.md`)

| Field | Type | Description |
|-------|------|-------------|
| `ci_watch_active` | boolean | Whether a watch is currently running |
| `ci_watch_retry_count` | integer | Number of fix cycles completed in this session |
| `ci_watch_commit_sha` | string | SHA of the commit being watched |

**Watch replacement:** When Ellis pushes again while a watch is active, Eva sets `ci_watch_active: false` on the old watch and starts a new watch for the new commit SHA. Only one watch is active at a time.

### Telemetry Accumulator Fields (PIPELINE_STATUS marker in `{pipeline_state_dir}/pipeline-state.md`)

Eva writes telemetry accumulator fields to PIPELINE_STATUS at each phase transition, piggybacking
on existing pipeline-state.md updates. This enables session recovery: if Eva restarts mid-pipeline,
she reads the last PIPELINE_STATUS to restore telemetry accumulators.

| Field | Type | Description |
|-------|------|-------------|
| `telemetry_pipeline_id` | string | `{feature_name}_{ISO_timestamp}`, set at pipeline start |
| `telemetry_total_invocations` | integer | Running count of agent invocations |
| `telemetry_total_cost_usd` | float or null | Running cost total (null if any invocation had no pricing data) |
| `telemetry_rework_by_unit` | object | `{unit_id: rework_count}` per work unit |

**Session recovery:** On pipeline resume, Eva reads the last PIPELINE_STATUS and restores telemetry
accumulators: `telemetry_total_invocations`, `telemetry_total_cost_usd`, and `telemetry_rework_by_unit`.

**Upgrade safety:** On the first pipeline after upgrade, PIPELINE_STATUS will lack telemetry fields.
Eva initializes absent telemetry fields to zero defaults: `telemetry_total_invocations: 0`,
`telemetry_total_cost_usd: null`, `telemetry_rework_by_unit: {}`. No crash, no undefined values.

</operations>

<section id="context-hygiene">

## Context Hygiene

### Compaction Strategy

When the Compaction API is active (`context_management.edits` enabled), server-side compaction
manages Eva's context automatically. Eva does not need to track context usage percentage or
suggest session breaks for context reasons.

- **Primary within-session mechanism: observation masking.** Before each subagent invocation and at phase transitions, Eva replaces superseded tool outputs (file reads, grep results, bash outputs) with structured placeholders. See `<protocol id="observation-masking">` below for the full procedure.
- **Cross-phase artifact compression: Distillator.** When upstream documents (spec, UX doc, ADR) exceed ~5K tokens at a phase boundary, Eva invokes Distillator. See gate 6 in `pipeline-orchestration.md`.
- **Between major phases:** start fresh subagent sessions. Pipeline-state.md is the recovery mechanism.
- **Within Colby+Roz interleaving:** Each unit is a separate subagent invocation (fresh context).
- **Eva herself:** Compaction API manages context automatically. Eva no longer tracks context usage
  percentage. For very large pipelines (20+ agent handoffs), Eva may still suggest a fresh session
  if response quality visibly degrades -- but this is a quality signal, not a context-counting
  heuristic.
- **Path-scoped rules survive compaction.** `pipeline-orchestration.md` and `pipeline-models.md`
  are re-injected from disk on every turn (ADR-0004 design). Mandatory gates and triage logic are
  protected from lossy summarization regardless of compaction events.
- **Eva writes pipeline-state.md at every phase transition (existing behavior).** This is the
  primary compaction safety net -- if compaction summarizes away in-progress details, Eva can
  recover from the last recorded phase. The PreCompact hook provides an additional safety net by
  appending a timestamped compaction marker to pipeline-state.md before compaction fires.
- **Brain captures provide a secondary recovery path** (when `brain_available: true`). Decisions,
  findings, and lessons captured during the pipeline are queryable after compaction via
  `agent_search`. Compaction may summarize Eva's accumulated context about agent outputs and triage
  findings; brain captures preserve the decisions that matter most.
- **Agent Teams Teammates have inherently fresh context per task.** Each Teammate is a new Claude
  Code instance -- no compaction needed. Teammates start fresh regardless of wave width.
- **Never carry Roz reports in Eva's context.** Read the verdict only.
- **Wave-boundary compact advisory.** A SubagentStop prompt hook (`prompt-compact-advisory.sh`) detects when Ellis completes a per-wave commit during the build phase and advises Eva to suggest `/compact` to the user. This is purely advisory -- Eva relays the suggestion; the user decides. The advisory does not fire on the final commit (review/complete phase) because the pipeline is ending.

### What Eva Carries vs. What Subagents Carry

| Context | Eva | Subagents |
|---------|-----|-----------|
| pipeline-state.md | Always | Never (they get their unit scope) |
| context-brief.md | Summary only | Relevant excerpt in CONTEXT field |
| CONVENTIONS.md | Never | Only when writing code |
| dor-dod.md | Never | In their persona file |
| retro-lessons.md | Never | Always (included in every READ) |
| Feature spec | Never | Only if directly relevant |
| ADR | Never | Only the relevant step |
| Teammate task description | Creates (via TaskCreate) | Consumes (read from task) |
| Masked observations | Placeholders with re-read metadata | Never (they get fresh context) |

</section>

<protocol id="observation-masking">

## Observation Masking

Observation masking is Eva's primary within-session context hygiene procedure.
It replaces superseded tool outputs with structured placeholders while
preserving all agent reasoning text verbatim.

**Design principle:** Mechanical substitution, not intelligent compression.
Replacing an old grep result with a placeholder requires no judgment. Masking
operates forward -- Eva controls what she carries into state files and
invocations, not backward (Claude Code's conversation history is append-only).

### Never Mask (Preserved Verbatim)

1. All agent reasoning, analysis, decisions, and conclusions -- any text an
   agent produced as output (not tool output). Test: did an LLM produce it
   (never mask) or did a tool produce it (maskable)?
2. The most recent instance of each unique file read (keyed by file path)
3. The most recent Bash output for each distinct command
4. The most recent Grep result for each distinct query
5. Any tool output referenced in an active BLOCKER or MUST-FIX finding
6. Content of `pipeline-state.md` and `context-brief.md` (always-live state)
7. Telemetry accumulators in PIPELINE_STATUS (`telemetry_total_invocations`,
   `telemetry_total_cost_usd`, `telemetry_rework_by_unit`) -- always-live state,
   already covered by the pipeline-state.md rule above

### Mask (Replace with Placeholder)

1. File read outputs superseded by a more recent read of the same path
2. Tool outputs from completed pipeline phases (e.g., Robert's spec exploration
   outputs after Cal has the ADR)
3. Verbose Bash outputs (build logs, test suite outputs) after Eva has
   extracted the verdict
4. Git diff outputs after Roz and Poirot have completed their review of that
   unit
5. Individual Tier 1 `agent_capture` responses after Eva has updated the
   telemetry accumulators (the brain response confirmation is transient)

### Placeholder Format

```
[masked: {tool} {target}, {size} lines, turn {N}. Re-read: {recovery_command}]
```

Examples:

- `[masked: Read source/rules/agent-system.md, 482 lines, turn 3. Re-read: Read source/rules/agent-system.md]`
- `[masked: Bash npm test, 147 lines, turn 12. Re-read: run test suite again]`
- `[masked: Grep "Distillator" source/, 35 matches, turn 5. Re-read: Grep "Distillator" source/]`

### Trigger Points (Mechanical -- Not Discretionary)

Eva applies masking at these four trigger points:

1. **Before each subagent invocation:** Mask all tool outputs from prior
   phases that are not in the current invocation's READ list.
2. **After processing a subagent's return:** Mask the invocation prompt and
   raw return output, preserving only the structured verdict (PASS/FAIL,
   findings list, DoD).
3. **After each phase transition:** Mask all tool outputs from the completed
   phase.
4. **When Eva's context cleanup advisory fires** (visible response degradation
   or 20+ agent handoffs): Apply aggressive masking -- preserve only
   pipeline-state.md content, context-brief.md, and the current phase's
   active tool outputs.

Telemetry: Log "Masking [N] observations from phase [phase]" at each trigger
point. Absence of this log line means masking is being skipped.

### Brain Integration (when `brain_available: true`)

Before masking a tool output that informed a decision, Eva captures a summary:

- Call `agent_capture` with `thought_type: 'observation'`, `source_agent: 'eva'`
- Content: one-line summary of what was learned from the output
- Metadata: `{ masked_at_turn: N, original_tool: 'Read', target: 'path/to/file' }`

This makes masked observations recoverable via `agent_search` in future
sessions (query by `thought_type: 'observation'` or by file path).

Telemetry: `agent_capture` calls with `thought_type: 'observation'` per
pipeline. Absence when brain is available means brain integration for masking
is not firing.

### Recovery (when `brain_available: false` or observation not captured)

Use the placeholder's recovery command to re-read the original content:

- `[masked: Read source/foo.md, 120 lines, turn 4. Re-read: Read source/foo.md]`
  -> Re-read: `Read source/foo.md`
- `[masked: Grep "pattern" src/, 22 matches, turn 7. Re-read: Grep "pattern" src/]`
  -> Re-read: run the Grep again

Recovery is always possible. Masking is never irreversible data loss.

</protocol>
