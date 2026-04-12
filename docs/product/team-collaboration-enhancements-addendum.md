## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Eva dual-writes context-brief entries to brain via `agent_capture` when brain is available | ADR-0002, R1; team-collaboration-enhancements.md Feature 1, AC-1/2/3 |
| 2 | Captured entries use `thought_type`: `preference` / `correction` / `rejection` matching entry type | ADR-0002, R2 |
| 3 | All captures use `source_agent: 'eva'`, current `source_phase`, and feature scope tag | ADR-0002, R3 |
| 4 | `agent_search` returns captured context-brief thoughts for teammates on the same feature | ADR-0002, R4 |
| 5 | No behavioral change when brain is unavailable | ADR-0002, R5 |
| 6 | Eva generates a structured handoff brief at pipeline end (Final Report) or on explicit "hand off" trigger | ADR-0002, R6 |
| 7 | Handoff brief contains: completed work, unfinished work, key decisions, surprises, user corrections, warnings | ADR-0002, R7 |
| 8 | Handoff brief captured via `agent_capture` with `thought_type: 'handoff'`, `source_agent: 'eva'`, `source_phase: 'handoff'` | ADR-0002, R8 |
| 9 | `handoff` thought type has high default importance (0.9, same tier as `decision`), no expiry | ADR-0002, R9 |
| 10 | `agent_search` returns handoff briefs for teammates on the same feature | ADR-0002, R10 |
| 11 | Handoff brief references ADR step numbers for completed and unfinished work | ADR-0002, R11 |
| 12 | No handoff brief generated when brain is unavailable — Final Report renders normally | ADR-0002, R12 |
| 13 | Schema: `handoff` added to `thought_type` and `source_phase` enums | ADR-0002, R14 |
| 14 | `thought_type_config` row for `handoff`: NULL TTL, 0.9 importance | ADR-0002, R15 |
| 15 | Brain failure mid-pipeline: context-brief captures silently fail; handoff brief skipped with logged warning | ADR-0002, R16 |
| 16 | Short sessions: no handoff brief if zero ADR step completions and zero context-brief entries | ADR-0002, R17 |
| 17 | Multiple handoffs on same feature: each is a separate thought, no merging | ADR-0002, R18 |

**Retro risks:** None directly applicable. Both features are brain-optional (additive on top of existing behavior).

---

# Feature Spec: Team Collaboration Enhancements Addendum

**Author:** Robert (CPO) | **Date:** 2026-04-12
**Status:** Draft
**ADR:** [ADR-0002](../architecture/ADR-0002-team-collaboration.md)
**Extends:** [team-collaboration-enhancements.md](./team-collaboration-enhancements.md) (S6 + S7 implementation detail)

This addendum documents the implementation specifics of S6 (Handoff Brief protocol) and S7 (context-brief dual-write gate) from the gauntlet, as implemented in ADR-0002. The parent spec (`team-collaboration-enhancements.md`) describes the features from the user perspective. This addendum documents the implementation contracts, schema changes, and behavioral gates that operators and contributors need to understand.

---

## Feature S7: Context-Brief Dual-Write Gate

### Problem

`context-brief.md` is the primary in-session communication channel for user intent. It is reset per feature pipeline. Teammate agents starting a new session on the same feature have no access to prior user preferences and corrections — they must re-discover them through conversation or find them scattered across individual brain thoughts.

### Implementation Contract

When Eva appends an entry to `context-brief.md` and brain is available, she also calls `agent_capture` to make user intent discoverable across sessions.

**Classification table (single source of truth: `source/commands/pipeline.md`):**

| Context-brief entry type | `thought_type` | Example |
|---|---|---|
| User preference or constraint | `preference` | "no modals," "keep it simple," "use existing component library" |
| Mid-course correction | `correction` | "actually make that a dropdown," "switch to tabs" |
| Rejected alternative with reasoning | `rejection` | "considered GraphQL but rejected — keep it simple" |
| Cross-agent resolution | `preference` | "Cal asked about caching, user said skip for v1" |

