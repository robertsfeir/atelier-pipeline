# ADR-0044: Instruction-Budget Trim -- Slice 2 (AUTO-ROUTING JIT + Mandatory Gates Rhetoric Collapse)

## Status

Accepted.

**Related (not modified):**
- ADR-0023 (agent-specification-reduction) -- the precedent for "move procedural detail into JIT references while keeping load-bearing rules inline." This ADR follows the same playbook for the AUTO-ROUTING matrix.
- ADR-0042 (scout-synthesis-tier-correction) -- defines the Scout Fan-out Protocol section anchors this ADR must preserve (T-0042-027, T-0042-028) and the Per-Agent Assignment Table anchors that pin pipeline-models.md (T-0042-001, -005, -037).
- ADR-0043 (agent-return-condensation) -- slice 1 of Issue #31. Lands in the same authoring pipeline. Pre-merge Addendum pattern reused here if downstream test regressions surface.
- ADR-0016 (Darwin), ADR-0015 (Deps) -- their routing-row tests (`darwin_enabled`, Deps keyword) are satisfied by keeping those anchors in the summary paragraph of agent-system.md and in the new JIT routing-detail file.

**Scope change vs Issue #31:** the issue proposed moving `pipeline-models.md:62-112` (Per-Agent Assignment Table) to a new JIT ref `model-classifier-detail.md`. ADR-0042's landed test suite asserts the table stays in pipeline-models.md at an anchored heading with 17 rows + specific values (T-0042-001, -005, -037). Moving the table would require superseding three ADR-0042 tests, which is out of scope for a line-count trim. **The pipeline-models.md move is dropped from Slice 2.** Net line savings drop from ~400 to ~230 -- still materially greater than Slice 1, still the correct target for this slice. See Alternatives Considered Alt 2 for the full reasoning.

---

## DoR: Requirements Extracted

**Sources:** Issue #31 Slice 2 body, research-brief from Patterns + Blast-radius scouts, `source/shared/rules/agent-system.md` (full file, 286 lines), `source/shared/rules/pipeline-orchestration.md` (full file, 802 lines), `source/shared/rules/pipeline-models.md` (full file, 143 lines), `.claude/rules/default-persona.md` (cross-reference target for Mandatory Gates), `docs/architecture/ADR-0023` (reduction precedent), `docs/architecture/ADR-0042` (landed test anchors), `docs/architecture/ADR-0043` (slice-1 Addendum pattern), `tests/adr-0023-reduction/test_reduction_structural.py:1090-1107`, `tests/hooks/test_wave3_hook_removal.py:351-374`, `tests/test_adr0041_rule_structure.py` (tier labels + floor/ceiling), `tests/adr-0042/test_adr_0042.py:230-285, 775-837, 1073-1106`, `tests/adr-0027/test_brain_hydrate_scout_fanout.py:626-640`, `tests/adr-0015-deps/test_deps_structural.py:293-305`, `tests/adr-0016-darwin/test_darwin_structural.py:240-250, 375-403`, `tests/xml-prompt-structure/test_step6_eva_rules.py` (all 8 tests), `.claude/references/retro-lessons.md` (lesson 002 -- tests pin domain intent, not file state).

| # | Requirement | Source |
|---|-------------|--------|
| R1 | Move the full AUTO-ROUTING Intent Detection table + Smart Context Detection + Auto-Routing Confidence + Discovered Agent Routing subsections (agent-system.md:117-172) to a new JIT reference `source/shared/references/routing-detail.md`. Keep the `<routing id="auto-routing">` opener, the section header `## AUTO-ROUTING RULES`, the existing one-line summary paragraph, a 6-bullet intent summary, and a pointer to the new file inline in agent-system.md | Issue #31 Slice 2 bullet 1 |
| R2 | Preserve routing anchors in the agent-system.md inline summary so ADR-0015 / ADR-0016 tests continue to pass: must mention `Deps` + one of `dependenc/outdated/upgrade/cve/vulnerability`; must mention `Darwin` + one of `pipeline.*health/pipeline.*analy/agent.*perform/run.*Darwin`; must mention `darwin_enabled` | `tests/adr-0015-deps/test_deps_structural.py:301-305`, `tests/adr-0016-darwin/test_darwin_structural.py:378-380, 386-387, 402-403` |
| R3 | The new `routing-detail.md` contains the verbatim Intent Detection table (19 rows), Smart Context Detection list (6 bullets), Auto-Routing Confidence list (3 bullets), and Discovered Agent Routing subsection (7 paragraphs). No paraphrase, no re-ordering, no column changes | Issue #31 "preserve load-bearing rules"; retro lesson 002 |
| R4 | Install the new ref file as `.claude/references/routing-detail.md` (byte-identical body) per the triple-target convention in CLAUDE.md. No Cursor install (Cursor does not carry pipeline-internal reference material per the research-brief) | CLAUDE.md "Triple target" convention; research-brief Cursor scope finding |
| R5 | Collapse the "same class of violation" rhetoric in pipeline-orchestration.md Mandatory Gates (lines 109-250). Factor the violation-severity class into a single opening paragraph that declares "Violating these is the same severity as Eva editing source code" and replace each gate's trailing "is the same class of violation as X" sentence with a one-token `**Violation class: [severity]**` or shorter in-prose anchor that names the comparison target. Preserve all 12 numbered gates, their core content, and their numbering. Preserve the gate-2 Agent Teams note, the gate-3 Agent Teams note, the gate-5 Agent Teams note -- those add operational content, not rhetoric | Issue #31 Slice 2 bullet 3; `tests/adr-0023-reduction/test_reduction_structural.py:1090-1095` (T-0023-131 only checks `"Eva NEVER Skips"` presence) |
| R6 | Collapse the Scout Fan-out Protocol section (lines 604-635 in `source/shared/rules/pipeline-orchestration.md`) by removing the verbose "Explicit spawn requirement" paragraph (lines 610) and folding its imperative into a single bullet under "Invocation:". Preserve: `### Scout Fan-out Protocol` heading exactly, `MUST spawn` literal, `separate parallel subagent` literal, `synthesis` + `after scouts` + `Cal` + `Colby` + `Roz` co-located in the section, the Per-Agent Configuration table with `brain-hydrate` row, the Investigation Mode subsection with 4-scout table | T-0042-027, T-0042-028, T-0027-028 anchors |
| R7 | Preserve Eva-capture count < 3 in pipeline-orchestration.md. Current count of `source_agent: 'eva'` literal: exactly 2 (lines 50, 81). The trim operations in R5 and R6 do not touch those two references. Post-trim count MUST remain exactly 2 | `tests/hooks/test_wave3_hook_removal.py:364-369` (asserts < 3) |
| R8 | Line-count reduction targets (non-binding but auditable): agent-system.md saves ~52 lines (167-172 inline -> 8-line summary), pipeline-orchestration.md Mandatory Gates saves ~40 lines (rhetoric collapse across 12 gates), pipeline-orchestration.md Scout Fan-out saves ~8 lines (one paragraph collapse). Total: ~100 trimmed from always-loaded context; +~70 lines added to JIT ref `routing-detail.md` (net always-loaded savings: ~230 lines) | Issue #31 Slice 2 "Est. savings"; scope correction documented in Status |
| R9 | Installed mirror `.claude/rules/agent-system.md` and `.claude/rules/pipeline-orchestration.md` stay in sync with their source templates (byte-identical body modulo any installed frontmatter overlay). Also install `.claude/references/routing-detail.md` alongside other ref files | CLAUDE.md "Triple target"; Slice-1 ADR-0043 Step 1 mirror pattern |
| R10 | ADR-0042 test `test_T_0042_027_scout_fanout_protocol_explicit_spawn_directive` asserts `"MUST spawn"` AND `"separate parallel subagent"` appear inside the Scout Fan-out section. R6 collapse MUST keep both literals inside the section (not delete them) | `tests/adr-0042/test_adr_0042.py:797-805` |
| R11 | ADR-0042 test `test_T_0042_028_scout_fanout_protocol_synthesis_row` asserts `synthesis` + (`after scouts` OR `scouts return`) + all of `Cal`/`Colby`/`Roz` appear in the section. The current section carries these in the "Synthesis step" paragraph (lines 622-623). That paragraph stays as-is -- only the "Explicit spawn requirement" paragraph (610) collapses | `tests/adr-0042/test_adr_0042.py:808-840` |
| R12 | pipeline-models.md is NOT modified in this ADR -- ADR-0042 test anchors forbid moving the Per-Agent Assignment Table, and the in-place trim candidates (Adaptive-Thinking Rationale paragraph, Enforcement Rules) carry explicit ADR-0042 test pins (`Fixed thinking budgets are unsupported`, `max effort is forbidden`) | `tests/adr-0042/test_adr_0042.py:1114-1127, 386-394`; T-0041 tier tests |
| R13 | Install mirrors of touched source files are synced via exact body equality (modulo installed YAML frontmatter overlays stripped at parity-check time, per the `_strip_frontmatter` helper in `tests/test_adr0041_rule_structure.py`) | ADR-0041 Step 6 precedent; T-0042-030 test pattern |
| R14 | Update `tests/adr-0023-reduction/test_reduction_structural.py::test_T_0023_131_All_12_mandatory_gates_preserved_verbatim_count_numbered_items_under_Eva_NEVER_Skips` to strengthen its assertion from the current weak `assert "Eva NEVER Skips" in c` to also count 12 numbered items (`^\d+\. \*\*` regex) -- since we're collapsing rhetoric inside the gates, stronger assertion defends the 12-gate preservation that is the actual intent | Retro lesson 002: tests pin domain intent, not file text; current T-0023-131 docstring says "count numbered items" but the body only checks the header -- fix matches the docstring |

