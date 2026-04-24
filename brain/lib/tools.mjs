/**
 * MCP tool registration -- all 6 tools.
 * Each tool is a separate inner function to reduce cyclomatic complexity.
 * Depends on: db.mjs (pool), embed.mjs, conflict.mjs, config.mjs (enums).
 */

import { z } from "zod";
import pgvector from "pgvector/pg";
import {
  THOUGHT_TYPES, SOURCE_AGENTS, SOURCE_PHASES,
  THOUGHT_STATUSES, RELATION_TYPES,
} from "./config.mjs";
import { getEmbedding } from "./embed.mjs";
import { detectConflicts, getBrainConfig } from "./conflict.mjs";
import {
  discoverSubagentFiles,
  discoverEvaFiles,
  hydrateSubagentFile,
  hydrateEvaFile,
  generateTier3Summaries,
  parseStateFiles,
  expandHome,
} from "./hydrate.mjs";

// =============================================================================
// Tool Registration
// =============================================================================

/**
 * Module-level status map for atelier_hydrate calls.
 * Key: expanded session_path (string)
 * Value: status object with shape:
 *   { status, session_path, started_at, completed_at?, files_processed, files_skipped, thoughts_inserted, errors[] }
 */
const hydrateStatusMap = new Map();

function registerTools(srv, pool, cfg) {
  const apiKey = cfg.openrouter_api_key;
  const capturedBy = cfg.capturedBy;

  registerAgentCapture(srv, pool, apiKey, capturedBy, cfg);
  registerAgentSearch(srv, pool, apiKey);
  registerAtelierBrowse(srv, pool);
  registerAtelierStats(srv, pool, cfg);
  registerAtelierRelation(srv, pool);
  registerAtelierTrace(srv, pool);
  registerAtelierHydrate(srv, pool, cfg);
  registerAtelierHydrateStatus(srv);
}

// =============================================================================
// Tool 1: agent_capture
// =============================================================================

function registerAgentCapture(srv, pool, apiKey, capturedBy, cfg) {
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
      scope: z.array(z.string()).optional().describe(
        "ltree scope paths. Pass an array of dot-separated namespace strings, e.g. ['pipeline.adr-0006', 'project.myproject']. Each element is one ltree path — do NOT use brace syntax ({a,b}). Labels may contain ASCII letters (case-sensitive), digits, underscores, and hyphens (hyphens require PostgreSQL >= 16 / ltree 1.2)."
      ),
      metadata: z.record(z.string(), z.unknown()).optional().describe("Additional metadata"),
      decided_by: z.object({
        agent: z.string(),
        human_approved: z.boolean(),
      }).optional().describe("Who made the decision and whether a human signed off"),
      alternatives_rejected: z.array(z.object({
        alternative: z.string(),
        reason: z.string(),
      })).optional().describe("Alternatives considered and why rejected"),
      evidence: z.array(z.object({
        file: z.string(),
        line: z.number().int().positive(),
      })).optional().describe("File:line references supporting the decision"),
      confidence: z.number().min(0).max(1).optional()
        .describe("Decision confidence 0-1; low values flag for retro review"),
    },
    async (params) => handleAgentCapture(params, pool, apiKey, capturedBy, cfg)
  );
}

