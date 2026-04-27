# Case File: brain-hydrate scout fan-out returns prose instead of `=== FILE: ===` delimited content

## Verdict

The scout output contract is documented as a *passive description of what
scouts return*, not as an *instruction given to the scout*. The root cause
lives in `skills/brain-hydrate/SKILL.md` at lines 92 and 106-118: the skill
tells Eva the scout "returns raw file content with clear delimiters per file"
and renders a worked example of the `=== FILE: path === ... === END FILE ===`
format — but the skill never supplies a scout-side invocation template, never
enumerates the delimiter format inside the prompt Eva must send to the
Explore subagent, and never specifies that Eva must include a `<read>` file
list plus a `<output>` format contract in the scout prompt. As a result,
Eva improvises the scout prompt on every call. The `Explore` subagent is
Anthropic's built-in research subagent with no project-local persona on
disk (`.claude/agents/` has no `explore.md`; global search finds none), so
its default behavior is to produce narrative research summaries, not raw
file dumps with specific delimiters. When Eva's improvised prompt
happens to be concrete ("read these 3 files and emit them between
`=== FILE: ===` markers"), the scout conforms; when Eva's improvised
prompt is loose ("read docs/product/*.md and return their content"), the
Explore scout falls back to its default summarizing behavior and returns
prose — no delimiters, nothing for the downstream Sonnet extraction
subagent's parser to lock onto. The completeness check at
`skills/brain-hydrate/SKILL.md:142-145` catches the file-count mismatch
after the fact but does not explain why; the explanation is that there
was never a format contract inside the scout's own context window, only
in Eva's.

## Evidence

1. **The delimiter format is documented only for Eva, not for the scout.**
   `skills/brain-hydrate/SKILL.md:108-118` shows the `=== FILE: ... ===`
   format under the heading "Scout Content Format" inside the skill body
   that Eva reads. The scout runs as `Agent(subagent_type: "Explore",
   model: "haiku")` — a fresh context with no session inheritance — and
   the skill does not instruct Eva to copy this format block into the
   scout's prompt. Grep confirms: `grep "=== FILE"` across
   `skills/`, `source/`, `.claude/` returns exactly two hits, both at
   `skills/brain-hydrate/SKILL.md:111` and `:115`, both inside the
   illustrative example block aimed at Eva.

2. **SKILL.md contains no `<task>/<output>/<constraints>/<read>` block
   for the scout.** `grep -n "<task>\|<output>\|<constraints>\|<read>"
   skills/brain-hydrate/SKILL.md` returns four hits — all on lines
   163-188, all inside Phase 2b (the Sonnet extraction subagent
   invocation). The Phase 2a scout fan-out section (lines 86-146) has
   zero prompt-template blocks. Every other agent in the pipeline has
   an invocation template under `source/shared/references/invocation-templates.md`
   (see Robert line 224, Colby line 176, Sarah section line 83). The
   brain-hydrate scouts do not. `grep "hydration-content\|hydrate-scout\|brain-hydrate"
   source/shared/references/invocation-templates.md` returns zero hits.

3. **No project-local or global `Explore` persona with the format
   contract baked in.** `ls .claude/agents/` returns 13 personas; none
   is `explore.md`. `find . ~/.claude/plugins -name "explore*"`
   returns nothing. The Explore subagent's behavior is therefore
   whatever Anthropic's built-in research subagent defaults to, which
   is a summarizing researcher — not a file-dumping courier. Without
   a format contract in the prompt, the scout has no reason to emit
   the delimiters.

4. **The failure record matches.** `docs/pipeline/error-patterns.md`
   logs three `StopFailure: Explore` entries at
   2026-04-05T16:23:30-31Z (lines 79-92), clustered within one second —
   a parallel fan-out's worth of scouts all failing or returning
   non-conforming output at the same moment. The `log-stop-failure.sh`
   hook at `.claude/hooks/log-stop-failure.sh:75` writes
   `AGENT_TYPE` from the `agent_type` JSON field, confirming these
   are in fact Explore subagents (not the generic "unknown" default
   at line 50 of the hook).

5. **Intermittency is explained by prompt improvisation.** Because the
   scout prompt is not templated, each fan-out Eva constructs can be
   different. Runs where Eva happens to include a verbatim format
   example in the prompt succeed; runs where Eva uses a generic
   "read and return" phrasing fail. This matches Q6's report that
   "some scouts in the same fan-out succeed while others don't" —
   each scout gets a slightly different prompt (one per category),
   so the scouts that happen to receive explicit delimiter
   instructions conform while the others drift to Explore's default
   prose output.

## Path walked

- `skills/brain-hydrate/SKILL.md:86-146` — scout fan-out protocol, the
  claimed contract site. Contract described passively; no prompt block.
- `skills/brain-hydrate/SKILL.md:108-118` — delimiter format rendered in
  the skill body (read by Eva, not by scout).
- `skills/brain-hydrate/SKILL.md:142-145` — completeness check gate,
  explains the *detection* mechanism but not the cause.
- `skills/brain-hydrate/SKILL.md:160-190` — Phase 2b Sonnet extraction
  subagent invocation with a full `<task>/<hydration-content>/<read>/<constraints>/<output>`
  block. The producer is templated; the scout that feeds it is not.
- `source/shared/references/invocation-templates.md:82-102` — pipeline
  scout template (`scout-research-brief`). This exists for the
  Sarah/Colby pre-build fan-out but is purpose-built for that flow
  and has no `=== FILE: ===` format requirement. Brain-hydrate
  scouts have no equivalent template.
- `docs/architecture/ADR-0027-brain-hydrate-scout-fanout.md:82-97,306-315`
  — the ADR that defined the scout-fanout design. Line 310 documents
  the contract boundary ("Scout (Explore+haiku) produces raw file
  content with `=== FILE: path ===` / `=== END FILE ===` delimiters")
  but the Implementation Plan (lines 181-218) only specifies
  modifications to SKILL.md and pipeline-orchestration.md — never a
  scout-side invocation template. The wiring was documented but
  never implemented as an executable prompt contract.
- `.claude/hooks/enforce-scout-swarm.sh:40-43` — the scout-swarm hook
  enforces `<research-brief>` / `<colby-context>` on sarah/colby
  invocations only. It does not enforce on Explore subagent
  invocations. Nothing mechanically forces Eva to include a format
  contract in a scout prompt.
- `docs/pipeline/error-patterns.md:79-92` — three clustered
  `StopFailure: Explore` entries at 2026-04-05T16:23:30-31Z, matching
  the symptom.

## Ruled out

- **Not an Explore subagent bug.** The Explore subagent runs with
  default Anthropic behavior; asking it for prose gets prose, asking
  it for delimited output gets delimited output. Its behavior is
  consistent with a scout that was never told what format to emit.
- **Not a file-reading failure.** The scouts return successfully, no
  stack traces, no tool errors — they return *content*, just the
  wrong shape. The `StopFailure: Explore` entries at
  `error-patterns.md:79-92` log `Error: unknown` and `Message: unknown`
  (from `log-stop-failure.sh:50-52` defaulting empty JSON fields to
  "unknown"), meaning the subagent turn ended without a structured
  API error — consistent with "returned clean but with non-conforming
  output," not with "crashed while reading files."
- **Not the completeness check gate.** The gate at
  `skills/brain-hydrate/SKILL.md:142-145` fires after the scout
  returns. The scout has already emitted prose by that point. The
  gate is a detector, not a cause.
- **Not a dedup-rule violation or file-count-gate miss.** The
  dedup rule (line 94) and >20-file split (lines 128-132) determine
  *which* files each scout gets, not *how* the scout formats its
  output. The bug would persist with a single file in a single
  scout.
- **Not a splitting-logic bug.** Even a single ADR scout with 3
  files reproduces the symptom when Eva's improvised prompt is
  underspecified.
- **Not a model-selection bug.** `pipeline-models.md` correctly
  assigns haiku to Explore scouts (line 91 of the Per-Agent table).
  Haiku is sufficient to emit the delimiter format *if instructed
  to do so*. The model isn't the problem; the prompt is.
- **Not a scout-swarm hook gap.** `enforce-scout-swarm.sh` enforces
  only on sarah/colby (lines 40-43); brain-hydrate's Sonnet
  extraction subagent has no `<hydration-content>` enforcement
  either. This means there's no mechanical safety net, but the
  hook gap is a missing mitigation, not the root cause. The root
  cause is the missing scout-side prompt contract.

## Reproduction confirmed

Partial. I did not invoke a live Explore scout with the improvised
prompt and observe the drift directly — invoking a fresh
`Agent(subagent_type: "Explore", model: "haiku")` from within this
Sherlock session would create a nested subagent with no inheritance
and would not faithfully reproduce Eva's improvised prompt. What I
confirmed instead: (a) the `=== FILE: ===` format appears only in
SKILL.md's illustrative block (grep hits only at lines 111 and 115
of the skill), (b) no scout-side invocation template exists anywhere
in the repo (zero hits for brain-hydrate scout prompts in
invocation-templates.md), (c) the `StopFailure: Explore` entries at
`docs/pipeline/error-patterns.md:79-92` match the reported failure
cluster, (d) no `Explore` persona file exists to carry the format
contract. The three independent observations converge on the
structural gap. A live repro would confirm the mechanism but is not
needed to pin the verdict — the contract is demonstrably absent
from the scout's context window.

## Recommended fix (prose, not a patch)

Add a scout-side invocation template to `skills/brain-hydrate/SKILL.md`
inside the Phase 2a scout-fanout protocol (between the existing
lines 106 and 120), following the same `<task>/<read>/<constraints>/<output>`
shape used for the Sonnet extraction subagent at lines 160-191. The
template should specify verbatim: the exact list of files the scout
must read (passed in by Eva from Phase 1 inventory), a `<constraints>`
block that forbids summarization and prose, and an `<output>` block
that reproduces the `=== FILE: {path} ===` / `=== END FILE ===`
delimiter format verbatim with an explicit note that every file
listed in `<read>` must appear once between these delimiters. Mirror
this into `source/shared/references/invocation-templates.md` as a new
`brain-hydrate-scout` template so the pattern is discoverable from
the canonical template index. Separately, extend
`.claude/hooks/enforce-scout-swarm.sh` with a second enforcement
clause that fires on `Agent` calls with `subagent_type == "Explore"`
when the parent context is brain-hydrate, requiring the `<output>`
block in the scout prompt to contain the `=== FILE:` literal — this
closes the mechanical loop (per `feedback_mechanical_enforcement.md`:
behavioral constraints are ignored, hook enforcement is required).
The completeness check at lines 142-145 stays as a belt-and-suspenders
detector.

## Unknowns

- **Whether the Explore subagent has documented default output
  behavior.** I could not inspect Anthropic's built-in Explore
  subagent persona (no project-local override exists; no public
  persona file is on disk). The claim that Explore defaults to
  prose summaries is inferred from: (a) the symptom description
  ("prose/narrative text with no delimiters"), (b) Explore's role
  per `source/shared/references/pipeline-phases.md:137-152` as a
  research/evidence-collection subagent, and (c) the absence of any
  file-dump format convention in its default behavior. If Explore
  does have a documented default that includes file delimiters, then
  the verdict narrows to "Eva's improvised prompt overrides
  Explore's default with looser instructions" — the fix is the same
  (template the prompt) but the attribution shifts.
- **Whether any prior fan-out succeeded purely by luck of prompt
  wording, or whether there's a code path I missed.** I grepped
  every skill, agent, reference, and hook file and found no
  scout-prompt template. If a template exists outside the
  repository (e.g., in a plugin cache or global Claude Code
  configuration), it would contradict the verdict. The absence of
  any project-local match is strong evidence but not conclusive
  for external injection.
- **The exact timestamps of user-reported recent failures.** The
  case brief cites the 2026-04-05T16:23:30Z `StopFailure: Explore`
  entry but the user describes the failure as intermittent and
  ongoing. I cannot confirm from `error-patterns.md` alone whether
  the 2026-04-05 cluster is the most recent instance or one of many.

## Correction to brief (if any)

The case brief describes the symptom as "the scout Agent call returns
successfully (no error, no exception) but their output contains no
parseable file content," and separately notes three clustered
`StopFailure: Explore` entries at 2026-04-05T16:23:30-31Z. These are
two different failure modes that likely share the same root cause:

- **Mode A: return clean, wrong shape.** The scout emits prose. No
  stop failure is logged. The Sonnet extraction subagent parses
  zero `=== FILE: ===` blocks and silently skips. This is the
  "silent" symptom the brief foregrounds.
- **Mode B: return with a StopFailure.** The three log entries at
  `error-patterns.md:79-92` show the turn ending in a stop failure
  with `Error: unknown` and `Message: unknown`. This is not
  "return successfully" — it's a distinct failure path. Both modes
  trace back to the same cause (no format contract in the scout's
  prompt), but mode B also involves the turn terminating in an
  unstructured error state, possibly because the scout attempted
  to emit structured output without a contract and exceeded turn
  limits or hit an internal error. The brief should not treat the
  StopFailure entries as synonymous with the "clean-but-wrong"
  symptom — they are two visible surfaces of one underlying
  structural gap.

Also, Q6 identifies the "completeness check" as a detection layer and
says "the root cause of why the scout returns non-conforming output
has not been determined." The brief's framing is accurate. The
verdict confirms it: the completeness check detects, it does not
explain. The explanation is the missing prompt-side contract.
