/**
 * Enum boundary tests for ADR-0034 Wave 1 Step 1.1.
 *
 * Tests T-0034-001, T-0034-002, T-0034-003R, T-0034-004, T-0034-005,
 *       T-0034-006, T-0034-007, T-0034-008, T-0034-009, T-0034-010,
 *       T-0034-011, T-0034-012, T-0034-013,
 *       T-0034-061 (Roz addition: count lock),
 *       T-0034-063 (Roz addition: migration 008 file exists with ADD VALUE IF NOT EXISTS).
 *
 * Uses mock pool for migration tests -- no real database required.
 * All assertions authored by Roz; Colby extends with the full set per spec.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';
import { z } from 'zod';
import { createMockPool } from './helpers/mock-pool.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BRAIN_DIR = path.join(__dirname, '..', '..', 'brain');
const CONFIG_PATH = path.join(BRAIN_DIR, 'lib', 'config.mjs');
const SCHEMA_PATH = path.join(BRAIN_DIR, 'schema.sql');
const MIGRATION_008_PATH = path.join(BRAIN_DIR, 'migrations', '008-extend-agent-and-phase-enums.sql');
const BRAIN_EXTRACTOR_PATH = path.join(__dirname, '..', '..', 'source', 'shared', 'agents', 'brain-extractor.md');
const REST_API_PATH = path.join(BRAIN_DIR, 'lib', 'rest-api.mjs');

// Dynamic import of config to get live values
const { SOURCE_AGENTS, SOURCE_PHASES } = await import('../../brain/lib/config.mjs');

// Dynamic import of runMigrations (optional -- skips if pg unavailable)
let runMigrations;
try {
  const dbModule = await import('../../brain/lib/db.mjs');
  runMigrations = dbModule.runMigrations;
} catch {
  runMigrations = null;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Parse the brain-extractor.md agent-to-metadata mapping table.
 * Returns an array of source_agent strings from the second column.
 */
function parseBrainExtractorAgents() {
  const content = readFileSync(BRAIN_EXTRACTOR_PATH, 'utf-8');
  const lines = content.split('\n');
  const agents = [];
  let inTable = false;
  for (const line of lines) {
    if (line.includes('agent_type') && line.includes('source_agent')) {
      inTable = true;
      continue;
    }
    if (inTable) {
      // Header separator row
      if (line.match(/^\s*\|[-| ]+\|\s*$/)) continue;
      // Table row: | agent_type | source_agent | source_phase |
      const match = line.match(/^\s*\|\s*\S+\s*\|\s*(\S+)\s*\|/);
      if (match) {
        agents.push(match[1]);
      } else if (line.trim() === '' || !line.includes('|')) {
        break; // end of table
      }
    }
  }
  return agents;
}

/**
 * Parse source_agent enum values from schema.sql CREATE TYPE statement.
 */
