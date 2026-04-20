# QA Report — 2026-04-20 (Wave sweep: enforce-sequencing.sh new guards)

## Verdict: PASS

Wave sweep covers two new guards in `source/claude/hooks/enforce-sequencing.sh`:
Gate 0b (investigator worktree enforcement) and Gate 5 amendment (empty
`docs/product/` exempts Robert review).

| Check | Status | Details |
|-------|--------|---------|
| Mirror byte-identical (source → .claude) | PASS | `diff` returns 0 |
| Targeted suite: `tests/hooks/test_enforce_sequencing.py` | PASS | 39/39 |
| Gate 0b scoped to investigator only | PASS | guard wrapped in `if [ "$SUBAGENT_TYPE" = "investigator" ]` (line 71); no impact on ellis/agatha/colby paths |
| Gate 0b fails open when worktree_path null/absent | PASS (by inspection) | `[ -n "$WORKTREE_PATH" ] && [ "$WORKTREE_PATH" != "null" ]` — no dedicated test for the absent case, see FIX-REQUIRED below |
| Gate 5 amendment reads `product_specs_dir` from config | PASS | `jq -r '.product_specs_dir // "docs/product"' "$CONFIG"` with correct fallback; joined with `PROJECT_ROOT` |
| Gate 5 amendment: empty product dir exempts Robert | PASS | covered by `test_gate5_no_product_specs_ellis_allowed` |
| Gate 5 amendment: present `.md` specs still block | PASS | covered by `test_gate5_product_specs_exist_ellis_still_blocked` |
| Gate 5 non-amendment regressions | PASS | T_GATE5_001..005 all green |
| Existing Ellis/Agatha/CI-Watch regressions | PASS | T_0003_042..057, T_0013_051..059, T_GATE3/4_* all green |
| Pre-existing failures re-introduced | NO | scope of change limited; targeted suite fully green |

### Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| 1 | Gate 0b fires when investigator invoked without worktree_path in prompt and PIPELINE_STATUS carries worktree_path | BLOCK | BLOCK confirmed (line 80 exit 2, message contains "worktree") | OK |
| 2 | Gate 0b allows investigator when prompt references worktree_path | ALLOW | ALLOW confirmed | OK |
| 3 | Gate 0b fails open when worktree_path is empty/null | ALLOW | ALLOW by inspection — conditional skip at line 73 | Missing dedicated test |
| 4 | Gate 0b only applies to investigator subagent_type | no effect on others | Confirmed — guard scope ends at line 85 before Ellis gates | OK |
| 5 | Gate 5 amendment: empty `docs/product/` exempts Robert review on medium/large | ALLOW | ALLOW confirmed (test_gate5_no_product_specs_ellis_allowed) | OK |
| 6 | Gate 5 amendment: present .md specs preserve BLOCK | BLOCK | BLOCK confirmed (test_gate5_product_specs_exist_ellis_still_blocked) | OK |
| 7 | Gate 5 amendment: absent `docs/product/` directory preserves original BLOCK | BLOCK | Confirmed by inspection — `if [ -d ... ]` skipped when dir absent; robert_reviewed check proceeds | Not covered by a dedicated test |
| 8 | Mirror byte-identical | identical | diff returns 0 | OK |

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` on changed files: 0 matches in
`source/claude/hooks/enforce-sequencing.sh`, `.claude/hooks/enforce-sequencing.sh`,
or `tests/hooks/test_enforce_sequencing.py`.

### Issues Found

**BLOCKER** (pipeline halts): None.

**FIX-REQUIRED** (queued before commit):

1. `tests/hooks/test_enforce_sequencing.py` — missing explicit test case:
   **Gate 0b fail-open when `worktree_path` is absent from PIPELINE_STATUS
   on an investigator invocation.** Current coverage verifies the BLOCK
   path (worktree_path present, prompt missing it) and the ALLOW path
   (worktree_path present, prompt includes it), but does not confirm the
   third branch: worktree_path absent → allow. Logic is correct by code
   inspection (lines 72-73), but the contract should be locked down with
   a regression test so a future refactor cannot silently flip the
   default.

2. `tests/hooks/test_enforce_sequencing.py` — missing explicit test case:
   **Gate 5 amendment when `docs/product/` directory is absent.** The
   amendment has three paths: dir absent (preserve original BLOCK), dir
   present and empty of .md (exempt), dir present with .md specs (BLOCK).
   Only the latter two are covered. Add a regression test that asserts
   BLOCK when `docs/product/` does not exist AND robert_reviewed is
   false. Without this, a future change to the `[ -d
   "$PROJECT_ROOT/$PRODUCT_SPECS_DIR" ]` branch could accidentally
   convert "dir absent" to "exempt", silently bypassing Robert review.

These are FIX-REQUIRED rather than BLOCKER because the guards are
correct by inspection and the 39 existing tests do cover the primary
positive and negative cases. Adding the two regression tests locks down
the defensive contract.

### Doc Impact: NO

Hook-internal guards with no user-facing surface change. Behavior is
additive (Gate 0b is new; Gate 5 amendment is a conditional carve-out
that only relaxes enforcement when the dir exists and is empty of .md).
No ADR, README, or user guide updates required.

### Roz's Assessment

Clean, additive work. Gate 0b is well-scoped (investigator-only, fails
open on empty/null worktree_path), and Gate 5 amendment uses a
conservative "exists and empty" check that preserves original
enforcement in the default case. The byte-identical mirror and green
targeted suite (39/39) are enough to ship this wave. The two missing
test cases are test-surface gaps, not logic defects — Colby should add
them in a follow-up so the fail-open and dir-absent contracts are
locked to regression tests, but they do not block this wave.

Minor style note for future hardening (not FIX-REQUIRED): Gate 0b uses
POSIX `case` glob matching in `case "$INVOCATION_PROMPT" in
*"$WORKTREE_PATH"*)`. If a worktree path ever contained shell glob
metacharacters (`*`, `?`, `[`), matching could misbehave. Worktree
paths are typically filesystem paths and safe, but a belt-and-suspenders
approach would prefer literal-substring matching. Filed as a style note
only — no action required this wave.
