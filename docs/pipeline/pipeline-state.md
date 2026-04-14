# Pipeline State

<!-- PIPELINE_STATUS: {"phase": "review", "sizing": "small", "roz_qa": "PASS", "telemetry_captured": true, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": true, "robert_reviewed": false, "brain_available": true, "stop_reason": null} -->

## Session Recovery — READ THIS FIRST

Three independent ADRs are launching in parallel. All 3 Cal invocations go out
simultaneously in a single message. Do NOT sequence them — they are designed to
run concurrently. After all 3 Cal ADRs are written, Colby+Roz for Wave 4 and
Agatha for Wave 5 also run in parallel. Wave 6 Cursor parity gates on Wave 4
completing first; all other Wave 6 work is independent.

## Wave Plan

### ADR-0035 — Wave 4: Remaining Brain Hardening + ADR-0032 Steps 2–3
**Theme:** Brain code correctness continuation.
**Owner:** Cal → Colby → Roz
**Files touched:**
- `brain/scripts/hydrate-telemetry.mjs` — rewire to use `session_state_dir()` helper
  (ADR-0032 Step 2: stop hardcoding `docs/pipeline/`, read from env signal set by
  `pipeline-state-path.sh`)
- `source/shared/hooks/session-boot.sh` — Eva hard-pause behavior on state isolation
  failure (ADR-0032 Step 3)
- `source/claude/hooks/enforce-ellis-paths.sh` — resolve contradiction with ADR-0022
  Rule 20 (S4: currently blocked, needs its own ADR decision)
- `docs/architecture/ADR-0035-*.md` — Cal writes this ADR

**Why these were deferred from Wave 3:** hydrate-telemetry.mjs is 1029 lines and
needs its own focused Colby session. S4 requires a new architectural decision, not
just a fix.

**Key constraint:** Do NOT touch `brain/lib/` files — those were Wave 3 territory
and are now correct. Scope is strictly hydrate-telemetry.mjs + session-boot ADR-0032
Steps 2–3.

---

### ADR-0036 — Wave 5: Documentation Sweep (Agatha-led, no Colby)
**Theme:** Close the documentation gap — 17 undocumented architectural decisions
+ migration runner prose + behavioral coverage.
**Owner:** Cal (retroactive ADR writing) → Agatha (prose docs)
**No Colby invocation — pure documentation wave.**

**Specific deliverables from the gauntlet register (M11, M15):**
- M11: Migration runner documentation — document the new generic file-loop runner
  (`brain/lib/db.mjs` `runMigrations()`), `schema_migrations` table, idempotency
  guarantees. Write to `docs/guide/technical-reference.md` (Agatha).
- M15: ADR index — Cal writes retrospective ADRs for the 17 undocumented
  architectural decisions identified in the gauntlet. These live in
  `docs/architecture/`. Cal should identify them by reading the codebase and
  existing ADRs to find decisions made in code with no ADR.
- Behavioral coverage: any significant areas where code exists but no prose
  explanation does. Agatha identifies gaps and writes.

**Key constraint:** No source code changes. All output is `docs/` only.

---

### ADR-0037 — Wave 6: Dashboard A11y + Cursor Parity + Product Spec Additions
**Theme:** UX surface hardening and spec completeness.
**Owner:** Sable (a11y spec) → Colby → Roz (for a11y); Cal (ADR-0037) → Colby
(Cursor parity, spec additions)

**Workstreams:**
1. **Dashboard a11y** (independent of Wave 4):
   - M12: Loading states in `brain/ui/dashboard.html` — skeleton/spinner for
     async data fetching
   - S2: Modal accessibility — ARIA roles, focus trap, keyboard dismiss
   - S18: Keyboard navigation — all interactive elements reachable via Tab/Enter

2. **Product spec additions** (independent):
   - Formalise specs for areas Robert flagged as "code exists, no spec" during
     prior gauntlet review. Robert-spec writes to `docs/product/`.

3. **Cursor parity** (GATES on Wave 4 completing first):
   - Mirror any `session-boot.sh` changes from Wave 4 to
     `source/cursor/hooks/session-boot.sh` and `.cursor-plugin/`.
   - DO NOT start this workstream until ADR-0035 (Wave 4) Ellis commit is done.

---

## Agent Receipts

### Wave 4 (ADR-0035)
- Cal: ADR at docs/architecture/ADR-0035-wave4-consumer-wiring-and-s4-resolution.md, 3 steps, 24 tests
- Roz pre-build: DONE — 24 tests (tests/hooks/test_adr0035_consumer_wiring.py ×14, tests/brain/hydrate-telemetry-statedir.test.mjs ×8, tests/hooks/test_enforce_eva_paths.py +2). 10 FAIL expected pre-build, 14 PASS.
- Colby Steps 1-3: scouts running (a5cced39f71000339, a78c160fd7f651273, a8b6abef2caa78fd7)

### Wave 5 (ADR-0036)
- Cal: ADR at docs/architecture/ADR-0036-wave5-documentation-sweep.md, 8 steps, 30 tests. Step 6 has 2-line source fix (not pure docs).
- Colby Step 6: DONE, 2 files changed (brain/server.mjs:9, brain/schema.sql:2), dead link fix
- Roz Step 6 scoped: PASS, 0 blockers
- Agatha Steps 1-5, 7-8: PENDING (blocked by build phase; runs after W4+W6 code builds complete and phase=review)

### Wave 6 (ADR-0037)
- Cal: ADR at docs/architecture/ADR-0037-wave6-dashboard-a11y-cursor-parity-specs.md, 7 steps (A1-A3, B1, C1), 41 tests. Workstream C [REQUIRES ADR-0035].
- Robert-spec B1: DONE, 5 specs written (docs/product/observation-masking.md, token-budget-estimate-gate.md, named-stop-reason-taxonomy.md, agent-discovery.md, team-collaboration-enhancements-addendum.md)
- Roz pre-build: DONE, tests/test_adr0037_wave6.py written, 35 tests
- Robert-spec B1 AC fix: DONE (observation-masking.md AC-17 + token-budget-estimate-gate.md AC-18 updated)
- Colby A1-A3: DONE, brain/ui/dashboard.html (modal ARIA+focus trap, agent card keyboard nav, loading skeletons), 35/35 tests PASS
- Roz W6 QA sweep: PASS (41/41 tests, T-0037-036 to T-0037-041 added and passing)
- Colby W6-C: DONE — source/cursor/hooks/session-boot.sh NEW, hooks.json UPDATED
- Roz W6-C unit-qa: PASS (T-0037-036 to T-0037-041)
- Agatha W5 Steps 1-5, 7-8: DONE — technical-reference.md, user-guide.md, docs/architecture/README.md
- Robert review W6-B1: DONE — 14 PASS, 3 DRIFT accepted (heading names; tests all pass)
- Robert-spec DRIFT fix: DONE — named-stop-reason-taxonomy.md + agent-discovery.md Personas heading
- Roz wave-sweep: PASS — 1500/1501 pytest, 193/194 node (2 pre-existing EACCES, not regressions)
- Poirot W6: PASS (a1863e619fd12ab7c)

## Parallel Launch Protocol (next session)

Eva reads this file at session start and executes the following:

**Step 1 — Launch all 3 Cal invocations simultaneously (single message, 3 Agent calls):**
```
Cal 1: Author ADR-0035 (Wave 4 — brain hardening + ADR-0032 Steps 2–3)
Cal 2: Author ADR-0036 (Wave 5 — documentation sweep, retroactive ADRs)
Cal 3: Author ADR-0037 (Wave 6 — dashboard a11y + Cursor parity + spec additions)
```
All 3 are background agents. Wait for all 3 to complete before Step 2.

**Step 2 — After all 3 ADRs written:**
- Wave 4: Roz test authoring → Colby build → Roz QA → Poirot → Ellis
- Wave 5: Agatha docs (no Colby) → Robert-subagent verifies → Ellis
- Wave 6 a11y + specs: Colby → Roz → Poirot → Ellis
- Wave 6 Cursor parity: START ONLY AFTER Wave 4 Ellis commit

**Step 3 — Final:**
- Robert reviews Wave 4 (if spec exists) and Wave 6
- T3 telemetry capture per ADR
- Ellis final push per ADR
- Version bump after all 3 ship (3.29.0)

---

## Dependency Map

```
Cal-0035 ──→ Roz (test spec) ──→ Colby (build) ──→ Roz QA ──→ Ellis ──→ Wave 6 Cursor parity
                                                                    ↑
Cal-0036 ──────────────────────────────────────→ Agatha (docs only) ──→ Ellis (independent)

Cal-0037 ──→ Colby (a11y) ──→ Roz QA ──→ Ellis (independent of W4 except Cursor parity step)
         └──→ Robert-spec (product specs) ──→ Ellis
```

---

## Prior Pipeline (closed)
**Feature:** feat/brain-setup-auto-fix — redesign brain-setup flow: auto-fix when configured, ask to add when not
**Stop Reason:** completed_clean
**Closed:** 2026-04-13
**Release:** v3.30.7 (commits 807189b, bb8d24e)

## Prior Pipeline (closed)
**Feature:** ADR-0035 + ADR-0036 + ADR-0037 — Waves 4, 5, 6 (parallel launch)
**Stop Reason:** completed_clean
**Closed:** 2026-04-12
**Release:** v3.29.0 (commits 36889e5, 18bbf58, 4955d09)

**Feature:** ADR-0034 Gauntlet remediation — brain correctness fixes
**Stop Reason:** completed_clean
**Closed:** 2026-04-12
**Release:** v3.28.0 (commit 6e50c0b)
<!-- COMPACTION: 2026-04-12T12:50:17Z -->
<!-- COMPACTION: 2026-04-12T13:42:43Z -->
<!-- COMPACTION: 2026-04-12T14:20:40Z -->
<!-- COMPACTION: 2026-04-12T14:58:48Z -->
<!-- COMPACTION: 2026-04-12T22:15:05Z -->
<!-- COMPACTION: 2026-04-13T19:55:35Z -->
<!-- COMPACTION: 2026-04-13T21:14:43Z -->
<!-- COMPACTION: 2026-04-13T21:53:05Z -->
<!-- COMPACTION: 2026-04-14T03:16:55Z -->
