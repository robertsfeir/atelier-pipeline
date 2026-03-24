/**
 * Mock fetch helpers for brain module unit tests.
 * Provides configurable responses for embedding and LLM API calls.
 */

/**
 * Creates a mock embedding response (OpenRouter format).
 * @param {number} dimensions - Number of dimensions (default 1536)
 * @returns {object} Response body matching OpenRouter embedding API shape
 */
function createEmbeddingResponse(dimensions = 1536) {
  const embedding = new Array(dimensions).fill(0).map((_, i) => Math.sin(i * 0.1));
  return {
    data: [{ embedding }],
  };
}

/**
 * Creates a mock LLM chat completion response (OpenRouter format).
 * @param {string} content - The content of the LLM response
 * @returns {object} Response body matching OpenRouter chat completions API shape
 */
function createLLMResponse(content) {
  return {
    choices: [{
      message: { content },
    }],
  };
}

/**
 * Creates a mock conflict classification LLM response.
 * @param {string} classification - One of: DUPLICATE, CONTRADICTION, COMPLEMENT, SUPERSESSION, NOVEL
 * @param {number} confidence - Confidence score 0-1
 * @param {string} reasoning - Reasoning text
 * @returns {object} Response body matching OpenRouter chat completions API shape with JSON content
 */
function createConflictClassificationResponse(classification, confidence = 0.9, reasoning = "Test classification") {
  return createLLMResponse(JSON.stringify({
    classification,
    confidence,
    reasoning,
  }));
}

/**
 * Creates a mock consolidation synthesis LLM response.
 * @param {string} synthesis - The synthesized text
 * @returns {object} Response body matching OpenRouter chat completions API shape
 */
function createSynthesisResponse(synthesis = "Synthesized insight from multiple observations.") {
  return createLLMResponse(synthesis);
}

/**
 * Creates a mock fetch function that routes responses based on URL.
 * @param {object} routes - Map of URL patterns to response configs
 * @returns {Function} Mock fetch function
 *
 * Route config shape:
 *   { status: 200, body: { ... } }           - successful JSON response
 *   { status: 401, body: "Unauthorized" }     - error response
 *   { error: new Error("Network error") }     - network failure
 *
 * Example:
 *   const mockFetch = createMockFetch({
 *     'embeddings': { status: 200, body: createEmbeddingResponse() },
 *     'chat/completions': { status: 200, body: createLLMResponse("hello") },
 *   });
 */
function createMockFetch(routes = {}) {
  const calls = [];

  async function mockFetch(url, options) {
    calls.push({ url, options });

    for (const [pattern, config] of Object.entries(routes)) {
      if (url.includes(pattern)) {
        if (config.error) {
          throw config.error;
        }
        const status = config.status || 200;
        const body = config.body || {};
        return {
          ok: status >= 200 && status < 300,
          status,
          text: async () => typeof body === 'string' ? body : JSON.stringify(body),
          json: async () => typeof body === 'string' ? JSON.parse(body) : body,
        };
      }
    }

    // Default: 404 for unmatched URLs
    return {
      ok: false,
      status: 404,
      text: async () => "Not found",
      json: async () => ({ error: "Not found" }),
    };
  }

  mockFetch.calls = calls;
  mockFetch.reset = () => { calls.length = 0; };

  return mockFetch;
}

export {
  createEmbeddingResponse,
  createLLMResponse,
  createConflictClassificationResponse,
  createSynthesisResponse,
  createMockFetch,
};
