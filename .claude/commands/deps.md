---
name: deps
description: Dependency scan flow -- Deps scans manifests, checks CVEs, predicts upgrade breakage. Use when checking outdated dependencies, CVE exposure, or requesting a migration ADR brief.---
<!-- Part of atelier-pipeline. Customize project-specific values in CLAUDE.md -->

<identity>
This is the deps flow -- Eva invokes the Deps subagent to scan dependency
manifests, check CVEs, predict breakage risk, and produce a risk-grouped report.
Eva orchestrates. Deps analyzes. Eva optionally routes a migration brief to Cal.
</identity>

<behavior>
## Pre-Flight Gate

Eva reads `deps_agent_enabled` from `.claude/pipeline-config.json` before
proceeding.

If `deps_agent_enabled: false`:
- Respond: "Deps agent is not enabled. Run `/pipeline-setup` and enable it in
  Step 6d to activate dependency scanning."
- Stop. Do not invoke Deps.

If `deps_agent_enabled: true`, proceed to the appropriate flow below.

## Flow A: Full Dependency Scan

Triggered when the user types `/deps`, asks about outdated dependencies,
CVE exposure, "check my deps," or similar.

1. Eva invokes Deps subagent with the `deps-scan` invocation template.
2. Deps produces a risk-grouped report: CVE Alerts, Needs Review, Safe to
   Upgrade, No Action Needed.
3. Eva presents the report to the user.
4. If the user asks "can you propose a migration ADR for [package]?", Eva
   transitions to Flow B.

## Flow B: Migration ADR Brief

Triggered when the user asks for a migration ADR for a specific package
(or after reviewing a Flow A report).

1. Eva invokes Deps subagent with the `deps-migration-brief` invocation
   template, scoped to the named package and version.
2. Deps produces a structured migration brief: breaking changes, files
   requiring migration, estimated effort, suggested migration order.
3. Eva receives the brief, then routes to Cal with the brief as context
   for ADR production.
4. Cal produces the migration ADR using the brief as a pre-scoped input.

## Auto-Routing (Without Typing /deps)

Eva also triggers this flow (if `deps_agent_enabled: true`) when the
auto-routing table classifies user intent as dependency-related:
- "Is [package] safe to upgrade?"
- "Do we have any CVEs?"
- "What dependencies need updates?"
- "Check my dependencies"

The same `deps_agent_enabled` gate applies to auto-routed requests.
</behavior>

<output>
The deps flow produces:
- Flow A: Deps risk-grouped report (CVE Alerts | Needs Review | Safe to Upgrade | No Action Needed)
- Flow B: Migration ADR brief (from Deps), then Cal ADR (from Cal)
</output>

<constraints>
- Eva does not scan dependencies herself -- Deps is the analysis agent.
- Deps does not modify files -- analysis and reporting only.
- The `deps_agent_enabled` gate is mandatory -- never bypass it silently.
- Migration ADR briefs always route through Cal for ADR production.
</constraints>
