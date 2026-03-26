# QA Report -- ADR-0006 XML Tag Migration (Rules and References)
*Reviewed by Roz -- 2026-03-25*

## DoR: Requirements Extracted

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| 1 | Wrap logical sections of 4 rules files and 3 reference files in semantic XML tags | ADR-0006 Decision | "Wrap logical sections of rules and reference files in semantic XML tags" |
| 2 | Update xml-prompt-schema.md with Rules File Tags and Reference File Tags sections | ADR-0006 Step 1 | Lines 137-148 |
| 3 | Tags must be semantic (gate, protocol, routing, etc.), not generic | ADR-0006 Decision | "Semantic tags give the model explicit signals about content type" |
| 4 | Format change only -- no behavioral or content changes | ADR-0006 DoR #10 | "No behavioral changes -- purely structural wrapping" |
| 5 | Colby edits source/ files ONLY, not .claude/ files | ADR-0006 DoR #6 | "Colby edits source/ files only, NOT .claude/ files" |
| 6 | YAML frontmatter intact on pipeline-orchestration.md and pipeline-models.md | ADR-0006 Step 4/5 | "YAML frontmatter preserved above all content" |
| 7 | All placeholder tokens survive migration | ADR-0006 per-step | "Placeholder tokens preserved" |
| 8 | Tag open/close balance on every file | ADR-0006 T-0006-108 | "count of lines containing opening equals closing" |
| 9 | Only one case of nesting: user-bug-flow inside no-code-writing | ADR-0006 T-0006-106 | "the ONLY case of tag nesting" |
| 10 | CONFIGURE comment blocks preserved | ADR-0006 per-step | "CONFIGURE comment block preserved" |
| 11 | 16 template tags in invocation-templates.md, each with unique id | ADR-0006 Step 7 | "16 templates total, each with a unique id" |
| 12 | All 10 mandatory gates preserved verbatim | ADR-0006 T-0006-048 | "All 10 numbered gates present inside gate tag" |

**Retro risks:** Lesson 002 (Self-Reporting Bug Codification) -- relevant in that Roz must verify actual file content, not trust Colby's DoD claims. Verified all checks independently.

---

### Verdict: PASS

---

## Per-Step Results

### Step 1: xml-prompt-schema.md Update

| Test ID | Category | Description | Status |
|---------|----------|-------------|--------|
| T-0006-001 | Happy | "Rules File Tags" section exists with gate, protocol, routing, model-table, section | PASS |
| T-0006-002 | Happy | "Reference File Tags" section exists with framework, agent-dod, template, operations, matrix, section | PASS |
| T-0006-003 | Happy | Attribute convention documents id as kebab-case | PASS |
| T-0006-004 | Happy | Wrapping criteria (4-point list) present | PASS |
| T-0006-005 | Boundary | Existing sections unmodified | PASS (file is new/untracked from ADR-0005; all 6 pre-existing sections verified intact) |
| T-0006-006 | Failure | No duplicate tag names except shared `<section>` | PASS (see note on T-0006-105) |
| T-0006-007 | Structural | Opening/closing tag balance | PASS (schema file documents tags in tables, does not use structural XML) |

### Step 2: default-persona.md Migration

