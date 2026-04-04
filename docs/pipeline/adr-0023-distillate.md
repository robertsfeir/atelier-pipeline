---
sources:
  - path: docs/architecture/ADR-0023-agent-specification-reduction.md
    original_tokens: ~13700
compression_ratio: "41%"
token_estimate: ~5600
date: 2026-04-03
downstream_consumer: "Roz (test spec review)"
---

# ADR-0023: Agent Specification Reduction -- Distillate

## DoR: Requirements (R1-R15)

| R# | Requirement | Source |
|---|------------|--------|
| R1 | Remove procedural instructions for generic competencies Opus has from training | Audit finding |
| R2 | Remove behavioral restrictions made redundant by ADR-0022's three-layer enforcement (Layer 1: tools/disallowedTools; Layer 2: frontmatter hooks; Layer 3: global hooks) | ADR-0022 dependency |
| R3 | **RETAIN** all project-specific constraints, output formats, design principles, conventions (DoR/DoD format, contract tables, step sizing gates, TDD-first, PASS/DRIFT/MISSING/AMBIGUOUS vocabulary, information asymmetry) | Audit finding |
| R4 | Upgrade examples from generic competency demos to project-specific judgment calibration (e.g., "wrong default -> correct behavior") | Anthropic docs |
| R5 | Scale example density by model tier: Opus 0-1, Sonnet 1-2, Haiku 2 | Audit finding |
| R6 | Consolidate brain capture protocol (~28 lines) into agent-preamble.md; keep only agent-specific thought_types in personas | Audit finding |
| R7 | Move step sizing gate (S1-S5) from Cal's persona to shared reference file | Audit finding |
| R8 | Collapse invocation-templates.md: extract shared patterns to header; remove repeated brain-context XML blocks (~200 lines); remove persona-constraint duplicates (~100 lines) | Audit finding |
| R9 | Remove "How X Fits the Pipeline" sections from agent personas | Audit finding |
| R10 | Remove explicit tool lists from persona body text (frontmatter is single source of truth post-ADR-0022) | ADR-0022 dependency |
| R11 | Move deterministic boot sequence steps 1-3d to SessionStart hook script (file reads, env var checks; ~70 lines) | Audit finding |
| R12 | Fold CI Watch invocation templates (roz-ci-investigation, colby-ci-fix, roz-ci-verify) into base variants as annotations | Audit finding |
| R13 | ADR-0022 Phase 2 must complete before this work begins (mechanical enforcement prerequisite) | Sequencing constraint |
| R14 | **PRESERVE** Distillator specification density (Haiku model needs procedural guidance) | Audit + model docs |
| R15 | **PRESERVE** TDD-specific instructions for Colby and Roz regardless of model tier | Anthropic docs ("Claude's default is implementation-first") |

**Retro risks:**
- **Lesson #002:** "Do not modify Roz's assertions" — critical constraint, must survive reduction; mechanical enforcement (Roz's Write-only access) backs it
- **Lesson #003:** Boot sequence hook must follow lightweight pattern: exit 0 always, no blocking, JSON output to stdout
- **Lesson #005:** Contract tables, vertical slice preference, cross-layer wiring checks are project-specific conventions that must survive per R3

**Spec challenge:** Assumes Opus performs generic tasks (ADR writing, code review, debugging, dependency scanning) at baseline without procedural guidance. Mitigation: Phase 2 telemetry gate — if first-pass QA rate drops >10%, specific agent is reverted and procedure reclassified as project-specific.

**SPOF:** Telemetry comparison gate (Phase 2, Step 2e) requires brain availability. Failure mode: can't detect quality regression. Fallback: manual review of Roz's first 3 post-reduction QA reports.

**Anti-goals:** (1) Do NOT reduce Distillator or Haiku-tier specs; (2) Do NOT remove output format templates (DoR/DoD, contract tables, QA structure); (3) Do NOT automate reduction (Darwin can measure impact, not classify generic vs project-specific).

