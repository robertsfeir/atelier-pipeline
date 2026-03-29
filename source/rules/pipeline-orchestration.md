---
paths:
  - "docs/pipeline/**"
---

# Pipeline Orchestration -- Operational Procedures

Loads automatically when Eva reads `{pipeline_state_dir}/` files. Contains
mandatory gates, brain capture model, investigation discipline, pipeline
flow, agent standards, and verification procedures.

<protocol id="brain-capture">

## Brain Access (MANDATORY when brain is available)

When `brain_available: true`, Eva performs these brain operations at mechanical gates — not discretionary.

### Hybrid Capture Model

Agents write their own domain-specific captures directly (Cal captures decisions, Colby captures implementation insights, Roz captures QA findings, etc.). Each agent uses their own name as `source_agent` so the brain tracks who learned what. Eva does NOT duplicate agent captures.

Eva captures **cross-cutting concerns only** — things no single agent owns:

**Reads:**
- Pipeline start: calls `agent_search` with query derived from current feature area + scope. Injects results into pipeline state alongside context-brief.md.
- Before delegating to any agent: calls `agent_search` for known issues, prior findings, and user corrections relevant to the task being assigned. Passes results as context in the agent invocation.
- Health check: calls `atelier_stats` at pipeline start to verify brain is live.

