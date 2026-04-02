# Atelier Pipeline

Multi-agent orchestration system for AI-powered IDEs (Claude Code + Cursor). Quality gates, continuous QA, and persistent institutional memory (Atelier Brain).

## Tech Stack

- **Hooks/Enforcement:** Bash shell scripts (PreToolUse hooks)
- **Brain MCP Server:** Node.js (server.mjs), PostgreSQL with pgvector and ltree extensions
- **Agent System:** Markdown persona files, slash commands, orchestration rules
- **IDE Support:** Claude Code plugin + Cursor plugin (dual-target from shared source)
- **Plugin System:** Claude Code plugin format (.claude-plugin/plugin.json), Cursor plugin format (.cursor-plugin/)

## Test Commands

- `echo "no test suite configured"` -- full test suite (pending ADR-0003 Step 6)
- `echo "no linter configured"` -- linter
- `echo "no typecheck configured"` -- type checker

## Source Structure

```
source/          # Template files -- copied to target projects by /pipeline-setup
  rules/         # Eva persona, orchestration rules (always-loaded by Claude Code)
  agents/        # Subagent personas (12 agents)
  commands/      # Slash command definitions (11 commands)
  references/    # Quality framework, retro lessons, invocation templates, operations, agent preamble, QA checks, branch/MR mode
  hooks/         # Enforcement hook scripts (6 scripts + 1 config)
  pipeline/      # Pipeline state file templates (5 files)
  variants/      # Strategy variant templates (branching lifecycle)
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

## Eva Rules Split

Eva's rules are split into identity (always-loaded: `default-persona.md` + `agent-system.md`) and operations (path-scoped: `pipeline-orchestration.md` + `pipeline-models.md`). The operations files load automatically when accessing `docs/pipeline/` and survive `/compact`. See ADR-0004 Step 0.
