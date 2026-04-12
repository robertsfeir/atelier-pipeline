/**
 * LLM response null guard tests — ADR-0034 Wave 3 Step 3.5
 * Test IDs: T-0034-057, T-0034-058, T-0034-059, T-0034-060
 *
 * These tests define correct behavior BEFORE Colby builds Step 3.5.
 * They are expected to FAIL until Colby creates brain/lib/llm-response.mjs
 * and wires conflict.mjs and consolidation.mjs to use assertLlmContent().
 *
 * S10 bug (pre-fix): both conflict.mjs and consolidation.mjs access
 *   data.choices[0].message.content
 * without null-checking. A malformed or truncated LLM response causes an
 * unhandled TypeError that crashes the consolidation/conflict cycle.
 *
 * Fix (Step 3.5):
 *   - NEW brain/lib/llm-response.mjs exports `assertLlmContent(data, context)`
 *   - Returns data.choices[0].message.content if present
 *   - Throws a named Error with "malformed" + truncated dump if not
 *   - conflict.mjs and consolidation.mjs import and call this helper
 *
 * T-0034-057: assertLlmContent({}) throws with "malformed" in message
 * T-0034-058: assertLlmContent({choices:[{message:{content:"ok"}}]}) returns "ok"
 * T-0034-059: assertLlmContent({choices:[]}) throws
 * T-0034-060: grep — .choices[0].message.content only appears in llm-response.mjs
 *
 * Authored by Roz before Colby builds (Roz-first TDD per ADR-0034).
 * Colby MUST NOT modify these assertions.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BRAIN_LIB_DIR = join(__dirname, '../../brain/lib');
const LLM_RESPONSE_PATH = join(BRAIN_LIB_DIR, 'llm-response.mjs');

// =============================================================================
// Dynamic import: llm-response.mjs
// This file does NOT EXIST yet — all tests that require it must fail gracefully
// until Colby creates it in Step 3.5.
// =============================================================================

let assertLlmContent = null;
let llmResponseImportError = null;
try {
  const mod = await import('../../brain/lib/llm-response.mjs');
  assertLlmContent = mod.assertLlmContent;
} catch (err) {
  llmResponseImportError = err;
}

/**
 * Helper: skip test if llm-response.mjs is not yet implemented.
 * Returns false (and skips) if the module is unavailable.
 */
function requireLlmResponse(t) {
  if (llmResponseImportError || !assertLlmContent) {
    t.skip(
      `brain/lib/llm-response.mjs not yet implemented (TDD: will fail until Step 3.5). ` +
      `Import error: ${llmResponseImportError ? llmResponseImportError.message : 'export missing'}`
    );
    return false;
  }
  return true;
}

// =============================================================================
// T-0034-057: assertLlmContent({}) throws with "malformed" in the error message
// =============================================================================

describe('ADR-0034 T-0034-057: assertLlmContent throws on missing choices', () => {
  it('T-0034-057: assertLlmContent({}) throws a named error containing "malformed"', (t) => {
    if (!requireLlmResponse(t)) return;

    let threw = false;
    let thrownError = null;

    try {
      assertLlmContent({}, 'test-context');
    } catch (err) {
      threw = true;
      thrownError = err;
    }

    assert.ok(
      threw,
      `assertLlmContent({}) should throw but returned normally. ` +
      `ADR-0034 Step 3.5: malformed LLM responses must throw a named error.`
    );

    assert.ok(
      thrownError instanceof Error,
      `assertLlmContent({}) should throw an Error instance, got: ${typeof thrownError}`
    );

    assert.ok(
      thrownError.message.toLowerCase().includes('malformed'),
      `Error message should contain "malformed". Got: "${thrownError.message}". ` +
      `ADR-0034 Step 3.5: error must include "malformed" so log consumers can identify ` +
      `LLM response parsing failures by message pattern.`
    );

    // The error must also include a truncated dump of the payload
    // (to aid debugging — "what did the LLM actually return?")
    // The spec says: JSON.stringify(data).slice(0, 200)
    // An empty object {} serializes to '{}' which should appear in the message
    assert.ok(
      thrownError.message.includes('{}') || thrownError.message.includes('LLM'),
      `Error message should include the truncated payload or "LLM". Got: "${thrownError.message}". ` +
      `ADR-0034 Step 3.5: error format: "LLM response malformed (context): <truncated JSON>"`
    );
  });

  it('T-0034-057b: assertLlmContent(null) throws', (t) => {
    if (!requireLlmResponse(t)) return;

    assert.throws(
      () => assertLlmContent(null, 'test-context'),
      (err) => err instanceof Error && err.message.toLowerCase().includes('malformed'),
      `assertLlmContent(null) must throw a "malformed" error. ` +
      `Null input is a common failure mode when the LLM HTTP call itself returns null.`
    );
  });
});

// =============================================================================
// T-0034-058: assertLlmContent with valid response returns content string
// =============================================================================

describe('ADR-0034 T-0034-058: assertLlmContent returns content on valid response', () => {
  it('T-0034-058: assertLlmContent({choices:[{message:{content:"ok"}}]}) returns "ok"', (t) => {
    if (!requireLlmResponse(t)) return;

    const validResponse = {
      choices: [
        { message: { content: 'ok' } },
      ],
    };

    let result;
    assert.doesNotThrow(
      () => { result = assertLlmContent(validResponse, 'test-context'); },
      `assertLlmContent with a valid response should not throw. ` +
      `ADR-0034 Step 3.5: happy path must pass through unchanged.`
    );

    assert.strictEqual(
      result,
      'ok',
      `assertLlmContent should return the content string "ok". ` +
      `Got: ${JSON.stringify(result)}`
    );
  });

  it('T-0034-058b: assertLlmContent returns non-empty content verbatim', (t) => {
    if (!requireLlmResponse(t)) return;

    const content = 'A longer response from the LLM with {"json": "embedded"}';
    const response = { choices: [{ message: { content } }] };

    const result = assertLlmContent(response, 'conflict');

    assert.strictEqual(
      result,
      content,
      `assertLlmContent should return the content verbatim. ` +
      `Expected: "${content}", Got: "${result}"`
    );
  });
});

