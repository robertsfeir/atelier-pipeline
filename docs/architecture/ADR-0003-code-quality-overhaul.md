# ADR-0003: Code Quality and Security Overhaul

## DoR: Requirements Extracted

**Source:** Roundtable consensus (5-agent review + Gilfoyle audit), user approval of 18 work items across 6 batches.

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Remove eval() from quality-gate.sh (line 52) and check-complexity.sh (line 39) | Gilfoyle audit, command injection finding |
| 2 | Fix unquoted word splitting in enforce-paths.sh (lines 59, 79) and check-brain-usage.sh (line 40) | Gilfoyle audit, ShellCheck violations |
| 3 | Make jq a hard failure in all hooks -- exit with error + message when jq missing | Roundtable consensus: silent pass = invisible enforcement bypass |
| 4 | Fix substring path matching in enforce-paths.sh -- anchor to path start | Gilfoyle audit: `*"$prefix"*` matches anywhere in path |
| 5 | Create CLAUDE.md template with project-specific values | Missing file: referenced by both persona files but does not exist |
| 6 | Create docs/architecture/README.md -- ADR index | Missing file: agent-system.md references Eva maintaining it |
| 7 | Fix Eva context contradiction between default-persona.md:34 and agent-system.md:72 | Doc contradiction: both claim to define Eva's loaded context, disagree on CLAUDE.md |
| 8 | Fix file count inconsistency across README, user-guide, technical-reference | README says 27 then 32; user-guide says 34; tech-ref says 27+7 |
| 9 | Replace grep-based gate in enforce-sequencing.sh with structured state parsing | Roundtable consensus: grep for "roz.*pass" is fragile, false positives/negatives |
| 10 | Add auth to brain REST API -- Bearer token via ATELIER_BRAIN_API_TOKEN | Security: REST API on port 8788 has no auth, CORS is `*` |
| 11 | Remove default password from docker-compose.yml -- fail if env not set | Security: `POSTGRES_PASSWORD: ${ATELIER_BRAIN_DB_PASSWORD:-atelier}` hardcodes a default |
| 12 | Add pronouns to cal.md, colby.md (she/her), roz.md, agatha.md, ellis.md, distillator.md | Agent consistency: only robert.md, sable.md, investigator.md have pronouns |
| 13 | Remove distillator from brain_required_agents in enforcement-config.json | Distillator has no Brain Access section in its persona |
| 14 | Add troubleshooting section to user-guide.md | Doc gap: common issues (jq missing, brain connection, hook errors) undocumented |
| 15 | Split server.mjs (1330 lines) into modules | Maintainability: monolith exceeds complexity thresholds |
| 16 | Fix O(n^2) consolidation clustering | Performance: sequential DB queries for pairwise similarity, lines 1079-1095 |
| 17 | Fix NOT IN anti-pattern in purge endpoint | Performance: lines 965-968, NOT IN subquery on potentially large table |
| 18 | Comprehensive test suite: shell hooks (bats-core) + server modules (node:test) | Coverage target: 80%+, complexity target: <10 per function |

**Retro risks:**
- "Sensitive Data in Return Shapes" lesson: REST API endpoints (`/api/config`, `/api/stats`) expose database configuration without auth. Directly relevant to item 10.
- "Self-Reporting Bug Codification" lesson: Roz writes tests before Colby builds. Relevant to batch 6 ordering -- test spec comes first.

## Status

Proposed

## Context

A comprehensive code review identified 18 issues across the atelier-pipeline codebase spanning security vulnerabilities (eval injection, missing auth, default credentials), reliability gaps (fragile grep-based enforcement, silent jq failures), documentation contradictions, and maintainability concerns (1330-line monolith, O(n^2) algorithm). The user approved all 18 items, organized into 6 batches ordered by risk (security first, tests last).

### Spec Challenge

The spec assumes that the 6 batches can be implemented sequentially with clean boundaries. If this is wrong -- specifically, if batch 5 (server.mjs modularization) changes exports/APIs that batch 6 (test suite) depends on -- the design fails because tests written against the pre-modularized API would break during modularization. **Mitigation:** Batch 5 defines the module API surface before batch 6 writes tests against it. Batch 6 tests the modularized code, not the monolith.

### Cyclomatic Complexity Analysis (Current State)

| Function | File | Estimated CC | Issue |
|----------|------|-------------|-------|
| `handleRestApi` | server.mjs:840-999 | ~25 | 9 route branches, nested validation |
| `agent_capture` handler | server.mjs:349-488 | ~18 | Conflict detection branching, transaction management |
| `detectConflicts` | server.mjs:247-307 | ~12 | Tiered similarity thresholds with LLM fallback |
| `runConsolidation` | server.mjs:1050-1173 | ~15 | Nested loops, cluster formation, LLM calls |
| `registerTools` | server.mjs:329-834 | ~30+ | All 6 MCP tools in one function |
| `resolveConfig` | server.mjs:46-91 | ~10 | Config cascade with env var resolution |
| `path_matches` + callers | enforce-paths.sh | ~12 | Case-statement branching per agent type |

Target: <10 per function after modularization.

## Decision

Implement all 18 items in 6 batches (mapped to 6 ADR steps), ordered by risk. Security and enforcement fixes first, then documentation, then modularization, then tests. Each batch is independently mergeable and testable.

### Module Map (server.mjs Split -- Step 5)

After modularization, `brain/` will contain these modules:

```
brain/
  server.mjs           # Entry point (~200 lines): startup, mode selection, HTTP server creation
  lib/
    config.mjs          # resolveConfig(), resolveIdentity(), constants (enums, model names)
    db.mjs              # Pool creation, pgvector registration, runMigrations()
    embed.mjs           # getEmbedding() -- OpenRouter embedding API client
    conflict.mjs        # classifyConflict(), detectConflicts(), getBrainConfig()
    tools.mjs           # registerTools() -- all 6 MCP tool definitions
    rest-api.mjs        # handleRestApi(), readBody() -- all REST routes
    consolidation.mjs   # runConsolidation(), startConsolidationTimer()
    ttl.mjs             # runTTLEnforcement(), startTTLTimer()
    static.mjs          # handleStaticFile(), MIME_TYPES
```

**Dependency graph (arrows = imports):**

```
server.mjs
  |-- config.mjs          (no deps on other lib/ modules)
  |-- db.mjs              <-- config.mjs (DATABASE_URL)
  |-- tools.mjs           <-- db.mjs (pool), embed.mjs, conflict.mjs, config.mjs (enums)
  |-- rest-api.mjs         <-- db.mjs (pool), conflict.mjs (getBrainConfig), config.mjs
  |-- consolidation.mjs   <-- db.mjs (pool), embed.mjs, conflict.mjs (getBrainConfig), config.mjs
  |-- ttl.mjs             <-- db.mjs (pool), conflict.mjs (getBrainConfig)
  |-- static.mjs          (no deps on other lib/ modules)

config.mjs   --> (standalone: fs, child_process, process.env)
db.mjs       --> config.mjs
embed.mjs    --> config.mjs (OPENROUTER_API_KEY, EMBEDDING_MODEL)
conflict.mjs --> embed.mjs (indirect, via caller passing embedding), db.mjs (for getBrainConfig)
```

