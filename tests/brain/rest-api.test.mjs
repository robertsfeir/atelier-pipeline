/**
 * Tests for brain/lib/rest-api.mjs
 * Test IDs: T-0003-103 through T-0003-112
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createMockPool } from './helpers/mock-pool.mjs';
import { createRestHandler } from '../../brain/lib/rest-api.mjs';
import { resetBrainConfigCache } from '../../brain/lib/conflict.mjs';

/**
 * Creates a mock HTTP request object.
 */
function createMockReq({ method = 'GET', url = '/', headers = {}, body = '' } = {}) {
  const listeners = {};
  return {
    method,
    url,
    headers: { host: 'localhost:8788', ...headers },
    on(event, handler) {
      listeners[event] = handler;
    },
    // Simulate body streaming
    _emit() {
      if (body && listeners.data) listeners.data(body);
      if (listeners.end) listeners.end();
    },
    destroy() {},
  };
}

/**
 * Creates a mock HTTP response object that captures output.
 */
function createMockRes() {
  let statusCode = 200;
  let headersWritten = {};
  let bodyData = '';

  return {
    writeHead(code, headers) {
      statusCode = code;
      Object.assign(headersWritten, headers);
    },
    end(data) {
      bodyData = data || '';
    },
    get statusCode() { return statusCode; },
    get headers() { return headersWritten; },
    get body() { return bodyData; },
    get json() {
      try { return JSON.parse(bodyData); } catch { return null; }
    },
  };
}

