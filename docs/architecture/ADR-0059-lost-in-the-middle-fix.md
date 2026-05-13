# ADR-0059: Lost-in-the-Middle Fix for Eva's Forbidden-Actions Gate

## Status
Accepted.

## Context
Eva's `<gate id="no-code-writing">` rule -- the contract that she never uses
`Write`/`Edit`/`MultiEdit` outside `{pipeline_state_dir}` -- is loaded at every
session boot via `default-persona.md`. The hook `enforce-eva-paths.sh` enforces
the rule mechanically. Both layers exist; both work. The rule still does not
bind reliably at decision time.

Observed failure this session: Eva fired six `Edit` calls on version manifests
in a single batch, each blocked by `enforce-eva-paths.sh`, before she
re-routed to Ellis. The hard block did its job. The persona instruction did
not stop the attempt from forming.

Two structural facts explain the drift:

1. **Position in file.** `<gate id="no-code-writing">` sits at lines 68-89 of
   `source/shared/rules/default-persona.md` (175 lines total -- 38-51% of the
   file). The file ends with `<section id="non-requirements">` ("What This
   Does NOT Mean"), a soft passage about not over-routing. The most binding
   rule in the file is in the middle; the end is a hedge.
   `source/shared/rules/agent-system.md` (275 lines) ends with
   `## Agent Teams (Experimental)` -- an opt-in feature flag.
2. **Anthropic's own guidance.** Per claude.com/docs prompting best practices:
   "longform data at the top, queries and instructions at the end can improve
   response quality by up to 30%." Both rule files end with non-binding
   content.

ADR-0005 already diagnosed the same silent-drop failure mode for brain reads:
agents at the bottom of long files ignored brain instructions. The fix was to
stop relying on static placement and inject the instruction at the moment of
decision (Eva pre-fetches; injects `<brain-context>`). The brain-capture gate
(ADR-0053) layers the same architecture: hard hook blocks, soft hook
(`prompt-brain-capture-reminder.sh`) injects curated guidance at the moment
of the Agent invocation. JIT injection is our proven pattern.

## Options Considered

**Option 1 -- Reorder only (Path A in isolation).** Move the gate to the end
of `default-persona.md` and the binding rule section to the end of
`agent-system.md`. Cheap, no new code, follows Anthropic guidance. But still
relies on the rule remaining loaded and salient across long sessions and
compaction. Position helps; it is not sufficient when the model is mid-batch
on a 6-tool plan.

**Option 2 -- JIT injection hook only (Path B in isolation).** Mirror
`prompt-brain-capture-reminder.sh`: a PreToolUse prompt hook on
`Write|Edit|MultiEdit` that, when Eva is on the main thread and the target
path is outside `{pipeline_state_dir}`, injects a soft reminder telling Eva to
route to Colby (code) or Ellis (git plumbing/manifests). Always exits 0; the
existing hard block stays as the backstop. This is the right architecture per
ADR-0005, but a JIT signal without good static placement is asking the hook
to compensate for a known prompt-design flaw -- redundant signal without
fixing the prompt itself.

**Option 3 -- Both paths together (chosen).** Reorder the two rule files so
each ends with a binding rule (Path A), AND add the JIT hook so the rule is
re-asserted at the exact moment Eva proposes a forbidden tool call (Path B).
Adopt a convention that future additions to these two files cannot push
binding rules deeper. Belt and suspenders: structural placement makes the
rule salient at boot and after compaction; JIT injection catches the
mid-batch case where Eva has drifted into "I'll just edit this" mode.

## Decision

Land Path A and Path B together as a single coherent fix.

**Path A -- Reorder.** Move `<gate id="no-code-writing">` (with its nested
`<protocol id="user-bug-flow">`) to the end of
`source/shared/rules/default-persona.md`. Relocate the soft
`<section id="non-requirements">` content into the body of the file so the
file ends on the binding gate. In `source/shared/rules/agent-system.md`, move
the binding rule blocks (the `<gate id="no-skill-tool">` "Custom Commands Are
NOT Skills" gate, and the agent invocation rules) to the end; relocate
`## Agent Teams (Experimental)` earlier in the file. The file ends on a
binding rule, not an experimental opt-in.

**Path A convention clause.** New content added to `default-persona.md` and
`agent-system.md` must not push binding rules deeper into the middle. The end
of each file remains a binding rule. Documented inline in each file as an
HTML comment at the top so future contributors see it before editing.

**Path B -- JIT injection hook.** Add
`source/claude/hooks/prompt-eva-path-reminder.sh` modelled on
`prompt-brain-capture-reminder.sh`: PreToolUse prompt hook matched against
`Write|Edit|MultiEdit`. Always exits 0. Reads the `tool_input.file_path`,
strips it to project-relative using the same normalization as
`enforce-eva-paths.sh`, and if (a) `agent_id` is empty (main thread, i.e.
Eva) and (b) the path is not `docs/pipeline/*` and not one of the two
`$HOME`-rooted exceptions, emits a short reminder: "This file is outside
{pipeline_state_dir}. Route to Colby for code, Ellis for git plumbing and
version manifests. The hard gate will block this call." Register the hook in
`.claude/settings.json` so it fires before `enforce-eva-paths.sh` in the
existing `Write|Edit|MultiEdit` PreToolUse matcher.

Colby exercises the new hook against a known-blocked path to confirm the
reminder text appears before the hard-block error. He also confirms the hook
exits 0 on every code path (no silent failures that would convert it from
advisory to blocking).

### Factual Claims
- `source/shared/rules/default-persona.md` is 175 lines; `<gate id="no-code-writing">` is at lines 66-136; file currently ends at line 175 with `</section>` closing `<section id="non-requirements">`.
- `source/shared/rules/agent-system.md` is 275 lines; currently ends at line 275 with `</section>` closing `<section id="agent-teams">` ("Agent Teams (Experimental)").
- `source/claude/hooks/prompt-brain-capture-reminder.sh` exists and is the structural template for the new hook: reads stdin JSON, gates on `tool_name`, gates on empty `agent_id` for main-thread-only, always exits 0.
- `source/claude/hooks/enforce-eva-paths.sh` already implements the path normalization (`PROJECT_ROOT` strip, Windows separator handling, two `$HOME`-rooted exceptions for memory and out-of-repo session state); the new hook reuses the same normalization logic.
- `.claude/settings.json` already has a `Write|Edit|MultiEdit` PreToolUse matcher containing `enforce-eva-paths.sh`; the new hook is added to the same matcher block as a `"type": "prompt"` entry before the existing command hook.
- The installed copies at `.claude/rules/default-persona.md` and `.claude/rules/agent-system.md` are derived from `source/shared/rules/` and must be kept in sync per the triple-target convention in CLAUDE.md.

### LOC Estimate
~120 lines changed across 5 files: ~70 lines of relocation in the two rule files (source + installed copies = 4 files), plus ~60 lines for the new hook, plus ~5 lines of settings.json registration.

## Rationale

Path A alone is partial: position helps but the lost-in-the-middle effect
also reappears after long sessions and compaction; the static fix decays.
Path B alone is redundant signal layered over a known prompt-design flaw; we
would be paying for a hook to compensate for something we could fix in the
prompt. Together they cover both regimes: Path A makes the rule salient at
boot and after `post-compact-reinject.sh` runs; Path B re-asserts the rule at
the exact moment Eva drifts mid-batch.

The pattern is not novel -- ADR-0005 established it for brain reads, ADR-0053
extended it to brain-capture (hard gate + soft reminder). Applying it to the
forbidden-actions gate is the consistent move. The hard block
(`enforce-eva-paths.sh`) stays unchanged; it is the safety net, not the
primary deterrent.

Risk shape: if the soft-reminder text is too verbose or fires too often, Eva
learns to ignore it the way she sometimes ignores boot content -- the
reminder becomes noise. Keep the message short, action-oriented, and
constrained to the main-thread-from-Eva case (subagents skip).
Counter-risk: if the convention clause is not enforced over time, contributors
will append new sections at the end of the files and re-create the original
problem. The clause is documentation, not a hook -- if it does not hold, the
falsifiability signal below catches it.

No DB or cross-service contract changes; rollback is `git revert` on the
reorder commit plus removing the hook registration from `settings.json`.

## Falsifiability

We will know this decision was wrong if any of the following hold one month
after landing:

1. **Hard block still fires from Eva on the main thread.** If
   `enforce-eva-paths.sh` continues to BLOCK Eva's `Write`/`Edit`/`MultiEdit`
   attempts at the historical rate (sample the last 30 days of session
   logs), the structural + JIT fix did not bind. Revisit by tightening the
   reminder copy or hardening the convention.
2. **Soft reminder fires and Eva proceeds anyway.** If the
   `prompt-eva-path-reminder.sh` invocation log shows the reminder fired and
   the immediately-following tool call was the same `Write`/`Edit` to the
   same path, JIT injection is insufficient signal for this rule. Escalate
   to a confirmation prompt or remove the reminder as dead weight.
3. **New lost-in-the-middle problem.** If audit of either rule file shows a
   binding rule has been pushed below a non-binding section (the end of the
   file is no longer a binding rule), the convention clause is not holding
   and needs a mechanical guard.

## Out of Scope

- Other agent persona files (Colby, Sarah, Poirot, Ellis, etc.). They end with
  `## DoD: Verification` / `## Findings`, which is structurally a binding
  output spec at the end; no change needed.
- `pipeline-orchestration.md`. The Mandatory Gates section sits at line 105
  of the file (upper zone, ~21%). Acceptable. Not touched.
- `.claude/settings.json` permission allowlist. The `Edit` grant stays broad;
  the hooks layer (hard block + soft reminder) is doing the binding work.
- Any existing ADR. ADR-0005, ADR-0053, and ADR-0057 are not modified --
  this ADR extends their pattern; it does not revise them.
- The hard-block contract in `enforce-eva-paths.sh`. Untouched.

## Load-Bearing Files

Colby edits:

- `source/shared/rules/default-persona.md` -- reorder: move
  `<gate id="no-code-writing">` (and nested `<protocol id="user-bug-flow">`)
  to the end of the file; relocate `<section id="non-requirements">` content
  earlier; add the convention HTML comment at the top.
- `source/shared/rules/agent-system.md` -- reorder: move the binding rule
  blocks (`<gate id="no-skill-tool">`, agent invocation rules) to the end;
  relocate `## Agent Teams (Experimental)` earlier; add the convention HTML
  comment at the top.
- `.claude/rules/default-persona.md` and `.claude/rules/agent-system.md` --
  installed copies must mirror the source changes (triple-target convention).
- `source/claude/hooks/prompt-eva-path-reminder.sh` -- new file, modelled on
  `prompt-brain-capture-reminder.sh`, reusing path normalization from
  `enforce-eva-paths.sh`. Always exits 0.
- `.claude/hooks/prompt-eva-path-reminder.sh` -- installed copy of the new
  hook.
- `.claude/settings.json` -- register the new prompt hook in the existing
  `Write|Edit|MultiEdit` PreToolUse matcher, before
  `enforce-eva-paths.sh`.

## Sources

- ADR-0005 (XML-based prompt structure / JIT injection pattern):
  `docs/architecture/ADR-0005-xml-based-prompt-structure.md`.
- ADR-0053 (mechanical brain-capture gate, hard+soft hook architecture):
  `docs/architecture/ADR-0053-mechanical-brain-capture-gate.md`.
- ADR-0057 (Eva brain-capture style, downstream of the same gate):
  `docs/architecture/ADR-0057-eva-brain-capture-style.md`.
- Anthropic prompting best practices (claude.com/docs, fetched 2026-05-13):
  "Put longform data at the top: Place your long documents and inputs near
  the top of your prompt, above your query, instructions, and examples."
  "Queries at the end can improve response quality by up to 30% in tests,
  especially with complex, multi-document inputs."
- Soft-reminder template: `source/claude/hooks/prompt-brain-capture-reminder.sh`.
- Hard-block reference: `source/claude/hooks/enforce-eva-paths.sh`.
- Hook registration site: `.claude/settings.json` (PreToolUse
  `Write|Edit|MultiEdit` matcher).
