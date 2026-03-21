# Feature Spec: Atelier Brain

**Author:** Robert Sfeir (CPO)
**Date:** 2026-03-21
**Status:** Draft
**Size:** Large

---

## Problem Statement

Atelier-pipeline agents lose all reasoning context between sessions. Every new session starts from zero — agents re-read files, re-discover patterns, and re-learn codebase conventions. Prior decisions, rejected alternatives, human corrections, and the reasoning behind architectural choices evaporate when a session ends.

This produces three measurable failures:

1. **Repeated mistakes.** Agents propose approaches that were previously tried and rejected, burning cycles on known dead ends.
2. **Spec and doc drift.** Without memory of why specs evolved, agents trust stale documentation and introduce silent inconsistencies. Research shows 42% task success decline and 487% increase in inter-agent conflicts without persistent context (arXiv:2601.04170).
3. **Lost institutional knowledge.** The "why" behind decisions exists only in human memory. When a developer isn't available, the reasoning behind the current architecture is inaccessible to agents and other team members.

## Vision

Give the atelier-pipeline agents persistent institutional memory — a shared brain that captures reasoning, tracks decision evolution, detects conflicts, and surfaces relevant context to agents mid-task. The brain is an enhancement, not a dependency. The pipeline works without it; with it, agents make better first-pass decisions and avoid known pitfalls.

## Users

| User | Need |
|---|---|
| **Solo developer** (current) | Cross-session context. Agents remember prior decisions, corrections, and patterns across pipeline runs. |
| **Small team** (2-5 developers) | Shared institutional memory. One developer's findings surface for another working on the same feature area. |
| **Multi-product organization** (future) | Cross-product learning. Decisions and patterns discovered in one product are discoverable by teams working on related capabilities in other products. |

## User Stories

### US-1: Cross-Session Memory
**As** a developer running multiple pipeline sessions on the same feature,
**I want** agents to remember prior decisions and reasoning from earlier sessions,
**So that** they don't re-propose rejected approaches or miss context that shaped current architecture.

**Acceptance Criteria:**
- Cal, when designing architecture, calls `agent_search` to retrieve prior architectural decisions relevant to the current feature area
- Robert-subagent, when reviewing spec compliance, calls `agent_search` + `atelier_trace` to retrieve the evolution history of a specification
- Roz, when running QA, calls `agent_search` to retrieve recurring patterns from past sweeps on similar code
- All retrieval is additive — agents work identically if the brain is unavailable

### US-2: Decision Evolution Trail
**As** a developer or PM reviewing a feature's history,
**I want** to trace the reasoning chain behind any current decision — what was decided, what was rejected, what triggered the change,
**So that** I understand provenance without detective work in git logs.

**Acceptance Criteria:**
- Every captured thought links to related thoughts via `atelier_relation` with typed relations (supersedes, triggered_by, evolves_from, contradicts, supports, synthesized_from)
- Given any thought, calling `atelier_trace` traverses backward ("what led here?") and forward ("what followed?")
- The chain includes human decisions (HALT resolutions), agent findings (drift, corrections), and rejected alternatives

### US-3: Conflict Detection
**As** a team lead with multiple developers working on related features,
**I want** the brain to detect when two developers capture contradicting decisions about the same capability,
**So that** alignment issues surface at capture time instead of in production.

**Acceptance Criteria:**
- When a decision/preference-type thought is captured via `agent_capture`, the brain internally searches for semantically similar active decisions in overlapping scopes
- Duplicates (>0.9 similarity) are merged automatically
- Same-team contradictions: newest wins, old thought is invalidated via `atelier_relation` (supersedes)
- Cross-team contradictions: both thoughts flagged as `status: 'conflicted'`, human is notified to resolve
- No pipeline is blocked by conflict detection — it's a flag, not a gate

### US-4: Knowledge Decay
**As** a developer working on a mature codebase with months of captured thoughts,
**I want** stale tactical findings to naturally fade from search results while important decisions persist,
**So that** the brain stays relevant and doesn't drown me in historical noise.

