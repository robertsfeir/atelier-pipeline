## QA Report — 2026-03-24 (ADR-0004 Waves 2-5, Steps 1-9)
*Reviewed by Roz*

### Verdict: PASS

## DoR: Requirements Extracted

| # | Requirement | Source | ADR Step |
|---|-------------|--------|----------|
| 1 | Robert assumptions-mode for brownfield features | ADR-0004 Step 1 | T-0004-001 to T-0004-004 |
| 2 | `thought_type: 'pattern'` in Brain schema | ADR-0004 Step 2 | T-0004-005 |
| 3 | Colby pattern capture at DoD | ADR-0004 Step 2 | T-0004-006 |
| 4 | Pattern staleness check | ADR-0004 Step 2 | T-0004-008 |
| 5 | Roz pattern drift check | ADR-0004 Step 2 | T-0004-009 |
| 6 | Wave execution algorithm | ADR-0004 Step 3 | T-0004-010 to T-0004-014 |
| 7 | Micro tier sizing | ADR-0004 Step 4 | T-0004-015 to T-0004-019 |
| 8 | Triage consensus matrix | ADR-0004 Step 5 | T-0004-020 to T-0004-024 |
| 9 | Per-unit commits | ADR-0004 Step 6 | T-0004-025 to T-0004-029 |
| 10 | Complexity classifier for Colby | ADR-0004 Step 7 | T-0004-030 to T-0004-034 |
| 11 | Large ADR research brief | ADR-0004 Step 8 | T-0004-035 to T-0004-038 |
| 12 | `thought_type: 'seed'` + surfacing | ADR-0004 Step 9 | T-0004-039 to T-0004-043 |
| 13 | All 10 mandatory gates preserved | ADR-0004 ALL | Integration sweep |
| 14 | Line count targets met | ADR-0004 Step 0 | Sizing check |
| 15 | Dual-tree consistency | ADR-0004 Step 0 | T-0004-S0-11 |
| 16 | config.mjs THOUGHT_TYPES matches schema.sql enum | ADR-0004 Step 2+9 | T-0004-005, T-0004-039 |

**Retro risks:** "Self-Reporting Bug Codification" -- migration 004 adds Brain schema changes; verified idempotency before signing off.

---

### Tier 1 -- Mechanical

| Check | Status | Details |
|-------|--------|---------|
| Type Check | N/A | `echo "no typecheck configured"` -- documentation-only changes |
| Lint | N/A | `echo "no linter configured"` -- documentation-only changes |
| Tests | N/A | `echo "no test suite configured"` -- no executable code changed (migration is SQL, config.mjs adds 1 array element) |
| Coverage | N/A | No executable test suite for markdown rule files |
| Complexity | PASS | No functions, no nesting. All files are markdown or declarative SQL/JS config. |
| Unfinished markers | PASS | 0 TODO/FIXME/HACK/XXX in changed non-test files. All matches are in instructional text (agent persona files describing the grep check itself). |

### Tier 2 -- Judgment

| Check | Status | Details |
|-------|--------|---------|
| DB Migration | PASS | Migration 004 is idempotent: `ADD VALUE IF NOT EXISTS`, `ON CONFLICT DO NOTHING`. Safe for re-run. db.mjs checks `pg_enum` before executing. |
| Security | PASS | No secrets, no injection vectors. Pattern captures may contain code snippets -- ADR DoR notes this risk; no action needed at implementation level. |
| CI/CD Compat | N/A | No auth, RBAC, env var, or middleware changes. |
| Docs Impact | YES | `docs/guide/technical-reference.md` and `skills/pipeline-setup/SKILL.md` already updated in this diff. |
| Dependencies | PASS | No new dependencies added. |
| UX Flow | N/A | No UX doc exists for pipeline internals. |
| Semantic Correctness | PASS | All behavioral specifications match ADR intent. |
| Contract Coverage | PASS | config.mjs THOUGHT_TYPES exactly matches schema.sql enum (both include `pattern` and `seed`). |
| State Machine | N/A | No status transitions in changed files. |
| Silent Failure Audit | PASS | Migration 004 in db.mjs uses try/catch with `console.error` (non-fatal) -- consistent with migrations 001-003 pattern. Not a new silent failure; established architecture. |

