# Robert — Product & Spec Alignment

**Round:** Gauntlet Round 6
**Date:** 2026-04-11
**Auditor:** Robert (Product Acceptance Reviewer)
**Mode:** Read-only. ADR-blind. No source modified.
**Scope:** Full product spec coverage — 9 specs in `docs/product/` vs. implementation in `brain/`, `source/`, `skills/`, `.claude-plugin/`, `.cursor-plugin/`.

---

## Summary

The pipeline is substantially aligned with its product specs: brain-hardening, agent-telemetry, deps-agent, dashboard-integration (core pieces), darwin, and cursor-port (structural) are all wired. However, three specs show meaningful drift. (1) **mechanical-brain-writes** has a scope regression — the DoR explicitly extends brain-extractor coverage to nine agents (ADR-0033) but both `source/` documentation and `.claude/settings.json` still scope the hook to only four (cal/colby/roz/agatha). (2) **team-collaboration-enhancements** Feature 2 (Handoff Brief generation at pipeline end) is absent from any orchestration rule — the thought-type exists in `brain/schema.sql` but no one writes to it; Feature 1's context-brief-to-brain capture is only partly implemented for routing preferences, not user preferences/corrections/rejections. (3) **cursor-port** AC-5/AC-7/AC-8/AC-9 require *all* enforcement hooks registered via `hooks.json` with `failClosed: true`, but `source/cursor/hooks/hooks.json` registers only a single `enforce-paths.sh` entry with no `failClosed` key — sequencing and git-ops enforcement is silently missing on Cursor.

Notable positives: `brain/lib/crash-guards.mjs` + `tests/brain/hardening.test.mjs` deliver all 12 brain-hardening ACs verifiably; the telemetry REST API is real and exceeds spec; Step 0 of `pipeline-setup` handles quality-gate.sh cleanup exactly as spec'd; Ci-Watch/Darwin/Deps configuration flags, commands, and personas are present and correctly default-off.

---

## Spec Status Matrix

| Spec | Status | Acceptance Criteria Met | Drift / Gaps |
|------|--------|------------------------|--------------|
| agent-telemetry.md | Reconciled | 10/10 core + out-of-scope creep | `/api/telemetry/*` REST endpoints exist despite spec line 174 "External dashboard or web UI" out of scope — intentional if superseded, but spec not reconciled |
| brain-hardening.md | Done | 12/12 | Fully implemented with tests |
| ci-watch.md | Reconciled (v3.7.0) | 12/12 specified, runtime unverifiable | All config + protocol scaffolding present; runtime flow not exercisable without live push |
| cursor-port.md | Done (claimed) | ~9/14 PASS, 4 DRIFT | Only one enforcement hook in `source/cursor/hooks/hooks.json`; sequencing, git, scout-swarm, pipeline-activation hooks missing; `failClosed` key absent |
| darwin.md | Draft | 15/15 scaffolded | Protocol + agent + command + config all present; runtime auto-trigger wired (`pipeline-orchestration.md` line 99) |
| dashboard-integration.md | Done (claimed) | 12/13 | Step 6f source path typo — SKILL.md line 802 says `source/dashboard/telemetry-bridge.sh`, actual file is `source/shared/dashboard/telemetry-bridge.sh`. AC-7 (bridge functional) unverifiable due to broken install path |
| deps-agent.md | Reconciled | 11/11 | Fully wired |
| mechanical-brain-writes.md | Draft | 12/18 | Scope regression: hook only fires for 4 of the 9 spec'd agents |
| team-collaboration-enhancements.md | Draft | 2/13 | Feature 1 partial (only routing preferences); Feature 2 (handoff brief) absent from orchestration |

---

## Findings

