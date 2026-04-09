/**
 * tests/brain/hydrate-mcp-tool.test.mjs
 *
 * Tests for the atelier_hydrate MCP tool (brain/lib/tools.mjs).
 *
 * Test IDs: T-HYDRATE-001 through T-HYDRATE-012
 *
 * The tool:
 *   - Accepts session_path (string, required)
 *   - Expands ~ in the path
 *   - Returns {status: "queued", session_path: <expanded>} immediately
 *   - Fires setImmediate for async DB processing (non-blocking)
 *   - Is registered in registerTools() alongside the other 6 tools
 *   - Uses the pool passed to registerTools, not a new DB connection
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import os from 'node:os';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { createMockPool } from './helpers/mock-pool.mjs';
import { registerTools, hydrateStatusMap } from '../../brain/lib/tools.mjs';
import { resetBrainConfigCache } from '../../brain/lib/conflict.mjs';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createMockServer() {
  const tools = new Map();
  function tool(name, description, schema, handler) {
    tools.set(name, { name, description, schema, handler });
  }
  return { tool, tools };
}

/** Wait for all pending setImmediate callbacks to drain. */
function drainSetImmediate() {
  return new Promise(resolve => setImmediate(resolve));
}

/** Build a minimal project sessions directory with one session and one subagent JSONL. */
function buildSessionDir(baseDir) {
  const sessionId = 'test-session-abc123';
  const sessionDir = path.join(baseDir, sessionId);
  const subagentsDir = path.join(sessionDir, 'subagents');
  mkdirSync(subagentsDir, { recursive: true });

  // Minimal JSONL — no usage data (all zeros), but parseable
  const agentId = 'colby-xyz';
  const jsonlPath = path.join(subagentsDir, `${agentId}.jsonl`);
  writeFileSync(jsonlPath, JSON.stringify({
    message: { model: 'claude-sonnet-4', usage: { input_tokens: 100, output_tokens: 50, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 } },
  }) + '\n');

  // Create a matching parent-level JSONL for Eva discovery
  // (session dir must exist AND .jsonl must be at parent level)
  writeFileSync(path.join(baseDir, `${sessionId}.jsonl`), JSON.stringify({
    message: { model: 'claude-sonnet-4', usage: { input_tokens: 200, output_tokens: 80, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 } },
  }) + '\n');

  return { sessionId, agentId, sessionDir, jsonlPath };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('atelier_hydrate MCP tool', () => {
  let pool;
  let srv;
  let originalFetch;
  let tmpDir;

  const defaultCfg = {
    openrouter_api_key: null,  // No API key → zero-vector embeddings (fast, no HTTP)
    capturedBy: 'Test User <test@example.com>',
    brain_name: 'Test Brain',
    _source: 'env',
    scope: 'test.project',
  };

  beforeEach(() => {
    originalFetch = globalThis.fetch;
    pool = createMockPool();
    srv = createMockServer();
    resetBrainConfigCache();
    tmpDir = mkdtempSync(path.join(os.tmpdir(), 'hydrate-mcp-test-'));

    // Mock brain_config query used by getBrainConfig (from conflict.mjs)
    pool.setQueryResult('brain_config', {
      rows: [{ brain_enabled: true, conflict_detection_enabled: false, conflict_duplicate_threshold: 0.9, conflict_candidate_threshold: 0.7, conflict_llm_enabled: false }],
      rowCount: 1,
    });

    // alreadyHydrated query returns not-hydrated by default (rows: [])
    // pool default result is { rows: [], rowCount: 0 } — correct for "not hydrated"

    registerTools(srv, pool, defaultCfg);
  });

  afterEach(async () => {
    globalThis.fetch = originalFetch;
    resetBrainConfigCache();
    try {
      rmSync(tmpDir, { recursive: true });
    } catch {
      // ignore cleanup errors
    }
    // Drain any pending setImmediate callbacks so they don't bleed into next test
    await drainSetImmediate();
  });

  function getToolHandler(name) {
    const toolDef = srv.tools.get(name);
    assert.ok(toolDef, `Tool '${name}' should be registered`);
    return toolDef.handler;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-001: atelier_hydrate is registered as the 7th tool
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-001: registerTools registers atelier_hydrate as the 7th tool', () => {
    assert.ok(srv.tools.has('atelier_hydrate'), 'atelier_hydrate must be registered');
    assert.strictEqual(srv.tools.size, 8, 'Total tool count must be 8 (6 existing + atelier_hydrate + atelier_hydrate_status)');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-002: returns {status: "queued", session_path} immediately
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-002: returns status queued with the resolved session_path', async () => {
    const handler = getToolHandler('atelier_hydrate');
    const result = await handler({ session_path: tmpDir });

    assert.ok(result.content, 'result must have content array');
    assert.strictEqual(result.content.length, 1);
    const body = JSON.parse(result.content[0].text);
    assert.strictEqual(body.status, 'queued');
    assert.strictEqual(body.session_path, tmpDir);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-003: ~ in session_path is expanded to HOME
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-003: expands ~ in session_path', async () => {
    const handler = getToolHandler('atelier_hydrate');
    const result = await handler({ session_path: '~/some/project' });

    const body = JSON.parse(result.content[0].text);
    const expectedExpanded = path.join(
      process.env.HOME || process.env.USERPROFILE || '',
      'some/project'
    );
    assert.strictEqual(body.session_path, expectedExpanded);
    assert.strictEqual(body.status, 'queued');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-004: does not block — returns before DB queries execute
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-004: returns immediately before any DB queries run', async () => {
    buildSessionDir(tmpDir);
    const handler = getToolHandler('atelier_hydrate');

    const queryCountBefore = pool.queries.length;
    const result = await handler({ session_path: tmpDir });
    const queryCountAfter = pool.queries.length;

    // No DB queries should have run yet (setImmediate defers them)
    assert.strictEqual(queryCountAfter, queryCountBefore, 'No DB queries must fire before setImmediate');
    const body = JSON.parse(result.content[0].text);
    assert.strictEqual(body.status, 'queued');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-005: after drainSetImmediate, DB queries are attempted for JSONL files
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-005: after setImmediate drains, DB queries are attempted for JSONL files', async () => {
    buildSessionDir(tmpDir);
    const handler = getToolHandler('atelier_hydrate');

    await handler({ session_path: tmpDir });
    await drainSetImmediate();

    // alreadyHydrated + INSERT for subagent and Eva files
    // Each file: 1 SELECT (alreadyHydrated) + 1 INSERT (insertTelemetryThought)
    // generateTier3Summaries: 1 SELECT (DISTINCT session_ids) → 0 rows → no INSERT
    assert.ok(pool.queries.length > 0, 'DB queries must have run after setImmediate');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-006: uses the pool passed to registerTools (not a new connection)
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-006: DB queries use the pool passed to registerTools', async () => {
    buildSessionDir(tmpDir);
    const handler = getToolHandler('atelier_hydrate');

    await handler({ session_path: tmpDir });
    await drainSetImmediate();

    // Verify queries went to OUR mock pool
    assert.ok(pool.queries.length > 0, 'Queries must appear on the mock pool');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-007: non-existent session_path does not throw or return error
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-007: non-existent session_path returns queued without error response', async () => {
    const handler = getToolHandler('atelier_hydrate');
    const result = await handler({ session_path: '/tmp/does-not-exist-hydrate-test-xyz' });

    assert.ok(!result.isError, 'result must not be an error');
    const body = JSON.parse(result.content[0].text);
    assert.strictEqual(body.status, 'queued');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-008: non-existent path does not throw after setImmediate either
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-008: non-existent session_path background processing does not throw', async () => {
    const handler = getToolHandler('atelier_hydrate');
    await handler({ session_path: '/tmp/does-not-exist-hydrate-test-xyz' });
    // If this throws, the test fails
    await drainSetImmediate();
    // No error thrown — test passes
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-009: empty session directory returns queued with 0 DB queries after drain
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-009: empty session directory returns queued and issues T3 check query', async () => {
    // tmpDir exists but has no JSONL files
    const handler = getToolHandler('atelier_hydrate');
    await handler({ session_path: tmpDir });
    await drainSetImmediate();

    // generateTier3Summaries always fires one SELECT (DISTINCT session_ids)
    const t3Query = pool.queries.find(q => q.sql && q.sql.includes('telemetry_tier'));
    assert.ok(t3Query, 'T3 summary query must be attempted even with empty directory');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-010: already-hydrated files are skipped (duplicate detection)
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-010: already-hydrated files are skipped (no INSERT issued)', async () => {
    buildSessionDir(tmpDir);

    // Mock alreadyHydrated to return true (already in DB)
    pool.setQueryResult('source_phase', { rows: [{ '?column?': 1 }], rowCount: 1 });

    const handler = getToolHandler('atelier_hydrate');
    await handler({ session_path: tmpDir });
    await drainSetImmediate();

    // No INSERT should have been issued (all files already hydrated)
    const insertQueries = pool.queries.filter(q => q.sql && q.sql.includes('INSERT INTO thoughts'));
    assert.strictEqual(insertQueries.length, 0, 'No INSERT must fire for already-hydrated files');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-011: tool description mentions non-blocking / idempotent
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-011: tool description documents non-blocking and idempotent behavior', () => {
    const toolDef = srv.tools.get('atelier_hydrate');
    assert.ok(toolDef, 'atelier_hydrate must be registered');
    const desc = toolDef.description.toLowerCase();
    assert.ok(
      desc.includes('non-blocking') || desc.includes('immediately'),
      'description must mention non-blocking behavior'
    );
    assert.ok(
      desc.includes('idempotent') || desc.includes('skip'),
      'description must mention idempotent behavior'
    );
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-012: existing 6 tools are still registered (no regression)
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-012: all 6 pre-existing tools remain registered (no regression)', () => {
    const existingTools = [
      'agent_capture', 'agent_search', 'atelier_browse',
      'atelier_stats', 'atelier_relation', 'atelier_trace',
    ];
    for (const name of existingTools) {
      assert.ok(srv.tools.has(name), `Tool '${name}' must still be registered`);
    }
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-013: atelier_hydrate_status returns "idle" for unknown path
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-013: atelier_hydrate_status returns idle for a path that was never hydrated', () => {
    hydrateStatusMap.clear();
    const handler = getToolHandler('atelier_hydrate_status');
    const result = handler({ session_path: '/tmp/never-hydrated-path-xyz' });

    assert.ok(result.content, 'result must have content array');
    const body = JSON.parse(result.content[0].text);
    assert.strictEqual(body.status, 'idle');
    assert.strictEqual(body.session_path, '/tmp/never-hydrated-path-xyz');
    assert.strictEqual(body.files_processed, 0);
    assert.strictEqual(body.files_skipped, 0);
    assert.strictEqual(body.thoughts_inserted, 0);
    assert.deepStrictEqual(body.errors, []);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-014: status transitions from "running" to "completed"
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-014: status is "running" immediately after atelier_hydrate and "completed" after drain', async () => {
    hydrateStatusMap.clear();
    buildSessionDir(tmpDir);

    const hydrateHandler = getToolHandler('atelier_hydrate');
    const statusHandler = getToolHandler('atelier_hydrate_status');

    // Kick off hydration — status should be "running" before setImmediate drains
    await hydrateHandler({ session_path: tmpDir });

    const runningBody = JSON.parse(statusHandler({ session_path: tmpDir }).content[0].text);
    assert.strictEqual(runningBody.status, 'running', 'status must be "running" before setImmediate drains');
    assert.ok(runningBody.started_at, 'started_at must be set when running');

    // Drain setImmediate so background hydration completes
    await drainSetImmediate();

    const completedBody = JSON.parse(statusHandler({ session_path: tmpDir }).content[0].text);
    assert.strictEqual(completedBody.status, 'completed', 'status must be "completed" after drain');
    assert.ok(completedBody.completed_at, 'completed_at must be set after completion');
    assert.ok(typeof completedBody.files_processed === 'number', 'files_processed must be a number');
    assert.ok(typeof completedBody.files_skipped === 'number', 'files_skipped must be a number');
    assert.ok(typeof completedBody.thoughts_inserted === 'number', 'thoughts_inserted must be a number');
    assert.deepStrictEqual(completedBody.errors, [], 'errors must be empty on success');
  });

  // ─────────────────────────────────────────────────────────────────────────
  // T-HYDRATE-015: atelier_hydrate_status is registered as Tool 8
  // ─────────────────────────────────────────────────────────────────────────
  it('T-HYDRATE-015: atelier_hydrate_status is registered as the 8th tool', () => {
    assert.ok(srv.tools.has('atelier_hydrate_status'), 'atelier_hydrate_status must be registered');
    const toolDef = srv.tools.get('atelier_hydrate_status');
    assert.ok(toolDef.description.toLowerCase().includes('session_path') ||
              toolDef.description.toLowerCase().includes('status'),
              'description must reference status behavior');
  });
});
