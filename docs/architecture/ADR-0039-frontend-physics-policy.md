# ADR-0039: Frontend Layout Physics -- Pipeline Policy

## DoR: Requirements Extracted

**Sources:** Failure mode analysis (3 confirmed systemic gaps), existing pipeline
source files (`source/shared/agents/roz.md`, `source/shared/references/dor-dod.md`,
`source/shared/agents/investigator.md`, `source/shared/agents/cal.md`,
`source/shared/references/retro-lessons.md`, `source/shared/references/qa-checks.md`).

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Roz's test authoring read list must include the UX doc when one exists | Failure Mode 1 (information chain gap) | dor-dod.md:90 -- current list is "ADR + spec + existing code" |
| R2 | Cal's UI Specification table must include layout context for constrained-container components | Failure Mode 1 (information chain gap) | cal.md:78-84 -- current table lacks container/flex/collapse fields |
| R3 | Roz must prefer asserting correct layout primitive usage over asserting CSS property values for constrained-container components | Failure Mode 2 (test vocabulary gap) | roz.md:33-40 -- no current guidance on layout-specific assertions |
| R4 | toBeVisible() must be preferred over toBeInTheDocument() for visibility-sensitive assertions | Failure Mode 2 (test vocabulary gap) | roz.md -- no current guidance |
| R5 | Poirot must trace through constant indirection when checking cross-layer wiring | Failure Mode 3 (constant-blind grep) | investigator.md:29-31 -- current instruction is raw string grep only |
| R6 | qa-checks.md wiring verification (check 14) must include constant-indirected route matching | Failure Mode 3 (constant-blind grep) | qa-checks.md:55-64 |
| R7 | retro-lessons.md must capture this as lesson 006 for future agent reference | Pipeline convention | retro-lessons.md format |
| R8 | API contract layer (OpenAPI + codegen) noted as recommended project-level pattern, not mandated | Fix 5 | Constraint: recommendation not mandate |
| R9 | No browser-based testing of any kind | Hard constraint | Absolute -- no Playwright, Chromatic, Percy, Storybook visual regression |
| R10 | No brittle per-property CSS assertions (e.g., "assert flex-shrink: 0 in every test") | Hard constraint | Principle: use correct primitive, test logical contract |
| R11 | Changes to source/shared/ only, never .claude/ (synced via /pipeline-setup) | Pipeline convention | CLAUDE.md |

**Retro risks:**

- **Lesson #005 (Frontend Wiring Omission):** Directly relevant -- this ADR
  extends lesson 005's scope. The wiring gap was endpoints; now we also address
  constant-indirected routes (Poirot) and layout-context information chains
  (Cal/Roz). The lesson's structural causes (layer-oriented ADR steps, fresh
  context windows, no end-to-end wiring gate) are the same root causes
  driving Failure Modes 1 and 3 here.
- **Lesson #002 (Self-Reporting Bug Codification):** Relevant to Fix 4. When
  Roz writes tests that assert `toBeInTheDocument()` on a component that
  should be visible, she is codifying a false positive. The principle addition
  prevents this specific form of bug codification.

---

**Spec challenge:** The spec assumes that layout primitives (components that
encapsulate flex-shrink, min-width, overflow behavior) will exist and be used
by consuming projects. **If wrong, the design fails because** the architectural
fix (test the primitive, not the CSS) requires the primitive to exist. However,
this ADR targets the pipeline's agent guidance, not any specific project. The
policy says "when constrained-container components exist, test the primitive."
If a project has no primitives, the guidance degrades to "Cal flags the
collapse risk and Colby writes defensive CSS" -- still better than the status
quo where neither happens.

**SPOF:** The information chain from UX doc to Roz's test target. **Failure
mode:** If Eva's invocation omits the UX doc from Roz's READ list (the
mechanical step that delivers the information), Roz writes tests without
layout context and the gap persists exactly as before. **Graceful
degradation:** Roz's DoR requires citing source files. If Roz lists "UX doc"
in her DoR but it was not in READ, she notes "Missing from READ: UX doc" per
dor-dod.md:72-74. This makes the omission visible to Eva at phase transition.
Not automatic, but observable.

