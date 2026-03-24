# Invocation Templates

<!-- CONFIGURE: Update the placeholders below to match your project -->
<!--
  docs/product   = directory for product specs (default: docs/product/)
  docs/ux         = directory for UX design docs (default: docs/ux/)
  docs/architecture    = directory for ADR files (default: docs/architecture/)
  source/        = feature directory pattern (e.g., src/features/, app/domains/)
  tests/            = test directory pattern (e.g., tests/, __tests__/, spec/)
  echo "no fast tests configured"   = command for rapid inner-loop tests (e.g., npm run test:fast)
  echo "no test suite configured"        = command to run full test suite (e.g., npx vitest run, npm test)
-->

Eva loads this file just-in-time when constructing sub-agent invocation
prompts. These are not pre-loaded into Eva's always-on context.

---

**Cal (ADR production -- after conversational clarification):**
> TASK: Produce ADR for [feature name]
> READ: docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, docs/product/FEATURE-doc-plan.md, .claude/references/retro-lessons.md
> CONTEXT: [User preferences and decisions from context-brief.md]
> BRAIN: [If brain available: prior architectural decisions, rejected approaches, technical constraints, handoff briefs, AND retro lessons relevant to this feature area from agent_search. Omit section if brain unavailable.]
> WARN: [Specific pattern if recurred 3x in error-patterns.md, otherwise omit]
> CONSTRAINTS:
> - Map blast radius (every file, module, integration, CI/CD impact)
> - Minimum two alternatives with concrete tradeoffs
> - Comprehensive test spec: failure tests >= happy path tests
> OUTPUT: ADR saved to docs/architecture/ADR-NNNN-feature-name.md with DoR/DoD sections

**Cal (Large ADR production -- with research brief):**
> TASK: Produce ADR for [feature name]
> READ: docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, docs/product/FEATURE-doc-plan.md, .claude/references/retro-lessons.md
> CONTEXT: [User preferences from context-brief.md]
> Research Brief (Large pipeline):
> - Existing patterns: [grep results -- file paths + pattern descriptions]
> - Dependencies: [relevant libraries from package.json/requirements.txt with versions]
> - Brain-surfaced decisions: [prior architectural decisions from agent_search("architecture:{feature}")]
> - Brain-surfaced rejections: [rejected approaches from agent_search("rejection:{feature}")]
> - Brain-surfaced patterns: [proven patterns from agent_search("pattern:{tech_stack}")]
> BRAIN: [Same as standard Cal invocation]
> WARN: [Specific pattern if recurred 3x in error-patterns.md, otherwise omit]
> CONSTRAINTS:
> - Map blast radius (every file, module, integration, CI/CD impact)
> - Minimum two alternatives with concrete tradeoffs
> - Comprehensive test spec: failure tests >= happy path tests
> - Reference research brief findings in Alternatives Considered section
> OUTPUT: ADR saved to docs/architecture/ADR-NNNN-feature-name.md with DoR/DoD sections

**Colby (mockup mode -- after Sable, before Cal):**
> TASK: Build mockup for [feature name]
> READ: docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, .claude/references/retro-lessons.md
> CONTEXT: [User preferences from context-brief.md]
> BRAIN: [If brain available: implementation patterns, known gotchas, handoff briefs, AND retro lessons relevant to this feature area from agent_search. Omit if unavailable.]
> CONSTRAINTS:
> - Real components in source//feature-name/ using existing component library
> - Wire to mock data hook, NOT API calls
> - Implement all states from Sable's doc (empty, loading, populated, error, overflow)
> - Add route and nav item. No backend, no tests.
> OUTPUT: Route path, list of files created, state switching instructions, with DoR/DoD sections

