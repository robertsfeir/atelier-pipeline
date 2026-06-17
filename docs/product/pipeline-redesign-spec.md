## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Default install includes only Robert, Sarah, and Colby | User direction |
| 2 | All other agents except Sable are opt-in, added after install; Sable is always-on but not core | User direction |
| 3 | Each added agent has a configurable firing position: after-every-unit, pipeline-end, or on-demand | User direction |
| 4 | Hooks must respect the active roster — absent agents produce no hook activity and no blocking | User direction |
| 5 | When Ellis is absent, Eva provides a generic commit capability with no persona and no ceremony | User direction |
| 6 | /pipeline-setup asks about tech stack and offers to install dependencies | User direction |
| 7 | /pipeline-setup presents an agent selection step; choices write the roster to pipeline-config.json | User direction |
| 8 | Dashboard feature is removed entirely | User direction |
| 9 | Kanban and other plugin integrations are removed entirely | User direction |
| 10 | Hooks that enforce absent agents must not block pipeline progress | User direction |

**Retro risks:** Existing installs may have all agents and all hooks registered. The upgrade path must disable hooks for unselected agents without breaking the enforcement chain for selected ones.

---

# Feature Spec: Pipeline Redesign — Minimal Install, Configurable Roster, Setup Wizard

**Author:** Robert (CPO) | **Date:** 2026-06-17
**Status:** Draft

## Summary

This redesign replaces a fixed, high-ceremony pipeline with a minimal core and an explicit opt-in model for every agent beyond the essential trio. Users get a working pipeline immediately after install — Eva orchestrating Robert (product, both reviewer and spec-producer personas), Sarah (architecture), and Colby (implementation) — and add more agents only when they want them. Each added agent is configured with a firing position that the user controls. The setup wizard collects enough context to configure the pipeline correctly at install time, including tech stack, dependency installation, and agent selection. Dashboard and plugin-integration features are removed.

## Problem Statement

### Problem 1 — Too Much Ceremony

The current pipeline installs every agent and routes work through every phase regardless of project size or user preference. Users encounter mandatory stops for reviewers they did not ask for, hooks that block progress when agents are absent, and sequential steps that feel like process for process's sake. For solo developers and small teams, this overhead outweighs the benefit.

The pipeline should start minimal and earn its ceremony. If a user never selects Poirot, the verification phase should not exist. If a user never selects Ellis, there should be no commit persona, just a direct commit capability.

### Problem 2 — Configurable Pipeline

The current model treats every agent as always-on. There is no supported way to say "run Poirot at the end of the pipeline, not after every unit" or "I want Sable available on demand but not blocking every Colby handoff." The result is a binary choice: full ceremony or manual workarounds.

The pipeline should let users define their roster and firing positions explicitly. The enforcement layer should respect those choices mechanically — if an agent is not on the roster, its hooks do not fire and do not block.

### Problem 3 — Project Setup Wizard

The current /pipeline-setup asks about branching strategy, model provider, and test commands. It does not ask about tech stack in a way that informs tooling decisions, does not offer to install missing dependencies, and does not ask which agents the user actually wants. Every user gets the same install regardless of their context.

The setup wizard should gather enough information to configure the pipeline for the user's actual environment, including stack-aware dependency offers and an explicit agent selection step that writes the roster to config.

## Personas

**Solo developers** who want a lightweight pipeline with minimal blocking and no agents they did not choose.

**Small teams** who want Poirot and Ellis but do not need Sable or Sentinel unless they ask for them.

**Established teams** doing a fresh install who want the full roster configured upfront rather than adding agents piecemeal.

**Users upgrading from the current pipeline** who need their existing configuration migrated to the new roster model without losing their branching strategy or project settings.

## Vocabulary

These terms are used precisely throughout this spec and in configuration:

| Term | Definition |
|------|-----------|
| **Roster** | The set of agents the user has explicitly enabled. Stored in `pipeline-config.json` as `agent_roster`. |
| **Core trio** | Robert (both `robert` reviewer and `robert-spec` producer), Sarah, and Colby — always installed, not configurable. |
| **Always-on, not core** | Sable (both `sable` reviewer and `sable-ux` producer) — available without roster selection; does not appear in the agent-selection list during setup; does not block if not invoked. |
| **Optional agents** | Poirot, Ellis, Agatha, Sentinel, Sherlock — available to add; each requires a firing position. |
| **Firing position** | When an optional agent activates: `after-every-unit`, `pipeline-end`, or `on-demand`. |
| **after-every-unit** | Agent fires each time Colby completes a work unit. |
| **pipeline-end** | Agent fires once at the end of the full pipeline, before any commit step. |
| **on-demand** | Agent is available but only fires when the user explicitly invokes it or Eva routes to it by name. |
| **Generic commit** | A no-persona commit capability Eva provides when Ellis is not on the roster. No ceremony, no changelog. |

