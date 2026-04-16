# QA Report -- ADR-0041 Wave Sweep -- 2026-04-16

## Verdict: FAIL (2 MUST-FIX items; not cosmetic)

Blocker-adjacent: Step 2 (classifier-score removal) and Step 5 (cost-table
update) are BOTH partially implemented. Verdict criteria state PASS requires
zero BLOCKERs AND at most 2 cosmetic MUST-FIX items. These two are real
contract gaps, not cosmetic; both need to be routed to Colby before Ellis.

Zero regressions. 59/59 ADR-0041 tests pass. The green test suite under-
asserts: both MUST-FIX defects slipped through because no test was watching.

---

## Summary

ADR-0041 replaces the size-dependent model table + universal scope classifier
with a 4-tier task-class model. 37 files changed; Steps 1, 3, 4, 6, 7, and 8
look clean. Steps 2 (pipeline-orchestration.md cleanup) and 5
(`telemetry-metrics.md` cost-table) are partially implemented:

- **Step 2 residual:** `source/shared/rules/pipeline-orchestration.md:683-684`
  still carries the old classifier framing: "Score files + complexity
  signals. Score >=3 -> Opus. Brain failures +3. Large always Opus." This is
  exactly the content ADR-0041 Decision-Removed list calls out (classifier
  score framing). The installed mirror at
  `.claude/rules/pipeline-orchestration.md` carries the same line.
- **Step 5 gap:** `telemetry-metrics.md` Cost Estimation Table still lists
  only `claude-opus-4`, `claude-sonnet-4-5`, `claude-haiku-3-5`. ADR-0041
  §Step 5 Acceptance requires a `claude-opus-4-7` row and an ADR-0041
  footnote on the Per-Invocation Cost Estimates table. Neither
  `claude-opus-4-7` nor `ADR-0041` appears in the file (`grep -c` = 0 for
  both).

The per-M-token substring hints (0.11, 0.33, 2.22) WERE added at line 124 --
that is what the test suite checked for, and it passed -- but that is NOT
the contract ADR §Step 5 Acceptance specified.

Full test suite: 1595 pass / 107 fail. Delta vs. pre-build baseline: +60 new
passes, 0 new regressions. The 107 remaining failures are all pre-existing
on main; not introduced by this build.

---

## Findings

### MUST-FIX -- queued before commit

#### 1. `source/shared/rules/pipeline-orchestration.md` -- Step 2 residual classifier text

**File / line:** `source/shared/rules/pipeline-orchestration.md:683-684` (and
the mirror at `.claude/rules/pipeline-orchestration.md` same offset)

**What:** The file still contains:

```
**Colby model selection:** See pipeline-models.md. Score files + complexity
signals. Score >=3 -> Opus. Brain failures +3. Large always Opus.
```

ADR-0041 §Decision Rule-Table-Replacement-Scope lists "classifier score /
Score >= 4 references" and "universal scope classifier" as content removed
from the rule file, and Step 2 Acceptance calls for zero "classifier score"
/ "Sonnet (classifier)" / "size-dependent model" references. The
`Score >=3 -> Opus` + `Brain failures +3` block is a direct carry-over of
the scoring-classifier framing the ADR retires.

**Why:** Eva reads both `pipeline-models.md` AND `pipeline-orchestration.md`
at pipeline start. When Eva hits this line she will apply the score-based
lookup, not the tier-table lookup. The rule-file producer is correct (the
4-tier table is in `pipeline-models.md`) but the consumer protocol in
`pipeline-orchestration.md` still points at the retired mechanism. Two
sources of truth = Eva chooses wrong at runtime, exactly the retro lesson
005 failure mode.

**Suggested resolution:** Colby replaces the paragraph with a pointer to
`pipeline-models.md` §Per-Agent Assignment Table + §Promotion Signals, no
score-based language. Something like: "Colby model/effort: see
`pipeline-models.md` §Per-Agent Assignment Table; effort adjusts by
promotion signals (Large, auth/security, new module). No discretion." Same
edit applied to the `.claude/` mirror. ~3 lines in each file.

