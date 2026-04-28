#!/usr/bin/env node
/**
 * brain/scripts/hydrate-telemetry.mjs
 *
 * Reads subagent JSONL files from Claude Code session directories and captures
 * Tier 1 telemetry thoughts into the brain database.
 *
 * Usage:
 *   node brain/scripts/hydrate-telemetry.mjs <project-sessions-path> [--state-dir PATH] [--silent]
 *
 * When --state-dir is provided, pipeline state files are read from that path.
 * When omitted, the script auto-resolves the out-of-repo state directory using
 * CLAUDE_PROJECT_DIR or CURSOR_PROJECT_DIR to compute
 * ~/.atelier/pipeline/{slug}/{hash}/ (ADR-0035 R1).
 *
 * Example:
 *   node brain/scripts/hydrate-telemetry.mjs ~/.claude/projects/-Users-sfeirr-projects-atelier-pipeline
 *
 * Core functions are re-exported from this module so brain/lib/hydrate.mjs can
 * share them with the atelier_hydrate MCP tool without duplicating logic.
 * Guard: main() only runs when this module is the entry point (not on import).
 */

import { readdirSync, readFileSync, statSync, existsSync } from "fs";
import { createHash } from "crypto";
import path from "path";
import os from "os";
import { fileURLToPath } from "url";
import { resolveConfig, buildProviderConfig } from "../lib/config.mjs";
import { createPool, runMigrations } from "../lib/db.mjs";
import { getEmbedding } from "../lib/embed.mjs";

// =============================================================================
// Scope Fallback Warning (fires once per module lifetime)
// =============================================================================

let scopeWarningEmitted = false;

function warnIfDefaultScope(scopeValue) {
  if (!scopeValue && !scopeWarningEmitted) {
    console.warn("Warning: config.scope is not set. Using 'default'. Run /brain-setup to configure a project scope.");
    scopeWarningEmitted = true;
  }
}

// =============================================================================
// Cost Estimation Table (per-1M tokens, USD)
// =============================================================================

const COST_TABLE = {
  // Opus variants
  "claude-opus":          { input: 15,   output: 75   },
  "claude-opus-4":        { input: 15,   output: 75   },
  "claude-opus-4-5":      { input: 15,   output: 75   },
  // Sonnet variants
  "claude-sonnet":        { input: 3,    output: 15   },
  "claude-sonnet-4":      { input: 3,    output: 15   },
  "claude-sonnet-4-5":    { input: 3,    output: 15   },
  "claude-sonnet-4-5-20251001": { input: 3, output: 15 },
  // Haiku variants
  "claude-haiku":         { input: 0.80, output: 4    },
  "claude-haiku-3-5":     { input: 0.80, output: 4    },
  "claude-haiku-4-5":     { input: 0.80, output: 4    },
  "claude-haiku-4-5-20251001": { input: 0.80, output: 4 },
};

// Cache read = 10% of input price; cache creation = 25% of input price
const CACHE_READ_FACTOR = 0.10;
const CACHE_CREATION_FACTOR = 0.25;

/**
 * Find the pricing row for a model string.
 * Tries exact match first, then prefix match on sorted keys (longest first).
 */
function lookupPricing(model) {
  if (!model || model === "unknown") return null;
  const normalized = model.toLowerCase();

  if (COST_TABLE[normalized]) return COST_TABLE[normalized];

  // Longest-prefix match so more-specific keys win
  const keys = Object.keys(COST_TABLE).sort((a, b) => b.length - a.length);
  for (const key of keys) {
    if (normalized.startsWith(key)) return COST_TABLE[key];
  }
  return null;
}

/**
 * Compute cost in USD given token counts and model.
 * Returns null when pricing is unavailable.
 */
function computeCost(model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens) {
  const pricing = lookupPricing(model);
  if (!pricing) return null;

  const inputCost         = (inputTokens         / 1_000_000) * pricing.input;
  const outputCost        = (outputTokens         / 1_000_000) * pricing.output;
  const cacheReadCost     = (cacheReadTokens      / 1_000_000) * pricing.input * CACHE_READ_FACTOR;
  const cacheCreationCost = (cacheCreationTokens  / 1_000_000) * pricing.input * CACHE_CREATION_FACTOR;

  return inputCost + outputCost + cacheReadCost + cacheCreationCost;
}

// =============================================================================
// JSONL Parsing
// =============================================================================

/**
 * Parse all lines of a JSONL file and return aggregated telemetry.
 */
