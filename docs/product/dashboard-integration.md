## DoR: Requirements Extracted
**Source:** User conversation (2026-04-01), brain research (ecb6afe9, c0cb471f), retro lesson #003

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Two mutually exclusive dashboard options during /pipeline-setup | User decision |
| 2 | PlanVisualizer: static project-level dashboard with 7 tabs | Brain research ecb6afe9 |
| 3 | claude-code-kanban: real-time session dashboard with live agent tracking | Brain research c0cb471f |
| 4 | User picks one or neither — never both installed simultaneously | User decision |
| 5 | Setup prompt shows links to each project's GitHub repo | User decision |
| 6 | PlanVisualizer needs bridge script (brain telemetry → markdown) | Brain research ecb6afe9 |
| 7 | claude-code-kanban reads Claude Code native files — minimal wiring | Brain research c0cb471f |
| 8 | Neither tool's source code is modified — we feed them data | User constraint |
| 9 | quality-gate.sh auto-removed during /pipeline-setup (no prompt) | User decision, retro lesson #003 |
| 10 | Config flag in pipeline-config.json tracks which dashboard is installed | Pattern from Sentinel/Agent Teams |

**Retro risks:** Lesson #003 (quality-gate.sh race condition) — directly relevant to cleanup item.

---

# Feature Spec: Dashboard Integration + quality-gate.sh Cleanup
**Author:** Robert (CPO) | **Date:** 2026-04-01
**Status:** Draft — Pending Review

## The Problem

Pipeline users have no visual way to track what's happening during or across pipeline runs. Two open-source tools solve this from different angles — PlanVisualizer for project-level tracking (EPICs, stories, cost trends, traceability) and claude-code-kanban for real-time session observation (live task movement, agent lifecycle). Neither is wired into atelier-pipeline today.

