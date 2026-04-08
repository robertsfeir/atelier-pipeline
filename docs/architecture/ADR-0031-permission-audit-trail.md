# ADR-0031: Permission Audit Trail

## DoR: Requirements Extracted

**Sources:** Brain planning decisions (deferred from planning review), `source/claude/hooks/enforce-colby-paths.sh` (enforcement hook pattern), `source/claude/hooks/enforce-eva-paths.sh` (enforcement hook pattern), `source/claude/hooks/enforce-roz-paths.sh` (enforcement hook pattern), `source/claude/hooks/enforce-git.sh` (compound enforcement hook), `source/claude/hooks/enforce-sequencing.sh` (compound enforcement hook), `source/claude/hooks/enforce-pipeline-activation.sh` (compound enforcement hook), `source/claude/hooks/log-agent-stop.sh` (existing JSONL logging pattern), `source/claude/hooks/session-hydrate.sh` (existing SessionStart hydration), `brain/lib/config.mjs` (THOUGHT_TYPES, SOURCE_PHASES enums), `brain/schema.sql` (PostgreSQL enums), `brain/migrations/004-add-pattern-and-seed-types.sql` (migration pattern), `.claude/references/retro-lessons.md`

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Each enforce-*.sh hook emits a JSONL line on block/allow decisions to `~/.claude/logs/enforcement-{DATE}.jsonl` | Task spec | ADR-0031 design constraint, hook side |
| R2 | JSONL fields: `timestamp`, `tool_name`, `agent_type`, `decision` (allowed/blocked), `reason`, `hook_name` | Task spec | ADR-0031 design constraint, hook side |
| R3 | One-line `echo` addition to each hook -- mechanical, Haiku-doable | Task spec | ADR-0031 design constraint, hook side |
| R4 | Hydration script runs at SessionStop (or appended to session-hydrate.sh) | Task spec | ADR-0031 design constraint, hydration side |
| R5 | Hydration reads today's enforcement log, bulk-captures blocked events to brain | Task spec | ADR-0031 design constraint, hydration side |
| R6 | Hydration uses `thought_type: 'enforcement'`, `source_phase: 'permission'` | Task spec | ADR-0031 design constraint, brain side |
| R7 | Skip if log does not exist; exit 0 always (fail-open) | Task spec | ADR-0031 design constraint, hydration side |
| R8 | Rejected alternative: direct hook-to-brain HTTP calls (latency + network dep on enforcement path) | Task spec | ADR-0031 key rejected alternative |
| R9 | Blocked decisions only are brain-captured (allowed decisions log to file but are not brain-captured) | Task spec | ADR-0031 design constraint, noise reduction |
| R10 | Check whether brain schema accepts `thought_type: 'enforcement'` or needs migration | Task spec | ADR-0031 constraint |

**Retro risks:**
- **Lesson #003 (Stop Hook Race Condition):** Enforcement hooks must never block on I/O beyond the local filesystem. The JSONL append is a single `echo >>` -- no network, no brain calls, no blocking. Hydration is post-session, not in the enforcement path.
- **Lesson #004 (Hung Process Retry Loop):** The hydration script must not retry on failure. Single attempt, exit 0 always.

**Spec challenge:** The spec assumes `thought_type: 'enforcement'` can be used with `agent_capture`. **This is wrong.** The brain schema uses PostgreSQL enums for `thought_type` (closed set: decision, preference, lesson, rejection, drift, correction, insight, reflection, handoff, pattern, seed) and `source_phase` (closed set: design, build, qa, review, reconciliation, setup, handoff, devops, telemetry, ci-watch, pipeline). Neither includes `'enforcement'` or `'permission'`. If the hydration script calls `agent_capture` with `thought_type: 'enforcement'`, the Zod validation in `brain/lib/tools.mjs` line 42 (`z.enum(THOUGHT_TYPES)`) will reject it. **Decision:** Use `thought_type: 'insight'` (existing, covers "mid-task discoveries") with `source_phase: 'qa'` (enforcement is a quality gate) and distinguish enforcement captures via `metadata.enforcement_event: true`. This avoids a DB migration and follows the pattern used by `hydrate-telemetry.mjs` (which uses `thought_type: 'insight'` for all telemetry data). The alternative (adding a new enum value) requires a PostgreSQL migration, config.mjs update, and schema.sql update -- disproportionate for this feature.

