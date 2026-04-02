# QA Report -- 2026-04-02
*Reviewed by Roz*
*Mode: ADR Test Spec Review -- ADR-0020 Wave 2 Hook Modernization*

---

## Verdict: REVISE

---

## Per-Step Findings

### Step 1 (Unit 2a: `if` Conditionals) -- Tests T-0020-001 through T-0020-008

**Category balance:** 5 Happy/Regression, 0 Failure, 1 Boundary, 1 explicit regression
**Required ratio check:** Failure >= Happy -- NOT MET. Zero failure cases for this step.

**Finding 1 (GAP -- FIX REQUIRED):** T-0020-001 and T-0020-002 are JSON structure assertions
against settings.json. The description says "settings.json contains..." but does not specify
which settings.json is under test -- the source template (`skills/pipeline-setup/SKILL.md`)
or the installed copy (`.claude/settings.json`). The ADR's AC3 requires both match, meaning
three distinct assertions are needed (source, installed, and a cross-file comparison). As written,
Colby could write a test against either file and claim coverage. Split into T-0020-001a (source
template contains the `if` field) and T-0020-001b (installed .claude/settings.json contains the
`if` field), and clarify T-0020-007 as the cross-file comparison test.

**Finding 2 (GAP -- FIX REQUIRED):** Step 1 AC5 reads: "A Bash call without 'git ' in the
command does not spawn enforce-git.sh (verified by `if` field presence, not testable in bats
since bats runs the script directly)." The ADR acknowledges this is untestable in bats. However,
no test ID is assigned to verify the proxy assertion (that the `if` field string value is correct).
T-0020-001 is the closest proxy, but it is listed under a different description that does not
explicitly link to AC5. The spec must either (a) update T-0020-001 or T-0020-007 to explicitly
state they serve as the AC5 proxy, or (b) add a new test ID that asserts the `if` expression
string matches exactly what Claude Code would need to evaluate. AC5 is currently unverifiable
by any listed test.

**Finding 3 (UNTESTABLE AS WRITTEN):** T-0020-008 description is "enforce-git.sh still blocks
git commit when called directly (if filter only prevents spawning, not script behavior)." This
is functionally identical to the existing test in enforce-git.bats:
`"enforce-git: git commit from main thread exits 2 with BLOCKED"`. T-0020-008 as described
would produce a duplicate test with the same assertion. Colby would need to either skip it
(violating test-ID coverage) or write a redundant test (causing a name collision in bats output).
The description must be differentiated to explain what new scenario or framing this test adds
that the existing regression test (T-0020-003) does not already cover.

**Missing failure cases for Step 1:**
- No test for: settings.json has the enforce-git.sh hook entry but the `if` field is missing
  entirely (partial config error -- hook spawns on every Bash call, defeating the optimization).
- No test for: the `if` expression contains a typo (e.g., `'git'` without the trailing space)
  resulting in over-filtering or under-filtering.

---

### Step 2a (SubagentStart Hook) -- Tests T-0020-009 through T-0020-016

**Category balance:** 2 Happy, 2 Failure, 2 Boundary, 1 Security, 0 Regression
**Required ratio check:** Failure >= Happy -- MET (2 == 2).

**Finding 4 (UNTESTABLE AS WRITTEN):** T-0020-011 says "Hook exits 0 when `.claude/telemetry/`
directory cannot be created (read-only filesystem simulation)." "Read-only filesystem simulation"
is not an actionable bats test description. Bats tests run in a temp directory; simulating a
read-only filesystem requires a specific technique (e.g., `chmod 000` on the target parent
directory, `mount --bind` with ro flag on Linux, or `chflags uchg` on macOS). Colby must choose
one of these -- the choice determines whether the test passes on macOS vs. Linux CI. Specify
exactly: "chmod 000 on the `.claude/` parent directory before the hook runs, then restore
permissions in teardown." Without this specification, the test is not portable.

**Finding 5 (DOMAIN INTENT AMBIGUITY -- must resolve before build):** T-0020-012 says "Hook
exits 0 when jq is not available -- falls back to printf-based JSON generation." Step 2a AC5
says only "Hook exits 0 when jq is not available" with no mention of fallback behavior. There
are two valid implementations: (a) exit 0 silently, writing nothing to the JSONL file, or
(b) exit 0 and write a JSON line using printf. These produce different downstream behavior:
option (a) means jq-less systems silently lose telemetry; option (b) means they continue
capturing. T-0020-024 asserts "JSONL file can be read by jq -s after multiple start+stop pairs"
-- if the jq-absent path writes nothing, T-0020-024 cannot cover that scenario. The domain
intent must be specified: which behavior is correct? Flag this for Cal to resolve before
Colby starts.

