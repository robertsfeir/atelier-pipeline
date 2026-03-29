# ADR-0013: CI Watch (Self-Healing CI)

## DoR: Requirements Extracted

| # | Requirement | Source | Priority |
|---|-------------|--------|----------|
| R1 | `ci_watch_enabled` flag in `pipeline-config.json`, default `false` | Spec AC#1 | Must |
| R2 | `ci_watch_max_retries` in `pipeline-config.json`, default `3`, set during setup | Spec AC#2 | Must |
| R3 | Offered as opt-in during `/pipeline-setup` Step 6c | Spec AC#3 | Must |
| R4 | After Ellis pushes, background process monitors CI via `gh run watch` or `glab ci status` | Spec AC#4 | Must |
| R5 | CI pass: user notified with run link | Spec AC#5 | Must |
| R6 | CI fail: failure logs pulled, Roz diagnose, Colby fix, Roz verify -- autonomous | Spec AC#6 | Must |
| R7 | Hard pause before Ellis pushes fix -- user must approve | Spec AC#7 | Must |
| R8 | Retry loop respects `ci_watch_max_retries` | Spec AC#8 | Must |
| R9 | 30-minute timeout prompts user | Spec AC#9 | Must |
| R10 | Watch dies with session -- no orphan processes | Spec AC#10 | Must |
| R11 | Works with both `gh` (GitHub) and `glab` (GitLab) | Spec AC#11 | Must |
| R12 | Brain captures CI failure pattern after resolution | Spec AC#12 | Should |
| R13 | No platform CLI configured blocks enablement | Spec edge case | Must |
| R14 | Failure logs truncated to ~200 lines | Spec NFR | Must |
| R15 | One watch per session -- new push replaces active watch | Spec scope | Must |
| R16 | Roz/Colby failure during auto-fix stops loop with report | Spec edge case | Must |
| R17 | Dual-tree: source/ templates + .claude/ installed copies | Project convention | Must |

**Retro risks:**
- Lesson #003 (Stop Hook Race Condition): CI Watch polls externally, not running test suites in hooks. No overlap. But the polling bash command must not hang -- lesson #004 (Hung Process Retry Loop) applies: if `gh run watch` hangs, diagnose, do not retry blindly.
- Lesson #004: `run_in_background` has a default 2-minute timeout for Bash. CI Watch must use explicit long timeouts or a polling loop with short individual commands.

---

## Status

Proposed

## Context

When Ellis pushes code, CI can fail for reasons not caught locally. Today the user discovers failures manually and re-enters the debug flow. CI Watch automates the post-push monitoring and fix cycle: watch CI status, diagnose failures via Roz, fix via Colby, verify via Roz, pause for user approval, and push the fix via Ellis. The feature is opt-in, session-scoped, and supports both GitHub Actions and GitLab CI.

This is a pipeline infrastructure feature. All deliverables are markdown files (rules, references, agent personas) and bash scripts (hooks) -- no application code.

### Spec Challenge

The spec assumes `run_in_background` with the Bash tool can run a 30-minute polling process reliably. If this is wrong (e.g., Bash `run_in_background` has a hard timeout shorter than 30 minutes, or background processes cannot report results back to the conversation), the design fails because the entire non-blocking watch mechanism depends on this capability.

Mitigation: the design uses a polling loop with short individual `gh run list` / `glab ci status` commands (30-second intervals, each with a 60-second timeout) rather than a single long-running `gh run watch`. This means even if `run_in_background` has limits, the polling approach degrades gracefully to a synchronous check-and-wait pattern that Eva can drive from the main thread.

**SPOF:** The CI status polling command (`gh run list` / `glab ci status`). If the platform CLI is broken, unauthenticated, or the API is down, the entire watch loop fails. **Failure mode:** polling returns errors or hangs. **Graceful degradation:** after 3 consecutive polling errors, the watch stops and Eva notifies the user: "CI Watch lost connection to [platform]. Check CI status manually: [link]." The pipeline continues without the watch -- it is advisory, not blocking.

### Anti-Goals

1. **Anti-goal: Cross-session persistence.** Reason: the watch process is tied to the Claude Code session lifetime; adding persistence would require external state management (database, file locks, cron) which is out of scope for a session-scoped tool. Revisit: if users report frequent session closures during active watches.

2. **Anti-goal: Custom CI systems (Jenkins, CircleCI, etc.).** Reason: the platform abstraction already exists in `pipeline-config.json` for `gh` and `glab` only; adding arbitrary CI systems would require a plugin architecture for CI adapters. Revisit: if a user requests a specific non-gh/glab CI system with a CLI that has equivalent `run list`/`status` commands.

3. **Anti-goal: Pre-push CI gates (running CI checks locally before push).** Reason: this is a separate concern from post-push monitoring; pre-push gates like `make ci-full` already exist as a pattern in the retro lessons. Revisit: never -- these are architecturally distinct features that should not be conflated.

## Decision

