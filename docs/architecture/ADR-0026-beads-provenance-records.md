# ADR-0026: Beads-Style Structured Provenance for Brain Captures

## DoR: Requirements Extracted

**Sources:** Issue #23, `brain/schema.sql` (current schema), `brain/lib/tools.mjs`
(agent_capture + atelier_trace implementation), `brain/lib/config.mjs` (enum constants),
`brain/lib/db.mjs` (migration runner), `brain/package.json` (version 1.2.0),
`tests/brain/tools.test.mjs` (T-0003-087 through T-0003-102),
`docs/architecture/ADR-0025-mechanical-telemetry-extraction.md` (prior art),
`.claude/references/retro-lessons.md`, `.claude/references/step-sizing.md`.

| # | Requirement | Source |
|---|-------------|--------|
| R1 | Add `decided_by` field to agent_capture: `{agent: string, human_approved: boolean}` | Issue #23 / task constraints |
| R2 | Add `alternatives_rejected` field to agent_capture: array of `{alternative: string, reason: string}` | Issue #23 / task constraints |
| R3 | Add `evidence` field to agent_capture: array of `{file: string, line: number}` | Issue #23 / task constraints |
| R4 | Add `confidence` field to agent_capture: number 0-1, degrades toward retro lessons | Issue #23 / task constraints |
| R5 | All four provenance fields are optional and apply only to `thought_type: decision` | Issue #23 / task constraints |
| R6 | `superseded_by` reverse lookup: computed from thought_relations, not a stored column | Issue #23 / task constraints |
| R7 | Extend atelier_trace or add new tool to surface structured provenance fields | Issue #23 / task constraints |
| R8 | Storage decision: new columns vs metadata JSONB, justified with trade-offs | Issue #23 / task constraints |
| R9 | Migration 007 for any schema changes | Issue #23 / task constraints |
| R10 | Document capture convention so agents know how to populate provenance fields | Issue #23 / task constraints |
| R11 | brain version bump from 1.2.0 to 1.3.0 | Issue #23 / task constraints |
| R12 | Complete test spec table for Roz (T-0026-NNN series) | Issue #23 / task constraints |
| R13 | Backward compatibility: existing captures without provenance fields continue working | Implied by optional fields |

**Retro risks:**

- **Lesson #001 (Sensitive Data in Return Shapes):** `evidence` contains file paths
  and line numbers. These are not sensitive, but the agent_capture response shape and
  atelier_trace response shape must be explicitly specified to avoid leaking unintended
  fields. The Data Sensitivity table below tags all methods.
- **Lesson #005 (Frontend Wiring Omission):** Every producer (new Zod params, new
  atelier_trace output fields, superseded_by lookup) must have at least one consumer
  in the same or an earlier step. The Wiring Coverage section below verifies this.

**Spec challenge:** The spec assumes `thought_type: decision` captures will include
structured provenance fields. If wrong -- because the brain-extractor (ADR-0024/0025)
generates decision captures mechanically without human review, and agents no longer
call agent_capture directly (ADR-0025 R12) -- then the provenance fields will be
empty on most captures. If wrong, the design fails because the structured fields
exist but are never populated, making the feature dead on arrival.

**Mitigation:** The provenance fields are designed for two population paths:
(1) the brain-extractor can parse Cal's ADR output which already contains
`## Alternatives Considered`, `decided_by` in DoD, and file:line evidence --
a future brain-extractor enhancement can populate these mechanically, and
(2) the hydrator can populate `decided_by` for Eva's state-file-derived
decisions. The fields are useful immediately for any direct agent_capture
call (devops captures, seed captures, manual brain operations via REST API)
and become more valuable as extraction improves. Zero population is not a
failure mode -- it is the graceful degradation path.

**SPOF:** The metadata JSONB column (the storage choice, justified below).
Failure mode: a malformed JSONB object in metadata could cause agent_capture
to fail if Zod validation rejects nested shapes. Graceful degradation:
provenance fields are optional at the Zod level; if an agent passes invalid
shapes, the capture proceeds without provenance (fields omitted, not rejected).
Validation is permissive on read (extract what exists, ignore what does not)
and strict-optional on write (validate shape when present, accept absence).

**Anti-goals:**

1. Anti-goal: Enforcing provenance on all decision captures. Reason: ADR-0025
   eliminated direct agent_capture calls. The brain-extractor and hydrator
   produce captures mechanically. Requiring provenance would either break
   these mechanical paths or require complex extraction logic for fields
   that may not be parseable from agent output. Revisit: When brain-extractor
   gains per-field structured extraction for Cal output (parsing Alternatives
   Considered sections).

