# Pipeline State

<!-- PIPELINE_STATUS: {"phase": "build", "sizing": "micro", "roz_qa": null, "telemetry_captured": false, "ci_watch_active": false, "ci_watch_retry_count": 0, "ci_watch_commit_sha": "", "poirot_reviewed": false, "robert_reviewed": false, "brain_available": true, "stop_reason": null} -->

## Active Pipeline (Micro)
**Feature:** ADR-0041 patch — 9 Poirot/Gauntlet findings
**Phase:** build
**Sizing:** Micro
**Started:** 2026-04-16
**Scope:** 9 targeted fixes across 8 files; Roz pre-build tests authored (6 RED)

---

## Prior Pipeline (closed)
**Feature:** ADR-0041 — Effort-per-agent task-class tier model (Opus 4.7 xhigh)
**Stop Reason:** completed_clean
**Closed:** 2026-04-16
**Release:** v3.34.0 (commit df47b85)
**Resolved:** GitHub issue #41

**Telemetry T3:** rework=3 cycles, first_pass_qa=0.25, evoscore=1.039 (+60 net new tests). Captured as brain thought 67fccb53.

**Key decision captured:** 4-tier task-class model replaces size-dependent model tables + universal scope classifier. Priority stack: accuracy > speed > cost. Sonnet eliminated from reasoning tiers. Supersedes brain thought b09f430b (Colby Medium=Opus, 2026-04-03).

**Known pattern:** Roz partial-output stall recurred 3× this session. Mitigation: Eva-run pytest diagnostic bridges the gap. Captured as lesson d70409af. Structural fix candidate: explicit "STOP and RETURN" constraint in Roz persona.

---

## Prior Pipeline (closed)
**Feature:** ADR-0040 Design system auto-loading + Cal institutional memory search
**Stop Reason:** completed_clean
**Closed:** 2026-04-13
**Release:** v3.33.0 (commit e5686ab)

## Prior Pipeline (closed)
**Feature:** feat/brain-setup-auto-fix
**Stop Reason:** completed_clean
**Closed:** 2026-04-13
**Release:** v3.30.7

## Prior Pipeline (closed)
**Feature:** ADR-0035 + ADR-0036 + ADR-0037 — Waves 4, 5, 6
**Stop Reason:** completed_clean
**Closed:** 2026-04-12
**Release:** v3.29.0

## Prior Pipeline (closed)
**Feature:** ADR-0034 Gauntlet remediation
**Stop Reason:** completed_clean
**Closed:** 2026-04-12
**Release:** v3.28.0
</content>
</invoke>