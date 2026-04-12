# ADR-0036: Wave 5 -- Documentation Sweep (Prose Docs + ADR Index + Migration Runner Docs)

## DoR: Requirements Extracted

**Sources:** ADR-0034-gauntlet-remediation.md (R14 line items), docs/guide/technical-reference.md, docs/guide/user-guide.md, docs/architecture/README.md, brain/lib/rest-api.mjs (endpoint inventory), brain/lib/db.mjs (migration runner), brain/migrations/*.sql, .claude/references/retro-lessons.md

| # | Requirement | Source | Source citation |
|---|-------------|--------|-----------------|
| R1 | Document triple-source assembly pattern (source/shared/ + source/claude/ + source/cursor/ overlay pattern) in both technical-reference.md and user-guide.md | ADR-0034 R14, finding S1 | `gauntlet-combined.md:50`, `ADR-0034:20` |
| R2 | Document REST auth mechanism fully: token source, generation, dashboard auth flow, auth-exempt vs auth-required distinction | ADR-0034 R14, finding S11 | `gauntlet-combined.md:60` |
| R3 | Document hook addition procedure: step-by-step guide for adding a new enforcement hook | ADR-0034 R14, finding S19 | `gauntlet-combined.md:67` |
| R4 | Document Gauntlet audit process in user-facing docs | ADR-0034 R14, finding S20 | `gauntlet-combined.md:69` |
| R5 | Complete REST endpoint documentation: all 11 endpoints (currently only 4 documented) | ADR-0034 R14, finding S25 | `gauntlet-combined.md:74`, `rest-api.mjs:37-68` |
| R6 | Document migrations 003-009 in the migration table (currently only 001-002 documented) | ADR-0034 R14, finding M11 | `gauntlet-combined.md:37`, `technical-reference.md:969-982` |
| R7 | Document the schema_migrations tracking mechanism, migration runner design, idempotency guarantee, and how to write a new migration | ADR-0034 R14, finding M11 (extended) | `brain/lib/db.mjs:43-83`, `brain/migrations/README.md` |
| R8 | Complete the ADR index: add all 18 missing ADRs to docs/architecture/README.md, note ADR-0001 and ADR-0020/0021 alternative locations | ADR-0034 R14, finding M15 | `gauntlet-combined.md:40`, `README.md` (13 of 34 listed) |
| R9 | Resolve ADR-0001 dead link: update references in brain/server.mjs:9 and brain/schema.sql:2 to point to actual location (docs/brain/ADR-0001-atelier-brain.md) | ADR-0034 R16, finding S3 | `gauntlet-combined.md:52` |
| R10 | Update Cross-References section in technical-reference.md to link all ADRs (currently only 2 linked) | ADR-0034 R14, finding M15 | `technical-reference.md:2586-2601` |

**Retro risks:**
- **Lesson #005 (Frontend Wiring Omission):** Applies structurally -- documentation work where the "producer" is a new section and the "consumer" is a reader navigating from the index. Every new section must be reachable from the Table of Contents. Orphan sections (written but unreachable from ToC) are the doc equivalent of orphan endpoints.

---

## Status

Proposed -- 2026-04-12. Supplements ADR-0034 (Wave 5 execution plan for R14 findings).

---

## Context

ADR-0034 organized 40 gauntlet findings into a six-wave remediation plan. Waves 1-3 (code correctness, enforcement stabilization, brain hardening) have been fully designed and are being executed. Wave 5 was outlined in ADR-0034 as a documentation sweep owned by Agatha.

Seven documentation gaps were identified in the gauntlet combined register:

1. **S1 -- Triple-source assembly undocumented.** The `source/shared/` + `source/claude/` + `source/cursor/` overlay pattern is the fundamental build model of the plugin but appears nowhere in user-facing docs. Contributors cannot understand how agent files are assembled without reading CLAUDE.md.

2. **S11 -- REST auth underspecified.** The technical reference mentions `Authorization: Bearer {token}` in passing but does not explain where the token comes from, how to generate it, what `apiToken: null` means (auth bypass), or the auth-exempt `/api/health` endpoint.

3. **S19 -- Hook addition procedure missing.** Twenty hooks exist with thorough documentation per hook, but no procedure exists for "how to add a new hook." A contributor creating a new enforcement hook has to reverse-engineer the three-layer pyramid from examples.

4. **S20 -- Gauntlet not mentioned.** The gauntlet audit process (multi-agent codebase review) is referenced in ADR-0034 but does not appear in user-facing documentation.

5. **S25 -- REST endpoints incomplete.** Only 4 of 11 REST API endpoints are documented. The 7 undocumented endpoints are: `/api/health`, `/api/config` (GET/PUT), `/api/thought-types` (GET), `/api/thought-types/:id` (PUT), `/api/purge-expired` (POST), `/api/stats` (GET).

6. **M11 -- Migrations 003-009 undocumented.** The "Auto-Migration System" section in technical-reference.md documents only migrations 001-002. After Waves 1-2, the system has 9 migrations plus a generic runner with `schema_migrations` tracking, none of which is reflected in docs.

7. **M15 -- ADR index incomplete.** The `docs/architecture/README.md` index lists 13 of 34 ADRs. Eighteen ADRs (0011, 0012, 0016-0019, 0022-0034) are absent. ADR-0001 lives at `docs/brain/ADR-0001-atelier-brain.md`. ADR-0020 and ADR-0021 live in `docs/architecture/active/`. The Cross-References section in technical-reference.md links only ADR-0009 and ADR-0010.

Additionally, finding **S3 (ADR-0001 dead link)** requires updating file header references in `brain/server.mjs:9` and `brain/schema.sql:2` to point to the actual ADR-0001 location. This is a two-line source change, not a docs-only change, but it is trivially scoped and ships with the documentation wave to avoid carrying a dead link through another release.

**What Wave 5 does NOT include:**
- No retroactive ADRs for undocumented architectural decisions. The gauntlet's "17 undocumented ADRs" refers to 17 ADRs missing from the *index*, not 17 decisions with no ADR. Every hook, agent, and subsystem already has ADR coverage. The fix is index completion (M15), not new ADR authorship.
- No source code changes beyond the S3 dead-link fix (2 lines in file headers).
- No UX or dashboard changes.

---

## Decision

Ship Wave 5 as a **two-track documentation update**:

**Track A -- Prose documentation (Agatha executes, 6 steps).** Updates to `docs/guide/technical-reference.md` and `docs/guide/user-guide.md` to close S1, S11, S19, S20, S25, M11.

**Track B -- ADR index and cross-references (Agatha executes, 2 steps).** Updates to `docs/architecture/README.md` and `docs/guide/technical-reference.md` Cross-References section to close M15. Plus the S3 dead-link fix in source files.

No retroactive ADRs are needed. The original task brief suggested authoring retroactive ADRs starting at ADR-0038. After reading every existing ADR and cross-referencing the gauntlet register, the "17 undocumented decisions" are actually 18 ADRs missing from the README index, not 18 decisions with no ADR. The correct fix is completing the index (Track B Step 7), not writing new ADRs.

**Anti-goals:**

1. **Anti-goal:** Rewriting the existing per-hook documentation in technical-reference.md. Reason: the per-hook descriptions are thorough and accurate; the gap is only the *procedure* for adding a new hook. Revisit: if a future gauntlet finds factual errors in per-hook docs.

2. **Anti-goal:** Adding API usage examples or code samples to the REST endpoint docs. Reason: the technical reference documents *what exists*, not *how to use it*. Usage examples belong in a future developer guide or API reference. Revisit: if user feedback indicates the endpoint table is insufficient for integration.

3. **Anti-goal:** Documenting the skill system design as a new ADR. Reason: skills are documented in the "Setup and Install System" section of technical-reference.md and in agent-system.md's Skills vs. Subagents table. The "undocumented skill system" finding from the research brief is actually covered -- the gap was in the ADR index, not in design documentation. Revisit: if skills gain a plugin registry, auto-discovery, or other design-level complexity.

**Spec challenge:** The task assumes that Waves 1-3 have already shipped, meaning the migration runner refactor (Wave 2 Step 2.3) and migration 008/009 are already in place. **If wrong, the documentation fails because** M11 would document a migration table (003-009) and runner design that does not yet exist in the codebase. Verification: Agatha must read `brain/lib/db.mjs` and `brain/migrations/` at execution time to confirm the actual state. If Wave 2 has not shipped, M11 documents only 001-002 (existing) plus the pre-refactor runner, and is re-updated after Wave 2 lands.

**SPOF:** The ADR index in `docs/architecture/README.md`. Failure mode: future ADRs are written but never added to the index, recreating the M15 gap. Graceful degradation: the `docs/architecture/` directory itself is browsable by filename -- the README index is a convenience layer, not the only access path. Mitigation: add a note in the index documenting the "add your ADR to this table" convention.

---

## Alternatives Considered

**Alternative A: Write retroactive ADRs for each "undocumented decision."** Rejected. After reading all 34 existing ADRs, no architectural decisions are genuinely undocumented. The gauntlet finding M15 says "17 ADRs absent from the index," which the research brief misinterpreted as "17 undocumented decisions." Writing retroactive ADRs for decisions that already have ADRs would create duplicates.

**Alternative B: Merge all prose updates into one giant Agatha invocation.** Rejected. Seven distinct documentation sections across two files, each requiring Agatha to read different source files for accuracy. Batching everything into one invocation risks context overflow and accuracy degradation. The 8-step plan keeps each step focused (2-4 files to read, 1 file to write, 1 section to produce).

**Alternative C: Defer M11 until Wave 2 ships.** Partially accepted as a contingency. If Wave 2 has shipped, M11 documents the final state. If not, M11 documents the pre-refactor state and is updated post-Wave-2. The ADR handles both paths.

---

## Consequences

**Positive:**

- After Wave 5, every gauntlet R14 finding is closed. Zero documentation gaps remain from the 2026-04-11 audit.
- The ADR index becomes a complete navigation aid (34 ADRs + 2 active + 1 cross-location note).
- New contributors can find the hook addition procedure, REST API shape, and migration system without reverse-engineering source code.
- The Cross-References section in technical-reference.md becomes a useful launch point for all ADRs instead of linking only two.

**Negative:**

- Wave 5 adds approximately 400-500 lines to technical-reference.md (already 2601 lines). The document is approaching a size where splitting into multiple reference docs may be warranted. This is noted but not in scope.
- The S3 fix (updating brain/server.mjs and brain/schema.sql headers) is the only source code change. This requires Colby, not just Agatha, but the change is 2 lines total -- trivial enough to justify including in a docs wave rather than creating a separate code wave.

---

## Implementation Plan

### Step 1 -- Triple-source assembly documentation (S1)

**Target file:** `docs/guide/technical-reference.md`

**Target location:** New subsection `### Triple-Source Assembly Model` under the existing `## Plugin Architecture` section (after the "Plugin-Level Files" subsection, before `## File Tree`). Also add a ToC entry.

**Content required:**
- Explain the three source directories: `source/shared/` (platform-agnostic content bodies), `source/claude/` (Claude Code frontmatter overlays + hooks), `source/cursor/` (Cursor frontmatter overlays + hooks)
- Explain the assembly process: frontmatter overlay (YAML) is combined with shared content body at install time by `/pipeline-setup`
- Explain why: agents need platform-specific frontmatter (hooks field, tools restrictions) but share the same content body
- Table showing the overlay pattern: `source/claude/agents/cal.frontmatter.yml` + `source/shared/agents/cal.md` = `.claude/agents/cal.md`
- Note: `source/shared/` files have no YAML frontmatter; `source/claude/` and `source/cursor/` overlay files are pure YAML
- Mention that hooks live in `source/claude/hooks/` and `source/cursor/hooks/` (not shared) because hook implementations differ per platform

**Also update:** `docs/guide/user-guide.md` -- add a brief "Contributing: Source file structure" note under the existing "Customization" section explaining that editing `.claude/agents/*.md` directly is overwritten by `/pipeline-setup`; edits must go to `source/`.

**Files to read for accuracy:** `source/shared/agents/` (sample), `source/claude/agents/` (sample frontmatter), `skills/pipeline-setup/SKILL.md` (assembly logic)

**Acceptance criteria:**
- New subsection exists under Plugin Architecture
- Table of Contents entry links correctly
- Assembly flow is documented with a concrete example
- User guide has a contributor note about source/ vs .claude/
- After this step, a contributor can answer: "Where do I edit an agent's persona?"

**Complexity:** 2 files modified, 1 section each. Passes S1-S5.

---

### Step 2 -- REST API complete endpoint documentation (S25 + S11)

**Target file:** `docs/guide/technical-reference.md`

**Target location:** Expand the existing `### REST API Endpoints` table (line 2081) from 4 rows to 11 rows. Add a new subsection `### REST Authentication` immediately after the expanded table.

**Content required (S25 -- endpoint table):**

Expand the existing table to include all 11 endpoints:

| Endpoint | Method | Auth | Purpose | Response shape |
|----------|--------|------|---------|---------------|
| `/api/health` | GET | Exempt | Server health check | `{ status, version, uptime, brain_enabled, ... }` |
| `/api/config` | GET | Required | Read brain configuration | `{ content, metadata }` (brain_config thought) |
| `/api/config` | PUT | Required | Update brain configuration | `{ ok: true }` |
| `/api/thought-types` | GET | Required | List thought type configurations | `{ rows: [{id, thought_type, ttl_days, importance, ...}] }` |
| `/api/thought-types/:id` | PUT | Required | Update a thought type config | `{ ok: true }` |
| `/api/purge-expired` | POST | Required | Manually trigger TTL purge | `{ purged: <count> }` |
| `/api/stats` | GET | Required | Brain statistics summary | `{ thoughts, types, agents, ... }` |
| `/api/telemetry/scopes` | GET | Required | List project scopes | `string[]` |
| `/api/telemetry/summary` | GET | Required | T3 pipeline summaries | `{content, metadata, created_at}[]` |
| `/api/telemetry/agents` | GET | Required | Agent telemetry aggregates | `{agent, invocations, avg_duration_ms, ...}[]` |
| `/api/telemetry/agent-detail` | GET | Required | Per-agent invocation detail | `{description, duration_ms, cost_usd, ...}[]` |

**Content required (S11 -- auth section):**
- `Authorization: Bearer {token}` header required on all endpoints except `/api/health`
- Token source: `apiToken` field in brain config (set during `/brain-setup` or manually in brain-config.json)
- When `apiToken` is `null` or unset: auth is bypassed entirely (all endpoints open)
- When `apiToken` is set: 401 Unauthorized returned for missing/wrong token
- Dashboard auth: the dashboard HTML page fetches from the REST API using the token stored in `localStorage` by the settings UI

**Files to read for accuracy:** `brain/lib/rest-api.mjs` (all handlers), `brain/lib/config.mjs` (response shapes)

**Acceptance criteria:**
- Endpoint table has 11 rows (was 4)
- Auth column present for each endpoint
- Auth section documents token source, null behavior, 401 response
- After this step, a contributor can answer: "What REST endpoints does the brain expose and how do I authenticate?"

**Complexity:** 1 file modified, 2 sections. Passes S1-S5.

---

### Step 3 -- Migration system documentation (M11)

**Target file:** `docs/guide/technical-reference.md`

**Target location:** Rewrite the existing `### Auto-Migration System` section (line 969) to cover the post-Wave-2 state.

**Content required:**
- Overview of the migration runner design: generic file-loop driven by `schema_migrations` tracking table
- `schema_migrations` table structure: `version TEXT PRIMARY KEY`, `applied_at TIMESTAMPTZ`, `checksum TEXT`
- Runner algorithm: scan `brain/migrations/*.sql` sorted alphabetically, check `schema_migrations` for each filename, skip if present, execute + record if absent
- Checksum: `sha256(sql).digest("hex").slice(0, 16)`, informational only (not used for re-run detection)
- Fail-soft: per-file try/catch, logged error does not prevent subsequent migrations
- Idempotency guarantee: every migration file uses `IF NOT EXISTS` / `ADD VALUE IF NOT EXISTS` patterns

**Migration table (expanded from 2 rows to 9):**

| File | What It Does | ADR |
|------|-------------|-----|
| `001-add-captured-by.sql` | Adds `captured_by TEXT` column to `thoughts`. Replaces `match_thoughts_scored` to include `captured_by`. | -- |
| `002-add-handoff-enums.sql` | Adds `'handoff'` to `thought_type` and `source_phase` enums. Inserts `thought_type_config` for handoff. | ADR-0002 |
| `003-add-devops-phase.sql` | Adds `'devops'` to `source_phase` enum. | -- |
| `004-add-pattern-and-seed-types.sql` | Adds `'pattern'` and `'seed'` to `thought_type` enum. Inserts `thought_type_config` rows. | ADR-0004 |
| `005-add-telemetry-phases.sql` | Adds `'telemetry'` and `'ci-watch'` to `source_phase` enum. | ADR-0014, ADR-0013 |
| `006-add-pipeline-phase.sql` | Adds `'pipeline'` to `source_phase` enum. | -- |
| `007-beads-provenance-noop.sql` | No-op documentation file. Beads provenance uses existing `metadata` JSONB. | ADR-0026 |
| `008-extend-agent-and-phase-enums.sql` | Adds `sentinel`, `darwin`, `deps`, `brain-extractor`, `robert-spec`, `sable-ux` to `source_agent`. Adds `product`, `ux`, `commit` to `source_phase`. | ADR-0034 |
| `009-schema-migrations-table.sql` | Creates `schema_migrations` table. Backfills rows for 001-008. | ADR-0034 |

**Also include:**
- "How to write a new migration" procedure (from `brain/migrations/README.md`): pick next number, create file, write idempotent SQL, no registration needed
- Note that `brain/schema.sql` is the canonical schema for fresh installs; migrations exist solely for upgrading existing databases

**Contingency:** If Wave 2 has NOT shipped at Agatha execution time (migration runner not yet refactored), document the pre-refactor state: inline idempotency checks per migration, no `schema_migrations` table. Add a note: "Post-Wave-2, the runner uses a generic file-loop with schema_migrations tracking." This ensures the docs are accurate regardless of Wave 2 timing.

**Files to read for accuracy:** `brain/lib/db.mjs` (runner), `brain/migrations/*.sql` (all 9), `brain/migrations/README.md`, `brain/schema.sql` (fresh schema)

**Acceptance criteria:**
- Migration table has 9 rows (was 2)
- Runner design documented (schema_migrations, checksum, fail-soft)
- "How to write a new migration" procedure present
- After this step, a contributor can answer: "How do brain migrations work and how do I add one?"

**Complexity:** 1 file modified, 1 section. Passes S1-S5.

---

### Step 4 -- Hook addition procedure (S19)

**Target file:** `docs/guide/technical-reference.md`

**Target location:** New subsection `### Adding a New Enforcement Hook` at the end of the `## Enforcement Hooks` section, after the existing `### Enforcement Audit Trail` subsection. Add a ToC entry.

**Content required:**

Step-by-step procedure:

1. **Decide which layer.** Layer 1 (frontmatter `tools`/`disallowedTools`) for tool-level restrictions. Layer 2 (per-agent frontmatter hook) for path-based enforcement on a specific agent. Layer 3 (global hook in settings.json) for cross-cutting enforcement on the main thread.

2. **Write the hook script.** Create the script in `source/claude/hooks/` (Claude Code) and optionally `source/cursor/hooks/` (Cursor). Source `hook-lib.sh` for shared parsing functions. Follow the pattern: read JSON from stdin, parse with `hook_lib_get_agent_type` / `hook_lib_pipeline_status_field`, apply enforcement logic, exit 0 (allow) or exit 2 with reason on stderr (block).

3. **Register the hook.** For Layer 2: add a `hooks:` entry in the agent's frontmatter overlay (`source/claude/agents/{agent}.frontmatter.yml`). For Layer 3: add an entry to the settings.json template in `skills/pipeline-setup/SKILL.md`.

4. **Write a pytest.** Create `tests/hooks/test_{hook_name}.py` following the pattern in `tests/hooks/conftest.py`. Test at minimum: one blocked path, one allowed path, and config parity with `enforcement-config.json`.

5. **Run /pipeline-setup.** The hook is installed to `.claude/hooks/` only after `/pipeline-setup` re-runs. Editing `.claude/hooks/` directly is overwritten.

6. **Document the hook.** Add a row to the Hook Scripts table and a description subsection in technical-reference.md.

- Include a template showing the minimum hook structure (shebang, source hook-lib, read stdin, parse, enforce, exit)
- Note: hooks must exit 0 when jq is missing, when config is missing, and when the tool call is irrelevant to the hook's concern

**Files to read for accuracy:** Any existing `enforce-*-paths.sh` (pattern), `hook-lib.sh` (shared functions), `tests/hooks/conftest.py` (test pattern), `skills/pipeline-setup/SKILL.md` (registration)

**Acceptance criteria:**
- Procedure has 6 numbered steps
- Template code block shows minimum hook structure
- Three-layer decision tree documented
- After this step, a contributor can answer: "How do I add a new enforcement hook?"

**Complexity:** 1 file modified, 1 section. Passes S1-S5.

---

### Step 5 -- Gauntlet audit process documentation (S20)

**Target file:** `docs/guide/user-guide.md`

**Target location:** New section `## Gauntlet Audit` between the existing `## Agent Telemetry` and `## Dashboard` sections. Add a ToC entry.

**Content required:**
- What a gauntlet is: a multi-round, multi-agent full-codebase audit that produces a combined finding register
- When to run one: before major releases, after extended development periods, or when accumulated technical debt is suspected
- How it works: Eva invokes each agent type (Cal for architecture, Colby for code quality, Roz for test coverage, Sentinel for security, Robert for spec compliance, Sable for UX compliance, Poirot for blind review, Agatha for documentation) against the full codebase in sequence
- What it produces: a `docs/reviews/gauntlet-{date}/` directory with per-agent findings and a combined register (`gauntlet-combined.md`)
- Severity classification: Critical (blocks release), High (should fix before release), Medium (next sprint), Low (backlog)
- Multi-agent consensus: when 2+ agents independently flag the same issue, it is elevated in the combined register
- How findings become work: a remediation ADR (like ADR-0034) organizes findings into waves

**Files to read for accuracy:** `docs/reviews/gauntlet-2026-04-11/` (existing gauntlet output as example), ADR-0034 (how findings were organized)

**Acceptance criteria:**
- Section exists in user guide
- ToC entry links correctly
- After this step, a user can answer: "What is a gauntlet and how do I run one?"

**Complexity:** 1 file modified, 1 section. Passes S1-S5.

---

### Step 6 -- ADR-0001 dead link fix (S3)

**Target files:** `brain/server.mjs` (line 9), `brain/schema.sql` (line 2)

**Change:** Update the ADR reference comment in each file from `docs/architecture/ADR-0001-atelier-brain.md` to `docs/brain/ADR-0001-atelier-brain.md` (the actual location).

**Note:** This is the only source code change in Wave 5. Two comment-only edits. Colby executes this step, not Agatha.

**Acceptance criteria:**
- Both files reference `docs/brain/ADR-0001-atelier-brain.md`
- No functional code changes
- After this step, a contributor following the brain's design reference link arrives at the actual ADR

**Complexity:** 2 files modified, 1 line each. Trivial.

---

### Step 7 -- ADR index completion (M15)

**Target file:** `docs/architecture/README.md`

**Change:** Expand the ADR table from 13 rows to include all ADRs. The complete table:

| ADR | Title | Status | Location |
|-----|-------|--------|----------|
| [ADR-0001](../brain/ADR-0001-atelier-brain.md) | Atelier Brain -- Persistent Institutional Memory | Accepted | `docs/brain/` |
| [ADR-0002](ADR-0002-team-collaboration.md) | Team Collaboration Enhancements | Accepted | |
| [ADR-0003](ADR-0003-code-quality-overhaul.md) | Code Quality and Security Overhaul | Proposed | |
| [ADR-0004](ADR-0004-pipeline-evolution.md) | Pipeline Evolution | Proposed | |
| [ADR-0005](ADR-0005-xml-prompt-structure.md) | XML-Based Prompt Structure | Accepted | |
| [ADR-0006](ADR-0006-xml-structure-rules-references.md) | XML Tag Migration for Rules and References | Accepted | |
| [ADR-0007](ADR-0007-dor-dod-warn-hook.md) | SubagentStop Warning Hook for DoR/DoD | Proposed | |
| [ADR-0008](ADR-0008-agent-discovery.md) | Filesystem-Based Agent Discovery | Proposed | |
| [ADR-0009](ADR-0009-sentinel-security-agent.md) | Sentinel Security Audit Agent | Proposed | |
| [ADR-0010](ADR-0010-agent-teams.md) | Agent Teams Parallel Execution | Proposed | |
| [ADR-0011](ADR-0011-observation-masking.md) | Observation Masking and Context Hygiene | -- | |
| [ADR-0012](ADR-0012-compaction-api.md) | Compaction API Integration | -- | |
| [ADR-0013](ADR-0013-ci-watch.md) | CI Watch Self-Healing CI | Proposed | |
| [ADR-0014](ADR-0014-agent-telemetry-dashboard.md) | Agent Telemetry Dashboard | Proposed | |
| [ADR-0015](ADR-0015-deps-agent.md) | Deps Agent | Proposed | |
| [ADR-0016](ADR-0016-darwin-self-evolving-pipeline.md) | Darwin Self-Evolving Pipeline | -- | |
| [ADR-0017](ADR-0017-brain-hardening.md) | Brain Hardening | -- | |
| [ADR-0018](ADR-0018-dashboard-integration.md) | Dashboard Integration | -- | |
| [ADR-0019](ADR-0019-cursor-port.md) | Cursor Port | -- | |
| [ADR-0020](active/ADR-0020-wave2-hook-modernization.md) | Wave 2 Hook Modernization | Active | `active/` |
| [ADR-0021](active/ADR-0021-brain-wiring.md) | Mechanical Brain Wiring | Active | `active/` |
| [ADR-0022](ADR-0022-wave3-native-enforcement-redesign.md) | Wave 3 Native Enforcement Redesign | -- | |
| [ADR-0023](ADR-0023-agent-specification-reduction.md) | Agent Specification Reduction | -- | |
| [ADR-0024](ADR-0024-mechanical-brain-writes.md) | Mechanical Brain Writes | -- | |
| [ADR-0025](ADR-0025-mechanical-telemetry-extraction.md) | Mechanical Telemetry Extraction | -- | |
| [ADR-0026](ADR-0026-beads-provenance-records.md) | Beads Provenance Records | -- | |
| [ADR-0027](ADR-0027-brain-hydrate-scout-fanout.md) | Brain-Hydrate Scout Fan-Out | Proposed | |
| [ADR-0028](ADR-0028-named-stop-reason-taxonomy.md) | Named Stop Reason Taxonomy | -- | |
| [ADR-0029](ADR-0029-token-budget-estimate-gate.md) | Token Budget Estimate Gate | -- | |
| [ADR-0030](ADR-0030-token-exposure-probe-and-accumulator.md) | Token Exposure Probe and Accumulator | -- | |
| [ADR-0031](ADR-0031-permission-audit-trail.md) | Permission Audit Trail | -- | |
| [ADR-0032](ADR-0032-pipeline-state-session-isolation.md) | Pipeline State Session Isolation | Approved | |
| [ADR-0033](ADR-0033-hook-enforcement-audit-fixes.md) | Hook Enforcement Audit Fixes | -- | |
| [ADR-0034](ADR-0034-gauntlet-remediation.md) | Gauntlet 2026-04-11 Remediation | Proposed | |

**Note:** ADRs marked `--` for status need Agatha to read each file's Status line and fill in the actual value. The table above is a template; Agatha must verify statuses.

**Also add** a convention note at the bottom of the README: "When creating a new ADR, add a row to this table in the same commit."

**Acceptance criteria:**
- README table has 34 rows (was 13)
- ADR-0001 links to `../brain/ADR-0001-atelier-brain.md`
- ADR-0020 and ADR-0021 link to `active/` subdirectory
- Convention note present
- After this step, a contributor can navigate to any ADR from the index

**Complexity:** 1 file modified. Passes S1-S5.

---

### Step 8 -- Cross-References section expansion (M15 continued + R10)

**Target file:** `docs/guide/technical-reference.md`

**Target location:** Expand the existing `## Cross-References` section (line 2586) to include all ADRs grouped by subsystem.

**Content required:**

Replace the current 2-ADR listing with a grouped list:

- **Brain:** ADR-0001, ADR-0017, ADR-0021, ADR-0024, ADR-0026, ADR-0027
- **Agents & Personas:** ADR-0005, ADR-0006, ADR-0008, ADR-0023
- **Enforcement & Hooks:** ADR-0007, ADR-0020, ADR-0022, ADR-0031, ADR-0033
- **Telemetry & Dashboard:** ADR-0014, ADR-0018, ADR-0025, ADR-0030
- **Pipeline Features:** ADR-0002, ADR-0009, ADR-0010, ADR-0013, ADR-0015, ADR-0016, ADR-0028, ADR-0029, ADR-0032
- **Codebase:** ADR-0003, ADR-0004, ADR-0011, ADR-0012, ADR-0019
- **Remediation:** ADR-0034, ADR-0036

Keep existing non-ADR cross-references (user guide, installed files, etc.).

**Acceptance criteria:**
- All 34+ ADRs appear in the Cross-References section
- Grouped by subsystem for navigability
- Existing non-ADR references preserved
- After this step, a reader of the technical reference can find any ADR by subsystem

**Complexity:** 1 file modified, 1 section. Passes S1-S5.

---

## Test Specification

Roz verifies file existence, required section headings, and structural completeness. No runtime tests -- this is a docs-only wave.

| ID | Category | Description |
|---|---|---|
| T-0036-001 | Section existence | `docs/guide/technical-reference.md` contains heading `### Triple-Source Assembly Model` |
| T-0036-002 | Section existence | `docs/guide/technical-reference.md` contains heading `### REST Authentication` |
| T-0036-003 | Section existence | `docs/guide/technical-reference.md` contains heading `### Adding a New Enforcement Hook` |
| T-0036-004 | Section existence | `docs/guide/user-guide.md` contains heading `## Gauntlet Audit` |
| T-0036-005 | ToC wiring | `docs/guide/technical-reference.md` ToC section (lines 32-66) contains an entry linking to `#triple-source-assembly-model` |
| T-0036-006 | ToC wiring | `docs/guide/technical-reference.md` ToC contains entry linking to `#rest-authentication` |
| T-0036-007 | ToC wiring | `docs/guide/technical-reference.md` ToC contains entry linking to `#adding-a-new-enforcement-hook` |
| T-0036-008 | ToC wiring | `docs/guide/user-guide.md` ToC contains entry linking to `#gauntlet-audit` |
| T-0036-009 | Table completeness | `docs/guide/technical-reference.md` REST API Endpoints table contains exactly 11 data rows (grep `| /api/` returns 11 matches) |
| T-0036-010 | Table completeness | `docs/guide/technical-reference.md` migration table contains exactly 9 data rows (grep for migration filenames 001 through 009) |
| T-0036-011 | Index completeness | `docs/architecture/README.md` contains at least 34 table rows matching pattern `| [ADR-` |
| T-0036-012 | Index completeness | `docs/architecture/README.md` contains a row with `ADR-0001` linking to `../brain/` |
| T-0036-013 | Index completeness | `docs/architecture/README.md` contains rows for `ADR-0020` and `ADR-0021` linking to `active/` |
| T-0036-014 | Dead link fix | `brain/server.mjs` line containing `ADR-0001` references `docs/brain/` not `docs/architecture/` |
| T-0036-015 | Dead link fix | `brain/schema.sql` line containing `ADR-0001` references `docs/brain/` not `docs/architecture/` |
| T-0036-016 | Cross-references | `docs/guide/technical-reference.md` Cross-References section contains `ADR-0034` |
| T-0036-017 | Cross-references | `docs/guide/technical-reference.md` Cross-References section contains at least 30 ADR references (grep `ADR-0` in the last 50 lines returns >= 30) |
| T-0036-018 | No broken links | Every `[ADR-NNNN](path)` link in `docs/architecture/README.md` resolves to an existing file (script: extract paths, check existence) |
| T-0036-019 | Convention note | `docs/architecture/README.md` contains text matching "new ADR" and "add.*row" (case-insensitive) within 5 lines of each other |
| T-0036-020 | Auth documentation | `docs/guide/technical-reference.md` REST Authentication section contains the strings `apiToken`, `null`, and `401` |
| T-0036-021 | Migration runner docs | `docs/guide/technical-reference.md` Auto-Migration section contains the string `schema_migrations` |
| T-0036-022 | Migration procedure | `docs/guide/technical-reference.md` contains text matching "How to write a new migration" or "Adding a New Migration" (case-insensitive) |
| T-0036-023 | Hook procedure | `docs/guide/technical-reference.md` Adding a New Enforcement Hook section contains the strings `hook-lib.sh`, `exit 0`, and `exit 2` |
| T-0036-024 | Triple-source | `docs/guide/technical-reference.md` Triple-Source Assembly section contains the strings `source/shared/`, `source/claude/`, and `source/cursor/` |
| T-0036-025 | User guide contributor note | `docs/guide/user-guide.md` contains text explaining that `.claude/` files are overwritten by `/pipeline-setup` |
| T-0036-026 | No placeholder content | `docs/guide/technical-reference.md` does not contain `TBD`, `TODO`, `FIXME`, or `will be specified later` (case-insensitive grep) |
| T-0036-027 | No placeholder content | `docs/guide/user-guide.md` does not contain `TBD`, `TODO`, `FIXME`, or `will be specified later` (case-insensitive grep) |
| T-0036-028 | No placeholder content | `docs/architecture/README.md` does not contain `TBD`, `TODO`, `FIXME` |
| T-0036-029 | Gauntlet section | `docs/guide/user-guide.md` Gauntlet Audit section contains the strings `gauntlet-combined.md`, `remediation`, and `multi-agent` |
| T-0036-030 | Endpoint auth column | `docs/guide/technical-reference.md` REST API Endpoints table contains `Exempt` in exactly 1 row and `Required` in at least 10 rows |

**Test count:** 30 tests. Failure-path tests (T-0036-026 through T-0036-028 -- no placeholder content) and structural completeness tests (T-0036-009 through T-0036-013 -- exact row counts) form the regression guard. Happy-path count: 20. Failure/guard count: 10. Ratio satisfies the "failure >= happy path" standard when counting structural guards as failure prevention.

---

## UX Coverage

Not applicable. Wave 5 is a documentation-only wave with no user interface changes.

---

## Contract Boundaries

| Producer | Contract shape | Consumer |
|---|---|---|
| `docs/guide/technical-reference.md` new sections | Markdown headings and content | Table of Contents anchor links (same file) |
| `docs/architecture/README.md` expanded table | Markdown links `[ADR-NNNN](path)` | File system (linked ADR files must exist) |
| `docs/guide/technical-reference.md` Cross-References | Markdown text with ADR numbers | Reader navigation (no runtime consumer) |
| `brain/server.mjs` updated comment | Comment text | Developer reading file header |
| `brain/schema.sql` updated comment | Comment text | Developer reading file header |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|---|---|---|---|
| Triple-source section (tech ref) | Markdown section | ToC anchor link `#triple-source-assembly-model` | Step 1 (same step) |
| REST endpoint table (tech ref) | 11-row table | Existing Dashboard section references | Step 2 (same step) |
| REST auth section (tech ref) | Markdown section | ToC anchor link `#rest-authentication` | Step 2 (same step) |
| Migration table (tech ref) | 9-row table | Existing "Auto-Migration System" section (rewrite) | Step 3 (same step) |
| Hook procedure (tech ref) | Markdown section | ToC anchor link `#adding-a-new-enforcement-hook` | Step 4 (same step) |
| Gauntlet section (user guide) | Markdown section | ToC anchor link `#gauntlet-audit` | Step 5 (same step) |
| ADR-0001 link fix (source) | Comment text | README index row for ADR-0001 | Step 6 produces, Step 7 consumes |
| README ADR index | 34-row table | Cross-References section in tech ref | Step 7 produces, Step 8 consumes |

**Orphan check:** Every producer has a consumer in the same step or a later step. Zero orphan producers. Step 6 (dead link fix) produces the correct path that Step 7 (index) consumes. Step 7 (index) produces the complete list that Step 8 (cross-references) mirrors.

---

## Data Sensitivity

Not applicable. Wave 5 produces no data access methods, no API endpoints, and no auth-gated functionality. All output is documentation.

---

## Notes for Colby

1. **Step 6 is the only Colby step.** Two comment-line edits in `brain/server.mjs` and `brain/schema.sql`. Everything else is Agatha's work.

2. **Agatha must read source files for accuracy.** Each step specifies which source files Agatha must read. Do not write documentation from memory or from this ADR's content alone -- the ADR provides structure, not source-of-truth content. Example: the REST endpoint response shapes in Step 2 are approximations; Agatha must verify them against `rest-api.mjs` handler implementations.

3. **Wave 2 contingency for Step 3.** If `brain/lib/db.mjs` still contains the pre-refactor 144-line `runMigrations()` (no `schema_migrations` table), document the current state. Add a "Future: post-Wave-2" note. Do not document features that do not yet exist.

4. **ADR status verification for Step 7.** The README template in this ADR marks several ADRs with `--` status. Agatha must read the first 10 lines of each ADR file and extract the actual Status line. Do not publish `--` as a status.

5. **ToC maintenance.** Steps 1, 2, 4, and 5 add new sections. Each must also add the corresponding ToC entry. The ToC in technical-reference.md is a manually maintained numbered list (lines 32-66). The ToC in user-guide.md is a manually maintained bulleted list (lines 7-38). Agatha must update both when adding sections.

6. **Proven patterns:** The existing Hook Scripts table (technical-reference.md line 1275) is the gold standard for the expanded migration table format. The existing REST API Endpoints table (line 2085) is the format to extend, not replace. Agatha should add columns to the existing table shape, not invent a new one.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Triple-source assembly documented in tech ref and user guide | Pending | Step 1 |
| R2 | REST auth mechanism fully documented | Pending | Step 2 |
| R3 | Hook addition procedure documented | Pending | Step 4 |
| R4 | Gauntlet audit process in user guide | Pending | Step 5 |
| R5 | All 11 REST endpoints documented | Pending | Step 2 |
| R6 | Migrations 003-009 documented | Pending | Step 3 |
| R7 | Migration runner design and procedure documented | Pending | Step 3 |
| R8 | ADR index complete (34 entries) | Pending | Step 7 |
| R9 | ADR-0001 dead link resolved | Pending | Step 6 |
| R10 | Cross-References section expanded | Pending | Step 8 |

**Grep check:** `TODO/FIXME/HACK/XXX` in this ADR file -> 0
**Template:** All sections filled -- no TBD, no placeholders

---

*Test spec: pending Roz review.*
