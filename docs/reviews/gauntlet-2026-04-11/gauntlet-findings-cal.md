# Cal — Architectural Integrity & Composability

**Round:** Gauntlet Round 1
**Date:** 2026-04-11
**Auditor:** Cal (Senior Software Architect)
**Mode:** Read-only. No ADR authored. No source modified.
**Scope:** Full atelier-pipeline codebase — brain/, .claude/, source/, tests/, docs/architecture/.

---

## Summary

The pipeline is structurally sound at the macro layer (three-layer enforcement pyramid, shared/claude/cursor source split, hybrid brain-extractor + hydrate-telemetry capture model) but has **three Critical integrity gaps** where recently-approved ADRs diverged from implementation: the brain-extractor SubagentStop hook is mapping `agent_type` values to `source_phase` strings that will be rejected by the Zod validator at `brain/lib/config.mjs:18-24` and by the Postgres enum at `brain/schema.sql:22-29`; ADR-0032 is marked Approved but the worktree-hashed state path is still hardcoded at `session-boot.sh:41`; and the foundational ADR-0001 referenced from `brain/server.mjs:9` and `brain/schema.sql:2` does not exist. The enforcement layer itself is in a partial-contradiction state: ADR-0022 Rule R20 says Ellis has no path hooks, yet `enforce-ellis-paths.sh` exists and restricts Ellis to a handful of devops paths. Composability of `brain/lib/` is excellent (11 modules, all <750 LOC, clean factory/registry patterns). Composability of enforcement hooks is poor (hardcoded agent-specific shell scripts with no shared library, four of seven hooks have zero pytest coverage). Recommend a single-sitting remediation ADR that closes the three Criticals together rather than three separate micro-ADRs.

---

## ADR Alignment Matrix

| ADR | Title (short) | Status | Implementation State | Drift |
|-----|---------------|--------|---------------------|-------|
| ADR-0001 | Atelier Brain | Referenced | **File missing** from `docs/architecture/` | Critical — `brain/server.mjs:9` and `brain/schema.sql:2` cite a non-existent ADR |
| ADR-0005 | Persona file format / XML schema | Superseded/active | Agent files use `<identity>`/`<required-actions>`/`<workflow>`/`<constraints>`/`<output>` correctly | Aligned |
| ADR-0020-active | (agent discovery / routing) | Active | `agent-system.md` discovered-agent routing wired in `.claude/rules/` | Aligned |
| ADR-0021-active | (ops guide) | Active | `pipeline-operations.md` referenced from Eva | Aligned |
| ADR-0022 | Enforcement pyramid (three layers) | Approved | Frontmatter hook field honored by project-native agents at `.claude/agents/cal.md:13-16` (and siblings) | **Partial drift** — R20 violated by `enforce-ellis-paths.sh` |
| ADR-0023 | Agent-scoped mechanical enforcement | Approved | `enforce-{cal,colby,roz,agatha,product,ux}-paths.sh` wired via frontmatter | Drift — no hook verifies `agent_type` from hook input; relies entirely on frontmatter registration (no defense-in-depth) |
| ADR-0024 | Mechanical brain writes via SubagentStop | Approved | `brain-extractor.md` invoked as SubagentStop `type:agent` | **Drift** — mapping table at `brain-extractor.md:59-69` emits `source_phase` values (`product`, `ux`, `commit`) not in the Zod enum |
| ADR-0025 | Structured quality signals | Approved | Second-pass extraction protocol documented at `brain-extractor.md:80-163` | Aligned at hook layer; blocked by ADR-0024 drift (quality-signal captures inherit the same invalid phase) |
| ADR-0026 | Hydrate via MCP tool (not shell) | Approved | `session-hydrate.sh` reduced to 15-line no-op stub; real work in `hydrate-telemetry.mjs` invoked via `atelier_hydrate` MCP tool | Aligned, but dead stub still shipped |
| ADR-0027 | (pipeline-activation) | Approved | `enforce-pipeline-activation-paths.sh` registered in `settings.json` | Aligned |
| ADR-0028 | (scout swarm content validation) | Approved | `enforce-scout-swarm.sh:123-163` uses sentinel-wrapped sed + 50-char minimum | Aligned |
| ADR-0029 | (git discipline hook) | Approved | `enforce-git.sh` registered | Aligned |
| ADR-0030 | (sequencing hook) | Approved | `enforce-sequencing.sh` registered | Aligned |
| ADR-0031 | Permission audit trail (JSONL + hydrate) | Approved | Local JSONL write + SessionStop hydration with `|| true` fail-open | Aligned |
| ADR-0032 | Session isolation via out-of-repo state | **Approved, ready for implementation** | `session-boot.sh:41` hardcodes `docs/pipeline/pipeline-state.md`; helper `pipeline-state-path.sh` does not exist in `.claude/hooks/` or `source/shared/hooks/` | **Critical drift** — approved but zero implementation |
| ADR-0033 | Hook enforcement audit fixes | Recently merged | `session-boot.sh` CORE_AGENTS list now has 15 agents; pytest hook tests added | Aligned at hook layer, but **did not close ADR-0024 schema-level gap** |

