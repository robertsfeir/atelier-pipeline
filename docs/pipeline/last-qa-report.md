## QA Report -- 2026-04-02 (Wave 1 Frontmatter + Distributed Routing)
*Reviewed by Roz*

### Verdict: PASS

| Check | Status | Details |
|-------|--------|---------|
| Cal frontmatter: `tools: Read, Write, Edit, Glob, Grep, Bash, Agent(roz)` | PASS | Confirmed in both source/agents/cal.md and .claude/agents/cal.md |
| Cal frontmatter: NO `disallowedTools` line | PASS | Zero matches in both files |
| Colby frontmatter: `tools: Read, Write, Edit, MultiEdit, Glob, Grep, Bash, Agent(roz, cal)` | PASS | Confirmed in both source/agents/colby.md and .claude/agents/colby.md |
| Colby frontmatter: NO `disallowedTools` line | PASS | Zero matches in both files |
| Roz `disallowedTools: Agent, Edit, MultiEdit, NotebookEdit` present | PASS | Confirmed in both source/agents/roz.md and .claude/agents/roz.md |
| Roz has no `tools` allowlist | PASS | No `^tools:` line in either roz.md |
| All other agents have `disallowedTools` with Agent in deny list | PASS | agatha, darwin, deps, distillator, ellis, investigator, robert, sable, sentinel -- all confirmed |
| Cal workflow: Test Spec Review Loop section present, mentions spawning Roz | PASS | Section at line 117, references spawn Roz, tight loop, Roz-approved ADR |
| Cal workflow: "Do NOT spawn Roz for anything other than test spec review" guard | PASS | Present at line 130 |
| Colby workflow: Per-Unit QA Loop section present, mentions spawning Roz | PASS | Section at line 66, references spawn Roz for per-unit QA |
| Colby workflow: Architectural Consultation section present, mentions spawning Cal | PASS | Section at line 85, references spawn Cal for architectural ambiguity |
| Roz identity: caller awareness (Eva, Cal, Colby) | PASS | Lines 23-26 in .claude/agents/roz.md |
| source/ and .claude/ frontmatter identical for cal, colby, roz | PASS | Byte-for-byte identical frontmatter blocks in all three |
| New workflow sections identical between source/ and .claude/ | PASS | Test Spec Review Loop and Per-Unit QA Loop sections are identical across trees |
| Pre-existing source/.claude/ placeholder divergence (cal, colby) | INFO | Pre-existing in HEAD before this change -- not a regression. See below. |
| TODO/FIXME/HACK/XXX in changed files | PASS | Matches are instructional directives written to agents, not unfinished code markers |
| `bats tests/hooks/` | PASS | 68/68 ok, 0 not ok |
| `node --test tests/brain/*.test.mjs` | PASS (pre-existing failures) | 89 pass, 4 fail -- failures confirmed pre-existing in HEAD before this change |

### Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| 1 | Cal frontmatter: `tools` allowlist with `Agent(roz)`, no `disallowedTools` | Done | PASS | tools field present, disallowedTools absent, in both trees |
| 2 | Colby frontmatter: `tools` allowlist with `Agent(roz, cal)`, no `disallowedTools` | Done | PASS | tools field present, disallowedTools absent, in both trees |
| 3 | Roz retains `disallowedTools: Agent, Edit, MultiEdit, NotebookEdit` | Done | PASS | Unchanged, no tools allowlist added |
| 4 | All other agents retain Agent in disallowedTools deny list | Done | PASS | All 9 other agents verified |
| 5 | Cal workflow section: Test Spec Review Loop with spawn Roz | Done | PASS | Section present with 4-step loop, guard clause, identical in both trees |
| 6 | Colby workflow section: Per-Unit QA Loop with spawn Roz | Done | PASS | Section present with scope boundary note, identical in both trees |
| 7 | Colby workflow section: Architectural Consultation with spawn Cal | Done | PASS | Section present with one-question-per-invocation constraint, identical in both trees |
| 8 | Roz identity mentions Eva, Cal, Colby as callers | Done | PASS | Three-caller awareness text in identity section |
| 9 | source/ and .claude/ frontmatter sync for cal, colby, roz | Done | PASS | All three frontmatter blocks are byte-identical |
| 10 | No regressions in bats hook tests | Done | PASS | 68/68 pass |
| 11 | No regressions in brain tests | Done | PASS (pre-existing) | 4 failures confirmed pre-existing in HEAD, not introduced by this change |

