# ADR-0015: Predictive Dependency Management Agent (Deps)

## Status

Proposed

---

## DoR: Requirements Extracted

| # | Requirement | Source | Notes |
|---|-------------|--------|-------|
| R1 | Agent persona at `source/shared/agents/deps.md`, installed to `.claude/agents/deps.md` | context-brief.md | Dual tree: template in source/, installed copy in .claude/ |
| R2 | `deps_agent_enabled` config flag in `pipeline-config.json`, default `false` | context-brief.md | Mirrors `sentinel_enabled` pattern |
| R3 | Opt-in offered during `/pipeline-setup` as Step 6d (after CI Watch, before Brain) | context-brief.md | Exact Sentinel pattern — no external tool prerequisite |
| R4 | `/deps` slash command at `source/commands/deps.md`, installed to `.claude/commands/deps.md` | context-brief.md | Follows debug.md / devops.md format |
| R5 | Agent scans dependency manifests: `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod` | spec §How It Works | All four ecosystems; skip any whose tool is absent |
| R6 | CVE scanning via `npm audit`, `pip-audit`, `cargo audit` | spec §How It Works | Report missing tools, skip that CVE section |
| R7 | Breakage prediction: cross-reference API usage (Grep) against changelog (WebFetch/WebSearch) | spec §How It Works | Degrade gracefully if WebFetch unavailable |
| R8 | Migration ADR brief handed to Cal by Eva when user requests it | spec §Migration ADR Flow | Deps produces brief; Eva routes to Cal |
| R9 | Agent is read-only — no Write/Edit/MultiEdit access | context-brief.md | Enforced by enforce-paths.sh catch-all for unknown agent types |
| R10 | Auto-routing: Eva routes dependency-related user questions to Deps agent | context-brief.md | New intent row in agent-system.md routing table |
| R11 | Report grouped by risk: CVE alerts, Needs Review, Safe to Upgrade, No action needed | spec §User Flow | Exact output format from spec |
| R12 | Edge case handling: no manifest, missing tools, offline, monorepo, private registry | spec §Edge Cases | Report, don't crash |
| R13 | SKILL.md updated with Step 6d opt-in block | context-brief.md | After Step 6c, before Brain offer |
| R14 | `invocation-templates.md` updated with `deps-scan` template | convention (Sentinel precedent) | Eva needs a standard invocation template |
| R15 | `agent-system.md` subagent table updated with Deps entry | convention (Sentinel precedent) | Subagent table + `no-skill-tool` table |

### Retro Risks

| Lesson | Risk to this feature | Mitigation |
|--------|---------------------|------------|
| #003 (Stop hook race) | Deps invocation via Bash commands (npm outdated etc.) could hang on large dep trees | Persona must include explicit "if command hangs, STOP — do not retry" constraint |
| #004 (Hung process retry loop) | `npm audit` with slow registry, `cargo audit` with large trees | Same mitigation: timeout is diagnostic, not retry trigger |
| Behavioral constraints ignored | Read-only access relies partly on `disallowedTools` frontmatter | Enforced mechanically by `enforce-paths.sh` catch-all (`*` case line 112) — no hook changes needed |

---

## Context

The pipeline has no proactive dependency management. Users defer upgrades because they cannot predict breakage risk, and CVEs linger undetected until a Dependabot alert fires reactively. Issue #20 requests a dedicated agent that scans dependency manifests, cross-references CVEs via audit tools, predicts breakage by analyzing code usage against changelogs, and surfaces a structured report — all without modifying any files.

Sentinel (ADR-0009) established the opt-in agent pattern: a config flag in `pipeline-config.json`, a setup step in SKILL.md, and a persona in `source/shared/agents/`. Deps follows this pattern exactly. Unlike Sentinel, Deps has no external MCP tool prerequisite — it uses only tools already available to Claude Code subagents (Bash, Read, Grep, Glob, WebSearch, WebFetch).

Deps is a standalone, on-demand agent. Unlike Sentinel (which runs at the review juncture as part of the pipeline flow), Deps is invoked explicitly via `/deps` or auto-routed when the user asks a dependency-related question. It does not intercept or gate pipeline phases.

### Spec Challenge

The spec assumes breakage prediction accuracy of "< 10% false safe" per quarter. If changelog quality is inconsistent (especially for minor versions, older packages, or non-English changelogs), the breakage prediction signal degrades significantly. The design fails to meet the KPI because the agent cannot distinguish "no breaking changes documented" from "no changelog exists." Are we confident? No. We accept this: the agent uses conservative risk labeling ("Needs review" when uncertain) and defers the accuracy KPI to post-launch measurement. This is explicitly noted in the spec's risk table.

