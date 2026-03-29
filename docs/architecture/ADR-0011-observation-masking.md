# ADR-0011: Observation Masking for Within-Session Context Management

## Status

Proposed

## DoR: Requirements Extracted

| # | Requirement | Source | Notes |
|---|-------------|--------|-------|
| R1 | Replace routine Distillator compression with mechanical placeholder substitution for within-session tool outputs | Issue #10, brain-context (JetBrains research insight) | Masking is cheaper, avoids stopping-signal obscuration |
| R2 | Preserve all agent reasoning text verbatim -- never mask agent analysis, decisions, or conclusions | Issue #10 | Only tool outputs (Read, Grep, Bash results) and file contents are maskable |
| R3 | Preserve the most recent tool outputs verbatim -- only mask older observations | Issue #10 | "Most recent" defined per tool output type within current conversation |
| R4 | Replace masked content with structured placeholders: `[file contents: path, N lines, read at turn M]` | Issue #10 | Placeholder must contain enough metadata to re-read if needed |
| R5 | Reserve Distillator for deliberate cross-phase artifact compression (spec -> Cal, ADR -> Colby) when artifacts exceed ~5K tokens | Issue #10, pipeline-orchestration.md gate 6 | Gate 6 scope narrows from "any compression" to "cross-phase artifact handoff only" |
| R6 | Brain serves as external memory for masked observations -- recoverable via `agent_search` | Issue #10 | Brain-available path: captured content is searchable. Brain-unavailable path: masking still works, recovery is manual (re-read file) |
| R7 | All changes target `source/` only (not `.claude/`) | context-brief.md | Dual tree convention |
| R8 | This is a non-code ADR -- changes are to Eva's rules, pipeline operations docs, and Distillator persona clarification | context-brief.md | Skip Roz test spec/authoring; Colby implements, Roz verifies against ADR |
| R9 | Masking rules must be mechanical procedures in Eva's operational docs, not behavioral suggestions | brain-context (behavioral constraints lesson), MEMORY.md | "Behavioral constraints are consistently ignored" -- masking must be procedural |
| R10 | Distillator is NOT removed -- persona file stays, gate 6 is refined, not eliminated | constraints | Distillator's role narrows to cross-phase compression of large artifacts |

### Retro Risks

| Lesson | Risk to this feature | Mitigation |
|--------|---------------------|------------|
| #004 (Hung process retry loop) | Distillator invocation can hang on routine compression; masking avoids this for within-session cases | Masking is purely textual substitution within Eva's context -- no subagent invocation, no process to hang |
| Behavioral constraints ignored (brain lesson) | Eva might skip masking or mask inconsistently if rules are phrased as guidance | Write masking rules as a numbered mechanical procedure in `pipeline-operations.md` with explicit trigger conditions, not as advice |
| #005 (Frontend wiring omission) | If masking removes a tool output that a later agent needs, wiring breaks silently | Masking preserves the placeholder with metadata (path, line count, turn number). Agent can re-read if needed. Most recent outputs always preserved verbatim. |

## Context

Eva's context window is the pipeline's bottleneck. As the central orchestrator, Eva accumulates tool outputs from every agent interaction: file reads, grep results, bash outputs, git diffs. Most of this content is consumed once (to make a routing decision) and then sits in the context window as dead weight, consuming tokens and degrading attention quality.

The current strategy has two mechanisms:
1. **Distillator** (gate 6) compresses upstream artifacts exceeding ~5K tokens before passing to downstream agents. This is a subagent invocation (Haiku model) that produces lossless distillates.
2. **Context Cleanup Advisory** suggests fresh sessions after 10 major agent handoffs.

Neither addresses the primary waste: Eva's own accumulated tool outputs from earlier in the same session. A file read from turn 3 that informed a routing decision at turn 4 remains verbatim in context through turn 40. This is the observation masking target.

JetBrains research (December 2025) found that simple placeholder substitution matched or exceeded LLM summarization quality in 4 of 5 settings, was 52% cheaper per session, and avoided a subtle failure mode where summarization obscures stopping signals (causing agents to run 15% longer). The research validates the approach: for within-session context, mechanical masking beats intelligent compression.

