---
name: darwin
description: Darwin pipeline evolution flow -- analyzes telemetry, evaluates agent fitness, proposes structural improvements. Use when checking pipeline health, agent performance, or requesting improvement proposals.
---
<!-- Part of atelier-pipeline. Customize project-specific values in CLAUDE.md -->

<identity>
This is the Darwin flow -- Eva invokes the Darwin subagent to analyze pipeline
telemetry, evaluate agent fitness, and produce structural improvement proposals.
Eva orchestrates. Darwin analyzes. Eva presents proposals individually for user
approval. Approved changes are routed to Colby for implementation.
</identity>

<behavior>
## Pre-Flight Gate (Triple Gate)

Eva checks three gates before proceeding. If `darwin_enabled` is absent from
the config, treat it as false (absent = false).

### Gate 1: Config Flag

Read `darwin_enabled` from `{config_dir}/pipeline-config.json`.

If `darwin_enabled: false` or not present (absent treated as false):
- Respond: "Darwin is not enabled. Run `/pipeline-setup` and enable it in
  Step 6e to activate pipeline evolution analysis."
- Stop. Do not invoke Darwin.

### Gate 2: Brain Availability

Check `brain_available` from pipeline state.

If `brain_available: false` or brain is not available:
- Respond: "Darwin requires brain telemetry data. Brain is not available.
  Set up the brain with `/brain-setup` first."
- Stop. Do not invoke Darwin.

### Gate 3: Telemetry Data Minimum (5 Pipelines)

Query brain for Tier 3 telemetry summaries (`agent_search` with telemetry
filter, limit 10). Count results.

If fewer than 5 pipeline telemetry summaries:
- Respond: "Insufficient data for Darwin analysis. Need 5+ pipelines of
  telemetry data. Currently have {N}. Run more pipelines to build up
  telemetry before invoking Darwin."
- Stop. Do not invoke Darwin.

All three gates pass: proceed to the appropriate flow below.

## Flow A: Full Pipeline Analysis

Triggered when the user types `/darwin`, asks about pipeline health, agent
performance, "how are agents performing", "what needs improving", or similar.

1. Eva pre-fetches brain context for Darwin:
   - `agent_search` with `source_phase: 'telemetry'`, telemetry tier 3, limit 10
   - `agent_search` with `thought_type: 'decision'`, metadata filter for
     `darwin_proposal_id` (prior Darwin proposals and outcomes)
2. Eva invokes Darwin subagent with the `darwin-analysis` invocation template,
   injecting telemetry data in `<brain-context>`.
3. Darwin produces a structured Darwin Report with FITNESS ASSESSMENT,
   PROPOSED CHANGES, and UNCHANGED sections.
4. Eva presents the report to the user.
5. Eva presents each proposed change individually for user review. Each
   proposal is presented separately -- no merging or batching of proposals.
6. For each proposal, the user can:
   - **Approve**: Eva captures the approval in brain (`agent_capture` with
     `thought_type: 'decision'`, `source_agent: 'eva'`, metadata:
     `darwin_proposal_id`, `target_metric`, `target_file`, `escalation_level`,
     `expected_impact`). Eva routes to Colby with the `darwin-edit-proposal`
     invocation template.
   - **Reject** (with reason): Eva captures the rejection in brain
     (`agent_capture` with `thought_type: 'rejection'`, `source_agent: 'eva'`,
     metadata: `darwin_proposal_id`, `rejection_reason`, `rejected: true`).
   - **Modify** (reject with feedback + repropose): This is a reject-then-repropose
     cycle. Eva captures the rejection with the user's modification feedback as
     the reason, then re-invokes Darwin with the feedback for a revised proposal
     on the same target. The revised proposal goes through the same
     approve/reject/modify flow.

## Flow B: Targeted Single-Agent Analysis

Triggered when the user asks about a specific agent's performance:
"How is Colby performing?", "Is Roz struggling?", "Check Cal's fitness."

1. Same triple gate check as Flow A.
2. Eva invokes Darwin with the `darwin-analysis` template, but adds a
   constraint scoping the analysis to the named agent only.
3. Darwin produces a scoped report for that single agent.
4. Same proposal presentation and approval flow as Flow A.

## Auto-Routing (Without Typing /darwin)

Eva also triggers this flow (if `darwin_enabled: true`) when the auto-routing
table classifies user intent as pipeline-analysis-related:
- "Analyze the pipeline"
- "How are agents performing"
- "Pipeline health"
- "Run Darwin"
- "What needs improving"

The same triple gate (darwin_enabled, brain, 5 pipelines) applies to
auto-routed requests.
</behavior>

<output>
The Darwin flow produces:
- Flow A: Darwin Report (FITNESS ASSESSMENT | PROPOSED CHANGES | UNCHANGED) +
  per-proposal approval/rejection results
- Flow B: Scoped Darwin Report for a single agent + per-proposal results
</output>

<constraints>
- Eva does not analyze telemetry herself -- Darwin is the analysis agent.
- Darwin does not modify files -- analysis and reporting only.
- The triple gate (darwin_enabled + brain + 5 pipelines) is mandatory -- never
  bypass it silently. If `darwin_enabled` key is absent, treat as false.
- Each proposal is presented to the user individually -- no batching.
- Approved changes are routed to Colby one at a time via `darwin-edit-proposal`.
- Rejected proposals are captured in brain with the rejection reason.
- Modified proposals follow a reject-then-repropose cycle with user feedback.
</constraints>