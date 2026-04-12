## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Replace routine Distillator compression with mechanical placeholder substitution for within-session tool outputs | ADR-0011, R1 |
| 2 | Preserve all agent reasoning text verbatim — never mask agent analysis, decisions, or conclusions | ADR-0011, R2 |
| 3 | Preserve the most recent tool output per unique key (file path, command, query) — only mask superseded outputs | ADR-0011, R3 |
| 4 | Replace masked content with structured placeholders containing enough metadata to re-read | ADR-0011, R4 |
| 5 | Reserve Distillator for cross-phase artifact compression (spec, UX doc, ADR handoffs exceeding ~5K tokens) | ADR-0011, R5 |
| 6 | Brain captures masked observations as recoverable memory (when brain is available) | ADR-0011, R6 |
| 7 | Masking rules are mechanical numbered procedures, not behavioral suggestions | ADR-0011, R9 |
| 8 | Distillator is not removed — its scope is narrowed, not eliminated | ADR-0011, R10 |

**Retro risks:** Behavioral constraints are consistently ignored in this project — masking rules must be a numbered mechanical procedure with explicit trigger points, not advisory guidance.

---

# Feature Spec: Observation Masking

**Author:** Robert (CPO) | **Date:** 2026-04-12
**Status:** Draft
**ADR:** [ADR-0011](../architecture/ADR-0011-observation-masking.md)

## The Problem

Eva's context window is the pipeline's bottleneck. As orchestrator, Eva accumulates tool outputs from every agent interaction: file reads, grep results, bash outputs, git diffs. Most of this content is consumed once to make a routing decision and then sits in the context window as dead weight, consuming tokens and degrading attention quality.

The current strategy — invoking Distillator (a Haiku-model subagent) for compression — is a category error for within-session cleanup. A file read from turn 3 that informed a routing decision at turn 4 does not require an LLM to determine it is no longer needed. Simple placeholder substitution achieves the same result at zero subagent cost.

JetBrains research (December 2025) validated the approach: mechanical placeholder substitution matched or exceeded LLM summarization quality in 4 of 5 settings, was 52% cheaper per session, and avoided a subtle failure mode where summarization obscures stopping signals (causing agents to run 15% longer).

## Who Is This For

Eva (the pipeline orchestrator). Observation masking is an Eva-internal context hygiene procedure, not a user-facing feature. The benefit to users is reduced session cost and more accurate routing decisions in long pipelines.

## Business Value

- **Cost reduction** — 30-50% fewer tokens in Eva's context window for medium and large pipelines
- **Attention quality** — less noise means Eva's routing and triage decisions improve
- **Reduced Distillator latency** — fewer subagent invocations means fewer potential hang failures
- **Preserved decision trail** — agent reasoning stays verbatim; auditability is maintained

**KPIs:**
| KPI | Measurement | Acceptance |
|-----|------------|------------|
| Distillator invocation count | Per pipeline | Decreases vs. pre-masking baseline for medium/large pipelines |
| Eva context window size | Token count at trigger points | Measurably reduced vs. unmasked baseline |
| Decision trail preservation | Agent reasoning present in context | 100% of agent reasoning text retained |

## Personas

**Eva (orchestrator):** Applies the masking procedure at four mechanical trigger points during every pipeline. Eva does not invoke Distillator for within-session tool outputs. She records placeholders instead of copying full outputs into invocations and state files.

**Pipeline operator:** Does not interact with masking directly. Benefits are lower cost and fewer Distillator timeouts. The masked placeholder format (`[masked: Read path/to/file, 42 lines, turn 3. Re-read: Read path/to/file]`) is visible in pipeline logs but never in user-facing output.

## Acceptance Criteria

**Masking rules (what Eva MUST preserve verbatim):**
- AC-1: Eva MUST NOT mask any text produced by an agent as its reasoning, analysis, decisions, or conclusions — only tool outputs (Read, Grep, Bash results) and file contents are maskable.
- AC-2: Eva MUST preserve the most recent Read output for each unique file path. A file read from turn 3 is preserved until a newer read of the same path is available.
- AC-3: Eva MUST preserve the most recent Bash output for each distinct command string.
- AC-4: Eva MUST preserve the most recent Grep result for each distinct query string.
- AC-5: Eva MUST NOT mask any tool output referenced in an active BLOCKER or MUST-FIX finding.
- AC-6: Eva MUST NOT mask `pipeline-state.md` or `context-brief.md` content — these are always-live state files.