| # | Severity | Spec | Category | Finding | Location | Recommendation |
|---|----------|------|----------|---------|----------|----------------|
| 1 | **Critical** | mechanical-brain-writes.md | Drift (scope regression) | Spec DoR line 17 says scope "extended from four target agents to nine"; scope line 122 enumerates `cal, colby, roz, agatha, robert, robert-spec, sable, sable-ux, ellis`; AC-1–AC-6 + DoD line 188 explicitly require 9 agents. Actual settings.json scopes the brain-extractor `"type": "agent"` hook to `agent_type == 'cal' \|\| 'colby' \|\| 'roz' \|\| 'agatha'` only. 5 of 9 target agents (robert, robert-spec, sable, sable-ux, ellis) never trigger brain extraction. | `.claude/settings.json` line 91; `source/shared/rules/pipeline-orchestration.md` line 37; `source/shared/rules/agent-system.md` line 267 | Update the `if:` condition in settings.json template + pipeline-orchestration.md to include all 9 agents, OR reconcile the spec DoR + ADR-0033 reference back to 4. Spec and code must agree. |
| 2 | **High** | team-collaboration-enhancements.md | Missing | Feature 2 (Handoff Brief at pipeline end) absent from orchestration. Spec AC-1 requires Eva to generate a structured handoff brief at Final Report; AC-2 requires `agent_capture(thought_type: 'handoff', source_agent: 'eva', source_phase: 'handoff')`. Brain schema supports it (`brain/schema.sql` lines 18, 61 — importance 0.9, no TTL) but no caller exists. Grep for "handoff" / "Handoff Brief" in `source/shared/rules/pipeline-orchestration.md` returns zero hits. | Spec: `docs/product/team-collaboration-enhancements.md` Feature 2 lines 81-87. Schema ready at `brain/schema.sql` lines 18, 28, 61. Missing from `source/shared/rules/pipeline-orchestration.md` (647 lines, no handoff protocol) | Add a "Handoff Brief" protocol section to `pipeline-orchestration.md` with generation trigger (Final Report phase or explicit user request) and capture gate. |
| 3 | **High** | team-collaboration-enhancements.md | Missing | Feature 1 AC-1/AC-2/AC-3 require Eva to capture user preferences, corrections, and rejections to brain when appending to `context-brief.md`. Only routing preferences are captured (`source/shared/rules/agent-system.md` lines 162-164). General user preferences, mid-course corrections, and rejected alternatives have no capture gate. | `source/shared/rules/agent-system.md` line 162 (routing preferences only); `source/shared/rules/default-persona.md` — no preference capture protocol | Add a "Context Brief Dual-Write" gate to pipeline-orchestration.md: when Eva appends preference/correction/rejection to context-brief.md, also call `agent_capture` with matching thought_type. |
| 4 | **High** | cursor-port.md | Drift | AC-5 requires "hooks/hooks.json registers all enforcement hooks" with `failClosed: true`. AC-7/AC-8/AC-9 require blocking path, sequencing, and git-ops violations in Cursor. Actual `source/cursor/hooks/hooks.json` registers exactly **one** hook (`enforce-paths.sh`), with no `failClosed` key and no sequencing/git/scout-swarm/pipeline-activation hooks. Cursor users get path enforcement only; git-ops and sequencing enforcement is silently absent. | `source/cursor/hooks/hooks.json` (entire 9-line file); contrast with `.claude/settings.json` lines 7-50 which register 5 PreToolUse enforcement hooks | Register all enforcement shell scripts in `source/cursor/hooks/hooks.json` (or document why Cursor cannot support them, then update spec). Add `failClosed: true` per AC-5. |
| 5 | **High** | dashboard-integration.md | Drift (broken path) | AC-5 requires PlanVisualizer install to "copy bridge script". The install step in `skills/pipeline-setup/SKILL.md` line 802 says: `Copy bridge script: 'source/dashboard/telemetry-bridge.sh' -> '.claude/dashboard/telemetry-bridge.sh'`. That source path does not exist. Actual file is at `source/shared/dashboard/telemetry-bridge.sh`. PlanVisualizer install will fail at step 5 for any user who selects it. | `skills/pipeline-setup/SKILL.md` line 802; actual file: `source/shared/dashboard/telemetry-bridge.sh` | Fix SKILL.md line 802 path to `source/shared/dashboard/telemetry-bridge.sh`. |
| 6 | **Medium** | agent-telemetry.md | Orphaned feature vs. spec | Spec line 174 "Out of Scope: REST API export from brain" and line 172 "External dashboard or web UI". Actual brain exposes 5 telemetry REST endpoints (`/api/telemetry/scopes`, `/summary`, `/agents`, `/agent-detail`, `/api/stats`). Not spec'd anywhere in agent-telemetry.md. | `brain/lib/rest-api.mjs` lines 55, 58, 61, 64, 67 | Update agent-telemetry.md out-of-scope section to reflect that a REST telemetry surface now exists (or confirm the endpoints are unused and mark for removal). |
| 7 | **Medium** | dashboard-integration.md | Drift (step numbering) | Spec User Flow shows dashboard offered at **Step 6e** (line 75). Implementation places it at **Step 6f** (SKILL.md line 769), because Darwin claimed 6e. Spec is stale. | `docs/product/dashboard-integration.md` line 75; `skills/pipeline-setup/SKILL.md` line 769 | Reconcile spec to say "Step 6f". |
| 8 | **Medium** | mechanical-brain-writes.md | Drift | Spec AC-5: "Haiku extractor does NOT fire for Eva, Ellis, Poirot, Robert, Sable, or Sentinel completions". But updated DoR scope *adds* ellis, robert, robert-spec, sable, sable-ux. AC-5 and the updated DoR contradict each other — AC-5 is stale. | `docs/product/mechanical-brain-writes.md` AC-5 line 104 vs. DoR line 17 + scope line 122 | Rewrite AC-5 to only exclude Eva, Poirot, Sentinel, brain-extractor itself (matching the 9-agent scope). |
| 9 | **Medium** | ci-watch.md | Unverifiable | All AC scaffolding present (config flags, protocol, pass/fail/timeout/retry logic in `pipeline-orchestration.md` lines 593, 631, 635) but `ci_watch_enabled: false` in template and no automated test of the runtime polling loop. AC-10 "no orphan processes" and AC-11 "gh + glab tested" cannot be verified statically. Spec DoD lines 201-211 all say "Pending". | `source/shared/pipeline/pipeline-config.json` line 14; `source/shared/rules/pipeline-orchestration.md` lines 631-635 | Mark DoD entries 1-11 as "Specified / runtime unverified" or exercise in a live test. |
| 10 | **Low** | team-collaboration-enhancements.md | Format inconsistency | This spec uses `Title/Author/Date/Status: Draft` header format; all 8 other specs use DoR-table-first format. Indicates pre-pipeline authoring. | `docs/product/team-collaboration-enhancements.md` lines 1-8 | Reconcile into DoR/DoD format for consistency, or mark as "pre-pipeline concept — deferred". |
| 11 | **Low** | darwin.md | Drift | Spec DoD lines 254-270 all say "Pending" even though implementation is present. Spec is stale. | `docs/product/darwin.md` DoD table lines 254-270 | Update DoD table to "Done" with evidence pointers. |
| 12 | **Low** | cursor-port.md | Drift | Spec DoD lines 178-188 claims all 10 DoR requirements Done, but DoR #2 "Full parity — all 12 agents, enforcement hooks..." is contradicted by Finding #4 (only 1 of 5+ enforcement hooks in Cursor plugin). DoD is inaccurate. | `docs/product/cursor-port.md` DoD line 180-181 | Either restore full hook parity in Cursor plugin or revise DoD honestly. |

