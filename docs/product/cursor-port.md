## DoR: Requirements Extracted
**Source:** User conversation (2026-04-01), brain research (19bee288, b6f772c2, e099e4dc, a96a961a)

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Single repo, dual-target — same source files serve both Claude Code and Cursor | User decision |
| 2 | Full parity — all 12 agents, enforcement hooks, brain MCP, all commands | User decision (feature branch for tester validation) |
| 3 | Cursor Marketplace plugin format (.cursor-plugin/plugin.json) | Brain b6f772c2 |
| 4 | Cursor uses auto-discovery: rules/, agents/, commands/, skills/, hooks/hooks.json, mcp.json | Brain b6f772c2 |
| 5 | Hooks rewrite: shell scripts → hooks/hooks.json pointing to same scripts | Brain 19bee288 |
| 6 | Eva orchestration adaptation — Cursor uses implicit delegation | Brain 19bee288 |
| 7 | Brain MCP server works via Cursor's mcp.json (zero changes to server.mjs) | Brain 19bee288 |
| 8 | CLAUDE.md → AGENTS.md or always-apply rules | Brain 19bee288 |
| 9 | No breaking changes to existing Claude Code files — Cursor files are additive | User constraint |
| 10 | Improvements to one target must carry to the other (shared source/) | User constraint |

**Retro risks:** Behavioral constraints ignored by LLMs (brain a867edc6) — enforcement hooks are critical, must port correctly.

---

# Feature Spec: Cursor Port of Atelier Pipeline
**Author:** Robert (CPO) | **Date:** 2026-04-01
**Status:** Draft — Pending Review

## The Problem

Atelier Pipeline currently only works with Claude Code. Cursor IDE has near-identical primitives (rules, agents, commands, hooks, MCP, plugins) and a growing marketplace, but zero production-grade multi-agent orchestration pipelines exist for it. Users who prefer Cursor or work in mixed-IDE teams cannot use atelier-pipeline. Maintaining a separate fork is not viable — improvements must propagate to both targets from a single source.

## Who Is This For

1. **Cursor users** — developers who prefer Cursor's IDE-first experience and want structured multi-agent orchestration with quality gates.
2. **Mixed-IDE teams** — organizations where some developers use Claude Code and others use Cursor, sharing the same repo and pipeline configuration.
3. **Existing atelier users** — who want to try the pipeline in Cursor without losing their Claude Code setup.

## Business Value

- **Market expansion:** First-to-market with an enforced multi-agent pipeline for Cursor. No competitor exists (brain research confirmed).
- **User growth:** Cursor's user base is large and actively seeking orchestration tools.
- **Reduced maintenance:** Single source of truth means every improvement benefits both platforms automatically.

**KPIs:**

| KPI | Definition | Measurement | Timeframe | Acceptance |
|-----|-----------|-------------|-----------|------------|
| Tester validation | Feature branch tested by 3+ colleagues in Cursor | Count of testers who complete a full pipeline run | 30 days | 3+ testers complete at least 1 full pipeline |
| Feature parity | All 12 agents functional in Cursor | Count of agents that successfully complete their role | During testing | 12/12 agents work |
| Hook enforcement | All 3 enforcement hooks block correctly in Cursor | Count of blocked violation attempts | During testing | 100% of violations blocked |

## User Stories

### US-1: Cursor plugin installation
As a Cursor user, I install atelier-pipeline from the Cursor Marketplace (or local testing path) and get all 12 agent personas, rules, commands, enforcement hooks, and brain MCP integration — the same experience Claude Code users get.

### US-2: Shared source, dual output
As a maintainer, when I update a file in `source/`, the change is available to both Claude Code and Cursor users. I don't maintain two copies of any agent persona, rule, or command.

### US-3: Eva orchestration in Cursor
As a Cursor user, Eva orchestrates my pipeline the same way she does in Claude Code — routing to agents, managing phase transitions, enforcing quality gates. The orchestration rules load as always-apply rules.

### US-4: Enforcement hooks in Cursor
As a Cursor user, the enforcement hooks (path enforcement, sequencing, git ops) block agents from writing outside their lanes, just like in Claude Code. Hooks are configured via hooks/hooks.json and call the same shell scripts.

### US-5: Brain integration in Cursor
As a Cursor user, I run /brain-setup and the brain MCP server connects via mcp.json. Brain captures, searches, and telemetry work identically to Claude Code.

### US-6: Setup experience in Cursor
As a Cursor user, I run a setup skill that walks me through configuration — the same questions as Claude Code's /pipeline-setup (tech stack, test commands, branching strategy, optional features).

## User Flow

### Installation (Cursor Marketplace)
```
Install atelier-pipeline from Cursor Marketplace
  → Plugin auto-discovers: rules/, agents/, commands/, skills/, hooks/, mcp.json
  → Run /pipeline-setup skill to configure project-specific values
  → Pipeline is ready
```

### Installation (local testing — feature branch)
```
ln -s /path/to/atelier-pipeline ~/.cursor/plugins/local/atelier-pipeline
  → Restart Cursor
  → Run /pipeline-setup
```

## Edge Cases and Error Handling

