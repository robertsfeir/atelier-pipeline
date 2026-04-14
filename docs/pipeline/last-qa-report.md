## QA Report -- 2026-04-14

### ADR-0032 last-mile + ADR-0038 Worktree-Per-Session

### Verdict: FAIL (1 FIX-REQUIRED before Ellis)

| Check | Status | Details |
|-------|--------|---------|
| Tier 1: Test suite (new file) | PASS | 11/11 pass, 0 new failures |
| Tier 1: TODO/FIXME/HACK/XXX | PASS | 0 matches across all changed files |
| Tier 2: ADR-0038 test spec (T-0038-001 to T-0038-030) | PASS | All 30 items verified |
| Tier 2: ADR-0032 last-mile (state_dir paragraph) | PASS | Present and correct in both source and .claude session-boot.md |
| Tier 2: Spec drift -- forbidden language | PASS | Zero matches for "Colby creates the feature branch" or "(non-worktree)" in variants/ and branch-mr-mode.md |
| Tier 2: branch-mr-mode.md preamble | FIX-REQUIRED | Line 7 still says "Colby handles branch creation" -- contradicts corrected body |

---

### Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| R1 | Every session that creates a branch gets its own worktree | Implemented | `<protocol id="worktree-per-session">` at line 399 in pipeline-orchestration.md | PASS |
| R2 | Worktree location: sibling `../<slug>-<session-id>/` | Implemented | Line 421: `WORKTREE_PATH="../${PROJECT_SLUG}-${SESSION_ID}"` | PASS |
| R3 | Session ID: 8 random hex chars (openssl rand -hex 4) | Implemented | Line 412: `SESSION_ID=$(openssl rand -hex 4)` | PASS |
| R4 | Same session ID for worktree dir, branch name, state | Implemented | Single SESSION_ID var drives both BRANCH_NAME and WORKTREE_PATH in creation sequence | PASS |
| R5 | Branch naming table: micro/small -> session/, medium/large -> feature/ | Implemented | Table present in protocol (lines 432-439) and all 4 variant files | PASS |
| R6 | Eva infers branch type from pipeline sizing | Implemented | Table drives inference; no extra ceremony added | PASS |
| R7 | Trunk-based: session branch + ff merge to main | Implemented | trunk-based.md and protocol Trunk-Based Integration section | PASS |
| R8 | Eva creates worktree BEFORE any Colby invocation | Implemented | Explicit "before any Colby invocation" language at line 404 | PASS |
| R9 | Eva copies .claude/brain-config.json to worktree | Implemented | Lines 426-429 in creation sequence | PASS |
| R10 | Agents receive worktree path via constraints tag | Implemented | Agent Path Constraint section with exact constraint text | PASS |
| R11 | Ellis removes worktree after successful MR/merge | Implemented | Worktree Cleanup section in ellis.md | PASS |
| R12 | git worktree add/remove NOT blocked by enforce-git.sh | Implemented | Tests T-0038-018 through T-0038-020 all pass | PASS |
| R13 | Branch lifecycle files remove Colby branch-creation language | Implemented | grep returns empty on all 4 variant files | PASS |
| R16 | No sessions.json registry | Implemented | No registry added anywhere in changed files | PASS |

### T-0038 Test Spec -- All 30 Items