async function handleAgentCapture(params, pool, apiKey, capturedBy, cfg) {
  const { content, thought_type, source_agent, source_phase, importance,
          trigger_event, supersedes_id, scope, metadata = {},
          decided_by, alternatives_rejected, evidence, confidence } = params;
  const client = await pool.connect();
  try {
    await client.query("BEGIN");

    let embedding;
    try {
      embedding = await getEmbedding(content, apiKey);
    } catch (err) {
      await client.query("ROLLBACK");
      return { content: [{ type: "text", text: `Error: Embedding generation failed: ${err.message}` }], isError: true };
    }

    const scopeArray = scope || ["default"];
    const brainConfig = await getBrainConfig(client);
    let conflictResult = { action: "store" };
    const relatedIds = [];

    if (["decision", "preference"].includes(thought_type)) {
      conflictResult = await detectConflicts(client, embedding, content, scopeArray, brainConfig, apiKey);
    }

    // Build provenance fields from explicit params (ADR-0026)
    const hasAnyProvenanceParam = decided_by !== undefined
      || alternatives_rejected !== undefined
      || evidence !== undefined
      || confidence !== undefined;

    const provenanceFields = {};
    if (decided_by !== undefined) provenanceFields.decided_by = decided_by;
    if (alternatives_rejected?.length) provenanceFields.alternatives_rejected = alternatives_rejected;
    if (evidence?.length) provenanceFields.evidence = evidence;
    if (confidence !== undefined) provenanceFields.confidence = confidence;

    let enrichedMetadata;
    if (Object.keys(provenanceFields).length > 0) {
      enrichedMetadata = { ...metadata, provenance: provenanceFields };
    } else if (hasAnyProvenanceParam) {
      // Explicit provenance params were passed but all were empty/absent --
      // still create an empty provenance object to signal intent (ADR-0026).
      enrichedMetadata = { ...metadata, provenance: {} };
    } else {
      enrichedMetadata = metadata;
    }

    if (conflictResult.action === "merge") {
      return await handleMerge(client, content, importance, enrichedMetadata, conflictResult);
    }

    const newThought = await insertThought(client, {
      content, embedding, metadata: enrichedMetadata, thought_type, source_agent,
      source_phase, importance, trigger_event, capturedBy,
      conflictResult, scopeArray,
    });

    await handleRelations(client, newThought.id, supersedes_id, conflictResult, relatedIds);

    await client.query("COMMIT");

    const response = {
      thought_id: newThought.id,
      created_at: newThought.created_at,
      captured_by: capturedBy,
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

async function handleMerge(client, content, importance, metadata, conflictResult) {
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

async function insertThought(client, params) {
  const result = await client.query(
    `INSERT INTO thoughts (content, embedding, metadata, thought_type, source_agent, source_phase, importance, trigger_event, captured_by, status, scope)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::ltree[])
     RETURNING id, created_at`,
    [
      params.content,
      pgvector.toSql(params.embedding),
      JSON.stringify(params.metadata),
      params.thought_type,
      params.source_agent,
      params.source_phase,
      params.importance,
      params.trigger_event || null,
      params.capturedBy,
      params.conflictResult.action === "conflict" ? "conflicted" : "active",
      params.scopeArray,
    ]
  );
  return result.rows[0];
}

async function handleRelations(client, newId, supersedesId, conflictResult, relatedIds) {
  if (supersedesId) {
    await createSupersessionRelation(client, newId, supersedesId, "Explicit supersession via agent_capture");
    relatedIds.push(supersedesId);
  }

  if (conflictResult.action === "supersede") {
    await createSupersessionRelation(
      client, newId, conflictResult.existingId,
      conflictResult.classification?.reasoning || "Automatic supersession"
    );
    relatedIds.push(conflictResult.existingId);
  }

  if (conflictResult.action === "conflict") {
    await client.query(
      `UPDATE thoughts SET status = 'conflicted' WHERE id = $1`,
      [conflictResult.existingId]
    );
    await client.query(
      `INSERT INTO thought_relations (source_id, target_id, relation_type, context)
       VALUES ($1, $2, 'contradicts', $3)
       ON CONFLICT (source_id, target_id, relation_type) DO NOTHING`,
      [newId, conflictResult.existingId, conflictResult.classification?.reasoning || "Cross-scope contradiction"]
    );
    relatedIds.push(conflictResult.existingId);
  }

  if (conflictResult.relatedId) {
    relatedIds.push(conflictResult.relatedId);
  }
}

async function createSupersessionRelation(client, sourceId, targetId, context) {
  await client.query(
    `INSERT INTO thought_relations (source_id, target_id, relation_type, context)
     VALUES ($1, $2, 'supersedes', $3)
     ON CONFLICT (source_id, target_id, relation_type) DO NOTHING`,
    [sourceId, targetId, context]
  );
  await client.query(
    `UPDATE thoughts SET status = 'superseded', invalidated_at = now() WHERE id = $1`,
    [targetId]
  );
}

// =============================================================================
// Tool 2: agent_search
// =============================================================================

function registerAgentSearch(srv, pool, apiKey) {
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
        const embedding = await getEmbedding(query, apiKey);
        const result = await pool.query(
          `SELECT * FROM match_thoughts_scored($1, $2, $3, $4, $5, $6)`,
          [pgvector.toSql(embedding), threshold, limit, JSON.stringify(filter), scope || null, include_invalidated]
        );

        if (result.rows.length === 0) {
          return { content: [{ type: "text", text: JSON.stringify({ results: [] }) }] };
        }

        const ids = result.rows.map(r => r.id);
        await pool.query(`UPDATE thoughts SET last_accessed_at = now() WHERE id = ANY($1)`, [ids]);

        const results = result.rows.map(r => ({
          id: r.id, content: r.content, metadata: r.metadata,
          thought_type: r.thought_type, source_agent: r.source_agent,
          source_phase: r.source_phase, importance: r.importance,
          status: r.status, scope: r.scope, captured_by: r.captured_by,
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
}

// =============================================================================
// Tool 3: atelier_browse
// =============================================================================

function registerAtelierBrowse(srv, pool) {
  srv.tool(
    "atelier_browse",
    "Browse thoughts with filtering by status, type, agent, and scope. Paginated.",
    {
      limit: z.number().min(1).max(100).optional().default(20).describe("Results per page"),
      offset: z.number().min(0).optional().default(0).describe("Pagination offset"),
      status: z.enum(THOUGHT_STATUSES).optional().describe("Filter by status"),
      thought_type: z.enum(THOUGHT_TYPES).optional().describe("Filter by thought type"),
      source_agent: z.enum(SOURCE_AGENTS).optional().describe("Filter by source agent"),
      captured_by: z.string().optional().describe("Filter by human who captured"),
      scope: z.string().optional().describe("Filter by ltree scope"),
    },
    async ({ limit = 20, offset = 0, status, thought_type, source_agent, captured_by, scope }) => {
      try {
        const conditions = [];
        const params = [];
        let paramIdx = 1;

        if (status) { conditions.push(`status = $${paramIdx++}`); params.push(status); }
        if (thought_type) { conditions.push(`thought_type = $${paramIdx++}`); params.push(thought_type); }
        if (source_agent) { conditions.push(`source_agent = $${paramIdx++}`); params.push(source_agent); }
        if (captured_by) { conditions.push(`captured_by = $${paramIdx++}`); params.push(captured_by); }
        if (scope) { conditions.push(`scope @> ARRAY[$${paramIdx++}]::ltree[]`); params.push(scope); }

        const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";
        params.push(limit, offset);

        const result = await pool.query(
          `SELECT id, content, thought_type, source_agent, source_phase, importance, status, scope, captured_by, created_at, updated_at
           FROM thoughts ${where}
           ORDER BY created_at DESC
           LIMIT $${paramIdx++} OFFSET $${paramIdx++}`,
          params
        );

        const countResult = await pool.query(
          `SELECT count(*)::int AS total FROM thoughts ${where}`,
          params.slice(0, -2)
        );

        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              thoughts: result.rows,
              total: countResult.rows[0].total,
              limit, offset,
            }),
          }],
        };
      } catch (err) {
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      }
    }
  );
}

// =============================================================================
// Tool 4: atelier_stats
// =============================================================================

function registerAtelierStats(srv, pool, cfg) {
  srv.tool(
    "atelier_stats",
    "Brain health check and statistics. Reports brain_enabled, counts by type/status/agent, consolidation timestamps.",
    {},
    async () => {
      try {
        const brainConfig = await getBrainConfig(pool);

        const [byType, byStatus, byAgent, byHuman, totalResult, activeResult, expiredResult, invalidatedResult] =
          await Promise.all([
            pool.query(`SELECT thought_type, count(*)::int AS count FROM thoughts GROUP BY thought_type ORDER BY count DESC`),
            pool.query(`SELECT status, count(*)::int AS count FROM thoughts GROUP BY status ORDER BY count DESC`),
            pool.query(`SELECT source_agent, count(*)::int AS count FROM thoughts GROUP BY source_agent ORDER BY count DESC`),
            pool.query(`SELECT COALESCE(captured_by, 'unknown') AS captured_by, count(*)::int AS count FROM thoughts GROUP BY captured_by ORDER BY count DESC`),
            pool.query(`SELECT count(*)::int AS total FROM thoughts`),
            pool.query(`SELECT count(*)::int AS active FROM thoughts WHERE status = 'active'`),
            pool.query(`SELECT count(*)::int AS expired FROM thoughts WHERE status = 'expired'`),
            pool.query(`SELECT count(*)::int AS invalidated FROM thoughts WHERE status IN ('superseded', 'invalidated')`),
          ]);

        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              brain_enabled: brainConfig.brain_enabled,
              brain_name: cfg.brain_name || "Brain",
              config_source: cfg._source,
              total: totalResult.rows[0].total,
              active: activeResult.rows[0].active,
              expired: expiredResult.rows[0].expired,
              invalidated: invalidatedResult.rows[0].invalidated,
              by_type: Object.fromEntries(byType.rows.map(r => [r.thought_type, r.count])),
              by_status: Object.fromEntries(byStatus.rows.map(r => [r.status, r.count])),
              by_agent: Object.fromEntries(byAgent.rows.map(r => [r.source_agent, r.count])),
              by_human: Object.fromEntries(byHuman.rows.map(r => [r.captured_by, r.count])),
              consolidation_interval_minutes: brainConfig.consolidation_interval_minutes,
            }),
          }],
        };
      } catch (err) {
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      }
    }
  );
}