**Finding 6 (GAP -- FIX REQUIRED):** T-0020-009 tests that the hook "creates `.claude/telemetry/`
directory AND writes a JSON line" in a single test. This conflates two distinct behaviors: directory
creation (AC1) and JSONL write (AC2). If directory creation succeeds but the write fails for a
separate reason, this test cannot isolate which AC failed. The existing bats pattern (as seen in
enforce-paths.bats) tests each behavior with a dedicated assertion. Recommend splitting: one test
for directory creation from a state where `.claude/telemetry/` does not exist, one test for JSONL
line content verification when the directory already exists.

**Finding 7 (MISSING BOUNDARY):** No test covers the case where the JSONL file already contains
content from a prior session. T-0020-015 covers "multiple sequential calls append multiple lines"
within a single test run, but this is different from a pre-populated file at test setup time. A
hook that truncates instead of appends would pass T-0020-015 (if all calls are in the same run
and the file starts empty) but would destroy prior session data in production. Add a test that
pre-populates the JSONL file with one line, runs the hook, and verifies both lines are present.

**Missing failure cases for Step 2a:**
- No test for: `CLAUDE_PROJECT_DIR` environment variable is unset or empty. The JSONL path
  (`$CLAUDE_PROJECT_DIR/.claude/telemetry/session-hooks.jsonl`) depends on this variable. An
  unset variable produces a path like `/.claude/telemetry/session-hooks.jsonl` which will fail
  or write to the root filesystem. The hook must handle this gracefully (exit 0, log warning to
  stderr, no write attempt to a path starting with `//` or `/`).

---

### Step 2b (SubagentStop Telemetry Hook) -- Tests T-0020-017 through T-0020-024

**Category balance:** 2 Happy, 2 Failure, 2 Boundary, 1 Regression, 1 Concurrency
**Required ratio check:** Failure >= Happy -- MET (2 == 2).

**Finding 8 (UNTESTABLE AS WRITTEN):** T-0020-022 says "warn-dor-dod.sh still receives
SubagentStop events and functions correctly (both hooks coexist)." Bats runs hook scripts
in isolation -- it cannot simulate the Claude Code engine dispatching the same event to two
separate scripts in sequence. What T-0020-022 is actually verifying (script-level independence)
is testable in bats, but the description frames it as engine-level coexistence, which is not.
Rewrite to: "log-agent-stop.sh and warn-dor-dod.sh each produce correct output independently
when given the same SubagentStop JSON input -- neither script modifies shared state that
would interfere with the other." This is concrete and bats-testable.

**Finding 9 (UNTESTABLE AS WRITTEN):** T-0020-023 says "Two SubagentStop hooks registered
in the same event array -- both execute without interference." Same category error as T-0020-022.
"Registered in the same event array" is a settings.json configuration assertion, not a script
behavior assertion. Bats cannot verify that two hooks registered in the same array both fire.
Rewrite to: "Both log-agent-stop.sh and warn-dor-dod.sh produce their expected outputs when
invoked with identical SubagentStop JSON -- scripts do not depend on shared temp files or
environment variables that would conflict." Alternatively, move this to a structural test
verifying that settings.json contains both scripts in the SubagentStop array (testable via jq).

**Finding 10 (MISSING HELPER VALIDATION):** Step 2b lists adding `build_subagent_stop_input`
to test_helper.bash. There is no test verifying this helper produces correctly structured JSON
for the SubagentStop event format. A helper that produces malformed JSON would cause all Step 2b
tests to pass vacuously (the hook receives garbage, cannot parse it with jq, and exits 0 for
the wrong reason). Add one test that calls the helper and pipes its output through `jq .` to
verify valid JSON, and checks that key fields (`agent_type`, `agent_id`, `session_id`,
`last_assistant_message`) are present in the output.

**Missing failure cases for Step 2b:**
- No test for: `has_output` when `last_assistant_message` is present but is an empty string `""`
  (distinct from null and from absent). The spec says "empty or null" maps to false but the
  implementation must handle the empty-string case explicitly. Specify whether `""` maps to
  `has_output: false`.

