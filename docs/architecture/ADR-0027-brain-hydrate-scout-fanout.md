# ADR-0027: Brain-Hydrate Scout Fan-Out and Model Demotion

## Status

Proposed

## DoR: Requirements Extracted

**Sources:** User task description, `skills/brain-hydrate/SKILL.md`, `source/shared/rules/pipeline-orchestration.md` (Scout Fan-out Protocol), `.claude/references/retro-lessons.md`

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Fan out Explore+haiku scouts to read all artifact files concurrently before extraction | User task | Direct instruction |
| R2 | Extraction/capture work runs on Sonnet, not Opus in the main thread | User task | "we should be setting off the hydrate in haiku or sonnet we don't need Opus" |
| R3 | Scout invocation uses `Agent(subagent_type: "Explore", model: "haiku")` -- same as pipeline protocol | pipeline-orchestration.md | Scout Fan-out Protocol, line 423 |
| R4 | Each file read by at most one scout (dedup rule) | pipeline-orchestration.md | Scout Fan-out Protocol, line 423 |
| R5 | brain-hydrate remains conversational: scan, present inventory, user approves, execute | SKILL.md | Phase 1: Scan & Inventory |
| R6 | Dedup logic preserved (agent_search at 0.85 threshold before each capture) | SKILL.md | Incremental Re-Hydration protocol |
| R7 | 100-thought cap per run preserved | SKILL.md | Guardrail #5 |
| R8 | All existing skill behavior preserved: scope controls, incremental re-hydration, guardrails | SKILL.md | Scope Controls + Guardrails sections |
| R9 | Changes target `source/shared/` and `skills/` only, never `.claude/` | User constraint | Direct instruction |
| R10 | Scout results arrive as named inline block content for the extraction agent | pipeline-orchestration.md | Scout Fan-out Protocol, line 425 |

**Retro risks:**
- Lesson #004 (Hung Process Retry Loop): Scouts reading large files could hang. Extraction agent must not sleep-poll-retry if scout returns slowly.
- Lesson #005 (Frontend Wiring Omission): Not directly applicable (no UI), but the vertical-slice principle applies -- scouts produce content, extraction agent consumes it, both defined in the same step.

## Context

The `brain-hydrate` skill is a conversational skill that Eva runs on the main thread. It reads ADRs, specs, UX docs, error patterns, retro lessons, context briefs, and git history, then extracts reasoning as brain thoughts via `agent_capture`.

Two problems:

1. **Sequential file reading on Opus.** Eva reads every artifact file one at a time on the main thread. For a project with 15 ADRs, 10 specs, and 5 UX docs, this means 30+ sequential file reads at Opus pricing before any extraction begins.

2. **Extraction on Opus.** The synthesis and `agent_capture` calls run on Opus. This work -- reading a file and extracting "decision: chose X over Y because Z" -- is well within Sonnet's capability. The extraction rules are mechanical (decision/rejection/insight/lesson with prescribed `thought_type`, `importance`, and `source_agent` values), and the thought quality bar is "one synthesized sentence, not a copy-paste."

The pipeline already has a proven pattern for cheap parallel file collection: the Scout Fan-out Protocol (Explore+haiku agents). Cal, Roz, and Colby all use it. brain-hydrate should use the same approach.

## Decision

Restructure brain-hydrate into a three-tier execution model:

1. **Phase 1 (Scan & Inventory)** -- unchanged. Eva runs this on the main thread (it's lightweight: Glob, Bash, `atelier_stats`). Remains conversational with user approval gate.

2. **Phase 2a (Scout Fan-Out)** -- NEW. After user approval, Eva fans out Explore+haiku scouts in parallel. Each scout reads one category of artifact files and returns raw content in a named inline block. Scout categories match the existing source types in SKILL.md:

   | Scout | Files | Block element |
   |-------|-------|---------------|
   | **ADR scout** | `docs/architecture/ADR-*.md` (or `docs/adrs/ADR-*.md`) | `<adrs>` |
   | **Specs scout** | `docs/product/*.md` | `<specs>` |
   | **UX scout** | `docs/ux/*.md` | `<ux-docs>` |
   | **Pipeline scout** | `error-patterns.md` + `retro-lessons.md` + `context-brief.md` | `<pipeline-artifacts>` |
   | **Git scout** | `git log` output (significant commits only) | `<git-history>` |

   Each scout is `Agent(subagent_type: "Explore", model: "haiku")`. Facts only -- no extraction, no opinions. Scouts return raw file content with clear delimiters per file. Dedup rule: each file read by exactly one scout.

   **Skip condition:** If the user narrowed scope to a single source type ("only ADRs"), only that scout fires. If a category has zero files (scan found 0 specs), that scout is skipped.

   **File-count gate:** If a single scout would read >20 files, split into multiple scouts (e.g., ADR scout A-M, ADR scout N-Z) to stay within haiku's context window. Each sub-scout handles a disjoint file set.

3. **Phase 2b (Extraction Agent)** -- NEW. Eva invokes a Sonnet subagent with the collected scout content in a `<hydration-content>` block. This subagent receives the full SKILL.md extraction rules, the `<hydration-content>` block, and the user's scope constraints. It performs:
   - Reading the scout content
   - Applying the extraction rules per source type
   - Calling `agent_capture` and `atelier_relation` for each extracted thought
   - Calling `agent_search` (0.85 threshold) before each capture for dedup
   - Respecting the 100-thought cap
   - Reporting progress per source type

   The extraction agent is `Agent(model: "sonnet")` -- a standard subagent, not Explore. It needs Write access to call MCP tools (`agent_capture`, `agent_search`, `atelier_relation`).

4. **Phase 3 (Summary)** -- mostly unchanged. Eva calls `atelier_stats` on the main thread and presents the final summary. The extraction agent's progress report feeds into this.

### Model Assignment

| Component | Model | Rationale |
|-----------|-------|-----------|
| Phase 1 (scan) | Opus (main thread) | Lightweight, conversational -- just Glob/Bash/stats |
| Phase 2a (scouts) | Haiku (Explore) | File reading only, no reasoning needed |
| Phase 2b (extraction) | Sonnet (subagent) | Synthesis quality sufficient for structured extraction rules |
| Phase 3 (summary) | Opus (main thread) | Format and present results |

### Scout Content Format

Each scout returns content with file delimiters:

```
=== FILE: docs/architecture/ADR-0002-team-collaboration.md ===
[full file content]
=== END FILE ===

=== FILE: docs/architecture/ADR-0005-xml-prompt-structure.md ===
[full file content]
=== END FILE ===
```

The extraction agent parses these delimiters to process each file individually against the extraction rules.

### Extraction Agent Prompt Shape

Eva constructs the extraction agent invocation:

```xml
<task>Extract reasoning and decisions from project artifacts into brain thoughts.
Follow the extraction rules exactly. Call agent_capture for each thought.
Call agent_search (threshold 0.85) before each capture for dedup.
Cap at 100 thoughts. Report progress per source type.</task>

<hydration-content>
  <adrs>[ADR scout output]</adrs>
  <specs>[Specs scout output]</specs>
  <ux-docs>[UX scout output]</ux-docs>
  <pipeline-artifacts>[Pipeline scout output]</pipeline-artifacts>
  <git-history>[Git scout output]</git-history>
</hydration-content>

<read>skills/brain-hydrate/SKILL.md</read>

<constraints>
- Extract the WHY, never the WHAT. Synthesize reasoning, never copy content.
- Never capture code, function signatures, SQL schemas, or config snippets.
- Respect write-time conflict detection -- if agent_capture returns conflict, skip.
- Maximum 100 thoughts per run. If more are extractable, stop and report.
- Dedup: agent_search at 0.85 before each capture. >0.85 = skip. 0.7-0.85 = new thought + evolves_from relation.
- User scope constraints: [injected from Phase 1]
</constraints>

<output>Progress report per source type with counts:
  [Source] Captured N decisions, N rejections, N insights. Created N relations. Skipped N (already captured).
Final totals: total captured, total skipped, total relations.</output>
```

## Alternatives Considered

### Alternative A: Haiku Extraction Agent (rejected)

Use Haiku for the extraction agent instead of Sonnet. Rejected because extraction requires synthesis quality: reading an ADR's "Alternatives Considered" section and producing a one-sentence rejection thought with correct rationale attribution is a judgment call. Haiku can read files (scouts), but its synthesis of "why was this rejected" would produce lower-quality thoughts. The brain is a curated reasoning ledger (SKILL.md: "Quality over quantity. 30 high-signal thoughts are worth more than 200 noisy ones"). Sonnet is the right tier.

### Alternative B: Multiple Sonnet Extraction Agents (rejected)

Fan out one extraction agent per source type (5 parallel Sonnet agents). Rejected because: (1) the 100-thought cap and dedup logic need centralized state -- parallel extractors would race on `agent_search` and could produce duplicates or exceed the cap, (2) cross-source relations (e.g., `triggered_by` from ADR decisions back to spec decisions) require seeing both sources, (3) the marginal latency improvement doesn't justify the complexity.

### Alternative C: Keep Extraction on Main Thread, Only Scouts for Reading (rejected)

Fan out scouts for file reading but keep extraction on Opus in the main thread. Rejected because this only solves half the problem. The user explicitly stated Opus is unnecessary for this work. The extraction rules are mechanical enough for Sonnet, and keeping extraction on Opus wastes cost on a batch operation that may process 30+ files.

## Consequences

**Positive:**
- Significant cost reduction: file reading moves from Opus to Haiku; extraction moves from Opus to Sonnet. For a typical hydration (25 files, ~50 thoughts), estimated savings of ~60-70% vs. current all-Opus execution.
- Faster file collection: parallel scout fan-out vs. sequential reads.
- Consistent with existing pipeline patterns (Scout Fan-out Protocol).
- No behavioral change to the user experience: scan, approve, execute, summary.

**Negative:**
- Increased orchestration complexity: Eva now coordinates scouts and a subagent instead of doing everything directly.
- Scout context window risk: if a single source category has many large files (e.g., 15 ADRs at 500 lines each), haiku scouts may hit context limits. Mitigated by the file-count gate (split at >20 files).
- Extraction agent does not have direct access to the on-disk files -- it works from scout-collected content. If a scout missed a file or truncated content, the extraction is incomplete. Mitigated by Eva verifying scout output completeness against the Phase 1 inventory before invoking the extraction agent.

**Neutral:**
- ADR immutability: this ADR does not supersede any prior ADR.
- No DB schema changes. No migration needed.
- No impact on the brain-extractor SubagentStop hook -- that hook fires on domain agent completions, not on skill execution.

## Anti-Goals

1. **Anti-goal: Real-time streaming of extraction progress to the user during Phase 2b.** Reason: The extraction agent is a subagent in its own context; streaming intermediate state to Eva's main thread would require polling or complex coordination. Revisit: If hydration runs routinely exceed 5 minutes and users report anxiety about stalled progress.

2. **Anti-goal: Automatic re-invocation of scouts on partial failure.** Reason: If a scout fails to read files, Eva should report the gap and let the user decide, not silently retry. Consistent with lesson #004 (no retry loops). Revisit: If scout failure rate exceeds 10% across projects.

3. **Anti-goal: Extending the extraction agent to also handle git history analysis.** Reason: Git history requires running `git log` commands (Bash tool), which scouts already handle. The extraction agent receives the git scout's output (pre-filtered significant commits) and extracts from that text. The extraction agent does not need Bash access. Revisit: If git history extraction quality drops because the git scout's commit filtering is too aggressive.

## Spec Challenge

The spec assumes that Sonnet has sufficient synthesis quality to extract architectural reasoning from ADRs with the same fidelity as Opus. If wrong, the design fails because the brain would accumulate low-quality thoughts (vague, missing rationale, incorrect attribution) that degrade agent performance when surfaced as `<brain-context>`. **Mitigation:** The guardrail "Never capture artifact content verbatim" + the dedup threshold act as quality filters. If Sonnet extraction quality is measurably worse, the user can re-run with narrower scope and Eva can escalate to Opus for re-extraction. The extraction rules are highly structured (prescribed `thought_type`, `importance`, `source_agent` per source type), which favors Sonnet over open-ended reasoning.

## SPOF

**SPOF: The extraction Sonnet subagent.** Failure mode: if the extraction agent fails mid-run (context exhaustion, MCP timeout, model error), all thoughts captured so far are preserved (brain is append-only), but the remaining files are unprocessed with no automatic resumption. Graceful degradation: Eva detects the failure, reports how many thoughts were captured vs. expected, and suggests "Run `/brain-hydrate` again -- dedup will skip already-captured thoughts and process the remainder." The incremental re-hydration protocol (SKILL.md) makes this safe.

## Implementation Plan

### Step 1: Scout Fan-Out and Extraction Agent Protocol in SKILL.md

**Files to modify:** `skills/brain-hydrate/SKILL.md`

**What changes:**

1. Add a new `<protocol id="scout-fanout">` section between Phase 1 (Scan & Inventory) and Phase 2 (Extract & Capture). This section defines:
   - The five scout categories (ADR, Specs, UX, Pipeline artifacts, Git history)
   - Scout invocation pattern: `Agent(subagent_type: "Explore", model: "haiku")`
   - Content format (file delimiters)
   - File-count gate (>20 files = split into sub-scouts)
   - Skip conditions (source type excluded by user, zero files found)
   - Completeness check: Eva verifies scout file counts match Phase 1 inventory before proceeding

2. Modify `<procedure id="extract-capture">` (Phase 2) to specify that extraction runs as a Sonnet subagent, not on the main thread:
   - Eva invokes `Agent(model: "sonnet")` with `<hydration-content>` block
   - The subagent receives SKILL.md extraction rules in its READ list
   - The subagent performs all `agent_capture`, `agent_search`, and `atelier_relation` calls
   - Dedup logic (agent_search at 0.85) preserved, executed by the subagent
   - 100-thought cap preserved, enforced by the subagent
   - Progress reporting format preserved (per source type)

3. Update `<section id="progress-summary">` (Phase 3) to clarify that Eva reads the extraction agent's output and presents the summary.

4. Add a note to `<section id="hydration-notes">` about model assignment: scouts are Haiku, extraction is Sonnet, scan/summary are main thread (Opus).

5. Update the `<protocol id="incremental-rehydration">` section to clarify that dedup is performed by the extraction subagent, not the main thread.

**Files to modify:** `source/shared/rules/pipeline-orchestration.md`

6. Add a row to the Scout Fan-out Protocol's Per-Agent Configuration table for brain-hydrate:

   | Agent | Block | Scouts | Skip condition |
   |-------|-------|--------|----------------|
   | **brain-hydrate** | `<hydration-content>` | ADRs (read ADR files), Specs (read spec files), UX (read UX files), Pipeline (read error-patterns + retro-lessons + context-brief), Git (run git log, filter significant commits) | Per-source skip when user excludes source type or scan finds 0 files |

**Acceptance criteria:**
- AC1: SKILL.md contains a `<protocol id="scout-fanout">` section defining 5 scout categories with Explore+haiku invocation pattern
- AC2: SKILL.md Phase 2 specifies extraction via `Agent(model: "sonnet")` subagent, not main thread
- AC3: Scout content format uses file delimiters (`=== FILE: ... ===` / `=== END FILE ===`)
- AC4: File-count gate documented: >20 files per category = split scouts
- AC5: Dedup logic (agent_search 0.85) explicitly assigned to extraction subagent
- AC6: 100-thought cap explicitly assigned to extraction subagent
- AC7: pipeline-orchestration.md Scout Fan-out table includes brain-hydrate row
- AC8: Incremental re-hydration section updated to reference subagent execution
- AC9: All existing guardrails, scope controls, and extraction rules remain intact
- AC10: Extraction agent prompt shape documented with `<hydration-content>` block structure

**Complexity:** Low-Medium (2 files, specification changes only -- no code, purely markdown skill/rule definition updates)

**Step sizing gate:**
- S1 (Demoable): "After this step, I can run `/brain-hydrate` and see scouts fan out in parallel before a Sonnet agent does extraction."
- S2 (Context-bounded): 2 files to modify.
- S3 (Independently verifiable): Yes -- Roz can verify the SKILL.md structure and pipeline-orchestration.md table update independently.
- S4 (Revert-cheap): Yes -- two file edits, one fresh invocation.
- S5 (Already small): Yes -- 2 files, one clear behavior change.

## Test Specification

### Structural Tests (Roz verifies SKILL.md content)

| ID | Category | Description |
|----|----------|-------------|
| T-0027-001 | Structure | SKILL.md contains `<protocol id="scout-fanout">` section |
| T-0027-002 | Structure | Scout-fanout protocol defines exactly 5 scout categories: ADR, Specs, UX, Pipeline, Git |
| T-0027-003 | Structure | Each scout category specifies `Agent(subagent_type: "Explore", model: "haiku")` invocation |
| T-0027-004 | Structure | Scout content format uses `=== FILE:` / `=== END FILE ===` delimiters |
| T-0027-005 | Structure | File-count gate documented: >20 files per category triggers scout splitting |
| T-0027-006 | Structure | Phase 2 (`extract-capture`) specifies `Agent(model: "sonnet")` for extraction |
| T-0027-007 | Structure | Extraction agent prompt shape includes `<hydration-content>` block with 5 child elements |
| T-0027-008 | Structure | Dedup logic (agent_search threshold 0.85) is explicitly assigned to extraction subagent, not main thread |
| T-0027-009 | Structure | 100-thought cap is explicitly assigned to extraction subagent |
| T-0027-010 | Structure | Incremental re-hydration section references subagent execution |

### Preservation Tests (existing behavior not broken)

| ID | Category | Description |
|----|----------|-------------|
| T-0027-011 | Preservation | All 7 extraction source types preserved: ADRs, Feature specs, UX docs, Error patterns, Retro lessons, Context brief, Git history |
| T-0027-012 | Preservation | All `thought_type` assignments preserved per source type (decision, rejection, insight, lesson, correction, preference) |
| T-0027-013 | Preservation | All `importance` scores preserved per extraction rule |
| T-0027-014 | Preservation | All `source_agent` assignments preserved per source type (cal, robert, sable/eva, roz, eva, colby) |
| T-0027-015 | Preservation | Scope controls table preserved: "only ADRs", "skip git history", "since January", single-file, "dry run" |
| T-0027-016 | Preservation | All 6 guardrails preserved: no verbatim, no code, no overwrite, respect conflicts, 100-cap, verify stats |
| T-0027-017 | Preservation | Conversational flow preserved: Phase 1 scan + user approval gate before Phase 2 |
| T-0027-018 | Preservation | Phase 3 summary format preserved with thought breakdown and top themes |
| T-0027-019 | Preservation | Relation types preserved: `evolves_from`, `contradicts`, `triggered_by`, `supports` |

### Failure/Edge Case Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0027-020 | Failure | Scout returns empty content (0 files in category) -- extraction agent skips that source type gracefully |
| T-0027-021 | Failure | Scout fails (timeout/error) -- Eva reports which category failed, does not retry, user decides |
| T-0027-022 | Failure | Extraction agent fails mid-run -- Eva reports captured-vs-expected count, suggests re-run |
| T-0027-023 | Edge | User narrows scope to single source -- only that scout fires, others skipped |
| T-0027-024 | Edge | User requests "dry run" -- scouts may fire (for content preview) but extraction agent does not call agent_capture |
| T-0027-025 | Edge | Category has >20 files -- scouts split into sub-scouts with disjoint file sets |
| T-0027-026 | Edge | Re-hydration: all thoughts already captured -- extraction agent reports "Skipped N, captured 0" and completes normally |
| T-0027-027 | Edge | Git scout: no significant commits found -- returns empty, extraction agent skips git source type |

### Integration Tests (pipeline-orchestration.md)

| ID | Category | Description |
|----|----------|-------------|
| T-0027-028 | Integration | pipeline-orchestration.md Scout Fan-out table contains brain-hydrate row |
| T-0027-029 | Integration | brain-hydrate scout row specifies `<hydration-content>` as block name |
| T-0027-030 | Integration | brain-hydrate scout row lists all 5 scout categories |
| T-0027-031 | Integration | brain-hydrate skip condition documented as scope-dependent |

**Test counts:** 31 total (10 structural, 9 preservation, 8 failure/edge, 4 integration). Failure tests (12) >= happy-path tests (10).

## Blast Radius

| File | Change | Risk |
|------|--------|------|
| `skills/brain-hydrate/SKILL.md` | Major restructure of Phase 2; new scout-fanout protocol section | Medium -- core skill definition |
| `source/shared/rules/pipeline-orchestration.md` | Add one row to Scout Fan-out table | Low -- additive only |
| `.cursor-plugin/skills/brain-hydrate/SKILL.md` | Sync from `skills/` (via `/pipeline-setup`) | Low -- mechanical sync |

**CI/CD impact:** None. Skill files are markdown, no build/test pipeline affected.
**Cross-service contracts:** No new contracts. `agent_capture`, `agent_search`, and `atelier_relation` MCP tools used with existing shapes -- called by extraction subagent instead of main thread.

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| Scout (Explore+haiku) | Raw file content with `=== FILE: path ===` / `=== END FILE ===` delimiters | Extraction agent (Sonnet) |
| Eva Phase 1 | Inventory counts + user scope constraints | Scout invocations + extraction agent constraints |
| Extraction agent (Sonnet) | Progress report: per-source-type captured/skipped/relation counts | Eva Phase 3 summary |
| Extraction agent (Sonnet) | `agent_capture` calls with existing thought shapes | Brain MCP server |
| Extraction agent (Sonnet) | `agent_search` calls with existing query shape | Brain MCP server |

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| Eva Phase 1 scan | File counts per category, user scope | Scout fan-out invocations | Step 1 |
| Scout (haiku) | `=== FILE: ... ===` delimited content | `<hydration-content>` block in extraction agent prompt | Step 1 |
| Eva (completeness check) | Scout file counts vs. inventory | Extraction agent invocation gate | Step 1 |
| Extraction agent | Progress report text | Eva Phase 3 summary formatter | Step 1 |
| Extraction agent | `agent_capture({thought_type, thought, ...})` | Brain MCP server (existing) | Step 1 |

No orphan producers. Every output has an explicit consumer in the same step.

## Data Sensitivity

| Method/Call | Tag | Rationale |
|-------------|-----|-----------|
| `atelier_stats` | public-safe | Returns aggregate counts only |
| `agent_search` | public-safe | Query-based read, returns thought summaries |
| `agent_capture` | auth-only | Writes to brain; requires brain to be enabled and reachable |
| `atelier_relation` | auth-only | Creates relations between thoughts; requires brain enabled |

## Notes for Colby

1. **Proven pattern:** The Scout Fan-out Protocol is already implemented and operational for Cal, Roz, and Colby. See `source/shared/rules/pipeline-orchestration.md` lines 419-445 for the exact invocation pattern. brain-hydrate adopts the same `Agent(subagent_type: "Explore", model: "haiku")` mechanism. No new infrastructure needed.

2. **SKILL.md is a specification, not code.** The changes are to a markdown file that Eva reads and follows as instructions. There is no runtime code to modify. The "implementation" is updating the skill specification so Eva follows the new protocol.

3. **Cursor sync:** After modifying `skills/brain-hydrate/SKILL.md`, run `/pipeline-setup` to sync to `.cursor-plugin/skills/brain-hydrate/SKILL.md`. The only difference between the two is the config directory reference (`.claude/` vs. `.cursor/`) on lines 47 and 168 -- the scout/extraction sections have no IDE-specific references.

4. **Extraction agent is NOT a persona agent.** It does not get a persona file in `.claude/agents/`. It is an ad-hoc subagent invoked by Eva with inline instructions (the SKILL.md extraction rules). This is consistent with how Eva uses subagents for other operational tasks.

5. **Git scout special case.** The Git scout needs Bash tool access to run `git log`. Explore agents have Bash access (they inherit all tools). The Git scout runs the `git log` command from SKILL.md Phase 2 and filters for significant commits, returning the filtered output as text content.

6. **File-count gate implementation.** When a category has >20 files, Eva splits the file list and launches multiple scouts. Example: 25 ADRs = 2 ADR scouts (13 + 12 files). Eva determines the split at fan-out time using the Phase 1 inventory counts. The extraction agent receives all sub-scout outputs concatenated in the same `<adrs>` element.

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Scout fan-out for file reading | Done | Phase 2a (Scout Fan-Out) section with 5 categories |
| R2 | Extraction on Sonnet, not Opus | Done | Phase 2b specifies `Agent(model: "sonnet")` |
| R3 | Scout invocation matches pipeline protocol | Done | `Agent(subagent_type: "Explore", model: "haiku")` specified |
| R4 | Dedup rule (each file read by one scout) | Done | Dedup rule stated in scout-fanout protocol |
| R5 | Conversational flow preserved | Done | Phase 1 unchanged, user approval gate preserved |
| R6 | Dedup logic preserved | Done | agent_search 0.85 threshold assigned to extraction subagent |
| R7 | 100-thought cap preserved | Done | Cap assigned to extraction subagent in constraints |
| R8 | All existing behavior preserved | Done | Preservation tests T-0027-011 through T-0027-019 |
| R9 | Changes target source/shared + skills only | Done | Blast radius table shows only those paths |
| R10 | Scout results as named inline block | Done | `<hydration-content>` block with child elements |

**Grep check:** TODO/FIXME/HACK/XXX in this ADR -> 0
**Template:** All sections filled -- no TBD, no placeholders
