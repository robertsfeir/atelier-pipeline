# Invocation Templates

<!-- CONFIGURE: Update the placeholders below to match your project -->
<!--
  docs/product   = directory for product specs (default: docs/product/)
  docs/ux         = directory for UX design docs (default: docs/ux/)
  docs/architecture    = directory for ADR files (default: docs/architecture/)
  source/        = feature directory pattern (e.g., src/features/, app/domains/)
  tests/            = test directory pattern (e.g., tests/, __tests__/, spec/)
  echo "no single test configured"   = command for rapid inner-loop tests (e.g., npm run test:fast)
  pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs        = command to run full test suite (e.g., npx vitest run, npm test)
-->

<!-- Telemetry timing protocol: Eva records wall-clock start_time before every
     Agent tool invocation and end_time after return. duration_ms = end_time -
     start_time. This is mechanical -- not a per-template change, but documented
     here as the telemetry timing source for Tier 1 duration_ms. Eva does not add
     timing instructions to individual templates. -->

<!-- Brain-context tag: Eva prefetches brain context via agent_search and injects
     results into the <brain-context> tag in invocations. This is for READ context
     only -- it gives agents prior decisions, patterns, and lessons relevant to
     their task. Agents with mcpServers: atelier-brain (Cal, Colby, Roz, Agatha)
     also capture independently via agent_capture per their Brain Access protocol.
     The brain-context tag is for reads; agent captures are separate writes that
     happen within the agent's own workflow. -->

Eva loads this file just-in-time when constructing sub-agent invocation
prompts. These are not pre-loaded into Eva's always-on context.

---

## Template Index

Eva: read this index to find the template line number, then read only that
template section using offset/limit. Do not read the entire file.

| # | Template ID | Agent | Purpose | Line |
|---|-------------|-------|---------| -----|
| 1 | cal-adr | Cal | ADR production (standard) | 60 |
| 2 | cal-adr-large | Cal | ADR production with research brief (large) | 92 |
| 3 | colby-mockup | Colby | UI mockup with mock data (before Cal) | 130 |
| 4 | colby-build | Colby | Implementation build unit | 156 |
| 5 | roz-investigation | Roz | Bug investigation (user-reported) | 186 |
| 6 | roz-test-spec-review | Roz | Test spec review (after Cal ADR) | 213 |
| 7 | roz-test-authoring | Roz | Test authoring per wave (pre-build) | 238 |
| 8 | roz-code-qa | Roz | Wave QA (after all units in wave built) | 264 |
| 9 | roz-scoped-rerun | Roz | Scoped re-run (after Colby fix) | 290 |
| 10 | ellis-commit | Ellis | Wave commit | 310 |
| 11 | agatha-writing | Agatha | Documentation writing | 334 |
| 12 | robert-acceptance | Robert | Product acceptance review | 358 |
| 13 | sable-acceptance | Sable | UX acceptance review | 382 |
| 14 | poirot-blind | Poirot | Blind wave diff review | 406 |
| 15 | sentinel-audit | Sentinel | Security audit (Semgrep-backed) | 424 |
| 16 | deps-scan | Deps | Full dependency scan | 449 |
| 17 | deps-migration-brief | Deps | Migration ADR brief | 473 |
| 18 | distillator-compress | Distillator | Lossless document compression | 502 |
| 19 | distillator-validate | Distillator | Compression with round-trip validation | 525 |
| 20 | agent-teams-task | Colby | Agent Teams teammate task (experimental) | 543 |
| 21 | roz-ci-investigation | Roz | CI Watch failure diagnosis | 602 |
| 22 | colby-ci-fix | Colby | CI Watch apply fix | 641 |
| 23 | roz-ci-verify | Roz | CI Watch post-fix verification | 679 |
| 24 | darwin-analysis | Darwin | Pipeline telemetry analysis | 714 |
| 25 | darwin-edit-proposal | Darwin | Structural improvement proposal | 746 |

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

<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, docs/product/FEATURE-doc-plan.md, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<warn>[Specific pattern if recurred 3x in error-patterns.md, otherwise omit this tag]</warn>

<constraints>
- Map blast radius (every file, module, integration, CI/CD impact)
- Minimum two alternatives with concrete tradeoffs
- Comprehensive test spec: failure tests >= happy path tests
</constraints>

