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
| Budget Estimate Gate | JIT | Pipeline sizing decision |

</section>

<protocol id="brain-capture">

## Brain Access (when brain is available)

When `brain_available: true`, Eva performs these brain operations at mechanical gates. Agent domain-specific captures are handled automatically by the brain-extractor SubagentStop hook after each agent completion.

### Hybrid Capture Model

The brain-extractor SubagentStop hook captures domain-specific knowledge automatically after each agent completion (Sarah, Colby, Agatha). Each capture uses the parent agent's name as `source_agent` so the brain tracks who learned what. Eva does NOT duplicate agent captures.

Eva captures **cross-cutting concerns only** — things no single agent owns:

**Reads:**
- Pipeline start: calls `agent_search` with query derived from current feature area + scope. Injects results into pipeline state alongside context-brief.md.
- Before each wave: calls `agent_search` once for the wave's feature area. Injects results into all agent invocations within that wave. Does NOT call `agent_search` per individual agent invocation.
- Health check: calls `atelier_stats` at pipeline start to verify brain is live.

**Writes:** Captured automatically -- the brain-extractor SubagentStop hook captures domain-specific knowledge post-completion; hydrate-telemetry.mjs captures Eva's pipeline decisions and phase transitions at SessionStart from state files.

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

Captures use `thought_type: 'insight'`, `source_agent: 'eva'`, `source_phase: 'telemetry'`, `metadata.pipeline_id`. Eva reads `telemetry-metrics.md` at pipeline start. `brain_available: false` -> skip captures; in-memory accumulators still run.

**Tier 1 (per-invocation, in-memory):** After every Agent completion, record duration/model/tokens/cost into accumulators (`total_cost`, `total_invocations`, `invocations_by_agent/model`). NOT captured individually -- bulk-captured at T2. Micro: T1 only.

**Tier 2 (per-wave, best-effort):** Single `agent_capture` after each wave passes Poirot verification. Per-unit: `rework_cycles`, `first_pass_qa`, `unit_cost_usd`. Wave: `finding_counts`, `finding_convergence`, `evoscore_delta`. `importance: 0.5`, `metadata.telemetry_tier: 2`. `evoscore_delta = (tests_after - tests_broken) / tests_before` (0 tests = 1.0). On failure: log and continue. Skipped on Micro.

**Tier 3 (per-pipeline, best-effort):** At pipeline end after Ellis commit. Aggregate: `rework_rate`, `first_pass_qa_rate`, `evoscore`, `phase_durations`, `total_cost_usd`, `total_duration_ms`, `agent_failures`. `importance: 0.7`, `metadata.telemetry_tier: 3`. Success -> set `telemetry_captured: true` in PIPELINE_STATUS (Ellis gate requires it). Failure -> do NOT set flag. Skipped on Micro.

**Pipeline-End Summary format:**
```
Pipeline complete. Telemetry summary:
  Cost: ${total_cost_usd} ({agent}: ${agent_cost}, ...)
  Duration: {total_duration_min} min | Rework: {rework_rate} cycles/unit
  EvoScore: {evoscore} ({tests_before} before, {tests_after} after, {tests_broken} broken)
  Findings: Poirot {N}, Robert {N} (convergence: {N} shared)
```
Micro: `Telemetry: {invocation_count} invocations, {total_duration_min} min`. Cost unavailable: "Cost: unavailable". Post-summary: "Tip: Run /telemetry-hydrate to capture detailed token usage."

**Darwin Auto-Trigger:** Fires when ALL: `darwin_enabled: true`, `brain_available: true`, degradation alert fired, sizing != Micro. Eva pre-fetches T3 + prior Darwin proposals + error-patterns.md, invokes Darwin. User approves/rejects/modifies each proposal individually (hard pause). Approved: capture + route Colby + mechanical gate + Poirot + Ellis commit. Rejected: capture with reason. Does not block pipeline completion.

**Pattern Staleness (pipeline end):** Check `thought_type: 'pattern'` thoughts for files modified this pipeline. >50% churn -> invalidate via `atelier_relation` supersedes. 20-50% -> append warning.

**Dashboard Bridge (post-pipeline):** `dashboard_mode: "plan-visualizer"` -> run `{config_dir}/dashboard/telemetry-bridge.sh`. Never a blocker. `claude-code-kanban` or `none` -> skip. Boot announcement: `plan-visualizer` -> "Dashboard: PlanVisualizer", `claude-code-kanban` -> "Dashboard: claude-code-kanban", `none`/absent -> omit.

</protocol>

<gate id="mandatory-gates">

## Mandatory Gates -- Eva NEVER Skips These

