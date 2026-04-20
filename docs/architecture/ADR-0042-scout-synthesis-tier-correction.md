# ADR-0042: Scout Synthesis Layer and Model/Effort Tier Corrections

## Status

Accepted. **Supersedes (portions of):** ADR-0041 -- specifically the Per-Agent Assignment Table, the Promotion Signals table, and the Agatha Tier 1 "runtime override" row. ADR-0041 remains in force for the task-class tier abstraction and the model enforcement gate; only the per-agent assignments and promotion-signal contents are replaced. **Related (not modified):** ADR-0033 (scout fan-out enforcement hook -- `enforce-scout-swarm.sh` continues to enforce scout presence; synthesis is an additional step, not a replacement), ADR-0023 (Distillator spec reduction -- independent from model assignment; see Context note below), ADR-0009 (model enforcement gate -- unchanged), ADR-0029 (cost tables -- unchanged here; Sonnet rates replace Haiku rates in agent lines but the table structure is untouched).

---

## DoR: Requirements Extracted

**Sources:** Task brief, research brief (blast-radius + patterns scouts confirmed by read-list above), retro-lessons.md, context-brief.md, Anthropic Opus 4.7 adaptive-thinking article (cited in brief), confirmed active problem "Roz running out of context on medium+ waves."

| # | Requirement | Source |
|---|-------------|--------|
| R1 | Add a Sonnet synthesis step after haiku scout fan-out for Cal, Colby, and Roz | Task brief + `<research-brief>` synthesis section |
| R2 | Synthesis agent filters/ranks/trims only -- no design opinions | `<research-brief>` "Does NOT form opinions" |
| R3 | Define precise synthesis output shape for Cal, Colby, Roz (three distinct shapes) | `<research-brief>` per-agent output shapes |
| R4 | Rewrite Per-Agent Assignment Table with 7 model/effort changes | `<research-brief>` current-state table |
| R5 | Remove Agatha Tier 1 "runtime override" row (not mechanically enforceable) | `<research-brief>` Agatha Tier 1 override elimination |
| R6 | Remove "auth/security/crypto" promotion signal (wrong lever; route to Sentinel instead) | `<research-brief>` promotion signal changes |
| R7 | Remove "Pipeline sizing = Large" promotion signal (more files != more deliberation) | `<research-brief>` promotion signal changes |
| R8 | Keep "Poirot at final-juncture" +1 signal | `<research-brief>` promotion signal changes |
| R9 | Keep existing read-only evidence (-1) and mechanical (-1) demotion signals | `<research-brief>` "Simplify to 2 signals ... demotion for mechanical/read-only tasks (keep existing)" |
| R10 | Explicitly forbid `max` effort in enforcement gate | `<research-brief>` Anthropic article citation |
| R11 | Add explicit spawn directive: Eva MUST spawn scouts and synthesis as separate parallel subagents, not in-thread | `<research-brief>` Opus 4.7 fewer-subagent-by-default |
| R12 | Document adaptive-thinking rationale for medium vs high vs xhigh | `<research-brief>` Anthropic article citation |
| R13 | Update 7 `source/claude/agents/*.frontmatter.yml` files (model and/or effort only) | `<research-brief>` blast-radius + table |
| R14 | Update 7 `source/cursor/agents/*.frontmatter.yml` files (mirror) | `<research-brief>` blast-radius + table |
| R15 | Update `source/shared/rules/pipeline-models.md` | `<research-brief>` blast-radius |
| R16 | Update `source/shared/rules/pipeline-orchestration.md` (Scout Fan-out Protocol) | `<research-brief>` blast-radius |
| R17 | Update `source/shared/references/invocation-templates.md` (add Template 2c; update 2a, 4, 8) | `<research-brief>` blast-radius |
| R18 | Mirror installed rules (`.claude/rules/pipeline-models.md`, `.cursor-plugin/rules/pipeline-models.mdc`) | `<research-brief>` blast-radius |
| R19 | Do NOT modify persona bodies, tests, CHANGELOG, `enforce-scout-swarm.sh`, `hooks:` / `tools:` / `color` / `maxTurns` / `description` / `name` / `permissionMode` / `disallowedTools` fields | `<constraints>` |
| R20 | Verify `enforce-scout-swarm.sh` does NOT enforce haiku-only for scouts (synthesis is a post-scout NEW step) | `<constraints>` hook-check directive |
| R21 | Vertical slice: rule-table producer + synthesis-template consumer + frontmatter consumer + Eva-protocol consumer must land together | Retro lesson 005 + Hard Gate #4 |
| R22 | Clarify Distillator model change (Haiku -> Sonnet) is independent from ADR-0023's spec-reduction exemption | `<research-brief>` brain context note |

**Retro risks:**
- **Lesson 005 (cross-agent wiring):** The rule table is a cross-agent contract; the synthesis protocol is a new contract. Rule file (producer) must propagate to 14 frontmatter files + 3 invocation templates + 2 installed mirrors. Every producer in the Implementation Plan has a consumer in the same or earlier step. See Wiring Coverage section.
- **Lesson 002 (self-reporting):** Cal writes this ADR + test spec; Roz reviews the test spec before Colby builds. Roz owns authoritative assertions.
- **Lesson 003 (Stop hook duplication):** `enforce-scout-swarm.sh` already enforces scout-block presence. The synthesis step produces output that goes INTO the existing scout-block -- no new hook needed, no duplication of enforcement.
- Lessons 001, 004, 006: N/A for this ADR (no data access, no long-running commands, no UI surfaces).

