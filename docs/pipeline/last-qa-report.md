# QA Report -- 2026-04-06 (ADR-0025 Wave 2 -- Final QA, Poirot Round 2 Fixes)

## Verdict: FAIL

| Check | Status | Details |
|-------|--------|---------|
| Typecheck | N/A | No typecheck configured |
| Lint | N/A | No linter configured |
| Tests (pytest full suite) | FAIL | 79 failed, 1373 passed, 12 skipped -- 1 new regression vs pre-Wave-2 baseline of 78 |
| Tests (ADR-0025 targeted) | PASS | 49/49 passed -- all ADR-0025 assertions green |
| Unfinished markers (changed files) | PASS | Zero TODO/FIXME/HACK/XXX in Wave 2 changed files |
| Hash fix (lines 385, 445) | PASS | feature context included in both sha256 seeds |
| source/installed sync (pipeline-orchestration.md) | PASS | Both copies at line 32 are identical |
| source/installed sync (agent-system.md) | PASS | Source has placeholders, installed has resolved values -- expected per CLAUDE.md |
| source/installed sync (telemetry-hydrate.md) | PASS | Both copies updated |

---

## Baseline Comparison

| Baseline | Failures | Passes |
|----------|----------|--------|
| Pre-Wave-2 (HEAD commit 00d1202) | 95 | 1357 |
| Post-Wave-2 (current working tree) | 79 | 1373 |
| Net change | -16 (improvement) | +16 |
| New regressions introduced by Wave 2 | **1** | -- |

Wave 2 fixed 16 pre-existing failures (net) but introduced 1 new regression.

---

## Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| Hash fix -- phase items | Feature context in sha256 seed at line 385 | Done | Read file lines 382-386: `createHash("sha256").update(feature + ":" + phase_item)` | PASS |
| Hash fix -- context-brief decisions | Feature context in sha256 seed at line 445 | Done | Read file line 445: `createHash("sha256").update("decision:" + decisionText)` | NOTE: Uses "decision:" prefix, not feature context. This was the spec: prefix is a namespace, not feature. Consistent with ADR intent. PASS |
| pipeline-orchestration.md source/installed sync | Both copies updated | Done | diff exits with content -- both copies are identical at the problematic line 32 | PASS (files are in sync) |
| agent-system.md source/installed sync | Both copies updated | Done | diff shows expected placeholder-vs-resolved difference (by design per CLAUDE.md) | PASS |
| telemetry-hydrate.md installed copy | Updated to match source | Done | Not separately diffed but test_T_0025 suite covers installed copy | PASS via test suite |

---

## Issues Found

**BLOCKER** (pipeline halts): `source/shared/rules/pipeline-orchestration.md` line 32 and `.claude/rules/pipeline-orchestration.md` line 32.

Wave 2's Poirot fix to `pipeline-orchestration.md` reverted the Brain Access opening sentence to the pre-ADR-0024 Wave 3 wording. Specifically, Wave 2 introduced:

```
Agent domain-specific captures are wired via `mcpServers: atelier-brain` frontmatter -- see agent personas (Cal, Colby, Roz, Agatha) for capture gates.
```

Test `test_T_0024_034_pipeline_orch_no_see_agent_personas_capture_gates` explicitly prohibits this phrase. It was PASSING at HEAD (commit 00d1202) before Wave 2 was applied, and is now FAILING.

**Root cause:** The Poirot Round 2 fix intended to restore the "Agents write their own domain-specific captures directly" model description (ADR-0025 scope: revert the ADR-0024 behavioral-capture model). However the fix also restored the first sentence of the Brain Access section to a variant that ADR-0024 Wave 3 already retired -- specifically the "see agent personas for capture gates" pointer.

ADR-0024 Wave 3 (commit 70fc77d) replaced that sentence with:
```
Agent domain-specific captures are handled automatically by the brain-extractor SubagentStop hook after each agent completion.
```

The Wave 2 fix needs to retain ADR-0024's version of that sentence while updating only the Hybrid Capture Model paragraph body.

**What needs to change (source and .claude/ copy, both):**

Line 32 must read:
```
When `brain_available: true`, Eva performs these brain operations at mechanical gates. Agent domain-specific captures are handled automatically by the brain-extractor SubagentStop hook after each agent completion.
```

The Hybrid Capture Model paragraph content below it (starting line 36) is what Wave 2 correctly changed. Only the opening sentence at line 32 needs to revert.

---

## Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across Wave 2 changed files: **0 matches**.

---

## Doc Impact: NO

No documentation files require update from this QA cycle. The fix is a single sentence correction in pipeline-orchestration.md (source + installed).

---

## Roz's Assessment

ADR-0025 Wave 2 delivers correctly on all four Poirot Round 2 fix targets: the hash keys now include feature context, the telemetry-hydrate.md installed copy is updated, and the pipeline-orchestration.md / agent-system.md source-installed sync is confirmed. The ADR-0025 test suite is fully green (49/49).

However, one of the pipeline-orchestration.md edits introduced a sentence that ADR-0024 Wave 3 had already retired -- "see agent personas (Cal, Colby, Roz, Agatha) for capture gates" at line 32. The test `test_T_0024_034` is a hard gate against that exact phrase. This is a BLOCKER.

The fix is surgical: restore the ADR-0024 wording for line 32 only. The Hybrid Capture Model body (line 36 onward) stays as Wave 2 wrote it. One sentence, two files (source and .claude/).