**Acceptance Criteria:**
- Different thought types have different default lifespans (configurable via lookup table)
- Decisions and preferences: no expiry
- Lessons and patterns: long-lived (configurable, default 365 days)
- Tactical findings (drift, corrections): short-lived (configurable, default 90 days)
- Expired thoughts are excluded from default search but accessible via chain traversal
- Lifespans are configurable without code changes (database lookup table)

### US-5: Consolidation
**As** a developer whose brain accumulates hundreds of granular findings per week,
**I want** the brain to periodically synthesize raw observations into higher-level insights,
**So that** search results surface patterns, not individual data points.

**Acceptance Criteria:**
- A background process runs on a configurable timer (default 30 minutes)
- It clusters related unconsolidated thoughts and produces reflection-type thoughts
- Reflections link to their source thoughts via relations
- Reflections naturally outrank raw observations in search (higher importance, broader relevance)
- Source thoughts remain active — they are not consumed or hidden by consolidation

### US-6: Scoped Access
**As** a developer in a multi-product organization,
**I want** to search within my product's context by default but widen to the organization when needed,
**So that** I get relevant results without noise from unrelated products, while still accessing cross-product learning when I choose to.

**Acceptance Criteria:**
- Every thought has a hierarchical scope (e.g., `acme.payments.auth`) using ltree
- Default search filters to the developer's product scope
- Developer can explicitly widen scope (e.g., search org-wide)
- A thought can belong to multiple scopes (ltree array)
- Scoping is a filter applied before scoring — it narrows the candidate set, not the ranking

### US-7: Brain as Optional Enhancement
**As** a developer setting up atelier-pipeline for a new project,
**I want** the brain to be an opt-in feature that I enable when ready,
**So that** the pipeline works out of the box without requiring database infrastructure.

**Acceptance Criteria:**
- Brain is disabled by default (`brain_config.brain_enabled = false`)
- Enabling requires: brain MCP server running (config file exists) + `brain_enabled = true` in database (set by `/brain-setup` or Settings UI toggle)
- Eva calls `atelier_stats` at pipeline start. Two gates: (1) tool available = server running, (2) `brain_enabled: true` in response. Both must pass for `brain_available: true`. Graceful fallback if either fails.
- Every pipeline gate has a baseline behavior (no brain) and an enhanced behavior (with brain)
- No pipeline run fails because the brain is unavailable
- Setup is guided by the `/brain-setup` skill that handles database creation, schema installation, and configuration

### US-8: Solo Developer Setup
**As** a solo developer trying atelier-pipeline,
**I want** to set up a personal brain with minimal friction,
**So that** I can start using institutional memory without needing shared infrastructure.

**Acceptance Criteria:**
- Running `/brain-setup` skill walks me through setup conversationally
- I can choose local PostgreSQL (Strategy A) or Docker (Strategy B)
- Docker option: a single `docker compose up -d` spins up PostgreSQL with pgvector + ltree, schema auto-applied
- Local option: skill runs schema.sql against my existing PostgreSQL
- Configuration written to `${CLAUDE_PLUGIN_DATA}/brain-config.json` (local to my machine, not committed)
- Brain MCP server starts connecting on next session
- If I never run `/brain-setup`, pipeline works identically to today — no prompts, no errors, no awareness of brain capability

### US-9: Team Shared Brain Setup
**As** a tech lead setting up the brain for my team,
**I want** to configure a shared brain once and have my colleagues inherit the configuration from the repo,
**So that** new developers are brain-enabled with minimal onboarding.

**Acceptance Criteria:**
- Running `/brain-setup --shared` (or selecting "shared" when prompted) writes config to `.claude/brain-config.json` in the project (committed to git)
- Database URL and scope are stored in the committed config. Secrets (OpenRouter API key, database password) are referenced as environment variable placeholders (e.g., `${OPENROUTER_API_KEY}`)
- When a colleague checks out the repo, the plugin detects the project-level brain config
- If the colleague has the required env vars set, the brain connects automatically — no `/brain-setup` needed
- If the colleague does NOT have env vars set, brain stays disabled with a clear message: "Brain config found but missing OPENROUTER_API_KEY. Set it to enable brain."
- No pipeline run fails because a colleague hasn't configured their env vars

