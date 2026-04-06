## DoR: Requirements Extracted
**Source:** Brain seed (pre-validated product decision)

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Replace warn-brain-capture.sh (warning-only) with an `"type": "agent"` SubagentStop hook that launches Haiku | Seed: brain writes |
| 2 | Haiku extractor reads `last_assistant_message`, extracts structured content, calls `agent_capture` | Seed: brain writes |
| 3 | Brain server handles dedup and conflict detection — extractor does not need to | Seed: brain writes |
| 4 | Zero Eva behavioral compliance required after this feature ships | Seed: brain writes |
| 5 | Remove explicit brain capture behavioral instructions from Cal, Colby, Roz, Agatha persona files | Seed: cleanup scope |
| 6 | Remove brain capture behavioral sections from orchestration docs that describe agent-level capture gates | Seed: cleanup scope |
| 7 | Remove prompt-brain-capture.sh (advisory prompt hook) — superseded by mechanical hook | Derived |
| 8 | Remove warn-brain-capture.sh — superseded by mechanical hook | Derived |
| 9 | Background hydration extension (hydrate-telemetry.mjs) is explicitly out of scope | Seed: scope note |
| 10 | No new MCP tools, no brain schema changes | Seed: scope note |

**Retro risks:** Lesson #003 (stop hook race condition) — the new agent hook fires on every SubagentStop. It MUST be scoped to the four brain-access agents (cal, colby, roz, agatha) via `if:` condition. A Haiku agent that itself triggers SubagentStop could create a capture loop. The extractor agent must be filtered out of its own hook condition.

---

# Feature Spec: Mechanical Brain Writes
**Author:** Robert (Product Spec Producer) | **Date:** 2026-04-05
**Status:** Draft

## The Problem

Brain writes are currently behavioral: each agent's persona file contains an explicit "Brain Access" section instructing the agent to call `agent_capture` at defined gates. Two reinforcement hooks attempt to verify compliance after the fact — `prompt-brain-capture.sh` (a prompt advisory reminding Eva to verify captures) and `warn-brain-capture.sh` (a warning that prints to stderr when it detects no `agent_capture` string in the agent's output).

Neither mechanism is mechanical. Both are easily skipped:
- Agents routinely complete their work without calling `agent_capture`, passing the string check by coincidence (e.g., mentioning the tool name in prose) or failing the check with no consequence.
- `warn-brain-capture.sh` exits 0 always — it cannot block or retry.
- `prompt-brain-capture.sh` adds tokens to Eva's context but does not force any action.
- Brain capture sections in persona files add verbosity that competes with functional instructions for agent attention.

The result: brain write coverage is inconsistent and invisible. The brain accumulates knowledge opportunistically rather than reliably.

## Who Is This For

Pipeline maintainers and users running the atelier-pipeline with brain enabled. The feature is invisible at the user level — it improves the reliability of institutional memory capture without changing any user-facing workflow or output.

## Business Value

- **Reliability:** Every Cal, Colby, Roz, and Agatha completion triggers a brain write attempt — not dependent on the agent remembering to call `agent_capture`
- **Persona clarity:** Removing brain capture behavioral sections from four agent persona files reduces persona length and eliminates a class of agent instruction the agent was already frequently ignoring
- **Hook simplification:** Replacing two partial-enforcement hooks (prompt advisory + warning) with one mechanical hook reduces hook surface and eliminates dead-weight script maintenance
- **KPI:** Brain write call rate for the four target agents rises from opportunistic (current: unmeasured, known incomplete) to mechanical (post-feature: one extractor invocation per agent completion when brain is available)
- **Measurement:** Compare `agent_capture` calls in brain per pipeline run before and after. Track via `atelier_stats` thought counts across pipeline runs.

## User Stories

1. As a pipeline maintainer, I want brain writes to happen automatically when Cal, Colby, Roz, or Agatha completes, so I don't have to audit persona files to verify capture compliance
2. As a pipeline maintainer, I want agent persona files to contain only functional instructions, so new agents are easier to write and existing agents are easier to tune
3. As a pipeline user, I want the brain to accumulate structured knowledge from every pipeline run without any Eva behavioral overhead, so brain retrieval quality improves over time without token cost increases