## User Flows

### Flow 1: Fresh Install — Minimal Path

```
User: /pipeline-setup

Wizard: What should I call this project in telemetry? > my-app
Wizard: What's your tech stack? > Python 3.12, FastAPI, PostgreSQL
Wizard: What's your test framework and commands? > pytest; pytest -x for single file
Wizard: Linting and type-checking? > ruff check . && mypy .
Wizard: Where does your source code live? > src/
Wizard: Which branching strategy? > trunk-based

Wizard: Which agents do you want beyond the core trio (Robert, Sarah, Colby)?
        Available agents:
          Poirot   — Blind code reviewer. Catches regressions and quality issues after Colby builds.
          Ellis    — Commit manager. Writes structured commit messages and manages changelogs.
          Agatha   — Documentation writer. Produces and maintains docs.
          Sentinel — Security auditor. Semgrep-backed SAST scanning.
          Sherlock — Bug detective. Deep investigation for user-reported bugs.

        Note: Sable (UX) is always available — invoke her any time via /ux or by name.
        (Press Enter to accept minimal install — core trio only)

User: Poirot, Ellis

Wizard: Poirot fires... (after-every-unit | pipeline-end | on-demand)?
User: pipeline-end

Wizard: Ellis fires... (after-every-unit | pipeline-end | on-demand)?
User: pipeline-end

Installing...
Done. Active roster: Robert, Sarah, Colby, Poirot (pipeline-end), Ellis (pipeline-end).
```

### Flow 2: Roster — Minimal (Core Trio Only)

Eva orchestrates Robert → Sarah → Colby with no additional agents. After Colby completes, Eva announces: "Work complete. Want to commit? I'll run `git commit` with a summary message." User confirms or provides a commit message. Eva runs the commit directly with no persona handoff.

### Flow 3: Roster — With Poirot at pipeline-end

Eva orchestrates Robert → Sarah → Colby (all units). At pipeline end, Eva invokes Poirot for a blind review of the full diff. Poirot findings route back to Colby if any are action items. No Poirot invocation occurs after individual Colby units.

### Flow 4: Roster — With Poirot after-every-unit

Eva invokes Poirot after each Colby unit completes. Findings from each unit are resolved before moving to the next. This matches the current pipeline behavior for teams that want maximum coverage.

### Flow 5: Roster — Ellis on-demand

Ellis is on the roster but does not fire automatically at pipeline end. The user says "commit this" or "ship it" and Eva routes to Ellis. Until then, no commit step appears.

### Flow 6: Generic Commit Fallback (Ellis Not on Roster)

When the user signals intent to commit ("commit", "ship it", "push this") and Ellis is not on the roster:

```
Eva: Ready to commit. What should the commit message say? (Or press Enter for a generated summary.)
User: [Enter]
Eva: Committing: "Add FastAPI endpoint for user profile retrieval"
     git commit -am "Add FastAPI endpoint for user profile retrieval"
     Done. SHA: a1b2c3d
```

No persona, no changelog, no structured commit format. One question, one commit.

### Flow 7: Adding an Agent After Install

```
User: Add Sentinel to my pipeline
Eva: Sentinel (security auditor) added to your roster. When should it fire?
     (after-every-unit | pipeline-end | on-demand)
User: on-demand
Eva: Sentinel is now available. It runs when you ask for a security review.
     Hooks updated in .claude/settings.json.
```

Eva routes to Colby to update `pipeline-config.json` and wire the relevant hooks. Eva never writes config files herself.

### Flow 8: Tech Stack Dependency Offer (Setup Wizard)

```
Wizard: Your stack includes FastAPI and PostgreSQL. I can check for missing tools.

Checking... ruff: not found. mypy: not found. psql: found.

On macOS, I can install missing tools with Homebrew:
  brew install ruff mypy

Install them now? (yes / no / show me the commands)
User: yes

Installing ruff... done.
Installing mypy... done.

Re-checking... ruff: found. mypy: found. psql: found.
All required tools available.
```