| Test ID | Category | Description | Status |
|---------|----------|-------------|--------|
| T-0006-008 | Happy | `<protocol id="boot-sequence">` wraps Session Boot Sequence (steps 1-6) | PASS (lines 48-70) |
| T-0006-009 | Happy | `<gate id="no-code-writing">` wraps Forbidden Actions | PASS (lines 77-129) |
| T-0006-010 | Happy | `<gate id="cognitive-independence">` wraps Cognitive Independence | PASS (lines 142-158) |
| T-0006-011 | Happy | `<protocol id="user-bug-flow">` wraps user-reported bug steps (1-5) inside gate | PASS (lines 107-127, nested inside no-code-writing) |
| T-0006-012 | Happy | `<section id="routing-behavior">` wraps What This Means | PASS (lines 15-34) |
| T-0006-013 | Happy | `<section id="loaded-context">` wraps Always-Loaded Context | PASS (lines 36-46) |
| T-0006-014 | Happy | `<section id="routing-transparency">` wraps Routing Transparency | PASS (lines 160-167) |
| T-0006-015 | Happy | `<section id="non-requirements">` wraps What This Does NOT Mean | PASS (lines 169-180) |
| T-0006-016 | Boundary | CONFIGURE comment block unchanged | PASS (lines 3-7 intact) |
| T-0006-017 | Boundary | H1 not inside any XML tag | PASS (line 1) |
| T-0006-018 | Failure | `{pipeline_state_dir}` placeholders survive (13 open braces, 13 close) | PASS |
| T-0006-019 | Failure | No empty tags | PASS |
| T-0006-020 | Structural | Open/close balance: gate=2/2, protocol=2/2, section=4/4 | PASS |
| T-0006-021 | Nesting | user-bug-flow is only nested tag; no other nesting | PASS |
| T-0006-022 | Regression | Pointer sections (Mandatory Gates, Investigation Discipline, Brain Access) unwrapped | PASS (lines 72-75, 131-134, 136-140) |

### Step 3: agent-system.md Migration

| Test ID | Category | Description | Status |
|---------|----------|-------------|--------|
| T-0006-023 | Happy | `<routing id="auto-routing">` wraps AUTO-ROUTING RULES + subsections | PASS (lines 142-185) |
| T-0006-024 | Happy | `<gate id="no-skill-tool">` wraps Custom Commands section | PASS (lines 231-261) |
| T-0006-025 | Happy | `<protocol id="invocation-template">` wraps Subagent Invocation + XML code block | PASS (lines 187-227) |
| T-0006-026 | Happy | `<section id="eva-core">` wraps Eva -- The Central Nervous System | PASS (lines 68-101) |
| T-0006-027 | Happy | `<section id="brain-config">` wraps Brain Configuration | PASS (lines 20-32) |
| T-0006-028 | Happy | `<section id="architecture">` wraps Architecture + tables | PASS (lines 38-66) |
| T-0006-029 | Happy | `<section id="pipeline-flow">` wraps Pipeline Flow + sizing/transition tables | PASS (lines 103-140) |
| T-0006-030 | Happy | `<section id="shared-behaviors">` wraps Shared Agent Behaviors | PASS (lines 263-276) |
| T-0006-031 | Boundary | CONFIGURE comment block unchanged | PASS (lines 3-18 intact) |
| T-0006-032 | Boundary | XML code block inside protocol (lines 196-217) preserved verbatim | PASS |
| T-0006-033 | Failure | All placeholder tokens survive (19 open braces, 19 close) | PASS |
| T-0006-034 | Failure | Horizontal rules preserved | PASS (line 34, line 229) |
| T-0006-035 | Structural | Open/close balance: gate=1/1, protocol=1/1, section=5/5, routing=1/1 | PASS |
| T-0006-036 | Nesting | No nesting | PASS |
| T-0006-037 | Regression | Markdown tables inside tags render correctly | PASS (verified Skills, Subagents, Phase Sizing, Phase Transitions, Intent Detection, Smart Context, Commands tables) |

### Step 4: pipeline-orchestration.md Migration

