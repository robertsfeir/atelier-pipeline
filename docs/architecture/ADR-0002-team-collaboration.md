# ADR-0002: Team Collaboration Enhancements — Context Brief Brain Capture + Structured Handoff

## DoR: Requirements Extracted

| # | Requirement | Source | Retro Risk |
|---|---|---|---|
| R1 | Eva dual-writes context-brief entries to brain via `agent_capture` when brain is available | Feature 1, AC-1/2/3 | — |
| R2 | Captured context-brief thoughts use `thought_type: 'preference'` / `'correction'` / `'rejection'` matching entry type | Feature 1, AC-1/2/3 | — |
| R3 | All context-brief captures use `source_agent: 'eva'`, current `source_phase`, and feature scope tag | Feature 1, AC-1/3/6 | — |
| R4 | `agent_search` returns captured context-brief thoughts for teammates on the same feature | Feature 1, AC-4 | — |
| R5 | No behavioral change when brain is unavailable — `context-brief.md` writes are unaffected | Feature 1, AC-5 | — |
| R6 | Eva generates a structured handoff brief at pipeline end (Final Report) or on explicit "hand off" trigger | Feature 2, AC-1/3 | — |
| R7 | Handoff brief contains: completed work, unfinished work, key decisions, surprises, user corrections, warnings | Feature 2, AC-1/7 | — |
| R8 | Handoff brief captured via `agent_capture` with `thought_type: 'handoff'`, `source_agent: 'eva'`, `source_phase: 'handoff'` | Feature 2, AC-2 | — |
| R9 | `handoff` thought type has high default importance (same tier as `decision`), no expiry | Feature 2, AC-5 | — |
| R10 | `agent_search` returns handoff briefs for teammates on the same feature | Feature 2, AC-4 | — |
| R11 | Handoff brief references ADR step numbers for completed and unfinished work | Feature 2, AC-7 | — |
| R12 | No handoff brief when brain is unavailable — Final Report renders normally | Feature 2, AC-6 | — |
| R13 | No new MCP tools — use existing `agent_capture` and `agent_search` | Constraints | — |
| R14 | Schema changes: add `handoff` to `thought_type` and `source_phase` enums | R8, schema design | — |
| R15 | `thought_type_config` row for `handoff` with NULL TTL, 0.9 importance | R9 | — |
| R16 | Brain failure mid-pipeline: context-brief captures silently fail, handoff brief skipped with warning | Edge cases | — |
| R17 | Short sessions: no handoff brief generated if zero ADR steps completed and no user corrections | Edge cases | — |
| R18 | Multiple handoffs on same feature: each is a separate thought, no merging | Edge cases | — |

## Status

Accepted

## Context

The atelier brain (ADR-0001) gives agents persistent institutional memory for *decisions* — what Cal chose, what Roz found, what was rejected. But it has two gaps that matter for team collaboration:

1. **User intent is not captured.** When a user says "no modals, keep it simple," Eva writes it to `context-brief.md`. That file is session-local and reset per feature pipeline. A teammate's agents can find Cal's REST-over-GraphQL decision but not the "keep it simple" directive that drove it.

2. **No synthesized handoff.** Individual brain thoughts from a session are fragments. A teammate's agents must piece together "where Alice left off" from scattered decisions, corrections, and insights. The synthesis a human would give in a hallway conversation — "I finished steps 1-3, watch out for the auth edge case, the user changed their mind about caching" — does not exist.

Both gaps are solvable with the existing brain infrastructure. No new MCP tools are needed. The changes are: two enum values, one config row, and updated Eva instructions.

## Spec Challenge

**The riskiest assumption:** "Eva can reliably classify context-brief entries into the correct `thought_type`" (R2). Context-brief entries are free-text written by Eva herself. A "user preference" vs. a "mid-course correction" vs. a "rejected alternative" can be ambiguous — "actually, let's use tabs instead of a sidebar" is both a correction (of a prior choice) and a preference (for tabs). Misclassification doesn't break anything — the thought still surfaces via semantic search — but it affects ranking (preference has importance 1.0, correction has 0.7). **Mitigation:** Eva already categorizes context-brief entries by type when she appends them (the pipeline.md instructions distinguish preferences, corrections, and rejected alternatives). The brain capture inherits that existing classification. If classification quality is poor, it surfaces as a ranking issue, not a data loss issue.

## Decision

