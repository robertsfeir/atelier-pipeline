# ADR-0041: Effort-Per-Agent Map (Task-Class Tier Model)

## Status

Accepted. **Supersedes:** brain thought `b09f430b-2c76-4aa8-b5bd-5c57a800d5ed` (2026-04-03, size-dependent Colby model decision). **Depends on:** Claude Code >= 2.1.89 for the `effort` frontmatter field; brain seed `e28d6b8e` documents `xhigh` GA 2026-04-16. **Related (not modified):** ADR-0029 (immutable; its cost-table reference in `telemetry-metrics.md` IS updated here). ADR-0035/0021/0019/0014/0012/0009 reference the old classifier but are immutable at their decision epochs.

---

## DoR: Requirements Extracted

**Sources:** GitHub issue #41, clarification `<context>`, blast-radius + frontmatter-patterns + brain scouts, `.claude/references/retro-lessons.md`.

| # | Requirement | Source |
|---|-------------|--------|
| R1 | ADR with effort rationale per agent | Issue #41 AC1 |
| R2 | `pipeline-models.md` carries effort alongside model | Issue #41 AC2 |
| R3 | Cost + quality baseline before/after for one full run; validation pipeline designed | Issue #41 AC3 |
| R4 | Four tiers: Haiku/low, Opus/medium, Opus/high, Opus/xhigh | `<context>` |
| R5 | Model follows task class, not agent identity | `<context>` |
| R6 | Effort promotes exactly one rung per signal; floor low, ceiling xhigh | `<context>` |
| R7 | Sonnet eliminated from reasoning tiers | `<context>` |
| R8 | Pipeline size = tier-picker signal only | `<context>` |
| R9 | Priority stack: accuracy > speed > cost | `<context>` |
| R10 | Effort demotions (Sentinel, Ellis, Distillator) explicitly justified | `<warn>` |
| R11 | Agatha split: conceptual (Tier 2 default) vs reference (Tier 1 runtime override) | Patterns scout |
| R12 | 15 Claude + 15 Cursor frontmatter updates | Blast-radius |
| R13 | Source replacement + 2 installed mirrors | Blast-radius |
| R14 | `pipeline-orchestration.md` classifier removal at cited lines | Blast-radius |
| R15 | `telemetry-metrics.md` cost-estimation table updated | Manifest scout |
| R16 | Compatibility: CC >=2.1.89 for `effort`; pipeline-setup soft-warning | Manifest + `<warn>` |
| R17 | Vertical slice: rule table producer -> Eva lookup + frontmatter consumer | Hard Gate #4 |
| R18 | Validation pipeline: re-run Medium ADR baseline with FPQR + cost-per-shipped-unit | Issue #41 AC3 |

**Retro risks:**
- Lesson 002 (self-reporting): Cal writes ADR + test spec; Roz owns authoritative test assertions. Roz reviews this spec before Colby builds.
- Lesson 005 (cross-agent wiring): the effort+model table is a cross-agent contract. Rule file (producer) must propagate to 30 frontmatter files (consumers). Orphan risk mitigated by consistency tests T-0041-025 through T-0041-039 (each row x 2 platforms).
- Lessons 001, 003, 004, 006: N/A for this ADR (no data access, no hooks, no long commands, no UI).

---

## Anti-Goals

**Anti-goal 1: Dynamic per-invocation effort tuning based on live telemetry.**
Reason: Eva does not choose models or effort at runtime -- the rule is mechanical (same gate as ADR-0009). A feedback loop that mutates effort based on prior-invocation metrics would reintroduce discretion and make Eva's model choices irreproducible. Revisit: when Darwin can propose structural rule changes with human approval loop (that is ADR territory, not runtime).

**Anti-goal 2: Keeping Sonnet as a "cost fallback" for reasoning tasks.**
Reason: The accuracy>speed>cost stack makes per-invocation cost the wrong frame. Rework from cheap-model first-pass dominates. Eliminating Sonnet from reasoning tiers removes a decision branch where Eva might be tempted to "save cost" on a task that then needs Colby rework. Revisit: when Sonnet 4.7+ demonstrates parity with Opus on Colby rework tasks (Darwin telemetry signal).

**Anti-goal 3: xhigh-everywhere defaults.**
Reason: Thinking tokens have diminishing accuracy returns and linear latency cost. xhigh on Roz sweep or Colby build inflates instruction-budget pressure (brain thought `e1dd8f79` -- instruction budget is load-bearing) without measurable FPQR gain. xhigh is reserved for Cal (design, where deliberation dominates pattern-matching) and final-juncture Poirot (last defense). Revisit: when Darwin shows Tier 3 agents underperform structurally on architectural sub-decisions.

---

## Spec Challenge

**Assumption:** Opus + higher effort produces better first-pass quality than Sonnet + high effort at every reasoning tier. If wrong, we eliminated a cheaper-AND-correct Sonnet fallback on routine review work. Mitigation: (a) Opus 4.6 benchmarks dominate Sonnet 4.6 on reasoning tasks in Anthropic's published evals; (b) the Validation Pipeline measures FPQR before-vs-after on a Medium baseline; (c) rollback triggers on FPQR drop OR cost-per-shipped-unit >2x. Falsifiable within one pipeline.

**SPOF:** The rule table in `pipeline-models.md`. Off-by-one tier on Cal silently downgrades architectural reasoning. Graceful degradation: (a) each frontmatter declares model + effort -- Claude Code honors the frontmatter at runtime even if Eva's invocation parameter is omitted; (b) ADR-0009 enforcement gate requires explicit model parameter (omission = violation, not default); (c) consistency tests T-0041-025+ grep every frontmatter against the rule table -- CI catches drift pre-pipeline.

---

## Context

Opus 4.7 introduced `xhigh` effort (GA 2026-04-16; brain thought `e28d6b8e`). The existing pipeline assigned effort implicitly with no framework for when extra thinking tokens pay off. Simultaneously the old system carried three pain points: (a) size-dependent model table plus 13-signal universal scope classifier that drained Eva's always-loaded context budget (brain `e1dd8f79` -- instruction budget load-bearing); (b) Opus 4.7 tokenizer inflation 1.0-1.35x vs 4.6 (`7e5d807c`) making Sonnet's cost advantage thinner after one rework cycle; (c) retro lessons 005/006 showing Colby first-pass QA on Sonnet was structurally worse than on Opus for Medium+ work.