---

## Decision

Reduce agent specification by ~57% through two sequential phases: structural reduction (personas, templates, references) + validation (telemetry comparison over 3 pipelines).

### Reduction Principles

1. **Constraints over procedures** — project-specific delta, not generic competencies
2. **Conventions over competencies** — keep project vocabulary (PASS/DRIFT/MISSING/AMBIGUOUS), output formats, design principles; remove generic methodology
3. **Format over methodology** — structured templates preserved; procedures removed
4. **Examples calibrate judgment, not demonstrate compliance** — example earns budget only if it shows judgment call model would get wrong without it
5. **Model tier determines example density** — Opus: 0-1 examples; Sonnet: 1-2; Haiku: 2

---

## Phase 1: Structural Reduction (12 steps)

| Step | Action | Target Lines | Files | Key Preservation |
|------|--------|--------------|-------|------------------|
| **1a** | Extract brain capture protocol to agent-preamble.md | agent-preamble.md +20; Cal/Colby/Roz/Agatha: <=6 each (vs ~27 now); save ~80 lines | cal.md, colby.md, roz.md, agatha.md, agent-preamble.md | All capture gates; agent-specific thought_type + importance values retained |
| **1b** | Extract step sizing gate (S1-S5) to shared reference | Create step-sizing.md (~45 lines); Cal: 1-line reference | Create: step-sizing.md; Modify: cal.md | S1-S5 table, split heuristics, evidence paragraph, Darwin review trigger |
| **1c** | Reduce Cal persona | <=120 lines (from 315) | cal.md | Spec challenge + SPOF analysis pattern; hard gates 1-4; vertical slice preference; anti-goals; contract tables in output |
| **1d** | Reduce Colby persona | <=95 lines (from 237) | colby.md | "Make Roz's tests pass, don't modify assertions" (TDD-first per R15); contract tables; premise verification; 1 example: premise verification judgment |
| **1e** | Reduce Roz persona | <=100 lines (from 242) | roz.md | Both current examples (judgment restraint: "looks wrong but isn't"); "assert domain-correct behavior"; qa-checks.md reference; TDD constraint explicit |
| **1f** | Reduce 8 remaining agents | Ellis: <=65; Agatha: <=55; Robert: <=60; Sable: <=60; Poirot: <=65; Sentinel: <=65; Darwin: <=100; Deps: <=90; Distillator: >=130 | ellis.md, agatha.md, robert.md, sable.md, investigator.md, sentinel.md, darwin.md, deps.md, distillator.md | Information asymmetry constraints (Robert, Sable, Sentinel, Poirot); PASS/DRIFT/MISSING/AMBIGUOUS (Robert); five-state audit (Sable); min 5 findings (Poirot); CWE/OWASP (Sentinel); fitness/escalation tables (Darwin); risk classification (Deps); **Distillator unchanged density** |
| **1g** | Collapse invocation-templates.md | <=300 lines (from 806); 20 templates (from 25) | invocation-templates.md | Brain-context protocol in header; standard READ items (retro-lessons.md, agent-preamble.md) in header; fold CI Watch variants; move agent-teams-task to pipeline-operations.md; remove dashboard-bridge |
| **1h** | Create session-boot.sh hook | New script (~65 lines) | Create: session-boot.sh in source/shared/hooks/; Modify: default-persona.md | Exits 0 always; outputs JSON: pipeline_active, phase, feature, stale_context, warn_agents[], branching_strategy, agent_teams_enabled, agent_teams_env, custom_agent_count, ci_watch_enabled, darwin_enabled, dashboard_mode, sentinel_enabled, deps_agent_enabled, project_name; handles missing files gracefully |
| **1i** | Reduce pipeline-orchestration.md | <=650 lines (from 952) | pipeline-orchestration.md | **Preserve verbatim:** all 12 mandatory gates; observation masking receipts; brain capture model; investigation discipline; pipeline flow diagram; phase sizing rules; **Condense:** telemetry capture prose; CI Watch protocol; Darwin auto-trigger; pattern staleness, dashboard bridge |
| **1j** | Register new reference + hook | N/A | Update: SKILL.md; /pipeline-setup logic | Copy step-sizing.md to target `.claude/references/`; register session-boot.sh hook in settings.json SessionStart event |
| **1k** | Write tests for new reference + hook | N/A | Create: tests/hooks/session-boot.bats (~25 tests) | session-boot.sh JSON output validation, missing file handling, exit 0 guarantee |
| **1l** | Final integration verification | Total agent personas <=935 lines (from 2,392); invocation-templates.md <=300; default-persona.md boot <=30; all tests pass | All agent files; invocation-templates.md; tests/ | All bats tests pass; all brain tests pass; 3 spot-check: assemble Cal, Colby, Roz from source/shared + source/claude overlay and verify valid markdown |

