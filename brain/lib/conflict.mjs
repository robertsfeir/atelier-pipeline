/**
 * Conflict detection and brain config cache.
 * Depends on: db.mjs (pool passed as parameter), embed.mjs (indirectly, caller provides embedding).
 */

import pgvector from "pgvector/pg";
import { assertLlmContent } from "./llm-response.mjs";

// =============================================================================
// Brain Config Cache
// =============================================================================

let brainConfigCache = null;
let brainConfigCacheTime = 0;

async function getBrainConfig(clientOrPool) {
  const now = Date.now();
  if (brainConfigCache && now - brainConfigCacheTime < 10000) return brainConfigCache;
  const result = await clientOrPool.query("SELECT * FROM brain_config WHERE id = 1");
  brainConfigCache = result.rows[0];
  brainConfigCacheTime = now;
  return brainConfigCache;
}

function resetBrainConfigCache() {
  brainConfigCache = null;
  brainConfigCacheTime = 0;
}

// =============================================================================
// LLM-Based Conflict Classification
// =============================================================================

async function classifyConflict(thoughtA, thoughtB, apiKey) {
  try {
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
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
    return JSON.parse(assertLlmContent(data, 'conflict'));
  } catch (err) {
    console.error("Conflict classification failed:", err.message);
    return null;
  }
}

// =============================================================================
// Conflict Detection
// =============================================================================

async function detectConflicts(client, embedding, content, scope, brainConfig, apiKey) {
  if (!brainConfig.conflict_detection_enabled) return { action: "store" };

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

  // Tier 2: Candidate (0.7-0.9) -- LLM classifies if enabled
  if (similarity > brainConfig.conflict_candidate_threshold) {
    if (!brainConfig.conflict_llm_enabled) {
      return { action: "store", conflictFlag: true, candidateId: topMatch.id, similarity };
    }

    const classification = await classifyConflict(topMatch.content, content, apiKey);
    if (!classification) {
      return { action: "store", warning: "Conflict classification failed" };
    }

    return handleClassification(classification, topMatch, scope);
  }

  // Tier 3: Novel (<0.7)
  return { action: "store" };
}

function handleClassification(classification, topMatch, scope) {
  switch (classification.classification) {
    case "DUPLICATE":
      return { action: "merge", existingId: topMatch.id, similarity: 0 };
    case "CONTRADICTION": {
      const sameScope = topMatch.scope?.some(s => scope?.includes(s));
      if (sameScope) {
        return { action: "supersede", existingId: topMatch.id, classification };
      }
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

export { classifyConflict, detectConflicts, getBrainConfig, resetBrainConfigCache };