**Key distinction:** Observation masking handles within-session tool output cleanup in Eva's own context window. Distillator handles cross-phase artifact compression when passing large documents between agents (spec to Cal, ADR to Colby). These are complementary, not competing.

### Spec Challenge

**The spec assumes** that Claude Code provides an API or mechanism for Eva to replace prior tool outputs in her own context window with placeholder text. If this is wrong (because the conversation history is immutable and Eva cannot retroactively modify tool output blocks), the design fails because masking would require a workaround such as summarizing before the output enters context, which defeats the simplicity advantage.

**Resolution:** Claude Code's conversation model does allow the orchestrating agent to control what content persists. Eva constructs subagent invocations and processes their returns -- she controls what she carries forward by choosing what to include in her own working notes versus what to let fall to conversation history. The masking procedure operates at the point where Eva decides what to carry: when updating `pipeline-state.md` and preparing the next invocation, Eva records structured placeholders instead of copying full outputs. The mechanism is not retroactive mutation of context -- it is forward-looking discipline about what Eva writes into her state files and invocation prompts.

**SPOF:** Eva's masking procedure itself. **Failure mode:** If Eva fails to apply masking (skips the procedure, applies it inconsistently, or masks content that should be preserved), the pipeline either wastes tokens (no masking) or loses information (over-masking). **Graceful degradation:** Failure to mask = status quo (no worse than current behavior, just no improvement). Over-masking is recoverable because placeholders contain re-read metadata (file path, line count) and brain captures provide searchable history. The worst case is Eva re-reading a file she already read, not data loss.

## Decision

Introduce observation masking as a mechanical context hygiene procedure in Eva's operational rules. Masking replaces within-session tool outputs with structured placeholders while preserving all agent reasoning text. Distillator's role narrows from "any compression" to "cross-phase artifact compression of large documents."

### Masking Rules (Mechanical Procedure)

Eva applies these rules after processing each tool output and before composing the next invocation or state update. The rules are ordered by priority:

**Never mask (preserved verbatim):**
1. All agent reasoning, analysis, decisions, and conclusions -- any text an agent produced as output (not tool output)
2. The most recent instance of each unique file read (keyed by file path)
3. The most recent Bash output for each distinct command
4. The most recent Grep result for each distinct query
5. Any tool output referenced in an active BLOCKER or MUST-FIX finding
6. Content of `pipeline-state.md` and `context-brief.md` (always-live state)

