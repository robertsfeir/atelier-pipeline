# QA Report -- 2026-03-28 (ADR-0008)
*Reviewed by Roz*

### Verdict: PASS

PIPELINE_STATUS: {"roz_qa": "PASS"}

## DoR: Requirements Extracted

| # | Requirement | Source | Notes |
|---|-------------|--------|-------|
| R1 | Boot-time discovery scan in default-persona.md step 3c | ADR-0008 Step 1 | Between 3b and 4, uses Glob, non-blocking errors |
| R2 | Inline creation via paste + Colby write | ADR-0008 Step 3 | Eva converts, Colby writes, user confirms |
| R3 | Semantic conflict detection | ADR-0008 Step 0, Step 2 | One-time per session, core first |
| R4 | Brain persistence for routing preferences | ADR-0008 Step 2 | agent_capture with thought_type: preference |
| R5 | Session-scoped fallback without brain | ADR-0008 Step 2 | context-brief.md under Routing Preferences |
| R6 | Core agents hardcoded, discovered additive | ADR-0008 Step 0, Step 4 | 9 names, never replace |
| R7 | XML conversion per schema + preamble reference | ADR-0008 Step 3 | 7 tags in order, agent-preamble.md |
| R8 | All changes in source/ only | ADR-0008 constraint | Not .claude/ |
| R9 | No trust scoring | ADR-0008 anti-goal | Quality is user responsibility |
| R10 | No registry, manifest, or API | ADR-0008 decision | Filesystem IS the registry |
| R11 | Eva never writes agent files | ADR-0008 constraint, default-persona.md gate | Routes to Colby |
| R12 | enforce-paths.sh catch-all blocks unknown agents | ADR-0008 blast radius | No changes to hook |

### Retro Risks

| Lesson | Risk | Status |
|--------|------|--------|
| #003 (Stop hook race condition) | Discovery scan adds latency; errors could block boot | Mitigated: step 3c.7 specifies non-blocking error handling |
| Behavioral constraints ignored (MEMORY) | Discovered agent XML conversion relies on behavioral guidance | Mitigated: hook catch-all provides mechanical enforcement for read-only default |

---

## Tier 1 -- Mechanical Checks

| Check | Status | Details |
|-------|--------|---------|
| Type Check | SKIP | No typecheck configured |
| Lint | SKIP | No linter configured for markdown |
| Tests | SKIP | Non-code ADR; no test suite applicable |
| Coverage | N/A | Non-code changes |
| Complexity | PASS | All additions are structured markdown sections, no nesting issues |
| Unfinished markers | PASS | 0 TODO/FIXME/HACK/XXX in any of the 4 changed files |

## Tier 2 -- Judgment Checks

| Check | Status | Details |
|-------|--------|---------|
| Security | PASS | Eva does NOT gain Write/Edit; discovered agents read-only by default; enforce-paths.sh untouched |
| Additions only | PASS | All 4 files verified via diff: only additions, no deletions of existing content |
| Eva tool constraints | PASS | Eva tools list (line 73 agent-system.md) unchanged: "NO Write/Edit/MultiEdit/NotebookEdit" |
| Doc Impact | YES | See below |
| Dependencies | PASS | No new dependencies |

---

## Per-Step Verification

### Step 0: Agent Discovery Section in agent-system.md

| Test ID | Status | Finding |
|---------|--------|---------|
| T-0008-001 | PASS | `<section id="agent-discovery">` at source/rules/agent-system.md:308. Contains 5 sub-protocols: Discovery Protocol, Conflict Detection, Brain Persistence for Routing Preferences, (brain-unavailable fallback within Brain Persistence), Inline Agent Creation Protocol |
| T-0008-002 | PASS | Core list at line 324: cal, colby, roz, ellis, agatha, robert, sable, investigator, distillator -- exactly 9 names |
| T-0008-003 | PASS | Line 314: "Discovered agents are **additive only** -- they never replace core agent routing." Line 353: "Discovered agents **never shadow** core agents without explicit user consent." |
| T-0008-004 | PASS | Lines 401-403: "Eva does **NOT** write the file herself -- this is a mandatory routing to Colby." |
| T-0008-005 | PASS | Lines 361-363: Brain-unavailable fallback to context-brief.md under "## Routing Preferences", session-scoped, re-asked next session |
| T-0008-006 | PASS | Verified via diff: existing `<routing id="auto-routing">` content unchanged; only new "### Discovered Agent Routing" subsection appended before closing `</routing>` tag |
| T-0008-007 | PASS | Verified via diff: existing `<section id="shared-behaviors">` content unchanged; new section added AFTER shared-behaviors closes |

### Step 1: Boot Sequence Discovery in default-persona.md

