# QA Report — 2026-03-21 (Scoped Re-Run: Post Cross-Validation)
*Reviewed by Roz*

**Scope:** Final QA review of all three brain specs after Cal's cross-validation fixes (F1-F5). Verifying fixes AND checking for new issues introduced.

**Artifacts reviewed:**
- `docs/product/atelier-brain-feature-spec.md` (feature spec)
- `docs/ux/atelier-brain-settings-ux.md` (UX spec)
- `docs/architecture/ADR-0001-atelier-brain.md` (ADR)

**Previous QA report:** None found at `docs/pipeline/last-qa-report.md` (first persisted report).

---

## DoR: Requirements Extracted

| # | Requirement | Source |
|---|---|---|
| R1 | Cal's F1-F5 fixes applied correctly | Cal cross-validation findings |
| R2 | Cross-document alignment: tools, endpoints, agents, tiers, states, relations | All three specs |
| R3 | Test count headers match actual test rows | ADR test spec |
| R4 | Failure:happy ratio >= 1:1 per step | Roz operating rules |
| R5 | Zero TODO/FIXME/HACK/XXX in all three files | Roz operating rules |
| R6 | No silent drops between specs | Roz operating rules |
| R7 | No contradictions between specs | Roz operating rules |

**Retro risks:** No `retro-lessons.md` referenced — not applicable to doc-only review.

**Missing from READ:** None. All three specs plus Roz template provided.

---

## Cal's Fixes (F1-F5) Verification

| Fix | What to verify | Status | Finding |
|---|---|---|---|
| F1 | ADR Context line 42: mybrain tools are `capture_thought`, `search_thoughts`, `browse_thoughts`, `brain_stats` | PASS | Correct. Line 42 lists all four mybrain tool names accurately. |
| F2 | ADR Context: "10 user stories" not "7" | PASS | Correct. Line 44 says "10 user stories (US-1 through US-10)". |
| F3 | ADR R2: `synthesized_from` in relation types | PASS | Correct. R2 (line 8) lists all 6 relation types including `synthesized_from`. |
| F4a | `brain_config` table: `brain_enabled BOOLEAN NOT NULL DEFAULT false` | PASS | Correct. Line 150 of schema. |
| F4b | Step 7 toggle references `brain_config.brain_enabled` | PASS | Correct. Line 495 explicitly connects toggle to field. |
| F4c | Step 8 two-gate detection clear | PASS | Correct. Lines 529-536 document Gate 1 (infrastructure) and Gate 2 (runtime) distinctly. |
| F4d | Step 10 sets `brain_enabled = true` | PASS | Correct. Line 609: "Set `brain_config.brain_enabled = true` in database". |
| F4e | Feature spec US-7 AC references `brain_config.brain_enabled` | PASS | Correct. Line 110: "`brain_config.brain_enabled = false`". |
| F4f | UX spec interaction table references `PUT /api/config` | PASS | Correct. Line 171: toggle calls `PUT /api/config { brain_enabled: true/false }`. |
| F5a | T-0006-015 exists for `GET /api/stats` | PASS | Correct. Line 847, Happy path. |
| F5b | T-0006-016 exists for `GET /api/stats` failure | PASS | Correct. Line 848, Failure path (DB unreachable). |
| F5c | T-0008-020 exists for `brain_enabled: false` path | PASS | Correct. Line 882, Failure path. |

**F1-F5 verdict: ALL FIXES VERIFIED.** Cal's cross-validation changes are correctly applied.

---

## Cross-Document Alignment

| Check | Status | Finding |
|---|---|---|
| Feature spec MCP tools (6) match ADR Step 3 | PASS | Same 6 tools: agent_capture, agent_search, atelier_browse, atelier_stats, atelier_relation, atelier_trace. |
| Feature spec REST endpoints (7) match ADR Step 6 | PASS | Same 7 endpoints. |
| Feature spec Agent Operating Model matches ADR Step 9 file list | PASS | 7 brain-touching agents mapped to 8 files (cal, colby, roz, robert, sable, documentation-expert, default-persona, invocation-templates). Poirot/Distillator/Ellis correctly excluded. |
| Feature spec Deployment Tiers match ADR Steps 10+11 | PASS | 3 tiers covered: solo personal (Step 10 Path A personal), team isolated (implicit), team shared (Step 10 Path A shared + Step 11 project config). |
| Feature spec Config Priority Chain matches ADR Step 11 | PASS | project > user > none in both docs. |
| UX spec states match ADR Step 7 states | MUST-FIX | See MF-1 below. |
| UX spec interactions map to ADR REST endpoints | PASS | All 7 interactions map to documented endpoints. |
| Relation types consistent across all three docs | PASS | All 6 relation types (supersedes, triggered_by, evolves_from, contradicts, supports, synthesized_from) consistent in feature spec US-2 AC, feature spec tool table, ADR R2, ADR relation_type enum. |