function parseSchemaAgents() {
  const content = readFileSync(SCHEMA_PATH, 'utf-8');
  const match = content.match(/CREATE TYPE source_agent AS ENUM\s*\(([\s\S]*?)\);/);
  if (!match) return [];
  return match[1].split(',').map(v => v.trim().replace(/'/g, '').replace(/--[^\n]*/g, '').trim()).filter(Boolean);
}

/**
 * Parse source_phase enum values from schema.sql CREATE TYPE statement.
 */
function parseSchemaPhases() {
  const content = readFileSync(SCHEMA_PATH, 'utf-8');
  const match = content.match(/CREATE TYPE source_phase AS ENUM\s*\(([\s\S]*?)\);/);
  if (!match) return [];
  return match[1].split(',').map(v => v.trim().replace(/'/g, '').replace(/--[^\n]*/g, '').trim()).filter(Boolean);
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('ADR-0034 Wave 1 — enum boundary', () => {

  // T-0034-001: SOURCE_AGENTS includes every agent from brain-extractor mapping table
  it('T-0034-001: SOURCE_AGENTS includes every brain-extractor mapping table agent', () => {
    const mappingAgents = parseBrainExtractorAgents();
    assert.ok(mappingAgents.length > 0, 'brain-extractor.md mapping table must have at least one row');

    const missing = mappingAgents.filter(a => !SOURCE_AGENTS.includes(a));
    assert.deepStrictEqual(
      missing,
      [],
      `SOURCE_AGENTS is missing these agents from brain-extractor mapping table: ${missing.join(', ')}`
    );
  });

  // T-0034-002: SOURCE_PHASES includes product, ux, commit plus all existing mapping phases
  it('T-0034-002: SOURCE_PHASES includes product, ux, commit and all mapping table phases', () => {
    const required = ['product', 'ux', 'commit'];
    const missing = required.filter(p => !SOURCE_PHASES.includes(p));
    assert.deepStrictEqual(
      missing,
      [],
      `SOURCE_PHASES is missing these new phases: ${missing.join(', ')}`
    );
    // Verify existing phases from brain-extractor mapping are present
    const mappingPhases = ['design', 'build', 'qa', 'handoff'];
    const missingExisting = mappingPhases.filter(p => !SOURCE_PHASES.includes(p));
    assert.deepStrictEqual(
      missingExisting,
      [],
      `SOURCE_PHASES is missing existing phases: ${missingExisting.join(', ')}`
    );
  });

  // T-0034-003R: config.mjs has # non-extracted comment near eva, poirot, distillator
  it('T-0034-003R: config.mjs has # non-extracted comment within 10 lines of eva, poirot, distillator', () => {
    const content = readFileSync(CONFIG_PATH, 'utf-8');
    const lines = content.split('\n');

    const NON_EXTRACTED_AGENTS = ['eva', 'poirot', 'distillator'];
    for (const agent of NON_EXTRACTED_AGENTS) {
      // Find the line where the agent appears inside SOURCE_AGENTS array
      const agentLineIdx = lines.findIndex(l => {
        const trimmed = l.trim();
        return trimmed.startsWith(`"${agent}"`) || trimmed.startsWith(`'${agent}'`);
      });
      assert.notStrictEqual(
        agentLineIdx,
        -1,
        `Agent "${agent}" not found in config.mjs SOURCE_AGENTS`
      );
      // Check surrounding 10 lines for # non-extracted marker
      const start = Math.max(0, agentLineIdx - 5);
      const end = Math.min(lines.length, agentLineIdx + 6);
      const surroundingText = lines.slice(start, end).join('\n');
      const hasMarker = /# non-extracted/i.test(surroundingText);
      assert.ok(
        hasMarker,
        `Agent "${agent}" in SOURCE_AGENTS is missing a "# non-extracted" comment within 5 lines. ` +
        `Surrounding lines:\n${surroundingText}`
      );
    }
  });

  // T-0034-004: schema.sql source_agent enum matches SOURCE_AGENTS
  it('T-0034-004: schema.sql source_agent enum matches SOURCE_AGENTS', () => {
    const schemaAgents = parseSchemaAgents();
    const missing = SOURCE_AGENTS.filter(a => !schemaAgents.includes(a));
    const extra = schemaAgents.filter(a => !SOURCE_AGENTS.includes(a));
    assert.deepStrictEqual(
      missing,
      [],
      `SOURCE_AGENTS has these values NOT in schema.sql: ${missing.join(', ')}`
    );
    assert.deepStrictEqual(
      extra,
      [],
      `schema.sql has these source_agent values NOT in SOURCE_AGENTS: ${extra.join(', ')}`
    );
  });

  // T-0034-005: schema.sql source_phase enum matches SOURCE_PHASES
  it('T-0034-005: schema.sql source_phase enum matches SOURCE_PHASES', () => {
    const schemaPhases = parseSchemaPhases();
    const missing = SOURCE_PHASES.filter(p => !schemaPhases.includes(p));
    const extra = schemaPhases.filter(p => !SOURCE_PHASES.includes(p));
    assert.deepStrictEqual(
      missing,
      [],
      `SOURCE_PHASES has these values NOT in schema.sql: ${missing.join(', ')}`
    );
    assert.deepStrictEqual(
      extra,
      [],
      `schema.sql has these source_phase values NOT in SOURCE_PHASES: ${extra.join(', ')}`
    );
  });

  // T-0034-006: Migration 008 idempotency — second run skips (already recorded in schema_migrations)
  it('T-0034-006: migration 008 skips on second run when sentinel already in pg_enum', async () => {
    if (!runMigrations) return;

    const pool = createMockPool();
    // ADR-0034 Wave 2 replaced the pg_enum sentinel check with schema_migrations tracking.
    // Simulate migration 008 already applied: schema_migrations returns a row for it.
    // The mock-pool matches params, so setting the migration filename as a pattern works
    // because the query uses $1 = '008-extend-agent-and-phase-enums.sql'.
    pool.setQueryResult('008-extend-agent-and-phase-enums.sql', { rows: [{ '1': 1 }], rowCount: 1 });

    await runMigrations(pool);

    // New runner checks schema_migrations before running each file.
    // With a row returned for 008-..., migration 008 DDL should NOT be executed.
    const alterQueries = pool.queries.filter(q => q.sql.includes('ALTER TYPE source_agent'));
    assert.strictEqual(
      alterQueries.length,
      0,
      'Migration 008 should not issue ALTER TYPE when schema_migrations shows it already applied'
    );
  });

  // T-0034-007: Migration 008 failure does not prevent boot (try/catch wrap)
  it('T-0034-007: migration 008 failure is non-fatal (try/catch wrap)', async () => {
    if (!runMigrations) return;

    const pool = createMockPool();
    // Return existing state for all checks except migration 008's sentinel check
    pool.setQueryResult('information_schema.columns', { rows: [{ '1': 1 }], rowCount: 1 });
    // Make pg_enum return empty for 'sentinel' check to trigger migration 008 attempt
    pool.setQueryResult("enumlabel = 'sentinel'", { rows: [], rowCount: 0 });
    // But other pg_enum checks pass
    pool.setQueryResult('pg_enum', { rows: [{ '1': 1 }], rowCount: 1 });
    // Make the migration file SQL execution fail
    pool.setQueryResult('ALTER TYPE source_agent', new Error('Transaction block'));

    // Should not throw
    await assert.doesNotReject(
      () => runMigrations(pool),
      'runMigrations should not throw even when migration 008 fails'
    );
  });

  // T-0034-008: rest-api.mjs does NOT contain the hardcoded IN literal
  it('T-0034-008: rest-api.mjs has no hardcoded IN literal for agent names', () => {
    const content = readFileSync(REST_API_PATH, 'utf-8');
    // The old literal started with IN ('eva','colby'
    const hasLiteral = content.includes("IN ('eva','colby'");
    assert.ok(
      !hasLiteral,
      "rest-api.mjs still contains hardcoded IN ('eva','colby'...) literal. Must use SOURCE_AGENTS dynamically."
    );
  });

  // T-0034-009: rest-api.mjs query includes sentinel, darwin, deps in agent filter
  it('T-0034-009: handleTelemetryAgents builds IN clause from SOURCE_AGENTS (includes new agents)', () => {
    // Verify the source code uses SOURCE_AGENTS import and builds placeholders
    const content = readFileSync(REST_API_PATH, 'utf-8');
    assert.ok(
      content.includes('SOURCE_AGENTS'),
      'rest-api.mjs must import and use SOURCE_AGENTS from config.mjs'
    );
    // Verify the new agents are in SOURCE_AGENTS (they will be in the query)
    for (const agent of ['sentinel', 'darwin', 'deps']) {
      assert.ok(
        SOURCE_AGENTS.includes(agent),
        `SOURCE_AGENTS must include '${agent}' so handleTelemetryAgents filters it`
      );
    }
  });

  // T-0034-010: Zod validation passes for sentinel + build
  it('T-0034-010: Zod accepts source_agent="sentinel" and source_phase="build"', () => {
    const schema = z.object({
      source_agent: z.enum(SOURCE_AGENTS),
      source_phase: z.enum(SOURCE_PHASES),
    });
    const result = schema.safeParse({ source_agent: 'sentinel', source_phase: 'build' });
    assert.ok(result.success, `Zod rejected sentinel/build: ${JSON.stringify(result.error)}`);
  });

  // T-0034-011: Zod validation passes for robert-spec + product
  it('T-0034-011: Zod accepts source_agent="robert-spec" and source_phase="product"', () => {
    const schema = z.object({
      source_agent: z.enum(SOURCE_AGENTS),
      source_phase: z.enum(SOURCE_PHASES),
    });
    const result = schema.safeParse({ source_agent: 'robert-spec', source_phase: 'product' });
    assert.ok(result.success, `Zod rejected robert-spec/product: ${JSON.stringify(result.error)}`);
  });

  // T-0034-012: Zod still rejects unknown agents (guard against over-opening)
  it('T-0034-012: Zod still rejects source_agent="nonsense"', () => {
    const schema = z.object({
      source_agent: z.enum(SOURCE_AGENTS),
    });
    const result = schema.safeParse({ source_agent: 'nonsense' });
    assert.ok(!result.success, 'Zod should reject source_agent="nonsense"');
  });

  // T-0034-013: Zod failure identifies the invalid field, not a silent drop
  it('T-0034-013: Zod failure produces an error with field identification', () => {
    const schema = z.object({
      source_agent: z.enum(SOURCE_AGENTS),
      source_phase: z.enum(SOURCE_PHASES),
    });
    const result = schema.safeParse({ source_agent: 'unknown-agent', source_phase: 'build' });
    assert.ok(!result.success, 'Zod must fail on invalid source_agent');
    const errorStr = JSON.stringify(result.error);
    // The error must identify "source_agent" as the bad field
    assert.ok(
      errorStr.includes('source_agent') || result.error.issues.some(i => i.path.includes('source_agent')),
      `Zod error should identify source_agent field. Got: ${errorStr}`
    );
  });

  // T-0034-061 (Roz): SOURCE_AGENTS total count is exactly 18
  it('T-0034-061: SOURCE_AGENTS has exactly 18 entries', () => {
    const EXPECTED_AGENTS = [
      'eva', 'cal', 'robert', 'sable', 'colby',
      'roz', 'agatha', 'ellis',
      'poirot', 'distillator',
      'robert-spec', 'sable-ux',
      'sentinel', 'darwin', 'deps', 'brain-extractor',
      'sarah', 'sherlock',
    ];
    assert.strictEqual(
      SOURCE_AGENTS.length,
      18,
      `SOURCE_AGENTS has ${SOURCE_AGENTS.length} entries, expected 18. ` +
      `Actual: [${SOURCE_AGENTS.join(', ')}]. ` +
      `Expected: [${EXPECTED_AGENTS.join(', ')}]`
    );
    // Also verify all expected names are present
    const missing = EXPECTED_AGENTS.filter(a => !SOURCE_AGENTS.includes(a));
    assert.deepStrictEqual(
      missing,
      [],
      `SOURCE_AGENTS is missing these expected entries: ${missing.join(', ')}`
    );
  });

  // T-0034-063 (Roz): migration 008 file exists and contains ADD VALUE IF NOT EXISTS
  it('T-0034-063: migration 008 file exists and contains ADD VALUE IF NOT EXISTS', () => {
    assert.ok(
      existsSync(MIGRATION_008_PATH),
      `brain/migrations/008-extend-agent-and-phase-enums.sql does not exist at ${MIGRATION_008_PATH}`
    );
    const content = readFileSync(MIGRATION_008_PATH, 'utf-8');
    assert.ok(
      content.includes('ADD VALUE IF NOT EXISTS') || content.includes('IF NOT EXISTS'),
      'migration 008 must use IF NOT EXISTS pattern for idempotency'
    );
  });

});