**Anti-goals:**

1. Anti-goal: Mandating a specific component library or design system.
   Reason: This is pipeline guidance for agents, not a project architecture
   decision. Different projects use different UI frameworks. The policy says
   "use layout primitives" -- it does not say "use Radix" or "use Shadcn."
   Revisit: If the pipeline ships a reference design system as a skill.

2. Anti-goal: Adding browser-based visual regression testing.
   Reason: Hard constraint. The architectural fix (layout primitives +
   logical assertions) replaces the need for rendered-dimension assertions.
   Browser testing adds infrastructure cost, flakiness, and CI latency that
   outweigh the marginal coverage gain for the pipeline's use case.
   Revisit: Never -- this is an absolute constraint.

3. Anti-goal: Building a CSS property assertion library for jsdom.
   Reason: jsdom does not compute layout. Any assertion library that checks
   computed CSS values (flex-shrink, rendered width, overflow) is lying --
   jsdom returns initial/specified values, not computed layout values. Tests
   that pass in jsdom and fail in a browser are worse than no tests.
   Revisit: If jsdom (or a successor) gains a layout engine. Do not hold
   your breath.

---

## Status

Proposed.

**Depends on:** None. All changes are additive to existing agent persona files
and reference docs.

**Supersedes:** None. Extends lesson #005's scope.

**Related:** ADR-0033 (hook enforcement audit -- same "fix the pipeline itself"
pattern), lesson #005 (frontend wiring omission).

## Context

Three systemic failure modes have been confirmed in how the pipeline handles
frontend verification:

1. **Information chain gap.** Roz's test authoring read list (dor-dod.md:90)
   is `ADR + spec + existing code`. The UX doc is not included. Sable's
   geometric constraints -- drawer width, flex direction, collapse risk --
   never reach Roz's test target. Cal's ADR steps encode logical correctness
   but not layout context (e.g., "this component renders inside a 400px
   flex-row container and must not collapse"). The gap propagates: Cal ADR
   (no geometry) -> Roz test (no physics assertions) -> Colby implementation
   (no defensive CSS).

2. **Test vocabulary gap.** jsdom does not compute layout.
   `toBeInTheDocument()` passes for elements collapsed to 0px by flex-shrink
   default behavior. `toBeVisible()` in jsdom also passes (checks
   `display:none` / `visibility:hidden`, not rendered dimensions). Neither
   happy-dom nor any DOM simulator computes layout. No browser-based testing
   of any kind is permitted. The fix is architectural, not environmental.

3. **Poirot's constant-blind wiring check.** investigator.md:29-31 instructs
   Poirot to grep for orphan endpoints. When frontend code uses a constant
   for API routes (e.g., `PROMOTION_ENDPOINT = '/api/v1/promote'`) and the
   backend uses the raw string, Poirot's grep finds no match and reports no
   wiring problem. The actual connection is severed.

All three are structural pipeline gaps, not one-off bugs. They recur on every
project that has constrained-container UI and constant-indirected routes.

## Decision

Five targeted policy changes to pipeline agent guidance, plus one retro lesson
and one project-level recommendation:

### D1: Layout Primitives as the Architectural Answer (Failure Modes 1 + 2)

Since no browser testing is permitted, visual layout correctness is enforced
**architecturally**, not through test assertions. Components rendered inside
constrained containers (drawers, sidebars, panels) must encapsulate their own
layout physics -- e.g., a Badge component always sets `flex-shrink: 0`
internally. The consumer cannot set the wrong value because there is no API
for it.

This shifts Roz's test target: instead of asserting CSS values (brittle,
jsdom-unreliable), Roz asserts that the correct primitive/component is used.
That is a logical assertion jsdom handles perfectly.

### D2: Information Chain Repair (Failure Mode 1)

Two surgical changes:

