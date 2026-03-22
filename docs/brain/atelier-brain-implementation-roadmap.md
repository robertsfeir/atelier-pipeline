# Implementation Roadmap: Atelier Brain

**Author:** Robert Sfeir | **Date:** 2026-03-21
**Source Artifacts:**
- Feature Spec: `docs/product/atelier-brain-feature-spec.md` (10 user stories)
- UX Spec: `docs/ux/atelier-brain-settings-ux.md` (single-page settings)
- ADR: `docs/architecture/ADR-0001-atelier-brain.md` (11 steps, 175 tests)

---

## Execution Summary

4 phases. 11 ADR steps grouped by dependency chain. Each phase has a gate — the next phase doesn't start until the gate passes. Total estimated effort: **5-7 pipeline runs** (Large pipeline size).

The critical path runs through **Phase 1 → Phase 2 → Phase 3**. Phase 4 is parallel-safe after Phase 2 completes.

```
Phase 1: Foundation          Phase 2: Intelligence         Phase 3: Integration       Phase 4: Polish
(schema + server + tools)    (TTL + consolidation + API)   (pipeline + personas)      (UI + setup + deploy)

┌─────────────────────┐      ┌─────────────────────┐      ┌──────────────────────┐   ┌──────────────────────┐
│ Step 1: Schema      │─────▶│ Step 4: TTL Timer   │─────▶│ Step 8: Brain Detect │──▶│ Step 7: Settings UI  │
│ Step 2: Scoring     │      │ Step 5: Consolidation│      │ Step 9: Agent Personas│  │ Step 10: Setup Skill │
│ Step 3: MCP Tools   │      │ Step 6: Settings API │      └──────────────────────┘   │ Step 11: Plugin Infra│
└─────────────────────┘      └─────────────────────┘                                  └──────────────────────┘

Gate: 6 tools respond        Gate: background timers       Gate: full pipeline run    Gate: end-to-end setup
via MCP stdio transport      + REST endpoints work         with brain = green         from zero → brain live

Tests: 67                    Tests: 38                     Tests: 23                  Tests: 47
```

---

## Phase 1: Foundation — Schema, Scoring, MCP Tools

**Goal:** A running brain MCP server with 6 tools that respond correctly via stdio.

**Why first:** Everything depends on the schema and server. No TTL without thought types. No consolidation without relations. No UI without API. No pipeline integration without tools.

### Step 1: Schema and Database Setup
| | |
|---|---|
| **ADR Step** | 1 |
| **Creates** | `brain/schema.sql` |
| **Tests** | 11 (4H, 5F, 2B) |
| **Complexity** | Low — DDL only |
| **User Stories** | US-2 (relations), US-3 (conflict schema), US-4 (TTL config), US-5 (brain_config), US-6 (ltree) |

**Deliverable:** Schema applies cleanly on PostgreSQL 17 with pgvector + ltree. All enums, tables, indexes, triggers, seed data verified. `brain_config.brain_enabled` defaults to `false`.

**Roz gate:** Run schema on fresh DB. Verify all 11 tests. Enum values match feature spec. Seed data matches UX spec defaults.

### Step 2: Three-Axis Scoring Function
| | |
|---|---|
| **ADR Step** | 2 |
| **Creates** | Appended to `brain/schema.sql` |
| **Depends on** | Step 1 (tables must exist) |
| **Tests** | 19 (7H, 7F, 5B) |
| **Complexity** | Medium — formula math is simple, testing weight balance needs real data |
| **User Stories** | US-1 (cross-session relevance ranking) |

**Deliverable:** `match_thoughts_scored()` function. `score = (0.5 × recency_decay) + (2.0 × importance) + (3.0 × cosine_similarity)`. Excludes invalidated by default. Scope filter via ltree.

**Roz gate:** Insert test thoughts with known values. Verify ordering under all three axes independently. Boundary cases (empty DB, threshold extremes).