// =============================================================================
// Tool 5: atelier_relation
// =============================================================================

function registerAtelierRelation(srv, pool) {
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

        if (relation_type === "supersedes") {
          const hasCycle = await checkSupersedeCycle(client, source_id, target_id);
          if (hasCycle) {
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
}

async function checkSupersedeCycle(client, sourceId, targetId) {
  const cycleCheck = await client.query(
    `WITH RECURSIVE chain AS (
      SELECT target_id AS id, 1 AS depth FROM thought_relations WHERE source_id = $2 AND relation_type = 'supersedes'
      UNION ALL
      SELECT r.target_id, chain.depth + 1
      FROM thought_relations r JOIN chain ON chain.id = r.source_id
      WHERE r.relation_type = 'supersedes' AND chain.depth < 20
    )
    SELECT 1 FROM chain WHERE id = $1 LIMIT 1`,
    [sourceId, targetId]
  );
  return cycleCheck.rows.length > 0;
}

// =============================================================================
// Tool 6: atelier_trace
// =============================================================================

function registerAtelierTrace(srv, pool) {
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
        const rootResult = await pool.query(
          `SELECT id, content, thought_type, source_agent, source_phase, importance, status, scope, captured_by, created_at, metadata
           FROM thoughts WHERE id = $1`,
          [thought_id]
        );
        if (rootResult.rows.length === 0) {
          return { content: [{ type: "text", text: `Error: Thought ${thought_id} not found` }], isError: true };
        }

        const chain = [{ ...rootResult.rows[0], depth: 0, via_relation: null, via_context: null, direction: "root" }];
        const visited = new Set([thought_id]);

        if (direction === "backward" || direction === "both") {
          await traverseBackward(pool, thought_id, max_depth, visited, chain);
        }

        if (direction === "forward" || direction === "both") {
          await traverseForward(pool, thought_id, max_depth, visited, chain);
        }

        chain.sort((a, b) => a.depth - b.depth);

        // Batch superseded_by lookup (ADR-0026): single query for entire chain
        const chainIds = chain.map(n => n.id);
        let supersededByMap = new Map();
        if (chainIds.length > 0) {
          const supersededByResult = await pool.query(
            `SELECT target_id, array_agg(source_id) AS superseded_by
             FROM thought_relations
             WHERE target_id = ANY($1) AND relation_type = 'supersedes'
             GROUP BY target_id`,
            [chainIds]
          );
          supersededByMap = new Map(
            supersededByResult.rows.map(r => [r.target_id, r.superseded_by])
          );
        }

        // Enrich each chain node with provenance and superseded_by
        for (let i = 0; i < chain.length; i++) {
          const { metadata: _m, ...rest } = chain[i];
          chain[i] = {
            ...rest,
            provenance: chain[i].metadata?.provenance || null,
            superseded_by: supersededByMap.get(chain[i].id) || [],
          };
        }

        return { content: [{ type: "text", text: JSON.stringify({ chain }) }] };
      } catch (err) {
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      }
    }
  );
}

