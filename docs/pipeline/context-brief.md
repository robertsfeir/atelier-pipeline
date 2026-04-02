# Context Brief

Captures conversational decisions, user corrections, and rejected alternatives.
Reset at the start of each new feature pipeline.

## Scope
Wave 1: Add `model`, `effort`, `color`, `maxTurns`, `disallowedTools` frontmatter fields to all 12 agent persona files. Issue #27.

## Key Constraints
- `model` in frontmatter is the BASE/default — Eva still overrides at invocation time via classifier (pipeline-models.md)
- Size-dependent agents (Cal, Colby, Agatha, Ellis) get their lowest-tier model as default
- `disallowedTools` already exists on Colby, Roz, Cal, Ellis — complete the rest
- Remove behavioral "You run on X" text from `<identity>` — frontmatter is mechanical enforcement
- source/ templates and .claude/ installed copies must stay in sync
- 8 available colors for 12 agents — some sharing is OK for agents that never run in parallel

## User Decisions
- Two-tier memory architecture (brain + agent memory) captured in brain — Wave 3 concern, not Wave 1
- Agent matrix from issue #27 is the spec

## Rejected Alternatives
(none yet)