function parseJsonl(filePath) {
  const raw = readFileSync(filePath, "utf-8");
  const lines = raw.split("\n").filter((l) => l.trim().length > 0);

  let model = "unknown";
  let inputTokens = 0;
  let outputTokens = 0;
  let cacheReadTokens = 0;
  let cacheCreationTokens = 0;
  let turnCount = 0;

  for (const line of lines) {
    let obj;
    try {
      obj = JSON.parse(line);
    } catch {
      continue; // skip malformed lines
    }

    const msg = obj.message;
    if (!msg) continue;

    // Capture model from first assistant message that has one
    if (model === "unknown" && msg.model) {
      model = msg.model;
    }

    // Sum usage fields
    const usage = msg.usage;
    if (usage) {
      inputTokens         += usage.input_tokens                 ?? 0;
      outputTokens        += usage.output_tokens                ?? 0;
      cacheReadTokens     += usage.cache_read_input_tokens      ?? 0;
      cacheCreationTokens += usage.cache_creation_input_tokens  ?? 0;
      turnCount++;
    }
  }

  return { model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens, turnCount };
}

// =============================================================================
// Session Directory Walking
// =============================================================================

/**
 * Expand ~ in paths.
 */
function expandHome(p) {
  if (p.startsWith("~")) {
    return path.join(process.env.HOME || process.env.USERPROFILE || "", p.slice(1));
  }
  return p;
}

/**
 * Resolve the out-of-repo Atelier state directory for a given worktree root.
 * Returns ~/.atelier/pipeline/{slug}/{hash} if it exists on disk, else null.
 *
 * This mirrors the bash helper pipeline-state-path.sh session_state_dir().
 * Cross-implementation contract test T-0035-012 verifies hash parity.
 *
 * @param {string} worktreeRoot - Absolute path to the project worktree root.
 * @returns {string|null} Absolute path to the state directory, or null.
 */
function resolveAtelierStateDir(worktreeRoot) {
  const slug = path.basename(worktreeRoot);
  const hash = createHash("sha256").update(worktreeRoot).digest("hex").slice(0, 8);
  const stateDir = path.join(os.homedir(), ".atelier", "pipeline", slug, hash);
  if (existsSync(stateDir)) {
    return stateDir;
  }
  return null;
}

/**
 * Returns array of { sessionId, agentId, jsonlPath } for the parent (Eva)
 * JSONL file for each session.
 * The parent session file lives at: {projectPath}/{sessionId}.jsonl
 * (a sibling of the session directory, at the project root level).
 */
function discoverEvaFiles(projectPath) {
  const results = [];

  let entries;
  try {
    entries = readdirSync(projectPath);
  } catch (err) {
    console.error(`Cannot read project path: ${projectPath} (${err.message})`);
    return results;
  }

  for (const entry of entries) {
    if (!entry.endsWith(".jsonl")) continue;
    const sessionId = entry.replace(".jsonl", "");
    const jsonlPath = path.join(projectPath, entry);
    // Confirm the corresponding session directory also exists (sanity check)
    const sessionDir = path.join(projectPath, sessionId);
    if (!existsSync(sessionDir)) continue;

    results.push({ sessionId, agentId: `eva-${sessionId}`, jsonlPath });
  }

  return results;
}

/**
 * Returns array of { sessionId, agentId, jsonlPath, metaPath } for all subagent
 * JSONL files found under the given project sessions root.
 */
function discoverSubagentFiles(projectPath) {
  const results = [];

  let entries;
  try {
    entries = readdirSync(projectPath);
  } catch (err) {
    console.error(`Cannot read project path: ${projectPath} (${err.message})`);
    return results;
  }

  for (const entry of entries) {
    const sessionDir = path.join(projectPath, entry);
    let stat;
    try {
      stat = statSync(sessionDir);
    } catch {
      continue;
    }
    if (!stat.isDirectory()) continue;

    const subagentsDir = path.join(sessionDir, "subagents");
    if (!existsSync(subagentsDir)) continue;

    let subentries;
    try {
      subentries = readdirSync(subagentsDir);
    } catch {
      continue;
    }

    for (const subentry of subentries) {
      if (!subentry.endsWith(".jsonl")) continue;
      const agentId = subentry.replace(".jsonl", "");
      const jsonlPath = path.join(subagentsDir, subentry);
      const metaPath  = path.join(subagentsDir, `${agentId}.meta.json`);
      results.push({ sessionId: entry, agentId, jsonlPath, metaPath });
    }
  }

  return results;
}

// =============================================================================
// Duplicate Detection
// =============================================================================

/**
 * Check if a telemetry thought for this (sessionId, agentId) already exists.
 */
