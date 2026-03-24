# ADR-0001: Atelier Brain — Persistent Institutional Memory for Pipeline Agents

## DoR: Requirements Extracted

| # | Requirement | Source | Retro Risk |
|---|---|---|---|
| R1 | Thoughts stored with vector embeddings for semantic search | Feature Spec US-1 | — |
| R2 | Typed relations between thoughts (supersedes, triggered_by, evolves_from, contradicts, supports, synthesized_from) | Feature Spec US-2 | — |
| R3 | Three-axis scoring: recency + importance + relevance | Feature Spec US-1, Research decisions | — |
| R4 | Write-time conflict detection with tiered thresholds (>0.9 dup, 0.7-0.9 candidate, <0.7 novel) | Feature Spec US-3 | — |
| R5 | LLM classification for conflict candidates (contradiction/complement/supersession) | Feature Spec US-3 | — |
| R6 | Same-team contradiction: newest wins. Cross-team: flag for human | Feature Spec US-3 | — |
| R7 | TTL per thought type, configurable via lookup table | Feature Spec US-4 | — |
| R8 | Background consolidation timer (default 30 min), produces reflection-type thoughts | Feature Spec US-5 | — |
| R9 | Hierarchical scoping via ltree, single-column, multi-membership via ltree[] | Feature Spec US-6 | — |
| R10 | Brain is opt-in. Config flag (`brain: enabled/disabled`) + health check (two-gate) | Feature Spec US-7 | — |
| R11 | Pipeline works identically without brain — every gate has baseline + enhanced variant | Feature Spec US-7 | — |
| R12 | Schema-enforced captures — required enums for thought_type, source_agent, source_phase | Feature Spec, Agent Operating Model | — |
| R13 | 7 agents get read+write, 3 get nothing (Poirot, Distillator, Ellis) | Feature Spec, Agent Operating Model | — |
| R14 | Eva captures gate-triggered events + creates cross-agent relations | Feature Spec, Agent Operating Model | — |
| R15 | Agents search mid-task for emergent questions (not just pre-loaded context) | Feature Spec, Agent Operating Model | — |
| R16 | `invalidated_at` timestamp for soft deprecation (Option D) | Design decisions | — |
| R17 | Settings UI: single page, status bar, lifecycle table, consolidation config, conflict config, purge | UX Spec | — |
| R18 | Fork from mybrain — separate codebase, embedded in atelier-pipeline plugin | Design decisions | — |
| R19 | Consolidation service runs inside brain MCP server, not separate process | Design decisions | — |
| R20 | 1536-dimension embeddings via OpenRouter text-embedding-3-small | Design decisions, embedding research | — |
| R21 | Three deployment tiers: solo personal, team isolated, team shared | Feature Spec US-8, US-9, US-10 | — |
| R22 | Config priority: project-level (`.claude/brain-config.json`) > user-level (`${CLAUDE_PLUGIN_DATA}/brain-config.json`) > none | Feature Spec US-10 | — |
| R23 | Shared config: connection details committed to repo, secrets via env var placeholders | Feature Spec US-9 | — |
| R24 | Plugin auto-registers brain MCP server via `.mcp.json`, inert until config exists | Plugin system, Feature Spec US-7 | — |
| R25 | `SessionStart` hook checks config existence and brain health each session | Plugin system, Feature Spec US-7 | — |
| R26 | Docker deployment option: `docker-compose.yml` with PostgreSQL 17 + pgvector + ltree, schema on first boot | Feature Spec US-8 | — |

## Status

Proposed

## Context

Atelier-pipeline agents lose all reasoning context between sessions. Research quantifies the impact: 42% decline in task success, 216% increase in human interventions, 487% increase in inter-agent conflicts without persistent context (arXiv:2601.04170). The existing recovery mechanism (`context-brief.md`, `pipeline-state.md`) captures session snapshots but loses the reasoning trail — the "why" behind decisions.

mybrain exists as a working MCP server (208 lines, single `server.mjs`) with PostgreSQL + pgvector + OpenRouter. It provides 4 tools: `capture_thought`, `search_thoughts`, `browse_thoughts`, `brain_stats`. It uses cosine similarity over 1536-dimensional embeddings with a single `thoughts` table. It works, but it has no relations, no scoring formula, no conflict detection, no consolidation, no scoping, and no schema enforcement.

The feature spec defines 10 user stories (US-1 through US-10). The UX spec defines a single-page settings interface. The agent operating model defines per-agent brain access patterns.

## Spec Challenge

**The riskiest assumption in the feature spec:** "Agents search mid-task for emergent questions" (R15). This assumes LLM agents will usefully self-direct brain searches during complex tasks. If agents search poorly (wrong queries, too broad, too narrow), the brain returns irrelevant context that wastes tokens or misleads. The mitigation — "disk always wins" — handles wrong results but not useless results. **Are we confident agents will search well enough to justify direct access?** The alternative is Eva-only retrieval with pre-loaded context, which was rejected in the design discussion. Monitoring search relevance (Success Metric: top-3 >80%) will validate or invalidate this assumption.

## Decision

Fork mybrain into an atelier-pipeline brain module (`brain/` directory within the plugin). Extend the schema to Option D (thoughts + thought_relations + thought_type_config + ltree scoping + invalidated_at). Rewrite the MCP tools with schema enforcement and three-axis scoring. Add conflict detection at write time and consolidation on a background timer. Integrate into the pipeline via two-gate detection and dual-mode gates.

## Alternatives Considered

| Alternative | Pros | Cons | Reason Rejected |
|---|---|---|---|
| **Enhance mybrain in-place** | No fork, single codebase | mybrain serves personal use (freeform). Pipeline brain needs schema enforcement. Different concerns. | Pollutes personal tool with pipeline opinions. |
| **File-based memory (enhanced context-brief.md)** | Zero infrastructure, works everywhere | No semantic search, no relations, no scoring, no conflict detection. Just a bigger flat file. | Doesn't solve the core problem — reasoning trail is still lost. |
| **Full Graphiti (Option C — bitemporal)** | Research gold standard, point-in-time reconstruction | Three tables, bitemporal queries, complex schema. Solves "what was true on March 5" which agents don't need. | Over-engineered for agent use case. Decision trees (Option D) answer the actual question: "how did we get here?" |
| **Eva-only brain access** | Clean metadata, consistent captures, brain-agnostic agents | Eva can't predict emergent questions. Agents discover what they need mid-task. Pre-loading doesn't cover it. | Creates bottleneck. Agents need direct read access for mid-task searches. |
| **Separate graph database (Neo4j, etc.)** | Purpose-built for graph traversal | New infrastructure dependency. PostgreSQL recursive CTEs handle the relation traversal we need. | PostgreSQL already present, ltree + recursive CTEs are sufficient for our graph depth (typically <20 hops). |

## Consequences

**Positive:**
- Agents gain cross-session institutional memory
- Decision evolution is traceable through the relation graph
- Cross-team conflicts surface at capture time
- Stale knowledge decays naturally via TTL
- Consolidation synthesizes patterns from raw observations
- Pipeline works without brain — purely additive

**Negative:**
- Every capture adds latency (embedding generation + similarity search + optional LLM classification)
- Brain MCP server is a new infrastructure dependency (PostgreSQL must be running)
- Agent prompts grow by ~200-400 tokens for brain interaction guidance
- Consolidation quality depends on LLM synthesis — plausible-but-wrong reflections are possible
- Six MCP tools to maintain instead of four

**Neutral:**
- mybrain personal brain stays independent — no coupling
- Embedding cost is negligible at projected volume (~$3/year)

## Implementation Plan

### Step 1: Schema and Database Setup

Create `brain/schema.sql` with the full Option D schema.

**Files to create:**
- `brain/schema.sql`

**Schema:**

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS ltree;

-- Thought type enum
CREATE TYPE thought_type AS ENUM (
  'decision', 'preference', 'lesson', 'rejection',
  'drift', 'correction', 'insight', 'reflection'
);

-- Agent enum
CREATE TYPE source_agent AS ENUM (
  'eva', 'cal', 'robert', 'sable', 'colby',
  'roz', 'poirot', 'agatha', 'distillator', 'ellis'
);