1. **dor-dod.md line 90** (Roz test authoring source): add `+ UX doc (when
   exists)` to the primary source list.

2. **cal.md Hard Gate 5** (UI Specification table): add a `layout context`
   column. For every step that renders components inside a constrained
   container, Cal specifies: container type, flex direction, collapse risk,
   and which layout primitives apply. This information propagates to Roz via
   the ADR.

### D3: Poirot Constant Tracing (Failure Mode 3)

Extend investigator.md cross-layer wiring check (line 29-31): when a new route
string appears in the diff, grep for both the raw string AND any constants
that could hold it. If a route is only reachable via a constant and the
constant is not imported by any consumer, flag it as FIX-REQUIRED.

Also extend qa-checks.md check 14 (Roz wiring verification) with the same
constant-tracing instruction.

### D4: Roz Test Vocabulary Principle (Failure Mode 2)

One principle addition to roz.md Test Authoring Mode: for components inside
constrained containers, verify the correct layout primitive is used rather
than asserting computed CSS values. Prefer `toBeVisible()` over
`toBeInTheDocument()` for visibility-sensitive assertions, with the
understanding that the architectural fix (primitives) is the primary defense.

### D5: API Contract Layer (Recommendation)

OpenAPI or equivalent schema + TypeScript codegen between frontend and backend.
When backend changes a route, frontend CI fails at `tsc --noEmit` before any
agent touches a mock. Poirot's grep problem is reduced (though not eliminated)
because type mismatches surface at compile time. This is a **project-level
recommendation** -- the ADR notes it as the contract layer pattern without
mandating a specific toolchain.

### D6: Retro Lesson

Capture as lesson #006 in retro-lessons.md, referencing all three failure
modes and the five fixes. Agents Cal, Colby, Roz, and Poirot.

## Alternatives Considered

### A1: Add browser-based visual regression testing

Rejected. Hard constraint: no browser testing of any kind. Infrastructure cost,
flakiness, and CI latency outweigh marginal coverage. The architectural fix
(layout primitives) is strictly superior for the pipeline's use case.

### A2: Build a CSS property assertion library for jsdom

Rejected. jsdom does not compute layout. Assertions on `getComputedStyle()`
in jsdom check specified values, not rendered values. Tests that pass in jsdom
and fail in a browser are worse than no tests. This creates false confidence.

### A3: Add a per-property CSS checklist to Roz's QA checks

Rejected. Brittle, high-maintenance, and still does not detect layout collapse
(jsdom limitation). Every new CSS property that matters requires updating the
checklist. The principle-based approach ("use the primitive, test the logical
contract") is sustainable.

### A4: Leave information chain as-is, add layout assertions to Cal's test spec

Rejected. Cal's test spec describes *what* to test, not *how*. If Roz never
reads the UX doc, she does not know which components are inside constrained
containers. The information chain must be repaired at the source (dor-dod.md
read list), not patched at the output (test spec).

## Consequences

**Positive:**
- Layout collapse bugs are prevented architecturally (primitives) rather than
  detected after implementation (tests that cannot detect them).
- Roz receives UX doc context, enabling physics-aware test authoring.
- Cal's ADR steps carry layout context, preventing information loss across
  agent boundaries.
- Poirot catches constant-indirected wiring breaks that previously passed
  silently.
- All changes are additive -- no existing behavior removed.

**Negative:**
- Cal's UI Specification table gains a column. Slightly more work per ADR step
  that touches UI. Justified: the column prevents a class of bugs.
- Poirot's cross-layer wiring check becomes two-step (raw string then constant
  trace). Slightly more tool calls per review. Justified: one-step grep was
  missing real problems.
- Roz's read list grows by one file (UX doc). Marginal context window cost.
  Justified: the alternative is writing tests without understanding the
  rendering constraints.

**Neutral:**
- The API contract layer recommendation (D5) has no pipeline enforcement. It
  is a pattern projects should adopt but the pipeline does not mandate it.

---

## Implementation Plan

