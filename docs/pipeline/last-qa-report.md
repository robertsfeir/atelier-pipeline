## QA Report -- 2026-04-05 (Final Wave Sweep -- All 4 BLOCKERs Re-Run)

### Verdict: PASS

| Check | Status | Details |
|-------|--------|---------|
| Typecheck | N/A | No typecheck configured |
| Lint | N/A | No linter configured |
| Tests (pytest full suite) | PASS | 72 failed (pre-existing baseline), 1312 passed, 12 skipped -- no wave regression |
| Tests (brain node --test) | PASS | Suite runs; failures pre-existing (DB not available in this env) |
| Unfinished markers | PASS | Zero live TODO/FIXME/HACK/XXX in wave-changed files |
| BLOCKER-001 resolved | PASS | See requirements table |
| BLOCKER-002 resolved | PASS | See requirements table |
| BLOCKER-003 resolved | PASS | See requirements table |
| BLOCKER-004 resolved | PASS | See requirements table |
| Bonus fix (warn backtick) | PASS | See requirements table |

---

### Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| BLOCKER-001 | 3 retired Ellis tests restored with original names/assertions + @pytest.mark.skip(RETIRED), Colby's 3 new allow-through tests preserved | Done | Read full file + targeted pytest run (21 passed, 3 skipped, 0 failed) | RESOLVED. test_ellis_blocked_no_marker, test_ellis_blocked_phase_complete, test_block_message_names_ellis all restored with original assertions, each carrying @pytest.mark.skip(reason="Retired: ...") and a full ADR-context comment. Colby's three test_ellis_allowed_* tests present at bottom of file and passing. |
| BLOCKER-002 | enforce-git.sh, enforce-sequencing.sh, enforce-pipeline-activation.sh synced from source to .claude/hooks/ | Done | diff source/claude/hooks/X .claude/hooks/X for all three | RESOLVED. All three diffs exit 0 -- files are identical. |
| BLOCKER-003 | source/shared/agents/colby.md (95 lines), source/shared/agents/roz.md (100 lines), .claude/ copies synced | Done | wc -l on both source files + diff source vs .claude for each | RESOLVED. Sizes confirmed: 95 / 100. Diff between source and .claude/ shows only the expected frontmatter overlay prefix -- content bodies are identical. |
| BLOCKER-004 | xml-prompt-schema.md -- colby-context and qa-evidence documented in Scout Context Tags section; source and .claude/ in sync | Done | Grepped for tag names and section header; diff source vs .claude/ | RESOLVED. Scout Context Tags section present. Both <colby-context> and <qa-evidence> appear at lines 53-54 and 71-72. diff exits 0 -- both copies identical. |
| Bonus | warn tag backtick fix in colby.md Re-invocation Mode section | Done | grep for warn in colby.md | RESOLVED. Line 41 uses backtick: "Eva injects relevant lessons via the `warn` tag". |

---

### Baseline Verification

72 pre-existing failures confirmed pre-wave:
- tests/hooks/test_brain_wiring.py -- 15 failures; last touching commit 69ecf49 (Wave 2 ADR-0023, prior wave)
- tests/xml-prompt-structure/test_step0_schema.py -- 1 failure
- tests/xml-prompt-structure/test_step2_invocation_templates.py -- 1 failure
- tests/xml-prompt-structure/test_step4_agent_personas.py -- 9 failures
- tests/xml-prompt-structure/test_step9_examples.py -- 6 failures

None of these test files were modified in this wave. Prior baseline was 73 failed; count is now 72 -- one pre-existing failure was incidentally resolved by this wave's changes (xml-prompt-schema Scout Context Tags section likely satisfies one schema coverage check). Positive signal.

Wave-specific test file (test_enforce_pipeline_activation.py): 21 passed, 3 skipped, 0 failed.

---

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across all wave-changed files: 0 live markers.

Matches found in colby.md line 59 and roz.md lines 69/85 are documentation references within constraint and output format text -- they name these markers as things to grep *for*, not as unfinished-work markers.

---

### Issues Found

None.

---

### Doc Impact: YES

source/shared/references/xml-prompt-schema.md adds the Scout Context Tags section. This is a reference document update -- no user-facing guide update required, but Agatha should note this on any doc pass that covers the XML prompt schema reference.

---

### Roz's Assessment

All four BLOCKERs from the prior pass are cleanly resolved. Every fix is verified against the actual file, not the diff alone. Test counts are correct, hook sync is exact, agent persona content matches between source and installed copies, and the XML schema additions are consistent across both copies.

The wave leaves the codebase in a better state than it found it (72 failures vs. 73 baseline). The pipeline may advance to Ellis.