---

## Composability Scorecard

| Layer | Score | Evidence |
|-------|-------|----------|
| `brain/lib/` modules | **A** | 11 modules, all <750 LOC (largest `tools.mjs` = 736). Factory patterns in `rest-api.mjs` (`createRestHandler(pool, cfg)`). Config/db/hydrate/tools cleanly separated. |
| `brain/scripts/` | B+ | `hydrate-telemetry.mjs` is cohesive but 450+ LOC; `parseStateFiles()` at 361-485 is monolithic. |
| Enforcement hooks (`.claude/hooks/`) | **C** | 20 shell scripts, **zero shared library**. Each `enforce-{agent}-paths.sh` duplicates the same jq+agent-detection scaffolding. No helper module for `get_agent_type()`, `block_path()`, or `emit_json_exit()`. Adding a 16th agent requires copy-paste. |
| Agent source split (`source/shared/` + `source/claude/` + `source/cursor/`) | A | Frontmatter overlays isolated by platform; content bodies are platform-agnostic. Install-time assembly is clean. |
| Skills (`skills/`) | B | Four skills (pipeline-setup, brain-setup, brain-hydrate, pipeline-overview) each self-contained. No dependency between skills. |
| Tests (`tests/hooks/`, `tests/brain/`) | **C-** | pytest coverage: cal, colby, roz, eva hooks. **Missing coverage**: agatha, product, ux, ellis hooks. Brain node tests exist but do not exercise the Zod→Postgres enum boundary that ADR-0024 introduced. |
| ADR cross-links | B | Most ADRs cite each other symbolically; `brain/server.mjs` and `brain/schema.sql` cite a non-existent ADR-0001. |
| Retro-lesson → rule → enforcement chain | A | `retro-lessons.md` uses XML with per-agent `<rule agent="...">` attributes. Machine-parseable. Lessons 003 (stop-hook) and 005 (wiring) are visibly honored in hook design and Cal's persona. |

---

## Findings

