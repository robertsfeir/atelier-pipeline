# Pipeline State

## Active Pipeline
**Feature:** ADR-0028 Named Stop Reason Taxonomy + ADR-0029 Token Budget Estimate Gate (v3.26.0)
**Phase:** complete
<!-- PIPELINE_STATUS: {"phase": "complete", "sizing": "small", "roz_qa": "PASS", "telemetry_captured": true, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": true, "robert_reviewed": false, "brain_available": true} -->
**Sizing:** Small
**Started:** 2026-04-07
**Seed:** brain-extractor emits a bare summary with no agent name or [Info]/[Warning] prefix — indistinguishable from agent prose in the conversation

## Configuration
**Branching Strategy:** trunk-based
**Platform:** Claude Code
**Integration Branch:** main
**Feature Branch:** main (trunk-based)

## Progress
- [x] Cal → ADR-0027 (docs/architecture/ADR-0027-brain-hydrate-scout-fanout.md, 1 step, 31 tests)
- [x] Roz → test spec review (APPROVED WITH GAPS — 5 gaps found + fixed, 36 tests total)
- [x] Roz → test authoring (36 tests written, 23 fail pre-build, 12 pass, 1 skip — tests/adr-0027/test_brain_hydrate_scout_fanout.py)
- [x] Colby → implement scout swarm (36/36 tests pass)
- [x] Roz QA + Poirot (parallel) — Roz PASS 36/36, Poirot 1 BLOCKER + 4 FIX-REQUIRED found
- [x] Colby → fix Poirot findings (6 fixes, 36/36 still pass)
- [x] Roz re-verify — PASS 36/36
- [x] Sync: .cursor-plugin/skills/brain-hydrate/SKILL.md + .claude/rules/pipeline-orchestration.md
- [ ] Ellis → push

## Prior pipeline (ADR-0026 complete)
ADR-0026 Beads-style provenance shipped (ebe6651, 2026-04-06). brain v1.3.0. 28/28 provenance tests, 121/121 brain suite.

## Prior pipeline (ADR-0025 complete)
ADR-0025 Mechanical Telemetry Extraction shipped as v3.25.0 (2026-04-06). v3.25.1 diagnostic scout swarm, v3.25.2 permissionMode + hook fix also shipped same day.

## Changes since last state
- Wave 1 complete: brain-extractor structured quality signal extraction (Step 1)
  - source_phase 'docs'→'handoff' for agatha (invalid enum fixed)
  - Quality signal captures use source_phase 'telemetry', thought_type 'insight'
  - drift_count/gap_count intentionally removed (Agatha output has no such labels)
  - Roz PASS 15/15 Wave 1 tests, 0 new baseline regressions
<!-- COMPACTION: 2026-04-06T16:03:18Z -->
<!-- COMPACTION: 2026-04-06T17:42:30Z -->
<!-- COMPACTION: 2026-04-07T00:48:51Z -->
<!-- COMPACTION: 2026-04-07T02:12:35Z -->
<!-- COMPACTION: 2026-04-07T14:06:34Z -->
