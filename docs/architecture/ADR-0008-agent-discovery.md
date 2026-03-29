# ADR-0008: Filesystem-Based Agent Discovery with Inline Creation and XML Conversion

## Status

Proposed

## DoR: Requirements Extracted

| # | Requirement | Source | Notes |
|---|-------------|--------|-------|
| R1 | Eva scans `.claude/agents/` at session boot, diffs against known core agents, announces unknowns | context-brief.md, brain-context | New boot sequence step between existing steps 3b and 4 |
| R2 | Users can paste agent markdown into chat; Eva converts to XML format and routes to Colby to write the file | context-brief.md | Eva NEVER writes files outside `docs/pipeline/` -- Colby writes |
| R3 | Conflict detection is semantic -- Eva reads descriptions of discovered agents and compares against core routing table | context-brief.md | No programmatic analysis; Eva compares descriptions to routing intents |
| R4 | When brain is available, routing preferences persist across sessions via `agent_capture` | context-brief.md | `thought_type: 'preference'`, `source_agent: 'eva'` |
| R5 | When brain is unavailable, conflict resolution is session-scoped only (context-brief.md) | context-brief.md | Graceful degradation to baseline |
| R6 | Core 9 agents remain hardcoded in agent-system.md; discovered agents are ADDITIVE only | context-brief.md, constraint | Never replace core routing |
| R7 | Converted agents get: agent-preamble.md reference, YAML frontmatter, XML tags per xml-prompt-schema.md | constraint | Tags: `<identity>`, `<required-actions>`, `<workflow>`, `<constraints>`, `<output>` |
| R8 | All changes in `source/` directory only | context-brief.md | Not `.claude/` -- dual tree convention |
| R9 | Quality is user's responsibility -- no trust scoring | context-brief.md | Anti-goal: automated quality/trust evaluation |
| R10 | No registry JSON, no manifest, no API, no marketplace | context-brief.md, brain-context (rejected alternatives) | Filesystem IS the registry |
| R11 | Eva must NOT gain Write/Edit access | constraint, default-persona.md gate `no-code-writing` | Routes to Colby for file creation |
| R12 | `enforce-paths.sh` catch-all blocks unknown agent_types from writing | source/hooks/enforce-paths.sh:112-118 | Discovered agents are read-only by default unless explicitly configured |

### Retro Risks

| Lesson | Risk to this feature | Mitigation |
|--------|---------------------|------------|
| #003 (Stop hook race condition) | New boot step adds latency; if it errors, could block session start | Discovery scan must be non-blocking -- errors log a warning, never prevent session boot |
| Behavioral constraints ignored (brain-context lesson) | Discovered agent XML conversion relies on behavioral guidance for quality | The conversion is mechanical (template + structural rules), not behavioral. Hook enforcement (`enforce-paths.sh` catch-all) provides the safety net. |

## Context

The pipeline currently supports exactly 9 hardcoded agents defined in `source/agents/`. Users who want custom agents (domain experts, project-specific reviewers, specialized tools) must manually create persona files and manually add routing rules. There is no discovery mechanism -- Eva does not know about agents she was not told about at design time.

Issue #15 requests filesystem-based agent discovery: Eva scans the agents directory, identifies non-core files, announces them, detects capability conflicts with core agents, and lets users resolve routing preferences. Additionally, users should be able to paste raw agent markdown into the chat and have it converted to the pipeline's XML format and written as a proper agent file.

### Spec Challenge

**The spec assumes** that Eva can reliably perform semantic conflict detection by reading agent descriptions and comparing them to core routing intents. If this is wrong (Eva misjudges a capability overlap or misses a conflict), the design degrades to the user manually resolving routing ambiguity -- which is acceptable since the user retains override capability via slash commands. **Are we confident?** Yes -- Eva already classifies user intent against the routing table on every message. Conflict detection uses the same reasoning but against agent descriptions instead of user messages.

**SPOF:** The boot-time discovery scan in `default-persona.md`. **Failure mode:** If the scan errors (e.g., Glob fails, file read fails), Eva would not know about discovered agents for the session. **Graceful degradation:** The scan wraps in error handling that logs the failure and proceeds with core-only routing. Discovered agents remain on disk and will be found next session. The pipeline runs identically to today's behavior.

