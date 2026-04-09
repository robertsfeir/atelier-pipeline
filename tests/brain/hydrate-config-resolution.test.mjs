/**
 * tests/brain/hydrate-config-resolution.test.mjs
 *
 * Regression tests for the config-resolution gap between the brain MCP server
 * and the standalone hydrate-telemetry.mjs script.
 *
 * Root cause being guarded against:
 *   The MCP server receives BRAIN_CONFIG_USER and ATELIER_BRAIN_DB_PASSWORD via
 *   .mcp.json env injection. The standalone script inherits only the shell
 *   environment of the caller, which typically lacks DATABASE_URL and does NOT
 *   set BRAIN_CONFIG_USER. resolveConfig() therefore returns null and the script
 *   exits 1 with "No database configuration found."
 *
 * Fix contract (asserted below):
 *   resolveConfig() MUST succeed when run from the project root because
 *   lib/config.mjs probes `${cwd}/.claude/brain-config.json` as a second candidate.
 *   That file uses ${ATELIER_BRAIN_DB_PASSWORD} interpolation, so the env var
 *   ATELIER_BRAIN_DB_PASSWORD must also be present. Both conditions together
 *   are sufficient for the script to connect.
 *
 * The tests also document which env vars the MCP server receives (via .mcp.json)
 * but which a bare `node brain/scripts/hydrate-telemetry.mjs` invocation does NOT
 * receive, so the gap is machine-verifiable going forward.
 *
 * NOTE: Every test that exercises a specific config probe (project, user, env) must
 * redirect process.cwd() to a directory with no .claude/brain-config.json.
 * Without this, the cwd probe fires first and shadows the probe under test
 * whenever ATELIER_BRAIN_DB_PASSWORD happens to be set in the ambient environment.
 */

import { describe, it, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdirSync, mkdtempSync, rmSync } from "fs";
import path from "path";
import os from "os";

