# Context Brief

Captures conversational decisions, user corrections, and rejected alternatives.
Reset at the start of each new feature pipeline.

## Scope
Brain MCP server (brain/server.mjs + brain/lib/) hardening for crash resilience. The brain runs as a stdio MCP child process of Claude Code. When it crashes mid-session, tools disappear and can't be recovered without restarting the session. Goal: make the process never crash.

## Key Constraints
- Keep stdio transport (it's what the entire MCP ecosystem uses)
- Do NOT switch to HTTP transport for this — HTTP has real SDK bugs and adds complexity
- Focus on preventing crashes, not recovering from them (stdio can't reconnect)
- Must have comprehensive tests for failure scenarios
- User quote: "the way it's written now is amateur hour" — production-quality hardening expected

## Crash Vectors Identified (from investigation)
1. No uncaughtException/unhandledRejection handlers — any unhandled error kills process
2. No EPIPE handler on stdout — Claude Code disconnect kills process
3. stdin EOF never detected (MCP SDK bug #1814) — zombie processes after client exit
4. setInterval swallows async rejections — timer errors become unhandled rejections
5. Pool config is bare minimum — no max, no timeouts, no statement_timeout
6. No SIGHUP handler — terminal hangup kills without cleanup
7. stderr write errors can crash if stderr pipe is broken

## User Decisions
- Stdio is the right transport (confirmed by research — all official MCP servers use stdio)
- HTTP transport rejected: real SDK bugs (#1699 stack overflow, #1771 dropped notifications, #1726 proxy kills), adds complexity, niche adoption
- Process supervisor (pm2/launchd) rejected: Claude Code can't reconnect to respawned stdio process
- Tests must cover failure scenarios and verify graceful handling

## Rejected Alternatives
- Switch to HTTP/StreamableHTTP transport — SDK bugs, complexity, niche adoption
- Process supervisor wrapper — useless because Claude Code can't reconnect mid-session
- Memory monitoring — server is lightweight, not a realistic crash vector
