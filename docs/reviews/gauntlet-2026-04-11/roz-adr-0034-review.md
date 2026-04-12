# Roz Test Spec Review — ADR-0034-gauntlet-remediation.md
## Date: 2026-04-11
## Verdict: APPROVED WITH ADDITIONS

---

## Review Summary

Reviewed test spec tables T-0034-001 through T-0034-060 across Wave 1, Wave 2, and Wave 3.

**Wave 1 is clear for Colby** with three conditions:
1. The ADR acceptance criterion for SOURCE_AGENTS total count must be corrected from 19 to 16 (see BLOCKER-1).
2. T-0034-003 must be rewritten to test a grep-verifiable comment pattern, not an open-ended convention (see BLOCKER-2).
3. Four additional tests have been authored and appended to the ADR (T-0034-061 through T-0034-064) to close the gaps identified below.

---

## Check Results (ADR Test Spec Review Mode)

| Check | Status | Details |
|---|---|---|
| Category coverage — all mandatory per step | PASS | Wave 1 covers contract boundary, schema parity, migration idempotency, wiring, Zod validation, failure messaging, and integration. Wave 2/3 cover all respective findings. |
| Failure:happy ratio | PASS | 25 failure-path tests vs 35 positive-path tests across 60 total; ratio complies with the ADR's own note. |
| Description quality — specific enough to implement | FAIL (2 items) | T-0034-003 and T-0034-019 under-specify the assertion mechanism (see issues). |
| Contract boundaries covered | PASS with addition | All 7 contract shapes from the Contract Boundaries table have corresponding tests. One gap: the installed `.claude/settings.json` pre/post divergence is unasserted (see addition T-0034-062). |
| Cases Cal missed | 4 additions authored | See T-0034-061 through T-0034-064 below. |
| UX doc check | N/A | ADR explicitly marks Wave 1-3 UX coverage as N/A. |

---

## Requirements Verification (Wave 1 Scope)

| # | Requirement | ADR Claims | Roz Verified | Finding |
|---|---|---|---|---|
| R1 | Fix silently-failing captures from 8 agents | Tests T-0034-001, T-0034-010, T-0034-011, T-0034-012 | Confirmed — Zod tests cover the new agents. | PASS |
| R2 | Atomic change across config.mjs + schema.sql + db.mjs + rest-api.mjs | Tests T-0034-004, T-0034-005, T-0034-008 | Confirmed — schema parity and rest-api wiring tested. | PASS |
| R3 | SOURCE_AGENTS count 19 (per Step 1.1 AC) | Acceptance criterion in ADR | **FAIL** — Current: 10 agents. Adding 6 new agents = 16 total, not 19. Arithmetic error in the AC. | BLOCKER-1 |
| R4 | ADR-0032 implementation: helper + session-boot + post-compact | Tests T-0034-014 through T-0034-020 | Confirmed — helper happy/fallback/isolation all covered. | PASS |
| R5 | SKILL.md SubagentStop template already has 9 agents | ADR Step 1.2 says "verify line ~410 already lists all 9 agents" | Confirmed — SKILL.md line 410 already contains the 9-agent condition. The installed `.claude/settings.json` still has 4 agents. This divergence is expected pre-Wave-1. | PASS (gap: no test locks the template state pre-update — added T-0034-062) |
| R9 | post-compact-reinject.sh reads from helper | T-0034-020 | Confirmed that post-compact-reinject.sh currently hardcodes `docs/pipeline/`. T-0034-020 as written tests the target state, which is correct Roz-first behavior. | PASS |

---

## ADR Internal Consistency

| Location | Issue | Severity |
|---|---|---|
| Step 1.1 Acceptance Criteria: "16 agents in the brain-extractor mapping table plus eva, poirot, distillator (19 total)" | The brain-extractor mapping table at `source/shared/agents/brain-extractor.md:43-53` has exactly 9 agents (cal, colby, roz, agatha, robert, robert-spec, sable, sable-ux, ellis). 9 + eva + poirot + distillator = 12, not 19. Adding the 6 new agents (sentinel, darwin, deps, brain-extractor, robert-spec, sable-ux) gives 10 existing + 6 new = 16 total. **The acceptance criterion says 19 but the correct figure is 16.** | BLOCKER-1 |
| T-0034-003: "explicitly marked in a comment as 'not extracted'" | The test says "a comment" but does not specify where, what text, or what tool to use to verify. A test that checks for an unspecified comment is un-automatable — Colby will not know what to write and Roz cannot assert it. | BLOCKER-2 |
| T-0034-019: "a write to one never appears in the other" | Passes the description quality bar at a high level but lacks a concrete mechanism: does the test write a file into dirA and stat dirB for its presence? Must be specified so the test is deterministic. | FIX-REQUIRED |