async function traverseBackward(pool, thoughtId, maxDepth, visited, chain) {
  const result = await pool.query(
    `WITH RECURSIVE chain AS (
      SELECT t.id, t.content, t.thought_type, t.source_agent, t.source_phase, t.importance, t.status, t.scope, t.captured_by, t.created_at, t.metadata,
             1 AS depth, r.relation_type AS via_relation, r.context AS via_context
      FROM thought_relations r
      JOIN thoughts t ON t.id = r.target_id
      WHERE r.source_id = $1
      UNION ALL
      SELECT t.id, t.content, t.thought_type, t.source_agent, t.source_phase, t.importance, t.status, t.scope, t.captured_by, t.created_at, t.metadata,
             chain.depth + 1, r.relation_type, r.context
      FROM thought_relations r
      JOIN thoughts t ON t.id = r.target_id
      JOIN chain ON chain.id = r.source_id
      WHERE chain.depth < $2
    )
    SELECT DISTINCT ON (id) * FROM chain ORDER BY id, depth`,
    [thoughtId, maxDepth]
  );
  for (const row of result.rows) {
    if (!visited.has(row.id)) {
      visited.add(row.id);
      chain.push({ ...row, direction: "backward" });
    }
  }
}

async function traverseForward(pool, thoughtId, maxDepth, visited, chain) {
  const result = await pool.query(
    `WITH RECURSIVE chain AS (
      SELECT t.id, t.content, t.thought_type, t.source_agent, t.source_phase, t.importance, t.status, t.scope, t.captured_by, t.created_at, t.metadata,
             1 AS depth, r.relation_type AS via_relation, r.context AS via_context
      FROM thought_relations r
      JOIN thoughts t ON t.id = r.source_id
      WHERE r.target_id = $1
      UNION ALL
      SELECT t.id, t.content, t.thought_type, t.source_agent, t.source_phase, t.importance, t.status, t.scope, t.captured_by, t.created_at, t.metadata,
             chain.depth + 1, r.relation_type, r.context
      FROM thought_relations r
      JOIN thoughts t ON t.id = r.source_id
      JOIN chain ON chain.id = r.target_id
      WHERE chain.depth < $2
    )
    SELECT DISTINCT ON (id) * FROM chain ORDER BY id, depth`,
    [thoughtId, maxDepth]
  );
  for (const row of result.rows) {
    if (!visited.has(row.id)) {
      visited.add(row.id);
      chain.push({ ...row, direction: "forward" });
    }
  }
}

