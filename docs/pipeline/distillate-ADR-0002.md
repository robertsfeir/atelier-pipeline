---
source: docs/architecture/ADR-0002-team-collaboration.md
status: Accepted
downstream_consumer: Agatha documentation
compression_ratio: 0.43
---

## DoR: Requirements

| # | Requirement |
|---|---|
| R1 | Eva dual-writes context-brief entries to brain via `agent_capture` when brain available |
| R2 | Captured thoughts use `thought_type` matching entry type: `'preference'` / `'correction'` / `'rejection'` |
| R3 | All captures use `source_agent: 'eva'`, current `source_phase`, feature scope tag |
| R4 | `agent_search` returns captured context-brief thoughts for teammates on same feature |
| R5 | No behavioral change when brain unavailable — `context-brief.md` writes unaffected |
| R6 | Eva generates structured handoff brief at pipeline end (Final Report) or on explicit "hand off" trigger |
| R7 | Handoff brief contains: completed work, unfinished work, key decisions, surprises, user corrections, warnings |
| R8 | Handoff captured via `agent_capture` with `thought_type: 'handoff'`, `source_agent: 'eva'`, `source_phase: 'handoff'` |
| R9 | `handoff` thought type: high default importance (0.9, same tier as `decision`), no expiry (NULL TTL) |
| R10 | `agent_search` returns handoff briefs for teammates on same feature |
| R11 | Handoff brief references ADR step numbers for completed/unfinished work |
| R12 | No handoff brief when brain unavailable — Final Report renders normally |
| R13 | No new MCP tools — use existing `agent_capture` and `agent_search` |
| R14 | Schema: add `'handoff'` to `thought_type` and `source_phase` enums |
| R15 | `thought_type_config` row: `handoff`, NULL TTL, 0.9 importance |
| R16 | Brain failure mid-pipeline: context-brief captures silently fail, handoff brief skipped with warning |
| R17 | Short sessions: no handoff brief if zero ADR steps completed AND zero user corrections |
| R18 | Multiple handoffs on same feature: each separate thought, no merging |

## Context

- Two gaps in brain (ADR-0001): (1) user intent not captured cross-session — `context-brief.md` is session-local, reset per feature pipeline; (2) no synthesized handoff — teammates must piece together fragments
- Both solvable with existing brain infrastructure: two enum values, one config row, updated Eva instructions

## Spec Challenge

- Riskiest assumption: Eva can reliably classify context-brief entries into correct `thought_type` (R2)
- Ambiguity example: "actually, let's use tabs instead of a sidebar" = both correction and preference
- Misclassification impact: ranking issue only (preference importance 1.0 vs correction 0.7), not data loss
- Mitigation: Eva already categorizes entries by type in pipeline.md instructions; brain capture inherits that classification

## Decision

- Extend brain schema: two enum values (`handoff` thought type, `handoff` source phase), one config row
- Update Eva's pipeline instructions: dual-write context-brief entries to brain + generate structured handoff briefs at pipeline end
- No new MCP tools, no scoring function changes, no agent persona changes except Eva

## Alternatives Rejected

| Alternative | Reason Rejected |
|---|---|
| Separate `handoff-brief.md` on disk | Not searchable across features, not ranked, not available without file sharing — solves format but not discovery |
| New MCP tool `agent_handoff` | Violates no-new-tools constraint; `agent_capture` with `thought_type: 'handoff'` achieves same result |
| Capture every context-brief entry immediately (not dual-write) | Removes file as in-session source of truth; if brain down, current-session agents lose context |
| Eva merges prior context-brief entries into new session | Bloats `context-brief.md` with prior-session data; conflicting preferences merged without human awareness; brain search+ranking already handles this |

## Consequences

- **Positive:** teammate agents discover preferences/corrections via `agent_search`; handoff briefs ranked alongside decisions; no new infrastructure; graceful degradation
- **Negative:** Eva instructions grow (dual-write + handoff template); each context-brief entry adds one `agent_capture` call (latency: embedding + conflict check); handoff quality depends on Eva synthesis
- **Neutral:** `match_thoughts_scored` return type unchanged; existing agent brain access unaffected

## Implementation Plan

### Step 1: Schema Migration

- **Create:** `brain/migrations/002-add-handoff-enums.sql`
- **Modify:** `brain/schema.sql`
- Add `'handoff'` to `thought_type` enum (after `'reflection'`): `('decision','preference','lesson','rejection','drift','correction','insight','reflection','handoff')`
- Add `'handoff'` to `source_phase` enum (after `'setup'`): `('design','build','qa','review','reconciliation','setup','handoff')`
- Add `thought_type_config` row: `('handoff', NULL, 0.9, 'Structured handoff briefs for team collaboration')`
- Migration is idempotent (uses `IF NOT EXISTS` checks, `ON CONFLICT DO NOTHING`)
- DoR: R8, R9, R14, R15
- DoD: Migration idempotent; `schema.sql` canonical for fresh installs; handoff importance 0.9, no expiry

