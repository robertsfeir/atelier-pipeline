## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Opt-in feature, not on by default | User constraint |
| 2 | Offered during `/pipeline-setup` (Step 6c pattern) | User decision |
| 3 | Config flag in `pipeline-config.json` | User decision |
| 4 | Support both GitHub Actions (`gh`) and GitLab CI (`glab`) via polling (`gh run list` / `glab ci list`) | User decision |
| 5 | Non-blocking — CI watch runs in background agent/process | User constraint |
| 6 | 30-minute timeout — prompt user to continue or abandon | User constraint |
| 7 | Single hard pause before push only (not before fix) | User decision |
| 8 | Configurable max retries, default 3, set at install | User decision |
| 9 | Watch dies with session — no cross-session persistence | User decision |
| 10 | On failure: Poirot diagnose → Colby fix → Poirot verify → pause → Ellis push | Issue #16 |

**Retro risks:** Brain context shows prior project had 6+ CI failure cycles from local/CI divergence. CI watch addresses post-push failures but does not replace pre-push gates (`make ci-full` pattern). Both are needed.

---

# Feature Spec: CI Watch (Self-Healing CI)

**Author:** Robert (CPO) | **Date:** 2026-03-29
**Status:** Planned -- spec captured pre-implementation. Agent assignments below (Poirot for diagnosis, Colby for fix) reflect the current agent roster and may be revisited at design time.
**Issue:** #16

## The Problem

When Ellis pushes code, CI can fail for reasons not caught by local tests — environment differences, integration issues, flaky tests, platform-specific behavior. Today the user discovers the failure manually, reports it, and Eva routes through the debug flow. This creates a gap between push and awareness, and a manual restart of a well-defined sequence.

## Who Is This For

Developers using the atelier-pipeline who push code via Ellis and have CI configured on their remote (GitHub Actions or GitLab CI). Solo developers and small teams who want faster feedback loops without manually watching CI dashboards.

## Business Value

- **Reduced mean-time-to-fix** for CI failures — automated diagnosis starts immediately, no human lag
- **Fewer context switches** — user doesn't need to monitor CI, the pipeline handles it
- **Knowledge capture** — brain records CI failure patterns for future WARN injection

**KPIs:**
| KPI | Measurement | Timeframe | Acceptance |
|-----|------------|-----------|------------|
| CI failure auto-detection rate | Failures detected by watch / total CI failures | Per month | > 90% |
| Auto-fix success rate | Fixes that pass CI on retry / total auto-fix attempts | Per month | > 50% (first slice) |
| Time from push to fix-pushed | Timestamp delta: Ellis push → fix Ellis push | Per incident | < 15 min for single-file fixes |

## User Stories

1. **As a developer**, after Ellis pushes, I want the pipeline to automatically watch CI status so I don't have to check it manually.
2. **As a developer**, when CI fails, I want the pipeline to automatically diagnose and fix the issue so I can just approve the fix and move on.
3. **As a developer**, I want to be prompted if CI takes longer than 30 minutes so I can decide whether to keep waiting.
4. **As a developer**, I want to control how many auto-fix attempts the pipeline makes before stopping.

## User Flow

### Happy Path (CI passes)

```
Ellis pushes → Eva launches background CI watch
  → CI passes (within 30 min)
  → Eva notifies user: "CI passed on [branch]. [link to run]"
  → Done
```

### Failure Path (auto-fix)

```
Ellis pushes → Eva launches background CI watch
  → CI fails
  → Eva pulls failure logs
  → Poirot investigates failure logs (autonomous)
  → Colby fixes based on Poirot diagnosis (autonomous)
  → Poirot verifies fix (autonomous)
  → Eva notifies user: "CI failed. Auto-fix ready."
     Shows: failure summary, what changed, Poirot verdict
  → HARD PAUSE — user reviews
  → User approves → Ellis pushes fix → back to watch (retry count +1)
  → User rejects → Done, user handles manually
```

### Timeout Path

```
Ellis pushes → Eva launches background CI watch
  → 30 minutes elapse, CI still running
  → Eva prompts: "CI has been running for 30 minutes. Keep waiting or abandon?"
  → User: "keep waiting" → reset timer, continue
  → User: "abandon" → stop watching, notify user to check manually
```

### Retry Exhaustion Path

```
  → Auto-fix attempt N (where N = ci_watch_max_retries)
  → CI fails again
  → Eva stops: "CI failed after [N] auto-fix attempts. Manual intervention needed."
     Shows: cumulative failure log, all attempted fixes
  → Done
```

### Session Close Path

```
  → User closes session while CI watch is running
  → Watch process dies with session
  → No notification, no persistence
  → User checks CI manually on next session
```

## Edge Cases and Error Handling

