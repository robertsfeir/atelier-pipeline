# ADR-0006: XML Tag Migration for Rules and Reference Files

## DoR: Requirements Extracted

**Sources:** User task (invocation prompt), source/references/xml-prompt-schema.md (existing schema), source/rules/*.md (4 files), source/references/*.md (5 files, including xml-prompt-schema.md itself), ADR-0005 (prior art for agents/commands migration)

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| 1 | Define XML tag vocabulary for rules files (default-persona.md, agent-system.md, pipeline-orchestration.md, pipeline-models.md) | Task constraints | "Define appropriate XML tags for rules files" |
| 2 | Define XML tag vocabulary for reference files (dor-dod.md, invocation-templates.md, pipeline-operations.md) | Task constraints | "these are NOT personas, so the tag vocabulary may differ" |
| 3 | Update xml-prompt-schema.md with new tag sections for rules and references | Task constraints | "xml-prompt-schema.md must be updated to document the new tag vocabulary" |
| 4 | Tags must be semantic and purposeful -- wrap logical sections, not every paragraph | Task constraints | "don't wrap every paragraph, wrap logical sections that benefit from unambiguous boundaries" |
| 5 | Maintain existing markdown within XML tags (tables, headers inside tags are fine) | Task constraints | "Maintain the existing markdown within XML tags" |
| 6 | Colby edits source/ files ONLY, not .claude/ files | Task context | "Colby edits source/ files only, NOT .claude/ files" |
| 7 | Each file gets its own ADR step for incremental implementation | Task constraints | "Each file gets its own ADR step" |
| 8 | Include test specs for Roz verification per step | Task constraints | "Include test specs for Roz to verify each file's migration" |
| 9 | Schema update (xml-prompt-schema.md) is Step 1 | Task output | "Tag vocabulary additions for xml-prompt-schema.md as Step 1" |
| 10 | Format change only -- no behavioral or content changes | Task context | "No behavioral changes -- purely structural wrapping" |
| 11 | retro-lessons.md already uses XML tags (ADR-0005 Step 3) -- excluded from migration scope | Codebase verification | source/references/retro-lessons.md lines 28-94: already wrapped in `<retro-lessons>`, `<lesson>`, etc. |
| 12 | Pipeline sizing: Small | Task context | "Pipeline sizing: Small" |

**Retro risks:**
- Lesson 003 (Stop Hook Race Condition): Not directly relevant. Hooks do not parse XML tags in rules/reference files -- verified via grep of source/claude/hooks/*.sh.
- No lesson about structural migration failures exists. Primary risk is introducing malformed XML that confuses the model or breaks cross-file references.

**Spec challenge:** The spec assumes wrapping existing markdown sections in XML tags improves model comprehension of rules and reference files. If this is wrong -- if the model already distinguishes sections well via `##` headers in these shorter, more focused files (96-399 lines each) -- the effort produces no behavioral improvement. However: (a) ADR-0005 already committed to XML tags for agents and commands, creating an inconsistency if rules/references remain plain markdown; (b) Anthropic's guidance applies equally to all long-context instruction files; (c) pipeline-orchestration.md at 399 lines is well within the "long enough to benefit" range. Confidence: high for consistency value, moderate for direct behavioral improvement.

---

## Status

Proposed

## Context

ADR-0005 migrated agent persona files (.claude/agents/*.md), skill command files (.claude/commands/*.md), invocation templates, and retro-lessons to XML tag structure. Four rules files and three reference files were excluded from that scope because they are not persona files and need a different tag vocabulary.

The current state:
- **Already using XML tags:** Agent personas (7 tags), skill commands (6 tags), invocation prompts (8 tags), retro-lessons (6 tags), brain context (1 tag + attributes). All documented in xml-prompt-schema.md.
- **Not using XML tags:** source/rules/default-persona.md (148 lines), source/rules/agent-system.md (244 lines), source/rules/pipeline-orchestration.md (399 lines), source/rules/pipeline-models.md (96 lines), source/references/dor-dod.md (190 lines), source/references/invocation-templates.md (350 lines), source/references/pipeline-operations.md (197 lines).
- **Already done, excluded from scope:** source/references/retro-lessons.md (already XML), source/references/xml-prompt-schema.md (the schema itself -- gets new sections, not wrapped).

These files serve a different purpose than persona files. Rules files define Eva's behavior, constraints, and operational procedures. Reference files define shared frameworks consumed by multiple agents. The tag vocabulary must reflect these roles: sections that gate behavior (mandatory gates, forbidden actions), sections that define procedures (boot sequence, investigation discipline), and sections that provide lookup tables (model selection, triage matrix).

## Decision

Wrap logical sections of rules and reference files in semantic XML tags. Two new tag categories are added to xml-prompt-schema.md: "Rules File Tags" and "Reference File Tags."

### Tag Vocabulary: Rules Files

Rules files (source/rules/*.md) use these tags to wrap logical sections. Unlike persona files (which have a fixed 7-tag structure), rules files use tags selectively -- only sections that benefit from unambiguous boundaries get wrapped. Short, self-contained sections (1-3 paragraphs) that are already clear from their markdown header do NOT need wrapping.

**Wrapping criteria:** A section gets an XML tag when it meets one or more of:
1. It contains a gate or constraint that must not be missed (mandatory gates, forbidden actions)
2. It contains a procedure with ordered steps (boot sequence, investigation protocol)
3. It contains a lookup table that agents reference mechanically (model tables, routing tables, triage matrix)
4. It defines a protocol with multiple interacting rules (brain capture model, wave execution)

| Tag | Purpose | Used in |
|-----|---------|---------|
| `<gate>` | A mandatory behavioral gate -- something Eva or agents must never skip | default-persona.md, pipeline-orchestration.md |
| `<protocol>` | An ordered operational procedure with numbered steps or a defined sequence | default-persona.md, pipeline-orchestration.md, agent-system.md |
| `<routing>` | Intent detection tables and routing rules | agent-system.md |
| `<model-table>` | Model selection tables and classifier rules | pipeline-models.md |
| `<section>` | General-purpose semantic section for content that benefits from boundaries but does not fit gate/protocol/routing categories | all rules files |

### Tag Vocabulary: Reference Files

Reference files (source/references/*.md) use these tags:

| Tag | Purpose | Used in |
|-----|---------|---------|
| `<framework>` | The core framework definition (DoR/DoD structure, how-it-works) | dor-dod.md |
| `<agent-dod>` | Per-agent DoD conditions block | dor-dod.md |
| `<template>` | A single invocation template for one agent scenario | invocation-templates.md |
| `<operations>` | An operational procedure block (QA flow, batch mode, wave execution) | pipeline-operations.md |
| `<matrix>` | A decision matrix used mechanically (triage consensus) | pipeline-operations.md |
| `<section>` | General-purpose semantic section (same as rules) | all reference files |

### Attribute Convention

Tags that benefit from filtering or identification use an `id` attribute:
- `<gate id="roz-verifies">` -- enables grep-based lookup of specific gates
- `<template id="cal-adr">` -- enables lookup of specific invocation templates
- `<protocol id="boot-sequence">` -- enables lookup of specific procedures

The `id` attribute is kebab-case, descriptive, and unique within a file.

### What Does NOT Get Wrapped

- The YAML frontmatter (`---paths:---`) on pipeline-orchestration.md and pipeline-models.md stays as-is -- Claude Code requires it.
- The `# H1` title of each file stays outside any tag -- it is the file identity.
- The `<!-- CONFIGURE -->` comment blocks stay as-is.
- Content already using XML tags (retro-lessons.md) is not re-wrapped.
- Markdown tables, headers, and lists inside tags remain markdown -- tags wrap sections, not replace formatting.
- Short transitional paragraphs (1-2 lines) between sections are not wrapped.

## Alternatives Considered

### Alternative A: Reuse Persona Tags (`<identity>`, `<constraints>`, etc.)

Map rules files onto the existing 7-tag persona vocabulary. For example, wrap Eva's forbidden actions in `<constraints>`, her boot sequence in `<workflow>`.

**Rejected because:** Rules files are not personas. Eva's default-persona.md has sections like "What This Means," "Session Boot Sequence," "Forbidden Actions," "Cognitive Independence" -- these map poorly to `<identity>/<workflow>/<constraints>`. Forcing a persona structure onto rules would require restructuring the content, violating the "format change only" constraint. Additionally, the model might confuse rules-file `<constraints>` with persona-file `<constraints>` when both are loaded simultaneously (default-persona.md + agent-system.md are always-loaded alongside persona files).

### Alternative B: Single `<section>` Tag for Everything

Use only `<section id="...">` with descriptive IDs. No semantic tags.

**Rejected because:** This loses the primary benefit of XML tags -- semantic clarity. `<section id="mandatory-gates">` tells the model "this is a section called mandatory gates." `<gate id="mandatory-gates">` tells the model "this is a behavioral gate -- something that must not be skipped." The semantic tag name carries meaning that a generic `<section>` does not.

### Alternative C: No Migration -- Leave Rules/References as Markdown

Accept the inconsistency. Agents and commands use XML; rules and references do not.

**Rejected because:** The inconsistency creates a two-tier system. When Eva loads default-persona.md (markdown headers) alongside an agent persona file (XML tags), the model processes two different structural paradigms in the same context window. Anthropic's guidance specifically warns against mixing structural approaches in the same prompt context.

## Consequences

**Positive:**
- Consistent structural approach across all pipeline files
- Semantic tags (gate, protocol, routing) give the model explicit signals about content type
- Enables future grep-based tooling (`grep -r '<gate' source/rules/` to find all gates)
- IDs on tags enable precise cross-file references

**Negative:**
- 8 files modified (migration effort)
- xml-prompt-schema.md grows by ~40 lines (two new sections)
- Colby must preserve all existing content exactly while adding wrapping

**Neutral:**
- .claude/ copies are NOT updated here -- /pipeline-setup handles that separately
- No hook changes needed -- verified that no hooks parse XML in rules/reference files

## Implementation Plan

### Step 1: Update xml-prompt-schema.md with Rules and Reference Tag Vocabulary

Add two new sections to source/references/xml-prompt-schema.md documenting the rules file tags (`<gate>`, `<protocol>`, `<routing>`, `<model-table>`, `<section>`) and reference file tags (`<framework>`, `<agent-dod>`, `<template>`, `<operations>`, `<matrix>`, `<section>`). Include attribute conventions.

- **Files to modify:** `source/references/xml-prompt-schema.md`
- **Acceptance criteria:**
  - New "Rules File Tags" section exists after "Retro Lessons Tags" section
  - New "Reference File Tags" section exists after "Rules File Tags" section
  - Every tag listed in this ADR's Decision section appears in the schema with Purpose and Attributes columns
  - Attribute convention (id, kebab-case) is documented
  - Wrapping criteria (the 4-point list from Decision) is included
- **Estimated complexity:** Low (additive, ~40 lines)

### Step 2: Migrate source/rules/default-persona.md

Wrap logical sections of Eva's default persona rules file. Key sections to wrap:
- "Session Boot Sequence" -> `<protocol id="boot-sequence">`
- "Forbidden Actions" -> `<gate id="no-code-writing">`
- "Cognitive Independence" -> `<gate id="cognitive-independence">`
- "User-reported bug flow" (within Forbidden Actions) -> `<protocol id="user-bug-flow">`
- "What This Means" -> `<section id="routing-behavior">`
- "Always-Loaded Context" -> `<section id="loaded-context">`
- "Routing Transparency" -> `<section id="routing-transparency">`
- Short pointer sections ("Mandatory Gates", "Investigation Discipline", "Brain Access") remain unwrapped -- they are 2-3 line cross-references, not substantive content.
- "What This Does NOT Mean" -> `<section id="non-requirements">`

- **Files to modify:** `source/rules/default-persona.md`
- **Acceptance criteria:**
  - All gate/protocol/section tags are properly opened and closed
  - CONFIGURE comment block preserved at top
  - H1 title remains outside any tag
  - All existing content preserved verbatim inside tags
  - No nested tags (tags wrap top-level sections only)
  - Placeholder `{pipeline_state_dir}` tokens preserved
- **Estimated complexity:** Low (148 lines, straightforward wrapping)

### Step 3: Migrate source/rules/agent-system.md

Wrap logical sections. Key sections to wrap:
- "Brain Configuration" -> `<section id="brain-config">`
- "Architecture" (Skills + Subagents tables) -> `<section id="architecture">`
- "Eva -- The Central Nervous System" -> `<section id="eva-core">`
- "Pipeline Flow" (Phase Sizing + Phase Transitions) -> `<section id="pipeline-flow">`
- "AUTO-ROUTING RULES" (Intent Detection + Smart Context + Confidence) -> `<routing id="auto-routing">`
- "Subagent Invocation" (Standardized Template) -> `<protocol id="invocation-template">`
- "Custom Commands Are NOT Skills" -> `<gate id="no-skill-tool">`
- "Shared Agent Behaviors" -> `<section id="shared-behaviors">`

- **Files to modify:** `source/rules/agent-system.md`
- **Acceptance criteria:**
  - All tags properly opened and closed
  - CONFIGURE comment block preserved at top
  - H1 title remains outside any tag
  - All existing markdown tables preserved inside tags
  - Code blocks (XML template example) preserved inside tags
  - Placeholder tokens preserved
  - Horizontal rules (`---`) between sections preserved
- **Estimated complexity:** Low-Medium (244 lines, multiple sections)

### Step 4: Migrate source/rules/pipeline-orchestration.md

Wrap logical sections. This is the largest file (399 lines). Key sections to wrap:
- "Brain Access" (Hybrid Capture Model + /devops gates + staleness + seed) -> `<protocol id="brain-capture">`
- "Mandatory Gates" (all 10 gates) -> `<gate id="mandatory-gates">`
- "Investigation Discipline" (Layer Escalation + Hypothesis Tracking) -> `<protocol id="investigation">`
- "State File Descriptions" -> `<section id="state-files">`
- "Phase Sizing Rules" (incl. Micro, Robert Discovery, Large Research Brief) -> `<section id="phase-sizing">`
- "Subagent Invocation & DoR/DoD Verification" -> `<protocol id="invocation-dor-dod">`
- "Pipeline Flow" (Spec Requirement + Sable Gate + Stakeholder Gate + Per-Unit Commits + Review Juncture + Reconciliation + Hard Pauses) -> `<section id="pipeline-flow">`
- "Mockup + UAT Phase" -> `<section id="mockup-uat">`
- "Agent Standards" -> `<gate id="agent-standards">`

- **Files to modify:** `source/rules/pipeline-orchestration.md`
- **Acceptance criteria:**
  - All tags properly opened and closed
  - YAML frontmatter (`---paths:---`) preserved above all content
  - H1 title remains outside any tag
  - All 10 mandatory gates preserved verbatim inside `<gate>` tag
  - Placeholder tokens preserved
  - No content reordering
- **Estimated complexity:** Medium (399 lines, many sections, careful boundary placement)

### Step 5: Migrate source/rules/pipeline-models.md

Wrap logical sections. Key sections to wrap:
- "Fixed-Model Agents" -> `<model-table id="fixed-models">`
- "Size-Dependent Agents" -> `<model-table id="size-dependent">`
- "Agatha's Model" -> `<model-table id="agatha-model">`
- "Task-Level Complexity Classifier" -> `<model-table id="complexity-classifier">`
- "Enforcement Rules" -> `<gate id="model-enforcement">`

- **Files to modify:** `source/rules/pipeline-models.md`
- **Acceptance criteria:**
  - All tags properly opened and closed
  - YAML frontmatter preserved
  - H1 title + intro paragraph remain outside tags
  - All markdown tables preserved inside tags
  - Score table and threshold rule preserved
- **Estimated complexity:** Low (96 lines, clean section boundaries)

### Step 6: Migrate source/references/dor-dod.md

Wrap logical sections. Key sections to wrap:
- "How It Works" + "DoR and DoD Inside `<output>`" -> `<framework id="dor-dod-structure">`
- "DoR Rules" -> `<section id="dor-rules">`
- "Per-Agent Sources" -> `<section id="per-agent-sources">`
- "DoD Universal Conditions" -> `<section id="dod-universal">`
- "Agent-Specific DoD Conditions" (all agent blocks) -> `<agent-dod>`
- "Roz: DoD Enforcement" -> `<section id="roz-enforcement">`
- "Eva's Responsibilities" -> `<section id="eva-responsibilities">`

- **Files to modify:** `source/references/dor-dod.md`
- **Acceptance criteria:**
  - All tags properly opened and closed
  - CONFIGURE comment block preserved
  - H1 title remains outside any tag
  - The code block showing `<output>` tag usage (lines 30-56) preserved inside `<framework>` -- ensure the example XML inside markdown code fences does not confuse tag parsing
  - Placeholder tokens preserved
- **Estimated complexity:** Low-Medium (190 lines)

### Step 7: Migrate source/references/invocation-templates.md

Wrap each invocation template in a `<template>` tag with an id. Key templates:
- `<template id="cal-adr">` -- Cal (ADR Production)
- `<template id="cal-adr-large">` -- Cal (Large ADR Production)
- `<template id="colby-mockup">` -- Colby Mockup
- `<template id="colby-build">` -- Colby Build
- `<template id="roz-investigation">` -- Roz Investigation
- `<template id="roz-test-spec-review">` -- Roz Test Spec Review
- `<template id="roz-test-authoring">` -- Roz Test Authoring
- `<template id="roz-code-qa">` -- Roz Code QA
- `<template id="roz-scoped-rerun">` -- Roz Scoped Re-Run
- `<template id="ellis-commit">` -- Ellis
- `<template id="agatha-writing">` -- Agatha
- `<template id="robert-acceptance">` -- Robert
- `<template id="sable-acceptance">` -- Sable
- `<template id="poirot-blind">` -- Poirot
- `<template id="distillator-compress">` -- Distillator
- `<template id="distillator-validate">` -- Distillator with Validation

- **Files to modify:** `source/references/invocation-templates.md`
- **Acceptance criteria:**
  - Each `### Agent (Scenario)` block wrapped in its own `<template id="...">` tag
  - The existing XML tags inside templates (`<task>`, `<constraints>`, etc.) are preserved -- they are content, not structure
  - CONFIGURE comment block preserved
  - H1 title + intro paragraph remain outside tags
  - Horizontal rules between sections preserved or removed as appropriate (inside templates they are not needed since the tag provides the boundary)
  - Placeholder tokens preserved
  - 16 templates total, each with a unique id
- **Estimated complexity:** Medium (350 lines, 16 template blocks, must not corrupt inner XML)

### Step 8: Migrate source/references/pipeline-operations.md

Wrap logical sections. Key sections to wrap:
- "Invocation Format" -> `<section id="invocation-format">`
- "Brain Context Prefetch" -> `<protocol id="brain-prefetch">`
- "Continuous QA" -> `<operations id="continuous-qa">`
- "Triage Consensus Matrix" -> `<matrix id="triage-consensus">`
- "Feedback Loops" -> `<section id="feedback-loops">`
- "Cross-Agent Consultation" -> `<section id="cross-agent-consultation">`
- "Batch Mode" -> `<operations id="batch-mode">`
- "Worktree Integration Rules" -> `<operations id="worktree-rules">`
- "Wave Execution" -> `<operations id="wave-execution">`
- "Context Hygiene" -> `<section id="context-hygiene">`

- **Files to modify:** `source/references/pipeline-operations.md`
- **Acceptance criteria:**
  - All tags properly opened and closed
  - H1 title + intro line remain outside tags
  - Triage matrix table preserved inside `<matrix>` tag
  - All numbered procedure steps preserved inside `<operations>` tags
  - Brain integration sub-sections within operations remain inside parent tag
- **Estimated complexity:** Low-Medium (197 lines)

## Comprehensive Test Specification

### Step 1 Tests: xml-prompt-schema.md Update

| ID | Category | Description |
|----|----------|-------------|
| T-0006-001 | Happy | "Rules File Tags" section exists with table containing gate, protocol, routing, model-table, section tags |
| T-0006-002 | Happy | "Reference File Tags" section exists with table containing framework, agent-dod, template, operations, matrix, section tags |
| T-0006-003 | Happy | Attribute convention section documents id attribute as kebab-case |
| T-0006-004 | Happy | Wrapping criteria (4-point list) is present |
| T-0006-005 | Boundary | Existing sections (Persona File Tags, Skill Command Tags, Invocation Prompt Tags, Brain Context Tags, Inline Content Tags, Retro Lessons Tags) are unmodified |
| T-0006-006 | Failure | No duplicate tag names between rules and reference vocabularies (except `<section>` which is shared) |
| T-0006-007 | Structural | Every opening tag in the file has a matching closing tag (open/close count per tag name is equal) |

### Step 2 Tests: default-persona.md Migration

| ID | Category | Description |
|----|----------|-------------|
| T-0006-008 | Happy | `<protocol id="boot-sequence">` wraps the Session Boot Sequence content (steps 1-6) |
| T-0006-009 | Happy | `<gate id="no-code-writing">` wraps Forbidden Actions section |
| T-0006-010 | Happy | `<gate id="cognitive-independence">` wraps Cognitive Independence section |
| T-0006-011 | Happy | `<protocol id="user-bug-flow">` wraps the user-reported bug steps (1-5) within the `<gate id="no-code-writing">` tag |
| T-0006-012 | Happy | `<section id="routing-behavior">` wraps "What This Means" section |
| T-0006-013 | Happy | `<section id="loaded-context">` wraps "Always-Loaded Context" section |
| T-0006-014 | Happy | `<section id="routing-transparency">` wraps "Routing Transparency" section |
| T-0006-015 | Happy | `<section id="non-requirements">` wraps "What This Does NOT Mean" section |
| T-0006-016 | Boundary | CONFIGURE comment block at lines 2-7 is unchanged |
| T-0006-017 | Boundary | H1 "# Default Persona: Eva" is not inside any XML tag |
| T-0006-018 | Failure | All `{pipeline_state_dir}` placeholders survive migration (count matches pre-migration) |
| T-0006-019 | Failure | No empty tags -- every opened tag has content between open and close |
| T-0006-020 | Structural | Count of opening tags matches count of closing tags for every tag name used in the file |
| T-0006-021 | Nesting | `<protocol id="user-bug-flow">` is the only tag nested inside another tag (`<gate id="no-code-writing">`). No other nesting exists in this file. |
| T-0006-022 | Regression | Pointer sections ("Mandatory Gates", "Investigation Discipline", "Brain Access") remain unwrapped plain markdown |

### Step 3 Tests: agent-system.md Migration

| ID | Category | Description |
|----|----------|-------------|
| T-0006-023 | Happy | `<routing id="auto-routing">` wraps AUTO-ROUTING RULES section including Intent Detection, Smart Context, and Confidence subsections |
| T-0006-024 | Happy | `<gate id="no-skill-tool">` wraps "Custom Commands Are NOT Skills" section |
| T-0006-025 | Happy | `<protocol id="invocation-template">` wraps Subagent Invocation section including the XML code block example |
| T-0006-026 | Happy | `<section id="eva-core">` wraps Eva -- The Central Nervous System section |
| T-0006-027 | Happy | `<section id="brain-config">` wraps "Brain Configuration" section |
| T-0006-028 | Happy | `<section id="architecture">` wraps "Architecture" section including Skills and Subagents tables |
| T-0006-029 | Happy | `<section id="pipeline-flow">` wraps "Pipeline Flow" section including Phase Sizing and Phase Transitions tables |
| T-0006-030 | Happy | `<section id="shared-behaviors">` wraps "Shared Agent Behaviors" section |
| T-0006-031 | Boundary | CONFIGURE comment block at lines 2-18 is unchanged |
| T-0006-032 | Boundary | XML code block inside `<protocol>` tag (lines 174-195) is preserved verbatim |
| T-0006-033 | Failure | All placeholder tokens (`{pipeline_state_dir}`, `{architecture_dir}`, `{product_specs_dir}`, etc.) survive migration |
| T-0006-034 | Failure | Horizontal rule (`---`) between Architecture and Brain Configuration sections is preserved |
| T-0006-035 | Structural | Count of opening tags matches count of closing tags for every tag name used in the file |
| T-0006-036 | Nesting | No tags are nested inside any other tag in this file |
| T-0006-037 | Regression | Markdown tables inside tags render correctly (no broken pipe characters) |

### Step 4 Tests: pipeline-orchestration.md Migration

| ID | Category | Description |
|----|----------|-------------|
| T-0006-038 | Happy | `<gate id="mandatory-gates">` wraps all 10 mandatory gates |
| T-0006-039 | Happy | `<protocol id="brain-capture">` wraps Brain Access section including Hybrid Capture, /devops gates, Staleness, Seed Capture, Seed Surfacing |
| T-0006-040 | Happy | `<protocol id="investigation">` wraps Investigation Discipline including Layer Escalation and Hypothesis Tracking |
| T-0006-041 | Happy | `<protocol id="invocation-dor-dod">` wraps Subagent Invocation & DoR/DoD Verification section |
| T-0006-042 | Happy | `<section id="state-files">` wraps "State File Descriptions" section |
| T-0006-043 | Happy | `<section id="phase-sizing">` wraps "Phase Sizing Rules" section including Micro, Robert Discovery, Large Research Brief |
| T-0006-044 | Happy | `<section id="pipeline-flow">` wraps "Pipeline Flow" section including Spec Requirement, Sable Gate, Stakeholder Gate, Per-Unit Commits, Review Juncture, Reconciliation, Hard Pauses |
| T-0006-045 | Happy | `<section id="mockup-uat">` wraps "Mockup + UAT Phase" section |
| T-0006-046 | Happy | `<gate id="agent-standards">` wraps "Agent Standards" section |
| T-0006-047 | Boundary | YAML frontmatter (`---paths: - "docs/pipeline/**"---`) is unchanged and above all XML tags |
| T-0006-048 | Failure | All 10 numbered gates (1-10) are present inside the gate tag -- count verification |
| T-0006-049 | Failure | All placeholder tokens survive migration |
| T-0006-050 | Failure | Gate tag is not nested inside any other tag |
| T-0006-051 | Structural | Count of opening tags matches count of closing tags for every tag name used in the file |
| T-0006-052 | Nesting | No tags are nested inside any other tag in this file |
| T-0006-053 | Regression | ASCII flow diagram (```Pipeline Flow```) preserved inside section tag |

### Step 5 Tests: pipeline-models.md Migration

| ID | Category | Description |
|----|----------|-------------|
| T-0006-054 | Happy | `<model-table id="fixed-models">` wraps Fixed-Model Agents table |
| T-0006-055 | Happy | `<model-table id="size-dependent">` wraps Size-Dependent Agents table |
| T-0006-056 | Happy | `<model-table id="agatha-model">` wraps Agatha's Model section |
| T-0006-057 | Happy | `<model-table id="complexity-classifier">` wraps Task-Level Complexity Classifier including score table and threshold rule |
| T-0006-058 | Happy | `<gate id="model-enforcement">` wraps Enforcement Rules section |
| T-0006-059 | Boundary | YAML frontmatter preserved |
| T-0006-060 | Failure | Score table values ("+0", "+1", "+2", "+3") are preserved exactly |
| T-0006-061 | Failure | Threshold rule "Score >= 3 -> Opus. Score < 3 -> Sonnet." is preserved |
| T-0006-062 | Structural | Count of opening tags matches count of closing tags for every tag name used in the file |
| T-0006-063 | Nesting | No tags are nested inside any other tag in this file |

### Step 6 Tests: dor-dod.md Migration

| ID | Category | Description |
|----|----------|-------------|
| T-0006-064 | Happy | `<framework id="dor-dod-structure">` wraps How It Works + DoR/DoD Inside `<output>` sections |
| T-0006-065 | Happy | `<agent-dod>` wraps Agent-Specific DoD Conditions block |
| T-0006-066 | Happy | `<section id="eva-responsibilities">` wraps Eva's Responsibilities section |
| T-0006-067 | Happy | `<section id="dor-rules">` wraps "DoR Rules" section |
| T-0006-068 | Happy | `<section id="per-agent-sources">` wraps "Per-Agent Sources" section |
| T-0006-069 | Happy | `<section id="dod-universal">` wraps "DoD Universal Conditions" section |
| T-0006-070 | Happy | `<section id="roz-enforcement">` wraps "Roz: DoD Enforcement" section |
| T-0006-071 | Boundary | The code block showing `<output>` tag usage (example with DoR/DoD pattern) is preserved verbatim inside `<framework>` |
| T-0006-072 | Failure | CONFIGURE comment block preserved |
| T-0006-073 | Failure | All placeholder tokens (`{lint_command}`, `{typecheck_command}`, `{test_command}`) survive |
| T-0006-074 | Structural | Count of opening tags matches count of closing tags for every tag name used in the file |
| T-0006-075 | Nesting | No tags are nested inside any other tag in this file |
| T-0006-076 | Regression | Per-Agent Sources table is fully preserved (all 11 agent rows: Sable skill, Sable subagent, Cal, Colby mockup, Colby build, Agatha, Robert subagent, Roz test-authoring, Roz, Poirot, Distillator) |

### Step 7 Tests: invocation-templates.md Migration

| ID | Category | Description |
|----|----------|-------------|
| T-0006-077 | Happy | 16 `<template>` tags present, each with a unique id attribute |
| T-0006-078 | Happy | `<template id="cal-adr">` wraps Cal (ADR Production) block including inner `<task>`, `<constraints>`, `<output>` tags |
| T-0006-079 | Happy | `<template id="poirot-blind">` wraps Poirot block -- verified inner `<constraints>` preserved |
| T-0006-080 | Boundary | Inner XML tags (`<task>`, `<brain-context>`, `<thought>`, `<constraints>`, `<output>`, `<read>`, `<warn>`, `<context>`, `<hypotheses>`) are all preserved as content, not parsed as structural tags |
| T-0006-081 | Failure | CONFIGURE comment block preserved |
| T-0006-082 | Failure | All placeholder tokens (`{product_specs_dir}`, `{ux_docs_dir}`, etc.) survive |
| T-0006-083 | Failure | No template tag is nested inside another template tag |
| T-0006-084 | Structural | Count of `<template` opening tags equals count of `</template>` closing tags (exactly 16 each) |
| T-0006-085 | Regression | `<thought>` elements with type/agent/phase/relevance attributes inside brain-context examples are unchanged |

### Step 8 Tests: pipeline-operations.md Migration

| ID | Category | Description |
|----|----------|-------------|
| T-0006-086 | Happy | `<matrix id="triage-consensus">` wraps the Triage Consensus Matrix table and its brain capture gate and escalation rule |
| T-0006-087 | Happy | `<operations id="continuous-qa">` wraps Continuous QA section (all 12 numbered steps) |
| T-0006-088 | Happy | `<operations id="wave-execution">` wraps Wave Execution section including algorithm and constraints |
| T-0006-089 | Happy | `<section id="invocation-format">` wraps "Invocation Format" section |
| T-0006-090 | Happy | `<protocol id="brain-prefetch">` wraps "Brain Context Prefetch" section |
| T-0006-091 | Happy | `<section id="feedback-loops">` wraps "Feedback Loops" section including the 11-row routing table |
| T-0006-092 | Happy | `<section id="cross-agent-consultation">` wraps "Cross-Agent Consultation" section |
| T-0006-093 | Happy | `<operations id="batch-mode">` wraps "Batch Mode" section including all 4 numbered rules |
| T-0006-094 | Happy | `<operations id="worktree-rules">` wraps "Worktree Integration Rules" section including all 4 numbered rules |
| T-0006-095 | Happy | `<section id="context-hygiene">` wraps "Context Hygiene" section including Compaction Strategy and What Eva Carries table |
| T-0006-096 | Boundary | H1 title + intro line remain unwrapped |
| T-0006-097 | Failure | Triage matrix table (10 data rows: 2 HALT, 1 HIGH-CONFIDENCE, 1 CONTEXT-ANCHORING MISS, 1 STANDARD, 2 HARD PAUSE for Robert, 1 HARD PAUSE for Sable, 1 CONVERGENT DRIFT, 1 ADVANCE) preserved inside matrix tag |
| T-0006-098 | Failure | All 12 numbered continuous QA steps preserved |
| T-0006-099 | Failure | Feedback Loops table (11 rows) preserved |
| T-0006-100 | Structural | Count of opening tags matches count of closing tags for every tag name used in the file |
| T-0006-101 | Nesting | No tags are nested inside any other tag in this file |
| T-0006-102 | Regression | Context Hygiene contains Compaction Strategy bullet list (4 items) and "What Eva Carries vs. What Subagents Carry" table (1 table, 7 data rows) -- both preserved inside section tag |

### Cross-Step Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0006-103 | Consistency | Every structural XML tag used in Steps 2-8 (gate, protocol, routing, model-table, section, framework, agent-dod, template, operations, matrix) is defined in the schema updated in Step 1. No tag appears in a migrated file without a corresponding schema entry. |
| T-0006-104 | Consistency | Every id attribute value used in Steps 2-8 is kebab-case and unique within its file, matching the convention documented in Step 1 |
| T-0006-105 | Consistency | The `<section>` tag is the only tag name shared between rules files (Steps 2-5) and reference files (Steps 6-8). No other tag name crosses the boundary. |
| T-0006-106 | Nesting | Across all 7 migrated files (Steps 2-8), `<protocol id="user-bug-flow">` inside `<gate id="no-code-writing">` in default-persona.md is the ONLY case of tag nesting. Every other file has zero nesting. |
| T-0006-107 | Sed-survival | For each source/ file modified in Steps 2-8: run `sed 's/{placeholder}/value/g'` with representative placeholder values. Verify that (a) all XML tags survive intact with correct open/close structure, (b) content within tags is unchanged except for substituted placeholders, (c) tag attributes are not corrupted by sed. Test with placeholders containing slashes and special characters. |
| T-0006-108 | Structural | For each migrated file: count of lines containing `<tagname` (opening) equals count of lines containing `</tagname>` (closing) for every tag name. Mismatched counts indicate unclosed or extra tags. |

### Contract Boundaries

| Producer | Consumer | Expected Shape |
|----------|----------|---------------|
| xml-prompt-schema.md (Step 1) | All other steps | Tag names and attributes defined in schema are the exact tags used in migration |
| source/rules/*.md (Steps 2-5) | /pipeline-setup skill | Copies to .claude/rules/*.md with placeholder substitution; XML tags must survive sed replacement (verified by T-0006-107) |
| source/references/*.md (Steps 6-8) | /pipeline-setup skill | Copies to .claude/references/*.md with placeholder substitution; XML tags must survive sed replacement (verified by T-0006-107) |
| source/rules/agent-system.md | Claude Code rules loader | Always-loaded; XML tags must not break Claude Code's markdown rendering |
| source/rules/pipeline-orchestration.md | Claude Code path-scoped loader | YAML frontmatter must remain first content for path-scoping to work |

## Notes for Colby

1. **Tag placement pattern:** Open tag goes on its own line before the `##` header. Close tag goes on its own line after the last content line of that section, with a blank line before it for readability. Example:
   ```
   <gate id="no-code-writing">

   ## Forbidden Actions -- Eva NEVER Writes Code

   [content...]

   </gate>
   ```

2. **Nested content that looks like XML:** invocation-templates.md contains `<task>`, `<constraints>`, etc. as *content* (example templates). These are not structural tags for this file -- they are the content being documented. Wrap the outer `<template>` tag around the whole block; do not modify the inner example XML.

3. **The `<protocol id="user-bug-flow">` inside `<gate id="no-code-writing">`:** This is the one case of intentional nesting in default-persona.md. The user-bug-flow is a procedure nested within the forbidden-actions gate because the procedure defines how Eva handles bugs without violating the gate. Keep the nesting shallow -- this is the only place it occurs.

4. **pipeline-orchestration.md YAML frontmatter:** The `---paths:---` block MUST remain the very first content. Place all XML tags below it. The path-scoped loading mechanism depends on the frontmatter being at byte offset 0.

5. **Placeholder preservation:** Run `grep -c '{' source/rules/FILE.md` before and after migration for each file. The count must match. Same for `}`.

6. **Do not reorder content.** The existing section order within each file is intentional. Tags wrap existing structure; they do not reorganize it.

7. **Horizontal rules (`---`):** In agent-system.md, there are two `---` lines (line 30 and line 205). These can be removed IF the XML tag boundary makes them redundant. If kept, they must be inside the tag, not between tag boundary and content.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | XML tag vocabulary for rules files | Done | Decision section: 5 tags defined (gate, protocol, routing, model-table, section) |
| 2 | XML tag vocabulary for reference files | Done | Decision section: 6 tags defined (framework, agent-dod, template, operations, matrix, section) |
| 3 | Update xml-prompt-schema.md | Done | Step 1 with acceptance criteria |
| 4 | Semantic, purposeful tags | Done | Wrapping criteria (4-point list) + "What Does NOT Get Wrapped" section |
| 5 | Maintain existing markdown within tags | Done | Acceptance criteria on every step require content preservation |
| 6 | Colby edits source/ only | Done | All steps target source/ files; .claude/ copies excluded |
| 7 | One step per file | Done | 8 steps: 1 schema + 4 rules + 3 references |
| 8 | Test specs per step | Done | 108 tests across 8 steps + cross-step (T-0006-001 through T-0006-108) |
| 9 | Schema update is Step 1 | Done | Step 1 is xml-prompt-schema.md |
| 10 | Format change only | Done | Constraints on every step: "preserve content verbatim" |
| 11 | retro-lessons.md excluded | Done | Not included in any step; noted in Context section |
| 12 | Pipeline sizing: Small | Done | 8 files, no behavioral change, structural wrapping only |

**Architectural decisions not in the spec:**
- Chose semantic tag names (gate, protocol, routing) over generic `<section>` for all sections. Rationale: semantic names carry meaning that helps the model distinguish content types.
- Defined wrapping criteria (4-point test) to prevent over-wrapping. Without this, Colby would have to guess which sections to wrap.
- Allowed one case of intentional nesting (user-bug-flow inside no-code-writing gate in default-persona.md). All other tags are top-level only.
- Included `id` attributes on tags for grep-based lookup. This is forward-looking but low-cost.

**Rejected alternatives with reasoning:**
- Reusing persona tags: would confuse model when rules and persona files are loaded together.
- Single `<section>` tag: loses semantic value that is the primary benefit of this migration.
- No migration: creates inconsistency that Anthropic guidance warns against.

**Technical constraints discovered:**
- YAML frontmatter on pipeline-orchestration.md and pipeline-models.md must remain at byte offset 0 for Claude Code path-scoped loading.
- invocation-templates.md contains inner XML tags as content -- wrapping must not corrupt them.
- /pipeline-setup copies source/ to .claude/ with sed placeholder substitution -- XML tags must not interfere with sed patterns (verified: tags use `<>` while placeholders use `{}`).

**Grep check:** TODO/FIXME/HACK/XXX in output -> 0
**Template:** All sections filled -- no TBD, no placeholders
