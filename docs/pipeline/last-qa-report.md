# QA Report -- 2026-04-03
*Reviewed by Roz*

## QA Report: Wave 4 -- Cursor Sync Remediation

### Verdict: PASS (with pre-existing issues noted, not introduced by this wave)

| Check | Status | Details |
|-------|--------|---------|
| T1: Type check | SKIP | No typecheck configured |
| T1: Lint | SKIP | No linter configured |
| T1: Tests (bats) | PASS | 274/274 passed, 0 failed |
| T1: Tests (brain) | PASS | 93/93 passed, 0 failed |
| T1: Coverage | N/A | No coverage threshold configured |
| T1: Complexity | PASS | No functions; all changed files are Markdown |
| T1: Unfinished markers | PASS | All TODO/FIXME hits are instructional text within persona/reference content, not actual unfinished markers |
| V1: 12 agents have single YAML frontmatter | PASS | All 12 agents have exactly 2 `---` delimiters; extra `---` in darwin/deps are horizontal rule separators in body content, confirmed not duplicate frontmatter |
| V2: All 12 agents have model, effort, maxTurns | PASS | All 12 cursor-plugin agents are byte-identical to source/agents/ -- all fields present |
| V3: Brain agents have mcpServers + brain-access | PASS | cal, colby, roz, agatha: mcpServers: atelier-brain in frontmatter; `<protocol id="brain-access">` section present with correct content |
| V4: .cursor-plugin/rules/ has 15 .mdc files | PASS | 15 files confirmed: 10 existing + 5 new (qa-checks, branch-mr-mode, telemetry-metrics, xml-prompt-schema, cloud-architecture) |
| V5: 5 new .mdc files have alwaysApply: false + correct content | PASS | All 5 have alwaysApply: false; body content byte-identical to source/references/ counterparts |
| V6: 3 regenerated .mdc rule files match source/rules/ | PASS | agent-system.mdc and default-persona.mdc: byte-identical to source. pipeline-orchestration.mdc: body identical; frontmatter correctly uses Cursor `globs:` format instead of Claude Code `paths:` format |
| V7: SKILL.md includes 5 new reference docs in Cursor sync step | PASS | Lines 397-401 list all 5 new entries in Step 3c table with correct source/destination/description |
| V8: No .cursor-plugin/ files reference hardcoded .claude/ paths | FAIL (pre-existing) | 4 files affected; all pre-date this wave (created ADR-0019 commit 554dd9f); 5 new files added in this wave do NOT have this problem |
| T2: Security | PASS | No secrets, injection risks, or missing auth in sync content |
| T2: Doc Impact | YES | See doc impact section |

---

### Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| P1a | All 12 agent personas synced from source/agents/ | Done | VERIFIED | All 12 cursor-plugin agents byte-identical to source |
| P1b | 3 .mdc rule files regenerated from source/rules/ | Done | VERIFIED | agent-system, default-persona: identical; pipeline-orchestration: body identical, frontmatter correctly converted to Cursor format |
| P1c | Agatha brain-access protocol in .cursor-plugin/agents/agatha.md | Done | VERIFIED | `<protocol id="brain-access">` present at line 53; mcpServers at line 11 |
| P2a | 5 new .mdc reference files in .cursor-plugin/rules/ | Done | VERIFIED | All 5 present with alwaysApply: false and correct content from source |
| P2b | Duplicate YAML frontmatter in colby.md and robert.md fixed | Done | VERIFIED | Both files have exactly 2 `---` delimiters; frontmatter appears once only |

---

### Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"`: 14 hits across cursor-plugin files. All are instructional references within agent constraints and QA procedure text (Colby's delivery constraint, Roz's grep instruction in qa-checks). Zero actual unfinished work markers.

---

### Issues Found

**FIX-REQUIRED** (pre-existing -- not introduced by this wave; queued for a separate cursor-sync remediation):

