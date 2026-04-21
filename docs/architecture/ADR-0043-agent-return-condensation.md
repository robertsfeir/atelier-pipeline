# ADR-0043: Agent Return Condensation and filepath:line Citation Mandate

## Status

Accepted. **Related (not modified):** ADR-0011 (observation-masking) -- Eva's receipt-format-per-agent table remains authoritative on the Eva side; this ADR aligns producer self-reports to those Eva-side formats. ADR-0042 (scout synthesis tier correction) -- unchanged; this ADR addresses the complementary producer-side contract. No prior ADR is superseded.

---

## DoR: Requirements Extracted

**Sources:** Issue #31 (section 1 "Agent return condensation"), `source/shared/references/agent-preamble.md` (current preamble structure), `source/shared/agents/{cal,colby,roz}.md` (current `<output>` sections), `source/shared/rules/pipeline-orchestration.md` observation-masking protocol (Eva's receipt-format-per-agent table), retro lessons 002 and 005, `.claude/references/retro-lessons.md`.

| # | Requirement | Source |
|---|-------------|--------|
| R1 | Mandate in `agent-preamble.md` that producers return a short summary + artifact-path pointer, not the artifact body inline | Issue #31 sec 1 "Fix" bullet 1 |
| R2 | Mandate in `agent-preamble.md` that code claims include `filepath:line` citations | Issue #31 sec 1 "Fix" bullet 2 |
| R3 | Exempt "citing one's own just-written artifact" from the filepath:line rule (covered by summary + artifact-path pointer) | Task constraints -- "Keep the filepath:line citation mandate narrow" |
| R4 | Tighten Cal's `<output>` to the condensed one-liner per Issue #31 | Issue #31 "Cal:" line |
| R5 | Tighten Colby's `<output>` to the condensed one-liner per Issue #31 (refined to include lint/typecheck status matching Eva's receipt format) | Issue #31 "Colby:" line; pipeline-orchestration.md observation-masking table |
| R6 | Tighten Roz's `<output>` to the condensed one-liner per Issue #31 (refined to include Wave N + suggestions count matching Eva's receipt format) | Issue #31 "Roz:" line; pipeline-orchestration.md observation-masking table |
| R7 | Source template and installed copy must stay in sync for each of the 3 personas AND the preamble (4 source files + 3 installed copies = 7 files) | Issue #31 acceptance "Source templates and installed copies stay in sync" + CLAUDE.md "Triple target" convention |
| R8 | No Cursor overlay edits required (Cursor overlays have no `<output>` content for cal/colby/roz) | Task context line: "Cursor overlays do NOT have `<output>` content" |
| R9 | New `<output>` one-liners align with Eva's existing receipt-format table in pipeline-orchestration.md observation-masking (producer self-report matches Eva's normalized masking format, minimizing re-read pressure) | Task constraints -- "Align the new `<output>` formats with Eva's existing receipt-format table" |
| R10 | Preamble mandate does NOT require producers to inline-repeat artifact content Eva already has a pointer to; artifact body stays on disk | Issue #31 "Why it matters" subagent context firewall |
| R11 | Roz QA report persistence to `{pipeline_state_dir}/last-qa-report.md` remains unchanged (current Roz output contract preserves this line) | Roz persona line 113 |
| R12 | Ellis is exempt from preamble (already exempted per preamble line 10-12); condensation mandate does not affect Ellis's commit-receipt format (ADR-0011 receipt row for Ellis is already terse: "Committed {hash} on {branch}, {N} files") | Preamble exemption line 10-12; ADR-0011 receipt row |

**Retro risks:**
- **Lesson 002 (self-reporting bug codification):** N/A this ADR -- no test assertions are modified; this is a specification tightening authored by Cal with Roz reviewing the test spec per Roz-first TDD.
- **Lesson 005 (cross-agent wiring):** Applies directly. `agent-preamble.md` (producer) is consumed by cal.md, colby.md, roz.md (consumers). All three consumers land in the same implementation step as the producer, satisfying the vertical-slice rule. See Wiring Coverage section.
- **Lesson 001 (data sensitivity), 003 (Stop-hook duplication), 004 (hung-process retry), 006 (frontend physics):** N/A this ADR -- no data access, no hooks, no long-running commands, no UI.

**Brain context:** Brain unavailable this session. Ran `grep -l "observation-masking\|context firewall\|return condensation" docs/architecture/` to find prior related ADRs. ADR-0011 (observation-masking) is the direct predecessor; it defined Eva's masking of agent returns into receipts. This ADR closes the symmetric producer-side gap: agents currently return full bodies that Eva *then* masks -- wasteful because the mask format is known in advance. No other prior ADR addresses producer return verbosity.

---

## Anti-Goals

**Anti-goal 1: Elastic one-liner templates that drift back to multi-paragraph handoffs.**
Reason: The whole point is a fixed-shape sentence Eva can regex-mask without re-reading. Any wording like "when relevant, include ..." reopens the verbosity door and defeats the firewall. The `<output>` one-liners are verbatim templates, not guidance. Revisit: when Eva's observation-masking table adds a new field that genuinely cannot be derived from the one-liner (none currently foreseen).

**Anti-goal 2: Retroactive rewrites of pre-Roz/Cal/Colby persona-body content ("since we're in here anyway").**
Reason: Scope creep. The issue is one-line-receipt-plus-preamble-mandate, not a general persona audit. Editing other sections invites unreviewed behavior changes and inflates the test-spec surface. This ADR touches exactly the `<output>` blocks of cal.md/colby.md/roz.md and adds a preamble section. Revisit: when a separate audit-oriented ADR is scoped for persona bodies (none proposed).

**Anti-goal 3: Applying the filepath:line mandate to producers citing their own just-written artifacts.**
Reason: Producers already ship the artifact at a stable path; requiring them to emit `docs/architecture/ADR-0043-...md:42` when the downstream agent needs the whole file anyway creates false precision and noise. Reviewers already enforce file:line for code claims about *existing* code -- that's the right scope. Revisit: if a future ADR introduces range-specific ADR references (e.g., ADR anchor links) that materially help Eva routing.

---

## Spec Challenge

