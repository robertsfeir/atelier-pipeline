# Agatha Divergence Report -- ADR-0042

**Feature:** ADR-0042 Scout Synthesis Layer and Model/Effort Tier Corrections
**Date:** 2026-04-20
**Scope:** Pipeline-internal change. No user-facing product docs exist for this feature area.

## DoR: Requirements Extracted

From ADR-0042 (doc-impact surface only):

| # | Requirement | Source |
|---|-------------|--------|
| D1 | User-facing docs that restate the Per-Agent Assignment Table must reflect the 8 agent model/effort changes (Roz, Robert, Sable, Sentinel, Deps, Ellis, Distillator, brain-extractor) | ADR-0042 Decision #2 |
| D2 | User-facing docs that restate the Promotion Signals must remove the 3 deleted signals (auth/crypto, Pipeline sizing = Large, New module / service creation) | ADR-0042 Decision #3 |
| D3 | User-facing docs that describe Agatha's tier must remove the Tier 1 runtime override | ADR-0042 Decision #2 ("Agatha Tier 1 runtime override: removed") |
| D4 | User-facing docs must introduce the `max` effort prohibition | ADR-0042 Decision #4 (Enforcement Rule 5) |
| D5 | User-facing docs must document the new Sonnet synthesis layer protocol and the explicit spawn directive, if they already describe the scout fan-out at the doc level | ADR-0042 Decision #1 + Decision #6 |
| D6 | User-facing docs that describe the brain-extractor as "Haiku" must change to "Sonnet" | ADR-0042 Decision #2 |
| D7 | CHANGELOG entry under [Unreleased] documenting the change set | Project convention (prior ADR-0041 entry at v3.34.0 set the template) |
| D8 | ADR files themselves are immutable and must NOT be edited | Project convention + CLAUDE.md |

## Scope Assessment

ADR-0042 is a **pipeline-internal** configuration change. The observable user impact:
- Some agents use different models (cost/latency characteristics shift) -- documented in the technical reference model tables.
- Scout-swarm behavior adds a synthesis step on Medium+ pipelines -- observable only if the user inspects Eva's invocation traces.

**No product-user-facing UI, workflow, API, or CLI command changes.** No `/` commands gained or lost. No end-user action required.

Source-of-truth documents for the technical substance (Per-Agent Assignment Table, Promotion Signals, Scout Fan-out Protocol, invocation templates) live in `source/shared/rules/pipeline-models.md`, `source/shared/rules/pipeline-orchestration.md`, and `source/shared/references/invocation-templates.md`. Those are updated by Colby under the ADR's Implementation Plan (Steps 1, 3, 4), not by Agatha.

## Files Modified (Worktree)

| File | Reason | Change |
|------|--------|--------|
| `docs/guide/technical-reference.md` | Restates Agent Table, Model Selection tier table, Promotion Signals table (all three diverged from ADR-0042) | See edits below |
| `docs/guide/user-guide.md` | "Haiku extractor" language now incorrect (brain-extractor is Sonnet) | One-line update |
| `CHANGELOG.md` | [Unreleased] entry for ADR-0042 per Keep a Changelog format | Added `### Added` and `### Changed` blocks |

### technical-reference.md -- edits applied

1. **Agent Table (§ Agent Roster).** Model/effort column updated for Robert (Opus->Sonnet), Sable (Opus->Sonnet), Roz (high->medium), Agatha (removed Tier 1 runtime-override clause), Sentinel (medium->low, removed "high on auth/crypto"), Deps (Opus->Sonnet), Ellis (Haiku->Sonnet), Distillator (Haiku->Sonnet), brain-extractor (Haiku->Sonnet). Added new row for Synthesis agent (Tier 2, Sonnet, low).
2. **Model Selection § 4-tier task-class table.** Tier 1 model changed from "Haiku" to "Sonnet (Explore scouts use Haiku)" and typical-agent list updated (removed `Agatha (reference)`; split Explore scouts out as the Haiku holdout). Tier 2 model changed from "Opus" to "Opus or Sonnet (per-agent)" with the Sonnet holdings named. Tier 3 base effort column annotated with Roz-medium exception.
3. **Model Selection § Adaptive-thinking rationale paragraph.** New paragraph added after the tier table, summarizing Opus 4.7 effort semantics (medium/high/xhigh) and the `max` prohibition.
4. **Model Selection § Promotion Signals table.** Three rows removed (auth/crypto, Pipeline sizing = Large, New module / service creation). Explanatory prose added below the reduced 3-row table naming each removed signal and the rationale (route to Sentinel / tier-picker / subsumed by xhigh).
5. **Model Selection § Enforcement Rules.** Added rule: `max` effort forbidden per ADR-0042 (Anthropic Opus 4.7 adaptive-thinking guidance).
6. **New § Scout Synthesis Layer (ADR-0042).** New subsection added after Model Selection, describing: the Sonnet/low synthesis step; per-primary-agent block names (`<research-brief>` / `<colby-context>` / `<qa-evidence>`); required field lists per shape (Cal, Colby, Roz); forbidden content; skip conditions; explicit spawn directive.
7. **§ Hybrid Capture Model.** "lightweight Haiku extractor" -> "lightweight Sonnet extractor".

