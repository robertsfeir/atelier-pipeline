## DoR: Diff Metadata
**Files:** 1 (scoped re-run on prior FIX-REQUIRED) | **Added:** ~18 | **Removed:** ~2
**Functions modified:** none (documentation/contract only)
**New dependencies:** none

Files changed in fix wave:
- `source/shared/references/xml-prompt-schema.md:109-126` -- agent count corrected from "10" to "18" with full enum enumeration; two new subsections added for `captured_by` and `created_at`

## Exercised
Static-only verification, sufficient for a documentation/contract diff.
- **Verified the agent count claim against ground truth:** read `brain/lib/config.mjs:18-38` (the `SOURCE_AGENTS` enum). Counted 18 entries: eva, cal, robert, sable, colby, roz, agatha, ellis, poirot, distillator, robert-spec, sable-ux, sentinel, darwin, deps, brain-extractor, sarah, sherlock. The diff's enumeration matches the enum exactly in name and order. Count of 18 is correct.
- **Verified the no-capture-path subset against the enum's own comments:** the diff lists 9 agents as having no automatic capture path (eva, poirot, distillator, sentinel, darwin, deps, brain-extractor, sarah, sherlock). Each one is annotated as "non-extracted" or equivalent in `config.mjs:19-37`. Subset is accurate.
- **Verified schema citations in new subsections:** `captured_by` references `brain/schema.sql:100` (column exists, TEXT, nullable). `created_at` cites `DEFAULT now()` -- matches `brain/schema.sql:105`. Both accurate.
- **Verified position and prose consistency:** new subsections sit between `agent` and `relevance`, matching the table-row order on line 85. The captured_by null-handling text ("treat null as 'unknown origin'") is consistent with the emission rule in `agent-system.md:144` ("Omit captured_by attribute only if null") -- same null model, expressed at two layers.
- **Wider sweep for stale agent-count claims:** grep across `source/`, `.claude/`, `docs/` for "10 agents". Only one source-tree hit remains in the **installed copy** `.claude/references/xml-prompt-schema.md:109` -- expected per the source-only convention; Eva queues `/pipeline-setup` to sync. Not a Colby regression. All other "9 agents" hits across ADRs and docs refer to unrelated scopes (brain-extractor mapping table, Cursor port discovery, SubagentStop hook config) and are accurate in their own contexts.
- **Wider sweep for stale `<thought>` attribute lists:** grep for `type, agent, phase, relevance` without `captured_by` across `source/`. Zero source-tree hits remain. Contract is fully consistent across `agent-system.md`, `invocation-templates.md`, `xml-prompt-schema.md`, and `agent-preamble.md`.

## DoD: Verification
**Findings:** 0 | **Categories:** documentation drift, schema accuracy, contract consistency | **Grep verified:** "10 agents" / "9 agents" across source+installed+docs; pre-fix `<thought>` attribute strings across `source/`; SOURCE_AGENTS enum read end-to-end | **Exercised:** new subsections re-read in context; schema citations verified against `brain/schema.sql:100,105`; agent enumeration verified against `brain/lib/config.mjs:18-38`; position/order verified against table-row at line 85

## Status
**PASS.**

Both fixes are clean and complete. The `### <thought> Attribute Values` section now has full coverage for all six attributes the table row advertises (`type`, `phase`, `agent`, `captured_by`, `created_at`, `relevance`). The agent-count correction is grounded in the live `SOURCE_AGENTS` enum, and the no-capture-path subset is correctly classified per the enum's inline comments. No new findings.

## Findings
| # | Location | Severity | Category | Description | Suggested Fix |
|---|----------|----------|----------|-------------|---------------|

(no findings)

## Side note (informational, not a finding -- restated from prior wave)
The installed copy `.claude/references/xml-prompt-schema.md` is now drifted from `source/shared/references/xml-prompt-schema.md` across all three lines touched in this fix series (line 85 table row, line 109 agent enumeration, lines 117-126 new subsections). Eva should queue `/pipeline-setup` before this contract lands in live agent context. Not a Colby concern (source-only convention).
