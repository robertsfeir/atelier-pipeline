---
name: brain-hydrate
description: Use when users want to bootstrap the brain with existing project knowledge -- reading ADRs, feature specs, UX docs, commit history, and error patterns to seed institutional memory on a project that already has artifacts on disk. Also use for incremental re-hydration after significant work outside the pipeline. Triggers on "hydrate brain", "bootstrap brain", "seed memory", "brain init", "populate brain", "import history".
---

# Atelier Brain -- Hydrate

This skill reads existing project artifacts and git history, extracts reasoning and decisions, and captures them as brain thoughts with proper types, importance scores, and relations. Run this conversationally -- present the scan results, get approval, then execute.

<gate id="extraction-principles">

## Core Principle

**Extract the WHY, never the WHAT.** Artifacts on disk are the source of truth for current state. Git is the source of truth for what changed and when. The brain captures reasoning, rejected alternatives, evolution context, and lessons -- the knowledge layer that no file or commit preserves.

**Never duplicate artifact content.** A decision thought references the ADR it came from but does not restate the ADR. A lesson thought captures the insight, not the code that was fixed.

</gate>

---

<procedure id="scan-inventory">

## Phase 1: Scan & Inventory

Before extracting anything, scan the project and present an inventory.

### Step 0: Pre-load Brain MCP Tool Schemas

Brain MCP tool schemas are deferred — the first call to any `atelier_*` or `agent_*` tool without its schema loaded fails with `InputValidationError`. Run ToolSearch once before any brain call to load the schemas up front:

```
ToolSearch query: select:mcp__plugin_atelier-pipeline_atelier-brain__atelier_stats,mcp__plugin_atelier-pipeline_atelier-brain__agent_capture,mcp__plugin_atelier-pipeline_atelier-brain__agent_search,mcp__plugin_atelier-pipeline_atelier-brain__atelier_relation,mcp__plugin_atelier-pipeline_atelier-brain__atelier_browse,mcp__plugin_atelier-pipeline_atelier-brain__atelier_trace
```

Proceed to Step 1 only after ToolSearch returns.

### Step 1: Verify Brain is Live

1. Call `atelier_stats` to confirm the brain is reachable and `brain_enabled: true`.
   - **Not reachable:** "Brain is not running. Run `/brain-setup` first."
   - **brain_enabled: false:** "Brain is disabled. Enable it with `PUT /api/config { brain_enabled: true }` or run `/brain-setup`."

2. Check current thought count. If thoughts already exist, warn:
   > "Brain already has [N] thoughts. This hydration will ADD to existing knowledge, not replace it. Duplicate detection will prevent exact re-imports. Proceed?"

### Step 2: Scan Artifacts

Scan the project for extractable sources. Use Glob and Bash to inventory:

| Source | How to find | What to count |
|--------|------------|---------------|
| ADRs | `ls docs/adrs/*.md` or `ls docs/architecture/*.md` | Number of ADR files |
| Feature specs | `ls docs/product/*.md` | Number of spec files |
| UX docs | `ls docs/ux/*.md` | Number of UX files |
| Error patterns | `cat docs/pipeline/error-patterns.md` | Number of entries |
| Context briefs | `cat docs/pipeline/context-brief.md` | Exists or not |
| Git history | `git log --oneline --since="6 months ago"` (or full history if <500 commits) | Number of significant commits |

### Step 3: Present Inventory

Present the scan results to the user:

```
Brain Hydration Scan
====================
ADRs:           [N] files in docs/adrs/
Feature specs:  [N] files in docs/product/
UX docs:        [N] files in docs/ux/
Error patterns: [N] entries
Context brief:  [exists/none]
Git commits:    [N] commits (last 6 months)

Estimated thoughts: [low]-[high]
Estimated relations: [low]-[high]

Ready to hydrate?
```

The user may exclude sources ("skip git history", "only ADRs") or adjust the time window. Respect their scope.

