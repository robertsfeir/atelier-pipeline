## QA Report -- 2026-04-03
*Reviewed by Roz*
*Scope: ADR-0022 Phase 2 Wave 2h -- compaction advisory hook + remediation fixes (P1-P3)*

---

### Verdict: PASS

| Check | Status | Details |
|-------|--------|---------|
| T1: Test suite runs | PASS | `pytest tests/hooks/` completes in 7.71s |
| T1: Test results | PASS | 616 passed, 1 failed (T-0020-068 -- expected pre-existing sync gap, not a regression) |
| T1: No TODO/FIXME/HACK/XXX in changed files | PASS | Zero matches across all 5 changed non-test files |
| T1: Implementation matches spec | PASS | All 22 compaction tests pass; hook behavior verified |
| T2: Compaction tests T-0022-170 through T-0022-191 | PASS | 22/22 |
| T2: Persona remediation tests T-0022-109 to T-0022-126 | PASS | All pass including T-0022-126 (robert-spec, sable-ux have permissionMode: acceptEdits) |
| T2: Cleanup tests | PASS | 37/37 for cleanup + persona combined run |
| T2: Hook behavior trace -- build phase | PASS | Outputs "WAVE BOUNDARY" advisory with /compact suggestion |
| T2: Hook behavior trace -- review/complete/idle phases | PASS | Exits silently, no output |
| T2: Hook behavior trace -- non-Ellis agents | PASS | Exits silently after agent_type check |
| T2: Hook behavior trace -- missing state file | PASS | Exits silently, no error |
| T2: Hook advisory language | PASS | "Do not auto-compact; this is the user's decision." present |
| T2: SKILL.md hook table entry | PASS | Row present with correct source and installed paths |
| T2: SKILL.md settings.json SubagentStop entry | PASS | Correct "type": "prompt" with "if": "agent_type == 'ellis'" condition |
| T2: pipeline-operations.md bullet | PASS | Wave-boundary compact advisory bullet added at line 497 |
| T2: Cursor enforcement-config.json schema | PASS | Full schema intentional -- Cursor monolith reads architecture_dir, product_specs_dir, ux_docs_dir at lines 55-57 of enforce-paths.sh |
| T2: File write check | PASS | Hook contains no >> or tee file write patterns |
| T2: Brain/test-runner check | PASS | Hook contains no agent_capture, pytest, vitest, npm test references |
| T2: Exit 0 always | PASS | All paths exit 0; never blocks |
| T2: CURSOR_PROJECT_DIR fallback | PASS | `${CLAUDE_PROJECT_DIR:-${CURSOR_PROJECT_DIR:-.}}` present |
| T2: Line count <= 35 | PASS | 22 lines |

---

### Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| 2h-1 | Hook detects Ellis SubagentStop during build/implement phase | Implemented | PASS | Advisory fires on both phase values (T-0022-171, T-0022-172) |
| 2h-2 | Hook is purely advisory, never blocks | Implemented | PASS | Always exits 0 (T-0022-178) |
| 2h-3 | Hook is silent in review/complete/idle phases | Implemented | PASS | Empty stdout confirmed (T-0022-173, T-0022-174, T-0022-175) |
| 2h-4 | Hook is silent for non-Ellis agents | Implemented | PASS | Exits immediately after agent_type check (T-0022-181) |
| 2h-5 | Advisory language preserves user agency | Implemented | PASS | "Do not auto-compact; this is the user's decision." confirmed (T-0022-189) |
| 2h-6 | Hook handles missing jq gracefully | Implemented | PASS | `command -v jq` guard at line 8 (T-0022-180) |
| 2h-7 | Hook handles missing state file gracefully | Implemented | PASS | File existence check at line 13 (T-0022-176) |
| 2h-8 | Registered in SKILL.md settings.json template | Implemented | PASS | "type": "prompt" entry with ellis condition (T-0022-185, T-0022-186) |
| 2h-9 | pipeline-operations.md updated with wave-boundary advisory bullet | Implemented | PASS | Bullet added at line 497 (T-0022-187) |
| P1 | robert-spec and sable-ux have permissionMode: acceptEdits | Implemented | PASS | Both frontmatter files contain the field (T-0022-126) |
| P2 | Cursor enforcement-config.json full schema | Implemented | PASS | Full schema correct -- Cursor monolith requires architecture/product/ux dir keys |
| P3 | Dashboard test names / T-0022-185 path fix / cleanup test exclusions | Implemented | PASS | All related tests pass in current suite run |

---

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across changed files: **0 matches**

---

### Known Expected Failure

**T-0020-068** (`test_doc_sync.py::test_T_0020_068_byte_identical`): `source/claude/hooks/prompt-compact-advisory.sh` was updated in this wave but `.claude/hooks/prompt-compact-advisory.sh` still holds the prior stub. This is the sync gap this test is designed to detect. Resolved by running `/pipeline-setup` to sync installed copies. Confirmed not a regression.

---

### Issues Found

**BLOCKER**: None

**FIX-REQUIRED**: None

**Informational -- pre-existing issue not introduced by this wave:**

`skills/pipeline-setup/SKILL.md` line 354 SubagentStop JSON block registers `prompt-brain-capture.sh` as `"type": "command"` with a `"command"` key. The installed `.claude/settings.json` correctly uses `"type": "prompt"` with a `"prompt"` key for that hook. This inconsistency predates Wave 2h and was not introduced by this change. The new `prompt-compact-advisory.sh` entry was correctly written as `"type": "prompt"`. The `prompt-brain-capture.sh` entry in SKILL.md should be corrected in a future pass to match the installed settings format.

---

### Doc Impact: NO

The wave adds one bullet to `pipeline-operations.md` (a reference doc, not user-facing guide). No guide, ADR, or spec documentation requires separate updates for this wave.

---

### Roz's Assessment

Clean wave. The compaction advisory hook is 22 lines, purely advisory, graceful on every failure path (empty stdin, missing jq, missing state file, wrong agent type, unrecognized phase), and correctly follows Retro lesson #003. The PHASE extraction pipeline was traced manually against the real pipeline-state.md format and works correctly. All 22 target tests pass. The Cursor enforcement-config.json full schema is correct -- Cursor's monolith `enforce-paths.sh` reads `architecture_dir`, `product_specs_dir`, and `ux_docs_dir` at lines 55-57, so retaining them in the Cursor config (while removing them from the simplified Claude Code config) is the right call. The robert-spec and sable-ux `permissionMode: acceptEdits` remediation is confirmed by T-0022-126. Pipeline is clear to advance to the review juncture.
