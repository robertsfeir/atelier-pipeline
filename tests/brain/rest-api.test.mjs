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

// =============================================================================
// ADR-0034 Wave 3 Step 3.2 — CORS wildcard override removal (T-0034-049, T-0034-050)
//
// These tests define correct behavior BEFORE Colby builds Step 3.2.
// They are expected to FAIL until Colby removes the 4 per-handler
// "Access-Control-Allow-Origin": "*" overrides from rest-api.mjs.
//
// After the fix, all CORS headers must originate from the server-level
// middleware in server.mjs (line 114), not from individual handlers.
//
// T-0034-049: grep-level assertion — zero wildcard CORS matches in rest-api.mjs
// T-0034-050: runtime assertion — each of the 4 formerly-wildcarded handlers
//             does NOT return "Access-Control-Allow-Origin: *"
// =============================================================================

// T-0034-049: grep-level — no Access-Control-Allow-Origin in rest-api.mjs
// (structural/file-content assertion)
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REST_API_SOURCE = readFileSync(
  join(__dirname, '../../brain/lib/rest-api.mjs'),
  'utf8'
);

describe('ADR-0034 T-0034-049: CORS wildcard removal — file content', () => {
  // T-0034-049: zero Access-Control-Allow-Origin occurrences in rest-api.mjs
  it('T-0034-049: rest-api.mjs contains no Access-Control-Allow-Origin header', () => {
    // After Step 3.2, all CORS is handled by server.mjs server-level middleware.
    // Individual handlers must not set this header at all.
    const matches = REST_API_SOURCE.match(/Access-Control-Allow-Origin/g);
    assert.strictEqual(
      matches,
      null,
      `rest-api.mjs still contains ${matches ? matches.length : 0} Access-Control-Allow-Origin ` +
      `occurrence(s). ADR-0034 Step 3.2 requires removing all per-handler CORS overrides. ` +
      `CORS must be set only at the server.mjs level (server.mjs:114).`
    );
  });
});

