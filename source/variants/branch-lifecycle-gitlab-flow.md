---
paths:
  - "docs/pipeline/**"
---

# Branch Lifecycle: GitLab Flow

Same as GitHub Flow for feature work, plus environment promotion branches.

## Branch Creation

Colby creates the feature branch in her first (non-worktree) invocation,
before any build work. If resuming a pipeline with an existing branch
(recorded in `{pipeline_state_dir}/pipeline-state.md`), Colby checks it out.

## Branch Naming

- ADR-backed: `feature/<adr-number>-<kebab-name>`
- Small/bug: `feature/<ticket-or-slug>`
- Micro: `feature/<slug>`

## Enforcement

Ellis NEVER pushes to main. Per-unit commits go to the feature branch. Colby
creates the MR via the configured platform CLI after the review juncture
passes. Hard pause before MR merge. User reviews CI results and merges, or
approves Eva to merge.

## MR Body

MR body includes: ADR reference, QA status, review juncture results.

## Environment Promotion

After MR merges to main, Eva offers promotion. "MR merged to main. Promote to
staging?" (hard pause). If approved, Colby creates promotion MR (main ->
staging). "Staging verified. Promote to production?" (hard pause). Each
promotion step is a hard pause. Eva never auto-promotes.

## Hotfix Flow

When the user reports a production bug, Colby creates `hotfix/<name>` from
main (or production branch). Normal pipeline: Roz diagnose -> Colby fix ->
Roz verify. Colby creates MR to main. After merge, Eva cherry-picks to
production branch if needed.

## Branch Cleanup

After MR merge, Eva deletes the feature branch (local + remote) and logs
cleanup in `{pipeline_state_dir}/pipeline-state.md`.

## CI Advisory

Run CI on MR events + push to main + push to staging/production. Protect all
environment branches.
