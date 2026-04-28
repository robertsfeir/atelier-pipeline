/**
 * Atelier Brain -- MCP Server Entry Point
 * Persistent institutional memory for atelier-pipeline agents.
 *
 * This is the startup orchestrator. All logic lives in brain/lib/ modules:
 *   config.mjs, db.mjs, embed.mjs, conflict.mjs, tools.mjs,
 *   rest-api.mjs, consolidation.mjs, ttl.mjs, static.mjs
 *
 * ADR: docs/brain/ADR-0001-atelier-brain.md
 * Modularization: docs/architecture/ADR-0003-code-quality-overhaul.md (Step 5)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createServer } from "http";
import crypto from "crypto";

import { resolveConfig, resolveIdentity, buildProviderConfig } from "./lib/config.mjs";
import { verifyEmbeddingDimension } from "./lib/llm-provider.mjs";
import { createPool, runMigrations } from "./lib/db.mjs";
import { registerTools } from "./lib/tools.mjs";
import { createRestHandler } from "./lib/rest-api.mjs";
import { startConsolidationTimer, stopConsolidationTimer } from "./lib/consolidation.mjs";
import { startTTLTimer, stopTTLTimer } from "./lib/ttl.mjs";
import { handleStaticFile } from "./lib/static.mjs";
import { installCrashGuards } from "./lib/crash-guards.mjs";

// Guarantee TLS relaxation reaches this process regardless of how it was launched.
process.env.NODE_TLS_REJECT_UNAUTHORIZED = process.env.NODE_TLS_REJECT_UNAUTHORIZED || '0';

// =============================================================================
// Configuration
// =============================================================================

const config = resolveConfig();
if (!config) {
  console.error("No brain config found. Brain disabled.");
  process.exit(0);
}

const DATABASE_URL = config.database_url;
const API_TOKEN = process.env.ATELIER_BRAIN_API_TOKEN || null;

// Backward-compat: surface OPENROUTER_API_KEY from env into the config so
// pre-ADR-0054 setups (only `openrouter_api_key` configured) continue to work.
if (!config.openrouter_api_key && process.env.OPENROUTER_API_KEY) {
  config.openrouter_api_key = process.env.OPENROUTER_API_KEY;
}

// =============================================================================
// Provider Config Resolution (ADR-0054)
// =============================================================================
//
// Build the embed and chat provider configs once at startup. These objects
// flow into modules via runtimeConfig and replace the legacy single
// OPENROUTER_API_KEY string. Validation:
//   - anthropic family is rejected as embedding provider (no embeddings API).
//   - non-local providers without a key are rejected.

const embedProviderConfig = buildProviderConfig(config, "embed");
const chatProviderConfig = buildProviderConfig(config, "chat");

if (embedProviderConfig.family === "anthropic") {
  console.error(
    "Configuration error: embedding_provider cannot be \"anthropic\" -- " +
    "Anthropic ships no embeddings API. Use openrouter, openai, github-models, " +
    "or local for embedding_provider."
  );
  process.exit(1);
}

if (embedProviderConfig.family !== "local" && !embedProviderConfig.apiKey) {
  console.error(
    `Missing API key for embedding provider "${embedProviderConfig.providerName}". ` +
    "Brain cannot generate embeddings. Set the appropriate API key in brain-config.json " +
    "or environment, or switch embedding_provider to \"local\"."
  );
  process.exit(1);
}

if (chatProviderConfig.family !== "local" && !chatProviderConfig.apiKey) {
  console.error(
    `Missing API key for chat provider "${chatProviderConfig.providerName}". ` +
    "Brain cannot run conflict classification or consolidation. Set the appropriate " +
    "API key in brain-config.json or environment, or switch chat_provider to \"local\"."
  );
  process.exit(1);
}

const CAPTURED_BY = resolveIdentity();

// =============================================================================
// Embedding Dimension Verification (ADR-0054, non-blocking)
// =============================================================================
//
// Best-effort pre-flight: probe the configured embed provider and warn if the
// returned vector dimension doesn't match the schema's 1536-dim expectation.
// Wrapped in a 5-second AbortSignal race so a slow or unavailable provider
// (Ollama not running, network latency) never blocks startup.

{
  const PROBE_TIMEOUT_MS = 5000;
  const timeoutId = setTimeout(() => {}, PROBE_TIMEOUT_MS); // keep event loop alive briefly
  try {
    const dimCheck = await Promise.race([
      verifyEmbeddingDimension(embedProviderConfig),
      new Promise((resolve) =>
        setTimeout(
          () => resolve({ ok: false, actual: null, expected: 1536, message: "Embed probe timed out after 5s" }),
          PROBE_TIMEOUT_MS
        )
      ),
    ]);
    if (!dimCheck.ok) {
      console.warn(
        `[brain] Embedding dimension warning: ${dimCheck.message} ` +
        "(startup continues — insert paths will surface the error downstream)"
      );
    }
  } catch (err) {
    console.warn(`[brain] Embedding dimension probe failed: ${err.message} (startup continues)`);
  } finally {
    clearTimeout(timeoutId);
  }
}

// =============================================================================
// Database Init
// =============================================================================

const pool = createPool(DATABASE_URL);
await runMigrations(pool);

// =============================================================================
// Shared Config Object (passed to modules that need runtime config)
// =============================================================================

const runtimeConfig = {
  ...config,
  // Backward-compat: openrouter_api_key remains on runtimeConfig so legacy
  // call sites (tools.mjs, hydrate scripts) keep working unchanged. New code
  // should consume embedProviderConfig / chatProviderConfig instead.
  openrouter_api_key: config.openrouter_api_key || null,
  embedProviderConfig,
  chatProviderConfig,
  apiToken: API_TOKEN,
  capturedBy: CAPTURED_BY,
};

// =============================================================================
// Process-Level Crash Guards (ADR-0017 Step 1)
// =============================================================================

installCrashGuards({
  exitFn: process.exit.bind(process),
  stopConsolidation: stopConsolidationTimer,
  stopTTL: stopTTLTimer,
  poolEnd: () => pool.end(),
});

// =============================================================================
// Server Startup
// =============================================================================

const mode = process.argv[2] || "stdio";

if (mode === "http") {
  startHttpMode(pool, runtimeConfig);
} else {
  await startStdioMode(pool, runtimeConfig);
}

// =============================================================================
// HTTP Mode
// =============================================================================

function startHttpMode(pool, cfg) {
  const PORT = process.env.PORT || 8788;
  const httpSessions = new Map();
  const handleRestApi = createRestHandler(pool, cfg);

  function createSessionTransport() {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => crypto.randomUUID(),
      onsessioninitialized: (sessionId) => {
        httpSessions.set(sessionId, transport);
      },
    });
    transport.onclose = () => {
      if (transport.sessionId) httpSessions.delete(transport.sessionId);
    };
    return transport;
  }

  const httpServer = createServer(async (req, res) => {
    try {
      res.setHeader("Access-Control-Allow-Origin", `http://localhost:${PORT}`);
      res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, mcp-session-id");
      res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");

      if (req.method === "OPTIONS") { res.writeHead(204); res.end(); return; }

      if (req.url.startsWith("/ui") && req.method === "GET") {
        if (handleStaticFile(req, res, cfg.apiToken)) return;
      }

      if (req.url.startsWith("/api/")) {
        const handled = await handleRestApi(req, res);
        if (handled) return;
      }

      await handleMcpRequest(req, res, httpSessions, createSessionTransport, pool, cfg);
    } catch (err) {
      console.error("Request error:", err.message);
      if (!res.headersSent) {
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: err.message }));
      }
    }
  });

  httpServer.listen(PORT, async () => {
    console.error(`Atelier Brain MCP server running on http://localhost:${PORT} (config: ${cfg._source})`);
    if (!cfg.apiToken) {
      console.warn("WARNING: ATELIER_BRAIN_API_TOKEN not set — REST API running without authentication (dev mode)");
    }
    await startTTLTimer(pool).catch(err => console.error("TTL timer start failed:", err.message));
    await startConsolidationTimer(pool, {
      embedConfig: cfg.embedProviderConfig,
      chatConfig: cfg.chatProviderConfig,
    }).catch(err => console.error("Consolidation timer start failed:", err.message));
  });
}

// =============================================================================
// MCP Request Routing (HTTP mode)
// =============================================================================

async function handleMcpRequest(req, res, httpSessions, createSessionTransport, pool, cfg) {
  const sessionId = req.headers["mcp-session-id"];

  if (sessionId && httpSessions.has(sessionId)) {
    await httpSessions.get(sessionId).handleRequest(req, res);
    return;
  }

  if (sessionId && !httpSessions.has(sessionId)) {
    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ jsonrpc: "2.0", error: { code: -32000, message: "Session not found" }, id: null }));
    return;
  }

  if (req.method === "POST") {
    const transport = createSessionTransport();
    const mcpServer = new McpServer({ name: "atelier-brain", version: "1.0.0" });
    registerTools(mcpServer, pool, cfg);
    await mcpServer.connect(transport);
    await transport.handleRequest(req, res);
    return;
  }

  res.writeHead(405, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "Method not allowed" }));
}

// =============================================================================
// Stdio Mode
// =============================================================================

async function startStdioMode(pool, cfg) {
  const server = new McpServer({ name: "atelier-brain", version: "1.0.0" });
  registerTools(server, pool, cfg);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  await startTTLTimer(pool).catch(err => console.error("TTL timer start failed:", err.message));
  await startConsolidationTimer(pool, {
    embedConfig: cfg.embedProviderConfig,
    chatConfig: cfg.chatProviderConfig,
  }).catch(err => console.error("Consolidation timer start failed:", err.message));
}
