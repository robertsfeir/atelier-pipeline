# XML Prompt Tag Vocabulary

This document defines every XML tag used in atelier-pipeline agent persona
files, skill command files, invocation prompts, and shared references. No
ad-hoc tags -- if a tag is not listed here, it should not appear in any
pipeline file.

## Persona File Tags

Agent persona files (`.claude/agents/*.md`) use these 7 tags in this order.
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

Skill command files (`.claude/commands/*.md`) use a slightly different
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
| `<context>` | Decisions from context-brief.md | None |
| `<hypotheses>` | Debug invocations only -- Eva's theory + alternative | None |
| `<read>` | Comma-separated file paths to read | None |
| `<warn>` | Retro lesson reference when error-patterns.md shows 3+ recurrences | None |
| `<constraints>` | Boundaries for this specific invocation (3-5 bullets) | None |
| `<output>` | What to produce, format, where to write it | None |

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
(cal, colby, roz, agatha, robert, sable, eva, poirot, ellis, distillator).

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

- `<lesson id="001" agents="cal, colby, roz">` -- the `id` is a three-digit
  zero-padded string, monotonically increasing. The `agents` list enables
  filtering: agents can read only lessons relevant to them.
- `<rule agent="cal">` -- the `agent` attribute matches one of the agents
  listed in the parent `<lesson>`'s `agents` attribute. Every agent listed
  in `agents` should have a corresponding `<rule>` child.
