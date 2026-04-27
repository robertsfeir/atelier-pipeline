# ADR-0047: Opus 4.7 Pipeline Tuning — Phased Implementation Plan

## Status
Accepted.

## Phase Status

Eva updates this section as phases complete. This is the primary
session-recovery signal — at session start Eva reads this checklist to
determine what is active, what is done, and what to do next. The first
unchecked phase is the active one.

- [x] Phase 1 — Literal-instruction fixes (Sentinel floor, Agatha return
  format + workflow, robert-spec workflow, sable-ux workflow, Sarah
  exploration ceiling, Eva read-cap)
- [x] Phase 2 — `maxTurns` recalibration (Colby 200→120, Agatha 60→40,
  Poirot 80→50, Sherlock 80→50, Sarah 45→30)
- [ ] Phase 3 — Sentinel model `opus → sonnet` (frontmatter, both source
  trees, plus per-agent table in `pipeline-models.md`)
- [ ] Phase 4 — Pin explicit model IDs across all frontmatter
  (`claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`) and
  align `skills/brain-hydrate/SKILL.md` model assignment table
- [ ] Phase 5 — Web-search regression note in `pipeline-models.md`

Each phase ends with a single commit (template below) and a session clear.
Phases are independent within their own commits but ordered: Phase 1's
literal-instruction fixes are prerequisite to Phase 2's tighter `maxTurns`
budget being safe.

## Context

Anthropic shipped Opus 4.7 with three behavior shifts that affect this
pipeline materially: roughly 2x call efficiency on equivalent work, adaptive
thinking that self-calibrates from `effort` (no `budget_tokens`), and
significantly more literal instruction following. There is one regression:
agentic web search degraded. The pipeline frontmatter still targets generic
aliases (`opus`, `sonnet`, `haiku`), which means a runtime alias resolution
to a non-4.7 model would silently invalidate the call-efficiency assumption
that any tightened `maxTurns` budget rests on.

Today's research session (2026-04-27) audited every agent persona and
frontmatter file under `source/`. The audit was text-based, not role-based —
the prior heuristic ("Eva is high-risk because she orchestrates") was wrong.
The actual literal-following risks live in agents whose persona language
contains hard floors, advisory hedges treated as suggestions by older models,
or under-specified workflow sections: Sentinel (`Minimum 3 findings`
constraint that pressures padding), Agatha (no explicit return-line format
that the brain-extractor parses), Sarah (`~8 files` ceiling without a
fallback condition), robert-spec and sable-ux (4-line workflows with no
output format), and Eva's invocation template (`prefer ≤6` advisory).
Sentinel additionally pays Opus rates to run `effort: low`, which suppresses
the very reasoning that justifies Opus pricing.

The constraint set: changes must land in a sequence where each phase can be
verified before the next compounds risk. Specifically, tighter `maxTurns`
budgets are only safe after literal-instruction fixes land, because under
4.7's literal following, vague workflow guidance burns turns the model
otherwise wouldn't have used. A single test catches the most likely
regression mode (alias drift on new agents) without ceremonial coverage.

## Options Considered

**Option A — Single big-bang commit.** Bundle all five concerns (literal
fixes, `maxTurns`, Sentinel model, ID pinning, search note) into one
PR/commit. Fast to write, but if any one change destabilizes a pipeline run
the bisect surface is the entire 4.7-tuning patch. With model-behavior
changes the common failure mode is "something feels worse" — a wide commit
makes that signal unactionable. Rejected.

**Option B — Per-file commits with no ordering.** Commit each frontmatter
or persona file independently as the change is made. Maximum bisectability
but loses the causal ordering: Phase 2's tighter `maxTurns` budgets assume
Phase 1's literal fixes have landed. Without enforced ordering, a fresh
session could ship `maxTurns` reductions before the workflow tightening
that makes them safe. Rejected.

**Option C — Five phased commits in dependency order, each followed by a
session clear.** Five commits, each scoped to one concern, ordered so that
each phase's preconditions are visibly satisfied by the prior phase's
landed work. Session clear between phases keeps Eva's working context off
stale assumptions about partially-applied state. The Phase Status checklist
in this ADR is the recovery artifact — Eva reads it at session start, sees
the first unchecked box, and knows exactly what to do next. Chosen.

## Decision

Tune the pipeline for Opus 4.7 in five sequenced phases. Phase 1 fixes
literal-instruction failure modes in agent personas. Phase 2 recalibrates
`maxTurns` against 4.7's 2x call efficiency. Phase 3 demotes Sentinel from
opus to sonnet (suppressed-reasoning case). Phase 4 pins explicit model IDs
in every frontmatter and the brain-hydrate model table. Phase 5 documents
the web-search regression in `pipeline-models.md`. Each phase ends with one
commit and a session clear; the Phase Status section above is the recovery
ledger.

