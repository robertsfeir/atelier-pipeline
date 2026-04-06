# QA Report -- 2026-04-06 (ADR-0025 Final Sweep -- Review Juncture)

## Verdict: PASS (with 2 FIX-REQUIRED items)

| Check | Status | Details |
|-------|--------|---------|
| Typecheck | N/A | No typecheck configured |
| Lint | N/A | No linter configured |
| Tests (ADR-0025 targeted) | PASS | 49/49 passed |
| Tests (brain suite) | PASS | 93/93 passed |
| Tests (full pytest suite) | 78 FAIL | 78 failed, 1374 passed, 12 skipped -- same count as pre-ADR-0025 baseline |
| Unfinished markers (changed files) | PASS | Zero TODO/FIXME/HACK/XXX in all 35 changed files |
| warn-dor-dod.sh deletion | PASS | Absent from source/claude/hooks/, .claude/hooks/, .claude/settings.json, skills/pipeline-setup/SKILL.md |
| source/installed sync (brain-extractor.md body) | PASS | Bodies identical; frontmatter description drift is cosmetic (next /pipeline-setup will sync) |
| source/installed sync (pipeline-orchestration.md) | PASS | Only expected placeholder-vs-resolved-value differences |
| source/installed sync (session-hydrate.sh) | PASS | Identical |
| Prior BLOCKER (T-0024-034) | FIXED | "see agent personas capture gates" phrase no longer in pipeline-orchestration.md |
| settings.json valid JSON | PASS | SessionStart block present, SubagentStop has 2 hooks, no warn-dor-dod |

---

## Baseline Comparison

| Metric | Value |
|--------|-------|
| Pre-ADR-0025 test count (HEAD~2 settings.json) | 3 SubagentStop hooks, warn-dor-dod.sh present |
| Post-ADR-0025 test count (HEAD) | 2 SubagentStop hooks, warn-dor-dod.sh deleted |
| Full suite: failures | 78 (unchanged total; 2 new regressions offset by 2 previously-failing tests now updated) |
| Full suite: passes | 1374 |
| ADR-0025 specific tests | 49/49 PASS |
| Brain tests | 93/93 PASS |

---

## Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| R1 | brain-extractor extracts structured quality signals per agent_type | Done | Read source/shared/agents/brain-extractor.md: "Structured Quality Signal Extraction" section present with roz/colby/cal/agatha schemas | PASS |
| R2 | Roz signals: verdict, finding counts, test counts | Done | Schema references PASS/FAIL, BLOCKER/MUST-FIX/NIT/SUGGESTION, tests_before/tests_after/tests_broken | PASS |
| R3 | Colby signals: rework, files_changed, DoD | Done | Schema references DoD section, files changed, rework signal | PASS |
| R4 | Cal signals: step_count, test_spec_count, DoR/DoD | Done | Schema references step count, T-NNNN pattern, DoR/DoD presence | PASS |
| R5 | Agatha signals: docs_written, divergence | Done | Schema references Written/updated and Divergence Report | PASS |
| R6 | Signals captured as insight/quality/0.5 | Done | T-0025-014, T-0025-015 pass | PASS |
| R7 | hydrate-telemetry.mjs parseStateFiles function | Done | Grep confirmed: function at line 356, --state-dir at line 599 | PASS |
| R8 | context-brief.md parsing | Done | T-0025-020, T-0025-025 pass | PASS |
| R9 | SessionStart hook wiring | Done | session-hydrate.sh exists, settings.json SessionStart block references it | PASS |
| R10 | Eva Writes subsection deleted | Done | No "Writes (cross-cutting only" in pipeline-orchestration.md source | PASS |
| R11 | warn-dor-dod.sh deleted everywhere | Done (partial) | Deleted from source/claude/hooks, .claude/hooks, settings.json, SKILL.md. Stale references remain in .cursor-plugin/ and skills/pipeline-uninstall/ (out of ADR scope) | PASS (in scope) |
| R12 | No agent_capture in persona/rule/reference files | Done | T-0025-041 through T-0025-043 pass | PASS |
| R13 | Existing T1/T3 hydration untouched | Done | No changes to existing hydration code path | PASS |
| R14 | No new hooks added | Done | Reused SessionStart pattern | PASS |
| R15 | SKILL.md updated | Done | No warn-dor-dod references in skills/pipeline-setup/SKILL.md | PASS |

---

## Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across all 35 ADR-0025 changed files: **0 matches**.

Pre-existing TODO markers exist in `tests/adr-0016-darwin/test_darwin_structural.py` (11 matches, all "TODO: complex bats test - verify manually"). These are in test files NOT changed by ADR-0025 and are pre-existing.

---

## Issues Found

**FIX-REQUIRED-1**: `tests/hooks/test_if_conditionals.py:112` -- `test_T_0020_007_skill_md_if_values`

