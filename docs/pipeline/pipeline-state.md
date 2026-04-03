# Pipeline State

## Active Pipeline
**Feature:** Agent frontmatter enrichment — Waves 2 & 3 (#28, #29)
**Phase:** review
<!-- PIPELINE_STATUS: {"phase": "commit", "sizing": "medium", "roz_qa": "PASS", "telemetry_captured": true, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": ""} -->
**Sizing:** Medium
**Started:** 2026-04-02

## Configuration
**Branching Strategy:** trunk-based
**Platform:** ---
**Integration Branch:** main
**Feature Branch:** main (trunk-based)

## Progress

### Wave 1 — Frontmatter enrichment (#27) ✓ SHIPPED
Committed as `596dfc5` (v3.16.0). All 12 agents have `model`, `effort`, `color`, `maxTurns`, `disallowedTools` frontmatter.

### Wave 2 — Hook modernization (#28)

| # | Unit | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 2a | Add `if` conditionals to existing hooks | Colby | queued | Reduce ~80% hook process spawns |
| 2b | SubagentStart/SubagentStop telemetry hooks | Colby | queued | log-agent-start.sh, log-agent-stop.sh → brain Tier 1 |
| 2c | PostCompact hook for context preservation | Colby | queued | post-compact-reinject.sh → re-inject pipeline-state + context-brief |
| 2d | StopFailure hook for error tracking | Colby | queued | log-stop-failure.sh → error-patterns.md |

### Wave 3 — Advanced features (#29)

| # | Unit | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 3a | `defer` permission decision in PreToolUse | Colby | queued | Soft guidance (defer) vs hard blocks (deny) |
| 3b | Per-agent `memory` frontmatter | Colby | queued | Colby, Cal, Roz get `memory: project` — complementary to Brain |
| 3c | `permissionMode` per agent | Colby | queued | Robert/Sable/Investigator/Distillator/Darwin/Deps/Sentinel → `plan` |
| 3d | Agent-scoped `hooks` in frontmatter | Colby | queued | Roz test-file-only enforcement moves to her frontmatter |

## Queue
Wave 2 → Wave 3 (sequential). Each wave needs Cal ADR → Roz test spec → Colby build → Roz QA.

## Changes since last state
- Wave 1 shipped (v3.16.0, commit 596dfc5)
- Pipeline-setup re-run (v3.6.6 → v3.15.1), then version bumped to v3.16.0
- State file restored after template overwrite during setup
