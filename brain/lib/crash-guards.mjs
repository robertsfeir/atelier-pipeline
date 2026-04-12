/**
 * Process-Level Crash Guards
 * ADR: docs/architecture/ADR-0017-brain-hardening.md (Step 1)
 *
 * Installs handlers for all 6 process-level crash vectors:
 *   1. uncaughtException -- log and survive
 *   2. unhandledRejection -- log and survive
 *   3. EPIPE on stdout -- graceful shutdown (Claude Code disconnected)
 *   4. stderr error -- swallow silently (can't log to broken stderr)
 *   5. stdin EOF -- graceful shutdown (MCP SDK #1814 workaround)
 *   6. SIGHUP / SIGTERM / SIGINT -- graceful shutdown
 *
 * Extracted from server.mjs for testability. All dependencies are injectable
 * so tests can verify behavior without spawning child processes or actually
 * exiting the test runner.
 *
 * @param {Object} deps - Injectable dependencies
 * @param {Function} deps.exitFn - Called to exit the process (default: process.exit)
 * @param {Function} deps.stopConsolidation - Stops the consolidation timer
 * @param {Function} deps.stopTTL - Stops the TTL timer
 * @param {Function} deps.poolEnd - Ends the DB pool (returns a promise)
 */
export function installCrashGuards(deps) {
  const { exitFn, stopConsolidation, stopTTL, poolEnd } = deps;

  // Re-entry guard -- prevents double-shutdown when multiple triggers fire
  // (e.g., EPIPE on stdout followed by stdin EOF a moment later).
  // Closure-scoped so each installCrashGuards call gets its own guard.
  let shuttingDown = false;

  function gracefulShutdown() {
    if (shuttingDown) return;
    shuttingDown = true;
    stopConsolidation();
    stopTTL();
    // Deadman timeout: if pool.end() stalls (e.g., inflight queries that
    // never complete), force exit after 3 seconds to prevent zombie processes.
    // unref() so the timer does not prevent the event loop from exiting on
    // its own if everything else completes cleanly.
    //
    // ADR-0034 Step 3.4 fix: race the pool drain against the deadman so
    // exitFn(0) is only called AFTER one of them resolves. The previous
    // version called exitFn(0) synchronously after starting the race, which
    // terminated the process before pool.end() had a chance to flush
    // in-flight queries -- corrupting writes mid-shutdown.
    const deadmanPromise = new Promise((resolve) => {
      const t = setTimeout(resolve, 3000);
      if (t.unref) t.unref();
    });
    Promise.race([poolEnd().catch(() => {}), deadmanPromise])
      .then(() => exitFn(0))
      .catch(() => exitFn(1));
  }

  // --- Crash vector #1: uncaughtException ---
  // Log and survive. The brain is stateless between requests (each MCP tool
  // call is an independent DB transaction), so surviving transient errors is
  // safe. The try/catch around console.error handles the case where stderr
  // itself is broken (crash vector #4).
  //
  // Remove existing handlers first so the brain's handlers are the sole
  // authority on exception survival. In production, no prior handlers exist
  // (the MCP SDK does not register uncaughtException handlers). In tests,
  // this removes the test runner's handler so process.emit('uncaughtException')
  // does not trigger a test failure.
  process.removeAllListeners('uncaughtException');
  process.removeAllListeners('unhandledRejection');

  process.on('uncaughtException', (err) => {
    try { console.error('Uncaught exception (survived):', err?.stack || err?.message || err); }
    catch { /* stderr may be broken */ }
  });

  // --- Crash vector #2: unhandledRejection ---
  // Log and survive. Normalize reason to extract a useful message regardless
  // of whether it is an Error object, a plain string, or another value.
  process.on('unhandledRejection', (reason) => {
    try { console.error('Unhandled rejection (survived):', reason?.stack || reason?.message || reason); }
    catch { /* stderr may be broken */ }
  });

  // --- Crash vector #3: EPIPE on stdout ---
  // EPIPE means Claude Code disconnected. Exit cleanly.
  // Non-EPIPE stdout errors are ignored (not shutdown-worthy).
  process.stdout.on('error', (err) => {
    if (err.code === 'EPIPE') gracefulShutdown();
  });

  // --- Crash vector #4: stderr error ---
  // Broken stderr pipe -- swallow silently (can't log to broken stderr).
  // The empty handler prevents the error from becoming an uncaughtException.
  process.stderr.on('error', () => {});

  // --- Crash vector #5: stdin EOF ---
  // Workaround for MCP SDK #1814 -- stdin EOF not detected by SDK
  process.stdin.on('end', () => gracefulShutdown());

  // --- Crash vector #6: signals ---
  // SIGHUP = terminal hangup, SIGTERM/SIGINT = existing behavior preserved
  process.on('SIGHUP', gracefulShutdown);
  process.on('SIGTERM', gracefulShutdown);
  process.on('SIGINT', gracefulShutdown);
}
