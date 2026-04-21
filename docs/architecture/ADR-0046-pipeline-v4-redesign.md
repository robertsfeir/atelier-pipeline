# ADR-0046: Pipeline v4.0 Redesign -- Trim the Ceremony, Exercise the Code

## Status

Accepted. Post-hoc: v4.0 has been implemented and released; this ADR captures
the decision for future sessions. Supersedes or obsoletes portions of prior
ADRs:

- **ADR-0007** (DoR/DoD WARN hook -- Roz-authored verification path): obsolete.
- **ADR-0023** (agent-spec reduction -- `ALL_AGENTS_CORE` roster anchor): agent
  roster changes; roster constant kept only if still referenced by surviving
  tests.
- **ADR-0034** (gauntlet remediation -- Roz self-review loop): obsolete.
- **ADR-0041 / ADR-0042** (Per-Agent Assignment Table): Roz row removed, Cal
  row renamed to Sarah.

Prior ADRs are not edited (ADR immutability). They remain correct as
historical record.

## Context

The v3.x pipeline accumulated agents and artifacts faster than it accumulated
value. Concretely: a test-authoring agent (Roz) produced assertions before
implementation; the architect (Cal) produced long-form ADRs with requirements
tables, verbatim replacement text, and step-sized implementation manuals;
scout fan-out ran on every pipeline regardless of size; ~1200 structural
pinning tests asserted line counts, section orders, and agent-roster shapes;
a retro-lessons file grew with every postmortem and was read by every agent
on every invocation.

Observed behavior in production: Roz's pre-built assertions tended to describe
what Colby already planned to do rather than independent behavioral contracts;
Cal's ADR steps got skimmed and re-derived by Colby rather than followed; the
structural tests burned tokens on every run and caught defects a human review
would have caught faster; scout fan-out cost more context than it saved on
Micro/Small work; retro-lessons grew monotonically and most entries were
either obsolete or cheaper to rediscover than to carry.

External research pointed the same direction. Anthropic's multi-agent guide
names "one agent writes code, another writes tests" as an anti-pattern.
Cognition's *Don't Build Multi-Agents* argues decision-dispersion across
role-split agents produces fragile output. Meta's TestGen-LLM data shows
roughly 1-in-20 LLM-generated tests survive build/run/pass/coverage filters.
Academic work reports 100% line coverage with ~4% mutation score and
near-verbatim training-data reproduction under compile-repair pressure.
OpenAI's *Scaling Code Verification* frames falsification of a change as
asymmetrically cheaper than generation. See CHANGELOG v4.0.0 for the full
citation list; this ADR does not re-argue the research.

## Options Considered

**Keep v3.x: Roz-first TDD, long-form Cal ADRs, always-on scouts, full
structural test suite.** Preserves continuity; avoids breaking downstream
projects. Rejected because the observed failure modes -- tests that mirror
implementation, ADRs skimmed rather than read, scouts that cost more than
they return, structural tests that catch nothing -- are structural
properties of the design, not tuning problems. Another round of gate
tightening (the v3.x pattern) would not change the shape of the output.

**Targeted trim: keep Roz but restrict to behavioral tests; keep Cal's ADR
format but cap length.** Preserves the roles while attacking the symptoms.
Rejected because the "one agent writes code, another writes tests" split is
itself the anti-pattern. Capping Cal's ADRs without changing the contract
produces truncated implementation manuals, not decision records. Partial
trims in v3.x (ADR-0023, ADR-0041, ADR-0042, ADR-0044) already tried the
tightening-without-restructuring path and the ceiling came from structure,
not from any individual lever.

**Full restructure (chosen): remove Roz, rename Cal to Sarah with a
decision-record output contract, mandate Colby's exercise-the-code feedback
loop, promote Poirot to default post-build verifier, sizing-gate scouts,
delete retro-lessons, cull structural tests.** Moves verification from a
pre-built-assertion contract to a post-build exercised-behavior contract.
Falsification (Poirot exercising the diff) replaces pre-specification (Roz
authoring assertions Colby then satisfies). Colby becomes the single
decision-maker for implementation; Sarah decides architecture, Colby
decides implementation, Poirot falsifies.

## Decision

We removed Roz; renamed Cal to Sarah and replaced the long-form ADR format
with a 1-2 page decision record (Status / Context / Options / Decision /
Rationale / Falsifiability); mandated that Colby exercise every change
before declaring done; promoted Poirot to the default post-build verifier;
sizing-gated scout fan-out to Medium/Large; deleted the retro-lessons
reference (one durable rule migrated into Colby's persona); and deleted
~1200 structural pinning tests while keeping ~500 behavioral tests.

Colby writes a behavioral test only when Sarah's ADR names a specific
failure mode that would bite users if regressed, or when the user asks.
This very ADR names one such mode below.

Falsifiability-of-pipeline-health failure mode: if a wave ships with Poirot
reporting "no concerns" and a user-visible regression surfaces within 7 days,
that signals the verification model is under-exercising. This is a
behavioral signal to watch, not a test to author.

## Rationale

The chosen path beats the alternatives on the axis that actually moved:
*who decides*. In v3.x, decision-making was dispersed across Cal (what to
build), Roz (what correctness looks like), and Colby (how to build it), with
the pipeline reconciling disagreements via re-invocation loops. v4.0
concentrates decisions: Sarah picks the architectural option, Colby owns
implementation including when a test earns its keep, Poirot falsifies after
the fact. The feedback loop (Colby runs what he writes) replaces the
pre-built assertion as the primary correctness signal -- cheaper to produce,
harder to game, and aligned with the OpenAI falsification-is-cheaper result.

Out of scope and worth naming: this redesign does not change Sherlock's
user-bug flow (ADR-0045 stands), does not change the branch lifecycle
(trunk-based on session worktrees), and does not change the brain capture
model. The Cursor plugin mirrors the Claude Code changes verbatim per the
existing dual-target convention.

Rollback sketch: v4.0 is a breaking change for downstream projects
(`enforce-roz-paths.sh` deleted, `Agent(roz, ...)` grants gone, Cal→Sarah
rename). Rollback means restoring the deleted agent file, hook, hook
registration, and tool grants from git history, and reverting the Cal→Sarah
rename. Prior-ADR content is untouched so the rollback target is clean.
Downstream projects installed after v4.0 would need to re-sync from a
pre-v4.0 tag.

## Falsifiability

Revisit this decision if any of the following signal shows up:

- Poirot's post-build findings catch fewer user-visible regressions per
  wave than Roz's QA reports did in the six months prior to v4.0, measured
  over a comparable wave count. (If falsification is weaker than
  pre-specification in practice, the research foundation overestimated the
  asymmetry.)
- Colby's feedback loop produces false-pass reports -- changes declared done
  after execution that regress behavior in the next wave -- at a rate above
  the pre-v4.0 Roz-verified rate. (If execution is cheaper but also less
  discriminating, the tradeoff inverted.)
- Sarah's 1-2 page ADRs leave Colby guessing at the intended scope often
  enough that he re-invokes Sarah mid-wave. (If the format under-specifies
  in practice, the long-form contract was load-bearing after all.)

Any one of these over a rolling 10-wave window is a revisit trigger, not a
single-incident one. A single miss is noise.

## Sources

See CHANGELOG v4.0.0 for the full research citation list and migration
notes. The scope brief that drove execution is at
`docs/pipeline/v4-scope.md`.
