# Brain Provenance Fields

Reference for the four provenance fields added to `agent_capture` in ADR-0026. These fields make
`decision` captures auditable: who decided, what alternatives were considered, what code evidence
supported the decision, and how confident the capture is.

**Introduced in:** ADR-0026 (Beads-style provenance), brain v1.3.0

---

## When to Use Provenance Fields

Provenance fields are accepted on any `thought_type` but are semantically meaningful only on
`thought_type: decision`. They are all optional. Existing captures without provenance continue
working unchanged.

Populate provenance when:
- Cal records an architectural decision (all four fields apply)
- Eva captures a gate-triggered decision (at minimum `decided_by` and `confidence`)
- The brain-extractor or hydrator mechanically extracts a decision from an ADR or state file

Do not populate provenance on `lesson`, `preference`, `pattern`, or other thought types unless
there is a specific reason to record evidence or confidence on those types.

---

## Field Reference

### `decided_by`

Who made the decision and whether a human approved it.

| Property | Type | Required |
|----------|------|----------|
| `agent` | `string` | yes |
| `human_approved` | `boolean` | yes |

- `agent`: the source agent identifier (`cal`, `eva`, `colby`, etc.)
- `human_approved`: `true` when the user explicitly signed off on this decision during the pipeline
  run; `false` for agent-autonomous decisions (tool selection, implementation approach) that were
  not surfaced for human approval

---

### `alternatives_rejected`

Alternatives that were considered and why they were not chosen. Maps directly to the
"Alternatives Considered" section in Cal's ADRs.

Each element:

| Property | Type | Required |
|----------|------|----------|
| `alternative` | `string` | yes |
| `reason` | `string` | yes |

An empty array is not stored (the field is omitted if no alternatives were captured).

---

### `evidence`

File and line references that support the decision. Points reviewers and future agents to the
code, config, or test that substantiates the decision.

Each element:

| Property | Type | Required |
|----------|------|----------|
| `file` | `string` | yes — relative path from project root |
| `line` | `integer > 0` | yes |

An empty array is not stored.

---

### `confidence`

Self-assessed confidence in the decision, on a 0–1 scale.

| Value | Meaning |
|-------|---------|
| `1.0` | Certain — backed by tests, spec, and evidence |
| `0.8` | High — well-reasoned, minor unknowns |
| `0.5` | Moderate — reasonable approach, some risk |
| `< 0.3` | Low — flag for retro review |

Decisions with `confidence < 0.3` should be reviewed at retro. Eva and Darwin can query for
them (see Querying Provenance below).

---

## Storage

Provenance fields are stored inside the existing `metadata` JSONB column under the
`metadata.provenance` key. No DDL migration is required (Migration 007 is a no-op). The GIN index
on `metadata` supports containment queries on provenance fields.

The `metadata` parameter to `agent_capture` continues to accept arbitrary keys alongside
provenance. If no provenance fields are provided, the `provenance` key is absent from metadata
entirely.

---

## Example: `agent_capture` Call with Provenance

```javascript
agent_capture({
  thought_type: "decision",
  content: "Use JSONB metadata column for provenance storage rather than new columns on the thoughts table.",
  source_agent: "cal",
  source_phase: "architecture",
  importance: 0.85,
  scope: "atelier-pipeline",
  supersedes_id: null,

  // Provenance fields
  decided_by: {
    agent: "cal",
    human_approved: true
  },
  alternatives_rejected: [
    {
      alternative: "New columns on thoughts table (decided_by, alternatives_rejected, evidence, confidence)",
      reason: "Four nullable columns on every row for 10 thought types that never use them. Schema bloat and a DDL migration for every new provenance field."
    },
    {
      alternative: "Standalone provenance audit table",
      reason: "Duplicates the decision lineage already captured by thought_relations. Two sources of truth for supersession."
    }
  ],
  evidence: [
    { file: "brain/lib/tools.mjs", line: 41 },
    { file: "brain/schema.sql", line: 12 }
  ],
  confidence: 0.9
})
```

The four provenance fields are merged into `metadata.provenance` before insertion. The
`agent_capture` response shape is unchanged.

---

## `atelier_trace` Response: Provenance and Superseded-By

`atelier_trace` chain nodes now include two additional fields on every node:

```javascript
{
  // Existing fields
  id,
  content,
  thought_type,
  source_agent,
  source_phase,
  importance,
  status,
  scope,
  captured_by,
  created_at,
  depth,
  via_relation,
  via_context,
  direction,

  // New fields (ADR-0026)
  provenance: {
    decided_by:            { agent: string, human_approved: boolean } | undefined,
    alternatives_rejected: [{ alternative: string, reason: string }] | undefined,
    evidence:              [{ file: string, line: number }]           | undefined,
    confidence:            number                                      | undefined
  } | null,   // null when no provenance was captured for this thought

  superseded_by: [uuid, ...]  // empty array when this thought has not been superseded
}
```

- `provenance` is `null` for thoughts captured before v1.3.0 or without provenance fields.
  It is never an empty object.
- `superseded_by` is computed from `thought_relations` (not a stored column). It contains the
  UUIDs of thoughts that supersede this one. The forward `supersedes_id` field on the superseding
  thought is the complement: `superseding.supersedes_id === superseded.id`.

---

## Querying Provenance Directly

The GIN index on `metadata` supports `@>` containment queries.

```sql
-- Decisions with alternatives_rejected captured
SELECT * FROM thoughts
WHERE metadata @> '{"provenance": {"alternatives_rejected": [{}]}}';

-- Decisions made by Cal
SELECT * FROM thoughts
WHERE metadata @> '{"provenance": {"decided_by": {"agent": "cal"}}}';

-- Human-approved decisions
SELECT * FROM thoughts
WHERE metadata @> '{"provenance": {"decided_by": {"human_approved": true}}}';

-- Low-confidence decisions flagged for retro (confidence < 0.3)
SELECT id, content, source_agent, created_at
FROM thoughts
WHERE thought_type = 'decision'
  AND status = 'active'
  AND (metadata->'provenance'->>'confidence')::float < 0.3;
```

---

## Backward Compatibility

Existing captures without provenance fields are unaffected. The fields are optional at both the
Zod layer (write-time) and the extraction layer (read-time). `atelier_trace` returns
`provenance: null` and `superseded_by: []` for thoughts that predate v1.3.0.

---

## Population Paths

Two paths produce provenance-rich captures today:

1. **Direct `agent_capture` call** -- Cal, Eva, or any agent passing provenance fields explicitly.
   Applies to devops captures, seed captures, and manual brain operations.
2. **Brain hydrator** -- `hydrate-telemetry.mjs` can populate `decided_by` for Eva's
   state-file-derived decisions.

A third path is planned but out of scope for ADR-0026: the **brain-extractor** parsing Cal's
ADR `## Alternatives Considered` sections to populate `alternatives_rejected` and `evidence`
mechanically. Until that extraction is implemented, those fields will be empty on
brain-extractor-produced captures.

---

## See Also

- [ADR-0026](../architecture/ADR-0026-beads-provenance-records.md) — full design record, storage
  rationale, and test spec
- [ADR-0025](../architecture/ADR-0025-mechanical-telemetry-extraction.md) — brain-extractor and
  `metadata.quality_signals` (the precedent for JSONB metadata extension)
- [ADR-0001](ADR-0001-atelier-brain.md) — brain schema, thought types, and relation types
