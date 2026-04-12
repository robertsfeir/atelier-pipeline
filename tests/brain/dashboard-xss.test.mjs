/**
 * Dashboard XSS regression tests — ADR-0034 Wave 3 Step 3.3
 * Test IDs: T-0034-051, T-0034-052, T-0034-053
 *
 * These tests define correct behavior BEFORE Colby builds Step 3.3.
 * They are expected to FAIL until Colby wraps all innerHTML interpolations
 * in escapeHtml() inside brain/ui/dashboard.html.
 *
 * ADR-0034 constraint #6: dashboard.html has no existing unit-test harness.
 * The viable regression guard is a file-grep (lint-style) that asserts every
 * `innerHTML =` assignment has a nearby `escapeHtml(`. This is intentionally
 * NOT a full DOM-level test — jsdom + module extraction is out of scope for
 * this ADR. The limitation is documented here so future maintainers understand
 * why these tests use file-content inspection rather than a real render cycle.
 *
 * What these tests guard against:
 *   - T-0034-051: s.sub2 interpolation is escapeHtml()-wrapped
 *   - T-0034-052: every innerHTML= assignment in dashboard.html has a nearby
 *                 escapeHtml( call (lint-style regression guard)
 *   - T-0034-053: renderAgents() metric interpolations at lines 1423-1426
 *                 (agent.invocations, avg_duration_ms, total_cost, avg_input/output_tokens)
 *                 are all wrapped in escapeHtml() — not just the agent.agent fields.
 *
 * Note on T-0034-053: agent.agent is ALREADY wrapped in escapeHtml() at lines
 * 1417 and 1419 (pre-existing partial fix). The remaining work per ADR-0034 is
 * to wrap the metric interpolations at lines 1423-1426 which use bare format
 * function calls (fmtDuration, fmtCost, fmt) without escapeHtml() wrapping.
 *
 * Authored by Roz before Colby builds (Roz-first TDD per ADR-0034).
 * Colby MUST NOT modify these assertions.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DASHBOARD_PATH = join(__dirname, '../../brain/ui/dashboard.html');

let dashboardSource;
try {
  dashboardSource = readFileSync(DASHBOARD_PATH, 'utf8');
} catch (err) {
  // File must exist — any read error is a hard failure, not a skip
  throw new Error(`Cannot read brain/ui/dashboard.html: ${err.message}`);
}

// =============================================================================
// T-0034-051: s.sub2 is wrapped in escapeHtml()
// =============================================================================

describe('ADR-0034 T-0034-051: s.sub2 XSS guard', () => {
  it('T-0034-051: s.sub2 interpolation is wrapped in escapeHtml()', () => {
    // The vulnerable line (pre-fix): ... + s.sub2 + '</div>' ...
    // The fixed line:               ... + escapeHtml(s.sub2) + '</div>' ...
    //
    // This test checks that the bare unescaped `s.sub2` pattern no longer
    // exists in dashboard.html. Specifically: s.sub2 must appear only inside
    // an escapeHtml() call, never as a bare string concatenation.

    // Check that the unescaped pattern does NOT appear.
    // We look for the bare interpolation: s.sub2 NOT preceded by escapeHtml(
    // Using a regex: s\.sub2 that is NOT preceded by escapeHtml(
    const unescapedPattern = /(?<!escapeHtml\()s\.sub2(?!\s*\))/g;
    const unescapedMatches = dashboardSource.match(unescapedPattern);

    assert.strictEqual(
      unescapedMatches,
      null,
      `dashboard.html contains unescaped s.sub2 interpolation(s) (${
        unescapedMatches ? unescapedMatches.length : 0
      } match(es)). ` +
      `ADR-0034 Step 3.3: s.sub2 must be wrapped in escapeHtml() to prevent XSS. ` +
      `Existing pattern: s.label, s.value, s.sub are already escaped (lines 1160-1162). ` +
      `s.sub2 must follow the same pattern.`
    );

    // Also verify the escaped form IS present (not just deleted)
    assert.ok(
      dashboardSource.includes('escapeHtml(s.sub2)'),
      `dashboard.html does not contain escapeHtml(s.sub2). ` +
      `ADR-0034 Step 3.3: s.sub2 must be wrapped — do not simply delete the sub2 rendering.`
    );
  });
});

// =============================================================================
// T-0034-052: Lint-style guard — every innerHTML= has nearby escapeHtml(
// =============================================================================

describe('ADR-0034 T-0034-052: innerHTML= assignments all have nearby escapeHtml(', () => {
  it('T-0034-052: every innerHTML= assignment is adjacent to escapeHtml( within 200 chars', () => {
    // Lint-style regression guard: scan for all `innerHTML =` assignments and
    // verify each one has an `escapeHtml(` call within 200 characters.
    //
    // This catches future additions that skip XSS escaping.
    //
    // Exceptions: innerHTML assignments that do NOT interpolate user-controlled
    // strings (e.g., constants, trusted static HTML) must have a comment:
    //   /* trusted: <reason> */
    // adjacent to them. This test accepts a nearby /* trusted: */ comment
    // as an explicit opt-out.
    //
    // Note: "within 200 chars" is measured in the raw source text following
    // the `innerHTML =` assignment. This is intentionally coarse — a full
    // AST-based check requires jsdom which is out of scope for ADR-0034.

    const WINDOW = 200; // characters to scan after each innerHTML= match

    // Find all innerHTML= positions (handle both 'innerHTML =' and 'innerHTML=')
    const innerHtmlPattern = /innerHTML\s*=/g;
    let match;
    const violations = [];

    while ((match = innerHtmlPattern.exec(dashboardSource)) !== null) {
      const pos = match.index;
      const endPos = match.index + match[0].length;
      // Look at WINDOW chars on both sides (before for context, after for content)
      const before = dashboardSource.slice(Math.max(0, pos - 50), pos);
      const after = dashboardSource.slice(endPos, endPos + WINDOW);
      const context = before + match[0] + after;

      const hasEscapeHtml = context.includes('escapeHtml(');
      const hasTrustedComment = /\/\*\s*trusted[:\s]/i.test(context);
      const hasEmptyCard = context.includes('emptyCard('); // trusted helper

      if (!hasEscapeHtml && !hasTrustedComment && !hasEmptyCard) {
        // Extract the line number for the match
        const lineNum = dashboardSource.slice(0, pos).split('\n').length;
        violations.push({
          line: lineNum,
          context: context.trim().slice(0, 120),
        });
      }
    }

    assert.strictEqual(
      violations.length,
      0,
      `Found ${violations.length} innerHTML= assignment(s) with no nearby escapeHtml() call:\n` +
      violations.map(v => `  Line ${v.line}: ${v.context}...`).join('\n') + '\n' +
      `ADR-0034 Step 3.3: all innerHTML= assignments interpolating external data must use ` +
      `escapeHtml(). Trusted static strings must have a /* trusted: <reason> */ comment.`
    );
  });
});

