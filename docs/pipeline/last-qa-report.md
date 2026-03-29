# QA Report -- 2026-03-29 (ADR-0012)
*Reviewed by Roz*

## Verdict: FAIL

Two blockers, one fix-required. Core implementation (Steps 1-4) is solid. Issues are in cross-ADR consistency and Step 5 documentation updates.

---

## Test-by-Test Verification (34 tests)

### Step 1: Compaction Strategy Update (source/references/pipeline-operations.md)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0012-001 | Happy | PASS | Lines 309-311: "When the Compaction API is active (`context_management.edits` enabled)..." |
| T-0012-002 | Happy | PASS | Lines 321-323: "Path-scoped rules survive compaction... re-injected from disk on every turn (ADR-0004 design)" |
| T-0012-003 | Happy | PASS | Lines 324-327: "Eva writes pipeline-state.md at every phase transition (existing behavior). This is the primary compaction safety net..." |
| T-0012-004 | Happy | PASS | Lines 328-331: "Brain captures provide a secondary recovery path (when `brain_available: true`)" |
| T-0012-005 | Regression | PASS | Line 315: "Between major phases: start fresh subagent sessions. Pipeline-state.md is the recovery mechanism." |
| T-0012-006 | Regression | PASS | Line 316: "Within Colby+Roz interleaving: Each unit is a separate subagent invocation (fresh context)." |
| T-0012-007 | Regression | PASS | Lines 332-333: "Agent Teams Teammates have inherently fresh context per task." |
| T-0012-008 | Regression | PASS | Line 334: "Never carry Roz reports in Eva's context. Read the verdict only." |
| T-0012-009 | Failure | PASS | No "60%" reference. Text says "Eva does not need to track context usage percentage" (negation of old trigger). |
| T-0012-010 | Boundary | PASS | Lines 318-320: "For very large pipelines (20+ agent handoffs)... quality signal, not a context-counting heuristic." |

### Step 2: Context Cleanup Advisory (source/rules/pipeline-orchestration.md)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0012-011 | Happy | PASS | Lines 488-490: "Server-side compaction (Compaction API) manages Eva's context window automatically" |
| T-0012-012 | Happy | PASS | Line 490: "Eva does not suggest session breaks based on handoff counts." |
| T-0012-013 | Happy | PASS | Line 503: "This is advisory, not mandatory -- Eva never forces a session break. The user decides." |
| T-0012-014 | Happy | PASS | Lines 492-498: "(a) Response quality visibly degrades" and "(b) The pipeline spans multiple days" |
| T-0012-015 | Failure | PASS | No "10 major" reference in pipeline-orchestration.md source file. Old count-based threshold replaced. |
| T-0012-016 | Failure | PASS | No "estimated context" or percentage references in pipeline-orchestration.md source file. |
| T-0012-017 | Regression | PASS | Lines 500-502: "Pipeline state is preserved in `{pipeline_state_dir}/pipeline-state.md` and `{pipeline_state_dir}/context-brief.md`" |

### Step 3: PreCompact Hook Script (source/hooks/pre-compact.sh)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0012-018 | Happy | PASS | File exists, permissions `-rwxr-xr-x` |
| T-0012-019 | Happy | PASS | Line 17: `echo "<!-- COMPACTION: $(date -u +%Y-%m-%dT%H:%M:%SZ) -->" >> "$STATE_FILE"` |
| T-0012-020 | Happy | PASS | Lines 14 and 19: two exit 0 paths (early return + final). No non-zero exits. |
| T-0012-021 | Failure | PASS | Lines 13-15: `if [ ! -f "$STATE_FILE" ]; then exit 0; fi` |
| T-0012-022 | Failure | PASS | Grep for `agent_capture`, `agent_search`, test commands: only comment matches. Script body is `echo >> file`. |
| T-0012-023 | Boundary | PASS | `wc -l` = 19 lines. Under 20. |
| T-0012-024 | Regression | PASS | `git diff HEAD` on enforce-paths.sh, enforce-sequencing.sh, enforce-git.sh, warn-dor-dod.sh: all empty (unchanged). |
| T-0012-025 | Security | PASS | Only write target: `$STATE_FILE` -> `docs/pipeline/pipeline-state.md`. No other file paths. |

