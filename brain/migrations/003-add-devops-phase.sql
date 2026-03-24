-- Migration 003: Add 'devops' to source_phase enum
-- Safe to run multiple times (idempotent check).

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'devops' AND enumtypid = 'source_phase'::regtype) THEN
    ALTER TYPE source_phase ADD VALUE 'devops';
  END IF;
END $$;