## Decision

Implement filesystem-based agent discovery as a three-capability addition to Eva's boot sequence, auto-routing logic, and agent creation flow. All changes in `source/` templates only.

### Capability 1: Boot-Time Discovery

Add a new step to Eva's Session Boot Sequence in `source/rules/default-persona.md` (between existing step 3b and step 4). Eva uses Glob to scan the agents directory, compares filenames against the known core agent list, and announces any discovered agents with their names and descriptions.

The core agent list is defined as a constant in the boot sequence itself:
```
Core agents: cal, colby, roz, ellis, agatha, robert, sable, investigator, distillator
```

Any `.md` file in `.claude/agents/` whose YAML frontmatter `name` field does not match a core agent name is a discovered agent.

### Capability 2: Conflict Detection and Routing

Add a new section to `source/rules/agent-system.md` under the auto-routing rules. When Eva detects a discovered agent whose description overlaps with a core agent's domain, she announces the conflict and asks the user once per session: "For [intent], route to [core agent] or [discovered agent]?"

- Brain available: Eva captures the preference via `agent_capture` with `thought_type: 'preference'`. On subsequent sessions, Eva queries brain for routing preferences before asking.
- Brain unavailable: Eva records the preference in `context-brief.md`. Preference is session-scoped -- lost on next session, re-asked.

### Capability 3: Inline Agent Creation with XML Conversion

When a user pastes agent markdown into the chat (detected by Eva recognizing an agent definition pattern), Eva:
1. Parses the content structure
2. Prepares a converted version following `xml-prompt-schema.md` tag vocabulary
3. Adds YAML frontmatter (name, description, disallowedTools)
4. Adds `agent-preamble.md` reference in `<required-actions>`
5. Wraps content in proper XML tags: `<identity>`, `<required-actions>`, `<workflow>`, `<constraints>`, `<output>`
6. Invokes Colby to write the file to `.claude/agents/{name}.md`
7. Re-runs discovery to register the new agent

Eva prepares the content and hands it to Colby with explicit file path and content. Eva does not write the file herself.

### Enforcement Hook Integration

The existing `enforce-paths.sh` catch-all (`*` case at line 112) blocks unknown agent types from Write/Edit/MultiEdit by default. This is correct behavior for discovered agents -- they get read-only access. Users who want a discovered agent to have write access must add an explicit case to their local `enforce-paths.sh`. This is documented but not automated (anti-goal: auto-modifying hooks).

## Alternatives Considered

### A1: Declarative Agent Manifest (agent-manifest.json)

A JSON file listing all agents with metadata, capabilities, and routing rules. Eva reads the manifest instead of scanning the filesystem.

**Pros:** Structured, explicit, easy to validate programmatically.
**Cons:** Another file to maintain in sync with actual `.md` files. Violates the "filesystem IS the registry" decision. Users must update two things (the file + the manifest) to add an agent. Drift between manifest and filesystem is a new failure mode.

**Rejected:** Adds maintenance burden with no benefit over filesystem scanning. The YAML frontmatter in each agent file already contains the metadata Eva needs.

### A2: A2A-Style Registry with Agent Cards

Formal agent capability registration with structured capability descriptors, protocol negotiation, and discovery API.

**Pros:** Industry-standard approach. Enables programmatic capability matching.
**Cons:** Massive overengineering for a local agent system. Nobody has shipped A2A in production at this scale. Requires new infrastructure. Brain context confirms this was explicitly rejected.

**Rejected:** The problem is "let Eva find extra agents in a directory." The solution does not need a protocol.

### A3: Brain-Only Registry

Store agent definitions and routing preferences exclusively in the brain. No filesystem scanning -- brain is the single source of truth.

**Pros:** Centralized, searchable, persistent.
**Cons:** Violates brain-is-optional principle. Users without brain lose all custom agent support. Creates hard dependency on infrastructure that is explicitly opt-in.

**Rejected:** Brain adds persistence to an already-working filesystem mechanism. It does not replace it.

## Consequences

### Positive

