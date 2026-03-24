-- Atelier Brain Schema (Option D)
-- ADR: docs/architecture/ADR-0001-atelier-brain.md
-- Steps 1 + 2: Schema + Three-Axis Scoring Function

-- =============================================================================
-- Extensions
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS ltree;

-- =============================================================================
-- Enums
-- =============================================================================

CREATE TYPE thought_type AS ENUM (
  'decision', 'preference', 'lesson', 'rejection',
  'drift', 'correction', 'insight', 'reflection', 'handoff'
);

CREATE TYPE source_agent AS ENUM (
  'eva', 'cal', 'robert', 'sable', 'colby',
  'roz', 'poirot', 'agatha', 'distillator', 'ellis'
);

CREATE TYPE source_phase AS ENUM (
  'design', 'build', 'qa', 'review', 'reconciliation', 'setup', 'handoff', 'devops'
);

CREATE TYPE thought_status AS ENUM (
  'active', 'superseded', 'invalidated', 'expired', 'conflicted'
);

CREATE TYPE relation_type AS ENUM (
  'supersedes', 'triggered_by', 'evolves_from',
  'contradicts', 'supports', 'synthesized_from'
);

-- =============================================================================
-- Configuration Tables
-- =============================================================================

-- Thought type configuration (lookup table for TTL and defaults)
CREATE TABLE thought_type_config (
  thought_type thought_type PRIMARY KEY,
  default_ttl_days INTEGER,          -- NULL = never expires
  default_importance FLOAT NOT NULL DEFAULT 0.5,
  description TEXT
);

INSERT INTO thought_type_config VALUES
  ('decision',    NULL, 0.9,  'Architectural or product decisions'),
  ('preference',  NULL, 1.0,  'Human preferences and HALT resolutions'),
  ('lesson',      365,  0.7,  'Retro learnings and patterns'),
  ('rejection',   180,  0.5,  'Alternatives considered and discarded'),
  ('drift',       90,   0.8,  'Spec/UX drift findings'),
  ('correction',  90,   0.7,  'Fixes applied after drift detection'),
  ('insight',     180,  0.6,  'Mid-task discoveries'),
  ('reflection',  NULL, 0.85, 'Consolidation-generated synthesis'),
  ('handoff',     NULL, 0.9,  'Structured handoff briefs for team collaboration');

-- Brain configuration (singleton — CHECK constraint enforces single row)
CREATE TABLE brain_config (
  id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  brain_enabled BOOLEAN NOT NULL DEFAULT false,
  consolidation_interval_minutes INTEGER NOT NULL DEFAULT 30,
  consolidation_min_thoughts INTEGER NOT NULL DEFAULT 3,
  consolidation_max_thoughts INTEGER NOT NULL DEFAULT 20,
  conflict_detection_enabled BOOLEAN NOT NULL DEFAULT true,
  conflict_duplicate_threshold FLOAT NOT NULL DEFAULT 0.9,
  conflict_candidate_threshold FLOAT NOT NULL DEFAULT 0.7,
  conflict_llm_enabled BOOLEAN NOT NULL DEFAULT true,
  default_scope ltree DEFAULT 'default'
);

INSERT INTO brain_config DEFAULT VALUES;

-- =============================================================================
-- Core Tables
-- =============================================================================

-- Thoughts table (Option D — with importance, invalidated_at, ltree scoping)
CREATE TABLE thoughts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB DEFAULT '{}',
  thought_type thought_type NOT NULL,
  source_agent source_agent NOT NULL,
  source_phase source_phase NOT NULL,
  importance FLOAT NOT NULL CHECK (importance >= 0 AND importance <= 1),
  trigger_event TEXT,
  captured_by TEXT,
  status thought_status NOT NULL DEFAULT 'active',
  scope ltree[] DEFAULT ARRAY['default']::ltree[],
  invalidated_at TIMESTAMPTZ,
  last_accessed_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Thought relations table (typed edges between thoughts)
-- Convention: source_id = NEWER/DERIVED thought, target_id = OLDER/ORIGINAL thought
CREATE TABLE thought_relations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source_id UUID NOT NULL REFERENCES thoughts(id) ON DELETE CASCADE,
  target_id UUID NOT NULL REFERENCES thoughts(id) ON DELETE CASCADE,
  relation_type relation_type NOT NULL,
  context TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (source_id, target_id, relation_type)
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- Thoughts indexes
CREATE INDEX thoughts_embedding_idx ON thoughts USING hnsw (embedding vector_cosine_ops);
CREATE INDEX thoughts_metadata_idx ON thoughts USING gin (metadata);
CREATE INDEX thoughts_scope_idx ON thoughts USING gist (scope);
CREATE INDEX thoughts_status_idx ON thoughts (status);
CREATE INDEX thoughts_type_idx ON thoughts (thought_type);
CREATE INDEX thoughts_created_idx ON thoughts (created_at DESC);
CREATE INDEX thoughts_agent_idx ON thoughts (source_agent);
CREATE INDEX thoughts_invalidated_idx ON thoughts (invalidated_at) WHERE invalidated_at IS NOT NULL;

-- Relations indexes
CREATE INDEX relations_source_idx ON thought_relations (source_id);
CREATE INDEX relations_target_idx ON thought_relations (target_id);
CREATE INDEX relations_type_idx ON thought_relations (relation_type);

-- =============================================================================
-- Triggers
-- =============================================================================

-- Auto-update updated_at on row modification
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER thoughts_updated_at
  BEFORE UPDATE ON thoughts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- Step 2: Three-Axis Scoring Function
-- =============================================================================
-- Formula: score = (0.5 * recency_decay) + (2.0 * importance) + (3.0 * cosine_similarity)
-- Where: recency_decay = 0.995 ^ hours_since_last_access
--
-- Weight rationale:
--   - Relevance (3.0): what you're asking about matters most
--   - Importance (2.0): decisions outrank tactical findings
--   - Recency (0.5): tiebreaker, not dominant — old decisions still surface

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
  -- Validate inputs
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
