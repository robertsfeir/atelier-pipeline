<procedure id="extract-capture">

## Phase 2b: Extract & Capture (Sonnet Subagent)

After scouts complete and the completeness check passes, Eva invokes a **Sonnet subagent** to perform all extraction and capture work. Extraction does NOT run on the main thread.

### Invocation

**Note:** This subagent is the intentional exception to the agent-preamble rule that says subagents do not call `agent_capture` directly. Per ADR-0027, extraction is the Sonnet subagent's primary job -- it calls `agent_capture` and `agent_search` directly as its core function.

Eva invokes `Agent(model: "sonnet")` with the collected scout content in a `<hydration-content>` block:

```xml
<task>Extract reasoning and decisions from project artifacts into brain thoughts.
Follow the extraction rules exactly. Call agent_capture for each thought.
Call agent_search (threshold 0.85) before each capture for dedup.
Report progress per source type.</task>

<hydration-content>
  <adrs>[ADR scout output]</adrs>
  <specs>[Specs scout output]</specs>
  <ux-docs>[UX scout output]</ux-docs>
  <pipeline-artifacts>[Pipeline scout output]</pipeline-artifacts>
  <git-history>[Git scout output]</git-history>
</hydration-content>

<read>skills/brain-hydrate/extraction.md</read>

<constraints>
- Extract the WHY, never the WHAT. Synthesize reasoning, never copy content.
- Never capture code, function signatures, SQL schemas, or config snippets.
- Respect write-time conflict detection -- if agent_capture returns conflict, skip.
- Dedup: agent_search at 0.85 before each capture. >0.85 = skip. 0.7-0.85 = new thought + evolves_from relation.
- Create relations via `atelier_relation` per source extraction rules (evolves_from, triggered_by, supports, contradicts).
- User scope constraints: [injected from Phase 1]
</constraints>

<output>Progress report per source type with counts:
  [Source] Captured N decisions, N rejections, N insights. Created N relations. Skipped N (already captured).
Final totals: total captured, total skipped, total relations.</output>
```

**No shell access.** Git history commands are run by the Git scout only. The Sonnet subagent works entirely from the scout-collected content in the `<hydration-content>` block -- no filesystem reads, no shell commands.

**Dry-run mode (Phase 2b):** In dry-run mode, the Sonnet subagent must NOT call `agent_capture`. It may process the hydration content and report what WOULD be captured (counts per source type, estimated thought types), but writes zero thoughts to the brain.

### Failure Handling (SPOF)

If the Sonnet subagent fails mid-run (context exhaustion, MCP timeout, or model error), all thoughts captured so far are preserved (the brain is append-only). Eva detects the subagent failure, reports captured-vs-expected count to the user, and suggests re-running. The incremental re-hydration protocol (dedup via `agent_search`) makes re-running safe -- already-captured thoughts will be skipped automatically.

### Extraction Rules by Source Type

The Sonnet subagent follows these rules for each source type. **Do not capture verbatim text** -- synthesize the reasoning into atomic thoughts.

#### ADRs → decisions, rejections, insights

Read each ADR file. Extract:

1. **Each decision made** → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "sarah"` (architect decisions)
   - `source_phase: "design"`
   - `importance: 0.9` (architectural decisions are high-importance)
   - `thought`: One sentence summarizing the decision and its rationale. Reference the ADR: "ADR-NNNN: [decision summary]. Rationale: [why]."

2. **Each rejected alternative** → `agent_capture` with:
   - `thought_type: "rejection"`
   - `source_agent: "sarah"`
   - `source_phase: "design"`
   - `importance: 0.5`
   - `thought`: "Rejected [alternative] for [feature]. Reason: [why]. See ADR-NNNN."

3. **Spec challenges or risk call-outs** → `agent_capture` with:
   - `thought_type: "insight"`
   - `source_agent: "sarah"`
   - `source_phase: "design"`
   - `importance: 0.6`

4. **Relations**: Create `evolves_from` between decisions in the same ADR that build on each other. Create `contradicts` between a decision and its rejected alternatives (if the rejection was due to direct conflict).

#### Feature Specs → decisions, preferences

Read each spec file. Extract:

1. **Key product decisions** (scope boundaries, what's in/out, deferred items) → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "robert"` (product decisions)
   - `source_phase: "design"`
   - `importance: 0.8`

2. **User-stated preferences or constraints** → `agent_capture` with:
   - `thought_type: "preference"`
   - `source_agent: "robert"`
   - `source_phase: "design"`
   - `importance: 0.9` (user constraints are high-importance)

3. **Explicitly deferred features or open questions** → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "robert"`
   - `source_phase: "design"`
   - `importance: 0.5`
   - `thought`: "Deferred: [what]. Reason: [why]. Revisit when [condition]."

4. **Relations**: Create `triggered_by` from ADR decisions back to the spec decisions that drove them (match by feature name).

#### UX Docs → decisions, preferences

Read each UX doc. Extract:

1. **UX pattern choices** (why this layout, why this interaction model) → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "sable"` (if agent exists) or `"eva"` (fallback)
   - `source_phase: "design"`
   - `importance: 0.7`

2. **Accessibility or usability constraints** → `agent_capture` with:
   - `thought_type: "preference"`
   - `source_agent: "sable"` or `"eva"`
   - `source_phase: "design"`
   - `importance: 0.8`

3. **Relations**: Create `supports` between UX decisions and the spec decisions they implement.

#### Error Patterns → lessons

Read `docs/pipeline/error-patterns.md`. Extract each entry:

1. **Each error pattern** → `agent_capture` with:
   - `thought_type: "lesson"`
   - `source_agent: 'poirot'` (QA-discovered patterns)
   - `source_phase: "qa"`
   - `importance`: Scale by recurrence count: 1-2 occurrences → 0.5, 3-4 → 0.7, 5+ → 0.9
   - `thought`: "[Pattern type]: [description]. Recurred [N] times. Mitigation: [what works]."

#### Context Brief → preferences, corrections

Read `docs/pipeline/context-brief.md` if it exists. Extract:

1. **User corrections** → `agent_capture` with:
   - `thought_type: "correction"`
   - `source_agent: "eva"`
   - `source_phase: "review"`
   - `importance: 0.8`

2. **Stated preferences** → `agent_capture` with:
   - `thought_type: "preference"`
   - `source_agent: "eva"`
   - `source_phase: "review"`
   - `importance: 0.9`

#### Git History → insights, lessons, decisions

Git history arrives pre-collected in the `<git-history>` block from the Git scout. The Sonnet subagent reads from that block only -- no shell access, no `git log` commands.

**Filter for significant commits only.** Skip:
- Merge commits with no body
- Commits with only a subject line and no narrative body
- Automated commits (dependabot, renovate, CI)
- Commits that are purely mechanical (formatting, lint fixes)

For significant commits (those with narrative bodies explaining WHY):

1. **Architecture or design commits** → `agent_capture` with:
   - `thought_type: "decision"`
   - `source_agent: "colby"`
   - `source_phase: "build"`
   - `importance: 0.6`
   - `thought`: Synthesize the reasoning from the commit body, not the diff.

2. **Bug fix commits with root cause explanation** → `agent_capture` with:
   - `thought_type: "lesson"`
   - `source_agent: "colby"`
   - `source_phase: "build"`
   - `importance: 0.6`
   - `thought`: "Bug: [symptom]. Root cause: [cause]. Fix: [approach]. Commit: [short hash]."

3. **Relations**: Create `triggered_by` from fix commits back to the error pattern they address (if matchable).

</procedure>