describe('ADR-0034 T-0034-050: CORS behavior — formerly-wildcarded handlers', () => {
  // These tests verify that after the fix each of the 4 telemetry handlers
  // does NOT return "Access-Control-Allow-Origin: *" in its response.
  // The server-level CORS in server.mjs sets the origin to the request host,
  // e.g. "http://localhost:8788". The handlers themselves set no CORS at all.

  let pool;

  beforeEach(() => {
    pool = createMockPool();
    resetBrainConfigCache();
  });

  afterEach(() => {
    resetBrainConfigCache();
  });

  // Helper: assert no wildcard CORS on a response
  function assertNoWildcardCors(res, handlerName) {
    const corsHeader = res.headers['Access-Control-Allow-Origin'];
    assert.strictEqual(
      corsHeader,
      undefined,
      `${handlerName} set "Access-Control-Allow-Origin: ${corsHeader}". ` +
      `ADR-0034 Step 3.2: per-handler CORS overrides must be removed entirely. ` +
      `CORS is the sole responsibility of server.mjs middleware, not individual handlers.`
    );
  }

  // T-0034-050a: GET /api/telemetry/scopes — no wildcard CORS
  it('T-0034-050a: handleTelemetryScopes does not set Access-Control-Allow-Origin: *', async () => {
    pool.setQueryResult("source_phase = 'telemetry'", {
      rows: [{ scope: 'project.atelier' }],
      rowCount: 1,
    });

    const cfg = { apiToken: null, _source: 'env' };
    const handler = createRestHandler(pool, cfg);

    const req = createMockReq({ method: 'GET', url: '/api/telemetry/scopes' });
    const res = createMockRes();

    await handler(req, res);

    assert.strictEqual(res.statusCode, 200,
      'handleTelemetryScopes should return 200');
    assertNoWildcardCors(res, 'handleTelemetryScopes (/api/telemetry/scopes)');
  });

  // T-0034-050b: GET /api/telemetry/summary — no wildcard CORS
  it('T-0034-050b: handleTelemetrySummary does not set Access-Control-Allow-Origin: *', async () => {
    pool.setQueryResult("telemetry_tier' = '3'", {
      rows: [{ content: 'summary content', metadata: {}, created_at: new Date() }],
      rowCount: 1,
    });

    const cfg = { apiToken: null, _source: 'env' };
    const handler = createRestHandler(pool, cfg);

    const req = createMockReq({ method: 'GET', url: '/api/telemetry/summary' });
    const res = createMockRes();

    await handler(req, res);

    assert.strictEqual(res.statusCode, 200,
      'handleTelemetrySummary should return 200');
    assertNoWildcardCors(res, 'handleTelemetrySummary (/api/telemetry/summary)');
  });

  // T-0034-050c: GET /api/telemetry/agents — no wildcard CORS
  it('T-0034-050c: handleTelemetryAgents does not set Access-Control-Allow-Origin: *', async () => {
    pool.setQueryResult("telemetry_tier' = '1'", {
      rows: [{ agent: 'colby', invocations: 5, avg_duration_ms: 1000, total_cost: '0.0500', avg_input_tokens: 1000, avg_output_tokens: 500 }],
      rowCount: 1,
    });
    pool.setQueryResult("telemetry_tier' = '3'", {
      rows: [{ rework_rate: '0.10', first_pass_qa_rate: '0.90' }],
      rowCount: 1,
    });

    const cfg = { apiToken: null, _source: 'env' };
    const handler = createRestHandler(pool, cfg);

    const req = createMockReq({ method: 'GET', url: '/api/telemetry/agents' });
    const res = createMockRes();

    await handler(req, res);

    assert.strictEqual(res.statusCode, 200,
      'handleTelemetryAgents should return 200');
    assertNoWildcardCors(res, 'handleTelemetryAgents (/api/telemetry/agents)');
  });

  // T-0034-050d: GET /api/telemetry/agent-detail?name=colby — no wildcard CORS
  it('T-0034-050d: handleTelemetryAgentDetail does not set Access-Control-Allow-Origin: *', async () => {
    pool.setQueryResult("agent_name' = $1", {
      rows: [{
        description: 'Build feature X',
        duration_ms: 5000,
        cost_usd: '0.0250',
        input_tokens: 2000,
        output_tokens: 800,
        model: 'claude-sonnet-4-6',
        created_at: new Date(),
      }],
      rowCount: 1,
    });

    const cfg = { apiToken: null, _source: 'env' };
    const handler = createRestHandler(pool, cfg);

    const req = createMockReq({ method: 'GET', url: '/api/telemetry/agent-detail?name=colby' });
    const res = createMockRes();

    await handler(req, res);

    assert.strictEqual(res.statusCode, 200,
      'handleTelemetryAgentDetail should return 200');
    assertNoWildcardCors(res, 'handleTelemetryAgentDetail (/api/telemetry/agent-detail)');
  });
});

// =============================================================================
// Quality query numeric cast guard (rework_rate / first_pass_qa_rate)
//
// Historical T3 brain captures store non-numeric strings like "low" and
// "1.0 cycles/unit" in metadata->>'rework_rate' / metadata->>'first_pass_qa_rate'.
// Bare ::numeric casts crash the entire /api/telemetry/agents endpoint.
// The fix wraps each cast in a CASE guard using the regex '^[0-9]*\.?[0-9]+$'
// so non-numeric values are silently NULLed rather than thrown.
// =============================================================================

