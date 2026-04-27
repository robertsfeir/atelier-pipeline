# ADR-0048: Scout and Synthesis Model Pinning via Registered Subagents

## Status
Accepted.

## Context

ADR-0047 Phase 4 pinned explicit model IDs (`claude-opus-4-7`,
`claude-sonnet-4-6`, `claude-haiku-4-5-20251001`) into the frontmatter of
every custom agent persona, defeating alias drift on those agents. Two
invocation paths were left untouched and remain on generic aliases:

1. **Scouts.** Eva spawns scout fan-out as
   `Agent(subagent_type: "Explore", model: "haiku")`. `Explore` is a
   Claude Code built-in subagent type for read-only file/grep/read work —
   it is not registered under `source/{claude,cursor}/agents/` and has no
   frontmatter we own. The `model: "haiku"` parameter is the only model
   selector on the call site.
2. **Synthesis.** Eva spawns the post-scout synthesis pass as
   `Agent(subagent_type: "general-purpose", model: "sonnet", effort: "low")`.
   `general-purpose` is also a built-in. ADR-0042 explicitly deferred
   creating a dedicated synthesis persona; the inline-prompt approach was
   accepted as provisional.

Anthropic's `Agent` tool resolves models in this order:
(1) `CLAUDE_CODE_SUBAGENT_MODEL` env var, (2) per-invocation `model` param,
(3) subagent frontmatter `model`, (4) main conversation model. Empirically,
the per-invocation `model` parameter only accepts aliases — passing a
versioned ID returns InputValidationError. The frontmatter `model` field
DOES accept versioned IDs. Phase 4's pinning works precisely because
custom agents own frontmatter that resolution falls through to when no
per-invocation override is present. Scouts and synthesis fail this test:
both explicitly pass an alias on every call site, so resolution stops at
step 2 and frontmatter is never consulted — even if the underlying type
had any.

The result is a silent durability gap. Any future Anthropic alias remap
would shift scouts and synthesis off Haiku 4.5 / Sonnet 4.6 with no
warning, invalidating the call-efficiency assumptions that ADR-0047's
tightened `maxTurns` budgets and the synthesis Tier 2 assignment in
`pipeline-models.md` rest on. Mechanical enforcement (`enforce-scout-swarm.sh`,
`.claude/settings.json`) currently keys off `subagent_type == "Explore"`
in two places: the format-contract check at line 43 of the hook, and the
sequencing-exemption guard at line 33 of settings.json.

## Options Considered

**Option A — Set `CLAUDE_CODE_SUBAGENT_MODEL` env var.** Pin both scouts
and synthesis at the env-var level; this overrides everything else.
Simple, no file changes. Rejected because the env var is a single global
value: it cannot pin scouts to Haiku and synthesis to Sonnet
simultaneously. It also defeats per-agent model assignment for every
other agent on the machine. Wrong tool for differential pinning.

**Option B — Drop the per-invocation `model` parameter and rely on
frontmatter.** This is the mechanism Phase 4 already uses for every
custom agent. For scouts, `Explore` is a built-in with no frontmatter we
control, so dropping the param falls through to the main conversation
model — Opus on the orchestrator thread. That defeats the entire point
of Haiku scouts (cost, speed). For synthesis, `general-purpose` is the
same built-in problem. Rejected for both: no frontmatter to fall through
to.

**Option C — Register custom subagents for scout and synthesis, then
drop the per-invocation `model` param.** Create `scout` and `synthesis`
personas under `source/{shared,claude,cursor}/agents/` with pinned
frontmatter (`claude-haiku-4-5-20251001` for scout, `claude-sonnet-4-6`
for synthesis). Update invocation templates and the brain-hydrate skill
to call `Agent(subagent_type: "scout")` and
`Agent(subagent_type: "synthesis")` with no `model` param. Resolution
falls to frontmatter, which we own and pin. Update both hook check sites
to recognize `scout` instead of `Explore`. Chosen.

## Decision

Register two custom subagents — `scout` and `synthesis` — with explicit
versioned-ID `model` pinning in frontmatter, then remove the
per-invocation `model` parameter from every scout and synthesis call
site. After this ADR, scout invocations are
`Agent(subagent_type: "scout")` and synthesis invocations are
`Agent(subagent_type: "synthesis")`. The Anthropic `Agent` tool's
resolution order falls to step 3 (frontmatter), which the project owns,
making scout and synthesis model assignments as durable as every other
custom agent.

