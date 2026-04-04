# ADR-0021: Mechanical Brain Wiring

## DoR: Requirements Extracted

| # | Requirement | Source | Priority |
|---|-------------|--------|----------|
| R1 | Add SubagentStop prompt hook that reminds Eva to capture after agent return | Roz investigation (Option A), context-brief.md | Must |
| R2 | Add PreToolUse(Agent) prompt hook that reminds Eva to prefetch brain context | Roz investigation (Option A), context-brief.md | Must |
| R3 | Add `mcpServers: atelier-brain` frontmatter to Cal, Colby, Roz, Agatha | Roz investigation (Option B), context-brief.md | Must |
| R4 | Add Brain Access workflow sections to Cal, Colby, Roz, Agatha defining WHAT and WHEN they capture | Roz investigation (Option B), context-brief.md | Must |
| R5 | Remove all dead behavioral brain prose from Eva's rules that has proven unreliable | context-brief.md ("Remove dead prose") | Must |
| R6 | Replace removed prose with pointers to mechanical systems (hooks, agent frontmatter) | context-brief.md | Must |
| R7 | Fix context eviction: brain capture protocols must NOT be evicted | Roz investigation (Root Cause 4), context-brief.md | Must |
| R8 | Keep Eva's cross-cutting captures (user decisions, phase transitions) but mark as best-effort | context-brief.md | Must |
| R9 | Read-only agents (Robert, Sable, Investigator, Distillator, Darwin, Deps, Sentinel, Ellis) do NOT get mcpServers | Eva's constraints | Must |
| R10 | Prompt hooks use `prompt` type (advisory, not blocking) | Eva's constraints | Must |
| R11 | `source/` templates and `.claude/` installed copies stay in sync | CLAUDE.md ("Triple target") | Must |
| R12 | Add `warn-brain-capture.sh` SubagentStop hook (parallel to `warn-dor-dod.sh`) | Roz investigation (Option B, point 3) | Must |
| R13 | Update `post-compact-reinject.sh` to include brain protocol reminder | Derived from R7 -- context eviction fix | Should |
| R14 | Update agent-preamble.md to reflect that agents with brain access capture directly | Derived from R4 -- shared preamble must reflect new model | Must |

**Retro risks:**
- Lesson #001 (behavioral constraints ignored): This is the CORE lesson driving the entire effort. Every design decision must answer "what enforces this mechanically?"
- Lesson #003 (stop hook race condition): New hooks must exit 0 always and not run expensive operations.

**Spec challenge:**
The spec assumes that Claude Code's `prompt` hook type will reliably re-inject brain reminders into Eva's context at the right moments. If prompt hooks are silently ignored or their injected messages are lost during compaction, the design degrades to status quo. However, prompt hooks are a strictly superior fallback compared to behavioral prose alone -- even 50% reliability beats 0%. Are we confident? Yes -- prompt hooks are documented Claude Code infrastructure, and even partial reliability improves the baseline.

**SPOF:** The `mcpServers: atelier-brain` frontmatter field. If Claude Code stops honoring `mcpServers` on project-owned agents (`.claude/agents/`), all four agents lose brain access simultaneously. Failure mode: agents silently skip brain captures (no error, no block). Graceful degradation: Eva's cross-cutting captures (marked best-effort) and the prompt hook reminders to Eva still function. The brain gets fewer domain-specific captures but does not go dark. The system reverts to status quo behavior, which is the same as today -- so this is non-catastrophic.

## Status

Proposed

## Context

Roz investigated why brain calls never happen during pipeline sessions despite 4500+ thoughts in the brain and fully functional MCP tools. Five root causes were identified:

1. **Behavioral, not mechanical.** Every brain interaction is a natural language directive to Eva. No hook, no enforcement script, no gate calls `agent_capture` or `agent_search`.
2. **Buried in JIT-loaded rules.** Brain protocols compete with five other concerns for Eva's attention at the moment they matter most.
3. **Hybrid capture model designed but never wired.** `pipeline-orchestration.md` defines agents capturing their own domain-specific knowledge, but no agent has `mcpServers` frontmatter or capture instructions.
4. **Context eviction kills protocol memory.** The eviction protocol removes telemetry capture logic from Eva's active context.
5. **Deferred-capture architecture.** JSONL hydration covers Tier 1 token metrics post-hoc but cannot cover Tier 2/3 quality metrics (rework rate, first-pass QA, EvoScore).

The brain's own research (thoughts `3c901c33`, `07c77c50`, `b2d7d075`) identified the exact hooks and frontmatter fields needed. The knowledge exists. The tools exist. The wiring does not.

## Decision

Implement Options A + B from Roz's investigation, plus cleanup of dead behavioral prose.

**Option A (Prompt Hooks):** Add two `prompt`-type hooks that inject advisory reminders into Eva's context at mechanical trigger points. These are not blocking -- they are context reinforcement that survives compaction.

**Option B (Agent Brain Wiring):** Add `mcpServers: atelier-brain` to Cal, Colby, Roz, and Agatha frontmatter. Add Brain Access sections to each persona defining domain-specific capture gates. Add a `warn-brain-capture.sh` SubagentStop hook that checks output for `agent_capture` mentions and warns on stderr when absent.

**Cleanup:** Remove all unreliable behavioral brain instructions from Eva's rules. Replace with pointers to the mechanical systems. Mark Eva's remaining cross-cutting captures as "best-effort" rather than "MANDATORY."

### Anti-Goals

1. **Anti-goal: Blocking enforcement of brain captures.** Reason: Shell hooks cannot call MCP tools -- they can only warn. A blocking hook that requires `agent_capture` before advancing would deadlock because the hook cannot verify MCP tool calls occurred. Revisit: when Claude Code hooks gain MCP tool call capability.

2. **Anti-goal: Real-time Tier 1 telemetry capture per invocation.** Reason: Tier 1 token metrics come from JSONL files post-session via `hydrate-telemetry.mjs`. The JSONL hydration system is already functional and covers Tier 1. In-session Tier 1 capture would duplicate this. Revisit: if the JSONL hydration system is deprecated or Agent tool returns expose token counts natively.

3. **Anti-goal: Giving read-only agents (Robert, Sable, Investigator, Distillator, Darwin, Deps, Sentinel, Ellis) brain access.** Reason: These agents consume brain context via Eva's injected `<brain-context>` tag. Giving them write access would create duplicate captures (`source_agent: 'robert'` vs Eva capturing Robert's findings). Read-only agents produce structured output that Eva can capture on their behalf. Revisit: if a read-only agent's domain-specific knowledge proves too nuanced for Eva to capture accurately.

## Alternatives Considered

### Alternative A: Prompt Hooks Only (No Agent Brain Access)

Add SubagentStop and PreToolUse(Agent) prompt hooks. Keep Eva as sole brain caller.

**Tradeoffs:**
- (+) Minimal change surface -- 2 hook scripts + settings.json update
- (+) No agent persona changes needed
- (-) Eva remains sole brain caller -- the behavioral reliability problem is mitigated, not eliminated
- (-) Brain captures are all `source_agent: 'eva'` -- loses domain attribution
- (-) Does not wire the hybrid capture model already designed in rules

**Rejected because:** This addresses "Eva forgets" but does not address "agents should capture in their own voice." The hybrid model exists for a reason -- domain expertise is freshest in the agent's own context window.

### Alternative B: Agent Brain Access Only (No Prompt Hooks)

Wire `mcpServers` into agents. Add capture instructions. No prompt hooks.

**Tradeoffs:**
- (+) Agents capture domain-specific knowledge with attribution
- (+) Reduces Eva's capture burden
- (-) Eva still forgets to prefetch brain context before invocations
- (-) Agent capture instructions are still behavioral -- agents can skip them
- (-) No mechanical reminder to Eva for cross-cutting captures

