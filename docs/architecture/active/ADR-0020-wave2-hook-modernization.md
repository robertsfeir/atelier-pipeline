# ADR-0020: Wave 2 -- Hook Modernization

## DoR: Requirements Extracted

**Sources:** Eva invocation prompt (task + constraints + brain-context), context-brief.md (scope decisions), retro-lessons.md (lessons #003, #004), Claude Code hooks documentation (hook events and `if` conditional field), existing hooks (source/hooks/*.sh), pipeline-state.md (Wave 2 units), SKILL.md (installation manifest), .claude/settings.json (hook registration), test_helper.bash (test patterns), hydrate-telemetry.mjs (existing telemetry pipeline)

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Add `if` conditionals to existing PreToolUse hooks to skip ~80% of process spawns | Task (2a) | "Claude Code now supports an `if` field on hook entries that matches before executing" |
| R2 | Add `if` conditionals to existing SubagentStop and PreCompact hooks | Task (2a) | "`if` conditionals to existing PreToolUse/SubagentStop/PreCompact hooks" |
| R3 | SubagentStart hook (log-agent-start.sh) captures agent lifecycle start data | Task (2b) | "log-agent-start.sh, log-agent-stop.sh that capture agent lifecycle data" |
| R4 | SubagentStop telemetry hook (log-agent-stop.sh) captures agent lifecycle end data | Task (2b) | "capture agent lifecycle data into the brain as Tier 1 telemetry" |
| R5 | Telemetry data written as JSONL to a session file, not direct brain calls | Constraints + brain-context | "Prefer logging to a file that Eva reads, not direct brain calls from hooks" + retro #003 |
| R6 | PostCompact hook (post-compact-reinject.sh) re-injects pipeline-state.md + context-brief.md after compaction | Task (2c) | "PostCompact hook fires after compaction. It can output text that gets injected into the context" |
| R7 | StopFailure hook (log-stop-failure.sh) appends to error-patterns.md when agent turn ends due to API error | Task (2d) | "appends to error-patterns.md when an agent turn ends due to API error" |
| R8 | All new hooks exit 0 always (non-enforcement hooks) | Retro #003 + constraints | "Exit 0 always for non-enforcement hooks" |
| R9 | All new hooks are lightweight -- no brain calls, no test suites, no subagent invocations | Retro #003 | "Keep new hooks lightweight, never block on quality checks" |
| R10 | Hook scripts go in source/hooks/ (templates) and install to .claude/hooks/ | Constraints | "New hook scripts go in source/hooks/ and are installed to .claude/hooks/ by /pipeline-setup" |
| R11 | Hook registrations go in settings.json template and installed .claude/settings.json | Constraints | "Hook registrations go in the settings.json template" |
| R12 | Tests use bats framework following existing test_helper.bash patterns | Constraints + existing tests | "Test specs should cover: hook script behavior (bats tests)" |
| R13 | `if` field format: JavaScript-like expression evaluated by Claude Code before spawning | Constraints | `"if": "tool_name == 'Write' && file_path.endsWith('.ts')"` |
| R14 | SubagentStart/Stop input includes: agent_type, agent_id, session_id. Stop adds: last_assistant_message | Constraints | "SubagentStart/Stop hook input includes: agent_type, agent_id, session_id" |
| R15 | PostCompact hook outputs text that gets injected into context | Constraints | "PostCompact hook fires after compaction. It can output text that gets injected into the context" |
| R16 | StopFailure hook input includes error details | Constraints | "StopFailure hook fires when a turn ends due to API error. Input includes error details" |
| R17 | source/ templates use `{placeholders}` for project-specific paths | CLAUDE.md | "source/ contains templates with `{placeholders}`" |
| R18 | Existing hook behavior must not change -- `if` conditionals are a performance optimization only | Task (2a) | "reduce ~80% hook process spawns" -- same behavior, fewer spawns |

**Retro risks:**

- **Lesson #003 (Stop Hook Race Condition):** Directly relevant to all 4 units. Every new hook MUST exit 0. The SubagentStop telemetry hook (2b) is the highest risk -- it fires on every agent completion and must be fast. The PostCompact hook (2c) outputs text (which is by design), but must never block. The StopFailure hook (2d) writes to disk, which must succeed or silently fail.
- **Lesson #004 (Hung Process Retry Loop):** Tangentially relevant. If a hook hangs (e.g., disk I/O stall on JSONL write), it could block the agent lifecycle. Mitigation: all writes are atomic (write to temp, mv) or append-only with short content.

**Spec challenge:** The spec assumes the `if` conditional field uses JavaScript-like expressions that can match on `tool_name`, `file_path`, `agent_type`, and other fields from the hook input. If the expression evaluator is more limited than assumed (e.g., only supports simple equality, not compound expressions with `&&`), the `if` conditionals for enforce-paths.sh (which needs `tool_name` matching but already has a matcher) may not reduce spawns as expected. **Are we confident?** Yes -- brain-context confirms Claude Code v2.1.89-90 introduced this feature, and the constraint specifies the exact syntax format. The `if` field is evaluated before process spawning, which is the documented purpose.

**SPOF:** The JSONL session telemetry file (unit 2b). If the file path is wrong, permissions prevent writing, or the disk is full, all Tier 1 telemetry from hooks is lost for the session. **Failure mode:** Eva's in-memory accumulators still work (they capture from Agent tool return values), but the hook-based real-time capture adds nothing. **Graceful degradation:** The existing telemetry pipeline (Eva in-memory + hydrate-telemetry.mjs post-session) continues to function. Hook telemetry is additive -- its loss degrades data richness but does not break the pipeline. The hooks log a warning to stderr and exit 0.

**Anti-goals:**

1. **Anti-goal: Direct brain writes from hooks.** Reason: Retro lesson #003 proved that hooks doing heavy work (test suites, network calls) cause race conditions and slowdowns. Brain MCP calls from shell hooks would add latency and fragility. Data flows to brain via Eva or hydration scripts. Revisit: If Claude Code adds a lightweight async hook output channel that does not block the main thread.

2. **Anti-goal: Replacing Eva's in-memory telemetry accumulators.** Reason: Eva's Tier 1 accumulator (from Agent tool return values) is the primary data source for pipeline telemetry. Hook-based telemetry is a complementary real-time capture that enriches data. Removing Eva's accumulators would create a single point of failure in the hook layer. Revisit: If hook telemetry proves more reliable than Agent tool metadata over 10+ pipelines.

3. **Anti-goal: Adding `if` conditionals to enforce-pipeline-activation.sh.** Reason: This hook already has internal early exits (checks agent_type for colby|ellis only), and it must fire on every Agent invocation to read pipeline state. An `if` conditional cannot express "only when subagent_type is colby or ellis" because the `if` field evaluates before the hook process reads stdin. The hook itself is the correct place for this filtering. Revisit: If Claude Code exposes `subagent_type` as a top-level field accessible to `if` expressions.

---

## Status

Proposed

## Context

The atelier-pipeline hook layer currently consists of 6 shell scripts + 1 config file, registered in `.claude/settings.json`. Every hook fires on every matching tool call, spawning a new bash process each time. For a typical pipeline session with ~50 tool calls:

- `enforce-paths.sh` fires on every Write/Edit/MultiEdit (~15 calls), but only ~3 are from subagents that need checking (the rest are Eva writing pipeline state, which the script checks and allows)
- `enforce-sequencing.sh` fires on every Agent call (~8 calls), but only ~2 involve Ellis (the primary gate)
- `enforce-git.sh` fires on every Bash call (~25 calls), but only ~2 contain git commands
- `warn-dor-dod.sh` fires on every SubagentStop (~8 calls), but only inspects Colby and Roz (~3 calls)
- `pre-compact.sh` fires on every PreCompact (~1-2 calls) -- this one is already efficient

Claude Code v2.1.89-90 introduced an `if` conditional field on hook entries. When present, Claude Code evaluates the expression before spawning the hook process. This enables filtering at the engine level, avoiding ~80% of process spawns.

Additionally, four new hook events are available that enable capabilities the pipeline currently lacks:

- **SubagentStart** -- enables real-time agent lifecycle tracking (currently, Eva tracks in-memory only after agents return)
- **PostCompact** -- enables context re-injection after compaction (currently, the pre-compact hook marks state but cannot inject content back)
- **StopFailure** -- enables error tracking when agents fail due to API errors (currently, these failures are silently lost)

Wave 1 of the frontmatter enrichment initiative (v3.16.0) established per-agent metadata. Wave 2 modernizes the hook layer to leverage Claude Code's expanded hook API.

## Decision

Implement all four units as a single wave with clear dependencies:

### Unit 2a: `if` Conditionals on Existing Hooks

Add `if` fields to existing hook registrations in settings.json. The hook scripts themselves do not change -- the `if` field prevents Claude Code from spawning the process when the condition does not match.

**Conditional mapping:**

| Hook | Event | Current Matcher | `if` Conditional | Rationale |
|------|-------|-----------------|------------------|-----------|
| enforce-paths.sh | PreToolUse | `Write\|Edit\|MultiEdit` | (none needed -- matcher already filters) | Matcher is sufficient; `if` would be redundant |
| enforce-sequencing.sh | PreToolUse | `Agent` | (none needed -- all Agent calls need checking) | The hook checks subagent_type internally; `if` cannot access tool_input fields |
| enforce-pipeline-activation.sh | PreToolUse | `Agent` | (none needed -- same reason as sequencing) | Internal filtering is more precise than `if` |
| enforce-git.sh | PreToolUse | `Bash` | `"if": "tool_input.command.includes('git ')"` | Skips ~90% of Bash calls that have no git commands |
| warn-dor-dod.sh | SubagentStop | (none) | `"if": "agent_type == 'colby' \|\| agent_type == 'roz'"` | Skips ~60% of SubagentStop events (only inspects Colby/Roz) |
| pre-compact.sh | PreCompact | (none) | (none needed -- fires rarely, 1-2 per session) | Not worth adding complexity |

**Revised estimate:** The `if` conditionals reduce spawns for enforce-git.sh (~23 of 25 Bash calls skipped) and warn-dor-dod.sh (~5 of 8 SubagentStop calls skipped). The PreToolUse Agent hooks already use internal filtering. Net reduction: ~28 spawns avoided per session out of ~57 total, approximately 50% reduction. The "~80%" from the task description was optimistic but the reduction is still significant.

### Unit 2b: SubagentStart/SubagentStop Telemetry Hooks

Two new scripts that capture agent lifecycle timestamps to a JSONL file:

- `log-agent-start.sh` (SubagentStart): writes `{"event":"start","agent_type":"...","agent_id":"...","session_id":"...","timestamp":"..."}`
- `log-agent-stop.sh` (SubagentStop): writes `{"event":"stop","agent_type":"...","agent_id":"...","session_id":"...","timestamp":"...","has_output":true|false}`

The JSONL file path: `$CLAUDE_PROJECT_DIR/.claude/telemetry/session-hooks.jsonl` (gitignored, ephemeral per-session). Eva or hydrate-telemetry.mjs reads this file for Tier 1 enrichment.

Design choices:
- **JSONL append, not brain call:** Retro #003 mandates lightweight hooks. A JSONL append is ~1ms. A brain MCP call is ~100-500ms.
- **No output inspection in stop hook:** The existing warn-dor-dod.sh already inspects output. The telemetry stop hook only records the timestamp and a boolean `has_output` flag.
- **Atomic writes:** Each line is written via `echo >> file`. JSONL is append-only and tolerates partial writes (each line is independent).

### Unit 2c: PostCompact Context Preservation Hook

`post-compact-reinject.sh` fires after compaction and outputs the contents of `pipeline-state.md` and `context-brief.md` to stdout. Claude Code injects this output into the post-compaction context, giving Eva immediate awareness of pipeline state without needing to re-read files.

Design choices:
- **Output to stdout:** PostCompact hooks can output text that gets injected. This is the documented mechanism.
- **Two files only:** pipeline-state.md (~2KB) and context-brief.md (~1KB) are small enough to inject without bloating context. Other files (error-patterns.md, retro-lessons.md) are read on-demand.
- **Existing pre-compact.sh preserved:** The PreCompact hook continues to write a compaction marker. The new PostCompact hook reads state after compaction and injects it.

### Unit 2d: StopFailure Error Tracking Hook

`log-stop-failure.sh` fires when an agent turn ends due to an API error. It appends a structured entry to `error-patterns.md` with the error type, agent, and timestamp.

Design choices:
- **Append to error-patterns.md:** This is Eva's existing error tracking file. The hook adds entries that Eva can review at pipeline end.
- **Structured format:** Each entry is a markdown section with error type, agent, timestamp, and a truncated error message (first 200 chars to avoid bloating the file).
- **Exit 0 always:** Even if the write fails (permissions, disk full), the hook exits 0. The error is logged to stderr.

## Alternatives Considered

### Alternative A: Hook-to-Brain Direct Capture (Rejected)

Instead of JSONL files, hooks would call brain MCP tools directly via HTTP.

**Pros:**
- Real-time brain population -- no post-session hydration needed
- Single data path (hook -> brain) instead of two (hook -> JSONL -> hydration -> brain)

**Cons:**
- Violates retro lesson #003 -- network calls from hooks add 100-500ms latency per spawn
- Brain unavailability would cause hook failures (or complex fallback logic)
- HTTP calls from bash are fragile (curl dependency, auth, error handling)
- Brain MCP server may not be running during all sessions

**Decision:** Rejected. The JSONL approach is aligned with the existing hydrate-telemetry.mjs pattern and keeps hooks lightweight.

### Alternative B: Single Unified Hook Script (Rejected)

Instead of separate scripts per hook event, use a single `atelier-hook.sh` that dispatches based on an event type argument.

**Pros:**
- Single file to maintain
- Shared utilities (JSON parsing, config loading) without duplication

**Cons:**
- Increases blast radius -- a bug in one event handler breaks all events
- Cannot use `if` conditionals per-event (the script is the same for all events)
- Harder to test in isolation
- Breaks the existing pattern of one-script-per-concern

**Decision:** Rejected. The existing one-script-per-concern pattern is proven and testable. Shared utilities are already in test_helper.bash for tests; the scripts themselves are small enough to be self-contained.

### Alternative C: `if` Conditionals on All Hooks Including Agent Hooks (Rejected)

Add `if` conditionals to enforce-sequencing.sh and enforce-pipeline-activation.sh using compound expressions like `"if": "tool_input.subagent_type == 'ellis' || tool_input.subagent_type == 'colby'"`.

**Pros:**
- Would skip process spawns for ~6 of 8 Agent calls (only Ellis/Colby need checking)

**Cons:**
- The `if` field evaluates against the hook input schema. `tool_input.subagent_type` may not be a top-level field accessible to the `if` expression evaluator -- it is nested inside `tool_input` which is the Agent tool's input object
- enforce-sequencing.sh checks multiple gates (Ellis QA, Agatha timing, telemetry) that apply to different agents -- a single `if` cannot express "ellis OR agatha OR colby"
- Risk of silently bypassing enforcement if the expression evaluator does not support nested field access

**Decision:** Rejected. The internal early-exit pattern in the scripts is more reliable than depending on undocumented `if` expression capabilities for nested fields.

## Consequences

**Positive:**
- ~50% reduction in hook process spawns per session (28 of ~57 eliminated)
- Real-time agent lifecycle telemetry available during sessions (not just post-session)
- Context preserved across compaction events (pipeline-state + context-brief re-injected)
- API error failures tracked in error-patterns.md (previously silent)
- All changes are backward-compatible -- existing behavior unchanged

**Negative:**
- 4 new hook scripts to maintain (10 total, up from 6)
- JSONL telemetry file requires cleanup (gitignore, ephemeral) -- adds a file management concern
- PostCompact re-injection adds ~3KB to post-compaction context -- a minor context cost

**Risks:**
- The `if` expression evaluator's exact capabilities are based on Claude Code documentation and brain context. If `tool_input.command.includes()` is not supported for enforce-git.sh, the `if` conditional falls back to the existing behavior (hook spawns on every Bash call, internal check exits early). No functional regression.
- The StopFailure event is new and may have undocumented input schema differences. The hook handles missing fields gracefully.

## Implementation Plan

### Step 1 (Unit 2a): Add `if` Conditionals to Existing Hooks

Add `if` fields to hook registrations in the settings.json template and installed settings.json. No hook script changes.

**Files to create:** (none)

**Files to modify:**
1. `source/hooks/enforce-git.sh` -- add a comment noting the `if` conditional in settings.json (documentation only, no behavioral change)
2. `.claude/settings.json` -- add `if` fields to enforce-git.sh and warn-dor-dod.sh entries
3. `skills/pipeline-setup/SKILL.md` -- update hook registration template with `if` fields
4. `tests/hooks/enforce-git.bats` -- add test verifying the hook still works when the `if` filter passes (existing tests already cover this, but add an explicit note)

**Acceptance criteria:**
- AC1: enforce-git.sh hook entry has `"if": "tool_input.command.includes('git ')"` in settings.json
- AC2: warn-dor-dod.sh hook entry has `"if": "agent_type == 'colby' || agent_type == 'roz'"` in settings.json
- AC3: pipeline-setup SKILL.md template matches installed settings.json
- AC4: All existing bats tests pass (no behavioral regression)
- AC5: A Bash call without "git " in the command does not spawn enforce-git.sh (verified by `if` field presence, not testable in bats since bats runs the script directly)

**Estimated complexity:** Low (config change + documentation)

---

### Step 2a (Unit 2b, Part 1): SubagentStart Telemetry Hook

Create the SubagentStart hook that logs agent start events to JSONL.

**Files to create:**
1. `source/hooks/log-agent-start.sh` -- SubagentStart hook script
2. `tests/hooks/log-agent-start.bats` -- bats tests

**Files to modify:**
1. `.claude/settings.json` -- add SubagentStart hook registration
2. `skills/pipeline-setup/SKILL.md` -- add to installation manifest and hook registration template
3. `.gitignore` -- add `.claude/telemetry/` to gitignore

**Acceptance criteria:**
- AC1: Hook creates `.claude/telemetry/` directory if missing
- AC2: Hook appends a valid JSON line to `.claude/telemetry/session-hooks.jsonl`
- AC3: JSON line contains: event, agent_type, agent_id, session_id, timestamp
- AC4: Hook exits 0 when JSONL write fails (e.g., permissions)
- AC5: Hook exits 0 when jq is not available (graceful degradation)
- AC6: Hook is registered as SubagentStart in settings.json
- AC7: SKILL.md installation manifest includes the new hook

**Estimated complexity:** Low-Medium (new script + registration + tests)

---

### Step 2b (Unit 2b, Part 2): SubagentStop Telemetry Hook

Create the SubagentStop hook that logs agent stop events to JSONL. This runs alongside the existing warn-dor-dod.sh on SubagentStop.

**Files to create:**
1. `source/hooks/log-agent-stop.sh` -- SubagentStop telemetry hook script
2. `tests/hooks/log-agent-stop.bats` -- bats tests

**Files to modify:**
1. `.claude/settings.json` -- add log-agent-stop.sh to SubagentStop hook array
2. `skills/pipeline-setup/SKILL.md` -- add to installation manifest and hook registration template
3. `tests/hooks/test_helper.bash` -- add `build_subagent_stop_input` helper for SubagentStop JSON format

**Acceptance criteria:**
- AC1: Hook appends a valid JSON line to `.claude/telemetry/session-hooks.jsonl`
- AC2: JSON line contains: event, agent_type, agent_id, session_id, timestamp, has_output (boolean)
- AC3: Hook does NOT inspect or log the `last_assistant_message` content (privacy + performance)
- AC4: Hook exits 0 always, even on write failure
- AC5: Hook exits 0 when jq is not available
- AC6: Hook is registered alongside warn-dor-dod.sh in SubagentStop array
- AC7: warn-dor-dod.sh continues to function unchanged (no interference)
- AC8: Both hooks can share the same SubagentStop event without conflict

**Estimated complexity:** Low-Medium (similar to 2a, shared JSONL format)

---

### Step 3 (Unit 2c): PostCompact Context Preservation Hook

Create the PostCompact hook that re-injects pipeline state after compaction.

**Files to create:**
1. `source/hooks/post-compact-reinject.sh` -- PostCompact hook script
2. `tests/hooks/post-compact-reinject.bats` -- bats tests

**Files to modify:**
1. `.claude/settings.json` -- add PostCompact hook registration (alongside existing pre-compact.sh)
2. `skills/pipeline-setup/SKILL.md` -- add to installation manifest and hook registration template

**Acceptance criteria:**
- AC1: Hook reads pipeline-state.md and context-brief.md from project root
- AC2: Hook outputs both files' contents to stdout with clear section markers
- AC3: Output includes a header: `--- Re-injected after compaction ---`
- AC4: If pipeline-state.md does not exist, hook outputs nothing and exits 0
- AC5: If context-brief.md does not exist, hook outputs only pipeline-state.md
- AC6: Hook exits 0 always
- AC7: Output is small enough to inject (~3KB for both files combined)
- AC8: Existing pre-compact.sh continues to function unchanged

**Estimated complexity:** Low (simple file read + stdout output)

---

### Step 4 (Unit 2d): StopFailure Error Tracking Hook

Create the StopFailure hook that appends error information to error-patterns.md.

**Files to create:**
1. `source/hooks/log-stop-failure.sh` -- StopFailure hook script
2. `tests/hooks/log-stop-failure.bats` -- bats tests

**Files to modify:**
1. `.claude/settings.json` -- add StopFailure hook registration
2. `skills/pipeline-setup/SKILL.md` -- add to installation manifest and hook registration template

**Acceptance criteria:**
- AC1: Hook reads error details from StopFailure input JSON
- AC2: Hook appends a structured entry to `docs/pipeline/error-patterns.md`
- AC3: Entry format: `### StopFailure: {agent_type} at {timestamp}\n- Error: {error_type}\n- Message: {first 200 chars of error message}`
- AC4: If error-patterns.md does not exist, hook creates it with a header
- AC5: Hook exits 0 always, even if write fails
- AC6: Hook exits 0 when jq is not available
- AC7: Error message is truncated to 200 characters to prevent file bloat
- AC8: Hook is registered as StopFailure in settings.json

**Estimated complexity:** Low-Medium (new event type, structured append)

---

### Step 5: Documentation and Sync

Update documentation to reflect the new hooks and `if` conditionals.

**Files to create:** (none)

**Files to modify:**
1. `docs/guide/technical-reference.md` -- add new hooks to hook documentation section
2. `docs/guide/user-guide.md` -- update hook overview with new events
3. `.claude/hooks/` -- install all new hooks (copies from source/hooks/) -- Colby copies during build, verified by Roz
4. `.cursor-plugin/skills/pipeline-setup/SKILL.md` -- sync with Claude Code SKILL.md

**Acceptance criteria:**
- AC1: Technical reference documents all 10 hooks (6 existing + 4 new)
- AC2: User guide mentions new hook events and `if` conditionals
- AC3: All source/hooks/ scripts have corresponding .claude/hooks/ installed copies
- AC4: Cursor plugin SKILL.md matches Claude Code SKILL.md for hook registration

**Estimated complexity:** Low (documentation sync)

## Comprehensive Test Specification

### Step 1 Tests (Unit 2a: `if` Conditionals)

| ID | Category | Description |
|----|----------|-------------|
| T-0020-001 | Happy | settings.json contains `"if"` field on enforce-git.sh Bash hook entry with value `tool_input.command.includes('git ')` |
| T-0020-002 | Happy | settings.json contains `"if"` field on warn-dor-dod.sh SubagentStop hook entry with value `agent_type == 'colby' \|\| agent_type == 'roz'` |
| T-0020-003 | Regression | All existing enforce-git.bats tests pass without modification |
| T-0020-004 | Regression | All existing enforce-paths.bats tests pass without modification |
| T-0020-005 | Regression | All existing enforce-sequencing.bats tests pass without modification |
| T-0020-006 | Regression | All existing enforce-pipeline-activation.bats tests pass without modification |
| T-0020-007 | Boundary | SKILL.md hook registration template contains the same `if` field values as installed settings.json for both enforce-git.sh and warn-dor-dod.sh |
| T-0020-008 | Failure | After Step 1 changes to settings.json, enforce-git.sh called directly (bypassing the `if` filter) with a `git commit` command still exits 2 with BLOCKED output -- verifying that the `if` optimization did not alter the script's enforcement behavior |
| T-0020-009 | Failure | settings.json enforce-git.sh hook entry has a non-empty `"if"` field that is a string (not null, not missing, not an empty string) -- structural validation that Colby did not ship a broken registration |
| T-0020-010 | Failure | settings.json warn-dor-dod.sh hook entry has a non-empty `"if"` field that is a string (not null, not missing, not an empty string) -- structural validation that Colby did not ship a broken registration |

Step 1 ratio: Happy=2, Failure=3. Met (3 >= 2).

### Step 1 Telemetry

Telemetry: Hook spawn count metric. Trigger: after a full pipeline session with `if` conditionals enabled. Absence means: `if` fields were not registered in settings.json or Claude Code is not evaluating them.

### Step 2a Tests (SubagentStart Hook)

| ID | Category | Description |
|----|----------|-------------|
| T-0020-011 | Happy | log-agent-start.sh creates `.claude/telemetry/` directory when missing and appends exactly one JSON line to `session-hooks.jsonl` |
| T-0020-012 | Happy | The appended JSON line is valid JSON (parseable by `jq .`) and contains all required fields: `event` (value "start"), `agent_type`, `agent_id`, `session_id`, `timestamp` |
| T-0020-013 | Failure | Hook exits 0 when `.claude/telemetry/` parent directory is unwritable (test: set parent dir to chmod 444 on macOS, or point CLAUDE_PROJECT_DIR to `/dev/null/subdir` as a portable alternative) and no JSONL file is created |
| T-0020-014 | Failure | Hook exits 0 when jq is not available (PATH manipulated via `hide_jq` helper) AND a valid JSON line is still written to the JSONL file via printf fallback |
| T-0020-015 | Failure | Hook exits 0 and writes a stderr warning when CLAUDE_PROJECT_DIR is unset or empty -- no file is written to the filesystem root |
| T-0020-016 | Boundary | Hook writes `"unknown"` (not empty string) for `agent_type` when the input JSON has an empty or missing `agent_type` field |
| T-0020-017 | Boundary | Hook writes `"unknown"` for `session_id` when the input JSON has an absent `session_id` key |
| T-0020-018 | Boundary | 3 sequential invocations of log-agent-start.sh produce exactly 3 lines in the JSONL file (verified by `wc -l`), confirming append-not-overwrite behavior |
| T-0020-019 | Boundary | `timestamp` field in the JSONL output matches ISO8601 format (regex: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}`) -- consumer contract for hydrate-telemetry.mjs |
| T-0020-020 | Boundary | Hook writes JSONL correctly when CLAUDE_PROJECT_DIR path contains a space (e.g., `"/tmp/my project"`) -- verifies path quoting in the script |
| T-0020-021 | Concurrency | Two simultaneous invocations of log-agent-start.sh (launched as background processes writing to the same JSONL file) produce two independently valid JSON lines with no interleaved content |
| T-0020-022 | Security | Hook does not log any content from the agent prompt or context -- JSONL line contains only the 5 contract fields |
| T-0020-023 | Happy | settings.json contains a SubagentStart hook entry with `hooks_file` pointing to log-agent-start.sh (AC6 registration test) |
| T-0020-024 | Happy | SKILL.md installation manifest includes log-agent-start.sh as a SubagentStart hook entry (AC7 registration test) |
| T-0020-025 | Failure | Hook exits 0 when the JSONL file exists but is not writable (chmod 444 on the file itself) -- verifies write-failure handling distinct from directory-creation failure |

Step 2a ratio: Happy=4, Failure=4. Met (4 >= 4).

### Step 2a Telemetry

Telemetry: `session-hooks.jsonl` line with `event: "start"`. Trigger: every SubagentStart event. Absence means: hook not registered or JSONL write failed.

### Step 2b Tests (SubagentStop Telemetry Hook)

| ID | Category | Description |
|----|----------|-------------|
| T-0020-026 | Happy | log-agent-stop.sh appends a JSON line with event=stop, agent_type, agent_id, session_id, timestamp, and `has_output` set to JSON boolean `true` (not the string "true") when `last_assistant_message` is a non-empty string |
| T-0020-027 | Happy | `has_output` is JSON boolean `false` (not string "false") when `last_assistant_message` is an empty string `""` |
| T-0020-028 | Happy | `has_output` is JSON boolean `false` when `last_assistant_message` is JSON `null` |
| T-0020-029 | Failure | Hook exits 0 when JSONL write fails (directory exists but file is unwritable) |
| T-0020-030 | Failure | Hook exits 0 when jq is not available (PATH manipulated via `hide_jq` helper) AND a valid JSON line with correct `has_output` boolean is still written via printf fallback |
| T-0020-031 | Failure | Hook exits 0 and writes a stderr warning when CLAUDE_PROJECT_DIR is unset or empty -- no file is written to the filesystem root |
| T-0020-032 | Boundary | `has_output` is JSON boolean `false` when the `last_assistant_message` key is entirely absent from the input JSON (not null, not empty -- absent). Verifies `jq -r '.last_assistant_message // empty'` vs `jq -r '.last_assistant_message'` handling |
| T-0020-033 | Boundary | Hook does NOT log the content of `last_assistant_message` -- JSONL line contains `has_output` boolean but no message text, verified by asserting the JSONL line does not contain a known unique string placed in the test input's `last_assistant_message` |
| T-0020-034 | Boundary | `timestamp` field in the JSONL output matches ISO8601 format (regex: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}`) -- consumer contract for hydrate-telemetry.mjs |
| T-0020-035 | Regression | warn-dor-dod.sh called directly with a Colby SubagentStop input (via `build_subagent_stop_input`) exits 0 and produces DoR/DoD output, confirming Step 2b settings.json changes did not alter warn-dor-dod.sh behavior |
| T-0020-036 | Regression | settings.json SubagentStop hook array contains entries for both warn-dor-dod.sh and log-agent-stop.sh (AC6 coexistence verification) |
| T-0020-037 | Concurrency | Two sequential invocations of log-agent-stop.sh appending to the same JSONL file produce exactly 2 lines, each independently valid JSON (verified by `jq -c . < file | wc -l`) |
| T-0020-038 | Boundary | JSONL file containing interleaved start and stop events can be read in full by `jq -s .` without errors (cross-step integration with Step 2a) |