| Edge Case | Handling |
|-----------|----------|
| No platform CLI configured | Block enablement: "CI Watch requires `gh` or `glab`. Configure a platform in pipeline-config.json first." |
| Platform CLI not authenticated | Block at setup time (Step 6c): auth check runs during `/pipeline-setup` before CI Watch is enabled. User directed to run `gh auth login` / `glab auth login` and re-run setup. |
| No CI run found for pushed commit | Polling loop detects no runs for the commit SHA. Watch stops with notification: "No CI run found for commit [sha]. Does this repo have CI configured?" Implemented via the polling pseudocode's "no run found" branch. |
| CI passes on retry but a different check fails | Each retry watches the full CI run, not individual checks. A partial pass is still a fail. |
| Multiple pushes in quick succession | Each Ellis push replaces the active watch. Only one watch per session. |
| Poirot or Colby fails during auto-fix | Stop the loop. Report: "Auto-fix failed at [agent] phase. Manual intervention needed." Show the agent's error output. |
| User is mid-conversation when CI result arrives | Notification is non-intrusive -- `run_in_background` notifications naturally append to the conversation when the background task completes, without interrupting current work. |
| Branch protection blocks push | Ellis reports the block. Eva sets `ci_watch_active: false` in PIPELINE_STATUS, stops the fix cycle, and notifies the user: "Push blocked by branch protection. Handle CI failure manually." |
| Flaky test (passes on re-run without code change) | First retry: Poirot may diagnose as flaky and Colby's "fix" is a re-push. This is acceptable — the retry mechanism handles it naturally. |

## Acceptance Criteria

| # | Criterion | Measurable |
|---|-----------|------------|
| 1 | `ci_watch_enabled` flag in `pipeline-config.json`, default `false` | Config file inspection |
| 2 | `ci_watch_max_retries` in `pipeline-config.json`, default `3`, set during setup | Config file inspection |
| 3 | Offered as opt-in during `/pipeline-setup` Step 6c | Setup flow observation |
| 4 | After Ellis pushes, background process monitors CI via polling (`gh run list` / `glab ci list`) every 30 seconds | Process observation |
| 5 | CI pass → user notified with run link | Notification observation |
| 6 | CI fail → failure logs pulled, Poirot → Colby → Poirot runs autonomously | Agent invocation observation |
| 7 | Hard pause before Ellis pushes fix — user must approve | Conversation observation |
| 8 | Retry loop respects `ci_watch_max_retries` | Counter verification |
| 9 | 30-minute timeout prompts user | Timer verification |
| 10 | Watch dies with session — no orphan processes | Process observation after session close |
| 11 | Works with both `gh` (GitHub) and `glab` (GitLab) | Platform test |
| 12 | Brain captures CI failure pattern after resolution | Brain query verification |

## Scope

### In Scope
- CI watch trigger after Ellis push
- Background non-blocking monitoring
- Auto-fix loop (Poirot → Colby → Poirot → pause → Ellis)
- Configurable retry limit
- 30-minute timeout with user prompt
- GitHub Actions and GitLab CI support
- Brain capture of CI failure patterns
- Setup integration (Step 6c opt-in)

### Out of Scope (won't do)
- Cross-session persistence (watch dies with session)
- Watching CI for pushes not made by Ellis
- Custom CI systems (Jenkins, CircleCI, etc.) — platform-cli only
- Automatic branch protection bypass
- Parallel CI watches (one per session)
- Dashboard or web UI for CI status
- Pre-push CI gates (existing `make ci-full` pattern, separate concern)

## Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Watch overhead | Near zero — single polling process, no CPU burn |
| Notification latency | < 30s after CI completes |
| Failure log size | Truncate to last 200 lines per failed job to fit agent context |
| No orphan processes | Watch must terminate when parent session exits |

## Dependencies

| Dependency | Status | Risk |
|------------|--------|------|
| `gh` CLI (GitHub) | External, user-installed | Low — widely available |
| `glab` CLI (GitLab) | External, user-installed | Low — widely available |
| Platform configured in `pipeline-config.json` | Internal | Gated — CI Watch requires platform to be set |
| Background agent/process support in Claude Code | Platform feature | Medium — verify `run_in_background` behavior with long-running watches |
| Ellis subagent (push trigger) | Internal, exists | None |
| Poirot subagent (diagnosis) | Internal, exists | None |
| Colby subagent (fix) | Internal, exists | None |

## Risks and Open Questions

| Risk | Mitigation |
|------|------------|
| `run_in_background` behavior for long polling is unproven | Polling loop uses short individual commands (30s intervals, 60s timeout each) rather than a long-running blocking process. If `run_in_background` has limits, the polling approach degrades gracefully. Dead-watch detection (35+ minutes without reporting) catches silent failures. |
| Background agent lifetime tied to session -- user may close before fix completes | Documented limitation. Fix-in-progress is lost. User can re-trigger. |
| Failure log truncation may lose critical context | 200-line tail is a starting default. Poirot can request more if diagnosis is inconclusive. |
| Auto-fix may introduce regressions not caught by CI | Poirot verifies before pause. User reviews at hard pause. Two safety layers. |
| 3 consecutive polling errors may indicate transient network issue | Error streak counter resets on any successful poll. Only 3 consecutive errors trigger connection-lost abort -- isolated failures are tolerated. |

## Timeline Estimate

Single slice — no phasing needed. All acceptance criteria ship together.

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Opt-in config flag | Pending | |
| 2 | Configurable retries at install | Pending | |
| 3 | Setup Step 6c integration | Pending | |
| 4 | Background CI monitoring (gh + glab) | Pending | |
| 5 | Pass notification | Pending | |
| 6 | Failure auto-fix loop | Pending | |
| 7 | Hard pause before fix push | Pending | |
| 8 | Retry limit enforcement | Pending | |
| 9 | 30-min timeout with user prompt | Pending | |
| 10 | Session-scoped (no orphans) | Pending | |
| 11 | Brain capture of CI patterns | Pending | |
| 12 | Docs updated | Done | User guide + technical reference CI Watch sections added; spec reconciled |