**Key design decisions for the split:**
- `db.mjs` exports a `pool` instance and an `init()` function (runs migrations, registers pgvector).
- `config.mjs` exports resolved config, constants, and identity. No database dependency.
- `tools.mjs` exports `registerTools(server, pool)` -- receives pool as parameter, no import cycle.
- `rest-api.mjs` exports `createRestHandler(pool)` -- returns the handler function, receives pool.
- `server.mjs` is the only module with top-level await. All others export functions/factories.

### Consolidation Fix (Step 5 -- Item 16)

**Current approach (O(n^2)):** Lines 1079-1095 iterate all thought pairs, issuing a DB query per pair to compute vector similarity:

```javascript
for (let i = 0; i < thoughts.length; i++) {
  for (let j = i + 1; j < thoughts.length; j++) {
    const simResult = await client.query(
      `SELECT (1 - ($1::vector(1536) <=> $2::vector(1536)))::float AS sim`,
      [thoughts[i].embedding, thoughts[j].embedding]
    );
  }
}
```

With `consolidation_max_thoughts = 20`, this is 190 queries per consolidation run.

**New approach (SQL vectorized):** Single query computes all pairwise similarities above threshold, returns clusterable pairs:

```sql
WITH candidates AS (
  SELECT t.id, t.content, t.thought_type, t.importance, t.embedding
  FROM thoughts t
  WHERE t.status = 'active'
    AND t.thought_type != 'reflection'
    AND NOT EXISTS (
      SELECT 1 FROM thought_relations r
      WHERE r.target_id = t.id AND r.relation_type = 'synthesized_from'
    )
  ORDER BY t.created_at DESC
  LIMIT $1
)
SELECT
  a.id AS id_a,
  b.id AS id_b,
  (1 - (a.embedding <=> b.embedding))::float AS similarity
FROM candidates a
JOIN candidates b ON a.id < b.id
WHERE (1 - (a.embedding <=> b.embedding)) > 0.6
```

This returns only the similar pairs in a single query. JS code then builds clusters from the pair list using union-find (no DB round-trips). Complexity drops from O(n^2) DB queries to 1 DB query + O(n) JS processing.

### Purge Fix (Step 5 -- Item 17)

**Current (anti-pattern):**
```sql
DELETE FROM thought_relations WHERE
  source_id NOT IN (SELECT id FROM thoughts) OR
  target_id NOT IN (SELECT id FROM thoughts)
```

**Fixed (LEFT JOIN):**
```sql
DELETE FROM thought_relations r
USING (
  SELECT r2.id
  FROM thought_relations r2
  LEFT JOIN thoughts t1 ON r2.source_id = t1.id
  LEFT JOIN thoughts t2 ON r2.target_id = t2.id
  WHERE t1.id IS NULL OR t2.id IS NULL
) orphans
WHERE r.id = orphans.id
```

## Alternatives Considered

### Alternative A: Incremental Fixes Without Modularization

Fix items 1-14, 16-17 in the monolithic server.mjs. Skip the modularization (item 15) and write tests against the monolith.

**Pros:** Less disruption, fewer files changed, faster to implement.
**Cons:** server.mjs stays at 1330 lines with CC>25 functions. Tests would be coupled to the monolith structure. Future changes remain high-risk. Does not meet the <10 CC target.

**Rejected because:** The complexity target is a hard requirement. Testing a monolith with 25+ CC functions means testing through deeply nested branches, which produces brittle tests.

### Alternative B: Full Rewrite of server.mjs in TypeScript

Rewrite the brain server in TypeScript with proper type safety, eliminating the need for runtime Zod validation of internal interfaces.

**Pros:** Type safety catches bugs at compile time. Better IDE support. Eliminates a class of errors entirely.
**Cons:** Doubles the scope. Requires build toolchain (tsc, tsconfig). Current Zod validation on MCP tool inputs is still needed (external boundary). The brain has no pre-existing TypeScript infrastructure.

**Rejected because:** The ROI does not justify the scope increase. The brain server's external boundary (MCP tools, REST API) already validates with Zod. Internal type safety is a nice-to-have, not a quality gate.

### Alternative C: Database-Level Auth Instead of Application-Level Auth

Use PostgreSQL's built-in role system and row-level security for REST API auth instead of Bearer token middleware.

**Pros:** Auth enforced at the database layer, harder to bypass. No token management in application code.
**Cons:** REST API runs over HTTP, not direct DB connections. RLS does not apply to HTTP requests. Would require a proxy layer (PostgREST or similar), adding infrastructure complexity.

**Rejected because:** The REST API is an HTTP server. Bearer token auth is the standard pattern for HTTP APIs. Database-level auth solves a different problem (direct DB access control, which is already handled by the Docker network).

## Consequences

**Positive:**
- All command injection vulnerabilities eliminated (eval removal)
- REST API protected by auth token, CORS restricted to localhost
- No default credentials in version control
- Hook enforcement becomes reliable (hard jq failure, structured state parsing, anchored paths)
- server.mjs drops from 1330 lines to ~200 lines entry point + 9 focused modules
- Consolidation performance improves from O(n^2) DB queries to 1 query
- Test suite provides 80%+ coverage as a regression safety net
- Documentation contradictions resolved -- single source of truth for file counts and Eva's context

**Negative:**
- Module split changes import paths -- any external code importing from server.mjs directly would break (currently no external consumers)
- Bearer token auth requires setting ATELIER_BRAIN_API_TOKEN env var -- one more setup step
- Removing the default DB password is a breaking change for users who relied on it

**Neutral:**
- bats-core becomes a dev dependency for shell hook testing
- node:test is built-in (Node 18+), no additional dependency

## Blast Radius

### Files Modified (by batch)

**Batch 1 -- Security & Enforcement:**
- `source/claude/hooks/quality-gate.sh` -- remove eval (line 52), add jq hard failure
- `source/claude/hooks/check-complexity.sh` -- remove eval (line 39), add jq hard failure
- `source/claude/hooks/enforce-paths.sh` -- fix word splitting (lines 59, 79), fix path anchoring (line 49), add jq hard failure
- `source/claude/hooks/enforce-sequencing.sh` -- add jq hard failure
- `source/claude/hooks/enforce-git.sh` -- add jq hard failure
- `source/claude/hooks/check-brain-usage.sh` -- fix word splitting (line 40), add jq hard failure
- Dual tree: `.claude/hooks/` mirrors `source/claude/hooks/` (installed copies)

