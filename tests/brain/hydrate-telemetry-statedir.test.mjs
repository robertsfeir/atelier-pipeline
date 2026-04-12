/**
 * tests/brain/hydrate-telemetry-statedir.test.mjs
 *
 * Pre-build test assertions for ADR-0035 Wave 4, Step 2:
 * hydrate-telemetry.mjs auto-resolution of the out-of-repo state directory.
 *
 * These tests define correct behavior BEFORE Colby implements. All tests
 * except T-0035-017 (full regression) are expected to FAIL until Colby
 * adds resolveAtelierStateDir() and the parseStateFiles() guard.
 *
 * Test IDs in scope:
 *   T-0035-010  resolveAtelierStateDir returns correct path when dir exists
 *   T-0035-011  resolveAtelierStateDir returns null when dir does not exist
 *   T-0035-012  Cross-implementation contract: JS hash == bash hash for 5 paths
 *   T-0035-013  parseStateFiles returns 0 on nonexistent dir (graceful skip)
 *   T-0035-014  Explicit --state-dir still takes precedence (backward compat)
 *   T-0035-015  Auto-resolve via CLAUDE_PROJECT_DIR env var
 *   T-0035-016  Graceful fallback when no --state-dir and no env vars
 *   T-0035-017  All existing brain tests pass (regression gate)
 */

import { describe, it, before, after, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, readFileSync, existsSync } from "fs";
import { execSync } from "child_process";
import path from "path";
import os from "os";
import { createHash } from "crypto";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const PROJECT_ROOT = path.resolve(
  path.dirname(new URL(import.meta.url).pathname),
  "../.."
);

const BASH_HELPER_PATH = path.join(
  PROJECT_ROOT,
  "source/shared/hooks/pipeline-state-path.sh"
);

/**
 * Compute the expected 8-char hash for a given worktree root path.
 * This mirrors what the bash helper does: sha256 of the path string, first 8 hex chars.
 */
function expectedHash(worktreeRoot) {
  return createHash("sha256").update(worktreeRoot).digest("hex").slice(0, 8);
}

/**
 * Compute the expected state dir path for a given worktree root.
 */
function expectedStateDir(worktreeRoot) {
  const slug = path.basename(worktreeRoot);
  const hash = expectedHash(worktreeRoot);
  return path.join(os.homedir(), ".atelier", "pipeline", slug, hash);
}

/**
 * Call the bash helper to get the session_state_dir for a given project path.
 * Returns the output path string (trimmed).
 */
function bashSessionStateDir(projectRoot) {
  // Source the helper and call session_state_dir with CLAUDE_PROJECT_DIR set
  const cmd = `CLAUDE_PROJECT_DIR="${projectRoot}" bash -c 'source "${BASH_HELPER_PATH}" && session_state_dir'`;
  return execSync(cmd, { encoding: "utf-8", timeout: 10000 }).trim();
}

/**
 * Cache-busted dynamic import of hydrate-telemetry.mjs so each test
 * gets a fresh module evaluation.
 */
async function importHydrate() {
  const modulePath = path.join(
    PROJECT_ROOT,
    "brain/scripts/hydrate-telemetry.mjs"
  );
  return await import(`${modulePath}?t=${Date.now()}-${Math.random()}`);
}

// ---------------------------------------------------------------------------
// Test Suite: resolveAtelierStateDir
// ---------------------------------------------------------------------------