-- Phase enum
CREATE TYPE source_phase AS ENUM (
  'design', 'build', 'qa', 'review', 'reconciliation', 'setup'
);

-- Thought status
CREATE TYPE thought_status AS ENUM (
  'active', 'superseded', 'invalidated', 'expired', 'conflicted'
);

-- Relation type
CREATE TYPE relation_type AS ENUM (
  'supersedes', 'triggered_by', 'evolves_from',
  'contradicts', 'supports', 'synthesized_from'
);

-- Thought type configuration (lookup table for TTL and defaults)
CREATE TABLE thought_type_config (
  thought_type thought_type PRIMARY KEY,
  default_ttl_days INTEGER,          -- NULL = never expires
  default_importance FLOAT NOT NULL DEFAULT 0.5,
  description TEXT
);

INSERT INTO thought_type_config VALUES
  ('decision',   NULL, 0.9,  'Architectural or product decisions'),
  ('preference',  NULL, 1.0,  'Human preferences and HALT resolutions'),
  ('lesson',      365,  0.7,  'Retro learnings and patterns'),
  ('rejection',   180,  0.5,  'Alternatives considered and discarded'),
  ('drift',       90,   0.8,  'Spec/UX drift findings'),
  ('correction',  90,   0.7,  'Fixes applied after drift detection'),
  ('insight',     180,  0.6,  'Mid-task discoveries'),
  ('reflection',  NULL, 0.85, 'Consolidation-generated synthesis');

-- Brain configuration (singleton)
CREATE TABLE brain_config (
  id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  brain_enabled BOOLEAN NOT NULL DEFAULT false,
  consolidation_interval_minutes INTEGER NOT NULL DEFAULT 30,
  consolidation_min_thoughts INTEGER NOT NULL DEFAULT 3,
  consolidation_max_thoughts INTEGER NOT NULL DEFAULT 20,
  conflict_detection_enabled BOOLEAN NOT NULL DEFAULT true,
  conflict_duplicate_threshold FLOAT NOT NULL DEFAULT 0.9,
  conflict_candidate_threshold FLOAT NOT NULL DEFAULT 0.7,
  conflict_llm_enabled BOOLEAN NOT NULL DEFAULT true,
  default_scope ltree DEFAULT 'default'
);

INSERT INTO brain_config DEFAULT VALUES;

-- Thoughts table (Option D)
CREATE TABLE thoughts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB DEFAULT '{}',
  thought_type thought_type NOT NULL,
  source_agent source_agent NOT NULL,
  source_phase source_phase NOT NULL,
  importance FLOAT NOT NULL CHECK (importance >= 0 AND importance <= 1),
  trigger_event TEXT,
  captured_by TEXT,
  status thought_status NOT NULL DEFAULT 'active',
  scope ltree[] DEFAULT ARRAY['default']::ltree[],
  invalidated_at TIMESTAMPTZ,
  last_accessed_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX thoughts_embedding_idx ON thoughts USING hnsw (embedding vector_cosine_ops);
CREATE INDEX thoughts_metadata_idx ON thoughts USING gin (metadata);
CREATE INDEX thoughts_scope_idx ON thoughts USING gist (scope);
CREATE INDEX thoughts_status_idx ON thoughts (status);
CREATE INDEX thoughts_type_idx ON thoughts (thought_type);
CREATE INDEX thoughts_created_idx ON thoughts (created_at DESC);
CREATE INDEX thoughts_agent_idx ON thoughts (source_agent);
CREATE INDEX thoughts_invalidated_idx ON thoughts (invalidated_at) WHERE invalidated_at IS NOT NULL;

-- Thought relations table
CREATE TABLE thought_relations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source_id UUID NOT NULL REFERENCES thoughts(id) ON DELETE CASCADE,
  target_id UUID NOT NULL REFERENCES thoughts(id) ON DELETE CASCADE,
  relation_type relation_type NOT NULL,
  context TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (source_id, target_id, relation_type)
);

CREATE INDEX relations_source_idx ON thought_relations (source_id);
CREATE INDEX relations_target_idx ON thought_relations (target_id);
CREATE INDEX relations_type_idx ON thought_relations (relation_type);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER thoughts_updated_at
  BEFORE UPDATE ON thoughts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

**Acceptance criteria:**
- Schema creates cleanly on fresh PostgreSQL 17 with pgvector and ltree extensions
- All enums match the feature spec's defined types
- `thought_type_config` seeded with default values matching design decisions
- `brain_config` singleton row created with defaults matching UX spec
- All indexes create without error

**Estimated complexity:** Low — DDL only, no application logic.

### Step 2: Three-Axis Scoring Function

Replace mybrain's `match_thoughts()` with a three-axis scoring function.

**Files to create/modify:**
- `brain/schema.sql` (append function)

**Function:**

```sql
CREATE OR REPLACE FUNCTION match_thoughts_scored(
  query_embedding vector(1536),
  similarity_threshold FLOAT DEFAULT 0.2,
  max_results INTEGER DEFAULT 10,
  metadata_filter JSONB DEFAULT '{}',
  scope_filter ltree DEFAULT NULL,
  include_invalidated BOOLEAN DEFAULT false
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  thought_type thought_type,
  source_agent source_agent,
  source_phase source_phase,
  importance FLOAT,
  status thought_status,
  scope ltree[],
  captured_by TEXT,
  created_at TIMESTAMPTZ,
  invalidated_at TIMESTAMPTZ,
  similarity FLOAT,
  recency_score FLOAT,
  combined_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    t.id,
    t.content,
    t.metadata,
    t.thought_type,
    t.source_agent,
    t.source_phase,
    t.importance,
    t.status,
    t.scope,
    t.created_at,
    t.invalidated_at,
    (1 - (t.embedding <=> query_embedding))::FLOAT AS similarity,
    POWER(0.995, EXTRACT(EPOCH FROM (now() - COALESCE(t.last_accessed_at, t.created_at))) / 3600)::FLOAT AS recency_score,
    (
      0.5 * POWER(0.995, EXTRACT(EPOCH FROM (now() - COALESCE(t.last_accessed_at, t.created_at))) / 3600) +
      2.0 * t.importance +
      3.0 * (1 - (t.embedding <=> query_embedding))
    )::FLOAT AS combined_score
  FROM thoughts t
  WHERE
    (1 - (t.embedding <=> query_embedding)) >= similarity_threshold
    AND (include_invalidated OR t.status = 'active')
    AND (metadata_filter = '{}' OR t.metadata @> metadata_filter)
    AND (scope_filter IS NULL OR t.scope @> ARRAY[scope_filter])
  ORDER BY combined_score DESC
  LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
```

**Acceptance criteria:**
- Function returns results ranked by combined score, not raw cosine similarity
- Recency decay is measurable: a thought accessed 1 hour ago scores higher than one accessed 1 week ago (all else equal)
- Importance weight is measurable: a 0.9 importance thought outranks a 0.5 importance thought at equal similarity and recency
- `include_invalidated = false` (default) excludes superseded/invalidated thoughts
- Scope filter narrows results to matching ltree paths
- `last_accessed_at` is updated on returned results (handled in application layer, not in function)

**Estimated complexity:** Medium — scoring formula is math, but testing the weighting balance requires real data.

### Step 3: Fork mybrain Server and Rewrite Tools

Fork `server.mjs` into `brain/server.mjs`. Rewrite the 4 existing tools with schema enforcement. Add 2 new tools.

**Files to create:**
- `brain/server.mjs`
- `brain/package.json`

**Tool 1: `agent_capture` (rewrite)**

Schema-enforced input:
```
content:       string (required)
thought_type:  enum (required)
source_agent:  enum (required)
source_phase:  enum (required)
importance:    float 0-1 (required)
trigger_event: string (optional)
supersedes_id: uuid (optional)
scope:         string[] (optional, ltree paths)
metadata:      object (optional)
```