---

## Positive Observations

1. **Brain hardening is fully delivered and tested.** `brain/lib/crash-guards.mjs` implements uncaughtException, unhandledRejection, EPIPE, stdin EOF, SIGHUP handling (lines 49-94); `brain/lib/db.mjs` lines 20-21 set `connectionTimeoutMillis: 5000` and `idleTimeoutMillis: 30000`; `tests/brain/hardening.test.mjs` exercises crash vectors. All 12 ACs verifiable at code level.
2. **`warn-brain-capture.sh` and `prompt-brain-capture.sh` are actually deleted**, not merely deprecated — mechanical-brain-writes AC-11 and AC-12 are satisfied in the source of truth, not just in docs.
3. **Brain schema supports team collaboration thought types up-front.** `brain/schema.sql` lines 17-18 include `'preference', 'rejection', 'correction', 'handoff'`; line 61 sets `handoff` importance to 0.9 with NULL TTL (no expiry), satisfying Feature 2 AC-5 at schema level before orchestration is wired.
4. **Telemetry REST surface exceeds spec** — `/api/telemetry/scopes`, `/summary`, `/agents`, `/agent-detail` endpoints exist in `brain/lib/rest-api.mjs` lines 58-67, enabling dashboard integrations the original spec didn't anticipate.
5. **Quality-gate.sh cleanup is a first-class Step 0** in `skills/pipeline-setup/SKILL.md` lines 36-56, handling file deletion, settings.json entry removal, malformed-JSON fallback, and conditional notice — satisfying dashboard-integration ACs 9, 10, 13 with retro-lesson-003 awareness baked in.
6. **Deps agent ships complete.** Persona, command, config flag, SKILL.md step, and auto-routing entry all present. DoD table in spec fully marked Done with evidence. 11/11 ACs.
7. **Darwin auto-trigger is wired into orchestration, not just documented as a command.** `source/shared/rules/pipeline-orchestration.md` line 99 defines the exact trigger condition (`darwin_enabled: true && brain_available: true && degradation alert && sizing != Micro`) with hard-pause user approval — matches darwin.md spec AC-12 precisely.
8. **Cursor port structural parity (non-hook)**: `.cursor-plugin/plugin.json`, `mcp.json`, `rules/`, `agents/`, `commands/`, `skills/` all present; spec Risk line 178 correctly notes Cursor cannot support `"type": "agent"` hooks — shows deliberate design awareness.
9. **Config flag template is consistent and centralized** — all 6 opt-in features have well-named, default-off flags in `source/shared/pipeline/pipeline-config.json` with a single flat structure.
10. **Setup steps 6c/6d/6e/6f are all idempotent by design** — each reads existing config and skips/confirms rather than blind-writing. Non-functional reliability target for `/pipeline-setup` re-runs implemented consistently across CI Watch, Deps, Darwin, and Dashboard.