| Test ID | Status | Finding |
|---------|--------|---------|
| T-0008-010 | PASS | Step 3c at source/rules/default-persona.md:61, positioned between step 3b (line 57) and step 4 (line 74) |
| T-0008-011 | PASS | Step 3c.1: `Glob(".claude/agents/*.md")` |
| T-0008-012 | PASS | Step 3c.2-3: YAML frontmatter name field comparison against core constant from agent-system.md |
| T-0008-013 | PASS | Step 3c.7: "Agent discovery scan failed: [reason]. Proceeding with core agents only." + "Never block session boot." |
| T-0008-014 | PASS | Step 3c.6: "If zero non-core agents found, no announcement or 'No custom agents found.'" |
| T-0008-015 | PASS | Covered by step 3c.3 -- comparison against core constant; if all files match core names, step 3c.6 applies (zero discovered) |
| T-0008-016 | PASS | Verified via diff: existing steps 1-3b and 4-6 are unmodified; only step 3c inserted and step 6 announcement appended |
| T-0008-017 | PASS | Line 86: "Custom agents: append 'Custom agents: N discovered' when discovered agent count > 0 (omit line when zero)" |

### Step 2: Auto-Routing Extension

| Test ID | Status | Finding |
|---------|--------|---------|
| T-0008-020 | PASS | "### Discovered Agent Routing" subsection at line 187 within `<routing id="auto-routing">` |
| T-0008-021 | PASS | Line 193: "The core routing table is always evaluated first. Core agents have priority for all intent categories they cover." |
| T-0008-022 | PASS | Line 346 (discovery section) + line 195 (routing section): asks user once per (intent, agent) pair |
| T-0008-023 | PASS | Line 200: `agent_capture` with `thought_type: 'preference'`, `source_agent: 'eva'`, `routing_rule: {intent} -> {chosen_agent}` |
| T-0008-024 | PASS | Line 202-203: Brain-unavailable appends to context-brief.md under "## Routing Preferences" |
| T-0008-025 | PASS | Line 209: "Explicit name mention routes to any discovered agent regardless of conflicts or preferences -- it is always a direct override." |
| T-0008-026 | PASS | Lines 207-208: "Discovered agents with no description overlap with core agents are available only via **explicit name mention**" |
| T-0008-027 | PASS | Verified via diff: existing Intent Detection table rows (lines 152-169) unchanged |
| T-0008-028 | PASS | Line 212: "Discovered agents cannot shadow core agents without explicit user consent." |

### Step 3: Inline Agent Creation

| Test ID | Status | Finding |
|---------|--------|---------|
| T-0008-030 | PASS | Detection heuristic at lines 373-377: "two or more" of identity, rules, tools, constraints, output format |
| T-0008-031 | PASS | Conversion process step 2 lists 7 tags in order: identity, required-actions, workflow, examples, tools, constraints, output. Matches xml-prompt-schema.md persona file tag order |
| T-0008-032 | PASS | Step 2 YAML frontmatter: name (kebab-case), description (one-line), disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit |
| T-0008-033 | PASS | Step 2: "`<required-actions>` with reference to `.claude/references/agent-preamble.md`" |
| T-0008-034 | PASS | Step 4: "Present the converted content to the user for approval before writing." |
| T-0008-035 | PASS | Step 5: "Eva does **NOT** write the file herself -- this is a mandatory routing to Colby." |
| T-0008-036 | PASS | Step 6: "If user declines: No file is written. Eva acknowledges and moves on." |
| T-0008-037 | PASS | Step 2 workflow entry: "omit tag entirely if source has no workflow content" |
| T-0008-038 | PASS | Step 3: "If the parsed name matches a core agent constant, Eva rejects: '[name] conflicts with a core agent.'" |
| T-0008-039 | PASS | Step 7: "Eva re-runs the discovery scan to register the new agent immediately." |
| T-0008-040 | PASS | Step 8: "Enforcement note: Eva announces: '[agent-name] has read-only access by default.'" |
| T-0008-041 | PASS | xml-prompt-schema.md line 193: "## Agent Conversion Template" section with YAML frontmatter, structural mapping table, required-actions content |
| T-0008-042 | PASS | Verified via diff: all existing xml-prompt-schema.md sections (lines 1-191) unchanged; new section appended at end |

### Step 4: Subagent Table Updates

| Test ID | Status | Finding |
|---------|--------|---------|
| T-0008-050 | PASS | `<gate id="no-skill-tool">` table at line 289: "*[Discovered agents]* \| *`.claude/agents/{name}.md` (see `<section id="agent-discovery">`)*" |
| T-0008-051 | PASS | `<section id="architecture">` subagent table at line 65: "*[Discovered agents]* \| *Per agent persona file* \| *Read, Glob, Grep, Bash (read-only by default)*" |
| T-0008-052 | PASS | Verified via diff: all 9 core agent rows unchanged in both tables |

### Step 5: Pipeline-Setup Awareness

| Test ID | Status | Finding |
|---------|--------|---------|
| T-0008-060 | PASS | "#### Custom Agent Discovery" subsection at SKILL.md after Step 3a (hooks installation), before Step 3b |
| T-0008-061 | PASS | Note mentions: drop file (with frontmatter), paste markdown (Eva converts), read-only default, hook customization for write access |
| T-0008-062 | PASS | Verified via diff: existing setup procedure steps unchanged |

