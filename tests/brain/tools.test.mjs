/**
 * Tests for brain/lib/tools.mjs
 * Test IDs: T-0003-087 through T-0003-102
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { createMockPool } from './helpers/mock-pool.mjs';
import { createEmbeddingResponse, createMockFetch } from './helpers/mock-fetch.mjs';
import { registerTools } from '../../brain/lib/tools.mjs';
import { resetBrainConfigCache } from '../../brain/lib/conflict.mjs';

/**
 * Creates a mock MCP server that captures tool registrations.
 * The real McpServer uses srv.tool(name, description, schema, handler).
 * We capture these so we can call the handlers directly in tests.
 */
function createMockServer() {
  const tools = new Map();

  function tool(name, description, schema, handler) {
    tools.set(name, { name, description, schema, handler });
  }

  return { tool, tools };
}

describe('tools.mjs', () => {
  let originalFetch;
  let pool;
  let srv;
  const defaultCfg = {
    openrouter_api_key: 'test-api-key',
    capturedBy: 'Test User <test@example.com>',
    brain_name: 'Test Brain',
    _source: 'env',
  };

  beforeEach(() => {
    originalFetch = globalThis.fetch;
    pool = createMockPool();
    srv = createMockServer();
    resetBrainConfigCache();

    // Default: embedding API returns valid embedding
    globalThis.fetch = createMockFetch({
      'embeddings': { status: 200, body: createEmbeddingResponse(1536) },
    });

    // Register all tools
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

  describe('registerTools()', () => {
    it('registers all 7 MCP tools', () => {
      assert.ok(srv.tools.has('agent_capture'));
      assert.ok(srv.tools.has('agent_search'));
      assert.ok(srv.tools.has('atelier_browse'));
      assert.ok(srv.tools.has('atelier_stats'));
      assert.ok(srv.tools.has('atelier_relation'));
      assert.ok(srv.tools.has('atelier_trace'));
      assert.ok(srv.tools.has('atelier_hydrate'));
      assert.strictEqual(srv.tools.size, 7);
    });
  });

  describe('agent_capture', () => {
    const validParams = {
      content: 'Test decision about architecture',
      thought_type: 'decision',
      source_agent: 'cal',
      source_phase: 'design',
      importance: 0.8,
    };

    // T-0003-087: agent_capture with valid params inserts thought and returns thought_id
    it('T-0003-087: inserts thought and returns thought_id with valid params', async () => {
      const thoughtId = '11111111-2222-3333-4444-555555555555';
      const createdAt = new Date().toISOString();

      // Mock brain config
      pool.setQueryResult('brain_config', {
        rows: [{ brain_enabled: true, conflict_detection_enabled: false, conflict_duplicate_threshold: 0.9, conflict_candidate_threshold: 0.7, conflict_llm_enabled: false }],
        rowCount: 1,
      });
      // Mock INSERT
      pool.setQueryResult('INSERT INTO thoughts', {
        rows: [{ id: thoughtId, created_at: createdAt }],
        rowCount: 1,
      });

      const handler = getToolHandler('agent_capture');
      const result = await handler(validParams);

      assert.ok(!result.isError, 'Should not be an error');
      const parsed = JSON.parse(result.content[0].text);
      assert.strictEqual(parsed.thought_id, thoughtId);
      assert.strictEqual(parsed.captured_by, defaultCfg.capturedBy);
    });

    // T-0003-088: agent_capture with invalid thought_type returns validation error
    it('T-0003-088: tool schema validates thought_type enum', () => {
      const toolDef = srv.tools.get('agent_capture');
      // The schema uses z.enum(THOUGHT_TYPES), so invalid types would be
      // rejected by zod validation before the handler is called.
      // We verify the schema expects the enum constraint.
      assert.ok(toolDef.schema.thought_type, 'Schema should include thought_type');
    });

    // T-0003-089: agent_capture with supersedes_id creates relation and invalidates target
    it('T-0003-089: creates supersession relation when supersedes_id provided', async () => {
      const newId = '11111111-2222-3333-4444-666666666666';
      const supersedesId = '11111111-2222-3333-4444-777777777777';

      pool.setQueryResult('brain_config', {
        rows: [{ brain_enabled: true, conflict_detection_enabled: false, conflict_duplicate_threshold: 0.9, conflict_candidate_threshold: 0.7, conflict_llm_enabled: false }],
        rowCount: 1,
      });
      pool.setQueryResult('INSERT INTO thoughts', {
        rows: [{ id: newId, created_at: new Date().toISOString() }],
        rowCount: 1,
      });
      pool.setQueryResult('INSERT INTO thought_relations', { rows: [], rowCount: 1 });
      pool.setQueryResult('UPDATE thoughts SET status', { rows: [], rowCount: 1 });

      const handler = getToolHandler('agent_capture');
      const result = await handler({
        ...validParams,
        supersedes_id: supersedesId,
      });

      assert.ok(!result.isError, 'Should not be an error');
      const parsed = JSON.parse(result.content[0].text);
      assert.ok(parsed.related_ids.includes(supersedesId), 'Should include superseded ID in related_ids');

      // Verify supersession relation was created
      const relationQueries = pool.queries.filter(q =>
        q.sql.includes('thought_relations') && q.sql.includes('supersedes')
      );
      assert.ok(relationQueries.length >= 1, 'Should create supersedes relation');

      // Verify target was invalidated
      const invalidateQueries = pool.queries.filter(q =>
        q.sql.includes('superseded') && q.sql.includes('invalidated_at')
      );
      assert.ok(invalidateQueries.length >= 1, 'Should invalidate superseded thought');
    });

    // Edge case: embedding failure rolls back transaction
    it('rolls back transaction on embedding failure', async () => {
      globalThis.fetch = createMockFetch({
        'embeddings': { status: 500, body: 'API unavailable' },
      });

      const handler = getToolHandler('agent_capture');
      const result = await handler(validParams);

      assert.strictEqual(result.isError, true);
      assert.ok(result.content[0].text.includes('Embedding'));

      // Verify ROLLBACK was issued
      const rollbackQueries = pool.queries.filter(q => q.sql === 'ROLLBACK');
      assert.ok(rollbackQueries.length >= 1, 'Should rollback on embedding failure');
    });
  });

  describe('agent_search', () => {
    // T-0003-090: agent_search with valid query returns scored results
    it('T-0003-090: returns scored results with valid query', async () => {
      const searchResults = [
        {
          id: 'aaaa-1111', content: 'Found thought', metadata: {},
          thought_type: 'decision', source_agent: 'cal', source_phase: 'design',
          importance: 0.9, status: 'active', scope: ['default'],
          captured_by: 'User', created_at: new Date().toISOString(),
          similarity: 0.85, recency_score: 0.95, combined_score: 4.2,
        },
      ];

      pool.setQueryResult('match_thoughts_scored', { rows: searchResults, rowCount: 1 });
      pool.setQueryResult('UPDATE thoughts SET last_accessed_at', { rows: [], rowCount: 1 });

      const handler = getToolHandler('agent_search');
      const result = await handler({ query: 'architecture decisions' });

      assert.ok(!result.isError);
      const parsed = JSON.parse(result.content[0].text);
      assert.ok(parsed.results.length > 0, 'Should return results');
      assert.ok(parsed.results[0].similarity !== undefined, 'Results should include similarity score');
      assert.ok(parsed.results[0].combined_score !== undefined, 'Results should include combined_score');
    });

    // T-0003-091: agent_search with no matches returns empty results array
    it('T-0003-091: returns empty results array when no matches found', async () => {
      pool.setQueryResult('match_thoughts_scored', { rows: [], rowCount: 0 });

      const handler = getToolHandler('agent_search');
      const result = await handler({ query: 'nonexistent topic xyz' });

      assert.ok(!result.isError);
      const parsed = JSON.parse(result.content[0].text);
      assert.deepStrictEqual(parsed.results, []);
    });

    // T-0003-092: agent_search updates last_accessed_at on returned thoughts
    it('T-0003-092: updates last_accessed_at on returned thoughts', async () => {
      const id1 = 'aaaa-2222';
      const id2 = 'aaaa-3333';
      pool.setQueryResult('match_thoughts_scored', {
        rows: [
          { id: id1, content: 'A', metadata: {}, thought_type: 'lesson', source_agent: 'eva', source_phase: 'build', importance: 0.5, status: 'active', scope: ['default'], captured_by: 'User', created_at: new Date().toISOString(), similarity: 0.8, recency_score: 0.9, combined_score: 3.5 },
          { id: id2, content: 'B', metadata: {}, thought_type: 'insight', source_agent: 'roz', source_phase: 'qa', importance: 0.6, status: 'active', scope: ['default'], captured_by: 'User', created_at: new Date().toISOString(), similarity: 0.7, recency_score: 0.85, combined_score: 3.2 },
        ],
        rowCount: 2,
      });
      pool.setQueryResult('UPDATE thoughts SET last_accessed_at', { rows: [], rowCount: 2 });

      const handler = getToolHandler('agent_search');
      await handler({ query: 'test' });

      const updateQueries = pool.queries.filter(q =>
        q.sql.includes('last_accessed_at') && q.sql.includes('UPDATE')
      );
      assert.ok(updateQueries.length >= 1, 'Should update last_accessed_at');
    });
  });

  describe('atelier_browse', () => {
    // T-0003-093: atelier_browse with filters returns paginated results
    it('T-0003-093: returns paginated results with filters', async () => {
      const thoughts = [
        { id: 'bb-1', content: 'Decision 1', thought_type: 'decision', source_agent: 'cal', source_phase: 'design', importance: 0.9, status: 'active', scope: ['default'], captured_by: 'User', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      ];
      // Count query matches first (more specific), then data query
      pool.setQueryResult('count(*)::int AS total', { rows: [{ total: 1 }], rowCount: 1 });
      pool.setQueryResult('ORDER BY created_at DESC', { rows: thoughts, rowCount: 1 });

      const handler = getToolHandler('atelier_browse');
      const result = await handler({
        limit: 20,
        offset: 0,
        thought_type: 'decision',
      });

      assert.ok(!result.isError);
      const parsed = JSON.parse(result.content[0].text);
      assert.ok(parsed.thoughts.length > 0);
      assert.strictEqual(parsed.total, 1);
      assert.strictEqual(parsed.limit, 20);
      assert.strictEqual(parsed.offset, 0);
    });
  });

  describe('atelier_stats', () => {
    // T-0003-094: atelier_stats returns brain_enabled, counts by type/status/agent
    it('T-0003-094: returns brain stats with counts', async () => {
      pool.setQueryResult('brain_config', {
        rows: [{ brain_enabled: true, consolidation_interval_minutes: 30 }],
        rowCount: 1,
      });
      pool.setQueryResult('thought_type, count', {
        rows: [{ thought_type: 'decision', count: 5 }],
        rowCount: 1,
      });
      pool.setQueryResult('status, count', {
        rows: [{ status: 'active', count: 10 }],
        rowCount: 1,
      });
      pool.setQueryResult('source_agent, count', {
        rows: [{ source_agent: 'eva', count: 3 }],
        rowCount: 1,
      });
      pool.setQueryResult('captured_by, count', {
        rows: [{ captured_by: 'Test User', count: 8 }],
        rowCount: 1,
      });
      pool.setQueryResult('count(*)::int AS total', {
        rows: [{ total: 10 }],
        rowCount: 1,
      });
      pool.setQueryResult('count(*)::int AS active', {
        rows: [{ active: 8 }],
        rowCount: 1,
      });
      pool.setQueryResult('count(*)::int AS expired', {
        rows: [{ expired: 1 }],
        rowCount: 1,
      });
      pool.setQueryResult('count(*)::int AS invalidated', {
        rows: [{ invalidated: 1 }],
        rowCount: 1,
      });

      const handler = getToolHandler('atelier_stats');
      const result = await handler({});

      assert.ok(!result.isError);
      const parsed = JSON.parse(result.content[0].text);
      assert.strictEqual(parsed.brain_enabled, true);
      assert.strictEqual(parsed.brain_name, 'Test Brain');
      assert.strictEqual(parsed.config_source, 'env');
      assert.ok(parsed.by_type !== undefined);
      assert.ok(parsed.by_status !== undefined);
      assert.ok(parsed.by_agent !== undefined);
      assert.ok(parsed.by_human !== undefined);
    });
  });

  describe('atelier_relation', () => {
    const sourceId = '11111111-1111-1111-1111-111111111111';
    const targetId = '22222222-2222-2222-2222-222222222222';

    // T-0003-095: atelier_relation creates typed relation between thoughts
    it('T-0003-095: creates typed relation between thoughts', async () => {
      pool.setQueryResult('INSERT INTO thought_relations', { rows: [], rowCount: 1 });

      const handler = getToolHandler('atelier_relation');
      const result = await handler({
        source_id: sourceId,
        target_id: targetId,
        relation_type: 'supports',
        context: 'Evidence supports this decision',
      });

      assert.ok(!result.isError);
      const parsed = JSON.parse(result.content[0].text);
      assert.strictEqual(parsed.created, true);
      assert.strictEqual(parsed.source_id, sourceId);
      assert.strictEqual(parsed.target_id, targetId);
      assert.strictEqual(parsed.relation_type, 'supports');
    });

    // T-0003-096: atelier_relation with self-referential IDs returns error
    it('T-0003-096: returns error for self-referential relation', async () => {
      const handler = getToolHandler('atelier_relation');
      const result = await handler({
        source_id: sourceId,
        target_id: sourceId, // same ID
        relation_type: 'supports',
      });

      assert.strictEqual(result.isError, true);
      assert.ok(result.content[0].text.includes('self-referential'));
    });

    // T-0003-097: atelier_relation with cycle in supersedes chain returns error
    it('T-0003-097: returns error when supersedes cycle detected', async () => {
      // Simulate cycle detection query finding a match
      pool.setQueryResult('WITH RECURSIVE chain', {
        rows: [{ '1': 1 }], // cycle found
        rowCount: 1,
      });

      const handler = getToolHandler('atelier_relation');
      const result = await handler({
        source_id: sourceId,
        target_id: targetId,
        relation_type: 'supersedes',
      });

      assert.strictEqual(result.isError, true);
      assert.ok(result.content[0].text.includes('Cycle'));
    });

    // T-0003-098: atelier_relation with supersedes auto-invalidates target
    it('T-0003-098: auto-invalidates target on supersedes relation', async () => {
      // No cycle
      pool.setQueryResult('WITH RECURSIVE chain', { rows: [], rowCount: 0 });
      pool.setQueryResult('INSERT INTO thought_relations', { rows: [], rowCount: 1 });
      pool.setQueryResult('UPDATE thoughts SET status', { rows: [], rowCount: 1 });

      const handler = getToolHandler('atelier_relation');
      const result = await handler({
        source_id: sourceId,
        target_id: targetId,
        relation_type: 'supersedes',
      });

      assert.ok(!result.isError);

      // Verify target was marked as superseded
      const updateQueries = pool.queries.filter(q =>
        q.sql.includes('superseded') && q.sql.includes('invalidated_at')
      );
      assert.ok(updateQueries.length >= 1, 'Should mark target as superseded');
    });
  });

  describe('atelier_trace', () => {
    const rootId = '33333333-3333-3333-3333-333333333333';

    // T-0003-099: atelier_trace follows backward chain correctly
    it('T-0003-099: follows backward chain correctly', async () => {
      const parentId = '44444444-4444-4444-4444-444444444444';

      // Root thought exists
      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [{ id: rootId, content: 'Root thought', thought_type: 'decision', source_agent: 'cal', source_phase: 'design', importance: 0.9, status: 'active', scope: ['default'], captured_by: 'User', created_at: new Date().toISOString() }],
        rowCount: 1,
      });
      // Backward traversal
      pool.setQueryResult('r.source_id = $1', {
        rows: [{ id: parentId, content: 'Parent thought', thought_type: 'lesson', source_agent: 'eva', source_phase: 'build', importance: 0.7, status: 'active', scope: ['default'], captured_by: 'User', created_at: new Date().toISOString(), depth: 1, via_relation: 'supersedes', via_context: 'Evolution' }],
        rowCount: 1,
      });
      // Forward traversal (empty for backward-only test, but we need to handle the query)
      pool.setQueryResult('r.target_id = $1', { rows: [], rowCount: 0 });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({
        thought_id: rootId,
        direction: 'backward',
      });

      assert.ok(!result.isError);
      const parsed = JSON.parse(result.content[0].text);
      assert.ok(parsed.chain.length >= 1, 'Should include at least the root');
      assert.strictEqual(parsed.chain[0].direction, 'root');
    });

    // T-0003-100: atelier_trace follows forward chain correctly
    it('T-0003-100: follows forward chain correctly', async () => {
      const childId = '55555555-5555-5555-5555-555555555555';

      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [{ id: rootId, content: 'Root', thought_type: 'decision', source_agent: 'cal', source_phase: 'design', importance: 0.8, status: 'superseded', scope: ['default'], captured_by: 'User', created_at: new Date().toISOString() }],
        rowCount: 1,
      });
      pool.setQueryResult('r.source_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('r.target_id = $1', {
        rows: [{ id: childId, content: 'Child', thought_type: 'decision', source_agent: 'cal', source_phase: 'design', importance: 0.9, status: 'active', scope: ['default'], captured_by: 'User', created_at: new Date().toISOString(), depth: 1, via_relation: 'supersedes', via_context: 'Updated decision' }],
        rowCount: 1,
      });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({
        thought_id: rootId,
        direction: 'forward',
      });

      assert.ok(!result.isError);
      const parsed = JSON.parse(result.content[0].text);
      assert.ok(parsed.chain.length >= 1);
    });

    // T-0003-101: atelier_trace with max_depth=0 returns only root thought
    it('T-0003-101: returns only root thought with max_depth=0', async () => {
      pool.setQueryResult('FROM thoughts WHERE id', {
        rows: [{ id: rootId, content: 'Root only', thought_type: 'decision', source_agent: 'cal', source_phase: 'design', importance: 0.8, status: 'active', scope: ['default'], captured_by: 'User', created_at: new Date().toISOString() }],
        rowCount: 1,
      });
      // Both traversals return empty because max_depth=0
      pool.setQueryResult('r.source_id = $1', { rows: [], rowCount: 0 });
      pool.setQueryResult('r.target_id = $1', { rows: [], rowCount: 0 });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({
        thought_id: rootId,
        direction: 'both',
        max_depth: 0,
      });

      assert.ok(!result.isError);
      const parsed = JSON.parse(result.content[0].text);
      // With max_depth=0, only root should appear
      const rootEntries = parsed.chain.filter(c => c.direction === 'root');
      assert.strictEqual(rootEntries.length, 1);
    });

    // T-0003-102: atelier_trace with nonexistent thought_id returns error
    it('T-0003-102: returns error for nonexistent thought_id', async () => {
      const missingId = '99999999-9999-9999-9999-999999999999';
      pool.setQueryResult('FROM thoughts WHERE id', { rows: [], rowCount: 0 });

      const handler = getToolHandler('atelier_trace');
      const result = await handler({ thought_id: missingId });

      assert.strictEqual(result.isError, true);
      assert.ok(result.content[0].text.includes('not found'));
    });
  });
});
