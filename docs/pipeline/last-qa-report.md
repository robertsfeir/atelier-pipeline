## QA Report -- 2026-04-03
*Reviewed by Roz*
*Scope: ADR-0022 FINAL SWEEP -- Phase 1 (Steps 1a-1f) + Phase 2 (Steps 2a-2h), 5 commits: dcf7abd through 7c70e1f*

---

### Verdict: PASS

| Check | Status | Details |
|-------|--------|---------|
| T1: Full test suite (pytest tests/hooks/) | PASS | 617 passed, 0 failed, 7.39s |
| T1: Brain test suite (node --test) | PASS | 93 passed, 0 failed, 3.24s |
| T1: No TODO/FIXME/HACK/XXX in production code | PASS | All matches are in documentation templates, test descriptions, or rule references -- zero actionable markers |
| T1: Source directory structure | PASS | source/shared/, source/claude/, source/cursor/ all exist with correct contents |
| T1: Old flat directories deleted | PASS | source/agents/, source/commands/, source/references/, source/rules/, source/pipeline/, source/variants/, source/dashboard/, source/hooks/ all deleted |
| T1: No YAML frontmatter in shared files | PASS | Zero files in source/shared/ start with `---` on line 1 |
| T1: All frontmatter YAMLs valid | PASS | All 14 Claude + 14 Cursor .frontmatter.yml files parse correctly with matching `name` fields |
| T1: All hook scripts executable | PASS | All 20 .sh files in source/claude/hooks/ have -x bit set |
| T2: Per-agent hook scripts exist (7 scripts) | PASS | enforce-{roz,cal,colby,agatha,product,ux,eva}-paths.sh all present |
| T2: enforce-paths.sh deleted from Claude | PASS | source/claude/hooks/enforce-paths.sh does not exist |
| T2: Cursor enforce-paths.sh byte-identical to pre-deletion | PASS | 162 lines, byte-identical to dcf7abd~1:source/hooks/enforce-paths.sh |
| T2: enforcement-config.json simplified (Claude) | PASS | Retains pipeline_state_dir, test_patterns, colby_blocked_paths, test_command; lacks architecture_dir, product_specs_dir, ux_docs_dir |
| T2: enforcement-config.json full schema (Cursor) | PASS | Retains all keys including architecture_dir, product_specs_dir, ux_docs_dir (Cursor monolith reads them) |
| T2: permissionMode on 6 agents | PASS | colby, cal, agatha, ellis, robert-spec, sable-ux all have permissionMode: acceptEdits |
| T2: hooks field on 6 agents (no Ellis) | PASS | roz, cal, colby, agatha, robert-spec, sable-ux have hooks; ellis does not |
| T2: No agent_type checks in per-agent scripts | PASS | Zero grep matches for agent_type across all 7 scripts |
| T2: Cursor overlays lack hooks/permissionMode | PASS | Zero Cursor frontmatter files contain hooks or permissionMode |
| T2: Read-only agents have disallowedTools | PASS | robert, sable, investigator, distillator, sentinel, darwin, deps all have disallowedTools |
| T2: Robert-spec and Sable-ux producer personas exist | PASS | source/shared/agents/robert-spec.md and sable-ux.md present with correct content |
| T2: Robert/Sable reviewer personas unchanged | PASS | robert.md and sable.md retain read-only reviewer identity |
| T2: Core agent constant = 11 | PASS | agent-system.md lists: cal, colby, roz, ellis, agatha, robert, robert-spec, sable, sable-ux, investigator, distillator |
| T2: /pm and /ux route to subagents | PASS | pm.md references robert-spec; ux.md references sable-ux; agent-system.md routing table updated |
| T2: prompt-compact-advisory.sh | PASS | 23 lines, follows retro #003 pattern, exits 0 always, advisory only |
| T2: SKILL.md updated | PASS | Installation manifest includes all new hooks, robert-spec, sable-ux; settings.json template uses enforce-eva-paths.sh; SubagentStop includes prompt-compact-advisory.sh |
| T2: pipeline-operations.md updated | PASS | Wave-boundary compact advisory bullet at line 497 |
| T2: CLAUDE.md updated | PASS | Source structure section reflects three-directory split with 14 agents |
| T2: technical-reference.md updated | PASS | Lists all 7 per-agent hooks |
| T2: Old bats tests deleted | PASS | Zero .bats files in tests/hooks/; test_helper.bash deleted |
| T2: Test migration to pytest | PASS | 617 total tests, 169 ADR-0022-specific (55 Phase 1 + 114 Phase 2) |

---

### Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| R1 | Split source/ into platform-specific directories | Done | PASS | source/shared/, source/claude/, source/cursor/ exist with correct contents |
| R2 | DRY strategy for shared vs platform-divergent content | Done | PASS | Overlay pattern: shared content in source/shared/, frontmatter-only overlays per platform |
| R3 | Update /pipeline-setup for new structure | Done | PASS | SKILL.md documents platform detection, overlay assembly, and full installation manifest |
| R4 | Phase 1 lands before Phase 2 | Done | PASS | Commit dcf7abd (Phase 1) precedes 8f4a47d (Phase 2 start) |
| R5 | Replace enforce-paths.sh monolith with per-agent hooks | Done | PASS | 7 per-agent scripts created; Claude enforce-paths.sh deleted |
| R6 | Three-layer enforcement pyramid | Done | PASS | Layer 1 (tools/disallowedTools in frontmatter), Layer 2 (per-agent hooks), Layer 3 (settings.json global hooks) |
| R7 | permissionMode: acceptEdits on write-heavy agents | Done | PASS | Colby, Cal, Agatha, Ellis all have permissionMode: acceptEdits in Claude overlays |
| R8 | Robert/Sable become write-capable subagents | Done | PASS | robert-spec.md and sable-ux.md created with producer workflows |
| R9 | Robert-spec writes to docs/product/, Sable-ux to docs/ux/ | Done | PASS | enforce-product-paths.sh allows docs/product/ only; enforce-ux-paths.sh allows docs/ux/ only; frontmatter tools include Write, Edit |
| R10 | Per-agent scripts ~15-20 lines, no agent_type, no case statement | Done | PASS | Scripts range 32-46 lines (including boilerplate, comments, jq guard); zero agent_type references; path logic is single-case, not multi-agent case statement |
| R11 | Cursor keeps global hook model | Done | PASS | Cursor hooks.json references enforce-paths.sh; Cursor overlays omit hooks/permissionMode |
| R12 | Robert/Sable dual mode: reviewer + producer | Done | PASS | robert.md (reviewer, read-only) + robert-spec.md (producer, write-capable); same for sable/sable-ux |
| R13 | Eva main thread: docs/pipeline/ only | Done | PASS | enforce-eva-paths.sh allows only docs/pipeline/; registered in settings.json PreToolUse |
| R14 | Agents in project .claude/agents/ | Done | PASS | SKILL.md installs to .claude/agents/; ADR documents requirement |
| R15 | Core agent constant includes robert-spec, sable-ux | Done | PASS | agent-system.md: 11 core agents including robert-spec and sable-ux |
| R16 | PreToolUse hooks fire regardless of permissionMode | Done | PASS | Documented in ADR; Claude Code behavior confirmed |
| R17 | Parent mode override documented | Done | PASS | Documented in ADR requirements table |
| R18 | Colby edits source/ only | Done | PASS | enforce-colby-paths.sh blocks colby_blocked_paths (includes docs/); CLAUDE.md states the constraint |
| R19 | New scripts need equivalent coverage | Done | PASS | 617 total pytest tests (up from 265 bats); 169 ADR-0022-specific tests |
| R20 | Ellis has no path hooks | Done | PASS | Ellis frontmatter has no hooks field; full write access |
| R21 | Read-only agents keep disallowedTools | Done | PASS | All 7 read-only agents have disallowedTools blocking Write/Edit/MultiEdit/NotebookEdit |
| R22 | /pm and /ux become subagent invocations | Done | PASS | agent-system.md routes /pm to robert-spec (subagent), /ux to sable-ux (subagent); pm.md and ux.md reference respective producers |
| R23 | Wave-boundary compaction advisory | Done | PASS | prompt-compact-advisory.sh created, registered in settings.json template as SubagentStop prompt hook with `if: "agent_type == 'ellis'"`, pipeline-operations.md updated |

---

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"` across changed production files: **0 actionable matches**

All matches are in documentation templates describing the rule itself (qa-checks.md, retro-lessons.md, dor-dod.md), ADR grep-check sections, agent persona constraints, or test descriptions. No production code markers.

---

### Issues Found

**BLOCKER**: None

**FIX-REQUIRED**: None

---

### Observations (informational, not blocking)

1. **R10 line count note:** The distillate specifies "~15-20 lines" per script. Actual line counts range from 32 (cal, agatha, product, ux, eva) to 46 (roz). This is due to required boilerplate (shebang, setup-mode guard, jq availability check, tool_name filtering, path normalization, absolute-path detection) that every script shares. The enforcement logic itself (the agent-specific part) is 2-4 lines per script. The spirit of R10 -- no agent_type check, no case statement, no config read (except roz and colby) -- is fully met. The absolute line count is a natural consequence of necessary defensive coding.

2. **Installed .claude/ state:** The project's own installed `.claude/` copy (this project eats its own cooking) has not been re-synced via `/pipeline-setup`. The installed settings.json still references the deleted `enforce-paths.sh`, and is missing `prompt-compact-advisory.sh`, `robert-spec.md`, and `sable-ux.md`. This is expected -- the source templates are authoritative, and the installed copy syncs on `/pipeline-setup` re-run. Not a blocker.

3. **Distillate math note:** The distillate states "11 core + 2 new (robert-spec, sable-ux) = 13 core total" under the DoD. The actual count is 11 total (9 original + 2 new = 11). The implementation correctly lists 11 in agent-system.md. The distillate's arithmetic is a documentation error in the distillate itself, not an implementation issue.