<output>ADR saved to docs/architecture/ADR-NNNN-feature-name.md with DoR/DoD sections</output>

</template>

<template id="cal-adr-large">

### Cal (Large ADR Production -- With Research Brief)

For large pipelines, Eva provides a research brief with pre-gathered context.

<task>Produce ADR for [feature name]</task>

<brain-context>
<thought type="decision" agent="cal" phase="design" relevance="0.85">Prior architectural decisions from agent_search("architecture:{feature}")</thought>
<thought type="rejection" agent="cal" phase="design" relevance="0.80">Rejected approaches from agent_search("rejection:{feature}")</thought>
<thought type="pattern" agent="colby" phase="build" relevance="0.75">Proven patterns from agent_search("pattern:Bash shell scripts, Node.js (brain MCP server), PostgreSQL with pgvector/ltree")</thought>
</brain-context>

<context>[User preferences from context-brief.md]

Research Brief (Large pipeline):
- Existing patterns: [grep results -- file paths + pattern descriptions]
- Dependencies: [relevant libraries from package.json/requirements.txt with versions]
- Brain-surfaced decisions: [prior architectural decisions]
- Brain-surfaced rejections: [rejected approaches]
- Brain-surfaced patterns: [proven patterns]</context>

<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, docs/product/FEATURE-doc-plan.md, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<warn>[Specific pattern if recurred 3x in error-patterns.md, otherwise omit this tag]</warn>

<constraints>
- Map blast radius (every file, module, integration, CI/CD impact)
- Minimum two alternatives with concrete tradeoffs
- Comprehensive test spec: failure tests >= happy path tests
- Reference research brief findings in Alternatives Considered section
</constraints>

<output>ADR saved to docs/architecture/ADR-NNNN-feature-name.md with DoR/DoD sections</output>

</template>

<template id="colby-mockup">

### Colby Mockup (After Sable, Before Cal)

<task>Build mockup for [feature name]</task>

<brain-context>
<thought type="pattern" agent="colby" phase="build" relevance="0.80">Implementation patterns and known gotchas for this feature area</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this feature area</thought>
</brain-context>

<context>[User preferences from context-brief.md]</context>

<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<constraints>
- Real components in source//feature-name/ using existing component library
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

