# QA Report -- 2026-04-11

## ADR-0034 Wave 1 Targeted Sweep

### Verdict: PASS WITH NOTES

Wave 1 implementation is clear for Ellis to commit. All 8 targeted checks pass. Zero blockers. Zero fix-required items. Two non-blocking notes documented below.

---

| Check | Status | Details |
|-------|--------|---------|
| 1. SOURCE_AGENTS count and values | PASS | Exactly 16 entries. Sorted set matches ADR-0034 spec exactly: `['agatha','brain-extractor','cal','colby','darwin','deps','distillator','ellis','eva','poirot','robert','robert-spec','roz','sable','sable-ux','sentinel']`. |
| 2. Non-extracted comments (eva, poirot, distillator) | PASS | All three agents have `# non-extracted` comment within 5 lines. Verified by line-window scan against config.mjs lines 19–26. Sentinel/darwin/deps/brain-extractor also annotated with a companion comment (lines 28–29). |
| 3. SOURCE_PHASES count and values | PASS | Exactly 14 entries. Includes `product`, `ux`, `commit` (3 new phases). All 11 original phases present. |
| 4. Migration 008 idempotency | PASS | 9 `IF NOT EXISTS` guards (6 source_agent, 3 source_phase). Each `ALTER TYPE` is individually wrapped in `IF NOT EXISTS (SELECT 1 FROM pg_enum ...)`. Runs inside a single `DO $$ ... $$` block. All 9 new values covered. |
| 5. rest-api.mjs IN clause dynamic | PASS | `handleTelemetryAgents` at line 344 uses `${agentPlaceholders}` (parameterized, built from `SOURCE_AGENTS.map()`). `SOURCE_AGENTS` imported at line 7. No hardcoded agent name literal in any `IN (...)` clause in the file. |
| 6. pipeline-state-path.sh exports both distinct functions | PASS | `session_state_dir()` and `error_patterns_path()` are separate named functions. File is executable (`-rwxr-xr-x`). Both functions return appropriate paths per ADR-0032 Decision. |
| 7. session-boot.sh fallback uses relative path | PASS | Fallback at line 24: `echo "docs/pipeline"` (relative, no `$PROJECT_DIR` prefix). Correct -- session-boot.sh runs with cwd = project root; relative path is appropriate and consistent with pre-ADR-0032 behavior. |
| 8. post-compact-reinject.sh fallback uses $PROJECT_DIR prefix | PASS | Fallback at line 34: `echo "$PROJECT_DIR/docs/pipeline"`. Absolute path via `$PROJECT_DIR`. Correct -- post-compact hook exits 0 early when `$PROJECT_DIR` is unset (line 19-21), so fallback is only reached when `$PROJECT_DIR` is guaranteed present. |
| 9. Release notes document /pipeline-setup action | PASS | Release notes state re-run `/pipeline-setup` in every installed project. Lists all 9 target agents. States before-state (4 agents) and after-state (9 agents). Includes verification steps. |
| 10. TODO/FIXME/HACK/XXX markers | PASS | Zero matches across all 7 changed production files. |
| 11. Test suite results | PASS | 15/15 Wave 1 brain tests (T-0034-001 through T-0034-013, T-0034-003R, T-0034-061, T-0034-063). 10/10 pipeline_state_path tests (T-0034-014 through T-0034-020, T-0034-064 + 2 helper existence tests). 6/6 pipeline_setup_skill tests (T-0034-062 + 5 prior). 159/159 full brain suite. 1575 pytest PASS. 6 pre-existing failures confirmed by baseline stash -- zero introduced by Wave 1. |

---

## Requirements Verification

| # | Requirement | ADR Spec | Roz Verified | Finding |
|---|-------------|----------|--------------|---------|
| R1 | Fix silently-failing agent_capture from 6 additional agents | M1: SOURCE_AGENTS extended to 16 | VERIFIED | config.mjs has exactly the 16 expected entries; Zod validator picks up new values automatically via z.enum(SOURCE_AGENTS) |
| R2 | Single coordinated change closing M1+M9 together | atomic Wave 1 Step 1.1 | VERIFIED | SOURCE_AGENTS extended AND IN clause now dynamic from SOURCE_AGENTS in same step -- no orphan producer |
| R4 (partial) | ADR-0032 Step 1: helper + session-boot + post-compact | M3 Wave 1 scope | VERIFIED | Helper present and executable; both functions exported; both hooks source the helper with correct fallback contracts |
| Release notes | Action required documented for users | Wave 1 Step 1.2 | VERIFIED | /pipeline-setup re-run documented with agent list, before/after state, and verification steps |

---

## Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across all 7 changed files: **0 matches**

---

## Issues Found

None.

### Notes (non-blocking)

**NOTE-1 -- Migration 008 comment says "ADD VALUE IF NOT EXISTS pattern" but uses pg_enum SELECT guard**

The comment on line 4 of the migration reads "ADD VALUE IF NOT EXISTS pattern." The actual mechanism is `IF NOT EXISTS (SELECT 1 FROM pg_enum ...)` wrapping the `ALTER TYPE ... ADD VALUE '...'` call -- not the `ADD VALUE IF NOT EXISTS` keyword syntax. The pg_enum guard approach is functionally equivalent and more portable (works on Postgres < 12, whereas the `ADD VALUE IF NOT EXISTS` keyword requires Postgres 12+). The idempotency guarantee holds. A cosmetic clarification to the comment would improve accuracy but no code action is needed and this does not affect Wave 2 or Wave 3.

**NOTE-2 -- T-0034-003R spec says "within 5 lines" but description says "surrounding 10 lines"**

The ADR Test Spec Review (T-0034-003R description) states "load brain/lib/config.mjs as a string; for each of the three agent names, assert that the surrounding 10 lines contain the marker." The category description says "comment within 5 lines." The actual implementation in config.mjs places the comment directly adjacent to the agent name (within 1-2 lines), satisfying either specification. No issue in practice; noted for future spec consistency only.

---

## Doc Impact: NO

Release notes file is the only new doc artifact from Wave 1. It was authored as part of Step 1.2 and is correct. No further Agatha action required for Wave 1.

---

## Roz's Assessment

Wave 1 is clean. All 8 scope checks pass with no surprises. The implementation is faithful to the ADR spec including the corrections from my Test Spec Review: T-0034-003R applied correctly with `# non-extracted` comments adjacent to eva, poirot, and distillator; T-0034-061 locks the exact 16-entry count; the dual-function API (`session_state_dir` / `error_patterns_path`) is present and correctly contracts to different paths.

The migration idempotency pattern is correct and more portable than the keyword syntax; the comment is slightly imprecise but the behavior is right. The post-compact vs. session-boot fallback asymmetry (absolute vs. relative path) is intentional and correctly reasoned in both files' inline comments.

The 6 pre-existing pytest failures are confirmed pre-existing. Wave 1 introduced zero new failures. These belong to Wave 3 scope.

**Wave 1 is clear for Ellis to commit. Finding count: 0 BLOCKERs, 0 FIX-REQUIRED, 2 non-blocking notes.**