### Step 3: Fork mybrain and Rewrite MCP Tools
| | |
|---|---|
| **ADR Step** | 3 |
| **Creates** | `brain/server.mjs`, `brain/package.json` |
| **Source** | Fork from `/Users/sfeirr/projects/mybrain/server.mjs` (208 lines) |
| **Depends on** | Steps 1 + 2 (schema + scoring function) |
| **Tests** | 37 (15H, 15F, 4B, 2S, 1C) |
| **Complexity** | High — conflict detection LLM integration, atomic transactions |
| **User Stories** | US-1 (search), US-2 (relations, trace), US-3 (conflict detection) |

**6 tools to implement:**

| Tool | Rewrite/New | Key Complexity |
|---|---|---|
| `agent_capture` | Rewrite | Schema-enforced enums, conflict detection (dup/candidate/novel), `supersedes_id` atomic transaction |
| `agent_search` | Rewrite | Uses `match_thoughts_scored()`, updates `last_accessed_at` |
| `atelier_browse` | Rewrite | Enhanced filters (status, type, agent, scope), pagination |
| `atelier_stats` | Rewrite | Reports `brain_enabled`, counts by type/status/agent, consolidation timestamps |
| `atelier_relation` | New | Typed relation creation, `supersedes` auto-invalidates target |
| `atelier_trace` | New | Recursive CTE traversal, configurable depth, backward/forward/both |

**Deliverable:** All 6 tools register and respond via stdio. `agent_capture` enforces all required enums. Conflict detection fires for decision/preference types only. `atelier_trace` traverses diamond graphs without duplication.

**Roz gate:** Full Step 3 test suite including security (SQL injection), concurrency (simultaneous captures), and boundary (self-referential relation, max depth). Verify contract shapes match ADR spec.

### Phase 1 Gate

```
Verification: start brain server → call all 6 tools → verify responses match contract shapes
Tests passing: 67 / 67
Artifact: brain/ directory with schema.sql, server.mjs, package.json
```

---

## Phase 2: Intelligence — TTL, Consolidation, Settings API

**Goal:** Background processes running inside the brain server + REST endpoints for configuration.

**Why second:** Phase 1 gives us tools that work. Phase 2 makes the brain self-maintaining (expired thoughts decay, patterns consolidate) and configurable (API for future UI).

### Step 4: TTL Enforcement Timer
| | |
|---|---|
| **ADR Step** | 4 |
| **Modifies** | `brain/server.mjs` |
| **Depends on** | Step 1 (thought_type_config table), Step 3 (server running) |
| **Tests** | 10 (4H, 4F, 2B) |
| **Complexity** | Low — single UPDATE query on a timer |
| **User Stories** | US-4 (knowledge decay) |

**Deliverable:** `setInterval` on server startup. Reads interval from `brain_config`. Marks expired thoughts. NULL TTL types never expire. Non-blocking.

### Step 5: Consolidation Engine
| | |
|---|---|
| **ADR Step** | 5 |
| **Modifies** | `brain/server.mjs` |
| **Depends on** | Steps 1-3 (schema, scoring, relation creation) |
| **Tests** | 12 (5H, 6F, 1B) |
| **Complexity** | High — LLM synthesis, clustering, relation creation, error handling |
| **User Stories** | US-5 (consolidation) |

**Deliverable:** Background timer. Clusters unconsolidated thoughts by similarity. LLM synthesizes each cluster into a reflection-type thought. `synthesized_from` relations created. Source thoughts stay active. Reflection importance = max(sources) + 0.05, capped at 1.0.

**Critical implementation note (from ADR Notes for Colby):** Don't over-engineer clustering. Simple pairwise cosine similarity > 0.6 among top N by recency is sufficient for v1.

### Step 6: Settings API
| | |
|---|---|
| **ADR Step** | 6 |
| **Modifies** | `brain/server.mjs` |
| **Depends on** | Steps 1, 3 (schema, running server with HTTP mode) |
| **Tests** | 16 (7H, 8F, 1B) |
| **Complexity** | Medium — thin CRUD, but coexists with MCP transport routing |
| **User Stories** | US-4 (TTL config), US-5 (consolidation config), US-7 (health endpoint) |

