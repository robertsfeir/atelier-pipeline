# Architecture Decision Records

| ADR | Title | Status | Location |
|-----|-------|--------|----------|
| [ADR-0001](../brain/ADR-0001-atelier-brain.md) | Atelier Brain -- Persistent Institutional Memory | Proposed | `docs/brain/` |
| [ADR-0002](ADR-0002-team-collaboration.md) | Team Collaboration Enhancements | Accepted | |
| [ADR-0003](ADR-0003-code-quality-overhaul.md) | Code Quality and Security Overhaul | Proposed | |
| [ADR-0004](ADR-0004-pipeline-evolution.md) | Pipeline Evolution | Proposed | |
| [ADR-0005](ADR-0005-xml-prompt-structure.md) | XML-Based Prompt Structure | Accepted | |
| [ADR-0006](ADR-0006-xml-structure-rules-references.md) | XML Tag Migration for Rules and References | Accepted | |
| [ADR-0007](ADR-0007-dor-dod-warn-hook.md) | SubagentStop Warning Hook for DoR/DoD | Proposed | |
| [ADR-0008](ADR-0008-agent-discovery.md) | Filesystem-Based Agent Discovery | Proposed | |
| [ADR-0009](ADR-0009-sentinel-security-agent.md) | Sentinel Security Audit Agent | Proposed | |
| [ADR-0010](ADR-0010-agent-teams.md) | Agent Teams Parallel Execution | Proposed | |
| [ADR-0011](ADR-0011-observation-masking.md) | Observation Masking and Context Hygiene | Proposed | |
| [ADR-0012](ADR-0012-compaction-api.md) | Compaction API Integration | Proposed | |
| [ADR-0013](ADR-0013-ci-watch.md) | CI Watch Self-Healing CI | Proposed | |
| [ADR-0014](ADR-0014-agent-telemetry-dashboard.md) | Agent Telemetry Dashboard | Proposed | |
| [ADR-0015](ADR-0015-deps-agent.md) | Deps Agent | Proposed | |
| [ADR-0016](ADR-0016-darwin-self-evolving-pipeline.md) | Darwin Self-Evolving Pipeline | Proposed | |
| [ADR-0017](ADR-0017-brain-hardening.md) | Brain Hardening | Proposed | |
| [ADR-0018](ADR-0018-dashboard-integration.md) | Dashboard Integration | Proposed | |
| [ADR-0019](ADR-0019-cursor-port.md) | Cursor Port | Proposed | |
| [ADR-0020](active/ADR-0020-wave2-hook-modernization.md) | Wave 2 Hook Modernization | Proposed | `active/` |
| [ADR-0021](active/ADR-0021-brain-wiring.md) | Mechanical Brain Wiring | Proposed | `active/` |
| [ADR-0022](ADR-0022-wave3-native-enforcement-redesign.md) | Wave 3 Native Enforcement Redesign | Proposed | |
| [ADR-0023](ADR-0023-agent-specification-reduction.md) | Agent Specification Reduction | Proposed | |
| [ADR-0024](ADR-0024-mechanical-brain-writes.md) | Mechanical Brain Writes | Proposed | |
| [ADR-0025](ADR-0025-mechanical-telemetry-extraction.md) | Mechanical Telemetry Extraction | Proposed | |
| [ADR-0026](ADR-0026-beads-provenance-records.md) | Beads Provenance Records | Proposed | |
| [ADR-0027](ADR-0027-brain-hydrate-scout-fanout.md) | Brain-Hydrate Scout Fan-Out | Proposed | |
| [ADR-0028](ADR-0028-named-stop-reason-taxonomy.md) | Named Stop Reason Taxonomy | Proposed | |
| [ADR-0029](ADR-0029-token-budget-estimate-gate.md) | Token Budget Estimate Gate | Proposed | |
| [ADR-0030](ADR-0030-token-exposure-probe-and-accumulator.md) | Token Exposure Probe and Accumulator | Accepted | |
| [ADR-0031](ADR-0031-permission-audit-trail.md) | Permission Audit Trail | Proposed | |
| [ADR-0032](ADR-0032-pipeline-state-session-isolation.md) | Pipeline State Session Isolation | Approved | |
| [ADR-0033](ADR-0033-hook-enforcement-audit-fixes.md) | Hook Enforcement Audit Fixes | Accepted | |
| [ADR-0034](ADR-0034-gauntlet-remediation.md) | Gauntlet 2026-04-11 Remediation | Proposed | |
| [ADR-0035](ADR-0035-wave4-consumer-wiring-and-s4-resolution.md) | Wave 4 Consumer Wiring and S4 Resolution | Proposed | |
| [ADR-0036](ADR-0036-wave5-documentation-sweep.md) | Wave 5 Documentation Sweep | Proposed | |
| [ADR-0037](ADR-0037-wave6-dashboard-a11y-cursor-parity-specs.md) | Wave 6 Dashboard A11y and Cursor Parity Specs | Proposed | |
| [ADR-0041](ADR-0041-effort-per-agent-map.md) | Effort-Per-Agent Map (Task-Class Tier Model) | Accepted | |

**Convention:** When creating a new ADR, add a row to this table in the same commit. The table is the primary navigation aid for finding ADRs; an ADR not listed here is effectively invisible to contributors browsing the index.

**Location notes:**
- ADR-0001 lives in `docs/brain/` alongside the brain-specific documentation, not in `docs/architecture/`.
- ADR-0020 and ADR-0021 live in `docs/architecture/active/` because they represent in-progress multi-wave work.
- All other ADRs live in `docs/architecture/` (this directory).