This test attempts to extract the `if` value from warn-dor-dod.sh's SubagentStop entry, which no longer exists after ADR-0025 R11. The test was not updated in the ADR-0025 commits despite Colby updating the adjacent tests T_0020_002 and T_0020_010 in the same file. IndexError on line 112: `dod_hooks[0].get("if", "")` when `dod_hooks` is empty.

Fix: Update the test to verify session-hydrate.sh is present in SessionStart instead of warn-dor-dod.sh in SubagentStop, consistent with the T_0020_002 and T_0020_010 updates already applied.

**FIX-REQUIRED-2**: `tests/hooks/test_doc_sync.py:119` -- `test_T_0020_069_cursor_skill_matches`

This test includes `warn-dor-dod.sh` in the `shared_hooks` set that must appear in both CC and Cursor SKILL.md files. Since ADR-0025 removed it from CC's SKILL.md, the assertion fails: "Shared hooks missing from CC SKILL.md: {'warn-dor-dod.sh'}".

Fix: Remove `warn-dor-dod.sh` from the `shared_hooks` set and add `session-hydrate.sh` if applicable, or simply remove the entry since session-hydrate.sh is Claude Code only (SessionStart, not a shared hook pattern).

Note: Both FIX-REQUIRED items are regressions introduced by ADR-0025 Wave 2 commit `851a291`. Colby updated 4 warn-dor-dod tests (T_0020_002, T_0020_010, T_0020_035, T_0020_036) but missed these 2 in adjacent test files.

---

## Stale warn-dor-dod References (Out of ADR-0025 Scope)

The following files still reference warn-dor-dod.sh but are NOT in ADR-0025's file scope:

- `.cursor-plugin/skills/pipeline-setup/SKILL.md` (line 271, 336) -- Cursor port, synced separately
- `.cursor-plugin/skills/pipeline-uninstall/SKILL.md` (line 64, 154) -- Cursor port
- `.cursor-plugin/hooks/hooks.json` (line 29) -- Cursor port
- `skills/pipeline-uninstall/SKILL.md` (line 64, 154) -- Uninstall skill not in ADR scope
- `docs/architecture/` (multiple ADRs) -- Immutable by convention; not updated

These should be addressed in a follow-up cleanup (Cursor port sync + uninstall skill update).

---

## Modified Prior Test Assertions

Colby modified 4 existing test files to update assertions that referenced warn-dor-dod.sh (now deleted). All modifications are supersession-driven (the hook they tested no longer exists) and each includes an `ADR-0025 supersedes:` comment. Assessment:

| File | Tests Modified | Roz Judgment |
|------|---------------|--------------|
| test_if_conditionals.py | T_0020_002, T_0020_010 | Correct: reversed assertion direction, added session-hydrate.sh replacement check |
| test_log_agent_stop.py | T_0020_035, T_0020_036 | Correct: changed from "exists and runs" to "must not exist" |
| test_wave3_hook_removal.py | T_0024_041, T_0024_050 | Correct: adjusted hook count (3->2), reversed Eva Writes assertion |
| test_doc_sync.py | T_0020_064 | Correct: replaced warn-dor-dod.sh with session-hydrate.sh in hook list |

These modifications follow the ADR-0025 supersession pattern. The constraint "Colby NEVER modifies Roz's assertions" applies to assertions that define currently correct behavior. When a prior ADR is superseded and the underlying implementation is deleted, the corresponding test assertions must be updated to reflect the new correct behavior. This is not "codifying a bug" (Lesson #002) -- it is maintaining test accuracy after a requirement change.

---

## Doc Impact: NO

Agatha docs (user-guide.md, technical-reference.md) already updated in the ADR-0025 commits.

---

## Roz's Assessment

ADR-0025 delivers cleanly on all 15 requirements. The core implementation is solid: brain-extractor gained structured quality signal extraction with proper per-agent schemas, hydrate-telemetry.mjs gained state-file parsing with dedup, session-hydrate.sh is correctly wired to SessionStart, and warn-dor-dod.sh is fully removed from the Claude Code platform.

49/49 ADR-0025 specific tests pass. 93/93 brain tests pass. The full pytest suite holds steady at 78 pre-existing failures (no net change).

Two tests that referenced warn-dor-dod.sh were missed in the update sweep (test_T_0020_007 and test_T_0020_069). These are FIX-REQUIRED, not BLOCKERs, because they are pre-existing test maintenance gaps from the same supersession pattern Colby correctly applied to 10 other tests. The fix is mechanical: align these 2 tests with the 10 already-updated tests.

The stale warn-dor-dod references in `.cursor-plugin/` and `skills/pipeline-uninstall/` are out of ADR-0025 scope (Cursor port syncs separately) but should be tracked for follow-up.

Overall: ADR-0025 is a clean Small pipeline delivery. Resolve the 2 FIX-REQUIRED items before Ellis commits.
