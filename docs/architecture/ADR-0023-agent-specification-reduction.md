# ADR-0023: Agent Specification Reduction -- Constraints Over Procedures

## DoR: Requirements Extracted

**Sources:** Conversation analysis (Eva/user audit session 2026-04-03), ADR-0022 (Wave 3 enforcement redesign -- prerequisite), Anthropic API documentation (prompting best practices, model capabilities), Claude Code documentation (CLAUDE.md guidance, sub-agents, hooks), brain context (5 retro lessons, 15 design decisions from Wave 3 session), agent persona files (12 core agents), invocation-templates.md (806 lines, 25 templates), pipeline-orchestration.md (952 lines), default-persona.md (283 lines), pipeline-models.md (139 lines)

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Remove procedural instructions that teach generic software engineering competencies Opus already has from training | Audit finding | "Opus is 'the most intelligent model for building agents and coding' with 'exceptional performance in coding and reasoning'" -- Anthropic model docs |
| R2 | Remove behavioral path/tool restriction text made redundant by ADR-0022's three-layer enforcement pyramid | ADR-0022 dependency | Layer 1 tools/disallowedTools + Layer 2 frontmatter hooks + Layer 3 global hooks mechanically enforce what persona text currently specifies behaviorally |
| R3 | Retain all project-specific constraints, output formats, design principles, and conventions that Opus cannot derive from training | Audit finding | Information asymmetry, DoR/DoD format, contract tables, step sizing gates, TDD-first, PASS/DRIFT/MISSING/AMBIGUOUS vocabulary |
| R4 | Upgrade examples from generic competency demonstrations to project-specific judgment calibration | Anthropic API docs + audit finding | "Examples are one of the most reliable ways to steer output format, tone, and structure" -- but only when they demonstrate judgment calls the model would get wrong without them |
| R5 | Scale example density by model tier: Opus 0-1, Sonnet 1-2, Haiku 2 | Audit finding | No documented model-specific guidance, but empirical: Sonnet benefits from judgment calibration examples, Haiku from compliance examples, Opus from counter-intuitive constraint examples only |
| R6 | Consolidate repeated brain capture protocol into agent-preamble.md; keep only agent-specific thought_types in personas | Audit finding | Brain Access protocol (~28 lines) is repeated verbatim across Cal, Colby, Roz, Agatha with only thought_type and importance differing |
| R7 | Move step sizing gate (S1-S5) from Cal's persona to a shared reference file | Audit finding | Reusable framework referenced by Cal and Darwin; 40 lines in Cal persona, not agent identity |
| R8 | Collapse invocation-templates.md: extract shared patterns to header, remove repeated brain-context XML blocks, remove persona-constraint duplicates | Audit finding | Brain-context tag repeated 15 times (~200 lines); retro-lessons.md + agent-preamble.md in every READ list (~50 lines); constraint bullets duplicating persona files (~100 lines) |
| R9 | Remove "How X Fits the Pipeline" sections from agent personas | Audit finding | Routing information is Eva's concern, not the agent's identity. Agents are invoked by Eva; they don't self-invoke. |
| R10 | Remove explicit tool lists from persona body text when redundant with frontmatter | ADR-0022 dependency | Post-Wave 3, tools/disallowedTools in frontmatter is the single source of truth for tool access |
| R11 | Move deterministic boot sequence steps (1-3d) to a SessionStart hook script | Audit finding | Steps 1-3d are file reads and env var checks requiring zero LLM reasoning; currently ~70 lines of behavioral instructions in default-persona.md |
| R12 | Fold CI Watch invocation templates (roz-ci-investigation, colby-ci-fix, roz-ci-verify) into their base template variants | Audit finding | CI Watch templates are minor variations of roz-investigation, colby-build, roz-scoped-rerun with CI-specific context injection |
| R13 | ADR-0022 Phase 2 must be complete and stable before this work begins | Sequencing constraint | This ADR depends on Layer 2 frontmatter hooks being operational; without them, removing behavioral path restrictions would leave enforcement gaps |
| R14 | Preserve Distillator's specification density (Haiku model needs procedural guidance) | Audit finding + model docs | Haiku is the smallest model tier; compress/strip/preserve rules are essentially a "prompt program" for a smaller model |
| R15 | Preserve TDD-specific instructions for Colby and Roz regardless of model tier | Anthropic docs | "Claude's default is implementation-first rather than test-first" -- TDD workflow requires explicit specification |

**Retro risks:**

- **Lesson #002 (Self-Reporting Bug Codification):** Directly relevant. "Do not modify Roz's assertions" is a constraint that MUST survive reduction. The lesson proves behavioral constraints can be effective for critical rules when reinforced by mechanical enforcement (Roz's Write-only tool access).
- **Lesson #003 (Stop Hook Race Condition):** Relevant to R11. Boot sequence hook must follow the same lightweight pattern: exit 0 always, no blocking, no complex logic. JSON output to stdout, not file writes.
- **Lesson #005 (Frontend Wiring Omission):** Relevant. Contract tables, vertical slice preference, and cross-layer wiring check are all project-specific conventions that must survive reduction per R3.

**Spec challenge:** This ADR assumes Opus performs generic software engineering tasks (ADR writing, code review, debugging, dependency scanning) as well as or better than the procedural instructions currently in agent personas. If Opus's performance degrades when procedural guidance is removed, the reduction was too aggressive. **Are we confident?** Partially. The Anthropic docs confirm Opus's capabilities but don't publish a "generic competencies" list. Mitigation: Phase 2 includes a telemetry comparison gate -- if first-pass QA rate drops >10% after reduction, the specific agent is reverted and the procedure is reclassified as project-specific.

**SPOF:** The telemetry comparison gate (Phase 2, Step 2e). If the brain is unavailable during the comparison window (first 3 pipelines after reduction), there's no baseline to compare against. **Failure mode:** We can't detect whether the reduction caused quality regression. **Graceful degradation:** Roz QA still catches issues per-wave; the pipeline doesn't lose safety, just loses the ability to measure the impact of the change. Manual review of Roz's first 3 post-reduction QA reports serves as a fallback signal.

**Anti-goals:**