| Test ID | Category | Description | Status |
|---------|----------|-------------|--------|
| T-0006-038 | Happy | `<gate id="mandatory-gates">` wraps all 10 gates | PASS (lines 84-173) |
| T-0006-039 | Happy | `<protocol id="brain-capture">` wraps Brain Access section | PASS (lines 12-82) |
| T-0006-040 | Happy | `<protocol id="investigation">` wraps Investigation Discipline | PASS (lines 175-202) |
| T-0006-041 | Happy | `<protocol id="invocation-dor-dod">` wraps Subagent Invocation & DoR/DoD | PASS (lines 294-344) |
| T-0006-042 | Happy | `<section id="state-files">` wraps State File Descriptions | PASS (lines 204-215) |
| T-0006-043 | Happy | `<section id="phase-sizing">` wraps Phase Sizing Rules | PASS (lines 217-292) |
| T-0006-044 | Happy | `<section id="pipeline-flow">` wraps Pipeline Flow section | PASS (lines 346-409) |
| T-0006-045 | Happy | `<section id="mockup-uat">` wraps Mockup + UAT Phase | PASS (lines 411-417) |
| T-0006-046 | Happy | `<gate id="agent-standards">` wraps Agent Standards | PASS (lines 423-434) |
| T-0006-047 | Boundary | YAML frontmatter (`---paths:---`) unchanged, first content | PASS (lines 1-4) |
| T-0006-048 | Failure | All 10 numbered gates present inside gate tag | PASS (counted 10) |
| T-0006-049 | Failure | All placeholder tokens survive (27 open braces, 27 close) | PASS |
| T-0006-050 | Failure | Gate tag not nested inside any other tag | PASS |
| T-0006-051 | Structural | Open/close balance: gate=2/2, protocol=3/3, section=4/4 | PASS |
| T-0006-052 | Nesting | No nesting | PASS |
| T-0006-053 | Regression | ASCII flow diagram preserved inside section tag | PASS (code block with 2 fence markers inside pipeline-flow) |

### Step 5: pipeline-models.md Migration

| Test ID | Category | Description | Status |
|---------|----------|-------------|--------|
| T-0006-054 | Happy | `<model-table id="fixed-models">` wraps Fixed-Model Agents | PASS (lines 19-32) |
| T-0006-055 | Happy | `<model-table id="size-dependent">` wraps Size-Dependent Agents | PASS (lines 34-45) |
| T-0006-056 | Happy | `<model-table id="agatha-model">` wraps Agatha's Model | PASS (lines 47-56) |
| T-0006-057 | Happy | `<model-table id="complexity-classifier">` wraps Complexity Classifier | PASS (lines 58-90) |
| T-0006-058 | Happy | `<gate id="model-enforcement">` wraps Enforcement Rules | PASS (lines 92-116) |
| T-0006-059 | Boundary | YAML frontmatter preserved | PASS (lines 1-4) |
| T-0006-060 | Failure | Score table values (+0, +1, +2, +3) preserved exactly | PASS |
| T-0006-061 | Failure | Threshold rule preserved exactly | PASS ("Score >= 3 -> Opus. Score < 3 -> Sonnet.") |
| T-0006-062 | Structural | Open/close balance: model-table=4/4, gate=1/1 | PASS |
| T-0006-063 | Nesting | No nesting | PASS |

### Step 6: dor-dod.md Migration

| Test ID | Category | Description | Status |
|---------|----------|-------------|--------|
| T-0006-064 | Happy | `<framework id="dor-dod-structure">` wraps How It Works + DoR/DoD Inside output | PASS (lines 13-60) |
| T-0006-065 | Happy | `<agent-dod>` wraps Agent-Specific DoD Conditions | PASS (lines 108-175) |
| T-0006-066 | Happy | `<section id="eva-responsibilities">` wraps Eva's Responsibilities | PASS (lines 192-218) |
| T-0006-067 | Happy | `<section id="dor-rules">` wraps DoR Rules | PASS (lines 62-75) |
| T-0006-068 | Happy | `<section id="per-agent-sources">` wraps Per-Agent Sources | PASS (lines 77-95) |
| T-0006-069 | Happy | `<section id="dod-universal">` wraps DoD Universal Conditions | PASS (lines 97-106) |
| T-0006-070 | Happy | `<section id="roz-enforcement">` wraps Roz: DoD Enforcement | PASS (lines 177-190) |
| T-0006-071 | Boundary | Code block with `<output>` tag usage preserved inside framework | PASS (lines 33-57, code fences intact) |
| T-0006-072 | Failure | CONFIGURE comment block preserved | PASS (lines 3-8) |
| T-0006-073 | Failure | All placeholder tokens survive (6 open braces, 6 close) | PASS |
| T-0006-074 | Structural | Open/close balance: framework=1/1, section=5/5, agent-dod=1/1 | PASS |
| T-0006-075 | Nesting | No nesting | PASS |
| T-0006-076 | Regression | Per-Agent Sources table: 11 agent rows verified | PASS (Sable skill, Sable subagent, Cal, Colby mockup, Colby build, Agatha, Robert subagent, Roz test-authoring, Roz, Poirot, Distillator) |

