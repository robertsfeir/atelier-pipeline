# Pipeline Phases Reference

JIT-loaded sections extracted from `pipeline-orchestration.md`. Eva loads this
file on demand per the triggers in that file's Loading Strategy table:

| Trigger | Protocol / Section |
|---------|--------------------|
| First state write | State File Descriptions |
| Pipeline sizing decision | Phase Sizing Rules |
| Pipeline sizing decision | Budget Estimate Gate |
| Session boot with concurrent stale state | Concurrent Session Detection |
| Debug flow entered | Investigation Discipline |

All anchor IDs below (`<section id="...">`, `<gate id="...">`,
`<protocol id="...">`) are preserved from the original orchestration file --
downstream references still resolve by ID.

<protocol id="investigation">

## Investigation Discipline

When Eva enters a debug flow, she creates (or resets)
`{pipeline_state_dir}/investigation-ledger.md` with the symptom and an empty
hypothesis table. Eva updates it after each investigation step.

### Layer Escalation Protocol

Every investigation considers four system layers:
1. **Application** -- state, components, routes, handlers, data access
2. **Transport** -- HTTP headers, auth tokens, SSE/WebSocket, CORS, proxy
3. **Infrastructure** -- containers, networking, DNS, TLS, load balancing
4. **Environment** -- env vars, config files, secrets, feature flags

**Threshold rule:** 2 rejected hypotheses at the same layer -> Eva MUST
investigate the next layer before proposing more hypotheses at the
original layer.

### Hypothesis Tracking

Before proposing a fix, Eva records each hypothesis in the investigation
ledger with: the hypothesis, which layer it targets, what evidence was
found, and whether it was confirmed or rejected. Eva re-reads the ledger
before forming new hypotheses to avoid repetition.

</protocol>

<protocol id="concurrent-session-hard-pause">

## Concurrent Session Detection

At session boot, if `stale_context: true` AND the stale state's phase is not
`idle` or `complete`, Eva HARD PAUSES and presents three options:

1. **Adopt existing state** -- resume the other session's pipeline.
   Eva reads the existing pipeline-state.md and continues from the recorded
   phase.
2. **Archive and start fresh** -- move the existing state aside.
   Eva executes: `mv "$STATE_DIR" "$STATE_DIR.archive-$(date +%s)"` via Bash
   (diagnostic command, not Write/Edit) and begins a clean pipeline in the
   newly-created empty state directory.
3. **Cancel this session** -- stop without modifying state.
   Eva writes `stop_reason: user_cancelled` and transitions to idle.

Eva records the user's choice in context-brief.md under "User Decisions"
so downstream brain hydration captures it.

This protocol fires only when stale state has an active pipeline phase.
If `stale_context: true` but the phase is `idle` or `complete`, Eva
announces the stale state and proceeds normally (the stale state is a
finished pipeline from a prior session, not a concurrent one).

</protocol>

<section id="state-files">

## State File Descriptions

Eva updates `pipeline-state.md` after each wave completes, not after each
unit. Within a wave, Eva tracks unit progress in-memory.

Eva maintains five files in `{pipeline_state_dir}`:
- **`pipeline-state.md`** -- Wave-level progress tracker with "Changes since last state" section.
- **`context-brief.md`** -- Conversational decisions, corrections, user preferences. Reset per feature.
- **`error-patterns.md`** -- Post-pipeline error log categorized by type.
- **`investigation-ledger.md`** -- Hypothesis tracking during debug flows.
- **`last-qa-report.md`** -- Poirot's most recent QA report. Eva reads verdict only.

</section>

<section id="phase-sizing">

## Phase Sizing Rules

**Robert-subagent on Small:** When Poirot flags doc impact, Eva checks for an
existing spec: `ls {product_specs_dir}/*<feature>*`. Spec exists -> run Robert.
No spec -> skip, log gap.

User overrides: "full ceremony" forces Small minimum. "stop"/"hold" halts auto-advance.

### Sizing Choice Presentation

Eva always presents sizing as a choice list with her recommendation in bold.
All four options are shown. The user picks.

Format:
```
This feature sizes as [assessment]. Pick your pipeline sizing:

- Micro
- Small
- **[Recommended]** (recommended)
- Large
```

If the user picks a different sizing, Eva re-sizes immediately. All subsequent
invocations use the chosen sizing's model assignments and ceremony level.
The user can say "upgrade to Large" or "downgrade to Small" at any point.

### Micro Classification Criteria

ALL five must be true: (1) <=2 files, (2) purely mechanical, (3) no behavioral
change, (4) no test changes needed, (5) user says "quick fix"/"typo"/equivalent.

Safety valve: Eva runs full suite after Micro. ANY test fail -> re-size to Small,
log `mis-sized-micro`. No brain on Micro.

**Key rules:** Colby NEVER modifies Poirot's assertions. Poirot does final sweep after
all units. Batch sequential by default. Worktree changes merge via git, not copying.

### Robert Discovery Mode Detection

Mechanical: (1) existing spec? (2) existing components? (3) brain 3+ thoughts?
Any -> assumptions mode. None -> question mode (default).

### Scout Fan-out Protocol

Eva fans out scout agents in parallel before invoking Sarah or Colby. Scouts collect raw evidence cheaply. The main agent receives it as a named inline block and skips the collection phase entirely.

**Invocation:** `Agent(subagent_type: "scout")`. Facts only — no design opinions. Dedup rule: each file read by at most one scout. The `model` parameter is omitted; resolution falls through to the scout frontmatter (`claude-haiku-4-5-20251001`) per ADR-0048.

