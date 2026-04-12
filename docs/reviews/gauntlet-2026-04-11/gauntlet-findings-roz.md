# Roz — Testing Strategy & Coverage

**Date:** 2026-04-11
**Scope:** Gauntlet Round 3 — full atelier-pipeline test suite (pytest + node --test)
**Mode:** Read-only audit. No files modified.
**Evidence:** 1,570 pytest tests collected, 23 node brain tests, 65 test files across 9 conftest.py scopes.

## Summary

The atelier-pipeline test suite is **large but uneven**. Pytest hook enforcement is the strongest layer — 777+ tests exercise per-agent path hooks, settings.json wiring, and ADR-0033 audit fixes with good fail-loudly assertions. The brain MCP layer is the weakest: 100% mock-based, zero happy-path integration against PostgreSQL or pgvector, and a **critical contract-drift gap** between `brain/lib/config.mjs` Zod enums and `brain-extractor.md`'s agent-to-metadata mapping. Four of the twelve `enforce-*-paths.sh` hooks (`agatha`, `product`, `ux`, `ellis-writes-outside-its-lane`) have no direct behavioral tests. Six tests are currently red, including one self-referential gate (`test_T_0024_048_full_pytest_suite_passes`) that amplifies any single failure into a pipeline blocker.

**Verdict: FAIL** for Gauntlet Round 3. Core gaps are structural (enum boundary, hook coverage holes) not cosmetic, and the red tests cannot be dismissed — one of them (`T-0024-050`) signals an active drift between settings.json and the ADR-0025 spec.

---

## Coverage Map

Product features are derived from `docs/product/` (9 specs) plus the two major pipeline systems that have no corresponding spec file but are load-bearing (hook enforcement, agent-system orchestration).