## User Flow

No user-visible flow change. The feature is entirely infrastructure:

1. Cal, Colby, Roz, or Agatha completes (SubagentStop fires)
2. Mechanical hook launches Haiku extractor agent
3. Haiku reads `last_assistant_message` from hook input, extracts structured knowledge (decisions, patterns, lessons), calls `agent_capture` with appropriate `source_agent`, `thought_type`, `source_phase`, and `importance` values
4. Brain server receives the capture, handles embedding, dedup, and conflict detection
5. Eva's context is unaffected — no advisory prompt injected, no warning emitted

## Architecture Notes

**Hook type change.** The current `warn-brain-capture.sh` is a `"type": "command"` hook (a shell script that exits 0). The replacement is a `"type": "agent"` hook entry in `settings.json` SubagentStop configuration. The `"type": "agent"` hook launches a Haiku subagent synchronously (within the SubagentStop event) with the hook input as context.

**Scoping requirement.** The `if:` condition on the new hook must restrict invocation to the four brain-access agents: `agent_type == 'cal' || agent_type == 'colby' || agent_type == 'roz' || agent_type == 'agatha'`. The Haiku extractor itself must not match this condition (i.e., the extractor `agent_type` must not be one of these four strings) to prevent a capture loop.

**Extractor contract.** The Haiku extractor receives `last_assistant_message` and the `agent_type` from the hook input. It outputs zero or more `agent_capture` calls. It does not read files, does not write files, and does not invoke other agents. Its only output is brain captures. It extracts:
- Decisions (architectural choices, scope decisions, trade-off resolutions)
- Patterns (recurring implementation structures, QA findings worth generalizing)
- Lessons (things that went wrong and why, test failure root causes)

Content that does not fit these categories is not captured. The extractor uses the completion agent's `agent_type` as `source_agent` and maps it to the correct `source_phase` (cal → `design`, colby → `build`, roz → `qa`, agatha → `docs`).

**Brain unavailability.** When brain is unavailable (`brain_available: false` in pipeline state), the hook must skip gracefully. The extractor agent checks availability before calling `agent_capture` and exits cleanly with no captures when unavailable.

**Eva cross-cutting captures are unchanged.** Eva's own cross-cutting `agent_capture` calls (user decisions, phase transitions, cross-agent patterns, model-vs-outcome telemetry) are not replaced by this feature. They remain behavioral in `pipeline-orchestration.md`. This feature only replaces agent-domain captures that were previously expected of Cal, Colby, Roz, and Agatha themselves.

