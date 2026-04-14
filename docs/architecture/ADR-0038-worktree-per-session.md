# ADR-0038: Worktree-Per-Session Pipeline Isolation

## DoR: Requirements Extracted

**Sources:** Design conversation (task brief + constraints), ADR-0032 Decision section (predecessor -- state file isolation, known gap: "two sessions in the same worktree still clobber"), `source/claude/hooks/enforce-git.sh` (git write block list), `source/shared/variants/branch-lifecycle-github-flow.md` (branch creation language), `source/shared/variants/branch-lifecycle-gitlab-flow.md` (same), `source/shared/variants/branch-lifecycle-trunk-based.md`, `source/shared/variants/branch-lifecycle-gitflow.md`, `source/shared/references/branch-mr-mode.md` (Colby branch creation reference), `source/shared/rules/pipeline-orchestration.md` (phase transitions, mandatory gates), `source/shared/rules/default-persona.md` (Eva's Bash permission), `source/shared/references/session-boot.md` (boot sequence), `source/shared/pipeline/pipeline-state.md` (PIPELINE_STATUS JSON template), `.claude/references/retro-lessons.md`, `.claude/references/dor-dod.md`.

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Every pipeline session that creates a branch must create its own git worktree at startup | Task brief | Constraint: unconditional |
| R2 | Worktree location: sibling directory `../<project-slug>-<session-id>/` | Task brief | Constraint: sibling, not inside repo |
| R3 | Session ID: 8 random hex chars, NOT timestamp | Task brief | Constraint: collision avoidance |
| R4 | Same session ID used for: worktree dir suffix, branch name suffix, ADR-0032 state dir hash alignment | Task brief | Constraint: single identity |
| R5 | Branch naming: micro/small -> `session/<8-hex>`, medium/large -> `feature/<adr-slug>-<8-hex>` | Task brief | Constraint: branch naming |
| R6 | Eva infers branch type from pipeline sizing, asks only when ambiguous | Task brief | Constraint: minimal ceremony |
| R7 | Trunk-based: session branch is the mechanism, Ellis fast-forward merges back | Task brief | Constraint: trunk-based support |
| R8 | Eva creates worktree before any Colby invocation via Bash | Task brief | Constraint: Eva responsibility |
| R9 | Eva copies `<main-repo>/.claude/brain-config.json` to worktree if it exists | Task brief | Constraint: gitignored file copy |
| R10 | Agents must be told worktree path explicitly via `<constraints>` tag | Task brief | Constraint: no implicit path knowledge |
| R11 | Ellis removes worktree after successful MR creation or fast-forward merge | Task brief | Constraint: cleanup |
| R12 | `git worktree add/remove` must NOT be blocked by enforce-git.sh | Task brief + enforce-git.sh line 59 | Verification requirement |
| R13 | Branch lifecycle files must remove "non-worktree invocation" language | Task brief | Constraint: language update |
| R14 | `.claude/` is git-tracked (except brain-config.json + telemetry/) -- worktrees get full agent/hook copy automatically | Design conversation | Verified in .gitignore |
| R15 | ADR-0032 state_dir hash is unique per session because CLAUDE_PROJECT_DIR resolves to worktree path | Design conversation | Architectural integration |
| R16 | No sessions.json registry -- ADR-0032 staleness detection handles concurrent-session detection | Task brief | Anti-design constraint |
| R17 | Mention ADR-0032 session-boot.md last-mile bug as dependency (not fixed here) | Task brief | Constraint: separate fix |

**Retro risks:**

- **Lesson #003 (Stop Hook Race Condition):** The worktree creation runs at pipeline start (Eva's `Bash` tool), not in a hook. No risk of hook stall. However, `git worktree add` can fail (branch already exists, disk full, permissions). Eva must handle failure gracefully: announce failure, do NOT proceed to Colby.
- **Lesson #005 (Frontend Wiring Omission):** The worktree path is a new "producer" (filesystem location for all work). Every downstream consumer (Colby, Roz, Ellis, Agatha, Poirot) must receive the path explicitly. An agent invoked without the worktree path will default to the main repo directory and clobber. The invocation template must be updated in pipeline-orchestration.md.
- **Lesson #002 (Self-Reporting Bug Codification):** Branch cleanup must be verified by Ellis or Eva -- not assumed to succeed silently. If `git worktree remove` fails, Eva should surface the error rather than swallowing it.

---

**Spec challenge:** The spec assumes that `CLAUDE_PROJECT_DIR` will resolve to the worktree path after Eva creates the worktree. **If wrong, the design fails because** ADR-0032's state dir hash uniqueness depends on `CLAUDE_PROJECT_DIR` pointing to the worktree root, and agents invoked in the wrong directory would read/write the main repo's state files instead of session-isolated ones. However, this assumption is correct: Claude Code sets `CLAUDE_PROJECT_DIR` based on the directory where the session was opened. When Eva creates a worktree and tells agents to operate there, `CLAUDE_PROJECT_DIR` for the *parent session* remains the original repo path. The *worktree path* is passed explicitly via `<constraints>`. The state dir hash uniqueness is actually achieved differently than assumed: session-boot.sh computes the hash from the worktree root (which is the directory where Claude Code was launched -- the MAIN repo for the parent Eva session). The session-specific state isolation comes from the 8-hex session ID being unique, not from CLAUDE_PROJECT_DIR changing.

**Revised understanding:** ADR-0032's hash is based on `CLAUDE_PROJECT_DIR` (or `pwd` fallback). For the parent Eva session, this stays the main repo. The worktree is a sibling directory where subagents operate. State isolation for the worktree session comes from ADR-0032's existing mechanism: if a second Claude Code session opens the worktree directory directly, `CLAUDE_PROJECT_DIR` will point to the worktree, giving it a different hash. Eva's session retains the main repo hash. This means we do NOT need to override the state dir -- we just need to ensure subagents operate in the worktree directory while Eva manages pipeline state in her own state dir (computed from the main repo path).

**SPOF:** The `git worktree add` command. **Failure mode:** If `git worktree add` fails (branch name conflict, insufficient permissions, corrupted git state), the pipeline has no isolation and would fall back to operating in the main repo -- exactly the collision scenario this ADR prevents. **Graceful degradation:** Eva treats `git worktree add` failure as a pipeline-start blocker. She announces the failure, surfaces the git error message, and does NOT proceed to Colby. The user can resolve the issue (delete stale worktree, choose different branch name) and retry. No silent fallback to in-place operation.

**Anti-goals:**

1. Anti-goal: Building a worktree registry or sessions.json. Reason: ADR-0032's staleness detection and `.session-marker` already handle concurrent-session detection. A registry adds state synchronization complexity (who writes it? who cleans stale entries?) with no benefit over the existing mechanism. Revisit: If worktree lifecycle tracking is needed for telemetry or dashboard visibility.

2. Anti-goal: Making worktree creation opt-out via a config flag. Reason: The entire point is unconditional isolation. An opt-out flag means some users run without isolation and hit the collision bug. The flag becomes a support burden ("did you turn off worktree mode?"). Revisit: Never -- worktrees are the mechanism for concurrent safety, not a feature.

3. Anti-goal: Having Colby create the worktree or branch. Reason: Branch creation is currently assigned to Colby in the branch lifecycle docs, but Colby is a subagent with a fresh context window. She cannot know whether another session already created a conflicting branch. Eva, as the orchestrator with access to session boot state and the ability to run diagnostic Bash commands, is the correct owner of worktree lifecycle. Moving branch creation to Eva is a deliberate architectural shift. Revisit: Never -- this is the core design decision of this ADR.

---

## Status

Approved — Roz round 1 signed off. Implemented.

**Depends on:** ADR-0032 (pipeline state session isolation -- already implemented). ADR-0032 session-boot.md last-mile bug (state_dir field not consumed by Eva's boot instructions) is a dependency for full end-to-end correctness but does NOT block this ADR's implementation. Mentioned as a note.

**Supersedes:** None (extends ADR-0032 to close the known gap).

**Related:** ADR-0032 (state file isolation), ADR-0033 (hook enforcement audit).

## Context

ADR-0032 solved pipeline STATE FILE isolation by moving `pipeline-state.md`, `context-brief.md`, `investigation-ledger.md`, and `last-qa-report.md` out of the repo into `~/.atelier/pipeline/{slug}/{hash}/`. This prevents two sessions from clobbering each other's pipeline metadata.

However, ADR-0032 explicitly acknowledged a remaining gap: **two sessions operating on the same git working tree still clobber each other's file changes.** Session A's Colby writes `src/foo.ts` while Session B's Colby is halfway through editing the same file. Git cannot merge these -- they're concurrent writes to the same file on disk. The result is lost work, corrupted diffs, and confused agents.

**The threat model:**

1. User opens Claude Code in `~/projects/my-app/` and starts a pipeline for Feature X.
2. User opens a second Claude Code window in the same directory and starts a pipeline for Feature Y.
3. Both sessions' Colby instances write to the same files. Neither knows the other exists.
4. Git status shows a soup of changes from both features. Commits mix Feature X and Feature Y changes.

**The solution: git worktrees.**

`git worktree add` creates a separate checked-out working tree from the same repository. Each worktree has its own directory, its own branch, and its own file state. Changes in one worktree do not appear in another. This is exactly the isolation primitive we need.

**Key architectural facts verified during design:**

1. `.claude/` is git-tracked in this project (only `brain-config.json` and `telemetry/` are in `.gitignore`). When `git worktree add` creates a new working tree, all git-tracked files appear in the new directory. This means every worktree automatically gets a full copy of agents, hooks, references, and rules. No manual setup needed.

2. `brain-config.json` is gitignored. It must be copied from the main repo to the worktree's `.claude/` at creation time.

3. `enforce-git.sh` blocks `git add|commit|push|reset|checkout --|restore|clean` (line 59). `git worktree add` and `git worktree remove` are NOT in this list. Eva can run them without triggering a block.

4. Branch lifecycle files (`branch-lifecycle-github-flow.md`, `branch-lifecycle-gitlab-flow.md`) currently say "Colby creates the feature branch in her first (non-worktree) invocation." This language must be replaced: Eva now creates the branch as part of worktree setup, and Colby never needs to create or check out a branch.

5. `branch-mr-mode.md` says "Colby creates the feature branch before starting any build work." This too must be updated.

**Ownership shift: branch creation moves from Colby to Eva.**

Currently, the branch lifecycle assigns branch creation to Colby. This made sense when sessions were not isolated -- Colby was the first agent to touch the codebase. With worktrees, Eva must create the branch at worktree creation time (`git worktree add -b <branch-name> <path>`), before any agent is invoked. Eva is already allowed to run Bash commands for diagnostics and setup (verified in `default-persona.md`). Creating a worktree is a setup operation, not a code-writing operation.

## Decision

**Every pipeline session that creates a branch gets a dedicated git worktree.** Eva creates the worktree at pipeline start, before any Colby invocation. All agents operate in the worktree directory. Ellis cleans up the worktree at pipeline end.

### Worktree Creation

Eva runs the following sequence at pipeline start (after sizing, after branch name determination):

```bash
# 1. Generate session ID
SESSION_ID=$(openssl rand -hex 4)  # 8 hex chars

# 2. Determine branch name
# Micro/Small: session/<session-id>
# Medium/Large: feature/<adr-slug>-<session-id>
BRANCH_NAME="session/${SESSION_ID}"  # or feature/<slug>-${SESSION_ID}

# 3. Determine worktree path
PROJECT_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || basename "$PWD")
WORKTREE_PATH="../${PROJECT_SLUG}-${SESSION_ID}"

# 4. Create worktree with new branch
git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH"

# 5. Copy gitignored files
if [ -f ".claude/brain-config.json" ]; then
  cp ".claude/brain-config.json" "${WORKTREE_PATH}/.claude/brain-config.json"
fi
```

Eva records `worktree_path`, `branch_name`, and `session_id` in `pipeline-state.md` under the Configuration section. These values are passed to every subagent invocation.

### Branch Naming Convention

| Pipeline Sizing | Branch Name | Use Case |
|----------------|-------------|----------|
| Micro | `session/<8-hex>` | Ephemeral, fast-forward merge to main |
| Small | `session/<8-hex>` | Ephemeral, fast-forward merge to main |
| Medium | `feature/<adr-slug>-<8-hex>` | Feature branch, PR/MR flow |
| Large | `feature/<adr-slug>-<8-hex>` | Feature branch, PR/MR flow |

Eva infers the branch type from the pipeline sizing decision. She only asks the user when the sizing is ambiguous (which is already handled by the sizing choice presentation in pipeline-orchestration.md).

### Trunk-Based Development Integration

In trunk-based development, teams conceptually commit "directly to trunk." With worktree-per-session, the mechanism changes but the intent is preserved:

1. Eva creates a `session/<8-hex>` branch and worktree.
2. All build work happens in the worktree on the session branch.
3. Ellis commits to the session branch (within the worktree).
4. At pipeline end, Ellis fast-forward merges the session branch to main: `git checkout main && git merge --ff-only session/<id>`.
5. Ellis removes the worktree and deletes the session branch.

If the fast-forward merge fails (main has diverged), Ellis rebases the session branch onto main first. The user is informed but this is routine.

### Agent Invocation Change

Every subagent invocation gains a new `<constraints>` entry:

```xml
<constraints>
Working directory for all file operations: /Users/alice/projects/my-app-a1b2c3d4
All Read, Write, Edit, Glob, Grep operations must use paths rooted in the worktree directory above.
Do NOT operate on the main repository at /Users/alice/projects/my-app/.
</constraints>
```

Eva passes the absolute worktree path. Agents use it for all file operations.

### Pipeline State Integration

The worktree path and session metadata are recorded in `pipeline-state.md`:

```markdown
## Configuration
**Branching Strategy:** github-flow
**Platform:** ---
**Integration Branch:** main
**Feature Branch:** feature/0038-worktree-session-a1b2c3d4
**Worktree Path:** /Users/alice/projects/my-app-a1b2c3d4
**Session ID:** a1b2c3d4
```

And in the PIPELINE_STATUS JSON:

```json
{"phase": "build", "sizing": "medium", "roz_qa": null, "telemetry_captured": false, "stop_reason": null, "worktree_path": "/Users/alice/projects/my-app-a1b2c3d4", "session_id": "a1b2c3d4", "branch_name": "feature/0038-worktree-session-a1b2c3d4"}
```

### Worktree Cleanup

Ellis performs cleanup as the final pipeline action:

```bash
# From the main repo directory (not the worktree)
cd /Users/alice/projects/my-app

# 1. Remove the worktree
git worktree remove --force "../my-app-a1b2c3d4"

# 2. Delete the session branch (after merge)
git branch -d "session/a1b2c3d4"  # or feature/<slug>-<id>
```

For MR-based strategies (github-flow, gitflow, gitlab-flow), cleanup happens after MR creation (the branch persists on the remote for the MR, but the local worktree is removed). For trunk-based, cleanup happens after the fast-forward merge to main.

### enforce-git.sh Verification

The current regex at line 59 blocks: `git add|commit|push|reset|checkout --|restore|clean`. The word-boundary `\b` ensures these are exact subcommand matches. `git worktree` does NOT match any of these patterns. No change needed to enforce-git.sh -- but the ADR documents this as a verified invariant and adds a test to prevent future regression.

### Interaction with Agent Teams

Agent Teams (experimental) already creates worktrees for Teammate Colby instances. This ADR's worktrees are at a different level:

- **ADR-0038 worktree:** Created by Eva at pipeline start. Contains the entire session's work. All agents operate here.
- **Agent Teams worktrees:** Created by the Claude Code runtime within a session. Contain individual build units. Managed by the Agent Teams runtime, not by Eva.

When both are active, the Agent Teams worktrees branch off from the ADR-0038 session worktree's branch (not from main). The merge flow remains: Teammate worktree -> session worktree branch -> main (at pipeline end).

## Alternatives Considered

### Alternative A: Lock-file per repo directory

Add a `.pipeline-lock` file to the repo root. First session claims the lock. Second session is blocked.

**Rejected because:** Stale lock recovery is complex (what if the session crashes?). Users who want concurrent work on different features are completely blocked. Does not scale to the use case -- the goal is concurrent safety, not mutual exclusion.

### Alternative B: Named branches without worktrees (branch-per-session)

Each session gets its own branch (`git checkout -b session/<id>`) but operates in the same directory. Before each agent invocation, Eva runs `git stash && git checkout session/<this-session-id>` to swap context.

**Rejected because:** Stash/checkout churn is error-prone. Agents cannot operate concurrently -- the second session must wait for the first to finish its current operation before swapping. Defeats the purpose of concurrent sessions.

### Alternative C: Docker containers per session

Spin up a container per session with a fresh clone.

**Rejected because:** Massive overhead. Requires Docker. Claude Code has no container integration. Full clone per session wastes bandwidth and disk. Overkill for the problem.

### Alternative D: Per-session copy of the repo (cp -r)

Copy the entire repo into a temp directory per session.

**Rejected because:** Breaks git history linkage. Changes in the copy cannot be merged back via git operations. `.git` directory duplication wastes disk. No branch management. Worktrees are the git-native solution for exactly this use case.

## Consequences

**Positive:**

- Concurrent Claude Code sessions can no longer clobber each other's file changes. Each session operates on an isolated filesystem.
- Combined with ADR-0032, both state files AND working tree files are fully isolated per session.
- `.claude/` contents (agents, hooks, references) are automatically available in worktrees because they are git-tracked. No manual setup.
- Branch naming convention (`session/<id>` vs `feature/<slug>-<id>`) provides clear intent signaling.
- Trunk-based development gains the same isolation benefits through ephemeral session branches that fast-forward merge.
- ADR-0032's state dir hash is naturally unique per worktree (different directory path -> different hash).

**Negative:**

- Disk usage increases: each worktree is a full checkout (minus `.git` objects, which are shared). For large repos this could be significant. Mitigated by worktree cleanup at pipeline end.
- Branch proliferation: each session creates a branch. Stale branches from crashed sessions accumulate until manually cleaned. Mitigated by the `session/` prefix convention making them easy to identify and prune (`git branch --list 'session/*' | xargs git branch -D`).
- Eva's responsibilities increase: she now owns worktree creation, gitignored file copying, and path propagation to all agents. This is additional orchestration complexity.
- Agents must respect the worktree path constraint. An agent that ignores the `<constraints>` and operates on `CLAUDE_PROJECT_DIR` (the main repo) breaks isolation. This is a behavioral constraint, not mechanically enforced (enforcement would require a hook that blocks Write/Edit outside the worktree path, which is out of scope for this ADR).

**Neutral:**

- The branch creation ownership shift from Colby to Eva is a philosophical change but reduces complexity: one agent (Eva) manages the full lifecycle instead of splitting it across Eva (cleanup) and Colby (creation).
- `branch-mr-mode.md` becomes a reference for MR creation only, not branch creation. Its scope narrows.

---

## Implementation Plan

### Step 1: Pipeline orchestration -- worktree protocol and invocation template update

This step establishes the worktree creation protocol in Eva's orchestration rules and updates the subagent invocation template to include the worktree path. These are the "producer" definitions that all subsequent steps consume.

**Files to modify (2):**

1. `source/shared/rules/pipeline-orchestration.md` -- Add a new section `<protocol id="worktree-per-session">` after the `concurrent-session-hard-pause` protocol (or after the phase sizing rules). Content:
   - **Worktree creation sequence:** After sizing decision and branch name determination, Eva runs `git worktree add -b <branch> ../<slug>-<session-id>`. Session ID is `openssl rand -hex 4`. Branch name follows the sizing table (session/ vs feature/).
   - **Failure handling:** If `git worktree add` fails, Eva announces the error and does NOT proceed. User resolves (stale worktree, branch conflict) and retries.
   - **Gitignored file copy:** Eva copies `.claude/brain-config.json` from main repo to worktree `.claude/` if the file exists.
   - **State recording:** Eva writes `worktree_path`, `session_id`, and `branch_name` to `pipeline-state.md` Configuration section and PIPELINE_STATUS JSON.
   - **Agent path constraint:** Eva includes the worktree path in every subagent `<constraints>` tag: `"Working directory for all file operations: <worktree-path>"`.
   - **Trunk-based integration:** For trunk-based, Ellis fast-forward merges `session/<id>` to main at pipeline end. If ff fails, Ellis rebases first.
   - **Cleanup:** Ellis runs `git worktree remove --force <path>` and `git branch -d <branch>` after MR creation (MR-based) or after ff merge (trunk-based).
   - **Agent Teams interaction:** When Agent Teams is active, Teammate worktrees branch from the session branch, not from main.

2. `source/shared/pipeline/pipeline-state.md` -- Add three new fields to the Configuration section template and to the PIPELINE_STATUS JSON comment:
   - `**Worktree Path:** ---`
   - `**Session ID:** ---`
   - PIPELINE_STATUS JSON gains `"worktree_path": null, "session_id": null, "branch_name": null`.

**Acceptance criteria:**
- `pipeline-orchestration.md` contains a `worktree-per-session` protocol section with creation, failure, copy, recording, constraint, trunk-based, cleanup, and Agent Teams subsections.
- `pipeline-state.md` template includes `Worktree Path`, `Session ID` fields and updated PIPELINE_STATUS JSON.
- The protocol specifies that worktree creation happens BEFORE any Colby invocation.
- The protocol specifies the branch naming convention table (sizing -> branch prefix).
- No references to "Colby creates the branch" in the new protocol.

**Complexity:** Low-Medium. 2 files. S1: "After this step, Eva's orchestration rules document when and how to create worktrees and how to pass the path to agents." S3: Verifiable by grep for protocol section and field names. S4: Revertable by removing the protocol section and template fields. S5: 2 files, one behavior (worktree protocol definition).

**After this step, I can:** read the orchestration rules and understand the complete worktree lifecycle from creation through cleanup.

### Step 2: Branch lifecycle files -- remove Colby branch creation, add Eva worktree language

This step updates the four branch lifecycle variant files and the branch-mr-mode reference to reflect the ownership shift from Colby to Eva.

**Files to modify (5):**

1. `source/shared/variants/branch-lifecycle-github-flow.md` -- Replace the "Branch Creation" section. Remove: "Colby creates the feature branch in her first (non-worktree) invocation, before any build work." Replace with: "Eva creates the feature branch and worktree at pipeline start, before any agent invocation. See `pipeline-orchestration.md` worktree-per-session protocol. If resuming a pipeline with an existing worktree (recorded in `{pipeline_state_dir}/pipeline-state.md`), Eva verifies the worktree still exists and re-uses it." Update Branch Naming to note the `<8-hex>` session ID suffix. Update Branch Cleanup to mention worktree removal alongside branch deletion.

2. `source/shared/variants/branch-lifecycle-gitlab-flow.md` -- Same changes as github-flow (identical "Branch Creation" section text).

3. `source/shared/variants/branch-lifecycle-gitflow.md` -- Update "Branch Creation" section: "Eva creates feature branches from develop via worktree: `git worktree add -b feature/<name> ../<slug>-<session-id> develop`." Remove reference to Colby creating branches.

4. `source/shared/variants/branch-lifecycle-trunk-based.md` -- Add new section "Session Branches" explaining the session/<8-hex> mechanism: Eva creates a session branch and worktree for every pipeline. Ellis fast-forward merges back to main. Remove or update the "Optional Short-Lived Branches" section to note that session branches are now the default mechanism (not opt-in).

5. `source/shared/references/branch-mr-mode.md` -- Update "Branch Creation (first invocation of a pipeline)" section. Change from "Colby creates the feature branch before starting any build work" to "Eva creates the feature branch and worktree at pipeline start (see worktree-per-session protocol in pipeline-orchestration.md). Colby receives the worktree path in her invocation constraints." Remove `git checkout -b` examples from Colby's responsibility; note that branch creation happens via `git worktree add -b`. Keep MR Creation section unchanged (Colby still creates MRs).

**Acceptance criteria:**
- No branch lifecycle file contains "Colby creates the feature branch" or "(non-worktree) invocation."
- All four branch lifecycle files reference Eva as the branch/worktree creator.
- `branch-mr-mode.md` separates branch creation (Eva) from MR creation (Colby).
- Trunk-based lifecycle documents the session branch mechanism.
- GitFlow lifecycle shows the `develop` base branch in the worktree add command.

**Complexity:** Low. 5 files, all text changes (no logic). S1: "After this step, all branch lifecycle documentation correctly attributes branch creation to Eva and describes the worktree mechanism." S3: Verifiable by grep for removed language ("non-worktree", "Colby creates the feature branch"). S4: Revertable via git checkout on 5 files. S5: 5 files, one behavior (documentation alignment).

**After this step, I can:** read any branch lifecycle variant and see correct worktree-based branch creation instructions attributed to Eva.

### Step 3: enforce-git.sh -- explicit allowlist comment and regression test

This step does not change enforce-git.sh logic (worktree is already allowed) but adds an explicit comment documenting the allowance and creates a regression test to prevent future accidental blocking.

**Files to modify (1):**

1. `source/claude/hooks/enforce-git.sh` -- Add a comment block after the git write operations regex (after line 65):
   ```bash
   # NOTE (ADR-0038): git worktree add/remove are intentionally NOT blocked.
   # Eva creates worktrees at pipeline start for session isolation.
   # Do NOT add 'worktree' to the blocked operations regex above.
   ```

**Files to create (1):**

1. `tests/hooks/test_enforce_git_worktree.py` -- Pytest test that shells out to enforce-git.sh with a simulated `git worktree add` command and verifies exit code 0 (not blocked). Also tests `git worktree remove` and `git worktree list`. Tests that blocked operations (`git add`, `git commit`) still return exit 2 for non-Ellis agents.

**Acceptance criteria:**
- `enforce-git.sh` contains the ADR-0038 comment documenting intentional worktree allowance.
- `test_enforce_git_worktree.py` passes: `git worktree add/remove/list` are not blocked for any agent type.
- `test_enforce_git_worktree.py` passes: `git add`, `git commit` remain blocked for non-Ellis agents (regression guard).
- No functional change to enforce-git.sh behavior.

**Complexity:** Low. 2 files (1 modify, 1 create). S1: "After this step, there is a regression test ensuring git worktree commands stay unblocked." S3: Independently testable via pytest. S4: Revertable by deleting test file and removing comment. S5: 2 files, one behavior (worktree allowance verification).

**After this step, I can:** run `pytest tests/hooks/test_enforce_git_worktree.py` and see green tests confirming worktree commands are allowed.

### Step 4: Ellis cleanup -- worktree removal and branch deletion logic in Ellis persona

This step adds worktree cleanup responsibilities to Ellis's persona file and updates the Ellis-relevant sections of pipeline-orchestration.md.

**Files to modify (2):**

1. `source/shared/agents/ellis.md` -- Add a new section in Ellis's `<workflow>` describing the cleanup protocol:
   - After final commit (MR-based) or after fast-forward merge (trunk-based), Ellis checks if `worktree_path` and `branch_name` are present in the invocation constraints.
   - If present, Ellis runs `git worktree remove --force <worktree_path>` from the main repo directory, then `git branch -d <branch_name>`.
   - If `git branch -d` fails (branch not fully merged), Ellis tries `git branch -D <branch_name>` for session branches only (prefix `session/`). For feature branches, Ellis warns and leaves the branch (it may be needed for the MR).
   - Ellis reports cleanup status in the commit summary.

2. `source/shared/rules/pipeline-orchestration.md` -- In the existing Ellis-related sections (gate 2 "Ellis commits. Eva does not." and the "Per-Unit Commits During Build" section), add a note: "At pipeline end, Eva includes `worktree_path`, `branch_name`, and `main_repo_path` in Ellis's invocation constraints for cleanup. See worktree-per-session protocol."

**Acceptance criteria:**
- `ellis.md` contains worktree cleanup workflow.
- Ellis cleanup distinguishes MR-based (cleanup after MR creation, keep remote branch) from trunk-based (cleanup after ff merge).
- `pipeline-orchestration.md` references Ellis cleanup in the relevant section.
- Ellis does not force-delete feature branches (only session branches).

**Complexity:** Low. 2 files. S1: "After this step, Ellis knows how to clean up worktrees and session branches at pipeline end." S3: Verifiable by reading the workflow section. S4: Revertable by removing the added sections. S5: 2 files, one behavior (cleanup protocol).

**After this step, I can:** invoke Ellis with worktree cleanup constraints and expect the worktree and branch to be removed.

---

## Test Specification

| ID | Category | Description |
|----|----------|-------------|
| T-0038-001 | Protocol: creation | `pipeline-orchestration.md` contains a `worktree-per-session` protocol section with subsections: creation, failure handling, gitignored file copy, state recording, agent constraint, trunk-based, cleanup, Agent Teams |
| T-0038-002 | Protocol: ordering | The worktree-per-session protocol specifies creation BEFORE any Colby invocation (grep for ordering language) |
| T-0038-003 | Protocol: branch naming | The protocol contains a table mapping sizing (micro/small/medium/large) to branch prefix (session/ or feature/) |
| T-0038-004 | Protocol: failure | The protocol specifies that `git worktree add` failure is a pipeline-start blocker (Eva does NOT proceed) |
| T-0038-005 | Protocol: brain-config copy | The protocol specifies copying `.claude/brain-config.json` from main repo to worktree |
| T-0038-006 | Template: state fields | `pipeline-state.md` template contains `Worktree Path`, `Session ID` fields |
| T-0038-007 | Template: JSON fields | `pipeline-state.md` PIPELINE_STATUS JSON comment contains `worktree_path`, `session_id`, `branch_name` keys |
| T-0038-008 | Lifecycle: github-flow | `branch-lifecycle-github-flow.md` does NOT contain "Colby creates the feature branch" or "(non-worktree) invocation" |
| T-0038-009 | Lifecycle: github-flow | `branch-lifecycle-github-flow.md` references Eva as worktree/branch creator |
| T-0038-010 | Lifecycle: gitlab-flow | `branch-lifecycle-gitlab-flow.md` does NOT contain "Colby creates the feature branch" or "(non-worktree) invocation" |
| T-0038-011 | Lifecycle: gitlab-flow | `branch-lifecycle-gitlab-flow.md` references Eva as worktree/branch creator |
| T-0038-012 | Lifecycle: gitflow | `branch-lifecycle-gitflow.md` does NOT contain "Colby creates feature branches from develop" |
| T-0038-013 | Lifecycle: gitflow | `branch-lifecycle-gitflow.md` shows `develop` as the base for feature worktrees |
| T-0038-013b | Lifecycle: gitflow | `branch-lifecycle-gitflow.md` references Eva as worktree/branch creator |
| T-0038-014 | Lifecycle: trunk-based | `branch-lifecycle-trunk-based.md` documents session branch mechanism with `session/<8-hex>` pattern |
| T-0038-015 | Lifecycle: trunk-based | `branch-lifecycle-trunk-based.md` specifies fast-forward merge to main at pipeline end |
| T-0038-016 | Reference: branch-mr-mode | `branch-mr-mode.md` attributes branch creation to Eva, not Colby |
| T-0038-017 | Reference: branch-mr-mode | `branch-mr-mode.md` retains Colby's MR creation responsibility |
| T-0038-018 | Enforcement: worktree allowed | `enforce-git.sh` with command `git worktree add -b session/a1b2c3d4 ../test-repo-a1b2c3d4` exits 0 for agent_type="" (Eva/main thread) |
| T-0038-019 | Enforcement: worktree remove allowed | `enforce-git.sh` with command `git worktree remove --force ../test-repo-a1b2c3d4` exits 0 for agent_type="ellis" |
| T-0038-020 | Enforcement: worktree list allowed | `enforce-git.sh` with command `git worktree list` exits 0 for any agent_type |
| T-0038-021 | Enforcement: git add still blocked | `enforce-git.sh` with command `git add .` exits 2 for agent_type="" (regression guard) |
| T-0038-022 | Enforcement: git commit still blocked | `enforce-git.sh` with command `git commit -m "test"` exits 2 for agent_type="colby" (regression guard) |
| T-0038-023 | Enforcement: comment present | `enforce-git.sh` contains "ADR-0038" comment documenting intentional worktree allowance |
| T-0038-024 | Ellis: cleanup workflow | `ellis.md` contains worktree removal workflow section |
| T-0038-025 | Ellis: session branch force-delete | `ellis.md` cleanup workflow allows `git branch -D` only for `session/` prefix branches |
| T-0038-026 | Ellis: feature branch preservation | `ellis.md` cleanup workflow does NOT force-delete feature branches (warns instead) |
| T-0038-027 | Orchestration: Ellis cleanup reference | `pipeline-orchestration.md` references worktree cleanup in Ellis-related sections |
| T-0038-028 | Consistency: no Colby branch creation | Zero files in `source/shared/variants/` contain "Colby creates the feature branch" (grep returns empty) |
| T-0038-029 | Consistency: no non-worktree language | Zero files in `source/shared/variants/` contain "(non-worktree)" (grep returns empty) |
| T-0038-030 | Consistency: no non-worktree in branch-mr-mode | `source/shared/references/branch-mr-mode.md` does not contain "(non-worktree)" |

---

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| Eva (worktree creation) | `worktree_path: string` (absolute path), `session_id: string` (8 hex), `branch_name: string` | pipeline-state.md (recording) |
| pipeline-state.md | PIPELINE_STATUS JSON with `worktree_path`, `session_id`, `branch_name` | session-boot.sh (resume detection), Eva (state reads) |
| Eva (invocation) | `<constraints>` tag with `"Working directory: <worktree_path>"` | Colby, Roz, Agatha, Ellis, Poirot (all subagents) |
| Eva (cleanup invocation) | `<constraints>` tag with `worktree_path`, `branch_name`, `main_repo_path` | Ellis (cleanup) |
| Ellis (cleanup result) | Bash exit codes: 0 (success), non-zero (failure with stderr message) | Eva (cleanup verification) |

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `pipeline-orchestration.md` worktree protocol | Protocol definition (text) | Branch lifecycle files, Ellis persona, Eva runtime | Step 1 (producer), Steps 2+4 (consumers) |
| `pipeline-state.md` template fields | `Worktree Path`, `Session ID`, JSON keys | Eva reads at invocation, session-boot.sh at resume | Step 1 |
| Branch lifecycle docs | Branch creation attribution (text) | Eva runtime behavior, developer understanding | Step 2 |
| `branch-mr-mode.md` updates | MR-only scope (text) | Colby MR creation behavior | Step 2 |
| `enforce-git.sh` comment | Documentation only | Developer reading hook code | Step 3 |
| `test_enforce_git_worktree.py` | Test assertions | CI / Roz QA | Step 3 |
| `ellis.md` cleanup workflow | Cleanup protocol (text) | Ellis runtime behavior | Step 4 |
| `pipeline-orchestration.md` Ellis cleanup ref | Cross-reference (text) | Eva invocation of Ellis | Step 4 |

## Data Sensitivity

| Method/Path | Classification | Rationale |
|-------------|---------------|-----------|
| `worktree_path` in pipeline-state.md | public-safe | Filesystem path, no secrets |
| `session_id` in pipeline-state.md | public-safe | Random hex, not a credential |
| `branch_name` in pipeline-state.md | public-safe | Git branch name, visible to anyone with repo access |
| `.claude/brain-config.json` copy | auth-only | May contain connection strings or credentials for brain DB |

## State Transition Table

| Current State | Event | Next State | Side Effects |
|--------------|-------|------------|-------------|
| Pipeline start (post-sizing) | Eva runs `git worktree add` | Worktree active | worktree_path, session_id, branch_name written to pipeline-state.md |
| Worktree active | `git worktree add` fails | Pipeline blocked | Eva announces error, user must resolve |
| Worktree active | Build/QA/Review phases | Worktree active | Agents operate in worktree via constraints |
| Worktree active (MR-based) | Ellis creates MR | Cleanup pending | MR URL returned to Eva |
| Worktree active (trunk-based) | Ellis ff-merges to main | Cleanup pending | main branch updated |
| Cleanup pending | Ellis runs `git worktree remove` | Worktree removed | Directory deleted |
| Worktree removed | Ellis runs `git branch -d` | Clean idle | Branch deleted, pipeline-state.md updated to idle |
| Worktree removed | `git branch -d` fails (feature branch) | Partial cleanup | Warning issued, branch preserved for MR |
| Pipeline crash (any state) | Session ends | Stale worktree | Worktree persists on disk until manual cleanup or next session recovery |

**Stuck states:**
- **Stale worktree after crash:** The worktree directory persists on disk. `git worktree list` shows it. Next session can detect and offer cleanup. Not automatically cleaned -- manual intervention needed for crashed sessions.
- **Orphan session branch:** If worktree is removed but branch delete fails, the branch persists. `git branch --list 'session/*'` identifies orphans. Safe to batch-delete: `git branch --list 'session/*' | xargs git branch -D`.

## Notes for Colby

1. **Step 1 is load-bearing.** The protocol section in pipeline-orchestration.md defines the entire worktree lifecycle. Get this right and everything else is documentation alignment. The protocol MUST include failure handling -- do not skip the "what if git worktree add fails" subsection.

2. **Step 2 is all text edits.** No logic changes. The key transformation is removing "Colby creates the feature branch in her first (non-worktree) invocation" and replacing with Eva-centric language. Grep for "non-worktree" across all variant files to ensure complete removal.

3. **Step 3 test file pattern.** Follow the existing test pattern in `tests/hooks/` (if tests exist there). The test should shell out to enforce-git.sh with controlled stdin JSON (simulating Claude Code hook input). Reference how `test_enforce_git.py` or similar tests construct the hook input JSON.

4. **Step 4 Ellis cleanup.** Ellis already has a workflow section in his persona. Add the cleanup as a conditional step: "If worktree_path is provided in constraints, perform cleanup after final commit." Ellis should NOT cleanup if no worktree_path is present (backward compat for sessions started without worktrees).

5. **brain-config.json copy edge case.** The file might not exist (user hasn't configured brain). The protocol says "if it exists." Colby's implementation in the protocol text must include the `[ -f ".claude/brain-config.json" ]` guard.

6. **Proven pattern from ADR-0032:** The shared helper `pipeline-state-path.sh` sources cleanly and exports env vars. Follow the same "source helper, use exported vars, fall back on source failure" pattern for any new bash logic. But this ADR adds no new helper scripts -- the worktree creation is a sequence of `git` and `cp` commands Eva runs directly.

7. **Branch-mr-mode.md scope change.** After this ADR, `branch-mr-mode.md` is a reference for MR creation only. Its title ("Branch & MR Mode") may be misleading. Consider renaming to "MR Mode" or adding a header note. Use judgment -- if the rename would break references elsewhere, add a note instead.

8. **Dependency note:** The ADR-0032 session-boot.md last-mile bug (Eva does not read `state_dir` from boot JSON) is a separate micro fix. This ADR works without that fix because Eva computes her state dir from her own `CLAUDE_PROJECT_DIR` (which stays the main repo). The last-mile bug affects Eva's ability to resume a worktree session after a session crash -- which is an edge case this ADR acknowledges as a "stale worktree" stuck state.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Unconditional worktree creation | Done | Step 1: protocol section mandates worktree for every pipeline with branch |
| R2 | Sibling directory location | Done | Step 1: protocol specifies `../<project-slug>-<session-id>/` |
| R3 | 8 random hex session ID | Done | Step 1: protocol specifies `openssl rand -hex 4` |
| R4 | Session ID reuse across worktree/branch/state | Done | Step 1: same ID used in worktree path, branch name, state recording |
| R5 | Branch naming convention | Done | Step 1: sizing-to-prefix table |
| R6 | Eva infers branch type | Done | Step 1: protocol links to sizing decision |
| R7 | Trunk-based session branches | Done | Steps 1+2: protocol + trunk-based lifecycle update |
| R8 | Eva creates worktree before Colby | Done | Step 1: protocol ordering requirement |
| R9 | brain-config.json copy | Done | Step 1: protocol includes copy step with existence guard |
| R10 | Agents told worktree path via constraints | Done | Step 1: invocation template update |
| R11 | Ellis cleanup | Done | Step 4: Ellis persona and orchestration cross-reference |
| R12 | git worktree not blocked by enforce-git.sh | Done | Step 3: verified, documented with comment, regression test |
| R13 | Remove "non-worktree invocation" language | Done | Step 2: all branch lifecycle files updated |
| R14 | .claude/ available in worktrees (git-tracked) | Done | Context section documents this property; no implementation needed |
| R15 | ADR-0032 state dir hash uniqueness | Done | Context/Decision section explains the mechanism |
| R16 | No sessions.json registry | Done | Anti-goal #1; no registry designed |
| R17 | Mention ADR-0032 last-mile bug as dependency | Done | Depends-on section and Notes for Colby #8 |

**Grep check:** `TODO/FIXME/HACK/XXX` in this document -> 0
**Template:** All sections filled -- no TBD, no placeholders
