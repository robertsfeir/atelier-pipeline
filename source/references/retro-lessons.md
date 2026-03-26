# Retro Lessons -- Shared Reference

<!-- CONFIGURE: No placeholders to update. This file is populated as your project runs pipelines. -->

Lessons learned from past pipeline runs. Referenced by Cal, Colby, and Roz
at the start of every work unit. Eva checks `error-patterns.md` for
recurrence and injects WARN entries into agent invocations when a pattern
repeats 3+ times.

## How to Use This File

- **After each pipeline:** Eva identifies systemic issues from Roz's QA
  findings. If an issue reveals a reusable lesson (not just a one-off bug),
  add it here AND capture it in the brain (if available) via `agent_capture`
  with `thought_type: 'lesson'`, `source_agent: 'eva'`, `source_phase: 'retro'`.
- **Format:** Each lesson entry has `id` and `agents` attributes, and
  contains what-happened, root-cause, and rules sections. Each rule
  targets a specific agent.
- **Agents search the brain first** (if available) for retro lessons relevant
  to the current feature area, then also read this file as a fallback. If a
  lesson is relevant, they note it in their DoR's "Retro risks" field.
- **This file is the canonical fallback** -- the pipeline works without a brain.
  The brain adds searchability so agents get relevant lessons instead of the
  full list.
- **Eva injects WARN** into agent invocations when error-patterns.md shows
  a pattern recurring 3+ times. The WARN references the specific lesson here.

<retro-lessons>

<lesson id="001" agents="cal, colby, roz">
<what-happened>
Sensitive Data in Return Shapes -- A data access function returned sensitive
fields (e.g., password hashes, API keys) to all callers because the ADR
specified method signatures but not return shapes. The implementer included
the fields everywhere because the ADR didn't say not to. QA caught it
during review.
</what-happened>
<root-cause>
Architecture gap, not implementation bug. When a data access layer serves
both privileged callers (need sensitive fields) and public callers (who
should not have sensitive fields), the ADR needs to specify two
normalization paths.
</root-cause>
<rules>
<rule agent="cal">Every data access method in the Data Sensitivity table should specify what it returns and what it excludes. Tag methods `public-safe` or `auth-only`.</rule>
<rule agent="colby">Before handoff, ask: "Who calls this function? Do ALL callers need ALL fields?" Default normalization should exclude sensitive fields. Create a separate privileged accessor for the one caller that needs it.</rule>
<rule agent="roz">In security review, check for data access methods returning sensitive fields to callers that don't need them. Scope to current diff -- flag pre-existing issues separately.</rule>
</rules>
</lesson>

<lesson id="002" agents="colby, roz">
<what-happened>
Self-Reporting Bug Codification -- The implementer found issues in shared
utility functions during testing. Instead of flagging them as bugs, she
adjusted test expectations to match the buggy behavior and labeled them
"behavioral quirks." Two were real bugs. When one bug was fixed in one
file, it existed in multiple other unfixed copies across the codebase.
</what-happened>
<root-cause>
Structural conflict of interest -- when the same agent writes both tests
and code, they control what "correct" means. Combined with completion bias,
the path of least resistance is adjusting expectations to match bugs rather
than fixing them.
</root-cause>
<rules>
<rule agent="colby">Do not modify Roz-authored test assertions. If they fail against existing code, the code has a bug -- fix it. When fixing a bug in a shared utility, grep the entire codebase for all instances and fix all copies.</rule>
<rule agent="roz">Assert what code SHOULD do (domain intent), not what it currently does. A test that codifies a bug is worse than no test. Roz writes test assertions BEFORE Colby builds -- tests define correct behavior.</rule>
</rules>
</lesson>

<lesson id="003" agents="eva, colby, roz">
<what-happened>
Stop Hook Race Condition -- The quality-gate Stop hook ran the full test
suite (including DB-dependent integration tests) on every conversation stop.
When test containers were down (after cleanup or between sessions), the hook
failed repeatedly, blocking all agent work. The hook fired dozens of times
per session (on every subagent completion), making the full test suite
prohibitively slow and fragile as a gate.
</what-happened>
<root-cause>
Single `test_command` field used for both the Stop hook (fires frequently,
needs to be fast) and Roz QA (fires once per unit, can be thorough). The
Stop hook needs checks that complete in seconds with no external
dependencies. The full test suite belongs in QA, not in a hook that fires
on every stop.
</root-cause>
<rules>
<rule agent="eva">Always configure `lint_command` (fast, no DB) separately from `test_command` (full suite). The Stop hook uses `lint_command`. Roz uses `test_command`.</rule>
<rule agent="colby">Do not put DB-dependent or slow commands in `lint_command`. Lint, typecheck, format checks only. If it needs a running service, it belongs in `test_command`.</rule>
<rule agent="roz">The Stop hook is not a substitute for QA. It catches formatting and type errors early. Full test verification is Roz's job, not the hook's job.</rule>
</rules>
</lesson>

</retro-lessons>