<context>Roz's test files define correct behavior. Make them pass. Do not modify Roz's assertions.
[When this step consumes a contract from a prior step, Eva includes the prior
step's Contracts Produced table here so Colby has the exact response shapes.]</context>

<read>docs/architecture/ADR-NNNN-feature-name.md (Step N + Contract Boundaries table), [Roz-authored test files], .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<constraints>
- Make Roz's pre-written tests pass -- do not modify her assertions
- Inner loop: `echo "no single test configured"` for rapid iteration. Full suite at unit completion.
- If a Roz test fails against existing code, the code has a bug -- fix it
- When fixing a shared utility bug, grep for all instances codebase-wide
- Zero TODO/FIXME/HACK in delivered code
- Read your assigned step of the ADR in full, plus the Contract Boundaries table for steps that consume your outputs. Do not read the full ADR — prior steps are done, future step implementations are not your concern.
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

<read>[relevant feature and API files], .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

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

<read>docs/architecture/ADR-NNNN-feature-name.md, docs/product/FEATURE.md, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md, .claude/references/qa-checks.md</read>

<constraints>
- Check failure:happy ratio (failure >= happy, hard rule)
- Check description quality (specific enough to write test without source)
- Verify Cal's DoR covers all spec requirements -- flag any silent drops
- Independently identify cases Cal missed
- Sizing check: for each ADR step, count the number of distinct test categories required. If a single step requires tests across 4+ categories (e.g., happy + failure + boundary + security + concurrency), flag it: "Step N may be over-packed — {N} test categories across {M} files suggests multiple behaviors. Consider sub-slicing."
</constraints>

<output>Category coverage table, gaps found, missing tests, Cal DoR verification, verdict (APPROVED / REVISE)</output>

</template>

<template id="roz-test-authoring">

### Roz Test Authoring (Pre-Build, Per Wave)

<task>Write test assertions for ADR-NNNN Wave W -- Steps [N, M, ...] -- [wave description]</task>

<brain-context>
<thought type="pattern" agent="roz" phase="qa" relevance="0.80">Test strategies that worked/failed on similar code</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this area</thought>
</brain-context>

<read>docs/architecture/ADR-NNNN-feature-name.md (Steps N, M, ...), docs/product/FEATURE.md, [relevant source files for each step in the wave], .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<constraints>
- Write concrete test assertions, not descriptions
- Assert DOMAIN-CORRECT behavior, not current code behavior
- For each utility/helper: reason about what the function name MEANS semantically
- If existing code contradicts domain intent, write the test for correct behavior -- Colby will fix the code
- Flag any ambiguous domain intent for Eva
- Write tests for ALL steps in this wave. Organize test files per step.
</constraints>

<output>Test files in tests// organized per step and covering all steps in this wave, with DoR/DoD sections</output>

</template>

<template id="roz-code-qa">

### Roz Code QA (Wave-Level, After All Units Built)

<task>Full QA on ADR-NNNN Wave W -- Steps [N, M, ...] implementation</task>

<brain-context>
<thought type="pattern" agent="roz" phase="qa" relevance="0.80">Prior findings on similar code patterns and known fragile areas</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this area</thought>
</brain-context>

<read>docs/architecture/ADR-NNNN-feature-name.md, docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md, .claude/references/qa-checks.md</read>

<constraints>
- Run all QA checks in order (per your persona file)
- REQUIREMENTS TO VERIFY: [Eva pastes enumerated requirements from spec/ADR here]
- Verify Colby's DoD coverage claims against actual code
- Grep for TODO/FIXME/HACK/XXX in all changed files -- non-test code match = BLOCKER
- Review ALL units in this wave. Report findings per unit.
- Run full test suite: pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs
</constraints>

<output>QA Report with verdict, check table, requirements verification per unit, issues found</output>

</template>

<template id="roz-scoped-rerun">

### Roz Scoped Re-Run (After Colby Fix)

<task>Scoped QA re-run on ADR-NNNN fix</task>

<read>docs/architecture/ADR-NNNN-feature-name.md, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md, .claude/references/qa-checks.md</read>

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

### Ellis (Wave Commit)

<task>Commit ADR-NNNN Wave W ([feature name]) -- wave QA passed</task>

<brain-context>
<thought type="decision" agent="colby" phase="build" relevance="0.75">Key implementation decisions for commit context</thought>
</brain-context>

<read>docs/architecture/ADR-NNNN-feature-name.md, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<constraints>
- Analyze the full diff, not just the last commit
- Narrative commit body, not bullet points (what + why, skip how)
- Include Changelog trailer for user-facing changes
- Final commit: present message to Eva for user approval before committing. Per-wave commit: commit without approval.
- This is a wave commit covering steps [N, M, ...]. List all units in the commit body.
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

<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, docs/architecture/ADR-NNNN-feature-name.md, docs/product/FEATURE-doc-plan.md, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

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

<read>docs/product/FEATURE.md, [implementation file paths], .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

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

<read>docs/ux/FEATURE-ux.md, [implementation file paths], .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

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

### Poirot (Blind Review, Wave-Level)

<task>Blind review of Wave W cumulative diff for ADR-NNNN</task>

<constraints>
- You receive ONLY the diff. No spec, no ADR, no context. This is by design.
- Minimum 5 findings required. Zero findings = HALT and re-analyze.
- Check: logic, security, error handling, naming, dead code, type safety, resource management, concurrency
- Grep codebase to verify patterns found in diff (but do not read spec/ADR/UX docs)
- Structured findings table only -- no prose paragraphs
</constraints>

<output>Findings table (location, severity, category, description, suggested fix) with DoR/DoD sections</output>

</template>

<template id="sentinel-audit">

### Sentinel (Security Audit)

Eva invokes Sentinel at the review juncture and after each Colby build unit
(when `sentinel_enabled: true` in `pipeline-config.json`).

<task>Security audit of Colby's build output for ADR-NNNN Step N</task>

(Or for the final review juncture: "Security audit -- full review juncture for ADR-NNNN")

<constraints>
- You receive ONLY the diff and Semgrep scan results. No spec, no ADR, no UX doc, no context. This is by design.
- Run `semgrep_scan` on changed files. Call `semgrep_findings` for structured results.
- Cross-reference all findings against the diff -- only report findings in added or modified code.
- Minimum 3 findings or explicit "clean scan" report with evidence (files scanned, rules matched, scan duration).
- Include CWE/OWASP references for every BLOCKER and MUST-FIX finding.
- If Semgrep scan hangs or times out, STOP. Report partial results. Do not retry.
- Grep codebase to verify whether flagged patterns exist in other files (scope check).
</constraints>

<output>Security report with findings table (location, severity, category, CWE/OWASP, description, remediation), scan metadata, DoR/DoD sections</output>

</template>

<template id="deps-scan">

### Deps (Full Dependency Scan)

Eva invokes Deps when the user types `/deps` or when dependency-related intent
is detected (when `deps_agent_enabled: true` in `pipeline-config.json`).

<task>Scan dependency manifests, check CVEs, predict breakage risk, and produce a risk-grouped report.</task>

<constraints>
- Detect which ecosystems are present (package.json, requirements.txt, Cargo.toml, go.mod). Skip missing ecosystems -- report them as absent rather than erroring.
- Run outdated checks and CVE audit per ecosystem. Skip any ecosystem whose tool is absent -- report the gap.
- Fetch changelogs for packages with major version bumps via WebFetch/WebSearch. If unavailable, note in report and skip changelog analysis.
- Grep codebase for usage of APIs listed as breaking changes in changelogs.
- Use conservative risk labels: prefer "Needs review" over "Safe" when uncertain.
- If a Bash command hangs or times out, STOP. Do not retry. Report partial results.
- Never modify files. This is analysis only.
- Monorepo: scan all manifests found. Group report by directory.
</constraints>

<output>Risk-grouped dependency report: CVE Alerts | Needs Review | Safe to Upgrade | No Action Needed. Each entry: package name, current version, target version, CVE IDs, breaking API usage found (file:line), risk label, recommendation. DoR (ecosystems detected, tools available) and DoD sections.</output>

</template>

<template id="deps-migration-brief">

### Deps (Migration ADR Brief)

Eva invokes Deps when the user requests a migration ADR for a specific package.
Eva then routes the brief to Cal for ADR production.

<task>Produce a migration ADR brief for upgrading [package] from [current] to [target].</task>

<constraints>
- Scope this invocation to the named package only.
- Fetch the full changelog/release notes for the version range.
- Grep the entire codebase for every usage of APIs that are removed or changed.
- Produce a structured brief: affected APIs, usage locations (file:line), suggested migration approach per API, estimated effort (low/medium/high).
- This brief is the input to Cal's ADR production -- it must be precise and complete.
- Never modify files.
</constraints>

<output>Migration ADR brief: package + version range, breaking changes table, usage inventory (file:line per API), migration approach, estimated effort, open questions for Cal. DoR and DoD sections.</output>

</template>

<!-- Distillator scope: Eva invokes Distillator only for cross-phase artifact
     compression (spec, UX doc, ADR exceeding ~5K tokens at a phase boundary).
     Within-session tool outputs (file reads, grep results, bash outputs) are
     handled by observation masking -- see pipeline-operations.md
     <protocol id="observation-masking">. Do not invoke Distillator for
     routine within-session context cleanup. -->

<template id="distillator-compress">

### Distillator (Compress Between Phases)

When cross-phase artifacts exceed ~5K tokens, Eva invokes the Distillator to
compress them for downstream consumption at a phase boundary.

<task>Compress spec + UX doc for downstream consumption by Cal</task>

<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md</read>

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

<read>docs/architecture/ADR-NNNN-feature-name.md</read>

<constraints>
- Same lossless rules as above
- Produce TWO outputs: distillate + reconstruction attempt
- downstream_consumer: "Colby implementation"
</constraints>

<output>Distillate + reconstruction, YAML frontmatter, DoR/DoD sections, preservation checklist</output>

</template>

<template id="agent-teams-task">

### Agent Teams Teammate Task (Experimental)

Eva uses this format when creating tasks for Colby Teammates during Agent
Teams wave execution (when `agent_teams_available: true`). This is the
task description written to TaskCreate -- not an Agent tool invocation
prompt. Teammates load Colby's persona from `.claude/agents/colby.md`
and project rules from `.claude/rules/` automatically via their worktree.

**Task description format (Eva writes this to TaskCreate):**

```
ADR: ADR-NNNN Step N -- [step description]
Wave: N of M, Unit: K of L
maxTurns: 25

Files to create:
- [path/to/new-file.ext]

Files to modify:
- [path/to/existing-file.ext]

Test files:
- [path/to/test-file.ext]

Acceptance criteria (from ADR step):
- [criterion 1]
- [criterion 2]
- [criterion N]

Constraints:
- Run lint after implementation: echo "no linter configured"
- Do NOT run the full test suite -- Eva runs it after merge
- Do NOT commit -- Eva merges and routes to Ellis
- Do NOT modify files outside your assigned scope above
- If a file that should exist does not exist (missing dependency from
  another step), mark this task as blocked with a description of
  what is missing rather than attempting to work around it
- Make Roz's pre-written tests pass -- do not modify her assertions
- Zero TODO/FIXME/HACK in delivered code
```

**Notes for Eva:**

- One task per wave unit. Tasks are created for all units in the wave
  before any Teammate begins execution.
- `maxTurns: 25` is the default. Adjust per unit complexity if needed.
  This is the only hard limit on runaway Teammate iterations (retro #004).
- Eva processes `TaskCompleted` events sequentially -- one at a time --
  to avoid race conditions in `pipeline-state.md` updates (retro #003).
- After all Teammates in the wave complete, Eva merges worktrees in task
  creation order (deterministic merge sequence).
- If a Teammate marks its task blocked: Eva falls back to sequential
  execution for that unit, resolves the missing dependency, then
  re-invokes Colby as a standard subagent.

</template>

<template id="roz-ci-investigation">

### Roz CI Investigation (CI Watch -- Failure Diagnosis)

Eva invokes Roz when CI Watch detects a CI failure and pulls the failure logs.
CI failure logs are passed in CONTEXT (ephemeral, not file-backed).

<task>Investigate CI failure -- [one-line summary of failing step/job from logs]</task>

<brain-context>
<thought type="pattern" agent="roz" phase="qa" relevance="0.85">Prior CI failure patterns and their root causes on this repo</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to CI failures in this area</thought>
</brain-context>

<context>
CI failure logs (truncated to 200 lines per job):

[Eva pastes truncated failure log content here -- not a file reference]

Branch: [branch name]
Commit SHA: [sha]
Platform: [gh | glab]
CI retry count: [N] of [max]
</context>

<read>[source files implicated by the failure logs -- max 4], .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<constraints>
- Diagnose from the CI logs + source code -- this is a CI failure, not a user-reported bug
- Identify root cause with file:line precision
- Do NOT write code -- diagnosis only
- Note whether this appears to be an environment issue (flaky test, missing secret, infra) vs. code defect
- If root cause is ambiguous, list the top 2 hypotheses with evidence for each
</constraints>

<output>CI failure diagnosis with: root cause (file:line or environment cause), affected code path, fix description, confidence level (HIGH/MEDIUM/LOW), recommended fix approach</output>

</template>

<template id="colby-ci-fix">

### Colby CI Fix (CI Watch -- Apply Fix)

Eva invokes Colby to fix a CI failure after Roz has diagnosed it.

<task>Fix CI failure -- [Roz's one-line root cause summary]</task>

<brain-context>
<thought type="pattern" agent="colby" phase="build" relevance="0.80">Implementation patterns relevant to the failing code area</thought>
<thought type="lesson" agent="eva" phase="retro" relevance="0.70">Retro lessons relevant to this fix area</thought>
</brain-context>

<context>
Roz's CI failure diagnosis:
[Eva pastes Roz's full diagnosis output here]

Original CI failure logs:
[Eva pastes truncated failure log content here]

Branch: [branch name]
Commit SHA that failed: [sha]
</context>

<read>[files identified by Roz's diagnosis -- max 5], .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<constraints>
- Fix the specific CI failure identified by Roz -- do not expand scope
- Run lint after implementing: echo "no linter configured"
- Do NOT modify Roz's test assertions
- Do NOT push -- Eva will invoke Ellis after Roz verifies
- Zero TODO/FIXME/HACK in delivered code
</constraints>

<output>Fix report with: files changed (list), root cause addressed, what changed and why, confidence that fix resolves the CI failure</output>

</template>

<template id="roz-ci-verify">

### Roz CI Verify (CI Watch -- Post-Fix Verification)

Eva invokes Roz to verify Colby's CI fix before presenting to the user for approval.

<task>Verify CI fix -- [Colby's one-line fix summary]</task>

<brain-context>
<thought type="pattern" agent="roz" phase="qa" relevance="0.80">Prior verification patterns on similar CI fix cycles</thought>
</brain-context>

<context>
Colby's fix report:
[Eva pastes Colby's full fix report here]

Original Roz diagnosis:
[Eva pastes Roz's diagnosis summary here]

Original CI failure: [one-line summary]
</context>

<read>[files Colby modified], .claude/references/retro-lessons.md, .claude/references/agent-preamble.md, .claude/references/qa-checks.md</read>

<constraints>
- Run the test suite locally to verify the fix: echo "no test suite configured"
- Verify the fix addresses the root cause Roz identified -- not just makes tests pass locally
- Check for regressions in related code paths
- SCOPED RE-RUN -- focus on the CI failure area + adjacent code, not full QA
</constraints>

<output>QA verdict: PASS or FAIL. If PASS: confirm root cause is addressed, no regressions found. If FAIL: list remaining issues with file:line evidence. One-line verdict summary for Eva's hard pause presentation to user.</output>

</template>

<template id="darwin-analysis">

### Darwin (Pipeline Analysis)

Eva invokes Darwin when the user types `/darwin` or when a degradation alert
fires at pipeline end (when `darwin_enabled: true` in `pipeline-config.json`).
Requires brain and 5+ pipelines of Tier 3 telemetry data.

<task>Analyze pipeline telemetry and propose structural improvements.</task>

<brain-context>
[Eva injects Tier 3 telemetry summaries from last N pipelines via agent_search.
Also injects prior Darwin proposals and their outcomes if any exist.]
</brain-context>

<read>docs/pipeline/error-patterns.md, .claude/references/retro-lessons.md,
.claude/references/telemetry-metrics.md, .claude/references/agent-preamble.md,
[agent persona files for agents flagged by telemetry]</read>

<constraints>
- Compute per-agent fitness: thriving/struggling/failing per fitness scoring table
- For each struggling/failing agent: identify pattern, select fix layer, apply escalation ladder
- Every proposal must include: evidence, layer, escalation level, risk, expected impact
- Cannot propose changes to your own persona file (darwin.md) -- self-edit protection
- Level 5 proposals require summary of all prior escalation attempts
- Conservative: when uncertain, propose the lower escalation level
</constraints>

<output>Darwin Report with FITNESS ASSESSMENT + PROPOSED CHANGES + UNCHANGED sections. DoR/DoD.</output>

</template>

<template id="darwin-edit-proposal">

### Darwin Edit Proposal (Colby Implementation)

Eva routes an approved Darwin proposal to Colby for implementation.
One proposal per Colby invocation.

<task>Implement Darwin proposal #{id}: {one-line description}</task>

<context>
Darwin proposal:
  Target file: {file_path}
  Target section: {section identifier}
  Change type: {constraint addition | workflow edit | enforcement addition | ...}
  Escalation level: {1-5}
  Evidence: {metric values, pattern references}
  Expected impact: {metric + expected delta}

Current content of target section:
[Eva pastes the current content of the section being modified]
</context>

<read>{target_file}, .claude/references/retro-lessons.md, .claude/references/agent-preamble.md</read>

<constraints>
- Make exactly the change described in the proposal -- no scope expansion
- Dual tree: if modifying source/{path}, also modify .claude/{path}
- Preserve existing content structure (XML tags, heading levels, list formatting)
- Do not modify Darwin's own persona file (darwin.md) even if the proposal somehow references it
</constraints>

<output>Files changed, diff summary, DoR/DoD sections</output>

</template>

<template id="dashboard-bridge">

### Dashboard Bridge (Eva self-invocation via Bash)

Eva runs this after Ellis commit when `dashboard_mode: "plan-visualizer"`.
Not a subagent invocation -- Eva runs the bridge script directly via Bash.

<task>Run the telemetry bridge script to regenerate PIPELINE_PLAN.md for PlanVisualizer.</task>

<constraints>
- Run `.claude/dashboard/telemetry-bridge.sh` via Bash.
- If the script fails, log the error and continue. Never block the pipeline.
- This is a Bash command, not a subagent invocation.
</constraints>

<output>PIPELINE_PLAN.md written to project root. Dashboard HTML regenerated (if node available).</output>

</template>