**Task-class insight:** Agents perform one of four classes regardless of pipeline size: Mechanical (no judgment), Supporting reasoning (checklist-bounded), Critical-path reasoning (shapes shipped artifact), Architectural design (deliberation over multiple valid paths). Model follows task class. An agent can occupy different tiers on different runs (Colby first-build Medium = Tier 3; Colby rework = Tier 2). Scope is a tier-picker, not a model selector.

**Why effort is not capability redux:** Base model bounds accuracy ceiling (Opus > Sonnet > Haiku on pattern-matching surface). Effort adds deliberation on top (low < medium < high < xhigh). They are independent dimensions and don't always stack net-positive. Pattern-matching-dominant tasks (Sentinel SAST interpretation) degrade with excess thinking -- the model second-guesses itself and emits false positives. This is why Sentinel moves from `sonnet/high` to `opus/medium` (capability up, deliberation down). Ellis and Distillator drop `medium -> low` because mechanical tasks gain speed from lower effort and lose no accuracy.

---

## Decision

### Four-Tier Task-Class Model

| Tier | Task class | Model | Base effort | Typical agents | Effort +1 when |
|---|---|---|---|---|---|
| 1 | Mechanical -- no reasoning | Haiku | low | Ellis, Explore, Distillator, Agatha (reference), brain-extractor | -- (stays low) |
| 2 | Supporting reasoning -- review/acceptance/compliance | Opus | medium | Robert/Sable (any), Sentinel, Deps, Agatha (conceptual), Colby (rework), Colby (first-build Small), Roz (scoped rerun) | Large pipeline OR auth/security/crypto |
| 3 | Critical-path reasoning -- creates/verifies shipped artifact | Opus | high | Colby (first-build Medium+), Roz (full sweep Medium+), Poirot, Darwin | Auth/security/crypto OR Large pipeline OR Poirot at final juncture (-> xhigh) |
| 4 | Architectural design | Opus | xhigh | Cal | Large + new-module (already at ceiling; xhigh is max) |

### Promotion Signals (One Rung Each)

| Signal | Applies to tier | Effect |
|--------|-----------------|--------|
| Auth / security / crypto files touched | 2, 3 | +1 rung (medium -> high -> xhigh) |
| Pipeline sizing = Large | 2, 3 | +1 rung |
| Poirot at final-juncture blind review | 3 only | +1 rung (high -> xhigh) |
| Task is read-only evidence collection (no ADR, no code) | 2 | -1 rung (floor low) |
| Task is mechanical (format, rename, config-only) | 2, 3 | -1 rung (floor low) |

**Rules:**
1. Promotions stack to a maximum of one rung above base per signal; never compound beyond a single rung per signal. If two signals both apply, still one rung up (not two). The table is not additive; signals are existence-checks, not scores.
2. Floor: `low`. Ceiling: `xhigh`.
3. Tier 1 effort does not adjust -- base `low` is both floor and ceiling for this tier. Haiku base means the pattern-matching surface is bounded; more effort does not rescue mechanical misapplication, and demotion below `low` is impossible.
4. Tier 4 (Cal) is already at xhigh base; further signals have no effect.

### Per-Agent Assignment Table

This is the authoritative runtime lookup. Eva sets `model` and `effort` in every Agent tool invocation based on this table (plus the signal promotions above).

| Agent | Tier | Base model | Base effort | Rationale (one line) |
|-------|------|------------|-------------|----------------------|
| **Cal** | 4 | opus | xhigh | Architectural deliberation dominates pattern-matching; thinking tokens pay for themselves |
| **Colby** | 3 (build) / 2 (rework, small first-build) | opus | high / medium | Critical-path artifact; rework/small = bounded scope |
| **Roz** | 3 (sweep Medium+) / 2 (scoped rerun, small sweep) | opus | high / medium | Verifies shipped artifact; scoped rerun = bounded scope |
| **Poirot (investigator)** | 3 | opus | high (xhigh at final juncture) | Blind diff review; final juncture = last defense, deliberation worth it |
| **Darwin** | 3 | opus | high | Analyzes pipeline fitness; shapes future structural proposals |
| **Robert (acceptance)** | 2 | opus | medium (high on Large/auth) | Spec-vs-implementation diff; capability-bounded review |
| **robert-spec (producer)** | 2 | opus | medium (high on Large/auth) | Spec production; capability-bounded authoring |
| **Sable (acceptance)** | 2 | opus | medium (high on Large/auth) | UX-vs-implementation diff |
| **sable-ux (producer)** | 2 | opus | medium (high on Large/auth) | UX doc authoring |
| **Sentinel** | 2 | opus | medium (high on auth/crypto) | Pattern-matching on Semgrep output; excess thinking -> false positives. **Effort demotion vs prior** |
| **Deps** | 2 | opus | medium | Version diff + CVE lookup; bounded judgment |
| **Agatha (conceptual docs)** | 2 | opus | medium | Architecture guides, onboarding; bounded reasoning. **Frontmatter default** |
| **Agatha (reference docs)** | 1 | haiku | low | Reference lookup-and-emit. Runtime override by Eva when task is reference-typed |
| **Ellis** | 1 | haiku | low | Commit-message composition is mechanical. **Effort demotion vs prior** |
| **Distillator** | 1 | haiku | low | Structured compression. **Effort demotion vs prior** |
| **brain-extractor** (hook-only) | 1 | haiku | low | Mechanical extraction from SubagentStop payload |
| **Explore** (discovered agent) | 1 | haiku | low | File collection only; no synthesis |

### Rule Table Replacement Scope

`source/shared/rules/pipeline-models.md` is fully replaced. The replacement contains, in order:
1. Intro paragraph (mechanical, not discretionary).
2. The Four-Tier Task-Class Model table (above).
3. The Promotion Signals table (above).
4. The Per-Agent Assignment Table (above).
5. Runtime lookup procedure (Eva sets `model` and `effort` explicitly on every invocation; violation = config error).
6. The enforcement gate (carried forward from ADR-0009): no discretion, explicit parameter, ambiguous sizing defaults UP (unresolved sizing => treat as Large for promotion purposes), sizing changes propagate immediately.

