# Context Brief

Captures conversational decisions, user corrections, and rejected alternatives.
Reset at the start of each new feature pipeline.

## Scope
Offer two mutually exclusive kanban/dashboard integrations as optional dependencies during /pipeline-setup:
1. **PlanVisualizer** (github.com/ksyed0/PlanVisualizer) — static HTML dashboard with 7 tabs (hierarchy, kanban, traceability, charts, costs, bugs, lessons). Needs bridge script to translate brain telemetry into its markdown format.
2. **claude-code-kanban** (github.com/NikiforovAll/claude-code-kanban) — real-time dashboard watching Claude Code's native task/session files via SSE. Low integration effort — already reads our TaskCreate/TaskUpdate output.

Also: detect and clean up deprecated quality-gate.sh stop hook during /pipeline-setup.

## Key Constraints
- Both dashboards are optional — same pattern as Sentinel/Agent Teams (config flag + setup question)
- Mutually exclusive: user picks one or neither, never both (both install hooks into settings.json)
- We do NOT modify either project's source code — we feed them data in their expected formats
- PlanVisualizer bridge reads brain telemetry (T1/T2/T3) or pipeline-state.md as fallback
- claude-code-kanban reads Claude Code native files directly — minimal bridge work
- quality-gate.sh cleanup: detect during /pipeline-setup, warn user, offer removal

## User Decisions
- Two dashboard options, mutually exclusive (decided 2026-04-01)
- No modifications to either dashboard codebase — we "upgrade them with our needs" by feeding data
- quality-gate.sh was already removed from atelier (retro lesson #003) but users with older installs still have it — need cleanup in /pipeline-setup

## User Decisions (continued)
- Enforcement hooks should be bypassed during /pipeline-setup via ATELIER_SETUP_MODE=1 env var (decided 2026-04-01). Each hook checks for this var and exits 0 immediately. Prevents hooks from blocking legitimate setup writes.

## Rejected Alternatives
- Temporarily disabling hooks by renaming settings.json section — rejected: risky if setup crashes mid-way, hooks stay disabled