### Step 1: Repair Roz's Information Chain and Test Vocabulary

**Files to modify:** `source/shared/references/dor-dod.md`,
`source/shared/agents/roz.md`

**Changes:**
1. `dor-dod.md` line 90 -- Roz (test authoring) source: change from
   `ADR + spec + existing code` to `ADR + spec + UX doc (when exists) + existing code`
2. `roz.md` Test Authoring Mode section -- add one principle paragraph after
   the existing guidance about domain intent (line 39): for components inside
   constrained containers (drawers, sidebars, panels), assert that the correct
   layout primitive is used rather than asserting CSS property values. Prefer
   `toBeVisible()` over `toBeInTheDocument()` for visibility-sensitive
   assertions. The architectural fix (layout primitives encapsulating their own
   physics) is the primary defense; tests verify primitive usage, not CSS.

**Acceptance criteria:**
- dor-dod.md Roz (test authoring) row includes "UX doc (when exists)"
- roz.md Test Authoring Mode contains the layout primitive principle
- No other sections of either file are modified
- The additions are single-paragraph surgical edits, not checklists

**Complexity:** Low (2 files, 2 targeted edits)

**After this step, I can:** confirm that Roz's test authoring input list and
test vocabulary guidance account for layout physics.

### Step 2: Extend Cal's UI Specification with Layout Context

**Files to modify:** `source/shared/agents/cal.md`

**Changes:**
1. Hard Gate 5 (UI specification, line 78-84) -- extend the UI Specification
   table description to include: `layout context (container type / flex
   direction / collapse risk / applicable primitives, or "unconstrained")`.
2. ADR skeleton (line 117) -- update the UI Specification column list to
   include `layout context`.

**Acceptance criteria:**
- Cal's Hard Gate 5 includes layout context as a required field
- ADR skeleton UI Specification line lists layout context
- No other sections of cal.md are modified

**Complexity:** Low (1 file, 2 targeted edits)

**After this step, I can:** confirm that Cal's ADR steps carry layout context
for constrained-container components.

### Step 3: Extend Poirot's Cross-Layer Wiring Check for Constant Indirection

**Files to modify:** `source/shared/agents/investigator.md`,
`source/shared/references/qa-checks.md`

**Changes:**
1. `investigator.md` line 29-31 (cross-layer wiring check) -- extend the
   instruction: after grepping for the raw route string, also grep for
   constants that could hold it (pattern: `UPPER_SNAKE.*=.*'/route/path'`
   or `const.*Endpoint.*=.*'/route/path'`). If the route is only reachable
   via a constant and the constant is not imported by any consumer, flag as
   FIX-REQUIRED.
2. `qa-checks.md` check 14 (wiring verification) -- add after the existing
   paragraph: when grepping for route URLs, also check for constant
   indirection. Grep for constants holding the route string. If frontend
   code uses a constant for a route and backend uses the raw string (or vice
   versa), verify the constant is defined and imported. Constant-indirected
   routes with no traceable consumer = BLOCKER.

**Acceptance criteria:**
- investigator.md cross-layer wiring check includes constant-tracing
  instruction
- qa-checks.md check 14 includes constant-tracing instruction
- No other sections of either file are modified

**Complexity:** Low (2 files, 2 targeted edits)

**After this step, I can:** confirm that both Poirot and Roz trace through
constant indirection during wiring verification.

### Step 4: Add Retro Lesson 006

**Files to modify:** `source/shared/references/retro-lessons.md`

**Changes:**
Add lesson 006 inside the `<retro-lessons>` block, after lesson 005. Format
matches existing lessons (id, agents, what-happened, root-cause, rules with
per-agent directives). Agents: cal, colby, roz, poirot.

**Acceptance criteria:**
- Lesson 006 exists with correct format and XML structure
- Agents listed: cal, colby, roz, poirot
- What-happened describes all three failure modes concisely
- Root-cause identifies the information chain gap as the structural cause
- Rules reference specific fixes (layout primitives, constant tracing,
  toBeVisible preference, UX doc in read list)
