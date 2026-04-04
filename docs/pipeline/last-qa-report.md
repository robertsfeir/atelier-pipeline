# QA Report -- 2026-04-03 (Phase 2 Wave 1: Steps 2a + 2d + 2e)

*Reviewed by Roz*

---

### Verdict: FAIL (4 BLOCKERs, 2 FIX-REQUIRED)

---

## Scope

Phase 2 Wave 1 of ADR-0022: Steps 2a (per-agent hook scripts), 2d (permissionMode), 2e (hooks: frontmatter wiring). Also includes proactive Step 2c/2f work (robert-spec, sable-ux personas; pm.md, ux.md, create-agent.md, darwin.md, agent-system.md, technical-reference.md updates).

## Tier 1 -- Mechanical Checks

| Check | Status | Details |
|-------|--------|---------|
| Type Check | SKIP | No typecheck configured |
| Lint | SKIP | No linter configured |
| Tests | FAIL | 563 passed, 70 failed. 2 in-scope failures (T-0022-156, T-0022-157). 12 future-wave (Steps 2g, 2h). 56 pre-existing (.setup-mode artifact, see note). Brain: 93 passed, 0 failed. |
| Unfinished Markers | PASS | Zero TODO/FIXME/HACK/XXX in any changed source/hooks or frontmatter file |

**Pre-existing failure note:** 56 old test failures (test_enforce_paths.py, test_enforce_git.py, test_enforce_pipeline_activation.py, test_enforce_sequencing.py, test_if_conditionals.py) are caused by an untracked `docs/pipeline/.setup-mode` file in the working directory. This file makes every hook short-circuit via `exit 0`. Not introduced by this wave -- confirmed via `git status` (untracked). The file should be deleted to restore the test baseline.

## Tier 2 -- Judgment Checks

| Check | Status | Details |
|-------|--------|---------|
| Security | PASS | No secrets, no injection vectors. Hook scripts use `set -uo pipefail`, jq validation, setup-mode bypass only. |
| Docs Impact | YES | technical-reference.md, user-guide.md, SKILL.md, CLAUDE.md all need stale reference cleanup (see B2, B4, F1, F2). |
| Wiring | PARTIAL | Per-agent hooks correctly wired in frontmatter. Settings.json template updated. Two stale references remain in SKILL.md and docs/guide/. |
| Semantic Correctness | PASS | All 7 per-agent scripts follow correct enforcement patterns. Config retains critical keys. |

## Requirements Verification (Steps 2a + 2d + 2e)