**Batch 2 -- Missing Files & Doc Contradictions:**
- `CLAUDE.md` -- NEW FILE (project root)
- `docs/architecture/README.md` -- NEW FILE
- `.claude/rules/default-persona.md` -- line 34, reconcile context statement
- `.claude/rules/agent-system.md` -- line 72, reconcile context statement
- `README.md` -- fix file count (lines 40, 206)
- `docs/guide/user-guide.md` -- verify file count (line 46, already says 34)
- `docs/guide/technical-reference.md` -- fix file count (lines 101, 153, 761)
- `skills/pipeline-setup/SKILL.md` -- fix file count (lines 109, 181, 241)
- Dual tree: `source/rules/` mirrors `.claude/rules/`

**Batch 3 -- Enforcement Reliability:**
- `source/claude/hooks/enforce-sequencing.sh` -- replace grep with structured parsing
- `brain/server.mjs` (or `brain/lib/rest-api.mjs` if batch 5 lands first) -- add Bearer auth middleware, restrict CORS
- `brain/docker-compose.yml` -- remove default password fallback
- Dual tree: `.claude/hooks/enforce-sequencing.sh`

**Batch 4 -- Agent Persona Cleanup:**
- `.claude/agents/cal.md` -- add pronouns
- `.claude/agents/colby.md` -- add pronouns (she/her)
- `.claude/agents/roz.md` -- add pronouns
- `.claude/agents/agatha.md` -- add pronouns
- `.claude/agents/ellis.md` -- add pronouns
- `.claude/agents/distillator.md` -- add pronouns
- `source/claude/hooks/enforcement-config.json` -- remove distillator from brain_required_agents
- `.claude/hooks/enforcement-config.json` -- same
- `docs/guide/user-guide.md` -- add troubleshooting section
- Dual tree: `source/shared/agents/` mirrors `.claude/agents/`

**Batch 5 -- server.mjs Modularization:**
- `brain/server.mjs` -- reduce to ~200 line entry point
- `brain/lib/config.mjs` -- NEW
- `brain/lib/db.mjs` -- NEW
- `brain/lib/embed.mjs` -- NEW
- `brain/lib/conflict.mjs` -- NEW
- `brain/lib/tools.mjs` -- NEW
- `brain/lib/rest-api.mjs` -- NEW (with auth middleware from batch 3)
- `brain/lib/consolidation.mjs` -- NEW (with SQL fix from item 16)
- `brain/lib/ttl.mjs` -- NEW
- `brain/lib/static.mjs` -- NEW

**Batch 6 -- Test Suite:**
- `tests/hooks/` -- NEW directory, bats test files
- `tests/brain/` -- NEW directory, node:test files
- `brain/package.json` -- add test script
- `package.json` (root) -- add test script, bats-core dev dependency (or document install)

### Consumers Affected

| Changed Entity | Consumers | Impact |
|----------------|-----------|--------|
| Hook exit codes (jq hard failure) | `.claude/settings.json` hook registration | Hooks now block instead of silently passing when jq missing |
| `enforce-sequencing.sh` state parsing | `docs/pipeline/pipeline-state.md` format | State file must include structured markers (not free-form text) |
| `brain/server.mjs` imports | `brain/package.json` "start" script | Entry point unchanged -- `node server.mjs` still works |
| REST API auth header | `brain/ui/settings.js` | Settings UI must send Bearer token (or be same-origin) |
| Docker default password removal | Users' shell profiles / CI configs | Must set `ATELIER_BRAIN_DB_PASSWORD` env var |
| `CLAUDE.md` creation | Claude Code (auto-loads CLAUDE.md) | New file, no existing consumers broken |
| File count references | README, user-guide, tech-ref, SKILL.md | All updated to consistent value |

## Implementation Plan

### Step 1: Security and Enforcement Hardening (Batch 1)

**Files to create/modify:**
- `source/claude/hooks/quality-gate.sh` -- replace `eval "$TEST_COMMAND"` with `bash -c "$TEST_COMMAND"` (or direct command splitting)
- `source/claude/hooks/check-complexity.sh` -- replace `eval "$CMD"` with `bash -c "$CMD"`
- `source/claude/hooks/enforce-paths.sh` -- fix `for pattern in $patterns` to `while IFS= read -r pattern`, fix `for blocked in $COLBY_BLOCKED` to `while IFS= read -r blocked`, change `*"$prefix"*` to `"$prefix"*` in path_matches
- `source/claude/hooks/check-brain-usage.sh` -- fix `for agent in $BRAIN_AGENTS` to `while IFS= read -r agent`
- All 6 hooks: replace `exit 0` after jq check with `echo "ERROR: jq is required..." >&2; exit 2`

**Acceptance criteria:**
- No `eval` calls remain in any hook file
- All `jq -r '...' | for x in $var` patterns use `while IFS= read -r` loops
- `path_matches` anchors patterns to path start (prefix match, not substring)
- Missing jq causes hook to exit 2 with descriptive error message
- All hooks still pass with valid inputs and jq installed

**Estimated complexity:** Low-Medium (6 files, mechanical replacements)

### Step 2: Missing Files and Documentation Fixes (Batch 2)

**Files to create/modify:**
- `CLAUDE.md` -- NEW: project-level context file with tech stack, test commands, source structure
- `docs/architecture/README.md` -- NEW: ADR index listing ADR-0001, ADR-0002, ADR-0003
- `.claude/rules/default-persona.md` (line 34) -- change "CLAUDE.md (the slimmed version)" to clarify it is auto-loaded by Claude Code, not manually loaded by Eva
- `.claude/rules/agent-system.md` (line 72) -- align language with default-persona.md
- `README.md` -- standardize file count to 34
- `docs/guide/technical-reference.md` -- standardize file count to 34
- `skills/pipeline-setup/SKILL.md` -- standardize file count to 34

**Acceptance criteria:**
- `CLAUDE.md` exists with project-specific values (not placeholders)
- `docs/architecture/README.md` exists with all ADRs indexed
- Eva context description is consistent between both rule files
- All references to installed file count say "34 files"

**Estimated complexity:** Low (new files + text edits)

### Step 3: Enforcement Reliability (Batch 3)

**Files to create/modify:**
- `source/claude/hooks/enforce-sequencing.sh` -- replace `grep -qi "roz.*pass\|qa.*pass\|verdict.*pass"` with structured JSON or marker-based parsing
- `brain/server.mjs` (or `brain/lib/rest-api.mjs`) -- add Bearer token auth middleware, restrict CORS from `*` to `localhost`
- `brain/docker-compose.yml` -- change `POSTGRES_PASSWORD: ${ATELIER_BRAIN_DB_PASSWORD:-atelier}` to `POSTGRES_PASSWORD: ${ATELIER_BRAIN_DB_PASSWORD:?Set ATELIER_BRAIN_DB_PASSWORD}` (bash parameter expansion -- error if unset)