- Users can add custom agents by dropping a `.md` file in `.claude/agents/` -- zero configuration
- Inline creation lowers the barrier: paste markdown, get a pipeline-compatible agent
- Brain persistence means routing preferences survive across sessions (when available)
- Core agents are untouched -- zero risk of breaking existing routing
- Enforcement hooks provide mechanical safety: discovered agents cannot write by default

### Negative

- Boot sequence adds ~2-3 seconds for Glob + file reads on projects with many custom agents
- Semantic conflict detection is LLM-judgment-based, not deterministic -- may produce false positives/negatives
- Users who want write access for discovered agents must manually edit `enforce-paths.sh` (no automation)
- Session-scoped preferences without brain means re-asking routing questions each session

### Neutral

- No database changes -- brain captures use existing `agent_capture` infrastructure
- No new dependencies
- Existing 9 core agents and their routing are completely unchanged

## Implementation Plan

### Step 0: Agent Discovery Section in agent-system.md (source template)

Add a new `<section id="agent-discovery">` to `source/rules/agent-system.md` containing:

1. The core agent constant list (9 names)
2. Discovery protocol: how Eva scans, what she reads, how she announces
3. Conflict detection rules: when Eva flags an overlap, how she asks, how she records
4. Brain integration: capture/query routing preferences
5. Inline creation protocol: how Eva detects pasted markdown, prepares XML conversion, invokes Colby

This section is the authoritative reference for all three capabilities.

**Files to modify:**
- `source/rules/agent-system.md` -- add `<section id="agent-discovery">` after `<section id="shared-behaviors">`

**Acceptance criteria:**
- Section defines core agent list as a constant (9 names)
- Section specifies discovery scan procedure (Glob + frontmatter read)
- Section specifies conflict detection protocol (description comparison + one-time user resolution)
- Section specifies brain persistence for routing preferences (with fallback to context-brief)
- Section specifies inline creation protocol (detect, convert, route to Colby)
- Section references xml-prompt-schema.md for conversion tag vocabulary
- Section references agent-preamble.md for injected required-actions

**Estimated complexity:** Medium (new section with multiple sub-protocols, must integrate with existing routing and brain patterns)

### Step 1: Boot Sequence Discovery Step in default-persona.md (source template)

Add step 3c to the Session Boot Sequence in `source/rules/default-persona.md`. This step:

