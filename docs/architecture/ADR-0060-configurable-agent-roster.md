# ADR-0060: Configurable Agent Roster and Roster-Aware Enforcement

## Status
Accepted.

## Context

Today every install ships the full agent set and every hook in
`.claude/settings.json` assumes that set is present. `enforce-sequencing.sh`
hardwires Ellis-after-Poirot and Agatha-after-build gates; the brain capture
gate (`enforce-brain-capture-gate.sh` + `enforce-brain-capture-pending.sh`)
carries an explicit allowlist of eight producers; the SubagentStop pipeline
and the `prompt-brain-prefetch.sh` clause name agents by literal string. A
fresh install therefore costs the user the full ceremony whether they
wanted it or not, and absent agents would currently produce "waiting for
Poirot" deadlocks rather than skipping cleanly.

The product spec at `docs/product/pipeline-redesign-spec.md` calls for a
minimal default install (Robert, Sarah, Colby), an explicit opt-in model
for every other agent with a per-agent firing position
(`after-every-unit` | `pipeline-end` | `on-demand`), and a lightweight
commit path when Ellis is absent. The non-negotiable constraint from
AC #15-16 is that existing full-roster installs must keep working through
the upgrade and that absent agents must never block pipeline progress.

ADR-0046 already trimmed v3 ceremony; this ADR extends that trajectory by
giving the user control over which agents constitute "the pipeline" for
their project, and by moving the source of that truth out of hook scripts
and into configuration.

## Options Considered

**Option A — Roster lives in `pipeline-config.json`; hooks consult it and
skip gracefully.** Add an `agent_roster` block to `pipeline-config.json`
keyed by agent name with `enabled` and `firing` fields. Each existing hook
that references a specific agent reads the roster early and exits 0 when
the agent is disabled. `/pipeline-setup` writes the roster at install
time and updates `settings.json` hook registrations to match. Generic
commit is an Eva capability (not an agent) that activates when
`roster.ellis.enabled` is false. This is what we are picking: one source
of truth, hooks become roster-aware in place rather than being rewritten,
and the existing full-roster install just keeps the roster fully
populated.

**Option B — Generate `settings.json` from the roster; keep hooks naive.**
The roster lives in config but hooks never read it; instead
`/pipeline-setup` generates `settings.json` so that disabled agents'
hooks simply are not registered. Cleaner separation, but it has two
sharp edges: (1) hook registration becomes a generated artifact that
drifts whenever someone edits `settings.json` by hand, and (2) hooks
that fire on `Agent` invocations with a `matcher` (e.g.
`enforce-sequencing.sh`) still encode multi-agent ordering rules in
their bodies — those rules need to know which agents exist regardless of
whether each individual hook is registered. We would end up doing the
roster lookup anyway, just in a more brittle place.