---

## Phase 2: Validation (3 pipelines)

| Step | Action | Acceptance Criteria |
|------|--------|-------------------|
| **2a** | Establish baseline metrics from brain telemetry (Tier 3, last 5 pipelines) | Baseline: per-agent first-pass QA rate, per-agent rework rate, agent finding counts, total pipeline cost; captured with `thought_type: 'decision'`, `source_phase: 'telemetry'`, metadata: `{baseline_for: 'ADR-0023', metrics: {...}}` |
| **2b** | Run 3 pipelines on reduced specs (normal operation, no code changes) | 3 pipelines completed with Tier 3 telemetry; no manual intervention due to spec gaps |
| **2c** | Compare post-reduction vs baseline; determine acceptance | **Regression thresholds:** First-pass QA drop >10% → revert agent; Rework increase >0.5 → investigate; Poirot BLOCKER increase >50% → investigate; Pipeline cost increase >20% → investigate. **Action:** If no regressions, mark ADR-0023 "Accepted"; if regressions, revert specific sections and mark "Accepted with amendments" |

---

## Comprehensive Test Specification (108 Tests)

All 108 tests preserved with exact IDs (T-0023-001 through T-0023-155):

### Step 1a (8 tests: T-0023-001 to T-0023-008)
- agent-preamble.md contains `<protocol id="brain-capture">`; Cal/Colby/Roz/Agatha <=6 lines each; retain thought_type + importance; step 4 retains mcpServers list

### Step 1b (6 tests: T-0023-010 to T-0023-015)
- step-sizing.md exists with S1-S5 table, split heuristics, evidence (57%->93%), Darwin trigger; Cal references by path; table NOT duplicated

### Step 1c (10 tests: T-0023-020 to T-0023-029)
- Cal <=120 lines; contains "spec challenge" + "SPOF"; hard gates 1-4; vertical slice; anti-goals; 1 example (spec challenge + SPOF judgment); NO "State Machine Analysis", "Blast Radius", "Migration & Rollback" headers; output template retains: DoR, ADR skeleton, UX Coverage, Wiring Coverage, Contract Boundaries, Notes for Colby, DoD

### Step 1d (8 tests: T-0023-030 to T-0023-037)
- Colby <=95 lines; "Make Roz's tests pass" + "do not modify assertions" verbatim; Contracts Produced table; premise verification; 1 example (premise verification judgment); NO "Retrieval-led reasoning" opening; TDD constraint explicit

### Step 1e (6 tests: T-0023-040 to T-0023-045)
- Roz <=100 lines; "assert domain-correct behavior" constraint; 2 examples (judgment restraint); qa-checks.md reference; NO numbered trace steps; NO Layer Awareness table

### Step 1f (21 tests: T-0023-050 to T-0023-070)
- Robert <=60 + info asymmetry + PASS/DRIFT/MISSING/AMBIGUOUS; Sable <=60 + five-state audit; Poirot <=65 + min 5 findings + cross-layer wiring; Ellis <=65; Sentinel <=65 + CWE/OWASP; Darwin <=100 + self-edit + "5+ pipelines"; Deps <=90 + conservative labeling; Distillator >=130 + 2 examples; Every agent >=1 example; NO "How X Fits" section; NO generic review checklists (logic, security, error handling, etc.)

