# Agatha — Documentation Coverage

**Round:** Gauntlet Round 9
**Date:** 2026-04-11
**Auditor:** Agatha (Documentation Specialist, she/her)
**Mode:** Read-only. No source modified.
**Scope:** `docs/`, `brain/`, `source/` — contributor-facing documentation coverage

---

## Summary

Documentation coverage for this codebase is exceptionally strong at the user and operational layer. `docs/guide/technical-reference.md` is a genuinely rare artifact: a ~2,500-line contributor reference that accurately describes orchestration logic, hook mechanics, brain architecture, model selection, telemetry tiers, and the agent enforcement pyramid at implementation depth. The two most critical gaps are (1) the triple-source assembly architecture (`source/shared` + `source/claude` + `source/cursor`) is not documented in either the user guide or the technical reference — a contributor modifying an agent persona today has no documented path for doing so correctly — and (2) the migration table in the technical reference documents only migrations 001–002 while the actual directory contains seven migrations (001–007), creating a verified spec-vs-code divergence. The Gauntlet itself is documented in an agent-facing reference file (`references/gauntlet.md`) but has no user-guide entry point, making it invisible to users who have not read the installed references directly.

---

## Coverage Assessment

| Area | Documented? | Gap | Priority |
|------|-------------|-----|----------|
| Triple-source assembly architecture (`source/shared` + overlays) | No | No prose in user guide or technical reference explaining the three-directory split, the frontmatter overlay pattern, or how a contributor adds/modifies an agent | Critical |
| Brain migration table completeness | Partial | Technical reference documents migrations 001–002; actual directory contains 001–007 (migrations 003–006 add `devops`, `pattern`, `seed`, `telemetry`, `ci-watch`, `pipeline` enum values; 007 is a DDL-free Beads record) | High |
| Brain REST API — full endpoint set | Partial | Technical reference documents 4 telemetry endpoints. Actual `rest-api.mjs` also exposes `/api/health`, `/api/config` (GET+PUT), `/api/thought-types` (GET+PUT), `/api/purge-expired`, `/api/stats` — 5 additional routes undocumented | High |
| Brain auth model for REST API | No | `rest-api.mjs` implements Bearer token auth controlled by an `apiToken` config field. Auth model, token provisioning, and the `/api/health` exemption are not documented anywhere in the guide docs | High |
| Enforcement hook system — contributor addition path | No | How to add a new enforcement hook is not documented. The three-layer pyramid is described behaviorally, but the mechanical steps (create script, add frontmatter overlay, register in settings) are absent | High |
| pipeline-config.json feature flags | Yes | All fields documented in technical reference with types, defaults, and upgrade-safety notes | — |
| Brain database schema | Yes | Full table descriptions, thought types, source phases, relation types, and TTL model documented | — |
| Auto-migration pattern | Partial | Pattern documented, but only 2 of 7 migrations described. Migrations 003–006 are undocumented additions that modified the closed `thought_type` and `source_phase` enums | High |
| Agent assembly / install process | Partial | `/pipeline-setup` flow documented. The underlying overlay assembly mechanism (frontmatter.yml + shared body = installed agent file) lives only in the ADR-0022 distillate in `docs/pipeline/` — not surfaced in the technical reference | High |
| Operational runbooks (run, debug, monitor) | Partial | Startup via `brain/start.sh` documented. Docker setup referenced but `docker-compose.yml` usage not described. No "how to debug a failing brain server" or "how to check brain connection health" runbook | Medium |
| ADR index completeness | Partial | `docs/architecture/README.md` lists 13 of 30 ADRs. Missing from the index: ADR-0011, 0012, 0016, 0017, 0018, 0019, 0022, 0023, 0024, 0025, 0026, 0028, 0029, 0030, 0031, 0032, 0033 (17 ADRs absent) | Medium |
| Technical reference → ADR cross-references | Partial | Technical reference cross-references section cites only ADR-0009 and ADR-0010 by link. Inline references exist for ADR-0004, 0013, 0015, 0016, 0025, 0028, 0029, 0030, 0031 as design rationale pointers | Medium |
| Gauntlet documented in user guide | No | `gauntlet.md` is an installed reference file with full procedural documentation, but is not mentioned in the user guide's table of contents or any user-guide section | Medium |
| Brain capture model end-to-end | Yes | SubagentStop → brain-extractor → Zod validation → `agent_capture` documented in detail, including per-agent quality signal extraction schemas | — |
| Cursor vs. Claude Code platform differences | Yes | Platform comparison table present in both user guide and technical reference at top-level | — |
| Enforcement audit trail | Yes | JSONL log schema, brain capture shape, querying instructions, and fail-open guarantees all documented | — |
| Telemetry hydration end-to-end | Yes | CLI flags, JSONL discovery, cost computation, duplicate detection, Tier 3 summary generation documented | — |
| State file recovery mechanism | Yes | Five state files, reset behavior, and recovery sequence documented | — |
| Wave execution + Agent Teams | Yes | Worktree rules, task lifecycle, fallback behavior, mandatory gate notes documented | — |
| Operational runbook — `brain/start.sh` | Partial | `start.sh` described as a wrapper. No documentation on required environment variables, restart procedure, or startup failure diagnosis | Medium |

