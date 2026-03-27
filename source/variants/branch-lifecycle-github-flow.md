---
paths:
  - "docs/pipeline/**"
---

# Branch Lifecycle: GitHub Flow

Every feature pipeline uses a feature branch. Main receives code only through
merge requests with passing CI.

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

## Hotfix Flow

When the user reports a production bug, Colby creates `hotfix/<name>` from
main. Normal pipeline: Roz diagnose -> Colby fix -> Roz verify. Colby creates
MR to main. No cherry-picks needed — main is the only long-lived branch.

## Branch Cleanup

After MR merge, Eva deletes the feature branch (local + remote) and logs
cleanup in `{pipeline_state_dir}/pipeline-state.md`.

## CI Advisory

Run CI on MR events + push to main. Protect main.
