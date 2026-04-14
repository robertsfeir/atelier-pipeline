# Branch Lifecycle: GitFlow

Two long-lived branches: main (production-ready) and develop (integration).

## Branch Creation

Eva creates feature branches from develop via worktree, before any agent
invocation:
`git worktree add -b feature/<adr-slug>-<8-hex> ../<slug>-<8-hex> develop`

See the `worktree-per-session` protocol in `pipeline-orchestration.md`.

## Branch Naming

- Feature: `feature/<adr-or-slug>` from develop -> MR to develop
- Release: `release/<version>` from develop -> MR to main
- Hotfix: `hotfix/<name>` from main -> MR to main AND develop

## Enforcement

Ellis NEVER pushes to main or develop directly. Per-unit commits go to the
feature branch. Colby creates the MR via the configured platform CLI after the
review juncture passes. Hard pause before MR merge.

## MR Body

MR body includes: ADR reference, QA status, review juncture results.

## Release Flow

Eva creates `release/<version>` from develop. Roz runs full regression. Bug
fixes go to the release branch. Colby creates MR from release branch to main.
After merge to main, Eva tags the release, back-merges main to develop.

## Hotfix Flow

Colby creates `hotfix/<name>` from main. Normal pipeline. Colby creates MR to
main AND a separate MR to develop. Both must pass CI.

## Branch Cleanup

After MR merge, Eva deletes the feature branch (local + remote) and logs
cleanup in `{pipeline_state_dir}/pipeline-state.md`.

## CI Advisory

Run CI on MR events for develop AND main. Protect both.
