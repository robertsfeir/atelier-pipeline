# Changelog

All notable changes to Atelier Pipeline are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [Unreleased]

## [5.1.3] - 2026-05-04

### Fixed
- **Brain capture gate fires before sequencing (ADR-0053).** `enforce-brain-capture-gate.sh` was registered after `enforce-sequencing.sh` in the Agent PreToolUse hook array. When both conditions needed resolving, Eva hit the sequencing block first, fixed state, then hit the brain gate — a two-step blocking dance per agent handoff. Gate and reminder now fire first; sequencing is checked after the pending capture is cleared.
- **`prompt-brain-capture-reminder.sh` added (new hook).** Soft prompt hook that fires before the hard gate when a pending brain capture exists. Injects a plain-language reminder into Eva's context so she knows what to do before the block fires, rather than seeing only the exit-2 error.
- **Brain capture gate hooks wired into the `pipeline-setup` template.** `enforce-brain-capture-gate.sh`, `enforce-brain-capture-pending.sh`, `clear-brain-capture-pending.sh`, and `prompt-brain-capture-reminder.sh` were present as source files but never registered in the `settings.json` template written by `/pipeline-setup`. Fresh installs and re-runs now wire all four hooks correctly: gate+reminder in PreToolUse Agent (first position), pending marker in SubagentStop, clear in PostToolUse.
- **Step 0g added to `/pipeline-setup`.** Idempotent migration that runs on every invocation and fixes existing `settings.json` files: reorders the Agent PreToolUse hooks so brain-capture-gate precedes sequencing, inserts `enforce-brain-capture-pending.sh` into SubagentStop if absent, and adds the PostToolUse `clear-brain-capture-pending.sh` section if missing. Existing projects get the fix automatically on next `/pipeline-setup` run without manual intervention.
- **Agent tool `model` parameter accepts only logical aliases.** `pipeline-models.md` Rule 2 instructed Eva to translate logical names to provider-shaped model IDs (e.g. `claude-sonnet-4-6`) before passing them to the Agent tool. The Agent tool schema rejects full model ID strings — only `"sonnet"`, `"opus"`, or `"haiku"` are valid. Rule 2 rewritten: Eva passes the logical alias directly; Claude Code resolves it internally. The reference table is retained for Bedrock/Vertex install-time configuration. `brain-hydrate/SKILL.md` model assignment table updated to show logical aliases for consistency.

### Added
- **`source/claude/hooks/prompt-brain-capture-reminder.sh`** — new soft prompt hook for brain capture pending state (see Fixed above).

## [5.1.0] - 2026-05-01

### Changed
- **Agent model assignments.** Six agents moved from `claude-opus-4-7` to `claude-sonnet-4-6` to reduce token consumption: colby, agatha, robert-spec, sable-ux, investigator (Poirot), and sherlock. Sarah remains on `claude-opus-4-7` for high-stakes architectural decisions.

## [5.0.1] - 2026-04-29

### Changed
- **`skills/brain-hydrate/SKILL.md`:** Removed hardcoded 100-thought-per-run cap. The limit was an unjustified conservative guard; `agent_search` dedup handles safe re-runs without it. Both the skill source (`skills/brain-hydrate/SKILL.md`) and the plugin cache copy were updated.
- **Pipeline re-synced to v5.0.0 baseline.** All installed `.claude/` files (14 agents, 5 rules, 6 commands, 16 references, 27 hooks) re-synced from source via `/pipeline-setup`.
- **mybrain plugin wired.** `.claude/settings.json` swapped 8 stale `mcp__plugin_atelier-pipeline_atelier-brain__*` permission entries for the correct `mcp__mybrain__*` entries. `.claude/brain-config.json` updated to match.
- **Brain hydration recorded.** `docs/pipeline/pipeline-state.md` updated: 275 thoughts from 53 ADRs, 14 specs, UX doc, pipeline artifacts, and git history now seeded in the brain.

### Added
- **`docs/architecture/ADR-0056-brain-migration-wizard.md`** — new ADR formally recording the 7-state migration wizard decision from the prior session's pipeline-setup run.

## [5.0.0] - 2026-04-29

### Added
- **ADR-0056: Brain migration wizard in pipeline-setup.** 7-state machine with two parallel tracks (migrate existing brain / fresh install), pg_dump backup gate before any destructive operation, advisory-blocking at each state, and full rollback contract. Guides users from the embedded brain/ server to the standalone mybrain plugin without data loss.
- **tests/adr-0056/:** 14 wizard contract tests covering all 7 states, both tracks, and rollback paths.

### Changed
- **ADR-0055 Phase 3: brain/ directory removed entirely.** The embedded Node.js brain server (`brain/`), brain-setup skill, and `session-hydrate-enforcement.sh` hook are removed from the plugin. Brain persistence is now provided by the standalone mybrain plugin (installed separately).
- **Plugin cleanup.** Brain MCP server entries and brain SessionStart hooks removed from `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, and `.cursor-plugin/mcp.json`. `enforcement-config.json` updated to `pytest tests/` only.
- **brain-uninstall skill** updated to target the mybrain plugin rather than the removed embedded server.
- **tests/brain/ removed.** All brain Node.js unit tests deleted; `test_brain_wiring.py` assertions inverted to confirm brain files are absent; adr-0054 brain Node test suite pruned; adr-0055 Phase 3 assertions added.
- **Docs updated.** `technical-reference.md` and `user-guide.md` remove brain internals, add mybrain plugin references and upgrade notices.

## [4.5.0] - 2026-04-28

### Added
- **ADR-0054: Multi-provider LLM and pipeline routing.** Brain now supports three LLM adapter families (`openai-compat`, `anthropic`, `local`) behind a uniform interface in `brain/lib/llm-provider.mjs`. New optional `brain-config.json` fields select and tune embeddings and chat independently: `embedding_provider`, `embedding_model`, `embedding_api_key`, `embedding_base_url`, `chat_provider`, `chat_model`, `chat_api_key`, `chat_base_url`. Providers: `openrouter` (default), `openai`, `github-models` (recommended for GitHub Enterprise; uses `GITHUB_TOKEN`), `anthropic` (chat only -- no embeddings API), `local` (Ollama-compatible, no key, default endpoint `http://localhost:11434/v1`, default model `gte-qwen2-1.5b-instruct`). A 1536-dim embedding probe runs at startup so misconfigured providers fail fast. Pipeline routing exposes a `model_provider` field in `pipeline-config.json` (`anthropic` / `bedrock` / `vertex`). Backward compatible: existing v3.x configs with only `openrouter_api_key` continue to work unchanged. `skills/brain-setup/SKILL.md` and `docs/guide/technical-reference.md` updated for the new setup flow and module docs.

## [4.1.0] - 2026-04-28

