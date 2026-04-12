# ADR-0035: Wave 4 -- ADR-0032 Consumer Wiring, Hydrate-Telemetry Hardening, S4 Ellis Hook Resolution

## DoR: Requirements Extracted

**Sources:** ADR-0032 Steps 2-3 (ratified, unimplemented), ADR-0034 Wave 4 outline, Gauntlet finding S4 (enforce-ellis-paths.sh vs. ADR-0022 R20), scout pre-flight research brief, `source/shared/hooks/pipeline-state-path.sh` (helper already shipped in Wave 1), `source/shared/hooks/hook-lib.sh` (shipped in Wave 2), `brain/scripts/hydrate-telemetry.mjs` (1029-line telemetry script), `source/claude/hooks/enforce-eva-paths.sh` (whitelist already present), `source/claude/hooks/enforce-ellis-paths.sh` (path-enforcing hook), ADR-0022 R20 ("Ellis has no path hooks"), `source/claude/hooks/post-compact-reinject.sh` (hardcoded path comments), `.claude/references/retro-lessons.md`, `.claude/references/dor-dod.md`, `.claude/references/step-sizing.md`.

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | `hydrate-telemetry.mjs` must auto-resolve the out-of-repo state dir when `--state-dir` is not provided | ADR-0032 Step 2 item 1 | ADR-0032:323-329 |
| R2 | `parseStateFiles()` must gracefully exit returning 0 when stateDir does not exist on disk | ADR-0032 Step 2 item 1 | ADR-0032:327 |
| R3 | `hydrate-telemetry.mjs` must still work with explicit `--state-dir` argument (backward compat) | ADR-0032 Step 2 | ADR-0032:359 |
| R4 | All agent persona references to `context-brief.md` must use the `{pipeline_state_dir}` placeholder | ADR-0032 Step 2 items 3-5 | ADR-0032:340-344 |
| R5 | All command file references to session-specific state files must use `{pipeline_state_dir}` placeholder | ADR-0032 Step 2 items 6-8 | ADR-0032:346-350 |
| R6 | `pipeline-orchestration.md` must distinguish session-specific from shared file paths | ADR-0032 Step 2 item 10 | ADR-0032:354 |
| R7 | `enforce-eva-paths.sh` `~/.atelier/pipeline/*/*/*` whitelist must have test coverage | ADR-0034 Wave 4 outline, test gap found | `tests/hooks/test_enforce_eva_paths.py` (no `.atelier` test exists) |
| R8 | `post-compact-reinject.sh` path comments must reflect the resolved path, not hardcoded `docs/pipeline/` | ADR-0032 Step 1 item 3, scout finding | `source/claude/hooks/post-compact-reinject.sh:57,64` |
| R9 | `pipeline-orchestration.md` must contain a concurrent-session hard-pause protocol | ADR-0032 Step 3 | ADR-0032:378-396 |
| R10 | Resolve S4 contradiction: `enforce-ellis-paths.sh` restricts Ellis to an allowlist vs. ADR-0022 R20 "Ellis has no path hooks (full write access)" | Gauntlet S4, ADR-0034 R15 | `source/claude/hooks/enforce-ellis-paths.sh:1-56`, ADR-0022:28 |
| R11 | `session-boot.sh` JSON output should include `state_dir` field for Eva's boot sequence | ADR-0032 Step 1 (partially deferred) | ADR-0032:296 |
| R12 | `source/shared/commands/debug.md` hardcoded `docs/pipeline/investigation-ledger.md` must use placeholder | Scout finding | `source/shared/commands/debug.md:22` |
| R13 | `source/shared/agents/roz.md` hardcoded `docs/pipeline/last-qa-report.md` must use placeholder | Scout finding | `source/shared/agents/roz.md:99` |
| R14 | `pipeline-orchestration.md` state-files section uses hardcoded `docs/pipeline` instead of `{pipeline_state_dir}` | Scout finding | `source/shared/rules/pipeline-orchestration.md:400` |
| R15 | `agent-system.md` brain-config section has hardcoded `docs/pipeline/pipeline-state.md` | Grep discovery | `source/shared/rules/agent-system.md:25` |
| R16 | `telemetry-bridge.sh` defaults `PIPELINE_STATE_PATH` to hardcoded `docs/pipeline/pipeline-state.md` | Grep discovery | `source/shared/dashboard/telemetry-bridge.sh:19` |
| R17 | `qa-checks.md` has hardcoded `docs/pipeline/last-qa-report.md` reference | Grep discovery | `source/shared/references/qa-checks.md:82` |

**Retro risks:**

- **Lesson #003 (Stop Hook Race Condition):** `session-boot.sh` is a SessionStart hook. Adding the `state_dir` JSON field must remain a trivial string interpolation -- no new I/O, no blocking call. Exit 0 always.
- **Lesson #005 (Frontend Wiring Omission):** ADR-0032 Step 1 produced a new out-of-repo state directory. Step 2 wires the consumers. Every consumer file must be updated in the same step to avoid orphan path drift. The research confirmed 10 consumer files with hardcoded `docs/pipeline/` paths that need conversion.
- **Lesson #002 (Self-Reporting Bug Codification):** The test spec for hydrate-telemetry must test the auto-resolve path computation, not just "it doesn't crash" -- the actual hash output must be deterministic and match the bash helper.

**Spec challenge:** The spec (ADR-0032 Step 2) assumes that `hydrate-telemetry.mjs` should reimplement the bash helper's slug/hash logic in JavaScript. **If the slug computation diverges between the bash helper and the JS reimplementation** (e.g., `basename` vs. `path.basename`, shell quoting differences, SHA256 library differences), the hydrate script reads from a different directory than session-boot.sh writes to -- silent data loss. Mitigation: the JS reimplementation must be tested against the bash helper's output for the same input paths, creating a cross-implementation contract test.