---

### Step 3 (PostCompact Hook) -- Tests T-0020-025 through T-0020-033

**Category balance:** 3 Happy, 2 Failure, 2 Boundary, 1 Regression, 1 Security
**Required ratio check:** Failure >= Happy -- NOT MET (2 < 3).

**Finding 11 (AMBIGUOUS ACCEPTANCE CRITERION):** T-0020-030 says "Output contains file path
labels so Eva knows which file content is which." AC2 in Step 3 says "outputs both files'
contents to stdout with clear section markers" and AC3 specifies a top-level header
`--- Re-injected after compaction ---`. Neither AC specifies the per-file label format.
T-0020-030 must assert a specific format -- if Colby writes `## pipeline-state.md` and the
test checks for `=== pipeline-state.md ===`, the test fails for the wrong reason. The ADR must
specify the exact per-file section marker format. Update AC2 with the format (e.g.,
`### File: pipeline-state.md`) and update T-0020-030 to assert that exact string.

**Finding 12 (AMBIGUOUS EXPECTED OUTPUT):** T-0020-032 says "Hook exits 0 when both files
are empty." The expected output is not stated. AC4 says "if pipeline-state.md does not exist,
hook outputs nothing." An empty file is a different condition from non-existent. When both files
exist but are empty, does the hook output nothing, the header only, or the header plus empty
sections? The test must specify the expected stdout content (or lack thereof).

**Finding 13 (GAP -- PRODUCTION CORRECTNESS RISK):** No AC and no test addresses how the hook
resolves the path to pipeline-state.md and context-brief.md. The ADR says these files are read
"from project root" but does not specify the mechanism (env var, relative to hook's `$0` location,
relative to cwd, or via enforcement-config.json). This matters because bats tests run the hook
from `$TEST_TMPDIR` -- if the hook uses a relative path, it will look for these files relative
to `$TEST_TMPDIR`, which is where test setup puts them. But in production, the hook is run by
Claude Code and the cwd may be different. The path resolution mechanism must be specified as an
AC and a test must verify it (e.g., "hook reads `$CLAUDE_PROJECT_DIR/docs/pipeline/pipeline-state.md`
when that env var is set, and falls back to `./docs/pipeline/pipeline-state.md` otherwise").

**Missing failure cases for Step 3:**
- No test for: pipeline-state.md exists but cannot be read (permissions error) -- hook should
  still exit 0 per R8, and should output nothing for that file (not an error message that gets
  injected into context).
- AC7 states "Output is small enough to inject (~3KB for both files combined)" -- no test
  enforces any upper bound. A pipeline-state.md that grows to 50KB (legitimate after a long
  pipeline) would be injected in full. Add either a size check test or explicitly document
  that no truncation occurs and AC7 is advisory only.

---

### Step 4 (StopFailure Hook) -- Tests T-0020-034 through T-0020-043

**Category balance:** 2 Happy, 3 Failure, 2 Boundary, 1 Security, 1 Regression
**Required ratio check:** Failure >= Happy -- MET (3 >= 2).

**Finding 14 (AMBIGUOUS ACCEPTANCE CRITERION):** T-0020-036 says "Hook creates error-patterns.md
with header when file does not exist." AC4 says "If error-patterns.md does not exist, hook creates
it with a header." Neither specifies the header text. If Colby writes `# Error Patterns` and the
test asserts `# API Error Patterns`, both fail for different reasons. The header format must be
specified in AC4, and T-0020-036 must assert the exact header text.

**Finding 15 (OVERLAP -- FIX REQUIRED):** T-0020-042 "Hook does not log full stack traces or
sensitive error details beyond 200 chars" overlaps with T-0020-039 "Error message is truncated
to 200 characters" in both substance and implementation. Both tests would verify that the
appended message length is at most 200 characters -- they produce identical bats assertions.
Either merge these two tests or rewrite T-0020-042 to test a distinct security property: for
example, "hook does not write the raw full StopFailure JSON input to any output stream (stdout
or the appended file)" -- verifying that context from the agent turn is not accidentally logged
in full.