Separately, users who installed atelier-pipeline before v3.4 may still have the deprecated `quality-gate.sh` stop hook, which causes infinite retry loops (retro lesson #003). There's no automated cleanup path.

## Who Is This For

1. **Project manager / lead** — wants to see pipeline runs as EPICs on a kanban board, track cost trends over time, see traceability between specs and implementation. Runs multiple pipelines per week. → PlanVisualizer.
2. **Solo developer** — wants to watch a long pipeline run in real-time, see tasks moving through states, know when the pipeline is waiting for input. Wants instant value with zero setup. → claude-code-kanban.
3. **Any existing user** — may have a stale quality-gate.sh causing pipeline breakage. → auto-cleanup.

## Business Value

- **Reduced support friction:** The quality-gate.sh cleanup eliminates a known bug that makes the pipeline unusable for affected users.
- **Differentiation:** No competing pipeline tool (Cursor or Claude Code) offers integrated dashboard options.
- **Retention:** Visual feedback keeps users engaged with the pipeline system instead of abandoning it after a few runs.

**KPIs:**

| KPI | Definition | Measurement | Timeframe | Acceptance |
|-----|-----------|-------------|-----------|------------|
| Dashboard adoption | % of /pipeline-setup runs that choose a dashboard | Count config flags set to non-"none" | 30 days post-release | >15% of installs choose a dashboard |
| quality-gate.sh cleanup rate | % of affected installs that get cleaned up | Count auto-removals during setup | 30 days post-release | 100% of users who re-run /pipeline-setup |

## User Stories

### US-1: Dashboard choice during setup
As a user running `/pipeline-setup`, I am offered a choice of dashboard integration after the existing optional features (Sentinel, Agent Teams, CI Watch, Brain). I see three options with descriptions and links, pick one (or none), and the pipeline installs my choice.

### US-2: PlanVisualizer bridge
As a user who chose PlanVisualizer, pipeline runs automatically generate a `PIPELINE_PLAN.md` file in PlanVisualizer's expected format. Each pipeline run becomes an EPIC, each agent phase becomes a story. When I run `node tools/generate-plan.js`, my pipeline runs appear on the kanban board with correct statuses.

### US-3: claude-code-kanban wiring
As a user who chose claude-code-kanban, the setup installs the dashboard hooks and I can run `npx claude-code-kanban --open` to see a real-time kanban of my pipeline's tasks. Eva's TaskCreate/TaskUpdate calls appear as cards moving through columns.

### US-4: quality-gate.sh auto-cleanup
As a user re-running `/pipeline-setup`, the deprecated quality-gate.sh hook is automatically detected and removed without prompting. The hook registration is removed from settings.json. I see a one-line notice: "Removed deprecated quality-gate.sh (see retro lesson #003)."

### US-5: Switch dashboard
As a user who previously chose PlanVisualizer, I re-run `/pipeline-setup` and can switch to claude-code-kanban (or none). The old dashboard artifacts are cleaned up and the new one is installed.

## User Flow

### Setup flow (new install or re-run)

```
/pipeline-setup
  ... existing steps (1-6d) ...

Step 6e: Dashboard Integration (optional)

  "Dashboard integration (optional):
    1. PlanVisualizer — project-level tracking with kanban, cost trends,
       traceability across pipeline runs
       https://github.com/ksyed0/PlanVisualizer
    2. claude-code-kanban — real-time session dashboard, watch agents
       work live (lightweight, instant setup)
       https://github.com/NikiforovAll/claude-code-kanban
    3. None

  Choose [1/2/3]:"

  → User picks 1: install PlanVisualizer + bridge script
  → User picks 2: install claude-code-kanban hooks
  → User picks 3: skip
```

### PlanVisualizer runtime flow

```
Pipeline runs → Eva captures telemetry as usual
  → After Ellis commit (post-Ellis step):
    → Bridge script reads brain T1/T2/T3 data (or pipeline-state.md fallback)
    → Generates PIPELINE_PLAN.md in PlanVisualizer format
    → Runs `node tools/generate-plan.js` to regenerate dashboard HTML
```

### claude-code-kanban runtime flow

```
Pipeline runs → Eva uses TaskCreate/TaskUpdate as usual
  → claude-code-kanban watches ~/.claude/tasks/ in real-time via filesystem watcher
  → Agent lifecycle tracked via installed SubagentStart/Stop hooks
  → User runs `npx claude-code-kanban --open` in a separate terminal
```

## Edge Cases and Error Handling

| Case | Handling |
|------|----------|
| User picks PlanVisualizer but Node.js < 18 | Warn: "PlanVisualizer requires Node.js 18+. Skipping." |
| User picks claude-code-kanban but npx not available | Warn: "claude-code-kanban requires npm/npx. Skipping." |
| User picks PlanVisualizer but brain is not configured | Bridge falls back to pipeline-state.md parsing (less data, still functional) |
| User re-runs setup with a different dashboard already installed | Detect current dashboard, clean up old artifacts, install new choice |
| Both dashboards somehow installed (manual tampering) | Detect on setup, force choice: "Both dashboards detected. Pick one or remove both." |
| PlanVisualizer install script fails | Log error, set config to "none", continue setup. Dashboard is never a blocker. |
| quality-gate.sh not found during cleanup | No-op. Silent. |
| quality-gate.sh found but settings.json entry already removed | Delete the file only. |
| settings.json has quality-gate.sh but file doesn't exist | Remove the settings.json entry only. |

## Acceptance Criteria

| # | Criterion | Measurable |
|---|-----------|------------|
| AC-1 | /pipeline-setup offers 3-option dashboard menu after existing optional features | Menu appears with descriptions and GitHub links |
| AC-2 | Choosing PlanVisualizer sets `dashboard_mode: "plan-visualizer"` in pipeline-config.json | Config flag verified |
| AC-3 | Choosing claude-code-kanban sets `dashboard_mode: "claude-code-kanban"` in pipeline-config.json | Config flag verified |
| AC-4 | Choosing None sets `dashboard_mode: "none"` in pipeline-config.json | Config flag verified |
| AC-5 | PlanVisualizer install clones repo, runs install script, copies bridge script | Files present in project |
| AC-6 | claude-code-kanban install runs `npx claude-code-kanban --install` and registers hooks | Hooks present in ~/.claude/hooks/ |
| AC-7 | Bridge script generates valid PIPELINE_PLAN.md from brain telemetry | Output parseable by PlanVisualizer's parse-release-plan.js |
| AC-8 | Bridge script falls back to pipeline-state.md when brain unavailable | Output generated without brain |
| AC-9 | quality-gate.sh auto-removed from hooks directory during /pipeline-setup | File deleted, no prompt |
| AC-10 | quality-gate.sh registration auto-removed from settings.json | Entry removed, no prompt |
| AC-11 | Re-running setup with different dashboard cleans up old choice | Old artifacts removed, new choice installed |
| AC-12 | Dashboard failure never blocks /pipeline-setup | Setup completes even if dashboard install fails |
| AC-13 | One-line notice printed when quality-gate.sh is cleaned up | "Removed deprecated quality-gate.sh (see retro lesson #003)" |

## Scope

### In scope
- Setup menu with 3 options (PlanVisualizer, claude-code-kanban, None)
- Config flag: `dashboard_mode` field in pipeline-config.json
- PlanVisualizer: clone, install script, bridge script (brain telemetry → PIPELINE_PLAN.md)
- claude-code-kanban: npx install, hook registration
- quality-gate.sh: auto-detect + auto-remove (file + settings.json entry)
- Switch between dashboards on re-run
- Bridge script fallback to pipeline-state.md when brain unavailable

### Out of scope
- Modifying PlanVisualizer or claude-code-kanban source code
- Custom dashboard themes or branding
- Dashboard hosting or deployment (users run locally)
- Automatic dashboard opening during pipeline runs
- Merging features from both dashboards into one

## Non-Functional Requirements

| NFR | Requirement |
|-----|-------------|
| Idempotency | Re-running /pipeline-setup with same dashboard choice is a no-op |
| Reversibility | Switching to "None" cleanly removes all dashboard artifacts |
| No blocker | Dashboard install failure never blocks pipeline setup or pipeline runs |
| No source modification | Neither dashboard's source code is modified by our integration |

## Dependencies

| Dependency | Required by | Risk |
|-----------|-------------|------|
| Node.js >= 18 | PlanVisualizer | Low — already required for brain |
| npm/npx | claude-code-kanban | Low — standard tooling |
| jq | claude-code-kanban hooks | Low — already required for enforcement hooks |
| Brain (optional) | PlanVisualizer bridge (full data) | None — fallback to pipeline-state.md |

## Risks and Open Questions

| # | Risk/Question | Mitigation |
|---|--------------|------------|
| 1 | PlanVisualizer install script may conflict with existing project npm scripts | Run install with --no-scripts-merge flag if available, or manual integration |
| 2 | claude-code-kanban hooks may conflict with our enforcement hooks in settings.json | Both use different hook events — verify no collision during implementation |
| 3 | PlanVisualizer may release breaking changes to its markdown format | Pin to a known-good version or tag during clone |
| 4 | Bridge script needs to handle empty brain (no telemetry data yet) | Generate minimal valid PIPELINE_PLAN.md with "No pipeline data yet" placeholder |

## Timeline Estimate

Medium pipeline. 2-3 ADR steps:
1. Setup integration (menu, config flag, install/uninstall for both dashboards, quality-gate cleanup)
2. PlanVisualizer bridge script (brain telemetry → PIPELINE_PLAN.md)
3. Eva post-pipeline wiring (bridge runs after Ellis, dashboard regenerated)

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Two mutually exclusive dashboard options | Done | Setup menu with 3 choices |
| 2 | PlanVisualizer static dashboard | Done | Config flag + install + bridge |
| 3 | claude-code-kanban real-time dashboard | Done | Config flag + npx install |
| 4 | Never both installed | Done | Mutual exclusion in setup logic |
| 5 | GitHub links in setup prompt | Done | Links in menu text |
| 6 | PlanVisualizer bridge script | Done | brain telemetry → PIPELINE_PLAN.md |
| 7 | claude-code-kanban minimal wiring | Done | Reads native Claude Code files |
| 8 | No source modification | Done | No fork, no patches |
| 9 | quality-gate.sh auto-removal | Done | File + settings.json cleaned |
| 10 | Config flag tracks dashboard choice | Done | `dashboard_mode` field in pipeline-config.json |

**Grep check:** TODO/FIXME/HACK/XXX in output files -> 0
**Template:** All sections filled — no TBD, no placeholders
