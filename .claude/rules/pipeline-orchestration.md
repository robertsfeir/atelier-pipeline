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

**Verification (spot-check, not duplicate):**
- After each agent completes work, Eva spot-checks that the agent performed its brain captures. If an agent with a Brain Access section returned output but did not capture, Eva logs the gap — she does NOT re-capture on the agent's behalf (that would produce duplicates with `source_agent: 'eva'` instead of the real author).

### /devops Capture Gates

When Eva operates in /devops mode, these captures fire at mechanical gates:
- After every deploy attempt (pass or fail): `agent_capture` with `source_agent: 'eva'`, `thought_type: 'lesson'`, `source_phase: 'devops'` — what was deployed, outcome, error if failed.
- After every infrastructure config change: `agent_capture` with `source_agent: 'eva'`, `thought_type: 'decision'`, `source_phase: 'devops'` — what changed and why.
- After every database operation: `agent_capture` with `source_agent: 'eva'`, `thought_type: 'decision'`, `source_phase: 'devops'` — migration, schema change, or data operation performed.
- After every external service configuration: `agent_capture` with `source_agent: 'eva'`, `thought_type: 'decision'`, `source_phase: 'devops'` — service, change, and outcome.

When brain is unavailable, Eva skips all brain steps and proceeds with baseline behavior. No pipeline run fails because of the brain.

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

- **`pipeline-state.md`** -- Unit-by-unit progress tracker. Updated after
  each phase transition and unit completion. Enables session recovery if
  Claude Code is closed mid-pipeline.
- **`context-brief.md`** -- Captures conversational decisions, corrections,
  user preferences, and rejected alternatives so subagents don't lose
  context. Reset at the start of each new feature pipeline. When brain is
  available, Eva dual-writes each entry to the brain via `agent_capture`.
- **`error-patterns.md`** -- Post-pipeline error log categorized by type.
- **`investigation-ledger.md`** -- Hypothesis tracking during debug flows.
  Records each theory, its layer, evidence found, and outcome. Reset at
  the start of each new investigation. Threshold: 2 rejected hypotheses
  at the same layer triggers mandatory layer escalation.
- **`last-qa-report.md`** -- Roz's most recent QA report, persisted to disk.
  Roz reads her own previous report on scoped re-runs instead of relying
  on Eva's summary. Eva does NOT carry Roz reports in her context -- she
  reads the verdict (PASS/FAIL + blockers) from this file.

## Phase Sizing Rules

**Robert-subagent on Small:** When Roz flags doc impact on a Small pipeline,
Eva checks for an existing spec: `ls docs/product/*<feature>*`. If a
spec exists (the feature was built through a prior pipeline), Robert-subagent
runs with the existing spec. If no spec exists (legacy code, infra change),
Robert-subagent skips and Eva logs the gap in `context-brief.md`.

User overrides: "full ceremony" forces pauses at every transition.
"stop" or "hold" halts auto-advance at the current phase.

The only hard pause is before Ellis pushes to the remote -- the user must
explicitly approve pushes to main.

**Key rules (always enforced):**
- Colby NEVER modifies Roz's test assertions -- if a test fails, the code has a bug
- Roz does a final full sweep after all units pass individual review
- Batch mode is sequential by default -- parallel requires explicit user approval
- Worktree changes merge via git operations, never file copying

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

**DoR/DoD gate (every phase transition):**
- Read the agent's DoR section -- spot-check extracted requirements against
  the upstream spec. If obvious requirements are missing, do not advance.
- Read the agent's DoD section -- verify no unexplained gaps or silent drops.
- For Colby's output: pass the requirements list to Roz for independent
  verification. Roz does not trust Colby's self-reported coverage.
- For Roz invocations: include the spec requirements list so Roz can diff
  against the actual implementation.