// =============================================================================
// Tool 7: atelier_hydrate
// =============================================================================

function registerAtelierHydrate(srv, pool, cfg) {
  srv.tool(
    "atelier_hydrate",
    "Hydrate JSONL telemetry from a Claude Code project sessions directory into the brain. Non-blocking: queues processing via setImmediate and returns immediately. Idempotent — already-hydrated files are skipped.",
    {
      session_path: z.string().min(1).describe("Absolute path to the Claude Code project sessions directory (e.g. ~/.claude/projects/-Users-you-myproject)"),
    },
    async ({ session_path }) => {
      const expandedPath = expandHome(session_path);

      // Write initial "running" status before setImmediate so callers can
      // poll atelier_hydrate_status immediately after the queued response.
      hydrateStatusMap.set(expandedPath, {
        status: "running",
        session_path: expandedPath,
        started_at: new Date().toISOString(),
        completed_at: undefined,
        files_processed: 0,
        files_skipped: 0,
        thoughts_inserted: 0,
        errors: [],
      });

      // Fire-and-forget: setImmediate schedules hydration after current event loop
      // tick so the MCP response returns immediately to the caller.
      setImmediate(async () => {
        const entry = hydrateStatusMap.get(expandedPath);
        try {
          const subagentFiles = discoverSubagentFiles(expandedPath);
          const evaFiles = discoverEvaFiles(expandedPath);

          for (const file of subagentFiles) {
            const inserted = await hydrateSubagentFile(pool, cfg, file);
            if (inserted) {
              entry.files_processed++;
              entry.thoughts_inserted++;
            } else {
              entry.files_skipped++;
            }
          }
          for (const file of evaFiles) {
            const inserted = await hydrateEvaFile(pool, cfg, file);
            if (inserted) {
              entry.files_processed++;
              entry.thoughts_inserted++;
            } else {
              entry.files_skipped++;
            }
          }

          const tier3Count = await generateTier3Summaries(pool, cfg);
          entry.thoughts_inserted += tier3Count;

          entry.status = "completed";
          entry.completed_at = new Date().toISOString();
        } catch (err) {
          // Non-fatal: log only — the MCP response has already been sent
          console.error(`atelier_hydrate background error: ${err.message}`);
          entry.status = "error";
          entry.errors.push(err.message);
          entry.completed_at = new Date().toISOString();
        }
      });

      return {
        content: [{
          type: "text",
          text: JSON.stringify({ status: "queued", session_path: expandedPath }),
        }],
      };
    }
  );
}

// =============================================================================
// Tool 8: atelier_hydrate_status
// =============================================================================

function registerAtelierHydrateStatus(srv) {
  srv.tool(
    "atelier_hydrate_status",
    "Returns the completion state of a previous atelier_hydrate call for the given session_path. Status is 'running' while processing, 'completed' on success, 'error' on failure, or 'idle' if no hydration has been queued for this path.",
    {
      session_path: z.string().min(1).describe("Absolute path passed to atelier_hydrate (same value, ~ expansion is applied automatically)"),
    },
    ({ session_path }) => {
      const expandedPath = expandHome(session_path);
      const entry = hydrateStatusMap.get(expandedPath);
      const payload = entry
        ? { ...entry }
        : {
            status: "idle",
            session_path: expandedPath,
            files_processed: 0,
            files_skipped: 0,
            thoughts_inserted: 0,
            errors: [],
            started_at: undefined,
            completed_at: undefined,
          };
      return {
        content: [{ type: "text", text: JSON.stringify(payload) }],
      };
    }
  );
}

export { registerTools, hydrateStatusMap };