## Edge Cases and Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Haiku extractor finds no extractable content in output | Zero captures — extractor exits cleanly, no error |
| Brain is unavailable | Extractor skips all captures, exits cleanly |
| `agent_capture` call fails (DB error, network error) | Extractor logs failure to stderr, exits 0 (non-blocking per retro lesson #003) |
| Agent output is very long (>10K tokens) | Extractor summarizes; does not truncate arbitrarily |
| Agent output is empty or null | Extractor exits cleanly with zero captures |
| Extractor itself throws an unhandled error | Hook exits non-zero only if blocking is desired; per retro lesson #003, prefer exit 0 + stderr log |
| Two brain-access agents complete in rapid succession | Each triggers its own extractor invocation independently — no coordination needed |

## Acceptance Criteria

| # | Criterion | Measurement |
|---|-----------|-------------|
| AC-1 | When Cal completes, a Haiku extractor is invoked via SubagentStop `"type": "agent"` hook | Hook fires on Cal completion; agent invocation observed in hook log |
| AC-2 | When Colby completes, a Haiku extractor is invoked | Hook fires on Colby completion |
| AC-3 | When Roz completes, a Haiku extractor is invoked | Hook fires on Roz completion |
| AC-4 | When Agatha completes, a Haiku extractor is invoked | Hook fires on Agatha completion |
| AC-5 | The Haiku extractor does NOT fire for Eva, Ellis, Poirot, Robert, Sable, or Sentinel completions | Verified via `if:` condition scoping in settings.json |
| AC-6 | The Haiku extractor does NOT trigger a second extractor invocation when it itself completes (no capture loop) | Extractor `agent_type` is not one of the four target values |
| AC-7 | When brain is unavailable, the extractor completes without calling `agent_capture` and without erroring | Test with `brain_available: false` — zero captures, clean exit |
| AC-8 | When the extractor runs against a Cal output containing an architectural decision, `agent_capture` is called with `source_agent: 'cal'`, `thought_type: 'decision'`, `source_phase: 'design'` | Inspect brain captures after test pipeline run |
| AC-9 | When the extractor runs against a Roz output containing a QA finding pattern, `agent_capture` is called with `source_agent: 'roz'`, `thought_type: 'pattern'`, `source_phase: 'qa'` | Inspect brain captures after test pipeline run |
| AC-10 | When the extractor runs against a Colby output with no extractable content, zero captures are made and the hook exits cleanly | Verify via hook exit code and brain thought count |
| AC-11 | `warn-brain-capture.sh` is removed from source and from settings.json SubagentStop hooks | File deleted, settings.json updated |
| AC-12 | `prompt-brain-capture.sh` is removed from source and from settings.json SubagentStop hooks | File deleted, settings.json updated |
| AC-13 | Brain Access sections are removed from Cal, Colby, Roz, and Agatha persona files in source/shared/agents/ | Grep for "## Brain Access" in these four files returns no match |
| AC-14 | Brain capture behavioral instruction (`agent_capture` per `agent-preamble.md`) is removed from Agatha persona DoD section | Grep confirms removal |
| AC-15 | Brain Capture Protocol section is removed from source/shared/references/agent-preamble.md | Section gone; shared preamble no longer instructs agents to call `agent_capture` |
| AC-16 | References in orchestration docs to "see agent personas for capture gates" are updated to reflect mechanical capture | No dangling references to removed persona sections |
| AC-17 | Existing Eva cross-cutting `agent_capture` calls in pipeline-orchestration.md are preserved unchanged | Diff shows no removals from Eva brain capture block |
| AC-18 | All existing tests pass after cleanup | `pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs` green |

## Scope

**In scope:**
- New `"type": "agent"` SubagentStop hook targeting cal, colby, roz, agatha
- Haiku extractor agent persona/prompt (minimal — instructions + output contract)
- settings.json SubagentStop block update (add agent hook, remove prompt-brain-capture and warn-brain-capture entries)
- Deletion of `source/claude/hooks/warn-brain-capture.sh`
- Deletion of `source/claude/hooks/prompt-brain-capture.sh`
- Removal of "## Brain Access" sections from four agent personas in `source/shared/agents/`
- Removal of "Brain Capture Protocol" section from `source/shared/references/agent-preamble.md`
- Cleanup of dangling references in orchestration docs to agent-level behavioral capture gates

**Out of scope:**
- Background hydration extension (`brain/scripts/hydrate-telemetry.mjs`) — future pipeline
- New MCP tools or brain schema changes
- Eva cross-cutting capture behavior — unchanged
- CI Watch brain capture (`agent_capture` after CI resolution) — remains in pipeline-orchestration.md unchanged
- Seed capture behavior — remains in pipeline-orchestration.md unchanged
- Telemetry Tier 2/Tier 3 captures — these are Eva-owned, not agent-owned

## Files With Brain Capture Behavioral Sections to Remove

The following files carry behavioral brain capture instructions that become redundant once mechanical extraction is in place. The cleanup half of this feature removes these sections:

| File | What Is Removed |
|------|----------------|
| `source/shared/agents/cal.md` | "## Brain Access" section (4 lines: preamble reference + cal-specific thought_types + source_agent/phase) |
| `source/shared/agents/colby.md` | "## Brain Access" section (4 lines: preamble reference + colby-specific thought_types + source_agent/phase) |
| `source/shared/agents/roz.md` | "## Brain Access" section (4 lines: preamble reference + roz-specific thought_types + source_agent/phase) |
| `source/shared/agents/agatha.md` | "## Brain Access" section (2 lines) + DoD instruction: "Capture reasoning via `agent_capture` per..." |
| `source/shared/references/agent-preamble.md` | "## Brain Capture Protocol -- Shared" section and all subsections (How to Capture, Capture Gates, When Brain is Unavailable) |
| `source/claude/hooks/warn-brain-capture.sh` | Entire file deleted |
| `source/claude/hooks/prompt-brain-capture.sh` | Entire file deleted |
| `source/shared/rules/agent-system.md` | References to "see agent personas for capture gates" and the brain writes description in Brain Configuration section updated to reflect mechanical model |
| `source/shared/rules/pipeline-orchestration.md` | Brain capture protocol section updated: remove "see agent personas (Cal, Colby, Roz, Agatha) for capture gates" language; the mechanical hook is the new reference |
| `source/shared/references/pipeline-operations.md` | References to agent-level domain-specific capture gates updated or removed |

Note: Eva's cross-cutting capture protocol block in `pipeline-orchestration.md` (`<protocol id="brain-capture">`) is not removed — it remains authoritative for Eva's own captures. Only the language describing what Cal/Colby/Roz/Agatha must do themselves is cleaned up.

## Non-Functional Requirements

- **Token cost:** Haiku is the selected model — cost per extractor invocation is negligible relative to the parent agent invocation
- **Latency:** Extractor runs as part of SubagentStop; it adds latency to the hook event but does not block the next agent invocation. Acceptable for a synchronous hook.
- **Reliability:** Extractor failure must never block pipeline flow. Exit 0 on all non-critical errors.
- **Compatibility:** No changes to brain MCP tool interfaces. `agent_capture` call signature is unchanged.

## Dependencies

- `"type": "agent"` SubagentStop hook support in Claude Code (already supported per seed validation)
- Haiku model availability (already used in scout fan-out)
- Brain MCP server available at hook invocation time (graceful skip when unavailable)

## Risks and Open Questions

| Risk | Mitigation |
|------|------------|
| Haiku extractor trigger loop (extractor's own SubagentStop triggers another extractor) | Scope the `if:` condition to explicitly exclude the extractor's agent_type. Verify in AC-6. |
| Extractor extracts low-quality or hallucinated content from sparse outputs | Extractor uses structured prompting tied to DoR/DoD output templates; captures only when confidence is high. Brain dedup and conflict detection provide a second filter. |
| Removing behavioral instructions from personas breaks agents that were relying on preamble lookup | The preamble section being removed only described how agents should call `agent_capture`. Removing it has no effect on agent functional behavior — only on voluntary capture behavior that is now mechanically replaced. |
| settings.json dual-target (Claude Code and Cursor) sync | Cursor plugin hooks.json does not support `"type": "agent"` hooks. The agent hook is Claude Code only. The Cursor source overlay must not include this hook entry. |

## Timeline Estimate

Small pipeline. Two deliverables: (1) new hook wiring + Haiku extractor persona, ~30-50 lines; (2) cleanup pass across 10 files, removing or rewriting identified sections. No new tests needed beyond AC verification in a live pipeline run.

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Agent hook fires for cal, colby, roz, agatha | Specified | AC-1 through AC-4 |
| 2 | Agent hook does not fire for other agents | Specified | AC-5 |
| 3 | No capture loop | Specified | AC-6 |
| 4 | Graceful skip when brain unavailable | Specified | AC-7 |
| 5 | Correct source_agent/thought_type/source_phase extraction | Specified | AC-8, AC-9 |
| 6 | Clean exit on empty output | Specified | AC-10 |
| 7 | warn-brain-capture.sh deleted | Specified | AC-11 |
| 8 | prompt-brain-capture.sh deleted | Specified | AC-12 |
| 9 | Brain Access sections removed from four agent personas | Specified | AC-13, AC-14 |
| 10 | Brain Capture Protocol removed from agent-preamble.md | Specified | AC-15 |
| 11 | Orchestration doc references updated | Specified | AC-16 |
| 12 | Eva cross-cutting captures preserved | Specified | AC-17 |
| 13 | Existing test suite green | Specified | AC-18 |

**Grep check:** TODO/FIXME/HACK in spec -> 0
**Template:** All sections filled — no TBD, no placeholders