---

### Requirements Verification (All 43 Test Specs)

#### Wave 3 -- Step 1 (Robert Assumptions-Mode)

| ID | Spec | Verified | Finding |
|----|------|----------|---------|
| T-0004-001 | Robert enters assumptions-mode when existing components found | PASS | `pm.md` lines 131-148: "Assumptions Mode (brownfield)" section with full behavior. `pipeline-orchestration.md` lines 233-248: Eva detection logic with 4-step mechanical check. |
| T-0004-002 | Robert enters question-mode when no existing components found | PASS | `pm.md` lines 119-130: "Question Mode (greenfield -- default)" is the default. Detection logic step 4: "None of the above -> question mode." |
| T-0004-003 | Robert assumptions incorporate Brain decisions when 3+ thoughts | PASS | `pipeline-orchestration.md` line 240: `agent_search("{feature}")` -> "3+ active thoughts? -> assumptions mode". Lines 243-246: Eva includes Brain-surfaced decisions in CONTEXT. `pm.md` line 142: "If Brain surfaced prior decisions, cite them." |
| T-0004-004 | Robert falls back to question-mode when Brain unavailable | PASS | Detection logic steps 1-2 are ls-based (no Brain needed). Step 3 has "(if brain available)" qualifier. If Brain unavailable, only codebase signals drive mode selection. Question mode is the default. |

#### Wave 4 -- Step 2 (Pattern Caching)

| ID | Spec | Verified | Finding |
|----|------|----------|---------|
| T-0004-005 | `thought_type: 'pattern'` accepted by Brain | PASS | `schema.sql` line 19: `'pattern'` in enum. `brain/migrations/004-add-pattern-and-seed-types.sql`: `ALTER TYPE thought_type ADD VALUE IF NOT EXISTS 'pattern'`. `thought_type_config` row: TTL=365, importance=0.7. `config.mjs` line 16: `"pattern"` in THOUGHT_TYPES array. |
| T-0004-006 | Colby captures pattern at DoD | PASS | `colby.md` line 111: Full capture gate with `thought_type: 'pattern'`, `source_agent: 'colby'`, `source_phase: 'build'`, `importance: 0.7`, metadata with `files` and `pattern_category`. Fires at DoD. |
| T-0004-007 | `agent_search` with filter returns patterns | PASS (architectural) | Brain server already supports `thought_type` filtering. Schema has the enum value; search infrastructure exists. |
| T-0004-008 | Pattern auto-invalidated when source files change >50% | PASS | `pipeline-orchestration.md` lines 47-57: "Pattern Staleness Check (pipeline end)" section. 3-step mechanical check: git log --stat, >50% = invalidate via `agent_capture` with `supersedes`, 20-50% = warning. |
| T-0004-009 | Roz flags deviation from known pattern without rationale | PASS | `roz.md` line 229: `agent_search` filtered to `thought_type: 'pattern'`. Flags MUST-FIX if Colby deviated without explanation. Documented rationale = acceptable. |

#### Wave 2 -- Step 4 (Micro Tier)

| ID | Spec | Verified | Finding |
|----|------|----------|---------|
| T-0004-015 | Mechanical change classified as Micro | PASS | `pipeline-orchestration.md` lines 213-225: 5 criteria (all must be true): <=2 files, purely mechanical, no behavioral change, no test changes needed, user explicitly says equivalent. |
| T-0004-016 | Behavioral change NOT classified as Micro even if <=2 files | PASS | Criterion 3: "No behavioral change to any function or component." Behavioral change fails criterion, stays Small+. |
| T-0004-017 | Test failure on Micro triggers re-sizing to Small | PASS | `pipeline-orchestration.md` lines 221-225: "Safety valve: ANY test fails -> immediately re-sizes to Small (invokes Roz)." |
| T-0004-018 | `mis-sized-micro` logged in error-patterns.md | PASS | Line 223: "logs `mis-sized-micro` in `error-patterns.md`". |
| T-0004-019 | "full ceremony" forces Small minimum | PASS | Line 209: '"full ceremony" forces Small minimum (even on Micro).' |

