# Brain Migrations

SQL migration files for the Atelier Brain PostgreSQL schema.

## File Naming Convention

```
NNN-description.sql
```

- `NNN` — 3-digit zero-padded sequence number (e.g., `009`, `010`, `011`)
- `description` — short lowercase hyphenated label for what the migration does
- Example: `010-add-cost-tracking.sql`

Files are sorted lexicographically by name, so the sequence number determines execution order.

## Idempotency Requirement

Every migration must be safe to run multiple times. Use guards that prevent duplicate application:

- DDL: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
- Columns: `ADD COLUMN IF NOT EXISTS`
- Enum values: `ADD VALUE IF NOT EXISTS`
- Wrap DDL in a transaction where possible so partial failures roll back cleanly

A migration that is not idempotent is a blocker — it will cause errors on re-runs and on fresh databases that already have some schema applied out-of-band.

## Migration Runner

The generic runner lives in `brain/lib/db.mjs`. At every brain startup it:

1. Reads all `.sql` files in `brain/migrations/` sorted by filename
2. Skips files whose filename is already recorded in the `schema_migrations` table
3. Executes new files in order
4. Records each applied file in `schema_migrations` (columns: `version` = filename, `checksum` = SHA-256 of file content, `applied_at` = timestamp)

The checksum column is informational — the runner does not re-run a migration if its checksum changes, it only checks whether the version string is present.

## Backfill for New Team Members and Fresh Databases

Migration `009-schema-migrations-table.sql` creates the `schema_migrations` table and automatically backfills rows for migrations `001` through `008` that were applied before tracking existed. Any fresh database that runs all migrations in sequence gets this for free — migration 009 runs after 001–008 and inserts their records idempotently.

If you inherit a database with some migrations partially applied, running the full sequence from the start is safe because every file is idempotent.

## Adding a New Migration

1. Pick the next sequence number (current highest is `009`, so next is `010`).
2. Create `NNN-description.sql` in `brain/migrations/`.
3. Write idempotent SQL (see requirements above).
4. No registration step needed — the runner discovers files automatically at next brain startup.

To apply immediately without restarting the brain server, restart the server process. There is no separate migration CLI.
