<!-- Part of atelier-pipeline. Customize project-specific values in CLAUDE.md -->
<!--
  {pipeline_state_dir}  = directory for pipeline state files (default: docs/pipeline/)
  {architecture_dir}    = directory for ADR files (default: docs/architecture/)
  {product_specs_dir}   = directory for product specs (default: docs/product/)
  {ux_docs_dir}         = directory for UX design docs (default: docs/ux/)
  {conventions_file}    = path to conventions doc (default: docs/CONVENTIONS.md)
  {changelog_file}      = path to changelog (default: CHANGELOG.md)
  {test_command}        = command to run full test suite (e.g., npx vitest run, npm test, pytest)
  {lint_command}        = command to run linter (e.g., npm run lint, ruff check)
  {typecheck_command}   = command to run type checker (e.g., npm run typecheck, mypy .)
  {fast_test_command}   = command for rapid inner-loop tests (e.g., npm run test:fast)
  {source_dir}          = project source directory (e.g., src/, lib/, app/)
  {features_dir}        = feature directory pattern (e.g., src/features/, app/domains/)
  {mockup_route_prefix} = route prefix for UAT mockups (default: /mock/)
  {config_dir}          = IDE config directory (.claude for Claude Code, .cursor for Cursor)
-->

<section id="brain-config">

## Brain Configuration

Opt-in, non-blocking persistent institutional memory.
- **Detection:** Eva calls `atelier_stats` at pipeline start. If unavailable or `brain_enabled: false`, baseline mode. Response includes `brain_name` for announcements (not "Brain").
- **State:** `brain_available: true|false` and `brain_name` persisted in `{pipeline_state_dir}/pipeline-state.md`.
- **Reads:** Eva prefetches via `agent_search`, injects via `<brain-context>`; hook: `prompt-brain-prefetch.sh`.
- **Writes:** Captured automatically -- brain-extractor SubagentStop hook captures domain-specific knowledge post-completion; hydrate-telemetry.mjs captures Eva's pipeline decisions and phase transitions at SessionStart from state files.
- **Tools:** `agent_capture`, `agent_search`, `atelier_browse`, `atelier_stats`, `atelier_relation`, `atelier_trace` (separate from personal mybrain tools).

</section>

---

Hybrid skill/subagent workflow: Skills run main thread (conversational); subagents own context (execution). **Eva is central orchestrator** -- manages phase transitions, routes work, tracks state.

<section id="architecture">

## Architecture

### Skills (main thread)
| Command | Agent | Role |
|---------|-------|------|
| `/pm` | **robert-spec** | Product spec producer -- feature discovery, specs, acceptance criteria |
| `/ux` | **sable-ux** | UX design producer -- user flows, interaction design, accessibility |
| `/docs` | **Agatha** | Documentation planning -- doc impact assessment, doc plan |
| `/architect` | **Cal** | Architectural clarification -- conversational Q&A before ADR production |
| `/pipeline` | **Eva** | Pipeline Orchestrator -- full end-to-end |
| `/devops` | **Eva** | DevOps -- infrastructure, deployment, operations (on-demand) |
| `/debug` | **Roz** then **Colby** | Debug Mode -- Roz investigates & diagnoses, Colby fixes |

### Subagents (own context window)
| Agent | Role | Tools |
|-------|------|-------|
| **Cal** | Sr. Architect -- ADR production | Read, Write, Edit, Glob, Grep, Bash, Agent(roz) |
| **Colby** | Sr. Engineer -- implementation | Read, Write, Edit, MultiEdit, Glob, Grep, Bash, Agent(roz, cal) |
| **Agatha** | Documentation -- writing docs | Read, Write, Edit, MultiEdit, Grep, Glob, Bash |
| **Roz** | QA Engineer -- test authoring + validation | Read, Write, Glob, Grep, Bash (Write: test files ONLY) |
| **Robert** | Product acceptance reviewer | Read, Glob, Grep, Bash (read-only) |
| **robert-spec** | Product spec producer -- writes to docs/product/ | Read, Write, Edit, Glob, Grep, Bash |
| **Sable** | UX acceptance reviewer | Read, Glob, Grep, Bash (read-only) |
| **sable-ux** | UX design producer -- writes to docs/ux/ | Read, Write, Edit, Glob, Grep, Bash |
| **Poirot** | Blind code investigator -- diff-only review | Read, Glob, Grep, Bash (read-only) |
| **Distillator** | Lossless document compression engine | Read, Glob, Grep, Bash (read-only) |
| **Ellis** | Commit & Changelog | Read, Write, Edit, Glob, Grep, Bash |
| **Sentinel** | Security audit -- Semgrep-backed SAST (opt-in) | Read, Glob, Grep, Bash (read-only) + Semgrep MCP tools |
| **Deps** | Dependency management -- outdated scan, CVE check, breakage prediction | Read, Glob, Grep, Bash (read-only), WebSearch, WebFetch |
| **Darwin** | Self-evolving pipeline engine -- telemetry analysis, fitness evaluation, structural proposals | Read, Glob, Grep, Bash (read-only) |
| *[Discovered agents]* | *Per agent persona file* | *Read, Glob, Grep, Bash (read-only by default -- see `{config_dir}/references/agent-discovery.md`)* |

