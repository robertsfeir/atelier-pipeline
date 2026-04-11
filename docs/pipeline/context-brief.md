# Context Brief

## Scope
Source hook enforcement audit — fix all review findings (ADR-0033)
Medium pipeline. All edits in source/ only — never .claude/.

## User Decisions
- 2026-04-11: Auto-advance through all phases without pausing. User said "continue to the end, don't stop."
- 2026-04-11: Design gaps G1+G2 (brain capture for robert/sable/ellis) added to scope — use same Haiku extractor pattern.
- 2026-04-11: Colby edits source/ only — .claude/ is re-synced via /pipeline-setup after Ellis commits.

## Rejected Alternatives
- Split into 13 separate ADRs — rejected (one subsystem, one pipeline)
- Fix critical/major only, defer minor+gap — rejected (minor fixes are trivial, gaps are natural extensions)