describe("ADR-0035 Step 2: resolveAtelierStateDir + parseStateFiles guard", () => {
  let tmpDir;
  let savedEnv;

  beforeEach(() => {
    savedEnv = { ...process.env };
    tmpDir = mkdtempSync(path.join(os.tmpdir(), "adr0035-statedir-"));
  });

  afterEach(() => {
    // Restore env
    for (const key of Object.keys(process.env)) {
      if (!(key in savedEnv)) delete process.env[key];
    }
    for (const [key, value] of Object.entries(savedEnv)) {
      process.env[key] = value;
    }
    try {
      rmSync(tmpDir, { recursive: true });
    } catch {
      /* ignore cleanup errors */
    }
  });

  // -----------------------------------------------------------------------
  // T-0035-010: resolveAtelierStateDir returns path when dir exists
  // Expected: FAIL before Colby implements (function does not exist yet)
  // -----------------------------------------------------------------------
  it("T-0035-010: resolveAtelierStateDir returns path under ~/.atelier/pipeline/ when directory exists", async () => {
    const fakeWorktree = path.join(tmpDir, "test-project");
    mkdirSync(fakeWorktree, { recursive: true });

    // Create the expected state directory so existsSync returns true
    const expected = expectedStateDir(fakeWorktree);
    mkdirSync(expected, { recursive: true });

    try {
      const { resolveAtelierStateDir } = await importHydrate();

      const result = resolveAtelierStateDir(fakeWorktree);

      assert.strictEqual(
        result,
        expected,
        `resolveAtelierStateDir('${fakeWorktree}') should return '${expected}'`
      );
      assert.ok(
        result.startsWith(path.join(os.homedir(), ".atelier", "pipeline")),
        "Returned path must be under ~/.atelier/pipeline/"
      );
      // Verify the hash portion is exactly 8 hex chars
      const hashPart = path.basename(result);
      assert.match(hashPart, /^[0-9a-f]{8}$/, "Hash portion must be 8 hex characters");
    } finally {
      // Clean up the state dir we created under ~/.atelier
      try {
        rmSync(expected, { recursive: true });
        // Also try to clean the slug parent if empty
        const slugDir = path.dirname(expected);
        rmSync(slugDir);
      } catch {
        /* ignore */
      }
    }
  });

  // -----------------------------------------------------------------------
  // T-0035-011: resolveAtelierStateDir returns null when dir does not exist
  // Expected: FAIL before Colby implements (function does not exist yet)
  // -----------------------------------------------------------------------
  it("T-0035-011: resolveAtelierStateDir returns null when computed directory does not exist on disk", async () => {
    const nonexistentWorktree = "/tmp/adr0035-definitely-not-a-real-project-" + Date.now();

    const { resolveAtelierStateDir } = await importHydrate();

    const result = resolveAtelierStateDir(nonexistentWorktree);

    assert.strictEqual(
      result,
      null,
      "resolveAtelierStateDir must return null when the computed state directory does not exist"
    );
  });

  // -----------------------------------------------------------------------
  // T-0035-012: Cross-implementation contract test (JS vs bash)
  // Expected: FAIL before Colby implements (function does not exist yet)
  // -----------------------------------------------------------------------
  it("T-0035-012: JS resolveAtelierStateDir produces identical hashes to bash session_state_dir for 5 test paths", async () => {
    // The 5 paths specified in the ADR test spec
    const testPaths = [
      "/tmp/a",
      "/Users/alice/projects/my-project",
      "/home/bob/work/atelier-pipeline",
      "/tmp/path with spaces",
      "/tmp/path-with-unicode-\u00e9",
    ];

    assert.ok(
      existsSync(BASH_HELPER_PATH),
      `Bash helper must exist at ${BASH_HELPER_PATH}`
    );

    const { resolveAtelierStateDir } = await importHydrate();

    for (const testPath of testPaths) {
      // Create temp directories to make the bash helper succeed and to
      // make the JS function's existsSync pass
      const expectedDir = expectedStateDir(testPath);
      mkdirSync(expectedDir, { recursive: true });

      // Also create the worktree path itself so bash `cd` succeeds
      mkdirSync(testPath, { recursive: true });

      try {
        // Get the bash helper's output
        const bashResult = bashSessionStateDir(testPath);

        // Get the JS function's output
        const jsResult = resolveAtelierStateDir(testPath);

        assert.strictEqual(
          jsResult,
          bashResult,
          `Hash mismatch for path '${testPath}':\n` +
            `  JS:   ${jsResult}\n` +
            `  Bash: ${bashResult}\n` +
            `Cross-implementation contract violated.`
        );
      } finally {
        // Clean up the state dirs we created
        try {
          rmSync(expectedDir, { recursive: true });
          const slugDir = path.dirname(expectedDir);
          rmSync(slugDir);
        } catch {
          /* ignore */
        }
        // Clean up temp worktree paths we created (only if in /tmp)
        if (testPath.startsWith("/tmp/")) {
          try {
            rmSync(testPath, { recursive: true });
          } catch {
            /* ignore */
          }
        }
      }
    }
  });

  // -----------------------------------------------------------------------
  // T-0035-013: parseStateFiles graceful exit on nonexistent dir
  // Expected: FAIL before Colby implements (no existsSync guard yet)
  // -----------------------------------------------------------------------
  it("T-0035-013: parseStateFiles returns 0 and does not throw when stateDir does not exist", async () => {
    const { parseStateFiles } = await importHydrate();
    const nonexistentDir = path.join(tmpDir, "this-dir-does-not-exist");

    // parseStateFiles requires pool and config arguments.
    // We pass stub objects since the function should bail out before using them.
    const stubPool = {
      query: async () => { throw new Error("should not be called"); },
      end: async () => {},
    };
    const stubConfig = { scope: "test", database_url: "stub" };

    // The function should NOT throw and should return 0
    const result = await parseStateFiles(nonexistentDir, stubPool, stubConfig);

    assert.strictEqual(
      result,
      0,
      "parseStateFiles must return 0 (zero captures) when stateDir does not exist"
    );
  });

  // -----------------------------------------------------------------------
  // T-0035-014: Explicit --state-dir backward compatibility
  // Expected: FAIL before Colby implements (structural check on source)
  //
  // This is a source-level structural test: verify that the main() function
  // still processes the explicit --state-dir argument, and that the explicit
  // arg pathway exists before the auto-resolve pathway.
  // -----------------------------------------------------------------------
  it("T-0035-014: hydrate-telemetry.mjs main() still processes explicit --state-dir argument", async () => {
    const scriptPath = path.join(
      PROJECT_ROOT,
      "brain/scripts/hydrate-telemetry.mjs"
    );
    const content = readFileSync(scriptPath, "utf-8");

    // The script must accept --state-dir as a CLI argument
    assert.ok(
      content.includes("--state-dir") || content.includes("state-dir"),
      "hydrate-telemetry.mjs must accept a --state-dir CLI argument for backward compatibility"
    );

    // After Colby's changes, the script should also contain resolveAtelierStateDir
    assert.ok(
      content.includes("resolveAtelierStateDir"),
      "hydrate-telemetry.mjs must contain resolveAtelierStateDir for auto-resolution (ADR-0035 R1)"
    );
  });

  // -----------------------------------------------------------------------
  // T-0035-015: Auto-resolve via CLAUDE_PROJECT_DIR
  // Expected: FAIL before Colby implements (no auto-resolution wiring yet)
  //
  // Structural check: the main() function must reference CLAUDE_PROJECT_DIR
  // and/or CURSOR_PROJECT_DIR as part of auto-resolution.
  // -----------------------------------------------------------------------
  it("T-0035-015: hydrate-telemetry.mjs references CLAUDE_PROJECT_DIR for auto-resolution", async () => {
    const scriptPath = path.join(
      PROJECT_ROOT,
      "brain/scripts/hydrate-telemetry.mjs"
    );
    const content = readFileSync(scriptPath, "utf-8");

    // After Colby's changes, main() should reference the env var for auto-resolution
    const hasClaudeProjectDir = content.includes("CLAUDE_PROJECT_DIR");
    const hasCursorProjectDir = content.includes("CURSOR_PROJECT_DIR");

    assert.ok(
      hasClaudeProjectDir,
      "hydrate-telemetry.mjs must reference CLAUDE_PROJECT_DIR for auto-resolution of state dir"
    );

    assert.ok(
      hasCursorProjectDir,
      "hydrate-telemetry.mjs must reference CURSOR_PROJECT_DIR as fallback env var for auto-resolution"
    );
  });

  // -----------------------------------------------------------------------
  // T-0035-016: Graceful fallback when no --state-dir and no env vars
  // Expected: FAIL before Colby implements (no auto-resolution logic yet)
  //
  // Structural check: resolveAtelierStateDir must be in the exports,
  // and the function must handle the case where the computed dir does not
  // exist by returning null (so main() skips state-file parsing).
  // -----------------------------------------------------------------------
  it("T-0035-016: resolveAtelierStateDir is exported from hydrate-telemetry.mjs", async () => {
    const mod = await importHydrate();

    assert.ok(
      typeof mod.resolveAtelierStateDir === "function",
      "hydrate-telemetry.mjs must export resolveAtelierStateDir as a function. " +
        "This is required for brain/lib/hydrate.mjs to reuse the resolution logic."
    );

    // Verify graceful fallback: calling with process.cwd() when no state dir
    // exists at the computed path should return null, not throw.
    const result = mod.resolveAtelierStateDir("/definitely/nonexistent/path/" + Date.now());
    assert.strictEqual(
      result,
      null,
      "resolveAtelierStateDir must return null (not throw) when the computed directory does not exist"
    );
  });

  // -----------------------------------------------------------------------
  // T-0035-017: All existing brain tests pass (regression gate)
  // Expected: PASS currently (no source changes yet)
  // -----------------------------------------------------------------------
  it("T-0035-017: existing brain tests pass (regression gate)", async () => {
    // Run all existing brain tests via subprocess
    // Note: this test file itself is excluded to avoid recursion
    const existingTestFiles = [
      "hydrate-config-resolution.test.mjs",
      "hydrate-mcp-tool.test.mjs",
    ];

    for (const testFile of existingTestFiles) {
      const testPath = path.join(PROJECT_ROOT, "tests/brain", testFile);
      if (!existsSync(testPath)) continue;

      try {
        execSync(`node --test "${testPath}"`, {
          cwd: PROJECT_ROOT,
          encoding: "utf-8",
          timeout: 60000,
          stdio: "pipe",
        });
      } catch (err) {
        assert.fail(
          `Existing brain test ${testFile} failed:\n${err.stdout || ""}\n${err.stderr || ""}`
        );
      }
    }
  });
});