**Masking rules (what Eva MUST replace with placeholders):**
- AC-7: Eva MUST replace file Read outputs that have been superseded by a more recent read of the same path.
- AC-8: Eva MUST replace tool outputs from completed pipeline phases (e.g., Robert's spec exploration outputs after Cal has the ADR).
- AC-9: Eva MUST replace verbose Bash outputs (build logs, test suite runs) after Eva has extracted the pass/fail verdict.
- AC-10: Eva MUST replace git diff outputs after Roz and Poirot have completed their review of that unit.

**Placeholder format:**
- AC-11: Every masked observation MUST use the exact format: `[masked: {tool} {target}, {size} lines, turn {N}. Re-read: {recovery_command}]`
  - Example (file): `[masked: Read source/rules/agent-system.md, 482 lines, turn 3. Re-read: Read source/rules/agent-system.md]`
  - Example (bash): `[masked: Bash npm test, 147 lines, turn 12. Re-read: run test suite again]`
  - Example (grep): `[masked: Grep "Distillator" source/, 35 matches, turn 5. Re-read: Grep "Distillator" source/]`

**Trigger points (when Eva MUST apply masking):**
- AC-12: Eva MUST apply masking before each subagent invocation — masking all tool outputs from prior phases not in the current invocation's read list.
- AC-13: Eva MUST apply masking after processing each subagent return — masking the invocation prompt and raw return, preserving only the structured verdict.
- AC-14: Eva MUST apply masking after each phase transition — masking all tool outputs from the completed phase.
- AC-15: At the context cleanup advisory threshold (10 major handoffs), Eva MUST apply aggressive masking — preserving only pipeline-state.md content, context-brief.md, and the current phase's active tool outputs.

**Brain integration:**
- AC-16: When brain is available and Eva is about to mask a tool output that informed a decision, Eva MUST call `agent_capture` with `thought_type: 'observation'` BEFORE masking, recording a one-line summary of what was learned.
- AC-17: When brain is unavailable, Eva MUST apply masking. Recovery path MUST be manual re-read using the placeholder's recovery command. Eva MUST NOT skip masking due to brain unavailability.

**Distillator scope boundary:**
- AC-18: Eva MUST NOT invoke Distillator for within-session tool outputs (file reads, grep results, bash outputs). Distillator is invoked only for cross-phase artifact compression when upstream documents (spec, UX doc, ADR) exceed ~5K tokens at a phase boundary.
- AC-19: The existing Distillator `>5K token threshold` and VALIDATE-on-first-run behavior MUST remain unchanged for cross-phase artifacts.

## Edge Cases

**Masking failure (Eva skips procedure):** The pipeline continues with more context than optimal — same as current behavior, no regression. Over-masking is recoverable because placeholders contain re-read metadata.

**Same file read multiple times:** Only the most recent read is preserved. Earlier reads of the same path are masked even if they were read very recently, unless they are the only read of that path.

**Brain goes down mid-pipeline:** Eva continues masking without brain captures. The brain capture-before-mask step is conditional on `brain_available: true`. Brain failure does not interrupt masking.

**Very long sessions with many placeholders:** Placeholders themselves consume tokens. The existing context cleanup advisory (recommend fresh session at 10 major handoffs) remains the backstop for extreme sessions.

**Anti-goal — retroactive context mutation:** Masking operates forward (controlling what Eva writes into state files and invocation prompts), not backward. Claude Code's conversation history is append-only.

**Anti-goal — masking subagent context windows:** Subagents get fresh context per invocation. Masking applies only to Eva's orchestrator context.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Mechanical placeholder substitution replaces routine Distillator compression | Done | Masking procedure documented in pipeline-operations.md with numbered rules and four trigger points |
| 2 | Agent reasoning preserved verbatim | Done | "Never mask" rule 1: only tool outputs are maskable |
| 3 | Most recent tool outputs preserved per unique key | Done | "Never mask" rules 2-4: per-path, per-command, per-query dedup |
| 4 | Structured placeholders with metadata | Done | Placeholder format spec with three concrete examples |
| 5 | Distillator reserved for cross-phase compression | Done | Gate 6 in pipeline-orchestration.md narrowed to cross-phase artifacts |
| 6 | Brain as external memory for masked observations | Done | Brain integration procedure: capture before mask when brain_available |
| 7 | Masking rules are mechanical, not behavioral | Done | Numbered procedure with explicit trigger conditions in pipeline-operations.md |
| 8 | Distillator not removed | Done | Distillator persona preserved; scope narrowed, not eliminated |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled — no TBD, no placeholders