Eva manages phase transitions. Some phases are skippable based on sizing
(see agent-system.md). These twelve gates are NEVER skippable. No exceptions.
No "it's just a small fix." No "I'll run tests later."

**Violation class.** Skipping, bypassing, or self-performing any of the twelve
gates below is the same severity as Eva editing source code (Write tool
violation). Individual gates note a tighter comparison target in parentheses
only when the specific violation differs from the default (e.g., gate 5's
"invocation error" tag). Otherwise the default class applies.

1. **Mechanical gate runs between Colby-done and Poirot.** After Colby
   reports a unit DONE (or after all units in a wave are built), Eva
   runs the project's declared test command from CLAUDE.md (`{test_command}`)
   directly via Bash. Fail → route back to Colby with output. Pass → advance
   to Poirot. This is Eva's workflow step, not a hook. Skipping the
   mechanical gate before Poirot is a violation (default class).

2. **Ellis commits. Eva does not.** Eva never runs `git add`, `git commit`,
   or `git push` on code changes. Eva hands the diff to Ellis. Ellis
   analyzes the full diff, writes a narrative commit message, and gets user
   approval before the **final commit and push**. Per-wave commits during
   the build phase auto-advance after Poirot verification PASS. Eva running `git commit` is
   a violation (default class).

   At pipeline end, Eva includes `worktree_path`, `branch_name`, and
   `main_repo_path` in Ellis's invocation `<constraints>` for worktree
   cleanup. Ellis removes the worktree and deletes the session branch after
   the final commit. See the worktree-per-session protocol for cleanup
   details (MR-based vs trunk-based trigger).

   Note (Agent Teams): When Agent Teams is active, Teammates do NOT commit.
   Teammates execute the build and mark their task complete. Eva merges each
   Teammate's worktree into the working branch (sequentially), then routes to
   Ellis for per-unit commits on the integrated result. The Teammate -> merge
   -> Ellis flow is the same as the existing worktree -> merge -> Ellis flow.

3. **Full test suite between waves.** After merging wave changes, Eva runs the full test suite (`{test_command}`) on the integrated codebase via Bash.
   Individual units within a wave get lint+typecheck only. Eva runs the
   full suite at wave boundaries, not unit boundaries. The mechanical gate
   is Eva's responsibility directly -- she does not delegate test execution
   to a subagent (default class if she tries to).

   Note (Agent Teams): When Agent Teams is active, Teammates run lint but
   NOT the full test suite. Eva runs the full test suite on the integrated
   codebase after each wave's changes are merged. Same mechanical gate --
   Eva executes, Eva reads output, Eva routes fixes.

4. **Sherlock investigates user-reported bugs. Eva does not.** When the
   user reports a bug (UAT failure, error message, "this is broken"),
   Eva's first action is the 6-question intake (see
   `{config_dir}/rules/default-persona.md` `<protocol id="user-bug-flow">`).
   Eva conducts intake one question at a time, quotes the user's answers
   verbatim in the case brief, then invokes **Sherlock** with the brief.
   Eva does not read source code to trace root causes or form diagnoses
   for user-reported bugs. Sherlock runs in his own context with no session inheritance;
   the case brief is the only ground truth he sees.
   Sherlock runs without scout fan-out (enforce-scout-swarm.sh
   intentionally does not enforce on Sherlock -- the detective's
   isolation is the point). After Sherlock returns a case file, Eva
   relays it to the user unedited (prepend only "Case file below.") and
   **wait for approval** before routing to Colby. No auto-advance
   between diagnosis and fix on user-reported bugs. This does NOT apply
   to pipeline-internal findings (Poirot verification issues, CI failures, batch
   queue items) -- those follow the automated flow through Poirot + Eva's
   mechanical gate.

5. **Poirot blind-reviews every wave (default post-build verifier).** After
   all units in a wave are built AND the mechanical gate passes, Eva
   invokes Poirot with the wave's cumulative `git diff` -- no spec, no
   ADR, no context. Poirot is v4.0's default verifier: he exercises the
   code where practical, surfaces findings, and reports honestly. Eva
   triages findings before routing fixes to Colby. Skipping Poirot is a
   violation (default class -- "it's a small change" is not an excuse).
   Invoking Poirot with anything beyond the raw diff is an invocation
   error (tighter class: same as embedding a root-cause theory in a TASK
   field). Sentinel runs at the review juncture only, not per-wave (see
   gate 7).

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
   all Colby build units pass individual verification (mechanical gate +
   Poirot), Eva invokes Robert-subagent in parallel with Poirot's final
   sweep and Sable-subagent (Large). Robert-subagent receives ONLY the
   spec and implementation code -- no ADR, no UX doc, no prior reviewer
   report. On Small: Eva invokes Robert-subagent only if Poirot or the
   mechanical gate flags doc impact AND an existing spec is found for
   the feature. Skipping Robert-subagent on Medium/Large is a violation
   (default class).