**Structured state parsing design:**
The pipeline-state.md file will include a machine-readable status line:
```
<!-- PIPELINE_STATUS: {"roz_qa": "PASS", "phase": "review", "timestamp": "..."} -->
```
The hook parses this with jq instead of grepping free-form text. Eva writes this marker when updating pipeline state. The hook checks `roz_qa == "PASS"` specifically.

**REST API auth design:**
- Read `ATELIER_BRAIN_API_TOKEN` from environment at startup
- If set: require `Authorization: Bearer <token>` on all `/api/*` routes except `/api/health` (health check remains public for monitoring)
- If not set: API runs without auth (development mode), log a warning at startup
- CORS: change `Access-Control-Allow-Origin: *` to `Access-Control-Allow-Origin: http://localhost:${PORT}`
- Settings UI served from same origin, no CORS needed for same-origin requests

**Acceptance criteria:**
- enforce-sequencing.sh uses structured parsing, not grep
- REST API rejects requests without valid Bearer token (when token configured)
- CORS restricted to localhost
- docker-compose.yml fails to start without ATELIER_BRAIN_DB_PASSWORD set
- Pipeline state file includes machine-readable status marker

**Estimated complexity:** Medium (structured parsing requires Eva state-writing changes)

### Step 4: Agent Persona Cleanup (Batch 4)

**Files to create/modify:**
- `.claude/agents/cal.md` -- add `Pronouns: he/him.` after name/role line
- `.claude/agents/colby.md` -- add `Pronouns: she/her.` after name/role line
- `.claude/agents/roz.md` -- add `Pronouns: she/her.` after name/role line
- `.claude/agents/agatha.md` -- add `Pronouns: she/her.` after name/role line
- `.claude/agents/ellis.md` -- add `Pronouns: he/him.` after name/role line
- `.claude/agents/distillator.md` -- add `Pronouns: it/its.` after name/role line (compression engine, not a persona)
- `source/claude/hooks/enforcement-config.json` -- remove `"distillator"` from `brain_required_agents` array
- `.claude/hooks/enforcement-config.json` -- same change
- `docs/guide/user-guide.md` -- add troubleshooting section covering: jq not installed, brain connection failures, hook blocking unexpectedly, pipeline state recovery

**Brain Access rationale note:** Distillator is removed from `brain_required_agents` because it has no Brain Access section in its persona file (`.claude/agents/distillator.md`). Distillator is a stateless compression engine -- it does not read from or write to the brain. The warning check in `check-brain-usage.sh` would always fire false positives for Distillator.

**Acceptance criteria:**
- All 9 agent persona files have pronouns declared
- Colby's pronouns are she/her (per user memory)
- `brain_required_agents` in both config files matches agents with Brain Access sections: cal, colby, roz, agatha, sable, robert (6 agents, not 7)
- user-guide.md has a Troubleshooting section with at least 4 common issues

**Estimated complexity:** Low (text edits, config change)

### Step 5: server.mjs Modularization and Performance Fixes (Batch 5)

**Files to create/modify:**
- `brain/lib/config.mjs` -- extract `resolveConfig()`, `resolveIdentity()`, enum constants, `EMBEDDING_MODEL`
- `brain/lib/db.mjs` -- extract pool creation, pgvector registration, `runMigrations()`
- `brain/lib/embed.mjs` -- extract `getEmbedding()`
- `brain/lib/conflict.mjs` -- extract `classifyConflict()`, `detectConflicts()`, `getBrainConfig()` + cache
- `brain/lib/tools.mjs` -- extract `registerTools()` (split into individual tool functions internally)
- `brain/lib/rest-api.mjs` -- extract `handleRestApi()`, `readBody()`, add auth middleware from step 3
- `brain/lib/consolidation.mjs` -- extract `runConsolidation()`, `startConsolidationTimer()`, implement SQL vectorized clustering
- `brain/lib/ttl.mjs` -- extract `runTTLEnforcement()`, `startTTLTimer()`
- `brain/lib/static.mjs` -- extract `handleStaticFile()`, `MIME_TYPES`
- `brain/server.mjs` -- reduce to entry point: imports, init sequence, HTTP server creation

**Module export contracts:**

```javascript
// config.mjs
export { resolveConfig, resolveIdentity, THOUGHT_TYPES, SOURCE_AGENTS,
         SOURCE_PHASES, THOUGHT_STATUSES, RELATION_TYPES, EMBEDDING_MODEL };

// db.mjs
export { createPool, runMigrations };
// createPool(databaseUrl) -> pg.Pool (with pgvector registered)

// embed.mjs
export { getEmbedding };
// getEmbedding(text, apiKey) -> number[]

// conflict.mjs
export { classifyConflict, detectConflicts, getBrainConfig };
// getBrainConfig(clientOrPool) -> brain_config row

// tools.mjs
export { registerTools };
// registerTools(server, pool, config) -> void

// rest-api.mjs
export { createRestHandler };
// createRestHandler(pool, config) -> (req, res) => Promise<boolean>

// consolidation.mjs
export { runConsolidation, startConsolidationTimer };

// ttl.mjs
export { runTTLEnforcement, startTTLTimer };

// static.mjs
export { handleStaticFile };
```

**Consolidation SQL fix (item 16):** Replace the nested for-loop + per-pair query with a single SQL self-join that returns all pairs above the 0.6 similarity threshold. JS code builds clusters from the pair list using union-find. See Decision section for full SQL.

**Purge LEFT JOIN fix (item 17):** Replace `NOT IN` subquery with LEFT JOIN + IS NULL. See Decision section for full SQL.

**Acceptance criteria:**
- `brain/server.mjs` is under 250 lines
- Every extracted module has a single clear responsibility
- No function exceeds CC of 10
- `node brain/server.mjs` starts without errors (both stdio and http modes)
- `node brain/server.mjs http` serves REST API, static files, and MCP transport
- Consolidation runs with 1 SQL query for similarity computation (no per-pair queries)
- Purge uses LEFT JOIN instead of NOT IN
- All existing MCP tools and REST endpoints behave identically

**Estimated complexity:** High (1330 lines refactored into 10 files, algorithm changes)

### Step 6: Comprehensive Test Suite (Batch 6)

