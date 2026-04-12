# ADR-0034: Gauntlet 2026-04-11 Remediation — Wave-Based Plan

## DoR: Requirements Extracted

| # | Requirement | Source | Traced from |
|---|---|---|---|
| R1 | Fix every silently-failing `agent_capture` from robert/robert-spec/sable/sable-ux/ellis/sentinel/darwin/deps/brain-extractor | M1 (4-agent) | `gauntlet-combined.md:26` |
| R2 | Resolve the single remaining active Zod/enum/hook drift across config.mjs + schema.sql + brain-extractor.md + settings.json + rest-api.mjs with ONE coordinated change set | M1, M9 | `gauntlet-combined.md:26,34` |
| R3 | Make the red test suite (6 failing tests) green OR explicitly delete the self-referential gate T-0024-048 | M4 | `gauntlet-combined.md:29` |
| R4 | Implement the ratified-but-absent ADR-0032 (pipeline state session isolation) | M3 | `gauntlet-combined.md:28`, `ADR-0032` Implementation Plan |
| R5 | Add hook tests for the four untested `enforce-*-paths.sh` hooks (agatha, product, ux, ellis) | M6 | `gauntlet-combined.md:31` |
| R6 | Extract a single shared hook library (`hook-lib.sh`) and re-wire duplicated parsers (PIPELINE_STATUS grep, agent_type jq, json_escape) | M5, S22 | `gauntlet-combined.md:30,71` |
| R7 | Replace the 144-line hand-rolled `runMigrations()` with a file-loop driven by a `schema_migrations` tracking table; ship migration 008 on the new rail | M7 | `gauntlet-combined.md:32` |
| R8 | Remove four per-handler `Access-Control-Allow-Origin: *` overrides in rest-api.mjs | M8 | `gauntlet-combined.md:33` |
| R9 | Harden three brain-side correctness bugs: gracefulShutdown drain race (S5), LLM null guards (S10), dashboard XSS on `s.sub2` + `renderAgents` (M10) | S5, S10, M10 | `gauntlet-combined.md:35,54,59` |
| R10 | Delete the `session-hydrate.sh` dead stub AND its settings.json registration in the pipeline-setup template | M13 | `gauntlet-combined.md:38` |
| R11 | Close the Cursor hook parity gap per `cursor-port.md` AC-5/AC-7/AC-8/AC-9 | S8 | `gauntlet-combined.md:57` |
| R12 | Fix the broken dashboard install path in SKILL.md:802 | S9 | `gauntlet-combined.md:58` |
| R13 | Tighten brain server hardening: static path traversal (S16), CDN SRI (S17), consolidation initial run (S24), health endpoint recon surface (S23), SQL placeholder non-sequential (S21), hardcoded LLM model (S14) | S14, S16, S17, S21, S23, S24 | `gauntlet-combined.md:63,65,66,70,72,73` |
| R14 | Documentation sweep owned by Agatha: triple-source assembly (S1), REST auth (S11), hook-addition procedure (S19), Gauntlet in user guide (S20), migrations table 001–007 (M11), REST endpoints completeness (S25), ADR index (M15) | S1, S11, S19, S20, S25, M11, M15 | `gauntlet-combined.md:37,40,50,60,67,69,74` |
| R15 | Resolve the `enforce-ellis-paths.sh` vs. ADR-0022 R20 contradiction (S4) — either delete the hook or author a superseding ADR | S4 | `gauntlet-combined.md:53` |
| R16 | Resolve the ADR-0001 dead link (S3) — move file or update references | S3 | `gauntlet-combined.md:52` |
| R17 | Address the two team-collaboration-enhancements spec gaps — Handoff Brief protocol (S6), context-brief dual-write gate (S7) | S6, S7 | `gauntlet-combined.md:55,56` |

**Explicitly out of scope (user-accepted risk):** M2 — MCP HTTP unauthenticated endpoint + token-in-HTML injection. Decision recorded in Gauntlet handoff; this ADR does NOT design any work for M2.

**Anti-goals:**

1. **Anti-goal:** Rewriting the brain-extractor persona or agent routing model. Reason: M1 is an enum-sync bug, not a design bug — the persona, the settings.json condition, and the rest-api SQL all already know the correct 9 agents individually; they are just out of sync. Revisit: if scout finds a second independent source of truth after Wave 1 ships.
2. **Anti-goal:** Closing M2 (MCP auth) in any wave. Reason: user has explicitly accepted the risk as a localhost dev tool. Revisit: if brain server is ever exposed beyond localhost OR if multi-user shared brain mode ships.
3. **Anti-goal:** Designing Darwin-generated structural proposals into any wave. Reason: this ADR is human-authored remediation; Darwin's outputs go through their own review gate. Revisit: after all waves land and Darwin re-runs on the fixed codebase.

**Spec challenge:** The combined register assumes the M1 cluster can be fixed in "one change set" that touches five files. **If the assumption is wrong in one load-bearing way, the fix fails because** the five files are not, in fact, the only sources of truth. Evidence gathered: `brain/lib/rest-api.mjs:340` hardcodes a literal agent list in a SQL `IN` clause — a *sixth* source of truth flagged separately as M9. Wave 1 MUST fix M1 and M9 together or the hardcoded SQL will silently shadow the fix. The ADR plan below treats M1+M9 as one atomic change.

**SPOF:** The Zod → Postgres enum boundary. Failure mode: Wave 1 ships config.mjs + schema.sql changes but the Postgres `ALTER TYPE` migration fails on a target database (e.g., user is inside a transaction that cannot ALTER TYPE, or the database is on an older pg with a bug). Graceful degradation: migration 008 is idempotent and wrapped in its own try/catch in the legacy `runMigrations()` flow; if it fails, the server still boots, logs the error, and all captures from the 9 agents continue to fail silently — same as today, no regression. The server does NOT panic. Wave 2 (migration runner refactor) can then land independently.

**Retro risks:**

- **Lesson #003 (Stop Hook Race Condition):** Wave 1 touches `session-boot.sh` via ADR-0032 implementation. The new helper must remain non-blocking, filesystem-local, and exit 0 on every error path.
- **Lesson: "Behavioral guidance is ignored — mechanical enforcement via PreToolUse hooks is required."** Every new hook added in this ADR must ship with a pytest in `tests/hooks/` in the same step (Roz-first).
- **Lesson: "Never bundle commit/push into Colby's prompt."** Each wave terminates with explicit Ellis hand-off; Colby never commits.

---

## Status

Proposed — 2026-04-11. Supersedes nothing (supplements ADR-0032, which remains Approved and will be *implemented* by Wave 1 of this ADR).

## Context

On 2026-04-11 the Gauntlet completed an 8-round full-codebase audit of `atelier-pipeline`. Rounds 1–9 (Cal, Colby, Roz, Sentinel, Sable, Robert, Poirot, Agatha) produced a combined register of 15 multi-agent findings and 25 single-agent findings at `docs/reviews/gauntlet-2026-04-11/gauntlet-combined.md`. Round 8 (Deps) was skipped because `deps_agent_enabled: false`.

The register's executive summary identified two clusters. **Cluster 1 (brain capture drift, 4-agent consensus):** the `SOURCE_AGENTS` and `SOURCE_PHASES` Zod enums in `brain/lib/config.mjs` have been out of sync with the brain-extractor persona mapping table and with the `.claude/settings.json` SubagentStop `if` condition. Every `agent_capture` call from robert, robert-spec, sable, sable-ux, ellis, sentinel, darwin, and deps currently fails Zod validation and is silently discarded — which means **the brain has been missing captures from 8 agents since the scope was extended**, and the SubagentStop hook does not even fire for 5 of them. **Cluster 2 (MCP HTTP auth gap, 2-agent consensus):** user-accepted, explicitly out of scope.

The register also surfaced four Critical findings (M1 enum drift, M3 ADR-0032 unimplemented, M4 red test suite, S1 triple-source assembly undocumented, S2 dashboard modal a11y, S3 ADR-0001 dead link), eleven High findings, and fourteen Medium/Low findings. This ADR organises all in-scope findings into a wave-based remediation plan.