// =============================================================================
// T-0034-059: assertLlmContent({choices:[]}) throws
// =============================================================================

describe('ADR-0034 T-0034-059: assertLlmContent throws on empty choices array', () => {
  it('T-0034-059: assertLlmContent({choices:[]}) throws', (t) => {
    if (!requireLlmResponse(t)) return;

    assert.throws(
      () => assertLlmContent({ choices: [] }, 'test-context'),
      (err) => {
        assert.ok(err instanceof Error, `Expected Error, got ${typeof err}`);
        assert.ok(
          err.message.toLowerCase().includes('malformed'),
          `Error message must contain "malformed". Got: "${err.message}"`
        );
        return true;
      },
      `assertLlmContent({choices:[]}) must throw. ` +
      `Empty choices array means the LLM returned no completion — accessing [0] would throw TypeError.`
    );
  });

  it('T-0034-059b: assertLlmContent({choices:[{message:{}}]}) throws (missing content)', (t) => {
    if (!requireLlmResponse(t)) return;

    // message exists but content is absent
    assert.throws(
      () => assertLlmContent({ choices: [{ message: {} }] }, 'test-context'),
      (err) => err instanceof Error && err.message.toLowerCase().includes('malformed'),
      `assertLlmContent({choices:[{message:{}}]}) must throw — content field is absent. ` +
      `This is a real failure mode when the LLM returns a tool_use block instead of text.`
    );
  });

  it('T-0034-059c: assertLlmContent({choices:[{message:{content:null}}]}) throws (null content)', (t) => {
    if (!requireLlmResponse(t)) return;

    // content is present but null — also a real LLM failure mode
    assert.throws(
      () => assertLlmContent({ choices: [{ message: { content: null } }] }, 'test-context'),
      (err) => err instanceof Error && err.message.toLowerCase().includes('malformed'),
      `assertLlmContent with content: null must throw. ` +
      `Null content means the LLM stopped generating before producing any text.`
    );
  });
});

// =============================================================================
// T-0034-060: grep — .choices[0].message.content only in llm-response.mjs
// =============================================================================

describe('ADR-0034 T-0034-060: .choices[0].message.content isolated to llm-response.mjs', () => {
  it(
    'T-0034-060: no .choices[0].message.content access exists in brain/lib/ ' +
    'outside llm-response.mjs',
    () => {
      // This is a structural integrity check: after Step 3.5, the direct
      // .choices[0].message.content access pattern must only exist in
      // llm-response.mjs (the helper). conflict.mjs and consolidation.mjs
      // must use assertLlmContent() instead.
      //
      // The grep pattern matches the exact JavaScript access chain.

      const PATTERN = /\.choices\s*\[\s*0\s*\]\s*\.message\s*\.content/;

      // Read all .mjs files in brain/lib/
      let libFiles;
      try {
        libFiles = readdirSync(BRAIN_LIB_DIR).filter(f => f.endsWith('.mjs'));
      } catch (err) {
        assert.fail(`Cannot read brain/lib/ directory: ${err.message}`);
      }

      const violations = [];

      for (const filename of libFiles) {
        // Skip llm-response.mjs — it is the ONLY allowed location
        if (filename === 'llm-response.mjs') continue;

        const filePath = join(BRAIN_LIB_DIR, filename);
        let source;
        try {
          source = readFileSync(filePath, 'utf8');
        } catch (err) {
          // Unreadable file is not a violation
          continue;
        }

        const lines = source.split('\n');
        lines.forEach((line, idx) => {
          if (PATTERN.test(line)) {
            violations.push({
              file: filename,
              line: idx + 1,
              text: line.trim().slice(0, 120),
            });
          }
        });
      }

      assert.strictEqual(
        violations.length,
        0,
        `Found ${violations.length} direct .choices[0].message.content access(es) ` +
        `in brain/lib/ outside llm-response.mjs:\n` +
        violations.map(v => `  brain/lib/${v.file}:${v.line}: ${v.text}`).join('\n') + '\n' +
        `ADR-0034 Step 3.5: all callers must use assertLlmContent() from llm-response.mjs. ` +
        `Offending files: conflict.mjs (pre-fix line 58), consolidation.mjs (pre-fix line 146).`
      );
    }
  );

  it('T-0034-060b: llm-response.mjs exists and exports assertLlmContent', () => {
    // Verify the file exists and has the expected export.
    // This test passes if llm-response.mjs exists even before it's fully correct.
    let fileExists = false;
    try {
      readFileSync(LLM_RESPONSE_PATH, 'utf8');
      fileExists = true;
    } catch {
      fileExists = false;
    }

    assert.ok(
      fileExists,
      `brain/lib/llm-response.mjs does not exist. ` +
      `ADR-0034 Step 3.5: Colby must create this file as the single source of ` +
      `truth for LLM response null-guarding.`
    );

    // If the file exists, verify the export
    if (fileExists) {
      assert.notStrictEqual(
        assertLlmContent,
        null,
        `brain/lib/llm-response.mjs exists but does not export assertLlmContent. ` +
        `Import error: ${llmResponseImportError ? llmResponseImportError.message : 'unknown'}`
      );
    }
  });
});
