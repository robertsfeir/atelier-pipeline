---
name: brain-hydrate
description: Use when users want to bootstrap the brain with existing project knowledge -- reading ADRs, feature specs, UX docs, commit history, and error patterns to seed institutional memory on a project that already has artifacts on disk. Also use for incremental re-hydration after significant work outside the pipeline. Triggers on "hydrate brain", "bootstrap brain", "seed memory", "brain init", "populate brain", "import history".
---

# Atelier Brain -- Hydrate

This skill reads existing project artifacts and git history, extracts reasoning and decisions, and captures them as brain thoughts with proper types, importance scores, and relations. Run this conversationally -- present the scan results, get approval, then execute.

<contract>
  <requires>
    - Brain configured via `/brain-setup`: `.claude/brain-config.json` (or personal equivalent) present with valid `database_url`, `openrouter_api_key`, and `scope`.
    - Brain reachable: `atelier_stats` returns successfully and `brain_enabled: true`.
    - Brain MCP tool schemas pre-loaded via ToolSearch (Phase 1 Step 0) before any `atelier_*` / `agent_*` call.
    - Pipeline installed: `scout` agent persona present in `.claude/agents/` (required for the Phase 2a fan-out).
    - At least one extractable source on disk: ADRs, feature specs, UX docs, `error-patterns.md`, `context-brief.md`, or git history.
  </requires>
  <produces>
    - Brain thoughts captured via `agent_capture` (types: `decision`, `rejection`, `preference`, `lesson`, `correction`, `insight`) — no per-run cap.
    - Brain relations created via `atelier_relation` (`evolves_from`, `triggered_by`, `supports`, `contradicts`).
    - Phase 3 progress and final-summary report on the main thread (counts per source type, breakdown, top themes).
  </produces>
  <invalidates />
</contract>

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

See `scout-fanout.md` for the Phase 2a scout fan-out protocol: invocation pattern, scout categories, content format, invocation template, skip conditions, file-count gate, dry-run mode, failure handling, and completeness check.

---

See `extraction.md` for the Phase 2b Extract & Capture protocol: Sonnet subagent invocation, failure handling, and extraction rules for each source type (ADRs, feature specs, UX docs, error patterns, context brief, and git history).

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

5. **Run to completion.** Hydration has no per-run cap. Extract every extractable thought from the collected scout content. Dedup via `agent_search` (0.85 threshold) handles re-runs safely — already-captured thoughts are skipped automatically.

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
| Phase 1 (scan) | opus (main thread) | Lightweight, conversational -- just Glob, shell inventory, stats |
| Phase 2a (scouts) | haiku (scout subagent — pinned via frontmatter) | File reading only, no reasoning needed |
| Phase 2b (extraction) | sonnet (subagent) | Synthesis quality sufficient for structured extraction rules |
| Phase 3 (summary) | opus (main thread) | Format and present results |

Scouts are invoked as `Agent(subagent_type: "scout")` with no `model` parameter; per ADR-0048 the model pinning (`claude-haiku-4-5-20251001`) is owned by the scout frontmatter at `source/{claude,cursor}/agents/scout.frontmatter.yml`. The Phase 2b extraction subagent (which calls `agent_capture` directly per ADR-0027) is invoked as `Agent(model: "sonnet")` and is intentionally distinct from the post-scout `synthesis` subagent registered by ADR-0048 — synthesis is read-only filter/rank/trim and cannot call `agent_capture`.

</section>
