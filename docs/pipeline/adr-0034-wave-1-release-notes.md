# ADR-0034 Wave 1 Release Notes

## What Changed

Wave 1 of ADR-0034 closes two critical silent-drop bugs in the Atelier Brain:

1. **Brain enum extension (M1+M9):** `SOURCE_AGENTS` and `SOURCE_PHASES` in `brain/lib/config.mjs` now include all 16 agents and 14 phases. Previously, captures from `robert-spec`, `sable-ux`, `sentinel`, `darwin`, `deps`, and `brain-extractor` were silently discarded by Zod validation. The `handleTelemetryAgents` SQL query now uses a dynamic `IN` clause from `SOURCE_AGENTS` instead of a hardcoded literal (M9).

2. **ADR-0032 implementation (M3):** `pipeline-state-path.sh` helper created. Session state files now live in a per-worktree directory under `~/.atelier/pipeline/{project-slug}/{worktree-hash}/` instead of the shared `docs/pipeline/`. Concurrent sessions in different worktrees no longer clobber each other's state. `error-patterns.md` stays in-repo (unchanged per ADR-0032 Decision).

## Action Required

**Re-run `/pipeline-setup` in every project** where Atelier Pipeline is installed.

This updates your `.claude/settings.json` to fire the `brain-extractor` SubagentStop hook for all 9 target agents:

```
cal, colby, roz, agatha, robert, robert-spec, sable, sable-ux, ellis
```

Before Wave 1, the installed `settings.json` only fired for 4 agents (`cal`, `colby`, `roz`, `agatha`). Five agents' outputs were never captured to the brain.

## How to Verify

After re-running `/pipeline-setup`, confirm the fix:

1. Check `.claude/settings.json` — the `brain-extractor` SubagentStop condition should list all 9 agents.
2. Run a test capture: invoke any of the newly-added agents (e.g., have `robert-spec` produce a spec). The brain-extractor hook should fire and you should be able to find the capture via `atelier_browse`.

## Files Changed

- `brain/lib/config.mjs` — SOURCE_AGENTS extended to 16, SOURCE_PHASES extended to 14
- `brain/schema.sql` — enum CREATE TYPE updated for fresh installs
- `brain/migrations/008-extend-agent-and-phase-enums.sql` — NEW: idempotent enum extension
- `brain/lib/db.mjs` — migration 008 block added to runMigrations()
- `brain/lib/rest-api.mjs` — handleTelemetryAgents IN clause now dynamic
- `source/shared/hooks/pipeline-state-path.sh` — NEW: per-worktree state helper
- `source/claude/hooks/session-boot.sh` — uses helper instead of hardcoded path
- `source/claude/hooks/post-compact-reinject.sh` — uses helper instead of hardcoded path
