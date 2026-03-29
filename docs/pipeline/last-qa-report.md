# QA Report -- 2026-03-29 (Final Sweep: ADR-0014 + ADR-0015)

*Reviewed by Roz*

### Verdict: FAIL

5 test failures in ADR-0014 tests, 1 in ADR-0015 tests, 7 pre-existing in hooks tests. Brain tests: 92/92 pass.

## Tier 1 -- Mechanical Checks

| Check | Status | Details |
|-------|--------|---------|
| Type check | SKIP | No typecheck configured |
| Lint | SKIP | No linter configured |
| ADR-0014 tests | FAIL | 57/62 pass, 5 fail (3 test bugs, 2 missing doc index entries) |
| ADR-0015 tests | FAIL | 63/64 pass, 1 fail (test regex bug) |
| Hooks tests | FAIL | 36/43 pass, 7 fail (ALL pre-existing, not introduced by this feature) |
| Brain tests | PASS | 92/92 pass |
| Coverage | N/A | No coverage tooling configured |
| Complexity | PASS | No excessive nesting or length in changed files |
| Unfinished markers | PASS | Zero TODO/FIXME/HACK/XXX in changed non-test files |

### Test Failure Analysis

#### ADR-0014 Failures

| Test | Root Cause | Category |
|------|-----------|----------|
| T-0014-043 (Mask section lists Tier 1 telemetry) | **Test bug.** awk `/^### Mask/,/^###/` self-terminates on the header line because `### Mask (Replace with Placeholder)` matches both start and end patterns. Code at line 493 of pipeline-operations.md correctly contains "Tier 1 `agent_capture` responses" in the Mask section. | Test regex |
| T-0014-046 (roz_qa in PIPELINE_STATUS) | **Test bug.** Test looks for `roz_qa` in pipeline-operations.md, but `roz_qa` lives in pipeline-orchestration.md (CI Watch protocol section). The PIPELINE_STATUS fields in pipeline-operations.md are CI Watch and Telemetry fields only. | Wrong file |
| T-0014-051 (Never Mask lists telemetry accumulators) | **Test bug.** Same awk extraction bug as T-0014-043. Code at line 480 of pipeline-operations.md correctly contains "Telemetry accumulators in PIPELINE_STATUS". | Test regex |
| T-0014-048 (ADR-0014 in README.md) | **Missing implementation.** `docs/architecture/README.md` has no ADR-0014 entry. Eva owns README.md updates per pipeline-orchestration.md. | Missing |
| T-0014-049 (ADR-0014 index title) | **Missing implementation.** Same as T-0014-048. | Missing |

#### ADR-0015 Failures

| Test | Root Cause | Category |
|------|-----------|----------|
| T-0015-039 (Sentinel row unchanged) | **Test bug.** Uses `grep -qiE "Sentinel.*security.*audit\|Sentinel.*Semgrep"`. In ERE mode (`-E`), `\|` is a literal pipe character, not alternation. The correct ERE alternation is bare `|`. Code is correct -- Sentinel row at line 49 of agent-system.md is unchanged. | Test regex |

#### Pre-Existing Hook Failures (7 tests, not introduced by ADR-0014/0015)

T-0003-018, T-0003-021, T-0003-028, T-0003-029 (enforce-paths.bats), T-0003-044, T-0003-045, T-0003-057 (enforce-sequencing.bats). Last modified in ADR-0013 commit `339fc8c`. These are known failures unrelated to the current feature.

## Tier 2 -- Judgment Checks

