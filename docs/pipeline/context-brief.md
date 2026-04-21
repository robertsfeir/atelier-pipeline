# Context Brief

## Scope
Issue #31 slice 4 + Sherlock subagent introduction. Medium pipeline.
Session: 0265ce7f. Worktree: /Users/Robert_Sfeir/projects/atelier/atelier-pipeline-0265ce7f on branch session/0265ce7f.

## Current state (for session-resume)
- **Phase:** architecture COMPLETE. Next phase: build (Roz test authoring).
- **Sarah ADR:** `docs/architecture/ADR-0045-sherlock-subagent-and-slice-4-cleanup.md` (103 KB, 5 steps, 71 tests, 9 test categories A-I).
- **Sherlock spec source:** `docs/pipeline/sherlock-spec.md` in worktree (copied from /Users/Robert_Sfeir/projects/test/sherlock.md).
- **Prior pipelines shipped this session:** slice 1 (v3.39.0, commit cffb86a) + slice 2 (v3.40.0, commit 07e9f6e). Both on origin/main.

## Next steps (paused, awaiting user go)
1. **Roz** — author test spec for ADR-0045 (71 tests across categories A-I). Scoped re-run friendly; uses `<qa-evidence>` block. File target: `tests/test_adr0045_*` (flat file per slice-1/slice-2 precedent). Also touches existing tests per Category H.
2. **Colby** — implement 5 steps from ADR-0045 §Implementation Plan. Includes large-scale deletions (5 commands × 3 variants + 2 agents × 3 variants + 3 skills × 2 plugin trees + 2 test dirs wholesale) + Sherlock persona creation + Gate 4 rewrite + routing updates.
3. **Roz safety-valve** — full suite.
4. **Poirot** — blind review.
5. **Ellis** — commit + release 3.41.0 + ff-merge (push blocked by user deny rule).

## User Decisions (confirmed pre-Sarah)
- **Sherlock as SUBAGENT**, not main-thread skill. Own context window.
- **Roz exits bug investigation** entirely. Roz stays on test-authoring + QA.
- **No scouts for Sherlock** — enforce-scout-swarm.sh hook must bypass. Sarah's ADR notes Sherlock is not currently in the hook's case statement, so no code change needed (confirm at Colby time).
- **Medium sizing** (not Large, despite broader scope than slice 1/2).
- **Slice 4 removals:** `/debug`, `/darwin`, `/deps`, `/create-agent`, `/telemetry-hydrate` commands (+ all 3 platform variants); `darwin` + `deps` agent personas (+ all 3 platform variants); `dashboard`, `pipeline-overview`, `load-design` skills (+ Cursor mirrors where present).
- **Fold:** `load-design` → `pipeline-setup` Step 1a ("Design System Path (Optional)"). Sarah chose earlier placement than suggested.
- **pipeline-config.json** drops `darwin_enabled`, `deps_agent_enabled`. Extra keys in existing users' configs are harmless (Sarah's install-migration note).

## Sarah Design Decisions (recorded in ADR-0045)
- Gate 4 keeps number 4; body rewrites Roz-investigates → Sherlock-investigates.
- Roz's `<workflow>` Investigation Mode section removed entirely.
- Eva's 6-question intake protocol lives in `default-persona.md <protocol id="user-bug-flow">` (structured routing procedure, not a skill).
- `ALL_AGENTS_12` constant refactored to `CORE_AGENTS` (identifier without count — avoids future cascade on agent count changes).
- Sherlock Per-Agent Assignment Table entry: **Tier 3, opus, high**. No final-juncture promotion signal applies (Sherlock runs before Colby, not at review juncture).
- Sherlock tools include `mcp__chrome-devtools__*` (optional; fallback to Read/Grep/Bash if MCP absent).

## Accepted Out-of-Scope (logged in ADR-0045 Anti-Goals)
- `docs/guide/technical-reference.md` lines 1280-2021 (darwin/deps schema docs) — deferred to future doc-sweep ADR.
- `ADR-0040` references to `/load-design` skill — ADR immutability; left as historical record.
- `.cursor-plugin/agents/` missing brain-extractor/robert-spec/sable-ux — pre-existing drift, not caused by slice 4.

## Test Impact (enumerated in ADR-0045 Category H + I)
- **Directory deletions:** `tests/adr-0015-deps/` (62 tests), `tests/adr-0016-darwin/` (96 tests). Total 158 deleted.
- **Updates** (exact replacement text in ADR §Test Specification):
  - `tests/conftest.py:68-72` — `ALL_AGENTS_12` → `CORE_AGENTS`
  - `tests/hooks/test_adr_0022_phase1_overlay.py:32` — shared commands count 11 → 6
  - `tests/adr-0023-reduction/test_reduction_structural.py` — 5 parametrize sites + T_0023_003 gate-4 regex + T_0023_116 session-boot JSON keys
  - `tests/cursor-port/test_cursor_port.py:524` — total agent count 12 → 11
  - `tests/dashboard/test_dashboard_integration.py:133-134` — T_0018_014 darwin/deps config keys
  - `tests/test_adr0044_instruction_budget_trim.py` — lines 384/510/568/1418 routing-detail anchors; line 941 gate 4 quote
  - `tests/adr-0042/test_adr_0042.py:235` — per-agent table 17 → 16 rows; test_T_0042_012 (Deps frontmatter) DELETE
  - `tests/hooks/test_session_boot.py:213` — agent count 15 → 14

## How to resume
Fresh Eva session reads `pipeline-state.md` + this file + applies session-boot protocol. ADR-0045 is the spec. Say "continue" or "route Roz" to kick next phase.

## Rejected Alternatives
- Sherlock as main-thread SKILL (user reversed to subagent).
- Large sizing (user wants Medium despite scope).
- Scouts for Sherlock (user: "not right now").
- Editing ADR-0040 in place to drop `/load-design` refs (ADR immutability).
