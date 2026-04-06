# ADR-0024: Mechanical Brain Writes -- SubagentStop Haiku Extractor

## DoR: Requirements Extracted

**Sources:** `docs/product/mechanical-brain-writes.md` (product spec), ADR-0023 Step 1a (R6 supersession), `.claude/references/retro-lessons.md` (lesson #003), `.claude/settings.json` (hook structure), `source/claude/hooks/warn-brain-capture.sh`, `source/claude/hooks/prompt-brain-capture.sh`, `source/shared/references/agent-preamble.md`, `source/shared/agents/{cal,colby,roz,agatha}.md`, `source/shared/rules/{agent-system,pipeline-orchestration,default-persona}.md`, `source/shared/references/pipeline-operations.md`, `source/shared/references/invocation-templates.md`, `tests/hooks/test_warn_brain_capture.py`, `tests/hooks/test_prompt_brain_capture.py`, `tests/hooks/test_brain_wiring.py`

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Replace `warn-brain-capture.sh` with a `"type": "agent"` SubagentStop hook launching a Haiku extractor | Spec AC-1 through AC-4 | spec:line 98-101 |
| R2 | Haiku extractor reads `last_assistant_message`, extracts structured content, calls `agent_capture` | Spec req 2 | spec:line 71-76 |
| R3 | Brain server handles dedup/conflict -- extractor does not | Spec req 3 | spec:line 3 |
| R4 | Zero Eva behavioral compliance required post-ship (for agent-domain captures) | Spec req 4 | spec:line 9 |
| R5 | Remove Brain Access sections from Cal, Colby, Roz, Agatha personas in `source/shared/agents/` | Spec req 5, AC-13 | spec:line 125-126 |
| R6 | Remove Brain Capture Protocol section from `source/shared/references/agent-preamble.md` | Spec req 6, AC-15 | spec:line 127 |
| R7 | Remove `prompt-brain-capture.sh` from source and settings.json | Spec req 7, AC-12 | spec:line 124 |
| R8 | Remove `warn-brain-capture.sh` from source and settings.json | Spec req 8, AC-11 | spec:line 123 |
| R9 | Extractor scoped to cal/colby/roz/agatha via `if:` condition; extractor agent_type excluded from condition (no loop) | Spec AC-5, AC-6 | spec:line 69, retro #003 |
| R10 | Graceful skip when brain unavailable | Spec AC-7 | spec:line 78, 104 |
| R11 | Correct source_agent/thought_type/source_phase mapping per parent agent | Spec AC-8, AC-9 | spec:line 72-76 |
| R12 | Clean exit on empty/null/no-extractable output | Spec AC-10 | spec:line 87-91 |
| R13 | Eva cross-cutting captures preserved unchanged | Spec AC-17 | spec:line 80, 132-135 |
| R14 | Update orchestration doc references to reflect mechanical capture | Spec AC-16 | spec:line 150-154 |
| R15 | All existing tests pass after cleanup | Spec AC-18 | spec:line 115 |
| R16 | Background hydration extension explicitly out of scope | Spec req 9 | spec:line 131 |
| R17 | No new MCP tools, no brain schema changes | Spec req 10 | spec:line 10 |
| R18 | Cursor hooks.json unchanged (no `"type": "agent"` support) | Spec risk table | spec:line 176 |

**Retro risks:**

- **Lesson #003 (Stop Hook Race Condition):** Directly relevant. The Haiku extractor is itself a subagent. When it completes, SubagentStop fires again. If the `if:` condition matches the extractor's `agent_type`, an infinite capture loop ensues. The design MUST exclude the extractor's agent_type from the hook condition. Additionally, per lesson #003, the extractor must exit 0 on all errors and never block the pipeline.

**Spec challenge:** The spec assumes `"type": "agent"` SubagentStop hooks receive `last_assistant_message` from the parent agent in the hook input. If the hook input schema for agent-type hooks differs from command-type hooks (e.g., the agent receives the hook input as a system prompt rather than stdin JSON), the extractor would not have access to the parent agent's output. **Mitigation:** The spec states this was validated during seed creation. The `"type": "agent"` hook receives the same SubagentStop input schema as command hooks. The agent's system prompt is the hook configuration, and the hook input (including `last_assistant_message`) is injected as context. If wrong, the extractor cannot extract -- graceful degradation is zero captures (not a pipeline blocker).

**SPOF:** The `if:` condition on the SubagentStop hook entry. This single condition string determines both the target agent set AND the loop prevention. **Failure mode:** If the condition is wrong (e.g., missing an agent, or failing to exclude the extractor), either captures are missed for an agent or an infinite loop is triggered. **Graceful degradation:** Missing agent = captures degrade to pre-feature behavior for that agent (zero mechanical captures, Eva cross-cutting captures still work). Loop = Claude Code's SubagentStop recursion limit terminates the loop (the extractor also checks `agent_type` and exits immediately if it does not match a target agent, providing a secondary defense).

**Anti-goals:**

1. **Anti-goal: Replacing Eva's cross-cutting captures.** Reason: Eva's captures (user decisions, phase transitions, cross-agent patterns, model-vs-outcome) are contextual observations that require pipeline-level awareness. A post-completion extractor cannot observe cross-agent convergence or user decisions made between agent invocations. Revisit: If the brain develops a correlation engine that can infer cross-cutting patterns from individual agent captures.

2. **Anti-goal: Extracting captures from non-brain-access agents (Ellis, Poirot, Robert, Sable, Sentinel, etc.).** Reason: These agents were never instrumented for brain writes. Their outputs lack the decision/pattern/lesson structure that makes extraction reliable. Adding them increases Haiku invocations per pipeline without proven value. Revisit: If brain retrieval quality shows gaps attributable to missing captures from these agents.

3. **Anti-goal: Making the extractor configurable (per-project thought_type mappings, custom extraction prompts).** Reason: The mapping from agent_type to source_agent/source_phase/thought_type is fixed at four entries. Configuration machinery for four static entries is over-engineering. The extractor prompt is the configuration. Revisit: If more than 6 agents become brain-access agents.

---

## Status

Proposed

**Supersedes:** ADR-0023 Step 1a (R6: "Extract shared brain capture protocol to agent-preamble.md"). ADR-0023 planned to consolidate brain capture behavioral instructions into a shared preamble section. This ADR eliminates the behavioral instructions entirely by replacing them with a mechanical SubagentStop hook. ADR-0023 remains active for all other requirements (R1-R5, R7-R15).

## Context

Brain writes from Cal, Colby, Roz, and Agatha are currently behavioral: each agent's persona file contains a "Brain Access" section instructing the agent to call `agent_capture` at defined gates. Two reinforcement hooks attempt to verify compliance after the fact:

1. **`prompt-brain-capture.sh`** (SubagentStop prompt hook, fires for cal/colby/roz): Outputs advisory text to Eva's context reminding her that the agent should have captured. Eva ignores this routinely.
2. **`warn-brain-capture.sh`** (SubagentStop command hook, fires for cal/colby/roz/agatha): Checks `last_assistant_message` for the string "agent_capture" and warns on stderr if absent. Exits 0 always -- cannot block or retry.

Neither mechanism is mechanical. Brain capture coverage is inconsistent and invisible. The behavioral instructions in agent personas (~4-6 lines each, plus ~28 lines in agent-preamble.md) consume context window without producing reliable captures.

### Current Hook Infrastructure (SubagentStop)

```json
"SubagentStop": [{
  "hooks": [
    { "type": "command", "command": "warn-dor-dod.sh", "if": "agent_type == 'colby' || agent_type == 'roz'" },
    { "type": "command", "command": "log-agent-stop.sh" },
    { "type": "prompt",  "prompt": "prompt-brain-capture.sh", "if": "agent_type == 'cal' || agent_type == 'colby' || agent_type == 'roz'" },
    { "type": "command", "command": "warn-brain-capture.sh", "if": "agent_type == 'cal' || agent_type == 'colby' || agent_type == 'roz' || agent_type == 'agatha'" }
  ]
}]
```

### Existing Tests Affected

Three test files cover the hooks being replaced or modified:

| File | Tests | Impact |
|------|-------|--------|
| `tests/hooks/test_warn_brain_capture.py` | 12 tests (T-0021-052 through T-0021-116) | **Delete entirely** -- the hook is being removed |
| `tests/hooks/test_prompt_brain_capture.py` | 10 tests (T-0021-002 through T-0021-109) | **Delete entirely** -- the hook is being removed |
| `tests/hooks/test_brain_wiring.py` | ~40 tests (structural validation) | **Modify** -- tests asserting `mcpServers: atelier-brain`, `<protocol id="brain-access">`, and persona Brain Access sections need updating |

### Blast Radius

| Category | Files | Direction |
|----------|-------|-----------|
| New hook script | 0 (agent hook = settings.json + agent persona, no shell script) | Create |
| New agent persona | `source/shared/agents/brain-extractor.md` | Create |
| New frontmatter overlay | `source/claude/agents/brain-extractor.frontmatter.yml` | Create |
| Hook scripts deleted | `source/claude/hooks/warn-brain-capture.sh`, `source/claude/hooks/prompt-brain-capture.sh` | Delete |
| Settings.json | `.claude/settings.json` (SubagentStop block update) | Modify |
| Agent personas (source) | `source/shared/agents/{cal,colby,roz,agatha}.md` | Modify (remove Brain Access sections) |
| Agent frontmatter (source) | `source/claude/agents/{cal,colby,roz,agatha}.frontmatter.yml` | Modify (remove `mcpServers: atelier-brain`) |
| Shared references | `source/shared/references/agent-preamble.md` | Modify (remove Brain Capture Protocol section) |
| Orchestration docs | `source/shared/rules/pipeline-orchestration.md` | Modify (update hybrid capture model language) |
| Agent system rules | `source/shared/rules/agent-system.md` | Modify (update brain config Writes bullet) |
| Default persona | `source/shared/rules/default-persona.md` | Modify (update Brain Access section) |
| Pipeline operations | `source/shared/references/pipeline-operations.md` | Modify (update brain prefetch references) |
| Invocation templates | `source/shared/references/invocation-templates.md` | Modify (update brain capture note) |
| Post-compact hook | `source/claude/hooks/post-compact-reinject.sh` | Modify (update Brain Protocol Reminder) |
| Tests deleted | `tests/hooks/test_warn_brain_capture.py`, `tests/hooks/test_prompt_brain_capture.py` | Delete |
| Tests modified | `tests/hooks/test_brain_wiring.py` | Modify (remove mcpServers/brain-access assertions) |
| Tests created | `tests/hooks/test_brain_extractor.py` | Create |
| Installed copies (.claude/) | Synced via /pipeline-setup post-pipeline | N/A (not directly edited) |

**Total: ~20 files touched.** Justified because the blast radius is wide but shallow -- most modifications are removing 2-6 lines from existing files. The actual new code is 1 agent persona (~50 lines) and 1 frontmatter overlay (~8 lines).

## Decision

Replace behavioral brain capture compliance with a mechanical SubagentStop `"type": "agent"` hook that launches a Haiku extractor agent. The extractor reads the parent agent's `last_assistant_message`, extracts structured knowledge (decisions, patterns, lessons), and calls `agent_capture` with the correct `source_agent`, `thought_type`, `source_phase`, and `importance` values. After the hook is verified working, remove all behavioral brain capture instructions from agent personas, the shared preamble, and orchestration docs. Remove the two superseded hooks (`prompt-brain-capture.sh`, `warn-brain-capture.sh`).

### Hook Type: `"type": "agent"` (not `"type": "command"` with CLI)

**Decision:** Use `"type": "agent"` SubagentStop hook.

**Tradeoff analysis:**

| Factor | `"type": "agent"` | `"type": "command"` (CLI) |
|--------|-------------------|---------------------------|
| Loop prevention | Requires `if:` condition excluding extractor's agent_type. Secondary defense: extractor checks agent_type internally and exits if not a target. | CLI process is external; does not trigger SubagentStop in parent context. Naturally loop-safe. |
| MCP access | Inherits project MCP servers (atelier-brain). Extractor calls `agent_capture` directly. | CLI invocation needs `--mcp-config` flag or project-dir resolution. MCP server startup adds latency per invocation. |
| Hook input | Receives SubagentStop input (including `last_assistant_message`) as context. Native. | Receives stdin JSON. Must parse and forward to CLI as prompt or file. Fragile serialization. |
| Latency | Runs in-process. Fast. | Spawns a new CLI process + MCP server connections. ~5-10s overhead per invocation. |
| Complexity | Agent persona + settings.json entry. No shell script. | Shell script + CLI invocation + stdin serialization + MCP config forwarding. ~40 lines of bash. |

**Choice rationale:** The `"type": "agent"` hook is architecturally cleaner (no shell script, no serialization, native MCP access) and faster (no CLI spawn overhead). The loop risk is the primary concern per retro lesson #003. It is mitigated by two independent mechanisms:

1. **Primary:** The `if:` condition on the SubagentStop hook entry explicitly lists only `cal`, `colby`, `roz`, `agatha`. The extractor agent's `agent_type` is `brain-extractor` -- it does not match the condition, so SubagentStop does not fire for it.
2. **Secondary:** The extractor's prompt includes an early-exit instruction: if `agent_type` is not one of `cal`, `colby`, `roz`, `agatha`, produce zero captures and exit.

### MCP Access for the Extractor

The extractor agent inherits the project's MCP server configuration (defined in `.mcp.json` at the project root). Since `atelier-brain` is configured as a project-level MCP server, the extractor has access to `agent_capture` without any additional wiring. This is the same mechanism that currently provides MCP access to Cal, Colby, Roz, and Agatha via `mcpServers: atelier-brain` in their frontmatter -- except the extractor gets it through project-level inheritance rather than per-agent frontmatter declaration.

After the extractor takes over brain writes, the `mcpServers: atelier-brain` frontmatter is **removed** from Cal, Colby, Roz, and Agatha. They no longer need direct brain access.

### Extractor Agent Design

The extractor agent (`brain-extractor`) is a minimal Haiku agent. Its persona defines:

- **Identity:** Brain knowledge extractor. No personality. Analytical.
- **Input contract:** Receives SubagentStop hook input containing `agent_type` and `last_assistant_message`.
- **Agent-to-metadata mapping:** `cal` -> `{source_agent: 'cal', source_phase: 'design'}`, `colby` -> `{source_agent: 'colby', source_phase: 'build'}`, `roz` -> `{source_agent: 'roz', source_phase: 'qa'}`, `agatha` -> `{source_agent: 'agatha', source_phase: 'docs'}`.
- **Extraction categories:** Decisions (`thought_type: 'decision'`), Patterns (`thought_type: 'pattern'`), Lessons (`thought_type: 'lesson'`).
- **Output contract:** Zero or more `agent_capture` calls. No file reads, no file writes, no agent invocations.
- **Error handling:** Brain unavailable -> zero captures, clean exit. `agent_capture` failure -> log to stderr, continue. Empty/null output -> zero captures, clean exit.
- **Importance values:** `decision` -> 0.7, `pattern` -> 0.5, `lesson` -> 0.6.

### Sequencing: Hook First, Cleanup Second

The implementation is sequenced into three waves to ensure no coverage gap:

1. **Wave 1:** Create extractor agent + hook wiring + new tests. At this point, both old hooks AND new hook coexist -- belt and suspenders.
2. **Wave 2:** Remove behavioral text from personas + preamble + orchestration docs. The mechanical hook is the sole capture mechanism.
3. **Wave 3:** Remove old hooks from settings.json + delete hook scripts + remove mcpServers frontmatter + update/delete tests.

This sequencing ensures that at no point during the build is brain capture coverage worse than before.

## Alternatives Considered

### Alternative 1: `"type": "command"` hook invoking `claude` CLI

Use a shell script that pipes the extraction prompt and `last_assistant_message` to `claude --model claude-haiku-4-5`. Naturally loop-safe (CLI is an external process). Rejected because: (a) CLI spawn + MCP server startup adds ~5-10s latency per invocation (4 agents x N invocations per pipeline), (b) serialization of `last_assistant_message` through stdin/arguments is fragile for large outputs, (c) MCP server access requires explicit forwarding, adding ~20 lines of bash.

### Alternative 2: ADR-0023 R6 approach (consolidate behavioral text to preamble)

Keep brain captures behavioral but consolidate the repeated instructions into agent-preamble.md. Reduces persona length but does not improve capture reliability. Rejected because: the core problem is behavioral compliance, not specification verbosity. Agents ignore brain capture instructions regardless of where those instructions live.

### Alternative 3: Post-pipeline batch extractor

Run a single Haiku extraction pass at pipeline end against all agent outputs stored on disk. Lower invocation count but: (a) requires storing all agent outputs to disk (currently not done), (b) loses per-agent granularity (agent_type context is stale at pipeline end), (c) adds a pipeline-end step that competes with telemetry, Agatha, and Ellis. Rejected for complexity and data availability reasons.

## Consequences

**Positive:**
- Brain write coverage becomes mechanical -- one extractor invocation per brain-access agent completion, guaranteed when brain is available
- Agent personas lose ~4-6 lines each of behavioral instructions they were already ignoring
- agent-preamble.md loses ~28 lines of shared brain capture protocol
- Two hooks (`prompt-brain-capture.sh`, `warn-brain-capture.sh`) and their ~80 lines of bash are deleted
- Eva's context window is cleaner -- no more advisory prompt injection after agent completions
- Token cost per extraction is minimal (Haiku)

**Negative:**
- Adds ~50 lines of agent persona (brain-extractor.md + frontmatter)
- Adds a SubagentStop invocation per brain-access agent completion (~500ms-1s latency)
- The `if:` condition is a single point of loop prevention -- must be correct
- Tests need significant rework (2 test files deleted, 1 modified, 1 created)

**Neutral:**
- Eva's cross-cutting captures are unchanged (behavioral, best-effort)
- Brain MCP server interface is unchanged (no new tools, no schema changes)
- Cursor is unaffected (no `"type": "agent"` hooks in Cursor)

---

## Implementation Plan

### Wave 1: Hook Infrastructure + Extractor Agent (3 steps)

#### Step 1a: Create brain-extractor agent persona

Create the Haiku extractor agent persona in `source/shared/agents/brain-extractor.md` and its Claude Code frontmatter overlay in `source/claude/agents/brain-extractor.frontmatter.yml`.

**Files to create:**
- `source/shared/agents/brain-extractor.md` (~40 lines)
- `source/claude/agents/brain-extractor.frontmatter.yml` (~8 lines)

**Acceptance criteria:**
- Persona defines identity, input contract (agent_type + last_assistant_message), extraction categories (decision/pattern/lesson), agent-to-metadata mapping, importance values, error handling
- Frontmatter specifies: `name: brain-extractor`, `model: haiku`, `maxTurns: 5`, `tools: Read, Bash` (read-only -- `agent_capture` is via MCP), `disallowedTools: Write, Edit, MultiEdit, NotebookEdit, Agent`
- Persona includes early-exit guard: if `agent_type` is not cal/colby/roz/agatha, produce zero captures
- No file I/O instructions -- extractor only calls `agent_capture`

**Complexity:** Low. ~50 lines total across 2 new files.
**After this step, I can:** inspect the extractor agent persona to verify the extraction contract before wiring it into hooks.

#### Step 1b: Wire SubagentStop agent hook in settings.json

Add the `"type": "agent"` hook entry to the SubagentStop block in `.claude/settings.json`. The old hooks (`prompt-brain-capture.sh`, `warn-brain-capture.sh`) remain in place during this step -- coexistence.

**Files to modify:**
- `.claude/settings.json` (add 1 hook entry to SubagentStop block, ~5 lines)

**Acceptance criteria:**
- New hook entry: `{ "type": "agent", "agent": "brain-extractor", "if": "agent_type == 'cal' || agent_type == 'colby' || agent_type == 'roz' || agent_type == 'agatha'" }`
- Old `prompt-brain-capture.sh` and `warn-brain-capture.sh` entries remain (coexistence)
- settings.json is valid JSON
- `brain-extractor` does NOT appear in the `if:` condition (loop prevention)

**Complexity:** Low. 5 lines added to 1 file.
**After this step, I can:** trigger a Cal/Colby/Roz/Agatha completion and observe both the old hooks AND the new extractor firing.

#### Step 1c: Create extractor test suite

Create `tests/hooks/test_brain_extractor.py` with structural validation tests for the new hook wiring and agent persona.

**Files to create:**
- `tests/hooks/test_brain_extractor.py` (~120 lines)

**Acceptance criteria:**
- Tests validate: settings.json has agent hook entry, `if:` condition includes exactly cal/colby/roz/agatha, `if:` condition excludes brain-extractor, agent persona exists with correct frontmatter (model: haiku, maxTurns, disallowedTools), persona contains agent-to-metadata mapping, persona contains early-exit guard
- Tests for graceful edge cases: empty message handling instruction present, brain unavailability instruction present
- All new tests pass

**Complexity:** Low. 1 new test file, ~120 lines.
**After this step, I can:** run `pytest tests/hooks/test_brain_extractor.py` and see all tests pass, confirming the hook wiring and persona are structurally correct.

### Wave 2: Behavioral Cleanup -- Personas and Preamble (2 steps)

#### Step 2a: Remove Brain Access sections from agent personas

Remove the "## Brain Access" section from Cal, Colby, Roz, and Agatha in `source/shared/agents/`. These sections contain behavioral instructions that the mechanical hook now replaces.

**Files to modify:**
- `source/shared/agents/cal.md` (remove ~4 lines: "## Brain Access" through source_phase line)
- `source/shared/agents/colby.md` (remove ~4 lines)
- `source/shared/agents/roz.md` (remove ~4 lines)
- `source/shared/agents/agatha.md` (remove ~4 lines: "## Brain Access" section + DoD `agent_capture` instruction line)

**Acceptance criteria:**
- `grep -r "## Brain Access" source/shared/agents/{cal,colby,roz,agatha}.md` returns no matches
- `grep -r "agent_capture" source/shared/agents/{cal,colby,roz,agatha}.md` returns no matches
- Agatha's DoD line "Capture reasoning via `agent_capture` per..." is removed
- No other sections in these files are modified (workflow, constraints, examples, identity all preserved)
- `grep "thought_type" source/shared/agents/{cal,colby,roz,agatha}.md` returns no matches (thought_type mapping moved to extractor)

**Complexity:** Low. 4 files, ~4 lines removed each.
**After this step, I can:** verify that agent personas no longer contain brain capture behavioral instructions.

#### Step 2b: Remove Brain Capture Protocol from agent-preamble.md

Remove the `<protocol id="brain-capture">` section from `source/shared/references/agent-preamble.md`. Update the brain context review step (step 4) to remove the capture reference.

**Files to modify:**
- `source/shared/references/agent-preamble.md` (remove lines 43-70: entire `<protocol id="brain-capture">` section; update step 4 text to remove capture-related language)

**Acceptance criteria:**
- `<protocol id="brain-capture">` section is gone from agent-preamble.md
- Step 4 ("Review brain context") no longer mentions "also capture domain-specific knowledge directly via `agent_capture`" -- it retains only the read/consumption instruction
- "How to Capture", "Capture Gates", "When Brain is Unavailable" subsections are gone
- The Ellis exemption line at the top still mentions brain capture exemption (or is simplified to just DoR/DoD exemption)
- No dangling references to "Brain Capture Protocol" in the file

**Complexity:** Low. 1 file, ~30 lines removed/rewritten.
**After this step, I can:** verify that the shared preamble no longer instructs agents to call `agent_capture`.

### Wave 3: Hook Removal + Frontmatter Cleanup + Doc Updates (4 steps)

#### Step 3a: Remove old hooks from settings.json and delete scripts

Remove `prompt-brain-capture.sh` and `warn-brain-capture.sh` entries from `.claude/settings.json` SubagentStop block. Delete the source hook scripts.

**Files to modify:**
- `.claude/settings.json` (remove 2 hook entries from SubagentStop block)

**Files to delete:**
- `source/claude/hooks/prompt-brain-capture.sh`
- `source/claude/hooks/warn-brain-capture.sh`

**Acceptance criteria:**
- settings.json SubagentStop block has no reference to `prompt-brain-capture.sh` or `warn-brain-capture.sh`
- settings.json is valid JSON
- `source/claude/hooks/prompt-brain-capture.sh` does not exist
- `source/claude/hooks/warn-brain-capture.sh` does not exist
- Remaining SubagentStop hooks (warn-dor-dod.sh, log-agent-stop.sh, brain-extractor agent hook) are intact

**Complexity:** Low. 1 file modified, 2 files deleted.
**After this step, I can:** confirm settings.json has exactly 3 SubagentStop hooks (warn-dor-dod, log-agent-stop, brain-extractor).

#### Step 3b: Remove mcpServers from agent frontmatter overlays

Remove `mcpServers: - atelier-brain` from Cal, Colby, Roz, and Agatha frontmatter overlays in `source/claude/agents/`.

**Files to modify:**
- `source/claude/agents/cal.frontmatter.yml` (remove last 2 lines: `mcpServers:` and `  - atelier-brain`)
- `source/claude/agents/colby.frontmatter.yml` (remove last 2 lines)
- `source/claude/agents/roz.frontmatter.yml` (remove last 2 lines)
- `source/claude/agents/agatha.frontmatter.yml` (remove last 2 lines)

**Acceptance criteria:**
- `grep -r "mcpServers" source/claude/agents/{cal,colby,roz,agatha}.frontmatter.yml` returns no matches
- `grep -r "atelier-brain" source/claude/agents/{cal,colby,roz,agatha}.frontmatter.yml` returns no matches
- All other frontmatter fields (name, model, tools, hooks, permissionMode, disallowedTools) are preserved
- brain-extractor.frontmatter.yml does NOT have mcpServers (it gets MCP via project-level inheritance)

**Complexity:** Low. 4 files, 2 lines removed each.
**After this step, I can:** verify that the four agents no longer declare brain MCP server access in their frontmatter.

#### Step 3c: Update orchestration docs and references

Update references to behavioral brain capture in orchestration docs, agent-system rules, default-persona rules, pipeline-operations, invocation-templates, and the post-compact-reinject hook.

**Files to modify:**
- `source/shared/rules/pipeline-orchestration.md` (~3 lines: update "Agent domain-specific captures are wired via `mcpServers: atelier-brain` frontmatter -- see agent personas (Cal, Colby, Roz, Agatha) for capture gates" to reference the mechanical SubagentStop hook instead; update "Hybrid Capture Model" paragraph to describe mechanical extraction; remove "see agent personas for capture gates" language)
- `source/shared/rules/agent-system.md` (~3 lines: update brain-config Writes bullet to reference mechanical hook instead of mcpServers; update shared-behaviors brain context bullet to remove "also capture directly" language)
- `source/shared/rules/default-persona.md` (~2 lines: update "Brain Access" section to reference mechanical hook instead of mcpServers + prompt-brain-capture.sh)
- `source/shared/references/pipeline-operations.md` (~3 lines: update brain-prefetch section to remove "Agents with `mcpServers: atelier-brain`...capture domain-specific knowledge directly" language)
- `source/shared/references/invocation-templates.md` (~1 line: update brain capture note in header)
- `source/claude/hooks/post-compact-reinject.sh` (~3 lines: update "Brain Protocol Reminder" section to reference mechanical hook instead of prompt-brain-capture.sh and mcpServers)

**Acceptance criteria:**
- `grep -r "see agent personas.*capture gates" source/shared/` returns no matches
- `grep -r "prompt-brain-capture.sh" source/` returns no matches (except git history)
- `grep -r "mcpServers: atelier-brain" source/shared/` returns no matches (frontmatter references gone)
- All references now describe the mechanical model: "SubagentStop hook launches a Haiku extractor that calls agent_capture"
- Eva's cross-cutting capture protocol in pipeline-orchestration.md is unchanged (Writes section, /devops gates, Seed Capture, Seed Surfacing all preserved)
- Seed Capture section still references `agent_capture` with `source_agent: '{current_agent}'` -- this is agent-initiated seed capture, distinct from domain capture, and remains behavioral by design

**Complexity:** Medium. 6 files, ~15 lines changed total, but requires careful surgical edits to avoid touching Eva's cross-cutting blocks.
**After this step, I can:** grep the entire source tree and confirm no dangling references to the old behavioral brain capture model.

#### Step 3d: Update and clean up test suite

Delete test files for removed hooks. Update `test_brain_wiring.py` to reflect the new architecture (no mcpServers in agent frontmatter, no brain-access protocol sections in personas, mechanical hook present).

**Files to delete:**
- `tests/hooks/test_warn_brain_capture.py`
- `tests/hooks/test_prompt_brain_capture.py`

**Files to modify:**
- `tests/hooks/test_brain_wiring.py` (remove/update: `test_frontmatter_has_mcp_servers`, `test_brain_access_section_exists`, `test_thought_type`, `test_source_agent`, `test_unavailable_clause`, `test_brain_access_identical`, all parametrized over BRAIN_AGENTS; remove `test_T_0021_115_cal_placement`; update `test_T_0021_070_brain_config_prompt_hooks` to assert absence of prompt-brain-capture.sh; update `test_T_0021_074_brain_access_references_personas` to check for mechanical hook reference; update `test_T_0021_108_non_brain_agents_no_mcpServers` to also assert brain-access agents no longer have mcpServers; add new tests: verify brain-extractor agent exists, verify settings.json has agent hook entry)

**Acceptance criteria:**
- `tests/hooks/test_warn_brain_capture.py` does not exist
- `tests/hooks/test_prompt_brain_capture.py` does not exist
- `test_brain_wiring.py` no longer asserts `mcpServers: atelier-brain` on cal/colby/roz/agatha
- `test_brain_wiring.py` no longer asserts `<protocol id="brain-access">` in agent personas
- `test_brain_wiring.py` includes new assertions for mechanical brain capture model
- `pytest tests/` passes (full suite green)
- `cd brain && node --test ../tests/brain/*.test.mjs` passes

**Complexity:** Medium. 2 files deleted, 1 file with significant structural changes (~40 test functions to review, ~15 to modify or remove, ~5 to add).
**After this step, I can:** run the full test suite and confirm everything is green.

---

## Test Specification

### Wave 1 Tests (new: `test_brain_extractor.py`)

| ID | Category | Description | How Roz Verifies | Pass Criteria |
|----|----------|-------------|-------------------|---------------|
| T-0024-001 | Hook wiring | settings.json SubagentStop has `"type": "agent"` entry for brain-extractor | Parse settings.json, find agent hook in SubagentStop | Hook entry exists with `"type": "agent"` and `"agent": "brain-extractor"` |
| T-0024-002 | Loop prevention | brain-extractor agent_type not in hook's `if:` condition | Parse `if:` string from settings.json agent hook | `brain-extractor` does not appear in condition; only cal/colby/roz/agatha appear |
| T-0024-003 | Loop prevention | Hook `if:` condition excludes non-target agents | Parse `if:` condition; verify no ellis/poirot/robert/sable/sentinel | Condition is exactly `agent_type == 'cal' || agent_type == 'colby' || agent_type == 'roz' || agent_type == 'agatha'` |
| T-0024-004 | Agent persona | brain-extractor.md exists in source/shared/agents/ | Check file existence | File exists |
| T-0024-005 | Agent persona | brain-extractor frontmatter specifies model: haiku | Parse frontmatter YAML | `model` field is `haiku` |
| T-0024-006 | Agent persona | brain-extractor frontmatter specifies maxTurns <= 5 | Parse frontmatter YAML | `maxTurns` <= 5 |
| T-0024-007 | Agent persona | brain-extractor has disallowedTools blocking Write/Edit/MultiEdit/NotebookEdit/Agent | Parse frontmatter YAML | All 5 tools in disallowedTools |
| T-0024-008 | Agent persona | brain-extractor persona contains agent-to-metadata mapping for all 4 agents | grep persona for cal/colby/roz/agatha mappings | All 4 agent_type -> source_agent/source_phase mappings present |
| T-0024-009 | Agent persona | brain-extractor persona contains early-exit guard for unknown agent_type | grep persona for guard instruction | Guard text present |
| T-0024-010 | Agent persona | brain-extractor persona contains brain unavailability instruction | grep persona for unavailable/skip | Instruction present |
| T-0024-011 | Agent persona | brain-extractor persona contains extraction categories (decision, pattern, lesson) | grep persona | All 3 thought_types mentioned |
| T-0024-012 | Agent persona | brain-extractor persona references importance values | grep persona for importance | Values 0.7, 0.5, 0.6 present |
| T-0024-013 | Coexistence | Old hooks still present in settings.json during Wave 1 | Parse settings.json | Both prompt-brain-capture.sh and warn-brain-capture.sh entries exist |
| T-0024-014 | Structural | settings.json is valid JSON after modification | json.loads() | No parse error |
| T-0024-015 | Structural | brain-extractor.frontmatter.yml exists | Check file existence | File exists in source/claude/agents/ |

### Wave 2 Tests (updates to existing, verified in full suite run)

| ID | Category | Description | How Roz Verifies | Pass Criteria |
|----|----------|-------------|-------------------|---------------|
| T-0024-016 | Persona cleanup | Cal source persona has no "## Brain Access" section | grep source/shared/agents/cal.md | No match |
| T-0024-017 | Persona cleanup | Colby source persona has no "## Brain Access" section | grep source/shared/agents/colby.md | No match |
| T-0024-018 | Persona cleanup | Roz source persona has no "## Brain Access" section | grep source/shared/agents/roz.md | No match |
| T-0024-019 | Persona cleanup | Agatha source persona has no "## Brain Access" section | grep source/shared/agents/agatha.md | No match |
| T-0024-020 | Persona cleanup | Agatha source persona has no `agent_capture` reference | grep source/shared/agents/agatha.md | No match |
| T-0024-021 | Persona cleanup | No agent persona in source/shared/agents/ references `thought_type` for brain capture | grep for thought_type in cal/colby/roz/agatha source personas | No matches |
| T-0024-022 | Preamble cleanup | agent-preamble.md has no `<protocol id="brain-capture">` section | grep source/shared/references/agent-preamble.md | No match |
| T-0024-023 | Preamble cleanup | agent-preamble.md step 4 does not mention "capture domain-specific knowledge directly" | grep for capture instruction in step 4 | No match for "capture" in step 4 context |
| T-0024-024 | Preamble cleanup | agent-preamble.md has no "How to Capture" subsection | grep | No match |
| T-0024-025 | Preamble cleanup | agent-preamble.md has no "Capture Gates" subsection | grep | No match |

### Wave 3 Tests (new assertions + deleted test files)

| ID | Category | Description | How Roz Verifies | Pass Criteria |
|----|----------|-------------|-------------------|---------------|
| T-0024-026 | Hook removal | settings.json SubagentStop has no prompt-brain-capture.sh reference | Parse settings.json | No match |
| T-0024-027 | Hook removal | settings.json SubagentStop has no warn-brain-capture.sh reference | Parse settings.json | No match |
| T-0024-028 | Hook removal | source/claude/hooks/prompt-brain-capture.sh does not exist | Check file existence | File not found |
| T-0024-029 | Hook removal | source/claude/hooks/warn-brain-capture.sh does not exist | Check file existence | File not found |
| T-0024-030 | Frontmatter cleanup | cal.frontmatter.yml has no mcpServers entry | grep source/claude/agents/cal.frontmatter.yml | No match for mcpServers |
| T-0024-031 | Frontmatter cleanup | colby.frontmatter.yml has no mcpServers entry | grep | No match |
| T-0024-032 | Frontmatter cleanup | roz.frontmatter.yml has no mcpServers entry | grep | No match |
| T-0024-033 | Frontmatter cleanup | agatha.frontmatter.yml has no mcpServers entry | grep | No match |
| T-0024-034 | Doc cleanup | pipeline-orchestration.md does not reference "see agent personas for capture gates" | grep source/shared/rules/ | No match |
| T-0024-035 | Doc cleanup | agent-system.md brain-config section does not reference prompt-brain-capture.sh | grep brain-config section | No match |
| T-0024-036 | Doc cleanup | agent-system.md shared-behaviors section does not reference "capture directly" for agents | grep shared-behaviors section | No match for "also capture directly" |
| T-0024-037 | Doc cleanup | default-persona.md does not reference prompt-brain-capture.sh | grep | No match |
| T-0024-038 | Doc cleanup | pipeline-operations.md brain-prefetch section does not reference agent domain-specific captures | grep | No match for "capture domain-specific knowledge directly" |
| T-0024-039 | Doc cleanup | invocation-templates.md does not reference "also capture via agent_capture" for agents | grep | No match |
| T-0024-040 | Doc cleanup | post-compact-reinject.sh Brain Protocol Reminder references mechanical hook | grep source/claude/hooks/post-compact-reinject.sh | Reference to SubagentStop extractor or mechanical capture present |
| T-0024-041 | Preservation | pipeline-orchestration.md still contains Eva cross-cutting Writes section | grep for "source_agent: 'eva'" | Multiple matches (user decisions, phase transitions, etc.) |
| T-0024-042 | Preservation | pipeline-orchestration.md still contains Seed Capture section | grep for "Seed Capture" | Match found |
| T-0024-043 | Preservation | pipeline-orchestration.md still contains /devops Capture Gates section | grep for "devops Capture Gates" | Match found |
| T-0024-044 | Test cleanup | test_warn_brain_capture.py does not exist | Check file existence | File not found |
| T-0024-045 | Test cleanup | test_prompt_brain_capture.py does not exist | Check file existence | File not found |
| T-0024-046 | Wiring | brain-extractor.frontmatter.yml does not have mcpServers | grep | No match |
| T-0024-047 | Regression | Non-brain agents (robert, sable, investigator, etc.) do not have mcpServers: atelier-brain | grep all non-brain agent frontmatter | No matches |
| T-0024-048 | Full suite | `pytest tests/` passes | Run command | Exit code 0 |
| T-0024-049 | Full suite | `cd brain && node --test ../tests/brain/*.test.mjs` passes | Run command | Exit code 0 |
| T-0024-050 | Structural | settings.json SubagentStop has exactly 3 hooks after cleanup | Parse settings.json | warn-dor-dod + log-agent-stop + brain-extractor = 3 |

**Test counts:** 15 Wave 1 + 10 Wave 2 + 25 Wave 3 = **50 tests total.** Failure tests (T-0024-002, -003, -026 through -029, -044, -045) outnumber happy-path tests.

---

## UX Coverage

No user-facing surfaces. This feature is entirely infrastructure. UX coverage section not applicable.

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| SubagentStop hook input | `{ agent_type: string, last_assistant_message: string }` | brain-extractor agent |
| brain-extractor agent | `agent_capture({ content, source_agent, thought_type, source_phase, importance })` | Brain MCP server (atelier-brain) |
| Brain MCP server | `{ id, created_at, ... }` (capture response) | brain-extractor (ignored -- fire-and-forget) |

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| brain-extractor.md persona | Extraction contract (categories, mapping, error handling) | settings.json `"type": "agent"` hook entry | Step 1a -> 1b |
| brain-extractor.frontmatter.yml | Agent metadata (model, tools, disallowedTools) | Claude Code agent loader | Step 1a |
| settings.json agent hook | `if:` condition + agent reference | SubagentStop event dispatcher | Step 1b |
| Step 2a persona cleanup | Removal of Brain Access sections | Step 3d test updates (assertions removed) | Step 2a -> 3d |
| Step 3a hook removal | Settings.json cleanup | Step 3d test file deletion | Step 3a -> 3d |
| Step 3b frontmatter removal | mcpServers cleanup | Step 3d wiring test updates | Step 3b -> 3d |

## Data Sensitivity

| Method/Endpoint | Classification |
|-----------------|---------------|
| `agent_capture` (brain MCP tool) | auth-only (project-scoped, requires MCP server auth) |
| SubagentStop hook input (`last_assistant_message`) | public-safe (agent output, no secrets by convention) |
| brain-extractor agent output | public-safe (extracted knowledge, no secrets) |

---

## Notes for Colby

### Pattern: Existing Hook Structures

The settings.json SubagentStop block currently has 4 hooks in a single matcher entry (no `matcher` field for SubagentStop -- it fires for all agent completions; `if:` conditions do the filtering). Follow this exact pattern when adding the agent hook. Reference: `.claude/settings.json` lines 57-81.

### Pattern: Agent Persona Structure

Follow the existing persona pattern in `source/shared/agents/`. Content body in shared, YAML frontmatter in `source/claude/agents/`. See `source/shared/agents/distillator.md` for the closest analog (Haiku model, minimal persona, analytical task). The extractor is even simpler -- it has no workflow modes, no examples, just an extraction contract.

### Pattern: Frontmatter Overlay Assembly

Colby creates `source/claude/agents/brain-extractor.frontmatter.yml` and `source/shared/agents/brain-extractor.md` separately. `/pipeline-setup` combines them into `.claude/agents/brain-extractor.md` with `---\n{frontmatter}\n---\n{content}`. During the build, also create the assembled `.claude/agents/brain-extractor.md` directly (the way the project eats its own cooking).

### Surgical Editing Warning (Step 3c)

Step 3c modifies 6 orchestration/reference files. The edits are all ~2-3 lines each, but the surrounding text MUST NOT be disrupted. In particular:

- `pipeline-orchestration.md`: The `<protocol id="brain-capture">` section contains BOTH the agent-domain text (to be updated) AND Eva's cross-cutting text (to be preserved). Do not remove the protocol section -- only update the opening paragraph and the "Hybrid Capture Model" subsection header paragraph. Everything after "Eva captures **cross-cutting concerns only**" stays verbatim.
- `agent-system.md`: The `<section id="brain-config">` has a "Writes:" bullet that currently says "Agents with `mcpServers: atelier-brain`...capture directly; Eva captures cross-cutting only; hook: `prompt-brain-capture.sh`." Replace with: "Domain-specific agent captures are handled mechanically by a SubagentStop hook (brain-extractor); Eva captures cross-cutting only."
- `default-persona.md`: The "## Brain Access" section has a single line. Replace the reference to hooks and mcpServers.
- `post-compact-reinject.sh`: Lines 57-59 reference prompt-brain-capture.sh and mcpServers. Update to reference the mechanical SubagentStop extractor.

### Test File Changes (Step 3d)

The `test_brain_wiring.py` file has parametrized tests over `BRAIN_AGENTS` that assert `mcpServers: atelier-brain` in frontmatter and `<protocol id="brain-access">` in persona body. These must all be removed. The `BRAIN_AGENTS` constant itself can be repurposed (still useful for listing the 4 agents the extractor targets) or removed.

Key tests to remove: `test_frontmatter_has_mcp_servers`, `test_brain_access_section_exists`, `test_thought_type`, `test_source_agent`, `test_unavailable_clause`, `test_brain_access_identical`, `test_T_0021_115_cal_placement`.

Key tests to update: `test_T_0021_070_brain_config_prompt_hooks` (assert absence, not presence), `test_T_0021_074_brain_access_references_personas` (assert mechanical hook reference), `test_T_0021_108_non_brain_agents_no_mcpServers` (add cal/colby/roz/agatha to the "no mcpServers" assertion list).

### Step 1b note: settings.json is installed, not source

`.claude/settings.json` is in the installed directory, not `source/`. This is one of the few files Colby edits outside `source/` -- settings.json is the project's hook configuration and is edited directly. No `/pipeline-setup` sync needed for this file.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Replace warn-brain-capture.sh with agent hook | Specified | Steps 1a, 1b, 3a |
| R2 | Haiku extractor reads output + calls agent_capture | Specified | Step 1a (persona contract) |
| R3 | Brain server handles dedup | Specified | No changes to brain server (OOS) |
| R4 | Zero behavioral compliance for agent-domain captures | Specified | Steps 2a, 2b (cleanup) |
| R5 | Remove Brain Access from 4 personas | Specified | Step 2a |
| R6 | Remove Brain Capture Protocol from preamble | Specified | Step 2b |
| R7 | Remove prompt-brain-capture.sh | Specified | Step 3a |
| R8 | Remove warn-brain-capture.sh | Specified | Step 3a |
| R9 | Loop prevention via if: condition | Specified | Steps 1b, 1c (T-0024-002, T-0024-003) |
| R10 | Graceful skip when brain unavailable | Specified | Step 1a (persona), T-0024-010 |
| R11 | Correct source_agent/thought_type/source_phase mapping | Specified | Step 1a (persona), T-0024-008 |
| R12 | Clean exit on empty/null output | Specified | Step 1a (persona), T-0024-009 |
| R13 | Eva cross-cutting captures preserved | Specified | Step 3c (surgical edit), T-0024-041 through T-0024-043 |
| R14 | Orchestration doc references updated | Specified | Step 3c |
| R15 | All existing tests pass | Specified | Step 3d, T-0024-048, T-0024-049 |
| R16 | Background hydration OOS | Deferred | Not in scope per spec |
| R17 | No new MCP tools, no schema changes | Specified | No brain/ changes |
| R18 | Cursor unchanged | Specified | No changes to source/cursor/ |

**Grep check:** TODO/FIXME/HACK in this ADR -> 0
**Template:** All sections filled -- no TBD, no placeholders
**Silent drops:** None. R16 explicitly deferred per spec.

---

ADR saved to `docs/architecture/ADR-0024-mechanical-brain-writes.md`. 9 steps, 50 total tests. Next: Roz reviews the test spec.
