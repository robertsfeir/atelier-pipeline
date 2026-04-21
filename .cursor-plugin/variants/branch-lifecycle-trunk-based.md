# Branch Lifecycle: Trunk-Based Development

All work happens on main. No long-lived feature branches. Session branches
provide isolation during the pipeline and are merged back to main via
fast-forward at pipeline end.

## Session Branches (default mechanism)

Eva creates a `session/<8-hex>` branch and worktree at pipeline start via:
`git worktree add -b session/<8-hex> ../<slug>-<8-hex>`

All build work happens in the worktree on the session branch. At pipeline end,
Ellis fast-forward merges the session branch to main:
`git checkout main && git merge --ff-only session/<id>`

If the fast-forward fails (main has diverged), Ellis rebases the session
branch onto main first, then fast-forward merges. The user is informed but
this is routine.

After successful merge, Ellis removes the worktree and deletes the session
branch:
```bash
git worktree remove --force ../<slug>-<8-hex>
git branch -D session/<8-hex>
```

## Commit Flow

Ellis commits to the session branch within the worktree during the pipeline.
Hard pause before the final fast-forward merge to main (existing behavior).
No MR flow. No long-lived branch cleanup.

## CI Advisory

Run CI on every push to main.
