## DoR: Requirements Extracted

| # | Requirement | Source |
|---|-------------|--------|
| 1 | Opt-in via Sentinel-style pattern (Step 6d, config flag, conditional install) | User decision (brain memory) |
| 2 | Agent persona in source/agents/ | User decision |
| 3 | Scan for outdated dependencies | Issue #20 |
| 4 | Cross-reference CVEs and changelogs | Issue #20 |
| 5 | Predict whether upgrades will break the codebase | Issue #20 |
| 6 | Propose migration ADRs for risky upgrades | Issue #20 |
| 7 | Support common ecosystems: npm, pip, cargo, go mod | Implied |
| 8 | Invokable via `/deps` command or auto-routed by Eva | Agent system convention |

**Retro risks:** None directly applicable.

---

# Feature Spec: Predictive Dependency Management Agent

**Author:** Robert (CPO) | **Date:** 2026-03-29
**Status:** Draft
**Issue:** #20

## The Problem

Fear-driven deferral of dependency upgrades. Teams avoid upgrading because they can't predict breakage. When they do upgrade, it's reactive (Dependabot PR broke something) rather than proactive. The result: security vulnerabilities linger, technical debt compounds, and upgrades become increasingly painful the longer they're deferred.

## Who Is This For

Developers using the pipeline who want proactive dependency management without the risk of blind upgrades. Especially valuable for projects with large dependency trees where manual changelog review is impractical.

## Business Value

- **Reduced security exposure** — CVEs surfaced before they become incidents
- **Lower upgrade cost** — small, frequent upgrades vs. big-bang migrations
- **Informed decisions** — risk assessment before committing to an upgrade
- **Time savings** — automated changelog/CVE cross-referencing

**KPIs:**
| KPI | Measurement | Timeframe | Acceptance |
|-----|------------|-----------|------------|
| Outdated deps detected | Count of deps behind latest | Per scan | All outdated deps identified |
| CVE coverage | Known CVEs surfaced / total known CVEs | Per scan | > 90% |
| Breakage prediction accuracy | Predicted-safe upgrades that actually broke / total predicted-safe | Per quarter | < 10% false safe |

## User Stories

1. **As a developer**, I want to run `/deps` and see which dependencies are outdated, which have CVEs, and which are safe to upgrade.
2. **As a developer**, for risky upgrades (major versions, breaking changes), I want the agent to propose a migration ADR so Cal can architect the upgrade.
3. **As a developer**, I want the agent to predict breakage by analyzing my usage patterns against changelog breaking changes.

## User Flow

### Happy Path (scan and report)
```
User: /deps
Eva: Routing to Deps agent for dependency analysis.

Deps Agent scans → produces report:

Dependency Report
=================
Safe to upgrade (no breaking changes, no CVE):
  express 4.18.2 → 4.19.1 (patch, changelog: bug fixes only)
  lodash 4.17.21 → 4.17.22 (patch, CVE-2024-XXXX fixed)

Needs review (breaking changes detected):
  react 18.3.1 → 19.0.0 (major, 12 breaking changes)
    Your usage: createRoot (safe), findDOMNode (REMOVED in 19)
    Risk: HIGH — you use findDOMNode in 3 files
    Recommendation: Migration ADR needed

  pg 8.11.3 → 8.12.0 (minor, new connection pool defaults)
    Your usage: Pool constructor with custom config (safe)
    Risk: LOW — your config overrides changed defaults
    Recommendation: Safe to upgrade, verify pool behavior

CVE alerts (upgrade immediately):
  axios 1.6.2 — CVE-2024-XXXXX (SSRF, severity: HIGH)
    Fixed in: 1.6.3
    Recommendation: Patch upgrade, no breaking changes

No action needed: 47 dependencies up to date.
```

### Migration ADR Flow
```
User: "Propose a migration ADR for the React 19 upgrade"
Eva: Routes to Deps agent for migration analysis, then Cal for ADR.

Deps Agent produces migration brief → Eva hands to Cal → Cal writes ADR
```

## How It Works