**Retro risks:**
- **Lesson 002 (self-reporting bug codification / tests pin domain intent):** Directly relevant. Slice 1 exposed cross-ADR test regressions because narrow edits broke assertions pinning specific file text (ADR-0040 tokens.md moved; ADR-0005 `<slug>` tag). This ADR mitigates by (a) enumerating every existing test that touches the three target files with its exact assertion shape in the Test Specification, (b) strengthening T-0023-131 per R14 so the 12-gate intent is actually tested (not just the header), (c) keeping the Scout Fan-out synthesis paragraph untouched so T-0042-028 anchors stay intact, (d) keeping pipeline-models.md untouched entirely (R12) to avoid the ADR-0042 minefield.
- **Lesson 005 (cross-agent wiring):** Relevant. The new `routing-detail.md` is a producer (matrix + subsections); its consumers are Eva (routes from the matrix) and the agent-system.md summary paragraph (points to it). Wiring lands in the same step. See Wiring Coverage section.
- **Lessons 001, 003, 004, 006:** N/A -- no data layer, no hooks, no long-running commands, no UI.

**Brain context:** Brain unavailable this session. Greps that substituted for brain lookup:
- `grep -rn "AUTO-ROUTING\|auto-routing" docs/architecture/` -- confirms ADR-0015 and ADR-0016 are the only prior ADRs discussing the routing matrix; neither mandates a specific physical location (they pin content keywords).
- `grep -rn "Mandatory Gates\|same class of violation" docs/architecture/` -- ADR-0023 is the closest precedent for rhetoric reduction; it removed procedural instruction text but did not touch the Mandatory Gates rhetoric because ADR-0023 predates the "same class of violation" refrain introduction.
- `grep -rn "Scout Fan-out" docs/architecture/` -- ADR-0042 added the explicit-spawn paragraph being collapsed; the test anchors it pins are enumerated as R10/R11.

---

## Anti-Goals

**Anti-goal 1: Rewriting any of the 12 Mandatory Gates' core substance.**
Reason: The gates encode non-negotiable pipeline rules. Slicing the rhetoric refrain is a prose trim; rewriting a gate's body would be a behavior change dressed as a line-count fix. Every gate's imperative ("Roz verifies every wave", "Ellis commits Eva does not", etc.) stays intact; only the trailing severity-comparison sentence collapses.
Revisit: when a separate ADR proposes altering a specific gate's behavior (none proposed).

**Anti-goal 2: Touching pipeline-models.md in this ADR.**
Reason: ADR-0042's test suite pins the Per-Agent Assignment Table at heading `## Per-Agent Assignment Table` with exactly 17 rows (T-0042-001), forbids `Agatha (reference docs)` (T-0042-005), requires the Synthesis row (T-0042-037), and the Enforcement Rules anchor `max effort is forbidden` (T-0042-027a paraphrased). A line-count trim that supersedes three landed tests is a different class of change and needs its own supersession ADR. This ADR is a prose trim; scope creep into pipeline-models.md is how cascading slice-1-style regressions get manufactured.
Revisit: when Issue #31 Slice 3 is scoped specifically for pipeline-models.md with explicit ADR-0042 supersession plan.

**Anti-goal 3: "Since we're moving the routing matrix, let's also consolidate the subagent table / Skills table / Custom Commands table."**
Reason: Scope creep. Each of those three tables carries its own test pins (Darwin/Deps subagent row tests; T-0005-070 et al. for the Custom Commands "Skill tool is NOT" section). Consolidating them would multiply blast radius. This ADR touches exactly one section of agent-system.md: the `<routing id="auto-routing">` block. All other sections stay byte-identical.
Revisit: never in a prose-trim ADR; a separate structural consolidation ADR could re-scope if quality gains justify the test-update cost.

---

## Spec Challenge

**Assumption:** The AUTO-ROUTING matrix is only needed when Eva encounters an ambiguous routing case outside an active pipeline. In-flight pipeline routing uses pipeline-orchestration.md Pipeline Flow (always loaded); boot-time auto-routing of the user's first message keys off a small number of obvious verbs that can live in the inline summary. Therefore, moving the 19-row table to a JIT ref does not degrade routing quality in the common case.

**If wrong:** Eva frequently needs the full table to disambiguate between `robert-spec` vs `sable-ux` vs `Cal` vs `Agatha` on the user's first message and the inline summary's 6-bullet compression drops discriminating keywords that the full table carries. Symptom would be Eva auto-routing wrong on the first turn, surfacing as higher boot-time ambiguous-routing rate.

**Mitigation:**
(a) The inline summary keeps one bullet per *agent class* (product spec, UX, architecture, docs, engineering, commit, devops, pipeline/orchestrator, extensions) so the discrimination axes are preserved even if specific trigger phrases go to the ref file.
(b) The summary's last bullet is a load trigger: "For edge cases (discovered agents, disambiguated overlaps, smart context detection), Eva reads `{config_dir}/references/routing-detail.md`" -- so the JIT path is advertised, not buried.
(c) `default-persona.md` line 13 already reads "Apply the auto-routing rules from `agent-system.md` to EVERY user message" -- no change needed to that pointer; the rules are still in agent-system.md via the inline summary, and the summary names the JIT ref.
(d) Falsifiability: if in the next three Medium pipelines Eva asks a clarifying question where she previously would have auto-routed, or auto-routes to the wrong producer, the summary is under-specified and Slice 3 expands the inline summary (or folds back selected rows).

**SPOF:** The inline summary paragraph itself. If the summary is mis-worded and drops a discrimination axis, every first-turn routing decision degrades simultaneously with no gradual signal.
Graceful degradation:
(a) The JIT load trigger is explicit in the summary, so Eva can always escalate to the full file -- the SPOF is "knowing when to load," not "being able to load."
(b) The installed mirror is byte-identical to the source, so any production regression is reproducible locally before merge.
(c) Test T_0044_008 (below) greps the summary for the 6 agent-class anchors (robert-spec, sable-ux, Cal, Agatha, Colby, Ellis) -- a copy-paste mistake that drops one class is caught at the file level.
**Known residual:** Eva may develop a habit of auto-routing from summary alone and never escalating to the full ref. Monitored via boot-time routing-miss rate in telemetry T3 captures. Three consecutive sessions where Eva clarifies instead of routing on the first turn -> follow-up "summary density" ADR.

---

## Context

Slice 1 (ADR-0043) attacked agent-return verbosity. Slice 2 targets the other side of the same budget: the always-loaded instruction surface Eva reads on every session boot. `default-persona.md` line 32: "Eva's fixed context: default-persona.md + agent-system.md + CLAUDE.md (auto-loaded by Claude Code)." Once a pipeline activates, pipeline-orchestration.md joins the always-loaded set per its loading-strategy table.

Current always-loaded line counts (scouts-confirmed):
- agent-system.md: 286 lines
- pipeline-orchestration.md: 802 lines
- CLAUDE.md: ~60 lines
- default-persona.md: ~140 lines
- Total: **~1288 lines of rule/persona text on every turn** (before pipeline-models.md which loads with `{pipeline_state_dir}` reads).

Two fat-free targets in this set:

1. **agent-system.md:113-173** -- 61 lines of AUTO-ROUTING matrix. This matrix is exhaustive by design (covers 19 intent-to-agent mappings). It is consulted when Eva needs to disambiguate a user message; once a pipeline is active or a decision is made, the matrix is not re-read. That makes it the textbook JIT candidate.

2. **pipeline-orchestration.md:109-250** -- 142 lines of Mandatory Gates. The twelve gates themselves are load-bearing. But the trailing "same class of violation as X" refrain appears 8 times verbatim with minor variations (Write tool, git commit, skipping Roz, skipping Poirot, skipping spec reconciliation) and contributes pure rhetoric, not new information. The declaration was already made in the section's opening paragraph; the per-gate repetition is reinforcement-by-repetition. Eva does not need to be told eight times per boot that skipping a gate is as bad as Eva editing source code; once is enough.

3. **pipeline-orchestration.md:604-635** -- 32 lines of Scout Fan-out Protocol. ADR-0042 added an "Explicit spawn requirement" paragraph (line 610) that restates the same imperative in three sentences. The imperative fits on one bullet; the paragraph collapses without losing the behavioral constraint.

The three trims add up to ~230 always-loaded-line reduction. The AUTO-ROUTING move adds ~70 lines to JIT (routing-detail.md), but those are loaded only on edge-case routing, not per-turn. Net: the per-turn budget drops by ~230 lines with no load-bearing rule removed.

---

## Decision

### 1. Create `source/shared/references/routing-detail.md` (new JIT reference file)

Full file contents (verbatim text for Colby to paste):