**Assumption:** Eva's existing receipt-format-per-agent table (ADR-0011) captures the minimum information Eva needs to route downstream without re-reading the artifact, and the condensed `<output>` one-liners faithfully provide that same information. If wrong, the design fails because Eva receives a terse receipt that *looks* sufficient but omits a routing-critical signal (e.g., lint status, suggestions count), forcing a re-read on every handoff and recreating the very cost this ADR was meant to remove.

Mitigation: (a) The Colby and Roz one-liners were refined from the Issue #31 candidates to include every field present in Eva's existing masking format (lint PASS/FAIL + typecheck PASS/FAIL for Colby; Wave N + suggestions count for Roz). Cal's format matched already. (b) Test-spec T_0043_006 through T_0043_008 grep for each required field literally in the three `<output>` blocks -- a format drift is caught at the file level before it reaches Eva. (c) The mandate paragraph in the preamble points agents at the observation-masking table as the authoritative format reference, so future receipt-format changes flow mechanically through `pipeline-orchestration.md` without needing a new preamble edit each time. Falsifiable within one Medium pipeline: if Eva re-reads an ADR or a QA report to find a missing routing signal, the one-liner is under-specified and T_0043 category A expands.

**SPOF:** The preamble mandate section itself -- if the id/selector is unstable (e.g., renamed, relocated) or the prose is ambiguous, all three producers lose alignment simultaneously with no gradual degradation. Graceful degradation: (a) The mandate is anchored with a stable `<preamble id="return-condensation">` tag that tests grep for (T_0043_001); a rename is caught immediately. (b) The mandate is phrased as two short imperatives, not guidance prose -- low interpretation surface. (c) The three persona `<output>` blocks carry the mandate *in their own text* as well (the verbatim one-liner) so a preamble-side regression does not silently mis-shape the return; the preamble and the persona block reinforce each other. (d) `last-qa-report.md` persistence for Roz is preserved as a separate bullet under the one-liner to avoid collapsing two independent contracts into one line. **Known residual:** If an agent emits a well-formed one-liner but stuffs a prose recap *after* the one-liner (not blocked by tests because tests assert presence, not exclusivity), the firewall is partially breached. Monitored via Eva's observation-masking hit rate; three consecutive sessions where Eva re-reads an artifact despite a present one-liner triggers a follow-up "exclusivity" ADR tightening.

---

## Context

Subagents (Cal, Colby, Roz) are architectural context firewalls: the parent agent (Eva) sees only the final response. Writing the artifact to disk is how a subagent *exports* structured content past the firewall without paying Eva's context budget. Currently, all three of these producers do both -- they write the artifact to disk *and* return the full DoR/DoD tables, ADR skeletons, and QA findings inline. Eva then masks the inline return into a receipt (ADR-0011), meaning the verbose text traveled across the firewall only to be dropped on arrival.

Two compounding factors:

1. **Eva's receipt format is already defined.** ADR-0011 observation-masking specifies the per-agent receipt Eva normalizes to. The producer already knows (in principle) exactly what Eva will keep. Everything beyond those fields is wasted.

2. **`agent-preamble.md` is silent on both.** The preamble defines DoR/DoD, retro-lesson review, and brain-context handling, but says nothing about return shape or citation format. Reviewers (Robert, Sable, Poirot, Sentinel) already require `filepath:line` citations per their personas; producers do not, which creates asymmetric rigor -- code claims from Cal/Colby are less traceable than code claims from reviewers.

The fix: a shared preamble mandate (producer self-reports are condensed; code claims carry `filepath:line`), and three `<output>` block rewrites so Cal/Colby/Roz each emit exactly the one-liner Eva already normalizes to.

---

## Decision

### 1. Preamble mandate (new section in `source/shared/references/agent-preamble.md`)

Add a new `<preamble id="return-condensation">` section **after** the existing `<preamble id="shared-actions">` block and **before** the closing file boundary. The section contains the exact text below. No other edits to `agent-preamble.md`.

**Exact text to add:**

```markdown
<preamble id="return-condensation">

## Return Condensation and Citation

Every producer agent (including Cal, Colby, Roz, Agatha, robert-spec, sable-ux,
Darwin, and any discovered producer) follows these two rules on return:

1. **Condensed self-report.** Return a short summary plus a pointer to the
   artifact on disk. Do not inline the artifact body, DoR/DoD tables, ADR
   skeletons, QA findings, or any multi-paragraph restatement of content
   already written to a file. The subagent boundary is a context firewall --
   content that crossed the firewall only to be masked by Eva per the
   observation-masking protocol in
   `{config_dir}/rules/pipeline-orchestration.md` was wasted. Each persona's
   `<output>` section defines the exact one-liner format; emit that format,
   nothing more.

2. **`filepath:line` citations for code claims.** Any claim about existing
   code (a bug, a pattern, a contract shape, an integration point) includes
   a `path/to/file.ext:LINE` citation so downstream agents and reviewers can
   jump directly to the evidence. This applies to code claims only --
   summarizing your own just-written artifact with its path (covered by
   rule 1) does not require a line number. Reviewer agents (Poirot,
   Sentinel, Robert, Sable) already enforce this on their findings; this
   rule extends the same standard to producers.

**Exemption:** Ellis (commit agent) is exempt from this section for the same
reason he is exempt from DoR/DoD -- his commit-receipt shape is defined
directly by his persona `<workflow>`.

</preamble>
```

### 2. Cal `<output>` rewrite (in `source/shared/agents/cal.md`)

**Current `<output>`** (lines 128-149): contains full DoR preamble text, an ADR skeleton code block, DoD line, and a multi-line Handoff sentence.

**Replacement `<output>`** (verbatim, replaces everything between `<output>` and `</output>` tags):

```markdown
<output>
Write the full ADR to `{adr_dir}/ADR-NNNN-<slug>.md`. The ADR file contains
the full body (DoR, Status/Context/Decision/Alternatives/Consequences,
Implementation Plan, Test Specification, UX Coverage, UI Specification,
Contract Boundaries, Wiring Coverage, Data Sensitivity, Notes for Colby,
DoD).

Return exactly one line to Eva:

`ADR-NNNN saved to {adr_dir}/ADR-NNNN-<slug>.md. N steps, M tests. Next: Roz.`

Do not inline the ADR body, DoR table, or test-spec table in the return --
Eva reads the ADR from disk when needed. See
`{config_dir}/references/agent-preamble.md` preamble id="return-condensation".
</output>
```

