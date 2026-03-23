-- Migration 002: Add handoff enum values for team collaboration
-- Safe to run multiple times (idempotent checks).

-- Add 'handoff' to thought_type enum
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'handoff' AND enumtypid = 'thought_type'::regtype) THEN
    ALTER TYPE thought_type ADD VALUE 'handoff';
  END IF;
END $$;

-- Add 'handoff' to source_phase enum
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'handoff' AND enumtypid = 'source_phase'::regtype) THEN
    ALTER TYPE source_phase ADD VALUE 'handoff';
  END IF;
END $$;

-- Add thought_type_config row for handoff
INSERT INTO thought_type_config (thought_type, default_ttl_days, default_importance, description)
VALUES ('handoff', NULL, 0.9, 'Structured handoff briefs for team collaboration')
ON CONFLICT (thought_type) DO NOTHING;
