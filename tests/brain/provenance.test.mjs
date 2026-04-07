/**
 * TDD: authored by Roz pre-build. Colby must not modify assertions.
 *
 * Tests for ADR-0026: Beads-Style Structured Provenance for Brain Captures
 * Test IDs: T-0026-001 through T-0026-028
 *
 * These tests define correct behavior BEFORE implementation. They are expected
 * to fail against the current implementation until Colby builds ADR-0026.
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createMockPool } from './helpers/mock-pool.mjs';
import { createEmbeddingResponse, createMockFetch } from './helpers/mock-fetch.mjs';
import { registerTools } from '../../brain/lib/tools.mjs';
import { resetBrainConfigCache } from '../../brain/lib/conflict.mjs';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

// ---------------------------------------------------------------------------
// Shared test infrastructure (mirrors tools.test.mjs)
// ---------------------------------------------------------------------------

function createMockServer() {
  const tools = new Map();
  function tool(name, description, schema, handler) {
    tools.set(name, { name, description, schema, handler });
  }
  return { tool, tools };
}

// Resolve project root relative to this test file's location.
// __dirname is not available in ESM; derive from import.meta.url.
const PROJECT_ROOT = resolve(new URL('.', import.meta.url).pathname, '..', '..');

// ---------------------------------------------------------------------------
// Shared base thought for mock DB rows (fields required by atelier_trace)
// ---------------------------------------------------------------------------
const BASE_THOUGHT = {
  id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  content: 'Use JSONB for provenance storage',
  thought_type: 'decision',
  source_agent: 'cal',
  source_phase: 'design',
  importance: 0.9,
  status: 'active',
  scope: ['default'],
  captured_by: 'Test User <test@example.com>',
  created_at: new Date().toISOString(),
};

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

describe('ADR-0026 Beads Provenance', () => {
  let originalFetch;
  let pool;
  let srv;

  const defaultCfg = {
    openrouter_api_key: 'test-api-key',
    capturedBy: 'Test User <test@example.com>',
    brain_name: 'Test Brain',
    _source: 'env',
  };

  // Standard valid params for agent_capture (no provenance)
  const baseCapture = {
    content: 'Architecture decision about storage',
    thought_type: 'decision',
    source_agent: 'cal',
    source_phase: 'design',
    importance: 0.85,
  };

  // Standard mock setup needed for agent_capture to succeed
  const thoughtId = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
  function setupCaptureSuccess(pool) {
    pool.setQueryResult('brain_config', {
      rows: [{ brain_enabled: true, conflict_detection_enabled: false, conflict_duplicate_threshold: 0.9, conflict_candidate_threshold: 0.7, conflict_llm_enabled: false }],
      rowCount: 1,
    });
    pool.setQueryResult('INSERT INTO thoughts', {
      rows: [{ id: thoughtId, created_at: new Date().toISOString() }],
      rowCount: 1,
    });
  }

  beforeEach(() => {
    originalFetch = globalThis.fetch;
    pool = createMockPool();
    srv = createMockServer();
    resetBrainConfigCache();

    globalThis.fetch = createMockFetch({
      'embeddings': { status: 200, body: createEmbeddingResponse(1536) },
    });

    registerTools(srv, pool, defaultCfg);
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    resetBrainConfigCache();
  });

  function getToolHandler(name) {
    const toolDef = srv.tools.get(name);
    assert.ok(toolDef, `Tool '${name}' should be registered`);
    return toolDef.handler;
  }

  function getToolSchema(name) {
    const toolDef = srv.tools.get(name);
    assert.ok(toolDef, `Tool '${name}' should be registered`);
    return toolDef.schema;
  }

  // =========================================================================
  // agent_capture / provenance — happy paths
  // =========================================================================

  describe('agent_capture provenance storage', () => {

    // T-0026-001: all four provenance fields stored under metadata.provenance
    it('T-0026-001: stores all four provenance fields in metadata.provenance', async () => {
      // T-0026-001
      setupCaptureSuccess(pool);

      const handler = getToolHandler('agent_capture');
      await handler({
        ...baseCapture,
        decided_by: { agent: 'cal', human_approved: true },
        alternatives_rejected: [{ alternative: 'new columns', reason: 'schema bloat' }],
        evidence: [{ file: 'brain/schema.sql', line: 42 }],
        confidence: 0.9,
      });

      // The INSERT INTO thoughts call must pass metadata containing provenance
      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');

      // The metadata param is the 3rd parameter (index 2, 0-based) in the INSERT
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      assert.ok(metadata.provenance, 'metadata.provenance must exist');
      assert.deepStrictEqual(metadata.provenance.decided_by, { agent: 'cal', human_approved: true });
      assert.deepStrictEqual(metadata.provenance.alternatives_rejected, [{ alternative: 'new columns', reason: 'schema bloat' }]);
      assert.deepStrictEqual(metadata.provenance.evidence, [{ file: 'brain/schema.sql', line: 42 }]);
      assert.strictEqual(metadata.provenance.confidence, 0.9);
    });

    // T-0026-002: only decided_by — no other provenance keys
    it('T-0026-002: stores only decided_by when only that field is provided', async () => {
      // T-0026-002
      setupCaptureSuccess(pool);

      const handler = getToolHandler('agent_capture');
      await handler({
        ...baseCapture,
        decided_by: { agent: 'eva', human_approved: false },
      });

      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      assert.ok(metadata.provenance, 'metadata.provenance must exist');
      assert.deepStrictEqual(metadata.provenance.decided_by, { agent: 'eva', human_approved: false });
      // No other provenance keys should be present
      assert.strictEqual(metadata.provenance.alternatives_rejected, undefined, 'alternatives_rejected must not be present');
      assert.strictEqual(metadata.provenance.evidence, undefined, 'evidence must not be present');
      assert.strictEqual(metadata.provenance.confidence, undefined, 'confidence must not be present');
    });

    // T-0026-003: only alternatives_rejected
    it('T-0026-003: stores only alternatives_rejected when only that field is provided', async () => {
      // T-0026-003
      setupCaptureSuccess(pool);

      const alts = [
        { alternative: 'Postgres columns', reason: 'DDL migration burden' },
        { alternative: 'Separate audit table', reason: 'two sources of truth' },
      ];

      const handler = getToolHandler('agent_capture');
      await handler({
        ...baseCapture,
        alternatives_rejected: alts,
      });

      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      assert.ok(metadata.provenance, 'metadata.provenance must exist');
      assert.deepStrictEqual(metadata.provenance.alternatives_rejected, alts);
      assert.strictEqual(metadata.provenance.decided_by, undefined);
      assert.strictEqual(metadata.provenance.evidence, undefined);
      assert.strictEqual(metadata.provenance.confidence, undefined);
    });

    // T-0026-004: only evidence
    it('T-0026-004: stores only evidence when only that field is provided', async () => {
      // T-0026-004
      setupCaptureSuccess(pool);

      const evidence = [{ file: 'brain/lib/tools.mjs', line: 82 }];

      const handler = getToolHandler('agent_capture');
      await handler({
        ...baseCapture,
        evidence,
      });

      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      assert.ok(metadata.provenance, 'metadata.provenance must exist');
      assert.deepStrictEqual(metadata.provenance.evidence, evidence);
      assert.strictEqual(metadata.provenance.decided_by, undefined);
      assert.strictEqual(metadata.provenance.alternatives_rejected, undefined);
      assert.strictEqual(metadata.provenance.confidence, undefined);
    });

    // T-0026-005: only confidence
    it('T-0026-005: stores only confidence when only that field is provided', async () => {
      // T-0026-005
      setupCaptureSuccess(pool);

      const handler = getToolHandler('agent_capture');
      await handler({
        ...baseCapture,
        confidence: 0.6,
      });

      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      assert.ok(metadata.provenance, 'metadata.provenance must exist');
      assert.strictEqual(metadata.provenance.confidence, 0.6);
      assert.strictEqual(metadata.provenance.decided_by, undefined);
      assert.strictEqual(metadata.provenance.alternatives_rejected, undefined);
      assert.strictEqual(metadata.provenance.evidence, undefined);
    });

    // T-0026-006: no provenance fields → no provenance key injected
    it('T-0026-006: does not add provenance key to metadata when no provenance fields are provided', async () => {
      // T-0026-006
      setupCaptureSuccess(pool);

      const handler = getToolHandler('agent_capture');
      await handler({ ...baseCapture });

      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      assert.strictEqual(metadata.provenance, undefined, 'provenance key must NOT be injected when no provenance fields are provided');
    });

    // T-0026-007: existing metadata keys are preserved alongside provenance
    it('T-0026-007: preserves existing metadata keys alongside provenance', async () => {
      // T-0026-007
      setupCaptureSuccess(pool);

      const handler = getToolHandler('agent_capture');
      await handler({
        ...baseCapture,
        metadata: { quality_signals: { extraction_method: 'adr_parse' }, custom_tag: 'adr-0026' },
        decided_by: { agent: 'cal', human_approved: false },
      });

      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      // Pre-existing keys must survive
      assert.deepStrictEqual(metadata.quality_signals, { extraction_method: 'adr_parse' });
      assert.strictEqual(metadata.custom_tag, 'adr-0026');
      // Provenance must also be present
      assert.deepStrictEqual(metadata.provenance.decided_by, { agent: 'cal', human_approved: false });
    });

    // T-0026-014: empty alternatives_rejected array → no provenance key for that field
    it('T-0026-014: does not store provenance.alternatives_rejected when empty array is provided', async () => {
      // T-0026-014
      setupCaptureSuccess(pool);

      const handler = getToolHandler('agent_capture');
      await handler({
        ...baseCapture,
        alternatives_rejected: [],
      });

      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      // Empty array must be treated as absent — provenance key must not appear at all,
      // OR if provenance exists for other reasons it must not contain alternatives_rejected.
      const hasAlts = metadata.provenance && metadata.provenance.alternatives_rejected !== undefined;
      assert.strictEqual(hasAlts, false, 'alternatives_rejected must not be stored when empty array provided');
    });

    // T-0026-015: empty evidence array → no provenance key for that field
    it('T-0026-015: does not store provenance.evidence when empty array is provided', async () => {
      // T-0026-015
      setupCaptureSuccess(pool);

      const handler = getToolHandler('agent_capture');
      await handler({
        ...baseCapture,
        evidence: [],
      });

      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      const hasEvidence = metadata.provenance && metadata.provenance.evidence !== undefined;
      assert.strictEqual(hasEvidence, false, 'evidence must not be stored when empty array provided');
    });

    // T-0026-025: merge precedence — explicit params overwrite raw metadata.provenance
    it('T-0026-025: explicit provenance params overwrite raw metadata.provenance when both present', async () => {
      // T-0026-025
      setupCaptureSuccess(pool);

      const handler = getToolHandler('agent_capture');
      await handler({
        ...baseCapture,
        // Raw provenance supplied via metadata — should be overwritten by explicit param
        metadata: { provenance: { decided_by: { agent: 'colby', human_approved: false } } },
        decided_by: { agent: 'cal', human_approved: true },
      });

      const insertQuery = pool.queries.find(q => q.sql.includes('INSERT INTO thoughts'));
      assert.ok(insertQuery, 'INSERT INTO thoughts must be executed');
      const metadataArg = insertQuery.params[2];
      const metadata = typeof metadataArg === 'string' ? JSON.parse(metadataArg) : metadataArg;

      // The explicit decided_by param must win
      assert.deepStrictEqual(
        metadata.provenance.decided_by,
        { agent: 'cal', human_approved: true },
        'Explicit decided_by must overwrite the value supplied via raw metadata.provenance'
      );
    });

  });

  // =========================================================================
  // agent_capture / validation — failure paths (Zod schema inspection)
  // The MCP SDK validates params before the handler runs, matching T-0003-088.
  // We test by calling .safeParse() on the registered schema object directly.
  // =========================================================================

  describe('agent_capture provenance validation', () => {

    // T-0026-008: decided_by missing agent field
    it('T-0026-008: rejects decided_by with missing agent field', async () => {
      // T-0026-008
      const { z } = await import('zod');
      const schema = getToolSchema('agent_capture');
      const zodSchema = z.object(schema);

      const result = zodSchema.safeParse({
        ...baseCapture,
        decided_by: { human_approved: true }, // missing agent
      });

      assert.strictEqual(result.success, false, 'Zod must reject decided_by missing agent field');
      const issues = result.error.issues.map(i => i.path.join('.'));
      assert.ok(
        issues.some(p => p.includes('decided_by') && p.includes('agent')),
        `Expected validation error on decided_by.agent, got: ${JSON.stringify(issues)}`
      );
    });

    // T-0026-009: decided_by missing human_approved field
    it('T-0026-009: rejects decided_by with missing human_approved field', async () => {
      // T-0026-009
      const { z } = await import('zod');
      const schema = getToolSchema('agent_capture');
      const zodSchema = z.object(schema);

      const result = zodSchema.safeParse({
        ...baseCapture,
        decided_by: { agent: 'cal' }, // missing human_approved
      });

      assert.strictEqual(result.success, false, 'Zod must reject decided_by missing human_approved field');
      const issues = result.error.issues.map(i => i.path.join('.'));
      assert.ok(
        issues.some(p => p.includes('decided_by') && p.includes('human_approved')),
        `Expected validation error on decided_by.human_approved, got: ${JSON.stringify(issues)}`
      );
    });

    // T-0026-010: confidence above 1
    it('T-0026-010: rejects confidence above 1 (e.g. 1.5)', async () => {
      // T-0026-010
      const { z } = await import('zod');
      const schema = getToolSchema('agent_capture');
      const zodSchema = z.object(schema);

      const result = zodSchema.safeParse({
        ...baseCapture,
        confidence: 1.5,
      });

      assert.strictEqual(result.success, false, 'Zod must reject confidence > 1');
    });

    // T-0026-011: confidence below 0
    it('T-0026-011: rejects confidence below 0 (e.g. -0.1)', async () => {
      // T-0026-011
      const { z } = await import('zod');
      const schema = getToolSchema('agent_capture');
      const zodSchema = z.object(schema);

      const result = zodSchema.safeParse({
        ...baseCapture,
        confidence: -0.1,
      });

      assert.strictEqual(result.success, false, 'Zod must reject confidence < 0');
    });

    // T-0026-012: evidence with non-positive line number
    it('T-0026-012: rejects evidence entry with non-positive line number (e.g. 0)', async () => {
      // T-0026-012
      const { z } = await import('zod');
      const schema = getToolSchema('agent_capture');
      const zodSchema = z.object(schema);

      const result = zodSchema.safeParse({
        ...baseCapture,
        evidence: [{ file: 'brain/lib/tools.mjs', line: 0 }],
      });

      assert.strictEqual(result.success, false, 'Zod must reject evidence.line = 0 (must be positive)');
    });

    // T-0026-013: alternatives_rejected missing reason
    it('T-0026-013: rejects alternatives_rejected entry with missing reason field', async () => {
      // T-0026-013
      const { z } = await import('zod');
      const schema = getToolSchema('agent_capture');
      const zodSchema = z.object(schema);

      const result = zodSchema.safeParse({
        ...baseCapture,
        alternatives_rejected: [{ alternative: 'WebSocket sync' }], // missing reason
      });

      assert.strictEqual(result.success, false, 'Zod must reject alternatives_rejected entry missing reason');
      const issues = result.error.issues.map(i => i.path.join('.'));
      assert.ok(
        issues.some(p => p.includes('reason')),
        `Expected validation error mentioning reason, got: ${JSON.stringify(issues)}`
      );
    });

    // T-0026-023: evidence missing file field
    it('T-0026-023: rejects evidence entry with missing file field', async () => {
      // T-0026-023
      const { z } = await import('zod');
      const schema = getToolSchema('agent_capture');
      const zodSchema = z.object(schema);

      const result = zodSchema.safeParse({
        ...baseCapture,
        evidence: [{ line: 42 }], // missing file
      });

      assert.strictEqual(result.success, false, 'Zod must reject evidence entry missing file field');
      const issues = result.error.issues.map(i => i.path.join('.'));
      assert.ok(
        issues.some(p => p.includes('file')),
        `Expected validation error mentioning file, got: ${JSON.stringify(issues)}`
      );
    });

    // T-0026-024: alternatives_rejected missing alternative field
    it('T-0026-024: rejects alternatives_rejected entry with missing alternative field', async () => {
      // T-0026-024
      const { z } = await import('zod');
      const schema = getToolSchema('agent_capture');
      const zodSchema = z.object(schema);

      const result = zodSchema.safeParse({
        ...baseCapture,
        alternatives_rejected: [{ reason: 'schema bloat' }], // missing alternative
      });

      assert.strictEqual(result.success, false, 'Zod must reject alternatives_rejected entry missing alternative field');
      const issues = result.error.issues.map(i => i.path.join('.'));
      assert.ok(
        issues.some(p => p.includes('alternative')),
        `Expected validation error mentioning alternative, got: ${JSON.stringify(issues)}`
      );
    });

    // T-0026-028: evidence with float line number (Zod .int() constraint)
    it('T-0026-028: rejects evidence entry with float line number (e.g. 1.5)', async () => {
      // T-0026-028
      const { z } = await import('zod');
      const schema = getToolSchema('agent_capture');
      const zodSchema = z.object(schema);

      const result = zodSchema.safeParse({
        ...baseCapture,
        evidence: [{ file: 'brain/lib/tools.mjs', line: 1.5 }],
      });

      assert.strictEqual(result.success, false, 'Zod must reject evidence.line that is a float (must be integer)');
    });

  });

  // =========================================================================
  // atelier_trace / provenance + superseded_by
  // =========================================================================

  describe('atelier_trace provenance and superseded_by', () => {

    const rootId = 'cccccccc-cccc-cccc-cccc-cccccccccccc';
    const supersederId = 'dddddddd-dddd-dddd-dddd-dddddddddddd';
    const supersederId2 = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee';
    const childId = 'ffffffff-ffff-ffff-ffff-ffffffffffff';

    const rootThoughtWithProvenance = {
      ...BASE_THOUGHT,
      id: rootId,
      metadata: {
        provenance: {
          decided_by: { agent: 'cal', human_approved: true },
          alternatives_rejected: [{ alternative: 'new columns', reason: 'schema bloat' }],
          evidence: [{ file: 'brain/schema.sql', line: 12 }],
          confidence: 0.85,
        },
      },
    };

    const rootThoughtWithoutProvenance = {
      ...BASE_THOUGHT,
      id: rootId,
      metadata: {},
    };

    // T-0026-016: thought with metadata.provenance → chain node contains provenance object
    it('T-0026-016: returns provenance object in chain node when thought has metadata.provenance', async () => {
      // T-0026-016
      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [rootThoughtWithProvenance],
        rowCount: 1,
      });
      // No backward/forward traversal results
      pool.setQueryResult('r.source_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('r.target_id = $1', { rows: [], rowCount: 0 });
      // superseded_by batch lookup returns empty
      pool.setQueryResult('target_id = ANY', { rows: [], rowCount: 0 });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({ thought_id: rootId, direction: 'both' });

      assert.ok(!result.isError, `Expected no error, got: ${result.content[0].text}`);
      const parsed = JSON.parse(result.content[0].text);
      const root = parsed.chain.find(n => n.direction === 'root');
      assert.ok(root, 'Chain must contain a root node');
      assert.ok(root.provenance !== undefined, 'Chain node must have a provenance field');
      assert.ok(root.provenance !== null, 'provenance must be an object, not null, when metadata.provenance exists');
      assert.deepStrictEqual(root.provenance.decided_by, { agent: 'cal', human_approved: true });
      assert.deepStrictEqual(
        root.provenance.alternatives_rejected,
        [{ alternative: 'new columns', reason: 'schema bloat' }]
      );
      assert.strictEqual(root.provenance.confidence, 0.85);
    });

    // T-0026-017: thought without metadata.provenance → chain node has provenance: null
    it('T-0026-017: returns provenance: null in chain node when thought has no metadata.provenance', async () => {
      // T-0026-017
      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [rootThoughtWithoutProvenance],
        rowCount: 1,
      });
      pool.setQueryResult('r.source_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('r.target_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('target_id = ANY', { rows: [], rowCount: 0 });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({ thought_id: rootId, direction: 'both' });

      assert.ok(!result.isError, `Expected no error, got: ${result.content[0].text}`);
      const parsed = JSON.parse(result.content[0].text);
      const root = parsed.chain.find(n => n.direction === 'root');
      assert.ok(root, 'Chain must contain a root node');
      assert.strictEqual(root.provenance, null, 'provenance must be null when metadata.provenance is absent');
    });

    // T-0026-018: superseded thought → superseded_by contains superseder's UUID
    it('T-0026-018: returns superseded_by array with superseding thought UUID', async () => {
      // T-0026-018
      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [{ ...rootThoughtWithoutProvenance, status: 'superseded' }],
        rowCount: 1,
      });
      pool.setQueryResult('r.source_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('r.target_id = $1', { rows: [], rowCount: 0 });
      // The batch superseded_by query
      pool.setQueryResult('target_id = ANY', {
        rows: [{ target_id: rootId, superseded_by: [supersederId] }],
        rowCount: 1,
      });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({ thought_id: rootId, direction: 'both' });

      assert.ok(!result.isError, `Expected no error, got: ${result.content[0].text}`);
      const parsed = JSON.parse(result.content[0].text);
      const root = parsed.chain.find(n => n.direction === 'root');
      assert.ok(root, 'Chain must contain a root node');
      assert.ok(Array.isArray(root.superseded_by), 'superseded_by must be an array');
      assert.ok(root.superseded_by.includes(supersederId), 'superseded_by must contain the superseding thought UUID');
    });

    // T-0026-019: non-superseded thought → superseded_by is empty array
    it('T-0026-019: returns superseded_by: [] for a thought that has not been superseded', async () => {
      // T-0026-019
      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [rootThoughtWithoutProvenance],
        rowCount: 1,
      });
      pool.setQueryResult('r.source_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('r.target_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('target_id = ANY', { rows: [], rowCount: 0 });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({ thought_id: rootId, direction: 'both' });

      assert.ok(!result.isError, `Expected no error, got: ${result.content[0].text}`);
      const parsed = JSON.parse(result.content[0].text);
      const root = parsed.chain.find(n => n.direction === 'root');
      assert.ok(root, 'Chain must contain a root node');
      assert.ok(Array.isArray(root.superseded_by), 'superseded_by must be an array');
      assert.deepStrictEqual(root.superseded_by, [], 'superseded_by must be empty array for non-superseded thought');
    });

    // T-0026-020: thought superseded by multiple thoughts → all UUIDs in superseded_by
    it('T-0026-020: returns all superseding UUIDs when thought is superseded by multiple thoughts', async () => {
      // T-0026-020
      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [{ ...rootThoughtWithoutProvenance, status: 'superseded' }],
        rowCount: 1,
      });
      pool.setQueryResult('r.source_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('r.target_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('target_id = ANY', {
        rows: [{ target_id: rootId, superseded_by: [supersederId, supersederId2] }],
        rowCount: 1,
      });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({ thought_id: rootId, direction: 'both' });

      assert.ok(!result.isError, `Expected no error, got: ${result.content[0].text}`);
      const parsed = JSON.parse(result.content[0].text);
      const root = parsed.chain.find(n => n.direction === 'root');
      assert.ok(root, 'Chain must contain a root node');
      assert.ok(Array.isArray(root.superseded_by), 'superseded_by must be an array');
      assert.ok(root.superseded_by.includes(supersederId), 'must include first superseder');
      assert.ok(root.superseded_by.includes(supersederId2), 'must include second superseder');
      assert.strictEqual(root.superseded_by.length, 2, 'must have exactly two superseding UUIDs');
    });

    // T-0026-021: chain depth > 1 → superseded_by executed as single batch query
    it('T-0026-021: executes superseded_by as a single batch query for chains with depth > 1', async () => {
      // T-0026-021
      // Root thought
      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [{ ...rootThoughtWithoutProvenance, id: rootId }],
        rowCount: 1,
      });
      // Backward traversal returns one child thought
      pool.setQueryResult('r.source_id = $1', {
        rows: [
          {
            id: childId,
            content: 'Child decision',
            thought_type: 'decision',
            source_agent: 'cal',
            source_phase: 'design',
            importance: 0.7,
            status: 'active',
            scope: ['default'],
            captured_by: 'Test User <test@example.com>',
            created_at: new Date().toISOString(),
            metadata: {},
            depth: 1,
            via_relation: 'supersedes',
            via_context: 'evolution',
          },
        ],
        rowCount: 1,
      });
      pool.setQueryResult('r.target_id = $1', { rows: [], rowCount: 0 });
      // Batch lookup: single query covers both nodes
      pool.setQueryResult('target_id = ANY', { rows: [], rowCount: 0 });

      const handler = getToolHandler('atelier_trace');
      await handler({ thought_id: rootId, direction: 'both' });

      // Count how many times the superseded_by query runs.
      // A batch implementation executes it exactly ONCE regardless of chain length.
      const supersededByQueries = pool.queries.filter(q =>
        q.sql.includes('target_id') &&
        q.sql.includes('supersedes') &&
        (q.sql.includes('ANY') || q.sql.includes('array_agg'))
      );
      assert.strictEqual(
        supersededByQueries.length,
        1,
        `superseded_by must be resolved with a single batch query, found ${supersededByQueries.length} matching queries`
      );
    });

    // T-0026-022: chain node carries both provenance and superseded_by
    it('T-0026-022: returns both provenance and superseded_by on the same chain node', async () => {
      // T-0026-022
      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [{ ...rootThoughtWithProvenance, status: 'superseded' }],
        rowCount: 1,
      });
      pool.setQueryResult('r.source_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('r.target_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('target_id = ANY', {
        rows: [{ target_id: rootId, superseded_by: [supersederId] }],
        rowCount: 1,
      });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({ thought_id: rootId, direction: 'both' });

      assert.ok(!result.isError, `Expected no error, got: ${result.content[0].text}`);
      const parsed = JSON.parse(result.content[0].text);
      const root = parsed.chain.find(n => n.direction === 'root');
      assert.ok(root, 'Chain must contain a root node');

      // provenance must be populated
      assert.ok(root.provenance !== null && root.provenance !== undefined, 'provenance must be present');
      assert.deepStrictEqual(root.provenance.decided_by, { agent: 'cal', human_approved: true });

      // superseded_by must be populated on the same node
      assert.ok(Array.isArray(root.superseded_by), 'superseded_by must be an array');
      assert.ok(root.superseded_by.includes(supersederId), 'superseded_by must contain superseder UUID');
    });

  });

  // =========================================================================
  // Migration 007 and version bump
  // =========================================================================

  describe('migration 007 and version bump', () => {

    // T-0026-026: migration 007 SQL file exists and references ADR-0026
    it('T-0026-026: brain/migrations/007-beads-provenance-noop.sql exists with ADR-0026 reference', () => {
      // T-0026-026
      const migrationPath = resolve(PROJECT_ROOT, 'brain', 'migrations', '007-beads-provenance-noop.sql');
      assert.ok(
        existsSync(migrationPath),
        `Migration file must exist at ${migrationPath}`
      );

      const content = readFileSync(migrationPath, 'utf8');
      assert.ok(
        content.includes('ADR-0026') || content.includes('ADR 0026'),
        `Migration file must contain a reference to ADR-0026. File content: ${content.slice(0, 200)}`
      );
    });

    // T-0026-027: brain/package.json version is 1.3.0
    it('T-0026-027: brain/package.json version is 1.3.0', () => {
      // T-0026-027
      const pkgPath = resolve(PROJECT_ROOT, 'brain', 'package.json');
      assert.ok(existsSync(pkgPath), `brain/package.json must exist at ${pkgPath}`);

      const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
      assert.strictEqual(
        pkg.version,
        '1.3.0',
        `brain/package.json version must be 1.3.0, found: ${pkg.version}`
      );
    });

  });

});
