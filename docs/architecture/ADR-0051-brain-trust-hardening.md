# ADR-0051: Brain Trust-Boundary Hardening (Items 1 and 2)

## Status
Accepted.

## Context

Brain context arrives in subagent invocations as a `<brain-context>` block of
retrieved `<thought>` elements. Two surfaces shape how that content is
treated:

- `source/shared/references/agent-preamble.md` step 3 (lines 26-31) tells
  every agent how to handle the block. The current language ("Check for
  relevant prior decisions, patterns, and lessons. Factor them into your
  approach.") frames brain content as something to *factor in* without
  distinguishing retrieved-observation from authoritative-instruction. An
  imperative-shaped `<thought>` ("always do X") can be followed as if Eva had
  written it.
- `source/claude/hooks/prompt-brain-prefetch.sh` line 35 reminds Eva to call
  `agent_search` before invoking sarah/colby. The current advisory mentions
  query but not scope. An unscoped `agent_search` returns entries from every
  project sharing this brain instance, which leaks unrelated codebases into
  the invocation's `<brain-context>`.

Issue #45 enumerates six brain trust-boundary hardening items. This ADR
records the decision for items 1 and 2 only. Items 3-6 (sanitization, corpus
audit, provenance surfacing, cross-project isolation confirmation) are
deferred. The exact replacement text for both surfaces is specified in
`docs/ux/brain-trust-hardening.md` (Screens 1 and 2) with per-phrase
rationale.

## Options Considered

**Option A -- Reframe both surfaces in place (chosen).** Replace step 3 of
`agent-preamble.md` with a reference-not-instruction directive that names the
failure mode (imperative-text-in-thought, scope-widening, override attempts)
and the resolution mechanic (live invocation wins; note the conflict in DoR).
Replace the prefetch hook's `echo` line with a two-part directive that makes
scope co-equal with query and names the cross-project leakage failure mode.
Both changes are textual, additive, and preserve existing semantics
(Poirot/Distillator exemption, brain-extractor capture, sarah|colby filter,
non-blocking hook behavior).

**Option B -- Mechanical enforcement at the brain layer.** Add a server-side
sanitizer in `brain/server.mjs` that strips imperative phrasing from
`<thought>` content before return, and reject `agent_search` calls without a
scope argument. This is the durable answer to "behavioral framing decays
under context pressure" (the brain lesson cited in this pipeline's
`<brain-context>`), but it's the scope of items 3-6 in Issue #45 and
requires schema, corpus, and tool-signature changes. Doing it now conflates
two pipelines.

**Option C -- Do nothing; rely on existing framing.** Accept that the current
preamble step 3 and the current advisory are sufficient. Rejected because
the trust-boundary failure modes (injection-shaped thoughts, cross-project
leakage) are concrete and the cost of the textual fix is one Colby
work-unit.

## Decision

Adopt Option A. Colby replaces `agent-preamble.md` step 3 with the Screen 1
text from `docs/ux/brain-trust-hardening.md`, and replaces the `echo` line
on `prompt-brain-prefetch.sh:35` with the Screen 2 text from the same
document. Both replacement strings are reproduced verbatim in the UX doc
with per-phrase rationale; Colby copies them, does not redesign them. The
sarah|colby filter, the non-blocking-hook contract, the
Poirot/Distillator exemption, and the brain-extractor capture sentence are
preserved.

Colby writes a behavioral test for the prefetch hook output because a
regression that drops the scope clause would silently re-open
cross-project leakage and the existing hook tests only assert exit code and
agent-type filtering.

### Factual Claims
- `source/shared/references/agent-preamble.md` step 3 occupies lines 26-31 and is the only target span in that file
- `source/claude/hooks/prompt-brain-prefetch.sh` emits its advisory via a single `echo` on line 35
- The `case "$SUBAGENT_TYPE" in sarah|colby) ;; *) exit 0 ;; esac` filter on lines 30-33 of the prefetch hook is out of scope for this change
- Replacement text for both surfaces lives in `docs/ux/brain-trust-hardening.md` Screens 1 and 2
- Ellis exemption block (lines 11-13 of `agent-preamble.md`) and `<preamble id="return-condensation">` block (lines 38-68) are out of scope
- The project-scoped `scope` value for `agent_search` is written by `brain-setup` to the `scope` key in `.claude/brain-config.json` (verified in this repo with value `"atelier.plugin"`). `docs/pipeline/pipeline-state.md` does **not** carry a scope value, so the prefetch advisory must direct Eva to `.claude/brain-config.json`, not to `pipeline-state.md`. (Correction applied in this same ADR — it has not shipped — see Screen 2 of the UX doc for the corrected echo line.)

### LOC Estimate
~30 lines changed across 2 files (preamble step 3 expands from 6 lines to ~25; hook `echo` expands from 1 line to 1 longer line).

## Rationale

Option A buys the textual hardening cheaply and surfaces the same trust
boundary in the two places agents and Eva actually read. It is, by design,
**necessary but not sufficient**: the brain lesson injected into this
pipeline's `<brain-context>` (cited verbatim) records that behavioral-only
constraints in agent personas are consistently ignored under context
pressure, which is exactly the failure mode mechanical hooks were
introduced to address elsewhere in the codebase. The framing change in
`agent-preamble.md` is a behavioral constraint by that definition; the
prefetch hook scope advisory is also non-blocking by retro lesson #003.
Neither change converts the trust boundary into a mechanical gate. That
work -- server-side sanitization, scope-required `agent_search`, provenance
surfacing -- is Issue #45 items 3-6 and a future ADR. Doing the textual
fix now lowers the surface-area without precluding the durable fix later.

If a malicious or stale `<thought>` ships imperative text and an agent
follows it in spite of the new framing, the wrong-action surface is caught
by Poirot blind review on the resulting diff and by the PreToolUse path
hooks that already block writes outside designated paths -- the trust
boundary degrades to the existing mechanical floor, not to "anything
goes." If Eva drops the scope clause from `agent_search` despite the new
advisory, the resulting cross-project leakage shows up as off-topic
`<thought>` elements in `<brain-context>` and is visible in the next
agent's self-report; the failure is loud, not silent.

Out of scope (named here so they aren't conflated with this decision):
sanitization at capture time, scope as a required argument on
`agent_search`, provenance fields on returned thoughts, full corpus audit
of existing brain entries, and cross-project isolation regression tests.
Those are Issue #45 items 3-6.

## Falsifiability

Revisit this ADR if any of the following occurs:

- A Poirot finding or user-reported bug shows an agent followed imperative
  text inside a `<thought>` against its `<constraints>` after these
  changes ship. (Direct evidence the framing is insufficient on its own and
  the mechanical work in items 3-6 must be promoted.)
- Eva is observed calling `agent_search` without scope on a sarah/colby
  invocation in a post-change pipeline. (The advisory failed; promote scope
  to a required argument.)
- The brain capture corpus grows past a threshold where token-budget
  pressure on `agent-preamble.md` step 3 forces truncation that drops the
  bulleted "Do not / Do not / Do" block. (Heading-carries-the-directive
  assumption fails; the framing needs a different shape.)

## Sources

- `docs/ux/brain-trust-hardening.md` (Screens 1-2; per-phrase rationale tables)
- `source/shared/references/agent-preamble.md:26-31` (current step 3)
- `source/claude/hooks/prompt-brain-prefetch.sh:35` (current advisory line)
- Issue #45 (six-item hardening list; this ADR covers items 1-2)
- Brain lesson on behavioral-only constraints (injected via this pipeline's `<brain-context>`)