// =============================================================================
// T-0034-053: renderAgents() metric interpolations are escapeHtml()-wrapped
// =============================================================================

describe('ADR-0034 T-0034-053: renderAgents() uses escapeHtml() for all metric interpolations', () => {
  it('T-0034-053: renderAgents() metric interpolations (lines 1423-1426) are escapeHtml()-wrapped', () => {
    // The ADR requires wrapping ALL interpolations in renderAgents(), including
    // the metric fields at lines 1423-1426 (pre-fix):
    //   agent.invocations — rendered as `(agent.invocations || 0)`
    //   agent.avg_duration_ms — rendered as `fmtDuration(agent.avg_duration_ms)`
    //   agent.total_cost — rendered as `fmtCost(agent.total_cost)`
    //   agent.avg_input_tokens / agent.avg_output_tokens — `fmt(...)`
    //
    // NOTE: agent.agent IS already wrapped in escapeHtml() at lines 1417 and 1419
    // (pre-existing partial fix). The remaining work is the metric interpolations
    // at lines 1423-1426 which use bare format function calls without escapeHtml().
    //
    // This test verifies that those metric format functions are wrapped.
    // Expected pattern after fix: escapeHtml(fmtDuration(agent.avg_duration_ms))
    //                              escapeHtml(fmtCost(agent.total_cost))
    //                              escapeHtml(String(agent.invocations || 0))
    //                              escapeHtml(fmt(agent.avg_input_tokens, 0))
    //                              escapeHtml(fmt(agent.avg_output_tokens, 0))

    // Find the renderAgents function body
    const renderAgentsStart = dashboardSource.indexOf('function renderAgents(');
    assert.ok(
      renderAgentsStart !== -1,
      `renderAgents() function not found in dashboard.html.`
    );

    // Extract ~3000 chars of the function body for analysis
    const renderAgentsBody = dashboardSource.slice(
      renderAgentsStart,
      renderAgentsStart + 3000
    );

    // --- Assert metric format functions are wrapped ---

    // fmtDuration must be inside escapeHtml()
    assert.ok(
      renderAgentsBody.includes('escapeHtml(fmtDuration(') ||
      renderAgentsBody.includes('escapeHtml( fmtDuration('),
      `renderAgents() does not wrap fmtDuration() in escapeHtml(). ` +
      `ADR-0034 Step 3.3: all metric interpolations in agent card HTML must be escaped. ` +
      `Expected pattern: escapeHtml(fmtDuration(agent.avg_duration_ms)) ` +
      `Current (pre-fix) line ~1424: '<div...>' + fmtDuration(agent.avg_duration_ms) + '</div>'`
    );

    // fmtCost must be inside escapeHtml()
    assert.ok(
      renderAgentsBody.includes('escapeHtml(fmtCost(') ||
      renderAgentsBody.includes('escapeHtml( fmtCost('),
      `renderAgents() does not wrap fmtCost() in escapeHtml(). ` +
      `ADR-0034 Step 3.3: fmtCost output must be escaped. ` +
      `Expected: escapeHtml(fmtCost(agent.total_cost)) ` +
      `Current (pre-fix) line ~1425: '...' + fmtCost(agent.total_cost) + '...'`
    );

    // Invocations must be inside escapeHtml() — either as escapeHtml(String(...))
    // or escapeHtml(agent.invocations || 0) etc.
    assert.ok(
      renderAgentsBody.includes('escapeHtml(') &&
      (renderAgentsBody.includes('agent.invocations') || renderAgentsBody.includes('invocations')),
      `renderAgents() does not wrap agent.invocations in escapeHtml(). ` +
      `ADR-0034 Step 3.3: invocations count must be escaped. ` +
      `Expected pattern: escapeHtml(String(agent.invocations || 0))`
    );

    // The invocations line must specifically use escapeHtml for that value
    // Check that bare `+ (agent.invocations || 0) +` no longer appears
    const bareInvocations = /['"]\s*\+\s*\(\s*agent\.invocations\s*\|\|\s*0\s*\)\s*\+\s*['"]/;
    assert.ok(
      !bareInvocations.test(renderAgentsBody),
      `renderAgents() still has bare agent.invocations interpolation (no escapeHtml). ` +
      `ADR-0034 Step 3.3 pre-fix line ~1423: ` +
      `'<div...>' + (agent.invocations || 0) + '</div>' must become escapeHtml(...)`
    );
  });
});
