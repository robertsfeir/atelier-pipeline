/**
 * TTL enforcement -- expires thoughts past their type's configured TTL.
 * Depends on: db.mjs (pool), conflict.mjs (getBrainConfig).
 */

import { getBrainConfig } from "./conflict.mjs";

// =============================================================================
// TTL Enforcement
// =============================================================================

async function runTTLEnforcement(pool) {
  try {
    const result = await pool.query(`
      UPDATE thoughts t
      SET status = 'expired', invalidated_at = now()
      FROM thought_type_config ttc
      WHERE t.thought_type = ttc.thought_type
        AND ttc.default_ttl_days IS NOT NULL
        AND t.status = 'active'
        AND t.created_at < now() - (ttc.default_ttl_days || ' days')::interval
      RETURNING t.id
    `);
    if (result.rowCount > 0) {
      console.error(`TTL: Expired ${result.rowCount} thoughts`);
    }
  } catch (err) {
    console.error("TTL enforcement error:", err.message);
  }
}

// =============================================================================
// Timer
// =============================================================================

let ttlTimer = null;

async function startTTLTimer(pool) {
  // TTL runs less frequently than consolidation -- default 60 min
  const intervalMs = 60 * 60 * 1000;
  ttlTimer = setInterval(async () => {
    try {
      await runTTLEnforcement(pool);
    } catch (err) {
      try { console.error('TTL timer error (survived):', err.message); }
      catch { /* stderr may be broken */ }
    }
  }, intervalMs);
  // Run once on startup
  await runTTLEnforcement(pool);
}

function stopTTLTimer() {
  if (ttlTimer) {
    clearInterval(ttlTimer);
    ttlTimer = null;
  }
}

export { runTTLEnforcement, startTTLTimer, stopTTLTimer };
