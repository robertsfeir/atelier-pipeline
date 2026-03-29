/**
 * REST API handler for Settings UI.
 * Includes auth middleware and all /api/* routes.
 * Depends on: db.mjs (pool), conflict.mjs (getBrainConfig), config.mjs (enums).
 */

import { THOUGHT_TYPES } from "./config.mjs";
import { getBrainConfig, resetBrainConfigCache } from "./conflict.mjs";

// =============================================================================
// REST Handler Factory
// =============================================================================

function createRestHandler(pool, cfg) {
  const apiToken = cfg.apiToken;

  function checkAuth(req, res, apiPath) {
    if (!apiToken) return true;
    if (apiPath === "/api/health") return true;
    const authHeader = req.headers["authorization"] || "";
    const token = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : "";
    if (token !== apiToken) {
      res.writeHead(401, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Unauthorized" }));
      return false;
    }
    return true;
  }

  async function handleRestApi(req, res) {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const urlPath = url.pathname;

    if (!checkAuth(req, res, urlPath)) return true;

    try {
      if (urlPath === "/api/health" && req.method === "GET") {
        return await handleHealth(res, pool, cfg);
      }
      if (urlPath === "/api/config" && req.method === "GET") {
        return await handleGetConfig(res, pool);
      }
      if (urlPath === "/api/config" && req.method === "PUT") {
        return await handlePutConfig(req, res, pool);
      }
      if (urlPath === "/api/thought-types" && req.method === "GET") {
        return await handleGetThoughtTypes(res, pool);
      }
      if (urlPath.startsWith("/api/thought-types/") && req.method === "PUT") {
        return await handlePutThoughtType(req, res, pool, urlPath);
      }
      if (urlPath === "/api/purge-expired" && req.method === "POST") {
        return await handlePurgeExpired(res, pool);
      }
      if (urlPath === "/api/stats" && req.method === "GET") {
        return await handleStats(res, pool);
      }
      if (urlPath === "/api/telemetry/scopes" && req.method === "GET") {
        return await handleTelemetryScopes(res, pool);
      }
      if (urlPath === "/api/telemetry/summary" && req.method === "GET") {
        return await handleTelemetrySummary(req, res, pool);
      }
      if (urlPath === "/api/telemetry/agents" && req.method === "GET") {
        return await handleTelemetryAgents(req, res, pool);
      }

      return false;
    } catch (err) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: err.message }));
      return true;
    }
  }

  return handleRestApi;
}

// =============================================================================
// Route Handlers
// =============================================================================

async function handleHealth(res, pool, cfg) {
  try {
    const brainConfig = await getBrainConfig(pool);
    const countResult = await pool.query(`SELECT count(*)::int AS total FROM thoughts WHERE status = 'active'`);
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
      brain_name: cfg.brain_name || "Brain",
      config_source: cfg._source,
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

async function handleGetConfig(res, pool) {
  const brainConfig = await getBrainConfig(pool);
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify(brainConfig));
  return true;
}

async function handlePutConfig(req, res, pool) {
  const body = await readBody(req);
  let data;
  try {
    data = JSON.parse(body);
  } catch {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Invalid JSON" }));
    return true;
  }
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
    if (!validateConfigField(key, value, res)) return true;
    updates.push(`${key} = $${paramIdx++}`);
    values.push(value);
  }

  if (updates.length === 0) {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "No valid fields to update" }));
    return true;
  }

  await pool.query(`UPDATE brain_config SET ${updates.join(", ")} WHERE id = 1`, values);
  resetBrainConfigCache();
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ updated: true }));
  return true;
}

function validateConfigField(key, value, res) {
  if (key.includes("interval") || key.includes("min_") || key.includes("max_")) {
    if (typeof value !== "number" || value < 0) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: `${key} must be a non-negative number` }));
      return false;
    }
  }
  if (key.includes("threshold")) {
    if (typeof value !== "number" || value < 0 || value > 1) {
      res.writeHead(400, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: `${key} must be between 0 and 1` }));
      return false;
    }
  }
  return true;
}

async function handleGetThoughtTypes(res, pool) {
  const result = await pool.query(`SELECT * FROM thought_type_config ORDER BY thought_type`);
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify(result.rows));
  return true;
}

async function handlePutThoughtType(req, res, pool, urlPath) {
  const typeName = urlPath.split("/").pop();
  if (!THOUGHT_TYPES.includes(typeName)) {
    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: `Unknown thought type: ${typeName}` }));
    return true;
  }
  const body = await readBody(req);
  let data;
  try {
    data = JSON.parse(body);
  } catch {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Invalid JSON" }));
    return true;
  }
  const updates = [];
  const values = [];
  let paramIdx = 1;
  if ("default_ttl_days" in data) { updates.push(`default_ttl_days = $${paramIdx++}`); values.push(data.default_ttl_days); }
  if ("default_importance" in data) { updates.push(`default_importance = $${paramIdx++}`); values.push(data.default_importance); }
  if ("description" in data) { updates.push(`description = $${paramIdx++}`); values.push(data.description); }

  if (updates.length === 0) {
    res.writeHead(400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "No valid fields to update" }));
    return true;
  }

  values.push(typeName);
  await pool.query(`UPDATE thought_type_config SET ${updates.join(", ")} WHERE thought_type = $${paramIdx}`, values);
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ updated: true, type: typeName }));
  return true;
}

