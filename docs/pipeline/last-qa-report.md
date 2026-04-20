# QA Report -- 2026-04-20 (Scoped Re-Run: ADR-0042 Poirot Fixes)

## Verdict: PASS

Scoped re-run verifying 5 Poirot findings were correctly resolved by Colby's fix cycle. All 5 findings resolved. Mirror parity confirmed. ADR-0042 test suite green (64/64).

## Scope

This was a scoped re-run per agent-preamble exemption — DoR/DoD protocol skipped (steps 1, 2, 3, 5 of agent-preamble), scoped to fix verification only.

Files verified:
- `source/shared/references/invocation-templates.md`
- `source/shared/rules/pipeline-models.md`
- `.claude/rules/pipeline-models.md` (installed Claude mirror)
- `.cursor-plugin/rules/pipeline-models.mdc` (installed Cursor mirror)

## Check Summary

| Check | Status | Details |
|-------|--------|---------|
| ADR-0042 scoped tests | PASS | 64/64 pass (pytest tests/adr-0042/ -q) |
| Source vs .claude mirror parity | PASS | byte-identical body (diff clean) |
| Source vs .cursor-plugin mirror parity | PASS | byte-identical body (diff clean) |
| TODO/FIXME/HACK/XXX in fix targets | PASS | No matches in pipeline-models files; invocation-templates hits are literal constraint phrases ("Zero TODO/FIXME/HACK", "Grep TODO/FIXME/HACK"), not unfinished markers |

## Finding-by-Finding Verification

| # | Finding | Target location | Expected after fix | Verified | Status |
|---|---------|-----------------|--------------------|----------|--------|
| 1 | Template 2c referenced non-existent `<primary_agent>-synthesis` persona | `source/shared/references/invocation-templates.md:121` | `Agent(subagent_type: "general-purpose", model: "sonnet", effort: "low")` with inline synthesis instructions and "switch to `subagent_type: "synthesis"`" when registered | Line 121-122: exact string present. Inline output-shape prompt preserved (lines 126-145). | PASS |
| 2 | "xhigh is max" ambiguity in Tier 4 row | All 3 pipeline-models files, task-class-tiers table | "`xhigh` is the ceiling value" | Present at source:28, .claude:33, .cursor-plugin:38. All three match. | PASS |
| 3 | Column header "Effort +1 when" (misleading — implies promotion-only) | All 3 pipeline-models files, task-class-tiers table | "Effort adjustment signal" | Present at source:23, .claude:28, .cursor-plugin:33. All three match. | PASS |
| 4 | Roz and Sentinel rows missing demotion rationale | All 3 pipeline-models files, agent-assignments table | Roz: explicit "Effort demoted high→medium baseline" with rationale. Sentinel: "effort demoted medium→low" with mechanical-task rationale. | Roz row (source:82, .claude:87, .cursor-plugin:92): rationale present. Sentinel row (source:89, .claude:94, .cursor-plugin:99): rationale present. All three files match. | PASS |
| 5 | Enforcement Rule 3 referenced removed Large effort-promotion signal | All 3 pipeline-models files, enforcement gate | Rule scoped to tier-selection only; explicit note "Effort is NOT affected by ambiguous sizing -- the Large effort-promotion signal was removed by ADR-0042" | Present at source:130-131, .claude:135-136, .cursor-plugin:140-141. All three files match. | PASS |

## Mirror Parity Verification

```
diff source/shared/rules/pipeline-models.md <(tail -n +6 .claude/rules/pipeline-models.md)
# exit 0 — byte-identical body after stripping 5-line Claude frontmatter

diff source/shared/rules/pipeline-models.md <(tail -n +11 .cursor-plugin/rules/pipeline-models.mdc)
# exit 0 — byte-identical body after stripping 10-line Cursor double-frontmatter
```

Fix 6 (placeholder substitution in mirrors) was correctly reverted — mirror-parity tests require byte-identical content, and `{pipeline_state_dir}` is intentional (resolved at runtime). Confirmed this design holds: installed mirrors contain the literal `{pipeline_state_dir}` token, not a substituted path.

## Unfinished Markers

`TODO/FIXME/HACK/XXX` grep on fix targets:
- `pipeline-models.md` (all 3 copies): zero matches
- `invocation-templates.md`: 2 matches at lines 201 and 261 — both are literal constraint phrases Colby is told to grep for ("Zero TODO/FIXME/HACK", "Grep TODO/FIXME/HACK -- non-test = BLOCKER"). Not unfinished work markers. No action required.

## Test Results

Command: `pytest tests/adr-0042/ -q`

Result: **64 passed in 0.13s** (1 warning — urllib3/chardet version mismatch, unrelated to ADR-0042).

Full suite status (per Colby's report, not re-run in scoped mode): 1843/1844 passing. The 1 pre-existing brain version failure is unrelated to ADR-0042 scope.

## Issues Found

None. No BLOCKER. No FIX-REQUIRED.

## Regression Check

Scoped check for new regressions in the 4 directly affected files:
- No new TODO/FIXME/HACK markers introduced
- Mirror parity preserved (byte-identical bodies)
- Template 2c's inline synthesis output-shape prompt remains intact — all per-primary-agent shapes preserved (Cal research-brief, Colby colby-context, Roz qa-evidence)
- Enforcement Rule 3 rewrite preserves the "higher tier default under ambiguity" behavior; only the effort-promotion reference was scoped out
- All `<model-table>` IDs and closing tags intact
- No new references to removed `effort_large_signal` or similar deprecated concepts

## Doc Impact: NO

Scoped fix to rule/reference files; no user-facing documentation surface affected. ADR-0042 itself is immutable and was not modified (correctly — ADRs are append-only, the "xhigh is max" and "Effort +1 when" strings still exist in ADR-0041 and ADR-0042 body text as historical record, which is expected behavior).

## Roz's Assessment

Clean fix cycle. Colby applied all 5 fixes precisely — each finding was addressed at the exact locus Poirot flagged, in all three mirror copies, with no drift between source and installed files. Mirror-parity tests passed without requiring placeholder substitution, which is the correct design call.

The decision to revert Fix 6 (placeholder substitution) deserves explicit note: the mirror-parity tests are a load-bearing invariant — byte-identical bodies between `source/shared/` and `.claude/` / `.cursor-plugin/`. Substituting `{pipeline_state_dir}` at install time would have broken that invariant. Colby reverted correctly.

One stylistic observation that is NOT a blocker: the Roz and Sentinel rationale rows both use a Unicode arrow (→). Consistent, and matches the pre-existing style elsewhere in the table. No change needed.

Ship it.

---

**Verdict: PASS** — all 5 Poirot findings resolved, no regressions detected, tests green. Ready for Ellis commit.
