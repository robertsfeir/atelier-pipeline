# Worktree-Per-Session Isolation

JIT-loaded reference. Extracted from `pipeline-orchestration.md`. Eva loads
this file on demand when a pipeline session needs worktree creation,
cleanup, or Agent-Teams branching details. The `<protocol id="worktree-per-session">`
anchor is preserved for downstream references.

<protocol id="worktree-per-session">

## Worktree-Per-Session Isolation (ADR-0038)

Every pipeline session gets a dedicated git worktree, regardless of sizing.
Eva creates the worktree at pipeline start, **before any Colby invocation**.

### Creation Sequence

After sizing decision and branch name determination, Eva runs:

```bash
# 1. Generate session ID (8 hex chars)
SESSION_ID=$(openssl rand -hex 4)

# 2. Determine branch name
# Micro/Small:   session/<session-id>
# Medium/Large:  feature/<adr-slug>-<session-id>
BRANCH_NAME="session/${SESSION_ID}"  # or feature/<slug>-${SESSION_ID}

# 3. Determine worktree path (sibling directory, NOT inside repo)
PROJECT_SLUG=$(basename "$(git remote get-url origin 2>/dev/null)" .git 2>/dev/null || basename "$PWD")
WORKTREE_PATH="../${PROJECT_SLUG}-${SESSION_ID}"

# 4. Create worktree with new branch
git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH"

# 5. Copy gitignored config (brain-config.json)
if [ -f ".claude/brain-config.json" ]; then
  cp ".claude/brain-config.json" "${WORKTREE_PATH}/.claude/brain-config.json"
fi
```

**Branch naming table:**

| Pipeline Sizing | Branch Prefix | Merge Strategy |
|----------------|---------------|----------------|
| Micro | `session/<8-hex>` | Fast-forward to main |
| Small | `session/<8-hex>` | Fast-forward to main |
| Medium | `feature/<adr-slug>-<8-hex>` | MR/PR flow |
| Large | `feature/<adr-slug>-<8-hex>` | MR/PR flow |

Worktree creation is not conditional — Micro and Small sessions create session branches and dedicated worktrees exactly as Medium and Large do.

### Failure Handling

If `git worktree add` fails (branch name conflict, disk full, permissions),
Eva announces the error verbatim and does NOT proceed to Colby. The pipeline
is a blocker. The user resolves the issue (delete stale worktree, choose
different branch name) and retries. No silent fallback to in-place operation.

### Gitignored File Copy

Eva copies `.claude/brain-config.json` from the main repo to the worktree's
`.claude/` directory if the file exists. This file is gitignored and therefore
not present in the worktree automatically. All other `.claude/` contents are
git-tracked and appear in the worktree automatically.

### State Recording

Eva records worktree metadata in `pipeline-state.md` Configuration section:
- `**Worktree Path:** <absolute-path>`
- `**Session ID:** <8-hex>`

And in the PIPELINE_STATUS JSON:
- `"worktree_path": "<absolute-path>"`
- `"session_id": "<8-hex>"`
- `"branch_name": "<branch-name>"`

### Agent Path Constraint

Every subagent invocation includes in the `<constraints>` tag:

```
Working directory for all file operations: <worktree-path>
All Read, Write, Edit, Glob, Grep operations must use paths rooted in the
worktree directory above. Do NOT operate on the main repository.
```

Eva passes the absolute worktree path. This constraint applies to Colby,
Agatha, Ellis (build/commit), and Poirot.

### Trunk-Based Integration

In trunk-based development, Eva creates a `session/<8-hex>` branch and
worktree. All build work happens in the worktree on the session branch. At
pipeline end, Ellis fast-forward merges the session branch to main:
`git checkout main && git merge --ff-only session/<id>`. If the ff merge
fails (main has diverged), Ellis rebases the session branch onto main first
and informs the user. After successful merge, Ellis removes the worktree and
deletes the session branch.

### Worktree Cleanup

Cleanup is Ellis's responsibility at pipeline end:
- **MR-based strategies** (github-flow, gitlab-flow, gitflow): cleanup after MR
  creation. The branch persists on the remote for the MR; only the local
  worktree is removed. Ellis runs:
  `git worktree remove --force <worktree-path>` (from main repo directory).
  `git branch -d <branch-name>` (soft delete; branch still exists on remote).
- **Trunk-based**: cleanup after successful fast-forward merge to main. Ellis
  runs: `git worktree remove --force <worktree-path>`, then
  `git branch -D session/<id>` (force delete; branch has been merged).

Eva includes `worktree_path`, `branch_name`, and `main_repo_path` in Ellis's
invocation constraints for cleanup. See Step 4: Ellis cleanup protocol.

### Agent Teams Interaction

When Agent Teams is active, Teammate Colby instances create their own
worktrees for individual build units (managed by the Agent Teams runtime,
not Eva). These Teammate worktrees branch from the ADR-0038 session branch,
not from main. The merge flow remains: Teammate worktree -> session worktree
branch -> main (at pipeline end via Ellis).

</protocol>