1. **Anti-goal: Reducing Distillator or Haiku-tier agent specification.** Reason: Haiku models need more procedural guidance, not less. The reduction targets Opus and Sonnet agents only (except for generic/routing sections that are model-independent). Revisit: If Haiku is replaced by a more capable model tier.

2. **Anti-goal: Removing project-specific output format templates (DoR/DoD, contract tables, QA report structure).** Reason: Output formats are conventions Opus cannot derive from training. They are the primary mechanism for structured agent-to-agent communication. Revisit: Never -- these are the pipeline's data contracts.

3. **Anti-goal: Automating the reduction (Darwin-driven).** Reason: This reduction requires human judgment about what constitutes "generic competence" vs "project convention." Darwin can measure the impact after reduction, but the classification decision is human. Revisit: If Darwin develops a validated methodology for classifying specification as generic vs project-specific.

---

## Status

Proposed

## Context

The atelier-pipeline agent system totals ~7,800 lines of specification across agent personas (2,392), rules (1,771), commands (1,171), and references (2,447). An audit against Claude Code's documented guidance, Anthropic's model capability documentation, and ADR-0022's enforcement redesign revealed that approximately 60% of agent persona content falls into two categories:

**Category 1: Generic procedures.** Step-by-step instructions that teach the model competencies it already has from training. Examples: "Run grep for every function being changed" (Cal blast radius), "Trace the full request path: frontend call -> API route -> handler -> data access" (Roz investigation), the 8-category code review checklist (Poirot). Opus performs these tasks at or above the quality described in the instructions without them.

**Category 2: Redundant behavioral restrictions.** Text that says "you may only write to X" or "do not modify files outside Y" -- now mechanically enforced by ADR-0022's three-layer pyramid (Layer 1 tools/disallowedTools, Layer 2 per-agent frontmatter hooks, Layer 3 global hooks). After ADR-0022, these instructions consume context window without adding enforcement value.

The remaining ~40% is **project-specific delta**: conventions, output formats, design principles, and constraints that Opus cannot derive from training (information asymmetry, DoR/DoD format, contract tables, step sizing gates, TDD-first workflow, PASS/DRIFT/MISSING/AMBIGUOUS vocabulary).

Anthropic's documentation gives two relevant but tensioned guidance points:
- API docs: "Be specific. Provide examples. 3-5 examples dramatically improve accuracy."
- Claude Code docs: "Longer files consume more context and reduce adherence."

The resolution: **fewer, better-targeted specifications.** Constraints over procedures. Conventions over competencies. Format over methodology. Examples that calibrate judgment, not demonstrate compliance.

### Why After ADR-0022

ADR-0022's enforcement redesign is a hard prerequisite. Without Layer 2 frontmatter hooks mechanically enforcing path restrictions, removing behavioral path restriction text from agent personas would create enforcement gaps. The sequencing is:

1. ADR-0022 Phase 1 (source split) -- structural foundation
2. ADR-0022 Phase 2 (enforcement redesign) -- mechanical enforcement active
3. **ADR-0023 (this work)** -- remove behavioral text that enforcement makes redundant

## Decision

Reduce agent specification by ~57% through two sequential phases: structural reduction (personas, templates, references) and validation (telemetry comparison over 3 pipelines).

### Reduction Principles

1. **Constraints over procedures.** Tell the agent what's different about your project, not how to do its job. "Assert what code SHOULD do, not what it currently does" stays. "Trace entry -> API -> handler -> data -> response" goes.

2. **Conventions over competencies.** Keep project-specific vocabulary (PASS/DRIFT/MISSING/AMBIGUOUS), output formats (DoR/DoD, contract tables), and design principles (information asymmetry, vertical slices). Remove generic software engineering methodology.

3. **Format over methodology.** Keep structured output templates. Remove the procedures that produce them -- Opus generates the content; the template ensures consistent structure.

4. **Examples calibrate judgment, not demonstrate compliance.** An example earns its context budget only if it demonstrates a judgment call the model would get wrong without seeing it. Generic retrieval patterns ("grep before assuming") fail this test. Judgment restraint ("looks wrong but isn't -- here's how to tell") passes it.

5. **Model tier determines density.** Opus agents get minimal specification (constraints + format + 0-1 examples). Sonnet agents get moderate specification (constraints + format + key procedures + 1-2 examples). Haiku agents retain current density.

### Phase 1: Structural Reduction (12 steps)

#### Step 1a: Extract shared brain capture protocol to agent-preamble.md

Move the brain capture protocol shared across Cal, Colby, Roz, and Agatha into `agent-preamble.md` as a new `<protocol id="brain-capture">` section. Each agent's persona retains only a 2-line pointer plus their agent-specific `thought_type` and `importance` values.

**Files to modify:**
- `source/shared/references/agent-preamble.md` (add shared protocol, ~20 lines)
- `source/shared/agents/cal.md` (replace ~28 lines with ~4 lines)
- `source/shared/agents/colby.md` (replace ~27 lines with ~4 lines)
- `source/shared/agents/roz.md` (replace ~27 lines with ~4 lines)
- `source/shared/agents/agatha.md` (replace ~20 lines with ~4 lines)

**Acceptance criteria:**
- agent-preamble.md contains shared brain capture protocol with placeholder for agent-specific values
- Each agent persona's Brain Access section is <=6 lines (pointer + thought_types + importance values)
- No information lost -- all capture gates preserved
- Total lines saved: ~80

#### Step 1b: Extract step sizing gate to shared reference file

Move Cal's S1-S5 step sizing gate and split heuristics to a new `source/shared/references/step-sizing.md`. Cal's persona gets a one-line reference.

**Files to create:**
- `source/shared/references/step-sizing.md` (~45 lines -- gate table, split heuristics, evidence, Darwin review trigger)

**Files to modify:**
- `source/shared/agents/cal.md` (replace ~40 lines with 1-line reference: "Apply step sizing gate from `.claude/references/step-sizing.md`")

