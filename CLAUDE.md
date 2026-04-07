# Atelier Pipeline

Multi-agent orchestration system for AI-powered IDEs (Claude Code + Cursor). Quality gates, continuous QA, and persistent institutional memory (Atelier Brain).

## Tech Stack

- **Hooks/Enforcement:** Bash shell scripts (PreToolUse hooks)
- **Brain MCP Server:** Node.js (server.mjs), PostgreSQL with pgvector and ltree extensions
- **Agent System:** Markdown persona files, slash commands, orchestration rules
- **IDE Support:** Claude Code plugin + Cursor plugin (dual-target from shared source)
- **Plugin System:** Claude Code plugin format (.claude-plugin/plugin.json), Cursor plugin format (.cursor-plugin/)

## Test Commands

- `pytest tests/ && cd brain && node --test ../tests/brain/*.test.mjs` -- full test suite
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
brain/           # Atelier Brain MCP server (Node.js + PostgreSQL)
skills/          # Plugin skills (pipeline-setup, brain-setup, brain-hydrate, pipeline-overview)
.claude/         # Installed pipeline files (this project eats its own cooking)
docs/            # User guide, technical reference, ADRs, pipeline state
scripts/         # Plugin lifecycle scripts (update checks)
```

## Key Conventions

- **Roz-first TDD:** Roz writes test assertions before Colby builds. Colby never modifies Roz's assertions.
- **Eva never writes code:** Eva orchestrates and routes. Colby implements. Ellis commits.
- **Triple target:** `source/` contains templates with `{placeholders}`. `.claude/` contains installed copies for Claude Code. `.cursor-plugin/` contains installed copies for Cursor. All stay in sync within their respective contexts.
- **ADR immutability:** ADRs are never updated in place. New ADRs supersede old ones.
- **Mechanical enforcement:** PreToolUse hooks block agents from writing outside their designated paths. Behavioral guidance is backed by shell-script enforcement.
- **Living artifacts:** Specs and UX docs are updated at pipeline end. Pipeline state files track session recovery.
- **Shared preamble:** Agent personas reference `agent-preamble.md` for shared DoR/DoD, retro, and brain protocols. Domain-specific behavior stays in persona files.
- **Cross-layer wiring:** Cal designs vertical slices (producer + consumer per step). Colby documents contract shapes. Roz and Poirot verify wiring. Orphan endpoints are blockers.

## Pipeline System (Atelier Pipeline)

This project uses a multi-agent orchestration pipeline for structured development.

**Agents:** Eva (orchestrator), Robert (product), Sable (UX), Cal (architect), Colby (engineer), Roz (QA), Agatha (docs), Ellis (commit)

**Commands:** /pm, /ux, /architect, /debug, /pipeline, /devops, /docs

**Pipeline state:** docs/pipeline/ -- Eva reads this at session start for recovery

**Key rules:**
- Roz writes tests before Colby builds (Roz-first TDD)
- Roz verifies every Colby output (no self-review)
- Ellis commits (Eva never runs git on code)
- Full test suite between work units