**Explicit spawn requirement.** Eva MUST spawn scouts as separate parallel subagent invocations and MUST spawn the synthesis agent as a separate parallel subagent invocation after scouts return for Sarah or Colby. In-thread scout collection or synthesis silently bypasses the fan-out -- the scout-swarm hook inspects the primary-agent prompt only, not Eva's reasoning -- and is a violation (default class).

#### Per-Agent Configuration

| Agent | Block | Scouts | Skip condition |
|-------|-------|--------|----------------|
| **Sarah** | `<research-brief>` | Patterns (grep existing patterns, file:line), Manifest (dependency versions), Blast-radius (≤15 files in scope), Brain (`agent_search` query derived from feature area) | Small pipelines |

| **Colby** | `<colby-context>` | Existing-code (files the ADR step will modify), Patterns (grep for similar constructs, file:line only), Brain (`agent_search` query derived from ADR step description) | Micro pipelines; Re-invocation fix cycle |
| **brain-hydrate** | `<hydration-content>` | ADR scout (reads `docs/architecture/ADR-*.md` or `docs/adrs/ADR-*.md`), Spec scout (reads `docs/product/*.md`), UX scout (reads `docs/ux/*.md`), Pipeline scout (reads error-patterns + retro-lessons + context-brief), Git scout (runs `git log`, filters significant commits) | Per-source type skip when user excludes that source type from scope or scan finds 0 files for that category |

All scouts are `Agent(subagent_type: "scout")`. The scout subagent inherits project MCP servers — the Brain scout calls `agent_search` directly, no custom agent needed. Eva collects all scout results and populates the named block before invoking the agent. Per ADR-0048, scout model pinning is owned by the scout frontmatter (`claude-haiku-4-5-20251001`); the `model` parameter is omitted from invocations.

**Synthesis step (Medium+ pipelines, applies to Sarah, Colby, and Poirot):** After scouts return for a primary agent (Sarah / Colby / Poirot), Eva invokes a single synthesis agent per Template 2c (scout-synthesis) before invoking the primary agent. Synthesis filters/ranks/trims scout output into the compact named block (`<research-brief>` for Sarah, `<colby-context>` for Colby, `<qa-evidence>` for Poirot) — synthesis replaces the raw scout dump in the block. Synthesis is invoked as `Agent(subagent_type: "synthesis", effort: "low")`; the model parameter is omitted and resolution falls through to the synthesis frontmatter (`claude-sonnet-4-6`) per ADR-0048. Skip conditions mirror the scout skip table (Sarah: Small/Micro; Colby: Micro + re-invocation fix cycle; Poirot: scoped re-run). The brain-hydrate flow is a batch hydration pipeline, not a primary-agent invocation — it does not use the synthesis step.

**Note:** Brain scout only fires when `brain_available: true`. When brain is unavailable, the Brain scout row is skipped and the `<brain>` element is omitted from the context block.

**Investigation Mode (user-reported bugs):** Sherlock handles user-reported bug investigation without scout fan-out. See default-persona.md `<protocol id="user-bug-flow">`.

| Scout | What it does |
|-------|-------------|
| **Files** | Reads files mentioned in the stack trace/error message + `git diff HEAD~5 --name-only` recent changes; deduplicates with stack trace files |
| **Tests** | Runs the failing test(s) from the bug report; captures output with `2>&1 \| head -100` |
| **Brain** | `agent_search` query derived from symptom/error message text (skipped when `brain_available: false`) |
| **Error grep** | Greps for the error string / exception type across the codebase; file:line output only, `\| head -30` |

</section>

<gate id="budget-estimate">

## Budget Estimate Gate [JIT -- Pipeline sizing decision]

Fires after user picks sizing, before first agent invocation. Formula and cost tables in `telemetry-metrics.md` "Budget Estimate Heuristic". Config: `token_budget_warning_threshold` in `pipeline-config.json` (`number | null`, default `null`).

| Sizing | threshold absent/null | threshold configured |
|--------|----------------------|---------------------|
| Micro/Small | No gate | No gate |
| Medium | No gate | Estimate shown; hard pause only if EXCEEDS threshold |
| Large | Estimate + hard pause (always) | Estimate + hard pause + threshold comparison |

Hard pause = Eva waits for explicit user response. Large always hard-pauses regardless of threshold. Label "order-of-magnitude -- not billing" required on every presentation.

**Large format:**
```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Large | Steps: [N or "TBD -- estimated after Sarah"] | Agents: [roster count]
  Estimated cost: $X.XX -- $Y.YY
  [Threshold: $Z.ZZ -- estimate EXCEEDS threshold / within threshold]
Proceed? (yes / cancel / downsize to Medium)
```
**Medium format (threshold configured):**
```
Pipeline estimate (order-of-magnitude -- not billing):
  Sizing: Medium | Steps: [N or "TBD"] | Agents: [roster count]
  Estimated cost: $X.XX -- $Y.YY | Threshold: $Z.ZZ -- [within / EXCEEDS]
Proceed? (yes / cancel)
```
"Downsize to Medium" appears only in Large prompt.

**On cancel:** Write `stop_reason: budget_threshold_reached` (or `user_cancelled` if ADR-0028 not yet implemented). Announce: "Pipeline cancelled. Stop reason: budget threshold. Consider: (a) downsize to Medium/Small, (b) break into smaller increments, (c) adjust threshold." Transition to idle.

**Brain integration:** Record estimate in memory; include in T3 metadata: `budget_estimate_low`, `budget_estimate_high`. With 5+ prior T3 captures: announce historical accuracy at boot (informational, formula not auto-tuned). Absent threshold -> no gate for Micro/Small/Medium; Large still hard-pauses.

</gate>