1. Runs `Glob(".claude/agents/*.md")` to list all agent files
2. Reads YAML frontmatter `name` field from each file
3. Compares against core agent constant (defined in Step 0's section)
4. For each non-core agent: reads the `description` field
5. If brain available: queries `agent_search` for existing routing preferences for each discovered agent
6. Announces: "Discovered N custom agent(s): [name] -- [description]. [Routing preference: {from brain}]" or "No custom agents found."
7. On error: logs "Agent discovery scan failed: [reason]. Proceeding with core agents only." and continues

This step runs AFTER branching strategy read (3b) and BEFORE brain health check (4), because brain health determines whether preferences can be loaded. The discovery scan itself does not need brain -- it just notes which agents exist. Brain preference lookup happens in step 5 (brain context retrieval) if brain is available.

**Files to modify:**
- `source/rules/default-persona.md` -- add step 3c to `<protocol id="boot-sequence">`
- `source/rules/default-persona.md` -- update step 6 announcement to include discovered agents

**Acceptance criteria:**
- Step 3c is positioned between 3b (branching strategy) and 4 (brain health check)
- Scan uses Glob, not Bash `ls` or `find`
- Error in scan does not block session boot (warning only, proceeds with core agents)
- Announcement includes agent name and one-line description
- Step 6 announcement updated to include "Custom agents: N discovered" or omitted if zero

**Estimated complexity:** Low (add a numbered step to an existing protocol, error handling)

### Step 2: Auto-Routing Extension for Discovered Agents

Add routing logic for discovered agents to the auto-routing section. This is part of the `<section id="agent-discovery">` written in Step 0 but the routing integration touches the existing `<routing id="auto-routing">` section.

Add a new subsection "### Discovered Agent Routing" after "### Auto-Routing Confidence" in `source/rules/agent-system.md`:

1. After classifying user intent against core routing table (existing behavior), Eva also checks discovered agents
2. If a discovered agent's description matches the user's intent better than any core agent, Eva announces the conflict: "This could go to [core agent] (core) or [discovered agent] (custom). Which do you prefer for [intent]?"
3. User's choice is recorded:
   - Brain available: `agent_capture` with `thought_type: 'preference'`, metadata includes `routing_rule: {intent} -> {chosen_agent}`
   - Brain unavailable: appended to context-brief.md under "## Routing Preferences"
4. On subsequent messages with the same intent pattern, Eva uses the recorded preference without re-asking
5. If no conflict, discovered agents are available via explicit name mention only (e.g., "ask [agent-name] about this")

**Files to modify:**
- `source/rules/agent-system.md` -- add "### Discovered Agent Routing" subsection within `<routing id="auto-routing">`

**Acceptance criteria:**
- Core routing table is checked FIRST -- discovered agents never shadow core agents without explicit user preference
- Conflict resolution asks user exactly once per (intent, agent) pair per session
- Brain persistence captures the preference with sufficient metadata to reconstruct the rule
- Without brain, preference stored in context-brief.md and re-asked next session
- Explicit name mention routes to any discovered agent regardless of conflicts

**Estimated complexity:** Medium (integrates with existing routing logic, brain capture, context-brief patterns)

### Step 3: Inline Agent Creation Protocol

Add the inline creation protocol details to the `<section id="agent-discovery">` in `source/rules/agent-system.md`. This defines:

1. **Detection heuristic:** Eva recognizes agent definitions when user pastes markdown containing an identity/role description, behavioral rules, and tool/constraint lists. Eva asks: "This looks like an agent definition. Want me to convert it to a pipeline agent?"
2. **Conversion template:** The XML structure Eva prepares:
   - YAML frontmatter: `name` (kebab-case from agent name), `description` (one-line from identity), `disallowedTools` (conservative default: `Agent, Write, Edit, MultiEdit, NotebookEdit` -- read-only)
   - `<!-- Part of atelier-pipeline. -->` comment
   - `<identity>` from agent's role/identity text
   - `<required-actions>` with reference to `agent-preamble.md` + agent-specific actions
   - `<workflow>` from agent's process/steps (if present, otherwise omitted)
   - `<constraints>` from agent's rules/boundaries
   - `<output>` from agent's output format (if present, otherwise minimal default)
3. **User confirmation:** Eva presents the converted content for approval before writing
4. **Write via Colby:** Eva invokes Colby with explicit task: "Write this file to `.claude/agents/{name}.md`" with the full content in the CONTEXT field
5. **Post-write discovery:** Eva re-runs discovery scan to register the new agent
6. **Enforcement note:** Eva announces: "[agent-name] has read-only access by default. To grant write access, add a case to `.claude/hooks/enforce-paths.sh`."

Also add a conversion template reference to `source/references/xml-prompt-schema.md` -- a new subsection "## Agent Conversion Template" showing the structural mapping from raw markdown to pipeline XML format.

**Files to modify:**
- `source/rules/agent-system.md` -- inline creation sub-protocol within `<section id="agent-discovery">`
- `source/references/xml-prompt-schema.md` -- add "## Agent Conversion Template" section

**Acceptance criteria:**
- Detection heuristic is described clearly enough for Eva to identify agent-like content
- Conversion produces valid XML per xml-prompt-schema.md tag vocabulary (7 tags in order)
- YAML frontmatter includes conservative `disallowedTools` (read-only default)
- Agent-preamble.md reference is injected in `<required-actions>`
- Eva presents converted content to user for approval before invoking Colby
- Eva announces read-only default and how to change it
- xml-prompt-schema.md updated with conversion template section

**Estimated complexity:** Medium (conversion logic is structural/template-based, not algorithmic)

### Step 4: Subagent Invocation Table Update

Update the "Subagents are invoked via the Agent tool" table in `<gate id="no-skill-tool">` to add a note about discovered agents. The core 9 agents remain hardcoded in the table. Add a row or note:

```
| [Discovered agents] | `.claude/agents/{name}.md` (see Agent Discovery) |
```

Also update the `<section id="architecture">` "Subagents (own context window)" table to note that additional subagents may exist via discovery.

**Files to modify:**
- `source/rules/agent-system.md` -- add note to `<gate id="no-skill-tool">` table
- `source/rules/agent-system.md` -- add note to `<section id="architecture">` subagent table

**Acceptance criteria:**
- Core 9 agents remain as-is in both tables
- A clear note indicates discovered agents supplement the table
- Note references the `<section id="agent-discovery">` for details

**Estimated complexity:** Low (add notes/rows to existing tables)

### Step 5: Pipeline-Setup Discovery Awareness

Update `skills/pipeline-setup/SKILL.md` to inform users about agent discovery during setup. After the main installation completes, add an informational note:

"Custom agents: drop any `.md` file into `.claude/agents/` with YAML frontmatter (name, description) and Eva will discover it at session start. Use `/pipeline` to convert raw markdown to pipeline XML format inline."

No setup logic changes -- discovery is automatic. This is documentation in the setup skill.

**Files to modify:**
- `skills/pipeline-setup/SKILL.md` -- add informational section after Step 3a (hooks)

**Acceptance criteria:**
- Note appears after hook installation (user already understands the agents directory)
- Note explains: drop file -> discovered at boot, or paste markdown -> Eva converts
- Note mentions read-only default and hook customization for write access

**Estimated complexity:** Low (add a paragraph to existing skill file)

## Comprehensive Test Specification

### Step 0 Tests: Agent Discovery Section

| ID | Category | Description |
|----|----------|-------------|
| T-0008-001 | Happy | agent-system.md contains `<section id="agent-discovery">` with all five sub-protocols (discovery, conflict detection, brain persistence, fallback to context-brief, inline creation) |
| T-0008-002 | Happy | Core agent list in the section matches exactly: cal, colby, roz, ellis, agatha, robert, sable, investigator, distillator (9 names) |
| T-0008-003 | Failure | Section explicitly states discovered agents NEVER replace core routing -- additive only |
| T-0008-004 | Failure | Section explicitly states Eva does NOT write agent files -- routes to Colby |
| T-0008-005 | Boundary | Section addresses brain-unavailable fallback: context-brief.md for session-scoped preferences |
| T-0008-006 | Regression | Existing `<routing id="auto-routing">` section is unchanged except for the new subsection addition |
| T-0008-007 | Regression | Existing `<section id="shared-behaviors">` is unchanged |

### Step 1 Tests: Boot Sequence Discovery

| ID | Category | Description |
|----|----------|-------------|
| T-0008-010 | Happy | default-persona.md boot sequence contains step 3c positioned between 3b and 4 |
| T-0008-011 | Happy | Step 3c specifies Glob scan of `.claude/agents/*.md` |
| T-0008-012 | Happy | Step 3c specifies YAML frontmatter `name` field comparison against core constant |
| T-0008-013 | Failure | Step 3c specifies error handling: scan failure logs warning and proceeds with core agents only |
| T-0008-014 | Boundary | Step 3c handles zero discovered agents (no announcement or "No custom agents found") |
| T-0008-015 | Boundary | Step 3c handles agents directory containing only core agents (no discovery announcement) |
| T-0008-016 | Regression | Existing boot steps 1-3b and 4-6 are unmodified except step 6 announcement update |
| T-0008-017 | Happy | Step 6 announcement includes discovered agent count when > 0 |

### Step 2 Tests: Auto-Routing Extension

| ID | Category | Description |
|----|----------|-------------|
| T-0008-020 | Happy | "Discovered Agent Routing" subsection exists within `<routing id="auto-routing">` |
| T-0008-021 | Happy | Core routing table is checked FIRST before discovered agents |
| T-0008-022 | Happy | Conflict resolution asks user once per (intent, agent) pair |
| T-0008-023 | Happy | Brain-available path uses `agent_capture` with `thought_type: 'preference'` |
| T-0008-024 | Failure | Brain-unavailable path falls back to context-brief.md under "## Routing Preferences" |
| T-0008-025 | Boundary | Explicit name mention routes to discovered agent without conflict check |
| T-0008-026 | Failure | Discovered agent with no description overlap: available only via explicit name mention |
| T-0008-027 | Regression | Existing intent detection table rows are unchanged |
| T-0008-028 | Security | Discovered agents cannot shadow core agents without explicit user consent |

### Step 3 Tests: Inline Agent Creation

| ID | Category | Description |
|----|----------|-------------|
| T-0008-030 | Happy | Detection heuristic described in protocol detects agent-like markdown patterns |
| T-0008-031 | Happy | Conversion template produces valid XML per xml-prompt-schema.md (7 tags in order) |
| T-0008-032 | Happy | YAML frontmatter includes name, description, and conservative disallowedTools |
| T-0008-033 | Happy | Agent-preamble.md reference injected in `<required-actions>` |
| T-0008-034 | Happy | User confirmation step exists before Colby write |
| T-0008-035 | Failure | Eva does NOT write the file -- invokes Colby with explicit path and content |
| T-0008-036 | Failure | If user declines conversion, no file is written |
| T-0008-037 | Boundary | Pasted markdown missing `<workflow>` section: converted agent omits `<workflow>` tag |
| T-0008-038 | Boundary | Pasted markdown with name colliding with core agent: Eva rejects with explanation |
| T-0008-039 | Happy | Post-write discovery re-scan registers the new agent |
| T-0008-040 | Security | Enforcement note announces read-only default for new agent |
| T-0008-041 | Happy | xml-prompt-schema.md contains "## Agent Conversion Template" section |
| T-0008-042 | Regression | Existing xml-prompt-schema.md sections are unchanged |

### Step 4 Tests: Subagent Table Update

| ID | Category | Description |
|----|----------|-------------|
| T-0008-050 | Happy | `<gate id="no-skill-tool">` table includes note about discovered agents |
| T-0008-051 | Happy | `<section id="architecture">` subagent table includes note about discovered agents |
| T-0008-052 | Regression | Core 9 agent rows in both tables are unchanged |

### Step 5 Tests: Pipeline-Setup Awareness

| ID | Category | Description |
|----|----------|-------------|
| T-0008-060 | Happy | SKILL.md contains informational note about agent discovery after Step 3a |
| T-0008-061 | Happy | Note mentions: drop file, paste markdown, read-only default, hook customization |
| T-0008-062 | Regression | Existing SKILL.md setup procedure steps are unchanged |

### Telemetry

| Step | Telemetry | Trigger | Absence Means |
|------|-----------|---------|---------------|
| Step 1 | Eva boot announcement: "Discovered N custom agent(s)" or "No custom agents found" | Every session boot when agents dir contains non-core files | Discovery scan silently failed or was skipped |
| Step 2 | Eva routing announcement: "Routing to [discovered-agent] for [intent] (user preference)" | User message matches discovered agent routing preference | Routing preference not persisted or not queried |
| Step 3 | Eva announcement: "Converted [name] to pipeline XML format. Invoking Colby to write." | User pastes agent markdown and confirms conversion | Inline creation detection or conversion failed |
| Step 4 | Structural only (table notes) -- no runtime telemetry | N/A | N/A |
| Step 5 | Structural only (setup note) -- no runtime telemetry | N/A | N/A |

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| Boot discovery scan (Step 1) | List of `{name, description, file_path}` for discovered agents | Auto-routing extension (Step 2) | Step 2 consumes discovered agent list to check for routing conflicts |
| Conflict resolution (Step 2) | `{intent, chosen_agent}` routing preference | Brain (`agent_capture`) or context-brief.md | Step 2 persists preference for cross-session retrieval |
| Inline creation (Step 3 -- Eva prepares content) | `{file_path, file_content}` | Colby subagent invocation (Step 3) | Eva passes prepared content to Colby for write |
| Inline creation post-write (Step 3) | Triggers re-scan | Boot discovery scan (Step 1 logic) | Step 3 re-invokes discovery after Colby writes |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| Discovery scan (Glob + frontmatter read) | `{name, description, file_path}[]` | Routing conflict check | 1 -> 2 |
| Conflict resolution prompt | `{intent, chosen_agent}` | `agent_capture` / context-brief.md | 2 (self-contained) |
| Eva XML conversion | `{file_path, content}` | Colby subagent write | 3 (self-contained) |
| Colby post-write | File on disk | Discovery re-scan | 3 -> 1 (re-invocation) |

No orphan producers. All data flows have consumers.

## Anti-Goals

1. **Anti-goal: Automated trust scoring or quality verification of discovered agents.** Reason: Quality is the user's responsibility -- the pipeline does not audit user-provided agent definitions for correctness, safety, or effectiveness. Revisit: if discovered agents cause pipeline failures frequently enough to warrant automated validation (3+ incidents logged in error-patterns.md).

2. **Anti-goal: Auto-modifying enforce-paths.sh to grant write access to discovered agents.** Reason: Hook modification is a security-sensitive operation that should require explicit human action. Discovered agents default to read-only, which is the safe default. Revisit: if a standardized "write-capable custom agent" pattern emerges with sufficient demand.

3. **Anti-goal: Custom slash commands for discovered agents.** Reason: Slash commands require files in `.claude/commands/` with specific structure. Auto-generating commands from discovered agents would create a coupling between discovery and the command system that is fragile and hard to debug. Revisit: if users consistently request `/custom-agent` shortcuts rather than using explicit name mentions.

## Blast Radius

### Files Modified (all in `source/`)

| File | Change Type | Impact |
|------|-------------|--------|
| `source/rules/default-persona.md` | Add step 3c to boot sequence, update step 6 | Eva boot behavior in all target projects |
| `source/rules/agent-system.md` | Add `<section id="agent-discovery">`, add routing subsection, update tables | Eva routing + agent architecture documentation |
| `source/references/xml-prompt-schema.md` | Add "Agent Conversion Template" section | Reference for XML tag vocabulary |
| `skills/pipeline-setup/SKILL.md` | Add informational note | Setup user experience |

### Files NOT Modified (verified no changes needed)

| File | Reason |
|------|--------|
| `source/hooks/enforce-paths.sh` | Catch-all `*)` already blocks unknown agents -- correct default behavior |
| `source/hooks/enforcement-config.json` | No new config keys needed -- discovery is behavioral |
| `source/agents/*.md` (all 9) | Core agents unchanged |
| `source/commands/*.md` (all 7) | No new commands |
| `source/references/agent-preamble.md` | Unchanged -- discovered agents reference it, preamble does not reference them |
| `source/references/invocation-templates.md` | No new invocation template needed -- discovered agents use the standard template |
| `source/rules/pipeline-orchestration.md` | No changes to mandatory gates, brain capture model, or pipeline flow |
| `source/rules/pipeline-models.md` | Discovered agents inherit Opus default (conservative). No model table changes. |

### Consumers of Modified Files

| File | Consumers |
|------|-----------|
| `source/rules/default-persona.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/rules/`), all target projects |
| `source/rules/agent-system.md` | `skills/pipeline-setup/SKILL.md` (copies to `.claude/rules/`), all target projects |
| `source/references/xml-prompt-schema.md` | Agent persona authors (reference), `skills/pipeline-setup/SKILL.md` (copies to `.claude/references/`), tests in `tests/xml-prompt-structure/` |
| `skills/pipeline-setup/SKILL.md` | Plugin skill system (invoked via `/pipeline-setup`) |

