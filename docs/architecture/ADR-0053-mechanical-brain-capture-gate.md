# ADR-0053: Mechanical Brain Capture via Three-Hook Gate

## Status
Accepted.

## Context

The brain has never hydrated knowledge from agent work despite a
`brain-extractor` SubagentStop hook existing in `settings.json` since the
brain shipped. Three independent investigations across the last two months
converged on the same root cause: `type: "agent"` SubagentStop hooks are
silently broken in Claude Code 2.1.121. A diagnostic probe placed as the
first action inside `brain-extractor` (before all guards) produced zero log
entries against 1,591 qualifying SubagentStop events; the parallel
`type: "command"` hooks on the same SubagentStop block fired correctly
9,006 times. GitHub Issue #40010 (open as of 2026-04-28) confirms the same
symptom upstream — the v2.1.113 fix patched non-Stop events only. A
secondary failure is also fatal: the registered config uses an `agent`
field that is not in the documented hook schema, and even if dispatch
worked the spawned agent has no MCP access (Read/Grep/Glob only), so
`agent_capture` is unreachable from inside it.

The lesson layer matters here: `feedback_eva_constraints.md` and
`feedback_mechanical_enforcement.md` jointly establish that Eva's
behavioral commitments fail under pipeline load — she forgets to call
`agent_capture`. The original `brain-extractor` SubagentStop hook existed
precisely to remove Eva from the loop. Its replacement must also be
mechanical. `feedback_no_background_agents.md` further bans `type: agent`
SubagentStop hooks outright (post-race-condition policy, ratified
post-ADR-0050). The replacement must avoid that pattern.

Today's empirical addition: `PostToolUse` on the MCP tool
`mcp__plugin_atelier-pipeline_atelier-brain__agent_capture` was confirmed
firing in a controlled test (one fire per call, same-second timestamp).
Combined with `PreToolUse` on `Agent` (already proven by
`enforce-scout-swarm.sh` firing on every qualifying invocation) and
`SubagentStop type:command` (proven by 9,006 fires of `log-agent-stop.sh`),
all three hook types required for a mechanical capture gate are
empirically validated on the running Claude Code version. The triggering
question is: should brain capture be hardcoded directly into a
`type: mcp_tool` SubagentStop hook (no Eva involvement, no curation), or
should it route through Eva via a hook-driven gate that forces her to call
`agent_capture` with curated content before her next agent invocation?

## Options Considered

**Option 1: Three-hook gate routing through Eva (chosen).** Three
`type: command` hooks form a closed loop. (a) A SubagentStop hook
(co-fired with `log-agent-stop.sh`) checks if the stopping agent is in
the 8-agent allowlist (`sarah`, `colby`, `agatha`, `robert`, `robert-spec`,
`sable`, `sable-ux`, `ellis`) and writes
`docs/pipeline/.pending-brain-capture.json` with `agent_type`,
`transcript_path`, and `timestamp`. (b) A PreToolUse hook on `Agent`
checks for the pending file's existence; if present and main-thread
(`agent_id` empty), exits 2 with a BLOCKED message instructing Eva to
call `agent_capture` with curated thoughts from the previous agent's work
before spawning the next one. (c) A PostToolUse hook on the
`agent_capture` MCP tool deletes the pending file on successful capture.
The brain-extractor agent file is removed; the orphaned `type: agent`
entry in `settings.json` is removed. Eva curates content (the brain stays
a curated knowledge store, not a transcript dump). Capture is mechanical
because the gate blocks her next forward step until she captures. The
escape hatch is a documented `rm` of the pending file when brain is
unreachable, gated by an Eva-only protocol step in
`pipeline-orchestration.md` plus a `--brain-unavailable` sentinel the
PreToolUse hook honors (sentinel file at
`docs/pipeline/.brain-unavailable`, written when `atelier_stats` returns
unreachable, cleared on next successful brain ping).

**Option 2: `type: mcp_tool` SubagentStop hook calling `agent_capture`
directly.** Added in Claude Code v2.1.118. Configuration shape:
`{"type": "mcp_tool", "server": "atelier-brain", "tool": "agent_capture",
"input": {...}}` with `${last_assistant_message}` interpolated as content.
Zero Eva involvement, no shell script, no PreToolUse gate. Rejected on
two grounds. First, `agent_capture`'s required fields (`thought_type`,
`source_agent`, `source_phase`, `importance`) would be hardcoded in the
hook config — every capture from every agent would carry identical
metadata, which destroys the brain's primary discrimination axis at
prefetch (Eva's `<brain-context>` injection is ranked partly by
`thought_type`, and a brain where every thought is the same type ranks
by recency only). Second, the content payload would be raw
`last_assistant_message` — typically several KB of agent prose
including chain-of-thought, file paths, and incidental status text.
The brain has been deliberately sized for curated thoughts (1–3
sentences, decision-grade), not raw transcripts; raw content degrades
prefetch precision and inflates `pgvector` storage by an order of
magnitude. The hook works mechanically; the *capture quality* is wrong.

