/**
 * Embedding generation via OpenRouter API.
 * Depends on: config.mjs (receives apiKey as parameter).
 */

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
// Embedding Generation
// =============================================================================

async function getEmbedding(text, apiKey) {
  let lastError;

  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    try {
      const res = await fetch("https://openrouter.ai/api/v1/embeddings", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ model: EMBEDDING_MODEL, input: text }),
      });

      if (!res.ok) {
        const errBody = await res.text();
        const err = new Error(`Embedding API error: ${res.status} ${errBody}`);

        if (!isRetryable(res.status)) {
          throw err;
        }
        lastError = err;
        if (attempt < MAX_ATTEMPTS - 1) {
          await sleep(BACKOFF_MS[attempt]);
          continue;
        }
        throw lastError;
      }

      const data = await res.json();

      if (!data.data || !Array.isArray(data.data) || data.data.length === 0) {
        throw new Error(
          "Embedding API returned invalid response: missing data array"
        );
      }

      const embedding = data.data[0].embedding;
      if (!Array.isArray(embedding)) {
        throw new Error(
          "Embedding API returned invalid response: missing embedding vector"
        );
      }

      return embedding;
    } catch (err) {
      lastError = err;
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