### US-10: Config Priority and Override
**As** a developer who has both a personal brain and a project-level team brain configured,
**I want** the project-level config to take priority,
**So that** I use the team's shared brain when working on team projects and my personal brain when working solo.

**Acceptance Criteria:**
- Brain MCP server reads config in priority order: project-level (`.claude/brain-config.json`) → user-level (`${CLAUDE_PLUGIN_DATA}/brain-config.json`) → neither exists (brain disabled)
- Project-level config wins when both exist
- User-level config is fallback for projects that don't have shared brain
- Priority order is deterministic and documented
- Settings UI shows which config source is active: "(personal)" or "(project)" in the status bar
- When project config is active, connection details (database URL, scope) are read-only in the UI
- Personal tuning (TTL adjustments, consolidation interval, conflict detection settings) can be overridden locally via `${CLAUDE_PLUGIN_DATA}/brain-overrides.json` — these never write to the project config
- Existing personal config is NOT deleted when project config appears — it remains as fallback for other projects

## Brain Tool Surface

The atelier brain exposes 6 MCP tools for agent interaction and 7 REST endpoints for the settings UI. These are separate from the personal mybrain tools — both coexist without namespace collision.

### MCP Tools (Agent-Facing)

| Tool | Purpose | Used By |
|---|---|---|
| `agent_capture` | Store a thought with schema-enforced metadata. Handles dedup (>0.9 similarity), conflict detection (0.7-0.9 + LLM classification for decision/preference types), and supersedes relations. | Eva, Cal, Robert-skill, Robert-subagent, Sable-skill, Sable-subagent, Colby, Roz, Agatha |
| `agent_search` | Semantic search with three-axis scoring (recency + importance + relevance). Scope filtering via ltree. Excludes invalidated thoughts by default. Updates `last_accessed_at` on returned results. | Eva, Cal, Robert-skill, Robert-subagent, Sable-skill, Sable-subagent, Colby, Roz, Agatha |
| `atelier_browse` | List/filter thoughts by status, thought_type, source_agent. Pagination. | Eva (pipeline monitoring) |
| `atelier_stats` | Counts by type, status, agent. Last consolidation timestamp. Active vs expired vs invalidated. | Eva (health check at pipeline start) |
| `atelier_relation` | Link two thoughts via typed relation (supersedes, triggered_by, evolves_from, contradicts, supports, synthesized_from). Supersedes type auto-invalidates target. | Eva (cross-agent relations), Cal (ADR reasoning chains), agents (when capturing linked thoughts) |
| `atelier_trace` | Given a thought ID, traverse the relation graph backward (what led here) or forward (what followed). Recursive with configurable depth limit. | Any agent tracing decision history mid-task |

### REST Endpoints (Settings UI)

| Endpoint | Purpose | Maps to |
|---|---|---|
| `GET /api/health` | Connection status, thought count, last/next consolidation | US-7 (brain health), UX status bar |
| `GET /api/config` | Read brain_config singleton | US-4, US-5 (view settings) |
| `PUT /api/config` | Update brain_config fields | US-4, US-5 (change settings) |
| `GET /api/thought-types` | Read thought_type_config rows | US-4 (view TTL/importance) |
| `PUT /api/thought-types/:type` | Update TTL and importance for a type | US-4 (change TTL/importance) |
| `POST /api/purge-expired` | Delete expired thoughts + orphaned relations | UX danger zone |
| `GET /api/stats` | Extended stats by type, status, agent | UX status bar detail |

### Coexistence with mybrain

The personal mybrain MCP server (`capture_thought`, `search_thoughts`, `browse_thoughts`, `brain_stats`) and the atelier brain (`agent_capture`, `agent_search`, `atelier_browse`, `atelier_stats`, `atelier_relation`, `atelier_trace`) are separate tools with separate databases. They share no data, no namespace, and no configuration. A developer can use mybrain for personal notes and the atelier brain for pipeline institutional memory simultaneously.

## Agent Operating Model