describe('rest-api.mjs', () => {
  let pool;

  beforeEach(() => {
    pool = createMockPool();
    resetBrainConfigCache();
  });

  afterEach(() => {
    resetBrainConfigCache();
  });

  describe('GET /api/health', () => {
    // T-0003-103: GET /api/health returns connected status
    it('T-0003-103: returns connected status with brain info', async () => {
      pool.setQueryResult('brain_config', {
        rows: [{
          brain_enabled: true,
          consolidation_interval_minutes: 30,
        }],
        rowCount: 1,
      });
      pool.setQueryResult("count(*)::int AS total", {
        rows: [{ total: 42 }],
        rowCount: 1,
      });
      pool.setQueryResult("thought_type = 'reflection'", {
        rows: [],
        rowCount: 0,
      });

      const cfg = { apiToken: null, brain_name: 'My Noodle', _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'GET', url: '/api/health' });
      const res = createMockRes();

      const handled = await handler(req, res);

      assert.strictEqual(handled, true);
      assert.strictEqual(res.statusCode, 200);
      const body = res.json;
      assert.strictEqual(body.connected, true);
      assert.strictEqual(body.brain_enabled, true);
      assert.strictEqual(body.brain_name, 'My Noodle');
      assert.strictEqual(body.thought_count, 42);
    });

    // Health is always public even with auth token set
    it('returns health without auth even when token is configured', async () => {
      pool.setQueryResult('brain_config', {
        rows: [{ brain_enabled: false, consolidation_interval_minutes: 30 }],
        rowCount: 1,
      });
      pool.setQueryResult("count(*)::int AS total", {
        rows: [{ total: 0 }],
        rowCount: 1,
      });
      pool.setQueryResult("thought_type = 'reflection'", { rows: [], rowCount: 0 });

      const cfg = { apiToken: 'secret-token', brain_name: 'Brain', _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'GET', url: '/api/health' });
      const res = createMockRes();

      await handler(req, res);
      assert.strictEqual(res.statusCode, 200);
    });
  });

  describe('GET /api/config', () => {
    // T-0003-104: GET /api/config returns brain config
    it('T-0003-104: returns brain configuration', async () => {
      const brainConfig = {
        id: 1,
        brain_enabled: true,
        consolidation_interval_minutes: 30,
        conflict_detection_enabled: true,
        conflict_duplicate_threshold: 0.9,
        conflict_candidate_threshold: 0.7,
      };
      pool.setQueryResult('brain_config', { rows: [brainConfig], rowCount: 1 });

      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'GET', url: '/api/config' });
      const res = createMockRes();

      const handled = await handler(req, res);

      assert.strictEqual(handled, true);
      assert.strictEqual(res.statusCode, 200);
      const body = res.json;
      assert.strictEqual(body.brain_enabled, true);
      assert.strictEqual(body.consolidation_interval_minutes, 30);
    });
  });

  describe('PUT /api/config', () => {
    // T-0003-105: PUT /api/config updates allowed fields
    it('T-0003-105: updates allowed config fields', async () => {
      pool.setQueryResult('UPDATE brain_config', { rows: [], rowCount: 1 });

      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const body = JSON.stringify({
        brain_enabled: false,
        consolidation_interval_minutes: 60,
      });
      const req = createMockReq({
        method: 'PUT',
        url: '/api/config',
        body,
      });
      const res = createMockRes();

      // Simulate body streaming
      const handlePromise = handler(req, res);
      req._emit();
      const handled = await handlePromise;

      assert.strictEqual(handled, true);
      assert.strictEqual(res.statusCode, 200);
      assert.deepStrictEqual(res.json, { updated: true });
    });

    // T-0003-106: PUT /api/config with invalid threshold (>1) returns 400
    it('T-0003-106: rejects threshold > 1 with 400', async () => {
      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const body = JSON.stringify({
        conflict_duplicate_threshold: 1.5,
      });
      const req = createMockReq({ method: 'PUT', url: '/api/config', body });
      const res = createMockRes();

      const handlePromise = handler(req, res);
      req._emit();
      await handlePromise;

      assert.strictEqual(res.statusCode, 400);
      assert.ok(res.json.error.includes('between 0 and 1'));
    });

    // T-0003-107: PUT /api/config with no valid fields returns 400
    it('T-0003-107: rejects config update with no valid fields', async () => {
      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const body = JSON.stringify({
        nonexistent_field: 'should be ignored',
      });
      const req = createMockReq({ method: 'PUT', url: '/api/config', body });
      const res = createMockRes();

      const handlePromise = handler(req, res);
      req._emit();
      await handlePromise;

      assert.strictEqual(res.statusCode, 400);
      assert.ok(res.json.error.includes('No valid fields'));
    });

    // Edge case: invalid JSON body returns 400
    it('rejects invalid JSON body with 400', async () => {
      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'PUT', url: '/api/config', body: 'not json {{{' });
      const res = createMockRes();

      const handlePromise = handler(req, res);
      req._emit();
      await handlePromise;

      assert.strictEqual(res.statusCode, 400);
      assert.ok(res.json.error.includes('Invalid JSON'));
    });
  });

  describe('GET /api/thought-types', () => {
    // T-0003-108: GET /api/thought-types returns all types
    it('T-0003-108: returns all thought type configurations', async () => {
      const types = [
        { thought_type: 'decision', default_ttl_days: null, default_importance: 0.9, description: 'Decisions' },
        { thought_type: 'lesson', default_ttl_days: 365, default_importance: 0.7, description: 'Lessons' },
      ];
      pool.setQueryResult('thought_type_config', { rows: types, rowCount: 2 });

      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'GET', url: '/api/thought-types' });
      const res = createMockRes();

      await handler(req, res);

      assert.strictEqual(res.statusCode, 200);
      const body = res.json;
      assert.ok(Array.isArray(body));
      assert.strictEqual(body.length, 2);
      assert.strictEqual(body[0].thought_type, 'decision');
    });
  });

  describe('PUT /api/thought-types/:type', () => {
    // T-0003-109: PUT /api/thought-types/:type updates TTL and importance
    it('T-0003-109: updates thought type TTL and importance', async () => {
      pool.setQueryResult('UPDATE thought_type_config', { rows: [], rowCount: 1 });

      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const body = JSON.stringify({ default_ttl_days: 180, default_importance: 0.8 });
      const req = createMockReq({ method: 'PUT', url: '/api/thought-types/lesson', body });
      const res = createMockRes();

      const handlePromise = handler(req, res);
      req._emit();
      await handlePromise;

      assert.strictEqual(res.statusCode, 200);
      assert.deepStrictEqual(res.json, { updated: true, type: 'lesson' });
    });

    // T-0003-110: PUT /api/thought-types/invalid returns 404
    it('T-0003-110: returns 404 for unknown thought type', async () => {
      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const body = JSON.stringify({ default_ttl_days: 90 });
      const req = createMockReq({ method: 'PUT', url: '/api/thought-types/nonexistent_type', body });
      const res = createMockRes();

      const handlePromise = handler(req, res);
      req._emit();
      await handlePromise;

      assert.strictEqual(res.statusCode, 404);
      assert.ok(res.json.error.includes('Unknown thought type'));
    });
  });

  describe('POST /api/purge-expired', () => {
    // T-0003-111: POST /api/purge-expired deletes expired thoughts and orphan relations
    it('T-0003-111: purges expired thoughts and orphan relations', async () => {
      pool.setQueryResult("DELETE FROM thoughts WHERE status = 'expired'", {
        rows: [{ id: 'a' }, { id: 'b' }],
        rowCount: 2,
      });
      pool.setQueryResult('DELETE FROM thought_relations', {
        rows: [{ id: 'c' }],
        rowCount: 1,
      });

      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'POST', url: '/api/purge-expired' });
      const res = createMockRes();

      await handler(req, res);

      assert.strictEqual(res.statusCode, 200);
      const body = res.json;
      assert.strictEqual(body.purged_thoughts, 2);
      assert.strictEqual(body.purged_relations, 1);
    });
  });

  describe('GET /api/stats', () => {
    // T-0003-112: GET /api/stats returns breakdown by type, status, agent
    it('T-0003-112: returns stats breakdown', async () => {
      pool.setQueryResult('thought_type, count', {
        rows: [{ thought_type: 'decision', count: 5 }, { thought_type: 'lesson', count: 3 }],
        rowCount: 2,
      });
      pool.setQueryResult('status, count', {
        rows: [{ status: 'active', count: 7 }, { status: 'expired', count: 1 }],
        rowCount: 2,
      });
      pool.setQueryResult('source_agent, count', {
        rows: [{ source_agent: 'eva', count: 4 }],
        rowCount: 1,
      });
      pool.setQueryResult('captured_by, count', {
        rows: [{ captured_by: 'User', count: 8 }],
        rowCount: 1,
      });

      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'GET', url: '/api/stats' });
      const res = createMockRes();

      await handler(req, res);

      assert.strictEqual(res.statusCode, 200);
      const body = res.json;
      assert.ok(body.by_type);
      assert.ok(body.by_status);
      assert.ok(body.by_agent);
      assert.ok(body.by_human);
      assert.strictEqual(body.by_type.decision, 5);
      assert.strictEqual(body.by_status.active, 7);
    });
  });

  describe('auth middleware', () => {
    it('returns 401 when token required but not provided', async () => {
      pool.setQueryResult('brain_config', { rows: [{ brain_enabled: true }], rowCount: 1 });

      const cfg = { apiToken: 'secret-123', _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'GET', url: '/api/config' });
      const res = createMockRes();

      await handler(req, res);

      assert.strictEqual(res.statusCode, 401);
      assert.deepStrictEqual(res.json, { error: 'Unauthorized' });
    });

    it('returns 401 with wrong token', async () => {
      const cfg = { apiToken: 'correct-token', _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({
        method: 'GET',
        url: '/api/config',
        headers: { authorization: 'Bearer wrong-token' },
      });
      const res = createMockRes();

      await handler(req, res);

      assert.strictEqual(res.statusCode, 401);
    });

    it('allows access with correct Bearer token', async () => {
      pool.setQueryResult('brain_config', {
        rows: [{ brain_enabled: true, consolidation_interval_minutes: 30 }],
        rowCount: 1,
      });

      const cfg = { apiToken: 'correct-token', _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({
        method: 'GET',
        url: '/api/config',
        headers: { authorization: 'Bearer correct-token' },
      });
      const res = createMockRes();

      await handler(req, res);

      assert.strictEqual(res.statusCode, 200);
    });

    it('allows all routes when no token configured', async () => {
      pool.setQueryResult('brain_config', {
        rows: [{ brain_enabled: false, consolidation_interval_minutes: 30 }],
        rowCount: 1,
      });

      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'GET', url: '/api/config' });
      const res = createMockRes();

      await handler(req, res);

      assert.strictEqual(res.statusCode, 200);
    });
  });

  describe('unmatched routes', () => {
    it('returns false for non-API paths', async () => {
      const cfg = { apiToken: null, _source: 'env' };
      const handler = createRestHandler(pool, cfg);

      const req = createMockReq({ method: 'GET', url: '/unknown-path' });
      const res = createMockRes();

      const handled = await handler(req, res);
      assert.strictEqual(handled, false);
    });
  });
});
