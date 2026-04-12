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
- Graceful pool shutdown with async drain and deadman timeout (ADR-0034 Wave 3 Step 3.4)
- LLM response null-guard wrappers (ADR-0034 Wave 3 Step 3.5)
- XSS escaping in dashboard.html (ADR-0034 Wave 3 Step 3.6)
- CORS headers for HTTP REST API (ADR-0034 Wave 3 Step 3.7)

**Out of scope:**
- Tool handler modifications (already have proper error handling)
- Structured logging (nice-to-have, separate initiative)
- DB health probe / watchdog (separate initiative if needed)
- Process supervisor / restart mechanism (useless for stdio — Claude Code can't reconnect)

## Implemented Additions (ADR-0034 Wave 3)

These subsections document the four scope additions implemented in Wave 3 that were not explicitly listed in the original spec.

### Graceful Pool Shutdown with Async Drain (Step 3.4)

**Context:** When EPIPE, stdin EOF, or a signal triggers `gracefulShutdown()`, the database pool must close cleanly. If in-flight queries stall indefinitely, the process can hang as a zombie.

**Implementation:**
- `pool.end()` returns a Promise that resolves when all active connections have drained
- A 3-second deadman timeout (using `Promise.race()`) forces exit if the pool drain stalls
- The deadman timer calls `.unref()` to prevent it from keeping the event loop alive if pool drain completes first
- Exit code 0 on success; code 1 if the deadman fires

**Code location:** `brain/lib/crash-guards.mjs`, lines 46-52

**Behavior:** `gracefulShutdown()` now awaits `Promise.race([poolEnd().catch(() => {}), deadmanPromise])` before calling `exitFn(0)` or `exitFn(1)`. This ensures the process does not terminate while queries are still in flight, avoiding data corruption on shutdown.

### LLM Response Null-Guard Wrapper (Step 3.5)

**Context:** Both `conflict.mjs` and `consolidation.mjs` parse LLM (OpenRouter / OpenAI) chat-completion responses to extract synthesis or conflict classification results. Before this fix, they accessed `.choices[0].message.content` directly, risking crashes if the response shape was malformed (null `data`, empty `choices` array, missing `message` or `content`).

**Implementation:**
- New module: `brain/lib/llm-response.mjs` exports `assertLlmContent(data, context)`
- Validates response shape: confirms `data` is not null, `choices` is a non-empty array, `message` exists, and `content` is non-empty
- Throws a named `Error` with the text "malformed" (for log pattern-matching) and a truncated 200-char JSON dump of the payload for debugging
- Both `conflict.mjs` and `consolidation.mjs` import and use this function instead of direct property access

**Code locations:**
- `brain/lib/llm-response.mjs` (entire module, 57 lines)
- `brain/lib/conflict.mjs`, line 7 (import), line 61 (usage)
- `brain/lib/consolidation.mjs`, line 10 (import), line 170 (usage)

**Behavior:** Any malformed LLM response now logs an error and returns `isError: true` to the tool caller, rather than crashing the consolidation or conflict cycle.

### XSS Escaping in Dashboard UI (Step 3.6)

**Context:** The Atelier Dashboard renders dynamic data (agent names, metrics, pipeline descriptions) into HTML via `innerHTML` assignments. User-controlled metadata fields could contain HTML tags or JavaScript, creating an XSS vulnerability.

**Implementation:**
- New function in `dashboard.html` (line 952): `escapeHtml(s)` — safely escapes text by setting a DOM element's `textContent` and reading back the escaped `innerHTML`
- All interpolations into `innerHTML` are wrapped in `escapeHtml()` with inline `/* trusted: <reason> */` comments for static literals
- Pattern enforced: every `innerHTML =` assignment either uses static markup marked with a trust comment or concatenates escaped strings
- ~40+ call sites in the dashboard now use `escapeHtml()` for agent names, labels, metrics, timestamps, and other user-facing text

**Code location:** `brain/ui/dashboard.html`, lines 952-1722+

**Behavior:** Agent names, thought descriptions, cost/duration values, and any other dynamic text is HTML-escaped before insertion, preventing script injection through malformed metadata.

### CORS Headers for HTTP REST API (Step 3.7)

**Context:** The brain server provides an HTTP REST API for the dashboard (`/api/health`, `/api/config`, `/api/stats`, `/api/telemetry/*`) and a settings UI (`/ui`). CORS headers are required for the dashboard to make cross-origin requests when served from `http://localhost:PORT/ui`.

**Implementation:**
- `brain/server.mjs` HTTP handler (lines 114-116) sets three CORS headers on all requests:
  - `Access-Control-Allow-Origin: http://localhost:PORT` (scoped to localhost only)
  - `Access-Control-Allow-Headers: Content-Type, Authorization, mcp-session-id`
  - `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
- OPTIONS requests return 204 No Content, allowing preflight requests to succeed
- All other requests proceed normally with the headers attached

**Code location:** `brain/server.mjs`, lines 114-118

**Behavior:** The dashboard and any localhost tools can make XMLHttpRequest/fetch calls to the REST API without CORS preflight blocking. Remote origins are rejected (localhost-only restriction).

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
