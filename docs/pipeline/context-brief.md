# Context Brief

Captures conversational decisions, user corrections, and rejected alternatives.
Reset at the start of each new feature pipeline.

## Scope
Four pipeline enhancement features, implemented sequentially: #13, #15, #19, #11. All modify source/ templates (not .claude/). Each is a non-code ADR (hooks, persona files, Eva behavior, pipeline config) — skip Roz test spec/authoring, Colby implements, Roz verifies against ADR.

## Key Constraints
- All changes in source/ only, .claude/ resync at end
- Version bump after all four are done (not per-feature)
- #11 (Agent Teams) is experimental — opt-in during /pipeline-setup with warning
- #19 (Sentinel) is optional — opt-in during /pipeline-setup with Semgrep MCP explanation
- #13 (DoR/DoD hook) — warn only (exit 0), never block (exit 2). Scoped to Colby + Roz.

## User Decisions
- Hooks must warn, not block — lesson from retro #003 (stop hook caused infinite loops)
- Sentinel backed by Semgrep MCP (open source, LGPL 2.1, pip installable)
- Agent discovery is filesystem-based — no registry JSON, no manifest, no API
- Users can paste agent markdown into prompt — Eva writes the file + converts to XML format
- Agent Teams requires env var — setup asks user, warns experimental
- "all 4, I already said that" — do not defer #11

## Rejected Alternatives
- Exit 2 blocking hooks for DoR/DoD — rejected due to recursion and retry loop risk
- A2A-style registry with Agent Cards — overengineered, nobody has shipped in production
- Declarative agent-manifest.json — still a separate file to maintain
- Brain-dependent routing as primary mechanism — violates brain-is-optional principle
