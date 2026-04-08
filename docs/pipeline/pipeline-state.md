# Pipeline State

## Active Pipeline
**Feature:** Model Assignment Gap Fix — Explore agent + investigation intent routing
**Phase:** build
<!-- PIPELINE_STATUS: {"phase": "commit", "sizing": "micro", "roz_qa": "PASS", "telemetry_captured": false, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": false, "robert_reviewed": false, "brain_available": true} -->
**Sizing:** Micro (user-chosen)
**Started:** 2026-04-07

## Context
Fix: pipeline defaults to Opus 4.6 for codebase investigation tasks instead of Haiku.
Root causes:
1. Explore agent not in pipeline-models.md base models table → classifier promotes security scans to Opus
2. No auto-routing row for "scan/investigate codebase" intent in agent-system.md
3. No scoring signal demoting read-only investigation tasks

## Files to modify
- source/shared/rules/pipeline-models.md
- source/shared/rules/agent-system.md
- source/shared/references/invocation-templates.md

## Progress
- [ ] Colby → add Explore to model table, add investigation scoring signal, add routing row, add template

## Prior pipeline (ADR-0027 complete, Ellis push pending)
ADR-0027 Brain-Hydrate Scout Fan-out shipped (all 36 tests pass). Ellis push still needed.

## Prior pipeline (ADR-0031 complete)
ADR-0031 Permission Audit Trail + ADR-0030 Token Exposure Probe (v3.27.0)