- No existing lessons are modified

**Complexity:** Low (1 file, 1 addition)

**After this step, I can:** confirm that future agent invocations will see
this lesson in their retro risks check.

---

## Test Specification

| ID | Category | Description |
|----|----------|-------------|
| T-0039-001 | Positive | dor-dod.md Roz (test authoring) row contains "UX doc (when exists)" in the primary source list |
| T-0039-002 | Positive | roz.md Test Authoring Mode contains layout primitive principle paragraph |
| T-0039-003 | Positive | roz.md layout primitive principle mentions toBeVisible preference |
| T-0039-004 | Positive | cal.md Hard Gate 5 includes "layout context" field description |
| T-0039-005 | Positive | cal.md ADR skeleton UI Specification line includes "layout context" |
| T-0039-006 | Positive | investigator.md cross-layer wiring check mentions constant/indirection tracing |
| T-0039-007 | Positive | qa-checks.md check 14 mentions constant-indirected route matching |
| T-0039-008 | Positive | retro-lessons.md contains lesson 006 with agents cal, colby, roz, poirot |
| T-0039-009 | Negative | roz.md does NOT contain "flex-shrink" as an assertion directive (explanatory context describing what primitives encapsulate is permitted) |
| T-0039-010 | Negative | roz.md does NOT contain "Playwright", "Chromatic", "Percy", "Storybook", or "browser" |
| T-0039-011 | Negative | cal.md does NOT contain "assert CSS" or "assert flex-shrink" |
| T-0039-012 | Negative | No changes to any file under .claude/ directory (source-only policy) |
| T-0039-013 | Boundary | dor-dod.md Roz (test authoring) row still contains "ADR + spec + existing code" (additive, not replacement) |
| T-0039-014 | Boundary | investigator.md still contains the original raw-string grep instruction (additive, not replacement) |
| T-0039-015 | Boundary | retro-lessons.md lessons 001-005 are unmodified |
| T-0039-016 | Negative | retro-lessons.md lesson 006 does NOT reference browser testing or visual regression |
| T-0039-017 | Positive | roz.md layout primitive principle is a single paragraph, not a checklist |
| T-0039-018 | Positive | qa-checks.md constant-tracing addition mentions BLOCKER severity for unresolved indirection |

Failure tests: 10 (T-0039-009 through T-0039-016, T-0039-017, T-0039-018).
Happy path tests: 8 (T-0039-001 through T-0039-008).
Ratio: 10:8 -- failure >= happy. Passes.

---

## Contract Boundaries

| Producer | Consumer | Shape |
|----------|----------|-------|
| UX doc (Sable output) | Roz test authoring read list (dor-dod.md) | File path in READ; layout constraints as prose |
| Cal ADR UI Specification table (layout context column) | Roz test spec (ADR as source) | Table row: step, elements, sort, color, states, nav, layout context |
| Poirot constant-tracing grep results | Poirot findings table | Finding row: location, severity, category, description |
| Roz wiring verification constant trace | Roz QA report | Check row: status, details |
| retro-lessons.md lesson 006 | All agents via preamble step 3 | XML lesson element with rules |

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| dor-dod.md Roz source list (UX doc) | Text: "UX doc (when exists)" | Roz test authoring mode (roz.md) | Step 1 |
| roz.md layout primitive principle | Prose paragraph | Roz agent during test authoring | Step 1 |
| cal.md layout context column | Table column spec | Cal agent during ADR production -> ADR -> Roz | Step 2 |
| investigator.md constant-tracing | Instruction text | Poirot agent during blind review | Step 3 |
| qa-checks.md constant-tracing | Instruction text | Roz agent during wiring verification | Step 3 |
| retro-lessons.md lesson 006 | XML lesson element | All agents via preamble | Step 4 |

No orphan producers. Every producer has a consuming agent in the same or
earlier step.

---

## Data Sensitivity

Not applicable. This ADR modifies pipeline agent guidance files (markdown
persona files and reference docs). No data access methods, no API endpoints,
no store methods.