**SPOF:** The slug/hash path computation, now duplicated in two languages (bash and JS). Failure mode: a platform-specific difference in path resolution (e.g., trailing slashes, symlink resolution) causes the two implementations to produce different hashes for the same worktree. Graceful degradation: the JS implementation falls back to `docs/pipeline/` when the computed out-of-repo directory does not exist (`existsSync` check), same as the bash helper's fallback. Hydration degrades to reading from in-repo state (which may be stale or from a prior session) but does not crash or lose already-captured data.

**Anti-goals:**

1. Anti-goal: Refactoring hydrate-telemetry.mjs beyond the stateDir resolution wiring. Reason: The file is 1029 lines with complex tier-1/tier-3 logic. Touching anything outside the `parseStateFiles` path and the `main()` caller creates unscoped blast radius. Revisit: If a future ADR proposes a hydrate-telemetry refactor.

2. Anti-goal: Implementing `.session-marker` nonce detection and `concurrent_session_detected` in session-boot.sh. Reason: ADR-0032 specified this as part of Step 1, but the Wave 1 implementation shipped without it and the system works correctly with the simpler staleness check. The hard-pause protocol in pipeline-orchestration.md is behavioral (Eva reads `stale_context: true` and acts) and does not require a new session-boot field to be useful. Revisit: If concurrent-session clobber incidents occur in production and `stale_context: true` proves insufficient to detect them.

3. Anti-goal: Changing `error-patterns.md` from its `docs/pipeline/` location. Reason: ADR-0032 Decision is explicit -- `error-patterns.md` stays in-repo, shared across sessions. Revisit: Never.

---

## Status

Proposed -- 2026-04-12.

**Depends on:** ADR-0034 Waves 1-3 (completed, shipped as v3.28.0). ADR-0032 Step 1 (completed in ADR-0034 Wave 1).
**Supersedes:** Nothing. Implements ADR-0032 Steps 2-3. Resolves Gauntlet finding S4.
**Related:** ADR-0022 (Wave 3 native enforcement redesign -- R20 is the Ellis path hook decision this ADR resolves).

## Context

ADR-0032 ratified a three-step plan for pipeline state session isolation. Step 1 (shared helper + session-boot + post-compact wiring) shipped in ADR-0034 Wave 1. Steps 2 and 3 were explicitly deferred to Wave 4 because:

1. **`hydrate-telemetry.mjs` is 1029 lines** and merits a focused session rather than being squeezed into a wave alongside brain enum fixes.
2. **The S4 Ellis hook contradiction** requires an architectural decision (Cal's call) before implementation can proceed.

Since Wave 1 shipped, the following state is in effect:

- `pipeline-state-path.sh` exists in both `source/shared/hooks/` and `.claude/hooks/` (identical, shipped Wave 1).
- `hook-lib.sh` exists in both locations (identical, shipped Wave 2).
- `session-boot.sh` and `post-compact-reinject.sh` source the helper and read state from the resolved out-of-repo directory.
- `enforce-eva-paths.sh` already has the `~/.atelier/pipeline/*/*/*` whitelist (shipped Wave 1) but **has no test coverage for it**.
- `post-compact-reinject.sh` has hardcoded comment strings (`## From: docs/pipeline/pipeline-state.md`) that do not reflect the resolved path.
- **10 consumer files** still reference hardcoded `docs/pipeline/` for session-specific files instead of using the `{pipeline_state_dir}` placeholder.
- `hydrate-telemetry.mjs` only parses state files when `--state-dir` is explicitly provided. It has no auto-resolution of the out-of-repo path.
- `pipeline-orchestration.md` has no concurrent-session hard-pause protocol.
- `session-boot.sh` JSON output does not include a `state_dir` field.

Additionally, the Gauntlet surfaced finding S4: `enforce-ellis-paths.sh` restricts Ellis to an allowlist of paths (CHANGELOG.md, git config files, CI/CD paths) via a PreToolUse hook. ADR-0022 R20 states: "Ellis has no path hooks (full write access, sequencing enforced at Layer 3)." This is a direct contradiction between a ratified ADR and the shipped enforcement code.

### Research-Brief Correction

The pre-flight scout research brief claimed that `pipeline-state-path.sh` and `hook-lib.sh` exist "in `.claude/hooks/` only, NOT in `source/`". This was incorrect. Both files exist in `source/shared/hooks/` (shipped in ADR-0034 Waves 1 and 2 respectively, verified via `git log`). The source-of-truth gap does not exist. This eliminates items 12-13 from the research brief's consumer file list and removes "add files to source/" from the ADR scope.

## Decision

### S4 Resolution: Keep enforce-ellis-paths.sh as a Safety Net (Option C)

**The contradiction:** ADR-0022 R20 says "Ellis has no path hooks (full write access, sequencing enforced at Layer 3)." The shipped `enforce-ellis-paths.sh` restricts Ellis to CHANGELOG.md, git config files, and CI/CD paths.

**Options evaluated:**

**(A) Delete the hook (pure R20 compliance).** Remove `enforce-ellis-paths.sh` entirely. Ellis gets full write access, relying on Layer 3 sequencing (Eva never invokes Ellis before Roz QA passes) to prevent bad writes. **Risk:** A prompt injection or agent hallucination in Ellis could write to arbitrary paths. Layer 3 is behavioral, not mechanical. The whole point of the atelier-pipeline enforcement philosophy is "behavioral guidance is ignored -- mechanical enforcement via PreToolUse hooks is required" (memory feedback). Deleting a working mechanical gate to comply with an ADR's aspirational statement is backwards.

**(B) Convert to a sequencing-only gate (not path enforcement).** Replace the path allowlist with a check that pipeline phase is "commit" before allowing Ellis writes. **Risk:** This requires reading pipeline-state.md inside a PreToolUse hook (I/O in hot path, Retro Lesson #003 risk). The phase field may be stale. And it still doesn't prevent Ellis from writing to arbitrary paths during the commit phase.

**(C) Keep the hook as a safety net with documented scope.** CHOSEN. The hook stays. ADR-0022 R20 is corrected: "Ellis has path hooks that restrict writes to commit-related paths (CHANGELOG.md, git config, CI/CD). This is a safety net, not a sequencing gate. Layer 3 sequencing (Eva invokes Ellis only after QA pass) remains the primary control." Update the test file docstring to reference this ADR. The allowlist already covers every path Ellis legitimately needs.

**Why C:** The enforcement philosophy of this project is "mechanical enforcement required." ADR-0022 R20 was written before the enforcement hook was implemented. Now that the hook exists and works, deleting it to comply with a pre-implementation decision is the wrong direction. The ADR's intent (Ellis should not be blocked from doing his job) is satisfied because the allowlist covers his actual job. The contradiction is resolved by updating the documentation, not by removing enforcement.

**Action items for S4:**
1. Add a comment to `source/claude/hooks/enforce-ellis-paths.sh` header: `# Note: ADR-0022 R20 said "no path hooks for Ellis." ADR-0035 supersedes that` + `# decision. This hook is a safety net for commit-related paths. Layer 3` + `# sequencing (Eva invokes Ellis only after QA) is the primary control.`
2. Update `tests/hooks/test_enforce_ellis_paths.py` docstring to reference ADR-0035.

### Hydrate-Telemetry: JS Reimplementation of Path Resolution (not execSync)

**Options evaluated:**

**(A) Shell out to the bash helper via `execSync`.** Call `source pipeline-state-path.sh && session_state_dir` from Node.js. **Rejected:** Requires the bash helper to be at a known path relative to the brain script. The brain directory tree (`brain/scripts/`) is unrelated to the hook directory tree (`source/shared/hooks/`). The helper path cannot be reliably resolved. Additionally, `execSync` in a database hydration script is fragile (shell environment, PATH, bash version).

**(B) Reimplement the path logic in JavaScript.** CHOSEN. The logic is 6 lines: read env var, compute basename, compute SHA256 hex prefix, join path. Use Node.js `crypto.createHash('sha256')` which produces identical output to `sha256sum`/`shasum -a 256` for the same input string. Add a contract test that verifies the JS and bash implementations produce the same hash for a set of test paths.

**Why B:** The path resolution logic is trivially small (basename + SHA256 + path join). The cross-implementation contract test catches divergence. The JS implementation needs no shell dependency and works on all platforms.

### Consumer File Updates: Replace Hardcoded `docs/pipeline/` with `{pipeline_state_dir}`

The `{pipeline_state_dir}` placeholder is already used throughout `source/shared/rules/` (default-persona.md, agent-system.md, pipeline-orchestration.md, pipeline-models.md) and `source/shared/variants/`. The following files still use hardcoded `docs/pipeline/` for session-specific state files:

| File | Line(s) | Hardcoded Reference | Correct Replacement |
|------|---------|--------------------|--------------------|
| `source/shared/agents/roz.md` | 99 | `docs/pipeline/last-qa-report.md` | `{pipeline_state_dir}/last-qa-report.md` |
| `source/shared/commands/architect.md` | 22 | `docs/pipeline/context-brief.md` | `{pipeline_state_dir}/context-brief.md` |
| `source/shared/commands/devops.md` | 17 | `docs/pipeline/context-brief.md` | `{pipeline_state_dir}/context-brief.md` |
| `source/shared/commands/debug.md` | 22 | `docs/pipeline/investigation-ledger.md` | `{pipeline_state_dir}/investigation-ledger.md` |
| `source/shared/commands/pipeline.md` | 19 | `docs/pipeline/pipeline-state.md` | `{pipeline_state_dir}/pipeline-state.md` |
| `source/shared/commands/pipeline.md` | 20 | `docs/pipeline/context-brief.md` | `{pipeline_state_dir}/context-brief.md` |
| `source/shared/commands/pipeline.md` | 138 | `docs/pipeline/context-brief.md` | `{pipeline_state_dir}/context-brief.md` |
| `source/shared/commands/pipeline.md` | 148 | `docs/pipeline/pipeline-state.md` | `{pipeline_state_dir}/pipeline-state.md` |
| `source/shared/rules/pipeline-orchestration.md` | 400 | `docs/pipeline` (state-files section) | `{pipeline_state_dir}` |
| `source/shared/rules/agent-system.md` | 25 | `docs/pipeline/pipeline-state.md` | `{pipeline_state_dir}/pipeline-state.md` |
| `source/shared/dashboard/telemetry-bridge.sh` | 19 | `docs/pipeline/pipeline-state.md` (default) | `{pipeline_state_dir}/pipeline-state.md` (note: this is a CLI default, see note below) |
| `source/shared/references/qa-checks.md` | 82 | `docs/pipeline/last-qa-report.md` | `{pipeline_state_dir}/last-qa-report.md` |

**Note on `telemetry-bridge.sh`:** This script accepts `--pipeline-state PATH` as a CLI argument with `docs/pipeline/pipeline-state.md` as the default. The default should reference `{pipeline_state_dir}/pipeline-state.md` in the comment/docs, but since this is a bash script that runs with `--pipeline-state` provided by the caller, the actual runtime path is already correct. The fix is updating the default and the JSDoc comment to reflect the new path convention.

**Note on `error-patterns.md` references:** Lines that reference `docs/pipeline/error-patterns.md` (pipeline.md:21, pipeline.md:153) stay as-is. `error-patterns.md` is the shared in-repo file per ADR-0032 Decision.

**Note on `{pipeline_state_dir}` resolution:** This is a template placeholder, not a runtime variable. It is resolved at install time by `pipeline-setup` (SKILL.md line 356 already configures it with default `docs/pipeline`). At runtime, Eva reads state files from the path the session-boot hook reported. The placeholder in agent/command files tells agents where to find state relative to the configured pipeline state directory. The session-boot.sh hook resolves the actual path and reports it in JSON; Eva uses that reported path for her writes. Agents that need to read state files receive the path via Eva's `<read>` tag in their invocation, not by resolving the placeholder themselves.

### Post-Compact Reinject Path Comments

`post-compact-reinject.sh` lines 57 and 64 output `## From: docs/pipeline/pipeline-state.md` and `## From: docs/pipeline/context-brief.md`. These should reflect the resolved `$STATE_DIR` path, not the hardcoded legacy path. The fix is string interpolation: `## From: $STATE_FILE` and `## From: $BRIEF_FILE` (these variables already hold the resolved paths at lines 39-40).

### Session-Boot `state_dir` Field

Add a `state_dir` field to `session-boot.sh` JSON output so Eva knows the resolved path at boot. This is a one-line addition to the output template. The `concurrent_session_detected` field from ADR-0032 is deferred (see Anti-goal #2).

### Concurrent-Session Hard-Pause Protocol

Add a `<protocol id="concurrent-session-hard-pause">` section to `pipeline-orchestration.md`. Eva triggers this when `stale_context: true` in session-boot JSON and the stale state's phase is not `idle`/`complete`. This uses the existing staleness detection (feature name mismatch) rather than the unimplemented nonce system.

## Alternatives Considered

### S4 Alternative A: Delete enforce-ellis-paths.sh

See Decision section. Rejected because it removes working mechanical enforcement to comply with a pre-implementation design statement. The project's enforcement philosophy is "behavioral constraints are ignored -- mechanical enforcement is required."

### S4 Alternative B: Sequencing-only gate

See Decision section. Rejected because it requires I/O in the PreToolUse hot path (reading pipeline-state.md to check phase) and still does not prevent path abuse during the commit phase.

### Hydrate-Telemetry Alternative A: execSync to bash helper

See Decision section. Rejected because the bash helper lives in a different directory tree than the brain scripts, and shelling out to bash from a Node.js database hydration script is fragile.

### Consumer Updates Alternative: Leave hardcoded paths and have Eva resolve at runtime

Leave `docs/pipeline/context-brief.md` in agent files and have Eva substitute the actual path when building invocations. **Rejected:** This creates a behavioral dependency (Eva must remember to substitute) rather than a mechanical one (the placeholder is resolved at install time). The project's philosophy is mechanical over behavioral. Additionally, the inconsistency between files that already use `{pipeline_state_dir}` and files that hardcode `docs/pipeline/` is confusing for any agent or human reading the source.

## Consequences

**Positive:**

- After Wave 4, every consumer of pipeline state files uses the `{pipeline_state_dir}` placeholder. No hardcoded `docs/pipeline/` references for session-specific files remain in agent/command/rule files.
- `hydrate-telemetry.mjs` auto-resolves the out-of-repo state directory, enabling brain hydration without manual `--state-dir` arguments.
- The S4 contradiction is resolved with a documented decision that aligns with the project's enforcement philosophy.
- Test coverage closes the gap for the `~/.atelier/pipeline` whitelist in enforce-eva-paths.sh.
- Cross-implementation contract test catches any bash/JS hash divergence before it causes silent data loss.

**Negative:**

- Two implementations of the slug/hash logic (bash and JS) create a maintenance surface. Mitigated by contract test. The logic is trivially small (6 lines).
- ADR-0022 R20 is now documented as superseded by this ADR for the Ellis-specific decision. Auditors reading ADR-0022 must follow the supersession chain.
- The `concurrent_session_detected` nonce system from ADR-0032 Step 1 is deferred indefinitely. The simpler `stale_context: true` check is the only concurrent-session signal.

**Neutral:**

- The `{pipeline_state_dir}` placeholder already existed in most rule files. This ADR completes the conversion for the remaining holdouts.
- `post-compact-reinject.sh` path comments become dynamic -- slightly harder to grep for but more accurate.

---

## Implementation Plan

### Step 1: Consumer File Placeholder Conversion (11 files, mechanical path substitution)

**Goal:** After this step, every agent, command, rule, reference, and dashboard file uses `{pipeline_state_dir}` for session-specific state files. No hardcoded `docs/pipeline/` references remain for pipeline-state.md, context-brief.md, investigation-ledger.md, or last-qa-report.md.

**Files (11):**

1. `source/shared/agents/roz.md` -- line 99: replace `docs/pipeline/last-qa-report.md` with `{pipeline_state_dir}/last-qa-report.md`.
2. `source/shared/commands/architect.md` -- line 22: replace `docs/pipeline/context-brief.md` with `{pipeline_state_dir}/context-brief.md`.
3. `source/shared/commands/devops.md` -- line 17: replace `docs/pipeline/context-brief.md` with `{pipeline_state_dir}/context-brief.md`.
4. `source/shared/commands/debug.md` -- line 22: replace `docs/pipeline/investigation-ledger.md` with `{pipeline_state_dir}/investigation-ledger.md`.
5. `source/shared/commands/pipeline.md` -- lines 19, 20, 138, 148: replace `docs/pipeline/pipeline-state.md` with `{pipeline_state_dir}/pipeline-state.md` and `docs/pipeline/context-brief.md` with `{pipeline_state_dir}/context-brief.md`. Lines 21, 153: `docs/pipeline/error-patterns.md` stays unchanged (shared file).
6. `source/shared/rules/pipeline-orchestration.md` -- line 400: replace `docs/pipeline` with `{pipeline_state_dir}` in state-files section header. Verify the investigation-discipline section (line 369) already uses `{pipeline_state_dir}` (it does). Verify the agent-standards section (line 625) already uses `{pipeline_state_dir}` (it does).
7. `source/shared/rules/agent-system.md` -- line 25: replace `docs/pipeline/pipeline-state.md` with `{pipeline_state_dir}/pipeline-state.md` in the brain-config state persistence reference.
8. `source/shared/references/qa-checks.md` -- line 82: replace `docs/pipeline/last-qa-report.md` with `{pipeline_state_dir}/last-qa-report.md`.
9. `source/shared/dashboard/telemetry-bridge.sh` -- line 19: update default `PIPELINE_STATE_PATH` to use `{pipeline_state_dir}/pipeline-state.md` in the comment. Since this is a bash script with a CLI `--pipeline-state` argument, also source `pipeline-state-path.sh` to resolve the default at runtime (falling back to `docs/pipeline/pipeline-state.md` if the helper is not available).
10. `source/claude/hooks/post-compact-reinject.sh` -- line 57: replace `echo "## From: docs/pipeline/pipeline-state.md"` with `echo "## From: $STATE_FILE"`. Line 64: replace `echo "## From: docs/pipeline/context-brief.md"` with `echo "## From: $BRIEF_FILE"`.
11. `source/shared/hooks/session-boot.sh` -- add `"state_dir": "$(json_escape "$STATE_DIR")"` to the JSON output template (after `deps_agent_enabled` field). Mirror the same change to `source/claude/hooks/session-boot.sh`.

**Acceptance criteria:**

- `grep -rn 'docs/pipeline/pipeline-state\.md\|docs/pipeline/context-brief\.md\|docs/pipeline/last-qa-report\.md\|docs/pipeline/investigation-ledger\.md' source/shared/agents/ source/shared/commands/ source/shared/rules/ source/shared/references/ source/shared/dashboard/` returns zero matches (excluding comments that explain the shared-file convention).
- `grep -rn 'docs/pipeline/error-patterns\.md' source/shared/commands/pipeline.md` returns exactly the expected shared-file references (lines 21, 153).
- `post-compact-reinject.sh` comments use `$STATE_FILE` and `$BRIEF_FILE` variables.
- `session-boot.sh` JSON output contains `state_dir` field.
- All existing hook tests pass (`pytest tests/hooks/`).

**Complexity:** 11 files. All mechanical path substitution -- no new logic, no new functions, no behavioral changes. Exceeds the 10-file threshold; justification below.

**Justification for 11 files exceeding the 10-file limit:**
S1 (demo): "After this step, every consumer file references state via placeholder, and session-boot reports the resolved path." Single coherent demo.
S2 (file count): 11 files. All changes are one-line path substitutions. No file introduces new logic. Splitting this step would create a window where some consumers use the placeholder and others use the hardcoded path -- an inconsistency that violates Retro Lesson #005 (orphan producers). The 3 additional files (agent-system.md, qa-checks.md, telemetry-bridge.sh) were found during implementation-time grep verification and must ship with the same step to avoid partial conversion.
S3 (testable): Each file is independently testable via grep.
S4 (revert): Each file reverts independently via `git checkout`.
S5 (single behavior): "Convert hardcoded `docs/pipeline/` to `{pipeline_state_dir}` placeholder." One vertical slice.

**After this step, I can:** grep the entire `source/shared/` tree and confirm no hardcoded `docs/pipeline/` references to session-specific files remain. The session-boot JSON tells Eva the resolved state directory path.

---

### Step 2: Hydrate-Telemetry State Dir Auto-Resolution (3 files)

**Goal:** After this step, `hydrate-telemetry.mjs` automatically resolves the out-of-repo state directory when `--state-dir` is not provided, and gracefully skips when the directory does not exist.

**Files (3):**

1. `brain/scripts/hydrate-telemetry.mjs` -- specific changes:
   - Add a new exported function `resolveAtelierStateDir(worktreeRoot)` near the existing `expandHome()`:
     ```
     // Takes an absolute worktree root path.
     // Returns ~/.atelier/pipeline/{slug}/{hash} if it exists, else null.
     // slug = basename(worktreeRoot)
     // hash = first 8 hex chars of sha256(worktreeRoot)
     ```
     Uses `crypto.createHash('sha256').update(worktreeRoot).digest('hex').slice(0, 8)`, `path.basename(worktreeRoot)`, `path.join(os.homedir(), '.atelier', 'pipeline', slug, hash)`. Returns the path only if `existsSync(stateDir)` is true; otherwise returns null.
   - In `main()`, around line 987: when `stateDirArg` is not provided, attempt auto-resolution:
     ```
     const worktreeRoot = process.env.CLAUDE_PROJECT_DIR || process.env.CURSOR_PROJECT_DIR || process.cwd();
     const autoStateDir = resolveAtelierStateDir(worktreeRoot);
     if (autoStateDir) {
       log("\nAuto-resolved state dir: " + autoStateDir);
       const stateInserted = await parseStateFiles(autoStateDir, pool, config, { silentMode });
       log(`State-file captures: ${stateInserted} new item(s) captured.`);
     }
     ```
   - At the top of `parseStateFiles()` (line 361), add an early-exit guard:
     ```
     if (!existsSync(stateDir)) {
       log(`  State dir not found: ${stateDir} (graceful skip)`);
       return 0;
     }
     ```
   - Update the JSDoc header (lines 7-12) to document the auto-resolution behavior.

2. `tests/brain/hydrate-telemetry-statedir.test.mjs` -- NEW. Tests:
   - `resolveAtelierStateDir` returns a path under `~/.atelier/pipeline/` for a valid worktree root where the directory exists.
   - `resolveAtelierStateDir` returns null when the directory does not exist.
   - `resolveAtelierStateDir` produces identical hashes to the bash helper for test paths (cross-implementation contract test -- calls the bash helper via `execSync` in the test only, not in production).
   - `parseStateFiles` returns 0 and does not throw when stateDir does not exist on disk.

3. `brain/scripts/hydrate-telemetry.mjs` -- add `resolveAtelierStateDir` to the exports list at line 1000.

**Note:** Items 1 and 3 are the same file. Total unique files: 2 (1 production + 1 test).

**Acceptance criteria:**

- `resolveAtelierStateDir('/Users/alice/projects/my-project')` returns `$HOME/.atelier/pipeline/my-project/{8-char-hash}` when that directory exists.
- `resolveAtelierStateDir('/nonexistent')` returns null.
- The JS and bash implementations produce the same 8-char hash for 5 test paths (contract test).
- `parseStateFiles('/nonexistent/dir', ...)` returns 0 and logs a graceful skip message.
- Explicit `--state-dir` still works (backward compat).
- `node --test tests/brain/hydrate-telemetry-statedir.test.mjs` passes.

**Complexity:** 2 unique files. S1: "After this step, brain hydration auto-discovers out-of-repo state files." S2: 2 files. S3: Independently testable. S4: One revert. S5: Already small.

**After this step, I can:** run `node brain/scripts/hydrate-telemetry.mjs <project-sessions-path>` without `--state-dir` and see it auto-discover and parse the out-of-repo state files.

---

### Step 3: S4 Resolution + Enforce-Eva-Paths Test Gap + Hard-Pause Protocol (5 files)

**Goal:** After this step, the S4 Ellis hook contradiction is documented and resolved, the `~/.atelier/pipeline` whitelist has test coverage, and the concurrent-session hard-pause protocol exists.

**Files (5):**

1. `source/claude/hooks/enforce-ellis-paths.sh` -- add header comments (lines 3-5):
   ```bash
   # Note: ADR-0022 R20 originally stated "no path hooks for Ellis."
   # ADR-0035 supersedes that decision. This hook is a safety net for
   # commit-related paths. Layer 3 sequencing is the primary control.
   ```

2. `tests/hooks/test_enforce_ellis_paths.py` -- update module docstring to reference ADR-0035 S4 resolution. No behavioral change to the tests themselves.

3. `tests/hooks/test_enforce_eva_paths.py` -- add 2 new tests:
   - `test_T_0035_001_atelier_pipeline_state_dir_allowed`: Eva writing to `$HOME/.atelier/pipeline/my-project/a1b2c3d4/pipeline-state.md` is allowed (exit 0).
   - `test_T_0035_002_atelier_pipeline_dir_not_too_permissive`: Eva writing to `$HOME/.atelier/pipeline/../../etc/passwd` is blocked (traversal check fires first).

4. `source/shared/rules/pipeline-orchestration.md` -- add a new section after the investigation-discipline section:

   ```markdown
   <protocol id="concurrent-session-hard-pause">

   ## Concurrent Session Detection

   At session boot, if `stale_context: true` AND the stale state's phase is not
   `idle` or `complete`, Eva HARD PAUSES and presents three options:

   1. **Adopt existing state** -- resume the other session's pipeline.
      Eva reads the existing pipeline-state.md and continues from the recorded
      phase.
   2. **Archive and start fresh** -- move the existing state aside.
      Eva runs: `mv "$STATE_DIR" "$STATE_DIR.archive-$(date +%s)"` and begins
      a clean pipeline in the newly-created empty state directory.
   3. **Cancel this session** -- stop without modifying state.
      Eva writes `stop_reason: user_cancelled` and transitions to idle.

   Eva records the user's choice in context-brief.md under "User Decisions"
   so downstream brain hydration captures it.

   This protocol fires only when stale state has an active pipeline phase.
   If `stale_context: true` but the phase is `idle` or `complete`, Eva
   announces the stale state and proceeds normally (the stale state is a
   finished pipeline from a prior session, not a concurrent one).

   </protocol>
   ```

5. `source/shared/rules/pipeline-orchestration.md` -- in the state-files section (line 400), change `Eva maintains five files in \`docs/pipeline\`:` to `Eva maintains five files in \`{pipeline_state_dir}\`:` and update the individual file descriptions to omit the `docs/pipeline/` prefix (they should be relative to `{pipeline_state_dir}`). Keep `error-patterns.md` description noting it stays at `docs/pipeline/error-patterns.md` (shared).

**Note:** Items 4 and 5 are the same file. Total unique files: 4 (2 source + 2 test).

**Acceptance criteria:**

- `enforce-ellis-paths.sh` has ADR-0035 supersession comment in header.
- `test_enforce_ellis_paths.py` docstring references ADR-0035.
- `test_enforce_eva_paths.py` has 2 new tests covering `~/.atelier/pipeline` paths; both pass.
- `pipeline-orchestration.md` contains `<protocol id="concurrent-session-hard-pause">` section with three options.
- `pipeline-orchestration.md` state-files section uses `{pipeline_state_dir}` not `docs/pipeline`.
- All existing hook tests pass.

**Complexity:** 4 unique files. S1: "After this step, S4 is resolved, Eva's out-of-repo whitelist is tested, and the hard-pause protocol is documented." S2: 4 files. S3: Independently testable. S4: Each file reverts independently. S5: Already small.

**After this step, I can:** read the enforce-ellis-paths.sh header and understand why the hook exists despite ADR-0022 R20. Run the new eva-paths tests and see the `~/.atelier/pipeline` whitelist verified. Read pipeline-orchestration.md and find the concurrent-session hard-pause protocol.

---

## Test Specification

### Step 1 Tests (grep-level verification)

| ID | Category | Description |
|----|----------|-------------|
| T-0035-001 | Regression | `grep -rn 'docs/pipeline/pipeline-state\.md' source/shared/agents/ source/shared/commands/ source/shared/rules/ source/shared/references/ source/shared/dashboard/` returns zero matches |
| T-0035-002 | Regression | `grep -rn 'docs/pipeline/context-brief\.md' source/shared/agents/ source/shared/commands/ source/shared/rules/ source/shared/references/ source/shared/dashboard/` returns zero matches |
| T-0035-003 | Regression | `grep -rn 'docs/pipeline/last-qa-report\.md' source/shared/agents/ source/shared/commands/ source/shared/rules/ source/shared/references/ source/shared/dashboard/` returns zero matches |
| T-0035-004 | Regression | `grep -rn 'docs/pipeline/investigation-ledger\.md' source/shared/agents/ source/shared/commands/ source/shared/rules/ source/shared/references/ source/shared/dashboard/` returns zero matches |
| T-0035-005 | Preservation | `grep -rn 'docs/pipeline/error-patterns\.md' source/shared/commands/pipeline.md` returns exactly 2 matches (lines 21 and 153) |
| T-0035-006 | Regression | `post-compact-reinject.sh` does not contain the string `## From: docs/pipeline/` (hardcoded path comments eliminated) |
| T-0035-007 | Feature | `session-boot.sh` JSON output template contains `"state_dir"` field |
| T-0035-008 | Regression | All existing pytest tests pass (`pytest tests/hooks/ -v`) |

### Step 2 Tests (hydrate-telemetry)

| ID | Category | Description |
|----|----------|-------------|
| T-0035-010 | Feature | `resolveAtelierStateDir('/tmp/test-project')` returns path matching `~/.atelier/pipeline/test-project/{8hex}` when directory exists |
| T-0035-011 | Feature | `resolveAtelierStateDir('/tmp/nonexistent')` returns null when directory does not exist |
| T-0035-012 | Contract | JS `resolveAtelierStateDir` produces the same 8-char hash as bash `session_state_dir` for 5 test paths: `/tmp/a`, `/Users/alice/projects/my-project`, `/home/bob/work/atelier-pipeline`, `/tmp/path with spaces`, `/tmp/path-with-unicode-` |
| T-0035-013 | Graceful | `parseStateFiles('/nonexistent/dir', pool, config)` returns 0 and does not throw |
| T-0035-014 | Backward | `hydrate-telemetry.mjs` invoked with explicit `--state-dir /tmp/test` still reads from `/tmp/test` (not auto-resolved path) |
| T-0035-015 | Feature | `hydrate-telemetry.mjs` invoked WITHOUT `--state-dir` but with `CLAUDE_PROJECT_DIR` set auto-resolves and parses state files from the out-of-repo path |
| T-0035-016 | Graceful | `hydrate-telemetry.mjs` invoked WITHOUT `--state-dir` and WITHOUT env vars falls back gracefully (no crash, logs skip message) |
| T-0035-017 | Regression | All existing brain tests pass (`cd brain && node --test ../tests/brain/*.test.mjs`) |

### Step 3 Tests (S4 + eva-paths + hard-pause)

| ID | Category | Description |
|----|----------|-------------|
| T-0035-020 | Feature | Eva writing to `$HOME/.atelier/pipeline/my-project/a1b2c3d4/pipeline-state.md` is allowed by enforce-eva-paths.sh (exit 0) |
| T-0035-021 | Security | Eva writing to `$HOME/.atelier/pipeline/../../etc/passwd` is blocked by enforce-eva-paths.sh (traversal, exit 2) |
| T-0035-022 | S4 | `enforce-ellis-paths.sh` header contains "ADR-0035" comment |
| T-0035-023 | S4 | `test_enforce_ellis_paths.py` docstring contains "ADR-0035" reference |
| T-0035-024 | Feature | `pipeline-orchestration.md` contains `<protocol id="concurrent-session-hard-pause">` |
| T-0035-025 | Feature | Concurrent-session protocol specifies exactly 3 user options |
| T-0035-026 | Regression | `pipeline-orchestration.md` state-files section uses `{pipeline_state_dir}` not `docs/pipeline` |
| T-0035-027 | Regression | All existing hook tests pass (`pytest tests/hooks/ -v`) |

**Failure-path tests >= happy-path tests:** 9 failure/security/graceful tests (T-0035-002, T-0035-003, T-0035-004, T-0035-006, T-0035-011, T-0035-013, T-0035-016, T-0035-021, T-0035-026) vs. 8 happy-path/feature tests.

---

## UX Coverage

No UX doc exists for this feature (infrastructure/enforcement work). N/A.

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| `session_state_dir()` (bash) | absolute path string `~/.atelier/pipeline/{slug}/{8hex}/` | session-boot.sh, post-compact-reinject.sh, all downstream Eva writes |
| `resolveAtelierStateDir()` (JS) | absolute path string or null | hydrate-telemetry.mjs main(), brain/lib/hydrate.mjs (future) |
| session-boot.sh `state_dir` field | JSON string in boot output | Eva boot sequence (reads JSON, uses path for state writes) |
| `{pipeline_state_dir}` placeholder | string resolved at install time | All agent/command/rule files that reference session-specific state |

**Cross-implementation contract:** The bash `session_state_dir()` and JS `resolveAtelierStateDir()` must produce identical paths for the same worktree root input. Verified by T-0035-012.

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `{pipeline_state_dir}` placeholder in agent/command/rule/reference/dashboard files | path string | Eva at invocation time (provides actual path via `<read>` tag) | Step 1 |
| session-boot.sh `state_dir` JSON field | string | Eva boot sequence | Step 1 |
| post-compact-reinject.sh `$STATE_FILE`/`$BRIEF_FILE` vars | path string in comment header | Eva post-compaction context | Step 1 |
| `resolveAtelierStateDir()` JS function | path or null | hydrate-telemetry.mjs `main()` | Step 2 |
| `resolveAtelierStateDir()` export | function | brain/lib/hydrate.mjs (future consumer, documented) | Step 2 |
| `parseStateFiles()` early-exit guard | returns 0 | hydrate-telemetry.mjs caller (avoids ENOENT) | Step 2 |
| enforce-ellis-paths.sh ADR-0035 comment | documentation | Human auditors, future ADR readers | Step 3 |
| enforce-eva-paths.sh `~/.atelier/pipeline` whitelist | test coverage | CI (pytest) | Step 3 |
| concurrent-session hard-pause protocol | markdown section | Eva orchestration behavior | Step 3 |

No orphan producers. Every producer has a consumer in the same or earlier step.

## Data Sensitivity

| Method/Path | Classification | Notes |
|-------------|---------------|-------|
| `session_state_dir()` | `public-safe` | Returns a filesystem path. No secrets. |
| `resolveAtelierStateDir()` | `public-safe` | Returns a filesystem path. No secrets. |
| `error_patterns_path()` | `public-safe` | Returns a fixed relative path. |
| session-boot.sh `state_dir` field | `public-safe` | Filesystem path in hook output. |
| Pipeline state file contents | `auth-only` | Contains feature names, phase info, user decisions. Written only by Eva (enforcement verified). |

## Notes for Colby

1. **Step 1 is pure find-and-replace.** Every edit is `docs/pipeline/{filename}` -> `{pipeline_state_dir}/{filename}`. The exception is `error-patterns.md` which stays at `docs/pipeline/`. Colby: do NOT touch `error-patterns.md` references. Grep after your edits to verify zero remaining hardcoded session-specific references.

2. **Step 1 session-boot.sh has two copies.** `source/shared/hooks/session-boot.sh` and `source/claude/hooks/session-boot.sh`. Both need the `state_dir` field added. Diff them first -- they should be identical or near-identical. If they differ, match the change pattern.

3. **Step 2 hydrate-telemetry.mjs: do not refactor.** Add `resolveAtelierStateDir()` near the top (after `expandHome`). Wire it into `main()`. Add the `existsSync` guard at the top of `parseStateFiles()`. Three surgical additions. Do not move functions, rename things, or restructure the file.

4. **Step 2 contract test: shell out in the TEST, not in production.** The test calls both the JS function and the bash helper (via subprocess) with the same input paths and asserts the hashes match. The production code never shells out to bash.

5. **Step 3 enforce-ellis-paths.sh: documentation only.** Add the ADR-0035 comment to the header. Do not change any enforcement behavior.

6. **Step 3 pipeline-orchestration.md: two changes in one file.** (a) Add the `concurrent-session-hard-pause` protocol section. (b) Fix the state-files section to use `{pipeline_state_dir}`. These are independent edits within the same file.

7. **Step 1 has 3 extra files found during ADR authoring.** `agent-system.md:25`, `qa-checks.md:82`, and `telemetry-bridge.sh:19` were found by grep during ADR production and added to Step 1. The step is now 11 files but remains pure path substitution. Colby: run `grep -rn 'docs/pipeline/' source/shared/` after your edits to catch any this ADR also missed. If you find more, fix them in Step 1 and note additions in DoD.

8. **Brain pattern:** ADR-0032 Step 1 shipped the path resolver and all hook wiring. ADR-0035 finishes the consumer side. This is the "producer then consumer" vertical-slice pattern from Retro Lesson #005.

9. **Cross-implementation hash verification paths for T-0035-012:** Use these 5 paths: `/tmp/a`, `/Users/alice/projects/my-project`, `/home/bob/work/atelier-pipeline`, `/tmp/path with spaces`, `/tmp/unicode-`. The test creates temporary directories at the `~/.atelier/pipeline/` locations so `existsSync` returns true during testing, then cleans them up.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | hydrate-telemetry auto-resolves state dir | Addressed | Step 2: `resolveAtelierStateDir()` + main() wiring |
| R2 | parseStateFiles graceful exit on missing dir | Addressed | Step 2: `existsSync(stateDir)` guard |
| R3 | Backward compat with explicit `--state-dir` | Addressed | Step 2: explicit arg takes precedence over auto-resolve |
| R4 | Agent personas use `{pipeline_state_dir}` | Addressed | Step 1: roz.md update |
| R5 | Command files use `{pipeline_state_dir}` | Addressed | Step 1: architect.md, devops.md, debug.md, pipeline.md |
| R6 | pipeline-orchestration.md path distinction | Addressed | Step 1 (state-files section) + Step 3 |
| R7 | enforce-eva-paths `~/.atelier` test coverage | Addressed | Step 3: T-0035-020, T-0035-021 |
| R8 | post-compact path comments dynamic | Addressed | Step 1: `$STATE_FILE`/`$BRIEF_FILE` interpolation |
| R9 | Concurrent-session hard-pause protocol | Addressed | Step 3: pipeline-orchestration.md section |
| R10 | S4 Ellis hook contradiction resolved | Addressed | Step 3: ADR-0035 comment + docstring update |
| R11 | session-boot `state_dir` field | Addressed | Step 1: JSON output template |
| R12 | debug.md placeholder conversion | Addressed | Step 1: investigation-ledger.md reference |
| R13 | roz.md placeholder conversion | Addressed | Step 1: last-qa-report.md reference |
| R14 | pipeline-orchestration state-files section | Addressed | Step 3: `{pipeline_state_dir}` replacement |
| R15 | agent-system.md brain-config section | Addressed | Step 1: line 25 placeholder conversion |
| R16 | telemetry-bridge.sh default path | Addressed | Step 1: default + runtime resolution |
| R17 | qa-checks.md last-qa-report reference | Addressed | Step 1: line 82 placeholder conversion |

**Grep check:** TODO/FIXME/HACK/XXX in this ADR -> 0.
**Template:** All sections filled -- no TBD, no placeholders.

**No silent drops.** Every requirement has a step and test coverage.