**SPOF:** The JSONL log file at `~/.claude/logs/enforcement-{DATE}.jsonl`. Failure mode: filesystem permissions prevent writing (read-only filesystem, disk full). Graceful degradation: each hook's echo is wrapped in `|| true` -- write failure is silent, hook continues to its normal exit (enforcement decision is not affected). Hydration script skips if the file does not exist. Zero enforcement decisions are lost in the enforcement path; only the audit trail capture is degraded.

**Anti-goals:**

1. Anti-goal: Direct hook-to-brain HTTP calls for real-time enforcement capture. Reason: Adding network I/O to the enforcement path means every tool call pays latency for brain capture. If the brain is down, hooks would need timeout logic, retry logic, or fail-open logic -- all adding complexity and risk to the critical enforcement path. The JSONL-then-hydrate pattern decouples enforcement from capture. Revisit: If brain latency drops below 10ms consistently AND a real-time enforcement dashboard is requested.

2. Anti-goal: Capturing allowed decisions to brain. Reason: Allowed decisions vastly outnumber blocked decisions (10:1 or higher). Bulk-capturing every allowed decision would flood the brain with low-signal noise, increasing storage cost and degrading search relevance. Allowed decisions log to the local JSONL file for forensic analysis; only blocked decisions carry enough signal for brain capture. Revisit: If Darwin analysis requires allowed-decision patterns (e.g., "which agents use which tools most frequently").

3. Anti-goal: Adding `'enforcement'` as a new `thought_type` enum value (DB migration + config update). Reason: The existing `'insight'` type with metadata tagging is sufficient. Adding a new enum value requires a PostgreSQL migration (008-add-enforcement-type.sql), an update to `brain/lib/config.mjs` THOUGHT_TYPES array, an update to `brain/schema.sql`, and testing against all brain query paths. This is disproportionate overhead for a feature whose primary value is the local JSONL log, with brain capture as a secondary best-effort enrichment. Revisit: If enforcement captures become a primary analysis axis for Darwin (requiring `atelier_browse` filtering by thought_type).

---

## Status

Proposed

## Context

The atelier-pipeline enforcement hooks (`source/claude/hooks/enforce-*.sh`) mechanically block agents from writing outside their designated paths, running unauthorized git commands, invoking agents out of sequence, and similar violations. Today these hooks produce BLOCKED messages on stderr (visible to the user) but leave no persistent record. There is no way to:

1. Audit which enforcement decisions were made during a session
2. Detect patterns across sessions (e.g., "Colby consistently attempts to write to docs/ -- is the ADR step design forcing this?")
3. Feed enforcement patterns into Darwin for pipeline evolution proposals

The solution has two parts: (1) local JSONL logging in each hook (cheap, always-on, no network dependency), and (2) post-session hydration that captures blocked events to the brain (best-effort, fail-open).

### Hook Inventory (10 hooks)

| Hook | What it enforces | Trigger |
|------|-----------------|---------|
| `enforce-agatha-paths.sh` | Agatha writes only to docs/ paths | Write/Edit/MultiEdit |
| `enforce-cal-paths.sh` | Cal writes only to docs/architecture/ | Write/Edit/MultiEdit |
| `enforce-colby-paths.sh` | Colby blocked from protected paths | Write/Edit/MultiEdit |
| `enforce-eva-paths.sh` | Eva writes only to docs/pipeline/ | Write/Edit/MultiEdit |
| `enforce-product-paths.sh` | Robert-spec writes only to docs/product/ | Write/Edit/MultiEdit |
| `enforce-roz-paths.sh` | Roz writes only to test files + docs/pipeline/ | Write/Edit/MultiEdit |
| `enforce-ux-paths.sh` | Sable-ux writes only to docs/ux/ | Write/Edit/MultiEdit |
| `enforce-git.sh` | Git write ops: Ellis only. Test execution: Roz/Colby only | Bash |
| `enforce-sequencing.sh` | Pipeline sequencing gates (Ellis requires Roz QA, Poirot review, telemetry, Robert review) | Agent |
| `enforce-pipeline-activation.sh` | Colby requires active pipeline | Agent |

### Existing JSONL Logging Pattern

`log-agent-stop.sh` already logs SubagentStop events to `{config_dir}/telemetry/session-hooks.jsonl`. The pattern: parse stdin JSON, extract fields, construct a JSONL line, append atomically. This ADR reuses the same pattern for enforcement events, writing to a separate file (`~/.claude/logs/enforcement-{DATE}.jsonl`) to keep enforcement audit separate from telemetry.

### Why Not `{config_dir}/telemetry/`

