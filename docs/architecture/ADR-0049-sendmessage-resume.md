# ADR-0049: Subagent Resume via SendMessage

## Status
Accepted.

## Context
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is now enabled in this project, which
exposes the Agent tool's `SendMessage` capability — the documented mechanism
for continuing a previously spawned subagent with its context window intact.
Today, every Eva-driven follow-up to Sarah or Poirot spawns a fresh agent: the
new instance re-reads the ADR, re-greps for callers, re-walks the integration
surface. For Sarah (30 maxTurns, high effort, ADR production) and Poirot (50
maxTurns, high effort, blind diff review), the prior context is exactly the
expensive-to-rebuild artifact we're throwing away.

Two distinct use cases sit on top of `SendMessage`. The first — in-session
continuation — is unambiguously supported: Eva holds the `agentId` returned
by the most recent Agent tool invocation and re-targets the same agent later
in the same Claude Code session. The second — cross-session crash recovery —
requires the Claude Code runtime to persist subagent contexts across host
process restarts. That persistence behavior is undocumented for the Agent
tool and unverified for our deployment. `pipeline-state.md` already carries a
`session_id` field as the natural shelf for resume identifiers, but a stale
`agentId` written on disk only helps if the runtime can rehydrate it.

The decision pertains only to Sarah and Poirot. Colby builds in fresh worktree
contexts per unit (and per Teammate under Agent Teams) and Ellis runs short
sequential commits — neither benefits from resume, both are explicitly
excluded.

## Options Considered

**Option A — In-session resume only.** Eva captures `agentId` for Sarah and
Poirot in transient session memory (her own context, not state files). When
the same logical work unit needs a follow-up — Sarah revising an ADR after a
Poirot finding, Poirot doing a scoped re-run after Colby's fix — Eva calls
`SendMessage` against the captured `agentId` instead of spawning a new Agent.
On any session boundary (compaction, restart, crash) the `agentId` is
discarded and the next invocation starts fresh. This is the behavior the
Agent tool clearly supports today and matches the dominant value case (saving
re-reads within a single pipeline run).

**Option B — In-session plus persisted cross-session resume.** Same as A,
plus Eva writes `agentId` (and a target agent name) into `PIPELINE_STATUS` in
`pipeline-state.md` on every Sarah/Poirot invocation, and on session boot
attempts `SendMessage` against the persisted ID before falling back to a
fresh spawn. Buys crash recovery if the runtime persists subagent contexts;
adds wasted work and a confusing error mode if it doesn't. The fallback path
also has to handle a class of "stale agentId pointing at expired context"
that we can't distinguish from "agentId pointing at live context" without
trying.

**Option C — Do nothing.** Keep spawning fresh agents for every follow-up.
Cheap to keep, but every Poirot scoped re-run pays full re-read cost on a
50-maxTurn budget, and every Sarah revision re-walks the codebase. With the
v4 pipeline running Sarah and Poirot multiple times per Medium+ feature, this
is the option we're explicitly trying to leave behind.

## Decision
Implement Option A — in-session resume for Sarah and Poirot only. Eva
captures the `agentId` returned by the Agent tool for the most recent Sarah
invocation and the most recent Poirot invocation, holds it in her own context
(no state-file persistence), and uses `SendMessage` instead of a fresh Agent
spawn when the follow-up is a continuation of the same logical work unit.
Session boundaries reset to fresh-spawn behavior; cross-session crash
recovery is explicitly out of scope until Claude Code documents subagent
context persistence.

The continuation rule Eva follows: use `SendMessage` against the captured
`agentId` when (a) the agent is Sarah or Poirot, (b) the captured `agentId`
exists in the current session, and (c) the follow-up is one of the
recognized continuation triggers below. Otherwise spawn fresh via Agent.

Recognized continuation triggers:
- **Sarah:** ADR revision after a Poirot finding routed back per the
  "Poirot code QA (structural) → Sarah subagent (revise)" feedback-loop row;
  any `<task>` Eva would otherwise mark "revision" per Sarah's Revision Mode.
