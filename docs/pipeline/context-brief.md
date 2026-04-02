# Context Brief

Captures conversational decisions, user corrections, and rejected alternatives.
Reset at the start of each new feature pipeline.

## Scope
Waves 2-3 of agent frontmatter enrichment initiative. Wave 2: hook modernization (#28) — `if` conditionals, lifecycle telemetry hooks, PostCompact context preservation, StopFailure error tracking. Wave 3: advanced features (#29) — `defer` permission, per-agent `memory`, `permissionMode`, agent-scoped `hooks`.

## Key Constraints
- Wave 1 (frontmatter fields) already shipped as v3.16.0 — do not re-touch those fields
- `source/` templates and `.claude/` installed copies must stay in sync
- Brain and agent `memory` are complementary, not competing (Brain = institutional, agent memory = working knowledge)
- `defer` is soft guidance; hard `deny` stays for security boundaries (Eva write outside docs/pipeline/)
- Read-only agents (Robert, Sable, Investigator, Distillator, Darwin, Deps, Sentinel) get `permissionMode: plan`

## User Decisions
- Two-tier memory architecture (brain + agent memory) — flagged during Wave 1, deferred to Wave 3
- Colors only on Cal/Colby/Roz/Ellis/Robert/Sable (6 of 12) — Wave 1 decision, still applies

## Rejected Alternatives
(none yet)
