# QA Check Procedures

<!-- Part of atelier-pipeline. Referenced by Roz during Code QA, Test Spec Review, and Scoped Re-Run modes. -->
<!-- CONFIGURE: Update the placeholders below to match your project -->
<!--
  {typecheck_command} = command to run type checker (e.g., npm run typecheck, mypy .)
  {lint_command}      = command to run linter (e.g., npm run lint, ruff check)
  {test_command}      = command to run full test suite (e.g., npx vitest run, npm test)
  {ux_docs_dir}       = directory for UX design docs (default: docs/ux/)
-->

## Code QA Checks

### Tier 1 -- Mechanical (always run first, stop on failure)

1. Type Check: `{typecheck_command}`
2. Lint: `{lint_command}`
3. Tests -- two modes (Eva signals via invocation):
   - **`unit-qa`** (default, per Colby→Roz handoff): run only the test files
     Eva names in the invocation (ADR-specific tests) plus any test files
     matching changed source files. Do NOT run `{test_command}`. Derive
     targeted files from the diff: for each changed source file, find the
     matching test file by name/path convention.
   - **`wave-sweep`** (pre-Ellis only, Eva explicitly requests): run
     `{test_command}` (full suite). Only one full-suite run per wave.
4. Coverage: run tests with coverage flag -- flag below project-defined
   thresholds (see CLAUDE.md)
5. Complexity: Functions exceeding project-defined thresholds; files with
   excessive length; nesting greater than 3
6. Unfinished markers: Grep for TODO/FIXME/HACK/XXX in all changed files.
   Non-test match is a blocker.

If any Tier 1 check fails, stop and report. Do not run Tier 2 on code that
does not compile or pass tests.

In `unit-qa` mode, run only checks 8 (Security) and 11 (Dependencies) from Tier 2. Skip all other Tier 2 checks unless Eva explicitly requests them in the invocation.

### Tier 2 -- Judgment (run after Tier 1 passes)

7. DB Migrations: reversible? safe for rolling deploy? (if applicable)
8. Security: hardcoded secrets, injection, unvalidated input, missing auth,
   sensitive data in logs
9. CI/CD Compat: conditional when diff touches auth, RBAC, env vars, middleware
10. Docs Impact (mandatory assessment): evaluate whether the diff changes
    user-facing behavior, endpoints, env vars, configuration, or error messages.
    Include a `Doc Impact: YES | NO` verdict. If YES, list which existing docs
    are affected. This triggers Agatha on Small pipelines.
11. Dependencies: new deps -> publish date, vulns, license, necessity
12. UX Flow Verification (blocker when UX doc exists): run
    `ls {ux_docs_dir}/*FEATURE*`. If a UX doc exists, trace every surface
    it specifies against the implementation. Missing UI for a UX-specified
    surface is a blocker.
13. Contract Coverage: conditional when diff touches job kinds, dynamic imports,
    cross-module mapping
14. Wiring verification (blocker when new API endpoints or routes are added in
    the diff, regardless of whether FE changes are present): For each new route
    added in the diff, grep frontend code for its URL/path. If a new route is
    added and no corresponding frontend call exists, that is a BLOCKER. For each
    frontend fetch/API call in the diff, grep backend code for the matching
    route. Orphan endpoints (backend route nothing calls) or phantom calls
    (frontend calling a non-existent endpoint) = BLOCKER. Also verify that the
    response shape consumed by the frontend matches the shape returned by the
    backend (check TypeScript types, interface definitions, or destructuring
    patterns).

## ADR Test Spec Review Mode

When reviewing a test spec (no code yet):
1. Category coverage -- all mandatory categories per step
2. Failure:happy ratio -- failure >= happy
3. Description quality -- specific enough to write test without seeing source
4. Contract boundaries -- all dynamic imports, shape dependencies, status
   consumers identified?
5. Independently identify cases Cal missed
6. UX doc completeness gate (blocker): run `ls {ux_docs_dir}/*FEATURE*`. If
   a UX doc exists, verify every surface has a corresponding ADR step with test
   coverage. Missing steps mean the ADR goes back to Cal.

Output: Coverage table, gaps, missing tests, verdict (APPROVED / REVISE).

## Scoped Re-Run Mode

When invoked after a fix: read `{pipeline_state_dir}/last-qa-report.md` (your own
previous report) to verify full findings from the previous pass. Run failed
checks + targeted tests for affected files + post-fix verification + security
re-check if auth/stores touched + verify all inherited issues are resolved.
Do NOT run the full test suite — that is reserved for the wave-sweep before
Ellis. Same report format with Re-Run header.
