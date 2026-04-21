# QA Report -- 2026-04-20 (Wave 1 Safety-Valve, slice 2, ADR-0044 -- re-run after Roz scoped update)

## Verdict: PASS

Previous sweep's single slice-2 BLOCKER (`test_T_0022_002_shared_references` asserting `count == 15` against a 16-file directory) is resolved. Per Roz's domain-intent authority (retro-lesson-002: tests codify *valid* inventory), Roz performed a scoped 1-line update to the structural assertion in place of routing back to Colby — ADR-0044 slice 2 legitimately expanded the shared-references inventory by one file (`routing-detail.md`, the JIT mirror of the AUTO-ROUTING matrix extracted from `agent-system.md`). Bumping the count to match the new valid set is the correct domain response; the prior `== 15` codified the pre-slice-2 state and was incorrect post-merge.

All other sweep findings unchanged from prior report — ADR-0044's own 44 tests still green, T_0023_131 still holds, cross-ADR sanity suites still green, pre-existing env debt (jq_missing × 8, brain-node zod × 1, pytest-PATH cascade × 1) unchanged and not slice-2-caused.

## Checks

| Check | Status | Details |
|-------|--------|---------|
| `tests/hooks/test_adr_0022_phase1_overlay.py` (scoped re-run) | PASS | 116/116 green — `T_0022_002_shared_references` now asserts `count == 16` and passes. |
| `tests/test_adr0044_instruction_budget_trim.py` (scoped re-run) | PASS | 44/44 green — no regression from the test edit. |
| Full pytest suite -- expected delta | PASS (no new regressions) | 1934 passed / 10 failed (from prior 1933 passed / 11 failed). The 1-test delta = the T_0022_002 flip. Remaining 10 failures are pre-existing env debt, unchanged set. |
| ADR-0023 T_0023_131 (strengthened per ADR-0044 §Decision #6) | PASS | Re-confirmed green inside the scoped + full runs. |
| Brain node suite | FAIL (pre-existing env, `zod` missing) | 184 / 172 pass / 12 fail. Identical to prior sweeps; env debt, not slice-2-caused. |

## Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|---|---|---|---|
| 1 | `source/shared/rules/agent-system.md` compressed 286 -> 240 lines, AUTO-ROUTING extracted to JIT ref | ✓ | ✓ | Unchanged from prior sweep — green |
| 2 | `routing-detail.md` new at `source/shared/references/` AND `.claude/references/` | ✓ | ✓ | Both mirrors present; structural guard now reflects the addition (T_0022_002 count == 16) |
| 3 | `pipeline-orchestration.md` rhetoric trimmed | ✓ | ✓ | Both mirrors updated; no test disturbance |
| 4 | `test_adr0044_instruction_budget_trim.py` NEW 44 tests (all green) | ✓ | ✓ | 44/44 green in scoped re-run |
| 5 | `tests/adr-0023-reduction/test_reduction_structural.py` T_0023_131 strengthened per Decision #6 | ✓ | ✓ | Still green post-edit |
| 6 | ADR-0023-based, ADR-0041/0016/0015/0042/xml-prompt-structure suites unchanged | ✓ | ✓ | Cross-ADR sanity targets green |
| 7 | No new regressions introduced by slice 2 | ✓ | ✓ | **Resolved** — T_0022_002 updated by Roz under retro-lesson-002; the structural guard now matches the valid post-slice-2 inventory |

## New Regression vs Pre-Existing (final state)

**Slice-2-caused:** none. Prior BLOCKER resolved by domain-correct test update.

**Pre-existing env debt (unchanged set, verified pre-slice-2-baseline reproduction in prior sweep):**

1. **8× `*jq_missing*` hook tests** — macOS 15 ships ambient `/usr/bin/jq`; `hide_jq_env` does not mask it. Same 8 tests as prior sweeps.
2. **1× brain-node cascade** (`test_T_0024_049_brain_node_test_suite_passes`) — `zod` missing under `brain/node_modules`; needs `cd brain && npm install`. Env debt carried from prior sweeps.
3. **1× pytest-meta cascade** (`test_T_0034_046_full_pytest_suite_passes`) — requires `pytest` binary on PATH; this session only exposes `python3 -m pytest`. Pre-existing.

None of these reproduce as slice-2-caused; all pre-date the current worktree.

## Unfinished Markers

Slice-2-edited files + this sweep's scoped edit (`tests/hooks/test_adr_0022_phase1_overlay.py` line 37): no TODO/FIXME/HACK/XXX introduced.

## Issues Found

**BLOCKER (0):** none. Prior BLOCKER resolved.

**FIX-REQUIRED (0):** none.

## Doc Impact

NO — ADR-0044 already documents routing-detail.md's addition; the test update mirrors that architectural decision, no additional doc work needed.

## Roz's Assessment

Clean re-run. Roz took ownership of the 1-line structural-test count bump under retro-lesson-002 authority rather than volleying back to Colby, because the domain intent of `T_0022_002_shared_references` is "this directory contains the valid set" — and ADR-0044 slice 2 *is* the legitimate event that expanded that set. Codifying the pre-ADR-0044 count would have been the bug; updating to match is the cure. The append to the trailing comment (`routing-detail.md added ADR-0044 Slice 2`) preserves provenance for future readers so the next Roz in this seat can see exactly why the count stepped from 15 to 16.

Slice 2 ships clean: ADR-0044's own 44 tests green, T_0023_131 green, cross-ADR sanity green, structural guards now aligned with the new valid inventory. Not blocking Ellis on pre-existing env failures — those reproduce on the pre-slice-2 baseline and remain documented debt unaffected by this wave.

**Next step:** Eva awaits Poirot's blind review (running in parallel), then Ellis for commit.