---

## Findings

| # | Severity | Layer | Category | Finding | Location | Recommendation |
|---|----------|-------|----------|---------|----------|----------------|
| 1 | **Critical** | Contributor | Missing Architecture | The triple-source assembly architecture (`source/shared/` + `source/claude/` + `source/cursor/` overlay pattern) is not documented in either the user guide or the technical reference. A contributor who wants to modify an agent persona, add a new hook, or understand why `source/` has three subdirectories has no documented path. The mechanism is described only in the ADR-0022 distillate at `docs/pipeline/adr-0022-distillate.md`, a pipeline-state artifact — not a contributor reference. | `docs/guide/technical-reference.md` (missing section); actual implementation at `source/claude/agents/colby.frontmatter.yml` + `source/shared/agents/colby.md` | Add a "Source Architecture" section to the technical reference documenting: (a) the three-directory split and rationale, (b) the frontmatter overlay assembly algorithm, (c) the rule that `source/shared/` files must contain no YAML frontmatter, (d) the constraint that contributors edit `source/shared/` and run `/pipeline-setup` to sync `.claude/` — never editing `.claude/` directly. |
| 2 | **High** | Brain | Divergence | The technical reference documents 2 database migrations (`001-add-captured-by.sql`, `002-add-handoff-enums.sql`) but the actual `brain/migrations/` directory contains 7 migrations. Migrations 003–006 add enum values (`devops`, `pattern`, `seed`, `telemetry`, `ci-watch`, `pipeline`) corresponding to documented features. Migration 007 (`beads-provenance-noop.sql`) is a DDL-free design decision record. | `docs/guide/technical-reference.md` lines 922–929; `brain/migrations/` (7 files) | Add migrations 003–007 to the migration table. Note that migration 007 is DDL-free — it exists as a versioned decision record, not a schema change. |
| 3 | **High** | Brain | Missing API Docs | The brain HTTP server exposes 9 REST routes. The technical reference documents 4 (telemetry endpoints). Five routes are undocumented: `/api/health` (GET), `/api/config` (GET/PUT), `/api/thought-types` (GET/PUT), `/api/purge-expired` (POST), `/api/stats` (GET). These are used by the Settings UI and brain health checks. | `brain/lib/rest-api.mjs` lines 37–69; `docs/guide/technical-reference.md` REST API section | Add the 5 undocumented endpoints to the REST API table. Include the auth model: Bearer token required on all routes except `/api/health`; token sourced from `apiToken` config field. |
| 4 | **High** | Brain | Missing Auth Docs | The REST API auth model is not documented anywhere in the guide docs. `rest-api.mjs` implements Bearer token authentication; `/api/health` is explicitly exempt. The `apiToken` config field is not mentioned in the brain configuration table. A team connecting to a shared brain server would have no documentation for securing the API. | `brain/lib/rest-api.mjs` lines 17–28; `docs/guide/technical-reference.md` Brain Configuration section | Add an "Authentication" subsection: the `apiToken` config field, the Bearer token flow, the `/api/health` exemption, and the consequence of a missing `apiToken` (unauthenticated access allowed). |
| 5 | **High** | Contributor | Missing Procedure | How to add a new enforcement hook is not documented. The three-layer enforcement pyramid is described behaviorally, but the mechanical contribution steps are absent: create a `source/claude/hooks/{agent}.sh` script, add the frontmatter `hooks:` field, update the Cursor overlay, and add a registration entry to the settings template. A contributor adding a new agent would produce a hook-less agent by default. | `docs/guide/technical-reference.md` Enforcement Hooks section | Add a "Adding a New Agent Hook" subsection with the 5-step mechanical procedure. Cross-reference the three-layer pyramid description. |
| 6 | **Medium** | Architecture | Incomplete Index | The ADR index at `docs/architecture/README.md` lists 13 of 30 ADRs. ADRs 0011, 0012, 0016, 0017, 0018, 0019, 0022, 0023, 0024, 0025, 0026, 0028, 0029, 0030, 0031, 0032, and 0033 are absent. The index exists as a table but was not updated as new ADRs were added. | `docs/architecture/README.md` | Add the 17 missing ADRs to the README table. Note that ADR-0001 lives at `docs/brain/ADR-0001-atelier-brain.md` rather than the architecture directory. |
| 7 | **Medium** | User-Facing | Missing Discovery | The Gauntlet is documented at `source/shared/references/gauntlet.md` with complete procedural detail but is not mentioned in the user guide's table of contents or any section. Users reading the guide would not know the Gauntlet exists. | `docs/guide/user-guide.md` (absent); `source/shared/references/gauntlet.md` (exists, complete) | Add a "The Gauntlet" section to the user guide similar in scope to the Darwin or Deps sections: overview, activation, when to use. Add a cross-reference from the technical reference. |
| 8 | **Medium** | Contributor | Missing Procedure | The technical reference describes the `/pipeline-setup` flow but does not document the developer workflow for modifying installed files. The constraint "edit `source/shared/`, then run `/pipeline-setup` to sync to `.claude/`; never edit `.claude/` directly" appears only in the ADR-0023 distillate, not in the guide docs. | `docs/guide/technical-reference.md` Setup and Install section | Add a "Contributing to Pipeline Files" subsection explaining the source-of-truth hierarchy and the sync workflow. |
| 9 | **Medium** | Operations | Missing Runbook | There is no "how to debug the brain server" runbook. The technical reference describes startup but does not cover: diagnosing connection failures, checking PostgreSQL extension availability, interpreting `atelier_stats` error responses, or the manual `npm install` step when the server fails to start. | `docs/guide/technical-reference.md` Brain Architecture section | Add a "Troubleshooting the Brain" subsection covering: verifying pgvector/ltree, running `npm install` manually, checking health via `atelier_stats`, reading `start.sh` logs. |
| 10 | **Medium** | Contributor | Missing Cross-Ref | The `brain/schema.sql` file is canonical for fresh installs, but the relationship between `schema.sql` and the migrations (migrations only apply to existing databases; `schema.sql` already includes all columns and enum values) is stated in a single sentence. A contributor who updates only `schema.sql` and not the migrations would break upgrade paths silently. | `docs/guide/technical-reference.md` Auto-Migration System section | Expand the migration pattern description with an explicit contributor checklist: (a) update `schema.sql` for fresh installs, (b) create a new idempotent migration file for existing databases, (c) add the migration to the technical reference table. |
| 11 | **Low** | User-Facing | Incomplete Cross-Ref | The technical reference's Cross-References section links to 2 ADRs by name (ADR-0009, ADR-0010). The remaining ADRs referenced inline throughout the document are not in the cross-references section. | `docs/guide/technical-reference.md` lines 2527–2528 | Add inline-referenced ADRs to the cross-references section for navigability. |
| 12 | **Low** | User-Facing | Missing Discovery | The `brain/ui/` Settings UI is served by the brain HTTP server but is not described in the technical reference or user guide beyond the `/dashboard` skill entry point. | `docs/guide/technical-reference.md` Dashboard section | Add one paragraph describing the Settings UI: what it surfaces and how to access it (same HTTP server as the dashboard). |