## Notes for Colby

1. **Step ordering matters.** Step 0 (agent-system.md section) must be implemented first because Steps 1-4 all reference content defined in that section. Steps 1-4 can be done in any order after Step 0. Step 5 should be last.

2. **Boot sequence numbering.** The new step is 3c (not 4) to avoid renumbering existing steps 4-6. The boot sequence uses sub-numbering already (3b exists for branching strategy).

3. **Core agent constant.** Define the list once in `<section id="agent-discovery">` and reference it from the boot sequence. Do not duplicate the list in two places.

4. **XML conversion is a guide, not code.** The inline creation protocol describes what Eva should do in natural language + structural rules. There is no code to write -- it's behavioral instructions for Eva backed by the existing xml-prompt-schema.md tag vocabulary.

5. **Enforce-paths.sh catch-all is the safety net.** Do not modify the hook. The existing `*)` case at line 112 already blocks unknown agent types. This is the mechanical enforcement that backs up the behavioral "read-only by default" instruction.

6. **Brain capture uses existing infrastructure.** The `agent_capture` calls for routing preferences use `thought_type: 'preference'` which already exists in the brain schema (see xml-prompt-schema.md thought type enum). No brain schema changes needed.

7. **Placeholder handling.** `source/rules/default-persona.md` uses `{pipeline_state_dir}` placeholders. The new step 3c should use `.claude/agents/` directly (not a placeholder) because the agents directory is always at that fixed path -- it is not project-configurable like the pipeline state directory.