**7 REST endpoints:**

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Status, count, last/next consolidation, `brain_enabled` |
| `GET /api/config` | Read `brain_config` singleton |
| `PUT /api/config` | Update config (including `brain_enabled` toggle) |
| `GET /api/thought-types` | Read `thought_type_config` rows |
| `PUT /api/thought-types/:type` | Update TTL and importance per type |
| `POST /api/purge-expired` | Delete expired + orphaned relations |
| `GET /api/stats` | Extended counts by type, status, agent |

**Routing note (ADR Notes for Colby):** `/api/*` → REST handlers. Everything else → MCP transport handler.

### Phase 2 Gate

```
Verification: TTL timer expires a test thought → consolidation creates a reflection →
              all 7 REST endpoints return valid JSON → health endpoint shows brain_enabled flag
Tests passing: 105 / 105 (cumulative: Phase 1 + 2)
Artifact: brain/server.mjs with background timers + REST API coexisting with MCP tools
```

---

## Phase 3: Integration — Pipeline Detection + Agent Personas

**Goal:** The atelier-pipeline knows the brain exists, checks its health, and every agent has mandatory brain behaviors.

**Why third:** The brain has to work (Phase 1) and be self-maintaining (Phase 2) before the pipeline starts depending on it. This phase wires the brain into the existing pipeline without breaking baseline behavior.

### Step 8: Pipeline Integration — Brain Detection
| | |
|---|---|
| **ADR Step** | 8 |
| **Modifies** | `templates/rules/agent-system.md`, `templates/rules/default-persona.md` |
| **Depends on** | Phase 2 complete (server + `atelier_stats` reporting `brain_enabled`) |
| **Tests** | 23 (10H, 10F, 3R) — includes regression tests for Poirot/Distillator isolation |
| **Complexity** | Low — config + one tool call + state variable |
| **User Stories** | US-7 (brain as optional enhancement) |

**Two-gate detection:**
1. **Gate 1 (infrastructure):** Is the brain MCP server running? (tool available?)
2. **Gate 2 (runtime):** Does `atelier_stats` return `brain_enabled: true`?

Both pass → `brain_available: true` in pipeline state. Either fails → baseline mode. No pipeline ever fails because of the brain.

**Regression critical:** T-0008-008 (Poirot gets no brain context), T-0008-009 (full run with brain disabled = identical to current output), T-0008-018 (Distillator gets no brain context).

### Step 9: Pipeline Integration — Agent Personas
| | |
|---|---|
| **ADR Step** | 9 |
| **Modifies** | 8 files (see below) |
| **Depends on** | Step 8 (brain_available flag exists in pipeline state) |
| **Tests** | Covered by Step 8-9 combined suite (23 tests) |
| **Complexity** | Medium — many files, additive changes |
| **User Stories** | Agent Operating Model (all 10 agents specified) |

**Files modified:**

| File | Agent | Changes |
|---|---|---|
| `templates/agents/cal.md` | Cal | `## Brain Access (MANDATORY)` section: `agent_search` before design + mid-ADR, `atelier_trace` for decision chains, `agent_capture` for decisions/rejections/insights |
| `templates/agents/colby.md` | Colby | Brain Access section: `agent_search` before build + mid-build, `agent_capture` for implementation insights/lessons |
| `templates/agents/roz.md` | Roz | Brain Access section: `agent_search` before tests + during QA, `agent_capture` for patterns/investigations/doc-impact |
| `templates/agents/robert.md` | Robert-skill + Robert-subagent | Brain Access section: `agent_search` for spec evolution/corrections, `agent_capture` for spec rationale/drift/verdicts, `atelier_relation` for supersedes chains, `atelier_trace` for drift history |
| `templates/agents/sable.md` | Sable-skill + Sable-subagent | Brain Access section: `agent_search` for prior UX/accessibility, `agent_capture` for UX rationale/drift/audits, `atelier_relation` for supersedes |
| `templates/agents/documentation-expert.md` | Agatha | Brain Access section: `agent_search` for prior doc reasoning, `agent_capture` for doc update reasoning |
| `templates/rules/default-persona.md` | Eva | Gate-triggered captures, cross-agent relations, pre-delegation search, health check, Poirot finding capture, session summary |
| `templates/references/invocation-templates.md` | All | Add optional BRAIN section to subagent prompt template |

