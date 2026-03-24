# ADR-0004: Pipeline Evolution — Borrowed Principles from Ruflo v3 and GSD

## DoR: Requirements Extracted

**Source:** Competitive analysis of Ruflo v3 (formerly Claude Flow) and GSD (Get Shit Done) plugin, evaluated against atelier-pipeline v1.7.4 architecture. User-directed: all 9 concepts to be drafted for team evaluation. Brain integration assessed per step.

| # | Requirement | Source | Brain Integration |
|---|-------------|--------|-------------------|
| 0 | Refactor Eva's rules into identity (always-loaded) + operations (path-scoped) | Anthropic docs: <200 lines/file, path-scoped rules | No — structural prerequisite |
| 1 | Robert-skill supports assumptions-mode for brownfield features | GSD discuss mode | Yes — Brain supplies prior decisions + patterns as assumption seed |
| 2 | New `thought_type: 'pattern'` in Brain schema for reusable implementation patterns | Ruflo ReasoningBank | Yes — core schema change |
| 3 | Wave-based parallel execution of independent ADR build units | GSD wave execution | Yes — Brain captures dependency graph decisions for future pipelines |
| 4 | Micro-tier sizing below Small for purely mechanical changes | Ruflo WASM fast-path | No — Brain irrelevant for renames and import fixes |
| 5 | Triage consensus matrix codifying reviewer × severity → action | Ruflo consensus mechanisms | Yes — Brain captures triage outcomes, surfaces patterns in recurring disagreements |
| 6 | Per-unit commits during build phase, squash on merge to main | GSD atomic commits | No — commit granularity is a git workflow concern |
| 7 | Task-level model routing for Colby based on unit complexity | Ruflo adaptive routing | Yes — Brain tracks model-vs-outcome data for future tuning |
| 8 | Structured research step in Cal's ADR flow for Large pipelines | GSD research phase | Yes — Brain surfaces prior research findings and architectural patterns |
| 9 | Seed capture system for out-of-scope ideas with trigger conditions | GSD seed system | Yes — Brain already covers 70%, needs explicit `thought_type: 'seed'` |

**Retro risks:**
- "Self-Reporting Bug Codification" lesson: Steps that add Brain schema changes (2, 9) must have Roz verify the migration before Colby builds features on top of it.
- "Sensitive Data in Return Shapes" lesson: Pattern captures (Step 2) may contain code snippets — ensure no secrets leak into Brain content.

## Status

Proposed — each step independently evaluable, independently implementable.

## Context

Two external multi-agent orchestration systems — Ruflo v3 and GSD — employ architectural principles absent from atelier-pipeline. Rather than adopting either system wholesale (they solve different problems), this ADR extracts 9 discrete concepts that strengthen Atelier's core thesis of correctness and institutional learning without introducing new runtime dependencies.

