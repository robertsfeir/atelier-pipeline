# Pipeline Operations Reference

Eva reads this file at pipeline start for detailed operational procedures.

<section id="invocation-format">

## Invocation Format

All subagent invocations use XML tags. Eva constructs prompts with `<task>`,
`<brain-context>`, `<context>`, `<hypotheses>`, `<read>`, `<warn>`,
`<constraints>`, and `<output>` tags. See `.claude/references/xml-prompt-schema.md`
and `.claude/references/invocation-templates.md` for the full tag vocabulary
and per-agent examples.

</section>

<protocol id="brain-prefetch">

## Brain Context Prefetch

Eva is responsible for all brain interactions. Before invoking any agent, Eva:

1. Calls `agent_search` with a query derived from the feature area
2. Injects results into the `<brain-context>` tag in the invocation prompt
3. Agents consume injected brain context as data -- they do not call
   `agent_search` themselves

After an agent returns, Eva inspects the output for capturable knowledge
(decisions, patterns, lessons, insights noted in the agent's DoD) and calls
`agent_capture`. Agents surface knowledge in their `<output>` section; Eva
captures it.

</protocol>

<operations id="continuous-qa">

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
6. **Eva invokes Ellis for a per-unit commit** on the feature branch after
   Roz QA PASS. Ellis uses per-unit commit mode (shorter message, no
   changelog trailer). The feature branch accumulates granular commits.
7. Eva updates `docs/pipeline/pipeline-state.md` after each unit transition

**Post-build pipeline tail (after all units pass individual QA):**
8. Eva invokes the review juncture: Roz final sweep + Poirot + Robert-subagent
   + Sable-subagent (Large) in parallel. Eva triages findings using the
   Triage Consensus Matrix (see below). Routes fixes to Colby if needed, re-runs Roz.
9. Eva invokes Agatha to write/update docs against the final verified code.
   On Small: only if Roz flagged doc impact. On Medium/Large: always.
10. Eva invokes Robert-subagent in doc review mode to verify Agatha's output
11. If Robert-subagent or Sable-subagent flagged DRIFT: hard pause. Human
    decides fix code or update spec/UX.
12. Final delivery (strategy-dependent, see `.claude/rules/branch-lifecycle.md`):
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
      ship as one merge. Per-unit history is preserved on the feature branch
      for `git bisect`.

</operations>

<matrix id="triage-consensus">

## Triage Consensus Matrix

At every review juncture, Eva consults this matrix to determine the action.
No discretion -- the matrix is the rule.

| Roz | Poirot | Robert | Sable | Action |
|-----|--------|--------|-------|--------|
| BLOCKER | any | any | any | **HALT.** Roz BLOCKER is always authoritative. |
| any | BLOCKER | any | any | **HALT.** Eva investigates Poirot's finding. If confirmed, same as Roz BLOCKER. |
| MUST-FIX | agrees | -- | -- | **HIGH-CONFIDENCE.** Queue fix, Colby priority. |
| PASS | flags issue | -- | -- | **CONTEXT-ANCHORING MISS.** Eva investigates -- Poirot caught what Roz's context biased her to miss. Treat as MUST-FIX minimum. |
| MUST-FIX | PASS | -- | -- | **STANDARD.** Queue fix per normal flow. |
| -- | -- | DRIFT | -- | **HARD PAUSE.** Human decides: fix code or update spec. |
| -- | -- | AMBIGUOUS | -- | **HARD PAUSE.** Human clarifies spec. |
| -- | -- | -- | DRIFT | **HARD PAUSE.** Human decides: fix code or update UX doc. |
| -- | -- | DRIFT | DRIFT | **CONVERGENT DRIFT.** High-confidence spec/UX misalignment. Escalate to human with both reports. |
| PASS | PASS | PASS | PASS | **ADVANCE.** All clear, proceed to Agatha. |

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
2. **Full test suite between issues.** If tests fail, Eva halts and routes the failure.
3. **Parallelization requires explicit user approval** and zero file overlap confirmation.
4. **No silent reordering.** Eva announces dependency-driven reorders.

</operations>

<operations id="worktree-rules">

## Worktree Integration Rules

Changes from isolated worktrees must be integrated using git operations -- **never naive file copying.**

1. **Use `git merge` or `git cherry-pick`** to bring worktree changes into the working branch.
2. **Resolve conflicts before advancing.** Route to Colby for resolution, run Roz before advancing.
3. **One worktree merges at a time.** Run the test suite between each merge.
4. **Worktree agents do not see each other's changes.** Eva is responsible for the integration.

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

**Brain integration (Eva, wave grouping):**
- **Read gate:** Before grouping, `agent_search` for prior wave decisions
  on this feature area. Reuse prior grouping as a starting point (still
  validate file overlap).
- **Write gate:** After grouping, `agent_capture` with
  `thought_type: 'decision'`, `source_agent: 'eva'`,
  `source_phase: 'build'`, content: "ADR-NNNN wave grouping:
  Wave 1 [steps ...], Wave 2 [steps ...]. Rationale: [file overlap]."

**Constraint preservation within waves:**
- Each unit within a wave still follows: Colby build -> Roz QA + Poirot
  blind review (per unit). All 10 mandatory gates apply per unit.
- Roz and Poirot run independently per unit -- no cross-unit review
  within a wave. Cross-unit integration is the final review juncture.
- The final review juncture (Roz sweep + Poirot + Robert + Sable) runs
  AFTER all waves complete, not after each wave.
- Batch-mode rules still apply: parallel requires zero file overlap,
  sequential is the fallback. Eva announces wave grouping to the user
  before execution begins.

</operations>

<section id="context-hygiene">

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

</section>