### Step 4: Pipeline-Setup Skill (skills/pipeline-setup/SKILL.md)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0012-026 | Happy | PASS | Line 173: pre-compact.sh in Step 3a manifest. Lines 211-215: PreCompact in settings.json template. |
| T-0012-027 | Happy | PASS | Line 173: listed alongside enforce-paths.sh, enforce-sequencing.sh, enforce-git.sh, warn-dor-dod.sh in Step 3a. |
| T-0012-028 | Happy | PASS | Line 331: "Compaction API: PreCompact hook installed for pipeline state preservation" |
| T-0012-029 | Failure | PASS | pre-compact.sh installed unconditionally in Step 3a -- not gated behind opt-in (unlike Sentinel Step 6a / Agent Teams Step 6b). |
| T-0012-030 | Regression | PASS | Steps 6a (Sentinel), 6b (Agent Teams), brain setup offer all preserved unchanged. |

### Step 5: Documentation Updates (docs/guide/)

| ID | Category | Status | Evidence |
|----|----------|--------|----------|
| T-0012-031 | Happy | PASS | technical-reference.md lines 842-850: Compaction API, server-side compaction, PreCompact hook, quality-based advisory. |
| T-0012-032 | Happy | PASS | user-guide.md line 390: "Server-side compaction (Compaction API) manages context automatically... Eva no longer suggests session breaks based on handoff counts." |
| T-0012-033 | Regression | PASS | Tech ref line 846 + user guide line 390: both mention pipeline-state.md and context-brief.md as recovery mechanisms. |
| T-0012-034 | Regression | **FAIL** | Tech ref line 848: has ADR-0004 path-scoped resilience. User guide: NO reference to ADR-0004 or path-scoped compaction resilience anywhere in the advisory section. |

**Summary: 33 PASS, 1 FAIL (T-0012-034)**

---

## Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| R1 | Enable Compaction API for Eva's session | Step 1 + Step 4 | YES | Strategy docs + setup hook registration |
| R2 | Remove manual `/compact` handling | Step 1 + Step 2 | YES | 60% trigger + 10-handoff threshold removed from their source files |
| R3 | pipeline-state.md remains cross-session recovery | All steps | YES | Preserved in all modified files |
| R4 | Document Eva's state preservation | Step 1 + Step 3 | YES | Phase-transition writes + PreCompact hook |
| R5 | Document what Eva writes to pipeline-state.md | Step 1 | YES | Existing behavior documented as primary safety net |
| R6 | Update context cleanup advisory | Step 2 | YES | Handoff-counting -> quality-based assessment |
| R7 | PreCompact hook | Step 3 | YES | 19 lines, exit 0 always, lightweight |
| R8 | Changes target source/ only (not .claude/) | All | YES | `git diff --name-only HEAD -- .claude/` = empty |
| R9 | Non-code ADR | All | YES | Rules, docs, one shell script |
| R10 | Relationship to #10 documented | ADR context | N/A | In ADR prose, not implementation files |

## Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across all changed files: **0 matches.**

---

## Issues Found

### BLOCKER-1: Observation masking trigger point 4 re-introduces removed "10 major handoffs" threshold

**File:** `source/references/pipeline-operations.md`, lines 409-411

```
4. **At the context cleanup advisory threshold** (10 major handoffs): Apply
   aggressive masking -- preserve only pipeline-state.md content,
   context-brief.md, and the current phase's active tool outputs.
```