**Mask (replace with placeholder):**
1. File read outputs superseded by a more recent read of the same path
2. Tool outputs from completed pipeline phases (e.g., Robert's spec exploration outputs after Cal has the ADR)
3. Verbose Bash outputs (build logs, test suite outputs) after Eva has extracted the verdict
4. Git diff outputs after Roz and Poirot have completed their review of that unit

**Placeholder format:**
```
[masked: {tool} {target}, {size} lines, turn {N}. Re-read: {recovery_command}]
```

Examples:
- `[masked: Read source/rules/agent-system.md, 482 lines, turn 3. Re-read: Read source/rules/agent-system.md]`
- `[masked: Bash npm test, 147 lines, turn 12. Re-read: run test suite again]`
- `[masked: Grep "Distillator" source/, 35 matches, turn 5. Re-read: Grep "Distillator" source/]`

### Brain Integration (when brain_available: true)

Before masking a tool output, Eva captures a summary to the brain if the content informed a decision:
- `agent_capture` with `thought_type: 'observation'`, `source_agent: 'eva'`, content: one-line summary of what was learned from the output, metadata: `{ masked_at_turn: N, original_tool: 'Read', target: 'path/to/file' }`
- This makes masked observations recoverable via `agent_search` in future sessions

When brain is unavailable, masking still applies. Recovery path is manual re-read using the placeholder's recovery command.

### Revised Gate 6 (Distillator Scope)

Gate 6 changes from:

> **Distillator compresses upstream artifacts when they exceed ~5K tokens.** Before passing upstream artifacts (spec, UX doc, ADR) to a downstream agent, Eva checks total token count. If >5K tokens, Eva MUST invoke Distillator first.

To:

> **Distillator compresses cross-phase artifacts when they exceed ~5K tokens.** Before passing upstream artifacts (spec, UX doc, ADR) to a downstream agent at a phase boundary, Eva checks total token count. If >5K tokens, Eva MUST invoke Distillator first. Within-session tool outputs (file reads, grep results, bash outputs) are handled by observation masking, not Distillator. Distillator is reserved for structured document compression where lossless preservation of decisions, constraints, and relationships matters.

### Masking Trigger Points

Eva applies masking at these mechanical trigger points (not discretionary):

1. **Before each subagent invocation:** Mask all tool outputs from prior phases that are not in the current invocation's READ list
2. **After processing a subagent's return:** Mask the invocation prompt and raw return output, preserving only the structured verdict (PASS/FAIL, findings list, DoD)
3. **After each phase transition:** Mask all tool outputs from the completed phase
4. **At the context cleanup advisory threshold** (10 major handoffs): Apply aggressive masking -- preserve only pipeline-state.md content, context-brief.md, and the current phase's active tool outputs

## Alternatives Considered

### Alternative A: Status Quo (Distillator for Everything)

Keep using Distillator for all compression, including within-session context cleanup.

**Pros:**
- No changes needed
- Distillator produces lossless, validated output

**Cons:**
- Distillator invocation costs a subagent context window (Haiku tokens) for every compression
- Distillator can hang (retro lesson #004), adding latency and retry risk
- Distillator is overkill for "this file read from 20 turns ago is no longer relevant"
- JetBrains research shows summarization obscures stopping signals, causing 15% longer agent runs
- 52% more expensive than mechanical masking for the same or worse quality

**Rejected because:** Using a subagent for routine within-session cleanup is a category error. Distillator's strength is lossless preservation of decisions and constraints in structured documents. Replacing old grep output with a placeholder requires no judgment.

### Alternative B: Aggressive Compaction (Summarize Everything)

Have Eva produce running summaries of all observations, replacing both tool outputs and agent reasoning with compressed summaries.

**Pros:**
- Maximum context savings
- A single mechanism for all context management

**Cons:**
- Loses agent reasoning text, which contains the decision trail
- Summarization by Eva is itself an LLM judgment call -- subject to hallucination and information loss
- JetBrains research explicitly warns against summarizing agent reasoning (obscures stopping signals)
- No recovery path for over-summarized content (unlike placeholders with re-read metadata)

**Rejected because:** Agent reasoning is the most valuable content in context. Summarizing it loses the "why" behind decisions. The spec explicitly requires preserving all agent reasoning verbatim.

### Alternative C: Turn-Based TTL (Mask Everything Older Than N Turns)

Simple time-based rule: any tool output older than N turns gets masked, regardless of relevance.

**Pros:**
- Extremely simple to implement
- Fully mechanical, no judgment needed

**Cons:**
- Might mask a file read from 2 turns ago that is still the most recent read of that path
- Does not account for outputs referenced by active findings
- Requires tuning N, which varies by pipeline size

**Rejected because:** The "most recent instance per path" rule (chosen approach) is equally mechanical but more precise. It avoids masking content that is still the best available version while aggressively masking truly superseded outputs.

## Consequences

### Positive

- **Immediate cost reduction:** Fewer tokens consumed per session (~30-50% reduction in Eva's context for medium/large pipelines, based on JetBrains research extrapolation)
- **Better attention quality:** Less noise in context means Eva's routing and triage decisions are more accurate
- **Fewer Distillator invocations:** Within-session compression no longer requires a subagent call, reducing latency and hang risk
- **Preserved decision trail:** All agent reasoning stays verbatim, maintaining auditability
- **Recoverable masking:** Placeholders contain re-read commands; brain captures provide searchable history

### Negative

- **New procedure for Eva to follow:** Masking rules add procedural overhead to Eva's orchestration. Risk of inconsistent application exists (mitigated by making rules mechanical, not discretionary)
- **No mechanical enforcement:** Unlike hooks that block tool calls, masking is a behavioral procedure. There is no PreToolUse hook that can enforce "Eva must mask before invoking." The brain lesson about behavioral constraints being ignored applies here. **Finding:** If masking discipline degrades in practice, a future ADR should explore a hook-based enforcement mechanism (e.g., context size check before Agent invocations)
- **Placeholder noise:** Masked placeholders are not zero-cost -- they still consume tokens. On very long sessions, hundreds of placeholders could themselves become noise. The context cleanup advisory (fresh session recommendation) remains the backstop.

### Anti-Goals

1. **Anti-goal: Retroactive context mutation.** Reason: Claude Code's conversation history is append-only. Designing against the assumption that Eva can delete or overwrite prior tool outputs in the conversation log would require platform changes outside our control. Revisit: if Claude Code introduces a context management API that allows retroactive redaction.

2. **Anti-goal: Masking subagent context windows.** Reason: Subagents already get fresh context per invocation (brain lesson). Observation masking applies only to Eva's orchestrator context, which is the actual bottleneck. Revisit: if a future architecture gives subagents persistent context across invocations.

3. **Anti-goal: Automated masking aggressiveness tuning.** Reason: The rules are static and mechanical by design. Adding a feedback loop that adjusts masking aggressiveness based on context usage metrics introduces complexity and judgment where the spec explicitly wants simplicity. Revisit: if pipeline telemetry shows masking is consistently too aggressive or too conservative across multiple projects.

## Blast Radius

### Files Modified

| File | Change | Scope |
|------|--------|-------|
| `source/references/pipeline-operations.md` | Add `<protocol id="observation-masking">` section with full masking procedure | New section in context hygiene area |
| `source/rules/pipeline-orchestration.md` | Revise gate 6 wording to scope Distillator to cross-phase artifacts only; add masking reference | Lines 153-161 (gate 6 text) |
| `source/agents/distillator.md` | Update "How Distillator Fits the Pipeline" section to clarify cross-phase-only scope | Lines 87-98 |
| `source/references/invocation-templates.md` | Add masking examples to invocation template notes; no template structure change | Near existing distillator templates (~line 400) |

### Files NOT Modified (verified no change needed)

| File | Reason |
|------|--------|
| `source/rules/agent-system.md` | Distillator remains in the agent roster. No architectural change to agent system. |
| `source/rules/pipeline-models.md` | Distillator stays Haiku. No model changes. |
| `source/hooks/enforce-paths.sh` | No new agents, no new write paths. Masking is Eva behavior, not a hook. |
| `source/rules/default-persona.md` | Eva's tool list unchanged. Masking is a procedure, not a new tool. |
| `source/references/dor-dod.md` | Distillator DoR/DoD entries unchanged -- Distillator still exists with same interface. |
| `source/references/agent-preamble.md` | No shared behavior changes. |

### Consumers of Modified Content

| Producer (modified) | Consumer | Impact |
|---------------------|----------|--------|
| Gate 6 (pipeline-orchestration.md) | Eva (orchestrator) | Eva's decision tree for "invoke Distillator or not" changes: within-session -> mask, cross-phase artifact -> Distillator |
| Context hygiene (pipeline-operations.md) | Eva (orchestrator) | Eva gains a new mandatory procedure at each trigger point |
| Distillator persona (distillator.md) | Eva (invoker) | Eva's invocation frequency for Distillator decreases (fewer routine calls) |
| Invocation templates | Eva (orchestrator) | Eva has masking examples to follow when composing invocations |

## Implementation Plan

### Step 1: Add Observation Masking Protocol to Pipeline Operations

**Files to modify:**
- `source/references/pipeline-operations.md` -- add new `<protocol id="observation-masking">` section after the existing `<section id="context-hygiene">` section

**What to add:**
- Full masking procedure with the "Never mask" and "Mask" rule lists from the Decision section
- Placeholder format specification with examples
- Trigger points (before subagent invocation, after processing return, after phase transition, at cleanup threshold)
- Brain integration procedure (capture before masking when brain available)
- Recovery procedure (re-read from placeholder metadata)

**Also update in same file:**
- Existing `<section id="context-hygiene">` Compaction Strategy: add bullet referencing observation masking as the primary within-session mechanism, positioned before the Distillator reference
- "What Eva Carries vs. What Subagents Carry" table: add row for "Masked observations" (Eva: placeholders with re-read metadata; Subagents: Never -- they get fresh context)

**Acceptance criteria:**
- Masking protocol is a numbered mechanical procedure, not advisory prose
- All four trigger points are listed with explicit conditions
- Placeholder format matches the spec: `[masked: {tool} {target}, {size} lines, turn {N}. Re-read: {recovery_command}]`
- Brain capture-before-mask procedure is conditional on `brain_available: true`
- Recovery via re-read is documented for brain-unavailable path
- Context hygiene section references masking as the primary within-session mechanism

**Estimated complexity:** Low. Additive content only -- no existing content removed.

### Step 2: Revise Gate 6 and Add Distillator Scope Clarification

**Files to modify:**
- `source/rules/pipeline-orchestration.md` -- revise gate 6 text (lines 153-161)
- `source/agents/distillator.md` -- revise "How Distillator Fits the Pipeline" section (lines 87-98)
- `source/references/invocation-templates.md` -- add a note to Distillator templates clarifying when to invoke Distillator vs. when masking handles it (near line 400)

**What to change in gate 6:**
- Change title from "Distillator compresses upstream artifacts" to "Distillator compresses cross-phase artifacts"
- Add clause: "Within-session tool outputs (file reads, grep results, bash outputs) are handled by observation masking (see pipeline-operations.md), not Distillator."
- Preserve all existing Distillator behavior for cross-phase artifact compression (>5K token threshold, VALIDATE on first run)

**What to change in distillator.md:**
- Update "How Distillator Fits the Pipeline" to state: "Eva invokes Distillator for cross-phase artifact compression when upstream documents (spec, UX doc, ADR) exceed ~5K tokens. Within-session tool outputs (file reads, grep results, bash command output) are handled by Eva's observation masking procedure -- Distillator is not invoked for these."
- Integration points list stays the same (after Robert, after Cal, after large outputs)

**What to change in invocation-templates.md:**
- Add a brief note above the Distillator templates: "Eva invokes Distillator only for cross-phase artifact compression. Within-session tool outputs are handled by observation masking (see pipeline-operations.md `<protocol id="observation-masking">`)."

**Acceptance criteria:**
- Gate 6 clearly distinguishes cross-phase artifacts (Distillator) from within-session tool outputs (masking)
- Distillator persona's pipeline integration section reflects narrowed scope
- Invocation templates include the scope clarification note
- No Distillator capabilities are removed -- only the trigger scope is narrowed
- Existing VALIDATE flow is unchanged

**Estimated complexity:** Low. Wording changes to existing sections; no structural changes.

## Comprehensive Test Specification

### Step 1 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0011-001 | Happy | Masking protocol section exists in `pipeline-operations.md` within or adjacent to the context hygiene section, with protocol id `observation-masking` |
| T-0011-002 | Happy | "Never mask" list contains all 6 categories from ADR Decision: agent reasoning, most recent file read per path, most recent Bash per command, most recent Grep per query, active BLOCKER/MUST-FIX referenced outputs, pipeline-state.md and context-brief.md |
| T-0011-003 | Happy | "Mask" list contains all 4 categories: superseded file reads, completed phase outputs, verbose Bash after verdict extraction, git diff after review completion |
| T-0011-004 | Happy | Placeholder format matches spec: `[masked: {tool} {target}, {size} lines, turn {N}. Re-read: {recovery_command}]` with at least 3 examples (Read, Bash, Grep) |
| T-0011-005 | Happy | All 4 trigger points documented: before subagent invocation, after processing return, after phase transition, at cleanup threshold |
| T-0011-006 | Happy | Brain integration procedure is conditional: capture before masking only when `brain_available: true`; uses `thought_type: 'observation'` |
| T-0011-007 | Happy | Recovery procedure documented for brain-unavailable path: re-read using placeholder metadata |
| T-0011-008 | Happy | Context hygiene Compaction Strategy updated with observation masking reference as primary within-session mechanism |
| T-0011-009 | Happy | "What Eva Carries" table includes masked observations row (Eva: placeholders; Subagents: Never) |
| T-0011-010 | Boundary | Masking rules are phrased as numbered mechanical steps (imperative), not advisory prose ("Eva should consider...") |
| T-0011-011 | Failure | If the masking protocol section is missing the trigger points subsection, verification fails -- trigger points are mandatory for mechanical enforcement |
| T-0011-012 | Failure | If placeholder format omits the re-read recovery command, verification fails -- recovery path is a requirement |
| T-0011-013 | Regression | Existing context hygiene content (Compaction Strategy, "What Eva Carries" table, Agent Teams context notes) is preserved -- masking is additive |
| T-0011-014 | Regression | Existing brain prefetch protocol is unchanged -- masking does not alter `agent_search` behavior |

### Step 2 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0011-015 | Happy | Gate 6 title or opening sentence includes "cross-phase" qualifier distinguishing Distillator scope from masking |
| T-0011-016 | Happy | Gate 6 contains explicit clause stating within-session tool outputs are handled by observation masking, not Distillator |
| T-0011-017 | Happy | Gate 6 preserves: >5K token threshold, VALIDATE on first run, mechanical (not discretionary) enforcement |
| T-0011-018 | Happy | Distillator persona "How Distillator Fits the Pipeline" section states cross-phase-only scope and references observation masking for within-session outputs |
| T-0011-019 | Happy | Invocation templates include scope clarification note above Distillator templates referencing observation masking protocol |
| T-0011-020 | Failure | If gate 6 removes the >5K token threshold or VALIDATE requirement, verification fails -- these are preserved behaviors |
| T-0011-021 | Failure | If Distillator persona file loses any content from Compress, Strip, or Preserve rules, verification fails -- compression mechanics are unchanged |
| T-0011-022 | Regression | Distillator remains listed in: agent-system.md agent roster, pipeline-models.md (Haiku), enforce-paths.sh core agent list, dor-dod.md, agent-preamble.md information asymmetry list |
| T-0011-023 | Regression | All 3 integration points in Distillator persona (after Robert, after Cal, after large outputs) remain documented |
| T-0011-024 | Boundary | Grep `source/` for "Distillator" -- all references remain valid after changes (no dangling references to removed scope) |

### Step 1 Telemetry

- **Telemetry:** Log line "Masking [N] observations from phase [phase]" at each trigger point. **Trigger:** Eva applies masking procedure. **Absence means:** Masking procedure is being skipped (behavioral drift).
- **Telemetry:** Brain capture count for `thought_type: 'observation'` per pipeline. **Trigger:** Eva captures before masking. **Absence means:** Brain integration for masking is not firing (when brain is available).

### Step 2 Telemetry

- **Telemetry:** Distillator invocation count per pipeline (should decrease compared to pre-masking baseline). **Trigger:** Eva invokes Distillator. **Absence means:** No cross-phase artifacts exceeded 5K tokens (normal for small pipelines, concerning for large ones).

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| Masking protocol (pipeline-operations.md) | Numbered procedure with trigger points, placeholder format spec, brain integration rules | Eva (orchestrator, reads pipeline-operations.md at pipeline start) | Step 1 |
| Revised gate 6 (pipeline-orchestration.md) | Decision tree: within-session -> mask, cross-phase artifact >5K -> Distillator | Eva (orchestrator, reads mandatory gates at pipeline start) | Step 2 |
| Distillator scope clarification (distillator.md) | Updated "How Distillator Fits" section stating cross-phase-only scope | Eva (invoker, reads persona before Distillator invocation) | Step 2 |
| Invocation template note (invocation-templates.md) | Scope note above Distillator templates | Eva (orchestrator, reads templates when composing invocations) | Step 2 |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `pipeline-operations.md` observation masking protocol | Procedure with rules, placeholders, triggers | Eva orchestrator (reads at pipeline start) | Step 1 |
| `pipeline-operations.md` context hygiene update | Updated table and compaction strategy | Eva orchestrator (reads at pipeline start) | Step 1 |
| `pipeline-orchestration.md` revised gate 6 | Narrowed Distillator trigger scope | Eva orchestrator (reads mandatory gates) | Step 2 |
| `distillator.md` updated pipeline integration | Cross-phase-only scope statement | Eva orchestrator (reads before Distillator invocation) | Step 2 |
| `invocation-templates.md` scope note | Clarification note above Distillator templates | Eva orchestrator (reads when composing invocations) | Step 2 |

No orphan producers. All modified content is consumed by Eva as part of her standard pipeline-start and invocation-composition reads.

## Notes for Colby

1. **Step 1 is the meat.** The masking protocol section in `pipeline-operations.md` should be placed immediately after the existing `<section id="context-hygiene">` closing tag -- or inside it as a new subsection. Given the section already covers Compaction Strategy and the "What Eva Carries" table, placing the masking protocol as a new `<protocol>` block within the context hygiene section is the cleanest structure. Use the XML tag convention: `<protocol id="observation-masking">`.

2. **Step 2 is surgical.** Gate 6 in `pipeline-orchestration.md` is lines 153-161. Change the title line and add one clause. Do not restructure the surrounding gates. The Distillator persona edit targets the "How Distillator Fits the Pipeline" subsection (lines 87-98 of `distillator.md`). The invocation template note goes above `<template id="distillator-compress">` at approximately line 402.

3. **Placeholder format is exact.** The placeholder format `[masked: {tool} {target}, {size} lines, turn {N}. Re-read: {recovery_command}]` is a spec -- do not paraphrase it or use a different format. Include the three examples from the Decision section.

4. **Brain `thought_type: 'observation'` is new.** The brain schema supports arbitrary `thought_type` strings. No brain schema change is needed. Eva's capture call uses the existing `agent_capture` tool with this new type value.

5. **Do not touch `.claude/` files.** All changes go to `source/`. The `.claude/` resync happens at version bump.

6. **The "Never mask" list order matters.** Item 1 (agent reasoning) is the most important -- it must be first and unambiguous. If Colby is unsure whether something is "agent reasoning" vs "tool output," the test is: did an LLM produce it (never mask) or did a tool produce it (maskable)?

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Mechanical placeholder substitution replaces routine Distillator compression | Covered | Step 1: masking protocol with numbered rules; Step 2: gate 6 narrows Distillator scope |
| R2 | Agent reasoning preserved verbatim | Covered | Step 1: "Never mask" rule 1 |
| R3 | Most recent tool outputs preserved | Covered | Step 1: "Never mask" rules 2-4 (per-path, per-command, per-query dedup) |
| R4 | Structured placeholders with metadata | Covered | Step 1: placeholder format spec with 3 examples |
| R5 | Distillator reserved for cross-phase compression | Covered | Step 2: gate 6 revision, distillator.md update, template note |
| R6 | Brain as external memory for masked observations | Covered | Step 1: brain integration procedure (capture before mask) |
| R7 | All changes in source/ only | Covered | Blast radius table shows only source/ files |
| R8 | Non-code ADR (rules/docs changes only) | Covered | No executable code, hooks, or config changes |
| R9 | Masking rules are mechanical, not behavioral | Covered | Step 1: numbered procedure with trigger points (T-0011-010 verifies) |
| R10 | Distillator not removed | Covered | Step 2: persona preserved, gate refined not eliminated (T-0011-022 verifies) |

### Architectural Decisions Not in Spec

- **"Most recent per path" dedup rule:** The spec says "preserve most recent tool outputs" without defining what "most recent" means when the same file is read multiple times. This ADR defines it as "most recent instance per unique file path" (and analogously per command/query), which is more precise and avoids masking a 2-turn-old read that is still the only read of that file.
- **Four trigger points:** The spec does not specify when masking fires. This ADR defines four explicit trigger points tied to Eva's existing mechanical gates (before invocation, after return, after phase transition, at cleanup threshold) to make masking procedural rather than discretionary.
- **`thought_type: 'observation'` for brain captures:** The spec says brain serves as external memory. This ADR introduces a new thought type for masked observations, enabling targeted `agent_search` queries filtered to recoverable observations.

### Rejected During Design

- **Turn-based TTL masking** (Alternative C): Rejected because it would mask the most recent read of a rarely-accessed file if that read happened to be old. The per-path dedup rule is equally mechanical but more precise.
- **Hook-based enforcement for masking:** Considered but deferred. No PreToolUse hook can enforce "Eva applied masking before this Agent invocation" because masking is a content-level decision, not a tool-level one. Flagged in Consequences as a future consideration if behavioral drift is observed.

### Technical Constraints Discovered

- **No retroactive context mutation.** Masking operates forward (controlling what Eva carries into state files and invocations), not backward (modifying conversation history). This is a platform constraint of Claude Code's append-only conversation model.
- **Placeholder tokens are not free.** On very long sessions, accumulated placeholders themselves consume context. The existing context cleanup advisory (fresh session at 10 handoffs) remains the backstop for this edge case.