2. Anti-goal: Adding provenance columns to the thoughts table. Reason:
   Provenance is a metadata concern specific to `thought_type: decision`.
   Adding columns to the thoughts table would add NULL columns to 10 other
   thought types that never use them, complicating schema maintenance and
   bloating row size. The metadata JSONB column already exists, is GIN-indexed,
   and is the canonical extension point. Revisit: When provenance query
   patterns show that JSONB extraction is a performance bottleneck (requires
   evidence from production query plans).

3. Anti-goal: Building a standalone provenance audit trail table. Reason:
   The thought_relations table already models the supersession graph. Adding
   a separate provenance table would duplicate the decision lineage that
   thought_relations already captures and create two sources of truth for
   "what superseded what." Revisit: When provenance needs to track changes
   within a single thought (edit history), which thought_relations cannot model.

---

## Status

Proposed

**Extends:** `brain/lib/tools.mjs` (agent_capture parameters, atelier_trace
output), `brain/lib/config.mjs` (no enum changes needed), `brain/schema.sql`
(documentation only -- no DDL changes).

## Context

The Atelier Brain stores free-text thoughts with semantic search and a typed
relation graph. Decisions are captured but lack structured provenance: no
record of who decided, what alternatives were rejected, what file evidence
supported the decision, or how confident the agent was. This makes the brain
useful for "what was decided" but not "why was it decided" or "what else was
considered."

The Beads pattern (structured decision records with queryable provenance)
makes decisions auditable and SQL-addressable. Instead of grepping through
free-text content for "we considered X but rejected it because Y," consumers
can query `metadata->'provenance'->'alternatives_rejected'` directly.

### Current State

- `agent_capture` accepts an open `metadata` JSONB field but provides no
  schema guidance for provenance data
- `atelier_trace` traverses the relation graph but returns only the base
  thought fields (content, thought_type, source_agent, etc.) without
  extracting or surfacing metadata substructure
- `supersedes_id` already creates forward supersession relations and marks
  targets as superseded, but there is no reverse lookup ("who superseded me?")
- The `thoughts.metadata` column has a GIN index (`thoughts_metadata_idx`)
  that supports `@>` containment queries on JSONB

### Why JSONB Metadata (Not New Columns)

**Option A: New columns on `thoughts` table** -- `decided_by JSONB`,
`alternatives_rejected JSONB`, `evidence JSONB`, `confidence FLOAT`.

Pros: direct SQL queries (`SELECT confidence FROM thoughts WHERE ...`),
type enforcement at the DB level, simpler indexing.

Cons: four new nullable columns on every row for 10 thought types that
never use them (decision is 1 of 11 types); requires Migration 007 with
DDL changes; every new provenance field requires another migration; the
`confidence` column would shadow the existing `importance` column semantically.

**Option B: Nested JSONB within existing `metadata` column** -- provenance
fields stored as `metadata.provenance.{field}`.

Pros: zero schema migration (the metadata column and its GIN index already
exist); extensible without DDL (new provenance fields are just new keys);
NULL-free (absent keys, not NULL columns); consistent with the existing
`metadata.quality_signals` pattern from ADR-0025.

Cons: no DB-level type enforcement (Zod validates on write, application
validates on read); JSONB path extraction is slightly slower than direct
column access; provenance fields are invisible to `\d thoughts`.

**Decision: Option B (JSONB metadata).** The metadata column is the
established extension point (ADR-0025 uses it for quality_signals). Provenance
is specific to decisions and would impose schema bloat on all other types.
The GIN index supports containment queries. Zod provides write-time
validation. Read-time extraction is permissive (return what exists).

### Why Extend atelier_trace (Not a New Tool)

A new `atelier_provenance` tool would do two things: (1) surface structured
provenance metadata for a thought, and (2) look up `superseded_by` reverse
references. Both of these are graph traversal operations that atelier_trace
already performs.

Adding a seventh MCP tool increases the tool surface area that every MCP
client must discover and learn. The existing atelier_trace tool already
accepts a `thought_id` and traverses relations. Extending it to also return
provenance metadata and superseded_by data keeps the tool count at six and
makes provenance a natural part of tracing a decision's lineage.

The extension is: when atelier_trace returns a thought node in its chain, it
now also includes `provenance` (extracted from metadata) and `superseded_by`
(computed from a forward-direction relation query on the target thought).

## Decision

### 1. Extend agent_capture with Provenance Parameters