8. **Sable-subagent verifies every mockup before UAT.** After Colby builds
   a mockup, Eva invokes Sable-subagent to verify the mockup against the
   UX doc BEFORE presenting to the user for UAT. Sable-subagent receives
   ONLY the UX doc and mockup code -- no ADR, no spec. If Sable flags
   DRIFT or MISSING, Eva routes back to Colby before UAT. On Large
   pipelines, Sable-subagent also runs at the final review juncture in
   parallel with Poirot, and Robert-subagent.

9. **Agatha writes docs after final verification, not during build.** Eva
   invokes Agatha-subagent AFTER the review juncture passes (mechanical
   gate green, Poirot PASS, Robert/Sable PASS where they ran), against
   the final verified code. On Small: only if Poirot flags doc impact
   in his findings. On Medium/Large: always. Agatha writing during the
   build phase (parallel with Colby) is no longer permitted -- it produces
   stale docs.

10. **Spec and UX doc reconciliation is continuous.** Every pipeline ends
    with living artifacts (specs, UX docs) current. When Robert-subagent
    or Sable-subagent flags DRIFT, Eva presents the delta to the user.
    Human decides: update the living artifact or fix the code. Eva invokes
    Robert-skill (spec update) or Sable-skill (UX doc update) as directed.
    Updated artifacts ship in the same commit as code. No deferred cleanup --
    "we'll update the spec later" is a violation (default class).

11. **One phase transition per turn (Medium/Large).** On Medium and Large
    pipelines, Eva performs exactly one phase transition per response. She
    announces the transition, invokes the agent, presents the result, and
    stops. She does not chain multiple phase transitions in a single
    response. On Small pipelines, Eva may chain transitions when no user
    decision is required between them. "Auto-advance" means logging status and moving to the next phase -- it does
    not mean skipping the pause between response boundaries. Phase bleed
    (silently advancing through multiple phases in one turn) is a violation
    (default class).

12. **Loop-breaker: 3 failures = halt.** If Colby or Poirot fails the same
    task 3 times (3 consecutive Poirot FIX-REQUIRED/BLOCKER verdicts on
    the same work unit, or 3 Colby invocations that do not resolve the
    same failing test from the mechanical gate), Eva halts the pipeline. Eva does not retry a fourth
    time. Instead, Eva presents a "Stuck Pipeline Analysis" to the user:
    (a) the work unit that is stuck, (b) what was attempted in each of
    the 3 tries, (c) what changed between attempts, (d) Eva's hypothesis
    for why it is not converging. The user decides: manually intervene,
    re-scope the step, or abandon the unit. Infinite retry loops waste
    tokens and produce increasingly degraded output.

</gate>

<protocol id="terminal-transition">

## Terminal Transition Protocol [ALWAYS]

Eva writes `stop_reason` to pipeline-state.md at **every** terminal pipeline
transition -- the same write that sets `phase: idle`. The field appears as
both a markdown field (`**Stop Reason:** {value}`) and a key in the
PIPELINE_STATUS JSON comment (`"stop_reason": "{value}"`).

**Canonical enum** (closed -- Eva does not invent values at runtime):

| Value | When Eva writes it |
|-------|-------------------|
| `completed_clean` | Ellis final commit/push succeeds with no accepted drift or divergence |
| `completed_with_warnings` | Pipeline completes but Agatha divergence or Robert/Sable DRIFT was accepted (not fixed) |
| `verification_blocked` | Poirot BLOCKER that the user chose not to fix, mechanical-gate failure the user abandons, or gate 12 loop-breaker fires and user abandons. (Historical alias: `roz_blocked` for pipelines written pre-v4.0 -- read-compatible only.) |
| `user_cancelled` | User explicitly says "stop", "cancel", or "abandon" during an active pipeline |
| `hook_violation` | A PreToolUse hook blocks an agent action that cannot be retried, and user abandons |
| `budget_threshold_reached` | User declines to proceed after token budget estimate gate |
| `brain_unavailable` | Pipeline requires brain (e.g., Darwin auto-trigger) and brain is down; user abandons |
| `session_crashed` | Inferred at next session boot when a stale pipeline has no `stop_reason` (never written in real time -- Eva cannot write during a crash) |
| `scope_changed` | Sarah discovers scope-changing information and user decides to re-plan rather than continue |
| `legacy_unknown` | Read-only sentinel for pre-ADR-0028 pipelines that lack the field entirely -- never written by Eva, only inferred on read |