The enforcement log uses `~/.claude/logs/` (user-level) rather than `{config_dir}/telemetry/` (project-level) because enforcement decisions may involve paths outside the project root (the hook already blocks these). A user-level log captures cross-project enforcement decisions if the user runs multiple projects. The date-partitioned filename (`enforcement-YYYY-MM-DD.jsonl`) keeps files small and enables date-scoped hydration.

## Decision

### JSONL Schema

```json
{
  "timestamp": "2026-04-07T14:30:00Z",
  "tool_name": "Write",
  "agent_type": "colby",
  "decision": "blocked",
  "reason": "Colby cannot write to blocked path. Attempted: docs/pipeline/state.md",
  "hook_name": "enforce-colby-paths"
}
```

Fields:
- `timestamp`: ISO 8601 UTC
- `tool_name`: The tool being intercepted (Write, Edit, MultiEdit, Bash, Agent)
- `agent_type`: From hook input JSON `.agent_type` (empty string for main thread / Eva)
- `decision`: `"blocked"` or `"allowed"`
- `reason`: The human-readable reason (for blocked: the BLOCKED message; for allowed: the exit condition)
- `hook_name`: The hook's basename without `.sh` extension

### Hook Modification Pattern

Each hook gains a logging function and a single call before each `exit` statement. The function:

```bash
log_enforcement() {
  local decision="$1" reason="$2"
  local LOG_DIR="$HOME/.claude/logs"
  local LOG_FILE="$LOG_DIR/enforcement-$(date -u +%Y-%m-%d).jsonl"
  mkdir -p "$LOG_DIR" 2>/dev/null || true
  printf '{"timestamp":"%s","tool_name":"%s","agent_type":"%s","decision":"%s","reason":"%s","hook_name":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$TOOL_NAME" "${AGENT_TYPE:-}" "$decision" "$reason" "HOOK_NAME" \
    >> "$LOG_FILE" 2>/dev/null || true
}
```

- `HOOK_NAME` is a constant per script (e.g., `enforce-colby-paths`)
- The `|| true` ensures write failures never affect the enforcement decision
- `AGENT_TYPE` is already parsed in most hooks; where it is not (path hooks that check agent_type to skip), the variable defaults to empty string

### Hydration Script

`source/claude/hooks/session-hydrate-enforcement.sh` runs at SessionStop. It:

1. Checks for today's enforcement log at `~/.claude/logs/enforcement-$(date -u +%Y-%m-%d).jsonl`
2. If absent: exit 0
3. Filters for `"decision":"blocked"` lines only
4. For each blocked event: calls the brain's `agent_capture` via the existing hydrate-telemetry.mjs pattern (direct DB insert, not MCP tool call)
5. Uses: `thought_type: 'insight'`, `source_agent: 'eva'`, `source_phase: 'qa'`, `metadata: { enforcement_event: true, hook_name: "...", agent_type: "...", tool_name: "...", decision: "blocked", reason: "..." }`
6. Exit 0 always, regardless of success or failure

**Alternative: Append to session-hydrate.sh instead of a new script.** Decided: new script. The existing session-hydrate.sh calls hydrate-telemetry.mjs for T1 JSONL hydration, which is a different concern. Keeping enforcement hydration separate makes it independently deployable and removable.

### Brain Capture Shape

```
thought_type: 'insight'
source_agent: 'eva'
source_phase: 'qa'
importance: 0.4
content: "Enforcement: [hook_name] blocked [agent_type] from [tool_name]. Reason: [reason]"
metadata: {
  enforcement_event: true,
  hook_name: string,
  agent_type: string,
  tool_name: string,
  decision: "blocked",
  reason: string,
  session_date: "YYYY-MM-DD"
}
```

Queryable via `agent_search` with query "enforcement blocked [agent_name]" or `atelier_browse` with metadata filter `enforcement_event: true`.

## Alternatives Considered

**Alternative A: Direct hook-to-brain HTTP calls.** Each hook calls the brain REST API or MCP tool on every enforcement decision. Rejected: adds 50-200ms latency per tool call, requires network availability in the enforcement path, requires error handling for brain downtime. The JSONL-then-hydrate pattern is zero-latency in the enforcement path.

**Alternative B: New `thought_type: 'enforcement'` and `source_phase: 'permission'` enum values.** Requires migration 008, config.mjs update, schema.sql update. Rejected for now: disproportionate infrastructure change for a best-effort capture feature. The `'insight'` type with metadata tagging is queryable and sufficient. See anti-goal #3.

