-- Migration 009: Create schema_migrations tracking table
-- ADR-0034 Wave 2 Step 2.3 — generic migration runner foundation
--
-- Creates the schema_migrations table (version TEXT PRIMARY KEY, applied_at,
-- checksum). The new generic runner (db.mjs runMigrations) uses this table
-- to track which migrations have been applied.
--
-- Backfill strategy for 001 through 008: the generic runner re-applies all
-- .sql files absent from schema_migrations. Since all prior migrations are
-- idempotent (IF NOT EXISTS, ADD VALUE IF NOT EXISTS patterns), re-running
-- them is safe and serves as the backfill mechanism.
--
-- On a fresh database: all 9 migrations run and get tracked entries.
-- On an existing database with 001-008 already applied but not yet tracked:
--   - 009 creates schema_migrations
--   - Runner adds tracking rows for 001-008 on the next startup
--     (idempotent re-application, no data loss)
--
-- Idempotent: CREATE TABLE IF NOT EXISTS
-- Transaction-wrapped: BEGIN...COMMIT

BEGIN;

-- Create the tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
  version    TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  checksum   TEXT
);

COMMIT;