// Cache-busted dynamic import so each test gets a fresh module evaluation.
async function importConfig() {
  return await import(`../../brain/lib/config.mjs?t=${Date.now()}-${Math.random()}`);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build a minimal valid brain-config.json with a literal (no interpolation) URL. */
function writeLiteralConfig(filePath, overrides = {}) {
  writeFileSync(
    filePath,
    JSON.stringify({
      database_url: "postgresql://localhost:5432/testbrain",
      openrouter_api_key: "test-key",
      scope: "test.scope",
      ...overrides,
    })
  );
}

/** Build a brain-config.json whose database_url references an env var (production pattern). */
function writeInterpolatedConfig(filePath, envVarName = "ATELIER_BRAIN_DB_PASSWORD") {
  writeFileSync(
    filePath,
    JSON.stringify({
      database_url: `postgresql://user:\${${envVarName}}@host:5432/db?sslmode=require`,
      openrouter_api_key: "test-key",
      scope: "test.scope",
    })
  );
}

/**
 * Make an empty tmpDir that has no .claude subdirectory — used as a safe cwd
 * for tests that want to isolate BRAIN_CONFIG_PROJECT/BRAIN_CONFIG_USER probes
 * from the cwd probe.
 */
function makeEmptyCwd(parentDir) {
  const dir = path.join(parentDir, "empty-cwd");
  mkdirSync(dir, { recursive: true });
  return dir;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("hydrate-telemetry config resolution (MCP vs standalone gap)", () => {
  let savedEnv;
  let tmpDir;
  let emptyCwd;
  let originalCwd;

  beforeEach(() => {
    savedEnv = { ...process.env };
    tmpDir = mkdtempSync(path.join(os.tmpdir(), "hydrate-cfg-test-"));
    emptyCwd = makeEmptyCwd(tmpDir);
    originalCwd = process.cwd;

    // Clear every variable resolveConfig() reads so tests are isolated.
    delete process.env.BRAIN_CONFIG_PROJECT;
    delete process.env.BRAIN_CONFIG_USER;
    delete process.env.DATABASE_URL;
    delete process.env.ATELIER_BRAIN_DATABASE_URL;
    delete process.env.OPENROUTER_API_KEY;
    delete process.env.ATELIER_BRAIN_DB_PASSWORD;
  });

  afterEach(() => {
    // Restore process.cwd in case a test left it overridden after an assertion failure.
    process.cwd = originalCwd;

    for (const key of Object.keys(process.env)) {
      if (!(key in savedEnv)) delete process.env[key];
    }
    for (const [key, value] of Object.entries(savedEnv)) {
      process.env[key] = value;
    }
    try {
      rmSync(tmpDir, { recursive: true });
    } catch {
      /* ignore */
    }
  });

  // -------------------------------------------------------------------------
  // T-HC-001: The MCP path — BRAIN_CONFIG_USER points to a file that works.
  // process.cwd is redirected to a dir with no .claude so the cwd probe is
  // skipped and the BRAIN_CONFIG_USER probe is the one exercised.
  // -------------------------------------------------------------------------
  it(
    "T-HC-001: resolveConfig() succeeds when BRAIN_CONFIG_USER points to a valid config " +
      "(the mechanism .mcp.json uses for the MCP server)",
    async () => {
      const configPath = path.join(tmpDir, "brain-config.json");
      writeLiteralConfig(configPath);
      process.env.BRAIN_CONFIG_USER = configPath;

      // Redirect cwd to a dir with no .claude so the cwd probe is a no-op.
      process.cwd = () => emptyCwd;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(
        config,
        null,
        "resolveConfig() must not return null when BRAIN_CONFIG_USER is set correctly"
      );
      assert.ok(
        config.database_url,
        "config.database_url must be truthy when BRAIN_CONFIG_USER is set correctly"
      );
      assert.strictEqual(config._source, "personal");
    }
  );

  // -------------------------------------------------------------------------
  // T-HC-002: The production MCP pattern — interpolated URL + password env var.
  // -------------------------------------------------------------------------
  it(
    "T-HC-002: resolveConfig() resolves interpolated database_url when the referenced env var is set " +
      "(the exact production pattern in .claude/brain-config.json)",
    async () => {
      const configPath = path.join(tmpDir, "brain-config-interp.json");
      writeInterpolatedConfig(configPath, "ATELIER_BRAIN_DB_PASSWORD");

      process.env.BRAIN_CONFIG_USER = configPath;
      process.env.ATELIER_BRAIN_DB_PASSWORD = "secret-password";

      // Redirect cwd so the cwd probe does not shadow BRAIN_CONFIG_USER.
      process.cwd = () => emptyCwd;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(config, null, "Must resolve when password env var is set");
      assert.ok(
        config.database_url.includes("secret-password"),
        "database_url must contain the resolved password"
      );
      assert.ok(
        !config.database_url.includes("${ATELIER_BRAIN_DB_PASSWORD}"),
        "database_url must not contain the literal placeholder after resolution"
      );
    }
  );

  // -------------------------------------------------------------------------
  // T-HC-003: The gap — interpolated URL but password env var absent → null.
  // This is the exact failure mode the user reported.
  // The script gets no BRAIN_CONFIG_USER and no ATELIER_BRAIN_DB_PASSWORD,
  // so resolveConfig() returns null and the script exits 1.
  // -------------------------------------------------------------------------
  it(
    "T-HC-003: resolveConfig() returns null when the config file references ${ATELIER_BRAIN_DB_PASSWORD} " +
      "but that env var is absent — the exact condition that causes the script to fail",
    async () => {
      const configPath = path.join(tmpDir, "brain-config-missing-pw.json");
      writeInterpolatedConfig(configPath, "ATELIER_BRAIN_DB_PASSWORD");
      process.env.BRAIN_CONFIG_USER = configPath;
      // ATELIER_BRAIN_DB_PASSWORD is deliberately NOT set.

      // Redirect cwd so there's no ambient .claude/brain-config.json to fall back on.
      process.cwd = () => emptyCwd;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.strictEqual(
        config,
        null,
        "resolveConfig() must return null when a referenced env var is missing — " +
          "this is what causes the script to print 'No database configuration found'"
      );
    }
  );

  // -------------------------------------------------------------------------
  // T-HC-004: The cwd fallback path — script run from project root finds
  // .claude/brain-config.json automatically via cwdPath in resolveConfig().
  // -------------------------------------------------------------------------
  it(
    "T-HC-004: resolveConfig() discovers .claude/brain-config.json under cwd " +
      "when no BRAIN_CONFIG_PROJECT/BRAIN_CONFIG_USER is set " +
      "(the cwd probe that allows the script to self-configure from project root)",
    async () => {
      const fakeCwd = path.join(tmpDir, "fake-project");
      const claudeDir = path.join(fakeCwd, ".claude");
      mkdirSync(claudeDir, { recursive: true });
      writeLiteralConfig(path.join(claudeDir, "brain-config.json"));

      process.cwd = () => fakeCwd;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(
        config,
        null,
        "resolveConfig() must discover .claude/brain-config.json in cwd when no env vars are set"
      );
      assert.ok(
        config.database_url,
        "config.database_url must be truthy from cwd-discovered config"
      );
      assert.strictEqual(
        config._source,
        "project-cwd",
        "_source must be 'project-cwd' when config is found via cwd probe"
      );
    }
  );

  // -------------------------------------------------------------------------
  // T-HC-005: The cwd path + interpolated URL requires password env var too.
  // Documents that the cwd fix alone is insufficient without the password.
  // -------------------------------------------------------------------------
  it(
    "T-HC-005: resolveConfig() returns null even with .claude/brain-config.json in cwd " +
      "when the file uses ${ATELIER_BRAIN_DB_PASSWORD} interpolation and the var is absent " +
      "(the script must also export ATELIER_BRAIN_DB_PASSWORD to fully work)",
    async () => {
      const fakeCwd = path.join(tmpDir, "fake-project-interp");
      const claudeDir = path.join(fakeCwd, ".claude");
      mkdirSync(claudeDir, { recursive: true });
      writeInterpolatedConfig(path.join(claudeDir, "brain-config.json"), "ATELIER_BRAIN_DB_PASSWORD");
      // ATELIER_BRAIN_DB_PASSWORD deliberately absent.

      process.cwd = () => fakeCwd;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.strictEqual(
        config,
        null,
        "resolveConfig() must still return null if the cwd config has missing env-var interpolation"
      );
    }
  );

  // -------------------------------------------------------------------------
  // T-HC-006: The cwd path + interpolated URL succeeds when password env var IS set.
  // This is the fully-working state after the fix.
  // -------------------------------------------------------------------------
  it(
    "T-HC-006: resolveConfig() resolves successfully with .claude/brain-config.json in cwd " +
      "AND ATELIER_BRAIN_DB_PASSWORD set — the complete working state after the fix",
    async () => {
      const fakeCwd = path.join(tmpDir, "fake-project-full");
      const claudeDir = path.join(fakeCwd, ".claude");
      mkdirSync(claudeDir, { recursive: true });
      writeInterpolatedConfig(path.join(claudeDir, "brain-config.json"), "ATELIER_BRAIN_DB_PASSWORD");
      process.env.ATELIER_BRAIN_DB_PASSWORD = "my-db-password";

      process.cwd = () => fakeCwd;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(config, null, "Must resolve with cwd config + password env var");
      assert.ok(
        config.database_url.includes("my-db-password"),
        "Resolved URL must include the interpolated password"
      );
      assert.strictEqual(config._source, "project-cwd");
    }
  );

  // -------------------------------------------------------------------------
  // T-HC-007: session-hydrate.sh does NOT forward BRAIN_CONFIG_USER or
  // ATELIER_BRAIN_DB_PASSWORD to the node process — documenting the env gap.
  // -------------------------------------------------------------------------
  it(
    "T-HC-007: session-hydrate.sh does not export BRAIN_CONFIG_USER or ATELIER_BRAIN_DB_PASSWORD " +
      "to the node process, meaning the script relies entirely on cwd-discovery + password env var",
    async () => {
      const { readFileSync } = await import("fs");
      let hookContent = null;
      const candidates = [
        new URL("../../source/claude/hooks/session-hydrate.sh", import.meta.url).pathname,
        new URL("../../.claude/hooks/session-hydrate.sh", import.meta.url).pathname,
      ];
      for (const p of candidates) {
        try {
          hookContent = readFileSync(p, "utf-8");
          break;
        } catch {
          // try next
        }
      }

      assert.ok(hookContent !== null, "session-hydrate.sh must exist at source or installed path");

      assert.ok(
        !hookContent.includes("DATABASE_URL="),
        "session-hydrate.sh must not hardcode DATABASE_URL — config resolution belongs in config.mjs"
      );

      assert.ok(
        !hookContent.includes("BRAIN_CONFIG_USER="),
        "session-hydrate.sh must not set BRAIN_CONFIG_USER inline"
      );

      assert.ok(
        hookContent.includes("node ") || hookContent.includes("node\t"),
        "session-hydrate.sh must invoke node (not a wrapper) to allow env inheritance"
      );
    }
  );

  // -------------------------------------------------------------------------
  // T-HC-008: The script exits with a specific error message when config is missing.
  // -------------------------------------------------------------------------
  it(
    "T-HC-008: hydrate-telemetry.mjs main() error gate text matches 'No database configuration found' " +
      "so the user-facing error is diagnosable without reading source",
    async () => {
      const { readFileSync } = await import("fs");
      const scriptPath = new URL("../../brain/scripts/hydrate-telemetry.mjs", import.meta.url).pathname;
      const scriptContent = readFileSync(scriptPath, "utf-8");

      assert.ok(
        scriptContent.includes("No database configuration found"),
        "hydrate-telemetry.mjs must print 'No database configuration found' when resolveConfig() returns null"
      );

      assert.ok(
        scriptContent.includes("BRAIN_CONFIG_PROJECT") ||
          scriptContent.includes("BRAIN_CONFIG_USER") ||
          scriptContent.includes("DATABASE_URL"),
        "The error message or surrounding code must reference the config vars so users know what to set"
      );
    }
  );
});
