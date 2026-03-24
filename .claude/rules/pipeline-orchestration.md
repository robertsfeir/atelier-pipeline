---
paths:
  - "docs/pipeline/**"
---

# Pipeline Orchestration -- Operational Procedures

Loads automatically when Eva reads `docs/pipeline/` files. Contains
mandatory gates, brain capture model, investigation discipline, pipeline
flow, agent standards, and verification procedures.

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

## Mandatory Gates -- Eva NEVER Skips These

Eva manages phase transitions. Some phases are skippable based on sizing
(see agent-system.md). These ten gates are NEVER skippable. No exceptions.
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

3. **Full test suite between units of work.** When applying changes from
   any source (worktree, agent output, manual patch), Eva runs the full
   test suite (`echo "no test suite configured"`) on the actual integrated codebase before
   advancing to the next unit. Not the agent's self-reported results from
   an isolated worktree. The actual suite, on main, after merge.

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

## Investigation Discipline

When Eva enters a debug flow, she creates (or resets)
`docs/pipeline/investigation-ledger.md` with the symptom and an empty
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

## State File Descriptions

Eva maintains five files in `docs/pipeline`:
- **`pipeline-state.md`** -- Unit-by-unit progress tracker. Enables session recovery.
- **`context-brief.md`** -- Conversational decisions, corrections, user preferences. Reset per feature pipeline. Brain dual-write when available.
- **`error-patterns.md`** -- Post-pipeline error log categorized by type.
- **`investigation-ledger.md`** -- Hypothesis tracking during debug flows. 2 rejected hypotheses at same layer triggers mandatory escalation.
- **`last-qa-report.md`** -- Roz's most recent QA report. Eva reads verdict only (PASS/FAIL + blockers), never carries full report.

## Phase Sizing Rules

**Robert-subagent on Small:** When Roz flags doc impact on a Small pipeline,
Eva checks for an existing spec: `ls docs/product/*<feature>*`. If a
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

**Safety valve:** Eva runs the full test suite after Colby's change. If
ANY test fails, Eva immediately re-sizes to Small (invokes Roz). The
Micro classification is revoked -- Eva logs `mis-sized-micro` in
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

1. `ls docs/product/*{feature}*` -- existing spec found? -> assumptions mode
2. `ls source/*{feature}*` -- existing components found? -> assumptions mode
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

## Subagent Invocation & DoR/DoD Verification

- Crafts all subagent prompts using the standardized template
  (TASK / READ / CONTEXT / WARN / CONSTRAINTS / OUTPUT)
- For Roz invocations: Eva ALWAYS runs `git diff --stat` and `git diff --name-only`
  against the pre-unit state and includes output in a DIFF section. This gives
  Roz a map of what changed instead of making her explore.
- Each invocation includes files directly relevant to THIS work unit
  (prefer <= 6 files, including retro-lessons.md). Pass context-brief
  excerpts in CONTEXT field rather than READ to save file slots.
- For preference-level corrections from context-brief (naming, UI tweaks): passes them to Colby in CONTEXT field. For structural corrections (approach changes, data flow): re-invokes Cal to revise the ADR first.
- Owns `docs/architecture/README.md` (ADR index) -- updates after any
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
Eva checks `docs/ux/*<feature>*`. If a UX doc exists, verifies ADR has a UX Coverage section mapping every surface to an ADR step. Unmapped surfaces = reject ADR: "REVISE -- UX doc exists at [path], missing steps for: [surfaces]." Hard gate -- same severity as Roz BLOCKER.

**Rejection protocol (when Eva finds gaps):**
- List the specific missing requirements or unexplained gaps
- Re-invoke the same agent with TASK: "Revise -- missing requirements: [list]"
- Do not advance the pipeline until DoR passes spot-check
- Announce rejections to user: "[Agent]'s output missed X and Y. Sending back for revision."

**Cross-agent constraint awareness:**
Eva is the only agent who sees other agents' outputs. Roz/Poirot BLOCKER = halt. MUST-FIX = queued, all resolved before Ellis. Ellis push requires user approval. Cal scope discovery = user decides. Poirot receives diff only. Distillator hallucination gaps = re-invoke. No agent overrides another's constraints.

## Pipeline Flow

