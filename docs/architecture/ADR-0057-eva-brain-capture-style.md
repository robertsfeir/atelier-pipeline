# ADR-0057: Eva Brain-Capture Style and Mechanical Defaults

## Status
Accepted.

## Context

The three-hook brain-capture gate (ADR-0053) is correct and stable: a
SubagentStop hook marks a pending capture, a PreToolUse hook on `Agent`
blocks Eva's next invocation, and a PostToolUse hook on `agent_capture`
clears the marker. The mechanism fires reliably. The cost surface is no
longer the gate.

Measured today: ~85% of per-capture wall time is the model -- Eva --
generating prose around the `agent_capture` call. Specifically: a
reasoning preamble ("Brain confirmed live, I'm about to capture two
items..."), then content that drifts well past the 1-3 sentence
contract written into `pipeline-orchestration.md`, then a post-call
summary that recites the returned UUIDs and re-narrates what was
linked. On a Medium pipeline with ~12 allowlisted handoffs the
preamble/postamble overhead repeats 12 times and dominates Eva's
turn latency. The brain itself is healthy (mybrain live, 1535
thoughts, 308 already captured by Eva); the curation contract is
not the issue. Eva's *talking style around the tool call* is.

Prior decisions to align with: ADR-0005 (Eva pre-fetches brain context
on behalf of agents; agents consume data, not instructions);
ADR-0043 (return-condensation -- subagent prose budgets are explicit;
this ADR extends the same discipline to Eva's tool-call prose);
ADR-0053 (the mechanical gate, untouched here); preference thought
captured 2026-05-07 ("Lead with outcome. Cut preamble. Skip 'Great
question, here's what I'll do.'").

## Decision

Lock in five mechanical defaults for Eva's brain-capture style. Each
applies to every `agent_capture` call Eva makes, in every mode (gated
handoff, /devops capture, cross-cutting capture, seed). No change to
the gate flow, the allowlist, or the schema.

1. **Default content cap: ≤500 characters.** Eva's `content` field
   stays at or under 500 characters by default. Verbosity is the
   exception and requires one stated trigger -- (a) an
   `alternatives_rejected` metadata list with ≥2 entries, (b) an
   `evidence` array with ≥1 entry, (c) a formal correction enumerating
   ≥3 runtime scenarios, or (d) the user explicitly flags the capture
   as load-bearing ("write it long"). The 1-3 sentence contract in
   `pipeline-orchestration.md` is preserved; this puts a hard
   character ceiling on what "1-3 sentences" means in practice and
   names the four cases where exceeding it is allowed.

2. **Mechanical metadata defaults.** Stop re-deriving these per call.
   `source_agent="eva"`. `source_phase="pipeline"`, with two
   exceptions only: `"setup"` when invoked from a setup command
   (`/pipeline-setup`, `/pipeline-uninstall`) and `"qa"` when capturing
   a Poirot finding. `decided_by.agent="eva"`.
   `decided_by.human_approved=true` iff the user explicitly asked for
   the capture in the current turn, otherwise `false`. These four
   fields are filled in mechanically; Eva does not deliberate.

3. **No post-capture summary.** The `agent_capture` tool result is the
   receipt. Eva does not enumerate what was captured, recite UUIDs, or
   re-narrate `evolves_from` links. At most a single short
   acknowledgement ("Done.") when conversational flow demands one --
   and never the UUID. If the user explicitly asks what was captured,
   that is a different turn and Eva answers it then.

4. **No pre-capture preamble.** Eva does not announce the upcoming
   call ("I'm about to capture..."), does not narrate brain health
   ("Brain confirmed live..."), and does not enumerate counts ("two
   captures coming up"). The only legitimate pre-call surfaces are
   real branches: a clarification question the user must answer
   before Eva can curate, a routing receipt for the *next* agent
   (one line, per existing routing-transparency rule), or a failure
   pre-flight when `atelier_stats` is unreachable and the
   `.brain-unavailable` sentinel needs to be touched. None of those
   are preambles; they are decisions Eva would have made anyway.

5. **Batch parallel when ≥2 captures are needed in one user turn.**
   The PreToolUse gate is per-`Agent`-call, not per-`agent_capture`
   call. Multiple `agent_capture` tool uses in a single assistant
   message are safe and run faster. When Eva needs to capture two or
   more curated thoughts before the next agent handoff, she emits
   them as parallel tool calls in the same message.

### Factual Claims
- `source/shared/rules/pipeline-orchestration.md` `<protocol id="brain-capture">` (lines 29-87) currently specifies "1-3 sentences" but no character cap and no mechanical-defaults table.
- `source/shared/rules/agent-system.md` `<section id="brain-config">` (lines 19-30) describes Eva's curation responsibility without specifying preamble/postamble discipline.
- `source/shared/rules/default-persona.md` `## Brain Access` section (line 63) references the three-hook gate but contains no style guidance for the tool call itself.
- `source/shared/references/agent-preamble.md` (lines 26-53) describes brain-context consumption from the agent side; the curator-side style guidance is absent.
- The `agent_capture` MCP tool schema requires `thought_type`, `source_agent`, `source_phase`, `importance`; `decided_by` is an optional structured field per existing usage.
- The PreToolUse gate (`enforce-brain-capture-gate.sh`) fires on `Agent` tool invocations only, not on `agent_capture` invocations -- parallel `agent_capture` calls in one assistant message do not double-fire the gate.

### LOC Estimate
~80 lines changed across 4 files. The bulk is a new style-defaults block in `pipeline-orchestration.md` (~40 lines) plus tightening sentences and pointer references in `default-persona.md`, `agent-system.md`, and `agent-preamble.md` (~10-15 lines each). No code, no hooks, no schema.

## Options Considered

**Option 1: Lock in style + mechanical defaults (chosen).** Codify the
five levers above in the four load-bearing rule files so the discipline
is loaded into Eva's context every session, not held in working memory.
The cost is a one-time documentation change. The gain is the ~85% prose
overhead drops out by default, with named exceptions for the cases
where verbosity actually earns its keep.

**Option 2: Add a hook that truncates `content` to 500 chars.**
Mechanically enforces lever 1 but does nothing about levers 3 and 4
(preamble/postamble), which are the larger share of the latency. Also
risks corrupting the legitimate verbose cases (alternatives_rejected,
evidence arrays) by silently chopping mid-sentence. Rejected:
mechanical enforcement of style is the wrong tool for a persona
problem when the gate itself is already mechanical and is not the
bottleneck.

**Option 3: Do nothing -- accept current latency.** The gate works,
captures are landing, the brain is hydrating. The cost is borne by
Eva's turn time, not by correctness. Rejected because per-handoff
latency compounds across a Medium pipeline (~12 handoffs) and is the
single largest user-visible drag on pipeline tempo today. The style
levers are cheap to specify and easy to comply with; the cost-benefit
favors locking them in.

## Rationale

The mechanical gate (ADR-0053) is doing its job -- captures are
landing. The remaining cost is persona discipline around the tool
call, which is exactly the layer Eva's rule files exist to govern.
The five levers each target a named source of overhead and together
remove the ~85% prose share without touching the gate, the schema,
or the brain. Each lever is also independently falsifiable, so a
later revision can soften one without softening the others.

Risk shape: if Eva over-corrects and the content cap squeezes out
genuinely load-bearing context (the case where a single decision
captures rejected alternatives, evidence, *and* a correction), the
brain's prefetch loses signal density and `<brain-context>`
injections get less useful over time. The four named verbosity
triggers are the relief valve for exactly this case -- if any one
applies, Eva exceeds the cap and notes which trigger fired. If the
relief valve turns out to be too narrow, revisit the trigger list,
not the cap.

Out of scope: no change to which agents are allowlisted (still the
eight from ADR-0053); no change to capture timing or the three-hook
flow; no change to mybrain (separate plugin, separate ADRs); no
change to existing captured thoughts; no change to the agent-side
brain-context consumption discipline in `agent-preamble.md`.

Rollback sketch: revert the documentation diffs across the four
files. No schema, no hooks, no captured data is affected. The gate
keeps firing, captures keep landing; Eva just goes back to her
verbose style.

## Falsifiability

Revisit this ADR if any of the following holds after one calendar
month of the change being live:

- Median `agent_capture` content length sampled from the brain
  remains above 500 characters across Eva-authored captures, with no
  named verbosity trigger present in metadata. (Signal: the default
  cap is being ignored.)
- A sampled review of Eva's assistant messages shows post-capture
  UUID enumerations or `evolves_from` re-narrations in more than
  10% of turns containing an `agent_capture` call. (Signal: lever
  3 didn't land.)
- Batched parallel `agent_capture` calls are observed double-firing
  the PreToolUse gate, or any other gate the assumption in lever 5
  depends on. (Signal: the batching assumption is wrong and lever 5
  must be withdrawn or re-scoped.)

## Load-Bearing Files

Colby's target list for the documentation change:

- `source/shared/rules/pipeline-orchestration.md` -- `<protocol id="brain-capture">` (around lines 29-87). Add a style-defaults block beneath the gate description.
- `source/shared/rules/agent-system.md` -- `<section id="brain-config">` (lines 19-30). One-line cross-reference to the new style block.
- `source/shared/rules/default-persona.md` -- `## Brain Access` section (around line 63). One-line cross-reference.
- `source/shared/references/agent-preamble.md` -- brain-capture paragraph (lines 50-53). Optional one-line cross-reference for consistency; agent-side guidance is unchanged.

## Sources

- ADR-0053 -- mechanical brain-capture gate (unchanged by this ADR).
- ADR-0005 -- Eva pre-fetches brain context on behalf of agents.
- ADR-0043 -- agent return condensation (precedent for prose-budget discipline).
- Preference thought captured 2026-05-07 by Robert -- "Lead with outcome. Cut preamble."
- Seed thought captured 2026-05-11 by Eva -- pipeline-start framing of this decision surface.