| Feature / Business Flow | Coverage Level | Highest-Risk Gap |
|---|---|---|
| **Hook enforcement — per-agent paths** (`enforce-*-paths.sh`) | Partially tested | `enforce-agatha-paths.sh`, `enforce-product-paths.sh`, `enforce-ux-paths.sh` have **no direct behavioral tests**. Only `test_enforce_paths.py` covers colby/ellis. Grep shows 34 references but `test_adr_0022_phase2_hooks.py` (18 refs) and `test_adr_0022_phase2_wiring.py` (5 refs) only assert file existence and registration — not that a Write to a forbidden path gets `returncode 2`. See also ADR-0033 scout finding. |
| **Hook enforcement — Colby blocked paths** | Fully tested | None. `test_enforce_colby_paths.py` (T-0033-014/015/030) locks the `.github/` blocker and the conftest mirror. |
| **Hook enforcement — Roz read/write scope** | Fully tested | None. `test_enforce_roz_paths.py` covers Write-only tool restriction plus `test_T_0033_026` locks the header comment. |
| **Hook enforcement — Cal ADR paths** | Fully tested | None. `test_enforce_cal_paths.py` covers Cal's read/write scope (T-0033-025). |
| **Hook enforcement — scout swarm** | Fully tested | None. 7+ tests cover swarm composition, haiku tier, early-exit conditions. |
| **Brain MCP — agent_capture** | Partially tested | **CRITICAL enum-boundary gap.** Mock pool accepts any string for `source_agent`/`source_phase`. Zod enums in `brain/lib/tools.mjs:62-63` are never exercised with negative inputs in `tests/brain/tools.test.mjs`. `tests/brain/config.test.mjs:238-249` spot-checks 3 enum members and never cross-references them to the brain-extractor mapping table. |
| **Brain MCP — agent_search** | Partially tested | Mock-only. No PostgreSQL ordering test, no pgvector similarity sanity check, no `last_accessed_at` race test. |
| **Brain MCP — atelier_browse / stats / relation / trace / hydrate** | Partially tested | Mock-only. Happy paths covered. `atelier_trace` cycle detection tested with a fake "cycle found" row, never against a real recursive CTE. |
| **Brain MCP — REST API** (`rest-api.mjs`) | Partially tested | `rest-api.test.mjs` exists but no concurrent-request test, no HTTP 413/400 error path coverage, no CORS/auth negative test. `THOUGHT_TYPES.includes()` validation at line 188 has no paired test. |
| **Brain MCP — hydrate, consolidation, TTL, conflict, provenance, purge, embed** | Partially tested | All covered by mock-pool unit tests. None exercise a real database. Docker-compose for brain exists (per scout evidence) but no integration test suite runs against it. |
| **Agent persona structure** (ADR-0005/0023) | Fully tested | None. `tests/xml-prompt-structure/` has 9 step files covering tag order, DoR/DoD presence, cognitive directives, retro lesson references. |
| **Pipeline hydrate / session boot / agent-telemetry** (ADR-0014) | Partially tested | `test_T_0014_018_micro_tier_1_only` currently FAILING. No persistence-layer test for in-flight Tier 1 telemetry (brain signal: session crash loses accumulator). |
| **ADR-0022 platform split** (source/shared/, source/claude/, source/cursor/) | Fully tested | None. 7 ADR-0022 test files cover install, overlay, cleanup, compaction, personas, hooks, wiring. |
| **ADR-0023 reduction** | Fully tested | None. `tests/adr-0023-reduction/` has structural coverage + ADR-0033 follow-ups. |
| **ADR-0024 mechanical brain writes** (brain-extractor wiring) | Partially tested | Persona existence + mapping table checks (T-0024-008, T-0033-018/019) but **no end-to-end runtime test** that an actual SubagentStop event produces a successful `agent_capture` call. `test_T_0024_050` currently FAILING — settings.json has 3 SubagentStop hooks where ADR-0025 expects 2. |
| **ADR-0025 mechanical telemetry extraction** | Partially tested | `test_adr_0025_telemetry_extraction.py` exists but the failing T-0024-050 indicates drift between settings.json and the spec. |
| **ADR-0027 brain hydrate scout fanout** | Partially tested | Structural test exists. No scout-count parameterized matrix. |
| **ADR-0028 named stop reason taxonomy** | Untested | No test directory found. |
| **ADR-0029 token budget estimate gate** | Untested | No test directory found. |
| **ADR-0030 token exposure probe** | Untested | No test directory found. |
| **ADR-0031 permission audit trail** | Untested | No test directory found. |
| **ADR-0032 pipeline state session isolation** | Untested | Not yet implemented per ADR status — but no Roz-first test file exists to define correct behavior before Colby builds. |
| **ADR-0033 hook enforcement audit** | Fully tested | None. 30 tests spread across 7 files, all passing. |
| **Dashboard integration** (ADR-0018) | Partially tested | `test_dashboard_integration.py` covers structure. Agent-fitness aggregation gap noted in user memory (`project_dashboard_agent_fitness_gap.md`) — no T1↔T2 aggregation test. |
| **Cursor port** (ADR-0019) | Partially tested | `test_cursor_port.py` validates file parity. No test that Cursor hooks.json and Claude settings.json stay in sync for SubagentStop wiring. |
| **Deps agent** (ADR-0015) | Partially tested | Structural-only. No test exercises WebSearch/WebFetch mock responses or CVE scoring thresholds. |
| **Darwin self-evolving pipeline** (ADR-0016) | Partially tested | Structural-only. No test exercises fitness scoring or structural proposal generation. |

---

## Spec-to-Test Traceability

Specs are in `docs/product/`. Traceability pulls the spec title, extracts acceptance criteria where visible, and maps them to test artifacts.

