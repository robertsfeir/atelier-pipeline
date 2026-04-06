# Pipeline State

## Active Pipeline
**Feature:** Mechanical brain writes — SubagentStop hook + agent instruction cleanup
**Phase:** spec
<!-- PIPELINE_STATUS: {"phase": "build", "sizing": "medium", "roz_qa": "PASS", "telemetry_captured": false, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": true, "robert_reviewed": false, "brain_available": true} -->
**Sizing:** Medium
**Started:** 2026-04-05
**Seed:** 55e79a4d-00c8-41a7-9232-a33ef5eb4c11

## Configuration
**Branching Strategy:** trunk-based
**Platform:** Claude Code
**Integration Branch:** main
**Feature Branch:** main (trunk-based)

## Progress
- [x] Robert-spec → spec (docs/product/mechanical-brain-writes.md)
- [x] Cal → ADR (docs/architecture/ADR-0024-mechanical-brain-writes.md, 9 steps, 3 waves)
- [x] Roz → test spec (67 tests authored)
- [x] Wave 1: brain-extractor agent + SubagentStop hook — Roz PASS 22/22, Poirot PASS
- [x] Wave 2: behavioral cleanup — personas + preamble — Roz PASS 13/13, Poirot 0 BLOCKERs (5 findings deferred to Wave 3)
- [ ] Wave 3: hook removal + frontmatter + doc updates
- [ ] Review juncture: Roz sweep + Poirot + Robert-subagent
- [ ] Agatha → docs
- [ ] **HARD PAUSE** → Ellis push

## Prior pipeline (ADR-0023 paused)
ADR-0023 Agent Specification Reduction — Phase 1 of 12 steps. This pipeline supersedes ADR-0023 R6 (brain capture consolidation) entirely; remaining ADR-0023 requirements still pending.

## Changes since last state
- New pipeline started: mechanical brain writes (seed 55e79a4d)
- Supersedes ADR-0023 R6 (brain capture consolidation)
