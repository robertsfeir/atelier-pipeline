/**
 * Embedding generation -- routes through llm-provider.mjs (ADR-0054).
 *
 * Public signature:
 *   getEmbedding(text, providerConfigOrApiKey)
 *
 * Backward-compat shim: when the second argument is a string, it is treated
 * as a legacy OpenRouter apiKey and wrapped into the openai-compat provider
 * config used before ADR-0054. New callers pass a providerConfig object built
 * via `buildProviderConfig(config, "embed")` in config.mjs.
 *
 * The retry/backoff loop lives here, not in llm-provider.mjs -- the provider
 * module is one round-trip per call so the embed-specific retry policy stays
 * with embed-specific concerns.
 */

import { embed as providerEmbed } from "./llm-provider.mjs";
import { EMBEDDING_MODEL } from "./config.mjs";

// =============================================================================
// Retry Configuration
// =============================================================================

const MAX_ATTEMPTS = 3;
const BACKOFF_MS = [1000, 2000, 4000];

function isRetryable(status) {
  return status >= 500 || status === 429;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// =============================================================================
// Backward-compat: lift a bare apiKey string into a providerConfig
// =============================================================================

function coerceProviderConfig(providerConfigOrApiKey) {
  if (
    providerConfigOrApiKey != null &&
    typeof providerConfigOrApiKey === "object"
  ) {
    return providerConfigOrApiKey;
  }
  // Legacy: string apiKey -> default OpenRouter openai-compat config.
  return {
    family: "openai-compat",
    baseUrl: "https://openrouter.ai/api/v1",
    apiKey: providerConfigOrApiKey || null,
    model: EMBEDDING_MODEL,
    extraHeaders: {},
  };
}

// =============================================================================
// Embedding Generation
// =============================================================================

async function getEmbedding(text, providerConfigOrApiKey) {
  const providerConfig = coerceProviderConfig(providerConfigOrApiKey);
  let lastError;

  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    try {
      return await providerEmbed(text, providerConfig);
    } catch (err) {
      lastError = err;

      // HTTP errors carry a numeric .status from llm-provider.mjs
      if (typeof err.status === "number") {
        if (!isRetryable(err.status)) {
          throw err;
        }
        if (attempt < MAX_ATTEMPTS - 1) {
          await sleep(BACKOFF_MS[attempt]);
          continue;
        }
        throw lastError;
      }

      // Network-class errors -- retry up to MAX_ATTEMPTS
      const isNetworkError =
        err.name === "TypeError" ||
        err.code === "ECONNRESET" ||
        err.code === "ECONNREFUSED" ||
        err.code === "ETIMEDOUT" ||
        err.code === "UND_ERR_CONNECT_TIMEOUT";

      if (isNetworkError && attempt < MAX_ATTEMPTS - 1) {
        await sleep(BACKOFF_MS[attempt]);
        continue;
      }
      throw lastError;
    }
  }

  throw lastError;
}

export { getEmbedding };