Step 2b ratio: Happy=3, Failure=3. Met (3 >= 3).

### Step 2b Telemetry

Telemetry: `session-hooks.jsonl` line with `event: "stop"`. Trigger: every SubagentStop event. Absence means: hook not registered, JSONL write failed, or SubagentStop events not firing.

### Step 3 Tests (PostCompact Hook)

| ID | Category | Description |
|----|----------|-------------|
| T-0020-039 | Happy | post-compact-reinject.sh outputs pipeline-state.md content to stdout when the file exists in `$CLAUDE_PROJECT_DIR/docs/pipeline/` |
| T-0020-040 | Happy | Output includes context-brief.md content when both files exist |
| T-0020-041 | Happy | Output begins with the header marker `--- Re-injected after compaction ---` (exact string match) |
| T-0020-042 | Failure | Hook outputs nothing (empty stdout) and exits 0 when pipeline-state.md does not exist |
| T-0020-043 | Failure | Hook exits 0 when pipeline-state.md exists but cannot be read (chmod 000) -- outputs nothing or partial content, does not crash |
| T-0020-044 | Failure | Hook exits 0 when CLAUDE_PROJECT_DIR is unset or empty -- outputs nothing, does not attempt to read from filesystem root |
| T-0020-045 | Failure | Hook exits 0 when both pipeline-state.md and context-brief.md exist but are empty (0 bytes) -- outputs the header marker and file labels but no file content |
| T-0020-046 | Boundary | Hook outputs only pipeline-state.md content (with its label) when context-brief.md does not exist -- no error, no placeholder for the missing file |
| T-0020-047 | Boundary | Output contains the exact file path labels `## From: docs/pipeline/pipeline-state.md` and `## From: docs/pipeline/context-brief.md` (matching Notes for Colby #4 format) |
| T-0020-048 | Boundary | settings.json contains a PostCompact hook entry pointing to post-compact-reinject.sh (registration AC test) |
| T-0020-049 | Regression | Existing pre-compact.sh continues to write compaction markers independently of post-compact-reinject.sh |
| T-0020-050 | Security | Hook does not output error-patterns.md or investigation-ledger.md content. Setup: all 5 pipeline files present with unique identifiable content strings. Assert: stdout contains pipeline-state.md's unique string, stdout contains context-brief.md's unique string, stdout does NOT contain error-patterns.md's unique string, stdout does NOT contain investigation-ledger.md's unique string |

Step 3 ratio: Happy=3, Failure=4. Met (4 >= 3).

### Step 3 Telemetry

Telemetry: Post-compaction context includes pipeline-state.md content. Trigger: after any compaction event. Absence means: hook not registered, PostCompact event not firing, or pipeline-state.md does not exist.

### Step 4 Tests (StopFailure Hook)

| ID | Category | Description |
|----|----------|-------------|
| T-0020-051 | Happy | log-stop-failure.sh appends a structured entry to error-patterns.md with agent_type, timestamp, error type, and truncated message |
| T-0020-052 | Happy | Entry format matches: `### StopFailure: {agent_type} at {timestamp}` as the section heading, followed by `- Error: {error_type}` and `- Message: {message}` as bullet points |
| T-0020-053 | Failure | Hook exits 0 when error-patterns.md exists but is not writable (chmod 444) -- logs to stderr, does not crash |
| T-0020-054 | Failure | Hook exits 0 when jq is not available (PATH manipulated via `hide_jq` helper) and still appends a valid entry via printf fallback |
| T-0020-055 | Failure | Hook exits 0 and writes a stderr warning when CLAUDE_PROJECT_DIR is unset or empty -- no file is written to the filesystem root |
| T-0020-056 | Boundary | Hook creates error-patterns.md with a `# Error Patterns` header when the file does not exist, then appends the entry below the header |
| T-0020-057 | Boundary | A 201-character error message in input is truncated to exactly 200 characters in the appended entry (exact boundary test at 201->200) |
| T-0020-058 | Boundary | Hook writes `"unknown"` for missing `agent_type`, `error_type`, and `error_message` fields in the input JSON |
| T-0020-059 | Boundary | Hook handles error message containing special markdown characters (backticks, pipes, brackets) without breaking the markdown structure of the appended entry |
| T-0020-060 | Boundary | Two sequential invocations of log-stop-failure.sh produce two markdown sections separated by at least one blank line (valid markdown rendering) |
| T-0020-061 | Boundary | settings.json contains a StopFailure hook entry pointing to log-stop-failure.sh (AC8 registration test) |
| T-0020-062 | Security | A 500-character error message containing a multi-line stack trace is truncated to 200 characters with no additional lines, stack frames, or sensitive details appearing after the truncation point |
| T-0020-063 | Regression | Existing error-patterns.md content (3 lines of pre-existing text) is preserved after hook appends a new entry -- verified by asserting the original 3 lines still appear at the start of the file |

Step 4 ratio: Happy=2, Failure=3. Met (3 >= 2).

### Step 4 Telemetry

Telemetry: New `### StopFailure` entry in error-patterns.md. Trigger: agent turn ends due to API error. Absence means: hook not registered, StopFailure event not firing, or no API errors occurred (which is the happy path).

### Step 5 Tests (Documentation)

| ID | Category | Description |
|----|----------|-------------|
| T-0020-064 | Happy | technical-reference.md documents all 10 hooks with event type, script name, and one-line purpose description |
| T-0020-065 | Happy | user-guide.md mentions `if` conditionals and lists the 4 new hook events (SubagentStart, SubagentStop telemetry, PostCompact, StopFailure) |
| T-0020-066 | Failure | A source/hooks/ script file (e.g., log-agent-start.sh) without a corresponding .claude/hooks/ installed copy is detected as a mismatch by comparing file lists (`ls source/hooks/*.sh` vs `ls .claude/hooks/*.sh`) |
| T-0020-067 | Failure | Cursor plugin SKILL.md containing a hook entry that is absent from Claude Code SKILL.md is detected as a divergence by diffing the hook registration sections of both files |
| T-0020-068 | Regression | All installed .claude/hooks/ files are byte-identical to their source/hooks/ counterparts (verified by `diff` or `cmp`) |
| T-0020-069 | Regression | Cursor plugin SKILL.md hook registration section matches Claude Code SKILL.md hook registration section |

Step 5 ratio: Happy=2, Failure=2. Met (2 >= 2).

### Step 5 Telemetry

Purely structural step -- no production telemetry applicable.

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `source/hooks/log-agent-start.sh` (SubagentStart) | `{"event":"start","agent_type":"str","agent_id":"str","session_id":"str","timestamp":"ISO8601"}` | `brain/scripts/hydrate-telemetry.mjs` (reads JSONL post-session) | 2a |
| `source/hooks/log-agent-stop.sh` (SubagentStop) | `{"event":"stop","agent_type":"str","agent_id":"str","session_id":"str","timestamp":"ISO8601","has_output":bool}` | `brain/scripts/hydrate-telemetry.mjs` (reads JSONL post-session) | 2b |
| `source/hooks/post-compact-reinject.sh` (PostCompact) | stdout text: pipeline-state.md + context-brief.md content | Claude Code context injection (engine-level consumer) | 3 |
| `source/hooks/log-stop-failure.sh` (StopFailure) | Markdown append to error-patterns.md | Eva (reads error-patterns.md at pipeline end) | 4 |
| `.claude/settings.json` (hook registrations) | JSON with `if` fields | Claude Code hook engine (evaluates `if` before spawning) | 1 |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| log-agent-start.sh -> session-hooks.jsonl | JSONL line (start event) | hydrate-telemetry.mjs | 2a |
| log-agent-stop.sh -> session-hooks.jsonl | JSONL line (stop event) | hydrate-telemetry.mjs | 2b |
| post-compact-reinject.sh -> stdout | Text (pipeline state + context brief) | Claude Code PostCompact injection | 3 |
| log-stop-failure.sh -> error-patterns.md | Markdown section | Eva pipeline-end error review | 4 |
| settings.json `if` fields | JSON conditional expressions | Claude Code hook engine | 1 |

No orphan producers. Every data output has an identified consumer.

## Blast Radius

### Files Created (4 new scripts + 4 test files)
- `source/hooks/log-agent-start.sh`
- `source/hooks/log-agent-stop.sh`
- `source/hooks/post-compact-reinject.sh`
- `source/hooks/log-stop-failure.sh`
- `tests/hooks/log-agent-start.bats`
- `tests/hooks/log-agent-stop.bats`
- `tests/hooks/post-compact-reinject.bats`
- `tests/hooks/log-stop-failure.bats`

### Files Modified
- `.claude/settings.json` -- hook registrations (Steps 1, 2a, 2b, 3, 4)
- `skills/pipeline-setup/SKILL.md` -- installation manifest + template (Steps 1, 2a, 2b, 3, 4)
- `.cursor-plugin/skills/pipeline-setup/SKILL.md` -- Cursor plugin sync (Step 5)
- `tests/hooks/test_helper.bash` -- new JSON builders (Step 2b)
- `docs/guide/technical-reference.md` -- hook documentation (Step 5)
- `docs/guide/user-guide.md` -- hook overview (Step 5)
- `.gitignore` -- add `.claude/telemetry/` (Step 2a)
- `source/hooks/enforce-git.sh` -- documentation comment only (Step 1)

### Files NOT Modified (verified no change needed)
- `source/hooks/enforce-paths.sh` -- no `if` conditional (matcher sufficient)
- `source/hooks/enforce-sequencing.sh` -- no `if` conditional (internal filtering)
- `source/hooks/enforce-pipeline-activation.sh` -- no `if` conditional
- `source/hooks/pre-compact.sh` -- fires rarely, no optimization needed
- `source/hooks/warn-dor-dod.sh` -- script unchanged (only settings.json `if` field added)
- `source/hooks/enforcement-config.json` -- no changes needed

### CI/CD Impact
- None. No CI pipeline configured. Tests run via `bats tests/hooks/`.

### Integration Points
- `brain/scripts/hydrate-telemetry.mjs` -- must be updated (future, not in this ADR) to read `session-hooks.jsonl` in addition to existing session files. The JSONL format is compatible with the existing hydration pattern.

## Data Sensitivity

Not applicable -- no store methods or data access layers. Hook scripts process tool metadata (agent_type, timestamps, error types). No sensitive data (passwords, API keys, user content) is logged. The `log-agent-stop.sh` hook explicitly does NOT log `last_assistant_message` content.

## Notes for Colby

1. **`if` field syntax verification:** The `if` field on hooks uses JavaScript-like expressions. Test the exact syntax `tool_input.command.includes('git ')` against Claude Code's evaluator. If `includes()` is not supported, fall back to a simpler expression or remove the `if` field (the script's internal check is the fallback).

