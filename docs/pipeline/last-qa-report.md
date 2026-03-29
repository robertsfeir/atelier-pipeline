# QA Report -- 2026-03-29
*Reviewed by Roz*

## Verdict: PASS

| Check | Status | Details |
|-------|--------|---------|
| **Tier 1** | | |
| 1. Type Check | N/A | No typecheck configured |
| 2. Lint | N/A | No linter configured |
| 3. Tests (ADR-0016 Darwin) | PASS | 98/98 passing, 0 failing |
| 3. Tests (ADR-0014 Telemetry) | PASS | 62/62 passing, 0 failing |
| 3. Tests (ADR-0015 Deps) | PASS | 64/64 passing, 0 failing |
| 3. Tests (Hooks) | PASS | 43/43 passing, 0 failing |
| 3. Tests (Brain) | PASS | 92/92 passing, 0 failing |
| 4. Coverage | N/A | No coverage thresholds configured |
| 5. Complexity | PASS | All deliverables are markdown files -- no function complexity applies |
| 6. Unfinished markers | PASS | 0 TODO/FIXME/HACK/XXX found in changed files |
| **Tier 2** | | |
| 7. DB Migrations | N/A | No database changes |
| 8. Security | PASS | Darwin is read-only (disallowedTools enforced, catch-all hook verified by T-0016-019/020). No secrets, no injection surface. |
| 9. CI/CD Compat | N/A | No auth/middleware changes |
| 10. Docs Impact | NO | Pipeline infrastructure feature -- no user-facing docs affected. ADR-0016 is the architectural record. |
| 11. Dependencies | N/A | No new dependencies |
| 12. UX Flow Verification | N/A | No UX doc for pipeline infrastructure |
| 13. Exploratory | PASS | Edge cases covered by tests: absent config key (T-0016-100), all-thriving report (T-0016-075), Level 5 double confirm (T-0016-076), self-edit protection (T-0016-077), modify=reject+repropose (T-0016-099), acceptance rate self-adjustment deferred (T-0016-104) |
| 14. Semantic Correctness | PASS | Tests assert domain intent (fitness thresholds, escalation levels, gate conditions) not just structural presence |
| 15. Contract Coverage | PASS | All producer-consumer contracts verified (see Wiring section below) |
| 16. State machine completeness | N/A | No state machine changes |
| 17. Silent failure audit | N/A | No worker/handler code |
| 18. Wiring verification | PASS | No orphan producers or phantom consumers (see below) |

## Requirements Verification

| # | Requirement | Colby Claims | Roz Verified | Finding |
|---|-------------|-------------|-------------|---------|
| R1 | Agent persona exists (dual tree) | Done | Verified | T-0016-001, T-0016-002: both files exist and are identical |
| R2 | Config flag defaults false | Done | Verified | T-0016-031, T-0016-032: both configs have `darwin_enabled: false` |
| R3 | Setup Step 6e opt-in | Done | Verified | T-0016-083 through T-0016-097: Step 6e present, correctly positioned |
| R4 | /darwin command with triple gate | Done | Verified | T-0016-023 through T-0016-030: command exists, all three gates documented |
| R5 | Reads brain telemetry | Done | Verified | T-0016-049, T-0016-057: telemetry read references present |
| R6 | Fitness assessment | Done | Verified | T-0016-009: thriving/struggling/failing thresholds encoded |
| R7 | Multi-layer fix proposals | Done | Verified | T-0016-011: all 7 fix layers present in workflow |
| R8 | Evidence + risk in proposals | Done | Verified | T-0016-014: all 5 proposal fields present in output spec |
| R9 | Individual approval flow | Done | Verified | T-0016-028, T-0016-060, T-0016-098: individual presentation confirmed |
| R10 | Approved changes routed to Colby | Done | Verified | T-0016-029, T-0016-050-053: Colby routing with edit-proposal template |
| R11 | Post-edit tracking | Done | Verified | T-0016-062-065: boot step 5b tracks Darwin edits with metric delta |
| R12 | Auto-trigger on degradation | Done | Verified | T-0016-055-061, T-0016-067-070: auto-trigger with 4 conditions |
| R13 | 5-level escalation ladder | Done | Verified | T-0016-010: WARN, constraint, workflow edit, rewrite, removal |
| R14 | Read-only enforcement | Done | Verified | T-0016-017-020: disallowedTools + enforce-paths.sh catch-all |
| R15 | Self-edit protection | Done | Verified | T-0016-005, T-0016-077: cannot propose changes to darwin.md |
| R16 | 5+ pipeline minimum | Done | Verified | T-0016-006, T-0016-027, T-0016-071 |
| R17 | Discovered agent (not core) | Done | Verified | T-0016-021, T-0016-022, T-0016-044: not in core constant list |
| R18 | Dual tree sync | Done | Verified | T-0016-002, T-0016-024, T-0016-037, T-0016-046, T-0016-081, T-0016-082 |
| R19 | Two invocation templates | Done | Verified | T-0016-045-054: darwin-analysis + darwin-edit-proposal present |
| R20 | Level 5 double confirmation | Done | Verified | T-0016-076: documented in persona |
| R21 | Post-edit regression flagging | Done | Verified | T-0016-065: flags worsened edits |
| R22 | All-thriving report | Done | Verified | T-0016-075: "No changes proposed" documented |
| R23 | Rejection recording | Done | Verified | T-0016-059, T-0016-078: captured with rejection_reason |
| R9a | Modify path | Done | Verified | T-0016-099: reject + repropose cycle |
| R2a | Absent config key handling | Done | Verified | T-0016-100: treated as false |
| R8a | Conflicting proposals | Done | Verified | T-0016-098: presented individually, no merge |
| R1a | Darwin Report contract | Done | Verified | T-0016-101: report shape validated |
| R12a | Auto-trigger ordering | Done | Verified | T-0016-102: after telemetry, before staleness |
| R10a | One Colby per proposal | Done | Verified | T-0016-103: no batching |