---

## Orphaned Features

- **`/api/telemetry/*` REST endpoints** (`brain/lib/rest-api.mjs` lines 58-67) — not covered by any spec. agent-telemetry.md explicitly out-of-scopes REST export. Dashboard-integration.md does not reference these endpoints.
- **`source/shared/agents/distillator.md`** — Distillator subagent in `agent-system.md` line 70, no corresponding product spec.
- **`source/shared/agents/investigator.md`** (Poirot) — "blind code investigator" agent present, no product spec.
- **`source/shared/commands/create-agent.md`** and **`telemetry-hydrate.md`** — no corresponding product specs.

---

## Spec Debt

- **team-collaboration-enhancements.md** — Status: Draft. Feature 1 partial, Feature 2 missing entirely. Oldest spec (2026-03-23) and only one in pre-pipeline format. Needs implementation push or explicit deferral.
- **cursor-port.md** — Status: Draft marked Done in DoD, but cursor hook parity (AC-5, AC-7, AC-8, AC-9) is not met. Complete the port or update DoD honestly.
- **mechanical-brain-writes.md** — Status: Draft. Scope expansion to 9 agents (per DoR + ADR-0033) not applied to hook condition in settings.json or source docs. Roll forward or roll back.
- **ci-watch.md** — Status: Reconciled, but DoD items 1-11 all "Pending". Spec admits implementation unverified at runtime. Needs live-push test pass or honest status.
- **darwin.md** — Status: Draft. DoD all "Pending" despite substantial implementation. Needs DoD reconciliation pass.

---

**Signed:** Robert
**Review mode:** READ-ONLY. ADR-blind. Zero files modified.