### user-guide.md -- edits applied

1. § What the brain captures: "A lightweight Haiku extractor fires..." -> "A lightweight Sonnet extractor fires...". Single-line factual fix; no workflow or UX change.

### CHANGELOG.md -- [Unreleased] entry added

Two sections under `[Unreleased]`:
- `### Added` -- ADR-0042 summary (synthesis layer, block mapping, Eva spawn directive, hook unchanged).
- `### Changed` -- enumerated per-agent model/effort changes; promotion-signal removals; `max` prohibition; Agatha Tier 1 runtime-override removal; guide files updated.

Release version NOT bumped. This entry accumulates under `[Unreleased]` until the next release cut (per project convention -- ADR-0041 landed the same way).

## Divergence Report

| Divergence | Spec (ADR) says | Prior code/docs did | Requires |
|-----------|-----------------|---------------------|----------|
| User-guide and technical-reference described the brain-extractor as a "Haiku extractor" | ADR-0042 moves brain-extractor to Sonnet/low (Tier 1) | Both guides hard-coded "Haiku extractor" | Fixed in this sweep (user-guide.md:1099; technical-reference.md:§Hybrid Capture Model) |
| Technical-reference Agent Table still listed Agatha as `Opus, medium (Tier 2 conceptual) / Haiku, low (Tier 1 reference)` | ADR-0042 Decision #2 removed the Tier 1 runtime override; Agatha is always Tier 2 | Table restated the ADR-0041 dual-tier mapping | Fixed in Agent Table row for Agatha |
| Technical-reference Agent Table listed Sentinel as `Opus, medium (Tier 2); high on auth/crypto` | ADR-0042 Decision #3 removed the auth/crypto promotion signal; Sentinel is Opus/low per Decision #2 | Table carried both the old effort (medium) and the removed promotion (high on auth/crypto) | Fixed in Agent Table row for Sentinel |
| Technical-reference Model Selection tier table listed `Haiku, low` Tier 1 with `Agatha (reference)` as a typical agent | ADR-0042 promotes Ellis/Distillator/brain-extractor to Sonnet and removes Agatha from Tier 1 entirely | Tier 1 row mapped to ADR-0041's composition | Fixed in tier table; Agatha moved out; Sonnet noted as Tier 1 model for extractors |
| Technical-reference Promotion Signals table included `Auth / security / crypto files touched` and `Pipeline sizing = Large` | ADR-0042 Decision #3 removes both | Prior table had 5 rows | Fixed -- table now 3 rows with rationale block naming removed signals |
| Neither guide mentioned `max` effort prohibition | ADR-0042 Decision #4 adds Enforcement Rule 5 | Guides silent on `max` | Added to technical-reference Enforcement Rules |
| Neither guide mentioned the Scout Synthesis layer or the explicit spawn directive | ADR-0042 Decision #1 + #6 introduce both | Guides described scout fan-out only via ADR-0027 cross-ref in ADR index | Added new § Scout Synthesis Layer in technical-reference.md |

**No spec-vs-code divergences found.** ADR-0042 is newly landed and the source-of-truth files (`pipeline-models.md`, agent frontmatters) are edited by Colby under the ADR's Implementation Plan. Verification of those edits is out of Agatha's scope -- it belongs to Roz under T-0042-001 through T-0042-029.

**No user-facing product docs exist for this feature area** (pipeline-internal change). The guides are the only user-visible doc surface and they are now aligned with ADR-0042.

## DoD: Verification

- [x] D1 covered: Agent Table model/effort column updated for all 8 changed agents; Synthesis row added.
- [x] D2 covered: Promotion Signals table trimmed to 3 rows; removed signals documented below the table.
- [x] D3 covered: Agatha row in Agent Table no longer references Tier 1 runtime override; Tier 1 row in model-selection table no longer lists Agatha (reference).
- [x] D4 covered: Enforcement Rules gained the `max` prohibition line.
- [x] D5 covered: New § Scout Synthesis Layer describes the layer, block-name mapping, field shapes, skip conditions, and the explicit spawn directive.
- [x] D6 covered: Both "Haiku extractor" references (user-guide § What the brain captures; technical-reference § Hybrid Capture Model) now read "Sonnet extractor".
- [x] D7 covered: CHANGELOG [Unreleased] section gained Added + Changed subsections describing ADR-0042.
- [x] D8 honored: No ADR files modified. No pipeline-state files modified.
- [x] Divergence report written to this file.
- [x] Worktree only: all edits under `/Users/sfeirr/projects/atelier-pipeline-86423e1f/` -- main repo untouched.

**Status:** Documentation sweep for ADR-0042 complete. Ready for Roz structural sign-off on the CHANGELOG entry and guide edits before Ellis commit.