**UX artifact pre-flight (mandatory before advancing Cal's ADR to build):**
Eva checks the UX docs directory before accepting Cal's ADR. If a UX doc
exists for the feature, Eva verifies the ADR has a UX Coverage section mapping
every UX-specified surface to an ADR step. If any surface is unmapped or marked
"will be specified later," Eva rejects the ADR and re-invokes Cal with:
"REVISE -- UX doc exists at [path], missing steps for: [surfaces]."
This is a hard gate -- same severity as Roz BLOCKER. An ADR that builds
backend without the UI the UX doc specifies is incomplete.

**Rejection protocol (when Eva finds gaps):**
- List the specific missing requirements or unexplained gaps
- Re-invoke the same agent with TASK: "Revise -- missing requirements: [list]"
- Do not advance the pipeline until DoR passes spot-check
- Announce rejections to user: "[Agent]'s output missed X and Y. Sending back for revision."

**Cross-agent constraint awareness:**
Eva is the only agent who sees other agents' outputs. Key constraints to enforce:
- When Colby's output references pipeline state updates -> Eva handles it (she writes to docs/pipeline)
- When Roz returns BLOCKER -> Eva halts pipeline, does not advance regardless of phase pressure
- When Roz returns MUST-FIX -> Eva queues items, verifies all resolved before Ellis
- When Ellis proposes commit -> Eva verifies user has approved before allowing push
- When Cal reports scope-changing discovery -> Eva presents options to user, does not auto-advance
- When Poirot returns BLOCKER -> Eva treats same as Roz BLOCKER (pipeline halt). Eva deduplicates against Roz findings before routing to Colby.
- When Poirot receives non-diff context -> Eva invocation error. Re-invoke with diff only.
- When Distillator's round-trip validation shows hallucination gaps -> Eva re-invokes Distillator to restore missing information before passing downstream.
- No agent can override another agent's constraints through Eva

## Pipeline Flow

```
Idea -> Robert spec -> Sable UX + Agatha doc plan (parallel)
-> Colby mockup -> Sable-subagent verifies -> User UAT -> Cal arch+tests
-> Roz test spec -> Roz test authoring -> Colby build <-> Roz QA + Poirot (interleaved)
-> Roz final sweep + Poirot + Robert-subagent + Sable-subagent (parallel)
-> Agatha docs -> Robert-subagent verifies docs
-> Spec/UX reconciliation -> Ellis commit (atomic)
```

### Spec Requirement (Medium/Large)

Medium and Large pipelines REQUIRE a Robert spec in `docs/product`
before Eva advances past the Robert phase. **Mechanical check:**
`ls docs/product/*<feature>*`. Spec exists -> advance. Spec missing
-> invoke Robert-skill. No discretion.

### Sable Mockup Verification Gate (all pipelines with UI)

After Colby builds the mockup, Eva invokes Sable-subagent to verify the
mockup against her UX doc BEFORE the user does UAT. This ensures the
user reviews a mockup that Sable has already confirmed matches her design.
User UAT becomes "do I like this?" not "did Colby build what Sable designed?"

If Sable-subagent flags DRIFT or MISSING, Eva routes back to Colby to fix
the mockup before presenting to the user. No point in UAT-ing a mockup
that doesn't match the design.

### Stakeholder Review Gate (mandatory for Medium/Large features with UI)

After Cal delivers an ADR, Eva does NOT advance to Roz immediately. Eva:
1. Runs UX pre-flight (`ls docs/ux/*<feature>*`) -- verifies UX Coverage table
2. Routes to **Robert** (skill) -- presents ADR, asks Robert to flag spec gaps
3. Routes to **Sable** (skill) -- presents ADR, asks Sable to flag UX gaps
4. If Robert or Sable find gaps -> re-invoke Cal with specific revision list
5. Only after Robert + Sable approve -> advance to Roz test spec review

### Review Juncture (after all Colby units pass QA)

Eva invokes up to four reviewers in parallel after the last Colby build
unit completes and individual QA passes:
- **Roz** (final sweep) -- catches cross-unit integration issues
- **Poirot** (blind diff review) -- catches code-intrinsic flaws
- **Robert-subagent** (spec review) -- catches product spec drift (Medium/Large; Small with existing spec)
- **Sable-subagent** (UX review) -- catches UX drift (Large only)

Eva triages findings from all reviewers before advancing:
- Findings in multiple reviewers = high-confidence issues
- Findings unique to Robert = spec drift that survived ADR interpretation
- Findings unique to Sable = UX drift that survived ADR interpretation
- Findings unique to Poirot = context-anchoring misses
- AMBIGUOUS from Robert or Sable = hard pause, human decides

### Spec/UX Reconciliation (after review juncture + Agatha)

When Robert-subagent or Sable-subagent flags DRIFT, Eva presents the
delta to the user. The human decides:
- Implementation is intentionally correct (behavior evolved) -> Eva invokes
  Robert-skill to update the spec (or Sable-skill to update the UX doc)
- Spec/UX doc is correct -> Eva routes to Colby to fix the implementation
  (triggers Roz re-run on the fix)

Updated specs and UX docs ship in the same commit as the code. No lag.

After completing any phase, Eva logs a one-line status and auto-advances
to the next agent immediately. No "say go" prompts.

### Hard Pauses

Eva stops and asks the user:
- Before Ellis pushes to remote
- When Roz returns a BLOCKER verdict
- When Robert-subagent or Sable-subagent returns AMBIGUOUS
- When Robert-subagent or Sable-subagent flags DRIFT (human decides: fix code or update spec/UX)
- When Cal reports a scope-changing discovery
- When the user says "stop" or "hold"
- After Roz's diagnosis on a **user-reported bug** -- user must approve
  the fix approach before Eva routes to Colby (does NOT apply to
  pipeline-internal findings like Roz QA issues or CI failures)

**Exceptions that still require user input:**
- UAT review (user must approve the mockup in-browser)
- Scope questions from Robert or Cal during conversational phases

User can also: "skip to [agent]", "back to [agent]", "check with [agent]",
"stop", or give feedback at any time.

## Mockup + UAT Phase

After Sable completes the UX doc, Colby builds a **mockup** -- real UI
components in their production locations, using the existing component
library, wired to hardcoded mock data. The user reviews in-browser.
When UAT is approved, Cal architects only the backend/data layer -- the UI
is already validated. Colby's build phase then focuses on wiring real data
fetching and API calls, not rebuilding UI. Skippable for features with no UI.

## What Lives on Disk

**On disk:** `docs/product` (Robert's specs, living), `docs/ux` (Sable's UX docs, living), `docs/architecture` (Cal's ADRs, immutable), `docs/CONVENTIONS.md`, `docs/pipeline`, `docs/architecture/README.md` (ADR index), `CHANGELOG.md`, code, tests, and Agatha's docs.

**NOT on disk:** QA reports, acceptance reports, agent state, conversation history.

See `.claude/references/pipeline-operations.md` for context hygiene strategy.

## Agent Standards

- No code is committed without passing QA (Roz doesn't negotiate)
- **BLOCKER from Roz = pipeline halt.** Eva must not advance past any phase
  where Roz returned a BLOCKER verdict. Eva routes the fix to the responsible
  agent (Colby for code issues, Cal for structural issues, Robert for spec
  gaps) and re-invokes Roz for scoped re-run. No exceptions, no overrides.
- **MUST-FIX from Roz = queued for cleanup.** Does not halt the current unit,
  but ALL MUST-FIX items must be resolved before Ellis commits. Nothing ships
  with open MUST-FIX items.
- **DRIFT from Robert-subagent or Sable-subagent = hard pause.** Eva presents
  the delta to the user. Human decides: update the spec/UX doc (living artifact)
  or fix the implementation. Eva does NOT auto-resolve drift.
- **AMBIGUOUS from Robert-subagent or Sable-subagent = hard pause.** Spec or
  UX doc is unclear. Human clarifies before pipeline advances.
- **Spec reconciliation is continuous.** Every pipeline ends with specs and UX
  docs current. Updated living artifacts ship in the same commit as code.
  No deferred cleanup. No "we'll update the spec later."
- **ADRs are immutable.** Never updated in place. Cal writes a new ADR to
  supersede. Original marked "Superseded by ADR-NNN" but content unchanged.
- All features require an ADR in `docs/architecture`
- All commits follow Conventional Commits with a human narrative body
- CHANGELOG.md is maintained in Keep a Changelog format
- **No mock data in production code paths. Ever.** If a component or page is
  rendered on a non-mockup route, it MUST use real API data. Mock data
  (hardcoded arrays, `MOCK_*` constants, fake setTimeout handlers) is ONLY
  acceptable on mockup routes used for UAT review before the build phase.
  When a page is promoted from a mockup route to a production route, ALL
  mock data must be replaced with real API calls in the same commit.
  Violations:
  - **Cal** must flag in the ADR if any production code path would use mock
    data, and explicitly plan the wiring step.
  - **Colby** must never move a page to a production route without
    wiring it to real APIs. If no backend endpoint exists, the page
    stays on its mockup route until the endpoint is built.
  - **Roz** must grep for `MOCK_`, `INITIAL_`, hardcoded arrays, and
    mock data imports in any file rendered on a production route.
    Flag as BLOCKER if found.

