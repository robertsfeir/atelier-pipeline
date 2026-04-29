# Atelier Pipeline

Multi-agent orchestration system for AI-powered IDEs (Claude Code + Cursor). Quality gates and continuous QA. Persistent institutional memory is provided by the separate `mybrain` plugin (optional; install alongside this plugin).

## Tech Stack

- **Hooks/Enforcement:** Bash shell scripts (PreToolUse hooks)
- **Agent System:** Markdown persona files, slash commands, orchestration rules
- **IDE Support:** Claude Code plugin + Cursor plugin (dual-target from shared source)
- **Plugin System:** Claude Code plugin format (.claude-plugin/plugin.json), Cursor plugin format (.cursor-plugin/)

## Test Commands

- `pytest tests/` -- full test suite
- `echo "no linter configured"` -- linter
- `echo "no typecheck configured"` -- type checker

## Source Structure

Source templates are split into three directories: `source/shared/` (platform-agnostic content), `source/claude/` (Claude Code overlays with frontmatter and hooks), and `source/cursor/` (Cursor overlays). Agent files are assembled at install time by combining platform-specific frontmatter overlays with shared content bodies.

```
source/          # Template files -- copied to target projects by /pipeline-setup
  shared/        # Platform-agnostic content (no YAML frontmatter)
    agents/      # Agent content bodies (14 agents incl. robert-spec, sable-ux producers)
    commands/    # Slash command definitions (11 commands)
    references/  # Quality framework, retro lessons, invocation templates, operations, agent preamble, QA checks, branch/MR mode
    pipeline/    # Pipeline state file templates (5 files)
    rules/       # Eva persona, orchestration rules (always-loaded by Claude Code)
    variants/    # Strategy variant templates (branching lifecycle)
    dashboard/   # Dashboard templates
  claude/        # Claude Code overlays
    agents/      # Claude Code frontmatter overlays (*.frontmatter.yml)
    hooks/       # Enforcement hook scripts (20 scripts + 1 config)
    commands/    # Command frontmatter overlays
    rules/       # Rule frontmatter overlays
    variants/    # Variant frontmatter overlays
  cursor/        # Cursor overlays
    agents/      # Cursor frontmatter overlays (*.frontmatter.yml, no hooks field)
    hooks/       # hooks.json for Cursor plugin
    commands/    # Command frontmatter overlays
    rules/       # Rule frontmatter overlays
    variants/    # Variant frontmatter overlays
skills/          # Plugin skills (pipeline-setup, pipeline-uninstall, pipeline-overview)
.claude/         # Installed pipeline files (this project eats its own cooking)
docs/            # User guide, technical reference, ADRs, pipeline state
scripts/         # Plugin lifecycle scripts (update checks)
```

## Key Conventions

- **Colby runs the code he writes:** every change is exercised (function called, endpoint hit, UI rendered, hook invoked) before DoD. Documentation-only wiring is not "done."
- **Sarah writes short ADRs:** 1-2 pages. Decision + rationale + falsifiability. No implementation manuals, no test specs, no line-by-line file lists.
- **Eva never writes code:** Eva orchestrates and routes. Colby implements. Ellis commits.
- **Triple target:** `source/` contains templates with `{placeholders}`. `.claude/` contains installed copies for Claude Code. `.cursor-plugin/` contains installed copies for Cursor. All stay in sync within their respective contexts.
- **ADR immutability:** ADRs are never updated in place. New ADRs supersede old ones.
- **Mechanical enforcement:** PreToolUse hooks block agents from writing outside their designated paths. Behavioral guidance is backed by shell-script enforcement.
- **Living artifacts:** Specs and UX docs are updated at pipeline end. Pipeline state files track session recovery.
- **Shared preamble:** Agent personas reference `agent-preamble.md` for shared DoR/DoD and brain protocols. Domain-specific behavior stays in persona files.
- **Cross-layer wiring is exercised, not documented:** Sarah decides; Colby exercises the wiring at build time; Poirot catches orphan endpoints post-build. Contract documentation is not a substitute for execution.

## Pipeline System (Atelier Pipeline)

This project uses a multi-agent orchestration pipeline for structured development.

**Agents:** Eva (orchestrator), Robert (product), Sable (UX), Sarah (architect), Colby (engineer), Poirot (default post-build verifier), Sherlock (user-reported bug detective), Agatha (docs), Ellis (commit)

**Commands:** /pm, /ux, /architect, /pipeline, /devops, /docs

**Pipeline state:** docs/pipeline/ -- Eva reads this at session start for recovery

**Key rules:**
- Colby exercises every change he ships (backend: call it; UI: render it; hook: invoke it)
- Eva runs the mechanical test gate between Colby-done and Poirot
- Poirot is the default post-build verifier (blind diff review, 1-3 findings typical, zero with confidence OK)
- Sherlock handles user-reported bugs only (never pipeline-internal findings)
- Ellis commits (Eva never runs git on code)
- Scout fan-out is sizing-gated: Micro/Small skip scouts; Medium/Large enforce evidence blocks