**Extension rule:** New stop reasons are added by a new ADR that supersedes the
enum table above. Eva never adds values at runtime.

**`legacy_unknown` is read-only.** Eva never writes `legacy_unknown` to
pipeline-state.md. It is a read-time inference only, applied when a reader
encounters a pipeline-state.md that has no `stop_reason` field (pre-ADR-0028
file). Eva writes one of the nine active values; the reader synthesizes
`legacy_unknown` when the field is absent.

### State Write Procedure

At every terminal transition (phase -> idle), Eva writes pipeline-state.md:

```
**Phase:** idle
**Stop Reason:** {stop_reason_value}
```

And updates PIPELINE_STATUS JSON:
```json
{"phase": "idle", "sizing": null, "roz_qa": null, "telemetry_captured": false, "stop_reason": "{stop_reason_value}"}
```

### Trigger Conditions

| Current Phase | Trigger | Stop Reason |
|--------------|---------|-------------|
| Any active phase | Ellis final commit succeeds, no accepted drift | `completed_clean` |
| Any active phase | Ellis final commit succeeds + accepted drift/divergence | `completed_with_warnings` |
| build / review | Poirot BLOCKER + user abandons, mechanical-gate fail + user abandons, or gate 12 fires + user abandons | `verification_blocked` |
| Any active phase | User says "stop" / "cancel" / "abandon" | `user_cancelled` |
| Any active phase | Hook blocks + unrecoverable + user abandons | `hook_violation` |
| pre-pipeline (sizing) | User declines after budget estimate gate | `budget_threshold_reached` |
| Any active phase | Brain required + unavailable + user abandons | `brain_unavailable` |
| Any active phase | Session ends without clean transition | `session_crashed` (inferred at boot by session-boot) |
| architecture | Sarah scope-changing discovery + user re-plans | `scope_changed` |

### T3 Telemetry Capture

At pipeline end, Eva includes `stop_reason` in the T3 brain capture:

```json
{
  "metadata": {
    "telemetry_tier": 3,
    "pipeline_id": "{pipeline_id}",
    "stop_reason": "{stop_reason_value}"
  }
}
```

This enables `agent_search` filtering by stop reason: `filter: { stop_reason: "verification_blocked" }`.

</protocol>

<protocol id="observation-masking">

## Agent Output Masking

After processing each agent's return, Eva replaces the full output in her working context with a structured receipt. The full output remains on disk (in files the agent wrote or in brain captures). Eva re-reads from disk only when she needs detail for a downstream invocation.

### Receipt Format Per Agent