async function alreadyHydrated(pool, sessionId, agentId) {
  const res = await pool.query(
    `SELECT 1 FROM thoughts
     WHERE source_phase = 'telemetry'
       AND metadata @> $1
     LIMIT 1`,
    [JSON.stringify({ session_id: sessionId, agent_id: agentId, hydrated: true })]
  );
  return res.rows.length > 0;
}

// =============================================================================
// Thought Insertion
// =============================================================================

/**
 * Insert a single telemetry thought into the brain database.
 * Uses a real embedding when possible; falls back to zero vector.
 * Pass createdAt (ISO string) to override the DB default of now().
 *
 * Optional overrides (with backward-compatible defaults):
 *   thought_type  — defaults to 'insight'
 *   source_agent  — defaults to 'eva'
 *   source_phase  — defaults to 'telemetry'
 *   importance    — defaults to 0.3
 */
async function insertTelemetryThought(pool, config, {
  content, metadata, scope, createdAt,
  thought_type = "insight",
  source_agent = "eva",
  source_phase = "telemetry",
  importance = 0.3,
}) {
  let embedding = null;
  const embedConfig = buildProviderConfig(config, "embed");
  const canEmbed = embedConfig.family === "local" || !!embedConfig.apiKey;

  if (canEmbed) {
    try {
      const vector = await getEmbedding(content, embedConfig);
      // pgvector expects the array as a string like '[0.1,0.2,...]'
      embedding = `[${vector.join(",")}]`;
    } catch (err) {
      // Non-fatal: fall back to zero vector
      console.warn(`  Embedding generation failed (${err.message}); using zero vector.`);
    }
  }

  if (embedding === null) {
    // Zero vector fallback — still searchable via metadata filters
    embedding = `[${new Array(1536).fill(0).join(",")}]`;
  }

  const scopeVal = scope || config.scope || "default";
  warnIfDefaultScope(scope || config.scope);

  if (createdAt) {
    await pool.query(
      `INSERT INTO thoughts
         (content, embedding, metadata, thought_type, source_agent, source_phase,
          importance, scope, status, created_at)
       VALUES ($1, $2::vector, $3, $5, $6, $7, $8,
               ARRAY[$4::ltree], 'active', $9)`,
      [content, embedding, JSON.stringify(metadata), scopeVal,
       thought_type, source_agent, source_phase, importance, createdAt]
    );
  } else {
    await pool.query(
      `INSERT INTO thoughts
         (content, embedding, metadata, thought_type, source_agent, source_phase,
          importance, scope, status)
       VALUES ($1, $2::vector, $3, $5, $6, $7, $8,
               ARRAY[$4::ltree], 'active')`,
      [content, embedding, JSON.stringify(metadata), scopeVal,
       thought_type, source_agent, source_phase, importance]
    );
  }
}

// =============================================================================
// State-File Duplicate Detection
// =============================================================================

/**
 * Check if a state-file capture with the given content hash already exists.
 * Uses source_phase='pipeline' and a composite key in metadata to avoid
 * re-inserting the same state-file item across sessions.
 */
async function stateItemAlreadyHydrated(pool, contentHash) {
  const res = await pool.query(
    `SELECT 1 FROM thoughts
     WHERE source_phase = 'pipeline'
       AND metadata @> $1
     LIMIT 1`,
    [JSON.stringify({ state_capture_key: contentHash, hydrated: true })]
  );
  return res.rows.length > 0;
}

// =============================================================================
// State-File Parsing (pipeline-state.md + context-brief.md)
// =============================================================================

/**
 * Parse pipeline state files from the given directory and insert brain captures
 * for Eva's pipeline decisions and phase transitions.
 *
 * Reads:
 *   {stateDir}/pipeline-state.md  — extracts Feature, Sizing, completed progress items
 *   {stateDir}/context-brief.md   — extracts items under ## User Decisions
 *
 * Each item becomes one thought with:
 *   thought_type: 'decision', source_agent: 'eva', source_phase: 'pipeline', importance: 0.6
 *
 * All file reads are guarded by existsSync. All errors are caught and logged.
 * This function never throws (Retro #002, Retro #003).
 */
