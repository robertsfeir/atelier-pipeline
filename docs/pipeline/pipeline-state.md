# Pipeline State

## Active Pipeline
**Feature:** Wave 1 — Agent persona frontmatter enrichment (#27)
**Phase:** build
**Sizing:** Small
**Started:** 2026-04-02

## Configuration
**Branching Strategy:** trunk-based
**Platform:** ---
**Integration Branch:** main
**Feature Branch:** main (trunk-based)

<!-- PIPELINE_STATUS: {"phase":"build","sizing":"small","roz_qa":"PASS","telemetry_captured":true,"ci_watch_active":false,"ci_watch_retry_count":0,"ci_watch_commit_sha":""} -->

## Progress

| # | Unit | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 1 | Add frontmatter to all 12 source/agents/*.md | Colby | done | model, effort, color, maxTurns |
| 2 | Sync .claude/agents/ from source/agents/ | Colby | done | Frontmatter synced, body preserved |
| 3 | Update behavioral text (remove "You run on X") | Colby | done | Removed from all 12 agents |
| 4 | QA verification | Roz | PASS | Final sweep: 68/68 bats, 93/93 brain tests pass |

## Queue
(empty)

## Changes since last state
- Units 1-3 complete (Colby). Fix round: Darwin model→opus, model IDs→short aliases, placeholder regression restored
- Unit 4 complete (Roz). Verdict: PASS. One pre-existing FIX-REQUIRED noted (out of scope)
- User correction: colors only on Cal/Colby/Roz/Ellis/Robert/Sable (6 of 12)
- Eva verification: all 7 checks pass against brain + pipeline-models.md
