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

<template id="cal-adr">

### Cal (ADR Production)

After conversational clarification is complete, Eva invokes Cal to produce
the ADR.

<task>Produce ADR for [feature name]</task>

<brain-context>
If brain is available, Eva pre-fetches and injects relevant context here:
<thought type="decision" agent="cal" phase="design" relevance="0.85">Prior architectural decisions relevant to this feature area</thought>
<thought type="rejection" agent="cal" phase="design" relevance="0.75">Previously rejected approaches with reasoning</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this feature area</thought>
</brain-context>

<context>[User preferences and decisions from context-brief.md]</context>

<read>{product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md, {product_specs_dir}/FEATURE-doc-plan.md, .claude/references/retro-lessons.md</read>

<warn>[Specific pattern if recurred 3x in error-patterns.md, otherwise omit this tag]</warn>

<constraints>
- Map blast radius (every file, module, integration, CI/CD impact)
- Minimum two alternatives with concrete tradeoffs
- Comprehensive test spec: failure tests >= happy path tests
</constraints>

<output>ADR saved to {architecture_dir}/ADR-NNNN-feature-name.md with DoR/DoD sections</output>

</template>

<template id="cal-adr-large">

### Cal (Large ADR Production -- With Research Brief)

For large pipelines, Eva provides a research brief with pre-gathered context.

<task>Produce ADR for [feature name]</task>

<brain-context>
<thought type="decision" agent="cal" phase="design" relevance="0.85">Prior architectural decisions from agent_search("architecture:{feature}")</thought>
<thought type="rejection" agent="cal" phase="design" relevance="0.80">Rejected approaches from agent_search("rejection:{feature}")</thought>
<thought type="pattern" agent="colby" phase="build" relevance="0.75">Proven patterns from agent_search("pattern:{tech_stack}")</thought>
</brain-context>

<context>[User preferences from context-brief.md]

Research Brief (Large pipeline):
- Existing patterns: [grep results -- file paths + pattern descriptions]
- Dependencies: [relevant libraries from package.json/requirements.txt with versions]
- Brain-surfaced decisions: [prior architectural decisions]
- Brain-surfaced rejections: [rejected approaches]
- Brain-surfaced patterns: [proven patterns]</context>

<read>{product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md, {product_specs_dir}/FEATURE-doc-plan.md, .claude/references/retro-lessons.md</read>

<warn>[Specific pattern if recurred 3x in error-patterns.md, otherwise omit this tag]</warn>

<constraints>
- Map blast radius (every file, module, integration, CI/CD impact)
- Minimum two alternatives with concrete tradeoffs
- Comprehensive test spec: failure tests >= happy path tests
- Reference research brief findings in Alternatives Considered section
</constraints>

<output>ADR saved to {architecture_dir}/ADR-NNNN-feature-name.md with DoR/DoD sections</output>

</template>

<template id="colby-mockup">

### Colby Mockup (After Sable, Before Cal)

<task>Build mockup for [feature name]</task>

<brain-context>
<thought type="pattern" agent="colby" phase="build" relevance="0.80">Implementation patterns and known gotchas for this feature area</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this feature area</thought>
</brain-context>

<context>[User preferences from context-brief.md]</context>

<read>{product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md, .claude/references/retro-lessons.md</read>

<constraints>
- Real components in {features_dir}/feature-name/ using existing component library
- Wire to mock data hook, not API calls
- Implement all states from Sable's doc (empty, loading, populated, error, overflow)
- Add route and nav item. No backend, no tests.
</constraints>

<output>Route path, list of files created, state switching instructions, with DoR/DoD sections</output>

</template>

<template id="colby-build">

### Colby Build (Unit N)

<task>Implement ADR-NNNN Step N -- [description]</task>

<brain-context>
<thought type="pattern" agent="colby" phase="build" relevance="0.80">Implementation patterns and known gotchas for this area</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this area</thought>
</brain-context>

<context>Roz's test files define correct behavior. Make them pass. Do not modify Roz's assertions.</context>

<read>{architecture_dir}/ADR-NNNN-feature-name.md, [Roz-authored test files], .claude/references/retro-lessons.md</read>

<constraints>
- Make Roz's pre-written tests pass -- do not modify her assertions
- Inner loop: `{fast_test_command}` for rapid iteration. Full suite at unit completion.
- If a Roz test fails against existing code, the code has a bug -- fix it
- When fixing a shared utility bug, grep for all instances codebase-wide
- Zero TODO/FIXME/HACK in delivered code
</constraints>

<output>Step N complete report with DoR/DoD sections, Bugs Discovered section, files changed</output>

</template>

<template id="roz-investigation">

### Roz Investigation (User Reports a Bug)

<task>Investigate bug -- [observed symptom, not theory]</task>

<hypotheses>[Eva's theory] | [alternative at different layer]</hypotheses>

<brain-context>
<thought type="pattern" agent="roz" phase="qa" relevance="0.80">Recurring QA patterns and prior findings on similar code</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this area</thought>
</brain-context>

<read>[relevant feature and API files], .claude/references/retro-lessons.md</read>

<constraints>
- Trace the full request path: frontend call -> API route -> handler -> data access
- Run relevant tests to confirm bug. Check API logs.
- Identify root cause with file paths and line numbers
- Check for related issues in the same area
- Do not write code -- diagnosis only
</constraints>

<output>Bug report with: symptom, root cause (file:line), affected code path, fix description, related issues</output>

</template>

<template id="roz-test-spec-review">

### Roz Test Spec Review (After Cal, Before Colby Build)

<task>Review test spec for ADR-NNNN</task>

<brain-context>
<thought type="pattern" agent="roz" phase="qa" relevance="0.80">Recurring QA patterns on this module</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this area</thought>
</brain-context>

<read>{architecture_dir}/ADR-NNNN-feature-name.md, {product_specs_dir}/FEATURE.md, .claude/references/retro-lessons.md</read>

<constraints>
- Check failure:happy ratio (failure >= happy, hard rule)
- Check description quality (specific enough to write test without source)
- Verify Cal's DoR covers all spec requirements -- flag any silent drops
- Independently identify cases Cal missed
</constraints>

<output>Category coverage table, gaps found, missing tests, Cal DoR verification, verdict (APPROVED / REVISE)</output>

</template>

<template id="roz-test-authoring">

### Roz Test Authoring (Pre-Build, Per ADR Step)

<task>Write test assertions for ADR-NNNN Step N -- [step description]</task>

<brain-context>
<thought type="pattern" agent="roz" phase="qa" relevance="0.80">Test strategies that worked/failed on similar code</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this area</thought>
</brain-context>

<read>{architecture_dir}/ADR-NNNN-feature-name.md (Step N), {product_specs_dir}/FEATURE.md, [relevant source files], .claude/references/retro-lessons.md</read>

<constraints>
- Write concrete test assertions, not descriptions
- Assert DOMAIN-CORRECT behavior, not current code behavior
- For each utility/helper: reason about what the function name MEANS semantically
- If existing code contradicts domain intent, write the test for correct behavior -- Colby will fix the code
- Flag any ambiguous domain intent for Eva
</constraints>

<output>Test files in {test_dir}/ matching ADR step scope, with DoR/DoD sections</output>

</template>

<template id="roz-code-qa">

### Roz Code QA (First Pass, After Colby Build)

<task>Full QA on ADR-NNNN implementation</task>

<brain-context>
<thought type="pattern" agent="roz" phase="qa" relevance="0.80">Prior findings on similar code patterns and known fragile areas</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this area</thought>
</brain-context>

<read>{architecture_dir}/ADR-NNNN-feature-name.md, {product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md, .claude/references/retro-lessons.md</read>

<constraints>
- Run all QA checks in order (per your persona file)
- REQUIREMENTS TO VERIFY: [Eva pastes enumerated requirements from spec/ADR here]
- Verify Colby's DoD coverage claims against actual code
- Grep for TODO/FIXME/HACK/XXX in all changed files -- non-test code match = BLOCKER
</constraints>

<output>QA Report with verdict, check table, requirements verification, issues found</output>

</template>

<template id="roz-scoped-rerun">

### Roz Scoped Re-Run (After Colby Fix)

<task>Scoped QA re-run on ADR-NNNN fix</task>

<read>{architecture_dir}/ADR-NNNN-feature-name.md, .claude/references/retro-lessons.md</read>

<constraints>
- Failed checks from first pass: [list specific failed checks]
- Inherited issues from previous reports: [list items and original report dates]
- SCOPED RE-RUN -- only re-check failed items + tests + post-fix verification
- Do not re-run dependency audit, exploratory, CI/CD checks
- Re-verify any requirements flagged as BLOCKER in first pass
</constraints>

<output>Scoped QA Report with re-run header, updated requirements verification</output>

</template>

<template id="ellis-commit">

### Ellis (Commit)

<task>Commit ADR-NNNN ([feature name]) -- QA passed</task>

<brain-context>
<thought type="decision" agent="colby" phase="build" relevance="0.75">Key implementation decisions for commit context</thought>
</brain-context>

<read>{architecture_dir}/ADR-NNNN-feature-name.md, .claude/references/retro-lessons.md</read>

<constraints>
- Analyze the full diff, not just the last commit
- Narrative commit body, not bullet points (what + why, skip how)
- Include Changelog trailer for user-facing changes
- Do not push without user approval
</constraints>

<output>Proposed commit message, then commit + push after confirmation</output>

</template>

<template id="agatha-writing">

### Agatha (Writing Mode)

<task>Write documentation for [feature name]</task>

<brain-context>
<thought type="pattern" agent="agatha" phase="build" relevance="0.80">Prior doc update reasoning and doc-drift patterns</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this area</thought>
</brain-context>

<read>{product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md, {architecture_dir}/ADR-NNNN-feature-name.md, {product_specs_dir}/FEATURE-doc-plan.md, .claude/references/retro-lessons.md</read>

<constraints>
- Follow doc plan
- Read actual code for accuracy -- specs describe intent, code describes reality
- Match existing doc structure and voice. One audience per document.
- Flag spec-vs-code divergences
</constraints>

<output>Documentation files per doc plan with DoR/DoD sections, list of files written/updated</output>

</template>

<template id="robert-acceptance">

### Robert (Acceptance Review)

<task>Review ADR-NNNN implementation against product spec</task>

<brain-context>
<thought type="decision" agent="robert" phase="review" relevance="0.80">Prior acceptance review patterns and decisions</thought>
</brain-context>

<read>{product_specs_dir}/FEATURE.md, [implementation file paths], .claude/references/retro-lessons.md</read>

<constraints>
- Verify every acceptance criterion from the spec against the actual code
- Each criterion gets a verdict: PASS / DRIFT / MISSING / AMBIGUOUS
- No blanket approvals -- each criterion has file:line evidence
- DRIFT findings include both spec reference and code reference
- AMBIGUOUS findings halt pipeline (human decides)
</constraints>

<output>Acceptance review with per-criterion verdicts, evidence table, overall verdict</output>

</template>

<template id="sable-acceptance">

### Sable (UX Acceptance Review)

<task>Review ADR-NNNN implementation against UX design doc</task>

<brain-context>
<thought type="decision" agent="sable" phase="review" relevance="0.80">Prior UX review patterns and decisions</thought>
</brain-context>

<read>{ux_docs_dir}/FEATURE-ux.md, [implementation file paths], .claude/references/retro-lessons.md</read>

<constraints>
- Verify every screen, state, interaction, a11y requirement, and copy item
- Five-state audit for every screen (empty, loading, populated, error, overflow)
- Accessibility audit (keyboard, ARIA, contrast, focus, screen reader)
- Each item gets a verdict: PASS / DRIFT / MISSING / AMBIGUOUS
- AMBIGUOUS findings halt pipeline (human decides)
</constraints>

<output>UX acceptance review with per-item verdicts, five-state audit, accessibility audit, overall verdict</output>

</template>

<template id="poirot-blind">

### Poirot (Blind Review)

<task>Blind review of Colby's build output for ADR-NNNN Step N</task>

<constraints>
- You receive ONLY the diff. No spec, no ADR, no context. This is by design.
- Minimum 5 findings required. Zero findings = HALT and re-analyze.
- Check: logic, security, error handling, naming, dead code, type safety, resource management, concurrency
- Grep codebase to verify patterns found in diff (but do not read spec/ADR/UX docs)
- Structured findings table only -- no prose paragraphs
</constraints>

<output>Findings table (location, severity, category, description, suggested fix) with DoR/DoD sections</output>

</template>

<template id="distillator-compress">

### Distillator (Compress Between Phases)

When artifacts exceed ~5K tokens, Eva invokes the Distillator to compress
them for downstream consumption.

<task>Compress spec + UX doc for downstream consumption by Cal</task>

<read>{product_specs_dir}/FEATURE.md, {ux_docs_dir}/FEATURE-ux.md</read>

<constraints>
- Lossless compression -- every decision, constraint, rejected alternative, open question, scope boundary survives
- Strip: prose transitions, hedging, self-reference, filler, decorative formatting
- Preserve: numbers/dates/versions, named entities, decisions + rationale, dependencies, risks
- Dense bullets under ## headings. YAML frontmatter with compression_ratio.
- downstream_consumer: "Cal architecture"
</constraints>

<output>Compressed distillate with YAML frontmatter, DoR/DoD sections, preservation checklist</output>

</template>

<template id="distillator-validate">

### Distillator (With Round-Trip Validation)

<task>Compress ADR for downstream consumption by Colby -- with validation</task>

<read>{architecture_dir}/ADR-NNNN-feature-name.md</read>

<constraints>
- Same lossless rules as above
- Produce TWO outputs: distillate + reconstruction attempt
- downstream_consumer: "Colby implementation"
</constraints>

<output>Distillate + reconstruction, YAML frontmatter, DoR/DoD sections, preservation checklist</output>

</template>