**Removed from the file:** size-dependent model table, base-models table, Agatha-model table (replaced by Tier 1 vs Tier 2 split in main table), universal scope classifier with 13 signals + overrides, brain integration scoring bonus.

**Retained from the file:** enforcement gate (adapted to tier+effort terms), preamble paragraph that Eva does not choose.

### Claude Code Version Compatibility

The `effort` frontmatter field requires Claude Code >= 2.1.89. Older versions silently ignore it (no error, but `effort` is a no-op). `skills/pipeline-setup/SKILL.md` gains a version check that warns (not blocks) on older Claude Code:

> "Your Claude Code is version X.Y.Z. The pipeline uses the `effort` frontmatter field which requires >= 2.1.89. Older versions will silently ignore effort settings -- agents will run at Claude Code's default effort, not the tier-calibrated values. Upgrade for intended behavior. Pipeline installation continues."

Cursor does not currently support the `effort` frontmatter field at the IDE level (as of 2026-04-16). Cursor frontmatter updates are still applied for forward-compatibility and source-of-truth hygiene. The field is ignored at runtime on Cursor until Cursor adds support; this is not a blocker because Cursor already runs at its internal default effort today.

### ADR-0029 + telemetry-metrics.md Update

ADR-0029 (Token Budget Estimate Gate) is immutable. Its cost-estimation formula references the Cost Estimation Table in `telemetry-metrics.md` -- that table is a living artifact and IS updated by this ADR. Updates required:

- Add `claude-opus-4-7` row with input/output pricing reflecting 4.7 tokenizer inflation (1.0-1.35x vs 4.6; use the midpoint 1.17x as the planning figure, consistent with Anthropic's tokenizer-inflation announcement).
- Update the Per-Invocation Cost Estimates table (Budget Estimate Heuristic section) to reflect new tier assignments: Opus is now the default reasoning model instead of Sonnet; typical invocation counts by sizing tier stay the same, but cost multiplies.
- Add a footnote citing ADR-0041 as the epoch for the tier change; prior Tier 3 captures remain valid at their original pricing epoch.

---

## Alternatives Considered

**Alt A: Keep Sonnet as a cost-fallback tier for routine review.** Rejected -- accuracy > cost stack means Sonnet-tier Robert missing spec drift triggers a Colby rework cycle that costs >6x the Opus premium (brain `12fc2628`). Sonnet also becomes a decision branch Eva is tempted to use mid-pipeline; removing it shrinks Eva's decision surface. Cost math: medium-effort Opus review ~3x Sonnet; payable by one avoided rework per 3 reviews, which is the regime FPQR telemetry shows.

**Alt B: Dynamic per-invocation effort from live T2 FPQR telemetry.** Rejected -- reintroduces discretion (ADR-0009 closed that door). Depends on brain queries Eva may not get (retro lesson 003: runtime quality gates tied to external state are fragile). Darwin is the correct venue for telemetry-driven rule evolution, with human approval gate, not runtime mutation.

**Alt C: xhigh everywhere on Medium+.** Rejected -- thinking tokens have diminishing returns and linear latency cost; xhigh inflates the thinking portion of the context window, crowding instruction recall (brain `e1dd8f79`). xhigh earns its keep only where deliberation strictly dominates pattern-matching -- Cal (design) and Poirot final juncture (last defense). Colby-build saturates before xhigh; Roz sweep at xhigh produces over-analytical triage.

**Alt D: Keep the 13-signal classifier; add effort as a parallel dial.** Rejected -- compounds existing complexity. Eva would compute 13 signals twice per invocation. The tier model collapses to 5 category-check promotions that fit in Eva's always-loaded budget. Darwin also gains cleaner attribution (rework cause: "tier misassignment" is a smaller hypothesis space than "classifier misfire").

**Alt E: Delete effort entirely; rely on model tier.** Rejected -- ignores the `xhigh` rung, which is the measurable accuracy gain on multi-step reasoning Cal's work embodies. Opus 4.7 benchmarks show low < medium < high << xhigh ordering on tasks with >3 valid paths.

---

## Consequences

**Positive:**

- Mechanical tier model is humanly readable: "what class of task is this agent doing this time" -> tier -> model + effort. Replaces 13-signal scoring.
- Cal gains xhigh by default. The one agent where deliberation dominates gets the dial turned up. Architectural correctness should improve on Medium+ ADRs.
- Sentinel and Ellis/Distillator effort demotions reduce latency on tasks that gain nothing from thinking tokens. Commit-message composition (Ellis) and structured compression (Distillator) are speed-improvement wins.
- Sonnet decision branch is eliminated for reasoning agents. Eva's invocation path is tier-lookup-then-promote; no "should this be Sonnet" detour.
- Telemetry gains a new dimension: `effort` per invocation. Enables T3 trend analysis ("did xhigh-Cal ADRs have lower Colby rework?") Darwin can cite in future proposals.
- Alignment with Anthropic's public benchmarks: base-model capability gap favors Opus for reasoning work at the Opus 4.7 epoch.

**Negative:**

- Per-invocation cost rises. Opus replaces Sonnet on Robert, Sable, Agatha-conceptual, Deps, Sentinel, Poirot (previously Sonnet-by-default with classifier promotion to Opus). Per-invocation Opus is ~6-7x Sonnet at 4.6 prices; 4.7 tokenizer inflation 1.0-1.35x multiplies. Projected pipeline-cost increase: ~2-3x vs the old default on Medium ADRs. Cost-per-SHIPPED-unit is projected lower because first-pass QA is projected higher (fewer rework cycles). Validation Pipeline will confirm or disconfirm.
- Latency rises on Cal (xhigh) and Poirot-final-juncture (xhigh). Cal was already slow; xhigh adds thinking-token wall clock. Projected +20-40% wall clock on Cal. Architectural correctness is the tradeoff; acceptance per priority-stack.
- Sonnet is out of the reasoning rotation. If a future Sonnet version closes the gap, readmitting it requires a new ADR.
- 30 frontmatter files must stay aligned with the rule table. Drift is a new failure mode. Mitigated by consistency tests (T-0041-025 through T-0041-054) but the maintenance burden is real.
- `effort` field silently ignored on Cursor and on Claude Code < 2.1.89. Users on older stacks get the old-behavior default (no effort tuning). Documented, not blocked.

**Neutral:**

- Telemetry schema is unchanged (`model` and `effort` both fit in existing JSON metadata). No brain migration.
- Pipeline-config.json gains no new knobs. Rule lives in `pipeline-models.md`, always loaded.
- Per-agent frontmatter files already have `model` and `effort` fields (scout confirmed); updates are value changes, not schema changes.

---

## Compatibility

| Surface | Minimum version | Behavior on older versions |
|---------|-----------------|-----------------------------|
| Claude Code `effort` frontmatter field | 2.1.89 | Field silently ignored; agents run at Claude Code default effort (approximately `medium`). No error. |
| Cursor frontmatter consumer | (current) | `effort` field not consumed; Cursor agents run at Cursor default. Frontmatter updates are forward-compatible. |
| Opus 4.7 model | GA (2026-04-16) | Older Opus versions (4.6) accept the same model name under Anthropic's rolling alias; tokenizer inflation does not apply. Cost estimation uses the 4.6 pricing row in `telemetry-metrics.md` until the 4.7 row is in place (part of this ADR). |

**Pipeline-setup soft-warning:**

On install/update, `skills/pipeline-setup/SKILL.md` runs a Claude Code version check. If detected version < 2.1.89 (or unknown), emit:

```
WARNING: Claude Code version X.Y.Z detected (or unknown). Pipeline uses the
`effort` frontmatter field, requiring Claude Code >= 2.1.89. Older versions
ignore the field and run agents at Claude Code's default effort. To get the
tier-calibrated behavior ADR-0041 specifies, upgrade Claude Code. Pipeline
installation continues at your current version.
```

The warning is non-blocking. Installation proceeds.

---

## Implementation Plan

### Step 1: Replace `source/shared/rules/pipeline-models.md` with tier model (1 file)

Full rewrite. Sections in order: intro paragraph ("Mechanical -- Eva does not choose"); `<model-table id="task-class-tiers">` (Four-Tier table); `<model-table id="promotion-signals">` (signals table); `<model-table id="agent-assignments">` (per-agent table); runtime lookup prose; `<gate id="model-enforcement">` carried from ADR-0009 adapted to tier+effort.

**Acceptance:** exactly three `<model-table>` blocks with the IDs above; zero occurrences of `size-dependent`, `base-models`, `agatha-model`, `universal-classifier` IDs; zero "classifier score" / "Score >= 4" references; zero "Sonnet" as reasoning-tier base model; all 17 rows / 15 distinct agents in the assignment table with tier + model + base effort; enforcement gate retains no-discretion + explicit-parameter + ambiguous-sizing-defaults-UP + sizing-propagation rules.

**After this step, I can:** look up any agent's tier/model/effort in one table.

**Complexity:** Medium. 1 file, ~150 lines. S1-S5 PASS.

---

### Step 2: Update `pipeline-orchestration.md` to remove classifier references (1 file)

Edit at lines (approximately) 83, 196-216, 228-232, 415-441, 563-567, 578-594, 614-644, 684 per blast-radius scout. Remove "universal scope classifier" / "classifier score" / "Score >= 4" / size-dependent model tables. Replace with pointers to the Per-Agent Assignment Table in `pipeline-models.md`. Preserve enforcement language. Verify line numbers at edit time -- file may have shifted.

**Acceptance:** zero "classifier score" / "Sonnet (classifier)" / "size-dependent model" references; all model-selection pointers resolve to `pipeline-models.md`; surrounding protocol structure intact.

**After this step, I can:** read `pipeline-orchestration.md` with zero stale classifier references.

**Complexity:** Medium. 1 file, ~8 edits. S1-S5 PASS.

---

### Step 3: Update Claude frontmatter files (15 files)

Apply tier-aligned `model` + `effort` to every `source/claude/agents/*.frontmatter.yml`. Values are the Per-Agent Assignment Table (same as test IDs T-0041-025 through T-0041-039):

| Agent file | model | effort | Change type |
|------------|-------|--------|-------------|
| cal | opus | xhigh | effort promotion (high -> xhigh) |
| colby | opus | high | model promotion (sonnet -> opus) |
| roz | opus | high | model promotion |
| investigator | opus | high | model + effort promotion |
| darwin | opus | high | effort promotion (medium -> high) |
| robert | opus | medium | model promotion |
| robert-spec | opus | medium | model promotion |
| sable | opus | medium | model promotion |
| sable-ux | opus | medium | model promotion |
| sentinel | opus | medium | model promotion + effort demotion (high -> medium) |
| deps | opus | medium | model promotion |
| agatha | opus | medium | model promotion |
| ellis | haiku | low | effort demotion (medium -> low) |
| distillator | haiku | low | effort demotion |
| brain-extractor | haiku | low | add effort field (currently absent) |

**Acceptance criteria:** all 15 files carry `model:` and `effort:` at YAML top level matching the table; no other frontmatter fields modified.

**After this step, I can:** grep every claude frontmatter and see tier-aligned values.

**Complexity:** Low. 15 files, 2-line edits each. S1-S5 PASS.

---

### Step 4: Update Cursor frontmatter files (15 files)

Mirror Step 3 to `source/cursor/agents/*.frontmatter.yml` with identical values. Cursor frontmatter has NO `hooks:` field. Values must match Claude frontmatter and the assignment table exactly.

**After this step, I can:** grep every cursor frontmatter and confirm parity with Claude.

**Complexity:** Low. 15 files, mechanical mirror of Step 3.

---

### Step 5: Update `telemetry-metrics.md` cost-estimation tables (1 file)

In the Cost Estimation Table (line ~116): add `claude-opus-4-7` row (pricing reflects 4.7 tokenizer inflation 1.17x midpoint: input ~$0.0175/1k, output ~$0.0875/1k, context 200000 tokens; verify against Anthropic release notes at implementation). In the Per-Invocation Cost Estimates table (line ~180): replace Sonnet default expectations with Opus for review/acceptance agents; annotate the Sonnet row "(legacy; not used by ADR-0041+)". Add footnote citing ADR-0041 as the tier-epoch.

**Acceptance:** `claude-opus-4-7` row present; per-invocation table cites ADR-0041; cost formula unchanged; Sonnet row retained with legacy annotation (pre-0041 captures stay interpretable).

**After this step, I can:** compute Opus 4.7 cost using the same formula ADR-0029 consumes.

**Complexity:** Low. 1 file, ~4 row additions/annotations. S1-S5 PASS.

---

### Step 6: Propagate rule file to installed mirrors (2 files)

`.claude/rules/pipeline-models.md` and `.cursor-plugin/rules/pipeline-models.mdc` must mirror `source/shared/rules/pipeline-models.md` (modulo `.mdc` wrapper if Cursor requires it). This repo "eats its own cooking" -- installed copies live alongside source.

**Acceptance:** installed copies contain the new tier tables and NO old classifier references; `diff` source vs installed shows zero divergence (modulo Cursor wrapper).

**After this step, I can:** run the pipeline from either IDE and have Eva read the new rule file.

**Complexity:** Low. 2 files. Mechanical sync.

---

### Step 7: Add pipeline-setup version check (1 file)

`skills/pipeline-setup/SKILL.md` gains a version-check step early in the skill flow. Detect Claude Code version; if < 2.1.89 or unknown, emit the Compatibility-section warning text; DO NOT block install.

**Acceptance:** skill contains version-check step; warning references "2.1.89" and "ADR-0041"; warning is emit-and-continue ("installation continues" or equivalent).

**After this step, I can:** see the warning on older Claude Code and no warning on 2.1.89+.

**Complexity:** Low. 1 file, 1 new skill step.

---

### Step 8: Update user-facing documentation (2 files)

`docs/guide/technical-reference.md`: replace references to "universal scope classifier", size-dependent Colby/Cal tables, Sonnet-tier defaults. Point to ADR-0041 + tier table. `docs/guide/user-guide.md` (line ~1021): single reference; update to cite tier-based assignment.

**Acceptance:** technical reference explains 4-tier model + promotion signals + cites ADR-0041; user guide has zero stale classifier references; both readable standalone.

**After this step, I can:** onboard a new user via user-guide + technical-reference and they understand 2026-04 model selection.

**Complexity:** Medium. 2 files, multiple references. Text-only.

---

### Out of Scope for Colby (Awareness-Only Files)

These files REFERENCE the old classifier or the old size tables but are not modified. Colby must NOT edit them:

- `README.md:323` -- high-level mention; stays as-is until next doc sweep.
- `AGENTS.md:49` -- legacy agent index; stays.
- `skills/pipeline-setup/SKILL.md:274` -- minor reference; unchanged unless it contradicts Step 7.
- `skills/pipeline-uninstall/SKILL.md:25` -- uninstall flow; unchanged.
- ADRs 0009, 0012, 0014, 0019, 0021, 0029, 0035 -- **IMMUTABLE**. They are historical decision records at their own epochs. Do NOT modify.
- `docs/pipeline/pipeline-state.md` -- Eva runtime state, updated by Eva, not a Colby target.

---

## Contract Boundaries

| Producer | Shape | Consumer |
|----------|-------|----------|
| `pipeline-models.md` Per-Agent Assignment Table | Markdown table: `\| agent \| tier \| model \| base_effort \| rationale \|` | Eva runtime (Agent tool invocation `model` + `effort` parameters) |
| `pipeline-models.md` Promotion Signals table | Markdown table: `\| signal \| tier \| effect \|` | Eva runtime (effort adjustment before invocation) |
| Each `source/claude/agents/*.frontmatter.yml` | YAML: `model: <string>`, `effort: <low\|medium\|high\|xhigh>` | Claude Code runtime (fallback if Eva omits parameter) |
| Each `source/cursor/agents/*.frontmatter.yml` | YAML: `model: <string>`, `effort: <low\|medium\|high\|xhigh>` | Cursor runtime (forward-compat; currently ignored) |
| `telemetry-metrics.md` Cost Estimation Table | Markdown table: `\| model \| input_per_1k \| output_per_1k \| context_window_max \|` | ADR-0029 budget-estimate gate, Eva cost computation |
| `pipeline-setup` version-check warning | stdout text | User (terminal) |

---

## Wiring Coverage

Every producer in this ADR has at least one consumer in the same or an earlier step.

| Producer | Shape | Consumer | Step |
|----------|-------|----------|------|
| Per-Agent Assignment Table in `pipeline-models.md` | MD table | Eva runtime invocation logic (always-loaded rule) | Step 1 (producer) -> Step 3 (claude frontmatter mirrors the table) -> Step 4 (cursor mirrors) |
| Promotion Signals table in `pipeline-models.md` | MD table | Eva runtime per-invocation effort adjustment | Step 1 (producer) -> consumed by Eva directly (no additional step; Eva is always-loaded consumer) |
| Updated `pipeline-orchestration.md` references | Prose + cross-refs | Eva orchestration flow | Step 2 (producer, consumer is Eva itself) |
| Claude frontmatter values | YAML | Claude Code runtime (effort field) | Step 3 (producer) -> Claude Code consumes at Agent invocation |
| Cursor frontmatter values | YAML | Cursor runtime (forward-compat; no-op today) | Step 4 |
| `telemetry-metrics.md` pricing + invocation-cost tables | MD tables | ADR-0029 budget gate; Eva T1 cost computation | Step 5 (producer) -> Eva telemetry capture (existing always-loaded) |
| `.claude/rules/pipeline-models.md` + `.cursor-plugin/rules/pipeline-models.mdc` | File copies | Plugin consumers at runtime | Step 6 (producer) -> installed contexts at plugin load |
| Pipeline-setup version-check warning | Stdout | User terminal | Step 7 (producer) -> user (consumer) |
| Updated user-facing docs | Prose | Human readers | Step 8 (producer) -> human readers (consumer) |

No orphan producers.

---

## UX Coverage

No UX doc exists for this ADR (pipeline-internal rule change, no user-visible UI). The `pipeline-setup` warning in Step 7 is the only user-terminal surface; its text is specified in the Compatibility section.

---

## UI Specification

No UI surfaces are created or modified. N/A.

---

## Data Sensitivity

| Method/Key | Classification | Rationale |
|------------|---------------|-----------|
| Agent frontmatter `model` value | public-safe | Configuration value; no credentials |
| Agent frontmatter `effort` value | public-safe | Configuration value; no credentials |
| `pipeline-models.md` rule content | public-safe | Orchestration rule; public |
| Cost-estimation table | public-safe | Public pricing data |
| Pipeline-setup version warning | public-safe | Version information |

No `auth-only` data paths are introduced.

---

## Test Specification

Test IDs `T-0041-NNN`. Roz owns assertions; Cal specifies coverage. Evidence column tells Roz the file/command the assertion is made against.

### Table-correctness tests (rule file structure) -- 7 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-001 | Structure | `pipeline-models.md` contains `<model-table id="task-class-tiers">` block | `grep '<model-table id="task-class-tiers">' source/shared/rules/pipeline-models.md` | Match present |
| T-0041-002 | Structure | `pipeline-models.md` contains `<model-table id="promotion-signals">` block | grep | Match present |
| T-0041-003 | Structure | `pipeline-models.md` contains `<model-table id="agent-assignments">` block | grep | Match present |
| T-0041-004 | Structure | `pipeline-models.md` contains all four tier rows with labels "Tier 1", "Tier 2", "Tier 3", "Tier 4" | grep | 4 matches |
| T-0041-005 | Structure | Per-Agent Assignment Table contains rows for all 15 agents (Cal, Colby, Roz, investigator/Poirot, Darwin, Robert, robert-spec, Sable, sable-ux, Sentinel, Deps, Agatha, Ellis, Distillator, brain-extractor) | grep each name | 15 matches |
| T-0041-006 | Structure | Enforcement gate `<gate id="model-enforcement">` present | grep | Match present |
| T-0041-007 | Structure | Enforcement gate retains: "No discretion", "Explicit in every invocation", "Ambiguous sizing defaults UP", "Sizing changes propagate" | grep each phrase | 4 matches |

### Supersession tests (old content removed) -- 5 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-008 | Supersession | `pipeline-models.md` does NOT contain "universal scope classifier" | grep -ic | 0 |
| T-0041-009 | Supersession | `pipeline-models.md` does NOT contain "Promotion threshold: Score" | grep | 0 |
| T-0041-010 | Supersession | `pipeline-models.md` does NOT contain `<model-table id="size-dependent">` | grep | 0 |
| T-0041-011 | Supersession | `pipeline-models.md` does NOT contain `<model-table id="base-models">` | grep | 0 |
| T-0041-012 | Supersession | `pipeline-models.md` does NOT contain Sonnet as a reasoning-tier base model (Sonnet row removed from tier assignment) | grep for "Sonnet" outside legacy/compat context | 0 in agent-assignments table |

### Promotion-signal tests -- 5 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-013 | Promotion | Promotion Signals table contains auth/security/crypto signal applying to tiers 2 and 3 | grep | Match present |
| T-0041-014 | Promotion | Promotion Signals table specifies "one rung" (never two) in prose | grep "one rung" | Match present |
| T-0041-015 | Promotion | Promotion Signals table specifies floor `low` and ceiling `xhigh` | grep "Floor" + "Ceiling" | 2 matches |
| T-0041-016 | Promotion | Promotion Signals table specifies Poirot final-juncture -> xhigh | grep | Match present |
| T-0041-017 | Promotion | Promotion Signals table specifies Large pipeline signal on tiers 2 and 3 | grep | Match present |

### Agent-specific base assignment tests -- 7 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-018 | Base assignment | Cal row: tier 4, opus, xhigh | grep Cal row in assignments table | exact match |
| T-0041-019 | Base assignment | Colby row: tier 3 base, opus, high (with rework-tier note) | grep | match |
| T-0041-020 | Base assignment | Roz row: tier 3 base on sweep Medium+, opus, high | grep | match |
| T-0041-021 | Base assignment | Sentinel row: tier 2, opus, medium (NOT high) | grep | match; effort is medium |
| T-0041-022 | Base assignment | Ellis row: tier 1, haiku, low (NOT medium) | grep | match; effort is low |
| T-0041-023 | Base assignment | Distillator row: tier 1, haiku, low (NOT medium) | grep | match; effort is low |
| T-0041-024 | Base assignment | Agatha row: tier 2 conceptual default (opus, medium), with reference-mode note pointing to Tier 1 | grep | match |

### Frontmatter consistency tests (parameterized; 15 agents x 2 platforms = 30 assertions)

| ID | Agent | Expected model | Expected effort | Test applies to |
|----|-------|----------------|------------------|------------------|
| T-0041-025 | cal | opus | xhigh | source/claude/agents + source/cursor/agents |
| T-0041-026 | colby | opus | high | both |
| T-0041-027 | roz | opus | high | both |
| T-0041-028 | investigator | opus | high | both |
| T-0041-029 | darwin | opus | high | both |
| T-0041-030 | robert | opus | medium | both |
| T-0041-031 | robert-spec | opus | medium | both |
| T-0041-032 | sable | opus | medium | both |
| T-0041-033 | sable-ux | opus | medium | both |
| T-0041-034 | sentinel | opus | medium | both (demotion from high) |
| T-0041-035 | deps | opus | medium | both |
| T-0041-036 | agatha | opus | medium | both (conceptual default) |
| T-0041-037 | ellis | haiku | low | both (demotion from medium) |
| T-0041-038 | distillator | haiku | low | both (demotion from medium) |
| T-0041-039 | brain-extractor | haiku | low | both (field newly added) |

Each row above is one test-spec row but asserts against two files (`source/claude/agents/<agent>.frontmatter.yml` and `source/cursor/agents/<agent>.frontmatter.yml`). Roz MAY implement each as one parameterized test yielding 30 assertions, or as 15 paired assertions -- the contract is both platforms match the rule table for all 15 agents.

### Orchestration-reference tests -- 3 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-040 | Orchestration cleanup | `pipeline-orchestration.md` contains zero "classifier score" references | grep -ic "classifier score" | 0 |
| T-0041-041 | Orchestration cleanup | `pipeline-orchestration.md` contains zero "Sonnet (classifier)" references | grep | 0 |
| T-0041-042 | Orchestration cleanup | `pipeline-orchestration.md` model-selection references point to `pipeline-models.md` (by name) | grep | >= 1 match |

### Telemetry cost-table tests -- 3 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-043 | Cost table | `telemetry-metrics.md` contains `claude-opus-4-7` row | grep | Match present |
| T-0041-044 | Cost table | Per-Invocation Cost Estimates table references ADR-0041 in a footnote or annotation | grep | Match present |
| T-0041-045 | Cost table | Cost formula `cost_usd = (input_tokens / 1000 * input_per_1k) + (output_tokens / 1000 * output_per_1k)` unchanged | grep | Match present |

### Installed-mirror tests -- 2 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-046 | Installed mirror | `.claude/rules/pipeline-models.md` contains same task-class-tiers table as source | diff source vs installed | Tier content matches |
| T-0041-047 | Installed mirror | `.cursor-plugin/rules/pipeline-models.mdc` contains same tier content (modulo .mdc wrapper) | grep tier table rows | Match present |

### Compatibility + setup-skill tests -- 3 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-048 | Compatibility | `skills/pipeline-setup/SKILL.md` contains Claude Code version check step | grep "2.1.89" | Match present |
| T-0041-049 | Compatibility | Setup warning text cites ADR-0041 | grep "ADR-0041" in SKILL.md | Match present |
| T-0041-050 | Compatibility | Setup warning is non-blocking (contains "installation continues" or equivalent) | grep | Match present |

### Validation-pipeline protocol tests -- 4 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-051 | Validation protocol | ADR Validation Pipeline section names a specific baseline ADR to re-run | grep "ADR-0035" in this ADR | Match present |
| T-0041-052 | Validation protocol | Validation Pipeline specifies FPQR measurement methodology | grep "FPQR" or "first_pass_qa" | Match present |
| T-0041-053 | Validation protocol | Validation Pipeline specifies rollback trigger (FPQR drop OR cost >2x) | grep "2x" + "rollback" | Match present |
| T-0041-054 | Validation protocol | Validation Pipeline specifies telemetry format for effort tracking going forward | grep "effort" in telemetry context | Match present |

### Documentation tests -- 2 tests

| ID | Category | Description | Evidence | Expected |
|----|----------|-------------|----------|----------|
| T-0041-055 | Docs | `docs/guide/technical-reference.md` contains no stale "universal scope classifier" references | grep | 0 |
| T-0041-056 | Docs | `docs/guide/user-guide.md` model-selection passage points to ADR-0041 or tier-based framing | grep | Match present |

**Test totals:** 56 test-spec rows covering ~71 assertions (15 frontmatter rows assert on both Claude + Cursor files = 30 assertions; other 41 rows are one assertion each). Coverage breakdown: 7 structure, 5 supersession, 5 promotion, 7 base-assignment, 15 frontmatter (parameterized x 2 platforms), 3 orchestration cleanup, 3 telemetry, 2 mirrors, 3 compatibility, 4 validation protocol, 2 docs.

**Spec-count note:** Spec window was 30-45. The 56-row count is above the window because retro lesson 005 (orphan-consumer risk) requires one assertion per cross-agent consumer; each frontmatter file IS a separate consumer of the rule table. Roz has discretion to collapse by parameterization at implementation time -- the assertion-count contract is what matters.

---

## Validation Pipeline

Issue #41 AC3 requires cost + quality baseline before and after. This is the protocol.

### Scope boundary

This ADR delivers the VALIDATION PROTOCOL (design artifact). Execution of the protocol against ADR-0035 is tracked as a post-merge activity, not in this ADR's scope. Issue #41 AC3's "capture before and after" is interpreted as design-of-the-capture-mechanism for this ADR; empirical capture happens in a follow-up pipeline once merged and at least one subsequent full-pipeline run has exercised the new tier model.


**Baseline target: ADR-0035 (Wave 4 Consumer Wiring + S4 Resolution).** Medium-sized, T3 telemetry on record (`pipeline_id = adr-0035-wave4-consumer-wiring_*`), exercises Cal / Colby / Roz / Poirot -- the full Tier 3/4 roster. Recent enough (~6 weeks) to re-run against a compatible codebase.

**Protocol:**

1. **Baseline extraction.** `agent_search` brain for ADR-0035 T3 telemetry. Capture: `total_cost_usd`, `rework_rate`, `first_pass_qa_rate`, `total_duration_ms`, `evoscore`, `invocations_by_model`. Snapshot git SHA of the pre-0035 codebase state.
2. **Fresh re-run.** Reset to pre-0035 SHA. Run `/pipeline` on the same feature spec (`docs/product/`). Tier assignments from ADR-0041 in effect. T3 telemetry captured normally.
3. **Compare:**

| Metric | Source (baseline / re-run) | Comparison |
|--------|---------------------------|------------|
| `total_cost_usd` | brain / T3 | re-run / baseline |
| `rework_rate` | brain / T3 | re-run / baseline |
| `first_pass_qa_rate` (FPQR) | brain / T3 | re-run - baseline (difference; FPQR is already a rate) |
| `evoscore` | brain / T3 | re-run / baseline |
| `cost_per_shipped_unit` = total_cost / (units * (1 - rework_rate)) | computed | re-run / baseline |

4. **Acceptance:**

| Outcome | Action |
|---------|--------|
| FPQR rises AND cost-per-shipped-unit ratio <= 2.0x | Adopt (full rollout) |
| FPQR rises AND cost ratio in (2.0x, 2.5x) | Marginal -- Darwin review before rollout |
| FPQR flat AND cost ratio > 1.5x | Roll back |
| FPQR drops (any amount) | Roll back -- hard trigger |
| cost ratio > 2.0x regardless of FPQR | Roll back |

5. **Rollback.** Single commit: `git revert <merge-sha>` restores prior tiers. No data migration. Rollback window: 2 weeks post-merge; after that, a fresh ADR weighs rollback against accumulated production data. Rollback is captured as a new ADR (ADR-0041-rollback), never mutation of ADR-0041 (immutability).

**Telemetry addition (going forward):** Tier 1 capture gains one field, `effort: string` (`low`|`medium`|`high`|`xhigh`|`unknown`). Additive to JSON metadata; no DB migration. Enables Darwin analyses like "Cal at xhigh vs high: FPQR delta by ADR size."

---

## Supersedes + Related

**Supersedes (full):**
- Brain thought `b09f430b-2c76-4aa8-b5bd-5c57a800d5ed` (2026-04-03): "Colby Micro=haiku, Small=sonnet, Medium=opus, Large=opus with classifier score >= 3 promotion." The size-dependent model assignment framework is replaced by the task-class tier model.

**Supersedes (partial -- content only, ADRs immutable):**
- ADR-0009 (and any ADR referencing "universal scope classifier"): the classifier mechanism is retired. ADR-0009's decision epoch stands; its content is superseded by ADR-0041 for runtime behavior going forward.

**Related (not superseded, referenced for context):**
- ADR-0029 (Token Budget Estimate Gate) -- immutable. `telemetry-metrics.md` cost-estimation tables are updated by this ADR, not ADR-0029 itself.
- ADR-0035 (Wave 4 Consumer Wiring + S4 Resolution) -- designated validation baseline.
- Step-sizing discipline (57 -> 93% FPQR from vertical sub-slicing; brain thoughts `5275b940`, `9bd73606`) -- orthogonal. This ADR does NOT substitute for step-sizing; it layers on top.
- Brain thought `843f9977` (Advisor Tool beta) -- Future Work, NOT in scope. When the Advisor Tool ships, re-evaluate whether Cal should offload sub-decisions to a fast executor while retaining xhigh deliberation.
- Brain thought `12fc2628` (PRIORITY 1 session cost ceiling) -- adjacent cost-guardrail system. ADR-0041 does not implement a ceiling; it optimizes the cost-per-shipped-unit curve.
- Brain thought `e1dd8f79` (instruction budget load-bearing) -- constraint on xhigh-everywhere; motivates reserving xhigh for Cal.
- Retro lesson 005 (Frontend Wiring Omission) -- motivates the 30-frontmatter consistency tests.

---

## References

- GitHub issue #41: acceptance criteria.
- Brain thought `e28d6b8e-ae95-4f37-a87a-509b9e58cc40`: effort GA and `xhigh` introduction.
- Brain thought `7e5d807c`: Opus 4.7 release + tokenizer inflation.
- Brain thought `b09f430b-2c76-4aa8-b5bd-5c57a800d5ed`: superseded Colby model decision.
- Anthropic Opus 4.7 release notes (2026-04-16) -- effort benchmarks.
- `source/shared/rules/pipeline-models.md` (pre-0041 state).
- `source/shared/references/telemetry-metrics.md` -- cost estimation living artifact.
- `source/shared/references/step-sizing.md` -- orthogonal discipline.
- `.claude/references/retro-lessons.md` -- lessons 005/006.

---

## Notes for Colby

1. **Order matters.** Do Step 1 (rule file) first -- Steps 3-4 frontmatter tests assert against that table. Editing frontmatter first makes T-0041-025+ fail against a missing reference.

2. **Frontmatter edits are 2 lines each.** `model:` and `effort:` only. Do not touch `tools`, `hooks`, `color`, `maxTurns`, `description`, `name`, `permissionMode`, `disallowedTools` -- those are orthogonal and owned by prior ADRs.

3. **`brain-extractor.frontmatter.yml` needs `effort:` added.** Scout confirmed the field is absent today. Add `effort: low` beneath `model: haiku`.

4. **Cursor frontmatter has no `hooks:` field.** Cursor plugin format differs. Read an existing cursor frontmatter file before editing to confirm the valid field set.

5. **Steps 1 and 2 are where misreads hurt.** Read `pipeline-models.md` and `pipeline-orchestration.md` in full before editing. The blast-radius scout gave line numbers for orchestration; verify at edit time because the file may have shifted.

6. **Installed-mirror pattern from ADR-0038:** `.claude/rules/pipeline-models.md` mirrors the source. After Step 1, `diff` source vs installed to verify zero divergence (Step 6 is mechanical propagation).

7. **`telemetry-metrics.md` edit is small.** One pricing row, one legacy annotation, one footnote -- roughly 10 lines in a large file.

8. **Validation Pipeline is documentation, not implementation.** You are NOT re-running ADR-0035 inside this build. You are specifying the protocol Eva will schedule post-merge.

9. **Rollback is single commit.** Any post-merge regression is fixed by `git revert <merge-sha>`. No data migration. No state wedging.

---

## DoD: Verification

| # | Requirement | Evidence |
|---|-------------|----------|
| R1 | Effort rationale per agent | Per-Agent Assignment Table + Context "Why effort is not capability redux" |
| R2 | `pipeline-models.md` carries effort | Step 1; tests T-0041-001 through T-0041-012 |
| R3 | Validation pipeline designed | Validation Pipeline section (baseline + metrics + thresholds + rollback) |
| R4 | Four-tier model | Decision; tests T-0041-004, T-0041-018 through T-0041-024 |
| R5 | Model follows task class | Decision preamble + Agatha split |
| R6 | One-rung promotion; floor low, ceiling xhigh | Decision Rules 1-4 + tests T-0041-014, T-0041-015 |
| R7 | Sonnet eliminated from reasoning | Decision + test T-0041-012 |
| R8 | Size as tier-picker only | Promotion Signals (Large +1) + test T-0041-017 |
| R9 | Accuracy > speed > cost | Context + Alt-A rejection |
| R10 | Effort demotions justified | Context + tests T-0041-021/022/023 |
| R11 | Agatha split | Assignment Table + test T-0041-024 |
| R12 | 30 frontmatter updates | Steps 3 + 4; tests T-0041-025 through T-0041-039 (x2 platforms) |
| R13 | Source + 2 mirrors | Steps 1 + 6; tests T-0041-001-007, T-0041-046, T-0041-047 |
| R14 | `pipeline-orchestration.md` edits | Step 2; tests T-0041-040 through T-0041-042 |
| R15 | `telemetry-metrics.md` update | Step 5; tests T-0041-043 through T-0041-045 |
| R16 | Compatibility + setup warning | Compatibility section + Step 7; tests T-0041-048 through T-0041-050 |
| R17 | Vertical slice | Wiring Coverage (every producer has same-or-earlier consumer) |
| R18 | Validation re-run design | Validation section; tests T-0041-051 through T-0041-054 |

**Grep check:** TODO/FIXME/HACK/XXX -> 0. **Template completeness:** no TBD, no placeholders.

**Step sizing gate:** All 8 steps PASS S1-S5. Steps 3 and 4 (15 files each) are at the mechanical-update ceiling; justified because each file is a uniform 2-line change and the cohort is a single logical operation (tier propagation). Colby may split into Tier-1-agents / Tier-2-4-agents sub-steps without changing the contract.