2. **JSONL file path:** Use `"$CLAUDE_PROJECT_DIR/.claude/telemetry/session-hooks.jsonl"`. The `$CLAUDE_PROJECT_DIR` env var is available in hook processes. For Cursor, use `$CURSOR_PROJECT_DIR` with the same fallback pattern as existing hooks.

3. **jq-free fallback for telemetry hooks:** The telemetry hooks (2b) should work without jq by falling back to `printf` for JSON generation. The input parsing can use simple pattern matching (`grep -o`) instead of jq for the 3-4 fields needed. This keeps the hooks runnable on systems where jq is not installed.

4. **PostCompact output format:** The output from post-compact-reinject.sh is injected verbatim by Claude Code. Include clear file path markers:
   ```
   --- Re-injected after compaction ---
   ## From: docs/pipeline/pipeline-state.md
   [contents]
   ## From: docs/pipeline/context-brief.md
   [contents]
   ---
   ```

5. **StopFailure input schema:** The StopFailure hook input schema may include fields like `error_type`, `error_message`, `agent_type`, `agent_id`. Since this is a newer event, parse defensively -- use `jq -r '.field // "unknown"'` pattern for every field.

6. **Template placeholders:** The source/hooks/ scripts should use `{pipeline_state_dir}` for the pipeline state directory path (matching enforce-paths.sh pattern) where applicable. However, most new hooks use `$CLAUDE_PROJECT_DIR` directly for the hooks and telemetry directories, so placeholders may not be needed for all scripts.