The remediation budget is bounded by two constraints: (1) Colby can only edit `source/` — the installed `.claude/` tree is rewritten by `/pipeline-setup`; and (2) pipeline-setup's SKILL.md is the actual source of truth for `.claude/settings.json` and must be edited there, not in the installed copy. Every fix that touches settings.json is therefore a skill-template edit followed by a user re-run of `/pipeline-setup`.

## Decision

Ship a **six-wave remediation** over six independent Colby+Roz sessions. Waves 1–3 carry the Critical and High-consensus findings and are designed in full detail below. Waves 4–6 carry the remaining Medium/Low/documentation work and are outlined for future ADRs (each wave will be re-planned in its own ADR before implementation).

**Wave ordering rationale:**

- **Wave 1 = restore silent drops.** Fix M1+M9 (enum drift + hardcoded SQL sources of truth) plus M3 (ADR-0032 implementation). These are the findings where *real work is being silently dropped on the floor today*: captures discarded by Zod, concurrent sessions clobbering each other's state. Bounded blast radius, independently deployable, independently testable. After Wave 1, every capture that tries to land actually lands and every session gets its own state directory.
- **Wave 2 = stabilize enforcement.** Close the three hook-layer gaps: M5 (shared hook library), M6 (four untested hooks), M7 (migration runner refactor), M13 (session-hydrate dead stub). This makes the enforcement layer safe to extend.
- **Wave 3 = harden brain correctness.** M8 (CORS), M10 (dashboard XSS), S5 (gracefulShutdown drain), S10 (LLM null guards), M4 (red test suite greening). This is the last Colby-heavy wave; after it lands the brain has no known correctness bugs.
- **Waves 4–6** are Sable/Agatha/Robert-heavy (dashboard a11y, docs sweep, spec additions) and will be designed in separate ADRs (ADR-0035, ADR-0036, ADR-0037).