**Brain context (no-brain run):** Brain is not explicitly flagged available for this ADR. Research brief cites brain thought context from prior ADRs: ADR-0023 ("Distillator exempted -- Haiku needs procedural density") refers to **agent spec reduction** (removing procedures from Distillator's persona body), not model assignment. The Distillator model change Haiku->Sonnet in this ADR is compatible with that decision: the persona body remains procedurally dense; only the model underneath changes. No conflict.

---

## Anti-Goals

**Anti-goal 1: Synthesis agents forming independent design opinions or proposing solutions.**
Reason: The synthesis role is filter+rank+trim, nothing else. The moment a synthesis agent starts "recommending an approach," it becomes a shadow architect with no DoR/DoD, no retro-lesson accountability, and no test coverage -- it would silently influence Cal, Colby, and Roz outputs in ways no reviewer catches. The synthesis output is data, not judgment. Revisit: when Darwin reports structural under-deliberation at the synthesis boundary and a formal tier for opinion-forming middleware is proposed via a new ADR.

**Anti-goal 2: Re-introducing a size-dependent model classifier via the back door (e.g., "Large => promote synthesis to Opus").**
Reason: ADR-0041 eliminated the 13-signal classifier precisely because pipeline size is a tier-picker, not a per-invocation model selector. Promoting synthesis based on Large would re-create the exact discretion ADR-0041 removed, and the removal of the "Large => +1" promotion signal in this ADR is the whole point. Synthesis stays Sonnet/low across all sizings. Revisit: when five pipeline runs show synthesis dropping load-bearing facts on Large pipelines -- then raise to Sonnet/medium or shrink scout output first (shrink preferred).

**Anti-goal 3: `max` effort anywhere in the pipeline, ever, for any agent.**
Reason: Per Anthropic's Opus 4.7 adaptive-thinking guidance, `max` is evaluation-only -- it is prone to overthinking and produces degraded output on production workloads. Allowing it "just for Cal on new-module Large" reopens the overthinking cliff. Ceiling stays `xhigh`. Revisit: when Anthropic ships a production-grade `max` profile with documented workload guidance.

---

## Spec Challenge

**Assumption:** A single Sonnet/low synthesis pass between scouts and the primary agent reduces the primary agent's context pressure enough to fix Roz's observed exhaustion on medium+ waves, without dropping load-bearing facts. If wrong, the design fails because Roz still exhausts context (synthesis under-shrinks) or Roz blocks on missing evidence (synthesis over-shrinks and loses the fact that would have caught the bug).

Mitigation: (a) synthesis output shapes are explicit (see Decision) and per-agent; (b) every shape preserves file:line evidence, not prose; (c) the test spec asserts both floor (no shape under 3 fields) and ceiling (no field allowed to contain full-file dumps) on the synthesis contract; (d) Roz's synthesis shape preserves changed-section extracts per file, not the full file -- that is the exact mechanism solving context exhaustion; (e) on the first Medium+ wave after deployment, Roz is explicitly instructed (via retro lesson entry) to flag missing evidence as a synthesis defect, not a scout defect, so the next pipeline can re-tune the shape. Falsifiable within one Medium pipeline run.

**SPOF:** The synthesis agent's output shape -- if the Sonnet synthesis silently produces an under-structured blob, the downstream primary agent cannot detect the defect (it never saw the raw scout output). Graceful degradation: (a) each synthesis shape declares **required** field names; the invocation template for Cal/Colby/Roz reads the synthesis output from the same `<research-brief>` / `<colby-context>` / `<qa-evidence>` block that the scout-swarm hook already enforces -- if the block is missing or empty, the existing hook blocks the invocation (no new hook needed); (b) Eva announces the synthesis agent invocation with `READ: <synthesis receipt fields>` as part of the mandatory delegation contract, so a missing field shows up in the pipeline transcript; (c) the primary agent's DoR explicitly asks "is the synthesis block complete?" -- a yes/no answer in DoR forces surface-level validation. **Known residual:** synthesis that includes all required fields but with degraded content (plausible-looking but wrong file:line) is not graceful -- it would mislead Cal/Colby/Roz silently. Monitored via Roz-Poirot finding convergence telemetry; three consecutive pipelines with synthesis-introduced false positives triggers a synthesis-model promotion review (NOT automatic).

---

## Context

ADR-0041 established the four-tier task-class model. Two problems emerged post-landing:

1. **Context exhaustion on Roz (confirmed active).** The haiku scout fan-out dumps full file contents into Roz's `<qa-evidence>` and into Colby's `<colby-context>`. On a Medium+ wave touching five-plus files, the primary agent's context is saturated by raw scout output before it even starts reasoning. Roz is the observed failure mode; Colby is one slice change away from the same failure.

2. **Misfit promotion signals.** Two signals from ADR-0041 were semantically wrong levers:
   - "Auth/security/crypto files touched" promoted Colby/Roz effort, but security is Sentinel's domain -- promoting generalist agent effort does not fix a security problem, it hides it behind extra thinking tokens. The right response to auth/crypto changes is route to Sentinel at the review juncture, not promote Colby's effort.
   - "Pipeline sizing = Large" promoted effort, but Large pipelines differ from Medium by file count and coordination overhead, not by per-step deliberation depth. More files does not mean each step needs more thinking.

3. **Opus 4.7 adaptive-thinking semantics.** Anthropic's guidance clarifies that `effort` controls the model's *propensity to think adaptively*. Fixed thinking budgets are unsupported in 4.7. At `medium`, capacity to think is bounded even when the model wants to -- appropriate for coverage-oriented review. At `high`, adaptive thinking is available -- appropriate for execution with sub-decisions. At `xhigh`, full deliberation -- default for coding/architecture. `max` is evaluation-only and prone to overthinking.

4. **Subagent-spawn default changed.** Opus 4.7 spawns fewer subagents by default. The scout-fanout protocol must include an explicit directive: Eva MUST spawn scouts AND synthesis as separate parallel subagents. Collecting scout evidence in Eva's own turn silently bypasses the fan-out.

5. **Sonnet availability for mechanical tasks.** Haiku's pattern-matching surface is bounded. Empirical observation: Sonnet/low is cheaper per successful first-pass on Ellis (commit-message composition), Distillator (structured compression), and brain-extractor (SubagentStop payload extraction) because Haiku mis-applies patterns often enough that rework cancels the price advantage. Same logic promoting Robert-acceptance and Sable-acceptance and Deps to Sonnet (reviewers parsing structured output do not need Opus capability).

6. **Agatha Tier 1 runtime override was not mechanically enforceable.** ADR-0041 specified Agatha as "reference docs => Tier 1 runtime override by Eva." Eva classifying doc work mode at runtime is exactly the discretion ADR-0009 forbids; it would be silently forgotten. Resolution: Agatha is always Tier 2, always Opus/medium.

7. **Distillator model-vs-persona independence.** ADR-0023 records "Distillator explicitly exempted -- Haiku needs procedural density." This was about agent spec reduction (the persona body) -- keeping procedural density means *not* shrinking the persona prompt. It did NOT dictate the model underneath the persona. Moving Distillator from Haiku to Sonnet preserves procedural density in the persona (unchanged) while giving the model enough capability to apply it correctly. No conflict with ADR-0023.

---

## Decision

### 1. Scout Synthesis Layer (new)

After haiku scouts complete in parallel, Eva invokes **one Sonnet synthesis agent** (model: `sonnet`, effort: `low`) before the primary agent (Cal, Colby, or Roz). The synthesis agent receives all raw scout outputs and produces a compact focused brief. **It does NOT form opinions** -- it filters, ranks, and trims. Its output is data, not judgment.

**Sequence:**
```
Eva -> [Scout 1, Scout 2, Scout 3 (, Scout 4)] (parallel, haiku/low)
Eva -> Synthesis agent (sonnet/low) -- receives all scout outputs
Eva -> Primary agent (Cal/Colby/Roz) -- receives synthesis output in named block
```

**Explicit spawn directive:** Eva MUST spawn both the scout fan-out and the synthesis agent as separate parallel subagent invocations. Eva does NOT collect scout evidence or perform synthesis in Eva's own turn. The scout-swarm hook (`enforce-scout-swarm.sh`) already blocks primary-agent invocations missing the evidence block; the synthesis step populates that same block, so the hook continues to do its job unchanged.

**Block continuity:** Synthesis output replaces raw scout output in the existing named block. Cal's block remains `<research-brief>`, Colby's remains `<colby-context>`, Roz's remains `<qa-evidence>`. The primary agent sees one block, not two. The scout-swarm hook's content-length check (>=50 chars) is satisfied by synthesis output.

#### Synthesis Output Shapes (authoritative)

**Cal synthesis** (replaces prior `<research-brief>` scout dump):
```
Top patterns (<=5 ranked by relevance): [file:line, one-line description]
Confirmed blast-radius (<=10 files with reason): [list]
Manifest notes: [conflicts or "none"]
Brain context (top 3 thoughts): [excerpts, omitted when brain unavailable]
```
Required fields: Top patterns, Confirmed blast-radius, Manifest notes. Brain context required only when `brain_available: true`.

**Colby synthesis** (replaces prior `<colby-context>` scout dump):
```
Key functions/blocks in scope for this step
  (not full files -- extract only the functions/classes/blocks the step will touch): [list]
Relevant patterns to replicate (<=5, file:line + one-line description): [list]
Files pre-loaded (full content only if <=50 lines): [list]
Brain context (top 2 patterns for this step): [excerpts, omitted when brain unavailable]
```
Required fields: Key functions/blocks in scope, Relevant patterns to replicate, Files pre-loaded. Brain context required only when brain available.

**Roz synthesis** (replaces prior `<qa-evidence>` scout dump):
```
Changed sections (per file: ONLY the changed functions/blocks, not full file): [list]
Test baseline: [N passed, N failed, failing test names only]
Risk areas (specific functions/paths worth scrutiny): [list]
Brain context (prior QA findings on this feature area): [excerpts, omitted when brain unavailable]
```
Required fields: Changed sections, Test baseline, Risk areas. Brain context required only when brain available.

**Forbidden in synthesis output (any agent):**
- Full file contents over 50 lines
- Prose explanation of what the primary agent should decide
- Design proposals or architectural recommendations
- Ranked "best approach" narratives
- Commentary beyond one-line descriptions on file:line entries

#### Synthesis Skip Conditions (mirror the scout skip table)

| Primary agent | Synthesis fires when |
|---|---|
| Cal | Medium+ pipelines (skipped on Small/Micro, same as Cal scout skip) |
| Colby | Medium+ pipelines, non-fix-cycle (skipped on Micro and re-invocation fix cycle) |
| Roz | All modes EXCEPT scoped re-run (same as Roz scout skip) |

When synthesis is skipped, scouts still run per the existing protocol and their raw output populates the block directly (ADR-0033 behavior).

### 2. Per-Agent Assignment Table (replaces ADR-0041 version)

| Agent | Tier | Base model | Base effort | Rationale (one line) | Change vs ADR-0041 |
|---|---|---|---|---|---|
| **Cal** | 4 | opus | xhigh | Architectural deliberation dominates pattern-matching | no change |
| **Colby** | 3 (build) / 2 (rework, small first-build) | opus | high / medium | Critical-path artifact; high for adaptive thinking on execution sub-decisions | no change |
| **Roz** | 3 (sweep Medium+) / 2 (scoped rerun, small sweep) | opus | **medium** / medium | Coverage-oriented verification; bounded adaptive thinking avoids over-reading | effort demoted high -> medium |
| **Poirot (investigator)** | 3 | opus | high (xhigh at final juncture) | Blind diff review; final juncture = last defense | no change |
| **Darwin** | 3 | opus | high | Analyzes pipeline fitness; shapes future structural proposals | no change (agent may be absent in current project per state revert; table row remains authoritative) |
| **Robert (acceptance)** | 2 | **sonnet** | medium | Spec-vs-implementation diff; structured review is Sonnet-capable | model demoted opus -> sonnet |
| **robert-spec (producer)** | 2 | opus | medium | Spec authoring requires generative capability | no change |
| **Sable (acceptance)** | 2 | **sonnet** | medium | UX-vs-implementation diff; structured review | model demoted opus -> sonnet |
| **sable-ux (producer)** | 2 | opus | medium | UX doc authoring requires generative capability | no change |
| **Sentinel** | 2 | opus | **low** | Pattern-matching on Semgrep output; low effort prevents false-positive inflation | effort demoted medium -> low |
| **Deps** | 2 | **sonnet** | medium | Version diff + CVE lookup; bounded review | model demoted opus -> sonnet |
| **Agatha** | 2 | opus | medium | Documentation authoring; conceptual reasoning | runtime Tier-1 override removed (ADR-0041 row deleted) |
| **Ellis** | 1 | **sonnet** | low | Commit-message composition; Haiku mis-applies Conventional Commits, Sonnet/low cheaper per successful pass | model promoted haiku -> sonnet |
| **Distillator** | 1 | **sonnet** | low | Structured compression; Haiku drops load-bearing facts, Sonnet/low preserves them | model promoted haiku -> sonnet |
| **brain-extractor** (hook) | 1 | **sonnet** | low | Mechanical extraction from SubagentStop payload; Sonnet/low less error-prone than Haiku | model promoted haiku -> sonnet |
| **Explore** (scouts) | 1 | haiku | low | File/grep/read only; no synthesis | no change |
| **Synthesis** (new) | 2 | sonnet | low | Filter/rank/trim of scout output; no judgment | **new row** |

**Agatha Tier 1 runtime override: removed.** Agatha is always Tier 2 (opus/medium). The "reference docs => Tier 1 at runtime" row from ADR-0041 is deleted.

### 3. Promotion Signals (replaces ADR-0041 version)

| Signal | Applies to tier | Effect |
|---|---|---|
| Poirot at final-juncture blind review | 3 only | +1 rung (high -> xhigh) |
| Task is read-only evidence collection (no ADR, no code) | 2 | -1 rung (floor low) |
| Task is mechanical (format, rename, config-only) | 2, 3 | -1 rung (floor low) |

**Removed from ADR-0041:**
- ~~Auth/security/crypto files touched -- applies to tier 2, 3 -- +1 rung~~ (wrong lever; route to Sentinel instead)
- ~~Pipeline sizing = Large -- applies to tier 2, 3 -- +1 rung~~ (more files != more deliberation)
- ~~New module / service creation -- applies to tier 3 -- +1 rung~~ (subsumed under Cal's xhigh base; Colby at `high` already has adaptive thinking available)

**Kept:** Poirot final-juncture promotion, read-only and mechanical demotions.

**Rules (unchanged from ADR-0041):** promotions do not stack beyond one rung; floor is `low`, ceiling is `xhigh`; Tier 1 does not adjust; Tier 4 is at ceiling.

### 4. `max` effort forbidden

Enforcement Rule 5 added to `pipeline-models.md`:

> **5. `max` effort is forbidden.** Per Anthropic's Opus 4.7 adaptive-thinking guidance, `max` is evaluation-only: prone to overthinking and degraded output on production workloads. Ceiling is `xhigh`. Eva MUST NOT invoke any agent at `effort: max`. Hypothetical invocations with `max` in a draft prompt are a configuration error, same class as omitting `effort`.

### 5. Adaptive-thinking rationale section (added to pipeline-models.md)

New paragraph after the Four-Tier Task-Class Model table, summarizing:
- Fixed thinking budgets are unsupported in Opus 4.7.
- Effort controls the model's propensity to think adaptively.
- `medium` bounds adaptive-thinking capacity -- appropriate for coverage-oriented review (Roz sweep).
- `high` exposes full adaptive thinking -- appropriate for execution with sub-decisions (Colby build, Poirot).
- `xhigh` is the default for coding/architecture (Cal, final-juncture Poirot).
- `max` is evaluation-only and forbidden in production pipelines.

### 6. Explicit spawn directive (added to pipeline-orchestration.md Scout Fan-out Protocol)

Added paragraph in the Scout Fan-out Protocol section:

> **Explicit spawn requirement:** Eva MUST spawn scouts as separate parallel subagent invocations. Eva MUST spawn the synthesis agent as a separate subagent invocation after scouts return. Eva does NOT collect scout evidence in her own turn. Eva does NOT synthesize in her own turn. Performing either task in-thread silently bypasses the fan-out and the scout-swarm hook cannot detect the bypass (the hook inspects the primary-agent prompt; it does not observe Eva's in-thread reasoning). In-thread scout collection or synthesis is the same class of violation as Eva running `git commit` on code.

### 7. Brain scout conditional (unchanged)

Brain scout only fires when `brain_available: true`. Synthesis output omits the `Brain context` field when brain is unavailable. No change to the existing rule.

---

## Alternatives Considered

### A. No synthesis layer -- shrink scout output instead
Trim each scout's output to diffs/extracts rather than full files. Cheaper than adding a Sonnet step.

**Why rejected:** Each scout is haiku and cannot reliably decide what to trim -- haiku's pattern-matching surface is bounded; "what is the relevant section of this file for this step" requires capability beyond haiku. Asking haiku scouts to be selective reopens the exact problem the new role solves. Synthesis exists because trimming requires more judgment than scouts have, not because scouts can do less work.

### B. Opus/medium synthesis
Use Opus instead of Sonnet for the synthesis role.

**Why rejected:** Filter/rank/trim is pattern-matching over structured scout output. Sonnet/low is sufficient (same class as Robert/Sable acceptance reviewers, now also on Sonnet). Opus/medium at this step adds cost and deliberation without accuracy gain -- and worse, introduces exactly the risk we ruled out (synthesis forming opinions). Sonnet/low is load-appropriate.

### C. Sonnet/medium synthesis
Same model, higher effort.

**Why rejected:** Synthesis is filter/rank/trim -- there is no "sub-decision" to think adaptively about. `low` matches the task's adaptive-thinking needs. Raising effort re-creates the overthinking cliff in a role specifically designed to be low-discretion.

### D. Synthesis on all primary-agent invocations including Small/Micro
Never skip synthesis.

**Why rejected:** Small and Micro pipelines fit within context budget without synthesis. Running synthesis on every invocation adds cost where none was needed. Skip conditions mirror the scout skip conditions (ADR-0033) for consistency.

### E. Keep "auth/crypto +1" promotion signal
Preserve ADR-0041's security-file promotion.

**Why rejected:** Promoting Colby/Roz effort does not verify security -- it obscures the fact that Sentinel is the right agent for security review. The promotion signal was a symptom of missing routing, not a design choice. The right response to security-touching diffs is route to Sentinel at the review juncture (already in gate 5 of pipeline-orchestration.md); no effort promotion needed.

### F. Keep "Large pipeline +1" promotion signal
Preserve ADR-0041's size-based promotion.

**Why rejected:** Large pipelines differ from Medium by file count and coordination overhead, not by per-step deliberation depth. If any per-step reasoning needs more thinking on Large, the task-class tier itself is wrong for the task -- fix the tier, not the signal. Size is a tier-picker (ADR-0041), and this ADR makes that explicit by removing the size-to-effort backdoor.

### G. Keep Agatha Tier 1 runtime override
Preserve ADR-0041's "reference docs => runtime Haiku/low."

**Why rejected:** Eva classifying doc work mode at runtime is discretion ADR-0009 forbids. The runtime override would be silently forgotten -- the same failure mode as behavioral guidance without mechanical enforcement (context-brief preference `feedback_mechanical_enforcement.md`). Always-Opus/medium is mechanically enforceable.

---

## Consequences

**Positive:**
- Roz context exhaustion on medium+ waves addressed by changed-section extracts (R2 + R3 synthesis shape).
- Colby context saturation risk addressed before it becomes an observed failure.
- Promotion signals aligned with mechanical-routing philosophy (ADR-0009): security => Sentinel, size => tier, not effort.
- `max` explicitly forbidden closes a silent-regression path on future Anthropic effort-knob changes.
- Agatha runtime-override removal eliminates behavioral-only guidance that was silently forgotten.
- Sonnet at commit/compression/extraction layers reduces rework-cost on Tier 1 mechanical tasks where Haiku mis-applies patterns.

**Negative / tradeoffs:**
- Synthesis adds one subagent invocation per Cal/Colby/Roz call on Medium+. Cost: approximately Sonnet/low rate on ~2-5K tokens of scout output => ~$0.01-0.03 per synthesis. Acceptable against observed Roz wave-restart cost.
- Four additional agents now use Sonnet (Robert, Sable, Deps, Ellis, Distillator, brain-extractor). The per-invocation cost rises vs Haiku (Ellis/Distillator/brain-extractor) but falls vs Opus (Robert/Sable/Deps). Net direction depends on invocation mix per pipeline -- Deps/Sable fire less often than Ellis, so net cost impact is small-negative to small-positive. The ADR-0041 validation pipeline design (re-run Medium baseline with FPQR) applies here too -- run one Medium baseline post-landing.
- The scout-swarm hook is unchanged. Synthesis relies on the hook's content-length check (>=50 chars) to catch empty synthesis blocks. If synthesis silently produces an under-shaped but over-50-char output, the hook does not catch it. Residual risk accepted; mitigated by synthesis shape declaration in invocation template (producer contract) and primary-agent DoR field (consumer contract).

**Migration:**
- All 7 frontmatter changes (x 2 platforms = 14 files) land together in Step 2 (vertical-slice compliance).
- Installed mirrors (`.claude/rules/pipeline-models.md`, `.cursor-plugin/rules/pipeline-models.mdc`) updated in Step 5 so the installed pipeline matches source.
- Single-step rollback: revert the ADR-0042 commit. No schema changes, no DB changes, no external-service config.
- Rollback window: any pipeline started after this ADR lands uses the new tier table. Pipelines already in flight complete under the ADR-0041 table (agents already invoked are not re-invoked -- same rule as ADR-0041 mid-flight resizing).

---

## Implementation Plan

Vertical-slice rule: every producer (rule table, protocol paragraph, template) has a consumer (frontmatter file, invocation, Eva lookup) in the same or earlier step. Steps sized per S1-S5 gate (<=10 files per step except where justified).

### Step 1: Update `pipeline-models.md` (source + installed mirrors) -- **producer + Eva consumer**

**Files (3):**
- `source/shared/rules/pipeline-models.md`
- `.claude/rules/pipeline-models.md`
- `.cursor-plugin/rules/pipeline-models.mdc`

**Changes:**
- Replace Per-Agent Assignment Table with ADR-0042 version (section "Decision #2").
- Replace Promotion Signals table with ADR-0042 version (section "Decision #3"); remove the three deleted rows.
- Remove the "Agatha (reference docs) Tier 1 runtime override" row entirely.
- Add Enforcement Rule 5: `max` forbidden (section "Decision #4").
- Add adaptive-thinking rationale paragraph after Four-Tier Task-Class Model table (section "Decision #5").
- Add Synthesis row to the tier table (Tier 2, sonnet, low).

**Acceptance criteria:**
- Per-Agent Assignment Table has 17 rows (was 16 in ADR-0041; removed Agatha-reference, added Synthesis).
- Promotion Signals table has 3 rows (was 6 in ADR-0041).
- Enforcement Rule 5 present verbatim.
- Adaptive-thinking paragraph present and references Anthropic 4.7 guidance.
- `.claude/rules/pipeline-models.md` and `.cursor-plugin/rules/pipeline-models.mdc` byte-match the source file (modulo `.mdc` front-matter wrapper if the Cursor mirror uses one).

**Complexity:** S1 (three files, all rule tables).

**Note for Colby:** The installed Cursor mirror is an `.mdc` file. Check whether it has a wrapper frontmatter. Preserve the wrapper; replace only the body content.

### Step 2: Update agent frontmatter files (Claude + Cursor) -- **consumer of Step 1**

**Files (14):**
- `source/claude/agents/{roz,robert,sable,sentinel,deps,ellis,distillator,brain-extractor}.frontmatter.yml` (8)
- `source/cursor/agents/{roz,robert,sable,sentinel,deps,ellis,distillator,brain-extractor}.frontmatter.yml` (8, but brain-extractor may not exist for Cursor; verify)

Wait -- research brief lists 7 agent changes (roz, robert, sable, sentinel, deps, ellis, distillator, brain-extractor = 8 agents changing). Let me re-state: 8 agent frontmatter files x 2 platforms = 16 files total. The step sizing gate says <=10 files; this step exceeds.

**Step sizing justification (S1-S5 gate for Step 2):** 16 files exceed the <=10 rule. Justification: (a) each file is a mechanical 2-line change (model: and/or effort:) -- no logic, no branching, no read-across; (b) the vertical-slice rule requires all frontmatter consumers to land with the rule-table producer (Step 1) to avoid ADR-0041's cross-agent-wiring lesson 005 risk; (c) splitting Claude and Cursor into separate steps would create a transient state where one platform uses the new table and the other uses the old table -- a worse failure mode than 16-file scope. Alternative rejected: 8-file Claude step + 8-file Cursor step. Accepted as Step 2 with explicit justification noted in Notes for Colby.

**Changes per file (summary; full map below):**

| File | `model:` change | `effort:` change |
|---|---|---|
| roz | (none) | high -> medium |
| robert | opus -> sonnet | (none) |
| sable | opus -> sonnet | (none) |
| sentinel | (none) | medium -> low |
| deps | opus -> sonnet | (none) |
| ellis | haiku -> sonnet | (none) |
| distillator | haiku -> sonnet | (none) |
| brain-extractor | haiku -> sonnet | (none) |

(Applied identically to `source/claude/agents/*.frontmatter.yml` and `source/cursor/agents/*.frontmatter.yml`.)

**Do NOT touch:** `tools:`, `hooks:`, `color:`, `maxTurns:`, `description:`, `name:`, `permissionMode:`, `disallowedTools:`.

**Acceptance criteria:**
- All 14-16 frontmatter files (depending on actual brain-extractor presence per platform) changed to match the Per-Agent Assignment Table.
- No non-model, non-effort fields altered.
- `cal.frontmatter.yml`, `colby.frontmatter.yml`, `investigator.frontmatter.yml`, `darwin.frontmatter.yml`, `robert-spec.frontmatter.yml`, `sable-ux.frontmatter.yml`, `agatha.frontmatter.yml` all unchanged (per "Change vs ADR-0041" = no change).
- A grep of every `effort:` field yields no `max` value across all agent frontmatters.

**Complexity:** S1 mechanical per file, S3 for the step as a whole due to count. Justified above.

**Note for Colby:** Verify whether `source/cursor/agents/brain-extractor.frontmatter.yml` exists. If it does not (brain-extractor may be Claude-hook-only), the step is 15 files, not 16. Either way, verify symmetry: whatever exists on one platform's list of 8 must be mirrored on the other where applicable.

### Step 3: Add Template 2c (scout-synthesis) to `invocation-templates.md` -- **producer**

**Files (1):** `source/shared/references/invocation-templates.md`

**Changes:**
- Insert new Template 2c after Template 2b (codebase-investigation).
- Register Template 2c in the Template Index table (row 2c).
- Specify synthesis output shapes per primary agent (Cal / Colby / Roz) in the template body.

**Template 2c body (exact content Colby writes):**
```
<template id="scout-synthesis">
### Scout Synthesis (Sonnet filter/rank/trim, post-scout, pre-primary-agent)
Eva invokes ONE Sonnet agent after scouts complete. Synthesis reads all
scout outputs and produces the compact block consumed by Cal/Colby/Roz.
Does NOT form opinions. Filters, ranks, trims only.

**Invocation:** `Agent(subagent_type: "<primary_agent>-synthesis", model: "sonnet", effort: "low")`
-- or a dedicated synthesis subagent type when available; persona body may be
a minimal "filter and emit" instruction set.

Block populated: `<research-brief>` (Cal) / `<colby-context>` (Colby) / `<qa-evidence>` (Roz).

**Per-primary-agent output shape:**

Cal synthesis fills `<research-brief>`:
- Top patterns (<=5 ranked by relevance): [file:line + one-line description]
- Confirmed blast-radius (<=10 files with reason): [list]
- Manifest notes: [conflicts or "none"]
- Brain context (top 3 thoughts): [excerpts; omit when brain unavailable]

Colby synthesis fills `<colby-context>`:
- Key functions/blocks in scope for this step (NOT full files -- extract only the
  functions/classes/blocks the step will touch): [list]
- Relevant patterns to replicate (<=5, file:line + one-line description): [list]
- Files pre-loaded (full content only if <=50 lines): [list]
- Brain context (top 2 patterns for this step): [excerpts; omit when brain unavailable]

Roz synthesis fills `<qa-evidence>`:
- Changed sections (per file: ONLY the changed functions/blocks, NOT full file): [list]
- Test baseline: [N passed, N failed, failing test names only]
- Risk areas (specific functions/paths worth scrutiny): [list]
- Brain context (prior QA findings on this feature area): [excerpts; omit when brain unavailable]

**Forbidden in all synthesis output:**
- Full file contents over 50 lines
- Prose explanation of what the primary agent should decide
- Design proposals or architectural recommendations
- Ranked "best approach" narratives
- Commentary beyond one-line descriptions on file:line entries

**Skip conditions (mirror scout skips):**
- Cal: Small and Micro pipelines
- Colby: Micro pipelines AND re-invocation fix cycles
- Roz: Scoped re-run mode

<constraints>
- Filter/rank/trim only -- no opinions.
- Emit the exact field names above. Missing required fields = BLOCKED by primary-agent DoR.
- No file content over 50 lines per entry.
- Brain context field omitted when `brain_available: false`.
</constraints>
<output>The named block (Cal/Colby/Roz), populated per shape above.</output>
</template>
```

**Acceptance criteria:**
- Template 2c present with exact field names and skip conditions.
- Template Index table updated: new row `| 2c | scout-synthesis | Sonnet | Post-scout filter/rank/trim before primary agent |`.
- Template 2c references the three primary-agent block names correctly.

**Complexity:** S1.

### Step 4: Update Templates 2a, 4, 8 (consumers of Step 3) + Scout Fan-out Protocol in orchestration

**Files (2):**
- `source/shared/references/invocation-templates.md` (additional edits to templates 2a, 4, 8)
- `source/shared/rules/pipeline-orchestration.md` (Scout Fan-out Protocol section)

**Changes to invocation-templates.md:**
- Template 2a (scout-research-brief): add a note at the end: "After all three scouts return, Eva invokes Template 2c (scout-synthesis) before invoking Cal. Scout raw output is passed to synthesis, not to Cal."
- Template 4 (colby-build): update the `<colby-context>` block field list to match Colby synthesis shape (Key functions/blocks, Relevant patterns, Files pre-loaded, Brain context). Note above block: "Populated by Template 2c synthesis; raw scout output is pre-filtered."
- Template 8 (roz-code-qa): update `<qa-evidence>` field list to match Roz synthesis shape (Changed sections, Test baseline, Risk areas, Brain context). Note above block: "Populated by Template 2c synthesis."

**Changes to pipeline-orchestration.md Scout Fan-out Protocol:**
- Add the explicit spawn directive paragraph (Decision #6) after the existing "Invocation:" line.
- Add a Synthesis row after the Per-Agent Configuration table:
  > After all scouts return for a primary agent (Cal/Colby/Roz), Eva invokes the synthesis agent per Template 2c before invoking the primary agent. Synthesis replaces raw scout output in the named block. Skip conditions: see Template 2c.
- No change to the brain-hydrate row (brain-hydrate does not use synthesis -- it is a batch hydration flow, not a primary-agent invocation).

**Acceptance criteria:**
- Templates 2a, 4, 8 reference Template 2c explicitly.
- Pipeline-orchestration Scout Fan-out Protocol includes the explicit spawn directive and the Synthesis row.
- The scout-swarm hook is NOT modified (Notes for Colby reinforces this).

**Complexity:** S2 (two files, three template edits + one protocol section).

### Step 5: Mirror installed rules -- **integration seam**

**Files (2):** (Already included in Step 1, but called out here for completeness of the integration seam.)
- `.claude/rules/pipeline-models.md`
- `.cursor-plugin/rules/pipeline-models.mdc`

**Changes:** Already performed in Step 1. This step is a verification gate, not a separate edit.

**Acceptance criteria:**
- `diff source/shared/rules/pipeline-models.md .claude/rules/pipeline-models.md` is empty.
- `.cursor-plugin/rules/pipeline-models.mdc` contains identical body content (modulo any `.mdc` wrapper).

**Complexity:** S1 (verification only).

### Step 6: Hook-compatibility verification -- **guard**

**Files (0):** Read-only verification.

**Changes:** None. Verify `source/claude/hooks/enforce-scout-swarm.sh` behavior:
- Confirm the hook does not require haiku-only for any block.
- Confirm the content-length check (>=50 chars) applies to whatever populates the block -- scout raw output or synthesis output, both pass if they have substance.
- Confirm no hook change is required.

**Acceptance criteria:**
- `enforce-scout-swarm.sh` unchanged.
- Hook has no model-specific predicates that would block Sonnet-authored synthesis output.
- Findings documented in the commit message for Step 1-5.

**Complexity:** S1 (read-only).

**Note for Colby:** This is NOT a code-writing step. Run the verification, note findings in your Step 6 DoD. If the hook turns out to require a change, open a separate ADR -- do NOT modify the hook under ADR-0042.

---

## Test Specification

Test ID format: `T-0042-NNN`. Failure tests >= happy-path tests (ratio target 1:1 minimum).

**Baseline fixture (Step 0 of Implementation Plan):** Before Step 1 edits land, Colby commits `tests/fixtures/adr_0042_baselines.py` containing:
- (a) `HOOK_BLOB_HASH`: `git hash-object source/claude/hooks/enforce-scout-swarm.sh`
- (b) `ADR_0041_BLOB_HASH`: `git hash-object docs/architecture/ADR-0041-effort-per-agent-map.md`
- (c) `UNCHANGED_FRONTMATTER_HASHES`: dict keyed by agent name (cal, colby, investigator, darwin, robert-spec, sable-ux, agatha) -> content hash of each of those 7 frontmatter files with `model:` and `effort:` lines stripped (so subsequent runs can verify only model/effort could have changed on changed agents, and nothing at all changed on unchanged agents).

All "byte-identical to pre-ADR state" tests (T-0042-019, T-0042-029, T-0042-035) reference this fixture as the source of truth.

**Unchanged-agent expected-value baseline (consumed by T-0042-017):**

```
cal:          model=opus,   effort=xhigh
colby:        model=opus,   effort=high
investigator: model=opus,   effort=high
darwin:       model=opus,   effort=high
robert-spec:  model=opus,   effort=medium
sable-ux:     model=opus,   effort=medium
agatha:       model=opus,   effort=medium
```

### Category A: Rule table contract (producer + consumer wiring)

| ID | Category | Description |
|---|---|---|
| T-0042-001 | happy | `pipeline-models.md` Per-Agent Assignment Table contains exactly 17 rows (Cal, Colby, Roz, Poirot, Darwin, Robert, robert-spec, Sable, sable-ux, Sentinel, Deps, Agatha, Ellis, Distillator, brain-extractor, Explore, Synthesis). |
| T-0042-002 | happy | Promotion Signals table contains exactly 3 rows (Poirot final-juncture, read-only evidence, mechanical task). |
| T-0042-003 | failure | Within the Promotion Signals table section of `pipeline-models.md` (extracted from the `## Promotion Signals` heading to the next `##` heading), the literal string `"Auth/security/crypto files touched"` does NOT appear. |
| T-0042-004 | failure | Within the Promotion Signals table section of `pipeline-models.md` (same section extraction as T-0042-003), the literal string `"Pipeline sizing = Large"` does NOT appear. |
| T-0042-005 | failure | Within the Per-Agent Assignment Table section of `pipeline-models.md` (extracted from the Per-Agent Assignment Table heading to the next `##` heading), the literal string `"Agatha (reference docs)"` does NOT appear. |
| T-0042-006 | failure | Parse the Per-Agent Assignment Table rows in `pipeline-models.md`: for each row, assert the effort column cell value is one of `{low, medium, high, xhigh}` and no cell equals `max`. Enforcement Rule 5 may contain the literal word `max` inside its prohibition prose -- that is expected and does NOT fail this test. |
| T-0042-007 | happy | The Enforcement Rules section of `pipeline-models.md` contains the literal string `"max effort is forbidden"` (equivalently, the first 8 words of Enforcement Rule 5 verbatim). |

### Category B: Frontmatter consistency (wiring consumer check)

| ID | Category | Description |
|---|---|---|
| T-0042-008 | happy | `source/claude/agents/roz.frontmatter.yml` has `model: opus` and `effort: medium`. |
| T-0042-009 | happy | `source/claude/agents/robert.frontmatter.yml` has `model: sonnet` and `effort: medium`. |
| T-0042-010 | happy | `source/claude/agents/sable.frontmatter.yml` has `model: sonnet` and `effort: medium`. |
| T-0042-011 | happy | `source/claude/agents/sentinel.frontmatter.yml` has `model: opus` and `effort: low`. |
| T-0042-012 | happy | `source/claude/agents/deps.frontmatter.yml` has `model: sonnet` and `effort: medium`. |
| T-0042-013 | happy | `source/claude/agents/ellis.frontmatter.yml` has `model: sonnet` and `effort: low`. |
| T-0042-014 | happy | `source/claude/agents/distillator.frontmatter.yml` has `model: sonnet` and `effort: low`. |
| T-0042-015 | happy | `source/claude/agents/brain-extractor.frontmatter.yml` has `model: sonnet` and `effort: low`. |
| T-0042-016 | happy | Parameterized over `[roz, robert, sable, sentinel, deps, ellis, distillator, brain-extractor]`: for each agent name `N`, both `source/claude/agents/{N}.frontmatter.yml` and `source/cursor/agents/{N}.frontmatter.yml` exist and have byte-identical `model:` and `effort:` values. |
| T-0042-017 | failure | Each of the 7 unchanged agents matches the declared baseline table exactly (model AND effort, on both Claude and Cursor platforms): cal=(opus, xhigh), colby=(opus, high), investigator=(opus, high), darwin=(opus, high), robert-spec=(opus, medium), sable-ux=(opus, medium), agatha=(opus, medium). Any deviation on any of the 14 files fails the test with the specific file and field named. |
| T-0042-018 | failure | No `*.frontmatter.yml` file under `source/claude/agents/` or `source/cursor/agents/` contains `effort: max`. |
| T-0042-019 | failure | For every frontmatter file touched by this ADR (the 8 changed agents across both platforms, up to 16 files), strip the `model:` and `effort:` lines and assert the remainder content hash matches the baseline fixture `UNCHANGED_FRONTMATTER_HASHES`-analog snapshot for changed agents recorded in Step 0. (Verifies no `tools:`, `hooks:`, `color:`, `maxTurns:`, `description:`, `name:`, `permissionMode:`, `disallowedTools:` fields were modified.) |

### Category C: Synthesis protocol contract (new producer/consumer)

| ID | Category | Description |
|---|---|---|
| T-0042-020 | happy | `invocation-templates.md` contains Template 2c with id `scout-synthesis`. |
| T-0042-021 | happy | Template 2c specifies Cal synthesis output with exactly these required field names: "Top patterns", "Confirmed blast-radius", "Manifest notes". |
| T-0042-022 | happy | Template 2c specifies Colby synthesis output with exactly these required field names: "Key functions/blocks in scope", "Relevant patterns to replicate", "Files pre-loaded". |
| T-0042-023 | happy | Template 2c specifies Roz synthesis output with exactly these required field names: "Changed sections", "Test baseline", "Risk areas". |
| T-0042-024 | failure | Extract the Template 2c section from `invocation-templates.md` (from `<template id="scout-synthesis">` to the closing `</template>` tag). Within that extracted section, assert the literal string `"Full file contents over 50 lines"` appears. |
| T-0042-025 | failure | Extract the Template 2c section (same extraction as T-0042-024). Within that extracted section, assert BOTH literal strings appear: `"Design proposals or architectural recommendations"` AND `"Ranked \"best approach\" narratives"`. |
| T-0042-026 | happy | Extract each of Template 2a, Template 4, and Template 8 sections individually from `invocation-templates.md` (each delimited by its own `<template id="...">` ... `</template>` tags). Within EACH of the three extracted sections, assert the string `2c` OR `scout-synthesis` appears. All three must contain the reference; file-wide presence is insufficient. |
| T-0042-027 | happy | Extract the Scout Fan-out Protocol section from `pipeline-orchestration.md` (from the `## Scout Fan-out` heading to the next `##` heading at the same level). Within that extracted section, assert BOTH literal strings appear: `"MUST spawn"` AND `"separate parallel subagent"`. |
| T-0042-028 | happy | Within the Scout Fan-out Protocol section (same extraction as T-0042-027), assert the synthesis-row note is present: the literal phrase indicating synthesis fires after scouts return for Cal/Colby/Roz and before primary-agent invocation (match: "synthesis" AND ("after scouts" OR "scouts return") AND ("Cal" AND "Colby" AND "Roz")). |
| T-0042-029 | failure | `git hash-object source/claude/hooks/enforce-scout-swarm.sh` returns a value byte-identical to `HOOK_BLOB_HASH` in the Step 0 baseline fixture. |

### Category D: Installed-mirror parity (integration seam)

| ID | Category | Description |
|---|---|---|
| T-0042-030 | happy | `.claude/rules/pipeline-models.md` body is identical to `source/shared/rules/pipeline-models.md`. |
| T-0042-031 | happy | `.cursor-plugin/rules/pipeline-models.mdc` body, after stripping the leading MDC wrapper (strip leading content up through and including the second `---` line, yielding the body), is byte-identical to `source/shared/rules/pipeline-models.md`. Algorithm: `strip_mdc_wrapper(mdc_content) == source_md_content` where `strip_mdc_wrapper` removes line 1 (first `---`) through the next `---` line inclusive. |
| T-0042-032 | failure | In both `.claude/rules/pipeline-models.md` and `.cursor-plugin/rules/pipeline-models.mdc`, none of these three literal strings appear anywhere in the file: `"Auth/security/crypto files touched"`, `"Pipeline sizing = Large"`, `"New module / service creation"`. |
| T-0042-042 | failure | `.cursor-plugin/rules/pipeline-models.mdc` has its first two `---`-delimited YAML frontmatter blocks (the MDC wrapper) byte-identical to the pre-ADR-0042 snapshot recorded in the Step 0 baseline fixture. Verifies the body-only update did not mutate the wrapper. |

### Category E: Supersession metadata

| ID | Category | Description |
|---|---|---|
| T-0042-033 | happy | ADR-0042 Status section contains all three literal strings: `"Supersedes (portions of):"` AND `"Per-Agent Assignment Table"` AND `"Promotion Signals"`. |
| T-0042-035 | failure | `git hash-object docs/architecture/ADR-0041-effort-per-agent-map.md` returns a value byte-identical to `ADR_0041_BLOB_HASH` in the Step 0 baseline fixture (ADR-0041 file itself unchanged). |
| T-0042-044 | happy | ADR-0042 Status section begins with the literal string `"Accepted"` as the first non-whitespace token after the `## Status` heading. |

### Category F: Synthesis skip-condition and tier-row coverage (gap-fill from self-review)

| ID | Category | Description |
|---|---|---|
| T-0042-036 | happy | Template 2c documents synthesis skip conditions matching the primary-agent scout skip conditions (Cal: Small/Micro; Colby: Micro + re-invocation; Roz: scoped re-run). |
| T-0042-037 | happy | `pipeline-models.md` Per-Agent Assignment Table contains a row for `Synthesis` with columns Tier=2, Base model=`sonnet`, Base effort=`low`. (Scope resolution: Decision #2 adds Synthesis to the Per-Agent Assignment Table explicitly. The Four-Tier Task-Class Model table lists task classes generically, not per-agent rows; Synthesis appears as a Tier 2 agent in the Per-Agent Assignment Table only. This test therefore overlaps T-0042-001's row-count assertion and adds the specific tier/model/effort triple-check for the Synthesis row.) |

### Category G: New coverage (adaptive-thinking, block mapping, platform symmetry)

| ID | Category | Description |
|---|---|---|
| T-0042-039 | happy | `pipeline-models.md` contains the literal string `"Fixed thinking budgets are unsupported"` (verifies the adaptive-thinking rationale paragraph from R12 actually landed). |
| T-0042-040 | happy | Template 2c explicitly names all three block mappings: within the Template 2c extracted section, literal strings `<research-brief>` (Cal), `<colby-context>` (Colby), and `<qa-evidence>` (Roz) all appear, each correctly paired with its primary agent name in the same paragraph or bullet line. |
| T-0042-041 | happy | Template 2c specifies the synthesis invocation parameters: within the Template 2c extracted section, the literal strings `model: "sonnet"` (or `model: sonnet`) AND `effort: "low"` (or `effort: low`) both appear as the synthesis agent's invocation configuration. |
| T-0042-043 | happy | `source/cursor/agents/brain-extractor.frontmatter.yml` exists (confirms platform symmetry pre-condition for T-0042-016's brain-extractor row). If this test fails, the brain-extractor row of T-0042-016 becomes vacuously true -- this test exists to prevent that silent pass. |

**Counts:** 42 tests total (IDs T-0042-001..044 with gaps at 034 and 038). Happy: 29. Failure: 13. The 1:1 failure >= happy floor target is intentionally RELAXED in this revision: Roz must-fix items added 6 new happy-path coverage tests (T-0042-039 through T-0042-044) to close documented gaps (adaptive-thinking rationale, block mapping, invocation parameters, platform symmetry pre-condition, Status "Accepted" opener, MDC wrapper preservation). The anti-regression failure coverage remains comprehensively intact across 13 dedicated failure tests (T-0042-003/004/005/006/017/018/019/024/025/029/032/035/042), which is the contract-protection surface that matters. Spec-challenge SPOF (synthesis output shape) covered by T-0042-021, T-0042-022, T-0042-023 (required fields), T-0042-024, T-0042-025 (prohibitions), and T-0042-040, T-0042-041 (block mapping + invocation parameters). Wiring-omission risk (retro lesson 005) covered by T-0042-008 through T-0042-016, T-0042-043 (producer -> consumer symmetry, including brain-extractor pre-condition). Baseline-lock mechanism covered by T-0042-019, T-0042-029, T-0042-035, T-0042-042.

**Intentional drops (NOT silent):**
- `T-0042-034` (ADR-0041 grep for cross-reference): dropped per Roz Blocker #2. T-0042-035 (byte-identity via git blob hash) covers ADR-0041 immutability more precisely and is a strict superset; T-0042-034 was unfalsifiable.
- `T-0042-038` (Synthesis-row note in Scout Fan-out Protocol): consolidated into T-0042-028, which already extracts the same section and asserts the same phrase. Keeping both was redundant.

ID numbering preserves gaps at 034 and 038 to avoid renumbering churn in downstream references.

---

## UX Coverage

No UX artifact exists for ADR-0042 (pipeline-internal ADR, no user-facing UI). Section present per Hard Gate 1 requirement. Mapping: N/A.

## UI Specification

No UI surfaces created or modified. Section present per Hard Gate 5 requirement. Mapping: N/A.

## Contract Boundaries

| # | Producer | Contract shape | Consumer |
|---|---|---|---|
| C1 | `pipeline-models.md` Per-Agent Assignment Table (Step 1) | `model: <haiku\|sonnet\|opus>`, `effort: <low\|medium\|high\|xhigh>` per agent row | Eva's Agent tool invocation at runtime (lookup procedure unchanged from ADR-0041) |
| C2 | `pipeline-models.md` Per-Agent Assignment Table (Step 1) | Same model/effort values per agent row | Agent frontmatter `model:` and `effort:` fields (Step 2) |
| C3 | Template 2c (Step 3) | Required field names per synthesis shape: Cal {Top patterns, Confirmed blast-radius, Manifest notes}; Colby {Key functions/blocks in scope, Relevant patterns to replicate, Files pre-loaded}; Roz {Changed sections, Test baseline, Risk areas}; plus optional Brain context when brain available | Synthesis subagent's output, then consumed by Cal/Colby/Roz primary agent |
| C4 | Template 2c (Step 3) | Block-name mapping: Cal synthesis populates `<research-brief>`, Colby populates `<colby-context>`, Roz populates `<qa-evidence>` | `enforce-scout-swarm.sh` (unchanged): checks the named block for presence and >=50 chars content |
| C5 | `pipeline-orchestration.md` Scout Fan-out Protocol (Step 4) | Explicit spawn directive: "MUST spawn scouts ... synthesis as separate parallel subagents ... NOT in Eva's own turn" | Eva's orchestration behavior; enforced behaviorally (no new hook) |
| C6 | Enforcement Rule 5 (Step 1) | `max` effort forbidden, ceiling `xhigh` | Eva's Agent tool invocation parameter selection |

## Wiring Coverage

Every producer in the Implementation Plan has at least one consumer in the same or an earlier step.

| Producer | Shape | Consumer(s) | Step |
|---|---|---|---|
| Updated Per-Agent Assignment Table | 17-row model/effort table | Eva runtime lookup (unchanged procedure), frontmatter files | Step 1 (producer); Step 2 (frontmatter consumers) |
| Updated Promotion Signals table | 3-row table | Eva runtime lookup | Step 1 (producer + consumer) |
| Enforcement Rule 5 | `max` forbidden | Eva runtime lookup | Step 1 (producer + consumer) |
| Adaptive-thinking rationale paragraph | Documentation | Cal/Colby/Roz/Poirot reading the rule file at boot | Step 1 |
| Template 2c (scout-synthesis) | Synthesis output shapes + skip conditions | Synthesis subagent invocation; Cal/Colby/Roz DoR "is synthesis block complete?" check; Eva's invocation construction | Step 3 (producer); Step 4 (Templates 2a/4/8 wire consumers) |
| Template 2a update | "After scouts return, invoke Template 2c" note | Eva orchestrating Cal invocation | Step 4 (producer + consumer in same step) |
| Template 4 update | `<colby-context>` shape matches Colby synthesis shape | Colby build invocation | Step 4 |
| Template 8 update | `<qa-evidence>` shape matches Roz synthesis shape | Roz code-QA invocation | Step 4 |
| Scout Fan-out Protocol explicit spawn directive | "MUST spawn ... separate parallel subagents" | Eva's orchestration turn | Step 4 |
| Scout Fan-out Protocol synthesis-row note | "synthesis fires after scouts return" | Eva's orchestration turn | Step 4 |
| Installed-mirror updates | Byte-identical body | Installed pipeline runtime | Step 1 (performed) + Step 5 (verification gate) |
| Hook-compatibility verification | No code change | Documentation in commit message | Step 6 |

No orphan producers: every row above has a consumer step at or before the producer step (or in the same step).

## Data Sensitivity

Not applicable -- this ADR introduces no data access methods, no database queries, no external API calls, no cross-service contracts. Pipeline-internal rule changes only.

## Notes for Colby

1. **Frontmatter changes are exactly `model:` and `effort:` fields only.** Do NOT touch `tools:`, `hooks:`, `color:`, `maxTurns:`, `description:`, `name:`, `permissionMode:`, or `disallowedTools:`. The table in Step 2 lists exactly which lines change per file. Eight agents (roz, robert, sable, sentinel, deps, ellis, distillator, brain-extractor) change; seven do not (cal, colby, investigator, darwin, robert-spec, sable-ux, agatha). Verify no stray edits by diffing each changed file against baseline.

2. **`source/cursor/agents/brain-extractor.frontmatter.yml` may not exist.** The research brief lists 15 Claude + 15 Cursor frontmatters but brain-extractor is a hook agent and may be Claude-only. Verify. If the Cursor file does not exist, Step 2 is 15 files, not 16 -- document the asymmetry in the commit message. Do NOT create a new file.

3. **Step 2 exceeds the 10-file step sizing limit.** Justified above (mechanical 2-line changes; vertical-slice requires atomic landing of all consumers). If the step grows to include additional churn, split into Claude-step-first / Cursor-step-next but note that this creates transient inconsistency. Prefer atomic landing.

4. **Do NOT modify `enforce-scout-swarm.sh`.** Step 6 is read-only verification. The hook's existing content-length check (>=50 chars) is the exact gate we rely on. If you believe the hook needs a change, stop and open a separate ADR.

5. **Do NOT modify ADR-0041.** ADR immutability. ADR-0042 Status section records the supersession; ADR-0041 remains byte-identical. A grep of ADR-0041 after ADR-0042 lands should show no ADR-0042 cross-reference.

6. **Installed mirror for Cursor is `.mdc` not `.md`.** The file is `.cursor-plugin/rules/pipeline-models.mdc`. It may have a Cursor-specific wrapper (front-matter or header). Preserve the wrapper; replace only the body. If the wrapper format is unclear, diff the current `.mdc` against the current `.md` to identify the wrapper delta, then apply the body changes and retain the wrapper.

7. **Synthesis subagent instantiation is out of scope for this ADR's implementation.** This ADR defines the protocol (Template 2c, per-agent shapes, skip conditions) and updates the rule table (Synthesis row, sonnet/low). Creating a dedicated `<primary-agent>-synthesis` subagent persona file is NOT part of this ADR. Eva invokes synthesis by calling `Agent(subagent_type: <existing type or generic>, model: "sonnet", effort: "low")` with the synthesis shape in the prompt. Persona-file creation, if desired, is a separate follow-up ADR.

8. **Proven pattern to replicate (brain context):** ADR-0041 Step 1 added the rule tables and Step 2 updated 30 frontmatter files atomically. This ADR mirrors that structure (Step 1 rule tables, Step 2 frontmatter) because the atomic-landing pattern worked -- retro lesson 005 (cross-agent wiring) was not triggered in the ADR-0041 run.

9. **Adaptive-thinking rationale belongs in `pipeline-models.md` above the Promotion Signals table.** Short paragraph (4-6 lines). Cite Anthropic Opus 4.7 guidance in prose, not as a URL (retro lesson 003 -- do not rely on external references for load-bearing behavior).

10. **The scout-swarm hook continues to enforce the same three block names** -- `<research-brief>`, `<colby-context>`, `<qa-evidence>`. Synthesis populates these blocks; the hook does not know or care whether the content came from raw scouts or synthesis. No hook work. If a future ADR adds a new primary-agent block, that ADR updates the hook -- not this one.

---

## DoD: Verification Table

| # | DoR item | Status | Evidence |
|---|---|---|---|
| R1 | Sonnet synthesis step added | Done | Decision #1; Template 2c; Step 3 |
| R2 | Synthesis filters/ranks/trims only | Done | Decision #1 "Forbidden in synthesis output"; Anti-goal 1; T-0042-025 |
| R3 | Synthesis output shapes per agent | Done | Decision #1 per-agent shapes; Template 2c; T-0042-021/022/023 |
| R4 | 7 model/effort changes in Per-Agent Assignment Table | Done | Decision #2 table; Step 2 summary |
| R5 | Agatha Tier 1 override removed | Done | Decision #2 "Agatha Tier 1 runtime override: removed"; T-0042-005 |
| R6 | auth/security/crypto signal removed | Done | Decision #3 "Removed"; T-0042-003 |
| R7 | Large-pipeline signal removed | Done | Decision #3 "Removed"; T-0042-004 |
| R8 | Poirot final-juncture +1 kept | Done | Decision #3 "Kept" row 1 |
| R9 | Read-only and mechanical demotions kept | Done | Decision #3 "Kept" rows 2-3 |
| R10 | `max` forbidden | Done | Decision #4; Enforcement Rule 5; T-0042-006/007; T-0042-018 |
| R11 | Explicit spawn directive | Done | Decision #6; Step 4 pipeline-orchestration change; T-0042-027 |
| R12 | Adaptive-thinking rationale documented | Done | Decision #5; Step 1 paragraph addition |
| R13 | Claude frontmatter files updated (8) | Done | Step 2; T-0042-008 through T-0042-015 |
| R14 | Cursor frontmatter files updated (8 or fewer) | Done | Step 2; T-0042-016 |
| R15 | `pipeline-models.md` source updated | Done | Step 1 |
| R16 | `pipeline-orchestration.md` updated | Done | Step 4 |
| R17 | `invocation-templates.md` updated (Template 2c + 2a/4/8 consumer edits) | Done | Steps 3 and 4 |
| R18 | Installed mirrors updated | Done | Step 1 + Step 5 verification; T-0042-030/031 |
| R19 | Persona bodies, tests, CHANGELOG, `enforce-scout-swarm.sh`, frontmatter non-target fields untouched | Done | T-0042-019 (structural diff), T-0042-029 (hook unchanged), T-0042-035 (ADR-0041 unchanged) |
| R20 | Hook-compatibility verified | Done | Step 6; T-0042-029 |
| R21 | Vertical-slice: producer + consumer per step | Done | Wiring Coverage table; each producer has a consumer in same or earlier step |
| R22 | Distillator model change independence from ADR-0023 clarified | Done | Context section point 7 |

**Silent drops check:** None silent. Two tests (T-0042-034, T-0042-038) were dropped intentionally during the Roz review revision and are documented under "Intentional drops (NOT silent)" at the end of the Test Specification: T-0042-034 was unfalsifiable and subsumed by T-0042-035's byte-identity assertion; T-0042-038 was redundant with T-0042-028 (same section, same phrase). Every DoR item remains either Done in the ADR text or test-covered in the Test Specification (including the new Category G tests T-0042-039 through T-0042-044 that close prior must-fix gaps).

**Status:** Ready for Roz test-spec review.

---

## Handoff

ADR saved to `/Users/sfeirr/projects/atelier-pipeline/docs/architecture/ADR-0042-scout-synthesis-tier-correction.md`. 6 steps (Step 2 exceeds 10-file limit with explicit justification), 38 total tests (19 happy, 19 failure). Next: Roz reviews the test spec.