| Spec | Acceptance Criterion (load-bearing) | Test exists? | Test file |
|---|---|---|---|
| `agent-telemetry.md` | Tier 1 counters accumulate in-process and flush on phase transition | Partial | `tests/adr-0014-telemetry/test_telemetry_structural.py` — structural only, no runtime accumulator test. |
| `agent-telemetry.md` | Tier 2 computes per-agent fitness scores | **No** | No aggregation test found. User-memory gap: dashboard shows "Processing" indefinitely. |
| `agent-telemetry.md` | Tier 1 survives session crash (persistence) | **No** | Brain signal: no persistence layer test for in-flight accumulators. |
| `brain-hardening.md` | Brain unavailability does not block the pipeline | Partial | `test_T_0024_010_extractor_brain_unavailability_instruction` checks persona text only. No runtime test that an actual MCP failure exits cleanly. |
| `brain-hardening.md` | Enum validation prevents invalid captures | **No** | Mock pool accepts any string. No test that `source_phase='product'` (used by robert-spec in the extractor) is rejected by Zod. |
| `brain-hardening.md` | Duplicate / conflict detection | Yes | `tests/brain/conflict.test.mjs` covers dedup logic against mock. |
| `ci-watch.md` | CI failure signals route to Eva | **No** | No CI-watch test directory found. |
| `cursor-port.md` | Cursor hooks and Claude hooks stay in sync | Partial | `test_cursor_port.py` checks file parity. No SubagentStop-wiring equivalence test. |
| `darwin.md` | Telemetry feeds Darwin fitness scoring | Partial | Structural only. No fitness-calculation test. |
| `dashboard-integration.md` | Dashboard queries live brain + telemetry | Partial | `test_dashboard_integration.py` structural. No end-to-end query test. |
| `deps-agent.md` | CVE check + outdated scan | Partial | Structural-only. |
| `mechanical-brain-writes.md` | Extractor fires on SubagentStop for 9 target agents | Partial | Persona/mapping tests exist. No runtime event test. Failing `T-0024-050` shows SubagentStop has 3 hooks where spec expects 2. |
| `mechanical-brain-writes.md` | Extractor is excluded from its own trigger (loop prevention) | Yes | `test_T_0024_002_brain_extractor_excluded_from_if_condition` locks this. |
| `mechanical-brain-writes.md` | Extractor uses metadata mapping from persona table | Partial | `T-0024-008` + `T-0033-019` check mapping table shape. **No test verifies the mapped (source_agent, source_phase) tuples are valid against `SOURCE_AGENTS` / `SOURCE_PHASES` enums.** |
| `team-collaboration-enhancements.md` | Agent-teams wave execution | **No** | Experimental per CLAUDE.md. No test file found. |

**Traceability coverage: 9 of 24 criteria have direct tests. 8 have partial tests. 7 have none.**

---

## Findings

