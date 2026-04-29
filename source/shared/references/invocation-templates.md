# Invocation Templates

<!-- CONFIGURE: docs/product, docs/ux, docs/architecture, source/, tests/,
     echo "no single test configured" (single test), pytest tests/ (full suite) -->

## Shared Protocols (apply to all templates below)

**Brain-context injection:** Eva prefetches via `agent_search` and injects
into `<brain-context>`. Captures are gated mechanically by the three-hook
loop (ADR-0053): SubagentStop marks the pending capture for allowlisted
agents, PreToolUse on `Agent` blocks Eva's next invocation until she calls
`agent_capture` with curated content, PostToolUse on `agent_capture` clears
the marker. Omit `<brain-context>` when brain unavailable.

Example fully-formed `<brain-context>` block:
```xml
<brain-context>
  <thought type="decision" agent="sarah" phase="architecture"
           captured_by="robert@sfeir.design" created_at="2026-03-15T14:22:00Z" relevance="0.87">
    Use ltree scoping for all agent_search calls; unscoped queries leak cross-project content.
  </thought>
</brain-context>
```
Agents use `captured_by` and `created_at` to weigh credibility -- a recent
thought from the same agent in the same scope carries more weight than a
months-old thought from a different feature.

**Standard READ items (included in every invocation, not listed per template):**
`{config_dir}/references/retro-lessons.md`, `{config_dir}/references/agent-preamble.md`

**Persona constraints apply:** Templates list only task-specific constraints
that supplement the persona. Do not duplicate persona-level rules.

**Telemetry timing:** Eva records `start_time`/`end_time` around every Agent
tool invocation. `duration_ms = end_time - start_time`.

**SendMessage resume capture (Sarah and Poirot only):** When Eva invokes Sarah
(templates 1, 2) or Poirot (template 14) via the Agent tool, she captures the
`agentId` returned in the tool result and holds it in her session context
keyed by agent name. On a recognized continuation trigger (Sarah revision
after a Poirot structural finding, Poirot scoped re-run after a Colby fix),
Eva uses `SendMessage` against the captured `agentId` instead of spawning a
fresh Agent -- this skips the re-read cost on these two high-context agents.
**Address by UUID, not name.** The `to` value passed to `SendMessage` MUST be
the captured `agentId` UUID string (e.g. `"a0f21b3784edcb4d4"`) returned in
the Agent tool result -- not the agent name. Name-based addressing
(`"sarah"`, `"poirot"`) only resolves for currently-running teammates and
returns "not currently addressable" for stopped subagents, which is exactly
the resume target. UUID is the only valid `to` value for resume.
No other agent qualifies; capture is in-session only and is discarded at
session boundaries (compaction, restart, crash). Full rule:
`{config_dir}/rules/agent-system.md` (`<protocol id="sendmessage-resume">`).

---

## Template Index

| # | Template ID | Agent | Purpose |
|---|-------------|-------|---------|
| 1 | sarah-adr | Sarah | ADR production (standard) |
| 2 | sarah-adr-large | Sarah | ADR production with research brief (medium/large) |
| 2a | scout-research-brief | scout (x3) | Pre-Sarah research scouts (medium+large) |
| 2b | codebase-investigation | scout (xN) → synthesis | Ad-hoc codebase scan: partition by area, collect evidence, synthesize |
| 2c | scout-synthesis | synthesis | Post-scout filter/rank/trim before primary agent |
| 2d | brain-hydrate-scout | scout | Brain hydration file-content scout |
| 3 | colby-mockup | Colby | UI mockup with mock data |
| 4 | colby-build | Colby | Build unit; **CI Watch variant:** scope to CI fix |
| 10 | ellis-commit | Ellis | Wave commit |
| 11 | agatha-writing | Agatha | Documentation writing |
| 12 | robert-acceptance | Robert | Product acceptance review |
| 13 | sable-acceptance | Sable | UX acceptance review |
| 14 | poirot-blind | Poirot | Blind wave diff review |
| 15 | sentinel-audit | Sentinel | Security audit (Semgrep-backed) |
| 16 | deps-scan | Deps | Full dependency scan |
| 17 | deps-migration-brief | Deps | Migration ADR brief |
| 18 | distillator-compress | Distillator | Lossless document compression |
| 19 | distillator-validate | Distillator | Compression with round-trip validation |
| 20 | darwin-analysis | Darwin | Pipeline telemetry analysis |