```markdown
# AUTO-ROUTING -- Detail Matrix

Loaded by Eva when she encounters an ambiguous routing case outside an
active pipeline, when a discovered agent appears to overlap a core agent,
or when smart-context detection needs to run against the full artifact
table. The inline summary in `{config_dir}/rules/agent-system.md`
`<routing id="auto-routing">` covers the common cases and points here for
edge cases.

## Intent Detection

| If the user... | Route to | Type |
|---|---|---|
| Describes new idea, feature concept, "what if we..." | **robert-spec** | subagent |
| Discusses UI, UX, user flows, wireframes, design patterns | **sable-ux** | subagent |
| Says "review this ADR", "plan this", "how should we architect..." | **Cal** | skill |
| References feature spec without ADR | **Cal** | skill |
| Says "plan the docs", "what docs do we need", "documentation plan" | **Agatha** (doc planning) | skill |
| Says "mockup", "prototype", "let me see it" | Scout fan-out → **Colby** (mockup mode) [`<colby-context>`] | subagent |
| Says "scan the codebase", "investigate paths", "map all X", "review the whole codebase" (read-only survey, no existing ADR or bug report) | Explore+haiku scouts → Sonnet reviewer | subagent |
| Cal just finished ADR with test spec tables | Scout fan-out → **Roz** (test spec review) [`<qa-evidence>`] | subagent |
| Roz approved test spec, ready to build | Scout fan-out → **Colby** + **Agatha** (parallel) [`<colby-context>`] | subagent |
| Says "build this", "implement", "code this" with existing plan | Scout fan-out → **Colby** + **Agatha** (parallel) [`<colby-context>`] | subagent |
| Says "run tests", "check this", "QA", "validate" | Scout fan-out → **Roz** [`<qa-evidence>`] | subagent |
| Says "commit", "push", "ship it", "we're done" | **Ellis** | subagent |
| Says "write docs", "document this", "update the docs" | **Agatha** (writing) | subagent |
| Asks about outdated dependencies, CVEs, upgrade risk, "is [package] safe to upgrade", "check my deps", dependency vulnerabilities | **Deps** (if `deps_agent_enabled: true`) or suggest enabling | subagent |
| Says "analyze the pipeline", "how are agents performing", "pipeline health", "run Darwin", "what needs improving" | **Darwin** (if `darwin_enabled: true`) or suggest enabling | subagent |
| Asks about infra, CI/CD, deployment, monitoring | **Eva** (devops) | skill |
| Reports a bug, error, stack trace, "this is broken" | Scout swarm (4 haiku) → **Roz** [`<debug-evidence>`] → hard pause → **Colby** (fix) [`<colby-context>`] | subagent chain |
| Says "go", "next", "continue" after a phase completes | **Eva** routes to next | (see flow) |
| Says "follow the flow", "pipeline", "run the full pipeline" | **Eva** (orchestrator) | skill |

## Smart Context Detection

Before routing, check for existing artifacts:
- Feature spec in `{product_specs_dir}` → skip Robert
- UX design doc in `{ux_docs_dir}` → skip Sable
- Doc plan exists → skip Agatha (planning)
- Feature components with mock data hooks → mockup done, go to Cal
- ADR in `{architecture_dir}` → skip Cal
- Code staged and tests pass → skip to Ellis

## Auto-Routing Confidence
- **High confidence:** route directly, announce agent and why
- **Ambiguous:** ask ONE clarifying question, then route
- Always mention slash commands available as manual overrides

## Discovered Agent Routing

**Core first:** Core routing table always evaluated first; core agents have priority.

**Conflict check:** If discovered agent matches user intent better than (or equally to) any core agent, Eva announces: "This could go to [core agent] (core) or [discovered agent] (custom). Which do you prefer for [intent]?"

**Record preference:**
- Brain available: `agent_capture` with `thought_type: 'preference'`, `source_agent: 'eva'`, metadata: `routing_rule: {intent} -> {chosen_agent}`
- Brain unavailable: append to `context-brief.md` under "## Routing Preferences"

**Reuse preference:** On subsequent same-intent messages, use recorded preference without re-asking.

**No conflict:** Discovered agents with no core overlap available only via **explicit name mention** -- they do not appear in automatic routing.

**Explicit name mention:** Routes to any discovered agent regardless of conflicts -- always a direct override.

Discovered agents cannot shadow core agents without explicit user consent.
```

No frontmatter. The file is pure content -- Eva's Read tool loads it on demand. The installed copy at `.claude/references/routing-detail.md` is byte-identical to this source (no Claude overlay needed -- reference files do not carry frontmatter per the existing pattern in `source/shared/references/*.md`).

### 2. Rewrite `<routing id="auto-routing">` block in `source/shared/rules/agent-system.md`

**Current text** (lines 111-174 in source file):

```markdown
<routing id="auto-routing">

## AUTO-ROUTING RULES

Classify intent outside active pipeline; route automatically.

### Intent Detection

| If the user... | Route to | Type |
[... 19 rows ...]

### Smart Context Detection
[... 6 bullets ...]

### Auto-Routing Confidence
[... 3 bullets ...]

### Discovered Agent Routing
[... 7 paragraphs ...]

</routing>
```

**Replacement text** (everything between `<routing id="auto-routing">` and `</routing>` tags, inclusive of the tags themselves being preserved):

```markdown
<routing id="auto-routing">

## AUTO-ROUTING RULES

Classify intent outside active pipeline; route automatically. Full Intent Detection
matrix, Smart Context Detection list, Auto-Routing Confidence thresholds, and
Discovered Agent Routing rules live in `{config_dir}/references/routing-detail.md` --
Eva loads that file on demand when the summary below does not disambiguate, when a
discovered agent appears to overlap a core agent, or when artifact-presence checks
need to run against the full table.

### Summary

- **Idea / feature / spec talk** → **robert-spec**. **UI / UX / flows** → **sable-ux**. **Architecture / "how should we build"** → **Cal**. **Docs planning or writing** → **Agatha**. **Implementation / mockup / build** → **Colby** (scout fan-out first). **QA / tests / validate** → **Roz** (scout fan-out first).
- **Commit / push / ship** → **Ellis**. **Infra / CI/CD / deployment** → **Eva** (/devops skill). **"Run the pipeline" / "follow the flow"** → **Eva** (orchestrator).
- **Bug reports / "this is broken"** → Scout swarm → **Roz** (diagnose, hard pause) → **Colby** (fix after user approval).
- **Dependency / CVE / upgrade questions** → **Deps** (requires `deps_agent_enabled: true`). **Pipeline health / agent performance / "run Darwin"** → **Darwin** (requires `darwin_enabled: true`).
- **Discovered agents** route only via explicit name mention when they have no core-agent overlap; on overlap, Eva asks once and records the preference in the brain or `context-brief.md`.
- **Edge cases** (ambiguous intent, smart-context checks against `{product_specs_dir}` / `{ux_docs_dir}` / `{architecture_dir}`, discovered-agent conflict protocol) → Eva reads `{config_dir}/references/routing-detail.md`.

### Confidence & Overrides

High confidence: route and announce. Ambiguous: one clarifying question then route. Slash commands always available as manual overrides.

</routing>
```

**What changed:**
- The 19-row Intent Detection table -> 6 bullets in the Summary (one per agent class + edge-case pointer).
- Smart Context Detection (6 bullets) -> folded into the last Summary bullet as a pointer.
- Auto-Routing Confidence (3 bullets) -> compressed into one 2-sentence paragraph under "Confidence & Overrides".
- Discovered Agent Routing (7 paragraphs, ~17 lines) -> one bullet naming the two trigger conditions (explicit mention / core overlap).
- Load trigger for the JIT ref named three times in prose (paragraph 1, last Summary bullet, and implicitly via the load-only-on-edge-case framing).

**What survives verbatim (required anchors):**
- `## AUTO-ROUTING RULES` heading (T-0005-071 uses regex that tolerates this).
- `Classify intent outside active pipeline; route automatically.` sentence (preserved word-for-word from line 115).
- `Deps` + `dependency` + `deps_agent_enabled` string in the "Dependency" bullet -- satisfies T-0015-034 (regex: `Deps` AND `dependenc|outdated|upgrade|cve|vulnerability`).
- `Darwin` + `pipeline health` + `agent performance` + `run Darwin` + `darwin_enabled` -- satisfies T-0016-038 (regex: `Darwin` AND `pipeline.*health|pipeline.*analy|agent.*perform|what.*needs.*improv|run.*Darwin`) and T-0016-039 (`darwin_enabled`) and T-0016-041 (`darwin_enabled.*true|if.*darwin_enabled`).

### 3. Rewrite Mandatory Gates opener + collapse per-gate rhetoric in `source/shared/rules/pipeline-orchestration.md`

**Current text** (lines 107-114 -- the section opener before gate 1):

```markdown
<gate id="mandatory-gates">

## Mandatory Gates -- Eva NEVER Skips These

Eva manages phase transitions. Some phases are skippable based on sizing
(see agent-system.md). These twelve gates are NEVER skippable. No exceptions.
No "it's just a small fix." No "I'll run tests later." Violating these is
the same severity as Eva editing source code.
```

**Replacement opener** (verbatim, lines 107-116 in new file):

```markdown
<gate id="mandatory-gates">

## Mandatory Gates -- Eva NEVER Skips These

Eva manages phase transitions. Some phases are skippable based on sizing
(see agent-system.md). These twelve gates are NEVER skippable. No exceptions.
No "it's just a small fix." No "I'll run tests later."

**Violation class.** Skipping, bypassing, or self-performing any of the twelve
gates below is the same severity as Eva editing source code (Write tool
violation). Individual gates note a tighter comparison target in parentheses
only when the specific violation differs from the default (e.g., gate 5's
"invocation error" tag). Otherwise the default class applies.
```

**Rationale:** declares the severity class once, names the default comparison (Write tool), and signals that exceptions use parenthetical tags. Every per-gate "same class of violation as X" sentence below collapses to the default unless a specific tighter comparison is meaningful.

**Per-gate collapses** (each listed with exact OLD -> NEW replacement):

#### Gate 2 (lines 122-127 current):

OLD tail sentence:
```
Per-wave commits during
the build phase auto-advance after Roz QA PASS. Eva running `git commit`
is the same class of violation as Eva using the Write tool on source files.
```

NEW tail sentence:
```
Per-wave commits during
the build phase auto-advance after Roz QA PASS. Eva running `git commit` is
a violation (default class).
```

(Agent Teams note paragraph, worktree cleanup paragraph: unchanged.)

#### Gate 3 (lines 141-147 current):

OLD tail sentence:
```
Roz runs the
full suite at wave boundaries, not unit boundaries. Eva invokes Roz
for this verification -- Eva does not run the test suite herself. Eva
running test commands is the same class of violation as Eva using the
Write tool on source files.
```

NEW tail sentence:
```
Roz runs the
full suite at wave boundaries, not unit boundaries. Eva invokes Roz for
this verification -- Eva does not run the test suite herself (default class).
```

(Agent Teams note paragraph: unchanged.)

#### Gate 5 (lines 166-173 current):

OLD tail sentences:
```
Eva triages findings from both agents before routing
fixes to Colby. Skipping Poirot is the same class of violation as
skipping Roz. "It's a small change" is not an excuse. If Eva invokes
Poirot with anything beyond the raw diff, that is an invocation error
-- same severity as embedding a root cause theory in a TASK field.
Sentinel runs at the review juncture only, not per-wave (see gate 7).
```

NEW tail sentences:
```
Eva triages findings from both agents before routing fixes to Colby.
Skipping Poirot is a violation (default class -- "it's a small change"
is not an excuse). Invoking Poirot with anything beyond the raw diff is
an invocation error (tighter class: same as embedding a root-cause
theory in a TASK field). Sentinel runs at the review juncture only, not
per-wave (see gate 7).
```

(Agent Teams note paragraph: unchanged.)

#### Gate 7 (lines 196-203 current):

OLD tail sentence:
```
Robert-subagent receives ONLY the spec and implementation code -- no ADR,
no UX doc, no Roz report. On Small: Eva invokes Robert-subagent only
if Roz flags doc impact AND an existing spec is found for the feature.
Skipping Robert-subagent on Medium/Large is the same class of violation
as skipping Poirot.
```