`scout` inherits the `Explore` agent's read-only file-exploration
contract: tools are Read, Glob, Grep, Bash (read-only). `synthesis`
inherits the `general-purpose` filter/rank/trim contract: same read-only
toolset. Neither registers a Write/Edit tool. The format contract
enforcement in `enforce-scout-swarm.sh` (the `=== FILE: {path} ===`
delimiter requirement) and the sequencing exemption in
`.claude/settings.json` both update from `subagent_type == "Explore"` to
`subagent_type == "scout"`. The brain-hydrate skill's scout invocation
template and Phase 2b synthesis call switch to the new subagent types.

This ADR supersedes the scout/synthesis invocation specifications in
ADR-0027 and ADR-0042 (both immutable). Anywhere the prior ADRs read
`Agent(subagent_type: "Explore", model: "haiku")` or
`Agent(subagent_type: "general-purpose", model: "sonnet", effort: "low")`,
the v4.x pipeline now uses the registered `scout` and `synthesis`
subagent types from this ADR.

### Factual Claims

- `enforce-scout-swarm.sh:43` checks `SUBAGENT_TYPE = "Explore"` for the file-dump format contract.
- `enforce-scout-swarm.sh:63-66` whitelists `sarah` and `colby` for scout-evidence-block enforcement; scout/synthesis subagent types must not be added to that case.
- `.claude/settings.json:33` exempts `tool_input.subagent_type != 'Explore'` from `enforce-sequencing.sh`; the exemption must be updated to `!= 'scout'`.
- `source/shared/references/invocation-templates.md` references `Agent(subagent_type: "Explore", model: "haiku")` at lines 107 and 168, and `Agent(subagent_type: "general-purpose", model: "sonnet", effort: "low")` at line 117.
- `source/shared/references/pipeline-phases.md:139,152` references the `Explore` invocation pattern.
- `skills/brain-hydrate/SKILL.md:92,187,494` references both `Explore` scout and `sonnet` synthesis invocations with explicit aliases.
- `source/shared/rules/pipeline-models.md` lists Synthesis (Tier 2, sonnet/low) and Explore scouts (Tier 1, haiku/low) at lines 96 and 100; both rows reference the pre-rename names.
- `source/claude/agents/distillator.frontmatter.yml` is a working precedent for read-only frontmatter (sets `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit`); scout and synthesis frontmatter follow the same pattern.

### LOC Estimate

~120 lines changed across roughly 12 files (4 new persona/frontmatter files for `scout` and `synthesis`, 1 hook script, 1 settings.json, 3 reference/skill files, plus mirrored copies under `source/cursor/` and the installed `.claude/` tree).

## Rationale

Option C is the only path that makes scout and synthesis model
assignments structurally identical to every other agent. ADR-0047 chose
frontmatter pinning as the durable layer specifically because it
survives alias remaps, and the only way to extend that durability to
scouts and synthesis is to give them frontmatter we own. The cost is
two new persona files and a coordinated rename across two hook check
sites; the benefit is removing the last two silent failure modes from
the Phase 4 pinning effort.

Rollback sketch: if registering `scout` causes the format-contract hook
to misfire on real scout output, revert the rename in
`enforce-scout-swarm.sh` and `.claude/settings.json` only — the
frontmatter files themselves are inert without the call-site rename. If
the synthesis persona produces worse-quality filter/rank/trim output
than the inline-prompt approach, revert
`source/shared/references/invocation-templates.md` Template 2c to the
inline form and leave the persona file in place unused; resolution
falls back to whatever the call site specifies.

Risk: if Anthropic later registers `scout` or `synthesis` as built-in
subagent types with their own semantics, our custom registrations would
collide — Eva would invoke the built-in instead of our pinned
frontmatter, silently re-introducing the alias-drift hole this ADR
closes. Revisit if Anthropic publishes a built-in `scout` or
`synthesis` subagent type.

## Falsifiability

This decision is wrong if: (1) versioned model IDs in custom subagent
frontmatter stop being honored by the `Agent` tool (resolution step 3
breaks), forcing a fallback to env-var pinning; (2) the rename of
`Explore` → `scout` in the hook breaks the existing format-contract
enforcement in a way that allows malformed scout output through to the
brain-hydrate Sonnet extractor; or (3) registering a custom subagent
with read-only tools materially degrades the file-exploration behavior
that the built-in `Explore` provides (e.g., loss of native parallelism
or built-in tool ergonomics). Revisit if any of these surface.

## Sources

- ADR-0042 (deferred synthesis persona).
- ADR-0047 §Phase 4 (versioned-ID frontmatter pinning).
- `source/shared/rules/pipeline-models.md` §model-enforcement Rule 2 (explicit model + effort in every invocation).
- `source/claude/hooks/enforce-scout-swarm.sh:43,63` (Explore type checks).
- `.claude/settings.json:33` (Explore sequencing exemption).
- Empirical: `Agent(model: "claude-haiku-4-5-20251001")` returns InputValidationError; frontmatter `model: claude-haiku-4-5-20251001` is accepted.
