# Definition of Ready / Definition of Done

<!-- CONFIGURE: Update the placeholders below to match your project -->
<!--
  {lint_command}      = command to run linter (e.g., npm run lint, ruff check)
  {typecheck_command} = command to run type checker (e.g., npm run typecheck, mypy .)
  {test_command}      = command to run tests for changed files (e.g., npm test [path], pytest [path])
-->

Shared framework for all agents. Replaces procedural checklists with
structural output requirements.

<framework id="dor-dod-structure">

### How It Works

- **DoR** = first section of your output. Proves you read upstream artifacts.
- **DoD** = last section of your output. Proves you covered everything.
- Eva verifies both at phase transitions.
- Roz independently verifies Colby's DoD against actual code.

Both DoR and DoD are placed inside the `<output>` tag in agent persona files.
The `<output>` tag is the structural container for everything an agent produces,
and DoR/DoD are the bookends: DoR opens the output, DoD closes it.

### DoR and DoD Inside `<output>`

When an agent produces output, the DoR section comes first and the DoD
section comes last. Everything the agent delivers goes between them.
Here is the structural pattern:

```markdown
<output>

## DoR: Requirements Extracted
**Source:** [paths to upstream artifacts you read]

| # | Requirement | Source | Source citations |
|---|-------------|--------|-----------------|
| 1 | [specific requirement] | [spec section / UX screen / ADR step] | [file:line or section ref] |
| 2 | [specific requirement] | [spec section / UX screen / ADR step] | [file:line or section ref] |

**Retro risks:** [relevant patterns from retro-lessons.md, or "None"]

[... agent's main work output goes here ...]

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | [from DoR] | Done | [where/how -- file, section, test] |
| 2 | [from DoR] | Deferred | [explicit reason] |

**Grep check:** `TODO/FIXME/HACK/XXX` in output files -> [count]
**Template:** All sections filled -- no TBD, no placeholders

</output>
```

</framework>

<section id="dor-rules">

### DoR Rules

- Extract every functional requirement, not just the ones you plan to address.
- Include edge cases, states, and acceptance criteria from the source.
- If the upstream artifact is vague on something, note it -- don't silently
  interpret.
- Eva spot-checks this list against the source. Gaps get caught here.
- If your READ list doesn't include an artifact that your DoR references,
  note it: "Missing from READ: [artifact]. Proceeding with available context."
  This makes orchestrator invocation omissions visible without blocking work.

</section>

<section id="per-agent-sources">

### Per-Agent Sources

| Agent | Primary Source | Extract |
|-------|---------------|---------|
| **Sable** (skill) | Robert's spec | User stories, personas, acceptance criteria, edge cases |
| **Sable** (subagent) | UX doc only (no ADR, no spec) | Screens, states, interactions, a11y, copy, responsive |
| **Cal** | Spec + UX doc + doc plan | Functional requirements, UX constraints, data concerns |
| **Colby** (mockup) | Spec + UX doc | Screens, states, interactions, copy |
| **Colby** (build) | Spec + UX doc + ADR | Acceptance criteria per step, spec edge cases, UX states |
| **Agatha** | Spec + UX + ADR + doc plan + code | Doc plan items, spec-vs-code divergences |
| **Robert** (subagent) | Spec only (no ADR, no UX doc) | Acceptance criteria, user stories, edge cases, NFRs |
| **Roz** (test authoring) | ADR + spec + existing code | Test descriptions, function signatures, domain intent |
| **Roz** | ADR + spec | Requirements to verify against implementation |
| **Poirot** | Git diff only (no upstream artifacts) | Diff metadata: files changed, lines added/removed, functions modified |
| **Distillator** | Source documents (spec, UX doc, ADR) | Source paths, token estimates, downstream consumer |

</section>

<section id="dod-universal">

### DoD Universal Conditions (every agent, every time)

1. Every DoR requirement has a status (Done or Deferred with explicit reason)
2. No silent drops -- missing = Deferred with reason, not absent
3. No TODO/FIXME/HACK in delivered output
4. Output template complete -- every section filled

</section>

<agent-dod>

### Agent-Specific DoD Conditions

**Colby (build):**
- `{lint_command} && {typecheck_command} && {test_command}` passes (full suite -- not scoped to changed files)
- If the full suite reveals failures in code Colby did not touch: fix them. "We didn't write that code" is not an exemption. Green suite before commit, full stop.
- Grep for TODO/FIXME/HACK across changed files -- show results
- Every ADR step acceptance criterion listed with pass evidence

