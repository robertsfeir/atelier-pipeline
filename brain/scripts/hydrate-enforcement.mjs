#!/usr/bin/env node
/**
 * brain/scripts/hydrate-enforcement.mjs
 *
 * Reads today's enforcement audit log and captures blocked enforcement events
 * into the brain database as 'insight' thoughts with metadata.enforcement_event: true.
 *
 * Usage:
 *   node brain/scripts/hydrate-enforcement.mjs [--date YYYY-MM-DD] [--silent]
 *
 * ADR: docs/architecture/ADR-0031-permission-audit-trail.md
 *
 * Fail-open: exits 0 always. Never throws to caller.
 * No retry logic (Retro #004: hung process).
 */

import { readFileSync, existsSync } from "fs";
import { createHash } from "crypto";
import path from "path";
import { resolveConfig, buildProviderConfig } from "../lib/config.mjs";
import { createPool, runMigrations } from "../lib/db.mjs";
import { getEmbedding } from "../lib/embed.mjs";

// =============================================================================
// Helpers
// =============================================================================

function expandHome(p) {
  if (p && p.startsWith("~")) {
    return path.join(process.env.HOME || process.env.USERPROFILE || "", p.slice(1));
  }
  return p;
}

function todayUTC() {
  return new Date().toISOString().slice(0, 10);
}

// =============================================================================
// Duplicate Detection
// =============================================================================

async function alreadyCaptured(pool, contentHash) {
  const res = await pool.query(
    `SELECT 1 FROM thoughts
     WHERE source_phase = 'qa'
       AND metadata @> $1
     LIMIT 1`,
    [JSON.stringify({ enforcement_content_key: contentHash, enforcement_event: true })]
  );
  return res.rows.length > 0;
}

// =============================================================================
// Thought Insertion
// =============================================================================

async function insertEnforcementThought(pool, config, event) {
  const {
    timestamp, tool_name, agent_type, reason, hook_name, session_date,
  } = event;

  const content = `Enforcement: ${hook_name} blocked ${agent_type || "main-thread"} from ${tool_name}. Reason: ${reason}`;

  // Dedup key: hash of content to avoid re-inserting across session hydrations
  const contentHash = createHash("sha256").update(content).digest("hex").slice(0, 16);

  const isDuplicate = await alreadyCaptured(pool, contentHash);
  if (isDuplicate) return false;

  const metadata = {
    enforcement_event: true,
    hook_name,
    agent_type: agent_type || "",
    tool_name,
    decision: "blocked",
    reason,
    session_date,
    enforcement_content_key: contentHash,
    hydrated: true,
  };

  let embedding = null;
  const embedConfig = buildProviderConfig(config, "embed");
  const canEmbed = embedConfig.family === "local" || !!embedConfig.apiKey;
  if (canEmbed) {
    try {
      const vector = await getEmbedding(content, embedConfig);
      embedding = `[${vector.join(",")}]`;
    } catch {
      // Non-fatal: fall back to zero vector
    }
  }
  if (embedding === null) {
    embedding = `[${new Array(1536).fill(0).join(",")}]`;
  }

  const scopeVal = config.scope || "default";

  if (timestamp) {
    await pool.query(
      `INSERT INTO thoughts
         (content, embedding, metadata, thought_type, source_agent, source_phase,
          importance, scope, status, created_at)
       VALUES ($1, $2::vector, $3, 'insight', 'eva', 'qa', 0.4,
               ARRAY[$4::ltree], 'active', $5)`,
      [content, embedding, JSON.stringify(metadata), scopeVal, timestamp]
    );
  } else {
    await pool.query(
      `INSERT INTO thoughts
         (content, embedding, metadata, thought_type, source_agent, source_phase,
          importance, scope, status)
       VALUES ($1, $2::vector, $3, 'insight', 'eva', 'qa', 0.4,
               ARRAY[$4::ltree], 'active')`,
      [content, embedding, JSON.stringify(metadata), scopeVal]
    );
  }

  return true;
}

// =============================================================================
// Main
// =============================================================================

async function main() {
  const args = process.argv.slice(2);
  const silentMode = args.includes("--silent");
  const log = (...a) => { if (!silentMode) console.log(...a); };

  // Parse optional --date YYYY-MM-DD
  let targetDate = todayUTC();
  const dateIdx = args.indexOf("--date");
  if (dateIdx !== -1 && dateIdx + 1 < args.length) {
    targetDate = args[dateIdx + 1];
  }

  const logFile = expandHome(`~/.claude/logs/enforcement-${targetDate}.jsonl`);

  if (!existsSync(logFile)) {
    log(`No enforcement log found for ${targetDate} at ${logFile}. Skipping.`);
    return;
  }

  // Resolve brain config
  const config = resolveConfig();
  if (!config || !config.database_url) {
    log("No brain database configuration found. Skipping enforcement hydration.");
    return;
  }

  let pool;
  try {
    pool = createPool(config.database_url);
    await runMigrations(pool);
  } catch (err) {
    log(`Brain unavailable (${err.message}). Skipping enforcement hydration.`);
    return;
  }

  // Read and parse the enforcement log
  let lines;
  try {
    const raw = readFileSync(logFile, "utf-8");
    lines = raw.split("\n").filter((l) => l.trim().length > 0);
  } catch (err) {
    log(`Cannot read enforcement log: ${err.message}`);
    await pool.end().catch(() => {});
    return;
  }

  // Filter for blocked decisions only (ADR anti-goal #2: skip allowed events)
  const blockedEvents = [];
  for (const line of lines) {
    let event;
    try {
      event = JSON.parse(line);
    } catch {
      continue; // skip malformed lines
    }
    if (event.decision === "blocked") {
      blockedEvents.push({
        timestamp: event.timestamp || null,
        tool_name: event.tool_name || "",
        agent_type: event.agent_type || "",
        reason: event.reason || "",
        hook_name: event.hook_name || "",
        session_date: targetDate,
      });
    }
  }

  log(`Found ${blockedEvents.length} blocked enforcement event(s) in ${logFile}.`);

  let insertedCount = 0;
  let skippedCount = 0;

  for (const event of blockedEvents) {
    try {
      const inserted = await insertEnforcementThought(pool, config, event);
      if (inserted) {
        insertedCount++;
        log(`  Captured: ${event.hook_name} blocked ${event.agent_type || "main-thread"} from ${event.tool_name}`);
      } else {
        skippedCount++;
      }
    } catch (err) {
      // Non-fatal: log and continue (Retro #003, Retro #004)
      log(`  Failed to capture enforcement event: ${err.message}`);
    }
  }

  log(`Enforcement hydration complete: ${insertedCount} captured, ${skippedCount} skipped (already hydrated).`);

  await pool.end().catch(() => {});
}

main().catch((err) => {
  // Fail-open: log but never exit non-zero (ADR R7)
  console.error(`Enforcement hydration error (non-fatal): ${err.message}`);
});