Note: Agent Teams task format is in pipeline-operations.md (TaskCreate format, not Agent invocation).
Note: darwin-edit-proposal uses colby-build with Darwin proposal in CONTEXT.

---

<template id="sarah-adr">
### Sarah (ADR Production)
<task>Produce ADR for [feature name]</task>
<context>[User preferences from context-brief.md]</context>
<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, docs/product/FEATURE-doc-plan.md, [blast_radius_files from scout when available]</read>
<constraints>
- Map blast radius (every file, module, integration, CI/CD impact)
- Minimum two alternatives with concrete tradeoffs
- Comprehensive test spec: failure tests >= happy path tests
</constraints>
<output>ADR at docs/architecture/ADR-NNNN-feature-name.md with DoR/DoD</output>
</template>

<template id="sarah-adr-large">
### Sarah (Large ADR -- With Research Brief)
<task>Produce ADR for [feature name]</task>
<research-brief>
- Existing patterns: [from patterns scout, file:line]
- Dependencies: [from manifest scout, name + version]
- Blast-radius files: [from blast-radius scout, ≤15 paths]
- Brain context: [from agent_search]
</research-brief>
<context>[User preferences from context-brief.md]</context>
<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, docs/product/FEATURE-doc-plan.md</read>
<constraints>
- Map blast radius. Two alternatives with tradeoffs.
- Test spec: failure >= happy. Reference research brief in Alternatives.
</constraints>
<output>ADR at docs/architecture/ADR-NNNN-feature-name.md with DoR/DoD</output>
</template>

<template id="scout-research-brief">
### Scout Research Brief (scout, pre-Sarah, Medium+Large)
Three scouts launched in parallel by Eva. Each receives one focused prompt.

**Patterns scout:**
<task>Find existing code patterns relevant to [feature area]. Grep for similar feature directories, hooks, naming conventions, shared utilities.</task>
<constraints>- Return file:line results only. No opinions. Max 20 results.</constraints>
<output>patterns: [{file, line, pattern_description}]</output>

**Manifest scout:**
<task>Check dependency manifests (package.json, requirements.txt, go.mod, etc.) for packages relevant to [feature area].</task>
<constraints>- Return package names and versions only. Flag anything outdated or potentially conflicting.</constraints>
<output>deps: [{name, version, relevance}]</output>

**Blast-radius scout:**
<task>Identify source files likely in scope for [feature area]: files matching the feature name, adjacent modules, integration points, test files.</task>
<constraints>- Return file paths only. Max 15 files. Prefer specific over broad.</constraints>
<output>blast_radius_files: [path, ...]</output>

**Post-scout synthesis:** After all three scouts return, Eva invokes Template 2c (scout-synthesis) before invoking Sarah. Scout raw output is passed to the synthesis agent, not directly to Sarah. Synthesis produces the compact `<research-brief>` block consumed by Sarah.
</template>

<template id="codebase-investigation">
### Codebase Investigation (scout → synthesis)
Ad-hoc read-only surveys (security mapping, architecture reviews, dependency tracing). No ADR, no code changes. Eva fans out parallel area scouts — `Agent(subagent_type: "scout")`, one concern per scout, facts only, `findings: [{file, line, description}]`. Passes evidence to `Agent(subagent_type: "synthesis", effort: "low")` via named `<scout-evidence>` blocks. Synthesis produces structured findings table with file:line evidence. DoR/DoD.
</template>

