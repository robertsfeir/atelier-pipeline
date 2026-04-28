# Pipeline State

<!-- PIPELINE_STATUS: {"phase": "idle", "sizing": null, "qa_status": null, "telemetry_captured": true, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": false, "robert_reviewed": false, "brain_available": true, "worktree_path": null, "session_id": "current", "branch_name": null, "stop_reason": "completed_clean"} -->

## Active Pipeline
**Feature:** ADR-0053 — Mechanical Brain Capture via Three-Hook Gate
**Phase:** idle — ADR accepted, awaiting Colby build in fresh session
**Sizing:** Small
**Stop Reason:** completed_clean (architecture phase done; session closed intentionally for fresh context)

### Scope (Colby's build — next session)

Per ADR-0053 (`docs/architecture/ADR-0053-mechanical-brain-capture-gate.md`):

1. **Remove** `type: agent` brain-extractor entry from `.claude/settings.json` SubagentStop block
2. **Remove** `source/claude/agents/brain-extractor.md` and `source/cursor/agents/brain-extractor.md`
3. **New** `source/claude/hooks/enforce-brain-capture-pending.sh` — SubagentStop command hook; writes `docs/pipeline/.pending-brain-capture.json` for 8-agent allowlist; exits 0 always (no blocking)
4. **New** `source/claude/hooks/enforce-brain-capture-gate.sh` — PreToolUse on Agent; blocks if pending file exists and `.brain-unavailable` absent; main-thread only; fail-open on missing config
5. **New** `source/claude/hooks/clear-brain-capture-pending.sh` — PostToolUse on `agent_capture` MCP tool; deletes pending file idempotently; logs to telemetry
6. **Update** `source/claude/hooks/enforcement-config.json` or settings.json source templates to register all three hooks
7. **Update** `source/shared/references/pipeline-orchestration.md` — add escape hatch protocol: when `atelier_stats` returns unreachable, Eva touches `docs/pipeline/.brain-unavailable`; gate honors that sentinel; cleared on next successful brain ping
8. **Tests** — pytest covering: (a) PreToolUse blocks Agent when pending file exists, (b) PostToolUse on agent_capture deletes pending file, (c) `.brain-unavailable` sentinel suppresses block
9. **Sync** — run pipeline-setup to sync installed `.claude/` copies from source

**Allowlist** (same as old type:agent if: clause): `sarah`, `colby`, `agatha`, `robert`, `robert-spec`, `sable`, `sable-ux`, `ellis`

**Pending file structure:**
```json
{"agent_type": "colby", "transcript_path": "/path/to/transcript", "timestamp": "2026-04-28T15:44:00Z"}
```

**LOC estimate (Sarah):** ~280 lines added, ~80 lines removed (brain-extractor files).

---

## Prior Pipeline (closed)
**Feature:** Issue #45 item 5 — provenance surfacing on prefetched brain thoughts
**Phase:** idle
**Sizing:** Micro
**Stop Reason:** completed_clean
**Commit:** c27594b (chore: v4.0.16)
**Release:** v4.0.16

---

## Prior Pipeline (closed)
**Feature:** Issue #45 steps 1-2 — brain-context trust framing (agent-preamble) + scope enforcement (prefetch hook)
**Phase:** idle
**Sizing:** Small
**Stop Reason:** completed_clean
**Session:** 11e70d16
**Commits:** e3e2586 (feat) · fd586df (chore: v4.0.14)
**Release:** v4.0.14

---

## Prior Pipeline (closed)
**Feature:** Issue #44 — Colby Stop verification hook (typecheck + auto-format)
**Phase:** idle
**Sizing:** Small
**Stop Reason:** completed_clean
**Session:** 57bc01ce
**Commit:** 652fcce
**Release:** (no version bump — internal tooling)

---

### Parked (brain-hydrate items 3 & 5)
Deferred: brain-hydrate skill ToolSearch pre-load (item 3) + scope format docs in tools.mjs (item 5). Resume in a separate session.

---

## Prior Pipeline (closed)
**Feature:** Issue #31 slice 4 + Sherlock subagent introduction
**Phase:** idle
**Stop Reason:** completed_with_warnings
**Sizing:** Medium
**Opened:** 2026-04-21
**Closed:** 2026-04-21
**Release:** v3.41.0
**Commits:** e042300 (feat: ADR-0045 Sherlock + slice-4 amputation) + 879d8e8 (chore: bump 3.41.0)
**Issue:** https://github.com/robertsfeir/atelier-pipeline/issues/31 (slice 4 of 4 closed)

**Scope delivered:** ADR-0045 — new Sherlock subagent (replaces Roz as user-reported-bug investigator, fresh general-purpose isolation, 6-question intake from Eva); amputated 5 slash commands (/debug, /darwin, /deps, /create-agent, /telemetry-hydrate), 2 agent personas (darwin, deps), 3 skills (dashboard, pipeline-overview, load-design — fold into /pipeline-setup Step 1a), 2 pipeline-config.json flags (darwin_enabled, deps_agent_enabled); rewrote Mandatory Gate 4 (Roz → Sherlock for user bugs); updated auto-routing matrix, per-agent assignment table, session-boot CORE_AGENTS (15 → 14: -darwin, -deps, +sherlock); deleted 2 test directories (adr-0015-deps, adr-0016-darwin = 158 tests); Category H updates + cascade cleanup across ~12 existing test files; CLAUDE.md agents + commands lines updated.

**Warnings (why completed_with_warnings):**
- **User override of "full suite passes" gate.** Pipeline shipped with ~9 pre-existing env-debt failures (jq_missing × 6, brain-node zod, pytest-meta). Some scope-gap tests (ADR-0040 load-design, ADR-0023 Darwin/Deps presence, dashboard Step 6e/6f, T_0022_154 create_agent, T_0005_066 debug-flow, T_0044_003/038 line/row pins, T_0042_031 cursor mirror, T_0021_041 Roz workflow) were in flight for deletion/update when the user stopped the cascade cleanup and directed "colby solo, ship it" — feature code is correct; test cascade was user-accepted unfinished.
- **Retro-lesson meta-finding.** Roz hit maxTurns 4× in this session. Root cause: current test authoring philosophy prescribes structural-pinning tests (line counts, row counts, exact literals) that grow quadratically with change scope. This is the flagged Roz strategy review.
- **Poirot never finalized.** Launched blind review in background; user stopped both Poirot and Roz #5 when frustrated with the ceremony. No review findings were processed.

**Medium ceremony observed:** 3 Colby invocations (initial build × 2 + cascade cleanup solo), 5 Roz invocations (authoring × 2 + scoped patch × 2 + cascade close attempt), 1 Poirot (killed), Ellis (commit + ff-merge; worktree + branch cleanup by Eva post-push).

**Bypassed gates:** Full suite passes (user override), Agatha docs pass (user focus on ship), Robert-subagent review (no spec for this internal change), Sable-subagent review (no UX doc).

**Spawned/Related GH:** #31 slice 4 closes Issue #31 wholesale.

---


### Roz test-authoring outcome (pre-build, Eva-bridged)
Roz authored 50 new T_0045 tests in `tests/adr-0045/test_adr_0045.py` and applied 21 Category H updates across 8 existing test files. Two consecutive Roz invocations stalled at maxTurns before writing last-qa-report.md; Eva ran pytest diagnostic per lesson d70409af to verify state on disk.

**Pre-build suite state** (full `pytest tests/` minus ignored pre-deletion dirs): 1750 passed / 71 failed.
- 45 new T_0045 tests FAIL as expected (assert-feature-exists against not-yet-built Sherlock + rewrites)
- 17 Category-H cascade fails as expected (tests now reference `ALL_AGENTS_CORE`, `EXPECTED_CORE_AGENTS_14`, updated gate-title list, etc. — Colby's code updates match)
- 9 pre-existing env-debt (jq_missing × 8, brain-node zod, pytest-meta) — unchanged from prior pipelines
- 5 T_0045 tests PASS correctly: T_0045_027 (pipeline-config valid JSON — regression guard), T_0045_030 (preserved-keys regression guard), T_0045_031 (Anti-goal 3 — hook already sarah/roz/colby-only), T_0045_032 (hook has no sherlock string — Anti-goal 3 bypass), T_0045_071 (test-file-structure delta proxy)

Category H target files modified: tests/conftest.py, tests/hooks/test_adr_0022_phase1_overlay.py, tests/adr-0023-reduction/test_reduction_structural.py, tests/hooks/test_session_boot.py, tests/adr-0042/test_adr_0042.py, tests/test_adr0044_instruction_budget_trim.py, tests/dashboard/test_dashboard_integration.py, tests/cursor-port/test_cursor_port.py.

Roz receipt: 50 new tests + 21 Category H updates applied verbatim per Sarah's §Test Specification. Ready for Colby's build wave.


**Sizing:** Medium
**Opened:** 2026-04-21
**Issue:** https://github.com/robertsfeir/atelier-pipeline/issues/31 (slice 4 of 4) + new Sherlock agent

### Configuration
- **Worktree Path:** /Users/Robert_Sfeir/projects/atelier/atelier-pipeline-0265ce7f
- **Session ID:** 0265ce7f
- **Branch:** session/0265ce7f
- **Branching strategy:** trunk-based (session/ prefix despite Medium — user preference; ff-merge at end)
- **Brain:** available

### Scope

**Additions:**
1. NEW subagent: `source/shared/agents/sherlock.md` + platform overlays + installed mirrors. Sherlock replaces Roz as the user-reported-bug investigator. Own context, own workflow, no scouts. Spec reference at `docs/pipeline/sherlock-spec.md` (copy of user-provided markdown at `/Users/Robert_Sfeir/projects/test/sherlock.md`).

**Removals (commands, 5 × up to 3 platform variants):**
- `/debug`, `/darwin`, `/deps`, `/create-agent`, `/telemetry-hydrate`

**Removals (agent personas):**
- `darwin` (source + claude + cursor + installed)
- `deps` (source + claude + cursor + installed)

**Removals (skills):**
- `skills/dashboard/` + Cursor mirror
- `skills/pipeline-overview/` + Cursor mirror
- `skills/load-design/` + Cursor mirror (folded into pipeline-setup)

**Folds:**
- Design-system-path prompt in `skills/pipeline-setup/SKILL.md` (new step; covers what load-design did)

**Structural updates:**
- Mandatory Gate 4 rewrite: Roz → Sherlock for user-reported bugs
- Auto-routing table in `agent-system.md` summary + `routing-detail.md` full matrix: drop debug/darwin/deps triggers; add Sherlock triggers on bug-shaped language
- `pipeline-models.md` Per-Agent Assignment Table: add Sherlock entry; remove darwin + deps
- `pipeline-config.json` schema: drop `darwin_enabled`, `deps_agent_enabled` (and references in pipeline-setup Step 6)
- `CLAUDE.md` pipeline section
- `pipeline-orchestration.md` scout fan-out section: no Sherlock scouts (per user; hook skip needed)

**Test removals/updates:**
- `tests/adr-0015-deps/` — wholesale delete
- `tests/adr-0016-darwin/` — wholesale delete
- `tests/test_adr0041_*.py` — remove darwin/deps tier entries
- Any tests referencing `/debug`, `/darwin`, `/deps` commands — delete or update
- Tests referencing Roz's debug-investigation role (mandatory-gate-4 wording) — update to Sherlock

**Release:**
- Bump to 3.41.0

### Out of scope
- Sherlock scout fan-out (user explicitly: "not right now")
- ADR-0040/0042/0043/0044-era test baselines (unless structural hash breaks from persona changes)

### Flow (Medium)
Sarah (ADR-0045: Sherlock + slice-4 cleanup) → Roz test spec authoring → Colby build (large deletion wave + sherlock add + routing updates) → Roz wave QA + Poirot blind review (parallel) → Robert-subagent skipped (no product spec) → Agatha doc-impact-dependent → Ellis commit + release 3.41.0 + ff-merge.

### Retro risk
- Lesson 002 (don't codify bug) applies to test removals — verify deletions are because feature is gone, not because test was inconvenient
- Slice 2 taught: narrow scope changes create cross-ADR cascades. Slice 4 has lots of wholesale deletes; cascades should be mostly "test referenced removed feature" which is expected
- Eva's routing changes on bug reports are a behavioral change — documenting carefully in ADR is important for future-Eva context

---

## Prior Pipeline (closed)
**Feature:** Issue #31 slice 2 — Instruction-budget trim + release 3.40.0
**Phase:** idle
**Stop Reason:** completed_with_warnings
**Sizing:** Medium
**Opened:** 2026-04-21
**Closed:** 2026-04-21
**Release:** v3.40.0
**Commits:** 12a55ad (feat: ADR-0044 slice 2) + 07e9f6e (chore: bump 3.40.0)
**Issue:** https://github.com/robertsfeir/atelier-pipeline/issues/31 (slice 2 of 4 closed)

**Scope delivered (narrower than issue estimate):**
1. ADR-0044: AUTO-ROUTING matrix moved from `agent-system.md` (286→240 lines) to new JIT ref `routing-detail.md` (65 lines). Install mirrors at `.claude/references/` (byte-identical per ADR §5) + `.cursor-plugin/rules/routing-detail.mdc`. Total always-loaded win: ~46 lines on the Claude side.
2. Mandatory Gates rhetoric collapse — `**Violation class.**` banner declares severity once; per-gate refrain replaced with terse `(default class)` or tighter-class parentheticals. All 12 gates preserved.
3. Scout Fan-out "Explicit spawn requirement" paragraph tightened (6 sentences → 2).
4. Cursor `.mdc` mirrors synced (agent-system.mdc 378→246, pipeline-orchestration.mdc rhetoric collapse).
5. Cross-ADR alignments: ADR-0022 shared-references count 15→16; ADR-0023 T_0023_131 strengthened to count 12 gate headers; `docs/guide/technical-reference.md` user-guide updated to match new rhetoric; `default-persona.md` routes Eva to routing-detail.md for edge cases; `skills/pipeline-setup/SKILL.md` Step 3c manifest extended to install routing-detail.mdc on Cursor projects.
6. 35-function pytest suite (`tests/test_adr0044_instruction_budget_trim.py`), all green.

**Warnings (scope reality):**
- Addendum A1 records scope narrowing: pipeline-orchestration.md line-count reduction ended ~2 lines, not ~42 (rhetoric collapse saved ~7 lines but opener banner added 5; Scout Fan-out paragraph collapse was single-line markdown = 0 line delta).
- `source/shared/references/pipeline-models.md` Per-Agent Assignment Table untouched (ADR-0042 tests pin). Original issue's ~400-line target not fully achieved.
- Cursor SKILL.md manifest-format asymmetry flagged by Colby (post-ship detail; acceptable).
- Poirot's background re-review output was truncated; first surfaced finding (Cursor install-manifest gap) addressed in fix-cycle-6; any additional truncated findings not processed.

**Out of scope (still open for #31):**
- Slice 3: brain-prefetch advisory gate.
- Slice 4: skill prune decision.

**Medium ceremony:** 4 Colby fix-cycles, 3 Roz test passes (author + consolidation + safety-valve + 2 scoped updates), 2 Poirot blind reviews, 2 Sarah invocations (ADR + Addendum A1). Robert-subagent skipped (no product spec for this internal change). Agatha skipped (no doc impact flagged beyond technical-reference.md update already in Colby scope).

**Spawned/Related GH:** #46 (scout-swarm hook gap for pre-build Roz authoring, filed earlier this pipeline) — not fixed here.

---

## Prior Pipeline (closed)
**Feature:** Issue #31 slice 1 — Agent return condensation + release 3.39.0

### Configuration
- **Worktree Path:** /Users/Robert_Sfeir/projects/atelier/atelier-pipeline-1f825cae
- **Session ID:** 1f825cae
- **Branch:** session/1f825cae
- **Branching strategy:** trunk-based
- **Brain:** unavailable

### Scope
1. `source/shared/references/pipeline-orchestration.md` (802 lines, Mandatory Gates 109-250) — collapse rhetoric ("same class of violation" ×8 at lines 127/146/169/202/225/236/610/780); collapse Scout Fan-out section (604-635). Must preserve all 12 gates verbatim (ADR-0023 test).
2. `source/shared/rules/agent-system.md` (286 lines) — move AUTO-ROUTING matrix (lines 113-173) to new JIT ref `routing-detail.md`. Keep 10-line summary inline.
3. `source/shared/references/pipeline-models.md` (143 lines) — move the classifier/per-agent-override verbosity to new JIT ref `model-classifier-detail.md`. Keep tier model + threshold rule inline (ADR-0041 tests pin Tier 1-4 labels).
4. Create `source/shared/references/routing-detail.md` + `source/shared/references/model-classifier-detail.md`; install mirrors at `.claude/references/`.
5. Cursor install paths: scouts confirmed agent-system.md/pipeline-models.md/pipeline-orchestration.md are NOT installed for Cursor — pipeline-internal only. No Cursor work.

### Out of scope
- Slice 3 (brain-prefetch advisory gate)
- Slice 4 (skill prune decision)

### Flow (Medium)
Sarah (ADR-0044 with research brief) → Roz test spec review → Colby build → Roz wave QA + Poirot blind review (parallel) → Robert-subagent skipped (no product spec) → Agatha doc impact (if flagged) → Ellis commit + release 3.40.0 + ff-merge.

### Retro risk
- Tests pin content in all 3 target files (ADR-0023 mandatory gates, ADR-0041 tier labels, ADR-0025 Eva capture count < 3 in pipeline-orchestration.md). Sarah must spec which existing tests get updated and how. Slice 1's F1/F2 cascades taught: narrow scope changes rarely stay narrow.
- Moving to JIT refs: the referencing agent must actually load the ref when it needs the detail. Lose a reference → silent gate-skip. Poirot + Roz wave QA are critical.

---

## Prior Pipeline (closed)
**Feature:** Issue #31 slice 1 — Agent return condensation + release 3.39.0
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Small
**Opened:** 2026-04-20
**Closed:** 2026-04-21
**Release:** v3.39.0
**Commits:** 1686115 (feat: agent return condensation) + cffb86a (chore: bump 3.39.0)
**Issue:** https://github.com/robertsfeir/atelier-pipeline/issues/31 (slice 1 of 4 closed)
**Spawned issue:** https://github.com/robertsfeir/atelier-pipeline/issues/46 (scout-swarm hook gap)

**Scope delivered:**
1. ADR-0043 condenses Sarah/Colby/Roz `<output>` to one-line receipts. New `<preamble id="return-condensation">` in agent-preamble.md mandates summary+path-pointer returns and `file:line` citations.
2. Eva observation-masking Roz receipt row updated to `{N} BLOCKERs, {N} FIX-REQUIREDs` (phantom Suggestions tier dropped).
3. ADR-0043 Addendum declares supersessions — ADR-0040 Colby UI-contract design-system row moves to `<workflow>`; `<slug>` → `{slug}` for ADR-0005 XML scanner compat; "skeleton" keyword retained in Sarah `<output>` body-list for ADR-0023 compat.
4. `skills/pipeline-setup/SKILL.md` Step 6g offers `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` as Claude Code SendMessage prerequisite (GH anthropics/claude-code#42737). Cursor plugin-setup unchanged (flag is Claude Code-specific).
5. 37-case pytest suite `tests/test_adr0043_output_contract.py`, all green. ADR-0015/0018/0023 cross-ADR regressions caused by slice 1 renumbering resolved in fix-cycle-4 (new step moved 6b → 6g).

**Out of scope (still open for #31):**
- Slice 2: instruction-budget trim (~400 always-loaded lines: pipeline-orchestration.md gates, agent-system.md routing matrix, pipeline-models.md classifier).
- Slice 3: brain-prefetch advisory gate (first-per-session marker or SessionStart memo).
- Slice 4: skill prune decision (dashboard, load-design, create-agent).

**Notable findings captured:**
- Poirot surfaced two contract-gap issues (Suggestions tier never defined; `filepath:line` vs `file:line` terminology drift); both resolved in fix-cycle-2.
- `enforce-scout-swarm.sh` forces scout fan-out on Roz pre-build test authoring and Colby re-invocation fix cycles — ceremonial, filed as GH #46. Same bug shape on both agents.
- Agent tool advertises `SendMessage` for subagent resume but the tool is gated behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` (verified against Claude Code 2.1.116 binary). GH anthropics/claude-code#42737 open upstream. Pipeline now offers the flag during install (Step 6g).

**Small ceremony:** Scout fan-out for Sarah skipped (per sizing); scout fan-out for Roz + Colby ran (per hook enforcement). Four Colby fix-cycles (initial build, Addendum re-apply, Poirot fixes + env-var step, step-letter restore + ADR-0023 skeleton keyword). Two Roz test updates (authoring, scoped F1/F2 cascade rewrites). Two Poirot blind reviews.

---

## Prior Pipeline (closed)
**Feature:** Update ADR-0042 Roz structural hash baseline (pre-push fix)
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Micro
**Opened:** 2026-04-20
**Closed:** 2026-04-20
**Commit:** (see commit log)

**Scope:** Test-fixture maintenance. Update two hex strings in `tests/fixtures/adr_0042_baselines.py`:
- `CHANGED_AGENT_STRUCTURAL_HASHES["roz"]["claude"]`: `e46543d4…3f2` → `c4ab9a22…b34`
- `CHANGED_AGENT_STRUCTURAL_HASHES["roz"]["cursor"]`: `3ce2d101…a2b` → `298e317e…17c`

**Rationale:** ADR-0042's T_0042_019[roz] test locks a structural hash over Roz's frontmatter (stripping model:/effort: lines). The Roz maxTurns 15→50 bump landed in commit 1cda942 legitimately changed the hash. Update the baseline to match.

**Why now (before push):** We committed 3.38.0 locally as ff3b645. Pushing would ship a red test to CI. Fix the baseline first so the release commit arrives green.

**Micro skips:** scout fan-out, brain capture T2/T3, budget estimate gate. Roz full suite as safety valve (T_0042_019[roz] flip from red to green is the primary signal).

**Status:** Ellis commit complete. Push pending user confirmation (all four commits together: 1cda942, 8fd1e4f, ff3b645, this commit).

---

## Prior Pipeline (closed)
**Feature:** v3.38.0 release — version bump + CHANGELOG
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Micro
**Opened:** 2026-04-20
**Closed:** 2026-04-20
**Release:** v3.38.0 (see commit log)

**Scope:** Mechanical version bump using the new `scripts/release.sh` utility (dogfood).
- Run `./scripts/release.sh 3.38.0` — updates 5 version files
- Update `CHANGELOG.md` — rename `## [Unreleased]` block heading to `## [3.38.0] - 2026-04-20`
- Commit with `chore(release): bump version to 3.38.0` subject
- Push pending user confirmation (push is blast-radius — user decides)

**Contents of 3.38.0 release (from Unreleased block):** new `scripts/release.sh` utility + tests, marketplace.json sync fix, Roz effort parity fix, Roz maxTurns 15→50 (from prior pipeline 1cda942).

**Micro skips:** scout fan-out, brain capture T2/T3, budget estimate gate. Roz full suite as safety valve.

**Status:** Ellis commit complete. Push pending user confirmation.

---

## Prior Pipeline (closed)
**Feature:** Pre-release cleanup — Roz effort parity + marketplace.json sync + release script
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Small
**Opened:** 2026-04-20
**Closed:** 2026-04-20
**Commit:** (see commit log)

**Scope (3 concerns, 5 files + 1 test + CHANGELOG + pipeline state):**
1. `.claude/agents/roz.md` — `effort: high` → `medium` (match source template and pipeline-models.md Tier 3 base) ✓ landed
2. `.claude-plugin/marketplace.json` — `"version": "3.34.0"` → `"3.37.0"` (end users currently can't install 3.35/3.36/3.37 via Claude marketplace; stale since 3.34.0) ✓ landed
3. `scripts/release.sh` — NEW utility bumping all 5 version files in a single invocation ✓ landed

**Rationale:** Investigation revealed `.claude-plugin/marketplace.json` was missed in every release commit from 3.35.0 onward. The 5 version files drift apart silently. Adding a release script mechanically prevents the class of error; updating marketplace.json to 3.37.0 clears the current lag.

**Progress:**
- Colby build v1: complete
- Roz safety-valve sweep: PASS
- Poirot blind review v1: CONCERNS — 4 FIX-REQUIRED items on release.sh/tests/CHANGELOG
- Colby rework: complete (strict semver regex, 9 parametrized rejection cases, nested-keys pin, CHANGELOG atomicity wording softened)
- Roz scoped re-run: PASS (13/13 tests, all findings resolved, no collateral damage)
- Poirot blind re-review: PASS (CONCERNS log-level only — ship-gate clear)
- Ellis commit: complete

**Out of scope:**
- Local plugin cache pollution at `~/.claude/plugins/cache/atelier-pipeline/atelier-pipeline/{3.36.0,3.37.0}` — local maintenance, not a code change. User will `rm -rf` separately.
- Bumping to 3.38.0 — user will do that as a follow-up once cleanup lands.
- `docs/pipeline/error-patterns.md` `unknown/unknown` telemetry noise (Poirot finding #7) — upstream capture hygiene, separate concern.

**Small ceremony:** Scout fan-out for Colby done. Roz full suite + scoped rework re-verify. Poirot blind diff review done (rework cycle got focused re-check). No Sarah (no architectural decision). No Robert (Small skips review-juncture Robert gate).
---

## Prior Pipeline (closed)
**Feature:** Roz maxTurns bump (15 → 50) — fix turn-cap truncation mid-generation
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Micro
**Opened:** 2026-04-20
**Closed:** 2026-04-20
**Commit:** (see commit log)

**Scope:** Frontmatter edits (maxTurns: 15 → 50):
- `.claude/agents/roz.md` (installed)
- `source/claude/agents/roz.frontmatter.yml` (source template)
- `source/cursor/agents/roz.frontmatter.yml` (source template, synced down for parity)
- Closed pipeline-state.md itself in same commit.

**Rationale:** Roz hit 15-turn ceiling and truncated mid-sentence on tool-heavy QA runs. Peer agents are at 40–75; Roz=15 is a documented outlier. 50 matches peer range (agatha=60, sarah=45, colby=75).

**Out of scope:** validate-dod-marker.sh hook (confirmed orphan artifact from abandoned Apr 17 iteration; not in git; shipped in local plugin cache only). `effort` discrepancy between roz.md (high) and source yml (medium) — tracked separately.

**Micro skips:** scout fan-out for Colby, brain capture T2/T3, budget estimate gate. Roz full suite still runs as safety valve.

---

## Prior Pipeline (closed)
**Feature:** v3.35.0 release — version bump + CHANGELOG
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Micro
**Closed:** 2026-04-17

---

## Prior Pipeline (closed)
**Feature:** Pre-existing test suite failures — 87 hooks + 4 xml-prompt-structure
**Phase:** idle
**Stop Reason:** completed_clean
**Sizing:** Small
**Closed:** 2026-04-16
**Commit:** 3c8e7cb

---

## Prior Pipeline (closed)
**Feature:** ADR-0041 — Effort-per-agent task-class tier model (Opus 4.7 xhigh)
**Stop Reason:** completed_clean
**Closed:** 2026-04-16
**Release:** v3.34.0 (commit df47b85)
**Resolved:** GitHub issue #41

**Telemetry T3:** rework=3 cycles, first_pass_qa=0.25, evoscore=1.039 (+60 net new tests). Captured as brain thought 67fccb53.

**Key decision captured:** 4-tier task-class model replaces size-dependent model tables + universal scope classifier. Priority stack: accuracy > speed > cost. Sonnet eliminated from reasoning tiers. Supersedes brain thought b09f430b (Colby Medium=Opus, 2026-04-03).

**Known pattern:** Roz partial-output stall recurred 3× this session. Mitigation: Eva-run pytest diagnostic bridges the gap. Captured as lesson d70409af. Structural fix candidate: explicit "STOP and RETURN" constraint in Roz persona.

---

## Prior Pipeline (closed)
**Feature:** ADR-0040 Design system auto-loading + Sarah institutional memory search
**Stop Reason:** completed_clean
**Closed:** 2026-04-13
**Release:** v3.33.0 (commit e5686ab)

## Prior Pipeline (closed)
**Feature:** feat/brain-setup-auto-fix
**Stop Reason:** completed_clean
**Closed:** 2026-04-13
**Release:** v3.30.7

## Prior Pipeline (closed)
**Feature:** ADR-0035 + ADR-0036 + ADR-0037 — Waves 4, 5, 6
**Stop Reason:** completed_clean
**Closed:** 2026-04-12
**Release:** v3.29.0

## Prior Pipeline (closed)
**Feature:** ADR-0034 Gauntlet remediation
**Stop Reason:** completed_clean
**Closed:** 2026-04-12
**Release:** v3.28.0
</content>
</invoke><!-- COMPACTION: 2026-04-17T02:23:07Z -->
<!-- COMPACTION: 2026-04-17T03:08:07Z -->
<!-- COMPACTION: 2026-04-21T20:56:22Z -->
<!-- COMPACTION: 2026-04-22T01:52:42Z -->
<!-- COMPACTION: 2026-04-24T19:43:44Z -->
<!-- COMPACTION: 2026-04-24T20:38:58Z -->
<!-- COMPACTION: 2026-04-24T21:36:21Z -->
<!-- COMPACTION: 2026-04-27T11:56:47Z -->
<!-- COMPACTION: 2026-04-28T15:35:34Z -->