On non-Mac platforms, the wizard detects the available package manager (apt-get, dnf, winget) and adapts the offer accordingly. If no package manager is found, the wizard prints the install commands and moves on.

## Configuration Model

The `agent_roster` key in `pipeline-config.json` is the single source of truth for the active roster. Example for the Poirot + Ellis at pipeline-end scenario:

```json
{
  "agent_roster": {
    "robert":   { "enabled": true,  "firing": "core" },
    "sarah":    { "enabled": true,  "firing": "core" },
    "colby":    { "enabled": true,  "firing": "core" },
    "poirot":   { "enabled": true,  "firing": "pipeline-end" },
    "ellis":    { "enabled": true,  "firing": "pipeline-end" },
    "sable":    { "enabled": false },
    "agatha":   { "enabled": false },
    "sentinel": { "enabled": false },
    "sherlock": { "enabled": false }
  }
}
```

Core trio agents always have `"firing": "core"` and cannot be disabled. Optional agents default to `"enabled": false`. When `enabled` is false, the agent's persona file is still installed (for on-demand use via explicit invocation), but its hooks do not register in `settings.json`.

## Hook Behavior by Roster State

| Hook | Agent Enabled | Agent Disabled |
|------|--------------|----------------|
| Poirot blind-review gate | Fires per firing position | Does not register in settings.json |
| Ellis commit gate | Fires per firing position | Does not register; generic commit used |
| Sable UX review gate | Fires per firing position | Does not register |
| Sentinel SAST gate | Fires per firing position | Does not register |
| enforce-sequencing | Respects enabled agents only | Absent agents not in sequence chain |

## Dashboard and Plugin Integration Removal

The `dashboard_mode` key is removed from `pipeline-config.json`. All dashboard-related hooks, commands, and references are deleted from the source tree. Kanban and other plugin integration files are deleted. No migration path is offered — these features are discontinued.

Existing `pipeline-config.json` files that contain `dashboard_mode` are silently migrated by /pipeline-setup: the key is stripped during Step 0 cleanup.

## Acceptance Criteria

**Minimal install:**

1. After /pipeline-setup completes with no agents selected beyond the core trio, `agent_roster` in `pipeline-config.json` contains exactly Robert, Sarah, and Colby with `"enabled": true`, and all other agents with `"enabled": false`.
2. After a minimal install, `settings.json` contains no hook registrations for Poirot, Ellis, Sable, Agatha, Sentinel, or Sherlock.
3. After a minimal install, a full pipeline run completes (Robert → Sarah → Colby) without any prompt, block, or error referencing a non-roster agent.

**Firing positions:**

4. When Poirot is set to `after-every-unit`, Eva invokes Poirot after each Colby work-unit completion, before starting the next unit.
5. When Poirot is set to `pipeline-end`, Eva invokes Poirot exactly once after all Colby units are done and before any commit step.
6. When Poirot is set to `on-demand`, Poirot does not appear in any pipeline phase unless the user explicitly requests a review.
7. When Ellis is set to `pipeline-end`, Eva hands off to Ellis after Poirot (if present) completes and before announcing the pipeline is done.
8. When Ellis is set to `on-demand`, Eva does not prompt or route to Ellis automatically at pipeline end.
9. Firing position applies independently per agent — two agents can have different firing positions simultaneously.

**Generic commit fallback:**

10. When Ellis is not on the roster and the user signals commit intent ("commit", "ship it", "push this"), Eva asks at most one question (commit message) and executes `git commit` directly.
11. When Ellis is not on the roster, Eva's commit execution produces no changelog entry, no structured commit format, and no persona handoff.
12. When Ellis is not on the roster and the user provides a commit message in their signal ("commit with message: fix login bug"), Eva skips the question and commits immediately.
13. When the user presses Enter without providing a message in the generic commit flow, Eva generates a one-line summary from the diff and commits with that message.

**Hook roster enforcement:**

14. When an agent is not on the roster (`"enabled": false`), its corresponding hook scripts are not listed in `settings.json` after install.
15. When an agent is removed from the roster (disabled after a prior install), running /pipeline-setup updates `settings.json` to remove that agent's hooks within the same session.
16. A pipeline run with a disabled agent never produces a "waiting for [agent]" state or a hook timeout from that agent.

**Setup wizard — agent selection:**

