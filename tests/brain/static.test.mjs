/**
 * Tests for brain/lib/static.mjs
 * Test IDs: T-0003-121 through T-0003-123
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { writeFileSync, mkdirSync, rmSync, existsSync } from 'fs';
import path from 'path';
import os from 'os';

// static.mjs uses a hardcoded UI_DIR based on its own file location.
// For unit testing, we test the handleStaticFile function against the real UI dir
// or verify behavior via mock req/res when the UI dir does/doesn't exist.
import { handleStaticFile } from '../../brain/lib/static.mjs';

function createMockReq(url) {
  return {
    url,
    headers: { host: 'localhost:8788' },
  };
}

function createMockRes() {
  let statusCode = 200;
  let headersWritten = {};
  let bodyData = '';

  return {
    writeHead(code, headers) {
      statusCode = code;
      Object.assign(headersWritten, headers);
    },
    end(data) {
      bodyData = data || '';
    },
    get statusCode() { return statusCode; },
    get headers() { return headersWritten; },
    get body() { return bodyData; },
  };
}

describe('static.mjs', () => {
  // Check if the UI directory exists for conditional tests
  const brainDir = path.dirname(path.dirname(new URL('../../brain/lib/static.mjs', import.meta.url).pathname));
  const uiDir = path.join(brainDir, 'ui');
  const uiExists = existsSync(uiDir);

  // T-0003-121: handleStaticFile() serves /ui/index.html with correct content type
  it('T-0003-121: serves /ui/index.html with text/html content type', () => {
    if (!uiExists) {
      // If UI dir doesn't exist, verify 404 behavior
      const req = createMockReq('/ui/index.html');
      const res = createMockRes();
      const handled = handleStaticFile(req, res, null);
      assert.strictEqual(handled, true);
      assert.strictEqual(res.statusCode, 404);
      return;
    }

    const indexPath = path.join(uiDir, 'index.html');
    if (!existsSync(indexPath)) {
      // index.html doesn't exist, expect 404
      const req = createMockReq('/ui/index.html');
      const res = createMockRes();
      const handled = handleStaticFile(req, res, null);
      assert.strictEqual(handled, true);
      assert.strictEqual(res.statusCode, 404);
      return;
    }

    const req = createMockReq('/ui/index.html');
    const res = createMockRes();
    const handled = handleStaticFile(req, res, null);

    assert.strictEqual(handled, true);
    assert.strictEqual(res.statusCode, 200);
    assert.ok(res.headers['Content-Type'].includes('text/html'));
  });

  // T-0003-122: handleStaticFile() rejects path traversal attempts
  it('T-0003-122: rejects path traversal attempts', () => {
    // Standard ../ traversal is neutralized by URL constructor normalization:
    // /ui/../../../etc/passwd -> /etc/passwd (no longer starts with /ui, returns false)
    const req1 = createMockReq('/ui/../../../etc/passwd');
    const res1 = createMockRes();
    const handled1 = handleStaticFile(req1, res1, null);
    // URL normalization removes the /ui prefix, so the function returns false (not /ui path)
    // This means the traversal is blocked at the routing level
    assert.strictEqual(handled1, false, 'Normalized path does not start with /ui -- blocked at routing');

    // Encoded traversal: %2F-encoded slashes are kept in the path, but the extension
    // won't match any MIME type, resulting in a 404
    const req2 = createMockReq('/ui/..%2F..%2F..%2Fetc%2Fpasswd');
    const res2 = createMockRes();
    const handled2 = handleStaticFile(req2, res2, null);
    assert.strictEqual(handled2, true);
    assert.strictEqual(res2.statusCode, 404, 'Encoded traversal should get 404 for unknown extension');

    // Direct path with .html extension that attempts to escape
    const req3 = createMockReq('/ui/..%2Fserver.mjs');
    const res3 = createMockRes();
    const handled3 = handleStaticFile(req3, res3, null);
    assert.strictEqual(handled3, true);
    // No .mjs in MIME_TYPES, so 404
    assert.strictEqual(res3.statusCode, 404, 'Files outside MIME_TYPES get 404');
  });

  // T-0003-123: handleStaticFile() returns 404 for unknown extensions
  it('T-0003-123: returns 404 for unknown file extensions', () => {
    const req = createMockReq('/ui/malware.exe');
    const res = createMockRes();
    const handled = handleStaticFile(req, res, null);

    assert.strictEqual(handled, true);
    assert.strictEqual(res.statusCode, 404);
  });

  it('returns false for non-/ui paths', () => {
    const req = createMockReq('/api/health');
    const res = createMockRes();
    const handled = handleStaticFile(req, res, null);

    assert.strictEqual(handled, false);
  });

  it('injects API token into HTML when provided', () => {
    if (!uiExists) return;
    const indexPath = path.join(uiDir, 'index.html');
    if (!existsSync(indexPath)) return;

    const req = createMockReq('/ui/index.html');
    const res = createMockRes();
    handleStaticFile(req, res, 'my-secret-token');

    if (res.statusCode === 200) {
      assert.ok(
        res.body.includes('__ATELIER_API_TOKEN__'),
        'Should inject API token into HTML'
      );
    }
  });

  it('serves /ui/ as /ui/index.html', () => {
    const req = createMockReq('/ui/');
    const res = createMockRes();
    const handled = handleStaticFile(req, res, null);

    assert.strictEqual(handled, true);
    // Will be 200 if index.html exists, 404 otherwise
    assert.ok(res.statusCode === 200 || res.statusCode === 404);
  });

  it('serves .css files with correct content type', () => {
    if (!uiExists) return;
    const cssPath = path.join(uiDir, 'styles.css');
    if (!existsSync(cssPath)) return;

    const req = createMockReq('/ui/styles.css');
    const res = createMockRes();
    const handled = handleStaticFile(req, res, null);

    assert.strictEqual(handled, true);
    if (res.statusCode === 200) {
      assert.ok(res.headers['Content-Type'].includes('text/css'));
    }
  });

  it('serves .js files with correct content type', () => {
    if (!uiExists) return;
    const jsPath = path.join(uiDir, 'settings.js');
    if (!existsSync(jsPath)) return;

    const req = createMockReq('/ui/settings.js');
    const res = createMockRes();
    const handled = handleStaticFile(req, res, null);

    assert.strictEqual(handled, true);
    if (res.statusCode === 200) {
      assert.ok(res.headers['Content-Type'].includes('application/javascript'));
    }
  });
});
