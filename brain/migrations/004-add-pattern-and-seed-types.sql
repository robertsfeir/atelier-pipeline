-- Migration 004: Add 'pattern' and 'seed' thought types
-- ADR: docs/architecture/ADR-0004-pipeline-evolution.md (Steps 2, 9)
-- Idempotent: safe to run multiple times

-- Add new enum values (IF NOT EXISTS prevents errors on re-run)
ALTER TYPE thought_type ADD VALUE IF NOT EXISTS 'pattern';
ALTER TYPE thought_type ADD VALUE IF NOT EXISTS 'seed';

-- Add configuration rows for new types
INSERT INTO thought_type_config (thought_type, default_ttl_days, default_importance, description)
VALUES ('pattern', 365, 0.7, 'Reusable implementation patterns')
ON CONFLICT (thought_type) DO NOTHING;

INSERT INTO thought_type_config (thought_type, default_ttl_days, default_importance, description)
VALUES ('seed', NULL, 0.5, 'Out-of-scope ideas with trigger conditions')
ON CONFLICT (thought_type) DO NOTHING;
