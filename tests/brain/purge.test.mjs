/**
 * Tests for purge endpoint implementation
 * Test ID: T-0003-126
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

describe('purge endpoint', () => {
  // T-0003-126: Regression -- purge endpoint uses LEFT JOIN instead of NOT IN
  it('T-0003-126: uses LEFT JOIN for orphan detection, not NOT IN anti-pattern', () => {
    // Read the rest-api.mjs source and verify the purge query uses LEFT JOIN
    const restApiPath = path.resolve(
      path.dirname(fileURLToPath(import.meta.url)),
      '../../brain/lib/rest-api.mjs'
    );
    const source = readFileSync(restApiPath, 'utf-8');

    // The purge query should use LEFT JOIN, not NOT IN
    assert.ok(
      source.includes('LEFT JOIN'),
      'Purge query should use LEFT JOIN for orphan detection'
    );

    // Verify NOT IN anti-pattern is not used for the orphan deletion
    // We look specifically in the handlePurgeExpired area
    const purgeSection = source.slice(
      source.indexOf('handlePurgeExpired'),
      source.indexOf('handlePurgeExpired') + 500
    );

    assert.ok(
      !purgeSection.includes('NOT IN (SELECT'),
      'Purge query should not use NOT IN anti-pattern'
    );
  });
});
