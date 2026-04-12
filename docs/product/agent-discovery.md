## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Eva scans `.claude/agents/` at session boot, diffs against known core agents, announces unknowns | ADR-0008, R1 |
| 2 | Users can paste agent markdown into chat; Eva converts to pipeline XML format and routes to Colby to write the file | ADR-0008, R2 |
| 3 | Conflict detection is semantic — Eva reads discovered agent descriptions and compares against core routing table | ADR-0008, R3 |
| 4 | When brain is available, routing preferences persist across sessions via `agent_capture` | ADR-0008, R4 |
| 5 | When brain is unavailable, conflict resolution is session-scoped only (context-brief.md) | ADR-0008, R5 |
| 6 | Core 9 agents remain hardcoded in agent-system.md; discovered agents are additive only | ADR-0008, R6 |
| 7 | Converted agents get: agent-preamble.md reference, YAML frontmatter, XML tags per xml-prompt-schema.md | ADR-0008, R7 |
| 8 | Eva must NOT gain Write/Edit access — routes to Colby for file creation | ADR-0008, R11 |
| 9 | Discovered agents have read-only access by default (enforce-paths.sh catch-all blocks write access) | ADR-0008, R12 |
| 10 | No registry JSON, no manifest, no API — filesystem IS the registry | ADR-0008, R10 |

**Retro risks:** None directly applicable. Discovery scan must be non-blocking — errors log a warning and never prevent session boot.

---

# Feature Spec: Agent Discovery

**Author:** Robert (CPO) | **Date:** 2026-04-12
**Status:** Draft
**ADR:** [ADR-0008](../architecture/ADR-0008-agent-discovery.md)

## The Problem

The pipeline currently supports exactly 9 hardcoded agents defined in `source/shared/agents/`. Users who want custom agents — domain experts, project-specific reviewers, specialized tools — must manually create persona files, manually add routing rules, and manually wire enforcement hooks. There is no discovery mechanism: Eva does not know about agents she was not told about at design time.

Additionally, users who want to bring an existing agent definition into the pipeline must hand-convert it to the pipeline's XML persona format, understand YAML frontmatter conventions, and manually add it to the agents directory.

## Who Is This For

**Project teams** who want to extend the pipeline with domain-specific agents (e.g., a security reviewer for a fintech project, a localization agent, a project-specific documentation specialist).

**Users integrating agents from other sources** (Anthropic cookbook, team wikis, custom GPT exports) who want to convert them to pipeline-compatible format without manually learning the XML schema.

**Pipeline operators** who want custom routing preferences (e.g., "always route security questions to Sentinel, not Colby") to persist across sessions.

## Business Value

- **Extensibility** — add custom agents by dropping a `.md` file in `.claude/agents/`; no source code changes, no configuration files
- **Lower barrier to contribution** — paste agent markdown into chat; Eva handles the XML conversion
- **Safe defaults** — discovered agents are read-only by default; write access requires explicit hook modification
- **Core routing integrity** — discovered agents never shadow core agents without explicit user consent

## User Flows

### Flow 1: Automatic Discovery at Session Boot

Eva runs a Glob scan of `.claude/agents/` at session boot (step 3c of the boot sequence), compares filenames against the core agent list, and announces any non-core agents:

```
Discovered 2 custom agent(s):
  - sentinel (Security auditor — Semgrep-backed SAST)
  - locale-reviewer (Localization QA — reviews copy for tone and translation gaps)
Custom agents have read-only access by default.
```

If no custom agents are found, Eva announces nothing (silent on zero results). Discovery scan failure logs a warning and proceeds with core agents — it never blocks session boot.

### Flow 2: Conflict Detection and Routing Preference

When a discovered agent's description overlaps with a core agent's routing domain, Eva announces the conflict once per session and asks the user to choose:

```
For security-related requests, I can route to:
  - sentinel (core) — comprehensive security audit
  - sec-advisor (custom) — lightweight advisory review

Which do you prefer for security questions? (sentinel / sec-advisor)
```

The user's response is recorded:
- Brain available: `agent_capture` with `thought_type: 'preference'`, `source_agent: 'eva'`, metadata includes `routing_rule: {intent} -> {chosen_agent}`. On future sessions, Eva queries brain before asking.
- Brain unavailable: appended to `context-brief.md` under `## Routing Preferences`. Session-scoped only — re-asked next session.

If there is no conflict, the discovered agent is available via explicit name mention only ("ask locale-reviewer about this"). It does not appear in automatic routing.

### Flow 3: Inline Agent Creation

When a user pastes agent markdown into the chat, Eva detects the agent-like content, prepares a pipeline-compatible XML conversion, presents it for approval, and routes to Colby to write the file:

1. User pastes raw agent markdown
2. Eva asks: "This looks like an agent definition. Want me to convert it to a pipeline agent?"
3. Eva presents the converted content with YAML frontmatter and XML tags for user review
4. User approves
5. Eva invokes Colby: "Write this file to `.claude/agents/{name}.md`" with full content
6. Eva re-runs the discovery scan and announces: "{agent-name} is now available. It has read-only access by default. To grant write access, add a case to `.claude/hooks/enforce-paths.sh`."

