# Definition of Ready / Definition of Done

<!-- CONFIGURE: Update the placeholders below to match your project -->
<!--
  {lint_command}      = command to run linter (e.g., npm run lint, ruff check)
  {typecheck_command} = command to run type checker (e.g., npm run typecheck, mypy .)
  {test_command}      = command to run tests for changed files (e.g., npm test [path], pytest [path])
-->

Shared framework for all agents. Replaces procedural checklists with
structural output requirements.

## How It Works

- **DoR** = first section of your output. Proves you read upstream artifacts.
- **DoD** = last section of your output. Proves you covered everything.
- Eva verifies both at phase transitions.
- Roz independently verifies Colby's DoD against actual code.

## Definition of Ready (DoR)

Before doing your main work, output this section:

```markdown
## DoR: Requirements Extracted
**Source:** [paths to upstream artifacts you read]

| # | Requirement | Source |
|---|-------------|--------|
| 1 | [specific requirement] | [spec section / UX screen / ADR step] |
| 2 | [specific requirement] | [spec section / UX screen / ADR step] |

**Retro risks:** [relevant patterns from retro-lessons.md, or "None"]
```

### Rules

- Extract EVERY functional requirement, not just the ones you plan to address.
- Include edge cases, states, and acceptance criteria from the source.
- If the upstream artifact is vague on something, note it -- don't silently
  interpret.
- Eva spot-checks this list against the source. Gaps get caught here.
- If your READ list doesn't include an artifact that your DoR references,
  note it: "Missing from READ: [artifact]. Proceeding with available context."
  This makes orchestrator invocation omissions visible without blocking work.

### Per-Agent Sources

| Agent | Primary Source | Extract |
|-------|---------------|---------|
| **Sable** | Robert's spec | User stories, personas, acceptance criteria, edge cases |
| **Cal** | Spec + UX doc + doc plan | Functional requirements, UX constraints, data concerns |
| **Colby** (mockup) | Spec + UX doc | Screens, states, interactions, copy |
| **Colby** (build) | Spec + UX doc + ADR | Acceptance criteria per step, spec edge cases, UX states |
| **Agatha** | Spec + UX + ADR + doc plan + code | Doc plan items, spec-vs-code divergences |
| **Roz** (test authoring) | ADR + spec + existing code | Test descriptions, function signatures, domain intent |
| **Roz** | ADR + spec | Requirements to verify against implementation |
| **Poirot** | Git diff only (no upstream artifacts) | Diff metadata: files changed, lines added/removed, functions modified |
| **Distillator** | Source documents (spec, UX doc, ADR) | Source paths, token estimates, downstream consumer |

## Definition of Done (DoD)

After completing your work, output this section:

```markdown
## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | [from DoR] | Done | [where/how -- file, section, test] |
| 2 | [from DoR] | Deferred | [explicit reason] |

**Grep check:** `TODO/FIXME/HACK/XXX` in output files -> [count]
**Template:** All sections filled -- no TBD, no placeholders
```

### Universal Conditions (every agent, every time)

1. Every DoR requirement has a status (Done or Deferred with explicit reason)
2. No silent drops -- missing = Deferred with reason, not absent
3. No TODO/FIXME/HACK in delivered output
4. Output template complete -- every section filled

### Agent-Specific Conditions

**Colby (build):**
- `{lint_command} && {typecheck_command} && {test_command} [changed files]` passes
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

**Sable:**
- Every spec requirement has a corresponding screen or interaction
- All five states designed: empty, loading, populated, error, overflow
- Actual copy written -- no TBD
- Accessibility specified per screen

**Agatha:**
- Every doc plan item addressed
- Code read for accuracy -- divergences flagged
- Examples for every endpoint or config option

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

## Roz: DoD Enforcement

Roz has a special role -- she verifies other agents' DoD claims:

- Eva includes the requirements list in Roz's invocation
- Roz diffs requirements against actual implementation
- Roz greps for TODO/FIXME/HACK independently
- Self-reported "Done" that doesn't match code = BLOCKER
- Requirements in the spec/ADR that Colby didn't even list in her DoR = BLOCKER (silent drop)
- Roz does not trust coverage tables -- she verifies them

## Eva's Responsibilities

**At invocation:**
- Include `.claude/references/retro-lessons.md` in READ for every subagent invocation
- Include upstream artifact paths directly relevant to the work unit
- Pass context-brief excerpts via the CONTEXT field, not READ
- For Roz: include the requirements list from the spec for independent verification

**At phase transition:**
- Read agent's DoR -- spot-check against spec for missing requirements
- Read agent's DoD -- verify no unexplained gaps or silent drops
- Do not advance pipeline if DoR has obvious omissions or DoD has gaps
- Pass Colby's requirements to Roz for independent verification