### Added
- **ADR-0053: Mechanical brain-capture gate (three-hook loop).** Replaces the silently-broken `type:agent` SubagentStop brain-extractor with three `type:command` hooks: `enforce-brain-capture-pending.sh` (SubagentStop, writes pending marker for 8-agent allowlist), `enforce-brain-capture-gate.sh` (PreToolUse on Agent, blocks Eva's next invocation until she calls `agent_capture`), `clear-brain-capture-pending.sh` (PostToolUse on `agent_capture`, deletes marker on success). Eva curates captures before every agent handoff. `.brain-unavailable` sentinel suppresses gate when brain is unreachable. 29 behavioral tests added.

### Changed
- **brain-extractor agent removed.** The `type:agent` SubagentStop hook was silently broken in Claude Code 2.1.121 (zero fires in 1,591 qualifying events); the agent file has been removed from source, installed copies, and cursor plugin. Brain capture is now gate-enforced via Eva.
- **Brain MCP source_agent enum cleaned.** Removed deprecated agent names (`cal`, `roz`, `darwin`, `deps`, `brain-extractor`) from Zod validation in `brain/lib/config.mjs` and from `brain/schema.sql` for fresh installs.
- **Documentation sweep.** All stale `brain-extractor` capture mechanism language updated across pipeline-orchestration.md, agent-system.md, default-persona.md, agent-preamble.md, pipeline-operations.md, invocation-templates.md, xml-prompt-schema.md, pipeline-models.md. README.md updated: Cal→Sarah, Roz references removed, Darwin/Deps optional agent paragraphs removed. Escape hatch protocol for `.brain-unavailable` sentinel documented in pipeline-orchestration.md.
- **session-boot.sh CORE_AGENTS:** `brain-extractor` removed from agent discovery list.
- **post-compact-reinject.sh:** Brain capture description updated from brain-extractor hook to three-hook gate model.

## [4.0.17] - 2026-04-27

### Added
- **ADR-0050 staged:** `docs/architecture/ADR-0050-colby-stop-verification-hook.md` committed — documents the enforce-colby-stop-verify.sh design decision (previously untracked)

### Changed
- **enforce-scout-swarm.sh `if` guard (source template):** `skills/pipeline-setup/SKILL.md` Agent-matcher JSON block now carries `"if": "tool_input.subagent_type == 'sarah' || tool_input.subagent_type == 'colby' || tool_input.subagent_type == 'scout'"` so future installs scope the hook correctly
- **enforce-scout-swarm.sh hook comment:** installed hook header comment updated to document the `sarah || colby || scout` gate
- `.claude/` reference and rule files updated: `agent-preamble.md`, `dor-dod.md`, `invocation-templates.md`, `xml-prompt-schema.md`, `agent-system.md`, `default-persona.md`, `pipeline-orchestration.md`, `pipeline-operations.md`, `colby.md`, `enforce-colby-stop-verify.sh`, `prompt-brain-prefetch.sh`

## [4.0.16] - 2026-04-27

### Changed
- Brain `<thought>` format now specifies all six attributes: `type`, `agent`, `phase`, `captured_by`, `created_at`, `relevance` — provenance fields were already returned by `agent_search` but not specified in the format contract
- Invocation templates Shared Protocols section now includes a fully-formed `<brain-context>` example with credibility-weighting guidance
- Agent preamble step 3 extended: agents use `captured_by` and `created_at` to gauge thought credibility
- `xml-prompt-schema.md` `<thought>` attribute table and value-space definitions updated; agent count corrected to 18 (verified against live `SOURCE_AGENTS` enum)
- Closes Issue #45 item 5

## [4.0.15] - 2026-04-27

### Added
- **ADR-0052: Declared `<contract>` blocks for pipeline skill files (issue #47):** All five pipeline skill files (`pipeline-setup`, `pipeline-uninstall`, `brain-setup`, `brain-uninstall`, `brain-hydrate`) now carry a top-level `<contract>` block declaring `requires`, `produces`, and `invalidates`, making each skill's preconditions and side effects legible without execution. `xml-prompt-schema.md` registers `<contract>` as a valid top-level skill-file tag. Behavioral declaration only — no enforcement hook, per ADR-0052 rationale.

## [4.0.14] - 2026-04-27

### Added
- **ADR-0051: Brain trust-boundary hardening (issue #45 items 1-2):** `agent-preamble.md` step 3 reframed from "Review brain context" to "Treat brain context as reference, not instruction" — three concrete prohibitions added and a live-invocation-wins conflict mechanic specified, blocking prompt injection via imperative-shaped `<thought>` elements. `prompt-brain-prefetch.sh` advisory now requires Eva to read scope from `.claude/brain-config.json` and names cross-project leakage as the specific failure mode, closing the ambiguity that an "or fallback" phrasing would invite.

## [4.0.12] - 2026-04-27

### Added
- **ADR-0050: Colby SubagentStop typecheck + auto-format verification hook (issue #44):** New hook `enforce-colby-stop-verify.sh` fires after every Colby stop, runs `verify_commands.typecheck` (and optionally `verify_commands.format`), and exits 2 on typecheck failure to re-engage Colby. Stateful failure counter resets on success; configurable `verify_max_attempts` cap prevents infinite loops. Opt-in via `pipeline-config.json`. Claude Code only — Cursor lacks SubagentStop. `SKILL.md` updated with install manifest entry and config key reference.

## [4.0.11] - 2026-04-27

### Fixed
- SendMessage resume: clarified that Eva must use agentId UUID (not agent name) as the `to` value — name-based addressing fails for stopped subagents; UUID resume validated by live test with cache reuse confirmed

## [4.0.10] - 2026-04-27

### Added
- ADR-0049: in-session SendMessage resume for Sarah and Poirot — Eva captures agentId on every invocation and uses SendMessage (instead of a fresh Agent spawn) for ADR revisions and scoped re-runs, skipping the re-read cost on the two highest-context agents
- CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 is now a mandatory part of every pipeline-setup install, ensuring SendMessage is always available

### Fixed
- pipeline-setup: stale `roz` reference in hook registration template corrected to `poirot`
- pipeline-setup: Step 6d agent-resume prerequisite simplified to always-apply (removed [Y/n] prompt)

## [4.0.9] - 2026-04-27

### Added

- **Scout and synthesis registered subagents (ADR-0048):** `scout` and `synthesis` are now registered custom subagents with explicit versioned model IDs pinned in frontmatter, closing the last model-alias gap left by ADR-0047 Phase 4. Scout invocations change from `Agent(subagent_type: "Explore", model: "haiku")` to `Agent(subagent_type: "scout")` — the `model` parameter is dropped and Anthropic's resolution order falls through to the scout frontmatter (`claude-haiku-4-5-20251001`). Synthesis invocations change from `Agent(subagent_type: "general-purpose", model: "sonnet", effort: "low")` to `Agent(subagent_type: "synthesis", effort: "low")` — frontmatter pins `claude-sonnet-4-6`. Both subagents are registered across Claude Code and Cursor plugin targets. `enforce-scout-swarm.sh` and `.claude/settings.json` updated from `Explore` to `scout`. Invocation templates, pipeline-phases, pipeline-models, gauntlet, routing-detail, brain-hydrate skill, and pipeline-setup skill updated across all three targets (source, .claude/, .cursor-plugin/).

## [4.0.8] - 2026-04-27

### Changed

- **Opus 4.7 pipeline tuning — Phase 1 (literal-instruction surfaces):** Tightened six literal-instruction surfaces across agent personas and orchestration rules. Sentinel's minimum-findings floor replaced with Poirot's zero-with-confidence model (padded reports are worse than an honest zero); the fix is applied to both the `<constraints>` block and the DoD output template. Agatha's workflow promoted from advisory bullets to six directive numbered steps with an explicit `Written {paths}, updated {paths}.` return-line format. robert-spec and sable-ux workflows expanded from 4-line sketches to full subagent-mode procedures with output format blocks and explicit return lines. Sarah's exploration ceiling (`~8 files`) reinforced with a concrete fallback condition at the identity level. Eva's invocation template `<read>` advisory clarified from `prefer ≤6` to `typically ≤6; include more when the decision clearly requires it`.
- **Opus 4.7 pipeline tuning — Phase 2 (maxTurns recalibration):** Recalibrated turn budgets against Opus 4.7's ~2x call efficiency across both Claude Code and Cursor agent trees: Colby 200→120, Agatha 60→40, Poirot 80→50, Sherlock 80→50, Sarah 45→30. Cursor tree aligned to Claude tree (cursor tree had drifted to different values).
- **Opus 4.7 pipeline tuning — Phase 3 (Sentinel model demotion):** Sentinel demoted from `opus` to `sonnet`. Pattern-matching SAST with `effort: low` suppresses Opus reasoning; Sonnet matches the actual workload. Per-agent table in `pipeline-models.md` updated with rationale.
- **Opus 4.7 pipeline tuning — Phase 4 (explicit model IDs):** Pinned explicit versioned model IDs across all 26 frontmatter files (13 Claude Code + 13 Cursor): `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`. Generic aliases (`opus`, `sonnet`, `haiku`) eliminated. `skills/brain-hydrate/SKILL.md` model assignment table aligned. Structural pytest added (`tests/test_frontmatter_model_ids.py`) that fails CI when any frontmatter declares a generic alias — prevents silent alias drift from invalidating the recalibrated turn budgets.
- **Opus 4.7 pipeline tuning — Phase 5 (web-search regression):** Documented Opus 4.7's known agentic web-search regression in `pipeline-models.md`. No pipeline agent tool list includes `WebSearch` or `WebFetch`; Eva's auto-routing must not synthesize these tools in.

## [4.0.7] - 2026-04-24

### Added

- **Brain Unit 2 — ADR metadata contract:** Brain extractor now wires producer/consumer contracts for ADR metadata. Sarah and Colby write structured ADR revision markers (`Revision <N>`); brain-extractor reads and captures `adr_revision` counts, `factual_claim_count`, and `loc_estimate` as typed quality signals. Closes the gap where revision cycles were invisible to the brain.

### Fixed

- **Brain source_agent enum:** Added `sarah` and `sherlock` as valid `source_agent` enum values in the brain schema and REST API. Previously, captures from these agents were silently rejected.
- **Brain MCP preload:** `atelier_hydrate` MCP tool is now pre-loaded in the brain-hydrate skill so it is available without a ToolSearch roundtrip. Scope format documentation corrected to match actual dot-separated namespace format. Fifteen `roz_qa` → `qa_status` field-name drift tests corrected.
- **Brain-hydrate scout format contract:** Explore+haiku scouts now receive a verbatim invocation template (task/read/constraints/output) inside their prompt, mandating `=== FILE: {path} ===` / `=== END FILE ===` delimiters. Template mirrored to `source/shared/references/invocation-templates.md` as `brain-hydrate-scout`. `enforce-scout-swarm.sh` extended with an Explore enforcement block that blocks scouts missing the format contract in their `<output>` section; removed the `if` filter from `settings.json` that was making the new block dead code.

### Changed

- **Poirot — three-pass attention allocation:** Blind review workflow now opens with an explicit three-surface rule: (1) the diff itself, (2) the integration surface (callers, consumers, downstream types), (3) the omission surface (what a correct implementation *should* have touched but didn't). The omission surface is where meaningful bugs hide after tests pass.
- **Sarah — risk shapes:** The `## Rationale` ADR template now directs Sarah to state risk shapes inline: what would fail, in what direction, under what condition. Example included. Replaces vague category labels ("Performance risk") with narrative failure descriptions.
- **Sarah — revision feedback classifier:** Revision Mode now instructs Sarah to classify incoming feedback before revising: implementation-specific feedback routes to Colby's Factual Claims section; design-level feedback warrants ADR revision. Mixed feedback is separated before acting.

## [4.0.6] - 2026-04-22

### Fixed

- **Colby scoped-test enforcement:** `{test_single_command}` was never defined as a substitution variable, causing Colby to fall back to the full test suite during her own verification step. Step 5 of Build Mode now provides a concrete scoping algorithm: map each changed source file to its test counterpart by convention (`src/foo/bar.ts` → `tests/foo/bar.test.ts`, co-located `bar.spec.*`, etc.), run only those files explicitly, and skip with a DoD note when no test file exists. A new hard constraint (`**Scoped tests only**`) explicitly forbids running the full suite — that gate belongs to Eva's mechanical check between Colby-done and Poirot. Applied to `source/shared/agents/colby.md`, `.claude/agents/colby.md`, and `.cursor-plugin/agents/colby.md`.

## [4.0.5] - 2026-04-22

### Changed

- **`roz_qa` → `qa_status` field rename:** The `roz_qa` PIPELINE_STATUS JSON field and `ROZ_QA` shell variable in `enforce-sequencing.sh` have been renamed to `qa_status` and `QA_STATUS` respectively — a naming artifact left over from the Roz→Poirot rename in v4.0. All pipeline-orchestration doc references updated to match across `source/shared/`, `.claude/`, and `.cursor-plugin/` targets.
- **`roz_blocked` alias removal:** Removed the historical `roz_blocked` alias footnote from the `verification_blocked` enum row in pipeline-orchestration docs (`source/shared/rules/pipeline-orchestration.md` and `.claude/rules/pipeline-orchestration.md`).
- **Pipeline state label:** Renamed queued follow-up label "Roz strategy review" → "Test-authoring strategy review" in `docs/pipeline/pipeline-state.md`.

## [4.0.4] - 2026-04-22

### Changed

- **Sherlock (user-reported bug detective):** `maxTurns` raised from 40 to 80 to prevent truncation on deep bug hunts.
- **Sherlock narration suppressed:** investigation runs silent; the full case file is written to `docs/pipeline/last-case-file.md` via Bash heredoc, and Sherlock returns a one-line receipt to Eva (Poirot/Robert/Sable pattern now applied to Sherlock).
- **Eva user-bug relay step updated:** Eva reads `docs/pipeline/last-case-file.md` from disk, prepends "Case file below." and presents it to the user without commentary.
- **Observation masking table:** Sherlock receipt row added to the masking/relay table in `pipeline-orchestration` across all targets (source/shared, .claude, .cursor-plugin).
- **User guide:** `last-case-file.md` added to the State files table.
- **Cursor plugin mirror sync:** all three Sherlock changes (maxTurns, narration suppression, case-file-on-disk relay) propagated to `.cursor-plugin/` so Cursor users receive parity behavior.

## [4.0.3] - 2026-04-22

### Added

- **Session hygiene guidance (user guide):** New `### Session hygiene` subsection in the Context Management section covering three practices from Anthropic's Claude Code session management guidance: one task per session (context rot prevention), rewind-over-correction (double-Esc in Claude Code to drop failed context rather than explaining failure forward), and compact anchor (Eva writes current phase + key decisions to `context-brief.md` before compaction so the model retains pipeline direction).

### Changed

- **Context Cleanup Advisory (pipeline-orchestration.md):** Expanded from a single reactive sentence into a three-part protocol: new-task/new-session guidance, compact anchor writing requirement at major phase boundaries (after Colby DONE, after review juncture), and explicit trigger rules for when Eva proactively suggests `/compact` vs `/clear`.
- **context-brief.md template:** Added `## Compact Anchor` section so installed copies include the slot Eva writes to before compaction.
- **Cursor mirror parity:** `.cursor-plugin/rules/pipeline-orchestration.mdc` updated to match the Claude target (triple-target sync).

## [4.0.2] - 2026-04-21

### Changed

- Poirot (investigator): raised `maxTurns` to 80, silenced mid-investigation narration, restructured output so findings table is last, mandatory report write to `docs/pipeline/last-qa-report.md` via Bash heredoc.
- Robert (acceptance reviewer): silenced review narration, mandatory report write to `docs/pipeline/last-robert-review.md` via Bash heredoc.
- Sable (acceptance reviewer): silenced review narration, mandatory report write to `docs/pipeline/last-sable-review.md` via Bash heredoc.
- brain-extractor: silenced extraction narration — only emits final `[Brain]` prefix line.
- Distillator: silenced compression narration — text output reserved for final distillate only.
- Ellis: silenced git narration — output is commit hash confirmation only.

### Fixed

- `brain/start.sh` and `.cursor-plugin/plugin.json`: replaced `node_modules/` directory existence check with `node_modules/.package-lock.json` check to detect and recover from partial npm installs after plugin upgrades.

## [4.0.1] - 2026-04-21

### Changed

- Raised Colby agent `maxTurns` from 75 to 200 to prevent turn-limit cutoff on large pipeline runs.

## [4.0.0] - 2026-04-21

**BREAKING.** Major pipeline redesign driven by observed over-engineering in
the v3.x line: too many agents producing too many artifacts that other agents
skim rather than read, too much ceremony around tests that only repeat the
implementation in a different syntax, too much reflexive process. v4.0 trims
hard and moves the verification model from a pre-built-test contract to a
post-build exercised-behavior contract.

### Removed

- **Roz agent (deleted entirely).** The QA / test-authoring agent is gone.
  Pre-built test assertions (Roz-first TDD) are no longer part of the default
  flow. Tests are written by Colby when Sarah's ADR names a specific failure
  mode that would bite users if regressed, or when the user asks for one
  explicitly — never "for coverage" or "to document behavior."
- **Roz-specific enforcement hook** (`enforce-roz-paths.sh`) deleted from
  `source/claude/hooks/`, `.claude/hooks/`, and hook registration in
  `.claude/settings.json`.
- **`source/shared/references/retro-lessons.md`** deleted. Lesson 004
  (hung-process rule) migrates into Colby's persona as a durable constraint.
  The remaining lessons were either obsolete or cheaper to rediscover than to
  carry in context.
- **`source/shared/references/qa-checks.md`** deleted (Roz-specific; no
  v4.0 consumer).
- **`source/shared/pipeline/last-qa-report.md` template** and the live
  `docs/pipeline/last-qa-report.md` deleted. Poirot returns his verifier
  report directly to Eva in his invocation return — no persisted file.
- **~1200 structural pinning tests** deleted across `tests/adr-0014-telemetry/`,
  `tests/adr-0023-reduction/`, `tests/adr-0027/`, `tests/adr-0042/`,
  `tests/adr-0045/`, `tests/xml-prompt-structure/`, `tests/cursor-port/`,
  `tests/dashboard/`, and the top-level ADR pin tests. These asserted
  structural properties of source files (line counts, section orders, agent
  rosters, template counts) that burn tokens to run and catch nothing a human
  review wouldn't. ~500 behavioral tests kept: brain MCP, hook behavior,
  script behavior.
- **`Agent(roz, cal)` tool grants** removed from Colby. **`Agent(roz)`**
  removed from Cal/Sarah. Post-v4.0, neither Sarah nor Colby delegates via
  the Agent tool.

### Changed

- **Cal renamed to Sarah** (pronouns she/her) with a fundamentally different
  output contract. Sarah's ADRs are now 1-2 pages: `## Status`, `## Context`,
  `## Options Considered` (2-3 options in prose, one paragraph each),
  `## Decision`, `## Rationale`, `## Falsifiability`, `## Sources` (optional).
  No implementation manuals. No requirements tables with source citations.
  No verbatim replacement text for files Colby will edit. No test
  specifications. No wiring-coverage sections. Sarah decides; Colby
  implements; Poirot catches orphans. Persona at
  `source/shared/agents/sarah.md`.
- **Colby's Feedback Loop is now mandatory.** Every change must be exercised
  at least once before DoD: backend code runs with representative input,
  frontend code renders in the dev server (screenshot or browser MCP), hooks
  fire with test payloads, endpoints get called, CLIs get executed. A change
  that has not been executed is not done. Documented-but-unexercised wiring
  is a blocker. Persona at `source/shared/agents/colby.md`.
- **Poirot promoted to default post-build verifier.** Previously
  opt-in-on-request; now runs on every wave after the mechanical gate
  passes. Minimum findings dropped from 5 to 1-3 typical; zero findings with
  confidence is acceptable ("I exercised X, Y, Z; all behaved as the diff
  implies; no concerns.") The old minimum-5 rule produced padding. Poirot
  exercises the code where practical (hooks, endpoints, MCP tools, UI
  components) and reports what happened. Persona at
  `source/shared/agents/investigator.md`.
- **Mandatory Gate 1 is now the mechanical test gate**, not "Roz verifies
  every wave." Between Colby-done and Poirot invocation, Eva runs the
  project's declared test command from CLAUDE.md directly via Bash. Pass →
  Poirot. Fail → back to Colby with output. Eva is responsible for the test
  run, not a subagent.
- **Scout fan-out is sizing-gated.** `enforce-scout-swarm.sh` now skips
  Micro/Small pipelines entirely (scouts' ceremony cost exceeds their value
  at that scale) and enforces `<research-brief>`/`<colby-context>` blocks
  only on Medium/Large. Roz dropped from the case statement. Cal renamed to
  Sarah in the case statement. Error messages updated to say Sarah.
- **Stop-reason enum**: `roz_blocked` → `verification_blocked` (with
  `roz_blocked` kept as read-time alias for pre-v4.0 pipelines).
- **`CLAUDE.md`** rewrote Key Conventions and Pipeline Key Rules for the
  v4.0 agent roster (no Roz, Cal→Sarah) and verification model.
- **`docs/guide/user-guide.md`** and **`docs/guide/technical-reference.md`**
  updated for v4.0 agent roster, verification model, and scout sizing gate.

- **`pipeline-orchestration.md` shrunk from 43.7k → 24.9k chars.** JIT-only
  sections (investigation discipline, concurrent-session detection, state file
  descriptions, phase sizing rules, budget estimate gate, worktree-per-session
  protocol, telemetry capture) extracted to dedicated reference files:
  `pipeline-phases.md`, `worktree-isolation.md`, and `telemetry-metrics.md`.
  The always-loaded file now stays under the 40k performance threshold.
- **Effort ceiling lowered from `xhigh` → `high` pipeline-wide.** Per
  Anthropic tokenizer regression research (Claude 4.x ~1.35x code/JSON
  overhead), `xhigh` causes excessive context burn on production workloads
  without quality gain. Sarah drops from `xhigh` → `high`; Poirot's
  final-juncture promotion (high→xhigh) removed. Both `xhigh` and `max` are
  now forbidden (ceiling is `high`). Stale `retro-lessons.md` reference
  removed from `agent-preamble.md`; `/compact` context hygiene guidance added
  to `pipeline-operations.md`.

### Migration notes

Downstream projects installing atelier-pipeline pull a breaking change:
- `enforce-roz-paths.sh` hook no longer exists. Any project-local custom
  hook chain that depends on it must be updated.
- `Agent(roz, ...)` invocations in project-local custom agents will fail
  (agent doesn't exist). Replace with `Agent(poirot, ...)` where semantics
  map; otherwise remove.
- Projects relying on pre-built test contracts from Roz in their own
  workflows need to either (a) write tests themselves, (b) have Colby write
  them when Sarah's ADR names a failure mode, or (c) accept that Poirot's
  exercise-the-code pass replaces contract-style test authoring.
- Downstream `/debug` users: the command now routes to Sherlock-then-Colby
  rather than Roz-then-Colby. Same semantics for user-reported bugs.

### Rationale (research-cited)

Capture of the research that drove this redesign lives in the post-hoc ADR
(Sarah writes it after this release lands). Eva's auto-memory records the
observed patterns that prompted the trim: structural-pinning tests with
near-zero regression signal, Roz-first TDD producing "tests that describe
what Colby already did" rather than behavioral contracts, ADR steps
expanding into implementation manuals Colby skims and re-derives, scout
fan-out cost exceeding its value at small scale. This release is the
response.

## [3.41.0] - 2026-04-21

### Added

- **ADR-0045: Sherlock subagent** — New blind-investigator agent (`source/shared/agents/sherlock.md` + Claude/Cursor overlays + installed mirrors) dedicated to bug investigation. Sherlock owns the Investigation Mode block previously in Roz's persona, receives all user-reported bug work via Mandatory Gate 4 rewrite, and returns structured case files (symptom → evidence → root cause at `file:line`) without fixing anything. Roz returns to test authorship and QA-pass verification only.
- **ADR-0045 slice 4 — instruction-budget amputation**: Removed 5 slash commands (`debug`, `darwin`, `deps`, `create-agent`, `telemetry-hydrate` × 5 install locations), 2 agent personas (`darwin`, `deps` × 5 install locations), 3 skill directories (`skills/dashboard`, `skills/pipeline-overview`, `skills/load-design`), and 2 Cursor skill mirrors. Dropped `darwin_enabled` and `deps_agent_enabled` flags from `pipeline-config.json`. Agent roster, routing summary, no-skill-tool tables, and per-agent model table updated across all mirrors.
- **50-case pytest suite** `tests/adr-0045/test_adr_0045.py` covering Sherlock file presence, persona structure, route-table entries, deleted-artifact absence, and Mandatory Gate 4 content; most cases green.

### Changed

- **Mandatory Gate 4** (`pipeline-orchestration.md` + mirror): rewritten to route all user-reported bug investigation through Sherlock. Eva invokes Sherlock first; Sherlock returns case file; hard pause; user approves; Colby fixes; Roz verifies green.
- **Eva user-bug-flow protocol** (`default-persona.md` + mirror): updated to invoke Sherlock rather than routing directly to Roz/Colby.
- **`skills/pipeline-setup/SKILL.md`**: Step 1a folds design-system path detection; Steps 6d/6e/6f (darwin/deps/dashboard setup) removed and renumbered. Cursor mirror updated to match.
- **`skills/pipeline-uninstall/SKILL.md`**: darwin/deps references dropped.

## [3.40.0] - 2026-04-21

### Added

- **ADR-0044 instruction-budget trim slice 2 — new `source/shared/references/routing-detail.md` JIT reference**: AUTO-ROUTING intent matrix extracted from `agent-system.md` (286→240 lines, -46). Install mirrors at `.claude/references/routing-detail.md` (byte-identical per ADR §5) and `.cursor-plugin/rules/routing-detail.mdc`. Eva loads on-demand for edge-case routing; always-loaded cost drops.

### Changed

- **Mandatory Gates rhetoric collapse** (`pipeline-orchestration.md`): section opens with a `**Violation class.**` banner declaring severity class once; per-gate `"same class of violation as X"` refrain replaced with terse tags (`(default class)` or tighter-class parenthetical). All 12 gates preserved. ADR-0023 T_0023_131 strengthened to COUNT 12 gate headers (was: just assert the section header).
- **`default-persona.md`** now tells Eva to consult `routing-detail.md` for the full auto-routing matrix; the summary remains inline in `agent-system.md` routing block for quick reference.
- **Cursor `.mdc` mirrors resynced**: `.cursor-plugin/rules/agent-system.mdc` 378→246 lines matching Claude-side compression; `.cursor-plugin/rules/pipeline-orchestration.mdc` gained the same rhetoric collapse; new `.cursor-plugin/rules/routing-detail.mdc`. `skills/pipeline-setup/SKILL.md` Step 3c manifest includes the new JIT ref.
- **`docs/guide/technical-reference.md`** updated to match new Mandatory Gates rhetoric and Scout Fan-out prose.

> **Note:** pipeline-orchestration.md line-count reduction ended up smaller than the ~400-line target initially scoped in Issue #31 slice 2. Agent-system.md JIT move delivered the bulk of the always-loaded savings (~46 lines). ADR-0044 Addendum A1 documents the right-sized scope honestly. Future ADR may revisit.

## [3.39.0] - 2026-04-21

### Added

- **ADR-0043 (slice 1) — Agent Return Condensation**: One-line receipts for Cal/Colby/Roz `<output>` blocks. New `<preamble id="return-condensation">` in `agent-preamble.md` mandates summary + path-pointer returns and `file:line` citations across all producers. 37-case pytest suite (`tests/test_adr0043_output_contract.py`) green. Closes slice 1 of Issue #31; slices 2–4 remain open.
- **`skills/pipeline-setup/SKILL.md` Step 6g**: Offers `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` as Claude Code SendMessage prerequisite (GH anthropics/claude-code#42737). Cursor plugin-setup unchanged — flag is Claude Code-specific.

### Changed

- **ADR-0043 Addendum supersedes ADR-0040's Colby UI-contract design-system row** (moves to Colby `<workflow>`). `<slug>` → `{slug}` resolves ADR-0005 XML scanner conflict. "Skeleton" keyword retained for ADR-0023 compat.
- **Roz `<output>` one-liner drops "N suggestions"** — Roz persona never defined a Suggestions tier. Eva observation-masking row updated to `{N} BLOCKERs, {N} FIX-REQUIREDs` (phantom suggestions tier dropped).
- **Preamble rule 2 terminology normalized to `file:line`** (matches robert.md/sable.md). Preamble mandate sentence split for clarity.

> **Note:** CHANGELOG entries under 3.37.0 forward-referenced "ADR-0043" for Poirot path enforcement and Robert spec-gate work that shipped without an ADR file. ADR-0043 now canonically refers to Agent Return Condensation (this release).

## [3.38.0] - 2026-04-20

### Added

- `scripts/release.sh` utility that bumps all 5 version files (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json`, `.cursor-plugin/marketplace.json`, `.claude/.atelier-version`) in a single invocation given a canonical semver argument (no leading zeros, no pre-release/build metadata, no `v` prefix), and `tests/scripts/test_release.py` covering happy path, non-canonical-input rejection (parametrized across 9 cases: leading zeros, pre-release, build metadata, `v`-prefix, truncated, over-component, empty, whitespace, plain non-semver), and a nested-version-key pin test. The script validates semver, refuses missing args, is idempotent, and deliberately does NOT commit/tag/push — it prints a next-steps checklist instead. Not atomic: four independent `sed` calls followed by one plain-text overwrite; a mid-run failure leaves earlier files already mutated, and the operator must re-run. Acceptable for a hand-run release utility.

### Fixed

- `.claude-plugin/marketplace.json` was stale at 3.34.0 while other version files were at 3.37.0, blocking Claude Code marketplace installs of 3.35–3.37. Now synced.
- Roz `effort` was `high` in installed `.claude/agents/roz.md`, inconsistent with `medium` in the source template and with `pipeline-models.md` Tier 3 baseline. Installed file brought back into alignment.
- Roz `maxTurns` raised 15 → 50 (`.claude/agents/roz.md`, `source/claude/agents/roz.frontmatter.yml`, `source/cursor/agents/roz.frontmatter.yml`). Roz was truncating mid-generation on tool-heavy QA runs; 50 matches peer-agent ceiling range.

## [3.37.0] - 2026-04-20

### Added

- **ADR-0043: Gate 0b — Investigator/Poirot worktree path enforcement** — New PreToolUse guard blocks `investigator` subagent invocations that do not reference the active `worktree_path` from PIPELINE_STATUS. Prevents Poirot from reading files in the main repository instead of the session worktree, which caused false-positive and false-negative findings. Fails open when no `worktree_path` is present in state (no active pipeline). Implemented in `enforce-sequencing.sh` as Gate 0b, before all other gates.

### Fixed

- **ADR-0043: Gate 5 amendment — Robert requirement conditional on product spec existence** — Gate 5 (Robert must review on Medium/Large pipelines at the review juncture) previously blocked Ellis on all Medium/Large pipelines regardless of whether a product spec existed. For pipeline-internal changes (hook guards, orchestration fixes, infrastructure) with no `docs/product/*.md` files, Robert was reviewing Eva's own rubric — circular and incorrect. Gate 5 now reads `product_specs_dir` from `pipeline-config.json` and counts spec files with `-maxdepth 1` (direct children only; excludes README.md and archived specs in subdirectories). Zero spec files → Ellis proceeds without Robert.

## [3.36.0] - 2026-04-20

### Added

- **ADR-0042: Scout Synthesis Layer and Model/Effort Tier Corrections** — Adds a Sonnet/low synthesis step between haiku scouts and the primary agent (Cal, Colby, Roz) on Medium+ pipelines. Synthesis filters/ranks/trims raw scout output into a compact per-agent brief (`<research-brief>` for Cal, `<colby-context>` for Colby, `<qa-evidence>` for Roz). Synthesis does NOT form opinions — it emits data, not judgment. Addresses Roz context exhaustion on medium+ waves by preserving `file:line` evidence while dropping full-file dumps. Eva MUST spawn scouts and synthesis as separate parallel subagents; in-thread collection silently bypasses the scout-swarm hook. The existing `enforce-scout-swarm.sh` hook is unchanged — synthesis output populates the same named blocks the hook already guards.

### Changed

- **Per-Agent Assignment Table rewritten** (supersedes portions of ADR-0041):
  - Roz effort: `high` → `medium` (coverage-oriented verification; bounded adaptive thinking)
  - Robert (acceptance) model: `opus` → `sonnet` (structured spec-vs-implementation review)
  - Sable (acceptance) model: `opus` → `sonnet` (structured UX-vs-implementation review)
  - Sentinel effort: `medium` → `low` (pattern-matching over Semgrep output; prevents false-positive inflation)
  - Deps model: `opus` → `sonnet` (version diff + CVE lookup)
  - Ellis model: `haiku` → `sonnet` (Haiku mis-applies Conventional Commits)
  - Distillator model: `haiku` → `sonnet` (Haiku drops load-bearing facts)
  - brain-extractor model: `haiku` → `sonnet` (Sonnet/low less error-prone on SubagentStop payload extraction)
  - Synthesis (new row): Tier 2, `sonnet`, `low`
- **Promotion Signals reduced to 3 rows** (supersedes portions of ADR-0041):
  - Removed: "Auth/security/crypto files touched" (wrong lever — route to Sentinel at review juncture, do not promote generalist effort)
  - Removed: "Pipeline sizing = Large" (more files != more per-step deliberation; size is a tier-picker, not a model-setter)
  - Removed: "New module / service creation" (subsumed under Cal's `xhigh` base and Colby's `high` adaptive thinking)
  - Kept: Poirot final-juncture +1, read-only evidence -1, mechanical task -1
- **`max` effort explicitly forbidden** — Enforcement Rule 5 added to `pipeline-models.md`. Per Anthropic's Opus 4.7 adaptive-thinking guidance, `max` is evaluation-only (prone to overthinking, degraded on production workloads). Ceiling is `xhigh`.
- **Agatha Tier 1 runtime override removed** — Agatha is always Tier 2 (`opus`, `medium`). The ADR-0041 "reference docs → runtime Haiku/low" row was not mechanically enforceable; runtime discretion is exactly what ADR-0009 forbids.
- **`docs/guide/technical-reference.md` §Model Selection** — Agent Table updated to reflect Robert/Sable (Sonnet), Roz (medium), Sentinel (low), Ellis/Distillator/brain-extractor (Sonnet), Agatha (always Tier 2); Promotion Signals table trimmed; Synthesis row added; adaptive-thinking rationale paragraph added.
- **`docs/guide/user-guide.md`** — "lightweight Haiku extractor" updated to "lightweight Sonnet extractor" for the brain-extractor description.

## [3.35.0] - 2026-04-17

### Fixed

- **`.mcp.json` blank-file regression** — Cleanup steps in `brain-setup` and `pipeline-setup` now use an atomic Python one-liner that removes the `atelier-brain` entry and deletes the file in a single execution block if `mcpServers` becomes empty. Eliminates the recurring `{"mcpServers": {}}` ghost file that suppressed plugin MCP registration on next session start. A safety-net check runs after primary cleanup; destructive `|| rm -f` fallback removed (would delete valid files on Python failure). Added `.mcp.json` to `.gitignore`. New tests T-0019-140/141/142 guard the invariant.

- **Bash 3.2 hook compatibility** — Eight `enforce-*-paths.sh` hook scripts used `${VAR,,}` (bash 4+ lowercase operator) which exits code 1 on macOS's default `/bin/bash` (3.2). With `set -uo pipefail`, this caused hooks to silently fail instead of blocking. Replaced with POSIX-portable `$(echo "$VAR" | tr '[:upper:]' '[:lower:]')`.

- **`log-stop-failure.sh` raw-payload fallback** — Removed a fallback that replaced the `"unknown"` default with the full raw payload string when input was not valid JSON. The `extract_field` function's `"unknown"` default is now authoritative.

- **`cal.md` brain instruction** — Removed a direct `agent_search` call instruction from Cal's brain context section (violates ADR-0005-103 mechanical enforcement). Cal now uses brain context injected by Eva via the `<brain-context>` tag.

- **`colby.md` HTML tags in UI Contract table** — Replaced raw `<select>`, `<input>`, `<button>` HTML tags in colby.md's UI Contract table with backtick notation to prevent XML prompt schema validation failures.

### Tests

- Removed 8 stale line-count limit tests from `test_reduction_structural.py` (T-0023-020/030/040/053/058/080/130/150) — limits set in 2023, legitimately exceeded by subsequent ADRs.
- Updated `test_brain_wiring.py` T-0021-088: removed Sonnet from approved model tier assertion (eliminated in ADR-0041).
- Updated `test_adr0040_design_system.py` T-0040-026b: assertion now checks for Eva-injected brain context pattern instead of direct `agent_search` call.
- Removed 2 stale step-ordering tests from `test_deps_structural.py` (T-0015-051/064) — brain cleanup moved to Step 0 in prior releases.

## [3.34.0] - 2026-04-16

### Added

- **ADR-0041: Effort-Per-Agent Map (Task-Class Tier Model)** — Replaces the size-dependent model tables and 13-signal universal scope classifier with a 4-tier task-class model. Tier 1 (mechanical) uses Haiku at `low` effort; Tiers 2-4 use Opus at `medium`/`high`/`xhigh` respectively. Model now follows task class, not agent identity — a single agent can occupy different tiers across runs (Colby first-build Medium is Tier 3; Colby rework is Tier 2). Pipeline sizing becomes a tier-picker signal, not a model-setter. Priority stack is accuracy > speed > cost; Sonnet is eliminated from reasoning tiers. Effort promotion is capped at one rung per invocation (floor `low`, ceiling `xhigh`). Cal defaults to `xhigh` for architectural deliberation; Sentinel, Ellis, and Distillator are effort-demoted because excess thinking tokens reduce accuracy or add no value on pattern-matching / mechanical work.

- **Claude Code >= 2.1.89 compatibility note** — `effort` frontmatter field requires Claude Code 2.1.89 or newer. `pipeline-setup` emits a non-blocking warning on older versions; installation continues but agents run at Claude Code's default effort until the upgrade. Cursor does not consume the `effort` field today but frontmatter values are kept in sync for forward compatibility.

### Changed

- **`source/shared/rules/pipeline-models.md` fully replaced** — three new `<model-table>` blocks (`task-class-tiers`, `promotion-signals`, `agent-assignments`) plus a retained enforcement gate. Size-dependent and base-model tables, Agatha-model table, the universal scope classifier, and the brain-integration scoring bonus are removed. `.claude/rules/pipeline-models.md` and `.cursor-plugin/rules/pipeline-models.mdc` mirrors updated in lockstep.
- **30 frontmatter files aligned to the new tier table** — 15 Claude + 15 Cursor agent frontmatter overlays now carry `model:` and `effort:` values matching the Per-Agent Assignment Table. `brain-extractor.frontmatter.yml` gains an `effort: low` field (previously absent).
- **`docs/guide/technical-reference.md` §Model Selection** — rewritten to describe the 4-tier model and promotion signals; stale "universal scope classifier" references removed.
- **`docs/guide/user-guide.md`** — model-selection passage updated to cite tier + effort framing.
- **`source/shared/references/telemetry-metrics.md`** — `claude-opus-4-7` pricing row added (1.17x midpoint tokenizer inflation); Per-Invocation Cost Estimates table updated to reflect Opus-default for review/acceptance agents with a legacy annotation on the Sonnet row; ADR-0041 footnote cites the tier epoch.

## [3.33.0] - 2026-04-16

### Added

- **ADR-0040: Design System Auto-Loading** — Sable and Colby now auto-detect a `design-system/` directory at the project root and load relevant files before generating UI. `tokens.md` loads always; domain files (components, navigation, data-viz, layouts) load selectively based on what is being built. No config required for the happy path. A `/load-design` skill handles external or shared design systems via an override path in `pipeline-config.json`. SVG icon assets are referenced directly — no format conversion. Design system context propagates from Sable to Colby via Eva's `<read>` tag (not `<constraints>`), consistent with retro lessons 005/006 on cross-agent context boundary failures.

- **Cal mandatory institutional memory search** — Cal now performs a mandatory brain/retro search before designing any ADR. Brain available: calls `agent_search` for prior decisions, lessons, and ADRs on the same domain. Brain unavailable: reads `retro-lessons.md` and greps existing ADRs. Findings populate the DoR "Retro risks" field. Step is unconditional — silence is not a valid finding. Closes the structural gap where Cal designed without the project's own retro history (which produced the correctable `<constraints>` vs `<read>` error in the same session).

## [3.32.2] - 2026-04-15

### Fixed

- **Scout step missing from auto-routing table** — Six subagent routing rows (Roz and Colby invocations) were missing the scout fan-out step and required evidence block annotation. Eva's always-loaded context now shows `Scout fan-out →` and the required `[<block-name>]` inline for every hooked agent route, eliminating the pattern where Eva would route directly to Roz or Colby without first running scouts, causing the `enforce-scout-swarm.sh` hook to block the invocation.

## [3.32.1] - 2026-04-15

### Fixed

- **Brain MCP server not registered on install** — `mcpServers` field was missing from `plugin.json`. Pipeline-setup Step 0d and brain-setup Step 0 both removed the legacy project-level `.mcp.json` entry ("now managed by plugin") but `plugin.json` was never updated with the replacement. Brain silently ran in baseline mode on all new installs since the migration. Users must run `claude plugin update` to pick up this fix.
- **Worktree creation skipped on Small pipelines** — Ambiguous language in `pipeline-orchestration.md` ("Every pipeline session *that creates a branch*...") gave Eva an escape hatch to skip worktree creation for Small and Micro pipelines. Now reads "Every pipeline session gets a dedicated git worktree, regardless of sizing." Clarifier added after the branch sizing table.

## [3.32.0] - 2026-04-14

### Added

- **ADR-0039: Frontend Layout Physics Policy** — Three systemic pipeline failures fixed: (1) Roz's test authoring read list now includes UX doc (information chain gap); (2) Cal's UI Specification table requires layout context for constrained-container components; (3) Roz's Test Authoring Mode adds layout primitive principle (toBeVisible over toBeInTheDocument); (4) Poirot and Roz now trace constant-indirected API routes (not just raw string grep); (5) Retro lesson 006 added covering all three failure modes

## [3.31.7] - 2026-04-14

### Changed

- **pipeline-setup:** On install, existing `CLAUDE.md` is now renamed to `CLAUDE.md.orig` and a fresh `CLAUDE.md` is written — project-specific content (tech stack, test commands, conventions) is carried forward; pipeline-owned sections (agent behavior, commit workflow, QA process) are dropped. User's original file is never lost.

## [3.31.6] - 2026-04-14

### Fixed

- **error-patterns.md capture:** StopFailure hook now tries multiple field name candidates (stop_reason, reason, error) before falling back to raw payload capture — eliminates "unknown/unknown" entries that made Eva's WARN injection loop non-functional

### Improved

- **Colby engineer:** Four stopping constraints added — run tests once, 50 tool call hard stop, no node_modules spelunking, 3-command git archaeology cap
- **Roz invocation template:** unit-qa and wave-sweep mode signals documented in roz-code-qa template so Eva correctly gates Tier 2 checks per mode

## [3.31.5] - 2026-04-14

### Improved

- **Cal architect agent:** Reduce maxTurns from 80 to 45 — turn budget now reflects actual ADR production cost rather than worst-case exploration
- **Cal architect agent:** Exploration constraint — prefer invocation context, limit self-directed reads to 8 files targeted at specific integration points; proceed with best available information rather than stopping mid-ADR
- **Cal architect agent:** Roz test spec review loop capped at 2 rounds — unresolved findings after 2 rounds surface to Eva rather than looping indefinitely

## [3.31.4] - 2026-04-14

### Fixed

- **Windows compatibility:** All 8 enforcement hooks now correctly strip Windows absolute paths before enforcing agent write restrictions — drive letter casing mismatches (`C:` vs `c:`) and backslash/forward-slash inconsistencies no longer cause false BLOCKED errors on legitimate writes

## [3.31.3] - 2026-04-14

### Improved

- **Roz QA agent:** Reduce maxTurns from 60 to 15 — hard cap on worst-case run time
- **Roz QA agent:** Add four stopping constraints — no node_modules spelunking, run tests once, 3-command git archaeology cap, 15 tool call hard stop
- **Roz QA agent:** Scoped Re-run mode now explicitly exempt from agent-preamble DoR/DoD ceremony
- **QA checks:** Remove Tier 2 checks 13 (Exploratory), 14 (Semantic Correctness), 16 (State machine completeness), 17 (Silent failure audit) — speculative checks that added time without catching bugs
- **QA checks:** Fix wiring verification guard — now triggers on any new API endpoint in the diff regardless of FE presence; missing frontend wiring is a BLOCKER
- **QA checks:** unit-qa mode now gates Tier 2 to checks 8 (Security) and 11 (Dependencies) only

## [3.31.2] - 2026-04-14

### Fixed

- **brain MCP server:** Restore missing `.mcp.json` at plugin root — accidentally deleted in 3.31.1 cleanup, causing brain MCP server to never register on user installs

## [3.31.1] - 2026-04-13

### Fixed

- **pipeline-setup:** Auto-remove stale project-level `atelier-brain` .mcp.json entries (now managed by plugin)

## [3.31.0] - 2026-04-13

### Fixed

- **brain MCP server:** Changed 8 `console.log` calls to `console.error` in `server.mjs` to prevent stdout corruption of JSON-RPC stdio transport. Logs now properly route to stderr, preserving JSON-RPC message integrity on stdout.

## [3.30.7] - 2026-04-13

### Fixed

- **brain-setup SKILL.md:** Step 0 migration protocol removes stale `atelier-brain` entries from project `.mcp.json` files, fixing `ERR_MODULE_NOT_FOUND` crashes on fresh checkouts.
- **brain MCP server self-locating:** `start.sh` now self-locates with environment fallbacks; `server.mjs` sets `NODE_TLS_REJECT_UNAUTHORIZED` at module level; `.mcp.json` delegates to start.sh for zero-config operation.

## [3.30.6] - 2026-04-13

### Fixed

- **brain-setup SKILL.md:** Step 0 migration protocol removes stale `atelier-brain` entries from project `.mcp.json` files, fixing `ERR_MODULE_NOT_FOUND` crashes on fresh checkouts.
- **brain MCP server self-locating:** `start.sh` now self-locates with environment fallbacks; `server.mjs` sets `NODE_TLS_REJECT_UNAUTHORIZED` at module level; `.mcp.json` delegates to start.sh for zero-config operation.

## [3.30.5] - 2026-04-12

### Fixed

- **dashboard.html:** Fix SyntaxError that caused the dashboard to show blank. A `*/` inside a JSDoc block comment example (`/* trusted: <reason> */`) prematurely closed the outer `/**` comment; the trailing backtick then opened an unterminated template literal that silently consumed the entire 900-line script. Fixed by adding a space: `* /`.

## [3.30.4] - 2026-04-12

### Fixed

- **rest-api.mjs:** Guard `rework_rate` and `first_pass_qa_rate` casts against non-numeric legacy values. Historical T3 captures stored non-numeric strings ("low", "1.0 cycles/unit") that caused PostgreSQL cast errors blanking the entire dashboard `/api/telemetry/agents` endpoint. Replaced bare `::numeric` casts with `CASE WHEN ~ regex ELSE NULL END` guards to safely skip non-numeric rows.

## [3.30.3] - 2026-04-12

### Fixed

- **telemetry-hydrate.md:** Always use `${CLAUDE_PLUGIN_ROOT}/brain/scripts/hydrate-telemetry.mjs` for script path. Removed broken relative-path fallback that resolved to target project directory (which has no brain/ subdirectory), causing "Cannot find module" crashes. Added clear error message when `CLAUDE_PLUGIN_ROOT` is unset. Removed stale `session-hydrate.sh` reference (no-op since ADR-0034).

## [3.30.2] - 2026-04-12

### Fixed

- **check-updates.sh:** Fixed three bugs in update detection. (1) Source path was `source/{dir}/` instead of `source/shared/{dir}/` — update detection has been broken since the source directory restructure. (2) Hooks directory was never checked — hook-lib.sh shipped broken to users silently. (3) Glob was `*.md` only, excluding .sh and .json hook files. Future hook updates will now be properly detected and users will be prompted to re-run /pipeline-setup.

## [3.30.1] - 2026-04-12

### Fixed

- Consolidated hotfix: Applied 3.29.1 hook dependency corrections and prepared release pipeline.

## [3.29.1] - 2026-04-12

### Fixed

- **pipeline-setup Step 3a install table:** Added `hook-lib.sh` and `pipeline-state-path.sh` to hook dependency copy list. Both files existed in `source/shared/hooks/` but were absent from the install table, causing 11 dependent hooks to silently degrade on fresh installs.

## [3.29.0] - 2026-04-12

### Added

#### ADR-0035: Session State Isolation Wiring (Wave 4)

- **Hydrate-telemetry auto-resolve:** Decoupled session boot from active telemetry collection. `hydrate-telemetry.mjs` now auto-resolves brain URL from `~/.atelier/config.json` when started without parameters. SessionStart hook no longer requires explicit `CLAUDE_BRAIN_URL` propagation; enables background hydration on fresh checkouts and concurrent session recovery.
- **Consumer path placeholders:** Cal/Colby/Roz consumer agents now resolve `{session_state_dir}` and `{claude_project_dir}` placeholders in read-list invocations, enabling session-isolated pipeline state reads. Eliminates per-project path hardcoding.
- **Concurrent-session protocol:** Multiple Claude Code instances on the same project can now run independent pipelines without state collision. Each session gets its own `pipeline-state.md` via `$CLAUDE_SESSION_ID` environment variable. Pipeline files are session-scoped; no merge conflicts. Session recovery handler reads only the current session's state on boot.
- **S4 Ellis hook resolution:** Ellis commit and push operations now resolve through session state directory helpers. Enables multi-session parallel commits without race conditions.

#### ADR-0036: Documentation Sweep (Wave 5)

- **7 gauntlet R14 gaps closed:**
  1. **Triple-source assembly:** Clarified `source/shared/` → `source/claude/` → `.claude/` template assembly pipeline in CLAUDE.md, with per-layer responsibility breakdown.
  2. **REST auth + endpoints:** Brain HTTP API authentication documented; endpoint signatures (GET /search, POST /capture, GET /hydrate-status) formalized in `technical-reference.md`.
  3. **Migration runner:** Brain schema migration execution flow (file-loop runner, idempotent `schema_migrations` tracking) formally specified in ADR-0034 trace.
  4. **Hook procedure:** All 20 hook lifecycle events (SessionStart, PreToolUse, AgentStart, AgentStop, etc.) cross-referenced with `.claude/hooks/` implementations. Behavior matrix added to `hook-procedure.md`.
  5. **Gauntlet audit:** Complete ADR index (ADR-0001 through ADR-0037) with summaries, status (accepted/superseded), and cross-references added to `docs/architecture/adr/`.
  6. **ADR index expansion:** 13 → 37 ADRs tracked; all prior ADRs indexed and backlinked.
  7. **Cross-references:** Agent personas now reference ADRs that ground their behavior (e.g., Colby references ADR-0018 for Wave-based build; Roz references ADR-0016 for Wave-based QA).

#### ADR-0037: Dashboard a11y + Product Specs (Wave 6)

- **Dashboard WCAG 2.1 AA:** Modal dialogs now trap focus, escape-to-close handlers, keyboard-navigable search/filter, loading spinners announce to screen readers via `aria-label`, table column headers have `scope="col"`, agent-selector button has `aria-expanded`. Tested with axe-core against 16 UI patterns.
- **5 product specs:** Cursor plugin integration (session-boot parity), brain persistence mode selection (in-memory vs. database), agent-teams feature (parallel Colby builds), model assignment per-pipeline (cost optimization), token-budget gates for Large pipelines.
- **Cursor session-boot parity:** `.cursor-plugin/hooks/session-boot.sh` now matches Claude Code's flow: brain dependency check, Atelier Hydrate MCP call, settings.json permissions pre-approval. Cursor plugin automatically synced with Claude plugin at release.

## [3.28.0] - 2026-04-12

### Added

#### ADR-0033: Hook Enforcement Audit Fixes (Waves 1–2)

- **Wave 1 — Enforcement Gap Closure (5 critical fixes):** Resolved C1 (brain-extractor tool allowlisting), M1 (scout-swarm reactivation), M2 (session-boot sync), M3 (post-compact reinject), and m1–m5 mechanical fixes (cal/roz path validation, prompt-brain-prefetch retry logic, enforce-eva-paths subagent bypass). 
- **Comprehensive Test Suite:** 30 test cases across 7 new test files covering enforcement config parsing, hook path validation, retro-lesson injection, and brain-extractor tool lifecycle.
  - tests/hooks/test_session_boot.py (7 cases)
  - tests/hooks/test_session_boot_sync.py (2 cases)
  - tests/hooks/test_enforce_colby_paths.py (5 cases)
  - tests/hooks/test_enforce_cal_paths.py (4 cases)
  - tests/hooks/test_pipeline_setup_skill.py (8 cases)
  - Expanded test_enforce_scout_swarm.py with 5 additional cases
  - Poirot blind review validation tests
- **Wave 2 — SKILL.md Surgical Edits:** C2 enforcement-scout-swarm hook added to manifest and Agent hook configuration. M4 session-hydrate.sh documented as intentional no-op with cleanup tasks. Expanded brain-extractor if-condition to cover 9 agent types, unlocking capture for Agatha/Colby/Roz/Poirot/Distillator/Sentinel/Deps/Darwin. All 30 tests passing.

#### ADR-0034: Brain Correctness Hardening (Waves 1–3)

- **Wave 1 — Brain Enum Extension:** Fixed critical M1+M9 enum drift — SOURCE_AGENTS and SOURCE_PHASES enums extended to include 6 missing agents (brain-extractor, investigator, sentinel, deps, darwin, distillator) and 3 missing phases (ci-watch, devops, telemetry). Previously these agent captures were silently dropped. Migration 008 patches existing database schema.
- **Wave 1 — ADR-0032 Implementation:** Introduced `pipeline-state-path.sh` helper to replace hardcoded session-boot.sh path logic, enabling per-project pipeline state isolation and recovery. Updated enforce-eva-paths.sh and enforce-roz-paths.sh to allow ~/.atelier/pipeline writes (brain config directory).
- **Wave 2 — Hook Library Extraction:** Extracted 6 reusable functions into `source/shared/hooks/hook-lib.sh` (hook_lib_pipeline_status_field, hook_lib_json_escape, hook_lib_get_agent_type, hook_lib_assert_agent_type, hook_lib_emit_deny, hook_lib_emit_allow). Rewired all 11 Claude hooks to source this library, reducing duplication.
- **Wave 2 — Migration Infrastructure:** Replaced 144-line hardcoded migration runner with generic file-loop runner in brain/lib/db.mjs. Introduced schema_migrations tracking table to persist applied migration IDs, enabling idempotent re-runs and safe schema evolution.
- **Wave 2 — Poirot Code Review Fixes:** enforce-roz-paths.sh traversal check moved before exception glob. Parameterized all SQL queries in brain/lib/db.mjs. brain-extractor.md agent documentation corrected. prompt-compact-advisory.sh migrated to session_state_dir() pattern.
- **Wave 3 — Brain Correctness Fixes (4 features):**
  1. **Graceful pool shutdown with async drain:** Database pool closes cleanly on shutdown (EPIPE, SIGTERM, stdin EOF) with 3-second deadman timeout via `Promise.race([poolEnd(), deadmanPromise])` in `brain/lib/crash-guards.mjs`.
  2. **LLM response null-guard module:** New `brain/lib/llm-response.mjs` provides `assertLlmContent(data, context)` for safe extraction of chat-completion responses, preventing TypeErrors from malformed data (null data, empty choices, missing message/content).
  3. **XSS escaping in dashboard:** All dynamic content in `brain/ui/dashboard.html` now HTML-escaped before `innerHTML` insertion using `escapeHtml()`, covering ~40+ call sites (agent names, metrics, timestamps, metadata). Prevents script injection through brain metadata.
  4. **CORS headers for HTTP REST API:** Brain server sets `Access-Control-Allow-Origin: http://localhost:PORT`, `Access-Control-Allow-Headers: Content-Type, Authorization, mcp-session-id`, `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`. Enables localhost dashboard and tools to make cross-origin REST requests.

- **Test Coverage:** ADR-0034 adds 29 new hook tests (hook-lib, path enforcement, session-hydrate, migration runner) and 3 new brain test suites (crash-guards.test.mjs, dashboard-xss.test.mjs, llm-response.test.mjs). Total: 186 tests across brain + hooks, 0 failures. Updated mock-pool.mjs for parameterized query support; conftest.py enhanced for hook-lib isolation testing.

## [3.27.5] - 2026-04-10

### Fixed
- **brain-extractor silent capture failure:** `agent_capture` was absent from the brain-extractor agent's `tools` allowlist, causing every MCP call to be silently blocked. The agent's own "brain unavailable → exit cleanly" fallback masked the failure — captures appeared to succeed but nothing landed in the brain. Adding `agent_capture` to the allowlist restores automatic post-agent knowledge extraction for cal, colby, roz, and agatha.
- **brain-setup missing permissions pre-approval:** Brain-setup now adds all 8 atelier-brain MCP tools to `permissions.allow` in `.claude/settings.json` during setup (Path A interactive, Path B silent). Prevents per-call approval prompts and ensures background hook agents like brain-extractor are not silently blocked by the tool permission gate.
- **Node brain tests fail on clean checkout:** `test_T_0024_049_brain_node_test_suite_passes` now runs `npm ci` in `brain/` before invoking `node --test`. Previously, the test assumed `node_modules` was present; a fresh clone without pre-installed deps would fail with `ERR_MODULE_NOT_FOUND`.

### Changed
- **ADR-0023 line cap compliance restored:** `source/shared/agents/darwin.md` compressed from 134 to 100 lines; `source/shared/rules/pipeline-orchestration.md` compressed from 759 to 647 lines. Both were above their ADR-0023 structural caps due to content added after the reduction target was set.

## [3.27.4] - 2026-04-09

### Added
- **Atelier Hydrate Status MCP Tool:** New `atelier_hydrate_status` tool (Tool 8) returns completion state (running/completed/error/idle), file counts (processed, skipped, thoughts_inserted), errors array, and timestamps for a previous `atelier_hydrate` call. Enables non-blocking async hydration monitoring without polling the shell.

## [3.27.3] - 2026-04-09

### Added
- **Atelier Hydrate MCP Tool:** New `atelier_hydrate` tool enables non-blocking JSONL telemetry hydration through the brain server's existing database connection. Replaces the standalone `hydrate-telemetry.mjs` script path that could not reliably resolve credentials in all environments. Called automatically from SessionStart hook; available on-demand via MCP interface.
- **Scout Swarm Evidence Enforcement:** New `enforce-scout-swarm.sh` PreToolUse hook blocks Cal/Roz/Colby Agent invocations that lack required evidence blocks (research-brief for Cal; debug-evidence for Roz; qa-evidence for Colby). Respects micro/small pipeline skip conditions. Ensures high-context invocations and prevents orphan agent calls.

### Changed
- **Brain Hydration Refactoring:** Extracted hydration logic into shared `brain/lib/hydrate.mjs` module for reuse by both `hydrate-telemetry.mjs` (offline) and `atelier_hydrate` MCP tool (online). Improves consistency and maintainability.
- **Session Boot Simplification:** `session-hydrate.sh` now exits immediately; hydration responsibility transferred to `atelier_hydrate` MCP tool invoked at session boot. Eliminates shell script race conditions and credential resolution issues.

## [3.27.2] - 2026-04-08

### Fixed
- **Test failure blocking behavior:** Colby's build DoD now explicitly runs the full test suite (not scoped to changed files) and requires pre-existing failures to be fixed before handoff. Roz constraint now treats all failing tests as blockers regardless of who introduced them. Updated retro-lesson 001 to scope "flag pre-existing issues" guidance to security checks only, not test failures. Ensures no agent can dismiss pre-existing test failures as out-of-scope.

## [3.27.1] - 2026-04-07

### Fixed
- **Classifier gap on codebase investigation tasks:** `Explore` agent was missing from the pipeline-models.md base-models table, causing the universal scope classifier to promote read-only codebase surveys (security mapping, architecture reviews) to Opus via the auth/security signal (+2) and file-count signal (+2). Added `Explore` as Haiku, classifier-exempt (like Distillator). Added `-3` scoring signal for read-only codebase scans to mechanically demote pure survey tasks. Added auto-routing intent row for "scan the codebase" to route to Explore+haiku scouts → Sonnet reviewer. Added compact `codebase-investigation` invocation template.

## [3.27.0] - 2026-04-07

### Added
- **Permission Audit Trail (ADR-0031):** All 10 enforce-*.sh PreToolUse hooks now emit structured JSONL enforcement records to `~/.claude/logs/enforcement-YYYY-MM-DD.jsonl` on both block and allow decisions. Fields: timestamp, tool_name, agent_type, decision, reason, hook_name. A new `session-hydrate-enforcement.sh` script (called from `session-hydrate.sh`) bulk-captures blocked events to the brain at session end as `thought_type: 'insight'` with `metadata.enforcement_event: true`. Fail-open: log write failures and brain unavailability are silent. Allowed events log to file only (not brain-captured).
- **Token Exposure Probe (ADR-0030, Branch 2b):** Confirmed that the Claude Code Agent tool does not expose `input_tokens`/`output_tokens` split in real-time Agent tool result metadata (768 records examined). `total_tokens` is present but insufficient for cost computation. Gap documented in `telemetry-metrics.md`. Live accumulator (Track B) deferred. Note: full input/output split is available post-hoc in subagent JSONL files, which `hydrate-telemetry.mjs` already reads.

## [3.26.0] - 2026-04-07

### Added
- **Named Stop Reason Taxonomy (ADR-0028):** Every terminal pipeline transition now writes a `stop_reason` field to `pipeline-state.md` from a closed 10-value enum: `completed_clean`, `completed_with_warnings`, `roz_blocked`, `user_cancelled`, `hook_violation`, `budget_threshold_reached`, `brain_unavailable`, `session_crashed`, `scope_changed`, `legacy_unknown` (read-only inference for upgrade safety). T3 telemetry includes `stop_reason`; Darwin can filter pipeline history by stop reason. Upgrade safety: absent field infers `legacy_unknown` on read, stale pipelines infer `session_crashed` at boot.
- **Token Budget Estimate Gate — Track A (ADR-0029):** Eva now shows a heuristic cost estimate before Large pipelines (always) and Medium pipelines (when `token_budget_warning_threshold` is configured). Estimate based on sizing tier, agent roster, and step count when known. Hard pause fires before the first agent invocation; Large prompt includes a "downsize to Medium" option. Estimate labeled "order-of-magnitude — not billing." New `token_budget_warning_threshold` field in `pipeline-config.json` (type: number | null, default: null). T3 telemetry captures `budget_estimate_low` and `budget_estimate_high` for post-hoc accuracy analysis.

## [3.25.5] - 2026-04-07

### Added
- brain-extractor now emits `[Brain]` prefixed status lines after each agent completes, distinguishing brain output from agent prose in the conversation
- session-boot.sh added to source/claude/hooks/ (was missing source counterpart despite being installed)

### Changed
- Colby and Ellis can now write to `.github/` and `scripts/` — removed from enforce-colby-paths.sh blocked list
- Test suite fully migrated from `.claude/` to `source/` (source is the canonical truth, not the installed copy)

### Fixed
- Roz Investigation Mode now explicitly handles pre-collected `debug-evidence` blocks from Eva's scout swarm
- Removed 8 dead skip stubs: 3 retired Ellis enforcement behaviors, 2 pre-ADR-0016 darwin-not-in-core assertions, 1 bats stub, 2 ADR-0023 removed-behavior assertions
- Enabled 3 previously-skipped tests now that ADR-0023 is complete: 6-tag persona schema check, identity pronouns check, no-Brain-Access-heading check
- PERSONA_TAGS updated to 6-tag schema (removed `tools` tag moved to frontmatter per ADR-0023)

## [3.25.4] - 2026-04-07

### Added
- **brain-hydrate Scout Swarm:** Phase 2a now fans out 5 parallel Explore+Haiku scouts to collect artifact content (ADRs, feature specs, UX docs, pipeline artifacts, git history). Phase 2b routes all collected content to a single Sonnet subagent for extraction and brain capture, replacing the previous single-threaded approach. Includes completeness check gate, file-count gate (>20 files = split scouts), dry-run mode support, and dedup via `agent_search` at 0.85 threshold (ADR-0027)

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