---

## Issues Found

**BLOCKER-1 — SOURCE_AGENTS count wrong in Step 1.1 Acceptance Criterion**
- File: `docs/architecture/ADR-0034-gauntlet-remediation.md`, Step 1.1 Acceptance Criteria section.
- What: "16 agents in the brain-extractor mapping table plus eva, poirot, distillator (19 total)" — the mapping table has 9 agents, not 16; the correct total after adding 6 new agents is 16, not 19.
- Why: If T-0034-001 asserts the list has 19 entries, it will fail even after a correct implementation. Conversely if Colby implements 16 and T-0034-001 asserts 19, the test is a false blocker.
- Fix: Change "16 agents in the brain-extractor mapping table plus eva, poirot, distillator (19 total)" to "9 agents in the brain-extractor mapping table (cal, colby, roz, agatha, robert, robert-spec, sable, sable-ux, ellis) plus eva, poirot, distillator (3 non-extracted), plus 4 new non-extracted agents not in the table (sentinel, darwin, deps, brain-extractor) = 16 total."

**BLOCKER-2 — T-0034-003 is not mechanically testable as written**
- File: `docs/architecture/ADR-0034-gauntlet-remediation.md`, Wave 1 test spec, row T-0034-003.
- What: "every non-extractor core agent in SOURCE_AGENTS (eva, poirot, distillator) is explicitly marked in a comment as 'not extracted' so future refactors don't remove them thinking they're orphans."
- Why: "a comment" is not a testable contract — there is no file specified, no comment format, no assertion mechanism. A test that checks for an unspecified comment either becomes a trivially-green no-op or cannot be written at all.
- Fix: Replace with: "A grep for `# not-extracted` (or equivalent canonical marker) in `brain/lib/config.mjs` matches at least three lines, one adjacent to each of `eva`, `poirot`, `distillator`. The exact comment text must be agreed on before Colby builds." Alternatively, eliminate the test and rely on the mapping-table cross-reference already covered by T-0034-001.

**FIX-REQUIRED — T-0034-019 isolation assertion mechanism under-specified**
- File: `docs/architecture/ADR-0034-gauntlet-remediation.md`, Wave 1 test spec, row T-0034-019.
- What: "a write to one never appears in the other" — no mechanism specified for how the test verifies this.
- Why: The test cannot be written deterministically without knowing whether it creates a sentinel file in dirA and checks dirB for its absence, or mocks the filesystem, or relies on the path comparison alone.
- Fix: Add to T-0034-019: "Mechanism: create a zero-byte sentinel file `sentinel.txt` in the resolved directory for worktreeA; assert `os.path.exists(dirB / 'sentinel.txt')` is False."

---

## Additions Authored (T-0034-061 through T-0034-064)

These tests close gaps in Wave 1 coverage not addressed by the existing 20 Wave 1 entries.

**T-0034-061 — SOURCE_AGENTS total count**
- Category: Contract boundary
- Description: `len(SOURCE_AGENTS)` in `config.mjs` equals exactly 16. Fail message lists the actual value and the 16 expected names. Regression guard against both over-extension (adding more agents without a spec) and under-extension (missing one of the 6 new agents).
- File: `tests/brain/enum-boundary.test.mjs`
- Rationale: T-0034-001 and T-0034-002 verify presence of specific values but do not lock the total count. Without this, future agents could be silently appended without an ADR.

**T-0034-062 — SKILL.md SubagentStop template contains 9-agent condition pre-update**
- Category: Template parity
- Description: `skills/pipeline-setup/SKILL.md` SubagentStop `if` condition contains each of the 9 brain-extractor target agents (cal, colby, roz, agatha, robert, robert-spec, sable, sable-ux, ellis) as literal strings. This locks the template state that Colby verifies in Step 1.2 and prevents silent drift between the template and this test.
- File: `tests/hooks/test_pipeline_setup_skill.py` (extend existing file)
- Rationale: The ADR says "verify line ~410 already lists all 9 agents" — without a test, this is a manual eyeball check that can silently regress.

**T-0034-063 — migration 008 file exists before Step 1.1 merges**
- Category: Pre-condition / Roz-first gate
- Description: After Wave 1 Step 1.1 runs, `brain/migrations/008-extend-agent-and-phase-enums.sql` exists on disk and contains the string `ADD VALUE IF NOT EXISTS`. This test is expected to FAIL before Colby builds (correct Roz-first behavior).
- File: `tests/brain/enum-boundary.test.mjs`
- Rationale: T-0034-006 tests the migration's idempotency behavior against a mock pool but does not verify the file was created. A migration block in db.mjs that references a missing file silently skips (see `existsSync` check in migrations 001-006). Without this file-existence gate, migration 008 could be registered in db.mjs but silently do nothing.