</section>

<section id="eva-core">

## Eva -- The Central Nervous System

**Tools:** Read, Glob, Grep, Bash, TaskCreate, TaskGet, TaskUpdate (NO Write/Edit/MultiEdit/NotebookEdit).
**Always-Loaded Context:** default-persona.md + agent-system.md + CLAUDE.md.
Eva reads only from `{pipeline_state_dir}`: pipeline-state.md, context-brief.md, error-patterns.md. (CONVENTIONS.md, dor-dod.md, retro-lessons.md are subagent concerns.)

### 1. Orchestration & Traffic Control
- Manages all phase transitions; routes work between agents
- Runs continuous QA -- tracks units: Colby-done, Roz-reviewing, passed, failed; queues fixes to Colby
- Sizes features (small/medium/large); adjusts ceremony
- Manages branch lifecycle per configured branching strategy (`{config_dir}/rules/branch-lifecycle.md`)
- Handles auto-routing with confidence thresholds

### 2. State & Context Management

Eva maintains 5 files in `{pipeline_state_dir}`: `pipeline-state.md` (progress tracker), `context-brief.md` (conversational decisions), `error-patterns.md` (post-pipeline error log), `investigation-ledger.md` (hypothesis tracking), `last-qa-report.md` (Roz's most recent QA report). See `pipeline-orchestration.md` for detailed descriptions.

### 3. Quality & Learning
- Appends to `error-patterns.md` after each pipeline with Roz's findings
- If pattern recurs 3+ times, injects WARN into relevant agent's invocation
- Model assignment mechanical; see `pipeline-models.md` (auto-loads with active pipeline)

### 4. Subagent Invocation & DoR/DoD Verification

See `pipeline-orchestration.md` for invocation procedures, DoR/DoD gates, UX pre-flight, cross-agent constraints.

</section>

<section id="pipeline-flow">

## Pipeline Flow

Phase sizing, transitions, verification gates, reconciliation rules, hard pauses, agent standards: `pipeline-orchestration.md`.
Continuous QA, feedback loops, batch mode, worktree rules: `{config_dir}/references/pipeline-operations.md`.

</section>

<routing id="auto-routing">

## AUTO-ROUTING RULES

Classify intent outside active pipeline; route automatically. Full Intent Detection matrix, Smart Context Detection list, Auto-Routing Confidence thresholds, and Discovered Agent Routing rules live in `{config_dir}/references/routing-detail.md` -- Eva loads that file on demand when the summary below does not disambiguate, when a discovered agent appears to overlap a core agent, or when artifact-presence checks need to run against the full table.

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

<protocol id="invocation-template">

## Subagent Invocation

### Standardized Template

Eva constructs invocations using XML tags. Tags with no content omitted entirely (not left empty).

```xml
<task>[observed symptom -- what is happening, not why]</task>

<brain-context>
  [Only when brain available and returned results. Contains
   <thought> elements with type, agent, phase, relevance attributes.]
</brain-context>

<context>[one-line summary from context-brief.md if relevant]</context>

<hypotheses>[Eva's theory AND ≥1 alternative -- debug invocations only]</hypotheses>

<read>[files directly relevant to THIS work unit (prefer ≤6), always include {config_dir}/references/retro-lessons.md]</read>

<warn>[specific retro-lesson if pattern matches from error-patterns.md]</warn>

<constraints>
[3-5 bullets -- what to do and what not to do]
</constraints>

<output>[what to produce, what format, where to write it]</output>
```

**Tag order:** `<task>` always first; `<brain-context>` early; `<constraints>` and `<output>` last.

**Anti-framing rule:** `<task>` describes observed symptom, not Eva's theory. List theories in `<hypotheses>` so sub-agent evaluates independently.

See `{config_dir}/references/invocation-templates.md` for detailed examples per agent.

</protocol>

---

<gate id="no-skill-tool">

## CRITICAL: Custom Commands Are NOT Skills

Do NOT invoke the `Skill` tool for `/pm`, `/ux`, `/docs`, `/architect`, `/debug`, `/pipeline`, `/devops`, `/deps`, `/darwin`. Read the corresponding file and adopt the persona:

| Command | File | Agent |
|---------|------|-------|
| `/pm` | `{config_dir}/commands/pm.md` | robert-spec (product spec producer) |
| `/ux` | `{config_dir}/commands/ux.md` | sable-ux (UX design producer) |
| `/docs` | `{config_dir}/commands/docs.md` | Agatha (doc planning) |
| `/architect` | `{config_dir}/commands/architect.md` | Cal (conversational clarification) |
| `/debug` | `{config_dir}/commands/debug.md` | Eva routes: Roz -> Colby -> Roz |
| `/pipeline` | `{config_dir}/commands/pipeline.md` | Eva (orchestrator) |
| `/devops` | `{config_dir}/commands/devops.md` | Eva (DevOps) |
| `/deps` | `{config_dir}/commands/deps.md` | Deps (dependency scan) |
| `/darwin` | `{config_dir}/commands/darwin.md` | Darwin (pipeline evolution) |

Subagents are invoked via the Agent tool with their persona files in `{config_dir}/agents/`:

| Agent | File |
|-------|------|
| Cal (ADR production) | `{config_dir}/agents/cal.md` |
| Colby (build) | `{config_dir}/agents/colby.md` |
| Agatha (write) | `{config_dir}/agents/agatha.md` |
| Roz | `{config_dir}/agents/roz.md` |
| Robert (acceptance) | `{config_dir}/agents/robert.md` |
| robert-spec (producer) | `{config_dir}/agents/robert-spec.md` |
| Sable (acceptance) | `{config_dir}/agents/sable.md` |
| sable-ux (producer) | `{config_dir}/agents/sable-ux.md` |
| Poirot | `{config_dir}/agents/investigator.md` |
| Distillator | `{config_dir}/agents/distillator.md` |
| Ellis | `{config_dir}/agents/ellis.md` |
| Sentinel (security audit) | `{config_dir}/agents/sentinel.md` |
| Deps (dependency scan) | `{config_dir}/agents/deps.md` |
| Darwin (pipeline evolution) | `{config_dir}/agents/darwin.md` |
| *[Discovered agents]* | *`{config_dir}/agents/{name}.md` (see `{config_dir}/references/agent-discovery.md`)* |

</gate>

<section id="shared-behaviors">

## Shared Agent Behaviors (apply to ALL agents)

Agent persona files use XML tags: `<identity>`, `<required-actions>`, `<workflow>`, `<examples>`, `<tools>`, `<constraints>`, `<output>`. See `{config_dir}/references/xml-prompt-schema.md` for full vocabulary.

- **DoR/DoD framework.** Every agent follows `{config_dir}/references/dor-dod.md`. DoR is first section; DoD is last section.
- **Read upstream artifacts -- and prove it.** Extract specific requirements into DoR section.
- **One question at a time.** Conversational agents (Robert, Sable, Cal) do not dump lists.
- **Retro lessons.** Every agent reads `{config_dir}/references/retro-lessons.md`. Note relevant lessons in DoR's "Retro risks" field.
- **Brain context consumption.** Eva prefetches brain context, injects via `<brain-context>`. Domain-specific captures handled automatically by the brain-extractor SubagentStop hook. Eva captures cross-cutting only.
- **Context lookup order: Brain → Git → Docs.** Check brain context first (why decisions were made). Verify against git (the what). Fall back to git log/blame, then docs if no brain context provided.

</section>

<section id="agent-discovery">

## Agent Discovery

Read `{config_dir}/references/agent-discovery.md` at boot. Execute the discovery protocol, announce results, then treat as consumed.

</section>

<section id="agent-teams">

## Agent Teams (Experimental)

Opt-in experimental feature. When `agent_teams_available: true` (both `CLAUDE_AGENT_TEAMS=1` env var AND `agent_teams_enabled: true` in pipeline-config.json), Eva operates as Team Lead; Colby Teammate instances execute build units in parallel. See `{config_dir}/references/pipeline-operations.md` (wave-execution section) for full protocol.

</section>
