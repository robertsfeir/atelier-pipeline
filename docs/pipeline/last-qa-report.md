# QA Report -- 2026-04-04
*Reviewed by Roz*

## Verdict: FAIL

### Scope
Scoped QA -- 5 changes across 9 source files.

**Files changed:**
- `source/shared/rules/agent-system.md` (core agent constant 11->14)
- `source/shared/agents/colby.md` (Re-invocation Mode section added)
- `source/shared/agents/roz.md` (Scoped Re-run Mode section added)
- `source/shared/rules/default-persona.md` (context eviction protocol replaced)
- `source/shared/agents/distillator.md` (observation masking constraint added)
- `source/claude/agents/colby.frontmatter.yml` (maxTurns 100->75)
- `source/cursor/agents/colby.frontmatter.yml` (maxTurns 100->75)
- `source/claude/agents/roz.frontmatter.yml` (maxTurns 100->60)
- `source/cursor/agents/roz.frontmatter.yml` (maxTurns 100->60)

---

### Checks

| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | XML well-formedness (colby.md) | PASS | `<workflow>` tag opens line 20, closes line 45. Re-invocation Mode section is inside `<workflow>`. No orphaned tags. |
| 2 | XML well-formedness (roz.md) | PASS | `<workflow>` tag opens line 19, closes line 51. Scoped Re-run Mode section is inside `<workflow>`. No orphaned tags. |
| 3 | XML well-formedness (default-persona.md) | PASS | `<protocol id="context-eviction">` opens and closes correctly. Content replaced cleanly. |
| 4 | XML well-formedness (distillator.md) | PASS | New constraint bullet added inside `<constraints>` block. No structural issues. |
| 5 | Core constant count | PASS | Header says 14. List contains: cal, colby, roz, ellis, agatha, robert, robert-spec, sable, sable-ux, investigator, distillator, sentinel, darwin, deps. Count: 14. Matches. |
| 6 | Colby TDD constraint preserved (R15) | PASS | constraint at line 58: "Make Roz's pre-written tests pass. Do not modify or delete her assertions." Intact. Build Mode at line 29 reads "run Roz's tests first (confirm they fail for the right reason)." Intact. |
| 7 | Roz test-first instructions preserved | PASS | Test Authoring Mode (lines 29-36) fully intact: "Tests define the target BEFORE Colby builds." constraint line 72: "Test-first: test assertions define correct behavior BEFORE Colby builds." Both intact. |
| 8 | New sections inside `<workflow>` | PASS | Colby's Re-invocation Mode is at lines 39-44, inside `<workflow>` (lines 20-45). Roz's Scoped Re-run Mode is at lines 44-50, inside `<workflow>` (lines 19-51). Both correctly scoped. |
| 9 | Claude/Cursor frontmatter maxTurns in sync | PASS | Colby: both claude and cursor frontmatter show maxTurns: 75. Roz: both claude and cursor frontmatter show maxTurns: 60. Synchronized. |
| 10 | Preamble exemption clause -- Ellis-only | PASS | `source/shared/references/agent-preamble.md` line 10: "Exemption: Ellis (commit agent) skips DoR/DoD and brain capture." The new Re-invocation Mode and Scoped Re-run Mode are fast-path protocols within each agent's `<workflow>` section, not preamble exemptions. No cross-reference breakage. The preamble correctly exempts only Ellis. |
| 11 | TODO/FIXME/HACK/XXX markers | PASS | Zero matches in all 9 changed source files. Matches in roz.md and colby.md are instruction text (telling agents to check for markers), not actual markers. |
| 12 | Tests (scoped -- line count regression) | FAIL | T-0023-030: colby.md is 97 lines, exceeds <=95 limit. T-0023-040: roz.md is 101 lines, exceeds <=100 limit. Both pass on baseline (git HEAD). New failures introduced by this changeset. |
| 13 | Tests (full suite) | FAIL | 2 new test failures introduced. 48 other failures are pre-existing (verified by baseline run). See details below. |
| 14 | Unfinished markers | PASS | Zero unfinished markers in changed files. |

---

### Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| 1 | Core constant 11->14, add sentinel/darwin/deps | Yes | YES | Line 302: "14 agents." Line 307 list contains all 14. Count confirmed. |
| 2 | Colby Re-invocation Mode added inside `<workflow>` | Yes | YES | Lines 39-44 inside `<workflow>` block. Well-formed. |
| 3 | Roz Scoped Re-run Mode added inside `<workflow>` | Yes | YES | Lines 44-50 inside `<workflow>` block. Well-formed. |
| 4 | maxTurns: Colby 100->75 (claude+cursor) | Yes | YES | Both frontmatter files show maxTurns: 75. |
| 5 | maxTurns: Roz 100->60 (claude+cursor) | Yes | YES | Both frontmatter files show maxTurns: 60. |
| 6 | Eva context eviction replaced with aggressive mechanical eviction | Yes | YES | Protocol at lines 142-161 of default-persona.md. New content adds: Telemetry trend query and Brain capture model to disposable list, plus Retained/Mechanical reinforcement clauses. Well-formed. |
| 7 | Distillator observation masking constraint added | Yes | YES | New bullet at line 90 of distillator.md. Inside `<constraints>` block. Content is correct: strips raw observation payloads, preserves derived facts. |
| 8 | Colby TDD (R15) not removed | Yes | YES | Confirmed intact at colby.md lines 29 and 58. |
| 9 | Roz test-first instructions not removed | Yes | YES | Confirmed intact at roz.md lines 29-36 and line 72. |
| 10 | Line count limits (ADR-0023: colby <=95, roz <=100) | Not mentioned | FAIL | colby.md: 97 lines (2 over). roz.md: 101 lines (1 over). Both tests pass on baseline. These are regressions introduced by the new workflow sections. |

---

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` in changed source files: **0 actual markers**

(Matches in roz.md and colby.md are instruction prose, not actual markers.)

---

### Issues Found

**BLOCKER** -- `source/shared/agents/colby.md`, line count: colby.md is 97 lines, exceeds the ADR-0023 limit of <=95 lines. Test T-0023-030 fails. The Re-invocation Mode section (lines 39-44, 6 lines including blank) pushed the file over the limit. The limit was established by ADR-0023 (reduction sprint). Adding content without trimming equivalent content elsewhere violates the constraint. Colby must trim 2 lines from colby.md while preserving all behavioral content.

**BLOCKER** -- `source/shared/agents/roz.md`, line count: roz.md is 101 lines, exceeds the ADR-0023 limit of <=100 lines. Test T-0023-040 fails. The Scoped Re-run Mode section (lines 44-50, 7 lines including blank) pushed the file over the limit. Colby must trim 1 line from roz.md while preserving all behavioral content.

---

### Pre-Existing Failures (not caused by this changeset)

Verified by running full suite on git HEAD (stash baseline). The following 48 failures existed before this changeset and are not attributable to these 5 changes:

- tests/adr-0014-telemetry (3 failures)
- tests/adr-0015-deps (1 pre-existing + 6 new due to `.claude/` sync already in working tree -- not caused by the 5 source changes)
- tests/adr-0016-darwin (14 pre-existing + several new due to `.claude/` sync already in working tree -- not caused by the 5 source changes)
- tests/adr-0023-reduction (1 pre-existing: ellis.md `<required-actions>` tag)
- tests/dashboard (1 pre-existing)
- tests/hooks/test_adr_0022_phase2_hooks (1 pre-existing -- passes in isolation, collection-order artifact)
- tests/hooks/test_brain_wiring (9 pre-existing)
- tests/xml-prompt-structure (11 pre-existing)

Note: The additional deps/darwin/`test_T_0005_100` failures appearing in the post-change run are attributable to the `.claude/` sync changes already staged in the working tree (git status shows these as modified from HEAD), not to the 5 source changes under review. They are present whether or not the 5 source changes are applied.

**Net new regressions introduced by this changeset: 2** (T-0023-030, T-0023-040).

---

### Doc Impact: NO

Source template changes. User-facing behavior is updated (smaller maxTurns, new fast-path modes, extended eviction list), but no documentation files need updating beyond these source templates.

---

### Roz's Assessment

The 5 changes are structurally correct and behaviorally sound. XML tags are well-formed throughout. All new sections land inside their correct parent tags. TDD constraints (R15 -- Colby never modifies Roz's assertions; Roz test-first principle) are fully intact. The core constant count and list are consistent. Claude/Cursor frontmatter files are in sync. The preamble exemption clause correctly exempts only Ellis and does not require updating for the new fast-path modes (those are `<workflow>`-level protocols, not preamble-level exemptions). The distillator observation masking constraint is well-placed and precise.

However, two ADR-0023 line-count constraints are violated. These constraints exist because ADR-0023 established explicit persona size budgets -- colby.md at 95 lines and roz.md at 100 lines. Both files were exactly at their limits before this changeset. Adding workflow sections without trimming equivalent content elsewhere is a constraint violation, not a judgment call. Colby needs to trim 2 lines from colby.md and 1 line from roz.md. Options include condensing the new section prose (both sections have some redundancy with the existing `<workflow>` modes) or trimming from existing content that is less load-bearing than the new fast-path behavior.

Pipeline is halted pending the line-count fix.