Add four optional parameters to agent_capture, validated by Zod. These
parameters are accepted for any thought_type but are semantically meaningful
only for `decision` captures. No server-side enforcement restricts them to
decisions -- the convention is documented, and the brain-extractor/agents
follow it.

**New Zod parameters (all optional):**

```javascript
// Added to the existing agent_capture schema in registerAgentCapture()
decided_by: z.object({
  agent: z.string(),
  human_approved: z.boolean(),
}).optional().describe("Who made the decision and whether a human signed off"),

alternatives_rejected: z.array(z.object({
  alternative: z.string(),
  reason: z.string(),
})).optional().describe("Alternatives considered and why rejected"),

evidence: z.array(z.object({
  file: z.string(),
  line: z.number().int().positive(),
})).optional().describe("File:line references supporting the decision"),

confidence: z.number().min(0).max(1).optional()
  .describe("Decision confidence 0-1; low values flag for retro review"),
```

**Storage:** These fields are merged into `metadata.provenance` before
insertion. The existing `metadata` parameter continues to work as before.
The merge logic in `handleAgentCapture`:

```javascript
// After destructuring params, before insertThought:
const provenanceFields = {};
if (decided_by) provenanceFields.decided_by = decided_by;
if (alternatives_rejected?.length) provenanceFields.alternatives_rejected = alternatives_rejected;
if (evidence?.length) provenanceFields.evidence = evidence;
if (confidence !== undefined) provenanceFields.confidence = confidence;

const enrichedMetadata = Object.keys(provenanceFields).length > 0
  ? { ...metadata, provenance: provenanceFields }
  : metadata;
```

**Queryability:** The existing GIN index on `metadata` supports:
```sql
-- Find decisions with alternatives_rejected
SELECT * FROM thoughts WHERE metadata @> '{"provenance": {"alternatives_rejected": [{}]}}';

-- Find decisions by a specific agent
SELECT * FROM thoughts WHERE metadata @> '{"provenance": {"decided_by": {"agent": "cal"}}}';

-- Find low-confidence decisions (requires extraction, not containment)
SELECT * FROM thoughts WHERE (metadata->'provenance'->>'confidence')::float < 0.5;
```

### 2. Extend atelier_trace with Provenance and Superseded-By

**Provenance surfacing:** When atelier_trace returns thought nodes in its
chain, each node now includes a `provenance` field extracted from
`metadata->'provenance'`. If the key does not exist, the field is `null`.

**Superseded_by reverse lookup:** For each thought in the chain, atelier_trace
runs a single additional query to find thoughts that supersede it:

```sql
SELECT source_id FROM thought_relations
WHERE target_id = $1 AND relation_type = 'supersedes'
```

This returns the UUID(s) of thoughts that superseded the target thought.
The result is included as `superseded_by: [uuid, ...]` on each chain node.
Empty array if not superseded.

**Updated chain node shape:**

```javascript
{
  id, content, thought_type, source_agent, source_phase, importance,
  status, scope, captured_by, created_at,
  depth, via_relation, via_context, direction,
  // New fields:
  provenance: { decided_by, alternatives_rejected, evidence, confidence } | null,
  superseded_by: [uuid, ...],  // empty array if none
}
```

**Performance:** The superseded_by lookup adds one query per unique thought
in the chain. For typical chains (depth <= 10), this is at most 10 additional
simple index-scanned queries. For larger chains, the `relations_target_idx`
index on `thought_relations(target_id)` ensures O(log n) per lookup.

**Optimization for batch:** Instead of per-node queries, collect all thought
IDs from the chain and run a single batch query:

```sql
SELECT target_id, array_agg(source_id) AS superseded_by
FROM thought_relations
WHERE target_id = ANY($1) AND relation_type = 'supersedes'
GROUP BY target_id
```

This reduces the superseded_by lookup to one query regardless of chain size.

### 3. Migration 007: No-Op

No DDL changes required. The `metadata` column and its GIN index already
exist. The provenance fields are stored within the existing JSONB structure.
The migration file is created as a no-op placeholder to maintain the
sequential numbering convention and document the design decision.

```sql
-- Migration 007: Beads-style provenance (ADR-0026)
-- No DDL changes required. Provenance fields are stored in the existing
-- metadata JSONB column. This file documents the design decision.
-- See: docs/architecture/ADR-0026-beads-provenance-records.md
```

The `db.mjs` migration runner gains a Migration 007 block that checks a
simple sentinel (e.g., a comment log) and exits immediately. This follows
the convention of migrations 001-006 but has no effect on the database.

