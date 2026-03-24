# Atelier Pipeline -- User Guide

A structured, multi-agent development workflow for Claude Code. Ten specialized agents handle product specs, UX design, architecture, implementation, QA, documentation, and commits -- so you focus on decisions, not process.

---

## Table of Contents

- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Slash Commands](#slash-commands)
- [Working with Agents](#working-with-agents)
- [Running a Full Pipeline](#running-a-full-pipeline)
- [Debugging with /debug](#debugging-with-debug)
- [Phase Sizing](#phase-sizing)
- [The Atelier Brain](#the-atelier-brain)
- [Team Collaboration](#team-collaboration)
- [State Recovery](#state-recovery)
- [Customization](#customization)
- [Mechanical Enforcement](#mechanical-enforcement)
- [Updating the Plugin](#updating-the-plugin)
- [Troubleshooting](#troubleshooting)
- [Reference](#reference)

---

## Quick Start

### 1. Install the plugin

```
/plugin marketplace add robertsfeir/atelier-pipeline
/plugin install atelier-pipeline@atelier-pipeline
```

Restart Claude Code after install.

### 2. Set up the pipeline in your project

Open Claude Code in your project directory and run:

```
/pipeline-setup
```

The setup asks about your project one question at a time: tech stack, test commands, source structure, coverage thresholds. It then installs 27 files into your project (agent personas, commands, references, state tracking).

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
| **Cal** | Software Architect | Produces an Architecture Decision Record (ADR) with implementation steps and a test spec. |
| **Colby** | Software Engineer | Builds mockups and production code. Works one ADR step at a time. |
| **Roz** | QA Engineer | Writes tests before Colby builds, reviews every code change, and verifies bug fixes. |
| **Poirot** | Blind Investigator | Reviews code diffs without seeing the spec -- catches issues that spec-aware reviewers miss. |
| **Agatha** | Documentation Specialist | Plans and writes documentation in parallel with the build. |
| **Ellis** | Commit Manager | Creates atomic commits with Conventional Commits format and updates the changelog. |
| **Distillator** | Compression Engine | Compresses large artifacts between phases to keep agent context windows efficient. |

### The flow

A full pipeline (for a large feature) runs through these phases:

```
Your idea
  -> Robert writes a spec
  -> Sable designs the UX + Agatha plans docs      (parallel)
  -> Colby builds a mockup
  -> Sable verifies the mockup
  -> You review the mockup in-browser (UAT)
  -> Cal architects the solution (ADR + test spec)
  -> Roz reviews the test spec
  -> Roz writes test assertions
  -> Colby builds + Roz reviews each step           (interleaved)
  -> Roz final sweep + Poirot blind review + Robert + Sable   (parallel)
  -> Agatha writes/updates docs
  -> Robert verifies docs match the spec
  -> Ellis commits everything atomically
```

Not every feature goes through every phase. See [Phase Sizing](#phase-sizing) for how Eva adjusts. When an ADR step produces non-code artifacts only (schema DDL, configuration, migration scripts, agent instruction files), the Roz test spec and test authoring phases are skipped for that step -- Colby implements, Roz verifies against ADR requirements, and Agatha follows sequentially.

---

## Slash Commands

These are installed into your project by `/pipeline-setup`. Use them to invoke a specific agent directly, bypassing auto-routing.

| Command | Agent | Use when you want to... |
|---------|-------|------------------------|
| `/pipeline` | Eva | Run the full pipeline from wherever you are |
| `/pm` | Robert | Explore a feature idea and produce a spec |
| `/ux` | Sable | Design the user experience for a spec |
| `/architect` | Cal | Discuss architecture or produce an ADR |
| `/debug` | Roz, Colby | Investigate and fix a bug |
| `/docs` | Agatha | Plan what documentation a feature needs |
| `/devops` | Eva | Handle infrastructure, CI/CD, deployment |

### When you don't need slash commands

Eva auto-routes based on what you say. Most of the time, just describe what you need:

| You say... | Eva routes to... |
|------------|-----------------|
| "What if we added a notification system?" | Robert (product spec) |
| "How should we structure the data layer?" | Cal (architecture) |
| "Build the settings page" | Colby (implementation) |
| "This endpoint returns 500 when the user has no profile" | Roz (bug investigation) |
| "Ship it" | Ellis (commit) |

Slash commands are useful when Eva's auto-routing picks the wrong agent, or when you want to jump directly to a specific phase.

---

## Working with Agents

### Conversational agents (skills)

Robert, Sable, Cal (clarification mode), and Agatha (planning mode) run in the main Claude Code thread. They have a conversation with you.

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

The same pattern applies to Sable (UX flows and states), Cal (architecture trade-offs), and Agatha (doc impact assessment).

### Execution agents (subagents)

Colby, Roz, Poirot, Ellis, and Distillator run in their own context windows. Eva invokes them with focused prompts and reads their results. You see Eva's summaries and status updates.

**Example: What you see during the build phase**

```
Eva: Colby completed ADR Step 1 (data model + migration). Invoking Roz
for scoped review.

Eva: Roz passed Step 1. Moving to Step 2 (API endpoints).

Eva: Colby completed Step 2. Invoking Roz for scoped review.

Eva: Roz flagged a MUST-FIX on Step 2 -- the PATCH endpoint does not
validate email format before saving. Queuing fix for Colby.

Eva: Colby fixed the validation. Roz scoped re-run passed. Moving to Step 3.
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
- A Roz BLOCKER verdict (pipeline halts until resolved)
- Drift between the spec and the implementation (you decide: update spec or fix code)
- An ambiguous finding from Robert or Sable
- A scope-changing discovery from Cal
- Applying a bug fix (you approve Roz's diagnosis first)

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
Starting with Cal for architecture.
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

After you approve the mockup, Cal architects only the backend and data wiring. The validated UI stays as-is.

### Continuous QA

Colby and Roz work in lockstep. Each ADR step is a work unit:

1. Roz writes test assertions for the step
2. Colby implements to pass the tests
3. Roz reviews Colby's output
4. Issues are caught and fixed immediately, before the next step

This prevents a bad pattern in step 2 from spreading to steps 3 through 6.

After all steps pass, Roz does a final sweep to catch cross-step integration issues. Poirot independently reviews the full diff. Robert verifies the implementation matches the spec. On large features, Sable verifies the implementation matches her UX doc.

### Commit

Ellis creates one atomic commit with all code, tests, documentation, and updated specs. Ellis uses Conventional Commits format with a human-readable narrative body.

Eva asks for your approval before pushing to the remote.

---

## Debugging with /debug

Report a bug, and the debug flow handles investigation, fix, and verification:

```
You: /debug The user profile page crashes when the user has no avatar set.
```

### Phase 1: Roz investigates

Roz reproduces the issue, traces the execution path, and identifies the root cause with file paths and line numbers.

### Phase 2: Eva challenges the diagnosis

Eva presents three perspectives before you approve a fix:

```
Eva:
  Roz's diagnosis: NullPointerError in ProfileAvatar.tsx:42 -- component
  assumes `user.avatar` is always defined. Recommended fix: add null check
  with fallback to default avatar.

  Technical counter-hypothesis: Could the API be returning a malformed
  user object when avatar is null? The frontend may be correct to assume
  a non-null value if the API contract specifies one.

  Product consequence check: If we add a fallback avatar, users who
  intentionally removed their avatar will see a default instead of nothing.
  Is that the desired behavior?

  Your call:
  - "fix it" -- Colby applies Roz's fix
  - "investigate the alternative" -- Roz checks the API contract
  - "this is a design problem, stop" -- route to Robert for spec review
```

### Phase 3: Colby fixes

After your approval, Colby applies the fix and writes a regression test that would have caught the bug.

### Phase 4: Roz verifies

Roz confirms the fix works, the regression test covers the bug, and nothing else broke.

### Phase 5: Ellis commits

A clean bug-fix commit with the code change and regression test.

---

## Phase Sizing

Eva assesses every request and adjusts how much ceremony to apply.

| Size | When Eva uses it | What runs | What gets skipped |
|------|-----------------|-----------|-------------------|
| **Small** | Bug fix, single file change, fewer than 3 files, or you say "quick fix" | Colby -> Roz -> Ellis | Robert, Sable, Cal. Agatha runs only if Roz flags doc impact. |
| **Medium** | 2-4 implementation steps, typical feature | Robert -> Cal -> Colby/Roz (interleaved) -> Agatha -> Ellis | Sable mockup + UX review (unless the feature has significant UI) |
| **Large** | 5+ implementation steps, new system, multiple concerns | Full pipeline including Sable mockup, UAT, and final UX review | Nothing |

### Overriding the sizing

| You say | Effect |
|---------|--------|
| "fast track this" | Forces Small sizing |
| "full pipeline" or "full ceremony" | Forces Large sizing with pauses at every transition |
| "quick fix" | Forces Small sizing |

The minimum pipeline is always Colby -> Roz -> Ellis. Roz and Ellis are never skipped.

### Non-code ADR steps

Some ADR steps produce no testable application code -- schema DDL, agent instruction files (markdown), configuration files, or migration scripts. For these steps, Eva skips the Roz test spec review and test authoring phases because there is no application code to test. Instead:

1. Colby implements the non-code step
2. Roz reviews Colby's output in verification mode -- checking that the ADR's acceptance criteria are met rather than running code QA checks
3. Agatha runs after Roz passes (sequentially, not in parallel with Colby, because there is no Roz test spec approval to gate the parallel launch)

If an ADR mixes code and non-code steps, Eva splits them: code steps follow the normal Roz-first TDD flow, non-code steps follow this flow. Both must pass before Ellis commits.

---

## The Atelier Brain

The brain is optional persistent memory that survives across Claude Code sessions. Without it, each session starts fresh. With it, agents recall architectural decisions, user corrections, QA lessons, and rejected alternatives from previous sessions.

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

Agents automatically capture and search during pipeline runs. You do not need to manage brain contents.

| What gets captured | When | Why it matters |
|-------------------|------|---------------|
| Architectural decisions | Cal produces an ADR | Future Cal knows why you chose REST over GraphQL |
| Rejected alternatives | Cal evaluates options | Prevents re-evaluating the same rejected approaches |
| User corrections | You correct an agent mid-pipeline | Future agents apply your preferences without re-asking |
| QA lessons | Roz finds recurring patterns | Future Colby gets warnings before making the same mistake |
| Scope decisions | Robert defines boundaries | Future Robert knows what was explicitly deferred and why |

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

With the brain enabled, Eva dual-writes each context brief entry to the brain as it happens. When a teammate starts a new session on the same feature, their agents find your preferences and corrections via `agent_search` alongside architectural decisions and QA findings.

For example, if you say "no modals, keep it simple" during your session, Eva writes that to the context brief and also captures it as a `preference` thought in the brain. When your teammate's session begins, their agents search for context on the feature and see your directive. They do not need to re-discover your preferences.

The same applies to mid-course corrections ("actually make that a dropdown") and rejected alternatives ("considered caching but rejected -- keep it simple for v1"). Each is captured with the appropriate type so the brain ranks them correctly.

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

If Claude Code is closed mid-pipeline, no work is lost. Eva persists progress to disk and resumes from the last completed phase when you reopen the session.

### State files

| File | Purpose |
|------|---------|
| `docs/pipeline/pipeline-state.md` | Which phase completed, which is next, unit-by-unit progress |
| `docs/pipeline/context-brief.md` | Your decisions, corrections, and preferences from conversation |
| `docs/pipeline/error-patterns.md` | Error categories from QA findings (feeds retro warnings) |
| `docs/pipeline/investigation-ledger.md` | Hypothesis tracking during debug flows |
| `docs/pipeline/last-qa-report.md` | Roz's most recent QA report |

### Resuming a session

Just open Claude Code in your project. Eva reads the state files and picks up where things left off:

```
Eva: Resuming pipeline for "dark-mode" feature. Last completed phase:
Colby build (Step 2 of 4). Roz passed Steps 1-2. Starting Colby on Step 3.
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

### What you can adjust after setup

The pipeline files live in your project and are plain Markdown. You can edit them directly:

- **Agent personas** (`.claude/agents/*.md`) -- adjust voice, constraints, or output format
- **Commands** (`.claude/commands/*.md`) -- modify slash command behavior
- **Quality thresholds** (`.claude/references/dor-dod.md`) -- change coverage or complexity targets
- **Retro lessons** (`.claude/references/retro-lessons.md`) -- add manual lessons for agents to reference

### What is stack-agnostic

The orchestration patterns, quality gates, agent boundaries, and pipeline flow work regardless of your tech stack. The only project-specific values are test commands, directory paths, and threshold numbers.

---

## Mechanical Enforcement

The pipeline does not rely solely on instructions to keep agents in their lanes. Four shell-script hooks run automatically on every tool call, blocking actions that would violate agent boundaries before they happen.

### What gets blocked

| Violation | What the agent sees |
|-----------|---------------------|
| Eva tries to edit source code | "BLOCKED: Main thread (Eva/Robert/Sable) can only write to docs/pipeline/, docs/product/, or docs/ux/. Route source code changes to Colby, architecture to Cal, documentation to Agatha." |
| Colby tries to edit a doc file | "BLOCKED: Colby cannot write to docs/. Route documentation changes to Agatha." |
| Eva runs `git commit` directly | "BLOCKED: Eva cannot run git write operations directly. Route commits through Ellis." |
| Eva invokes Ellis before Roz passes QA | "BLOCKED: Cannot invoke Ellis -- no Roz QA PASS found in pipeline-state.md. Roz must verify Colby's output before committing." |
| Eva invokes Agatha during the build phase | "BLOCKED: Cannot invoke Agatha during the build phase. Agatha writes docs after Roz's final sweep against verified code." |

When an agent sees a block message, it adjusts: Eva routes the work to the correct agent, or waits until the prerequisite gate is satisfied. You do not need to intervene.

### What you need to know

- **Nothing to configure.** `/pipeline-setup` installs the hook scripts, registers them in `.claude/settings.json`, and customizes the config file with your project's directory paths. It all happens during setup.
- **jq is required.** The hooks use `jq` to parse tool input. If `jq` is not installed, the hooks degrade gracefully (they allow everything rather than blocking). Install it with `brew install jq` (macOS) or `apt install jq` (Linux).
- **Brain usage warnings.** A separate hook warns (without blocking) when an agent completes work without evidence of brain tool usage. This is a visibility aid, not a hard gate.

### Why this matters

Behavioral guidance tells agents what to do. Hooks ensure they cannot do what they should not. A Colby that tries to write documentation gets stopped before the write reaches disk. An Eva that tries to commit code gets redirected to Ellis. The enforcement is mechanical, not discretionary.

For technical details on how the hooks work, see the [Technical Reference](technical-reference.md#enforcement-hooks).

---

## Updating the Plugin

### Standard update

```
claude plugin marketplace update atelier-pipeline
claude plugin update atelier-pipeline@atelier-pipeline
```

The first command refreshes the marketplace catalog. The second pulls the new plugin version. Restart Claude Code after updating.

### Refreshing project files

When you update the plugin, a session-start hook checks whether your project's pipeline files are outdated. If they are, you will see a notification suggesting you re-run `/pipeline-setup`.

Re-running `/pipeline-setup` on an existing project asks whether to merge or replace existing files. Your project-specific customizations (test commands, directory paths) are preserved during the setup conversation.

### Manual installation (without the plugin system)

```bash
git clone https://github.com/robertsfeir/atelier-pipeline.git /tmp/atelier-pipeline
```

Then in Claude Code:

```
Read /tmp/atelier-pipeline/skills/pipeline-setup/SKILL.md and follow its
instructions to install the pipeline in this project
```

---

## Troubleshooting

### Pipeline issues

| Problem | Cause | Fix |
|---------|-------|-----|
| Eva does not recognize slash commands | Pipeline files not installed or Claude Code not restarted | Run `/pipeline-setup` and restart Claude Code |
| Eva routes to the wrong agent | Ambiguous request | Use a slash command to invoke the agent directly (e.g., `/pm`, `/architect`) |
| Pipeline stuck after a Roz BLOCKER | A blocking QA issue was found | Read Roz's report. The issue must be fixed before the pipeline can advance. Eva will route it to Colby. |
| "Say go to continue" prompts | Feature was sized as Large | Say "go" to advance, or say "fast track this" to reduce ceremony |
| Pipeline resumes at the wrong phase | Stale state file | Check `docs/pipeline/pipeline-state.md` and correct the current phase, or delete it to start fresh |

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
| Editing Roz's test assertions to make them pass | Violates Roz-first TDD -- the test defines correct behavior | Fix the code to pass the test, not the other way around |
| Skipping UAT on a UI feature | Colby may have built something that does not match Sable's design | Review the mockup in-browser when Eva presents it |
| Force-pushing mid-pipeline | Pipeline state tracks commits | Let Ellis handle all git operations |

---

## Reference

### Installed file structure

```
your-project/
  .claude/
    rules/                       # Always loaded by Claude Code
      default-persona.md         # Eva orchestrator persona
      agent-system.md            # Orchestration rules and routing
    agents/                      # Loaded when subagents are invoked
      cal.md                     # Architect
      colby.md                   # Engineer
      roz.md                     # QA
      robert.md                  # Product reviewer
      sable.md                   # UX reviewer
      investigator.md            # Poirot (blind investigator)
      distillator.md             # Compression engine
      ellis.md                   # Commit manager
      documentation-expert.md    # Agatha (documentation)
    commands/                    # Loaded on slash command
      pm.md, ux.md, architect.md, debug.md,
      pipeline.md, devops.md, docs.md
    references/                  # Loaded by agents on demand
      dor-dod.md                 # Quality framework
      retro-lessons.md           # Shared lessons from past runs
      invocation-templates.md    # Subagent invocation examples
      pipeline-operations.md     # Operational procedures
    hooks/                       # Mechanical enforcement (PreToolUse/PostToolUse)
      enforce-paths.sh           # Blocks Write/Edit outside agent's allowed paths
      enforce-sequencing.sh      # Blocks out-of-order agent invocations
      enforce-git.sh             # Blocks git write ops from main thread
      check-brain-usage.sh       # Warns when agents skip brain tools
      enforcement-config.json    # Project-specific paths and rules
    settings.json                # Hook registration
  docs/
    pipeline/                    # Eva reads at session start
      pipeline-state.md          # Session recovery state
      context-brief.md           # Cross-session context
      error-patterns.md          # Error pattern tracking
      investigation-ledger.md    # Debug hypothesis tracking
      last-qa-report.md          # Roz's most recent QA report
```

### Agent quick reference

| Agent | Slash command | Produces | Reads from |
|-------|-------------|----------|------------|
| Robert | `/pm` | Feature spec (`docs/product/`) | Your idea, existing codebase |
| Sable | `/ux` | UX design doc (`docs/ux/`) | Robert's spec |
| Agatha | `/docs` | Doc plan (`docs/product/*-doc-plan.md`) | Spec + UX doc + existing docs |
| Cal | `/architect` | ADR (`docs/architecture/`) | Spec + UX doc + doc plan + codebase |
| Roz | (via Eva) | Test assertions, QA reports | ADR test spec + Colby's code |
| Colby | (via Eva) | Implementation code, mockups | ADR + Roz's tests |
| Poirot | (via Eva) | Blind diff review | Code diff only (no spec, no ADR) |
| Ellis | (via Eva) | Git commit + changelog entry | All verified code + docs |

### Quality gates

| Gate | What it checks | What happens on failure |
|------|---------------|----------------------|
| Spec quality | Every endpoint has response shape, measurable acceptance criteria, no "TBD" edge cases | Eva sends Robert back with specific gaps |
| UX pre-flight | ADR maps every UX-specified surface to an implementation step | Eva rejects the ADR and re-invokes Cal |
| Roz BLOCKER | Critical code issue (security, data loss, broken functionality) | Pipeline halts. Colby fixes. Roz re-verifies. |
| Roz MUST-FIX | Non-critical but required fix | Queued. All must be resolved before Ellis commits. |
| Spec drift | Implementation diverges from spec intent | Hard pause. You decide: update the spec or fix the code. |

### Further reading

- [Technical Reference](technical-reference.md) -- internal architecture, brain schema, agent invocation format, model selection, and operational procedures
