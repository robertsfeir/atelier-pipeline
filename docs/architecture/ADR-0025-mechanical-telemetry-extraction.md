# ADR-0025: Mechanical Telemetry Extraction

## DoR: Requirements Extracted

**Sources:** ADR-0024 (mechanical brain writes precedent), `source/shared/agents/brain-extractor.md`
(current extractor), `source/claude/agents/brain-extractor.frontmatter.yml`, `brain/scripts/hydrate-telemetry.mjs`
(current hydrator), `source/shared/rules/pipeline-orchestration.md` (Hybrid Capture Model section),
`source/claude/hooks/warn-dor-dod.sh`, `docs/pipeline/pipeline-state.md` (Eva write format reference),
`docs/pipeline/context-brief.md` (Eva write format reference), `.claude/settings.json` (hook wiring),
`source/shared/commands/telemetry-hydrate.md` (aspirational SessionStart doc).

| # | Requirement | Source |
|---|-------------|--------|
| R1 | brain-extractor extracts structured quality signals per agent_type (roz, colby, cal, agatha) from last_assistant_message | Context decision 1 |
| R2 | Roz signals: PASS/FAIL verdict, tests_before, tests_after, tests_broken, finding counts by severity (BLOCKER/MUST-FIX/NIT/SUGGESTION) | Context decision 1 |
| R3 | Colby signals: rework flag (is this agent invocation fixing a prior Roz FAIL?), files changed count, DoD completeness | Context decision 1 |
| R4 | Cal signals: step count, test spec count, ADR revision number, DoR/DoD sections present | Context decision 1 |
| R5 | Agatha signals: docs written count, divergence findings count, drift vs gap breakdown | Context decision 1 |
| R6 | Structured signals captured as thought_type: 'insight', source_phase: 'quality', metadata.quality_signals present | Context decision 1 |
| R7 | hydrate-telemetry.mjs parses pipeline-state.md from the project docs/pipeline directory and emits brain captures for Eva's decisions and phase transitions | Context decision 2 |
| R8 | hydrate-telemetry.mjs parses context-brief.md and emits brain captures for user preferences and key constraints | Context decision 2 |
| R9 | Hydrator SessionStart wiring: a SessionStart shell hook (`session-hydrate.sh`) invokes hydrate-telemetry.mjs --silent after each session boot | Context decision 2 |
| R10 | Eva's behavioral brain capture protocol (Hybrid Capture Model "Writes" section) deleted from pipeline-orchestration.md | Context decision 3 |
| R11 | warn-dor-dod.sh deleted from source/claude/hooks/ and removed from settings.json SubagentStop block and SKILL.md references | Context decision 4 |
| R12 | After this ADR, no persona file, no rule file, no reference file instructs any agent to call agent_capture directly | Context decision 5 |
| R13 | Existing T1/T3 hydration for cost/tokens untouched | Constraint |
| R14 | No new hooks added — reuse existing SubagentStop + SessionStart wiring patterns | Constraint |
| R15 | SKILL.md updated: remove warn-dor-dod.sh from hook install list and settings.json template | R11 |

**Retro risks:**

- **Lesson #003 (Stop Hook Race Condition):** Session hydrate hook must be exit-0 always. No blocking. No retry loops.
- **Lesson #002 (Self-Reporting Bug Codification):** Structured signal extraction must parse agent output faithfully. The extractor must not invent signals from ambiguous text -- zero extraction is always acceptable.

**Spec challenge:** The context assumes `last_assistant_message` from Roz, Colby, Cal, and Agatha contains parseable structured output (e.g., "PASS", "BLOCKER: 2", "tests_before: 14"). If agents produce free-form prose without these markers, the extractor cannot parse structured signals. If wrong, the quality signal extraction fails silently (zero structured captures) while unstructured knowledge extraction (ADR-0024 decisions/patterns/lessons) continues unaffected. Graceful degradation: structured fields absent from metadata, unstructured extraction proceeds normally.

**SPOF:** The `insertTelemetryThought` function in hydrate-telemetry.mjs (and the new state-file parsing it will invoke). Failure mode: DB write errors during SessionStart hydration block no pipeline work (non-blocking), but emit confusing errors to the user. Graceful degradation: all hydration functions catch errors, log to stderr, and exit 0.

**Anti-goals:**

1. Anti-goal: Real-time structured telemetry capture (Roz signals captured to brain during the pipeline run as it happens). Reason: The brain-extractor fires post-completion via SubagentStop -- it reads the completed output, not a live stream. Intra-pipeline structured signals are not available in real time. Revisit: If Claude Code exposes streaming SubagentStop events with partial output.