**Test-gap note:** ADR test-spec IDs T-0041-040/041/042 explicitly asked
for grep assertions on "classifier score" / "Sonnet (classifier)" /
`pipeline-models.md` references in this file. The 59-test suite does NOT
include these assertions in any of the three test files. That is why this
slipped through.

---

#### 2. `source/shared/references/telemetry-metrics.md` -- Step 5 contract gap

**File / line:** `source/shared/references/telemetry-metrics.md:116-120`
(Cost Estimation Table) and `:182-186` (Per-Invocation Cost Estimates
table)

**What:** The Cost Estimation Table still lists only three rows:
`claude-opus-4`, `claude-sonnet-4-5`, `claude-haiku-3-5`. ADR-0041 §Step 5
Acceptance requires a fourth row: `claude-opus-4-7` with input/output
pricing reflecting the 4.7 tokenizer inflation (~$0.0175 / $0.0875 per 1k,
1.17x midpoint). The Per-Invocation Cost Estimates table does NOT cite
ADR-0041 in any footnote or annotation. Neither `claude-opus-4-7` nor
`ADR-0041` appears anywhere in the file (`grep -c` returns 0 for both).

**Why:** ADR-0029's budget-estimate gate consumes this table to compute
`cost_usd`. With Tier 2/3 work now executing on Opus 4.7 (GA 2026-04-16),
cost computations silently fall back to the Opus 4.6 row, under-counting by
the tokenizer-inflation multiplier. This is a living-artifact update Cal
explicitly scoped to this ADR (§ADR-0029 + telemetry-metrics.md Update).
Missing it orphans the producer from the Validation-Pipeline consumer: the
rollback threshold is "cost ratio > 2.0x", which is computed against a
pricing row that does not yet exist.

The per-M-rate hint at line 124 is useful but is NOT the same contract as
"Cost Estimation Table row for `claude-opus-4-7`."

**Suggested resolution:** Colby adds `claude-opus-4-7` row to the Cost
Estimation Table with 1.17x-inflated pricing, adds a footnote on the
Per-Invocation Cost Estimates table citing ADR-0041 as the tier-epoch,
optionally annotates the existing Sonnet row as legacy (pre-0041 captures
stay interpretable). ~10 lines total.

**Test-gap note:** ADR test-spec IDs T-0041-043/044 explicitly asked for
grep assertions on `claude-opus-4-7` row and ADR-0041 footnote. The docs
test file asserts only on the per-M-rate substrings (0.11, 0.33, 2.22).
The `claude-opus-4-7` row assertion is missing.

---

### FIX-REQUIRED -- none

---

### NIT -- cosmetic

#### 3. Sixth promotion signal not in ADR Decision table

**File:** `source/shared/rules/pipeline-models.md:43` and mirrors

**What:** The implemented Promotion Signals table carries 6 rows
(`auth/security`, `Large`, `Poirot final juncture`, `read-only evidence`,
`mechanical task`, `new module / service`). The ADR §Decision Promotion
Signals table has only the first 5 rows. The 6th row
("new module / service +1 rung") is consistent with Tier 4's
"Large + new module" header hint but isn't in the ADR's explicit Decision
table.

**Why this is a NIT, not a defect:** The test suite parametrizes over
`"new module"` as a required signal phrase
(`test_adr0041_rule_structure.py:152`), so Roz's test spec clearly expected
this signal. The ADR's Tier 1/2/3/4 header column ("Effort +1 when") also
references `Large + new module` in the Tier 4 row. The ADR and the
implementation agree on intent; the Decision Promotion Signals table just
didn't enumerate this signal as its own row. ADRs are immutable so this
can't be patched in place -- future related ADR can codify. No action
required now.

---

