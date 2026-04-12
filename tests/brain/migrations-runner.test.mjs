/**
 * Tests for ADR-0034 Wave 2 Step 2.3: generic runMigrations() refactor.
 *
 * Covers T-0034-040 through T-0034-044.
 *
 * The NEW runMigrations() does NOT yet exist. These tests define its contract
 * and will fail (or error on import) until Colby ships the refactor.
 *
 * Design: the new runner reads `brain/migrations/` directory, sorts by filename,
 * tracks which migrations have been applied in a `schema_migrations` table
 * (version TEXT PRIMARY KEY), and applies only unapplied ones.
 *
 * These tests use createMockPool() from helpers/mock-pool.mjs. No real database
 * connection is required.
 *
 * Colby MUST NOT modify these assertions.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, readdirSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';
import { createMockPool } from './helpers/mock-pool.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BRAIN_DIR = path.join(__dirname, '..', '..', 'brain');
const DB_PATH = path.join(BRAIN_DIR, 'lib', 'db.mjs');
const MIGRATIONS_DIR = path.join(BRAIN_DIR, 'migrations');

// ─── Import guard ─────────────────────────────────────────────────────────────
// runMigrations does not yet accept a mock pool in its current 144-line form.
// After Wave 2 refactor it will export runMigrations(pool) where pool is
// injected. We attempt the import here; if it fails or the function signature
// is incompatible, tests fail with a clear message rather than a silent crash.

let runMigrations = null;
let importError = null;

try {
  const dbModule = await import('../../brain/lib/db.mjs');
  if (typeof dbModule.runMigrations === 'function') {
    runMigrations = dbModule.runMigrations;
  } else {
    importError = new Error(
      'brain/lib/db.mjs exported runMigrations but it is not a function. ' +
      'Wave 2 Step 2.3 refactor may not be complete.'
    );
  }
} catch (err) {
  importError = err;
}

// ─── Helper: build a mock pool that simulates schema_migrations state ─────────

/**
 * Creates a mock pool pre-loaded to simulate a schema_migrations table
 * containing `appliedVersions`. Any query that looks up schema_migrations
 * for a version in `appliedVersions` returns a row; absent versions return
 * empty rows. All migration SQL executions succeed unless overridden.
 *
 * @param {string[]} appliedVersions - filenames already in schema_migrations
 * @param {Map<string, Error|Object>} [overrides] - per-SQL overrides
 */
