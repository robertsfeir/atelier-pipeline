/**
 * Atelier Brain — MCP Server
 * Persistent institutional memory for atelier-pipeline agents.
 *
 * Forked from mybrain/server.mjs. Extended with:
 * - Schema-enforced captures (required enums for thought_type, source_agent, source_phase)
 * - Three-axis scoring (recency + importance + relevance)
 * - Write-time conflict detection (duplicate/candidate/novel)
 * - Typed relations with supersedes auto-invalidation
 * - Recursive chain traversal
 * - REST API for Settings UI (Phase 2 — Steps 4-6)
 *
 * ADR: docs/architecture/ADR-0001-atelier-brain.md (Steps 3, 4, 5, 6)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import pg from "pg";
import pgvector from "pgvector/pg";
import { createServer } from "http";
import crypto from "crypto";
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import path from "path";

// =============================================================================
// Configuration
// =============================================================================

const EMBEDDING_MODEL = "openai/text-embedding-3-small";

// Enums matching schema.sql — used for Zod validation
const THOUGHT_TYPES = ["decision", "preference", "lesson", "rejection", "drift", "correction", "insight", "reflection"];
const SOURCE_AGENTS = ["eva", "cal", "robert", "sable", "colby", "roz", "poirot", "agatha", "distillator", "ellis"];
const SOURCE_PHASES = ["design", "build", "qa", "review", "reconciliation", "setup"];
const THOUGHT_STATUSES = ["active", "superseded", "invalidated", "expired", "conflicted"];
const RELATION_TYPES = ["supersedes", "triggered_by", "evolves_from", "contradicts", "supports", "synthesized_from"];

// =============================================================================
// Config Resolution (Step 11 logic — project > user > env > none)
// =============================================================================

function resolveConfig() {
  const projectPath = process.env.BRAIN_CONFIG_PROJECT;
  const userPath = process.env.BRAIN_CONFIG_USER;

  for (const configPath of [projectPath, userPath]) {
    if (!configPath) continue;
    try {
      const raw = readFileSync(configPath, "utf-8");
      const config = JSON.parse(raw);
      // Resolve ${ENV_VAR} placeholders
      const resolved = {};
      for (const [key, value] of Object.entries(config)) {
        if (typeof value === "string" && value.startsWith("${") && value.endsWith("}")) {
          const envKey = value.slice(2, -1);
          const envVal = process.env[envKey];
          if (!envVal) {
            console.error(`Missing env var ${envKey} referenced in config`);
            return null;
          }
          resolved[key] = envVal;
        } else {
          resolved[key] = value;
        }
      }
      resolved._source = configPath === projectPath ? "project" : "personal";
      return resolved;
    } catch {
      // File doesn't exist or is malformed — try next
      continue;
    }
  }

  // Fallback to env vars
  const dbUrl = process.env.DATABASE_URL || process.env.ATELIER_BRAIN_DATABASE_URL;
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (dbUrl) {
    return { database_url: dbUrl, openrouter_api_key: apiKey, _source: "env" };
  }

  return null;
}

const config = resolveConfig();
if (!config) {
  // No config = no brain. Exit cleanly per ADR Step 11.
  console.log("No brain config found. Brain disabled.");
  process.exit(0);
}

const DATABASE_URL = config.database_url;
const OPENROUTER_API_KEY = config.openrouter_api_key || process.env.OPENROUTER_API_KEY;

if (!OPENROUTER_API_KEY) {
  console.error("Missing OPENROUTER_API_KEY. Brain cannot generate embeddings.");
  process.exit(1);
}

const pool = new pg.Pool({ connectionString: DATABASE_URL });

pool.on("connect", async (client) => {
  await pgvector.registerTypes(client);
});

pool.on("error", (err) => {
  console.error("Database pool error:", err.message);
});

// =============================================================================
// Embedding Generation
// =============================================================================

async function getEmbedding(text) {
  const res = await fetch("https://openrouter.ai/api/v1/embeddings", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENROUTER_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model: EMBEDDING_MODEL, input: text }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Embedding API error: ${res.status} ${err}`);
  }
  const data = await res.json();
  return data.data[0].embedding;
}

// =============================================================================
// Conflict Detection (ADR Step 3 — agent_capture conflict logic)
// =============================================================================

async function classifyConflict(thoughtA, thoughtB) {
  try {
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${OPENROUTER_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "openai/gpt-4o-mini",
        messages: [{
          role: "user",
          content: `You are a conflict classifier for an institutional memory system. Compare these two thoughts and classify their relationship.

Thought A (existing): ${thoughtA}
Thought B (new): ${thoughtB}

Classify as exactly one of: DUPLICATE, CONTRADICTION, COMPLEMENT, SUPERSESSION, or NOVEL

Respond in JSON format:
{"classification": "...", "confidence": 0.0-1.0, "reasoning": "..."}`,
        }],
        response_format: { type: "json_object" },
      }),
    });
    if (!res.ok) throw new Error(`LLM API error: ${res.status}`);
    const data = await res.json();
    return JSON.parse(data.choices[0].message.content);
  } catch (err) {
    console.error("Conflict classification failed:", err.message);
    return null; // Classification failure = store without conflict check
  }
}

async function detectConflicts(client, embedding, content, scope, brainConfig) {
  if (!brainConfig.conflict_detection_enabled) return { action: "store" };

  // Search for similar active decisions in overlapping scopes
  const result = await client.query(
    `SELECT id, content, scope, source_agent
     FROM match_thoughts_scored($1, $2, 5, '{}', $3, false)
     WHERE thought_type IN ('decision', 'preference')`,
    [pgvector.toSql(embedding), brainConfig.conflict_candidate_threshold, scope?.[0] || null]
  );

  if (result.rows.length === 0) return { action: "store" };

  const topMatch = result.rows[0];
  const similarity = parseFloat(
    (await client.query(
      `SELECT (1 - (embedding <=> $1))::float AS sim FROM thoughts WHERE id = $2`,
      [pgvector.toSql(embedding), topMatch.id]
    )).rows[0].sim
  );

  // Tier 1: Duplicate (>0.9)
  if (similarity > brainConfig.conflict_duplicate_threshold) {
    return { action: "merge", existingId: topMatch.id, similarity };
  }

  // Tier 2: Candidate (0.7-0.9) — LLM classifies if enabled
  if (similarity > brainConfig.conflict_candidate_threshold) {
    if (!brainConfig.conflict_llm_enabled) {
      return { action: "store", conflictFlag: true, candidateId: topMatch.id, similarity };
    }

    const classification = await classifyConflict(topMatch.content, content);
    if (!classification) {
      // LLM failed — store without conflict check, return warning
      return { action: "store", warning: "Conflict classification failed" };
    }

    switch (classification.classification) {
      case "DUPLICATE":
        return { action: "merge", existingId: topMatch.id, similarity };
      case "CONTRADICTION":
        // Check if same scope = same team (newest wins) or cross-scope (flag for human)
        const sameScope = topMatch.scope?.some(s => scope?.includes(s));
        if (sameScope) {
          return { action: "supersede", existingId: topMatch.id, classification };
        } else {
          return { action: "conflict", existingId: topMatch.id, classification };
        }
      case "SUPERSESSION":
        return { action: "supersede", existingId: topMatch.id, classification };
      case "COMPLEMENT":
      case "NOVEL":
      default:
        return { action: "store", relatedId: topMatch.id, classification };
    }
  }

  // Tier 3: Novel (<0.7)
  return { action: "store" };
}

// =============================================================================
// Brain Config Cache
// =============================================================================

let brainConfigCache = null;
let brainConfigCacheTime = 0;

async function getBrainConfig(client) {
  const now = Date.now();
  if (brainConfigCache && now - brainConfigCacheTime < 10000) return brainConfigCache;
  const result = await (client || pool).query("SELECT * FROM brain_config WHERE id = 1");
  brainConfigCache = result.rows[0];
  brainConfigCacheTime = now;
  return brainConfigCache;
}

// =============================================================================
// MCP Tools (ADR Step 3)
// =============================================================================

function registerTools(srv) {

  // ───────────────────────────────────────────────────────────────────────────
  // Tool 1: agent_capture — Schema-enforced thought capture with conflict detection
  // ───────────────────────────────────────────────────────────────────────────

  srv.tool(
    "agent_capture",
    "Store a thought with schema-enforced metadata. Handles dedup, conflict detection, and supersedes relations. Required: content, thought_type, source_agent, source_phase, importance.",
    {
      content: z.string().min(1).describe("The thought content"),
      thought_type: z.enum(THOUGHT_TYPES).describe("Type of thought"),
      source_agent: z.enum(SOURCE_AGENTS).describe("Agent capturing the thought"),
      source_phase: z.enum(SOURCE_PHASES).describe("Pipeline phase"),
      importance: z.number().min(0).max(1).describe("Importance score 0-1"),
      trigger_event: z.string().optional().describe("What triggered this capture"),
      supersedes_id: z.string().uuid().optional().describe("UUID of thought this supersedes"),
      scope: z.array(z.string()).optional().describe("ltree scope paths"),
      metadata: z.record(z.string(), z.unknown()).optional().describe("Additional metadata"),
    },
    async ({ content, thought_type, source_agent, source_phase, importance, trigger_event, supersedes_id, scope, metadata = {} }) => {
      const client = await pool.connect();
      try {
        await client.query("BEGIN");

        // Generate embedding
        let embedding;
        try {
          embedding = await getEmbedding(content);
        } catch (err) {
          await client.query("ROLLBACK");
          return { content: [{ type: "text", text: `Error: Embedding generation failed: ${err.message}` }], isError: true };
        }

        const scopeArray = scope || ["default"];
        const brainConfig = await getBrainConfig(client);
        let conflictResult = { action: "store" };
        let relatedIds = [];

        // Conflict detection (only for decision/preference types)
        if (["decision", "preference"].includes(thought_type)) {
          conflictResult = await detectConflicts(client, embedding, content, scopeArray, brainConfig);
        }

        // Handle conflict detection result
        if (conflictResult.action === "merge") {
          // Duplicate — update existing thought
          await client.query(
            `UPDATE thoughts SET
              content = CASE WHEN importance < $2 THEN $1 ELSE content END,
              importance = GREATEST(importance, $2),
              metadata = metadata || $3,
              last_accessed_at = now(),
              updated_at = now()
            WHERE id = $4`,
            [content, importance, JSON.stringify(metadata), conflictResult.existingId]
          );
          await client.query("COMMIT");
          return {
            content: [{
              type: "text",
              text: JSON.stringify({
                thought_id: conflictResult.existingId,
                action: "merged",
                similarity: conflictResult.similarity,
              }),
            }],
          };
        }

        // Insert new thought
        const insertResult = await client.query(
          `INSERT INTO thoughts (content, embedding, metadata, thought_type, source_agent, source_phase, importance, trigger_event, status, scope)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::ltree[])
           RETURNING id, created_at`,
          [
            content,
            pgvector.toSql(embedding),
            JSON.stringify(metadata),
            thought_type,
            source_agent,
            source_phase,
            importance,
            trigger_event || null,
            conflictResult.action === "conflict" ? "conflicted" : "active",
            `{${scopeArray.join(",")}}`,
          ]
        );
        const newThought = insertResult.rows[0];

        // Handle supersedes
        if (supersedes_id) {
          await client.query(
            `INSERT INTO thought_relations (source_id, target_id, relation_type, context)
             VALUES ($1, $2, 'supersedes', 'Explicit supersession via agent_capture')
             ON CONFLICT (source_id, target_id, relation_type) DO NOTHING`,
            [newThought.id, supersedes_id]
          );
          await client.query(
            `UPDATE thoughts SET status = 'superseded', invalidated_at = now() WHERE id = $1`,
            [supersedes_id]
          );
          relatedIds.push(supersedes_id);
        }

        // Handle conflict detection actions
        if (conflictResult.action === "supersede") {
          await client.query(
            `INSERT INTO thought_relations (source_id, target_id, relation_type, context)
             VALUES ($1, $2, 'supersedes', $3)
             ON CONFLICT (source_id, target_id, relation_type) DO NOTHING`,
            [newThought.id, conflictResult.existingId, conflictResult.classification?.reasoning || "Automatic supersession"]
          );
          await client.query(
            `UPDATE thoughts SET status = 'superseded', invalidated_at = now() WHERE id = $1`,
            [conflictResult.existingId]
          );
          relatedIds.push(conflictResult.existingId);
        }

        if (conflictResult.action === "conflict") {
          // Mark existing as conflicted too
          await client.query(
            `UPDATE thoughts SET status = 'conflicted' WHERE id = $1`,
            [conflictResult.existingId]
          );
          await client.query(
            `INSERT INTO thought_relations (source_id, target_id, relation_type, context)
             VALUES ($1, $2, 'contradicts', $3)
             ON CONFLICT (source_id, target_id, relation_type) DO NOTHING`,
            [newThought.id, conflictResult.existingId, conflictResult.classification?.reasoning || "Cross-scope contradiction"]
          );
          relatedIds.push(conflictResult.existingId);
        }

        if (conflictResult.relatedId) {
          relatedIds.push(conflictResult.relatedId);
        }

        await client.query("COMMIT");

        const response = {
          thought_id: newThought.id,
          created_at: newThought.created_at,
          conflict_flag: conflictResult.action === "conflict" || conflictResult.conflictFlag || false,
          related_ids: relatedIds,
        };
        if (conflictResult.warning) response.warning = conflictResult.warning;

        return { content: [{ type: "text", text: JSON.stringify(response) }] };
      } catch (err) {
        await client.query("ROLLBACK");
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      } finally {
        client.release();
      }
    }
  );

  // ───────────────────────────────────────────────────────────────────────────
  // Tool 2: agent_search — Semantic search with three-axis scoring
  // ───────────────────────────────────────────────────────────────────────────

  srv.tool(
    "agent_search",
    "Semantic search using three-axis scoring (recency + importance + relevance). Updates last_accessed_at on returned results.",
    {
      query: z.string().min(1).describe("Natural language search query"),
      threshold: z.number().min(0).max(1).optional().default(0.2).describe("Minimum similarity 0-1"),
      limit: z.number().min(1).max(100).optional().default(10).describe("Max results"),
      scope: z.string().optional().describe("ltree scope filter (e.g. acme.payments)"),
      include_invalidated: z.boolean().optional().default(false).describe("Include superseded/invalidated thoughts"),
      filter: z.record(z.string(), z.unknown()).optional().describe("Metadata filter"),
    },
    async ({ query, threshold = 0.2, limit = 10, scope, include_invalidated = false, filter = {} }) => {
      try {
        const embedding = await getEmbedding(query);
        const result = await pool.query(
          `SELECT * FROM match_thoughts_scored($1, $2, $3, $4, $5, $6)`,
          [
            pgvector.toSql(embedding),
            threshold,
            limit,
            JSON.stringify(filter),
            scope || null,
            include_invalidated,
          ]
        );

        if (result.rows.length === 0) {
          return { content: [{ type: "text", text: JSON.stringify({ results: [] }) }] };
        }

        // Update last_accessed_at on returned thoughts
        const ids = result.rows.map(r => r.id);
        await pool.query(
          `UPDATE thoughts SET last_accessed_at = now() WHERE id = ANY($1)`,
          [ids]
        );

        const results = result.rows.map(r => ({
          id: r.id,
          content: r.content,
          metadata: r.metadata,
          thought_type: r.thought_type,
          source_agent: r.source_agent,
          source_phase: r.source_phase,
          importance: r.importance,
          status: r.status,
          scope: r.scope,
          created_at: r.created_at,
          similarity: parseFloat(r.similarity?.toFixed(4)),
          recency_score: parseFloat(r.recency_score?.toFixed(4)),
          combined_score: parseFloat(r.combined_score?.toFixed(4)),
        }));

        return { content: [{ type: "text", text: JSON.stringify({ results }) }] };
      } catch (err) {
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      }
    }
  );

  // ───────────────────────────────────────────────────────────────────────────
  // Tool 3: atelier_browse — List/filter thoughts with pagination
  // ───────────────────────────────────────────────────────────────────────────

  srv.tool(
    "atelier_browse",
    "Browse thoughts with filtering by status, type, agent, and scope. Paginated.",
    {
      limit: z.number().min(1).max(100).optional().default(20).describe("Results per page"),
      offset: z.number().min(0).optional().default(0).describe("Pagination offset"),
      status: z.enum(THOUGHT_STATUSES).optional().describe("Filter by status"),
      thought_type: z.enum(THOUGHT_TYPES).optional().describe("Filter by thought type"),
      source_agent: z.enum(SOURCE_AGENTS).optional().describe("Filter by source agent"),
      scope: z.string().optional().describe("Filter by ltree scope"),
    },
    async ({ limit = 20, offset = 0, status, thought_type, source_agent, scope }) => {
      try {
        const conditions = [];
        const params = [];
        let paramIdx = 1;

        if (status) { conditions.push(`status = $${paramIdx++}`); params.push(status); }
        if (thought_type) { conditions.push(`thought_type = $${paramIdx++}`); params.push(thought_type); }
        if (source_agent) { conditions.push(`source_agent = $${paramIdx++}`); params.push(source_agent); }
        if (scope) { conditions.push(`scope @> ARRAY[$${paramIdx++}]::ltree[]`); params.push(scope); }

        const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";
        params.push(limit, offset);

        const result = await pool.query(
          `SELECT id, content, thought_type, source_agent, source_phase, importance, status, scope, created_at, updated_at
           FROM thoughts ${where}
           ORDER BY created_at DESC
           LIMIT $${paramIdx++} OFFSET $${paramIdx++}`,
          params
        );

        const countResult = await pool.query(
          `SELECT count(*)::int AS total FROM thoughts ${where}`,
          params.slice(0, -2) // exclude limit/offset
        );

        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              thoughts: result.rows,
              total: countResult.rows[0].total,
              limit,
              offset,
            }),
          }],
        };
      } catch (err) {
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      }
    }
  );

  // ───────────────────────────────────────────────────────────────────────────
  // Tool 4: atelier_stats — Brain health and statistics
  // ───────────────────────────────────────────────────────────────────────────

  srv.tool(
    "atelier_stats",
    "Brain health check and statistics. Reports brain_enabled, counts by type/status/agent, consolidation timestamps.",
    {},
    async () => {
      try {
        const brainConfig = await getBrainConfig();

        const byType = await pool.query(
          `SELECT thought_type, count(*)::int AS count FROM thoughts GROUP BY thought_type ORDER BY count DESC`
        );
        const byStatus = await pool.query(
          `SELECT status, count(*)::int AS count FROM thoughts GROUP BY status ORDER BY count DESC`
        );
        const byAgent = await pool.query(
          `SELECT source_agent, count(*)::int AS count FROM thoughts GROUP BY source_agent ORDER BY count DESC`
        );
        const totalResult = await pool.query(`SELECT count(*)::int AS total FROM thoughts`);
        const activeResult = await pool.query(`SELECT count(*)::int AS active FROM thoughts WHERE status = 'active'`);
        const expiredResult = await pool.query(`SELECT count(*)::int AS expired FROM thoughts WHERE status = 'expired'`);
        const invalidatedResult = await pool.query(`SELECT count(*)::int AS invalidated FROM thoughts WHERE status IN ('superseded', 'invalidated')`);

        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              brain_enabled: brainConfig.brain_enabled,
              config_source: config._source,
              total: totalResult.rows[0].total,
              active: activeResult.rows[0].active,
              expired: expiredResult.rows[0].expired,
              invalidated: invalidatedResult.rows[0].invalidated,
              by_type: Object.fromEntries(byType.rows.map(r => [r.thought_type, r.count])),
              by_status: Object.fromEntries(byStatus.rows.map(r => [r.status, r.count])),
              by_agent: Object.fromEntries(byAgent.rows.map(r => [r.source_agent, r.count])),
              consolidation_interval_minutes: brainConfig.consolidation_interval_minutes,
            }),
          }],
        };
      } catch (err) {
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      }
    }
  );

  // ───────────────────────────────────────────────────────────────────────────
  // Tool 5: atelier_relation — Create typed relations between thoughts
  // ───────────────────────────────────────────────────────────────────────────

  srv.tool(
    "atelier_relation",
    "Link two thoughts via a typed relation. 'supersedes' auto-invalidates the target. source_id = newer/derived, target_id = older/original.",
    {
      source_id: z.string().uuid().describe("UUID of the newer/derived thought"),
      target_id: z.string().uuid().describe("UUID of the older/original thought"),
      relation_type: z.enum(RELATION_TYPES).describe("Type of relation"),
      context: z.string().optional().describe("Optional context for the relation"),
    },
    async ({ source_id, target_id, relation_type, context }) => {
      if (source_id === target_id) {
        return { content: [{ type: "text", text: "Error: Cannot create self-referential relation" }], isError: true };
      }

      const client = await pool.connect();
      try {
        await client.query("BEGIN");

        // Check for cycles if supersedes
        if (relation_type === "supersedes") {
          const cycleCheck = await client.query(
            `WITH RECURSIVE chain AS (
              SELECT target_id AS id, 1 AS depth FROM thought_relations WHERE source_id = $2 AND relation_type = 'supersedes'
              UNION ALL
              SELECT r.target_id, chain.depth + 1
              FROM thought_relations r JOIN chain ON chain.id = r.source_id
              WHERE r.relation_type = 'supersedes' AND chain.depth < 20
            )
            SELECT 1 FROM chain WHERE id = $1 LIMIT 1`,
            [source_id, target_id]
          );
          if (cycleCheck.rows.length > 0) {
            await client.query("ROLLBACK");
            return { content: [{ type: "text", text: "Error: Cycle detected in supersedes chain" }], isError: true };
          }
        }

        await client.query(
          `INSERT INTO thought_relations (source_id, target_id, relation_type, context)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (source_id, target_id, relation_type) DO UPDATE SET context = $4`,
          [source_id, target_id, relation_type, context || null]
        );

        // Auto-invalidate on supersedes
        if (relation_type === "supersedes") {
          await client.query(
            `UPDATE thoughts SET status = 'superseded', invalidated_at = now() WHERE id = $1 AND status = 'active'`,
            [target_id]
          );
        }

        await client.query("COMMIT");
        return {
          content: [{
            type: "text",
            text: JSON.stringify({ created: true, source_id, target_id, relation_type }),
          }],
        };
      } catch (err) {
        await client.query("ROLLBACK");
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      } finally {
        client.release();
      }
    }
  );

  // ───────────────────────────────────────────────────────────────────────────
  // Tool 6: atelier_trace — Recursive chain traversal
  // ───────────────────────────────────────────────────────────────────────────

  srv.tool(
    "atelier_trace",
    "Traverse the relation graph from a thought. Backward = what led here. Forward = what followed. Returns ordered chain with relation types.",
    {
      thought_id: z.string().uuid().describe("Starting thought UUID"),
      direction: z.enum(["backward", "forward", "both"]).optional().default("both").describe("Traversal direction"),
      max_depth: z.number().min(0).max(50).optional().default(10).describe("Maximum traversal depth"),
    },
    async ({ thought_id, direction = "both", max_depth = 10 }) => {
      try {
        // Get the root thought
        const rootResult = await pool.query(
          `SELECT id, content, thought_type, source_agent, source_phase, importance, status, scope, created_at
           FROM thoughts WHERE id = $1`,
          [thought_id]
        );
        if (rootResult.rows.length === 0) {
          return { content: [{ type: "text", text: `Error: Thought ${thought_id} not found` }], isError: true };
        }

        const chain = [{ ...rootResult.rows[0], depth: 0, via_relation: null, via_context: null, direction: "root" }];
        const visited = new Set([thought_id]);

        // Backward traversal: follow source_id → find target_id (what this came from)
        if (direction === "backward" || direction === "both") {
          const backResult = await pool.query(
            `WITH RECURSIVE chain AS (
              SELECT t.id, t.content, t.thought_type, t.source_agent, t.source_phase, t.importance, t.status, t.scope, t.created_at,
                     1 AS depth, r.relation_type AS via_relation, r.context AS via_context
              FROM thought_relations r
              JOIN thoughts t ON t.id = r.target_id
              WHERE r.source_id = $1
              UNION ALL
              SELECT t.id, t.content, t.thought_type, t.source_agent, t.source_phase, t.importance, t.status, t.scope, t.created_at,
                     chain.depth + 1, r.relation_type, r.context
              FROM thought_relations r
              JOIN thoughts t ON t.id = r.target_id
              JOIN chain ON chain.id = r.source_id
              WHERE chain.depth < $2
            )
            SELECT DISTINCT ON (id) * FROM chain ORDER BY id, depth`,
            [thought_id, max_depth]
          );
          for (const row of backResult.rows) {
            if (!visited.has(row.id)) {
              visited.add(row.id);
              chain.push({ ...row, direction: "backward" });
            }
          }
        }

        // Forward traversal: follow target_id → find source_id (what was derived)
        if (direction === "forward" || direction === "both") {
          const forwardResult = await pool.query(
            `WITH RECURSIVE chain AS (
              SELECT t.id, t.content, t.thought_type, t.source_agent, t.source_phase, t.importance, t.status, t.scope, t.created_at,
                     1 AS depth, r.relation_type AS via_relation, r.context AS via_context
              FROM thought_relations r
              JOIN thoughts t ON t.id = r.source_id
              WHERE r.target_id = $1
              UNION ALL
              SELECT t.id, t.content, t.thought_type, t.source_agent, t.source_phase, t.importance, t.status, t.scope, t.created_at,
                     chain.depth + 1, r.relation_type, r.context
              FROM thought_relations r
              JOIN thoughts t ON t.id = r.source_id
              JOIN chain ON chain.id = r.target_id
              WHERE chain.depth < $2
            )
            SELECT DISTINCT ON (id) * FROM chain ORDER BY id, depth`,
            [thought_id, max_depth]
          );
          for (const row of forwardResult.rows) {
            if (!visited.has(row.id)) {
              visited.add(row.id);
              chain.push({ ...row, direction: "forward" });
            }
          }
        }

        // Sort by depth
        chain.sort((a, b) => a.depth - b.depth);

        return { content: [{ type: "text", text: JSON.stringify({ chain }) }] };
      } catch (err) {
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      }
    }
  );
}

// =============================================================================
// REST API (ADR Step 6 — Settings UI endpoints)
// =============================================================================

async function handleRestApi(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const path = url.pathname;

  try {
    // GET /api/health
    if (path === "/api/health" && req.method === "GET") {
      try {
        const brainConfig = await getBrainConfig();
        const countResult = await pool.query(`SELECT count(*)::int AS total FROM thoughts WHERE status = 'active'`);
        // Get last consolidation (most recent reflection created_at)
        const lastConsolResult = await pool.query(
          `SELECT created_at FROM thoughts WHERE thought_type = 'reflection' ORDER BY created_at DESC LIMIT 1`
        );
        const lastConsolidation = lastConsolResult.rows[0]?.created_at || null;
        const nextConsolidation = lastConsolidation
          ? new Date(new Date(lastConsolidation).getTime() + brainConfig.consolidation_interval_minutes * 60 * 1000)
          : null;
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({
          connected: true,
          brain_enabled: brainConfig.brain_enabled,
          config_source: config._source,
          thought_count: countResult.rows[0].total,
          consolidation_interval_minutes: brainConfig.consolidation_interval_minutes,
          last_consolidation: lastConsolidation,
          next_consolidation_at: nextConsolidation,
        }));
      } catch {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ connected: false }));
      }
      return true;
    }

    // GET /api/config
    if (path === "/api/config" && req.method === "GET") {
      const brainConfig = await getBrainConfig();
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(brainConfig));
      return true;
    }

    // PUT /api/config
    if (path === "/api/config" && req.method === "PUT") {
      const body = await readBody(req);
      const data = JSON.parse(body);
      const allowed = [
        "brain_enabled", "consolidation_interval_minutes", "consolidation_min_thoughts",
        "consolidation_max_thoughts", "conflict_detection_enabled", "conflict_duplicate_threshold",
        "conflict_candidate_threshold", "conflict_llm_enabled", "default_scope",
      ];
      const updates = [];
      const values = [];
      let paramIdx = 1;
      for (const [key, value] of Object.entries(data)) {
        if (!allowed.includes(key)) continue;
        // Validate types
        if (key.includes("interval") || key.includes("min_") || key.includes("max_")) {
          if (typeof value !== "number" || value < 0) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: `${key} must be a non-negative number` }));
            return true;
          }
        }
        if (key.includes("threshold")) {
          if (typeof value !== "number" || value < 0 || value > 1) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: `${key} must be between 0 and 1` }));
            return true;
          }
        }
        updates.push(`${key} = $${paramIdx++}`);
        values.push(value);
      }
      if (updates.length === 0) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "No valid fields to update" }));
        return true;
      }
      await pool.query(`UPDATE brain_config SET ${updates.join(", ")} WHERE id = 1`, values);
      brainConfigCache = null; // Invalidate cache
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ updated: true }));
      return true;
    }

    // GET /api/thought-types
    if (path === "/api/thought-types" && req.method === "GET") {
      const result = await pool.query(`SELECT * FROM thought_type_config ORDER BY thought_type`);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(result.rows));
      return true;
    }

    // PUT /api/thought-types/:type
    if (path.startsWith("/api/thought-types/") && req.method === "PUT") {
      const typeName = path.split("/").pop();
      if (!THOUGHT_TYPES.includes(typeName)) {
        res.writeHead(404, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: `Unknown thought type: ${typeName}` }));
        return true;
      }
      const body = await readBody(req);
      const data = JSON.parse(body);
      const updates = [];
      const values = [];
      let paramIdx = 1;
      if ("default_ttl_days" in data) { updates.push(`default_ttl_days = $${paramIdx++}`); values.push(data.default_ttl_days); }
      if ("default_importance" in data) { updates.push(`default_importance = $${paramIdx++}`); values.push(data.default_importance); }
      if ("description" in data) { updates.push(`description = $${paramIdx++}`); values.push(data.description); }
      values.push(typeName);
      await pool.query(`UPDATE thought_type_config SET ${updates.join(", ")} WHERE thought_type = $${paramIdx}`, values);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ updated: true, type: typeName }));
      return true;
    }

    // POST /api/purge-expired
    if (path === "/api/purge-expired" && req.method === "POST") {
      const thoughtResult = await pool.query(
        `DELETE FROM thoughts WHERE status = 'expired' RETURNING id`
      );
      const orphanResult = await pool.query(
        `DELETE FROM thought_relations WHERE
          source_id NOT IN (SELECT id FROM thoughts) OR
          target_id NOT IN (SELECT id FROM thoughts)
        RETURNING id`
      );
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        purged_thoughts: thoughtResult.rowCount,
        purged_relations: orphanResult.rowCount,
      }));
      return true;
    }

    // GET /api/stats
    if (path === "/api/stats" && req.method === "GET") {
      const byType = await pool.query(`SELECT thought_type, count(*)::int AS count FROM thoughts GROUP BY thought_type`);
      const byStatus = await pool.query(`SELECT status, count(*)::int AS count FROM thoughts GROUP BY status`);
      const byAgent = await pool.query(`SELECT source_agent, count(*)::int AS count FROM thoughts GROUP BY source_agent`);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        by_type: Object.fromEntries(byType.rows.map(r => [r.thought_type, r.count])),
        by_status: Object.fromEntries(byStatus.rows.map(r => [r.status, r.count])),
        by_agent: Object.fromEntries(byAgent.rows.map(r => [r.source_agent, r.count])),
      }));
      return true;
    }

    return false; // Not a REST API route
  } catch (err) {
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: err.message }));
    return true;
  }
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

// =============================================================================
// Step 4: TTL Enforcement Timer
// =============================================================================

async function runTTLEnforcement() {
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
      console.log(`TTL: Expired ${result.rowCount} thoughts`);
    }
  } catch (err) {
    console.error("TTL enforcement error:", err.message);
  }
}

let ttlTimer = null;

async function startTTLTimer() {
  const brainConfig = await getBrainConfig();
  // TTL runs less frequently than consolidation — default 60 min
  const intervalMs = 60 * 60 * 1000;
  ttlTimer = setInterval(runTTLEnforcement, intervalMs);
  // Run once on startup
  await runTTLEnforcement();
}

// =============================================================================
// Step 5: Consolidation Engine
// =============================================================================

async function runConsolidation() {
  const client = await pool.connect();
  try {
    const brainConfig = await getBrainConfig(client);
    if (!brainConfig.brain_enabled) return;

    // Find active, non-reflection thoughts not yet consolidated
    const unconsolidated = await client.query(`
      SELECT t.id, t.content, t.thought_type, t.importance, t.embedding
      FROM thoughts t
      WHERE t.status = 'active'
        AND t.thought_type != 'reflection'
        AND NOT EXISTS (
          SELECT 1 FROM thought_relations r
          WHERE r.target_id = t.id AND r.relation_type = 'synthesized_from'
        )
      ORDER BY t.created_at DESC
      LIMIT $1
    `, [brainConfig.consolidation_max_thoughts]);

    if (unconsolidated.rows.length < brainConfig.consolidation_min_thoughts) {
      return; // Not enough thoughts to consolidate
    }

    // Simple clustering: group by pairwise similarity > 0.6
    const thoughts = unconsolidated.rows;
    const clusters = [];
    const assigned = new Set();

    for (let i = 0; i < thoughts.length; i++) {
      if (assigned.has(thoughts[i].id)) continue;
      const cluster = [thoughts[i]];
      assigned.add(thoughts[i].id);

      for (let j = i + 1; j < thoughts.length; j++) {
        if (assigned.has(thoughts[j].id)) continue;
        // Check similarity between embeddings
        const simResult = await client.query(
          `SELECT (1 - ($1::vector(1536) <=> $2::vector(1536)))::float AS sim`,
          [thoughts[i].embedding, thoughts[j].embedding]
        );
        if (simResult.rows[0].sim > 0.6) {
          cluster.push(thoughts[j]);
          assigned.add(thoughts[j].id);
        }
      }

      if (cluster.length >= 3) {
        clusters.push(cluster);
      }
    }

    if (clusters.length === 0) return;

    // Synthesize each cluster into a reflection
    for (const cluster of clusters) {
      try {
        const thoughtContents = cluster.map((t, i) => `${i + 1}. [${t.thought_type}] ${t.content}`).join("\n");

        const llmRes = await fetch("https://openrouter.ai/api/v1/chat/completions", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${OPENROUTER_API_KEY}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model: "openai/gpt-4o-mini",
            messages: [{
              role: "user",
              content: `Synthesize these ${cluster.length} observations into a single higher-level insight. Preserve specific details, decisions, and reasoning. Do not generalize away the useful specifics.\n\n${thoughtContents}`,
            }],
          }),
        });

        if (!llmRes.ok) {
          console.error(`Consolidation LLM error for cluster: ${llmRes.status}`);
          continue; // Skip this cluster, try next
        }

        const llmData = await llmRes.json();
        const synthesis = llmData.choices[0].message.content;
        if (!synthesis) continue;

        // Generate embedding for the reflection
        const reflectionEmbedding = await getEmbedding(synthesis);

        // Compute importance: max(cluster) + 0.05, capped at 1.0
        const maxImportance = Math.max(...cluster.map(t => t.importance));
        const reflectionImportance = Math.min(1.0, maxImportance + 0.05);

        // Insert reflection
        await client.query("BEGIN");
        const reflResult = await client.query(
          `INSERT INTO thoughts (content, embedding, thought_type, source_agent, source_phase, importance, scope)
           VALUES ($1, $2, 'reflection', 'eva', 'reconciliation', $3, ARRAY['default']::ltree[])
           RETURNING id`,
          [synthesis, pgvector.toSql(reflectionEmbedding), reflectionImportance]
        );
        const reflectionId = reflResult.rows[0].id;

        // Create synthesized_from relations (reflection = source_id, source thought = target_id)
        for (const thought of cluster) {
          await client.query(
            `INSERT INTO thought_relations (source_id, target_id, relation_type, context)
             VALUES ($1, $2, 'synthesized_from', 'Automatic consolidation')
             ON CONFLICT (source_id, target_id, relation_type) DO NOTHING`,
            [reflectionId, thought.id]
          );
        }

        await client.query("COMMIT");
        console.log(`Consolidation: Created reflection from ${cluster.length} thoughts`);
      } catch (clusterErr) {
        await client.query("ROLLBACK").catch(() => {});
        console.error(`Consolidation cluster error: ${clusterErr.message}`);
        // Continue to next cluster
      }
    }
  } catch (err) {
    console.error("Consolidation error:", err.message);
  } finally {
    client.release();
  }
}

let consolidationTimer = null;

async function startConsolidationTimer() {
  const brainConfig = await getBrainConfig();
  const intervalMs = brainConfig.consolidation_interval_minutes * 60 * 1000;
  consolidationTimer = setInterval(runConsolidation, intervalMs);
  console.log(`Consolidation timer: every ${brainConfig.consolidation_interval_minutes} min`);
}

// =============================================================================
// Static File Serving (Settings UI — ADR Step 7)
// =============================================================================

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const UI_DIR = path.join(__dirname, "ui");

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
};

function handleStaticFile(req, res) {
  let urlPath = new URL(req.url, `http://${req.headers.host}`).pathname;

  // Only handle /ui paths
  if (!urlPath.startsWith("/ui")) return false;

  // /ui or /ui/ → serve index.html
  let relativePath = urlPath.slice("/ui".length) || "/index.html";
  if (relativePath === "/") relativePath = "/index.html";

  const ext = path.extname(relativePath);
  const contentType = MIME_TYPES[ext];
  if (!contentType) {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found");
    return true;
  }

  const filePath = path.join(UI_DIR, relativePath);

  // Prevent directory traversal
  if (!filePath.startsWith(UI_DIR)) {
    res.writeHead(403, { "Content-Type": "text/plain" });
    res.end("Forbidden");
    return true;
  }

  if (!existsSync(filePath)) {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found");
    return true;
  }

  try {
    const content = readFileSync(filePath);
    res.writeHead(200, { "Content-Type": contentType });
    res.end(content);
  } catch {
    res.writeHead(500, { "Content-Type": "text/plain" });
    res.end("Internal server error");
  }
  return true;
}

// =============================================================================
// Server Startup (stdio or HTTP mode)
// =============================================================================

const mode = process.argv[2] || "stdio";

if (mode === "http") {
  const PORT = process.env.PORT || 8788;
  const httpSessions = new Map();

  function createSessionTransport() {
    let transport;
    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => crypto.randomUUID(),
      onsessioninitialized: (sessionId) => {
        httpSessions.set(sessionId, transport);
      },
    });
    transport.onclose = () => {
      if (transport.sessionId) httpSessions.delete(transport.sessionId);
    };
    return transport;
  }

  const httpServer = createServer(async (req, res) => {
    try {
      res.setHeader("Access-Control-Allow-Origin", "*");
      res.setHeader("Access-Control-Allow-Headers", "*");
      res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");

      if (req.method === "OPTIONS") { res.writeHead(204); res.end(); return; }

      // Serve static UI files
      if (req.url.startsWith("/ui") && req.method === "GET") {
        if (handleStaticFile(req, res)) return;
      }

      // Route /api/* to REST handlers
      if (req.url.startsWith("/api/")) {
        const handled = await handleRestApi(req, res);
        if (handled) return;
      }

      // MCP transport
      const sessionId = req.headers["mcp-session-id"];
      if (sessionId && httpSessions.has(sessionId)) {
        await httpSessions.get(sessionId).handleRequest(req, res);
        return;
      }
      if (sessionId && !httpSessions.has(sessionId)) {
        res.writeHead(404, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ jsonrpc: "2.0", error: { code: -32000, message: "Session not found" }, id: null }));
        return;
      }
      if (req.method === "POST") {
        const transport = createSessionTransport();
        const mcpServer = new McpServer({ name: "atelier-brain", version: "1.0.0" });
        registerTools(mcpServer);
        await mcpServer.connect(transport);
        await transport.handleRequest(req, res);
        return;
      }

      res.writeHead(405, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Method not allowed" }));
    } catch (err) {
      console.error("Request error:", err.message);
      if (!res.headersSent) {
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: err.message }));
      }
    }
  });

  httpServer.listen(PORT, async () => {
    console.log(`Atelier Brain MCP server running on http://localhost:${PORT} (config: ${config._source})`);
    // Start background timers (non-blocking)
    await startTTLTimer().catch(err => console.error("TTL timer start failed:", err.message));
    await startConsolidationTimer().catch(err => console.error("Consolidation timer start failed:", err.message));
  });
} else {
  const server = new McpServer({ name: "atelier-brain", version: "1.0.0" });
  registerTools(server);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // Start background timers in stdio mode too
  await startTTLTimer().catch(err => console.error("TTL timer start failed:", err.message));
  await startConsolidationTimer().catch(err => console.error("Consolidation timer start failed:", err.message));
}