2. Anti-goal: Replacing the Tier 2 wave-level telemetry with structured per-agent signals. Reason: Tier 2 captures wave-level aggregates (rework_cycles, finding_convergence, evoscore_delta) that require cross-unit state. The structured signals in R1-R5 are per-invocation signals from a single agent output. These are additive metadata, not replacements. Revisit: If a downstream consumer wants to roll up per-invocation structured signals into wave-level aggregates.

3. Anti-goal: Structured signal extraction from Ellis, Poirot, Robert, Sable, or Sentinel. Reason: These agents were explicitly excluded from brain-extractor scope in ADR-0024 (Anti-goal #2). Adding structured extraction to agents with no established capture history adds Haiku invocation cost without proven retrieval value. Revisit: If brain retrieval shows gaps attributable to missing structured signals from these agents.

---

## Status

Proposed

**Supersedes:** Behavioral brain capture protocol in `source/shared/rules/pipeline-orchestration.md` (the "Writes (cross-cutting only, best-effort)" subsection of the Hybrid Capture Model). The hydrator takes over Eva's state-derived captures; the structured brain-extractor extension takes over quality signal capture. After this ADR, no Writes subsection exists.

## Context

ADR-0024 replaced behavioral brain capture compliance for Cal, Colby, Roz, and Agatha with a mechanical SubagentStop Haiku extractor. That ADR explicitly excluded three remaining behavioral capture responsibilities from scope (R13: "Eva cross-cutting captures preserved unchanged"):

1. **Eva's direct agent_capture calls** -- user decisions, phase transitions, wave decisions, model-vs-outcome, cross-agent patterns, pipeline end summaries. These are behavioral: Eva is supposed to call `agent_capture` at the right moment. She frequently does not.

2. **Quality signal captures** -- the brain-extractor currently extracts free-form decisions/patterns/lessons. It does not extract the structured quality signals already present in agent output (Roz verdicts, finding counts, Colby file counts, Cal test spec counts). These signals exist in every agent output but are lost because the extractor has no schema for them.

3. **warn-dor-dod.sh** -- a SubagentStop pre-hoc behavioral warning that fires for Colby and Roz, checking output for ## DoR and ## DoD section headers. ADR-0024 deleted the analogous `warn-brain-capture.sh` because the brain-extractor mechanically validates brain capture post-completion. The same logic applies here: if brain-extractor now validates DoD completeness as a structured quality signal (R3: DoD completeness in Colby signals), the pre-hoc behavioral warning is a redundant behavioral layer that follows the exact pattern of the deleted hook.

### Why Eva's Behavioral Captures Are Unreliable

Eva operates on a main thread with a large, busy context window. She manages phase transitions, processes agent outputs, routes fixes, and answers user questions. Calling `agent_capture` requires Eva to: (a) recognize the moment, (b) construct the capture content, (c) invoke the MCP tool, and (d) handle errors. At any of these steps, context pressure, compaction, or routing tasks cause the call to be skipped. The "best-effort -- reinforced by prompt hook" qualifier in the pipeline-orchestration.md Hybrid Capture Model section is accurate: it is best-effort, and the effort frequently fails.

### What Eva Does Reliably: Write State Files

Eva writes `pipeline-state.md` and `context-brief.md` reliably because these files drive pipeline recovery. Losing them means losing pipeline state -- a direct operational cost Eva can observe. Writing to the brain has no observable operational cost when it fails, so Eva treats it as optional.

The hydrator already parses JSONL files for cost/token data (T1/T3). Extending it to also parse the state files Eva already writes -- extracting user decisions from context-brief.md and phase transitions from pipeline-state.md -- converts Eva's reliable file writes into brain captures without requiring any behavioral change from Eva.

### SessionStart Wiring Gap

`source/shared/commands/telemetry-hydrate.md` documents: "The SessionStart hook runs this automatically with --silent on each new session." This is aspirational -- no SessionStart hook entry exists in `settings.json` and no `session-hydrate.sh` script exists in `source/claude/hooks/`. This ADR closes that gap as part of Wave 2.

## Decision

**Wave 1:** Extend brain-extractor to emit structured quality signals per agent type. The extractor already fires post-completion for cal/colby/roz/agatha. Add a second capture per invocation (when brain available): a `thought_type: 'insight'` capture with `metadata.quality_signals` containing the structured fields from R1-R5. Parse these fields from natural markers already present in agent output (e.g., Roz always writes "PASS" or "FAIL", Colby's DoD table has a Files Changed row). If a marker is absent, omit that field -- no fabrication.

**Wave 2:** Extend hydrate-telemetry.mjs to parse `docs/pipeline/pipeline-state.md` and `docs/pipeline/context-brief.md` from the project working directory, emitting `source_agent: 'eva'` brain captures for user decisions (from context-brief.md) and phase transitions (from pipeline-state.md). Create `session-hydrate.sh` as a thin SessionStart shell hook that invokes `hydrate-telemetry.mjs --silent` with the current project path. Register it in `settings.json` under `SessionStart`. Delete `warn-dor-dod.sh` from source and settings.json, and remove Eva's Writes subsection from pipeline-orchestration.md.

The result is zero agent_capture calls in any persona, rule, or reference file.

## Alternatives Considered

**Alternative A: Keep Eva's behavioral captures, add structured extraction only.** Eva continues to call `agent_capture` for user decisions and phase transitions. Only Wave 1 is implemented. Rejected: behavioral captures remain unreliable for the same reasons documented above. The "best-effort" qualifier means coverage is sparse. The hydrator extension (Wave 2) is lower risk and higher reliability than behavioral compliance.

**Alternative B: Extend brain-extractor to extract Eva's state from pipeline-state.md.** The brain-extractor is a SubagentStop hook -- it fires when a subagent (cal/colby/roz/agatha) completes, not at pipeline-level events. Pipeline-state.md is written by Eva between agent invocations. The extractor cannot observe it at SubagentStop time without reading the file -- which couples the extractor to a file read path that was not its original purpose and creates a separate concern in the extractor persona. The hydrator is the right tool because it already reads disk artifacts (JSONL files) and writes brain captures in batch. Rejected for coupling reasons.

**Alternative C: Use a PostCompact hook to read pipeline-state.md and emit captures.** PostCompact fires after context compaction, which is too infrequent and unpredictable to reliably capture all phase transitions. SessionStart fires at the beginning of every new session -- hydrating the previous session's state at that point is the right granularity. Rejected.

## Consequences

**Positive:**
- Eva's user decisions and phase transitions reliably reach the brain (via hydrator parsing files Eva already writes, not behavioral compliance)
- Structured quality signals (Roz verdicts, finding counts, Colby files changed, Cal step counts) captured per invocation with zero behavioral overhead
- warn-dor-dod.sh removed -- one fewer pre-hoc behavioral warning hook that produces stderr noise without mechanical effect
- After this ADR: no persona, no rule file, no reference instructs any agent to call agent_capture directly

**Negative:**
- Structured signal extraction depends on parsing natural language output. Agents that change their output format without updating the extractor's parsing logic produce silent extraction failures (missing metadata fields, not wrong data).
- State-file hydration has session granularity, not real-time granularity. A phase transition from a session that ended without a new session starting is not hydrated until the user next opens the project.

---

## Implementation Plan

### Wave 1: Structured Quality Signal Extraction (brain-extractor extension)

**Step 1: Extend brain-extractor.md with per-agent structured extraction schema**

Files:
- `source/shared/agents/brain-extractor.md` (modify)
- `source/claude/agents/brain-extractor.frontmatter.yml` (modify: bump description only)

The brain-extractor persona gains a new workflow section: "Structured Quality Signal Extraction." After the existing extraction steps (decisions/patterns/lessons), the extractor attempts a second capture for each of the four target agents using a per-agent parsing schema. The capture uses `thought_type: 'insight'`, `source_phase: 'quality'`, `importance: 0.5`, and `metadata.quality_signals: {...}`.

Per-agent parsing schemas (markers to search in `last_assistant_message`):

- `roz`: look for `PASS` or `FAIL` verdict line near the end of output (verdict field); scan for `BLOCKER`, `MUST-FIX`, `NIT`, `SUGGESTION` count patterns (e.g., "2 BLOCKERs", "BLOCKER: 2"); scan for `tests_before`, `tests_after`, `tests_broken` from suite summary lines (e.g., "14 passed", "1 failed").
- `colby`: look for `## DoD` section and a "Files Changed" row to extract file count; look for "rework" signal by scanning for phrases like "fixing Roz", "addressing Roz", "FAIL verdict", "prior QA FAIL" in the DoR section.
- `cal`: look for "N steps" pattern (ADR step count), "N tests" or "T-NNNN" pattern (test spec count), presence of `## DoR` and `## DoD` sections (boolean).
- `agatha`: look for "Written" and "updated" path lists in Agatha's receipt format (`Agatha: Written {paths}, updated {paths}`); scan for "Divergence" section and count findings by type ("drift", "gap").

If a marker is absent from the output, the corresponding field is omitted from `quality_signals` -- never set to null or fabricated. If zero fields are parseable, emit no quality signal capture.

Complexity: low. New workflow section in the extractor persona, no new tools, no schema changes.

Acceptance criteria:
- brain-extractor.md contains a "Structured Quality Signal Extraction" section with per-agent parsing schemas for all four agents
- Roz schema references PASS/FAIL, BLOCKER, MUST-FIX, NIT, SUGGESTION, tests_before, tests_after, tests_broken
- Colby schema references DoD section, files changed, rework signal
- Cal schema references step count, test spec count (T-NNNN pattern), DoR/DoD presence
- Agatha schema references Written/updated path count and Divergence findings
- Persona instructs: omit fields when markers absent; zero quality signal captures if no markers found
- Extraction is a best-effort second pass -- it does not replace or gate the existing decisions/patterns/lessons extraction

---

### Wave 2a: Hydrator state-file parsing

**Step 2: Extend hydrate-telemetry.mjs with state-file parsing**

Files:
- `brain/scripts/hydrate-telemetry.mjs` (modify: add `parseStateFiles()` function and a `--state-dir` argument)

Add a new top-level function `parseStateFiles(stateDir, pool, config)` that:
1. Reads `{stateDir}/pipeline-state.md` and `{stateDir}/context-brief.md` if they exist.
2. From `pipeline-state.md`: extract the feature name (from `**Feature:**` line), the sizing (from `**Sizing:**` line), and the phase transitions from the Progress checklist (lines matching `- [x]`). Each completed progress item becomes one `source_agent: 'eva'`, `thought_type: 'decision'`, `source_phase: 'pipeline'` capture with content: "Pipeline phase complete: {item text}" and metadata: `{ feature, sizing, phase_item, session_id, hydrated: true }`.
3. From `context-brief.md`: extract items under `## User Decisions` section (lines starting with `- `). Each becomes one `source_agent: 'eva'`, `thought_type: 'decision'`, `source_phase: 'pipeline'` capture with content: "{decision text}" and metadata: `{ feature, section: 'user_decisions', session_id, hydrated: true }`.
4. Duplicate detection: reuse the existing `alreadyHydrated()` pattern -- use `(session_id + '_state_phase_' + md5_of_item_text)` as the composite key in metadata. State-file captures skip if already present.
5. `insertTelemetryThought` reuse: uses the existing `insertTelemetryThought()` function with `thought_type: 'decision'`, `source_agent: 'eva'`, `source_phase: 'pipeline'`, `importance: 0.6`.

New CLI flags:
- `--state-dir <path>`: absolute path to the docs/pipeline directory to parse. Default: `{projectPath}/docs/pipeline` is NOT inferred from the JSONL path (different concerns). Must be provided explicitly for state-file parsing. When absent, state-file parsing is skipped.

The existing T1/T3 hydration path is unmodified. The new `parseStateFiles()` function runs as an additional step at the end of `main()` when `--state-dir` is provided.

Complexity: medium. New parsing logic and DB inserts; existing hydration code untouched.

Acceptance criteria:
- `parseStateFiles()` function exists and handles missing files gracefully (no-op when files absent)
- `--state-dir` argument recognized; when absent, state-file parsing skipped entirely
- Completed progress items from pipeline-state.md produce captures with correct metadata fields
- User decisions from context-brief.md produce captures with correct metadata fields
- Duplicate detection prevents re-insertion across sessions
- All error paths exit 0 (non-blocking, Retro #003)

---

### Wave 2b: SessionStart hook + cleanup

**Step 3: Create session-hydrate.sh and wire to SessionStart**

Files:
- `source/claude/hooks/session-hydrate.sh` (create)
- `.claude/hooks/session-hydrate.sh` (create — installed copy)
- `.claude/settings.json` (modify: add SessionStart block)
- `source/shared/commands/telemetry-hydrate.md` (modify: update SessionStart wiring description to match reality)

`session-hydrate.sh` is a thin wrapper (exit 0 always, Retro #003):
```
#!/bin/bash
# session-hydrate.sh -- SessionStart hook
# Runs hydrate-telemetry.mjs for T1 JSONL hydration and state-file parsing.
# Non-blocking: exits 0 always.
set -uo pipefail
...
PLUGIN_BRAIN="$CLAUDE_PROJECT_DIR/brain/scripts/hydrate-telemetry.mjs"
[ -f "$PLUGIN_BRAIN" ] || exit 0
PROJECT_PATH=$(echo "$CLAUDE_PROJECT_DIR" | sed 's|/|-|g' | sed 's/^-//')
SESSION_PATH="$HOME/.claude/projects/-$PROJECT_PATH"
STATE_DIR="$CLAUDE_PROJECT_DIR/docs/pipeline"
node "$PLUGIN_BRAIN" "$SESSION_PATH" --silent --state-dir "$STATE_DIR" >/dev/null 2>&1 || true
exit 0
```

Settings.json addition:
```json
"SessionStart": [{
  "hooks": [
    { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-hydrate.sh" }
  ]
}]
```

Complexity: low. Thin shell script, single settings.json addition.

Acceptance criteria:
- `source/claude/hooks/session-hydrate.sh` exists and is executable
- Script exits 0 on all paths (including missing node, missing script, hydration errors)
- settings.json `SessionStart` block exists with `session-hydrate.sh` entry
- `telemetry-hydrate.md` description updated to match actual wiring

**Step 4: Delete warn-dor-dod.sh + remove Eva's Writes subsection**

Files:
- `source/claude/hooks/warn-dor-dod.sh` (delete)
- `.claude/hooks/warn-dor-dod.sh` (delete — installed copy)
- `.claude/settings.json` (modify: remove warn-dor-dod.sh from SubagentStop block)
- `source/shared/rules/pipeline-orchestration.md` (modify: delete "Writes (cross-cutting only, best-effort)" subsection from Hybrid Capture Model)
- `source/shared/rules/agent-system.md` (modify: update Brain Configuration "Writes" bullet under `<section id="brain-config">` if present)
- `skills/pipeline-setup/SKILL.md` (modify: remove warn-dor-dod.sh from install list and settings.json template)
- `docs/guide/technical-reference.md` (modify: remove warn-dor-dod.sh from hook reference table)

Complexity: low. File deletions and targeted text removals.

Acceptance criteria:
- `source/claude/hooks/warn-dor-dod.sh` does not exist
- `.claude/hooks/warn-dor-dod.sh` does not exist
- `settings.json` SubagentStop block does not contain warn-dor-dod.sh entry
- `pipeline-orchestration.md` Hybrid Capture Model section contains no "Writes (cross-cutting only, best-effort)" subsection and no bulleted list of `agent_capture` calls attributed to Eva (excluding seed capture and reads which remain)
- `pipeline-orchestration.md` Hybrid Capture Model section retains the Reads subsection and the Seed Capture protocol
- SKILL.md does not reference warn-dor-dod.sh in hook install steps or settings.json template
- technical-reference.md does not list warn-dor-dod.sh as an active hook

---

## Test Specification

Tests live in `tests/hooks/test_brain_extractor_quality.py` (Wave 1) and `tests/adr-0025-telemetry/test_mechanical_telemetry.py` (Wave 2).

All tests in `test_mechanical_telemetry.py` use pytest. No bats.

| ID | Category | Description | Happy / Failure |
|----|----------|-------------|-----------------|
| T-0025-001 | Wave 1 / Roz signals | brain-extractor.md contains "Structured Quality Signal Extraction" section | Failure: section absent |
| T-0025-002 | Wave 1 / Roz signals | Roz schema references PASS/FAIL verdict extraction | Failure: neither PASS nor FAIL mentioned in Roz schema |
| T-0025-003 | Wave 1 / Roz signals | Roz schema references BLOCKER, MUST-FIX, NIT, SUGGESTION as parseable fields | Failure: one or more severity terms absent |
| T-0025-004 | Wave 1 / Roz signals | Roz schema references tests_before, tests_after, tests_broken (or equivalents: passed/failed counts) | Failure: no test count markers |
| T-0025-005 | Wave 1 / Colby signals | Colby schema references DoD section and files changed | Failure: neither DoD nor file count mentioned |
| T-0025-006 | Wave 1 / Colby signals | Colby schema references rework signal detection (prior FAIL, fixing Roz, or equivalent) | Failure: no rework language |
| T-0025-007 | Wave 1 / Cal signals | Cal schema references step count extraction | Failure: no step count language |
| T-0025-008 | Wave 1 / Cal signals | Cal schema references test spec count (T-NNNN pattern or equivalent) | Failure: no test spec count |
| T-0025-009 | Wave 1 / Cal signals | Cal schema references DoR/DoD presence check | Failure: no DoR or DoD presence check |
| T-0025-010 | Wave 1 / Agatha signals | Agatha schema references Written/updated path count | Failure: no Written/updated reference |
| T-0025-011 | Wave 1 / Agatha signals | Agatha schema references Divergence findings | Failure: no Divergence reference |
| T-0025-012 | Wave 1 / Omission guard | Persona instructs: omit fields when markers absent (not null, not fabricated) | Failure: "null" or "fabricate" or "infer" used as fallback instruction |
| T-0025-013 | Wave 1 / Omission guard | Persona instructs: zero quality signal captures is acceptable when no markers found | Failure: no "zero" or "skip" or "no capture" language for missing markers |
| T-0025-014 | Wave 1 / Metadata | Persona specifies thought_type: 'insight' and source_phase: 'quality' for quality signal captures | Failure: neither insight nor quality present in structured extraction schema |
| T-0025-015 | Wave 1 / Metadata | Persona specifies importance: 0.5 for quality signal captures | Failure: importance value absent from quality extraction section |
| T-0025-016 | Wave 2 / Hydrator function | hydrate-telemetry.mjs contains `parseStateFiles` function | Failure: function not present |
| T-0025-017 | Wave 2 / Hydrator CLI | hydrate-telemetry.mjs contains `--state-dir` argument handling | Failure: --state-dir not referenced |
| T-0025-018 | Wave 2 / Hydrator parsing | parseStateFiles parses pipeline-state.md Feature line and Sizing line | Failure: neither `**Feature:**` nor `**Sizing:**` pattern referenced in parse logic |
| T-0025-019 | Wave 2 / Hydrator parsing | parseStateFiles parses completed progress items (- [x] lines) | Failure: `[x]` or checkbox pattern absent from parse logic |
| T-0025-020 | Wave 2 / Hydrator parsing | parseStateFiles parses User Decisions section from context-brief.md | Failure: `## User Decisions` pattern absent |
| T-0025-021 | Wave 2 / Hydrator captures | State-file captures use source_agent 'eva', thought_type 'decision', source_phase 'pipeline' | Failure: any of these three fields incorrect |
| T-0025-022 | Wave 2 / Hydrator captures | State-file captures use importance 0.6 | Failure: importance 0.6 not in hydrator source |
| T-0025-023 | Wave 2 / Hydrator dedup | Duplicate detection for state-file captures is distinct from T1 agent-JSONL dedup (different metadata key) | Failure: same `hydrated: true` metadata key structure used without phase-item disambiguation |
| T-0025-024 | Wave 2 / Hydrator error handling | parseStateFiles does not throw when pipeline-state.md is absent | Failure: no file-existence guard in parse function |
| T-0025-025 | Wave 2 / Hydrator error handling | parseStateFiles does not throw when context-brief.md is absent | Failure: no file-existence guard for context-brief |
| T-0025-026 | Wave 2 / SessionStart hook | source/claude/hooks/session-hydrate.sh exists | Failure: file absent |
| T-0025-027 | Wave 2 / SessionStart hook | session-hydrate.sh exits 0 on all paths (no set -e, has `|| true` on node call) | Failure: `set -e` present without override, or node call lacks error guard |
| T-0025-028 | Wave 2 / SessionStart hook | session-hydrate.sh invokes hydrate-telemetry.mjs with --silent and --state-dir flags | Failure: either flag absent from script body |
| T-0025-029 | Wave 2 / SessionStart wiring | settings.json contains SessionStart block | Failure: SessionStart key absent from hooks |
| T-0025-030 | Wave 2 / SessionStart wiring | settings.json SessionStart block references session-hydrate.sh | Failure: session-hydrate.sh not in SessionStart hooks |
| T-0025-031 | Wave 2 / SessionStart wiring | settings.json remains valid JSON after SessionStart addition | Failure: json.loads() raises JSONDecodeError |
| T-0025-032 | Wave 2 / warn-dor-dod deletion | source/claude/hooks/warn-dor-dod.sh does not exist | Failure: file still present |
| T-0025-033 | Wave 2 / warn-dor-dod deletion | .claude/hooks/warn-dor-dod.sh does not exist (installed copy) | Failure: installed copy still present |
| T-0025-034 | Wave 2 / warn-dor-dod deletion | settings.json SubagentStop block does not reference warn-dor-dod.sh | Failure: warn-dor-dod.sh found in SubagentStop hooks |
| T-0025-035 | Wave 2 / Eva protocol deletion | source/shared/rules/pipeline-orchestration.md does not contain "Writes (cross-cutting only, best-effort)" subsection | Failure: "cross-cutting only, best-effort" string found in source |
| T-0025-036 | Wave 2 / Eva protocol deletion | pipeline-orchestration.md Hybrid Capture Model section does not contain "User decisions: calls agent_capture" bullet | Failure: "User decisions: calls" present in source |
| T-0025-037 | Wave 2 / Eva protocol deletion | pipeline-orchestration.md Hybrid Capture Model section does not contain "Phase transitions: calls agent_capture" bullet | Failure: "Phase transitions: calls" present in source |
| T-0025-038 | Wave 2 / Eva protocol deletion | pipeline-orchestration.md retains Reads subsection and Seed Capture protocol | Failure: "agent_search" or "Seed Capture" absent from brain-capture protocol |
| T-0025-039 | Wave 2 / SKILL.md cleanup | SKILL.md does not reference warn-dor-dod.sh in hook install list | Failure: "warn-dor-dod.sh" found in SKILL.md hook install section (not counting migration notes) |
| T-0025-040 | Wave 2 / SKILL.md cleanup | SKILL.md settings.json template does not include warn-dor-dod.sh SubagentStop entry | Failure: "warn-dor-dod.sh" in SKILL.md settings.json template block |
| T-0025-041 | Wave 2 / Zero agent_capture in personas | None of source/shared/agents/{cal,colby,roz,agatha}.md contains the string "agent_capture" | Failure: agent_capture found in any persona body |
| T-0025-042 | Wave 2 / Zero agent_capture in rules | source/shared/rules/pipeline-orchestration.md Hybrid Capture Model section does not contain "agent_capture" except in Reads context (agent_search) and Seed Capture protocol | Failure: "agent_capture" found in Eva Writes context |
| T-0025-043 | Wave 2 / Zero agent_capture in preamble | source/shared/references/agent-preamble.md does not contain "agent_capture" (Brain Capture Protocol removed in ADR-0024; verify still absent) | Failure: "agent_capture" found in preamble |

---

## UX Coverage

Not applicable. This ADR is pure infrastructure with no user-facing surfaces.

---

## Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| brain-extractor (per roz invocation) | `{ thought_type: 'insight', source_phase: 'quality', metadata: { quality_signals: { verdict, blocker_count, must_fix_count, nit_count, suggestion_count, tests_before, tests_after, tests_broken } } }` | Brain DB (atelier-brain agent_capture) | Step 1 |
| brain-extractor (per colby invocation) | `{ thought_type: 'insight', source_phase: 'quality', metadata: { quality_signals: { files_changed, dod_present, rework } } }` | Brain DB | Step 1 |
| brain-extractor (per cal invocation) | `{ thought_type: 'insight', source_phase: 'quality', metadata: { quality_signals: { step_count, test_spec_count, dor_present, dod_present } } }` | Brain DB | Step 1 |
| brain-extractor (per agatha invocation) | `{ thought_type: 'insight', source_phase: 'quality', metadata: { quality_signals: { docs_written, docs_updated, divergence_count, drift_count, gap_count } } }` | Brain DB | Step 1 |
| hydrate-telemetry.mjs (parseStateFiles) | `{ thought_type: 'decision', source_agent: 'eva', source_phase: 'pipeline', importance: 0.6, metadata: { feature, sizing, phase_item, session_id, hydrated: true } }` | Brain DB via insertTelemetryThought | Step 2 |
| session-hydrate.sh | Invokes hydrate-telemetry.mjs with project path + --state-dir | brain/scripts/hydrate-telemetry.mjs | Step 3 |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| brain-extractor.md quality signals section | Instructs extractor to call agent_capture with quality_signals metadata | atelier-brain MCP agent_capture | Step 1 |
| hydrate-telemetry.mjs parseStateFiles() | Reads docs/pipeline/{pipeline-state.md, context-brief.md}, writes brain thoughts | Brain DB (thoughts table) | Step 2 |
| session-hydrate.sh (SessionStart hook) | Fires hydrate-telemetry.mjs at session start | hydrate-telemetry.mjs main() | Step 3 |
| settings.json SessionStart block | Triggers session-hydrate.sh via Claude Code SessionStart event | session-hydrate.sh | Step 3 |

---

## Data Sensitivity

All captures are process metadata, not user data. No PII. Quality signals and pipeline state are internal pipeline telemetry -- `public-safe` in the brain (scope-restricted by project scope key).

---

## Notes for Colby

### Wave 1: brain-extractor.md extension

The brain-extractor is a Haiku agent. The new workflow section must be dense and unambiguous -- no hedging. The parsing schemas are pattern-matching instructions, not code. Use imperative language: "Scan for...", "If found...", "Emit...". The per-agent schemas are additive -- they come AFTER the existing decisions/patterns/lessons extraction steps (don't replace them).

Keep the section short. Haiku context window is small. Target: ~40 lines of new content in the persona.

The `metadata.quality_signals` object must be mentioned by name so the extractor emits the right key. The brain-extractor calls `agent_capture` with a `metadata` argument -- the existing `agent_capture` tool already supports arbitrary metadata objects.

Verify the existing `agent_capture` call signature in the extractor and make sure the structured extraction output uses the same call structure, just with different `thought_type` and `metadata`.

### Wave 2: hydrate-telemetry.mjs

The new `parseStateFiles()` function lives after the existing Eva-file processing loop (after the `for evaFiles` loop, before the Tier 3 summary generation). It is a new exported function with its own try/catch block.

The pipeline-state.md Progress section format is:
```
- [x] Agent name → phase description
- [ ] Pending item
```
Extract only `[x]` lines. The feature name is on `**Feature:** text` and sizing on `**Sizing:** text`.

The context-brief.md format for User Decisions:
```
## User Decisions
- 2026-04-04: decision text
```
Extract lines that start with `- ` under the `## User Decisions` header, up to the next `##` header.

For dedup keys: use a composite `session_id` + sha256 hash of the item text (first 8 chars of hash). Store as `metadata.content_hash`. The existing `alreadyHydrated()` function can be extended with a new query that checks `metadata @> { session_id, content_hash }`.

The `--state-dir` argument is optional. When not provided, `parseStateFiles()` is not called. This preserves backward compatibility with existing CI/test invocations that don't pass `--state-dir`.

### Wave 2: session-hydrate.sh

This script is extremely simple. Its only job is to construct the right paths and invoke hydrate-telemetry.mjs. Follow the same defensive pattern as session-boot.sh: `set -uo pipefail` (NOT `set -e`), `|| true` on all fallible commands, `exit 0` unconditionally at the end.

The path construction for SESSION_PATH is the same transform used in `telemetry-hydrate.md`:
- Take `$CLAUDE_PROJECT_DIR`
- Replace each `/` with `-`
- Strip leading `-`
- Prepend `$HOME/.claude/projects/-`

Verify `node` is available before calling it. If not, `exit 0`.

### Wave 2: pipeline-orchestration.md cleanup

The Hybrid Capture Model section in `source/shared/rules/pipeline-orchestration.md` currently has two subsections: "Reads" and "Writes (cross-cutting only, best-effort)". Delete the entire "Writes" subsection (lines 45-54 approximately in the source file) and the /devops Capture Gates section below it that instructs Eva to call `agent_capture` in /devops mode (this is also behavioral and unreliable -- the hydrator extension covers it via state files).

Retain:
- "Reads" subsection (agent_search calls, brain health check)
- "Seed Capture" protocol (seeds are a different mechanism -- they capture prospective ideas out-of-scope, not pipeline state)
- "Seed Surfacing" protocol (Eva reads seeds at boot)
- Brain unavailability fallback statement

The installed `.claude/rules/pipeline-orchestration.md` is updated by /pipeline-setup after Colby modifies the source. Colby edits `source/shared/rules/pipeline-orchestration.md` only.

### Wave 2: warn-dor-dod.sh removal and SKILL.md

Delete `source/claude/hooks/warn-dor-dod.sh` and `.claude/hooks/warn-dor-dod.sh`. Remove the SubagentStop entry from `settings.json`. In `skills/pipeline-setup/SKILL.md`:
- Remove warn-dor-dod.sh from the hook copy list
- Remove or update the settings.json template block -- the SubagentStop section should show only `log-agent-stop.sh` and the brain-extractor agent hook
- The existing migration note checking for `prompt-brain-capture.sh` can remain (it's a backward-compat cleanup for older installs)

In `docs/guide/technical-reference.md`, remove warn-dor-dod.sh from the hook reference table.

### Steps exceeding 10 files

Step 4 touches 7 files. Justified: each modification is a targeted deletion (remove one hook entry, delete one section, delete one table row). No new logic is introduced. The blast radius is wide but shallow -- consistent with ADR-0024's pattern.

---

## DoD: Verification Table

| Criterion | Verification | ADR Steps |
|-----------|-------------|-----------|
| All T-0025-001 through T-0025-015 pass | `pytest tests/hooks/test_brain_extractor_quality.py` | Step 1 |
| All T-0025-016 through T-0025-025 pass | `pytest tests/adr-0025-telemetry/test_mechanical_telemetry.py -k hydrator` | Step 2 |
| All T-0025-026 through T-0025-031 pass | `pytest tests/adr-0025-telemetry/test_mechanical_telemetry.py -k session` | Step 3 |
| All T-0025-032 through T-0025-043 pass | `pytest tests/adr-0025-telemetry/test_mechanical_telemetry.py -k cleanup` | Step 4 |
| Full test suite passes | `pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs` | All |
| No agent persona contains "agent_capture" | `grep -r "agent_capture" source/shared/agents/{cal,colby,roz,agatha}.md` returns nothing | Step 4 |
| No rule file instructs Eva to call agent_capture for pipeline events | `grep "User decisions.*calls agent_capture\|Phase transitions.*calls agent_capture" source/shared/rules/pipeline-orchestration.md` returns nothing | Step 4 |
| Session hydrate hook exits 0 when brain unavailable | `bash source/claude/hooks/session-hydrate.sh < /dev/null; echo $?` returns 0 | Step 3 |
| warn-dor-dod.sh absent from both source and installed dirs | `ls source/claude/hooks/warn-dor-dod.sh .claude/hooks/warn-dor-dod.sh` returns no such file | Step 4 |
| settings.json valid JSON with SessionStart block, without warn-dor-dod.sh | `python3 -c "import json; d=json.load(open('.claude/settings.json')); assert 'SessionStart' in d['hooks']"` passes | Step 3/4 |

---

## Handoff

ADR saved to `docs/architecture/ADR-0025-mechanical-telemetry-extraction.md`. 4 steps, 43 tests specified. Next: Roz reviews the test spec. Test spec: pending Roz approval.