---

## Divergence Report (Code vs. Documentation)

| Divergence | Spec says (technical reference) | Code does |
|-----------|--------------------------------|-----------|
| Brain migrations 001–002 only | Lines 922–929: lists only `001-add-captured-by.sql`, `002-add-handoff-enums.sql` | `brain/migrations/` contains 7 files: 001–007. Migrations 003–006 add enum values for CI Watch, Darwin, telemetry hydration, and pipeline phases. |
| REST API: 4 telemetry endpoints only | Documents `/api/telemetry/scopes`, `/summary`, `/agents`, `/agent-detail` | `brain/lib/rest-api.mjs` exposes 9 routes: the 4 telemetry routes + `/api/health`, `/api/config` (GET+PUT), `/api/thought-types` (GET+PUT), `/api/purge-expired`, `/api/stats` |

---

## Positive Observations

1. **The technical reference is implementation-depth.** At ~2,500 lines, `docs/guide/technical-reference.md` covers orchestration logic, the three-layer enforcement pyramid, brain capture model, telemetry tiers, model selection classifier, stop reason taxonomy, and wave execution mechanics at a level of precision that matches the actual code. This is genuinely rare. (`docs/guide/technical-reference.md`)
2. **The brain capture model is documented end-to-end.** The path from SubagentStop hook → brain-extractor Haiku → `last_assistant_message` parsing → `agent_capture` Zod validation → PostgreSQL write is laid out with per-agent metadata mappings, quality signal extraction schemas, omission rules, and loop prevention logic. (`docs/guide/technical-reference.md` lines 855–903)
3. **pipeline-config.json feature flags are fully documented.** Every flag has a documented type, default value, setter, description, and upgrade-safety note. The `token_budget_warning_threshold` null-vs-number semantics and `ci_watch_max_retries` minimum are both present. (`docs/guide/technical-reference.md` lines 1142–1179)
4. **The enforcement hook system is documented as a system.** The three-layer pyramid, blocking vs. non-blocking exit codes, `jq` graceful degradation, and `if:` performance optimization are all documented with the exact registration format shown for both Claude Code and Cursor. (`docs/guide/technical-reference.md` lines 1214–1415)
5. **The Gauntlet reference file is comprehensive and immediately usable.** `source/shared/references/gauntlet.md` is a complete operational document: phased execution protocol, per-agent mandates with output schemas, deduplication rules, severity definitions, and adaptation guidelines. The quality of this reference makes its absence from the user guide all the more notable.
6. **The user guide leads with examples throughout.** Every major pipeline phase is illustrated with verbatim conversation examples. The debug flow, UAT mockup review, and CI Watch fix cycle are shown as dialogue rather than abstract procedure.
7. **The brain's three-axis scoring function is documented with the formula.** The `match_thoughts_scored` function's `0.5 * recency_decay + 2.0 * importance + 3.0 * cosine_similarity` formula, the decay constant, and the weighting rationale are all present. (`docs/guide/technical-reference.md` lines 808–819)
8. **Platform differences are surfaced at the top of both documents.** Both the user guide and technical reference open with a platform comparison table before any feature content. Cursor-specific limitations are stated once at entry point rather than scattered as footnotes.

---

**Signed:** Agatha
**Review mode:** READ-ONLY. Zero files modified.
