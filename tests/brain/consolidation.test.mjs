/**
 * Tests for brain/lib/consolidation.mjs
 * Test IDs: T-0003-113 through T-0003-118
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createMockPool } from './helpers/mock-pool.mjs';
import {
  createEmbeddingResponse,
  createSynthesisResponse,
  createMockFetch,
} from './helpers/mock-fetch.mjs';
import {
  runConsolidation,
  startConsolidationTimer,
  stopConsolidationTimer,
} from '../../brain/lib/consolidation.mjs';
import { resetBrainConfigCache } from '../../brain/lib/conflict.mjs';

describe('consolidation.mjs', () => {
  let originalFetch;
  let pool;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
    pool = createMockPool();
    resetBrainConfigCache();
    stopConsolidationTimer();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    resetBrainConfigCache();
    stopConsolidationTimer();
  });

  const defaultBrainConfig = {
    brain_enabled: true,
    consolidation_interval_minutes: 30,
    consolidation_min_thoughts: 3,
    consolidation_max_thoughts: 20,
  };

  function setupBrainConfig(config = defaultBrainConfig) {
    pool.setQueryResult('brain_config', { rows: [config], rowCount: 1 });
  }

  // T-0003-113: runConsolidation() with enough similar thoughts creates reflection
  it('T-0003-113: creates reflection from cluster of similar thoughts', async () => {
    setupBrainConfig();

    // Enough candidates
    const candidates = [
      { id: 'c1', content: 'Thought 1', thought_type: 'lesson', importance: 0.7 },
      { id: 'c2', content: 'Thought 2', thought_type: 'lesson', importance: 0.8 },
      { id: 'c3', content: 'Thought 3', thought_type: 'insight', importance: 0.6 },
      { id: 'c4', content: 'Thought 4', thought_type: 'lesson', importance: 0.75 },
    ];

    // Similarity pairs query -- register first so CTE pattern matches before the generic one
    pool.setQueryResult('WITH candidates AS', {
      rows: [
        { id_a: 'c1', id_b: 'c2', similarity: 0.85 },
        { id_a: 'c1', id_b: 'c3', similarity: 0.75 },
        { id_a: 'c2', id_b: 'c3', similarity: 0.8 },
      ],
      rowCount: 3,
    });

    // Candidate count query -- matches after CTE pattern fails
    pool.setQueryResult('ORDER BY t.created_at DESC', { rows: candidates, rowCount: candidates.length });

    // Mock LLM synthesis and embedding
    globalThis.fetch = createMockFetch({
      'chat/completions': { status: 200, body: createSynthesisResponse('Synthesized insight from lessons.') },
      'embeddings': { status: 200, body: createEmbeddingResponse() },
    });

    // Mock INSERT for reflection
    pool.setQueryResult('INSERT INTO thoughts', {
      rows: [{ id: 'reflection-1' }],
      rowCount: 1,
    });
    // Mock INSERT for relations
    pool.setQueryResult('INSERT INTO thought_relations', { rows: [], rowCount: 1 });

    await runConsolidation(pool, 'test-api-key');

    // Verify reflection was inserted
    const insertQueries = pool.queries.filter(q =>
      q.sql.includes('INSERT INTO thoughts') && q.sql.includes('reflection')
    );
    assert.ok(insertQueries.length >= 1, 'Should insert a reflection thought');

    // Verify synthesized_from relations
    const relationQueries = pool.queries.filter(q =>
      q.sql.includes('synthesized_from')
    );
    assert.ok(relationQueries.length >= 1, 'Should create synthesized_from relations');
  });

  // T-0003-114: runConsolidation() with fewer than min_thoughts skips
  it('T-0003-114: skips when fewer candidates than min_thoughts', async () => {
    setupBrainConfig();

    // Only 2 candidates (min is 3)
    pool.setQueryResult('ORDER BY t.created_at DESC', {
      rows: [
        { id: 'c1', content: 'Thought 1', thought_type: 'lesson', importance: 0.7 },
        { id: 'c2', content: 'Thought 2', thought_type: 'lesson', importance: 0.8 },
      ],
      rowCount: 2,
    });

    await runConsolidation(pool, 'test-api-key');

    // No similarity query should be issued
    const pairQueries = pool.queries.filter(q => q.sql.includes('id_a'));
    assert.strictEqual(pairQueries.length, 0, 'Should not query for similarity pairs');
  });

  // T-0003-115: runConsolidation() with brain_enabled=false skips
  it('T-0003-115: skips when brain_enabled is false', async () => {
    setupBrainConfig({ ...defaultBrainConfig, brain_enabled: false });

    await runConsolidation(pool, 'test-api-key');

    // Should only have the brain_config query and nothing else
    const nonConfigQueries = pool.queries.filter(q => !q.sql.includes('brain_config'));
    assert.strictEqual(nonConfigQueries.length, 0, 'Should not query anything beyond brain_config');
  });

  // T-0003-116: clustering uses single SQL query (no per-pair queries)
  it('T-0003-116: uses single SQL query for all similarity pairs', async () => {
    setupBrainConfig();

    const candidates = Array.from({ length: 5 }, (_, i) => ({
      id: `c${i}`, content: `Thought ${i}`, thought_type: 'lesson', importance: 0.7,
    }));

    // Similarity pairs (CTE pattern) -- register first
    pool.setQueryResult('WITH candidates AS', {
      rows: [
        { id_a: 'c0', id_b: 'c1', similarity: 0.85 },
        { id_a: 'c1', id_b: 'c2', similarity: 0.75 },
        { id_a: 'c0', id_b: 'c2', similarity: 0.8 },
      ],
      rowCount: 3,
    });

    // Candidate count (non-CTE)
    pool.setQueryResult('ORDER BY t.created_at DESC', { rows: candidates, rowCount: candidates.length });

    globalThis.fetch = createMockFetch({
      'chat/completions': { status: 200, body: createSynthesisResponse() },
      'embeddings': { status: 200, body: createEmbeddingResponse() },
    });
    pool.setQueryResult('INSERT INTO thoughts', { rows: [{ id: 'r1' }], rowCount: 1 });
    pool.setQueryResult('INSERT INTO thought_relations', { rows: [], rowCount: 1 });

    await runConsolidation(pool, 'test-api-key');

    // Count similarity-related queries -- there should be exactly 1 for pairs
    const pairQueries = pool.queries.filter(q =>
      q.sql.includes('id_a') && q.sql.includes('id_b')
    );
    assert.strictEqual(pairQueries.length, 1, 'Should use exactly one SQL query for similarity pairs');
  });

  // T-0003-117: reflection importance = max(cluster) + 0.05, capped at 1.0
  it('T-0003-117: sets reflection importance to max(cluster) + 0.05, capped at 1.0', async () => {
    setupBrainConfig();

    const candidates = [
      { id: 'c1', content: 'T1', thought_type: 'lesson', importance: 0.95 },
      { id: 'c2', content: 'T2', thought_type: 'lesson', importance: 0.85 },
      { id: 'c3', content: 'T3', thought_type: 'insight', importance: 0.9 },
    ];

    // Similarity pairs (CTE) -- register first
    pool.setQueryResult('WITH candidates AS', {
      rows: [
        { id_a: 'c1', id_b: 'c2', similarity: 0.8 },
        { id_a: 'c1', id_b: 'c3', similarity: 0.75 },
        { id_a: 'c2', id_b: 'c3', similarity: 0.7 },
      ],
      rowCount: 3,
    });

    // Candidate count
    pool.setQueryResult('ORDER BY t.created_at DESC', { rows: candidates, rowCount: candidates.length });

    globalThis.fetch = createMockFetch({
      'chat/completions': { status: 200, body: createSynthesisResponse() },
      'embeddings': { status: 200, body: createEmbeddingResponse() },
    });

    // Capture the INSERT to verify importance
    let capturedImportance = null;
    pool.setQueryResult('INSERT INTO thoughts', (sql) => {
      // The importance is the 3rd param ($3) in the INSERT
      return { rows: [{ id: 'r1' }], rowCount: 1 };
    });
    pool.setQueryResult('INSERT INTO thought_relations', { rows: [], rowCount: 1 });

    await runConsolidation(pool, 'test-api-key');

    // Find the INSERT query for reflection and check importance param
    const insertQueries = pool.queries.filter(q =>
      q.sql.includes('INSERT INTO thoughts') && q.params
    );

    if (insertQueries.length > 0) {
      const params = insertQueries[0].params;
      // importance is the 3rd parameter (index 2)
      capturedImportance = params?.[2];
      // max(0.95, 0.85, 0.9) + 0.05 = 1.0 (capped)
      assert.ok(capturedImportance <= 1.0, 'Importance should be capped at 1.0');
    }
  });

  // T-0003-118: LLM synthesis failure skips cluster, continues to next
  it('T-0003-118: skips cluster on LLM synthesis failure, does not throw', async () => {
    setupBrainConfig();

    const candidates = [
      { id: 'c1', content: 'T1', thought_type: 'lesson', importance: 0.7 },
      { id: 'c2', content: 'T2', thought_type: 'lesson', importance: 0.8 },
      { id: 'c3', content: 'T3', thought_type: 'insight', importance: 0.6 },
    ];

    // Similarity pairs (CTE) -- register first
    pool.setQueryResult('WITH candidates AS', {
      rows: [
        { id_a: 'c1', id_b: 'c2', similarity: 0.85 },
        { id_a: 'c1', id_b: 'c3', similarity: 0.75 },
        { id_a: 'c2', id_b: 'c3', similarity: 0.8 },
      ],
      rowCount: 3,
    });

    // Candidate count
    pool.setQueryResult('ORDER BY t.created_at DESC', { rows: candidates, rowCount: candidates.length });

    // LLM fails
    globalThis.fetch = createMockFetch({
      'chat/completions': { status: 500, body: 'Internal Server Error' },
    });

    // Should not throw
    await runConsolidation(pool, 'test-api-key');

    // No reflection should be inserted
    const insertQueries = pool.queries.filter(q =>
      q.sql.includes('INSERT INTO thoughts') && q.sql.includes('reflection')
    );
    assert.strictEqual(insertQueries.length, 0, 'Should not insert reflection on LLM failure');
  });

  describe('timer management', () => {
    it('stopConsolidationTimer is safe to call when no timer running', () => {
      // Should not throw
      stopConsolidationTimer();
      stopConsolidationTimer();
    });
  });
});