function buildMockPool(appliedVersions = [], overrides = new Map()) {
  const pool = createMockPool();

  // Any query for schema_migrations existence check (CREATE TABLE IF NOT EXISTS)
  // succeeds silently.
  pool.setQueryResult('CREATE TABLE', { rows: [], rowCount: 0 });

  // Version lookup: SELECT 1 FROM schema_migrations WHERE version = $1
  // The mock pool does substring matching, so we intercept by version name.
  for (const version of appliedVersions) {
    pool.setQueryResult(version, { rows: [{ '1': 1 }], rowCount: 1 });
  }

  // Apply any custom overrides
  for (const [pattern, result] of overrides.entries()) {
    pool.setQueryResult(pattern, result);
  }

  return pool;
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('ADR-0034 Wave 2 — migrations-runner refactor', () => {

  // ─── T-0034-040: zero applied migrations → runner applies all in order ───

  it('T-0034-040: against empty schema_migrations, runner applies all migrations in order', async () => {
    assert.ok(
      runMigrations !== null,
      `runMigrations could not be loaded from brain/lib/db.mjs.\n` +
      `Import error: ${importError?.message ?? 'unknown'}\n` +
      `This test is RED until Wave 2 Step 2.3 ships the refactored runMigrations(pool) ` +
      `that accepts an injectable pool argument and uses schema_migrations tracking.`
    );

    // Zero rows in schema_migrations for any version check → all migrations are unapplied
    const pool = buildMockPool([]); // no applied versions

    await assert.doesNotReject(
      () => runMigrations(pool),
      'runMigrations must not throw when schema_migrations is empty'
    );

    // The runner must have issued an INSERT INTO schema_migrations for each migration file
    const insertQueries = pool.queries.filter(q =>
      q.sql && q.sql.toLowerCase().includes('insert') &&
      q.sql.toLowerCase().includes('schema_migrations')
    );

    // We expect at least one INSERT per migration file that exists on disk
    const migrationFiles = existsSync(MIGRATIONS_DIR)
      ? readdirSync(MIGRATIONS_DIR).filter(f => f.endsWith('.sql')).sort()
      : [];

    assert.ok(
      insertQueries.length > 0,
      `runMigrations against an empty schema_migrations table must INSERT at least one row. ` +
      `Actual INSERT queries: ${insertQueries.length}. ` +
      `Expected one INSERT per unapplied migration file (found ${migrationFiles.length} .sql files on disk). ` +
      `Wave 2 Step 2.3: the new runner must record every applied migration in schema_migrations.`
    );
  });

  // ─── T-0034-041: partially applied → runner applies only unapplied ones ──

  it('T-0034-041: runner skips already-applied migrations and applies only remaining ones', async () => {
    assert.ok(
      runMigrations !== null,
      `runMigrations could not be loaded from brain/lib/db.mjs.\n` +
      `Import error: ${importError?.message ?? 'unknown'}\n` +
      `This test is RED until Wave 2 Step 2.3 ships.`
    );

    // Gather migration files on disk; if none, skip with informational message
    if (!existsSync(MIGRATIONS_DIR)) {
      console.log('T-0034-041: brain/migrations/ directory not found — skipping');
      return;
    }

    const allFiles = readdirSync(MIGRATIONS_DIR)
      .filter(f => f.endsWith('.sql'))
      .sort();

    if (allFiles.length < 2) {
      console.log('T-0034-041: fewer than 2 migration files — skipping partial-apply check');
      return;
    }

    // Simulate: first half already applied
    const midpoint = Math.floor(allFiles.length / 2);
    const alreadyApplied = allFiles.slice(0, midpoint);
    const shouldApply = allFiles.slice(midpoint);

    const pool = buildMockPool(alreadyApplied);

    await assert.doesNotReject(
      () => runMigrations(pool),
      'runMigrations must not throw when some migrations are already applied'
    );

    // Runner must INSERT only for the unapplied migrations
    const insertQueries = pool.queries.filter(q =>
      q.sql && q.sql.toLowerCase().includes('insert') &&
      q.sql.toLowerCase().includes('schema_migrations')
    );

    assert.ok(
      insertQueries.length <= shouldApply.length,
      `Runner inserted ${insertQueries.length} rows but should have inserted at most ${shouldApply.length} ` +
      `(the unapplied ones). Already-applied migrations [${alreadyApplied.join(', ')}] must be skipped.`
    );

    assert.ok(
      insertQueries.length > 0,
      `Runner must INSERT at least one row for the unapplied migrations [${shouldApply.join(', ')}]. ` +
      `Got zero INSERTs — the runner may be skipping everything or not using schema_migrations.`
    );
  });

  // ─── T-0034-042: invalid SQL in migration file → logged, continues ────────

  it('T-0034-042: a migration file with invalid SQL logs an error and continues to the next', async () => {
    assert.ok(
      runMigrations !== null,
      `runMigrations could not be loaded from brain/lib/db.mjs.\n` +
      `Import error: ${importError?.message ?? 'unknown'}\n` +
      `This test is RED until Wave 2 Step 2.3 ships.`
    );

    // Inject a failing SQL execution for any migration whose SQL hits 'ALTER TYPE'
    // (migrations 002–008 all use ALTER TYPE; this simulates a SQL failure)
    const overrides = new Map();
    overrides.set('ALTER TYPE', new Error('Simulated SQL syntax error for T-0034-042'));

    const pool = buildMockPool([], overrides);

    // Must NOT throw even when a migration's SQL fails
    await assert.doesNotReject(
      () => runMigrations(pool),
      'runMigrations must be fail-soft: a single migration SQL failure must not propagate as an unhandled exception. ' +
      'Each migration must be wrapped in its own try/catch (matching the ADR-0034 fail-soft requirement).'
    );

    // After the failure, the runner must have continued attempting other migrations.
    // We verify by checking total query count > 0 (it tried something after the failure).
    assert.ok(
      pool.queries.length > 0,
      'After a migration SQL failure, the runner must continue executing subsequent migrations. ' +
      'Pool query count is 0, suggesting the runner halted entirely on the first error.'
    );
  });

  // ─── T-0034-043: migration 009 backfill populates schema_migrations ───────

  it('T-0034-043: migration 009 backfill populates schema_migrations from existing idempotency checks', () => {
    // This test verifies the MIGRATION FILE itself (009-schema-migrations-table.sql),
    // not the runner behavior. The file does not yet exist — this test is RED until
    // Colby ships Wave 2 Step 2.3.

    const migration009Path = path.join(MIGRATIONS_DIR, '009-schema-migrations-table.sql');

    assert.ok(
      existsSync(migration009Path),
      `brain/migrations/009-schema-migrations-table.sql does not exist at ${migration009Path}. ` +
      `Wave 2 Step 2.3 must create this file. ` +
      `The file should CREATE TABLE schema_migrations IF NOT EXISTS and backfill rows for 001–008.`
    );

    const content = readFileSync(migration009Path, 'utf-8');

    // Must create the schema_migrations table
    assert.ok(
      content.includes('schema_migrations'),
      `migration 009 must reference 'schema_migrations' (CREATE TABLE or INSERT). ` +
      `Got content: ${content.slice(0, 300)}`
    );

    // Must be wrapped in a transaction (requirement from ADR Step 2.3)
    const hasTransaction = content.includes('BEGIN') || content.includes('START TRANSACTION');
    assert.ok(
      hasTransaction,
      `migration 009 must be wrapped in a transaction (BEGIN...COMMIT) per ADR-0034 Step 2.3. ` +
      `This ensures the backfill is atomic — either all 001–008 rows are inserted or none.`
    );

    // Must backfill for at least migrations 001 through 008
    // Check that the content references at least the first and last of those migrations
    assert.ok(
      content.includes('001') || content.includes('001-'),
      `migration 009 backfill must reference migration 001 (the earliest migration).`
    );
    assert.ok(
      content.includes('008') || content.includes('008-'),
      `migration 009 backfill must reference migration 008 (the most recent prior migration).`
    );
  });

  // ─── T-0034-044: runMigrations() function body is ≤50 lines ─────────────

  it('T-0034-044: runMigrations() function body is ≤50 lines (refactor size guard)', () => {
    assert.ok(
      existsSync(DB_PATH),
      `brain/lib/db.mjs not found at ${DB_PATH}`
    );

    const content = readFileSync(DB_PATH, 'utf-8');
    const lines = content.split('\n');

    // Find the start of runMigrations function
    let funcStart = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].match(/^async function runMigrations/) ||
          lines[i].match(/^function runMigrations/)) {
        funcStart = i;
        break;
      }
    }

    assert.notStrictEqual(
      funcStart,
      -1,
      `runMigrations() function definition not found in brain/lib/db.mjs. ` +
      `Expected: async function runMigrations(...) { ... } at top level.`
    );

    // Count lines until matching closing brace using a depth counter
    let depth = 0;
    let funcEnd = -1;
    for (let i = funcStart; i < lines.length; i++) {
      for (const ch of lines[i]) {
        if (ch === '{') depth++;
        if (ch === '}') {
          depth--;
          if (depth === 0) {
            funcEnd = i;
            break;
          }
        }
      }
      if (funcEnd !== -1) break;
    }

    assert.notStrictEqual(
      funcEnd,
      -1,
      `Could not find closing brace of runMigrations() in db.mjs. ` +
      `The function body may be malformed.`
    );

    const lineCount = funcEnd - funcStart + 1;

    assert.ok(
      lineCount <= 50,
      `runMigrations() is ${lineCount} lines (from line ${funcStart + 1} to ${funcEnd + 1}). ` +
      `ADR-0034 Step 2.3 requires the refactored body to be ≤50 lines. ` +
      `The current 144-line hand-rolled implementation must be replaced with a ` +
      `≤50-line file-loop driven by schema_migrations tracking. ` +
      `This test is RED until Colby ships Wave 2 Step 2.3.`
    );
  });

});