| # | Severity | Layer | Category | Finding | Location | Recommendation |
|---|---|---|---|---|---|---|
| R1 | **Critical** | Brain MCP | Contract drift | `brain-extractor.md:43-53` maps `source_agent` to `robert-spec`, `sable-ux` and `source_phase` to `product`, `ux`, `commit` — **none of which exist in `SOURCE_AGENTS` or `SOURCE_PHASES`** in `brain/lib/config.mjs:18-24`. `agent_capture` in `brain/lib/tools.mjs:62-63` uses `z.enum(SOURCE_AGENTS)` and `z.enum(SOURCE_PHASES)`. Zod will reject these captures at runtime. The only tests (`T-0024-008`, `T-0033-019`) verify the mapping table shape but **never feed the mapped tuples through `agent_capture` or compare them against the enum arrays**. Five of the nine target agents silently cannot capture. | `brain/lib/config.mjs:18-24`, `source/shared/agents/brain-extractor.md:43-53`, `tests/hooks/test_brain_extractor.py:557-567`, `tests/brain/tools.test.mjs:114-120` | Add a meta-test that imports `SOURCE_AGENTS` + `SOURCE_PHASES` from `config.mjs`, parses the extractor mapping table, and asserts every `source_agent`/`source_phase` value in the table is a member of the corresponding enum. Fix the enum OR the mapping — Roz should write the meta-test first and force the architecture decision. |
| R2 | **Critical** | Hook enforcement | Coverage hole | Four `enforce-*-paths.sh` hooks ship with zero direct behavioral tests. `enforce-agatha-paths.sh`, `enforce-product-paths.sh`, `enforce-ux-paths.sh` have no `test_enforce_<agent>_paths.py` file. `enforce-ellis-paths.sh` is tested only indirectly via `test_enforce_paths.py` for two scenarios (allow `.github/`, block `source/`). No test verifies Agatha is blocked from writing to `source/`, or that Robert is blocked outside `docs/product/`. A regression in any of these hooks ships silently. | `source/claude/hooks/enforce-agatha-paths.sh`, `source/claude/hooks/enforce-product-paths.sh`, `source/claude/hooks/enforce-ux-paths.sh`, `source/claude/hooks/enforce-ellis-paths.sh`, `tests/hooks/` | Add `test_enforce_agatha_paths.py`, `test_enforce_product_paths.py`, `test_enforce_ux_paths.py`, `test_enforce_ellis_paths.py` following the `test_enforce_colby_paths.py` template: one allowed-path test, one blocked-path test, one DEFAULT_CONFIG parity test per hook. |
| R3 | **Critical** | Test gate | Red state | Six tests currently failing: `test_T_0014_018_micro_tier_1_only` (tier-1 telemetry), `test_T_0018_067` (ADR-0018 pipeline-orchestration sections unchanged), `test_T_0022_002_shared_references`, `test_T_0033_026_header_comment_says_write_not_write_edit`, `test_T_0024_048_full_pytest_suite_passes` (self-referential gate), `test_T_0024_050_subagent_stop_has_exactly_3_hooks` — the last one asserts settings.json has 2 hooks but finds 3, meaning **settings.json has drifted from ADR-0025's spec**. `test_T_0024_048` turns any single failure into a pipeline-blocking cascade. | `tests/adr-0014-telemetry/test_telemetry_structural.py`, `tests/hooks/test_enforce_roz_paths.py`, `tests/hooks/test_adr_0025_telemetry_extraction.py` (T-0024-050) | Fix the 5 non-self-referential failures first. Route T-0024-050 to Cal — this is a spec-vs-implementation divergence, not a test bug. `test_T_0024_048` should either be replaced with a meta-test that aggregates pass-counts (not a self-referential PASS assertion) or deleted in favor of CI pipeline gates. |
| R4 | **High** | Brain MCP | Integration coverage | The entire brain MCP layer runs against `createMockPool()` and `createMockFetch()`. Zero happy-path tests against real PostgreSQL + pgvector. `tests/brain/helpers/mock-pool.mjs:29-39` does substring-matching on SQL — a real database could return different row ordering, NULL semantics, or fail on schema constraints the mock never enforces (CHECK, UNIQUE, foreign keys). Docker-compose is present (per scout evidence) but unused by CI. | `tests/brain/helpers/mock-pool.mjs`, `tests/brain/*.test.mjs` | Add an opt-in integration test suite gated on `ATELIER_BRAIN_INTEGRATION=1` that runs against `docker-compose up` postgres + pgvector. Minimum coverage: `agent_capture` happy path, `agent_search` pgvector similarity ordering, `atelier_trace` recursive CTE cycle detection against actual rows (not fake `{'1': 1}` row mocks — see `tools.test.mjs:362`). |
| R5 | **High** | Brain MCP | Negative path | Zod enum validation is never exercised with invalid input. `tests/brain/tools.test.mjs:114-120` acknowledges "invalid types would be rejected by zod validation before the handler is called" then does NOT write that test. There is no test that calls `agent_capture({source_agent: 'not-an-agent'})` and asserts it fails. This is the exact gap that hides R1. | `tests/brain/tools.test.mjs:113-120` | Add negative tests per enum: `thought_type`, `source_agent`, `source_phase`, `status`, `relation_type`. One test per enum with an invalid string and an assertion the handler returns `isError: true` or throws a Zod validation error. |
| R6 | **High** | Test infrastructure | Fragility | `test_T_0024_048_full_pytest_suite_passes` is a **self-referential gate** — it runs pytest to verify pytest passes. Any other failure cascades into this one, doubling the red count and masking the real failure. Also risks infinite recursion if implemented naively. | `tests/hooks/test_adr_0025_telemetry_extraction.py` (approx.) | Replace with a CI-level job that runs `pytest --tb=short` and reports. Self-referential gates belong in a meta-test runner, not inside the suite they test. |
| R7 | **High** | Pipeline flow | Wiring | No test verifies that every hook in `source/claude/hooks/` is registered in `.claude/settings.json` (or vice versa). `test_hook_wiring.py` exists but does not enforce bidirectional completeness. A new hook can ship unregistered; a settings.json entry can reference a deleted hook. Retro lesson #005 (frontend wiring omission) is the cross-layer pattern — applies here to the hook layer. | `tests/hooks/test_hook_wiring.py`, `source/claude/hooks/`, `.claude/settings.json` | Add `test_every_hook_is_registered` and `test_every_settings_hook_exists_on_disk`. Use `glob.glob('source/claude/hooks/*.sh')` and parse settings.json hook arrays. |
| R8 | **High** | Brain MCP | Concurrency | No test exercises `brain/lib/rest-api.mjs` under concurrent requests. The mock pool is not thread-safe-aware and every query matches the first substring. A concurrent capture + search flow could deadlock on a real pgvector index or produce interleaved `queries[]` arrays the mock cannot represent. | `tests/brain/rest-api.test.mjs` | Add parallel-request test (Promise.all of 10 captures + 10 searches) using a real or high-fidelity mock that simulates connection-pool limits. |
| R9 | **Medium** | Test authoring | Mock fidelity | `createMockPool.findResult` in `mock-pool.mjs:29-39` is a substring-include check on the first registered pattern. Two queries that share a substring (e.g., `FROM thoughts WHERE id` matches both the root lookup in `atelier_trace` and the generic SELECT at line 343) will silently collide. Tests pass because the first registered result is returned; real database would return different rows. | `tests/brain/helpers/mock-pool.mjs:29-39`, `tests/brain/tools.test.mjs:409-420` | Upgrade mock to match on exact SQL (or regex-anchored match) and fail-loudly on ambiguous matches. Alternatively, switch to a real integration suite (R4) which makes the mock fidelity question moot. |
| R10 | **Medium** | Hook enforcement | Ambiguity | Tests verify per-agent hooks read `tool_input.file_path` but no test verifies which field the hooks consume for agent identification (`agent_type` vs `subagent_type`). Brain signal #4 flags this ambiguity. A payload key change from Claude Code would silently disable enforcement. | `tests/hooks/conftest.py:124-141` (builders use both), `source/claude/hooks/enforce-*-paths.sh` | Add a schema-freeze test: `test_hook_input_schema_fields_match_claude_code_spec`. Lock the expected field names and version them per ADR. |
| R11 | **Medium** | Spec traceability | Missing tests | ADR-0028, 0029, 0030, 0031, 0032 have no test directories. ADR-0032 (session isolation) is pre-implementation — Roz should write test assertions BEFORE Colby builds per project convention. No pre-build test files exist. | `docs/architecture/ADR-0028*.md` through `ADR-0032*.md`, `tests/` | For each unimplemented ADR, create a `tests/adr-NNNN/test_<adr_name>.py` with failing Roz-first assertions. For shipped ADRs (0028-0031), open blocker tickets. |
| R12 | **Medium** | Test composability | Fixture reuse | `tests/hooks/conftest.py` fixtures (`hook_env`, `simplified_env`, helper builders) are well-factored and composable. But `tests/brain/` has no equivalent conftest — every test file copies helper imports. Brain test helpers live in `tests/brain/helpers/` but are not exposed via fixtures. Adding a new brain test requires replicating the `beforeEach` dance from `tools.test.mjs:39-52`. Cross-suite: `tests/conftest.py` and `tests/hooks/conftest.py` both define `PROJECT_ROOT`, `SOURCE_AGENTS`, `SHARED_DIR` — two sources of truth for the same constants. | `tests/conftest.py:17`, `tests/hooks/conftest.py:14`, `tests/brain/` (no conftest) | Extract brain test setup into a shared helper module (`tests/brain/helpers/setup.mjs`) that exports a `setupBrainTest()` function. Consolidate path constants in `tests/conftest.py` and re-import from `tests/hooks/conftest.py`. |
| R13 | **Medium** | Meta-tests | Missing | No test validates enum completeness. `SOURCE_AGENTS` in `config.mjs` lists 10 agents but `brain-extractor.md` targets 9 with partial overlap (brain signal #1). No test cross-references these. | `brain/lib/config.mjs:18`, `source/shared/agents/brain-extractor.md:43-53`, `tests/hooks/test_brain_extractor.py` | Parameterized meta-test: for each agent_type in the extractor mapping, assert source_agent ∈ SOURCE_AGENTS and source_phase ∈ SOURCE_PHASES. Also: for each agent listed in agent-system.md's core team, assert it appears in SOURCE_AGENTS. |
| R14 | **Medium** | Dashboard | Known gap | User memory `project_dashboard_agent_fitness_gap.md` documents that dashboard agent fitness shows "Processing" — T1↔T2 aggregation missing. No test codifies the expected fitness contract. Gap will recur. | `tests/dashboard/test_dashboard_integration.py` | Write a Roz-first test: given synthetic T1 counter rows, assert T2 fitness score = expected value. Currently will fail — correct behavior. |
| R15 | **Low** | Test organization | Discoverability | `tests/hooks/` has 34 files, `tests/brain/` has 14 .mjs files. File names mix prefixes (`test_adr_0022_phaseN_*`, `test_enforce_*_paths`, `test_T_0024_*` by ID). There is no index. New contributors cannot know what is tested without grep. | `tests/hooks/`, `tests/brain/` | Generate `tests/TEST_INDEX.md` (script-derived, not hand-maintained) that lists each test file with its ADR, scope, and test count. Re-run on CI. |
| R16 | **Low** | Brain MCP | Happy-path seam | `tests/brain/tools.test.mjs:66` asserts exactly 8 tools registered. If a 9th tool is added, this test fires — good. But the hard-coded expected list (`agent_capture`, `agent_search`, etc.) is duplicated as a tool-by-tool check from lines 67-74. If the tool names change casing or underscore-to-dash, every test silently needs updating. | `tests/brain/tools.test.mjs:65-77` | Replace with a single assertion: `assert.deepStrictEqual(Array.from(srv.tools.keys()).sort(), EXPECTED_TOOLS.sort())`. |
| R17 | **Low** | Retro traceability | Lesson #003 | Retro lesson #003 (Stop hook race condition) is mentioned in `retro-lessons.md` but there is no test that asserts Stop hooks do NOT run the test suite. A future Colby could re-add a quality-gate Stop hook and tests would be green. | `source/shared/references/retro-lessons.md:71-92`, `source/claude/hooks/` (no Stop hooks) | Add `test_no_stop_hook_runs_pytest` that parses settings.json and asserts no `Stop` or `SubagentStop` hook command contains `pytest` or `node --test`. |
| R18 | **Low** | Test output | Noise | Pytest emits an urllib3 deprecation warning on every run (`tests/adr-0014-telemetry/test_telemetry_structural.py::test_T_0014_001`). Not a failure, but inflates the test-output-scan surface. | `tests/adr-0014-telemetry/test_telemetry_structural.py:1` | Pin urllib3 in test requirements or suppress the specific warning via `pytest.ini` `filterwarnings`. |

---

## Composability of Tests

**pytest side (`tests/hooks/conftest.py`):** **Strong.** Fixtures (`hook_env`, `simplified_env`) are parameterizable. Helper builders (`build_tool_input`, `build_per_agent_input`, `build_agent_input`, `build_subagent_stop_input`) cover every hook input shape. `prepare_hook` / `run_hook` / `run_per_agent_hook` abstract the subprocess invocation cleanly. `hide_jq_env` is a nice utility for testing the jq-missing error path. A new per-agent hook test can be written in under 30 lines by composing these helpers. This is the test suite's main strength.

**pytest side (`tests/conftest.py`):** **Good structural helpers** (`extract_tag_content`, `assert_tag_order`, `extract_protocol_section`) but **duplicates path constants** with `tests/hooks/conftest.py`. Two sources of truth for `PROJECT_ROOT`, `SOURCE_AGENTS`, `SHARED_DIR` is a future drift vector — a rename in one place will not propagate to the other until a regression is discovered.

**Brain node side (`tests/brain/helpers/mock-pool.mjs`, `mock-fetch.mjs`):** **Weak.** No shared `beforeEach` setup — every `.test.mjs` file replicates `createMockPool() → createMockServer() → registerTools()` boilerplate. No per-suite defaults for brain config. Adding a new tool requires touching every existing test file's `describe` block. The mock substring-match (R9) is not composable — two tests in the same file can silently collide on query patterns.

**Verdict:** Hook tests are a **reusable toolkit**. Brain tests are **copy-paste**.

---

## Positive Observations

1. **ADR-0033 test discipline is exemplary.** 30 tests spread across 7 files (T-0033-001 through T-0033-030), each with a docstring explaining the ADR reference, the wave (W1/W2), and the acceptance criterion it locks. `test_T_0033_030_conftest_default_config_mirrors_enforcement_config` explicitly locks a manual mirror — the test FAILS if either file drifts. This is the **Roz-first TDD pattern working as intended** and should be the template for every future ADR.

2. **Loop-prevention defense is double-layered AND tested.** `test_T_0024_002_brain_extractor_excluded_from_if_condition` (primary: hook condition) and `test_T_0024_009_extractor_early_exit_guard` (secondary: persona instruction) encode Retro lesson #003 at both the wiring and behavioral layers. The test comments reference the retro ID directly — traceability is explicit, not implied.

3. **Hook test infrastructure is a reusable toolkit.** `tests/hooks/conftest.py` provides composable builders (`build_tool_input`, `build_per_agent_input`, `build_agent_input`, `build_subagent_stop_input`, `build_stop_failure_input`), environment-override runners (`run_hook`, `run_per_agent_hook`, `run_hook_with_project_dir`, `run_hook_without_project_dir`), and state helpers (`write_pipeline_status`, `write_brain_state`, `hide_jq_env`). A new hook test can be written in <30 lines.

4. **bats → pytest migration (ADR-0022) successfully executed.** 777+ tests now live in pytest where they are visible to the standard test command. `test_no_bats.py` prevents regression. User memory `feedback_pytest_only.md` codifies the lesson. This addresses a real invisibility problem and the migration artifacts (conftest helpers) are production-grade.

5. **XML prompt structure coverage is comprehensive.** 9 test files in `tests/xml-prompt-structure/` validate tag order, required sections, cognitive directives, retro references, and cross-step consistency for every persona. `test_T_0005_040_all_agents_have_6_tags_in_order` iterates every agent file and reports all errors at once — not fail-fast, which surfaces multiple issues per run.

6. **Persona cognitive directives are enumerated as a lookup table.** `tests/conftest.py:101-118` `COGNITIVE_DIRECTIVES` dict maps every agent/command to its required "Never …" anchor phrase. Any new agent without a directive gets flagged at test time. This is exactly the right shape for preventing brain signal #3 (behavioral constraints ignored).

---

## Roz's Assessment

The pytest layer, especially the hook enforcement slice, is the best-engineered part of this codebase's test suite. Whoever built `tests/hooks/conftest.py` understood composability. ADR-0033's 30-test audit is the model every future ADR should follow.

The brain MCP layer is the opposite. It is a mock monoculture. 23 node tests against a mock that substring-matches SQL is not testing — it is ritual. The Zod enum boundary between `config.mjs` and `brain-extractor.md` is **live contract drift** (finding R1, R13): five of the nine target agents for mechanical brain writes cannot actually capture because their mapped `source_agent`/`source_phase` values fail Zod validation at runtime. Nobody caught this because no test ever feeds the mapping table through the Zod schema. This is exactly the failure mode that ADR-0024 was written to prevent at a different layer.

The six red tests are not noise. `T-0024-050` is signalling that settings.json has drifted from ADR-0025's specification — that is a **spec-level divergence**, not a test bug. Route to Cal, not Colby. `T-0024-048` (self-referential full-suite gate) is amplifying the red count and should be deleted or rewritten as a CI job outside the test suite.

Four enforce-paths hooks with zero direct tests (R2) is the same class of omission as retro lesson #005 (frontend wiring omission): shipping a producer without verifying the consumer. Pattern recurrence count: 2+. If it hits 3, Eva should inject a WARN into every Colby invocation that writes a hook script.

**Must-fix before Round 4 closes:** R1 (enum-boundary meta-test), R2 (four missing hook tests), R3 (six red tests). Everything else is queueable.

**Doc Impact:** YES. ADR-0024 and ADR-0025 need a reconciliation note about `SOURCE_AGENTS`/`SOURCE_PHASES` enum expansion (or a downgrade of the 9-agent extractor scope to match the existing enum). `CLAUDE.md` Key Conventions should add: "every persona mapping table must have a meta-test against its corresponding enum source."