**Unchanged:** `distillator.md`, `ellis.md`, `investigator.md` (Poirot) — no brain access by design.

**Language requirement:** All brain sections use directive language — "MUST call", "calls" — never "can", "may", "should consider". Conditional on availability, mandatory when available.

### Phase 3 Gate

```
Verification: full pipeline run with brain enabled → agents search and capture →
              brain thoughts appear in database → second pipeline run retrieves prior context →
              brain disabled run produces identical output to pre-brain baseline
Tests passing: 128 / 128 (cumulative: Phase 1 + 2 + 3)
Artifact: all agent personas updated, pipeline state tracks brain_available
```

---

## Phase 4: Polish — UI, Setup Skill, Plugin Infrastructure

**Goal:** End-to-end developer experience from zero to brain-enabled. Settings UI. Docker deployment. Colleague onboarding.

**Why last:** The brain works (Phase 1), maintains itself (Phase 2), and the pipeline uses it (Phase 3). Phase 4 is the developer-facing wrapper — it doesn't change brain behavior, it makes it accessible.

**Parallel-safe:** Phase 4 can start after Phase 2 completes. Steps 7 and 10 depend on the REST API (Phase 2), not on pipeline integration (Phase 3). Step 11 is infrastructure-only.

### Step 7: Settings UI
| | |
|---|---|
| **ADR Step** | 7 |
| **Creates** | `brain/ui/index.html`, `brain/ui/settings.js`, `brain/ui/settings.css` |
| **Depends on** | Step 6 (REST API endpoints) |
| **Tests** | 20 (5H, 8F, 2B, 1S, 4A) |
| **Complexity** | Medium — vanilla HTML/CSS/JS, but accessibility and responsive requirements |
| **User Stories** | US-4 (TTL config), US-5 (consolidation config), US-7 (health visibility) |

**All 7 UX states from Sable's spec:**

| State | Key Behavior |
|---|---|
| Empty (not configured) | Dimmed sections, "Run /brain-setup..." helper |
| Loading (connecting) | Pulse animation, disabled inputs |
| Populated (normal) | Full layout, all editable |
| Shared config, missing env vars | Config found message, env var guidance, toggle disabled |
| Shared config, connected | "(shared)" badge on read-only fields, "(local override)" labels |
| Error (brain unreachable) | Amber status, sections still editable |
| Overflow | N/A (scrolls naturally) |

**Implementation constraints (from ADR Notes for Colby):**
- Vanilla HTML/CSS/JS. No build step. No framework.
- Status bar polls `/api/health` every 30s
- Inline edit: click cell → show input → blur → save (no edit-mode button)
- ∞ rendered as text, falls back to "never"
- Focus-trap on confirmation modals, Escape to dismiss

### Step 10: Brain Setup Skill
| | |
|---|---|
| **ADR Step** | 10 |
| **Creates** | `skills/brain-setup/SKILL.md` |
| **Modifies** | `.claude-plugin/plugin.json` (add skill reference) |
| **Depends on** | Steps 1 (schema.sql), 11 (docker-compose.yml) |
| **Tests** | 14 (5H, 9F) |
| **Complexity** | Medium — branching flow (personal/shared, Docker/local, first-time/colleague) |
| **User Stories** | US-7 (opt-in setup), US-8 (solo), US-9 (team shared) |