**Files to create/modify:**
- `tests/hooks/quality-gate.bats` -- NEW
- `tests/hooks/check-complexity.bats` -- NEW
- `tests/hooks/enforce-paths.bats` -- NEW
- `tests/hooks/enforce-sequencing.bats` -- NEW
- `tests/hooks/enforce-git.bats` -- NEW
- `tests/hooks/check-brain-usage.bats` -- NEW
- `tests/hooks/test_helper.bash` -- NEW (shared setup/teardown for bats tests)
- `tests/brain/config.test.mjs` -- NEW
- `tests/brain/db.test.mjs` -- NEW
- `tests/brain/embed.test.mjs` -- NEW
- `tests/brain/conflict.test.mjs` -- NEW
- `tests/brain/tools.test.mjs` -- NEW
- `tests/brain/rest-api.test.mjs` -- NEW
- `tests/brain/consolidation.test.mjs` -- NEW
- `tests/brain/ttl.test.mjs` -- NEW
- `tests/brain/integration.test.mjs` -- NEW (real DB via docker-compose)
- `brain/package.json` -- add `"test": "node --test tests/brain/*.test.mjs"`, `"test:integration": "node --test tests/brain/integration.test.mjs"`

**Test framework decisions:**
- Shell hooks: bats-core (standard shell testing framework, `brew install bats-core`)
- Node modules: built-in `node:test` + `node:assert` (no external test framework dependency)
- Mocking: `node:test` mock facilities for DB pool, fetch (embeddings/LLM)
- Integration tests: real PostgreSQL via docker-compose, separate test database
- Coverage: `node --test --experimental-test-coverage` (built-in, Node 20+) or c8 for older Node

**Acceptance criteria:**
- Every hook has a bats test file with valid input, invalid input, jq missing, and edge case tests
- Every brain module has a unit test file with mocked dependencies
- Integration tests run against a real PostgreSQL instance
- Coverage report shows 80%+ line coverage
- No function exceeds CC of 10 (verified by complexity tooling)

**Estimated complexity:** High (30+ test files, comprehensive coverage)

## Comprehensive Test Specification

### Step 1 Tests: Security and Enforcement Hardening

| ID | Category | Description |
|----|----------|-------------|
| T-0003-001 | Security | quality-gate.sh: verify no eval() in the file (grep confirms removal) |
| T-0003-002 | Security | check-complexity.sh: verify no eval() in the file |
| T-0003-003 | Happy | quality-gate.sh: with jq installed, TEST_COMMAND set, and source changes present, runs the test command and exits 0 on success |
| T-0003-004 | Happy | quality-gate.sh: with no source changes, exits 0 without running tests |
| T-0003-005 | Failure | quality-gate.sh: with jq missing, exits 2 with error message containing "jq" |
| T-0003-006 | Failure | quality-gate.sh: test command fails, exits 2 with "BLOCKED" message |
| T-0003-007 | Boundary | quality-gate.sh: ATELIER_STOP_HOOK_ACTIVE=1, exits 0 (loop guard) |
| T-0003-008 | Boundary | quality-gate.sh: TEST_COMMAND is empty string, exits 0 |
| T-0003-009 | Boundary | quality-gate.sh: TEST_COMMAND is "echo skip", exits 0 (placeholder skip) |
| T-0003-010 | Happy | check-complexity.sh: with jq installed, COMPLEXITY_COMMAND set, runs command with file path substituted |
| T-0003-011 | Failure | check-complexity.sh: with jq missing, exits 2 with error message |
| T-0003-012 | Boundary | check-complexity.sh: tool_name is "Read" (not Write/Edit/MultiEdit), exits 0 without running |
| T-0003-013 | Boundary | check-complexity.sh: file is .md (non-source), exits 0 without running |
| T-0003-014 | Happy | enforce-paths.sh: cal writing to docs/architecture/foo.md, exits 0 |
| T-0003-015 | Failure | enforce-paths.sh: cal writing to src/main.js, exits 2 with BLOCKED |
| T-0003-016 | Security | enforce-paths.sh: path "/home/user/docs/architecture/evil" does NOT match "docs/architecture" because it's not anchored to start -- verify the fix works |
| T-0003-017 | Happy | enforce-paths.sh: colby writing to src/feature.js, exits 0 |
| T-0003-018 | Failure | enforce-paths.sh: colby writing to docs/guide/foo.md, exits 2 with BLOCKED |
| T-0003-019 | Failure | enforce-paths.sh: with jq missing, exits 2 |
| T-0003-020 | Happy | enforce-paths.sh: roz writing to tests/foo.test.js, exits 0 |
| T-0003-021 | Failure | enforce-paths.sh: roz writing to src/main.js, exits 2 |
| T-0003-022 | Happy | enforce-paths.sh: main thread writing to docs/pipeline/state.md, exits 0 |
| T-0003-023 | Failure | enforce-paths.sh: main thread writing to src/main.js, exits 2 |
| T-0003-024 | Boundary | enforce-paths.sh: unknown agent type writing any file, exits 2 |
| T-0003-025 | Happy | enforce-paths.sh: ellis writing to any file, exits 0 |
| T-0003-026 | Happy | enforce-paths.sh: agatha writing to docs/guide/foo.md, exits 0 |
| T-0003-027 | Failure | enforce-paths.sh: agatha writing to src/main.js, exits 2 |
| T-0003-028 | Security | enforce-paths.sh: word splitting in test_patterns does not cause unexpected pattern matching (test with pattern containing spaces) |
| T-0003-029 | Security | enforce-paths.sh: word splitting in colby_blocked_paths does not cause unexpected matching |
| T-0003-030 | Failure | enforce-sequencing.sh: with jq missing, exits 2 |
| T-0003-031 | Failure | enforce-git.sh: with jq missing, exits 2 |
| T-0003-032 | Failure | check-brain-usage.sh: with jq missing, exits 2 |
| T-0003-033 | Security | check-brain-usage.sh: word splitting in brain_required_agents loop does not cause false matches |

### Step 2 Tests: Missing Files and Documentation

| ID | Category | Description |
|----|----------|-------------|
| T-0003-034 | Happy | CLAUDE.md exists at project root |
| T-0003-035 | Happy | CLAUDE.md contains tech stack section |
| T-0003-036 | Happy | CLAUDE.md contains test commands section |
| T-0003-037 | Happy | CLAUDE.md contains source structure section |
| T-0003-038 | Happy | docs/architecture/README.md exists |
| T-0003-039 | Happy | docs/architecture/README.md lists ADR-0001, ADR-0002, ADR-0003 |
| T-0003-040 | Regression | default-persona.md and agent-system.md agree on Eva's loaded context (grep both files for "Always-Loaded Context" or equivalent, verify same list) |
| T-0003-041 | Regression | All references to installed file count use the number 34 (grep README.md, user-guide.md, technical-reference.md, SKILL.md for "\d+ files") |

### Step 3 Tests: Enforcement Reliability