**Alternative C: Log to `{config_dir}/telemetry/enforcement.jsonl` (project-level).** Rejected: enforcement events may involve cross-project paths. User-level logging at `~/.claude/logs/` captures all enforcement decisions regardless of which project triggered them. Also avoids adding files to the project's git-tracked directory.

## Consequences

**Positive:**
- Every enforcement decision (block and allow) is durably logged to local JSONL
- Blocked decisions are captured to brain for pattern detection by Darwin
- Zero performance impact on the enforcement path (single echo, no network)
- Fail-open hydration: missed captures never block enforcement
- Date-partitioned log files enable easy cleanup and date-scoped analysis

**Negative:**
- 10 hook files modified (one function + call sites per hook). Blast radius is wide but each change is mechanical and identical.
- JSONL log grows indefinitely without cleanup (mitigated: date-partitioned, one file per day, each line ~200 bytes)
- Using `thought_type: 'insight'` with metadata tagging is less queryable than a dedicated enum value (must filter by metadata, not by type)

**Neutral:**
- The hydration script is a new file but follows the established pattern (session-hydrate.sh, hydrate-telemetry.mjs). Deployment via the existing plugin install mechanism.

---

## Implementation Plan

### Step 1: JSONL Logging in Enforcement Hooks

**Files to modify (10):**
1. `source/claude/hooks/enforce-agatha-paths.sh`
2. `source/claude/hooks/enforce-cal-paths.sh`
3. `source/claude/hooks/enforce-colby-paths.sh`
4. `source/claude/hooks/enforce-eva-paths.sh`
5. `source/claude/hooks/enforce-product-paths.sh`
6. `source/claude/hooks/enforce-roz-paths.sh`
7. `source/claude/hooks/enforce-ux-paths.sh`
8. `source/claude/hooks/enforce-git.sh`
9. `source/claude/hooks/enforce-sequencing.sh`
10. `source/claude/hooks/enforce-pipeline-activation.sh`

**Files to create:** None

**Justification for 10 files:** All 10 changes are identical in structure (add `log_enforcement` function + call sites). Each hook already parses `TOOL_NAME` and `AGENT_TYPE`. The modification is: (1) add the function definition at the top of each script, (2) add `log_enforcement "blocked" "reason"` before each `exit 2`, (3) optionally add `log_enforcement "allowed" "exit condition"` before key `exit 0` statements. This is mechanical text substitution -- Haiku can do it file by file.

**Acceptance criteria:**
- Each of the 10 hooks has a `log_enforcement` function that writes a JSONL line to `~/.claude/logs/enforcement-$(date -u +%Y-%m-%d).jsonl`
- Every `exit 2` (blocked) path calls `log_enforcement "blocked" "reason"` before exiting
- The `|| true` on the echo ensures write failures never affect exit codes
- `mkdir -p` creates the log directory if absent
- No network calls, no brain calls in any hook
- Existing hook behavior is unchanged (same exit codes, same stderr messages)
- JSONL format matches the schema defined in the Decision section

**Complexity:** Medium (10 files, but all changes are mechanically identical). Each file gets ~10 lines added (function definition + 1-3 call sites). Total ~100 lines across 10 files. S1: "After this step, I can see enforcement decisions logged to JSONL." S2: 10 files (at limit, but all identical changes). S3: Testable by running hooks with mock input. S4: Revertable by removing the function + calls. S5: One clear behavior (JSONL logging).

**After this step, I can:** see enforcement decisions (blocked and allowed) logged to `~/.claude/logs/enforcement-YYYY-MM-DD.jsonl` after any hook fires.

### Step 2: Hydration Script for Brain Capture

**Files to modify:**
1. `source/claude/hooks/session-hydrate.sh` -- add a call to the new enforcement hydration script (or register it as a separate SessionStop hook)

**Files to create:**
1. `source/claude/hooks/session-hydrate-enforcement.sh` -- reads today's enforcement log, filters blocked events, bulk-captures to brain

**Acceptance criteria:**
- `session-hydrate-enforcement.sh` exists and is executable
- Script reads `~/.claude/logs/enforcement-$(date -u +%Y-%m-%d).jsonl`
- Script filters for `"decision":"blocked"` lines only
- For each blocked line: inserts a brain thought with `thought_type: 'insight'`, `source_agent: 'eva'`, `source_phase: 'qa'`, `metadata.enforcement_event: true`
- Script skips silently if log file does not exist
- Script exits 0 always (fail-open)
- Script does not require brain to be available (checks before attempting inserts)
- Script follows the established hydration pattern from hydrate-telemetry.mjs (direct DB insert, not MCP tool call)
- `session-hydrate.sh` calls the enforcement hydration script after telemetry hydration (or the new script is registered as a separate SessionStop hook entry)