**Colby (mockup):**
- All UX doc states implemented and switchable
- Lint + typecheck pass
- Route and nav item added

**Cal:**
- Every spec requirement traceable to at least one ADR step's acceptance criteria
- Failure tests >= happy path tests
- Return shapes defined for every data access method and endpoint
- Code shape examples per step
- Every step passes the 5-test sizing gate (S1-S5) from workflow section
- No step exceeds 8 files without explicit justification in Notes for Colby
- Each step has a one-sentence "After this step, I can ___" demo description

**Sable:**
- Every spec requirement has a corresponding screen or interaction
- All five states designed: empty, loading, populated, error, overflow
- Actual copy written -- no TBD
- Accessibility specified per screen

**Agatha:**
- Every doc plan item addressed
- Code read for accuracy -- divergences flagged
- Examples for every endpoint or config option

**Robert (subagent):**
- Every acceptance criterion from the spec has a verdict (PASS / DRIFT / MISSING / AMBIGUOUS)
- No blanket approvals -- each criterion has file:line evidence or explicit explanation
- DRIFT findings include both spec reference and code reference
- AMBIGUOUS findings halt pipeline (human decides)
- When reviewing docs: every user-facing behavior in spec verified against docs

**Sable (subagent):**
- Every screen, state, interaction, a11y requirement, and copy item has a verdict
- Five-state audit completed for every screen (empty, loading, populated, error, overflow)
- Accessibility audit completed (keyboard, ARIA, contrast, focus, screen reader)
- DRIFT findings include both UX doc reference and code reference
- AMBIGUOUS findings halt pipeline (human decides)

**Poirot:**
- Minimum 5 findings produced (or HALT documented with re-analysis)
- All severity categories checked: logic, security, error handling, naming, dead code, type safety, resource management, concurrency
- Cross-file analysis completed (or "Not applicable -- single file" noted)
- Grep verification performed for pattern-based findings

**Distillator:**
- Preservation checklist complete -- all categories (decisions, rejected alternatives, constraints, dependencies, open questions, scope boundaries, named entities, numbers/dates/versions) counted and verified
- Compression ratio reported in YAML frontmatter
- Zero prose paragraphs -- bullets only
- Round-trip reconstruction produced when VALIDATE: true (or explicitly marked N/A)

**Ellis:**
- Diff analyzed completely -- no missed files
- Changelog trailer present for user-facing changes (or explicitly skipped with reason)

**Roz (test authoring):**
- Every Cal test description has a corresponding concrete assertion
- Domain intent reasoning documented for non-obvious expected values
- Ambiguous intent flagged, not silently decided
- Test files lint and typecheck (tests may fail -- implementation doesn't exist yet)

</agent-dod>

<section id="roz-enforcement">

### Roz: DoD Enforcement

Roz has a special role -- she verifies other agents' DoD claims:

- Eva includes the requirements list in Roz's invocation
- Roz diffs requirements against actual implementation
- Roz greps for TODO/FIXME/HACK independently
- Self-reported "Done" that doesn't match code = BLOCKER
- Requirements in the spec/ADR that Colby didn't even list in her DoR = BLOCKER (silent drop)
- Roz does not trust coverage tables -- she verifies them

</section>

<section id="eva-responsibilities">

### Eva's Responsibilities

**At invocation:**
- Include `{config_dir}/references/retro-lessons.md` in READ for every subagent invocation
- Include upstream artifact paths directly relevant to the work unit
- Pass context-brief excerpts via the CONTEXT field, not READ
- For Roz: include the requirements list from the spec for independent verification
- For Robert-subagent: include ONLY the spec and code paths. No ADR, UX doc, or Roz report.
- For Sable-subagent: include ONLY the UX doc and code paths. No ADR, spec, or Roz report.
- For Agatha: invoke AFTER final Roz sweep (not parallel with Colby)

**At phase transition:**
- Read agent's DoR -- spot-check against spec for missing requirements
- Read agent's DoD -- verify no unexplained gaps or silent drops
- Do not advance pipeline if DoR has obvious omissions or DoD has gaps
- Pass Colby's requirements to Roz for independent verification

**At pipeline end (spec/UX reconciliation):**
- Triage DRIFT findings from Robert-subagent and Sable-subagent
- Present delta to user -- human decides: update living artifact or fix code
- If update: invoke Robert-skill (spec) or Sable-skill (UX doc) to correct
- If fix: route to Colby, re-run Roz, then re-run the subagent that flagged it
- Updated artifacts ship in same commit as code via Ellis

</section>
