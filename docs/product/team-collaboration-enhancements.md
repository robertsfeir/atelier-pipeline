# Team Collaboration Enhancements: Context Brief Capture + Structured Handoff

**Author:** Robert Sfeir (CPO)
**Date:** 2026-03-23
**Status:** Draft
**Depends on:** [Atelier Brain Feature Spec](../brain/atelier-brain-feature-spec.md)

---

## Feature 1: Context Brief Brain Capture

### Problem

When a user tells their session "no modals, keep it simple," Eva writes that preference to `context-brief.md`. This works within a single session -- every subagent reads the file. But `context-brief.md` is reset at the start of each new feature pipeline. If Bob picks up the same feature the next day, his agents have no access to Alice's preferences and mid-course corrections.

The brain already captures agent *decisions* (Cal's architectural choices, Roz's QA findings). It does not capture the *user intent* that drove those decisions. The gap: a teammate's agents can find "Cal chose REST over GraphQL" but not "the user said keep it simple, no over-engineering" -- the directive that shaped Cal's choice.

### Solution

Eva captures user-facing entries from `context-brief.md` into the brain using the existing dual-write pattern (same as retro lessons). Specifically:

1. **When Eva appends to context-brief.md** (user preference, correction, rejected alternative, or cross-agent resolution), she also calls `agent_capture` if brain is available:
   - `thought_type: 'preference'` for user preferences and constraints ("no modals," "keep it simple")
   - `thought_type: 'correction'` for mid-course corrections ("actually make that a dropdown")
   - `thought_type: 'rejection'` for rejected alternatives with reasoning
   - `source_agent: 'eva'`
   - `source_phase`: current pipeline phase
   - Tags: feature name, `context-brief`

2. **When any agent calls `agent_search` at session start**, these preference/correction thoughts surface alongside architectural decisions and lessons. Bob's agents see Alice's "no modals" directive when they search for context on the same feature.

3. **No brain, no change.** Without brain, Eva writes to `context-brief.md` exactly as today. The brain capture is additive.

### Acceptance Criteria

- AC-1: When Eva appends a user preference to `context-brief.md` and brain is available, Eva also calls `agent_capture` with `thought_type: 'preference'` containing the preference text, feature scope, and current phase.
- AC-2: When Eva appends a mid-course correction to `context-brief.md` and brain is available, Eva also calls `agent_capture` with `thought_type: 'correction'`.
- AC-3: When Eva appends a rejected alternative to `context-brief.md` and brain is available, Eva also calls `agent_capture` with `thought_type: 'rejection'`.
- AC-4: When Bob starts a new session on the same feature and brain is available, `agent_search` for the feature area returns Alice's captured preferences and corrections in the results.
- AC-5: When brain is unavailable, Eva writes to `context-brief.md` with zero changes to current behavior. No errors, no warnings, no degradation.
- AC-6: Captured context-brief thoughts include the feature scope tag so they surface for teammates working on the same feature but not for unrelated features.

---

## Feature 2: Structured Handoff Brief

### Problem

Alice builds ADR steps 1-3 and closes her session. Bob picks up steps 4-6. Bob's agents will search the brain and get individual thoughts from Alice's session -- a decision here, a correction there, an insight somewhere else. But there is no synthesis. No "here's where I left off, here's what surprised me, here's what I learned that isn't in the ADR."

Implementation insights are scattered across individual thoughts. Bob's agents must piece together Alice's session from fragments. The signal-to-noise ratio is low, and the most valuable context -- what Alice *would have told Bob* in a hallway conversation -- is never captured.

### Solution

At pipeline end (or when the user says "hand off" / "someone else is picking this up"), Eva produces a structured handoff brief and captures it as a single brain thought.

1. **Trigger:** Eva generates the handoff brief in two cases:
   - Pipeline reaches the Final Report phase (automatic)
   - User says "hand off," "someone else is picking this up," or similar mid-pipeline (explicit)