async function handlePurgeExpired(res, pool) {
  const thoughtResult = await pool.query(
    `DELETE FROM thoughts WHERE status = 'expired' RETURNING id`
  );
  const orphanResult = await pool.query(
    `DELETE FROM thought_relations r
     USING (
       SELECT r2.id
       FROM thought_relations r2
       LEFT JOIN thoughts t1 ON r2.source_id = t1.id
       LEFT JOIN thoughts t2 ON r2.target_id = t2.id
       WHERE t1.id IS NULL OR t2.id IS NULL
     ) orphans
     WHERE r.id = orphans.id
     RETURNING r.id`
  );
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({
    purged_thoughts: thoughtResult.rowCount,
    purged_relations: orphanResult.rowCount,
  }));
  return true;
}

async function handleStats(res, pool) {
  const [byType, byStatus, byAgent, byHuman] = await Promise.all([
    pool.query(`SELECT thought_type, count(*)::int AS count FROM thoughts GROUP BY thought_type`),
    pool.query(`SELECT status, count(*)::int AS count FROM thoughts GROUP BY status`),
    pool.query(`SELECT source_agent, count(*)::int AS count FROM thoughts GROUP BY source_agent`),
    pool.query(`SELECT COALESCE(captured_by, 'unknown') AS captured_by, count(*)::int AS count FROM thoughts GROUP BY captured_by`),
  ]);
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({
    by_type: Object.fromEntries(byType.rows.map(r => [r.thought_type, r.count])),
    by_status: Object.fromEntries(byStatus.rows.map(r => [r.status, r.count])),
    by_agent: Object.fromEntries(byAgent.rows.map(r => [r.source_agent, r.count])),
    by_human: Object.fromEntries(byHuman.rows.map(r => [r.captured_by, r.count])),
  }));
  return true;
}

// =============================================================================
// Telemetry Handlers
// =============================================================================

async function handleTelemetryScopes(res, pool) {
  const result = await pool.query(
    `SELECT DISTINCT unnest(scope)::text AS scope
     FROM thoughts
     WHERE thought_type = 'insight'
       AND source_phase = 'telemetry'
     ORDER BY scope`
  );
  const scopes = result.rows.map(r => r.scope);
  res.writeHead(200, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  });
  res.end(JSON.stringify(scopes));
  return true;
}

function parseScopeFilter(req) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const scope = url.searchParams.get("scope");
  if (scope && scope !== "all") return scope;
  return null;
}

async function handleTelemetrySummary(req, res, pool) {
  const scope = parseScopeFilter(req);
  const params = [];
  let scopeClause = "";
  if (scope) {
    params.push(scope);
    scopeClause = ` AND scope @> ARRAY[$${params.length}]::ltree[]`;
  }

  const result = await pool.query(
    `SELECT content, metadata, created_at
     FROM thoughts
     WHERE thought_type = 'insight'
       AND source_phase = 'telemetry'
       AND metadata->>'telemetry_tier' = '3'${scopeClause}
     ORDER BY created_at DESC
     LIMIT 10`,
    params
  );
  res.writeHead(200, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  });
  res.end(JSON.stringify(result.rows));
  return true;
}

async function handleTelemetryAgents(req, res, pool) {
  const scope = parseScopeFilter(req);
  const params = [];
  let scopeClause = "";
  if (scope) {
    params.push(scope);
    scopeClause = ` AND scope @> ARRAY[$${params.length}]::ltree[]`;
  }

  const result = await pool.query(
    `SELECT
       metadata->>'agent_name' as agent,
       count(*)::int as invocations,
       avg((metadata->>'duration_ms')::numeric)::int as avg_duration_ms,
       sum((metadata->>'cost_usd')::numeric)::numeric(10,4) as total_cost,
       avg((metadata->>'input_tokens')::numeric)::int as avg_input_tokens,
       avg((metadata->>'output_tokens')::numeric)::int as avg_output_tokens
     FROM thoughts
     WHERE thought_type = 'insight'
       AND source_phase = 'telemetry'
       AND metadata->>'telemetry_tier' = '1'${scopeClause}
     GROUP BY metadata->>'agent_name'
     ORDER BY total_cost DESC`,
    params
  );
  res.writeHead(200, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  });
  res.end(JSON.stringify(result.rows));
  return true;
}

// =============================================================================
// Utilities
// =============================================================================

const MAX_BODY_SIZE = 1024 * 1024; // 1MB

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    let size = 0;
    req.on("data", chunk => {
      size += chunk.length;
      if (size > MAX_BODY_SIZE) {
        req.destroy();
        reject(new Error("Request body too large"));
        return;
      }
      body += chunk;
    });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

export { createRestHandler };