**Finding 16 (BOUNDARY PRECISION -- FIX REQUIRED):** T-0020-039 "Error message is truncated
to 200 characters" does not specify whether the test uses a message of exactly 200, 201, or
significantly longer characters. A test using a 500-character message verifies that truncation
occurs, but does not verify the boundary is 200 (vs. 199, 201, or 256). Add: one test with a
200-character message (should NOT be truncated), one test with a 201-character message (SHOULD
be truncated to exactly 200 characters). The existing T-0020-039 description covers neither
boundary case precisely.

**Finding 17 (MISSING FAILURE CASE):** No test addresses the path resolution mechanism for
error-patterns.md. Other hooks (enforce-paths.sh, enforce-git.sh, enforce-sequencing.sh) all
read their target paths from enforcement-config.json's `pipeline_state_dir` field. AC2 of Step 4
says the hook appends to `docs/pipeline/error-patterns.md` but does not specify whether this
path is hardcoded or read from enforcement-config.json. If hardcoded, the hook breaks in projects
that configure a different pipeline_state_dir. Add an AC and test for path resolution -- consistent
with the pattern used by other hooks.

---

### Step 5 (Documentation) -- Tests T-0020-044 through T-0020-047

**Category balance:** 2 Happy, 0 Failure, 0 Boundary, 2 Regression
**Required ratio check:** Failure >= Happy -- NOT MET (0 < 2).

**Finding 18 (MISSING FAILURE CASES):** Documentation-only steps have fewer failure cases,
but two are identifiable and absent:
- No test for: technical-reference.md still references the old hook count (6 hooks) rather
  than the updated count (10 hooks). A grep for "6" in a hook-count context would catch this.
- No test for: Cursor plugin SKILL.md differs from Claude Code SKILL.md (line count differs
  or a hook entry appears in one but not the other).

**Finding 19 (AMBIGUOUS ASSERTION):** T-0020-044 "technical-reference.md documents all 10 hooks
with event type, script name, and purpose." The assertion on "purpose" is subjective and
untestable in bats (what constitutes adequate purpose documentation?). Narrow to a concrete
assertion: "for each of the 10 hook script names, technical-reference.md contains at least one
line with the script filename and at least one of the event type keywords (SubagentStart,
SubagentStop, PostCompact, StopFailure, PreToolUse, PreCompact)." This is grep-implementable.

**Finding 20 (UNSPECIFIED ASSERTION MECHANISM):** T-0020-046 "All installed .claude/hooks/
files match source/hooks/ files" and T-0020-047 "Cursor plugin SKILL.md matches Claude Code
SKILL.md" do not specify the comparison method. Options include: byte-for-byte diff (strict),
normalized diff ignoring whitespace (lenient), or field-level JSON comparison. Specify: "a diff
invocation exits 0 for each hook script name (byte-for-byte comparison)." Without this
specification, Colby cannot write a deterministic test.

---

## ID Uniqueness and Sequencing Verification

All 47 IDs (T-0020-001 through T-0020-047) are unique and sequential. No gaps, no duplicates.
No conflicts with existing T-0003-* or T-0013-* namespaces in the test suite.

---

## AC-to-Test Coverage Mapping