7. **Step ordering:** Steps 2a and 2b share the JSONL file and telemetry directory. Step 2a creates the directory; Step 2b assumes it exists. Build 2a first.

8. **test_helper.bash additions:** Add these builders:
   - `build_subagent_start_input "agent_type" "agent_id" "session_id"` -- for SubagentStart hooks
   - `build_subagent_stop_input "agent_type" "agent_id" "session_id" "last_message"` -- for SubagentStop hooks (used by both warn-dor-dod and log-agent-stop)
   - `build_stop_failure_input "agent_type" "error_type" "error_message"` -- for StopFailure hooks

9. **Brain context (proven patterns):** The existing hooks follow a consistent pattern: `set -euo pipefail`, read `INPUT=$(cat)`, parse with jq, early exit for non-matching cases, main logic, `exit 0`. New hooks should follow the same pattern. However, the telemetry hooks can be simpler since they never block (no `set -e` needed if we want to continue on write failure -- use explicit error handling instead).

10. **Retro lesson #003 compliance checklist:** For each new hook, verify:
    - No `exit 2` (except enforcement hooks, and none of these are enforcement)
    - No subagent invocations
    - No test suite execution
    - No brain MCP calls
    - No long-running operations (all operations complete in <10ms)
    - No blocking on external services

---