| Case | Handling |
|------|----------|
| User has both Claude Code and Cursor in same project | Both .claude/ and .cursor/ can coexist — different directories, no conflict |
| Cursor hook script fails (wrong path, permission) | Hook fails open by default; add failClosed: true for enforcement hooks |
| Brain MCP server not configured | Pipeline runs in baseline mode (same as Claude Code) |
| CURSOR_PROJECT_DIR vs CLAUDE_PROJECT_DIR | Cursor provides both as aliases in hook env vars |
| Cursor's model routing differs from Claude Code's | Agent personas specify model in frontmatter; Cursor respects this |
| Plugin auto-discovery conflicts with manifest paths | Manifest paths replace auto-discovery — use explicit paths for control |

## Acceptance Criteria

| # | Criterion | Measurable |
|---|-----------|------------|
| AC-1 | .cursor-plugin/plugin.json exists with valid manifest | File present, valid JSON |
| AC-2 | Cursor auto-discovers all 12 agent personas from agents/ | All agents available in Cursor |
| AC-3 | Cursor auto-discovers all rules from rules/ | Rules loaded (always-apply and path-scoped) |
| AC-4 | Cursor auto-discovers all commands from commands/ | Commands available via / prefix |
| AC-5 | hooks/hooks.json registers all enforcement hooks | preToolUse events configured with failClosed: true |
| AC-6 | mcp.json registers brain MCP server | Brain tools available in Cursor |
| AC-7 | Enforcement hooks block path violations in Cursor | Test: agent attempts write outside lane → blocked |
| AC-8 | Enforcement hooks block sequencing violations | Test: Ellis without Roz QA → blocked |
| AC-9 | Enforcement hooks block git ops from main thread | Test: Eva runs git commit → blocked |
| AC-10 | Eva orchestration works via always-apply rules | Eva persona loads on every chat |
| AC-11 | /pipeline-setup skill configures project | Setup completes with project-specific values |
| AC-12 | Brain MCP connects and brain tools work | agent_capture and agent_search succeed |
| AC-13 | Existing Claude Code files unchanged | git diff on .claude/ shows zero changes |
| AC-14 | source/ directory is shared — not duplicated | Cursor plugin points to same source/ files |

## Scope

### In scope
- .cursor-plugin/plugin.json manifest
- Cursor-compatible directory structure (rules/, agents/, commands/, skills/)
- hooks/hooks.json pointing to existing shell scripts in source/claude/hooks/
- mcp.json for brain MCP server
- AGENTS.md (Cursor equivalent of CLAUDE.md) or always-apply rules
- /pipeline-setup skill adapted for Cursor
- Eva orchestration as always-apply rules
- Local testing path (symlink to ~/.cursor/plugins/local/)

### Out of scope
- Cursor Marketplace publication (after tester validation)
- Cursor-specific features not in Claude Code (prompt hooks, Agent Teams differences)
- Modifying existing Claude Code plugin structure
- Cursor-specific UI components or themes
- Supporting Cursor versions older than current stable

## API Contracts

N/A — no new APIs. Brain MCP server is unchanged.

## Non-Functional Requirements

| NFR | Requirement |
|-----|-------------|
| Zero duplication | Agent personas, rules, commands exist once in source/ — both plugins reference them |
| Additive only | No changes to .claude-plugin/, .claude/, or existing Claude Code files |
| Same shell scripts | Hooks call the same enforce-*.sh scripts — logic is not duplicated |
| Platform detection | Hook scripts detect CURSOR_PROJECT_DIR or CLAUDE_PROJECT_DIR for path resolution |

## Dependencies

| Dependency | Required by | Risk |
|-----------|-------------|------|
| Cursor IDE (current stable) | All | None — target platform |
| jq | Enforcement hooks | Low — already required for Claude Code |
| Node.js >= 18 | Brain MCP server | Low — already required |
| PostgreSQL + pgvector | Brain (optional) | Low — same as Claude Code |

## Risks and Open Questions

| # | Risk/Question | Mitigation |
|---|--------------|------------|
| 1 | Cursor's hook stdin format may differ from Claude Code's | Test enforcement hooks early — they parse JSON from stdin |
| 2 | Cursor's subagent type names may differ (generalPurpose vs general-purpose) | Check Cursor docs for exact enum values |
| 3 | Eva's orchestration relies on Claude Code's Agent tool — Cursor may use different invocation | Eva's rules describe behavior; Cursor's agent delegates based on descriptions |
| 4 | Cursor may not support all frontmatter fields we use | Test each agent persona loads correctly |
| 5 | Plugin auto-discovery may not handle our nested source/ structure | Use explicit manifest paths if auto-discovery doesn't work |

## Timeline Estimate

Medium pipeline. Estimated 3-4 ADR steps:
1. Plugin structure (manifest, directory layout, AGENTS.md)
2. Hooks adaptation (hooks.json, platform detection in shell scripts)
3. Rules and commands adaptation (frontmatter conversion)
4. Setup skill and brain MCP wiring

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Single repo, dual-target | Done | Same source/, two plugin manifests |
| 2 | Full parity | Done | 12 agents, hooks, brain, commands |
| 3 | Cursor plugin format | Done | .cursor-plugin/plugin.json |
| 4 | Auto-discovery structure | Done | rules/, agents/, commands/, etc. |
| 5 | Hooks via hooks.json | Done | preToolUse with failClosed |
| 6 | Eva orchestration | Done | Always-apply rules |
| 7 | Brain MCP | Done | mcp.json |
| 8 | AGENTS.md | Done | Cursor project instructions |
| 9 | No Claude Code changes | Done | .claude/ untouched |
| 10 | Shared source/ | Done | Both plugins reference source/ |

**Grep check:** TODO/FIXME/HACK/XXX in output files -> 0
**Template:** All sections filled — no TBD, no placeholders
