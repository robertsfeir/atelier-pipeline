# ADR-0052: Declared `<contract>` Blocks on Pipeline Skill Files

## Status
Accepted.

## Context

Pipeline skills run on the main thread (Eva) via Claude Code's Skill mechanism.
Five of them — `pipeline-setup`, `pipeline-uninstall`, `brain-setup`,
`brain-uninstall`, and `brain-hydrate` — form a load-bearing dependency chain:
`pipeline-setup` must run before any brain skill, `brain-setup` must succeed
before `brain-hydrate` can capture anything, and both uninstall skills assume
their setup counterpart already ran. None of these preconditions are declared
anywhere in the skill files. The chain is discovered at runtime, usually as a
silent failure (`brain-hydrate` calls `atelier_stats`, hits "brain not
reachable," and aborts the user's hydration mid-conversation).

Subagent persona files already use a fixed XML schema (`xml-prompt-schema.md`):
`<output>` declares what the agent produces, and Eva reads it before invoking.
Skill files use `<procedure>`, `<gate>`, `<protocol>`, `<error-handling>`, and
`<section>` — no equivalent of `<output>`. Skills describe procedure but never
contract.

The triggering question: should the contract be declared only (Claude reads
`<requires>` at invocation time and self-checks), or is structural enforcement
(a hook or validator script) needed to make the contract load-bearing?

## Options Considered

**Option 1: Declare `<contract>` blocks, no enforcement layer.** Add a
`<contract>` tag to each of the five skill files, listing `<requires>`
(preconditions — file paths, env vars, prior-skill markers), `<produces>`
(what the skill writes), and `<invalidates>` (what becomes stale). Claude
reads the block at skill invocation and surface-checks the listed
preconditions before proceeding. No new hook, no new parser. Cost: one block
per skill, ~10–20 lines each. The failure mode this catches —
`brain-hydrate` running with no brain — is detected by the skill's existing
Step 1 (`atelier_stats` health check); the contract makes the precondition
explicit *before* that step rather than as a runtime side effect, which
shortens the failure message from "brain not reachable, do X, Y, Z" to "this
skill requires `.claude/brain-config.json` and `brain_enabled: true` — run
`/brain-setup` first."

**Option 2: Declared contracts plus a validator hook.** Add `<contract>`
blocks (as in Option 1) AND ship a `validate-skill-contract.sh` PreToolUse
hook that parses the block, reads each `<requires>` clause, and blocks the
skill if any precondition is missing. Cost: one new hook script, parsing
logic for the contract DSL, registration in `settings.json`, plus the
contract blocks themselves. Catches the same failure mode as Option 1, but
mechanically rather than behaviorally. Justified when behavioral instruction
is known to be ignored — the established pattern in this project for paths,
sequencing, and git operations. The case here is weaker: skills run on the
main thread (where Claude actually reads procedural instructions reliably,
unlike subagents under context pressure), the chain is five files, and the
preconditions reduce to "does file X exist" and "is env var Y set" — both of
which the skills already check in their first procedural step.

**Option 3: Do nothing — leave skills as-is.** Document the install order in
README and rely on the skills' existing health checks to fail loudly. Lowest
cost, but the specific failure mode (`brain-hydrate` against a non-existent
brain) already happens today and the failure message is procedural noise
rather than a clean precondition violation. Doing nothing concedes the
diagnostic clarity gain.

## Decision

Adopt **Option 1**: declare `<contract>` blocks on all five pipeline skill
files. Each block contains `<requires>` (preconditions for invocation),
`<produces>` (artifacts the skill writes), and `<invalidates>` (what becomes
stale). Add `<contract>` to `xml-prompt-schema.md` as a top-level tag valid
in skill files only — agent and command files keep their existing `<output>`
semantics.

No validator hook is added. Claude reads `<contract>` on the main thread at
skill invocation, the same way it reads the procedure block today. The
skills' existing health checks (`atelier_stats`, `pg_isready`, file
existence) remain the runtime fail-loud layer.

If a contract clause is regularly ignored at runtime — i.e., a skill runs
through to a procedural step and fails on a precondition the contract
already declared — that is the falsifiability signal for revisiting Option
2.

### LOC Estimate

~80 lines added across 6 files (5 skill files + 1 schema entry). No code
changes. No new hooks.

## Rationale

The mechanical-enforcement default in this project exists because behavioral
instructions to subagents under context pressure get ignored. Skill files
are not under that pressure — they run on the main thread, are read in full
on every invocation, and Claude follows their procedural steps reliably (the
existing `<gate>` tags in the same files are honored without a hook). Adding
a parser/validator for five files where the failure mode already
self-reports through a health check is over-investment.

The contract block buys two things the procedure block does not: (1) a
single declarative location for "what must be true before this skill starts"
that agents and skills consuming a skill's output can reference, and (2) an
explicit `<invalidates>` clause — `brain-uninstall` invalidates the brain
config that `brain-hydrate` depends on, which is currently undocumented. The
declared contract makes that dependency reviewable.

Risk shape: the failure this misses is a contract that drifts from procedure
— someone updates the procedure to require a new env var without updating
`<requires>`. That drift is caught at the next skill run when the
procedural step fails, which is the same surface the skills produce today.
The drift window is bounded and self-healing.

Out of scope: extending `<contract>` to subagent or command files
(subagents already declare `<output>`; commands inherit Eva's main-thread
context). If a future skill is added that shells out to a subagent for a
load-bearing precondition, that's an Option 2 conversation, not this one.

## Falsifiability

Revisit and adopt Option 2 (validator hook) if any of these occur:

- A skill is invoked twice in a calendar quarter and proceeds past its
  `<requires>` clause when a precondition is unmet — i.e., Claude reads the
  block and ignores it.
- A pipeline-internal Poirot finding traces a user-visible failure to a
  contract clause that drifted from procedure for more than one release.
- A new skill is added whose preconditions cannot be expressed as
  file-existence or env-var checks (e.g., requires a network probe with
  retry semantics).

If none of these trigger within two quarters of adoption, the declared-only
contract is sufficient and the validator-hook investment is correctly avoided.

## Sources

- `source/shared/references/xml-prompt-schema.md` — current tag vocabulary,
  Plugin Skill Tags section.
- `skills/brain-hydrate/SKILL.md` Step 1 — existing runtime precondition
  check (`atelier_stats`, `brain_enabled`).
- `skills/brain-setup/SKILL.md` path-detection protocol — existing
  precondition check (`.claude/brain-config.json` presence).
- ADR-0033 (hook enforcement audit) — establishes the mechanical-enforcement
  bar for subagent-class failures, which skill-class failures do not meet.