**Rejected because:** Moves the "behavioral instruction" problem from Eva to agents. Agents are fresher (single-task context) so they are more likely to follow instructions, but there is no reinforcement mechanism.

### Chosen: A + B Combined

Prompt hooks reinforce Eva's cross-cutting responsibilities. Agent brain access enables domain-specific captures. `warn-brain-capture.sh` provides a safety net. Each mechanism covers the other's gaps.

## Consequences

### Positive
- Brain captures shift from ~0% reliability to a layered reinforcement model
- Domain-specific knowledge gets proper attribution (`source_agent: 'cal'` vs `source_agent: 'eva'`)
- Dead behavioral prose removed -- rules become honest about what is enforced and what is best-effort
- Context eviction fix ensures brain protocols survive compaction
- `warn-brain-capture.sh` provides telemetry on capture compliance (visible in stderr)

### Negative
- Prompt hooks add latency per invocation (single-turn eval cost)
- Agent brain calls increase per-agent token usage
- Four agent personas gain complexity (Brain Access sections)
- Agent brain captures are still behavioral within the agent context -- the `warn-brain-capture.sh` hook is a safety net, not a gate

### Risks
- If `mcpServers` frontmatter is silently ignored on project-owned agents, the entire Option B path fails. Mitigation: test immediately in Step 1. If frontmatter is ignored, fall back to prompt hooks as the primary mechanism.
- Prompt hook latency may be noticeable. Mitigation: prompt hooks are advisory (non-blocking) and lightweight -- a single-turn evaluation, not a full agent invocation.

## Implementation Plan

### Step 1: Prompt Hooks for Eva (Advisory Brain Reminders)

Create two prompt hook scripts and register them in `settings.json`.

**S1: Demoable.** After this step, Eva receives advisory brain reminders before every agent invocation and after every agent return.
**S2: Context-bounded.** 6 files.
**S3: Independently verifiable.** Yes -- prompt hooks fire independently of agent brain access.
**S4: Revert-cheap.** Yes -- remove hooks from settings.json and delete scripts.
**S5: Already small.** Yes -- 6 files, one clear behavior.

- **Files to create:**
  - `.claude/hooks/prompt-brain-prefetch.sh` -- PreToolUse(Agent) prompt hook. Outputs a reminder to Eva to call `agent_search` before constructing the invocation. Exits 0 always.
  - `.claude/hooks/prompt-brain-capture.sh` -- SubagentStop prompt hook. Outputs a reminder to Eva to call `agent_capture` for the key finding/decision from this agent's output. Exits 0 always.
  - `source/claude/hooks/prompt-brain-prefetch.sh` -- Template copy (source/ sync)
  - `source/claude/hooks/prompt-brain-capture.sh` -- Template copy (source/ sync)

- **Files to modify:**
  - `.claude/settings.json` -- Register both prompt hooks with `"type": "prompt"`. PreToolUse(Agent) gets `prompt-brain-prefetch.sh`. SubagentStop gets `prompt-brain-capture.sh`.
  - `source/settings.json.template` -- If it exists (it does not -- settings.json is project-specific, not templated). Note: `.claude/settings.json` is project-installed, not templated from source/. Only the `.claude/` copy is modified.