| ID | Category | Description |
|----|----------|-------------|
| T-0003-042 | Happy | enforce-sequencing.sh: Ellis invocation with PIPELINE_STATUS JSON showing roz_qa=PASS, exits 0 |
| T-0003-043 | Failure | enforce-sequencing.sh: Ellis invocation with PIPELINE_STATUS JSON showing roz_qa=FAIL, exits 2 |
| T-0003-044 | Failure | enforce-sequencing.sh: Ellis invocation with no PIPELINE_STATUS marker, exits 2 |
| T-0003-045 | Failure | enforce-sequencing.sh: Ellis invocation with malformed JSON in PIPELINE_STATUS, exits 2 |
| T-0003-046 | Boundary | enforce-sequencing.sh: Agatha invocation during build phase (PIPELINE_STATUS shows phase=build), exits 2 |
| T-0003-047 | Happy | enforce-sequencing.sh: Agatha invocation during review phase, exits 0 |
| T-0003-048 | Happy | enforce-sequencing.sh: non-main-thread (agent_id set) invocations always exit 0 |
| T-0003-049 | Security | REST API: GET /api/config without Bearer token returns 401 (when ATELIER_BRAIN_API_TOKEN set) |
| T-0003-050 | Security | REST API: GET /api/config with wrong Bearer token returns 401 |
| T-0003-051 | Happy | REST API: GET /api/config with correct Bearer token returns 200 |
| T-0003-052 | Happy | REST API: GET /api/health without token returns 200 (health is public) |
| T-0003-053 | Security | REST API: PUT /api/config without token returns 401 |
| T-0003-054 | Security | REST API: CORS header is http://localhost:PORT, not * |
| T-0003-055 | Failure | docker-compose.yml: without ATELIER_BRAIN_DB_PASSWORD env var, docker compose config fails |
| T-0003-056 | Happy | docker-compose.yml: with ATELIER_BRAIN_DB_PASSWORD set, docker compose config succeeds |
| T-0003-057 | Regression | enforce-sequencing.sh: free-form text "roz passed QA" in pipeline-state.md does NOT satisfy the gate (verifies structured parsing, not grep) |

### Step 4 Tests: Agent Persona Cleanup

| ID | Category | Description |
|----|----------|-------------|
| T-0003-058 | Happy | All 9 agent files (cal, colby, roz, agatha, ellis, distillator, robert, sable, investigator) contain a "Pronouns:" line |
| T-0003-059 | Happy | colby.md contains "she/her" |
| T-0003-060 | Happy | enforcement-config.json brain_required_agents contains exactly: cal, colby, roz, agatha, sable, robert |
| T-0003-061 | Regression | enforcement-config.json brain_required_agents does NOT contain "distillator" |
| T-0003-062 | Happy | user-guide.md contains a "Troubleshooting" heading |
| T-0003-063 | Happy | user-guide.md troubleshooting covers jq installation |
| T-0003-064 | Happy | user-guide.md troubleshooting covers brain connection failures |

### Step 5 Tests: server.mjs Modularization and Performance

| ID | Category | Description |
|----|----------|-------------|
| T-0003-065 | Happy | config.mjs: resolveConfig() with valid project config file returns parsed config with _source="project" |
| T-0003-066 | Happy | config.mjs: resolveConfig() with env var DATABASE_URL returns config with _source="env" |
| T-0003-067 | Failure | config.mjs: resolveConfig() with missing env vars in config template returns null |
| T-0003-068 | Boundary | config.mjs: resolveConfig() with no config and no env vars returns null |
| T-0003-069 | Happy | config.mjs: resolveIdentity() with ATELIER_BRAIN_USER set returns that value |
| T-0003-070 | Happy | config.mjs: resolveIdentity() without env var falls back to git config |
| T-0003-071 | Boundary | config.mjs: resolveIdentity() with no env var and no git returns null |
| T-0003-072 | Happy | db.mjs: createPool() returns a pg.Pool instance |
| T-0003-073 | Happy | db.mjs: runMigrations() with fresh schema is idempotent (no errors) |
| T-0003-074 | Regression | db.mjs: runMigrations() adds captured_by column if missing |
| T-0003-075 | Regression | db.mjs: runMigrations() adds handoff enum values if missing |
| T-0003-076 | Happy | embed.mjs: getEmbedding() with valid API key returns 1536-dim array |
| T-0003-077 | Failure | embed.mjs: getEmbedding() with invalid API key throws Error |
| T-0003-078 | Error | embed.mjs: getEmbedding() with network failure throws Error |
| T-0003-079 | Happy | conflict.mjs: detectConflicts() with no similar thoughts returns { action: "store" } |
| T-0003-080 | Happy | conflict.mjs: detectConflicts() with similarity > 0.9 returns { action: "merge" } |
| T-0003-081 | Happy | conflict.mjs: detectConflicts() with similarity 0.7-0.9 and LLM returning DUPLICATE returns { action: "merge" } |
| T-0003-082 | Happy | conflict.mjs: detectConflicts() with similarity 0.7-0.9 and LLM returning CONTRADICTION (same scope) returns { action: "supersede" } |
| T-0003-083 | Happy | conflict.mjs: detectConflicts() with similarity 0.7-0.9 and LLM returning CONTRADICTION (different scope) returns { action: "conflict" } |
| T-0003-084 | Failure | conflict.mjs: detectConflicts() with LLM failure returns { action: "store", warning: "..." } |
| T-0003-085 | Boundary | conflict.mjs: detectConflicts() with conflict_detection_enabled=false returns { action: "store" } |
| T-0003-086 | Happy | conflict.mjs: getBrainConfig() caches result for 10 seconds |
| T-0003-087 | Happy | tools.mjs: agent_capture with valid params inserts thought and returns thought_id |
| T-0003-088 | Failure | tools.mjs: agent_capture with invalid thought_type returns validation error |
| T-0003-089 | Happy | tools.mjs: agent_capture with supersedes_id creates relation and invalidates target |
| T-0003-090 | Happy | tools.mjs: agent_search with valid query returns scored results |
| T-0003-091 | Boundary | tools.mjs: agent_search with no matches returns empty results array |
| T-0003-092 | Happy | tools.mjs: agent_search updates last_accessed_at on returned thoughts |
| T-0003-093 | Happy | tools.mjs: atelier_browse with filters returns paginated results |
| T-0003-094 | Happy | tools.mjs: atelier_stats returns brain_enabled, counts by type/status/agent |
| T-0003-095 | Happy | tools.mjs: atelier_relation creates typed relation between thoughts |
| T-0003-096 | Failure | tools.mjs: atelier_relation with self-referential IDs returns error |
| T-0003-097 | Failure | tools.mjs: atelier_relation with cycle in supersedes chain returns error |
| T-0003-098 | Happy | tools.mjs: atelier_relation with supersedes auto-invalidates target |
| T-0003-099 | Happy | tools.mjs: atelier_trace follows backward chain correctly |
| T-0003-100 | Happy | tools.mjs: atelier_trace follows forward chain correctly |
| T-0003-101 | Boundary | tools.mjs: atelier_trace with max_depth=0 returns only root thought |
| T-0003-102 | Failure | tools.mjs: atelier_trace with nonexistent thought_id returns error |
| T-0003-103 | Happy | rest-api.mjs: GET /api/health returns connected status |
| T-0003-104 | Happy | rest-api.mjs: GET /api/config returns brain config |
| T-0003-105 | Happy | rest-api.mjs: PUT /api/config updates allowed fields |
| T-0003-106 | Failure | rest-api.mjs: PUT /api/config with invalid threshold (>1) returns 400 |
| T-0003-107 | Failure | rest-api.mjs: PUT /api/config with no valid fields returns 400 |
| T-0003-108 | Happy | rest-api.mjs: GET /api/thought-types returns all types |
| T-0003-109 | Happy | rest-api.mjs: PUT /api/thought-types/:type updates TTL and importance |
| T-0003-110 | Failure | rest-api.mjs: PUT /api/thought-types/invalid returns 404 |
| T-0003-111 | Happy | rest-api.mjs: POST /api/purge-expired deletes expired thoughts and orphan relations |
| T-0003-112 | Happy | rest-api.mjs: GET /api/stats returns breakdown by type, status, agent |
| T-0003-113 | Happy | consolidation.mjs: runConsolidation() with enough similar thoughts creates reflection |
| T-0003-114 | Boundary | consolidation.mjs: runConsolidation() with fewer than min_thoughts skips |
| T-0003-115 | Boundary | consolidation.mjs: runConsolidation() with brain_enabled=false skips |
| T-0003-116 | Happy | consolidation.mjs: clustering uses single SQL query (no per-pair queries) |
| T-0003-117 | Happy | consolidation.mjs: reflection importance = max(cluster) + 0.05, capped at 1.0 |
| T-0003-118 | Failure | consolidation.mjs: LLM synthesis failure skips cluster, continues to next |
| T-0003-119 | Happy | ttl.mjs: runTTLEnforcement() expires thoughts past their type's TTL |
| T-0003-120 | Boundary | ttl.mjs: runTTLEnforcement() does not expire thoughts with NULL TTL (decisions, preferences) |
| T-0003-121 | Happy | static.mjs: handleStaticFile() serves /ui/index.html with correct content type |
| T-0003-122 | Failure | static.mjs: handleStaticFile() rejects path traversal attempts (../../../etc/passwd) |
| T-0003-123 | Boundary | static.mjs: handleStaticFile() returns 404 for unknown extensions |
| T-0003-124 | Happy | server.mjs: entry point starts in stdio mode by default |
| T-0003-125 | Happy | server.mjs: entry point starts in http mode with "http" argument |
| T-0003-126 | Regression | purge endpoint uses LEFT JOIN instead of NOT IN |