**Alternatively:** Skip the migration file entirely and bump the version
without a DDL migration. Both approaches are valid; the no-op file is
preferred for auditability (the migration sequence documents that ADR-0026
was considered and required no schema change).

### 4. Version Bump

`brain/package.json` version: `1.2.0` -> `1.3.0`. This is a minor version
bump (new features, backward compatible).

### 5. Capture Convention for Agents

When an agent (or the brain-extractor) captures a decision with provenance,
the convention is:

| Field | Population Source | Example |
|-------|-------------------|---------|
| `decided_by` | Agent identity + whether user approved | `{agent: "cal", human_approved: false}` |
| `alternatives_rejected` | Cal's "Alternatives Considered" section, Colby's rejected approaches | `[{alternative: "WebSocket sync", reason: "Serverless platform has no persistent connections"}]` |
| `evidence` | File:line references from code, tests, or config that support the decision | `[{file: "brain/lib/tools.mjs", line: 36}]` |
| `confidence` | Self-assessed confidence; 1.0 = certain, 0.5 = reasonable, < 0.3 = flag for retro | `0.8` |

**Confidence degradation convention:** When a decision's confidence is below
0.3, it should be flagged in retro-lessons.md review. Consumers (Eva, Darwin)
can query for low-confidence decisions:
```sql
SELECT * FROM thoughts
WHERE thought_type = 'decision'
  AND (metadata->'provenance'->>'confidence')::float < 0.3
  AND status = 'active';
```

**Brain-extractor integration (future, not this ADR):** The brain-extractor
could parse Cal's ADR output to extract `alternatives_rejected` from the
`## Alternatives Considered` section and `evidence` from file references in
the implementation plan. This is a natural extension of ADR-0025's structured
signal extraction pattern but is out of scope for ADR-0026.

## Alternatives Considered

**Alternative A: Provenance as top-level columns.** Four new columns on the
thoughts table. Rejected: schema bloat for 10 non-decision thought types,
requires DDL migration for every new provenance field, and the existing JSONB
metadata approach is the established extension pattern (ADR-0025 precedent).

**Alternative B: New `atelier_provenance` MCP tool.** A dedicated tool for
provenance queries. Rejected: adds tool surface area (7th tool), duplicates
atelier_trace's graph traversal, and consumers must learn a new tool for
what is fundamentally a "tell me more about this thought" query that
atelier_trace already answers.

**Alternative C: Store superseded_by as a materialized view.** A PostgreSQL
view or materialized view that pre-computes the reverse supersession lookup.
Rejected: premature optimization -- the batch query approach (single query
with `ANY($1)`) is sufficient for chain sizes under 50. A materialized view
adds refresh complexity. Revisit if chain sizes regularly exceed 50 nodes.

**Alternative D: Strict type enforcement -- reject provenance fields on
non-decision types.** The Zod schema would conditionally require
`thought_type: 'decision'` when provenance fields are present. Rejected:
adds brittle coupling between thought_type and parameter validation. Some
`preference` or `lesson` captures may legitimately carry evidence or
confidence. The convention documents the intended usage; enforcement adds
friction without proportional safety.

## Consequences

**Positive:**
- Decisions become auditable: who decided, what was considered, what evidence
  supports it, how confident the capture is
- `superseded_by` reverse lookup closes the "who replaced me?" gap without
  schema changes
- Zero-migration approach: no DDL changes, no rollback risk, no migration
  coordination
- Backward compatible: existing captures without provenance continue working
  unchanged
- Follows the established JSONB metadata extension pattern (ADR-0025
  quality_signals precedent)

**Negative:**
- No DB-level type enforcement on provenance structure; relies on Zod for
  write-time validation and permissive read-time extraction
- atelier_trace response size increases slightly (provenance object +
  superseded_by array per node)
- Provenance fields will be empty on most existing and mechanically-captured
  decisions until brain-extractor gains provenance extraction (future ADR)

---

## Implementation Plan

### Step 1: Extend agent_capture with Provenance Parameters

**Files:**
- `brain/lib/tools.mjs` (modify: add Zod params, merge provenance into metadata)
- `brain/lib/config.mjs` (no changes -- no new enums needed)

After this step, I can capture a decision with `decided_by`, `alternatives_rejected`,
`evidence`, and `confidence` fields, and they are stored in `metadata.provenance`.

**What to do:**

1. Add four new optional Zod parameters to the `agent_capture` tool registration
   in `registerAgentCapture()` (the schema object at line 41-50 of tools.mjs):
   `decided_by`, `alternatives_rejected`, `evidence`, `confidence` -- shapes
   as specified in the Decision section above.