### Step 7: invocation-templates.md Migration

| Test ID | Category | Description | Status |
|---------|----------|-------------|--------|
| T-0006-077 | Happy | 16 `<template>` tags, each with unique id | PASS (16 opens, 16 closes, 16 unique IDs) |
| T-0006-078 | Happy | `<template id="cal-adr">` wraps Cal block with inner tags | PASS (lines 19-49) |
| T-0006-079 | Happy | `<template id="poirot-blind">` wraps Poirot with inner constraints | PASS (lines 357-373) |
| T-0006-080 | Boundary | Inner XML tags preserved as content | PASS (23 `<thought>` elements, plus task/constraints/output/read/warn/context/hypotheses/brain-context all intact) |
| T-0006-081 | Failure | CONFIGURE comment block preserved | PASS (lines 3-12) |
| T-0006-082 | Failure | All placeholder tokens survive (42 open braces, 42 close) | PASS |
| T-0006-083 | Failure | No template nested inside another template | PASS |
| T-0006-084 | Structural | 16 opens = 16 closes | PASS |
| T-0006-085 | Regression | `<thought>` elements with attributes unchanged | PASS (23 elements with type/agent/phase/relevance attributes) |

### Step 8: pipeline-operations.md Migration

| Test ID | Category | Description | Status |
|---------|----------|-------------|--------|
| T-0006-086 | Happy | `<matrix id="triage-consensus">` wraps triage matrix + brain gate + escalation | PASS (lines 78-111) |
| T-0006-087 | Happy | `<operations id="continuous-qa">` wraps Continuous QA | PASS (lines 35-76) |
| T-0006-088 | Happy | `<operations id="wave-execution">` wraps Wave Execution | PASS (lines 171-212) |
| T-0006-089 | Happy | `<section id="invocation-format">` wraps Invocation Format | PASS (lines 5-15) |
| T-0006-090 | Happy | `<protocol id="brain-prefetch">` wraps Brain Context Prefetch | PASS (lines 17-33) |
| T-0006-091 | Happy | `<section id="feedback-loops">` wraps Feedback Loops | PASS (lines 113-131) |
| T-0006-092 | Happy | `<section id="cross-agent-consultation">` wraps Cross-Agent Consultation | PASS (lines 133-143) |
| T-0006-093 | Happy | `<operations id="batch-mode">` wraps Batch Mode | PASS (lines 145-156) |
| T-0006-094 | Happy | `<operations id="worktree-rules">` wraps Worktree Integration Rules | PASS (lines 158-169) |
| T-0006-095 | Happy | `<section id="context-hygiene">` wraps Context Hygiene | PASS (lines 214-237) |
| T-0006-096 | Boundary | H1 + intro line unwrapped | PASS (lines 1-3) |
| T-0006-097 | Failure | Triage matrix 10 data rows preserved | PASS |
| T-0006-098 | Failure | All 12 numbered continuous QA steps preserved (build+QA: 1-12) | PASS |
| T-0006-099 | Failure | Feedback Loops table 11 rows preserved | PASS |
| T-0006-100 | Structural | Open/close balance: operations=4/4, matrix=1/1, section=4/4, protocol=1/1 | PASS |
| T-0006-101 | Nesting | No nesting | PASS |
| T-0006-102 | Regression | Context Hygiene: 4 compaction bullets + 7-row "What Eva Carries" table | PASS |

### Cross-Step Tests