### Step 6 Tests: Integration (Real DB)

| ID | Category | Description |
|----|----------|-------------|
| T-0003-127 | Integration | Full agent_capture -> agent_search round-trip: capture a thought, search by content, verify it appears in results |
| T-0003-128 | Integration | Conflict detection round-trip: capture two similar decisions, verify merge or conflict action |
| T-0003-129 | Integration | Supersession chain: capture thought A, capture thought B that supersedes A, verify A is status=superseded |
| T-0003-130 | Integration | Consolidation round-trip: insert 5+ similar thoughts, trigger consolidation, verify reflection created with synthesized_from relations |
| T-0003-131 | Integration | TTL enforcement: insert thought with type having 1-day TTL, backdate created_at, trigger TTL, verify status=expired |
| T-0003-132 | Integration | Purge round-trip: create expired thoughts, purge, verify count reduced |
| T-0003-133 | Integration | REST API end-to-end: start HTTP server, GET /api/health, verify JSON response |
| T-0003-134 | Integration | REST API auth end-to-end: start HTTP server with ATELIER_BRAIN_API_TOKEN, verify 401 without token, 200 with token |
| T-0003-135 | Integration | atelier_trace traversal: create chain A -> B -> C via supersedes, trace from C backward, verify complete chain |
| T-0003-136 | Integration | Three-axis scoring: insert thoughts with varying recency/importance, search, verify combined_score ordering matches expected |
| T-0003-137 | Concurrency | Concurrent agent_capture: 10 parallel captures, verify all stored without deadlock or lost writes |
| T-0003-138 | Security | REST API with auth: verify all mutating endpoints (PUT, POST, DELETE) require token |

### Contract Boundaries

| Producer | Consumer | Expected Shape |
|----------|----------|----------------|
| `config.mjs:resolveConfig()` | `db.mjs`, `server.mjs` | `{ database_url: string, openrouter_api_key?: string, brain_name?: string, _source: "project"\|"personal"\|"env" } \| null` |
| `config.mjs:resolveIdentity()` | `tools.mjs` (CAPTURED_BY) | `string \| null` |
| `db.mjs:createPool(url)` | all modules needing DB | `pg.Pool` instance with pgvector types registered |
| `embed.mjs:getEmbedding(text, key)` | `tools.mjs`, `consolidation.mjs` | `number[]` (length 1536) |
| `conflict.mjs:detectConflicts(...)` | `tools.mjs` (agent_capture) | `{ action: "store"\|"merge"\|"supersede"\|"conflict", existingId?: string, similarity?: number, classification?: object, warning?: string, conflictFlag?: boolean, candidateId?: string, relatedId?: string }` |
| `conflict.mjs:getBrainConfig(client?)` | `tools.mjs`, `rest-api.mjs`, `consolidation.mjs`, `ttl.mjs` | `brain_config` row object (all columns from brain_config table) |
| `tools.mjs:registerTools(srv, pool, cfg)` | `server.mjs` | `void` (side effect: registers 6 MCP tools on srv) |
| `rest-api.mjs:createRestHandler(pool, cfg)` | `server.mjs` | `(req, res) => Promise<boolean>` |
| `consolidation.mjs:startConsolidationTimer(pool)` | `server.mjs` | `void` (side effect: starts interval timer) |
| `ttl.mjs:startTTLTimer(pool)` | `server.mjs` | `void` (side effect: starts interval timer) |
| Pipeline state marker | `enforce-sequencing.sh` | `<!-- PIPELINE_STATUS: {"roz_qa":"PASS"\|"FAIL"\|"PENDING","phase":"...","timestamp":"..."} -->` |

## Data Sensitivity

| Method/Endpoint | Classification | Notes |
|-----------------|---------------|-------|
| `GET /api/health` | public-safe | No sensitive data; thought count + connection status |
| `GET /api/config` | auth-only | Exposes DB config, scope, thresholds |
| `PUT /api/config` | auth-only | Mutates brain configuration |
| `GET /api/thought-types` | auth-only | Exposes lifecycle config |
| `PUT /api/thought-types/:type` | auth-only | Mutates lifecycle config |
| `POST /api/purge-expired` | auth-only | Destructive: deletes data |
| `GET /api/stats` | auth-only | Exposes usage patterns |
| `agent_capture` (MCP) | transport-secured | MCP tools secured by transport (stdio = local only, HTTP = session-based) |
| `agent_search` (MCP) | transport-secured | Returns thought content including potential decisions/preferences |

