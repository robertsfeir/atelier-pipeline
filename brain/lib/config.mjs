/**
 * Configuration resolution and constants.
 * Standalone module -- no dependencies on other lib/ modules.
 */

import { readFileSync } from "fs";
import { execSync } from "child_process";

// =============================================================================
// Constants (enums matching schema.sql)
// =============================================================================

const THOUGHT_TYPES = [
  "decision", "preference", "lesson", "rejection",
  "drift", "correction", "insight", "reflection", "handoff",
  "pattern", "seed",
];
const SOURCE_AGENTS = [
  // # non-extracted: eva orchestrates but does not submit agent_capture calls
  "eva",
  "robert", "sable", "colby",
  "agatha", "ellis",
  // # non-extracted: poirot is read-only, no brain captures
  "poirot",
  // # non-extracted: distillator compresses but does not capture decisions
  "distillator",
  "robert-spec", "sable-ux",
  // # non-extracted: sentinel has no automatic capture path; included in
  // SOURCE_AGENTS for Zod validation of any future captures
  "sentinel",
  // # non-pipeline-extracted: sarah submits no automatic agent_capture calls; source_agent used for manual captures
  "sarah",
  // # non-extracted: sherlock runs in fresh general-purpose isolation, read-only
  "sherlock",
];
const SOURCE_PHASES = [
  "design", "build", "qa", "review", "reconciliation", "setup", "handoff", "devops", "telemetry", "ci-watch", "pipeline",
  "product", "ux", "commit",
];
const THOUGHT_STATUSES = [
  "active", "superseded", "invalidated", "expired", "conflicted",
];
const RELATION_TYPES = [
  "supersedes", "triggered_by", "evolves_from",
  "contradicts", "supports", "synthesized_from",
];

const EMBEDDING_MODEL = "openai/text-embedding-3-small";

// =============================================================================
// Provider Defaults (ADR-0054)
// =============================================================================
//
// Three adapter families: openai-compat, anthropic (chat only), local.
// Per-family base URL + per-provider model defaults. Selecting an
// embedding_provider or chat_provider name maps to a (family, baseUrl, model)
// triple via PROVIDER_PRESETS below; explicit overrides in brain-config.json
// (embedding_base_url, embedding_model, chat_base_url, chat_model) win.

const PROVIDER_PRESETS = {
  // openai-compat family
  "openrouter": {
    family: "openai-compat",
    baseUrl: "https://openrouter.ai/api/v1",
    embeddingModel: "openai/text-embedding-3-small",
    chatModel: "openai/gpt-4o-mini",
  },
  "openai": {
    family: "openai-compat",
    baseUrl: "https://api.openai.com/v1",
    embeddingModel: "text-embedding-3-small",
    chatModel: "gpt-4o-mini",
  },
  "github-models": {
    family: "openai-compat",
    baseUrl: "https://models.github.ai/inference",
    embeddingModel: "openai/text-embedding-3-small",
    chatModel: "openai/gpt-4o-mini",
    extraHeaders: {
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2026-03-10",
    },
  },
  // anthropic family (chat only -- embeddings will be rejected by llm-provider)
  "anthropic": {
    family: "anthropic",
    baseUrl: "https://api.anthropic.com/v1",
    embeddingModel: null,
    chatModel: "claude-haiku-4-5-20251001",
  },
  // local family
  "local": {
    family: "local",
    baseUrl: "http://localhost:11434/v1",
    embeddingModel: "rjmalagon/gte-qwen2-1.5b-instruct-embed-f16",
    chatModel: "llama3.1",
  },
};

const DEFAULT_EMBEDDING_PROVIDER = "openrouter";
const DEFAULT_CHAT_PROVIDER = "openrouter";

// =============================================================================
// Config Resolution (project > user > env > none)
// =============================================================================

function resolveConfig() {
  const projectPath = process.env.BRAIN_CONFIG_PROJECT;
  const cwdPath = process.cwd() + "/.claude/brain-config.json";
  const userPath = process.env.BRAIN_CONFIG_USER;

  for (const configPath of [projectPath, cwdPath, userPath]) {
    if (!configPath) continue;
    try {
      const raw = readFileSync(configPath, "utf-8");
      const config = JSON.parse(raw);
      const resolved = {};
      for (const [key, value] of Object.entries(config)) {
        if (typeof value === "string" && value.includes("${")) {
          let missing = false;
          const result = value.replace(/\$\{([^}]+)\}/g, (_, envKey) => {
            const envVal = process.env[envKey];
            if (!envVal) {
              console.error(`Missing env var ${envKey} referenced in config`);
              missing = true;
              return "";
            }
            return envVal;
          });
          if (missing) return null;
          resolved[key] = result;
        } else {
          resolved[key] = value;
        }
      }
      resolved._source = configPath === projectPath ? "project" : configPath === cwdPath ? "project-cwd" : "personal";
      return resolved;
    } catch {
      continue;
    }
  }

  const dbUrl = process.env.DATABASE_URL || process.env.ATELIER_BRAIN_DATABASE_URL;
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (dbUrl) {
    return { database_url: dbUrl, openrouter_api_key: apiKey, _source: "env" };
  }

  return null;
}