async function parseStateFiles(stateDir, pool, config, { silentMode = false } = {}) {
  const log = (...a) => { if (!silentMode) console.log(...a); };

  // Early-exit guard: gracefully skip when stateDir does not exist (ADR-0035 R2)
  if (!existsSync(stateDir)) {
    log(`  State dir not found: ${stateDir} (graceful skip)`);
    return 0;
  }

  let inserted = 0;

  // ── pipeline-state.md ──────────────────────────────────────────────────
  const pipelineStatePath = path.join(stateDir, "pipeline-state.md");

  try {
    if (existsSync(pipelineStatePath)) {
      const raw = readFileSync(pipelineStatePath, "utf-8");
      const lines = raw.split("\n");

      // Extract **Feature:** and **Sizing:** values
      let feature = "unknown";
      let sizing = "unknown";
      for (const line of lines) {
        const featureMatch = line.match(/\*\*Feature:\*\*\s*(.+)/);
        if (featureMatch) feature = featureMatch[1].trim();
        const sizingMatch = line.match(/\*\*Sizing:\*\*\s*(.+)/);
        if (sizingMatch) sizing = sizingMatch[1].trim();
      }

      // Extract completed progress items (- [x] lines)
      for (const line of lines) {
        const checkboxMatch = line.match(/^-\s*\[x\]\s*(.+)/i);
        if (!checkboxMatch) continue;

        const phase_item = checkboxMatch[1].trim();
        const contentHash = createHash("sha256").update(feature + ":" + phase_item).digest("hex").slice(0, 16);
        const state_capture_key = `state_phase_${contentHash}`;

        // Duplicate detection
        const isDuplicate = await stateItemAlreadyHydrated(pool, state_capture_key);
        if (isDuplicate) continue;

        const content = `Pipeline phase complete: ${phase_item}`;
        const metadata = {
          feature,
          sizing,
          phase_item,
          state_capture_key,
          hydrated: true,
        };

        log(`  State capture: ${content}`);

        await insertTelemetryThought(pool, config, {
          content,
          metadata,
          scope: config.scope || "default",
          thought_type: "decision",
          source_agent: "eva",
          source_phase: "pipeline",
          importance: 0.6,
        });
        inserted++;
      }
    }
  } catch (err) {
    // Non-fatal: log and continue (Retro #002, Retro #003)
    console.error(`  State-file parse error (pipeline-state.md): ${err.message}`);
  }

  // ── context-brief.md ───────────────────────────────────────────────────
  const contextBriefPath = path.join(stateDir, "context-brief.md");

  try {
    if (existsSync(contextBriefPath)) {
      const raw = readFileSync(contextBriefPath, "utf-8");
      const lines = raw.split("\n");

      // Extract items under ## User Decisions section
      let inUserDecisions = false;
      for (const line of lines) {
        // Start capturing at ## User Decisions header
        if (/^##\s+User Decisions/i.test(line)) {
          inUserDecisions = true;
          continue;
        }
        // Stop at the next ## header
        if (inUserDecisions && /^##\s/.test(line)) {
          break;
        }
        // Capture decision items (lines starting with - )
        if (inUserDecisions && /^\s*-\s+/.test(line)) {
          const decisionText = line.replace(/^\s*-\s+/, "").trim();
          if (!decisionText) continue;

          const contentHash = createHash("sha256").update("decision:" + decisionText).digest("hex").slice(0, 16);
          const state_capture_key = `state_decision_${contentHash}`;

          // Duplicate detection
          const isDuplicate = await stateItemAlreadyHydrated(pool, state_capture_key);
          if (isDuplicate) continue;

          const content = decisionText;
          const metadata = {
            section: "user_decisions",
            state_capture_key,
            hydrated: true,
          };

          log(`  User decision capture: ${content}`);

          await insertTelemetryThought(pool, config, {
            content,
            metadata,
            scope: config.scope || "default",
            thought_type: "decision",
            source_agent: "eva",
            source_phase: "pipeline",
            importance: 0.6,
          });
          inserted++;
        }
      }
    }
  } catch (err) {
    // Non-fatal: log and continue (Retro #002, Retro #003)
    console.error(`  State-file parse error (context-brief.md): ${err.message}`);
  }

  return inserted;
}

// =============================================================================
// Tier 3 Summary Generation
// =============================================================================

/**
 * For each unique session_id in Tier 1, produce one Tier 3 summary thought
 * unless one already exists for that session.
 * Returns the count of newly inserted Tier 3 rows.
 */