<template id="scout-synthesis">
### Scout Synthesis (synthesis filter/rank/trim, post-scout, pre-primary-agent)
<task>Filter, rank, and trim scout outputs into the named block for the primary agent. Emit only the required field names per the output shape. No opinions, no design proposals.</task>
Eva invokes ONE synthesis agent after scouts complete. Synthesis reads all
scout outputs and produces the compact block consumed by Sarah/Colby/Poirot.
Does NOT form opinions. Filters, ranks, trims only.

**Invocation:** `Agent(subagent_type: "synthesis", effort: "low")` with the
synthesis output-shape prompt embedded inline. The `model` parameter is
omitted; resolution falls through to the synthesis frontmatter
(`claude-sonnet-4-6`) per ADR-0048.

Block populated: `<research-brief>` (Sarah) / `<colby-context>` (Colby) / `<qa-evidence>` (Poirot).

**Per-primary-agent output shape:**

Sarah synthesis fills `<research-brief>`:
- Top patterns (<=5 ranked by relevance): [file:line + one-line description]
- Confirmed blast-radius (<=10 files with reason): [list]
- Manifest notes: [conflicts or "none"]
- Brain context (top 3 thoughts): [excerpts; omit when brain unavailable]

Colby synthesis fills `<colby-context>`:
- Key functions/blocks in scope for this step (NOT full files -- extract only the
  functions/classes/blocks the step will touch): [list]
- Relevant patterns to replicate (<=5, file:line + one-line description): [list]
- Files pre-loaded (full content only if <=50 lines): [list]
- Brain context (top 2 patterns for this step): [excerpts; omit when brain unavailable]

Poirot synthesis fills `<qa-evidence>`:
- Changed sections (per file: ONLY the changed functions/blocks, NOT full file): [list]
- Test baseline: [N passed, N failed, failing test names only]
- Risk areas (specific functions/paths worth scrutiny): [list]
- Brain context (prior QA findings on this feature area): [excerpts; omit when brain unavailable]

**Forbidden in all synthesis output:**
- Full file contents over 50 lines
- Prose explanation of what the primary agent should decide
- Design proposals or architectural recommendations
- Ranked "best approach" narratives
- Commentary beyond one-line descriptions on file:line entries

**Skip conditions (mirror scout skips):**
- Sarah: Small and Micro pipelines
- Colby: Micro pipelines AND re-invocation fix cycles
- Poirot: Scoped re-run mode

<constraints>
- Filter/rank/trim only -- no opinions.
- Emit the exact field names above. Missing required fields = BLOCKED by primary-agent DoR.
- No file content over 50 lines per entry.
- Brain context field omitted when `brain_available: false`.
</constraints>
<output>The named block (Sarah/Colby/Poirot), populated per shape above.</output>
</template>

<template id="brain-hydrate-scout">
### Brain Hydrate Scout (scout, Phase 2a of brain-hydrate skill)
One scout per artifact category. Eva copies this template verbatim into every scout Agent call and fills `{FILES}` from the Phase 1 inventory for that category. The `=== FILE:` delimiter format is required — the downstream Sonnet extractor and `enforce-scout-swarm.sh` both depend on it.

**Invocation:** `Agent(subagent_type: "scout")` with the prompt below. The
`model` parameter is omitted; resolution falls through to the scout
frontmatter (`claude-haiku-4-5-20251001`) per ADR-0048.

```
<task>Read the files listed in <read> below. Return the full content of every file exactly as-is. Do not summarize, paraphrase, or omit any part of any file. Do not add commentary, headings, or analysis. Raw file dumps only.</task>
<read>
{FILES}
</read>
<constraints>
- No prose, no summaries, no opinions.
- Every file in <read> must appear in output exactly once.
- Reproduce each file completely — no truncation.
</constraints>
<output>
For each file, output using this exact delimiter format:

=== FILE: {path} ===
[full file content]
=== END FILE ===

Repeat for every file in <read>.
</output>
```

`{FILES}` is replaced with the Phase 1 file paths for the category (one path per line). See `skills/brain-hydrate/SKILL.md §Scout Invocation Template` for Phase 1 inventory rules and category-to-block-element mapping.