| Step | AC | Covered by Test(s) | Finding |
|------|----|--------------------|---------|
| Step 1 | AC1 | T-0020-001 | PARTIAL -- source vs. installed ambiguous (Finding 1) |
| Step 1 | AC2 | T-0020-002 | PARTIAL -- same ambiguity (Finding 1) |
| Step 1 | AC3 | T-0020-007 | YES |
| Step 1 | AC4 | T-0020-003 through T-0020-006 | YES |
| Step 1 | AC5 | NONE | GAP -- acknowledged in ADR but uncovered (Finding 2) |
| Step 2a | AC1 | T-0020-009 | PARTIAL -- conflated with AC2 (Finding 6) |
| Step 2a | AC2 | T-0020-009, T-0020-010 | PARTIAL -- conflated (Finding 6) |
| Step 2a | AC3 | T-0020-009 | YES (fields listed in description) |
| Step 2a | AC4 | T-0020-011 | PARTIAL -- simulation technique unspecified (Finding 4) |
| Step 2a | AC5 | T-0020-012 | PARTIAL -- fallback behavior unspecified (Finding 5) |
| Step 2a | AC6 | NOT COVERED | GAP -- no bats test for settings.json registration |
| Step 2a | AC7 | NOT COVERED | GAP -- no bats test for SKILL.md update |
| Step 2b | AC1 | T-0020-017 | YES |
| Step 2b | AC2 | T-0020-017, T-0020-018 | YES |
| Step 2b | AC3 | T-0020-021 | YES |
| Step 2b | AC4 | T-0020-019 | YES |
| Step 2b | AC5 | T-0020-020 | YES |
| Step 2b | AC6 | NOT COVERED | GAP -- same settings.json gap as 2a AC6 |
| Step 2b | AC7 | T-0020-022 | UNTESTABLE AS WRITTEN (Finding 8) |
| Step 2b | AC8 | T-0020-023 | UNTESTABLE AS WRITTEN (Finding 9) |
| Step 3 | AC1 | T-0020-025, T-0020-026 | YES |
| Step 3 | AC2 | T-0020-025, T-0020-026 | PARTIAL -- per-file labels unspecified (Finding 11) |
| Step 3 | AC3 | T-0020-027 | YES |
| Step 3 | AC4 | T-0020-028 | YES |
| Step 3 | AC5 | T-0020-029 | YES |
| Step 3 | AC6 | T-0020-028, T-0020-032 | PARTIAL -- exit-0 confirmed; expected output ambiguous (Finding 12) |
| Step 3 | AC7 | NONE | GAP -- no test enforces ~3KB bound |
| Step 3 | AC8 | T-0020-031 | YES |
| Step 4 | AC1 | T-0020-034 | YES |
| Step 4 | AC2 | T-0020-034, T-0020-035 | YES |
| Step 4 | AC3 | T-0020-035 | YES (format in description matches AC3) |
| Step 4 | AC4 | T-0020-036 | PARTIAL -- header text unspecified (Finding 14) |
| Step 4 | AC5 | T-0020-037 | YES |
| Step 4 | AC6 | T-0020-038 | YES |
| Step 4 | AC7 | T-0020-039 | PARTIAL -- boundary precision insufficient (Finding 16) |
| Step 4 | AC8 | NOT COVERED | GAP -- no bats test for settings.json registration |
| Step 5 | AC1 | T-0020-044 | PARTIAL -- "purpose" is subjective (Finding 19) |
| Step 5 | AC2 | T-0020-045 | YES |
| Step 5 | AC3 | T-0020-046 | PARTIAL -- assertion mechanism unspecified (Finding 20) |
| Step 5 | AC4 | T-0020-047 | PARTIAL -- assertion mechanism unspecified (Finding 20) |

**Recurring gap:** AC for settings.json registration appears in Steps 2a, 2b, 3, and 4 but
has no corresponding bats test in any of those steps. Step 1's T-0020-001/002 are the closest
proxy but are scoped to Step 1's specific `if` field assertions. Cal should add a cross-step
structural test (settings-registration.bats or similar) or explicitly designate T-0020-001/002
as the canonical settings.json tests and cross-reference them from each step's AC table.

---

## Issues Found

**BLOCKER (Colby cannot build to this spec as-written):**

1. **T-0020-001 / T-0020-002 (Step 1):** Both tests are ambiguous about which settings.json
   file is under test. The ADR's AC3 requires both the source template and installed copy to
   match, meaning at minimum two test IDs are required per assertion. Add T-0020-001a (source)
   and T-0020-001b (installed), and clarify T-0020-007 as the cross-file diff test.

2. **Step 1 AC5 (unassigned test):** No test ID covers AC5 (the `if` field prevents spawning).
   The ADR acknowledges this is not bats-testable as a process-spawn verification, but the
   proxy assertion (the `if` field string value in settings.json) is bats-testable and must be
   assigned to an explicit test ID so coverage is not lost.

3. **T-0020-008 (Step 1):** Description is a functional duplicate of an existing enforce-git.bats
   test. Colby cannot write this test without creating a bats name collision or a redundant
   assertion. Differentiate the description to explain what this test adds beyond T-0020-003
   (regression catch on all existing bats tests passing).

4. **T-0020-011 (Step 2a):** "Read-only filesystem simulation" is not an actionable description
   for a bats test. Platform-specific technique must be specified. Colby writing this test on
   macOS would use a different mechanism than on Linux CI, producing a test that is not portable.

5. **T-0020-012 (Step 2a) -- domain intent unresolved:** Whether the jq-absent fallback writes
   a JSON line via printf or exits 0 silently is unspecified. This decision propagates to
   T-0020-024. Cal must resolve before Colby implements.

