---
source: docs/architecture/ADR-0022-wave3-native-enforcement-redesign.md
original_tokens: "~22000"
compression_ratio: "58%"
token_estimate: "~9200"
date: "2026-04-03"
downstream_consumer: "Roz (test authoring), Colby (implementation)"
status: "Proposed"
---

# ADR-0022 Distillate: Wave 3 -- Native Enforcement Redesign

## DoR: Source Analysis

**Sources:** Brain (Cal/Eva architecture decisions), context-brief.md (Wave 3 scope), enforce-paths.sh (163-line monolith), agent persona files (12 core agents), ADR-0020/ADR-0019 (predecessors), retro-lessons.md (Lesson #003, #005)

**Spec challenge verified:** Claude Code frontmatter hooks receive identical input schema to global PreToolUse hooks (tool_name, tool_input.file_path). Confidence: yes -- confirmed against Claude Code documentation.

**SPOF: Platform detection in /pipeline-setup.** Bug = wrong frontmatter overlay selected (Claude Code gets Cursor hooks or vice versa). Graceful degradation: Layer 3 global hooks + Layer 1 disallowedTools continue; Layer 2 per-agent enforcement fails, system degrades to Wave 2 behavior (not zero enforcement).

---

## Requirements (R1-R23)

| # | Requirement | Source |
|---|-------------|--------|
| R1 | Split `source/` into platform-specific directories | Brain Decision 5 |
| R2 | DRY strategy for shared vs platform-divergent content | Brain Decision 5 |
| R3 | Update /pipeline-setup for new structure | Brain Decision 4 |
| R4 | Phase 1 lands BEFORE Phase 2 (sequential, user-mandated) | Brain Decision 4 |
| R5 | Replace enforce-paths.sh monolith with per-agent frontmatter hooks | Brain Decision 2 |
| R6 | Three-layer enforcement pyramid: Layer 1 tools/disallowedTools, Layer 2 frontmatter hooks, Layer 3 global hooks | Brain Decision 2 |
| R7 | Add `permissionMode: acceptEdits` on write-heavy agents (Colby, Cal, Agatha, Ellis) | Brain Decision 1 |
| R8 | Robert/Sable become write-capable subagents for spec/UX production | Brain Decision 1 |
| R9 | Robert-spec writes to docs/product/, Sable-ux writes to docs/ux/ | Brain Decision 2 |
| R10 | Per-agent scripts ~15-20 lines, no agent_type check, no case statement | Brain Decision 2 |
| R11 | Cursor keeps global hook model (no frontmatter hooks at runtime) | Brain Decision 3 |
| R12 | Robert/Sable dual mode: two persona files each (reviewer + producer) | Brain Decision 3 |
| R13 | Eva main thread: docs/pipeline/ write access only | Brain Decision 3 |
| R14 | Agents MUST be in project .claude/agents/ (plugin native agents/ loses frontmatter) | Brain Decision 3 |
| R15 | Core agent constant: clarify robert-spec and sable-ux naming | Brain Decision 3 |
| R16 | PreToolUse hooks fire regardless of permissionMode | Brain Decision 3 |
| R17 | Parent mode override: user's auto/bypassPermissions overrides subagent permissionMode | Brain Decision 3 |
| R18 | Colby edits source/ only, never .claude/ | CLAUDE.md |
| R19 | 265 existing bats tests; new scripts need equivalent coverage | Brain Decision 3 |
| R20 | Ellis has no path hooks (full write access, sequencing at Layer 3) | Brain Decision 2 |
| R21 | Read-only agents keep disallowedTools blocking Write/Edit/MultiEdit/NotebookEdit | Brain Decision 2 |
| R22 | /pm and /ux become subagent invocations for spec/UX production | Brain Decision 3 |
| R23 | Wave-boundary compaction advisory: SubagentStop prompt hook detects Ellis per-wave commit and advises Eva to suggest /compact | User request 2026-04-03 |

---

## Decision: Two Sequential Phases

### Phase 1: Source Directory Split + Install Verification (6 steps)

**Overlay pattern:** Shared content body in `source/shared/`; platform-specific frontmatter overlays in `source/claude/agents/` and `source/cursor/agents/`; assembly at install time.

**Directory structure:**

```
source/shared/
  agents/                     # Content bodies, no YAML frontmatter
  commands/, references/, pipeline/, rules/, variants/, dashboard/
source/claude/
  agents/*.frontmatter.yml    # Claude Code frontmatter only
  hooks/                      # Claude Code hooks (enforce-paths.sh deleted in Phase 2)
source/cursor/
  agents/*.frontmatter.yml    # Cursor frontmatter (omits hooks, permissionMode)
  hooks/hooks.json
```

**Assembly during /pipeline-setup:**

1. Read `source/{claude|cursor}/agents/{name}.frontmatter.yml`
2. Read `source/shared/agents/{name}.md` (body)
3. Concatenate: `---\n` + frontmatter + `---\n` + body
4. Write to target project

**Example:** `source/claude/agents/colby.frontmatter.yml` + `source/shared/agents/colby.md` = assembled `.claude/agents/colby.md` with identical frontmatter + content

**What does NOT move:** `.cursor-plugin/` (plugin distribution) stays as-is.

#### Steps 1a-1f:

| Step | What | Files |
|------|------|-------|
| 1a | Move commands/, references/, pipeline/, rules/, variants/, dashboard/ to source/shared/ | ~50 files, all identical across platforms |
| 1b | Split agents: extract YAML frontmatter to source/claude/agents/, source/cursor/agents/; content to source/shared/agents/ | 12 agents, 24 frontmatter files created, 12 content files, original source/agents/ deleted |
| 1c | Move hooks to source/claude/hooks/ (enforcement-config.json kept; enforce-paths.sh kept in Phase 1, deleted Phase 2) | ~12 hooks + config |
| 1d | Update /pipeline-setup: detect platform (CURSOR_PROJECT_DIR env var), assemble from correct overlay directory | 1 file modified |
| 1e | Update test_helper.bash: HOOKS_DIR from source/hooks/ -> source/claude/hooks/ | 1 file, cascades to all hook tests |
| 1f | Verify file count, test suite passes (bats tests/hooks/ green) | N/A |

#### Phase 1 Acceptance Criteria:

- `source/shared/` directories contain all commands, references, pipeline, rules, variants, dashboard files
- No file in `source/shared/` starts with YAML frontmatter (`grep -rl "^---" source/shared/` returns zero)
- All 12 agents: concatenating claude frontmatter + shared content produces byte-identical output to original pre-split agent files
- Assembly output has structure: `---\n{frontmatter}\n---\n{content}` (trailing newline after closing `---` is critical -- missing newline = invalid YAML)
- Original flat `source/{agents,commands,references,rules,pipeline,variants,dashboard}/` directories deleted (content moved to source/shared/, source/claude/, source/cursor/)
- /pipeline-setup correctly detects platform and installs from correct overlay directory (CURSOR_PROJECT_DIR precedence over CLAUDE_PROJECT_DIR)
- Installed Claude Code agents have `hooks:` frontmatter; installed Cursor agents do not
- SKILL.md documents platform detection and overlay assembly procedure
- All existing tests pass (265 bats tests)
- `.frontmatter.yml` files are valid YAML; each has `name:` field matching expected agent name
- Hook scripts in source/claude/hooks/ are executable (-x bit)

---

### Phase 2: Enforcement Redesign (8 steps)

#### Three-Layer Enforcement Pyramid

**Layer 1: tools/disallowedTools (zero cost, runtime)**

| Agent | Model | Tools Field |
|-------|-------|-------------|
| Cal | Read, Write, Edit | `tools: Read, Write, Edit, Glob, Grep, Bash, Agent(roz)` |
| Colby | Read, Write, Edit, MultiEdit | `tools: Read, Write, Edit, MultiEdit, Glob, Grep, Bash, Agent(roz, cal)` |
| Roz | Read, Bash (test-scoped) | `disallowedTools: Agent, Edit, MultiEdit, NotebookEdit` |
| Ellis | Full write | `disallowedTools: Agent, NotebookEdit` |
| Agatha | Write: docs/ | `disallowedTools: Agent, NotebookEdit` |
| Robert (reviewer) | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| Robert-spec (producer) | Write: docs/product/ | `tools: Read, Write, Edit, Glob, Grep, Bash` |
| Sable (reviewer) | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| Sable-ux (producer) | Write: docs/ux/ | `tools: Read, Write, Edit, Glob, Grep, Bash` |
| Investigator, Distillator, Sentinel, Darwin, Deps | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |

**Layer 2: Per-agent frontmatter hooks (Claude Code only)**

| Agent | Script | Enforces |
|-------|--------|----------|
| Roz | enforce-roz-paths.sh | Only test files (test_patterns) + docs/pipeline/ |
| Cal | enforce-cal-paths.sh | Only docs/architecture/ |
| Colby | enforce-colby-paths.sh | Block colby_blocked_paths |
| Agatha | enforce-agatha-paths.sh | Only docs/ |
| Robert-spec | enforce-product-paths.sh | Only docs/product/ |
| Sable-ux | enforce-ux-paths.sh | Only docs/ux/ |
| Ellis | (none) | Full access; sequencing at Layer 3 |

Each script: ~15-20 lines, hardcoded paths (no agent_type check, no case statement), exits 0 if not Write/Edit operation

**Layer 3: Global hooks in settings.json (cross-cutting)**

| Hook | Status |
|------|--------|
| enforce-paths.sh | **DELETED** (replaced by Layer 2) |
| enforcement-config.json | **SIMPLIFIED**: remove `architecture_dir`, `product_specs_dir`, `ux_docs_dir`; retain `pipeline_state_dir` (enforce-sequencing.sh, enforce-pipeline-activation.sh), `test_patterns`, `colby_blocked_paths`, `test_command` |
| enforce-sequencing.sh | KEPT (cross-cutting: phase order) |
| enforce-pipeline-activation.sh | KEPT (cross-cutting: pipeline activation) |
| enforce-git.sh | KEPT (cross-cutting: git operations) |
| Lifecycle/telemetry hooks | KEPT (non-enforcement) |

#### Steps 2a-2h:

| Step | What | Files |
|------|------|-------|
| 2a | Create 7 per-agent hook scripts (enforce-{roz,cal,colby,agatha,product,ux}-paths.sh); create enforce-eva-paths.sh for main thread; update enforcement-config.json | 8 files created, 1 modified |
| 2b | Write comprehensive bats tests for 7 scripts; validate against 265-test baseline | New test files |
| 2c | Create Robert-spec and Sable-ux personas; dual-mode design (reviewer + producer); update core agent constant in agent-system.md | 2 persona files created; 1 file modified |
| 2d | Add `permissionMode: acceptEdits` to claude overlays (Colby, Cal, Agatha, Ellis) | 4 frontmatter files modified |
| 2e | Add `hooks:` frontmatter field to 7 agent overlays (roz, cal, colby, agatha, robert-spec, sable-ux, eva main thread) | 7 frontmatter files modified |
| 2f | Tighten Eva main thread to docs/pipeline/ only via enforce-eva-paths.sh; update default-persona.md and agent-system.md routing (robert-spec, sable-ux as subagents) | 2 files modified |
| 2g | Update all test files referencing enforce-paths.sh or old source/ paths; verify bats tests pass | ~15 test files |
| 2h | Create SubagentStop prompt hook (prompt-compact-advisory.sh) to detect Ellis per-wave commit and advise `/compact`; update SKILL.md settings.json template | 1 file created, 1 modified |

#### Phase 2 Acceptance Criteria:

- All 7 per-agent hook scripts exist and are executable; each ~15-20 lines; exit 0 if tool_name is not Write/Edit/MultiEdit
- enforcement-config.json retains pipeline_state_dir, test_patterns, colby_blocked_paths, test_command; lacks architecture_dir, product_specs_dir, ux_docs_dir
- Robert-spec and Sable-ux persona files exist with producer workflows (discovery, spec/design writing, acceptance criteria authoring)
- robert-spec information asymmetry: MAY read prior specs/ADRs; must NOT reference current pipeline QA reports or active ADR
- sable-ux information asymmetry: same as robert-spec
- Robert and Sable reviewer personas unchanged
- Core agent constant updated: 11 core agents + robert-spec + sable-ux = 13 core agents total
- Claude Code frontmatter overlays for write-heavy agents (Colby, Cal, Agatha, Ellis) include `permissionMode: acceptEdits`
- 7 agent overlays include `hooks:` field with event/matcher/command entries
- enforce-eva-paths.sh restricts main thread to docs/pipeline/ only
- /pm and /ux route to robert-spec and sable-ux subagents (not main-thread skills)
- Cursor enforce-paths.sh (in source/cursor/hooks/) is byte-identical to pre-deletion Claude version (SPOF protection)
- All bats tests pass; >= 56 @test entries across 7 new hook script test files
- prompt-compact-advisory.sh detects Ellis per-wave commits and outputs advisory suggesting `/compact`
- SKILL.md documents SubagentStop hook registration and prompt injection pattern
- pipeline-operations.md updated with wave-boundary compaction advisory bullet

---

## Anti-Goals (Never Implement)

1. **Merging Claude Code and Cursor into single universal format.** Platforms have different runtime capabilities; lowest-common-denominator sacrifices Claude Code. Revisit if Cursor adopts frontmatter hooks.

2. **Dynamic source template generation at install time.** Build-step toolchain complexity for problem solved by overlay pattern. Revisit if platform variations exceed 3 or per-project customization outgrows placeholders.

3. **Migrating enforce-paths.sh tests to per-agent files in Phase 1.** Phase 1 is structural. Test migration belongs to Phase 2 where enforcement is replaced.

---

## Test Specifications Summary

**Total: 178 tests (T-0022-001 through T-0022-191, with gaps)**

### Test Distribution by Step:

| Step | Count | IDs | Categories |
|------|-------|-----|------------|
| 1a | 3 | T-0022-001–006, T-0022-009 | Happy (3), Structural (1) |
| 1b | 8 | T-0022-010, T-0022-010a, T-0022-011–015, T-0022-058 | Happy (4), Boundary (2), Failure (1), Regression (1) |
| 1c | 5 | T-0022-016–019, T-0022-025a–025b | Regression (3), Boundary (2) |
| 1d | 8 | T-0022-020–032, T-0022-033–034a | Happy (6), Boundary (4), Failure (2), SPOF (4) |
| 1e | 3 | T-0022-035–045, T-0022-057 | Happy (2), Regression (1) |
| 1f | 2 | T-0022-046–050, T-0022-051–056 | Happy (1), Failure (1) |
| **Phase 1 Total** | **29** | — | — |
| 2a | 17 | T-0022-059–087f | Happy (8), Failure (5), Boundary (2), Security (1), Regression (1) |
| 2b | 15 | T-0022-088–102 | Happy (8), Failure (4), Boundary (2), Regression (1) |
| 2c | 12 | T-0022-103–117 | Happy (6), Boundary (3), Failure (2), Domain Intent (1) |
| 2d | 8 | T-0022-118–125 | Happy (4), Boundary (2), Failure (2) |
| 2e | 17 | T-0022-126–156a | Happy (8), Boundary (5), Failure (2), Regression (2) |
| 2f | 6 | T-0022-157–162 | Happy (3), Boundary (2), Failure (1) |
| 2g | 9 | T-0022-163–169 | Happy (4), Regression (3), Boundary (2) |
| 2h | 22 | T-0022-170–191 | Happy (7), Failure (7), Boundary (4), Security (1), Regression (2), Boundary (1) |
| **Phase 2 Total** | **106** | — | — |
| **Grand Total** | **178** | — | — |

### Key Test Specs (Sampling):

**Happy path samples:**
- T-0022-001: `source/shared/commands/` has all 11 command files
- T-0022-010: All 12 agents: concat claude frontmatter + shared content = byte-identical to original
- T-0022-033a: CURSOR_PROJECT_DIR unset → Claude overlays, `hooks:` field present
- T-0022-088: enforce-roz-paths.sh only allows test files + docs/pipeline/
- T-0022-106: All 11 core agents present in agent-system.md
- T-0022-170: prompt-compact-advisory.sh detects build/implement phase, Ellis agent
- T-0022-186: Advisory stdout matches pattern `suggested_action: '/compact'`

**Boundary/failure samples:**
- T-0022-009: `grep -rl "^---" source/shared/` returns zero (no frontmatter in shared files)
- T-0022-033c: CURSOR_PROJECT_DIR precedence over CLAUDE_PROJECT_DIR documented
- T-0022-034: Missing overlay → error-and-halt (not silent skip)
- T-0022-087a: enforce-roz-paths.sh exits 0 when tool_name is Read
- T-0022-137a: Cursor enforce-paths.sh byte-identical to pre-deletion Claude version
- T-0022-183: prompt-compact-advisory.sh stdout has no stray output redirection syntax
- T-0022-191: Unrecognized phase value produces empty stdout, exit 0

---

## Notes for Colby (13 Implementation Hints)

1. **Frontmatter extraction pattern:** Use `awk` or `sed` to split at second `---`. Content between first and second `---` (exclusive) is frontmatter; after second `---` is body.

2. **File move order:** Non-agent files (commands/, references/, etc.) first; then split agents; then hooks. Independent validation per move.

3. **test_helper.bash HOOKS_DIR:** Line 6 uses relative path from test file to `source/hooks/`. After split, change to `source/claude/hooks/`. One-line change affects all tests.

4. **{config_dir} placeholder:** Shared content files retain `{config_dir}` unresolved. It resolves at /pipeline-setup install time. Do not accidentally resolve it during split.

5. **`<!-- Part of atelier-pipeline -->` comment:** In current files, appears after closing `---` of frontmatter. In split, becomes first line of shared content file. No blank line between comment and identity section.

6. **Per-agent hook scripts needing config:** enforce-roz-paths.sh and enforce-colby-paths.sh read enforcement-config.json via `SCRIPT_DIR` to locate config in same directory (mirrors enforce-paths.sh pattern). Other 5 scripts hardcode paths -- no config file reads.

7. **Main thread detection (enforce-eva-paths.sh):** Does NOT check `agent_type` because it fires from main thread only (registered in settings.json, not agent frontmatter). Trusts main-thread context.

8. **Robert-spec information asymmetry:** Producer MAY read prior specs/ADRs (context needed for consistency). Producer must NOT reference current pipeline QA reports (last-qa-report.md) or active ADR -- prevents anchoring. Asymmetry applies only to reviewer variant (robert.md).

9. **Sable-ux information asymmetry:** Same pattern as Robert-spec. Producer inherits UX expertise, replaces reviewer workflow with design workflow (user flow, state design, interaction patterns, accessibility). Asymmetry = reviewer mode only.

10. **enforce-paths.sh deletion (Claude Code only):** Verify Cursor copy in `source/cursor/hooks/enforce-paths.sh` is complete and byte-identical to pre-deletion Claude version before deleting Claude copy. Cursor copy must be self-contained.

11. **settings.json update pattern:** Current settings.json has `"matcher": "Write|Edit|MultiEdit"` pointing to enforce-paths.sh. In Phase 2, changes to point to enforce-eva-paths.sh. Per-agent scripts are NOT in settings.json -- they are in agent frontmatter `hooks:` field. Only main-thread hook goes in settings.json.

11a. **CRITICAL -- enforcement-config.json simplification scope:** Remove ONLY enforcement-path-specific keys: `architecture_dir`, `product_specs_dir`, `ux_docs_dir`. DO NOT remove `pipeline_state_dir` (used by enforce-pipeline-activation.sh line 48 and enforce-sequencing.sh line 42; silent removal breaks pipeline activation). Also retain `test_command`, `test_patterns`, `colby_blocked_paths`.

12. **Step sizing:** Steps 2c and 2e are largest. Step 2c touches 8 files (6 created, 2 modified) -- at 8-file boundary, justified by simplicity. Step 2e touches 9 files (8 modified overlays, 1 deleted). Both pass sizing gates (independently verifiable, demoable).

13. **Wave-boundary compaction advisory hook pattern (Step 2h):** Follow prompt-brain-capture.sh exactly: `set -uo pipefail` (not `set -e`), `INPUT=$(cat 2>/dev/null) || true`, graceful jq fallback, agent_type case-statement defensive check. Phase detection: `grep -o '<!-- PIPELINE_STATUS: .*-->' pipeline-state.md | sed | jq -r '.phase'`. Hook registration: add to existing SubagentStop array in settings.json (do NOT replace existing entries: warn-dor-dod.sh, log-agent-stop.sh, prompt-brain-capture.sh, warn-brain-capture.sh). **Source location: `source/hooks/` (not `source/claude/hooks/`) because no Cursor equivalent exists and hook follows shared pattern (pre-compact.sh, log-agent-stop.sh).** Install destination is `.claude/hooks/prompt-compact-advisory.sh`.

---

## Revisions

| Revision | Date | Summary | Test Delta |
|----------|------|---------|-----------|
| 0 (initial) | 2026-04-03 | 136-test specification | — |
| 1 (Roz QA) | 2026-04-03 | Resolved 27 findings; added SPOF behavioral tests, hook matcher verification, config structure validation, executable perms | +20 tests → 156 total |
| 2 (User feature) | 2026-04-03 | Added Step 2h wave-boundary compaction advisory with 21 tests | +21 tests → 177 total |
| 3 (Roz scoped re-review) | 2026-04-03 | Fixed T-0022-183 grep pattern, added T-0022-191 (unrecognized phase), clarified Note 13 source path | +1 test → **178 total** |

---

## DoD: Verification Checklist

| Category | Count | Preserved |
|----------|-------|-----------|
| Requirements (R1-R23) | 23 | All 23 |
| Test Specs (T-0022-001 through T-0022-191) | 178 | All 178; gaps noted where revision removed specs |
| Phase 1 Steps (1a-1f) | 6 | All 6 with acceptance criteria |
| Phase 2 Steps (2a-2h) | 8 | All 8 with acceptance criteria |
| Notes for Colby | 13 | All 13 (Hints 1-13, including Note 11a CRITICAL) |
| Layer 1 tool restrictions (9 agents) | 9 | All 9 with field specs |
| Layer 2 hook scripts (7 agents) | 7 | All 7 with enforced paths |
| Layer 3 global hooks | 7 | 4 kept, 1 simplified (config keys listed), 2 deleted with rationale |
| Anti-goals | 3 | All 3 with revisit conditions |
| SPOF analysis | 1 | Platform detection (CURSOR_PROJECT_DIR precedence, T-0022-033a-d, graceful degradation documented) |
| Alternatives considered | 3 | Full copies (rejected: drift), templating (rejected: over-engineering), overlay (chosen: detailed reasoning) |
| Revisions | 3 | All 3 summarized; findings cross-referenced to test specs |
| Wiring diagram (Phase 1) | 4 rows | All preserved with test IDs |
| Wiring diagram (Phase 2) | 7 rows | All preserved with test IDs |
| Core agent constant | 1 | Updated: 11 core + 2 new (robert-spec, sable-ux) = 13 core total |
| Domain decisions | 2 | Robert-spec asymmetry (may read specs, not QA reports); enforcement-config.json retains pipeline_state_dir |

**Compression ratio:** ~22000 tokens → ~9200 tokens (58% reduction). All facts, decisions, constraints, dependencies, test IDs, and notes preserved. Format: dense bullets, no prose transitions.
