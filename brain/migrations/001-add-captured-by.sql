-- Migration 001: Add captured_by column for human attribution
-- Run against existing databases to add team member tracking.
-- Safe to run multiple times (IF NOT EXISTS).

ALTER TABLE thoughts ADD COLUMN IF NOT EXISTS captured_by TEXT;

-- Update match_thoughts_scored to include captured_by in return type.
-- This replaces the existing function definition.
CREATE OR REPLACE FUNCTION match_thoughts_scored(
  query_embedding vector(1536),
  similarity_threshold FLOAT DEFAULT 0.2,
  max_results INTEGER DEFAULT 10,
  metadata_filter JSONB DEFAULT '{}',
  scope_filter ltree DEFAULT NULL,
  include_invalidated BOOLEAN DEFAULT false
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  thought_type thought_type,
  source_agent source_agent,
  source_phase source_phase,
  importance FLOAT,
  status thought_status,
  scope ltree[],
  captured_by TEXT,
  created_at TIMESTAMPTZ,
  invalidated_at TIMESTAMPTZ,
  similarity FLOAT,
  recency_score FLOAT,
  combined_score FLOAT
) AS $$
BEGIN
  IF query_embedding IS NULL THEN
    RAISE EXCEPTION 'query_embedding must not be NULL';
  END IF;
  IF max_results < 0 THEN
    RAISE EXCEPTION 'max_results must be non-negative, got %', max_results;
  END IF;
  IF similarity_threshold < 0 OR similarity_threshold > 1 THEN
    RAISE EXCEPTION 'similarity_threshold must be between 0 and 1, got %', similarity_threshold;
  END IF;

  RETURN QUERY
  SELECT
    t.id,
    t.content,
    t.metadata,
    t.thought_type,
    t.source_agent,
    t.source_phase,
    t.importance,
    t.status,
    t.scope,
    t.captured_by,
    t.created_at,
    t.invalidated_at,
    (1 - (t.embedding <=> query_embedding))::FLOAT AS similarity,
    POWER(0.995, EXTRACT(EPOCH FROM (now() - COALESCE(t.last_accessed_at, t.created_at))) / 3600)::FLOAT AS recency_score,
    (
      0.5 * POWER(0.995, EXTRACT(EPOCH FROM (now() - COALESCE(t.last_accessed_at, t.created_at))) / 3600) +
      2.0 * t.importance +
      3.0 * (1 - (t.embedding <=> query_embedding))
    )::FLOAT AS combined_score
  FROM thoughts t
  WHERE
    (1 - (t.embedding <=> query_embedding)) >= similarity_threshold
    AND (include_invalidated OR t.status = 'active')
    AND (metadata_filter = '{}' OR t.metadata @> metadata_filter)
    AND (scope_filter IS NULL OR t.scope @> ARRAY[scope_filter])
  ORDER BY combined_score DESC
  LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