### Step 2: Server Enum Arrays

- **Modify:** `brain/server.mjs`
- Add `'handoff'` to `THOUGHT_TYPES` array (drives Zod validation for `agent_capture`)
- Add `'handoff'` to `SOURCE_PHASES` array
- Add auto-migration block in `runMigrations()`: check `pg_enum` for `'handoff'` in `thought_type`, run `002-add-handoff-enums.sql` if missing
- DoR: R14
- DoD: `agent_capture` accepts `thought_type: 'handoff'` and `source_phase: 'handoff'` without validation error; auto-migration idempotent

### Step 3: Context Brief Brain Capture

- **Modify:** `source/commands/pipeline.md` — add "Brain Dual-Write" subsection to Context Brief Maintenance
- Classification table: preference/constraint -> `preference`; mid-course correction -> `correction`; rejected alternative -> `rejection`; cross-agent resolution -> `preference`
- Capture params: `source_agent: 'eva'`, current `source_phase`, `thought_type_config` default importance, feature scope, `metadata: { "tags": ["<feature-name>", "context-brief"] }`
- Failure: `agent_capture` fails -> Eva continues silently; `context-brief.md` is session source of truth
- DoR: R1, R2, R3, R5, R16
- DoD: Dual-write for all four entry types; silent failure; feature scope tag in metadata

### Step 4: Structured Handoff Brief

- **Modify:** `source/commands/pipeline.md` — add "Handoff Brief Generation" section, update Final Report section
- Triggers: (1) pipeline reaches Final Report (automatic), (2) user says "hand off" (explicit, mid-pipeline)
- Skip conditions: brain unavailable; zero ADR step completions AND zero context-brief entries; user says "no handoff"
- Template sections: Completed Work (with ADR step refs), Unfinished Work, Key Decisions, Surprises, User Corrections, Warnings for Next Developer
- Capture: `thought_type: 'handoff'`, `source_agent: 'eva'`, `source_phase: 'handoff'`, `importance: 0.9`, `metadata: { "tags": ["<feature-name>", "<adr-reference>", "handoff"] }`
- Failure: log "Handoff brief not captured — brain unavailable." Final Report renders normally
- Mid-pipeline handoff: generate -> capture -> announce -> pipeline ends (no Final Report unless user asks)
- DoR: R6, R7, R8, R10, R11, R12, R16, R17, R18
- DoD: Auto + explicit triggers; single `handoff`-type thought; ADR step refs; brain-unavailable unchanged

### Step 5: Agent System Rules Update

- **Modify:** `source/rules/agent-system.md` — update `context-brief.md` description in State & Context Management
- Add: "When brain is available, Eva dual-writes each entry to the brain via `agent_capture`"
- Cross-references pipeline.md for classification table (no duplication)
- DoR: R1
- DoD: agent-system.md reflects dual-write; single source of truth in pipeline.md

### Step 6: Invocation Templates

- **Modify:** `source/references/invocation-templates.md` — add "handoff briefs" to BRAIN sections
- Applies to: Sarah, Colby mockup, Colby build, Roz (all variants), Agatha, Robert
- No structural template changes — clarification only
- DoR: R4, R10
- DoD: All BRAIN sections mention handoff briefs

## Blast Radius

| Step | File | Change |
|---|---|---|
| 1 | `brain/schema.sql` | Modify: add `'handoff'` to two enums + config row |
| 1 | `brain/migrations/002-add-handoff-enums.sql` | Create: idempotent migration |
| 2 | `brain/server.mjs` | Modify: enum arrays + migration 002 auto-run |
| 3,4 | `source/commands/pipeline.md` | Modify: dual-write subsection + handoff section + Final Report update |
| 5 | `source/rules/agent-system.md` | Modify: context-brief.md description |
| 6 | `source/references/invocation-templates.md` | Modify: BRAIN sections |

**No-touch confirmed:** `match_thoughts_scored` function, agent persona files, `.mcp.json`, brain config files, `brain/migrations/001-add-captured-by.sql`

## DoD: Verification Checklist

- [ ] Fresh install: `schema.sql` creates both enums with `handoff`, `thought_type_config` includes handoff row
- [ ] Existing DB: migration 002 adds enum values + config row idempotently
- [ ] `agent_capture` with `thought_type: 'handoff'`, `source_phase: 'handoff'` succeeds (no Zod error)
- [ ] `agent_search` returns handoff thoughts ranked by three-axis scoring (importance 0.9 = decision tier)
- [ ] Eva dual-writes context-brief entries when brain available
- [ ] Eva skips brain capture silently when brain unavailable
- [ ] Eva generates handoff brief at Final Report when brain available
- [ ] Eva generates handoff brief on explicit "hand off" trigger mid-pipeline
- [ ] Eva skips handoff brief for empty sessions (zero completions + zero context-brief entries)
- [ ] Eva logs warning when handoff capture fails at pipeline end
- [ ] Final Report renders normally when brain unavailable
- [ ] No new MCP tools registered
