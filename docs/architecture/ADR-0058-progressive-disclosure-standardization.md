# ADR-0058: Progressive-Disclosure Standardization for Skills, Agents, and Slash Commands

## Status
Accepted.

## Context

Anthropic's published guidance for skill authoring recommends a progressive-disclosure pattern: a short top-level entrypoint (SKILL.md, persona file, command file) that lists what the consumer can load on demand, with the heavy material lifted into companion files that the model only reads when the task requires them. The recommended split threshold is around 500 lines.

This codebase already uses the pattern at the agent layer. Agent persona files in `source/shared/agents/` reference on-demand companion files in `source/shared/references/` (`agent-preamble.md`, `dor-dod.md`, `invocation-templates.md`, `design-system-loading.md`, `pipeline-operations.md`, and others). Colby's persona file is 234 lines and offloads shared DoR/DoD, brain-context discipline, and invocation discipline to those references. That layer is healthy.

The pattern is *not* applied at the plugin-skill layer. `skills/pipeline-setup/SKILL.md` is 1,482 lines -- nearly 3x the guideline -- and bundles installation flow, hook registration logic, post-install verification, and the full directory layout into one file. `skills/brain-hydrate/SKILL.md` is 511 lines and bundles scout fan-out and extraction-principle content alongside the run procedure. Both files have observable sections that are only relevant on certain branches of the skill's execution (e.g., post-install verification fires once, at the end), but the model reads the whole file every time the skill is invoked.

Slash command files in `source/shared/commands/` are all under the 500-line guideline today, but the convention is uneven: some commands offload references and some inline content that future growth would push over the threshold. Standardizing now is cheap; standardizing later means refactoring each command on its own pipeline cycle.

The decision we want to codify: every skill, agent persona, and slash command in this plugin follows the same progressive-disclosure shape, with functional filenames for bundled split files (not generic `CONTEXT.md`).

## Options Considered

**Option A: Split skills on the 500-line threshold using generic `CONTEXT.md` filenames.** Mirrors one variant of Anthropic's public example structure. Cheap to apply mechanically. Rejected because when a parent file has more than one split (and `pipeline-setup` will have three), generic filenames force a numeric suffix (`CONTEXT.md`, `CONTEXT2.md`, `CONTEXT3.md`) and lose meaning on a directory listing. A maintainer scanning `ls skills/pipeline-setup/` should be able to tell what each split contains without opening it.

**Option B: Follow Anthropic's published example structure verbatim, including their specific filenames and section headings.** Lowest deviation cost from upstream guidance and easiest to defend in code review. Rejected because Anthropic's example is illustrative, not prescriptive -- the underlying pattern is progressive disclosure with sensible names, and "sensible names" in this codebase are the functional ones the agent-layer references already use (`agent-preamble.md`, `design-system-loading.md`, etc.). Adopting the example verbatim would create two naming conventions in the same plugin.

**Option C: Standardize skills and agents, but leave slash commands alone because none cross the threshold today.** Lower-effort. Rejected because the slash command files are the public-surface contract for `/pm`, `/architect`, `/pipeline`, etc., and inconsistency between commands ("this one offloads, this one doesn't") imposes a re-derivation cost on every future command author. The slash-command standardization is cheap precisely because no command crosses the threshold -- the work is structural, not content-moving.

**Option D (chosen): Standardize all three layers -- skills, agent personas, slash commands -- on the same progressive-disclosure shape with functional split filenames.** One convention, one threshold (~500 lines), one naming rule (functional, not generic). The agent layer is already compliant. The skill layer gets the bulk of the immediate refactor work. The slash-command layer gets a structural pass for consistency.

## Decision

Skills, agent personas, and slash commands in this plugin follow Anthropic's progressive-disclosure pattern. The top-level entrypoint stays short and references on-demand companion files. The split threshold is approximately 500 lines per file. Bundled split files use functional filenames that describe their content (`hooks.md`, `extraction.md`, `post-install.md`, `scout-fanout.md`), not generic ones (`CONTEXT.md`).

The agent layer is already compliant via `source/shared/references/` and stays as-is. The skill layer is the immediate refactor target: `skills/pipeline-setup/SKILL.md` splits into three companions (hooks, post-install, directory-layout), and `skills/brain-hydrate/SKILL.md` splits into two (scout-fanout, extraction). The slash-command layer gets a structural pass for consistency even though no command file currently exceeds the threshold -- the rule is what's being standardized, not the line counts.