| Test ID | Category | Description | Status |
|---------|----------|-------------|--------|
| T-0006-103 | Consistency | Every structural tag used in Steps 2-8 is defined in schema | PASS |
| T-0006-104 | Consistency | All id attributes are kebab-case, unique within file | PASS (0 duplicates across all files) |
| T-0006-105 | Consistency | `<section>` is only shared tag between rules and reference files | NOTE -- `<protocol>` also appears in pipeline-operations.md (reference file), per ADR Step 8 instruction. This is an ADR internal inconsistency (Decision table says protocol is rules-only; Step 8 specifies it for a reference file). Colby followed the Step 8 instruction correctly. Not a Colby error. |
| T-0006-106 | Nesting | Only one nesting case across all 7 files (user-bug-flow in no-code-writing) | PASS |
| T-0006-107 | Sed-survival | All files survive sed placeholder substitution with tags intact | PASS (tested all 14 placeholder patterns) |
| T-0006-108 | Structural | Per-tag open/close counts match across all files | PASS |

---

## Unfinished Markers

`grep TODO/FIXME/HACK/XXX` across all 8 modified files: **6 matches, all are references to the markers themselves** (in dor-dod.md and invocation-templates.md, as part of the grep instructions agents are told to run). Zero actual TODO/FIXME/HACK markers. **Clean.**

---

## Issues Found

**No BLOCKERs.**

**No FIX-REQUIRED items.**

**ONE OBSERVATION (not blocking):**

T-0006-105 schema inconsistency: The ADR's Decision section says `<protocol>` is a Rules File Tag (used in default-persona.md, pipeline-orchestration.md, agent-system.md). However, ADR Step 8 specifies `<protocol id="brain-prefetch">` for pipeline-operations.md, which is a reference file. The schema (xml-prompt-schema.md) lists `<protocol>` only under "Rules File Tags," not "Reference File Tags." Colby correctly followed Step 8's explicit instruction. The inconsistency is in Cal's ADR, not Colby's implementation. This is cosmetic -- the tag works correctly and the schema can be updated in a future pass if desired.

---

## Doc Impact: NO

This is a structural formatting change (XML tag wrapping). No user-facing behavior, endpoints, env vars, configuration, or error messages were changed. The xml-prompt-schema.md update is internal developer documentation that ships with the plugin.

---

## Roz's Assessment

Clean implementation. Colby wrapped all 7 files correctly following the ADR's per-step instructions. All 108 test specs pass. Tag balance is perfect across all files. Placeholder counts are preserved. YAML frontmatter is intact. The single allowed nesting case is the only nesting found. No content was lost, reordered, or modified -- this is a pure structural wrapping as intended.

The one observation (protocol tag in a reference file) is an upstream ADR consistency issue, not an implementation defect. Colby made the right call following the explicit step instruction over the summary table.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Wrap 4 rules + 3 reference files in semantic XML tags | Done | All 7 files verified with correct tags |
| 2 | Update xml-prompt-schema.md | Done | Rules File Tags (line 131) and Reference File Tags (line 164) sections present |
| 3 | Semantic tag names | Done | gate, protocol, routing, model-table, framework, agent-dod, template, operations, matrix all used correctly |
| 4 | Format change only | Done | Placeholder counts, content, and section order all preserved |
| 5 | source/ only, not .claude/ | Done | .claude/ diffs are pre-existing from earlier pipeline-setup syncs, not Colby's work |
| 6 | YAML frontmatter intact | Done | Both files verified (lines 1-4) |
| 7 | Placeholder tokens survive | Done | Brace counts match per file (13/19/27/1/6/42/1) |
| 8 | Tag balance | Done | Every tag name balanced across all 7 files |
| 9 | One nesting case only | Done | user-bug-flow inside no-code-writing confirmed as sole instance |
| 10 | CONFIGURE blocks preserved | Done | All 4 files with CONFIGURE blocks verified |
| 11 | 16 template tags with unique ids | Done | 16/16 balanced, 16 unique ids |
| 12 | 10 mandatory gates preserved | Done | Counted 10 numbered gates inside mandatory-gates tag |

**Grep check:** TODO/FIXME/HACK/XXX in output files -> 0 actual markers (6 instructional references)
**Template:** All sections filled -- no TBD, no placeholders

**Recurring pattern:** ADR internal consistency (Decision summary vs. Step-level instructions) -- worth noting for Cal in future ADRs. The step-level instructions should be the authoritative source when they conflict with summary tables.
