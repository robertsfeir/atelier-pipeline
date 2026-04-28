# Context Brief

## Scope
ADR-0053 — Mechanical Brain Capture via Three-Hook Gate. Small pipeline.
Session closed intentionally after architecture phase; resume in fresh session.

## Current State (for session-resume)
- **Phase:** idle. Architecture complete. ADR-0053 accepted. Next: Colby build.
- **ADR:** `docs/architecture/ADR-0053-mechanical-brain-capture-gate.md`
- **Why this exists:** type:agent SubagentStop hooks are silently broken in Claude Code 2.1.121 (GitHub #40010, 0 fires vs 9,006 for type:command). brain-extractor agent never ran. All three replacement hook types confirmed working empirically.

## What Colby Builds

Three hooks + settings wiring + protocol doc update + tests + file deletions.
Full scope is in pipeline-state.md Active Pipeline section.

**Key files:**
- `source/claude/hooks/enforce-brain-capture-pending.sh` — NEW (SubagentStop, writes pending file)
- `source/claude/hooks/enforce-brain-capture-gate.sh` — NEW (PreToolUse on Agent, blocks if pending)
- `source/claude/hooks/clear-brain-capture-pending.sh` — NEW (PostToolUse on agent_capture, clears pending)
- `source/claude/agents/brain-extractor.md` — DELETE
- `source/cursor/agents/brain-extractor.md` — DELETE
- `source/shared/references/pipeline-orchestration.md` — add escape-hatch protocol
- `.claude/settings.json` — remove type:agent entry, add PostToolUse entry (Colby also runs pipeline-setup to sync)

**Pattern to follow:**
- SubagentStop writer: see `source/claude/hooks/log-agent-stop.sh` (never blocks, exits 0 always)
- PreToolUse gate: see `source/claude/hooks/enforce-scout-swarm.sh` (jq parse, agent_id empty guard, fail-open, exit 2 on violation)
- Internal agent_type gating in SubagentStop: see `source/claude/hooks/enforce-colby-stop-verify.sh` (ADR-0050)

## Escape Hatch (brain unavailable)
When `atelier_stats` unreachable → Eva touches `docs/pipeline/.brain-unavailable`.
Gate hook checks for this sentinel and passes through if present.
File cleared on next successful `atelier_stats` ping.

## Confirmed Empirical Evidence
- SubagentStop type:command fires reliably: 9,006 confirmed fires
- PreToolUse type:command on Agent fires reliably: enforce-scout-swarm.sh operational
- PostToolUse type:command on agent_capture MCP tool fires: confirmed 2026-04-28T15:44:06Z (same-second)
- type:agent SubagentStop: 0 fires out of 1,591 qualifying events — confirmed broken (GitHub #40010)

## User Decisions
- Capture must be mechanical (behavioral capture fails under pipeline load — documented lesson)
- type:mcp_tool SubagentStop rejected: hardcoded metadata destroys thought_type discrimination; raw content degrades brain prefetch quality
- Eva curates captures herself (gate forces her to call agent_capture before next agent handoff)
- brain-extractor agent files removed entirely

## How to Resume
Fresh Eva session reads pipeline-state.md + this file. Say "continue" or "build ADR-0053" to kick Colby.
Run scout fan-out (Small sizing → scouts required for Colby per enforce-scout-swarm.sh on Medium+; Small skips scouts — confirm sizing).
