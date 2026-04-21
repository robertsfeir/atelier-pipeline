# Branch & MR Mode

<!-- Part of atelier-pipeline. Referenced by Colby when pipeline uses an MR-based branching strategy. -->
<!-- CONFIGURE: No placeholders to update. -->

When the pipeline uses an MR-based branching strategy (GitHub Flow, GitLab
Flow, GitFlow), Eva creates the branch and worktree at pipeline start. Colby handles MR creation.

## Branch Creation

Eva creates the feature branch and worktree at pipeline start (before any
agent invocation) using `git worktree add -b <branch-name> <worktree-path>`.
See the `worktree-per-session` protocol in `pipeline-orchestration.md` for
the full creation sequence.

Colby receives the worktree path in her invocation `<constraints>` and operates
entirely within the worktree. Colby does NOT create or check out branches.

If resuming a pipeline with an existing worktree (noted in Eva's task), Eva
verifies the worktree still exists and instructs Colby to continue there.

## MR Creation (after review juncture passes)

After all QA passes and the review juncture is complete, Eva invokes Colby to
create the MR:
1. Ensure all changes are committed and pushed to the feature branch.
2. Create MR using the platform CLI from pipeline-config.json:
   `{mr_command} --title "TYPE(SCOPE): <summary>" --body "<MR body>"`
   MR body includes: summary, ADR reference, QA status, review juncture results.
3. Return MR URL to Eva for hard pause.
4. For GitFlow hotfixes: create TWO MRs (one targeting main, one targeting develop).
5. For GitLab Flow promotions: create promotion MRs (main -> staging, staging -> production).