// =============================================================================
// Provider Config Builder (ADR-0054)
// =============================================================================

/**
 * Build a providerConfig object suitable for `llm-provider.mjs` from the
 * resolved brain config plus an operation tag ("embed" or "chat").
 *
 * Backward compat: if the config has only `openrouter_api_key` set (the v3.x
 * shape), both operations resolve to OpenRouter with the historical defaults.
 * Newer configs may set `embedding_provider`, `embedding_model`,
 * `embedding_api_key`, `embedding_base_url`, and the `chat_*` equivalents
 * independently.
 *
 * Returns: { family, baseUrl, apiKey, model, extraHeaders }.
 */
function buildProviderConfig(config, operation) {
  if (operation !== "embed" && operation !== "chat") {
    throw new Error(`buildProviderConfig: operation must be "embed" or "chat", got "${operation}"`);
  }
  const cfg = config || {};

  // Provider name resolution
  const providerKey = operation === "embed" ? "embedding_provider" : "chat_provider";
  const providerName =
    cfg[providerKey] ||
    (operation === "embed" ? DEFAULT_EMBEDDING_PROVIDER : DEFAULT_CHAT_PROVIDER);

  const preset = PROVIDER_PRESETS[providerName];
  if (!preset) {
    throw new Error(
      `buildProviderConfig: unknown ${providerKey} "${providerName}" ` +
      `(expected one of: ${Object.keys(PROVIDER_PRESETS).join(", ")})`
    );
  }

  // Model resolution: explicit override > preset default
  const explicitModel =
    operation === "embed" ? cfg.embedding_model : cfg.chat_model;
  const model = explicitModel || (operation === "embed" ? preset.embeddingModel : preset.chatModel);

  // Base URL resolution: explicit override > preset default
  const explicitBaseUrl =
    operation === "embed" ? cfg.embedding_base_url : cfg.chat_base_url;
  const baseUrl = explicitBaseUrl || preset.baseUrl;

  // API key resolution:
  //   1. Explicit per-operation key if present (embedding_api_key / chat_api_key)
  //   2. Provider-specific keys (e.g. github_token for github-models, anthropic_api_key)
  //   3. Backward-compat: openrouter_api_key when provider is openrouter (or unset)
  //   4. local family is allowed to have no key
  let apiKey = null;
  const explicitKey =
    operation === "embed" ? cfg.embedding_api_key : cfg.chat_api_key;
  if (explicitKey) {
    apiKey = explicitKey;
  } else if (providerName === "openrouter") {
    apiKey = cfg.openrouter_api_key || null;
  } else if (providerName === "openai") {
    apiKey = cfg.openai_api_key || null;
  } else if (providerName === "github-models") {
    apiKey = cfg.github_token || cfg.github_models_api_key || null;
  } else if (providerName === "anthropic") {
    apiKey = cfg.anthropic_api_key || null;
  } else if (providerName === "local") {
    apiKey = cfg.local_api_key || null; // typically null
  }

  return {
    family: preset.family,
    baseUrl,
    apiKey,
    model,
    extraHeaders: preset.extraHeaders ? { ...preset.extraHeaders } : {},
    providerName,
  };
}

// =============================================================================
// Human Identity Resolution
// =============================================================================

function resolveIdentity() {
  const envUser = process.env.ATELIER_BRAIN_USER;
  if (envUser) return envUser;

  try {
    const name = execSync("git config user.name", { encoding: "utf-8", timeout: 5000 }).trim();
    const email = execSync("git config user.email", { encoding: "utf-8", timeout: 5000 }).trim();
    if (name && email) return `${name} <${email}>`;
    if (name) return name;
    if (email) return email;
  } catch {
    // git not available or not configured
  }

  return null;
}

export {
  resolveConfig,
  resolveIdentity,
  buildProviderConfig,
  THOUGHT_TYPES,
  SOURCE_AGENTS,
  SOURCE_PHASES,
  THOUGHT_STATUSES,
  RELATION_TYPES,
  EMBEDDING_MODEL,
  PROVIDER_PRESETS,
  DEFAULT_EMBEDDING_PROVIDER,
  DEFAULT_CHAT_PROVIDER,
};
