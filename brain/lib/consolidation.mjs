/**
 * Consolidation engine -- clusters similar thoughts and synthesizes reflections.
 * Uses SQL vectorized similarity (single query) + union-find clustering in JS.
 * Depends on: db.mjs (pool), embed.mjs, conflict.mjs (getBrainConfig).
 */

import pgvector from "pgvector/pg";
import { getEmbedding } from "./embed.mjs";
import { getBrainConfig } from "./conflict.mjs";

// =============================================================================
// Union-Find for Cluster Formation
// =============================================================================

function createUnionFind() {
  const parent = new Map();
  const rank = new Map();

  function find(x) {
    if (!parent.has(x)) {
      parent.set(x, x);
      rank.set(x, 0);
    }
    if (parent.get(x) !== x) {
      parent.set(x, find(parent.get(x)));
    }
    return parent.get(x);
  }

  function union(x, y) {
    const rootX = find(x);
    const rootY = find(y);
    if (rootX === rootY) return;
    const rankX = rank.get(rootX);
    const rankY = rank.get(rootY);
    if (rankX < rankY) {
      parent.set(rootX, rootY);
    } else if (rankX > rankY) {
      parent.set(rootY, rootX);
    } else {
      parent.set(rootY, rootX);
      rank.set(rootX, rankX + 1);
    }
  }

  function getClusters() {
    const clusters = new Map();
    for (const key of parent.keys()) {
      const root = find(key);
      if (!clusters.has(root)) clusters.set(root, []);
      clusters.get(root).push(key);
    }
    return [...clusters.values()];
  }

  return { find, union, getClusters };
}

// =============================================================================
// SQL Vectorized Similarity Query
// =============================================================================

const SIMILARITY_PAIRS_SQL = `
  WITH candidates AS (
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
  )
  SELECT a.id AS id_a, b.id AS id_b,
    (1 - (a.embedding <=> b.embedding))::float AS similarity
  FROM candidates a
  JOIN candidates b ON a.id < b.id
  WHERE (1 - (a.embedding <=> b.embedding)) > 0.6
`;

const CANDIDATE_COUNT_SQL = `
  SELECT t.id, t.content, t.thought_type, t.importance
  FROM thoughts t
  WHERE t.status = 'active'
    AND t.thought_type != 'reflection'
    AND NOT EXISTS (
      SELECT 1 FROM thought_relations r
      WHERE r.target_id = t.id AND r.relation_type = 'synthesized_from'
    )
  ORDER BY t.created_at DESC
  LIMIT $1
`;

// =============================================================================
// Consolidation Run
// =============================================================================

async function runConsolidation(pool, apiKey) {
  const client = await pool.connect();
  try {
    const brainConfig = await getBrainConfig(client);
    if (!brainConfig.brain_enabled) return;

    // First check if we have enough candidates
    const candidateResult = await client.query(CANDIDATE_COUNT_SQL, [brainConfig.consolidation_max_thoughts]);
    if (candidateResult.rows.length < brainConfig.consolidation_min_thoughts) {
      return;
    }

    // Get all similar pairs in a single query
    const pairsResult = await client.query(SIMILARITY_PAIRS_SQL, [brainConfig.consolidation_max_thoughts]);

    if (pairsResult.rows.length === 0) return;

    // Build clusters using union-find
    const uf = createUnionFind();
    for (const pair of pairsResult.rows) {
      uf.union(pair.id_a, pair.id_b);
    }

    // Map candidate data by ID for quick lookup
    const candidateMap = new Map();
    for (const row of candidateResult.rows) {
      candidateMap.set(row.id, row);
    }

    const clusters = uf.getClusters().filter(c => c.length >= 3);
    if (clusters.length === 0) return;

    for (const clusterIds of clusters) {
      const cluster = clusterIds.map(id => candidateMap.get(id)).filter(Boolean);
      if (cluster.length < 3) continue;
      await synthesizeCluster(client, cluster, apiKey);
    }
  } catch (err) {
    console.error("Consolidation error:", err.message);
  } finally {
    client.release();
  }
}

async function synthesizeCluster(client, cluster, apiKey) {
  try {
    const thoughtContents = cluster.map((t, i) => `${i + 1}. [${t.thought_type}] ${t.content}`).join("\n");

    const llmRes = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
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
      return;
    }

    const llmData = await llmRes.json();
    const synthesis = llmData.choices[0].message.content;
    if (!synthesis) return;

    const reflectionEmbedding = await getEmbedding(synthesis, apiKey);
    const maxImportance = Math.max(...cluster.map(t => t.importance ?? 0));
    const reflectionImportance = Math.min(1.0, maxImportance + 0.05);

    await client.query("BEGIN");
    const reflResult = await client.query(
      `INSERT INTO thoughts (content, embedding, thought_type, source_agent, source_phase, importance, scope)
       VALUES ($1, $2, 'reflection', 'eva', 'reconciliation', $3, ARRAY['default']::ltree[])
       RETURNING id`,
      [synthesis, pgvector.toSql(reflectionEmbedding), reflectionImportance]
    );
    const reflectionId = reflResult.rows[0].id;

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
  }
}

// =============================================================================
// Timer
// =============================================================================

let consolidationTimer = null;

async function startConsolidationTimer(pool, apiKey) {
  const brainConfig = await getBrainConfig(pool);
  const intervalMs = brainConfig.consolidation_interval_minutes * 60 * 1000;
  consolidationTimer = setInterval(() => runConsolidation(pool, apiKey), intervalMs);
  console.log(`Consolidation timer: every ${brainConfig.consolidation_interval_minutes} min`);
}

function stopConsolidationTimer() {
  if (consolidationTimer) {
    clearInterval(consolidationTimer);
    consolidationTimer = null;
  }
}

export { runConsolidation, startConsolidationTimer, stopConsolidationTimer };