</procedure>

---

<protocol id="scout-fanout">

## Phase 2a: Scout Fan-Out

After the user approves the scan inventory, Eva fans out Explore+haiku scouts in parallel. Each scout reads one category of artifact files and returns raw content in a named inline block. This keeps all file reading off the main thread and off Opus.

**Invocation pattern:** `Agent(subagent_type: "Explore", model: "haiku")`. Facts only -- no extraction, no opinions. Each scout returns raw file content with clear delimiters per file.

**Dedup rule:** Each file is read by exactly one scout. No file appears in more than one scout's file set.

### Scout Categories

| Scout | Files | Block element |
|-------|-------|---------------|
| **ADR scout** | `docs/architecture/ADR-*.md` or `docs/adrs/ADR-*.md` | `<adrs>` |
| **Specs scout** | `docs/product/*.md` | `<specs>` |
| **UX scout** | `docs/ux/*.md` | `<ux-docs>` |
| **Pipeline scout** | `error-patterns.md` + `context-brief.md` | `<pipeline-artifacts>` |
| **Git scout** | `git log` output -- filter for significant commits only; if no significant commits found, returns empty | `<git-history>` |

### Scout Content Format

Each scout returns content using file delimiters:

```
=== FILE: docs/architecture/ADR-0002-team-collaboration.md ===
[full file content]
=== END FILE ===

=== FILE: docs/architecture/ADR-0005-xml-prompt-structure.md ===
[full file content]
=== END FILE ===
```

The Sonnet subagent parses these delimiters to process each file individually against the extraction rules.

### Skip Conditions

- **User excluded source type:** If the user narrowed scope (e.g., "only ADRs"), only the ADR scout fires. All other scouts are skipped.
- **Zero files in category:** If the Phase 1 scan found zero files for a category (e.g., no UX docs), that scout is skipped entirely. The Sonnet subagent skips that source type gracefully.
- **Scope-based exclusion:** If the user explicitly says "skip git history", the Git scout does not fire.

### File-Count Gate

If a single scout would read **more than 20 files**, split into multiple sub-scouts with **disjoint** (non-overlapping) file sets. Each file is assigned to exactly one sub-scout.

Example: 25 ADRs → ADR scout A (13 files) + ADR scout B (12 files). Split as evenly as possible; if the count is odd, the first sub-scout gets the larger half. Eva determines the split at fan-out time using Phase 1 inventory counts. The Sonnet subagent receives all sub-scout outputs concatenated in the same `<adrs>` element.

### Dry-Run Mode (Phase 2a)

In dry-run mode, scouts still fire normally so the user can preview what content would be extracted. Scout results are collected but not passed to a capture subagent.

### Scout Failure Handling

If a scout fails (timeout or error), Eva reports which category failed to the user. **No automatic re-invocation.** The user decides whether to proceed with partial content or abort. Consistent with retro lesson #004: hang-and-timeout failures are diagnostic information, not a trigger for re-invocation.

### Completeness Check (Gate Before Extraction)

Before invoking the Sonnet subagent, Eva verifies scout output completeness: the file count returned by each scout must match the Phase 1 inventory count for that category. If a mismatch is found, Eva reports the gap to the user before proceeding. Skipped scouts (per skip conditions above -- zero-file categories, user-excluded sources, or scope-based exclusions) are excluded from this check and do not count as mismatches.

</protocol>

---

<procedure id="extract-capture">

## Phase 2b: Extract & Capture (Sonnet Subagent)

After scouts complete and the completeness check passes, Eva invokes a **Sonnet subagent** to perform all extraction and capture work. Extraction does NOT run on the main thread.

### Invocation

**Note:** This subagent is the intentional exception to the agent-preamble rule that says subagents do not call `agent_capture` directly. Per ADR-0027, extraction is the Sonnet subagent's primary job -- it calls `agent_capture` and `agent_search` directly as its core function.

