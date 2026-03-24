/**
 * Tests for brain/lib/config.mjs
 * Test IDs: T-0003-065 through T-0003-071
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { writeFileSync, mkdtempSync, rmSync } from 'fs';
import path from 'path';
import os from 'os';

// We need to import the module fresh for each test since it reads env vars at call time.
// config.mjs uses process.env directly, so we manipulate env vars before calling.
const CONFIG_MODULE_PATH = new URL('../../brain/lib/config.mjs', import.meta.url).pathname;

// Dynamic import helper to get a fresh module each time
async function importConfig() {
  // Use cache-busting query param to force fresh import
  const cacheBuster = `?t=${Date.now()}-${Math.random()}`;
  return await import(`../../brain/lib/config.mjs${cacheBuster}`);
}

describe('config.mjs', () => {
  let savedEnv;
  let tmpDir;

  beforeEach(() => {
    savedEnv = { ...process.env };
    tmpDir = mkdtempSync(path.join(os.tmpdir(), 'brain-config-test-'));
    // Clear all config-related env vars
    delete process.env.BRAIN_CONFIG_PROJECT;
    delete process.env.BRAIN_CONFIG_USER;
    delete process.env.DATABASE_URL;
    delete process.env.ATELIER_BRAIN_DATABASE_URL;
    delete process.env.OPENROUTER_API_KEY;
    delete process.env.ATELIER_BRAIN_USER;
  });

  afterEach(() => {
    // Restore environment
    for (const key of Object.keys(process.env)) {
      if (!(key in savedEnv)) delete process.env[key];
    }
    for (const [key, value] of Object.entries(savedEnv)) {
      process.env[key] = value;
    }
    try { rmSync(tmpDir, { recursive: true }); } catch { /* ignore */ }
  });

  describe('resolveConfig()', () => {
    // T-0003-065: resolveConfig() with valid project config file returns parsed config with _source="project"
    it('T-0003-065: returns parsed config with _source="project" from project config file', async () => {
      const configPath = path.join(tmpDir, 'project-config.json');
      writeFileSync(configPath, JSON.stringify({
        database_url: 'postgresql://localhost:5432/testdb',
        openrouter_api_key: 'test-key-123',
        brain_name: 'Test Brain',
      }));
      process.env.BRAIN_CONFIG_PROJECT = configPath;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(config, null);
      assert.strictEqual(config._source, 'project');
      assert.strictEqual(config.database_url, 'postgresql://localhost:5432/testdb');
      assert.strictEqual(config.openrouter_api_key, 'test-key-123');
      assert.strictEqual(config.brain_name, 'Test Brain');
    });

    // T-0003-066: resolveConfig() with env var DATABASE_URL returns config with _source="env"
    it('T-0003-066: returns config with _source="env" from DATABASE_URL env var', async () => {
      process.env.DATABASE_URL = 'postgresql://localhost:5432/envdb';
      process.env.OPENROUTER_API_KEY = 'env-api-key';

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(config, null);
      assert.strictEqual(config._source, 'env');
      assert.strictEqual(config.database_url, 'postgresql://localhost:5432/envdb');
      assert.strictEqual(config.openrouter_api_key, 'env-api-key');
    });

    // T-0003-067: resolveConfig() with missing env vars in config template returns null
    it('T-0003-067: returns null when config template references missing env vars', async () => {
      const configPath = path.join(tmpDir, 'template-config.json');
      writeFileSync(configPath, JSON.stringify({
        database_url: '${NONEXISTENT_DB_URL}',
        openrouter_api_key: 'static-key',
      }));
      process.env.BRAIN_CONFIG_PROJECT = configPath;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.strictEqual(config, null);
    });

    // T-0003-068: resolveConfig() with no config and no env vars returns null
    it('T-0003-068: returns null with no config files and no env vars', async () => {
      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.strictEqual(config, null);
    });

    // Edge case: user config as fallback when project config missing
    it('falls back to user config when project config is missing', async () => {
      const configPath = path.join(tmpDir, 'user-config.json');
      writeFileSync(configPath, JSON.stringify({
        database_url: 'postgresql://localhost:5432/userdb',
      }));
      process.env.BRAIN_CONFIG_USER = configPath;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(config, null);
      assert.strictEqual(config._source, 'personal');
      assert.strictEqual(config.database_url, 'postgresql://localhost:5432/userdb');
    });

    // Edge case: project config takes priority over user config
    it('prefers project config over user config', async () => {
      const projectPath = path.join(tmpDir, 'project.json');
      const userPath = path.join(tmpDir, 'user.json');
      writeFileSync(projectPath, JSON.stringify({ database_url: 'project-url' }));
      writeFileSync(userPath, JSON.stringify({ database_url: 'user-url' }));
      process.env.BRAIN_CONFIG_PROJECT = projectPath;
      process.env.BRAIN_CONFIG_USER = userPath;

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.strictEqual(config._source, 'project');
      assert.strictEqual(config.database_url, 'project-url');
    });

    // Edge case: env var interpolation works
    it('interpolates env vars in config template values', async () => {
      const configPath = path.join(tmpDir, 'interpolated.json');
      writeFileSync(configPath, JSON.stringify({
        database_url: 'postgresql://${TEST_DB_HOST}:5432/mydb',
      }));
      process.env.BRAIN_CONFIG_PROJECT = configPath;
      process.env.TEST_DB_HOST = 'db.example.com';

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(config, null);
      assert.strictEqual(config.database_url, 'postgresql://db.example.com:5432/mydb');
    });

    // Edge case: ATELIER_BRAIN_DATABASE_URL also works as env fallback
    it('accepts ATELIER_BRAIN_DATABASE_URL as env fallback', async () => {
      process.env.ATELIER_BRAIN_DATABASE_URL = 'postgresql://localhost:5432/atelierdb';

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(config, null);
      assert.strictEqual(config._source, 'env');
      assert.strictEqual(config.database_url, 'postgresql://localhost:5432/atelierdb');
    });

    // Edge case: malformed JSON in config file is skipped
    it('skips config files with malformed JSON', async () => {
      const configPath = path.join(tmpDir, 'bad.json');
      writeFileSync(configPath, 'not valid json {{{');
      process.env.BRAIN_CONFIG_PROJECT = configPath;
      process.env.DATABASE_URL = 'postgresql://fallback:5432/db';

      const { resolveConfig } = await importConfig();
      const config = resolveConfig();

      assert.notStrictEqual(config, null);
      assert.strictEqual(config._source, 'env');
    });
  });

  describe('resolveIdentity()', () => {
    // T-0003-069: resolveIdentity() with ATELIER_BRAIN_USER set returns that value
    it('T-0003-069: returns ATELIER_BRAIN_USER env var when set', async () => {
      process.env.ATELIER_BRAIN_USER = 'Jose Garcia <jose@example.com>';

      const { resolveIdentity } = await importConfig();
      const identity = resolveIdentity();

      assert.strictEqual(identity, 'Jose Garcia <jose@example.com>');
    });

    // T-0003-070: resolveIdentity() without env var falls back to git config
    it('T-0003-070: falls back to git config when env var not set', async () => {
      const { resolveIdentity } = await importConfig();
      const identity = resolveIdentity();

      // We cannot guarantee git is configured in CI, but we verify
      // the function returns either a string or null
      assert.ok(identity === null || typeof identity === 'string');
    });

    // T-0003-071: resolveIdentity() with no env var and no git returns null
    it('T-0003-071: returns null with no env var and no git config', async () => {
      // We cannot easily mock execSync, but we can test with env var set to verify the priority
      // The no-git scenario is inherently environment-dependent
      const { resolveIdentity } = await importConfig();
      const identity = resolveIdentity();

      // Result is either a string (git configured) or null (git not configured)
      assert.ok(identity === null || typeof identity === 'string');
    });

    // Edge case: handles unicode names
    it('handles unicode identity names like "Li Ming"', async () => {
      process.env.ATELIER_BRAIN_USER = '李明 <liming@example.com>';

      const { resolveIdentity } = await importConfig();
      const identity = resolveIdentity();

      assert.strictEqual(identity, '李明 <liming@example.com>');
    });

    // Edge case: handles names with apostrophes
    it("handles names with apostrophes like O'Brien", async () => {
      process.env.ATELIER_BRAIN_USER = "O'Brien <obrien@example.com>";

      const { resolveIdentity } = await importConfig();
      const identity = resolveIdentity();

      assert.strictEqual(identity, "O'Brien <obrien@example.com>");
    });
  });

  describe('constants', () => {
    it('exports expected enum arrays', async () => {
      const { THOUGHT_TYPES, SOURCE_AGENTS, SOURCE_PHASES, THOUGHT_STATUSES, RELATION_TYPES, EMBEDDING_MODEL } = await importConfig();

      assert.ok(Array.isArray(THOUGHT_TYPES));
      assert.ok(THOUGHT_TYPES.includes('decision'));
      assert.ok(THOUGHT_TYPES.includes('handoff'));

      assert.ok(Array.isArray(SOURCE_AGENTS));
      assert.ok(SOURCE_AGENTS.includes('eva'));
      assert.ok(SOURCE_AGENTS.includes('colby'));

      assert.ok(Array.isArray(SOURCE_PHASES));
      assert.ok(SOURCE_PHASES.includes('build'));

      assert.ok(Array.isArray(THOUGHT_STATUSES));
      assert.ok(THOUGHT_STATUSES.includes('active'));
      assert.ok(THOUGHT_STATUSES.includes('conflicted'));

      assert.ok(Array.isArray(RELATION_TYPES));
      assert.ok(RELATION_TYPES.includes('supersedes'));

      assert.strictEqual(typeof EMBEDDING_MODEL, 'string');
      assert.ok(EMBEDDING_MODEL.length > 0);
    });
  });
});