#### 4. Test suite under-asserts 6 spec rows (T-0041-040/041/042/043/044 + T-0041-051 through T-0041-054)

**Files:** `tests/test_adr0041_docs.py`, `tests/test_adr0041_rule_structure.py`

**What:** The 59-test suite green-lighted MUST-FIX #1 and #2 because no
test watched. Specifically uncovered:

- **T-0041-040/041/042:** pipeline-orchestration.md cleanup (classifier
  score, Sonnet classifier, pipeline-models.md pointer). No assertions in
  any of the three test files.
- **T-0041-043:** `claude-opus-4-7` row presence. Docs test asserts "2.22"
  per-M substring only.
- **T-0041-044:** ADR-0041 footnote in telemetry-metrics.md. Not asserted.
- **T-0041-051 through T-0041-054:** Validation Pipeline protocol content
  (ADR-0035 baseline, FPQR methodology, 2.0x rollback trigger, telemetry
  effort-field addition). ADR content is correct (grep confirms 23 hits),
  but no test asserts presence.

**Suggested resolution:** Roz follow-up pass after MUST-FIX #1 + #2 land:
add 9 assertions covering the gap. Since these are Roz's own test files,
the fix is adding `assert "X" in text` lines -- straightforward. Not a
commit blocker once MUST-FIX #1 + #2 are in -- but without this coverage
the next rule-file change will slip the same way.

---

## Coverage Confirmation (Cal's 6 Test Spec Categories)

| Category | Assertions in ADR | Assertions in suite | Status |
|----------|------------------:|--------------------:|--------|
| Structure (T-0041-001 through 007) | 7 | 14 rule_structure tests cover this | Covered |
| Supersession (T-0041-008 through 012) | 5 | 5 banned-marker params | Covered |
| Promotion signals (T-0041-013 through 017) | 5 | 5 signal-phrase params | Covered |
| Base assignments (T-0041-018 through 024) | 7 | Subsumed by frontmatter test (30 asserts) + rule tier-row proximity check | Covered |
| Frontmatter consistency (T-0041-025 through 039) | 30 (15 agents x 2 platforms) | 30 asserts parameterized | Covered in full |
| Orchestration cleanup (T-0041-040 through 042) | 3 | NOT covered by any test; grep reveals real residual content at line 683-684 | **Gap + Defect -- see MUST-FIX 1** |
| Cost table (T-0041-043 through 045) | 3 | Only per-M-rate substrings covered; `claude-opus-4-7` row + ADR-0041 footnote NOT asserted AND NOT present | **Gap + Defect -- see MUST-FIX 2** |
| Installed mirrors (T-0041-046, 047) | 2 | Both asserted (byte-identical source; Cursor Tier 1/4 present) | Covered |
| Compatibility / setup skill (T-0041-048 through 050) | 3 | Covered by "2.1.89 OR effort" disjunctive test | Covered loosely; SKILL.md does contain "2.1.89", "effort", and "still functions" phrasing |
| Validation protocol (T-0041-051 through 054) | 4 | NOT covered by any test; grep confirms content present in ADR (23 hits for ADR-0035/FPQR/rollback/2.0x) | Content present; test gap (see NIT 4) |
| Docs (T-0041-055, 056) | 2 | Both asserted | Covered |

**Net:** 8 of 11 categories fully green. 2 categories (orchestration
cleanup, cost table) are both un-asserted AND reveal real defects on
inspection. 1 category (validation protocol) is content-verified but
test-gapped.

---

## Requirements Verification