Implement CI Watch as an Eva orchestration protocol embedded in the existing pipeline rules, with platform-specific CI commands abstracted through `pipeline-config.json`. The watch runs as a background Bash polling loop launched after Ellis pushes, with the fix cycle using existing Roz/Colby/Ellis subagent invocations from the main thread.

### Architecture

```
Ellis pushes -> Eva launches background poll (run_in_background)
  -> Poll loop: gh run list / glab ci status every 30s
  -> On completion: Eva reads result
     -> PASS: notify user
     -> FAIL: pull logs (truncate 200 lines) -> Roz diagnose -> Colby fix
        -> Roz verify -> HARD PAUSE -> user approves -> Ellis push -> re-watch
  -> On timeout (30 min): prompt user
  -> On retry exhaustion: stop, report cumulative failures
```

**Key design choices:**
- Polling loop (not `gh run watch`) -- more resilient, works with both platforms uniformly, and handles `run_in_background` timeout constraints
- Fix cycle runs on the main thread (not background) -- subagent invocations (Roz, Colby, Ellis) require main-thread orchestration
- Platform commands stored in `pipeline-config.json` as `ci_watch_poll_command` and `ci_watch_log_command` -- computed at setup time from `platform_cli`
- State tracked in `pipeline-state.md` via PIPELINE_STATUS JSON marker fields: `ci_watch_active`, `ci_watch_retry_count`, `ci_watch_commit_sha`

## Alternatives Considered

### Alternative A: `gh run watch` / `glab ci trace` (Long-Running Background Process)

Use the platform's built-in watch commands which block until CI completes.

**Pros:**
- Simpler implementation -- one command, platform handles polling
- `gh run watch` provides real-time streaming output

**Cons:**
- `glab` has no exact equivalent to `gh run watch` -- `glab ci trace` streams job logs but does not wait for completion across all jobs
- `run_in_background` Bash timeout behavior is uncertain for 30+ minute processes
- A single hung command is harder to recover from than a polling loop
- No intermediate state -- either watching or not, no partial status reporting

**Rejected because:** platform asymmetry between `gh` and `glab` would require two completely different watch implementations, and the long-running process model is fragile with `run_in_background`.

### Alternative B: Main-Thread Synchronous Polling (No Background)

Eva polls CI status from the main thread in a loop, blocking conversation.

**Pros:**
- Simplest implementation -- no background process management
- Full access to subagent invocation from the polling context

**Cons:**
- Blocks the user's conversation entirely during CI wait
- Violates the "non-blocking" requirement from the spec
- User cannot do other work while waiting for CI

**Rejected because:** the spec explicitly requires non-blocking behavior. However, this is the graceful degradation fallback if `run_in_background` proves unreliable.

## Consequences

**Positive:**
- Automated CI failure detection and fix cycle reduces manual intervention
- Opt-in design means zero impact on users who do not enable it
- Platform abstraction through config means no code branching for gh vs glab
- Brain capture of CI patterns builds institutional memory for WARN injection

**Negative:**
- Adds complexity to Eva's orchestration rules (~80 lines of protocol)
- `run_in_background` behavior for long polling is unproven in production use
- The 30-second polling interval means up to 30 seconds of latency between CI completion and detection

**Risks:**
- If `run_in_background` has undocumented limits, the watch may silently die. Mitigation: the polling loop has a finite iteration count (60 iterations), so a dead watch is detected by the absence of a completion notification. On the next user interaction, Eva checks `ci_watch_active` in PIPELINE_STATUS and, if the watch has been running longer than 35 minutes without reporting, declares it dead and notifies the user.
- The fix cycle runs autonomously (Roz -> Colby -> Roz) without user oversight until the hard pause. If the autonomous fix introduces a different regression, it will be caught on the next CI run (retry loop).

## Implementation Plan

### Step 1: Config Schema Extension

Add CI Watch fields to the pipeline-config.json template and installed copy.

**Files to create/modify:**
- `source/pipeline/pipeline-config.json` -- add `ci_watch_enabled`, `ci_watch_max_retries` fields
- `.claude/pipeline-config.json` -- add same fields to installed copy (literal values)

**Changes:**
```json
{
  "ci_watch_enabled": false,
  "ci_watch_max_retries": 3
}
```

**Acceptance criteria:**
- Both `ci_watch_enabled` (boolean, default `false`) and `ci_watch_max_retries` (integer, default `3`) exist in the config schema
- Source template uses same defaults as installed copy
- Existing config fields are unchanged

**Estimated complexity:** Low (2 files, additive JSON changes)

### Step 2: Setup Step 6c Integration

Add CI Watch opt-in to the pipeline-setup skill, following the Step 6a (Sentinel) and Step 6b (Agent Teams) pattern.

**Files to create/modify:**
- `skills/pipeline-setup/SKILL.md` -- add Step 6c section after Step 6b

**Changes:**
Add a new "Step 6c: CI Watch (Opt-In)" section that:
1. Offers CI Watch after Agent Teams offer (Step 6b)
2. Gates on platform CLI being configured: if `platform_cli` is empty in `pipeline-config.json`, block with message "CI Watch requires `gh` or `glab`. Configure a platform first."
3. If platform CLI exists, checks authentication: `gh auth status` / `glab auth status`
4. Asks user to set max retries (default 3)
5. Sets `ci_watch_enabled: true` and `ci_watch_max_retries: N` in `pipeline-config.json`
6. Updates setup summary to show CI Watch status

