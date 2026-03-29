# Retro Lessons -- Shared Reference


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
The Stop hook duplicated quality checks already performed by pipeline agents
(Colby runs lint, Roz runs QA, Ellis verifies before commit). It also caused
infinite loops for subagents (stop -> blocked -> retry -> stop -> blocked).
The quality-gate Stop hook was removed entirely. Lint and complexity checks
are handled by the agents themselves during their normal workflow.
</root-cause>
<rules>
<rule agent="eva">Quality checks are handled by pipeline agents, not hooks. Colby runs lint during implementation, Roz runs the full test suite during QA, and Ellis verifies before commit.</rule>
<rule agent="colby">Run lint and typecheck as part of implementation workflow. Do not rely on external hooks to catch formatting or type errors.</rule>
<rule agent="roz">Full test verification is Roz's job. No Stop hook exists to pre-filter -- Roz is the single quality gate for test results.</rule>
</rules>
</lesson>

<lesson id="004" agents="colby, roz">
<what-happened>
Hung Process Retry Loop -- When a Bash command hangs (e.g., full test suite
OOM, vitest memory exhaustion), the subagent defaults to sleep-poll-kill-retry
with escalating durations. This burns tokens and time without diagnosing the
actual problem.
</what-happened>
<root-cause>
Subagents don't inherit the parent system prompt's anti-retry guidance. When a
command hangs or times out, the base model's default behavior is to retry the
same command with longer timeouts, sleep between attempts, and eventually try
to kill and restart -- none of which addresses the underlying cause.
</root-cause>
<rules>
<rule agent="colby">When a command hangs or times out, STOP. Diagnose the cause (check config, check memory with `ps aux`, run a single test file first, check for open handles). Never sleep-poll-kill-retry. If a command doesn't return within the Bash timeout, that is diagnostic information — not a reason to retry the same command.</rule>
<rule agent="roz">When a command hangs or times out, STOP. Diagnose the cause (check config, check memory with `ps aux`, run a single test file first, check for open handles). Never sleep-poll-kill-retry. If a command doesn't return within the Bash timeout, that is diagnostic information — not a reason to retry the same command.</rule>
</rules>
</lesson>

<lesson id="005" agents="cal, colby, roz, poirot">
<what-happened>
Frontend Wiring Omission -- Colby consistently produced strong backend code
(API endpoints, store methods, data access) but forgot to wire the frontend
consumer. The pattern recurred across multiple pipelines. Backend passed all
unit tests, Roz QA passed per-step, but the UI was never connected to the
real APIs.
</what-happened>
<root-cause>
Three structural causes: (1) Cal's ADR steps were layer-oriented (all APIs
first, then all UI), so by the time Colby reached UI steps the backend
context was lost across subagent boundaries. (2) Each Colby invocation is a
fresh context window with no memory of prior step's response shapes. (3) No
pipeline gate verified end-to-end wiring -- Roz QA'd each unit against its
ADR step but nobody traced user click -> API call -> response -> UI render.
</root-cause>
<rules>
<rule agent="cal">Design ADR steps as vertical slices. Every step that creates a data contract (endpoint, store method) must include the primary consumer in the same step. Orphan producers = incomplete plan. Include a Wiring Coverage section mapping every producer to its consumer.</rule>
<rule agent="colby">Document exact response/return shapes in a Contracts Produced table in your DoD. When consuming a prior step's contract, verify the actual shape matches what was documented. Shape mismatches are blockers -- do not silently adapt.</rule>
<rule agent="roz">Wiring verification is a Tier 2 blocker: grep for orphan endpoints (backend routes nothing calls) and phantom calls (frontend calling non-existent endpoints). Verify response shape alignment between producer and consumer.</rule>
<rule agent="poirot">Cross-layer wiring check: flag API endpoints in the diff that nothing calls, frontend calls to endpoints not in the diff (grep to verify), and type mismatches between backend response shapes and frontend expectations.</rule>
</rules>
</lesson>

</retro-lessons>
