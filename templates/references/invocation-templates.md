# Invocation Templates

<!-- CONFIGURE: Update the placeholders below to match your project -->
<!--
  {product_specs_dir}   = directory for product specs (default: docs/product/)
  {ux_docs_dir}         = directory for UX design docs (default: docs/ux/)
  {architecture_dir}    = directory for ADR files (default: docs/architecture/)
  {features_dir}        = feature directory pattern (e.g., src/features/, app/domains/)
  {test_dir}            = test directory pattern (e.g., tests/, __tests__/, spec/)
  {fast_test_command}   = command for rapid inner-loop tests (e.g., npm run test:fast)
  {test_command}        = command to run full test suite (e.g., npx vitest run, npm test)
-->

Eva loads this file just-in-time when constructing sub-agent invocation
prompts. These are not pre-loaded into Eva's always-on context.

---

**Cal (ADR production -- after conversational clarification):**
> TASK: Produce ADR for [feature name]
> READ: {product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md, {product_specs_dir}/FEATURE-doc-plan.md, .claude/references/retro-lessons.md
> CONTEXT: [User preferences and decisions from context-brief.md]
> WARN: [Specific pattern if recurred 3x in error-patterns.md, otherwise omit]
> CONSTRAINTS:
> - Map blast radius (every file, module, integration, CI/CD impact)
> - Minimum two alternatives with concrete tradeoffs
> - Comprehensive test spec: failure tests >= happy path tests
> OUTPUT: ADR saved to {architecture_dir}/ADR-NNNN-feature-name.md with DoR/DoD sections

**Colby (mockup mode -- after Sable, before Cal):**
> TASK: Build mockup for [feature name]
> READ: {product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md, .claude/references/retro-lessons.md
> CONTEXT: [User preferences from context-brief.md]
> CONSTRAINTS:
> - Real components in {features_dir}/feature-name/ using existing component library
> - Wire to mock data hook, NOT API calls
> - Implement all states from Sable's doc (empty, loading, populated, error, overflow)
> - Add route and nav item. No backend, no tests.
> OUTPUT: Route path, list of files created, state switching instructions, with DoR/DoD sections

**Roz (bug investigation -- user reports a bug):**
> TASK: Investigate bug -- [observed symptom, not theory]
> HYPOTHESES: [Eva's theory] | [alternative at different layer]
> READ: [relevant feature and API files], .claude/references/retro-lessons.md
> CONSTRAINTS:
> - Trace the full request path: frontend call -> API route -> handler -> data access
> - Run relevant tests to confirm bug. Check API logs.
> - Identify root cause with file paths and line numbers
> - Check for related issues in the same area
> - Do NOT write code -- diagnosis only
> OUTPUT: Bug report with: symptom, root cause (file:line), affected code path, fix description, related issues

**Roz (test spec review -- after Cal, before Colby build):**
> TASK: Review test spec for ADR-NNNN
> READ: {architecture_dir}/ADR-NNNN-feature-name.md, {product_specs_dir}/FEATURE.md, .claude/references/retro-lessons.md
> CONSTRAINTS:
> - Check failure:happy ratio (failure >= happy, hard rule)
> - Check description quality (specific enough to write test without source)
> - Verify Cal's DoR covers all spec requirements -- flag any silent drops
> - Independently identify cases Cal missed
> OUTPUT: Category coverage table, gaps found, missing tests, Cal DoR verification, verdict (APPROVED / REVISE)

**Roz (test authoring -- pre-build, per ADR step):**
> TASK: Write test assertions for ADR-NNNN Step N -- [step description]
> READ: {architecture_dir}/ADR-NNNN-feature-name.md (Step N), {product_specs_dir}/FEATURE.md, [relevant source files], .claude/references/retro-lessons.md
> CONSTRAINTS:
> - Write concrete test assertions, not descriptions
> - Assert DOMAIN-CORRECT behavior, not current code behavior
> - For each utility/helper: reason about what the function name MEANS semantically
> - If existing code contradicts domain intent, write the test for correct behavior -- Colby will fix the code
> - Flag any ambiguous domain intent for Eva
> OUTPUT: Test files in {test_dir}/ matching ADR step scope, with DoR/DoD sections

**Colby (build mode -- unit N):**
> TASK: Implement ADR-NNNN Step N -- [description]
> READ: {architecture_dir}/ADR-NNNN-feature-name.md, [Roz-authored test files], .claude/references/retro-lessons.md
> CONTEXT: Roz's test files define correct behavior. Make them pass. Do not modify Roz's assertions.
> CONSTRAINTS:
> - Make Roz's pre-written tests pass -- NEVER modify her assertions
> - **Inner loop:** `{fast_test_command}` for rapid iteration. **Full suite** at unit completion.
> - If a Roz test fails against existing code, the code has a bug -- fix it
> - When fixing a shared utility bug, grep for all instances codebase-wide
> - Zero TODO/FIXME/HACK in delivered code
> OUTPUT: Step N complete report with DoR/DoD sections, Bugs Discovered section, files changed

**Roz (code QA -- first pass, after Colby build):**
> TASK: Full QA on ADR-NNNN implementation
> READ: {architecture_dir}/ADR-NNNN-feature-name.md, {product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md, .claude/references/retro-lessons.md
> DIFF: [output of `git diff --stat` and `git diff --name-only` for unit N]
> CONSTRAINTS:
> - Run all QA checks in order (per your persona file)
> - REQUIREMENTS TO VERIFY: [Eva pastes enumerated requirements from spec/ADR here]
> - Verify Colby's DoD coverage claims against actual code
> - Grep for TODO/FIXME/HACK/XXX in all changed files -- non-test code match = BLOCKER
> OUTPUT: QA Report with verdict, check table, requirements verification, issues found

**Roz (scoped re-run -- after Colby fix):**
> TASK: Scoped QA re-run on ADR-NNNN fix
> READ: {architecture_dir}/ADR-NNNN-feature-name.md, .claude/references/retro-lessons.md
> DIFF: [files changed in fix]
> CONSTRAINTS:
> - Failed checks from first pass: [list specific failed checks]
> - Inherited MUST-FIX from previous reports: [list items and original report dates]
> - SCOPED RE-RUN -- only re-check failed items + tests + post-fix verification
> - Do NOT re-run dependency audit, exploratory, CI/CD checks
> - Re-verify any requirements flagged as BLOCKER in first pass
> OUTPUT: Scoped QA Report with re-run header, updated requirements verification

**Ellis:**
> TASK: Commit ADR-NNNN ([feature name]) -- QA passed
> READ: {architecture_dir}/ADR-NNNN-feature-name.md, .claude/references/retro-lessons.md
> CONSTRAINTS:
> - Analyze the full diff, not just the last commit
> - Narrative commit body, not bullet points (what + why, skip how)
> - Include Changelog trailer for user-facing changes
> - Do not push without user approval
> OUTPUT: Proposed commit message, then commit + push after confirmation

**Agatha (writing mode):**
> TASK: Write documentation for [feature name]
> READ: {product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md, {architecture_dir}/ADR-NNNN-feature-name.md, {product_specs_dir}/FEATURE-doc-plan.md, .claude/references/retro-lessons.md
> CONSTRAINTS:
> - Follow doc plan
> - Read actual code for accuracy -- specs describe intent, code describes reality
> - Match existing doc structure and voice. One audience per document.
> - Flag spec-vs-code divergences
> OUTPUT: Documentation files per doc plan with DoR/DoD sections, list of files written/updated