Colby writes a structural pytest that fails when any
`source/claude/agents/*.frontmatter.yml` or
`source/cursor/agents/*.frontmatter.yml` file declares a generic alias
(`model: opus`, `model: sonnet`, `model: haiku`) instead of an explicit
versioned ID, because alias drift on a future new agent is the regression
that silently undoes Phase 4 and invalidates Phase 2's tighter call budget.

### Phase 1 — Literal-instruction fixes

Files and changes:

- `source/shared/agents/sentinel.md` — replace `Minimum 3 findings or
  explicit "clean scan" report with evidence.` (line 39) with Poirot's
  zero-with-confidence model: clean scan acceptable when evidence supports
  it, no minimum count.
- `source/shared/agents/agatha.md` — add a return-line format directive to
  `<output>` matching the brain-extractor's parser:
  `Written {paths}, updated {paths}.` Promote workflow from advisory bullets
  to directive numbered steps.
- `source/shared/agents/robert-spec.md` — expand `<workflow>` with explicit
  scope guidance and an `<output>` format block. The current 4-line workflow
  is insufficient under literal following.
- `source/shared/agents/sable-ux.md` — same treatment as robert-spec; the
  current workflow is similarly thin past the design-system check.
- `source/shared/agents/sarah.md` — keep the `~8 files` ceiling but add a
  concrete fallback condition: when integration-point reading would exceed
  the ceiling, name what's missing in the ADR and proceed with the best
  available information. (Already partially present; reinforce as the
  literal rule.)
- `source/shared/rules/agent-system.md` — clarify the Eva invocation template
  `<read>` line so its advisory nature is unambiguous under literal
  following: replace `prefer ≤6` with explicit-advisory language plus stated
  permission to exceed when warranted (e.g., `typically ≤6; include more
  when the decision clearly requires it`).

Commit message template: `fix(agents): tighten literal-instruction surfaces
for Opus 4.7 (Phase 1 of 5)`

### Phase 2 — `maxTurns` recalibration

Files and changes (apply to both `source/claude/agents/` and
`source/cursor/agents/`):

- `colby.frontmatter.yml`: `maxTurns: 200` → `120`
- `agatha.frontmatter.yml`: `maxTurns: 60` → `40`
- `investigator.frontmatter.yml` (Poirot): `maxTurns: 80` → `50`
- `sherlock.frontmatter.yml`: `maxTurns: 80` → `50`
- `sarah.frontmatter.yml`: `maxTurns: 45` → `30`

Rationale per agent: 2x call efficiency on Opus 4.7 means historical
turn-budget headroom was set for a less efficient model. The new ceilings
preserve roughly 1.2x slack against expected average completion to absorb
variance.

Commit message template: `chore(agents): recalibrate maxTurns for Opus 4.7
call efficiency (Phase 2 of 5)`

### Phase 3 — Sentinel model demotion

Files and changes:

- `source/claude/agents/sentinel.frontmatter.yml`: `model: opus` →
  `model: sonnet`
- `source/cursor/agents/sentinel.frontmatter.yml`: same change
- `source/shared/rules/pipeline-models.md` — update Sentinel row in the
  Per-Agent Assignment Table from `opus | low` to `sonnet | low` with the
  rationale: pattern-matching SAST with `effort: low` suppresses Opus
  reasoning; Sonnet matches the actual workload.

Commit message template: `chore(sentinel): demote model to sonnet (Phase 3
of 5)`

### Phase 4 — Pin explicit model IDs

Files and changes — every frontmatter file in `source/claude/agents/` and
`source/cursor/agents/` (13 agents per tree):

- Replace `model: opus` with `model: claude-opus-4-7`
- Replace `model: sonnet` with `model: claude-sonnet-4-6`
- Replace `model: haiku` with `model: claude-haiku-4-5-20251001`

Also align `skills/brain-hydrate/SKILL.md` Model Assignment table (lines
~487-494) and any in-text references (e.g., `Agent(model: "haiku")`,
`Agent(model: "sonnet")` callouts) to use the same explicit IDs.

The structural pytest from the Decision section lands with this phase and
prevents future alias drift.

Commit message template: `chore(agents): pin explicit model IDs for Opus
4.7 (Phase 4 of 5)`

### Phase 5 — Web-search regression note

File and change:

- `source/shared/rules/pipeline-models.md` — add a short subsection under
  the Adaptive-Thinking Rationale block noting Opus 4.7's regression on
  agentic web search; agent tool lists do not include `WebSearch` or
  `WebFetch`, and Eva's auto-routing must not synthesize them in.

Commit message template: `docs(pipeline-models): note Opus 4.7 web-search
regression (Phase 5 of 5)`

### Factual Claims