---

## Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| R1 | Boot-time discovery scan | Step 3c added | PASS | Correct position, Glob scan, non-blocking errors |
| R2 | Inline creation via Colby | Conversion + Colby write | PASS | Eva converts, routes to Colby, user confirms |
| R3 | Semantic conflict detection | Core first, one-time ask | PASS | Explicit in both discovery section and routing subsection |
| R4 | Brain persistence | agent_capture with preference | PASS | Correct thought_type, source_agent, metadata |
| R5 | Session-scoped fallback | context-brief.md | PASS | Under "## Routing Preferences", session-scoped |
| R6 | Core hardcoded, discovered additive | 9 names, never replace | PASS | List exact, "additive only" + "never shadow" stated |
| R7 | XML conversion per schema | 7 tags, preamble ref | PASS | Tags match schema order; preamble in required-actions |
| R8 | Changes in source/ only | source/ templates modified | PASS | .claude/ copies NOT modified (277 vs 411 lines) |
| R9 | No trust scoring | Not implemented | PASS | No quality/trust evaluation anywhere in additions |
| R10 | No registry/manifest/API | Filesystem scanning only | PASS | No JSON, no manifest, no API |
| R11 | Eva never writes agent files | Routes to Colby | PASS | "Eva does **NOT** write the file herself" explicit; Eva tools list unchanged |
| R12 | enforce-paths.sh unchanged | Catch-all blocks unknown | PASS | No diff to hooks; enforcement note in creation protocol references it |

---

## Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across all 4 changed files: **0 matches.**

---

## Issues Found

**No blockers. No fix-required items.**

### Observations (informational, not blocking)

1. **Out-of-scope changes in SKILL.md:** The diff includes warn-dor-dod.sh hook addition (manifest row, SubagentStop registration, file count bumps 38->39, 4->5 hooks). These are from a separate ADR-0007 work unit, not part of ADR-0008. They are correct and additive but should be attributed separately at commit time.

2. **Dual tree sync deferred:** The `.claude/` installed copies were NOT updated (`.claude/rules/agent-system.md` has 277 lines vs `source/` at 411). This is correct per constraint R8 ("all changes in source/ only"). The project's own installed pipeline will not have discovery capabilities until setup is re-run.

---

## Doc Impact: YES

**Affected docs:** All 4 modified files ARE the documentation (non-code ADR). No additional external docs require updates. The ADR at `docs/architecture/ADR-0008-agent-discovery.md` serves as architectural documentation.

---

## Roz's Assessment

Clean implementation. All 42 test spec items (T-0008-001 through T-0008-062) pass verification. Every ADR requirement (R1-R12) is traceable to specific lines in the implementation.

The changes are purely additive -- verified by diffing every file against HEAD, confirming no existing content was deleted or modified. The implementation correctly maintains the critical safety invariants: Eva's tool list is unchanged (no Write/Edit), discovered agents default to read-only, enforce-paths.sh is untouched, and the core 9 agents are hardcoded with discovered agents explicitly marked as additive-only.

The section placement follows the ADR's instructions precisely: `<section id="agent-discovery">` is after `<section id="shared-behaviors">`, the routing subsection is after "### Auto-Routing Confidence" within the routing block, and the boot step 3c sits correctly between 3b and 4.

The xml-prompt-schema.md conversion template is well-structured with a clear structural mapping table, explicit required/optional markers, and the mandatory agent-preamble.md reference in required-actions. The mapping covers all 7 persona file tags with correct optionality rules.

---

## DoD: Verification

| ADR Requirement | Test IDs | Status |
|-----------------|----------|--------|
| R1: Boot-time discovery | T-0008-010 through T-0008-017 | Done (8/8 pass) |
| R2: Inline creation | T-0008-030 through T-0008-042 | Done (13/13 pass) |
| R3: Conflict detection | T-0008-001, T-0008-020 through T-0008-028 | Done (10/10 pass) |
| R4: Brain persistence | T-0008-023 | Done |
| R5: Session-scoped fallback | T-0008-024 | Done |
| R6: Core hardcoded, additive | T-0008-003, T-0008-006, T-0008-028, T-0008-052 | Done |
| R7: XML conversion + preamble | T-0008-031 through T-0008-033, T-0008-041 | Done |
| R8: Source/ only | Verified via diff | Done |
| R9: No trust scoring | Absence verified | Done |
| R10: No registry/manifest | Absence verified | Done |
| R11: Eva never writes | T-0008-004, T-0008-035 | Done |
| R12: Hook catch-all preserved | T-0008-040, diff verified | Done |

All 12 requirements verified. 42/42 test spec items pass. No deferred items.

### Recurring QA Patterns

None identified. First ADR-0008 review.

### Investigation Findings Beyond Immediate Scope

The SKILL.md diff bundles ADR-0007 (warn-dor-dod.sh) changes with ADR-0008 (agent discovery) changes. These should be separated at commit time for clean attribution.