Extend the brain schema with two enum values (`handoff` thought type, `handoff` source phase) and one config row. Update Eva's pipeline instructions to dual-write context-brief entries to the brain and generate structured handoff briefs at pipeline end. No new MCP tools, no changes to the scoring function return type, no changes to agent personas other than Eva.

## Alternatives Considered

| Alternative | Pros | Cons | Reason Rejected |
|---|---|---|---|
| **Separate `handoff-brief.md` file on disk** | No brain dependency, git-trackable | Not searchable across features, not ranked by relevance, not available to teammates without file sharing | Solves the format problem but not the discovery problem. Teammates need semantic search to find relevant handoffs. |
| **New MCP tool `agent_handoff`** | Dedicated tool surface, could enforce handoff structure | Violates constraint (no new tools), adds maintenance surface. `agent_capture` with `thought_type: 'handoff'` achieves the same result. | Over-engineering. The existing capture tool handles it. |
| **Capture every context-brief entry immediately (not dual-write)** | Simpler — one write path | Removes the file as source of truth within the session. If brain is down, current-session agents lose context. | `context-brief.md` must remain the primary in-session communication channel. Brain capture is additive for cross-session use. |
| **Eva searches brain for prior context-brief entries and merges into new session's context-brief** | Automatic cross-session context without requiring agents to search brain | Bloats `context-brief.md` with prior-session data. Conflicting preferences from different sessions get merged without human awareness. | The brain's search + ranking already handles surfacing relevant prior context. Merging creates noise. |

## Consequences

**Positive:**
- Teammate agents automatically discover user preferences and corrections from prior sessions via `agent_search`
- Handoff briefs provide synthesized session summaries ranked alongside architectural decisions
- No new infrastructure — builds entirely on existing brain tools and schema patterns
- Graceful degradation — all changes are additive, brain-unavailable behavior is unchanged

**Negative:**
- Eva's pipeline instructions grow (dual-write logic + handoff brief generation template)
- Each context-brief entry adds one `agent_capture` call (latency: embedding generation + conflict check)
- Handoff brief quality depends on Eva's synthesis ability — a poor handoff is noise, not signal

**Neutral:**
- `match_thoughts_scored` return type does not change — `handoff` is just another thought type value
- Existing agents' brain access patterns are unaffected — they already search by feature scope, and handoff/preference thoughts surface naturally via scoring

## Implementation Plan

### Step 1: Schema Migration — Add `handoff` Enum Values

Add `handoff` to the `thought_type` and `source_phase` PostgreSQL enums. Add a `thought_type_config` row for the `handoff` type.

**Files to create:**
- `brain/migrations/002-add-handoff-enums.sql`

**Files to modify:**
- `brain/schema.sql` — add `'handoff'` to `thought_type` enum, `'handoff'` to `source_phase` enum, add INSERT row to `thought_type_config`

**Migration SQL:**

```sql
-- Migration 002: Add handoff enum values for team collaboration
-- Safe to run multiple times (idempotent checks).

-- Add 'handoff' to thought_type enum
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'handoff' AND enumtypid = 'thought_type'::regtype) THEN
    ALTER TYPE thought_type ADD VALUE 'handoff';
  END IF;
END $$;

-- Add 'handoff' to source_phase enum
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'handoff' AND enumtypid = 'source_phase'::regtype) THEN
    ALTER TYPE source_phase ADD VALUE 'handoff';
  END IF;
END $$;

-- Add thought_type_config row for handoff
INSERT INTO thought_type_config (thought_type, default_ttl_days, default_importance, description)
VALUES ('handoff', NULL, 0.9, 'Structured handoff briefs for team collaboration')
ON CONFLICT (thought_type) DO NOTHING;
```

**schema.sql changes:**

In the `thought_type` enum definition, add `'handoff'` after `'reflection'`:
```sql
CREATE TYPE thought_type AS ENUM (
  'decision', 'preference', 'lesson', 'rejection',
  'drift', 'correction', 'insight', 'reflection', 'handoff'
);
```

In the `source_phase` enum definition, add `'handoff'` after `'setup'`:
```sql
CREATE TYPE source_phase AS ENUM (
  'design', 'build', 'qa', 'review', 'reconciliation', 'setup', 'handoff'
);
```

In the `thought_type_config` INSERT, add the handoff row:
```sql
  ('handoff',     NULL, 0.9,  'Structured handoff briefs for team collaboration');
```