async function generateTier3Summaries(pool, config) {
  // Find all sessions that have Tier 1 data but no Tier 3 summary yet.
  const sessionsRes = await pool.query(
    `SELECT DISTINCT metadata->>'session_id' AS session_id
     FROM thoughts
     WHERE source_phase = 'telemetry'
       AND metadata->>'telemetry_tier' = '1'
       AND metadata->>'session_id' IS NOT NULL
       AND metadata->>'session_id' NOT IN (
         SELECT metadata->>'session_id'
         FROM thoughts
         WHERE source_phase = 'telemetry'
           AND metadata->>'telemetry_tier' = '3'
           AND metadata->>'session_id' IS NOT NULL
       )`
  );

  const sessionIds = sessionsRes.rows.map((r) => r.session_id);
  if (sessionIds.length === 0) return 0;

  let inserted = 0;

  for (const sessionId of sessionIds) {
    // Aggregate all Tier 1 rows for this session.
    const aggRes = await pool.query(
      `SELECT
         count(*)::int                                  AS total_invocations,
         sum((metadata->>'cost_usd')::numeric)          AS total_cost_usd,
         sum((metadata->>'duration_ms')::numeric)       AS total_duration_ms,
         min(created_at)                                AS earliest_at,
         array_agg(metadata->>'agent_name')             AS agent_names
       FROM thoughts
       WHERE source_phase = 'telemetry'
         AND metadata->>'telemetry_tier' = '1'
         AND metadata->>'session_id' = $1`,
      [sessionId]
    );

    const row = aggRes.rows[0];
    if (!row || !row.total_invocations) continue;

    // Build invocations_by_agent map
    const invocationsByAgent = {};
    for (const name of (row.agent_names || [])) {
      if (!name) continue;
      invocationsByAgent[name] = (invocationsByAgent[name] || 0) + 1;
    }

    const totalCost    = row.total_cost_usd    ? parseFloat(row.total_cost_usd).toFixed(4)    : "0.0000";
    const totalDurMs   = row.total_duration_ms ? parseFloat(row.total_duration_ms).toFixed(0) : "0";
    const invocations  = row.total_invocations;
    const earliestAt   = row.earliest_at;

    const content = `Telemetry T3: Pipeline summary — ${invocations} invocations, $${totalCost} total cost`;

    const metadata = {
      telemetry_tier: "3",
      session_id: sessionId,
      total_cost_usd: parseFloat(totalCost),
      total_duration_ms: parseFloat(totalDurMs),
      total_invocations: invocations,
      invocations_by_agent: invocationsByAgent,
      sizing: "unknown",
      hydrated: true,
    };

    // Reuse embedding strategy from insertTelemetryThought
    let embedding = null;
    const t3EmbedConfig = buildProviderConfig(config, "embed");
    const t3CanEmbed = t3EmbedConfig.family === "local" || !!t3EmbedConfig.apiKey;
    if (t3CanEmbed) {
      try {
        const vector = await getEmbedding(content, t3EmbedConfig);
        embedding = `[${vector.join(",")}]`;
      } catch (err) {
        // Non-fatal
      }
    }
    if (embedding === null) {
      embedding = `[${new Array(1536).fill(0).join(",")}]`;
    }

    const scopeVal = config.scope || "default";
    warnIfDefaultScope(config.scope);

    await pool.query(
      `INSERT INTO thoughts
         (content, embedding, metadata, thought_type, source_agent, source_phase,
          importance, scope, status, created_at)
       VALUES ($1, $2::vector, $3, 'insight', 'eva', 'telemetry', 0.7,
               ARRAY[$4::ltree], 'active', $5)`,
      [content, embedding, JSON.stringify(metadata), scopeVal, earliestAt]
    );

    inserted++;
  }

  return inserted;
}

// =============================================================================
// Per-File Hydration Helpers (shared with atelier_hydrate MCP tool via hydrate.mjs)
// =============================================================================

/**
 * Hydrate a single subagent JSONL file into the brain database.
 * Returns true if inserted, false if skipped (duplicate or error).
 */
async function hydrateSubagentFile(pool, config, { sessionId, agentId, jsonlPath, metaPath }) {
  const duplicate = await alreadyHydrated(pool, sessionId, agentId);
  if (duplicate) return false;

  let agentType = "unknown";
  let description = "";
  if (metaPath && existsSync(metaPath)) {
    try {
      const meta = JSON.parse(readFileSync(metaPath, "utf-8"));
      agentType   = meta.agentType   || "unknown";
      description = meta.description || "";
    } catch {
      // non-fatal
    }
  }

  let durationMs = 0;
  let fileCreatedAt = null;
  try {
    const jsonlStat = statSync(jsonlPath);
    const birthtimeMs = jsonlStat.birthtimeMs || jsonlStat.ctimeMs;
    const modifiedAt  = jsonlStat.mtimeMs;
    durationMs    = Math.max(0, modifiedAt - birthtimeMs);
    fileCreatedAt = new Date(birthtimeMs).toISOString();
  } catch {
    // leave 0 / null
  }

  const { model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens, turnCount } =
    parseJsonl(jsonlPath);

  const totalAgentTokens = inputTokens + outputTokens + cacheReadTokens + cacheCreationTokens;
  const cost = computeCost(model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens);

  const costStr = cost !== null ? `$${cost.toFixed(6)}` : "cost unknown";
  const descStr = description ? ` (${description})` : "";
  const content = `Telemetry T1: ${agentType}${descStr} — ${model}, ${totalAgentTokens} tokens, ${costStr}`;

  const metadata = {
    telemetry_tier: 1,
    agent_id: agentId,
    agent_name: agentType,
    agent_type: agentType,
    description,
    model,
    input_tokens: inputTokens,
    output_tokens: outputTokens,
    cache_read_tokens: cacheReadTokens,
    cache_creation_tokens: cacheCreationTokens,
    total_tokens: totalAgentTokens,
    duration_ms: durationMs,
    cost_usd: cost,
    turn_count: turnCount,
    session_id: sessionId,
    hydrated: true,
  };

  warnIfDefaultScope(config.scope);

  try {
    await insertTelemetryThought(pool, config, {
      content,
      metadata,
      scope: config.scope || "default",
      createdAt: fileCreatedAt,
    });
    return true;
  } catch (err) {
    console.error(`  Failed to insert ${agentId}: ${err.message}`);
    return false;
  }
}

