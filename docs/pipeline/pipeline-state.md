# Pipeline State

## Active Pipeline
**Feature:** Mechanical telemetry extraction — brain-extractor structured quality signals + hydrator state file parsing
**Phase:** build
<!-- PIPELINE_STATUS: {"phase": "review", "sizing": "small", "roz_qa": "PASS", "telemetry_captured": true, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": true, "robert_reviewed": false, "brain_available": true} -->
**Sizing:** Small
**Started:** 2026-04-06
**Seed:** (no seed — architecture derived from session conversation)

## Configuration
**Branching Strategy:** trunk-based
**Platform:** Claude Code
**Integration Branch:** main
**Feature Branch:** main (trunk-based)

## Progress
- [x] Cal → ADR (docs/architecture/ADR-0025-mechanical-telemetry-extraction.md, 4 steps, 2 waves, 43 tests)
- [x] Roz → test spec review + test authoring (49 tests, 25 Wave 1)
- [x] Wave 1: brain-extractor structured extraction (Step 1) — Roz PASS 15/15, Poirot clean
- [x] Wave 2: hydrator quality T3 + SessionStart hook + warn-dor-dod.sh removal (Steps 2-4)
- [ ] Review juncture
- [ ] Ellis → push

## Prior pipeline (ADR-0024 complete)
ADR-0024 Mechanical Brain Writes shipped as v3.24.0 / brain 1.1.0 (2026-04-06).

## Changes since last state
- Wave 1 complete: brain-extractor structured quality signal extraction (Step 1)
  - source_phase 'docs'→'handoff' for agatha (invalid enum fixed)
  - Quality signal captures use source_phase 'telemetry', thought_type 'insight'
  - drift_count/gap_count intentionally removed (Agatha output has no such labels)
  - Roz PASS 15/15 Wave 1 tests, 0 new baseline regressions
<!-- COMPACTION: 2026-04-06T16:03:18Z -->
<!-- COMPACTION: 2026-04-06T17:42:30Z -->
