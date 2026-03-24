/**
 * Atelier Brain -- MCP Server Entry Point
 * Persistent institutional memory for atelier-pipeline agents.
 *
 * This is the startup orchestrator. All logic lives in brain/lib/ modules:
 *   config.mjs, db.mjs, embed.mjs, conflict.mjs, tools.mjs,
 *   rest-api.mjs, consolidation.mjs, ttl.mjs, static.mjs
 *
 * ADR: docs/architecture/ADR-0001-atelier-brain.md
 * Modularization: docs/architecture/ADR-0003-code-quality-overhaul.md (Step 5)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createServer } from "http";
import crypto from "crypto";

import { resolveConfig, resolveIdentity } from "./lib/config.mjs";
import { createPool, runMigrations } from "./lib/db.mjs";
import { registerTools } from "./lib/tools.mjs";
import { createRestHandler } from "./lib/rest-api.mjs";
import { startConsolidationTimer, stopConsolidationTimer } from "./lib/consolidation.mjs";
import { startTTLTimer, stopTTLTimer } from "./lib/ttl.mjs";
import { handleStaticFile } from "./lib/static.mjs";

// =============================================================================
// Configuration
// =============================================================================

const config = resolveConfig();
if (!config) {
  console.log("No brain config found. Brain disabled.");
  process.exit(0);
}

const DATABASE_URL = config.database_url;
const API_TOKEN = process.env.ATELIER_BRAIN_API_TOKEN || null;
const OPENROUTER_API_KEY = config.openrouter_api_key || process.env.OPENROUTER_API_KEY;

if (!OPENROUTER_API_KEY) {
  console.error("Missing OPENROUTER_API_KEY. Brain cannot generate embeddings.");
  process.exit(1);
}

const CAPTURED_BY = resolveIdentity();

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
  openrouter_api_key: OPENROUTER_API_KEY,
  apiToken: API_TOKEN,
  capturedBy: CAPTURED_BY,
};

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
// Graceful Shutdown
// =============================================================================

function gracefulShutdown() {
  stopConsolidationTimer();
  stopTTLTimer();
  pool.end().catch(() => {});
  process.exit(0);
}

process.on("SIGTERM", gracefulShutdown);
process.on("SIGINT", gracefulShutdown);

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
    console.log(`Atelier Brain MCP server running on http://localhost:${PORT} (config: ${cfg._source})`);
    if (!cfg.apiToken) {
      console.warn("WARNING: ATELIER_BRAIN_API_TOKEN not set — REST API running without authentication (dev mode)");
    }
    await startTTLTimer(pool).catch(err => console.error("TTL timer start failed:", err.message));
    await startConsolidationTimer(pool, cfg.openrouter_api_key).catch(err => console.error("Consolidation timer start failed:", err.message));
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
  await startConsolidationTimer(pool, cfg.openrouter_api_key).catch(err => console.error("Consolidation timer start failed:", err.message));
}