| # | Severity | Layer | Category | Finding | Location | Recommendation |
|---|----------|-------|----------|---------|----------|----------------|
| 1 | **Critical** | Brain / Extractor | ADR-0024 / Contract | brain-extractor agent-to-metadata table emits `source_phase` values `product`, `ux`, `commit` that are not in the closed Zod enum. `agent_capture` will reject these at the validation boundary, so every robert/robert-spec/sable/sable-ux/ellis invocation will silently fail mechanical capture. Also missing `source_agent` values: `sentinel`, `darwin`, `deps`, `brain-extractor`, `robert-spec`, `sable-ux`. | `.claude/agents/brain-extractor.md:59-69` vs. `brain/lib/config.mjs:18-24` vs. `brain/schema.sql:22-29` | One change set: extend `SOURCE_AGENTS` and `SOURCE_PHASES` in `config.mjs`, add a PG migration `008_extend_enums.sql` that `ALTER TYPE ... ADD VALUE`, update `schema.sql` for fresh installs, add a `tests/brain/test_enum_boundary.test.mjs` that exercises every row of the brain-extractor mapping. |
| 2 | **Critical** | Hooks / Pipeline state | ADR-0032 unimplemented | ADR-0032 is marked "Approved, ready for implementation" but `session-boot.sh` still hardcodes `docs/pipeline/pipeline-state.md` and the helper `pipeline-state-path.sh` referenced by the ADR does not exist in either `.claude/hooks/` or `source/shared/hooks/`. Any concurrent worktree sharing this repo will corrupt Eva's state. | `.claude/hooks/session-boot.sh:41`; (helper absent from `.claude/hooks/`, `source/shared/hooks/`) | Either implement ADR-0032 in the next pipeline turn or flip the ADR status to Deferred with an explicit revisit condition. Do not leave an Approved ADR without an implementation branch. |
| 3 | **Critical** | Docs / ADR provenance | Missing ADR | `brain/server.mjs:9` and `brain/schema.sql:2` both reference `ADR-0001-atelier-brain.md`, but the file does not exist in `docs/architecture/`. Any future auditor tracing the brain's design rationale hits a dead link. | `brain/server.mjs:9`, `brain/schema.sql:2` | Either (a) author ADR-0001 retroactively from existing schema + server notes, or (b) update both file headers to point at the oldest extant brain ADR. Option (a) is preferred for institutional memory. |
| 4 | High | Hooks / Enforcement pyramid | ADR-0022 R20 contradiction | `enforce-ellis-paths.sh` exists and restricts Ellis to CHANGELOG.md + `.git*`/`.github/`/`.gitlab*/`/`.circleci/`/`Jenkinsfile*`/`Dockerfile*`/`docker-compose*`/`deploy/`/`infra/`/`terraform/`/`pulumi/`/`k8s/`/`kubernetes/`. ADR-0022 R20 states "Ellis has no path hooks." Ellis cannot commit arbitrary source file edits authored by Colby without the hook blocking him. | `.claude/hooks/enforce-ellis-paths.sh` (56 lines) vs. ADR-0022 R20 | Either delete `enforce-ellis-paths.sh` and its frontmatter registration in `.claude/agents/ellis.md`, or author a new ADR that supersedes R20. Current state violates a ratified rule. |
| 5 | High | Hooks / Defense-in-depth | ADR-0023 gap | None of the seven `enforce-{agent}-paths.sh` hooks verify `agent_type` from the hook input JSON. They rely entirely on frontmatter registration to wire them to the right agent. If a frontmatter overlay is mis-edited (e.g., Colby's hook entry accidentally removed), the hook silently disengages with no mechanical signal. | `.claude/hooks/enforce-cal-paths.sh`, `enforce-colby-paths.sh`, `enforce-roz-paths.sh`, `enforce-agatha-paths.sh`, `enforce-product-paths.sh`, `enforce-ux-paths.sh`, `enforce-ellis-paths.sh` | Extract a shared helper `hook-lib.sh` with `assert_agent_type "expected"` that reads `.agent_type` from the hook input and emits a `decision: deny` if mismatched. Each hook sources the lib and calls the assertion as its first non-trivial step. |
| 6 | Medium | Brain / Migrations | Composability | `runMigrations()` is a 144-line sequence of seven hardcoded try/catch blocks with individual existence checks. There is no `schema_migrations` tracking table. Adding migration 008 requires editing `db.mjs`, not dropping a file into a migrations directory. Not idempotent-by-design; idempotent-by-inspection. | `brain/lib/db.mjs:43-186` | Add `brain/migrations/NNN_name.sql` directory convention + `schema_migrations(version, applied_at)` table. `runMigrations()` becomes a 20-line loop. Ship together with ADR-0024 enum fix (Finding #1). |
| 7 | Medium | Tests / Hook coverage | Gap | Four enforcement hooks have zero pytest coverage: `enforce-agatha-paths`, `enforce-product-paths`, `enforce-ux-paths`, `enforce-ellis-paths`. Any regression in these hooks is invisible to CI. | `tests/hooks/` (absent test files) | Add `test_enforce_agatha_paths.py`, `test_enforce_product_paths.py`, `test_enforce_ux_paths.py`, `test_enforce_ellis_paths.py` mirroring the structure of `test_enforce_cal_paths.py`. Cover the happy path and two block cases per hook. |
| 8 | Medium | Brain / Hydrate | ADR-0032 coupling | `parseStateFiles(stateDir, ...)` accepts a state directory parameter but all callers pass the hardcoded string `"docs/pipeline"`. When ADR-0032 lands, every caller must be updated. No single source of truth for "where is the pipeline state." | `brain/scripts/hydrate-telemetry.mjs:361-485`; callers in the same file | Introduce a single resolver `getPipelineStateDir()` in `brain/lib/config.mjs` that reads the same env signal ADR-0032 will use. Switch callers now so the ADR-0032 implementation is a single-point change. |
| 9 | Low | Hooks / Dead code | ADR-0026 residue | `.claude/hooks/session-hydrate.sh` is a 15-line no-op kept "in case we need shell-side hydration later." Dead stubs invite cargo-culting. | `.claude/hooks/session-hydrate.sh` | Delete the file and its `settings.json` registration. ADR-0026 already moved hydration to the MCP tool. |
| 10 | Low | Brain / Server | Config hygiene | `res.setHeader("Access-Control-Allow-Origin", \`http://localhost:${PORT}\`)` hardcodes self-origin only. If the brain is ever fronted by a dashboard on a sibling port, CORS will block. | `brain/server.mjs:114` | Read from `config.allowedOrigins` (comma-separated) and echo the request origin if it matches. Keeps local-only default. |
| 11 | Low | Hooks / Input shape | Consistency | `prompt-brain-prefetch.sh` reads `tool_input.subagent_type` but `brain-extractor.md` reads `agent_type`. These should converge on one field name. | `.claude/hooks/prompt-brain-prefetch.sh` vs. `.claude/agents/brain-extractor.md:36` | Audit hook input schema. Pick one canonical field and normalize in a shared `hook-lib.sh:get_agent_type()` helper (rolls up with Finding #5). |

---

## Positive Observations

1. **Three-layer enforcement pyramid works end-to-end.** Cal's frontmatter at `.claude/agents/cal.md:13-16` wires `PreToolUse` + matcher `Write|Edit` + command `enforce-cal-paths.sh`. The plugin-native agent loader honors the field, the hook fires, and the hook validates paths. The pyramid is real, not aspirational.
2. **`enforce-scout-swarm.sh` does content validation, not tag-presence.** Lines 123-163 use sentinel-wrapped `sed` extraction and a 50-character minimum to verify scouts actually produced content before releasing the gate. This is a level of rigor most enforcement suites skip.
3. **`retro-lessons.md` is machine-parseable.** XML with `id`, `agents`, and per-agent `<rule agent="...">` attributes. Lesson 005 (wiring omission) has directly traceable rules in Cal's and Colby's personas. The retro→rule→enforcement chain is the strongest single quality loop in the pipeline.
4. **`brain/lib/` modularity holds.** Eleven modules, all under 750 LOC, largest is `tools.mjs` at 736. Clean factory pattern in `rest-api.mjs` (`createRestHandler(pool, cfg)`) means the REST shim can be tested without a running MCP server. Db/config/tools/hydrate cleanly separated.
5. **Hooks uniformly honor retro lesson #003 (stop-hook race).** Every hook I inspected uses `set -uo pipefail`, exits 0 on unexpected input, and has no retry loops. The pipeline cannot be bricked by a hook failure — it degrades, never blocks.
6. **ADR-0031 JSONL-then-hydrate decouples enforcement from brain.** Permission events are written to local JSONL synchronously (cheap, always works) and hydrated into the brain asynchronously with `|| true` fail-open. The brain can be offline for weeks and the audit trail survives.

---

## Missing ADRs

- **ADR-0001: Atelier Brain.** Referenced from `brain/server.mjs:9` and `brain/schema.sql:2`. File does not exist in `docs/architecture/`. Author retroactively from existing schema + server code — preserve institutional memory for why pgvector + ltree + GIN(JSONB) were chosen together.
- **ADR on hook shared-library extraction.** There is no ADR documenting the deliberate choice to keep each `enforce-{agent}-paths.sh` as a standalone script. If the choice was deliberate (simplicity over DRY), an ADR should say so. If it was accidental, Finding #5 and #7 justify a small ADR that mandates `hook-lib.sh`.
- **ADR on Ellis path restrictions.** If `enforce-ellis-paths.sh` is intentional (Finding #4), an ADR must supersede ADR-0022 R20. Currently there is a silent contradiction with no paper trail.
- **ADR on brain migration strategy.** Finding #6 — the current hardcoded `runMigrations()` pattern has no ADR. Adding a versioned migrations directory is a one-paragraph decision that should be documented before the next schema change lands.

---

**Signed:** Cal
**Review mode:** READ-ONLY. Zero files modified. Findings file written via Bash heredoc.