2. In `handleAgentCapture()` (line 55), destructure the four new params from
   the params object.

3. After the metadata destructuring (line 57) and before the `insertThought`
   call (line 83), build a `provenanceFields` object from whichever new params
   are present. Merge it into `metadata` as `metadata.provenance` only when
   at least one provenance field is provided. Pass the enriched metadata to
   `insertThought`.

4. The agent_capture response (line 93-101) does not change shape. The
   provenance data is persisted in metadata; consumers retrieve it via
   atelier_trace or agent_search.

**Acceptance criteria:**
- agent_capture accepts `decided_by`, `alternatives_rejected`, `evidence`,
  and `confidence` as optional parameters
- Zod validates shapes: `decided_by` is `{agent: string, human_approved: boolean}`,
  `alternatives_rejected` is `[{alternative: string, reason: string}]`,
  `evidence` is `[{file: string, line: int>0}]`, `confidence` is `number 0-1`
- Provenance fields are stored in `metadata.provenance` (not at metadata root)
- When no provenance fields are provided, `metadata` is unchanged (no empty
  `provenance` key)
- Existing captures without provenance fields continue to work (backward compat)
- The `metadata` parameter continues to accept arbitrary keys alongside provenance

**Complexity:** Low. Four optional Zod params + 10 lines of merge logic.

---

### Step 2: Extend atelier_trace with Provenance and Superseded-By

**Files:**
- `brain/lib/tools.mjs` (modify: atelier_trace response enrichment)

After this step, I can trace a decision and see its provenance metadata and
which thoughts superseded it.

**What to do:**

1. In `registerAtelierTrace()` (line 448), after the chain is built and sorted
   (line 478), add two enrichment passes before returning the response:

   a. **Provenance extraction:** For each node in the chain, extract
      `node.provenance = node.metadata?.provenance || null`. Then delete
      `node.metadata` from the response to keep the chain lean (metadata
      can be large; provenance is the structured subset consumers want).
      Actually -- the chain query at lines 459 and 489-503 does not currently
      SELECT metadata. Add `t.metadata` to the SELECT list in the root query
      (line 459), the backward recursive CTE (lines 490-503), and the forward
      recursive CTE (lines 516-530). Then extract provenance from metadata
      on each node and include it in the response. Drop the raw metadata
      from the response node to avoid bloat.

   b. **Superseded_by batch lookup:** Collect all thought IDs from the chain.
      Run a single batch query:
      ```sql
      SELECT target_id, array_agg(source_id) AS superseded_by
      FROM thought_relations
      WHERE target_id = ANY($1) AND relation_type = 'supersedes'
      GROUP BY target_id
      ```
      Build a Map from target_id to superseded_by array. For each chain node,
      set `node.superseded_by = map.get(node.id) || []`.

2. The updated chain node shape includes `provenance` (object or null) and
   `superseded_by` (array of UUIDs, possibly empty).

**Acceptance criteria:**
- atelier_trace chain nodes include `provenance` field (object when present,
  null when absent)
- atelier_trace chain nodes include `superseded_by` field (array of UUIDs)
- Superseded_by is computed from thought_relations (not a stored column)
- Superseded_by uses a single batch query, not per-node queries
- Existing thoughts without provenance return `provenance: null`
- Thoughts not superseded return `superseded_by: []`
- The root query, backward CTE, and forward CTE all SELECT metadata for
  provenance extraction

**Complexity:** Medium. CTE modifications + batch query + response enrichment.

---

### Step 3: Migration 007 (No-Op) + Version Bump + db.mjs Runner

**Files:**
- `brain/migrations/007-beads-provenance-noop.sql` (create)
- `brain/lib/db.mjs` (modify: add Migration 007 block)
- `brain/package.json` (modify: version 1.2.0 -> 1.3.0)

After this step, the brain server starts cleanly with migration 007 logged
and the package version reflects the new feature.

**What to do:**

1. Create `brain/migrations/007-beads-provenance-noop.sql` with a comment-only
   body explaining that ADR-0026 requires no DDL changes.

2. In `brain/lib/db.mjs`, add a Migration 007 block after the Migration 006
   block (line 177). The check is trivial: log a message and skip. The block
   follows the same try/catch pattern as migrations 001-006 but performs no
   database operations.

   ```javascript
   // Migration 007: Beads provenance (ADR-0026) -- no DDL changes
   try {
     console.log("Migration 007: Beads provenance -- no DDL changes needed (metadata JSONB).");
   } catch (err) {
     console.error("Migration 007 failed (non-fatal):", err.message);
   }
   ```

