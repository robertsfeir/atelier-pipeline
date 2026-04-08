# Pipeline State

## Active Pipeline
**Feature:** Fix marketplace.json version mismatch (3.27.0 → 3.27.1)
**Phase:** build
<!-- PIPELINE_STATUS: {"phase": "build", "sizing": "micro", "roz_qa": "PENDING", "telemetry_captured": false, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": false, "robert_reviewed": false, "brain_available": true} -->
**Sizing:** Micro
**Started:** 2026-04-08

## Context
Doctor flags "Plugin atelier-pipeline not found in marketplace atelier-pipeline" because marketplace.json lists version 3.27.0 but installed_plugins.json records 3.27.1. Doctor checks the marketplace index for the installed version and can't find it.

## Files to modify
- `.claude-plugin/marketplace.json` — bump version from 3.27.0 to 3.27.1

## Progress
- [x] Colby → bump version field in marketplace.json
