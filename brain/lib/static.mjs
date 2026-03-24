/**
 * Static file serving for the Settings UI.
 * Standalone module -- no dependencies on other lib/ modules.
 */

import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import path from "path";

// =============================================================================
// Constants
// =============================================================================

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
};

const BRAIN_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const UI_DIR = path.join(BRAIN_DIR, "ui");

// =============================================================================
// Static File Handler
// =============================================================================

function handleStaticFile(req, res, apiToken) {
  let urlPath = new URL(req.url, `http://${req.headers.host}`).pathname;

  if (!urlPath.startsWith("/ui")) return false;

  let relativePath = urlPath.slice("/ui".length) || "/index.html";
  if (relativePath === "/") relativePath = "/index.html";

  const ext = path.extname(relativePath);
  const contentType = MIME_TYPES[ext];
  if (!contentType) {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found");
    return true;
  }

  const filePath = path.join(UI_DIR, relativePath);

  // Prevent directory traversal
  if (!filePath.startsWith(UI_DIR)) {
    res.writeHead(403, { "Content-Type": "text/plain" });
    res.end("Forbidden");
    return true;
  }

  if (!existsSync(filePath)) {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found");
    return true;
  }

  try {
    const isText = ext === ".html" || ext === ".css" || ext === ".js";
    let content = readFileSync(filePath, isText ? "utf-8" : undefined);
    if (ext === ".html" && apiToken) {
      content = content.replace(
        "</head>",
        `<script>window.__ATELIER_API_TOKEN__ = ${JSON.stringify(apiToken)};</script>\n</head>`
      );
    }
    res.writeHead(200, { "Content-Type": contentType });
    res.end(content);
  } catch {
    res.writeHead(500, { "Content-Type": "text/plain" });
    res.end("Internal server error");
  }
  return true;
}

export { handleStaticFile };