## State Machine: Pipeline Status (enforce-sequencing.sh)

| From State | To State | Trigger | Who |
|------------|----------|---------|-----|
| (none) | `roz_qa: PENDING` | Pipeline starts, Colby begins build | Eva |
| `roz_qa: PENDING` | `roz_qa: PASS` | Roz QA passes | Eva |
| `roz_qa: PENDING` | `roz_qa: FAIL` | Roz QA fails | Eva |
| `roz_qa: FAIL` | `roz_qa: PENDING` | Colby fixes, resubmits | Eva |
| `roz_qa: PASS` | (consumed) | Ellis invoked, commits | Eva |

**Stuck states:** `roz_qa: FAIL` with no Colby fix queued. Recovery: Eva re-invokes Colby or user manually resolves.

**Terminal states:** `roz_qa: PASS` consumed by Ellis commit. Pipeline state file is reset at next pipeline start.

## Notes for Colby

1. **Batch ordering matters.** Batch 1 (security) is independent. Batch 2 (docs) is independent. Batch 3 (enforcement) depends on batch 1 (jq hard failure must land first). Batch 4 (personas) is independent. Batch 5 (modularization) should incorporate batch 3's auth middleware during the split. Batch 6 (tests) must come after batch 5 (tests target the modularized code).

2. **eval() replacement in quality-gate.sh.** `eval "$TEST_COMMAND"` on line 52 is the command injection vector. Replace with `bash -c "$TEST_COMMAND"`. This still allows compound commands (pipelines, redirects) without eval's full expansion. The test command comes from enforcement-config.json which the user controls, but defense-in-depth matters.

3. **eval() replacement in check-complexity.sh.** Same pattern on line 39. `CMD=$(echo "$COMPLEXITY_COMMAND" | sed "s|{file}|$FILE_PATH|g")` followed by `eval "$CMD"`. Replace with `bash -c "$CMD"`. Note: `$FILE_PATH` comes from jq parsing of hook input -- it is attacker-controlled (a malicious agent could craft a file path with shell metacharacters). The sed substitution should also be hardened: if FILE_PATH contains `|`, `;`, or backticks, they would execute. Consider using an environment variable instead: `FILE_PATH="$FILE_PATH" bash -c "$COMPLEXITY_COMMAND_WITH_ENV_REF"` where the config uses `$FILE_PATH` instead of `{file}`.

4. **Word splitting fix pattern.** Replace:
   ```bash
   PATTERNS=$(jq -r '.array[]' "$CONFIG")
   for item in $PATTERNS; do
   ```
   With:
   ```bash
   while IFS= read -r item; do
     # ... use "$item"
   done < <(jq -r '.array[]' "$CONFIG" 2>/dev/null)
   ```

5. **Path anchoring in enforce-paths.sh.** The `path_matches` function uses `*"$prefix"*` which matches the prefix anywhere in the path. Change to `"$prefix"*` to anchor to the start. This prevents `/home/user/docs/architecture/evil.md` from matching the `docs/architecture` prefix when the file is outside the project.

6. **Structured state parsing.** The `PIPELINE_STATUS` HTML comment marker must be written by Eva in `docs/pipeline/pipeline-state.md`. Eva's state-writing code is in the main thread -- Colby does not modify Eva's behavior. Colby's job is to make enforce-sequencing.sh parse the marker. Eva's state-writing must be updated separately (this is a docs/pipeline file, so Eva can write it). Flag this in your DoD as a dependency.

7. **server.mjs modularization.** Do not change the public API (MCP tools, REST endpoints, CLI arguments). The `brain/package.json` "start" script must still work: `node server.mjs`. Create `brain/lib/` directory for extracted modules. Use named exports, not default exports.

8. **Docker password removal.** The bash parameter expansion `${VAR:?message}` causes the shell to exit with the message if VAR is unset or empty. This is a docker-compose.yml feature (it evaluates at `docker compose up` time). Test with `docker compose config` to verify it fails correctly.

9. **REST API auth.** The Settings UI (`brain/ui/settings.js`) makes fetch calls to `/api/*`. Since it is served from the same origin (same HTTP server on the same port), it does not need CORS headers. The CORS restriction to localhost affects only cross-origin requests (e.g., a different app trying to hit the API).

10. **Dual tree awareness.** Files in `source/claude/hooks/` are templates. Files in `.claude/hooks/` are installed copies. Both must be updated. The canonical source is `source/claude/hooks/` -- the installed copies in `.claude/hooks/` are what actually runs. Same for `source/shared/agents/` and `.claude/agents/`, `source/rules/` and `.claude/rules/`.

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Remove eval() from hooks | Done | Step 1, T-0003-001, T-0003-002 |
| 2 | Fix word splitting | Done | Step 1, T-0003-028, T-0003-029, T-0003-033 |
| 3 | Make jq hard failure | Done | Step 1, T-0003-005, T-0003-011, T-0003-019, T-0003-030, T-0003-031, T-0003-032 |
| 4 | Fix substring path matching | Done | Step 1, T-0003-016 |
| 5 | Create CLAUDE.md | Done | Step 2, T-0003-034 through T-0003-037 |
| 6 | Create ADR index | Done | Step 2, T-0003-038, T-0003-039 |
| 7 | Fix Eva context contradiction | Done | Step 2, T-0003-040 |
| 8 | Fix file count | Done | Step 2, T-0003-041 |
| 9 | Replace grep-based gate | Done | Step 3, T-0003-042 through T-0003-048, T-0003-057 |
| 10 | Add REST API auth | Done | Step 3, T-0003-049 through T-0003-054 |
| 11 | Remove default password | Done | Step 3, T-0003-055, T-0003-056 |
| 12 | Add pronouns | Done | Step 4, T-0003-058, T-0003-059 |
| 13 | Remove distillator from brain_required_agents | Done | Step 4, T-0003-060, T-0003-061 |
| 14 | Add troubleshooting section | Done | Step 4, T-0003-062 through T-0003-064 |
| 15 | Split server.mjs | Done | Step 5, T-0003-124, T-0003-125 |
| 16 | Fix O(n^2) consolidation | Done | Step 5, T-0003-116 |
| 17 | Fix NOT IN purge | Done | Step 5, T-0003-126 |
| 18 | Comprehensive test suite | Done | Step 6, T-0003-127 through T-0003-138 |

**Grep check:** `TODO/FIXME/HACK/XXX` in this file -> 0
**Template:** All sections filled -- no TBD, no placeholders
