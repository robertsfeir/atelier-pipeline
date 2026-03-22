---
name: brain-hydrate
description: Use when users want to bootstrap the brain with existing project knowledge -- reading ADRs, feature specs, UX docs, commit history, retro lessons, and error patterns to seed institutional memory on a project that already has artifacts on disk. Also use for incremental re-hydration after significant work outside the pipeline. Triggers on "hydrate brain", "bootstrap brain", "seed memory", "brain init", "populate brain", "import history".
---

# Atelier Brain -- Hydrate

This skill reads existing project artifacts and git history, extracts reasoning and decisions, and captures them as brain thoughts with proper types, importance scores, and relations. Run this conversationally -- present the scan results, get approval, then execute.

## Core Principle

**Extract the WHY, never the WHAT.** Artifacts on disk are the source of truth for current state. Git is the source of truth for what changed and when. The brain captures reasoning, rejected alternatives, evolution context, and lessons -- the knowledge layer that no file or commit preserves.

**Never duplicate artifact content.** A decision thought references the ADR it came from but does not restate the ADR. A lesson thought captures the insight, not the code that was fixed.

---

## Phase 1: Scan & Inventory

Before extracting anything, scan the project and present an inventory.

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
| Retro lessons | `cat .claude/references/retro-lessons.md` or `cat source/references/retro-lessons.md` | Number of lessons |
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
Retro lessons:  [N] entries
Context brief:  [exists/none]
Git commits:    [N] commits (last 6 months)

Estimated thoughts: [low]-[high]
Estimated relations: [low]-[high]

Ready to hydrate?
```

The user may exclude sources ("skip git history", "only ADRs") or adjust the time window. Respect their scope.

---

## Phase 2: Extract & Capture

Process each source type in order. For each artifact, read the full file, then use LLM reasoning to extract thoughts. **Do not capture verbatim text** -- synthesize the reasoning into atomic thoughts.

### Extraction Rules by Source Type

#### ADRs → decisions, rejections, insights

Read each ADR file. Extract:

1. **Each decision made** → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "cal"` (architect decisions)
   - `source_phase: "design"`
   - `importance: 0.9` (architectural decisions are high-importance)
   - `thought`: One sentence summarizing the decision and its rationale. Reference the ADR: "ADR-NNNN: [decision summary]. Rationale: [why]."

2. **Each rejected alternative** → `agent_capture` with:
   - `thought_type: "rejection"`
   - `source_agent: "cal"`
   - `source_phase: "design"`
   - `importance: 0.5`
   - `thought`: "Rejected [alternative] for [feature]. Reason: [why]. See ADR-NNNN."

3. **Spec challenges or risk call-outs** → `agent_capture` with:
   - `thought_type: "insight"`
   - `source_agent: "cal"`
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
   - `source_agent: "roz"` (QA-discovered patterns)
   - `source_phase: "qa"`
   - `importance`: Scale by recurrence count: 1-2 occurrences → 0.5, 3-4 → 0.7, 5+ → 0.9
   - `thought`: "[Pattern type]: [description]. Recurred [N] times. Mitigation: [what works]."

#### Retro Lessons → lessons, corrections

Read `.claude/references/retro-lessons.md` (or `source/references/retro-lessons.md`). Extract each lesson:

1. **Each lesson** → `agent_capture` with:
   - `thought_type: "lesson"` (general lessons) or `"correction"` (if the lesson corrects a prior approach)
   - `source_agent: "eva"` (retro lessons are pipeline-level)
   - `source_phase: "review"`
   - `importance: 0.7`

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

Run `git log --format="%H|%s|%b" --since="6 months ago"` (adjust window per user).

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

---

## Phase 3: Progress & Summary

### During Extraction

Report progress after each source type:

```
[ADRs] Captured 12 decisions, 5 rejections, 3 insights. Created 4 relations.
[Specs] Captured 8 decisions, 3 preferences. Created 6 cross-references to ADR thoughts.
[UX] Captured 4 decisions, 2 preferences.
[Error patterns] Captured 7 lessons.
[Retro lessons] Captured 5 lessons, 2 corrections.
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

---

## Incremental Re-Hydration

If the user runs `/brain-hydrate` on a project that was previously hydrated:

1. The scan phase is identical.
2. Before each capture, the skill calls `agent_search` with the candidate thought text (threshold 0.85).
   - **Match found (>0.85 similarity):** Skip — this knowledge is already in the brain. Log: "Skipped (already captured): [summary]"
   - **Partial match (0.7-0.85):** Capture as a new thought and create an `evolves_from` relation to the existing thought.
   - **No match (<0.7):** Capture normally.
3. Report skip count in the summary: "Skipped [N] thoughts already in brain."

This makes re-hydration safe to run multiple times. The brain's write-time conflict detection provides a second safety net.

---

## Scope Controls

The user can narrow scope at any point:

| User says | Behavior |
|-----------|----------|
| "only ADRs" | Skip all other sources |
| "skip git history" | Process artifacts only |
| "since January" | Adjust git log window |
| "just docs/product/feature-x.md" | Single-file extraction |
| "dry run" | Scan and show what WOULD be captured, but don't write |

---

## Guardrails

These rules are mandatory:

1. **Never capture artifact content verbatim.** The thought must be a synthesized reasoning statement, not a copy-paste. If you find yourself capturing more than 2 sentences from a single source paragraph, you're copying, not synthesizing.

2. **Never capture code.** No function signatures, no SQL schemas, no config snippets. The brain stores reasoning about code decisions, not the code itself.

3. **Never overwrite existing thoughts.** Hydration is additive. If the brain already has thoughts, hydration adds to them. It never deletes or modifies existing thoughts.

4. **Respect the write-time conflict detection.** If `agent_capture` returns a conflict warning (duplicate or candidate), log it and move on. Do not force-write.

5. **Cap single-run extraction.** Maximum 100 thoughts per hydration run. If the scan estimates more, batch: "Found ~150 extractable thoughts. I'll capture the first 100 (highest importance). Run again for the remainder."

6. **Always verify at the end.** Call `atelier_stats` after hydration to confirm thought count increased as expected.

---

## Important Notes

- **This skill is conversational.** Present the scan, get approval, then execute. Do not auto-run extraction without user confirmation.
- **First hydration on a new project is the primary use case.** Incremental re-hydration is the secondary use case for catching up after work done outside the pipeline.
- **Quality over quantity.** 30 high-signal thoughts are worth more than 200 noisy ones. When in doubt, skip the extraction — the brain should be a curated reasoning ledger, not a dump.
- **The user can abort at any time.** Thoughts already captured remain (they're individually valid). The brain is append-only — partial hydration is fine.