**Complexity:** Low-Medium. One new file (~60-80 lines following hydrate-telemetry.mjs pattern), one existing file modified (1-2 lines to call the new script). S1: "After this step, I can see blocked enforcement decisions captured in the brain." S2: 2 files (1 create, 1 modify). S3: Testable with a mock enforcement log. S4: Revertable by removing the file and the call. S5: One clear behavior (enforcement hydration).

**After this step, I can:** query the brain for enforcement patterns (e.g., "which agents are most frequently blocked, and by which hooks") and see Darwin incorporate enforcement signals into pipeline evolution proposals.

---

## Test Specification

| ID | Category | Description |
|----|----------|-------------|
| T-0031-001 | Hook logging | Each of the 10 enforce-*.sh hooks contains a `log_enforcement` function |
| T-0031-002 | Hook logging | Every `exit 2` path in each hook is preceded by a `log_enforcement "blocked"` call |
| T-0031-003 | Hook logging | JSONL output contains all 6 required fields: timestamp, tool_name, agent_type, decision, reason, hook_name |
| T-0031-004 | Hook logging | Log directory is `~/.claude/logs/` (user-level, not project-level) |
| T-0031-005 | Hook logging | Log filename contains today's date in `enforcement-YYYY-MM-DD.jsonl` format |
| T-0031-006 | Hook logging | Write failures in `log_enforcement` do not change the hook's exit code |
| T-0031-007 | Hook logging | No network calls or brain calls exist in any enforcement hook |
| T-0031-008 | Hydration | `session-hydrate-enforcement.sh` exists and is executable |
| T-0031-009 | Hydration | Hydration script filters for `"decision":"blocked"` only (does not capture allowed) |
| T-0031-010 | Hydration | Brain captures use `thought_type: 'insight'` (not a new enum value) |
| T-0031-011 | Hydration | Brain captures include `metadata.enforcement_event: true` |
| T-0031-012 | Hydration | Script exits 0 when log file does not exist |
| T-0031-013 | Hydration | Script exits 0 when brain is unavailable |
| T-0031-014 | Hydration | Script exits 0 on any error (fail-open) |
| T-0031-015 | Failure: hook blocks on I/O | No enforcement hook contains `curl`, `wget`, `node`, or network calls in the enforcement path |
| T-0031-016 | Failure: enforcement behavior changed | Each hook's exit codes are unchanged (same `exit 0` and `exit 2` paths as before) |
| T-0031-017 | Failure: new thought_type enum | No file in `brain/migrations/` adds an `'enforcement'` thought_type value |
| T-0031-018 | Failure: allowed events captured to brain | Hydration script grep confirms only blocked events are passed to brain insert |
| T-0031-019 | Failure: hydration blocks | Hydration script contains no retry loops, no sleep, no blocking waits |
| T-0031-020 | Integration | `session-hydrate.sh` calls or references `session-hydrate-enforcement.sh` |
| T-0031-021 | Consistency | JSONL schema in all 10 hooks matches the schema defined in the ADR Decision section |
| T-0031-022 | Consistency | Brain capture metadata shape matches the schema in the ADR Decision section |

**Test counts:** 22 total. 11 happy path, 11 failure/negative/consistency. Failure >= happy path: satisfied.

---

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| enforce-*.sh hooks (10) | JSONL lines: `{ timestamp, tool_name, agent_type, decision, reason, hook_name }` | `session-hydrate-enforcement.sh`, forensic analysis |
| `session-hydrate-enforcement.sh` | Brain thought: `thought_type: 'insight'`, `metadata.enforcement_event: true` + enforcement fields | `agent_search` queries, Darwin pattern detection, `atelier_browse` |
| `session-hydrate.sh` (modified) | Calls `session-hydrate-enforcement.sh` | Hook lifecycle (SessionStop or SessionStart) |

---

## Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| 10 enforce-*.sh hooks | JSONL line per decision | Local log file | Step 1 |
| Local log file `enforcement-{DATE}.jsonl` | Blocked decision lines | `session-hydrate-enforcement.sh` | Step 2 |
| `session-hydrate-enforcement.sh` | Brain thought with `metadata.enforcement_event: true` | `agent_search`, Darwin, `atelier_browse` | Step 2 |
| `session-hydrate.sh` | Calls enforcement hydration | `session-hydrate-enforcement.sh` execution | Step 2 |

