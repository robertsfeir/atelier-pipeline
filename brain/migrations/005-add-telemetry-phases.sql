-- Migration 005: Add 'telemetry' and 'ci-watch' to source_phase enum
-- Safe to run multiple times (idempotent check).

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'telemetry' AND enumtypid = 'source_phase'::regtype) THEN
    ALTER TYPE source_phase ADD VALUE 'telemetry';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ci-watch' AND enumtypid = 'source_phase'::regtype) THEN
    ALTER TYPE source_phase ADD VALUE 'ci-watch';
  END IF;
END $$;
