/**
 * Tests for brain/lib/embed.mjs
 * Test IDs: T-0003-076 through T-0003-078
 */

import { describe, it, beforeEach, afterEach, mock } from 'node:test';
import assert from 'node:assert/strict';
import { createEmbeddingResponse, createMockFetch } from './helpers/mock-fetch.mjs';

// Import the module under test
import { getEmbedding } from '../../brain/lib/embed.mjs';

describe('embed.mjs', () => {
  let originalFetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  // T-0003-076: getEmbedding() with valid API key returns 1536-dim array
  it('T-0003-076: returns 1536-dimensional embedding array with valid API key', async () => {
    const embeddingResponse = createEmbeddingResponse(1536);
    globalThis.fetch = createMockFetch({
      'embeddings': { status: 200, body: embeddingResponse },
    });

    const result = await getEmbedding('test content', 'valid-api-key');

    assert.ok(Array.isArray(result), 'Result should be an array');
    assert.strictEqual(result.length, 1536, 'Embedding should have 1536 dimensions');
    assert.strictEqual(typeof result[0], 'number', 'Each element should be a number');
  });

  // T-0003-077: getEmbedding() with invalid API key throws Error
  it('T-0003-077: throws Error with invalid API key (non-200 response)', async () => {
    globalThis.fetch = createMockFetch({
      'embeddings': { status: 401, body: 'Unauthorized - invalid API key' },
    });

    await assert.rejects(
      () => getEmbedding('test content', 'invalid-key'),
      (err) => {
        assert.ok(err instanceof Error);
        assert.ok(err.message.includes('Embedding API error'), `Expected error about API, got: ${err.message}`);
        assert.ok(err.message.includes('401'), `Expected 401 status in error, got: ${err.message}`);
        return true;
      }
    );
  });

  // T-0003-078: getEmbedding() with network failure throws Error
  it('T-0003-078: throws Error on network failure', async () => {
    globalThis.fetch = createMockFetch({
      'embeddings': { error: new Error('Network error: ECONNREFUSED') },
    });

    await assert.rejects(
      () => getEmbedding('test content', 'valid-key'),
      (err) => {
        assert.ok(err instanceof Error);
        assert.ok(err.message.includes('ECONNREFUSED'), `Expected network error, got: ${err.message}`);
        return true;
      }
    );
  });

  // Edge case: sends correct request format
  it('sends correct request format to OpenRouter API', async () => {
    const mockFetch = createMockFetch({
      'embeddings': { status: 200, body: createEmbeddingResponse() },
    });
    globalThis.fetch = mockFetch;

    await getEmbedding('Hello world', 'my-api-key');

    assert.strictEqual(mockFetch.calls.length, 1);
    const call = mockFetch.calls[0];
    assert.ok(call.url.includes('openrouter.ai/api/v1/embeddings'));
    assert.strictEqual(call.options.method, 'POST');

    const headers = call.options.headers;
    assert.strictEqual(headers['Authorization'], 'Bearer my-api-key');
    assert.strictEqual(headers['Content-Type'], 'application/json');

    const body = JSON.parse(call.options.body);
    assert.strictEqual(body.input, 'Hello world');
    assert.ok(body.model, 'Should include model in request body');
  });

  // Edge case: unicode content
  it('handles unicode content like "Jose Garcia" and "Li Ming"', async () => {
    globalThis.fetch = createMockFetch({
      'embeddings': { status: 200, body: createEmbeddingResponse() },
    });

    const result = await getEmbedding('Decision by Jose Garcia and 李明', 'valid-key');
    assert.ok(Array.isArray(result));
    assert.strictEqual(result.length, 1536);
  });
});