Eva invokes `Agent(model: "sonnet")` with the collected scout content in a `<hydration-content>` block:

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
- Create relations via `atelier_relation` per source extraction rules (evolves_from, triggered_by, supports, contradicts).
- User scope constraints: [injected from Phase 1]
</constraints>

<output>Progress report per source type with counts:
  [Source] Captured N decisions, N rejections, N insights. Created N relations. Skipped N (already captured).
Final totals: total captured, total skipped, total relations.</output>
```

**No shell access.** Git history commands are run by the Git scout only. The Sonnet subagent works entirely from the scout-collected content in the `<hydration-content>` block -- no filesystem reads, no shell commands.

**Dry-run mode (Phase 2b):** In dry-run mode, the Sonnet subagent must NOT call `agent_capture`. It may process the hydration content and report what WOULD be captured (counts per source type, estimated thought types), but writes zero thoughts to the brain.

### Failure Handling (SPOF)

If the Sonnet subagent fails mid-run (context exhaustion, MCP timeout, or model error), all thoughts captured so far are preserved (the brain is append-only). Eva detects the subagent failure, reports captured-vs-expected count to the user, and suggests re-running. The incremental re-hydration protocol (dedup via `agent_search`) makes re-running safe -- already-captured thoughts will be skipped automatically.

### Extraction Rules by Source Type

The Sonnet subagent follows these rules for each source type. **Do not capture verbatim text** -- synthesize the reasoning into atomic thoughts.

#### ADRs → decisions, rejections, insights

Read each ADR file. Extract:

1. **Each decision made** → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "sarah"` (architect decisions)
   - `source_phase: "design"`
   - `importance: 0.9` (architectural decisions are high-importance)
   - `thought`: One sentence summarizing the decision and its rationale. Reference the ADR: "ADR-NNNN: [decision summary]. Rationale: [why]."

2. **Each rejected alternative** → `agent_capture` with:
   - `thought_type: "rejection"`
   - `source_agent: "sarah"`
   - `source_phase: "design"`
   - `importance: 0.5`
   - `thought`: "Rejected [alternative] for [feature]. Reason: [why]. See ADR-NNNN."

3. **Spec challenges or risk call-outs** → `agent_capture` with:
   - `thought_type: "insight"`
   - `source_agent: "sarah"`
   - `source_phase: "design"`
   - `importance: 0.6`

4. **Relations**: Create `evolves_from` between decisions in the same ADR that build on each other. Create `contradicts` between a decision and its rejected alternatives (if the rejection was due to direct conflict).

#### Feature Specs → decisions, preferences

Read each spec file. Extract:

1. **Key product decisions** (scope boundaries, what's in/out, deferred items) → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "robert"` (product decisions)
   - `source_phase: "design"`
   - `importance: 0.8`

2. **User-stated preferences or constraints** → `agent_capture` with:
   - `thought_type: "preference"`
   - `source_agent: "robert"`
   - `source_phase: "design"`
   - `importance: 0.9` (user constraints are high-importance)

3. **Explicitly deferred features or open questions** → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "robert"`
   - `source_phase: "design"`
   - `importance: 0.5`
   - `thought`: "Deferred: [what]. Reason: [why]. Revisit when [condition]."

4. **Relations**: Create `triggered_by` from ADR decisions back to the spec decisions that drove them (match by feature name).

#### UX Docs → decisions, preferences

Read each UX doc. Extract:

1. **UX pattern choices** (why this layout, why this interaction model) → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "sable"` (if agent exists) or `"eva"` (fallback)
   - `source_phase: "design"`
   - `importance: 0.7`

2. **Accessibility or usability constraints** → `agent_capture` with:
   - `thought_type: "preference"`
   - `source_agent: "sable"` or `"eva"`
   - `source_phase: "design"`
   - `importance: 0.8`

3. **Relations**: Create `supports` between UX decisions and the spec decisions they implement.

#### Error Patterns → lessons

Read `docs/pipeline/error-patterns.md`. Extract each entry:

1. **Each error pattern** → `agent_capture` with:
   - `thought_type: "lesson"`
   - `source_agent: 'poirot'` (QA-discovered patterns)
   - `source_phase: "qa"`
   - `importance`: Scale by recurrence count: 1-2 occurrences → 0.5, 3-4 → 0.7, 5+ → 0.9
   - `thought`: "[Pattern type]: [description]. Recurred [N] times. Mitigation: [what works]."

#### Context Brief → preferences, corrections

Read `docs/pipeline/context-brief.md` if it exists. Extract:

1. **User corrections** → `agent_capture` with:
   - `thought_type: "correction"`
   - `source_agent: "eva"`
   - `source_phase: "review"`
   - `importance: 0.8`

2. **Stated preferences** → `agent_capture` with:
   - `thought_type: "preference"`
   - `source_agent: "eva"`
   - `source_phase: "review"`
   - `importance: 0.9`

#### Git History → insights, lessons, decisions

Git history arrives pre-collected in the `<git-history>` block from the Git scout. The Sonnet subagent reads from that block only -- no shell access, no `git log` commands.

**Filter for significant commits only.** Skip:
- Merge commits with no body
- Commits with only a subject line and no narrative body
- Automated commits (dependabot, renovate, CI)
- Commits that are purely mechanical (formatting, lint fixes)

For significant commits (those with narrative bodies explaining WHY):

1. **Architecture or design commits** → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "colby"`
   - `source_phase: "build"`
   - `importance: 0.6`
   - `thought`: Synthesize the reasoning from the commit body, not the diff.

2. **Bug fix commits with root cause explanation** → `agent_capture` with:
   - `thought_type: "lesson"`
   - `source_agent: "colby"`
   - `source_phase: "build"`
   - `importance: 0.6`
   - `thought`: "Bug: [symptom]. Root cause: [cause]. Fix: [approach]. Commit: [short hash]."

3. **Relations**: Create `triggered_by` from fix commits back to the error pattern they address (if matchable).

</procedure>

---

<section id="progress-summary">

## Phase 3: Progress & Summary

The Sonnet subagent produces a progress report per source type. Eva reads this output and presents the summary on the main thread.

### During Extraction

The Sonnet subagent reports progress after each source type:

```
[ADRs] Captured 12 decisions, 5 rejections, 3 insights. Created 4 relations.
[Specs] Captured 8 decisions, 3 preferences. Created 6 cross-references to ADR thoughts.
[UX] Captured 4 decisions, 2 preferences.
[Error patterns] Captured 7 lessons.
[Git history] Scanned 187 commits, captured 11 significant insights/lessons.
```

### Final Summary

After all sources are processed, call `atelier_stats` and present:

```
Brain Hydration Complete
========================
Thoughts captured: [N] (was [M] before hydration)
Relations created: [R]

Breakdown:
  decisions:   [n]
  rejections:  [n]
  preferences: [n]
  lessons:     [n]
  corrections: [n]
  insights:    [n]

Top themes (by thought density):
  1. [theme] — [count] thoughts
  2. [theme] — [count] thoughts
  3. [theme] — [count] thoughts

The brain now has institutional memory of your project's
decisions, rejected alternatives, lessons learned, and
user preferences. Agents will surface this context
automatically during pipeline runs.
```

</section>

---

<protocol id="incremental-rehydration">

## Incremental Re-Hydration

If the user runs `/brain-hydrate` on a project that was previously hydrated:

1. The scan phase is identical.
2. The Sonnet subagent performs dedup before each capture by calling `agent_search` with the candidate thought text (threshold 0.85):
   - **Match found (>0.85 similarity):** Skip — this knowledge is already in the brain. Log: "Skipped (already captured): [summary]"
   - **Partial match (0.7-0.85):** Capture as a new thought and create an `evolves_from` relation to the existing thought.
   - **No match (<0.7):** Capture normally.
3. The Sonnet subagent reports skip count in its progress output: "Skipped [N] thoughts already in brain."

If all candidates are already captured, the Sonnet subagent completes normally with captured=0 and reports the full skip count. Eva presents this in the Phase 3 summary.

This makes re-hydration safe to run multiple times. The brain's write-time conflict detection provides a second safety net.

</protocol>

---

<section id="scope-controls">

## Scope Controls

The user can narrow scope at any point:

| User says | Behavior |
|-----------|----------|
| "only ADRs" | Skip all other sources |
| "skip git history" | Process artifacts only |
| "since January" | Adjust git log window |
| "just docs/product/feature-x.md" | Single-file extraction |
| "dry run" | Scan and show what WOULD be captured, but don't write |

</section>

---

<gate id="hydration-guardrails">

## Guardrails

These rules are mandatory:

1. **Never capture artifact content verbatim.** The thought must be a synthesized reasoning statement, not a copy-paste. If you find yourself capturing more than 2 sentences from a single source paragraph, you're copying, not synthesizing.

2. **Never capture code.** No function signatures, no SQL schemas, no config snippets. The brain stores reasoning about code decisions, not the code itself.

3. **Never overwrite existing thoughts.** Hydration is additive. If the brain already has thoughts, hydration adds to them. It never deletes or modifies existing thoughts.

4. **Respect the write-time conflict detection.** If `agent_capture` returns a conflict warning (duplicate or candidate), log it and move on. Do not force-write.

5. **Cap single-run extraction.** Maximum 100 thoughts per hydration run. If the scan estimates more, batch: "Found ~150 extractable thoughts. I'll capture the first 100 (highest importance). Run again for the remainder."

6. **Always verify at the end.** Call `atelier_stats` after hydration to confirm thought count increased as expected.

7. **Use the correct `scope` format for `agent_capture`.** `agent_capture` takes `scope` as an **array** of dot-separated ltree strings, e.g. `["pipeline.adr-0006", "project.atelier"]` — not a bare string. Each array element is one ltree path; segments are dot-separated (`org.product.feature`). Labels may contain ASCII letters (case-sensitive), digits, underscores, and hyphens (hyphens require PostgreSQL >= 16 / ltree 1.2). Do NOT use PostgreSQL brace syntax (`{a,b}`) — that is the wire format, not the input format.

   **`agent_search` and `atelier_browse`** take `scope` as a **bare string** (a single ltree path), not an array. Pass `"pipeline.adr-0006"`, not `["pipeline.adr-0006"]`.

</gate>

---

<section id="hydration-notes">

## Important Notes

- **This skill is conversational.** Present the scan, get approval, then execute. Do not auto-run extraction without user confirmation.
- **First hydration on a new project is the primary use case.** Incremental re-hydration is the secondary use case for catching up after work done outside the pipeline.
- **Quality over quantity.** 30 high-signal thoughts are worth more than 200 noisy ones. When in doubt, skip the extraction — the brain should be a curated reasoning ledger, not a dump.
- **The user can abort at any time.** Thoughts already captured remain (they're individually valid). The brain is append-only — partial hydration is fine.

### Model Assignment

| Component | Model | Rationale |
|-----------|-------|-----------|
| Phase 1 (scan) | Opus (main thread) | Lightweight, conversational -- just Glob, shell inventory, stats |
| Phase 2a (scouts) | Haiku (Explore subagent) | File reading only, no reasoning needed |
| Phase 2b (extraction) | Sonnet (subagent) | Synthesis quality sufficient for structured extraction rules |
| Phase 3 (summary) | Opus (main thread) | Format and present results |

Scouts use `model: "haiku"` via `Agent(subagent_type: "Explore", model: "haiku")`. The capture subagent uses `model: "sonnet"` via `Agent(model: "sonnet")`.

</section>