---

## Notes for Colby

1. **All edits are in `source/shared/`**, never `.claude/`. After Ellis
   commits, run `/pipeline-setup` to sync installed copies.

2. **Surgical edits only.** Each file change is one paragraph or one table
   column addition. Do not restructure surrounding content. The existing
   formatting and line structure must be preserved.

3. **dor-dod.md line 90 edit** -- The current line reads:
   `| **Roz** (test authoring) | ADR + spec + existing code | Test descriptions, function signatures, domain intent |`
   Change to:
   `| **Roz** (test authoring) | ADR + spec + UX doc (when exists) + existing code | Test descriptions, function signatures, domain intent |`
   This is the single most important edit. Without it, the entire information
   chain remains broken.

4. **roz.md Test Authoring Mode** -- Insert a new paragraph after line 39
   (after "flag it -- do not guess."). The paragraph should state the layout
   primitive principle in approximately 3-4 sentences. Do not add a numbered
   list, a checklist, or sub-sections. One paragraph. It should mention
   `toBeVisible()` preference over `toBeInTheDocument()` for visibility-
   sensitive assertions.

5. **cal.md Hard Gate 5** -- Extend the existing table description, do not
   replace it. After the current fields (UI elements, sort order, color
   coding, states, nav wiring), add: `layout context (container type / flex
   direction / collapse risk / applicable layout primitives, or
   "unconstrained")`.

6. **investigator.md line 29-31** -- The current instruction says "orphan
   endpoints (nothing calls them), phantom calls (endpoints not in diff --
   grep to verify)". Extend with a second sentence about constant
   indirection. Do not rewrite the existing sentence.

7. **qa-checks.md check 14** -- Add a second paragraph after the existing
   wiring verification paragraph. The new paragraph covers constant-indirected
   routes specifically.

8. **retro-lessons.md lesson 006** -- Follow the exact XML structure of
   lessons 001-005. The lesson needs `<what-happened>`, `<root-cause>`, and
   `<rules>` with `<rule agent="...">` for cal, colby, roz, and poirot.

9. **Pattern reference for constant grep:** When tracing constants, the
   practical grep patterns are:
   - `grep -r "UPPER_SNAKE.*=.*'/api/" src/` (constant definitions)
   - `grep -r "const.*[Ee]ndpoint.*=.*'/api/" src/` (camelCase definitions)
   - Then for each constant found, grep for its import/usage.
   Poirot and Roz do not need the exact grep commands in their persona files,
   but the investigator.md instruction should be concrete enough that the
   agent knows to trace through the indirection, not just grep for the raw
   URL string.

10. **D5 (API contract layer) is a recommendation only.** It does not appear
    in any file edit. It is documented in this ADR's Decision section for
    project-level reference. Do not add it to any agent persona file.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Roz test authoring read list includes UX doc | Done | Step 1: dor-dod.md edit |
| R2 | Cal UI Specification table includes layout context | Done | Step 2: cal.md edit |
| R3 | Roz layout primitive principle | Done | Step 1: roz.md edit |
| R4 | toBeVisible preference | Done | Step 1: roz.md edit (same paragraph) |
| R5 | Poirot constant tracing | Done | Step 3: investigator.md edit |
| R6 | qa-checks.md constant tracing | Done | Step 3: qa-checks.md edit |
| R7 | Retro lesson 006 | Done | Step 4: retro-lessons.md addition |
| R8 | API contract layer recommendation | Done | Decision section D5 (no file edit -- by design) |
| R9 | No browser testing | Done | Anti-goal 2, Alternative A1 rejected |
| R10 | No brittle CSS assertions | Done | Anti-goal 3, Alternative A3 rejected, T-0039-009, T-0039-011 |
| R11 | Source-only edits | Done | All steps target source/shared/, T-0039-012 |

**Grep check:** `TODO/FIXME/HACK/XXX` in output files -> 0
**Template:** All sections filled -- no TBD, no placeholders