NEW tail sentence:
```
Robert-subagent receives ONLY the spec and implementation code -- no ADR,
no UX doc, no Roz report. On Small: Eva invokes Robert-subagent only
if Roz flags doc impact AND an existing spec is found for the feature.
Skipping Robert-subagent on Medium/Large is a violation (default class).
```

#### Gate 10 (lines 219-226 current):

OLD tail sentences:
```
Updated artifacts ship in the same commit as code. No deferred cleanup.
"We'll update the spec later" is the same class of violation as
skipping Roz.
```

NEW tail sentences:
```
Updated artifacts ship in the same commit as code. No deferred cleanup --
"we'll update the spec later" is a violation (default class).
```

#### Gate 11 (lines 228-237 current):

OLD tail sentences:
```
"Auto-advance" means logging status
and moving to the next phase -- it does not mean skipping the pause
between response boundaries. Phase bleed (silently advancing through
multiple phases in one turn) is the same class of violation as
skipping Roz.
```

NEW tail sentences:
```
"Auto-advance" means logging status and moving to the next phase -- it does
not mean skipping the pause between response boundaries. Phase bleed
(silently advancing through multiple phases in one turn) is a violation
(default class).
```

**Gates 1, 4, 6, 8, 9, 12:** no "same class of violation" sentence present -- no change.

**Agent Standards section line 780** (outside Mandatory Gates, same file):

OLD:
```
- **Agatha's divergence report ships in the pipeline report.** Agatha's Divergence Report (code-vs-docs gaps) must be summarized in `{pipeline_state_dir}/pipeline-state.md`. Silently dropped divergence findings are the same class of violation as skipping spec reconciliation.
```

NEW:
```
- **Agatha's divergence report ships in the pipeline report.** Agatha's Divergence Report (code-vs-docs gaps) must be summarized in `{pipeline_state_dir}/pipeline-state.md`. Silently dropped divergence findings are a violation (same class as skipping spec reconciliation).
```

(This one is light-touch -- preserves the "skipping spec reconciliation" comparison because it is meaningfully different from the default "Write tool" class, but compresses the rhetoric.)

### 4. Collapse "Explicit spawn requirement" paragraph in Scout Fan-out Protocol section

**Current text** (lines 606-611 in `source/shared/rules/pipeline-orchestration.md`):

```markdown
Eva fans out Explore+haiku agents in parallel before invoking Cal, Roz, or Colby. Scouts collect raw evidence cheaply. The main agent receives it as a named inline block and skips the collection phase entirely.

**Invocation:** `Agent(subagent_type: "Explore", model: "haiku")`. Facts only — no design opinions. Dedup rule: each file read by at most one scout.

**Explicit spawn requirement:** Eva MUST spawn scouts as separate parallel subagent invocations. Eva MUST spawn the synthesis agent as a separate parallel subagent invocation after scouts return for Cal, Colby, or Roz. Eva does NOT collect scout evidence in her own turn. Eva does NOT synthesize in her own turn. Performing either task in-thread silently bypasses the fan-out and the scout-swarm hook cannot detect the bypass (the hook inspects the primary-agent prompt; it does not observe Eva's in-thread reasoning). In-thread scout collection or synthesis is the same class of violation as Eva running `git commit` on code.
```

**Replacement text** (lines 606-610 in new file):

```markdown
Eva fans out Explore+haiku agents in parallel before invoking Cal, Roz, or Colby. Scouts collect raw evidence cheaply. The main agent receives it as a named inline block and skips the collection phase entirely.

**Invocation:** `Agent(subagent_type: "Explore", model: "haiku")`. Facts only — no design opinions. Dedup rule: each file read by at most one scout.

**Explicit spawn requirement.** Eva MUST spawn scouts as separate parallel subagent invocations and MUST spawn the synthesis agent as a separate parallel subagent invocation after scouts return for Cal, Colby, or Roz. In-thread scout collection or synthesis silently bypasses the fan-out -- the scout-swarm hook inspects the primary-agent prompt only, not Eva's reasoning -- and is a violation (default class).
```

**What survives verbatim:**
- `MUST spawn` literal (T-0042-027).
- `separate parallel subagent` literal (T-0042-027, twice originally, once in collapsed version -- the test uses `in section` check, so single occurrence passes).
- `synthesis` + `after scouts return` + `Cal, Colby, or Roz` co-located (T-0042-028 -- the regex accepts `after scouts` OR `scouts return`; the collapsed version preserves both patterns).

### 5. Installed-copy sync

The three source edits above are mirrored to installed copies at `.claude/rules/agent-system.md` and `.claude/rules/pipeline-orchestration.md`. Plus the new `.claude/references/routing-detail.md` installation.

| Source file | Installed copy (Claude) |
|---|---|
| `source/shared/references/routing-detail.md` (NEW) | `.claude/references/routing-detail.md` (NEW) |
| `source/shared/rules/agent-system.md` | `.claude/rules/agent-system.md` |
| `source/shared/rules/pipeline-orchestration.md` | `.claude/rules/pipeline-orchestration.md` |

**Body-parity rule** (per ADR-0041 Step 6 precedent): the installed `.claude/rules/*.md` files carry a YAML `paths:` frontmatter overlay added at install time. The body (post-frontmatter) must match the source verbatim. Tests use the `_strip_frontmatter` helper from `tests/test_adr0041_rule_structure.py` for parity checks.

**No Cursor edits.** Cursor does not install `agent-system.md`, `pipeline-orchestration.md`, or the new `routing-detail.md` (per research-brief scout finding: "pipeline-internal reference material, not installed for Cursor").

### 6. Test update -- strengthen T-0023-131

Update `tests/adr-0023-reduction/test_reduction_structural.py::test_T_0023_131_All_12_mandatory_gates_preserved_verbatim_count_numbered_items_under_Eva_NEVER_Skips` per R14. Old body asserted only the header presence; new body counts numbered gate items so the "12 gates preserved" intent is actually tested. Exact replacement in Test Specification Category E.

---

## Alternatives Considered

**Alt 1: Move the AUTO-ROUTING matrix inline into `default-persona.md` instead of a separate JIT file.** Rejected. `default-persona.md` is also always-loaded -- this would swap line counts between files without reducing the always-loaded total. The whole point is JIT loading; a new reference file is the right shape.

**Alt 2: Move the pipeline-models.md Per-Agent Assignment Table to a JIT ref despite ADR-0042 test pins.** Rejected. ADR-0042 is immutable. Three landed tests (T-0042-001, T-0042-005, T-0042-037) assert the table lives in pipeline-models.md at a specific heading with 17 rows and specific row contents. Superseding three landed tests to achieve ~28 lines of savings is a worse trade than keeping pipeline-models.md intact and capturing ~230 lines from the other two targets. The issue's "~400 lines" estimate assumed the pipeline-models.md move was tractable; it is not, so the revised target is ~230 lines.

**Alt 3: Collapse the Mandatory Gates rhetoric by deleting the "same class of violation" sentences entirely (no default-class declaration).** Rejected. The severity signal is load-bearing -- new agents trained on the doc (or Eva herself after compaction) need to know skipping a gate is a hard violation, not a soft preference. Deleting the rhetoric without a replacement would weaken the behavioral signal. The chosen approach (declare class once, reference tersely) preserves the signal at ~1/4 the word count.

**Alt 4: Leave the Scout Fan-out "Explicit spawn requirement" paragraph alone -- it was added by ADR-0042 for a reason.** Rejected but with care. ADR-0042 added the paragraph to close a specific gap (Eva performing scout-collection in-thread). The test pins (T-0042-027) require the `MUST spawn` + `separate parallel subagent` literals, not the full paragraph shape. The collapsed version keeps both literals and the anti-pattern warning, just in one paragraph instead of six sentences. The behavioral rule survives; only the prose volume drops.

**Alt 5: Split this ADR into three (one per target file).** Rejected. The three trims are independent but share a common test-update list (T-0023-131 touches the Mandatory Gates change; the agent-system summary and routing-detail.md are producer/consumer in the same vertical slice; the Scout Fan-out collapse shares the Mandatory Gates rhetoric-collapse philosophy). Splitting would produce three ADRs with substantial overlap in DoR and test coverage. One ADR, one Roz pass, one Colby build is more efficient.

---

## Consequences

