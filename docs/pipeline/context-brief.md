# Context Brief

Captures conversational decisions, user corrections, and rejected alternatives.
Reset at the start of each new feature pipeline.

## Scope
ADR-0023: Agent Specification Reduction — Constraints Over Procedures. ~57% reduction of agent persona specification by removing generic procedures (Opus baseline competencies) and redundant behavioral restrictions (now enforced by ADR-0022's three-layer pyramid). Two phases: structural reduction (12 steps) then validation (3 pipelines with telemetry comparison).

## Key Constraints
- ADR-0022 is prerequisite (complete, unpushed) — Layer 2 frontmatter hooks must be operational before removing behavioral text
- Distillator is the exception: >=130 lines, NOT reduced (Haiku needs procedural density per R14)
- TDD instructions preserved for Colby and Roz regardless of model tier (R15)
- Line count targets are +-10%
- Examples must demonstrate judgment calls the model would get wrong without them (R4)
- session-boot.sh follows retro lesson #003: lightweight, exit 0 always, no blocking

## User Decisions
- 2026-04-04: Zero bats anywhere in project. All tests must be pytest. Mechanically enforced via test_no_bats.py. Test command updated from `bats tests/hooks/` to `pytest tests/` across all config files.
- 2026-04-04: User authorized autonomous execution through all remaining waves to final commit. Stop before push.

## Rejected Alternatives
(none yet)