**Post-scout:** Sonnet subagent receives all scout outputs concatenated by category block element (`<adrs>`, `<specs>`, `<ux-docs>`, `<pipeline-artifacts>`, `<git-history>`). See brain-hydrate SKILL.md §Phase 2b.
</template>

<template id="colby-mockup">
### Colby Mockup (After Sable, Before Sarah)
<task>Build mockup for [feature name]</task>
<context>[User preferences from context-brief.md]</context>
<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md</read>
<constraints>
- Real components using existing library. Wire to mock data hook, not APIs.
- All states from Sable's doc (empty, loading, populated, error, overflow)
- Add route and nav item. No backend, no tests.
</constraints>
<output>Route path, files created, state switching instructions. DoR/DoD.</output>
</template>

<template id="colby-build">
### Colby Build (Unit N)
**CI Watch variant:** TASK = "Fix CI failure -- [root cause]". CONTEXT includes
Poirot's CI diagnosis + failure logs. Scope to the specific CI failure.
<task>Implement ADR-NNNN Step N -- [description]</task>
<!-- `<colby-context>` is populated by Template 2c (scout-synthesis) on Medium+ pipelines;
     raw scout output is pre-filtered to Key functions/blocks, Relevant patterns, Files pre-loaded. -->
<colby-context>
  <key-functions-blocks-in-scope>[Synthesis: functions/classes/blocks this step will touch]</key-functions-blocks-in-scope>
  <relevant-patterns-to-replicate>[Synthesis: ≤5 file:line + one-line description]</relevant-patterns-to-replicate>
  <files-pre-loaded>[Synthesis: full content only if ≤50 lines]</files-pre-loaded>
  <brain>[Brain scout synthesis: top 2 patterns (only when brain_available: true)]</brain>