describe('quality query numeric cast guard', () => {
  let pool;

  beforeEach(() => {
    pool = createMockPool();
    resetBrainConfigCache();
  });

  afterEach(() => {
    resetBrainConfigCache();
  });

  // T-QUALITY-001: non-numeric rework_rate "low" must not crash the endpoint
  it('T-QUALITY-001: non-numeric rework_rate "low" returns 200 without crashing', async () => {
    // T1 row required so the agent list is non-empty
    pool.setQueryResult("telemetry_tier' = '1'", {
      rows: [{ agent: 'colby', invocations: 3, avg_duration_ms: 800, total_cost: '0.0300', avg_input_tokens: 900, avg_output_tokens: 400 }],
      rowCount: 1,
    });
    // T3 quality row with a non-numeric rework_rate — the DB CASE guard returns NULL avg
    pool.setQueryResult("telemetry_tier' = '3'", {
      rows: [{ rework_rate: null, first_pass_qa_rate: null }],
      rowCount: 1,
    });

    const cfg = { apiToken: null, _source: 'env' };
    const handler = createRestHandler(pool, cfg);

    const req = createMockReq({ method: 'GET', url: '/api/telemetry/agents' });
    const res = createMockRes();

    await handler(req, res);

    assert.strictEqual(res.statusCode, 200, 'endpoint must return 200 when rework_rate is "low"');
    const body = res.json;
    assert.ok(Array.isArray(body), 'response body must be an array');
    // Colby row should have null quality metrics (non-numeric skipped)
    const colby = body.find(r => r.agent === 'colby');
    assert.ok(colby, 'colby row must be present');
    assert.strictEqual(colby.metadata.rework_rate, null, 'rework_rate must be null when only "low" is stored');
  });

  // T-QUALITY-002: mixed rework_rate — "low" ignored, "0.5" averages correctly
  it('T-QUALITY-002: mixed rework_rate "low"+"0.5" — numeric row averages to 0.5', async () => {
    pool.setQueryResult("telemetry_tier' = '1'", {
      rows: [{ agent: 'colby', invocations: 2, avg_duration_ms: 700, total_cost: '0.0200', avg_input_tokens: 800, avg_output_tokens: 300 }],
      rowCount: 1,
    });
    // DB-side CASE guard already skipped "low"; avg of the single valid 0.5 row = 0.5
    pool.setQueryResult("telemetry_tier' = '3'", {
      rows: [{ rework_rate: '0.5', first_pass_qa_rate: null }],
      rowCount: 1,
    });

    const cfg = { apiToken: null, _source: 'env' };
    const handler = createRestHandler(pool, cfg);

    const req = createMockReq({ method: 'GET', url: '/api/telemetry/agents' });
    const res = createMockRes();

    await handler(req, res);

    assert.strictEqual(res.statusCode, 200);
    const body = res.json;
    const colby = body.find(r => r.agent === 'colby');
    assert.ok(colby, 'colby row must be present');
    assert.strictEqual(colby.metadata.rework_rate, 0.5, 'rework_rate must be 0.5 — non-numeric row silently skipped');
  });

  // T-QUALITY-003: "1.0 cycles/unit" silently skipped — rework_rate is null
  it('T-QUALITY-003: rework_rate "1.0 cycles/unit" is silently skipped — result is null', async () => {
    pool.setQueryResult("telemetry_tier' = '1'", {
      rows: [{ agent: 'colby', invocations: 1, avg_duration_ms: 600, total_cost: '0.0100', avg_input_tokens: 700, avg_output_tokens: 200 }],
      rowCount: 1,
    });
    // DB CASE guard rejects "1.0 cycles/unit"; avg of zero valid rows = NULL
    pool.setQueryResult("telemetry_tier' = '3'", {
      rows: [{ rework_rate: null, first_pass_qa_rate: null }],
      rowCount: 1,
    });

    const cfg = { apiToken: null, _source: 'env' };
    const handler = createRestHandler(pool, cfg);

    const req = createMockReq({ method: 'GET', url: '/api/telemetry/agents' });
    const res = createMockRes();

    await handler(req, res);

    assert.strictEqual(res.statusCode, 200);
    const body = res.json;
    const colby = body.find(r => r.agent === 'colby');
    assert.ok(colby, 'colby row must be present');
    assert.strictEqual(colby.metadata.rework_rate, null, 'rework_rate must be null when only "1.0 cycles/unit" is stored');
  });

  // T-QUALITY-004: regression — valid numeric "0.29" still computes correctly
  it('T-QUALITY-004: regression — numeric rework_rate "0.29" returns 0.29', async () => {
    pool.setQueryResult("telemetry_tier' = '1'", {
      rows: [{ agent: 'colby', invocations: 4, avg_duration_ms: 900, total_cost: '0.0400', avg_input_tokens: 1100, avg_output_tokens: 600 }],
      rowCount: 1,
    });
    pool.setQueryResult("telemetry_tier' = '3'", {
      rows: [{ rework_rate: '0.29', first_pass_qa_rate: '0.95' }],
      rowCount: 1,
    });

    const cfg = { apiToken: null, _source: 'env' };
    const handler = createRestHandler(pool, cfg);

    const req = createMockReq({ method: 'GET', url: '/api/telemetry/agents' });
    const res = createMockRes();

    await handler(req, res);

    assert.strictEqual(res.statusCode, 200);
    const body = res.json;
    const colby = body.find(r => r.agent === 'colby');
    assert.ok(colby, 'colby row must be present');
    assert.strictEqual(colby.metadata.rework_rate, 0.29, 'numeric rework_rate must still compute correctly after guard is applied');
    assert.strictEqual(colby.metadata.first_pass_qa_rate, 0.95, 'numeric first_pass_qa_rate must still compute correctly after guard is applied');
  });
});
