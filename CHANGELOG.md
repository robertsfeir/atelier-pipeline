# Changelog

All notable changes to Atelier Pipeline are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [3.25.3] - 2026-04-06

### Added
- **brain 1.3.0: Beads-style structured provenance fields:** Extended `agent_capture` schema with optional metadata fields for `thought_type: decision` — `decided_by` (`{agent: string, human_approved: boolean}`), `alternatives_rejected` (array of `{alternative, reason}`), `evidence` (array of `{file, line}`), and `confidence` (0-1 number). No DDL migration needed; fields stored in existing metadata JSONB column (GIN-indexed). `atelier_trace` adds `superseded_by` reverse lookup (computed from thought_relations, not stored). Migration 007 is noop. Graceful degradation: missing provenance fields accepted. Wiring coverage verified via Roz test spec (T-0026 series, 28 tests). Poirot review fixes: merge-path enrichment, dead try/catch removal in migration 007, non-destructive destructuring, empty chainIds guard, decided_by consistency guard (issue #23, ADR-0026)

## [3.25.2] - 2026-04-06

### Added
- **`permissionMode: plan` for read-only agents:** robert, sable, investigator, distillator, darwin, deps, and sentinel frontmatter overlays now declare `permissionMode: plan`, adding harness-level read-only enforcement on top of the existing `disallowedTools` restrictions (issue #29 3c)

### Fixed
- **enforce-eva-paths.sh subagent bypass:** Hook now checks `agent_type` from PreToolUse stdin JSON and exits 0 for subagent contexts, letting per-agent frontmatter hooks handle their own enforcement. Previously the hook blocked all subagent writes outside `docs/pipeline/`, requiring the setup-mode sentinel as a workaround

## [3.25.1] - 2026-04-06

### Added
- **Diagnostic scout swarm for Investigation Mode:** Roz now receives a `<debug-evidence>` block pre-populated by four haiku scouts (Files — stack trace + recent git diff; Tests — failing test output; Brain — symptom-derived agent_search; Error grep — error string grep) before investigating a user-reported bug. Previously scouts were skipped for Investigation Mode entirely, requiring Roz to do all file discovery herself. (`pipeline-orchestration.md`, `debug.md`)

## [3.25.0] - 2026-04-06

### Added
- **brain-extractor structured quality signals:** Extended brain-extractor to emit per-invocation `thought_type: 'insight'` captures with `metadata.quality_signals` containing structured fields from Roz (verdict, test counts, finding counts), Colby (rework flag, files changed, DoD completeness), Cal (step count, test spec count, ADR revision), and Agatha (docs written, divergence findings) — with graceful degradation for absent markers (ADR-0025 Wave 1)
- **State-file hydration:** `hydrate-telemetry.mjs` now accepts `--state-dir` to parse `pipeline-state.md` (completed progress items) and `context-brief.md` (user decisions) into the brain with `thought_type: 'decision'`, `source_agent: 'eva'`, `source_phase: 'pipeline'` — deduplication via sha256 content hashing (ADR-0025 Wave 2)
- **SessionStart hook (`session-hydrate.sh`):** New hook runs telemetry hydration and state-file parsing automatically at each session start; non-blocking (`exit 0` always) (ADR-0025 Wave 2)
- **`pipeline` source_phase:** New enum value added to `source_phase` via migration 006 for state-file decision captures

### Removed
- **`warn-dor-dod.sh`:** Deleted. DoR/DoD compliance checking superseded by mechanical quality signal extraction in brain-extractor; `session-hydrate.sh` occupies the SessionStart slot (ADR-0025 Wave 2)
- **Eva behavioral brain writes:** Removed "Writes (cross-cutting only)" section from `pipeline-orchestration.md` — Eva's pipeline decisions now captured mechanically via state-file parsing at SessionStart (ADR-0025 Wave 2)

### Fixed
- **Agatha source_phase:** Changed from invalid `'docs'` to `'handoff'` to align with SOURCE_PHASES enum validation (brain captures were silently dropped)

## [3.24.0] - 2026-04-05

### Added
- **brain-extractor agent:** New Haiku subagent (`source/shared/agents/brain-extractor.md`) invoked via `SubagentStop` `"type": "agent"` hook after every Cal, Colby, Roz, and Agatha completion. Extracts decisions, patterns, lessons, and seeds from the parent agent's output and calls `agent_capture` -- no agent instruction required (ADR-0024)

### Removed
- **`warn-brain-capture.sh`:** Deleted. Replaced by mechanical brain-extractor hook
- **`prompt-brain-capture.sh`:** Deleted. Advisory prompt hook superseded by mechanical extraction
- **Brain Access persona sections:** Removed from Cal, Colby, Roz, and Agatha in `source/shared/agents/` -- behavioral brain capture instruction replaced by hook
- **Brain Capture Protocol section:** Removed from `source/shared/references/agent-preamble.md` -- shared instruction block superseded by hook mechanism

### Changed
- **Agent persona files:** ~44 lines of brain capture behavioral instructions removed across four agent personas (Cal, Colby, Roz, Agatha) -- personas now contain only functional instructions
- **settings.json SubagentStop block:** Replaced `warn-brain-capture` and `prompt-brain-capture` hook entries with a single `"type": "agent"` entry scoped to `cal || colby || roz || agatha` (loop prevention: extractor `agent_type` excluded from condition)
- **Orchestration docs:** References to agent-level behavioral capture gates updated to reflect mechanical model; Eva cross-cutting captures unchanged
- **Technical reference:** Hybrid Capture Model section updated; Agent Reference Table updated with brain-extractor row and mechanical capture annotation for Cal/Colby/Roz/Agatha brain access column

## [3.23.3] - 2026-04-05

### Fixed
- **Hook enforcement:** Fixed 5 PreToolUse hooks with improved guards (enforce-eva-paths glob pattern matching, enforce-sequencing task iteration, enforce-pipeline-activation phase checks, enforce-git safety checks, enforce-context-brief state management)
- **Haiku scout fan-out:** Colby/Roz receive pre-fetched brain context from Eva scouts in `<colby-context>` and `<qa-evidence>` blocks; fast-path re-invocations skip brain calls entirely
- **Roz fast-path mode:** Scoped re-run for fix verification skips DoR ceremony, maxTurns reduced to 60
- **Colby fast-path mode:** Re-invocation fix cycles skip DoR/retro/brain checks, maxTurns reduced to 75
- **Poirot finding triage:** Test coverage assertions auto-populate, XML schema tags for xml-prompt-schema.md, eva-paths glob pattern matching simplified

### Added
- New enforcement test suite: `tests/hooks/test_enforce_eva_paths.py` covers glob patterns and path validation

## [3.23.2] - 2026-04-05

### Changed
- **Context reduction:** Always-loaded baseline reduced ~1,780 words across default-persona.md (274→109 lines, 72% reduction) and agent-system.md (64% reduction) via Distillator compression; boot sequence and agent discovery moved to read-on-boot reference files
- **Haiku fan-out:** Medium+ pipelines now use Explore+haiku fan-out scouts for ADR research (3 parallel scouts replace Eva grep) instead of Eva doing all reading herself
- **Reference files:** Extracted session-boot.md and agent-discovery.md as consumable boot-only files, evicted from active context after session initialization

### Fixed
- pipeline-orchestration.md: Medium ADR research extended to use scout-driven briefing (was Eva-only)
- invocation-templates.md: Added scout-research-brief template; cal-adr and cal-adr-large updated

### Credits
- Context reduction and haiku fan-out approaches inspired by [Andrey Popov's](https://github.com/vospr) reverse analysis of Atelier Pipeline against the Context Engineering template

## [3.23.1] - 2026-04-05

### Fixed
- prompt-brain-capture hook: added `"if"` guard to prevent feedback loops on scout agents (cal/colby/roz only)
- pipeline-setup SKILL.md: corrected hook type from "command" to "prompt" for brain-capture hook in template

## [3.23.0] - 2026-04-04

### Changed
- Colby: re-invocation fast path — skip DoR/retro/brain on fix cycles, maxTurns 100→75
- Roz: scoped re-run mode — skip full ceremony on fix verification, maxTurns 100→60
- Eva: aggressive context eviction — boot-once sections marked consumed and disposable
- Distillator: observation masking constraint — strip raw tool payloads, preserve conclusions

### Fixed
- Core agent constant: added sentinel, darwin, deps (were falsely announced as custom agents)

## [3.22.0] - 2026-04-04

### Changed
- Ellis agent rewritten to fast-path commit mode — exempt from DoR/DoD preamble
- Ellis maxTurns reduced from 40 to 12 (expected ~5-6 per commit)
- Agent preamble now includes explicit Ellis exemption clause
- Claude marketplace.json version synced (was stuck at 3.17.0)

## [3.21.0] - 2026-04-04

### Changed
- Agent specification reduction: 12 agent personas reduced 58% (2,392→1,003 lines)
- Invocation templates compressed (806→300 lines)
- Session boot sequence delegated to shell hook (session-boot.sh)
- Pipeline-orchestration.md condensed (948→578 lines)
- Poirot persona restored Sonnet-critical procedural scaffolding (65→73 lines)
- Ellis persona reduced to fast-path commit mode (64→54 lines)
- Universal scope classifier enabled on Large pipelines (removed blanket all-Opus rule)
- Opus promotion threshold raised from ≥3 to ≥4; Haiku demotion at ≤-2
- Cal and Colby on Large now use per-step classifier
- Large pipeline sizing advisory: Eva offers Medium as cost-aware alternative

### Added
- Step-sizing reference file (extracted from Cal persona)
- Session-boot.sh hook for mechanical boot sequence steps
- Large Sizing Cost Advisory in pipeline-orchestration.md

## [3.20.0] - 2026-04-03

### Added
- Three-layer enforcement pyramid: per-agent frontmatter hooks (Layer 2) replacing monolithic enforce-paths.sh
- 7 per-agent enforcement scripts (enforce-{roz,cal,colby,agatha,product,ux,eva}-paths.sh)
- Robert-spec and Sable-ux producer personas for spec/UX document authoring
- Wave-boundary compaction advisory hook (prompt-compact-advisory.sh)
- Path traversal (..) rejection in all enforcement hooks
- permissionMode: acceptEdits on all 6 write-capable agents
- Cursor-specific enforcement-config.json with full schema

### Changed
- Source directory split: source/shared/, source/claude/, source/cursor/ with overlay assembly pattern
- enforcement-config.json simplified for Claude Code (architecture_dir, product_specs_dir, ux_docs_dir removed — per-agent hooks hardcode paths)
- /pm and /ux commands now route to robert-spec and sable-ux subagents
- Agent count: 14 (11 core + 3 opt-in)
- Hook count: 20 scripts + 1 config

### Removed
- enforce-paths.sh monolith (Claude Code only — Cursor retains it)
- test_enforce_paths.py (replaced by per-agent enforcement tests)

## [3.19.0] - 2026-04-03

### Added
- T3 telemetry schema: `invocations_by_model` (per-model invocation counts), `total_tokens` (aggregate token consumption), `project_name` (cross-project scope identifier)
- `project_name` field in `pipeline-config.json` — collected during `/pipeline-setup`, used as telemetry scope with git remote fallback
- State file guard in `/pipeline-setup` — `docs/pipeline/` state files and `pipeline-config.json` are no longer overwritten on re-install

### Changed
- T2 and T3 telemetry captures now include `scope` parameter with `pipeline_project_name` for cross-project analysis
- Boot sequence step 3b derives `pipeline_project_name` from config, git remote, or directory basename

## [3.18.0] - 2026-04-03

### Added
- Hybrid agent brain capture model (ADR-0021) — Cal, Colby, Roz, and Agatha now capture domain-specific knowledge directly via `mcpServers: atelier-brain` frontmatter
- Three prompt hooks for brain integration: `prompt-brain-prefetch` (pre-invocation context), `prompt-brain-capture` (post-invocation reminder), `warn-brain-capture` (brain offline warning)
- Seed capture protocol — agents can capture out-of-scope ideas as seeds for future pipelines
- Poirot (gate 5) and Robert (gate 7) enforcement in `enforce-sequencing.sh`
- `colby_blocked_paths` in `enforcement-config.json` — 14 blocked prefixes prevent Colby from writing to docs/, infra/, deploy/, etc.
- Five new Cursor plugin reference docs (`.mdc`): `qa-checks`, `branch-mr-mode`, `telemetry-metrics`, `xml-prompt-schema`, `cloud-architecture`
- Pipeline-setup Step 3c for Cursor reference doc sync

### Changed
- Agent personas enriched with `model`, `effort`, `color`, `maxTurns` frontmatter and brain-access protocol sections
- `{config_dir}` placeholder replaces hardcoded `.claude/` in source templates (IDE-agnostic)
- `{features_dir}` and `{source_dir}` placeholders added to pipeline-setup

### Fixed
- Cursor plugin agent drift — all 12 agents synced from source/ (byte-identical)
- Duplicate YAML frontmatter in `.cursor-plugin/agents/colby.md` and `robert.md`
- Three `.mdc` rule files regenerated from source/ (`agent-system`, `default-persona`, `pipeline-orchestration`)

## [3.17.0] - 2026-04-02

### Added
- Four new lifecycle hooks: `log-agent-start.sh` (SubagentStart), `log-agent-stop.sh` (SubagentStop telemetry), `post-compact-reinject.sh` (PostCompact context preservation), `log-stop-failure.sh` (StopFailure error tracking)
- `if` conditional support in `settings.json` hook entries -- added to `enforce-git.sh` and `warn-dor-dod.sh`, reducing ~50% hook process spawns

### Changed
- Hook system modernized (Wave 2) -- hooks now support conditional evaluation and lifecycle-aware triggers
- README pipeline diagram replaced with Mermaid flowchart for better GitHub rendering

## [3.16.1] - 2026-04-02

### Fixed
- Restored distributed routing capability that was missing after 3.16.0 merge

### Changed
- Upgraded Roz and Colby default model from Sonnet to Opus for higher-quality output

## [3.16.0] - 2026-04-02

### Added
- Agent frontmatter enrichment with YAML metadata (name, description, tools, allowed_write_paths)
- Distributed routing -- Cal and Colby can spawn scoped Agent sub-invocations (Cal spawns Roz for test spec review; Colby spawns Roz for per-unit QA and Cal for architectural consultation)

### Changed
- Updated technical reference and agent-system documentation for distributed routing

## [3.15.2] - 2026-04-02

### Fixed
- Cursor plugin version aligned to match Claude Code release version
- Stale metadata corrected -- marketplace version sync, CLAUDE.md agent counts

## [3.15.1] - 2026-04-02

### Fixed
- Enforcement hook bypass switched from environment variable to file sentinel for improved security

## [3.15.0] - 2026-04-02

### Added
- Wave-based build ceremony -- QA, blind review, and commits happen per wave instead of per unit, reducing agent invocations by ~70%
- Universal model classifier -- scope-based model selection replaces hardcoded Opus; estimated 60-70% cost reduction
- Cursor IDE support with full feature parity (same agents, hooks, brain, commands)
- Agent output masking -- Eva replaces full outputs with structured receipts for 98% context reduction
- Just-in-time rule loading -- Eva's orchestration rules split into always-loaded and on-demand sections
- Brain operations batched per wave instead of per invocation

## [3.14.0] - 2026-04-01

### Added
- Dashboard integration with pipeline telemetry visualization
- Quality-gate cleanup and consolidation
- Setup hook bypass for smoother installation flow

## [3.12.2] - 2026-03-31

### Fixed
- Brain MCP server hardened against all 7 identified crash vectors (ADR-0017)

## [3.12.1] - 2026-03-30

### Added
- Pipeline-activation enforcement hook -- blocks Colby and Ellis from operating without an active pipeline

## [3.12.0] - 2026-03-30

### Added
- Cal sizing gate for architectural reviews
- Context diet protocol to reduce token consumption
- Template index for easier file discovery

### Fixed
- Brain-setup scope defaulting bug (was using "default" instead of project-derived value)
- Dashboard chart canvas destruction on scope switch

## [3.11.0] - 2026-03-30

### Changed
- Dashboard metrics now show honest, day-aggregated cost trends with hydration timestamps
- Telemetry charts improved for accuracy and readability

## [3.10.1] - 2026-03-30

### Fixed
- Enforcement-config.json validation added after installation to catch setup issues

## [3.10.0] - 2026-03-30

### Added
- Dashboard improvements with enhanced telemetry visualization
- Telemetry hydration for populating dashboards from brain data
- Tier 3 enforcement gate for telemetry quality

### Fixed
- Brain MCP server environment variable passthrough for plugin contexts

## [3.9.0] - 2026-03-29

### Added
- Darwin pipeline evolution engine -- analyzes telemetry, evaluates agent fitness, proposes structural improvements (opt-in, requires brain)
- Telemetry dashboard for visualizing pipeline health metrics

## [3.8.0] - 2026-03-29

### Added
- Agent telemetry capture -- duration, cost, and outcome tracking per agent invocation
- Deps dependency scanner -- outdated package detection, CVE checking, and upgrade breakage prediction (opt-in)
- CI Watch self-healing CI protocol for automated CI failure detection and recovery (ADR-0013)

## [3.7.0] - 2026-03-29

### Added
- `pipeline-uninstall` and `brain-uninstall` skills for clean removal

### Fixed
- Atelier Brain MCP server restored in plugin `.mcp.json` configuration

## [3.6.6] - 2026-03-29

### Fixed
- Ellis allowed on Micro pipelines where Roz is skipped

## [3.6.5] - 2026-03-29

### Fixed
- Sentinel uses Semgrep plugin as prerequisite instead of standalone install
- Legacy Sentinel setup artifacts cleaned up

## [3.6.4] - 2026-03-29

### Changed
- Replaced deprecated `semgrep-mcp` with built-in Semgrep MCP integration

## [3.6.3] - 2026-03-29

### Fixed
- Semgrep MCP setup updated to use built-in integration

## [3.6.2] - 2026-03-29

### Fixed
- Semgrep CLI install step added to Sentinel setup to prevent missing-binary failures

## [3.6.1] - 2026-03-29

### Fixed
- Sentinel install hardened against Python 3.14 and setuptools >= 81 compatibility issues

## [3.6.0] - 2026-03-29

### Added
- Compaction API integration -- server-side context management with `PreCompact` hook for pipeline state preservation
- Observation masking -- superseded tool outputs replaced with structured placeholders to keep Eva's context lean
- Distillator reserved for structured document compression at phase boundaries

### Changed
- Context cleanup advisory updated -- Eva no longer estimates context usage or counts handoffs

## [3.5.1] - 2026-03-29

### Fixed
- Sentinel security audit hardened with improved scan reliability

### Security
- Word boundary regex in enforcement hooks prevents false-positive blocks

## [3.5.0] - 2026-03-29

### Added
- Sentinel security agent (opt-in) -- Semgrep-backed SAST scanning at the review juncture
- Agent Teams experimental feature -- parallel wave execution with Colby Teammate instances
- ADR-0009 (Sentinel) and ADR-0010 (Agent Teams) architecture documentation

## [3.4.1] - 2026-03-28

### Added
- DoR/DoD warn hook (`SubagentStop`) -- advisory warning when Colby or Roz output is missing quality sections
- Agent discovery -- Eva scans for custom agent personas at session boot
- Eva test blocking -- enforcement hook prevents test commands from the main thread (Roz owns all QA)

### Fixed
- Ellis sequencing gate -- allows non-pipeline commits while still gating during active pipelines

[Unreleased]: https://github.com/robertsfeir/atelier-pipeline/compare/main...HEAD
[3.18.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.17.0...v3.18.0
[3.17.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.16.1...v3.17.0
[3.16.1]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.16.0...v3.16.1
[3.16.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.15.2...v3.16.0
[3.15.2]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.15.1...v3.15.2
[3.15.1]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.15.0...v3.15.1
[3.15.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.14.0...v3.15.0
[3.14.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.12.2...v3.14.0
[3.12.2]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.12.1...v3.12.2
[3.12.1]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.12.0...v3.12.1
[3.12.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.11.0...v3.12.0
[3.11.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.10.1...v3.11.0
[3.10.1]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.10.0...v3.10.1
[3.10.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.9.0...v3.10.0
[3.9.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.8.0...v3.9.0
[3.8.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.7.0...v3.8.0
[3.7.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.6.6...v3.7.0
[3.6.6]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.6.5...v3.6.6
[3.6.5]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.6.4...v3.6.5
[3.6.4]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.6.3...v3.6.4
[3.6.3]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.6.2...v3.6.3
[3.6.2]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.6.1...v3.6.2
[3.6.1]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.6.0...v3.6.1
[3.6.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.5.1...v3.6.0
[3.5.1]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.5.0...v3.5.1
[3.5.0]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.4.1...v3.5.0
[3.4.1]: https://github.com/robertsfeir/atelier-pipeline/compare/v3.4.0...v3.4.1