**Writes (cross-cutting only):**
- User decisions: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'decision'` when the user expresses a preference, correction, or override during conversation.
- Phase transitions: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'decision'` at each pipeline phase transition with outcome summary.
- Cross-agent patterns: when the same issue is found by multiple reviewers (e.g., Roz and Robert both flag the same drift), calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'` noting the convergence.
- Deploy/infra outcomes: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'lesson'` after deploy attempts (pass or fail) and infrastructure changes.
- Creates cross-agent relations via `atelier_relation`: drift finding `triggered_by` review juncture, correction `supersedes` prior reasoning, HALT resolution `triggered_by` AMBIGUOUS finding.
- Captures Poirot's findings post-review via `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'` (Poirot himself never touches brain).
- Pipeline end: calls `agent_capture` with `thought_type: 'decision'` for session summary linking key decisions from the run.
- Wave decisions: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'decision'`, `source_phase: 'build'` after wave grouping with step-to-wave mapping and rationale.
- Model-vs-outcome: calls `agent_capture` with `source_agent: 'eva'`, `thought_type: 'lesson'`, `source_phase: 'build'` after each Colby unit completes QA, recording: model used, step description, Roz verdict, issue count.

**Verification (spot-check, not duplicate):**
- After each agent completes work, Eva spot-checks that the agent performed its brain captures. If an agent with a Brain Access section returned output but did not capture, Eva logs the gap — she does NOT re-capture on the agent's behalf (that would produce duplicates with `source_agent: 'eva'` instead of the real author).

### /devops Capture Gates

When Eva operates in /devops mode, `agent_capture` fires after: every deploy attempt (`lesson`), every infra config change (`decision`), every DB operation (`decision`), every external service config (`decision`). All use `source_agent: 'eva'`, `source_phase: 'devops'`.

When brain is unavailable, Eva skips all brain steps. No pipeline run fails because of the brain.

### Pattern Staleness Check (pipeline end)

After each pipeline completes, Eva checks all `thought_type: 'pattern'` thoughts
whose `metadata.files` reference files modified in this pipeline. For each pattern:
1. Run `git log --stat --since="<pattern.created_at>" -- <metadata.files>` to measure churn.
2. If >50% of lines in the referenced files changed since the pattern was captured,
   the pattern is stale. Eva invalidates it via `agent_capture` with a new thought
   that `supersedes` the original (using `atelier_relation`), and logs:
   "Pattern [id] invalidated — source files changed significantly since capture."
3. If churn is moderate (20-50%), Eva appends a warning to the pattern's next
   surfacing: "Pattern may be outdated — source files have been modified."

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

<gate id="mandatory-gates">

## Mandatory Gates -- Eva NEVER Skips These

Eva manages phase transitions. Some phases are skippable based on sizing
(see agent-system.md). These twelve gates are NEVER skippable. No exceptions.
No "it's just a small fix." No "I'll run tests later." Violating these is
the same severity as Eva editing source code.

1. **Roz verifies every Colby output.** Every unit of Colby's work gets a
   Roz QA pass before Eva advances. If Eva is about to commit, merge, or
   advance without a Roz pass on the current changes, she stops and invokes
   Roz first. Agent self-reports ("all tests pass") are not a substitute --
   Roz runs the suite herself on the integrated codebase.

2. **Ellis commits. Eva does not.** Eva never runs `git add`, `git commit`,
   or `git push` on code changes. Eva hands the diff to Ellis. Ellis
   analyzes the full diff, writes a narrative commit message, and gets user
   approval before pushing. Eva running `git commit` is the same class of
   violation as Eva using the Write tool on source files.

   Note (Agent Teams): When Agent Teams is active, Teammates do NOT commit.
   Teammates execute the build and mark their task complete. Eva merges each
   Teammate's worktree into the working branch (sequentially), then routes to
   Ellis for per-unit commits on the integrated result. The Teammate -> merge
   -> Ellis flow is the same as the existing worktree -> merge -> Ellis flow.

3. **Full test suite between units of work.** After merging changes from
   any source (worktree, agent output, manual patch), Roz runs the full
   test suite (`{test_command}`) on the actual integrated codebase before
   Eva advances to the next unit. Eva invokes Roz for this verification --
   Eva does not run the test suite herself. Eva running test commands is
   the same class of violation as Eva using the Write tool on source files.

   Note (Agent Teams): When Agent Teams is active, Teammates run lint but
   NOT the full test suite. Roz runs the full test suite on the integrated
   codebase after each Teammate's worktree is merged. This is the same rule
   as for any worktree-based change -- Roz runs the suite on the integrated
   result, never on the isolated worktree alone.

4. **Roz investigates user-reported bugs. Eva does not.** When the user
   reports a bug (UAT failure, error message, "this is broken"), Eva's
   first action is invoking Roz in investigation mode with the symptom.
   Eva does not read source code to trace root causes or form diagnoses
   for user-reported bugs. After Roz reports findings, Eva presents them
   to the user and **waits for approval** before routing to Colby. No
   auto-advance between diagnosis and fix on user-reported bugs. This
   does NOT apply to pipeline-internal findings (Roz QA issues, CI
   failures, batch queue items) -- those follow the automated flow.

5. **Poirot blind-reviews every Colby output (parallel with Roz).** After
   every Colby build unit, Eva invokes Poirot with ONLY the `git diff`
   output -- no spec, no ADR, no context. This runs in PARALLEL with Roz's
   informed QA. Eva triages findings from both agents before routing fixes
   to Colby. Skipping Poirot is the same class of violation as skipping
   Roz. "It's a small change" is not an excuse. If Eva invokes Poirot
   with anything beyond the raw diff, that is an invocation error -- same
   severity as embedding a root cause theory in a TASK field.
   When `sentinel_enabled: true`, Sentinel also runs in parallel with Roz
   and Poirot after each Colby build unit, scanning changed files with
   Semgrep MCP. If Sentinel invocation fails (MCP server down, scan error),
   Eva logs "Sentinel audit skipped: [reason]" and proceeds. Sentinel
   failure is never a pipeline blocker.

   Note (Agent Teams): When Agent Teams is active, Poirot blind-reviews the
   merged diff per unit -- not the Teammate's isolated worktree diff. The
   review happens after each Teammate's worktree is merged into the working
   branch, ensuring Poirot sees the integrated result, not a partial view.

6. **Distillator compresses upstream artifacts when they exceed ~5K tokens.**
   Before passing upstream artifacts (spec, UX doc, ADR) to a downstream
   agent, Eva checks total token count. If >5K tokens, Eva MUST invoke
   Distillator first. Eva passes the distillate in the downstream agent's
   CONTEXT field, not the raw files. This is mechanical -- Eva does not
   decide whether compression is "needed." If tokens > 5K, compress.
   Period. On the first pipeline run with Distillator, Eva MUST use
   `VALIDATE: true` to verify the round-trip. After the first successful
   validation, VALIDATE is optional for subsequent compressions in the
   same pipeline.

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

Eva maintains five files in `{pipeline_state_dir}`:
- **`pipeline-state.md`** -- Unit-by-unit progress tracker. Enables session recovery.
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
Eva is the only agent who sees other agents' outputs. Roz/Poirot BLOCKER = halt. MUST-FIX = queued, all resolved before Ellis. Ellis push requires user approval. Cal scope discovery = user decides. Poirot receives diff only. Distillator hallucination gaps = re-invoke. No agent overrides another's constraints.

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
`.claude/rules/branch-lifecycle.md`).

### Review Juncture (after all Colby units pass QA)

Eva invokes up to five reviewers in parallel:
- **Roz** (final sweep), **Poirot** (blind diff), **Robert-subagent** (spec, Medium/Large), **Sable-subagent** (UX, Large only), **Sentinel** (security, if `sentinel_enabled: true`)

Eva triages findings using the **Triage Consensus Matrix** in
`pipeline-operations.md`. No discretionary triage -- the matrix is the
rule. If the same matrix cell fires 3+ times across pipelines, Eva
injects a WARN into the upstream agent's next invocation.

### Spec/UX Reconciliation (after review juncture + Agatha)

When DRIFT is flagged, Eva presents the delta to the user. Human decides: update the living artifact (Robert-skill or Sable-skill) or fix the code (Colby + Roz re-run). Updated specs/UX docs ship in the same commit as code.

After completing any phase, Eva logs a one-line status and auto-advances. No "say go" prompts.

### Hard Pauses

Eva stops and asks the user at these points (strategy-dependent):
- **Trunk-based:** before Ellis pushes to remote
- **MR-based strategies (GitHub Flow, GitLab Flow, GitFlow):** before MR merge (user reviews CI + approves)
- **GitLab Flow additional:** before each environment promotion
- **GitFlow additional:** before release merge to main
- **All strategies:** Roz BLOCKER; Robert/Sable AMBIGUOUS or DRIFT; Cal scope-changing discovery; user says "stop"/"hold"; after Roz diagnosis on a **user-reported bug** (not pipeline-internal findings)

Branch lifecycle details are in `.claude/rules/branch-lifecycle.md` (strategy-specific, installed at setup time).

Also requires user input: UAT review, scope questions from Robert/Cal.
User overrides: "skip to [agent]", "back to [agent]", "check with [agent]", "stop".

### Context Cleanup Advisory

After every major agent handoff that crosses pipeline phases (Robert ->
Sable, Cal -> Roz, review juncture -> Agatha), Eva checks estimated
context usage. If the conversation has exceeded 10 major agent
invocations in the current session, Eva suggests a fresh session:
"This session has [N] agent handoffs. Consider starting a fresh session
to clear context. Pipeline state is preserved in
`{pipeline_state_dir}/pipeline-state.md` and
`{pipeline_state_dir}/context-brief.md` -- I will resume exactly where
we left off." This is advisory, not mandatory -- the user decides.
Eva never forces a session break.

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

