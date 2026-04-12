# Pipeline State

## Active Pipeline
**Feature:** ADR-0034 Gauntlet remediation — fix all register findings
**Phase:** review
<!-- PIPELINE_STATUS: {"phase": "review", "sizing": "medium", "roz_qa": "PASS", "telemetry_captured": true, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": true, "robert_reviewed": true, "brain_available": true} -->
**Sizing:** Medium
**Started:** 2026-04-11

## Wave Progress
- [x] Wave 1 — brain enum extension + ADR-0032 + enforcement fixes → commit `ebda3af`
- [x] Wave 2 — hook-lib.sh extraction + migration runner refactor + session-hydrate shim + Poirot fix round → commit `f3c0090`
- [ ] Wave 3 — brain correctness (M8 CORS, M10 dashboard XSS, S5 gracefulShutdown drain, S10 LLM null guards, M4 red test greening)
  - [x] Step 3.1 Roz triage: 8 test drift fixes applied, T-0034-046→T-0034-060 authored (RED pre-build), pytest 7→1 failure
  - [x] Steps 3.2–3.5 Colby build: rest-api.mjs CORS fix, dashboard.html XSS escaping, crash-guards.mjs async drain, llm-response.mjs null guards — 5 production files + 1 new module
  - [x] Roz test authoring: crash-guards.test.mjs, dashboard-xss.test.mjs, llm-response.test.mjs, rest-api.test.mjs appended — T-0034-049/050/051–060
  - [x] Roz hardening test update: T-0017-003/006/007/008/009/010 made async (ADR-0034 Step 3.4 drift) — 186 tests, 0 fail
  - [x] Wave 3 QA: Roz sweep PASS (186 tests, 0 fail) + Poirot blind diff (7 findings, all resolved) + Roz targeted re-check PASS (39/39)
  - [x] Wave 3 Ellis commit → 5b627cc (21 files)
- [x] Agatha docs: brain-hardening.md + technical-reference.md + CHANGELOG.md updated, all Robert N/A findings documented
- [ ] Ellis final push to remote (hard pause — trunk-based)
- [ ] Waves 4–6 — separate ADRs (ADR-0035, ADR-0036, ADR-0037)

## Context
Full review of source/claude/hooks/, source/shared/hooks/, source/claude/agents/, and
skills/pipeline-setup/SKILL.md revealed bugs and gaps. Constraint: Colby edits source/
only. .claude/ is not touched.

## Prior Pipeline (closed)
**Feature:** Fix marketplace.json version mismatch (3.27.0 → 3.27.1)
**Stop Reason:** user_cancelled (stale — new pipeline directive received 2026-04-11)

## All Findings

### Critical (must fix)
- C1: source/shared/hooks/session-boot.sh — PIPELINE_STATUS pattern `{.*}` (no space) vs
  canonical format `PIPELINE_STATUS: {` (with space) — boot always reports pipeline_active=false
- C2: skills/pipeline-setup/SKILL.md — enforce-scout-swarm.sh missing from file manifest
  AND settings.json template — fresh installs have zero scout swarm enforcement

### Major (must fix)
- M1: source/claude/hooks/enforcement-config.json — missing .github/ in colby_blocked_paths
  (Colby can overwrite CI workflows on fresh installs)
- M2: source/shared/hooks/session-boot.sh — CORE_AGENTS list missing 6 agents
  (sentinel, darwin, deps, brain-extractor, robert-spec, sable-ux)
- M3: source/claude/hooks/enforce-scout-swarm.sh — Roz evidence block not validated
  for content (empty <debug-evidence> tag passes)
- M4: skills/pipeline-setup/SKILL.md — session-hydrate.sh description wrong ("Runs
  telemetry hydration") and should be updated; source comment says no-op

### Minor (should fix)
- m1: source/claude/hooks/enforce-roz-paths.sh — header comment says "Write|Edit", should be "Write"
- m2: source/claude/hooks/enforce-cal-paths.sh — dead MultiEdit case branch (unreachable code)
- m3: source/claude/hooks/post-compact-reinject.sh — brain reminder says "injects" but only reminds
- m4: source/claude/hooks/prompt-brain-prefetch.sh — scope includes agatha but scout enforcement doesn't
- m5: source/claude/agents/brain-extractor.frontmatter.yml — full model ID instead of shorthand "haiku"

### Design Gaps (in scope — user confirmed)
- G1: skills/pipeline-setup/SKILL.md — brain-extractor if: condition missing robert, robert-spec,
  sable, sable-ux, ellis (same Haiku extractor pattern, extend existing hook)
- G2: source/claude/hooks/prompt-brain-prefetch.sh scope mismatch (same file as m4)

## Files to Modify
- source/shared/hooks/session-boot.sh (C1 + M2)
- source/claude/hooks/enforce-scout-swarm.sh (M3)
- source/claude/hooks/enforcement-config.json (M1)
- source/claude/hooks/enforce-roz-paths.sh (m1)
- source/claude/hooks/enforce-cal-paths.sh (m2)
- source/claude/hooks/post-compact-reinject.sh (m3)
- source/claude/hooks/prompt-brain-prefetch.sh (m4/G2)
- source/claude/agents/brain-extractor.frontmatter.yml (m5)
- skills/pipeline-setup/SKILL.md (C2 + M4 + G1)

## Progress
- [x] Cal → ADR-0033 at docs/architecture/ADR-0033-hook-enforcement-audit-fixes.md, 10 steps, 2 waves, 30 test IDs
- [x] Roz → test spec review (PASS — 30 specs sound, 0 gaps)
- [x] Roz → test authoring (30 tests across 10 files; 23 red pre-build, 7 green)
- [x] Colby → implement (wave 1: 12 source files; Poirot F2+F6 fixed post-review)
- [x] Roz QA Wave 1: 26/26 PASS. Poirot: 2 MUST-FIX resolved, 6 NIT accepted.
- [x] Ellis → Wave 1 commit: 460381f (23 files, 1382 insertions)
- [x] Colby → implement (wave 2: SKILL.md, Steps 8-10, 5/5 tests PASS)
- [x] Roz QA Wave 2: 5/5 PASS. Poirot: 3 MUST-FIX resolved, 3 accepted.
- [x] Ellis → Wave 2 commit: 9b73eec (2 files)
- [x] Robert → skipped (no spec/UI — ADR-0033 is infrastructure only, N/A per ADR)
- [x] Agatha → docs/guide/technical-reference.md + docs/product/mechanical-brain-writes.md updated (11 locations, 9-agent scope + Agatha source_phase correction)
- [ ] Ellis → final commit + push (includes source/shared/references/gauntlet.md — added post-Wave 2)
<!-- COMPACTION: 2026-04-11T20:55:08Z -->
<!-- COMPACTION: 2026-04-11T22:10:49Z -->
<!-- COMPACTION: 2026-04-11T22:42:32Z -->
<!-- COMPACTION: 2026-04-11T23:17:47Z -->
<!-- COMPACTION: 2026-04-12T00:46:05Z -->
<!-- COMPACTION: 2026-04-12T02:07:11Z -->
<!-- COMPACTION: 2026-04-12T03:35:53Z -->
<!-- COMPACTION: 2026-04-12T04:04:44Z -->
