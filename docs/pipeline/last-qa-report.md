# QA Report -- 2026-04-06

## ADR-0027: Brain-Hydrate Scout Fan-Out -- Scoped Re-Run (Poirot 6-Finding Fix Verification)

### Verdict: PASS

| Check | Status | Details |
|-------|--------|---------|
| ADR-0027 Tests (scoped) | PASS | 36/36 passed, 0 failed, 0 skipped (0.13s) |
| Poirot Finding 1: no git log shell imperative in extraction rules | PASS | SKILL.md line 305 explicitly states "no shell access, no `git log` commands" in the extraction rules section |
| Poirot Finding 2: atelier_relation in subagent constraints | PASS | SKILL.md line 176: `atelier_relation` listed in the extraction agent `<constraints>` block |
| Poirot Finding 3: skipped scouts excluded from completeness check | PASS | SKILL.md line 136: "Skipped scouts (per skip conditions above -- zero-file categories, user-excluded sources, or scope-based exclusions) are excluded from this check and do not count as mismatches." |
| Poirot Finding 4: dry-run notes in Phase 2a and Phase 2b | PASS | Phase 2a: SKILL.md line 128 "Dry-Run Mode (Phase 2a)" subsection present. Phase 2b: SKILL.md line 187 "Dry-run mode (Phase 2b)" paragraph present |
| Poirot Finding 5: preamble exemption note near invocation template | PASS | SKILL.md line 150: "Note: This subagent is the intentional exception to the agent-preamble rule..." appears immediately before the invocation template |
| Poirot Finding 6: split rounding rule stated | PASS | SKILL.md line 124: "if the count is odd, the first sub-scout gets the larger half" |
| Unfinished Markers | PASS | 0 TODO/FIXME/HACK/XXX in changed file |
| Regression (pre-existing tests) | PASS | All 36 tests pass -- no regression introduced by Colby's fixes |

---

## Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| 1 | No git log shell imperative in extraction rules | Fixed | PASS | Line 305: "no shell access, no `git log` commands" -- Sonnet subagent explicitly prohibited from running shell commands in the Git History extraction section |
| 2 | atelier_relation in subagent constraints | Fixed | PASS | Line 176: `atelier_relation` appears in the extraction agent `<constraints>` block, matching the constraint placement required by Poirot |
| 3 | Skipped scouts excluded from completeness check | Fixed | PASS | Line 136: completeness check paragraph explicitly enumerates skip conditions and states they "do not count as mismatches" |
| 4 | Dry-run notes in Phase 2a and 2b | Fixed | PASS | Both phases have their own dedicated dry-run subsection -- Phase 2a at line 128, Phase 2b at line 187 -- with distinct behaviors documented (scouts still fire in 2a; subagent must NOT call agent_capture in 2b) |
| 5 | Preamble exemption note near invocation template | Fixed | PASS | Line 150: note is co-located with the invocation template in the `extract-capture` procedure, not isolated elsewhere |
| 6 | Split rounding rule stated | Fixed | PASS | Line 124: "if the count is odd, the first sub-scout gets the larger half" -- unambiguous, deterministic |

---

## Test Results

```
pytest tests/adr-0027/test_brain_hydrate_scout_fanout.py -v
36 passed, 1 warning in 0.13s
```

All 36 tests pass: 10 structural (T-0027-001 through T-0027-010), 9 preservation
(T-0027-011 through T-0027-019), 8 failure/edge (T-0027-020 through T-0027-027),
4 integration (T-0027-028 through T-0027-031), 5 Roz-added (ROZ-001 through ROZ-005).

No regressions. All tests that passed in the initial QA pass continue to pass.

---

## Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` in `skills/brain-hydrate/SKILL.md`: 0 matches.

---

## Issues Found

None. All 6 Poirot findings are correctly addressed.

No BLOCKERs. No FIX-REQUIRED items.

Pending items from prior QA pass (not affected by this fix):
- `.claude/rules/pipeline-orchestration.md` sync (requires `/pipeline-setup`)
- `.cursor-plugin/skills/brain-hydrate/SKILL.md` sync (requires `/pipeline-setup`)
These remain unchanged -- Colby's 6-finding fix did not touch either file.

---

## Doc Impact: YES

`skills/brain-hydrate/SKILL.md` is the deliverable. All 6 fixes are in-place edits within
that file. No separate documentation affected.

---

## Roz's Assessment

Colby's 6-finding fix is clean and complete. Each Poirot finding maps to a specific
line in SKILL.md and the fix is exact -- no over-engineering, no collateral changes.
The two most structurally important fixes (Finding 1: no shell imperative; Finding 3:
skipped scout exclusion from completeness check) are correctly placed at the logical
boundary where the rule applies. Finding 4 (dry-run notes in both phases) correctly
distinguishes the two behaviors: scouts still fire in Phase 2a dry-run to give the
user a preview, but the Sonnet subagent writes nothing in Phase 2b dry-run. That
asymmetry is preserved verbatim in the two subsections.

All 36 ADR-0027 tests continue to pass. No regression.

**Verdict: PASS. Route to Ellis.**