8. **Section placement in agent-system.md.** The `<section id="agent-discovery">` goes after `<section id="shared-behaviors">` and before the closing of the file. The routing subsection goes inside `<routing id="auto-routing">` after the existing "### Auto-Routing Confidence" subsection.

## DoD: Verification

| Requirement | Step | Test IDs | Status |
|-------------|------|----------|--------|
| R1: Boot-time discovery scan | Step 1 | T-0008-010 through T-0008-017 | Designed |
| R2: Inline creation via paste + Colby write | Step 3 | T-0008-030 through T-0008-042 | Designed |
| R3: Semantic conflict detection | Step 0, Step 2 | T-0008-001, T-0008-020 through T-0008-028 | Designed |
| R4: Brain persistence for routing preferences | Step 2 | T-0008-023 | Designed |
| R5: Session-scoped fallback without brain | Step 2 | T-0008-024 | Designed |
| R6: Core agents hardcoded, discovered additive | Step 0, Step 4 | T-0008-003, T-0008-006, T-0008-028, T-0008-052 | Designed |
| R7: XML conversion per schema + preamble reference | Step 3 | T-0008-031 through T-0008-033, T-0008-041 | Designed |
| R8: All changes in source/ only | All | Blast radius table | Designed |
| R9: No trust scoring | Anti-goal #1 | T-0008-003 (additive only) | Designed (explicitly excluded) |
| R10: No registry, manifest, or API | Decision section | N/A (architectural constraint) | Designed |
| R11: Eva never writes agent files | Step 3 | T-0008-004, T-0008-035 | Designed |
| R12: Enforce-paths.sh blocks unknown agents | Blast radius (no changes) | T-0008-040 | Designed (existing behavior preserved) |