**Design constraint:** Every step must work within the existing Claude Code plugin architecture (no daemon, no WASM, no npm dependencies beyond Brain's Node.js server). Every step must preserve the 10 mandatory gates. Steps are ordered by impact, not dependency — the team can pick any subset.

**Brain-first principle:** Robert's directive is to consciously leverage the Brain where it sharpens a concept. Each step's Brain Integration section is not optional decoration — it's a design decision about whether persistent memory makes the concept meaningfully better. "No" is a valid answer.

### Spec Challenge

The risk is scope creep: 9 steps that each seem small but collectively change Eva's orchestration behavior, the Brain schema, Robert-skill's UX, the invocation template, the model selection table, and the sizing rules. If this is wrong — if the interactions between steps create emergent complexity — the design fails because Eva's always-loaded context (default-persona.md + agent-system.md) grows beyond the point where she can reliably execute it. **Mitigation:** Step 0 is a hard prerequisite that restructures Eva's rules files using Claude Code's native path-scoped rules ([Anthropic docs: "Organize rules with .claude/rules/"](https://code.claude.com/docs/en/memory#organize-rules-with-clauderules)). This splits identity (always-loaded, ~350 lines total) from operations (path-scoped to `docs/pipeline/**`, loaded only during active pipelines). Steps 1-9 add features to the path-scoped operational file, not the always-loaded identity files. Each step is self-contained and independently adoptable.

---

## Decision

Implement 10 enhancements: 1 structural prerequisite (Step 0) + 9 independent feature steps organized by impact tier. Step 0 is a hard dependency for all other steps. Steps 1-9 include a Brain integration assessment and an explicit "changes to existing files" section so the team can evaluate blast radius before approving.

---

## Implementation Plan

### Step 0: Eva Context Refactor — Identity vs. Operations Split (PREREQUISITE)

**Origin:** [Anthropic Claude Code documentation](https://code.claude.com/docs/en/memory) — "target under 200 lines per CLAUDE.md file," path-scoped rules load only when matching files are opened, and rules files survive `/compact` (re-injected fresh from disk).

**Problem:** Eva's always-loaded rules total 883 lines across 3 files (`default-persona.md`: 281, `agent-system.md`: 560, `CLAUDE.md`: 42). Anthropic's guidance says adherence degrades above 200 lines per file. `agent-system.md` at 560 lines is nearly 3× the recommended ceiling. Adding ADR-0004's 9 features to these files would push total always-loaded context past 1,200 lines — well into the zone where Claude starts "forgetting" earlier instructions ([Best Practices](https://code.claude.com/docs/en/best-practices): "Bloated CLAUDE.md files cause Claude to ignore your actual instructions!").

**Why path-scoped rules, not JIT Read:** Content loaded via the `Read` tool enters the conversation context and gets summarized (potentially lossy) on `/compact`. Rules files are re-injected from disk after compaction — they survive intact. For Eva's operational procedures (the 10 mandatory gates, phase transitions, triage logic), lossy summarization is unacceptable. Path-scoped rules give us JIT loading WITH compaction resilience.

**Brain integration: No.** This is a structural prerequisite. No Brain reads or writes.

**What changes:** Eva's rules split into four files using Claude Code's native [path-scoped rules](https://code.claude.com/docs/en/memory#organize-rules-with-clauderules):

#### File 1: `default-persona.md` (always-loaded, ~150 lines)

Keeps Eva's **identity and constraints** — who she is, what she never does:

| Section | Lines | Status |
|---------|-------|--------|
| Preamble + What This Means | 31 | Stays |
| Always-Loaded Context | 8 | Stays |
| Session Boot Sequence | 20 | Stays |
| Forbidden Actions | 46 | Stays |
| Cognitive Independence | 14 | Stays |
| Routing Transparency | 5 | Stays |
| What This Does NOT Mean | 8 | Stays |

**Moves OUT:**
- Brain Access (37 lines) → `pipeline-orchestration.md` (operational, only needed during pipeline)
- Mandatory Gates (87 lines) → `pipeline-orchestration.md` (these are pipeline enforcement rules)
- Investigation Discipline (25 lines) → `pipeline-orchestration.md` (debug-flow operational procedure)

Note: `default-persona.md` retains a 3-line stub for each moved section: "See `pipeline-orchestration.md` for [section name]. Loaded automatically when pipeline is active." This ensures Eva knows the rules exist even in casual mode — she just doesn't carry their full weight until she needs them.

#### File 2: `agent-system.md` (always-loaded, ~200 lines)

Keeps **architecture, routing, and agent identity** — what Eva needs for every session:

| Section | Lines | Status |
|---------|-------|--------|
| Brain Configuration | 22 | Stays |
| Architecture (skill + subagent tables) | 26 | Stays |
| Eva §1 Orchestration & Traffic Control | 10 | Stays |
| Eva §2 State & Context Management | 23 | Stays |
| Eva §3 Quality & Learning | 16 | Stays |
| Auto-Routing Rules (intent + confidence) | 44 | Stays |
| Subagent Invocation (template) | 30 | Stays |
| Custom Commands table | 39 | Stays |
| Shared Agent Behaviors | 19 | Stays |

**Moves OUT:**
- Eva §4 Subagent Invocation/DoR/DoD (61 lines) → `pipeline-orchestration.md`
- Pipeline Flow: all prose (Spec Requirement, ADR Immutability, Stakeholder gate, Review juncture, Reconciliation, Hard pauses — ~124 lines) → `pipeline-orchestration.md`
- Pipeline Flow: keeps ONLY the Sizing table and Phase Transitions lookup table (~50 lines) for auto-routing
- Mockup + UAT (9 lines) → `pipeline-orchestration.md`
- What Lives on Disk (18 lines) → `pipeline-orchestration.md`
- Context Hygiene (7 lines) → `pipeline-orchestration.md`
- Agent Standards (42 lines) → `pipeline-orchestration.md`

`agent-system.md` retains a one-line reference: "See `pipeline-orchestration.md` for detailed operational procedures. Loaded when pipeline state files are accessed."

#### File 3: `pipeline-orchestration.md` (path-scoped, ~350 lines)

New file. Contains everything Eva needs when **actively orchestrating a pipeline**:

```yaml
---
paths:
  - "docs/pipeline/**"
---
```

**Contents (moved from existing files + new ADR-0004 additions):**

| Section | Source | Lines |
|---------|--------|-------|
| Mandatory Gates (10 gates) | default-persona.md | 87 |
| Brain Access + Capture Model | default-persona.md | 37 |
| Investigation Discipline + Layer Escalation | default-persona.md | 25 |
| Pipeline Flow (prose: Spec Requirement, ADR Immutability, Stakeholder gate, Review juncture, Reconciliation, Hard pauses) | agent-system.md | 124 |
| Eva §4: DoR/DoD Verification + UX Pre-flight + Cross-agent constraints | agent-system.md | 61 |
| Agent Standards (BLOCKER/MUST-FIX/DRIFT rules, mock data prohibition) | agent-system.md | 42 |
| Mockup + UAT Phase | agent-system.md | 9 |
| What Lives on Disk | agent-system.md | 18 |
| Context Hygiene reference | agent-system.md | 7 |
| **ADR-0004 additions land here:** | | |
| Triage Consensus Matrix (Step 5) | new | ~50 |
| Wave Execution rules (Step 3) | new | ~40 |
| Per-unit commit flow (Step 6) | new | ~20 |

This file loads when Eva reads `docs/pipeline/pipeline-state.md` at boot — which she does on every session with an active pipeline. On casual sessions, it never loads.

#### File 4: `pipeline-models.md` (path-scoped, ~80 lines)

New file. Lookup tables that Eva references during pipeline execution:

```yaml
---
paths:
  - "docs/pipeline/**"
---
```

**Contents:**
- Model Selection tables (from `pipeline-operations.md`, currently loaded via Read tool)
- Micro-tier criteria and safety valve (Step 4)
- Complexity classifier for Colby (Step 7)

Separating models from orchestration keeps each file focused and under 200 lines.

#### Trigger mechanics

The path-scoped trigger is `docs/pipeline/**`. Eva's boot sequence (Step 1 of Session Boot in `default-persona.md`) explicitly reads `docs/pipeline/pipeline-state.md`. This Read triggers Claude Code to load both `pipeline-orchestration.md` and `pipeline-models.md` into context. The trigger is reliable because:

1. Eva's boot sequence is in the always-loaded `default-persona.md`
2. The boot sequence mandates reading `docs/pipeline/pipeline-state.md`
3. Claude Code's path-scoped rules fire on file reads matching the glob
4. Both new files use `docs/pipeline/**` as their path scope

For brand-new pipelines (no `pipeline-state.md` yet), Eva creates the file as her first act — which also triggers the rules to load.

**Edge case:** If the user asks a casual question and Eva doesn't touch `docs/pipeline/`, the operational rules don't load. This is correct behavior — Eva in casual mode doesn't need 350 lines of pipeline procedure.

#### What `pipeline-operations.md` becomes

The existing JIT-read reference file (`pipeline-operations.md`, 192 lines) currently contains Continuous QA flow, Feedback Loops, Batch Mode, Worktree Rules, Context Hygiene details, and Model Selection tables. After the refactor:

- Model Selection tables → `pipeline-models.md` (path-scoped, compaction-resistant)
- Continuous QA flow → stays in `pipeline-operations.md` (detailed procedures, JIT-read by Eva is fine — this content is procedural, not gate-level)
- Feedback Loops, Batch Mode, Worktree Rules → stay in `pipeline-operations.md`

`pipeline-operations.md` shrinks from 192 to ~130 lines. Eva still reads it JIT at pipeline start for detailed procedures. The critical gate-level content now lives in compaction-resistant path-scoped rules.

**Files to create/modify:**
- Create: `source/rules/pipeline-orchestration.md` (with `paths: ["docs/pipeline/**"]` frontmatter)
- Create: `source/rules/pipeline-models.md` (with `paths: ["docs/pipeline/**"]` frontmatter)
- Modify: `source/rules/default-persona.md` (remove 3 sections, add stubs, target ~150 lines)
- Modify: `source/rules/agent-system.md` (remove operational sections, add reference stubs, target ~200 lines)
- Modify: `source/references/pipeline-operations.md` (remove model tables, ~130 lines)
- Mirror all changes in `.claude/` installed copies

**Acceptance criteria:**
- `default-persona.md` ≤ 160 lines
- `agent-system.md` ≤ 220 lines
- `pipeline-orchestration.md` ≤ 400 lines (with room for ADR-0004 additions)
- `pipeline-models.md` ≤ 100 lines
- No content is lost — every section traceable from source to destination
- Eva's boot sequence triggers path-scoped rules loading via `docs/pipeline/` read
- All 10 mandatory gates present in `pipeline-orchestration.md` and enforced
- `/compact` in a long pipeline session preserves gate-level rules (they're rules files, not Read-tool content)
- Casual Eva (no active pipeline) carries only identity + routing (~350 lines vs. current 883)

**Estimated complexity:** Medium. Content reorganization, no behavioral changes. Risk is mechanical — ensuring every section lands in the right file with correct cross-references.

**This step is a hard prerequisite for Steps 1-9.** Without it, adding features to the always-loaded rules files pushes Eva past the adherence threshold documented by Anthropic.

---

### Step 1: Assumptions-Mode for Robert-Skill (Brownfield Discovery)

**Origin:** GSD's discuss mode — "assumptions" strategy reads codebase first, surfaces what it would build, asks only for corrections.

**What changes:** Robert-skill (`source/commands/pm.md` and `.claude/commands/pm.md`) gains a behavioral toggle. When a feature touches existing code (Eva detects via `ls` + `grep` for existing components), Robert reads the codebase and presents his understanding before asking discovery questions. Greenfield features retain current question-first flow.

**Brain integration: Yes — high value.**
- **Read gate (Robert-skill start):** `agent_search` with query `"feature:{feature_area} type:decision OR type:preference OR type:pattern"`. Results seed Robert's assumptions. If Brain contains 3+ relevant decisions about this area, Robert *starts* in assumptions mode automatically — he already has enough context to form a position.
- **Write gate (Robert-skill end):** Robert captures his spec's key decisions as `thought_type: 'decision'`, `source_agent: 'robert'`, `source_phase: 'design'`. This is already specified in Robert's persona; no new capture gate needed.
- **Why it matters:** Without Brain, assumptions-mode only sees the codebase. With Brain, it also sees *why* the codebase looks the way it does — prior decisions, rejected alternatives, user preferences. The assumptions become dramatically better.

**Detection logic (Eva):**
```
1. ls docs/product/*{feature}*   → existing spec? → assumptions mode
2. ls {source_dir}/*{feature}*   → existing components? → assumptions mode
3. agent_search("{feature}")     → 3+ active thoughts? → assumptions mode
4. None of the above             → question mode (greenfield)
```

**Files to create/modify:**
- Modify: `source/commands/pm.md` (add assumptions-mode section, ~30 lines)
- Modify: `source/rules/default-persona.md` (add detection logic to auto-routing, ~10 lines)
- No schema changes. No new agents.

**Acceptance criteria:**
- Robert presents codebase-derived assumptions when existing components found
- Robert asks for corrections, not discovery questions, in assumptions mode
- Robert falls back to question mode when no prior code or Brain context exists
- Brain results visibly influence the assumptions (not just codebase reading)

**Estimated complexity:** Low. Behavioral change to one skill file.

---

### Step 2: Pattern Caching in Brain (`thought_type: 'pattern'`)

**Origin:** Ruflo's ReasoningBank — stores proven solution patterns so agents don't re-derive solutions they've already found.

**What changes:** Brain schema gains `thought_type: 'pattern'` with TTL of 365 days and default importance 0.7 (same tier as `lesson`). Colby gains a capture gate at DoD: "If you created a reusable pattern (pagination, auth flow, state machine, API integration), capture it." All agents with Brain read access gain a mandatory search for patterns relevant to their current task.

**Brain integration: Yes — this IS a Brain feature.**

**Schema change:**
```sql
-- Migration 003
ALTER TYPE thought_type ADD VALUE 'pattern';
INSERT INTO thought_type_config (thought_type, default_ttl_days, default_importance)
VALUES ('pattern', 365, 0.7);
```

**Capture gate (Colby DoD):**
```
If the implementation created a reusable approach:
  agent_capture({
    content: "[description of pattern + file paths + key code structure]",
    thought_type: 'pattern',
    source_agent: 'colby',
    source_phase: 'build',
    importance: 0.7,
    metadata: { files: [...], pattern_category: "pagination|auth|state|api|..." }
  })
```

**Read gate (all code-touching agents):**
- **Colby (build start):** `agent_search` with `"pattern:{task_description}"`, filter `thought_type: 'pattern'`. If results found, include in CONTEXT field: "Prior pattern found: [summary]. Reuse or explain deviation."
- **Cal (ADR production):** `agent_search` for patterns in the architectural area. Existing patterns influence the design — Cal shouldn't architect from scratch what Colby has already solved.
- **Roz (QA):** `agent_search` for patterns in the test area. If a prior pattern exists and Colby deviated without explanation, flag as MUST-FIX (pattern drift without rationale).

**Staleness mitigation:** Patterns include file paths in metadata. Eva adds a mechanical check: if `metadata.files` references files that have been significantly modified since `created_at` (>50% of lines changed per `git log --stat`), Eva marks the pattern as `status: 'invalidated'` via `agent_capture` with `supersedes_id`.

**Files to create/modify:**
- Create: `brain/migrations/003-add-pattern-type.sql`
- Modify: `source/agents/colby.md` (add Brain capture gate at DoD, ~15 lines)
- Modify: `source/agents/cal.md` (add pattern search to Brain read gate, ~5 lines)
- Modify: `source/agents/roz.md` (add pattern drift check, ~10 lines)
- Modify: `source/rules/default-persona.md` (add pattern staleness check to Eva's pipeline-end duties, ~10 lines)

**Acceptance criteria:**
- `thought_type: 'pattern'` accepted by Brain schema
- Colby captures patterns at DoD when reusable approaches are created
- Cal's `agent_search` at ADR start returns relevant patterns
- Roz flags deviation from known patterns without rationale
- Stale patterns auto-invalidated when source files change significantly

**Estimated complexity:** Medium. Schema migration + behavioral changes to 3 agent personas.

---

### Step 3: Wave-Based Parallel Build Units

**Origin:** GSD's dependency-aware execution waves — independent tasks run in parallel within a wave, dependent tasks sequence across waves.

**What changes:** Eva's build phase gains dependency analysis. After Cal's ADR is approved and Roz's test spec is ready, Eva extracts the file-level dependency graph from the ADR steps. Steps with zero file overlap are grouped into waves and executed in parallel. Steps with shared files sequence.

**Brain integration: Yes — moderate value.**
- **Write gate (Eva, after wave grouping):** `agent_capture` with `thought_type: 'decision'`, content: "ADR-NNNN wave grouping: Wave 1 [steps 1,3], Wave 2 [steps 2,4,5]. Rationale: [file overlap analysis]." This lets future pipelines on the same feature area inherit the parallelization knowledge.
- **Read gate (Eva, before wave grouping):** `agent_search` for prior wave decisions on this feature area. If a prior pipeline grouped the same kind of steps, Eva reuses the grouping as a starting point (still validates file overlap).

**Wave extraction algorithm (Eva):**
```
1. For each ADR step, extract: files_to_create, files_to_modify (from Cal's plan)
2. Build adjacency: step A depends on step B if A modifies/reads a file B creates
3. Topological sort into waves
4. Validate: git diff --name-only on each wave's steps confirms zero overlap
5. If overlap detected after Colby completes: fall back to sequential, log as lesson
```

**Constraint preservation:**
- Each wave still follows: Colby build → Roz + Poirot review (per unit within the wave)
- Roz and Poirot run independently per unit — no cross-unit review within a wave
- The final review juncture (Roz sweep + Poirot + Robert + Sable) still runs AFTER all waves complete
- Batch-mode rules still apply: parallel requires zero file overlap, sequential is the fallback

**Files to create/modify:**
- Modify: `source/references/pipeline-operations.md` (add Wave Execution section, ~40 lines)
- Modify: `source/rules/agent-system.md` (add wave grouping to Phase Transitions table, ~15 lines)
- Modify: `source/rules/default-persona.md` (add wave extraction to Eva's build-phase duties, ~20 lines)

**Acceptance criteria:**
- Eva identifies independent ADR steps via file-overlap analysis
- Independent steps execute in parallel waves
- Dependent steps sequence across waves
- All 10 mandatory gates preserved within each wave
- Fallback to sequential if overlap detected mid-execution
- Brain captures wave decisions for future reference

**Estimated complexity:** Medium-High. Eva behavioral change + new section in pipeline-operations.

---

### Step 4: Micro-Tier Sizing

**Origin:** Ruflo's WASM fast-path — skips full agent orchestration for trivial operations.

**What changes:** A new sizing tier below Small. When Eva classifies a change as purely mechanical (single-token replacement, import path fix, version bump, typo fix), the pipeline becomes: **Colby → Ellis**. Roz is skipped. No ADR, no spec, no review juncture.

**Brain integration: No.**
Micro changes are, by definition, not worth remembering. No Brain reads or writes. If a "Micro" change turns out to be non-trivial (Colby discovers complexity), Eva re-sizes to Small and the full pipeline kicks in.

**Micro classification criteria (all must be true):**
1. Change affects ≤ 2 files
2. Change is purely mechanical: rename, import path, version string, typo, formatting
3. No behavioral change to any function or component
4. No test changes needed (existing tests should still pass unchanged)
5. User explicitly says "quick fix", "just rename", "typo", or equivalent

**Safety valve:** Eva runs the full test suite after Colby's change. If ANY test fails, Eva immediately re-sizes to Small (invokes Roz). The "Micro" classification is revoked — Eva logs this in `error-patterns.md` as `mis-sized-micro` so future similar requests don't get Micro treatment.

**Updated sizing table:**

| Size | Criteria | Pipeline |
|------|----------|----------|
| **Micro** | ≤2 files, mechanical only, no behavioral change | Colby → test suite → Ellis |
| **Small** | Single file, < 3 files, bug fix | Colby → Roz → Ellis |
| **Medium** | 2-4 ADR steps | Robert → Cal → Colby ↔ Roz + Poirot → ... → Ellis |
| **Large** | 5+ ADR steps | Full pipeline |

**Files to create/modify:**
- Modify: `source/rules/agent-system.md` (add Micro to sizing table, ~15 lines)
- Modify: `source/rules/default-persona.md` (add Micro classification criteria + safety valve, ~20 lines)
- Modify: `source/references/pipeline-operations.md` (add Micro model selection: Colby=Haiku, Ellis=Sonnet, ~5 lines)

**Acceptance criteria:**
- Mechanical changes classified as Micro bypass Roz
- Full test suite still runs after Colby's change
- Test failure triggers automatic re-sizing to Small
- `mis-sized-micro` tracked in error-patterns.md
- User can override: "full ceremony" on any Micro change forces Small minimum

**Estimated complexity:** Low. Sizing table + Eva behavioral rule.

---

### Step 5: Triage Consensus Matrix

**Origin:** Ruflo's Byzantine fault-tolerant consensus — formalized multi-agent agreement protocol.

**What changes:** Eva's review juncture triage becomes mechanical instead of discretionary. A lookup table in `pipeline-operations.md` maps every combination of reviewer × severity to a specific action. Eva no longer "uses judgment" at the moment where judgment is most dangerous.

**Brain integration: Yes — high value.**
- **Write gate (Eva, after each triage):** `agent_capture` with `thought_type: 'insight'`, content: "Triage outcome: [matrix cell triggered]. Reviewers agreed/disagreed on [issue]. Action taken: [action]." This builds a dataset of how triage decisions play out.
- **Read gate (Eva, at review juncture start):** `agent_search` for prior triage insights on this feature area. If a recurring pattern exists (e.g., "Poirot consistently flags auth issues that Roz misses in this module"), Eva adds a WARN to Roz's invocation.
- **Relation gate:** When triage reveals a new cross-reviewer pattern, Eva creates `atelier_relation` linking the triage insight to the relevant error-pattern entry (`supports` or `triggered_by`).

**The matrix:**

| Roz | Poirot | Robert | Sable | Action |
|-----|--------|--------|-------|--------|
| BLOCKER | any | any | any | **HALT.** Roz BLOCKER is always authoritative. |
| any | BLOCKER | any | any | **HALT.** Eva investigates Poirot's finding. If confirmed → same as Roz BLOCKER. |
| MUST-FIX | agrees | — | — | **HIGH-CONFIDENCE.** Queue fix, Colby priority. |
| PASS | flags issue | — | — | **CONTEXT-ANCHORING MISS.** Eva investigates — Poirot caught what Roz's context biased her to miss. Treat as MUST-FIX minimum. |
| MUST-FIX | PASS | — | — | **STANDARD.** Queue fix per normal flow. |
| — | — | DRIFT | — | **HARD PAUSE.** Human decides: fix code or update spec. |
| — | — | AMBIGUOUS | — | **HARD PAUSE.** Human clarifies spec. |
| — | — | — | DRIFT | **HARD PAUSE.** Human decides: fix code or update UX doc. |
| — | — | DRIFT | DRIFT | **CONVERGENT DRIFT.** High-confidence spec/UX misalignment. Escalate to human with both reports. |
| PASS | PASS | PASS | PASS | **ADVANCE.** All clear, proceed to Agatha. |

**Escalation rule:** If the same matrix cell fires 3+ times across pipelines (tracked via Brain), Eva injects a WARN into the upstream agent's next invocation. Persistent Roz-PASS + Poirot-flags-issue on the same module → WARN to Roz: "Poirot has caught issues in this module that you've missed 3 times. Extra scrutiny warranted."

**Files to create/modify:**
- Modify: `source/references/pipeline-operations.md` (add Triage Consensus Matrix section, ~50 lines)
- Modify: `source/rules/default-persona.md` (add matrix lookup to review juncture, ~10 lines)
- Modify: `source/rules/agent-system.md` (update review juncture description to reference matrix, ~5 lines)

**Acceptance criteria:**
- Eva consults the matrix at every review juncture — no discretionary triage
- BLOCKER from any reviewer halts pipeline
- Roz-PASS + Poirot-flags triggers investigation, not dismissal
- Convergent DRIFT from Robert + Sable escalated with both reports
- Brain captures triage outcomes and surfaces patterns at 3+ recurrences

**Estimated complexity:** Low. Documentation + Eva behavioral rule.

---

### Step 6: Per-Unit Commits During Build

**Origin:** GSD's atomic commits per task — each completed task gets its own commit immediately.

**What changes:** During the build phase, Ellis commits after each Roz-verified unit instead of waiting for the final review juncture. The feature branch accumulates per-unit commits. After the review juncture passes, Ellis either: (a) preserves granular history on the feature branch and creates a merge commit to main, or (b) squashes per user preference.

**Brain integration: No.**
Commit granularity is a git workflow concern. No institutional memory value.

**Flow change:**
```
CURRENT:  Colby unit 1 → Roz pass → Colby unit 2 → Roz pass → ... → Ellis single commit
PROPOSED: Colby unit 1 → Roz pass → Ellis commit(unit 1) → Colby unit 2 → Roz pass → Ellis commit(unit 2) → ... → Ellis merge/squash
```

**Constraint preservation:**
- Ellis still handles all commits (Gate 2 preserved)
- Roz still verifies every unit before commit (Gate 1 preserved)
- Full test suite still runs between units (Gate 3 preserved)
- The final review juncture still runs after all units — but now on committed (not staged) code
- If the review juncture finds issues, Colby's fix gets its own commit + Roz verification

**Benefits:**
- `git bisect` identifies exactly which unit introduced a regression
- Session recovery is cleaner: crashed mid-pipeline, units 1-3 are committed, resume at unit 4
- Each unit's diff is smaller, making Poirot's blind review more focused

**Files to create/modify:**
- Modify: `source/references/pipeline-operations.md` (update Continuous QA section for per-unit commits, ~20 lines)
- Modify: `source/agents/ellis.md` (add per-unit commit mode vs. final commit mode, ~15 lines)
- Modify: `source/rules/default-persona.md` (add Ellis invocation after each Roz pass in build phase, ~10 lines)

**Acceptance criteria:**
- Each Roz-verified unit gets its own commit on the feature branch
- Feature branch merges to main as single merge commit (or squash per user preference)
- `git bisect` can identify failing unit
- Session recovery resumes from last committed unit
- All 10 mandatory gates preserved

**Estimated complexity:** Medium. Ellis behavioral change + Eva orchestration change.

---

### Step 7: Task-Level Model Routing for Colby

**Origin:** Ruflo's adaptive complexity routing — routes to the appropriate model tier based on task difficulty, not agent identity.

**What changes:** Colby's model assignment becomes task-aware within the existing sizing framework. On Small and Medium pipelines, Eva assesses each ADR step's complexity (file count, dependency depth, algorithmic vs. CRUD) and may promote Colby to Opus for high-complexity steps while keeping Sonnet for straightforward ones.

**Brain integration: Yes — long-term value.**
- **Write gate (Eva, after each Colby invocation):** `agent_capture` with `thought_type: 'lesson'`, content: "Colby model: [model] on [step description]. Roz verdict: [PASS/FAIL]. Issues: [count]." This builds a dataset correlating model choice with QA outcomes.
- **Read gate (Eva, before Colby invocation):** `agent_search` for prior model-outcome data on similar tasks. If Brain shows Sonnet consistently fails on a task category (e.g., state machine implementations), Eva promotes to Opus automatically.
- **Threshold:** 3+ Sonnet failures on similar tasks (similarity > 0.7 via Brain search) → auto-promote to Opus for that category.

**Complexity classifier (Eva, per ADR step):**

| Signal | Score |
|--------|-------|
| ≤ 2 files modified | +0 |
| 3-5 files modified | +1 |
| 6+ files modified | +2 |
| Creates new module/service | +2 |
| Touches auth/security | +2 |
| State machine or complex flow | +2 |
| CRUD / standard pattern | +0 |
| Brain shows Sonnet failures on similar tasks | +3 |

**Score ≥ 3 → Opus. Score < 3 → Sonnet.** Only applies to Small/Medium. Large is already all-Opus.

**Scope restriction:** This ONLY applies to Colby. Roz, Poirot, Robert-subagent, and Sable-subagent model assignments are NEVER changed. Their judgment quality is non-negotiable.

**Files to create/modify:**
- Modify: `source/references/pipeline-operations.md` (add complexity classifier table, ~25 lines)
- Modify: `source/rules/default-persona.md` (add classifier to Eva's Colby invocation logic, ~15 lines)

**Acceptance criteria:**
- Eva scores each ADR step before invoking Colby
- High-complexity steps on Small/Medium get Opus
- Low-complexity steps stay on Sonnet
- Brain captures model-vs-outcome data after each unit
- 3+ Sonnet failures on similar tasks triggers auto-promotion
- Roz/Poirot/Robert/Sable model assignments unchanged

**Estimated complexity:** Low-Medium. Eva behavioral rule + pipeline-operations update.

---

### Step 8: Structured Research Step for Large ADRs

**Origin:** GSD's parallel domain researchers — dedicated research phase before architecture decisions.

**What changes:** For Large pipelines only, Cal's ADR production gains a structured pre-research step. Before Cal writes the ADR, Eva invokes a lightweight research pass that explores the codebase for existing patterns, checks dependencies for relevant libraries, and surfaces prior architectural decisions from Brain.

**Brain integration: Yes — this is where Brain pays for itself on Large pipelines.**
- **Read gate (research step):** `agent_search` with broad queries: `"architecture:{feature_area}"`, `"pattern:{tech_stack_component}"`, `"rejection:{feature_area}"` (what was tried and rejected before). Results compiled into a research brief that Cal receives in his CONTEXT field.
- **Write gate (research step end):** `agent_capture` with `thought_type: 'insight'`, content: "Research findings for {feature}: [ecosystem patterns, library options, existing code patterns, Brain-surfaced decisions]."
- **Why it matters:** Cal currently does research AND decision-making in the same invocation. Splitting them means Cal receives pre-digested context and focuses purely on architectural judgment. Brain turns this from "read the codebase" into "read the codebase + everything we've ever decided about this area."

**Implementation — NOT a new agent:**
This is an expanded READ phase in Cal's invocation template, not a separate agent. Eva constructs the research brief by:
1. Running `grep -r` for related patterns in the codebase
2. Checking `package.json` / `requirements.txt` for relevant dependencies
3. Querying Brain for decisions, patterns, rejections, and lessons in the feature area
4. Compiling results into a structured CONTEXT section for Cal

**Files to create/modify:**
- Modify: `source/references/invocation-templates.md` (add Large ADR research brief to Cal template, ~20 lines)
- Modify: `source/rules/default-persona.md` (add research compilation to Eva's pre-Cal duties for Large, ~15 lines)

**Acceptance criteria:**
- Large pipeline Cal invocations include a research brief in CONTEXT
- Research brief contains: existing code patterns, dependency analysis, Brain-surfaced decisions
- Cal's ADR references research findings in its Alternatives Considered section
- Small/Medium pipelines unaffected

**Estimated complexity:** Low. Template expansion + Eva behavioral rule. No new agents.

---

### Step 9: Seed Capture System

**Origin:** GSD's seeds — ideas captured during early phases, resurfaced as prompts at appropriate later milestones.

**What changes:** Brain schema gains `thought_type: 'seed'` with NULL TTL (permanent) and default importance 0.5. Any agent can capture a seed when an out-of-scope idea surfaces during work. Seeds carry `metadata: { trigger_when: "{feature_area_or_keyword}" }` so they surface mechanically when a related pipeline starts.

**Brain integration: Yes — this extends an existing Brain capability.**

**Schema change:**
```sql
-- Can share migration 003 with Step 2
ALTER TYPE thought_type ADD VALUE 'seed';
INSERT INTO thought_type_config (thought_type, default_ttl_days, default_importance)
VALUES ('seed', NULL, 0.5);
```

**Capture gate (any agent, any phase):**
When an agent discovers an out-of-scope idea during work:
```
agent_capture({
  content: "[idea description]",
  thought_type: 'seed',
  source_agent: '{current_agent}',
  source_phase: '{current_phase}',
  importance: 0.5,
  metadata: {
    trigger_when: "{keyword or feature area}",
    origin_pipeline: "ADR-NNNN",
    origin_context: "[one-line: what prompted this idea]"
  }
})
```

**Surfacing gate (Eva, pipeline start):**
During Eva's boot sequence step 5 (Brain context retrieval), add: `agent_search` filtered to `thought_type: 'seed'` with query matching the current feature area. If seeds found, Eva announces: "Brain surfaced [N] seed ideas related to this area: [list]. Want to incorporate any?"

**How this differs from existing Brain:** Current `insight` and `rejection` types are retrospective — they capture what happened. Seeds are prospective — they capture what *should* happen next. The `trigger_when` metadata makes surfacing mechanical rather than dependent on embedding similarity alone.

**Files to create/modify:**
- Create: `brain/migrations/003-add-pattern-and-seed-types.sql` (combines Step 2 and Step 9 schema changes)
- Modify: `source/rules/default-persona.md` (add seed surfacing to Eva's boot sequence, ~10 lines)
- Modify: `source/rules/agent-system.md` (add seed capture as a shared agent behavior, ~10 lines)

**Acceptance criteria:**
- `thought_type: 'seed'` accepted by Brain schema
- Any agent can capture seeds during work
- Seeds surface at pipeline start when `trigger_when` matches feature area
- Eva announces seeds to user — user decides whether to incorporate
- Seeds don't expire (NULL TTL) but can be manually invalidated

**Estimated complexity:** Low. Schema migration (shared with Step 2) + behavioral additions.

---

## Comprehensive Test Specification

### Step 0 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-S0-01 | Size | `default-persona.md` ≤ 160 lines |
| T-0004-S0-02 | Size | `agent-system.md` ≤ 220 lines |
| T-0004-S0-03 | Size | `pipeline-orchestration.md` ≤ 400 lines |
| T-0004-S0-04 | Size | `pipeline-models.md` ≤ 100 lines |
| T-0004-S0-05 | Frontmatter | `pipeline-orchestration.md` has `paths: ["docs/pipeline/**"]` |
| T-0004-S0-06 | Frontmatter | `pipeline-models.md` has `paths: ["docs/pipeline/**"]` |
| T-0004-S0-07 | Completeness | All 10 mandatory gates present in `pipeline-orchestration.md` |
| T-0004-S0-08 | Trigger | Eva's boot sequence read of `docs/pipeline/pipeline-state.md` loads path-scoped rules |
| T-0004-S0-09 | Compaction | After `/compact` during active pipeline, gate-level rules still present in context |
| T-0004-S0-10 | Casual | Eva answering a question without pipeline active does NOT load operational rules |
| T-0004-S0-11 | Sync | `source/rules/` and `.claude/rules/` copies are in sync (dual-tree) |
| T-0004-S0-12 | Stubs | `default-persona.md` contains stubs referencing moved sections |

### Step 1 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-001 | Behavior | Robert enters assumptions-mode when existing components found via `ls` |
| T-0004-002 | Behavior | Robert enters question-mode when no existing components found |
| T-0004-003 | Brain | Robert's assumptions incorporate Brain decisions when 3+ relevant thoughts exist |
| T-0004-004 | Fallback | Robert falls back to question-mode when Brain unavailable |

### Step 2 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-005 | Schema | `thought_type: 'pattern'` accepted by Brain insert |
| T-0004-006 | Capture | Colby captures pattern at DoD when reusable approach created |
| T-0004-007 | Search | `agent_search` with `thought_type` filter returns patterns |
| T-0004-008 | Staleness | Pattern auto-invalidated when source files change >50% |
| T-0004-009 | QA | Roz flags deviation from known pattern without rationale |

### Step 3 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-010 | Analysis | Eva correctly identifies independent ADR steps (zero file overlap) |
| T-0004-011 | Analysis | Eva correctly sequences dependent steps (shared file overlap) |
| T-0004-012 | Execution | Independent units execute in parallel within a wave |
| T-0004-013 | Fallback | Overlap detected mid-execution triggers sequential fallback |
| T-0004-014 | Gates | All 10 mandatory gates preserved within each wave |

### Step 4 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-015 | Classification | Mechanical change (rename) classified as Micro |
| T-0004-016 | Classification | Behavioral change NOT classified as Micro even if ≤2 files |
| T-0004-017 | Safety | Test failure on Micro triggers automatic re-sizing to Small |
| T-0004-018 | Tracking | `mis-sized-micro` logged in error-patterns.md on re-sizing |
| T-0004-019 | Override | User "full ceremony" forces Small minimum on Micro change |

### Step 5 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-020 | Matrix | Roz BLOCKER halts pipeline regardless of other verdicts |
| T-0004-021 | Matrix | Poirot BLOCKER triggers investigation, not auto-halt |
| T-0004-022 | Matrix | Roz PASS + Poirot flags treated as MUST-FIX minimum |
| T-0004-023 | Matrix | Convergent DRIFT (Robert + Sable) escalated with both reports |
| T-0004-024 | Brain | Triage outcomes captured; 3+ recurring pattern triggers WARN |

### Step 6 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-025 | Commits | Each Roz-verified unit gets its own commit on feature branch |
| T-0004-026 | Merge | Feature branch merges to main as single commit (or squash) |
| T-0004-027 | Bisect | `git bisect` isolates failing unit in per-unit commit history |
| T-0004-028 | Recovery | Session resume starts from last committed unit |
| T-0004-029 | Gates | Ellis handles all commits (Gate 2), Roz verifies before each (Gate 1) |

### Step 7 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-030 | Classifier | Score ≥3 assigns Opus to Colby on Small/Medium |
| T-0004-031 | Classifier | Score <3 keeps Sonnet for Colby on Small/Medium |
| T-0004-032 | Scope | Roz/Poirot/Robert/Sable model assignments unchanged regardless of score |
| T-0004-033 | Brain | Model-vs-outcome data captured after each Colby invocation |
| T-0004-034 | Learning | 3+ Sonnet failures on similar tasks triggers auto-promotion |

### Step 8 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-035 | Research | Large pipeline Cal invocations include research brief in CONTEXT |
| T-0004-036 | Content | Research brief contains existing code patterns + dependency analysis |
| T-0004-037 | Brain | Research brief includes Brain-surfaced decisions and rejections |
| T-0004-038 | Scope | Small/Medium pipelines skip research step |

### Step 9 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0004-039 | Schema | `thought_type: 'seed'` accepted by Brain insert |
| T-0004-040 | Capture | Agent captures seed with `trigger_when` metadata |
| T-0004-041 | Surface | Eva surfaces seeds at pipeline start matching feature area |
| T-0004-042 | TTL | Seeds do not expire (NULL TTL) |
| T-0004-043 | User | Eva announces seeds and waits for user decision before incorporating |

---

## Alternatives Considered

### Alternative A: Adopt Ruflo Wholesale

Rejected. Ruflo solves throughput and cost optimization. Atelier solves correctness and institutional learning. Replacing one with the other loses the core value proposition. Cherry-picking principles is the right granularity.

### Alternative B: Adopt GSD Wholesale

Rejected. GSD's spec-driven approach overlaps significantly with Atelier's existing pipeline. Its XML prompt formatting and wave execution are interesting, but its quality gates are weaker (no information asymmetry, no TDD-first, no blind review). Cherry-picking principles is again the right granularity.

### Alternative C: Build a Hybrid Orchestrator

Rejected. A new orchestration layer that combines Ruflo's routing, GSD's waves, and Atelier's quality gates would be architecturally ambitious but would break the "27 markdown files, no daemon" value proposition. The 9 steps in this ADR achieve 80% of the benefit at 10% of the complexity.

---

## Consequences

**Positive:**
- Pipeline velocity improves (Micro tier, wave execution, assumptions-mode)
- Institutional memory deepens (pattern caching, triage learning, seed system)
- Review juncture becomes reproducible (consensus matrix)
- Session recovery improves (per-unit commits)

**Negative:**
- Eva's always-loaded context grows by ~40 lines per adopted step
- Brain schema expands (2 new thought_types)
- More capture gates = more token spend on Brain writes
- Complexity classifier (Step 7) introduces a judgment call that was previously mechanical

**Risks:**

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Micro-tier mis-classification ships buggy code | 2 | 4 | Full test suite + automatic re-sizing safety valve |
| Wave parallelism causes merge conflicts | 3 | 3 | File overlap analysis + sequential fallback |
| Pattern caching surfaces stale patterns | 3 | 2 | File-change staleness check + auto-invalidation |
| Triage matrix doesn't cover edge case | 2 | 3 | Brain captures all triage outcomes; matrix evolves |
| Assumptions-mode Robert anchors to wrong codebase signal | 2 | 2 | User corrects; Brain improves future assumptions |

---

## Notes for Colby

0. **Step 0 is a hard prerequisite.** No other step should land before the rules refactor is complete and verified. The dual-tree convention applies: changes to `source/rules/` must be mirrored to `.claude/rules/` with placeholder resolution. Verify with `diff` that installed copies match templates (modulo placeholders).
1. **Steps 2 and 9 share a migration.** Create one file: `brain/migrations/003-add-pattern-and-seed-types.sql`. Both `ALTER TYPE` commands in one migration.
2. **Step 4 (Micro) has a safety valve.** If tests fail, the pipeline re-sizes. Do NOT skip the test suite run just because it's Micro.
3. **Step 5 (Triage Matrix) is documentation, not code.** The matrix lives in `pipeline-operations.md`. Eva's behavioral change is ~10 lines in `default-persona.md`.
4. **Step 7 (Model Routing) scope is strictly Colby.** Do not add complexity classifiers for any other agent. If the PR touches Roz or Poirot model assignments, it will be rejected.
5. **Brain captures are agent-owned.** Colby captures patterns (Step 2), Eva captures triage outcomes (Step 5) and wave decisions (Step 3). Don't cross-capture.

---

## DoD: Verification Checklist

| # | Requirement | Step | Verified By |
|---|-------------|------|-------------|
| 0 | Eva rules split: identity ≤ 220 lines always-loaded, operations path-scoped | 0 | Roz: T-0004-S0-01 through T-0004-S0-12 |
| 1 | Robert assumptions-mode triggers on brownfield features | 1 | Roz: T-0004-001 through T-0004-004 |
| 2 | `thought_type: 'pattern'` in Brain schema | 2 | Roz: T-0004-005 |
| 3 | Colby captures patterns at DoD | 2 | Roz: T-0004-006 |
| 4 | Stale patterns auto-invalidated | 2 | Roz: T-0004-008 |
| 5 | Independent ADR steps execute in parallel waves | 3 | Roz: T-0004-010 through T-0004-014 |
| 6 | Micro tier classifies correctly + safety valve works | 4 | Roz: T-0004-015 through T-0004-019 |
| 7 | Triage matrix is mechanical — no Eva discretion at review juncture | 5 | Roz: T-0004-020 through T-0004-024 |
| 8 | Per-unit commits on feature branch + squash option | 6 | Roz: T-0004-025 through T-0004-029 |
| 9 | Colby model routing based on complexity score | 7 | Roz: T-0004-030 through T-0004-034 |
| 10 | Large ADR research brief compiled by Eva | 8 | Roz: T-0004-035 through T-0004-038 |
| 11 | `thought_type: 'seed'` in Brain schema + surfacing | 9 | Roz: T-0004-039 through T-0004-043 |
| 12 | All 10 mandatory gates preserved across all steps | ALL | Roz: integration sweep |
| 13 | Eva's always-loaded context stays under token budget | ALL | Eva: context measurement |
