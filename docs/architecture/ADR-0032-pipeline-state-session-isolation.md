# ADR-0032: Pipeline State Session Isolation

## DoR: Requirements Extracted

**Sources:** Scout research brief (fan-out findings), `source/claude/hooks/session-boot.sh` (boot-time state reader), `source/claude/hooks/post-compact-reinject.sh` (post-compaction re-injection), `brain/scripts/hydrate-telemetry.mjs` (`parseStateFiles` function, lines 344-485), `source/shared/pipeline/pipeline-state.md` (state file template), `source/shared/pipeline/context-brief.md` (context file template), `source/claude/hooks/enforce-eva-paths.sh` (out-of-repo whitelist precedent, lines 31-39), `.claude/references/retro-lessons.md`, `.claude/references/dor-dod.md`, ADR-0031 (recent ADR format reference).

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Concurrent Claude Code sessions in the same worktree must not clobber each other's pipeline state | Task brief | Clobber scenario section |
| R2 | Agent Teams worktrees (distinct filesystem paths) must be isolated from each other and from the main checkout | Task brief | Worktree case section |
| R3 | `error-patterns.md` must remain cross-session shared (accumulates across runs; session-boot reads it to build `warn_agents[]`) | Task brief + session-boot.sh lines 65-74 | Constraint list |
| R4 | Fix must work for Cursor (no SessionStart hook, no session IDs) | Task brief | Scout finding |
| R5 | Fix must not require manual cleanup between sessions | Task brief | Constraint list |
| R6 | `session-boot.sh` must be updated | Task brief | Constraint list |
| R7 | `post-compact-reinject.sh` must be updated if paths change | Task brief | Constraint list |
| R8 | `hydrate-telemetry.mjs` `parseStateFiles()` must be updated if paths change; must gracefully degrade when state dir is empty | Task brief + hydrate-telemetry.mjs lines 361-485 | Constraint list, existing `existsSync` guards |
| R9 | All agent persona required-reading references to `context-brief.md` must still resolve (cal.md, colby.md, architect.md, devops.md) | Scout research brief | Readers that must be updated |
| R10 | State isolation must not depend on Claude Code session IDs (they don't exist in Cursor) | Task brief | R4 is the hard constraint that eliminates option D |
| R11 | Staleness detection between pipeline-state.md and context-brief.md (same feature name) must still work | session-boot.sh lines 54-62 | Current behavior |
| R12 | Four strategies must be evaluated explicitly with tradeoffs: (A) branch subdirs, (B) worktree-path hash subdirs, (C) out-of-repo per-worktree, (D) session_id + lock | Task brief | Constraint list |
| R13 | No new git-tracked files per session (session-specific state must not pollute the repo) | Derived from R5 + clobber scenario | Implied |
| R14 | The implementation plan must list exactly what changes in each file (not "update X") | Task brief | Output spec |
| R15 | Test spec must cover: two concurrent sessions, error-patterns sharing, staleness, Cursor, worktrees, hydrate-telemetry empty-dir degradation | Task brief | Output spec |

**Retro risks:**

- **Lesson #003 (Stop Hook Race Condition):** `session-boot.sh` is a SessionStart hook. Any isolation logic added to it must remain non-blocking, filesystem-local, and exit 0 on every error path. A hash computation and `mkdir -p` are both cheap and local. No network, no brain calls, no locking primitives that could stall.
- **Lesson #005 (Frontend Wiring Omission):** The producer (new out-of-repo state directory) must be wired to every consumer in the same step. Consumers are: `session-boot.sh`, `post-compact-reinject.sh`, `hydrate-telemetry.mjs`, Eva's write paths (pipeline-orchestration.md mentions of file locations), and agent required-reading references (cal.md, colby.md, architect.md, devops.md, roz.md). A producer that relocates files without updating every consumer is an orphan path.
- **Lesson #001 (Sensitive Data in Return Shapes):** Not directly applicable, but the Data Sensitivity section must still classify the new out-of-repo state path.

**Spec challenge:** The spec (task brief) assumes that all five state files are roughly equivalent "session state" and differ only in whether they should be shared or per-session. **This is wrong in one load-bearing way.** `session-boot.sh` resolves `CONFIG_DIR` via `if [ -d ".claude" ]` with current working directory (line 34) and reads `docs/pipeline/pipeline-state.md` with a hardcoded relative path (line 41). It does NOT use `CLAUDE_PROJECT_DIR`. `post-compact-reinject.sh` DOES use `CLAUDE_PROJECT_DIR` (line 18). If the design computes the worktree hash from the project root in one place and from `$PWD` in another, the two hooks will write to and read from different directories -- split-brain at a different level. Mitigation: the new path resolution is centralized in a single helper script (`pipeline-state-path.sh`) that both hooks source. The helper always resolves the worktree root via `CLAUDE_PROJECT_DIR`/`CURSOR_PROJECT_DIR` with a `pwd` fallback, and both hooks use the same helper output. If the helper fails to locate the worktree root, both hooks degrade to the legacy `docs/pipeline/` path (backward compatible).

**SPOF:** The worktree-root resolution function in the shared helper. Failure mode: `CLAUDE_PROJECT_DIR`, `CURSOR_PROJECT_DIR`, and `pwd` all return different or empty values under an unusual invocation context (e.g., a hook fired from a sub-shell with a changed CWD). Graceful degradation: the helper emits the legacy in-repo path (`docs/pipeline/`) on any resolution failure. In that case, the worktree falls back to pre-ADR-0032 behavior (clobber risk returns) but nothing breaks -- every existing consumer still works against `docs/pipeline/`. The SPOF degrades the ISOLATION GUARANTEE, not the pipeline itself.

**Anti-goals:**

1. Anti-goal: Using Claude Code session IDs as the scoping key. Reason: Cursor has no SessionStart hook and no equivalent session ID mechanism. A design that works only on Claude Code creates two forks of the state-isolation story and violates R4. Revisit: Never (or only if Cursor adds an equivalent primitive).

2. Anti-goal: Introducing file locking (`flock`, lock files, semaphores). Reason: Lock-based coordination requires stale-lock detection, timeout handling, and recovery logic. The existing codebase has no locking primitives (scout confirmed). Adding them to `session-boot.sh` violates Retro Lesson #003 (non-blocking SessionStart) and creates a new class of failure (zombie locks from crashed sessions). Isolation via distinct filesystem paths is simpler, lock-free, and naturally survives process crashes. Revisit: If concurrent writes to the SAME isolated directory become an issue -- but that requires multiple processes acting as the same worktree, which is outside the threat model.

3. Anti-goal: Moving `error-patterns.md` into per-session isolation. Reason: `error-patterns.md` accumulates StopFailure entries across runs. `session-boot.sh` lines 65-74 read it to compute `warn_agents[]` and inject WARN entries into agent invocations when a pattern recurs 3+ times. Per-session isolation of `error-patterns.md` would reset the recurrence counter every session -- the WARN system would never fire. `error-patterns.md` stays in `docs/pipeline/` (git-tracked, shared, intentionally cross-session). Revisit: Never -- this is a load-bearing cross-session primitive.

---

## Status

Proposed — Roz round 1 addressed; pending Roz re-review.

**Depends on:** None (self-contained).
**Supersedes:** None.
**Related:** ADR-0031 (Permission Audit Trail) established the "out-of-repo state at `~/.claude/...`" precedent that this ADR extends.

## Context

The pipeline currently stores five state files in `docs/pipeline/`, all git-tracked, none in `.gitignore`:

| File | Purpose | Session scope |
|------|---------|---------------|
| `pipeline-state.md` | `PIPELINE_STATUS` JSON: phase, sizing, roz_qa, telemetry_captured, stop_reason, telemetry_pipeline_id, brain_available | Session-specific |
| `context-brief.md` | Scope, Key Constraints, User Decisions, Rejected Alternatives | Session-specific |
| `error-patterns.md` | StopFailure entries, recurrence counter -- feeds `warn_agents[]` | **Cross-session (shared)** |
| `investigation-ledger.md` | Hypothesis tracking (debug mode only) | Session-specific |
| `last-qa-report.md` | Roz's per-wave verdict | Session-specific |

**The clobber scenario:**

1. Session A is running Feature X. It writes `pipeline-state.md` (`feature: X`), `context-brief.md` (scope: X), `last-qa-report.md` (Roz's verdict for wave 3 of X).
2. The user opens a second Claude Code session (Session B) in the same directory and starts Feature Y via `/pipeline`.
3. Session B resets `pipeline-state.md` to `feature: Y` and writes a fresh `context-brief.md` for Y.
4. Session A resumes work. `session-boot.sh` does not fire (only SessionStart). Eva re-reads `context-brief.md` mid-session as part of her always-loaded protocol and now sees Y's constraints under A's in-memory belief that she is running X.
5. Eva invokes Colby with X's task but Y's constraints from `context-brief.md`. Split-brain.

**The worktree case:**

Agent Teams spawn Colby Teammate workers via `git worktree add`. Each worktree is a distinct filesystem path but shares the same underlying repository. All worktrees resolve `docs/pipeline/pipeline-state.md` to the SAME relative path within their own worktree -- but the content of pipeline-state.md in each worktree is tracked independently unless committed. This is actually slightly safer than the concurrent-sessions case because worktrees have distinct on-disk copies, but:

- Concurrent sessions in DIFFERENT worktrees writing to `docs/pipeline/` do so in different directories (isolated by git worktree semantics).
- Concurrent sessions in the SAME worktree (or the main checkout) clobber each other.

The worktree case is already somewhat isolated by virtue of distinct filesystem paths. The remaining risk is two sessions opened in the exact same worktree -- which is the general clobber scenario.

**Readers of the state files:**

- `source/claude/hooks/session-boot.sh` (SessionStart, reads all three shared files by relative path)
- `source/claude/hooks/post-compact-reinject.sh` (PostCompact, re-injects pipeline-state.md + context-brief.md)
- `brain/scripts/hydrate-telemetry.mjs` `parseStateFiles()` (reads pipeline-state.md + context-brief.md, already guards with `existsSync`)
- `source/shared/agents/cal.md` required-reading: "Read context-brief.md"
- `source/shared/agents/colby.md` required-reading: "Read context-brief.md"
- `source/shared/commands/architect.md` required-reading
- `source/shared/commands/devops.md` required-reading
- `source/shared/rules/default-persona.md` (Eva's always-loaded protocol)

**No session/worktree scoping exists anywhere.** The staleness check in `session-boot.sh` (lines 54-62) compares the `feature` field in `pipeline-state.md` against the "feature" line in `context-brief.md`. That catches cross-file mismatch within one session but is invisible to a second session that rewrites both files consistently with its own (wrong, from A's perspective) feature.

**Out-of-repo precedent:** `enforce-eva-paths.sh` already whitelists writes to `${HOME}/.claude/projects/*/memory/*` (lines 31-39). There is a working, reviewed precedent for out-of-repo Claude state at that path. ADR-0031's enforcement log at `~/.claude/logs/enforcement-{DATE}.jsonl` is a second precedent.

**The Cursor constraint:** Cursor has no SessionStart hook and no session ID primitive. The only Cursor hook is PreToolUse path enforcement. Any design requiring session IDs is DOA for Cursor. This eliminates option (D) outright.

## Decision

**Adopt Strategy C (modified): Out-of-repo per-worktree session state directory, with `error-patterns.md` staying in-repo.**

### Path Scheme

```
# Session-specific files (per-worktree, out-of-repo, untracked)
~/.atelier/pipeline/{project_slug}/{worktree_hash}/
  ├── pipeline-state.md
  ├── context-brief.md
  ├── investigation-ledger.md
  └── last-qa-report.md

# Cross-session shared file (in-repo, git-tracked)
<worktree>/docs/pipeline/
  └── error-patterns.md
```

Where:
- `{project_slug}` = project name derived from `git remote get-url origin` basename (same logic as `session-boot.sh` lines 96-103), sanitized to `[a-zA-Z0-9_-]+`
- `{worktree_hash}` = first 8 hex chars of `sha256(absolute_worktree_root_path)`

The absolute worktree root path is the key insight: git worktrees have distinct on-disk paths (`git worktree add` creates a new directory), and the main checkout has yet another path. Hashing the absolute path naturally isolates:
- Session A in `/Users/robert/projects/atelier` → hash X
- Session B in `/Users/robert/projects/atelier` → same hash X (same worktree, still clobbers within the worktree pair, but...)
- Main checkout vs `git worktree add ../atelier-feat-y` → different hashes

**Remaining clobber risk in the "same worktree, two sessions" case:** Two sessions opened on the same worktree path still resolve to the same hash directory. This is by design -- see Alternative C in the alternatives section for why introducing session IDs here violates R4 (Cursor compatibility). The mitigation for the same-worktree case is the staleness detection enhancement described below, which now compares more than just feature names.

### Enhanced Staleness Detection

Current `session-boot.sh` staleness check compares only the `feature` field between `pipeline-state.md` and `context-brief.md`. Because the new path is per-worktree and survives across sessions within the same worktree, we add a second staleness signal: a `session_marker` file.

- On every Eva invocation that writes `pipeline-state.md`, Eva also writes `{stateDir}/.session-marker` containing an ISO timestamp + a random 16-hex-char nonce (generated once per Eva boot).
- `session-boot.sh` reads `.session-marker` at SessionStart. If present AND the nonce in the marker does not match the current session's nonce (generated at boot), AND the marker's timestamp is less than 2 hours old, `session-boot.sh` emits `stale_context: true` AND adds a new field `concurrent_session_detected: true` to its JSON output.
- Eva, on seeing `concurrent_session_detected: true`, HARD PAUSES and asks the user: "Another session wrote pipeline state within the last 2 hours. Options: (1) Adopt the existing state (resume the other session's work), (2) Archive the existing state and start fresh, (3) Cancel this session."

The 2-hour window is chosen because: (a) pipelines rarely run that long, (b) a stale marker older than 2 hours is very likely a crashed session, not a concurrent one, (c) session-boot.sh should not pause on false positives from old idle sessions.

### Legacy Path Fallback

If the worktree-root resolution fails (all three sources -- `CLAUDE_PROJECT_DIR`, `CURSOR_PROJECT_DIR`, `pwd` -- return unusable values), the helper falls back to `./docs/pipeline/` (legacy path). This preserves backward compatibility: a user with a broken or unusual invocation context still gets working state files, at the cost of the isolation guarantee.

Additionally, on first invocation where the new path is empty but the legacy path contains files, `session-boot.sh` performs a ONE-TIME migration: copy the four session-specific files from `docs/pipeline/` to the new out-of-repo path (leaving the originals in place for backward compatibility until a future cleanup ADR). This ensures upgrading users do not lose in-progress pipeline state.

### Shared Helper Script

A new helper `source/claude/hooks/pipeline-state-path.sh` is sourced by `session-boot.sh`, `post-compact-reinject.sh`, and any future hook that reads pipeline state. It exports:

- `ATELIER_STATE_DIR` -- resolved absolute path to the per-worktree state directory
- `ATELIER_SHARED_DIR` -- resolved absolute path to the in-repo `docs/pipeline/` directory (for `error-patterns.md`)
- `ATELIER_STATE_FALLBACK` -- `"true"` if the helper fell back to the legacy path, `"false"` otherwise

### Eva Write Path Change

Eva's enforcement hook (`enforce-eva-paths.sh`) currently whitelists writes to `docs/pipeline/*` and to `${HOME}/.claude/projects/*/memory/*`. We add a third whitelist entry for `${HOME}/.atelier/pipeline/*`. Eva's writes to the new out-of-repo path are mechanically allowed; writes to `docs/pipeline/error-patterns.md` continue to be allowed (shared file); writes to other `docs/pipeline/*` files are still allowed during a transition grace period (legacy fallback).

### Contract Shape: pipeline-state-path.sh Output

```bash
# Sourced by other scripts. Sets these env vars:
export ATELIER_STATE_DIR="/Users/alice/.atelier/pipeline/atelier-pipeline/a1b2c3d4"
export ATELIER_SHARED_DIR="/Users/alice/projects/atelier-pipeline/docs/pipeline"
export ATELIER_STATE_FALLBACK="false"
```

On fallback:
```bash
export ATELIER_STATE_DIR="/Users/alice/projects/atelier-pipeline/docs/pipeline"
export ATELIER_SHARED_DIR="/Users/alice/projects/atelier-pipeline/docs/pipeline"
export ATELIER_STATE_FALLBACK="true"
```

## Alternatives Considered

### Alternative A: Branch-scoped subdirectories inside `docs/pipeline/`

Pattern: `docs/pipeline/{branch-name}/pipeline-state.md`

**Pros:**
- Stays in-repo; no new path conventions.
- Naturally aligns with developer mental model ("each branch has its own state").
- Works for Cursor (no session IDs needed).
- Git-tracked, so state travels with the branch.

**Cons:**
- **Concurrent sessions on the SAME branch still clobber.** Branch is not a per-session key. A developer running two sessions on `main` -- which is common -- is back to the original bug.
- Git-tracking session-specific files pollutes the repo. Every pipeline run commits (or dirties) a `docs/pipeline/{branch}/*` directory. `last-qa-report.md` and `investigation-ledger.md` should not be committed at all.
- Branch names can contain characters that are invalid or awkward as directory names (`/`, spaces, non-ASCII). Sanitization adds complexity.
- Switching branches mid-pipeline (which Agent Teams do) causes state files to "disappear" unless the hook copies them to the new branch's subdir.
- Requires `.gitignore` entries to prevent session-specific files from being committed, but `error-patterns.md` must NOT be ignored -- mixed `.gitignore` patterns inside one subtree are error-prone.

**Rejected because:** Branch is not a session key (R1 fails on same-branch concurrent sessions) AND git-tracking session state is an active disadvantage (R13).

### Alternative B: Worktree-path hash scoping inside `docs/pipeline/`

Pattern: `docs/pipeline/{sha8-of-worktree-path}/pipeline-state.md`

**Pros:**
- Worktree-path hashing naturally isolates Agent Teams worktrees and the main checkout.
- Works for Cursor.
- All state stays in one directory tree.

**Cons:**
- **Still in-repo.** Git-tracking per-worktree hashed subdirectories means every worktree commits (or dirties) a different subdirectory. On merge, the main branch accumulates stale per-worktree directories forever. `git status` becomes noisy.
- `.gitignore` can exclude them, but then the worktree hash subdirectories exist only in the working tree -- which defeats the main claim of "state stays in one directory tree."
- The same-worktree concurrent-session case is not solved (same hash, same clobber).
- Adds a confusing layer to the repo structure. Developers opening `docs/pipeline/` see cryptic hash subdirectories and have to figure out which one is theirs.

**Rejected because:** In-repo hashed subdirectories are worse than in-repo branch subdirectories (no semantic meaning) and worse than out-of-repo hashed subdirectories (pollute the repo). Alternative C has all of B's advantages without the repo pollution.

### Alternative C (CHOSEN): Out-of-repo per-worktree at `~/.atelier/pipeline/{project}/{worktree_hash}/`

See Decision section for the full design.

**Pros:**
- Session-specific files never touch the repo. No `.gitignore` gymnastics.
- Worktree hashing provides natural isolation for Agent Teams and distinct checkouts.
- `error-patterns.md` stays in-repo where it belongs (cross-session, git-tracked).
- Out-of-repo precedent already exists (`~/.claude/logs/`, `~/.claude/projects/*/memory/`).
- Works for Cursor (no session IDs used as the scoping key).
- Legacy fallback path preserves backward compatibility on unusual invocation contexts.
- Small, mechanical migration from the old layout.

**Cons:**
- Two different directories to remember (in-repo `docs/pipeline/` for `error-patterns.md`, out-of-repo for everything else). Mitigated by the shared helper script.
- State does not travel with the branch or the repo. If a developer archives the project and sends it to a colleague, the pipeline state does not go with it. This is almost always desirable (stale pipeline state is a bug source), but it is a behavior change.
- Same-worktree concurrent-session case requires the enhanced staleness detection (additional complexity).
- Requires updates to every consumer that currently hardcodes `docs/pipeline/` (enumerated in the implementation plan).

**Accepted because:** This is the only option that satisfies R1, R2, R3, R4, R5, R10, and R13 simultaneously. The complexity cost is concentrated in one shared helper and well-documented consumer updates.

### Alternative D: Embedding `session_id` in `PIPELINE_STATUS` JSON + advisory lock file `docs/pipeline/.pipeline.lock`

Pattern: Each session generates a UUID at boot. `PIPELINE_STATUS` JSON gets a `session_id` field. `docs/pipeline/.pipeline.lock` contains the active session_id + timestamp. Any session that reads `pipeline-state.md` and finds a different `session_id` than the lock file warns and bails out.

**Pros:**
- Simple mental model: "one active session owns the lock."
- Works with minimal file-layout changes.

**Cons:**
- **Cursor has no session ID primitive.** There is no reliable way to generate a per-session ID in Cursor that survives across hook invocations. Any workaround (e.g., hashing `pwd + timestamp`) either collides across concurrent sessions or changes during a single session -- both break the mechanism. R4 fails outright.
- Lock files introduce stale-lock recovery (what if the owning session crashed?). Hook scripts become more complex.
- Two sessions still race on writing `pipeline-state.md`; the lock file only detects the race after the fact.
- Lock-based coordination in a SessionStart hook violates Retro Lesson #003 (non-blocking).

**Rejected because:** Cursor-incompatible (R4, R10 fail). Lock-file complexity on the enforcement path violates retro lesson #003.

## Consequences

**Positive:**
- Concurrent sessions in different worktrees are fully isolated. Agent Teams worker state does not leak to the main checkout.
- `error-patterns.md` remains cross-session shared (R3 satisfied), preserving the `warn_agents[]` recurrence signal.
- Cursor fully supported (R4 satisfied). No session ID or platform-specific primitive used as the scoping key.
- Session-specific files never touch the repo (R13 satisfied). No `.gitignore` changes needed.
- Same-worktree concurrent-session case is detected and surfaces to the user as an explicit hard pause, not silent clobber.
- Legacy path fallback preserves backward compatibility for unusual invocation contexts.
- One-time migration on first upgrade: no manual cleanup (R5 satisfied).

**Negative:**
- Two directory locations to track (out-of-repo session state + in-repo `error-patterns.md`). Mitigated by the shared helper script, but required-reading references in agent personas now need to use a placeholder (resolved by Eva at invocation time) rather than a hardcoded path.
- State files do not travel with the repo. Archiving the repo no longer archives pipeline state. For most cases this is desirable, but it is a behavior change.
- Wide blast radius: ~10 files need updates (session-boot, post-compact, hydrate-telemetry, enforce-eva-paths, agent personas with required-reading references, command required-reading references). All updates are mechanical path-substitution.
- Users with multiple atelier-pipeline projects will see `~/.atelier/pipeline/` accumulate subdirectories over time. Cleanup is manual (not automated in this ADR).

**Neutral:**
- The shared helper script is a new file (`pipeline-state-path.sh`) but follows the existing bash-hook pattern.
- Eva's `enforce-eva-paths.sh` gains a third whitelist entry -- mechanically identical to the existing `${HOME}/.claude/projects/*/memory/*` whitelist.

---

## Implementation Plan

### Step 1: Shared helper + session-boot + post-compact (atomic vertical slice)

This step establishes the new path scheme and wires it through both SessionStart (boot) and PostCompact (re-inject) paths in a single commit. These two hooks are the primary producers of "where does state live" and must not diverge.

**Files to create (1):**

1. `source/claude/hooks/pipeline-state-path.sh` -- shared helper, sourced by other hooks. Exports `ATELIER_STATE_DIR`, `ATELIER_SHARED_DIR`, `ATELIER_STATE_FALLBACK`. Contains:
   - `resolve_worktree_root()` function -- tries `CLAUDE_PROJECT_DIR`, then `CURSOR_PROJECT_DIR`, then `pwd`, returns the first non-empty valid absolute path or empty on total failure.
   - `resolve_project_slug()` function -- runs `git -C "$WORKTREE_ROOT" remote get-url origin 2>/dev/null | xargs -I{} basename {} .git`, falls back to `basename "$WORKTREE_ROOT"`, sanitizes the result via `tr -c 'a-zA-Z0-9_-' '-'`.
   - `resolve_worktree_hash()` function -- `printf '%s' "$WORKTREE_ROOT" | shasum -a 256 | cut -c1-8` (falls back to `sha256sum` if `shasum` missing; falls back to `openssl dgst -sha256` if both missing).
   - Main logic: if all three resolvers succeed, set `ATELIER_STATE_DIR="$HOME/.atelier/pipeline/$SLUG/$HASH"` and `ATELIER_STATE_FALLBACK="false"`. Otherwise set `ATELIER_STATE_DIR="$WORKTREE_ROOT/docs/pipeline"` and `ATELIER_STATE_FALLBACK="true"`.
   - Always set `ATELIER_SHARED_DIR="$WORKTREE_ROOT/docs/pipeline"` (or `./docs/pipeline` if even that fails).
   - `mkdir -p "$ATELIER_STATE_DIR" 2>/dev/null || true` at the end (ensure directory exists, fail-open).
   - One-time migration block: if `ATELIER_STATE_FALLBACK="false"` AND `ATELIER_STATE_DIR` is empty (no `pipeline-state.md` present) AND `$WORKTREE_ROOT/docs/pipeline/pipeline-state.md` exists, copy `pipeline-state.md`, `context-brief.md`, `investigation-ledger.md`, `last-qa-report.md` (each guarded with `-f`) from the in-repo path to the new path. Do NOT delete the originals (backward compat). Do NOT copy `error-patterns.md` (it stays in-repo).

**Files to modify (3):**

2. `source/claude/hooks/session-boot.sh` -- specific changes:
   - After line 38 (`CONFIG_DIR` resolution), insert `source "$(dirname "${BASH_SOURCE[0]}")/pipeline-state-path.sh" 2>/dev/null || true`.
   - Line 41: change `PIPELINE_STATE_FILE="docs/pipeline/pipeline-state.md"` to `PIPELINE_STATE_FILE="${ATELIER_STATE_DIR:-docs/pipeline}/pipeline-state.md"`.
   - Line 54: change `CONTEXT_BRIEF="docs/pipeline/context-brief.md"` to `CONTEXT_BRIEF="${ATELIER_STATE_DIR:-docs/pipeline}/context-brief.md"`.
   - Line 65: `ERROR_PATTERNS` stays at `"${ATELIER_SHARED_DIR:-docs/pipeline}/error-patterns.md"` (shared path, NOT the session-specific one).
   - Add new section after the `error-patterns` read: `.session-marker` handling. Read the current nonce file from `$HOME/.atelier/nonces/$PROJECT_NAME-$HASH` (if present) and compare with `$ATELIER_STATE_DIR/.session-marker` nonce and timestamp. If nonce differs AND timestamp is within 2 hours, set `CONCURRENT_SESSION_DETECTED=true`. Generate a new nonce (`openssl rand -hex 16` with `head -c 32 /dev/urandom | xxd -p` fallback) and write it to the nonces dir for this session.
   - Extend the output JSON to include two new fields: `"state_dir": "$(json_escape "$ATELIER_STATE_DIR")"` and `"concurrent_session_detected": $CONCURRENT_SESSION_DETECTED`. Default `CONCURRENT_SESSION_DETECTED=false` at the top of the script.

3. `source/claude/hooks/post-compact-reinject.sh` -- specific changes:
   - Replace line 23-25 hardcoded paths with `source "$(dirname "${BASH_SOURCE[0]}")/pipeline-state-path.sh" 2>/dev/null || true` followed by `PIPELINE_DIR="${ATELIER_STATE_DIR:-$PROJECT_DIR/docs/pipeline}"` and `STATE_FILE="$PIPELINE_DIR/pipeline-state.md"` and `BRIEF_FILE="$PIPELINE_DIR/context-brief.md"`.
   - Update the section headers on lines 42 and 49 from `"## From: docs/pipeline/pipeline-state.md"` to `"## From: $PIPELINE_DIR/pipeline-state.md"` (show the resolved path in the re-injection header).

4. `source/shared/hooks/session-boot.sh` -- identical source-side changes mirrored to this shared copy if it exists (scout showed it in the files list). If the shared copy is just a symlink, skip.

**Acceptance criteria:**
- Sourcing `pipeline-state-path.sh` in a fresh shell sets `ATELIER_STATE_DIR` to a path under `$HOME/.atelier/pipeline/{slug}/{8-hex}/`.
- When all env vars are unset and `git` is not in `$PATH`, sourcing the helper sets `ATELIER_STATE_FALLBACK="true"` and `ATELIER_STATE_DIR` points to `./docs/pipeline`.
- `session-boot.sh` run in a worktree with an existing legacy `docs/pipeline/pipeline-state.md` but an empty new state dir copies the file to the new path and reads from the new path.
- `session-boot.sh` JSON output contains the new `state_dir` and `concurrent_session_detected` fields.
- `post-compact-reinject.sh` re-injects `pipeline-state.md` from the new path when the helper resolves successfully.
- `error-patterns.md` reads still resolve to `$WORKTREE_ROOT/docs/pipeline/error-patterns.md` regardless of whether `ATELIER_STATE_FALLBACK` is true or false.
- No hook blocks on I/O; all error paths exit 0.

**Complexity:** Medium. 4 files total (1 create, 3 modify). All changes mechanical path substitution plus one new helper script (~80 lines). S1: "After this step, I can write pipeline-state.md in two concurrent worktrees and see both isolated." S2: 4 files (under 10, no justification needed). S3: Testable via pytest fixture that shells out to the hook with a controlled `CLAUDE_PROJECT_DIR`. S4: Revertable by deleting the helper and reverting the three hook edits. S5: One behavior -- state file path resolution.

**After this step, I can:** run two concurrent Claude Code sessions in different worktrees and observe that `pipeline-state.md` writes land in separate directories under `$HOME/.atelier/pipeline/`. The staleness detection triggers `concurrent_session_detected: true` when a second session opens the same worktree within 2 hours of the first.

### Step 2: hydrate-telemetry + Eva write path + agent persona required-reading

This step wires the consumer side. Producers from Step 1 must have consumers in this step to avoid orphan path drift.

**Files to modify (11):**

1. `brain/scripts/hydrate-telemetry.mjs` -- specific changes to `parseStateFiles` (line 361):
   - Change the function signature: `parseStateFiles(stateDir, pool, config, options)` already takes a `stateDir` parameter -- preserve it. The caller at line 989 passes `expandHome(stateDirArg)` from command-line args. Change the caller chain so that when `stateDirArg` is not explicitly provided, the module computes the default state dir using a new helper `resolveDefaultStateDir()` that:
     - Reads `$HOME/.atelier/pipeline/{slug}/{hash}/` if it exists (using the same slug/hash logic as the bash helper, implemented in JS via `crypto.createHash('sha256')`)
     - Falls back to `path.join(process.cwd(), 'docs/pipeline')` if not
   - The existing `existsSync` guards at lines 370 and 429 already handle the missing-file case gracefully. Add an additional early-exit: if the `stateDir` itself does not exist, log `"  State dir not found: ${stateDir} (graceful skip)"` and return 0 inserted. This prevents `readdirSync`-style errors if a future refactor assumes the directory exists.
   - Add the slug/hash resolution to a new exported helper function `resolveAtelierStateDir(worktreeRoot)` in the same module for re-use by `brain/lib/hydrate.mjs`.
   - Update the module's JSDoc example (lines 11-13) to reference the new path.

2. `source/claude/hooks/enforce-eva-paths.sh` -- specific changes:
   - After line 35 (existing `${HOME}/.claude/projects/*/memory/*` whitelist `exit 0`), add a new whitelist block:
     ```bash
     if [[ "$FILE_PATH" == ${HOME}/.atelier/pipeline/*/*/* ]]; then
       exit 0
     fi
     ```
   - This allows Eva to write to the new per-worktree path while preserving all other enforcement. The existing `docs/pipeline/*` whitelist on line 41 stays (Eva still writes `error-patterns.md` there).

3. `source/shared/agents/cal.md` -- find the required-reading line that says "Read context-brief.md" and replace with `"Read context-brief.md at {ATELIER_STATE_DIR}/context-brief.md (Eva provides this path at invocation time via the PIPELINE_STATE_DIR env var or the <read> tag)"`.

4. `source/shared/agents/colby.md` -- identical change to the required-reading reference.

5. `source/shared/agents/roz.md` -- identical change to any required-reading reference for `context-brief.md` or `pipeline-state.md` (scout research brief listed roz.md as a reader indirectly via `{pipeline_state_dir}` template references -- verify and update).

6. `source/shared/commands/architect.md` -- update required-reading section to use `{pipeline_state_dir}/context-brief.md` template placeholder if not already doing so.

7. `source/shared/commands/devops.md` -- identical template-placeholder update.

8. `source/shared/commands/pipeline.md` -- Lines 19, 20, 138, 148: replace `docs/pipeline/pipeline-state.md` with `{pipeline_state_dir}/pipeline-state.md` and `docs/pipeline/context-brief.md` with `{pipeline_state_dir}/context-brief.md`. Lines 21, 153: `docs/pipeline/error-patterns.md` stays as-is (shared file).

9. `source/shared/rules/default-persona.md` -- uses `{pipeline_state_dir}` as a placeholder already. No change needed to the text, BUT the placeholder resolution logic (done at plugin install time or via orchestration rules) must now resolve `{pipeline_state_dir}` to `$ATELIER_STATE_DIR` at runtime rather than a hardcoded `docs/pipeline/`. Add a note in the file's header comment: "At runtime, `{pipeline_state_dir}` is resolved via `pipeline-state-path.sh` output (`$ATELIER_STATE_DIR` for session-specific files, `$ATELIER_SHARED_DIR` for `error-patterns.md`)."

10. `source/shared/rules/pipeline-orchestration.md` -- search for any hardcoded `docs/pipeline/` references in Eva's orchestration rules. For each session-specific file reference (pipeline-state.md, context-brief.md, investigation-ledger.md, last-qa-report.md), replace with `{pipeline_state_dir}/...`. For `error-patterns.md` references, leave as `docs/pipeline/error-patterns.md` (shared path).

11. `source/claude/hooks/session-hydrate.sh` -- Line 12: replace `STATE_DIR="$PROJECT_DIR/docs/pipeline"` with the output of sourcing `pipeline-state-path.sh`: `source "$(dirname "${BASH_SOURCE[0]}")/pipeline-state-path.sh" 2>/dev/null || true` then `STATE_DIR="${ATELIER_STATE_DIR:-$PROJECT_DIR/docs/pipeline}"`. This ensures the hydration script receives the per-worktree state dir. No other changes to this file.

**Acceptance criteria:**
- `hydrate-telemetry.mjs` `parseStateFiles` resolves its default state dir to `$HOME/.atelier/pipeline/{slug}/{hash}/` when the directory exists.
- `hydrate-telemetry.mjs` gracefully exits with 0 inserted when the state dir does not exist (no uncaught `ENOENT`).
- `hydrate-telemetry.mjs` still works when invoked with an explicit `stateDirArg` (backward compat for existing CLI invocations).
- `enforce-eva-paths.sh` allows Eva to write to `$HOME/.atelier/pipeline/foo/a1b2c3d4/pipeline-state.md`.
- `enforce-eva-paths.sh` continues to allow Eva to write to `docs/pipeline/error-patterns.md`.
- `enforce-eva-paths.sh` still BLOCKS Eva from writing to arbitrary paths outside the whitelist.
- Agent persona files (cal.md, colby.md, roz.md) reference `{pipeline_state_dir}` template placeholder, not a hardcoded path.
- Command files (architect.md, devops.md) reference `{pipeline_state_dir}` placeholder.
- `pipeline-orchestration.md` distinguishes session-specific file references (use `{pipeline_state_dir}`) from `error-patterns.md` references (use `docs/pipeline/`).

**Complexity:** Medium. 11 files (above the 8-file default but all mechanical path substitution). Justified below.

**Justification for 11 files exceeding the default 8-file limit:**
S1 (demo): "After this step, Eva can write state to the new path, agents read from the new path via template placeholders, brain hydration finds the new path, enforcement allows it, and the `/pipeline` command file instructs Eva to use the placeholder-resolved paths." Single coherent demo.
S2 (file count): 11 files. All changes are path-substitution. None introduce new logic. Splitting this step would create orphan producers (Step 1 produces a new state dir with no consumer) for the duration between commits, violating retro lesson #005. The addition of `pipeline.md` over the initial 9-file count is required because Roz flagged it as an in-scope consumer: the `/pipeline` command file contains Eva action instructions that hardcode `docs/pipeline/pipeline-state.md` and `docs/pipeline/context-brief.md` at lines 19, 20, 138, 148 -- leaving them unchanged would create an Eva invocation path that routes writes to the legacy directory even after the helper is wired. The addition of `session-hydrate.sh` brings the count to 11 because this SessionStart hook hardcodes `STATE_DIR="$PROJECT_DIR/docs/pipeline"` and passes it to `hydrate-telemetry.mjs` via `--state-dir`, which would silently route telemetry hydration to the legacy path post-migration -- a second orphan-consumer gap in the same vertical slice.
S3 (testable): Each file is independently testable -- hook tests for enforce-eva-paths, pytest for hydrate-telemetry, grep for persona file and pipeline.md references.
S4 (revert): Each file reverts independently via `git checkout`.
S5 (single behavior): "Wire the new state path to its consumers." One vertical slice.

**After this step, I can:** run a full pipeline where Eva writes session state to the new path, Cal/Colby/Roz read it via template-resolved paths, `hydrate-telemetry.mjs` finds and captures the state, and enforcement allows Eva's writes mechanically.

### Step 3: Eva's concurrent-session hard pause behavior

**Files to modify (1):**

1. `source/shared/rules/pipeline-orchestration.md` -- add a new section `<protocol id="concurrent-session-hard-pause">` that specifies Eva's behavior on `concurrent_session_detected: true` from session-boot JSON:
   - Read the existing state dir's `pipeline-state.md` and summarize the other session's active feature and phase.
   - Hard pause. Present three options to the user: (1) Adopt existing state (resume the other session), (2) Archive existing state and start fresh (move `$ATELIER_STATE_DIR` to `$ATELIER_STATE_DIR.archive-$(date +%s)` and start clean), (3) Cancel this session.
   - Record the decision in `context-brief.md` under "User Decisions" so downstream hydration captures it.
   - On option (2), execute the archive via a bash command that Eva is allowed to run (mv is a filesystem operation, not a restricted tool).

**Acceptance criteria:**
- `pipeline-orchestration.md` contains a `concurrent-session-hard-pause` protocol section.
- The protocol specifies exactly three user options with clear consequences.
- The protocol requires Eva to record the user's choice in `context-brief.md`.
- The protocol is referenced from Eva's boot sequence (step after session-boot JSON is read).

**Complexity:** Low. 1 file, ~30 lines added.

**After this step, I can:** run two concurrent sessions on the same worktree within 2 hours and see Eva present the hard-pause menu instead of silently clobbering state.

---

## Test Specification

| ID | Category | Description |
|----|----------|-------------|
| T-0032-001 | Helper: resolution | Sourcing `pipeline-state-path.sh` with `CLAUDE_PROJECT_DIR=/tmp/test-a` sets `ATELIER_STATE_DIR` to a path containing `/.atelier/pipeline/` |
| T-0032-001b | Helper: out-of-repo guarantee | After sourcing helper with `CLAUDE_PROJECT_DIR=/tmp/test-worktree`, `ATELIER_STATE_DIR` does NOT start with `/tmp/test-worktree` (state dir is outside the project root) |
| T-0032-002 | Helper: resolution | Two different worktree roots produce two different `ATELIER_STATE_DIR` values (hashes differ) |
| T-0032-003 | Helper: resolution | The same worktree root produces the same `ATELIER_STATE_DIR` value on repeated invocations (deterministic hash) |
| T-0032-004 | Helper: fallback | With no `CLAUDE_PROJECT_DIR`, no `CURSOR_PROJECT_DIR`, and `pwd` returning `/`, `ATELIER_STATE_FALLBACK` is `"true"` and `ATELIER_STATE_DIR` equals `./docs/pipeline` |
| T-0032-005 | Helper: shared path | `ATELIER_SHARED_DIR` always resolves to `$WORKTREE_ROOT/docs/pipeline`, never to the out-of-repo path |
| T-0032-006 | Helper: directory creation | After sourcing, `$ATELIER_STATE_DIR` exists on disk (mkdir succeeded or failed silently) |
| T-0032-007 | Helper: migration | When legacy `docs/pipeline/pipeline-state.md` exists and `$ATELIER_STATE_DIR/pipeline-state.md` does not, the file is copied to the new location |
| T-0032-008 | Helper: migration preserves error-patterns | `error-patterns.md` is NOT copied from legacy to new path (it stays shared in-repo) |
| T-0032-009 | Helper: missing dependencies | If `shasum` is missing, helper falls back to `sha256sum` or `openssl dgst -sha256` |
| T-0032-010 | Isolation: concurrent worktrees | Two worktrees at different filesystem paths produce non-colliding state dirs (write to one, read from other -- files are separate) |
| T-0032-011 | session-boot: new fields | `session-boot.sh` JSON output contains `state_dir` and `concurrent_session_detected` fields |
| T-0032-012 | session-boot: reads from new path | When `$ATELIER_STATE_DIR/pipeline-state.md` exists with a `PIPELINE_STATUS` JSON, `session-boot.sh` extracts the phase from that file, not from `docs/pipeline/pipeline-state.md` |
| T-0032-013 | session-boot: error-patterns still shared | `session-boot.sh` reads `error-patterns.md` from `docs/pipeline/`, not from the new state dir, and `warn_agents[]` is computed from the shared file |
| T-0032-014 | session-boot: staleness detection -- feature mismatch | When `pipeline-state.md` feature = "X" and `context-brief.md` feature = "Y" (both in the new path), `stale_context: true` in output |
| T-0032-015 | session-boot: concurrent session detection | When `.session-marker` nonce in state dir differs from current-session nonce AND marker timestamp is < 2 hours old, `concurrent_session_detected: true` |
| T-0032-015a | session-boot: marker format | After `session-boot.sh` runs, `$ATELIER_STATE_DIR/.session-marker` exists and matches `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z [0-9a-f]{16}$` (ISO 8601 UTC timestamp + space + 16 lowercase hex chars) |
| T-0032-016 | session-boot: stale marker ignored | When `.session-marker` timestamp is > 2 hours old, `concurrent_session_detected: false` (treated as crashed session, not concurrent) |
| T-0032-017 | post-compact: reads from new path | `post-compact-reinject.sh` outputs `pipeline-state.md` content from `$ATELIER_STATE_DIR/pipeline-state.md` when the helper resolves successfully |
| T-0032-018 | post-compact: fallback | `post-compact-reinject.sh` still works when helper cannot be sourced (falls back to `docs/pipeline/pipeline-state.md`) |
| T-0032-019 | hydrate-telemetry: reads from new path | `parseStateFiles()` with the new default state dir captures `pipeline-state.md` checkbox items from the new location |
| T-0032-020 | hydrate-telemetry: graceful empty dir | `parseStateFiles()` with a state dir that does not exist returns 0 inserted and does not throw |
| T-0032-021 | hydrate-telemetry: graceful missing files | `parseStateFiles()` with a state dir that exists but is empty returns 0 inserted and does not throw |
| T-0032-022 | hydrate-telemetry: explicit arg backward compat | `parseStateFiles(explicitPath, ...)` reads from `explicitPath`, not from the resolved default |
| T-0032-023 | enforce-eva-paths: new path whitelisted | Eva writing to `$HOME/.atelier/pipeline/slug/a1b2c3d4/pipeline-state.md` exits 0 (allowed) |
| T-0032-024 | enforce-eva-paths: legacy path still whitelisted | Eva writing to `docs/pipeline/error-patterns.md` exits 0 (allowed for shared file) |
| T-0032-025 | enforce-eva-paths: non-whitelist path still blocked | Eva writing to `/tmp/random.md` exits 2 (BLOCKED) |
| T-0032-026 | enforce-eva-paths: memory path still whitelisted | Eva writing to `$HOME/.claude/projects/foo/memory/bar.md` still exits 0 (ADR-0031 precedent preserved) |
| T-0032-027a | Cursor compat | Pre-build: `source/claude/hooks/pipeline-state-path.sh` does not yet exist (baseline; this test becomes orphaned after Step 1 is built -- its purpose is to confirm the helper did not exist before ADR-0032) |
| T-0032-027b | Cursor compat | Post-build: `pipeline-state-path.sh` and all Step 1+2 modified files contain zero occurrences of `session_id`, `SESSION_ID`, or `CLAUDE_SESSION` as path-scoping keys (grep returns empty) |
| T-0032-028 | Cursor compat | `session-boot.sh` runs identically under `CURSOR_PROJECT_DIR` and `CLAUDE_PROJECT_DIR` (resolution falls through correctly) |
| T-0032-029 | Agent persona: cal.md | `cal.md` does NOT contain a hardcoded `docs/pipeline/context-brief.md` reference -- uses `{pipeline_state_dir}` placeholder |
| T-0032-030 | Agent persona: colby.md | `colby.md` does NOT contain a hardcoded `docs/pipeline/context-brief.md` reference -- uses `{pipeline_state_dir}` placeholder |
| T-0032-031 | Agent persona: roz.md | `roz.md` state-file references use `{pipeline_state_dir}` placeholder |
| T-0032-032 | Commands: architect.md | `architect.md` required-reading uses `{pipeline_state_dir}` placeholder |
| T-0032-033 | Commands: devops.md | `devops.md` required-reading uses `{pipeline_state_dir}` placeholder |
| T-0032-029e | Agent persona: pipeline.md | `pipeline.md` Eva action instructions for session-specific files (`pipeline-state.md`, `context-brief.md`) reference `{pipeline_state_dir}` placeholder; `error-patterns.md` references stay as `docs/pipeline/error-patterns.md` |
| T-0032-034 | pipeline-orchestration.md | session-specific file references use `{pipeline_state_dir}`, `error-patterns.md` references stay as `docs/pipeline/` |
| T-0032-035 | Failure: no file locks | No modified file contains `flock`, `.lock`, or `lockfile` (design commitment) |
| T-0032-036 | Failure: non-blocking boot | `session-boot.sh` contains no `sleep`, no `wait`, no network calls, no brain calls (retro lesson #003) |
| T-0032-037 | Failure: error-patterns still cross-session | Two distinct worktrees reading `docs/pipeline/error-patterns.md` see the same file contents (not isolated) |
| T-0032-038 | Failure: error-patterns not copied to new path | Helper's migration block does not copy `error-patterns.md` to `$ATELIER_STATE_DIR` |
| T-0032-039 | Failure: legacy path not deleted | Helper's migration block does not delete files from `docs/pipeline/` after copying |
| T-0032-040 | Failure: helper idempotent | Sourcing `pipeline-state-path.sh` twice in the same shell produces identical env var values |
| T-0032-041 | Failure: JSON escape | New `state_dir` field in session-boot.sh JSON output is properly escaped (no injection from paths containing quotes). Fixture: set `CLAUDE_PROJECT_DIR` to a path containing a double-quote (inject via env var override or temp dir rename); run `session-boot.sh`; pipe output to `python3 -c 'import sys,json; d=json.loads(sys.stdin.read()); assert "state_dir" in d'`; assert exit 0 (valid JSON, no injection) |
| T-0032-042 | Concurrent: same worktree detection | Two simulated sessions writing `.session-marker` within 2 hours trigger `concurrent_session_detected: true`. Fixture: write `$ATELIER_STATE_DIR/.session-marker` with timestamp 30 minutes in the past and nonce `aabbccdd11223344`; set nonces dir to contain nonce `1122334455667788` for current session; run `session-boot.sh`; assert `concurrent_session_detected: true` in JSON output |
| T-0032-043 | Concurrent: different worktree no-op | Two simulated sessions in different worktrees do NOT trigger `concurrent_session_detected: true` in either (distinct nonces dirs). Fixture: two distinct `tmp_path` subdirs as separate worktree roots; source helper twice with different `CLAUDE_PROJECT_DIR` values; verify `ATELIER_STATE_DIR` differs; write `.session-marker` in each; run `session-boot.sh` for each; assert `concurrent_session_detected: false` in both outputs |
| T-0032-044a | Integration: path consistency | `session-boot.sh` outputs `state_dir`; a file written to that path is readable by `post-compact-reinject.sh` (both hooks source `pipeline-state-path.sh` and resolve the same `ATELIER_STATE_DIR`) |
| T-0032-044b | Integration: path consistency | `post-compact-reinject.sh` and `session-boot.sh` with identical `CLAUDE_PROJECT_DIR` input produce the same `ATELIER_STATE_DIR` value (deterministic re-invocation) |
| T-0032-044c | Integration: path consistency | `hydrate-telemetry.mjs` `resolveAtelierStateDir()` returns the same path as bash helper `pipeline-state-path.sh` for the same worktree root (cross-language hash consistency) |
| T-0032-044-integration | Integration: deferred | DEFERRED -- Full E2E: `session-boot.sh` -> Eva writes state -> `post-compact-reinject.sh` -> `hydrate-telemetry.mjs` all operate on the same `$ATELIER_STATE_DIR`. Requires Eva agent mock; not a blocker for Colby implementation |
| T-0032-045 | Integration: error-patterns warn_agents | `warn_agents[]` is correctly computed from `docs/pipeline/error-patterns.md` even when session-specific files are out-of-repo |
| T-0032-046 | Hard pause protocol exists | `pipeline-orchestration.md` contains a `concurrent-session-hard-pause` protocol section with exactly three user options |

**Test counts:** 52 total (plus 1 deferred integration). 24 happy-path, 29 failure/negative/edge/consistency. Failure count (29) >= happy count (24). Satisfied.

---

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| `pipeline-state-path.sh` (helper) | Env vars: `ATELIER_STATE_DIR` (abs path string), `ATELIER_SHARED_DIR` (abs path string), `ATELIER_STATE_FALLBACK` ("true"\|"false") | `session-boot.sh`, `post-compact-reinject.sh`, future hooks |
| `session-boot.sh` (enhanced) | JSON with new fields: `state_dir` (string), `concurrent_session_detected` (bool) | Eva's boot sequence (reads SessionStart hook output) |
| `session-boot.sh` | `.session-marker` file at `$ATELIER_STATE_DIR/.session-marker` containing ISO timestamp + 16-hex nonce | Next `session-boot.sh` invocation (concurrent detection) |
| Eva (runtime writer) | Writes to `$ATELIER_STATE_DIR/pipeline-state.md`, `context-brief.md`, `investigation-ledger.md`, `last-qa-report.md` | `session-boot.sh` (next session), `post-compact-reinject.sh`, `hydrate-telemetry.mjs`, cal/colby/roz agents |
| Eva (runtime writer) | Writes to `$ATELIER_SHARED_DIR/error-patterns.md` (shared path) | `session-boot.sh` `warn_agents[]` computation |
| `hydrate-telemetry.mjs` `resolveAtelierStateDir()` | JS function returning the resolved state dir path | `parseStateFiles()`, `brain/lib/hydrate.mjs` |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `pipeline-state-path.sh` | env vars | `session-boot.sh`, `post-compact-reinject.sh` | Step 1 |
| `session-boot.sh` enhanced JSON | `state_dir`, `concurrent_session_detected` | Eva boot sequence | Step 1 (producer), Step 3 (consumer Eva hard-pause) |
| `.session-marker` file | ISO timestamp + nonce | Next `session-boot.sh` run | Step 1 (producer), Step 1 (consumer -- self-referential, same script) |
| `$ATELIER_STATE_DIR/pipeline-state.md` | existing `PIPELINE_STATUS` JSON | `session-boot.sh` reader, `post-compact-reinject.sh` re-injector, `hydrate-telemetry.mjs` parser | Step 1 (session-boot, post-compact), Step 2 (hydrate-telemetry) |
| `$ATELIER_STATE_DIR/context-brief.md` | sectioned markdown | `hydrate-telemetry.mjs` parseStateFiles, Cal, Colby, Roz | Step 2 (all consumers) |
| `enforce-eva-paths.sh` whitelist | `$HOME/.atelier/pipeline/*/*/*` allowed | Eva's runtime writes | Step 2 |
| `{pipeline_state_dir}` template placeholder in persona files | resolved to `$ATELIER_STATE_DIR` at invocation time | cal.md, colby.md, roz.md, architect.md, devops.md | Step 2 |
| Eva (pipeline.md command file) | Writes `{pipeline_state_dir}/pipeline-state.md`, `{pipeline_state_dir}/context-brief.md` | session-boot.sh, post-compact-reinject.sh, hydrate-telemetry.mjs, cal/colby/roz agents | Step 2 |
| `session-hydrate.sh` (SessionStart hook) | Passes `$ATELIER_STATE_DIR` as `--state-dir` arg to `hydrate-telemetry.mjs` | `hydrate-telemetry.mjs` `parseStateFiles()` | 2 |
| Eva's concurrent-session hard-pause protocol | user-facing menu, three options | User, `context-brief.md` write | Step 3 |

**Orphan check:** Every producer has at least one consumer in the same step or earlier. No orphan producers. `pipeline-state-path.sh` produces env vars consumed by two hooks in the same step. `enforce-eva-paths.sh` whitelist produces a permission that Eva consumes at runtime. Agent persona placeholder changes produce path-lookup expectations that `{pipeline_state_dir}` resolution at runtime consumes. Step 3's hard-pause protocol consumes the `concurrent_session_detected` field produced in Step 1.

---

## Data Sensitivity

| Method/Field | Classification | Rationale |
|-------------|---------------|-----------|
| `$ATELIER_STATE_DIR/pipeline-state.md` | `public-safe` | Same content as existing `docs/pipeline/pipeline-state.md` -- phase, feature, progress. No PII, no secrets. Only relocated. |
| `$ATELIER_STATE_DIR/context-brief.md` | `public-safe` | Same content as existing file -- scope, constraints, user decisions. Users should avoid pasting secrets here (same guidance as today). |
| `$ATELIER_STATE_DIR/investigation-ledger.md` | `public-safe` | Debug hypothesis tracking. No secrets by design. |
| `$ATELIER_STATE_DIR/last-qa-report.md` | `public-safe` | Roz's per-wave verdict. No secrets. |
| `$ATELIER_STATE_DIR/.session-marker` | `public-safe` | ISO timestamp + random nonce. No user data. |
| `$ATELIER_SHARED_DIR/error-patterns.md` | `public-safe` | Same content as existing file. Cross-session shared. |
| `resolveAtelierStateDir()` (JS helper) | `public-safe` | Returns a filesystem path string. No data access. |
| `pipeline-state-path.sh` env vars | `public-safe` | Filesystem paths only. No data, no credentials. |

The relocation from in-repo to `$HOME/.atelier/pipeline/` does not change the sensitivity classification of any file. The new directory is under the user's home -- same filesystem permissions context as `~/.claude/logs/` (ADR-0031) and `~/.claude/projects/*/memory/`.

---

## Notes for Colby

- **Step 1 model recommendation: Sonnet.** The shared helper requires careful env-var resolution with three fallback levels plus a one-time migration block. Not pure mechanical work -- the bash path-resolution logic has edge cases (empty vars, relative vs absolute pwd, missing git). Score: -1 (careful but bounded). Scout swarm: one "Existing-code" scout reads the three files being modified; one "Env" scout greps for `CLAUDE_PROJECT_DIR`, `CURSOR_PROJECT_DIR` usage across all hooks.
- **Step 2 model recommendation: Sonnet (hydrate-telemetry) + Haiku (enforce-eva-paths + persona files).** The hydrate-telemetry change touches an existing 485-line function with a specific graceful-degradation contract -- Sonnet required. The enforce-eva-paths whitelist addition and the persona-file placeholder substitutions are mechanical -- Haiku.
- **Step 3 model recommendation: Haiku.** Adding a protocol section to `pipeline-orchestration.md` following existing `<protocol id=...>` patterns. Score: -2 (mechanical, follows pattern).
- **The worktree hash MUST be computed from the absolute worktree root path**, not from `$PWD`. `session-boot.sh` currently reads state via relative paths with `$PWD` assumption -- the new helper resolves the worktree root explicitly before hashing. If the user `cd`'s into a subdirectory of the worktree, the hash must not change. Test this.
- **`error-patterns.md` STAYS in `docs/pipeline/`.** Do not accidentally migrate it. The helper's migration block must explicitly skip `error-patterns.md` when copying. The test T-0032-008 enforces this.
- **The `.session-marker` file goes in `$ATELIER_STATE_DIR`, not in `$ATELIER_SHARED_DIR`.** This is the per-session isolation marker -- it must live in the session-specific directory. The nonces directory at `$HOME/.atelier/nonces/` holds the current session's own nonce (for comparison against the marker).
- **The 2-hour concurrent-detection window is load-bearing.** If shorter, crashed sessions from the same day falsely trigger; if longer, stale idle sessions trigger. 2 hours is the documented choice; tune via a constant at the top of `session-boot.sh`.
- **`hydrate-telemetry.mjs` already has `existsSync` guards in `parseStateFiles`.** The "graceful empty dir" acceptance criterion is partially satisfied by existing code. The change is to add a single early-return at the top of the function: if `!existsSync(stateDir)`, log and return 0.
- **Do NOT touch `hydrate-telemetry.mjs`'s MCP tool re-export path.** The module exports `parseStateFiles` at line 1009 for `brain/lib/hydrate.mjs` to consume via the `atelier_hydrate` MCP tool. Preserve the export. Add new helpers as additional exports, not as replacements.
- **Enforce-eva-paths pattern:** the existing `${HOME}/.claude/projects/*/memory/*` glob uses bash `[[ ]]` pattern matching. Copy the exact form for the new `${HOME}/.atelier/pipeline/*/*/*` whitelist. The triple glob matches `project/hash/filename` -- do not change to `**` or `*` (different semantics).
- **Agent persona files use `{pipeline_state_dir}` as a placeholder.** Verify this placeholder is already resolved at plugin-install time by `/pipeline-setup`. If it is NOT (i.e., the persona files are copied verbatim), we need to either: (a) resolve the placeholder at install time to `$HOME/.atelier/pipeline/{slug}/{hash}/` (bad -- install-time resolution is static, hash changes per worktree), or (b) have Eva resolve the placeholder dynamically at invocation time (good -- Eva sources the helper and substitutes). Option (b) is the correct choice. The install-time `/pipeline-setup` must NOT substitute `{pipeline_state_dir}` in persona files with a hardcoded path -- it must leave the placeholder alone for runtime resolution. Verify this in Step 2.
- **Tests for concurrent-session detection (T-0032-042, T-0032-043) require simulation.** Use pytest with a fixture that writes `.session-marker` files with controlled nonces and timestamps, then invokes `session-boot.sh` via subprocess with `CLAUDE_PROJECT_DIR` set. Do not attempt to run two real Claude Code sessions.
- **Tests must be pytest, not bats** (per user feedback `feedback_pytest_only.md`). The helper shell script is tested by a Python test that subprocess-invokes it.
- **Rollback plan:** Single-step rollback. Revert the four files from Step 1 + the nine files from Step 2 + one file from Step 3. The new out-of-repo directory (`$HOME/.atelier/pipeline/`) becomes orphan but does no harm. Users who ran the new code have their state files in the new path; on rollback, `session-boot.sh` re-reads `docs/pipeline/` and finds the pre-migration copies (migration was copy, not move). Zero data loss on rollback. Rollback window: any time; no migration barrier.
- **Migration plan:** On first invocation of the new `session-boot.sh` (or any hook that sources the helper), the one-time migration block runs. Legacy `docs/pipeline/*.md` files are COPIED to `$ATELIER_STATE_DIR/*.md` (leaving originals). Subsequent writes go to the new path. No user action required. `error-patterns.md` never migrates.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Concurrent sessions must not clobber each other's pipeline state | Done | Step 1 (worktree-hash isolation), Step 3 (same-worktree hard pause). T-0032-010, T-0032-015, T-0032-042. |
| R2 | Agent Teams worktrees must be isolated | Done | Step 1 worktree-hash isolation (distinct filesystem paths yield distinct hashes). T-0032-002, T-0032-010. |
| R3 | `error-patterns.md` must remain cross-session shared | Done | Decision section explicit: stays in `docs/pipeline/`. Step 1 helper does not touch it. T-0032-008, T-0032-013, T-0032-037, T-0032-038. |
| R4 | Fix must work for Cursor (no session IDs) | Done | Worktree-path hash is the scoping key, not session ID. Helper uses `CURSOR_PROJECT_DIR` fallback. T-0032-027, T-0032-028. |
| R5 | No manual cleanup between sessions | Done | Automatic `mkdir -p`, automatic nonce rotation, automatic migration. No user action required. |
| R6 | `session-boot.sh` updated | Done | Step 1 file 2, specific changes listed. |
| R7 | `post-compact-reinject.sh` updated | Done | Step 1 file 3, specific changes listed. |
| R8 | `hydrate-telemetry.mjs` updated; graceful empty-dir degradation | Done | Step 2 file 1, `parseStateFiles` early-exit added. T-0032-019, T-0032-020, T-0032-021, T-0032-022. |
| R9 | Agent persona required-reading references still resolve | Done | Step 2 files 3-8 update `{pipeline_state_dir}` placeholder. T-0032-029..T-0032-034. |
| R10 | No dependency on Claude Code session IDs | Done | Alternative D explicitly rejected. T-0032-027. |
| R11 | Staleness detection still works | Done | Existing feature-mismatch check preserved in Step 1 file 2. T-0032-014. |
| R12 | Four strategies evaluated with tradeoffs | Done | Alternatives Considered section: A (rejected), B (rejected), C (chosen), D (rejected). |
| R13 | No new git-tracked files per session | Done | New path is `$HOME/.atelier/pipeline/` -- out-of-repo. No `.gitignore` changes needed. Only `error-patterns.md` remains git-tracked. |
| R14 | Implementation plan lists specific changes per file | Done | Every file in Steps 1-3 has specific line-level or function-level change instructions. |
| R15 | Test spec covers all required cases | Done | T-0032-010 (concurrent isolation), T-0032-008/013/037/038 (error-patterns sharing), T-0032-014 (staleness), T-0032-027/028 (Cursor), T-0032-002/010 (worktrees), T-0032-020 (hydrate graceful empty dir). |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled, no TBD, no placeholders.
