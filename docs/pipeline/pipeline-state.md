# Pipeline State

## Active Pipeline
**Feature:** Wave 3 — Native Enforcement Redesign (ADR-0022)
**Phase:** build (Phase 2, Wave 1 — Steps 2a+2d+2e+2g: enforcement layer + cleanup)
<!-- PIPELINE_STATUS: {"phase": "build", "sizing": "medium", "roz_qa": "PASS", "telemetry_captured": true, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": true, "robert_reviewed": false} -->
**Sizing:** Medium
**Started:** 2026-04-03

## Configuration
**Branching Strategy:** trunk-based
**Platform:** ---
**Integration Branch:** main
**Feature Branch:** main (trunk-based)

## Progress

### Wave 1 — Frontmatter enrichment (#27) ✓ SHIPPED
Committed as `596dfc5` (v3.16.0). All 12 agents have `model`, `effort`, `color`, `maxTurns`, `disallowedTools` frontmatter.

### Wave 2 — Hook modernization (#28) ✓ SHIPPED
Committed as `bda22ad` (v3.17.0). `if` conditionals on enforce-git + warn-dor-dod. 4 new lifecycle hooks: log-agent-start, log-agent-stop, post-compact-reinject, log-stop-failure. 69 bats tests. ADR-0020.

### Wave 3 — Advanced features (#29) — NOT STARTED
Deferred. Depends on review findings remediation completing first.

| # | Unit | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 3a | `defer` permission decision in PreToolUse | Colby | queued | Soft guidance (defer) vs hard blocks (deny) |
| 3b | Per-agent `memory` frontmatter | Colby | queued | Colby, Cal, Roz get `memory: project` — complementary to Brain |
| 3c | `permissionMode` per agent | Colby | queued | Robert/Sable/Investigator/Distillator/Darwin/Deps/Sentinel → `plan` |
| 3d | Agent-scoped `hooks` in frontmatter | Colby | queued | Roz test-file-only enforcement moves to her frontmatter |

### Review Findings Remediation (Roz full audit, 2026-04-02)

Source: `docs/pipeline/last-qa-report.md`. Addresses blockers B1-B4 and fix-required F2.

| # | Item | Agent | Status | Notes |
|---|------|-------|--------|-------|
| M-1 | Add Poirot (gate 5) + Robert (gate 7) enforcement to enforce-sequencing.sh | Colby | done | New PIPELINE_STATUS fields: poirot_reviewed, robert_reviewed |
| M-2 | Add `colby_blocked_paths` to enforcement-config.json | Colby | done | B1 closed — 14 blocked prefixes added |
| M-3 | Update CLAUDE.md test commands to real bats/node command | Colby | done | Now points to real bats+node command |
| M-4 | {config_dir} placeholder + telemetry hook IDE detection | Colby | done | Replaced hardcoded .claude/ in source templates, fixed hook path derivation |
| M-5 | {features_dir} + {source_dir} placeholders in SKILL.md | Colby | done | Added to placeholder table + Step 1 collection |
| Cursor P1a | Sync agent frontmatter to .cursor-plugin/agents/ | Colby | done | 12 agents synced, byte-identical to source/ |
| Cursor P1b | Sync brain protocol in 3 .mdc rule files | Colby | done | agent-system, default-persona, pipeline-orchestration regenerated |
| Cursor P1c | Add brain-access protocol to .cursor-plugin/agents/agatha.md | Colby | done | Part of P1a sync |
| Cursor P2a | Add 5 missing reference docs as .mdc files | Colby | done | SKILL.md Step 3c + 5 .mdc files created |
| Cursor P2b | Fix duplicate frontmatter in colby.md and robert.md | Colby | done | Overwritten with clean source/ copies |

## Uncommitted Changes (on disk, not yet committed)
ADR-0021 brain wiring: settings.json hook registrations (prompt-brain-prefetch, prompt-brain-capture, warn-brain-capture), agent persona updates (agatha, cal, ellis), rule/reference updates. These changes predate the remediation work.

## Queue
**→ Ellis per-wave commit (Phase 2 Wave 1)** → Colby Wave 2 (Steps 2c+2f: producer personas + routing) → Roz+Poirot QA → Ellis per-wave commit → Colby Wave 3 (Step 2h: compaction advisory) → Roz+Poirot QA → Ellis per-wave commit → review juncture → Ellis final commit.

## Changes since last state
- Phase 2 Wave 1 built by Colby (Steps 2a+2d+2e+2g):
  - 7 per-agent enforcement scripts created in source/claude/hooks/
  - enforce-paths.sh monolith deleted from source/claude/hooks/
  - enforcement-config.json simplified (removed architecture_dir, product_specs_dir, ux_docs_dir)
  - permissionMode: acceptEdits added to 4 Claude overlays (colby, cal, agatha, ellis)
  - hooks: field added to 6 Claude overlays (roz, cal, colby, agatha, robert-spec, sable-ux)
  - SKILL.md updated (settings.json registration: enforce-paths.sh → enforce-eva-paths.sh)
  - test_enforce_paths.py deleted (monolith tests replaced by per-agent tests)
  - test_doc_sync.py updated for platform-specific enforcement architecture
  - test_if_conditionals.py updated (enforce-paths → enforce-eva-paths)
  - test_adr_0022_phase1_overlay.py updated (hook count 14 → 20)
  - docs/guide/technical-reference.md + user-guide.md updated
  - CLAUDE.md updated with robert-spec/sable-ux
  - pm.md, ux.md, create-agent.md, darwin.md updated (enforce-paths.sh → per-agent)
- Roz QA: Initial FAIL (4 BLOCKERs) → fixes applied → PASS
- Poirot: 3 BLOCKERs, 5 FIX-REQ, 3 NITs — key fixes: path normalization, CURSOR_PROJECT_DIR fallback
- Tests: 607 pass, 10 fail (all future-wave TDD: 3 cleanup + 7 compaction)
<!-- COMPACTION: 2026-04-03T20:04:01Z -->
<!-- COMPACTION: 2026-04-03T20:53:39Z -->