### Unfinished Markers

`grep -rn "TODO|FIXME|HACK|XXX"` on changed agent files (cal.md, colby.md, roz.md): all matches are instructional text embedded in agent constraints (Colby: "no unfinished markers (TODO/FIXME/HACK)"; Roz: "Grep for TODO/FIXME/HACK/XXX"). These are directives written to agents, not unfinished markers in implementation code. Not blockers.

### Issues Found

**BLOCKER:** None.

**FIX-REQUIRED:** None.

**Informational (pre-existing, not introduced by this change):**

Two source-to-.claude divergences exist at the body level but were present in HEAD before this wave:

1. `source/agents/cal.md` lines 173-180: Contains `{ux_docs_dir}` and `{product_specs_dir}` placeholders. `.claude/agents/cal.md` has these resolved to `docs/ux` and `docs/product`. Divergence confirmed pre-existing in HEAD before the unstaged changes. Out of scope for this change.

2. `source/agents/colby.md`: Contains `{lint_command}`, `{typecheck_command}`, `{test_command_fast}`, and `{test_single_command}` placeholders. `.claude/agents/colby.md` has these resolved to echo commands. Divergence confirmed pre-existing in HEAD. This was the FIX-REQUIRED item from the Wave 1 final QA report. Still open. Still out of scope for this routing change -- should be scheduled.

**Brain test failures (pre-existing):**

Four tests fail in `tests/brain/config.test.mjs`: `T-0003-066`, "falls back to user config when project config is missing", "accepts ATELIER_BRAIN_DATABASE_URL as env fallback", and "skips config files with malformed JSON". All four fail identically on HEAD before the unstaged changes. Confirmed by running the test suite against the stashed working tree. These are not regressions from this wave.

### Doc Impact: NO

The distributed routing changes are mechanics within agent persona files. No user-facing documentation references which agents can spawn which other agents. `docs/guide/` and `docs/architecture/` do not need updates. The agent system section of `agent-system.md` describes the subagent tool roster -- those descriptions remain accurate. No doc updates required.

### Roz's Assessment

The combined Wave 1 frontmatter + distributed routing change is clean. All 11 specific constraints from the task brief pass.

The tool-switching approach (from `disallowedTools` to explicit `tools` allowlist for Cal and Colby) is semantically correct: an allowlist is stronger enforcement than a denylist for agents that need scoped Agent access. Roz retains `disallowedTools` which is appropriate -- she cannot spawn anyone, and a denylist is the right form when the base set of allowed tools is the full set minus a few.

The three new workflow sections (Cal's Test Spec Review Loop, Colby's Per-Unit QA Loop, Colby's Architectural Consultation) are well-scoped: each has a clear entry condition, a guard clause preventing scope creep, and matching text in both source/ and .claude/ trees.

Roz's caller-awareness text in identity is accurate and neutral -- identical behavior regardless of invoker is the correct specification. The text makes the multi-caller contract legible without changing how Roz operates.

The two pre-existing source/.claude divergences (Cal placeholders, Colby command substitutions) are not regressions from this wave and were present before the change. They remain open items from prior waves and should be closed separately.

**Recurring pattern:** The source-to-.claude body divergence pattern has now appeared in three consecutive waves. This project eats its own cooking, meaning the source/ templates are the ground truth for new installs. Divergences in body content (not just frontmatter) accumulate silently and can surprise operators installing on fresh projects. A sync check between source/ and .claude/ for each changed agent should be part of Colby's DoD going forward.