| # | Requirement | Colby claim | Roz verified | Finding |
|---|-------------|-------------|-------------|---------|
| R1-R10 | ADR + tier model + rules + Sonnet removal | yes | yes | via `pipeline-models.md` rewrite; 0-match grep for `sonnet` in all 30 frontmatters |
| R11 | Agatha split conceptual/reference | yes | yes | Tier 2 + Tier 1 rows present, reference-mode noted |
| R12 | 30 frontmatter updates | yes | yes | 15 x 2 files correct |
| R13 | Source + 2 installed mirrors | yes | yes | `.claude/rules/pipeline-models.md` byte-identical, `.cursor-plugin/rules/pipeline-models.mdc` fully synced with frontmatter wrapper |
| R14 | `pipeline-orchestration.md` classifier refs removed | **partial** | **partial -- see MUST-FIX 1** | stale "Score >=3 -> Opus" at line 683-684 |
| R15 | `telemetry-metrics.md` update | **partial** | **partial -- see MUST-FIX 2** | per-M-rates added; Opus 4.7 row + ADR-0041 footnote absent |
| R16 | Compat + setup warning | yes | yes | SKILL.md:10 carries "2.1.89" + "effort" warning, non-blocking |
| R17 | Vertical slice | yes | yes | producer->consumer mapping intact (modulo R14/R15 gaps above) |
| R18 | Validation pipeline design | yes | yes | §Validation Pipeline has baseline, metrics, thresholds, rollback, telemetry addition |

---

## Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` on all 37 changed files: 0 hits in
production content. Clean.

---

## Full-Suite Regression Confirmation

Per `<qa-evidence>` block:
- Pre-build baseline (main): 108 fail / 1535 pass
- Post-build (worktree): 107 fail / 1595 pass
- Delta: **+60 new passes, 1 pre-existing fail resolved, 0 new regressions**
- ADR-0041-specific: 59/59 pass

Regression check: PASS.

---

## Doc Impact: NO

ADR-0041's documentation consumers (`technical-reference.md`,
`user-guide.md`, SKILL.md, `telemetry-metrics.md` per-M-rates) are updated
in this build. Agatha does not need a separate doc pass. The MUST-FIX on
`telemetry-metrics.md` is Colby's scope (Step 5), not a documentation gap.

---

## Roz's Assessment

This is a close call but the verdict is FAIL because two MUST-FIX items
are real contract gaps, not cosmetic noise, and the PASS criteria
explicitly require "no BLOCKER and <= 2 MUST-FIX items that are cosmetic."

The substance of ADR-0041 is solidly implemented. The 4-tier table reads
cleanly and is humanly lookup-able. All 30 frontmatter mirrors are
correct. Cursor `.mdc` is fully synchronized. Technical-reference Model
Selection section is a proper rewrite, not a stub. The pipeline-models.md
producer is correct. The frontmatter consumers are correct. The test
suite is green on what it watches.

What's broken is the wiring:
- **Step 2**: `pipeline-orchestration.md` consumer still carries the
  retired score-classifier language. Same file, same Eva context.
  Producer says "use the tier table", consumer says "score files, >=3 ->
  Opus, brain failures +3." Eva reads both. Two sources of truth in Eva's
  always-loaded context = non-deterministic runtime behavior on the next
  pipeline. Retro lesson 005 territory.
- **Step 5**: `telemetry-metrics.md` living-artifact update is half-done.
  Per-M-hint added (good), Opus 4.7 row and ADR-0041 footnote absent
  (bad). Budget gate now under-counts Tier 2/3 cost by the tokenizer-
  inflation multiplier until fixed.

Both are 10-line edits. Colby can land MUST-FIX #1 + #2 in a single
sub-wave. After that the test gap (NIT #4) is worth a follow-up Roz pass
so the next rule-file change doesn't slip through the same hole -- but
that's not a commit blocker.

Route MUST-FIX #1 (pipeline-orchestration.md:683-684 + mirror) and
MUST-FIX #2 (telemetry-metrics.md Cost Estimation Table + footnote) to
Colby. Re-run scoped verification after.

One rung up on Roz's own discipline: when Cal's §Test Specification lists
a test ID, every ID gets an assertion, even if parameterization collapses
rows. The "56 rows -> 59 assertions" count here masked 9 genuinely
missing assertions. Cal's spec was solid; the test authoring was light.