- `source/shared/agents/sentinel.md:39` contains `Minimum 3 findings or explicit "clean scan" report with evidence.`
- `source/shared/agents/agatha.md` `<output>` does not contain a literal `Written {paths}` return-line format.
- `source/shared/agents/robert-spec.md` `<workflow>` is 4 numbered steps with no `<output>` format block.
- `source/shared/agents/sable-ux.md` `<workflow>` is steps 0-4 with no explicit `<output>` format block beyond the DoR design-system line.
- `source/shared/agents/sarah.md` lines 13-16 already contain the `~8 files` ceiling and the "name what's missing" fallback; Phase 1 reinforces, not invents.
- `source/shared/rules/agent-system.md` invocation template `<read>` line reads `prefer ≤6` (advisory).
- `source/claude/agents/colby.frontmatter.yml:10` declares `maxTurns: 200`.
- `source/claude/agents/agatha.frontmatter.yml:8` declares `maxTurns: 60`.
- `source/claude/agents/investigator.frontmatter.yml:10` declares `maxTurns: 80`.
- `source/claude/agents/sherlock.frontmatter.yml:10` declares `maxTurns: 80`.
- `source/claude/agents/sarah.frontmatter.yml:10` declares `maxTurns: 45`.
- `source/claude/agents/sentinel.frontmatter.yml:6` declares `model: opus`, `effort: low`, `maxTurns: 40`.
- Both `source/claude/agents/` and `source/cursor/agents/` contain 13 frontmatter files each, all using generic model aliases (`opus`, `sonnet`, `haiku`).
- `source/shared/rules/pipeline-models.md` Per-Agent Assignment Table (lines ~76-93) lists Sentinel as `opus | low`.
- `skills/brain-hydrate/SKILL.md` Model Assignment table (lines ~488-494) uses generic aliases (`Opus`, `Haiku`, `Sonnet`).

### LOC Estimate
~80 lines changed across ~30 files (≈26 frontmatter files for ID pinning, ~4 persona files for literal fixes, 2 rules files, 1 skill file, 1 new pytest).

## Rationale

Five phased commits beat a single big-bang because model-behavior changes
produce diffuse "feels worse" failure signals where bisect width is the
recovery cost. Five phased commits beat per-file unordered commits because
Phase 2's tighter turn budget is only safe after Phase 1's literal-fix
work — without ordering, a fresh session could land Phase 2 first and burn
budget on under-specified workflows.

The Phase Status section is load-bearing: ADRs are normally immutable, but
this ADR has a designated mutable region (the checklist) explicitly to
serve as the session-recovery artifact. Eva updates only the checklist;
the rest of the ADR stays frozen. If the design itself proves wrong mid-
execution, Sarah supersedes with a new ADR rather than revising the body
here.

The structural pytest is the only test added. It is justified because the
failure mode is silent and high-impact: if a future agent is added with
`model: opus` (alias) and Anthropic later resolves that alias to a model
without 4.7's call efficiency, Phase 2's `maxTurns` reductions cause turn-
budget exhaustion with no obvious cause. A 30-line pytest that scans every
frontmatter file under both `source/claude/agents/` and
`source/cursor/agents/` and asserts the model field starts with `claude-`
catches this at CI time.

If 4.7's call-efficiency claim is overstated for our specific workloads,
the failure mode is Phase 2 agents hitting `maxTurns` exhaustion and Eva
queuing rework — the signal is observable in QA reports and recoverable by
raising the affected agent's ceiling. That's the bounded downside that
makes phasing tolerable.

Out of scope: changing `effort` parameters beyond Sentinel's existing `low`
(already correct), modifying agent task-class assignments in
`pipeline-models.md` beyond Sentinel's row, and broader IDE-config schema
changes. Adaptive thinking via `effort` is already correctly modeled per
ADR-0041; this ADR does not relitigate it.

## Falsifiability

Revisit if any of: (a) a Phase 2 agent hits `maxTurns` exhaustion in two
consecutive Medium+ pipeline runs after Phase 1 has landed — call-
efficiency assumption is wrong for our workload; (b) Phase 3 produces a
Sentinel false-positive rate worse than its opus baseline (measurable from
QA reports) — pattern-matching workload was Opus-bound after all;
(c) Phase 4 lands and Anthropic deprecates one of the pinned IDs before
the next planned tuning cycle — pinning cost outweighs benefit and we
revert to aliases with a different drift-detection strategy.

## Sources

- Brain thoughts captured 2026-04-27: `f5e40525` (model ID pinning),
  `a4c47346` (Sentinel demotion), `c9e24dbd` (3-phase work order — note
  this ADR refines that into 5), `429f000a` (4.7 capability shifts),
  `b4112080` (text-based audit lesson), `59d163df` (Sentinel floor),
  `f873864a` (Agatha return format), `3849dbc3` (robert-spec/sable-ux
  workflow thinness), `b208826b` (Sarah exploration ceiling),
  `caaaafd8` (Eva read-cap), `34879fdd` (brain-hydrate alias inconsistency),
  `b5eab8e7` (web-search regression policy).
- Prior ADRs: ADR-0041 (effort-per-agent map), ADR-0042 (scout/synthesis
  tier correction).
- Files audited: `source/shared/agents/{sentinel,agatha,sarah,robert-spec,sable-ux}.md`,
  `source/claude/agents/*.frontmatter.yml`, `source/shared/rules/{agent-system,pipeline-models}.md`,
  `skills/brain-hydrate/SKILL.md`.