**Acceptance criteria:**
- step-sizing.md contains S1-S5 table, split heuristics table, evidence paragraph, Darwin review trigger
- Cal persona references it by path
- Darwin persona can also reference it (already reads Cal's persona; now has a direct path)

#### Step 1c: Reduce Cal persona -- remove generic procedures, upgrade examples

Remove from Cal:
- ADR Production steps 1-4 intro ("Understand, produce alternatives, break into steps") -- generic architecture
- State Machine Analysis section -- generic competency; condense to one constraint line: "For entities with status fields, include state transition table with stuck-state analysis"
- Blast Radius Verification procedure -- generic; "Map blast radius" is already in constraints
- Migration & Rollback section -- generic; condense to one constraint line: "If schema/state changes, include migration plan + single-step rollback strategy"
- All 3 current examples (generic retrieval patterns)

Add to Cal:
- 1 new example demonstrating the spec challenge + SPOF analysis pattern (project-specific judgment)

Condense:
- Test Specification section (10->4 lines)
- Test Spec Review Loop (14->5 lines)
- Scope-Changing Discovery (8->3 lines)
- Output template (55->30 lines -- keep skeleton, drop inline commentary)

**Files to modify:**
- `source/shared/agents/cal.md`

**Acceptance criteria:**
- Cal persona <=120 lines (currently 315)
- Zero project-specific constraints lost
- 1 example demonstrating spec challenge + SPOF (non-obvious judgment pattern)
- Hard gates 1-4 preserved verbatim
- Vertical slice preference preserved verbatim
- Anti-goals requirement preserved

#### Step 1d: Reduce Colby persona -- remove generic procedures, upgrade examples

Remove from Colby:
- Retrieval-led reasoning required-actions text -- Opus baseline behavior
- Mockup Mode step-by-step -- generic UI dev; condense to 3-line constraint
- Build Mode steps 1-6 -- generic TDD; condense to constraint: "Run Roz's tests first (confirm they fail), implement to pass them, lint+typecheck, output DoD"
- Architectural Consultation procedure -- condense to 1-line constraint: "Spawn Cal for architectural ambiguity, one question per invocation"
- All 3 current examples (generic retrieval)

Add to Colby:
- 1 example demonstrating premise verification in fix mode (non-obvious: "verify root cause against actual code before implementing fix")

Condense:
- Per-Unit QA Loop (16->5 lines)
- Brain Access (27->4 lines via Step 1a)
- Output template (54->25 lines)

**Files to modify:**
- `source/shared/agents/colby.md`

**Acceptance criteria:**
- Colby persona <=95 lines (currently 237)
- "Make Roz's tests pass, do not modify her assertions" preserved verbatim
- Contract Produced/Consumed tables preserved in output template
- Premise verification section preserved
- TDD constraint explicit per R15
- 1 example demonstrating premise verification judgment

#### Step 1e: Reduce Roz persona -- remove generic procedures, keep judgment examples

Remove from Roz:
- Investigation Mode trace steps 1-6 -- generic debugging
- Layer Awareness table -- generic
- Test Authoring step-by-step (20 lines) -- generic TDD

Keep (explicitly):
- Both current examples (judgment restraint -- "looks wrong but isn't") -- these are the strongest examples in the system per R4

Condense:
- Investigation output format (12->6 lines)
- Test Authoring to constraint-level: "Assert domain-correct behavior, not current code behavior. Flag ambiguous domain intent."
- Brain Access (27->4 lines via Step 1a)
- Output template (42->25 lines)

**Files to modify:**
- `source/shared/agents/roz.md`

**Acceptance criteria:**
- Roz persona <=100 lines (currently 242)
- Both current examples preserved (judgment restraint calibration)
- "Assert what SHOULD do, not what DOES" preserved verbatim
- Reference to qa-checks.md preserved
- TDD constraint explicit per R15

#### Step 1f: Reduce remaining agent personas

Apply the reduction principles to Ellis, Agatha, Robert, Sable, Poirot, Sentinel, Darwin, and Deps:

| Agent | Current | Target | Key Removals | Key Preservations | Example Strategy |
|-------|---------|--------|-------------|-------------------|-----------------|
| **Ellis** | 134 | <=65 | Standard process step-by-step; both examples (generic) | QA verification; commit format; per-unit vs final distinction | Replace with 1 example: per-unit vs final commit judgment |
| **Agatha** | 128 | <=55 | Generic doc writing procedure; examples | Doc-type constraints; doc plan reference | Replace with 1 example: flagging spec-vs-code divergence |
| **Robert** | 149 | <=60 | Code/Doc Review procedures; "How Robert Fits"; Design Principle prose; 1 example (constraint compliance) | Information asymmetry constraint; PASS/DRIFT/MISSING/AMBIGUOUS; output format | Keep 1 example: DRIFT detection via grep (info asymmetry discipline) |
| **Sable** | 146 | <=60 | Review procedures; "How Sable Fits"; Design Principle prose; 1 example | Information asymmetry; five-state audit; a11y audit; output format | Keep 1 example: five-state audit finding (project-specific) |
| **Poirot** | 164 | <=65 | Review Process steps 1-5 (8-category checklist); Design Principle prose; severity definitions; both examples (generic) | Information asymmetry; min 5 findings; cross-layer wiring check | Replace with 1 example: cross-layer wiring finding (project-specific) |
| **Sentinel** | 174 | <=65 | Scan/Interpret/Report phases; Tools section; severity definitions; both examples | Information asymmetry; CWE/OWASP requirement; pre-existing filtering; min 3 findings | Keep 1 example: downgrading BLOCKER due to existing mitigation (judgment) |
| **Darwin** | 259 | <=100 | Phase 1-4 procedures; 2 of 3 examples; Tools section | Fitness table; fix layer table; escalation ladder; self-edit protection; conservative default | Keep 1 example: escalation when constraint failed (project-specific ladder) |
| **Deps** | 267 | <=90 | Phase 1-3 procedures; edge case handling; Tools section; 2 of 3 examples | Risk classification table; conservative labeling; bash command safety | Keep 1 example: breakage prediction with grep evidence (full flow) |
| **Distillator** | 177 | <=140 | "How Distillator Fits"; examples only | Transform rules; strip/preserve lists; round-trip validation; output format | Keep both examples (Haiku -- needs compliance grounding per R14) |

**Files to modify:**
- `source/shared/agents/ellis.md`
- `source/shared/agents/agatha.md`
- `source/shared/agents/robert.md`
- `source/shared/agents/sable.md`
- `source/shared/agents/investigator.md`
- `source/shared/agents/sentinel.md`
- `source/shared/agents/darwin.md`
- `source/shared/agents/deps.md`
- `source/shared/agents/distillator.md` (minimal changes)

**Acceptance criteria:**
- Each agent meets its target line count (+-10%)
- Zero project-specific constraints lost across any agent
- Information asymmetry constraints preserved verbatim for Robert, Sable, Poirot, Sentinel
- Every agent has >=1 `<examples>` section with >=1 example
- All output format templates preserved (structure intact, inline commentary removed)
- No changes to frontmatter (model, tools, disallowedTools, effort, maxTurns, mcpServers)

#### Step 1g: Reduce invocation-templates.md -- extract shared patterns, remove duplication

**Extract to header (lines 1-40):**
- Brain-context injection protocol: "Eva injects brain context via `<brain-context>` tag using `agent_search` results. Tags with no content are omitted."
- Standard READ items: "Eva always includes `.claude/references/retro-lessons.md` and `.claude/references/agent-preamble.md` in every invocation READ list. These are not listed per-template."
- Persona constraint note: "Agent persona constraints apply to every invocation. Templates specify only per-invocation variables: task, context, read list, and invocation-specific constraints."

**Remove from each template:**
- Brain-context XML example blocks (repeated 15 times)
- `retro-lessons.md` and `agent-preamble.md` from READ lists
- Constraint bullets that duplicate persona constraints
- "How X Fits" context paragraphs

**Fold CI Watch templates:**
- Merge `roz-ci-investigation` into `roz-investigation` as a "CI Watch variant" annotation
- Merge `colby-ci-fix` into `colby-build` as a "CI Watch variant" annotation
- Merge `roz-ci-verify` into `roz-scoped-rerun` as a "CI Watch variant" annotation

**Move out of templates:**
- `agent-teams-task` template to `pipeline-operations.md` (it's a TaskCreate format, not an Agent invocation)
- `dashboard-bridge` template removed (it's a Bash command Eva runs directly)

**Files to modify:**
- `source/shared/references/invocation-templates.md`

**Acceptance criteria:**
- invocation-templates.md <=300 lines (currently 806)
- Template index updated (25->20 templates after folding)
- Each remaining template is 8-15 lines (task + context + read + constraints + output)
- No invocation-specific context lost (per-step contracts, CI failure logs, etc.)
- Shared header explains brain-context, standard READ, and persona-constraint protocol

#### Step 1h: Create session-boot.sh hook script

Create a SessionStart hook script that handles deterministic boot steps currently in Eva's behavioral instructions (default-persona.md steps 1-3d).

**The script:**
- Reads `docs/pipeline/pipeline-state.md` -- extracts PIPELINE_STATUS JSON
- Reads `docs/pipeline/context-brief.md` -- checks if feature matches pipeline-state
- Reads `docs/pipeline/error-patterns.md` -- counts entries with Recurrence >= 3
- Reads `.claude/pipeline-config.json` -- extracts branching_strategy, agent_teams_enabled, project_name, ci_watch_enabled, darwin_enabled, dashboard_mode, sentinel_enabled, deps_agent_enabled
- Counts non-core agent files in `.claude/agents/`
- Checks `CLAUDE_AGENT_TEAMS` env var
- Outputs structured JSON summary to stdout

**Files to create:**
- `source/shared/hooks/session-boot.sh` (~65 lines)

**Files to modify:**
- `source/shared/rules/default-persona.md` (replace steps 1-3d with "Parse session-boot.sh output"; retain steps 4-6 for brain interactions and announcement)

**Acceptance criteria:**
- Hook outputs valid JSON with: pipeline_active, phase, feature, stale_context, warn_agents[], branching_strategy, agent_teams_enabled, agent_teams_env, custom_agent_count, ci_watch_enabled, darwin_enabled, dashboard_mode, project_name
- Hook exits 0 always (even if files are missing -- outputs defaults)
- Hook follows retro lesson #003: lightweight, no blocking, no brain calls
- Eva's boot sequence in default-persona.md reduced by ~70 lines
- Eva still handles steps 4-6 (brain health check, brain context retrieval, announcement synthesis)

#### Step 1i: Slim down pipeline-orchestration.md and pipeline-models.md

**pipeline-orchestration.md (952 lines -> target ~650):**
- Remove procedural prose from telemetry capture protocol where it restates the tier definitions
- Condense CI Watch protocol (verbose edge case handling that Opus can reason about)
- Condense Darwin auto-trigger (procedural steps Opus derives from constraints)
- Condense pattern staleness check and dashboard bridge sections
- Preserve: mandatory gates (verbatim), observation masking receipts, brain capture model, investigation discipline, phase sizing rules, pipeline flow diagram

**pipeline-models.md (139 lines -> keep as-is):**
- Already structured as decision tables. No procedural content. Model-correct specification.

**Files to modify:**
- `source/shared/rules/pipeline-orchestration.md`

**Acceptance criteria:**
- pipeline-orchestration.md <=650 lines
- All 12 mandatory gates preserved verbatim (grep for "Eva NEVER Skips" header and count numbered items)
- All observation masking receipt formats preserved
- Telemetry tier definitions preserved; procedural capture steps condensed
- No changes to pipeline-models.md

#### Step 1j: Update SKILL.md and /pipeline-setup for new reference file

Register `step-sizing.md` in the installation manifest so `/pipeline-setup` copies it to target projects.

**Files to modify:**
- `SKILL.md` (add step-sizing.md to references list)
- Skills pipeline-setup logic (add step-sizing.md to copy list)

**Acceptance criteria:**
- `/pipeline-setup` copies step-sizing.md to target project's `.claude/references/`
- SKILL.md lists step-sizing.md
- Hook registration for session-boot.sh added to SKILL.md settings.json template (SessionStart event)

#### Step 1k: Update tests for new reference file and hook

- Write bats tests for session-boot.sh (JSON output validation, missing file handling, exit 0 guarantee)
- Update any existing tests that reference line counts or section names in modified agent personas

**Files to create:**
- `tests/hooks/session-boot.bats` (~25 tests)

**Files to modify:**
- Existing test files referencing modified personas (if any assert specific content)

**Acceptance criteria:**
- session-boot.sh has >=25 bats tests covering: valid JSON output, missing pipeline-state.md, missing config, missing agents dir, correct custom agent count, env var detection
- All existing bats tests pass
- Hook exits 0 in every test case

#### Step 1l: Verify all reductions and run full test suite

Final integration verification:

**Acceptance criteria:**
- Total agent persona lines across 12 agents <=935 (currently 2,392) -- target 57% reduction
- Total invocation-templates.md <=300 lines (currently 806)
- Total default-persona.md boot sequence <=30 lines (currently ~100)
- All bats tests pass: `bats tests/hooks/`
- All brain tests pass: `cd brain && node --test ../tests/brain/*.test.mjs`
- `/pipeline-setup` installs all new and modified files correctly
- Every agent persona has >=1 example (except Distillator which keeps 2)
- Spot-check: assemble 3 agent personas (Cal, Colby, Roz) from source/shared + source/claude overlay and verify the assembled file is valid markdown with correct frontmatter

---

### Phase 2: Validation (3 pipelines)

#### Step 2a: Establish baseline metrics

Before the first pipeline on the reduced specifications, record from brain telemetry (Tier 3):
- Per-agent first-pass QA rate (last 5 pipelines)
- Per-agent rework rate (last 5 pipelines)
- Per-agent finding counts from Roz and Poirot
- Total pipeline cost average

**Acceptance criteria:**
- Baseline metrics captured to brain via `agent_capture` with `thought_type: 'decision'`, `source_phase: 'telemetry'`, metadata: `{ baseline_for: 'ADR-0023', metrics: {...} }`

#### Step 2b: Run 3 pipelines on reduced specifications

No code changes in this step. Normal pipeline operation on any features. Eva and all agents operate on the reduced personas. Telemetry captures normally per Tier 1-3 protocol.

**Acceptance criteria:**
- 3 pipelines completed with Tier 3 telemetry captured
- No manual intervention required due to specification gaps (agents completing tasks without confusion)

#### Step 2c: Compare and evaluate

After 3 pipelines, compare post-reduction metrics against baseline:

| Metric | Regression Threshold | Action if Exceeded |
|--------|---------------------|-------------------|
| First-pass QA rate (per agent) | Drop >10% from baseline | Revert that agent's persona; reclassify removed content as project-specific |
| Rework rate (per agent) | Increase >0.5 from baseline | Investigate which removed section caused the regression |
| Poirot finding severity | Increase in BLOCKER count >50% | Investigate Poirot's reduced persona specifically |
| Pipeline cost | Increase >20% | Investigate whether agents are spending more turns compensating for missing guidance |

**Acceptance criteria:**
- Comparison report produced with per-agent deltas
- Any agent exceeding regression threshold has specific remediation plan
- If no regressions: ADR-0023 marked "Accepted"
- If regressions: specific sections reverted, ADR-0023 marked "Accepted with amendments" listing reverted sections

---

## Alternatives Considered

### Alternative 1: Proportional reduction (cut 30% across all agents evenly)

Reduce each agent by a fixed percentage without distinguishing between procedure and constraint.

**Rejected.** Equal treatment ignores that some agents have more procedural bloat than others (Deps at 267 lines vs Ellis at 134). It would cut useful constraints from lean agents while leaving unnecessary procedures in bloated ones. The audit showed the cut/keep boundary is content-type (procedure vs constraint), not proportional.

### Alternative 2: Model-tier-only reduction (cut Opus agents, leave Sonnet/Haiku unchanged)

Only reduce agents that run on Opus, since Opus has the strongest baseline capabilities.

**Rejected.** Most agents run on Sonnet (Colby, Roz, Robert, Sable, Poirot, Sentinel, Deps). Leaving Sonnet agents unchanged would miss the majority of the reduction opportunity. The audit showed that even Sonnet agents contain generic procedures (Roz's trace steps, Poirot's 8-category checklist) that can be safely removed. The model-tier-appropriate approach is to adjust *example density*, not specification scope.

### Alternative 3: Defer until Darwin can automate the analysis

Wait for Darwin to develop telemetry-based methodology for identifying over-specified agent sections.

**Rejected.** Darwin measures outcomes (first-pass QA rate, rework rate) but cannot classify whether a specification line is "generic competence" vs "project convention" -- that requires understanding what the model already knows from training, which is a human judgment. Darwin will be valuable for Phase 2 validation but cannot replace the audit that produced the reduction plan.

## Consequences

**Positive:**
- ~2,000 lines reclaimed from agent context windows, reducing competition between instructions and task context
- Agent personas become primarily constraints + conventions + format, making them easier to maintain and audit
- New `step-sizing.md` reference is reusable across Cal and Darwin without duplication
- SessionStart hook eliminates ~70 lines of behavioral boot instructions that could be lost during compaction
- Invocation templates become concise per-invocation variable sheets rather than persona-constraint duplicates

**Negative:**
- Risk of regression if "generic competence" classification was wrong for specific procedures (mitigated by Phase 2 telemetry gate)
- Smaller agent personas may feel "under-specified" to human readers even if model performance is equivalent or better
- Session-boot.sh adds a new hook to maintain; must follow retro lesson #003 patterns

**Neutral:**
- Total reference file count increases by 1 (step-sizing.md); total hook count increases by 1 (session-boot.sh)
- pipeline-orchestration.md reduction is moderate (~30%) because most content is mandatory gates and protocol definitions that are genuinely project-specific

---

## Comprehensive Test Specification

### Phase 1 Tests

#### Step 1a Tests (agent-preamble.md + brain protocol extraction)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-001 | Happy | agent-preamble.md contains `<protocol id="brain-capture">` section with shared capture protocol |
| T-0023-002 | Happy | Cal persona Brain Access section is <=6 lines and references agent-preamble.md |
| T-0023-003 | Happy | Colby persona Brain Access section is <=6 lines and references agent-preamble.md |
| T-0023-004 | Happy | Roz persona Brain Access section is <=6 lines and references agent-preamble.md |
| T-0023-005 | Happy | Agatha persona Brain Access section is <=6 lines and references agent-preamble.md |
| T-0023-006 | Boundary | Cal persona retains `thought_type: 'decision'` and `thought_type: 'pattern'` with correct importance values |
| T-0023-006a | Boundary | Roz persona retains `thought_type: 'pattern'` and `thought_type: 'lesson'` with correct importance values |
| T-0023-006b | Boundary | Agatha persona retains `thought_type: 'decision'` and `thought_type: 'insight'` with correct importance values |
| T-0023-007 | Boundary | Colby persona retains `thought_type: 'insight'` and `thought_type: 'pattern'` with correct importance values |
| T-0023-008 | Regression | agent-preamble.md step 4 brain context review still references `mcpServers: atelier-brain` agents list |

#### Step 1b Tests (step-sizing.md extraction)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-010 | Happy | step-sizing.md exists in `source/shared/references/` and contains S1-S5 table |
| T-0023-011 | Happy | step-sizing.md contains split heuristics table |
| T-0023-012 | Happy | step-sizing.md contains evidence paragraph with 57%->93% data |
| T-0023-013 | Happy | step-sizing.md contains Darwin review trigger |
| T-0023-014 | Happy | Cal persona references step-sizing.md by path |
| T-0023-015 | Regression | Cal persona does NOT contain the S1-S5 table inline (moved, not duplicated) |

#### Step 1c Tests (Cal reduction)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-020 | Happy | Cal persona <=120 lines |
| T-0023-021 | Happy | Cal persona contains "spec challenge" and "SPOF" in required-actions |
| T-0023-022 | Happy | Cal persona contains all 4 hard gates |
| T-0023-023 | Happy | Cal persona contains vertical slice preference text |
| T-0023-024 | Happy | Cal persona contains anti-goals requirement |
| T-0023-025 | Happy | Cal persona has exactly 1 example demonstrating spec challenge + SPOF pattern |
| T-0023-026 | Regression | Cal persona does NOT contain "State Machine Analysis" as a section header |
| T-0023-027 | Regression | Cal persona does NOT contain "Blast Radius Verification" as a section header |
| T-0023-028 | Regression | Cal persona does NOT contain "Migration & Rollback" as a section header |
| T-0023-029 | Boundary | Cal persona output template retains: DoR, ADR skeleton, UX Coverage, Wiring Coverage, Contract Boundaries, Notes for Colby, DoD |

#### Step 1d Tests (Colby reduction)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-030 | Happy | Colby persona <=95 lines |
| T-0023-031 | Happy | Colby persona contains "Make Roz's pre-written tests pass" verbatim |
| T-0023-032 | Happy | Colby persona contains "do not modify" + "assertions" (anti-modification constraint) |
| T-0023-033 | Happy | Colby persona contains Contracts Produced table in output template |
| T-0023-034 | Happy | Colby persona contains premise verification section |
| T-0023-035 | Happy | Colby persona has exactly 1 example demonstrating premise verification |
| T-0023-036 | Regression | Colby persona does NOT contain "Retrieval-led reasoning" as the opening sentence of required-actions |
| T-0023-037 | Boundary | Colby persona TDD constraint is explicit (contains "test" + "fail" + "implement" in same section) |

#### Step 1e Tests (Roz reduction)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-040 | Happy | Roz persona <=100 lines |
| T-0023-041 | Happy | Roz persona contains "assert what code SHOULD do" or equivalent domain-intent constraint |
| T-0023-042 | Happy | Roz persona contains 2 examples (both judgment restraint) |
| T-0023-043 | Happy | Roz persona references qa-checks.md |
| T-0023-044 | Regression | Roz persona does NOT contain numbered trace steps (1. Entry point, 2. API call, etc.) |
| T-0023-045 | Regression | Roz persona does NOT contain Layer Awareness table |
| T-0023-045a | Boundary | Roz persona contains explicit TDD constraint language (e.g., "tests define correct behavior" or "BEFORE Colby builds" or "test-first") per R15 |

#### Step 1f Tests (remaining agents -- sampled)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-050 | Happy | Robert persona <=60 lines |
| T-0023-051 | Happy | Robert persona contains "information asymmetry" constraint |
| T-0023-052 | Happy | Robert persona contains PASS/DRIFT/MISSING/AMBIGUOUS vocabulary |
| T-0023-053 | Happy | Sable persona <=60 lines |
| T-0023-053a | Happy | Sable persona contains "information asymmetry" constraint |
| T-0023-054 | Happy | Sable persona contains five-state audit requirement |
| T-0023-055 | Happy | Poirot persona <=65 lines |
| T-0023-056 | Happy | Poirot persona contains "minimum 5 findings" constraint |
| T-0023-057 | Happy | Poirot persona contains cross-layer wiring check constraint |
| T-0023-058 | Happy | Ellis persona <=65 lines |
| T-0023-058a | Happy | Ellis persona contains per-unit vs final commit distinction |
| T-0023-059 | Happy | Sentinel persona <=65 lines |
| T-0023-060 | Happy | Sentinel persona contains CWE/OWASP requirement |
| T-0023-061 | Happy | Darwin persona <=100 lines |
| T-0023-062 | Happy | Darwin persona contains self-edit protection constraint |
| T-0023-063 | Happy | Darwin persona contains "5+ pipelines" data requirement |
| T-0023-064 | Happy | Deps persona <=90 lines |
| T-0023-065 | Happy | Deps persona contains conservative risk labeling constraint |
| T-0023-066 | Happy | Distillator persona >=130 lines (NOT reduced below Haiku threshold per R14) |
| T-0023-066a | Boundary | Distillator persona <=140 lines (ceiling from Step 1f table) |
| T-0023-067 | Happy | Distillator persona contains 2 examples (Haiku compliance grounding) |
| T-0023-068 | Boundary | Every agent persona has >=1 `<examples>` section with >=1 example |
| T-0023-069 | Regression | No agent persona contains "How [Agent] Fits the Pipeline" section |
| T-0023-070 | Regression | No Opus/Sonnet agent persona contains generic review category checklists (logic, security, error handling, naming, dead code, resource management, concurrency, type safety as enumerated list) |
| T-0023-071 | Regression | Every reduced agent persona retains its original YAML frontmatter unchanged (model, tools, disallowedTools, effort, maxTurns, mcpServers). Verify by diffing frontmatter blocks before/after reduction. |
| T-0023-072 | Regression | Every reduced agent persona contains all required XML tags: `<identity>`, `<required-actions>`, `<workflow>`, `<examples>`, `<constraints>`, `<output>` (per Colby Note #11 / xml-prompt-schema.md) |

#### Step 1g Tests (invocation-templates.md reduction)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-080 | Happy | invocation-templates.md <=300 lines |
| T-0023-081 | Happy | File header contains brain-context injection protocol note |
| T-0023-082 | Happy | File header contains standard READ items note (retro-lessons.md, agent-preamble.md) |
| T-0023-083 | Happy | File header contains persona-constraint note |
| T-0023-084 | Happy | Template index lists <=20 templates (reduced from 25) |
| T-0023-085 | Regression | No individual template contains `<brain-context>` XML example block |
| T-0023-086 | Regression | No individual template READ list contains `retro-lessons.md` or `agent-preamble.md` |
| T-0023-087 | Happy | roz-investigation template contains "CI Watch variant" annotation |
| T-0023-088 | Happy | colby-build template contains "CI Watch variant" annotation |
| T-0023-089 | Happy | roz-scoped-rerun template contains "CI Watch variant" annotation |
| T-0023-090 | Regression | agent-teams-task content moved to pipeline-operations.md |
| T-0023-091 | Regression | dashboard-bridge template removed from invocation-templates.md |

#### Step 1h Tests (session-boot.sh)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-100 | Happy | session-boot.sh outputs valid JSON to stdout |
| T-0023-101 | Happy | JSON contains pipeline_active boolean field |
| T-0023-102 | Happy | JSON contains phase string field |
| T-0023-103 | Happy | JSON contains branching_strategy string field |
| T-0023-104 | Happy | JSON contains custom_agent_count integer field |
| T-0023-104a | Happy | JSON contains `feature` string field |
| T-0023-104b | Happy | JSON contains `stale_context` boolean field |
| T-0023-105 | Happy | JSON contains agent_teams_enabled and agent_teams_env boolean fields |
| T-0023-106 | Happy | JSON contains warn_agents array field |
| T-0023-107 | Failure | Missing pipeline-state.md -> outputs defaults (pipeline_active: false, phase: "idle") and exits 0 |
| T-0023-108 | Failure | Missing pipeline-config.json -> outputs defaults (branching_strategy: "trunk-based") and exits 0 |
| T-0023-109 | Failure | Missing .claude/agents/ directory -> outputs custom_agent_count: 0 and exits 0 |
| T-0023-110 | Failure | Malformed pipeline-state.md (no PIPELINE_STATUS marker) -> outputs defaults and exits 0 |
| T-0023-111 | Boundary | CLAUDE_AGENT_TEAMS env var set -> agent_teams_env: true |
| T-0023-112 | Boundary | CLAUDE_AGENT_TEAMS env var unset -> agent_teams_env: false |
| T-0023-113 | Happy | Script is executable (-x bit set) |
| T-0023-114 | Happy | Script starts with `set -uo pipefail` (retro lesson #003 pattern -- not set -e) |
| T-0023-115 | Boundary | warn_agents array contains agent names from error-patterns.md entries with Recurrence count >= 3 |
| T-0023-116 | Happy | JSON contains ci_watch_enabled, darwin_enabled, dashboard_mode, sentinel_enabled, deps_agent_enabled fields |
| T-0023-117 | Happy | JSON contains project_name field (from config or derived from git remote) |
| T-0023-118 | Failure | No git remote and no project_name in config -> project_name is current directory basename |
| T-0023-119 | Boundary | Script completes in <500ms on typical project (no network calls, no brain) |
| T-0023-120 | Happy | default-persona.md boot sequence references session-boot.sh output parsing for steps 1-3d |
| T-0023-121 | Regression | default-persona.md boot sequence still contains steps 4-6 (brain health, brain context, announcement) |

#### Step 1i Tests (pipeline-orchestration.md reduction)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-130 | Happy | pipeline-orchestration.md <=650 lines |
| T-0023-131 | Regression | All 12 mandatory gates preserved verbatim (grep for "Eva NEVER Skips" header and count numbered items) |
| T-0023-132 | Regression | All observation masking receipt formats preserved (grep for receipt table) |
| T-0023-133 | Regression | Brain capture model section preserved |
| T-0023-134 | Regression | Investigation discipline section preserved |
| T-0023-134a | Regression | Pipeline flow diagram preserved (grep for "Idea -> Robert" or equivalent flow marker) |

#### Step 1j Tests (SKILL.md and /pipeline-setup)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-140 | Happy | SKILL.md lists step-sizing.md in references |
| T-0023-141 | Happy | SKILL.md settings.json template includes session-boot.sh in SessionStart hooks |
| T-0023-142 | Happy | /pipeline-setup copies step-sizing.md to target .claude/references/ |
| T-0023-143 | Happy | /pipeline-setup registers session-boot.sh hook |

#### Step 1l Tests (final integration)

| ID | Category | Description |
|----|----------|-------------|
| T-0023-150 | Happy | Total agent persona lines across 12 agents <=935 |
| T-0023-151 | Happy | All bats tests pass |
| T-0023-152 | Happy | All brain tests pass |
| T-0023-153 | Happy | Assembled Cal persona (claude overlay + shared content) is valid markdown |
| T-0023-154 | Happy | Assembled Colby persona (claude overlay + shared content) is valid markdown |
| T-0023-155 | Happy | Assembled Roz persona (claude overlay + shared content) is valid markdown |

### Test Distribution Summary

| Step | Count | IDs | Categories |
|------|-------|-----|------------|
| 1a | 10 | T-0023-001--008 | Happy (5), Boundary (4), Regression (1) |
| 1b | 6 | T-0023-010--015 | Happy (5), Regression (1) |
| 1c | 10 | T-0023-020--029 | Happy (6), Regression (3), Boundary (1) |
| 1d | 8 | T-0023-030--037 | Happy (5), Regression (1), Boundary (2) |
| 1e | 7 | T-0023-040--045a | Happy (3), Regression (2), Boundary (2) |
| 1f | 26 | T-0023-050--072 | Happy (18), Boundary (2), Regression (6) |
| 1g | 12 | T-0023-080--091 | Happy (7), Regression (5) |
| 1h | 24 | T-0023-100--121 | Happy (13), Failure (4), Boundary (5), Regression (2) |
| 1i | 6 | T-0023-130--134a | Happy (1), Regression (5) |
| 1j | 4 | T-0023-140--143 | Happy (4) |
| 1l | 6 | T-0023-150--155 | Happy (6) |
| **Total** | **119** | | |

---

## Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| step-sizing.md | Markdown file with S1-S5 table, split heuristics, evidence, Darwin trigger | Cal persona (reference), Darwin persona (reference) | 1b -> 1c |
| agent-preamble.md brain protocol | `<protocol id="brain-capture">` with shared capture gates | Cal, Colby, Roz, Agatha personas (pointer + agent-specific values) | 1a -> 1c, 1d, 1e, 1f |
| session-boot.sh | JSON to stdout: `{pipeline_active, phase, feature, stale_context, warn_agents[], branching_strategy, ...}` | Eva boot sequence in default-persona.md (parse and use) | 1h |
| invocation-templates.md header | Brain injection protocol, standard READ items, persona-constraint note | All templates in the file (no longer repeat these) | 1g |
| Baseline metrics (Phase 2) | Brain capture: `{baseline_for: 'ADR-0023', per_agent_first_pass_qa, per_agent_rework_rate, ...}` | Phase 2 comparison (Step 2c) | 2a -> 2c |

## Wiring Coverage

| Producer | Consumer | Step |
|----------|----------|------|
| step-sizing.md | Cal persona (references by path) | 1b |
| step-sizing.md | Darwin persona (can reference for threshold data) | 1b |
| agent-preamble.md brain protocol | Cal, Colby, Roz, Agatha persona pointers | 1a |
| session-boot.sh JSON output | Eva default-persona.md boot parsing | 1h |
| session-boot.sh | SKILL.md hook registration | 1j |
| session-boot.sh | /pipeline-setup install logic | 1j |
| Reduced personas | /pipeline-setup overlay assembly | 1l |
| Phase 1 all changes | Phase 2 baseline measurement | 2a |

---

## Notes for Colby

1. **ADR-0022 must be complete before starting.** All source/ paths in this ADR assume the post-ADR-0022 directory structure (`source/shared/agents/`, `source/shared/references/`, etc.). If ADR-0022 is not yet merged, all paths need adjustment.

2. **Line count targets are +-10%.** Cal <=120 means 108-132 is acceptable. Don't pad to hit exact numbers or cut useful content to squeeze under.

3. **"Remove" means delete, not comment out.** No `<!-- removed: ... -->` blocks. No `_unused` renames. If it's cut, it's gone.

4. **Examples are write-once.** When replacing generic examples with project-specific ones, write the new example from scratch. Don't try to retrofit an existing example by adding project-specific details -- that produces awkward hybrid examples.

5. **Test the examples.** Each replacement example should demonstrate a judgment call with a clear "wrong default -> correct project-specific behavior" structure. If you can't articulate what the model would do wrong without the example, the example isn't earning its context budget.

6. **session-boot.sh follows the prompt-brain-capture.sh pattern exactly:** `set -uo pipefail` (not `set -e`), `INPUT=$(cat 2>/dev/null) || true` for stdin, graceful `jq` fallback, exit 0 always. Source location: `source/shared/hooks/` (not platform-specific -- the hook is useful on both platforms as a SessionStart prompt injection).

7. **invocation-templates.md template index must be updated.** After folding CI Watch variants and removing dashboard-bridge and agent-teams-task, the index goes from 25 to ~20 entries. Line numbers in the index shift after header expansion.

8. **Dual tree for installed files.** After editing `source/shared/`, run `/pipeline-setup` to sync to `.claude/`. Do NOT edit `.claude/` directly.

9. **Distillator is the exception.** When reducing `source/shared/agents/distillator.md`, the target is >=130 lines, not <=. Haiku agents get denser specification. Don't apply the Opus/Sonnet reduction principles to Distillator.

10. **pipeline-orchestration.md reduction scope.** Only condense procedural prose within protocols. Do NOT touch: mandatory gates section, observation masking receipts, brain capture model, pipeline flow diagram, phase sizing rules, or any section that contains decision tables. If a section is a table, keep it. If a section is prose describing how to execute a table, condense it.

11. **Preserve XML tag structure in personas.** The tags (`<identity>`, `<required-actions>`, `<workflow>`, `<examples>`, `<constraints>`, `<output>`) stay even when their content shrinks. The tag vocabulary is documented in `xml-prompt-schema.md` and agents rely on it.

---

## Revisions

| Revision | Date | Summary | Test Delta |
|----------|------|---------|-----------|
| 0 (initial) | 2026-04-03 | 108-test specification, 12 Phase 1 steps + 3 Phase 2 steps | -- |
| 1 | 2026-04-03 | Added 11 tests from Roz test spec review (3 blocking, 8 non-blocking) | +11 (108 -> 119) |

---

## DoD: Verification Checklist

| Category | Count | Preserved |
|----------|-------|-----------|
| Requirements (R1-R15) | 15 | All 15 |
| Test Specs (T-0023-001 through T-0023-155) | 119 | All 119; gaps at step boundaries |
| Phase 1 Steps (1a-1l) | 12 | All 12 with acceptance criteria |
| Phase 2 Steps (2a-2c) | 3 | All 3 with acceptance criteria and regression thresholds |
| Notes for Colby | 11 | All 11 |
| Anti-goals | 3 | All 3 with revisit conditions |
| SPOF analysis | 1 | Telemetry comparison gate (brain unavailability, fallback documented) |
| Alternatives considered | 3 | Proportional (rejected), Model-tier-only (rejected), Defer to Darwin (rejected) |
| Contract Boundaries | 5 | All producer->consumer mappings with shapes |
| Wiring Coverage | 8 | All producer->consumer->step mappings |
| Per-agent reduction targets | 12 | All 12 agents with current/target lines, key removals, key preservations, example strategy |
| Reduction principles | 5 | All 5 documented in Decision section |
| Retro risks | 3 | Lessons #002, #003, #005 with applicability analysis |