SPOF: WebFetch/WebSearch availability for changelog analysis. Failure mode: If WebFetch is unavailable (no internet access, tool not available in the agent's context window), breakage prediction degrades to "unknown" for all dependencies — the agent cannot fetch changelogs. Graceful degradation: The agent still produces the full CVE report and outdated dep list from local data (audit tools, manifest reads). The report notes: "Breakage prediction unavailable — changelog fetch failed." The CVE alert section is independent of WebFetch. This is a partial-capability degradation, not a total failure.

---

## Decision

Implement Deps as an opt-in, read-only, on-demand agent following the Sentinel pattern. All changes are additive and gated behind `deps_agent_enabled: true` in `pipeline-config.json`. The agent is installed via `/pipeline-setup` Step 6d. No changes to enforcement hooks are required — the existing `enforce-paths.sh` catch-all blocks all unknown agent types from writing.

### Anti-Goals

Anti-goal: Automatic dependency upgrades. Reason: the agent is intentionally read-only; file modifications require Colby and are out of scope for an analysis agent. Revisit: when a "safe-upgrade" confidence threshold and regression test gate can be specified in an ADR.

Anti-goal: Transitive dependency analysis. Reason: the first slice scopes to direct dependencies only, keeping scan time and report complexity manageable. Revisit: when direct-dep coverage is validated and users request deep-tree analysis.

Anti-goal: License compliance scanning. Reason: this is a distinct concern from security and breakage prediction; mixing it into the Deps report conflates two different user decisions. Revisit: as a separate agent or an opt-in sub-mode of Deps (e.g., `--license-check` flag).

### Agent Design

Deps is a read-only subagent (`disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit`). It receives no pipeline diff — it operates on the current working tree's dependency manifests. It has full internet access via WebSearch and WebFetch for changelog retrieval.

Workflow:

1. Detect which ecosystems are present (manifest files + package manager availability).
2. Run outdated checks per ecosystem: `npm outdated --json`, `pip list --outdated --format=json`, `cargo outdated`, `go list -m -u all`.
3. Run CVE scans per ecosystem: `npm audit --json`, `pip-audit --format=json`, `cargo audit --json`. Go has no standard CVE audit tool equivalent — omit the CVE section for Go and include a noted gap: "Go CVE scan unavailable: no standard `go audit` tool. Use Dependabot or manual advisory review for Go CVEs."
4. For each outdated package, fetch changelog or release notes via WebFetch/WebSearch.
5. Grep the codebase for usage of APIs listed as breaking changes in changelogs.
6. Classify each dependency by risk: CVE alert, Needs review, Safe to upgrade, or No action needed.
7. Produce a structured report grouped by risk level.
8. If the user requests a migration ADR brief, produce a structured brief for Cal.

### Pipeline Integration

Deps is on-demand only. It is NOT invoked at the review juncture and does NOT run as part of a Colby build wave. Eva routes to Deps when:
- User types `/deps`
- User asks a dependency-related question (auto-routing)
- User asks "is [package] safe to upgrade" or similar

After Deps produces a report and the user requests a migration ADR: Eva routes to Cal with the Deps migration brief as context.

---

## Alternatives Considered

### Alternative A: Extend Sentinel to also scan dependencies

Sentinel already runs at review juncture and has Bash access. We could add a dependency scan phase to Sentinel's workflow.

Rejected. Sentinel operates under information asymmetry (no spec, no ADR, no context) and is scoped to static analysis of the current diff. Dependency scanning requires reading the full working tree, fetching external changelogs, and correlating usage patterns — a fundamentally different analysis mode. Mixing them in one agent would break Sentinel's design principle and make both concerns worse. Sentinel also runs automatically in the pipeline; Deps is on-demand. These are different lifecycles.

### Alternative B: Build as a plugin skill (main thread, conversational)

Skills run in the main thread alongside Eva. This would avoid subagent invocation overhead.

Rejected. Dependency scanning requires running Bash commands (`npm outdated`, `cargo audit`), reading multiple files, and fetching external URLs. These are non-trivial tool call sequences that benefit from a dedicated context window. Skills are better suited for short conversational workflows (Robert spec discovery, Sable UX review). The codebase scan + CVE audit + changelog fetch pattern is an execution task, not a conversational one. Subagent is the correct pattern.

---

## Consequences

Positive:
- Users get proactive CVE and breakage risk visibility without leaving the pipeline.
- Migration ADR briefs reduce the cognitive overhead of major version upgrades.
- Zero impact on users who do not opt in — all behavior is gated behind the config flag.
- No new external tool prerequisites — Bash, WebFetch, and WebSearch are already available.

Negative:
- Breakage prediction accuracy is inherently uncertain for poorly documented packages.
- Scan time is bounded by the slowest external tool (`cargo audit` on a large tree can take 30+ seconds).
- WebFetch rate limits or failures silently degrade the changelog analysis section.

---

## Blast Radius

| File | Change | Impact |
|------|--------|--------|
| `source/shared/agents/deps.md` | CREATE | New agent persona template |
| `.claude/agents/deps.md` | CREATE | Installed copy (dual tree) |
| `source/commands/deps.md` | CREATE | New slash command template |
| `.claude/commands/deps.md` | CREATE | Installed copy (dual tree) |
| `source/pipeline/pipeline-config.json` | MODIFY | Add `deps_agent_enabled: false` |
| `.claude/pipeline-config.json` | MODIFY | Add `deps_agent_enabled: false` |
| `skills/pipeline-setup/SKILL.md` | MODIFY | Add Step 6d opt-in block |
| `source/rules/agent-system.md` | MODIFY | Add Deps to subagent table + no-skill-tool table + auto-routing table |
| `.claude/rules/agent-system.md` | MODIFY | Installed copy (dual tree) |
| `source/references/invocation-templates.md` | MODIFY | Add `deps-scan` template |
| `.claude/references/invocation-templates.md` | MODIFY | Installed copy (dual tree) |
| `source/claude/hooks/enforce-paths.sh` | NO CHANGE | Catch-all `*` case already blocks unknown agents |
| `.claude/hooks/enforce-paths.sh` | NO CHANGE | Same |

Consumer mapping (Wiring Coverage):
- `source/shared/agents/deps.md` (producer: agent persona) → consumed by Eva via subagent invocation, and by `/deps` slash command dispatch (Step 1 + Step 3)
- `source/commands/deps.md` (producer: slash command) → consumed by user typing `/deps` → Eva reads command file → invokes Deps subagent (Step 2 + Step 3)
- `deps_agent_enabled` flag (producer: pipeline-config.json) → consumed by SKILL.md Step 6d (install gate) and by Eva auto-routing (Step 4)
- `deps-scan` invocation template (producer: invocation-templates.md) → consumed by Eva when routing to Deps (Step 5)

---

## Implementation Plan

### Step 1: Agent Persona (`source/shared/agents/deps.md` + `.claude/agents/deps.md`)

**Files to create:**
- `source/shared/agents/deps.md` — template persona (source of truth for pipeline-setup to install from)
- `.claude/agents/deps.md` — installed copy (this project eats its own cooking)

**Persona content (Colby implements this as the file body):**

YAML frontmatter:
```yaml
---
name: deps
description: >
  Predictive dependency management agent. Scans dependency manifests, checks
  CVEs via audit tools, predicts breakage by cross-referencing usage patterns
  against changelogs, and produces a risk-grouped report. Opt-in via
  pipeline-config.json. Invoked on-demand via /deps or auto-routing.
disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit
---
```

The persona XML structure must follow the established pattern (`identity`, `required-actions`, `workflow`, `examples`, `tools`, `constraints`, `output`). Key behavioral rules for Colby to encode:

- `<identity>`: Deps is the Dependency Management Agent. Pronouns: they/them. Read-only. Produces reports, never modifies files. Runs on Sonnet model (on-demand, not review-juncture heavyweight analysis).
- `<required-actions>`: (1) DoR — list detected ecosystems + manifest paths + package manager availability. (2) Follow agent-preamble.md steps. (3) If brain context injected, factor in prior dependency decisions. (4) Scan manifests, run outdated checks, run CVE checks, fetch changelogs. (5) Grep codebase for breaking API usage. (6) Produce report. (7) DoD.
- `<workflow>`: Three phases — Detect, Scan, Report. See §How It Works in spec. Edge cases from spec §Edge Cases must be encoded here. Go ecosystem handling must be explicit: `go list -m -u all` is used for outdated detection; no Go CVE audit tool is available; the CVE subsection for Go is omitted and the report notes the gap rather than leaving it blank or erroring.
- `<examples>`: (a) Skipping a missing tool: cargo not found — skip Rust ecosystem, note in report. (b) Breakage prediction: react 18 → 19, grep for `findDOMNode`, found in 3 files → HIGH risk. (c) Go CVE gap: `go.mod` detected, `go list -m -u all` run for outdated versions, CVE section omitted with noted gap: "Go CVE scan unavailable." This tag is required — the file must contain an `<examples>` tag (T-0015-005).
- `<tools>`: Bash (read-only: npm outdated, pip list, cargo outdated, go list, npm audit, pip-audit, cargo audit — never modify files), Read (manifests), Grep (API usage patterns), Glob (manifest discovery), WebSearch, WebFetch (changelogs, release notes).
- `<constraints>`: Never modify files. If a Bash command hangs or times out, STOP — do not retry. Use conservative risk labels — prefer "Needs review" over "Safe" when uncertain. If WebFetch unavailable, note in report and skip changelog analysis. If no manifests found, report and stop. Monorepo: scan all manifests, group by directory. Permitted Bash commands (explicit whitelist): `npm outdated`, `npm audit`, `pip list --outdated`, `pip-audit`, `cargo outdated`, `cargo audit`, `go list -m -u all`. Prohibited Bash commands (explicit blocklist): any command that modifies the filesystem including `npm install`, `npm update`, `pip install`, `pip install --upgrade`, `cargo update`, `go get`, `go mod tidy`. Any Bash invocation not on the whitelist requires a justification comment in the constraint section.
- `<output>`: Structured report with four sections: CVE Alerts, Needs Review, Safe to Upgrade, No Action Needed. Each dep entry: name, current version, latest version, CVE IDs (if any), breaking changes found in usage (file:line), risk label, recommendation. Plus optional migration ADR brief section if requested.

**Acceptance criteria:**
- `source/shared/agents/deps.md` exists with correct YAML frontmatter (`name: deps`, `disallowedTools` set).
- `.claude/agents/deps.md` exists with identical content.
- Eva's boot-sequence agent discovery scan finds `deps` and announces it as a discovered agent (since `deps` is not in the core agent constant list).
- `disallowedTools` frontmatter blocks Write/Edit from the frontmatter layer; enforce-paths.sh catch-all blocks it at the mechanical layer.

**Estimated complexity:** Low. Persona authoring following a clear template.

---

### Step 2: Slash Command (`source/commands/deps.md` + `.claude/commands/deps.md`)

**Files to create:**
- `source/commands/deps.md`
- `.claude/commands/deps.md`

**Command content:** The `/deps` command file is a behavior descriptor for Eva, not for the Deps agent itself (same pattern as `debug.md`). It tells Eva how to invoke Deps and handle the two flow variants:

Flow A — Scan and report:
1. Eva reads `deps_agent_enabled` from `pipeline-config.json`. If `false`, respond: "Deps agent is not enabled. Run `/pipeline-setup` and enable it in Step 6d." Stop.
2. Eva invokes Deps subagent with the `deps-scan` invocation template.
3. Eva presents the report to the user.

Flow B — Migration ADR brief:
1. User asks "propose a migration ADR for [package]" (or equivalent).
2. Eva invokes Deps subagent with `deps-migration-brief` invocation template, scoped to the named package.
3. Eva receives the brief, then routes to Cal with the brief as context.

The command file must also document that auto-routing (without typing `/deps`) follows the same flow when Eva classifies dependency intent.

**Acceptance criteria:**
- `source/commands/deps.md` and `.claude/commands/deps.md` exist.
- File follows the same YAML frontmatter format as `debug.md` (`name: deps`, `description` one-liner).
- The `deps_agent_enabled` gate is present — the command does not silently proceed when the agent is not installed.

**Estimated complexity:** Low.

---

### Step 3: Config Flag (`source/pipeline/pipeline-config.json` + `.claude/pipeline-config.json`)

**Files to modify:**
- `source/pipeline/pipeline-config.json` — add `"deps_agent_enabled": false`
- `.claude/pipeline-config.json` — add `"deps_agent_enabled": false`

Both files must add the key after the existing `ci_watch_log_command` field (maintain field ordering convention established by prior flags: sentinel, agent_teams, ci_watch, then deps).

**Acceptance criteria:**
- Both files contain `"deps_agent_enabled": false`.
- No existing field is modified or removed.
- JSON remains valid (parseable by `jq .`).

**Estimated complexity:** Trivial.

---

### Step 4: Auto-Routing Update (`source/rules/agent-system.md` + `.claude/rules/agent-system.md`)

**Files to modify:**
- `source/rules/agent-system.md`
- `.claude/rules/agent-system.md`

**Three changes in each file:**

Change A — Subagent table (under `### Subagents (own context window)`): add row after Sentinel:
```
| **Deps** | Dependency management -- outdated scan, CVE check, breakage prediction | Read, Glob, Grep, Bash (read-only), WebSearch, WebFetch |
```

Change B — `no-skill-tool` table (gate section at the bottom): add row:
```
| Deps (dependency scan) | `.claude/agents/deps.md` |
```

Change C — Auto-routing intent table: add row in the appropriate position (between general codebase questions and infra/devops questions):
```
| Asks about outdated dependencies, CVEs, upgrade risk, "is [package] safe to upgrade", "check my deps", dependency vulnerabilities | **Deps** (if `deps_agent_enabled: true`) or suggest enabling | subagent |
```

The routing entry must include the `deps_agent_enabled` gate condition — Eva should not silently route to a disabled agent.

**Acceptance criteria:**
- Both files updated with all three changes.
- Deps appears in subagent table with correct tool access.
- Auto-routing table contains a Deps row with the `deps_agent_enabled` gate condition.
- `no-skill-tool` gate maps Deps correctly.

**Estimated complexity:** Low.

---

### Step 5: Invocation Template (`source/references/invocation-templates.md` + `.claude/references/invocation-templates.md`)

**Files to modify:**
- `source/references/invocation-templates.md`
- `.claude/references/invocation-templates.md`

Add two templates after the `sentinel-audit` template block:

Template A — `deps-scan` (full scan):
```xml
<template id="deps-scan">

### Deps (Full Dependency Scan)

Eva invokes Deps when the user types `/deps` or when dependency-related intent
is detected (when `deps_agent_enabled: true` in `pipeline-config.json`).

<task>Scan dependency manifests, check CVEs, predict breakage risk, and produce a risk-grouped report.</task>

<constraints>
- Detect which ecosystems are present (package.json, requirements.txt, Cargo.toml, go.mod).
- Run outdated checks and CVE audit per ecosystem. Skip any ecosystem whose tool is absent — report the gap.
- Fetch changelogs for packages with major version bumps via WebFetch/WebSearch. If unavailable, note in report and skip changelog analysis.
- Grep codebase for usage of APIs listed as breaking changes in changelogs.
- Use conservative risk labels: prefer "Needs review" over "Safe" when uncertain.
- If a Bash command hangs or times out, STOP. Do not retry. Report partial results.
- Never modify files. This is analysis only.
- Monorepo: scan all manifests found. Group report by directory.
</constraints>

<output>Risk-grouped dependency report: CVE Alerts | Needs Review | Safe to Upgrade | No Action Needed. Each entry: package name, current version, target version, CVE IDs, breaking API usage found (file:line), risk label, recommendation. DoR (ecosystems detected, tools available) and DoD sections.</output>

</template>
```

Template B — `deps-migration-brief` (scoped to one package):
```xml
<template id="deps-migration-brief">

### Deps (Migration ADR Brief)

Eva invokes Deps when the user requests a migration ADR for a specific package.
Eva then routes the brief to Cal for ADR production.

<task>Produce a migration ADR brief for upgrading [package] from [current] to [target].</task>

<constraints>
- Scope this invocation to the named package only.
- Fetch the full changelog/release notes for the version range.
- Grep the entire codebase for every usage of APIs that are removed or changed.
- Produce a structured brief: affected APIs, usage locations (file:line), suggested migration approach per API, estimated effort (low/medium/high).
- This brief is the input to Cal's ADR production — it must be precise and complete.
- Never modify files.
</constraints>

<output>Migration ADR brief: package + version range, breaking changes table, usage inventory (file:line per API), migration approach, estimated effort, open questions for Cal. DoR and DoD sections.</output>

</template>
```

**Acceptance criteria:**
- Both files updated with both templates.
- Template IDs are `deps-scan` and `deps-migration-brief`.
- Templates follow the established XML tag format (task, constraints, output).

**Estimated complexity:** Low.

---

### Step 6: Setup Step 6d (`skills/pipeline-setup/SKILL.md`)

**File to modify:**
- `skills/pipeline-setup/SKILL.md`

Add Step 6d block after the existing Step 6c (CI Watch) block, before the Brain setup offer.

**Content to add:**

```
### Step 6d: Deps Agent Opt-In

After the CI Watch offer (whether user said yes or no), offer the optional Deps agent:

> Would you also like to enable the **Deps agent** -- predictive dependency management?
> It scans your dependencies for CVEs, checks for outdated packages, and predicts
> breakage risk before you upgrade. No external tools required beyond your existing
> package managers. Optional -- the pipeline works fine without it.

**If user says yes:**

1. Set `deps_agent_enabled: true` in `.claude/pipeline-config.json`.
2. Copy `source/shared/agents/deps.md` to `.claude/agents/deps.md`.
3. Copy `source/commands/deps.md` to `.claude/commands/deps.md`.
4. Print: "Deps agent: enabled. Use /deps to scan your dependencies."

**Idempotency:** If `deps_agent_enabled` already exists in `pipeline-config.json`
and is `true`, skip mutation and inform: "Deps agent is already enabled." If it
exists and is `false`, confirm before changing.

**If user says no:** Skip entirely. `deps_agent_enabled` remains `false`.
Print: "Deps agent: not enabled"

**Installation manifest addition (conditional):**

| Template Source | Destination | Install When |
|----------------|-------------|-------------|
| `source/shared/agents/deps.md` | `.claude/agents/deps.md` | User enables Deps in Step 6d |
| `source/commands/deps.md` | `.claude/commands/deps.md` | User enables Deps in Step 6d |
```

Also update the **summary printout** in Step 6 to add a line:
```
Deps agent: [enabled | not enabled]
```

And update the file count in the summary from "40 mandatory files" to remain accurate (the new files are conditional, not mandatory — no count change needed).

**Acceptance criteria:**
- Step 6d block exists in SKILL.md, positioned after Step 6c and before the Brain setup offer.
- The block follows the exact pattern of Step 6a (Sentinel): offer text, yes-path with numbered steps, idempotency check, no-path, conditional manifest table.
- The step sets both the config flag AND copies both files (persona + command).
- The summary printout line is added.

**Estimated complexity:** Low.

---

## Comprehensive Test Specification

### Step 1 Tests: Agent Persona

| ID | Category | Description |
|----|----------|-------------|
| T-0015-001 | Happy | `source/shared/agents/deps.md` exists and contains YAML frontmatter with `name: deps` |
| T-0015-002 | Happy | `.claude/agents/deps.md` exists and its content is identical to `source/shared/agents/deps.md` |
| T-0015-003 | Happy | `disallowedTools` frontmatter includes `Write`, `Edit`, `MultiEdit` |
| T-0015-004 | Happy | Persona contains `<identity>`, `<required-actions>`, `<workflow>`, `<tools>`, `<constraints>`, `<output>` tags |
| T-0015-005 | Happy | Persona contains an `<examples>` tag with at least two examples (missing tool skip + breakage prediction) |
| T-0015-006 | Happy | `<tools>` section lists Bash, Read, Grep, Glob, WebSearch, WebFetch and no Write/Edit tools |
| T-0015-007 | Happy | `<workflow>` encodes the three phases: Detect, Scan, Report |
| T-0015-008 | Happy | `<constraints>` includes "if command hangs, STOP — do not retry" |
| T-0015-009 | Happy | `<constraints>` includes "Never modify files" |
| T-0015-010 | Happy | `<constraints>` includes WebFetch unavailability degradation instruction |
| T-0015-011 | Happy | `<output>` specifies four sections: CVE Alerts, Needs Review, Safe to Upgrade, No Action Needed |
| T-0015-012 | Happy | `<workflow>` encodes all six edge cases from spec §Edge Cases |
| T-0015-013 | Happy | `<constraints>` contains an explicit Bash command whitelist (e.g., `npm outdated`, `pip list`, `cargo outdated`, `go list`, `npm audit`, `pip-audit`, `cargo audit`) and an explicit prohibition on filesystem-modifying commands (e.g., `npm install`, `pip install`, `cargo update`) |
| T-0015-014 | Happy | `<workflow>` Go ecosystem handling states explicitly that no Go CVE audit tool is available, `go list -m -u all` is used for outdated detection only, and the CVE section for Go is omitted with a noted gap in the report |
| T-0015-015 | Failure | Persona does NOT include any Write tool in `<tools>` section |
| T-0015-016 | Failure | Persona does NOT include any Edit tool in `<tools>` section |
| T-0015-017 | Security | `enforce-paths.sh` catch-all (`*` case) blocks a Write tool call from agent_type `deps` — exit code 2 |
| T-0015-018 | Security | `enforce-paths.sh` catch-all blocks an Edit tool call from agent_type `deps` — exit code 2 |
| T-0015-019 | Boundary | Eva boot-sequence discovery scan detects `deps` as a non-core discovered agent (not in core constant list) |
| T-0015-020 | Regression | `name: deps` does not appear in the core agent constant list in `agent-system.md` (would shadow discovery) |

### Step 2 Tests: Slash Command

| ID | Category | Description |
|----|----------|-------------|
| T-0015-021 | Happy | `source/commands/deps.md` exists with YAML frontmatter `name: deps` |
| T-0015-022 | Happy | `.claude/commands/deps.md` exists with identical content to source |
| T-0015-023 | Happy | Command file describes Flow A (scan and report): checks `deps_agent_enabled`, invokes Deps subagent, presents report |
| T-0015-024 | Happy | Command file describes Flow B (migration ADR brief): invokes Deps with scoped brief template, Eva routes to Cal |
| T-0015-025 | Failure | Command file includes a gate: when `deps_agent_enabled: false`, respond with "not enabled" message and stop |
| T-0015-026 | Boundary | Command file format matches `debug.md` structure (has `<identity>` or equivalent behavior block, not raw prose) |

### Step 3 Tests: Config Flag

| ID | Category | Description |
|----|----------|-------------|
| T-0015-027 | Happy | `source/pipeline/pipeline-config.json` contains `"deps_agent_enabled": false` |
| T-0015-028 | Happy | `.claude/pipeline-config.json` contains `"deps_agent_enabled": false` |
| T-0015-029 | Happy | Both files remain valid JSON after modification (`jq . file` exits 0) |
| T-0015-030 | Regression | No existing fields in either config file are removed or renamed |
| T-0015-031 | Regression | `sentinel_enabled`, `agent_teams_enabled`, `ci_watch_enabled` fields are unchanged in both files |

### Step 4 Tests: Auto-Routing Update

| ID | Category | Description |
|----|----------|-------------|
| T-0015-032 | Happy | `source/rules/agent-system.md` subagent table contains a `Deps` row |
| T-0015-033 | Happy | `.claude/rules/agent-system.md` subagent table contains a `Deps` row (dual tree parity) |
| T-0015-034 | Happy | Auto-routing table in both files contains a row matching dependency-related intent to Deps |
| T-0015-035 | Happy | Auto-routing Deps row includes `deps_agent_enabled: true` gate condition |
| T-0015-036 | Happy | `no-skill-tool` gate in both files maps Deps to `.claude/agents/deps.md` |
| T-0015-037 | Failure | Auto-routing does NOT route deps intent when `deps_agent_enabled` is absent/false — Eva must present "not enabled" message |
| T-0015-038 | Boundary | Deps row in subagent table lists correct tools: Read, Glob, Grep, Bash (read-only), WebSearch, WebFetch |
| T-0015-039 | Regression | Sentinel row in subagent table is unchanged after Step 4 edits |
| T-0015-040 | Regression | Core agent constant list is unchanged (no `deps` entry in the core list) |

### Step 5 Tests: Invocation Templates

| ID | Category | Description |
|----|----------|-------------|
| T-0015-041 | Happy | `source/references/invocation-templates.md` contains `<template id="deps-scan">` block |
| T-0015-042 | Happy | `.claude/references/invocation-templates.md` contains `<template id="deps-scan">` block (dual tree parity) |
| T-0015-043 | Happy | `deps-scan` template contains `<task>`, `<constraints>`, `<output>` tags |
| T-0015-044 | Happy | `deps-scan` constraints include: skip missing ecosystems, degrade if WebFetch unavailable, stop on hang, no file modifications |
| T-0015-045 | Happy | `deps-scan` output specifies four risk sections and DoR/DoD sections |
| T-0015-046 | Happy | Both files contain `<template id="deps-migration-brief">` block |
| T-0015-047 | Happy | `deps-migration-brief` template is scoped to a single named package |
| T-0015-048 | Happy | `deps-migration-brief` output specifies: breaking changes table, usage inventory (file:line), migration approach, estimated effort |
| T-0015-049 | Regression | Existing template IDs (`sentinel-audit`, `distillator-compress`, etc.) are unchanged in both files |

### Step 6 Tests: Setup Step 6d

| ID | Category | Description |
|----|----------|-------------|
| T-0015-050 | Happy | `skills/pipeline-setup/SKILL.md` contains a `### Step 6d` block |
| T-0015-051 | Happy | Step 6d is positioned after Step 6c and before the Brain setup offer |
| T-0015-052 | Happy | Step 6d offer text matches the spec: CVE, outdated packages, breakage risk |
| T-0015-053 | Happy | Step 6d yes-path sets `deps_agent_enabled: true` in config |
| T-0015-054 | Happy | Step 6d yes-path copies `source/shared/agents/deps.md` to `.claude/agents/deps.md` |
| T-0015-055 | Happy | Step 6d yes-path copies `source/commands/deps.md` to `.claude/commands/deps.md` |
| T-0015-056 | Happy | Step 6d no-path leaves `deps_agent_enabled: false` and prints "Deps agent: not enabled" |
| T-0015-057 | Happy | Summary printout in Step 6 includes "Deps agent: [enabled | not enabled]" line |
| T-0015-058 | Failure | First-time setup where `deps_agent_enabled` key is entirely absent from `pipeline-config.json`: Step 6d treats absence as `false`, offers opt-in, and writes the key on acceptance — no KeyError or silent skip |
| T-0015-059 | Boundary | Idempotency: if `deps_agent_enabled: true` already set, Step 6d skips mutation and announces "already enabled" |
| T-0015-060 | Boundary | Idempotency: if `deps_agent_enabled: false` already set, Step 6d confirms before changing |
| T-0015-061 | Regression | Step 6a (Sentinel) block is unchanged after Step 6d insertion |
| T-0015-062 | Regression | Step 6b (Agent Teams) block is unchanged after Step 6d insertion |
| T-0015-063 | Regression | Step 6c (CI Watch) block is unchanged after Step 6d insertion |
| T-0015-064 | Regression | Brain setup offer remains positioned after Step 6d |

### Step N Telemetry

**Step 1 (Persona):**
Telemetry: Eva boot-sequence log announces "Discovered 1 custom agent(s): deps -- [description]". Trigger: every session boot when `deps_agent_enabled: true` and `.claude/agents/deps.md` exists. Absence means: agent file is missing or has malformed frontmatter.

**Step 2 (Slash command):**
Telemetry: When `/deps` is typed and `deps_agent_enabled: false`, Eva responds with "Deps agent is not enabled." message. When enabled, Eva announces "Routing to Deps for dependency scan." Trigger: user invokes `/deps`. Absence means: command file missing or Eva is not reading the command file correctly.

**Step 3 (Config flag):**
Telemetry: `jq .deps_agent_enabled .claude/pipeline-config.json` returns `false` (default) or `true` (after Step 6d). Absence means: config key was not written.

**Step 4 (Auto-routing):**
Telemetry: Eva announces routing decision when user asks a dep-related question: "Routing to Deps for dependency analysis." Trigger: auto-routing intent match. Absence means: routing row missing or `deps_agent_enabled` gate blocks silently without message.

**Step 5 (Invocation template):**
Telemetry: Eva's invocation prompt for Deps subagent includes the `deps-scan` template content (observable in the Agent tool call). Trigger: every Deps subagent invocation. Absence means: Eva is not loading invocation-templates.md before routing to Deps.

**Step 6 (Setup):**
Telemetry: After `/pipeline-setup` Step 6d acceptance, `jq .deps_agent_enabled .claude/pipeline-config.json` returns `true`, and both agent/command files exist. Trigger: user completes Step 6d opt-in. Absence means: Step 6d failed to write config or copy files.

---

### Contract Boundaries

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `source/shared/agents/deps.md` (agent persona) | Markdown with YAML frontmatter: `name: deps`, `disallowedTools`, XML-tagged behavior | Eva (subagent invocation via Agent tool), `/deps` command dispatch | Step 1 |
| `.claude/agents/deps.md` (installed persona) | Same as above — installed copy | Claude Code at subagent invocation time | Step 1 |
| `source/commands/deps.md` (slash command) | Markdown behavior descriptor: Flow A + Flow B, `deps_agent_enabled` gate | Eva reads when user types `/deps` | Step 2 |
| `deps-scan` template (invocation-templates.md) | XML `<template>` with `<task>`, `<constraints>`, `<output>` | Eva constructs Deps subagent invocation prompt | Step 5 |
| `deps-migration-brief` template | XML `<template>` scoped to single package | Eva constructs migration brief invocation, then routes to Cal | Step 5 |
| `deps_agent_enabled` flag (pipeline-config.json) | Boolean JSON field | SKILL.md Step 6d install gate, Eva auto-routing gate, `/deps` command gate | Step 3 |
| Deps report (agent output) | Structured report: CVE Alerts + Needs Review + Safe to Upgrade + No Action Needed sections | Eva presents to user; migration brief section routes to Cal → Cal produces ADR | Step 1 |
| Migration ADR brief (agent output subset) | Structured brief: breaking changes table + usage inventory + migration approach + effort | Cal (ADR production subagent), invoked by Eva after user confirms | Step 2 |

### Wiring Coverage

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| `source/shared/agents/deps.md` | Persona template | `/pipeline-setup` copies to `.claude/agents/deps.md`; Eva invokes as subagent | Step 1, Step 6 |
| `.claude/agents/deps.md` | Installed persona | Claude Code loads for Deps subagent context window | Step 1 |
| `source/commands/deps.md` | Command behavior descriptor | `/pipeline-setup` copies to `.claude/commands/deps.md`; Claude Code loads when user types `/deps` | Step 2, Step 6 |
| `deps_agent_enabled` (pipeline-config.json) | Boolean | Eva auto-routing (Step 4), `/deps` command gate (Step 2), Step 6d install check | Step 3 |
| `deps-scan` template | Invocation template | Eva uses to construct Deps subagent invocation | Step 5 |
| `deps-migration-brief` template | Invocation template | Eva uses to construct migration-scoped Deps invocation, then routes result to Cal | Step 5 |
| Deps report | Structured output | Eva presents to user directly; migration brief routes to Cal | Step 1 (persona defines shape), Step 2 (command defines dispatch) |

No orphan producers. Every file created in Steps 1–3 has a consumer identified in the same or earlier step.

---

## Data Sensitivity

No data stores involved. Deps reads public package registry metadata and local dependency manifests. Dependency manifests may contain private registry URLs or internal package names — these are read-only and never exfiltrated beyond the report output. The report is presented to the user in the same session. No fields require `auth-only` tagging.

---

## Notes for Colby

**Dual tree discipline:** Every file created in `source/` must be mirrored to `.claude/` with identical content. Colby creates both in the same step. Do not create one and forget the other — Roz will grep both directories.

**Enforce-paths.sh catch-all:** No hook changes are needed. The `*` case at line 112 of `enforce-paths.sh` already blocks any agent type not explicitly listed. `deps` is not listed, so it falls through to the catch-all and Write/Edit are blocked mechanically. Verify this by reading the actual file before implementation (do not assume the line number is still 112 after any other changes in the same pipeline run).

**Agent discovery and the core constant list:** The core agent constant in `agent-system.md` is the literal list: `cal, colby, roz, ellis, agatha, robert, sable, investigator, distillator`. Do NOT add `deps` to this list. `deps` is a discovered agent, not a core agent. Adding it to the core list would break discovery.

**Config field ordering:** The convention is: sentinel_enabled, agent_teams_enabled, ci_watch_enabled, ci_watch_max_retries, ci_watch_poll_command, ci_watch_log_command. Add `deps_agent_enabled` after `ci_watch_log_command`. Both config files (`source/pipeline/pipeline-config.json` and `.claude/pipeline-config.json`) must be updated in the same step.

**SKILL.md Step 6d positioning:** The Brain setup offer paragraph starts with "After the CI Watch offer (whether user said yes or no), ask the user:" — Step 6d must be inserted before this paragraph. The Brain offer must remain the last item before `/pipeline-setup` ends.

**Migration brief → Cal handoff:** When Eva routes the migration brief to Cal, Cal receives the brief as context (not raw agent output). Eva constructs a Cal invocation using the standard `architect-adr` template, with the migration brief in the `<context>` tag. This handoff is Eva's responsibility, not Deps'. Deps produces the brief and stops.

**WebSearch/WebFetch conditional:** These tools may not be available in all environments or may be rate-limited. The persona `<constraints>` must make the degradation explicit and observable — not a silent skip, but a noted gap in the report: "Changelog analysis unavailable: WebFetch not accessible. CVE and version data are from local audit tools only."

**Bash commands are read-only by intent, not enforcement:** The persona uses Bash for `npm outdated`, `npm audit`, etc. These are analysis commands. The `<constraints>` section must include an explicit whitelist of permitted commands (`npm outdated`, `npm audit`, `pip list --outdated`, `pip-audit`, `cargo outdated`, `cargo audit`, `go list -m -u all`) and an explicit blocklist of prohibited commands (`npm install`, `npm update`, `pip install`, `pip install --upgrade`, `cargo update`, `go get`, `go mod tidy`). Since Bash is not in `disallowedTools`, this constraint is behavioral — Roz verifies the language is unambiguous (T-0015-013). Do not use vague language like "read-only Bash" without spelling out the exact commands.

**Go CVE gap — explicit persona requirement:** Go has no standard CLI CVE audit tool equivalent to `npm audit` or `pip-audit`. The `<workflow>` must state this explicitly: use `go list -m -u all` for outdated detection only; omit the CVE subsection for Go; include a noted gap in the report ("Go CVE scan unavailable: no standard audit tool. Use Dependabot or manual advisory review."). The gap must appear in the report body, not be silently skipped (T-0015-014).

---

## DoD: Verification

| # | Requirement | ADR Step | Evidence |
|---|-------------|----------|----------|
| R1 | Agent persona at `source/shared/agents/deps.md` installed to `.claude/agents/deps.md` | Step 1 | Both files exist, content identical, T-0015-001/002 |
| R2 | `deps_agent_enabled` flag default false in both config files | Step 3 | `jq .deps_agent_enabled` on both files, T-0015-027/028 |
| R3 | Offered as opt-in during /pipeline-setup Step 6d | Step 6 | Step 6d block exists, correct positioning, T-0015-050/051 |
| R4 | /deps slash command invokes the agent | Step 2 | Command file exists, Flow A described, T-0015-021/023 |
| R5 | Agent scans dependency manifests | Step 1 | Workflow Detect+Scan phases in persona, T-0015-007 |
| R6 | CVE scanning via audit tools | Step 1 | `<workflow>` encodes npm audit, pip-audit, cargo audit, T-0015-007 |
| R7 | Breakage prediction via changelog+usage analysis | Step 1 | `<workflow>` Scan phase: WebFetch + Grep, T-0015-007 |
| R8 | Migration ADR brief handed to Cal | Step 2 | Flow B in command file + `deps-migration-brief` template, T-0015-024/046 |
| R9 | Agent is read-only | Step 1 | `disallowedTools` frontmatter + enforce-paths.sh catch-all, T-0015-017/018 |
| R10 | Auto-routing for dep-related questions | Step 4 | Auto-routing table row in agent-system.md, T-0015-034 |
| R11 | Report format grouped by risk | Step 1 | `<output>` tag in persona, T-0015-011 |
| R12 | Edge case handling | Step 1 | `<workflow>` edge cases section, T-0015-012 |
| R13 | SKILL.md Step 6d updated | Step 6 | Step 6d block exists, T-0015-050/064 |
| R14 | `invocation-templates.md` has deps-scan template | Step 5 | Template block exists in both files, T-0015-041/042 |
| R15 | agent-system.md subagent table updated | Step 4 | Deps row in both files, T-0015-032/033 |

**Architectural decisions not in the spec:**
- Deps is a discovered agent (not a core agent). This was a deliberate choice to avoid bloating the core constant list with opt-in agents. The implication: `deps` is announced by Eva's boot discovery scan when installed, which is correct behavior.
- Two invocation templates (`deps-scan` and `deps-migration-brief`) rather than one parameterized template. Reason: the two flows have meaningfully different constraints and output shapes. A single template with conditionals would be harder for Eva to apply correctly.
- No SKILL.md file count update needed (new files are conditional installs, same as Sentinel).

**Rejected alternatives:**
- Extending Sentinel rejected: information asymmetry incompatibility and lifecycle mismatch (Sentinel is pipeline-phase-gated; Deps is on-demand).
- Plugin skill (main thread) rejected: execution complexity (multi-tool Bash + WebFetch sequences) belongs in a subagent context window.

**Technical constraints discovered:**
- enforce-paths.sh catch-all covers `deps` with no changes needed — verified by reading the actual file (line 112, `*` case).
- Dual tree discipline must be applied to agent-system.md (both `source/rules/` and `.claude/rules/`) — Colby must update both.
- `deps` must not appear in the core agent constant list — Eva's discovery scan relies on this exclusion.

---

ADR saved to `/Users/sfeirr/projects/atelier-pipeline/docs/architecture/ADR-0015-deps-agent.md`.