All captures use:
- `source_agent: 'eva'`
- `source_phase`: current pipeline phase (e.g., `'design'`, `'build'`)
- Scope: current feature scope
- Metadata: `{ "tags": ["<feature-name>", "context-brief"] }`

**Failure mode:** If `agent_capture` fails (brain down mid-pipeline), Eva continues without error. `context-brief.md` remains the source of truth for the current session. The brain capture is additive for cross-session use only.

### Acceptance Criteria (S7 — Dual-Write Gate)

- AC-S7-1: When Eva appends a user preference to `context-brief.md` and brain is available, Eva MUST also call `agent_capture` with `thought_type: 'preference'`, the preference text, current feature scope, and current phase.
- AC-S7-2: When Eva appends a mid-course correction to `context-brief.md` and brain is available, Eva MUST also call `agent_capture` with `thought_type: 'correction'`.
- AC-S7-3: When Eva appends a rejected alternative to `context-brief.md` and brain is available, Eva MUST also call `agent_capture` with `thought_type: 'rejection'`.
- AC-S7-4: When a teammate starts a new session on the same feature and brain is available, `agent_search` for the feature area MUST return prior captured preferences and corrections in results.
- AC-S7-5: When brain is unavailable, Eva MUST write to `context-brief.md` with zero changes to current behavior. No errors, no warnings, no degradation.
- AC-S7-6: Captured context-brief thoughts MUST include the feature scope tag so they surface for teammates working on the same feature but not for unrelated features.

---

## Feature S6: Handoff Brief Protocol

### Problem

Alice builds ADR steps 1-3 and closes her session. Bob picks up steps 4-6. Bob's agents can search the brain and find individual thoughts from Alice's session — a decision here, a correction there, an insight somewhere else — but there is no synthesis. The most valuable context ("here's where I left off, here's what surprised me, here's what I learned that isn't in the ADR") is never captured as a unit.

### Implementation Contract

Eva generates a structured handoff brief at pipeline end (automatic) or on explicit user trigger (mid-pipeline). The brief is captured as a single `handoff`-type brain thought, making it retrievable by teammates at the top of search results (importance 0.9, same tier as `decision`).

**Schema additions (ADR-0002 Step 1):**

```sql
-- thought_type enum: add 'handoff'
ALTER TYPE thought_type ADD VALUE 'handoff';

-- source_phase enum: add 'handoff'
ALTER TYPE source_phase ADD VALUE 'handoff';

-- thought_type_config: handoff row
INSERT INTO thought_type_config (thought_type, default_ttl_days, default_importance, description)
VALUES ('handoff', NULL, 0.9, 'Structured handoff briefs for team collaboration')
ON CONFLICT (thought_type) DO NOTHING;
```

**Server-side (ADR-0002 Step 2):**

`THOUGHT_TYPES` array in `server.mjs` MUST include `'handoff'`. `SOURCE_PHASES` array MUST include `'handoff'`. Without this, `agent_capture` rejects handoff-type thoughts with a Zod validation error.

**Handoff brief template (Eva synthesizes from session state):**

```
## Handoff Brief — [Feature Name]
**Session:** [date] | **ADR:** [ADR reference if exists]

### Completed Work
- [ADR Step N]: [brief description of what was done]

### Unfinished Work
- [ADR Step P]: [status — not started / partially started + what remains]

### Key Decisions (this session)
1. [Decision]: [reasoning] — [ADR step reference if applicable]

### Surprises
- [What deviated from the plan and why]

### User Corrections
- [Preferences and mid-course changes that shaped the work]

### Warnings for Next Developer
- [Known risks, fragile areas, "watch out for X" notes]
```

**Capture call:**
- `thought_type: 'handoff'`
- `source_agent: 'eva'`
- `source_phase: 'handoff'`
- `importance: 0.9`
- Scope: current feature scope
- Metadata: `{ "tags": ["<feature-name>", "<adr-reference>", "handoff"] }`

**Skip conditions (no handoff brief generated):**
- Brain is unavailable
- Session produced zero ADR step completions AND zero context-brief entries (empty session)
- User explicitly says "no handoff" or "skip handoff"

### Acceptance Criteria (S6 — Handoff Brief Protocol)