**Acceptance criteria:**
- Step 6c follows Step 6b in the setup flow
- Platform CLI must be configured before CI Watch can be enabled
- Auth check runs before enablement
- Max retries is configurable with default 3
- Idempotent: re-running setup with CI Watch already enabled skips mutation
- Setup summary includes CI Watch line

**Estimated complexity:** Medium (1 file, follows established pattern from 6a/6b but adds platform gate)

### Step 3: Eva CI Watch Protocol

Add the CI Watch orchestration protocol to pipeline-orchestration.md. This is the core logic: when to start a watch, how to poll, how to handle results, the fix cycle, timeouts, and retry limits.

**Files to create/modify:**
- `source/rules/pipeline-orchestration.md` -- add `<protocol id="ci-watch">` section
- `.claude/rules/pipeline-orchestration.md` -- add same protocol (installed copy, literal values)

**Changes:**
Add a new protocol section containing:

1. **Activation gate:** `ci_watch_enabled: true` in `pipeline-config.json` AND Ellis just pushed to remote
2. **Watch launch:** Eva runs background Bash polling loop via `run_in_background`:
   - GitHub: `gh run list --commit {sha} --json status,conclusion,url --limit 1`
   - GitLab: `glab ci status --branch {branch} --output json`
   - Poll every 30 seconds, max 60 iterations (30 minutes)
   - On each poll: check if status is `completed` / `success` / `failure`
3. **On CI pass:** Eva notifies user: "CI passed on [branch]. [link to run]"
4. **On CI fail:**
   - Pull failure logs: `gh run view {run_id} --log-failed | tail -200` / `glab ci trace --branch {branch} | tail -200`
   - Write truncated logs to a temp context
   - Invoke Roz in investigation mode with failure logs (autonomous)
   - Invoke Colby with Roz's diagnosis (autonomous)
   - Invoke Roz to verify Colby's fix (autonomous)
   - **HARD PAUSE** -- present to user: failure summary, what changed, Roz verdict
   - User approves -> invoke Ellis to push -> increment retry counter -> re-watch
   - User rejects -> stop, user handles manually
5. **On timeout (30 min):** prompt user: "CI has been running for 30 minutes. Keep waiting or abandon?"
6. **On retry exhaustion:** stop with cumulative failure report
7. **On agent failure:** if Roz or Colby fails during auto-fix, stop the loop, report which agent failed and its output
8. **Watch replacement:** new Ellis push replaces active watch (set `ci_watch_active: false` on old, start new)
9. **Brain capture:** after resolution, `agent_capture` with `thought_type: 'pattern'`, `source_agent: 'eva'`, `source_phase: 'ci-watch'`, content describing the failure pattern and fix

**Pipeline-state.md marker fields added to PIPELINE_STATUS:**
- `ci_watch_active`: boolean
- `ci_watch_retry_count`: integer
- `ci_watch_commit_sha`: string

**Acceptance criteria:**
- Protocol activates only when `ci_watch_enabled: true` AND Ellis pushes
- Background polling uses platform-appropriate commands from `pipeline-config.json`
- Failure logs are truncated to 200 lines
- Fix cycle is Roz -> Colby -> Roz (autonomous), then HARD PAUSE before Ellis push
- Retry counter increments after each fix push; stops at `ci_watch_max_retries`
- 30-minute timeout prompts user (not auto-abandon)
- New push replaces active watch
- Brain captures CI failure patterns after resolution
- Protocol integrates with existing mandatory gates (Roz verifies Colby, Ellis commits)
- Dual-tree: source/ uses `{pipeline_state_dir}` placeholder, .claude/ uses literal `docs/pipeline`

**Estimated complexity:** High (2 files, ~80 lines each, core feature logic)

### Step 4: Pipeline Operations CI Watch Reference

Add CI Watch operational details to pipeline-operations.md -- the platform command reference, polling loop pseudocode, and failure log extraction commands.

**Files to create/modify:**
- `source/references/pipeline-operations.md` -- add `<operations id="ci-watch">` section
- `.claude/references/pipeline-operations.md` -- add same section (installed copy)

**Changes:**
Add an operations section containing:

1. **Platform command reference table:**

| Operation | GitHub (`gh`) | GitLab (`glab`) |
|-----------|--------------|-----------------|
| Check run status | `gh run list --commit {sha} --json status,conclusion,url --limit 1` | `glab ci list --branch {branch} -o json \| head -1` |
| Get failure logs | `gh run view {run_id} --log-failed \| tail -200` | `glab ci trace {job_id} \| tail -200` |
| Get run URL | Included in `gh run list` JSON output | `glab ci view --branch {branch} --web` (URL construction) |
| Auth check | `gh auth status` | `glab auth status` |

