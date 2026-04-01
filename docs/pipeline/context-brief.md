# Context Brief

Captures conversational decisions, user corrections, and rejected alternatives.
Reset at the start of each new feature pipeline.

## Scope
Port atelier-pipeline to work with Cursor IDE. Cursor has near-1:1 feature parity with Claude Code's primitives: .cursor/rules/ (with YAML frontmatter), .cursor/agents/ (subagent personas), .cursor/commands/, .cursor/hooks.json, MCP integration, and a plugin marketplace. The port produces a parallel set of Cursor-compatible files alongside the existing Claude Code files.

## Key Constraints
- Most files are markdown — they port with frontmatter adjustments
- Hooks need rewriting from shell scripts (Claude Code) to .cursor/hooks.json format (Cursor)
- Eva orchestration adaptation is the hardest part — Cursor uses implicit delegation, not explicit subagent invocation
- Brain MCP server works as-is via Cursor's MCP config (zero changes to server.mjs)
- No breaking changes to existing Claude Code files — Cursor files are additive

## Brain Research Reference
- Brain thought 19bee288: full Cursor port feasibility analysis (2026-04-01)
- Key sources: cursor.com/docs/rules, cursor.com/docs/hooks, cursor.com/docs/subagents, cursor.com/blog/marketplace

## User Decisions
- Single repo, dual-target — improvements to source/ carry to both Claude Code and Cursor (decided 2026-04-01)
- Full parity on feature branch — all 12 agents, hooks, brain MCP. Testers validate before marketplace publication.
- No-repo support: ask user during /pipeline-setup Step 1 "Do you have a git repository?" BEFORE branching strategy. If no: set git_available: false, skip branching strategy, skip platform CLI, skip CI Watch. Git-dependent features degrade gracefully at runtime (Ellis → reporter, Poirot skipped, Roz uses file listing). Fold into ADR-0019.

## Rejected Alternatives
- Separate repo for Cursor — rejected: maintenance burden, improvements don't propagate
- Tiered launch (core agents only for Cursor) — rejected: feature branch is for validation, ship everything
- Eva detects git at boot — rejected: detect once at setup, not every session