2. **Content:** Eva synthesizes from the session's context-brief, pipeline-state, and any brain thoughts she captured during the run:
   - **Completed work:** which ADR steps (or phases) were finished
   - **Unfinished work:** what remains, including any partially-started steps
   - **Key decisions:** the 3-5 most consequential choices made this session, with reasoning
   - **Surprises:** anything that deviated from the plan -- unexpected complexity, changed requirements, discovered constraints
   - **User corrections:** preferences and mid-course changes that shaped the work (references Feature 1 captures)
   - **Warnings:** known risks, fragile areas, or "watch out for X" notes for the next developer

3. **Capture:** Eva calls `agent_capture` with:
   - `thought_type: 'handoff'`
   - `source_agent: 'eva'`
   - `source_phase: 'handoff'`
   - Tags: feature name, ADR reference, `handoff`
   - Content: the structured brief as a single thought

4. **Retrieval:** When Bob starts a session on the same feature, `agent_search` returns the handoff brief as a high-relevance result. The `handoff` thought type should have high default importance (same tier as decisions) so it ranks above scattered tactical findings.

5. **No brain, no handoff thought.** The handoff brief is brain-only. Without brain, Eva's Final Report (which already exists) serves as the session summary. The handoff brief adds teammate-oriented synthesis that the Final Report doesn't provide.

### Acceptance Criteria

- AC-1: When a pipeline reaches Final Report and brain is available, Eva generates a structured handoff brief containing completed work, unfinished work, key decisions, surprises, user corrections, and warnings.
- AC-2: Eva captures the handoff brief via `agent_capture` with `thought_type: 'handoff'`, `source_agent: 'eva'`, `source_phase: 'handoff'`, and feature scope tags.
- AC-3: When the user says "hand off" or equivalent mid-pipeline, Eva generates the handoff brief from the session's current state and captures it before ending the session.
- AC-4: When Bob starts a new session on the same feature and brain is available, `agent_search` for the feature area returns Alice's handoff brief.
- AC-5: The `handoff` thought type has high default importance in the thought_type_config table (no expiry, same tier as `decision`).
- AC-6: When brain is unavailable, pipeline end behavior is unchanged -- Final Report renders normally, no errors from missing handoff capture.
- AC-7: The handoff brief references the ADR and lists ADR step numbers for completed and unfinished work, so the next developer can orient by step.

---

## Shared Edge Cases

**Brain becomes unavailable mid-pipeline.** Eva checks brain availability at pipeline start. If brain goes down mid-session:
- Feature 1: Eva continues writing to `context-brief.md`. Brain captures silently fail. No pipeline disruption. Thoughts captured before the outage remain in the brain.
- Feature 2: If brain is down at pipeline end, the handoff brief is not captured. The Final Report still renders. Eva logs a warning: "Handoff brief not captured -- brain unavailable."

**Very short sessions.** If a session produces no user corrections and completes zero ADR steps (e.g., user starts pipeline, changes mind, closes session):
- Feature 1: No context-brief entries means no brain captures. No-op.
- Feature 2: Eva skips handoff brief generation. A handoff with no content is noise.

**Multiple handoffs on the same feature.** Alice hands off to Bob, Bob hands off to Carol. Each handoff is a separate thought. `agent_search` returns all of them, ordered by recency. The most recent handoff is the most relevant, but earlier ones provide history. No merging -- each handoff is a point-in-time snapshot.

**Conflicting preferences across handoffs.** Alice says "no modals." Bob says "actually, modals are fine for confirmations." The brain's existing conflict detection (US-3 in the brain spec) handles this: both are `preference` type, the newer one supersedes the older via `atelier_relation`. No new mechanism needed.

**Context-brief reset on new feature.** `context-brief.md` is reset at the start of each new feature pipeline. Brain thoughts from prior features are not affected -- they persist with their feature scope tags and are retrievable via `agent_search` for that feature. The reset is local-file-only.

**User opts out of handoff.** If the user says "no handoff" or "skip handoff," Eva respects it. The handoff brief is not generated or captured. This is an edge case, not a setting -- no configuration needed.