3. Bump `brain/package.json` version from `1.2.0` to `1.3.0`.

**Acceptance criteria:**
- `brain/migrations/007-beads-provenance-noop.sql` exists with ADR reference
- `brain/lib/db.mjs` contains Migration 007 block
- `brain/package.json` version is `1.3.0`
- Brain server starts without errors after migration runner executes 007

**Complexity:** Low. One new file (comment-only), two small modifications.

---

## Test Specification

Tests extend `tests/brain/tools.test.mjs`, continuing from T-0003-102.
New test IDs: T-0026-001 through T-0026-028.

| ID | Category | Description | Happy / Failure |
|----|----------|-------------|-----------------|
| T-0026-001 | agent_capture / provenance | agent_capture with all four provenance fields stores them in `metadata.provenance` | Happy path |
| T-0026-002 | agent_capture / provenance | agent_capture with `decided_by` only stores `metadata.provenance.decided_by`; no other provenance keys present | Happy path |
| T-0026-003 | agent_capture / provenance | agent_capture with `alternatives_rejected` only stores array in `metadata.provenance.alternatives_rejected` | Happy path |
| T-0026-004 | agent_capture / provenance | agent_capture with `evidence` only stores array in `metadata.provenance.evidence` | Happy path |
| T-0026-005 | agent_capture / provenance | agent_capture with `confidence` only stores number in `metadata.provenance.confidence` | Happy path |
| T-0026-006 | agent_capture / backward compat | agent_capture without any provenance fields does not add `provenance` key to metadata | Failure path: regression -- empty provenance object injected |
| T-0026-007 | agent_capture / backward compat | agent_capture with existing `metadata` keys preserves them alongside `provenance` | Happy path |
| T-0026-008 | agent_capture / validation | agent_capture rejects `decided_by` missing `agent` field (Zod validation) | Failure path |
| T-0026-009 | agent_capture / validation | agent_capture rejects `decided_by` missing `human_approved` field (Zod validation) | Failure path |
| T-0026-010 | agent_capture / validation | agent_capture rejects `confidence` outside 0-1 range (e.g., 1.5) | Failure path |
| T-0026-011 | agent_capture / validation | agent_capture rejects `confidence` below 0 (e.g., -0.1) | Failure path |
| T-0026-012 | agent_capture / validation | agent_capture rejects `evidence` with non-positive line number (e.g., 0 or -1) | Failure path |
| T-0026-013 | agent_capture / validation | agent_capture rejects `alternatives_rejected` with missing `reason` field | Failure path |
| T-0026-014 | agent_capture / provenance | agent_capture with empty `alternatives_rejected` array ([]) does not store provenance key (treated as absent) | Failure path: regression -- empty array stored |
| T-0026-015 | agent_capture / provenance | agent_capture with empty `evidence` array ([]) does not store provenance key (treated as absent) | Failure path: regression -- empty array stored |
| T-0026-016 | atelier_trace / provenance | atelier_trace on a thought with `metadata.provenance` returns provenance in chain node | Happy path |
| T-0026-017 | atelier_trace / provenance | atelier_trace on a thought without `metadata.provenance` returns `provenance: null` in chain node | Failure path: graceful degradation |
| T-0026-018 | atelier_trace / superseded_by | atelier_trace on a superseded thought returns `superseded_by` array with superseding thought's UUID | Happy path |
| T-0026-019 | atelier_trace / superseded_by | atelier_trace on a non-superseded thought returns `superseded_by: []` (empty array) | Failure path: graceful degradation |
| T-0026-020 | atelier_trace / superseded_by | atelier_trace on a thought superseded by multiple thoughts returns all superseding UUIDs | Happy path |
| T-0026-021 | atelier_trace / batch query | atelier_trace with chain depth > 1 executes superseded_by as a single batch query (not per-node) | Happy path: performance |
| T-0026-022 | atelier_trace / combined | atelier_trace returns both provenance and superseded_by on the same chain node | Happy path: integration |
| T-0026-023 | agent_capture / validation | agent_capture rejects `evidence` with missing `file` field (Zod validation) | Failure path |
| T-0026-024 | agent_capture / validation | agent_capture rejects `alternatives_rejected` with missing `alternative` field | Failure path |
| T-0026-025 | agent_capture / provenance merge | agent_capture with both `metadata.provenance` (raw) and explicit provenance params: explicit params overwrite raw metadata.provenance | Failure path: merge precedence regression |
| T-0026-026 | migration 007 | brain/migrations/007-beads-provenance-noop.sql exists and contains ADR-0026 reference | Happy path |
| T-0026-027 | version bump | brain/package.json version is 1.3.0 | Happy path |
| T-0026-028 | agent_capture / validation | `agent_capture` rejects `evidence` entry with a float line number (e.g., `line: 1.5`) -- Zod `.int()` constraint | Failure path |