6. **T-0020-022 and T-0020-023 (Step 2b):** Both describe engine-level behavior (Claude Code
   dispatching the same event to two hooks) that bats cannot test. Rewrite to script-level
   assertions (each script independently produces correct output) or move to a manual integration
   test category explicitly labeled as outside the bats suite.

7. **T-0020-030 (Step 3):** Per-file label format is unspecified in the ADR. The test cannot
   assert a specific label without knowing what the hook will produce. AC2 must be updated with
   the exact per-file section marker format before Colby can implement.

8. **Finding 13 -- PostCompact path resolution (Step 3):** No AC and no test covers path
   resolution for pipeline-state.md and context-brief.md. This is the most significant
   production-correctness risk in the spec: if the hook uses a cwd-relative path and Claude
   Code runs it from a different working directory than tests assume, the hook will silently
   output nothing in production. Add an explicit AC and corresponding test.

**FIX-REQUIRED (all resolved before Ellis commits):**

9. **T-0020-036 / AC4 (Step 4):** Header text for a newly created error-patterns.md is
   unspecified. Update AC4 with the exact header format, and update T-0020-036 to assert it.

10. **T-0020-039 (Step 4):** Add boundary precision: one test with a 200-character message
    (no truncation), one test with a 201-character message (truncated to exactly 200 characters).
    The existing description covers "long message is truncated" but not the exact boundary.

11. **T-0020-042 (Step 4):** Overlaps with T-0020-039. Either merge or rewrite to a distinct
    security assertion: "hook does not write raw StopFailure JSON input to any output channel
    (stdout or the appended file)."

12. **T-0020-044 (Step 5):** Rewrite to a grep-implementable assertion: each of the 10 hook
    script names appears in technical-reference.md alongside at least one event type keyword.
    Drop the subjective "purpose" criterion.

13. **T-0020-046 / T-0020-047 (Step 5):** Specify assertion mechanism as byte-for-byte diff
    (diff command exits 0) for each hook script and for the SKILL.md comparison.

14. **Missing test (Step 2a):** Add a test for when CLAUDE_PROJECT_DIR is unset or empty --
    verify the hook exits 0 with a warning to stderr and does not attempt a write to a path
    beginning with `//` or `/` root.

15. **Missing test (Step 2b):** Specify and test the `has_output` behavior when
    `last_assistant_message` is an empty string `""` (not null, not absent).

16. **Missing test (Step 4):** Add a test verifying error-patterns.md path is derived from
    enforcement-config.json `pipeline_state_dir` field, consistent with other hooks. Hardcoded
    paths break projects with non-default pipeline_state_dir configurations.

17. **Systemic settings.json registration gap (Steps 2a, 2b, 3, 4):** AC for settings.json
    registration is listed in each step but not covered by any test in those steps. Add a
    cross-step settings-registration test file or explicitly cross-reference T-0020-001/002 as
    the canonical coverage for all settings.json ACs and document this decision in each step's
    test table.

---

## Doc Impact: NO

This is a test spec review of an ADR in pre-build state. No production code or documentation
has changed. When the ADR moves to implementation, Step 5 is entirely documentation work and
will require Agatha.

---

## Roz's Assessment

The ADR-0020 test spec shows strong structural thinking: JSONL append rather than brain calls
aligns with retro lesson #003, the new event types are well-motivated, and most bats test
descriptions are concrete enough to implement. Cal correctly self-identified the AC5 untestability
and flagged it in the ADR text -- that is the right transparency.

However, eight blockers prevent Colby from building to this spec as-written. The most acute
are the engine-level test descriptions (T-0020-022, T-0020-023) that bats physically cannot
verify, the unresolved domain intent on jq-absent fallback behavior (T-0020-012), and the
missing path resolution spec for the PostCompact hook -- which is the single highest
production-correctness risk in the entire ADR.

The systemic settings.json registration gap (no bats test for any per-step registration AC
beyond Step 1) appears to be a template carry-over from the step structure. It needs one
explicit resolution decision rather than individual fixes per step.

The spec should return to Cal for revision on the 8 blockers. The 9 FIX-REQUIRED items can
be incorporated in the same revision pass. Once Cal revises, this spec is worth a second
Roz review before Colby starts -- the engine-level test rewrites in particular need verification
that the replacement descriptions are bats-implementable.