2. **Polling loop pseudocode** (what Eva's background Bash script does)
3. **Failure log truncation rules:** last 200 lines per failed job; if multiple jobs fail, concatenate with job headers, total cap at 400 lines

**Acceptance criteria:**
- Commands are correct for both `gh` and `glab` CLIs
- Log truncation rules are specified
- Polling interval (30s) and max iterations (60 = 30 min) are documented
- Dual-tree sync

**Estimated complexity:** Medium (2 files, reference documentation with command tables)

### Step 5: Invocation Templates for CI Watch Agents

Add invocation templates for the CI Watch-specific agent invocations: Roz CI investigation, Colby CI fix, and Roz CI verification.

**Files to create/modify:**
- `source/references/invocation-templates.md` -- add CI Watch templates
- `.claude/references/invocation-templates.md` -- add same templates (installed copy)

**Changes:**
Add three templates:

1. **`<template id="roz-ci-investigation">`** -- Roz investigates CI failure logs
   - TASK: "Investigate CI failure -- [truncated failure log summary]"
   - READ: failure logs (passed as CONTEXT, not files), relevant source files
   - CONSTRAINTS: diagnose from logs + code; identify root cause file:line; do not write code
   - OUTPUT: CI failure diagnosis with root cause, affected files, recommended fix

2. **`<template id="colby-ci-fix">`** -- Colby fixes CI failure based on Roz diagnosis
   - TASK: "Fix CI failure -- [Roz diagnosis summary]"
   - CONTEXT: Roz's diagnosis, CI failure logs
   - CONSTRAINTS: fix the specific CI failure; run lint; do not modify test assertions
   - OUTPUT: fix report with files changed

3. **`<template id="roz-ci-verify">`** -- Roz verifies Colby's CI fix
   - TASK: "Verify CI fix -- [fix summary]"
   - CONSTRAINTS: run test suite locally; verify fix addresses root cause; check for regressions
   - OUTPUT: QA verdict (PASS/FAIL)

**Acceptance criteria:**
- Templates follow the existing XML tag format (task, brain-context, context, read, constraints, output)
- CI failure logs are passed in CONTEXT (not READ) because they are ephemeral, not files
- Roz CI investigation is distinct from Roz bug investigation (different constraints -- working from CI logs, not user symptoms)
- Dual-tree sync

**Estimated complexity:** Medium (2 files, follows established template pattern)

### Step 6: Enforce-Sequencing Hook CI Watch Gate

Add a gate to the enforce-sequencing hook that allows Ellis to push during CI Watch retry cycles without requiring a fresh Roz QA PASS from the pipeline's main build phase. The CI Watch has its own Roz verification in the fix cycle.

**Files to create/modify:**
- `source/hooks/enforce-sequencing.sh` -- add CI Watch exemption to Gate 1
- `.claude/hooks/enforce-sequencing.sh` -- add same exemption (installed copy)

**Changes:**
In Gate 1 (Ellis requires Roz QA PASS), add a check: if `ci_watch_active` is `true` in PIPELINE_STATUS and `roz_qa` is `CI_VERIFIED` (a new status distinct from the build-phase `PASS`), allow Ellis through. This prevents the hook from blocking Ellis during the CI Watch fix cycle while maintaining the gate for normal build-phase commits.

The `CI_VERIFIED` status is written by Eva to PIPELINE_STATUS after Roz verifies Colby's CI fix, distinguishing CI Watch verification from build-phase QA.

**Acceptance criteria:**
- Ellis is allowed during CI Watch fix cycle when `ci_watch_active: true` and `roz_qa: CI_VERIFIED`
- Ellis is still blocked during active build phase without normal Roz QA PASS
- Hook correctly parses the new PIPELINE_STATUS fields
- No regression on existing Gate 1 behavior (Ellis blocked without Roz QA in build phase)
- Dual-tree sync

**Estimated complexity:** Medium (2 files, modifying existing conditional logic)

### Step 7: Documentation Updates

Update pipeline documentation to cover CI Watch setup, configuration, and behavior.

**Files to create/modify:**
- `source/rules/pipeline-orchestration.md` -- add CI Watch to Hard Pauses list
- `.claude/rules/pipeline-orchestration.md` -- same (installed copy)
- `source/references/pipeline-operations.md` -- add CI Watch to feedback loops table
- `.claude/references/pipeline-operations.md` -- same (installed copy)

**Changes:**
1. In `pipeline-orchestration.md` Hard Pauses section: add "CI Watch fix ready -- user must approve before Ellis pushes fix"
2. In `pipeline-operations.md` feedback loops table: add "CI failure (watched) | Roz (CI investigate) -> Colby (fix) -> Roz (verify) -> hard pause -> Ellis (push)"
3. In `pipeline-orchestration.md` phase sizing: note that CI Watch is orthogonal to sizing -- it runs post-pipeline on any size

**Acceptance criteria:**
- Hard Pauses list in `pipeline-orchestration.md` includes CI Watch pause point
- Feedback loops table in `pipeline-operations.md` includes CI Watch flow
- Dual-tree sync (4 files: 2 for pipeline-orchestration, 2 for pipeline-operations)
- No changes to existing rules behavior

**Estimated complexity:** Low (4 files, additive text changes)

---

## Comprehensive Test Specification

### Step 1 Tests: Config Schema Extension

| ID | Category | Description |
|----|----------|-------------|
| T-0013-001 | Happy | Source template `pipeline-config.json` contains `ci_watch_enabled: false` and `ci_watch_max_retries: 3` as default values |
| T-0013-002 | Happy | Installed `.claude/pipeline-config.json` contains `ci_watch_enabled` and `ci_watch_max_retries` fields |
| T-0013-003 | Boundary | `ci_watch_max_retries` accepts integer values 1-10 |
| T-0013-004 | Failure | Missing `ci_watch_enabled` field does not break existing config consumers (backward compatible) |
| T-0013-005 | Regression | All existing config fields (`branching_strategy`, `platform`, `sentinel_enabled`, `agent_teams_enabled`) are unchanged |

### Step 1 Telemetry

Telemetry: Config file parse success at pipeline boot. Trigger: Eva reads `pipeline-config.json`. Absence means: config file is missing or malformed.

### Step 2 Tests: Setup Step 6c

| ID | Category | Description |
|----|----------|-------------|
| T-0013-006 | Happy | Step 6c appears in SKILL.md after Step 6b, offering CI Watch opt-in |
| T-0013-007 | Happy | User accepts: `ci_watch_enabled` set to `true`, `ci_watch_max_retries` set to user-specified value |
| T-0013-008 | Happy | User declines: no config mutation, summary shows "CI Watch: not enabled" |
| T-0013-009 | Failure | Platform CLI not configured (`platform_cli: ""`): setup blocks with message "CI Watch requires `gh` or `glab`" |
| T-0013-010 | Failure | Platform CLI configured but not authenticated: setup blocks with auth message |
| T-0013-011 | Boundary | User specifies max retries = 1 (minimum): accepted |
| T-0013-012 | Boundary | User specifies max retries = 0: rejected with message "Must be at least 1" |
| T-0013-013 | Regression | Steps 6a (Sentinel) and 6b (Agent Teams) behavior unchanged |
| T-0013-014 | Happy | Idempotent: re-running with `ci_watch_enabled: true` already set skips mutation |
| T-0013-015 | Happy | Setup summary includes "CI Watch: enabled (max N retries)" line |

### Step 2 Telemetry

Telemetry: Setup summary includes CI Watch status line. Trigger: Step 6c completes. Absence means: Step 6c was skipped or crashed before summary.

### Step 3 Tests: Eva CI Watch Protocol

| ID | Category | Description |
|----|----------|-------------|
| T-0013-016 | Happy | CI Watch activates when `ci_watch_enabled: true` AND Ellis pushes to remote |
| T-0013-017 | Happy | CI passes: Eva notifies user with branch name and run link |
| T-0013-018 | Happy | CI fails: failure logs pulled, truncated to 200 lines, Roz investigates autonomously |
| T-0013-019 | Happy | Roz diagnosis passed to Colby, Colby fixes, Roz verifies fix -- all autonomous |
| T-0013-020 | Happy | HARD PAUSE after Roz verifies fix: user sees failure summary, changes, and Roz verdict |
| T-0013-021 | Happy | User approves: Ellis pushes fix, retry counter increments, new watch starts |
| T-0013-022 | Happy | User rejects: watch stops, user handles manually |
| T-0013-023 | Happy | Brain captures CI failure pattern after resolution (when brain available) |
| T-0013-024 | Failure | CI Watch does not activate when `ci_watch_enabled: false` |
| T-0013-025 | Failure | Roz fails during CI investigation: loop stops, report shows "Auto-fix failed at Roz phase" |
| T-0013-026 | Failure | Colby fails during CI fix: loop stops, report shows "Auto-fix failed at Colby phase" |
| T-0013-027 | Failure | No CI run found for pushed commit: watch stops with "No CI run found for commit [sha]" |
| T-0013-028 | Failure | Platform CLI returns errors 3 times consecutively: watch stops with connection-lost message |
| T-0013-029 | Boundary | Retry counter reaches `ci_watch_max_retries`: watch stops with cumulative failure report |
| T-0013-030 | Boundary | 30-minute timeout reached: user prompted "Keep waiting or abandon?" |
| T-0013-031 | Boundary | User says "keep waiting" after timeout: timer resets, polling continues |
| T-0013-032 | Boundary | User says "abandon" after timeout: watch stops, user checks manually |
| T-0013-033 | Concurrency | New Ellis push replaces active watch: old watch marked inactive, new watch starts |
| T-0013-034 | Concurrency | User is mid-conversation when CI result arrives: notification appended non-intrusively |
| T-0013-035 | Failure | `pipeline-config.json` has no `platform_cli`: watch does not activate (same as disabled) |
| T-0013-036 | Happy | PIPELINE_STATUS marker updated with `ci_watch_active`, `ci_watch_retry_count`, `ci_watch_commit_sha` |
| T-0013-037 | Failure | Brain unavailable: CI Watch works identically, brain capture skipped |
| T-0013-038 | Security | Failure logs do not contain secrets: log truncation uses `tail -200`, no filtering, but logs are ephemeral context (not written to disk) |
| T-0013-039 | Regression | Existing mandatory gates (Roz verifies Colby, Ellis commits, etc.) are unmodified |

### Step 3 Telemetry

Telemetry: "CI Watch: polling [platform] for commit [sha]" log line. Trigger: background poll starts. Absence means: watch failed to launch.
Telemetry: "CI Watch: [pass/fail] after [N] polls ([M]s elapsed)" log line. Trigger: CI run completes. Absence means: watch died or timed out without reporting.
Telemetry: `agent_capture` with `source_phase: 'ci-watch'` and `thought_type: 'pattern'`. Trigger: CI failure resolved. Absence means: brain capture not firing after CI fix.

### Step 4 Tests: Pipeline Operations Reference

| ID | Category | Description |
|----|----------|-------------|
| T-0013-040 | Happy | Platform command reference table lists correct `gh` commands for status check, log retrieval, and auth check |
| T-0013-041 | Happy | Platform command reference table lists correct `glab` commands for status check, log retrieval, and auth check |
| T-0013-042 | Happy | Polling loop pseudocode specifies 30-second interval and 60-iteration max |
| T-0013-043 | Boundary | Failure log truncation: single failed job gets 200-line tail |
| T-0013-044 | Boundary | Failure log truncation: multiple failed jobs concatenated with headers, total cap 400 lines |
| T-0013-045 | Regression | Existing operations sections (continuous QA, wave execution, batch mode) unchanged |
| T-0013-063 | Failure | Platform command reference documents fallback guidance when `glab ci trace` returns a non-zero exit code (e.g., job not found, auth expired) |

### Step 4 Telemetry

Structural step (reference documentation). No runtime telemetry.

### Step 5 Tests: Invocation Templates

| ID | Category | Description |
|----|----------|-------------|
| T-0013-046 | Happy | `roz-ci-investigation` template uses CONTEXT for failure logs (not READ for files) |
| T-0013-047 | Happy | `colby-ci-fix` template includes Roz diagnosis in CONTEXT |
| T-0013-048 | Happy | `roz-ci-verify` template includes test suite run in CONSTRAINTS |
| T-0013-049 | Failure | Templates do not reference non-existent files or tools |
| T-0013-050 | Regression | Existing templates (cal-adr, colby-build, roz-code-qa, etc.) unchanged |
| T-0013-064 | Wiring | Template IDs referenced in the CI Watch protocol (Step 3) -- `roz-ci-investigation`, `colby-ci-fix`, `roz-ci-verify` -- each have a matching `<template id="...">` definition in `invocation-templates.md` (Step 5). No ID mismatch between producer and consumer. |

### Step 5 Telemetry

Structural step (templates). No runtime telemetry.

### Step 6 Tests: Enforce-Sequencing Hook

| ID | Category | Description |
|----|----------|-------------|
| T-0013-051 | Happy | Ellis allowed when `ci_watch_active: true` AND `roz_qa: CI_VERIFIED` in PIPELINE_STATUS |
| T-0013-052 | Failure | Ellis blocked when `ci_watch_active: true` but `roz_qa` is empty (fix not verified) |
| T-0013-053 | Failure | Ellis blocked when `ci_watch_active: false` and `roz_qa` is not `PASS` (normal build phase) |
| T-0013-054 | Happy | Ellis allowed when `ci_watch_active: false` and `roz_qa: PASS` (normal build phase, unchanged) |
| T-0013-055 | Regression | Existing Gate 1 behavior (Ellis requires Roz QA PASS during active pipeline) unchanged |
| T-0013-056 | Regression | Existing Gate 2 behavior (Agatha blocked during build) unchanged |
| T-0013-057 | Boundary | PIPELINE_STATUS JSON with both `ci_watch_active` and `roz_qa` fields parses correctly |
| T-0013-058 | Failure | Malformed PIPELINE_STATUS JSON: hook exits 0 (allow, fail-open for parse errors -- existing behavior) |

### Step 6 Telemetry

Telemetry: Hook stderr output "BLOCKED: Cannot invoke Ellis" when Ellis is blocked during CI Watch without CI_VERIFIED. Trigger: Ellis invoked before Roz CI verification. Absence means: gate is not firing.

### Step 7 Tests: Documentation Updates

| ID | Category | Description |
|----|----------|-------------|
| T-0013-059 | Happy | Hard Pauses list in `pipeline-orchestration.md` includes CI Watch pause point |
| T-0013-060 | Happy | Feedback loops table in `pipeline-operations.md` includes CI Watch flow entry |
| T-0013-061 | Regression | Existing hard pause entries unchanged |
| T-0013-062 | Regression | Existing feedback loop entries unchanged |

### Step 7 Telemetry

Structural step (documentation). No runtime telemetry.

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `pipeline-config.json` fields (`ci_watch_enabled`, `ci_watch_max_retries`) | `boolean`, `integer` | Setup Step 6c (writes), Eva CI Watch protocol (reads) | Step 1 -> Steps 2, 3 |
| PIPELINE_STATUS marker fields (`ci_watch_active`, `ci_watch_retry_count`, `ci_watch_commit_sha`) | `boolean`, `integer`, `string` in JSON | Eva CI Watch protocol (writes), enforce-sequencing hook (reads) | Step 3 -> Step 6 |
| `roz_qa: "CI_VERIFIED"` status value | string enum extension | Eva CI Watch protocol (writes), enforce-sequencing hook (reads) | Step 3 -> Step 6 |
| Roz CI investigation output (diagnosis) | bug report format (symptom, root cause, recommended fix) | Eva passes to Colby CI fix invocation via CONTEXT | Step 5 (templates define format) |
| Colby CI fix output (files changed) | build report format (files changed, DoD) | Eva passes to Roz CI verify via CONTEXT | Step 5 (templates define format) |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `pipeline-config.json` `ci_watch_enabled` | boolean | Eva CI Watch protocol activation gate | 1 -> 3 |
| `pipeline-config.json` `ci_watch_max_retries` | integer | Eva CI Watch protocol retry limit | 1 -> 3 |
| Setup SKILL.md Step 6c | writes config fields | `pipeline-config.json` | 2 -> 1 |
| Eva CI Watch protocol | writes PIPELINE_STATUS fields | enforce-sequencing.sh Gate 1 | 3 -> 6 |
| Invocation template `roz-ci-investigation` | defines invocation format | Eva CI Watch protocol uses it | 5 -> 3 |
| Invocation template `colby-ci-fix` | defines invocation format | Eva CI Watch protocol uses it | 5 -> 3 |
| Invocation template `roz-ci-verify` | defines invocation format | Eva CI Watch protocol uses it | 5 -> 3 |
| Eva CI Watch hard pause | defines new pause point | `pipeline-orchestration.md` Hard Pauses list | 3 -> 7 |
| Eva CI Watch flow | defines new feedback loop | `pipeline-operations.md` feedback loops | 3 -> 7 |

No orphan producers. Every data contract has at least one consumer.

## Blast Radius

### Files Modified (13 files -- 6 source templates + 6 installed copies + 1 doc)

| File | Change Type | Scope |
|------|-------------|-------|
| `source/pipeline/pipeline-config.json` | Modified | 2 new fields added (Step 1) |
| `.claude/pipeline-config.json` | Modified | 2 new fields added (Step 1) |
| `skills/pipeline-setup/SKILL.md` | Modified | Step 6c section added (Step 2) |
| `source/rules/pipeline-orchestration.md` | Modified | CI Watch protocol section (Step 3) + Hard Pauses entry (Step 7) |
| `.claude/rules/pipeline-orchestration.md` | Modified | CI Watch protocol section (Step 3) + Hard Pauses entry (Step 7) |
| `source/references/pipeline-operations.md` | Modified | CI Watch operations section (Step 4) + feedback loops entry (Step 7) |
| `.claude/references/pipeline-operations.md` | Modified | CI Watch operations section (Step 4) + feedback loops entry (Step 7) |
| `source/references/invocation-templates.md` | Modified | 3 CI Watch templates added (Step 5) |
| `.claude/references/invocation-templates.md` | Modified | 3 CI Watch templates added (Step 5) |
| `source/hooks/enforce-sequencing.sh` | Modified | CI Watch exemption in Gate 1 (Step 6) |
| `.claude/hooks/enforce-sequencing.sh` | Modified | CI Watch exemption in Gate 1 (Step 6) |
| `docs/architecture/README.md` | Modified | ADR index entry added |

### Files NOT Modified (verified no impact)

- Agent persona files (ellis.md, roz.md, colby.md) -- no changes to agent behavior; CI Watch uses existing agents through Eva orchestration
- enforce-paths.sh -- no new write paths needed; CI Watch operates through existing Eva/Roz/Colby/Ellis write permissions
- enforce-git.sh -- no changes to git command enforcement
- warn-dor-dod.sh -- no changes to DoR/DoD warning
- pre-compact.sh -- no changes to compaction
- enforcement-config.json -- no new paths or patterns
- branch-lifecycle.md -- CI Watch is orthogonal to branching strategy
- plugin.json -- version bump handled by Ellis at commit time

### CI/CD Impact

None. CI Watch monitors CI from within the pipeline session. It does not modify CI configuration files, workflow definitions, or deployment scripts.

## Data Sensitivity

| Method/Field | Classification | Rationale |
|--------------|---------------|-----------|
| `ci_watch_enabled` | public-safe | Boolean feature flag, no secrets |
| `ci_watch_max_retries` | public-safe | Integer configuration, no secrets |
| CI failure logs (ephemeral) | auth-only | May contain environment variables, paths, or partial secrets from CI output. Never written to disk -- passed as agent context only. |
| `ci_watch_commit_sha` | public-safe | Git commit SHA, public information |
| Brain CI pattern captures | public-safe | Abstracted failure patterns, no raw logs |

## Notes for Colby

1. **Dual-tree sync is mandatory.** Every file in `source/` has a corresponding installed copy in `.claude/` (or `docs/`). The source version uses `{placeholders}` (e.g., `{pipeline_state_dir}`); the installed version uses literal values (e.g., `docs/pipeline`). Modify both in every step.

2. **Follow the Step 6a pattern exactly for Step 6c.** Read the Sentinel opt-in section in `skills/pipeline-setup/SKILL.md` and mirror its structure: offer, gate check, config mutation, summary update. The CI Watch gate is different (platform CLI required, not Semgrep MCP), but the flow is identical.

3. **The enforce-sequencing hook uses `parse_pipeline_status` to read JSON from a comment marker.** When adding CI Watch fields to PIPELINE_STATUS, ensure they are valid JSON that the existing `jq` parser handles. Test with: `echo '{"roz_qa": "CI_VERIFIED", "ci_watch_active": true, "ci_watch_retry_count": 1}' | jq -r '.ci_watch_active'`

4. **The `CI_VERIFIED` status is intentionally distinct from `PASS`.** Normal build-phase Roz QA writes `PASS`. CI Watch Roz verification writes `CI_VERIFIED`. The hook checks for both -- this prevents a CI Watch verification from accidentally satisfying the build-phase gate (different quality context).

5. **Background polling uses `run_in_background` Bash, not Agent `run_in_background`.** The polling loop is a Bash command, not a subagent. Use `timeout` parameter on the Bash tool for individual poll commands (60s each). The overall 30-minute timeout is tracked by iteration count (60 iterations x 30s = 30 min).

6. **Log truncation is `tail -200`, not `head -200`.** CI failures are diagnosed from the end of the log (where the error is), not the beginning (where the setup is).

7. **The source/rules/pipeline-orchestration.md file uses `{pipeline_state_dir}` as a placeholder** where the installed copy uses `docs/pipeline`. Check the existing pattern in the file to confirm which placeholders are used before writing.

8. **Brain integration pattern:** Follow the existing pattern in `pipeline-orchestration.md` brain-capture protocol. CI Watch captures use `source_phase: 'ci-watch'` to distinguish from `source_phase: 'build'` or `source_phase: 'retro'`. This makes brain queries filterable by phase.

---

## DoD: Verification

| # | Requirement | Step | Status | Evidence |
|---|-------------|------|--------|----------|
| R1 | `ci_watch_enabled` flag, default `false` | 1 | Designed | Config schema in Step 1 |
| R2 | `ci_watch_max_retries`, default `3` | 1 | Designed | Config schema in Step 1 |
| R3 | Setup Step 6c opt-in | 2 | Designed | SKILL.md modification in Step 2 |
| R4 | Background CI monitoring (gh + glab) | 3, 4 | Designed | Protocol in Step 3, commands in Step 4 |
| R5 | Pass notification | 3 | Designed | Protocol on-pass handler |
| R6 | Failure auto-fix loop | 3, 5 | Designed | Protocol on-fail handler + templates in Step 5 |
| R7 | Hard pause before fix push | 3 | Designed | Protocol HARD PAUSE gate |
| R8 | Retry limit enforcement | 3 | Designed | Protocol retry counter |
| R9 | 30-min timeout | 3 | Designed | Protocol timeout handler |
| R10 | Session-scoped (no orphans) | 3 | Designed | Background Bash dies with session |
| R11 | Both gh and glab | 4 | Designed | Platform command table |
| R12 | Brain capture | 3 | Designed | Protocol brain capture gate |
| R13 | Platform CLI gate | 2, 3 | Designed | Setup gate + activation gate |
| R14 | Log truncation 200 lines | 3, 4 | Designed | Truncation rules in Step 4 |
| R15 | One watch per session | 3 | Designed | Watch replacement rule |
| R16 | Agent failure stops loop | 3 | Designed | Protocol error handler |
| R17 | Dual-tree sync | 1-7 | Designed | All steps specify both source/ and .claude/ files |

**Architectural decisions not in the spec:**
- Polling loop (not `gh run watch`) for platform uniformity and resilience
- `CI_VERIFIED` as distinct status from `PASS` to prevent cross-context gate leakage
- 3 consecutive poll errors = connection-lost abort (spec did not specify polling error handling)
- Dead-watch detection via stale `ci_watch_active` flag (no separate heartbeat mechanism)
- Multiple-job failure log concatenation capped at 400 lines (spec said 200 per job)

**Rejected alternatives:**
- `gh run watch` long-running process: rejected for platform asymmetry and `run_in_background` timeout uncertainty
- Main-thread synchronous polling: rejected for violating non-blocking requirement, kept as degradation fallback

**Technical constraints discovered:**
- `run_in_background` Bash behavior with long-running processes is unverified; polling loop is the mitigation
- `glab ci status` does not have a direct equivalent to `gh run watch` -- polling is necessary for GitLab
- enforce-sequencing hook fail-open on JSON parse errors is existing behavior that applies to new CI Watch fields

---

Handoff: ADR saved to `docs/architecture/ADR-0013-ci-watch.md`. 7 steps, 64 total tests. Next: Roz reviews the test spec.