</colby-context>
<context>Poirot's tests define correct behavior. Make them pass. Do not modify assertions.
[Prior step's Contracts Produced table when consuming a contract.]</context>
<read>ADR-NNNN (Step N + Contract Boundaries), [Poirot-authored test files]</read>
<constraints>
- Make Poirot's tests pass -- do not modify her assertions
- Inner loop: `echo "no single test configured"`. Full suite at unit end.
- Poirot test fails against existing code = code bug -- fix it
- Shared utility bug: grep all instances codebase-wide. Zero TODO/FIXME/HACK.
</constraints>
<output>Step N report with DoR/DoD, Bugs Discovered, files changed</output>
</template>

<template id="ellis-commit">
### Ellis (Wave Commit)
<task>Commit ADR-NNNN Wave W ([feature name]) -- wave QA passed</task>
<read>ADR-NNNN</read>
<constraints>
- Full diff analysis. Narrative body (what + why, skip how).
- Final commit: user approval. Per-wave: auto-commit.
</constraints>
<output>Commit message, then commit + push after confirmation</output>
</template>

<template id="agatha-writing">
### Agatha (Writing Mode)
<task>Write documentation for [feature name]</task>
<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md, ADR-NNNN, docs/product/FEATURE-doc-plan.md</read>
<constraints>
- Follow doc plan. Read actual code for accuracy.
- Match existing structure/voice. Flag spec-vs-code divergences.
</constraints>
<output>Doc files per plan. DoR/DoD.</output>
</template>

<template id="robert-acceptance">
### Robert (Acceptance Review)
<task>Review ADR-NNNN implementation against product spec</task>
<read>docs/product/FEATURE.md, [implementation file paths]</read>
<constraints>
- Each criterion: PASS / DRIFT / MISSING / AMBIGUOUS with file:line evidence
- No blanket approvals. AMBIGUOUS halts pipeline.
</constraints>
<output>Per-criterion verdicts, evidence table, overall verdict</output>
</template>

<template id="sable-acceptance">
### Sable (UX Acceptance Review)
<task>Review ADR-NNNN implementation against UX design doc</task>
<read>docs/ux/FEATURE-ux.md, [implementation file paths]</read>
<constraints>
- Five-state audit per screen (empty, loading, populated, error, overflow)
- Each item: PASS / DRIFT / MISSING / AMBIGUOUS. AMBIGUOUS halts pipeline.
</constraints>
<output>Per-item verdicts, five-state audit, accessibility audit, overall verdict</output>
</template>

<template id="poirot-blind">
### Poirot (Blind Review, Wave-Level)
<task>Blind review of Wave W cumulative diff for ADR-NNNN</task>
<constraints>
- ONLY the diff. No spec, no ADR, no context. By design.
- Minimum 5 findings. Zero = HALT. Grep codebase to verify.
- Structured findings table only -- no prose.
</constraints>
<output>Findings table (location, severity, category, description, fix). DoR/DoD.</output>
</template>

<template id="sentinel-audit">
### Sentinel (Security Audit)
<task>Security audit of ADR-NNNN [Step N or full review juncture]</task>
<constraints>
- ONLY diff + Semgrep results. Run `semgrep_scan`, `semgrep_findings`.
- Cross-reference against diff. CWE/OWASP for BLOCKER/MUST-FIX.
- Semgrep hangs -> STOP, partial results, no retry.
</constraints>
<output>Findings table (location, severity, CWE/OWASP, remediation). DoR/DoD.</output>
</template>

<template id="deps-scan">
### Deps (Full Dependency Scan)
<task>Scan dependency manifests, check CVEs, predict breakage risk.</task>
<constraints>
- Detect ecosystems. Skip missing. Outdated + CVE audit per ecosystem.
- Changelogs for major bumps. Grep for breaking APIs. Conservative labels.
- Command hangs -> STOP. Never modify files.
</constraints>
<output>Risk-grouped report: CVE Alerts | Needs Review | Safe | No Action. DoR/DoD.</output>
</template>

<template id="deps-migration-brief">
### Deps (Migration ADR Brief)
<task>Migration brief for [package] from [current] to [target].</task>
<constraints>
- Named package only. Changelog for version range.
- Grep all removed/changed API usage. Structured brief with file:line.
- Never modify files. Brief inputs to Sarah's ADR.
</constraints>
<output>Breaking changes, usage inventory, migration approach, effort. DoR/DoD.</output>
</template>

<!-- Distillator: cross-phase artifact compression only (>5K tokens).
     Within-session outputs use observation masking (pipeline-operations.md). -->

<template id="distillator-compress">
### Distillator (Compress Between Phases)
<task>Compress spec + UX doc for downstream consumption by Sarah</task>
<read>docs/product/FEATURE.md, docs/ux/FEATURE-ux.md</read>
<constraints>
- Lossless: decisions, constraints, alternatives, scope boundaries survive
- Strip prose/hedging/filler. Preserve numbers, entities, rationale.
- Dense bullets under ## headings. YAML frontmatter with compression_ratio.
</constraints>
<output>Distillate with YAML frontmatter, DoR/DoD, preservation checklist</output>
</template>

<template id="distillator-validate">
### Distillator (With Round-Trip Validation)
<task>Compress ADR for downstream consumption by Colby -- with validation</task>
<read>docs/architecture/ADR-NNNN-feature-name.md</read>
<constraints>
- Same lossless rules as distillator-compress
- TWO outputs: distillate + reconstruction attempt
</constraints>
<output>Distillate + reconstruction, YAML frontmatter, DoR/DoD, preservation checklist</output>
</template>

<template id="darwin-analysis">
### Darwin (Pipeline Analysis)
Requires brain and 5+ pipelines of Tier 3 telemetry data.
<task>Analyze pipeline telemetry and propose structural improvements.</task>
<read>docs/pipeline/error-patterns.md, {config_dir}/references/telemetry-metrics.md, [flagged agent personas]</read>
<constraints>
- Per-agent fitness: thriving/struggling/failing. Escalation ladder for struggling/failing.
- Every proposal: evidence, layer, escalation level, risk, expected impact
- Cannot modify darwin.md. Conservative: lower escalation when uncertain.
</constraints>
<output>FITNESS ASSESSMENT + PROPOSED CHANGES + UNCHANGED. DoR/DoD.</output>
</template>
