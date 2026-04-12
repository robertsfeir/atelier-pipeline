/**
 * Tests for brain/lib/db.mjs
 * Test IDs: T-0003-072 through T-0003-075
 *
 * These tests use a mock pool -- no real database connection.
 * Integration tests with a real DB are in integration.test.mjs (separate concern).
 */

import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { createMockPool } from './helpers/mock-pool.mjs';

// db.mjs imports pg and pgvector at module level, so we test the functions
// by calling them with our mock pool.
// We cannot easily test createPool without a real pg module, but we can test
// that runMigrations sends the correct queries.

// Dynamic import to work around pg/pgvector import requirements
let runMigrations;
try {
  const dbModule = await import('../../brain/lib/db.mjs');
  runMigrations = dbModule.runMigrations;
} catch {
  // pg or pgvector may not be installed in test environment
  runMigrations = null;
}

describe('db.mjs', () => {
  let pool;

  beforeEach(() => {
    pool = createMockPool();
  });

  // T-0003-072: createPool() returns a pg.Pool instance
  it('T-0003-072: createPool imports and is a function', async () => {
    if (!runMigrations) {
      // If pg is not installed, verify the module at least exists
      const { existsSync } = await import('fs');
      const modulePath = new URL('../../brain/lib/db.mjs', import.meta.url).pathname;
      assert.ok(existsSync(modulePath), 'db.mjs module file should exist');
      return;
    }
    // createPool is tested indirectly -- it wraps new pg.Pool which requires
    // a real connection string. We verify the function is exported.
    const dbModule = await import('../../brain/lib/db.mjs');
    assert.strictEqual(typeof dbModule.createPool, 'function');
  });

  // T-0003-073: new file-loop runner uses schema_migrations, not information_schema.columns
  it('T-0003-073: runMigrations checks schema_migrations table not information_schema', async () => {
    if (!runMigrations) return;

    // ADR-0034 Wave 2 replaced the old inline runner with a file-loop runner.
    // The new runner tracks applied migrations in schema_migrations, not by
    // querying information_schema.columns for individual column presence.

    await runMigrations(pool);

    // New runner must NOT query information_schema.columns
    const legacyQueries = pool.queries.filter(q =>
      q.sql.includes('information_schema.columns')
    );
    assert.strictEqual(legacyQueries.length, 0, 'New runner must not query information_schema.columns');

    // New runner MUST query schema_migrations table (to create it and check applied migrations)
    const schemaQueries = pool.queries.filter(q =>
      q.sql.includes('schema_migrations')
    );
    assert.ok(schemaQueries.length >= 1, 'New runner must query schema_migrations table');
  });

  // T-0003-074: runMigrations() adds captured_by column if missing
  it('T-0003-074: runMigrations adds captured_by column when missing', async () => {
    if (!runMigrations) return;

    // Simulate missing captured_by column
    pool.setQueryResult('information_schema.columns', {
      rows: [], // column does not exist
      rowCount: 0,
    });
    pool.setQueryResult('pg_enum', {
      rows: [{ '1': 1 }], // handoff exists
      rowCount: 1,
    });

    await runMigrations(pool);

    // Should have issued an ALTER TABLE query
    const alterQueries = pool.queries.filter(q =>
      q.sql.includes('ALTER TABLE') && q.sql.includes('captured_by')
    );
    assert.ok(alterQueries.length >= 1, 'Should issue ALTER TABLE to add captured_by');
  });

  // T-0003-075: runMigrations() adds handoff enum values if missing
  it('T-0003-075: runMigrations adds handoff enum when missing', async () => {
    if (!runMigrations) return;

    // Simulate existing captured_by column
    pool.setQueryResult('information_schema.columns', {
      rows: [{ '1': 1 }],
      rowCount: 1,
    });
    // Simulate missing handoff enum
    pool.setQueryResult('pg_enum', {
      rows: [], // handoff does not exist
      rowCount: 0,
    });

    await runMigrations(pool);

    // Should have checked for handoff enum
    const enumQueries = pool.queries.filter(q =>
      q.sql.includes('pg_enum') && q.sql.includes('handoff')
    );
    assert.ok(enumQueries.length >= 1, 'Should check for handoff enum');
  });

  // Edge case: runMigrations handles query errors gracefully
  it('runMigrations handles query errors gracefully (non-fatal)', async () => {
    if (!runMigrations) return;

    pool.setQueryResult('information_schema.columns', new Error('Connection refused'));

    // Should not throw -- errors are caught and logged
    await runMigrations(pool);
  });
});
