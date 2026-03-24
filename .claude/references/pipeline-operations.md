# Pipeline Operations Reference

Eva reads this file at pipeline start for detailed operational procedures.

## Continuous QA (Interleaved Roz + Colby)

Cal's ADR steps become work units. Roz writes tests first, Colby implements to pass them.

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
   Findings unique to Poirot get special attention.
5. If Roz or Poirot flags an issue on unit N, Eva queues the fix. Colby
   finishes the current unit, then addresses the fix before starting the next unit
6. Eva updates `docs/pipeline/pipeline-state.md` after each unit transition

**Post-build pipeline tail (after all units pass individual QA):**
7. Eva invokes the review juncture: Roz final sweep + Poirot + Robert-subagent
   + Sable-subagent (Large) in parallel
8. Eva triages all findings, routes fixes to Colby if needed, re-runs Roz
9. Eva invokes Agatha to write/update docs against the final verified code.
   On Small: only if Roz flagged doc impact. On Medium/Large: always.
10. Eva invokes Robert-subagent in doc review mode to verify Agatha's output
11. If Robert-subagent or Sable-subagent flagged DRIFT: hard pause. Human
    decides fix code or update spec/UX.
12. Eva invokes Ellis. Code + docs + updated specs/UX ship in one atomic commit.

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

Default execution model is **sequential with full pipeline per issue.**

1. **One issue at a time.** Eva does not start issue N+1 until issue N is committed and verified.
2. **Full test suite between issues.** If tests fail, Eva halts and routes the failure.
3. **Parallelization requires explicit user approval** and zero file overlap confirmation.
4. **No silent reordering.** Eva announces dependency-driven reorders.

## Worktree Integration Rules

Changes from isolated worktrees must be integrated using git operations -- **never naive file copying.**

1. **Use `git merge` or `git cherry-pick`** to bring worktree changes into the working branch.
2. **Resolve conflicts before advancing.** Route to Colby for resolution, run Roz before advancing.
3. **One worktree merges at a time.** Run the test suite between each merge.
4. **Worktree agents do not see each other's changes.** Eva is responsible for the integration.

## Context Hygiene

### Compaction Strategy

- **Between major phases:** start fresh subagent sessions. Pipeline-state.md is the recovery mechanism.
- **Within Colby+Roz interleaving:** Each unit is a separate subagent invocation (fresh context).
- **Eva herself:** At 60% context usage, summarize to pipeline-state.md and recommend a fresh session.
- **Never carry Roz reports in Eva's context.** Read the verdict only.

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
