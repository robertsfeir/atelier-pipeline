-- Migration 006: Add 'pipeline' to source_phase enum
-- Safe to run multiple times (idempotent check).

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'pipeline' AND enumtypid = 'source_phase'::regtype) THEN
    ALTER TYPE source_phase ADD VALUE 'pipeline';
  END IF;
END $$;