No orphan producers. Every producer has a documented consumer.

---

## Data Sensitivity

| Method/Field | Classification | Rationale |
|-------------|---------------|-----------|
| Enforcement JSONL log | `public-safe` | Contains tool names, agent types, and enforcement reasons -- no PII, no secrets, no file content |
| Brain enforcement captures | `public-safe` | Same data as JSONL, no sensitive content. File paths in reason strings are project-relative. |
| `log_enforcement` function | `public-safe` | Writes operational metadata only |

---

## Notes for Colby

- **Step 1 model recommendation: Haiku.** All 10 hooks need the same mechanical change. Score: -2 (mechanical text addition). Scout swarm: one "Existing-code" scout reads all 10 enforce-*.sh files. One "Patterns" scout greps for `exit 2` across all hooks to count call sites.
- **Step 2 model recommendation: Haiku (hydration script), Haiku (session-hydrate.sh edit).** The hydration script follows the pattern of `hydrate-telemetry.mjs` and `session-hydrate.sh`. Score: -2 (mechanical, follows pattern). Scout swarm: one "Existing-code" scout reads `session-hydrate.sh` and `hydrate-telemetry.mjs` (first 100 lines).
- **The `log_enforcement` function should be defined once at the top of each script**, not sourced from a shared file. Each hook is a standalone script (no shared library pattern in the existing hooks). Copy-pasting the function is intentional -- it keeps each hook self-contained per the existing design.
- **Do NOT add `'enforcement'` to `THOUGHT_TYPES` in `brain/lib/config.mjs`.** The ADR explicitly decided to use `thought_type: 'insight'` with `metadata.enforcement_event: true`. See anti-goal #3 and the spec challenge section.
- **The `AGENT_TYPE` variable:** Path enforcement hooks (enforce-*-paths.sh) parse `agent_type` from the hook input JSON via the frontmatter `name` field mapping. Some hooks (enforce-eva-paths.sh) check `agent_type` to skip (if agent_type is set, it's a subagent, not Eva). The `log_enforcement` function should use `${AGENT_TYPE:-}` with a default to handle hooks where the variable is not set.
- **The `reason` parameter needs JSON-safe escaping.** The reason strings may contain double quotes (from file paths). Use `printf` with `%s` and pipe through a minimal escaper, or use single quotes in reason strings. The simplest approach: `reason=$(echo "$reason" | sed 's/"/\\"/g')` before the printf.
- **Hydration script is Node.js (not bash).** It needs DB access via the existing `brain/lib/db.mjs` and `brain/lib/embed.mjs` modules. Model it on `hydrate-telemetry.mjs`: resolve config, create pool, run migrations, read JSONL, insert thoughts, close pool.
- **Step 1 has 10 files but passes the sizing gate.** S1: demoable (enforcement JSONL logging). S2: 10 files, at the limit, but all changes are identical (a function definition + 1-3 call sites). S3: independently testable (run any hook with mock input, check JSONL output). S4: revert-cheap (remove function + calls). The 10-file count is justified because the change is mechanical duplication, not 10 distinct behaviors.

---

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Each hook emits JSONL on block/allow | Done | Step 1, all 10 hooks modified |
| R2 | JSONL fields match schema | Done | Schema defined in Decision, tested by T-0031-003 |
| R3 | One-line echo addition, Haiku-doable | Done | Mechanical function + call site, Haiku recommended |
| R4 | Hydration script runs at SessionStop/SessionStart | Done | Step 2, called from session-hydrate.sh |
| R5 | Hydration reads today's log, bulk-captures blocked events | Done | Step 2 acceptance criteria |
| R6 | Uses `thought_type: 'insight'`, `source_phase: 'qa'` (not new enum) | Done | Decision section, spec challenge analysis |
| R7 | Skip if log absent, exit 0 always | Done | Step 2 acceptance criteria, T-0031-012/013/014 |
| R8 | Direct hook-to-brain calls rejected | Done | Alternatives Considered, anti-goal #1 |
| R9 | Only blocked decisions brain-captured | Done | Step 2 acceptance criteria, T-0031-009/018 |
| R10 | Brain schema checked for thought_type compatibility | Done | Spec challenge section: enum is closed, 'enforcement' not accepted, using 'insight' instead |

**Grep check:** `TODO/FIXME/HACK/XXX` in output -> 0
**Template:** All sections filled, no TBD, no placeholders