17. During /pipeline-setup, after branching strategy selection, the wizard presents the five optional agents (Poirot, Ellis, Agatha, Sentinel, Sherlock) with one-line descriptions of each. Sable is not listed — she is always available without selection.
18. The wizard accepts a blank Enter as "core trio only" and writes the roster accordingly.
19. For each selected agent, the wizard asks exactly one follow-up question: the firing position.
20. The firing-position prompt offers exactly three choices: `after-every-unit`, `pipeline-end`, `on-demand`.
21. The wizard writes the complete `agent_roster` block to `pipeline-config.json` before moving to the next setup step.
22. The wizard prints a confirmation line listing the active roster and firing positions before finishing.
23. When /pipeline-setup runs as part of a plugin update and detects an existing full-roster install, it prompts the user: "Want to keep your current pipeline configuration or customize it?" — if the user chooses to customize, the wizard launches the agent-selection step (AC 17–22); if the user keeps the current configuration, the existing roster is preserved without modification.

**Setup wizard — tech stack and dependencies:**

24. During /pipeline-setup Step 1, the wizard asks the user to describe their tech stack in plain language (language, framework, runtime).
25. After the user provides a tech stack, the wizard checks whether tools inferred from that stack are available on PATH (e.g., `node`, `python3`, `cargo`, `psql`, the configured lint and test commands).
26. For each missing tool, the wizard offers to install it using the platform's package manager (Homebrew on macOS, apt-get on Debian/Ubuntu, dnf on Fedora, winget on Windows).
27. If the user accepts the install offer, the wizard runs the package manager command and re-checks PATH before continuing.
28. If no package manager is detected, the wizard prints the install command(s) and moves on without blocking.
29. The wizard does not attempt to install tools the user's stack does not require.
30. The wizard's tool-to-package-manager mapping covers the predefined common stacks: Node/JS, Python, Go, Rust, Ruby, Java/JVM, PHP, and .NET. For tools the user mentions that fall outside this table, the wizard attempts best-effort inference to a known package manager install; if no mapping is found, the wizard prints the tool name and instructs the user to install it manually, then continues without blocking.

**Sable always-on status:**

31. After a minimal install (core trio only), Sable is available via `/ux` or explicit name mention without any additional configuration step.
32. Sable does not appear in the agent-selection list presented by the setup wizard. The wizard displays a note that Sable is always available.
33. Sable's absence from a user's explicit selections does not produce any "agent not on roster" error or hook block; she never requires a firing-position entry in `agent_roster`.

**Agatha firing position:**

34. The setup wizard offers only `pipeline-end` as the firing position for Agatha. The wizard does not present `after-every-unit` or `on-demand` as choices when the user selects Agatha.

**Dashboard and plugin integration removal:**

35. After install, `pipeline-config.json` does not contain a `dashboard_mode` key.
36. After install, no file in `.claude/` references dashboard mode, Kanban, or plugin integration (except in changelog/ADR documents).
37. When /pipeline-setup encounters an existing `pipeline-config.json` containing `dashboard_mode`, it removes the key and continues without prompting the user.

**Agent addition post-install:**

38. When the user asks to add an agent after install, Eva prompts for the firing position, then routes to Colby to update `pipeline-config.json` and `settings.json`.
39. After Colby completes the addition, Eva announces the agent's name and its configured firing position.
40. Eva does not write `pipeline-config.json` or `settings.json` herself — these changes always route to Colby.

## Out of Scope

- **Removing agent persona files for disabled agents.** Persona files are always installed so agents remain available for on-demand invocation via explicit name mention, even when not on the roster.
- **Per-feature firing position overrides.** Firing position is configured per agent at install time, not per feature or per pipeline run. Dynamic overrides are not supported in this slice.
- **Brain integration changes.** The brain capture model, mybrain migration, and hydration behavior are unchanged by this redesign.
- **Discovered agents.** The agent discovery protocol (custom agents dropped into `.claude/agents/`) is unchanged. Discovered agents remain available via explicit name mention regardless of roster state.
- **CI Watch behavior.** CI Watch remains a separate opt-in feature with its own config flag. This spec does not change how CI Watch is configured or fired.
- **Agent teams (experimental).** The experimental agent teams feature is unchanged.
- **Cursor plugin.** This spec covers the Claude Code install path. Cursor overlay changes are a follow-on task.
- **Rollback or undo for agent removal.** Re-adding a removed agent follows the same add-after-install flow; no special rollback is provided.
- **Sable UX review as a blocking gate.** This spec does not decide whether Sable at `after-every-unit` is a hard block or a soft advisory. That decision is deferred to the implementation ADR.

## Open Questions

None. All open questions resolved.