| Test ID | Description | Status |
|---------|-------------|--------|
| T-0038-001 | protocol section has all 8 subsections (creation, failure, copy, state, constraint, trunk, cleanup, Agent Teams) | PASS |
| T-0038-002 | protocol specifies creation BEFORE any Colby invocation | PASS |
| T-0038-003 | branch naming table present (micro/small/medium/large) | PASS |
| T-0038-004 | failure is pipeline-start blocker; Eva does NOT proceed | PASS |
| T-0038-005 | brain-config.json copy specified in protocol | PASS |
| T-0038-006 | pipeline-state.md template has Worktree Path and Session ID fields | PASS |
| T-0038-007 | PIPELINE_STATUS JSON has worktree_path, session_id, branch_name | PASS |
| T-0038-008 | github-flow: no "Colby creates the feature branch" or "(non-worktree)" | PASS |
| T-0038-009 | github-flow: Eva named as branch/worktree creator | PASS |
| T-0038-010 | gitlab-flow: no forbidden language | PASS |
| T-0038-011 | gitlab-flow: Eva named as creator | PASS |
| T-0038-012 | gitflow: no "Colby creates feature branches from develop" | PASS |
| T-0038-013 | gitflow: develop as base in worktree add command | PASS |
| T-0038-013b | gitflow: Eva named as creator | PASS |
| T-0038-014 | trunk-based: session/<8-hex> pattern documented | PASS |
| T-0038-015 | trunk-based: ff merge to main at pipeline end | PASS |
| T-0038-016 | branch-mr-mode: branch creation attributed to Eva | PASS (body correct -- see FIX-REQUIRED for preamble) |
| T-0038-017 | branch-mr-mode: Colby's MR creation responsibility retained | PASS |
| T-0038-018 | git worktree add exits 0 for main thread (Eva) | PASS (pytest) |
| T-0038-018b | git worktree add exits 0 for agent_type="colby" | PASS (pytest) |
| T-0038-019 | git worktree remove exits 0 for ellis | PASS (pytest) |
| T-0038-020 | git worktree list exits 0 for any agent | PASS (pytest -- 3 agents tested) |
| T-0038-021 | git add still exits 2 for main thread (regression) | PASS (pytest) |
| T-0038-022 | git commit still exits 2 for colby (regression) | PASS (pytest) |
| T-0038-023 | enforce-git.sh contains ADR-0038 intentional-allowance comment | PASS (pytest) |
| T-0038-024 | ellis.md contains worktree cleanup workflow section | PASS |
| T-0038-025 | session branch force-delete (-D) allowed | PASS (lines 56-59 in ellis.md) |
| T-0038-026 | feature branch NOT force-deleted (warns instead) | PASS (lines 48, 60 in ellis.md) |
| T-0038-027 | pipeline-orchestration.md references Ellis cleanup in Ellis-related section | PASS (lines 129-133 and 501-502) |
| T-0038-027b | Ellis cleanup distinguishes MR-based from trunk-based trigger | PASS (lines 39-52 in ellis.md: separate MR-based and trunk-based blocks) |
| T-0038-028 | No "Colby creates the feature branch" in source/shared/variants/ | PASS (grep empty) |
| T-0038-029 | No "(non-worktree)" in source/shared/variants/ | PASS (grep empty) |
| T-0038-030 | No "(non-worktree)" in branch-mr-mode.md | PASS (grep empty) |

### ADR-0032 Last-Mile

| File | state_dir paragraph present | error-patterns.md anchor correct | Finding |
|------|----------------------------|----------------------------------|---------|
| source/shared/references/session-boot.md | YES (lines 22-27) | YES (line 26: "always stays at docs/pipeline/error-patterns.md regardless of state_dir") | PASS |
| .claude/references/session-boot.md | YES (same content confirmed) | YES | PASS |

Both copies are consistent. The fix is correctly scoped: state_dir drives pipeline-state.md, context-brief.md, investigation-ledger.md, and last-qa-report.md only. error-patterns.md stays at docs/pipeline/ unconditionally.

---

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across all changed files: **0 matches**

---

### Issues Found

**FIX-REQUIRED** (`source/shared/references/branch-mr-mode.md`, line 7):

The file's introductory paragraph reads:

> "When the pipeline uses an MR-based branching strategy (GitHub Flow, GitLab Flow, GitFlow), Colby handles branch creation and MR creation."

The body of the same file (lines 11-17) directly contradicts this:

> "Eva creates the feature branch and worktree at pipeline start..."
> "Colby receives the worktree path in her invocation constraints and operates entirely within the worktree. Colby does NOT create or check out branches."

T-0038-016 checks that branch creation is attributed to Eva and passes (the body is correct). However, the stale preamble sentence creates a direct contradiction within the same file. A reader who only reads the summary line gets the wrong mental model before reaching the corrected content.

**Recommended fix (Colby, production file):** Change line 7 from:
> "Colby handles branch creation and MR creation."

To:
> "Eva creates the branch and worktree at pipeline start. Colby handles MR creation."

This is a one-line change in a production file. Roz does not touch production files -- route to Colby.

---

### Doc Impact: NO

ADR-0038 status field already updated to "Implemented." No further doc changes required.

---

### Roz's Assessment

All 11 new hook regression tests pass cleanly. The enforce-git.sh comment is present, the behavior is correct, and regression guards for blocked operations (git add, git commit) still hold. The ADR-0032 last-mile fix is present in both the source template and the installed .claude copy -- the state_dir and error-patterns.md scoping are correctly specified.

All 30 ADR-0038 test spec items are satisfied. The four variant files are clean, the pipeline-state.md template has the new fields, pipeline-orchestration.md has the complete protocol, and ellis.md has the correct MR-based vs trunk-based distinction.

The single FIX-REQUIRED is a stale introductory sentence in branch-mr-mode.md that contradicts its own corrected body. It does not affect runtime behavior -- agents read the full file -- but it will mislead anyone skimming the file. One line, Colby fixes, then clear to Ellis.
