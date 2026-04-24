-- Migration 010: Add sarah and sherlock source_agent enum values
-- Added when Sarah/Sherlock agents were introduced.
-- Additive only — existing 'cal' and 'roz' values remain valid for backward
-- compatibility with historical thoughts.
-- Safe to run multiple times (ADD VALUE IF NOT EXISTS pattern).

ALTER TYPE source_agent ADD VALUE IF NOT EXISTS 'sarah';
ALTER TYPE source_agent ADD VALUE IF NOT EXISTS 'sherlock';