## DoD: Verification

| # | DoR Requirement | Status | Evidence |
|---|----------------|--------|----------|
| R1 | `if` conditionals on PreToolUse hooks | Covered | Step 1, AC1 (enforce-git.sh) |
| R2 | `if` conditionals on SubagentStop/PreCompact hooks | Covered | Step 1, AC2 (warn-dor-dod.sh); PreCompact skipped (fires rarely, documented in Decision) |
| R3 | SubagentStart hook captures start data | Covered | Step 2a, AC1-AC3 |
| R4 | SubagentStop telemetry hook captures end data | Covered | Step 2b, AC1-AC2 |
| R5 | Telemetry written as JSONL, not brain calls | Covered | Steps 2a/2b, all writes go to session-hooks.jsonl |
| R6 | PostCompact re-injects pipeline-state + context-brief | Covered | Step 3, AC1-AC2 |
| R7 | StopFailure appends to error-patterns.md | Covered | Step 4, AC1-AC2 |
| R8 | All new hooks exit 0 always | Covered | Steps 2a AC4, 2b AC4, 3 AC6, 4 AC5 |
| R9 | Hooks are lightweight (no brain calls, no tests) | Covered | Decision section + Notes for Colby #10 |
| R10 | Scripts in source/hooks/, installed to .claude/hooks/ | Covered | Steps 2a-4 (create in source/hooks/), Step 5 (install) |
| R11 | Hook registrations in settings.json | Covered | Steps 1-4 all modify settings.json |
| R12 | Tests use bats framework | Covered | Steps 2a-4 each create .bats test files |
| R13 | `if` field format matches spec | Covered | Step 1, AC1-AC2 |
| R14 | SubagentStart/Stop input fields used correctly | Covered | Steps 2a/2b, AC3/AC2 |
| R15 | PostCompact outputs to stdout for injection | Covered | Step 3, AC1-AC2 |
| R16 | StopFailure input includes error details | Covered | Step 4, AC1 |
| R17 | Templates use {placeholders} | Covered | Notes for Colby #6 |
| R18 | Existing behavior unchanged | Covered | Step 1 AC3-AC4, Step 2b AC7, Step 3 AC8 |

**Architectural decisions not in the spec:**
- PreCompact hook (`pre-compact.sh`) does NOT get an `if` conditional -- it fires 1-2 times per session, optimization is not worth the complexity. Documented in Decision section.
- enforce-paths.sh, enforce-sequencing.sh, enforce-pipeline-activation.sh do NOT get `if` conditionals -- internal filtering is more reliable than depending on `if` expression evaluator capabilities for nested fields.
- Spawn reduction estimate revised from "~80%" to "~50%" based on actual hook call frequency analysis.
- The PostCompact hook re-injects only 2 files (pipeline-state.md, context-brief.md), not all 5 pipeline files, to keep context injection small.

**Rejected alternatives:** Hook-to-brain direct capture (latency + fragility), single unified hook script (blast radius), `if` on all hooks including Agent hooks (unreliable nested field access).

**Technical constraints discovered:**
- `if` field cannot reliably access `tool_input.subagent_type` (nested field), limiting its usefulness for Agent tool hooks.
- SubagentStop telemetry hook and warn-dor-dod.sh must coexist in the same event array -- Claude Code fires all hooks in the array sequentially.
- The `.claude/telemetry/` directory does not exist by default and must be created by the first hook that writes to it.