**`.cursor-plugin/rules/agent-preamble.mdc`** (pre-existing from commit 554dd9f, ADR-0019)
- Lines 15, 22, 31: `.claude/references/` hardcoded. Cursor installs should read `.cursor/references/`.
- Line 4: CONFIGURE comment incorrectly says "No placeholders to update" -- source template now has `{config_dir}` placeholder.
- Lines 27-31: Missing brain-access content added to source/references/agent-preamble.md after ADR-0019. Cursor-plugin copy lacks the paragraph about agents with `mcpServers: atelier-brain` capturing directly, and agents without brain access surfacing knowledge in output.

**`.cursor-plugin/rules/pipeline-operations.mdc`** (pre-existing from ADR-0019)
- Lines 11-12, 81, 280, 328-329: `.claude/references/`, `.claude/agents/`, `.claude/rules/` hardcoded. Should use `.cursor/` equivalents.
- Lines 21-31: Brain prefetch protocol section describes old model (Eva-only capture) rather than current hybrid model (agents with mcpServers capture directly). 30+ lines of content drift from source.

**`.cursor-plugin/rules/invocation-templates.mdc`** (pre-existing from ADR-0019)
- Multiple `<read>` tags throughout: `.claude/references/` hardcoded. Cursor users following these read lists will reference non-existent paths.
- CONFIGURE comment lists project-specific resolved values rather than generic template placeholders -- this copy was customized for this project rather than keeping the template format.
- 251 lines of diff from source -- significant content drift from multiple source updates since ADR-0019.

**`.cursor-plugin/rules/dor-dod.mdc`** (pre-existing from ADR-0019)
- Line 204: `.claude/references/retro-lessons.md` hardcoded. Should use `.cursor/references/retro-lessons.md`.

**Scope note:** These 4 files were not touched by this wave. This wave correctly addressed the 5 new .mdc files (which do not have the `.claude/` problem) and the 12 agent syncs. The pre-existing `.claude/` path issue affects Cursor users who follow `<read>` tag guidance -- they will see `.claude/references/` paths that do not exist in a Cursor install (which uses `.cursor/`). The 5 original ADR-0019 .mdc reference files need a re-sync pass comparable to what this wave did for the agents.

---

### Doc Impact: YES

The SKILL.md update (Step 3c expansion to 10 entries) changes the documented installation procedure for the Cursor plugin. Users running `/pipeline-setup` in Cursor now install 5 additional reference .mdc files. If user-guide.md or technical-reference.md describes the .cursor-plugin/ contents by count or by file list, those docs need updating to reflect 15 .mdc files total.

---

### Roz's Assessment

This wave delivers exactly what it claimed. All 12 agents are synced correctly and are byte-identical to source -- the model, effort, and maxTurns fields are all present, brain agents have mcpServers frontmatter and brain-access sections, and the duplicate frontmatter in colby and robert is fixed. The 5 new .mdc files are present with correct frontmatter and content. The 3 regenerated rule .mdc files are correct, including the intentional `paths:` to `globs:` conversion for pipeline-orchestration.

The `.claude/` hardcoded path issue is pre-existing in 4 ADR-0019 files not touched by this wave. It is a functional correctness issue for Cursor users -- every `<read>` tag in invocation-templates.mdc points agents to `.claude/references/` paths that do not exist in a Cursor install. I am marking these FIX-REQUIRED (not BLOCKER) because they predate this wave and represent known drift from a separate remediation track. The 5 new .mdc files added here avoid this problem entirely.

All 367 tests pass. No regressions introduced.

---

### Brain Patterns to Capture (Eva to capture on Roz's behalf)

**Pattern:** Cursor plugin .mdc files diverge from source when source is updated after initial creation. The 5 original ADR-0019 .mdc files (agent-preamble, dor-dod, invocation-templates, pipeline-operations, retro-lessons) are now behind source by multiple updates. A re-sync pass is needed for those 5 files, analogous to what this wave did for agents and the 5 new reference docs.

**Lesson:** When `source/references/*.md` files are updated, the corresponding `.cursor-plugin/rules/*.mdc` wrappers must be re-synced in the same commit. Recommend adding a bats test that diffs each .mdc body against its source counterpart to catch drift automatically.
