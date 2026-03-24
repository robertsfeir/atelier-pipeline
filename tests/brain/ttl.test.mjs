/**
 * Tests for brain/lib/ttl.mjs
 * Test IDs: T-0003-119 through T-0003-120
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createMockPool } from './helpers/mock-pool.mjs';
import { runTTLEnforcement, startTTLTimer, stopTTLTimer } from '../../brain/lib/ttl.mjs';

describe('ttl.mjs', () => {
  let pool;

  beforeEach(() => {
    pool = createMockPool();
    stopTTLTimer();
  });

  afterEach(() => {
    stopTTLTimer();
  });

  // T-0003-119: runTTLEnforcement() expires thoughts past their type's TTL
  it('T-0003-119: expires thoughts past their TTL', async () => {
    // Simulate 3 thoughts being expired
    pool.setQueryResult('UPDATE thoughts t', {
      rows: [{ id: 'a' }, { id: 'b' }, { id: 'c' }],
      rowCount: 3,
    });

    await runTTLEnforcement(pool);

    // Verify the UPDATE query was executed
    const updateQueries = pool.queries.filter(q =>
      q.sql.includes('UPDATE thoughts') && q.sql.includes('expired')
    );
    assert.ok(updateQueries.length >= 1, 'Should execute TTL expiration query');

    // Verify the query joins with thought_type_config for TTL
    const ttlQuery = updateQueries[0].sql;
    assert.ok(ttlQuery.includes('thought_type_config'), 'Should join with thought_type_config');
    assert.ok(ttlQuery.includes('default_ttl_days'), 'Should reference default_ttl_days');
  });

  // T-0003-120: runTTLEnforcement() does not expire thoughts with NULL TTL
  it('T-0003-120: does not expire thoughts with NULL TTL (decisions, preferences)', async () => {
    pool.setQueryResult('UPDATE thoughts t', { rows: [], rowCount: 0 });

    await runTTLEnforcement(pool);

    // Verify the query has the NULL check
    const updateQueries = pool.queries.filter(q =>
      q.sql.includes('UPDATE thoughts') && q.sql.includes('expired')
    );
    assert.ok(updateQueries.length >= 1);
    const sql = updateQueries[0].sql;
    assert.ok(sql.includes('IS NOT NULL'), 'Should check that ttl_days IS NOT NULL, excluding decisions and preferences');
  });

  // Edge case: handles query errors gracefully
  it('handles query errors without throwing', async () => {
    pool.setQueryResult('UPDATE thoughts t', new Error('Connection lost'));

    // Should not throw
    await runTTLEnforcement(pool);
  });

  describe('timer management', () => {
    it('stopTTLTimer is safe to call when no timer running', () => {
      stopTTLTimer();
      stopTTLTimer();
    });
  });
});