The Deps agent uses existing tools:
- **Bash** — runs `npm outdated`, `pip list --outdated`, `cargo outdated`, `go list -m -u all`
- **Bash** — runs `npm audit`, `pip-audit`, `cargo audit` for CVE scanning
- **WebSearch/WebFetch** — fetches changelogs and release notes for outdated deps
- **Grep** — scans codebase for usage patterns of APIs that have breaking changes
- **Read** — reads dependency manifests (package.json, requirements.txt, Cargo.toml, go.mod)

The agent does NOT modify any files. It produces a report. If a migration ADR is needed, Eva routes to Cal.

## Edge Cases and Error Handling

| Edge Case | Handling |
|-----------|----------|
| No dependency manifest found | Report: "No package.json, requirements.txt, Cargo.toml, or go.mod found." |
| Package manager not installed | Report which tool is missing: "npm not found — install Node.js to scan JS deps." Skip that ecosystem. |
| No internet access (offline) | CVE and changelog checks fail gracefully. Report outdated deps from local data only. |
| Monorepo with multiple manifests | Scan all manifests found. Group report by directory. |
| Private registry deps | Use existing auth. If auth fails, report: "Cannot check [dep] — private registry auth failed." |
| No outdated deps | Report: "All dependencies up to date. No CVEs found." |

## Acceptance Criteria

| # | Criterion | Measurable |
|---|-----------|------------|
| 1 | Agent persona exists at source/agents/deps.md | File inspection |
| 2 | `deps_agent_enabled` flag in pipeline-config.json, default false | Config inspection |
| 3 | Offered as opt-in during /pipeline-setup Step 6d | Setup flow observation |
| 4 | /deps command invokes the agent | Command observation |
| 5 | Agent scans dependency manifests for outdated packages | Report output |
| 6 | Agent checks for known CVEs via audit tools | Report output |
| 7 | Agent predicts breakage by cross-referencing usage with changelogs | Report output |
| 8 | Agent proposes migration ADR for risky upgrades | Report output |
| 9 | Agent is read-only (no file modifications) | Hook enforcement |
| 10 | Auto-routing: Eva routes dep-related questions to Deps agent | Routing observation |

## Scope

### In Scope
- Agent persona with dependency analysis workflow
- Setup Step 6d opt-in (Sentinel pattern)
- Config flag in pipeline-config.json
- /deps slash command
- Auto-routing for dependency-related questions
- Support: npm, pip, cargo, go mod
- CVE scanning via audit tools
- Breakage prediction via changelog + usage analysis
- Migration ADR brief (handed to Cal)

### Out of Scope
- Automatic dependency upgrades (report only, no file changes)
- Dependabot/Renovate integration
- License compliance scanning
- Transitive dependency analysis (direct deps only for first slice)
- Custom registry authentication setup

## Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Scan time | < 60s for projects with < 200 deps |
| Report readability | Grouped by risk level, actionable recommendations |
| No file modifications | Agent is read-only by default (enforce-paths.sh) |

## Dependencies

| Dependency | Status | Risk |
|------------|--------|------|
| Package managers (npm, pip, cargo, go) | External, user-installed | Low — skip unavailable ecosystems |
| Audit tools (npm audit, pip-audit, cargo audit) | External, user-installed | Low — CVE section skipped if missing |
| WebSearch/WebFetch for changelogs | Platform feature | Low — breakage prediction degrades without it |

## Risks and Open Questions

| Risk | Mitigation |
|------|------------|
| Changelog quality varies wildly | Focus on major version bumps where changelogs are most reliable. Minor/patch: trust semver. |
| CVE databases may have false positives | Report all, let user decide. Don't auto-classify severity. |
| Breakage prediction is inherently uncertain | Use conservative risk labels. "Needs review" is safer than "Safe to upgrade." |
| WebSearch/WebFetch may not be available | Degrade gracefully — report outdated deps and CVEs without changelog analysis. |

## Timeline Estimate

Single slice — Small sizing. Agent persona + setup + command + routing.

## DoD: Verification

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Agent persona | Pending | |
| 2 | Config flag | Pending | |
| 3 | Setup Step 6d | Pending | |
| 4 | /deps command | Pending | |
| 5 | Dep scanning | Pending | |
| 6 | CVE checking | Pending | |
| 7 | Breakage prediction | Pending | |
| 8 | Migration ADR brief | Pending | |
| 9 | Read-only enforcement | Pending | |
| 10 | Auto-routing | Pending | |
| 11 | Docs updated | Pending | |
