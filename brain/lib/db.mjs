/**
 * Database pool creation and migrations.
 * Depends on: config.mjs (indirectly -- receives DATABASE_URL as parameter).
 */

import pg from "pg";
import pgvector from "pgvector/pg";
import { readFileSync, existsSync, readdirSync } from "fs";
import { createHash } from "crypto";
import { fileURLToPath } from "url";
import path from "path";

// =============================================================================
// Pool Creation
// =============================================================================

function createPool(databaseUrl) {
  const pool = new pg.Pool({
    connectionString: databaseUrl,
    max: 5,
    connectionTimeoutMillis: 5000,
    idleTimeoutMillis: 30000,
  });

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

// Generic file-loop migration runner (ADR-0034 Wave 2 Step 2.3).
// Reads brain/migrations/*.sql sorted by filename, tracks applied migrations
// in schema_migrations table, applies unapplied files. Fail-soft per file.
async function runMigrations(pool) {
  const client = await pool.connect();
  try {
    const brainDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
    const migrationsDir = path.join(brainDir, "migrations");
    await client.query(
      `CREATE TABLE IF NOT EXISTS schema_migrations ` +
      `(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now(), checksum TEXT)`
    );
    const files = existsSync(migrationsDir)
      ? readdirSync(migrationsDir).filter(f => f.endsWith(".sql")).sort()
      : [];
    for (const filename of files) {
      try {
        const check = await client.query(
          `SELECT 1 FROM schema_migrations WHERE version = $1`, [filename]
        );
        if (check.rows.length > 0) {
          console.error(`Migration ${filename}: skipped (already applied)`);
          continue;
        }
        const filePath = path.join(migrationsDir, filename);
        const sql = readFileSync(filePath, "utf-8");
        const checksum = createHash("sha256").update(sql).digest("hex").slice(0, 16);
        console.error(`Migration ${filename}: applying...`);
        await client.query(sql);
        await client.query(
          `INSERT INTO schema_migrations (version, applied_at, checksum) ` +
          `VALUES ($1, now(), $2)`, [filename, checksum]
        );
        console.error(`Migration ${filename}: applied.`);
      } catch (err) {
        console.error(`Migration ${filename} failed (non-fatal):`, err.message);
      }
    }
  } catch (err) {
    console.error("Migration runner failed (non-fatal):", err.message);
  } finally {
    client.release();
  }
}

export { createPool, runMigrations };