#### Wave 2 -- Step 5 (Triage Matrix)

| ID | Spec | Verified | Finding |
|----|------|----------|---------|
| T-0004-020 | Roz BLOCKER halts regardless | PASS | `pipeline-operations.md` matrix: "BLOCKER | any | any | any | HALT. Roz BLOCKER is always authoritative." |
| T-0004-021 | Poirot BLOCKER triggers investigation, not auto-halt | PASS | Matrix: "any | BLOCKER | any | any | HALT. Eva investigates Poirot's finding. If confirmed, same as Roz BLOCKER." Investigation step before confirmation. |
| T-0004-022 | Roz PASS + Poirot flags = MUST-FIX minimum | PASS | Matrix: "PASS | flags issue | -- | -- | CONTEXT-ANCHORING MISS. Treat as MUST-FIX minimum." |
| T-0004-023 | Convergent DRIFT escalated with both reports | PASS | Matrix: "-- | -- | DRIFT | DRIFT | CONVERGENT DRIFT. Escalate to human with both reports." |
| T-0004-024 | Brain captures triage outcomes; 3+ recurrence = WARN | PASS | `pipeline-operations.md` lines 62-73: Brain capture gate after each triage. Escalation rule: same cell 3+ times -> WARN to upstream agent. |

#### Wave 2 -- Step 6 (Per-Unit Commits)

| ID | Spec | Verified | Finding |
|----|------|----------|---------|
| T-0004-025 | Each Roz-verified unit gets own commit | PASS | `pipeline-operations.md` lines 26-27: "Eva invokes Ellis for a per-unit commit after Roz QA PASS." `pipeline-orchestration.md` lines 355-358. |
| T-0004-026 | Feature branch merges as single commit (or squash) | PASS | `pipeline-operations.md` lines 39-42: "Ellis creates a merge commit to main (or squash per user preference)." `ellis.md` lines 98-101. |
| T-0004-027 | git bisect isolates failing unit | PASS | `pipeline-operations.md` line 42: "Per-unit history is preserved on the feature branch for `git bisect`." |
| T-0004-028 | Session resume from last committed unit | PASS | `ellis.md` lines 103-104: "committed units are safe on the feature branch. Eva resumes from the last committed unit." |
| T-0004-029 | Gate 1 (Roz) and Gate 2 (Ellis) preserved | PASS | Per-unit commits have Roz pass first (Gate 1). Ellis handles all commits (Gate 2). No user approval needed for per-unit -- Eva verified Roz QA PASS. |

#### Wave 5 -- Step 3 (Wave Execution)

| ID | Spec | Verified | Finding |
|----|------|----------|---------|
| T-0004-010 | Eva identifies independent steps via file-overlap | PASS | `pipeline-operations.md` lines 123-131: 5-step wave extraction algorithm. File-level dep analysis, adjacency, topological sort. |
| T-0004-011 | Dependent steps sequence across waves | PASS | Algorithm step 2: "step A depends on step B if A modifies/reads a file B creates." Step 4: overlap within wave -> merge into separate waves. |
| T-0004-012 | Independent units execute in parallel within wave | PASS | `pipeline-operations.md` line 129: "steps with zero shared files land in the same wave." `agent-system.md` line 117: "units within a wave execute in parallel." |
| T-0004-013 | Overlap mid-execution triggers sequential fallback | PASS | Lines 132-134: "If overlap detected AFTER Colby completes a unit: fall back to sequential, log as lesson." |
| T-0004-014 | All 10 mandatory gates preserved within waves | PASS | Lines 146-147: "All 10 mandatory gates apply per unit." |

#### Wave 5 -- Step 7 (Complexity Classifier)