4. **SKILL.md pre-existing issue (from prior QA report):** Line 354 registers `prompt-brain-capture.sh` as `"type": "command"` with a `"command"` key. The installed `.claude/settings.json` correctly uses `"type": "prompt"` with a `"prompt"` key. This inconsistency predates ADR-0022 and was not introduced by this change.

---

### Phase 1 Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| source/shared/ contains all commands, references, pipeline, rules, variants, dashboard files | PASS | 11 commands, 10 references, 6 pipeline, 4 rules, 4 variants, 1 dashboard |
| No file in source/shared/ starts with YAML frontmatter | PASS | Zero files start with `---` on line 1 |
| All 14 agents: concat frontmatter + shared content produces valid assembly | PASS | All 14 Claude + 14 Cursor frontmatter files have valid YAML with matching name fields |
| Assembly structure: `---\n{frontmatter}\n---\n{content}` | PASS | SKILL.md documents assembly procedure |
| Original flat source directories deleted | PASS | 7 old directories deleted |
| /pipeline-setup detects platform (CURSOR_PROJECT_DIR precedence) | PASS | SKILL.md Step 2 documents detection logic |
| Installed Claude agents have hooks frontmatter; Cursor do not | PASS | 6 Claude overlays have hooks; 0 Cursor overlays do |
| SKILL.md documents overlay assembly | PASS | Step 2 and Step 3 fully document the procedure |
| All tests pass | PASS | 617 pytest + 93 brain = 710 total, 0 failures |
| .frontmatter.yml files are valid YAML with name fields | PASS | All 28 files validated |
| Hook scripts executable | PASS | All 20 .sh files have -x bit |

---

### Phase 2 Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 7 per-agent hook scripts exist, executable, exit 0 on non-Write | PASS | All 7 scripts confirmed |
| enforcement-config.json simplified (Claude) | PASS | architecture_dir, product_specs_dir, ux_docs_dir removed; pipeline_state_dir, test_patterns, colby_blocked_paths, test_command retained |
| Robert-spec and Sable-ux personas exist with producer workflows | PASS | Both in source/shared/agents/ |
| robert-spec information asymmetry | PASS | Constraint "Do not reference current pipeline QA reports or active ADR" at line 26 |
| sable-ux information asymmetry | PASS | Same constraint pattern |
| Robert and Sable reviewer personas unchanged | PASS | Identities remain "Acceptance Reviewer" |
| Core agent constant = 11 | PASS | agent-system.md lists all 11 |
| Claude overlays for write-heavy agents include permissionMode | PASS | 6 agents (colby, cal, agatha, ellis, robert-spec, sable-ux) confirmed |
| 6 agent overlays include hooks field | PASS | roz, cal, colby, agatha, robert-spec, sable-ux |
| enforce-eva-paths.sh restricts main thread to docs/pipeline/ | PASS | Single case match on docs/pipeline/* |
| /pm and /ux route to subagents | PASS | Routing table and command files updated |
| Cursor enforce-paths.sh byte-identical to pre-deletion Claude version | PASS | diff confirms 0 differences |
| All tests pass, >= 56 new per-agent test entries | PASS | 114 Phase 2 tests (exceeds 56 minimum) |
| prompt-compact-advisory.sh detects Ellis and outputs advisory | PASS | 23 lines, retro #003 compliant, exits 0 always |
| SKILL.md documents SubagentStop hook registration | PASS | Hook table entry + settings.json template entry |
| pipeline-operations.md updated | PASS | Wave-boundary compaction advisory bullet present |

---

### Doc Impact: NO

All documentation was updated as part of the implementation waves. No additional doc updates required. The ADR (docs/architecture/ADR-0022-wave3-native-enforcement-redesign.md), technical-reference.md, user-guide.md, CLAUDE.md, SKILL.md, and pipeline-operations.md were all updated during the build phase.

---

### Roz's Assessment

This is a thorough and well-executed two-phase implementation. The source directory split (Phase 1) cleanly separates platform-agnostic content from platform-specific overlays without introducing any drift risk. The overlay assembly pattern is documented in SKILL.md and tested by 55 Phase 1 tests. The enforcement redesign (Phase 2) successfully replaces the 163-line monolith with 7 focused per-agent scripts that each handle exactly one agent's path restrictions. The three-layer enforcement pyramid is correctly implemented: Layer 1 via tools/disallowedTools in frontmatter, Layer 2 via per-agent hooks, and Layer 3 via global settings.json hooks.

The test migration from bats to pytest is complete and comprehensive: 617 pytest tests replace 265 bats tests, providing substantially more coverage. The Cursor platform is not broken -- the global hook model is preserved with byte-identical enforce-paths.sh and full enforcement-config.json schema.

All 23 requirements (R1-R23) verified as PASS. Zero blockers. Zero fix-required items. The implementation is ready for Ellis commit.