/**
 * Hydrate a single Eva (parent session) JSONL file into the brain database.
 * Returns true if inserted, false if skipped (duplicate or error).
 */
async function hydrateEvaFile(pool, config, { sessionId, agentId, jsonlPath }) {
  const duplicate = await alreadyHydrated(pool, sessionId, agentId);
  if (duplicate) return false;

  let durationMs = 0;
  let fileCreatedAt = null;
  try {
    const jsonlStat = statSync(jsonlPath);
    const birthtimeMs = jsonlStat.birthtimeMs || jsonlStat.ctimeMs;
    const modifiedAt  = jsonlStat.mtimeMs;
    durationMs    = Math.max(0, modifiedAt - birthtimeMs);
    fileCreatedAt = new Date(birthtimeMs).toISOString();
  } catch {
    // leave 0 / null
  }

  const { model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens, turnCount } =
    parseJsonl(jsonlPath);

  const totalAgentTokens = inputTokens + outputTokens + cacheReadTokens + cacheCreationTokens;
  const cost = computeCost(model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens);

  const costStr = cost !== null ? `$${cost.toFixed(6)}` : "cost unknown";
  const description = "Eva (orchestrator) — main thread";
  const content = `Telemetry T1: eva (${description}) — ${model}, ${totalAgentTokens} tokens, ${costStr}`;

  const metadata = {
    telemetry_tier: 1,
    agent_id: agentId,
    agent_name: "eva",
    agent_type: "eva",
    description,
    model,
    input_tokens: inputTokens,
    output_tokens: outputTokens,
    cache_read_tokens: cacheReadTokens,
    cache_creation_tokens: cacheCreationTokens,
    total_tokens: totalAgentTokens,
    duration_ms: durationMs,
    cost_usd: cost,
    turn_count: turnCount,
    session_id: sessionId,
    hydrated: true,
  };

  warnIfDefaultScope(config.scope);

  try {
    await insertTelemetryThought(pool, config, {
      content,
      metadata,
      scope: config.scope || "default",
      createdAt: fileCreatedAt,
    });
    return true;
  } catch (err) {
    console.error(`  Failed to insert Eva ${agentId}: ${err.message}`);
    return false;
  }
}

// =============================================================================
// Main
// =============================================================================