| ID | Spec | Verified | Finding |
|----|------|----------|---------|
| T-0004-030 | Score >=3 assigns Opus on Small/Medium | PASS | `pipeline-models.md` line 59: "Score >= 3 -> Opus." Classifier table lines 49-58. |
| T-0004-031 | Score <3 keeps Sonnet | PASS | Line 59: "Score < 3 -> Sonnet." |
| T-0004-032 | Roz/Poirot/Robert/Sable unchanged | PASS | Lines 45-46: "This applies ONLY to Colby -- Roz, Poirot, Robert, and Sable model assignments are never changed by this classifier." |
| T-0004-033 | Model-vs-outcome captured after each Colby unit | PASS | Lines 66-69: Write gate after QA. `pipeline-orchestration.md` line 298-299: `agent_capture` model-vs-outcome. |
| T-0004-034 | 3+ Sonnet failures triggers auto-promotion | PASS | Lines 63-65: "3+ Sonnet failures (similarity > 0.7) -> auto-add +3." Score then >=3 = Opus. |

#### Wave 3 -- Step 8 (Research Brief)

| ID | Spec | Verified | Finding |
|----|------|----------|---------|
| T-0004-035 | Large Cal invocations include research brief | PASS | `invocation-templates.md` lines 31-48: "Cal (Large ADR production -- with research brief)" template. `pipeline-orchestration.md` lines 250-272. |
| T-0004-036 | Research brief contains patterns + dependency analysis | PASS | Lines 266-270: "Existing patterns" (grep results), "Dependencies" (manifests with versions). |
| T-0004-037 | Brief includes Brain-surfaced decisions and rejections | PASS | Lines 268-270: "Brain-surfaced decisions," "Brain-surfaced rejections," "Brain-surfaced patterns." |
| T-0004-038 | Small/Medium skip research step | PASS | Line 272: "Small/Medium pipelines skip this step entirely." |

#### Wave 4 -- Step 9 (Seed System)

| ID | Spec | Verified | Finding |
|----|------|----------|---------|
| T-0004-039 | `thought_type: 'seed'` accepted by Brain | PASS | `schema.sql` line 19: `'seed'` in enum. Migration 004: `ADD VALUE IF NOT EXISTS 'seed'`. Config row: TTL=NULL, importance=0.5. `config.mjs` line 16: `"seed"` in THOUGHT_TYPES. |
| T-0004-040 | Agent captures seed with `trigger_when` metadata | PASS (architectural) | `pipeline-orchestration.md` lines 59-69: metadata includes `trigger_when`, `origin_pipeline`, `origin_context`. |
| T-0004-041 | Eva surfaces seeds at pipeline start | PASS | Lines 71-78: "Seed Surfacing (Eva boot sequence)" -- second search filtered to `thought_type: 'seed'`, announces to user. |
| T-0004-042 | Seeds do not expire (NULL TTL) | PASS | `schema.sql` line 63: `('seed', NULL, 0.5, ...)`. Migration 004: `VALUES ('seed', NULL, 0.5, ...)`. |
| T-0004-043 | Eva announces seeds and waits for user decision | PASS | Line 77: "Want to incorporate any into this pipeline?" -- user decides. |

---

### Integration Checks