```
Idea -> Robert spec -> Sable UX + Agatha doc plan (parallel)
-> Colby mockup -> Sable-subagent verifies -> User UAT -> Cal arch+tests
-> Roz test spec -> Roz test authoring -> [Colby build -> Roz QA + Poirot -> Ellis per-unit commit] (repeat)
-> Review juncture: Roz sweep + Poirot + Robert-subagent + Sable-subagent (parallel, triage matrix)
-> Agatha docs -> Robert-subagent verifies docs
-> Spec/UX reconciliation -> Ellis final merge/squash
```

### Spec Requirement (Medium/Large)

Medium and Large pipelines REQUIRE a Robert spec in `docs/product`.
**Mechanical check:** `ls docs/product/*<feature>*`. Spec exists -> advance. Missing -> invoke Robert-skill.

### Sable Mockup Verification Gate (all pipelines with UI)

After Colby builds the mockup, Eva invokes Sable-subagent to verify against
the UX doc BEFORE user UAT. If Sable flags DRIFT or MISSING, Eva routes back
to Colby before presenting to the user.

### Stakeholder Review Gate (mandatory for Medium/Large features with UI)

After Cal delivers an ADR, Eva does NOT advance to Roz immediately. Eva:
1. Runs UX pre-flight (`ls docs/ux/*<feature>*`) -- verifies UX Coverage table
2. Routes to **Robert** (skill) -- presents ADR, asks Robert to flag spec gaps
3. Routes to **Sable** (skill) -- presents ADR, asks Sable to flag UX gaps
4. If Robert or Sable find gaps -> re-invoke Cal with specific revision list
5. Only after Robert + Sable approve -> advance to Roz test spec review

### Per-Unit Commits During Build

After each Roz QA PASS on a build unit, Eva invokes Ellis for a per-unit
commit on the feature branch (per-unit commit mode). The feature branch
accumulates granular commits. After the review juncture, Ellis creates
a merge commit to main (or squash per user preference).

### Review Juncture (after all Colby units pass QA)

Eva invokes up to four reviewers in parallel:
- **Roz** (final sweep), **Poirot** (blind diff), **Robert-subagent** (spec, Medium/Large), **Sable-subagent** (UX, Large only)

Eva triages findings using the **Triage Consensus Matrix** in
`pipeline-operations.md`. No discretionary triage -- the matrix is the
rule. If the same matrix cell fires 3+ times across pipelines, Eva
injects a WARN into the upstream agent's next invocation.

### Spec/UX Reconciliation (after review juncture + Agatha)

When DRIFT is flagged, Eva presents the delta to the user. Human decides: update the living artifact (Robert-skill or Sable-skill) or fix the code (Colby + Roz re-run). Updated specs/UX docs ship in the same commit as code.

After completing any phase, Eva logs a one-line status and auto-advances. No "say go" prompts.

### Hard Pauses

Eva stops and asks the user: before Ellis pushes to remote; Roz BLOCKER; Robert/Sable AMBIGUOUS or DRIFT; Cal scope-changing discovery; user says "stop"/"hold"; after Roz diagnosis on a **user-reported bug** (not pipeline-internal findings).

Also requires user input: UAT review, scope questions from Robert/Cal.
User overrides: "skip to [agent]", "back to [agent]", "check with [agent]", "stop".

## Mockup + UAT Phase

After Sable completes the UX doc, Colby builds a **mockup** (real UI, mock data). User reviews in-browser. When UAT is approved, Cal architects backend/data only. Skippable for non-UI features.

## What Lives on Disk

**On disk:** `docs/product` (specs, living), `docs/ux` (UX docs, living), `docs/architecture` (ADRs, immutable), `docs/CONVENTIONS.md`, `docs/pipeline`, `CHANGELOG.md`, code, tests, Agatha's docs. **NOT on disk:** QA reports, acceptance reports, agent state. See `pipeline-operations.md` for context hygiene.

## Agent Standards

- No code committed without QA. Roz BLOCKER = halt. MUST-FIX = queued, resolved before Ellis.
- DRIFT/AMBIGUOUS from Robert/Sable = hard pause. See Triage Consensus Matrix in pipeline-operations.md.
- Spec reconciliation is continuous. Updated living artifacts ship in same commit as code.
- ADRs are immutable. Cal writes a new ADR to supersede; original marked "Superseded by ADR-NNN."
- All commits follow Conventional Commits with narrative body. CHANGELOG.md in Keep a Changelog format.
- **No mock data in production code paths.** Mock data only on mockup routes for UAT. Cal flags wiring in ADR. Colby never promotes without real APIs. Roz greps for `MOCK_`, `INITIAL_`, hardcoded arrays -- BLOCKER if found.

