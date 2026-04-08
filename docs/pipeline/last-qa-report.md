# QA Report -- 2026-04-08

## Micro: marketplace.json version bump 3.27.0 -> 3.27.1

### Verdict: PASS

| Check | Status | Details |
|-------|--------|---------|
| Version field reads 3.27.1 | PASS | `plugins[0].version` confirmed as "3.27.1" at line 11 |
| No other fields changed | PASS | Diff shows exactly one line changed: version string only |
| Diff is a single-line change | PASS | `-"version": "3.27.0"` / `+"version": "3.27.1"` -- all other fields identical |
| TODO/FIXME/HACK/XXX grep | PASS | Zero markers in `.claude-plugin/marketplace.json` |
| pytest full suite | PASS (baseline) | 1484 passed, 5 failed -- all 5 failures pre-existing, unrelated to this change |
| brain node tests | PASS | 121 pass, 0 fail |

---

### Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| 1 | `plugins[0].version` field set to "3.27.1" | Done | Confirmed at line 11 of `.claude-plugin/marketplace.json` | OK |
| 2 | No other fields in the file changed | Done | Git diff shows single-line change: version string only | OK |
| 3 | File is valid JSON | Done | File parses; all surrounding structure intact | OK |

---

### Change Verification

Git diff against HEAD confirms the change is exactly what was specified:

```
-      "version": "3.27.0",
+      "version": "3.27.1",
```

All other fields in `.claude-plugin/marketplace.json` are identical to HEAD:
- `name`: "atelier-pipeline" -- unchanged
- `description`: unchanged
- `owner.name` and `owner.email`: unchanged
- `plugins[0].name`: "atelier-pipeline" -- unchanged
- `plugins[0].source`: "./" -- unchanged
- `plugins[0].description`: unchanged

---

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` in `.claude-plugin/marketplace.json`: 0 matches.

---

### Issues Found

None. No BLOCKERs. No FIX-REQUIRED items.

---

### Pre-existing Test Failures (not introduced by this change)

Confirmed via stash round-trip: the same 5 pytest failures exist on HEAD before this Micro change is applied. Identical failure set with and without the marketplace.json change.

| Test | Failure | Cause |
|------|---------|-------|
| `test_T_0023_061_Darwin_persona_100_lines` | 133 lines > 100 limit | darwin.md persona exceeds ADR-0023 budget -- pre-existing |
| `test_T_0023_130_pipeline_orchestration_md_650_lines` | 759 lines > 650 limit | pipeline-orchestration.md exceeds budget -- pre-existing |
| `test_T_0023_150_Total_agent_persona_lines_across_12_agents_935` | 1026 > 1010 limit | Total agent lines exceeds tolerance -- pre-existing |
| `test_T_0022_021_claude_hooks` | 20 .sh files != expected 19 | Hook count mismatch from prior wave -- pre-existing |
| `test_T_0024_048_full_pytest_suite_passes` | Cascade from above 4 failures | Meta-test that asserts suite passes -- pre-existing |

None of these tests reference `.claude-plugin/marketplace.json`. The Micro change introduces zero new failures.

---

### Doc Impact: NO

`.claude-plugin/marketplace.json` is a distribution manifest. The version change aligns it with the installed version. No documentation requires updating.

---

### Roz's Assessment

The Micro change is clean and surgically correct. Exactly one field was modified: `plugins[0].version` from "3.27.0" to "3.27.1". The JSON structure is intact, all surrounding fields are unchanged, and the version now matches what `installed_plugins.json` records (3.27.1), which resolves the Doctor mismatch the pipeline state file describes.

Test suite baseline is unchanged: 5 pre-existing failures, all in ADR-0023 line-count budgets and hook count assertions that long predate this change. Brain tests pass cleanly (121/121).

Micro safety valve satisfied: full test suite ran, no new failures introduced.

**Verdict: PASS. Route to Ellis.**
