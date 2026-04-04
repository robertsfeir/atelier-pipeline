# ADR-0022: Wave 3 -- Native Enforcement Redesign

## DoR: Requirements Extracted

**Sources:** Brain context (5 design decisions from Cal/Eva architecture session), context-brief.md (Wave 3 scope), pipeline-state.md (Wave 3 queue), enforce-paths.sh (163-line monolith), enforcement-config.json (current config), agent persona files (12 source templates + 12 installed copies per platform), SKILL.md (installation manifest), settings.json (hook registration), .cursor-plugin/hooks/hooks.json (Cursor hook model), retro-lessons.md, ADR-0020 (Wave 2 predecessor), ADR-0019 (Cursor port)

| # | Requirement | Source | Citation |
|---|-------------|--------|----------|
| R1 | Split `source/` into platform-specific directories for Claude Code and Cursor | Brain Decision 5 (user decision) | "Split source/ into separate Claude Code and Cursor directories" |
| R2 | Design DRY strategy for shared content vs platform-divergent frontmatter | Brain Decision 5 | "Persona CONTENT is largely shared; FRONTMATTER diverges. Cal must design a DRY strategy" |
| R3 | Update /pipeline-setup to install from new directory structure | Brain Decision 4 | "verify /pipeline-setup installs correctly" |
| R4 | Phase 1 must land and stabilize BEFORE Phase 2 begins | Brain Decision 4 (user decision) | "If enforcement changes land on structure about to be split, everything needs rebasing" |
| R5 | Replace enforce-paths.sh monolith with per-agent frontmatter hooks | Brain Decision 2 (Layer 2) | "Move from global enforce-paths.sh monolith to per-agent frontmatter hooks. Delete enforce-paths.sh entirely" |
| R6 | Three-layer enforcement pyramid: tools/disallowedTools -> frontmatter hooks -> global hooks | Brain Decision 2 | "LAYER 1 tools/disallowedTools, LAYER 2 frontmatter hooks, LAYER 3 global hooks" |
| R7 | Add `permissionMode: acceptEdits` on write-heavy agents (Colby, Cal, Agatha, Ellis) | Brain Decision 1 | "Use acceptEdits on write-heavy agents to auto-approve file edits" |
| R8 | Robert and Sable become write-capable subagents for spec/UX production | Brain Decision 1 (bonus) | "Robert and Sable become write-capable subagents for spec/UX production" |
| R9 | Robert-spec writes to docs/product/, Sable-ux writes to docs/ux/ | Brain Decision 2 | "Robert-spec: tools: Read, Write, Edit, Glob, Grep, Bash -- writes to docs/product/" |
| R10 | Per-agent hook scripts are ~15-20 lines each, no agent_type check, no case statement | Brain Decision 2 | "Each script ~15-20 lines. No agent_type check, no case statement, no config file read" |
| R11 | Cursor keeps global hook model (no frontmatter hooks at runtime) | Brain Decision 3 (#1) | "Cursor divergence: No frontmatter hooks/permissionMode/disallowedTools at runtime" |
| R12 | Robert/Sable dual mode: two persona files each (read-only reviewer + write-capable producer) | Brain Decision 3 (#2) | "Two persona files each (read-only reviewer + write-capable producer)" |
| R13 | Eva main thread tightened: only docs/pipeline/ write access | Brain Decision 3 (#3) | "Eva: Only docs/pipeline/ write access after Robert-spec/Sable-ux become subagents" |
| R14 | Agents MUST be in project .claude/agents/ (plugin native agents/ loses frontmatter) | Brain Decision 3 (#4) | "Agents MUST be in project .claude/agents/" |
| R15 | Core agent constant updated: clarify robert-spec and sable-ux naming | Brain Decision 3 (#6) | "Adding robert-spec and sable-ux -- clarify if they're new core agents or variants" |
| R16 | PreToolUse hooks fire regardless of permissionMode | Brain Decision 3 (#7) | "Hooks fire with acceptEdits" |
| R17 | Parent mode override: user's auto/bypassPermissions overrides subagent permissionMode | Brain Decision 3 (#8) | "Parent mode override" |
| R18 | Colby edits source/ only, never .claude/ | Brain Decision 3 (#9) + CLAUDE.md | "Source-only editing" |
| R19 | 265 existing bats tests cover enforce-paths.sh; new scripts need equivalent coverage | Brain Decision 3 (#10) | "265 existing bats tests" |
| R20 | Ellis has no path hooks (full write access, sequencing enforced at Layer 3) | Brain Decision 2 | "Ellis: No path hooks" |
| R21 | Read-only agents keep existing disallowedTools blocking Write/Edit/MultiEdit/NotebookEdit | Brain Decision 2 (Layer 1) | "Read-only agents (7): Keep existing disallowedTools" |
| R22 | /pm and /ux become subagent invocations for spec/UX production | Brain Decision 3 (#2) | "/pm and /ux become subagent invocations" |
| R23 | Wave-boundary compaction advisory: SubagentStop prompt hook detects Ellis per-wave commit and advises Eva to suggest /compact | User request (2026-04-03) | Context quality degrades in long sessions; wave boundaries are optimal compact trigger |

**Retro risks:**

- **Lesson #003 (Stop Hook Race Condition):** Directly relevant to Phase 2 hook design. Per-agent hooks must be lightweight (~15-20 lines), exit 0 on non-enforcement paths, and never block. The new scripts are simpler than enforce-paths.sh (no config file reads, no case statements), which reduces this risk.
- **Lesson #005 (Frontend Wiring Omission):** Relevant to the source/ split design. The split creates a producer (source templates) and multiple consumers (.claude/, .cursor-plugin/, target project installs). All three must stay in sync. The DRY strategy must prevent drift between Claude Code and Cursor persona content.

**Spec challenge:** The spec assumes Claude Code frontmatter hooks (`hooks:` field in agent YAML) fire per-agent and receive the same input schema as global PreToolUse hooks (tool_name, tool_input.file_path). If the frontmatter hook input differs from global hook input (different JSON schema, missing fields), every per-agent enforcement script would need to handle both schemas. **Are we confident?** Yes -- Claude Code documentation confirms frontmatter hooks receive identical input to their global counterparts for the same event type. The `hooks:` frontmatter field maps 1:1 to the same event types in settings.json.

**SPOF:** The /pipeline-setup install logic (Phase 1). After the source/ split, every target project relies on /pipeline-setup reading from the correct platform subdirectory. If the install logic has a bug in platform detection (Claude Code vs Cursor), agents get the wrong frontmatter and enforcement silently fails. **Failure mode:** Claude Code project gets Cursor agents (no frontmatter hooks) or vice versa (Cursor gets hooks it cannot execute). **Graceful degradation:** Layer 3 global hooks (enforce-sequencing.sh, enforce-git.sh) still function regardless of platform. Layer 1 tools/disallowedTools still functions. Only Layer 2 (per-agent path enforcement) fails. The system degrades to Wave 2 behavior (global enforce-paths.sh model), not to zero enforcement.

**Anti-goals:**

1. **Anti-goal: Merging Claude Code and Cursor into a single universal format.** Reason: The platforms have fundamentally different runtime capabilities (Claude Code has frontmatter hooks, permissionMode, disallowedTools enforcement; Cursor has none of these at runtime). Forcing a lowest-common-denominator format would sacrifice Claude Code capabilities. Revisit: If Cursor adopts Claude Code's frontmatter hook model (full parity).

2. **Anti-goal: Dynamic source template generation at install time.** Reason: Source templates are static files with placeholders. A build system that generates templates from fragments would add toolchain complexity (build step, validation, debugging) for a problem that is adequately solved by the overlay pattern described below. Revisit: If the number of platform-specific variations exceeds 3 (currently 2: Claude Code, Cursor) or if per-project customization requirements grow beyond placeholder substitution.

3. **Anti-goal: Migrating existing enforce-paths.sh test coverage to per-agent test files in Phase 1.** Reason: Phase 1 is structural (directory split + install verification). Test migration belongs to Phase 2 where enforce-paths.sh is actually replaced. Running Phase 1 tests against the existing monolith verifies the split did not break anything. Revisit: N/A -- test migration happens in Phase 2 by design.

---

## Status

Proposed

## Context

The atelier-pipeline has shipped two waves of the agent frontmatter enrichment initiative:

- **Wave 1 (v3.16.0):** Added per-agent metadata fields (model, effort, color, maxTurns, disallowedTools) to all 12 agent persona files.
- **Wave 2 (v3.17.0, ADR-0020):** Modernized the hook layer with `if` conditionals, lifecycle telemetry hooks (SubagentStart/SubagentStop), PostCompact context re-injection, and StopFailure error tracking.

Wave 3 addresses two remaining gaps:

**Gap 1: Source directory structure does not reflect platform divergence.** The `source/` directory contains a single set of templates used for both Claude Code and Cursor. Today, persona content is identical across platforms, but frontmatter diverges significantly: Claude Code agents get `hooks:`, `permissionMode`, `mcpServers` fields that Cursor ignores at runtime. Maintaining a single set of templates with both platforms' frontmatter in the same file is unsustainable -- it forces either lowest-common-denominator frontmatter or complex conditional logic in /pipeline-setup.

**Gap 2: Path enforcement is centralized in a monolith.** `enforce-paths.sh` (163 lines, 7-branch case statement) handles all agent path enforcement through a single global PreToolUse hook. Every Write/Edit/MultiEdit triggers this script, which reads `enforcement-config.json`, determines the agent type, and applies agent-specific rules. This design has three problems:
1. **Performance:** Every write operation spawns the process and reads the config, even when the agent has no path restrictions (Ellis) or when the restriction is trivially expressible.
2. **Maintenance:** Adding a new write-capable agent requires modifying the monolith's case statement, the config file, the tests, and the documentation. Each change is a merge conflict risk.
3. **Visibility:** Agent restrictions are scattered across enforce-paths.sh, enforcement-config.json, and agent persona files. No single file answers "what can this agent write?"

Claude Code's frontmatter `hooks:` field (available since v2.1.89) enables per-agent hook registration directly in the agent's persona file. This moves enforcement from a global script to the agent definition itself -- the agent file becomes the single source of truth for that agent's capabilities and restrictions.

Additionally, Robert and Sable currently exist only as read-only reviewers (subagent mode) and main-thread skill personas. They cannot produce specs or UX docs as subagents because they lack write access. Making them write-capable subagents eliminates the main-thread bottleneck where Eva holds context while Robert-skill or Sable-skill writes.

### Why Two Phases

The source/ split (Phase 1) and the enforcement redesign (Phase 2) are deliberately sequenced, not parallelized. If enforcement changes (new hook scripts, modified frontmatter) land on the current single-source structure, and the source split then follows, every file touched in Phase 2 needs rebasing against the new directory structure. Splitting first creates a stable foundation. The user has explicitly mandated this sequencing.

## Decision

Implement Wave 3 in two sequential phases:

### Phase 1: Source Directory Split + Install Verification

Split `source/` into platform-specific directories using an **overlay pattern**: a shared base directory contains content common to both platforms, and platform-specific overlays contain only the divergent frontmatter.

**Directory structure after split:**

```
source/
  shared/                          # Content bodies (no frontmatter)
    agents/
      cal.md                       # Full persona content, no YAML frontmatter
      colby.md
      roz.md
      robert.md
      sable.md
      ellis.md
      agatha.md
      investigator.md
      distillator.md
      sentinel.md
      darwin.md
      deps.md
    commands/                      # Identical across platforms
      pm.md
      ux.md
      architect.md
      debug.md
      pipeline.md
      devops.md
      docs.md
      create-agent.md
      telemetry-hydrate.md
      deps.md
      darwin.md
    references/                    # Identical across platforms
      agent-preamble.md
      dor-dod.md
      invocation-templates.md
      pipeline-operations.md
      qa-checks.md
      retro-lessons.md
      branch-mr-mode.md
      telemetry-metrics.md
      xml-prompt-schema.md
      cloud-architecture.md
    pipeline/                      # Identical across platforms
      pipeline-state.md
      context-brief.md
      error-patterns.md
      investigation-ledger.md
      last-qa-report.md
      pipeline-config.json
    rules/                         # Identical across platforms
      default-persona.md
      agent-system.md
      pipeline-orchestration.md
      pipeline-models.md
    variants/                      # Identical across platforms
      branch-lifecycle-trunk-based.md
      branch-lifecycle-github-flow.md
      branch-lifecycle-gitlab-flow.md
      branch-lifecycle-gitflow.md
    dashboard/                     # Identical across platforms
      telemetry-bridge.sh
  claude/                          # Claude Code frontmatter overlays
    agents/
      cal.frontmatter.yml
      colby.frontmatter.yml
      roz.frontmatter.yml
      robert.frontmatter.yml
      sable.frontmatter.yml
      ellis.frontmatter.yml
      agatha.frontmatter.yml
      investigator.frontmatter.yml
      distillator.frontmatter.yml
      sentinel.frontmatter.yml
      darwin.frontmatter.yml
      deps.frontmatter.yml
    hooks/                         # Claude Code hook scripts
      enforce-git.sh
      enforce-sequencing.sh
      enforce-pipeline-activation.sh
      enforce-paths.sh             # KEPT in Phase 1 (deleted in Phase 2)
      enforcement-config.json
      log-agent-start.sh
      log-agent-stop.sh
      log-stop-failure.sh
      post-compact-reinject.sh
      pre-compact.sh
      prompt-brain-capture.sh
      prompt-brain-prefetch.sh
      warn-brain-capture.sh
      warn-dor-dod.sh
  cursor/                          # Cursor frontmatter overlays
    agents/
      cal.frontmatter.yml
      colby.frontmatter.yml
      roz.frontmatter.yml
      robert.frontmatter.yml
      sable.frontmatter.yml
      ellis.frontmatter.yml
      agatha.frontmatter.yml
      investigator.frontmatter.yml
      distillator.frontmatter.yml
      sentinel.frontmatter.yml
      darwin.frontmatter.yml
      deps.frontmatter.yml
    hooks/
      hooks.json                   # Cursor plugin hook registration
```

**Overlay pattern explained:**

Each `*.frontmatter.yml` file contains only the YAML frontmatter block for that agent on that platform. During /pipeline-setup installation, the install script:
1. Reads the frontmatter overlay for the target platform
2. Reads the shared content body
3. Concatenates: `---\n` + frontmatter + `---\n` + content body
4. Writes the assembled file to the target project

Example `source/claude/agents/colby.frontmatter.yml`:
```yaml
name: colby
description: >
  Senior Software Engineer. Invoke when there is an ADR with an implementation
  plan ready to build. Implements code step-by-step, writes tests (TDD),
  produces production-ready code.
model: sonnet
effort: high
color: green
maxTurns: 100
tools: Read, Write, Edit, MultiEdit, Glob, Grep, Bash, Agent(roz, cal)
permissionMode: acceptEdits
hooks:
  - event: PreToolUse
    matcher: Write|Edit|MultiEdit
    hooks:
      - type: command
        command: "$CLAUDE_PROJECT_DIR/.claude/hooks/enforce-colby-paths.sh"
mcpServers:
  - atelier-brain
```

Example `source/cursor/agents/colby.frontmatter.yml`:
```yaml
name: colby
description: >
  Senior Software Engineer. Invoke when there is an ADR with an implementation
  plan ready to build. Implements code step-by-step, writes tests (TDD),
  produces production-ready code.
model: sonnet
effort: high
color: green
maxTurns: 100
tools: Read, Write, Edit, MultiEdit, Glob, Grep, Bash, Agent(roz, cal)
mcpServers:
  - atelier-brain
```

The Cursor overlay omits `permissionMode` and `hooks` (Cursor ignores them at runtime). The shared content body in `source/shared/agents/colby.md` contains the full persona from `<identity>` through `</output>` with the `<!-- Part of atelier-pipeline -->` comment but no YAML frontmatter.

**What does NOT move:** The `.cursor-plugin/` directory (plugin distribution format) is NOT part of this split. It remains as-is -- it is the packaged plugin, not the source templates. The split affects only `source/` (the template source of truth).

### Phase 2: Enforcement Redesign

After Phase 1 stabilizes, implement the three-layer enforcement pyramid:

**Layer 1 -- tools/disallowedTools (zero cost, runtime-level):**

| Agent | Capability Model | Field |
|-------|-----------------|-------|
| Cal | Write: docs/architecture/ only | `tools: Read, Write, Edit, Glob, Grep, Bash, Agent(roz)` |
| Colby | Write: most paths (blocked paths enforced by hook) | `tools: Read, Write, Edit, MultiEdit, Glob, Grep, Bash, Agent(roz, cal)` |
| Roz | Write: test files + docs/pipeline/ only | `disallowedTools: Agent, Edit, MultiEdit, NotebookEdit` |
| Ellis | Full write access | `disallowedTools: Agent, NotebookEdit` |
| Agatha | Write: docs/ only | `disallowedTools: Agent, NotebookEdit` |
| Robert (reviewer) | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| Robert-spec (producer) | Write: docs/product/ only | `tools: Read, Write, Edit, Glob, Grep, Bash` |
| Sable (reviewer) | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| Sable-ux (producer) | Write: docs/ux/ only | `tools: Read, Write, Edit, Glob, Grep, Bash` |
| Investigator | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| Distillator | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| Sentinel | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| Darwin | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |
| Deps | Read-only | `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit` |

**Layer 2 -- Per-agent frontmatter hooks (Claude Code only):**

| Agent | Hook Event | Script | What it enforces |
|-------|-----------|--------|-----------------|
| Roz | PreToolUse(Write) | enforce-roz-paths.sh | Only test files (test_patterns) + docs/pipeline/ |
| Cal | PreToolUse(Write\|Edit) | enforce-cal-paths.sh | Only docs/architecture/ |
| Colby | PreToolUse(Write\|Edit\|MultiEdit) | enforce-colby-paths.sh | Block colby_blocked_paths |
| Agatha | PreToolUse(Write\|Edit\|MultiEdit) | enforce-agatha-paths.sh | Only docs/ |
| Robert-spec | PreToolUse(Write\|Edit) | enforce-product-paths.sh | Only docs/product/ |
| Sable-ux | PreToolUse(Write\|Edit) | enforce-ux-paths.sh | Only docs/ux/ |
| Ellis | (none) | -- | Full access; sequencing at Layer 3 |

Each script follows a minimal pattern (~15-20 lines):
```bash
#!/bin/bash
# enforce-{agent}-paths.sh -- Per-agent path enforcement
# Frontmatter hook: fires only for this agent's Write/Edit operations
set -euo pipefail
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
[ -f "${CLAUDE_PROJECT_DIR:-.}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
FILE_PATH="${FILE_PATH#"$PROJECT_ROOT"/}"

# Agent-specific path check (example: Cal)
case "$FILE_PATH" in
  docs/architecture/*) exit 0 ;;
  *) echo "BLOCKED: Cal can only write to docs/architecture/. Attempted: $FILE_PATH" >&2
     exit 2 ;;
esac
```

No `agent_type` check needed (the hook only fires for its agent). No config file read needed (paths are hardcoded -- simpler, faster, and the paths rarely change). No case statement over agents (each script handles exactly one agent).

**Layer 3 -- Global hooks in settings.json (cross-cutting only):**

| Hook | Status | Rationale |
|------|--------|-----------|
| enforce-paths.sh | **DELETED** | Replaced by Layer 2 per-agent hooks |
| enforcement-config.json | **SIMPLIFIED** | Remove enforcement-path-specific keys (`architecture_dir`, `product_specs_dir`, `ux_docs_dir`); retain `pipeline_state_dir` (consumed by enforce-pipeline-activation.sh, enforce-sequencing.sh), `test_patterns`, `colby_blocked_paths`, `test_command` |
| enforce-sequencing.sh | KEPT | Cross-cutting: enforces pipeline phase order |
| enforce-pipeline-activation.sh | KEPT | Cross-cutting: enforces active pipeline for Colby/Ellis |
| enforce-git.sh | KEPT | Cross-cutting: enforces git operations via Ellis |
| All lifecycle/telemetry hooks | KEPT | Non-enforcement, cross-cutting |

**Eva main thread tightening:**

After Robert-spec and Sable-ux become write-capable subagents, the main thread (Eva + Robert-skill + Sable-skill) no longer needs docs/product/ or docs/ux/ write access. The global settings.json PreToolUse hook for the main thread restricts to docs/pipeline/ only. A new lightweight `enforce-eva-paths.sh` replaces the main-thread case in the deleted enforce-paths.sh.

**permissionMode additions (Claude Code only):**

| Agent | permissionMode | Rationale |
|-------|---------------|-----------|
| Colby | acceptEdits | Write-heavy; auto-approve reduces friction |
| Cal | acceptEdits | Write-heavy during ADR production |
| Agatha | acceptEdits | Write-heavy during doc writing |
| Ellis | acceptEdits | Write-heavy during commit operations |
| All others | (omitted) | Read-only agents do not need plan mode; tools/disallowedTools handles capability restriction; plan mode blocks Bash which reviewers need |

**Robert/Sable dual-mode design:**

Each agent gets two persona files:
- `robert.md` -- Read-only reviewer (existing, unchanged). `name: robert`
- `robert-spec.md` -- Write-capable producer. `name: robert-spec`
- `sable.md` -- Read-only reviewer (existing, unchanged). `name: sable`
- `sable-ux.md` -- Write-capable producer. `name: sable-ux`

**Core agent constant update:** `robert-spec` and `sable-ux` are added as new core agents (not variants of robert/sable). The constant becomes:

```
cal, colby, roz, ellis, agatha, robert, robert-spec, sable, sable-ux, investigator, distillator
```

This ensures agent discovery does not treat them as custom agents. The enforce-sequencing.sh hook recognizes both robert and robert-spec (and both sable and sable-ux) for gate enforcement.

**Routing changes:**

| Current | After |
|---------|-------|
| `/pm` -> Robert-skill (main thread writes docs/product/) | `/pm` -> Robert-spec subagent (own context, writes docs/product/) |
| `/ux` -> Sable-skill (main thread writes docs/ux/) | `/ux` -> Sable-ux subagent (own context, writes docs/ux/) |
| Eva main thread: docs/pipeline/ + docs/product/ + docs/ux/ | Eva main thread: docs/pipeline/ only |

**Cursor enforcement strategy:**

Cursor keeps the global hook model. The Cursor `hooks.json` continues to reference `enforce-paths.sh` (which still exists in `source/cursor/hooks/` for Cursor's use, even though it is deleted from `source/claude/hooks/` in Phase 2). Cursor agents get frontmatter overlays without `hooks:` or `permissionMode` fields. Cursor enforcement is equivalent to the current Wave 2 model.

## Alternatives Considered

### Alternative A: Full File Copies (No Overlay)

Maintain complete, independent copies of each agent file per platform in `source/claude/agents/` and `source/cursor/agents/` with no shared directory.

**Pros:**
- Simplest to understand -- each platform directory is self-contained
- No assembly step during install -- copy file directly
- Easy to diverge platform content if needed in the future

**Cons:**
- 12 agents x 2 platforms = 24 files with near-identical content bodies (100-250 lines each)
- Content changes (workflow updates, constraint changes, example additions) must be applied to both copies
- Drift between copies is inevitable without CI enforcement
- Existing tests that reference `source/agents/*.md` break and need 2x path updates

**Rejected because:** The drift risk is the dealbreaker. Persona content changes (which happen frequently -- every retro, every pipeline evolution) would need to be applied to 24 files instead of 12. The overlay pattern eliminates this by maintaining content in one place.

### Alternative B: Build-Time Assembly with Templating Engine

Use a templating engine (e.g., Mustache, Handlebars, or a custom shell script) to generate platform-specific files from a single template with conditional blocks.

**Pros:**
- Single source file per agent
- Platform differences expressed as conditionals within the template
- No separate frontmatter files

**Cons:**
- Adds a build step to the development workflow
- Template syntax mixed with markdown content reduces readability
- Conditional blocks for frontmatter fields create visual noise in a file that agents read at invocation time
- Debugging template rendering errors is harder than debugging file concatenation
- Violates the project's "static files with placeholders" convention (CLAUDE.md)

**Rejected because:** The complexity is disproportionate. The divergence is confined to YAML frontmatter (5-15 lines); the content body (100-250 lines) is identical. A full templating engine to manage 5-15 lines of divergence per file is over-engineering.

### Alternative C: Overlay Pattern (Chosen)

Separate frontmatter into platform-specific `.frontmatter.yml` files. Shared content in `source/shared/`. Assembly at install time via string concatenation.

**Pros:**
- Content maintained once (12 shared files, not 24 copies)
- Frontmatter divergence is explicit and visible (compare `.frontmatter.yml` files side by side)
- Assembly is trivial: `cat frontmatter.yml + content.md > output.md`
- No build toolchain, no template engine, no conditional syntax
- Existing placeholder pattern (`{config_dir}`, `{test_command}`, etc.) works unchanged
- Git diffs are clean -- frontmatter changes show in frontmatter files, content changes show in content files

**Cons:**
- More files in the repository (12 shared + 12 claude frontmatter + 12 cursor frontmatter = 36 vs current 12)
- /pipeline-setup install logic becomes slightly more complex (read + concatenate vs copy)
- Developers must know to check both the frontmatter and content files when reviewing an agent

**Chosen because:** It eliminates drift risk (single content source), keeps platform differences visible (separate files), and uses no build toolchain. The file count increase is manageable and well-organized.

## Consequences

### Positive
- **Single source of truth per agent:** Each agent's capabilities (tools, permissions, hooks, paths) are visible in its persona file's frontmatter, not scattered across enforce-paths.sh + enforcement-config.json + the persona file.
- **Simpler enforcement scripts:** Per-agent scripts are 15-20 lines each vs 163-line monolith. No shared state, no config file reads, no case statements.
- **Platform divergence is explicit:** Claude Code and Cursor frontmatter differences are visible in separate files, not hidden in conditional logic.
- **Performance improvement:** Per-agent hooks fire only for that agent's operations, not for every write operation across all agents.
- **Robert/Sable as subagents:** Spec and UX doc production runs in its own context window, freeing Eva's context for orchestration.
- **Eva tightening:** Eva's main thread write access shrinks from 3 directories to 1, reducing the blast radius of any main-thread enforcement bug.

### Negative
- **More source files:** 36 agent-related files (shared + 2 platform overlays) vs current 12.
- **Install complexity:** /pipeline-setup must assemble files from overlay + content instead of direct copy.
- **Cursor divergence widens:** Cursor keeps the monolith pattern while Claude Code moves to per-agent hooks. This is intentional but increases the maintenance surface.
- **Test rewrite:** The enforce-paths.bats test file (16 @test declarations) must be replaced with per-agent test files. Net test count will increase (minimum 56 tests across 7 files) due to per-agent specificity, distributed across dedicated files.
- **Two Robert/Sable files:** Developers and Eva must distinguish between `robert.md` (reviewer) and `robert-spec.md` (producer). Naming makes this clear but it is a new concept.

### Risk: No graceful degradation path for Phase 2 hooks

If a per-agent frontmatter hook has a bug (e.g., enforce-colby-paths.sh incorrectly blocks a valid path), there is no fallback to the deleted enforce-paths.sh. The mitigation is that Layer 1 (tools/disallowedTools) and Layer 3 (global hooks) still function. An agent blocked by a buggy Layer 2 hook can be unblocked by temporarily removing the `hooks:` field from its frontmatter (a one-line edit). This is a finding, not a blocker.

## Migration Path

### For Existing Projects (Already Using Atelier Pipeline)

Running `/pipeline-setup` (re-install/update) after upgrading the plugin:

1. **Phase 1 migration (automatic):** /pipeline-setup detects the new source structure and installs from `source/shared/` + `source/claude/` (or `source/cursor/`). The assembled output is identical to current installed files (content + frontmatter = same file). No manual action needed. Existing pipeline state files are preserved (state file guard).

2. **Phase 2 migration (automatic):** /pipeline-setup installs the new per-agent hook scripts to `.claude/hooks/`, updates agent persona files with frontmatter hooks, and removes the enforce-paths.sh entry from settings.json. The old enforce-paths.sh file remains on disk but is no longer registered. Existing enforcement-config.json is simplified (agent-specific rules removed, test_patterns and colby_blocked_paths retained).

3. **Robert-spec / Sable-ux (new files):** /pipeline-setup installs the new persona files. Eva's routing logic (in agent-system.md / default-persona.md) is updated to recognize the new subagent names.

### Rollback Strategy

**Phase 1 rollback:** Revert the source/ directory structure to flat (undo the split). /pipeline-setup reads from `source/` as before. One `git revert` of the Phase 1 commit(s). Safe indefinitely -- no data migration involved.

**Phase 2 rollback:** Revert the enforcement changes. Re-register enforce-paths.sh in settings.json. Remove per-agent hook scripts. Remove frontmatter `hooks:` and `permissionMode` fields from agent overlays. One `git revert` of the Phase 2 commit(s), followed by `/pipeline-setup` re-install in target projects. Safe indefinitely -- no data migration involved.

**Rollback window:** Unlimited. Both phases modify only source templates and installed config files. No database schema changes, no data migration, no state format changes.

---

## Implementation Plan

### Phase 1: Source Directory Split + Install Verification

#### Step 1a: Create Shared Content Directory

Create `source/shared/` and move content bodies (without frontmatter) for all non-agent files that are identical across platforms.

- **Files to create:**
  - `source/shared/commands/` -- move all 11 command files (identical across platforms)
  - `source/shared/references/` -- move all 10 reference files (identical across platforms)
  - `source/shared/pipeline/` -- move all 6 pipeline files (identical across platforms)
  - `source/shared/rules/` -- move all 4 rule files (identical across platforms)
  - `source/shared/variants/` -- move all 4 variant files (identical across platforms)
  - `source/shared/dashboard/` -- move telemetry-bridge.sh (identical across platforms)
- **Files to modify:** None (these are moves)
- **Acceptance criteria:**
  - All non-agent, non-hook files exist in `source/shared/` with identical content to their current `source/` locations
  - Original files in `source/commands/`, `source/references/`, `source/pipeline/`, `source/rules/`, `source/variants/`, `source/dashboard/` are removed
  - `source/shared/` directory structure mirrors the original flat structure
- **Estimated complexity:** Low (file moves only, no content changes)

#### Step 1b: Split Agent Templates into Overlay + Content

For each of the 12 agent templates, separate YAML frontmatter from content body. Create platform-specific frontmatter overlays for Claude Code and Cursor.

- **Files to create:**
  - `source/shared/agents/{name}.md` -- 12 files (content body without frontmatter, with the `<!-- Part of atelier-pipeline -->` comment retained)
  - `source/claude/agents/{name}.frontmatter.yml` -- 12 files (Claude Code frontmatter, identical to current frontmatter in source/agents/*.md)
  - `source/cursor/agents/{name}.frontmatter.yml` -- 12 files (Cursor frontmatter, identical to Claude Code frontmatter for now -- Phase 2 diverges them)
- **Files to delete:**
  - `source/agents/*.md` -- 12 files (replaced by shared content + overlay)
- **Acceptance criteria:**
  - Concatenating `source/claude/agents/{name}.frontmatter.yml` + `source/shared/agents/{name}.md` produces byte-identical output to the original `source/agents/{name}.md` (with proper `---` delimiters)
  - Same for `source/cursor/agents/` (at this point, frontmatter is identical across platforms)
  - Original `source/agents/` directory is removed
  - No content drift between Claude Code and Cursor overlays (they start identical)
- **Estimated complexity:** Medium (careful extraction of frontmatter from 12 files, validation of reassembly)

#### Step 1c: Move Hook Scripts to Platform Directories

Move hook scripts into `source/claude/hooks/` and `source/cursor/hooks/`.

- **Files to create:**
  - `source/claude/hooks/` -- move all 14 hook scripts + enforcement-config.json from `source/hooks/`
  - `source/cursor/hooks/hooks.json` -- move from current location or create (Cursor uses a different hook registration format)
- **Files to delete:**
  - `source/hooks/` -- entire directory (replaced by platform-specific directories)
- **Acceptance criteria:**
  - `source/claude/hooks/` contains all 14 .sh scripts + enforcement-config.json (identical content)
  - `source/cursor/hooks/hooks.json` exists with Cursor hook registrations
  - `source/hooks/` directory no longer exists
  - All hook scripts reference the correct project root detection pattern (`CURSOR_PROJECT_DIR` / `CLAUDE_PROJECT_DIR`)
- **Estimated complexity:** Low (file moves)

#### Step 1d: Update /pipeline-setup Install Logic

Update SKILL.md to read from the new `source/shared/` + `source/{platform}/` structure. The install produces identical output to the current behavior.

- **Files to modify:**
  - `skills/pipeline-setup/SKILL.md` -- update Step 2 (Read Templates), Step 3 (Install Files), Step 3a (Install Enforcement Hooks), Step 3c (Cursor Plugin Rules Sync) to reference new paths and implement overlay assembly
  - `.cursor-plugin/skills/pipeline-setup/SKILL.md` -- mirror changes for Cursor plugin distribution
- **Acceptance criteria:**
  - /pipeline-setup reads templates from `source/shared/` + `source/claude/` (Claude Code) or `source/shared/` + `source/cursor/` (Cursor)
  - Agent installation assembles frontmatter overlay + content body into a complete `.md` file
  - Non-agent files install directly from `source/shared/`
  - Hook scripts install from `source/claude/hooks/` (Claude Code) or `source/cursor/hooks/` (Cursor)
  - Installed output is byte-identical to current behavior (no functional change)
  - Platform detection: `CURSOR_PROJECT_DIR` set -> use `source/cursor/`; otherwise -> use `source/claude/`
  - Installation manifest in SKILL.md is updated to reflect new source paths
- **Estimated complexity:** High (SKILL.md is ~600 lines; path references throughout must be updated carefully)

#### Step 1e: Update Documentation and Path References

Update CLAUDE.md source structure, README, technical reference, and test helper paths to reflect the new directory layout.

- **Files to modify:**
  - `CLAUDE.md` -- update Source Structure section
  - `README.md` -- update any source/ directory references
  - `docs/guide/technical-reference.md` -- update hook and agent template path references
  - `tests/hooks/test_helper.bash` -- update `HOOKS_DIR` to point to `source/claude/hooks/`
- **Acceptance criteria:**
  - All documentation references to `source/agents/`, `source/hooks/`, `source/commands/`, `source/references/`, `source/rules/`, `source/pipeline/`, `source/variants/` are updated to the new structure
  - `HOOKS_DIR` in test_helper.bash points to `source/claude/hooks/` (tests run against Claude Code hook scripts)
  - `bats tests/hooks/` passes (all existing 265+ tests still pass against new paths)
- **Estimated complexity:** Medium (many files reference source/ paths)

#### Step 1f: Add Phase 1 Validation Tests

Write bats tests that verify the overlay assembly produces correct output and that the directory structure is complete.

- **Files to create:**
  - `tests/hooks/source-split.bats` -- tests for overlay assembly, directory completeness, byte-identity of assembled files
- **Acceptance criteria:**
  - Test verifies each of the 12 agents assembles correctly (frontmatter + content = valid markdown with YAML frontmatter)
  - Test verifies all expected files exist in `source/shared/`, `source/claude/`, `source/cursor/`
  - Test verifies no files remain in the old flat `source/agents/`, `source/hooks/`, etc.
  - Test verifies Claude Code and Cursor frontmatter overlays both assemble successfully
  - All tests pass
- **Estimated complexity:** Medium (assembly validation logic)

---

### Phase 2: Enforcement Redesign

#### Step 2a: Create Per-Agent Enforcement Scripts

Write the 6 per-agent hook scripts that will replace the enforce-paths.sh case statement. Also write the enforce-eva-paths.sh for main thread tightening.

- **Files to create:**
  - `source/claude/hooks/enforce-roz-paths.sh` (~18 lines)
  - `source/claude/hooks/enforce-cal-paths.sh` (~15 lines)
  - `source/claude/hooks/enforce-colby-paths.sh` (~20 lines)
  - `source/claude/hooks/enforce-agatha-paths.sh` (~15 lines)
  - `source/claude/hooks/enforce-product-paths.sh` (~15 lines)
  - `source/claude/hooks/enforce-ux-paths.sh` (~15 lines)
  - `source/claude/hooks/enforce-eva-paths.sh` (~15 lines, replaces main-thread case in enforce-paths.sh)
- **Files to modify:**
  - `source/claude/hooks/enforcement-config.json` -- simplify: remove enforcement-path-specific keys (`architecture_dir`, `product_specs_dir`, `ux_docs_dir`); retain `pipeline_state_dir` (consumed by enforce-pipeline-activation.sh and enforce-sequencing.sh), `test_patterns` (consumed by enforce-roz-paths.sh), `colby_blocked_paths` (consumed by enforce-colby-paths.sh), and `test_command`
- **Acceptance criteria:**
  - Each script is self-contained: no agent_type check, no case statement, no external config read (except enforce-roz-paths.sh which needs test_patterns and enforce-colby-paths.sh which needs colby_blocked_paths)
  - Each script follows the minimal pattern: setup-mode bypass, read stdin, extract file_path, normalize path, check against allowed paths, block or allow
  - Each script exits 0 on allowed paths and exits 2 with BLOCKED message on disallowed paths
  - enforce-eva-paths.sh allows only docs/pipeline/ (not docs/product/ or docs/ux/)
  - All scripts are executable (chmod +x)
- **Estimated complexity:** Medium (7 small scripts, each following the same pattern)

#### Step 2b: Write Per-Agent Hook Tests

Write bats tests for each new per-agent enforcement script, replacing the enforce-paths.sh test coverage.

- **Files to create:**
  - `tests/hooks/enforce-roz-paths.bats`
  - `tests/hooks/enforce-cal-paths.bats`
  - `tests/hooks/enforce-colby-paths.bats`
  - `tests/hooks/enforce-agatha-paths.bats`
  - `tests/hooks/enforce-product-paths.bats`
  - `tests/hooks/enforce-ux-paths.bats`
  - `tests/hooks/enforce-eva-paths.bats`
- **Acceptance criteria:**
  - Each test file covers: allowed paths (happy), blocked paths (failure), edge cases (boundary: absolute paths, empty paths, setup-mode bypass)
  - Combined @test count across all 7 files >= 56 (replaces enforce-paths.bats 16 tests with per-agent specifics including all 14 colby prefixes, jq-missing, exit-fast, setup-mode bypass)
  - All tests pass against the new per-agent scripts
  - Tests use existing test_helper.bash patterns (setup/teardown, JSON input builders)
- **Estimated complexity:** Medium (7 test files, each following existing test patterns)

#### Step 2c: Create Robert-spec and Sable-ux Persona Files

Create the write-capable producer variants for Robert and Sable.

- **Files to create:**
  - `source/shared/agents/robert-spec.md` -- Robert producer persona content (writes specs to docs/product/)
  - `source/shared/agents/sable-ux.md` -- Sable producer persona content (writes UX docs to docs/ux/)
  - `source/claude/agents/robert-spec.frontmatter.yml` -- Claude Code frontmatter with tools + hooks
  - `source/claude/agents/sable-ux.frontmatter.yml` -- Claude Code frontmatter with tools + hooks
  - `source/cursor/agents/robert-spec.frontmatter.yml` -- Cursor frontmatter (tools, no hooks)
  - `source/cursor/agents/sable-ux.frontmatter.yml` -- Cursor frontmatter (tools, no hooks)
- **Files to modify:**
  - `source/shared/rules/agent-system.md` -- update core agent constant, add robert-spec and sable-ux to subagent table, update routing table for /pm and /ux
  - `skills/pipeline-setup/SKILL.md` -- add robert-spec.md and sable-ux.md to installation manifest
- **Acceptance criteria:**
  - robert-spec.md has a producer-focused identity ("Your job is to write product specs") with write access to docs/product/
  - sable-ux.md has a producer-focused identity ("Your job is to write UX design docs") with write access to docs/ux/
  - Both inherit the Robert/Sable domain expertise (product/UX knowledge) but with write-focused workflows
  - Core agent constant in agent-system.md lists all 11 core agents
  - Installation manifest includes both new files
  - /pm routing changed to subagent invocation of robert-spec
  - /ux routing changed to subagent invocation of sable-ux
- **Estimated complexity:** High (new persona content, routing changes, manifest updates)

#### Step 2d: Add permissionMode to Write-Heavy Agent Overlays

Add `permissionMode: acceptEdits` to Claude Code frontmatter overlays for Colby, Cal, Agatha, and Ellis.

- **Files to modify:**
  - `source/claude/agents/colby.frontmatter.yml` -- add `permissionMode: acceptEdits`
  - `source/claude/agents/cal.frontmatter.yml` -- add `permissionMode: acceptEdits`
  - `source/claude/agents/agatha.frontmatter.yml` -- add `permissionMode: acceptEdits`
  - `source/claude/agents/ellis.frontmatter.yml` -- add `permissionMode: acceptEdits`
- **Acceptance criteria:**
  - Only Claude Code overlays get permissionMode (Cursor overlays unchanged)
  - permissionMode is `acceptEdits` (not `plan` -- plan blocks Bash)
  - PreToolUse hooks still fire regardless of permissionMode (verified by existing hook tests)
  - No permissionMode on read-only agents (they do not need it and it would be misleading)
- **Estimated complexity:** Low (4 one-line additions to YAML files)

#### Step 2e: Wire Frontmatter Hooks into Agent Overlays + Delete Monolith

Add per-agent `hooks:` field to Claude Code frontmatter overlays. Delete enforce-paths.sh from Claude Code hooks. Update settings.json registration.

- **Files to modify:**
  - `source/claude/agents/roz.frontmatter.yml` -- add hooks field referencing enforce-roz-paths.sh
  - `source/claude/agents/cal.frontmatter.yml` -- add hooks field referencing enforce-cal-paths.sh
  - `source/claude/agents/colby.frontmatter.yml` -- add hooks field referencing enforce-colby-paths.sh
  - `source/claude/agents/agatha.frontmatter.yml` -- add hooks field referencing enforce-agatha-paths.sh
  - `source/claude/agents/robert-spec.frontmatter.yml` -- add hooks field referencing enforce-product-paths.sh
  - `source/claude/agents/sable-ux.frontmatter.yml` -- add hooks field referencing enforce-ux-paths.sh
  - `skills/pipeline-setup/SKILL.md` -- update settings.json hook registration to replace enforce-paths.sh with enforce-eva-paths.sh for main thread; add new per-agent hook scripts to installation manifest
  - `.cursor-plugin/skills/pipeline-setup/SKILL.md` -- mirror changes (Cursor still installs enforce-paths.sh from source/cursor/hooks/)
- **Files to delete:**
  - `source/claude/hooks/enforce-paths.sh` -- replaced by per-agent hooks (Cursor copy in `source/cursor/hooks/` retained)
- **Acceptance criteria:**
  - Each write-capable agent's Claude Code frontmatter has a `hooks:` field with the correct event matcher and script path
  - settings.json PreToolUse registration for Write|Edit|MultiEdit points to enforce-eva-paths.sh (main thread only) instead of enforce-paths.sh
  - enforce-paths.sh no longer exists in source/claude/hooks/
  - enforce-paths.sh still exists in source/cursor/hooks/ for Cursor platform
  - New per-agent hook scripts are in the installation manifest
  - Cursor hooks.json unchanged (still references enforce-paths.sh)
- **Estimated complexity:** High (coordination across 8+ files, deletion of a core script)

#### Step 2f: Update Eva Routing + Documentation

Update Eva's routing rules, command definitions, and all documentation to reflect the new enforcement model and Robert-spec/Sable-ux subagents.

- **Files to modify:**
  - `source/shared/rules/default-persona.md` -- update Eva's forbidden actions: remove docs/product/ and docs/ux/ from main thread write access
  - `source/shared/commands/pm.md` -- note that /pm now triggers robert-spec subagent invocation
  - `source/shared/commands/ux.md` -- note that /ux now triggers sable-ux subagent invocation
  - `source/shared/commands/create-agent.md` -- update enforce-paths.sh reference to per-agent hook pattern
  - `docs/guide/technical-reference.md` -- update enforcement architecture section
  - `docs/guide/user-guide.md` -- update agent descriptions if Robert/Sable dual-mode is mentioned
  - `CLAUDE.md` -- update agent count and conventions if needed
- **Acceptance criteria:**
  - Eva's forbidden actions gate lists docs/pipeline/ as the only main-thread write path
  - /pm command documentation reflects subagent invocation pattern
  - /ux command documentation reflects subagent invocation pattern
  - create-agent.md references the per-agent hook pattern (not enforce-paths.sh)
  - Technical reference describes the three-layer enforcement pyramid
  - All references to enforce-paths.sh in documentation are updated to describe the new model
- **Estimated complexity:** Medium (documentation updates across multiple files)

#### Step 2g: Delete Legacy Test File + Final Verification

Remove the enforce-paths.bats test file (replaced by per-agent test files from Step 2b) and run the full test suite.

- **Files to delete:**
  - `tests/hooks/enforce-paths.bats` -- replaced by per-agent test files
- **Files to modify:**
  - `tests/hooks/doc-sync.bats` -- update any references to enforce-paths.sh or source/hooks/ paths
  - `tests/hooks/if-conditionals.bats` -- update any references to enforce-paths.sh
- **Acceptance criteria:**
  - enforce-paths.bats is deleted
  - All remaining test files that referenced enforce-paths.sh or old source/ paths are updated
  - `bats tests/hooks/` passes (full test suite green)
  - No references to `source/hooks/` remain in the codebase (all updated to `source/claude/hooks/` or `source/cursor/hooks/` or `source/shared/`)
  - No references to enforce-paths.sh remain in Claude Code paths (only in Cursor paths and this ADR)
- **Estimated complexity:** Medium (cross-referencing all test files for path updates)

#### Step 2h: Wave-Boundary Compaction Advisory Hook

Create a SubagentStop prompt hook that detects wave-boundary moments (Ellis completing a per-wave commit) and injects an advisory telling Eva to suggest `/compact` to the user before starting the next wave. This addresses context quality degradation in long pipeline sessions -- nothing currently triggers compaction proactively; the existing PreCompact/PostCompact hooks handle what happens IF compaction fires, but nothing tells Eva to recommend `/compact` at the right time.

Wave boundaries are the ideal trigger because: all units are built, QA'd, and committed by Ellis; pipeline state is fully persisted (pipeline-state.md, brain, git); the PostCompact hook already handles recovery; and Eva starts the next wave with clean context.

- **Files to create:**
  - `source/hooks/prompt-compact-advisory.sh` -- SubagentStop prompt hook (~25-30 lines). Claude Code only (Cursor has no SubagentStop prompt hooks)
- **Files to modify:**
  - `source/references/pipeline-operations.md` -- add wave-boundary compact advisory bullet to the Compaction Strategy subsection within `<section id="context-hygiene">`
  - `skills/pipeline-setup/SKILL.md` -- add prompt-compact-advisory.sh to the hook source table AND add the prompt hook entry to the SubagentStop section of the settings.json template
- **Acceptance criteria:**
  - Script is a SubagentStop prompt hook (`"type": "prompt"`) with `"if": "agent_type == 'ellis'"` conditional so it only fires when Ellis completes
  - Script reads pipeline-state.md to check for PIPELINE_STATUS marker (pipeline must be active)
  - Script extracts the `phase` field from the PIPELINE_STATUS JSON marker
  - Script outputs advisory text ONLY when phase is `build` or `implement` (per-wave commit = suggest compact). When phase is `review`, `complete`, `idle`, or absent, the script outputs nothing (final commit or non-pipeline session = no advisory)
  - Advisory text output to stdout: `WAVE BOUNDARY: Ellis completed a per-wave commit. Pipeline state is fully persisted. Before starting the next wave, suggest to the user: "This is a good moment to run /compact -- wave state is saved and the next wave will start with cleaner context." Do not auto-compact; this is the user's decision.`
  - Script exits 0 always (purely advisory, never blocks)
  - Script is lightweight: no brain calls, no test runs, no subagent invocations. Only reads pipeline-state.md (one file read). Retro lesson #003 compliant
  - Script uses `$CLAUDE_PROJECT_DIR` (with fallback to `$CURSOR_PROJECT_DIR` then `$PWD`) to locate pipeline-state.md, consistent with pre-compact.sh and post-compact-reinject.sh patterns
  - Script gracefully degrades: exits 0 silently if pipeline-state.md does not exist, if jq is unavailable, if PIPELINE_STATUS marker is absent, or if stdin is empty
  - SKILL.md hook source table includes `source/hooks/prompt-compact-advisory.sh` with destination `.claude/hooks/prompt-compact-advisory.sh` and purpose description
  - SKILL.md settings.json template SubagentStop section includes the prompt hook entry: `{"type": "prompt", "prompt": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/prompt-compact-advisory.sh", "if": "agent_type == 'ellis'"}`
  - pipeline-operations.md Compaction Strategy subsection includes a new bullet: "**Wave-boundary compact advisory.** A SubagentStop prompt hook (`prompt-compact-advisory.sh`) detects when Ellis completes a per-wave commit during the build phase and advises Eva to suggest `/compact` to the user. This is purely advisory -- Eva relays the suggestion; the user decides. The advisory does not fire on the final commit (review/complete phase) because the pipeline is ending."
- **Estimated complexity:** Low (lightweight prompt hook following established patterns in prompt-brain-capture.sh)

---

## Comprehensive Test Specification

### Step 1a Tests (Shared Content Directory)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-001 | Happy | `source/shared/commands/` contains all 11 command files with content identical to original `source/commands/` |
| T-0022-002 | Happy | `source/shared/references/` contains all 10 reference files with content identical to original `source/references/` |
| T-0022-003 | Happy | `source/shared/pipeline/` contains all 6 pipeline files with content identical to original `source/pipeline/` |
| T-0022-004 | Happy | `source/shared/rules/` contains all 4 rule files with content identical to original `source/rules/` |
| T-0022-005 | Happy | `source/shared/variants/` contains all 4 variant files with content identical to original `source/variants/` |
| T-0022-006 | Happy | `source/shared/dashboard/telemetry-bridge.sh` exists with content identical to original `source/dashboard/telemetry-bridge.sh` |
| T-0022-007 | Boundary | Original `source/commands/`, `source/references/`, `source/pipeline/`, `source/rules/`, `source/variants/`, `source/dashboard/` directories no longer exist |
| T-0022-008 | Regression | `{config_dir}` placeholder appears in shared files where expected (not prematurely resolved); `{platform}` placeholder does NOT appear in any `source/shared/` file |
| T-0022-009 | Structural | No file in the entire `source/shared/` tree starts with a YAML frontmatter block (`---` on line 1). Assertion: `grep -rl "^---" source/shared/` returns zero results. Covers commands/, references/, rules/, pipeline/, variants/, dashboard/, and agents/ |

### Step 1a Telemetry

Telemetry: directory existence check for `source/shared/`. Trigger: /pipeline-setup reads templates. Absence means: source split incomplete, install will fail.

### Step 1b Tests (Agent Template Split)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-010 | Happy | Parametric over all 12 agents (cal, colby, roz, robert, sable, ellis, agatha, investigator, distillator, sentinel, darwin, deps): concatenating `source/claude/agents/{name}.frontmatter.yml` + `source/shared/agents/{name}.md` (with `---\n` + frontmatter + `---\n` + content structure) produces output matching the original `source/agents/{name}.md` byte-for-byte. Each agent MUST be tested explicitly or via parametric loop -- testing one agent is insufficient |
| T-0022-010a | Boundary | Assembly output has exactly `---\n{frontmatter}\n---\n{content}` structure: frontmatter block ends with a trailing newline before the closing `---`. Missing newline produces invalid YAML. Verify for at least 3 agents spanning different frontmatter sizes (one minimal, one with hooks, one with mcpServers) |
| T-0022-011 | Happy | Parametric over all 12 agents: concatenating `source/cursor/agents/{name}.frontmatter.yml` + `source/shared/agents/{name}.md` (with `---` delimiters) produces valid markdown with YAML frontmatter |
| T-0022-012 | Happy | Each `source/shared/agents/{name}.md` begins with `<!-- Part of atelier-pipeline` comment (no `---` YAML delimiter before it) |
| T-0022-013 | Boundary | Each `.frontmatter.yml` file is valid YAML (parseable by `yq` or equivalent) |
| T-0022-014 | Boundary | Each `.frontmatter.yml` file contains a `name:` field matching the agent's expected name |
| T-0022-015 | Failure | Original `source/agents/` directory no longer exists |
| T-0022-016 | Regression | All 12 Claude Code frontmatter files have `name`, `description`, `model`, `effort`, `maxTurns` fields (Wave 1 fields preserved) |
| T-0022-017 | Regression | Agents with `tools:` field in current frontmatter (cal, colby) retain it in Claude Code overlay |
| T-0022-018 | Regression | Agents with `disallowedTools:` field retain it in Claude Code overlay |
| T-0022-019 | Regression | Agents with `mcpServers:` field retain it in Claude Code overlay |
| T-0022-020 | Boundary | Cursor frontmatter overlays are identical to Claude Code overlays at this point (divergence comes in Phase 2) |

### Step 1b Telemetry

Telemetry: assembly validation count. Trigger: test runner verifies all 12 agents assemble correctly. Absence means: overlay pattern has a structural defect.

### Step 1c Tests (Hook Script Move)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-021 | Happy | `source/claude/hooks/` contains all 14 .sh scripts + enforcement-config.json |
| T-0022-022 | Happy | `source/cursor/hooks/hooks.json` exists with valid JSON content |
| T-0022-023 | Boundary | Original `source/hooks/` directory no longer exists |
| T-0022-024 | Regression | Each hook script in `source/claude/hooks/` is byte-identical to the original in `source/hooks/` |
| T-0022-025 | Regression | All hook scripts contain `CURSOR_PROJECT_DIR` fallback pattern (dual-IDE compatibility preserved) |
| T-0022-025a | Mechanical | All `.sh` scripts in `source/claude/hooks/` have executable permissions (`-x` bit set). Assertion: `find source/claude/hooks/ -name "*.sh" ! -perm -u+x` returns zero results |
| T-0022-025b | Boundary | Every script path referenced in `source/cursor/hooks/hooks.json` exists as an actual file in `source/cursor/hooks/`. No orphan references (a hooks.json reference to a non-existent script fails silently on Cursor) |

### Step 1c Telemetry

Telemetry: hook script count in `source/claude/hooks/`. Trigger: file listing. Absence means: incomplete hook migration.

### Step 1d Tests (Pipeline-Setup Update)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-030 | Happy | Grep SKILL.md for `source/shared/` in Step 2 (template reading) -- at least one match. This is a documentation-level spec verifying SKILL.md instructions reference the new path; behavioral verification is covered by T-0022-033a through T-0022-033d |
| T-0022-031 | Happy | Grep SKILL.md for lines containing both `source/shared/` and `.claude/` in Step 3 (installation manifest) -- at least one match. Documentation-level spec; installed-file behavioral verification is T-0022-034a |
| T-0022-032 | Happy | Grep SKILL.md for `frontmatter` AND `content` (or `overlay` AND `assembly`) -- at least one match confirming the overlay assembly procedure is documented. Documentation-level spec |
| T-0022-033 | Boundary | SKILL.md platform detection uses `CURSOR_PROJECT_DIR` env var to choose `source/cursor/` vs `source/claude/`. Grep SKILL.md for `CURSOR_PROJECT_DIR` -- present |
| T-0022-033a | Happy (SPOF) | When `CURSOR_PROJECT_DIR` is unset: assembled agents use `source/claude/` overlays and installed files contain the `hooks:` frontmatter field (Claude Code enforcement active) |
| T-0022-033b | Happy (SPOF) | When `CURSOR_PROJECT_DIR` is set: assembled agents use `source/cursor/` overlays and installed files do NOT contain the `hooks:` frontmatter field (Cursor has no frontmatter hook support) |
| T-0022-033c | Boundary (SPOF) | When both `CURSOR_PROJECT_DIR` and `CLAUDE_PROJECT_DIR` are set: `CURSOR_PROJECT_DIR` takes precedence (Cursor overlay used). Document which env var wins the precedence check in SKILL.md |
| T-0022-033d | Boundary (SPOF) | Installed Claude Code agents in `.claude/agents/` have `hooks:` field in assembled frontmatter; installed Cursor agents in `.cursor/agents/` do not |
| T-0022-034 | Failure | When a `.frontmatter.yml` overlay file is missing for an agent: the assembler MUST error and halt installation with a clear message ("Missing overlay for {agent} on {platform}"). It must NOT silently skip the agent or install without frontmatter -- silent skip is the SPOF failure mode (enforcement disappears). SKILL.md documents this error-and-halt behavior |
| T-0022-034a | Boundary | /pipeline-setup assembly of each installed agent file in `.claude/agents/` produces output byte-identical to the source assembly (`source/claude/agents/{name}.frontmatter.yml` + `source/shared/agents/{name}.md`). Verifies the install step does not corrupt or modify content |
| T-0022-035 | Regression | SKILL.md installation manifest total file count matches current (40 mandatory + conditionals) |
| T-0022-036 | Regression | SKILL.md Step 3c Cursor sync still references correct source paths |
| T-0022-037 | Regression | Cursor plugin's SKILL.md mirrors the path changes |

### Step 1d Telemetry

Telemetry: /pipeline-setup install success rate. Trigger: user runs /pipeline-setup after upgrade. Absence means: install path regression.

### Step 1e Tests (Documentation Updates)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-040 | Happy | CLAUDE.md Source Structure section reflects `source/shared/`, `source/claude/`, `source/cursor/` directories |
| T-0022-041 | Happy | `tests/hooks/test_helper.bash` `HOOKS_DIR` points to `source/claude/hooks/` |
| T-0022-042 | Regression | `bats tests/hooks/` full suite passes (all 265+ existing tests green) |
| T-0022-043 | Regression | No references to `source/agents/` (flat, non-shared) remain in documentation |
| T-0022-044 | Regression | No references to `source/hooks/` (flat) remain in documentation or test infrastructure |
| T-0022-045 | Happy | `README.md` source/ directory references are updated to reflect `source/shared/`, `source/claude/`, `source/cursor/` structure. Grep README.md for old flat paths (`source/agents/`, `source/hooks/`, `source/commands/`, `source/references/`) -- zero matches |

### Step 1e Telemetry

Telemetry: test suite pass count. Trigger: `bats tests/hooks/` execution. Absence means: path update incomplete causing test failures.

### Step 1f Tests (Phase 1 Validation)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-050 | Happy | Validation test assembles each of 12 Claude Code agents and verifies valid YAML frontmatter in output |
| T-0022-051 | Happy | Validation test assembles each of 12 Cursor agents and verifies valid YAML frontmatter in output |
| T-0022-052 | Happy | Validation test verifies all expected directories exist: `source/shared/{agents,commands,references,pipeline,rules,variants,dashboard}`, `source/claude/{agents,hooks}`, `source/cursor/{agents,hooks}` |
| T-0022-053 | Failure | Validation test verifies no files remain in deprecated paths: `source/agents/`, `source/hooks/`, `source/commands/`, `source/references/`, `source/pipeline/`, `source/rules/`, `source/variants/`, `source/dashboard/` |
| T-0022-054 | Boundary | Validation test verifies frontmatter overlay files have no `---` delimiters (raw YAML, not wrapped) |
| T-0022-055 | Boundary | Validation test verifies shared content files have no `---` YAML frontmatter block at the top |
| T-0022-056 | Security | Validation test verifies no `.frontmatter.yml` file contains shell command injection patterns. Specifically checks for: `$(` (command substitution), backtick `` ` `` (legacy command substitution), `eval ` (eval invocation), `exec ` (exec invocation), `!!` (history expansion). Assertion: grep for these patterns across all `.frontmatter.yml` files returns zero results |
| T-0022-057 | Boundary | Total file count in `source/` after the split equals expected count: original file count minus deleted files plus new overlay/frontmatter files. A silent deletion during the move is detected by this assertion |
| T-0022-058 | Happy | Validation test assembles robert-spec and sable-ux (Phase 2 new agents) and verifies: (a) assembled output has valid `---` YAML frontmatter structure, (b) frontmatter contains required fields (name, description, model, tools), (c) content body is non-empty. No byte-identity check (no original exists for these agents) |

### Step 1f Telemetry

Telemetry: source-split.bats test count and pass rate. Trigger: test execution. Absence means: validation tests were not written or all fail.

### Step 2a Tests (Per-Agent Enforcement Scripts)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-060 | Happy | enforce-cal-paths.sh allows writing to `docs/architecture/ADR-0022-test.md` |
| T-0022-061 | Failure | enforce-cal-paths.sh blocks writing to `src/main.ts` with exit code 2 and BLOCKED message |
| T-0022-062 | Failure | enforce-cal-paths.sh blocks writing to `docs/product/spec.md` with exit code 2 |
| T-0022-063 | Happy | enforce-roz-paths.sh allows writing to `tests/hooks/new-test.bats` (matches test_patterns) |
| T-0022-064 | Happy | enforce-roz-paths.sh allows writing to `docs/pipeline/last-qa-report.md` |
| T-0022-065 | Failure | enforce-roz-paths.sh blocks writing to `src/main.ts` with exit code 2 |
| T-0022-066 | Happy | enforce-colby-paths.sh allows writing to `src/features/auth/login.ts` |
| T-0022-067 | Failure | enforce-colby-paths.sh blocks writing to `docs/guide/user-guide.md` (docs/ is colby_blocked) |
| T-0022-068 | Failure | enforce-colby-paths.sh blocks writing to `.github/workflows/ci.yml` |
| T-0022-069 | Happy | enforce-agatha-paths.sh allows writing to `docs/guide/technical-reference.md` |
| T-0022-070 | Failure | enforce-agatha-paths.sh blocks writing to `src/main.ts` |
| T-0022-071 | Happy | enforce-product-paths.sh allows writing to `docs/product/feature-spec.md` |
| T-0022-072 | Failure | enforce-product-paths.sh blocks writing to `docs/ux/design.md` |
| T-0022-073 | Failure | enforce-product-paths.sh blocks writing to `src/main.ts` |
| T-0022-074 | Happy | enforce-ux-paths.sh allows writing to `docs/ux/feature-design.md` |
| T-0022-075 | Failure | enforce-ux-paths.sh blocks writing to `docs/product/spec.md` |
| T-0022-076 | Failure | enforce-ux-paths.sh blocks writing to `src/main.ts` |
| T-0022-077 | Happy | enforce-eva-paths.sh allows writing to `docs/pipeline/pipeline-state.md` |
| T-0022-078 | Failure | enforce-eva-paths.sh blocks writing to `docs/product/spec.md` (tightened from current) |
| T-0022-079 | Failure | enforce-eva-paths.sh blocks writing to `docs/ux/design.md` (tightened from current) |
| T-0022-080 | Boundary | Parametric over all 7 scripts (enforce-roz-paths.sh, enforce-cal-paths.sh, enforce-colby-paths.sh, enforce-agatha-paths.sh, enforce-product-paths.sh, enforce-ux-paths.sh, enforce-eva-paths.sh): each exits 0 when `ATELIER_SETUP_MODE=1` is set |
| T-0022-081 | Boundary | Parametric over all 7 scripts: each exits 0 when `docs/pipeline/.setup-mode` file exists in the project root |
| T-0022-082 | Boundary | Parametric over all 7 scripts: each exits 0 when `file_path` is empty or absent in the JSON input |
| T-0022-083 | Boundary | enforce-colby-paths.sh correctly normalizes absolute paths to project-relative |
| T-0022-084 | Failure | enforce-colby-paths.sh blocks paths outside the project root (absolute paths not under PROJECT_ROOT) |
| T-0022-085 | Boundary | enforce-roz-paths.sh reads test_patterns from enforcement-config.json in the same directory |
| T-0022-086 | Boundary | enforce-colby-paths.sh reads colby_blocked_paths from enforcement-config.json in the same directory |
| T-0022-087 | Error | Each script outputs a clear error message to stderr when blocking, including the attempted path |
| T-0022-087a | Boundary (Lesson #003) | All 7 scripts (enforce-roz-paths.sh, enforce-cal-paths.sh, enforce-colby-paths.sh, enforce-agatha-paths.sh, enforce-product-paths.sh, enforce-ux-paths.sh, enforce-eva-paths.sh) exit 0 immediately when `tool_name` is `Read` with a non-empty `file_path`. Per-agent hooks must exit-fast on non-enforcement paths to avoid blocking. Parametric over all 7 scripts |
| T-0022-087b | Structural | Post-2a `enforcement-config.json` contains keys: `pipeline_state_dir`, `test_patterns`, `colby_blocked_paths`, `test_command`. Does NOT contain removed keys: `architecture_dir`, `product_specs_dir`, `ux_docs_dir`. The `pipeline_state_dir` key MUST be retained -- it is consumed by `enforce-pipeline-activation.sh` and `enforce-sequencing.sh` (not part of this redesign) |
| T-0022-087c | Failure | enforce-roz-paths.sh exits 2 with stderr containing "jq" when jq is not available on PATH. Mirrors T-0003-019 behavior for the per-agent script that reads enforcement-config.json via jq |
| T-0022-087d | Failure | enforce-colby-paths.sh exits 2 with stderr containing "jq" when jq is not available on PATH. Mirrors T-0003-019 behavior for the per-agent script that reads enforcement-config.json via jq |
| T-0022-087e | Failure | enforce-eva-paths.sh blocks writing to `docs/architecture/ADR-0022.md` (Eva should not write architecture files) |
| T-0022-087f | Failure | enforce-eva-paths.sh blocks writing to `src/main.ts` (Eva should not write source files) |

### Step 2a Telemetry

Telemetry: per-agent hook execution count in session telemetry JSONL. Trigger: any write operation by a write-capable agent. Absence means: frontmatter hook is not firing (registration or wiring issue).

### Step 2b Tests (Per-Agent Hook Test Files)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-090 | Happy | enforce-roz-paths.bats has tests for: test file patterns (.test., .spec., /tests/, /__tests__/, /test_, _test., conftest), docs/pipeline/ access, blocked non-test paths |
| T-0022-091 | Happy | enforce-cal-paths.bats has tests for: docs/architecture/ access, blocked non-architecture paths |
| T-0022-092 | Happy | enforce-colby-paths.bats has tests for: allowed source paths, and explicit test cases for all 14 `colby_blocked_paths` prefixes: `docs/`, `.github/`, `.gitlab-ci`, `.circleci/`, `Jenkinsfile`, `Dockerfile`, `docker-compose`, `.gitlab/`, `deploy/`, `infra/`, `terraform/`, `pulumi/`, `k8s/`, `kubernetes/`. Each prefix must have at least one test asserting exit 2 with BLOCKED |
| T-0022-093 | Happy | enforce-agatha-paths.bats has tests for: docs/ access (any subpath), blocked non-docs paths |
| T-0022-094 | Happy | enforce-product-paths.bats has tests for: docs/product/ access, blocked other docs paths, blocked source paths |
| T-0022-095 | Happy | enforce-ux-paths.bats has tests for: docs/ux/ access, blocked other docs paths, blocked source paths |
| T-0022-096 | Happy | enforce-eva-paths.bats has tests for: docs/pipeline/ access, blocked docs/product/ (tightened), blocked docs/ux/ (tightened) |
| T-0022-097 | Regression | Combined `@test` declaration count across all 7 new per-agent test files (`enforce-{roz,cal,colby,agatha,product,ux,eva}-paths.bats`) is >= 56. Rationale: enforce-paths.bats has 16 tests covering 7 agents; 7 dedicated files with per-agent specifics (14 colby prefixes, 7 test_patterns, jq-missing, exit-fast, setup-mode bypass) require at minimum 56 tests to maintain equivalent coverage. Assertion: `grep -c '@test' tests/hooks/enforce-*-paths.bats | awk -F: '{sum += $2} END {print sum}'` >= 56 |
| T-0022-098 | Regression | All 7 new test files contain `load test_helper` as a non-comment line before the first `@test` declaration. Assertion: for each file, grep for `^load test_helper` returns a match |

### Step 2b Telemetry

Telemetry: per-agent test file count and pass rate. Trigger: `bats tests/hooks/enforce-*-paths.bats`. Absence means: test coverage gap.

### Step 2c Tests (Robert-spec and Sable-ux)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-100 | Happy | `source/shared/agents/robert-spec.md` exists AND contains producer workflow strings (at least one of: "writes to docs/product/", "spec writing", "discovery") AND does NOT contain reviewer-specific strings ("DRIFT", "AMBIGUOUS", "acceptance criteria verdict") |
| T-0022-101 | Happy | `source/shared/agents/sable-ux.md` exists AND contains producer workflow strings (at least one of: "writes to docs/ux/", "design doc", "user flow") AND does NOT contain reviewer-specific strings ("DRIFT", "MISSING", "acceptance criteria verdict") |
| T-0022-102 | Happy | `source/claude/agents/robert-spec.frontmatter.yml` has `tools: Read, Write, Edit, Glob, Grep, Bash` and hooks referencing enforce-product-paths.sh |
| T-0022-103 | Happy | `source/claude/agents/sable-ux.frontmatter.yml` has `tools: Read, Write, Edit, Glob, Grep, Bash` and hooks referencing enforce-ux-paths.sh |
| T-0022-104 | Happy | `source/cursor/agents/robert-spec.frontmatter.yml` has `tools:` field but no `hooks:` field |
| T-0022-105 | Happy | `source/cursor/agents/sable-ux.frontmatter.yml` has `tools:` field but no `hooks:` field |
| T-0022-106 | Happy | agent-system.md core agent constant includes `robert-spec` and `sable-ux` |
| T-0022-107 | Happy | agent-system.md subagent table includes Robert-spec and Sable-ux with correct tools |
| T-0022-108 | Happy | SKILL.md installation manifest includes robert-spec.md and sable-ux.md |
| T-0022-109 | Boundary | robert-spec.md has a `name: robert-spec` field (not `name: robert`) to avoid agent_type collision |
| T-0022-110 | Boundary | sable-ux.md has a `name: sable-ux` field (not `name: sable`) |
| T-0022-111 | Regression | Existing robert.md (reviewer) is unchanged -- still read-only with disallowedTools |
| T-0022-112 | Regression | Existing sable.md (reviewer) is unchanged -- still read-only with disallowedTools |
| T-0022-113 | Happy | agent-system.md contains `robert-spec` in the routing table row that handles `/pm` intent. Assertion: grep agent-system.md for a line containing both `/pm` and `robert-spec` -- match found (documentation-level spec; LLM routing behavior is not verifiable in bats) |
| T-0022-114 | Happy | agent-system.md contains `sable-ux` in the routing table row that handles `/ux` intent. Assertion: grep agent-system.md for a line containing both `/ux` and `sable-ux` -- match found (documentation-level spec) |
| T-0022-115 | Security | robert-spec persona content does NOT reference Roz QA reports (`last-qa-report.md`) or the current pipeline's ADR. It MAY reference prior specs in `docs/product/` and prior ADRs for consistency -- the information asymmetry constraint applies only to the reviewer variant (robert.md), not the producer variant. Domain decision: a spec writer needs prior specs and architectural context to write good specs; isolation is for preventing anchoring during review, which does not apply to production |
| T-0022-116 | Security | sable-ux persona content does NOT reference product specs (`docs/product/`) or Roz QA reports. It MAY reference prior UX docs in `docs/ux/` for design consistency. The information asymmetry constraint applies only to the reviewer variant (sable.md), not the producer variant |

### Step 2c Telemetry

Telemetry: robert-spec and sable-ux invocation count. Trigger: Eva routes /pm or /ux. Absence means: routing not wired or new agents not installed.

### Step 2d Tests (permissionMode)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-120 | Happy | `source/claude/agents/colby.frontmatter.yml` contains `permissionMode: acceptEdits` |
| T-0022-121 | Happy | `source/claude/agents/cal.frontmatter.yml` contains `permissionMode: acceptEdits` |
| T-0022-122 | Happy | `source/claude/agents/agatha.frontmatter.yml` contains `permissionMode: acceptEdits` |
| T-0022-123 | Happy | `source/claude/agents/ellis.frontmatter.yml` contains `permissionMode: acceptEdits` |
| T-0022-124 | Boundary | No Cursor frontmatter overlay contains `permissionMode` (Cursor ignores it) |
| T-0022-125 | Boundary | None of the 7 read-only agent Claude Code frontmatter overlays contain `permissionMode`. The 7 read-only agents are: robert (reviewer), sable (reviewer), investigator, distillator, sentinel, darwin, deps. Parametric check over all 7 |
| T-0022-126 | Regression | robert-spec and sable-ux do NOT get permissionMode (they are not write-heavy in the same way -- they write docs, not code, and user review is desirable) |

### Step 2d Telemetry

Telemetry: permissionMode field presence in installed agent files. Trigger: /pipeline-setup verification. Absence means: permissionMode not applied.

### Step 2e Tests (Frontmatter Hooks Wiring + Monolith Deletion)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-130 | Happy | `source/claude/agents/roz.frontmatter.yml` has `hooks:` field with event `PreToolUse`, matcher `Write`, and command referencing `enforce-roz-paths.sh`. Verify both the `command:` value AND the `matcher:` value |
| T-0022-131 | Happy | `source/claude/agents/cal.frontmatter.yml` has `hooks:` field with event `PreToolUse`, matcher `Write\|Edit`, and command referencing `enforce-cal-paths.sh`. Verify both `command:` and `matcher:` |
| T-0022-132 | Happy | `source/claude/agents/colby.frontmatter.yml` has `hooks:` field with event `PreToolUse`, matcher `Write\|Edit\|MultiEdit`, and command referencing `enforce-colby-paths.sh`. Verify both `command:` and `matcher:` |
| T-0022-133 | Happy | `source/claude/agents/agatha.frontmatter.yml` has `hooks:` field with event `PreToolUse`, matcher `Write\|Edit\|MultiEdit`, and command referencing `enforce-agatha-paths.sh`. Verify both `command:` and `matcher:` |
| T-0022-134 | Happy | `source/claude/agents/robert-spec.frontmatter.yml` has `hooks:` field with event `PreToolUse`, matcher `Write\|Edit`, and command referencing `enforce-product-paths.sh`. Verify both `command:` and `matcher:` |
| T-0022-135 | Happy | `source/claude/agents/sable-ux.frontmatter.yml` has `hooks:` field with event `PreToolUse`, matcher `Write\|Edit`, and command referencing `enforce-ux-paths.sh`. Verify both `command:` and `matcher:` |
| T-0022-136 | Happy | `source/claude/hooks/enforce-paths.sh` does not exist (deleted) |
| T-0022-137 | Happy | `source/cursor/hooks/enforce-paths.sh` still exists (retained for Cursor) |
| T-0022-137a | Regression | `source/cursor/hooks/enforce-paths.sh` is byte-identical to the pre-deletion Claude Code copy of `source/claude/hooks/enforce-paths.sh`. Verify content match before the Claude Code copy is deleted (ADR Note 10). The Cursor copy must be self-contained |
| T-0022-138 | Happy | SKILL.md settings.json template replaces enforce-paths.sh with enforce-eva-paths.sh for main thread. The entry has event `PreToolUse`, matcher `Write\|Edit\|MultiEdit`, and command referencing `enforce-eva-paths.sh` |
| T-0022-139 | Happy | SKILL.md settings.json template no longer has Write\|Edit\|MultiEdit -> enforce-paths.sh entry |
| T-0022-140 | Happy | SKILL.md installation manifest includes all 7 new per-agent hook scripts |
| T-0022-141 | Boundary | No Claude Code agent frontmatter overlay references enforce-paths.sh (only per-agent scripts) |
| T-0022-142 | Boundary | Cursor hooks.json still references enforce-paths.sh |
| T-0022-143 | Regression | settings.json still has enforce-sequencing.sh, enforce-pipeline-activation.sh, enforce-git.sh entries (unchanged) |
| T-0022-144 | Regression | settings.json still has all lifecycle/telemetry hooks (unchanged) |
| T-0022-145 | Security | Ellis frontmatter has NO `hooks:` field (full write access, no path enforcement at Layer 2) |

### Step 2e Telemetry

Telemetry: enforce-paths.sh absence in Claude Code installs. Trigger: /pipeline-setup completes. Absence means: monolith not deleted, old enforcement still active.

### Step 2f Tests (Eva Routing + Documentation)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-150 | Happy | default-persona.md contains text restricting Eva to `docs/pipeline/` writes. Assertion: grep default-persona.md for "docs/pipeline" in the forbidden actions gate -- present. This is a documentation-level spec; actual enforcement is verified by T-0022-077 through T-0022-079 (enforce-eva-paths.sh behavioral tests) |
| T-0022-151 | Happy | default-persona.md forbidden actions gate does NOT list `docs/product/` or `docs/ux/` as allowed main-thread write paths. Assertion: grep for "docs/product" and "docs/ux" in the "Eva may" list -- zero matches |
| T-0022-152 | Happy | pm.md command file references robert-spec subagent invocation pattern |
| T-0022-153 | Happy | ux.md command file references sable-ux subagent invocation pattern |
| T-0022-154 | Happy | create-agent.md references per-agent hook pattern (not enforce-paths.sh) for granting write access |
| T-0022-155 | Happy | technical-reference.md describes three-layer enforcement pyramid |
| T-0022-156 | Regression | No reference to enforce-paths.sh remains in Claude Code documentation (only in Cursor docs, this ADR, and git history). Grep `source/shared/`, `source/claude/`, `docs/guide/`, `CLAUDE.md` for `enforce-paths.sh` -- zero matches |
| T-0022-156a | Regression | Cursor-facing documentation correctly retains `enforce-paths.sh` references (Cursor still uses the monolith). Grep `source/cursor/` for `enforce-paths.sh` -- at least one match |
| T-0022-157 | Regression | CLAUDE.md Agents section reflects the updated roster. "14 agents" refers to: 11 core agents (cal, colby, roz, ellis, agatha, robert, robert-spec, sable, sable-ux, investigator, distillator) + 3 optional agents (sentinel, darwin, deps). The count and roster listing must be consistent |

### Step 2f Telemetry

Telemetry: documentation grep for "enforce-paths.sh" returns zero Claude Code references. Trigger: post-install verification. Absence means: stale documentation references.

### Step 2g Tests (Legacy Cleanup + Final Verification)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-160 | Happy | `tests/hooks/enforce-paths.bats` does not exist (deleted) |
| T-0022-161 | Happy | `bats tests/hooks/` full suite passes (all tests green) |
| T-0022-162 | Regression | doc-sync.bats references updated source paths (source/claude/hooks/ or source/shared/) |
| T-0022-163 | Regression | if-conditionals.bats T-0020-004 (which asserts enforce-paths.sh blocks colby writing to docs) is either: (a) removed (the test's subject no longer exists in Claude Code) and replaced with a test that verifies enforce-colby-paths.sh blocks colby writing to docs, or (b) updated to reference a Cursor-specific test path. The replacement assertion must verify the same enforcement behavior (colby blocked from docs/) using the new per-agent script |
| T-0022-164 | Regression | No test file references `source/hooks/` (flat, deprecated path) |
| T-0022-165 | Boundary | grep -r for `source/agents/` across entire codebase returns zero results (excluding this ADR and git history) |
| T-0022-166 | Boundary | grep -r for `source/hooks/` across entire codebase returns zero results (excluding this ADR, git history, and `source/cursor/hooks/` which is intentional) |

### Step 2g Telemetry

Telemetry: full bats test suite pass rate. Trigger: `bats tests/hooks/`. Absence means: test regression in final verification.

### Step 2h Tests (Wave-Boundary Compaction Advisory Hook)

| ID | Category | Description |
|----|----------|-------------|
| T-0022-170 | Happy | `source/hooks/prompt-compact-advisory.sh` exists and is executable (`-x` bit set) |
| T-0022-171 | Happy | Script outputs advisory text containing "WAVE BOUNDARY" and "/compact" when: stdin has `agent_type: "ellis"`, pipeline-state.md exists with `PIPELINE_STATUS` marker containing `"phase": "build"`. Assertion: run script with mocked stdin and pipeline-state.md, capture stdout, verify it contains both strings |
| T-0022-172 | Happy | Script outputs advisory text when phase is `implement` (alternative build-phase name). Same setup as T-0022-171 but with `"phase": "implement"` in PIPELINE_STATUS |
| T-0022-173 | Failure | Script outputs NO text (empty stdout) when phase is `review`. Setup: stdin has `agent_type: "ellis"`, pipeline-state.md has `"phase": "review"`. Assertion: stdout is empty |
| T-0022-174 | Failure | Script outputs NO text when phase is `complete`. Same setup with `"phase": "complete"` |
| T-0022-175 | Failure | Script outputs NO text when phase is `idle`. Same setup with `"phase": "idle"` |
| T-0022-176 | Failure | Script outputs NO text when pipeline-state.md does not exist. Stdin has `agent_type: "ellis"` but no state file. Assertion: stdout is empty, exit code is 0 |
| T-0022-177 | Failure | Script outputs NO text when PIPELINE_STATUS marker is absent from pipeline-state.md. State file exists but contains no `<!-- PIPELINE_STATUS:` marker. Assertion: stdout is empty, exit code is 0 |
| T-0022-178 | Boundary | Script exits 0 in ALL cases -- advisory (stdout present), silent (stdout empty), and error (missing dependencies). Parametric: test exit code for phase=build, phase=review, missing state file, missing jq, empty stdin. All must be 0 |
| T-0022-179 | Failure | Script outputs NO text when stdin is empty (no JSON input). Assertion: stdout is empty, exit code is 0 |
| T-0022-180 | Boundary | Script outputs NO text when jq is not available on PATH. Remove jq from PATH, run with valid stdin and pipeline-state.md with phase=build. Assertion: stdout is empty, exit code is 0. Graceful degradation, not failure |
| T-0022-181 | Failure | Script outputs NO text when agent_type is not `ellis`. Stdin has `agent_type: "colby"`, pipeline-state.md has phase=build. Assertion: stdout is empty, exit code is 0. Note: in production, the `"if": "agent_type == 'ellis'"` conditional in settings.json prevents the hook from firing for non-Ellis agents, but the script must also handle this defensively |
| T-0022-182 | Boundary | Script is under 35 lines (lightweight requirement per retro lesson #003). Assertion: `wc -l < source/hooks/prompt-compact-advisory.sh` returns a number <= 35 |
| T-0022-183 | Security | Script does NOT write to any file. Assertion: script execution does not create or modify any files outside its stdout output -- verified by comparing directory state before and after running the script (e.g., `find . -newer /tmp/before_marker -not -path './.git/*'` returns zero results). Alternative assertion: `grep -E '(>>?\s+["/]|tee\s)' source/hooks/prompt-compact-advisory.sh` returns zero matches (matches redirect-to-file patterns only, avoiding false-positives on `>` in advisory text or comparison operators) |
| T-0022-184 | Regression | Script does NOT invoke brain (`agent_capture`, `agent_search`), run tests (`bats`, `npm test`, `pytest`), or invoke subagents (`Agent`). Grep script content for these patterns. Assertion: zero matches |
| T-0022-185 | Happy | `skills/pipeline-setup/SKILL.md` hook source table contains a row with `source/hooks/prompt-compact-advisory.sh` as template source and `.claude/hooks/prompt-compact-advisory.sh` as destination |
| T-0022-186 | Happy | `skills/pipeline-setup/SKILL.md` settings.json template SubagentStop section contains a hook entry with `"type": "prompt"` and `"prompt":` value referencing `prompt-compact-advisory.sh` and `"if": "agent_type == 'ellis'"` conditional |
| T-0022-187 | Happy | `source/references/pipeline-operations.md` Compaction Strategy subsection contains text referencing `prompt-compact-advisory.sh` and "wave-boundary" or "wave boundary" |
| T-0022-188 | Regression | Existing SubagentStop hooks in settings.json template are unchanged: warn-dor-dod.sh (command, if colby/roz), log-agent-stop.sh (command), prompt-brain-capture.sh (prompt), warn-brain-capture.sh (command, if cal/colby/roz/agatha). The new hook is ADDED, not replacing any existing entry |
| T-0022-189 | Boundary | Advisory text includes the string "user's decision" or "Do not auto-compact" -- the hook must make clear this is advisory, not automatic. Assertion: stdout from a phase=build run contains one of these strings |
| T-0022-190 | Happy | Script uses `CLAUDE_PROJECT_DIR` environment variable to locate pipeline-state.md with fallback to `CURSOR_PROJECT_DIR` then `PWD`. Grep script content for `CLAUDE_PROJECT_DIR` -- present. Grep for `CURSOR_PROJECT_DIR` -- present (fallback pattern consistent with other hooks) |
| T-0022-191 | Boundary | `prompt-compact-advisory.sh` outputs empty stdout and exits 0 when `PIPELINE_STATUS` phase is an unrecognized value (e.g., `"phase": "unknown"`) -- script does not assume all unrecognized phases should trigger advisory. Stdin has `agent_type: "ellis"`, pipeline-state.md has PIPELINE_STATUS with `"phase": "unknown"`. Assertion: stdout is empty, exit code is 0 |

### Step 2h Telemetry

Telemetry: "WAVE BOUNDARY" advisory text in Eva's context after Ellis per-wave commit. Trigger: Ellis completes a SubagentStop event during build phase. Absence means: prompt hook is not firing, not registered in settings.json, or phase detection is broken.

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `source/shared/agents/{name}.md` (content body) | Markdown without YAML frontmatter; starts with `<!-- Part of atelier-pipeline -->` comment | /pipeline-setup overlay assembly (SKILL.md) | 1d |
| `source/{platform}/agents/{name}.frontmatter.yml` (frontmatter overlay) | Raw YAML (no `---` delimiters); required fields: name, description, model, effort, maxTurns | /pipeline-setup overlay assembly (SKILL.md) | 1d |
| /pipeline-setup assembled agent file | Complete `.md` with `---` YAML frontmatter + content body | Claude Code / Cursor runtime (`.claude/agents/` or `.cursor/agents/`) | 1d |
| `source/claude/hooks/enforce-{agent}-paths.sh` (per-agent hook) | Bash script, exit 0 (allow) or exit 2 (block), stderr message on block | Agent frontmatter `hooks:` field (PreToolUse registration) | 2e |
| `source/claude/hooks/enforce-eva-paths.sh` (main thread hook) | Bash script, exit 0 (allow) or exit 2 (block) | settings.json PreToolUse registration (Write\|Edit\|MultiEdit) | 2e |
| `source/shared/agents/robert-spec.md` (producer persona) | Markdown persona content with write-focused identity and workflow | Eva routing (agent-system.md /pm intent) | 2c |
| `source/shared/agents/sable-ux.md` (producer persona) | Markdown persona content with write-focused identity and workflow | Eva routing (agent-system.md /ux intent) | 2c |
| Platform detection logic (`CURSOR_PROJECT_DIR` env var) | Boolean: set -> Cursor platform, unset -> Claude Code platform | /pipeline-setup overlay directory selection (SPOF contract) | 1d |
| `enforcement-config.json` (simplified) | JSON with `pipeline_state_dir`, `test_patterns`, `colby_blocked_paths`, `test_command` keys | enforce-roz-paths.sh, enforce-colby-paths.sh, enforce-pipeline-activation.sh, enforce-sequencing.sh | 2a |
| `source/hooks/prompt-compact-advisory.sh` (wave-boundary advisory) | Bash prompt hook, stdout advisory text when phase=build/implement, empty stdout otherwise. Exit 0 always | settings.json SubagentStop prompt hook registration (`"if": "agent_type == 'ellis'"`) -> Eva's context | 2h |
| `pipeline-operations.md` Compaction Strategy (wave-boundary bullet) | Prose rule documenting the wave-boundary advisory behavior | Eva runtime (loaded via path-scoped rules) | 2h |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `source/shared/` (content bodies) | Markdown files | /pipeline-setup SKILL.md (overlay assembly) | 1d |
| `source/claude/agents/*.frontmatter.yml` | YAML frontmatter | /pipeline-setup SKILL.md (overlay assembly) | 1d |
| `source/cursor/agents/*.frontmatter.yml` | YAML frontmatter | /pipeline-setup SKILL.md (overlay assembly) | 1d |
| `source/claude/hooks/*` | Bash scripts | /pipeline-setup SKILL.md (install to .claude/hooks/) | 1d |
| `source/cursor/hooks/*` | JSON + Bash | .cursor-plugin SKILL.md (install to .cursor/hooks/) | 1d |
| Per-agent hook scripts | exit 0 / exit 2 | Agent frontmatter hooks field (Claude Code runtime) | 2e |
| enforce-eva-paths.sh | exit 0 / exit 2 | settings.json PreToolUse (main thread) | 2e |
| robert-spec.md (assembled) | Agent persona | Eva auto-routing (/pm intent -> robert-spec subagent) | 2c, 2f |
| sable-ux.md (assembled) | Agent persona | Eva auto-routing (/ux intent -> sable-ux subagent) | 2c, 2f |
| permissionMode in frontmatter | `acceptEdits` string | Claude Code runtime (auto-approve file edits) | 2d |
| enforcement-config.json (simplified) | JSON with pipeline_state_dir, test_patterns, colby_blocked_paths, test_command | enforce-roz-paths.sh, enforce-colby-paths.sh, enforce-pipeline-activation.sh, enforce-sequencing.sh | 2a |
| /pipeline-setup assembled output | Complete .md files in .claude/agents/ or .cursor/agents/ | Claude Code / Cursor runtime | 1d (T-0022-034a) |
| Platform detection (CURSOR_PROJECT_DIR) | Overlay directory selection (source/claude/ or source/cursor/) | /pipeline-setup install logic, all installed agents | 1d (T-0022-033a through T-0022-033d) |
| prompt-compact-advisory.sh | Advisory stdout text ("WAVE BOUNDARY...") or empty | Eva's context (injected by Claude Code SubagentStop prompt hook system) | 2h |
| SKILL.md settings.json SubagentStop prompt entry | `{"type": "prompt", "prompt": "...prompt-compact-advisory.sh", "if": "agent_type == 'ellis'"}` | Claude Code hook system (fires on Ellis SubagentStop) | 2h |
| pipeline-operations.md wave-boundary bullet | Prose rule | Eva runtime (behavioral documentation) | 2h |

## Data Sensitivity

No store methods involved (this ADR modifies source templates, hooks, and documentation only). No database changes. No API endpoints.

## Notes for Colby

### Phase 1 Implementation Hints

1. **Frontmatter extraction pattern:** Use `awk` or `sed` to split at the second `---`. Everything between first and second `---` (exclusive) is frontmatter. Everything after the second `---` is content body. Verify with the byte-identity test (T-0022-010).

2. **File move order matters:** Move non-agent files first (Step 1a), then split agents (Step 1b), then hooks (Step 1c). This sequence lets you validate each move independently. Do not move everything at once.

3. **test_helper.bash HOOKS_DIR:** The `HOOKS_DIR` variable on line 6 uses a relative path from the test file to `source/hooks/`. After the split, it needs to point to `source/claude/hooks/`. This is a one-line change but it affects every test. Change it in Step 1e, not earlier.

4. **{config_dir} placeholder:** The shared content files retain `{config_dir}` as a placeholder. It is NOT resolved during the split -- it is resolved during /pipeline-setup installation in the target project. Do not accidentally resolve it.

5. **The `<!-- Part of atelier-pipeline -->` comment:** In current agent files, this comment appears right after the closing `---` of the frontmatter. In the split, it becomes the first line of the shared content file. Ensure there is no blank line between the comment and the identity section.

### Phase 2 Implementation Hints

6. **Per-agent hook scripts:** The scripts that need enforcement-config.json (enforce-roz-paths.sh and enforce-colby-paths.sh) should use `SCRIPT_DIR` to locate the config file in the same directory, identical to how enforce-paths.sh does it today. The other 5 scripts hardcode their allowed paths directly -- they do not need config file reads.

7. **Main thread detection:** enforce-eva-paths.sh does NOT check `agent_type` because it fires only from the main thread (registered in settings.json, not in any agent's frontmatter). The script trusts that it is called from the main thread context.

8. **Robert-spec persona content:** The producer persona should inherit Robert's domain expertise (product thinking, outcome focus, ROI analysis) but replace the reviewer workflow with a producer workflow (discovery questions, spec writing, acceptance criteria authoring). The information asymmetry constraint does NOT apply to the producer variant -- robert-spec needs to read prior specs, prior ADRs, and brain context to write good specs. However, robert-spec should NOT reference Roz's QA reports (`last-qa-report.md`) or the current pipeline's active ADR -- those are review-phase artifacts that could anchor spec writing. The asymmetry applies only to robert.md (reviewer mode) for implementation review isolation.

9. **Sable-ux persona content:** Same pattern as Robert-spec. The producer persona inherits Sable's UX expertise but replaces the reviewer workflow with a design workflow (user flow analysis, state design, interaction patterns, accessibility requirements). Information asymmetry applies only to sable.md (reviewer mode).

10. **enforce-paths.sh deletion (Claude Code only):** When deleting enforce-paths.sh from `source/claude/hooks/`, verify that the Cursor copy in `source/cursor/hooks/enforce-paths.sh` is complete and byte-identical to the pre-deletion Claude Code version. The Cursor copy must be self-contained.

11. **settings.json update pattern:** The current settings.json has `"matcher": "Write|Edit|MultiEdit"` pointing to enforce-paths.sh. In Phase 2, this changes to point to enforce-eva-paths.sh. The per-agent scripts are NOT registered in settings.json -- they are registered in each agent's frontmatter `hooks:` field. Only the main-thread hook goes in settings.json.

**11a. CRITICAL -- enforcement-config.json simplification scope:** When simplifying enforcement-config.json, remove ONLY the enforcement-path-specific keys: `architecture_dir`, `product_specs_dir`, `ux_docs_dir`. Do NOT remove `pipeline_state_dir` -- it is consumed by `enforce-pipeline-activation.sh` (line 48) and `enforce-sequencing.sh` (line 42), which are not part of this redesign. Removing `pipeline_state_dir` would silently break pipeline activation enforcement. Also retain `test_command` and `test_patterns` and `colby_blocked_paths`.

13. **Wave-boundary compaction advisory hook pattern (Step 2h).** Follow the prompt-brain-capture.sh pattern exactly: `set -uo pipefail` (not `set -e`), `INPUT=$(cat 2>/dev/null) || true`, graceful jq fallback, agent_type check via case statement. For phase detection, use the same `parse_pipeline_status` approach as enforce-sequencing.sh: grep for `<!-- PIPELINE_STATUS:` in pipeline-state.md, extract the JSON, parse with jq. But keep it simpler -- the hook only needs the `phase` field, not the full parser. A one-liner `grep -o '<!-- PIPELINE_STATUS: .*-->' | sed | jq -r '.phase'` is sufficient. The `if` conditional `"agent_type == 'ellis'"` goes in the settings.json registration, NOT in the script's case statement (the case statement is a defensive fallback). Register the hook in SKILL.md's settings.json template by adding a new entry to the existing SubagentStop hooks array -- do NOT replace the existing entries (warn-dor-dod.sh, log-agent-stop.sh, prompt-brain-capture.sh, warn-brain-capture.sh). Place `prompt-compact-advisory.sh` in `source/hooks/`, not `source/claude/hooks/`, because it has no Cursor equivalent and follows the shared hook pattern (like pre-compact.sh and log-agent-stop.sh). The install destination is still `.claude/hooks/prompt-compact-advisory.sh`.

12. **Step sizing note:** Steps 2c and 2e are the largest in Phase 2. Step 2c touches 8 files (create 6, modify 2) -- at the boundary of the 8-file guideline. This is justified because the 6 created files are simple (frontmatter YAML + persona content) and the 2 modified files (agent-system.md, SKILL.md) have well-defined insertion points. Step 2e touches 9 files (modify 8, delete 1) but the modifications are small (adding a `hooks:` YAML field to each overlay). Both steps pass the S1-S5 sizing gates because each is independently verifiable and demoable.

---

## DoD: Verification

| # | Requirement | Status | ADR Coverage |
|---|-------------|--------|-------------|
| R1 | Split source/ into platform-specific directories | Done | Steps 1a, 1b, 1c |
| R2 | DRY strategy for shared vs platform-divergent content | Done | Overlay pattern (Decision section) |
| R3 | Update /pipeline-setup for new structure | Done | Step 1d |
| R4 | Phase 1 before Phase 2 (sequential) | Done | Two-phase structure, explicit dependency |
| R5 | Replace enforce-paths.sh with per-agent hooks | Done | Steps 2a, 2e |
| R6 | Three-layer enforcement pyramid | Done | Decision section (Layer 1/2/3 tables) |
| R7 | permissionMode: acceptEdits on write-heavy agents | Done | Step 2d |
| R8 | Robert/Sable write-capable subagents | Done | Step 2c |
| R9 | Robert-spec -> docs/product/, Sable-ux -> docs/ux/ | Done | Steps 2a, 2c |
| R10 | Per-agent scripts ~15-20 lines, no case statement | Done | Step 2a (template pattern shown) |
| R11 | Cursor keeps global hook model | Done | Decision section (Cursor enforcement strategy) |
| R12 | Robert/Sable dual mode (two persona files each) | Done | Step 2c |
| R13 | Eva main thread: docs/pipeline/ only | Done | Steps 2a (enforce-eva-paths.sh), 2f |
| R14 | Agents in project .claude/agents/ | Done | Step 1d (install target unchanged) |
| R15 | Core agent constant updated | Done | Step 2c (11 core agents listed) |
| R16 | Hooks fire with acceptEdits | Done | Step 2d (noted, verified by existing tests) |
| R17 | Parent mode override documented | Done | Step 2d acceptance criteria |
| R18 | Colby edits source/ only | Done | All steps target source/ directory |
| R19 | Equivalent test coverage for new scripts | Done | Steps 2b, 2g (T-0022-097) |
| R20 | Ellis: no path hooks | Done | Step 2e (T-0022-145) |
| R21 | Read-only agents keep disallowedTools | Done | Layer 1 table in Decision |
| R22 | /pm and /ux become subagent invocations | Done | Steps 2c, 2f |
| R23 | Wave-boundary compaction advisory: prompt hook detects Ellis per-wave commit and advises Eva to suggest /compact | Done | Step 2h |

**Architectural decisions not in the spec:**
- Overlay pattern chosen over full copies or templating engine (see Alternatives)
- enforcement-config.json simplified but retained (not deleted) -- enforce-roz-paths.sh needs test_patterns, enforce-colby-paths.sh needs colby_blocked_paths, and enforce-pipeline-activation.sh / enforce-sequencing.sh need pipeline_state_dir. Only enforcement-path-specific keys (architecture_dir, product_specs_dir, ux_docs_dir) are removed
- enforce-eva-paths.sh created as a new script rather than modifying enforce-paths.sh -- cleaner separation

**Rejected alternatives with reasoning:**
- Full file copies: drift risk with 24 files
- Build-time templating: over-engineering for 5-15 lines of divergence
- Plan mode for read-only agents: blocks Bash which reviewers need

**Technical constraints discovered during design:**
- Cursor has no runtime support for frontmatter hooks, permissionMode, or disallowedTools enforcement -- divergence is structural, not a configuration difference
- enforce-roz-paths.sh and enforce-colby-paths.sh cannot be fully self-contained (they need test_patterns and colby_blocked_paths from config) -- this is acceptable since the config read is lightweight
- The `{config_dir}` placeholder must survive the source split intact -- it is resolved at install time, not at template-split time

**Test spec: Roz-approved (revision 1, 2026-04-03).**

ADR saved to `docs/architecture/ADR-0022-wave3-native-enforcement-redesign.md`. 14 steps (6 Phase 1, 8 Phase 2), 178 total tests. Roz reviewed the initial 136-test spec and returned REVISE with 4 blockers, 9 fix-required items, 7 ambiguity flags, 5 untestable specs, and 2 domain intent flags. All 27 findings are resolved in revision 1. Revision 2 added Step 2h (wave-boundary compaction advisory) with 21 tests. Revision 3 applied 3 targeted fixes from Roz's scoped re-review (T-0022-183 precision, T-0022-191 added, Note 13 source path guidance).

---

## ADR-0022 Revision Log

### Revision 1 (2026-04-03) -- Roz QA Test Spec Review Response

**Source:** `docs/pipeline/last-qa-report.md` (Roz ADR Test Spec Review, 2026-04-03)

**Summary:** Roz reviewed the initial 136-test specification and returned REVISE with 27 findings across 5 categories. All findings are resolved in this revision, bringing the total test count from 136 to 156 (+20 tests added).

#### Blockers Resolved (4)

| Blocker | Finding | Resolution |
|---------|---------|------------|
| BLOCKER 1 | SPOF (platform detection) had no behavioral test spec -- only T-0022-033 checking SKILL.md text | Added T-0022-033a (Claude overlay when CURSOR_PROJECT_DIR unset), T-0022-033b (Cursor overlay when set), T-0022-033c (precedence when both set), T-0022-033d (installed file frontmatter verification) |
| BLOCKER 2 | jq-missing behavior unspecified for per-agent scripts that read enforcement-config.json via jq | Added T-0022-087c (enforce-roz-paths.sh jq-missing exits 2) and T-0022-087d (enforce-colby-paths.sh jq-missing exits 2). Mirrors T-0003-019 pattern |
| BLOCKER 3 | T-0022-115 and Note 8 contradicted on robert-spec information asymmetry | Domain decision: Note 8 is correct. Robert-spec MAY read prior specs/ADRs (a spec writer needs context). T-0022-115 narrowed to: does NOT reference Roz QA reports or current pipeline ADR. Asymmetry applies only to reviewer variant (robert.md) |
| BLOCKER 4 | T-0022-097 used line count (>= 199 lines) instead of test count -- not verifiable as a coverage metric | Rewritten to: combined @test count across 7 files >= 56, with explicit grep assertion |

#### Fix-Required Items Resolved (9)

| Item | Finding | Resolution |
|------|---------|------------|
| FIX-REQ 1 | Exit-fast on non-write tool not specified (Lesson #003) | Added T-0022-087a: all 7 scripts exit 0 when tool_name is Read. Parametric |
| FIX-REQ 2 | Hook matcher values not verified in T-0022-130 through T-0022-135 | Updated all 6 specs to explicitly verify both `command:` and `matcher:` values per the Layer 2 table |
| FIX-REQ 3 | enforcement-config.json simplification not verified -- missing negative assertion for removed keys | Added T-0022-087b: asserts retained keys (pipeline_state_dir, test_patterns, colby_blocked_paths, test_command) and absence of removed keys (architecture_dir, product_specs_dir, ux_docs_dir) |
| FIX-REQ 4 | Executable permissions not tested for hook scripts | Added T-0022-025a: all .sh scripts in source/claude/hooks/ have -x bit |
| FIX-REQ 5 | robert-spec and sable-ux assembly validation missing from Phase 1 tests | Added T-0022-058: validates assembly structure, required fields, non-empty content for both new agents |
| FIX-REQ 6 | README.md missing from Step 1e documentation specs | Added T-0022-045: grep README.md for old flat paths returns zero matches |
| FIX-REQ 7 | Colby 14-path coverage not fully enumerated in T-0022-092 | Rewritten T-0022-092 to explicitly list all 14 prefixes from enforcement-config.json |
| FIX-REQ 8 | T-0022-125 missing enumeration of read-only agents | Rewritten to name all 7: robert (reviewer), sable (reviewer), investigator, distillator, sentinel, darwin, deps |
| FIX-REQ 9 | Cursor enforce-paths.sh byte-identity before deletion not specified (ADR Note 10) | Added T-0022-137a: Cursor copy byte-identical to pre-deletion Claude copy |

#### Ambiguity Flags Resolved (7)

| Flag | Finding | Resolution |
|------|---------|------------|
| AMB-001 | T-0022-010 "each 12 agents" did not enumerate or state parametric intent | Rewritten with "Parametric over all 12 agents" and full agent name list |
| AMB-002 | T-0022-080 through T-0022-082 "all 7 scripts" did not enumerate | Rewritten with "Parametric over all 7 scripts" and full script name list |
| AMB-003 | T-0022-056 "injection patterns" not defined | Enumerated: `$(`, backtick, `eval `, `exec `, `!!` (history expansion) |
| AMB-004 | T-0022-097 mixed line count with coverage metric | Rewritten as @test count >= 56 with grep assertion (same as BLOCKER 4) |
| AMB-005 | T-0022-115 vs Note 8 contradiction on robert-spec | Resolved via domain decision (same as BLOCKER 3) |
| AMB-006 | T-0022-157 "14 agents" count undisambiguated from T-0022-106 "11 core" | Disambiguated: 11 core + 3 optional = 14 total. Roster and count listed explicitly |
| AMB-007 | T-0022-034 overlay fallback behavior unspecified (silent skip is SPOF) | Rewritten: assembler MUST error-and-halt on missing overlay. Silent skip is explicitly prohibited |

#### Untestable Specs Resolved (5)

| Spec | Finding | Resolution |
|------|---------|------------|
| UNTESTABLE-001 | T-0022-098 "all use test_helper.bash patterns" -- code review criterion, not behavioral | Rewritten: "All 7 files contain `load test_helper` as non-comment line before first @test" with grep assertion |
| UNTESTABLE-002 | T-0022-030 through T-0022-032 verify SKILL.md behavior, not content | Rewritten with explicit grep assertions and labeled as documentation-level specs with cross-references to behavioral verification specs |
| UNTESTABLE-003 | T-0022-100/101 "producer-focused" is qualitative | Rewritten with string-present/string-absent assertions (producer workflow strings vs reviewer-only strings) |
| UNTESTABLE-004 | T-0022-150/151 "Eva main thread = docs/pipeline/ only" describes runtime behavior | Scoped as documentation-level specs with explicit note that behavioral verification is T-0022-077 through T-0022-079 |
| UNTESTABLE-005 | T-0022-113/114 "routing: /pm -> robert-spec" implies behavioral verification impossible in bats | Rewritten with grep assertion on agent-system.md and labeled as documentation-level specs |

#### Domain Intent Flags Resolved (2)

| Flag | Finding | Resolution |
|------|---------|------------|
| FLAG-001 | robert-spec information asymmetry: producer vs reviewer isolation | Domain decision: producer MAY read prior specs/ADRs (consistency requires context). Producer must NOT reference current pipeline QA reports or active ADR (prevents anchoring). Reviewer isolation unchanged. T-0022-115 and Note 8 now aligned |
| FLAG-002 | enforcement-config.json simplification must retain `pipeline_state_dir` | Explicit in T-0022-087b, Note 11a, Step 2a acceptance criteria, and the SIMPLIFIED table row. Only enforcement-path-specific keys removed: `architecture_dir`, `product_specs_dir`, `ux_docs_dir`. `pipeline_state_dir` retained (used by enforce-pipeline-activation.sh line 48, enforce-sequencing.sh line 42) |

#### Additional Tests Added (by step)

| Step | Tests Added | IDs |
|------|------------|-----|
| 1a | +1 | T-0022-009 (shared tree no frontmatter) |
| 1b | +1 | T-0022-010a (assembly separator correctness) |
| 1c | +2 | T-0022-025a (executable perms), T-0022-025b (hooks.json orphan check) |
| 1d | +5 | T-0022-033a/033b/033c/033d (SPOF behavioral), T-0022-034a (installed file identity) |
| 1e | +1 | T-0022-045 (README.md) |
| 1f | +2 | T-0022-057 (file count stability), T-0022-058 (new agent assembly) |
| 2a | +6 | T-0022-087a (exit-fast), T-0022-087b (config structure), T-0022-087c/087d (jq-missing), T-0022-087e/087f (eva blocked paths) |
| 2e | +1 | T-0022-137a (cursor byte-identity). Also updated: T-0022-130 through T-0022-135 and T-0022-138 (matcher field verification added to existing specs) |
| 2f | +1 | T-0022-156a (cursor retains enforce-paths.sh refs) |
| **Total** | **+20** | **136 -> 156** |

#### Wiring Coverage Updates

- Added `/pipeline-setup assembled output -> .claude/agents/` row (T-0022-034a)
- Added `Platform detection (CURSOR_PROJECT_DIR) -> overlay directory selection` row (T-0022-033a through T-0022-033d)
- Updated `enforce-{agent}-paths.sh -> frontmatter hooks` row to note matcher field verification

### Revision 2 (2026-04-03) -- Wave-Boundary Compaction Advisory (User-Requested Addition)

**Source:** User-reported context quality degradation in long pipeline sessions. No existing mechanism proactively triggers compaction; PreCompact/PostCompact hooks only handle what happens IF compaction fires.

**Summary:** Added Step 2h (wave-boundary compaction advisory hook) with 21 new tests (T-0022-170 through T-0022-190), bringing the total from 156 to 177 tests and from 13 to 14 steps. Added requirement R23 to the DoD verification table. (Test count subsequently updated to 178 by Revision 3.)

#### What Was Added

| Section | Change |
|---------|--------|
| Implementation Plan | Step 2h: Wave-Boundary Compaction Advisory Hook (1 file to create, 2 files to modify) |
| Test Specification | 21 tests (T-0022-170 through T-0022-190): 7 happy, 7 failure, 4 boundary, 1 security, 2 regression (Revision 3 added T-0022-191, total 22 Step 2h tests) |
| Contract Boundaries | 2 new rows: prompt-compact-advisory.sh -> settings.json/Eva context, pipeline-operations.md wave-boundary bullet -> Eva runtime |
| Wiring Coverage | 3 new rows: prompt-compact-advisory.sh stdout -> Eva context, SKILL.md SubagentStop entry -> Claude Code hook system, pipeline-operations.md bullet -> Eva runtime |
| DoD Verification | R23: wave-boundary compaction advisory -> Step 2h |
| Notes for Colby | Note 13: hook pattern guidance, phase detection, settings.json registration |
| Handoff | Updated: 14 steps, 177 total tests (Revision 3: 178 total tests) |

#### Design Decisions

1. **SubagentStop prompt hook (not command hook).** A command hook's stdout is not injected into Eva's context -- only prompt hooks inject text. The hook needs Eva to see the advisory and relay it. Follows the established pattern of prompt-brain-capture.sh.

2. **`if` conditional at settings.json level + defensive check in script.** The `"if": "agent_type == 'ellis'"` conditional in settings.json prevents the hook from even executing for non-Ellis agents (zero cost). The script also checks agent_type defensively (T-0022-181) because the `if` conditional is a settings.json feature that could be stripped during manual editing.

3. **Phase-based wave detection (not commit-message parsing).** The PIPELINE_STATUS `phase` field is the source of truth for pipeline state. During `build`/`implement` phase, Ellis does per-wave commits. During `review`/`complete`, Ellis does the final commit. This is more reliable than parsing commit messages for "wave" keywords.

4. **Advisory, not automatic.** The hook suggests `/compact` -- it does not trigger compaction itself. The user decides. This matches the project's principle that Eva never forces session breaks (ADR-0012, pipeline-orchestration.md Context Cleanup Advisory).

5. **Claude Code only.** Cursor has no SubagentStop prompt hooks. The hook goes in `source/hooks/` (not `source/cursor/hooks/`). SKILL.md registers it in the settings.json template which is Claude Code specific. No Cursor equivalent needed or possible.

---

### Revision 3 (2026-04-03) -- Roz Scoped Re-Review Fixes

**Source:** `docs/pipeline/last-qa-report.md` (Roz ADR Test Spec Review Mode, Scoped Re-Run, 2026-04-03). Roz verdict: PASS with 3 fix-required items.

**Summary:** Three targeted fixes applied to T-0022-183, the Step 2h test table (T-0022-191 added), and Notes for Colby Note 13. Total test count: 177 -> 178. No architectural changes.

| Section | Change |
|---------|--------|
| T-0022-183 | Replaced broad `>` grep pattern (false-positives on advisory text) with filesystem-state check + precise `grep -E '(>>?\s+["/]\|tee\s)'` alternative |
| Test Specification (Step 2h) | Added T-0022-191 (Boundary): unrecognized phase value produces empty stdout and exit 0 -- closes case-statement default-branch gap |
| Notes for Colby Note 13 | Added one sentence explicitly stating `prompt-compact-advisory.sh` goes in `source/hooks/` (not `source/claude/hooks/`), with rationale (no Cursor equivalent, shared hook pattern) |
| Handoff | Updated: 178 total tests (was 177) |