**DoR:** R8, R9, R14, R15 covered. Enum values match spec. Config row has NULL TTL (no expiry) and 0.9 importance (same tier as `decision`).

**DoD:** Migration is idempotent. `schema.sql` is the canonical schema for fresh installs. Migration file handles existing databases. `thought_type_config` row sets handoff importance to 0.9 with no expiry.

---

### Step 2: Server Enum Arrays — Sync with Schema

Update the `THOUGHT_TYPES` and `SOURCE_PHASES` arrays in `server.mjs` to include `'handoff'`. These arrays drive Zod validation for `agent_capture` — without this change, agents cannot capture handoff-type thoughts.

**Files to modify:**
- `brain/server.mjs` — add `'handoff'` to `THOUGHT_TYPES` array (line 36) and `SOURCE_PHASES` array (line 38)

**Changes:**

```javascript
// Before:
const THOUGHT_TYPES = ["decision", "preference", "lesson", "rejection", "drift", "correction", "insight", "reflection"];
const SOURCE_PHASES = ["design", "build", "qa", "review", "reconciliation", "setup"];

// After:
const THOUGHT_TYPES = ["decision", "preference", "lesson", "rejection", "drift", "correction", "insight", "reflection", "handoff"];
const SOURCE_PHASES = ["design", "build", "qa", "review", "reconciliation", "setup", "handoff"];
```

**Files to modify:**
- `brain/server.mjs` — add auto-migration block for migration 002

Add a migration check in the `runMigrations()` function (after the existing 001 block) that runs `002-add-handoff-enums.sql` if the `handoff` value is not present in the `thought_type` enum:

```javascript
// Check if handoff enum value exists
const handoffCheck = await client.query(
  `SELECT 1 FROM pg_enum WHERE enumlabel = 'handoff' AND enumtypid = 'thought_type'::regtype`
);
if (handoffCheck.rows.length === 0) {
  console.log("Migration: adding handoff enum values...");
  const migrationPath = path.join(path.dirname(fileURLToPath(import.meta.url)), "migrations", "002-add-handoff-enums.sql");
  if (existsSync(migrationPath)) {
    const sql = readFileSync(migrationPath, "utf-8");
    await client.query(sql);
  }
  console.log("Migration: handoff enum values added.");
}
```

**DoR:** R14 covered. Server-side validation matches schema enums.

**DoD:** `agent_capture` accepts `thought_type: 'handoff'` and `source_phase: 'handoff'` without validation errors. Auto-migration runs idempotently on existing databases.

---

### Step 3: Context Brief Brain Capture — Eva Dual-Write Instructions

Update Eva's pipeline instructions to dual-write context-brief entries to the brain. This is the core of Feature 1.

**Files to modify:**
- `source/commands/pipeline.md` — update the "Context Brief Maintenance" section

**Current section** (lines 179-191 of `pipeline.md`):

```markdown
## Context Brief Maintenance

Eva maintains `docs/pipeline/context-brief.md` as a living document throughout
the pipeline. Append to it whenever:

- The user expresses a preference conversationally ("keep it simple," "no modals")
- A mid-phase correction is made ("actually make that a dropdown")
- An alternative is considered and rejected, with the reason
- A cross-agent question is resolved ("Cal asked about caching, user said skip for v1")

**Reset this file at the start of each new feature pipeline.**
Every subagent invocation includes `READ: docs/pipeline/context-brief.md`.
```

**Updated section:**

```markdown
## Context Brief Maintenance

Eva maintains `docs/pipeline/context-brief.md` as a living document throughout
the pipeline. Append to it whenever:

- The user expresses a preference conversationally ("keep it simple," "no modals")
- A mid-phase correction is made ("actually make that a dropdown")
- An alternative is considered and rejected, with the reason
- A cross-agent question is resolved ("Cal asked about caching, user said skip for v1")

**Reset this file at the start of each new feature pipeline.**
Every subagent invocation includes `READ: docs/pipeline/context-brief.md`.

### Brain Dual-Write (when brain_available: true)

When Eva appends an entry to `context-brief.md` and brain is available, she
also calls `agent_capture` with the entry. This makes user intent discoverable
across sessions and teammates. The classification:

| Context-brief entry type | thought_type | Example |
|---|---|---|
| User preference or constraint | `preference` | "no modals," "keep it simple," "use existing component library" |
| Mid-course correction | `correction` | "actually make that a dropdown," "switch to tabs" |
| Rejected alternative with reasoning | `rejection` | "considered GraphQL but rejected — keep it simple" |
| Cross-agent resolution | `preference` | "Cal asked about caching, user said skip for v1" |

All captures use:
- `source_agent: 'eva'`
- `source_phase`: current pipeline phase (e.g., `'design'`, `'build'`)
- `importance`: use the `thought_type_config` default (preference: 1.0, correction: 0.7, rejection: 0.5)
- `scope`: current feature scope
- `metadata`: include `{ "tags": ["<feature-name>", "context-brief"] }`

**If the `agent_capture` call fails** (brain went down mid-pipeline), Eva
continues without error. The `context-brief.md` entry is the source of truth
for the current session. The brain capture is additive for cross-session use.
```