| Check | Status | Details |
|-------|--------|---------|
| DB Migrations | N/A | No DB changes |
| Security | PASS | No secrets, no auth changes, no injection surfaces |
| CI/CD Compat | N/A | No middleware/env var changes |
| Docs Impact | YES | ADR-0014 and ADR-0015 entries missing from `docs/architecture/README.md` |
| Dependencies | N/A | No new dependencies |
| UX Flow | N/A | No UI changes |
| Exploratory | PASS | Edge cases documented (brain unavailable, Micro pipelines, missing tools) |
| Semantic Correctness | PASS | Domain intent correctly encoded in all deliverables |
| Contract Coverage | PASS | All telemetry tiers have defined schemas, triggers, and consumers |
| State Machine | N/A | No state machine changes |
| Silent Failure Audit | PASS | All capture gates document log-and-continue failure handling |
| Wiring Verification | PASS | Every producer has a consumer (see below) |

### Wiring Verification Detail

| Producer | Consumer | Verified |
|----------|----------|----------|
| telemetry-metrics.md (schemas) | pipeline-orchestration.md (capture protocol), default-persona.md (boot query) | Yes |
| Tier 1 capture (per-invocation) | Tier 2 aggregation (unit_cost_usd), Tier 3 aggregation (total_cost_usd), pipeline-end summary | Yes |
| Tier 2 capture (per-unit) | Tier 3 aggregation (rework_rate, first_pass_qa_rate), pipeline-end summary | Yes |
| Tier 3 capture (per-pipeline) | Boot trend query (step 5b), degradation alerts | Yes |
| deps_agent_enabled config | /deps command gate, auto-routing gate, SKILL.md Step 6d | Yes |
| deps-scan template | /deps command, Eva auto-routing | Yes |
| deps-migration-brief template | /deps command (migration flow) | Yes |
| deps.md persona | agent-system.md subagent table, no-skill-tool gate, enforce-paths.sh catch-all | Yes |

### Dual-Tree Sync Verification

| File Pair | Status |
|-----------|--------|
| source/references/telemetry-metrics.md <-> .claude/references/telemetry-metrics.md | Identical |
| source/agents/deps.md <-> .claude/agents/deps.md | Identical |
| source/commands/deps.md <-> .claude/commands/deps.md | Identical |
| source/rules/pipeline-orchestration.md <-> .claude/rules/pipeline-orchestration.md | Both contain telemetry-capture protocol |
| source/rules/default-persona.md <-> .claude/rules/default-persona.md | Both contain step 5b (source uses placeholder, installed uses literal) |
| source/rules/agent-system.md <-> .claude/rules/agent-system.md | Both contain Deps row in subagent table |
| source/references/invocation-templates.md <-> .claude/references/invocation-templates.md | Both contain deps-scan template |
| source/pipeline/pipeline-config.json <-> .claude/pipeline-config.json | Both contain deps_agent_enabled: false |

### Requirements Verification

| # | ADR-0014 Requirement | Verified | Finding |
|---|---------------------|----------|---------|
| R1 | Tier 1 per-invocation metrics | Yes | All 14 fields present in telemetry-metrics.md |
| R2 | Tier 2 per-unit metrics | Yes | All 6 fields present |
| R3 | Tier 3 per-pipeline metrics | Yes | All 10 fields present |
| R4 | Tier 4 over-time trends | Yes | Boot step 5b queries brain for Tier 3 data |
| R5 | Eva surfaces trend at boot | Yes | Step 5b + step 6 announcement format |
| R6 | Metrics stored via agent_capture | Yes | Capture protocol uses insight/eva/telemetry |
| R7 | Degradation alerts 3+ consecutive | Yes | Documented in both default-persona.md and telemetry-metrics.md |
| R8 | Pipeline-end summary | Yes | Format documented in pipeline-orchestration.md |
| R9 | Non-blocking | Yes | Every gate has log-and-continue handling |
| R10 | Token counts unavailable | Yes | Documented in capture protocol |
| R11 | First pipeline no-data case | Yes | "No prior pipeline data" documented |
| R12 | Micro Tier 1 only | Yes | Documented in capture protocol |
| R15 | Dual-tree sync | Yes | All pairs verified |
| R20 | No external dashboard | Yes | Brain queries + Eva summary only |