**Roz (bug investigation -- user reports a bug):**
> TASK: Investigate bug -- [observed symptom, not theory]
> HYPOTHESES: [Eva's theory] | [alternative at different layer]
> READ: [relevant feature and API files], .claude/references/retro-lessons.md
> BRAIN: [If brain available: recurring QA patterns, prior findings on similar code, handoff briefs, AND retro lessons relevant to this area from agent_search. Omit if unavailable.]
> CONSTRAINTS:
> - Trace the full request path: frontend call -> API route -> handler -> data access
> - Run relevant tests to confirm bug. Check API logs.
> - Identify root cause with file paths and line numbers
> - Check for related issues in the same area
> - Do NOT write code -- diagnosis only
> OUTPUT: Bug report with: symptom, root cause (file:line), affected code path, fix description, related issues

**Roz (test spec review -- after Cal, before Colby build):**
> TASK: Review test spec for ADR-NNNN
> READ: docs/architecture/ADR-NNNN-feature-name.md, docs/product/FEATURE.md, .claude/references/retro-lessons.md
> BRAIN: [If brain available: recurring QA patterns on this module, handoff briefs, AND retro lessons relevant to this area from agent_search. Omit if unavailable.]
> CONSTRAINTS:
> - Check failure:happy ratio (failure >= happy, hard rule)
> - Check description quality (specific enough to write test without source)
> - Verify Cal's DoR covers all spec requirements -- flag any silent drops
> - Independently identify cases Cal missed
> OUTPUT: Category coverage table, gaps found, missing tests, Cal DoR verification, verdict (APPROVED / REVISE)

**Roz (test authoring -- pre-build, per ADR step):**
> TASK: Write test assertions for ADR-NNNN Step N -- [step description]
> READ: docs/architecture/ADR-NNNN-feature-name.md (Step N), docs/product/FEATURE.md, [relevant source files], .claude/references/retro-lessons.md
> BRAIN: [If brain available: test strategies that worked/failed on similar code, handoff briefs, AND retro lessons relevant to this area from agent_search. Omit if unavailable.]
> CONSTRAINTS:
> - Write concrete test assertions, not descriptions
> - Assert DOMAIN-CORRECT behavior, not current code behavior
> - For each utility/helper: reason about what the function name MEANS semantically
> - If existing code contradicts domain intent, write the test for correct behavior -- Colby will fix the code
> - Flag any ambiguous domain intent for Eva
> OUTPUT: Test files in tests// matching ADR step scope, with DoR/DoD sections

**Colby (build mode -- unit N):**
> TASK: Implement ADR-NNNN Step N -- [description]
> READ: docs/architecture/ADR-NNNN-feature-name.md, [Roz-authored test files], .claude/references/retro-lessons.md
> CONTEXT: Roz's test files define correct behavior. Make them pass. Do not modify Roz's assertions.
> BRAIN: [If brain available: implementation patterns, known gotchas, prior build failures, handoff briefs, AND retro lessons relevant to this area from agent_search. Omit if unavailable.]
> CONSTRAINTS:
> - Make Roz's pre-written tests pass -- NEVER modify her assertions
> - **Inner loop:** `echo "no fast tests configured"` for rapid iteration. **Full suite** at unit completion.
> - If a Roz test fails against existing code, the code has a bug -- fix it
> - When fixing a shared utility bug, grep for all instances codebase-wide
> - Zero TODO/FIXME/HACK in delivered code
> OUTPUT: Step N complete report with DoR/DoD sections, Bugs Discovered section, files changed

**Poirot (blind review -- parallel with Roz QA, after Colby build):**
> TASK: Blind review of Colby's build output for ADR-NNNN Step N
> DIFF: [raw output of `git diff` for this unit -- Eva pastes the full diff here]
> CONSTRAINTS:
> - You receive ONLY the diff. No spec, no ADR, no context. This is by design.
> - Minimum 5 findings required. Zero findings = HALT and re-analyze.
> - Check: logic, security, error handling, naming, dead code, type safety, resource management, concurrency
> - Grep codebase to verify patterns found in diff (but do NOT read spec/ADR/UX docs)
> - Structured findings table only -- no prose paragraphs
> OUTPUT: Findings table (location, severity, category, description, suggested fix) with DoR/DoD sections

**Distillator (compress between phases -- when artifacts exceed ~5K tokens):**
> TASK: Compress spec + UX doc for downstream consumption by Cal
> READ: docs/product/FEATURE.md, docs/ux/FEATURE-ux.md
> CONSTRAINTS:
> - Lossless compression -- every decision, constraint, rejected alternative, open question, scope boundary must survive
> - Strip: prose transitions, hedging, self-reference, filler, decorative formatting
> - Preserve: numbers/dates/versions, named entities, decisions + rationale, dependencies, risks
> - Dense bullets under ## headings. YAML frontmatter with compression_ratio.
> - downstream_consumer: "Cal architecture"
> OUTPUT: Compressed distillate with YAML frontmatter, DoR/DoD sections, preservation checklist

**Distillator (with round-trip validation):**
> TASK: Compress ADR for downstream consumption by Colby -- with validation
> READ: docs/architecture/ADR-NNNN-feature-name.md
> VALIDATE: true
> CONSTRAINTS:
> - Same lossless rules as above
> - Produce TWO outputs: distillate + reconstruction attempt
> - downstream_consumer: "Colby implementation"
> OUTPUT: Distillate + reconstruction, YAML frontmatter, DoR/DoD sections, preservation checklist

**Roz (code QA -- first pass, after Colby build):**
> TASK: Full QA on ADR-NNNN implementation
> READ: docs/architecture/ADR-NNNN-feature-name.md, docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, .claude/references/retro-lessons.md
> BRAIN: [If brain available: prior findings on similar code patterns, known fragile areas, handoff briefs, AND retro lessons relevant to this area from agent_search. Omit if unavailable.]
> DIFF: [output of `git diff --stat` and `git diff --name-only` for unit N]
> CONSTRAINTS:
> - Run all QA checks in order (per your persona file)
> - REQUIREMENTS TO VERIFY: [Eva pastes enumerated requirements from spec/ADR here]
> - Verify Colby's DoD coverage claims against actual code
> - Grep for TODO/FIXME/HACK/XXX in all changed files -- non-test code match = BLOCKER
> OUTPUT: QA Report with verdict, check table, requirements verification, issues found

**Roz (scoped re-run -- after Colby fix):**
> TASK: Scoped QA re-run on ADR-NNNN fix
> READ: docs/architecture/ADR-NNNN-feature-name.md, .claude/references/retro-lessons.md
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
> READ: docs/architecture/ADR-NNNN-feature-name.md, .claude/references/retro-lessons.md
> CONSTRAINTS:
> - Analyze the full diff, not just the last commit
> - Narrative commit body, not bullet points (what + why, skip how)
> - Include Changelog trailer for user-facing changes
> - Do not push without user approval
> OUTPUT: Proposed commit message, then commit + push after confirmation

**Agatha (writing mode):**
> TASK: Write documentation for [feature name]
> READ: docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, docs/architecture/ADR-NNNN-feature-name.md, docs/product/FEATURE-doc-plan.md, .claude/references/retro-lessons.md
> BRAIN: [If brain available: prior doc update reasoning, doc-drift patterns, handoff briefs, AND retro lessons relevant to this area from agent_search. Omit if unavailable.]
> CONSTRAINTS:
> - Follow doc plan
> - Read actual code for accuracy -- specs describe intent, code describes reality
> - Match existing doc structure and voice. One audience per document.
> - Flag spec-vs-code divergences
> OUTPUT: Documentation files per doc plan with DoR/DoD sections, list of files written/updated