**DoR:** R1, R2, R3, R5, R16 covered. Classification table maps entry types to thought types. Failure mode documented.

**DoD:** Eva's instructions include dual-write logic for all four context-brief entry types. Failure is silent. Feature scope tag is included in metadata for cross-feature filtering.

---

### Step 4: Structured Handoff Brief — Eva Generation and Capture

Add handoff brief generation instructions to Eva's pipeline. This is the core of Feature 2.

**Files to modify:**
- `source/commands/pipeline.md` — add a new section after "Context Brief Maintenance" and update the "Final Report" section

**New section to add after the updated Context Brief Maintenance section:**

```markdown
## Handoff Brief Generation

When brain is available, Eva generates a structured handoff brief in two cases:

1. **Pipeline reaches Final Report** (automatic)
2. **User says "hand off," "someone else is picking this up," or equivalent** (explicit, mid-pipeline)

### Skip conditions

Do NOT generate a handoff brief if:
- Brain is unavailable
- The session produced zero ADR step completions AND zero context-brief entries (empty session)
- The user explicitly says "no handoff" or "skip handoff"

### Handoff brief template

Eva synthesizes the following from the session's context-brief, pipeline-state,
and any brain thoughts captured during the run:

```
## Handoff Brief — [Feature Name]
**Session:** [date] | **ADR:** [ADR reference if exists]

### Completed Work
- [ADR Step N]: [brief description of what was done]
- [ADR Step M]: [brief description]

### Unfinished Work
- [ADR Step P]: [status — not started / partially started + what remains]
- [ADR Step Q]: [status]

### Key Decisions (this session)
1. [Decision]: [reasoning] — [ADR step reference if applicable]
2. [Decision]: [reasoning]
3. [Decision]: [reasoning]

### Surprises
- [What deviated from the plan and why]

### User Corrections
- [Preferences and mid-course changes that shaped the work]
- [References to context-brief captures if applicable]

### Warnings for Next Developer
- [Known risks, fragile areas, "watch out for X" notes]
```

### Capture

Eva calls `agent_capture` with:
- `content`: the rendered handoff brief (full text above)
- `thought_type: 'handoff'`
- `source_agent: 'eva'`
- `source_phase: 'handoff'`
- `importance: 0.9`
- `scope`: current feature scope
- `metadata`: `{ "tags": ["<feature-name>", "<adr-reference>", "handoff"] }`

### Failure handling

If `agent_capture` fails at pipeline end, Eva logs: "Handoff brief not captured
— brain unavailable." The Final Report still renders normally. No pipeline
disruption.

### Mid-pipeline handoff

When the user triggers an explicit handoff mid-pipeline:
1. Eva generates the handoff brief from current state (pipeline-state.md + context-brief.md)
2. Eva captures it to brain
3. Eva announces: "Handoff brief captured. The next developer can pick up from [current phase]."
4. Pipeline ends (Eva does not proceed to Final Report unless user asks)
```

**Update to Final Report section** (section 3 of the Process):

Add a line before the report table:

```markdown
### 3. Final Report

**If brain is available:** generate and capture the handoff brief (see Handoff
Brief Generation above) before rendering the Final Report.
```

**DoR:** R6, R7, R8, R10, R11, R12, R16, R17, R18 covered. Template includes all six required sections. Skip conditions handle empty sessions. Failure mode documented.

**DoD:** Eva generates handoff brief at pipeline end (automatic) and on explicit user trigger (mid-pipeline). Brief is captured as a single `handoff`-type thought. ADR step numbers are referenced. Brain-unavailable behavior is unchanged.

---

### Step 5: Agent System Rules — Context Brief Maintenance Update

Update the agent-system.md rules to reflect the brain dual-write behavior for context-brief entries.