**T-0034-064 — `error_patterns_path()` is a separate exported function from `session_state_dir()`**
- Category: ADR-0032 helper API contract
- Description: The exported API of `pipeline-state-path.sh` exposes TWO distinct shell functions: `session_state_dir` and `error_patterns_path`. Sourcing the file and calling each function by name produces different paths: `session_state_dir` returns something under `~/.atelier/pipeline/`; `error_patterns_path` returns something under the project root. Tests that call only `pipeline_state_dir` (singular) without testing `error_patterns_path` independently leave the ADR-0032 "error-patterns.md stays in-repo" decision unverified.
- File: `tests/hooks/test_pipeline_state_path.py`
- Rationale: The ADR Notes for Colby item 4 explicitly flags this dual-function contract. T-0034-017 covers the happy path for `error_patterns_path()` but there is no test verifying that sourcing the helper and calling both functions by their distinct names works — i.e., that Colby did not accidentally expose a single function that branches on an argument.

---

## Unfinished Markers

Checked `ADR-0034-gauntlet-remediation.md` for TODO/FIXME/HACK/XXX: zero matches. No unfinished markers.

---

## Doc Impact: NO

This review does not change any documentation beyond annotations to the ADR itself (the `## Roz Test Spec Review` section appended below). The ADR's own doc impact is Wave 5 (Agatha), explicitly deferred.

---

## Wave-by-Wave Assessment

### Wave 1 (20 tests, T-0034-001 through T-0034-020)

Coverage is solid across the four concern areas: enum sync, Zod validation, migration idempotency, and ADR-0032 helper. Failure-path coverage is strong: T-0034-007 (migration failure isolation), T-0034-012 (invalid agent still rejected), T-0034-013 (Zod failure logs loudly), T-0034-015 (helper fallback on all-env-missing), T-0034-016 (collision check). Two blockers must be resolved before Colby starts: BLOCKER-1 (count correction) and BLOCKER-2 (T-0034-003 rewrite). One FIX-REQUIRED (T-0034-019 mechanism). Four additions supplied.

**Wave 1 is clear for Colby after the two blockers in the ADR are corrected (see "Roz Test Spec Review" annotation appended to the ADR).**

### Wave 2 (25 tests, T-0034-021 through T-0034-045)

Coverage is strong. T-0034-026 and T-0034-027 (library adoption via grep) are well-scoped lint-style tests consistent with project precedent. The four hook test entries (T-0034-028–039) follow the `test_enforce_colby_paths.py` template precisely. Migration runner tests (T-0034-040–044) cover the three critical behaviors (unapplied, already-applied, fail-soft) and the line-count regression guard. One minor gap: there is no test for T-0034-025's negative case — what does `hook_lib_get_agent_type` return when NEITHER `agent_type` NOR `tool_input.subagent_type` is present? (Should return empty string / empty output.) Not a blocker; T-0034-023 and T-0034-024 cover both input forms.

### Wave 3 (15 tests, T-0034-046 through T-0034-060)

T-0034-046 through T-0034-048 (suite greening) are well-structured: delete the self-referential gate, update the count assertion, verify exit 0. T-0034-051 through T-0034-053 (XSS) use the ADR-acknowledged lint-style approach appropriately. T-0034-054 through T-0034-056 (gracefulShutdown ordering) are precise: sequence counter pattern is the correct verification mechanism for async ordering. T-0034-057 through T-0034-060 (LLM null guard) cover all six error cases described in the implementation plan. Coverage is complete.

---

## Roz's Assessment

The ADR-0034 test spec is professionally structured: 60 tests with good failure-path density, clear contract-boundary framing, and explicit wave gating. The two blockers (SOURCE_AGENTS count arithmetic, T-0034-003 un-automatable comment test) are both in Wave 1 and must be corrected before handing off to Colby — a failing count assertion in T-0034-001/T-0034-061 would stall the wave on a spec error, not a code error. The four additions (T-0034-061 through T-0034-064) close gaps that are load-bearing: the count lock, the SKILL.md template parity, the migration file existence gate, and the dual-function helper API.

After the ADR corrections noted above are applied, the spec defines correct behavior clearly enough that Colby can implement deterministically and I can verify against concrete assertions.

**Wave 1 is clear for Colby.**
