/**
 * LLM provider abstraction (ADR-0054).
 *
 * Single entry point for all LLM calls in the brain. Three adapter families:
 *   - openai-compat: OpenRouter, OpenAI-direct, GitHub Models. Identical wire
 *     format (OpenAI JSON shape), different base URL + Bearer auth + optional
 *     extra headers (GitHub Models requires Accept and X-GitHub-Api-Version).
 *   - anthropic: chat ONLY (Anthropic ships no embeddings API). Uses
 *     api.anthropic.com/v1/messages with x-api-key header. Response shape is
 *     normalized into the openai-compat shape so `assertLlmContent` works
 *     unchanged downstream.
 *   - local: Ollama / LM Studio / llama.cpp at localhost. openai-compat wire
 *     format, no auth header emitted when apiKey is empty/null.
 *
 * `embed(text, providerConfig)` -- returns Array<number>. Anthropic family is
 * rejected at this entry point with a clear error.
 *
 * `chat(messages, providerConfig)` -- returns the parsed JSON response in
 * openai-compat shape (`{ choices: [{ message: { content: ... } }] }`),
 * regardless of which family produced it. Callers continue to use
 * `assertLlmContent` from llm-response.mjs without modification.
 *
 * `verifyEmbeddingDimension(providerConfig, expectedDim = 1536)` -- single
 * end-to-end embed call; returns `{ ok, actual, expected, message? }`. Used by
 * brain-setup as the ADR-0054 "dimension drift" guard before any insert path
 * runs against a newly-configured embedding provider.
 *
 * The retry/backoff loop lives in callers (embed.mjs preserves its 3-attempt
 * loop). This module is one HTTP round-trip per call.
 */

// =============================================================================
// Defaults per family
// =============================================================================

const DEFAULT_BASE_URL = {
  "openai-compat": "https://openrouter.ai/api/v1",
  "anthropic": "https://api.anthropic.com/v1",
  "local": "http://localhost:11434/v1",
};

const ANTHROPIC_VERSION = "2023-06-01";
const GITHUB_MODELS_API_VERSION = "2026-03-10";

// =============================================================================
// Helpers
// =============================================================================

function normalizeProviderConfig(providerConfig, operation) {
  if (providerConfig == null) {
    throw new Error(`llm-provider: providerConfig is required for ${operation}`);
  }
  const family = providerConfig.family || "openai-compat";
  if (!DEFAULT_BASE_URL[family]) {
    throw new Error(
      `llm-provider: unknown adapter family "${family}" (expected one of: openai-compat, anthropic, local)`
    );
  }
  const baseUrl = (providerConfig.baseUrl || DEFAULT_BASE_URL[family]).replace(/\/+$/, "");
  return {
    family,
    baseUrl,
    apiKey: providerConfig.apiKey ?? null,
    model: providerConfig.model,
    extraHeaders: providerConfig.extraHeaders || {},
  };
}

function buildAuthHeaders(family, apiKey, extraHeaders) {
  const headers = { "Content-Type": "application/json", ...extraHeaders };
  if (family === "anthropic") {
    if (!apiKey) {
      throw new Error("llm-provider: anthropic adapter requires an apiKey");
    }
    headers["x-api-key"] = apiKey;
    headers["anthropic-version"] = ANTHROPIC_VERSION;
    return headers;
  }
  // openai-compat and local share the same auth scheme; local omits when no key.
  if (apiKey) {
    headers["Authorization"] = `Bearer ${apiKey}`;
  }
  return headers;
}

// =============================================================================
// embed(text, providerConfig)
// =============================================================================

async function embed(text, providerConfig) {
  const cfg = normalizeProviderConfig(providerConfig, "embed");
  if (cfg.family === "anthropic") {
    throw new Error(
      "llm-provider: anthropic family does not support embeddings (Anthropic has no embeddings API). " +
      "Configure embedding_provider as openrouter, openai, github-models, or local."
    );
  }
  if (!cfg.model) {
    throw new Error("llm-provider: embed() requires providerConfig.model");
  }

  const url = `${cfg.baseUrl}/embeddings`;
  const headers = buildAuthHeaders(cfg.family, cfg.apiKey, cfg.extraHeaders);
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ model: cfg.model, input: text }),
  });

  if (!res.ok) {
    const errBody = await res.text();
    const err = new Error(`Embedding API error: ${res.status} ${errBody}`);
    err.status = res.status;
    throw err;
  }

  const data = await res.json();
  if (!data || !Array.isArray(data.data) || data.data.length === 0) {
    throw new Error("Embedding API returned invalid response: missing data array");
  }
  const embedding = data.data[0].embedding;
  if (!Array.isArray(embedding)) {
    throw new Error("Embedding API returned invalid response: missing embedding vector");
  }
  return embedding;
}