**Every wave is independently shippable:** if Wave 2 stalls on code review, Wave 3 can still land because its only brain dependency is the schema (unchanged) and its only hook dependency is the unshared `session-boot.sh` (Wave 2 does not block Wave 3 on hooks — Wave 2 only extracts *duplicated* code, so Wave 3's edits are disjoint).

## Alternatives Considered

**Alternative A: One mega-PR covering everything.** Rejected. The combined register has ~40 in-scope findings; a single session cannot hold this scope. Colby's context window and Roz's review capacity both cap at roughly 10–12 files of focused work before quality degrades.

**Alternative B: Fix by severity, ignoring coupling.** Start with all Critical findings, then all High, then all Medium. Rejected because M1 and M9 must ship together (otherwise rest-api.mjs's hardcoded SQL silently shadows the enum fix), and M1 and M7 are coupled through the migration file (new migration 008 rides on either the old rail or the new rail — it cannot straddle both). Coupling beats severity as the grouping axis.

**Alternative C: Fix M1 in isolation and defer everything else to a rolling triage.** Rejected because M3 (ADR-0032) and M4 (red tests) have both been open for weeks and the longer they sit the more the codebase drifts around them. The 3-wave-detailed plan is the minimum scope that restores both "no silent drops" AND "no red tests" AND "no unimplemented approved ADRs" in one sprint.

**Alternative D: Rewrite `brain/lib/` end-to-end.** Rejected as anti-goal #1.

## Consequences

**Positive:**

- After Wave 1: every `agent_capture` from every target agent lands successfully; concurrent sessions no longer clobber each other; the register's two most-cited Critical findings close.
- After Wave 2: the enforcement layer has a single audited parser for `PIPELINE_STATUS` + `agent_type`, so any future bug fix applies in one place. Four previously untested hooks now have behavioural tests.
- After Wave 3: dashboard has no known XSS vector, brain has no unguarded LLM response access, and the full test suite is green.

**Negative:**

- Wave 1 requires users to re-run `/pipeline-setup` to pick up the new settings.json SubagentStop condition. This is a one-time migration cost documented in the Wave 1 release notes.
- Wave 2's migration runner refactor is risky because it replaces 144 lines of working-but-ugly code. Mitigation: the new runner must run backfill against the existing schema in a test environment before Wave 2 ships; the old `runMigrations()` stays in git history for one release as a rollback target.
- The ADR index (M15) and the 17 missing ADRs will not be added until Wave 5. Auditors during Waves 1–4 still hit incomplete navigation.

**Migration / rollback (Wave 1):**

- **Migration 008** — `ALTER TYPE source_agent ADD VALUE IF NOT EXISTS ...` for `sentinel`, `darwin`, `deps`, `brain-extractor`, `robert-spec`, `sable-ux`; same pattern for `source_phase` adding `product`, `ux`, `commit`. Idempotent — matches the pattern of migrations 003–006.
- **Rollback window:** one release. A rollback removes the migration 008 file but does NOT attempt to remove enum values (Postgres does not support removing enum values cleanly). The Zod enum in `config.mjs` can be reverted independently. Rolling back M1 means captures go back to silent-drop mode — same as today, no data loss.
- **Rollback for ADR-0032 helper:** the helper returns the legacy `docs/pipeline/` path on any resolution failure, so rolling back is removing the helper and the hook will automatically fall through to legacy.

---

## Implementation Plan

### Wave 1: Silent Drops — Enum Sync + ADR-0032 Implementation

**Goal:** After this wave, zero `agent_capture` calls are silently discarded, and two concurrent sessions in the same worktree no longer clobber each other's pipeline state.

**Findings closed:** M1, M3, M9, S12, S15 (partial — only ADR-0032 tests, the other ADR test coverage stays in a later wave).

**Cross-cutting dependency:** Wave 1 is the only wave that touches `skills/pipeline-setup/SKILL.md`'s settings.json template. Users must re-run `/pipeline-setup` after Wave 1 to pick up the SubagentStop condition change. Release notes must be explicit.

#### Step 1.1 — Brain enum extension + migration 008 + schema + rest-api wiring (atomic vertical slice)

**Files (10):**

1. `brain/lib/config.mjs` — extend `SOURCE_AGENTS` with `sentinel`, `darwin`, `deps`, `brain-extractor`, `robert-spec`, `sable-ux`; extend `SOURCE_PHASES` with `product`, `ux`, `commit`.
2. `brain/schema.sql` — mirror the extended enum values in the `CREATE TYPE` statements (fresh-install parity).
3. `brain/migrations/008-extend-agent-and-phase-enums.sql` — new file. `ALTER TYPE source_agent ADD VALUE IF NOT EXISTS '...'` for each new agent, same for phases. Follow the idempotency pattern of migrations 003 and 005.
4. `brain/lib/db.mjs` — add a new Migration 008 block in `runMigrations()` mirroring the 003/005 pattern (check `pg_enum` for label existence, then apply the file). This is a *temporary* addition — Wave 2 replaces the entire runner — but Wave 1 cannot ship on the Wave 2 runner.
5. `brain/lib/rest-api.mjs` — import `SOURCE_AGENTS` from `config.mjs`; in `handleTelemetryAgents` around line 340, replace the hardcoded `IN (...)` literal with a dynamically constructed parameterized clause. This closes M9.
6. `brain/lib/tools.mjs` — verify `z.enum(SOURCE_AGENTS)` picks up new values automatically (no edit expected; sanity check only). Document in Notes for Colby.
7. `tests/brain/enum-boundary.test.mjs` — NEW Roz-authored test (see Roz test spec below). Cross-validates: every row in the brain-extractor mapping table → appears in SOURCE_AGENTS; every phase → appears in SOURCE_PHASES; every SOURCE_AGENTS entry → has a row in the mapping table OR is explicitly marked as eva/poirot/distillator (non-extracted agents).
8. `tests/brain/rest-api.test.mjs` — extend with a test that asserts `handleTelemetryAgents` uses `SOURCE_AGENTS` as the source (not a hardcoded literal).
9. `tests/brain/db.test.mjs` — extend with a test that asserts migration 008 registers a label check before running, same as 003/005.
10. `docs/architecture/ADR-0034-gauntlet-remediation.md` — this file (link existing; no edit).

**Complexity:** 10 files, 5 production + 3 test + 2 schema. Passes S1 (one design axis: enum sync), S2 (Wave 1 Step 1 is standalone), S3 (migration idempotent), S4 (test fixture adds 2 files), S5 (Colby session fits).

**Acceptance criteria:**

- `SOURCE_AGENTS` in `config.mjs` has exactly 16 entries: 9 agents in the brain-extractor mapping table (cal, colby, roz, agatha, robert, robert-spec, sable, sable-ux, ellis) plus eva, poirot, distillator (3 non-extracted), plus 4 new non-extracted agents not in the table (sentinel, darwin, deps, brain-extractor) = 16 total.
- `SOURCE_PHASES` in `config.mjs` includes `product`, `ux`, `commit` in addition to existing.
- `schema.sql` fresh install declares the same values.
- Migration 008 applies cleanly against a database at any prior migration state (001 through 007).
- `handleTelemetryAgents` in `rest-api.mjs` constructs its SQL `IN` clause from `SOURCE_AGENTS`, not a literal.
- `tests/brain/enum-boundary.test.mjs` passes.
- Running `pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs` produces zero new failures.

#### Step 1.2 — Settings.json SubagentStop condition (skill template) + release notes

**Files (3):**

1. `skills/pipeline-setup/SKILL.md` — verify line ~410 already lists all 9 agents in the SubagentStop `if` condition (scout confirmed it does). If drifted from canonical list, update.
2. `skills/pipeline-setup/SKILL.md` — add a "Migration Note" block near the top documenting that users on older installs must re-run `/pipeline-setup` to pick up the Wave 1 SubagentStop condition change. Include the exact agent list.
3. `docs/pipeline/adr-0034-wave-1-release-notes.md` — NEW file. One-page summary: what changed, who must re-run `/pipeline-setup`, how to verify (example `agent_capture` call from sentinel hitting the brain and appearing in `atelier_browse`).

**Complexity:** 3 files, doc-only in this step. Passes the sizing gate trivially.

**Acceptance criteria:**

- SKILL.md SubagentStop condition lists `cal || colby || roz || agatha || robert || robert-spec || sable || sable-ux || ellis` (9 agents, matching brain-extractor mapping).
- Release notes file exists and is linked from the wave-1 handoff.

#### Step 1.3 — ADR-0032 implementation: pipeline-state-path.sh helper + session-boot.sh + post-compact-reinject.sh

ADR-0032 already contains a ratified Implementation Plan (Steps 1–3). Wave 1 Step 1.3 executes ADR-0032's Step 1 only (shared helper + session-boot + post-compact). ADR-0032 Steps 2–3 (hydrate-telemetry rewire + Eva hard-pause behavior) are **deferred to Wave 4** because they touch `hydrate-telemetry.mjs` (1029 lines) and merit their own Colby session.

**Files (6):**

1. `source/shared/hooks/pipeline-state-path.sh` — NEW. Shared bash function library. Exports `pipeline_state_dir()` which resolves: (a) `CLAUDE_PROJECT_DIR` if set, (b) `CURSOR_PROJECT_DIR` if set, (c) `pwd` fallback. Computes `sha256sum | head -c 8` of the absolute worktree root. Returns `~/.atelier/pipeline/{project_slug}/{worktree_hash}/`. On any error, returns the legacy `docs/pipeline/` string and exits 0. Follows ADR-0032 Decision section exactly. Sourced by both hooks below.
2. `source/claude/hooks/session-boot.sh` — update line 41: replace `PIPELINE_STATE_FILE="docs/pipeline/pipeline-state.md"` with `source "$SCRIPT_DIR/pipeline-state-path.sh"; STATE_DIR=$(pipeline_state_dir); PIPELINE_STATE_FILE="$STATE_DIR/pipeline-state.md"`. Update lines 54 and 65 similarly for `context-brief.md` and `error-patterns.md`. Verify `error-patterns.md` stays in-repo per ADR-0032 Decision (it does — the helper returns the per-worktree dir but the migration logic distinguishes per-file).

   **Subtlety:** ADR-0032 Decision specifies that `error-patterns.md` stays in-repo while the other three files move out-of-repo. The helper should expose TWO functions: `session_state_dir()` (per-worktree, out-of-repo) and `error_patterns_path()` (in-repo, unchanged). Update session-boot accordingly.
3. `source/claude/hooks/post-compact-reinject.sh` — source the same helper and read from `$(session_state_dir)/pipeline-state.md` and `$(session_state_dir)/context-brief.md`.
4. `source/cursor/hooks/session-boot.sh` — mirror the Claude-side changes (ensuring Cursor picks up the helper too). Scout: verify this file exists and source it; if not, document as deferred.
5. `tests/hooks/test_pipeline_state_path.py` — NEW Roz-authored test (see Roz spec below).
6. `tests/hooks/test_session_boot_state_isolation.py` — NEW Roz-authored test asserting that two mock worktrees resolve to different directories under `~/.atelier/pipeline/` AND that a helper failure falls back to `docs/pipeline/`.

**Complexity:** 6 files, 3 hook edits + 1 new helper + 2 tests. S1–S5 all pass. Note: ADR-0032 Step 1 in its own plan identified ~6 files; this matches.

**Acceptance criteria:**

- `source/shared/hooks/pipeline-state-path.sh` exists, is executable, and both functions return the specified paths.
- `session-boot.sh` reads state files from the helper's output, never from a hardcoded `docs/pipeline/` path (except through the helper's legacy fallback).
- `post-compact-reinject.sh` reads from the same helper.
- Two concurrent mock sessions in different worktrees produce different state directories AND never overwrite each other.
- All existing hook tests still pass (`tests/hooks/`).
- ADR-0032 status stays **Approved** (this ADR implements it, does not supersede it).

---

### Wave 2: Enforcement Stabilization — Shared Hook Library + Missing Tests + Migration Runner + Dead Stub

**Goal:** After this wave, the three-layer enforcement pyramid has zero duplicated parsers, four previously-untested hooks have pytest coverage, the 144-line migration runner is a 20-line file loop, and the dead `session-hydrate.sh` registration is removed from the skill template.

**Findings closed:** M5, M6, M7, M13, S22.

#### Step 2.1 — Shared hook library `hook-lib.sh`

**Files (~12):**

1. `source/shared/hooks/hook-lib.sh` — NEW. Bash function library exporting:
   - `hook_lib_pipeline_status_field <field_name>` — reads stdin, uses `jq -R 'fromjson? // empty | .PIPELINE_STATUS // empty | .[$name]' --arg name "$field"`. Multiline-safe, handles missing field.
   - `hook_lib_get_agent_type` — reads stdin, `jq -r '.agent_type // .tool_input.subagent_type // empty'`. Canonical.
   - `hook_lib_assert_agent_type <expected>` — defense-in-depth; exits 0 if match, 2 with BLOCKED message otherwise.
   - `hook_lib_json_escape <string>` — uses `jq -Rs .` (fixes S22 non-functional sed).
   - `hook_lib_emit_deny <reason>` / `hook_lib_emit_allow` — uniform JSON output helpers.
2. `source/shared/hooks/session-boot.sh` — replace inline `json_escape()` with `source $SCRIPT_DIR/hook-lib.sh; hook_lib_json_escape`. This closes S22.
3. `source/claude/hooks/session-boot.sh` — source `hook-lib.sh` and use the shared PIPELINE_STATUS parser on line 43 and around. Delete the inline parser.
4. `source/claude/hooks/enforce-sequencing.sh` — replace the duplicated parser with `hook_lib_pipeline_status_field phase`.
5. `source/claude/hooks/enforce-scout-swarm.sh` — same.
6. `source/claude/hooks/log-agent-start.sh` — replace inline `jq -r '.agent_type // empty'` with `hook_lib_get_agent_type`.
7. `source/claude/hooks/log-agent-stop.sh` — same.
8. `source/claude/hooks/enforce-cal-paths.sh` — same.
9. `source/claude/hooks/enforce-colby-paths.sh` — same.
10. `source/claude/hooks/enforce-roz-paths.sh` — same.
11. `source/claude/hooks/enforce-agatha-paths.sh` — same.
12. `source/claude/hooks/enforce-pipeline-activation.sh` — same.
13. *(Continues for remaining hooks that match the scout-identified 15+ duplication sites. Colby enumerates during build.)*

**Roz test:** `tests/hooks/test_hook_lib.py` — NEW. Unit-tests the five library functions against golden inputs, including:
- Multiline content containing `}` inside the PIPELINE_STATUS value.
- Missing PIPELINE_STATUS field.
- Missing agent_type / fallback to `tool_input.subagent_type`.
- `json_escape` of strings with newlines, quotes, backslashes, tabs.

**Complexity:** ~13 files — the upper bound of Colby session tolerance. Justification: the library itself is small; the rewiring is mechanical sed-style edits, one line per hook. If scout during build finds more than 15 duplication sites, Colby splits Wave 2 Step 1 into 2.1a (library + top 6 hooks) and 2.1b (remaining hooks). Documented in Notes for Colby.

**Acceptance criteria:**

- `hook-lib.sh` exists with all five functions documented.
- Every hook scout-identified as duplicating the PIPELINE_STATUS parser now sources `hook-lib.sh` and delegates.
- `json_escape` behavior now correctly encodes newlines (regression test T-0034-022 passes).
- All existing hook tests still pass.

#### Step 2.2 — Four missing hook tests (M6)

**Files (4):** New pytest files mirroring `test_enforce_colby_paths.py`:

1. `tests/hooks/test_enforce_agatha_paths.py` — 3 tests: blocked path, allowed path, DEFAULT_CONFIG parity.
2. `tests/hooks/test_enforce_product_paths.py` — same pattern.
3. `tests/hooks/test_enforce_ux_paths.py` — same pattern.
4. `tests/hooks/test_enforce_ellis_paths.py` — same pattern (plus: if Wave 2 ships *before* the S4 Ellis/ADR-0022 contradiction is resolved, the test must lock whichever behavior is canonical today; note in test docstring).

**Complexity:** 4 files, identical template, trivial. Test-only step.

**Acceptance criteria:**

- Each new test file contains at least 3 tests following the `test_enforce_colby_paths.py` template.
- `pytest tests/hooks/ -v` shows 12 new tests, all passing.

#### Step 2.3 — Migration runner refactor + schema_migrations table (M7)

**Files (6):**

1. `brain/schema.sql` — add `CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now(), checksum TEXT);`
2. `brain/migrations/009-schema-migrations-table.sql` — NEW. Creates `schema_migrations` in existing databases AND backfills rows for 001–008 as already-applied (using the existing idempotency checks to decide which version is actually applied). Wraps everything in a transaction.
3. `brain/lib/db.mjs` — rewrite `runMigrations()`. New shape: read `brain/migrations/` directory, sort by filename, for each file compute `sha256(content)`, check `schema_migrations` by `version = filename`; if absent, run the file's SQL inside a transaction, insert into `schema_migrations`, commit. Log applied/skipped per migration. Wrap individual migrations in try/catch to match current fail-soft semantics. Target: ≤40 lines (144 → 40 is a realistic reduction).
4. `brain/migrations/README.md` — NEW. Documents the file naming convention (`NNN-description.sql`), the idempotency requirement (`IF NOT EXISTS` / `ADD VALUE IF NOT EXISTS` / transaction-wrapped), and the backfill procedure.
5. `tests/brain/migrations-runner.test.mjs` — NEW. Tests the runner against `createMockPool()`: verify (a) unapplied migration runs and records in schema_migrations, (b) already-applied migration is skipped, (c) syntax error in migration file is logged and does not prevent subsequent migrations. Use mock pool's substring matching.
6. `tests/brain/db.test.mjs` — extend to verify the refactored runner preserves Migration 008 behavior (label check still present).

**Risk note:** This is the riskiest single step in the ADR. The new runner replaces 144 lines of working code. Mitigations: (a) the old runner stays in git for rollback; (b) Migration 009's backfill is idempotent and can be run repeatedly; (c) Roz runs the integration tests in the next step against real Postgres before Wave 2 ships.

**Complexity:** 6 files, 2 schema/migration + 1 runner + 2 tests + 1 doc. Near the upper limit. Justification: the runner is inherently coupled to the migration files and the schema table — splitting further creates an orphan producer (schema_migrations table with no writer).

**Acceptance criteria:**

- `runMigrations()` is ≤50 lines and contains no hardcoded migration numbers.
- Against a fresh database, all 009 migrations apply cleanly and schema_migrations has 9 rows.
- Against a database already at migration 008 (Wave 1 state), migration 009 runs, backfills schema_migrations, and subsequent startup is a no-op.
- A deliberately-broken migration file logged but does not prevent the next migration from running.

#### Step 2.4 — Delete session-hydrate.sh dead stub (M13)

**Files (2):**

1. `skills/pipeline-setup/SKILL.md` — remove all references to `session-hydrate.sh` except the intentional-no-op comment block (ADR-0026 context). Remove the install-copy line if present. Ensure the removal step already described at lines 71–82 of SKILL.md is correct (scout confirmed it is).
2. `source/claude/hooks/session-hydrate.sh` — keep the file (the SKILL.md doc says it's installed as a backward-compat shim) but add a deletion deadline comment: `# DELETE BEFORE: 2026-07-01 — see ADR-0034 Wave 2`. Actual deletion happens in a future ADR after one quarter of backward-compat.

**Note:** The register says "delete the stub AND its settings.json registration." Scout confirmed the registration is already absent from `.claude/settings.json` in the current repo. The remaining work is (a) ensuring the SKILL.md removal step remains in place for fresh installs of users on older versions, (b) adding the deletion deadline so the stub doesn't linger forever.

**Complexity:** 2 files, trivial.

**Acceptance criteria:**

- SKILL.md's Step 1 session-hydrate.sh removal block is still present and correct.
- The stub file has a deletion-deadline comment pointing at ADR-0034.

---

### Wave 3: Brain Correctness + Red Test Greening

**Goal:** After this wave, the full test suite is green, dashboard has no known XSS sink, gracefulShutdown actually drains the pool, and LLM response access is null-guarded.

**Findings closed:** M4, M8, M10, S5, S10.

#### Step 3.1 — Red test triage (M4)

**Files (~6, test-only except one config):**

1. `tests/adr-0014-telemetry/` (T-0014-018) — Roz investigates and fixes OR deletes with documented rationale. Must not touch production code unless the test reveals a production bug, in which case the fix is promoted to its own step and Wave 3 re-scoped.
2. `tests/` (T-0018-067) — same triage.
3. `tests/` (T-0022-002) — same.
4. `tests/` (T-0033-026) — same.
5. `tests/hooks/test_enforce_roz_paths.py` — DELETE T-0024-048 (self-referential gate). Replace with a CI job entry (documented, not implemented) OR a note in Notes for Colby for a future CI ADR.
6. `tests/hooks/test_adr_0025_telemetry_extraction.py` — T-0024-050 currently expects 2 SubagentStop hooks, finds 3. This is spec divergence that Wave 1 changes: after Wave 1, settings.json registers 3 SubagentStop hooks (the brain-extractor for 9 agents + ellis-specific + the aggregate). Update the expected count to 3 AND document the reason in the test docstring linking ADR-0034.

**Roz authority note:** This step is Roz-first from the start — Roz investigates each red test's root cause before any code change. Colby is only invoked if a production fix is actually required.

**Complexity:** ~6 files, mostly test edits. Passes sizing gate.

**Acceptance criteria:**

- `pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs` exits 0 with zero failures.
- T-0024-048 is deleted with a clear replacement path documented.
- T-0024-050 asserts `== 3` with a link to ADR-0034 in its docstring.

#### Step 3.2 — CORS wildcard override removal (M8)

**Files (2):**

1. `brain/lib/rest-api.mjs` — remove lines 278, 312, 386, 429 (`"Access-Control-Allow-Origin": "*"`). Verify the server-level CORS in `server.mjs:114` applies to these handlers and is sufficient.
2. `tests/brain/rest-api.test.mjs` — extend. For each of the 4 telemetry handlers, assert the response headers do NOT contain `Access-Control-Allow-Origin: *` and DO contain the per-request localhost origin set by server.mjs.

**Complexity:** 2 files, surgical.

**Acceptance criteria:**

- `grep -n "Access-Control-Allow-Origin" brain/lib/rest-api.mjs` returns zero matches (all CORS originated from `server.mjs`).
- Tests assert no wildcard on any of the 4 handlers.
- Manual curl against a running server produces `Access-Control-Allow-Origin: http://localhost:${PORT}` not `*`.

#### Step 3.3 — Dashboard XSS fixes (M10)

**Files (3):**

1. `brain/ui/dashboard.html` — line 1163: wrap `s.sub2` in `escapeHtml(s.sub2)`. Lines 1423–1427: wrap every `innerHTML =` agent metric interpolation in `escapeHtml()`. Scout every `innerHTML =` in the file; wrap any unwrapped string interpolations.
2. `brain/ui/dashboard.html` — add a top-of-file JSDoc-style comment documenting the XSS convention: "All `innerHTML =` assignments MUST wrap interpolated strings in `escapeHtml()`. Exceptions require a comment explaining why the source is trusted."
3. `tests/brain/dashboard-xss.test.mjs` — NEW. Tests that the rendered HTML for a stat with `sub2 = "<img src=x onerror=alert(1)>"` contains the escaped form `&lt;img src=x onerror=alert(1)&gt;` and not the raw tag. Use a jsdom-free approach: extract the template function into a testable export OR load the file content and regex-check that `s.sub2` appears inside `escapeHtml(`.

**Note on test approach:** dashboard.html is not currently module-tested. The simplest honest test is a grep-level assertion: load the file contents, regex-search for `innerHTML =`, and for every match require a nearby `escapeHtml(`. This is a lint-style test, not a runtime test, but it's the minimum viable regression guard. Document this limitation in Notes for Colby.

**Complexity:** 3 files, 1 dashboard + 1 test + 1 convention comment.

**Acceptance criteria:**

- `s.sub2` is `escapeHtml()`-wrapped.
- `renderAgents()` metric interpolations are `escapeHtml()`-wrapped.
- The new test asserts no unwrapped `innerHTML =` string interpolation in dashboard.html.

#### Step 3.4 — gracefulShutdown drain fix (S5)

**Files (2):**

1. `brain/lib/crash-guards.mjs` — rewrite `gracefulShutdown`. Current flow: schedule deadman, register `.then(exitFn)`, then immediately call `exitFn(0)`. New flow: schedule deadman, `await Promise.race([poolEnd(), deadmanPromise])`, then call `exitFn(0)`. Preserve the existing mock-pool test path (the tests pass `exitFn` as a parameter).
2. `tests/brain/hardening.test.mjs` (or `crash-guards.test.mjs` if it exists) — extend. Test: (a) pool drain completes before exitFn is called (assert order via promise resolution), (b) deadman timer firing still forces exit even if pool hangs, (c) existing fast-path tests still pass.

**Complexity:** 2 files, ~20 lines of production change.

**Acceptance criteria:**

- `exitFn` is never called before `poolEnd()` resolves OR the deadman fires.
- Test asserts ordering via a spy or sequence counter.

#### Step 3.5 — LLM response null guards (S10)

**Files (3):**

1. `brain/lib/conflict.mjs` — line 60. Replace `data.choices[0].message.content` with a guarded helper call: `assertLlmContent(data, 'conflict')`. Throw a named error class if missing.
2. `brain/lib/consolidation.mjs` — line 169. Same call: `assertLlmContent(data, 'consolidation')`.
3. `brain/lib/llm-response.mjs` — NEW. Exports `assertLlmContent(data, context)`. Returns `data.choices[0].message.content` if present, throws `new Error(\`LLM response malformed (\${context}): \${JSON.stringify(data).slice(0, 200)}\`)` otherwise. Importable by both conflict.mjs and consolidation.mjs.

**Roz test:** `tests/brain/llm-response.test.mjs` — NEW. Tests `assertLlmContent` with: (a) happy path, (b) missing `choices`, (c) empty `choices` array, (d) missing `message.content`, (e) content is `null`, (f) data is `null`.

**Complexity:** 4 files (3 + 1 test), surgical.

**Acceptance criteria:**

- No `.choices[0].message.content` access exists in `brain/lib/` outside `llm-response.mjs`.
- Malformed responses produce a named error with a truncated dump.
- Both call sites import the helper.

---

### Wave 4 (outlined — full ADR later)

**Theme:** Remaining brain hardening + ADR-0032 Steps 2–3 (hydrate-telemetry rewire + Eva hard-pause).

**Findings:** S16 (static path traversal), S17 (CDN SRI), S24 (consolidation initial run), S23 (health endpoint recon), S21 (SQL placeholders), S14 (LLM model config), ADR-0032 Steps 2–3, M14 (integration tests against real Postgres), S13 (hydrate fire-and-forget polling spec), S4 (Ellis hook vs. ADR-0022 R20 resolution — needs Cal decision before this wave).

**Why later:** These are mostly independent, lower-severity, and require either a separate ADR authoring cycle (S4) or an integration test infrastructure investment (M14) that doesn't fit Wave 3's correctness theme.

### Wave 5 (outlined — full ADR later)

**Theme:** Documentation sweep, owned by Agatha.

**Findings:** S1 (triple-source assembly doc), S11 (REST auth doc), S19 (hook-addition procedure), S20 (Gauntlet in user guide), S25 (REST endpoint completeness), M11 (migrations table 001–007 → 001–009 post Wave 2), M15 (ADR index 13→30), S3 (ADR-0001 dead link resolution — decide move vs. update references).

**Why later:** Agatha's work block is cohesive and should not be fragmented across code waves. After Wave 2 changes the migration runner, the migration doc (M11) benefits from being written against the final shape.

### Wave 6 (outlined — full ADR later)

**Theme:** Dashboard a11y + Cursor parity + product spec additions.

**Findings:** S2 (modal semantics), S18 (agent card keyboard), M12 (dashboard loading states), S8 (Cursor hook parity gap), S6 (Handoff Brief protocol), S7 (context-brief dual-write gate), S9 (SKILL.md dashboard install path — fix early if trivially urgent, else here), S15 (Roz-first tests for remaining unimplemented ADRs).

**Why later:** Sable a11y work is cohesive; Robert spec additions (S6, S7) want Cal review first; Cursor parity (S8) needs product alignment on scope. None of these block Waves 1–3.

---

## Test Specification

**Wave 1 test spec (Roz authors before Colby builds):**

| ID | Category | Description |
|---|---|---|
| T-0034-001 | Contract boundary | `SOURCE_AGENTS` in `config.mjs` includes every `source_agent` value emitted by the brain-extractor mapping table (`source/shared/agents/brain-extractor.md:43-53`). Fail shows which agent is missing. |
| T-0034-002 | Contract boundary | `SOURCE_PHASES` in `config.mjs` includes `product`, `ux`, `commit`, plus every phase already in the mapping table. |
| T-0034-003R | Cross-source parity | `config.mjs` contains a comment within 5 lines of each of `eva`, `poirot`, and `distillator` in the `SOURCE_AGENTS` array that matches the pattern `# non-extracted` (case-insensitive). Test: load `brain/lib/config.mjs` as a string; for each of the three agent names, assert that the surrounding 10 lines contain the marker. Fail message identifies which agent is missing the comment. |
| T-0034-004 | Schema parity | `schema.sql` `CREATE TYPE source_agent AS ENUM (...)` contains the same set as `SOURCE_AGENTS`. Test reads both files and diffs. |
| T-0034-005 | Schema parity | Same check for `source_phase`. |
| T-0034-006 | Migration idempotency | Migration 008 against a mock pg pool: running twice against the same database produces only one round of ALTER TYPE calls (the second run detects labels exist and skips). |
| T-0034-007 | Migration isolation | Migration 008 failing does not prevent the rest of the boot flow from running (try/catch wrap observed). |
| T-0034-008 | Rest-api wiring (M9) | `handleTelemetryAgents` constructs its `IN` clause from `SOURCE_AGENTS`, not a hardcoded literal. Test greps `rest-api.mjs` for the literal `IN ('eva','colby'` and asserts zero matches. |
| T-0034-009 | Rest-api wiring (M9) | `handleTelemetryAgents` query execution includes `sentinel`, `darwin`, `deps` (newly added to SOURCE_AGENTS) as valid filter values. |
| T-0034-010 | Zod validation | A mock `agent_capture({source_agent: 'sentinel', source_phase: 'build'})` passes Zod validation (proves the enum extension took). |
| T-0034-011 | Zod validation | `agent_capture({source_agent: 'robert-spec', source_phase: 'product'})` passes. |
| T-0034-012 | Zod validation | `agent_capture({source_agent: 'nonsense'})` still fails Zod (guard against over-opening). |
| T-0034-013 | Failure messaging | A Zod failure logs a clear error identifying WHICH field is invalid, not a silent drop. Regression guard. |
| T-0034-014 | ADR-0032 helper happy path | `pipeline-state-path.sh` with `CLAUDE_PROJECT_DIR` set produces `~/.atelier/pipeline/{slug}/{8-char-hash}/`. |
| T-0034-015 | ADR-0032 helper fallback | `pipeline-state-path.sh` with all env vars unset AND `pwd` failing falls back to `docs/pipeline/`. Must exit 0 in the fallback path. |
| T-0034-016 | ADR-0032 helper isolation | Two different absolute paths hash to different 8-char prefixes (collision probability ~0 for two paths). |
| T-0034-017 | ADR-0032 helper error-patterns | `error_patterns_path()` returns the in-repo `docs/pipeline/error-patterns.md` regardless of session state dir. |
| T-0034-018 | session-boot integration | `session-boot.sh` under a mocked `CLAUDE_PROJECT_DIR=/tmp/worktreeA` writes state to `~/.atelier/pipeline/{slug}/{hashA}/pipeline-state.md`. |
| T-0034-019 | session-boot integration | Two mocked worktrees produce disjoint state directories AND a write to one never appears in the other. |
| T-0034-020 | post-compact integration | `post-compact-reinject.sh` reads from the same directory `session-boot.sh` wrote to (same helper, same CLAUDE_PROJECT_DIR). |

**Wave 2 test spec (Roz authors before Colby builds):**

| ID | Category | Description |
|---|---|---|
| T-0034-021 | hook-lib.sh parser | `hook_lib_pipeline_status_field phase` on stdin `{"PIPELINE_STATUS": {"phase": "build", "feature": "with } brace"}}` returns `build` not a truncated value. |
| T-0034-022 | hook-lib.sh json_escape | `hook_lib_json_escape` of a string containing `\n`, `"`, `\`, tab, and unicode produces a JSON-valid escaped form (S22 regression). |
| T-0034-023 | hook-lib.sh agent_type | `hook_lib_get_agent_type` on stdin `{"tool_input": {"subagent_type": "roz"}}` returns `roz`. |
| T-0034-024 | hook-lib.sh agent_type | `hook_lib_get_agent_type` on stdin `{"agent_type": "colby"}` returns `colby`. |
| T-0034-025 | hook-lib.sh agent_type | Prefers top-level `agent_type` over `tool_input.subagent_type` when both present. |
| T-0034-026 | Library adoption | `grep -rn 'grep -o .PIPELINE_STATUS' source/claude/hooks/` returns zero matches (the parser is now only in the library). |
| T-0034-027 | Library adoption | `grep -rn "jq -r '\.agent_type // empty'" source/claude/hooks/` returns zero matches. |
| T-0034-028 | Agatha hook | `enforce-agatha-paths.sh` blocks a Write to `source/claude/hooks/new-hook.sh`. |
| T-0034-029 | Agatha hook | `enforce-agatha-paths.sh` allows a Write to `docs/guide/user-guide.md`. |
| T-0034-030 | Agatha hook | conftest DEFAULT_CONFIG mirrors `source/claude/hooks/enforcement-config.json` `agatha_allowed_paths`. |
| T-0034-031–033 | Product hook | Same three tests for `enforce-product-paths.sh`. |
| T-0034-034–036 | UX hook | Same three tests for `enforce-ux-paths.sh`. |
| T-0034-037–039 | Ellis hook | Same three tests for `enforce-ellis-paths.sh`. Note: ellis test documents today's behavior, not the post-S4-resolution behavior. |
| T-0034-040 | Migration runner | Against a mock pool with zero rows in schema_migrations, the runner applies 001–009 in order and inserts 9 rows. |
| T-0034-041 | Migration runner | Against a mock pool with schema_migrations containing rows for 001–005, the runner applies 006–009 only. |
| T-0034-042 | Migration runner | A migration file with invalid SQL logs an error and continues to the next migration (fail-soft preserved). |
| T-0034-043 | Migration runner | Migration 009 (the backfill) populates schema_migrations from existing idempotency checks on a database at pre-009 state. |
| T-0034-044 | Migration runner size | `runMigrations()` function body is ≤50 lines (regression guard on refactor). |
| T-0034-045 | SKILL.md dead stub | SKILL.md Step 1 session-hydrate.sh removal instructions still present and correct. |

**Wave 3 test spec (Roz authors before Colby builds):**

| ID | Category | Description |
|---|---|---|
| T-0034-046 | Red test triage | Full test suite (`pytest tests/ && node --test ../tests/brain/*.test.mjs`) exits 0 with zero failures. |
| T-0034-047 | Red test triage | T-0024-048 does not exist (deleted). |
| T-0034-048 | Red test triage | T-0024-050 asserts `== 3` and docstring references ADR-0034. |
| T-0034-049 | CORS removal | `grep "Access-Control-Allow-Origin" brain/lib/rest-api.mjs` returns zero matches. |
| T-0034-050 | CORS behavior | Each of the 4 formerly-wildcarded handlers, when called, returns the server-level CORS origin (`http://localhost:${PORT}`). |
| T-0034-051 | XSS guard | Dashboard rendering of `s.sub2 = "<img src=x>"` produces escaped output in the resulting HTML string. |
| T-0034-052 | XSS guard | `grep -n 'innerHTML =' brain/ui/dashboard.html` matches are ALL adjacent to `escapeHtml(` within 200 chars. Lint-style regression guard. |
| T-0034-053 | XSS guard | `renderAgents()` interpolations in dashboard.html are `escapeHtml()`-wrapped. |
| T-0034-054 | gracefulShutdown | `poolEnd()` resolves before `exitFn` is called in a test with mock pool. Assert via sequence counter. |
| T-0034-055 | gracefulShutdown | Deadman timer still fires (and exitFn called) if pool hangs. |
| T-0034-056 | gracefulShutdown | Existing fast-path test still passes. |
| T-0034-057 | LLM null guard | `assertLlmContent({})` throws a named error containing "malformed" and the (truncated) payload. |
| T-0034-058 | LLM null guard | `assertLlmContent({choices: [{message: {content: "ok"}}]})` returns `"ok"`. |
| T-0034-059 | LLM null guard | `assertLlmContent({choices: []})` throws. |
| T-0034-060 | LLM null guard | `grep -rn '\.choices\[0\]\.message\.content' brain/lib/` matches only inside `llm-response.mjs`. |

**Test count:** 60 tests across Waves 1–3. Failure-path count (25) is greater than happy-path count (35 minus setup) — complies with the "failure ≥ happy path" standard for Roz-first specs focused on regression prevention.

---

## UX Coverage

Not applicable to Waves 1–3. Dashboard UX work (M10 XSS fix is a security fix, not a UX surface change; M12 loading states, S2 modal a11y, S18 keyboard access) is deferred to Wave 6 where Sable authors the a11y ADR. M10 in Wave 3 does not alter visible surfaces — it only escapes values that render identically when the input is safe.

---

## Contract Boundaries

| Producer | Contract shape | Consumer | Wave |
|---|---|---|---|
| `brain/lib/config.mjs` `SOURCE_AGENTS` (JS array) | `Array<string>` of 16 canonical agent names | `tools.mjs` Zod validator (line 62), `rest-api.mjs` handleTelemetryAgents (line 340) | Wave 1 |
| `brain/lib/config.mjs` `SOURCE_PHASES` | `Array<string>` of 14 canonical phase names | `tools.mjs` Zod validator, every capture from Eva's hydration, brain-extractor persona | Wave 1 |
| `brain/schema.sql` `source_agent` enum | Postgres enum type | Every INSERT into thoughts; the Zod enum must be a subset-or-equal of this | Wave 1 |
| `brain/migrations/008-*.sql` | SQL DDL emitting `ALTER TYPE ... ADD VALUE IF NOT EXISTS` | `brain/lib/db.mjs` `runMigrations()` | Wave 1 |
| `source/shared/hooks/pipeline-state-path.sh` | Bash function `pipeline_state_dir()` returning absolute path | `session-boot.sh`, `post-compact-reinject.sh`, (future: `hydrate-telemetry.mjs` via env signal in Wave 4) | Wave 1 |
| `source/shared/hooks/hook-lib.sh` | 5 bash functions (pipeline_status_field, get_agent_type, assert_agent_type, json_escape, emit_deny/allow) | ~15 hooks under `source/claude/hooks/` | Wave 2 |
| `brain/schema_migrations` table | PK `version`, `applied_at`, `checksum` columns | `brain/lib/db.mjs` new `runMigrations()` loop | Wave 2 |
| `brain/lib/llm-response.mjs` `assertLlmContent(data, context)` | Function throwing on malformed LLM payload | `brain/lib/conflict.mjs`, `brain/lib/consolidation.mjs` | Wave 3 |

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|---|---|---|---|
| `SOURCE_AGENTS` extended enum | JS array | Zod validator in `tools.mjs:62` | Wave 1 Step 1.1 |
| `SOURCE_AGENTS` extended enum | JS array | SQL `IN` clause in `rest-api.mjs:340` | Wave 1 Step 1.1 (M9 closed in same step — NO orphan producer) |
| `SOURCE_PHASES` extended enum | JS array | Zod validator in `tools.mjs` | Wave 1 Step 1.1 |
| Migration 008 file | SQL | `db.mjs` runMigrations() try/catch block | Wave 1 Step 1.1 |
| `pipeline-state-path.sh` helper | Bash function | `session-boot.sh` (reader + writer) | Wave 1 Step 1.3 (same step — NO orphan) |
| `pipeline-state-path.sh` helper | Bash function | `post-compact-reinject.sh` (reader) | Wave 1 Step 1.3 (same step) |
| SKILL.md SubagentStop condition (9 agents) | JSON hook registration | Installed `.claude/settings.json` (after user re-runs `/pipeline-setup`) | Wave 1 Step 1.2 (consumer = user action, documented in release notes) |
| `hook-lib.sh` | Bash functions | 15+ enforce-* and log-* hooks | Wave 2 Step 2.1 (same step — all consumers updated with the producer) |
| New `enforce-*-paths.sh` tests | pytest files | CI test suite | Wave 2 Step 2.2 (consumer = CI, ratified) |
| `schema_migrations` table | Postgres table | `runMigrations()` new loop | Wave 2 Step 2.3 (same step) |
| `session-hydrate.sh` deletion deadline | Code comment | Future ADR deleting the stub | Wave 2 Step 2.4 (deferred consumer, documented) |
| `llm-response.mjs` helper | JS function | `conflict.mjs`, `consolidation.mjs` | Wave 3 Step 3.5 (same step — NO orphan) |

**Orphan check:** Every producer above has a consumer in the same step or earlier. Zero orphan producers.

## Data Sensitivity

Wave 1–3 changes do not introduce new `public-safe` / `auth-only` distinctions. The Wave 1 rest-api.mjs change (M9) simply removes a hardcoded literal; the endpoint remains auth-gated via the existing `checkAuth` applied to `/api/*`. The Wave 3 CORS removal (M8) does NOT change auth posture — those handlers were and remain auth-gated.

No new `public-safe` methods are introduced. No auth boundaries change.

## Notes for Colby

1. **Wave 1 Step 1.1 is atomic.** Do not open a PR with config.mjs changes but no schema.sql change. The enum drift is exactly the bug we're fixing — introducing new drift during the fix would be Poetic Justice.
2. **Migration 008 ships on the OLD runner.** Do not try to combine Wave 1 and Wave 2's migration runner refactor. Add the 008 block to the existing `runMigrations()` in Wave 1; Wave 2 replaces the whole function later.
3. **Scout before rewiring hooks (Wave 2 Step 2.1).** Run `grep -rn "grep -o 'PIPELINE_STATUS" source/claude/hooks/` to get the actual duplication count. If > 15, split 2.1 into 2.1a (library + top-6 hooks) and 2.1b (rest). Do not exceed a single-session file count.
4. **`error-patterns.md` stays in-repo (ADR-0032 Decision section).** The new helper must expose TWO functions: `session_state_dir()` per-worktree and `error_patterns_path()` in-repo. Do NOT conflate them.
5. **Wave 1 Step 1.2 does NOT edit `.claude/settings.json` directly.** That file is installed by `/pipeline-setup`. Edit only `skills/pipeline-setup/SKILL.md`'s template.
6. **Wave 3 Step 3.3 dashboard test is lint-style.** `brain/ui/dashboard.html` has no existing unit-test harness. The viable regression guard is a file-grep that asserts every `innerHTML =` has a nearby `escapeHtml(`. A full DOM-level test requires jsdom + module extraction and is out of scope for this ADR. Document the limitation in the test file docstring.
7. **Wave 3 Step 3.1 is Roz-first.** Roz investigates each of the 5 red tests BEFORE Colby touches any production code. If a red test reveals a production bug, Roz creates a finding and this wave re-scopes to include the fix as a new step. Do not silently fix production code while closing red tests.
8. **S4 (Ellis hook vs ADR-0022 R20) is parked.** Wave 2 Step 2.2's `test_enforce_ellis_paths.py` locks today's behavior. Resolution of the contradiction happens in Wave 4 via a new ADR. Do not pre-emptively delete the hook; do not pre-emptively amend ADR-0022.
9. **M2 is explicitly out of scope.** If during Wave 1 work you notice the unauthenticated MCP endpoint, do not fix it — record a note in your handoff and continue. User has accepted the risk.
10. **Proven brain patterns in scope for this wave:** mock-pool substring matching (tests/brain/helpers/mock-pool.mjs), existing test-per-tool layout in tests/brain/*.test.mjs, pytest conftest composition in tests/hooks/conftest.py. Reuse; do not reinvent.

---

## DoD: Verification

| Gate | Wave 1 | Wave 2 | Wave 3 |
|---|---|---|---|
| `pytest tests/` exits 0 | Pass | Pass | **Green suite restored** |
| `node --test tests/brain/*.test.mjs` exits 0 | Pass | Pass | Pass |
| Zero new `grep` matches of hardcoded literal | Pass (M9 literal gone) | Pass (duplicated parsers gone) | Pass (CORS wildcards gone, `.choices[0].message.content` outside helper gone) |
| Schema.sql enum matches config.mjs enum | **Pass** | Pass (stable) | Pass |
| Migration 008/009 applies idempotently against mock pool | **Pass** | Pass (new runner) | Pass |
| Two mock worktrees produce disjoint state dirs | **Pass** | Pass | Pass |
| Four missing hook tests exist and pass | Pre-existing gap | **Pass** | Pass |
| `runMigrations()` ≤ 50 lines | N/A | **Pass** | Pass |
| `s.sub2` is escapeHtml-wrapped | N/A | N/A | **Pass** |
| gracefulShutdown drains pool before exitFn | N/A | N/A | **Pass** |
| LLM response access is guarded at every call site | N/A | N/A | **Pass** |
| No silent drops (any Zod failure logs loudly) | **Pass** | Pass | Pass |
| ADR-0032 Step 1 implemented (helper + session-boot + post-compact) | **Pass** | Pass | Pass |

**Silent-drop guarantee:** After Wave 1, any `agent_capture` call from any of the 16 target agents that fails Zod validation produces a loud error log referencing the specific field and expected values. Wave 1 Step 1.1 test T-0034-013 locks this behavior.

---

*Test spec review: pending Roz approval.*

---

## Roz Test Spec Review — 2026-04-11

**Verdict: APPROVED WITH ADDITIONS**

**Wave 1 is clear for Colby after the two corrections below are applied.**

### Corrections Required Before Colby Starts

**BLOCKER-1 — SOURCE_AGENTS count arithmetic error (Step 1.1 Acceptance Criteria)**

The acceptance criterion reads: "16 agents in the brain-extractor mapping table plus eva, poirot, distillator (19 total)."

Actual counts from live files:
- `source/shared/agents/brain-extractor.md` mapping table (lines 43–53): **9 agents** (cal, colby, roz, agatha, robert, robert-spec, sable, sable-ux, ellis).
- New agents being added: **6** (sentinel, darwin, deps, brain-extractor, robert-spec, sable-ux — but robert-spec and sable-ux are already in the mapping table; the net new are sentinel, darwin, deps, brain-extractor).
- Existing `SOURCE_AGENTS` (config.mjs): **10** (eva, cal, robert, sable, colby, roz, poirot, agatha, distillator, ellis).
- After extension: 10 + 6 = **16 total**.

**Corrected acceptance criterion:** `SOURCE_AGENTS` has exactly 16 entries: the 10 existing plus sentinel, darwin, deps, brain-extractor, robert-spec, sable-ux. T-0034-061 (added by Roz) locks the exact count. The "Silent-drop guarantee" note at the bottom of the DoD (which also says "19 target agents") must be updated to read "16".

**BLOCKER-2 — T-0034-003 is not mechanically testable**

T-0034-003 says: "Every non-extractor core agent in SOURCE_AGENTS (eva, poirot, distillator) is explicitly marked in a comment as 'not extracted' so future refactors don't remove them thinking they're orphans."

No file is specified, no comment format is specified, and no assertion mechanism is described. This test cannot be written by Colby and cannot be verified by Roz.

**Replacement for T-0034-003:** Roz replaces this test with T-0034-003R:

| ID | Category | Description |
|---|---|---|
| T-0034-003R | Contract boundary | `config.mjs` contains a comment within 5 lines of each of `eva`, `poirot`, and `distillator` in the `SOURCE_AGENTS` array that matches the pattern `# non-extracted` (case-insensitive). Test: load `brain/lib/config.mjs` as a string; for each of the three agent names, assert that the surrounding 10 lines contain the marker. Fail message identifies which agent is missing the comment. |

**FIX-REQUIRED — T-0034-019 mechanism under-specified**

T-0034-019 says "a write to one never appears in the other" without specifying the verification mechanism.

**Addition to T-0034-019:** The test creates a zero-byte file `roz-sentinel-a.txt` inside the resolved directory for worktreeA. It then resolves the directory for worktreeB (different absolute path). It asserts `os.path.exists(dirB / 'roz-sentinel-a.txt')` is False. The sentinel file is cleaned up in the test's teardown.

### Added Tests (T-0034-061 through T-0034-064)

These tests are authored by Roz and must be placed in the target test files before Colby begins Wave 1 implementation. Tests are expected to FAIL before Colby builds (correct Roz-first behavior).

| ID | Category | Description | File |
|---|---|---|---|
| T-0034-061 | Contract boundary | `SOURCE_AGENTS` array in `config.mjs` has exactly 16 entries. Fail message lists actual count and all 16 expected names: `['agatha','brain-extractor','cal','colby','darwin','deps','distillator','ellis','eva','poirot','robert','robert-spec','roz','sable','sable-ux','sentinel']` (sorted). Regression guard against silent append or deletion. | `tests/brain/enum-boundary.test.mjs` |
| T-0034-062 | Template parity | `skills/pipeline-setup/SKILL.md` SubagentStop brain-extractor `if` condition contains all 9 brain-extractor target agent names as literal strings: cal, colby, roz, agatha, robert, robert-spec, sable, sable-ux, ellis. Grep the SKILL.md text for the settings.json template block (block containing both "SubagentStop" and '"hooks"') and assert each of the 9 strings appears in the `if` condition value. Locks the template state that Step 1.2 verifies. | `tests/hooks/test_pipeline_setup_skill.py` |
| T-0034-063 | Pre-condition gate | `brain/migrations/008-extend-agent-and-phase-enums.sql` exists on disk AND its content contains the string `ADD VALUE IF NOT EXISTS`. This test is expected to FAIL before Colby builds Step 1.1 (file does not exist yet). Without this gate, db.mjs could register a migration 008 block referencing the file while the file is absent — which silently skips the migration per the `existsSync` check pattern in migrations 001-006. | `tests/brain/enum-boundary.test.mjs` |
| T-0034-064 | ADR-0032 helper API contract | Sourcing `pipeline-state-path.sh` exposes TWO callable functions: `session_state_dir` (returns a path under `~/.atelier/pipeline/`) and `error_patterns_path` (returns a path containing `docs/pipeline/error-patterns.md`). The test calls each function by its distinct exported name and verifies: (a) `session_state_dir` output does NOT contain `docs/pipeline`; (b) `error_patterns_path` output DOES contain `docs/pipeline/error-patterns.md`. Locks the dual-function API specified in ADR-0034 Notes for Colby item 4. | `tests/hooks/test_pipeline_state_path.py` |

### Coverage Gaps That Remain (Non-Blocking)

These are known gaps that do not block Wave 1 but should be noted for future coverage improvement:

1. **Wave 2 — `hook_lib_get_agent_type` missing-key behavior:** T-0034-023 through T-0034-025 cover the two input forms and the priority order but there is no test asserting what happens when BOTH `agent_type` and `tool_input.subagent_type` are absent. Expected: empty output / empty string. This is a minor edge case; not a blocker.

2. **Wave 1 — Zod validation failure mode for source_phase:** T-0034-011 covers `robert-spec` with `source_phase: 'product'` (happy path). There is no test asserting `agent_capture({source_agent: 'sentinel', source_phase: 'nonsense-phase'})` fails validation. The `source_agent: 'nonsense'` case is covered by T-0034-012 but the analogous phase rejection is not. Low risk since Zod applies both enums uniformly, but a future regression would be silent.

3. **Wave 1 — Migration 008 file content validation beyond `ADD VALUE IF NOT EXISTS`:** T-0034-063 (added) gates on file existence and the idempotency keyword but does not assert the file includes all 9 new enum values by name. This is by design — asserting specific SQL content in a test creates coupling. The T-0034-001 / T-0034-002 / T-0034-004 / T-0034-005 cross-validation approach is the correct mechanism.

---

*Roz Test Spec Review completed: 2026-04-11. Wave 1 clear for Colby pending ADR corrections above.*