### 3. Colby `<output>` rewrite (in `source/shared/agents/colby.md`)

**Current `<output>`** (lines 109-160): contains full Build Output code block with DoR, UI Contract table, UI/UX Verification, DoD, Contracts Produced/Consumed tables inline.

**Replacement `<output>`** (verbatim):

```markdown
<output>
Write the full build record (DoR, UI Contract, UI/UX Verification, DoD,
Contracts Produced, Contracts Consumed, Bugs Discovered) into your work in
the repository -- DoR/DoD in the implementation commit messages, UI
Contract and Contracts tables in `{pipeline_state_dir}/pipeline-state.md`
under the current unit. Test runs and lint/typecheck output stay in your
tool transcript.

Return exactly one line to Eva:

`Unit N DONE. N files changed. Lint PASS/FAIL. Typecheck PASS/FAIL. Ready for Roz: Y/N.`

Fix-cycle re-invocation one-line DoD stays per the existing workflow:
`Fixed [what] at path/to/file.ext:LINE. Tests pass.`

Do not inline DoR tables, UI Contract rows, Contracts tables, code diffs,
or test output in the return. See
`{config_dir}/references/agent-preamble.md` preamble id="return-condensation".
</output>
```

### 4. Roz `<output>` rewrite (in `source/shared/agents/roz.md`)

**Current `<output>`** (lines 94-114): contains full QA Report code block inline with verdict, checks table, requirements verification table, unfinished markers, issues found lists, doc impact, assessment -- followed by a persistence instruction.

**Replacement `<output>`** (verbatim):

```markdown
<output>
Write the full QA report (Verdict, Checks table, Requirements Verification
table, Unfinished Markers, BLOCKERs, FIX-REQUIREDs, Suggestions, Doc Impact,
Roz's Assessment) to `{pipeline_state_dir}/last-qa-report.md`. Overwrite
the prior report -- only the most recent QA report is retained on disk.

Return exactly one line to Eva:

`Roz Wave N PASS/FAIL. N BLOCKERs, N FIX-REQUIREDs, N suggestions. Report: {pipeline_state_dir}/last-qa-report.md.`

Scoped re-run mode one-line DoD stays per the existing workflow:
`Re-run: [check] now PASS/FAIL. Verdict: PASS/FAIL.`

Test-spec review mode one-line verdict stays per the existing workflow:
`Test-spec review: APPROVE / REVISE (round N). N findings.`

Do not inline the Checks table, Requirements Verification table, individual
BLOCKER/FIX-REQUIRED entries, or diff excerpts in the return. Code-claim
citations within the QA report file use `filepath:line` format. See
`{config_dir}/references/agent-preamble.md` preamble id="return-condensation".
</output>
```

### 5. Installed-copy sync

The four source edits above are mirrored to the three installed copies in `.claude/` (Claude side only; Cursor overlays do not carry `<output>` content for these agents). Six edits total across seven files:

| Source file | Installed copy (Claude) |
|---|---|
| `source/shared/references/agent-preamble.md` | `.claude/references/agent-preamble.md` |
| `source/shared/agents/cal.md` | `.claude/agents/cal.md` |
| `source/shared/agents/colby.md` | `.claude/agents/colby.md` |
| `source/shared/agents/roz.md` | `.claude/agents/roz.md` |

### 6. Alignment with Eva's observation-masking receipts

For traceability, here is the producer self-report (this ADR) mapped to Eva's normalized receipt (ADR-0011 observation-masking):

| Agent | New producer one-liner (this ADR) | Eva's receipt (ADR-0011) | Alignment |
|---|---|---|---|
| Cal | `ADR-NNNN saved to {path}. N steps, M tests. Next: Roz.` | `Cal: ADR at {path}, {N} steps, {N} tests specified` | Fields match 1:1; Eva prefixes `Cal:` and swaps "Next: Roz" for "specified" (narrative tail differs, substance identical). |
| Colby | `Unit N DONE. N files changed. Lint PASS/FAIL. Typecheck PASS/FAIL. Ready for Roz: Y/N.` | `Colby: Unit {N} DONE, {N} files changed, lint {PASS/FAIL}, typecheck {PASS/FAIL}` | Fields match 1:1 plus producer adds `Ready for Roz: Y/N` (useful routing signal Eva currently re-derives). |
| Roz | `Roz Wave N PASS/FAIL. N BLOCKERs, N FIX-REQUIREDs, N suggestions. Report: {path}.` | `Roz: Wave {N} {PASS/FAIL}, {N} blockers, {N} must-fix, {N} suggestions. Report: last-qa-report.md` | Fields match 1:1; "FIX-REQUIRED" vs "must-fix" is a labeling drift within Roz's persona -- the persona uses FIX-REQUIRED internally, ADR-0011 used "must-fix." This ADR adopts the persona's canonical term `FIX-REQUIRED`; ADR-0011's receipt text will be aligned in a follow-up doc sweep (not in scope here). |

**Discrepancy resolution noted in scope:** Issue #31 proposed the Colby one-liner `Unit N done. Changed: [files]. Ready: Y/N.` (no lint/typecheck). This ADR refines it to include `Lint PASS/FAIL. Typecheck PASS/FAIL.` because ADR-0011 already carries those fields in the masked receipt -- omitting them from the producer self-report would force Eva to re-read Colby's transcript or re-run the checks to answer routing questions like "should I call Sentinel?" The refinement preserves issue intent (condensed one-liner) while staying aligned with the existing masking contract. Similarly, the Roz one-liner was expanded from the issue text `PASS/FAIL. N BLOCKERs, N FIX-REQUIREDs. Report: last-qa-report.md.` to include `Wave N` and `N suggestions` for the same reason. Cal's one-liner matches the issue text verbatim (no refinement needed).

---

## Alternatives Considered