**Two paths:**
- **Path A (first-time):** Personal or shared? → Docker or local? → API key → scope → verify → write config → set `brain_enabled: true`
- **Path B (colleague):** Detect project config → check env vars → verify or guide

**Security constraint:** Shared setup never writes bare secrets. Only `${ENV_VAR}` placeholders in `.claude/brain-config.json`. Docker default password triggers warning for team use.

### Step 11: Plugin Deployment Infrastructure
| | |
|---|---|
| **ADR Step** | 11 |
| **Creates** | `.mcp.json`, `brain/docker-compose.yml`, `brain/docker-entrypoint.sh` |
| **Modifies** | `.claude-plugin/plugin.json` (hooks, MCP server reference) |
| **Depends on** | Step 3 (server.mjs exists) |
| **Tests** | 13 (6H, 7F) |
| **Complexity** | Medium — config resolution with fallbacks, override merging |
| **User Stories** | US-7 (opt-in), US-8 (Docker), US-9 (shared config), US-10 (config priority) |

**Config priority chain (brain server startup):**
1. `BRAIN_CONFIG_PROJECT` (`.claude/brain-config.json`) → project-level
2. `BRAIN_CONFIG_USER` (`${CLAUDE_PLUGIN_DATA}/brain-config.json`) → user-level
3. Neither exists → exit cleanly, no tools registered

**Local overrides:** `${CLAUDE_PLUGIN_DATA}/brain-overrides.json` merges behavior settings on top of project config. Cannot override connection details.

### Phase 4 Gate

```
Verification: fresh machine → install plugin → /brain-setup (Docker) → brain live →
              Settings UI shows populated state → colleague clones repo → env vars → brain connects →
              Settings UI shows shared state with badges
Tests passing: 175 / 175 (all)
Artifact: complete developer experience, all deployment tiers functional
```

---

## Dependency Graph

```
Step 1 ─────┬──▶ Step 2 ──▶ Step 3 ─────┬──▶ Step 4
(schema)    │    (scoring)   (tools)     │    (TTL timer)
            │                            │
            │                            ├──▶ Step 5
            │                            │    (consolidation)
            │                            │
            │                            ├──▶ Step 6 ──▶ Step 7
            │                            │    (API)      (UI)
            │                            │
            │                            ├──▶ Step 8 ──▶ Step 9
            │                            │    (detect)   (personas)
            │                            │
            └──▶ Step 11 ◀──────────────┘
                 (deploy infra)

            Step 10 depends on: Step 1 (schema.sql) + Step 11 (docker-compose)
```

**Parallelization opportunities within phases:**
- Phase 2: Steps 4, 5, 6 are independent of each other (all depend on Phase 1, not each other)
- Phase 4: Steps 7, 10, 11 can run in parallel after their respective dependencies are met

---

## Pipeline Execution Plan

Each row is one pipeline run. Pipeline size reflects expected Colby effort.

| Run | Pipeline Size | Steps | Gate | Cumulative Tests |
|---|---|---|---|---|
| **Run 1** | Large | Step 1 + Step 2 | Schema + scoring function pass all 30 tests | 30 |
| **Run 2** | Large | Step 3 | 6 MCP tools working via stdio, all 37 tests | 67 |
| **Run 3** | Medium | Steps 4 + 5 + 6 (parallel) | TTL timer + consolidation + REST API, 38 tests | 105 |
| **Run 4** | Medium | Steps 8 + 9 | Pipeline detection + agent personas, 23 tests | 128 |
| **Run 5** | Medium | Steps 7 + 10 + 11 (parallel) | UI + setup skill + deploy infra, 47 tests | 175 |

**Total: 5 pipeline runs.**

Run 2 is the riskiest — conflict detection LLM integration, atomic transactions, and 37 tests is the largest single-step suite. If it needs a fix cycle, budget a Run 2b.

---

## Risk Register