Eva never writes the file herself.

## Acceptance Criteria

**Boot-time discovery:**
- AC-1: Eva MUST scan `.claude/agents/` during session boot using Glob (not Bash `find` or `ls`).
- AC-2: Eva MUST compare discovered agent filenames against the core agent constant: `cal, colby, roz, ellis, agatha, robert, sable, investigator, distillator`.
- AC-3: Eva MUST announce each discovered non-core agent with its name and description.
- AC-4: If the discovery scan errors, Eva MUST log a warning and proceed with core-only routing. The scan failure MUST NOT block session boot.
- AC-5: If zero non-core agents are found, Eva MUST produce no discovery announcement (silent).

**Conflict detection and routing:**
- AC-6: Core routing table MUST be checked first. Discovered agents MUST NOT shadow core agents without explicit user preference.
- AC-7: Eva MUST ask the user at most once per (intent, agent) pair per session when a routing conflict exists.
- AC-8: When brain is available, routing preference MUST be captured via `agent_capture` with `thought_type: 'preference'` and metadata containing `routing_rule: {intent} -> {chosen_agent}`.
- AC-9: When brain is unavailable, routing preference MUST be written to `context-brief.md` under `## Routing Preferences`.
- AC-10: Explicit agent name mention MUST route to any discovered agent regardless of conflicts — explicit mention is always a direct override.
- AC-11: Discovered agents with no routing conflict MUST be available ONLY via explicit name mention, not via automatic intent-based routing.

**Inline agent creation:**
- AC-12: Eva MUST detect agent-like markdown (identity/role description, behavioral rules, tool/constraint lists) and offer conversion.
- AC-13: Converted agent files MUST include YAML frontmatter with `name` (kebab-case), `description` (one-line), and `disallowedTools` (conservative default: `Agent, Write, Edit, MultiEdit, NotebookEdit`).
- AC-14: Converted agent files MUST include a reference to `agent-preamble.md` in the `<required-actions>` XML tag.
- AC-15: Converted agent content MUST use the XML tag vocabulary from `xml-prompt-schema.md`: `<identity>`, `<required-actions>`, `<workflow>` (if present in source), `<constraints>`, `<output>`.
- AC-16: Eva MUST present the converted content to the user for approval BEFORE invoking Colby.
- AC-17: If the user declines conversion, NO file MUST be written.
- AC-18: Eva MUST NOT write the agent file herself. Eva invokes Colby with the explicit file path and full content.
- AC-19: When the user pastes an agent with a name colliding with a core agent, Eva MUST reject the conversion with an explanation.
- AC-20: After Colby writes the new agent file, Eva MUST re-run the discovery scan to register the new agent in the current session.

**Enforcement:**
- AC-21: Discovered agents MUST have read-only access by default. The `enforce-paths.sh` catch-all (`*)` case) blocks write access from unknown agent types.
- AC-22: Eva MUST announce the read-only default when a new agent is created inline: "{agent-name} has read-only access by default. To grant write access, add a case to `.claude/hooks/enforce-paths.sh`."

## Edge Cases

**Agents directory does not exist:** Eva logs a warning and proceeds with core-only routing. Not expected in normal installations.

**Agent file with malformed frontmatter:** Eva reads what it can. If `name` field is missing or unparseable, Eva treats the file as unknown and skips it in the discovery announcement. No crash.

**Discovered agent with same routing domain as two core agents:** Eva announces all conflicts separately and asks the user to resolve each.

**User pastes content that is not an agent definition:** Eva should not offer conversion. The detection heuristic (identity/role + behavioral rules + tool/constraint lists) filters out most non-agent content. False positives result in Eva asking an unnecessary question — the user declines.

**Anti-goal — quality scoring:** The pipeline does not audit discovered agent definitions for correctness, safety, or effectiveness. Quality is the user's responsibility.

**Anti-goal — auto-modifying enforce-paths.sh:** Granting write access to discovered agents requires explicit human action (manual hook edit). This is intentional security behavior.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Boot-time discovery scan | Done | Step 3c added to boot sequence in default-persona.md |
| 2 | Inline agent creation with Colby write | Done | Inline creation protocol in agent-system.md `<section id="agent-discovery">` |
| 3 | Semantic conflict detection | Done | Discovered Agent Routing subsection in auto-routing section |
| 4 | Brain persistence for routing preferences | Done | `agent_capture` with `thought_type: 'preference'` |
| 5 | Session-scoped fallback without brain | Done | context-brief.md under `## Routing Preferences` |
| 6 | Core agents hardcoded, discovered additive | Done | Core agent constant defined in agent-system.md; discovered agents never replace core routing |
| 7 | XML conversion per schema + preamble reference | Done | Conversion template in agent-system.md; preamble reference injected |
| 8 | Eva never writes agent files | Done | Routes to Colby with file path and content |
| 9 | Discovered agents read-only by default | Done | enforce-paths.sh catch-all blocks unknown agent writes; Eva announces default on creation |
| 10 | No registry, manifest, or API | Done | Filesystem is the registry; no new config files |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled — no TBD, no placeholders