// =============================================================================
// chat(messages, providerConfig, options)
// =============================================================================

async function chat(messages, providerConfig, options = {}) {
  const cfg = normalizeProviderConfig(providerConfig, "chat");
  if (!cfg.model) {
    throw new Error("llm-provider: chat() requires providerConfig.model");
  }

  if (cfg.family === "anthropic") {
    return chatAnthropic(messages, cfg, options);
  }
  return chatOpenAICompat(messages, cfg, options);
}

async function chatOpenAICompat(messages, cfg, options) {
  const url = `${cfg.baseUrl}/chat/completions`;
  const body = { model: cfg.model, messages };
  if (options.responseFormat) {
    body.response_format = options.responseFormat;
  }
  const headers = buildAuthHeaders(cfg.family, cfg.apiKey, cfg.extraHeaders);
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errBody = await res.text();
    const err = new Error(`Chat API error: ${res.status} ${errBody}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

async function chatAnthropic(messages, cfg, _options) {
  // Anthropic /v1/messages requires top-level system + user/assistant messages
  // (no role: "system" inside the messages array), and a max_tokens field.
  const systemMessages = messages.filter((m) => m.role === "system");
  const conversationMessages = messages.filter((m) => m.role !== "system");
  const body = {
    model: cfg.model,
    max_tokens: 4096,
    messages: conversationMessages,
  };
  if (systemMessages.length > 0) {
    body.system = systemMessages.map((m) => m.content).join("\n\n");
  }

  const url = `${cfg.baseUrl}/messages`;
  const headers = buildAuthHeaders(cfg.family, cfg.apiKey, cfg.extraHeaders);
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errBody = await res.text();
    const err = new Error(`Chat API error: ${res.status} ${errBody}`);
    err.status = res.status;
    throw err;
  }

  const data = await res.json();
  // Normalize anthropic shape -> openai-compat shape so assertLlmContent works.
  // Anthropic: { content: [{ type: "text", text: "..." }, ...], ... }
  let text = "";
  if (Array.isArray(data?.content)) {
    text = data.content
      .filter((c) => c && c.type === "text" && typeof c.text === "string")
      .map((c) => c.text)
      .join("");
  }
  return {
    choices: [{ message: { role: "assistant", content: text } }],
    _raw: data,
  };
}

// =============================================================================
// verifyEmbeddingDimension(providerConfig, expectedDim)
// =============================================================================

/**
 * Run a single end-to-end embed call against the configured provider and
 * verify the returned vector dimension matches the schema's expectation.
 *
 * Returns { ok: bool, actual: number|null, expected: number, message?: string }.
 * Never throws on a normal HTTP/auth error -- those are reported as
 * { ok: false, actual: null, message: "..." } so callers can present a clear
 * setup-time remediation. Programmer errors (missing model, unknown family)
 * still throw via normalizeProviderConfig.
 */
async function verifyEmbeddingDimension(providerConfig, expectedDim = 1536) {
  try {
    const vec = await embed("dimension probe", providerConfig);
    if (!Array.isArray(vec)) {
      return {
        ok: false,
        actual: null,
        expected: expectedDim,
        message: "Provider returned non-array response for embed probe.",
      };
    }
    const actual = vec.length;
    if (actual !== expectedDim) {
      return {
        ok: false,
        actual,
        expected: expectedDim,
        message:
          `Embedding dimension mismatch: provider returned ${actual}-dim, ` +
          `schema expects ${expectedDim}-dim. ` +
          `Either select a 1536-dim model (e.g. openai/text-embedding-3-small, ` +
          `gte-qwen2-1.5b-instruct) or run a schema migration before any insert.`,
      };
    }
    return { ok: true, actual, expected: expectedDim };
  } catch (err) {
    return {
      ok: false,
      actual: null,
      expected: expectedDim,
      message: `Embed probe failed: ${err.message}`,
    };
  }
}

// =============================================================================
// Exports
// =============================================================================

export {
  embed,
  chat,
  verifyEmbeddingDimension,
  DEFAULT_BASE_URL,
  GITHUB_MODELS_API_VERSION,
  ANTHROPIC_VERSION,
};
