# Pipeline Operations Reference

Eva loads this file when actively orchestrating a pipeline. It is NOT
pre-loaded into context -- Eva reads it at pipeline start and when she
needs to look up specific operational details.

## Model Selection (Mechanical -- Eva Does Not Choose)

Model assignment is determined by the agent and the pipeline sizing.
Eva sets the model parameter in every Agent tool invocation by looking
up the table below. There is no discretion, no judgment call, no
"this one feels complex enough for Opus." The table is the rule.

**Fixed-model agents (always the same, regardless of sizing):**

| Agent | Model | Rationale |
|-------|-------|-----------|
| **Roz** | Opus | QA judgment is non-negotiable. Sonnet missed bugs in past runs (see retro: Self-Reporting Bug Codification). |
| **Robert** (subagent) | Opus | Product acceptance review requires strong reasoning to diff spec intent against implementation. |
| **Sable** (subagent) | Opus | UX acceptance review requires strong reasoning to diff UX intent against implementation. |
| **Poirot** | Opus | Blind review with no context requires the strongest reasoning to find issues from a raw diff alone. |
| **Distillator** | Haiku | Mechanical compression with structured validation. No judgment required. |
| **Ellis** | Sonnet | Reads diff, writes commit message, runs git. Zero ambiguity in the task. |

**Size-dependent agents:**

| Agent | Small | Medium | Large |
|-------|-------|--------|-------|
| **Cal** | _(skipped)_ | Opus | Opus |
| **Colby** | Sonnet | Sonnet | Opus |
| **Agatha** | _(per doc type, Roz doc-impact trigger)_ | _(per doc type)_ | _(per doc type)_ |

**Agatha's model is doc-type-dependent, not size-dependent:**

| Doc type | Model | Examples |
|----------|-------|----------|
| Reference docs | Haiku | API docs, config references, setup guides, changelogs |
| Conceptual docs | Sonnet | Architecture guides, onboarding, tutorials |

**Enforcement rules:**

1. **No discretion.** Eva does not choose models. The sizing + agent
   identity determines the model mechanically. If Eva is about to invoke
   Colby on a Small pipeline with `model: "opus"`, that is a configuration
   error -- same severity class as invoking Poirot with spec context.
2. **Explicit in every invocation.** The model parameter MUST be set
   explicitly in every Agent tool invocation. No relying on defaults.
   Omitting the model parameter is a violation.
3. **Ambiguous sizing defaults UP.** If Eva has not yet confirmed the
   pipeline sizing (Small/Medium/Large), she MUST use the higher model
   tier for size-dependent agents until sizing is confirmed. Concretely:
   Colby gets Opus, Cal gets Opus. Once sizing is confirmed, subsequent
   invocations use the correct tier.
4. **Sizing changes propagate immediately.** If Eva re-sizes a pipeline
   mid-flight (e.g., Small escalates to Medium after discovering scope),
   all subsequent invocations use the new sizing's model assignments.
   Already-completed invocations are not re-run.

## Continuous QA (Interleaved Roz + Colby)

Replaces the batch model. Cal's ADR steps become work units. Roz writes
tests first, Colby implements to pass them.

**Pre-build test authoring (per unit):**
1. Eva invokes Roz in Test Authoring Mode for unit N's ADR step
2. Roz reads Cal's test spec + existing code + product spec
3. Roz writes test files with concrete assertions defining correct behavior
4. Tests are expected to fail -- they define the target state

**Build + QA interleaving:**
1. Eva invokes Colby for unit 1 with Roz's test files as the target
2. Colby implements to make Roz's tests pass (may add additional tests)
3. When Colby finishes unit 1, Eva invokes Roz for QA review AND Poirot
   for blind diff review in PARALLEL. Roz gets full context; Poirot gets
   ONLY the `git diff` output.
4. Eva triages findings from both: deduplicates, classifies severity.
   Findings unique to Poirot (missed by Roz due to context anchoring)
   get special attention. Roz writes tests for unit 2 (parallel if supported).
5. If Roz or Poirot flags an issue on unit N, Eva queues the fix. Colby
   finishes the current unit, then addresses the fix before starting the next unit
