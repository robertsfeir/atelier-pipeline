## DoR: Requirements Extracted
**Source:** User conversation (crash investigation + MCP ecosystem research)

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Catch uncaughtException — log and survive, don't crash | Crash vector #1 |
| 2 | Catch unhandledRejection — log and survive, don't crash | Crash vector #1 |
| 3 | Handle EPIPE on stdout — exit cleanly when Claude Code disconnects | Crash vector #2 |
| 4 | Handle errors on stderr — swallow silently (can't log to broken stderr) | Crash vector #7 |
| 5 | Detect stdin EOF — graceful shutdown when client exits (workaround for MCP SDK #1814) | Crash vector #3 |
| 6 | Wrap setInterval callbacks — catch async rejections from timer functions | Crash vector #4 |
| 7 | Harden pool config — explicit max, idleTimeoutMillis, connectionTimeoutMillis | Crash vector #5 |
| 8 | Add SIGHUP handler — clean shutdown on terminal hangup | Crash vector #6 |
| 9 | Comprehensive test suite — tests for every crash vector and recovery path | User requirement |
| 10 | No behavioral changes to tool handlers — existing try/catch is correct | Assumption #5 |

**Retro risks:** Lesson #003 (stop hook race condition) — hooks that duplicate agent-level checks cause loops. Lesson #004 (hung process retry) — if tests involve process spawning, don't sleep-poll-retry on hangs.

---

# Feature Spec: Brain MCP Server Hardening
**Author:** Robert (CPO) | **Date:** 2026-03-31
**Status:** Draft -- Pending Review

## The Problem
The brain MCP server runs as a stdio child process of Claude Code. When it crashes mid-session, all brain tools (agent_capture, agent_search, atelier_stats, etc.) disappear. There is no mid-session recovery — the user must restart the entire Claude Code session. The server has zero crash protection: no uncaught exception handlers, no EPIPE guards, no pool timeouts. A single unhandled error from the DB, embedding API, or pipe break kills the process.

## Who Is This For
Any user running the atelier-pipeline with brain enabled. The brain holds institutional memory (2,935+ thoughts in production). Losing it mid-pipeline forces baseline mode for the rest of the session — no brain reads, no brain writes, degraded context for all agents.

## Business Value
- **Reliability:** Brain stays available for the full session duration instead of dying mid-pipeline
- **KPI:** Zero unplanned brain disconnections per session (currently: at least 1 observed crash per multi-hour session)
- **Measurement:** Track via brain_available status across pipeline runs. Post-hardening, brain should maintain availability through sessions that previously triggered crashes
- **Acceptance:** Brain process survives EPIPE, DB transient errors, embedding API failures, and timer exceptions without dying

## User Stories
1. As a pipeline user, I want the brain server to survive transient DB connection errors so I don't lose brain tools mid-pipeline
2. As a pipeline user, I want the brain server to exit cleanly when Claude Code disconnects (not hang as a zombie)
3. As a pipeline user, I want the brain server to survive embedding API failures during background consolidation without crashing

## User Flow
No user flow changes. The hardening is invisible — the server continues to behave identically for all tool calls. The only observable difference: the server stops crashing.

## Edge Cases and Error Handling
| Scenario | Current Behavior | Expected Behavior |
|----------|-----------------|-------------------|
| Claude Code disconnects (EPIPE on stdout) | Process crash | Clean exit (code 0) |
| DB connection drops during tool call | Tool returns error (correct) | No change — already handled |
| DB connection drops during timer | Unhandled rejection, process crash | Log error, timer continues |
| Embedding API 500 during consolidation | Unhandled rejection, process crash | Log error, skip this cycle |
| stdin EOF (Claude Code exits) | Process hangs as zombie | Graceful shutdown |
| Terminal hangup (SIGHUP) | Process killed without cleanup | Graceful shutdown |
| Pool exhaustion (all connections busy) | Hangs indefinitely | Timeout after 5s, return error |
| Uncaught exception from any source | Process crash | Log error, process survives |
| stderr pipe broken | Potential crash on console.error | Silently swallow |

## Acceptance Criteria
| # | Criterion | Measurement |
|---|-----------|-------------|
| AC-1 | Process survives `process.emit('uncaughtException', new Error('test'))` | Test assertion |
| AC-2 | Process survives `process.emit('unhandledRejection', new Error('test'))` | Test assertion |
| AC-3 | EPIPE on stdout triggers clean exit (code 0), not crash | Test assertion |
| AC-4 | stderr errors are swallowed silently | Test assertion |
| AC-5 | stdin 'end' event triggers graceful shutdown | Test assertion |
| AC-6 | SIGHUP triggers graceful shutdown (timers stopped, pool closed) | Test assertion |
| AC-7 | Pool has explicit max (5), connectionTimeoutMillis (5000), idleTimeoutMillis (30000) | Code inspection test |
| AC-8 | setInterval callbacks catch and log async rejections | Test with mock throwing timer |
| AC-9 | Consolidation timer survives runConsolidation throwing | Test assertion |
| AC-10 | TTL timer survives runTTLEnforcement throwing | Test assertion |
| AC-11 | Existing tool handlers continue to work identically | Existing test suite passes |
| AC-12 | No behavioral changes — all MCP tools return same results | Existing test suite passes |

## Scope
**In scope:**
- Process-level crash guards in server.mjs
- Pool configuration hardening in db.mjs
- Safe timer wrappers in consolidation.mjs and ttl.mjs
- stdin EOF detection in server.mjs
- Comprehensive test suite for all crash vectors

**Out of scope:**
- HTTP transport changes (existing HTTP mode untouched)
- Tool handler modifications (already have proper error handling)
- Structured logging (nice-to-have, separate initiative)
- DB health probe / watchdog (separate initiative if needed)
- Process supervisor / restart mechanism (useless for stdio — Claude Code can't reconnect)

## Non-Functional Requirements
- **Performance:** Zero overhead on happy path — crash guards only fire on errors
- **Compatibility:** No changes to MCP tool interfaces or behavior
- **Test coverage:** Every crash vector has at least one test. Failure scenarios outnumber happy-path tests.

## Dependencies
- Node.js process API (built-in — no new dependencies)
- Existing `pg.Pool` configuration options (already available)
- Existing test infrastructure (`node --test`)

## Risks and Open Questions
| Risk | Mitigation |
|------|------------|
| `uncaughtException` handler masks real bugs during development | Handler logs full stack trace to stderr before suppressing |
| Swallowing exceptions could leave process in inconsistent state | Only suppress at process level; tool handlers still return `isError: true` |
| Pool timeout (5s) may be too aggressive for slow cloud DBs | Make configurable via pool options, start with 5s |

## Timeline Estimate
Small-medium scope. ~30-40 lines of hardening code + 100-150 lines of tests.

## DoD: Verification
| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | uncaughtException handler | Specified | AC-1 |
| 2 | unhandledRejection handler | Specified | AC-2 |
| 3 | EPIPE handling | Specified | AC-3 |
| 4 | stderr error handling | Specified | AC-4 |
| 5 | stdin EOF detection | Specified | AC-5 |
| 6 | SIGHUP handler | Specified | AC-6 |
| 7 | Pool hardening | Specified | AC-7 |
| 8 | Timer safety wrappers | Specified | AC-8, AC-9, AC-10 |
| 9 | No behavioral changes | Specified | AC-11, AC-12 |
| 10 | Comprehensive tests | Specified | AC-1 through AC-12 |

**Grep check:** TODO/FIXME/HACK in spec -> 0
**Template:** All sections filled -- no TBD, no placeholders