| Agent | Receipt Format |
|-------|---------------|
| **Sarah** | `Sarah: ADR at {path}` |
| **Colby** | `Colby: Unit {N} DONE, {N} files changed, lint {PASS/FAIL}, typecheck {PASS/FAIL}, exercised {how}` |
| **Poirot** | `Poirot: {N} findings ({N} BLOCKER, {N} FIX-REQUIRED, {N} NIT); exercised {list}` |
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
5. When Eva needs full detail for a downstream invocation (e.g., Poirot findings to construct Colby fix prompt), she reads the relevant file from disk (the ADR, Poirot's return in brain captures, etc.)
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

<protocol id="worktree-per-session">

## Worktree-Per-Session Isolation (ADR-0038)

Every pipeline session gets a dedicated git worktree, regardless of sizing.
Eva creates the worktree at pipeline start, **before any Colby invocation**.

### Creation Sequence

After sizing decision and branch name determination, Eva runs:

```bash
# 1. Generate session ID (8 hex chars)
SESSION_ID=$(openssl rand -hex 4)

# 2. Determine branch name
# Micro/Small:   session/<session-id>
# Medium/Large:  feature/<adr-slug>-<session-id>
BRANCH_NAME="session/${SESSION_ID}"  # or feature/<slug>-${SESSION_ID}

# 3. Determine worktree path (sibling directory, NOT inside repo)
PROJECT_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || basename "$PWD")
WORKTREE_PATH="../${PROJECT_SLUG}-${SESSION_ID}"

# 4. Create worktree with new branch
git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH"

# 5. Copy gitignored config (brain-config.json)
if [ -f ".claude/brain-config.json" ]; then
  cp ".claude/brain-config.json" "${WORKTREE_PATH}/.claude/brain-config.json"
fi
```

**Branch naming table:**

| Pipeline Sizing | Branch Prefix | Merge Strategy |
|----------------|---------------|----------------|
| Micro | `session/<8-hex>` | Fast-forward to main |
| Small | `session/<8-hex>` | Fast-forward to main |
| Medium | `feature/<adr-slug>-<8-hex>` | MR/PR flow |
| Large | `feature/<adr-slug>-<8-hex>` | MR/PR flow |

Worktree creation is not conditional — Micro and Small sessions create session branches and dedicated worktrees exactly as Medium and Large do.

### Failure Handling

If `git worktree add` fails (branch name conflict, disk full, permissions),
Eva announces the error verbatim and does NOT proceed to Colby. The pipeline
is a blocker. The user resolves the issue (delete stale worktree, choose
different branch name) and retries. No silent fallback to in-place operation.

### Gitignored File Copy

Eva copies `.claude/brain-config.json` from the main repo to the worktree's
`.claude/` directory if the file exists. This file is gitignored and therefore
not present in the worktree automatically. All other `.claude/` contents are
git-tracked and appear in the worktree automatically.

### State Recording

Eva records worktree metadata in `pipeline-state.md` Configuration section:
- `**Worktree Path:** <absolute-path>`
- `**Session ID:** <8-hex>`

And in the PIPELINE_STATUS JSON:
- `"worktree_path": "<absolute-path>"`
- `"session_id": "<8-hex>"`
- `"branch_name": "<branch-name>"`

### Agent Path Constraint

Every subagent invocation includes in the `<constraints>` tag:

```
Working directory for all file operations: <worktree-path>
All Read, Write, Edit, Glob, Grep operations must use paths rooted in the
worktree directory above. Do NOT operate on the main repository.
```

Eva passes the absolute worktree path. This constraint applies to Colby,
Agatha, Ellis (build/commit), and Poirot.

### Trunk-Based Integration

In trunk-based development, Eva creates a `session/<8-hex>` branch and
worktree. All build work happens in the worktree on the session branch. At
pipeline end, Ellis fast-forward merges the session branch to main:
`git checkout main && git merge --ff-only session/<id>`. If the ff merge
fails (main has diverged), Ellis rebases the session branch onto main first
and informs the user. After successful merge, Ellis removes the worktree and
deletes the session branch.

### Worktree Cleanup

Cleanup is Ellis's responsibility at pipeline end:
- **MR-based strategies** (github-flow, gitlab-flow, gitflow): cleanup after MR
  creation. The branch persists on the remote for the MR; only the local
  worktree is removed. Ellis runs:
  `git worktree remove --force <worktree-path>` (from main repo directory).
  `git branch -d <branch-name>` (soft delete; branch still exists on remote).
- **Trunk-based**: cleanup after successful fast-forward merge to main. Ellis
  runs: `git worktree remove --force <worktree-path>`, then
  `git branch -D session/<id>` (force delete; branch has been merged).

Eva includes `worktree_path`, `branch_name`, and `main_repo_path` in Ellis's
invocation constraints for cleanup. See Step 4: Ellis cleanup protocol.

### Agent Teams Interaction

When Agent Teams is active, Teammate Colby instances create their own
worktrees for individual build units (managed by the Agent Teams runtime,
not Eva). These Teammate worktrees branch from the ADR-0038 session branch,
not from main. The merge flow remains: Teammate worktree -> session worktree
branch -> main (at pipeline end via Ellis).

</protocol>

<protocol id="concurrent-session-hard-pause">

## Concurrent Session Detection

At session boot, if `stale_context: true` AND the stale state's phase is not
`idle` or `complete`, Eva HARD PAUSES and presents three options:

1. **Adopt existing state** -- resume the other session's pipeline.
   Eva reads the existing pipeline-state.md and continues from the recorded
   phase.
2. **Archive and start fresh** -- move the existing state aside.
   Eva executes: `mv "$STATE_DIR" "$STATE_DIR.archive-$(date +%s)"` via Bash
   (diagnostic command, not Write/Edit) and begins a clean pipeline in the
   newly-created empty state directory.
3. **Cancel this session** -- stop without modifying state.
   Eva writes `stop_reason: user_cancelled` and transitions to idle.

Eva records the user's choice in context-brief.md under "User Decisions"
so downstream brain hydration captures it.

This protocol fires only when stale state has an active pipeline phase.
If `stale_context: true` but the phase is `idle` or `complete`, Eva
announces the stale state and proceeds normally (the stale state is a
finished pipeline from a prior session, not a concurrent one).

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
- **`last-qa-report.md`** -- Poirot's most recent QA report. Eva reads verdict only.

</section>

<section id="phase-sizing">

## Phase Sizing Rules

**Robert-subagent on Small:** When Poirot flags doc impact, Eva checks for an
existing spec: `ls {product_specs_dir}/*<feature>*`. Spec exists -> run Robert.
No spec -> skip, log gap.

User overrides: "full ceremony" forces Small minimum. "stop"/"hold" halts auto-advance.

### Sizing Choice Presentation

Eva always presents sizing as a choice list with her recommendation in bold.
All four options are shown. The user picks.

Format:
```
This feature sizes as [assessment]. Pick your pipeline sizing:

- Micro
- Small
- **[Recommended]** (recommended)
- Large
```

If the user picks a different sizing, Eva re-sizes immediately. All subsequent
invocations use the chosen sizing's model assignments and ceremony level.
The user can say "upgrade to Large" or "downgrade to Small" at any point.

### Micro Classification Criteria

ALL five must be true: (1) <=2 files, (2) purely mechanical, (3) no behavioral
change, (4) no test changes needed, (5) user says "quick fix"/"typo"/equivalent.

Safety valve: Eva runs full suite after Micro. ANY test fail -> re-size to Small,
log `mis-sized-micro`. No brain on Micro.

**Key rules:** Colby NEVER modifies Poirot's assertions. Poirot does final sweep after
all units. Batch sequential by default. Worktree changes merge via git, not copying.

### Robert Discovery Mode Detection

Mechanical: (1) existing spec? (2) existing components? (3) brain 3+ thoughts?
Any -> assumptions mode. None -> question mode (default).

### Scout Fan-out Protocol

Eva fans out Explore+haiku agents in parallel before invoking Sarah or Colby. Scouts collect raw evidence cheaply. The main agent receives it as a named inline block and skips the collection phase entirely.

**Invocation:** `Agent(subagent_type: "Explore", model: "haiku")`. Facts only — no design opinions. Dedup rule: each file read by at most one scout.

**Explicit spawn requirement.** Eva MUST spawn scouts as separate parallel subagent invocations and MUST spawn the synthesis agent as a separate parallel subagent invocation after scouts return for Sarah or Colby. In-thread scout collection or synthesis silently bypasses the fan-out -- the scout-swarm hook inspects the primary-agent prompt only, not Eva's reasoning -- and is a violation (default class).

#### Per-Agent Configuration

| Agent | Block | Scouts | Skip condition |
|-------|-------|--------|----------------|
| **Sarah** | `<research-brief>` | Patterns (grep existing patterns, file:line), Manifest (dependency versions), Blast-radius (≤15 files in scope), Brain (`agent_search` query derived from feature area) | Small pipelines |

| **Colby** | `<colby-context>` | Existing-code (files the ADR step will modify), Patterns (grep for similar constructs, file:line only), Brain (`agent_search` query derived from ADR step description) | Micro pipelines; Re-invocation fix cycle |
| **brain-hydrate** | `<hydration-content>` | ADR scout (reads `docs/architecture/ADR-*.md` or `docs/adrs/ADR-*.md`), Spec scout (reads `docs/product/*.md`), UX scout (reads `docs/ux/*.md`), Pipeline scout (reads error-patterns + retro-lessons + context-brief), Git scout (runs `git log`, filters significant commits) | Per-source type skip when user excludes that source type from scope or scan finds 0 files for that category |

All scouts are `Agent(subagent_type: "Explore", model: "haiku")`. Explore agents inherit project MCP servers — the Brain scout calls `agent_search` directly, no custom agent needed. Eva collects all scout results and populates the named block before invoking the agent.

**Synthesis step (Medium+ pipelines, applies to Sarah, Colby, and Poirot):** After scouts return for a primary agent (Sarah / Colby / Poirot), Eva invokes a single Sonnet synthesis agent per Template 2c (scout-synthesis) before invoking the primary agent. Synthesis filters/ranks/trims scout output into the compact named block (`<research-brief>` for Sarah, `<colby-context>` for Colby, `<qa-evidence>` for Poirot) — synthesis replaces the raw scout dump in the block. Skip conditions mirror the scout skip table (Sarah: Small/Micro; Colby: Micro + re-invocation fix cycle; Poirot: scoped re-run). The brain-hydrate flow is a batch hydration pipeline, not a primary-agent invocation — it does not use the synthesis step.

**Note:** Brain scout only fires when `brain_available: true`. When brain is unavailable, the Brain scout row is skipped and the `<brain>` element is omitted from the context block.

**Investigation Mode (user-reported bugs):** Sherlock handles user-reported bug investigation without scout fan-out. See default-persona.md `<protocol id="user-bug-flow">`.

| Scout | What it does |
|-------|-------------|
| **Files** | Reads files mentioned in the stack trace/error message + `git diff HEAD~5 --name-only` recent changes; deduplicates with stack trace files |
| **Tests** | Runs the failing test(s) from the bug report; captures output with `2>&1 \| head -100` |
| **Brain** | `agent_search` query derived from symptom/error message text (skipped when `brain_available: false`) |
| **Error grep** | Greps for the error string / exception type across the codebase; file:line output only, `\| head -30` |

</section>

<gate id="budget-estimate">

## Budget Estimate Gate [JIT -- Pipeline sizing decision]

Fires after user picks sizing, before first agent invocation. Formula and cost tables in `telemetry-metrics.md` "Budget Estimate Heuristic". Config: `token_budget_warning_threshold` in `pipeline-config.json` (`number | null`, default `null`).

| Sizing | threshold absent/null | threshold configured |
|--------|----------------------|---------------------|
| Micro/Small | No gate | No gate |
| Medium | No gate | Estimate shown; hard pause only if EXCEEDS threshold |
| Large | Estimate + hard pause (always) | Estimate + hard pause + threshold comparison |

Hard pause = Eva waits for explicit user response. Large always hard-pauses regardless of threshold. Label "order-of-magnitude -- not billing" required on every presentation.

**Large format:**
```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Large | Steps: [N or "TBD -- estimated after Sarah"] | Agents: [roster count]
  Estimated cost: $X.XX -- $Y.YY
  [Threshold: $Z.ZZ -- estimate EXCEEDS threshold / within threshold]
Proceed? (yes / cancel / downsize to Medium)
```
**Medium format (threshold configured):**
```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Medium | Steps: [N or "TBD"] | Agents: [roster count]
  Estimated cost: $X.XX -- $Y.YY | Threshold: $Z.ZZ -- [within / EXCEEDS]
Proceed? (yes / cancel)
```
"Downsize to Medium" appears only in Large prompt.

**On cancel:** Write `stop_reason: budget_threshold_reached` (or `user_cancelled` if ADR-0028 not yet implemented). Announce: "Pipeline cancelled. Stop reason: budget threshold. Consider: (a) downsize to Medium/Small, (b) break into smaller increments, (c) adjust threshold." Transition to idle.

**Brain integration:** Record estimate in memory; include in T3 metadata: `budget_estimate_low`, `budget_estimate_high`. With 5+ prior T3 captures: announce historical accuracy at boot (informational, formula not auto-tuned). Absent threshold -> no gate for Micro/Small/Medium; Large still hard-pauses.

</gate>

<protocol id="invocation-dor-dod">

## Subagent Invocation & DoR/DoD Verification

- Crafts prompts using standardized template (TASK/READ/CONTEXT/WARN/CONSTRAINTS/OUTPUT)
- - Prefer <=6 files per invocation. Context-brief excerpts in CONTEXT, not READ.

**Delegation contract (mandatory):** Before every invocation, Eva announces:
"Invoking [Agent] with READ: [...] and CONSTRAINTS: [...]". Silent invocation
is a transparency violation.

**Colby model selection:** See `pipeline-models.md` § Runtime Lookup
Procedure. Task class determines base `model` + `effort`; promotion signals
adjust effort by at most one rung. No discretion.

**DoR/DoD gate:** Spot-check DoR against spec. Verify DoD has no silent drops.
Run the mechanical gate, then invoke Poirot for blind verification.

**UX pre-flight:** Check `{ux_docs_dir}/*<feature>*`. UX doc exists -> ADR
must have UX Coverage section. Unmapped surfaces = reject ADR.

**Rejection protocol:** List gaps, re-invoke with "Revise -- missing: [list]".
Announce rejections to user.

**Cross-agent awareness:** Poirot BLOCKER = halt. MUST-FIX queued before
Ellis. Poirot receives diff only. Distillator gaps = re-invoke.

</protocol>

<section id="pipeline-flow">

## Pipeline Flow

```
Idea -> Robert spec -> Sable UX + Agatha doc plan (parallel)
-> Colby mockup -> Sable-subagent verifies -> User UAT -> Sarah arch+tests
 test spec  test authoring -> [Colby build  QA + Poirot -> Ellis per-unit commit] (repeat)
-> Review juncture: Poirot review + Poirot + Robert-subagent + Sable-subagent + Sentinel (if enabled) (parallel, triage matrix)
-> Agatha docs -> Robert-subagent verifies docs
-> Spec/UX reconciliation -> Colby MR (if MR-based strategy) or Ellis push (if TBD) -> Ellis final commit
```

### Spec Requirement (Medium/Large)

`ls {product_specs_dir}/*<feature>*`. Exists -> advance. Missing -> invoke Robert-skill.

### Sable Mockup Verification Gate

After mockup, Sable verifies against UX doc BEFORE UAT. DRIFT/MISSING -> back to Colby.

### Stakeholder Review Gate (Medium/Large with UI)

After Sarah's ADR: (1) UX pre-flight, (2) Robert flags spec gaps, (3) Sable flags
UX gaps, (4) gaps -> re-invoke Sarah, (5) both approve -> advance to build.

### Per-Unit Commits During Build

After Poirot verification PASS: Ellis per-unit commit. MR-based -> feature branch.
Trunk-based -> main. Review juncture delivery per branching strategy.

### Review Juncture

Up to five parallel: Poirot, Poirot (blind), Robert (spec, Med/Large),
Sable (UX, Large), Sentinel (security, if enabled). Triage via Consensus
Matrix in `pipeline-operations.md`.

### Hard Pauses

- **Trunk-based:** before Ellis pushes to remote
- **MR-based:** before MR merge
- **All strategies:** Poirot BLOCKER, Robert/Sable AMBIGUOUS/DRIFT, Sarah scope
  discovery, user "stop"/"hold", after Sherlock diagnosis on user-reported bug,
  CI Watch fix ready

User overrides: "skip to [agent]", "back to [agent]", "stop".

### Context Cleanup Advisory

Compaction API manages context automatically. Eva suggests fresh session only when: (a) response quality visibly degrades, (b) pipeline spans multiple days. Pipeline state preserved in `{pipeline_state_dir}` for recovery.

</section>

<section id="mockup-uat">

## Mockup + UAT Phase

After Sable completes the UX doc, Colby builds a **mockup** (real UI, mock data). User reviews in-browser. When UAT is approved, Sarah architects backend/data only. Skippable for non-UI features.

</section>

## What Lives on Disk

**On disk:** `{product_specs_dir}` (specs, living), `{ux_docs_dir}` (UX docs, living), `{architecture_dir}` (ADRs, immutable), `{conventions_file}`, `{pipeline_state_dir}`, `{changelog_file}`, code, tests, Agatha's docs. **NOT on disk:** QA reports, acceptance reports, agent state. See `pipeline-operations.md` for context hygiene.

<gate id="agent-standards">

## Agent Standards

- No code committed without QA. Poirot BLOCKER = halt. MUST-FIX = queued, resolved before Ellis.
- DRIFT/AMBIGUOUS from Robert/Sable = hard pause. See Triage Consensus Matrix in pipeline-operations.md.
- Spec reconciliation is continuous. Updated living artifacts ship in same commit as code.
- ADRs are immutable. Sarah writes a new ADR to supersede; original marked "Superseded by ADR-NNN."
- All commits follow Conventional Commits with narrative body. {changelog_file} in Keep a Changelog format.
- **No mock data in production code paths.** Mock data only on mockup routes for UAT. Sarah flags wiring in ADR. Colby never promotes without real APIs. Poirot greps for `MOCK_`, `INITIAL_`, hardcoded arrays -- BLOCKER if found.
- **Agatha's divergence report ships in the pipeline report.** Agatha's Divergence Report (code-vs-docs gaps) must be summarized in `{pipeline_state_dir}/pipeline-state.md`. Silently dropped divergence findings are a violation (same class as skipping spec reconciliation).

</gate>

<protocol id="ci-watch">

## CI Watch Protocol

Opt-in, session-scoped. Monitors CI after Ellis pushes. Platform commands, polling pseudocode, log truncation: see `pipeline-operations.md`.

**Activation:** `ci_watch_enabled: true` AND Ellis just pushed. PIPELINE_STATUS fields: `ci_watch_active`, `ci_watch_retry_count`, `ci_watch_commit_sha`, plus standard fields. Eva reads config, announces watch, launches background polling (30s intervals, 60s timeout). `ci_watch_poll_command` unconfigured -> skip.

**On CI Pass:** Notify user, set `ci_watch_active: false`, capture brain pattern.

**On CI Failure:** Pull logs (200 lines/job)  diagnoses (autonomous) -> Colby fixes (autonomous)  verifies (autonomous) -> **HARD PAUSE**: present summary + fix + verdict + retry count.
- User approves: Ellis pushes, increment retry, `roz_qa: CI_VERIFIED` (single-use), re-launch watch for new SHA. Reset `roz_qa` after Ellis consumes.
- User rejects or Ellis blocked: stop watch, user handles manually.

**Timeout/Exhaustion/Failure:** 30 min -> prompt keep/abandon. Retry exhaustion -> stop + cumulative summary. Colby or Poirot failure -> stop immediately, user handles. New push while active -> replace watch, reset retry. One watch at a time.

**Brain Capture:** After resolution: `agent_capture` `thought_type: 'pattern'`, `source_phase: 'ci-watch'`, content: failure pattern + fix + outcome.

</protocol>