The observation masking protocol (ADR-0011, added in the same diff) uses "10 major handoffs" as a trigger -- the exact count-based threshold that ADR-0012 removes from both pipeline-orchestration.md and the Compaction Strategy section. After ADR-0012, the context cleanup advisory no longer has a handoff-count threshold. Trigger point 4 references a threshold that does not exist.

**Fix:** Reword trigger point 4 to align with the quality-based advisory. For example: "At the quality-based advisory threshold (20+ agent handoffs with visible degradation, per Compaction Strategy)."

### BLOCKER-2: Technical reference file tree and counts not updated for pre-compact.sh

**File:** `docs/guide/technical-reference.md`, lines 149-153, 109, 165, 862

- The hooks/ file tree (lines 149-153) lists 4 files. Missing: `warn-dor-dod.sh` (pre-existing gap) and `pre-compact.sh` (new).
- Line 109: "38 files" -- does not account for pre-compact.sh.
- Line 165: "38 files across 6 directories" -- should be updated.
- Line 862: "35 files... 4 enforcement hooks" -- should be 5 hooks.

The SKILL.md correctly says "40 mandatory files across 7 directories" and lists 6 hook files. The technical reference is out of sync.

**Fix:** Add `warn-dor-dod.sh` and `pre-compact.sh` to the file tree. Update all file counts to match SKILL.md (40 mandatory files, 6 hook files).

### FIX-REQUIRED-1: User guide missing ADR-0004 path-scoped compaction resilience (T-0012-034)

**File:** `docs/guide/user-guide.md`, line 390

The context cleanup advisory paragraph does not mention that path-scoped rules survive compaction (ADR-0004 design). The tech reference has this (line 848). T-0012-034 requires both docs to preserve this reference. The user guide never had it before, but the test explicitly says "Both docs preserve ADR-0004 path-scoped rules compaction resilience reference."

**Fix:** Add one sentence: "Path-scoped rules (pipeline-orchestration.md, pipeline-models.md) survive compaction because Claude Code re-injects them from disk on every turn (ADR-0004 design)."

---

## Doc Impact: YES

- `docs/guide/technical-reference.md` -- file tree and counts need updating (BLOCKER-2)
- `docs/guide/user-guide.md` -- one sentence addition for ADR-0004 reference (FIX-REQUIRED-1)

## Roz's Assessment

The core implementation is well-executed. Steps 1 through 4 are thorough and precise:

- The Compaction Strategy rewrite in `pipeline-operations.md` covers all acceptance criteria while preserving every required existing bullet.
- The Context Cleanup Advisory in `pipeline-orchestration.md` cleanly replaces count-based thresholds with quality-based assessment while preserving recovery mechanisms and the "never forces" stance.
- The PreCompact hook is exactly the right weight: 19 lines, two exit-0 paths, no heavy operations, correct `CLAUDE_PROJECT_DIR` usage with PWD fallback. Follows the warn-dor-dod.sh pattern faithfully.
- The SKILL.md correctly adds the hook to the manifest, settings.json template, and summary, with updated file counts.

The three issues are all fixable with small text edits. BLOCKER-1 is a cross-ADR consistency issue between ADR-0011 (observation masking) and ADR-0012 (compaction) that was introduced because both were implemented in the same working session. BLOCKER-2 and FIX-REQUIRED-1 are Step 5 documentation gaps.

### DoD Notes

- **Recurring pattern:** File count inconsistencies between SKILL.md and technical-reference.md. The SKILL.md is the installation source of truth; the technical reference must be kept in sync. Consider adding a cross-reference check to future doc reviews.
- **Cross-ADR dependency:** The observation masking protocol (ADR-0011) and compaction API integration (ADR-0012) share the concept of "context cleanup advisory threshold." When one ADR changes the threshold definition, the other must be updated. This interaction should be captured as a brain insight.
- **Pre-existing gap:** The technical reference file tree was already missing `warn-dor-dod.sh` before ADR-0012. This was not caught in prior QA because it was not in scope. Now that a new hook is being added, the gap is visible.
