/**
 * Database pool creation and migrations.
 * Depends on: config.mjs (indirectly -- receives DATABASE_URL as parameter).
 */

import pg from "pg";
import pgvector from "pgvector/pg";
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import path from "path";

// =============================================================================
// Pool Creation
// =============================================================================

function createPool(databaseUrl) {
  const pool = new pg.Pool({ connectionString: databaseUrl });

  pool.on("connect", async (client) => {
    await pgvector.registerTypes(client);
  });

  pool.on("error", (err) => {
    console.error("Database pool error:", err.message);
  });

  return pool;
}

// =============================================================================
// Auto-Migration (idempotent -- safe to run on every startup)
// =============================================================================

// Migrations are idempotent by design -- each checks whether its change
// has already been applied before running.  Individual migrations are
// wrapped in try/catch so a failure in one does not prevent the others
// from being evaluated.
async function runMigrations(pool) {
  const client = await pool.connect();
  try {
    const brainDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

    // Migration 001: captured_by column
    try {
      const colCheck = await client.query(
        `SELECT 1 FROM information_schema.columns
         WHERE table_name = 'thoughts' AND column_name = 'captured_by'`
      );
      if (colCheck.rows.length === 0) {
        console.log("Migration 001: adding captured_by column...");
        await client.query(`ALTER TABLE thoughts ADD COLUMN captured_by TEXT`);

        const migrationPath = path.join(brainDir, "migrations", "001-add-captured-by.sql");
        if (existsSync(migrationPath)) {
          const sql = readFileSync(migrationPath, "utf-8");
          await client.query(sql);
        }
        console.log("Migration 001: captured_by column added.");
      }
    } catch (err) {
      console.error("Migration 001 failed (non-fatal):", err.message);
    }

    // Migration 002: handoff enum values
    try {
      const handoffCheck = await client.query(
        `SELECT 1 FROM pg_enum WHERE enumlabel = 'handoff' AND enumtypid = 'thought_type'::regtype`
      );
      if (handoffCheck.rows.length === 0) {
        console.log("Migration 002: adding handoff enum values...");
        const migrationPath = path.join(brainDir, "migrations", "002-add-handoff-enums.sql");
        if (existsSync(migrationPath)) {
          const sql = readFileSync(migrationPath, "utf-8");
          await client.query(sql);
        }
        console.log("Migration 002: handoff enum values added.");
      }
    } catch (err) {
      console.error("Migration 002 failed (non-fatal):", err.message);
    }

    // Migration 003: devops source_phase enum value
    try {
      const devopsCheck = await client.query(
        `SELECT 1 FROM pg_enum WHERE enumlabel = 'devops' AND enumtypid = 'source_phase'::regtype`
      );
      if (devopsCheck.rows.length === 0) {
        console.log("Migration 003: adding devops phase...");
        const migrationPath = path.join(brainDir, "migrations", "003-add-devops-phase.sql");
        if (existsSync(migrationPath)) {
          const sql = readFileSync(migrationPath, "utf-8");
          await client.query(sql);
        }
        console.log("Migration 003: devops phase added.");
      }
    } catch (err) {
      console.error("Migration 003 failed (non-fatal):", err.message);
    }

    // Migration 004: pattern and seed thought_type enum values
    try {
      const patternCheck = await client.query(
        `SELECT 1 FROM pg_enum WHERE enumlabel = 'pattern' AND enumtypid = 'thought_type'::regtype`
      );
      if (patternCheck.rows.length === 0) {
        console.log("Migration 004: adding pattern and seed thought types...");
        const migrationPath = path.join(brainDir, "migrations", "004-add-pattern-and-seed-types.sql");
        if (existsSync(migrationPath)) {
          const sql = readFileSync(migrationPath, "utf-8");
          await client.query(sql);
        }
        console.log("Migration 004: pattern and seed thought types added.");
      }
    } catch (err) {
      console.error("Migration 004 failed (non-fatal):", err.message);
    }
  } catch (err) {
    console.error("Migration check failed (non-fatal):", err.message);
  } finally {
    client.release();
  }
}

export { createPool, runMigrations };