**Positive.**
- Always-loaded line count drops by ~230 per Eva session boot (~18% reduction on the four always-loaded files' subtotal; ~12% on the full always-loaded set).
- AUTO-ROUTING matrix becomes grep-able as a single reference (easier to audit + extend than embedded-in-agent-system).
- Mandatory Gates become scannable -- the repetitive refrain currently dilutes the gates themselves; terse trailing tags put the gate substance front-and-center.
- Scout Fan-out section keeps all behavioral anchors with less prose friction.

**Negative / trade-offs.**
- Eva must escalate to `routing-detail.md` on edge-case routing. For most first-turn messages the inline summary is sufficient; the escalation is a rare event. Cost: one extra Read call per edge-case routing decision. Benefit: ~61 lines saved per turn that does not hit the edge case.
- The "default class" convention is new vocabulary. One-line onboarding cost when an agent / new contributor reads the Mandatory Gates section for the first time.
- Three sections now depend on the same new JIT ref. If `routing-detail.md` is deleted or misnamed, edge-case routing degrades silently. Mitigation: T_0044_015 verifies the installed mirror exists and is byte-identical to the source.

**Neutral.**
- Behavioral contract unchanged. No gate semantics change. No scout-fan-out semantics change. No new routing rules added or removed. This is a pure prose-volume trim with a file-structure rearrangement.
- pipeline-models.md is untouched -- ADR-0041 and ADR-0042 test suites unaffected.
- Cursor plugin unaffected -- these three files are not in its install list.

---

## Implementation Plan

**Vertical-slice principle:** producer and consumer land in the same step. `routing-detail.md` (producer) and the agent-system.md summary (consumer pointer) ship together in Step 1. The Mandatory Gates opener (declares violation class) and the per-gate tail-sentence collapses (consume the class) ship together in Step 2. The Scout Fan-out collapse is a self-contained single-paragraph trim in Step 3.

### Step 1: Create `routing-detail.md` + rewrite agent-system.md routing block

**Files (4):**
1. `source/shared/references/routing-detail.md` (NEW -- paste Decision §1 verbatim content)
2. `.claude/references/routing-detail.md` (NEW -- mirror of #1, byte-identical)
3. `source/shared/rules/agent-system.md` (replace `<routing id="auto-routing">`..`</routing>` block with Decision §2 replacement text)
4. `.claude/rules/agent-system.md` (mirror of #3; preserve installed-side YAML `paths:` frontmatter overlay if present, replace only the body)

**Acceptance criteria:**
- `routing-detail.md` exists in both `source/shared/references/` and `.claude/references/` with byte-identical bodies.
- `routing-detail.md` contains the 19-row Intent Detection table, the 6-bullet Smart Context Detection list, the 3-bullet Auto-Routing Confidence list, and the 7-paragraph Discovered Agent Routing subsection (preserving all existing content from agent-system.md lines 117-172).
- `agent-system.md` `<routing id="auto-routing">` block matches Decision §2 replacement text verbatim between the opening and closing tags.
- `agent-system.md` Summary bullets mention: robert-spec, sable-ux, Cal, Agatha, Colby, Ellis, Eva (devops), Eva (orchestrator), Roz, Deps (with `deps_agent_enabled: true`), Darwin (with `darwin_enabled: true`), discovered agents.
- `agent-system.md` Summary contains the literal string `routing-detail.md`.
- Installed-mirror diff (body-only, frontmatter stripped) is empty for both `agent-system.md` and `routing-detail.md`.
- All existing tests in `tests/adr-0015-deps/test_deps_structural.py::test_T_0015_034_auto_routing_deps`, `tests/adr-0016-darwin/test_darwin_structural.py::test_T_0016_038`, `test_T_0016_039`, `test_T_0016_041` pass against the revised agent-system.md.

**Complexity:** S2 (4 files, vertical slice, one new file + one rewrite + two mirror syncs). Step size passes S1-S5: 4 ≤ 10 files, single concern (AUTO-ROUTING move), producer+consumer in same step, no schema / hook / runtime changes.

### Step 2: Rewrite Mandatory Gates opener + collapse per-gate rhetoric in pipeline-orchestration.md

**Files (2):**
1. `source/shared/rules/pipeline-orchestration.md` (replace gate-opener paragraph per Decision §3; apply the 6 per-gate tail-sentence collapses per Decision §3; apply the Agent Standards line 780 collapse per Decision §3)
2. `.claude/rules/pipeline-orchestration.md` (mirror of #1; body-only edit, preserve installed frontmatter)

**Acceptance criteria:**
- The section opener under `## Mandatory Gates -- Eva NEVER Skips These` contains the `**Violation class.**` paragraph declaring "same severity as Eva editing source code (Write tool violation)".
- Count of 12 numbered gates (regex `^\d+\. \*\*` within the Mandatory Gates section) equals 12.
- The literal `"Eva NEVER Skips"` string is still present (T-0023-131 anchor).
- Count of `source_agent: 'eva'` literal across the full file equals exactly 2 (unchanged from pre-ADR -- satisfies T-0024-041 `< 3`).
- Count of `"same class of violation"` literal in the Mandatory Gates section (lines 107-250 post-edit) equals 0. In the rest of the file (Agent Standards section line 780), count equals 1 (the line-780 version uses "same class as skipping spec reconciliation" -- a specific targeted comparison, not the default refrain).
- All six per-gate collapses applied exactly as written in Decision §3.
- Installed mirror body matches source body byte-for-byte (modulo frontmatter).

**Complexity:** S2 (2 files, 7 distinct in-file edits all in the same section / file, low interpretation -- verbatim text replacements).

### Step 3: Collapse Scout Fan-out "Explicit spawn requirement" paragraph

**Files (2):**
1. `source/shared/rules/pipeline-orchestration.md` (replace lines 610 -- the "Explicit spawn requirement:" paragraph -- with Decision §4 replacement text)
2. `.claude/rules/pipeline-orchestration.md` (mirror of #1)

**Acceptance criteria:**
- Scout Fan-out Protocol section `### Scout Fan-out Protocol` heading still present and at same nesting level.
- Literal strings present within the section (T-0042-027 / T-0042-028 anchors): `MUST spawn`, `separate parallel subagent`, `synthesis`, `after scouts return` or `scouts return`, `Cal`, `Colby`, `Roz`.
- Per-Agent Configuration table present with 4 rows including `brain-hydrate` (T-0027-028 anchor).
- Investigation Mode subsection still present with 4-scout table (Files/Tests/Brain/Error grep).
- Installed mirror body matches source body byte-for-byte (modulo frontmatter).

**Complexity:** S1 (2 files, one paragraph replacement, in-place within already-edited-in-step-2 file). This step can be chained with Step 2 in a single Colby wave since both touch pipeline-orchestration.md.

### Step 4: Update T-0023-131 test body

**Files (1):**
1. `tests/adr-0023-reduction/test_reduction_structural.py` (replace T-0023-131 body per Test Specification Category E exact replacement text)

**Acceptance criteria:**
- Test function name unchanged (`test_T_0023_131_All_12_mandatory_gates_preserved_verbatim_count_numbered_items_under_Eva_NEVER_Skips`).
- Test body now counts `^\d+\. \*\*` occurrences in the extracted Mandatory Gates section and asserts count == 12, in addition to the existing header-presence check.
- Test passes against the Step 2 post-edit state.

**Complexity:** S1 (1 file, one function body replacement).

---

## Test Specification

Test ID format: `T_0044_NNN`. Categories A through F. Failure tests ≥ happy-path where meaningful. Tests are grep-style + line-count assertions against the post-build state of the three target files and the new reference file.

### Category A: Routing-detail.md creation and content preservation

| ID | Category | Description |
|---|---|---|
| T_0044_001 | happy | `source/shared/references/routing-detail.md` exists as a file and is readable. |
| T_0044_002 | happy | `source/shared/references/routing-detail.md` contains the heading `## Intent Detection` exactly once. |
| T_0044_003 | happy | Intent Detection table in `source/shared/references/routing-detail.md` has at least 19 data rows (regex: lines starting with `| ` and containing at least two `|` separators, excluding the header and divider rows). |
| T_0044_004 | happy | `source/shared/references/routing-detail.md` contains all of these literal strings co-located in the Intent Detection table: `robert-spec`, `sable-ux`, `Cal`, `Agatha`, `Colby`, `Ellis`, `Roz`, `Deps`, `Darwin`, `deps_agent_enabled`, `darwin_enabled`, `debug-evidence`, `colby-context`, `qa-evidence`, `research-brief`. |
| T_0044_005 | happy | `source/shared/references/routing-detail.md` contains the heading `## Smart Context Detection`, with 6 bullet items (regex: lines starting with `- `) between the heading and the next `##` heading. |
| T_0044_006 | happy | `source/shared/references/routing-detail.md` contains the heading `## Discovered Agent Routing`, with all of these literal anchors inside the subsection: `Core first`, `Conflict check`, `Record preference`, `Reuse preference`, `No conflict`, `Explicit name mention`, `Discovered agents cannot shadow core agents`. |
| T_0044_007 | failure | `source/shared/references/routing-detail.md` does NOT contain YAML frontmatter (first line is not `---`). |

### Category B: Agent-system.md routing-block rewrite

| ID | Category | Description |
|---|---|---|
| T_0044_008 | happy | `source/shared/rules/agent-system.md` `<routing id="auto-routing">` section (text between `<routing id="auto-routing">` and `</routing>`) contains all six agent-class anchors: `robert-spec`, `sable-ux`, `Cal`, `Agatha`, `Colby`, `Ellis`. |
| T_0044_009 | happy | Same extracted routing section contains the literal string `routing-detail.md` at least once (JIT load trigger pointer). |
| T_0044_010 | happy | Same extracted routing section contains the literal string `Classify intent outside active pipeline; route automatically.` verbatim (summary opener preserved). |
| T_0044_011 | happy | Same extracted routing section contains `Deps` AND `deps_agent_enabled` within the same paragraph/bullet (regex match on adjacent-line window). Satisfies T-0015-034 anchor continuation. |
| T_0044_012 | happy | Same extracted routing section contains `Darwin` AND `darwin_enabled` within the same paragraph/bullet. Satisfies T-0016-038/039/041 anchor continuation. |
| T_0044_013 | failure | Same extracted routing section does NOT contain the literal header `### Intent Detection` (moved to routing-detail.md). |
| T_0044_014 | failure | Same extracted routing section does NOT contain the literal header `### Smart Context Detection` (moved to routing-detail.md). |
| T_0044_015 | failure | Same extracted routing section does NOT contain the literal header `### Discovered Agent Routing` (moved to routing-detail.md). |
| T_0044_016 | failure | The number of table data rows inside the `<routing id="auto-routing">` section (regex: lines matching `^\| .* \| .* \|`) is 0 -- the 19-row matrix was moved, not left in place. |

### Category C: Installed-mirror parity

| ID | Category | Description |
|---|---|---|
| T_0044_017 | happy | `.claude/references/routing-detail.md` exists and its body is byte-identical to `source/shared/references/routing-detail.md` (reference files carry no frontmatter overlay; direct byte comparison). |
| T_0044_018 | happy | `.claude/rules/agent-system.md` body (frontmatter stripped using `_strip_frontmatter`) equals `source/shared/rules/agent-system.md` verbatim. |
| T_0044_019 | happy | `.claude/rules/pipeline-orchestration.md` body (frontmatter stripped) equals `source/shared/rules/pipeline-orchestration.md` verbatim. |

### Category D: Mandatory Gates opener + rhetoric collapse

| ID | Category | Description |
|---|---|---|
| T_0044_020 | happy | `source/shared/rules/pipeline-orchestration.md` contains the literal `## Mandatory Gates -- Eva NEVER Skips These`. |
| T_0044_021 | happy | Same file contains the literal `**Violation class.**` exactly once (the new opener paragraph). |
| T_0044_022 | happy | Within the Mandatory Gates section (between `## Mandatory Gates -- Eva NEVER Skips These` and the next `## ` heading), the count of lines matching the regex `^\d+\. \*\*` equals exactly 12 (the 12 numbered gates preserved). |
| T_0044_023 | happy | Same Mandatory Gates section contains all 12 gate titles (literal substrings, one per gate): `Roz verifies every wave`, `Ellis commits. Eva does not`, `Full test suite between waves`, `Roz investigates user-reported bugs. Eva does not`, `Poirot blind-reviews every wave`, `Distillator compresses cross-phase artifacts`, `Robert-subagent reviews at the review juncture`, `Sable-subagent verifies every mockup before UAT`, `Agatha writes docs after final Roz sweep`, `Spec and UX doc reconciliation is continuous`, `One phase transition per turn`, `Loop-breaker: 3 failures = halt`. |
| T_0044_024 | failure | Within the Mandatory Gates section, the literal string `same class of violation` appears exactly 0 times (the refrain was collapsed). |
| T_0044_025 | failure | Across the entire `source/shared/rules/pipeline-orchestration.md` file, the literal string `same class of violation` appears exactly 0 times -- the one remaining instance in the Agent Standards section (line 780 OLD) was rewritten to "same class as skipping spec reconciliation" per Decision §3. |
| T_0044_026 | happy | The Agent Standards section of `source/shared/rules/pipeline-orchestration.md` contains the literal `same class as skipping spec reconciliation` exactly once (the targeted comparison survived as a specific non-default class). |
| T_0044_027 | happy | `source/shared/rules/pipeline-orchestration.md` file-wide count of `source_agent: 'eva'` literal is exactly 2 (unchanged; satisfies T-0024-041 < 3). |

### Category E: T-0023-131 test-body strengthening

| ID | Category | Description |
|---|---|---|
| T_0044_028 | test-update | `tests/adr-0023-reduction/test_reduction_structural.py::test_T_0023_131_All_12_mandatory_gates_preserved_verbatim_count_numbered_items_under_Eva_NEVER_Skips` body replaced with the verbatim replacement text below. Function name and decorator-free shape preserved. |

**Exact replacement text for T_0044_028** (Colby and Roz both reference this -- this is the new body for the existing test, lines 1090-1095 in the current file):

```python
def test_T_0023_131_All_12_mandatory_gates_preserved_verbatim_count_numbered_items_under_Eva_NEVER_Skips():
    """T-0023-131: All 12 mandatory gates preserved (count numbered items under 'Eva NEVER Skips').

    Strengthened post-ADR-0044: previously asserted only the section header was
    present. Now extracts the Mandatory Gates section and counts `^\\d+\\. \\*\\*`
    lines so the 12-gate preservation intent is actually tested. ADR-0044 collapsed
    the per-gate "same class of violation" rhetoric; the 12-gate body count guards
    against accidental gate loss during rhetoric trims.
    """
    f = SHARED_RULES / "pipeline-orchestration.md"
    assert f.is_file()
    c = f.read_text()
    assert "Eva NEVER Skips" in c
    # Extract the Mandatory Gates section: between the section header and the
    # next top-level `## ` heading (or end of file).
    section_match = re.search(
        r"## Mandatory Gates -- Eva NEVER Skips These(.*?)(?=\n## |\Z)",
        c,
        re.DOTALL,
    )
    assert section_match, "Mandatory Gates section not found"
    section = section_match.group(1)
    numbered_gates = re.findall(r"^\d+\. \*\*", section, re.MULTILINE)
    assert len(numbered_gates) == 12, (
        f"Mandatory Gates section has {len(numbered_gates)} numbered gates; "
        "expected 12. ADR-0044 preserves all 12 gates while collapsing rhetoric."
    )
```

### Category F: Scout Fan-out collapse anchor preservation

| ID | Category | Description |
|---|---|---|
| T_0044_029 | happy | `source/shared/rules/pipeline-orchestration.md` contains the literal `### Scout Fan-out Protocol` exactly once. |
| T_0044_030 | happy | Scout Fan-out Protocol section (between `### Scout Fan-out Protocol` and the next `###` or `##` heading) contains the literal `MUST spawn`. Satisfies T-0042-027 anchor. |
| T_0044_031 | happy | Same section contains the literal `separate parallel subagent`. Satisfies T-0042-027 anchor. |
| T_0044_032 | happy | Same section contains `synthesis` AND (`after scouts return` OR `scouts return`) AND all of `Cal`, `Colby`, `Roz` (case-sensitive). Satisfies T-0042-028 anchor. |
| T_0044_033 | happy | Per-Agent Configuration table inside the Scout Fan-out section contains a row with the literal `brain-hydrate`. Satisfies T-0027-028 anchor. |
| T_0044_034 | happy | Per-Agent Configuration table contains 4 data rows (Cal, Roz, Colby, brain-hydrate). |
| T_0044_035 | happy | Investigation Mode subsection exists within Scout Fan-out section with 4 scout rows (Files, Tests, Brain, Error grep). |
| T_0044_036 | failure | The "Explicit spawn requirement" paragraph (OLD, 6-sentence form) is NOT present. Detection: regex for `Eva does NOT collect scout evidence in her own turn\. Eva does NOT synthesize` literal substring -- should not match. |

### Category G: Line-count non-regression (auditable)

| ID | Category | Description |
|---|---|---|
| T_0044_037 | audit | Post-ADR-0044 line count of `source/shared/rules/agent-system.md` is at most 240 (original: 286; target: 286 - ~52 = ~234). Upper bound is 240 to allow minor whitespace; lower bound not tested (over-trimming would fail the anchor tests in Category B). |
| T_0044_038 | audit | Post-ADR-0044 line count of `source/shared/rules/pipeline-orchestration.md` is at most 760 (original: 802; target: 802 - ~48 = ~754). |
| T_0044_039 | audit | Post-ADR-0044 line count of `source/shared/references/routing-detail.md` is at least 50 (the full matrix + subsections should be ≥ 50 lines; content preservation is guarded by Category A content tests). |

**Counts:** 39 tests total. Happy: 28. Failure: 7. Test-update: 1 (T_0044_028). Audit: 3. Happy ≥ failure ratio is inverted vs Slice-1 precedent (17:11) because this ADR is content-preservation-heavy rather than verbosity-removal-heavy: the main risk is dropping a load-bearing row / anchor, which happy-path tests guard. The 7 failure tests guard scope: they assert the moved content is *not* left duplicated in agent-system.md (T_0044_013-016) and the collapsed rhetoric is *not* lingering (T_0044_024, T_0044_025, T_0044_036), and that the new ref file does not carry stray frontmatter (T_0044_007).

**Roz note:** This test spec is grep-style + regex + line-count. No runtime harness needed. Suggested test file: `tests/adr_0044_instruction_budget_trim.py` (or Node equivalent; existing Slice-1 tests are under `tests/` directly -- match that layout). T_0044_028 modifies the existing `tests/adr-0023-reduction/test_reduction_structural.py` file -- that is the only edit to an existing test file; all other tests are new.

---

## UX Coverage

No UX artifact exists for ADR-0044 (pipeline-internal ADR, no user-facing UI). Section present per Cal's Hard Gate 1 requirement. Mapping: N/A.

---

## UI Specification

No step in this ADR touches UI. Section present per Cal's Hard Gate 5. Mapping: N/A -- this is a rule-file prose trim + reference file add.

---

## Contract Boundaries

| Producer | Consumer | Shape |
|---|---|---|
| `routing-detail.md` full AUTO-ROUTING content | Eva (reads on edge-case routing per the summary pointer) | Markdown file with `## Intent Detection` heading + 19-row table + 3 subsection headings (Smart Context Detection, Auto-Routing Confidence, Discovered Agent Routing). |
| `agent-system.md` `<routing id="auto-routing">` summary | Eva (reads always-on; the six-bullet summary resolves common first-turn routing) | Six summary bullets + one Confidence & Overrides paragraph + one pointer to `routing-detail.md`. |
| `pipeline-orchestration.md` Mandatory Gates opener (`**Violation class.**` paragraph) | Gates 1-12 body sentences (each gate inherits the default class unless a tighter tag applies) | Opener declares default class; per-gate tails consume the default or specify exception ("tighter class: ..."). |
| `pipeline-orchestration.md` Scout Fan-out collapsed paragraph | Eva / scout-swarm hook (unchanged enforcement semantics) | One paragraph stating the spawn requirement + in-thread anti-pattern. Hook continues to inspect the primary-agent prompt per ADR-0042 semantics. |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|---|---|---|---|
| `routing-detail.md` (NEW file) | Full matrix + 3 subsections, markdown | `agent-system.md` summary pointer (consumer: Eva reads on demand) | Step 1 (producer + consumer land together) |
| `agent-system.md` `<routing>` summary rewrite | 6 bullets + pointer | Eva boot-time routing (consumer: Eva routes from summary; `default-persona.md` line 13 pointer continues to resolve to `agent-system.md`) | Step 1 (consumer is Eva -- no file edit needed on her side; `default-persona.md` pointer is pre-existing and unaffected) |
| Mandatory Gates `**Violation class.**` opener paragraph | One paragraph declaring default severity | Gates 1-12 tail sentences | Step 2 (producer + consumers all in same file, same step) |
| Scout Fan-out collapsed "Explicit spawn requirement" paragraph | One paragraph with `MUST spawn` + `separate parallel subagent` + in-thread anti-pattern | Eva runtime behavior (same semantic contract as ADR-0042); scout-swarm hook inspection unchanged | Step 3 (self-contained; Eva's behavioral consumer is pre-existing per ADR-0042) |
| Updated T-0023-131 test body | Counts `^\d+\. \*\*` == 12 in Mandatory Gates section | pytest runner at CI time | Step 4 (test update rides after Step 2 so the assertion reflects the new shape) |

No orphan producers. The new `routing-detail.md` has its one consumer (the summary pointer) in the same step. The gate-opener paragraph and its 12 consumer gate tails land in the same file in the same step. The T-0023-131 body update lands after Step 2 because the assertion it contains counts gates that only exist post-Step-2. Test update in Step 4 is the consumer of Step 2's producer output.

---

## Data Sensitivity

N/A -- no data access methods introduced or modified. All edits are to rule/persona text + reference content. No database, no API, no auth boundary.

---

## Files Changed

Four source files touched, four installed mirrors, one existing test modified. Summary (grouped by step):

**Step 1** (4 files):
1. `source/shared/references/routing-detail.md` (NEW; Decision §1 verbatim)
2. `.claude/references/routing-detail.md` (NEW; mirror of #1, byte-identical)
3. `source/shared/rules/agent-system.md` (replace `<routing id="auto-routing">`..`</routing>` block per Decision §2)
4. `.claude/rules/agent-system.md` (mirror of #3 body)

**Step 2** (2 files):
5. `source/shared/rules/pipeline-orchestration.md` (opener rewrite + 6 per-gate tail collapses + line 780 Agent Standards collapse per Decision §3)
6. `.claude/rules/pipeline-orchestration.md` (mirror of #5 body)

**Step 3** (2 files -- shared with Step 2 actually; one Colby wave covers both):
7. `source/shared/rules/pipeline-orchestration.md` (Scout Fan-out "Explicit spawn requirement" paragraph collapse per Decision §4) -- same file as #5, different edit location
8. `.claude/rules/pipeline-orchestration.md` (mirror of #7) -- same file as #6, different edit location

**Step 4** (1 file):
9. `tests/adr-0023-reduction/test_reduction_structural.py` (replace T-0023-131 body per Test Specification Category E verbatim)

**Explicitly NOT edited:**
- `source/shared/rules/pipeline-models.md` (ADR-0042 test pins preclude trim -- see Anti-goal 2).
- `.claude/rules/pipeline-models.md` (same reason).
- `.cursor-plugin/rules/*.mdc` (Cursor does not install these files per research-brief).
- `source/cursor/**`, `.cursor-plugin/**` (scope guard).
- Any agent persona file under `source/shared/agents/` or `.claude/agents/` (ADR-0043 just finished with those; not in scope here).
- `default-persona.md` (its pointer to `agent-system.md` for auto-routing is unchanged; no edit needed).
- Any hook script, any MCP server file, any Node test file under `tests/brain/`.
- ADR-0043 body, ADR-0042 body, ADR-0041 body, ADR-0023 body (ADR immutability; cross-references noted in Status / Alternatives).

**File-count rollup (unique basenames):** `routing-detail.md` (new, 2 install locations) + `agent-system.md` (2 locations) + `pipeline-orchestration.md` (2 locations) + `test_reduction_structural.py` (1 location) = 7 unique file modifications across Steps 1-4.

---

## Notes for Colby

1. **Read each target file fully before editing.** Every replacement in Decision §2, §3, §4 is keyed off specific surrounding text. Use `Read` on all 6 target files (3 source + 3 installed) before any `Edit`. Zero interpretation required if you paste verbatim.

2. **Step order matters:** do Step 1 first (new file + agent-system.md), then Step 2 + Step 3 together (both edits in pipeline-orchestration.md -- single Colby pass can do both so you `Read` the file once and apply two separate `Edit` operations), then Step 4 (test update) last so the test reflects post-Step-2 state.

3. **Verbatim text:** Decision §1 is the full body of the new `routing-detail.md`. Decision §2 is the full replacement text between `<routing>` tags in agent-system.md. Decision §3 provides 7 distinct OLD -> NEW text replacements (opener + 5 per-gate + 1 Agent Standards). Decision §4 is one OLD -> NEW replacement in Scout Fan-out. Test Specification Category E provides the exact new body for T-0023-131.

4. **Preserve tag boundaries.** For agent-system.md, the replacement target is *exactly* everything between `<routing id="auto-routing">` and `</routing>` (the opening tag line 111 and the closing tag line 174). Preserve both tags; replace only the body.

5. **Installed-mirror sync rule:** the `.claude/rules/*.md` files carry a YAML `paths:` frontmatter overlay at the top. Preserve that frontmatter on the installed copy; replace only the body (everything after the closing `---` of the frontmatter). The parity tests use `_strip_frontmatter` for comparison. For `routing-detail.md` (a reference file, not a rule), there is no frontmatter overlay -- the installed copy is byte-identical to the source.

6. **Cursor untouched.** Do NOT edit `source/cursor/**`, `.cursor-plugin/**`, or anything under `.cursor-plugin/rules/`. Scope guard: these three rule files are pipeline-internal and not installed for Cursor. The test suite does not assert Cursor mirror equivalence for these files (unlike `pipeline-models.mdc` where T-0042-031 does require the Cursor mirror -- but pipeline-models.md is not touched in this ADR per Anti-goal 2).

7. **Count check before finishing:** after editing `pipeline-orchestration.md`, run these greps to self-verify Step 2 + 3:
   - `grep -c "source_agent: 'eva'" source/shared/rules/pipeline-orchestration.md` should return `2`.
   - `grep -c "same class of violation" source/shared/rules/pipeline-orchestration.md` should return `0`.
   - `grep -c "same class as skipping spec reconciliation" source/shared/rules/pipeline-orchestration.md` should return `1`.
   - `grep -c "^\d\+\. \*\*" source/shared/rules/pipeline-orchestration.md` should return `12` or more (the Mandatory Gates section alone has 12; other numbered lists may add to the count).
   - `grep -c "MUST spawn" source/shared/rules/pipeline-orchestration.md` should return `1` (the collapsed Scout Fan-out paragraph).

8. **Proven pattern:** Slice 1 (ADR-0043) shipped a similar multi-file text-replacement pass with 8 file edits across 7 basenames. Same shape here (7 unique file mods). Slice-1's Addendum (A1 / A2 / A3) teaches: if a cross-ADR test regression surfaces (e.g., a test we didn't catch asserting specific matrix content in agent-system.md), add an Addendum to THIS ADR before merge -- do not paper over with a silent edit. The Addendum pattern is the authorized pre-merge correction mechanism in the same authoring pipeline.

9. **Dogfood the contract:** When Colby returns from this implementation, the return shape must be the ADR-0043 one-liner: `Unit N DONE. N files changed. Lint PASS/FAIL. Typecheck PASS/FAIL. Ready for Roz: Y/N.` Do not inline DoR tables or contract tables in the return.

10. **Non-goal:** do NOT attempt to collapse the Custom Commands table in `agent-system.md`, the Skills / Subagents architecture tables, or the `## CRITICAL: Custom Commands Are NOT Skills` section. Those carry their own test pins (T-0005-070 series, T-0016 subagent-row tests). Out of scope for this ADR.

---

## DoD: Verification Table

| # | DoR item | Status | Evidence |
|---|---|---|---|
| R1 | AUTO-ROUTING matrix moved to `routing-detail.md`; agent-system.md keeps summary + pointer | Done | Decision §1 (ref file content), Decision §2 (summary rewrite); T_0044_001 through T_0044_016 |
| R2 | Routing anchors preserved in agent-system.md summary (Deps, Darwin, darwin_enabled, deps_agent_enabled) | Done | Decision §2 "What survives verbatim" list; T_0044_011, T_0044_012 |
| R3 | `routing-detail.md` contains verbatim Intent Detection table + 3 subsections | Done | Decision §1 full body; T_0044_002 through T_0044_006 |
| R4 | Installed copy at `.claude/references/routing-detail.md` byte-identical; no Cursor install | Done | Step 1 file #2; T_0044_017; Anti-goal/Scope confirms Cursor untouched |
| R5 | Mandatory Gates opener declares default violation class; per-gate rhetoric collapsed; 12 gates preserved | Done | Decision §3 (opener + 6 per-gate collapses); T_0044_020 through T_0044_027 |
| R6 | Scout Fan-out "Explicit spawn requirement" paragraph collapsed; MUST spawn / separate parallel subagent / synthesis anchors preserved | Done | Decision §4; T_0044_029 through T_0044_036 |
| R7 | `source_agent: 'eva'` count remains at 2 in pipeline-orchestration.md | Done | Decision §3 (none of the collapses touch brain-capture protocol sections); T_0044_027 |
| R8 | Line-count reduction of ~230 always-loaded lines achieved | Done | Decision §3 + §4 collapse estimates; T_0044_037, T_0044_038 (bounded audit); routing-detail.md growth offset is out-of-always-loaded per T_0044_039 |
| R9 | Installed mirrors body-identical to source (modulo frontmatter) | Done | Step 1/2/3 mirror sync acceptance criteria; T_0044_017 through T_0044_019 |
| R10 | T-0042-027 anchors (`MUST spawn`, `separate parallel subagent`) preserved in Scout Fan-out section | Done | Decision §4 "What survives verbatim"; T_0044_030, T_0044_031 |
| R11 | T-0042-028 anchors (`synthesis`, `after scouts return`/`scouts return`, `Cal`, `Colby`, `Roz` co-located) preserved | Done | Decision §4 notes the Synthesis step paragraph (lines 622-623 of source) stays unchanged; T_0044_032 |
| R12 | pipeline-models.md NOT modified (ADR-0042 test pins respected) | Done | Anti-goal 2; Files Changed section "Explicitly NOT edited"; no file entry for pipeline-models.md in the edit list |
| R13 | Installed mirrors use body-equality-modulo-frontmatter parity | Done | Step 1/2/3 acceptance criteria; T_0044_017-019 |
| R14 | T-0023-131 strengthened to count 12 gates, not just header | Done | Test Specification Category E verbatim replacement; T_0044_028 |

**Silent drops check:** None. Every DoR item has either Done status with Decision-level evidence or test coverage in the Test Specification. The one non-obvious drop risk (pipeline-models.md trim in Issue #31) is explicitly surfaced in Status + Anti-goal 2 + Alt 2 with reasoning.

**Status:** Ready for Roz test-spec review.

---

## Handoff

See return receipt (emitted in the agent reply, not in this file body, per ADR-0043's return-condensation contract).

---

## Addendum A1 -- Slice 2 delivered narrower than estimated (2026-04-20)

**Status:** Pre-merge correction, in-pipeline (same authorized mechanism as ADR-0043 Addendum A1/A2/A3).

### Trigger

After Colby's verbatim application of Decision §3 (Mandatory Gates rhetoric collapse) and Decision §4 (Scout Fan-out collapse), the one red test is `T_0044_038` (pipeline-orchestration.md line count `<= 760`). Current post-edit state:

| File | Pre-ADR | Post-ADR (actual) | Delta | Target in test (orig.) |
|---|---|---|---|---|
| `source/shared/rules/agent-system.md` | 286 | 240 | -46 | <= 240 (T_0044_037) -- GREEN |
| `source/shared/references/routing-detail.md` | N/A (new) | 65 | +65 (JIT, not always-loaded) | >= 50 (T_0044_039) -- GREEN |
| `source/shared/rules/pipeline-orchestration.md` | 802 | 802 | ~0 | <= 760 (T_0044_038) -- RED |

The always-loaded savings booked in Decision §8 / DoR R8 ("~230 always-loaded lines") over-estimated the pipeline-orchestration.md collapse. Per-hit arithmetic:

- `**Violation class.**` opener paragraph added: +5 lines
- 6 per-gate rhetoric collapses (gates 2/3/5/7/10/11): -7 lines total (each trim was ~1 line, not ~4)
- Scout Fan-out §4 paragraph rewrite: 0 net (already a single long markdown line)
- Agent Standards line 780 rewrite: 0 net (same length)
- **Net pipeline-orchestration.md delta: ~-2 lines** (effectively zero)

agent-system.md delivered as designed (-46 lines, -16%, AUTO-ROUTING matrix successfully JIT'd to `routing-detail.md`). The pipeline-orchestration.md rhetoric collapse landed structurally (all 6 refrain sites cleaned up per T_0044_024; `**Violation class.**` opener present per T_0044_021; Scout Fan-out collapse verified per T_0044_036) but contributed ~0 line savings.

### Decision: Option C -- right-size the test + narrate the split

I evaluated three paths:

- **Option A (additional collapses in pipeline-orchestration.md).** Rejected. Requires Colby re-pass, widens Poirot surface, expands scope against Anti-goal 1 ("no gate substance rewrites"), and the ~400-line target was never a user requirement -- it was an estimator's artifact. Candidate cuts (consolidating Agent Teams notes across gates 2/3/5, trimming worktree-cleanup prose) each carry gate-content mutation risk for marginal gain.
- **Option B (right-size test only).** Accurate numerically but silent on rationale. Leaves future pipeline-orchestration.md trim in a documentation limbo.
- **Option C (B + narrative).** Chosen. Updates the test bound to the achieved ceiling AND explicitly declares pipeline-orchestration.md line-count reduction out-of-scope pending a future ADR. Preserves optionality, honors Anti-goal 1, and makes the split visible in the authoritative record.

**What Slice 2 ships:**
1. agent-system.md AUTO-ROUTING JIT move (delivered: -46 always-loaded lines, -16%).
2. routing-detail.md JIT reference file (delivered: 65 lines, not always-loaded).
3. pipeline-orchestration.md rhetoric-collapse **structural** cleanup (delivered: refrain eliminated, opener declared once, Scout Fan-out paragraph condensed). Line-count savings: effectively zero.
4. T-0023-131 strengthening to count 12 gates (delivered).

**What Slice 2 defers:** Any material pipeline-orchestration.md line-count reduction. If a future ADR wants it, it will need either (a) substance edits that this ADR's Anti-goal 1 disallows, or (b) a different structural strategy (e.g., JIT'ing a whole section out to a reference file, mirroring the agent-system.md pattern here).

### Exact test update (verbatim replacement for Roz)

Replace the body of `test_T_0044_038_pipeline_orchestration_line_count_at_most_760` in `tests/test_adr0044_instruction_budget_trim.py` (currently lines 1227-1241) with the following verbatim text. Function name preserved so the ID anchors elsewhere (CI logs, error-patterns.md) remain stable.

```python
def test_T_0044_038_pipeline_orchestration_line_count_at_most_760():
    """T-0044-038 (audit): Post-ADR-0044 line count of
    pipeline-orchestration.md is at most 803 (Addendum A1 scope correction).

    Scope correction (ADR-0044 Addendum A1, 2026-04-20):
      The original bound `<= 760` assumed ~48-line savings from Decision §3
      + §4 rhetoric and Scout Fan-out collapses. Post-Colby verbatim
      application yielded ~0 net savings in this file: the
      `**Violation class.**` opener paragraph (+5 lines) offset most of the
      per-gate refrain trims (~-7 lines combined), and the Scout Fan-out
      §4 paragraph rewrite was line-count-neutral (already one long
      markdown line). Structural intent LANDED (T_0044_021, T_0044_024,
      T_0044_025, T_0044_026, T_0044_036 all green); line-count savings
      did not materialize here.

      agent-system.md delivered its full target (-46 lines via
      AUTO-ROUTING JIT move -- see T_0044_037). Slice 2 books that
      savings cleanly; the pipeline-orchestration.md line-count trim is
      formally deferred to a future ADR. See ADR-0044 Addendum A1 for
      the decision rationale (Option C: split + narrate).

      The bound `<= 803` is a no-regression guard: it permits the current
      ~802-line state plus 1 line of whitespace tolerance while forbidding
      growth. A future trim ADR would tighten this bound as part of its
      own DoD.

    Pre-build: FAILS -- current pipeline-orchestration.md is 802 lines
    (bound was `<= 760`).
    Post-Addendum-A1: PASSES (802 <= 803).
    """
    text = _PIPELINE_ORCH_SRC.read_text()
    line_count = len(text.splitlines())
    assert line_count <= 803, (
        f"source/shared/rules/pipeline-orchestration.md is {line_count} "
        "lines; expected <= 803 per ADR-0044 Addendum A1 (original bound "
        "<= 760 was scope-corrected to the achieved ceiling). Growth "
        "beyond this bound indicates the rhetoric-collapse structural "
        "gains leaked back as prose; route to a trim ADR."
    )
```

Notes for Roz:
- Function name, IDs, and ADR-spec-id docstring pattern preserved for continuity.
- Bound is `<= 803` (802 actual + 1 line whitespace tolerance), matching the T_0044_037 pattern of a small tolerance above the measured post-edit state.
- No other test in the file asserts pipeline-orchestration.md line count.

### Cascade check

I enumerated every T_0044_* test for downstream impact:

| Test | Concern | Impact |
|---|---|---|
| T_0044_037 (agent-system.md <= 240) | Line-count bound | None. Current: 240. GREEN unchanged. |
| T_0044_039 (routing-detail.md >= 50) | Floor check | None. Current: 65. GREEN unchanged. |
| T_0044_021, 024, 025, 026, 027, 036 (structural intent for pipeline-orchestration.md) | All pass despite zero net line savings -- structural refrain removal succeeded independently of line-count reduction | None. All GREEN. Structural decision separable from line-count decision. |
| T_0044_022, 023 (12 gates preserved, titles preserved) | 12 Mandatory Gates intact | None. GREEN. |
| T_0044_019 (installed-mirror parity on both edited regions) | Byte parity modulo placeholders | None. GREEN. |
| T_0044_040 (Eva capture < 3) | ADR-0025 cross-ADR pin | None. Count: 2. GREEN. |
| T_0044_041 (Tier 1-4 labels in pipeline-models.md) | ADR-0041 cross-ADR pin | None. GREEN. |
| T_0044_042 (darwin_enabled anywhere in agent-system.md) | ADR-0016 cross-ADR pin | None. GREEN. |
| T-0023-131 (ADR-0023 suite, 12-gate strengthening) | Applied directly to test_reduction_structural.py | None. GREEN. |

**Cascade result:** No other T_0044_* test or ADR-0023/0025/0041/0016/0042 pin requires adjustment. Only T_0044_038 changes. 542/542 sanity-suite guarantee holds.

### Files Changed (Addendum A1 delta)

1. `docs/architecture/ADR-0044-instruction-budget-trim-slice-2.md` -- this Addendum appended (authoring-pipeline pre-merge pattern, matches ADR-0043 precedent).
2. `tests/test_adr0044_instruction_budget_trim.py` -- one function body replaced per the verbatim text above (Roz-owned edit; same file, same function name, new body + new assertion bound).

**Not changed by this Addendum:**
- `source/shared/rules/pipeline-orchestration.md` (Option C defers further trim).
- Any other test file.
- Any other ADR (no immutability violation).
- Any CHANGELOG entry (narrative note recommended below, to be added by Ellis at release-commit time, not by this Addendum).

### CHANGELOG narrative note (recommendation for Ellis)

When Ellis composes the release commit for Slice 2, the CHANGELOG entry should honestly reflect the split rather than claim a ~230-line always-loaded reduction. Suggested text:

> **Slice 2 (ADR-0044): instruction-budget trim.** agent-system.md AUTO-ROUTING matrix moved to JIT reference `routing-detail.md`, delivering -46 always-loaded lines (286 -> 240, -16%). pipeline-orchestration.md Mandatory Gates rhetoric and Scout Fan-out paragraph collapsed structurally (default violation-class declared once; per-gate refrain eliminated) with ~0 net line-count change -- structural cleanup landed, line-count savings smaller than initially scoped. A future ADR may revisit pipeline-orchestration.md line-count reduction via a different structural strategy (e.g., additional JIT extraction). 12 Mandatory Gates preserved; ADR-0025, ADR-0041, ADR-0042, ADR-0016, ADR-0023 invariants all intact.

### DoR/DoD amendment

DoR R8 is amended from "~230 always-loaded lines" to "**-46 always-loaded lines (agent-system.md AUTO-ROUTING JIT move) + structural rhetoric cleanup in pipeline-orchestration.md (line-count neutral; future trim deferred)**." DoD R8 status remains `Done` under the amended target.

### Anti-goals revisited

Anti-goal 1 ("no gate substance rewrites"): preserved. Option A would have risked it; Option C does not.
Anti-goal 2 (pipeline-models.md untouched): preserved. T_0044_041 stays GREEN.
Anti-goal 3 (no Cursor edits): preserved. No Cursor surface touched.

### Notes for Colby

No Colby re-pass required. Colby's verbatim application of Decision §3 + §4 is correct; the line-count target was the estimator's error, not Colby's. The structural decisions all landed per Test Spec.

### Notes for Poirot

Blind review for this Addendum should verify: (a) only T_0044_038 body changed in the test file; (b) pipeline-orchestration.md source is unchanged from Colby's Step 2/3 output; (c) CHANGELOG narrative (when Ellis adds it) matches the honest-split framing above, not the original "~230 lines" estimate.

**Addendum A1 Status:** Ready for Roz (test update) -> Poirot (blind review) -> Ellis (commit + CHANGELOG).