### Step 1g (12 tests: T-0023-080 to T-0023-091)
- invocation-templates.md <=300 lines; header has brain-context protocol, standard READ items, persona-constraint notes; <=20 templates; NO brain-context XML examples per template; NO retro-lessons.md/agent-preamble.md in individual READ lists; CI Watch variants annotated; agent-teams-task moved to pipeline-operations.md; dashboard-bridge removed

### Step 1h (22 tests: T-0023-100 to T-0023-121)
- session-boot.sh outputs valid JSON with: pipeline_active, phase, feature, stale_context, warn_agents[], branching_strategy, agent_teams_enabled/env, custom_agent_count, ci_watch_enabled, darwin_enabled, dashboard_mode, sentinel_enabled, deps_agent_enabled, project_name; handles missing files (exits 0, outputs defaults); env var detection; executable; `set -uo pipefail` (not `set -e`); <500ms; default-persona.md boot refs session-boot.sh for steps 1-3d; steps 4-6 retained

### Step 1i (5 tests: T-0023-130 to T-0023-134)
- pipeline-orchestration.md <=650 lines; all 12 mandatory gates verbatim; observation masking receipts preserved; brain capture model preserved; investigation discipline preserved

### Step 1j (4 tests: T-0023-140 to T-0023-143)
- SKILL.md lists step-sizing.md; settings.json template includes session-boot.sh in SessionStart hooks; /pipeline-setup copies step-sizing.md; registers session-boot.sh

### Step 1l (6 tests: T-0023-150 to T-0023-155)
- Total agent lines <=935; all bats tests pass; all brain tests pass; assembled Cal/Colby/Roz valid markdown

**Test distribution:** Step 1a: 8; 1b: 6; 1c: 10; 1d: 8; 1e: 6; 1f: 21; 1g: 12; 1h: 22; 1i: 5; 1j: 4; 1l: 6. **Total: 108 tests.**

---

## Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| step-sizing.md | Markdown: S1-S5 table, split heuristics, evidence, Darwin trigger | Cal (reference), Darwin (reference) | 1b |
| agent-preamble.md `<protocol id="brain-capture">` | Shared capture gates; agents specify thought_type + importance | Cal, Colby, Roz, Agatha (pointer + agent-specific) | 1a |
| session-boot.sh | JSON stdout: pipeline_active, phase, feature, stale_context, warn_agents[], branching_strategy, agent_teams_enabled/env, custom_agent_count, ci_watch_*, project_name | Eva boot sequence default-persona.md (parse + use) | 1h |
| invocation-templates.md header | Brain injection protocol, standard READ items, persona-constraint note | All templates (no longer repeat) | 1g |
| Baseline metrics | Brain capture: `{baseline_for: 'ADR-0023', per_agent_first_pass_qa, per_agent_rework_rate, ...}` | Phase 2 Step 2c comparison | 2a |

## Wiring Coverage

- step-sizing.md → Cal (references by path), Darwin (threshold data)
- agent-preamble.md brain protocol → Cal, Colby, Roz, Agatha persona pointers
- session-boot.sh JSON → Eva default-persona.md boot parsing, SKILL.md hook registration, /pipeline-setup install
- Reduced personas → /pipeline-setup overlay assembly
- Phase 1 all changes → Phase 2 baseline measurement

---

## Notes for Colby (11 items)