---

## Test Count Verification

### Per-Step Header vs Actual Row Count

| Step | Header Claim | Actual Count | Header Category Breakdown | Actual Category Breakdown | Match? |
|---|---|---|---|---|---|
| 1: Schema | 11 | 11 | 4H, 5F, 2B | 4H, 5F, 2B | MATCH |
| 2: Scoring | **18** | **19** | 7H, 7F, **4B** | 7H, 7F, **5B** | **MISMATCH** — T-0002-017 is Boundary, not counted in header |
| 3: MCP Tools | 37 | 37 | **14H**, 15F, **5B**, 2S, 1C | **15H**, 15F, **4B**, 2S, 1C | **MISMATCH** — T-0003-034 is Happy not Boundary; totals happen to cancel |
| 4: TTL | 9 | 9 | **3H, 4F**, 2B | **4H, 3F**, 2B | **MISMATCH** — T-0004-005 is Happy, swapped with a Failure |
| 5: Consolidation | 12 | 12 | 5H, 6F, 1B | 5H, 6F, 1B | MATCH |
| 6: Settings API | 16 | 16 | 7H, 8F, 1B | 7H, 8F, 1B | MATCH |
| 7: Settings UI | **18** | **20** | 4H, 7F, 2B, 1S, 4A | **5H, 8F**, 2B, 1S, 4A | **MISMATCH** — 2 extra tests (T-0007-019 Failure, T-0007-020 Happy) not reflected in header |
| 8-9: Pipeline | **18** | **20** | **8H**, 7F, 3R | **10H**, 7F, 3R | **MISMATCH** — T-0008-020 added + original tests shifted count |
| 10: Setup Skill | 14 | 14 | 5H, 9F | 5H, 9F | MATCH |
| 11: Plugin Deploy | 13 | 13 | 6H, 7F | 6H, 7F | MATCH |
| **TOTAL** | **172** | **171** | 66H, 75F, 15B, 3S, 4A, 3R, 1C | **68H, 75F, 17B, 3S, 4A, 3R, 1C** | **MISMATCH** |

**Summary:** 5 step headers have wrong category breakdowns. The footer total (172) does not match the actual test row count (171). The footer category breakdown (66H, 15B) does not match actual (68H, 17B).

### Failure:Happy Ratio Per Step

| Step | Happy | Failure* | Ratio | Pass? |
|---|---|---|---|---|
| 1: Schema | 4 | 5 | 1.25:1 | PASS |
| 2: Scoring | 7 | 7 | 1.00:1 | PASS |
| 3: MCP Tools | 15 | 15 | 1.00:1 | PASS |
| 4: TTL | 4 | 3 | **0.75:1** | **FAIL** |
| 5: Consolidation | 5 | 6 | 1.20:1 | PASS |
| 6: Settings API | 7 | 8 | 1.14:1 | PASS |
| 7: Settings UI | 5 | 8 | 1.60:1 | PASS |
| 8-9: Pipeline | 10 | 7 | **0.70:1** | **FAIL** |
| 10: Setup Skill | 5 | 9 | 1.80:1 | PASS |
| 11: Plugin Deploy | 6 | 7 | 1.17:1 | PASS |

*Failure column counts only "Failure" category tests, not Boundary/Security/etc.

**Steps 4 and 8-9 fail the >= 1:1 failure:happy ratio.** Step 4 needs 1 more failure test. Step 8-9 needs 3 more failure tests (or the happy count was inflated by the F5 fix adding tests without adjusting the ratio).

---

## Standard Roz Checks

### TODO/FIXME/HACK/XXX Grep

| File | Count | Finding |
|---|---|---|
| Feature spec | 0 | Clean |
| UX spec | 0 | Clean |
| ADR | 0 | Clean (one meta-reference in D9 is a check description, not a marker) |

### Silent Drops

| Requirement | Present In | Missing From | Severity |
|---|---|---|---|
| UX shared config states (missing env vars, connected with shared badge) | UX spec (lines 162-163) | ADR Step 7 (says "All five UX states" but only lists 5 generic states, omits 2 shared-config sub-states) | MUST-FIX (MF-1) |
| Feature spec US-1 AC uses `agent_search` tool name | Feature spec line 40 | — | N/A (verified correct) |

No other silent drops detected. All 10 user stories are covered in ADR Product Spec Coverage. All 7 REST endpoints are covered. All 6 MCP tools are covered. All relation types are consistent.

### Contradictions

No contradictions found between the three specs. Feature spec, UX spec, and ADR are aligned on:
- Tool names and purposes
- Relation types and semantics
- Config priority chain
- Deployment tiers
- brain_enabled field and two-gate detection
- Thought types and TTL defaults

---

## Issues Found

### BLOCKER

None.

### MUST-FIX (resolve before Colby builds)