## Unfinished Markers

`grep -r "TODO|FIXME|HACK|XXX"`: 0 matches in changed files.

## Wiring Verification

| Producer | Consumer(s) | Status |
|----------|------------|--------|
| `source/agents/darwin.md` (persona) | Eva subagent invocation via `darwin-analysis` template | Wired |
| `source/commands/darwin.md` (command) | Eva reads on `/darwin` | Wired |
| `darwin_enabled` config flag | routing gate, command gate, auto-trigger gate, boot announcement, SKILL.md Step 6e | Wired (6 files reference it) |
| `darwin-analysis` template | commands/darwin.md, pipeline-orchestration.md | Wired (3 files) |
| `darwin-edit-proposal` template | commands/darwin.md, pipeline-orchestration.md | Wired (3 files) |
| `darwin_proposal_id` metadata | pipeline-orchestration.md (capture), commands/darwin.md (reference) | Wired |
| Auto-trigger protocol | pipeline-orchestration.md (self-contained) | Wired |
| Boot announcement Darwin line | default-persona.md (self-contained) | Wired |
| Step 6e setup | SKILL.md (self-contained) | Wired |

No orphan producers. No phantom consumers.

## Dual-Tree Parity

| File Pair | Parity | Method |
|-----------|--------|--------|
| agents/darwin.md | Identical | `diff -q` (T-0016-002) |
| commands/darwin.md | Identical | `diff -q` (T-0016-024) |
| rules/agent-system.md | Matching Darwin references (4 each) | grep count |
| rules/pipeline-orchestration.md | Matching Darwin references (9 each) | grep count + T-0016-081 |
| rules/default-persona.md | Matching Darwin references (5 each) | grep count + T-0016-082 |
| references/invocation-templates.md | Matching Darwin references (6 each) | grep count + T-0016-046 |
| pipeline-config.json | Both have `darwin_enabled: false` | jq + T-0016-031/032 |

## Issues Found

No blockers. No fix-required items.

## Doc Impact: NO

Pipeline infrastructure feature. All deliverables are agent system files (personas, commands, rules, references, config). No user-facing documentation is affected. ADR-0016 serves as the architectural record.

## Roz's Assessment

Clean sweep. All 98 ADR-0016 Darwin structural tests pass. All regression test suites (ADR-0014: 62/62, ADR-0015: 64/64, hooks: 43/43, brain: 92/92) pass with zero failures across the board. Total: 359 tests, 0 failures.

Dual-tree parity is verified across all 7 file pairs. Wiring coverage is complete -- every producer has at least one consumer, no orphans. Zero unfinished markers in any changed file.

The implementation follows the established opt-in agent pattern (Sentinel, Deps) faithfully: config flag, setup step, persona, command, routing, invocation templates, pipeline integration. The self-edit protection and read-only enforcement are both behavioral (persona constraints) and mechanical (disallowedTools frontmatter + enforce-paths.sh catch-all), consistent with the project's defense-in-depth principle.

Test coverage is thorough: 98 tests covering happy paths (Steps 1-4), failure modes (gates, enforcement), boundary conditions (5-pipeline minimum, all-thriving, Level 5, absent config key, modify path), regression checks (existing agents, templates, config fields unchanged), and contract verification (producer-consumer wiring).

Recurring QA pattern worth capturing: the opt-in agent pattern (Sentinel -> Deps -> Darwin) is now a well-established template. Each iteration adds the same structural components (persona, command, config flag, routing, templates, setup step) with agent-specific behavior encoded in the persona. This pattern should be captured as a brain lesson for future agents.
