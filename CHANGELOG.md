# Changelog

All notable changes to Atelier Pipeline are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [Unreleased]

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
