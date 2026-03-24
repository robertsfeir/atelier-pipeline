# Atelier Pipeline

A Claude Code plugin providing multi-agent orchestration with quality gates, continuous QA, and persistent institutional memory (Atelier Brain).

## Tech Stack

- **Hooks/Enforcement:** Bash shell scripts (PreToolUse/PostToolUse/Stop hooks)
- **Brain MCP Server:** Node.js (server.mjs), PostgreSQL with pgvector and ltree extensions
- **Agent System:** Markdown persona files, slash commands, orchestration rules
- **Plugin System:** Claude Code plugin format (.claude-plugin/plugin.json)

## Test Commands

- `echo "no test suite configured"` -- full test suite (pending ADR-0003 Step 6)
- `echo "no linter configured"` -- linter
- `echo "no typecheck configured"` -- type checker

## Source Structure

```
source/          # Template files -- copied to target projects by /pipeline-setup
  rules/         # Eva persona, orchestration rules (always-loaded by Claude Code)
  agents/        # Subagent personas (9 agents)
  commands/      # Slash command definitions (7 commands)
  references/    # Quality framework, retro lessons, invocation templates, operations
  hooks/         # Enforcement hook scripts (6 scripts + 1 config)
  pipeline/      # Pipeline state file templates (5 files)
brain/           # Atelier Brain MCP server (Node.js + PostgreSQL)
skills/          # Plugin skills (pipeline-setup, brain-setup, brain-hydrate, pipeline-overview)
.claude/         # Installed pipeline files (this project eats its own cooking)
docs/            # User guide, technical reference, ADRs, pipeline state
scripts/         # Plugin lifecycle scripts (update checks)
```

## Key Conventions

- **Roz-first TDD:** Roz writes test assertions before Colby builds. Colby never modifies Roz's assertions.
- **Eva never writes code:** Eva orchestrates and routes. Colby implements. Ellis commits.
- **Dual tree:** `source/` contains templates with `{placeholders}`. `.claude/` contains installed copies with literal values. Both must stay in sync within their respective contexts.
- **ADR immutability:** ADRs are never updated in place. New ADRs supersede old ones.
- **Mechanical enforcement:** PreToolUse hooks block agents from writing outside their designated paths. Behavioral guidance is backed by shell-script enforcement.
- **Living artifacts:** Specs and UX docs are updated at pipeline end. Pipeline state files track session recovery.
