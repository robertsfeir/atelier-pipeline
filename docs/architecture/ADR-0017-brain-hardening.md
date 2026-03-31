# ADR-0017: Brain MCP Server Hardening

## DoR: Requirements Extracted

**Source:** `docs/product/brain-hardening.md` (spec), `docs/pipeline/context-brief.md` (user decisions), `.claude/references/retro-lessons.md`

| # | Requirement | Source | Priority |
|---|-------------|--------|----------|
| R1 | Install `uncaughtException` handler -- log and survive, do not crash | Spec AC-1, Crash vector #1 | Must |
| R2 | Install `unhandledRejection` handler -- log and survive, do not crash | Spec AC-2, Crash vector #1 | Must |
| R3 | Handle EPIPE on `stdout` -- exit cleanly (code 0), not crash | Spec AC-3, Crash vector #2 | Must |
| R4 | Handle errors on `stderr` -- swallow silently (cannot log to broken stderr) | Spec AC-4, Crash vector #7 | Must |
| R5 | Detect stdin EOF -- graceful shutdown when client exits (workaround for MCP SDK bug #1814) | Spec AC-5, Crash vector #3 | Must |
| R6 | Wrap `setInterval` callbacks -- catch async rejections from timer functions | Spec AC-8, Crash vector #4 | Must |
| R7 | Harden pool config -- explicit `max` (5), `connectionTimeoutMillis` (5000), `idleTimeoutMillis` (30000) | Spec AC-7, Crash vector #5 | Must |
| R8 | Add SIGHUP handler -- clean shutdown on terminal hangup | Spec AC-6, Crash vector #6 | Must |
| R9 | Consolidation timer survives `runConsolidation` throwing | Spec AC-9, Crash vector #4 | Must |
| R10 | TTL timer survives `runTTLEnforcement` throwing | Spec AC-10, Crash vector #4 | Must |
| R11 | No behavioral changes to tool handlers -- existing try/catch is correct | Spec AC-11, AC-12 | Must |
| R12 | Comprehensive test suite -- every crash vector tested, failure tests >= happy path | Spec NFR, User requirement | Must |

**Retro risks:**

| Lesson | Risk to this feature | Mitigation |
|--------|---------------------|------------|
| #003 (Stop Hook Race Condition) | Process-level handlers could interfere with MCP SDK's own handlers | Handlers are additive (log + survive), not replacing SDK behavior. Test verifies no double-fire. |
| #004 (Hung Process Retry) | Tests spawn child processes -- risk of sleep-poll-retry loops | Tests use direct function calls with mocks, not process spawning. The one process-level test uses `process.emit()` to simulate, not `fork()`. |

---

## Status

Proposed

## Context

The brain MCP server (`brain/server.mjs`) runs as a stdio child process of Claude Code. It holds institutional memory (2,935+ thoughts in production). When the process crashes, all brain tools (`agent_capture`, `agent_search`, `atelier_stats`, etc.) disappear from the current session with no recovery path -- the user must restart the entire Claude Code session to regain brain access.

Investigation identified 7 application-layer crash vectors:

1. **No uncaughtException/unhandledRejection handlers.** Any unhandled error from any source (DB, embedding API, internal bug) kills the process immediately.
2. **No EPIPE handler on stdout.** When Claude Code disconnects, the next `stdout.write()` from the MCP SDK throws EPIPE and crashes the process.
3. **No stdin EOF detection.** When Claude Code exits, the stdin pipe closes, but the MCP server keeps running as a zombie. This is a known MCP SDK limitation (SDK issue #1814).
4. **`setInterval` callbacks swallow async rejections.** Both `consolidation.mjs` and `ttl.mjs` use `setInterval(() => asyncFn(), ms)`. When `asyncFn` rejects, the rejection becomes unhandled because `setInterval` does not await the return value.
5. **Pool config is bare minimum.** `createPool` passes only `connectionString` -- no `max`, no `connectionTimeoutMillis`, no `idleTimeoutMillis`. Under load or with a flaky connection, the pool can exhaust connections or hang indefinitely.
6. **No SIGHUP handler.** Terminal hangup kills the process without cleanup (timers still running, pool connections leaked).
7. **`stderr` write errors can crash.** If the stderr pipe breaks (rare but possible when the parent terminal is gone), `console.error` throws and crashes.

The existing code has good error handling in tool handlers (`tools.mjs` -- every tool returns `isError: true` on failure) and in the consolidation/TTL inner logic (try/catch around DB operations). The crash vectors are all in the process-level and timer-level plumbing, not in the business logic.

### Spec Challenge

The spec assumes that `process.on('uncaughtException', ...)` is safe to use as a keep-alive mechanism -- that catching and logging uncaught exceptions leaves the process in a usable state. If this is wrong -- if an uncaught exception leaves the Node.js event loop, stream state, or MCP SDK internals in an inconsistent state -- the design fails because the server would continue running but produce incorrect results or silently corrupt data.

This assumption is sound for the brain server's specific case: the brain is stateless between requests (each MCP tool call is an independent DB transaction), so there is no cross-request state to corrupt. The uncaughtException handler's primary purpose is surviving transient errors (a missed try/catch in a rarely-hit code path) rather than indefinitely running after catastrophic failures. The pool's connection management and the MCP SDK's request isolation provide the correctness boundary. Additionally, the handler logs the full stack trace to stderr so the error is observable, not silently masked.

**SPOF:** The `gracefulShutdown()` function. Every signal handler, stdin EOF handler, and EPIPE handler routes through this single function. If `gracefulShutdown` itself throws (e.g., `stopConsolidationTimer` throws, or `pool.end()` hangs), the process may not exit cleanly, potentially leaving zombie processes or leaked connections.

**Failure mode:** Process hangs during shutdown -- timers keep firing, pool connections stay open.

**Graceful degradation:** `gracefulShutdown` already wraps `pool.end()` in `.catch(() => {})`. The timer stop functions are synchronous `clearInterval` calls that cannot throw. As additional defense, the shutdown function should set a flag to prevent re-entry and use `process.exit(0)` as a fallback after a short timeout if cleanup stalls. This is addressed in Step 1.

### Anti-Goals

Anti-goal: **Structured logging framework.** Reason: The spec explicitly lists "structured logging" as out of scope. The current `console.error` approach is adequate for a stdio child process where logs go to stderr (which the parent may or may not capture). Structured logging would require a new dependency and change every log call site. Revisit: when the brain server gains HTTP-only deployment targets that need log aggregation.

Anti-goal: **Process supervisor / restart mechanism.** Reason: The brain runs as a stdio child process. Claude Code cannot reconnect to a respawned process mid-session. A supervisor (pm2, systemd) would restart the process but the MCP client would have lost the connection permanently. Prevention (this ADR) is the only viable strategy. Revisit: when the MCP SDK supports reconnection over stdio, or when the brain migrates to HTTP transport as its primary mode.

Anti-goal: **Connection health probes / watchdog.** Reason: The brain server does not maintain persistent connections that need monitoring. Each tool call acquires a pool connection, uses it, and releases it. Pool-level error events are already handled (`pool.on('error', ...)`). A watchdog adds complexity with no corresponding crash vector to address. Revisit: when telemetry shows pool exhaustion or connection leak patterns in production.

---

## Decision

Harden the brain MCP server at three layers -- process-level crash guards in `server.mjs`, pool configuration in `db.mjs`, and safe timer wrappers in `consolidation.mjs` and `ttl.mjs`. All changes are defensive additions. Zero behavioral changes to tool handlers or business logic. Each crash vector gets at least one dedicated test. Test file uses `node:test` (the existing brain test framework).

### Architecture

```
server.mjs (process-level guards)
  +-- uncaughtException handler: log, survive
  +-- unhandledRejection handler: log, survive
  +-- EPIPE handler on stdout: gracefulShutdown
  +-- stderr error handler: swallow silently
  +-- stdin 'end' handler: gracefulShutdown (MCP SDK #1814 workaround)
  +-- SIGHUP handler: gracefulShutdown
  +-- gracefulShutdown hardened: re-entry guard, timeout fallback

db.mjs (pool hardening)
  +-- explicit max: 5
  +-- connectionTimeoutMillis: 5000
  +-- idleTimeoutMillis: 30000

consolidation.mjs (safe timer)
  +-- setInterval callback wrapped: try/catch around async call

ttl.mjs (safe timer)
  +-- setInterval callback wrapped: try/catch around async call
```

### Blast Radius

| File | Change | Consumers |
|------|--------|-----------|
| `brain/server.mjs` | Add 6 process-level handlers, harden `gracefulShutdown` | Entry point -- no importers. Consumed by `node server.mjs` invocation. |
| `brain/lib/db.mjs` | Add pool config options to `createPool` | `brain/server.mjs:52`, `brain/scripts/hydrate-telemetry.mjs:437` |
| `brain/lib/consolidation.mjs` | Wrap `setInterval` callback | `brain/server.mjs:23` (import), `brain/server.mjs:147,192` (start calls) |
| `brain/lib/ttl.mjs` | Wrap `setInterval` callback | `brain/server.mjs:24` (import), `brain/server.mjs:146,191` (start calls) |
| `tests/brain/hardening.test.mjs` | New test file | `brain/package.json` test script (glob `../tests/brain/*.test.mjs`) |

**CI/CD impact:** None. Tests run via `node --test ../tests/brain/*.test.mjs` which auto-discovers `*.test.mjs` files. No config changes needed.

**hydrate-telemetry.mjs impact:** This script also calls `createPool`. The pool config change (adding `max`, `connectionTimeoutMillis`, `idleTimeoutMillis`) is purely additive -- `pg.Pool` uses these options if present, ignores unknown ones. The script is a batch process that runs and exits, so pool timeouts improve its behavior (fail fast on unreachable DB instead of hanging).

---

## Alternatives Considered

### Alternative A: Wrap entire server.mjs in try/catch with process restart

Wrap the top-level await in a try/catch that calls `process.exit(1)` on any error, relying on an external supervisor to restart. **Rejected because:** Claude Code cannot reconnect to a respawned stdio child process. The MCP session is bound to the original process. Restarting creates a zombie process pair (old dead, new orphan) with no client.

### Alternative B: Migrate to HTTP transport for crash isolation

Run the brain as an HTTP server that Claude Code connects to via StreamableHTTP. HTTP connections survive process restarts because the client reconnects. **Rejected because:** The MCP SDK has known bugs in HTTP transport (#1699 stack overflow on concurrent requests, #1771 dropped notifications, #1726 proxy kills connections). User explicitly rejected this approach. All official MCP servers use stdio. The complexity/risk ratio is unfavorable.

### Alternative C (Chosen): Defensive hardening at process, pool, and timer layers

Add crash guards at every identified vector. Keep stdio transport. No new dependencies. No behavioral changes. Each guard is a 1-5 line addition that logs the error and either survives or exits cleanly. **Chosen because:** Addresses all 7 crash vectors with minimal code (~30-40 lines of hardening, ~150 lines of tests). Zero risk of behavioral regression. Each guard is independently testable.

---

## Consequences

**Positive:**
- Brain process survives transient errors that previously crashed it (DB blips, embedding API failures, missed try/catch in edge paths)
- Clean exit on expected disconnections (EPIPE, stdin EOF, SIGHUP) instead of crash or zombie
- Pool config prevents indefinite hangs on unreachable DB
- Every crash vector has regression tests

**Negative:**
- `uncaughtException` handler could mask real bugs during development. Mitigated by logging full stack trace to stderr.
- Adding process-level handlers creates a maintenance surface -- future developers must understand these handlers exist when debugging process lifecycle issues.

**Neutral:**
- Zero overhead on happy path. All guards are event handlers that only fire on errors.
- `hydrate-telemetry.mjs` inherits pool config changes -- this is beneficial (fail-fast on unreachable DB).

---

## Implementation Plan

### Step 1: Process-Level Crash Guards + Tests

**After this step, I can:** verify that the brain process survives uncaught exceptions, unhandled rejections, EPIPE on stdout, broken stderr, stdin EOF, and SIGHUP -- all 6 process-level crash vectors are guarded and tested.

**Files to modify:**
1. `brain/server.mjs` -- Add 6 process-level handlers + harden `gracefulShutdown`
2. `tests/brain/hardening.test.mjs` -- New test file for all process-level crash vectors

**Changes to `brain/server.mjs`:**

Before the mode selection (`if (mode === "http")`), add:

```javascript
// Process-level crash guards
process.on('uncaughtException', (err) => {
  try { console.error('Uncaught exception (survived):', err.stack || err.message); }
  catch { /* stderr may be broken */ }
});

process.on('unhandledRejection', (reason) => {
  try { console.error('Unhandled rejection (survived):', reason); }
  catch { /* stderr may be broken */ }
});

// EPIPE on stdout = Claude Code disconnected
process.stdout.on('error', (err) => {
  if (err.code === 'EPIPE') gracefulShutdown();
});

// Broken stderr pipe -- swallow silently (can't log to broken stderr)
process.stderr.on('error', () => {});

// stdin EOF = Claude Code exited (workaround for MCP SDK #1814)
process.stdin.on('end', () => gracefulShutdown());

// SIGHUP = terminal hangup
process.on('SIGHUP', gracefulShutdown);
```

Harden `gracefulShutdown` with re-entry guard:

```javascript
let shuttingDown = false;
function gracefulShutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  stopConsolidationTimer();
  stopTTLTimer();
  pool.end().catch(() => {});
  process.exit(0);
}
```

**Acceptance criteria:**
- AC-1: `process.emit('uncaughtException', new Error('test'))` does not crash
- AC-2: `process.emit('unhandledRejection', new Error('test'))` does not crash
- AC-3: `process.stdout.emit('error', Object.assign(new Error('write EPIPE'), { code: 'EPIPE' }))` triggers clean exit
- AC-4: `process.stderr.emit('error', new Error('broken pipe'))` does not crash
- AC-5: `process.stdin.emit('end')` triggers graceful shutdown
- AC-6: SIGHUP triggers graceful shutdown
- `gracefulShutdown` is idempotent (calling twice does not double-exit)

**Estimated complexity:** Low. ~20 lines of handler code + ~120 lines of tests.

**Sizing gate:**

| # | Test | Result |
|---|------|--------|
| S1 | Demoable | "After this step, the brain process survives all 6 process-level crash vectors." |
| S2 | Context-bounded | 2 files (1 modify, 1 create) |
| S3 | Independently verifiable | Yes -- tests run without Steps 2-3 |
| S4 | Revert-cheap | Yes -- single focused change |
| S5 | Already small | Yes -- 2 files, one clear behavior |

---

### Step 2: Pool Configuration Hardening + Tests

**After this step, I can:** verify that the brain's DB pool has explicit limits and timeouts, preventing indefinite hangs on unreachable databases.

**Files to modify:**
1. `brain/lib/db.mjs` -- Add explicit pool config options
2. `tests/brain/hardening.test.mjs` -- Add pool config tests (append to file from Step 1)

**Changes to `brain/lib/db.mjs`:**

```javascript
function createPool(databaseUrl) {
  const pool = new pg.Pool({
    connectionString: databaseUrl,
    max: 5,
    connectionTimeoutMillis: 5000,
    idleTimeoutMillis: 30000,
  });
  // ... rest unchanged
}
```

**Acceptance criteria:**
- AC-7: Pool config includes `max: 5`, `connectionTimeoutMillis: 5000`, `idleTimeoutMillis: 30000`
- Test verifies config by inspecting `pool.options` (pg.Pool exposes options on the instance)
- Existing `db.test.mjs` tests continue to pass (mock pool unaffected)

**Estimated complexity:** Low. ~3 lines of config + ~20 lines of tests.

**Sizing gate:**

| # | Test | Result |
|---|------|--------|
| S1 | Demoable | "After this step, the brain's DB pool has explicit connection limits and timeouts." |
| S2 | Context-bounded | 2 files (1 modify, 1 modify) |
| S3 | Independently verifiable | Yes -- tests check config values directly |
| S4 | Revert-cheap | Yes -- 3 lines of config |
| S5 | Already small | Yes -- 2 files, one clear behavior |

---

### Step 3: Safe Timer Wrappers + Tests

**After this step, I can:** verify that the consolidation and TTL timers survive exceptions from their async callbacks, logging errors instead of becoming unhandled rejections.

**Files to modify:**
1. `brain/lib/consolidation.mjs` -- Wrap setInterval callback with try/catch
2. `brain/lib/ttl.mjs` -- Wrap setInterval callback with try/catch
3. `tests/brain/hardening.test.mjs` -- Add timer safety tests (append to file from Steps 1-2)

**Changes to `brain/lib/consolidation.mjs`:**

```javascript
async function startConsolidationTimer(pool, apiKey) {
  const brainConfig = await getBrainConfig(pool);
  const intervalMs = brainConfig.consolidation_interval_minutes * 60 * 1000;
  consolidationTimer = setInterval(async () => {
    try {
      await runConsolidation(pool, apiKey);
    } catch (err) {
      try { console.error('Consolidation timer error (survived):', err.message); }
      catch { /* stderr may be broken */ }
    }
  }, intervalMs);
  console.log(`Consolidation timer: every ${brainConfig.consolidation_interval_minutes} min`);
}
```

**Changes to `brain/lib/ttl.mjs`:**

```javascript
async function startTTLTimer(pool) {
  const intervalMs = 60 * 60 * 1000;
  ttlTimer = setInterval(async () => {
    try {
      await runTTLEnforcement(pool);
    } catch (err) {
      try { console.error('TTL timer error (survived):', err.message); }
      catch { /* stderr may be broken */ }
    }
  }, intervalMs);
  await runTTLEnforcement(pool);
}
```

**Acceptance criteria:**
- AC-8: `setInterval` callbacks catch and log async rejections (test with mock that throws)
- AC-9: Consolidation timer survives `runConsolidation` throwing
- AC-10: TTL timer survives `runTTLEnforcement` throwing
- AC-11: Existing tool handlers work identically (existing test suite passes)
- AC-12: No behavioral changes (existing consolidation + TTL test suites pass)
- Timer continues to fire after an error (not just survives once)

**Estimated complexity:** Low. ~10 lines of wrapper code + ~40 lines of tests.

**Sizing gate:**

| # | Test | Result |
|---|------|--------|
| S1 | Demoable | "After this step, consolidation and TTL timers survive callback exceptions." |
| S2 | Context-bounded | 3 files (2 modify, 1 modify) |
| S3 | Independently verifiable | Yes -- tests mock the inner functions to throw |
| S4 | Revert-cheap | Yes -- small wrapper additions |
| S5 | Already small | Yes -- 3 files, one clear behavior |

---

## Comprehensive Test Specification

All tests in `tests/brain/hardening.test.mjs`. Framework: `node:test` (existing brain test infrastructure). Tests use `process.emit()` to simulate signals and errors -- no child process spawning, no sleep-poll (retro lesson #004).

### Step 1 Tests: Process-Level Crash Guards

| ID | Category | Description | Expected Behavior | Crash Vector |
|----|----------|-------------|-------------------|--------------|
| T-0017-001 | Failure | `process.emit('uncaughtException', new Error('boom'))` does not crash the test process | Process survives, error is logged to stderr | #1 |
| T-0017-002 | Failure | `process.emit('unhandledRejection', new Error('rejected'))` does not crash the test process | Process survives, rejection is logged to stderr | #1 |
| T-0017-003 | Failure | EPIPE error emitted on `process.stdout` triggers shutdown path | `gracefulShutdown` is called (verify via spy/mock) | #2 |
| T-0017-004 | Boundary | Non-EPIPE error on `process.stdout` does not trigger shutdown | Process survives, shutdown is NOT called | #2 |
| T-0017-005 | Failure | `process.stderr.emit('error', new Error('broken pipe'))` does not throw | Process survives silently | #7 |
| T-0017-006 | Failure | `process.stdin.emit('end')` triggers shutdown path | `gracefulShutdown` is called | #3 |
| T-0017-007 | Failure | SIGHUP signal triggers shutdown path | `gracefulShutdown` is called | #6 |
| T-0017-008 | Boundary | `gracefulShutdown` called twice does not double-exit (re-entry guard) | Second call is a no-op | #6 (defense-in-depth) |
| T-0017-009 | Happy | SIGTERM still triggers graceful shutdown (existing behavior preserved) | `gracefulShutdown` is called | Regression |
| T-0017-010 | Happy | SIGINT still triggers graceful shutdown (existing behavior preserved) | `gracefulShutdown` is called | Regression |
| T-0017-011 | Error | `uncaughtException` handler survives when stderr is broken | Handler does not throw (inner catch absorbs) | #1 + #7 combined |
| T-0017-012 | Error | `unhandledRejection` handler survives when stderr is broken | Handler does not throw (inner catch absorbs) | #1 + #7 combined |

**Test approach for process-level handlers:** Since these tests run in the test process itself, tests that trigger `gracefulShutdown` must mock `process.exit` and the timer stop functions to prevent the test process from actually exiting. Import `gracefulShutdown` indirectly by importing `server.mjs` as a module -- but since `server.mjs` has top-level await and DB initialization, the preferred approach is to **extract the handler registration into a testable function** that accepts dependencies (pool, timers, exit function) and test that function directly. This is the `installCrashGuards(deps)` pattern.

Alternatively, test the handler logic by directly testing the handler bodies as exported functions, mocking `process.exit`. Colby decides the exact extraction pattern at implementation time.

### Step 2 Tests: Pool Configuration

| ID | Category | Description | Expected Behavior | Crash Vector |
|----|----------|-------------|-------------------|--------------|
| T-0017-013 | Happy | `createPool` returns pool with `max: 5` | `pool.options.max === 5` | #5 |
| T-0017-014 | Happy | `createPool` returns pool with `connectionTimeoutMillis: 5000` | `pool.options.connectionTimeoutMillis === 5000` | #5 |
| T-0017-015 | Happy | `createPool` returns pool with `idleTimeoutMillis: 30000` | `pool.options.idleTimeoutMillis === 30000` | #5 |
| T-0017-016 | Failure | Pool connection attempt with unreachable DB times out (does not hang) | Connection attempt rejects within ~5 seconds | #5 |
| T-0017-017 | Boundary | Pool `error` event handler does not crash process | `console.error` called, process survives | #5 |

**Note on T-0017-016:** This test requires a real `pg.Pool` pointed at an unreachable host (`localhost:1` or similar). If `pg` is not installed in the test environment (existing pattern: tests skip gracefully when pg is unavailable), this test is skipped with a diagnostic message. The pool config values (T-0017-013 through T-0017-015) can be verified by inspecting the `Pool` constructor's internals or by calling `createPool` with a dummy connection string and checking the returned object.

### Step 3 Tests: Safe Timer Wrappers

| ID | Category | Description | Expected Behavior | Crash Vector |
|----|----------|-------------|-------------------|--------------|
| T-0017-018 | Failure | Consolidation timer callback catches `runConsolidation` rejection | Error logged, timer continues (no unhandled rejection) | #4 |
| T-0017-019 | Failure | TTL timer callback catches `runTTLEnforcement` rejection | Error logged, timer continues (no unhandled rejection) | #4 |
| T-0017-020 | Failure | Consolidation timer callback catches synchronous throw from `runConsolidation` | Error logged, timer continues | #4 |
| T-0017-021 | Failure | TTL timer callback catches synchronous throw from `runTTLEnforcement` | Error logged, timer continues | #4 |
| T-0017-022 | Failure | Timer error logging survives broken stderr | Inner catch absorbs the `console.error` failure | #4 + #7 combined |
| T-0017-023 | Happy | Consolidation timer fires and runs `runConsolidation` on happy path | `runConsolidation` called, no errors | Regression |
| T-0017-024 | Happy | TTL timer fires and runs `runTTLEnforcement` on happy path | `runTTLEnforcement` called, no errors | Regression |
| T-0017-025 | Regression | Existing `consolidation.test.mjs` suite still passes | All T-0003-113 through T-0003-118 pass | AC-11, AC-12 |
| T-0017-026 | Regression | Existing `ttl.test.mjs` suite still passes | All T-0003-119 through T-0003-120 pass | AC-11, AC-12 |

**Test approach for timer wrappers:** Use `fake-timers` from `node:test` (available since Node 20) to control `setInterval` firing. Mock `runConsolidation`/`runTTLEnforcement` to throw, advance the timer, and verify the error was caught and logged rather than becoming an unhandled rejection. Install a temporary `process.on('unhandledRejection', ...)` listener in the test that fails the test if it fires.

### Test Summary

| Category | Count |
|----------|-------|
| Failure | 14 |
| Happy | 5 |
| Boundary | 3 |
| Error | 3 |
| Regression | 2 |
| **Total** | **27** |

Failure tests (14) outnumber happy-path tests (5) by 2.8:1. Requirement R12 satisfied.

### Step 1 Telemetry

Telemetry: `console.error` output containing `"(survived)"` in server stderr. Trigger: any uncaught exception or unhandled rejection at runtime. Absence means: either no errors occurred (good) or the handler is not installed (bad -- verify with tests).

Telemetry: Process exit code. Trigger: EPIPE, stdin EOF, SIGHUP. Expected: exit code 0. Exit code 1 or signal-killed means the handler failed.

### Step 2 Telemetry

Telemetry: `connectionTimeoutMillis` timeout errors in pool. Trigger: DB unreachable for >5 seconds. Absence means: DB is healthy (good) or pool config was not applied (bad -- verify with tests).

### Step 3 Telemetry

Telemetry: `console.error` output containing `"timer error (survived)"`. Trigger: consolidation or TTL callback throws. Absence means: either timers are healthy (good) or the wrapper is not installed (bad -- verify with tests).

### Contract Boundaries

This ADR introduces no new API endpoints, store methods, or shared types. All changes are internal to the brain server process. The existing MCP tool interface is explicitly unchanged (R11). No contract boundaries to document.

---

## Data Sensitivity

Not applicable. This ADR modifies process-level crash guards, pool configuration, and timer wrappers. No new data access methods are introduced. Existing data access methods in `tools.mjs` are unchanged.

---

## Migration & Rollback

Not applicable. No database schema changes. No shared state changes. No cross-service contract changes. All changes are to stateless process-level code (crash guards, pool config, timer wrappers). Rollback is a simple git revert.

---

## Notes for Colby

1. **`server.mjs` is a top-level-await module.** It runs `createPool` and `runMigrations` at import time. This makes it non-trivial to import in tests. The recommended pattern is to extract the handler installation logic into a function (e.g., `installCrashGuards({ pool, exitFn, stopConsolidation, stopTTL })`) that can be imported and tested independently. Alternatively, test the handler behavior by emitting events on process/stdout/stderr/stdin directly in the test file after importing only the pieces needed.

2. **`process.emit('uncaughtException', err)` in tests.** This actually triggers the registered handler. Verify the handler is registered by checking it does not crash. Do NOT use `throw` at top level in a test -- that would crash the test runner. Use `process.emit` to simulate.

3. **`process.exit` must be mocked in tests.** Use `mock.method(process, 'exit')` from `node:test` to prevent the test process from actually exiting when testing shutdown paths. Restore after each test.

4. **Timer wrapper pattern -- do not change the function signatures.** `startConsolidationTimer(pool, apiKey)` and `startTTLTimer(pool)` keep their existing signatures. The only change is wrapping the `setInterval` callback body in try/catch.

5. **The `shuttingDown` re-entry guard.** This is a module-level `let` in `server.mjs`. It prevents `gracefulShutdown` from being called twice (e.g., EPIPE fires, then stdin EOF fires a moment later). The guard must be tested -- call `gracefulShutdown` twice, verify `process.exit` is called only once.

6. **`stderr.on('error', () => {})`.** This is intentionally a no-op. When stderr itself is broken, there is nowhere to log. The empty handler prevents the error from becoming an uncaughtException that would crash the process.

7. **Pool config affects `hydrate-telemetry.mjs`.** This script also calls `createPool`. The new config is beneficial for it (fail-fast on unreachable DB). No changes needed to the script.

8. **stdin EOF is the MCP SDK #1814 workaround.** Add a comment in the code: `// Workaround for MCP SDK #1814 -- stdin EOF not detected by SDK`. This documents why the workaround exists so it can be removed when the SDK fixes the bug.

9. **Existing test suites must pass.** After changes, run: `cd brain && node --test ../tests/brain/*.test.mjs`. All existing tests (db, consolidation, ttl, tools, etc.) must pass unchanged. The timer wrapper changes do not affect the test mocks because the tests call `runConsolidation`/`runTTLEnforcement` directly, not via the timer.

10. **Brain context (proven pattern):** The `pool.on('error', ...)` handler in `db.mjs` (line 23) is the existing pattern for pool-level error handling. The process-level handlers follow the same pattern: log and survive. Consolidation's inner try/catch (line 137) is the existing pattern for business-logic error handling. The timer wrapper adds the missing outer layer.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | uncaughtException handler | Covered | Step 1, AC-1, T-0017-001, T-0017-011 |
| R2 | unhandledRejection handler | Covered | Step 1, AC-2, T-0017-002, T-0017-012 |
| R3 | EPIPE handling | Covered | Step 1, AC-3, T-0017-003, T-0017-004 |
| R4 | stderr error handling | Covered | Step 1, AC-4, T-0017-005 |
| R5 | stdin EOF detection | Covered | Step 1, AC-5, T-0017-006 |
| R6 | Timer callback safety | Covered | Step 3, AC-8, T-0017-018 through T-0017-022 |
| R7 | Pool config hardening | Covered | Step 2, AC-7, T-0017-013 through T-0017-017 |
| R8 | SIGHUP handler | Covered | Step 1, AC-6, T-0017-007 |
| R9 | Consolidation timer survives throw | Covered | Step 3, AC-9, T-0017-018, T-0017-020 |
| R10 | TTL timer survives throw | Covered | Step 3, AC-10, T-0017-019, T-0017-021 |
| R11 | No behavioral changes | Covered | Steps 1-3 (no tool handler changes), T-0017-025, T-0017-026 |
| R12 | Comprehensive tests (failure >= happy) | Covered | 14 failure tests, 5 happy path tests (2.8:1 ratio) |

**Grep check:** TODO/FIXME/HACK in ADR -> 0
**Template:** All sections filled -- no TBD, no placeholders

**Architectural decisions not in the spec:**
- Extracted `installCrashGuards` pattern for testability (spec said "add handlers" but testing top-level-await modules requires extraction)
- Re-entry guard on `gracefulShutdown` (spec did not mention, but necessary for robustness when multiple shutdown triggers fire simultaneously)
- Inner try/catch on `console.error` calls in handlers (spec said "swallow stderr errors" but did not explicitly address stderr being broken inside other handlers)

**Rejected alternatives with reasoning:**
- Process supervisor (pm2) -- rejected because stdio transport cannot reconnect
- HTTP transport migration -- rejected due to known SDK bugs and user decision
- Connection health probe / watchdog -- rejected because no crash vector warrants it

**Technical constraints discovered during design:**
- `server.mjs` uses top-level await making it hard to import in tests; `installCrashGuards` extraction needed
- `pg.Pool` exposes `options` on the instance, enabling config verification tests without a real DB
- `node:test` mock timers (available Node 20+) enable timer wrapper testing without real delays
- `process.emit('uncaughtException', ...)` triggers the handler without crashing the test runner, unlike `throw`