- **Acceptance criteria:**
  - Both hooks registered in `.claude/settings.json` with `"type": "prompt"`
  - Both hooks exit 0 always (non-blocking)
  - `prompt-brain-prefetch.sh` outputs advisory text when the invoked agent is one of the capture-capable agents (cal, colby, roz, agatha)
  - `prompt-brain-capture.sh` outputs advisory text identifying the agent that just returned
  - Both hooks handle missing `jq` gracefully (exit 0 with no output)
  - Both hooks follow `set -uo pipefail` (not `set -e` per retro #003)

- **Estimated complexity:** Low

### Step 2a: Agent Brain Access -- Cal Frontmatter + Brain Access Section

Add `mcpServers: atelier-brain` to Cal's frontmatter and a Brain Access workflow section defining what and when Cal captures.

**S1: Demoable.** After this step, Cal has brain tools available and capture instructions for architectural decisions.
**S2: Context-bounded.** 2 files.
**S3: Independently verifiable.** Yes -- Cal's brain access is independent of other agents.
**S4: Revert-cheap.** Yes -- revert frontmatter and remove section.
**S5: Already small.** Yes -- 2 files, one behavior.

- **Files to modify:**
  - `.claude/agents/cal.md` -- Add `mcpServers` to frontmatter. Add `<protocol id="brain-access">` section to workflow defining: capture decisions (`thought_type: 'decision'`) after ADR completion with alternatives chosen/rejected; capture patterns (`thought_type: 'pattern'`) for reusable architectural patterns identified during design. Captures use `source_agent: 'cal'`, `source_phase: 'design'`.
  - `source/shared/agents/cal.md` -- Mirror changes (source/ sync)

- **Acceptance criteria:**
  - Cal frontmatter includes `mcpServers:\n  - atelier-brain` in both `.claude/` and `source/`
  - Brain Access section defines 2+ specific capture gates with `thought_type`, `source_agent`, `source_phase`, and trigger condition
  - Brain Access section includes a "When brain is unavailable, skip all captures" clause
  - Existing persona content unchanged except for the additions
  - The "Eva uses these to capture knowledge to the brain" line in output section updated to reflect Cal's own capture responsibility

- **Estimated complexity:** Low

### Step 2b: Agent Brain Access -- Colby Frontmatter + Brain Access Section

Add `mcpServers: atelier-brain` to Colby's frontmatter and a Brain Access workflow section.

**S1: Demoable.** After this step, Colby has brain tools available and capture instructions for implementation insights.
**S2: Context-bounded.** 2 files.
**S3: Independently verifiable.** Yes.
**S4: Revert-cheap.** Yes.
**S5: Already small.** Yes -- 2 files, one behavior.

- **Files to modify:**
  - `.claude/agents/colby.md` -- Add `mcpServers` to frontmatter. Add `<protocol id="brain-access">` section defining: capture implementation insights (`thought_type: 'insight'`) after each unit (gotchas, contract shapes, workarounds documented in DoD); capture patterns (`thought_type: 'pattern'`) for reusable implementation patterns discovered during build. Captures use `source_agent: 'colby'`, `source_phase: 'build'`.
  - `source/shared/agents/colby.md` -- Mirror changes (source/ sync)

- **Acceptance criteria:**
  - Colby frontmatter includes `mcpServers:\n  - atelier-brain`
  - Brain Access section defines 2+ specific capture gates
  - "When brain is unavailable" clause present
  - The "Eva uses these to capture knowledge to the brain" line updated
  - Existing persona content unchanged

- **Estimated complexity:** Low

### Step 2c: Agent Brain Access -- Roz Frontmatter + Brain Access Section

Add `mcpServers: atelier-brain` to Roz's frontmatter and a Brain Access workflow section.

**S1: Demoable.** After this step, Roz has brain tools available and capture instructions for QA findings.
**S2: Context-bounded.** 2 files.
**S3: Independently verifiable.** Yes.
**S4: Revert-cheap.** Yes.
**S5: Already small.** Yes -- 2 files, one behavior.

- **Files to modify:**
  - `.claude/agents/roz.md` -- Add `mcpServers` to frontmatter. Add `<protocol id="brain-access">` section defining: capture QA findings (`thought_type: 'pattern'`) for recurring failure patterns and module-specific risks after each QA run; capture lessons (`thought_type: 'lesson'`) for investigation findings that go beyond the immediate fix. Captures use `source_agent: 'roz'`, `source_phase: 'qa'`.
  - `source/shared/agents/roz.md` -- Mirror changes (source/ sync)

- **Acceptance criteria:**
  - Roz frontmatter includes `mcpServers:\n  - atelier-brain`
  - Brain Access section defines 2+ specific capture gates
  - "When brain is unavailable" clause present
  - The "Eva uses these to capture knowledge to the brain" line updated
  - Existing persona content unchanged

- **Estimated complexity:** Low

### Step 2d: Agent Brain Access -- Agatha Frontmatter + Brain Access Section

Add `mcpServers: atelier-brain` to Agatha's frontmatter and a Brain Access workflow section.

**S1: Demoable.** After this step, Agatha has brain tools available and capture instructions for documentation decisions.
**S2: Context-bounded.** 2 files.
**S3: Independently verifiable.** Yes.
**S4: Revert-cheap.** Yes.
**S5: Already small.** Yes -- 2 files, one behavior.

- **Files to modify:**
  - `.claude/agents/agatha.md` -- Add `mcpServers` to frontmatter. Add `<protocol id="brain-access">` section defining: capture decisions (`thought_type: 'decision'`) for doc structure decisions, what was added vs deferred; capture insights (`thought_type: 'insight'`) for divergences found between spec and code. Captures use `source_agent: 'agatha'`, `source_phase: 'docs'`.
  - `source/shared/agents/agatha.md` -- Mirror changes (source/ sync)

- **Acceptance criteria:**
  - Agatha frontmatter includes `mcpServers:\n  - atelier-brain`
  - Brain Access section defines 2+ specific capture gates
  - "When brain is unavailable" clause present
  - The "Eva uses these to capture knowledge to the brain" line updated
  - Existing persona content unchanged

- **Estimated complexity:** Low

### Step 3: Warning Hook for Brain Capture Compliance

Create `warn-brain-capture.sh` as a SubagentStop hook that checks agent output for `agent_capture` and warns when absent. Parallel to existing `warn-dor-dod.sh` pattern.

**S1: Demoable.** After this step, agents that have brain access receive a stderr warning when they return without evidence of brain captures.
**S2: Context-bounded.** 4 files.
**S3: Independently verifiable.** Yes -- fires independently of prompt hooks and agent content.
**S4: Revert-cheap.** Yes.
**S5: Already small.** Yes -- 4 files, one behavior.

- **Files to create:**
  - `.claude/hooks/warn-brain-capture.sh` -- SubagentStop hook. Checks `agent_type` against `cal|colby|roz|agatha`. If output does not contain `agent_capture`, warns on stderr. Exits 0 always.
  - `source/claude/hooks/warn-brain-capture.sh` -- Template copy (source/ sync)

- **Files to modify:**
  - `.claude/settings.json` -- Add `warn-brain-capture.sh` to SubagentStop hooks with `"if": "agent_type == 'cal' || agent_type == 'colby' || agent_type == 'roz' || agent_type == 'agatha'"`
  - (Note: `.claude/settings.json` already modified in Step 1 -- this step adds one more hook entry to the SubagentStop array)

- **Acceptance criteria:**
  - Hook fires only for cal, colby, roz, agatha (not for read-only agents)
  - Hook checks `last_assistant_message` for the string `agent_capture`
  - When `agent_capture` is absent from output, hook writes a warning to stderr
  - When `agent_capture` is present, hook exits silently
  - Hook handles missing `jq`, missing output gracefully (exit 0)
  - Hook follows `warn-dor-dod.sh` pattern exactly (no set -e, exit 0 always)

- **Estimated complexity:** Low

### Step 4: Shared Preamble and Output Boilerplate Update

Update `agent-preamble.md` to reflect that agents with brain access capture directly. Update the "Eva uses these to capture knowledge to the brain" DoD line across non-brain-access agents to clarify the distinction.

**S1: Demoable.** After this step, the shared preamble accurately describes the hybrid capture model where some agents capture directly and others surface knowledge for Eva.
**S2: Context-bounded.** 6 files.
**S3: Independently verifiable.** Yes -- documentation accuracy is independently verifiable.
**S4: Revert-cheap.** Yes.
**S5: Already small.** Yes -- 6 files, one behavior (documentation alignment).

- **Files to modify:**
  - `.claude/references/agent-preamble.md` -- Update step 4 to differentiate: agents with brain access (`mcpServers: atelier-brain`) capture directly per their Brain Access protocol; agents without brain access surface knowledge in their output for Eva to capture.
  - `source/references/agent-preamble.md` -- Mirror changes (source/ sync)
  - `.claude/agents/ellis.md` -- Update the "Eva uses these to capture knowledge to the brain" line to be accurate (Ellis does not have brain access; Eva captures on his behalf).
  - `source/shared/agents/ellis.md` -- Mirror changes
  - `.claude/references/invocation-templates.md` -- Update brain-context tag documentation to note that agents with `mcpServers: atelier-brain` also capture independently (the template brain-context tag is for prefetched read context; agent captures happen within the agent's own workflow).
  - `source/references/invocation-templates.md` -- Mirror changes

- **Acceptance criteria:**
  - agent-preamble.md step 4 distinguishes brain-access agents from read-only agents
  - Ellis output section accurately reflects that Eva captures on his behalf
  - Invocation templates document that brain-context tag is for reads; agent captures are separate
  - All changes mirrored between `.claude/` and `source/`

- **Estimated complexity:** Low

### Step 5: Dead Prose Cleanup -- Eva's Rules

Remove unreliable behavioral brain instructions from Eva's rules. Replace with pointers to mechanical systems. Fix context eviction.

**S1: Demoable.** After this step, Eva's rules honestly describe what is mechanically enforced vs best-effort, and the context eviction protocol no longer strips brain capture awareness.
**S2: Context-bounded.** 8 files (this is the ceiling; justified below).
**S3: Independently verifiable.** Yes -- a grep for "MANDATORY" combined with brain instructions will show reduced count, and the context eviction protocol will exclude brain captures.
**S4: Revert-cheap.** Yes -- rules are markdown.
**S5: Not applicable -- 8 files exceeds S5 threshold.

**8-file justification:** This step modifies 4 rules files plus their source/ mirrors (4 + 4 = 8). The changes are all the same type (text edits to markdown) and serve one purpose (cleanup dead prose). Splitting this into per-file steps would add orchestration overhead with no verifiability benefit -- the prose cleanup is only meaningful as a set.

- **Files to modify:**
  - `.claude/rules/agent-system.md` -- **Brain Configuration section (lines 10-14):** Remove "Brain reads are Eva's responsibility" and "Brain writes are Eva's responsibility" directives. Replace with: "Brain reads: Eva prefetches via `agent_search` and injects into `<brain-context>`. Prompt hook reinforcement: `prompt-brain-prefetch.sh`. Brain writes: Agents with `mcpServers: atelier-brain` (Cal, Colby, Roz, Agatha) capture domain-specific knowledge directly. Eva captures cross-cutting concerns only (best-effort -- reinforced by `prompt-brain-capture.sh`). See individual agent personas for capture gates." Also update **Shared Agent Behaviors section (line 266-267):** Update brain context consumption bullet to reflect hybrid model.
  - `.claude/rules/pipeline-orchestration.md` -- **Brain Access protocol (lines 35-90):** Remove the "MANDATORY" label from the heading. Retain the Hybrid Capture Model description but update it to reference agent frontmatter as the mechanism. Remove the "Verification (spot-check)" subsection -- `warn-brain-capture.sh` replaces this behavioral instruction. Mark Eva's cross-cutting write list as "best-effort (reinforced by prompt hook)." Keep the `/devops Capture Gates` and `Seed Capture` sections (those are Eva-specific and already low-frequency). Remove "Agents write their own domain-specific captures directly" as a behavioral instruction -- it is now wired via frontmatter. Replace with a pointer: "See agent personas (Cal, Colby, Roz, Agatha) for domain-specific capture gates, wired via `mcpServers: atelier-brain` frontmatter."
  - `.claude/rules/pipeline-orchestration.md` -- **Telemetry Capture Protocol:** Remove "MANDATORY" from the heading. Keep the Tier 1/2/3 structure but mark Tier 2 and Tier 3 captures as "best-effort (Eva-dependent, reinforced by prompt hook)." This is honest: the prompt hook reminds Eva, but Eva may still skip under context pressure.
  - `.claude/rules/default-persona.md` -- **Context Eviction protocol (lines 148-160):** Remove "Telemetry trend computation logic" from the eviction list. Add explicit retention note: "Eva retains: ... brain capture protocol awareness (reinforced by hooks post-compaction)." **Brain Access section (lines 162-165):** Update pointer to note mechanical enforcement via hooks and agent frontmatter.
  - `.claude/rules/pipeline-models.md` -- **Brain Integration subsection (lines 101-105):** The `agent_search` and `agent_capture` instructions here are model-selection-specific. Keep them but mark as "best-effort" rather than leaving the implicit "MANDATORY" framing.
  - `.claude/references/pipeline-operations.md` -- **Brain prefetch protocol (lines 17-33):** Remove the Eva-only framing. Update to reference the hybrid model: "Eva prefetches brain context. Agents with brain access also capture directly." Keep the 3-step summary but add: "Reinforced by `prompt-brain-prefetch.sh` PreToolUse hook."
  - `source/rules/agent-system.md` -- Mirror `.claude/rules/agent-system.md` changes
  - `source/rules/pipeline-orchestration.md` -- Mirror changes
  - `source/rules/default-persona.md` -- Mirror changes
  - `source/rules/pipeline-models.md` -- Mirror changes
  - `source/references/pipeline-operations.md` -- Mirror changes

**Wait -- this is 11 files (6 unique + 5 mirrors). Splitting required.**

### Step 5a: Dead Prose Cleanup -- agent-system.md + pipeline-orchestration.md (Brain Access Protocol)

Remove dead behavioral prose from the two primary brain protocol files.

**S1: Demoable.** After this step, the two core brain protocol documents honestly describe the hybrid capture model with mechanical enforcement pointers.
**S2: Context-bounded.** 4 files.
**S3: Independently verifiable.** Yes.
**S4: Revert-cheap.** Yes.
**S5: Already small.** Yes.

- **Files to modify:**
  - `.claude/rules/agent-system.md` -- Brain Configuration section: replace Eva-centric directives with hybrid model pointers. Shared Agent Behaviors: update brain consumption bullet.
  - `source/rules/agent-system.md` -- Mirror changes
  - `.claude/rules/pipeline-orchestration.md` -- Brain Access protocol: remove "MANDATORY" label, update Hybrid Capture Model to reference agent frontmatter, remove Verification (spot-check) subsection, mark Eva's cross-cutting writes as best-effort. Telemetry Capture: remove "MANDATORY", mark Tier 2/3 as best-effort.
  - `source/rules/pipeline-orchestration.md` -- Mirror changes

- **Acceptance criteria:**
  - No instance of "MANDATORY" in brain-related protocol headings
  - Brain Access section references `mcpServers: atelier-brain` as the mechanism for agent captures
  - Eva's cross-cutting captures marked "best-effort (reinforced by prompt hook)"
  - "Verification (spot-check)" subsection removed (replaced by `warn-brain-capture.sh`)
  - Telemetry Tier 2/3 headings do not say "MANDATORY"
  - Content is accurate and pointers reference the correct hook/file names
  - Source/ mirrors match .claude/ copies

- **Estimated complexity:** Medium (careful editing of dense rules text)

### Step 5b: Dead Prose Cleanup -- default-persona.md, pipeline-models.md, pipeline-operations.md

Clean up remaining dead prose in Eva's boot sequence, context eviction, model selection, and prefetch protocol.

**S1: Demoable.** After this step, Eva's boot sequence, context eviction, and model selection rules accurately describe brain interaction with mechanical reinforcement.
**S2: Context-bounded.** 6 files.
**S3: Independently verifiable.** Yes.
**S4: Revert-cheap.** Yes.
**S5: Already small.** Yes -- 6 files (3 unique + 3 mirrors), one behavior.

- **Files to modify:**
  - `.claude/rules/default-persona.md` -- Context Eviction: remove "Telemetry trend computation logic" from eviction list, add brain capture protocol awareness to retention list. Brain Access section: update pointer.
  - `source/rules/default-persona.md` -- Mirror changes
  - `.claude/rules/pipeline-models.md` -- Brain Integration subsection: mark `agent_search` and `agent_capture` instructions as best-effort.
  - `source/rules/pipeline-models.md` -- Mirror changes
  - `.claude/references/pipeline-operations.md` -- Brain prefetch protocol: update to reflect hybrid model, add prompt hook reference.
  - `source/references/pipeline-operations.md` -- Mirror changes

- **Acceptance criteria:**
  - Context eviction no longer strips brain capture awareness
  - Context eviction retention list explicitly includes "brain capture protocol awareness"
  - pipeline-models.md brain integration section marked best-effort
  - pipeline-operations.md prefetch protocol references prompt hook reinforcement
  - All source/ mirrors match .claude/ copies

- **Estimated complexity:** Medium

### Step 6: PostCompact Hook Enhancement

Update `post-compact-reinject.sh` to include a brain protocol reminder after compaction, ensuring brain capture awareness survives context window compaction.

**S1: Demoable.** After this step, Eva's context after compaction includes a brain protocol reminder.
**S2: Context-bounded.** 2 files.
**S3: Independently verifiable.** Yes.
**S4: Revert-cheap.** Yes.
**S5: Already small.** Yes -- 2 files.

- **Files to modify:**
  - `.claude/hooks/post-compact-reinject.sh` -- Add a brain protocol reminder section after the context-brief output. The reminder should be a short block (5-6 lines) stating: brain prefetch before Agent invocations, agent captures by cal/colby/roz/agatha, Eva cross-cutting captures (best-effort).
  - `source/claude/hooks/post-compact-reinject.sh` -- Mirror changes

- **Acceptance criteria:**
  - PostCompact output includes brain protocol reminder section
  - Reminder is concise (<10 lines) and actionable
  - Reminder mentions the three mechanisms: prompt hooks, agent captures, Eva cross-cutting
  - Hook still exits 0 always
  - Hook still handles missing files gracefully

- **Estimated complexity:** Low

## Comprehensive Test Specification

### Step 1 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-001 | Happy | `prompt-brain-prefetch.sh` receives valid JSON with `tool_name: "Agent"` and `agent_type: "colby"` on stdin, outputs advisory text containing "agent_search" to stdout, exits 0 |
| T-0021-002 | Happy | `prompt-brain-capture.sh` receives valid JSON with `agent_type: "cal"` and non-empty `last_assistant_message` on stdin, outputs advisory text containing "agent_capture" to stdout, exits 0 |
| T-0021-003 | Failure | `prompt-brain-prefetch.sh` receives JSON with missing `tool_input` field, exits 0 with no output (graceful degradation) |
| T-0021-004 | Failure | `prompt-brain-capture.sh` receives JSON with `agent_type: ""` (empty), exits 0 with no output |
| T-0021-005 | Boundary | `prompt-brain-prefetch.sh` receives JSON with `agent_type: "ellis"` (read-only agent), outputs nothing (only fires for capture-capable agents), exits 0 |
| T-0021-006 | Boundary | `prompt-brain-prefetch.sh` receives JSON with `agent_type: "poirot"` (read-only agent), outputs nothing, exits 0 |
| T-0021-007 | Boundary | `prompt-brain-capture.sh` receives JSON with `agent_type: "sentinel"` (read-only agent), outputs nothing, exits 0 |
| T-0021-008 | Error | `prompt-brain-prefetch.sh` runs on system without `jq` installed, exits 0 with no output |
| T-0021-009 | Error | `prompt-brain-capture.sh` receives malformed JSON on stdin, exits 0 with no output |
| T-0021-010 | Regression | `.claude/settings.json` contains both prompt hooks registered with `"type": "prompt"`, not `"type": "command"` |
| T-0021-011 | Regression | `prompt-brain-prefetch.sh` is registered on `PreToolUse` matcher `Agent` (same matcher as `enforce-sequencing.sh`), not a different matcher |
| T-0021-012 | Regression | `prompt-brain-capture.sh` is registered on `SubagentStop` (same event as `warn-dor-dod.sh`), not a different event |
| T-0021-013 | Happy | `prompt-brain-prefetch.sh` receives JSON with `agent_type: "cal"`, outputs advisory text mentioning "cal" and "agent_search", exits 0 |
| T-0021-014 | Happy | `prompt-brain-capture.sh` receives JSON with `agent_type: "roz"`, outputs advisory text mentioning "roz" and "agent_capture", exits 0 |
| T-0021-015 | Happy | `prompt-brain-prefetch.sh` receives JSON with `agent_type: "agatha"`, outputs advisory text, exits 0 |
| T-0021-099 | Error | `prompt-brain-prefetch.sh` receives completely empty stdin (zero bytes), exits 0 with no output |
| T-0021-100 | Regression | `.claude/hooks/prompt-brain-prefetch.sh` and `.claude/hooks/prompt-brain-capture.sh` are executable (file mode includes execute bit, verified by `test -x`) |
| T-0021-105 | Regression | `.claude/settings.json` is valid JSON after all hook registrations from Steps 1 and 3 (parseable by `jq .` without error) |
| T-0021-109 | Error | `prompt-brain-capture.sh` receives completely empty stdin (zero bytes), exits 0 with no output |
| T-0021-117 | Regression | `source/claude/hooks/prompt-brain-prefetch.sh` and `source/claude/hooks/prompt-brain-capture.sh` are executable (file mode includes execute bit) |

### Step 2a Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-016 | Happy | `.claude/agents/cal.md` YAML frontmatter contains `mcpServers` key with value including `atelier-brain` |
| T-0021-017 | Happy | `source/shared/agents/cal.md` YAML frontmatter contains `mcpServers` key with value including `atelier-brain` |
| T-0021-018 | Happy | `.claude/agents/cal.md` contains a `<protocol id="brain-access">` section |
| T-0021-019 | Happy | Cal's Brain Access section mentions `thought_type: 'decision'` as a capture gate |
| T-0021-020 | Happy | Cal's Brain Access section mentions `source_agent: 'cal'` |
| T-0021-021 | Failure | Cal's Brain Access section contains the exact string "When brain is unavailable" followed by a skip/no-op instruction |
| T-0021-022 | Regression | Cal's `tools` frontmatter field is unchanged (still includes Read, Write, Edit, Glob, Grep, Bash, Agent(roz)) |
| T-0021-023 | Regression | Cal's existing `<workflow>` tag content (from `## ADR Production` through `## Hard Gates`) is byte-identical to pre-edit content |
| T-0021-024 | Boundary | `.claude/agents/cal.md` and `source/shared/agents/cal.md` Brain Access sections are identical |
| T-0021-101 | Error | `.claude/agents/cal.md` YAML frontmatter (content between `---` delimiters) is valid YAML parseable by `python3 -c "import yaml; yaml.safe_load(open(...))"` or equivalent |
| T-0021-115 | Boundary | Cal's `<protocol id="brain-access">` section appears after the closing `</workflow>` tag and before the `<examples>` tag |

### Step 2b Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-025 | Happy | `.claude/agents/colby.md` YAML frontmatter contains `mcpServers` key with value including `atelier-brain` |
| T-0021-026 | Happy | `source/shared/agents/colby.md` YAML frontmatter contains `mcpServers` key with value including `atelier-brain` |
| T-0021-027 | Happy | `.claude/agents/colby.md` contains a `<protocol id="brain-access">` section |
| T-0021-028 | Happy | Colby's Brain Access section mentions `thought_type: 'insight'` as a capture gate |
| T-0021-029 | Happy | Colby's Brain Access section mentions `source_agent: 'colby'` |
| T-0021-030 | Failure | Colby's Brain Access section contains the exact string "When brain is unavailable" followed by a skip/no-op instruction |
| T-0021-031 | Regression | Colby's `tools` frontmatter field is unchanged |
| T-0021-032 | Regression | Colby's existing `<workflow>` tag content (from `## Mockup Mode` through `## Branch & MR Mode`) is byte-identical to pre-edit content |
| T-0021-033 | Boundary | `.claude/agents/colby.md` and `source/shared/agents/colby.md` Brain Access sections are identical |
| T-0021-102 | Error | `.claude/agents/colby.md` YAML frontmatter is valid YAML parseable by a standard YAML parser |

### Step 2c Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-034 | Happy | `.claude/agents/roz.md` YAML frontmatter contains `mcpServers` key with value including `atelier-brain` |
| T-0021-035 | Happy | `source/shared/agents/roz.md` YAML frontmatter contains `mcpServers` key with value including `atelier-brain` |
| T-0021-036 | Happy | `.claude/agents/roz.md` contains a `<protocol id="brain-access">` section |
| T-0021-037 | Happy | Roz's Brain Access section mentions `thought_type: 'pattern'` for recurring failure patterns |
| T-0021-038 | Happy | Roz's Brain Access section mentions `source_agent: 'roz'` |
| T-0021-039 | Failure | Roz's Brain Access section contains the exact string "When brain is unavailable" followed by a skip/no-op instruction |
| T-0021-040 | Regression | Roz's `disallowedTools` frontmatter field is unchanged (Agent, Edit, MultiEdit, NotebookEdit) |
| T-0021-041 | Regression | Roz's existing `<workflow>` tag content (from `## Investigation Mode` through `## Code QA Mode`) is byte-identical to pre-edit content |
| T-0021-042 | Boundary | `.claude/agents/roz.md` and `source/shared/agents/roz.md` Brain Access sections are identical |
| T-0021-103 | Error | `.claude/agents/roz.md` YAML frontmatter is valid YAML parseable by a standard YAML parser |

### Step 2d Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-043 | Happy | `.claude/agents/agatha.md` YAML frontmatter contains `mcpServers` key with value including `atelier-brain` |
| T-0021-044 | Happy | `source/shared/agents/agatha.md` YAML frontmatter contains `mcpServers` key with value including `atelier-brain` |
| T-0021-045 | Happy | `.claude/agents/agatha.md` contains a `<protocol id="brain-access">` section |
| T-0021-046 | Happy | Agatha's Brain Access section mentions `thought_type: 'decision'` for doc structure decisions |
| T-0021-047 | Happy | Agatha's Brain Access section mentions `source_agent: 'agatha'` |
| T-0021-048 | Failure | Agatha's Brain Access section contains the exact string "When brain is unavailable" followed by a skip/no-op instruction |
| T-0021-049 | Regression | Agatha's `disallowedTools` frontmatter field is unchanged (Agent, NotebookEdit) |
| T-0021-050 | Regression | Agatha's existing `<workflow>` tag content (from `## Documentation Process` through `## Audience Types`) is byte-identical to pre-edit content |
| T-0021-051 | Boundary | `.claude/agents/agatha.md` and `source/shared/agents/agatha.md` Brain Access sections are identical |
| T-0021-104 | Error | `.claude/agents/agatha.md` YAML frontmatter is valid YAML parseable by a standard YAML parser |

### Step 3 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-052 | Happy | `warn-brain-capture.sh` receives JSON with `agent_type: "cal"` and `last_assistant_message` containing "agent_capture", exits 0 with no stderr output |
| T-0021-053 | Happy | `warn-brain-capture.sh` receives JSON with `agent_type: "colby"` and `last_assistant_message` NOT containing "agent_capture", writes warning to stderr mentioning "colby" and "brain capture", exits 0 |
| T-0021-054 | Boundary | `warn-brain-capture.sh` receives JSON with `agent_type: "ellis"` (not a brain-access agent), exits 0 with no output regardless of message content |
| T-0021-055 | Boundary | `warn-brain-capture.sh` receives JSON with `agent_type: "poirot"`, exits 0 with no output |
| T-0021-056 | Boundary | `warn-brain-capture.sh` receives JSON with `agent_type: "roz"` and `last_assistant_message` containing "agent_capture" within a code block, exits 0 with no stderr (presence of string is sufficient, context does not matter) |
| T-0021-057 | Error | `warn-brain-capture.sh` receives JSON with missing `last_assistant_message`, exits 0 with warning about missing output on stderr |
| T-0021-058 | Error | `warn-brain-capture.sh` runs without `jq`, exits 0 with no output |
| T-0021-059 | Regression | `.claude/settings.json` SubagentStop array contains `warn-brain-capture.sh` with correct `"if"` condition matching cal, colby, roz, agatha |
| T-0021-060 | Regression | `warn-brain-capture.sh` exits 0 in ALL code paths (never exits 2, never blocks) |
| T-0021-061 | Regression | `source/claude/hooks/warn-brain-capture.sh` exists and is identical to `.claude/hooks/warn-brain-capture.sh` |
| T-0021-106 | Failure | `warn-brain-capture.sh` receives JSON with `agent_type: "roz"` and `last_assistant_message` NOT containing "agent_capture", writes warning to stderr mentioning "roz", exits 0 |
| T-0021-107 | Failure | `warn-brain-capture.sh` receives JSON with `agent_type: "agatha"` and `last_assistant_message` NOT containing "agent_capture", writes warning to stderr mentioning "agatha", exits 0 |
| T-0021-110 | Error | `warn-brain-capture.sh` receives completely empty stdin (zero bytes), exits 0 with no output |
| T-0021-116 | Regression | `source/claude/hooks/warn-brain-capture.sh` is executable (file mode includes execute bit, verified by `test -x`) |

### Step 4 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-062 | Happy | `.claude/references/agent-preamble.md` step 4 contains the string "mcpServers: atelier-brain" or "mcpServers" to distinguish agents with brain access from those without |
| T-0021-063 | Happy | `source/references/agent-preamble.md` matches `.claude/references/agent-preamble.md` |
| T-0021-064 | Regression | agent-preamble.md still contains steps 1-5 in order (DoR, upstream, retro, brain, DoD) |
| T-0021-065 | Regression | `.claude/agents/ellis.md` output section does NOT contain the exact string "Eva uses these to capture knowledge to the brain" (replaced with updated phrasing) |
| T-0021-066 | Boundary | `.claude/references/invocation-templates.md` contains text within the first 60 lines referencing both "brain-context" (prefetch/read) and "agent_capture" or "capture directly" (write) as distinct operations |
| T-0021-067 | Regression | `source/references/invocation-templates.md` matches `.claude/references/invocation-templates.md` for the modified sections |
| T-0021-118 | Failure | `.claude/references/agent-preamble.md` step 4 does NOT contain the phrase "they do not call agent_search themselves" as the sole brain instruction (old Eva-only framing must be updated) |
| T-0021-119 | Failure | `.claude/agents/ellis.md` output section still contains the word "brain" (the line was updated, not deleted) |

### Step 5a Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-068 | Happy | `.claude/rules/agent-system.md` Brain Configuration section references `mcpServers: atelier-brain` as mechanism for agent captures |
| T-0021-069 | Happy | `.claude/rules/agent-system.md` Brain Configuration section names the four brain-access agents (Cal, Colby, Roz, Agatha) |
| T-0021-070 | Happy | `.claude/rules/agent-system.md` Brain Configuration section references `prompt-brain-prefetch.sh` and `prompt-brain-capture.sh` by name |
| T-0021-071 | Happy | `.claude/rules/pipeline-orchestration.md` Brain Access heading does NOT contain "MANDATORY" |
| T-0021-072 | Happy | `.claude/rules/pipeline-orchestration.md` Brain Access section contains "best-effort" for Eva's cross-cutting captures |
| T-0021-073 | Happy | `.claude/rules/pipeline-orchestration.md` does NOT contain the "Verification (spot-check)" subsection |
| T-0021-074 | Happy | `.claude/rules/pipeline-orchestration.md` Brain Access section references agent personas for domain-specific capture gates |
| T-0021-075 | Regression | `.claude/rules/agent-system.md` Shared Agent Behaviors section still lists brain context consumption as a shared behavior |
| T-0021-076 | Regression | `.claude/rules/pipeline-orchestration.md` Seed Capture and /devops Capture Gates subsections are preserved |
| T-0021-077 | Regression | `.claude/rules/pipeline-orchestration.md` Telemetry Tier 1 section is preserved (in-memory accumulator structure unchanged) |
| T-0021-078 | Boundary | `source/rules/agent-system.md` matches `.claude/rules/agent-system.md` for all modified sections |
| T-0021-079 | Boundary | `source/rules/pipeline-orchestration.md` matches `.claude/rules/pipeline-orchestration.md` for all modified sections |
| T-0021-080 | Regression | `.claude/rules/pipeline-orchestration.md` Telemetry Capture heading does NOT contain "MANDATORY" |
| T-0021-111 | Failure | `.claude/rules/pipeline-orchestration.md` still contains the heading "Seed Capture" (not accidentally deleted during prose cleanup) |
| T-0021-112 | Failure | `.claude/rules/pipeline-orchestration.md` still contains the heading "/devops Capture Gates" or "devops Capture Gates" (not accidentally deleted during prose cleanup) |

### Step 5b Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-081 | Happy | `.claude/rules/default-persona.md` Context Eviction retention list includes "brain capture protocol awareness" or equivalent |
| T-0021-082 | Happy | `.claude/rules/default-persona.md` Context Eviction list does NOT contain "Telemetry trend computation logic" as an eviction target |
| T-0021-083 | Happy | `.claude/rules/default-persona.md` Brain Access section references hooks and agent frontmatter |
| T-0021-084 | Happy | `.claude/rules/pipeline-models.md` Brain Integration subsection contains "best-effort" qualifier |
| T-0021-085 | Happy | `.claude/references/pipeline-operations.md` Brain prefetch protocol references `prompt-brain-prefetch.sh` |
| T-0021-086 | Happy | `.claude/references/pipeline-operations.md` Brain prefetch protocol references hybrid model (agent self-capture) |
| T-0021-087 | Regression | `.claude/rules/default-persona.md` boot sequence steps 4-5 (brain health check, context retrieval) are preserved |
| T-0021-088 | Regression | `.claude/rules/pipeline-models.md` model tables are unmodified |
| T-0021-089 | Boundary | `source/rules/default-persona.md` matches `.claude/rules/default-persona.md` for modified sections |
| T-0021-090 | Boundary | `source/rules/pipeline-models.md` matches `.claude/rules/pipeline-models.md` for modified sections |
| T-0021-091 | Boundary | `source/references/pipeline-operations.md` matches `.claude/references/pipeline-operations.md` for modified sections |
| T-0021-113 | Failure | `.claude/rules/default-persona.md` boot sequence steps 4 and 5 still contain the tool references `atelier_stats` and `agent_search` (these are operational boot steps, not dead prose) |

### Step 6 Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-092 | Happy | `post-compact-reinject.sh` outputs a brain protocol reminder section after pipeline-state.md and context-brief.md content |
| T-0021-093 | Happy | Brain protocol reminder mentions three mechanisms: prompt hooks, agent captures (cal/colby/roz/agatha), Eva cross-cutting (best-effort) |
| T-0021-094 | Boundary | Brain protocol reminder is less than 10 lines |
| T-0021-095 | Regression | `post-compact-reinject.sh` still outputs pipeline-state.md and context-brief.md content before the brain reminder |
| T-0021-096 | Regression | `post-compact-reinject.sh` exits 0 in all code paths |
| T-0021-097 | Error | `post-compact-reinject.sh` handles missing pipeline-state.md gracefully (exits 0, no brain reminder output) |
| T-0021-098 | Boundary | `source/claude/hooks/post-compact-reinject.sh` matches `.claude/hooks/post-compact-reinject.sh` |
| T-0021-114 | Failure | `post-compact-reinject.sh` does NOT output brain protocol reminder when `pipeline-state.md` does not exist (brain reminder is contextual to active pipeline state; if no state file, no reminder) |

### Cross-Step Tests

| ID | Category | Description |
|----|----------|-------------|
| T-0021-108 | Boundary | After all steps complete, none of the read-only agent files (`.claude/agents/robert.md`, `.claude/agents/sable.md`, `.claude/agents/investigator.md`, `.claude/agents/distillator.md`, `.claude/agents/darwin.md`, `.claude/agents/deps.md`, `.claude/agents/sentinel.md`, `.claude/agents/ellis.md`) contain `mcpServers` in their YAML frontmatter |

### Step Telemetry

| Step | Telemetry | Trigger | Absence Means |
|------|-----------|---------|---------------|
| 1 | stderr from `prompt-brain-prefetch.sh` or `prompt-brain-capture.sh` if they error | Hook execution on Agent invocation/return | Hooks not registered or settings.json misconfigured |
| 2a-2d | Brain thought with `source_agent: 'cal'` (or colby/roz/agatha) appearing in `atelier_stats` output | Agent completes work with brain available | Agent did not call `agent_capture` despite having access |
| 3 | WARNING line in stderr from `warn-brain-capture.sh` | Agent returns without `agent_capture` in output | Either agent called `agent_capture` (good) or hook not firing (bad -- check settings.json) |
| 4 | (Structural -- no runtime telemetry) | N/A | N/A |
| 5a-5b | (Structural -- no runtime telemetry) | N/A | N/A |
| 6 | Brain protocol reminder appearing in post-compaction context | Compaction occurs during pipeline session | Hook not running or brain reminder section removed |

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `prompt-brain-prefetch.sh` (stdout) | Plain text advisory: "Brain prefetch reminder: call agent_search for {feature area}..." | Eva's context window (injected by Claude Code prompt hook runtime) | Step 1 |
| `prompt-brain-capture.sh` (stdout) | Plain text advisory: "Brain capture reminder: {agent} just returned..." | Eva's context window (injected by Claude Code prompt hook runtime) | Step 1 |
| `warn-brain-capture.sh` (stderr) | Warning text: "WARNING: {agent} output missing agent_capture call..." | Pipeline operator (visible in stderr log) | Step 3 |
| `post-compact-reinject.sh` (stdout, brain section) | Plain text: "## Brain Protocol Reminder\n..." | Eva's context window (injected by Claude Code PostCompact runtime) | Step 6 |
| `.claude/settings.json` (final shape after Steps 1+3) | JSON with PreToolUse[Agent] array containing `prompt-brain-prefetch.sh` entry (`"type": "prompt"`), SubagentStop array containing `prompt-brain-capture.sh` (`"type": "prompt"`) and `warn-brain-capture.sh` (`"type": "command"`, `"if"` condition for cal/colby/roz/agatha) | Claude Code hook runtime (reads at session start) | Steps 1, 3 |
| Cal `agent_capture` call | `{ thought_type: 'decision', source_agent: 'cal', source_phase: 'design', ... }` | Brain MCP server -> future `agent_search` queries | Step 2a |
| Colby `agent_capture` call | `{ thought_type: 'insight', source_agent: 'colby', source_phase: 'build', ... }` | Brain MCP server -> future `agent_search` queries | Step 2b |
| Roz `agent_capture` call | `{ thought_type: 'pattern', source_agent: 'roz', source_phase: 'qa', ... }` | Brain MCP server -> future `agent_search` queries | Step 2c |
| Agatha `agent_capture` call | `{ thought_type: 'decision', source_agent: 'agatha', source_phase: 'docs', ... }` | Brain MCP server -> future `agent_search` queries | Step 2d |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `prompt-brain-prefetch.sh` | Advisory text | Eva context (Claude Code runtime) | 1 |
| `prompt-brain-capture.sh` | Advisory text | Eva context (Claude Code runtime) | 1 |
| Cal `mcpServers: atelier-brain` | MCP tool access | Cal Brain Access protocol | 2a |
| Colby `mcpServers: atelier-brain` | MCP tool access | Colby Brain Access protocol | 2b |
| Roz `mcpServers: atelier-brain` | MCP tool access | Roz Brain Access protocol | 2c |
| Agatha `mcpServers: atelier-brain` | MCP tool access | Agatha Brain Access protocol | 2d |
| `warn-brain-capture.sh` | stderr warning | Pipeline operator / session log | 3 |
| Updated agent-preamble.md | Documentation | All agents (loaded at work unit start) | 4 |
| Updated rules (agent-system, pipeline-orchestration) | Documentation | Eva (always-loaded) | 5a |
| Updated rules (default-persona, pipeline-models, pipeline-operations) | Documentation | Eva (loaded at pipeline activation) | 5b |
| `post-compact-reinject.sh` brain reminder | Reinject text | Eva context (PostCompact) | 6 |

No orphan producers exist. All producers have consumers in the same or earlier step.

## Blast Radius

### Files Created (4)
| File | Step |
|------|------|
| `.claude/hooks/prompt-brain-prefetch.sh` | 1 |
| `.claude/hooks/prompt-brain-capture.sh` | 1 |
| `source/claude/hooks/prompt-brain-prefetch.sh` | 1 |
| `source/claude/hooks/prompt-brain-capture.sh` | 1 |

### Files Created (2)
| File | Step |
|------|------|
| `.claude/hooks/warn-brain-capture.sh` | 3 |
| `source/claude/hooks/warn-brain-capture.sh` | 3 |

### Files Modified
| File | Steps | What changes |
|------|-------|-------------|
| `.claude/settings.json` | 1, 3 | New hook registrations |
| `.claude/agents/cal.md` | 2a | Frontmatter + Brain Access section |
| `.claude/agents/colby.md` | 2b | Frontmatter + Brain Access section |
| `.claude/agents/roz.md` | 2c | Frontmatter + Brain Access section |
| `.claude/agents/agatha.md` | 2d | Frontmatter + Brain Access section |
| `.claude/agents/ellis.md` | 4 | Output section brain line |
| `.claude/references/agent-preamble.md` | 4 | Step 4 brain context text |
| `.claude/references/invocation-templates.md` | 4 | Brain-context tag docs |
| `.claude/rules/agent-system.md` | 5a | Brain Config + Shared Behaviors |
| `.claude/rules/pipeline-orchestration.md` | 5a | Brain Access + Telemetry headings |
| `.claude/rules/default-persona.md` | 5b | Context Eviction + Brain Access pointer |
| `.claude/rules/pipeline-models.md` | 5b | Brain Integration subsection |
| `.claude/references/pipeline-operations.md` | 5b | Brain prefetch protocol |
| `.claude/hooks/post-compact-reinject.sh` | 6 | Brain reminder section |
| `source/shared/agents/cal.md` | 2a | Mirror |
| `source/shared/agents/colby.md` | 2b | Mirror |
| `source/shared/agents/roz.md` | 2c | Mirror |
| `source/shared/agents/agatha.md` | 2d | Mirror |
| `source/shared/agents/ellis.md` | 4 | Mirror |
| `source/references/agent-preamble.md` | 4 | Mirror |
| `source/references/invocation-templates.md` | 4 | Mirror |
| `source/rules/agent-system.md` | 5a | Mirror |
| `source/rules/pipeline-orchestration.md` | 5a | Mirror |
| `source/rules/default-persona.md` | 5b | Mirror |
| `source/rules/pipeline-models.md` | 5b | Mirror |
| `source/references/pipeline-operations.md` | 5b | Mirror |
| `source/claude/hooks/post-compact-reinject.sh` | 6 | Mirror |

### Integration Impact
- **Claude Code hook runtime:** Two new prompt hooks, one new command hook. No changes to existing hooks.
- **Cursor plugin:** `.cursor-plugin/` is not in scope. Cursor-specific sync happens at `/pipeline-setup` time (copies from `source/`).
- **Brain MCP server:** No changes. Agents call existing `agent_capture` and `agent_search` tools.
- **CI/CD:** No changes. Hooks are client-side only.
- **Existing hooks:** `enforce-paths.sh`, `enforce-sequencing.sh`, `enforce-git.sh`, `enforce-pipeline-activation.sh`, `log-agent-start.sh`, `log-agent-stop.sh`, `warn-dor-dod.sh`, `pre-compact.sh`, `log-stop-failure.sh` are unchanged.

### Consumers of Changed Files (grep verification)

| Changed entity | Consumers | Impact |
|----------------|-----------|--------|
| `.claude/settings.json` | Claude Code runtime (reads hook config at session start) | Additive -- new entries only |
| Agent frontmatter (`mcpServers` field) | Claude Code agent spawner (reads frontmatter to configure subagent MCP access) | Additive -- new field |
| `agent-preamble.md` | All agents (loaded at work unit start via persona `<required-actions>`) | Step 4 text change -- must be accurate |
| Brain Config in `agent-system.md` | Eva (always-loaded via `default-persona.md` reference) | Step 5a text change |
| Brain Access in `pipeline-orchestration.md` | Eva (loaded when pipeline is active, ALWAYS section) | Step 5a text change |
| Context Eviction in `default-persona.md` | Eva (loaded at session start) | Step 5b text change |
| `post-compact-reinject.sh` | Claude Code PostCompact runtime | Step 6 -- additive output section |

## Notes for Colby

1. **Prompt hook scripts must use `"type": "prompt"`, not `"type": "command"`.** The `prompt` type means Claude Code runs a single-turn evaluation of whether the hook's output is appropriate to inject into context. The `command` type runs the script directly and injects stdout. For advisory hooks, `prompt` is correct because Claude evaluates appropriateness per-turn. However, if Claude Code's `prompt` type adds latency that proves problematic, Colby may use `command` type as a fallback since the scripts already output advisory text -- the only difference is that `command` injects unconditionally while `prompt` injects conditionally.

2. **`mcpServers` frontmatter format:** Based on brain context confirming that project-owned agents in `.claude/agents/` support `mcpServers`, the format is:
   ```yaml
   mcpServers:
     - atelier-brain
   ```
   This goes in the YAML frontmatter block (between `---` delimiters), alongside `name`, `model`, `tools`, etc. The value `atelier-brain` must match the MCP server name as configured in the project's MCP settings.

3. **Brain Access section placement in agent personas:** Place the `<protocol id="brain-access">` section after the existing `<workflow>` section and before `<examples>`. This follows the XML prompt schema convention where protocols define mechanical procedures, distinct from workflow steps. The section should be short (15-25 lines) and specific.

4. **`warn-brain-capture.sh` checks for the string `agent_capture` in `last_assistant_message`.** This is a crude check -- it will pass if the agent merely discusses `agent_capture` without calling it. This is acceptable because: (a) the warn hook is a safety net, not an enforcement gate, (b) a more sophisticated check would require parsing the agent's tool call history, which is not available in the SubagentStop hook input, and (c) even a false negative (hook passes when agent discussed but did not call) is still better than no check at all.

5. **Source/ sync is mandatory.** Every `.claude/` change must be mirrored in `source/`. The source/ files are templates used by `/pipeline-setup` to install into target projects. If source/ is out of sync, new installations will get the old behavior.

6. **`post-compact-reinject.sh` brain reminder must be concise.** The reminder is injected into Eva's context after every compaction. It must be short enough to not waste context window space but specific enough to trigger brain protocol awareness. Target: 5-7 lines. Do not duplicate the full Brain Access protocol -- just name the three mechanisms and the four brain-access agents.

7. **Dead prose cleanup requires careful editing.** Steps 5a and 5b modify dense rules text. Do not remove entire sections -- update them in place. The goal is honesty (marking behavioral instructions as best-effort, adding mechanical enforcement pointers) not deletion. The Seed Capture, /devops Capture Gates, and Telemetry Tier structure must survive intact.

8. **Brain context from this ADR's task:** The brain confirms that `.claude/agents/` (project-owned) is the correct location for `mcpServers` frontmatter. Plugin-native agents (`agents/` inside a plugin directory) silently ignore `mcpServers`. All four target agents are already in `.claude/agents/` -- no file moves needed.

## DoD: Verification

| # | Requirement | Status | Step | Notes |
|---|-------------|--------|------|-------|
| R1 | SubagentStop prompt hook | Covered | 1 | `prompt-brain-capture.sh` |
| R2 | PreToolUse(Agent) prompt hook | Covered | 1 | `prompt-brain-prefetch.sh` |
| R3 | mcpServers frontmatter for 4 agents | Covered | 2a, 2b, 2c, 2d | Cal, Colby, Roz, Agatha |
| R4 | Brain Access workflow sections | Covered | 2a, 2b, 2c, 2d | Per-agent capture gates |
| R5 | Remove dead behavioral brain prose | Covered | 5a, 5b | Rules cleanup |
| R6 | Replace with pointers to mechanical systems | Covered | 5a, 5b | References hooks and frontmatter |
| R7 | Fix context eviction | Covered | 5b, 6 | Eviction list updated + PostCompact reminder |
| R8 | Keep Eva's cross-cutting captures as best-effort | Covered | 5a | Marked best-effort in Brain Access protocol |
| R9 | Read-only agents do NOT get mcpServers | Covered | 2a-2d | Only Cal, Colby, Roz, Agatha modified |
| R10 | Prompt hooks use `prompt` type | Covered | 1 | `"type": "prompt"` in settings.json |
| R11 | source/ and .claude/ in sync | Covered | All steps | Mirror changes in every step |
| R12 | warn-brain-capture.sh SubagentStop hook | Covered | 3 | Parallel to warn-dor-dod.sh |
| R13 | PostCompact brain reminder | Covered | 6 | post-compact-reinject.sh update |
| R14 | Update agent-preamble.md | Covered | 4 | Hybrid model distinction |

**Architectural decisions not in the spec:**
- Chose `<protocol id="brain-access">` XML tag for agent persona Brain Access sections (consistent with existing protocol tags in pipeline-orchestration.md).
- `warn-brain-capture.sh` uses string-matching for `agent_capture` rather than tool call history parsing (tool call history not available in SubagentStop hook input).
- PostCompact brain reminder placed after pipeline-state.md and context-brief.md content (maintains existing output order, appends new content).

**Rejected alternatives with reasoning:**
- Full enforcement (Option C) rejected -- shell hooks cannot call MCP tools, so they cannot verify brain captures occurred. Blocking enforcement would deadlock.
- Prompt hooks alone (Alternative A above) rejected -- does not enable domain attribution.
- Agent brain access alone (Alternative B above) rejected -- does not address Eva's prefetch forgetting.

**Technical constraints discovered during design:**
- `.claude/settings.json` has no source/ template. It is project-specific. Only `.claude/` copy is modified.
- `mcpServers` frontmatter is only honored on project-owned agents in `.claude/agents/`, not plugin-native agents.
- SubagentStop hook input includes `last_assistant_message` but not tool call history. This limits `warn-brain-capture.sh` to string-matching.

---

ADR saved to `docs/architecture/active/ADR-0021-brain-wiring.md`. 9 steps (1, 2a-2d, 3, 4, 5a-5b, 6), 119 total tests. Test spec: Roz-approved.