- AC-S6-1: When a pipeline reaches Final Report and brain is available, Eva MUST generate a structured handoff brief containing all six sections: completed work, unfinished work, key decisions, surprises, user corrections, warnings.
- AC-S6-2: Eva MUST capture the handoff brief via `agent_capture` with `thought_type: 'handoff'`, `source_agent: 'eva'`, `source_phase: 'handoff'`, and feature scope tags.
- AC-S6-3: When the user says "hand off" or equivalent mid-pipeline, Eva MUST generate the handoff brief from current session state and capture it before ending the session.
- AC-S6-4: When a teammate starts a new session on the same feature and brain is available, `agent_search` for the feature area MUST return the handoff brief as a high-relevance result.
- AC-S6-5: The `handoff` thought type MUST have a `thought_type_config` row with NULL TTL (no expiry) and 0.9 importance (same tier as `decision`).
- AC-S6-6: When brain is unavailable, pipeline end behavior MUST be unchanged — Final Report renders normally, no errors from missing handoff capture.
- AC-S6-7: The handoff brief MUST reference the ADR and list ADR step numbers for completed and unfinished work, so the next developer can orient by step.
- AC-S6-8: Eva MUST NOT generate a handoff brief for empty sessions (zero ADR step completions AND zero context-brief entries).
- AC-S6-9: When multiple handoffs exist on the same feature, each MUST be a separate brain thought. Eva MUST NOT merge prior handoffs with the new one. `agent_search` returns all, ordered by recency.

---

## Shared Edge Cases

**Brain becomes unavailable mid-pipeline:**
- S7: Eva continues writing to `context-brief.md`. Brain captures silently fail. No pipeline disruption. Thoughts captured before the outage remain in the brain.
- S6: If brain is down at pipeline end, the handoff brief is not captured. The Final Report still renders. Eva logs: "Handoff brief not captured — brain unavailable."

**Conflicting preferences across handoffs:** Alice says "no modals." Bob says "modals are fine for confirmations." The brain's existing conflict detection handles this: both are `preference` type, the newer one supersedes the older. No new mechanism needed for this case.

**Context-brief reset on new feature:** `context-brief.md` is reset at the start of each new feature pipeline. Brain thoughts from prior features persist with their feature scope tags and remain retrievable via `agent_search`.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Eva dual-writes context-brief entries when brain available | Done | pipeline.md Context Brief Maintenance section: Brain Dual-Write subsection |
| 2 | Classification table maps entry types to thought_types | Done | Four-row classification table in pipeline.md |
| 3 | All captures include feature scope tag | Done | Metadata: `{ "tags": ["<feature-name>", "context-brief"] }` |
| 4 | `agent_search` returns captures for teammates | Done | Handoff thoughts importance 0.9; preference/correction thoughts surface via standard scoring |
| 5 | No behavioral change when brain unavailable | Done | Dual-write is conditional on `brain_available: true`; failure is silent |
| 6 | Handoff brief generated at Final Report and on explicit trigger | Done | pipeline.md Handoff Brief Generation section |
| 7 | Handoff brief contains all six required sections | Done | Template in pipeline.md |
| 8 | Handoff brief captured as `thought_type: 'handoff'` | Done | Capture parameters in pipeline.md |
| 9 | `handoff` thought type has high importance, no expiry | Done | thought_type_config: NULL TTL, 0.9 importance |
| 10 | ADR step references in handoff brief | Done | Template includes ADR step numbers for completed and unfinished work |
| 11 | Brain-unavailable: Final Report unchanged, no errors | Done | Skip condition and warning log in pipeline.md |
| 12 | Schema additions: `handoff` enum values + config row | Done | brain/schema.sql + brain/migrations/002-add-handoff-enums.sql |
| 13 | Server-side arrays synced with schema | Done | brain/server.mjs `THOUGHT_TYPES` and `SOURCE_PHASES` arrays include `'handoff'` |
| 14 | Short sessions: no handoff brief | Done | Skip conditions in pipeline.md Handoff Brief Generation section |
| 15 | Multiple handoffs: no merging, each is a separate thought | Done | Capture is a new `agent_capture` call each time; no merge logic |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled — no TBD, no placeholders