**Option 3: Do nothing — accept that categories 1–3 and 5 stay
uncaptured.** Telemetry (category 4) is already covered by
`hydrate-telemetry.mjs` at SessionStart. Agent decisions, conversational
decisions, bug patterns, and cross-session institutional knowledge stay
captured only when Eva remembers — which the lesson layer says she
doesn't. Rejected on the same grounds the original `brain-extractor`
hook existed: behavioral capture under pipeline load is unreliable, and
the brain's value proposition collapses without consistent ingest.

## Decision

Adopt Option 1: a three-hook gate routing brain capture through Eva.

- Remove the `type: agent` `brain-extractor` entry from
  `.claude/settings.json` SubagentStop block. Remove the
  `brain-extractor` agent file from `source/claude/agents/` and
  `source/cursor/agents/`.
- Add `enforce-brain-capture-pending.sh` as a `type: command`
  SubagentStop hook (co-fired with `log-agent-stop.sh`). The script
  gates internally on the 8-agent allowlist, exits 0 for any other
  agent_type, and writes the pending file when allowlisted. No
  blocking; SubagentStop hooks must not exit 2.
- Add `enforce-brain-capture-gate.sh` as a `type: command` PreToolUse
  hook on `Agent`. Pattern matches `enforce-scout-swarm.sh`: main-thread
  only (`agent_id` empty), fail-open on missing config or
  `ATELIER_SETUP_MODE`. If `.pending-brain-capture.json` exists and
  `.brain-unavailable` does not, exit 2 with a BLOCKED message.
- Add `clear-brain-capture-pending.sh` as a `type: command` PostToolUse
  hook scoped to the `agent_capture` MCP tool. On successful tool
  result, delete `.pending-brain-capture.json`. Idempotent — exits 0 if
  the file is absent.
- Document the escape hatch in `pipeline-orchestration.md`: when
  `atelier_stats` returns unreachable, Eva touches
  `docs/pipeline/.brain-unavailable`; the gate hook honors that
  sentinel and the pending file is cleared at next successful brain
  ping (Eva runs an `atelier_stats` probe at session start anyway, per
  `default-persona.md`).

Allowlist for the SubagentStop pending-write: `sarah`, `colby`,
`agatha`, `robert`, `robert-spec`, `sable`, `sable-ux`, `ellis`.
This mirrors the original `brain-extractor` `if:` clause exactly —
the agents that produce brain-grade output. Poirot, Sherlock,
Sentinel, Distillator, scouts, and discovered agents are excluded
(verification/investigation/scout output is logged elsewhere or is
ephemeral).

Colby writes a behavioral test for the gate because the regression
this ADR closes is the exact failure mode the brain has been silently
exhibiting for months — a hook present in config but never firing.
The test must assert that (a) PreToolUse blocks `Agent` invocation
when the pending file exists, (b) PostToolUse on a successful
`agent_capture` deletes the pending file, and (c) the
`.brain-unavailable` sentinel suppresses the block.

### Factual Claims
- `.claude/settings.json` SubagentStop block currently contains a
  `type: agent` entry with `agent: "brain-extractor"` and an `if:`
  clause matching the 8-agent allowlist.
- `source/claude/hooks/log-agent-stop.sh` is the canonical
  `type: command` SubagentStop pattern: reads stdin, parses with jq,
  exits 0 always, no blocking.
- `source/claude/hooks/enforce-scout-swarm.sh` is the canonical
  `type: command` PreToolUse-on-Agent pattern: jq stdin parse,
  main-thread guard via empty `agent_id`, fail-open on missing config,
  exit 2 with stderr BLOCKED message on violation.
- `source/claude/hooks/enforce-colby-stop-verify.sh` (ADR-0050) is the
  precedent for SubagentStop scripts that gate internally on
  `agent_type` rather than via `if:` clauses.
- `feedback_no_background_agents.md` bans `type: agent` SubagentStop
  hooks; this ADR completes the migration the policy implies.
- PostToolUse hooks on MCP tools fire — confirmed by test on
  `mcp__plugin_atelier-pipeline_atelier-brain__agent_capture` at
  2026-04-28T15:44:06Z.
- `agent_capture` requires `thought_type`, `source_agent`,
  `source_phase`, `importance` as input fields (per brain MCP server
  schema).
- Eva's session boot already calls `atelier_stats` and writes
  `brain_available` to `pipeline-state.md` (per
  `agent-system.md` brain-config section).