### Architectural Decisions Not in Spec

1. **Step 3c position (between 3b and 4):** Discovery scan runs before brain health check because brain is only needed for preference lookup, not for finding files on disk. This ordering means discovery works even if brain check fails.
2. **Conservative disallowedTools default:** New agents get `Agent, Write, Edit, MultiEdit, NotebookEdit` (read-only) rather than requiring users to specify. Safer default -- users explicitly opt-in to write access via hook modification.
3. **No model table entry for discovered agents:** Discovered agents inherit Opus by default (ambiguous sizing defaults UP per pipeline-models.md enforcement rule #3). This is safe but potentially wasteful. Users can specify model in the persona file's `<identity>` tag.

### Rejected During Design

1. **New `/create-agent` command:** Would require a new command file and registration. Inline creation within the existing conversation flow is simpler and does not add command system complexity.
2. **Automatic write access based on agent description:** Rejected because description parsing for security decisions is fragile. Read-only default with manual override is safer.

### Technical Constraints Discovered

1. `enforce-paths.sh` line 112-118: The `*)` catch-all blocks ALL unknown agent types. This is the correct mechanical enforcement for discovered agents but means any discovered agent that needs write access requires manual hook modification. Documenting this is sufficient -- automating it would weaken the security boundary.
2. `xml-prompt-schema.md` is not currently in the pipeline-setup installation manifest's mandatory files list (it's referenced by agents but not explicitly installed). The conversion template addition in Step 3 does not change this -- the schema file lives in `source/references/` and is available to the pipeline.

---

ADR saved to `docs/architecture/ADR-0008-agent-discovery.md`. 6 steps (0-5), 42 total tests. Next: Roz reviews the test spec.