1. **ADR-0022 must be complete.** All `source/` paths assume post-ADR-0022 structure (`source/shared/agents/`, `source/shared/references/`, etc.).
2. **Line count targets are ±10%.** Cal <=120 means 108-132 acceptable; don't pad or cut useful content.
3. **"Remove" = delete, not comment.** No `<!-- removed: ... -->` blocks, no `_unused` renames.
4. **Examples are write-once.** Replace generic examples from scratch with "wrong default → correct behavior" structure, not retrofit.
5. **Test the examples.** Each replacement demonstrates judgment call; if you can't articulate what model would get wrong without it, example isn't earning budget.
6. **session-boot.sh follows prompt-brain-capture.sh pattern exactly:** `set -uo pipefail` (not `set -e`), `INPUT=$(cat 2>/dev/null) || true`, graceful `jq` fallback, exit 0 always. Location: `source/shared/hooks/` (both platforms).
7. **invocation-templates.md index must update:** 25 → ~20 templates after folding CI Watch variants and removing dashboard-bridge/agent-teams-task; line numbers shift after header expansion.
8. **Dual tree for installed files:** Edit `source/shared/`, then run `/pipeline-setup` to sync to `.claude/`. Do NOT edit `.claude/` directly.
9. **Distillator is exception:** Target >=130 lines (not <=); Haiku agents get denser spec. Don't apply Opus/Sonnet reduction to Distillator.
10. **pipeline-orchestration.md reduction scope:** Condense procedural prose within protocols only. **Do NOT touch:** mandatory gates, observation masking receipts, brain capture model, pipeline flow diagram, phase sizing rules, decision tables. Tables stay; prose describing execution gets condensed.
11. **Preserve XML tag structure:** Tags (`<identity>`, `<required-actions>`, `<workflow>`, `<examples>`, `<constraints>`, `<output>`) stay even when content shrinks; vocabulary in xml-prompt-schema.md.

---

## Alternatives Considered & Rejected

| Alternative | Reason for Rejection |
|-------------|----------------------|
| **Alt 1: Proportional reduction (30% across all agents evenly)** | Ignores content-type boundary (procedure vs constraint). Some agents bloated (Deps 267 lines), others lean (Ellis 134). Cut/keep boundary is content-type, not proportional. |
| **Alt 2: Model-tier-only reduction (cut Opus, leave Sonnet/Haiku)** | Most agents run on Sonnet (Colby, Roz, Robert, Sable, Poirot, Sentinel, Deps). Leaving them unchanged misses majority of opportunity. Audit shows Sonnet agents contain generic procedures (Roz's trace steps, Poirot's 8-category checklist). Model-tier approach adjusts *example density*, not specification scope. |
| **Alt 3: Defer until Darwin automates analysis** | Darwin measures outcomes (first-pass QA, rework rate) but cannot classify "generic competence" vs "project convention" — requires understanding what model knows from training (human judgment). Darwin valuable for Phase 2 validation, not replacement for audit. |

---

## DoD: Preservation Checklist

| Category | Count | Status |
|----------|-------|--------|
| Requirements (R1-R15) | 15 | All 15 preserved with citations |
| Test Specs (T-0023-001 to T-0023-155) | 108 | All 108 preserved; gaps at step boundaries only |
| Phase 1 Steps (1a-1l) | 12 | All 12 with acceptance criteria |
| Phase 2 Steps (2a-2c) | 3 | All 3 with acceptance criteria + regression thresholds |
| Per-agent reduction targets | 12 agents | All with current/target lines, key removals, key preservations, example strategy |
| Reduction principles | 5 | Constraints over procedures, conventions over competencies, format over methodology, examples calibrate judgment, model tier determines density |
| Anti-goals | 3 | Don't reduce Distillator/Haiku; don't remove output formats; don't automate (with revisit conditions) |
| Contract Boundaries | 5 producer-consumer mappings | All preserved with shapes |
| Wiring Coverage | 8 producer-consumer-step mappings | All preserved |
| SPOF analysis | 1 | Telemetry comparison gate (brain unavailability; fallback: manual Roz QA review) |
| Notes for Colby | 11 | All preserved with exact ordering |

**Compression: 13,700 tokens → 5,600 tokens (41% of original)**