| Risk | P | I | Mitigation | Owner |
|---|---|---|---|---|
| Conflict detection LLM integration takes >1 run | 3 | 3 | Extract `classifyConflict()` as isolated function. Test LLM contract independently before integration. | Colby |
| Consolidation produces low-quality reflections | 2 | 4 | Prompt engineering in v1. Human can invalidate bad reflections. Source thoughts preserved. Iterate prompt post-launch. | Cal (prompt design) |
| Agent personas bloat token count with brain sections | 3 | 2 | Brain sections are conditional (~200-400 tokens). Monitor total prompt size per agent. Distillator compression already exists. | Eva |
| Settings UI accessibility misses Roz's 4 checks | 2 | 3 | Roz's test spec has explicit a11y tests (T-0007-015 through T-0007-018). Build to spec, not after-the-fact audit. | Colby |
| Docker compose port conflict on 5432 (existing PostgreSQL) | 3 | 2 | Docker compose should use configurable port. `/brain-setup` detects existing PostgreSQL and offers local option. | Step 11 |
| mybrain tool namespace collision despite renaming | 1 | 5 | All 6 atelier tools have distinct names (agent_*, atelier_*). Verified across all three specs. No overlap with mybrain's 4 tools. | Verified |

---

## File Manifest

**New files (12):**

| File | Created in | Purpose |
|---|---|---|
| `brain/schema.sql` | Step 1 | Full Option D schema + scoring function |
| `brain/server.mjs` | Step 3 | Forked from mybrain, 6 MCP tools + REST API + timers |
| `brain/package.json` | Step 3 | Dependencies for brain server |
| `brain/ui/index.html` | Step 7 | Settings page |
| `brain/ui/settings.js` | Step 7 | Settings page logic |
| `brain/ui/settings.css` | Step 7 | Settings page styles |
| `brain/docker-compose.yml` | Step 11 | PostgreSQL 17 + pgvector + ltree |
| `brain/docker-entrypoint.sh` | Step 11 | Schema on first boot |
| `.mcp.json` | Step 11 | Brain MCP server registration |
| `skills/brain-setup/SKILL.md` | Step 10 | Setup skill definition |
| `templates/references/invocation-templates.md` | Step 9 | Updated with BRAIN context slot |
| `docs/architecture/atelier-brain-implementation-roadmap.md` | Now | This document |

**Modified files (10):**

| File | Modified in | Change |
|---|---|---|
| `.claude-plugin/plugin.json` | Steps 10, 11 | Add skill reference + hooks + MCP server |
| `templates/agents/cal.md` | Step 9 | Brain Access section |
| `templates/agents/colby.md` | Step 9 | Brain Access section |
| `templates/agents/roz.md` | Step 9 | Brain Access section |
| `templates/agents/robert.md` | Step 9 | Brain Access section |
| `templates/agents/sable.md` | Step 9 | Brain Access section |
| `templates/agents/documentation-expert.md` | Step 9 | Brain Access section |
| `templates/rules/agent-system.md` | Step 8 | Brain detection config |
| `templates/rules/default-persona.md` | Steps 8, 9 | Eva: health check + gate captures + brain context |

**Untouched (intentionally):**

| File | Reason |
|---|---|
| `templates/agents/distillator.md` | No brain access — mechanical compression |
| `templates/agents/ellis.md` | No brain access — git is the memory |
| `templates/agents/investigator.md` | No brain access — Poirot stays blind |
| `/Users/sfeirr/projects/mybrain/*` | Separate project. Personal brain untouched. |

---

## Success Criteria

After Run 5 completes:

1. **175 tests pass.** No exceptions, no skips.
2. **Zero baseline regression.** Pipeline with `brain_enabled: false` produces identical output to pre-brain pipeline.
3. **End-to-end setup works on fresh machine.** `/brain-setup` → Docker → brain live → agents capture and retrieve.
4. **Colleague onboarding path works.** Clone repo with project config → set env var → brain connects automatically.
5. **Settings UI shows all 7 states.** Including shared-config badges and local override labels.
6. **mybrain untouched.** Personal brain has no changes, no coupling, no namespace collision.
