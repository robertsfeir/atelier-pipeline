# XML Prompt Tag Vocabulary

This document defines every XML tag used in atelier-pipeline agent persona
files, skill command files, invocation prompts, and shared references. No
ad-hoc tags -- if a tag is not listed here, it should not appear in any
pipeline file.

## Persona File Tags

Agent persona files (`{config_dir}/agents/*.md`) use these 7 tags in this order.
`<identity>` is always first, `<output>` is always last.

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<identity>` | Who the agent is, role, pronouns, model | None |
| `<required-actions>` | Cognitive directive + proactive behaviors (numbered list) | None |
| `<workflow>` | Ordered steps for the agent's main work | None |
| `<examples>` | 2-3 short scenarios showing the agent doing its job correctly | None |
| `<tools>` | Tool access list and tool-specific guidance | None |
| `<constraints>` | Boundaries and forbidden actions | None |
| `<output>` | Output format templates, DoR/DoD structure, handoff messages | None |

Tag ordering: `<identity>` first, then `<required-actions>`, `<workflow>`,
`<examples>`, `<tools>`, `<constraints>`, `<output>` last. This order
ensures the agent reads its identity and required-actions before workflow,
sees examples of correct work before encountering boundaries, and knows
its output format last.

## Skill Command Tags

Skill command files (`{config_dir}/commands/*.md`) use a slightly different
structure for conversational agents running in the main thread.

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<identity>` | Who the skill agent is, voice, personality | None |
| `<required-actions>` | Cognitive directive (no numbered steps for skills) | None |
| `<required-reading>` | Files to read at start of every invocation | None |
| `<behavior>` | How the skill operates -- question flow, modes, phases | None |
| `<output>` | Output format, where to save, handoff message | None |
| `<constraints>` | Boundaries and forbidden actions | None |

## Invocation Prompt Tags

Eva constructs invocation prompts using these tags. `<task>` is always first.
Tags with no content for a given invocation are omitted entirely, not left empty.

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<task>` | What to do -- observed symptom for debug, feature name for build. Task is always first. | None |
| `<required-actions>` | Per-invocation capture requirements (when needed beyond persona defaults) | None |
| `<brain-context>` | Pre-fetched brain context (only when brain is available and returned results) | None |
| `<colby-context>` | Pre-collected scout evidence for Colby (file content, patterns, brain results) | None |
| `<qa-evidence>` | Pre-collected scout evidence for Poirot (changed files, test output, brain results) | None |
| `<context>` | Decisions from context-brief.md | None |
| `<hypotheses>` | Debug invocations only -- Eva's theory + alternative | None |
| `<read>` | Comma-separated file paths to read | None |
| `<warn>` | Retro lesson reference when error-patterns.md shows 3+ recurrences | None |
| `<constraints>` | Boundaries for this specific invocation (3-5 bullets) | None |
| `<output>` | What to produce, format, where to write it | None |

## Scout Context Tags

The `<colby-context>` and `<qa-evidence>` tags carry pre-collected scout
evidence injected by Eva before invoking Colby or Poirot. When present, the
receiving agent uses the provided content directly and skips redundant reads
or test runs.

| Tag | Consumer | Content |
|-----|----------|---------|
| `<colby-context>` | Colby | File content for ADR step files, grep pattern results (file:line only), brain search results for the step's feature area. When provided: do NOT re-read listed files, do NOT re-grep listed patterns, read additional files only if context is insufficient for a specific decision. |
| `<qa-evidence>` | Poirot | Full content of changed source files (≤200 lines; ±20 lines per hunk if larger), targeted test output (`pytest` or `node --test` scoped to changed files, first 100 lines), brain search results for changed file names + feature area. When provided: do NOT re-read listed files, do NOT re-run listed tests, begin analysis immediately. |

Eva populates these tags via haiku scout fan-out (see `pipeline-orchestration.md`
phase-sizing section). Tags are omitted when scouts are skipped (Micro pipelines,
Scoped Re-run Mode, Re-invocation fix cycle).

## Brain Context Tags

The `<brain-context>` tag in invocations contains `<thought>` elements with
these attributes:

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<thought>` | A single brain thought injected as context | `type`, `agent`, `phase`, `relevance` |

### `<thought>` Attribute Values

**`type`** -- matches the brain `thought_type` enum:
- `decision` -- architectural or design decision
- `pattern` -- reusable implementation pattern
- `lesson` -- retro lesson learned from past pipeline
- `correction` -- user correction of agent behavior
- `drift` -- spec-vs-implementation drift finding
- `insight` -- observation or realization during work
- `handoff` -- context passed between pipeline phases
- `rejection` -- explicitly rejected approach with reasoning
- `preference` -- user preference captured during conversation

**`phase`** -- pipeline phase when the thought was captured:
- `design` -- during spec/UX/architecture work
- `build` -- during implementation
- `qa` -- during testing and QA review
- `review` -- during acceptance review (Robert/Sable)
- `reconciliation` -- during spec/UX reconciliation
- `retro` -- during post-pipeline retrospective
- `handoff` -- during phase transition context packaging

**`agent`** -- source agent who captured the thought. Any of the 10 agents
(sarah, colby, agatha, robert, sable, eva, poirot, ellis, distillator).

**`relevance`** -- relevance score from agent_search, ranging from 0.00 to 1.00.

## Inline Content Tags

These tags appear within agent workflow content as inline structural markers.
They are used in invocation examples and workflow descriptions to denote
variable content that Eva fills in at invocation time.

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<feature>` | Feature name placeholder in workflow descriptions | None |
| `<test-files>` | Test file paths placeholder in workflow descriptions | None |
| `<scope>` | Scope description placeholder in workflow descriptions | None |
| `<type>` | Type/category placeholder in workflow descriptions | None |

## Retro Lessons Tags

The `retro-lessons.md` file uses these tags:

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<retro-lessons>` | Root wrapper for all lessons | None |
| `<lesson>` | A single retro lesson | `id` (3-digit zero-padded), `agents` (comma-separated agent names) |
| `<what-happened>` | Description of what went wrong | None |
| `<root-cause>` | Why it went wrong | None |
| `<rules>` | Container for per-agent rules derived from the lesson | None |
| `<rule>` | A specific rule for one agent | `agent` (single agent name) |

### Attribute Details

- `<lesson id="001" agents="sarah, colby">` -- the `id` is a three-digit
  zero-padded string, monotonically increasing. The `agents` list enables
  filtering: agents can read only lessons relevant to them.
- `<rule agent="sarah">` -- the `agent` attribute matches one of the agents
  listed in the parent `<lesson>`'s `agents` attribute. Every agent listed
  in `agents` should have a corresponding `<rule>` child.

## Rules File Tags

Rules files (`source/rules/*.md`) use these tags to wrap logical sections.
Unlike persona files (which have a fixed 7-tag structure), rules files use
tags selectively -- only sections that benefit from unambiguous boundaries
get wrapped.

**Wrapping criteria:** A section gets an XML tag when it meets one or more of:
1. It contains a gate or constraint that must not be missed (mandatory gates, forbidden actions)
2. It contains a procedure with ordered steps (boot sequence, investigation protocol)
3. It contains a lookup table that agents reference mechanically (model tables, routing tables, triage matrix)
4. It defines a protocol with multiple interacting rules (brain capture model, wave execution)

Short, self-contained sections (1-3 paragraphs) that are already clear from
their markdown header do NOT need wrapping.

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<gate>` | A mandatory behavioral gate -- something Eva or agents must never skip | `id` (kebab-case) |
| `<protocol>` | An ordered operational procedure with numbered steps or a defined sequence | `id` (kebab-case) |
| `<routing>` | Intent detection tables and routing rules | `id` (kebab-case) |
| `<model-table>` | Model selection tables and classifier rules | `id` (kebab-case) |
| `<section>` | General-purpose semantic section for content that benefits from boundaries but does not fit gate/protocol/routing/model-table categories | `id` (kebab-case) |

### Attribute Convention (Rules and Reference Files)

Tags use an `id` attribute for filtering and identification:
- `<gate id="mandatory-gates">` -- enables grep-based lookup of specific gates
- `<template id="sarah-adr">` -- enables lookup of specific invocation templates
- `<protocol id="boot-sequence">` -- enables lookup of specific procedures

The `id` attribute is kebab-case, descriptive, and unique within a file.

## Reference File Tags

Reference files (`source/references/*.md`) use these tags:

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<framework>` | The core framework definition (DoR/DoD structure, how-it-works) | `id` (kebab-case) |
| `<agent-dod>` | Per-agent DoD conditions block | None |
| `<template>` | A single invocation template for one agent scenario | `id` (kebab-case) |
| `<operations>` | An operational procedure block (QA flow, batch mode, wave execution) | `id` (kebab-case) |
| `<matrix>` | A decision matrix used mechanically (triage consensus) | `id` (kebab-case) |
| `<section>` | General-purpose semantic section (shared with rules files) | `id` (kebab-case) |

## Plugin Skill Tags

Plugin skill files (`skills/*/SKILL.md`) use these tags to wrap logical sections.
These are procedural instruction files consumed by Claude when a skill is invoked.
They contain ordered procedures, conditional paths, error handling tables, guardrails,
and scope controls. Like rules files, skill files use tags selectively -- only sections
that benefit from unambiguous boundaries get wrapped.

| Tag | Purpose | Attributes |
|-----|---------|------------|
| `<procedure>` | An ordered multi-step setup or execution procedure | `id` (kebab-case) |
| `<gate>` | Security constraints, guardrails, mandatory rules (reused from rules vocabulary) | `id` (kebab-case) |
| `<error-handling>` | Error conditions table with messages and recovery guidance | `id` (kebab-case) |
| `<protocol>` | A routing decision or conditional execution path (reused from rules vocabulary) | `id` (kebab-case) |
| `<section>` | General-purpose semantic section (shared across all file types) | `id` (kebab-case) |

## Agent Conversion Template

When converting raw markdown agent definitions to pipeline-compatible XML
format (see `agent-system.md` section "Agent Discovery"), use this structural
mapping. Tags appear in the standard persona file order: `<identity>` first,
`<output>` last.

### YAML Frontmatter

```yaml
---
name: {kebab-case-agent-name}
description: {one-line description from the agent's identity/role}
disallowedTools:
  - Agent
  - Write
  - Edit
  - MultiEdit
  - NotebookEdit
---
```

The `disallowedTools` list is the conservative read-only default. Users who
need write access for a discovered agent must also add a per-agent
frontmatter hook (e.g., enforce-{name}-paths.sh) to the agent's overlay.

### Structural Mapping

| Source Content | Target Tag | Required |
|----------------|------------|----------|
| Role, identity, pronouns, personality | `<identity>` | Yes |
| Cognitive directive, proactive behaviors | `<required-actions>` | Yes -- always includes reference to `{config_dir}/references/agent-preamble.md` |
| Ordered steps, process, methodology | `<workflow>` | No -- omit tag if source has no workflow |
| Scenarios showing correct behavior | `<examples>` | No -- omit tag if source has no examples |
| Tool access list, tool-specific guidance | `<tools>` | No -- omit tag if source has no tool list |
| Rules, boundaries, forbidden actions | `<constraints>` | Yes -- include at minimum: "Follow DoR/DoD framework" |
| Output format, templates, handoff messages | `<output>` | Yes -- if absent in source, use: "Produce structured output with DoR and DoD sections." |

### Required `<required-actions>` Content

Every converted agent's `<required-actions>` must begin with:

```
Follow the shared required actions in `{config_dir}/references/agent-preamble.md`:
DoR first, read upstream artifacts, review retro lessons, review brain context
(if provided), DoD last.
```

Agent-specific actions from the source material follow after this reference.