**Files to modify:**
- `source/rules/agent-system.md` — update the State & Context Management subsection for `context-brief.md`

**Current text** (lines 97-99):

```markdown
- **`context-brief.md`** -- Captures conversational decisions, corrections,
  user preferences, and rejected alternatives so subagents don't lose
  context. Reset at the start of each new feature pipeline.
```

**Updated text:**

```markdown
- **`context-brief.md`** -- Captures conversational decisions, corrections,
  user preferences, and rejected alternatives so subagents don't lose
  context. Reset at the start of each new feature pipeline. When brain is
  available, Eva dual-writes each entry to the brain via `agent_capture`
  (see pipeline.md Context Brief Maintenance section for classification
  table and capture parameters).
```

**DoR:** R1 reference in agent-system rules. Cross-references pipeline.md for details.

**DoD:** Agent-system.md reflects the dual-write behavior. No duplication of the classification table — single source of truth in pipeline.md.

---

### Step 6: Invocation Templates — Brain Context for Handoff

Update Eva's invocation templates to include handoff brief context when brain is available.

**Files to modify:**
- `source/references/invocation-templates.md` — update BRAIN sections in agent invocation templates

**Change:** In each agent's BRAIN section comment, add "handoff briefs" to the list of brain context that Eva injects. This is not a template structure change — it's a clarification that handoff-type thoughts are included in `agent_search` results.

**Example update for Cal template:**

```markdown
> BRAIN: [If brain available: prior architectural decisions, rejected approaches, technical constraints, handoff briefs, AND retro lessons relevant to this feature area from agent_search. Omit section if brain unavailable.]
```

Apply the same "handoff briefs" addition to: Cal, Colby mockup, Colby build, Roz (all variants), Agatha, and Robert invocation BRAIN sections where they exist.

**DoR:** R4, R10 covered. Agents receive handoff context via existing `agent_search` results.

**DoD:** All agent invocation templates with BRAIN sections mention handoff briefs. No structural template changes.

---

## Blast Radius

Every file that changes, grouped by step:

| Step | File | Change Type | Change Description |
|---|---|---|---|
| 1 | `brain/schema.sql` | Modify | Add `'handoff'` to `thought_type` enum, `'handoff'` to `source_phase` enum, add `thought_type_config` row |
| 1 | `brain/migrations/002-add-handoff-enums.sql` | Create | Idempotent migration for existing databases |
| 2 | `brain/server.mjs` | Modify | Add `'handoff'` to `THOUGHT_TYPES` and `SOURCE_PHASES` arrays, add migration 002 auto-run block |
| 3 | `source/commands/pipeline.md` | Modify | Add "Brain Dual-Write" subsection to Context Brief Maintenance |
| 4 | `source/commands/pipeline.md` | Modify | Add "Handoff Brief Generation" section, update Final Report section |
| 5 | `source/rules/agent-system.md` | Modify | Update `context-brief.md` description in State & Context Management |
| 6 | `source/references/invocation-templates.md` | Modify | Add "handoff briefs" to BRAIN sections in agent templates |

**Files NOT changed (confirmed no-touch):**
- `match_thoughts_scored` function — return type unchanged, `handoff` is just another enum value
- Agent persona files — no agent gains or loses brain access; Eva's expanded behavior is in pipeline.md
- `.mcp.json` — no new tools
- Brain config files — no new config keys
- `brain/migrations/001-add-captured-by.sql` — untouched

## DoD: Verification Checklist

- [ ] Fresh install: `schema.sql` creates both enums with `handoff` value, `thought_type_config` includes handoff row
- [ ] Existing database: migration 002 adds enum values and config row idempotently
- [ ] `agent_capture` with `thought_type: 'handoff'`, `source_phase: 'handoff'` succeeds (no Zod validation error)
- [ ] `agent_search` returns handoff thoughts ranked by three-axis scoring (handoff importance 0.9 = same tier as decision)
- [ ] Eva dual-writes context-brief entries when brain is available
- [ ] Eva skips brain capture silently when brain is unavailable
- [ ] Eva generates handoff brief at Final Report when brain is available
- [ ] Eva generates handoff brief on explicit "hand off" trigger mid-pipeline
- [ ] Eva skips handoff brief for empty sessions (zero completions + zero context-brief entries)
- [ ] Eva logs warning when handoff capture fails at pipeline end
- [ ] Final Report renders normally when brain is unavailable
- [ ] No new MCP tools registered
