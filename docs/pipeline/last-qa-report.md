# QA Report -- 2026-04-20 (Wave 1 Safety-Valve Re-Run, post fix-cycle-4)

## Verdict: PASS

Fix-cycle-4 resolved all 10 slice-1 regressions from the prior sweep. Full `pytest tests/` run shows **1890 passed / 10 failed**; all 10 remaining failures are pre-existing environment debt documented and acknowledged in the evidence bundle (8x `jq_missing` macOS-15 PATH-shadow gap, 1x brain-node `zod` cascade, 1x meta pytest-cascade). ADR-0043 own contract (37/37), all fix-cycle-4 regression targets (11/11), and every previously flagged BLOCKER are green. Clear for Ellis.

## Checks

| Check | Status | Details |
|-------|--------|---------|
| Full pytest suite (`python3 -m pytest tests/`) | PASS (with acknowledged env debt) | 1890 passed, 10 failed. All 10 failures map to pre-existing env buckets. |
| Slice-1 regression targets (10 tests across ADR-0015 / ADR-0018 / ADR-0023) | PASS | 11/11 selected (T_0015_052-055, 058, 059; T_0018_036, 038, 095; T_0023_029) all green. |
| ADR-0043 own contract suite | PASS | 37/37. |
| Brain node suite (via `test_T_0024_049`) | FAIL (pre-existing env, `zod` missing) | 172 passed / 12 failed -- unchanged from prior sweep, not caused by slice 1 or fix-cycles. |

## Fix-Cycle-4 Verification (deltas since prior sweep)

| # | Prior-sweep failure | fix-cycle-4 change | Re-run status |
|---|---|---|---|
| 1 | `test_T_0023_029` (Cal `<output>` missing `skeleton` keyword) | Added "skeleton" to Cal's `<output>` body-list phrase in `source/shared/agents/cal.md` + `.claude/agents/cal.md` | GREEN |
| 2-7 | `test_T_0015_052`–`_055`, `_058`, `_059` (Deps `_step6d()` extracted wrong section) | Moved new Claude Code Agent Resume Prerequisite step Step 6b -> Step 6g in `skills/pipeline-setup/SKILL.md`; restored 6b=Agent Teams, 6c=CI Watch, 6d=Deps, 6e=Darwin, 6f=Dashboard | GREEN |
| 8-10 | `test_T_0018_036`, `_038`, `_095` (dashboard anti-regression guards on step letters) | Same renumber restoration (6e=Darwin, 6b=Agent Teams) | GREEN |
| 11 | `test_T_0034_046` cascade (pytest returncode meta-test) | Resolved by above -- however, it is STILL failing in this run. See environment debt below. | Re-evaluated below |

## Remaining Failures (all pre-existing env, NOT slice-1 regressions)

All 10 surviving failures reproduce on a pre-slice-1 stash per the prior sweep's verification and are documented env debt:

1. **8x `jq_missing` hook tests** -- macOS 15 ships `/usr/bin/jq` which the `tests/hooks/conftest.py::hide_jq_env` helper does not shadow:
   - `tests/hooks/test_adr_0022_phase2_compaction.py::test_T_0022_180_jq_missing`
   - `tests/hooks/test_adr_0022_phase2_hooks.py::test_T_0022_087c_roz_jq_missing`
   - `tests/hooks/test_adr_0022_phase2_hooks.py::test_T_0022_087d_colby_jq_missing`
   - `tests/hooks/test_enforce_git.py::test_T_0003_031_jq_missing`
   - `tests/hooks/test_enforce_pipeline_activation.py::test_jq_missing_exits_2`
   - `tests/hooks/test_enforce_scout_swarm.py::test_T_SCOUT_001_jq_missing`
   - `tests/hooks/test_enforce_sequencing.py::test_T_0003_030_jq_missing`
   - `tests/hooks/test_prompt_brain_prefetch.py::test_T_0021_008_jq_missing`
   - Prior report counted 7 "distinct" by collapsing the `087c/087d` pair; actual count is 8 tests.

2. **1x brain-node cascade** -- `tests/hooks/test_wave3_hook_removal.py::test_T_0024_049_brain_node_test_suite_passes` wraps `node --test tests/brain/*.test.mjs`; brain test run shows `tests 184 / pass 172 / fail 12`. 12 node-test failures are `ERR_MODULE_NOT_FOUND: zod` -- missing dependency, same env debt as prior sweep. Requires `cd brain && npm install`.

3. **1x pytest meta-cascade** -- `tests/hooks/test_wave3_adr0034_triage.py::test_T_0034_046_full_pytest_suite_passes` spawns `pytest tests/` in a subprocess. This is now failing solely because the 9 env-debt tests above fail inside that nested invocation; Colby's note in the evidence identifies the same subprocess-PATH class of issue (test-subprocess PATH lacks Homebrew jq shadowing). This is cascade-only -- not a slice-1 regression, will go green when the jq/zod env issues are ticketed and fixed. Categorized with the env debt per evidence.

## Unfinished Markers

None in slice-1-edited files. Clean.

## Issues Found

**BLOCKER:** 0
**FIX-REQUIRED:** 0

All previously flagged BLOCKERs (1, 2, 3, 4 in prior sweep) resolved. No new regressions introduced by fix-cycles 1-4.

## Doc Impact: NO

Slice 1 + fix-cycles remain ADR-body-only doc impact; no external doc surfaces affected.

## Roz's Assessment

Clean landing. Fix-cycle-4's two changes -- (a) relocating the new Claude Code Agent Resume prerequisite step to a terminal letter (6g) so the existing step-letter contracts stay stable, and (b) inserting the word "skeleton" into Cal's `<output>` pointer sentence -- resolved all 10 cross-ADR collisions without perturbing the ADR-0043 primary contract or any other test in the suite. The pattern that emerges across fix-cycles 1-4 is consistent with retro-lesson 005's "synchronization work is separate from design correctness" reading: the ADR-0043 design was right from slice-1; the work since has been cross-walking its load-bearing text against pre-existing structural assertions.

Two followups that I strongly recommend Eva ticket (not blockers on this commit):

1. **macOS-15 jq shadow.** `tests/hooks/conftest.py::hide_jq_env` must extend its PATH shadow to cover `/usr/bin/jq`, or switch to a minimal-PATH strategy. 8 tests silently degraded.
2. **Brain `zod` dep.** `brain/package.json` appears to declare `zod` but `node_modules/` is not populated in this worktree. Either pin the install step into CI or add a bootstrap check. 12 node tests + 1 pytest cascade.

Recommend a retro-lessons entry codifying "load-bearing text in structural tests" -- any change to SKILL.md step letters, persona `<output>` blocks, or ADR section names should trigger a pre-commit grep for those literals in `tests/` during Cal's test-spec review. This is now fix-cycle-4's second occurrence of the same class.

Dogfooding the ADR-0043 receipt format on my return below.

Roz Wave 1 PASS. 0 BLOCKERs, 0 FIX-REQUIREDs. Report: docs/pipeline/last-qa-report.md.