**Option C — Keep hooks hardwired; gate roster enforcement only at
invocation time.** Eva consults the roster before invoking agents and
just never calls disabled ones. Hooks stay untouched. Simplest, but it
moves all enforcement into Eva's discipline and undoes the mechanical
guarantee that hooks provide. The brain capture pending marker would
still get written for stopping agents Eva chose not to invoke (it
wouldn't, by construction), but the sequencing gate would still block
Ellis on `poirot_reviewed=true` even when Poirot is not on the roster.
Brittle in the exact way we're trying to fix.

## Decision

The active roster lives in `agent_roster` inside `pipeline-config.json`
and is the single authority on which agents exist for a project.
Roster-touching hooks — `enforce-sequencing.sh`,
`enforce-brain-capture-pending.sh`, `enforce-brain-capture-gate.sh`,
and the `if:`-clause filters in `settings.json` for
`prompt-brain-prefetch.sh` — read the roster and exit 0 when the
referenced agent is disabled. When Ellis is absent from the roster, Eva
operates a generic commit path (one-question, no persona, no changelog)
in response to commit intent.

Colby writes a behavioral test for the "absent agent never blocks" path
because a single missed roster check anywhere in the gate chain would
recreate the deadlock this ADR exists to prevent.

Colby writes a behavioral test for the Ellis-absent commit flow because
a regression that re-routes generic commit through the Ellis persona
would silently restore the ceremony we are removing.

### Factual Claims
- `.claude/settings.json` registers `enforce-sequencing.sh`, `enforce-brain-capture-pending.sh`, `enforce-brain-capture-gate.sh`, `prompt-brain-prefetch.sh`, and `enforce-pipeline-activation.sh` against the `Agent` matcher and need roster-aware skip logic.
- `enforce-sequencing.sh` hardwires Ellis (Gates 0, 1, 3, 4, 5), Agatha (Gate 2), and investigator (Gate 0b) — each gate must short-circuit when its agent is disabled.
- `enforce-brain-capture-pending.sh` carries an explicit producer allowlist `sarah|colby|agatha|robert|robert-spec|sable|sable-ux|ellis`; this allowlist must be intersected with the active roster at runtime.
- `pipeline-config.json` currently has no `agent_roster` key; the new schema adds it with `robert`, `sarah`, `colby` always `enabled: true, firing: "core"`.
- `dashboard_mode` is currently present in `pipeline-config.json` and must be removed during setup migration.
- `enforcement-config.json` lives at `.claude/hooks/enforcement-config.json` and is separate from `pipeline-config.json`; roster lookups read `pipeline-config.json`, not `enforcement-config.json`.
- The generic commit capability is an Eva behavior, not an agent; it does not need a persona file and does not need to appear in the roster.
- `agent_roster` schema: `{ enabled: bool, firing: "core" | "after-every-unit" | "pipeline-end" | "on-demand" }`. `firing: "core"` is reserved for Robert/Sarah/Colby and is not selectable in the wizard.

### LOC Estimate
~350 lines changed across ~12 files (5 hook scripts, settings.json, pipeline-config.json schema + default, /pipeline-setup, Eva persona generic-commit section, 2-3 reference docs).

## Rationale

Option A wins because the roster is conceptually a config concern and
hooks are already the right enforcement layer — the missing piece is
just that hooks were written against a fixed roster. Reading
`pipeline-config.json` from a hook is a five-line `jq` call we already
do in `enforce-sequencing.sh` Gate 0 and Gate 5; extending that pattern
to the gates that name specific agents is mechanical, not architectural.

Option B's generated `settings.json` sounds clean until you remember
that `enforce-sequencing.sh` encodes the *relationships* between
agents (Ellis depends on Poirot's review, Agatha follows the build
phase) — those relationships don't disappear when an agent is disabled,
they need to be conditionally skipped. The hook has to read the roster
either way. Generating `settings.json` would still be valuable as a
second-order cleanup (don't register hooks you'll no-op anyway), but it
is not the load-bearing decision and we can do it later without
re-architecting.

Option C's "Eva just doesn't invoke disabled agents" loses the
mechanical guarantee. A future agent persona that calls Ellis directly,
or a discovered-agent flow that bypasses Eva, would punch straight
through the roster. Hooks are where the floor lives.

Out of scope inline: dashboard and kanban removal is mentioned in the
spec but is a deletion pass, not a design decision — Colby strips the
files and the `dashboard_mode` key during setup migration; there is no
architectural choice to make. Per-feature firing overrides and dynamic
roster changes mid-pipeline are explicitly deferred (spec Out of Scope).
Robert-spec and sable-ux are skill-activated producers, not pipeline
agents — they stay outside the roster as today; the roster covers only
agents Eva invokes in pipeline phases.

Rollback sketch: the roster is additive — if a hook's roster-aware skip
logic misfires, reverting that hook to its hardwired form is a per-file
revert and the roster block in `pipeline-config.json` becomes a no-op
read. No schema migration is destructive: `agent_roster` absent means
"behave as v5" (the missing-key fallback path the hooks must already
honor for upgrades).

The shape of the risk worth naming: if a hook reads the roster but the
roster key is malformed or missing in an upgraded install, the hook
must fail *open* (let the agent through) — failing closed would
deadlock the upgrade path. Every roster-aware skip needs the same
fallback pattern as the existing `enforcement-config.json` reads:
default to "agent enabled" when the key is absent.

## Falsifiability

Revisit if any of these happen:

- A minimal-install user reports a pipeline phase blocking on
  "waiting for Poirot" or any absent agent — the roster-aware skip
  failed somewhere.
- A full-roster install upgraded from v5 reports a hook that newly
  blocks because its roster lookup defaulted disabled-on-missing
  instead of enabled-on-missing — the open-fail default was wrong.
- Users routinely re-enable Ellis after trying generic commit because
  the one-question flow misses something material (e.g. they actually
  do want a changelog) — the "no ceremony" call was too aggressive
  and Ellis-lite is a real product, not the fallback we thought.
- Per-feature firing overrides become a recurring user request within
  the first three months — the per-install firing model was too
  static.

## Sources

- `docs/product/pipeline-redesign-spec.md` — spec, acceptance criteria 1-34
- `.claude/hooks/enforce-sequencing.sh` — current hardwired gates
- `.claude/hooks/enforce-brain-capture-pending.sh:50-53` — producer allowlist
- `.claude/settings.json:32-62` — current Agent matcher chain
- `.claude/pipeline-config.json` — current config schema
- `docs/architecture/ADR-0046-pipeline-v4-redesign.md` — prior ceremony trim
- `docs/architecture/ADR-0053-mechanical-brain-capture-gate.md` — capture gate mechanism