### Factual Claims

- `skills/pipeline-setup/SKILL.md` is 1,482 lines.
- `skills/brain-hydrate/SKILL.md` is 511 lines.
- `source/shared/agents/colby.md` is 234 lines and references companion files in `source/shared/references/`.
- `source/shared/references/agent-preamble.md` is 90 lines and is the established example of an on-demand companion file.
- `source/shared/references/` contains 16 companion files in the agent-layer pattern.
- No file in `source/shared/commands/` currently exceeds 500 lines.
- `skills/brain-uninstall/` and `skills/pipeline-uninstall/` directories exist and are in scope for the same convention if their `SKILL.md` files approach the threshold.

### LOC Estimate

~150 lines moved across ~10 files in the skill-layer refactor (no net new content for skills; bulk is relocation from `SKILL.md` into the functional companions). Slash-command standardization is a structural pass with negligible LOC impact (~20 lines of reference pointers added across command files). Agent layer is unchanged.

## Rationale

Option D beats A and B on the naming question because functional names are self-documenting on a directory listing -- a maintainer scanning `skills/pipeline-setup/` should be able to tell that `hooks.md` is about hook registration and `post-install.md` is about post-install verification without opening either. Generic names lose that property the moment a parent file has more than one split, which `pipeline-setup` requires today.

It beats C on the consistency question because slash commands are the public-surface contract for the pipeline's user-facing entrypoints, and the standardization cost is structurally trivial when no file is over the threshold. The work is rule-establishing, not content-moving. Future commands inherit the convention without re-deriving it.

The pattern is already proven in this codebase at the agent layer. `source/shared/references/agent-preamble.md`, `dor-dod.md`, and friends have been load-bearing for multiple pipeline cycles without drift problems. The skill layer adopts the same shape, the same threshold, and the same naming rule. There is no new mechanism to validate -- only an existing mechanism applied to a layer where it isn't yet.

Risk shape: if a split file drifts out of sync with the parent `SKILL.md` (e.g., the parent describes a step that the companion no longer documents), a future skill invocation reads stale guidance and a step is skipped or duplicated. The agent-layer references have not suffered this in practice because the entrypoint enumerates what it offloads. The skill-layer companions follow the same enumeration rule: the parent file lists its companions and what each contains, so a drift between the listing and the companion is locally detectable.

Out of scope: changing the content of any skill, agent, or command; changing how Claude Code or Cursor loads files; changing the agent-layer references; touching `mybrain` or other separate plugins. This ADR codifies a structural convention, not a content rewrite.

Rollback sketch: a revert is a git revert of the skill-layer refactor commits. No schema, no hooks, no runtime contract changes. The agent layer is untouched, so reverting the skill layer leaves the codebase in a consistent (if inconsistent-across-layers) state.

## Falsifiability

Revisit this ADR if any of the following holds after the refactor lands and runs for one calendar month of normal use:

- A skill invocation produces a known-buggy outcome traced to Claude not loading a companion file the parent `SKILL.md` referenced -- meaning the progressive-disclosure mechanism is unreliable at the skill layer in a way it is not at the agent layer.
- Two or more maintainers (or one maintainer twice) report that they could not find content they expected in a skill's directory, and the content was in a companion file with a name that did not signal its presence. (Signal: functional naming isn't actually self-documenting in practice.)
- A split companion drifts out of sync with its parent `SKILL.md` in a way that ships a broken skill -- the parent describes a step the companion no longer documents, or vice versa, and the divergence isn't caught at review time. (Signal: the enumeration-at-the-entrypoint discipline is insufficient as a drift guard and needs a mechanical check.)

## Sources

- Anthropic skill-authoring guidance: progressive disclosure with ~500-line entrypoints.
- `source/shared/references/` -- 16 companion files demonstrating the pattern at the agent layer.
- `source/shared/agents/colby.md`, `sarah.md`, etc. -- entrypoints that reference companions.
- `skills/pipeline-setup/SKILL.md` (1,482 lines) and `skills/brain-hydrate/SKILL.md` (511 lines) -- the immediate refactor targets.
- ADR-0057 -- precedent for codifying mechanical defaults across rule files.