- **Poirot:** scoped re-run on a unit after Colby fixes a finding, per the
  "Poirot code QA (minor) → Colby fix → scoped re-run" and "fix → Poirot
  scoped rerun on the affected unit(s) only" rules in continuous QA.

Fresh-spawn cases (no `SendMessage`) include: a different feature, a
different ADR, a different wave's blind review, devil's-advocate mode (once
per pipeline, by design a fresh perspective), and any case where the prior
`agentId` has been discarded.

### Factual Claims
- `pipeline-state.md` PIPELINE_STATUS marker contains a `session_id` field but no `agent_id` field.
- `.claude/agents/sarah.md` declares `maxTurns: 30`, `effort: high`.
- `.claude/agents/investigator.md` declares `maxTurns: 50`, `effort: high`.
- The feedback-loop table in `source/shared/references/pipeline-operations.md` includes a "Poirot code QA (structural) → Sarah subagent (revise)" row and a "Poirot code QA (minor) → Colby fix scoped re-run" row.
- Continuous-QA section in `pipeline-operations.md` specifies "Eva invokes Poirot for a scoped rerun on the affected unit(s) only" after fix routing.
- Colby and Ellis are explicitly excluded from this decision; their persona files require no changes.

### LOC Estimate
~40 lines changed across 2 files (Eva orchestration rules in
`source/shared/rules/agent-system.md` or `source/shared/references/pipeline-operations.md`,
plus the matching invocation-template guidance). No persona changes for Sarah
or Poirot. No `pipeline-state.md` schema change.

## Rationale
Option A captures the value (skip re-reads on the most expensive, most-often-
revisited agents) without taking on the unknown-runtime-behavior risk of B.
Cross-session resume only pays off if the Claude Code runtime persists
subagent contexts across process restarts; we have no documented guarantee of
that, and the failure mode if it doesn't is "Eva tries SendMessage, gets a
stale-agent error, falls back to fresh spawn" — i.e., we paid coordination
overhead to land in C anyway. The right time to add B is after we've
confirmed runtime behavior with a deliberate test, not as speculative
infrastructure.

Holding `agentId` in Eva's context rather than `pipeline-state.md` is also
deliberate: state-file persistence implies cross-session validity, which we
are explicitly not claiming. If the value is in-session only, the storage
should be in-session only — that way the absence of an `agent_id` field on
disk is itself documentation that resume is not a recovery mechanism.

If continuation triggers misclassify and Eva sends a follow-up to the wrong
captured agent (Sarah's `agentId` used for a different feature's revision,
say), the failure shape is "wrong context surfaces in the ADR or report" —
caught by Poirot blind review on the resulting diff, but worth watching during
rollout. Discipline is enforced in the trigger rule, not in `SendMessage`
itself.

Out of scope: resume for Colby (fresh worktree per unit is the design),
Ellis (commits are short and stateless), discovered agents (per-agent
opt-in if needed later), and any persistence of `agentId` to disk.

## Falsifiability
Revisit this decision if any of the following hold:
- Claude Code documents (or we verify by experiment) that subagent contexts
  persist across host process restarts — at that point Option B becomes
  cheaply additive and we should add cross-session resume.
- Telemetry shows Sarah-revision or Poirot-scoped-rerun invocations are not
  measurably cheaper after rollout (e.g., re-read counts unchanged, turn
  consumption unchanged within ±10%) — the implementation isn't routing
  through `SendMessage` in practice and Option C was the honest answer all
  along.
- Wrong-context findings appear in Poirot blind review traceable to a
  misrouted `SendMessage` continuation more than once per ten pipelines —
  the trigger rule is too permissive and needs tightening or removal.

## Sources
- `.claude/agents/sarah.md` (lines 1-18, 139-150 — Revision Mode)
- `.claude/agents/investigator.md` (lines 1-13, 86-90 — scoped re-run context)
- `source/shared/pipeline/pipeline-state.md` (line 9 — current PIPELINE_STATUS schema)
- `source/shared/references/pipeline-operations.md` (lines 32-90 — continuous QA, lines 132-150 — feedback loops)
