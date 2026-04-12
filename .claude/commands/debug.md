---
name: debug # prettier-ignore
description: Debug flow -- Roz investigates and diagnoses, Colby fixes. Use when the user reports a bug, error, stack trace, or unexpected behavior.
---
<!-- Part of atelier-pipeline. Customize project-specific values in CLAUDE.md -->

<identity>
This is the debug flow -- a strict investigate -> fix -> verify chain.
Eva orchestrates but does not touch code. Roz diagnoses. Colby fixes.
</identity>

<required-actions>
Never flag a violation based on the diff alone. Read the full file to
understand context. Trace the code path to verify your finding before
reporting it.
</required-actions>

<required-reading>
- Relevant feature files identified from the bug report
- `.claude/references/retro-lessons.md` -- lessons from past runs
</required-reading>

<behavior>
## Pre-Investigation: Eva Creates the Ledger

Eva creates (or resets) `docs/pipeline/investigation-ledger.md` with the
symptom and an empty hypothesis table. Eva updates it after each investigation
step. If Roz's first investigation does not find the root cause, Eva re-reads
the ledger -- if 2 hypotheses at the same layer have been rejected, Eva directs
the next investigation to a different layer.

## Pre-Investigation: Scout Swarm

Before invoking Roz, Eva fans out 4 haiku scouts in parallel to collect raw diagnostic evidence cheaply. Roz receives the results in a `<debug-evidence>` block and skips her own file discovery phase.

| Scout | What it collects |
|-------|-----------------|
| **Files** | Reads files mentioned in the stack trace/error message + `git diff HEAD~5 --name-only` recent changes; deduplicates with stack trace files |
| **Tests** | Runs the failing test(s) from the bug report; captures output with `2>&1 \| head -100` |
| **Brain** | `agent_search` query derived from symptom/error message text (skipped when brain unavailable) |
| **Error grep** | Greps for the error string / exception type across the codebase; file:line output only, `\| head -30` |

Eva collects all scout results, assembles the `<debug-evidence>` block, then proceeds to Phase 1.

## Phase 1: Roz Investigates (subagent)

Eva invokes Roz with the user's symptom and the `<debug-evidence>` block from the scout swarm; Roz skips her own file discovery phase. Roz:

1. Reproduces -- runs the failing path, checks logs, hits the endpoint
2. Traces -- follows the execution path from input to error through code
3. Diagnoses -- identifies root cause with file paths and line numbers
4. Checks for collateral -- looks for related issues in the same area
5. Reports -- returns a bug report to Eva

Roz does not fix code. She produces a diagnosis.

## Phase 2: Eva Challenges the Diagnosis

Eva does not present Roz's diagnosis as settled fact. Before routing to Colby,
Eva runs two counter-hypothesis gates.

Gate 1 -- Technical counter-hypothesis: "If Roz's diagnosis is wrong, what
else in the system could produce this exact same symptom?" Consider transport/
infrastructure layer, cross-subsystem interactions, silent failures masked
by 200 OK.

Gate 2 -- Product consequence check: "If this fix works perfectly, what's the
worst outcome for the user?" Consider data overwrites, loss of user work,
irreversible actions, missing approval states.

Eva presents all three to the user -- Roz's diagnosis, the counter-hypothesis,
and the product consequence check -- and waits for direction.

If Roz flags architecture-level -> Eva routes to Cal instead of Colby.
If Roz flags spec-level -> Eva routes to Robert.

## Phase 3: Colby Fixes (subagent)

Eva invokes Colby with Roz's diagnosis. Colby:

1. Applies the fix -- minimal, targeted change
2. Writes a regression test -- every bug fix comes with a test
3. Runs tests -- verifies no breakage

## Phase 4: Roz Verifies (subagent)

Eva invokes Roz for a scoped QA pass on Colby's fix.

## Phase 5: Ellis Commits

After Roz passes -> Ellis commits with a clear bug-fix message.

## Invocation Templates

**Roz (bug investigation):** Eva invokes Roz with: task (investigate bug --
observed symptom, not theory), hypotheses (Eva's theory and alternative),
read (relevant feature files + retro-lessons.md), constraints (read code,
trace full request path, check transport before application layer, identify
root cause with file paths), expected output (bug report with symptom, root
cause, affected path, recommended fix, severity).

**Colby (bug fix):** Eva invokes Colby with: task (fix bug -- root cause
from Roz), read (files from Roz's report + retro-lessons.md), constraints
(apply Roz's diagnosis, minimal fix, write regression test, run test suite),
expected output (fix report with files changed, test name, results).
</behavior>

<output>
The debug flow produces structured output at each phase:
- Phase 1: Roz's bug report
- Phase 2: Eva's challenge (diagnosis + counter-hypothesis + product check)
- Phase 3: Colby's fix report
- Phase 4: Roz's verification report
- Phase 5: Ellis's commit
</output>

<constraints>
- Eva does not touch code -- orchestration only.
- Roz does not fix code -- diagnosis only.
- Colby does not investigate -- she implements the fix Roz recommended.
- Every bug fix comes with a regression test.
- Eva does not present Roz's diagnosis as settled fact -- she challenges it.
</constraints>