Logic:
1. Validate enums against schema (reject malformed)
2. Generate embedding via OpenRouter
3. If `thought_type IN ('decision', 'preference')` AND conflict detection enabled:
   a. Run similarity search against active decisions in overlapping scopes
   b. Tiered classification:
      - similarity > `brain_config.conflict_duplicate_threshold` → merge (update existing, return merged ID)
      - similarity > `brain_config.conflict_candidate_threshold` → if LLM enabled, classify via OpenRouter; else flag as candidate
      - LLM returns `contradiction` + same scope → newest wins, invalidate old, create `supersedes` relation
      - LLM returns `contradiction` + cross-scope → store both as `status: 'conflicted'`, return conflict flag
      - LLM returns `complement` or `supersession` → store normally, create appropriate relation
4. If `supersedes_id` provided → atomic transaction: insert thought + create `supersedes` relation + set `invalidated_at` on target
5. Insert thought with all fields
6. Return: thought ID, created_at, conflict_flag (if any), related_thought_ids (if any)

**Tool 2: `agent_search` (rewrite)**

Uses `match_thoughts_scored()` function. After returning results, updates `last_accessed_at` on all returned thought IDs. Accepts `scope` and `include_invalidated` parameters.

**Tool 3: `atelier_browse` (rewrite)**

Enhanced filtering: by `status`, `thought_type`, `source_agent`, scope. Pagination unchanged.

**Tool 4: `atelier_stats` (rewrite)**

Enhanced: `brain_enabled` flag, counts by type, by status, by agent. Last consolidation timestamp. Active vs expired vs invalidated counts.

**Tool 5: `atelier_relation` (new)**

Input: `source_id`, `target_id`, `relation_type` (enum), `context` (optional text).
If type is `supersedes` → atomically set `invalidated_at` and `status: 'superseded'` on target.

**Tool 6: `atelier_trace` (new)**

Input: `thought_id`, `direction` (backward | forward | both), `max_depth` (default 10).
Recursive CTE traversal of `thought_relations`. Returns ordered chain with relation types, context, and thought content.

```sql
WITH RECURSIVE chain AS (
  SELECT t.*, 0 AS depth, NULL::relation_type AS via_relation, NULL::text AS via_context
  FROM thoughts t WHERE t.id = $1
  UNION ALL
  SELECT t.*, chain.depth + 1, r.relation_type, r.context
  FROM thought_relations r
  JOIN thoughts t ON t.id = CASE WHEN $2 = 'backward' THEN r.target_id ELSE r.source_id END
  JOIN chain ON chain.id = CASE WHEN $2 = 'backward' THEN r.source_id ELSE r.target_id END
  WHERE chain.depth < $3
)
SELECT * FROM chain ORDER BY depth;
```

**Acceptance criteria:**
- `agent_capture` rejects input missing required enum fields
- `agent_capture` with `supersedes_id` atomically creates relation and invalidates target
- Conflict detection only fires for decision/preference types
- Duplicate merge combines metadata, keeps higher importance
- `agent_search` returns `combined_score` and updates `last_accessed_at`
- `atelier_relation` with type `supersedes` sets `invalidated_at` on target
- `atelier_trace` backward from any thought returns the full decision tree
- All 6 tools register and respond via stdio transport

**Estimated complexity:** High — conflict detection LLM integration, atomic transactions, relation management.

### Step 4: TTL Enforcement Timer

Background timer inside the brain MCP server that checks for expired thoughts.

**Files to modify:**
- `brain/server.mjs`

**Logic:**
1. On server startup, start `setInterval` (configurable, default 60 minutes, read from `brain_config`)
2. Each tick:
   ```sql
   UPDATE thoughts t
   SET status = 'expired', invalidated_at = now()
   FROM thought_type_config ttc
   WHERE t.thought_type = ttc.thought_type
     AND ttc.default_ttl_days IS NOT NULL
     AND t.status = 'active'
     AND t.created_at < now() - (ttc.default_ttl_days || ' days')::interval;
   ```
3. Log count of expired thoughts

**Acceptance criteria:**
- Timer reads interval from `brain_config` on startup
- Expired thoughts get `status: 'expired'` and `invalidated_at` set
- Thoughts with NULL TTL (decisions, preferences, reflections) are never expired
- Timer does not block MCP tool responses (async, non-blocking)
- If no thoughts to expire, timer completes silently

**Estimated complexity:** Low — single UPDATE query on a timer.

### Step 5: Consolidation Engine

Background timer that synthesizes clusters of unconsolidated thoughts into reflection-type thoughts.

**Files to modify:**
- `brain/server.mjs`

**Logic:**
1. On server startup, start `setInterval` (read `consolidation_interval_minutes` from `brain_config`)
2. Each tick:
   a. Query active, non-reflection thoughts that haven't been consolidated (no `synthesized_from` relation pointing to them)
   b. If count < `consolidation_min_thoughts`, skip
   c. Cluster by embedding similarity (simple: take top N by recency, check pairwise similarity > 0.6)
   d. For each cluster of 3+ thoughts:
      - Send to OpenRouter LLM: "Synthesize these observations into a single higher-level insight. Preserve specific details, decisions, and reasoning. Do not generalize away the useful specifics."
      - Create reflection-type thought with importance = max(cluster importances) + 0.05 (capped at 1.0)
      - Create `synthesized_from` relations from reflection to each source thought
      - Source thoughts remain `status: 'active'` (Stanford model)
3. Log count of reflections created