6. Eva updates `{pipeline_state_dir}/pipeline-state.md` after each unit transition

**Post-build pipeline tail (after all units pass individual QA):**
7. Eva invokes the review juncture: Roz final sweep + Poirot + Robert-subagent
   + Sable-subagent (Large) in parallel
8. Eva triages all findings, routes fixes to Colby if needed, re-runs Roz
9. Eva invokes Agatha to write/update docs against the final verified code.
   On Small: only if Roz flagged doc impact. On Medium/Large: always.
10. Eva invokes Robert-subagent in doc review mode to verify Agatha's output
11. If Robert-subagent or Sable-subagent flagged DRIFT: hard pause. Human
    decides fix code or update spec/UX. Eva invokes Robert-skill or Sable-skill
    to update living artifacts if directed.
12. Eva invokes Ellis. Code + docs + updated specs/UX ship in one atomic commit.

**Key rule:** Colby NEVER modifies Roz's test assertions. If Roz's test
fails against existing code, the code has a bug -- Colby fixes the code.

**Roz still does a final full sweep** after all units pass individual review.
This catches cross-unit integration issues that scoped reviews miss.

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

## Cross-Agent Consultation

If any agent raises a concern about another agent's domain, Eva asks the
user if they want to loop that agent back in:
- Cal questions Robert's spec -> "Want me to check with Robert on this?"
- Sable's design implies arch changes -> "Cal should weigh in. Loop him in?"
- Roz finds a spec gap -> "This traces back to the spec. Want Robert to clarify?"

## Batch Mode (Multiple Issues)

When Eva receives multiple issues, bug reports, or tasks at once, the
default execution model is **sequential with full pipeline per issue.**

1. **One issue at a time.** Each issue goes through the minimum pipeline
   (Colby -> Roz -> Ellis) or the full pipeline based on sizing. Eva does
   not start issue N+1 until issue N is committed and verified.
2. **Full test suite between issues.** After Ellis commits issue N, Eva
   runs the full test suite before starting issue N+1. If tests fail,
   Eva halts and routes the failure to the responsible agent.
3. **Parallelization requires explicit user approval** ("run these in
   parallel") AND Eva's confirmation that the issues have zero file
   overlap. If Eva cannot determine file overlap, she defaults to
   sequential.
4. **No silent reordering.** Eva processes issues in the order given
   unless she identifies a dependency that requires reordering, in
   which case she announces the change and explains why.

## Worktree Integration Rules

When agents work in isolated worktrees (git worktrees), their changes
must be integrated using git operations -- **never naive file copying.**

1. **Use `git merge` or `git cherry-pick`** to bring worktree changes
   into the working branch. Never use `cp`, `rsync`, or manual file
   copying to move files from a worktree to main. Git merge surfaces
   conflicts explicitly; file copying silently overwrites.
2. **Resolve conflicts before advancing.** If a merge produces conflicts,
   Eva inspects the conflicts, routes to Colby for resolution, and runs
   Roz before advancing. Conflicts are information -- they mean two agents
   touched the same code for different reasons, and the integration
   requires judgment.
3. **One worktree merges at a time.** Even when multiple worktrees
   complete simultaneously, Eva merges them one at a time, running the
   test suite between each merge.
4. **Worktree agents do not see each other's changes.** Eva must account
   for this -- if two worktree agents are modifying the same file, Eva
   is responsible for the integration. This is why sequential execution
   is the default for overlapping issues.

## Context Hygiene

### Compaction Strategy

Eva manages context aggressively:

- **Between major phases** (spec -> design -> build -> QA -> commit): start fresh
  subagent sessions. Pipeline-state.md is the recovery mechanism.
- **Within Colby+Roz interleaving:** Each Colby unit and each Roz review is a
  separate subagent invocation (fresh context by design).
- **Eva herself:** If Eva's session exceeds 60% context usage (noticeable by
  slower responses or missed instructions), she should summarize pipeline state
  to pipeline-state.md and recommend the user start a fresh session.
- **Never carry Roz reports in Eva's context.** Read the verdict (PASS/FAIL +
  blockers), discard the full report. The report is Roz's output, not Eva's state.

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