**Test ID mapping to steps:**
- T-0026-001 through T-0026-015, T-0026-023 through T-0026-025, T-0026-028: Step 1 (agent_capture provenance)
- T-0026-016 through T-0026-022: Step 2 (atelier_trace extension)
- T-0026-026 through T-0026-027: Step 3 (migration + version)

**Failure-to-happy ratio:** 15 failure / 13 happy = 1.15. Meets the >= 1.0
target. The validation tests (T-0026-008 through T-0026-015, T-0026-023
through T-0026-025, T-0026-028) are heavily weighted toward failure paths
because Zod boundary validation and merge precedence are where bugs hide.

**Note:** T-0026-008 through T-0026-013 test Zod schema validation. In the
existing test pattern (T-0003-088), schema validation is tested by inspecting
the registered schema object rather than calling the handler, because the MCP
SDK validates params before the handler is invoked. The new tests should follow
the same pattern: verify the Zod schema rejects invalid shapes using Zod's
`.safeParse()` method on the schema object, rather than calling the handler
with invalid params.

---

## UX Coverage

Not applicable. This ADR is pure brain infrastructure with no user-facing
surfaces. The provenance data is consumed by agents (Eva, Darwin) and the
brain REST API/UI, not by end users directly.

---

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| agent_capture (provenance params) | `{ decided_by?: {agent, human_approved}, alternatives_rejected?: [{alternative, reason}], evidence?: [{file, line}], confidence?: number }` | Brain DB (stored in metadata.provenance) |
| Brain DB (metadata.provenance) | `{ decided_by?, alternatives_rejected?, evidence?, confidence? }` | atelier_trace (extracted per chain node) |
| atelier_trace (superseded_by) | `superseded_by: uuid[]` | Eva, Darwin, brain UI (consumers of trace output) |
| thought_relations (supersedes) | `{source_id, target_id, relation_type: 'supersedes'}` | atelier_trace batch query (reverse lookup) |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| agent_capture Zod params | `decided_by`, `alternatives_rejected`, `evidence`, `confidence` (optional objects/arrays/number) | `handleAgentCapture` merge logic -> `metadata.provenance` | Step 1 |
| `handleAgentCapture` merge logic | `enrichedMetadata` with `provenance` key | `insertThought` (existing function, no changes needed) | Step 1 |
| `insertThought` | Row in `thoughts` table with `metadata.provenance` in JSONB | `atelier_trace` provenance extraction | Step 1 -> Step 2 |
| atelier_trace root/CTE queries | `t.metadata` column in SELECT | Provenance extraction loop post-chain-build | Step 2 |
| atelier_trace batch superseded_by query | `{target_id, superseded_by[]}` | Chain node enrichment loop | Step 2 |
| Chain node enrichment | `{...node, provenance, superseded_by}` | MCP response to caller | Step 2 |

All producers have consumers. No orphan endpoints.

---

## Data Sensitivity

| Method | Tag | Rationale |
|--------|-----|-----------|
| `agent_capture` (provenance params) | `public-safe` | Provenance contains agent names, alternative descriptions, file paths, and confidence scores. No secrets, no credentials, no PII. File paths are project-relative source paths. |
| `atelier_trace` (provenance + superseded_by) | `public-safe` | Returns the same provenance data plus UUIDs. No sensitive fields. |
| `agent_search` (unchanged) | `public-safe` | Returns metadata which may now contain provenance. Same sensitivity as existing metadata exposure. |
| `atelier_browse` (unchanged) | `public-safe` | Does not return metadata in its current SELECT list (line 286). No change needed. |

---

## State Transition Table

No new status fields or state machines introduced. The existing `thought_status`
enum (`active`, `superseded`, `invalidated`, `expired`, `conflicted`) is unchanged.
The `superseded_by` reverse lookup reads from the existing `thought_relations`
table without modifying any status transitions.

**Existing supersession flow (unchanged):**
```
active --[supersedes relation created]--> superseded (invalidated_at set)
```

**New capability (read-only):**
```
Given thought T with status=superseded:
  atelier_trace(T) now returns superseded_by: [U1, U2, ...]
  where U1, U2 are the source_ids of supersedes relations targeting T
```

No stuck states possible. The superseded_by array is a computed read, not a
state transition.

---