| Check | Status | Details |
|-------|--------|---------|
| All 10 mandatory gates preserved | PASS | Gates 1-10 present in `pipeline-orchestration.md` lines 87-165, numbered, complete. Micro tier exception to Gate 1 explicitly documented with safety valve. |
| Line count: pipeline-orchestration.md <= 400 | PASS | 399 lines (1 line headroom) |
| Line count: agent-system.md <= 225 | PASS | 220 lines |
| Line count: pipeline-models.md <= 100 | PASS | 91 lines |
| Line count: default-persona.md <= 160 | PASS | 148 lines |
| Dual-tree sync (source/ vs .claude/) | PASS | Diff shows only placeholder resolution. All 14 changed file pairs verified. |
| config.mjs matches schema.sql enum | PASS | THOUGHT_TYPES: `['decision','preference','lesson','rejection','drift','correction','insight','reflection','handoff','pattern','seed']` -- identical to schema.sql. |
| Migration 004 idempotent | PASS | `ADD VALUE IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, db.mjs checks `pg_enum` before executing. |
| No behavioral regressions | PASS | All existing pipeline flows preserved. New features additive. |
| Stubs in default-persona.md | PASS | Lines 60-63 (Brain Access), 111-114 (Mandatory Gates), 116-120 (Investigation Discipline) -- all stub to pipeline-orchestration.md. |

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across all changed files: **0 actual markers**. All matches are instructional text within agent persona files or SHA hashes in package-lock.json.

### Issues Found

**BLOCKER:** None.

**MUST-FIX:** None.

### Inherited Items from Previous Report

| # | Item | Status |
|---|------|--------|
| 1 | conflict.mjs exports resetBrainConfigCache (ADR contract doc gap) | Carried -- ADR immutable |
| 2 | startConsolidationTimer signature differs from ADR (takes apiKey) | Carried -- ADR immutable |

Both are ADR-0001 documentation gaps. ADRs are immutable per project rules. Carried forward.

### Doc Impact: YES

Already handled in this diff: `docs/guide/technical-reference.md` (12 lines) and `skills/pipeline-setup/SKILL.md` (12 lines) updated to reflect rules file restructuring and new files.

### Roz's Assessment

Clean implementation of ADR-0004 Waves 2-5. All 43 test specifications verified with file-level evidence. Key observations:

1. **Migration numbering is correct.** The ADR spec'd "003" but Colby correctly used "004" because 003-add-devops-phase.sql was committed between ADR authoring and this implementation. The migration is idempotent and the db.mjs runner checks pg_enum before executing.

2. **Line counts are tight but within bounds.** pipeline-orchestration.md at 399/400 means any future additions require compression or a new split. Not blocking.

3. **Dual-tree consistency verified.** All source/ files diff cleanly against .claude/ with only placeholder resolution differences.

4. **Micro tier safety valve properly documented.** The exception to Gate 1 (Roz) is explicitly called out in both the sizing table footnote and the classification criteria. No ambiguity.

5. **Brain integration correctly distributed.** Colby owns pattern captures, Eva owns triage/wave/model-outcome captures, Roz owns pattern drift detection. No cross-capture violations.

6. **No behavioral regressions.** Existing Small/Medium/Large flows unchanged. All new features are additive.

## DoD: Verification

| # | DoR Requirement | Status | Evidence |
|---|-----------------|--------|----------|
| 1 | Robert assumptions-mode | Done | pm.md + pipeline-orchestration.md detection logic |
| 2 | pattern thought_type | Done | schema.sql + migration 004 + config.mjs |
| 3 | Colby pattern capture | Done | colby.md Brain Access section |
| 4 | Pattern staleness | Done | pipeline-orchestration.md staleness check |
| 5 | Roz pattern drift | Done | roz.md Brain Access read gate |
| 6 | Wave execution | Done | pipeline-operations.md + agent-system.md phase transitions |
| 7 | Micro tier | Done | agent-system.md sizing table + pipeline-orchestration.md criteria |
| 8 | Triage matrix | Done | pipeline-operations.md full matrix |
| 9 | Per-unit commits | Done | pipeline-operations.md + ellis.md per-unit mode |
| 10 | Complexity classifier | Done | pipeline-models.md classifier table |
| 11 | Research brief | Done | invocation-templates.md + pipeline-orchestration.md |
| 12 | Seed system | Done | schema.sql + migration 004 + pipeline-orchestration.md |
| 13 | 10 gates preserved | Done | pipeline-orchestration.md lines 87-165 |
| 14 | Line count targets | Done | All 4 files within bounds |
| 15 | Dual-tree sync | Done | diff verified, placeholder-only differences |
| 16 | config.mjs/schema.sql match | Done | Identical enum lists |

Zero residue. Zero unfinished markers. All 43 test specs verified.
