# Atelier Pipeline -- User Guide

A structured, multi-agent development workflow for Claude Code and Cursor. Twelve specialized agents handle product specs, UX design, architecture, implementation, QA, security audit, dependency management, documentation, and commits -- so you focus on decisions, not process.

---

## Table of Contents

- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Slash Commands](#slash-commands)
- [Working with Agents](#working-with-agents)
- [Running a Full Pipeline](#running-a-full-pipeline)
- [Debugging with /debug](#debugging-with-debug)
- [Phase Sizing](#phase-sizing)
- [Token Budget Estimate Gate](#token-budget-estimate-gate)
- [Pipeline Stop Reasons](#pipeline-stop-reasons)
- [The Atelier Brain](#the-atelier-brain)
- [Team Collaboration](#team-collaboration)
- [State Recovery](#state-recovery)
- [Customization](#customization)
- [Branching Strategy](#branching-strategy)
- [Sentinel Security Agent](#sentinel-security-agent)
- [Agent Teams](#agent-teams)
- [CI Watch](#ci-watch)
- [Deps Agent](#deps-agent)
- [Darwin Agent](#darwin-agent)
- [Model Selection](#model-selection)
- [Agent Telemetry](#agent-telemetry)
- [Gauntlet Audit](#gauntlet-audit)
- [Dashboard](#dashboard)
- [Telemetry Hydration](#telemetry-hydration)
- [Agent Discovery](#agent-discovery)
- [Context Management](#context-management)
- [Mechanical Enforcement](#mechanical-enforcement)
  - [Enforcement Audit Trail](#enforcement-audit-trail)
- [Uninstalling](#uninstalling)
- [Updating the Plugin](#updating-the-plugin)
- [Troubleshooting](#troubleshooting)
- [Reference](#reference)

---

## Platform Differences

Atelier Pipeline runs on both Claude Code and Cursor with near-complete feature parity. This table summarizes where the two platforms differ:

| Feature | Claude Code | Cursor |
|---------|------------|--------|
| Agent Teams (parallel wave execution) | Yes (experimental) | Not available |
| Distributed routing (Agent spawning by Sarah/Colby) | Yes | Not available |
| Telemetry hydration | Automatic (SessionStart) + manual | Automatic (SessionStart) + manual |
| Worktrees | Yes | Not available |
| Hook enforcement | Full (20 hooks) | Full (20 hooks) |
| Brain integration | Full | Full |
| All 14 agents | Full | Full |
| Installed file directory | `.claude/` | `.cursor/` |
| Rules file extension | `.md` | `.mdc` (with frontmatter) |
| Project env variable | `$CLAUDE_PROJECT_DIR` | `$CURSOR_PROJECT_DIR` |
| Project instructions file | `CLAUDE.md` | `AGENTS.md` |
| Settings file | `.claude/settings.json` | `.cursor/settings.json` |

When Agent Teams is unavailable on Cursor, the pipeline runs sequentially -- same output, same quality gates, just without parallel wave execution. When distributed routing is unavailable, Eva routes all agent invocations centrally.

---

## Quick Start

### 1. Install the plugin

**Claude Code:**

```
/plugin marketplace add robertsfeir/atelier-pipeline
/plugin install atelier-pipeline@atelier-pipeline
```

Restart Claude Code after install.

**Cursor:**

Install from the Cursor Marketplace -- search "atelier-pipeline".

Or manually:

```bash
git clone https://github.com/robertsfeir/atelier-pipeline.git /tmp/atelier-pipeline
```

Then in Cursor:

```
Read /tmp/atelier-pipeline/.cursor-plugin/skills/pipeline-setup/SKILL.md and follow its instructions
```

### 2. Set up the pipeline in your project

Open your IDE (Claude Code or Cursor) in your project directory and run:

```
/pipeline-setup
```

The setup asks about your project one question at a time: tech stack, test commands, source structure, coverage thresholds, and branching strategy. It then installs ~45 files into your project -- into `.claude/` (Claude Code) or `.cursor/` (Cursor) -- including agent personas, commands, references, enforcement hooks, path-scoped rules, branch lifecycle rules, and state tracking. At the end, it offers optional features: Sentinel security agent, Agent Teams parallel execution (Claude Code only), CI Watch, Deps agent, and Atelier Brain persistent memory.

### 3. Build something

Describe a feature idea in plain language:

```
I want to add a user settings page where users can update their display name and email preferences.
```

Eva, the orchestrator, sizes the work and routes it to the right agent. You approve decisions along the way. The pipeline handles the rest -- spec, design, architecture, tests, implementation, QA, docs, and commit.

---

## How It Works

The pipeline gives you a team of specialized agents, each with a clear job. You interact with them through normal conversation. Eva coordinates everything.

### The agents

| Agent | Role | What they do for you |
|-------|------|---------------------|
| **Eva** | Orchestrator | Routes work, tracks state, enforces quality gates. Your main point of contact during pipeline runs. |
| **Robert** | Chief Product Officer | Turns your idea into a structured spec with user stories, acceptance criteria, and scope boundaries. |
| **Sable** | UI/UX Designer | Designs user flows, screen layouts, states, and accessibility requirements from Robert's spec. |
| **Sarah** | Software Architect | Produces an Architecture Decision Record (ADR) with implementation steps and a test spec. |
| **Colby** | Software Engineer | Builds mockups and production code. Works one ADR step at a time. |

| **Poirot** | Blind Investigator | Reviews code diffs without seeing the spec -- catches issues that spec-aware reviewers miss. |
| **Agatha** | Documentation Specialist | Plans and writes documentation in parallel with the build. |
| **Ellis** | Commit Manager | Creates atomic commits with Conventional Commits format and updates the changelog. |
| **Distillator** | Compression Engine | Compresses large structured documents (spec, UX doc, ADR) at phase boundaries when they exceed ~5K tokens. |
| **Sentinel** | Security Auditor (opt-in) | Scans changed code for vulnerabilities using Semgrep MCP static analysis. Runs at the review juncture. |
| **Deps** | Dependency Manager (opt-in) | Scans dependency manifests, checks CVEs, predicts upgrade breakage, and produces risk-grouped reports. |
| **Darwin** | Pipeline Evolution Engine (opt-in) | Queries telemetry from the brain, evaluates agent fitness, and proposes structural improvements to the pipeline itself. Requires the brain. |

### The flow

A full pipeline (for a large feature) runs through these phases:

```
Your idea
  -> Robert writes a spec
  -> Sable designs the UX + Agatha plans docs      (parallel)
  -> Colby builds a mockup
  -> Sable verifies the mockup
  -> You review the mockup in-browser (UAT)
  -> Sarah architects the solution (ADR + test spec)
   reviews the test spec
  -> [Per wave]
       Poirot writes test assertions for all units in the wave
       Colby builds each unit (lint + typecheck only per unit)
       Poirot verification + Poirot blind review run for the whole wave  (parallel)
       Ellis commits the wave
   final sweep + Poirot + Robert + Sable + Sentinel  (parallel review juncture)
  -> Agatha writes/updates docs
  -> Robert verifies docs match the spec
  -> Ellis creates final delivery commit
```

Not every feature goes through every phase. See [Phase Sizing](#phase-sizing) for how Eva adjusts. When an ADR step produces non-code artifacts only (schema DDL, configuration, migration scripts, agent instruction files), the Poirot test spec and test authoring phases are skipped for that step -- Colby implements, Poirot verifies against ADR requirements, and Agatha follows sequentially.

---

## Slash Commands

These are installed into your project by `/pipeline-setup`. Use them to invoke a specific agent directly, bypassing auto-routing.

| Command | Agent | Use when you want to... |
|---------|-------|------------------------|
| `/pipeline` | Eva | Run the full pipeline from wherever you are |
| `/pm` | Robert | Explore a feature idea and produce a spec |
| `/ux` | Sable | Design the user experience for a spec |
| `/architect` | Sarah | Discuss architecture or produce an ADR |
| `/debug` | Poirot, Colby | Investigate and fix a bug |
| `/docs` | Agatha | Plan what documentation a feature needs |
| `/devops` | Eva | Handle infrastructure, CI/CD, deployment |
| `/deps` | Deps | Scan dependencies for outdated packages, CVEs, and upgrade risk |
| `/darwin` | Darwin | Analyze telemetry, evaluate agent fitness, and propose pipeline improvements |
| `/telemetry-hydrate` | Eva | Manually capture agent telemetry from session files into the brain |
| `/dashboard` | Eva | Open the Atelier Dashboard in the browser (starts brain HTTP server if needed) |

### When you don't need slash commands

Eva auto-routes based on what you say. Most of the time, just describe what you need:

| You say... | Eva routes to... |
|------------|-----------------|
| "What if we added a notification system?" | Robert (product spec) |
| "How should we structure the data layer?" | Sarah (architecture) |
| "Build the settings page" | Colby (implementation) |
| "This endpoint returns 500 when the user has no profile" | Poirot (bug investigation) |
| "Ship it" | Ellis (commit) |

Slash commands are useful when Eva's auto-routing picks the wrong agent, or when you want to jump directly to a specific phase.

---

## Working with Agents

### Conversational agents (skills)

Robert, Sable, Sarah (clarification mode), and Agatha (planning mode) run in the main IDE thread on both Claude Code and Cursor. They have a conversation with you.

**Example: Working with Robert**

```
You: I want to add email notifications when a teammate comments on your work.

Robert: Who specifically gets notified -- the work owner, all collaborators,
or configurable per-user?

You: Just the work owner for v1.

Robert: Makes sense. What notification channels -- email only, or in-app as
well? In-app is lower effort and gives us a foundation for email later.

You: Email only. We already have SendGrid set up.

Robert: Good. One more -- what about muting? Can the owner turn off
notifications for a specific project, or is it all-or-nothing?

You: All-or-nothing toggle in settings for v1.

Robert: Here's what I heard: [summary]. Correct me now, then I'll write the spec.
```

Robert asks questions one at a time. He pushes back on scope creep. He produces a spec with acceptance criteria, edge cases, and API contracts.

The same pattern applies to Sable (UX flows and states), Sarah (architecture trade-offs), and Agatha (doc impact assessment).

### Execution agents (subagents)

Colby, Poirot, Ellis, and Distillator run in their own context windows. Eva invokes them with focused prompts and reads their results. You see Eva's summaries and status updates.

**Example: What you see during the build phase**

```
Eva: Wave 1 (Steps 1-2 are independent). Poirot writing tests for both units.

Eva: Colby built Step 1 (data model + migration). Lint PASS, typecheck PASS.

Eva: Colby built Step 2 (API endpoints). Lint PASS, typecheck PASS.

Eva: Invoking Poirot verification and Poirot blind review for Wave 1.

Eva: Poirot: Wave 1 PASS, 0 blockers, 1 must-fix, 2 suggestions. Report: last-qa-report.md
Eva: Poirot: Wave 1 2 findings (0 BLOCKER, 1 MUST-FIX, 1 NIT)

Eva: Convergent MUST-FIX: the PATCH endpoint does not validate email format.
Queuing fix for Colby.

Eva: Colby fixed the validation. Poirot scoped re-run passed. Ellis committing Wave 1.
```

### Interacting during a pipeline

You can intervene at any time during a pipeline run:

| You say | What happens |
|---------|-------------|
| "stop" or "hold" | Eva pauses at the current phase |
| "skip to [agent]" | Eva jumps to the named agent's phase |
| "back to [agent]" | Eva returns to a previous phase |
| "full ceremony" | Eva pauses at every transition for your approval |
| "check with [agent]" | Eva consults a specific agent mid-phase |
| Any feedback or correction | Eva records it in the context brief and routes it to the right agent |

### Hard pauses

Eva stops and asks you before:

- Ellis pushes to the remote repository
- A Poirot BLOCKER verdict (pipeline halts until resolved)
- Drift between the spec and the implementation (you decide: update spec or fix code)
- An ambiguous finding from Robert or Sable
- A scope-changing discovery from Sarah
- Applying a bug fix (you approve Poirot's diagnosis first)
- A Stuck Pipeline Analysis (the same task has failed 3 consecutive times -- you decide whether to intervene, re-scope, or abandon)
- Invoking the first agent on a Large pipeline (token budget estimate gate -- always fires)
- Invoking the first agent on a Medium pipeline when your configured threshold is exceeded

---

## Running a Full Pipeline

### Starting from an idea

```
You: I want to add dark mode support to the dashboard.

Eva: I'll size this as Medium -- it touches the theme system, component
library, and user preferences (3 ADR steps estimated). Starting with Robert
for the spec.

Robert: Let's scope this. When you say dark mode, do you mean a system-
preference-aware toggle, a manual toggle in settings, or both?
```

The pipeline proceeds through spec, UX, architecture, build, QA, docs, and commit. Eva announces each transition.

### Starting from existing artifacts

If you already have a spec, UX doc, or ADR, Eva detects them and skips completed phases:

```
You: The spec is at docs/product/dark-mode.md and the UX doc is at
docs/ux/dark-mode-ux.md. Let's build it.

Eva: Found existing spec and UX doc. Skipping Robert and Sable.
Starting with Sarah for architecture.
```

### User acceptance testing (UAT)

For features with a UI, Colby builds a mockup with real components and mock data. Sable verifies the mockup matches her design. Then Eva presents it to you:

```
Eva: Mockup ready. Starting the dev server...

Eva: Navigate to http://localhost:5173/mock/dark-mode to review.
Here's what you should see: [description of each state].

You: The toggle works, but the sidebar doesn't pick up the dark theme.

Eva: Noted. Routing back to Colby to fix the sidebar theming.
```

After you approve the mockup, Sarah architects only the backend and data wiring. The validated UI stays as-is.

### Continuous QA

Sarah's ADR steps are grouped into waves based on file independence. QA ceremonies happen at the wave boundary, not per unit:

1. **Poirot writes test assertions for all units in the wave** before Colby builds anything
2. **Colby builds each unit** and runs only lint and typecheck as a fast sanity check -- not the full test suite
3. **After all units in the wave are built**, Eva invokes Poirot (full QA) and Poirot (blind diff review) in parallel for the entire wave
4. Issues are caught and fixed at wave boundaries, before the next wave begins
5. **Ellis commits the wave** after Poirot pass

This prevents regressions from spreading across waves while avoiding per-unit full-suite overhead.

After all waves complete, Poirot does a final sweep, Poirot reviews the full pipeline diff, Robert verifies the implementation matches the spec, and on large features, Sable verifies it matches her UX doc. When Sentinel is enabled, it runs here at the review juncture -- not during the build phase.

### Commit

Ellis commits each wave on the feature branch using wave commit mode. At the final review juncture, Ellis creates a merge commit or squash to main. Ellis uses Conventional Commits format with a human-readable narrative body.

Eva asks for your approval before pushing to the remote.

---

## Debugging with /debug

Report a bug, and the debug flow handles investigation, fix, and verification:

```
You: /debug The user profile page crashes when the user has no avatar set.
```

### Phase 1: Poirot investigates

Poirot reproduces the issue, traces the execution path, and identifies the root cause with file paths and line numbers.

### Phase 2: Eva challenges the diagnosis

Eva presents three perspectives before you approve a fix:

```
Eva:
  Poirot's diagnosis: NullPointerError in ProfileAvatar.tsx:42 -- component
  assumes `user.avatar` is always defined. Recommended fix: add null check
  with fallback to default avatar.

  Technical counter-hypothesis: Could the API be returning a malformed
  user object when avatar is null? The frontend may be correct to assume
  a non-null value if the API contract specifies one.

  Product consequence check: If we add a fallback avatar, users who
  intentionally removed their avatar will see a default instead of nothing.
  Is that the desired behavior?

  Your call:
  - "fix it" -- Colby applies Poirot's fix
  - "investigate the alternative" -- Poirot checks the API contract
  - "this is a design problem, stop" -- route to Robert for spec review
```

### Phase 3: Colby fixes

After your approval, Colby applies the fix and writes a regression test that would have caught the bug.

### Phase 4: Poirot verifies

Poirot confirms the fix works, the regression test covers the bug, and nothing else broke.

### Phase 5: Ellis commits

A clean bug-fix commit with the code change and regression test.

---

## Phase Sizing

Eva assesses every request and adjusts how much ceremony to apply.

| Size | When Eva uses it | What runs | What gets skipped |
|------|-----------------|-----------|-------------------|
| **Micro** | Rename, typo, import fix, version bump -- mechanical only, no behavioral change, 2 files or fewer | Colby -> test suite -> Ellis | Everything else. If tests fail, Eva re-sizes to Small automatically. |
| **Small** | Bug fix, single file change, fewer than 3 files, or you say "quick fix" | Colby -> Ellis | Robert, Sable, Sarah. Agatha runs only if Poirot flags doc impact. |
| **Medium** | 2-4 implementation steps, typical feature | Robert -> Sarah -> Colby/Poirot (interleaved) -> Agatha -> Ellis | Sable mockup + UX review (unless the feature has significant UI) |
| **Large** | 5+ implementation steps, new system, multiple concerns | Full pipeline including Sable mockup, UAT, and final UX review | Nothing |

### Overriding the sizing

| You say | Effect |
|---------|--------|
| "fast track this" | Forces Small sizing |
| "full pipeline" or "full ceremony" | Forces Large sizing with pauses at every transition |
| "quick fix" | Forces Small sizing |

The minimum pipeline is always Colby -> Ellis. Poirot and Ellis are never skipped.

### Non-code ADR steps

Some ADR steps produce no testable application code -- schema DDL, agent instruction files (markdown), configuration files, or migration scripts. For these steps, Eva skips the Poirot test spec review and test authoring phases because there is no application code to test. Instead:

1. Colby implements the non-code step
2. Poirot reviews Colby's output in verification mode -- checking that the ADR's acceptance criteria are met rather than running code QA checks
3. Agatha runs after Poirot passes (sequentially, not in parallel with Colby, because there is no Poirot test spec approval to gate the parallel launch)

If an ADR mixes code and non-code steps, Eva splits them: code steps follow the normal  flow, non-code steps follow this flow. Both must pass before Ellis commits.

---

## Token Budget Estimate Gate

Before starting a Large pipeline, Eva shows you a cost estimate so you can decide whether to proceed. This is an order-of-magnitude estimate -- not billing -- based on the agent roster, model assignments, and expected number of invocations for your chosen sizing tier.

### What you see

After you confirm the sizing and before Eva invokes the first agent, you will see something like:

```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Large | Steps: TBD -- estimated after Sarah | Agents: 15-30+
  Estimated cost: $8.10 -- $17.35 (based on sizing heuristics and model assignments)

Proceed? (yes / cancel / downsize to Medium)
```

If the estimate exceeds your configured threshold, the output includes a threshold comparison line:

```
  Threshold: $10.00 -- estimate EXCEEDS threshold
```

Eva waits for your response before invoking any agent. Saying "cancel" writes a `budget_threshold_reached` stop reason to `pipeline-state.md` and closes the pipeline cleanly.

### When the estimate appears

| Sizing | No threshold set | Threshold configured |
|--------|-----------------|---------------------|
| Micro | No estimate | No estimate |
| Small | No estimate | No estimate |
| Medium | No estimate | Estimate shown if threshold exceeded |
| Large | Estimate always shown | Estimate always shown |

### Configuring a threshold

Add `token_budget_warning_threshold` to your project's `.claude/pipeline-config.json` (Claude Code) or `.cursor/pipeline-config.json` (Cursor):

```json
{
  "token_budget_warning_threshold": 10.0
}
```

- **Type:** number (USD) or null
- **Default:** null (Large-only estimate shown, no threshold gate on Medium)
- **Example:** `10.0` triggers the gate on Medium pipelines when the estimate exceeds $10.00

Set it to null (or remove the key) to return to the default Large-only behavior.

### What the estimate is based on

The estimate uses your pipeline sizing, the number of agent invocations typical for that tier, and per-model average token costs from the pricing table in `telemetry-metrics.md`. It applies a 0.7x optimistic and 1.5x pessimistic multiplier to produce a range. When Sarah has already produced an ADR with a step count, Colby and Poirot invocation counts are derived from the actual number of steps.

The estimate is a heuristic. It will be wrong on features with deep rework cycles or unusually large context windows. Treat the range as guidance, not a budget ceiling.

---

## Pipeline Stop Reasons

Every pipeline ends with a structured reason written to `docs/pipeline/pipeline-state.md`. This tells Eva (and you) exactly how the pipeline ended, which matters for session recovery and trend analysis.

### Where you see stop reasons

**In the Pipeline Complete report** -- at the end of every pipeline, Eva includes a Stop Reason line in the summary.

**In `docs/pipeline/pipeline-state.md`** -- the `**Stop Reason:**` field is updated at every terminal transition. You can open this file at any time to see why the last pipeline ended.

### Stop reason values

| Value | When Eva writes it |
|-------|--------------------|
| `completed_clean` | Pipeline reached Ellis final commit and pushed successfully |
| `completed_with_warnings` | Pipeline completed but an Agatha divergence or Robert/Sable DRIFT was accepted rather than fixed |
| `roz_blocked` | Poirot returned a BLOCKER verdict and you chose not to fix it, or the loop-breaker (3 consecutive failures) fired and you abandoned |
| `user_cancelled` | You said "stop", "cancel", or "abandon" during an active pipeline |
| `hook_violation` | A PreToolUse hook blocked an agent action that could not be retried (path violation), and you abandoned rather than retrying |
| `budget_threshold_reached` | You declined to proceed after the token budget estimate gate |
| `brain_unavailable` | The pipeline required the brain (e.g., Darwin auto-trigger) and the brain was down; you chose to abandon rather than continue in baseline mode |
| `scope_changed` | Sarah discovered scope-changing information and you decided to re-plan rather than continue |
| `session_crashed` | Inferred at next session boot when Eva detects a stale (non-idle) pipeline with no stop reason -- Eva cannot write this in real time during a crash |
| `legacy_unknown` | Read-only inference for pipelines that ran before this feature existed; never written by Eva |

### How session recovery uses stop reasons

When you reopen your IDE after an unclean shutdown, Eva reads the stop reason from `pipeline-state.md`. A `session_crashed` inference tells Eva the previous session ended unexpectedly. A `user_cancelled` tells Eva you made a deliberate choice to stop. These lead to different recovery suggestions.

If the pipeline is stale (non-idle phase, no stop reason recorded), Eva infers `session_crashed` and treats the pipeline as interrupted rather than intentionally stopped.

---

## Sentinel Security Agent

Sentinel is an opt-in security audit agent backed by Semgrep MCP static analysis. It operates under partial information asymmetry: Sentinel receives the code diff and Semgrep scan results, but no spec, ADR, or UX doc. It evaluates security independently of what the code was "intended" to do.

### When Sentinel runs

- **Review juncture only:** In parallel with Poirot final review, Poirot, Robert, and Sable -- after all waves complete, not per wave or per unit

### How Sentinel works

1. Receives the `git diff` for changed files
2. Runs `semgrep_scan` on those files via Semgrep MCP
3. Retrieves structured findings via `semgrep_findings`
4. Filters noise: only reports findings in code that was added or modified (ignores pre-existing issues)
5. Classifies each finding by severity: BLOCKER (exploitable vulnerability), MUST-FIX (security concern), or NIT (hardening suggestion)
6. Cross-references CWE and OWASP identifiers for each finding

### Triage

Eva triages Sentinel findings alongside Poirot using the triage consensus matrix:

- **Sentinel BLOCKER:** Pipeline halts (same as Poirot BLOCKER). Eva verifies the finding is not a false positive before halting.
- **Sentinel MUST-FIX + Poirot/Poirot PASS:** Security concern that other reviewers missed. Queued for Colby with priority.
- **Sentinel MUST-FIX + Poirot MUST-FIX:** Convergent security finding. High-confidence fix needed.

### Enabling Sentinel

**Prerequisite:** Install the Semgrep MCP plugin before running setup.

**Claude Code:**
```sh
claude mcp add semgrep semgrep mcp
```

**Cursor:** Add Semgrep MCP via the Cursor MCP settings or project `.mcp.json`.

You also need a free [semgrep.dev](https://semgrep.dev/login) account -- run `semgrep login` once to authenticate. The free tier includes the Pro Engine for individual use.

During `/pipeline-setup`, answer "yes" when asked about the Sentinel security agent. Setup copies the Sentinel persona file and sets `sentinel_enabled: true` in `pipeline-config.json`.

**Legacy cleanup:** If you ran an older version of `/pipeline-setup`, you may have a `semgrep` entry in your project's `.mcp.json` that was added by setup. That entry is no longer managed by the pipeline. You can remove it manually -- global registration supersedes the project-level entry.

### When Sentinel is disabled

When `sentinel_enabled: false`, Sentinel is completely absent. The triage consensus matrix drops the Sentinel column and behaves as it did before Sentinel was added. No performance cost, no extra tool calls.

---

## Agent Teams

> **Claude Code only.** Agent Teams requires the Claude Code Agent Teams runtime. On Cursor, the pipeline runs sequentially -- same output, same quality gates, same correctness. Agent Teams affects execution speed only.

Agent Teams is an experimental feature that enables parallel wave execution during the Colby build phase. When multiple ADR steps are independent (no shared files), Eva normally executes them sequentially. With Agent Teams enabled, Eva creates Colby Teammate instances that execute those steps simultaneously.

### How it works

1. Eva groups independent ADR steps into waves (existing wave extraction algorithm)
2. For each wave with multiple units, Eva creates one task per unit via `TaskCreate`
3. Teammate instances (Colby clones) pick up tasks and execute build units in parallel
4. Each Teammate marks its task complete when done
5. Eva merges each Teammate's worktree sequentially (deterministic merge order)
6. Poirot verification + Poirot blind review run per unit after merge (unchanged)

### Activation (two gates)

| Gate | How to set | What it means |
|------|-----------|--------------|
| Config gate | `"agent_teams_enabled": true` in `.claude/pipeline-config.json` (Claude Code) or `.cursor/pipeline-config.json` (Cursor) | Pipeline-level opt-in. Set during `/pipeline-setup` (Step 6b). |
| Environment gate | `export CLAUDE_AGENT_TEAMS=1` | Claude Code feature flag that enables the Agent Teams runtime. |

Both gates must pass. If either fails, the pipeline falls back to sequential execution with zero behavioral change.

### What changes with Agent Teams

- Build units within a wave execute in parallel (faster)
- Merge order is deterministic (task creation order, not completion order)
- Full test suite runs between each Teammate merge (quality unchanged)
- Merge conflicts trigger fallback to sequential for the conflicting unit

### What does not change

- Poirot, Robert, Sable, Ellis, Agatha, and all other agents are invoked sequentially
- All 12 mandatory gates are preserved
- Pipeline output is identical -- Agent Teams affects speed, not correctness

---

## CI Watch

CI Watch is an opt-in feature that monitors your CI pipeline after Ellis pushes and autonomously fixes failures. When CI fails, Eva pulls the failure logs, Sherlock diagnoses (user-reported) or Eva investigates (pipeline-internal) the problem, Colby applies a fix, and Poirot verifies it -- all without manual intervention. You review and approve the fix before Ellis pushes it.

### How it works

1. Ellis pushes code to the remote
2. Eva launches a background polling loop that checks CI status every 30 seconds
3. If CI passes, you get a notification with a link to the run
4. If CI fails, the auto-fix cycle runs:
   - Eva pulls the failure logs (last 200 lines)
   - Poirot investigates and diagnoses the root cause
   - Colby applies a fix based on Poirot's diagnosis
   - Poirot verifies the fix
   - Eva pauses and shows you the failure summary, what changed, and Poirot's verdict
   - You approve or reject the fix
5. If you approve, Ellis pushes the fix and the watch restarts
6. The cycle repeats up to a configurable retry limit (default: 3)

### Enabling CI Watch

**Prerequisite:** You need `gh` (GitHub) or `glab` (GitLab) CLI installed and authenticated.

During `/pipeline-setup`, answer "yes" when asked about CI Watch (Step 6c). Setup checks that your platform CLI is configured and authenticated, asks for your preferred max retries, and sets the config values.

If you already ran setup, re-run `/pipeline-setup` to be offered CI Watch.

### Timeout behavior

If CI runs for more than 30 minutes without completing, Eva asks whether you want to keep waiting or abandon the watch. If you abandon, Eva gives you a direct link to check CI status manually.

### Retry exhaustion

After the configured number of fix attempts (default: 3), CI Watch stops and reports all failure patterns encountered. You take over manually from there.

### Session scope

CI Watch is tied to your current session. If you close the terminal while CI is running, the watch stops. There are no orphan processes or cross-session persistence. Check CI manually on your next session if needed.

### When CI Watch is disabled

When `ci_watch_enabled: false` (the default), CI Watch is completely absent. Ellis pushes and the pipeline ends. No polling, no background processes.

---

## Deps Agent

The Deps agent is an opt-in dependency management agent that scans your project for outdated packages, CVE vulnerabilities, and upgrade risk. It produces a report -- it never modifies your files.

### What Deps does

1. **Detects ecosystems** -- finds `package.json`, `requirements.txt`, `Cargo.toml`, and `go.mod` across your project (including monorepos)
2. **Checks for outdated packages** -- runs `npm outdated`, `pip list --outdated`, `cargo outdated`, or `go list -m -u all`
3. **Scans for CVEs** -- runs `npm audit`, `pip-audit`, or `cargo audit` (Go has no standard audit tool -- the report notes this gap)
4. **Predicts breakage** -- for major version bumps, fetches changelogs and cross-references breaking API changes against your actual code usage
5. **Classifies by risk** -- groups results into CVE Alert, Needs Review, Safe to Upgrade, and No Action Needed

### Using /deps

Run `/deps` to trigger a full dependency scan. You can also ask naturally:

```
"Are any of our dependencies outdated?"
"Do we have any CVEs?"
"Is react safe to upgrade?"
```

Eva auto-routes dependency-related questions to the Deps agent when it is enabled.

### Report format

The report groups dependencies by risk level:

- **CVE Alerts** -- packages with known vulnerabilities, with CVSS scores and fix versions
- **Needs Review** -- major version bumps with breaking changes detected in your codebase, with file:line evidence
- **Safe to Upgrade** -- minor/patch bumps with no breaking changes found
- **No Action Needed** -- already at latest version

For risky upgrades, you can ask Deps to produce a migration brief, which Eva then hands to Sarah for a full migration ADR.

### Enabling Deps

During `/pipeline-setup`, answer "yes" when asked about the Deps agent (Step 6d). Setup copies the Deps persona and command files and sets `deps_agent_enabled: true` in `pipeline-config.json`.

If you already ran setup, re-run `/pipeline-setup` to be offered the Deps agent.

### When Deps is disabled

When `deps_agent_enabled: false` (the default), the Deps agent is completely absent. The `/deps` command responds with a message directing you to enable it via `/pipeline-setup`.

---

## Darwin Agent

Darwin is an opt-in pipeline evolution engine. It queries telemetry from the brain, evaluates how each agent has been performing, and proposes structural improvements -- to agent personas, model assignments, wave groupings, or ceremony thresholds. It never modifies files without your approval.

### Prerequisites

Darwin requires the Atelier Brain. Without stored telemetry, Darwin has no data to analyze.

### What Darwin does

1. Reads Tier 3 telemetry summaries from the brain (cost, rework rate, first-pass QA rate, EvoScore per pipeline)
2. Reads agent fitness data (invocation counts, duration, Poirot verdicts per agent)
3. Evaluates degradation signals against configurable thresholds
4. Proposes targeted changes at escalating confidence levels -- conservative suggestions before structural rewrites
5. Presents proposals to you one at a time. You approve, reject (with a reason), or modify each one.

### Using /darwin

Run `/darwin` to trigger a manual analysis. You can also ask naturally:

```
"How are agents performing?"
"Is the pipeline getting more expensive?"
"Analyze the last 5 pipelines"
```

Eva also auto-triggers Darwin at pipeline end when a degradation alert fires (3+ consecutive threshold breaches) and `darwin_enabled: true` is set.

### Enabling Darwin

Set `darwin_enabled: true` in `.claude/pipeline-config.json`, or ask Eva to enable it during a session. Darwin requires the brain to be configured. If `brain_available: false`, Darwin remains unavailable even when the config flag is set.

### When Darwin is disabled

When `darwin_enabled: false` (the default), Darwin is completely absent. No auto-trigger at pipeline end, no `/darwin` routing. Eva announces "Darwin: disabled" at session boot when `darwin_enabled: true` but the brain is unavailable.

---

## Model Selection

Model selection follows a 4-tier task-class system. Each task class maps to a base model and effort level; see `pipeline-models.md` for the authoritative tier table. The effort field in agent frontmatter reflects this assignment.

---

## Agent Telemetry

Agent Telemetry gives you visibility into pipeline efficiency -- cost, duration, rework rates, and quality trends across sessions. It requires the Atelier Brain.

### What you see

**At pipeline end**, Eva prints a telemetry summary:

```
Pipeline complete. Telemetry summary:
  Cost: $3.42 (Colby: $1.80, Poirot: $0.95, Sarah: $0.45, Ellis: $0.12, Poirot: $0.10)
  Duration: 34 min (build: 18 min, QA: 10 min, review: 4 min, docs: 2 min)
  Rework: 1.5 cycles/unit (3 units, 2 first-pass QA)
  EvoScore: 1.0 (24 tests before, 28 after, 0 broken)
  Findings: Poirot 4, Poirot 2, Robert 0 (convergence: 1 shared finding)
```

**At session boot** (after 2+ pipelines with telemetry data), Eva shows trends:

```
Telemetry: Last 5 pipelines -- avg $4.10, 41 min. Rework: 1.2/unit. First-pass QA: 73%.
```

**Degradation alerts** fire when thresholds are exceeded for 3+ consecutive pipelines:

```
Warning: Rework rate above 2.0 for 3 consecutive pipelines.
Last 3: 2.1, 2.3, 2.5. Colby may need persona revision or model upgrade.
```

Alerts only trigger after 3 consecutive breaches to avoid noise from one bad pipeline.

### How it works

Eva captures metrics at three points during a pipeline:

1. **After every agent invocation** -- duration, model, token counts, cost estimate
2. **After each work unit passes QA** -- rework cycles, first-pass QA rate, EvoScore delta, finding counts
3. **At pipeline end** -- aggregated cost, duration, rework rate, quality scores

All metrics are stored in the brain via `agent_capture`. If the brain is unavailable, telemetry capture is skipped entirely -- the pipeline works identically without it. The pipeline-end summary still prints from in-memory data even without the brain, but trend data at boot requires stored history.

### Micro pipelines

Micro pipelines (2 or fewer files, mechanical changes) capture per-invocation metrics only. They skip per-unit and per-pipeline summaries and do not contribute to trend data.

---

## Gauntlet Audit

A gauntlet is a multi-agent, full-codebase audit that produces a combined finding register. It is the most thorough quality assessment the pipeline can perform, examining architecture, code quality, test coverage, security, documentation, spec compliance, and UX compliance in a single coordinated review.

### When to run a gauntlet

- Before major releases, to catch accumulated issues
- After extended development periods with many incremental changes
- When you suspect accumulated technical debt across multiple subsystems
- Periodically as a health check (recommended: once per quarter on active projects)

### How it works

Eva invokes each agent type against the full codebase in sequence. Each agent reviews from its own perspective using its specialized expertise:

1. **Sarah** -- architecture review (structural patterns, ADR compliance, design consistency)
2. **Colby** -- code quality review (implementation patterns, dead code, inconsistencies)
3. **Poirot** -- test coverage review (untested paths, assertion quality, test gaps)
4. **Sentinel** -- security audit (Semgrep-backed SAST, dependency vulnerabilities)
5. **Robert** -- spec compliance review (feature specs vs. implemented behavior)
6. **Sable** -- UX compliance review (user flows vs. implemented interfaces)
7. **Poirot** -- blind code investigation (diff-only review without spec context)
8. **Agatha** -- documentation review (doc coverage, accuracy, staleness)

### What it produces

The gauntlet outputs a directory of findings at `docs/reviews/gauntlet-{date}/`:

- Per-agent finding files (one per agent that participated)
- A combined register (`gauntlet-combined.md`) that merges all findings, deduplicates, and assigns severity

**Severity classification:**

| Severity | Meaning | Action |
|----------|---------|--------|
| Critical | Blocks release -- correctness, security, or data integrity risk | Fix before shipping |
| High | Should fix before release -- significant quality or maintainability concern | Prioritize for current cycle |
| Medium | Next sprint -- moderate impact, not urgent | Schedule in near-term backlog |
| Low | Backlog -- minor improvement opportunity | Address when convenient |

**Multi-agent consensus.** When two or more agents independently flag the same issue from different perspectives, the finding is elevated in the combined register. Consensus findings carry higher confidence than single-agent findings.

### From findings to fixes

Gauntlet findings do not automatically become code changes. The typical flow:

1. Review the combined register with your team
2. Create a remediation ADR (like ADR-0034) that organizes findings into prioritized waves
3. Execute each wave through the normal pipeline flow (Sarah designs, Colby builds, Poirot verifies)

This separation ensures that the audit is thorough and independent, while fixes go through the same quality process as any other change.

---

## Dashboard

The Atelier Dashboard is a browser-based telemetry visualization page. It shows pipeline cost, quality trends, agent fitness, and degradation alerts in one view.

### Opening the dashboard

Run `/dashboard` in your IDE. The skill starts the brain HTTP server if it is not already running and opens the dashboard in your default browser at `http://localhost:8788/ui/dashboard.html`.

### What you see

The dashboard has five sections:

**Pipeline Overview** -- summary stat cards showing all-time totals and per-pipeline averages. Each card shows a primary value (e.g., total cost) with supporting context (e.g., avg cost/pipeline). Duration cards also show min and max across all pipelines when more than one pipeline has been recorded. Before any pipeline data exists, the section displays "Awaiting pipeline data."

**Cost Trend** -- a line chart of daily aggregated pipeline cost. Each data point sums the cost of all pipelines that ran on that calendar day, with tooltips showing the exact dollar amount and pipeline count. Before data exists: "Cost trends appear after your first pipeline."

**Quality Trend** -- a line chart tracking first-pass QA rate and rework rate over time. Quality metrics require pipeline-level telemetry capture. Before data exists: "Quality metrics not yet available" with an explanation of what is needed.

**Agent Fitness** -- a grid of agent cards, one per agent that has been invoked. Each card shows invocation count, average duration, total cost, and average token counts (input/output). Cards display a fitness badge based on quality telemetry:

| Badge | Meaning |
|-------|---------|
| **Thriving** | First-pass QA rate >= 80% and rework rate <= 1.0 |
| **Nominal** | Within acceptable range |
| **Struggling** | QA rate between 50--80% or rework rate between 1.0--2.0 |
| **Processing** | No quality telemetry data available yet |

Eva's card always shows "ORCHESTRATOR" instead of a fitness badge. Clicking any non-Eva agent card opens a detail modal showing that agent's recent invocations (description, duration, cost, model, date).

**Degradation Alerts** -- active alerts from the telemetry alert threshold system. Alerts fire only after 3+ consecutive threshold breaches.

### Project scope selector

When your brain contains telemetry from multiple projects, a project scope selector appears in the header. Select a specific project to filter all dashboard sections, or choose "All Projects" for the combined view. When only one scope exists, the selector is hidden.

### Auto-refresh

The dashboard auto-refreshes every 10 minutes. A green dot indicator in the header shows auto-refresh is active. The "Updated" timestamp shows the last data load time.

---

## Telemetry Hydration

Telemetry hydration reads IDE session JSONL files and captures per-agent token usage, cost, and duration into the brain database. This is how historical telemetry data populates the dashboard and boot trend reports.

### Automatic hydration

Hydration runs automatically at the start of every session via `session-hydrate.sh`, registered as a `SessionStart` hook on both Claude Code and Cursor. It runs silently in the background and never blocks session startup. If the brain is not configured or the hydration script encounters an error, it fails silently.

Each session start triggers two hydration steps:

1. **JSONL telemetry hydration** -- reads token usage, cost, and duration from session JSONL files into the brain (Tier 1 and Tier 3)
2. **State-file parsing** -- reads `docs/pipeline/pipeline-state.md` and `docs/pipeline/context-brief.md` from your project directory. Completed pipeline phases and user decisions from the previous session are captured as brain thoughts attributed to Eva. This is how pipeline history and your session decisions become searchable across sessions and by teammates.

The hook uses the platform-appropriate environment variable (`$CLAUDE_PROJECT_DIR` on Claude Code, `$CURSOR_PROJECT_DIR` on Cursor) to locate both session files and the state directory.

### State-file hydration: what it captures

At the start of each session, the hydrator parses the state files Eva wrote during the previous session:

| Source file | What is extracted | Brain thought type |
|-------------|------------------|--------------------|
| `pipeline-state.md` | Each completed phase item (`- [x]` lines), plus the feature name and sizing | `decision` (`source_agent: 'eva'`, `source_phase: 'pipeline'`) |
| `context-brief.md` | Bullet items under `## User Decisions` | `decision` (`source_agent: 'eva'`, `source_phase: 'pipeline'`) |

This is the mechanism that captures "Eva's pipeline decisions" mentioned in the brain capture overview. Eva writes to these files reliably because they drive session recovery -- the hydrator converts those writes into brain captures without requiring any additional agent behavior.

State-file captures are idempotent. The hydrator uses a content hash per item to skip already-captured entries. You can restart sessions, run multiple sessions, or re-run hydration without duplicating entries.

### Manual hydration

Run `/telemetry-hydrate` to trigger JSONL telemetry hydration manually with verbose output. This is useful after initial brain setup when you want to backfill telemetry from past sessions.

The command:
1. Checks brain availability (stops if brain is not configured)
2. Constructs the session files path from your project directory (using `$CLAUDE_PROJECT_DIR` or `$CURSOR_PROJECT_DIR`)
3. Runs the hydration script and reports results

Example output:
```
Hydrated 12 agents across 4 sessions. Total: 847,293 tokens, $2.4130.
Skipped 8 already-hydrated agents.
```

If everything is already captured: "Telemetry is up to date -- no new data to hydrate."

Note: `/telemetry-hydrate` handles JSONL hydration only. State-file parsing happens automatically at SessionStart via `session-hydrate.sh`.

### What gets captured from JSONL files

The hydration script processes two types of JSONL files:

- **Subagent files** -- one per agent invocation, found in `{session}/subagents/`. Each contains the full conversation between Eva and the subagent, with per-turn token usage.
- **Eva (parent session) files** -- one per session, found at the project sessions root. Contains Eva's main thread conversation.

For each file, the script extracts: model name, input/output tokens, cache read/creation tokens, turn count, and duration (from file timestamps). Cost is computed using the built-in pricing table. Each agent invocation becomes a Tier 1 telemetry thought in the brain.

After processing all Tier 1 entries, the script generates Tier 3 session summaries -- one per session, aggregating total cost, duration, and invocation counts. These summaries power the dashboard's Pipeline Overview and trend charts.

### Duplicate detection

Already-hydrated agents are skipped automatically. You can run hydration repeatedly without creating duplicate entries.

### Live cost data vs. post-session cost data

The pipeline telemetry summary at pipeline end (showing cost per agent and total) is computed from token data extracted by `hydrate-telemetry.mjs` from session JSONL files -- this is the authoritative source for cost figures.

The Claude Code Agent tool does not expose per-agent input/output token counts at runtime (this was investigated as part of ADR-0030 and confirmed unavailable). Eva cannot accumulate a live running cost during the pipeline. What Eva shows mid-pipeline is a heuristic estimate based on phase sizing; the actual figures appear in the post-session telemetry summary after `session-hydrate.sh` runs at the next session start.

If you need cost data before the next session, run `/telemetry-hydrate` manually -- it processes the current session's JSONL files and reports results immediately.

---

## Agent Discovery

Eva discovers custom agents at session boot by scanning `.claude/agents/` (Claude Code) or `.cursor/agents/` (Cursor) for non-core persona files. This lets you extend the pipeline with project-specific agents without modifying core pipeline files.

### Adding a custom agent

1. Create a persona file at `.claude/agents/your-agent-name.md` (Claude Code) or `.cursor/agents/your-agent-name.md` (Cursor) with YAML frontmatter (`name`, `description`, `disallowedTools`)
2. Restart your IDE or start a new session
3. Eva announces the discovery: "Discovered 1 custom agent(s): your-agent-name -- [description]."

### Routing

- Custom agents with **no domain overlap** with core agents are available only via explicit name mention (e.g., "ask your-agent-name about this")
- Custom agents with **overlapping domains** trigger a conflict prompt: "This could go to [core agent] (core) or [your-agent-name] (custom). Which do you prefer?" Your choice is remembered for the session (and persisted in the brain if available)
- Core agents always have routing priority. Custom agents never shadow core agents without explicit consent.

### Inline agent creation

If you paste markdown containing an agent definition pattern (role description, behavioral rules, tool lists, constraints), Eva recognizes it and offers to convert it to a pipeline agent persona file. She handles the conversion, name collision checks, and file writing (via Colby).

---

## Context Management

The pipeline uses three complementary strategies to manage context window usage during long sessions.

### Agent output masking (within-session)

After processing each agent's return, Eva replaces the full output in her working context with a structured one-line receipt. The full output remains on disk (files the agent wrote, `last-qa-report.md`, brain captures). Eva re-reads from disk only when she needs detail to construct the next agent's invocation.

Example receipts:

```
Colby: Unit 2 DONE, 4 files changed, lint PASS, typecheck PASS
Poirot: Wave 1 PASS, 0 blockers, 1 must-fix, 2 suggestions. Report: last-qa-report.md
Poirot: Wave 1 2 findings (0 BLOCKER, 1 MUST-FIX, 1 NIT)
Ellis: Committed a3f8c12 on feature/dark-mode, 7 files
```

This keeps Eva's context window lean across long pipelines without losing any information -- everything is on disk.

### File read masking (within-session)

Before each subagent invocation and at phase transitions, Eva also replaces superseded file read outputs with structured placeholders:

```
[masked: Read src/api/routes.ts, 142 lines, turn 5. Re-read: Read src/api/routes.ts]
```

**Never masked:** Agent reasoning and analysis text, the most recent read of each file, active BLOCKER/MUST-FIX findings, pipeline state files.

**Always masked:** Superseded file reads (older reads of the same file), tool outputs from completed phases, verbose build/test logs after verdict extraction, git diffs after review completion.

### Distillator compression (cross-phase)

When upstream documents (spec, UX doc, ADR) exceed ~5K tokens at a phase boundary, Eva invokes Distillator for lossless compression. Distillator preserves all decisions, constraints, relationships, and scope boundaries while reducing token count. This is reserved for structured documents -- tool outputs use observation masking instead.

### Compaction API (server-side)

Server-side context management handles automatic compaction when the context window fills. On Claude Code, this uses the Compaction API. On Cursor, an equivalent compaction mechanism performs the same function. The pipeline is designed to survive compaction on both platforms:

- **Path-scoped rules** (`pipeline-orchestration.md`, `pipeline-models.md`) -- stored in `.claude/rules/` (Claude Code) or `.cursor/rules/` (Cursor) -- are re-injected from disk on every turn, so mandatory gates and triage logic survive compaction intact
- **Pipeline state** is written to disk at every phase transition, so Eva can recover from the last recorded phase
- **Brain captures** provide a secondary recovery path for decisions and findings
- **PreCompact hook** writes a timestamped marker to `pipeline-state.md` before compaction fires

---

## The Atelier Brain

The brain is optional persistent memory that survives across sessions. Without it, each session starts fresh. With it, agents recall architectural decisions, user corrections, QA lessons, and rejected alternatives from previous sessions.

### Setting up the brain

Run `/brain-setup` (or accept the offer at the end of `/pipeline-setup`).

The setup asks five things:

1. **Personal or shared?**
   - Personal: config stored locally, never committed to git.
   - Shared: config committed to the repo with `${ENV_VAR}` placeholders. Teammates run `/brain-setup` and it detects the existing config automatically.

2. **Database strategy:**

   | Option | Best for | Requirements |
   |--------|----------|-------------|
   | Docker | Quick start, local dev | Docker installed |
   | Local PostgreSQL | Already running PostgreSQL | pgvector and ltree extensions |
   | Remote PostgreSQL | Team use, managed databases | RDS, Supabase, or similar |

3. **OpenRouter API key** -- needed for vector embeddings. Get one at https://openrouter.ai/keys and set `export OPENROUTER_API_KEY="sk-or-..."` in your shell profile.

4. **Scope path** -- a dot-separated namespace like `myorg.myproduct` that organizes brain knowledge.

5. **Brain name** (optional) -- a display name for your brain (e.g., "My Noodle", "Cortex"). Eva uses this name in pipeline announcements and reports instead of the generic "Brain". Leave blank to keep the default.

After answering these questions, the setup registers the brain MCP server in your project's `.mcp.json` with absolute paths and verifies the connection. You do not need to configure the MCP registration manually.

### Teammate onboarding

If a shared brain config already exists in the repo, `/brain-setup` detects it and tells the new team member which environment variables to set. No interactive setup required.

### Hydrating the brain

For existing projects with ADRs, specs, or meaningful git history, run:

```
/brain-hydrate
```

This scans your project artifacts, extracts the reasoning behind decisions (not the content itself), and imports it as brain thoughts. The skill presents what it found and asks for your approval before writing anything.

```
Brain Hydration Scan
====================
ADRs:           4 files in docs/architecture/
Feature specs:  6 files in docs/product/
Error patterns: 3 entries
Git commits:    187 commits (last 6 months)

Estimated thoughts: 25-40
Ready to hydrate?
```

You can narrow the scope: "only ADRs", "skip git history", "since January".

Safe to re-run. Duplicate detection prevents re-importing the same knowledge.

### What the brain captures

Knowledge is captured automatically after each agent completes. You do not need to manage brain contents.

A lightweight Sonnet extractor fires on every Sarah, Colby, or Agatha completion via a `SubagentStop` hook. It reads the agent's output, identifies what is worth preserving, and writes it to the brain -- no agent instruction required. Eva separately captures cross-cutting concerns (your decisions, phase transitions, cross-agent findings).

| What gets captured | Captured by | Why it matters |
|-------------------|-------------|---------------|
| Architectural decisions | brain-extractor (from Sarah) | Future Sarah knows why you chose REST over GraphQL |
| Rejected alternatives | brain-extractor (from Sarah) | Prevents re-evaluating the same rejected approaches |
| Implementation patterns | brain-extractor (from Colby) | Future Colby reuses working patterns without re-discovering them |
| QA lessons | brain-extractor (from Poirot) | Future Colby gets warnings before making the same mistake |
| Structured quality signals | brain-extractor (second pass) | Per-invocation metrics -- Poirot verdicts, finding counts, test counts, Colby file counts, Sarah step counts, Agatha divergence counts -- stored in `metadata.quality_signals` for Darwin analysis |
| Pipeline phase completions | hydrate-telemetry (state-file parse) | Completed pipeline phases from `pipeline-state.md` captured as Eva decisions at session start; Darwin and brain search can see your pipeline history across sessions |
| Your decisions during conversation | hydrate-telemetry (state-file parse) | Items under `## User Decisions` in `context-brief.md` captured at next session start; teammates find your directives via brain search without re-asking |

### Human attribution

Every brain thought records who produced it in a `captured_by` field. The value is resolved automatically from your git config (`user.name`) or the `ATELIER_BRAIN_USER` environment variable if set. You do not need to configure this -- it happens on every capture.

Attribution shows up in search results, browse output, and stats. On a team, this lets you see that Alice captured a preference and Bob captured a correction, giving you a clear trail of who shaped each decision.

If you are running against an existing brain database created before attribution was added, the server auto-migrates the schema on startup. Existing thoughts will have a blank `captured_by` until they are re-captured or updated.

### Brain tools

The brain provides six MCP tools that agents use automatically:

| Tool | Purpose |
|------|---------|
| `agent_capture` | Save a decision, lesson, preference, or correction |
| `agent_search` | Semantic search across brain thoughts |
| `atelier_browse` | Paginated browse by type or status |
| `atelier_stats` | Brain health check |
| `atelier_relation` | Create typed edges between thoughts |
| `atelier_trace` | Walk relation chains from a thought |

For details on brain internals, see the [Technical Reference](technical-reference.md).

---

## Team Collaboration

When multiple people work on the same feature across sessions, the brain bridges the gap between them. Two mechanisms make this work: context brief capture and handoff briefs.

### Context brief preferences carry across sessions

During a pipeline run, Eva records your preferences, corrections, and rejected alternatives in `context-brief.md`. This file is reset at the start of each new feature pipeline, so those decisions would normally be lost.

With the brain enabled, the hydrator captures context brief entries automatically at the start of each session. When `session-hydrate.sh` runs at SessionStart, it parses the `## User Decisions` section of `context-brief.md` and writes each item to the brain as a decision thought attributed to Eva. When a teammate starts a new session on the same feature, their agents find your preferences and corrections via `agent_search` alongside architectural decisions and QA findings.

For example, if you say "no modals, keep it simple" during your session, Eva writes that to the context brief. At the start of the next session (yours or a teammate's), the hydrator captures it to the brain. When your teammate's agents search for context on the feature, they see your directive. They do not need to re-discover your preferences.

The same applies to mid-course corrections ("actually make that a dropdown") and rejected alternatives ("considered caching but rejected -- keep it simple for v1"). Each item under `## User Decisions` in `context-brief.md` is captured at session start.

If the brain is unavailable, nothing changes. Eva writes to `context-brief.md` exactly as before. The brain capture is additive -- it adds cross-session discovery without affecting in-session behavior.

### Handoff briefs

When you finish a session (or say "hand off" mid-pipeline), Eva generates a structured handoff brief and captures it to the brain. This is the synthesis a teammate needs to pick up where you left off -- not scattered fragments, but a single coherent summary.

A handoff brief contains:

- **Completed work** -- which ADR steps or phases were finished
- **Unfinished work** -- what remains, including partially started steps
- **Key decisions** -- the most consequential choices made this session, with reasoning
- **Surprises** -- anything that deviated from the plan
- **User corrections** -- preferences and mid-course changes that shaped the work
- **Warnings** -- known risks, fragile areas, or "watch out for X" notes

When a teammate starts a session on the same feature, the handoff brief surfaces as a high-relevance search result. Multiple handoffs on the same feature (Alice to Bob, Bob to Carol) each appear as separate entries, ordered by recency.

Handoff briefs are generated automatically at pipeline completion and on explicit request mid-pipeline. Eva skips handoff generation for empty sessions (no ADR steps completed and no context brief entries) and when the brain is unavailable. Without the brain, Eva's existing Final Report serves as the session summary.

---

## State Recovery

If your IDE is closed mid-pipeline, no work is lost. Eva persists progress to disk and resumes from the last completed phase when you reopen the session.

### State files

| File | Purpose |
|------|---------|
| `docs/pipeline/pipeline-state.md` | Which phase completed, which is next, unit-by-unit progress |
| `docs/pipeline/context-brief.md` | Your decisions, corrections, and preferences from conversation |
| `docs/pipeline/error-patterns.md` | Error categories from QA findings (feeds retro warnings) |
| `docs/pipeline/investigation-ledger.md` | Hypothesis tracking during debug flows |
| `docs/pipeline/last-qa-report.md` | Poirot's most recent QA report |

### Resuming a session

Just open your IDE in your project. Eva reads the state files and picks up where things left off:

```
Eva: Resuming pipeline for "dark-mode" feature. Last completed phase:
Colby build (Step 2 of 4). Poirot passed Steps 1-2. Starting Colby on Step 3.
```

---

## Customization

### What you configure during setup

`/pipeline-setup` asks about your project-specific values and bakes them into the installed files:

| Setting | Example |
|---------|---------|
| Tech stack | React 19 with Vite, Express.js, PostgreSQL |
| Lint command | `npm run lint` |
| Type check command | `npm run typecheck` |
| Test command | `npm test` |
| Single file test | `npx vitest run` |
| Source structure | `src/features/<feature>/` for UI, `services/api/` for backend |
| Database pattern | Prisma ORM |
| Build command | `npm run build` |
| Coverage thresholds | stmt=70, branch=65, fn=75, lines=70 |
| Complexity limits | TSX CCN <= 18, TS/JS CCN <= 12 |
| Branching strategy | Trunk-based, GitHub Flow, GitLab Flow, or GitFlow |

### What you can adjust after setup

The pipeline files live in your project and are plain Markdown. You can edit them directly. All paths below use `.claude/` (Claude Code) or `.cursor/` (Cursor):

- **Agent personas** (`agents/*.md`) -- adjust voice, constraints, or output format
- **Commands** (`commands/*.md`) -- modify slash command behavior
- **Quality thresholds** (`references/dor-dod.md`) -- change coverage or complexity targets
- **Retro lessons** (`references/retro-lessons.md`) -- add manual lessons for agents to reference
- **Shared agent actions** (`references/agent-preamble.md`) -- customize the shared DoR/DoD and retro lesson protocols
- **QA check procedures** (`references/qa-checks.md`) -- add or modify Poirot's quality checks

### Contributing: Source file structure

Files in `.claude/` (or `.cursor/`) are **generated** by `/pipeline-setup` -- do not edit them directly. Your edits will be overwritten the next time setup runs. Instead, edit the source templates:

- **Agent content** (identity, constraints, workflow): edit `source/shared/agents/{name}.md`
- **Agent frontmatter** (model, tools, hooks): edit `source/claude/agents/{name}.frontmatter.yml` (Claude Code) or `source/cursor/agents/{name}.frontmatter.yml` (Cursor)
- **Commands, rules, references**: same pattern -- shared content in `source/shared/`, platform frontmatter in `source/claude/` or `source/cursor/`

After editing source files, run `/pipeline-setup` to re-install. See the [Triple-Source Assembly Model](technical-reference.md#triple-source-assembly-model) section in the technical reference for full details.

### What is stack-agnostic

The orchestration patterns, quality gates, agent boundaries, and pipeline flow work regardless of your tech stack. The only project-specific values are test commands, directory paths, and threshold numbers.

---

## Branching Strategy

During `/pipeline-setup`, you choose how the pipeline manages branches. The selected strategy determines how Colby creates branches, how Ellis commits, and how Eva handles cleanup after merges.

### Available strategies

| Strategy | Best for | How it works |
|----------|----------|-------------|
| **Trunk-Based Development** | Solo developers, small teams | Commits go directly to main. No branch management overhead. Simplest setup. |
| **GitHub Flow** | Teams using GitHub | Feature branches + merge requests. Main is always deployable. |
| **GitLab Flow** | Teams with staged deployments | GitHub Flow + environment branches (staging, production). Promotion between environments requires approval. |
| **GitFlow** | Versioned software with scheduled releases | Formal release cycle with develop + main branches. Feature branches merge to develop, release branches merge to main. |

### What happens per strategy

**Trunk-Based Development.** Ellis pushes directly to main (or the current branch). No merge requests. If you want a short-lived branch for a specific feature, ask Colby to create one -- this is opt-in, not default.

**GitHub Flow.** Colby creates a feature branch (e.g., `feature/dark-mode`) before building. Per-unit commits go to the feature branch. After the review juncture passes, Colby creates a merge request via the platform CLI (`gh` for GitHub, `glab` for GitLab). Eva asks for your approval before merging. After merge, Eva deletes the feature branch.

**GitLab Flow.** Same feature branch workflow as GitHub Flow, plus environment promotion. After a merge request merges to main, Eva offers to promote: "MR merged to main. Promote to staging?" Each promotion step is a hard pause -- Eva never auto-promotes between environments.

**GitFlow.** Feature branches are created from develop (not main). Colby creates merge requests to develop. Release branches (`release/<version>`) are created from develop when you are ready to release. Hotfix branches are created from main and merge to both main and develop.

### Hotfix flows

All MR-based strategies (GitHub Flow, GitLab Flow, GitFlow) support hotfix branches. When you report a production bug, Colby creates `hotfix/<name>` from main (or the production branch in GitLab Flow). The normal debug pipeline runs: Sherlock diagnoses (user-reported) or Eva investigates (pipeline-internal), Colby fixes, Poirot verifies. Colby then creates a merge request back to the appropriate branch.

### Platform CLI detection

For strategies that use merge requests, setup detects your platform from the git remote URL (GitHub -> `gh`, GitLab -> `glab`). If the CLI is not installed, setup offers to install it for you or tells you how to install it manually.

### Changing your branching strategy

You can switch strategies without re-running the full setup. Ask Eva to "change branching strategy" or "switch to GitHub Flow." Eva will:

1. Confirm no pipeline is currently active
2. Ask which strategy you want
3. Update `.claude/pipeline-config.json` and `.claude/rules/branch-lifecycle.md`

No other files are modified. This takes a few seconds.

### Configuration file

The selected strategy is stored in `.claude/pipeline-config.json` (Claude Code) or `.cursor/pipeline-config.json` (Cursor):

```json
{
  "branching_strategy": "github-flow",
  "platform": "github",
  "platform_cli": "gh",
  "base_branch": "main",
  "integration_branch": "main"
}
```

Eva reads this file at session start. Agents reference it to determine branch naming conventions, merge targets, and cleanup procedures.

---

## Mechanical Enforcement

The pipeline does not rely solely on instructions to keep agents in their lanes. Ten shell-script hooks run automatically on tool calls, blocking actions that would violate agent boundaries, tracking agent telemetry, and preserving context across compaction events.

### What gets blocked

| Violation | What the agent sees |
|-----------|---------------------|
| Eva tries to edit source code | "BLOCKED: Main thread (Eva/Robert/Sable) can only write to docs/pipeline/, docs/product/, or docs/ux/. Route source code changes to Colby, architecture to Sarah, documentation to Agatha." |
| Colby tries to edit a doc file | "BLOCKED: Colby cannot write to docs/. Route documentation changes to Agatha." |
| Eva runs `git commit` directly | "BLOCKED: Eva cannot run git write operations directly. Route commits through Ellis." |
| Eva invokes Ellis during an active pipeline before Poirot passes QA | "BLOCKED: Cannot invoke Ellis — pipeline is active (phase: build) but no Poirot verification PASS found. Poirot must verify Colby's output before committing." |
| Eva invokes Agatha during the build phase | "BLOCKED: Cannot invoke Agatha during the build phase. Agatha writes docs after Poirot's final sweep against verified code." |
| Eva invokes Ellis during an active pipeline before telemetry is captured | "BLOCKED: Cannot invoke Ellis — pipeline is active but telemetry has not been captured. Eva must capture T3 telemetry before committing." |
| Eva runs `npm test` directly | "BLOCKED: Eva cannot run test suites directly. Route QA verification through Poirot." |
| Eva invokes Colby or Ellis without an active pipeline | "BLOCKED: Invoking [agent] without an active pipeline. No telemetry will be captured." |
| Colby or Poirot output is missing DoR/DoD | Advisory warning: "Output may be missing DoR/DoD sections" (does not block) |

When an agent sees a block message, it adjusts: Eva routes the work to the correct agent, or waits until the prerequisite gate is satisfied. You do not need to intervene.

### Non-enforcement hooks

Beyond the blocking hooks, four additional hooks handle telemetry and context preservation:

- **Agent telemetry** (`log-agent-start.sh`, `log-agent-stop.sh`) -- fire on SubagentStart and SubagentStop events, logging agent lifecycle events to `.claude/telemetry/session-hooks.jsonl`. These provide the raw data for pipeline duration and agent performance analysis.
- **Context re-injection** (`post-compact-reinject.sh`) -- fires on PostCompact events (after context compaction) and re-injects `pipeline-state.md` and `context-brief.md` into the post-compaction context, ensuring Eva retains pipeline progress and conversational decisions.
- **Failure tracking** (`log-stop-failure.sh`) -- fires on StopFailure events (when an agent turn ends due to an API error), appending structured entries to `error-patterns.md` for post-pipeline analysis.

These hooks never block -- they exit 0 always and degrade gracefully if the telemetry directory or pipeline files are unavailable.

### Enforcement Audit Trail

Every enforcement decision is durably logged so you can audit what happened during a session and detect recurring violation patterns across sessions.

**What gets logged.** Every time an enforcement hook fires -- whether it blocks an action or allows it -- a JSON line is appended to `~/.claude/logs/enforcement-YYYY-MM-DD.jsonl` (one file per calendar day, UTC). The log captures six fields: timestamp, the tool being intercepted (Write, Edit, Bash, Agent), the agent involved, the decision (blocked or allowed), the reason, and which hook fired. Write failures to this file are silent and never affect the enforcement decision.

**What gets brain-captured.** At session start, `session-hydrate.sh` calls `session-hydrate-enforcement.sh`, which reads the previous day's log and captures blocked decisions into the brain database. Allowed decisions are logged locally for forensic analysis but are not brain-captured (too much noise relative to signal). Blocked events are stored as `insight` thoughts with `metadata.enforcement_event: true`, making them queryable via `agent_search` and visible to Darwin for pattern detection.

**It is automatic and fail-open.** You do not configure or trigger enforcement logging. If the log directory cannot be written, logging degrades silently. If the brain is unavailable during hydration, capture is skipped. The enforcement decision itself is never affected by logging or capture failures.

For the log schema and brain capture details, see the [Technical Reference](technical-reference.md#enforcement-audit-trail).

### Performance: `if` conditionals

One hook uses an `if` conditional in its settings registration (`.claude/settings.json` or `.cursor/settings.json`) to skip hook execution when the condition is not met. The IDE evaluates these expressions before spawning the hook process:

- **`enforce-git.sh`** -- `"if": "tool_input.command.includes('git ')"` skips the hook for Bash calls that do not contain a git command.

This reduces overhead on high-frequency tool calls (Bash calls happen constantly; most are not git commands).

### What you need to know

- **Nothing to configure.** `/pipeline-setup` installs the hook scripts, registers them in `.claude/settings.json` (Claude Code) or `.cursor/settings.json` (Cursor), and customizes the config file with your project's directory paths and test command. It all happens during setup.
- **jq is required for enforcement hooks.** The blocking hooks use `jq` to parse tool input. If `jq` is not installed, the enforcement hooks degrade gracefully (they allow everything rather than blocking). Install it with `brew install jq` (macOS) or `apt install jq` (Linux). The telemetry and compaction hooks do not require `jq`.
- **Quality checks are agent-driven.** Colby runs lint and typecheck during implementation, Eva runs the full test suite during QA, and Ellis verifies before commit. There are no hook-based quality gates -- quality enforcement lives in the pipeline agents themselves.

### Why this matters

Behavioral guidance tells agents what to do. Hooks ensure they cannot do what they should not. A Colby that tries to write documentation gets stopped before the write reaches disk. An Eva that tries to commit code gets redirected to Ellis. The enforcement is mechanical, not discretionary.

For technical details on how the hooks work, see the [Technical Reference](technical-reference.md#enforcement-hooks).

---

## Uninstalling

### Removing pipeline files from a project

Run `/pipeline-uninstall` in your IDE. The skill:

1. **Inventories** all installed pipeline files (rules, agents, commands, references, hooks, state files)
2. **Presents** a full removal plan showing what will be removed, modified, and preserved
3. **Preserves** user-created custom agents (any `.md` files in `.claude/agents/` that are not core pipeline agents)
4. **Offers to back up** retro lessons if the file contains accumulated knowledge
5. **Asks for confirmation** before removing anything
6. **Removes** core pipeline files, cleans up hook registrations from `.claude/settings.json`, and removes the pipeline section from `CLAUDE.md`

After uninstalling, the atelier-pipeline plugin itself remains registered with your IDE. To fully remove the plugin:
- **Claude Code:** `claude plugin remove atelier-pipeline`
- **Cursor:** remove via the Cursor extension manager

To reinstall later: `/pipeline-setup`.

### Disconnecting or removing the brain

Run `/brain-uninstall` in your IDE. The skill detects your brain configuration and offers two paths:

- **Disconnect only** -- removes the config file but leaves the database untouched. You can reconnect later with `/brain-setup`.
- **Full uninstall** -- removes the config file and cleans up the database. The cleanup procedure depends on how the brain was set up:
  - **Docker:** stops the container and optionally deletes the Docker volume
  - **Local PostgreSQL:** optionally drops the database
  - **Remote PostgreSQL:** optionally drops all brain tables (preserves the database itself)

Both paths require explicit confirmation before any destructive action. Database passwords are masked in all output.

The `brain/` directory inside the plugin is not removed -- it contains plugin code, not your data.

---

## Updating the Plugin

### Standard update

**Claude Code:**

1. **Refresh the marketplace and pull the update:**
   ```
   claude plugin marketplace update atelier-pipeline
   claude plugin update atelier-pipeline@atelier-pipeline
   ```

2. **Restart Claude Code** to load the new plugin version.

3. **Re-run `/pipeline-setup`** to sync the updated templates into your project's `.claude/` directory. The setup detects existing files and asks whether to merge or replace. Your project-specific customizations (test commands, directory paths) are preserved during the setup conversation.

**Cursor:**

1. **Update the plugin** via the Cursor extension manager (check for updates).

2. **Restart Cursor** to load the new plugin version.

3. **Re-run `/pipeline-setup`** to sync the updated templates into your project's `.cursor/` directory. Same merge-or-replace behavior as Claude Code.

A session-start hook automatically notifies you when your project's pipeline files are outdated on both platforms. You will see: "Update available: installed vX.Y.Z, plugin vA.B.C."

### Refreshing project files

When you update the plugin, a session-start hook checks whether your project's pipeline files are outdated. If they are, you will see a notification suggesting you re-run `/pipeline-setup`.

Re-running `/pipeline-setup` on an existing project asks whether to merge or replace existing files. Your project-specific customizations (test commands, directory paths) are preserved during the setup conversation.

### Manual installation (without the plugin system)

**Claude Code:**

```bash
git clone https://github.com/robertsfeir/atelier-pipeline.git /tmp/atelier-pipeline
```

Then in Claude Code:

```
Read /tmp/atelier-pipeline/skills/pipeline-setup/SKILL.md and follow its
instructions to install the pipeline in this project
```

**Cursor:**

```bash
git clone https://github.com/robertsfeir/atelier-pipeline.git /tmp/atelier-pipeline
```

Then in Cursor:

```
Read /tmp/atelier-pipeline/.cursor-plugin/skills/pipeline-setup/SKILL.md and follow its instructions
```

---

## Troubleshooting

### Pipeline issues

| Problem | Cause | Fix |
|---------|-------|-----|
| Eva does not recognize slash commands | Pipeline files not installed or IDE not restarted | Run `/pipeline-setup` and restart your IDE (Claude Code or Cursor) |
| Eva routes to the wrong agent | Ambiguous request | Use a slash command to invoke the agent directly (e.g., `/pm`, `/architect`) |
| Pipeline stuck after a Poirot BLOCKER | A blocking QA issue was found | Read Poirot's report. The issue must be fixed before the pipeline can advance. Eva will route it to Colby. |
| "Say go to continue" prompts | Feature was sized as Large | Say "go" to advance, or say "fast track this" to reduce ceremony |
| Pipeline resumes at the wrong phase | Stale state file | Check `docs/pipeline/pipeline-state.md` and correct the current phase, or delete it to start fresh |
| Pipeline state lost after a crash | IDE closed mid-pipeline | State is persisted to `docs/pipeline/pipeline-state.md` after each phase transition. Reopen your IDE and Eva resumes from the last completed phase. If the file is corrupted, delete it and restart the pipeline from the last known good phase. |

### Hook and enforcement issues

| Problem | Cause | Fix |
|---------|-------|-----|
| `jq: command not found` or hooks silently pass everything | `jq` is not installed | macOS: `brew install jq`. Linux: `sudo apt install jq`. The enforcement hooks require `jq` to parse tool input. Without it, hooks cannot inspect arguments and allow all operations through. |
| Hook blocks an action unexpectedly | The agent is attempting an operation outside its allowed boundaries | Read the block message -- it explains which rule was violated and which agent should handle the action instead. Common cases: Eva trying to edit source code (route to Colby), Colby trying to edit docs (route to Agatha), Eva trying to `git commit` (route to Ellis). |
| Hook blocks with a path error for a valid file | The file path matches a blocked prefix in `enforcement-config.json` | Check `.claude/hooks/enforcement-config.json` (Claude Code) or `.cursor/hooks/enforcement-config.json` (Cursor) for `colby_blocked_paths` and other path rules. Adjust if your project structure differs from the defaults. |
| Sequencing hook blocks Ellis invocation | Active pipeline with no Poirot verification PASS | Ellis is only gated during active pipeline phases (build, review, qa). For non-pipeline commits (infrastructure, docs, setup), ensure `pipeline-state.md` has no active phase or set phase to `idle`. If Poirot already passed but the state file was not updated, check `docs/pipeline/pipeline-state.md` for the QA verdict. |

### Brain issues

| Problem | Cause | Fix |
|---------|-------|-----|
| "Brain is not running" | Database not started | Docker: `docker compose -f <plugin-root>/brain/docker-compose.yml up -d`. Local PG: `brew services start postgresql` (macOS) or `sudo systemctl start postgresql` (Linux). |
| "Authentication failed" | Wrong database password | Check that `ATELIER_BRAIN_DB_PASSWORD` is set in your shell profile and matches the database |
| "pgvector extension is required" | Extension not installed | macOS: `brew install pgvector`. Ubuntu: `sudo apt install postgresql-16-pgvector`. Then: `psql -d <db> -c 'CREATE EXTENSION vector;'` |
| "ltree extension is required" | Extension not enabled | `psql -d <db> -c 'CREATE EXTENSION ltree;'` (ships with PostgreSQL) |
| Brain available but agents not using it | `brain_enabled` is false | Check with `atelier_stats`. Re-run `/brain-setup` if needed. |
| Hydration skips everything | Already hydrated | Duplicate detection is working correctly. New thoughts are only captured for new or changed artifacts. |

### Common mistakes

| Mistake | Why it fails | What to do instead |
|---------|-------------|-------------------|
| Saying "build it" without a spec on a Medium/Large feature | Eva requires a Robert spec before advancing past the spec phase | Describe the feature and let Robert produce a spec first, or point Eva to an existing spec |
| Editing Poirot's test assertions to make them pass | Violates  -- the test defines correct behavior | Fix the code to pass the test, not the other way around |
| Skipping UAT on a UI feature | Colby may have built something that does not match Sable's design | Review the mockup in-browser when Eva presents it |
| Force-pushing mid-pipeline | Pipeline state tracks commits | Let Ellis handle all git operations |

---

## Reference

### Installed file structure

The pipeline installs into `.claude/` (Claude Code) or `.cursor/` (Cursor). The structure is identical on both platforms. On Cursor, rules files use the `.mdc` extension instead of `.md` and include frontmatter metadata.

```
your-project/
  .claude/ (or .cursor/)
    .atelier-version                # Plugin version marker for update detection
    rules/                          # Always loaded by the IDE
      default-persona.md (.mdc)     # Eva orchestrator persona
      agent-system.md (.mdc)        # Orchestration rules and routing
      pipeline-orchestration.md (.mdc) # Path-scoped: mandatory gates, triage, wave execution
      pipeline-models.md (.mdc)     # Path-scoped: model selection tables, Micro tier
      branch-lifecycle.md (.mdc)    # Path-scoped: branching strategy rules (selected variant)
    agents/                         # Loaded when subagents are invoked
      sarah.md                        # Architect
      colby.md                      # Engineer
      robert.md                     # Product reviewer
      sable.md                      # UX reviewer
      investigator.md               # Poirot (blind investigator)
      distillator.md                # Compression engine
      ellis.md                      # Commit manager
      agatha.md                     # Documentation
      sentinel.md                   # Security audit (opt-in)
      deps.md                       # Dependency manager (opt-in)
      darwin.md                     # Pipeline evolution engine (opt-in)
    commands/                       # Loaded on slash command
      pm.md, ux.md, architect.md, debug.md,
      pipeline.md, devops.md, docs.md,
      deps.md, darwin.md, telemetry-hydrate.md
    references/                     # Loaded by agents on demand
      dor-dod.md                    # Quality framework
      retro-lessons.md              # Shared lessons from past runs
      invocation-templates.md       # Subagent invocation examples
      pipeline-operations.md        # Operational procedures, observation masking
      agent-preamble.md             # Shared agent required actions
      qa-checks.md                  # Poirot verification check procedures
      branch-mr-mode.md             # Colby branch/MR procedures
      telemetry-metrics.md          # Telemetry metric schemas, cost table, alert thresholds
    hooks/                          # Mechanical enforcement + telemetry + compaction
      enforce-{agent}-paths.sh      # Per-agent Write/Edit path enforcement (7 scripts)
      enforce-sequencing.sh         # Blocks out-of-order agent invocations
      enforce-git.sh                # Blocks git write ops and test commands from main thread
      enforce-pipeline-activation.sh # Blocks Colby/Ellis without active pipeline
      session-hydrate.sh            # SessionStart hook: hydrates brain context at session start
      log-agent-start.sh            # Logs agent start events to telemetry JSONL
      log-agent-stop.sh             # Logs agent stop events to telemetry JSONL
      pre-compact.sh                # Compaction marker for pipeline state preservation
      post-compact-reinject.sh      # Re-injects pipeline state after compaction
      log-stop-failure.sh           # Tracks agent API failures in error-patterns.md
      enforcement-config.json       # Project-specific paths and rules
    pipeline-config.json            # Branching strategy, Sentinel, Agent Teams config
    settings.json                   # Hook registration
  docs/
    pipeline/                       # Eva reads at session start
      pipeline-state.md             # Session recovery state
      context-brief.md              # Cross-session context
      error-patterns.md             # Error pattern tracking
      investigation-ledger.md       # Debug hypothesis tracking
      last-qa-report.md             # Poirot's most recent QA report
```

### Agent quick reference

| Agent | Slash command | Produces | Reads from |
|-------|-------------|----------|------------|
| Robert | `/pm` | Feature spec (`docs/product/`) | Your idea, existing codebase |
| Sable | `/ux` | UX design doc (`docs/ux/`) | Robert's spec |
| Agatha | `/docs` | Doc plan (`docs/product/*-doc-plan.md`) | Spec + UX doc + existing docs |
| Sarah | `/architect` | ADR (`docs/architecture/`) | Spec + UX doc + doc plan + codebase |
| Poirot | (via Eva) | Test assertions, QA reports | ADR test spec + Colby's code |
| Colby | (via Eva) | Implementation code, mockups | ADR + Poirot's tests |
| Poirot | (via Eva) | Blind diff review | Code diff only (no spec, no ADR) |
| Sentinel | (via Eva, opt-in) | Security audit | Code diff + Semgrep scan results |
| Deps | `/deps` (opt-in) | Dependency risk report | Manifests, CVE databases, changelogs |
| Darwin | `/darwin` (opt-in) | Pipeline improvement proposals | Brain telemetry, agent fitness data |
| Ellis | (via Eva) | Git commit + changelog entry | All verified code + docs |

### Quality gates

| Gate | What it checks | What happens on failure |
|------|---------------|----------------------|
| Spec quality | Every endpoint has response shape, measurable acceptance criteria, no "TBD" edge cases | Eva sends Robert back with specific gaps |
| UX pre-flight | ADR maps every UX-specified surface to an implementation step | Eva rejects the ADR and re-invokes Sarah |
| Poirot BLOCKER | Critical code issue (security, data loss, broken functionality) | Pipeline halts. Colby fixes. Poirot re-verifies. |
| Poirot MUST-FIX | Non-critical but required fix | Queued. All must be resolved before Ellis commits. |
| Spec drift | Implementation diverges from spec intent | Hard pause. You decide: update the spec or fix the code. |
| Security vulnerability | Sentinel finds an exploitable issue (BLOCKER) | Pipeline halts. Eva verifies finding is not false positive. Colby fixes. |

### Further reading

- [Technical Reference](technical-reference.md) -- internal architecture, brain schema, agent invocation format, model selection, and operational procedures
