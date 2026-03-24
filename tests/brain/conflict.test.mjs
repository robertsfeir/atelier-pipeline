/**
 * Tests for brain/lib/conflict.mjs
 * Test IDs: T-0003-079 through T-0003-086
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createMockPool } from './helpers/mock-pool.mjs';
import {
  createEmbeddingResponse,
  createConflictClassificationResponse,
  createMockFetch,
} from './helpers/mock-fetch.mjs';
import {
  detectConflicts,
  getBrainConfig,
  resetBrainConfigCache,
  classifyConflict,
} from '../../brain/lib/conflict.mjs';

describe('conflict.mjs', () => {
  let originalFetch;
  let pool;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
    pool = createMockPool();
    resetBrainConfigCache();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    resetBrainConfigCache();
  });

  describe('detectConflicts()', () => {
    const fakeEmbedding = new Array(1536).fill(0.1);
    const defaultBrainConfig = {
      conflict_detection_enabled: true,
      conflict_duplicate_threshold: 0.9,
      conflict_candidate_threshold: 0.7,
      conflict_llm_enabled: true,
    };

    // T-0003-079: detectConflicts() with no similar thoughts returns { action: "store" }
    it('T-0003-079: returns { action: "store" } when no similar thoughts found', async () => {
      const client = await pool.connect();
      pool.setQueryResult('match_thoughts_scored', { rows: [], rowCount: 0 });

      const result = await detectConflicts(
        client, fakeEmbedding, 'new content', ['default'],
        defaultBrainConfig, 'api-key'
      );

      assert.deepStrictEqual(result, { action: 'store' });
    });

    // T-0003-080: detectConflicts() with similarity > 0.9 returns { action: "merge" }
    it('T-0003-080: returns { action: "merge" } when similarity > 0.9', async () => {
      const client = await pool.connect();
      const existingId = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

      pool.setQueryResult('match_thoughts_scored', {
        rows: [{ id: existingId, content: 'existing', scope: ['default'], source_agent: 'eva' }],
        rowCount: 1,
      });
      // Similarity query returns > 0.9
      pool.setQueryResult('embedding <=>', {
        rows: [{ sim: 0.95 }],
        rowCount: 1,
      });

      const result = await detectConflicts(
        client, fakeEmbedding, 'similar content', ['default'],
        defaultBrainConfig, 'api-key'
      );

      assert.strictEqual(result.action, 'merge');
      assert.strictEqual(result.existingId, existingId);
      assert.strictEqual(result.similarity, 0.95);
    });

    // T-0003-081: detectConflicts() with similarity 0.7-0.9 and LLM returning DUPLICATE returns { action: "merge" }
    it('T-0003-081: returns { action: "merge" } when LLM classifies as DUPLICATE', async () => {
      const client = await pool.connect();
      const existingId = 'aaaaaaaa-bbbb-cccc-dddd-ffffffffffff';

      pool.setQueryResult('match_thoughts_scored', {
        rows: [{ id: existingId, content: 'existing', scope: ['default'], source_agent: 'eva' }],
        rowCount: 1,
      });
      pool.setQueryResult('embedding <=>', {
        rows: [{ sim: 0.8 }],
        rowCount: 1,
      });

      globalThis.fetch = createMockFetch({
        'chat/completions': {
          status: 200,
          body: createConflictClassificationResponse('DUPLICATE', 0.95, 'These are the same'),
        },
      });

      const result = await detectConflicts(
        client, fakeEmbedding, 'similar content', ['default'],
        defaultBrainConfig, 'api-key'
      );

      assert.strictEqual(result.action, 'merge');
      assert.strictEqual(result.existingId, existingId);
    });

    // T-0003-082: detectConflicts() with LLM returning CONTRADICTION (same scope) returns { action: "supersede" }
    it('T-0003-082: returns { action: "supersede" } on CONTRADICTION with same scope', async () => {
      const client = await pool.connect();
      const existingId = 'aaaaaaaa-bbbb-cccc-dddd-111111111111';
      const scope = ['project.payments'];

      pool.setQueryResult('match_thoughts_scored', {
        rows: [{ id: existingId, content: 'old decision', scope: scope, source_agent: 'cal' }],
        rowCount: 1,
      });
      pool.setQueryResult('embedding <=>', {
        rows: [{ sim: 0.75 }],
        rowCount: 1,
      });

      globalThis.fetch = createMockFetch({
        'chat/completions': {
          status: 200,
          body: createConflictClassificationResponse('CONTRADICTION', 0.9, 'Contradictory decisions'),
        },
      });

      const result = await detectConflicts(
        client, fakeEmbedding, 'new contradicting decision', scope,
        defaultBrainConfig, 'api-key'
      );

      assert.strictEqual(result.action, 'supersede');
      assert.strictEqual(result.existingId, existingId);
      assert.ok(result.classification);
    });

    // T-0003-083: detectConflicts() with LLM returning CONTRADICTION (different scope) returns { action: "conflict" }
    it('T-0003-083: returns { action: "conflict" } on CONTRADICTION with different scope', async () => {
      const client = await pool.connect();
      const existingId = 'aaaaaaaa-bbbb-cccc-dddd-222222222222';

      pool.setQueryResult('match_thoughts_scored', {
        rows: [{ id: existingId, content: 'other decision', scope: ['project.auth'], source_agent: 'cal' }],
        rowCount: 1,
      });
      pool.setQueryResult('embedding <=>', {
        rows: [{ sim: 0.75 }],
        rowCount: 1,
      });

      globalThis.fetch = createMockFetch({
        'chat/completions': {
          status: 200,
          body: createConflictClassificationResponse('CONTRADICTION', 0.85, 'Cross-scope conflict'),
        },
      });

      const result = await detectConflicts(
        client, fakeEmbedding, 'contradicting in different scope', ['project.payments'],
        defaultBrainConfig, 'api-key'
      );

      assert.strictEqual(result.action, 'conflict');
      assert.strictEqual(result.existingId, existingId);
    });

    // T-0003-084: detectConflicts() with LLM failure returns { action: "store", warning: "..." }
    it('T-0003-084: returns { action: "store", warning } when LLM fails', async () => {
      const client = await pool.connect();
      const existingId = 'aaaaaaaa-bbbb-cccc-dddd-333333333333';

      pool.setQueryResult('match_thoughts_scored', {
        rows: [{ id: existingId, content: 'existing', scope: ['default'], source_agent: 'eva' }],
        rowCount: 1,
      });
      pool.setQueryResult('embedding <=>', {
        rows: [{ sim: 0.8 }],
        rowCount: 1,
      });

      globalThis.fetch = createMockFetch({
        'chat/completions': { status: 500, body: 'Internal Server Error' },
      });

      const result = await detectConflicts(
        client, fakeEmbedding, 'new content', ['default'],
        defaultBrainConfig, 'api-key'
      );

      assert.strictEqual(result.action, 'store');
      assert.ok(result.warning, 'Should include a warning about failed classification');
    });

    // T-0003-085: detectConflicts() with conflict_detection_enabled=false returns { action: "store" }
    it('T-0003-085: returns { action: "store" } when conflict detection disabled', async () => {
      const client = await pool.connect();
      const disabledConfig = { ...defaultBrainConfig, conflict_detection_enabled: false };

      const result = await detectConflicts(
        client, fakeEmbedding, 'any content', ['default'],
        disabledConfig, 'api-key'
      );

      assert.deepStrictEqual(result, { action: 'store' });
    });

    // Edge case: LLM not enabled stores with conflictFlag
    it('stores with conflictFlag when LLM classification disabled', async () => {
      const client = await pool.connect();
      const existingId = 'aaaaaaaa-bbbb-cccc-dddd-444444444444';

      pool.setQueryResult('match_thoughts_scored', {
        rows: [{ id: existingId, content: 'existing', scope: ['default'], source_agent: 'eva' }],
        rowCount: 1,
      });
      pool.setQueryResult('embedding <=>', {
        rows: [{ sim: 0.8 }],
        rowCount: 1,
      });

      const noLlmConfig = { ...defaultBrainConfig, conflict_llm_enabled: false };

      const result = await detectConflicts(
        client, fakeEmbedding, 'candidate content', ['default'],
        noLlmConfig, 'api-key'
      );

      assert.strictEqual(result.action, 'store');
      assert.strictEqual(result.conflictFlag, true);
      assert.strictEqual(result.candidateId, existingId);
    });
  });

  describe('getBrainConfig()', () => {
    // T-0003-086: getBrainConfig() caches result for 10 seconds
    it('T-0003-086: caches result and does not re-query within 10 seconds', async () => {
      const configRow = {
        id: 1,
        brain_enabled: true,
        consolidation_interval_minutes: 30,
        conflict_detection_enabled: true,
      };
      pool.setQueryResult('brain_config', { rows: [configRow], rowCount: 1 });

      // First call
      const result1 = await getBrainConfig(pool);
      assert.deepStrictEqual(result1, configRow);

      const queryCountAfterFirst = pool.queries.length;

      // Second call within cache window
      const result2 = await getBrainConfig(pool);
      assert.deepStrictEqual(result2, configRow);
      assert.strictEqual(pool.queries.length, queryCountAfterFirst,
        'Should not issue another query within cache window');
    });

    // Edge case: cache resets on resetBrainConfigCache()
    it('resetBrainConfigCache() forces re-query', async () => {
      const configRow = { id: 1, brain_enabled: false };
      pool.setQueryResult('brain_config', { rows: [configRow], rowCount: 1 });

      await getBrainConfig(pool);
      const queryCountFirst = pool.queries.length;

      resetBrainConfigCache();

      await getBrainConfig(pool);
      assert.ok(pool.queries.length > queryCountFirst,
        'Should issue new query after cache reset');
    });
  });

  describe('classifyConflict()', () => {
    it('returns classification object on success', async () => {
      globalThis.fetch = createMockFetch({
        'chat/completions': {
          status: 200,
          body: createConflictClassificationResponse('NOVEL', 0.8, 'Different topics'),
        },
      });

      const result = await classifyConflict('thought A', 'thought B', 'api-key');

      assert.ok(result);
      assert.strictEqual(result.classification, 'NOVEL');
      assert.strictEqual(result.confidence, 0.8);
    });

    it('returns null on LLM failure', async () => {
      globalThis.fetch = createMockFetch({
        'chat/completions': { status: 500, body: 'Server error' },
      });

      const result = await classifyConflict('thought A', 'thought B', 'api-key');

      assert.strictEqual(result, null);
    });
  });
});