### LOC Estimate
~280 lines added across 6 files (3 new hook scripts ~180 lines,
`settings.json` add 3 entries / remove 1 ~12 lines net,
`pipeline-orchestration.md` escape-hatch protocol ~30 lines, pytest
~50 lines). Removed: `source/claude/agents/brain-extractor.md` and
`source/cursor/agents/brain-extractor.md` (~80 lines net deletion).

## Rationale

The mechanical-vs-behavioral choice was settled by prior lessons: Eva
forgets, so capture must be enforced. The remaining choice — Eva-curated
vs. raw-content capture — turns on what the brain is *for*. The brain is
the prefetch layer that makes Eva's `<brain-context>` injection useful;
its value is curation density (decision/lesson/seed thoughts at 1–3
sentences) and metadata discrimination (`thought_type`, `source_agent`,
`source_phase`). Option 2 ships hooks that fire reliably but capture
content the prefetch layer cannot use well. Option 1 keeps the curation
contract intact and uses three proven hook types to make Eva's
non-curation impossible (the gate blocks her forward step).

The risk shape is loop deadlock: Eva calls `agent_capture`, the
PostToolUse hook fails to delete the pending file (filesystem error,
race with a parallel SubagentStop write, jq parse error), and the next
`Agent` invocation is permanently blocked. Mitigation: the clear hook
runs idempotently, logs failures to `.claude/telemetry/`, and the
escape-hatch sentinel is a one-line manual unblock Eva can invoke when
diagnostics confirm the loop is wedged. The sentinel also covers the
intentional case (brain genuinely unreachable mid-pipeline).

A second risk: the gate fires *between* agent invocations, which
introduces a per-handoff latency cost (Eva must compose a curated
thought and call `agent_capture` before spawning the next agent). On a
Medium pipeline with ~12 agent stops in the allowlist, that's ~12
captures per pipeline. The cost is bounded and is the explicit
design intent — the brain's value comes from per-handoff capture
density, not per-pipeline summary.

Out of scope: capturing from Poirot, Sherlock, Sentinel, scouts, or
discovered agents. Their output is either logged separately
(`last-qa-report.md`, `last-case-file.md`) or ephemeral by design.
Adding them to the allowlist later is a one-line config change and
does not require a new ADR.

Rollback sketch: revert the three hook entries in `settings.json`,
delete the three new scripts, and the system returns to the prior
broken-but-silent state. No DB schema changes. The brain's
`thoughts` table is append-only and tolerates missing capture
gracefully (prefetch returns fewer results, ranking still works).

## Falsifiability

Revisit this ADR if any of these occur:

- Within one calendar quarter, Eva is observed bypassing the gate
  more than three times (e.g., touching `.brain-unavailable` to
  unblock a flow when `atelier_stats` is actually healthy). That
  signals the curation cost-per-handoff is too high and Option 2's
  raw-content tradeoff becomes worth re-examining with a curation
  filter applied post-hoc.
- The PostToolUse-on-MCP-tool hook stops firing in a future Claude
  Code release (the empirical evidence is single-version: 2.1.121).
  This collapses the gate's clear-leg and forces a redesign.
- The brain's prefetch quality (measured by
  `<brain-context>` relevance scores returned by `agent_search`)
  degrades after one quarter of mechanical capture, suggesting Eva's
  curated thoughts are systematically lower-quality than the raw
  transcripts Option 2 would have captured.
- A future Claude Code release fixes `type: agent` SubagentStop
  dispatch (Issue #40010 closes) AND ships MCP access to spawned
  agents. At that point the three-hook gate is more machinery than
  the problem requires and a single-hook design becomes viable —
  but the curation argument from Option 2 still applies, so
  revisit only if the `brain-extractor` agent can be configured
  with explicit metadata extraction rather than dump-and-go.

## Sources

- `source/claude/hooks/enforce-scout-swarm.sh` — PreToolUse-on-Agent
  pattern: jq parse, main-thread guard, fail-open, exit 2 with BLOCKED.
- `source/claude/hooks/log-agent-stop.sh` — SubagentStop
  `type: command` pattern: never blocks, exits 0 always, telemetry-only.
- `source/claude/hooks/enforce-colby-stop-verify.sh` (ADR-0050) —
  internal `agent_type` gating in SubagentStop scripts.
- GitHub Issue #40010 — `type: agent` hooks silently ignored on
  SubagentStop in Claude Code 2.1.x.
- `feedback_no_background_agents.md` — bans `type: agent` SubagentStop
  hooks post-race-condition.
- `feedback_eva_constraints.md`, `feedback_mechanical_enforcement.md`
  — behavioral capture under load is unreliable; mechanical
  enforcement required.
- ADR-0050 — `enforce-colby-stop-verify.sh` precedent for
  internally-gated SubagentStop scripts and per-session counter files.
- ADR-0051 — brain trust hardening (capture-side data integrity).
