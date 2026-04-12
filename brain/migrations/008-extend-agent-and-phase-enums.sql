-- Migration 008: Add new source_agent and source_phase enum values
-- Closes ADR-0034 M1+M9: fixes silently-discarded agent_capture calls from
-- robert-spec, sable-ux, sentinel, darwin, deps, brain-extractor.
-- Safe to run multiple times (ADD VALUE IF NOT EXISTS pattern).

DO $$
BEGIN
  -- New source_agent values
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'robert-spec' AND enumtypid = 'source_agent'::regtype) THEN
    ALTER TYPE source_agent ADD VALUE 'robert-spec';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'sable-ux' AND enumtypid = 'source_agent'::regtype) THEN
    ALTER TYPE source_agent ADD VALUE 'sable-ux';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'sentinel' AND enumtypid = 'source_agent'::regtype) THEN
    ALTER TYPE source_agent ADD VALUE 'sentinel';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'darwin' AND enumtypid = 'source_agent'::regtype) THEN
    ALTER TYPE source_agent ADD VALUE 'darwin';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'deps' AND enumtypid = 'source_agent'::regtype) THEN
    ALTER TYPE source_agent ADD VALUE 'deps';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'brain-extractor' AND enumtypid = 'source_agent'::regtype) THEN
    ALTER TYPE source_agent ADD VALUE 'brain-extractor';
  END IF;

  -- New source_phase values
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'product' AND enumtypid = 'source_phase'::regtype) THEN
    ALTER TYPE source_phase ADD VALUE 'product';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ux' AND enumtypid = 'source_phase'::regtype) THEN
    ALTER TYPE source_phase ADD VALUE 'ux';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'commit' AND enumtypid = 'source_phase'::regtype) THEN
    ALTER TYPE source_phase ADD VALUE 'commit';
  END IF;
END $$;