**Acceptance criteria:**
- Timer reads config from `brain_config`
- Reflections have higher importance than their sources (outrank in search)
- Source thoughts remain active after consolidation
- `synthesized_from` relations link reflection to all source thoughts
- Reflection content is specific and useful (not generic summaries)
- Consolidation handles partial failures gracefully (one bad cluster doesn't stop the pass)
- Min/max thoughts per pass respected

**Estimated complexity:** High — LLM call, clustering logic, relation creation, error handling.

### Step 6: Settings API

REST endpoints for the settings UI to read and write brain configuration.

**Files to modify:**
- `brain/server.mjs`

**Endpoints (added to HTTP mode):**

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Connection status, thought count, last consolidation, next consolidation |
| GET | `/api/config` | Read `brain_config` singleton |
| PUT | `/api/config` | Update `brain_config` fields |
| GET | `/api/thought-types` | Read all rows from `thought_type_config` |
| PUT | `/api/thought-types/:type` | Update TTL and importance for a thought type |
| POST | `/api/purge-expired` | Delete expired thoughts and orphaned relations |
| GET | `/api/stats` | Extended stats: by type, by status, by agent |

**Acceptance criteria:**
- All endpoints return JSON
- `/api/health` responds in <100ms (simple query)
- `/api/health` returns `next_consolidation_at` computed as `last_consolidation + consolidation_interval_minutes`
- `/api/config` PUT validates field types before writing
- `/api/thought-types/:type` rejects invalid type names
- `/api/purge-expired` returns count of deleted thoughts and count of orphaned relations cleaned
- All endpoints work alongside MCP transport (shared HTTP server)

**Estimated complexity:** Medium — thin CRUD layer, but needs to coexist with MCP transport routing.

### Step 7: Settings UI

Single-page settings interface per Sable's UX spec.

**Files to create:**
- `brain/ui/index.html`
- `brain/ui/settings.js`
- `brain/ui/settings.css`

**Implementation maps directly to UX spec:**
- Status bar → `GET /api/health` polled every 30s
- Enable/disable toggle → `PUT /api/config` { brain_enabled } — writes to `brain_config.brain_enabled`. Default `false` (opt-in per R10). `/brain-setup` sets to `true`. `atelier_stats` reports this flag. Eva's health check reads it.
- Connection section → `GET /api/health` + scope from `GET /api/config`
- Thought lifecycle table → `GET /api/thought-types` + inline edit → `PUT /api/thought-types/:type`
- Consolidation section → `GET /api/config` + edit → `PUT /api/config`
- Conflict detection section → `GET /api/config` + toggles/inputs → `PUT /api/config`
- Danger zone → `POST /api/purge-expired`

**All seven UX states implemented:**
- Empty (not configured): no connection, dimmed sections, helper text "Run /brain-setup..."
- Loading (connecting): pulse animation, disabled inputs
- Populated (normal operation): full layout, all sections editable
- Shared config, missing env vars: config found message, env var guidance, enable toggle disabled
- Shared config, connected: "(shared)" badge on DB URL and scope (read-only), "(local override)" label on any setting differing from project defaults, personal overrides write to `brain-overrides.json`
- Error (brain unreachable): amber status with "pipeline will use baseline mode", sections still editable
- Overflow: N/A (scrolls naturally)

**Acceptance criteria:**
- All interactions match UX spec (toggle, inline edit, test connection, purge with confirmation)
- Keyboard navigation covers all interactive elements
- Screen reader: `role="status"` on status bar, `aria-live="polite"`, fieldset/legend on sections
- 4.5:1 contrast on all text
- Touch targets ≥44px on mobile
- Responsive: desktop, tablet, mobile per UX spec
- No external dependencies (vanilla HTML/CSS/JS — developer tool, not a consumer app)

**Estimated complexity:** Medium — straightforward CRUD UI, but accessibility and responsive requirements add detail.

### Step 8: Pipeline Integration — Brain Detection

Add two-gate brain detection to atelier-pipeline.

**Files to modify:**
- `templates/rules/agent-system.md`
- `templates/rules/default-persona.md`

**Changes:**
- Eva behavior on pipeline start: call `atelier_stats` as health check. This checks two things: (1) brain MCP server is running (config file exists, server started), and (2) `brain_enabled` flag is `true` in `brain_config` table. Both must be true for brain to be active.
- Set `brain_available: true | false` in pipeline state
- Document dual-mode gate behavior (baseline vs enhanced)

**Two-gate detection:**
- Gate 1 (infrastructure): Brain MCP server running? If no config file exists, server never started — no `atelier_stats` tool available. Eva detects tool absence = brain not configured.
- Gate 2 (runtime): `atelier_stats` returns `brain_enabled: true`? If false, brain is installed but user disabled it via Settings UI toggle.
- Both gates pass → `brain_available: true`

**Acceptance criteria:**
- Brain MCP server not running (no config) → `atelier_stats` tool unavailable, Eva skips brain interaction
- Brain MCP server running + `brain_enabled: false` → `atelier_stats` returns disabled flag, `brain_available: false`
- Brain MCP server running + `brain_enabled: true` + responding → `brain_available: true`
- Brain MCP server running + `brain_enabled: true` + server down → `brain_available: false`, Eva logs warning, pipeline continues in baseline mode
- `brain_available` persisted in pipeline-state.md for session recovery

**Estimated complexity:** Low — config flag + one tool call + state variable.

### Step 9: Pipeline Integration — Agent Personas

Update agent personas with brain access patterns per the Agent Operating Model.

**Files to modify:**
- `templates/agents/cal.md`
- `templates/agents/colby.md`
- `templates/agents/roz.md`
- `templates/agents/robert.md`
- `templates/agents/sable.md`
- `source/agents/agatha.md`
- `templates/rules/default-persona.md` (Eva)
- `templates/references/invocation-templates.md`

**Per-agent additions:**
- New section: `## Brain Access (MANDATORY when brain is available)` with specific read/write requirements
- Read requirements: which `agent_search` calls to make, when (before starting work + mid-task for emergent questions), with what queries
- Write requirements: which `agent_capture` calls to make, with exact `thought_type`, `source_agent`, `source_phase`, `importance` values. These are not suggestions — they are required steps in the agent's workflow.
- All requirements conditional on availability: "If brain is available..." — agents skip cleanly when brain is absent. But when brain IS available, these steps are mandatory, not optional.

**Eva-specific additions:**
- Gate-triggered capture rules (which events → which thought types)
- Relation creation rules (which events → which relation types)
- Pre-delegation search patterns (what to search before invoking each agent)
- Pipeline-end session summary capture

**Invocation template update:**
- Add optional BRAIN section to subagent prompt template: prior context from brain search, if available

**Acceptance criteria:**
- Poirot, Distillator, Ellis personas unchanged (no brain access)
- Every brain-touching agent persona includes a `## Brain Access (MANDATORY when brain is available)` section
- Each brain access section specifies exact tool calls (`agent_search`, `agent_capture`, `atelier_relation`, `atelier_trace`) with required parameters (`thought_type`, `source_agent`, `source_phase`, `importance`)
- Language in agent personas is directive ("MUST call", "calls"), not suggestive ("can", "may", "should consider")
- All brain interactions are conditional on availability ("if brain is available") — but mandatory when it is
- Eva's capture rules are mechanical (gate fires → capture), not discretionary
- Invocation templates include brain context injection slot

**Estimated complexity:** Medium — many files to touch, but changes are additive (append sections, don't rewrite).

### Step 10: Brain Setup Skill

New atelier-pipeline skill that guides brain setup. Supports all three deployment tiers.

**Files to create:**
- `skills/brain-setup/SKILL.md`

**Files to modify:**
- `.claude-plugin/plugin.json` (add skill reference)

**Skill flow:**

**Path A — No config exists (first-time setup):**
1. Ask: "Personal brain or shared team brain?"
2. Ask: database strategy — "Local PostgreSQL or Docker?"
   - Docker: run `docker compose -f ${CLAUDE_PLUGIN_ROOT}/brain/docker-compose.yml up -d`. Schema auto-applies on first boot.
   - Local: Ask database name (default: `atelier_brain`). Run `schema.sql` against their PostgreSQL.
3. Ask: OpenRouter API key (or confirm existing from environment)
4. Ask: scope path (e.g., `myorg.myproduct`)
5. Verify connection via `atelier_stats`
6. **Personal:** Write config to `${CLAUDE_PLUGIN_DATA}/brain-config.json` (local, not committed)
7. **Shared:** Write config to `.claude/brain-config.json` (project-level, committed). Secrets as env var references.
8. Set `brain_config.brain_enabled = true` in database
9. Confirm: "Brain is live. [N] tools available. Scope: [path]. Config: [personal/shared]."

**Path B — Project-level config exists (colleague onboarding):**
1. Detect `.claude/brain-config.json` exists
2. Check env vars (OPENROUTER_API_KEY, database password if applicable)
   - All present → verify connection → "Brain connected. You're using the team brain at [scope]."
   - Missing → "Project brain config found. Set these env vars to connect: [list]. Pipeline will run in baseline mode until configured."
3. No interactive setup needed — just env var guidance.

**Acceptance criteria:**
- Skill runs conversationally (one question at a time)
- Detects existing project-level config and short-circuits to Path B
- Schema creates cleanly on fresh database (both Docker and local)
- Docker compose starts cleanly, schema auto-applies via entrypoint
- Handles "database already exists" gracefully (skip schema, verify tables)
- Personal config never committed to git (written to `${CLAUDE_PLUGIN_DATA}`)
- Shared config committed with env var placeholders, never bare secrets
- Sets config flag after successful verification
- Provides clear error messages for common failures (PostgreSQL not running, Docker not installed, wrong credentials, extension missing)

**Estimated complexity:** Medium — branching flow (personal vs shared, Docker vs local, first-time vs colleague).

### Step 11: Plugin Deployment Infrastructure

Plugin-level files that enable auto-registration and session lifecycle.

**Files to create:**
- `.mcp.json` (MCP server declaration)
- `brain/docker-compose.yml`
- `brain/docker-entrypoint.sh` (runs schema.sql on first boot)

**Files to modify:**
- `.claude-plugin/plugin.json` (add hooks, MCP server reference)

**.mcp.json:**
```json
{
  "mcpServers": {
    "atelier-brain": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/brain/server.mjs"],
      "env": {
        "DATABASE_URL": "${ATELIER_BRAIN_DATABASE_URL}",
        "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
        "BRAIN_CONFIG_PROJECT": "${CLAUDE_PROJECT_DIR}/.claude/brain-config.json",
        "BRAIN_CONFIG_USER": "${CLAUDE_PLUGIN_DATA}/brain-config.json"
      }
    }
  }
}
```

**SessionStart hook (in plugin.json):**
The brain MCP server itself handles config detection on startup:
1. Check `BRAIN_CONFIG_PROJECT` path — if exists, read and use
2. Else check `BRAIN_CONFIG_USER` path — if exists, read and use
3. Else exit cleanly (brain disabled, no tools registered)

**docker-compose.yml:**
```yaml
services:
  brain-db:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: atelier_brain
      POSTGRES_USER: atelier
      POSTGRES_PASSWORD: ${ATELIER_BRAIN_DB_PASSWORD:-atelier}
    volumes:
      - brain-data:/var/lib/postgresql/data
      - ./schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    ports:
      - "5432:5432"

volumes:
  brain-data:
```

**Config resolution logic in brain server:**
The brain MCP server does NOT use the `DATABASE_URL` env var from `.mcp.json` directly. On startup:
1. Check `BRAIN_CONFIG_PROJECT` path → if file exists and valid JSON, read `database_url` and `scope` from it. Resolve any `${ENV_VAR}` placeholders in values against the process environment.
2. Else check `BRAIN_CONFIG_USER` path → same logic.
3. Else exit cleanly (no config = no brain).

The `.mcp.json` env vars (`DATABASE_URL`, `OPENROUTER_API_KEY`) serve as fallbacks ONLY if the config file doesn't specify them. Config file values always win over env vars. This ensures the config file is the single source of truth for connection details.

**Local overrides in shared mode:**
When using project-level config, the brain server also checks for `${CLAUDE_PLUGIN_DATA}/brain-overrides.json`. This file stores personal tuning (consolidation interval, TTL adjustments, etc.) that don't belong in the shared project config. Override values merge on top of project config — connection details are never overridden, only behavior settings.

**Acceptance criteria:**
- `.mcp.json` registers brain MCP server with plugin system
- Brain MCP server reads config priority chain (project > user > none) on startup
- Config FILE values win over env vars when both exist
- `${ENV_VAR}` placeholders in config files are resolved against process environment
- Local overrides file merges behavior settings (TTL, consolidation) but cannot override connection details (database URL, scope)
- If no config found, server exits without error — no tools registered, pipeline unaffected
- Docker compose creates PostgreSQL 17 with pgvector AND ltree extensions, schema auto-applied via initdb
- Docker volume persists data across container restarts
- `docker compose down && docker compose up` preserves all existing thoughts
- Docker compose default password (`atelier`) is for local development only. `/brain-setup --shared` with Docker warns if default password is detected: "Set ATELIER_BRAIN_DB_PASSWORD for team use."

**Estimated complexity:** Medium — config resolution logic with fallbacks, override merging, env var placeholder resolution.

## Comprehensive Test Specification

*Revised per Roz QA review. All steps meet failure >= happy ratio.*

### Step 1 Tests: Schema (4 Happy, 5 Failure, 2 Boundary = 11)

| ID | Category | Description |
|---|---|---|
| T-0001-001 | Happy | Schema creates on fresh PostgreSQL 17 with pgvector + ltree |
| T-0001-002 | Happy | `thought_type_config` seeded with 8 rows matching defaults |
| T-0001-003 | Happy | `brain_config` singleton row created with all defaults (`brain_enabled = false`) |
| T-0001-004 | Failure | INSERT thought with invalid enum value → rejected |
| T-0001-005 | Failure | INSERT thought with importance > 1.0 → rejected |
| T-0001-006 | Failure | INSERT thought with importance < 0.0 → rejected |
| T-0001-007 | Boundary | INSERT thought with importance = 0.0 → accepted |
| T-0001-008 | Boundary | INSERT thought with importance = 1.0 → accepted |
| T-0001-009 | Failure | INSERT second brain_config row → rejected (CHECK constraint) |
| T-0001-010 | Happy | All indexes create without error |
| T-0001-011 | Failure | INSERT thought with malformed ltree scope (e.g. `'not..valid'`) → rejected |

### Step 2 Tests: Scoring Function (7 Happy, 7 Failure, 5 Boundary = 19)

| ID | Category | Description |
|---|---|---|
| T-0002-001 | Happy | Function returns results ordered by combined_score DESC |
| T-0002-002 | Happy | Higher importance thought outranks lower importance at equal similarity and recency |
| T-0002-003 | Happy | More recently accessed thought outranks older at equal similarity and importance |
| T-0002-004 | Happy | Higher similarity thought outranks lower at equal importance and recency |
| T-0002-005 | Happy | Scope filter narrows results to matching ltree paths only |
| T-0002-006 | Happy | `include_invalidated = false` excludes superseded thoughts |
| T-0002-007 | Happy | `include_invalidated = true` includes superseded thoughts |
| T-0002-008 | Boundary | Empty database returns 0 results, no error |
| T-0002-009 | Boundary | Similarity threshold 1.0 returns only exact matches |
| T-0002-010 | Boundary | Similarity threshold 0.0 returns all thoughts |
| T-0002-011 | Failure | NULL embedding input → error, not crash |
| T-0002-012 | Failure | Query embedding with wrong dimensionality (768d to 1536d function) → error with clear message |
| T-0002-013 | Failure | Scope filter with malformed ltree → error, not crash |
| T-0002-014 | Failure | `max_results = 0` → returns empty set, no error |
| T-0002-015 | Failure | `max_results = -1` → error, not unbounded query |
| T-0002-016 | Boundary | `importance = 0.0` thought with high similarity → still returned (not filtered, just low-ranked) |
| T-0002-017 | Boundary | Default-scoped thoughts (`'default'`) returned when `scope_filter = 'default'` |
| T-0002-018 | Failure | Similarity threshold > 1.0 → error or clamped, not silent pass |
| T-0002-019 | Failure | Similarity threshold < 0.0 → error or clamped, not silent pass |

### Step 3 Tests: MCP Tools (15 Happy, 15 Failure, 4 Boundary, 2 Security, 1 Concurrency = 37)

| ID | Category | Description |
|---|---|---|
| T-0003-001 | Happy | `agent_capture` with all required fields → stored, ID returned |
| T-0003-002 | Failure | `agent_capture` missing `thought_type` → rejected with error |
| T-0003-003 | Failure | `agent_capture` with invalid `source_agent` → rejected |
| T-0003-004 | Happy | `agent_capture` with `supersedes_id` → relation created, target invalidated |
| T-0003-005 | Happy | Conflict detection: duplicate (>0.9) → merged, single ID returned |
| T-0003-006 | Happy | Conflict detection: candidate (0.7-0.9) + LLM → classified correctly |
| T-0003-007 | Happy | Conflict detection: novel (<0.7) → stored, no classification |
| T-0003-008 | Happy | Conflict detection skipped for `thought_type: 'drift'` |
| T-0003-009 | Happy | `agent_search` updates `last_accessed_at` on returned thoughts |
| T-0003-010 | Happy | `agent_search` with scope filter returns only matching scope |
| T-0003-011 | Happy | `atelier_browse` filters by status, thought_type, source_agent |
| T-0003-012 | Happy | `atelier_stats` returns counts by type, status, agent |
| T-0003-013 | Happy | `atelier_relation` with `supersedes` type → target invalidated |
| T-0003-014 | Happy | `atelier_relation` with `triggered_by` type → no side effects |
| T-0003-015 | Happy | `atelier_trace` backward returns full ancestry |
| T-0003-016 | Happy | `atelier_trace` forward returns all descendants |
| T-0003-017 | Boundary | `atelier_trace` on thought with no relations → returns only the thought |
| T-0003-018 | Boundary | `atelier_trace` with max_depth = 0 → returns only the thought |
| T-0003-019 | Failure | `atelier_relation` with non-existent thought ID → FK error |
| T-0003-020 | Security | `agent_capture` content with SQL injection attempt → safely parameterized |
| T-0003-021 | Failure | `agent_capture` with `supersedes_id` pointing to already-invalidated thought → accepted (double-invalidate is idempotent, relation still created) |
| T-0003-022 | Failure | `agent_capture` when OpenRouter embedding generation fails → rejected with clear error, nothing stored |
| T-0003-023 | Failure | `agent_capture` conflict detection LLM call fails mid-classification → thought stored without conflict check, warning returned |
| T-0003-024 | Failure | `atelier_relation` creating a cycle (A supersedes B, B supersedes A) → rejected with cycle detection error |
| T-0003-025 | Boundary | `atelier_trace` at max_depth stops cleanly, returns partial chain with depth indicators |
| T-0003-026 | Failure | `agent_search` with empty query string → error with message, not empty results |
| T-0003-027 | Failure | `atelier_browse` with conflicting filters producing empty set → returns empty array, not error |
| T-0003-028 | Failure | Any MCP tool called when database connection is lost → error with reconnect guidance, not crash |
| T-0003-029 | Failure | `agent_capture` with `importance` outside 0-1 range → rejected before embedding call (fail fast) |
| T-0003-030 | Failure | `agent_capture` duplicate merge combines metadata and keeps higher importance |
| T-0003-031 | Failure | `atelier_relation` with source_id = target_id (self-referential) → rejected |
| T-0003-032 | Concurrency | Two simultaneous `agent_capture` calls with identical content → one merged, not two duplicates |
| T-0003-033 | Boundary | `atelier_trace` on diamond graph (A→B, A→C, B→D, C→D) → D returned once, not twice |
| T-0003-034 | Happy | `agent_capture` with multi-scope `['acme.payments', 'acme.notifications']` → search with either scope returns the thought |
| T-0003-035 | Failure | `atelier_trace` direction = 'backward' from source thought correctly follows `synthesized_from` relations TO the reflection (relation direction: reflection→source, backward traversal from source finds reflection) |
| T-0003-036 | Security | `agent_capture` metadata JSONB with deeply nested object (>10 levels) → accepted but capped or rejected if oversized |
| T-0003-037 | Failure | `agent_capture` with content exceeding max length (if defined) → rejected with size error |

### Step 4 Tests: TTL (4 Happy, 4 Failure, 2 Boundary = 10)

| ID | Category | Description |
|---|---|---|
| T-0004-001 | Happy | Thought past TTL → status set to 'expired', invalidated_at set |
| T-0004-002 | Happy | Decision type (NULL TTL) → never expired |
| T-0004-003 | Happy | Reflection type (NULL TTL) → never expired |
| T-0004-004 | Boundary | Thought exactly at TTL boundary → not expired (< not <=) |
| T-0004-005 | Happy | Timer reads interval from brain_config |
| T-0004-006 | Failure | `thought_type_config` row has TTL changed to shorter than existing thoughts' age → bulk expiration on next tick, all affected thoughts updated |
| T-0004-007 | Failure | `thought_type_config` row deleted for a type → timer skips that type gracefully, no crash |
| T-0004-008 | Failure | Timer fires during concurrent `agent_search` reading the same thought → no deadlock, both operations complete |
| T-0004-009 | Boundary | TTL set to 0 → all thoughts of that type expire on next tick |
| T-0004-010 | Failure | TTL timer tick with database connection lost mid-update → partial expiration rolled back, no thoughts left in inconsistent state |

### Step 5 Tests: Consolidation (5 Happy, 6 Failure, 1 Boundary = 12)

| ID | Category | Description |
|---|---|---|
| T-0005-001 | Happy | 3+ related unconsolidated thoughts → reflection created |
| T-0005-002 | Happy | Reflection importance > max source importance |
| T-0005-003 | Happy | `synthesized_from` relations created from reflection to all sources (direction: reflection.id = source_id, source_thought.id = target_id) |
| T-0005-004 | Happy | Source thoughts remain `status: 'active'` after consolidation |
| T-0005-005 | Boundary | < min_thoughts unconsolidated → consolidation skips |
| T-0005-006 | Failure | LLM call fails → consolidation skips cluster, continues to next |
| T-0005-007 | Happy | max_thoughts respected — large backlog processed in chunks |
| T-0005-008 | Failure | Consolidation runs while new thoughts being captured → new thoughts not included in current pass, picked up next pass |
| T-0005-009 | Failure | Consolidation produces reflection semantically similar to existing reflection → dedup applies, existing reflection updated |
| T-0005-010 | Failure | Source thought superseded AFTER being included in a reflection → reflection remains valid, relation preserved |
| T-0005-011 | Failure | OpenRouter embedding call fails during reflection creation → reflection discarded, source thoughts remain unconsolidated |
| T-0005-012 | Failure | Config changes mid-consolidation pass → current pass finishes with original config, next pass reads updated config |

### Step 6 Tests: Settings API (7 Happy, 8 Failure, 1 Boundary = 16)

| ID | Category | Description |
|---|---|---|
| T-0006-001 | Happy | `GET /api/health` returns status, count, last consolidation, next consolidation |
| T-0006-002 | Happy | `PUT /api/config` updates consolidation interval |
| T-0006-003 | Happy | `PUT /api/thought-types/drift` updates TTL |
| T-0006-004 | Failure | `PUT /api/thought-types/invalid` → 404 |
| T-0006-005 | Happy | `POST /api/purge-expired` deletes expired thoughts, returns count of thoughts and orphaned relations cleaned |
| T-0006-006 | Boundary | Purge with 0 expired thoughts → returns count: 0 |
| T-0006-007 | Happy | API coexists with MCP transport on same HTTP server |
| T-0006-008 | Failure | `PUT /api/config` with string where number expected → 400 with validation error |
| T-0006-009 | Failure | `PUT /api/thought-types/decision` setting TTL to a number → accepted (user override of "never expires" default is intentional, not blocked) |
| T-0006-010 | Failure | `PUT /api/config` with negative consolidation_interval → 400 validation error |
| T-0006-011 | Failure | `GET /api/health` when database unreachable → returns `{ connected: false }`, not 500 |
| T-0006-012 | Happy | `GET /api/health` `next_consolidation_at` = last_consolidation + consolidation_interval_minutes |
| T-0006-013 | Failure | `POST /api/purge-expired` cascades relation cleanup — no orphaned `thought_relations` rows referencing deleted thoughts |
| T-0006-014 | Failure | Concurrent PUT to same config key → last-write-wins, no corruption |
| T-0006-015 | Happy | `GET /api/stats` returns counts by type, by status, by agent |
| T-0006-016 | Failure | `GET /api/stats` when database unreachable → returns empty counts or error, not crash |

### Step 7 Tests: Settings UI (5 Happy, 8 Failure, 2 Boundary, 1 Security, 4 Accessibility = 20)

| ID | Category | Description |
|---|---|---|
| T-0007-001 | Happy | Page loads, status bar shows connection state |
| T-0007-002 | Happy | Toggle disable → confirmation dialog → brain disabled |
| T-0007-003 | Happy | Inline edit TTL → save → value persisted |
| T-0007-004 | Happy | Purge → confirmation with count → expired thoughts removed |
| T-0007-005 | Boundary | Empty state (no brain configured) → dimmed sections, helper text "Run /brain-setup..." |
| T-0007-006 | Boundary | Error state (brain down) → amber status, sections still editable |
| T-0007-007 | Security | Scope input with path traversal attempt → validation rejects, only lowercase alphanumeric and dots accepted |
| T-0007-008 | Failure | Scope input uppercase → validation error "Invalid scope format. Use lowercase letters separated by dots" |
| T-0007-009 | Failure | Scope input empty string → validation error |
| T-0007-010 | Failure | Scope input trailing dot (`acme.payments.`) → validation error |
| T-0007-011 | Failure | TTL number input with negative value → validation rejects |
| T-0007-012 | Failure | TTL number input with non-numeric text → validation rejects |
| T-0007-013 | Failure | Rapid toggle clicks (enable → disable → enable in <1s) → debounced, final state correct |
| T-0007-014 | Failure | Test Connection when brain unreachable → shows "✗ [error message]" inline, not page crash |
| T-0007-015 | Accessibility | Status bar `role="status"` with `aria-live="polite"` announces changes to screen reader |
| T-0007-016 | Accessibility | Confirmation dialog focus-trapped, Escape dismisses, focus returns to trigger button |
| T-0007-017 | Accessibility | All interactive elements keyboard-reachable in visual order (Tab), toggles activated with Space |
| T-0007-018 | Accessibility | TTL ∞ displayed for NULL value; edit mode shows empty field with placeholder "never" |
| T-0007-019 | Failure | Mobile viewport (<480px) → lifecycle table renders as card layout, not broken horizontal table |
| T-0007-020 | Happy | Status bar polls `/api/health` every 30s, updates without page reload |

### Step 8-9 Tests: Pipeline Integration (10 Happy, 10 Failure, 0 Boundary, 0 Security, 3 Regression = 23)

| ID | Category | Description |
|---|---|---|
| T-0008-001 | Happy | Brain MCP server not running (no config) → Eva detects tool unavailable, skips brain interaction |
| T-0008-002 | Happy | Brain MCP server running + `brain_enabled: true` + healthy → `brain_available: true` |
| T-0008-003 | Happy | Brain MCP server running + `brain_enabled: true` + down → `brain_available: false`, pipeline continues baseline |
| T-0008-020 | Failure | Brain MCP server running + `brain_enabled: false` → `atelier_stats` reports disabled, `brain_available: false`, pipeline baseline |
| T-0008-004 | Happy | Agent with brain: searches before task, captures after task |
| T-0008-005 | Happy | Agent without brain: identical behavior to current baseline |
| T-0008-006 | Happy | Eva captures DRIFT finding as thought with correct metadata |
| T-0008-007 | Happy | Eva creates relation: correction `triggered_by` drift finding |
| T-0008-008 | Regression | Poirot receives no brain context in invocation prompt |
| T-0008-009 | Regression | Full pipeline run with brain disabled produces identical output to current |
| T-0008-010 | Happy | Eva captures Poirot's findings post-review (Poirot himself never touches brain) |
| T-0008-011 | Happy | Colby searches brain for codebase patterns before building; proceeds without results if brain empty |
| T-0008-012 | Happy | Agatha searches brain for prior doc reasoning before writing docs |
| T-0008-013 | Failure | Brain becomes unavailable mid-pipeline-run → agents that haven't started brain-enhanced work fall back to baseline; agents mid-search get error and proceed without results |
| T-0008-014 | Failure | `brain: enabled` but brain MCP tools not registered → Eva's health check fails, `brain_available: false`, pipeline continues baseline |
| T-0008-015 | Failure | Eva captures thought but brain is at capacity (disk full) → capture fails gracefully, pipeline continues, warning logged |
| T-0008-016 | Failure | Agent searches brain, gets results, but disk artifact contradicts brain context → agent uses disk artifact (disk always wins) |
| T-0008-017 | Failure | `conflicted` status thought does NOT halt pipeline — it's a flag for human, not a gate |
| T-0008-018 | Regression | Distillator receives no brain context in invocation prompt |
| T-0008-019 | Failure | Agent search returns irrelevant results → agent proceeds with normal behavior, irrelevant context doesn't corrupt output |
| T-0008-021 | Failure | Eva captures gate event but `agent_capture` returns conflict flag → Eva logs conflict, does NOT halt pipeline, continues normally |
| T-0008-022 | Failure | Agent persona brain section says "MUST call agent_search" but brain became unavailable between health check and agent invocation → agent detects tool error, skips brain steps, proceeds baseline |
| T-0008-023 | Failure | `brain_available: true` persisted in pipeline-state.md but brain goes down before session recovery reads it → Eva re-checks on recovery, updates to false, proceeds baseline |

### Step 10 Tests: Setup Skill (5 Happy, 9 Failure = 14)

| ID | Category | Description |
|---|---|---|
| T-0010-001 | Happy | Fresh personal setup (local PostgreSQL): database created, schema applied, config written to `${CLAUDE_PLUGIN_DATA}` |
| T-0010-002 | Happy | Fresh personal setup (Docker): `docker compose up`, schema auto-applied, config written to `${CLAUDE_PLUGIN_DATA}` |
| T-0010-003 | Happy | Fresh shared setup: database created, config written to `.claude/brain-config.json` with env var placeholders |
| T-0010-004 | Happy | Existing database: schema verified, no duplicate creation |
| T-0010-005 | Happy | Colleague onboarding (Path B): project config exists + env vars set → connection verified, no interactive setup |
| T-0010-006 | Failure | PostgreSQL not running → clear error message |
| T-0010-007 | Failure | pgvector extension missing → clear error message with install instruction |
| T-0010-008 | Failure | ltree extension missing → clear error message with install instruction |
| T-0010-009 | Failure | Database exists but schema is outdated (missing columns) → reports version mismatch, suggests re-run |
| T-0010-010 | Failure | Docker not installed → clear error message, suggests local PostgreSQL alternative |
| T-0010-011 | Failure | Colleague onboarding: project config exists but env vars missing → clear message listing required env vars |
| T-0010-012 | Failure | Shared setup: skill does NOT write bare secrets to `.claude/brain-config.json` — only env var references |
| T-0010-013 | Failure | Developer with existing personal config pulls repo with project config → settings UI shows project config active with note "Project config active. Personal brain accessible via direct connection." Personal config is NOT deleted. |
| T-0010-014 | Failure | Shared setup with Docker: default password detected → warning "Set ATELIER_BRAIN_DB_PASSWORD for team use" |

### Step 11 Tests: Plugin Deployment (6 Happy, 7 Failure = 13)

| ID | Category | Description |
|---|---|---|
| T-0011-001 | Happy | Brain MCP server reads project-level config when both project and user configs exist |
| T-0011-002 | Happy | Brain MCP server reads user-level config when only user config exists |
| T-0011-003 | Happy | Brain MCP server exits cleanly when no config exists — no tools registered, no errors |
| T-0011-004 | Failure | `.mcp.json` references brain server but config missing → server starts, finds no config, exits cleanly |
| T-0011-005 | Failure | Docker compose `down` + `up` preserves all existing thoughts (volume persistence) |
| T-0011-006 | Failure | Brain server started with project config containing `${OPENROUTER_API_KEY}` but env var not set → clear error, exits without crash |
| T-0011-007 | Failure | Two brain servers started simultaneously (user restarts session) → second instance detects port conflict, exits cleanly |
| T-0011-008 | Happy | Docker compose first boot creates both pgvector AND ltree extensions successfully |
| T-0011-009 | Failure | Project-level `brain-config.json` is malformed JSON → brain server logs parse error, exits cleanly, pipeline runs baseline |
| T-0011-010 | Failure | Project-level `brain-config.json` exists but missing required `database_url` field → brain server logs "missing database_url", exits cleanly |
| T-0011-011 | Happy | Config file contains `${OPENROUTER_API_KEY}` placeholder → resolved against process environment, correct key used |
| T-0011-012 | Happy | Local overrides file changes consolidation_interval → brain uses override value, not project config value |
| T-0011-013 | Failure | Local overrides file attempts to override database_url → ignored, project config database_url used, warning logged |

### Contract Boundaries

| Producer | Consumer | Expected Shape |
|---|---|---|
| `agent_capture` MCP tool | Pipeline agents (Cal, Robert, Sable, Colby, Roz, Agatha) | `{ thought_id: uuid, created_at: timestamp, conflict_flag?: boolean, related_ids?: uuid[] }` |
| `agent_search` MCP tool | Pipeline agents | `{ results: [{ id, content, metadata, thought_type, similarity, combined_score }] }` |
| `atelier_trace` MCP tool | Eva, agents tracing decisions | `{ chain: [{ id, content, depth, via_relation, via_context }] }` |
| `/api/health` REST endpoint | Settings UI | `{ connected: boolean, thought_count: number, last_consolidation: timestamp, next_consolidation_at: timestamp }` |
| `/api/config` REST endpoint | Settings UI | `{ consolidation_interval_minutes, conflict_detection_enabled, ... }` |
| `/api/thought-types` REST endpoint | Settings UI | `[{ thought_type, default_ttl_days, default_importance, description }]` |
| LLM conflict classification (OpenRouter) | `agent_capture` conflict detector | **Input:** `{ messages: [{ role: "user", content: "Thought A: [content]\nThought B: [content]\nClassify: DUPLICATE, CONTRADICTION, COMPLEMENT, SUPERSESSION, or NOVEL" }], model: "configured_model" }` **Output:** `{ classification: enum, confidence: float, reasoning: string }` — If response doesn't match expected shape, treat as classification failure (thought stored without conflict check). |
| LLM consolidation synthesis (OpenRouter) | Consolidation engine | **Input:** `{ messages: [{ role: "user", content: "Synthesize these [N] observations into a single higher-level insight: [thought contents]" }], model: "configured_model" }` **Output:** Free-text synthesis. If response is empty or error, skip cluster. |

### Relation Direction Convention

`thought_relations.source_id` = the NEWER or DERIVED thought. `thought_relations.target_id` = the OLDER or ORIGINAL thought.

| Relation Type | Direction | Example |
|---|---|---|
| `supersedes` | new → old | Correction → original decision |
| `triggered_by` | effect → cause | Drift finding → review juncture event |
| `evolves_from` | evolved → origin | Spec v3 reasoning → spec v2 reasoning |
| `contradicts` | newer → older | Team B decision → Team A decision |
| `supports` | supporting → supported | Evidence → claim |
| `synthesized_from` | reflection → source | Consolidated insight → raw observation |

`atelier_trace` backward traversal follows `target_id → source_id` (finds what this thought came from). Forward traversal follows `source_id → target_id` (finds what was derived from this thought). Test T-0003-035 explicitly verifies that backward traversal from a source thought correctly finds the reflection via `synthesized_from`.

### Data Sensitivity

| Method/Endpoint | Classification | Notes |
|---|---|---|
| `agent_capture` | auth-only | Contains reasoning, decisions, potentially sensitive business logic |
| `agent_search` | auth-only | Returns thought content |
| `atelier_browse` | auth-only | Returns thought content |
| `atelier_stats` | public-safe | Aggregate counts only |
| `/api/health` | public-safe | Connection status, no content |
| `/api/config` | auth-only | System configuration |
| `/api/thought-types` | public-safe | Type definitions, no content |
| `/api/purge-expired` | auth-only | Destructive operation |
| Embedding API call (OpenRouter) | auth-only | Sends thought content to external service for embedding |

## UX Coverage

| UX Doc Section | ADR Step | Test IDs | Status |
|---|---|---|---|
| Status bar (connected/disconnected) | Step 6 (`/api/health`), Step 7 (UI) | T-0007-001, T-0007-020 | Covered |
| Enable/disable toggle | Step 6 (`/api/config`), Step 7 (UI), Step 8 (pipeline config) | T-0007-002, T-0007-013 | Covered |
| Connection section (DB URL, scope, test) | Step 6 (`/api/health`, `/api/config`), Step 7 (UI) | T-0007-007, T-0007-008, T-0007-009, T-0007-010, T-0007-014 | Covered |
| Thought lifecycle table (TTL, importance) | Step 1 (schema), Step 6 (`/api/thought-types`), Step 7 (UI) | T-0007-003, T-0007-011, T-0007-012, T-0007-018 | Covered |
| TTL ∞ / NULL mapping | Step 7 (UI) | T-0007-018 | Covered |
| Consolidation config (timer, min/max) | Step 1 (schema), Step 5 (engine), Step 6 (`/api/config`), Step 7 (UI) | T-0006-001, T-0006-012 | Covered |
| Consolidation "Next scheduled" timestamp | Step 6 (`/api/health`) | T-0006-012 | Covered |
| Conflict detection config (thresholds, LLM toggle) | Step 1 (schema), Step 3 (detection), Step 6 (`/api/config`), Step 7 (UI) | T-0003-005 through T-0003-008 | Covered |
| Danger zone (purge) | Step 6 (`/api/purge-expired`), Step 7 (UI) | T-0007-004, T-0006-005, T-0006-013 | Covered |
| Empty state | Step 7 (UI) | T-0007-005 | Covered |
| Loading state | Step 7 (UI) | T-0007-020 (status bar polling) | Covered |
| Error state | Step 7 (UI) | T-0007-006, T-0007-014, T-0006-011 | Covered |
| Responsive (mobile card layout) | Step 7 (UI) | T-0007-019 | Covered |
| Accessibility (keyboard) | Step 7 (UI) | T-0007-017 | Covered |
| Accessibility (screen reader) | Step 7 (UI) | T-0007-015 | Covered |
| Accessibility (focus management) | Step 7 (UI) | T-0007-016 | Covered |

## Product Spec Coverage

| Feature Spec Requirement | ADR Step | Status |
|---|---|---|
| US-1: Cross-session memory | Step 2 (scoring), Step 3 (search), Step 9 (agent personas) | Covered |
| US-2: Decision evolution trail | Step 1 (relations table), Step 3 (atelier_relation, atelier_trace) | Covered |
| US-3: Conflict detection | Step 1 (schema), Step 3 (agent_capture conflict logic) | Covered |
| US-4: Knowledge decay | Step 1 (thought_type_config), Step 4 (TTL timer) | Covered |
| US-5: Consolidation | Step 1 (brain_config), Step 5 (consolidation engine) | Covered |
| US-6: Scoped access | Step 1 (ltree), Step 2 (scope filter in scoring) | Covered |
| US-7: Brain as optional | Step 8 (two-gate detection), Step 10 (setup skill), Step 11 (plugin deployment) | Covered |
| US-8: Solo developer setup | Step 10 (setup skill Path A — personal), Step 11 (Docker compose) | Covered |
| US-9: Team shared brain setup | Step 10 (setup skill — shared path), Step 11 (plugin deployment, config priority) | Covered |
| US-10: Config priority and override | Step 11 (brain server config priority chain) | Covered |
| Agent Operating Model | Step 9 (agent persona updates) | Covered |

## Notes for Colby

- Start from mybrain's `server.mjs` (208 lines). The fork-and-extend approach preserves the working MCP transport patterns.
- The conflict detection LLM call in `agent_capture` is the most complex integration point. Consider extracting it into a separate function (`classifyConflict`) to keep the tool handler clean.
- The consolidation engine's clustering logic doesn't need to be sophisticated in v1. Simple pairwise cosine similarity > 0.6 among the top N unconsolidated thoughts (sorted by recency) is sufficient. Don't over-engineer the clustering.
- The Settings API shares the HTTP server with MCP transport. Route by path prefix: `/api/*` → REST handlers, everything else → MCP transport handler.
- The Settings UI is vanilla HTML/CSS/JS. No build step, no framework. Served as static files from `brain/ui/`.
- `last_accessed_at` update after search: use a single `UPDATE thoughts SET last_accessed_at = now() WHERE id = ANY($1)` with the returned IDs. Don't update inside the scoring function.
- Consolidation timer and TTL timer are independent `setInterval` calls. They don't coordinate — consolidation might process a thought that TTL expires in the same cycle. That's fine — the reflection already captured the value.

---

## DoD: Verification

| # | Criterion | Status |
|---|---|---|
| D1 | Every feature spec user story (US-1 through US-10) mapped to at least one step | Done — see Product Spec Coverage |
| D2 | Every UX spec section mapped to at least one step | Done — see UX Coverage |
| D3 | All agent operating model behaviors addressed in Step 9 | Done |
| D4 | Test spec covers Happy, Failure, Boundary, Security, Regression, Accessibility, Concurrency categories | Done — 175 tests across all categories |
| D5 | Contract boundaries defined for all MCP tools, REST endpoints, and LLM classification calls | Done |
| D6 | Data sensitivity tagged for all methods | Done |
| D7 | Alternatives considered with rejection rationale | Done — 5 alternatives |
| D8 | Spec challenge stated | Done — agent mid-task search quality |
| D9 | No TODO/FIXME/HACK in this document | Verified |
| D10 | Blast radius: mybrain untouched, atelier-pipeline templates modified (8 files), new brain/ directory | Verified |
| D11 | Failure:happy ratio >= 1:1 across all steps | Done — see per-step counts |
| D12 | Relation direction convention documented with explicit examples | Done — see Relation Direction Convention |
| D13 | Agent operating model cross-checked: Poirot/Eva capture, Colby reads, Agatha reads all tested | Done — T-0008-010, T-0008-011, T-0008-012 |
| D14 | UX spec cross-checked: accessibility, responsive, ∞ mapping, next-consolidation all tested | Done — T-0007-015 through T-0007-020, T-0006-012 |
| D15 | `next_consolidation_at` added to health endpoint | Done — Step 6 acceptance criteria updated |

---

**ADR revised per Roz deployment review + Cal cross-validation + Roz final QA. 11 steps, 175 total tests (68 happy, 79 failure, 17 boundary, 3 security, 4 accessibility, 3 regression, 1 concurrency). All Roz findings resolved. Cal cross-validation findings (F1-F5) resolved. Roz final QA findings (MF-1 through MF-10) resolved: Step 7 states expanded to 7, all test headers corrected, ratio-violating steps patched with additional failure tests, DoD updated.**