| ID | File | Location | Issue | Why It Matters |
|---|---|---|---|---|
| MF-1 | ADR | Step 7, line ~502-507 | Step 7 says "All five UX states implemented" and lists 5 states, but UX spec defines 7 states (adding "Shared config, missing env vars" and "Shared config, connected" as distinct states with different behaviors). ADR Step 7 must acknowledge all 7 UX states or explicitly note the shared-config states are sub-states of Populated/Error. | Colby building from ADR alone would miss the shared-config UI behavior (read-only fields, "(shared)" badge, "(local override)" labels). |
| MF-2 | ADR | Step 2 header (line 732) | Header says "4 Boundary = 18" but actual is 5 Boundary = 19 tests. T-0002-017 (Boundary) was added but header not updated. | Test count mismatch causes Colby to undercount implementation scope. |
| MF-3 | ADR | Step 3 header (line 756) | Header says "14 Happy ... 5 Boundary" but actual is 15 Happy, 4 Boundary. T-0003-034 is Happy, not Boundary. | Category miscount. |
| MF-4 | ADR | Step 4 header (line 798) | Header says "3 Happy, 4 Failure" but actual is 4 Happy (T-0004-005 is Happy), 3 Failure. | Category miscount AND failure:happy ratio now 0.75:1, violating the >= 1:1 rule. Needs 1 additional failure test for Step 4. |
| MF-5 | ADR | Step 7 header (line 850) | Header says "18" but actual row count is 20 (T-0007-019 and T-0007-020 exist but aren't counted). Header says "4 Happy, 7 Failure" but actual is 5 Happy, 8 Failure. | Test count mismatch (18 vs 20). |
| MF-6 | ADR | Step 8-9 header (line 875) | Header says "8 Happy ... = 18" but actual is 10 Happy, 7 Failure, 3 Regression = 20. T-0008-020 was added (F5 fix) plus original counts were wrong. | Test count mismatch (18 vs 20) AND failure:happy ratio is 0.70:1, violating >= 1:1. Needs 3 additional failure tests for Step 8-9. |
| MF-7 | ADR | Footer (line 1050) | Claims "172 total tests (66 happy ... 15 boundary)" but actual is 171 total (68 happy, 17 boundary). | Global count mismatch propagates to DoD D4. |
| MF-8 | ADR | DoD D1 (line 1032) | Says "US-1 through US-7" but Product Spec Coverage table covers US-1 through US-10, and the feature spec defines 10 user stories. | D1 understates coverage scope. Should say "US-1 through US-10". |
| MF-9 | ADR | DoD D4 (line 1035) | Claims "172 tests" — should be updated when footer is corrected. | Stale count. |
| MF-10 | ADR | DoD D11 (line 1042) | Claims failure:happy >= 1:1 across all steps, but Steps 4 and 8-9 currently fail this ratio. | DoD criterion is not met. Either add failure tests or update the claim. |

---

## Roz's Assessment

Cal's F1-F5 cross-validation fixes are clean and correctly applied. The substantive alignment between the three specs is solid — tool names, relation types, config chain, deployment tiers, and two-gate detection are all consistent. No contradictions found. No TODO/FIXME markers.

The issues introduced are all bookkeeping errors: test count headers that weren't updated when tests were added or recategorized during the fix pass. This is the classic "fix the content, forget the summary" pattern. The fixes themselves are correct; it's the metadata about the fixes that drifted.

The two actionable items beyond header corrections:
1. **MF-1 (shared-config states):** Step 7 needs to explicitly acknowledge the UX spec's shared-config sub-states so Colby doesn't miss read-only fields and override labels.
2. **MF-4 and MF-6 (ratio violations):** Steps 4 and 8-9 need additional failure tests to meet the >= 1:1 ratio. Step 4 needs 1 more failure test. Step 8-9 needs 3 more failure tests.

None of these are blockers. All are fixable in a single Cal pass without restructuring.

---

## DoD: Verification

| # | Criterion | Status |
|---|---|---|
| D1 | Cal's F1-F5 fixes all verified | Done — all 12 sub-checks pass |
| D2 | Cross-document alignment checked (tools, endpoints, agents, tiers, states, relations) | Done — 1 issue found (MF-1) |
| D3 | Test count headers verified against actual rows | Done — 5 mismatches found (MF-2 through MF-7) |
| D4 | Failure:happy ratio verified per step | Done — 2 steps fail (MF-4, MF-6, MF-10) |
| D5 | TODO/FIXME/HACK/XXX grep on all three files | Done — 0 markers found |
| D6 | Silent drops checked | Done — 1 found (MF-1) |
| D7 | Contradictions checked | Done — 0 found |
| D8 | Report written to `docs/pipeline/last-qa-report.md` | Done |

**Verdict: 0 BLOCKER, 10 MUST-FIX.** All MUST-FIX items are metadata/header corrections except MF-1 (shared-config states in Step 7) which is a coverage gap. Route back to Cal for a fix pass.