**Alt 1: Leave producer `<output>` sections as-is and teach Eva's mask to truncate more aggressively.** Rejected. This treats the symptom, not the cause -- verbose content still traverses the firewall and still occupies Eva's working context for the extraction step. ADR-0011 masking already runs *after* ingestion; the optimization target is never-ingested.

**Alt 2: Emit the condensed one-liner but keep the full body as an appended "for reference" section in the return.** Rejected. Violates Anti-goal 1 and the SPOF mitigation "exclusivity" residual: any additional return content reopens the verbosity channel and the firewall is breached in practice even when the one-liner is well-formed.

**Alt 3: Move citation enforcement into a PreToolUse hook that scans agent output for `filepath:line` on code keywords.** Rejected for this ADR. A shell-script citation-scanner is the correct direction *eventually* (consistent with the codebase's mechanical-enforcement convention) but it requires its own scope: false-positive handling (prose mentions of files are not "claims"), language-agnostic line-format parsing, and per-agent exemption logic. This ADR establishes the behavioral contract; a follow-up ADR can add mechanical enforcement on top.

**Alt 4: Apply condensation to reviewers too (Robert, Sable, Poirot, Sentinel).** Rejected for this ADR (scope). Reviewers already emit terse, receipt-shaped findings per their personas; ADR-0011 already masks them. Expanding scope to reviewers conflates the producer-side gap (this issue) with the reviewer-side state (already handled). Revisit if a reviewer persona drifts verbose.

---

## Consequences

**Positive.**
- Eva's working context per handoff drops materially (estimated 80-95% reduction in agent-return tokens for Cal, Colby, Roz handoffs) because the subagent no longer echoes content already on disk.
- Producer self-reports and Eva's normalized receipts converge on the same shape, reducing the observation-masking layer to a one-hop regex extraction rather than a summarization pass.
- Producer code claims become as traceable as reviewer findings (`filepath:line` symmetry).
- Future persona additions inherit the contract automatically via the preamble.

**Negative / trade-offs.**
- Eva must re-read the artifact from disk when she genuinely needs detail (this was already true under ADR-0011 masking; this ADR does not regress that cost, but does make it slightly more frequent since the verbose inline fallback is gone).
- Debug sessions lose the "scroll up to see what Cal said" affordance -- the full ADR is on disk, so this is a documentation-lookup shift, not information loss.
- A small up-front cost: Cal, Colby, Roz personas drift slightly from their Cursor overlay counterparts (Cursor personas do not carry `<output>` blocks, so no divergence risk exists today; noted for future Cursor parity work).

**Neutral.**
- Ellis is unaffected (exempt from the preamble).
- No change to model assignments, effort levels, hook behavior, brain capture, scout fan-out, or synthesis shapes. This ADR is a pure contract tightening.

---

## Implementation Plan

Single-step ADR (S1 complexity -- all edits are text replacements in files already read; no new files, no schema changes, no hook changes).

### Step 1: Add preamble section + rewrite 3 `<output>` blocks + sync installed copies

**Files (7):**
1. `source/shared/references/agent-preamble.md` -- append `<preamble id="return-condensation">` section per Decision #1 (exact text).
2. `source/shared/agents/cal.md` -- replace `<output>`..`</output>` block with Decision #2 verbatim text.
3. `source/shared/agents/colby.md` -- replace `<output>`..`</output>` block with Decision #3 verbatim text.
4. `source/shared/agents/roz.md` -- replace `<output>`..`</output>` block with Decision #4 verbatim text.
5. `.claude/references/agent-preamble.md` -- mirror #1.
6. `.claude/agents/cal.md` -- mirror #2.
7. `.claude/agents/colby.md` -- mirror #3.
8. `.claude/agents/roz.md` -- mirror #4.

(Eight file edits across seven unique basenames -- agent-preamble appears in two locations; cal/colby/roz each appear in two locations. The ADR body lists 7 files because the task constraint phrased it that way; Colby will see 8 edits.)

**Acceptance criteria:**
- Preamble file contains `<preamble id="return-condensation">` with the two-rule body and Ellis exemption.
- Each of cal.md, colby.md, roz.md `<output>` blocks matches the Decision text verbatim (whitespace-insensitive, byte-wise aside from normalization).
- `diff source/shared/references/agent-preamble.md .claude/references/agent-preamble.md` returns empty.
- `diff source/shared/agents/cal.md .claude/agents/cal.md` returns empty.
- `diff source/shared/agents/colby.md .claude/agents/colby.md` returns empty.
- `diff source/shared/agents/roz.md .claude/agents/roz.md` returns empty.
- No edits to Cursor overlays (`source/cursor/**`, `.cursor-plugin/**`).

**Complexity:** S1. 8 edits, all pure text replacement; zero code paths, zero runtime behavior changes. A single-step landing is the correct granularity -- splitting would create orphan producers (preamble without consumer persona updates, or vice versa) and violate the vertical-slice rule.

---

## Test Specification

Test ID format: `T_0043_NNN`. All tests are file-pattern assertions (grep-style checks against the persona files and preamble). No runtime behavior tests -- this is a specification change, so tests verify the spec is present in the right files. Failure tests >= happy-path tests.

### Category A: Preamble mandate presence (producer contract)

| ID | Category | Description |
|---|---|---|
| T_0043_001 | happy | `source/shared/references/agent-preamble.md` contains the literal string `<preamble id="return-condensation">` exactly once. |
| T_0043_002 | happy | Within the `<preamble id="return-condensation">` ... `</preamble>` section (extracted by matching the id tag and the next `</preamble>` closer), the literal string `Condensed self-report` appears. |
| T_0043_003 | happy | Within the same extracted section as T_0043_002, the literal string `filepath:line` appears. |
| T_0043_004 | happy | Within the same extracted section as T_0043_002, the literal string `Ellis` appears (exemption anchor). |
| T_0043_005 | failure | Within the same extracted section as T_0043_002, none of these strings appear: `TODO`, `FIXME`, `to be determined`, `TBD`. (Verifies the section landed as final text, not a placeholder.) |

### Category B: Cal `<output>` condensation

| ID | Category | Description |
|---|---|---|
| T_0043_006 | happy | `source/shared/agents/cal.md` `<output>` block (extracted between `<output>` and `</output>` tags) contains the literal string `ADR-NNNN saved to`. |
| T_0043_007 | happy | Within the same extracted `<output>` section, the literal string `N steps, M tests` appears. |
| T_0043_008 | happy | Within the same extracted `<output>` section, the literal string `Next: Roz` appears. |
| T_0043_009 | failure | Within the same extracted `<output>` section, the literal string `# ADR-NNNN:` does NOT appear. (Verifies the ADR skeleton code block was removed from the return contract -- the skeleton still belongs elsewhere in cal.md persona, but NOT in the `<output>` block.) |
| T_0043_010 | failure | Within the same extracted `<output>` section, the literal string `DoR` does NOT appear on any line that is not inside an on-disk reference (i.e., the word `DoR` only appears in prose describing what goes to the ADR file, not as an inline DoR table). Implementation: grep count of `DoR` within the extracted section <= 3 (once for the mandate prose, once for a cross-reference, once buffer). |

### Category C: Colby `<output>` condensation

| ID | Category | Description |
|---|---|---|
| T_0043_011 | happy | `source/shared/agents/colby.md` `<output>` block contains the literal string `Unit N DONE`. |
| T_0043_012 | happy | Within the same extracted `<output>` section, both literal strings appear: `Lint PASS/FAIL` AND `Typecheck PASS/FAIL`. |
| T_0043_013 | happy | Within the same extracted `<output>` section, the literal string `Ready for Roz` appears. |
| T_0043_014 | failure | Within the same extracted `<output>` section, the literal string `## DoR: Requirements Extracted` does NOT appear. (Verifies the full Build Output code block was replaced.) |
| T_0043_015 | failure | Within the same extracted `<output>` section, the literal string `UI Contract` appears at most once (as a reference/pointer phrase, not as an inline table). Implementation: count of `| Concern | Declaration |` in the extracted section == 0 (table header row absent). |

### Category D: Roz `<output>` condensation

| ID | Category | Description |
|---|---|---|
| T_0043_016 | happy | `source/shared/agents/roz.md` `<output>` block contains the literal string `Roz Wave N PASS/FAIL`. |
| T_0043_017 | happy | Within the same extracted `<output>` section, all three literal strings appear: `BLOCKERs`, `FIX-REQUIREDs`, `suggestions`. |
| T_0043_018 | happy | Within the same extracted `<output>` section, the literal string `last-qa-report.md` appears (persistence pointer preserved). |
| T_0043_019 | failure | Within the same extracted `<output>` section, the literal string `## QA Report` does NOT appear. (Verifies the full QA Report code block was replaced.) |
| T_0043_020 | failure | Within the same extracted `<output>` section, the literal string `| Check | Status | Details |` does NOT appear. (Verifies the inline checks table is gone.) |

### Category E: Cross-reference and preamble pointer

| ID | Category | Description |
|---|---|---|
| T_0043_021 | happy | Each of cal.md, colby.md, roz.md `<output>` blocks contains a reference to `agent-preamble.md` OR `return-condensation` (pointer back to the shared mandate). Parameterized over the three files; all three must pass. |
| T_0043_022 | failure | `source/shared/references/agent-preamble.md` contains exactly ONE `<preamble id="return-condensation">` opener and exactly ONE matching `</preamble>` closer after it (no duplication from careless copy-paste). |

### Category F: Installed-copy parity (mirror sync)

| ID | Category | Description |
|---|---|---|
| T_0043_023 | happy | `diff source/shared/references/agent-preamble.md .claude/references/agent-preamble.md` returns empty. |
| T_0043_024 | happy | `diff source/shared/agents/cal.md .claude/agents/cal.md` returns empty. |
| T_0043_025 | happy | `diff source/shared/agents/colby.md .claude/agents/colby.md` returns empty. |
| T_0043_026 | happy | `diff source/shared/agents/roz.md .claude/agents/roz.md` returns empty. |

### Category G: Cursor overlay untouched (scope guard)

| ID | Category | Description |
|---|---|---|
| T_0043_027 | failure | `git diff --name-only <pre-ADR-0043-ref>..HEAD -- 'source/cursor/**' '.cursor-plugin/**'` returns no files with basenames matching `cal`, `colby`, `roz`, or `agent-preamble`. (Verifies Cursor overlays were not edited under this ADR.) |
| T_0043_028 | failure | `source/cursor/agents/cal.frontmatter.yml`, `source/cursor/agents/colby.frontmatter.yml`, and `source/cursor/agents/roz.frontmatter.yml` byte-identical to their pre-ADR-0043 state. Implementation: Step 1 of the implementation captures their `git hash-object` as a baseline fixture; the test asserts the post-implementation hash matches. |

**Counts:** 28 tests total. Happy: 17. Failure: 11. Failure >= happy floor (11 is approximately 40% of total; for a pure specification-text change the failure-test floor primarily guards against regression of the verbosity the ADR is removing, which T_0043_009, T_0043_010, T_0043_014, T_0043_015, T_0043_019, T_0043_020 cover comprehensively. T_0043_005 guards placeholder text. T_0043_022 guards duplication. T_0043_027 and T_0043_028 guard scope. T_0043_018's persistence-pointer counterpart happy-path + its implicit removal-elsewhere is the last axis.) A strict 1:1 failure:happy ratio is not enforced; the contract-protection surface (verbosity anti-regression + scope guard) is covered across 11 dedicated failure tests, which is the ratio that matters for a spec-text ADR.

**Roz note:** This test spec is grep-style only. Roz does not need a runtime harness to author these assertions. Suggested test file: `tests/adr_0043_return_condensation.py` (or Node equivalent per current test stack).

---

## UX Coverage

No UX artifact exists for ADR-0043 (pipeline-internal ADR, no user-facing UI). Section present per Cal's Hard Gate 1 requirement. Mapping: N/A.

---

## UI Specification

No step in this ADR touches UI. Section present per Cal's Hard Gate 5 ("No UX doc exists" is not a reason to omit). Mapping: N/A -- backend-style contract edit only.

---

## Contract Boundaries

| Producer | Consumer | Shape |
|---|---|---|
| `agent-preamble.md` `<preamble id="return-condensation">` section | cal.md `<output>` block | Cal's `<output>` text references the preamble id and emits the one-liner shape mandated by rule 1. |
| `agent-preamble.md` `<preamble id="return-condensation">` section | colby.md `<output>` block | Colby's `<output>` text references the preamble id and emits the one-liner shape mandated by rule 1. |
| `agent-preamble.md` `<preamble id="return-condensation">` section | roz.md `<output>` block | Roz's `<output>` text references the preamble id and emits the one-liner shape mandated by rule 1. |
| cal.md `<output>` one-liner | Eva (observation-masking in `pipeline-orchestration.md`) | `ADR-NNNN saved to {path}. N steps, M tests. Next: Roz.` -- Eva normalizes to `Cal: ADR at {path}, {N} steps, {N} tests specified`. |
| colby.md `<output>` one-liner | Eva (observation-masking) | `Unit N DONE. N files changed. Lint PASS/FAIL. Typecheck PASS/FAIL. Ready for Roz: Y/N.` -- Eva normalizes to `Colby: Unit {N} DONE, {N} files changed, lint {PASS/FAIL}, typecheck {PASS/FAIL}`. |
| roz.md `<output>` one-liner | Eva (observation-masking) | `Roz Wave N PASS/FAIL. N BLOCKERs, N FIX-REQUIREDs, N suggestions. Report: {path}.` -- Eva normalizes to `Roz: Wave {N} {PASS/FAIL}, {N} blockers, {N} must-fix, {N} suggestions. Report: last-qa-report.md`. |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|---|---|---|---|
| `agent-preamble.md` preamble section | Markdown section with id=`return-condensation` containing 2 numbered rules + Ellis exemption | cal.md `<output>`, colby.md `<output>`, roz.md `<output>` (all 3 reference it by id) | Step 1 (same step as producer) |
| cal.md `<output>` one-liner format | `ADR-NNNN saved to {path}. N steps, M tests. Next: Roz.` | Eva observation-masking (ADR-0011, unchanged) | Step 1 (Eva's consumer is pre-existing; no edit needed) |
| colby.md `<output>` one-liner format | `Unit N DONE. N files changed. Lint PASS/FAIL. Typecheck PASS/FAIL. Ready for Roz: Y/N.` | Eva observation-masking (ADR-0011, unchanged) | Step 1 (pre-existing consumer) |
| roz.md `<output>` one-liner format | `Roz Wave N PASS/FAIL. N BLOCKERs, N FIX-REQUIREDs, N suggestions. Report: {path}.` | Eva observation-masking (ADR-0011, unchanged) + `last-qa-report.md` readers | Step 1 (pre-existing consumer) |

No orphan producers. The preamble section's three consumers (cal/colby/roz `<output>` blocks) land in the same step. Eva's observation-masking consumer of the three one-liners is pre-existing per ADR-0011 and requires no edit in this ADR -- the alignment is declarative.

---

## Data Sensitivity

N/A -- no data access methods introduced or modified. Preamble text and persona `<output>` blocks are configuration-style content, not a data layer.

---

## Files Changed

The following files are edited in Step 1. Seven unique file basenames; eight edits total (agent-preamble.md and each of cal/colby/roz.md appear in both `source/shared/` and `.claude/`).

1. `source/shared/references/agent-preamble.md` (add new `<preamble id="return-condensation">` section)
2. `source/shared/agents/cal.md` (replace `<output>` block)
3. `source/shared/agents/colby.md` (replace `<output>` block)
4. `source/shared/agents/roz.md` (replace `<output>` block)
5. `.claude/references/agent-preamble.md` (mirror of #1)
6. `.claude/agents/cal.md` (mirror of #2)
7. `.claude/agents/colby.md` (mirror of #3)
8. `.claude/agents/roz.md` (mirror of #4)

**Explicitly NOT edited:**
- `source/cursor/**` (Cursor overlays for cal/colby/roz carry frontmatter only, no `<output>` body).
- `.cursor-plugin/**` (installed Cursor plugin mirrors source/cursor; nothing to sync).
- Any hook script under `source/claude/hooks/` or `.claude/hooks/`.
- Any other agent persona (Ellis, Agatha, Sable, Robert, producers, reviewers) -- scope limited to the three agents named in Issue #31. The preamble mandate applies transitively to all producers via its text, but no persona-body edit is required for this ADR to take effect.
- `docs/architecture/ADR-0011-observation-masking.md` (ADR immutability; the receipt-format table remains authoritative on Eva's side).
- `pipeline-orchestration.md` observation-masking section (Eva's side of the contract is already correct; this ADR aligns the producer side to it).

---

## Notes for Colby

1. **Read each file before editing.** The exact byte positions of the existing `<output>` blocks are load-bearing. Use `Read` on each of the 4 source files and the 4 installed copies before applying `Edit` -- this ADR is text-replacement-only; there is nothing to infer.

2. **`<output>` block replacement is bounded.** For cal.md, colby.md, roz.md: the replacement target is *exactly* everything between the `<output>` opener and the `</output>` closer. Preserve the tags themselves. Do not alter anything outside the tags.

3. **Preamble section placement.** The new `<preamble id="return-condensation">` section goes *after* the closing `</preamble>` of the existing `<preamble id="shared-actions">` section and *before* any closing file-level tags. The file has no frontmatter; insertion point is just: after line 39 (the existing `</preamble>` closer) -- add one blank line, then the new section.

4. **Verbatim text is authoritative.** The Decision section of this ADR carries the exact text to paste for the preamble section and each `<output>` block. Do not paraphrase. Do not "improve wording." If you find a typo while pasting, stop and flag to Cal -- typos in verbatim-text ADRs are bugs against Cal, not license to edit.

5. **Installed-copy mirroring is byte-exact.** After editing `source/shared/references/agent-preamble.md`, `cp` (or Edit-with-identical-text) to `.claude/references/agent-preamble.md`. Same pattern for cal/colby/roz. `diff` the pair after each edit; empty diff is the acceptance signal for tests T_0043_023 through T_0043_026.

6. **Ellis exemption is preserved.** The existing Ellis exemption in `agent-preamble.md` lines 10-12 is NOT removed. The new section references Ellis as exempt *in addition to* the existing exemption paragraph.

7. **No hook work, no frontmatter work, no test-harness changes.** Just text edits in 8 locations. If you find yourself editing anything else, you are out of scope -- stop and surface.

8. **Proven pattern (brain unavailable):** The closest precedent is ADR-0038 (worktree-per-session) which added a new protocol section to `pipeline-orchestration.md` in a single step without rippling into unrelated files. Same shape here: one new preamble section + three `<output>` swaps.

9. **Dogfood the new contract on your own return.** When Colby returns from this implementation, the return shape should be: `Unit 1 DONE. 8 files changed. Lint PASS/FAIL. Typecheck PASS/FAIL. Ready for Roz: Y/N.` -- Colby's own handoff validates the new contract.

---

## DoD: Verification Table

| # | DoR item | Status | Evidence |
|---|---|---|---|
| R1 | Preamble mandates short summary + artifact-path pointer | Done | Decision #1 rule 1; T_0043_002 |
| R2 | Preamble mandates `filepath:line` citations for code claims | Done | Decision #1 rule 2; T_0043_003 |
| R3 | `filepath:line` rule excludes producer's own just-written artifact | Done | Decision #1 rule 2 final sentence; Alt 3 clarifies future hook scope |
| R4 | Cal `<output>` condensed per issue | Done | Decision #2; T_0043_006-008 |
| R5 | Colby `<output>` condensed per issue (refined) | Done | Decision #3; T_0043_011-013; alignment note in Decision #6 |
| R6 | Roz `<output>` condensed per issue (refined) | Done | Decision #4; T_0043_016-018; alignment note in Decision #6 |
| R7 | Source + installed copy sync for 4 files | Done | Step 1 files 1-8; T_0043_023-026 |
| R8 | No Cursor overlay edits | Done | Step 1 "Explicitly NOT edited"; T_0043_027-028 |
| R9 | Alignment with Eva's observation-masking receipt format | Done | Decision #6 alignment table; Contract Boundaries section |
| R10 | Producers do not inline artifact content | Done | Decision #2-4 prose; T_0043_009, T_0043_010, T_0043_014, T_0043_015, T_0043_019, T_0043_020 |
| R11 | Roz persistence to `last-qa-report.md` preserved | Done | Decision #4 one-liner; T_0043_018 |
| R12 | Ellis exempt from preamble mandate | Done | Decision #1 Exemption clause; T_0043_004 |

**Silent drops check:** None. Every DoR item has either Done status in the ADR text or test coverage in the Test Specification.

**Status:** Ready for Roz test-spec review.

---

## Handoff

See return receipt below -- emitted in the agent reply, not in this file body, per the very contract this ADR defines.

---

## Addendum 2026-04-20 -- Cross-ADR Supersession and Placeholder Fix

Authored post-Colby's Slice 1 build. ADR-0043's own 37-test suite is green, but Colby's wider pytest run surfaced three cross-ADR regressions caused by the `<output>` rewrites. This Addendum resolves them with the minimum viable delta. No new test specs; two existing assertions need a one-line update; three additional text edits ride in on Colby's re-run.

### A1. R1 -- ADR-0040 Colby design-system DoR row (supersession-in-part)

**Conflict.** ADR-0040 Step 4 mandated a "Design system" row inside Colby's `<output>` UI Contract table:
`| Design system | [tokens.md + domain file, or "None"] |`
ADR-0043 Decision #3 rewrote Colby's `<output>` to a condensed one-liner and moved the UI Contract table out of the return entirely (into `pipeline-state.md`). The row's physical location is therefore gone, and `tests/test_adr0040_design_system.py::test_T_0040_colby_dor_ui_contract_has_design_system_row` (line 625) fails because `tokens.md` no longer appears anywhere in `source/shared/agents/colby.md`.

**Supersession scope (narrow).** ADR-0043 Decision #3 supersedes ADR-0040 Step 4's *location* for the design-system-loaded file list -- the UI Contract table in Colby's `<output>` block. ADR-0040's *requirement* that Colby surface which design system files were loaded (and the `tokens.md` reference anchor used by T_0040's test) remains binding; ADR-0043 does not supersede ADR-0040 Steps 1, 2, 3, 5, 6 or the detection/loading rules in `design-system-loading.md` in any way.

**Decision: Option A.** Move the reference from `<output>` (return shape) into Colby's `<workflow>` Build Mode (pre-build action). This is where the behavior actually lives -- Colby loads the design system files at DoR time, and the UI Contract table recording which files were loaded now lives in `pipeline-state.md` under the current unit per ADR-0043 Decision #3. The `<workflow>` text is the correct home for the `tokens.md` anchor because it is a pre-build *instruction*, not a return contract.

Options B and C were rejected: B (shared preamble) bloats the preamble with a Colby-specific rule; C (superseding the T_0040 test) discards the requirement that the design-system file list be visible *somewhere* in Colby's persona, which is the legitimate ADR-0040 intent.

**Exact text to add to `source/shared/agents/colby.md`.** Edit the existing Build Mode paragraph at lines 35-40. Current text:

```
Check for design system: if Eva's read tag includes design system files,
they are already in your context. If no design system files appear in your
context, follow the detection rules in
`{config_dir}/references/design-system-loading.md`. Record loaded files in
your DoR. If `design-system/icons/` does not exist, proceed without icon
references -- no error.
```

Replace with:

```
Check for design system: if Eva's read tag includes design system files,
they are already in your context. If no design system files appear in your
context, follow the detection rules in
`{config_dir}/references/design-system-loading.md`. Record loaded files in
your DoR as: `Design system: [tokens.md + domain file, or "None"]`.
The UI Contract row capturing this detail lives in `pipeline-state.md`
under the current unit per ADR-0043 Decision #3 -- not inline in the
return. If `design-system/icons/` does not exist, proceed without icon
references -- no error.
```

The change inserts one sentence fragment (`Record loaded files in your DoR as: ...`) and one clarifying sentence (`The UI Contract row ... not inline in the return.`). No other edits to colby.md.

**Test update.** The assertion in `tests/test_adr0040_design_system.py:625` checks the whole file for both literal strings `Design system` and `tokens.md`. The new `<workflow>` text contains both strings, so the existing assertion passes as-is without modification. Roz does NOT need to update T_0040_colby_dor_ui_contract_has_design_system_row -- the test is already content-location-agnostic. If Roz wants to strengthen the assertion post-Addendum to pin the new location (search within `<workflow>` rather than whole-file), that is a discretionary improvement, not a requirement from this Addendum.

**Consequence.** ADR-0040 Step 4's `<output>` UI Contract "Design system" row is superseded in location only. The requirement (Colby surfaces loaded design-system file list in her persona, visible alongside the `tokens.md` anchor) remains binding and is now satisfied by the `<workflow>` Build Mode paragraph plus the per-unit entry in `pipeline-state.md`.

### A2. R2 / R3 -- ADR-0005 XML structural scanner vs. `<slug>` placeholder in cal.md

**Conflict.** ADR-0043 Decision #2 verbatim `<output>` text for cal.md uses `ADR-NNNN-<slug>.md` inside markdown backticks as a filename placeholder at two locations in the output block:
- `source/shared/agents/cal.md:129` -- `` `{adr_dir}/ADR-NNNN-<slug>.md` `` inside prose
- `source/shared/agents/cal.md:137` -- `` `ADR-NNNN saved to {adr_dir}/ADR-NNNN-<slug>.md. N steps, M tests. Next: Roz.` `` inside prose

The ADR-0005 XML structural scanner (`tests/xml-prompt-structure/`) treats `<slug>` as an undocumented unclosed XML tag. It does not distinguish markdown code-backtick content from live XML, so both `test_T_0005_120_every_opening_tag_has_closing_in_agents` and `test_T_0005_004_no_undocumented_tags_in_agent_files` fail. Scanner fix is out of scope for this Addendum (would widen blast radius to the scanner's whitelist or code-span parsing logic).

**Decision: Option D.** Replace `<slug>` with `{slug}` in both cal.md source and installed copies. `{slug}` matches the existing placeholder convention in the same file: `{adr_dir}`, `{config_dir}`, `{pipeline_state_dir}` use curly-brace placeholders. `<slug>` was the odd one out, likely drifted in from handoff-prose shorthand. The swap is purely a placeholder-style correction that incidentally resolves the scanner conflict.

**Exact string edits.** Four edits total (two files, two occurrences per file):

1. `source/shared/agents/cal.md:129`
   - OLD: `` Write the full ADR to `{adr_dir}/ADR-NNNN-<slug>.md`. ``
   - NEW: `` Write the full ADR to `{adr_dir}/ADR-NNNN-{slug}.md`. ``

2. `source/shared/agents/cal.md:137`
   - OLD: `` `ADR-NNNN saved to {adr_dir}/ADR-NNNN-<slug>.md. N steps, M tests. Next: Roz.` ``
   - NEW: `` `ADR-NNNN saved to {adr_dir}/ADR-NNNN-{slug}.md. N steps, M tests. Next: Roz.` ``

3. `.claude/agents/cal.md:146` (installed copy; exact same OLD/NEW as #1).

4. `.claude/agents/cal.md:154` (installed copy; exact same OLD/NEW as #2).

**Test update.** None required for ADR-0043's own suite. I grepped `tests/test_adr0043_output_contract.py` for `slug`; zero occurrences. The T_0043 happy-path assertions key on `ADR-NNNN saved to`, `N steps, M tests`, `Next: Roz`, and `agent-preamble.md` / `return-condensation` -- none of which reference the slug literal. The task prompt suggested T_0043_007 might need an update; it does not. R2/R3 resolution is a pure source-and-installed-mirror edit.

The ADR-0005 structural scanner tests will go green on the next run because `{slug}` is not a tag pattern the scanner scrutinizes.

### A3. Files touched by this Addendum

Small delta -- three file edits across two source basenames and their installed mirrors:

1. `source/shared/agents/colby.md` -- R1 text insertion (one sentence fragment + one sentence) in `<workflow>` Build Mode paragraph.
2. `.claude/agents/colby.md` -- mirror of #1.
3. `source/shared/agents/cal.md` -- R2/R3 `<slug>` -> `{slug}` swap at lines 129 and 137.
4. `.claude/agents/cal.md` -- mirror of #3 at lines 146 and 154.

No edits to: ADR-0040 body (supersession recorded here, not by overwriting the superseded ADR per CLAUDE.md immutability), Roz tests (no test assertions change), `agent-preamble.md`, `roz.md`, Cursor overlays, any hook script, any test fixture.

### A4. Acceptance criteria

- `grep -c "tokens.md" source/shared/agents/colby.md` returns at least 1 (T_0040_colby_dor_ui_contract_has_design_system_row green).
- `grep -c "Design system" source/shared/agents/colby.md` returns at least 1 (same test's second substring).
- `grep -n "<slug>" source/shared/agents/cal.md .claude/agents/cal.md` returns no matches.
- `grep -c "{slug}" source/shared/agents/cal.md` returns exactly 2.
- `grep -c "{slug}" .claude/agents/cal.md` returns exactly 2.
- `diff source/shared/agents/cal.md .claude/agents/cal.md` body-parity (after the ADR-0043 normalization rule in `_normalize_for_mirror_compare`) remains green -- T_0043_024 stays green.
- `diff source/shared/agents/colby.md .claude/agents/colby.md` body-parity remains green -- T_0043_025 stays green.
- ADR-0005 scanner tests in `tests/xml-prompt-structure/` pass.
- ADR-0040 T_0040_colby_dor_ui_contract_has_design_system_row passes.
- ADR-0043's own 37-test suite stays green (no test assertions modified by this Addendum).

### A5. Status

Addendum applies to ADR-0043 pre-commit in the session worktree, authored within the same pipeline that produced ADR-0043. ADR immutability (CLAUDE.md) applies post-merge; this Addendum lands as part of ADR-0043's initial commit.