**When brain is available, the following read and write behaviors are MANDATORY for each listed agent.** These are not suggestions. Agent personas MUST be updated to include these tool calls as required steps in their workflow. The behaviors are conditional on brain availability — if brain is unavailable, agents skip the brain steps and proceed with baseline behavior. But when the brain is live, these are not optional.

All brain interactions use the tools defined in [Brain Tool Surface](#brain-tool-surface) above.

### Eva (Orchestrator)

**Reads:**
- Pipeline start: calls `agent_search` with query derived from current feature area + scope. Injects results into her pipeline state alongside `context-brief.md`.
- Before delegating to any agent: calls `agent_search` for known issues, prior findings, and user corrections relevant to the task she's about to assign. Passes results as context in the agent invocation.
- Health check: calls `atelier_stats` at pipeline start to verify brain is live.

**Writes:**
- After every gate-triggered event: calls `agent_capture` with `source_agent: 'eva'`, appropriate `thought_type` and `source_phase` (DRIFT finding, HALT resolution, spec correction, phase transition).
- Creates cross-agent relations via `atelier_relation`: drift finding `triggered_by` review juncture, correction `supersedes` prior reasoning, HALT resolution `triggered_by` AMBIGUOUS finding.
- Captures Poirot's findings post-review via `agent_capture` with `source_agent: 'eva'`, `thought_type: 'insight'` (Poirot himself never touches brain).
- Pipeline end: calls `agent_capture` with `thought_type: 'decision'` for session summary linking key decisions from the run.

**Behavior change:** Eva becomes the pipeline's memory manager in addition to orchestrator. She doesn't decide *what* to capture — the gates are mechanical. She executes the capture when a gate fires.

### Cal (Architect)

**Reads:**
- Before designing architecture: calls `agent_search` for prior architectural decisions on this feature area, rejected approaches, and known technical constraints.
- Mid-ADR: calls `agent_search` for specific patterns or technologies as emergent questions arise. ("Has event sourcing been tried in this codebase?")
- When referencing a prior decision: calls `atelier_trace` to understand the full reasoning chain behind it.

**Writes:**
- Calls `agent_capture` with `thought_type: 'decision'`, `source_agent: 'cal'`, `source_phase: 'design'` for each ADR decision point: what was decided, what alternatives were considered, why they were rejected.
- Calls `agent_capture` with `thought_type: 'rejection'`, `source_agent: 'cal'` for each rejected alternative with rationale.
- Calls `agent_capture` with `thought_type: 'insight'`, `source_agent: 'cal'` for technical constraints discovered during design that aren't in the spec.

**Behavior change:** Cal's first draft is better because he starts with institutional context. Fewer rejected-approach cycles. ADR reasoning is preserved beyond the document itself.

### Robert-skill (CPO — Spec Author)

**Reads:**
- Before writing a spec: calls `agent_search` for prior specs on this feature area, user corrections to past specs, and drift findings that indicate spec weakness.
- Mid-spec: calls `agent_search` for domain-specific decisions and preferences when clarifying requirements.

**Writes:**
- Calls `agent_capture` with `thought_type: 'decision'`, `source_agent: 'robert'`, `source_phase: 'design'` for spec rationale: why requirements were framed this way, what user feedback shaped them, what was deliberately excluded and why.
- When updating a living spec: calls `agent_capture` with `thought_type: 'correction'`, `source_agent: 'robert'` with the triggering event (drift finding, user correction, scope change). Calls `atelier_relation` to link correction `supersedes` prior spec reasoning.

**Behavior change:** Specs carry forward institutional knowledge. A spec for auth v3 reflects lessons from auth v1 and v2 without the PM having to manually recall them.

### Robert-subagent (Product Acceptance Reviewer)

**Reads:**
- Before reviewing: calls `agent_search` for the spec's evolution history. Calls `atelier_trace` on prior drift findings to understand not just what the spec says, but how it got there and what prior drift was found.

**Writes:**
- Calls `agent_capture` with `thought_type: 'drift'`, `source_agent: 'robert'`, `source_phase: 'review'` for every DRIFT/MISSING verdict, including what drifted, what the spec expected, and what the code does instead.
- Calls `agent_capture` with `thought_type: 'decision'`, `source_agent: 'robert'` for PASS verdicts on non-trivial features (creates the "was verified" record).
- AMBIGUOUS findings captured with `thought_type: 'insight'` — Eva creates the HALT relation.

**Behavior change:** Robert-subagent's reviews are informed by prior spec evolution. A recurring DRIFT pattern on the same module surfaces as a pattern, not an isolated finding.

### Sable-skill (UX Designer — Doc Author)

**Reads:**
- Before designing UX: calls `agent_search` for prior UX decisions on this feature area, accessibility findings, and user feedback on similar flows.
- Mid-design: calls `agent_search` for component patterns and interaction decisions from other features.

**Writes:**
- Calls `agent_capture` with `thought_type: 'decision'`, `source_agent: 'sable'`, `source_phase: 'design'` for UX rationale: why this flow was chosen, what alternatives were sketched, what accessibility constraints shaped the design.
- When updating a living UX doc: calls `agent_capture` with `thought_type: 'correction'`, `source_agent: 'sable'` with change reasoning. Calls `atelier_relation` to link to prior UX reasoning.

**Behavior change:** UX designs carry forward cross-feature pattern knowledge. Sable doesn't redesign a modal pattern that was already refined on another feature.

### Sable-subagent (UX Acceptance Reviewer)

**Reads:**
- Before reviewing: calls `agent_search` for the UX doc's evolution history and prior UX drift findings on this feature.

**Writes:**
- Calls `agent_capture` with `thought_type: 'drift'`, `source_agent: 'sable'`, `source_phase: 'review'` for every DRIFT/MISSING verdict.
- Calls `agent_capture` with `thought_type: 'insight'`, `source_agent: 'sable'` for five-state audit results — useful for consolidation to surface "which features consistently miss error states?"

**Behavior change:** Sable-subagent can spot recurring UX drift patterns across features, not just within one review.

### Colby (Engineer)

**Reads:**
- Before building: calls `agent_search` for implementation patterns used in this codebase, known gotchas, and prior build failures on similar code.
- Mid-build: calls `agent_search` for specific technical solutions when hitting unexpected problems.

**Writes:**
- Calls `agent_capture` with `thought_type: 'insight'`, `source_agent: 'colby'`, `source_phase: 'build'` for implementation decisions that aren't in the ADR: "used debounce instead of throttle because the API rate-limits at 10/sec."
- Calls `agent_capture` with `thought_type: 'lesson'`, `source_agent: 'colby'` for workarounds and their reasons: "shimmed the date library because timezone handling broke in v3.2."

**Behavior change:** Colby starts with knowledge of codebase conventions and known pitfalls. Fewer "tried something → Roz caught it → redo" cycles.

### Roz (QA Engineer)

**Reads:**
- Before writing tests: calls `agent_search` for recurring QA patterns on this module, known fragile areas, and test strategies that worked or failed.
- During code QA: calls `agent_search` for prior findings on similar code patterns.

**Writes:**
- Calls `agent_capture` with `thought_type: 'lesson'`, `source_agent: 'roz'`, `source_phase: 'qa'` for recurring QA patterns: "auth module consistently fails on timeout edge cases."
- Calls `agent_capture` with `thought_type: 'insight'`, `source_agent: 'roz'` for investigation findings that went beyond the immediate fix — root cause analysis that future sessions should know.
- Calls `agent_capture` with `thought_type: 'insight'`, `source_agent: 'roz'` for doc impact assessments when `Doc Impact: YES` — useful for tracking which features consistently trigger doc updates.

**Behavior change:** Roz's test coverage is informed by historical failure patterns. Tests target known-fragile areas more aggressively. QA findings feed the consolidation engine, surfacing systemic patterns.

### Poirot (Blind Code Reviewer)

**Reads:** None. Poirot is deliberately context-free — he sees only the diff. Brain access would compromise the information asymmetry that makes his review valuable.

**Writes:**
- Eva captures Poirot's findings post-review (not Poirot himself, to preserve his isolation).

**Behavior change:** None. Poirot stays blind. This is intentional.

### Agatha (Documentation)

**Reads:**
- Before writing docs: calls `agent_search` for prior doc update reasoning on this feature, known doc-drift patterns, and user feedback on documentation quality.

**Writes:**
- Calls `agent_capture` with `thought_type: 'decision'`, `source_agent: 'agatha'`, `source_phase: 'reconciliation'` for doc update reasoning: what changed in the docs, what triggered it (Roz doc-impact flag, Robert/Sable drift finding), what was intentionally left unchanged.

**Behavior change:** Agatha's documentation reflects institutional knowledge about what users and agents actually reference. Docs improve based on usage patterns, not just code changes.

### Distillator (Compression)

**Reads:** None. Distillator is a mechanical compression engine. Brain context would add tokens to an agent whose job is reducing tokens.

**Writes:** None. Compression artifacts are ephemeral — they exist to fit context windows, not to persist as institutional knowledge.

**Behavior change:** None. Distillator stays mechanical.

### Ellis (Commit Manager)

**Reads:** None. Ellis sees the diff and writes a commit message. Brain context is irrelevant to commit message quality.

**Writes:** None. Commits are in git — the Layer 2 that already exists.

**Behavior change:** None. Ellis stays focused.

### Summary: Who Touches the Brain (MANDATORY when brain available)

| Agent | Reads (MUST call) | Writes (MUST call) | Notes |
|---|---|---|---|
| **Eva** | `agent_search` (pre-delegation), `atelier_stats` (health) | `agent_capture` (gate events), `atelier_relation` (cross-agent links) | Memory manager |
| **Cal** | `agent_search` (prior arch, mid-ADR), `atelier_trace` (decision chains) | `agent_capture` (decisions, rejections, insights) | Better first drafts |
| **Robert-skill** | `agent_search` (prior specs, corrections) | `agent_capture` (spec rationale, corrections), `atelier_relation` (supersedes) | Institutional spec knowledge |
| **Robert-subagent** | `agent_search` (spec evolution), `atelier_trace` (drift history) | `agent_capture` (verdicts, drift findings) | Pattern detection |
| **Sable-skill** | `agent_search` (prior UX, accessibility) | `agent_capture` (UX rationale, corrections), `atelier_relation` (supersedes) | Cross-feature patterns |
| **Sable-subagent** | `agent_search` (UX evolution, prior drift) | `agent_capture` (verdicts, five-state audits) | Pattern detection |
| **Colby** | `agent_search` (patterns, gotchas, mid-build) | `agent_capture` (implementation decisions, workarounds) | Fewer redo cycles |
| **Roz** | `agent_search` (QA patterns, failure history) | `agent_capture` (patterns, investigations, doc-impact) | Targeted testing |
| **Poirot** | ✗ (intentionally blind) | ✗ (Eva captures post-review) | Isolation preserved |
| **Agatha** | `agent_search` (prior doc reasoning) | `agent_capture` (doc update reasoning) | Usage-informed docs |
| **Distillator** | ✗ | ✗ | Mechanical, no memory |
| **Ellis** | ✗ | ✗ | Git is the memory |

## What This Feature Is NOT

- **Not a replacement for artifacts on disk.** Specs, ADRs, UX docs, and code remain the source of truth. The brain stores reasoning context — the "why" — not a duplicate of the "what."
- **Not a chat log.** The brain stores atomic, structured thoughts with enforced metadata — not conversation transcripts.
- **Not required.** The pipeline must function identically (minus brain-enhanced context) when the brain is unavailable.
- **Not a real-time collaboration tool.** The brain is eventually consistent. Consolidation runs on a timer. Conflict detection happens at write time, not continuously.
- **Not an agent decision-maker.** The brain provides context. Agents and humans make decisions. Memory retrieval is always treated as supplementary, never authoritative.
- **Not a replacement for mybrain.** The personal mybrain MCP server and the atelier brain are separate tools with separate databases, separate tool names, and separate purposes. mybrain is for personal knowledge. The atelier brain is for pipeline institutional memory. Both coexist without conflict. See [Coexistence with mybrain](#coexistence-with-mybrain).

## Success Metrics

| Metric | Baseline (no brain) | Target (with brain) | How measured |
|---|---|---|---|
| Repeated rejected approaches | Unmeasured (anecdotal) | 0 per pipeline run | Agent proposes approach, brain returns prior rejection, agent pivots |
| Spec drift caught at review | Caught at review juncture | Caught at design phase (agent retrieves spec evolution context) | Pipeline phase where drift is first flagged |
| Cross-session context recovery | Manual (read context-brief.md) | Automatic (brain search on session start) | Time from session start to first agent invocation |
| Cross-team conflict detection time | Discovered at integration or production | Discovered at capture time | Time between contradicting decisions captured and conflict surfaced |
| Brain search relevance | N/A | Top-3 results contain relevant context >80% of the time | Spot-check during pipeline runs |

## Deployment Tiers

| Tier | Scenario | Setup | Brain Shared? |
|---|---|---|---|
| **Solo personal** | Individual developer experimenting | `/brain-setup` → local PostgreSQL or Docker, config in `${CLAUDE_PLUGIN_DATA}` | No — personal brain |
| **Team isolated** | Team without shared infra | Each developer runs `/brain-setup` independently | No — N isolated brains |
| **Team shared** | Team with shared database | First dev: `/brain-setup --shared` → DB + project config committed. Others: set env var only | Yes — one brain, scoped access |

### Config Priority Chain

```
1. .claude/brain-config.json       (project-level, shared via git)
2. ${CLAUDE_PLUGIN_DATA}/brain-config.json  (user-level, local only)
3. Neither exists                   → brain disabled, pipeline baseline
```

Project-level wins over user-level when both exist. This ensures team config overrides individual preferences on team projects.

### Plugin Installation Flow

1. User installs plugin: `/plugin install atelier-pipeline@robertsfeir`
2. Plugin copies to cache. MCP server declared in `.mcp.json` but inert (no config yet).
3. **If project-level config exists** (colleague pulled repo):
   - Brain MCP server attempts connection using committed config + env vars
   - If env vars present → brain available, enhanced mode
   - If env vars missing → brain disabled, baseline mode, message logged
4. **If no config exists** (fresh install):
   - Pipeline runs baseline. No prompts, no errors.
   - User runs `/brain-setup` when ready to enable brain.
5. `SessionStart` hook checks config existence and brain health each session.

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| PostgreSQL + pgvector + ltree | Infrastructure | Available (mybrain already running locally) |
| Docker (optional, Strategy B) | Infrastructure | Available on most dev machines |
| OpenRouter API access | Service | Available (mybrain already configured) |
| mybrain codebase | Starting point | Exists, will be forked |
| atelier-pipeline v1 (Q1/Q2 changes) | Prerequisite | Shipped and committed |

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Stale brain context misleads agent | Agent makes wrong decision based on outdated reasoning | Disk always wins principle. Agents verify brain context against current artifacts. |
| Consolidation produces plausible but wrong reflections | Bad synthesis propagates as institutional "knowledge" | Reflections link to sources. Source thoughts remain accessible. Human can invalidate bad reflections. |
| Conflict detection false positives create alert fatigue | Team ignores real conflicts | Tiered thresholds. LLM classification reduces false positives. Only cross-team contradictions surface to human. |
| Brain becomes a single point of failure | Pipeline breaks when brain is down | Two-gate detection. Graceful fallback. Every gate has baseline behavior. |
| Thought volume exceeds useful retrieval | Search returns too many marginal results | TTL-based deprecation. Consolidation reduces active thought count. Three-axis scoring ranks aggressively. |

## Open Questions

1. **MCP transport for atelier brain** — stdio (same as mybrain current) or HTTP? Decision deferred — stdio for now, revisit when multi-developer networking is needed.
2. **LLM model for conflict classification and consolidation** — use the same OpenRouter routing as embeddings? Separate model selection? Needs cost analysis at scale.
3. **Brain backup and migration** — how are thoughts exported/imported when moving between environments? Not in scope for v1 but needs design before multi-team.
4. **Retro-lessons migration** — should existing `retro-lessons.md` content be seeded into the brain as initial thoughts? Useful for bootstrapping but introduces unstructured legacy content.