| # | ADR-0015 Requirement | Verified | Finding |
|---|---------------------|----------|---------|
| R1 | Agent persona deps.md | Yes | Both trees, identical |
| R2 | deps_agent_enabled config | Yes | Default false in both configs |
| R3 | SKILL.md Step 6d | Yes | Positioned after 6c, before Brain |
| R4 | /deps slash command | Yes | Both trees, identical |
| R5-R8 | Workflow phases | Yes | Detect, Scan, Report + migration brief |
| R9 | Read-only enforcement | Yes | disallowedTools + catch-all in enforce-paths.sh |
| R10 | Auto-routing | Yes | Intent row with gate condition |
| R11 | Risk-grouped output | Yes | 4 sections in output format |
| R12 | Edge case handling | Yes | 5 edge cases in workflow |
| R14 | Invocation templates | Yes | deps-scan + deps-migration-brief |
| R15 | agent-system.md updated | Yes | Subagent table + no-skill-tool gate |

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` in changed non-test files: 0 matches. All occurrences are in documentation describing the marker-checking process itself.

## Issues Found

**BLOCKER** (pipeline halts -- fix before advancing):

1. **`docs/architecture/README.md` missing ADR-0014 and ADR-0015 entries.** Per pipeline-orchestration.md, Eva owns the ADR index and must update it after any commit that adds an ADR file. Both ADR-0014 and ADR-0015 .md files exist in `docs/architecture/` but have no corresponding index entries. Tests T-0014-048, T-0014-049 fail.

**FIX-REQUIRED** (queued -- all resolved before Ellis commits):

1. **Test T-0014-043 awk extraction bug.** The awk pattern `/^### Mask/,/^###/` self-terminates because the start line also matches the end pattern. Fix: use `/^### Mask/{ found=1; next } found && /^###/{ exit } found` or equivalent. File: `tests/adr-0014-telemetry/telemetry-structural.test.bats`, line 604.

2. **Test T-0014-046 checks wrong file.** Looks for `roz_qa` in pipeline-operations.md; the field is in pipeline-orchestration.md. Fix: change `$INSTALLED_REFS/pipeline-operations.md` to `$INSTALLED_RULES/pipeline-orchestration.md`. File: `tests/adr-0014-telemetry/telemetry-structural.test.bats`, line 635.

3. **Test T-0014-051 same awk extraction bug as T-0014-043.** File: `tests/adr-0014-telemetry/telemetry-structural.test.bats`, line 669.

4. **Test T-0015-039 ERE regex bug.** Uses `\|` for alternation in ERE mode (`-E`), which matches a literal pipe. Fix: change `\|` to `|`. File: `tests/adr-0015-deps/deps-structural.test.bats`, line 518.

### Doc Impact: YES

- `docs/architecture/README.md` must be updated with ADR-0014 and ADR-0015 entries.

### Roz's Assessment

The implementation deliverables are solid. All ADR-0014 telemetry protocol content is correctly placed in the right files with proper dual-tree sync. All ADR-0015 deps agent artifacts are complete and correctly wired. The wiring is clean -- every producer has a consumer, every config flag has a gate, every template has a caller.

The 4 test bugs (3 awk extraction, 1 ERE regex) are authoring defects in my own test files from the pre-build round. They need fixing. The 1 blocker (missing ADR index entries) is a gap that should have been caught during the build phase -- Eva owns README.md updates.

The 7 pre-existing hook test failures are tech debt from prior work and are outside the scope of this feature.

### Recurring QA Patterns

- **awk section extraction on macOS:** The `/^### X/,/^###/` range pattern fails when the start line itself matches the end pattern. This is the second time I have seen this (noted during test authoring hardening). Future tests should use the `found` flag approach instead of range patterns for markdown section extraction.

- **ERE vs BRE alternation:** Using `\|` with `grep -E` is a recurring mistake. ERE uses `|` for alternation; BRE uses `\|`. Future tests should be validated with a quick manual check before commit.