| # | Requirement | Source | Colby Claims | Roz Verified | Finding |
|---|-------------|--------|-------------|-------------|---------|
| R5 | Replace enforce-paths.sh with per-agent hooks | ADR | Done | PASS | 7 per-agent scripts created, enforce-paths.sh deleted from source/claude/, retained in source/cursor/ |
| R7 | permissionMode: acceptEdits on Colby, Cal, Agatha, Ellis | ADR | Done | PASS | All 4 frontmatter overlays have `permissionMode: acceptEdits` |
| R10 | Per-agent scripts ~15-20 lines, no agent_type, no case | ADR | Done | PASS | Line counts: 22-39 lines. Roz (36) and Colby (39) are larger due to config reads (justified by Note 6). No agent_type checks. No case statements for agent routing. |
| R11 | Cursor keeps global hook model | ADR | Done | PASS | source/cursor/hooks/enforce-paths.sh retained and complete. hooks.json references it. |
| R13 | Eva main thread: docs/pipeline/ write only | ADR | Done | PASS | enforce-eva-paths.sh restricts to docs/pipeline/*. Registered in settings.json template. |
| R16 | PreToolUse hooks fire regardless of permissionMode | ADR | Claimed | VERIFIED | Claude Code spec: permissionMode controls approval prompts; PreToolUse hooks fire independently. |
| R20 | Ellis has no path hooks | ADR | Done | PASS | ellis.frontmatter.yml has `permissionMode: acceptEdits` but no `hooks:` field. |
| R21 | Read-only agents keep disallowedTools | ADR | Done | PASS | robert.frontmatter.yml, sable.frontmatter.yml, investigator, distillator, sentinel, darwin, deps all have `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |

## Per-Agent Script Pattern Verification (Constraint 1)

All 7 scripts follow the required pattern:

| Script | Setup bypass | Read stdin | Extract file_path | Normalize | Check paths | Block/Allow | Config read |
|--------|-------------|------------|-------------------|-----------|-------------|-------------|-------------|
| enforce-roz-paths.sh | ATELIER_SETUP_MODE + .setup-mode | cat | jq .tool_input.file_path | N/A (relative) | test_patterns + docs/pipeline/ | exit 2 with BLOCKED | Yes (enforcement-config.json) |
| enforce-cal-paths.sh | ATELIER_SETUP_MODE + .setup-mode | cat | jq .tool_input.file_path | N/A | docs/architecture/ | exit 2 with BLOCKED | No |
| enforce-colby-paths.sh | ATELIER_SETUP_MODE + .setup-mode | cat | jq .tool_input.file_path | Absolute->relative | colby_blocked_paths | exit 2 with BLOCKED | Yes (enforcement-config.json) |
| enforce-agatha-paths.sh | ATELIER_SETUP_MODE + .setup-mode | cat | jq .tool_input.file_path | N/A | docs/ | exit 2 with BLOCKED | No |
| enforce-product-paths.sh | ATELIER_SETUP_MODE + .setup-mode | cat | jq .tool_input.file_path | N/A | docs/product/ | exit 2 with BLOCKED | No |
| enforce-ux-paths.sh | ATELIER_SETUP_MODE + .setup-mode | cat | jq .tool_input.file_path | N/A | docs/ux/ | exit 2 with BLOCKED | No |
| enforce-eva-paths.sh | ATELIER_SETUP_MODE + .setup-mode | cat | jq .tool_input.file_path | N/A | docs/pipeline/ | exit 2 with BLOCKED | No |

All scripts: exit 0 for non-Write/Edit tools, exit 0 for empty file_path, exit 2 with descriptive BLOCKED message on violation.

## enforcement-config.json Verification (Constraint 2)

| Key | Present | Required |
|-----|---------|----------|
| pipeline_state_dir | YES ("docs/pipeline") | CRITICAL -- enforce-pipeline-activation.sh and enforce-sequencing.sh depend on this |
| test_patterns | YES (7 patterns) | Required for enforce-roz-paths.sh |
| colby_blocked_paths | YES (14 prefixes) | Required for enforce-colby-paths.sh |
| test_command | YES | Required for Roz QA |
| architecture_dir | NO (removed) | Correct -- per distillate |
| product_specs_dir | NO (removed) | Correct -- per distillate |
| ux_docs_dir | NO (removed) | Correct -- per distillate |

## Hooks Field YAML Verification (Constraint 3)

| Agent | hooks: present | event | matcher | command | Valid |
|-------|---------------|-------|---------|---------|-------|
| roz | YES | PreToolUse | Write | enforce-roz-paths.sh | PASS |
| cal | YES | PreToolUse | Write\|Edit | enforce-cal-paths.sh | PASS |
| colby | YES | PreToolUse | Write\|Edit\|MultiEdit | enforce-colby-paths.sh | PASS |
| agatha | YES | PreToolUse | Write\|Edit\|MultiEdit | enforce-agatha-paths.sh | PASS |
| robert-spec | YES | PreToolUse | Write\|Edit | enforce-product-paths.sh | PASS |
| sable-ux | YES | PreToolUse | Write\|Edit | enforce-ux-paths.sh | PASS |
| ellis | NO hooks: | -- | -- | -- | PASS (R20) |

## Monolith Deletion Verification (Constraint 4)

| Check | Result |
|-------|--------|
| source/claude/hooks/enforce-paths.sh exists? | NO (deleted) |
| source/cursor/hooks/enforce-paths.sh exists? | YES (retained) |
| Cursor copy complete? | YES -- contains all agent cases (cal, colby, roz, ellis, agatha) and is executable |

## Cursor Overlay Verification (Constraint 5)

Verified: Zero matches for `permissionMode` or `hooks:` in any file under `source/cursor/agents/`.

## Executable Permissions

All 7 per-agent scripts have `-rwxr-xr-x` permissions. PASS.

## Unfinished Markers

`grep -rn "TODO|FIXME|HACK|XXX"` across all changed hook scripts, frontmatter files, and test files: **0 matches**.

## Issues Found

### BLOCKERs (pipeline halts -- Colby fixes before advancing)

**B1: T-0022-156 -- stale `enforce-paths.sh` references in docs/guide/ (11 instances)**

`docs/guide/technical-reference.md` contains 10 references to `enforce-paths.sh` in the enforcement config table (lines 1268-1274), the settings.json example (line 1288), the matcher explanation (line 1336), and the Teammates section (line 1427). `docs/guide/user-guide.md` contains 1 reference (line 1339 in the directory tree).

These files were explicitly in the diff (technical-reference.md was updated with the new per-agent hook directory tree) but the enforcement config section and settings.json example sections were not updated to match. The old references describe a monolith that no longer exists.

**B2: T-0022-157 -- CLAUDE.md missing `robert-spec` / `sable-ux` roster entries**

CLAUDE.md does not mention `robert-spec` or `sable-ux` anywhere. The distillate requirement R15 calls for "Core agent constant: clarify robert-spec and sable-ux naming." The test asserts these terms appear in CLAUDE.md. While `source/shared/rules/agent-system.md` was correctly updated with both agents, the project-level CLAUDE.md (which summarizes key conventions and is always-loaded context) was not.

**B3: Per-agent hooks missing `CURSOR_PROJECT_DIR` fallback (T-0022-025)**

All 7 per-agent hook scripts use `${CLAUDE_PROJECT_DIR:-.}` in the setup-mode check (line 6) but do not include the `CURSOR_PROJECT_DIR` fallback that existing cross-cutting hooks use (pattern: `${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-.}}`). While per-agent hooks fire from Claude Code frontmatter only (not Cursor), this breaks the convention established by enforce-git.sh, enforce-pipeline-activation.sh, and enforce-sequencing.sh. The Phase 1 test T-0022-025 explicitly asserts: "every .sh file in source/claude/hooks/ that references CLAUDE_PROJECT_DIR must also reference CURSOR_PROJECT_DIR."

Files affected: enforce-roz-paths.sh, enforce-cal-paths.sh, enforce-colby-paths.sh, enforce-agatha-paths.sh, enforce-product-paths.sh, enforce-ux-paths.sh, enforce-eva-paths.sh (line 6 in each).

**B4: SKILL.md stale reference to `enforce-paths.sh` for discovered agents (line 394)**

`skills/pipeline-setup/SKILL.md` line 394 still says: "To grant write access, add an explicit case to `.claude/hooks/enforce-paths.sh` for the agent's name." This should reference the per-agent frontmatter hook pattern instead. The create-agent.md command file was correctly updated (line 46: "add a per-agent frontmatter hook") but the SKILL.md was not.

A separate reference on line 56 ("Other hook entries (enforce-paths.sh, enforce-sequencing.sh, enforce-git.sh, etc.) are not affected") is in the quality-gate.sh cleanup section and is also stale, though less critical since it is in a legacy cleanup context.

### FIX-REQUIRED (queued -- all resolved before Ellis commits)

**F1: Phase 1 test T-0022-021 expects 14 hook scripts, actual is 20**

`test_adr_0022_phase1_overlay.py::test_T_0022_021_claude_hooks` asserts `sh_count == 14`. After this wave added 7 per-agent scripts and deleted 1 (enforce-paths.sh), the count is now 20 (was 14, +7 new, -1 deleted = 20). This test needs updating as part of Step 2g (test file updates referencing old paths/counts).

**F2: Untracked `docs/pipeline/.setup-mode` file poisoning test baseline**

An untracked file `docs/pipeline/.setup-mode` exists in the working directory. This causes every hook script's setup-mode bypass (`[ -f "${CLAUDE_PROJECT_DIR:-.}/docs/pipeline/.setup-mode" ] && exit 0`) to trigger when tests run without `CLAUDE_PROJECT_DIR` set -- silently passing 56 tests that should fail. This is pre-existing (not introduced by this wave) but masks regressions. The file should be deleted from the working directory before the next commit.

## ADR-0022 Failure Classification

| Category | Count | Tests |
|----------|-------|-------|
| In-scope BLOCKER (Steps 2a/2d/2e/2f) | 4 | T-0022-156, T-0022-157, T-0022-025, SKILL.md L394 |
| Future-wave Step 2g (test count/cleanup) | 4 | T-0022-021, T-0022-164, T-0022-165, T-0022-166 |
| Future-wave Step 2h (compaction advisory) | 7 | T-0022-171, 172, 185, 186, 187, 189, 190 |
| Pre-existing (.setup-mode artifact) | 56 | test_enforce_paths.py (16), test_enforce_git.py (10), test_enforce_pipeline_activation.py (11), test_enforce_sequencing.py (11), test_if_conditionals.py (5), test_doc_sync.py (3) |

## Doc Impact: YES

Files requiring updates:
- `docs/guide/technical-reference.md` -- Replace enforce-paths.sh references with per-agent enforcement description (B1)
- `docs/guide/user-guide.md` -- Update directory tree entry (B1)
- `CLAUDE.md` -- Add robert-spec/sable-ux to agent roster (B2)
- `skills/pipeline-setup/SKILL.md` -- Fix discovered agent enforcement reference (B4)

## Roz's Assessment

The core implementation is solid. All 7 per-agent hook scripts follow the correct pattern, enforcement-config.json retains critical keys (pipeline_state_dir intact -- Note 11a honored), permissionMode is correctly applied to all 4 write-heavy agents, hooks: frontmatter wiring is correct for all 6 agents that need it, Ellis correctly has no hooks, and Cursor overlays correctly omit both permissionMode and hooks: fields. The monolith deletion is clean with the Cursor copy properly retained.

Four issues prevent PASS:

1. Stale `enforce-paths.sh` references in docs/guide/ describe a monolith that no longer exists (11 instances across 2 files). These were in-scope for the technical-reference.md update that was partially done.

2. CLAUDE.md (always-loaded context) does not mention the new robert-spec/sable-ux agents that were added to agent-system.md.

3. Per-agent hooks break the CURSOR_PROJECT_DIR convention. While these hooks only fire from Claude Code, the Phase 1 test enforcement and code consistency require the fallback pattern. This is a 1-line fix per script (7 files, line 6 each).

4. SKILL.md still tells users to add cases to enforce-paths.sh for custom agents -- a file that was deleted.

The pre-existing `.setup-mode` file is a separate concern but should be removed before Ellis commits to prevent masking future regressions.

All blockers are straightforward fixes. No architectural issues. The enforcement redesign is sound.
