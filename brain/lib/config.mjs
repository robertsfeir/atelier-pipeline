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
  "eva", "cal", "robert", "sable", "colby",
  "roz", "poirot", "agatha", "distillator", "ellis",
];
const SOURCE_PHASES = [
  "design", "build", "qa", "review", "reconciliation", "setup", "handoff", "devops", "telemetry", "ci-watch", "pipeline",
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
  THOUGHT_TYPES,
  SOURCE_AGENTS,
  SOURCE_PHASES,
  THOUGHT_STATUSES,
  RELATION_TYPES,
  EMBEDDING_MODEL,
};
