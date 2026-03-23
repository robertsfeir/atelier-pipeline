<!-- Part of atelier-pipeline. Customize project-specific values in CLAUDE.md -->
---
name: debug # prettier-ignore
description: Debug flow -- Roz investigates and diagnoses, Colby fixes. Use when the user reports a bug, error, stack trace, or unexpected behavior.
---

# Debug Flow -- Roz -> Colby -> Roz

Bug reports follow a strict investigate -> fix -> verify chain.
Eva orchestrates but never touches code. Roz diagnoses. Colby fixes.

## Flow

### Pre-Investigation: Eva Creates the Ledger

Eva creates (or resets) `docs/pipeline/investigation-ledger.md` with the
symptom and an empty hypothesis table. Eva updates it after each
investigation step. If Roz's first investigation doesn't find the root
cause, Eva re-reads the ledger -- if 2 hypotheses at the same layer have
been rejected, Eva directs the next investigation to a different layer.

### Phase 1: Roz Investigates (subagent)

Eva invokes Roz with the user's symptom. Roz:

1. **Reproduces** -- runs the failing path, checks logs, hits the endpoint
2. **Traces** -- follows the execution path from input to error through
   code, not guessing
3. **Diagnoses** -- identifies root cause with file paths and line numbers
4. **Checks for collateral** -- looks for related issues in the same area
5. **Reports** -- returns a bug report to Eva

Roz does NOT fix code. She produces a diagnosis:

> **Symptom:** [what the user sees]
> **Root cause:** [file:line -- what's wrong and why]
> **Affected path:** [full execution trace from input to error]
> **Recommended fix:** [precise description of what needs to change]
> **Related issues:** [anything else found in the same area]
> **Severity:** code-level | architecture-level | spec-level

### Phase 2: Eva Challenges the Diagnosis

Eva does NOT present Roz's diagnosis as settled fact. Before routing to
Colby, Eva runs two counter-hypothesis gates.

**Gate 1 -- Technical counter-hypothesis.** Eva asks: "If Roz's diagnosis
is wrong, what else in the system could produce this exact same symptom?"

Consider at minimum:
- Transport/infrastructure layer assumptions (the bug may not be in
  application code at all -- auth headers, SSE/WebSocket transport,
  proxy behavior, container networking)
- Cross-subsystem interactions (a closure capturing stale state,
  a middleware short-circuiting before the handler runs, a race between
  two concurrent callers)
- Silent failures masked by 200 OK (the request "succeeded" but returned
  wrong/empty data -- the bug is upstream of where the symptom appears)

**Gate 2 -- Product consequence check.** Eva asks: "If this fix works
perfectly as designed, what's the worst outcome for the user?"

Consider at minimum:
- Data overwrites without user consent (fix silently replaces user input)
- Loss of user work (fix discards draft state, unsaved changes, or
  in-progress edits)
- Irreversible actions (fix applies a destructive change with no undo)
- Missing approval/review states (fix bypasses a step the user expects
  to control)

If Gate 2 surfaces a real concern, the bug may not be in the code -- it
may be in the feature design. That requires Robert, not Colby.

**Eva presents all three to the user:**

> **Roz's diagnosis:** [summary of root cause and recommended fix]
>
> **Technical counter-hypothesis:** [alternative explanation for the
> same symptom -- what if the real cause is at a different layer?]
>
> **Product consequence check:** [what could go wrong for the user
> even if this fix works exactly as intended?]
>
> Your call:
> - **"fix it"** -- Colby applies Roz's recommended fix
> - **"investigate the alternative"** -- Roz digs into the counter-hypothesis
> - **"this is a design problem, stop"** -- route to Robert for spec review

If Roz flags architecture-level -> Eva routes to Cal instead of Colby.
If Roz flags spec-level -> Eva routes to Robert.

### Phase 3: Colby Fixes (subagent)

Eva invokes Colby with Roz's diagnosis. Colby:

1. **Applies the fix** -- minimal, targeted change
2. **Writes a regression test** -- every bug fix comes with a test that
   would have caught it. Non-negotiable.
3. **Runs tests** -- verifies the fix doesn't break anything else

### Phase 4: Roz Verifies (subagent)

Eva invokes Roz for a scoped QA pass on Colby's fix:

- Re-run the originally failing path -- confirm it's fixed
- Run tests for the affected area
- Check that the regression test actually covers the bug
- Standard QA checks on changed files

### Phase 5: Ellis Commits

After Roz passes -> Ellis commits with a clear bug-fix message.

## Invocation Templates

**Roz (bug investigation):**
> TASK: Investigate bug -- [observed symptom, not theory]
> HYPOTHESES: [Eva's theory] | [alternative at different layer]
> READ: [relevant feature files], .claude/references/retro-lessons.md
> BRAIN: [If brain available: recurring QA patterns, prior findings on similar code, AND retro lessons relevant to this area from agent_search. Omit if unavailable.]
> CONTEXT: [excerpt from docs/pipeline/context-brief.md if relevant, otherwise omit]
> WARN: [specific retro-lesson if pattern matches, otherwise omit]
> CONSTRAINTS:
> - Read code, check logs, run tests
> - Trace the full request path from input to error
> - Check transport layer (auth headers, response status) before application layer
> - Report which layers were checked and what was found, even if normal
> - Identify root cause with file paths and line numbers
> - Check for related issues in the same area
> - Do NOT write code -- diagnosis only
> OUTPUT: Bug report with: symptom, root cause (file:line), affected code path, recommended fix description, severity, related issues

**Colby (bug fix -- after Roz diagnosis):**
> TASK: Fix bug -- [root cause summary from Roz]
> READ: [files from Roz's report], .claude/references/retro-lessons.md
> BRAIN: [If brain available: implementation patterns, known gotchas, AND retro lessons relevant to this area from agent_search. Omit if unavailable.]
> CONTEXT: [excerpt from docs/pipeline/context-brief.md if relevant, otherwise omit]
> WARN: [specific retro-lesson if pattern matches, otherwise omit]
> CONSTRAINTS:
> - Roz's diagnosis: [paste Roz's root cause and recommended fix]
> - Minimal fix -- fix the bug, don't refactor the neighborhood
> - Write a regression test that would have caught this bug
> - Run affected test suite to verify no breakage
> - Zero TODO/FIXME/HACK in delivered code
> OUTPUT: Fix report with files changed, regression test name, test results