async function main() {
  const args = process.argv.slice(2);
  const silentMode = args.includes("--silent");

  // Parse --state-dir <path> argument
  let stateDirArg = null;
  const stateDirIdx = args.indexOf("--state-dir");
  if (stateDirIdx !== -1 && stateDirIdx + 1 < args.length) {
    stateDirArg = args[stateDirIdx + 1];
  }

  const projectPathArg = args.find((a) => !a.startsWith("--") && a !== stateDirArg);

  if (!projectPathArg) {
    console.error("Usage: node brain/scripts/hydrate-telemetry.mjs <project-sessions-path> [--silent]");
    console.error("Example: node brain/scripts/hydrate-telemetry.mjs ~/.claude/projects/-Users-sfeirr-projects-atelier-pipeline");
    process.exit(1);
  }

  const projectPath = expandHome(projectPathArg);

  // Helper: only print when not in silent mode
  const log = (...a) => { if (!silentMode) console.log(...a); };

  // Resolve config
  const config = resolveConfig();
  if (!config || !config.database_url) {
    console.error("No database configuration found. Set BRAIN_CONFIG_PROJECT, BRAIN_CONFIG_USER, or DATABASE_URL.");
    process.exit(1);
  }

  const pool = createPool(config.database_url);
  await runMigrations(pool);

  // Discover all subagent JSONL files
  const files = discoverSubagentFiles(projectPath);
  log(`Found ${files.length} subagent JSONL files across sessions in: ${projectPath}`);

  // Discover Eva (parent session) JSONL files
  const evaFiles = discoverEvaFiles(projectPath);
  log(`Found ${evaFiles.length} Eva (parent session) JSONL files.`);

  let hydratedCount = 0;
  let skippedCount = 0;
  let sessionSet = new Set();
  let totalTokens = 0;
  let totalCost = 0;
  let costAvailable = true;

  for (const { sessionId, agentId, jsonlPath, metaPath } of files) {
    // Duplicate check
    const duplicate = await alreadyHydrated(pool, sessionId, agentId);
    if (duplicate) {
      skippedCount++;
      continue;
    }

    // Read meta.json for agent type and description
    let agentType = "unknown";
    let description = "";
    if (existsSync(metaPath)) {
      try {
        const meta = JSON.parse(readFileSync(metaPath, "utf-8"));
        agentType   = meta.agentType   || "unknown";
        description = meta.description || "";
      } catch {
        // non-fatal — leave defaults
      }
    }

    // Get file timestamps for duration and created_at
    let durationMs = 0;
    let fileCreatedAt = null;
    try {
      const jsonlStat = statSync(jsonlPath);
      // birthtime = when the file was created; fallback to ctime
      const birthtimeMs = jsonlStat.birthtimeMs || jsonlStat.ctimeMs;
      const modifiedAt  = jsonlStat.mtimeMs;
      durationMs    = Math.max(0, modifiedAt - birthtimeMs);
      fileCreatedAt = new Date(birthtimeMs).toISOString();
    } catch {
      // leave 0 / null
    }

    // Parse JSONL
    const { model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens, turnCount } =
      parseJsonl(jsonlPath);

    const totalAgentTokens = inputTokens + outputTokens + cacheReadTokens + cacheCreationTokens;
    const cost = computeCost(model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens);

    // Accumulate summary stats
    sessionSet.add(sessionId);
    totalTokens += totalAgentTokens;
    if (cost !== null) {
      totalCost += cost;
    } else {
      costAvailable = false;
    }

    // Build content string
    const costStr = cost !== null ? `$${cost.toFixed(6)}` : "cost unknown";
    const descStr = description ? ` (${description})` : "";
    const content = `Telemetry T1: ${agentType}${descStr} — ${model}, ${totalAgentTokens} tokens, ${costStr}`;

    // Build metadata
    const metadata = {
      telemetry_tier: 1,
      agent_id: agentId,
      agent_name: agentType,
      agent_type: agentType,
      description,
      model,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      cache_read_tokens: cacheReadTokens,
      cache_creation_tokens: cacheCreationTokens,
      total_tokens: totalAgentTokens,
      duration_ms: durationMs,
      cost_usd: cost,
      turn_count: turnCount,
      session_id: sessionId,
      hydrated: true,
    };

    log(`  Inserting: ${agentId} (${sessionId.slice(0, 8)}…) — ${agentType}, ${model}, ${totalAgentTokens} tokens, ${costStr}`);
    warnIfDefaultScope(config.scope);

    try {
      await insertTelemetryThought(pool, config, {
        content,
        metadata,
        scope: config.scope || "default",
        createdAt: fileCreatedAt,
      });
      hydratedCount++;
    } catch (err) {
      console.error(`  Failed to insert ${agentId}: ${err.message}`);
    }
  }

  // Process Eva (parent session) files
  for (const { sessionId, agentId, jsonlPath } of evaFiles) {
    const duplicate = await alreadyHydrated(pool, sessionId, agentId);
    if (duplicate) {
      skippedCount++;
      continue;
    }

    let durationMs = 0;
    let fileCreatedAt = null;
    try {
      const jsonlStat = statSync(jsonlPath);
      const birthtimeMs = jsonlStat.birthtimeMs || jsonlStat.ctimeMs;
      const modifiedAt  = jsonlStat.mtimeMs;
      durationMs    = Math.max(0, modifiedAt - birthtimeMs);
      fileCreatedAt = new Date(birthtimeMs).toISOString();
    } catch {
      // leave 0 / null
    }

    const { model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens, turnCount } =
      parseJsonl(jsonlPath);

    const totalAgentTokens = inputTokens + outputTokens + cacheReadTokens + cacheCreationTokens;
    const cost = computeCost(model, inputTokens, outputTokens, cacheReadTokens, cacheCreationTokens);

    sessionSet.add(sessionId);
    totalTokens += totalAgentTokens;
    if (cost !== null) {
      totalCost += cost;
    } else {
      costAvailable = false;
    }

    const costStr = cost !== null ? `$${cost.toFixed(6)}` : "cost unknown";
    const description = "Eva (orchestrator) — main thread";
    const content = `Telemetry T1: eva (${description}) — ${model}, ${totalAgentTokens} tokens, ${costStr}`;

    const metadata = {
      telemetry_tier: 1,
      agent_id: agentId,
      agent_name: "eva",
      agent_type: "eva",
      description,
      model,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      cache_read_tokens: cacheReadTokens,
      cache_creation_tokens: cacheCreationTokens,
      total_tokens: totalAgentTokens,
      duration_ms: durationMs,
      cost_usd: cost,
      turn_count: turnCount,
      session_id: sessionId,
      hydrated: true,
    };

    log(`  Inserting Eva: ${agentId} (${sessionId.slice(0, 8)}…) — eva, ${model}, ${totalAgentTokens} tokens, ${costStr}`);
    warnIfDefaultScope(config.scope);

    try {
      await insertTelemetryThought(pool, config, {
        content,
        metadata,
        scope: config.scope || "default",
        createdAt: fileCreatedAt,
      });
      hydratedCount++;
    } catch (err) {
      console.error(`  Failed to insert Eva ${agentId}: ${err.message}`);
    }
  }

  // Summary
  const sessionCount = sessionSet.size;
  const costSummary = costAvailable
    ? `$${totalCost.toFixed(4)}`
    : `$${totalCost.toFixed(4)} (partial — some models unpriced)`;

  // The final summary line always prints (visible even in --silent mode)
  console.log(`Hydrated ${hydratedCount} agents across ${sessionCount} sessions. Total: ${totalTokens} tokens, ${costSummary}.`);
  if (!silentMode && skippedCount > 0) {
    console.log(`Skipped ${skippedCount} already-hydrated agents.`);
  }

  // ==========================================================================
  // Tier 3 — Session-Level Summary Aggregation
  // ==========================================================================
  // Generate one Tier 3 thought per session from the Tier 1 data already in
  // the database. Skip sessions that already have a Tier 3 entry.

  log("\nGenerating Tier 3 session summaries...");

  const t3Inserted = await generateTier3Summaries(pool, config);
  log(`Tier 3 summaries: ${t3Inserted} new session(s) summarized.`);

  // ==========================================================================
  // State-File Parsing (pipeline-state.md + context-brief.md)
  // ==========================================================================
  // When --state-dir is provided, parse pipeline state files and emit captures
  // for Eva's decisions and phase transitions. When absent, auto-resolve the
  // out-of-repo state directory via CLAUDE_PROJECT_DIR / CURSOR_PROJECT_DIR
  // (ADR-0035 R1).

  if (stateDirArg) {
    log("\nParsing pipeline state files...");
    const stateInserted = await parseStateFiles(expandHome(stateDirArg), pool, config, { silentMode });
    log(`State-file captures: ${stateInserted} new item(s) captured.`);
  } else {
    const worktreeRoot = process.env.CLAUDE_PROJECT_DIR || process.env.CURSOR_PROJECT_DIR;
    if (worktreeRoot) {
      const autoStateDir = resolveAtelierStateDir(worktreeRoot);
      if (autoStateDir) {
        log("\nAuto-resolved state dir: " + autoStateDir);
        const stateInserted = await parseStateFiles(autoStateDir, pool, config, { silentMode });
        log(`State-file captures: ${stateInserted} new item(s) captured.`);
      }
    }
  }

  await pool.end();
}

// =============================================================================
// Exports (shared with atelier_hydrate MCP tool via brain/lib/hydrate.mjs)
// =============================================================================

export {
  expandHome,
  resolveAtelierStateDir,
  discoverEvaFiles,
  discoverSubagentFiles,
  alreadyHydrated,
  hydrateSubagentFile,
  hydrateEvaFile,
  insertTelemetryThought,
  generateTier3Summaries,
  parseStateFiles,
  parseJsonl,
  computeCost,
  lookupPricing,
  warnIfDefaultScope,
  stateItemAlreadyHydrated,
};

// Guard: only run main() when this is the entry point, not when imported as a module.
// This allows brain/lib/hydrate.mjs to re-export these functions without triggering
// the CLI main() path (which would call process.exit on missing args).
const isEntryPoint = process.argv[1] &&
  (process.argv[1] === fileURLToPath(import.meta.url) ||
   process.argv[1].endsWith("hydrate-telemetry.mjs"));

if (isEntryPoint) {
  main().catch((err) => {
    console.error("Fatal:", err.message);
    process.exit(1);
  });
}