## Rollback Strategy

**Rollback scope:** Code-only (tools.mjs, db.mjs, package.json). No DDL to
reverse.

**Rollback procedure:** Revert the three modified files to their pre-ADR-0026
state. The migration 007 no-op SQL file can remain (it does nothing).
Existing captures with `metadata.provenance` data remain in the database but
are simply ignored by the reverted atelier_trace (which does not extract the
key).

**Rollback window:** Immediate. No data migration to reverse, no schema to
drop, no dependent services to coordinate.

**Data cleanup (optional, not required for rollback):** If provenance metadata
should be removed from existing captures:
```sql
UPDATE thoughts
SET metadata = metadata - 'provenance'
WHERE metadata ? 'provenance';
```

---

## Notes for Colby

1. **Zod validation happens before the handler.** The MCP SDK calls
   `schema.parse(params)` before invoking the handler function. Colby does not
   need to add try/catch for Zod errors in `handleAgentCapture` -- the SDK
   handles that. The Zod schema definition IS the validation.

2. **The `metadata` param merge order matters.** If a caller passes both
   `metadata: { provenance: { custom: true } }` and `decided_by: {agent: "cal", human_approved: false}`,
   the explicit provenance fields should WIN (overwrite metadata.provenance).
   Merge order: start with caller's metadata, then overwrite `.provenance`
   with the structured provenance fields. This prevents callers from
   bypassing Zod validation by stuffing unvalidated provenance into the
   raw metadata object.

3. **Empty arrays mean absent.** `alternatives_rejected: []` and `evidence: []`
   should be treated as "no provenance" (do not store an empty array). Check
   `.length > 0` before including in the provenance object.

4. **The atelier_trace CTE queries need metadata added to SELECT.** The root
   query (line 459), backward CTE (lines 490-503), and forward CTE
   (lines 516-530) all need `t.metadata` in their SELECT lists. Currently
   they select specific columns but not metadata.

5. **The superseded_by batch query goes AFTER chain construction, BEFORE
   sorting.** The chain array is fully built (root + backward + forward),
   then enriched with provenance + superseded_by, then sorted by depth.
   Do not try to interleave the batch query into the recursive CTEs.

6. **Existing test pattern for Zod validation (T-0003-088).** The test
   inspects the schema object, not the handler. New validation tests
   (T-0026-008 through T-0026-013) should use `schema.decided_by.safeParse()`
   or equivalent Zod methods to verify rejection. The Zod schema is
   accessible from `srv.tools.get('agent_capture').schema`.

7. **brain/package.json version bump is a single-line edit.** Change
   `"version": "1.2.0"` to `"version": "1.3.0"`. No other version files
   need updating for the brain subpackage.

8. **Proven pattern: ADR-0025 metadata extension.** The `metadata.quality_signals`
   pattern from ADR-0025 (Step 1, line 119 of the ADR) stores structured data
   in metadata JSONB without schema changes. This ADR follows the identical
   pattern with `metadata.provenance`.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | `decided_by` field in agent_capture | Done | Step 1: Zod schema addition, merge logic |
| R2 | `alternatives_rejected` field in agent_capture | Done | Step 1: Zod schema addition, merge logic |
| R3 | `evidence` field in agent_capture | Done | Step 1: Zod schema addition, merge logic |
| R4 | `confidence` field in agent_capture | Done | Step 1: Zod schema addition, merge logic |
| R5 | All provenance fields optional, decision-only convention | Done | Zod `.optional()` on all four; convention documented in Decision section |
| R6 | `superseded_by` reverse lookup as computed query | Done | Step 2: batch query on thought_relations, not stored column |
| R7 | Extend atelier_trace with provenance + superseded_by | Done | Step 2: chain node enrichment |
| R8 | Storage decision: JSONB metadata, justified | Done | Decision section: Option B with trade-off analysis |
| R9 | Migration 007 | Done | Step 3: no-op SQL file + db.mjs runner block |
| R10 | Capture convention documented | Done | Decision section 5: table + confidence degradation convention |
| R11 | brain version bump to 1.3.0 | Done | Step 3: package.json edit |
| R12 | Test spec table for Roz | Done | T-0026-001 through T-0026-028 (28 tests) |
| R13 | Backward compatibility | Done | T-0026-006 (no empty provenance key), T-0026-007 (existing metadata preserved), T-0026-017 (provenance: null graceful), T-0026-019 (superseded_by: [] graceful) |

**Grep check:** TODO/FIXME/HACK/XXX in this document -> 0
**Template:** All sections filled -- no TBD, no placeholders
